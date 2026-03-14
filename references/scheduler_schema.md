# Scheduler Schema

Scheduler JSON is the policy input for a workflow run.

## Minimal Fields

- `version`
- `timezone`
- `mode`
- `pack_naming.topic_slug`
- `research_policy`
- `copy_policy`
- `publish_policy`
- `image_policy`
- `review_policy`
- `topic`
- `audience`
- `core_value`
- `cta`

## Core Rules

- One scheduler schema should serve both cron and manual triggers.
- Scheduler files define policy, not run state.
- Scheduler files must not contain credentials, browser profile paths, or machine-private directories.
- `allow_publish=false` must prevent final publish even if the rest of the workflow succeeds.

## Stage Policies

### `research_policy`

Controls how `research.md` and `research.json` are produced.

Recommended fields:

- `adapter`: `mock` or `openclaw`
- `keywords`: optional keyword list
- `limit`: optional integer

### `copy_policy`

Controls how `title.txt`, `content.txt`, `hashtags.txt`, `asset_plan.md`, `image_prompts.md`, and `review_checklist.md` are produced.

Recommended fields:

- `adapter`: `mock` or `openclaw`
- `language`: optional, default `zh-CN`

### `image_policy`

Controls how the cover asset and `assets/manifest.json` are produced.

Required fields:

- `adapter`: `mock` or `source-file`
- `required_output`
- `required_role`
- `count`

Optional fields:

- `source_file`: required when `adapter=source-file`
- `model`: used by `openai-images` or `gemini-images`
- `size`: used by `openai-images`
- `quality`: optional for `openai-images`
- `background`: optional for `openai-images`
- `aspect_ratio`: optional for `gemini-images`
- `image_size`: optional for `gemini-images`
- `api_key_env`: optional override env var name for `openai-images`
- `api_key_env`: optional override env var name for `gemini-images`

### `review_policy`

Controls how `review_report.json` is produced.

Recommended fields:

- `adapter`: `validator` or `openclaw`

`validator` means deterministic validation is the source of truth.
`openclaw` means deterministic validation still gates the result, but OpenClaw also writes a human-readable summary.

## OpenClaw Block

If you use OpenClaw for `research`, `copy`, or `review`, the scheduler may include:

```json
{
  "openclaw": {
    "agent": "main",
    "session_id": "xhs-workflow",
    "thinking": "medium"
  }
}
```

This block should contain workflow-facing OpenClaw settings only.
Do not store user secrets or machine-private absolute paths here.

## Image Setup Reference

For real image adapters and environment-variable setup, see:

- `references/image_adapter_setup.md`
