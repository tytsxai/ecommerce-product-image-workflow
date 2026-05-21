from __future__ import annotations

import json
import shutil
from pathlib import Path

from .batch import ProductRow
from .stylepacks import StylePack, style_pack_prompt_lines
from .util import ValidationError, atomic_write_json, atomic_write_text, file_sha256, now_utc_iso, safe_id


QC_FAIL_FAST = [
    "Product changed (shape/structure/color/ratio).",
    "Background too similar to supplier image (duplicate suspicion).",
    "Any visible text is not English (except immutable brand trademark).",
    "Specs values/units/meaning changed.",
    "How-to meaning changed (steps/tips no longer match the source).",
]

QC_REJECT_TAGS = [
    "product_changed",
    "background_too_similar",
    "text_not_english",
    "spec_value_error",
    "howto_meaning_changed",
    "personalization_rule_violation",
    "low_realism",
]


def _write_text(path: Path, content: str) -> None:
    atomic_write_text(path, content)


def _write_json(path: Path, obj: object) -> None:
    atomic_write_json(path, obj)


def _dimensions_line(product: ProductRow) -> str | None:
    if not (product.dimensions_l and product.dimensions_w and product.dimensions_h):
        return None
    return f"Dimensions: {product.dimensions_l} x {product.dimensions_w} x {product.dimensions_h} {product.units}"


def _validate_batch_id(batch_id: str | None) -> str | None:
    if batch_id is None:
        return None
    raw = batch_id.strip().replace(" ", "_")
    safe = safe_id(batch_id)
    if not safe:
        raise ValidationError("batch_id cannot be empty after normalization")
    if safe != raw:
        raise ValidationError(
            "batch_id contains unsafe characters; allowed: letters, numbers, '-' and '_'"
        )
    return safe


def _read_existing_manifest_product_id(product_dir: Path) -> str | None:
    manifest_path = product_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in existing {manifest_path}: {e}") from None

    if not isinstance(data, dict):
        raise ValidationError(f"Invalid existing {manifest_path}: expected JSON object")
    product = data.get("product")
    if not isinstance(product, dict):
        raise ValidationError(f"Invalid existing {manifest_path}: missing 'product' object")
    pid = product.get("product_id")
    if pid is None:
        return None
    if not isinstance(pid, str):
        raise ValidationError(f"Invalid existing {manifest_path}: product.product_id must be a string")
    return pid


def _source_path_is_remote(raw: str) -> bool:
    lowered = raw.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _resolve_source_path(raw: str, source_base_dir: str | Path | None) -> Path:
    p = Path(raw).expanduser()
    if p.is_absolute():
        return p
    base = Path(source_base_dir) if source_base_dir is not None else Path.cwd()
    return base / p


def _safe_source_filename(index: int, src: Path) -> str:
    stem = safe_id(src.stem) or f"source_{index:02d}"
    suffix = src.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}:
        suffix = ".bin"
    return f"{index:02d}_{stem}{suffix}"


def _collect_source_images(
    product: ProductRow,
    source_dir: Path,
    *,
    source_base_dir: str | Path | None,
    copy_source_images: bool,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index, raw in enumerate(product.source_image_paths, start=1):
        record: dict[str, object] = {"original_path": raw}
        if _source_path_is_remote(raw):
            if copy_source_images:
                raise ValidationError(f"Cannot copy remote source image for {product.product_id}: {raw}")
            record["type"] = "remote_reference"
            records.append(record)
            continue

        resolved = _resolve_source_path(raw, source_base_dir)
        record["resolved_path"] = str(resolved)
        record["exists"] = resolved.is_file()
        if resolved.is_file():
            record["sha256"] = file_sha256(resolved)
            if copy_source_images:
                dest = source_dir / _safe_source_filename(index, resolved)
                shutil.copy2(resolved, dest)
                record["package_path"] = str(dest.relative_to(source_dir.parent))
        elif copy_source_images:
            raise ValidationError(f"Source image not found for {product.product_id}: {resolved}")
        records.append(record)
    return records


def _review_packet_text(product: ProductRow, expected: dict[str, list[str]]) -> str:
    lines = [
        f"# QA Review Packet: {product.product_id}",
        "",
        f"- Product: {product.product_name_en}",
        f"- Style pack: {product.style_pack}",
        f"- Output set: {product.output_set}",
        "",
        "## Expected Outputs",
    ]
    for category, files in expected.items():
        lines.append(f"### {category}")
        lines.extend(f"- `{fname}`" for fname in files)
    lines.extend(
        [
            "",
            "## Fail-fast Rules",
            *[f"- {item}" for item in QC_FAIL_FAST],
            "",
            "## Rejection Tags",
            ", ".join(f"`{tag}`" for tag in QC_REJECT_TAGS),
        ]
    )
    return "\n".join(lines)


def generate_product_package(
    product: ProductRow,
    out_root: str | Path,
    batch_id: str | None,
    *,
    style_pack: StylePack | None = None,
    source_base_dir: str | Path | None = None,
    copy_source_images: bool = False,
) -> Path:
    root = Path(out_root)
    if root.exists() and not root.is_dir():
        raise ValidationError(f"Output root must be a directory: {root}")
    safe_product_id = safe_id(product.product_id)
    if not safe_product_id:
        raise ValidationError(
            f"product_id '{product.product_id}' cannot be converted to a safe folder name."
        )
    if safe_product_id != product.product_id:
        raise ValidationError(
            "product_id contains unsafe characters; allowed: letters, numbers, '-' and '_'"
        )

    safe_batch_id = _validate_batch_id(batch_id)

    product_dir = root / safe_product_id
    existing_pid = _read_existing_manifest_product_id(product_dir)
    if existing_pid is not None and existing_pid != product.product_id:
        raise ValidationError(
            "product_id collision after normalization: "
            f"existing '{existing_pid}' vs new '{product.product_id}' map to '{safe_product_id}'"
        )
    showcase_dir = product_dir / "showcase"
    spec_dir = product_dir / "spec"
    howto_dir = product_dir / "howto"
    source_dir = product_dir / "source"
    prompts_dir = product_dir / "prompts"
    texts_dir = product_dir / "texts"
    meta_dir = product_dir / "meta"

    for d in [showcase_dir, spec_dir, howto_dir, source_dir, prompts_dir, texts_dir, meta_dir]:
        d.mkdir(parents=True, exist_ok=True)

    prefix = safe_product_id
    suffix = f"_{safe_batch_id}" if safe_batch_id else ""

    expected = {
        "showcase": [
            f"{prefix}_showcase_01{suffix}.png",
            f"{prefix}_showcase_02{suffix}.png",
            f"{prefix}_showcase_03{suffix}.png",
        ],
        "spec": [
            f"{prefix}_spec_01{suffix}.png",
            f"{prefix}_spec_02{suffix}.png",
        ],
        "howto": [
            f"{prefix}_howto_01{suffix}.png",
            f"{prefix}_howto_02{suffix}.png",
        ],
    }

    source_images = _collect_source_images(
        product,
        source_dir,
        source_base_dir=source_base_dir,
        copy_source_images=copy_source_images,
    )

    # Text sources (English-only; intended to be template-rendered onto generated backgrounds).
    dims = _dimensions_line(product)
    spec_01_lines = [product.product_name_en]
    if dims:
        spec_01_lines.append(dims)
    spec_01_lines.extend(f"- {s}" for s in product.specs)
    _write_text(texts_dir / "spec_01.txt", "\n".join(spec_01_lines))

    spec_02_lines = ["Key Specs", ""]
    spec_02_lines.extend(f"- {s}" for s in product.specs)
    _write_text(texts_dir / "spec_02.txt", "\n".join(spec_02_lines))

    howto_01_lines = [product.howto_title, ""]
    howto_01_lines.extend(f"Step {i+1}: {s}" for i, s in enumerate(product.steps))
    _write_text(texts_dir / "howto_01.txt", "\n".join(howto_01_lines))

    howto_02_lines = ["Tips", ""]
    if product.tips:
        howto_02_lines.extend(f"- {t}" for t in product.tips)
    else:
        howto_02_lines.append("- (Optional) Add 2-4 short English tips.")
    _write_text(texts_dir / "howto_02.txt", "\n".join(howto_02_lines))

    if product.personalization_text_en:
        _write_text(texts_dir / "personalization_text.txt", product.personalization_text_en)

    # Prompts.
    global_constraints = [
        "NON-NEGOTIABLES:",
        "- Product Lock: product must be 100% identical to supplier product (shape/structure/color/ratio).",
        "- Background must be clearly different from supplier images (no duplication).",
        "- Final images must contain only English text; do not invent text.",
        "- Keep realism, correct materials, and believable shadows.",
        "",
        *style_pack_prompt_lines(style_pack, product.style_pack),
    ]
    if product.must_have_keywords:
        global_constraints.append(f"Must-have keywords (manager): {product.must_have_keywords}")
    if product.must_avoid_elements:
        global_constraints.append(f"Must-avoid elements (manager): {product.must_avoid_elements}")
    if product.manager_notes:
        global_constraints.append(f"Manager notes (may be EN/RU): {product.manager_notes}")

    showcase_01 = [
        *global_constraints,
        "",
        "SHOT TYPE: Clean main e-commerce image (1:1).",
        "- Simple, clean background suitable for marketplaces.",
        "- Product centered, uncluttered, soft shadow.",
        "- No extra props that could alter perception of the product.",
    ]
    _write_text(prompts_dir / "showcase_01_clean_main.txt", "\n".join(showcase_01))

    showcase_02 = [
        *global_constraints,
        "",
        "SHOT TYPE: Lifestyle scene (variation A).",
        "- Clearly different background and composition vs supplier images.",
        "- Keep product identity locked.",
        "- Add context props appropriate to the category, but do not occlude key product parts.",
    ]
    _write_text(prompts_dir / "showcase_02_lifestyle_A.txt", "\n".join(showcase_02))

    showcase_03 = [
        *global_constraints,
        "",
        "SHOT TYPE: Lifestyle scene (variation B).",
        "- Different scene/lighting/composition vs variation A.",
        "- Keep product identity locked.",
    ]
    _write_text(prompts_dir / "showcase_03_lifestyle_B.txt", "\n".join(showcase_03))

    spec_common = [
        *global_constraints,
        "",
        "TYPE: Specs image background + product (text will be template-rendered).",
        "- Do NOT render any text inside the image.",
        "- Reserve a clean info bar area (~30% of canvas) at the bottom or side.",
        "- Keep safe margins >= 120px.",
        "- Ensure the info area has enough contrast for later text overlay.",
    ]
    _write_text(prompts_dir / "spec_01_dimensions_background.txt", "\n".join(spec_common + [
        "",
        "TEXT SOURCE (for later overlay): texts/spec_01.txt",
        "CONTENT: dimensions/structure emphasis.",
    ]))
    _write_text(prompts_dir / "spec_02_specs_background.txt", "\n".join(spec_common + [
        "",
        "TEXT SOURCE (for later overlay): texts/spec_02.txt",
        "CONTENT: key specs list emphasis.",
    ]))

    howto_common = [
        *global_constraints,
        "",
        "TYPE: How-to image background + product (text will be template-rendered).",
        "- Do NOT render any text inside the image.",
        "- Reserve a clean info area (~30% of canvas) for steps/tips.",
        "- Keep safe margins >= 120px.",
        "- Ensure the info area has enough contrast for later text overlay.",
    ]
    _write_text(prompts_dir / "howto_01_steps_background.txt", "\n".join(howto_common + [
        "",
        "TEXT SOURCE (for later overlay): texts/howto_01.txt",
        "CONTENT: steps/instructions.",
    ]))
    _write_text(prompts_dir / "howto_02_tips_background.txt", "\n".join(howto_common + [
        "",
        "TEXT SOURCE (for later overlay): texts/howto_02.txt",
        "CONTENT: tips/notice.",
    ]))

    # Meta.
    manifest = {
        "version": "0.2.0",
        "generated_at_utc": now_utc_iso(),
        "batch_id": safe_batch_id,
        "product": {
            "product_id": product.product_id,
            "safe_product_id": safe_product_id,
            "product_name_en": product.product_name_en,
            "style_pack": product.style_pack,
            "output_set": product.output_set,
        },
        "source_images": source_images,
        "expected_outputs": expected,
        "paths": {
            "showcase_dir": str(showcase_dir.relative_to(product_dir)),
            "spec_dir": str(spec_dir.relative_to(product_dir)),
            "howto_dir": str(howto_dir.relative_to(product_dir)),
            "source_dir": str(source_dir.relative_to(product_dir)),
            "prompts_dir": str(prompts_dir.relative_to(product_dir)),
            "texts_dir": str(texts_dir.relative_to(product_dir)),
            "meta_dir": str(meta_dir.relative_to(product_dir)),
        },
    }
    _write_json(product_dir / "manifest.json", manifest)

    qc = {
        "fail_fast": QC_FAIL_FAST,
        "reject_tags": QC_REJECT_TAGS,
        "notes": "If any fail_fast item fails, reject immediately.",
    }
    _write_json(meta_dir / "qc_checklist.json", qc)
    _write_text(meta_dir / "review_packet.md", _review_packet_text(product, expected))

    product_meta = {
        "generated_at_utc": now_utc_iso(),
        "product_id": product.product_id,
        "style_pack": product.style_pack,
        "units": product.units,
        "dimensions": {
            "l": product.dimensions_l,
            "w": product.dimensions_w,
            "h": product.dimensions_h,
        },
        "has_personalization_text": bool(product.personalization_text_en),
        "source_image_count": len(product.source_image_paths),
    }
    _write_json(meta_dir / "product.json", product_meta)

    return product_dir
