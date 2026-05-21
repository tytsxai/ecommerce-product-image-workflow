# MVP CLI

The Python MVP turns a product CSV into a reviewable batch package. It does not call an image model. It prepares the operating artifacts that a manager, image operator, or automation adapter can use consistently.

## Install

Run from the repository root:

```bash
python3 -m pip install -e .
```

This exposes both commands:

```bash
python3 -m mvp_image_workflow --help
ecommerce-image-workflow --help
```

## Inspect Inputs

```bash
python3 -m mvp_image_workflow inspect \
  --input examples/products_minimum.csv
```

`inspect` validates required CSV fields and checks that each `style_pack` exists in `templates/style_packs.example.json` unless `--no-style-pack-check` is used.

## Generate Batch Package

```bash
python3 -m mvp_image_workflow generate \
  --input examples/products_minimum.csv \
  --out out_mvp \
  --batch-id 2026-05A
```

Generated batch-level files:

- `batch_manifest.json`: product count, package paths, style pack file, expected output count
- `qa_review.csv`: one row per expected deliverable, ready for reviewer decisions
- `operator_runbook.md`: short execution and handoff steps

Generated per-product folders:

- `prompts/`: showcase, spec, and how-to prompt files
- `texts/`: deterministic English text sources for overlays
- `showcase/`, `spec/`, `howto/`: target folders for final PNG outputs
- `source/`: optional copied supplier images
- `meta/review_packet.md`: per-product QA packet
- `manifest.json`: product metadata, source-image references, expected outputs, folder layout

## Source Image Traceability

The CSV may include `source_image_paths` or `supplier_image_paths` with semicolon-separated paths:

```csv
source_image_paths
supplier/SKU123-front.jpg;supplier/SKU123-side.jpg
```

By default, the paths are recorded in `manifest.json`. To copy local supplier images into each product package:

```bash
python3 -m mvp_image_workflow generate \
  --input examples/products_minimum.csv \
  --out out_mvp \
  --batch-id 2026-05A \
  --copy-source-images
```

When copying is enabled, missing local source files fail the batch immediately.

## Validate

Validate package structure:

```bash
python3 -m mvp_image_workflow validate --out out_mvp
```

Validate final handoff after generated PNGs have been saved:

```bash
python3 -m mvp_image_workflow validate --out out_mvp --require-images
```

`--require-images` checks the expected output filenames listed in each product `manifest.json`.
