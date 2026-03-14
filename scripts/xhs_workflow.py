#!/usr/bin/env python3
"""Run a draft-first XiaoHongShu workflow from a scheduler and an existing pack."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from adapters.xhs_codex_cli import CodexCliPublisherAdapter, PublisherConfig
from adapters.xhs_mock_publisher import MockPublisherAdapter


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SKILL_ROOT = Path.home() / ".codex/skills/xiaohongshu-skills"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_command(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if result.returncode != 0:
        details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise SystemExit(details or "command failed")
    return "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


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


def transition(pack_dir: Path, state: str, last_step: str, allow_any: bool = False, **extra: str) -> None:
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
    if allow_any:
        cmd.append("--allow-any")
    for key, value in extra.items():
        if value is not None:
            cmd.extend([f"--{key.replace('_', '-')}", value])
    run_command(cmd)


def resolve_pack_dir(packs_root: Path, scheduler: dict, date_text: str) -> Path:
    slug = scheduler["pack_naming"]["topic_slug"]
    return packs_root / f"{date_text}-{slug}"


def ensure_pack(packs_root: Path, scheduler: dict, date_text: str, pack_dir_arg: str | None) -> Path:
    pack_dir = Path(pack_dir_arg).resolve() if pack_dir_arg else resolve_pack_dir(packs_root, scheduler, date_text)
    if pack_dir.exists():
        return pack_dir
    run_command([str(SCRIPT_DIR / "scaffold_pack.sh"), str(packs_root), scheduler["pack_naming"]["topic_slug"], date_text])
    return pack_dir


def normalize_tags(raw_text: str) -> list[str]:
    tags: list[str] = []
    for token in raw_text.replace("，", " ").replace(",", " ").split():
        cleaned = token.strip()
        if cleaned:
            tags.append(cleaned.lstrip("#"))
    return tags


def resolve_image_path(pack_dir: Path, scheduler: dict) -> Path:
    required_output = str(scheduler.get("image_policy", {}).get("required_output", "")).strip()
    if required_output:
        candidate = Path(required_output)
        if not candidate.is_absolute():
            candidate = pack_dir / candidate
        if candidate.exists():
            return candidate.resolve()

    manifest_path = pack_dir / "assets" / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        assets = manifest.get("assets")
        if isinstance(assets, list):
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                if str(asset.get("role", "")).strip() != "cover":
                    continue
                rel_path = str(asset.get("path", "")).strip()
                if not rel_path:
                    continue
                candidate = Path(rel_path)
                if not candidate.is_absolute():
                    candidate = pack_dir / candidate
                if candidate.exists():
                    return candidate.resolve()

    raise SystemExit("Could not resolve a publishable cover image from scheduler or assets/manifest.json.")


def resolve_image_reference(pack_dir: Path, scheduler: dict) -> str:
    required_output = str(scheduler.get("image_policy", {}).get("required_output", "")).strip()
    if required_output:
        return required_output

    manifest_path = pack_dir / "assets" / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        assets = manifest.get("assets")
        if isinstance(assets, list):
            for asset in assets:
                if isinstance(asset, dict) and str(asset.get("role", "")).strip() == "cover":
                    rel_path = str(asset.get("path", "")).strip()
                    if rel_path:
                        return rel_path
    return "assets/cover.png"


def update_publish_result(pack_dir: Path, **patch: object) -> None:
    path = pack_dir / "publish_result.json"
    current = read_json(path)
    current.update(patch)
    current["updated_at"] = now_iso()
    write_json(path, current)


def ensure_scheduler_valid(scheduler: dict, mode: str) -> None:
    required_fields = [
        "version",
        "timezone",
        "mode",
        "pack_naming",
        "publish_policy",
        "image_policy",
        "topic",
        "audience",
        "core_value",
        "cta",
    ]
    missing = [field for field in required_fields if field not in scheduler]
    if missing:
        raise SystemExit(f"Scheduler missing required fields: {', '.join(missing)}")
    if "topic_slug" not in scheduler["pack_naming"]:
        raise SystemExit("Scheduler pack_naming.topic_slug is required.")

    allow_publish = bool(scheduler["publish_policy"].get("allow_publish", False))
    if mode == "publish" and not allow_publish:
        raise SystemExit("Scheduler publish_policy.allow_publish=false, refusing to publish.")


def sync_brief_from_scheduler(pack_dir: Path, scheduler: dict) -> None:
    brief_path = pack_dir / "brief.md"
    if brief_path.exists() and "Topic slug:" in read_text(brief_path):
        return
    pack_date = "-".join(pack_dir.name.split("-")[:3]) if "-" in pack_dir.name else ""

    audience = ", ".join(str(item) for item in scheduler.get("audience", []))
    brief = "\n".join(
        [
            "# Brief",
            "",
            f"- Date: {pack_date}",
            f"- Topic slug: {scheduler['pack_naming']['topic_slug']}",
            f"- Audience: {audience}",
            f"- Core value proposition: {scheduler.get('core_value', '')}",
            f"- Evidence source: {scheduler.get('evidence_source', '')}",
            f"- CTA: {scheduler.get('cta', '')}",
            f"- Must not claim: {scheduler.get('must_not_claim', '')}",
            "- Competitive references:",
        ]
    )
    write_text(brief_path, brief)


def validate_pack(pack_dir: Path, profile: str) -> dict:
    output = run_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "xhs_pack_validate.py"),
            "--pack-dir",
            str(pack_dir),
            "--profile",
            profile,
        ]
    )
    return json.loads(output)


def ensure_review_approved(pack_dir: Path, scheduler: dict) -> None:
    if not bool(scheduler.get("publish_policy", {}).get("require_review_approved", True)):
        return
    review = read_json(pack_dir / "review_report.json")
    if review.get("decision") != "approved":
        raise SystemExit("review_report.json is not approved; refusing publisher stage.")


def resolve_adapter(name: str):
    adapter_name = (name or os.environ.get("XHS_PUBLISHER_ADAPTER", "mock")).strip()
    if adapter_name == "mock":
        return MockPublisherAdapter(), "mock"
    if adapter_name == "codex-cli":
        skill_root_text = os.environ.get("XHS_SKILL_ROOT", "").strip()
        skill_root = Path(skill_root_text).expanduser().resolve() if skill_root_text else DEFAULT_SKILL_ROOT
        cli_text = os.environ.get("XHS_PUBLISHER_CLI", "").strip()
        cli_path = Path(cli_text).expanduser().resolve() if cli_text else skill_root / "scripts/cli.py"
        if not cli_path.exists():
            raise SystemExit(
                "Publisher CLI not found. Set XHS_PUBLISHER_CLI or XHS_SKILL_ROOT to a valid installation."
            )
        return CodexCliPublisherAdapter(PublisherConfig(skill_root=skill_root, cli_path=cli_path)), "codex-cli"
    raise SystemExit(f"Unsupported publisher adapter: {adapter_name}")


def build_fill_args(pack_dir: Path, scheduler: dict) -> list[str]:
    image_path = resolve_image_path(pack_dir, scheduler)
    tags = normalize_tags(read_text(pack_dir / "hashtags.txt")) if (pack_dir / "hashtags.txt").exists() else []
    args = [
        "--title-file",
        str((pack_dir / "title.txt").resolve()),
        "--content-file",
        str((pack_dir / "content.txt").resolve()),
        "--images",
        str(image_path),
    ]
    if tags:
        args.extend(["--tags", *tags])
    return args


def fail_workflow(pack_dir: Path, state: str, reason: str, step: str) -> None:
    transition(
        pack_dir,
        state,
        step,
        allow_any=True,
        publisher_status="failed",
        failed_reason=reason,
    )
    update_publish_result(pack_dir, status="failed", error=reason)
    record_run(pack_dir, "xhs-orchestrator", step, "failed", reason)


def run_prepare_only(pack_dir: Path) -> None:
    transition(
        pack_dir,
        "reviewed",
        "prepare-only",
        allow_any=True,
        content_status="done",
        image_status="done",
        review_status="approved",
        publisher_status="pending",
        failed_reason="",
    )
    update_publish_result(pack_dir, status="pending", error="", mode="prepare_only")
    record_run(pack_dir, "xhs-orchestrator", "workflow", "completed", "Stopped at prepare_only.")


def run_publisher_flow(pack_dir: Path, scheduler: dict, mode: str, adapter_name: str) -> None:
    adapter, resolved_adapter_name = resolve_adapter(adapter_name)
    ensure_review_approved(pack_dir, scheduler)

    review_report = validate_pack(pack_dir, "review")
    if review_report.get("decision") == "blocked":
        raise SystemExit("Pack did not pass review-profile validation.")

    transition(
        pack_dir,
        "ready_to_fill",
        "review",
        allow_any=True,
        content_status="done",
        image_status="done",
        review_status="approved",
        publisher_status="pending",
        failed_reason="",
    )
    validate_pack(pack_dir, "publish")

    logged_in = adapter.check_login().get("logged_in")
    if not logged_in:
        raise SystemExit("Publisher adapter reports not logged in.")

    update_publish_result(pack_dir, mode=mode, error="", status="pending")
    fill_args = build_fill_args(pack_dir, scheduler)

    preflight_output = adapter.run_action("preflight-publish", [])
    record_run(pack_dir, "xhs-orchestrator", "preflight-publish", "completed", preflight_output or "Preflight passed.")
    update_publish_result(pack_dir, status="preflight_ok", error="")

    fill_output = adapter.run_action("fill-publish", fill_args)
    transition(
        pack_dir,
        "filled",
        "fill-publish",
        allow_any=True,
        publisher_status="filled",
        failed_reason="",
    )
    record_run(pack_dir, "xhs-orchestrator", "fill-publish", "completed", fill_output or "Filled publish form.")
    update_publish_result(
        pack_dir,
        status="filled",
        title=read_text(pack_dir / "title.txt"),
        images=[resolve_image_reference(pack_dir, scheduler)],
        error="",
    )

    if mode == "save_draft":
        save_output = adapter.run_action("save-draft", [])
        transition(
            pack_dir,
            "filled",
            "save-draft",
            allow_any=True,
            publisher_status="draft_saved",
            failed_reason="",
        )
        record_run(pack_dir, "xhs-orchestrator", "save-draft", "completed", save_output or "Saved draft.")
        update_publish_result(pack_dir, status="draft_saved", error="")
    else:
        publish_output = adapter.run_action("click-publish", [])
        transition(
            pack_dir,
            "published",
            "click-publish",
            allow_any=True,
            publisher_status="published",
            failed_reason="",
        )
        record_run(pack_dir, "xhs-orchestrator", "click-publish", "completed", publish_output or "Published note.")
        update_publish_result(pack_dir, status="published", error="")

    state = read_json(pack_dir / "workflow_state.json")
    state["publisher_adapter"] = resolved_adapter_name
    state["updated_at"] = now_iso()
    write_json(pack_dir / "workflow_state.json", state)


def run_workflow(args: argparse.Namespace) -> int:
    scheduler = read_json(Path(args.scheduler_file))
    ensure_scheduler_valid(scheduler, args.mode)

    packs_root = Path(args.packs_root).expanduser().resolve()
    packs_root.mkdir(parents=True, exist_ok=True)
    pack_dir = ensure_pack(packs_root, scheduler, args.date, args.pack_dir)
    sync_brief_from_scheduler(pack_dir, scheduler)
    record_run(pack_dir, "xhs-orchestrator", "workflow", "started", f"Workflow started in mode={args.mode}.")

    try:
        if args.mode == "prepare_only":
            run_prepare_only(pack_dir)
        else:
            run_publisher_flow(pack_dir, scheduler, args.mode, args.publisher_adapter)
    except SystemExit as exc:
        reason = str(exc) or "workflow failed"
        fail_workflow(pack_dir, "failed", reason, "workflow")
        raise

    record_run(pack_dir, "xhs-orchestrator", "workflow", "completed", f"Workflow completed in mode={args.mode}.")

    print(
        json.dumps(
            {
                "pack_dir": str(pack_dir),
                "mode": args.mode,
                "status": read_json(pack_dir / "publish_result.json").get("status"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a draft-first XiaoHongShu workflow from a scheduler.")
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
