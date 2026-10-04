"""One owner per fact: find long passages copied between tracked Markdown files.

Daniel (2026-10-04, approved doc-growth measure 1): a fact lives in ONE file; every other
file links to it. This check lists passages of MIN_LINES or more identical lines that
appear in two or more tracked .md files (archive/ excluded - it is never authoritative).

WARN-ONLY for now: it prints the duplicates (as GitHub warning annotations in CI) and
always exits 0. Pass --strict to exit 1 when anything is found, once the current
offenders are cleaned up.

What counts as a line:
  - compared after stripping leading/trailing whitespace
  - blank lines, code fences, table separator rows (|---|---|), horizontal rules and bare
    heading marks are skipped (they would make every table and code block look copied)
  - lines shorter than 4 characters are skipped for the same reason
A passage is MIN_LINES or more of the remaining lines, in the same order, in both files.

Usage:  python .github/scripts/check_doc_duplicates.py [--min N] [--strict]
Standard library only.
"""
import argparse
import collections
import os
import re
import subprocess
import sys

MIN_LINES = 6
TRIVIAL = re.compile(r"^(```.*|~~~.*|[-*_]{3,}|\|?[\s:|-]+\|?|#+)$")


def tracked_md(root):
    out = subprocess.run(["git", "ls-files", "-z", "--", "*.md"], cwd=root,
                         capture_output=True, check=True).stdout.decode("utf-8")
    return sorted(p for p in out.split("\0") if p and not p.startswith("archive/"))


def meaningful_lines(path):
    """[(original line number, normalized text)] for the lines that count."""
    keep = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, raw in enumerate(fh, 1):
            t = raw.strip()
            if len(t) < 4 or TRIVIAL.match(t):
                continue
            keep.append((n, t))
    return keep


def find_duplicates(root, min_lines):
    files = {p: meaningful_lines(os.path.join(root, p)) for p in tracked_md(root)}
    where = collections.defaultdict(list)          # window text -> [(file, start index)]
    for p, lines in files.items():
        for i in range(len(lines) - min_lines + 1):
            where[tuple(t for _, t in lines[i:i + min_lines])].append((p, i))

    # For each pair of files, merge consecutive matching windows into one passage.
    hits = collections.defaultdict(set)            # (file a, file b) -> {(i, j)}
    for spots in where.values():
        if len({p for p, _ in spots}) < 2:
            continue
        for pa, i in spots:
            for pb, j in spots:
                if pa < pb:
                    hits[(pa, pb)].add((i, j))
    passages = []
    for (pa, pb), pairs in hits.items():
        done = set()
        for i, j in sorted(pairs):
            if (i, j) in done:
                continue
            k = 0
            while (i + k, j + k) in pairs:
                done.add((i + k, j + k))
                k += 1
            la, lb = files[pa], files[pb]
            n = k + min_lines - 1                      # meaningful lines in the passage
            passages.append((n, pa, la[i][0], la[i + n - 1][0], pb, lb[j][0], lb[j + n - 1][0],
                             la[i][1]))
    passages.sort(key=lambda r: (-r[0], r[1], r[2]))
    return passages


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--min", type=int, default=MIN_LINES, help="shortest passage to report")
    ap.add_argument("--strict", action="store_true", help="exit 1 if anything is found")
    a = ap.parse_args()
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                          text=True, check=True).stdout.strip()
    found = find_duplicates(root, a.min)
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    for n, pa, a0, a1, pb, b0, b1, first in found:
        msg = "%d duplicated lines: %s:%d-%d = %s:%d-%d (starts %r)" % (
            n, pa, a0, a1, pb, b0, b1, first[:60])
        if gha:
            print("::warning file=%s,line=%d,endLine=%d,title=Duplicated passage::%s"
                  % (pb, b0, b1, msg))
        else:
            print("  " + msg)
    files = sorted({r[1] for r in found} | {r[4] for r in found})
    print("\n%d duplicated passage(s) of %d+ lines across %d file(s). One owner per fact: keep "
          "the passage in one file and link to it from the others." % (len(found), a.min, len(files)))
    if not a.strict:
        print("(warn-only - this check never fails the build unless run with --strict)")
    return 1 if (a.strict and found) else 0


if __name__ == "__main__":
    sys.exit(main())
