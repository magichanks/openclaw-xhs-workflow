#!/usr/bin/env python3
"""Image adapter for OpenAI Images API and compatible gateways."""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class OpenAIImageConfig:
    api_key: str
    base_url: str
    model: str
    size: str
    quality: str | None = None
    background: str | None = None


def _post_json(url: str, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise SystemExit("OpenAI image API returned a non-object payload.")
        return data


def _download_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read()


def generate_image(config: OpenAIImageConfig, prompt: str) -> tuple[bytes, dict[str, Any]]:
    payload: dict[str, Any] = {
        "model": config.model,
        "prompt": prompt,
        "n": 1,
        "size": config.size,
    }
    if config.quality:
        payload["quality"] = config.quality
    if config.background:
        payload["background"] = config.background

    data = _post_json(f"{config.base_url.rstrip('/')}/images/generations", payload, config.api_key)
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise SystemExit("OpenAI image API returned no image data.")
    first = items[0]
    if not isinstance(first, dict):
        raise SystemExit("OpenAI image API returned an invalid image item.")

    if first.get("b64_json"):
        image_bytes = base64.b64decode(first["b64_json"])
    elif first.get("url"):
        image_bytes = _download_bytes(str(first["url"]))
    else:
        raise SystemExit("OpenAI image API returned neither b64_json nor url.")

    meta = {
        "model": config.model,
        "status": "generated",
        "width": None,
        "height": None,
        "response_created": data.get("created"),
    }
    return image_bytes, meta
