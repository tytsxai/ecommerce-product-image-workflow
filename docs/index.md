# E-commerce Product Image Workflow

E-commerce Product Image Workflow is an open-source, model-agnostic workflow and local toolset for AI-assisted e-commerce product image production.

It helps teams convert supplier product photos and product data into structured prompt packages, QA records, and export-ready workflows for showcase images, specification cards, and how-to images.

中文：这是一个电商商品图 AI 工作流项目，用 CSV、风格包、提示词模板、QA 清单、Python CLI 和本地 Web 工作台，让供应商图改造成可复核、可退回、可交付的商品图片生产流程。

## Project facts

| Item | Details |
| --- | --- |
| Project category | AI product photography workflow, e-commerce image production tooling, local workbench |
| Main problem | Make supplier product photos and product data usable in a repeatable image-generation and QA process |
| Current tools | Python CLI, FastAPI + SQLite backend, React/Vite UI, CSV/JSON templates, style packs, QA checklist |
| Directly runnable providers | `local_mock` for no-API-key demos; `generic_http` for compatible image-generation APIs |
| Current boundary | No model weights, no hosted SaaS service, no automatic commercial-rights guarantee |
| Best search phrases | e-commerce product image workflow, AI product photography workflow, supplier image to hero image, product image QA checklist |

## Best for

- e-commerce managers and content operations teams
- creative production vendors
- developers and automation engineers building AI product photography pipelines
- local proof-of-concepts before connecting image-generation APIs or automation tools

## What you can run today

- Generate a reviewable product image package from `examples/products_minimum.csv`.
- Validate prompt/text/manifest folder structure before handoff.
- Start a local browser workbench at `http://127.0.0.1:8787`.
- Use `local_mock` to create placeholder images without API keys.
- Use `generic_http` to call a compatible image-generation endpoint that returns a base64 image field.

## Start here

- [Quick Start](en/quickstart.md)
- [Web Workbench](en/web-workbench.md)
- [MVP CLI](en/mvp-cli.md)
- [End-to-End Workflow](en/workflow.md)
- [Quality Gate](en/quality-gate.md)
- [Risk & Compliance](en/compliance.md)
- [FAQ](en/faq.md)

## Docs deployment

The public documentation site is built from `mkdocs.yml` and deployed to GitHub Pages by the `Deploy Docs` workflow after changes land on `main`.

## Chinese docs

- [中文导航](zh-CN/README.md)
- [原始参考文档目录](zh-CN/reference/README.md)

## Search keywords

AI product photography workflow, e-commerce product image workflow, supplier image to hero image, product image QA checklist, brand-consistent product images, 电商商品图 AI 工作流, 供应商图改造电商主图, 商品图提示词模板, AI 商品图质检清单.
