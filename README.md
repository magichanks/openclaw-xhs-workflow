# OpenClaw XiaoHongShu Workflow

Give this workflow one topic, and it will turn that topic into a reviewable XiaoHongShu post draft:

`research -> copy -> image -> review -> publisher`

More concretely, this repository does this:

1. take one topic
2. run it through research, copywriting, cover generation, review, and publisher preparation
3. leave behind a complete pack directory that can be inspected, resumed, saved to draft, or published later

更具体地说，这个仓库做的是这件事：

1. 接收一个选题
2. 让它依次经过 research、文案、封面、审核、发布准备
3. 最终产出一个完整的 pack 目录，供你检查、续跑、存草稿或稍后正式发布

What you provide at the human level:

- one topic
- optionally one real cover image
- optionally your own OpenClaw environment for real runs

What the workflow gives back:

- `brief.md`
- `title.txt`
- `content.txt`
- `hashtags.txt`
- `research.md` and `research.json`
- `assets/cover.png` and `assets/manifest.json`
- `review_report.json`
- `publish_result.json`
- `agent_runs.json`
- `workflow_state.json`

从人的视角，你实际提供的是：

- 一个选题
- 可选，一张真实封面图
- 可选，你自己的 OpenClaw 运行环境

workflow 最终返回的是：

- `brief.md`
- `title.txt`
- `content.txt`
- `hashtags.txt`
- `research.md` 和 `research.json`
- `assets/cover.png` 和 `assets/manifest.json`
- `review_report.json`
- `publish_result.json`
- `agent_runs.json`
- `workflow_state.json`

If it succeeds in `save_draft` mode, the result is not just “some text was generated”. The result is a complete, inspectable working folder for one XiaoHongShu post.

如果它以 `save_draft` 模式成功结束，结果不只是“生成了一段文案”，而是得到了一整个可检查、可续跑的小红书内容工作目录。

## What Happens To One Topic

When you give the workflow one topic, it goes through these stages:

1. `research`
   It expands the topic into angles, pain points, and claim boundaries.
2. `copy`
   It writes the title, body, hashtags, asset plan, and image prompt.
3. `image`
   It prepares one cover image, either from a source file or an image model.
4. `review`
   It checks whether the pack is publishable and records the decision.
5. `publisher`
   It fills the publish form and usually stops at `save_draft` unless publish is explicitly allowed.

给一个选题之后，它会依次经过这些阶段：

1. `research`
   把选题扩展成角度、痛点和可说不可说的边界。
2. `copy`
   生成标题、正文、标签、素材计划和配图提示。
3. `image`
   准备一张封面图，来源可以是真实文件，也可以是图像模型。
4. `review`
   检查这条内容是否具备可发布条件，并记录审核结论。
5. `publisher`
   填写发布表单，默认通常停在 `save_draft`，除非明确允许正式发布。

So the real outcome is:

- not just a title
- not just a prompt
- not just one final publish action

It is a complete post package with state, files, and history.

所以它真正交付的不是：

- 只有一个标题
- 只有一段 prompt
- 只有一次最终发布动作

而是一整套带状态、带文件、带历史记录的内容包。


## What This Project Is

This project is a workflow plugin for teams or individuals who want XiaoHongShu content generation and publishing to behave like an actual production workflow instead of a one-off prompt.

It turns one post into a durable working directory with:

- explicit stage boundaries
- resumable state
- reviewable intermediate files
- a draft-first publisher path
- clear handoff between human operators and OpenClaw

这个项目本身是一个 workflow plugin，面向那些希望把“小红书内容生成和发布”做成真实生产流程，而不是一次性 prompt 的团队或个人。

它把“一篇内容”变成一个可持续操作的工作目录，具备：

- 明确的阶段边界
- 可续跑的状态
- 可审阅的中间文件
- 默认先存草稿的 publisher 路径
- 人和 OpenClaw 之间清晰的交接方式

In practice, it is meant for cases like:

- you want OpenClaw to generate content, but you still want files you can inspect
- you want failures to be resumable instead of starting over
- you want draft-first publishing instead of blind final publish
- you want the same contract to work across local testing and real runs

实际适用的场景包括：

- 你希望 OpenClaw 负责生成内容，但仍然保留可检查的文件
- 你希望失败后可以续跑，而不是每次重来
- 你希望默认先存草稿，而不是直接盲发
- 你希望同一套 contract 同时适用于本地验证和真实运行

It is not trying to be:

- a private content repository
- a browser profile manager
- a credential vault
- a giant prompt collection

它不是：

- 私有内容仓库
- 浏览器 profile 管理器
- 凭证保险箱
- 大而全的 prompt 集合

## A Simple Mental Model

Think of this project as:

- a machine that turns `topic -> pack/`
- plus a state machine that lets you resume after failure
- plus a publisher boundary that can stop at draft instead of forcing final publish

把这个项目理解成下面这样会更直观：

- 一个把 `topic -> pack/` 的工作机
- 外加一个失败后可续跑的状态机
- 外加一个可以停在草稿而不是强制发布的 publisher 边界

Example result directory:

```text
2026-03-14-developer-honest-share/
├── brief.md
├── title.txt
├── content.txt
├── hashtags.txt
├── research.md
├── research.json
├── image_prompts.md
├── review_report.json
├── publish_result.json
├── workflow_state.json
├── agent_runs.json
└── assets/
    ├── cover.png
    └── manifest.json
```

That directory is the product of the workflow.

这个目录本身，就是 workflow 的产物。

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
- `openclaw-images`
  - uses OpenClaw for content, image, and publisher stages
  - the image stage consumes the prompt written during `copy`
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
- `openclaw-images`
  - 内容、图片和 publisher 阶段都走 OpenClaw
  - 图片阶段会直接消费 `copy` 阶段写出的提示词
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
