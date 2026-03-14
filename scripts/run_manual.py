#!/usr/bin/env python3
"""Build a one-off workflow instruction from a scheduler and extra requirements."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_extra(args: argparse.Namespace) -> str:
    chunks: list[str] = []
    for item in args.extra or []:
        if item.strip():
            chunks.append(item.strip())
    if args.extra_file:
        text = Path(args.extra_file).read_text(encoding="utf-8").strip()
        if text:
            chunks.append(text)
    return "\n\n".join(chunks).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a one-off OpenClaw message for a XiaoHongShu workflow run.")
    parser.add_argument("--scheduler-file", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--extra", action="append")
    parser.add_argument("--extra-file")
    args = parser.parse_args()

    scheduler_path = Path(args.scheduler_file).resolve()
    scheduler = json.loads(scheduler_path.read_text(encoding="utf-8"))
    extra = load_extra(args)

    payload = {
        "scheduler_file": str(scheduler_path),
        "date": args.date,
        "topic_slug": scheduler["pack_naming"]["topic_slug"],
        "mode": scheduler.get("mode", "save_draft"),
        "extra_requirements": extra,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
