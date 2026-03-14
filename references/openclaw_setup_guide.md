# OpenClaw Setup Guide

This guide is for users who already work inside OpenClaw and want to get this workflow running with the fewest moving parts.

## Recommended Rollout

Do not start with every real integration turned on.

Use this order:

1. `mock` everywhere
2. `source-file` for image
3. `openclaw` for research/copy/review
4. `codex-cli` for publisher
5. `openai-images` or `gemini-images` for image generation

That order isolates failures and makes debugging much faster.

## Step 1: Copy the environment template

```bash
cp .env.example .env.local
```

Then fill only the values you actually need.

Minimum useful fields for local testing:

```bash
XHS_PUBLISHER_ADAPTER=mock
XHS_OPENCLAW_AGENT=main
XHS_OPENCLAW_SESSION_ID=xhs-workflow
XHS_OPENCLAW_THINKING=medium
```

## Step 2: Load the environment

In a shell:

```bash
set -a
source ./.env.local
set +a
```

If you prefer direnv or another secrets loader, that is fine too. The workflow only requires these values to be present in the environment.

## Step 3: Verify the local full flow first

This does not require a real image API, browser profile, or publisher login.

```bash
/usr/bin/python3 scripts/xhs_workflow.py \
  --packs-root ./tmp-packs \
  --scheduler-file ./assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --start-at research \
  --mode save_draft \
  --publisher-adapter mock
```

Expected result:

- `status` is `draft_saved`
- a new pack is created under `./tmp-packs`

## Step 4: Switch image to `source-file`

This is the safest first real-world step.

1. Put a real cover image somewhere in your business repo.
2. Copy `assets/examples/scheduler-openclaw-save-draft.json`.
3. Set:

```json
{
  "image_policy": {
    "adapter": "source-file",
    "source_file": "./source-assets/cover.png"
  }
}
```

Now the workflow still remains deterministic, but the output image is real.

## Step 5: Turn on OpenClaw for content stages

Use `openclaw` adapters only after the local mock path works.

Recommended scheduler settings:

```json
{
  "research_policy": {
    "adapter": "openclaw",
    "limit": 5
  },
  "copy_policy": {
    "adapter": "openclaw",
    "language": "zh-CN"
  },
  "review_policy": {
    "adapter": "openclaw"
  },
  "openclaw": {
    "agent": "main",
    "session_id": "xhs-workflow",
    "thinking": "medium"
  }
}
```

If you want deterministic review gating with a generated summary, keep:

- `review_policy.adapter = openclaw`

The workflow still uses deterministic validation to decide whether the pack is blocked.

## Step 6: Turn on the real publisher

Only do this after you have verified:

- OpenClaw can generate the pack
- the pack reaches `reviewed`
- `assets/manifest.json` points to one real cover image

Then set:

```bash
XHS_PUBLISHER_ADAPTER=codex-cli
XHS_SKILL_ROOT="$HOME/.codex/skills/xiaohongshu-skills"
```

Recommended first command:

```bash
/usr/bin/python3 scripts/xhs_workflow.py \
  --packs-root ./packs \
  --scheduler-file ./assets/examples/scheduler-openclaw-save-draft.json \
  --date 2026-03-14 \
  --start-at publisher \
  --pack-dir ./packs/2026-03-14-developer-honest-share \
  --mode save_draft \
  --publisher-adapter codex-cli
```

That keeps the risk low because you are only testing publisher-stage integration.

## Step 7: Turn on a real image API

### OpenAI

Set:

```bash
OPENAI_API_KEY=...
XHS_IMAGE_MODEL=gpt-image-1.5
```

Scheduler change:

```json
{
  "image_policy": {
    "adapter": "openai-images",
    "model": "gpt-image-1.5",
    "size": "1024x1024"
  }
}
```

### Gemini

Set:

```bash
GEMINI_API_KEY=...
XHS_GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

Scheduler change:

```json
{
  "image_policy": {
    "adapter": "gemini-images",
    "model": "gemini-2.5-flash-image",
    "aspect_ratio": "3:4"
  }
}
```

## Common Failure Modes

### 1. OpenClaw stage fails immediately

Check:

- `OPENCLAW_BIN`
- the `openclaw` binary is on `PATH`
- the configured OpenClaw `agent` exists

### 2. Publisher stage says not logged in

Check:

- `XHS_PUBLISHER_ADAPTER=codex-cli`
- `XHS_SKILL_ROOT`
- your XiaoHongShu browser/login environment

### 3. Image stage fails before generation

Check:

- the adapter name in `image_policy.adapter`
- required env vars exist
- `image_prompts.md` contains a usable `- Prompt:` line, or the fallback prompt is acceptable

### 4. Pack is blocked before publisher

Check:

- `review_report.json`
- `assets/manifest.json`
- `workflow_state.json`
- title/body/hashtags do not still contain placeholders

## Suggested First Real Workflow

For most users, this is the safest first production-shaped combination:

- `research_policy.adapter = openclaw`
- `copy_policy.adapter = openclaw`
- `image_policy.adapter = source-file`
- `review_policy.adapter = validator`
- `publisher-adapter = codex-cli`

That keeps the fragile parts separated:

- OpenClaw handles text generation
- a human or business repo controls the cover image
- deterministic validation decides whether the workflow can continue
- the publisher only runs after the pack is ready
