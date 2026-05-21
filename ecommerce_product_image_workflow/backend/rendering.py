from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

from mvp_image_workflow.util import ValidationError


DEFAULT_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def render_text_overlay(
    *,
    background_path: str | Path,
    text_path: str | Path,
    output_path: str | Path,
    font_path: str | Path | None = None,
    canvas_size: tuple[int, int] = (1024, 1024),
    text_box: tuple[int, int, int, int] = (88, 700, 936, 948),
    min_font_size: int = 22,
    max_font_size: int = 40,
    line_spacing: int = 10,
) -> Path:
    bg = Path(background_path)
    txt = Path(text_path)
    out = Path(output_path)
    if not bg.is_file():
        raise ValidationError(f"Template background not found: {bg}")
    if not txt.is_file():
        raise ValidationError(f"Template text source not found: {txt}")
    source_text = txt.read_text(encoding="utf-8").strip()
    if not source_text:
        raise ValidationError(f"Template text source is empty: {txt}")

    image = Image.open(bg).convert("RGB").resize(canvas_size)
    draw = ImageDraw.Draw(image, "RGBA")
    x1, y1, x2, y2 = text_box
    draw.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=(255, 255, 255, 224))

    font_file = _find_font(font_path)
    font = _fit_font(source_text, font_file, max_font_size, min_font_size, x2 - x1 - 48, y2 - y1 - 40, line_spacing)
    lines = _wrap_text(source_text, font, x2 - x1 - 48)
    y = y1 + 24
    for line in lines:
        draw.text((x1 + 24, y), line, font=font, fill="#0f172a")
        bbox = draw.textbbox((x1 + 24, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, format="PNG")
    return out


def _find_font(font_path: str | Path | None) -> Path:
    if font_path is not None:
        p = Path(font_path)
        if not p.is_file():
            raise ValidationError(f"Configured font not found: {p}")
        return p
    for candidate in DEFAULT_FONT_CANDIDATES:
        p = Path(candidate)
        if p.is_file():
            return p
    raise ValidationError("No usable font found. Configure a commercial-use font path.")


def _fit_font(
    text: str,
    font_path: Path,
    max_size: int,
    min_size: int,
    max_width: int,
    max_height: int,
    line_spacing: int,
) -> ImageFont.FreeTypeFont:
    probe = Image.new("RGB", (16, 16))
    draw = ImageDraw.Draw(probe)
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(str(font_path), size=size)
        lines = _wrap_text(text, font, max_width)
        total_height = 0
        widest = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            widest = max(widest, bbox[2] - bbox[0])
            total_height += (bbox[3] - bbox[1]) + line_spacing
        if widest <= max_width and total_height <= max_height:
            return font
    raise ValidationError("Text does not fit the template text area.")


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    probe = Image.new("RGB", (16, 16))
    draw = ImageDraw.Draw(probe)
    lines: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        words = raw_line.split()
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                    current = word
                else:
                    lines.extend(wrap(word, 18))
                    current = ""
        if current:
            lines.append(current)
    return lines
