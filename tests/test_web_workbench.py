from __future__ import annotations

import base64
import os
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from ecommerce_product_image_workflow.backend.app import create_app
from ecommerce_product_image_workflow.backend.rendering import render_text_overlay
from ecommerce_product_image_workflow.providers.base import safe_response_summary
from ecommerce_product_image_workflow.providers.generic_http import GenericHttpProvider
from mvp_image_workflow.util import ValidationError


class TestWebWorkbench(unittest.TestCase):
    def test_provider_summary_redacts_secret_like_fields(self) -> None:
        summary = safe_response_summary(
            {
                "status": 200,
                "api_key": "abc",
                "Authorization": "Bearer token",
                "model": "demo",
            }
        )
        self.assertEqual(summary["api_key"], "[REDACTED]")
        self.assertEqual(summary["Authorization"], "[REDACTED]")
        self.assertEqual(summary["model"], "demo")

    def test_generic_provider_config_validation(self) -> None:
        provider = GenericHttpProvider()
        self.assertFalse(provider.test({})["ok"])
        os.environ.pop("EPI_TEST_KEY", None)
        self.assertFalse(
            provider.test({"endpoint_url": "http://127.0.0.1:9", "api_key_env": "EPI_TEST_KEY"})["ok"]
        )
        os.environ["EPI_TEST_KEY"] = "secret"
        self.assertTrue(
            provider.test({"endpoint_url": "http://127.0.0.1:9", "api_key_env": "EPI_TEST_KEY"})["ok"]
        )

    def test_text_renderer_outputs_png_and_rejects_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bg = root / "bg.png"
            text = root / "text.txt"
            out = root / "out.png"
            Image.new("RGB", (256, 256), "white").save(bg)
            text.write_text("Key Specs\n- Capacity: 500 ml\n- Leak-proof lid\n- BPA-free materials\n", encoding="utf-8")
            render_text_overlay(
                background_path=bg,
                text_path=text,
                output_path=out,
                canvas_size=(512, 512),
                text_box=(32, 300, 480, 480),
                min_font_size=12,
                max_font_size=24,
            )
            self.assertTrue(out.is_file())

            text.write_text(" ".join(["verylongtext"] * 300), encoding="utf-8")
            with self.assertRaises(ValidationError):
                render_text_overlay(
                    background_path=bg,
                    text_path=text,
                    output_path=root / "bad.png",
                    canvas_size=(256, 256),
                    text_box=(16, 180, 240, 220),
                    min_font_size=18,
                    max_font_size=20,
                )

    def test_api_generation_review_and_export_flow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            app = create_app(storage_root=td)
            client = TestClient(app)
            created = client.post(
                "/api/batches",
                json={"project_name": "Demo Store", "batch_name": "May Launch"},
            )
            self.assertEqual(created.status_code, 200, created.text)
            batch_id = created.json()["batch"]["id"]

            product_resp = client.post(
                f"/api/batches/{batch_id}/products",
                json={
                    "product_id": "SKU123",
                    "product_name_en": "Stainless Steel Insulated Tumbler",
                    "style_pack": "minimal_white",
                    "units": "cm",
                    "dimensions": {"l": "20", "w": "8", "h": "8"},
                    "specs": ["Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"],
                    "steps": ["Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"],
                    "tips": ["Hand wash recommended"],
                },
            )
            self.assertEqual(product_resp.status_code, 200, product_resp.text)
            product_pk = product_resp.json()["product"]["id"]

            source_bytes = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
            )
            upload = client.post(
                f"/api/products/{product_pk}/source-images",
                files={"file": ("source.png", source_bytes, "image/png")},
            )
            self.assertEqual(upload.status_code, 200, upload.text)
            self.assertIn("sha256", upload.json()["source_image"])

            providers = client.get("/api/providers")
            self.assertEqual(providers.status_code, 200)
            provider_ids = {p["provider_id"] for p in providers.json()["providers"]}
            self.assertIn("generic_http", provider_ids)
            self.assertIn("openai_images", provider_ids)
            self.assertIn("replicate", provider_ids)
            self.assertIn("comfyui_http", provider_ids)

            jobs_resp = client.post(
                f"/api/batches/{batch_id}/generate",
                json={"provider_id": "local_mock", "model": "local-placeholder"},
            )
            self.assertEqual(jobs_resp.status_code, 200, jobs_resp.text)
            jobs = jobs_resp.json()["jobs"]
            self.assertEqual(len(jobs), 7)
            first_job_id = jobs[0]["id"]

            first_asset_id = None
            for _ in range(80):
                app.state.runtime.jobs.join()
                batch = client.get(f"/api/batches/{batch_id}").json()
                if len(batch["assets"]) == 7:
                    first_asset_id = batch["assets"][0]["id"]
                    break
                time.sleep(0.05)
            self.assertIsNotNone(first_asset_id)
            job = client.get(f"/api/jobs/{first_job_id}").json()["job"]
            self.assertIn(job["status"], {"succeeded", "running", "queued"})

            review = client.post(
                f"/api/assets/{first_asset_id}/review",
                json={"decision": "pass", "reviewer": "manager_a", "notes": "Looks good"},
            )
            self.assertEqual(review.status_code, 200, review.text)

            retry = client.post(f"/api/assets/{first_asset_id}/retry")
            self.assertEqual(retry.status_code, 200, retry.text)
            app.state.runtime.jobs.join()

            exported = client.post(f"/api/batches/{batch_id}/export")
            self.assertEqual(exported.status_code, 200, exported.text)
            zip_path = Path(td) / "export.zip"
            zip_path.write_bytes(exported.content)
            with zipfile.ZipFile(zip_path) as zf:
                names = set(zf.namelist())
            self.assertIn("batch_manifest.json", names)
            self.assertIn("qa_review.csv", names)
            self.assertTrue(any(name.startswith("assets/") for name in names))

            exported_get = client.get(f"/api/batches/{batch_id}/export")
            self.assertEqual(exported_get.status_code, 200, exported_get.text)

    def test_api_rejects_raw_provider_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            client = TestClient(create_app(storage_root=td))
            batch_id = client.post(
                "/api/batches",
                json={"project_name": "Demo Store", "batch_name": "Secrets"},
            ).json()["batch"]["id"]
            client.post(
                f"/api/batches/{batch_id}/products",
                json={
                    "product_id": "SKU123",
                    "product_name_en": "Stainless Steel Insulated Tumbler",
                    "style_pack": "minimal_white",
                    "specs": ["Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"],
                    "steps": ["Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"],
                },
            )
            resp = client.post(
                f"/api/batches/{batch_id}/generate",
                json={"provider_id": "generic_http", "model": "demo", "config": {"api_key": "raw-secret"}},
            )
            self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
