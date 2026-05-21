from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductRow:
    product_id: str
    product_name_en: str
    style_pack: str
    output_set: str

    units: str  # "cm" | "in"
    dimensions_l: str | None
    dimensions_w: str | None
    dimensions_h: str | None

    specs: tuple[str, ...]
    howto_title: str
    steps: tuple[str, ...]
    tips: tuple[str, ...]

    manager_notes: str | None
    must_have_keywords: str | None
    must_avoid_elements: str | None

    personalization_text_en: str | None


DEFAULT_STYLE_PACK = "minimal_white"
DEFAULT_OUTPUT_SET = "minimum"
