"""Doc-growth guard: flag oversized Markdown files and unlisted top-level docs.

Daniel (2026-10-04, approved doc-growth measure; built 2026-10-13). WARN-ONLY: prints
GitHub warning annotations and always exits 0 (pass --strict to exit 1).

  1. Any tracked .md file longer than MAX_LINES lines.
  2. Any tracked top-level .md file whose name is not mentioned in AGENTS.md (the project map).

No auto-archiving and no "untouched for N days" sweep - those were rejected.

Usage:  python .github/scripts/check_doc_size.py [--max N] [--strict]
Standard library only.
"""
import argparse
import os
import subprocess
import sys

MAX_LINES = 1500
MAP_FILE = "AGENTS.md"


def tracked_md(root):
    out = subprocess.run(["git", "ls-files", "-z", "--", "*.md"], cwd=root,
                         capture_output=True, check=True).stdout.decode("utf-8")
    return sorted(p for p in out.split("\0") if p and not p.startswith("archive/"))


def count_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--max", type=int, default=MAX_LINES)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    files = tracked_md(root)
    found = 0

    for p in files:
        n = count_lines(os.path.join(root, p))
        if n > args.max:
            found += 1
            print(f"::warning file={p}::{p} is {n} lines (guard {args.max}). Split it, or move "
                  f"finished history out; one owner per fact.")

    with open(os.path.join(root, MAP_FILE), encoding="utf-8", errors="replace") as fh:
        project_map = fh.read()
    for p in files:
        if "/" not in p and p != MAP_FILE and p not in project_map:
            found += 1
            print(f"::warning file={p}::top-level {p} is not listed in the project map "
                  f"({MAP_FILE}). Add it there, or move it under docs/.")

    print(f"check_doc_size: {found} warning(s) ({len(files)} .md files checked)")
    return 1 if (found and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
