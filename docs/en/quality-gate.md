# Quality Gate

## Fail-fast rules

1. Product identity mismatch
2. Background too similar to source
3. Non-English output text
4. Incorrect spec values/units
5. How-to meaning drift

## Suggested rejection tags

- `product_changed`
- `background_too_similar`
- `text_not_english`
- `spec_value_error`
- `howto_meaning_changed`
- `low_realism`

## Audit minimum

- source image hash or filename
- style pack ID and version
- exported asset names
- reviewer decision and reason
- latest review decision determines export eligibility

## CLI-supported artifacts

The MVP CLI creates review-ready audit files:

- `batch_manifest.json`: batch ID, product folders, expected output counts, style pack file
- `manifest.json`: per-product expected outputs, source image references, folder layout
- `meta/review_packet.md`: per-product fail-fast review packet
- `qa_review.csv`: one row per expected PNG, with decision, reject tag, reviewer, timestamp, and notes

Before final handoff, run:

```bash
python3 -m mvp_image_workflow validate --out out_mvp --require-images
```

In the web workbench, reviewers can pass, reject, or retry each generated asset. Exported ZIP files include only approved assets.

## Web workbench production checks

- Reject duplicate product IDs in a batch before generation.
- Reject unreadable or unsupported source image uploads before saving them.
- Do not queue duplicate generation jobs while a batch has active work.
- Keep retry outputs versioned so approved files are not overwritten by unreviewed retries.
- Before handoff, export only assets whose latest review decision is `pass`.
