---
name: ship-change
description: Ships a finished repo change through a PR to protected `main` and cleans up afterward. Use when Dan says "ship this", "open a PR", "merge it", or work in a worktree/branch is done and ready to land. Covers the required status checks, squash-merge, and removing the worktree/branches when done. Do NOT use this mid-change — only once the work is committed and ready to go out.
paths:
  - .github/workflows/checks.yml
  - .github/workflows/protect-research-hub.yml
---
# ship-change

## Where to run
- The worktree/branch with the finished change. Shell: PowerShell.

## Critical
- `main` is protected: a PR needs **"Repo checks"** and **"Protect research hub"** green before it can merge.
- Rebase on `origin/main` before opening the PR — don't let it drift stale.
- Never commit `docs/research-hub.html` (the pre-commit hook refuses it; the "Regenerate research hub" Action owns it — `git restore --staged docs/research-hub.html && git checkout -- docs/research-hub.html` if it's staged) or anything from `_research/` (local-only, untracked, read-only).
- Never force-push.
- Squash-merge once both checks are green.
- After merge, remove the worktree and delete both the local and remote branch — don't leave a stale worktree or branch behind.

## Instructions
1. Confirm the working tree is clean and the branch is current: `git status`, `git fetch origin`, `git rebase origin/main`.
2. Confirm no `docs/research-hub.html` or `_research/` content is staged or committed; restore/checkout it out if it crept in.
3. Push the branch and open the PR against `main`.
4. Wait for **Repo checks** and **Protect research hub** to go green; fix and re-push if either fails (never skip them).
5. Squash-merge the PR once green.
6. Remove the worktree (`git worktree remove <path>`) and delete the local and remote branch (`git branch -d <branch>`, `git push origin --delete <branch>`).

## Verification
- The PR is merged (squash) with both required checks green.
- `git worktree list` no longer shows the worktree; the branch is gone both locally and on the remote.
