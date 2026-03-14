# OpenClaw XiaoHongShu Workflow

An OpenClaw plugin/skill skeleton for building reviewable XiaoHongShu content packs and pushing them to draft or publish through a pluggable publisher adapter.

一个面向 OpenClaw 的小红书工作流插件/skill 骨架，用来生成可审阅的内容 pack，并通过可插拔的 publisher adapter 将内容保存为草稿或正式发布。

## What This Repo Is

This repository is the workflow layer, not a business-specific content repository.

It is meant to hold:

- a stable pack contract
- a stable scheduler contract
- a resumable workflow state machine
- validation and pack utility scripts
- a pluggable publisher adapter boundary
- minimal examples for dogfooding and reuse

这个仓库是 workflow 层，不是某个业务项目的内容仓库。

它承载的是：

- 稳定的 pack contract
- 稳定的 scheduler contract
- 可恢复的 workflow 状态机
- 校验与 pack 工具脚本
- 可插拔的 publisher adapter 边界
- 可用于 dogfood 和复用的最小示例

## What This Repo Is Not

This repository should not contain:

- account credentials
- browser profile data
- private product briefs
- business-specific source materials
- machine-private absolute paths

这个仓库不应该包含：

- 账号凭证
- 浏览器 profile 数据
- 私有产品 brief
- 业务专属素材源
- 某台机器私有的绝对路径

## Repository Layout

```text
openclaw-xhs-workflow/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── assets/examples/
├── references/
└── scripts/
```

Key directories:

- `scripts/`: workflow, state, validation, and adapter scripts
- `references/`: stable contracts and integration guidance
- `assets/examples/`: example scheduler files and an example pack
- `agents/openai.yaml`: UI metadata for the skill

关键目录：

- `scripts/`：workflow、状态、校验和 adapter 脚本
- `references/`：稳定 contract 和集成说明
- `assets/examples/`：示例 scheduler 与 example pack
- `agents/openai.yaml`：skill 的 UI metadata

## Core Concepts

### 1. Pack

A pack is the reviewable working directory for one XiaoHongShu post.

Pack details are documented in:

- `references/pack_schema.md`

`pack` 是一篇小红书内容的标准工作目录和审计记录。

详细定义见：

- `references/pack_schema.md`

### 2. Scheduler

A scheduler JSON is the policy input for one workflow run.

Scheduler details are documented in:

- `references/scheduler_schema.md`

`scheduler JSON` 是一次 workflow run 的策略输入。

详细定义见：

- `references/scheduler_schema.md`

### 3. State Machine

The main workflow state is intentionally narrow:

```text
created -> researched -> drafted -> imaged -> reviewed -> ready_to_fill -> filled -> published
```

Detailed rules live in:

- `references/state_machine.md`

主状态机刻意保持收敛：

```text
created -> researched -> drafted -> imaged -> reviewed -> ready_to_fill -> filled -> published
```

详细规则见：

- `references/state_machine.md`

### 4. Publisher Adapter

The workflow engine should not hardcode a local browser automation implementation.

Instead, publisher actions are treated as an adapter boundary:

- `check-login`
- `preflight-publish`
- `fill-publish`
- `click-publish`
- `save-draft`

Details live in:

- `references/publisher_contract.md`

workflow engine 不应该把本地浏览器自动化实现写死。

publisher 动作应该被视为 adapter 边界：

- `check-login`
- `preflight-publish`
- `fill-publish`
- `click-publish`
- `save-draft`

详细定义见：

- `references/publisher_contract.md`

## Current Status

This repository now includes a runnable draft-first publisher MVP.

Implemented:

- pack scaffolding
- pack state management
- pack validation
- asset manifest building
- runnable `save_draft` / `publish` workflow for an already prepared pack
- manual run payload builder
- codex-cli and mock publisher adapters

Not fully implemented yet:

- end-to-end research/copy/image/review execution
- richer OpenClaw-native content generation pipeline
- CI and release packaging

当前仓库已经包含一个可运行的 draft-first publisher MVP。

已具备：

- pack scaffold
- pack 状态管理
- pack 校验
- asset manifest 生成
- 面向已准备好 pack 的 `save_draft` / `publish` workflow
- 手动 run payload 构造
- codex-cli 与 mock publisher adapter

尚未完整实现：

- 真正端到端的 research/copy/image/review 执行
- 更完整的 OpenClaw 原生内容生成链路
- CI 与 release 打包

## Environment Assumptions

Minimum assumptions:

- Python 3.10+
- a Unix-like shell for `scripts/scaffold_pack.sh`
- OpenClaw available when you want to invoke the workflow through OpenClaw
- a publisher adapter implementation if you want to fill/save/publish for real

If you use the codex-cli publisher adapter, you also need:

- `uv`
- a local installation of the XiaoHongShu automation skill/CLI
- a valid browser/login environment

最小环境前提：

- Python 3.10+
- 可运行 `scripts/scaffold_pack.sh` 的类 Unix shell
- 如果要通过 OpenClaw 调度，则需要 OpenClaw 可用
- 如果要真实 fill/save/publish，则需要可用的 publisher adapter

如果使用 codex-cli publisher adapter，还需要：

- `uv`
- 本地安装好的小红书自动化 skill/CLI
- 可用的浏览器与登录环境

## Quick Start

### 1. Create a pack

```bash
bash scripts/scaffold_pack.sh ./packs developer-honest-share 2026-03-14
```

### 2. Inspect or advance state

```bash
python3 scripts/xhs_pack_state.py show --pack-dir ./packs/2026-03-14-developer-honest-share
python3 scripts/xhs_pack_state.py transition \
  --pack-dir ./packs/2026-03-14-developer-honest-share \
  --state reviewed \
  --last-step review \
  --content-status done \
  --image-status done \
  --review-status approved
```

### 3. Validate a pack

```bash
python3 scripts/xhs_pack_validate.py \
  --pack-dir ./packs/2026-03-14-developer-honest-share \
  --profile draft
```

### 4. Build a manual run payload

```bash
python3 scripts/run_manual.py \
  --scheduler-file assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --extra "Write from a developer perspective and keep the tone honest."
```

### 5. Run the workflow with the mock adapter

```bash
python3 scripts/xhs_workflow.py \
  --packs-root ./packs \
  --scheduler-file assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --mode save_draft
```

If you want a verified local example, use the bundled example pack:

```bash
python3 scripts/xhs_workflow.py \
  --packs-root ./assets/examples \
  --scheduler-file ./assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --pack-dir ./assets/examples/example-pack \
  --mode save_draft \
  --publisher-adapter mock
```

That command is expected to end with:

```json
{
  "status": "draft_saved"
}
```

如果你想先跑一个仓库内自带、已经验证过的例子，可以直接用内置的 example pack：

```bash
python3 scripts/xhs_workflow.py \
  --packs-root ./assets/examples \
  --scheduler-file ./assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --pack-dir ./assets/examples/example-pack \
  --mode save_draft \
  --publisher-adapter mock
```

这条命令的预期结果是：

```json
{
  "status": "draft_saved"
}
```

### 6. Run a real `save_draft` flow with the codex-cli adapter

Prerequisites:

- the pack is already review-approved
- `assets/manifest.json` exists and points to one real cover image
- the local XiaoHongShu automation CLI is installed
- the login/browser environment is valid

```bash
export XHS_PUBLISHER_ADAPTER=codex-cli
export XHS_SKILL_ROOT="$HOME/.codex/skills/xiaohongshu-skills"

python3 scripts/xhs_workflow.py \
  --packs-root ./packs \
  --scheduler-file assets/examples/scheduler-save-draft.json \
  --date 2026-03-14 \
  --pack-dir ./packs/2026-03-14-developer-honest-share \
  --mode save_draft \
  --publisher-adapter codex-cli
```

Success means:

- `preflight-publish` succeeded
- `fill-publish` succeeded
- `save-draft` succeeded
- `workflow_state.json` shows `publisher_status: draft_saved`
- `publish_result.json` shows `status: draft_saved`

成功的判定标准：

- `preflight-publish` 成功
- `fill-publish` 成功
- `save-draft` 成功
- `workflow_state.json` 中 `publisher_status` 为 `draft_saved`
- `publish_result.json` 中 `status` 为 `draft_saved`

## OpenClaw Usage

This repository is designed for people already using OpenClaw.

The recommended split is:

1. Use your OpenClaw agent or business repo to generate and review the pack.
2. Let this repository own the stable publisher-stage contract.
3. Invoke `scripts/xhs_workflow.py` from OpenClaw once the pack is approved.

这个仓库是按“用户本身已经在用 OpenClaw”来设计的。

建议的职责拆分是：

1. 用你自己的 OpenClaw agent 或业务仓库生成并审核 pack。
2. 让这个仓库负责稳定的 publisher-stage contract。
3. 在 pack 审核通过后，再从 OpenClaw 调用 `scripts/xhs_workflow.py`。

### Example OpenClaw prompt

```text
Use $openclaw-xhs-workflow to run the publisher stage only.

Inputs:
- scheduler file: /abs/path/to/scheduler.json
- packs root: /abs/path/to/packs
- pack dir: /abs/path/to/packs/2026-03-14-developer-honest-share
- mode: save_draft
- publisher adapter: codex-cli

Rules:
- Do not regenerate content.
- Validate the pack first.
- Refuse to publish if review_report.json is not approved.
- Run preflight-publish -> fill-publish -> save-draft.
- On failure, persist workflow_state.json, publish_result.json, and agent_runs.json.
```

### Workspace guidance for OpenClaw

- Make sure the pack root lives inside the OpenClaw workspace.
- Do not infer a pack root outside the workspace.
- Pass `--pack-dir` explicitly when resuming a specific pack.
- Keep scheduler files in the business repo, not in this plugin repo.

## Integration Model

The intended deployment model is:

1. Keep this repository generic.
2. Keep business-specific schedulers, briefs, and materials in another repository.
3. Let the business repository call this workflow plugin through scripts or OpenClaw.

建议的集成方式是：

1. 让本仓库保持通用。
2. 把业务侧 scheduler、brief、素材留在另一个仓库。
3. 由业务仓库通过脚本或 OpenClaw 调用这个 workflow plugin。

## Safety and Privacy

- Do not commit account cookies, tokens, or browser profile directories.
- Do not put machine-private absolute paths into scheduler or pack examples.
- Do not present the workflow as guaranteed content quality; review remains a first-class stage.

- 不要提交账号 cookie、token 或浏览器 profile 目录。
- 不要把某台机器私有的绝对路径写进 scheduler 或 pack 示例。
- 不要把这个 workflow 描述成“自动生成就一定优质内容”；review 仍然是一等阶段。

## First Release Scope

Recommended first public release:

- stable contracts
- workflow skeleton
- adapter boundary
- examples
- draft-first positioning

What can wait:

- multi-account routing
- hot-topic discovery
- business-specific copy templates
- advanced release tooling

建议首个公开版本只覆盖：

- 稳定 contract
- workflow skeleton
- adapter boundary
- examples
- draft-first 定位

这些可以后置：

- 多账号路由
- 热点发现
- 业务专属文案模板
- 更复杂的 release tooling
