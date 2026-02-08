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
