#!/usr/bin/env python3
"""Shared environment helpers for local workflow scripts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_env_file() -> Path:
    return repo_root() / ".env.local"


def load_env_file(path: Optional[Path] = None) -> Optional[Path]:
    target = path or default_env_file()
    if not target.exists():
        return None
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value
    return target
