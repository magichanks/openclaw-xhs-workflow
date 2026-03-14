# OpenClaw XiaoHongShu Workflow

Turn one topic into a reviewable, resumable XiaoHongShu post pack.

`research -> copy -> image -> review -> publisher`

把一个选题变成一套可检查、可续跑、可存草稿的小红书内容包。

## Quick Start

```bash
cp .env.example .env.local
/usr/bin/python3 scripts/check_env.py --profile mock
/usr/bin/python3 scripts/quickstart.py --profile mock
```

Expected result:

- a new pack under `./tmp-packs`
- final status `draft_saved`

这是最快的首次跑通路径。

预期结果：

- `./tmp-packs` 下出现一个新 pack
- 最终状态是 `draft_saved`

This path needs:

- no real image API
- no browser profile
- no publisher login

这条路径不需要：

- 真实图像 API
- 浏览器 profile
- publisher 登录

## What This Project Does

This repo is a workflow layer for one XiaoHongShu post.

Give it one topic, and it will:

1. research the topic
2. write the post
3. prepare one cover image
4. review the pack
5. save it to draft or publish it later

这个仓库是“一篇小红书内容”的 workflow 层。

给它一个选题后，它会：

1. 做 research
2. 写文案
3. 准备一张封面图
4. 做审核
5. 存草稿，或者稍后正式发布

## What You Get Back

The result is not just generated text. The result is a working folder for one post, for example:

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

So the real output is:

- draft content
- one cover image
- review decision
- publish result
- run history
- resumable workflow state

所以它真正交付的是：

- 草稿内容
- 一张封面图
- 审核结论
- 发布结果
- 运行历史
- 可续跑的工作流状态

## How One Topic Flows Through The System

1. `research`
   expand the topic into angles, pain points, and claim boundaries
2. `copy`
   write title, body, hashtags, asset plan, and image prompt
3. `image`
   create one cover image from a source file, OpenClaw image capability, or an image API
4. `review`
   decide whether the pack is ready for publisher stage
5. `publisher`
   fill the publish flow and usually stop at `save_draft`

一个选题会按这个顺序流过系统：

1. `research`
   扩展成角度、痛点和表达边界
2. `copy`
   生成标题、正文、标签、素材计划和图片提示词
3. `image`
   用真实图片、OpenClaw 图像能力或图像 API 生成封面图
4. `review`
   判断 pack 是否具备进入 publisher 阶段的条件
5. `publisher`
   填写发布流程，默认通常停在 `save_draft`

## Who This Repo Is For

This repo is written for two readers at the same time:

- the human operator who wants the shortest path to a successful run
- the user's OpenClaw, which needs a stable contract and a clear execution boundary

这个仓库同时写给两个读者：

- 想尽快跑通流程的人
- 需要稳定 contract 和明确执行边界的 OpenClaw

It is useful when:

- you want OpenClaw to generate content, but still leave inspectable files
- you want failures to be resumable instead of restarting from zero
- you want draft-first publishing instead of direct blind publish

它适合这些场景：

- 你希望 OpenClaw 负责生成内容，但仍然保留可检查文件
- 你希望失败后可以续跑，而不是每次重来
- 你希望默认先存草稿，而不是直接盲发

It is not:

- a private content repository
- a browser profile manager
- a credential vault

它不是：

- 私有内容仓库
- 浏览器 profile 管理器
- 凭证保险箱

## If You Already Use OpenClaw

### Minimal real path

If your first real run should stay simple, provide one explicit cover image:

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

如果你已经在用 OpenClaw，想让第一次真实运行保持简单，就提供一张明确的封面图：

```bash
/usr/bin/python3 scripts/check_env.py --profile openclaw --source-file /abs/path/to/cover.png
/usr/bin/python3 scripts/quickstart.py --profile openclaw --source-file /abs/path/to/cover.png
```

### If OpenClaw already owns image generation

Use the `openclaw-images` path. The image stage will consume the prompt written during `copy` and ask OpenClaw to generate the cover image.

如果 OpenClaw 本身已经接好了图像生成，就用 `openclaw-images` 路径。图片阶段会直接消费 `copy` 写出的提示词，并让 OpenClaw 生成封面。

## Supported Profiles

- `mock`
  - fastest first success path
  - fully local
- `openclaw`
  - content and publisher go through OpenClaw
  - image comes from `--source-file`
- `openclaw-images`
  - content, image, and publisher all go through OpenClaw
- `openai-images`
  - image generation goes through OpenAI
- `gemini-images`
  - image generation goes through Gemini

支持的 profile：

- `mock`
  - 最快的首次成功路径
  - 完全本地
- `openclaw`
  - 内容和 publisher 走 OpenClaw
  - 图片来自 `--source-file`
- `openclaw-images`
  - 内容、图片和 publisher 都走 OpenClaw
- `openai-images`
  - 图片生成走 OpenAI
- `gemini-images`
  - 图片生成走 Gemini

## What To Tell OpenClaw

If OpenClaw is invoking this repo, keep the instruction narrow:

1. read the scheduler or run configuration first
2. treat the pack directory as the source of truth
3. respect `allow_publish=false`
4. prefer `save_draft`
5. write failures back into the pack files

如果由 OpenClaw 调用这个仓库，指令保持收敛：

1. 先读 scheduler 或运行配置
2. 把 pack 目录当作唯一事实源
3. 遵守 `allow_publish=false`
4. 默认优先 `save_draft`
5. 失败时把结果写回 pack 文件

## Main Entry Points

- [.env.example](/Users/maic/virtualcloset/openclaw-xhs-workflow/.env.example)
- [scripts/check_env.py](/Users/maic/virtualcloset/openclaw-xhs-workflow/scripts/check_env.py)
- [scripts/quickstart.py](/Users/maic/virtualcloset/openclaw-xhs-workflow/scripts/quickstart.py)
- [scripts/xhs_workflow.py](/Users/maic/virtualcloset/openclaw-xhs-workflow/scripts/xhs_workflow.py)

## Read Next

- [SKILL.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/SKILL.md)
- [references/openclaw_setup_guide.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/openclaw_setup_guide.md)
- [references/image_adapter_setup.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/image_adapter_setup.md)
- [references/pack_schema.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/pack_schema.md)
- [references/publisher_contract.md](/Users/maic/virtualcloset/openclaw-xhs-workflow/references/publisher_contract.md)
