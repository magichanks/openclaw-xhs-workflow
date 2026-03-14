---
name: openclaw-xhs-workflow
description: Build and run reviewable XiaoHongShu content-pack workflows with OpenClaw. Use when creating packs, advancing pack state, validating publish readiness, or saving to draft/publish through a pluggable publisher adapter.
---

# OpenClaw XiaoHongShu Workflow

This skill manages a XiaoHongShu workflow as a stable pack contract instead of ad hoc prompts.

Use it when the task is to:

- create a new pack from a scheduler
- run or resume a full pack workflow
- validate a pack before review or publishing
- save a completed pack to draft or publish through a configured adapter

For the current engine, the strongest path is:

- let OpenClaw or mock adapters handle `research` and `copy`
- let `mock`, `source-file`, `openai-images`, or `gemini-images` handle `image`
- let `validator` or OpenClaw handle `review`
- let a publisher adapter handle `save_draft` or `publish`, preferably `openclaw`

## Rules

- Treat the pack directory as the source of truth for workflow state and outputs.
- Read the scheduler JSON before generating or publishing anything.
- Respect `mode` and `publish_policy`; do not publish when the scheduler forbids it.
- On failure, write the failure back to `workflow_state.json`, `publish_result.json`, and `agent_runs.json`.
- Prefer `save_draft` as the default publisher path unless the scheduler explicitly allows publish.
- If `--start-at` is later than `research`, treat the existing pack files as source of truth.

## Workflow

1. Create or resolve the pack directory with `scripts/scaffold_pack.sh` or an existing `pack_dir`.
2. Read the scheduler contract in `references/scheduler_schema.md`.
3. Run `research -> copy -> image -> review`.
4. If `mode` is not `prepare_only`, run the configured publisher path.
5. Persist all stage outputs and status transitions back into the pack.

For OpenClaw users, this usually means:

1. Your business repo provides scheduler files and any source assets.
2. This skill owns the stable workflow contract and stage transitions.
3. You can resume from a specific stage by passing `--start-at`.

## Resources

- Pack contract: `references/pack_schema.md`
- Scheduler contract: `references/scheduler_schema.md`
- State machine: `references/state_machine.md`
- Publisher adapter boundary: `references/publisher_contract.md`
- Image adapter setup: `references/image_adapter_setup.md`
- OpenClaw setup guide: `references/openclaw_setup_guide.md`
- Integration guidance: `references/business_integration.md`

## Scripts

- `scripts/scaffold_pack.sh`
- `scripts/xhs_pack_state.py`
- `scripts/xhs_pack_validate.py`
- `scripts/xhs_manifest_builder.py`
- `scripts/xhs_workflow.py`
- `scripts/run_manual.py`

Only load the reference file relevant to the task at hand. Do not load every reference by default.
