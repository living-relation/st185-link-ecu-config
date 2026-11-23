#!/usr/bin/env bash
# Branch state gate (always blocks; no mode, no label escape). Template: skills/git-checker/hooks/.
# Live state lives in the repo: each branch commits its STATE-<slug>.md, and pr-closeout archives the
# state file as the PR's last commit (state_manager.py archive-branch runs
# `git mv STATE-<slug>.md archives/STATE-<slug>-<YYYYMMDD>.md`). This gate fails when the tree being
# checked (a PR merge ref, or a commit) still has any top-level STATE-*.md outside archives/.
# Usage: state-files-gate.sh [<tree-ish>]   (default HEAD). Read-only: never edits, commits or pushes.
set -u
tree=${1:-HEAD}
if ! names=$(git ls-tree --name-only "$tree" 2>/dev/null); then
  echo "state-files-gate: cannot read $tree" >&2
  exit 2
fi
left=$(printf '%s\n' "$names" | grep -E '^STATE-.+\.md$' || true)
if [ -n "$left" ]; then
  echo "state-files-gate: a branch state file would land on the trunk:"
  printf '%s\n' "$left" | sed 's/^/  /'
  echo "Fix: on the PR branch, archive the state file as the last commit:"
  echo "  python <workstation>/scripts/state/state_manager.py archive-branch"
  echo "  git commit -m \"Archive the state file\" && git push"
  exit 1
fi
echo "state-files-gate: OK (no top-level STATE-*.md)"
exit 0
