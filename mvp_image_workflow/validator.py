from __future__ import annotations

import json
from pathlib import Path

from .util import ValidationError, safe_id


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValidationError(f"Missing required file: {path}") from None
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {path}: {e}") from None

    if not isinstance(data, dict):
        raise ValidationError(f"Invalid JSON in {path}: expected an object")
    return data


def _validate_expected_filename(fname: str) -> None:
    if "/" in fname or "\\" in fname:
        raise ValidationError(f"Invalid expected filename (must not contain path separators): {fname}")
    p = Path(fname)
    if p.is_absolute() or p.name != fname:
        raise ValidationError(f"Invalid expected filename (must be a basename): {fname}")
    if fname in {"", ".", ".."}:
        raise ValidationError(f"Invalid expected filename: {fname}")
    if p.suffix.lower() != ".png":
        raise ValidationError(f"Invalid expected filename (must end with .png): {fname}")


def validate_product_package(product_dir: str | Path, require_images: bool) -> None:
    root = Path(product_dir)
    manifest_path = root / "manifest.json"
    manifest = _read_json(manifest_path)

    expected_layout = {
        "showcase_dir": root / "showcase",
        "spec_dir": root / "spec",
        "howto_dir": root / "howto",
        "source_dir": root / "source",
        "prompts_dir": root / "prompts",
        "texts_dir": root / "texts",
        "meta_dir": root / "meta",
    }
    prompts_dir = expected_layout["prompts_dir"]
    texts_dir = expected_layout["texts_dir"]
    meta_dir = expected_layout["meta_dir"]

    required_files = [
        manifest_path,
        prompts_dir / "showcase_01_clean_main.txt",
        prompts_dir / "showcase_02_lifestyle_A.txt",
        prompts_dir / "showcase_03_lifestyle_B.txt",
        prompts_dir / "spec_01_dimensions_background.txt",
        prompts_dir / "spec_02_specs_background.txt",
        prompts_dir / "howto_01_steps_background.txt",
        prompts_dir / "howto_02_tips_background.txt",
        texts_dir / "spec_01.txt",
        texts_dir / "spec_02.txt",
        texts_dir / "howto_01.txt",
        texts_dir / "howto_02.txt",
        meta_dir / "qc_checklist.json",
        meta_dir / "product.json",
    ]

    missing = [str(p) for p in required_files if not p.is_file()]
    if missing:
        raise ValidationError("Missing required files:\n- " + "\n- ".join(missing))

    manifest_product = manifest.get("product")
    if not isinstance(manifest_product, dict):
        raise ValidationError("manifest.json missing 'product' dict")
    manifest_product_id = manifest_product.get("product_id")
    if not isinstance(manifest_product_id, str) or not manifest_product_id:
        raise ValidationError("manifest.product.product_id must be a non-empty string")
    manifest_safe_product_id = manifest_product.get("safe_product_id")
    if not isinstance(manifest_safe_product_id, str) or not manifest_safe_product_id:
        raise ValidationError("manifest.product.safe_product_id must be a non-empty string")
    if safe_id(manifest_product_id) != manifest_safe_product_id:
        raise ValidationError("manifest.product.safe_product_id does not match manifest.product.product_id")
    if manifest_safe_product_id != root.name:
        raise ValidationError(
            f"manifest.product.safe_product_id ({manifest_safe_product_id}) does not match folder name ({root.name})"
        )

    product_meta = _read_json(meta_dir / "product.json")
    meta_product_id = product_meta.get("product_id")
    if meta_product_id != manifest_product_id:
        raise ValidationError("meta/product.json product_id does not match manifest.json")

    paths_config = manifest.get("paths")
    if not isinstance(paths_config, dict):
        raise ValidationError("manifest.json missing 'paths' dict")

    for key, expected_dir in expected_layout.items():
        rel_value = paths_config.get(key)
        if not isinstance(rel_value, str):
            raise ValidationError(f"manifest.paths.{key} must be a string")
        manifest_dir = root / rel_value
        if not manifest_dir.is_dir():
            raise ValidationError(f"manifest.paths.{key} points to missing directory: {manifest_dir}")
        if manifest_dir.resolve() != expected_dir.resolve():
            raise ValidationError(
                f"manifest.paths.{key} ({rel_value}) does not match the actual layout ({expected_dir.relative_to(root)})"
            )

    if not require_images:
        return

    expected_outputs = manifest.get("expected_outputs")
    if not isinstance(expected_outputs, dict):
        raise ValidationError("manifest.json missing 'expected_outputs' dict")

    expected_counts = {
        "showcase": 3,
        "spec": 2,
        "howto": 2,
    }
    for category, expected_count in expected_counts.items():
        files = expected_outputs.get(category)
        if not isinstance(files, list):
            raise ValidationError(f"manifest.json expected_outputs.{category} must be a list")
        if len(files) != expected_count:
            raise ValidationError(
                f"manifest.json expected_outputs.{category} must contain {expected_count} file(s)"
            )
        if len(set(files)) != len(files):
            raise ValidationError(f"manifest.json expected_outputs.{category} contains duplicate filenames")

        category_dir = expected_layout[f"{category}_dir"]
        if not category_dir.is_dir():
            raise ValidationError(f"Missing expected category folder: {category_dir}")
        for fname in files:
            if not isinstance(fname, str):
                raise ValidationError(f"manifest.json expected_outputs.{category} contains non-string")
            _validate_expected_filename(fname)
            if not (category_dir / fname).is_file():
                raise ValidationError(f"Missing expected image: {category_dir / fname}")
