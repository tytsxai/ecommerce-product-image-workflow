from __future__ import annotations

import json
import os
import queue
import threading
import time
import zipfile
from io import StringIO
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from mvp_image_workflow.batch import ProductRow
from mvp_image_workflow.generator import QC_REJECT_TAGS, generate_product_package
from mvp_image_workflow.stylepacks import default_style_pack_path, load_style_packs
from mvp_image_workflow.util import ValidationError, file_sha256, now_utc_iso, safe_id

from ecommerce_product_image_workflow.backend.db import Database
from ecommerce_product_image_workflow.backend.rendering import render_text_overlay
from ecommerce_product_image_workflow.providers import get_provider, list_provider_metadata
from ecommerce_product_image_workflow.providers.base import GenerateRequest


JOB_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}


class WorkbenchRuntime:
    def __init__(self, storage_root: str | Path):
        self.storage_root = Path(storage_root).expanduser().resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.db = Database(self.storage_root / "workflow.sqlite3")
        self.jobs: "queue.Queue[int]" = queue.Queue()
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def enqueue(self, job_id: int) -> None:
        self.jobs.put(job_id)

    def _worker_loop(self) -> None:
        while True:
            job_id = self.jobs.get()
            try:
                self.run_job(job_id)
            finally:
                self.jobs.task_done()

    def run_job(self, job_id: int) -> None:
        job = self.db.query_one("SELECT * FROM generation_jobs WHERE id = ?", (job_id,))
        if not job or job["status"] == "cancelled":
            return
        self.db.execute(
            "UPDATE generation_jobs SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (job_id,),
        )
        try:
            product = self.db.query_one("SELECT * FROM products WHERE id = ?", (job["product_pk"],))
            if product is None:
                raise ValidationError("Product not found for generation job")
            source_paths = tuple(
                Path(row["path"])
                for row in self.db.query_all(
                    "SELECT path FROM source_images WHERE product_pk = ? ORDER BY id",
                    (product["id"],),
                )
            )
            provider = get_provider(job["provider_id"])
            package_dir = self._package_dir(int(job["batch_id"]))
            product_dir = package_dir / safe_id(product["product_id"])
            expected_filename = _expected_filename(job, product)
            final_path = product_dir / job["category"] / expected_filename
            background_path = final_path
            if job["category"] in {"spec", "howto"}:
                background_path = product_dir / "meta" / "backgrounds" / expected_filename

            provider_result = provider.generate(
                GenerateRequest(
                    prompt=job["prompt"],
                    model=job["model"],
                    output_path=background_path,
                    config=_job_config(job),
                    source_image_paths=source_paths,
                    aspect_ratio="1:1",
                )
            )
            output_path = provider_result.output_path
            if job["category"] in {"spec", "howto"}:
                text_path = product_dir / "texts" / f"{job['category']}_{int(job['slot']):02d}.txt"
                output_path = render_text_overlay(
                    background_path=background_path,
                    text_path=text_path,
                    output_path=final_path,
                )

            version = _next_asset_version(self.db, int(job["product_pk"]), job["category"], expected_filename)
            asset_id = self.db.execute(
                """
                INSERT INTO generated_assets
                  (job_id, batch_id, product_pk, category, filename, path, version,
                   provider_id, model, prompt, response_summary_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job["batch_id"],
                    job["product_pk"],
                    job["category"],
                    expected_filename,
                    str(output_path),
                    version,
                    job["provider_id"],
                    job["model"],
                    job["prompt"],
                    json.dumps(provider_result.response_summary, ensure_ascii=False),
                ),
            )
            self.db.execute(
                """
                UPDATE generation_jobs
                SET status = 'succeeded', asset_id = ?, error = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (asset_id, job_id),
            )
        except Exception as e:
            self.db.execute(
                """
                UPDATE generation_jobs
                SET status = 'failed', error = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(e), job_id),
            )
        self.refresh_batch_status(int(job["batch_id"]))

    def _package_dir(self, batch_id: int) -> Path:
        return self.storage_root / "batches" / str(batch_id) / "package"

    def refresh_batch_status(self, batch_id: int) -> None:
        rows = self.db.query_all("SELECT status FROM generation_jobs WHERE batch_id = ?", (batch_id,))
        if not rows:
            return
        statuses = {row["status"] for row in rows}
        if statuses <= {"succeeded"}:
            status = "ready_for_review"
        elif statuses <= {"succeeded", "failed", "cancelled"}:
            status = "needs_attention"
        else:
            status = "generating"
        self.db.execute("UPDATE batches SET status = ? WHERE id = ?", (status, batch_id))


def create_app(storage_root: str | Path | None = None) -> FastAPI:
    root = Path(storage_root or os.environ.get("EPI_WORKFLOW_HOME", "~/.ecommerce_product_image_workflow"))
    runtime = WorkbenchRuntime(root)
    app = FastAPI(title="E-commerce Product Image Workflow", version="0.2.0")
    app.state.runtime = runtime

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8787", "http://127.0.0.1:8787"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/media", StaticFiles(directory=str(runtime.storage_root)), name="media")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "storage_root": str(runtime.storage_root)}

    @app.get("/api/style-packs")
    def style_packs() -> dict[str, Any]:
        packs = load_style_packs(default_style_pack_path())
        return {"style_packs": [pack.__dict__ for pack in packs.values()]}

    @app.get("/api/providers")
    def providers() -> dict[str, Any]:
        return {"providers": list_provider_metadata()}

    @app.post("/api/providers/test")
    def test_provider(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            provider = get_provider(str(payload.get("provider_id") or ""))
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return provider.test(payload.get("config") or {})

    @app.get("/api/batches")
    def list_batches() -> dict[str, Any]:
        rows = runtime.db.query_all(
            """
            SELECT batches.*, projects.name AS project_name
            FROM batches JOIN projects ON projects.id = batches.project_id
            ORDER BY batches.id DESC
            """
        )
        return {"batches": rows}

    @app.post("/api/batches")
    def create_batch(payload: dict[str, Any]) -> dict[str, Any]:
        project_name = str(payload.get("project_name") or "Default Project").strip()
        batch_name = str(payload.get("batch_name") or payload.get("name") or f"Batch {now_utc_iso()}").strip()
        if not project_name or not batch_name:
            raise HTTPException(status_code=400, detail="project_name and batch_name are required")
        project_id = runtime.db.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
        batch_id = runtime.db.execute(
            "INSERT INTO batches (project_id, name, status) VALUES (?, ?, 'draft')",
            (project_id, batch_name),
        )
        return get_batch_payload(runtime, batch_id)

    @app.get("/api/batches/{batch_id}")
    def get_batch(batch_id: int) -> dict[str, Any]:
        return get_batch_payload(runtime, batch_id)

    @app.post("/api/batches/{batch_id}/products")
    def add_product(batch_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        batch = runtime.db.query_one("SELECT id FROM batches WHERE id = ?", (batch_id,))
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        try:
            row = _product_row_from_payload(payload)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        product_pk = runtime.db.execute(
            """
            INSERT INTO products
              (batch_id, product_id, product_name_en, style_pack, output_set, units,
               dimensions_json, specs_json, steps_json, tips_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                row.product_id,
                row.product_name_en,
                row.style_pack,
                row.output_set,
                row.units,
                json.dumps({"l": row.dimensions_l, "w": row.dimensions_w, "h": row.dimensions_h}),
                json.dumps(list(row.specs), ensure_ascii=False),
                json.dumps(list(row.steps), ensure_ascii=False),
                json.dumps(list(row.tips), ensure_ascii=False),
            ),
        )
        return {"product": _product_payload(runtime, product_pk)}

    @app.post("/api/products/{product_pk}/source-images")
    async def upload_source_image(product_pk: int, file: UploadFile = File(...)) -> dict[str, Any]:
        product = runtime.db.query_one("SELECT id FROM products WHERE id = ?", (product_pk,))
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        safe_name = safe_id(Path(file.filename or "source").stem) or "source"
        suffix = Path(file.filename or "").suffix.lower() or ".bin"
        target = runtime.storage_root / "uploads" / str(product_pk) / f"{int(time.time() * 1000)}_{safe_name}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(await file.read())
        digest = file_sha256(target)
        image_id = runtime.db.execute(
            "INSERT INTO source_images (product_pk, filename, path, sha256) VALUES (?, ?, ?, ?)",
            (product_pk, file.filename or target.name, str(target), digest),
        )
        return {"source_image": {**runtime.db.query_one("SELECT * FROM source_images WHERE id = ?", (image_id,)), "media_url": _media_url(runtime, target)}}

    @app.post("/api/batches/{batch_id}/generate")
    def generate_batch(batch_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        provider_id = str(payload.get("provider_id") or "local_mock")
        model = str(payload.get("model") or "local-placeholder")
        config = _safe_provider_config(payload.get("config") or {})
        try:
            get_provider(provider_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        products = runtime.db.query_all("SELECT * FROM products WHERE batch_id = ? ORDER BY id", (batch_id,))
        if not products:
            raise HTTPException(status_code=400, detail="Batch has no products")
        jobs: list[dict[str, Any]] = []
        for product in products:
            row = _product_row_from_db(runtime, product)
            product_dir = generate_product_package(
                row,
                runtime._package_dir(batch_id),
                batch_id=f"B{batch_id}",
                source_base_dir=runtime.storage_root,
                copy_source_images=False,
            )
            prompt_map = _prompt_map(product_dir)
            for category in ("showcase", "spec", "howto"):
                for slot in range(1, 4 if category == "showcase" else 3):
                    prompt = prompt_map[(category, slot)].read_text(encoding="utf-8")
                    job_id = runtime.db.execute(
                        """
                        INSERT INTO generation_jobs
                          (batch_id, product_pk, category, slot, status, provider_id, model, prompt, config_json)
                        VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?)
                        """,
                        (batch_id, product["id"], category, slot, provider_id, model, prompt, json.dumps(config)),
                    )
                    runtime.enqueue(job_id)
                    jobs.append(runtime.db.query_one("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)))
        runtime.db.execute("UPDATE batches SET status = 'generating' WHERE id = ?", (batch_id,))
        return {"jobs": jobs}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: int) -> dict[str, Any]:
        job = runtime.db.query_one("SELECT * FROM generation_jobs WHERE id = ?", (job_id,))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": _job_payload(runtime, job)}

    @app.post("/api/assets/{asset_id}/review")
    def review_asset(asset_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        asset = runtime.db.query_one("SELECT * FROM generated_assets WHERE id = ?", (asset_id,))
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        decision = str(payload.get("decision") or "").lower()
        if decision not in {"pass", "reject"}:
            raise HTTPException(status_code=400, detail="decision must be pass or reject")
        reject_tag = payload.get("reject_tag")
        if decision == "reject" and reject_tag not in QC_REJECT_TAGS:
            raise HTTPException(status_code=400, detail="reject_tag is required and must be valid for reject")
        review_id = runtime.db.execute(
            """
            INSERT INTO qa_reviews (asset_id, decision, reject_tag, reviewer, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                decision,
                reject_tag if decision == "reject" else None,
                payload.get("reviewer") or "",
                payload.get("notes") or "",
            ),
        )
        return {"review": runtime.db.query_one("SELECT * FROM qa_reviews WHERE id = ?", (review_id,))}

    @app.post("/api/assets/{asset_id}/retry")
    def retry_asset(asset_id: int) -> dict[str, Any]:
        asset = runtime.db.query_one("SELECT * FROM generated_assets WHERE id = ?", (asset_id,))
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        old_job = runtime.db.query_one("SELECT * FROM generation_jobs WHERE id = ?", (asset["job_id"],))
        if old_job is None:
            raise HTTPException(status_code=404, detail="Original job not found")
        job_id = runtime.db.execute(
            """
            INSERT INTO generation_jobs
              (batch_id, product_pk, category, slot, status, provider_id, model, prompt, config_json)
            VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?)
            """,
            (
                old_job["batch_id"],
                old_job["product_pk"],
                old_job["category"],
                old_job["slot"],
                old_job["provider_id"],
                old_job["model"],
                old_job["prompt"],
                old_job.get("config_json") or "{}",
            ),
        )
        runtime.enqueue(job_id)
        return {"job": runtime.db.query_one("SELECT * FROM generation_jobs WHERE id = ?", (job_id,))}

    @app.get("/api/batches/{batch_id}/export")
    @app.post("/api/batches/{batch_id}/export")
    def export_batch(batch_id: int) -> FileResponse:
        path = _export_batch(runtime, batch_id)
        return FileResponse(path, media_type="application/zip", filename=path.name)

    return app


def get_batch_payload(runtime: WorkbenchRuntime, batch_id: int) -> dict[str, Any]:
    batch = runtime.db.query_one(
        """
        SELECT batches.*, projects.name AS project_name
        FROM batches JOIN projects ON projects.id = batches.project_id
        WHERE batches.id = ?
        """,
        (batch_id,),
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    products = [_product_payload(runtime, row["id"]) for row in runtime.db.query_all("SELECT id FROM products WHERE batch_id = ? ORDER BY id", (batch_id,))]
    jobs = [_job_payload(runtime, row) for row in runtime.db.query_all("SELECT * FROM generation_jobs WHERE batch_id = ? ORDER BY id DESC", (batch_id,))]
    assets = [_asset_payload(runtime, row) for row in runtime.db.query_all("SELECT * FROM generated_assets WHERE batch_id = ? ORDER BY id DESC", (batch_id,))]
    return {"batch": batch, "products": products, "jobs": jobs, "assets": assets}


def _product_row_from_payload(payload: dict[str, Any]) -> ProductRow:
    product_id = str(payload.get("product_id") or "").strip()
    product_name_en = str(payload.get("product_name_en") or "").strip()
    if not product_id or safe_id(product_id) != product_id:
        raise ValidationError("product_id is required and must use letters, numbers, '-' or '_'")
    if not product_name_en:
        raise ValidationError("product_name_en is required")
    specs = tuple(str(item).strip() for item in payload.get("specs", []) if str(item).strip())
    steps = tuple(str(item).strip() for item in payload.get("steps", []) if str(item).strip())
    if len(specs) < 3:
        raise ValidationError("At least 3 specs are required")
    if len(steps) < 3:
        raise ValidationError("At least 3 steps are required")
    dimensions = payload.get("dimensions") or {}
    return ProductRow(
        product_id=product_id,
        product_name_en=product_name_en,
        style_pack=str(payload.get("style_pack") or "minimal_white"),
        output_set="minimum",
        units=str(payload.get("units") or "cm"),
        dimensions_l=_optional_str(dimensions.get("l")),
        dimensions_w=_optional_str(dimensions.get("w")),
        dimensions_h=_optional_str(dimensions.get("h")),
        specs=specs,
        howto_title=str(payload.get("howto_title") or "How to Use"),
        steps=steps,
        tips=tuple(str(item).strip() for item in payload.get("tips", []) if str(item).strip()),
        manager_notes=_optional_str(payload.get("manager_notes")),
        must_have_keywords=_optional_str(payload.get("must_have_keywords")),
        must_avoid_elements=_optional_str(payload.get("must_avoid_elements")),
        personalization_text_en=_optional_str(payload.get("personalization_text_en")),
    )


def _product_row_from_db(runtime: WorkbenchRuntime, product: dict[str, Any]) -> ProductRow:
    dimensions = json.loads(product["dimensions_json"])
    source_paths = tuple(
        row["path"]
        for row in runtime.db.query_all("SELECT path FROM source_images WHERE product_pk = ? ORDER BY id", (product["id"],))
    )
    return ProductRow(
        product_id=product["product_id"],
        product_name_en=product["product_name_en"],
        style_pack=product["style_pack"],
        output_set=product["output_set"],
        units=product["units"],
        dimensions_l=dimensions.get("l"),
        dimensions_w=dimensions.get("w"),
        dimensions_h=dimensions.get("h"),
        specs=tuple(json.loads(product["specs_json"])),
        howto_title="How to Use",
        steps=tuple(json.loads(product["steps_json"])),
        tips=tuple(json.loads(product["tips_json"])),
        manager_notes=None,
        must_have_keywords=None,
        must_avoid_elements=None,
        personalization_text_en=None,
        source_image_paths=source_paths,
    )


def _product_payload(runtime: WorkbenchRuntime, product_pk: int) -> dict[str, Any]:
    product = runtime.db.query_one("SELECT * FROM products WHERE id = ?", (product_pk,))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["dimensions"] = json.loads(product.pop("dimensions_json"))
    product["specs"] = json.loads(product.pop("specs_json"))
    product["steps"] = json.loads(product.pop("steps_json"))
    product["tips"] = json.loads(product.pop("tips_json"))
    product["source_images"] = [
        {**row, "media_url": _media_url(runtime, Path(row["path"]))}
        for row in runtime.db.query_all("SELECT * FROM source_images WHERE product_pk = ? ORDER BY id", (product_pk,))
    ]
    return product


def _job_payload(runtime: WorkbenchRuntime, job: dict[str, Any]) -> dict[str, Any]:
    if job.get("asset_id"):
        asset = runtime.db.query_one("SELECT * FROM generated_assets WHERE id = ?", (job["asset_id"],))
        job["asset"] = _asset_payload(runtime, asset) if asset else None
    return job


def _asset_payload(runtime: WorkbenchRuntime, asset: dict[str, Any]) -> dict[str, Any]:
    asset = dict(asset)
    asset["media_url"] = _media_url(runtime, Path(asset["path"]))
    asset["response_summary"] = json.loads(asset.pop("response_summary_json"))
    asset["reviews"] = runtime.db.query_all("SELECT * FROM qa_reviews WHERE asset_id = ? ORDER BY id DESC", (asset["id"],))
    return asset


def _prompt_map(product_dir: Path) -> dict[tuple[str, int], Path]:
    return {
        ("showcase", 1): product_dir / "prompts" / "showcase_01_clean_main.txt",
        ("showcase", 2): product_dir / "prompts" / "showcase_02_lifestyle_A.txt",
        ("showcase", 3): product_dir / "prompts" / "showcase_03_lifestyle_B.txt",
        ("spec", 1): product_dir / "prompts" / "spec_01_dimensions_background.txt",
        ("spec", 2): product_dir / "prompts" / "spec_02_specs_background.txt",
        ("howto", 1): product_dir / "prompts" / "howto_01_steps_background.txt",
        ("howto", 2): product_dir / "prompts" / "howto_02_tips_background.txt",
    }


def _expected_filename(job: dict[str, Any], product: dict[str, Any]) -> str:
    safe_product_id = safe_id(product["product_id"])
    suffix = f"_B{job['batch_id']}"
    return f"{safe_product_id}_{job['category']}_{int(job['slot']):02d}{suffix}.png"


def _job_config(job: dict[str, Any]) -> dict[str, Any]:
    raw = job.get("config_json") or "{}"
    return json.loads(raw) if raw else {}


def _safe_provider_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="provider config must be an object")
    blocked = ("api_key", "token", "secret", "password", "authorization")
    for key in config:
        lowered = str(key).lower()
        if lowered == "api_key_env":
            continue
        if any(item in lowered for item in blocked):
            raise HTTPException(
                status_code=400,
                detail="Do not send raw API keys in provider config. Use api_key_env and local environment variables.",
            )
    return config


def _next_asset_version(db: Database, product_pk: int, category: str, filename: str) -> int:
    row = db.query_one(
        "SELECT MAX(version) AS version FROM generated_assets WHERE product_pk = ? AND category = ? AND filename = ?",
        (product_pk, category, filename),
    )
    return int(row["version"] or 0) + 1


def _media_url(runtime: WorkbenchRuntime, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(runtime.storage_root)
    except ValueError:
        return ""
    return "/media/" + "/".join(rel.parts)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _export_batch(runtime: WorkbenchRuntime, batch_id: int) -> Path:
    export_dir = runtime.storage_root / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"batch_{batch_id}_approved_assets.zip"
    approved_assets = runtime.db.query_all(
        """
        SELECT DISTINCT generated_assets.*
        FROM generated_assets
        JOIN qa_reviews ON qa_reviews.asset_id = generated_assets.id
        WHERE generated_assets.batch_id = ? AND qa_reviews.decision = 'pass'
        ORDER BY generated_assets.id
        """,
        (batch_id,),
    )
    batch = get_batch_payload(runtime, batch_id)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("batch_manifest.json", json.dumps(batch, ensure_ascii=False, indent=2))
        zf.writestr("operator_runbook.md", "# Export\n\nOnly QA-approved assets are included.\n")
        zf.writestr("qa_review.csv", _qa_csv(runtime, batch_id))
        for asset in approved_assets:
            path = Path(asset["path"])
            if path.is_file():
                zf.write(path, f"assets/{asset['filename']}")
    return zip_path


def _qa_csv(runtime: WorkbenchRuntime, batch_id: int) -> str:
    import csv

    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(["asset_id", "filename", "decision", "reject_tag", "reviewer", "reviewed_at", "notes"])
    reviews = runtime.db.query_all(
        """
        SELECT generated_assets.id AS asset_id, generated_assets.filename, qa_reviews.*
        FROM generated_assets
        LEFT JOIN qa_reviews ON qa_reviews.asset_id = generated_assets.id
        WHERE generated_assets.batch_id = ?
        ORDER BY generated_assets.id
        """,
        (batch_id,),
    )
    for row in reviews:
        writer.writerow(
            [
                row.get("asset_id") or "",
                row.get("filename") or "",
                row.get("decision") or "",
                row.get("reject_tag") or "",
                row.get("reviewer") or "",
                row.get("created_at") or "",
                row.get("notes") or "",
            ]
        )
    return out.getvalue()
