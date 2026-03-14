#!/usr/bin/env python3
"""Run opinionated quickstart flows with minimal local setup."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

from common_env import load_env_file, repo_root


REPO_ROOT = repo_root()
SCRIPT_DIR = REPO_ROOT / "scripts"
EXAMPLES_DIR = REPO_ROOT / "assets" / "examples"
EXAMPLE_SOURCE_FILE = EXAMPLES_DIR / "example-pack" / "assets" / "cover.png"
PYTHON_BIN = os.environ.get("XHS_PYTHON_BIN", "/usr/bin/python3")
PROFILE_TO_SCHEDULER = {
    "mock": EXAMPLES_DIR / "scheduler-save-draft.json",
    "openclaw": EXAMPLES_DIR / "scheduler-openclaw-save-draft.json",
    "openclaw-images": EXAMPLES_DIR / "scheduler-openclaw-images-save-draft.json",
    "openai-images": EXAMPLES_DIR / "scheduler-openai-images-save-draft.json",
    "gemini-images": EXAMPLES_DIR / "scheduler-gemini-images-save-draft.json",
}


def run_command(cmd: list[str], env: dict[str, str]) -> int:
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env)
    return int(result.returncode)


def prepare_scheduler(profile: str, source_file: Optional[str]) -> Path:
    scheduler = json.loads(PROFILE_TO_SCHEDULER[profile].read_text(encoding="utf-8"))
    if profile == "openclaw":
        source_path = Path(source_file).expanduser().resolve() if source_file else EXAMPLE_SOURCE_FILE.resolve()
        scheduler.setdefault("image_policy", {})
        scheduler["image_policy"]["adapter"] = "source-file"
        scheduler["image_policy"]["source_file"] = str(source_path)

    temp_root = REPO_ROOT / ".tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="xhs-quickstart-", dir=str(temp_root)))
    target = temp_dir / f"{profile}-scheduler.json"
    target.write_text(json.dumps(scheduler, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the shortest successful path for openclaw-xhs-workflow.")
    parser.add_argument("--profile", choices=["mock", "openclaw", "openclaw-images", "openai-images", "gemini-images"], default="mock")
    parser.add_argument("--date", default=str(date.today()), help="Pack date in YYYY-MM-DD.")
    parser.add_argument("--packs-root", default="./tmp-packs", help="Where generated packs should be created.")
    parser.add_argument("--mode", choices=["save_draft", "publish"], default="save_draft")
    parser.add_argument("--source-file", help="Cover image path for the openclaw/source-file profile.")
    parser.add_argument("--publisher-adapter", choices=["mock", "openclaw"], help="Optional publisher adapter override.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved command without executing it.")
    args = parser.parse_args()

    load_env_file()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SCRIPT_DIR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    doctor_cmd = [
        PYTHON_BIN,
        str(SCRIPT_DIR / "check_env.py"),
        "--profile",
        args.profile,
        "--strict",
    ]
    if args.source_file:
        doctor_cmd.extend(["--source-file", args.source_file])
    doctor_code = run_command(doctor_cmd, env)
    if doctor_code != 0:
        raise SystemExit(doctor_code)

    scheduler_file = prepare_scheduler(args.profile, args.source_file)
    publisher_adapter = args.publisher_adapter
    if not publisher_adapter:
        publisher_adapter = "mock" if args.profile == "mock" else "openclaw"

    cmd = [
        PYTHON_BIN,
        str(SCRIPT_DIR / "xhs_workflow.py"),
        "--packs-root",
        args.packs_root,
        "--scheduler-file",
        str(scheduler_file),
        "--date",
        args.date,
        "--start-at",
        "research",
        "--mode",
        args.mode,
        "--publisher-adapter",
        publisher_adapter,
    ]

    print(f"Profile: {args.profile}")
    print(f"Scheduler: {scheduler_file}")
    if args.profile == "openclaw" and not args.source_file:
        print(f"Source file fallback: {EXAMPLE_SOURCE_FILE}")
    print("Command:")
    print(" ".join(cmd))
    sys.stdout.flush()

    if args.dry_run:
        return

    raise SystemExit(run_command(cmd, env))


if __name__ == "__main__":
    main()
