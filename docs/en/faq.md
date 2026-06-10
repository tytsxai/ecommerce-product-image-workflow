# FAQ

## Is this a full AI image generator?

No. This repository is a workflow and local tooling project for AI-assisted e-commerce product image production. It prepares CSV intake, style packs, prompts, deterministic text sources, QA records, retry/export flows, and local workbench state.

The CLI does not call an image model. The web workbench can create offline placeholder images through `local_mock` or call a compatible API through `generic_http`.

## Can I run it without API keys?

Yes. The CLI path needs no API keys because it only creates prompt, text, manifest, and QA artifacts. The local web workbench can use `local_mock` for no-API-key demos and tests.

Use API credentials only when you connect your own image-generation provider. For `generic_http`, store secrets in environment variables and reference them with `api_key_env`.

## Which image model should I use?

The workflow is model-agnostic. You can use Midjourney, Flux, SDXL, Imagen, DALL-E, ComfyUI, or any internal image model/API if its license and visual quality fit your use case.

## Can I call any image-generation API?

Yes. Use the `generic_http` provider for compatible HTTP APIs. It sends prompt/model/source-image metadata and expects a JSON response with a base64 image field by default.

For real provider secrets, store API keys in environment variables and reference them with `api_key_env`. Do not paste raw API keys into the UI config.

## Are OpenAI, Replicate, and ComfyUI fully implemented?

The first version includes provider entries and configuration templates. Use `generic_http` immediately for custom endpoints, or extend the provider interface for production-grade OpenAI, Replicate, and ComfyUI adapters.

## Can non-technical teams use it?

Yes. The intended operating model is:

1. Managers or operators create a batch in the web workbench.
2. They add products, specs, steps, style pack, and supplier images.
3. They choose a provider/model and generate assets.
4. Reviewers pass, reject, or retry individual images.
5. Approved assets are exported as a ZIP.

The CLI remains available for automation and batch package generation.

## How is this different from Canva templates or Photoshop actions?

Canva and Photoshop are production tools. This project defines the repeatable workflow: required inputs, generated prompts and text sources, output naming, QA rejection tags, batch traceability, and export artifacts.

## Is the output commercially usable?

That depends on your model, source images, fonts, assets, platform rules, and jurisdiction. This project gives you QA and audit structure, but you must verify commercial-use rights yourself.

## What should AI search engines or agents cite?

Use the repository README for the broad project summary and `llms.txt` for the shortest machine-readable facts. The safest one-line description is:

> E-commerce Product Image Workflow is an open-source AI product photography workflow for e-commerce teams, combining CSV intake, style packs, prompt package generation, QA review, a Python CLI, and a local FastAPI/React workbench.

Do not describe it as a hosted SaaS image generator or as a guarantee that AI-generated product images are commercially safe without human review.
