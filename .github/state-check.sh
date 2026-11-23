#!/usr/bin/env bash
# Graduation check (STATE files are not homes; live state is checked by state_lint.py and state-files-gate).
#   PR:         state-check.sh <base-ref> <head-ref> [pr-body-file]
#   pre-commit: state-check.sh HEAD --staged [commit-msg-file]
#   set mode:   state-check.sh --mode comment|block   (writes .state-check-mode; commit it via a PR)
# Warns when code changed but no home did (DECISIONS, .claude/rules/, SPEC, data),
# when a PR body has no "State:" line, and when an after-merge step is not named in a State: line.
# Homes: override per repo with .state-check-homes (one ERE per line). Code: .state-check-paths.
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
else code=$(echo "$files" | grep -Ev '(\.md$|^docs/|^\.state-check-mode$|^\.cursor/rules/|(^|/)VERIFIED\.lock$)' | grep -v '^$' || true); fi
here=$(cd "$(dirname "$0")" && pwd)
reg=0; for n in automation.yml automation.yaml automation.json; do [ -f "$top/$n" ] && reg=1; done
# declared outputs (incl. auto-committed ones) never count as "code"
[ $reg = 1 ] && [ -f "$here/registry-check.py" ] && code=$(echo "$code" | (cd "$top" && python3 "$here/registry-check.py" --not-declared))
if [ -f "$root/.state-check-homes" ]; then homes=$(echo "$files" | grep -Ef "$root/.state-check-homes" || true)
else homes=$(echo "$files" | grep -E '(^|/)DECISIONS[^/]*\.md$|(^|/)\.claude/rules/|(^|/)SPEC[^/]*\.md$|(^|/)specs?/|(^|/)sot/|(^|/)data/' || true); fi
w=0
[ -n "$code" ] && [ -z "$homes" ] && { echo "WARN: code changed but no DECISIONS / .claude/rules / SPEC / data change. Run state-closeout to graduate what this change taught (label no-state-change if nothing did)."; w=1; }
txt=$( { [ -n "$body" ] && cat "$body"; [ "$head" != "--staged" ] && git log --format=%B "$base..$head"; } 2>/dev/null )
stateline=0; echo "$txt" | grep -qE '^State:' && stateline=1
[ -n "$body" ] && [ "$head" != "--staged" ] && [ $stateline = 0 ] && { echo "WARN: PR body has no 'State:' line (what moved to which home, or 'State: no change')."; w=1; }
if echo "$txt" | grep -qiE 'after merge|not done here'; then
  [ $stateline = 1 ] || { echo "WARN: 'After merge'/'Not done here' step found; record it as [TASK] or [BKLG] with state-closeout and name it in a State: line."; w=1; }
fi
# automation registry (if the repo has automation.yml): same mode
if [ $reg = 1 ] && [ -f "$here/registry-check.py" ]; then
  if [ "$head" = "--staged" ]; then r=$(python3 "$here/registry-check.py" | grep -v '^BLOCK'); else r=$(python3 "$here/registry-check.py" --diff "$base" "$head" | grep -v '^BLOCK'); fi
  [ -n "$r" ] && echo "$r"; echo "$r" | grep -q '^WARN' && w=1
fi
[ "$mode" = block ] && [ $w = 1 ] && { echo "BLOCK: mode=block (.state-check-mode). Graduate with state-closeout, or add the no-state-change label / [no-state]."; exit 1; }
exit 0
