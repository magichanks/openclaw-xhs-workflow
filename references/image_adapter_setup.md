# Image Adapter Setup

This workflow supports multiple image-generation paths for the `image` stage.

## Supported Adapters

- `mock`
- `source-file`
- `openclaw-images`
- `openai-images`
- `gemini-images`

## 1. `mock`

Use this for local workflow verification.

Scheduler example:

```json
{
  "image_policy": {
    "adapter": "mock",
    "required_output": "assets/cover.png",
    "required_role": "cover",
    "count": 1
  }
}
```

No credentials are required.

## 2. `source-file`

Use this when your business repo or a human operator already prepared the cover image.

Scheduler example:

```json
{
  "image_policy": {
    "adapter": "source-file",
    "required_output": "assets/cover.png",
    "required_role": "cover",
    "count": 1,
    "source_file": "./source-assets/cover.png"
  }
}
```

`source_file` may be:

- an absolute path
- a path relative to `--packs-root`

## 3. `openclaw-images`

Use this when OpenClaw itself already has image generation configured and you want the workflow to reuse that capability.

### Required environment

- `OPENCLAW_BIN` or `openclaw` on `PATH`
- `XHS_OPENCLAW_AGENT` or `openclaw.agent` in the scheduler

Optional:

```bash
export XHS_OPENCLAW_IMAGE_AGENT="image-agent-name"
```

Scheduler example:

```json
{
  "image_policy": {
    "adapter": "openclaw-images",
    "required_output": "assets/cover.png",
    "required_role": "cover",
    "count": 1
  }
}
```

Optional scheduler override:

```json
{
  "image_policy": {
    "adapter": "openclaw-images",
    "image_agent": "image-agent-name"
  }
}
```

Prompt source:

- `copy` writes `image_prompts.md`
- `image` reads the `- Prompt:` line from that file
- OpenClaw is asked to generate exactly one cover image at `assets/cover.png`

Use this when:

- the user already manages image API credentials inside OpenClaw
- you want one less API setup surface in this repo

## 4. `openai-images`

Use this for the OpenAI Images API or an OpenAI-compatible image gateway.

### Required environment

Default:

```bash
export OPENAI_API_KEY="..."
```

Optional:

```bash
export XHS_IMAGE_BASE_URL="https://api.openai.com/v1"
export XHS_IMAGE_MODEL="gpt-image-1.5"
export XHS_IMAGE_SIZE="1024x1024"
export XHS_IMAGE_QUALITY="high"
export XHS_IMAGE_BACKGROUND="auto"
```

### Scheduler example

```json
{
  "image_policy": {
    "adapter": "openai-images",
    "required_output": "assets/cover.png",
    "required_role": "cover",
    "count": 1,
    "model": "gpt-image-1.5",
    "size": "1024x1024"
  }
}
```

If you do not want to use `OPENAI_API_KEY`, you may point to another env var:

```json
{
  "image_policy": {
    "adapter": "openai-images",
    "api_key_env": "MY_IMAGE_API_KEY"
  }
}
```

This adapter is a good default for:

- OpenAI Images API
- most OpenAI-compatible image gateways

## 5. `gemini-images`

Use this when your team already runs image generation through Gemini.

### Required environment

```bash
export GEMINI_API_KEY="..."
```

### Scheduler example

```json
{
  "image_policy": {
    "adapter": "gemini-images",
    "required_output": "assets/cover.png",
    "required_role": "cover",
    "count": 1,
    "model": "gemini-2.5-flash-image",
    "aspect_ratio": "3:4"
  }
}
```

Optional fields:

- `base_url`
- `image_size`
- `aspect_ratio`
- `api_key_env`

## Prompt Source

The image prompt is taken from `image_prompts.md`.

Current rule:

- if `image_prompts.md` contains a line starting with `- Prompt:`, that value is used
- otherwise the workflow synthesizes a fallback prompt from `topic`, `core_value`, and `audience`

## Recommended Rollout Path

For most users, the lowest-risk progression is:

1. Start with `mock`
2. Move to `source-file`
3. Move to `openclaw-images` if OpenClaw already owns image generation
4. Move to `openai-images` or `gemini-images` if this repo should call the image API directly

This keeps the workflow stable while you set up model credentials and prompt tuning.
