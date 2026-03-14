#!/usr/bin/env python3
"""Image adapter for Gemini image generation REST API."""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class GeminiImageConfig:
    api_key: str
    base_url: str
    model: str
    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = None


def _post_json(url: str, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise SystemExit("Gemini image API returned a non-object payload.")
        return data


def _extract_inline_data(response: dict[str, Any]) -> bytes:
    candidates = response.get("candidates")
    if not isinstance(candidates, list):
        raise SystemExit("Gemini image API returned no candidates.")
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", {})
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if not isinstance(inline, dict):
                continue
            data = inline.get("data")
            if isinstance(data, str) and data:
                return base64.b64decode(data)
    raise SystemExit("Gemini image API returned no inline image data.")


def generate_image(config: GeminiImageConfig, prompt: str) -> tuple[bytes, dict[str, Any]]:
    payload: dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["Image"],
        },
    }
    image_config: dict[str, Any] = {}
    if config.aspect_ratio:
        image_config["aspectRatio"] = config.aspect_ratio
    if config.image_size:
        image_config["imageSize"] = config.image_size
    if image_config:
        payload["generationConfig"]["imageConfig"] = image_config

    response = _post_json(
        f"{config.base_url.rstrip('/')}/models/{config.model}:generateContent",
        payload,
        config.api_key,
    )
    image_bytes = _extract_inline_data(response)
    meta = {
        "model": config.model,
        "status": "generated",
    }
    return image_bytes, meta
