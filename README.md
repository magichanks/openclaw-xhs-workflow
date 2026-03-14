# OpenClaw XiaoHongShu Workflow

Build one XiaoHongShu post as a resumable pack:

`research -> copy -> image -> review -> publisher`


## What This Repo Owns

- one stable pack format
- one stable scheduler format
- one resumable workflow engine
- one draft-first publisher path
- minimal examples that are safe to copy

这个仓库负责：

- 一套稳定的 pack 格式
- 一套稳定的 scheduler 格式
- 一套可续跑的 workflow engine
- 一条默认先存草稿的 publisher 路径
- 一组可以直接复制的最小示例

It does not hold your account credentials, browser profile data, private briefs, or machine-private paths.

它不保存你的账号凭证、浏览器 profile、私有 brief 或机器私有路径。

## Start Here

If you are the human operator, do this first:

```bash
cp .env.example .env.local
/usr/bin/python3 scripts/check_env.py --profile mock
/usr/bin/python3 scripts/quickstart.py --profile mock
```

Expected result:

- one new pack under `./tmp-packs`
- final status `draft_saved`

如果你是人类操作者，先跑这三条命令：

```bash
cp .env.example .env.local
/usr/bin/python3 scripts/check_env.py --profile mock
/usr/bin/python3 scripts/quickstart.py --profile mock
```

预期结果：

- `./tmp-packs` 下生成一个新 pack
- 最终状态是 `draft_saved`

This is the lowest-friction path:

- no real image API
- no browser profile
- no publisher login

这是阻力最小的路径：

- 不需要真实图像接口
- 不需要浏览器 profile
- 不需要 publisher 登录

## If You Already Use OpenClaw

For the first real run, keep image generation simple and use one explicit cover file:

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

If `--source-file` is omitted, quickstart falls back to the bundled example cover so you can verify the full chain first.

如果你已经在用 OpenClaw，第一次真实接入时先用一张明确的封面图，保持路径最短：

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

如果省略 `--source-file`，quickstart 会先回退到仓库内置示例封面，先帮你验证全链路。

## What To Tell OpenClaw

Use this repo as the workflow layer, not the business-content layer.

Tell OpenClaw to:

1. read the scheduler first
2. treat the pack directory as the source of truth
3. prefer `save_draft` unless publish is explicitly allowed
4. resume from `--start-at` when a pack already exists

可以这样告诉 OpenClaw：

1. 先读 scheduler
2. 把 pack 目录当作唯一事实源
3. 默认优先 `save_draft`，除非 scheduler 明确允许 publish
4. 如果 pack 已存在，就从 `--start-at` 续跑

Example prompt:

```text
Use this repository to run the XiaoHongShu workflow.

Inputs:
- scheduler file: /abs/path/to/scheduler.json
- packs root: /abs/path/to/packs
- start_at: research
- mode: save_draft

Rules:
- Read the scheduler first.
- Treat the pack directory as the source of truth.
- Do not publish if allow_publish=false.
- On failure, write the result back into the pack files.
```

## The Three Entry Files

### 1. `.env.example`

Copy to `.env.local`. Fill only what you need for the current step.

Start with `mock`. Switch to `openclaw`, `openai-images`, or `gemini-images` only after the local path works.

先复制成 `.env.local`。只填写当前这一步真正需要的变量。

先从 `mock` 开始。只有本地链路跑通后，再切到 `openclaw`、`openai-images` 或 `gemini-images`。

### 2. `scripts/check_env.py`

Use it as the first gate. It tells you what is missing for a specific profile.

```bash
/usr/bin/python3 scripts/check_env.py --profile mock
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
```

把它当作第一道门。它会告诉你某个 profile 还缺什么。

### 3. `scripts/quickstart.py`

Use it as the shortest runnable path. It:

- loads `.env.local` automatically
- runs `check_env.py --strict`
- selects a scheduler template
- creates a temporary scheduler with safe defaults
- runs `scripts/xhs_workflow.py`

把它当作最短可运行入口。它会：

- 自动加载 `.env.local`
- 先执行 `check_env.py --strict`
- 选择对应的 scheduler 模板
- 生成一份带安全默认值的临时 scheduler
- 调用 `scripts/xhs_workflow.py`

## Supported Profiles

- `mock`
  - fastest first success path
  - fully local
- `openclaw`
  - uses OpenClaw for content and publisher stages
  - image input comes from `--source-file` or the example cover
- `openai-images`
  - same as `openclaw`, but image generation uses OpenAI
- `gemini-images`
  - same as `openclaw`, but image generation uses Gemini

支持的 profile：

- `mock`
  - 最快的首次成功路径
  - 完全本地
- `openclaw`
  - 内容和 publisher 阶段走 OpenClaw
  - 图片来自 `--source-file` 或示例封面
- `openai-images`
  - 与 `openclaw` 类似，但图片生成走 OpenAI
- `gemini-images`
  - 与 `openclaw` 类似，但图片生成走 Gemini

## Files OpenClaw Should Care About

- [SKILL.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/SKILL.md)
- [references/scheduler_schema.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/scheduler_schema.md)
- [references/pack_schema.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/pack_schema.md)
- [references/publisher_contract.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/publisher_contract.md)

## Files Humans Should Read Next

- [references/openclaw_setup_guide.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/openclaw_setup_guide.md)
- [references/image_adapter_setup.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/image_adapter_setup.md)

## Repository Layout

```text
openclaw-xhs-workflow/
├── SKILL.md
├── README.md
├── .env.example
├── assets/examples/
├── references/
└── scripts/
```

Key folders:

- `scripts/`: executable entrypoints and adapters
- `references/`: contracts and setup docs
- `assets/examples/`: safe example schedulers and pack data

关键目录：

- `scripts/`：脚本入口和 adapters
- `references/`：contract 与接入文档
- `assets/examples/`：可安全复制的 scheduler 和 pack 示例
