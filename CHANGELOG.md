# Changelog

## Unreleased

### Added

- Local web workbench with FastAPI, SQLite, local file storage, and React/Vite frontend.
- Provider abstraction for `local_mock`, `generic_http`, `openai_images`, `replicate`, and `comfyui_http`.
- Async generation jobs, QA review, retry, and approved-assets ZIP export.
- Pillow-based deterministic text overlay for spec/how-to cards.
- Web API tests covering batch creation, product intake, upload, generation, review, retry, export, provider config safety, and rendering.

## 1.1.1 - 2026-05-19

### Added (Documentation)

- **`llms.txt`** — AI-search-engine index covering what the workflow provides, model-agnostic positioning, and explicit non-goals (no model weights, no automation runtime, no legal advice, no fonts/assets shipped).
- **README — bilingual keyword block** + nav row (llms.txt / Issues).
- **README — 6-question FAQ** clarifying model agnosticism, commercial usability caveat, Canva/Photoshop comparison, n8n/Make/Zapier integration path, platform-agnostic positioning.

### Notes

Documentation-only release. Templates, prompts, and QA checklist are unchanged from 1.1.0.

## 1.1.0 - 2026-02-09

- Added bilingual repository badges for docs/release/license visibility.
- Added screenshot placeholder assets for workflow, manager input, and QA checklist.
- Added MkDocs configuration (`mkdocs.yml`) and docs dependency file (`requirements-docs.txt`).
- Enabled GitHub Pages documentation publishing from `main/docs`.
- Added docs landing page (`docs/index.md`) and contributing doc entry (`docs/en/contributing.md`).

## 1.0.0 - 2026-02-08

- Initial open-source release.
- Added English and Chinese READMEs.
- Added reusable templates for manager input, QA, style packs, and batch tracking.
- Added contribution, security, and governance files.
- Imported original Chinese reference documentation into `docs/zh-CN/reference/`.
