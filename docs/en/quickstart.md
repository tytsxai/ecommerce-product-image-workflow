# Quick Start

This guide helps a new user run the real local paths in this repository:

- **MVP CLI**: generate prompt/text/manifest packages from a CSV.
- **Local Web Workbench**: operate batches in a browser with uploads, provider selection, generation jobs, QA review, retry, and export.

The project is model-agnostic. The CLI prepares production artifacts; it does not call an image model. The web workbench can use the built-in `local_mock` provider for demos or `generic_http` for a compatible image-generation API.

## 1) Choose Your Path

Use the CLI when you want a reproducible folder package for each product before image generation.

Use the web workbench when non-technical operators need a browser UI for intake, review, retry, and export.

## 2) Prepare Inputs

Start with the runnable sample:

```text
examples/products_minimum.csv
```

The CSV contains fields for:

- `product_id`
- `product_name_en`
- `style_pack`
- `output_set`
- dimensions and units
- `spec_1`, `spec_2`, `spec_3`, optional `spec_4`
- how-to title, steps, and tips
- optional `source_image_paths`

Style packs are loaded from:

```text
templates/style_packs.example.json
```

## 3) Run the MVP CLI

Install the package from the repository root:

```bash
python3 -m pip install -e .
```

Inspect the sample CSV and style pack coverage:

```bash
python3 -m mvp_image_workflow inspect \
  --input examples/products_minimum.csv
```

Generate a batch package:

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

When final PNG files have been produced and placed in the expected folders, require image presence:

```bash
python3 -m mvp_image_workflow validate --out out_mvp --require-images
```

If your CSV contains local supplier image paths in `source_image_paths` or `supplier_image_paths`, copy them into each package and record hashes:

```bash
python3 -m mvp_image_workflow generate \
  --input examples/products_minimum.csv \
  --out out_mvp \
  --batch-id 2026-05A \
  --copy-source-images
```

## 4) Run the Local Web Workbench

Install Python web extras:

```bash
python3 -m pip install -e ".[web]"
```

Build the frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start the workbench:

```bash
python3 -m ecommerce_product_image_workflow.web
```

Open:

```text
http://127.0.0.1:8787
```

Optional local state path:

```bash
EPI_WORKFLOW_HOME=/path/to/local/state python3 -m ecommerce_product_image_workflow.web
```

## 5) Validate and Export

Use `templates/qa_checklist.csv` or the web workbench review UI.

Fail immediately if:

- product shape, structure, color, material, or ratio changed
- background is too similar to the supplier image
- visible text is not English, except immutable brand trademarks
- spec values, units, or meaning changed
- how-to steps no longer match the source meaning

Recommended final naming convention:

```text
{sku}_{image_type}_{style_pack}_{version}.png
```

The CLI package and web export both preserve batch-level audit artifacts so reviewers can trace outputs back to inputs.

## 6) Next Docs

- [MVP CLI](mvp-cli.md)
- [Local Web Workbench](web-workbench.md)
- [End-to-End Workflow](workflow.md)
- [Quality Gate](quality-gate.md)
- [Risk & Compliance](compliance.md)
- [FAQ](faq.md)
