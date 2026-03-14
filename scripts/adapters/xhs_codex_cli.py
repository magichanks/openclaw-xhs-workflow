#!/usr/bin/env python3
"""Publisher adapter for a locally installed xiaohongshu Codex CLI skill."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PublisherConfig:
    skill_root: Path
    cli_path: Path


class CodexCliPublisherAdapter:
    def __init__(self, config: PublisherConfig) -> None:
        self.config = config

    def _run(self, args: list[str]) -> str:
        result = subprocess.run(
            args,
            cwd=str(self.config.skill_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
            raise SystemExit(details or "publisher adapter command failed")
        return "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()

    def check_login(self) -> dict[str, Any]:
        output = self._run(["uv", "run", "python", str(self.config.cli_path), "check-login"])
        return extract_first_json_block(output)

    def run_action(self, action: str, args: list[str]) -> str:
        return self._run(["uv", "run", "python", str(self.config.cli_path), action, *args])


def extract_first_json_block(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise SystemExit("Could not parse JSON payload from publisher adapter output.")
