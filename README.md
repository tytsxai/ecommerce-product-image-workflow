# E-commerce Product Image Workflow (Phase 1: Image Assets)

[![Docs](https://img.shields.io/badge/docs-github%20pages-0969da?logo=github)](https://tytsxai.github.io/ecommerce-product-image-workflow/)
[![Release](https://img.shields.io/github/v/release/tytsxai/ecommerce-product-image-workflow)](https://github.com/tytsxai/ecommerce-product-image-workflow/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/tytsxai/ecommerce-product-image-workflow)](https://github.com/tytsxai/ecommerce-product-image-workflow/commits/main)

[中文说明](README.zh-CN.md) · [Docs Site](https://tytsxai.github.io/ecommerce-product-image-workflow/) · [Quick Start](docs/en/quickstart.md) · [llms.txt](llms.txt) · [Issues](https://github.com/tytsxai/ecommerce-product-image-workflow/issues)

> **Keywords**: e-commerce product image workflow · AI product photography pipeline · supplier image to hero image · AI 商品图工作流 · 电商商品图 AI 生成 · 供应商图改造电商主图 · Midjourney 电商商品图 · Flux 商品图 prompt · SDXL 电商主图模板 · brand-consistent e-commerce images · alternative to Canva templates for e-commerce

A practical, **non-technical-friendly workflow** for transforming supplier product images into publish-ready e-commerce assets while enforcing:

- **Product consistency** (same product identity)
- **Visual differentiation** (new background/composition)
- **Text control** (English-only output text)
- **Reviewability** (clear QA and rejection reasons)

## Screenshots

### Workflow Overview

![Workflow Overview Placeholder](docs/assets/screenshots/workflow-overview.svg)

### Manager Input Template

![Manager Form Placeholder](docs/assets/screenshots/manager-form-preview.svg)

### QA Checklist Template

![QA Checklist Placeholder](docs/assets/screenshots/qa-checklist-preview.svg)

> These are placeholders. Replace with real screenshots from your production pipeline.

## Why this project

Many stores rely on supplier images that are visually repetitive and hard to brand. This workflow gives teams a reproducible way to generate:

1. Showcase images (hero/lifestyle)
2. Spec images (dimensions/spec text)
3. How-to images (instructional visual cards)

without drifting from the actual product.

## Who this is for

- E-commerce managers
- Content operation teams
- Creative production vendors
- Automation builders integrating AI image pipelines

## Repository structure

```text
.
├── docs/
│   ├── en/
│   ├── zh-CN/
│   └── assets/
├── templates/
├── prompts/
├── examples/
└── .github/
```

## Quick start

1. Read `docs/en/quickstart.md`
2. Fill `templates/manager_input_form.csv`
3. Select or edit a style pack in `templates/style_packs.example.json`
4. Use prompt templates under `prompts/`
5. Validate output with `templates/qa_checklist.csv`
6. Log each batch in `templates/batch_record.csv`

## Documentation site (GitHub Pages)

- Site URL: `https://tytsxai.github.io/ecommerce-product-image-workflow/`
- Publishing source: GitHub Pages from `main` branch `docs/` folder
- Optional local docs build: `mkdocs build` with `mkdocs.yml`

## Core principles

- **Same product, different scene**: the product must remain accurate, but background/composition should change.
- **Deterministic text handling**: spec/how-to text should be template-rendered when possible.
- **Fail fast QA**: one-vote rejection criteria are explicit and auditable.
- **Compliance first**: only use commercially licensed fonts/assets.

## FAQ

**Which image model should I use?** Model-agnostic. Midjourney, Flux (dev/schnell), SDXL, Imagen, DALL-E — pick based on your platform's commercial-use terms and visual fit.

**Is the output commercially usable?** Depends on the underlying model's license and your jurisdiction. The QA checklist enforces commercial-only fonts/assets, but you must verify the AI model output license yourself.

**How is this different from Canva templates or Photoshop actions?** Those are *tools*. This is a *workflow specification*: it defines which artifacts exist, what each must contain, and which gates content must pass before publishing. Generation can happen in any tool.

**Can I plug it into n8n / Make / Zapier?** Yes — that's Phase 2 by design. CSVs and prompt templates are machine-readable.

**Non-technical team — can they actually use this?** Yes, this is the design constraint. Managers fill a CSV, operators run prompts, QA uses a checklist. No code required.

**Is this affiliated with any e-commerce platform?** No. The workflow is platform-agnostic (Shopify, Amazon, Temu, Shopee, Etsy — same workflow).

## Limitations

- This repo provides workflow specifications and operational templates, not model weights.
- Not legal advice. You must review platform policies and local regulations.

## Roadmap

- [ ] Add visual QA reference examples (pass/fail image pairs)
- [ ] Add multilingual manager forms (EN/RU/ES)
- [ ] Publish automation adapters (n8n / Make / Zapier)
- [ ] Add CI checks for template schema consistency

## License

MIT (see `LICENSE`).
