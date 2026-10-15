"""PR body gate (M3): the body must contain a line `Rows: <n>, <n>` or `Rows: none`.

    PR_BODY="..." python .github/scripts/check_pr_rows.py     exit 0 = line present

The line says which docs/OPEN-ITEMS.md rows the change touched, so the tracker is
updated by the session that did the work (st185-ship-change "docs updated" step).
"""
import os
import re
import sys

ROWS_LINE = re.compile(r"^\s*Rows:\s*(none|\d+(\s*,\s*\d+)*)\s*$", re.I | re.M)


def has_rows_line(body: str) -> bool:
    return bool(ROWS_LINE.search(body or ""))


def main() -> int:
    if has_rows_line(os.environ.get("PR_BODY", "")):
        print("PR body has a Rows: line.")
        return 0
    print("::error::PR body needs a line 'Rows: <n>, <n>' (OPEN-ITEMS rows touched) or 'Rows: none'.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
