# Publisher Contract

The workflow engine should treat publisher automation as an adapter boundary.

## Required Actions

- `check-login`
- `preflight-publish`
- `fill-publish`
- `click-publish`
- `save-draft`

## Rules

- The workflow engine must not hardcode a local skill installation path.
- Publisher failures must be persisted back to the pack.
- Draft-first behavior should be the default.
- A mock adapter should exist for local tests and CI.
