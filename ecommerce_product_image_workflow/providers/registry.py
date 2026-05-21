from __future__ import annotations

from dataclasses import asdict

from .base import ImageProvider
from .generic_http import GenericHttpProvider
from .hosted import ComfyUiHttpProvider, OpenAIImagesProvider, ReplicateProvider
from .local_mock import LocalMockProvider


_PROVIDERS: dict[str, ImageProvider] = {
    "local_mock": LocalMockProvider(),
    "generic_http": GenericHttpProvider(),
    "openai_images": OpenAIImagesProvider(),
    "replicate": ReplicateProvider(),
    "comfyui_http": ComfyUiHttpProvider(),
}


def get_provider(provider_id: str) -> ImageProvider:
    try:
        return _PROVIDERS[provider_id]
    except KeyError:
        raise KeyError(f"Unknown provider_id: {provider_id}") from None


def list_provider_metadata() -> list[dict]:
    return [asdict(provider.metadata) for provider in _PROVIDERS.values()]
