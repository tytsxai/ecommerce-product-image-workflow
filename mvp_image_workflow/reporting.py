from __future__ import annotations

import csv
import json
from pathlib import Path

from .batch import ProductRow
from .generator import QC_FAIL_FAST
from .util import atomic_write_json, atomic_write_text, now_utc_iso


def _load_manifest(product_dir: Path) -> dict:
    return json.loads((product_dir / "manifest.json").read_text(encoding="utf-8"))


def write_batch_artifacts(
    out_root: str | Path,
    products: list[ProductRow],
    product_dirs: list[Path],
    *,
    batch_id: str | None,
    style_pack_file: str | Path | None,
) -> None:
    root = Path(out_root)
    manifests = [_load_manifest(product_dir) for product_dir in product_dirs]
    normalized_batch_id = manifests[0].get("batch_id") if manifests else batch_id
    if normalized_batch_id is not None and not isinstance(normalized_batch_id, str):
        normalized_batch_id = str(normalized_batch_id)

    batch_manifest = {
        "version": "0.2.0",
        "generated_at_utc": now_utc_iso(),
        "batch_id": normalized_batch_id,
        "product_count": len(product_dirs),
        "style_pack_file": str(style_pack_file) if style_pack_file is not None else None,
        "products": [
            {
                "product_id": product.product_id,
                "product_name_en": product.product_name_en,
                "style_pack": product.style_pack,
                "package_dir": product_dir.name,
                "source_image_count": len(product.source_image_paths),
                "expected_output_count": sum(
                    len(files) for files in manifest.get("expected_outputs", {}).values()
                ),
            }
            for product, product_dir, manifest in zip(products, product_dirs, manifests)
        ],
    }
    atomic_write_json(root / "batch_manifest.json", batch_manifest)

    qa_path = root / "qa_review.csv"
    with qa_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "batch_id",
                "product_id",
                "category",
                "expected_filename",
                "asset_exists",
                "decision",
                "reject_tag",
                "reviewer",
                "reviewed_at",
                "notes",
            ]
        )
        for product, product_dir, manifest in zip(products, product_dirs, manifests):
            expected_outputs = manifest.get("expected_outputs", {})
            for category, files in expected_outputs.items():
                for fname in files:
                    writer.writerow(
                        [
                            normalized_batch_id or "",
                            product.product_id,
                            category,
                            fname,
                            "no",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )

    atomic_write_text(root / "operator_runbook.md", _operator_runbook_text(len(product_dirs)))


def _operator_runbook_text(product_count: int) -> str:
    fail_fast = "\n".join(f"- {item}" for item in QC_FAIL_FAST)
    return f"""# Operator Runbook

This batch package contains {product_count} product package(s).

## Run Order

1. Open each product folder and generate images from `prompts/`.
2. Use `texts/` as the only text source for spec/how-to overlays.
3. Save finished images using the exact names listed in `manifest.json`.
4. Fill `qa_review.csv` after visual review.
5. Run `python3 -m mvp_image_workflow validate --out <this-folder> --require-images` before handoff.

## Fail-fast Rules

{fail_fast}
"""
