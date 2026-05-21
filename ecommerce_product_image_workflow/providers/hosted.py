from __future__ import annotations

import os
from typing import Any

from .base import ImageProvider, ProviderCapability, ProviderMetadata


class EnvCheckedProvider(ImageProvider):
    metadata: ProviderMetadata

    def generate(self, request):  # pragma: no cover - network providers are integration-tested by users.
        raise RuntimeError(
            f"{self.metadata.provider_id} is configured as a provider template. "
            "Use generic_http for custom endpoints or extend this provider for production calls."
        )


class OpenAIImagesProvider(EnvCheckedProvider):
    metadata = ProviderMetadata(
        provider_id="openai_images",
        display_name="OpenAI Images",
        capabilities=ProviderCapability(True, True, True, True, False, ("1:1", "4:5", "16:9"), 1),
        required_env=("OPENAI_API_KEY",),
        request_schema={"model": {"type": "string", "default": "gpt-image-1"}},
    )


class ReplicateProvider(EnvCheckedProvider):
    metadata = ProviderMetadata(
        provider_id="replicate",
        display_name="Replicate",
        capabilities=ProviderCapability(True, True, True, True, True, ("1:1", "4:5", "16:9"), 1),
        required_env=("REPLICATE_API_TOKEN",),
        request_schema={"model": {"type": "string", "required": True}},
    )


class ComfyUiHttpProvider(EnvCheckedProvider):
    metadata = ProviderMetadata(
        provider_id="comfyui_http",
        display_name="ComfyUI HTTP",
        capabilities=ProviderCapability(True, True, True, True, True, ("1:1", "4:5", "16:9"), 1),
        required_env=(),
        request_schema={"endpoint_url": {"type": "string", "default": "http://127.0.0.1:8188"}},
    )

    def test(self, config: dict[str, Any]) -> dict[str, Any]:
        endpoint = (config.get("endpoint_url") or os.environ.get("COMFYUI_ENDPOINT") or "").strip()
        return {
            "ok": bool(endpoint),
            "provider_id": self.metadata.provider_id,
            "message": "ComfyUI endpoint configured." if endpoint else "Missing endpoint_url or COMFYUI_ENDPOINT.",
        }
