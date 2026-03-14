#!/usr/bin/env python3
"""Validate XiaoHongShu content packs before review or publishing."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"待补"),
    re.compile(r"占位"),
    re.compile(r"\bxxx\b", re.IGNORECASE),
    re.compile(r"Write .* here\.", re.IGNORECASE),
]

REQUIRED_BY_PROFILE = {
    "draft": [
        "brief.md",
        "research.md",
        "research.json",
        "title.txt",
        "content.txt",
        "hashtags.txt",
        "asset_plan.md",
        "image_prompts.md",
        "review_checklist.md",
        "workflow_state.json",
    ],
    "review": [
        "brief.md",
        "research.md",
        "research.json",
        "title.txt",
        "content.txt",
        "hashtags.txt",
        "asset_plan.md",
        "image_prompts.md",
        "review_checklist.md",
        "workflow_state.json",
        "assets/manifest.json",
    ],
    "publish": [
        "brief.md",
        "research.md",
        "research.json",
        "title.txt",
        "content.txt",
        "hashtags.txt",
        "workflow_state.json",
        "review_report.json",
        "assets/manifest.json",
    ],
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def add_finding(findings: list[dict[str, str]], level: str, code: str, message: str) -> None:
    findings.append({"level": level, "code": code, "message": message})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def validate_required_files(pack_dir: Path, profile: str, findings: list[dict[str, str]]) -> None:
    for relative in REQUIRED_BY_PROFILE[profile]:
        if not (pack_dir / relative).exists():
            add_finding(findings, "error", "missing_file", f"Missing required file: {relative}")


def validate_placeholders(name: str, text: str, findings: list[dict[str, str]]) -> None:
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            add_finding(findings, "error", "placeholder", f"{name} contains placeholder text")
            return


def validate_content_files(pack_dir: Path, findings: list[dict[str, str]]) -> None:
    title = read_text(pack_dir / "title.txt")
    content = read_text(pack_dir / "content.txt")
    hashtags = read_text(pack_dir / "hashtags.txt")

    validate_placeholders("title.txt", title, findings)
    validate_placeholders("content.txt", content, findings)
    validate_placeholders("hashtags.txt", hashtags, findings)

    if len(title) < 6:
        add_finding(findings, "error", "title_short", "title.txt is too short")
    if len(content) < 60:
        add_finding(findings, "error", "content_short", "content.txt is too short")
    if not hashtags.strip():
        add_finding(findings, "warning", "tags_empty", "hashtags.txt is empty")


def validate_workflow_state(pack_dir: Path, profile: str, findings: list[dict[str, str]]) -> None:
    data = json.loads((pack_dir / "workflow_state.json").read_text(encoding="utf-8"))
    if profile == "publish" and data.get("state") != "ready_to_fill":
        add_finding(findings, "error", "invalid_state", f"workflow_state.json must be ready_to_fill before publishing, got {data.get('state')}")


def validate_review_report(pack_dir: Path, findings: list[dict[str, str]]) -> None:
    data = json.loads((pack_dir / "review_report.json").read_text(encoding="utf-8"))
    if data.get("decision") != "approved":
        add_finding(findings, "error", "review_not_approved", "review_report.json is not approved")


def validate_manifest(pack_dir: Path, findings: list[dict[str, str]]) -> None:
    data = json.loads((pack_dir / "assets/manifest.json").read_text(encoding="utf-8"))
    assets = data.get("assets") if isinstance(data, dict) else None
    if not isinstance(assets, list) or not assets:
        add_finding(findings, "error", "manifest_assets", "assets/manifest.json must contain a non-empty assets list")
        return
    if len(assets) != 1:
        add_finding(findings, "error", "asset_count", f"exactly 1 asset is allowed, got {len(assets)}")


def decision_for(findings: list[dict[str, str]]) -> str:
    if any(item["level"] == "error" for item in findings):
        return "blocked"
    if any(item["level"] == "warning" for item in findings):
        return "needs_fix"
    return "approved"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate XiaoHongShu pack quality.")
    parser.add_argument("--pack-dir", required=True)
    parser.add_argument("--profile", choices=("draft", "review", "publish"), required=True)
    parser.add_argument("--write-report")
    args = parser.parse_args()

    pack_dir = Path(args.pack_dir)
    if not pack_dir.exists():
        raise SystemExit(f"Pack not found: {pack_dir}")

    findings: list[dict[str, str]] = []
    validate_required_files(pack_dir, args.profile, findings)
    if not any(item["code"] == "missing_file" for item in findings):
        validate_content_files(pack_dir, findings)
        validate_workflow_state(pack_dir, args.profile, findings)
        if args.profile in {"review", "publish"}:
            validate_manifest(pack_dir, findings)
        if args.profile == "publish":
            validate_review_report(pack_dir, findings)

    report = {
        "pack_dir": str(pack_dir),
        "profile": args.profile,
        "decision": decision_for(findings),
        "findings": findings,
        "updated_at": now_iso(),
    }
    if args.write_report:
        Path(args.write_report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
