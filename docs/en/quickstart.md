# Quick Start

## 1) Prepare inputs

Use `templates/manager_input_form.csv` and provide:

- product SKU
- supplier image paths
- optional spec/how-to source text
- target style pack

## 2) Run generation pipeline

This repo is tool-agnostic. You can implement pipeline via:

- the local MVP CLI in this repository
- n8n / Make / Zapier
- internal scripts
- manual AI tool operations

Suggested stages:

1. intake validation
2. product lock generation
3. text-safe rendering for spec/how-to cards
4. QA checks
5. export and batch logging

## 3) Validate outputs

Use `templates/qa_checklist.csv`.

Fail immediately if:

- product shape/color is changed
- scene is too similar to supplier image
- non-English text appears in output
- spec values are wrong

## 4) Export and track

Use naming convention:

`{sku}_{image_type}_{style_pack}_{version}.png`

Log everything in `templates/batch_record.csv`.

## MVP CLI (Python)

Use the MVP when you want a concrete local package for each product before image generation. It creates prompt files, text-source files, expected output names, and a `manifest.json`.

```bash
python3 -m mvp_image_workflow generate \
  --input examples/products_minimum.csv \
  --out out_mvp \
  --batch-id 2026-05A
```

Validate the generated package:

```bash
python3 -m mvp_image_workflow validate --out out_mvp
```

Require expected image files during final QA:

```bash
python3 -m mvp_image_workflow validate --out out_mvp --require-images
```
