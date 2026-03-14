---
name: openclaw-xhs-workflow
description: Build and run reviewable XiaoHongShu content-pack workflows with OpenClaw. Use when creating packs, advancing pack state, validating publish readiness, or saving to draft/publish through a pluggable publisher adapter.
---

# OpenClaw XiaoHongShu Workflow

This skill manages a XiaoHongShu workflow as a stable pack contract instead of ad hoc prompts.

Use it when the task is to:

- create a new pack from a scheduler
- run or resume a pack workflow
- validate a pack before review or publishing
- save a completed pack to draft or publish through a configured adapter

## Rules

- Treat the pack directory as the source of truth for workflow state and outputs.
- Read the scheduler JSON before generating or publishing anything.
- Respect `mode` and `publish_policy`; do not publish when the scheduler forbids it.
- On failure, write the failure back to `workflow_state.json`, `publish_result.json`, and `agent_runs.json`.
- Prefer `save_draft` as the default publisher path unless the scheduler explicitly allows publish.

## Workflow

1. Create or resolve the pack directory with `scripts/scaffold_pack.sh` or an existing `pack_dir`.
2. Read the scheduler contract in `references/scheduler_schema.md`.
3. Advance the pack through the state machine in `references/state_machine.md`.
4. Validate the pack before review/publish with `scripts/xhs_pack_validate.py`.
5. Use the configured publisher adapter only for publisher-stage actions.

## Resources

- Pack contract: `references/pack_schema.md`
- Scheduler contract: `references/scheduler_schema.md`
- State machine: `references/state_machine.md`
- Publisher adapter boundary: `references/publisher_contract.md`
- Integration guidance: `references/business_integration.md`

## Scripts

- `scripts/scaffold_pack.sh`
- `scripts/xhs_pack_state.py`
- `scripts/xhs_pack_validate.py`
- `scripts/xhs_manifest_builder.py`
- `scripts/xhs_workflow.py`
- `scripts/run_manual.py`

Only load the reference file relevant to the task at hand. Do not load every reference by default.
