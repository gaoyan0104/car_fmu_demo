# 官方 Action 版：在 car_fmu_demo 试运行

第一版只做四件事：自动创建草稿 PR、AI review、中文总结、按需创建后续 Issue。

```text
推送 work/<任务> 分支
  → Review automation 创建或找到草稿 PR
  → 直接调度默认分支的 AI 审查任务
  → anthropics/claude-code-action 读取代码、调用 DeepSeek、使用 GitHub 工具
  → 发布审查总结，按需创建后续 Issue
  → 人决定修复和合并
```

## 这次主要配置什么

| 文件 | 职责 |
| --- | --- |
| `.github/workflows/review-automation.yml` | 推送后创建 PR、调度 AI 审查，配置官方 Action 的模型和权限 |
| `.github/prompts/review.md` | 集中说明项目规则、审查步骤、中文总结和后续 Issue 的指令 |
| `examples/review-automation/known-unit-error.patch` | 可重复的已知缺陷和独立后续需求样例 |

模型请求、agent 工具循环和源码阅读交给官方 Claude Code Action。第一版不实现自写模型客户端、严格 Issue 去重、固定创建数量限制、自定义 AI 合并门禁或单独的多轮复核服务。

本流程只审查源码，不运行项目测试、构建或 FMU 仿真。总结必须明确说明这一点；AI 没发现问题不代表测试通过。

## 第一步：上传安装配置

当前准备分支是 `codex/review-automation-pilot`。在有该仓库写入权限且已经完成 GitHub 登录的终端执行：

```bash
cd /home/gy/project/car_fmu_demo
git status
git add .github .gitignore README.md docs examples
git commit -m "Configure official Claude Code Action review pilot"
git push -u origin codex/review-automation-pilot
```

打开 <https://github.com/gaoyan0104/car_fmu_demo>，手动创建安装 PR：该分支 → `main`。人工检查配置后合并，流程才安装到默认分支；第一个安装 PR 需要手动创建。

## 第二步：网页配置

1. **Settings → Secrets and variables → Actions → Secrets → New repository secret**：名称填 `DEEPSEEK_API_KEY`，值填写你自己的 DeepSeek API 密钥。
2. **Settings → Actions → General → Workflow permissions**：允许 GitHub Actions 创建 Pull Request；若界面显示 “Allow GitHub Actions to create and approve pull requests”，勾选并保存。程序任务只包括审查和建 Issue，不提交批准。

模型默认 `deepseek-flash`；需要更改时添加 Variable `AI_REVIEW_MODEL`。密钥按仓库隔离，Daidalis 仓库中的 Secret 不会自动用于这里。

工作流将 `DEEPSEEK_API_KEY` 传给官方 Action 的 `anthropic_api_key` 输入，并将 `ANTHROPIC_BASE_URL` 配为 `https://api.deepseek.com/anthropic`。这里采用 DeepSeek 的 Anthropic 兼容接口，不是之前自写客户端使用的 Chat Completions 接口。

工作流显式提供 GitHub 自带的 `GITHUB_TOKEN`，不要求额外安装 Claude GitHub App，也不把个人 GitHub PAT 写进源码。上传仓库仍需要你的 GitHub 登录；DeepSeek 密钥不能用于 GitHub 登录。

## 第三步：制造一个可验证的错误

安装 PR 合并后，在本地执行：

```bash
git switch main
git pull --ff-only
git switch -c work/demo-review
git apply examples/review-automation/known-unit-error.patch
git diff
git add src/export_sysml_to_json.py docs/review-demo-follow-up.md
git commit -m "Demo a known speed-unit defect"
git push -u origin work/demo-review
```

补丁只修改 exporter 中的速度表达式，并新增一份需求文档：

- 当前缺陷：把 `vTarget_mps` 错误乘以 `3.6`，使 `27.78 m/s` 导出为 `100.008`，但字段仍表示 m/s。
- 独立后续需求：以后增加批量 SysML 导出命令，为两个输入生成两个互不覆盖的 JSON 输出，并给出明确验收标准。

本地只需 Git 即可构造样例。云端由官方 Action 安装 Claude Code 运行时，无需为这套审查流程安装 Python、FMPy 或 OpenModelica。

## 第四步：看 GitHub 结果

打开仓库 Actions，查看 **Review automation**。一次推送会产生两次运行：`push` 运行创建 PR 并发起调度，随后 `workflow_dispatch` 运行执行 AI 审查。第一次运行的 AI job 显示跳过是正常的。

期望看到：

1. 自动创建一个 Draft PR。
2. 官方 Action 阅读差异和相关文件，在 PR 中用中文指出单位错误、源码位置和影响。
3. 总结注明“源码审查，未运行项目测试、构建或仿真”。
4. 有依据的独立批量导出需求被整理为后续 Issue，其链接进入总结。

没有发现依据时允许不建 Issue。模型调用失败、权限不足或只输出最终对话而没实际发表评论，均不能当作线上验收成功。此测试仓库的最近一条机器人评论由提示词指导使用 GitHub CLI 内置 `--edit-last --create-if-none` 更新。

补充 PR 的 Goal、范围和验收标准后，可在 Actions 的 **Review automation → Run workflow** 手动重跑：执行分支选 `main`，输入 `branch` 填 `work/demo-review`。这次直接审查该分支当前提交，不等待其他工作流。

## 第五步：修复并再次上传

```bash
git apply --reverse --include=src/export_sysml_to_json.py examples/review-automation/known-unit-error.patch
git add src/export_sysml_to_json.py
git commit -m "Fix the intentional speed-unit conversion"
git push
```

Review automation 应对最新提交重新审查，确认单位错误已修复并更新总结。第一版不对“绝不重复创建 Issue”作保证，重复的候选任务先人工整理。

演示结束后，在网页关闭演示 PR，按需删除演示分支、保留或关闭候选 Issue。已安装到 `main` 的流程可以继续用于新的 `work/<任务>` 分支。

## 为什么推送后分两次运行

固定的官方 Action 版本为 `d70510b174a1244958df0b03166a54912811f3e6`（v1），其 Claude Code 运行时为 2.1.312。该版本接受 `workflow_dispatch`，不直接接受 `push`。

因此，同一个工作流分两种入口：`push` 只准备 PR 并调用 GitHub 的 `workflow_dispatch` 接口；`workflow_dispatch` 准备 PR 后执行官方 Action，不再发起调度，所以不会循环。GitHub 允许 `GITHUB_TOKEN` 触发这种事件，不需要额外 PAT。准备 job 的 `actions: write` 用于调度；官方 Action 显式允许 `github-actions[bot]` 账号发起的这类运行。

所有审查指令都写在 `.github/prompts/review.md`，修改审查要求时编辑这一份文件即可。AI 从默认分支读取提示词，通过 GitHub 工具读取提交源码，发布评论和后续 Issue。它不执行提交中的代码。工作流成功只表示任务完成，合并由人决定。

此前已经验证同版本 Claude Code 通过 DeepSeek Anthropic 兼容接口使用原生 Read 工具，识别出演示的单位缺陷与独立后续需求。本版已移除项目测试，仍需上传后实测 GitHub 调度、PR 评论和 Issue 创建；本地验证不能替代线上验收。

参考：[官方 Action](https://github.com/anthropics/claude-code-action)、[DeepSeek Anthropic 兼容接口](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api/)、[GitHub 工作流之间的触发规则](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow)、[GitHub CLI 评论更新](https://cli.github.com/manual/gh_pr_comment)。
