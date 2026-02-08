# Quick Start

## 1) Prepare inputs

Use `templates/manager_input_form.csv` and provide:

- product SKU
- supplier image paths
- optional spec/how-to source text
- target style pack

## 2) Run generation pipeline

This repo is tool-agnostic. You can implement pipeline via:

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
