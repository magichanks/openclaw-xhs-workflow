#!/usr/bin/env python3
"""Publisher adapter that delegates publisher actions to the user's own OpenClaw agent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from adapters.openclaw_agent import OpenClawAgentClient


@dataclass
class PublisherOpenClawContext:
    pack_dir: str
    mode: str


def _parse_cli_style_args(args: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {"images": [], "tags": []}
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--title-file" and index + 1 < len(args):
            parsed["title_file"] = args[index + 1]
            index += 2
            continue
        if token == "--content-file" and index + 1 < len(args):
            parsed["content_file"] = args[index + 1]
            index += 2
            continue
        if token == "--images":
            index += 1
            while index < len(args) and not args[index].startswith("--"):
                parsed["images"].append(args[index])
                index += 1
            continue
        if token == "--tags":
            index += 1
            while index < len(args) and not args[index].startswith("--"):
                parsed["tags"].append(args[index])
                index += 1
            continue
        parsed.setdefault("extra_args", []).append(token)
        index += 1
    return parsed


class OpenClawPublisherAdapter:
    def __init__(self, client: OpenClawAgentClient, context: PublisherOpenClawContext) -> None:
        self.client = client
        self.context = context

    def check_login(self) -> dict[str, Any]:
        prompt = f"""
Use your current OpenClaw environment and available XiaoHongShu publisher tooling to check whether the publisher account is logged in and ready.

Context:
- pack_dir: {self.context.pack_dir}
- mode: {self.context.mode}

Rules:
- Do not click publish.
- Do not change files.
- Use the user's own OpenClaw-compatible publisher tooling or skills.
- Return exactly one JSON object and nothing else.

JSON schema:
{{
  "logged_in": true,
  "note": "short explanation"
}}
""".strip()
        payload = self.client.run_structured(prompt)
        if not isinstance(payload, dict):
            raise SystemExit("OpenClaw publisher login payload must be an object.")
        return payload

    def run_action(self, action: str, args: list[str]) -> str:
        parsed = _parse_cli_style_args(args)
        prompt = f"""
Use your current OpenClaw environment and available XiaoHongShu publisher tooling to run one publisher action.

Context:
- pack_dir: {self.context.pack_dir}
- mode: {self.context.mode}
- action: {action}

Inputs:
```json
{json.dumps(parsed, ensure_ascii=False, indent=2)}
```

Rules:
- Use the user's own OpenClaw AI and installed tooling.
- Respect the action exactly.
- If action is `fill-publish`, fill the publish form but do not click publish.
- If action is `save-draft`, save the current note as draft.
- If action is `click-publish`, click publish only if the action explicitly requests it.
- Return exactly one JSON object and nothing else.

JSON schema:
{{
  "success": true,
  "note": "short explanation"
}}
""".strip()
        payload = self.client.run_structured(prompt)
        if not isinstance(payload, dict):
            raise SystemExit("OpenClaw publisher action payload must be an object.")
        success = bool(payload.get("success"))
        note = str(payload.get("note", "")).strip()
        if not success:
            raise SystemExit(note or f"OpenClaw publisher action failed: {action}")
        return note or f"OpenClaw publisher action completed: {action}"
