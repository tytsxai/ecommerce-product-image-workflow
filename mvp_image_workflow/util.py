from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

_SAFE_FILENAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


@dataclass(frozen=True)
class ValidationError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def contains_disallowed_scripts(text: str) -> bool:
    # English-only policy: reject Cyrillic and CJK blocks as a practical MVP check.
    for ch in text:
        code = ord(ch)
        if 0x0400 <= code <= 0x04FF:  # Cyrillic
            return True
        if 0x4E00 <= code <= 0x9FFF:  # CJK Unified Ideographs
            return True
        if 0x3040 <= code <= 0x30FF:  # Hiragana + Katakana
            return True
        if 0xAC00 <= code <= 0xD7AF:  # Hangul Syllables
            return True
    return False


def require_english_text(field_name: str, value: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValidationError(f"Missing required English text: {field_name}")
    if contains_disallowed_scripts(v):
        raise ValidationError(
            f"Field '{field_name}' contains non-English characters (Cyrillic/CJK detected)."
        )
    if not v.isascii():
        raise ValidationError(
            f"Field '{field_name}' must be ASCII English text (no non-ASCII characters)."
        )
    for ch in v:
        if ch in "\n\t":
            continue
        if ord(ch) < 32:
            raise ValidationError(f"Field '{field_name}' contains control characters.")
    return v


def optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return v or None


def safe_id(raw: str) -> str:
    s = (raw or "").strip().replace(" ", "_")
    s = "".join(ch for ch in s if ch in _SAFE_FILENAME_CHARS)
    return s


def atomic_write_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=p.parent,
            delete=False,
        ) as f:
            tmp_path = f.name
            f.write(content.rstrip() + "\n")
        os.replace(tmp_path, p)
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def atomic_write_json(path: str | Path, obj: object) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def file_sha256(path: str | Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def split_path_list(value: str | None) -> tuple[str, ...]:
    v = optional_text(value)
    if v is None:
        return ()
    return tuple(item.strip() for item in v.split(";") if item.strip())
