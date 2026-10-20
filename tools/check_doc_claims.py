"""No stale documents (DECISIONS R211): when a new document or SoT replaces an older one, the older
one is consolidated into it or deleted - never archived, bannered "superseded" or kept for reference.

  C1  no tracked file lives in an archive-style folder (archive / old / legacy / superseded / deprecated)
  C2  no document outside the keep list says it IS a source of truth (the keep list owns that claim)
  C3  no document opens (first 15 lines) with a superseded / historical / archived / kept-for-reference banner
  C4  no document names a repo file under docs/ or sot/ that no longer exists (a removed SoT or doc that older
      text still points at); DECISIONS and OPEN-ITEMS history are exempt

HARD: all four. Exit 1 on any finding.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_EXT = (".md", ".html", ".txt")
SKIP = ("docs/research-hub.html", "docs/status/")
SKIP_DIRS = (".claude/", ".cursor/", "cad/", "tune/", "docs/intercooler-turbo-study/", "docs/5sgte-project-data/", "docs/harness/routes/",
             "docs/vendor/", "docs/harness/rebuild/")
# The keep list (R211) and the docs that state the chain of sources; only these may call something a source of truth.
KEEP = {
    "AGENTS.md", "README.md", "XTREMEX-IO-TABLE.html", "sot/README.md",
    "docs/harness/README.md", "docs/RECONCILIATION-RULES.md", "docs/dispatch/DISPATCH-RULES.md",
    "docs/harness/redesign/DECISIONS.md", "docs/OPEN-ITEMS.md", "docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md",
}
IS_SOT = re.compile(r"\b(is|are|as) (the |a |our )?(one |single |only )?(\w+ ){0,2}(source of truth|sources of truth|SoT)\b|"
                    r"\bSoT (for|of) (the )?\w+", re.I)
NEGATED = re.compile(r"\b(not|never|no) (a |the )?(\w+ ){0,2}(source of truth|SoT)\b", re.I)
BANNER = re.compile(r"\bsupersed(ed|es)\b|\bhistorical\b|history only|\barchived?\b|kept for reference|\bobsolete\b|\bretired\b", re.I)
ARCHIVE_DIR = re.compile(r"(^|/)(archive|archived|old|legacy|superseded|deprecated)(/|$)", re.I)


PATH_REF = re.compile(r"(?<![\w/.-])((?:docs|sot)/[\w./-]*[\w-]\.(?:md|html|csv|json|py|xlsx|txt))")
HISTORY = ("docs/harness/redesign/DECISIONS.md", "docs/OPEN-ITEMS.md")


def main():
    files = subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True, encoding="utf-8").split("\n")
    bad = []
    for f in files:
        if not f:
            continue
        if ARCHIVE_DIR.search(f):
            bad.append("C1 %s: archive-style folder" % f)
        if not f.endswith(DOC_EXT) or f in SKIP or f.startswith(SKIP) or f.startswith(SKIP_DIRS):
            continue
        try:
            text = open(os.path.join(REPO, f), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if f not in KEEP:
            for n, line in enumerate(text.split("\n"), 1):
                if IS_SOT.search(line) and not NEGATED.search(line):
                    bad.append("C2 %s:%d: claims to be a source of truth: %s" % (f, n, line.strip()[:110]))
        if f not in HISTORY and not f.startswith("docs/harness/rebuild/"):
            for m in sorted(set(PATH_REF.findall(text))):
                if "*" in m or "<" in m or m.startswith("docs/vendor/") or os.path.exists(os.path.join(REPO, m)):
                    continue            # docs/vendor is gitignored (local-only vendor PDFs)
                bad.append("C4 %s: names %s, which does not exist" % (f, m))
        head = "\n".join(text.split("\n")[:15])
        m = BANNER.search(head)
        if m and f not in ("docs/harness/redesign/DECISIONS.md", "docs/OPEN-ITEMS.md", "docs/dispatch/DISPATCH-RULES.md"):
            bad.append("C3 %s: opens with a '%s' banner" % (f, m.group(0)))
    for b in bad:
        print("FAIL", b)
    print("check_doc_claims: %s" % ("FAIL (%d)" % len(bad) if bad else "OK"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
