---
name: openclaw-xhs-workflow
description: Run a resumable XiaoHongShu workflow pack through research, copy, image, review, and publisher stages. Use when the user wants to create, resume, validate, save to draft, or publish one content pack.
---

# OpenClaw XiaoHongShu Workflow

This skill is for two actors:

- the human user, who provides scheduler files, assets, and final intent
- OpenClaw, which executes the workflow against a pack directory

## Use This Skill When

- a scheduler file already exists
- a pack needs to be created or resumed
- the task is `save_draft` or `publish`
- the pack directory should remain the source of truth

## Core Rules

- Read the scheduler before doing anything else.
- Treat the pack directory as the source of truth for state and outputs.
- Respect `publish_policy.allow_publish`; do not publish when it is false.
- Prefer `save_draft` unless the user explicitly asks for publish and the scheduler allows it.
- If `--start-at` is later than `research`, reuse the existing pack files.
- On failure, write the result back into `workflow_state.json`, `publish_result.json`, and `agent_runs.json`.

## Preferred Execution Order

1. Validate the environment if the task is a first run or a new machine.
2. Create or resolve the pack directory.
3. Run only the requested stage range.
4. Persist outputs and transitions back into the pack.

## Minimal Tool Entry Points

- `scripts/check_env.py`
- `scripts/quickstart.py`
- `scripts/xhs_workflow.py`
- `scripts/xhs_pack_validate.py`

## Stage Model

`research -> copy -> image -> review -> publisher`

Publisher actions are:

- `check-login`
- `preflight-publish`
- `fill-publish`
- `click-publish`
- `save-draft`

## What To Read

Read only what is needed:

- scheduler contract: `references/scheduler_schema.md`
- pack contract: `references/pack_schema.md`
- publisher boundary: `references/publisher_contract.md`
- human setup guide: `references/openclaw_setup_guide.md`

Do not bulk-load every reference file unless the task actually needs it.
