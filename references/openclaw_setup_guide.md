# OpenClaw Setup Guide / OpenClaw 接入指南

This guide is for both:

- the human operator who wants the fewest setup steps
- the OpenClaw instance that needs a predictable rollout order

这份指南同时写给：

- 想用最少配置把流程跑通的人
- 需要明确 rollout 顺序的 OpenClaw

## One-Screen Recommendation

Use this rollout order and do not skip ahead:

1. `mock`
2. `openclaw` with `source-file`
3. `openai-images` or `gemini-images`

推荐 rollout 顺序，不要跳步：

1. `mock`
2. 带 `source-file` 的 `openclaw`
3. `openai-images` 或 `gemini-images`

Why:

- `mock` proves the workflow engine
- `source-file` proves your real pack can carry one real cover image
- real image APIs are the last variable, not the first

原因：

- `mock` 先验证 workflow engine
- `source-file` 再验证你的真实 pack 能带着一张真实封面图走完
- 真实图像接口应该是最后一个变量，不应该是第一个变量

## Shortest Path

```bash
cp .env.example .env.local
/usr/bin/python3 scripts/check_env.py --profile mock
/usr/bin/python3 scripts/quickstart.py --profile mock
```

Success means:

- a pack is created
- `workflow_state.json` advances
- final status is `draft_saved`

成功的定义是：

- pack 被创建
- `workflow_state.json` 正常推进
- 最终状态是 `draft_saved`

## First Real Path

When you are ready for the first real run, keep everything except the cover image as simple as possible:

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

Do this only after the mock path works.

第一次真实接入时，除了封面图之外，其余部分尽量保持简单：

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

前提是 `mock` 路径已经跑通。

## What The Profiles Mean

### `mock`

Use when:

- you want the first successful run
- you are validating local installation
- you do not want external dependencies yet

适用场景：

- 想先拿到第一次成功运行
- 验证本地安装是否正常
- 暂时不引入外部依赖

### `openclaw`

Use when:

- your OpenClaw should write research/copy/review
- your OpenClaw should execute publisher actions
- you can provide one explicit cover image

适用场景：

- 让 OpenClaw 生成 research/copy/review
- 让 OpenClaw 执行 publisher 动作
- 你能提供一张明确的封面图

### `openai-images` / `gemini-images`

Use only after `openclaw + source-file` works.

只在 `openclaw + source-file` 跑通之后再打开。

## What OpenClaw Should Do

When you invoke this repo from OpenClaw, keep the instructions narrow:

1. read the scheduler first
2. treat the pack directory as the source of truth
3. run only from the requested `--start-at` stage
4. default to `save_draft`
5. write failures back into the pack files

从 OpenClaw 调用这个仓库时，指令应该尽量收敛：

1. 先读 scheduler
2. 把 pack 目录当作唯一事实源
3. 只从指定的 `--start-at` 阶段开始执行
4. 默认走 `save_draft`
5. 失败时把结果写回 pack 文件

## Environment Notes

### Minimum local setup

`.env.local` is optional but recommended.

If present, `scripts/check_env.py`, `scripts/quickstart.py`, and `scripts/xhs_workflow.py` load it automatically.

`.env.local` 不是强制的，但推荐保留。

如果存在，`scripts/check_env.py`、`scripts/quickstart.py` 和 `scripts/xhs_workflow.py` 都会自动加载它。

### Minimum useful values

```bash
XHS_PUBLISHER_ADAPTER=mock
XHS_OPENCLAW_AGENT=main
XHS_OPENCLAW_SESSION_ID=xhs-workflow
XHS_OPENCLAW_THINKING=medium
```

### For the real OpenClaw publisher path

```bash
XHS_PUBLISHER_ADAPTER=openclaw
XHS_PUBLISHER_OPENCLAW_AGENT=main
XHS_PUBLISHER_OPENCLAW_SESSION_ID=xhs-workflow-publisher
```

### For real image generation

OpenAI:

```bash
OPENAI_API_KEY=...
XHS_IMAGE_MODEL=gpt-image-1.5
```

Gemini:

```bash
GEMINI_API_KEY=...
XHS_GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

More image-specific setup lives in [image_adapter_setup.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/image_adapter_setup.md).

## Common Failure Checks

### `mock` fails

Check:

- `/usr/bin/python3` exists
- the repo is writable
- the scripts can create `./tmp-packs`

### `openclaw` fails early

Check:

- `OPENCLAW_BIN` or `openclaw` on `PATH`
- the configured OpenClaw agent exists
- the source cover file exists

### publisher fails

Check:

- `XHS_PUBLISHER_ADAPTER=openclaw`
- the publisher OpenClaw agent exists
- the XiaoHongShu login/browser environment is valid

### image generation fails

Check:

- the selected adapter name is correct
- the required API key exists
- `image_prompts.md` contains a usable prompt, or the fallback prompt is acceptable
