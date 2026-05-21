# Local Web Workbench

The web workbench is the product-facing layer for non-technical operators. It keeps the existing CLI/package contract, but wraps it in a local UI for intake, model selection, generation, QA review, retry, and export.

## Run Locally

Install the Python web extras:

```bash
python3 -m pip install -e ".[web]"
```

Build the frontend once:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start the local workbench:

```bash
python3 -m ecommerce_product_image_workflow.web
```

Default URL: `http://127.0.0.1:8787`

Use `EPI_WORKFLOW_HOME=/path/to/local/state` to choose where SQLite data, uploads, generated assets, and exports are stored.

## Operator Flow

1. Create or open a batch.
2. Add a product with SKU, English name, specs, steps, and style pack.
3. Upload supplier/source images.
4. Choose a provider and model.
5. Click Generate.
6. Review generated assets against supplier images.
7. Pass, reject, or retry individual assets.
8. Export QA-approved assets as a ZIP.

The main UI uses product language: project, batch, product, style, model, generation, review, export. Manifest files and prompt paths remain available as technical artifacts, but are not required for ordinary operation.

## Built-in Providers

- `local_mock`: offline placeholder image generator for demo and tests.
- `generic_http`: configurable HTTP image API adapter for custom or self-hosted models.
- `openai_images`: provider metadata/template for OpenAI image models.
- `replicate`: provider metadata/template for Replicate-hosted models.
- `comfyui_http`: provider metadata/template for local or server-hosted ComfyUI.

Only `local_mock` and `generic_http` are directly runnable without extending provider code. The hosted provider entries are intentionally present as integration starting points so teams can wire their own production API contracts without storing raw secrets in exported workflow files.

For `generic_http`, configure:

```json
{
  "endpoint_url": "https://example.com/generate",
  "api_key_env": "MY_IMAGE_API_KEY",
  "response_image_field": "image_base64"
}
```

Raw API keys must not be sent in the UI JSON. Store keys in environment variables and reference them through `api_key_env`.

## API Surface

The workbench exposes:

- `POST /api/batches`
- `POST /api/batches/{id}/products`
- `POST /api/products/{id}/source-images`
- `GET /api/style-packs`
- `GET /api/providers`
- `POST /api/providers/test`
- `POST /api/batches/{id}/generate`
- `GET /api/jobs/{id}`
- `POST /api/assets/{id}/review`
- `POST /api/assets/{id}/retry`
- `POST /api/batches/{id}/export`

Jobs use these statuses: `queued`, `running`, `succeeded`, `failed`, `cancelled`.

## QA and Rendering

Showcase images are saved directly from the selected provider.

Spec and how-to outputs are rendered with a deterministic local text overlay using Pillow. The model generates the product/background layer; the workflow renders English text from the product package text sources.

The export ZIP includes only QA-approved assets plus batch manifest, QA review CSV, and a short operator runbook.
