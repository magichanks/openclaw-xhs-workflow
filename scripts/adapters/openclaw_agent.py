#!/usr/bin/env python3
"""Helpers for structured OpenClaw agent calls."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OpenClawConfig:
    agent: str
    session_id: str
    thinking: str
    bin_path: str
    cwd: Path


def resolve_openclaw_bin() -> str:
    configured = os.environ.get("OPENCLAW_BIN", "").strip()
    if configured:
        return configured
    discovered = shutil.which("openclaw")
    if discovered:
        return discovered
    raise SystemExit("openclaw binary not found. Set OPENCLAW_BIN or add openclaw to PATH.")


def extract_first_json_block(text: str) -> Any:
    fenced_match = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
            return parsed
        except json.JSONDecodeError:
            continue
    raise SystemExit("No JSON payload found in OpenClaw output.")


def extract_openclaw_text(openclaw_output: str) -> str:
    payload = extract_first_json_block(openclaw_output)
    if not isinstance(payload, dict):
        raise SystemExit("Unexpected OpenClaw JSON envelope.")
    payloads = payload.get("result", {}).get("payloads", [])
    text_parts: list[str] = []
    for item in payloads:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if text:
            text_parts.append(text)
    if not text_parts:
        raise SystemExit("OpenClaw response did not include any text payloads.")
    return "\n".join(text_parts).strip()


class OpenClawAgentClient:
    def __init__(self, config: OpenClawConfig) -> None:
        self.config = config

    def run_structured(self, prompt: str) -> Any:
        result = subprocess.run(
            [
                self.config.bin_path,
                "agent",
                "--agent",
                self.config.agent,
                "--session-id",
                self.config.session_id,
                "--message",
                prompt,
                "--thinking",
                self.config.thinking,
                "--json",
            ],
            cwd=str(self.config.cwd),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
            raise SystemExit(details or "OpenClaw agent call failed.")
        assistant_text = extract_openclaw_text("\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip())
        return extract_first_json_block(assistant_text)
