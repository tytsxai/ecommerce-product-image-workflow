from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mvp_image_workflow.util import ValidationError, atomic_write_json


PROVIDER_TIMEOUT_SECONDS = 60
MAX_RESPONSE_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class ProviderCapability:
    text_to_image: bool
    image_to_image: bool
    reference_images: bool
    mask: bool
    async_remote_job: bool
    supported_aspect_ratios: tuple[str, ...]
    max_images_per_request: int


@dataclass(frozen=True)
class ProviderMetadata:
    provider_id: str
    display_name: str
    capabilities: ProviderCapability
    required_env: tuple[str, ...]
    request_schema: dict[str, Any]


@dataclass(frozen=True)
class GenerateRequest:
    prompt: str
    model: str
    output_path: Path
    config: dict[str, Any]
    source_image_paths: tuple[Path, ...] = ()
    aspect_ratio: str = "1:1"


@dataclass(frozen=True)
class ProviderResult:
    output_path: Path
    response_summary: dict[str, Any]
    duration_ms: int


class ImageProvider:
    metadata: ProviderMetadata

    def test(self, config: dict[str, Any]) -> dict[str, Any]:
        missing = [name for name in self.metadata.required_env if not os.environ.get(name)]
        if missing:
            return {
                "ok": False,
                "provider_id": self.metadata.provider_id,
                "message": "Missing required environment variable(s): " + ", ".join(missing),
            }
        return {
            "ok": True,
            "provider_id": self.metadata.provider_id,
            "message": "Provider configuration is available.",
        }

    def generate(self, request: GenerateRequest) -> ProviderResult:
        raise NotImplementedError


def safe_response_summary(data: dict[str, Any]) -> dict[str, Any]:
    blocked = {"api_key", "authorization", "password", "secret", "token"}
    out: dict[str, Any] = {}
    for key, value in data.items():
        lowered = key.lower()
        if any(item in lowered for item in blocked):
            out[key] = "[REDACTED]"
        else:
            out[key] = value
    return out


def write_provider_trace(path: Path, summary: dict[str, Any]) -> None:
    atomic_write_json(path, safe_response_summary(summary))


def http_json_post(
    *,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: int = PROVIDER_TIMEOUT_SECONDS,
) -> tuple[int, dict[str, Any]]:
    if not url.startswith(("http://", "https://")):
        raise ValidationError("Provider endpoint must start with http:// or https://")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(headers or {}),
        },
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValidationError("Provider response exceeded maximum allowed size")
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise ValidationError(f"Provider response must be JSON, got: {content_type}")
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValidationError("Provider JSON response must be an object")
            return resp.status, data
    except urllib.error.HTTPError as e:
        raw = e.read(4096).decode("utf-8", errors="replace")
        raise ValidationError(f"Provider HTTP {e.code}: {raw}") from None
    except urllib.error.URLError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        raise ValidationError(f"Provider request failed after {elapsed}ms: {e.reason}") from None


def write_base64_image(encoded: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(encoded))
