# 官方 Action 版：在 car_fmu_demo 试运行

当前流程做三件事：自动创建或复用草稿 PR、AI review、中文总结。

```text
推送 work/<任务> 分支
  → Review automation 创建或找到草稿 PR
  → 直接调度默认分支的 AI 审查任务
  → anthropics/claude-code-action 读取代码、调用 DeepSeek、使用 GitHub 工具
  → 在 PR 发布或更新中文审查总结
  → 人决定修复和合并
```

## 这次主要配置什么

| 文件 | 职责 |
| --- | --- |
| `.github/workflows/review-automation.yml` | 推送后创建 PR、调度 AI 审查，配置官方 Action 的模型和权限 |
| `.github/prompts/review.md` | 集中说明项目规则、审查步骤和中文总结的指令 |
| `examples/review-automation/known-unit-error.patch` | 可重复的已知单位错误样例 |

模型请求、agent 工具循环和源码阅读交给官方 Claude Code Action。审查结果全部保留在 PR 中；独立后续任务由负责人另行安排。

本流程只审查源码，不运行项目测试、构建或 FMU 仿真。总结必须明确说明这一点；AI 没发现问题不代表测试通过。

从最新 `main` 创建的任务分支，自动生成的 PR 正文只包含“任务目标”和“改动范围”，由提交者补充；AI 不把缺少验收标准单独列为问题。已有 PR 继续使用其原有正文，审查总结在评论中更新。

## 第一步：上传安装配置

迁移到其他仓库时，复制 `.github/workflows/review-automation.yml` 和 `.github/prompts/review.md`，按目标项目修改提示词第 4 条的单位、接口等规则，然后通过 PR 合入目标仓库的默认分支。首次安装需要手动创建 PR；工作流合入后才能为任务分支自动创建 PR。

本文和演示补丁仅用于说明与测试，不是工作流运行的必需文件。仓库名称和默认分支由 GitHub 自动读取，无需写死 `car_fmu_demo` 或 `main`。

## 第二步：网页配置

1. **Settings → Secrets and variables → Actions → Secrets → New repository secret**：名称填 `DEEPSEEK_API_KEY`，值填写你自己的 DeepSeek API 密钥。
2. **Settings → Actions → General → Workflow permissions**：允许 GitHub Actions 创建 Pull Request；若界面显示 “Allow GitHub Actions to create and approve pull requests”，勾选并保存。AI 负责审查和发布评论，合并由人决定。

模型默认 `deepseek-flash`；需要更改时添加 Variable `AI_REVIEW_MODEL`。密钥按仓库隔离，Daidalis 仓库中的 Secret 不会自动用于这里。

工作流将 `DEEPSEEK_API_KEY` 传给官方 Action 的 `anthropic_api_key` 输入，并将 `ANTHROPIC_BASE_URL` 配为 `https://api.deepseek.com/anthropic`。这里采用 DeepSeek 的 Anthropic 兼容接口，不是之前自写客户端使用的 Chat Completions 接口。

工作流显式提供 GitHub 自带的 `GITHUB_TOKEN`，不要求额外安装 Claude GitHub App，也不把个人 GitHub PAT 写进源码。上传仓库仍需要你的 GitHub 登录；DeepSeek 密钥不能用于 GitHub 登录。

## 第三步：制造一个可验证的错误

安装 PR 合并后，在本地执行。每次测试请换一个未使用过的分支名：

```bash
git switch main
git pull --ff-only
git switch -c work/demo-review
git apply examples/review-automation/known-unit-error.patch
git diff
git add src/export_sysml_to_json.py
git commit -m "Demo a known speed-unit defect"
git push -u origin work/demo-review
```

补丁只修改 exporter 中的速度表达式：把 `vTarget_mps` 错误乘以 `3.6`，使 `27.78 m/s` 导出为 `100.008`，但字段仍表示 m/s。

本地只需 Git 即可构造样例。云端由官方 Action 安装 Claude Code 运行时，无需为这套审查流程安装 Python、FMPy 或 OpenModelica。

## 第四步：看 GitHub 结果

打开仓库 Actions，查看 **Review automation**。一次推送会产生两次运行：`push` 运行创建 PR 并发起调度，随后 `workflow_dispatch` 运行执行 AI 审查。第一次运行的 AI job 显示跳过是正常的。

期望看到：

1. 自动创建一个 Draft PR。
2. 官方 Action 阅读差异和相关文件，在 PR 中用中文指出单位错误、源码位置和影响。
3. 总结注明“源码审查，未运行项目测试、构建或仿真”。

模型调用失败、权限不足或只输出最终对话而没实际发表评论，均不能当作线上验收成功。工作流会检查本轮是否存在带专用标记、完整提交 SHA 和新更新时间的机器人总结；没有找到则报错。成功时，Actions 运行摘要中提供总结链接。

总结使用隐藏标记 `<!-- ai-pr-review -->` 定位。同一 PR 后续审查更新这条总结，保留其他评论。第一次使用此版本时，旧版没有标记的总结会保留，机器人会新建一条带标记的总结。

补充 PR 的“任务目标”和“改动范围”后，可在 Actions 的 **Review automation → Run workflow** 手动重跑：执行分支选 `main`，输入 `branch` 填 `work/demo-review`。这次直接审查该分支当前提交，不等待其他工作流。

## 第五步：修复并再次上传

```bash
git apply --reverse examples/review-automation/known-unit-error.patch
git add src/export_sysml_to_json.py
git commit -m "Fix the intentional speed-unit conversion"
git push
```

Review automation 应对最新提交重新审查，确认单位错误已修复并更新总结。

同一分支后续推送会复用仍打开的 PR，包括已经从草稿转为待审核的 PR，不会把它重新改为草稿。同一 PR 的新审查会取消尚未完成的旧审查；获得运行机会后再读取最新提交。发布前还会检查 PR 是否仍打开且提交未变，避免把旧结果当作最新结论。

只创建分支而没有提交文件改动时，流程正常跳过，不建 PR、不调用模型。缺少 `DEEPSEEK_API_KEY` 时，在调用模型前明确报错。修复代码后仍按普通开发方式 `git commit`、`git push` 即可。

演示结束后，在网页关闭演示 PR，按需删除演示分支。已安装到 `main` 的流程可以继续用于新的 `work/<任务>` 分支。

## 为什么推送后分两次运行

固定的官方 Action 版本为 `d70510b174a1244958df0b03166a54912811f3e6`（v1），其 Claude Code 运行时为 2.1.312。该版本接受 `workflow_dispatch`，不直接接受 `push`。

因此，同一个工作流分两种入口：`push` 只准备 PR 并调用 GitHub 的 `workflow_dispatch` 接口；`workflow_dispatch` 准备 PR 后执行官方 Action，不再发起调度，所以不会循环。GitHub 允许 `GITHUB_TOKEN` 触发这种事件，不需要额外 PAT。准备 job 的 `actions: write` 用于调度；官方 Action 显式允许 `github-actions[bot]` 账号发起的这类运行。

所有审查指令都写在 `.github/prompts/review.md`，修改审查要求时编辑这一份文件即可。AI 从目标默认分支的最新提交读取提示词，通过 GitHub 工具读取待审查提交的源码并发布 PR 评论。它不执行提交中的代码。工作流成功表示本轮审查总结已发布（或本轮已过期/无差异而跳过），不代表代码无缺陷，合并由人决定。

审查 job 仅保留读取代码和写入 PR 评论所需的权限，不配置 `issues: write`，不提供创建 Issue 的工具。GitHub 的普通 PR 评论也使用 `issues/comments` API 路径，此路径仅用于定位和更新本流程的总结。验收时需要确认 Actions 运行成功，且 PR 中实际出现了对应提交的审查总结；本地检查不能替代云端验收。

参考：[官方 Action](https://github.com/anthropics/claude-code-action)、[DeepSeek Anthropic 兼容接口](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api/)、[GitHub 工作流之间的触发规则](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow)、[GitHub CLI 评论更新](https://cli.github.com/manual/gh_pr_comment)。
