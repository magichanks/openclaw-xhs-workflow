#!/usr/bin/env python3
"""Mock publisher adapter for local tests."""

from __future__ import annotations

import json
from typing import Any


class MockPublisherAdapter:
    def check_login(self) -> dict[str, Any]:
        return {"logged_in": True, "adapter": "mock"}

    def run_action(self, action: str, args: list[str]) -> str:
        return json.dumps({"success": True, "action": action, "args": args}, ensure_ascii=False)
