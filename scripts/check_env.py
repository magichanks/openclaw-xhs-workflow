#!/usr/bin/env python3
"""Check the minimum environment required for different workflow profiles."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from common_env import default_env_file, load_env_file, repo_root


REPO_ROOT = repo_root()
EXAMPLE_SOURCE_FILE = REPO_ROOT / "assets" / "examples" / "example-pack" / "assets" / "cover.png"


def _env(key: str) -> str:
    return os.environ.get(key, "").strip()


def _status(ok: bool) -> str:
    return "ok" if ok else "missing"


def build_checks(profile: str, source_file: Optional[str]) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    openclaw_bin = _env("OPENCLAW_BIN") or shutil.which("openclaw") or ""

    checks.append(
        {
            "name": ".env.local",
            "ok": True,
            "detail": f"optional but recommended: {default_env_file()}",
        }
    )

    if profile == "mock":
        checks.append(
            {
                "name": "python",
                "ok": sys.version_info >= (3, 9),
                "detail": f"detected {sys.version.split()[0]}",
            }
        )
        return checks

    needs_openclaw = profile in {"openclaw", "openclaw-images", "openai-images", "gemini-images"}
    if needs_openclaw:
        checks.append(
            {
                "name": "openclaw binary",
                "ok": bool(openclaw_bin),
                "detail": openclaw_bin or "set OPENCLAW_BIN or add openclaw to PATH",
            }
        )
        checks.append(
            {
                "name": "XHS_OPENCLAW_AGENT",
                "ok": bool(_env("XHS_OPENCLAW_AGENT")),
                "detail": _env("XHS_OPENCLAW_AGENT") or "set in .env.local, default example: main",
            }
        )
        checks.append(
            {
                "name": "XHS_PUBLISHER_OPENCLAW_AGENT",
                "ok": bool(_env("XHS_PUBLISHER_OPENCLAW_AGENT") or _env("XHS_OPENCLAW_AGENT")),
                "detail": _env("XHS_PUBLISHER_OPENCLAW_AGENT") or _env("XHS_OPENCLAW_AGENT") or "set publisher agent name",
            }
        )

    if profile == "openclaw":
        candidate = Path(source_file).expanduser() if source_file else EXAMPLE_SOURCE_FILE
        checks.append(
            {
                "name": "cover image",
                "ok": candidate.exists(),
                "detail": str(candidate),
            }
        )

    if profile == "openai-images":
        checks.append(
            {
                "name": "OPENAI_API_KEY",
                "ok": bool(_env("OPENAI_API_KEY")),
                "detail": "required for image generation",
            }
        )

    if profile == "gemini-images":
        checks.append(
            {
                "name": "GEMINI_API_KEY",
                "ok": bool(_env("GEMINI_API_KEY")),
                "detail": "required for image generation",
            }
        )

    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local environment for openclaw-xhs-workflow.")
    parser.add_argument("--profile", choices=["mock", "openclaw", "openclaw-images", "openai-images", "gemini-images"], default="mock")
    parser.add_argument("--source-file", help="Optional cover image path for the openclaw/source-file profile.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any required check fails.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    loaded = load_env_file()
    checks = build_checks(args.profile, args.source_file)
    ok = all(bool(item["ok"]) for item in checks)
    payload = {
        "profile": args.profile,
        "env_file": str(loaded) if loaded else None,
        "ok": ok,
        "checks": checks,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        env_line = f"Loaded env: {loaded}" if loaded else f"No env file loaded. Expected optional file: {default_env_file()}"
        print(env_line)
        print(f"Profile: {args.profile}")
        print("")
        for item in checks:
            print(f"[{_status(bool(item['ok']))}] {item['name']}: {item['detail']}")
        print("")
        if ok:
            print("Environment check passed.")
        else:
            print("Environment check failed. Fix the missing items above, then run again.")

    if args.strict and not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
