#!/usr/bin/env python3
"""Image adapter that delegates image generation to the user's own OpenClaw setup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.openclaw_agent import OpenClawAgentClient


@dataclass
class OpenClawImageContext:
    pack_dir: str
    output_path: str


def generate_image(client: OpenClawAgentClient, context: OpenClawImageContext, prompt: str) -> dict[str, Any]:
    request = f"""
Use your current OpenClaw environment and any image-generation capability already configured there to generate one XiaoHongShu cover image.

Context:
- pack_dir: {context.pack_dir}
- output_path: {context.output_path}

Prompt:
{prompt}

Rules:
- Generate exactly one cover image.
- Save the final image file exactly at output_path.
- Do not write outside pack_dir.
- Return exactly one JSON object and nothing else.

JSON schema:
{{
  "success": true,
  "model": "short model or provider name",
  "note": "short explanation"
}}
""".strip()
    payload = client.run_structured(request)
    if not isinstance(payload, dict):
        raise SystemExit("OpenClaw image payload must be an object.")
    if not bool(payload.get("success")):
        raise SystemExit(str(payload.get("note", "")).strip() or "OpenClaw image generation failed.")
    if not Path(context.output_path).exists():
        raise SystemExit(f"OpenClaw image adapter reported success but file was not created: {context.output_path}")
    return {
        "model": str(payload.get("model", "openclaw-images")).strip() or "openclaw-images",
        "status": "generated",
        "note": str(payload.get("note", "")).strip(),
    }
