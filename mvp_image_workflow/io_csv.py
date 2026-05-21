from __future__ import annotations

import csv
from pathlib import Path

from .batch import DEFAULT_OUTPUT_SET, DEFAULT_STYLE_PACK, ProductRow
from .util import ValidationError, optional_text, require_english_text, safe_id


def _pick_list(prefix: str, row: dict[str, str], max_items: int) -> list[str]:
    items: list[str] = []
    for i in range(1, max_items + 1):
        v = (row.get(f"{prefix}_{i}") or "").strip()
        if v:
            items.append(v)
    return items


def read_products_csv(path: str | Path) -> list[ProductRow]:
    p = Path(path)
    if not p.exists():
        raise ValidationError(f"Input CSV not found: {p}")

    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValidationError("CSV has no header row.")

        products: list[ProductRow] = []
        for idx, row in enumerate(reader, start=2):
            try:
                product_id = (row.get("product_id") or "").strip()
                if not product_id:
                    raise ValidationError("Missing required field: product_id")
                sid = safe_id(product_id)
                if sid != product_id:
                    raise ValidationError(
                        "product_id contains unsafe characters; allowed: letters, numbers, '-' and '_'"
                    )

                product_name_en = require_english_text("product_name_en", row.get("product_name_en", ""))

                style_pack = (row.get("style_pack") or DEFAULT_STYLE_PACK).strip() or DEFAULT_STYLE_PACK
                output_set = (row.get("output_set") or DEFAULT_OUTPUT_SET).strip().lower() or DEFAULT_OUTPUT_SET
                if output_set not in {"minimum"}:
                    raise ValidationError(
                        f"Unsupported output_set '{output_set}' (MVP supports: minimum)"
                    )

                units = (row.get("units") or "cm").strip().lower() or "cm"
                if units not in {"cm", "in"}:
                    raise ValidationError("units must be 'cm' or 'in'")

                dimensions_l = optional_text(row.get("dimensions_l"))
                dimensions_w = optional_text(row.get("dimensions_w"))
                dimensions_h = optional_text(row.get("dimensions_h"))

                specs_raw = _pick_list("spec", row, max_items=8)
                specs = tuple(require_english_text(f"spec_{i+1}", s) for i, s in enumerate(specs_raw))
                if len(specs) < 3:
                    raise ValidationError("Need at least 3 specs (spec_1..spec_8).")

                howto_title = require_english_text(
                    "howto_title", (row.get("howto_title") or "How to Use")
                )
                steps_raw = _pick_list("step", row, max_items=6)
                steps = tuple(require_english_text(f"step_{i+1}", s) for i, s in enumerate(steps_raw))
                if len(steps) < 3:
                    raise ValidationError("Need at least 3 steps (step_1..step_6).")

                tips_raw = _pick_list("tip", row, max_items=4)
                tips = tuple(require_english_text(f"tip_{i+1}", t) for i, t in enumerate(tips_raw))

                manager_notes = optional_text(row.get("manager_notes"))
                must_have_keywords = optional_text(row.get("must_have_keywords"))
                must_avoid_elements = optional_text(row.get("must_avoid_elements"))

                personalization_text_en = optional_text(row.get("personalization_text_en"))
                if personalization_text_en is not None:
                    personalization_text_en = require_english_text(
                        "personalization_text_en", personalization_text_en
                    )

                products.append(
                    ProductRow(
                        product_id=product_id,
                        product_name_en=product_name_en,
                        style_pack=style_pack,
                        output_set=output_set,
                        units=units,
                        dimensions_l=dimensions_l,
                        dimensions_w=dimensions_w,
                        dimensions_h=dimensions_h,
                        specs=specs,
                        howto_title=howto_title,
                        steps=steps,
                        tips=tips,
                        manager_notes=manager_notes,
                        must_have_keywords=must_have_keywords,
                        must_avoid_elements=must_avoid_elements,
                        personalization_text_en=personalization_text_en,
                    )
                )
            except ValidationError as e:
                raise ValidationError(f"CSV line {idx}: {e}") from None

    if not products:
        raise ValidationError("CSV has no product rows.")
    return products
