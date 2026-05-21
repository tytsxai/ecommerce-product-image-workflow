from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from mvp_image_workflow.util import ValidationError

from .base import (
    GenerateRequest,
    ImageProvider,
    ProviderCapability,
    ProviderMetadata,
    ProviderResult,
    http_json_post,
    safe_response_summary,
    write_base64_image,
)


class GenericHttpProvider(ImageProvider):
    metadata = ProviderMetadata(
        provider_id="generic_http",
        display_name="Generic HTTP Image API",
        capabilities=ProviderCapability(
            text_to_image=True,
            image_to_image=True,
            reference_images=True,
            mask=True,
            async_remote_job=False,
            supported_aspect_ratios=("1:1", "4:5", "16:9"),
            max_images_per_request=1,
        ),
        required_env=(),
        request_schema={
            "endpoint_url": {"type": "string", "required": True},
            "api_key_env": {"type": "string", "required": False},
            "model": {"type": "string", "required": False},
            "response_image_field": {"type": "string", "default": "image_base64"},
        },
    )

    def test(self, config: dict[str, Any]) -> dict[str, Any]:
        endpoint = (config.get("endpoint_url") or "").strip()
        if not endpoint:
            return {"ok": False, "provider_id": self.metadata.provider_id, "message": "Missing endpoint_url."}
        api_key_env = (config.get("api_key_env") or "").strip()
        if api_key_env and not os.environ.get(api_key_env):
            return {
                "ok": False,
                "provider_id": self.metadata.provider_id,
                "message": f"Missing environment variable: {api_key_env}",
            }
        return {"ok": True, "provider_id": self.metadata.provider_id, "message": "Generic HTTP config is usable."}

    def generate(self, request: GenerateRequest) -> ProviderResult:
        start = time.monotonic()
        endpoint = (request.config.get("endpoint_url") or "").strip()
        if not endpoint:
            raise ValidationError("generic_http requires config.endpoint_url")
        api_key_env = (request.config.get("api_key_env") or "").strip()
        headers = {}
        if api_key_env:
            api_key = os.environ.get(api_key_env)
            if not api_key:
                raise ValidationError(f"Missing environment variable: {api_key_env}")
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "prompt": request.prompt,
            "model": request.model,
            "aspect_ratio": request.aspect_ratio,
            "source_images": [str(p) for p in request.source_image_paths],
        }
        status, data = http_json_post(url=endpoint, payload=payload, headers=headers)
        image_field = request.config.get("response_image_field") or "image_base64"
        encoded = _nested_value(data, str(image_field))
        if not isinstance(encoded, str) or not encoded:
            raise ValidationError(f"Provider response missing base64 image field: {image_field}")
        write_base64_image(encoded, request.output_path)
        return ProviderResult(
            output_path=request.output_path,
            response_summary=safe_response_summary(
                {
                    "provider_id": self.metadata.provider_id,
                    "status": status,
                    "model": request.model,
                    "endpoint_url": endpoint,
                    "response_keys": sorted(data.keys()),
                }
            ),
            duration_ms=int((time.monotonic() - start) * 1000),
        )


def _nested_value(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current
