# v0.1.0 Release Notes

## Summary

`openclaw-xhs-workflow` is now a usable first release for running a draft-first XiaoHongShu content workflow with OpenClaw.

This release focuses on one clear goal:

- turn one topic into a reviewable and resumable post pack

## What Is Included

- five-stage workflow:
  - `research`
  - `copy`
  - `image`
  - `review`
  - `publisher`
- draft-first publisher flow
- resumable pack state
- OpenClaw adapters for content generation and publishing
- image adapters for:
  - `source-file`
  - `openclaw-images`
  - `openai-images`
  - `gemini-images`
- local first-run helpers:
  - `scripts/check_env.py`
  - `scripts/quickstart.py`
- bilingual setup and reference docs

## Recommended First Run

```bash
cp .env.example .env.local
/usr/bin/python3 scripts/check_env.py --profile mock
/usr/bin/python3 scripts/quickstart.py --profile mock
```

## Recommended First Real Run

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

## Why This Release Exists

Most AI content flows look fine as a one-off prompt, but break down in real usage.

This release treats XiaoHongShu posting as a workflow instead of a single generation step. The output is a pack directory with content, image prompt, cover asset, review result, publish result, and run history.

## Current Boundaries

- the repository is a workflow layer, not a private content repository
- browser login state and credentials stay outside the repo
- the default safest path is still `save_draft`

## Suggested GitHub Release Title

`v0.1.0: draft-first XiaoHongShu workflow for OpenClaw`
