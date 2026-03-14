#!/usr/bin/env python3
"""Generic XiaoHongShu workflow runner skeleton."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_command(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if result.returncode != 0:
        details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise SystemExit(details or "command failed")
    return "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_run(pack_dir: Path, actor: str, step: str, status: str, note: str) -> None:
    run_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "xhs_pack_state.py"),
            "record-run",
            "--pack-dir",
            str(pack_dir),
            "--actor",
            actor,
            "--step",
            step,
            "--status",
            status,
            "--note",
            note,
        ]
    )


def transition(pack_dir: Path, state: str, last_step: str, **extra: str) -> None:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "xhs_pack_state.py"),
        "transition",
        "--pack-dir",
        str(pack_dir),
        "--state",
        state,
        "--last-step",
        last_step,
    ]
    for key, value in extra.items():
        if value:
            cmd.extend([f"--{key.replace('_', '-')}", value])
    run_command(cmd)


def resolve_pack_dir(packs_root: Path, scheduler: dict, date_text: str) -> Path:
    slug = scheduler["pack_naming"]["topic_slug"]
    return packs_root / f"{date_text}-{slug}"


def ensure_pack(args: argparse.Namespace, scheduler: dict) -> Path:
    pack_dir = Path(args.pack_dir) if args.pack_dir else resolve_pack_dir(Path(args.packs_root), scheduler, args.date)
    if pack_dir.exists():
        return pack_dir
    run_command([str(SCRIPT_DIR / "scaffold_pack.sh"), str(Path(args.packs_root)), scheduler["pack_naming"]["topic_slug"], args.date])
    return pack_dir


def run_workflow(args: argparse.Namespace) -> int:
    scheduler = read_json(Path(args.scheduler_file))
    pack_dir = ensure_pack(args, scheduler)

    record_run(pack_dir, "xhs-orchestrator", "workflow", "started", "Workflow started from scheduler.")

    if args.mode == "prepare_only":
        transition(pack_dir, "reviewed", "workflow", content_status="done", image_status="done", review_status="approved")
        record_run(pack_dir, "xhs-orchestrator", "workflow", "completed", "Skeleton workflow stopped at prepare_only.")
        return 0

    transition(pack_dir, "ready_to_fill", "review", content_status="done", image_status="done", review_status="approved")
    record_run(pack_dir, "xhs-orchestrator", "preflight-publish", "pending", "Plug in a publisher adapter here.")

    state = read_json(pack_dir / "workflow_state.json")
    state["publisher_status"] = "pending"
    state["updated_at"] = now_iso()
    write_json(pack_dir / "workflow_state.json", state)

    result = read_json(pack_dir / "publish_result.json")
    result["mode"] = args.mode
    result["updated_at"] = now_iso()
    write_json(pack_dir / "publish_result.json", result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a generic XiaoHongShu workflow from a scheduler.")
    parser.add_argument("--packs-root", required=True)
    parser.add_argument("--scheduler-file", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--pack-dir")
    parser.add_argument("--mode", choices=("prepare_only", "save_draft", "publish"), default="save_draft")
    parser.add_argument("--publisher-adapter", default=os.environ.get("XHS_PUBLISHER_ADAPTER", "mock"))
    args = parser.parse_args()
    return run_workflow(args)


if __name__ == "__main__":
    sys.exit(main())
