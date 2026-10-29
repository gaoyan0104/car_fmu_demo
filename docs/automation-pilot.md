# Review Automation Pilot with the Official Claude Code Action

The workflow creates a draft PR or reuses an existing PR, reviews its changes, and publishes a review summary.

```text
Push a work/<task> branch
  -> Review automation creates or finds the PR
  -> The default branch workflow starts the AI review
  -> anthropics/claude-code-action reads code, calls DeepSeek, and uses GitHub tools
  -> The review summary is posted or updated in the PR
  -> A person decides what to fix and whether to merge
```

## Configuration Files

| File | Purpose |
| --- | --- |
| `.github/workflows/review-automation.yml` | Creates PRs after a push, starts reviews, and configures the model and permissions |
| `.github/prompts/review.md` | Defines the review steps, reporting rules, and summary format |
| `examples/review-automation/known-unit-error.patch` | Optional example of a known speed-unit defect |

The official Claude Code Action handles model requests, the agent tool loop, and source reading. Review findings stay in the PR; maintainers arrange independent follow-up work separately.

The workflow reviews source code without running project tests, builds, or FMU simulations. A review with no findings does not establish that tests pass.

New task branches created from the updated default branch use a PR description with two sections: **Goal** and **Scope**. The author fills these in. Existing PR descriptions are preserved, while review summaries are updated in comments.

## 1. Install the Configuration

To use this workflow in another repository, copy `.github/workflows/review-automation.yml` and `.github/prompts/review.md`, then merge them into its default branch through a PR. The prompt uses requirements already documented in the repository. The initial installation PR must be created manually; subsequent task PRs can be created automatically.

This guide and the optional demo patch are for documentation and testing. The workflow discovers the repository name and default branch through GitHub.

Create task branches from the updated default branch. A push uses the workflow stored on the pushed branch, so an older branch can still create a PR using an older template.

## 2. Configure GitHub

1. Open **Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret**. Add `DEEPSEEK_API_KEY` with your DeepSeek API key.
2. Open **Settings -> Actions -> General -> Workflow permissions**. Enable **Allow GitHub Actions to create and approve pull requests** if that option is shown. The AI reviews and comments; a person decides whether to merge.

The default model is `deepseek-flash`. Set the `AI_REVIEW_MODEL` repository variable to choose another model. Secrets are configured separately for each repository.

The workflow passes `DEEPSEEK_API_KEY` to the Action's `anthropic_api_key` input and sets `ANTHROPIC_BASE_URL` to `https://api.deepseek.com/anthropic`, using DeepSeek's Anthropic-compatible API.

The workflow explicitly supplies GitHub's built-in `GITHUB_TOKEN`. No separate Claude GitHub App installation or personal access token is required for the workflow. Pushing code still requires your GitHub login.

## 3. Prepare a Repeatable Defect

After the installation PR is merged, start from the latest default branch. Use a new branch name for each experiment. The following commands assume the default branch is `main`:

```bash
git switch main
git pull --ff-only origin main
git switch -c work/demo-review-english
```

In `src/export_sysml_to_json.py`, add the following validation inside `find_block`, immediately before `m = re.search(...)`:

```python
    if not header_regex:
        raise ValueError("header_regex must not be empty")
```

Then deliberately change the closing-brace branch from `depth -= 1` to:

```python
        elif c == "}":
            depth += 1
```

This prevents the depth from returning to zero for a valid block. Keep the input validation when fixing the defect so the PR retains a real change. If that validation already exists, choose another legitimate change that will remain after the defect is fixed.

Commit and push:

```bash
git add src/export_sysml_to_json.py
git commit -m "Add parser input validation"
git push -u origin work/demo-review-english
```

The Action installs the Claude Code runtime on the runner. This review workflow does not require you to install Python, FMPy, or OpenModelica on the runner.

## 4. Check the First Review

Open **Actions -> Review automation**. One push normally produces two runs: the `push` run prepares the PR and dispatches the workflow; the `workflow_dispatch` run performs the AI review. The AI job being skipped in the first run is expected.

Check that:

1. A draft PR is created with **Goal** and **Scope** in its description.
2. A review comment contains **Change Summary** and **Review Findings**.
3. The findings identify the incorrect closing-brace depth update, with its code location, trigger conditions, impact, and a fix suggestion.

The workflow checks for a published bot summary with the dedicated marker, the full reviewed commit ID, and an updated timestamp for this run. If no matching summary is found, the run fails. Successful runs include a link to the summary in the Actions run summary.

The hidden marker `<!-- ai-pr-review -->` identifies the review comment. Later reviews update this comment and preserve other comments. Older summaries without the marker are retained; the first marked summary is created separately.

After filling in the PR's **Goal** and **Scope**, you can rerun the review through **Review automation -> Run workflow**. Select the default branch as the execution branch and enter `work/demo-review-english` in the `branch` input.

Wait for the first review to finish before continuing.

## 5. Fix the Defect and Push Again

Restore the closing-brace branch to:

```python
        elif c == "}":
            depth -= 1
```

Keep the input validation, then commit and push:

```bash
git add src/export_sysml_to_json.py
git commit -m "Fix closing brace depth tracking"
git push
```

The next review should use the same PR, update the same marked comment, and note that the earlier defect is fixed. Findings that still apply should use current code locations and evidence.

Further pushes reuse the open PR, including a PR already marked ready for review. The workflow does not turn it back into a draft. A new review cancels an unfinished review for the same PR and resolves the latest commit after acquiring its concurrency slot. The PR state and commit are checked again before publishing.

If the branch has no file changes relative to the default branch, the workflow skips PR creation and the AI call. This is why the experiment keeps the input validation after fixing the intentional defect. A missing `DEEPSEEK_API_KEY` is reported before calling the model.

Close the experimental PR when finished and delete its branch if desired.

## Why a Push Starts Two Runs

The workflow pins the official Action to `d70510b174a1244958df0b03166a54912811f3e6`. This version accepts `workflow_dispatch` and does not directly accept `push`.

The `push` entry prepares a PR and calls GitHub's workflow dispatch API. The dispatched run prepares the PR and runs the Action without dispatching again. GitHub permits `GITHUB_TOKEN` to trigger this event. The prepare job needs `actions: write` to dispatch, and the Action allows `github-actions[bot]` to initiate these runs.

Review instructions live in `.github/prompts/review.md`. The review job reads the prompt from the latest default branch commit, uses GitHub tools to read the commit under review, and publishes the summary without executing project code. A successful workflow means the review summary was published, or the run was skipped because it was outdated or had no changes. Merging remains a human decision.

The review job has permissions to read code and write PR comments. GitHub uses the `issues/comments` API for ordinary PR comments as well; this workflow uses it to locate and update its summary. It does not configure `issues: write` or provide Issue creation tools. Verify both the Actions result and the review comment for the relevant commit.

References: [Official Action](https://github.com/anthropics/claude-code-action), [DeepSeek Anthropic-compatible API](https://api-docs.deepseek.com/guides/anthropic_api/), [Triggering a workflow from a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow), [GitHub CLI PR comments](https://cli.github.com/manual/gh_pr_comment).
