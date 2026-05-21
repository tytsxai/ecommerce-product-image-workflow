from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from .generator import generate_product_package
from .io_csv import read_products_csv
from .reporting import write_batch_artifacts
from .stylepacks import default_style_pack_path, load_style_packs, validate_product_style_packs
from .util import ValidationError, safe_id
from .validator import validate_product_package


def _style_pack_path_from_args(args: argparse.Namespace) -> Path | None:
    if getattr(args, "no_style_pack_check", False):
        return None
    explicit = getattr(args, "style_packs", None)
    if explicit:
        return Path(explicit)
    default_path = default_style_pack_path()
    return default_path if default_path.exists() else None


def _load_style_packs_for_products(args: argparse.Namespace, products) -> dict:
    if getattr(args, "no_style_pack_check", False):
        return {}
    style_pack_path = _style_pack_path_from_args(args)
    if style_pack_path is None:
        return {}
    style_packs = load_style_packs(style_pack_path)
    validate_product_style_packs({p.style_pack for p in products}, style_packs)
    return style_packs


def _cmd_generate(args: argparse.Namespace) -> int:
    products = read_products_csv(args.input)
    style_packs = _load_style_packs_for_products(args, products)
    style_pack_path = _style_pack_path_from_args(args)
    out_root = Path(args.out)

    if out_root.exists() and not out_root.is_dir():
        raise ValidationError(f"Output root must be a directory: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    seen_product_ids: set[str] = set()
    for p in products:
        if p.product_id in seen_product_ids:
            raise ValidationError(f"Duplicate product_id in CSV: '{p.product_id}'")
        seen_product_ids.add(p.product_id)

    created: list[Path] = []
    for p in products:
        created.append(
            generate_product_package(
                p,
                out_root,
                batch_id=args.batch_id,
                style_pack=style_packs.get(p.style_pack),
                source_base_dir=Path(args.input).resolve().parent,
                copy_source_images=args.copy_source_images,
            )
        )

    write_batch_artifacts(
        out_root,
        products,
        created,
        batch_id=args.batch_id,
        style_pack_file=style_pack_path,
    )

    print(f"Generated {len(created)} product package(s) in {out_root}")
    print(f"Batch artifacts: {out_root / 'batch_manifest.json'}, {out_root / 'qa_review.csv'}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    products = read_products_csv(args.input)
    style_packs = _load_style_packs_for_products(args, products)
    style_counts: dict[str, int] = {}
    output_counts: dict[str, int] = {}
    source_rows = 0
    for product in products:
        style_counts[product.style_pack] = style_counts.get(product.style_pack, 0) + 1
        output_counts[product.output_set] = output_counts.get(product.output_set, 0) + 1
        if product.source_image_paths:
            source_rows += 1

    print(f"Products: {len(products)}")
    print("Output sets: " + ", ".join(f"{k}={v}" for k, v in sorted(output_counts.items())))
    print("Style packs: " + ", ".join(f"{k}={v}" for k, v in sorted(style_counts.items())))
    print(f"Rows with source image references: {source_rows}")
    if style_packs:
        print(f"Style pack file OK: {_style_pack_path_from_args(args)}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    out_root = Path(args.out)
    if not out_root.exists():
        raise ValidationError(f"Output root not found: {out_root}")
    if not out_root.is_dir():
        raise ValidationError(f"Output root must be a directory: {out_root}")

    if args.product_id:
        raw = args.product_id.strip()
        sid = safe_id(raw)
        if not sid or sid != raw:
            raise ValidationError(
                "product_id contains unsafe characters; allowed: letters, numbers, '-' and '_'"
            )
        product_dir = out_root / sid
        validate_product_package(product_dir, require_images=args.require_images)
        print(f"OK: {product_dir}")
        return 0

    # Validate all product folders that have a manifest.json.
    manifests = list(out_root.glob("*/manifest.json"))
    if not manifests:
        raise ValidationError(f"No product manifests found under: {out_root}")

    for m in manifests:
        validate_product_package(m.parent, require_images=args.require_images)
    print(f"OK: validated {len(manifests)} product package(s) under {out_root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mvp_image_workflow")
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Generate per-product prompt/text packages")
    g.add_argument("--input", required=True, help="CSV file (utf-8) with product rows")
    g.add_argument("--out", required=True, help="Output root folder")
    g.add_argument(
        "--batch-id",
        default=None,
        help="Optional batch id appended to expected image filenames (e.g. 2025-12-26A)",
    )
    g.add_argument(
        "--style-packs",
        default=None,
        help="Style pack JSON file. Defaults to templates/style_packs.example.json when present.",
    )
    g.add_argument(
        "--no-style-pack-check",
        action="store_true",
        help="Skip style_pack existence/schema validation.",
    )
    g.add_argument(
        "--copy-source-images",
        action="store_true",
        help="Copy local source/supplier images referenced by the CSV into each product package.",
    )
    g.set_defaults(func=_cmd_generate)

    i = sub.add_parser("inspect", help="Inspect CSV inputs and style pack coverage")
    i.add_argument("--input", required=True, help="CSV file (utf-8) with product rows")
    i.add_argument(
        "--style-packs",
        default=None,
        help="Style pack JSON file. Defaults to templates/style_packs.example.json when present.",
    )
    i.add_argument(
        "--no-style-pack-check",
        action="store_true",
        help="Skip style_pack existence/schema validation.",
    )
    i.set_defaults(func=_cmd_inspect)

    v = sub.add_parser("validate", help="Validate generated packages")
    v.add_argument("--out", required=True, help="Output root folder")
    v.add_argument("--product-id", default=None, help="Validate a single product id")
    v.add_argument(
        "--require-images",
        action="store_true",
        help="Also require expected .png images to exist",
    )
    v.set_defaults(func=_cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ValidationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130
    except Exception as e:
        if os.environ.get("MVP_IMAGE_WORKFLOW_DEBUG") == "1":
            traceback.print_exc()
        else:
            print(f"FATAL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
