---
name: aomori-git-publish
description: 青森調査repoで、作業の区切りに変更内容の日本語要旨をコミット本文へ記録し、現在のブランチへplain Gitでコミット・プッシュする。Use when the user says「ここまでをコメント付きでコミット・プッシュ」「作業内容要旨を付けてpush」など、PR作成を伴わない通常の区切り作業を依頼したとき。
---

# Aomori Git Publish

## Goal

Publish completed work without making GitHub CLI or pull-request creation a prerequisite.
Use local `git` and the repository's configured HTTPS credentials.

## Routing

- Use this Skill for commit-and-push requests that do not mention a pull request.
- Do not require `gh`, create a branch, or open a pull request for this route.
- Use `github:yeet` instead only when the user explicitly requests a PR or a full branch-and-PR publication flow.
- Keep the current branch. Direct push from `main` is allowed in this repository when the user requests a normal work-boundary push.

## Workflow

1. Inspect `git status -sb`, the current branch, remotes, and the complete diff.
2. Treat the user's commit-and-push request as authorization for changes created in the current task.
3. If unrelated or ambiguous changes are present, stop and ask which files belong. Otherwise, continue without redundant confirmation.
4. Run or confirm the relevant validation. Do not rerun expensive checks already passed unless affected files changed afterward.
5. Stage only intended paths with explicit `git add -- <paths>`.
6. Inspect `git diff --cached --name-status`, `--stat`, and `--check`.
7. Create one Japanese commit:
   - Use a concise subject describing the outcome.
   - Add 2-4 body paragraphs or bullets summarizing what changed, why, and the main validation.
8. Push with `git push -u origin <current-branch>`.
9. Verify that local `HEAD` equals `origin/<current-branch>` and report the branch, full commit hash, subject, validation, and clean/remaining worktree state.

## Safety

- Never use force push, destructive reset, rebase, or amend unless explicitly requested.
- Never stage unrelated changes silently.
- Do not treat missing `gh` as a blocker for plain commit and push.
- If HTTPS authentication or the push itself fails, preserve the commit and report the exact failure.
- Do not open a pull request unless explicitly requested.
