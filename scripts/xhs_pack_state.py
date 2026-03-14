#!/usr/bin/env python3
"""Manage XiaoHongShu pack workflow state and run locks."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


STATE_TRANSITIONS = {
    "created": {"researched", "failed", "blocked"},
    "researched": {"drafted", "failed", "blocked"},
    "drafted": {"imaged", "failed", "blocked"},
    "imaged": {"reviewed", "failed", "blocked"},
    "reviewed": {"ready_to_fill", "failed", "blocked"},
    "ready_to_fill": {"filled", "failed", "blocked"},
    "filled": {"published", "failed", "blocked"},
    "published": set(),
    "failed": {"created", "researched", "drafted", "imaged", "reviewed", "ready_to_fill"},
    "blocked": {"created", "researched", "drafted", "imaged", "reviewed"},
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def workflow_path(pack_dir: Path) -> Path:
    return pack_dir / "workflow_state.json"


def runs_path(pack_dir: Path) -> Path:
    return pack_dir / "agent_runs.json"


def lock_path(pack_dir: Path) -> Path:
    return pack_dir / "pack.lock"


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_pack(pack_dir: Path) -> None:
    if not pack_dir.exists():
        raise SystemExit(f"Pack not found: {pack_dir}")


def cmd_show(args: argparse.Namespace) -> None:
    pack_dir = Path(args.pack_dir)
    ensure_pack(pack_dir)
    print(json.dumps(load_json(workflow_path(pack_dir), {}), ensure_ascii=False, indent=2))


def cmd_init(args: argparse.Namespace) -> None:
    pack_dir = Path(args.pack_dir)
    ensure_pack(pack_dir)
    state = {
        "pack_id": args.pack_id or pack_dir.name,
        "mode": args.mode,
        "state": "created",
        "owner": args.owner,
        "content_status": "pending",
        "image_status": "pending",
        "review_status": "pending",
        "publisher_status": "pending",
        "failed_reason": "",
        "last_step": "init",
        "updated_at": now_iso(),
    }
    save_json(workflow_path(pack_dir), state)
    if not runs_path(pack_dir).exists():
        save_json(runs_path(pack_dir), [])
    print(json.dumps(state, ensure_ascii=False, indent=2))


def cmd_transition(args: argparse.Namespace) -> None:
    pack_dir = Path(args.pack_dir)
    ensure_pack(pack_dir)
    path = workflow_path(pack_dir)
    data = load_json(path, {})
    if not isinstance(data, dict):
        raise SystemExit("workflow_state.json must be an object")

    current = str(data.get("state", ""))
    if args.expected_state and current != args.expected_state:
        raise SystemExit(f"Expected state '{args.expected_state}', got '{current}' for {pack_dir}")

    next_state = args.state
    allowed = STATE_TRANSITIONS.get(current, set())
    if not args.allow_any and next_state not in allowed and next_state != current:
        raise SystemExit(f"Invalid transition: {current} -> {next_state}")

    data["state"] = next_state
    data["owner"] = args.owner or data.get("owner", "")
    data["updated_at"] = now_iso()
    for field in ("mode", "content_status", "image_status", "review_status", "publisher_status"):
        value = getattr(args, field, None)
        if value:
            data[field] = value
    if args.failed_reason is not None:
        data["failed_reason"] = args.failed_reason
    if args.last_step:
        data["last_step"] = args.last_step

    save_json(path, data)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_record_run(args: argparse.Namespace) -> None:
    pack_dir = Path(args.pack_dir)
    ensure_pack(pack_dir)
    data = load_json(runs_path(pack_dir), [])
    if not isinstance(data, list):
        raise SystemExit("agent_runs.json must be an array")
    record = {
        "actor": args.actor,
        "step": args.step,
        "status": args.status,
        "note": args.note,
        "timestamp": now_iso(),
    }
    data.append(record)
    save_json(runs_path(pack_dir), data)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def cmd_lock(args: argparse.Namespace) -> None:
    pack_dir = Path(args.pack_dir)
    ensure_pack(pack_dir)
    payload = {"owner": args.owner, "pid": os.getpid(), "created_at": now_iso()}
    path = lock_path(pack_dir)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = load_json(path, {})
        raise SystemExit(f"Pack already locked: {pack_dir} owner={existing.get('owner', 'unknown')}")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_unlock(args: argparse.Namespace) -> None:
    pack_dir = Path(args.pack_dir)
    ensure_pack(pack_dir)
    path = lock_path(pack_dir)
    if not path.exists():
        print(json.dumps({"success": True, "status": "not_locked"}, ensure_ascii=False))
        return
    existing = load_json(path, {})
    if not args.force and args.owner and existing.get("owner") != args.owner:
        raise SystemExit(f"Refusing to unlock {pack_dir}: owner mismatch ({existing.get('owner')} != {args.owner})")
    path.unlink()
    print(json.dumps({"success": True, "status": "unlocked"}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage XiaoHongShu pack workflow state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("show")
    sub.add_argument("--pack-dir", required=True)
    sub.set_defaults(func=cmd_show)

    sub = subparsers.add_parser("init")
    sub.add_argument("--pack-dir", required=True)
    sub.add_argument("--pack-id")
    sub.add_argument("--mode", default="save_draft")
    sub.add_argument("--owner", default="xhs-orchestrator")
    sub.set_defaults(func=cmd_init)

    sub = subparsers.add_parser("transition")
    sub.add_argument("--pack-dir", required=True)
    sub.add_argument("--state", required=True)
    sub.add_argument("--expected-state")
    sub.add_argument("--mode")
    sub.add_argument("--owner")
    sub.add_argument("--content-status")
    sub.add_argument("--image-status")
    sub.add_argument("--review-status")
    sub.add_argument("--publisher-status")
    sub.add_argument("--failed-reason")
    sub.add_argument("--last-step")
    sub.add_argument("--allow-any", action="store_true")
    sub.set_defaults(func=cmd_transition)

    sub = subparsers.add_parser("record-run")
    sub.add_argument("--pack-dir", required=True)
    sub.add_argument("--actor", required=True)
    sub.add_argument("--step", required=True)
    sub.add_argument("--status", required=True)
    sub.add_argument("--note", default="")
    sub.set_defaults(func=cmd_record_run)

    sub = subparsers.add_parser("lock")
    sub.add_argument("--pack-dir", required=True)
    sub.add_argument("--owner", required=True)
    sub.set_defaults(func=cmd_lock)

    sub = subparsers.add_parser("unlock")
    sub.add_argument("--pack-dir", required=True)
    sub.add_argument("--owner")
    sub.add_argument("--force", action="store_true")
    sub.set_defaults(func=cmd_unlock)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
