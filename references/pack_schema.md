# Pack Schema

The pack is the stable workflow contract. A valid pack must be human-readable, resumable by an agent, and consumable by a publisher stage.

## Required Files

- `brief.md`
- `title.txt`
- `content.txt`
- `hashtags.txt`
- `asset_plan.md`
- `research.md`
- `research.json`
- `image_prompts.md`
- `review_checklist.md`
- `workflow_state.json`
- `review_report.json`
- `publish_result.json`
- `agent_runs.json`
- `assets/`

## Core Rules

- Pack ids should follow `YYYY-MM-DD-topic-slug`.
- Use pack-relative paths for assets wherever possible.
- `agent_runs.json` is append-only.
- `draft_saved` belongs in `publisher_status` or `publish_result.status`, not the main workflow state.
- Do not store account credentials, profile paths, tokens, or machine-private data in the pack.
