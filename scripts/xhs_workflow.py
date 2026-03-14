#!/usr/bin/env python3
"""Run a full XiaoHongShu workflow from scheduler to review, then optionally draft or publish."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.openclaw_agent import OpenClawAgentClient, OpenClawConfig
from adapters.image_gemini import GeminiImageConfig, generate_image as generate_gemini_image
from adapters.image_openai import OpenAIImageConfig, generate_image as generate_openai_image
from adapters.xhs_codex_cli import CodexCliPublisherAdapter, PublisherConfig
from adapters.xhs_mock_publisher import MockPublisherAdapter


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SKILL_ROOT = Path.home() / ".codex/skills/xiaohongshu-skills"
STAGE_ORDER = ["research", "copy", "image", "review", "publisher"]
MOCK_PNG_HEX = (
    "89504e470d0a1a0a0000000d4948445200000001000000010804000000b51c0c02"
    "0000000b4944415478da63fcff1f0003030200eed9d2740000000049454e44ae42"
    "6082"
)


@dataclass
class WorkflowContext:
    packs_root: Path
    pack_dir: Path
    scheduler: dict[str, Any]
    mode: str
    publisher_adapter_name: str
    start_at: str
    openclaw_client: OpenClawAgentClient | None


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_command(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if result.returncode != 0:
        details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise SystemExit(details or "command failed")
    return "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def ensure_file(path: Path, content: str) -> None:
    if not path.exists():
        write_text(path, content)


def stage_enabled(start_at: str, stage: str) -> bool:
    return STAGE_ORDER.index(stage) >= STAGE_ORDER.index(start_at)


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


def resolve_pack_dir(packs_root: Path, scheduler: dict[str, Any], date_text: str) -> Path:
    slug = scheduler["pack_naming"]["topic_slug"]
    return packs_root / f"{date_text}-{slug}"


def ensure_pack(packs_root: Path, scheduler: dict[str, Any], date_text: str, pack_dir_arg: str | None) -> Path:
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


def resolve_image_path(pack_dir: Path, scheduler: dict[str, Any]) -> Path:
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


def resolve_image_reference(pack_dir: Path, scheduler: dict[str, Any]) -> str:
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


def update_review_report(pack_dir: Path, **patch: object) -> None:
    path = pack_dir / "review_report.json"
    current = read_json(path)
    current.update(patch)
    current["updated_at"] = now_iso()
    write_json(path, current)


def build_scheduler_defaults(scheduler: dict[str, Any]) -> dict[str, Any]:
    scheduler = dict(scheduler)
    scheduler.setdefault("keywords", [])
    scheduler.setdefault("research_policy", {"adapter": "mock", "limit": 5})
    scheduler.setdefault("copy_policy", {"adapter": "mock", "language": "zh-CN"})
    image_policy = dict(scheduler.get("image_policy", {}))
    image_policy.setdefault("adapter", "mock")
    image_policy.setdefault("count", 1)
    image_policy.setdefault("required_role", "cover")
    image_policy.setdefault("required_output", "assets/cover.png")
    image_policy.setdefault("forbid_detail_images", True)
    image_policy.setdefault("model", os.environ.get("XHS_IMAGE_MODEL", "gpt-image-1.5"))
    image_policy.setdefault("size", os.environ.get("XHS_IMAGE_SIZE", "1024x1024"))
    scheduler["image_policy"] = image_policy
    scheduler.setdefault("review_policy", {"adapter": "validator"})
    scheduler.setdefault(
        "openclaw",
        {
            "agent": os.environ.get("XHS_OPENCLAW_AGENT", "main"),
            "session_id": os.environ.get("XHS_OPENCLAW_SESSION_ID", "xhs-workflow"),
            "thinking": os.environ.get("XHS_OPENCLAW_THINKING", "medium"),
        },
    )
    scheduler.setdefault("evidence_source", "")
    scheduler.setdefault("must_not_claim", "")
    return scheduler


def ensure_scheduler_valid(scheduler: dict[str, Any], mode: str) -> None:
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


def sync_brief_from_scheduler(pack_dir: Path, scheduler: dict[str, Any], date_text: str) -> None:
    audience = ", ".join(str(item) for item in scheduler.get("audience", []))
    brief = "\n".join(
        [
            "# Brief",
            "",
            f"- Date: {date_text}",
            f"- Topic slug: {scheduler['pack_naming']['topic_slug']}",
            f"- Audience: {audience}",
            f"- Core value proposition: {scheduler.get('core_value', '')}",
            f"- Evidence source: {scheduler.get('evidence_source', '')}",
            f"- CTA: {scheduler.get('cta', '')}",
            f"- Must not claim: {scheduler.get('must_not_claim', '')}",
            "- Competitive references:",
        ]
    )
    write_text(pack_dir / "brief.md", brief)


def validate_pack(pack_dir: Path, profile: str) -> dict[str, Any]:
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
    payload = json.loads(output)
    if not isinstance(payload, dict):
        raise SystemExit("Pack validation returned an invalid payload.")
    return payload


def ensure_review_approved(pack_dir: Path, scheduler: dict[str, Any]) -> None:
    if not bool(scheduler.get("publish_policy", {}).get("require_review_approved", True)):
        return
    review = read_json(pack_dir / "review_report.json")
    if review.get("decision") != "approved":
        raise SystemExit("review_report.json is not approved; refusing publisher stage.")


def resolve_openclaw_client(scheduler: dict[str, Any], cwd: Path) -> OpenClawAgentClient:
    config = scheduler.get("openclaw", {})
    bin_path = str(config.get("bin_path") or os.environ.get("OPENCLAW_BIN") or shutil.which("openclaw") or "")
    if not bin_path:
        raise SystemExit("OpenClaw is required for adapter=openclaw stages, but openclaw binary was not found.")
    return OpenClawAgentClient(
        OpenClawConfig(
            agent=str(config.get("agent", "main")),
            session_id=str(config.get("session_id", "xhs-workflow")),
            thinking=str(config.get("thinking", "medium")),
            bin_path=bin_path,
            cwd=cwd,
        )
    )


def resolve_publisher_adapter(name: str):
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


def build_fill_args(pack_dir: Path, scheduler: dict[str, Any]) -> list[str]:
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


def scheduler_json(scheduler: dict[str, Any]) -> str:
    return json.dumps(scheduler, ensure_ascii=False, indent=2)


def cover_prompt_from_pack(pack_dir: Path, scheduler: dict[str, Any]) -> str:
    prompt_path = pack_dir / "image_prompts.md"
    if prompt_path.exists():
        for line in prompt_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("- Prompt:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    return value
    return (
        f"Create one Xiaohongshu cover image. Topic: {scheduler['topic']}. "
        f"Core value: {scheduler['core_value']}. Audience: {', '.join(scheduler['audience'])}. "
        "Keep it clean, honest, readable, and suitable for a single cover image."
    )


def run_research_stage(ctx: WorkflowContext) -> None:
    adapter = str(ctx.scheduler.get("research_policy", {}).get("adapter", "mock"))
    keywords = ctx.scheduler.get("research_policy", {}).get("keywords") or ctx.scheduler.get("keywords") or [ctx.scheduler["topic"]]
    limit = int(ctx.scheduler.get("research_policy", {}).get("limit", 5))

    if adapter == "mock":
        research_json: dict[str, Any] = {
            "topic": ctx.scheduler["topic"],
            "keywords": keywords[:limit],
            "angles": [
                f"面向{str(ctx.scheduler['audience'][0])}，用真实工作流解释 {ctx.scheduler['core_value']}",
                "强调可验证能力，不做夸张承诺",
            ],
            "pain_points": [
                "流程断点多，工具之间上下文容易丢失",
                "demo 顺利，但真实发布链路容易卡住",
            ],
            "approved_claims": [ctx.scheduler["core_value"]],
            "risky_claims": [ctx.scheduler.get("must_not_claim", "")] if ctx.scheduler.get("must_not_claim") else [],
        }
        research_md = "\n".join(
            [
                "# Research Summary",
                "",
                f"- Topic: {ctx.scheduler['topic']}",
                f"- Audience: {', '.join(ctx.scheduler['audience'])}",
                f"- Keywords: {', '.join(keywords[:limit])}",
                "",
                "## Suggested Angles",
                "",
                *[f"- {item}" for item in research_json["angles"]],
                "",
                "## Pain Points",
                "",
                *[f"- {item}" for item in research_json["pain_points"]],
            ]
        )
    elif adapter == "openclaw":
        if ctx.openclaw_client is None:
            raise SystemExit("research adapter=openclaw requires OpenClaw to be available.")
        prompt = f"""
Create Xiaohongshu research notes for one content pack.

Return exactly one JSON object and nothing else.

JSON schema:
{{
  "research_markdown": "full markdown for research.md",
  "research_json": {{
    "topic": "string",
    "keywords": ["string"],
    "angles": ["string"],
    "pain_points": ["string"],
    "approved_claims": ["string"],
    "risky_claims": ["string"]
  }}
}}

Use this scheduler as the source of truth:
```json
{scheduler_json(ctx.scheduler)}
```

Rules:
- Write in Simplified Chinese.
- Focus on verifiable positioning and audience pain points.
- Keep angles narrow and operational.
""".strip()
        payload = ctx.openclaw_client.run_structured(prompt)
        if not isinstance(payload, dict):
            raise SystemExit("OpenClaw research payload must be an object.")
        research_md = str(payload["research_markdown"])
        research_json = payload["research_json"]
    else:
        raise SystemExit(f"Unsupported research adapter: {adapter}")

    write_text(ctx.pack_dir / "research.md", research_md)
    write_json(ctx.pack_dir / "research.json", research_json)
    transition(
        ctx.pack_dir,
        "researched",
        "research",
        allow_any=True,
        content_status="pending",
        failed_reason="",
    )
    record_run(ctx.pack_dir, "xhs-orchestrator", "research", "completed", f"Research completed with adapter={adapter}.")


def run_copy_stage(ctx: WorkflowContext) -> None:
    adapter = str(ctx.scheduler.get("copy_policy", {}).get("adapter", "mock"))
    research_md = read_text(ctx.pack_dir / "research.md")

    if adapter == "mock":
        title = f"{ctx.scheduler['topic'][:18]}".strip() or "真诚分享一个工作流"
        hashtags = ["#小红书运营", "#工作流", "#真实分享"]
        content = "\n\n".join(
            [
                f"最近我更想从真实工作流的角度，聊聊 {ctx.scheduler['topic']}。",
                f"如果只看 demo，很多事情都很顺；但真正落到业务里，最关键的是 {ctx.scheduler['core_value']}。",
                "我越来越不想把 AI 产品讲得太万能。真正重要的是失败后怎么恢复、人工怎么接手、最后一公里有没有真的落地。",
                ctx.scheduler["cta"],
            ]
        )
        asset_plan_md = "\n".join(
            [
                "# Asset Plan",
                "",
                "## Cover",
                f"- Primary message: {ctx.scheduler['core_value']}",
                "- Source: generated or operator-provided cover",
                "- Visual direction: simple, readable, honest",
                "- Keep it to one image only: yes",
                "- Redaction notes: no private data",
            ]
        )
        image_prompts_md = "\n".join(
            [
                "# Image Prompts",
                "",
                "## Cover",
                f"- Goal: express {ctx.scheduler['core_value']}",
                f"- Prompt: clean editorial cover, Chinese headline, honest developer perspective, topic is {ctx.scheduler['topic']}",
            ]
        )
        review_checklist = "\n".join(
            [
                "# Review Checklist",
                "",
                "- [ ] Claims are verifiable",
                "- [ ] Tone is honest rather than over-promising",
                "- [ ] CTA is explicit",
                "- [ ] No private or machine-specific data",
            ]
        )
    elif adapter == "openclaw":
        if ctx.openclaw_client is None:
            raise SystemExit("copy adapter=openclaw requires OpenClaw to be available.")
        prompt = f"""
Create Xiaohongshu copy assets for one workflow pack.

Return exactly one JSON object and nothing else.

JSON schema:
{{
  "title": "final title",
  "content": "final body",
  "hashtags": ["tag1", "tag2", "tag3"],
  "asset_plan_markdown": "full markdown for asset_plan.md",
  "image_prompts_markdown": "full markdown for image_prompts.md",
  "review_checklist_markdown": "full markdown for review_checklist.md"
}}

Use this scheduler as the source of truth:
```json
{scheduler_json(ctx.scheduler)}
```

Current research:
```md
{research_md}
```

Rules:
- Write in Simplified Chinese.
- Keep the post focused on one core value.
- Avoid unverifiable growth or revenue claims.
- The tone should feel sincere and operational, not hype-driven.
""".strip()
        payload = ctx.openclaw_client.run_structured(prompt)
        if not isinstance(payload, dict):
            raise SystemExit("OpenClaw copy payload must be an object.")
        title = str(payload["title"])
        content = str(payload["content"])
        hashtags = payload["hashtags"]
        asset_plan_md = str(payload["asset_plan_markdown"])
        image_prompts_md = str(payload["image_prompts_markdown"])
        review_checklist = str(payload["review_checklist_markdown"])
    else:
        raise SystemExit(f"Unsupported copy adapter: {adapter}")

    write_text(ctx.pack_dir / "title.txt", title)
    write_text(ctx.pack_dir / "content.txt", content)
    if isinstance(hashtags, list):
        write_text(ctx.pack_dir / "hashtags.txt", " ".join(f"#{str(tag).lstrip('#')}" for tag in hashtags))
    else:
        write_text(ctx.pack_dir / "hashtags.txt", str(hashtags))
    write_text(ctx.pack_dir / "asset_plan.md", asset_plan_md)
    write_text(ctx.pack_dir / "image_prompts.md", image_prompts_md)
    write_text(ctx.pack_dir / "review_checklist.md", review_checklist)
    transition(
        ctx.pack_dir,
        "drafted",
        "copy",
        allow_any=True,
        content_status="done",
        failed_reason="",
    )
    record_run(ctx.pack_dir, "xhs-orchestrator", "copy", "completed", f"Copy completed with adapter={adapter}.")


def create_manifest(pack_dir: Path, output_rel: str, model: str, prompt_hash: str, status: str) -> None:
    asset_path = pack_dir / output_rel
    manifest = {
        "pack_dir": str(pack_dir),
        "assets": [
            {
                "path": output_rel,
                "role": "cover",
                "model": model,
                "prompt_hash": prompt_hash,
                "status": status,
                "width": 1,
                "height": 1,
                "bytes": asset_path.stat().st_size if asset_path.exists() else 0,
            }
        ],
        "updated_at": now_iso(),
    }
    write_json(pack_dir / "assets" / "manifest.json", manifest)


def run_image_stage(ctx: WorkflowContext) -> None:
    policy = ctx.scheduler.get("image_policy", {})
    adapter = str(policy.get("adapter", "mock"))
    output_rel = str(policy.get("required_output", "assets/cover.png"))
    output_path = ctx.pack_dir / output_rel
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = cover_prompt_from_pack(ctx.pack_dir, ctx.scheduler)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    if adapter == "mock":
        output_path.write_bytes(bytes.fromhex(MOCK_PNG_HEX))
        create_manifest(ctx.pack_dir, output_rel, "mock-image", prompt_hash, "generated")
    elif adapter == "source-file":
        source_text = str(policy.get("source_file", "")).strip()
        if not source_text:
            raise SystemExit("image_policy.adapter=source-file requires image_policy.source_file.")
        source_path = Path(source_text).expanduser()
        if not source_path.is_absolute():
            source_path = ctx.packs_root / source_path
        source_path = source_path.resolve()
        if not source_path.exists():
            raise SystemExit(f"image source file does not exist: {source_path}")
        shutil.copyfile(source_path, output_path)
        create_manifest(ctx.pack_dir, output_rel, "source-file", prompt_hash, "generated")
    elif adapter == "openai-images":
        api_key_env = str(policy.get("api_key_env", "")).strip()
        api_key = os.environ.get(api_key_env, "").strip() if api_key_env else ""
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise SystemExit("openai-images adapter requires OPENAI_API_KEY or image_policy.api_key_env.")
        base_url = str(policy.get("base_url") or os.environ.get("XHS_IMAGE_BASE_URL") or "https://api.openai.com/v1").strip()
        model = str(policy.get("model") or os.environ.get("XHS_IMAGE_MODEL") or "gpt-image-1.5").strip()
        size = str(policy.get("size") or os.environ.get("XHS_IMAGE_SIZE") or "1024x1024").strip()
        quality = str(policy.get("quality") or os.environ.get("XHS_IMAGE_QUALITY") or "").strip() or None
        background = str(policy.get("background") or os.environ.get("XHS_IMAGE_BACKGROUND") or "").strip() or None
        image_bytes, meta = generate_openai_image(
            OpenAIImageConfig(
                api_key=api_key,
                base_url=base_url,
                model=model,
                size=size,
                quality=quality,
                background=background,
            ),
            prompt,
        )
        output_path.write_bytes(image_bytes)
        create_manifest(ctx.pack_dir, output_rel, str(meta.get("model", model)), prompt_hash, str(meta.get("status", "generated")))
    elif adapter == "gemini-images":
        api_key_env = str(policy.get("api_key_env", "")).strip()
        api_key = os.environ.get(api_key_env, "").strip() if api_key_env else ""
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise SystemExit("gemini-images adapter requires GEMINI_API_KEY or image_policy.api_key_env.")
        base_url = str(policy.get("base_url") or os.environ.get("XHS_GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta").strip()
        model = str(policy.get("model") or os.environ.get("XHS_GEMINI_IMAGE_MODEL") or "gemini-2.5-flash-image").strip()
        aspect_ratio = str(policy.get("aspect_ratio") or os.environ.get("XHS_GEMINI_ASPECT_RATIO") or "").strip() or None
        image_size = str(policy.get("image_size") or os.environ.get("XHS_GEMINI_IMAGE_SIZE") or "").strip() or None
        image_bytes, meta = generate_gemini_image(
            GeminiImageConfig(
                api_key=api_key,
                base_url=base_url,
                model=model,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            ),
            prompt,
        )
        output_path.write_bytes(image_bytes)
        create_manifest(ctx.pack_dir, output_rel, str(meta.get("model", model)), prompt_hash, str(meta.get("status", "generated")))
    else:
        raise SystemExit(f"Unsupported image adapter: {adapter}")

    transition(
        ctx.pack_dir,
        "imaged",
        "image",
        allow_any=True,
        image_status="done",
        failed_reason="",
    )
    record_run(ctx.pack_dir, "xhs-orchestrator", "image", "completed", f"Image stage completed with adapter={adapter}.")


def run_review_stage(ctx: WorkflowContext) -> None:
    adapter = str(ctx.scheduler.get("review_policy", {}).get("adapter", "validator"))
    validation = validate_pack(ctx.pack_dir, "review")
    decision = str(validation.get("decision", "blocked"))
    findings = validation.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    if adapter == "validator":
        summary = "Pack passed deterministic validation and is ready for publisher stage." if decision == "approved" else "Pack needs fixes before publisher stage."
    elif adapter == "openclaw":
        if ctx.openclaw_client is None:
            raise SystemExit("review adapter=openclaw requires OpenClaw to be available.")
        prompt = f"""
Summarize a Xiaohongshu pack review.

Return exactly one JSON object and nothing else.

JSON schema:
{{
  "summary": "short review summary",
  "notes": ["optional short notes"]
}}

Validation report:
```json
{json.dumps(validation, ensure_ascii=False, indent=2)}
```

Rules:
- Write in Simplified Chinese.
- Do not override the deterministic decision.
- Keep the summary concise and operational.
""".strip()
        payload = ctx.openclaw_client.run_structured(prompt)
        if not isinstance(payload, dict):
            raise SystemExit("OpenClaw review payload must be an object.")
        notes = payload.get("notes", [])
        if isinstance(notes, list) and notes:
            findings.extend({"level": "info", "code": "openclaw_note", "message": str(item)} for item in notes)
        summary = str(payload.get("summary", "")).strip() or "OpenClaw generated a review summary."
    else:
        raise SystemExit(f"Unsupported review adapter: {adapter}")

    update_review_report(ctx.pack_dir, decision=decision, summary=summary, findings=findings)
    if decision == "approved":
        transition(
            ctx.pack_dir,
            "reviewed",
            "review",
            allow_any=True,
            review_status="approved",
            failed_reason="",
        )
    else:
        transition(
            ctx.pack_dir,
            "blocked",
            "review",
            allow_any=True,
            review_status=decision,
            failed_reason="Pack did not pass review stage.",
        )
        raise SystemExit("Pack did not pass review stage.")
    record_run(ctx.pack_dir, "xhs-orchestrator", "review", "completed", f"Review completed with adapter={adapter}.")


def run_publisher_stage(ctx: WorkflowContext) -> None:
    adapter, resolved_adapter_name = resolve_publisher_adapter(ctx.publisher_adapter_name)
    ensure_review_approved(ctx.pack_dir, ctx.scheduler)
    validate_pack(ctx.pack_dir, "publish")

    transition(
        ctx.pack_dir,
        "ready_to_fill",
        "review",
        allow_any=True,
        content_status="done",
        image_status="done",
        review_status="approved",
        publisher_status="pending",
        failed_reason="",
    )

    logged_in = adapter.check_login().get("logged_in")
    if not logged_in:
        raise SystemExit("Publisher adapter reports not logged in.")

    update_publish_result(ctx.pack_dir, mode=ctx.mode, error="", status="pending")
    fill_args = build_fill_args(ctx.pack_dir, ctx.scheduler)

    preflight_output = adapter.run_action("preflight-publish", [])
    record_run(ctx.pack_dir, "xhs-orchestrator", "preflight-publish", "completed", preflight_output or "Preflight passed.")
    update_publish_result(ctx.pack_dir, status="preflight_ok", error="")

    fill_output = adapter.run_action("fill-publish", fill_args)
    transition(
        ctx.pack_dir,
        "filled",
        "fill-publish",
        allow_any=True,
        publisher_status="filled",
        failed_reason="",
    )
    record_run(ctx.pack_dir, "xhs-orchestrator", "fill-publish", "completed", fill_output or "Filled publish form.")
    update_publish_result(
        ctx.pack_dir,
        status="filled",
        title=read_text(ctx.pack_dir / "title.txt"),
        images=[resolve_image_reference(ctx.pack_dir, ctx.scheduler)],
        error="",
    )

    if ctx.mode == "save_draft":
        save_output = adapter.run_action("save-draft", [])
        transition(
            ctx.pack_dir,
            "filled",
            "save-draft",
            allow_any=True,
            publisher_status="draft_saved",
            failed_reason="",
        )
        record_run(ctx.pack_dir, "xhs-orchestrator", "save-draft", "completed", save_output or "Saved draft.")
        update_publish_result(ctx.pack_dir, status="draft_saved", error="")
    else:
        publish_output = adapter.run_action("click-publish", [])
        transition(
            ctx.pack_dir,
            "published",
            "click-publish",
            allow_any=True,
            publisher_status="published",
            failed_reason="",
        )
        record_run(ctx.pack_dir, "xhs-orchestrator", "click-publish", "completed", publish_output or "Published note.")
        update_publish_result(ctx.pack_dir, status="published", error="")

    state = read_json(ctx.pack_dir / "workflow_state.json")
    state["publisher_adapter"] = resolved_adapter_name
    state["updated_at"] = now_iso()
    write_json(ctx.pack_dir / "workflow_state.json", state)


def run_workflow(args: argparse.Namespace) -> int:
    raw_scheduler = read_json(Path(args.scheduler_file))
    scheduler = build_scheduler_defaults(raw_scheduler)
    ensure_scheduler_valid(scheduler, args.mode)

    packs_root = Path(args.packs_root).expanduser().resolve()
    packs_root.mkdir(parents=True, exist_ok=True)
    pack_dir = ensure_pack(packs_root, scheduler, args.date, args.pack_dir)
    sync_brief_from_scheduler(pack_dir, scheduler, args.date)

    openclaw_client = None
    if any(
        str(scheduler.get(f"{stage}_policy", {}).get("adapter", "")) == "openclaw"
        for stage in ("research", "copy", "review")
    ):
        openclaw_client = resolve_openclaw_client(scheduler, packs_root)

    ctx = WorkflowContext(
        packs_root=packs_root,
        pack_dir=pack_dir,
        scheduler=scheduler,
        mode=args.mode,
        publisher_adapter_name=args.publisher_adapter,
        start_at=args.start_at,
        openclaw_client=openclaw_client,
    )

    record_run(pack_dir, "xhs-orchestrator", "workflow", "started", f"Workflow started in mode={args.mode}, start_at={args.start_at}.")

    try:
        if stage_enabled(args.start_at, "research"):
            run_research_stage(ctx)
        if stage_enabled(args.start_at, "copy"):
            run_copy_stage(ctx)
        if stage_enabled(args.start_at, "image"):
            run_image_stage(ctx)
        if stage_enabled(args.start_at, "review"):
            run_review_stage(ctx)
        if args.mode != "prepare_only" and stage_enabled(args.start_at, "publisher"):
            run_publisher_stage(ctx)
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
                "start_at": args.start_at,
                "state": read_json(pack_dir / "workflow_state.json").get("state"),
                "status": read_json(pack_dir / "publish_result.json").get("status"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a full XiaoHongShu workflow from a scheduler.")
    parser.add_argument("--packs-root", required=True)
    parser.add_argument("--scheduler-file", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--pack-dir")
    parser.add_argument("--mode", choices=("prepare_only", "save_draft", "publish"), default="save_draft")
    parser.add_argument("--start-at", choices=STAGE_ORDER, default="research")
    parser.add_argument("--publisher-adapter", default=os.environ.get("XHS_PUBLISHER_ADAPTER", "mock"))
    args = parser.parse_args()
    return run_workflow(args)


if __name__ == "__main__":
    sys.exit(main())
