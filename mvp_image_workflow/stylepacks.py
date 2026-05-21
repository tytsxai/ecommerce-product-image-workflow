from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .util import ValidationError, safe_id


@dataclass(frozen=True)
class StylePack:
    pack_id: str
    scene: str
    lighting: str
    tone: str
    props: tuple[str, ...]
    forbidden: tuple[str, ...]


def default_style_pack_path() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "style_packs.example.json"


def _require_string(obj: dict, field: str, pack_id: str) -> str:
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"style pack '{pack_id}' missing non-empty string field: {field}")
    return value.strip()


def _require_string_list(obj: dict, field: str, pack_id: str) -> tuple[str, ...]:
    value = obj.get(field)
    if not isinstance(value, list):
        raise ValidationError(f"style pack '{pack_id}' field '{field}' must be a list")
    items: list[str] = []
    for idx, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"style pack '{pack_id}' field '{field}[{idx}]' must be a non-empty string")
        items.append(item.strip())
    return tuple(items)


def load_style_packs(path: str | Path) -> dict[str, StylePack]:
    p = Path(path)
    if not p.exists():
        raise ValidationError(f"Style pack file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in style pack file {p}: {e}") from None
    if not isinstance(data, dict):
        raise ValidationError(f"Invalid style pack file {p}: expected JSON object")

    raw_packs = data.get("style_packs")
    if not isinstance(raw_packs, list) or not raw_packs:
        raise ValidationError(f"Style pack file {p} must contain a non-empty 'style_packs' list")

    packs: dict[str, StylePack] = {}
    for idx, raw in enumerate(raw_packs, start=1):
        if not isinstance(raw, dict):
            raise ValidationError(f"style_packs[{idx}] must be an object")
        pack_id = _require_string(raw, "pack_id", f"#{idx}")
        if safe_id(pack_id) != pack_id:
            raise ValidationError(
                f"style pack '{pack_id}' uses unsafe pack_id; allowed: letters, numbers, '-' and '_'"
            )
        if pack_id in packs:
            raise ValidationError(f"Duplicate style pack id: {pack_id}")

        packs[pack_id] = StylePack(
            pack_id=pack_id,
            scene=_require_string(raw, "scene", pack_id),
            lighting=_require_string(raw, "lighting", pack_id),
            tone=_require_string(raw, "tone", pack_id),
            props=_require_string_list(raw, "props", pack_id),
            forbidden=_require_string_list(raw, "forbidden", pack_id),
        )

    return packs


def validate_product_style_packs(product_style_ids: set[str], style_packs: dict[str, StylePack]) -> None:
    missing = sorted(product_style_ids - set(style_packs))
    if missing:
        available = ", ".join(sorted(style_packs)) or "(none)"
        raise ValidationError(
            "Unknown style_pack value(s): "
            + ", ".join(missing)
            + f". Available style packs: {available}"
        )


def style_pack_prompt_lines(style_pack: StylePack | None, fallback_id: str) -> list[str]:
    if style_pack is None:
        return [f"Style pack: {fallback_id}"]
    lines = [
        f"Style pack: {style_pack.pack_id}",
        f"- Scene: {style_pack.scene}",
        f"- Lighting: {style_pack.lighting}",
        f"- Tone: {style_pack.tone}",
    ]
    if style_pack.props:
        lines.append("- Suggested props: " + ", ".join(style_pack.props))
    if style_pack.forbidden:
        lines.append("- Forbidden style elements: " + ", ".join(style_pack.forbidden))
    return lines
