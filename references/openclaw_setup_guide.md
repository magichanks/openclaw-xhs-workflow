# OpenClaw Setup Guide / OpenClaw 接入指南

This guide is for users who already work inside OpenClaw and want to get this workflow running with the fewest moving parts.

这份指南面向已经在使用 OpenClaw 的用户，目标是用最少的变量把这套 workflow 跑起来。

## Why The Guide Defaults To `openclaw` Publisher

The guide now recommends `openclaw` as the default real publisher path for one practical reason:

- it lets users keep publisher execution inside their own OpenClaw AI and tooling environment

This is not an architectural restriction.

The architecture only requires a publisher adapter contract:

- `check-login`
- `preflight-publish`
- `fill-publish`
- `click-publish`
- `save-draft`

If another real publisher adapter is implemented later, the guide should be updated to include it.

现在这份指南默认推荐 `openclaw` 作为真实 publisher 路径，原因也很直接：

- 它可以把 publisher 执行留在用户自己的 OpenClaw AI 和工具环境里

这不是架构限制。

架构层真正要求的只是 publisher adapter contract：

- `check-login`
- `preflight-publish`
- `fill-publish`
- `click-publish`
- `save-draft`

以后如果补上别的真实 publisher adapter，这份指南也应该继续扩展。

## Recommended Rollout / 推荐接入顺序

Do not start with every real integration turned on.

Use this order:

1. `mock` everywhere
2. `source-file` for image
3. `openclaw` for research/copy/review
4. the real publisher adapter, `openclaw`
5. `openai-images` or `gemini-images` for image generation

That order isolates failures and makes debugging much faster.

不要一开始就把所有真实集成都打开。

推荐顺序是：

1. 全部先用 `mock`
2. 图片先切到 `source-file`
3. research/copy/review 再切到 `openclaw`
4. publisher 再切到真实 adapter，也就是 `openclaw`
5. 最后再接 `openai-images` 或 `gemini-images`

这个顺序能把故障面拆开，排错会快很多。

## Step 1: Copy The Environment Template / 先复制环境模板

```bash
cp .env.example .env.local
```

Then fill only the values you actually need.

然后只填写你当前这一步真正需要的变量。

Minimum useful fields for local testing:

```bash
XHS_PUBLISHER_ADAPTER=mock
XHS_OPENCLAW_AGENT=main
XHS_OPENCLAW_SESSION_ID=xhs-workflow
XHS_OPENCLAW_THINKING=medium
```

本地最小可用配置就是上面这几项。

## Step 2: Load The Environment / 加载环境变量

In a shell:

```bash
set -a
source ./.env.local
set +a
```

If you prefer direnv or another secrets loader, that is fine too. The workflow only requires these values to be present in the environment.

如果你更习惯 direnv 或其他 secrets loader 也可以，关键只是这些变量最终要出现在环境里。

## Step 3: Verify The Local Full Flow First / 先验证本地全流程

This does not require a real image API, browser profile, or publisher login.

这一步不需要真实图像接口、不需要浏览器 profile，也不需要 publisher 登录态。

```bash
/usr/bin/python3 scripts/xhs_workflow.py \
  --packs-root ./tmp-packs \
  --scheduler-file ./assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --start-at research \
  --mode save_draft \
  --publisher-adapter mock
```

Expected result:

- `status` is `draft_saved`
- a new pack is created under `./tmp-packs`

预期结果：

- `status` 为 `draft_saved`
- `./tmp-packs` 下会生成一个新 pack

## Step 4: Switch Image To `source-file` / 图片先切到 `source-file`

This is the safest first real-world step.

这是最稳的第一步真实接入。

1. Put a real cover image somewhere in your business repo.
2. Copy `assets/examples/scheduler-openclaw-save-draft.json`.
3. Set:

1. 在你的业务仓库里放一张真实封面图。
2. 复制 `assets/examples/scheduler-openclaw-save-draft.json`。
3. 改成：

```json
{
  "image_policy": {
    "adapter": "source-file",
    "source_file": "./source-assets/cover.png"
  }
}
```

Now the workflow remains deterministic, but the output image is real.

这样 workflow 仍然是确定性的，但图片已经变成真实输出。

## Step 5: Turn On OpenClaw For Content Stages / 打开 OpenClaw 内容阶段

Use `openclaw` adapters only after the local mock path works.

只有在本地 mock 路径跑通之后，再打开 `openclaw` adapter。

Recommended scheduler settings:

```json
{
  "research_policy": {
    "adapter": "openclaw",
    "limit": 5
  },
  "copy_policy": {
    "adapter": "openclaw",
    "language": "zh-CN"
  },
  "review_policy": {
    "adapter": "openclaw"
  },
  "openclaw": {
    "agent": "main",
    "session_id": "xhs-workflow",
    "thinking": "medium"
  }
}
```

If you want deterministic review gating with a generated summary, keep:

- `review_policy.adapter = openclaw`

The workflow still uses deterministic validation to decide whether the pack is blocked.

如果你想要“OpenClaw 生成 review summary，但最终放行仍由确定性校验决定”，那就保留：

- `review_policy.adapter = openclaw`

因为 workflow 仍然会用 deterministic validation 决定 pack 是否被拦住。

## Step 6: Turn On The Real Publisher / 打开真实 publisher

Only do this after you have verified:

- OpenClaw can generate the pack
- the pack reaches `reviewed`
- `assets/manifest.json` points to one real cover image

只有在下面三件事都确认无误之后，再打开真实 publisher：

- OpenClaw 能稳定生成 pack
- pack 能走到 `reviewed`
- `assets/manifest.json` 已经指向真实封面图

Then set:

```bash
XHS_PUBLISHER_ADAPTER=openclaw
XHS_PUBLISHER_OPENCLAW_AGENT=main
XHS_PUBLISHER_OPENCLAW_SESSION_ID=xhs-workflow-publisher
```

Recommended first command:

```bash
/usr/bin/python3 scripts/xhs_workflow.py \
  --packs-root ./packs \
  --scheduler-file ./assets/examples/scheduler-openclaw-save-draft.json \
  --date 2026-03-14 \
  --start-at publisher \
  --pack-dir ./packs/2026-03-14-developer-honest-share \
  --mode save_draft \
  --publisher-adapter openclaw
```

That keeps the risk low because you are only testing publisher-stage integration.

这样风险最低，因为你只是在测试 publisher 阶段接入。

## Step 7: Turn On A Real Image API / 打开真实图像接口

### OpenAI

Set:

```bash
OPENAI_API_KEY=...
XHS_IMAGE_MODEL=gpt-image-1.5
```

Scheduler change:

```json
{
  "image_policy": {
    "adapter": "openai-images",
    "model": "gpt-image-1.5",
    "size": "1024x1024"
  }
}
```

OpenAI 路径只需要补 API key 和 image policy。

### Gemini

Set:

```bash
GEMINI_API_KEY=...
XHS_GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

Scheduler change:

```json
{
  "image_policy": {
    "adapter": "gemini-images",
    "model": "gemini-2.5-flash-image",
    "aspect_ratio": "3:4"
  }
}
```

Gemini 路径同样只需要补 API key 和 image policy。

## Common Failure Modes / 常见失败点

### 1. OpenClaw stage fails immediately

Check:

- `OPENCLAW_BIN`
- the `openclaw` binary is on `PATH`
- the configured OpenClaw `agent` exists

### 1. OpenClaw 阶段一开始就失败

检查：

- `OPENCLAW_BIN`
- `openclaw` 是否在 `PATH` 上
- 配置的 OpenClaw `agent` 是否存在

### 2. Publisher stage says not logged in

Check:

- `XHS_PUBLISHER_ADAPTER=openclaw`
- `XHS_PUBLISHER_OPENCLAW_AGENT`
- your XiaoHongShu browser/login environment

### 2. Publisher 阶段提示未登录

检查：

- `XHS_PUBLISHER_ADAPTER=openclaw`
- `XHS_PUBLISHER_OPENCLAW_AGENT`
- 小红书浏览器/登录环境是否可用

### 3. Image stage fails before generation

Check:

- the adapter name in `image_policy.adapter`
- required env vars exist
- `image_prompts.md` contains a usable `- Prompt:` line, or the fallback prompt is acceptable

### 3. Image 阶段在生成前就失败

检查：

- `image_policy.adapter` 是否写对
- 必需环境变量是否存在
- `image_prompts.md` 里是否有可用的 `- Prompt:` 行，或者 fallback prompt 是否可接受

### 4. Pack is blocked before publisher

Check:

- `review_report.json`
- `assets/manifest.json`
- `workflow_state.json`
- title/body/hashtags do not still contain placeholders

### 4. Pack 在 publisher 前被拦住

检查：

- `review_report.json`
- `assets/manifest.json`
- `workflow_state.json`
- title/body/hashtags 是否还残留 placeholder

## Suggested First Real Workflow / 推荐的第一套真实工作流

For most users, this is the safest first production-shaped combination:

- `research_policy.adapter = openclaw`
- `copy_policy.adapter = openclaw`
- `image_policy.adapter = source-file`
- `review_policy.adapter = validator`
- `publisher-adapter = openclaw`

That keeps the fragile parts separated:

- OpenClaw handles text generation
- a human or business repo controls the cover image
- deterministic validation decides whether the workflow can continue
- the publisher only runs after the pack is ready

对大多数用户来说，最稳的第一套生产形态组合仍然是：

- `research_policy.adapter = openclaw`
- `copy_policy.adapter = openclaw`
- `image_policy.adapter = source-file`
- `review_policy.adapter = validator`
- `publisher-adapter = openclaw`

这样能把脆弱点拆开：

- OpenClaw 负责文本生成
- 人或业务仓库控制封面图
- 确定性校验决定 workflow 能不能继续
- publisher 只在 pack 真正准备好后才运行
