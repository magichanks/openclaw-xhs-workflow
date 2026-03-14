# Scheduler Schema

Scheduler JSON is the policy input for a workflow run.

## Minimal Fields

- `version`
- `timezone`
- `mode`
- `pack_naming.topic_slug`
- `publish_policy`
- `image_policy`
- `topic`
- `audience`
- `core_value`
- `cta`

## Core Rules

- One scheduler schema should serve both cron and manual triggers.
- Scheduler files define policy, not run state.
- Scheduler files must not contain credentials, browser profile paths, or machine-private directories.
- `allow_publish=false` must prevent final publish even if the rest of the workflow succeeds.
