from __future__ import annotations

import time
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

from .base import (
    GenerateRequest,
    ImageProvider,
    ProviderCapability,
    ProviderMetadata,
    ProviderResult,
)


class LocalMockProvider(ImageProvider):
    metadata = ProviderMetadata(
        provider_id="local_mock",
        display_name="Local Mock Generator",
        capabilities=ProviderCapability(
            text_to_image=True,
            image_to_image=True,
            reference_images=True,
            mask=False,
            async_remote_job=False,
            supported_aspect_ratios=("1:1", "4:5", "16:9"),
            max_images_per_request=1,
        ),
        required_env=(),
        request_schema={
            "model": {"type": "string", "default": "local-placeholder"},
            "purpose": "Creates local placeholder PNGs for demo, QA, and offline testing.",
        },
    )

    def generate(self, request: GenerateRequest) -> ProviderResult:
        start = time.monotonic()
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = _size_from_aspect(request.aspect_ratio)
        image = Image.new("RGB", (width, height), "#f8fafc")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.rectangle((24, 24, width - 24, height - 24), outline="#94a3b8", width=3)
        draw.rectangle((48, 48, width - 48, height // 2), fill="#e2e8f0", outline="#cbd5e1")
        lines = [
            "AI Product Image Workflow",
            f"Provider: {self.metadata.provider_id}",
            f"Model: {request.model or 'local-placeholder'}",
            "",
            *wrap(request.prompt.replace("\n", " "), 62)[:8],
        ]
        y = height // 2 + 32
        for line in lines:
            draw.text((56, y), line, fill="#0f172a", font=font)
            y += 20
        image.save(request.output_path, format="PNG")
        return ProviderResult(
            output_path=request.output_path,
            response_summary={
                "provider_id": self.metadata.provider_id,
                "model": request.model,
                "mode": "local_placeholder",
            },
            duration_ms=int((time.monotonic() - start) * 1000),
        )


def _size_from_aspect(aspect_ratio: str) -> tuple[int, int]:
    if aspect_ratio == "4:5":
        return 1024, 1280
    if aspect_ratio == "16:9":
        return 1280, 720
    return 1024, 1024
