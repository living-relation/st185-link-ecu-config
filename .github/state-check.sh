#!/usr/bin/env bash
# State-file check (git-checker PR hook; Dan 2026-11-01: COMMENT mode).
#   PR:         state-check.sh <base-ref> <head-ref> [pr-body-file]
#   pre-commit: state-check.sh HEAD --staged
#   set mode:   state-check.sh --mode comment|block   (writes .state-check-mode; commit it via a PR)
# comment (default): always exit 0, print WARN lines. block: exit 1 if any WARN.
root=$(cd "$(git rev-parse --git-common-dir)/.." && pwd)   # worktree -> main repo
if [ "$1" = "--mode" ]; then
  case "$2" in comment|block) t=$(git rev-parse --show-toplevel); echo "$2" > "$t/.state-check-mode"; echo "mode set to $2 in $t/.state-check-mode (commit it on a branch + PR)"; exit 0;;
  *) echo "usage: state-check.sh --mode comment|block" >&2; exit 2;; esac
fi
top=$(git rev-parse --show-toplevel)   # committed mode file on this checkout wins, else main repo's
mf="$top/.state-check-mode"; [ -f "$mf" ] || mf="$root/.state-check-mode"
mode=comment; [ -f "$mf" ] && mode=$(tr -d '[:space:]' < "$mf")
base=${1:-origin/main}; head=${2:-HEAD}; body=${3:-}
if [ "$head" = "--staged" ]; then files=$(git diff --cached --name-only); else files=$(git diff --name-only "$base...$head"); fi
if [ -f "$root/.state-check-paths" ]; then code=$(echo "$files" | grep -Ef "$root/.state-check-paths" || true)
else code=$(echo "$files" | grep -Ev '(\.md$|^docs/|^\.state-check-mode$)' | grep -v '^$' || true); fi
here=$(cd "$(dirname "$0")" && pwd)
reg=0; for n in automation.yml automation.yaml automation.json; do [ -f "$top/$n" ] && reg=1; done
# declared outputs (incl. auto-committed ones) never count as "code"
[ $reg = 1 ] && [ -f "$here/registry-check.py" ] && code=$(echo "$code" | (cd "$top" && python3 "$here/registry-check.py" --not-declared))
state=$(echo "$files" | grep -E '(^|/)(STATE\.md|DECISIONS\.md|OPEN-ITEMS[^/]*|AGENTS\.md)$' || true)
w=0
[ -n "$code" ] && [ -z "$state" ] && { echo "WARN: code changed but STATE.md/DECISIONS.md/OPEN-ITEMS not updated (label no-state-change if intended)."; w=1; }
txt=$( { [ -n "$body" ] && cat "$body"; [ "$head" != "--staged" ] && git log --format=%B "$base..$head"; } 2>/dev/null )
if echo "$txt" | grep -qiE 'after merge|not done here'; then
  echo "$state" | grep -qE 'STATE\.md|OPEN-ITEMS' || { echo "WARN: 'After merge'/'Not done here' step found; record it in STATE.md or OPEN-ITEMS."; w=1; }
fi
# automation registry (if the repo has automation.yml): same mode
if [ $reg = 1 ] && [ -f "$here/registry-check.py" ]; then
  if [ "$head" = "--staged" ]; then r=$(python3 "$here/registry-check.py" | grep -v '^BLOCK'); else r=$(python3 "$here/registry-check.py" --diff "$base" "$head" | grep -v '^BLOCK'); fi
  [ -n "$r" ] && echo "$r"; echo "$r" | grep -q '^WARN' && w=1
fi
[ "$mode" = block ] && [ $w = 1 ] && { echo "BLOCK: mode=block (.state-check-mode). Update the state file, or add the no-state-change label / [no-state]."; exit 1; }
exit 0
