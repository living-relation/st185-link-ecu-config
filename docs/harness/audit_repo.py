"""Inventory every harness file and wiring document, with git dates.

Run from the repo root:  python docs/harness/audit_repo.py
"""
import io, os, json, subprocess, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)


def gitdate(path):
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
                             capture_output=True, text=True).stdout.strip()
        return out or "untracked"
    except Exception:
        return "?"


def counts(path):
    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except Exception as e:
        return "UNREADABLE %s" % e
    n = lambda k: len(d.get(k) or [])
    cores = sum(len(c.get("cores") or []) for c in (d.get("cables") or []))
    return "conn %-3d wire %-4d cable %-2d cores %-3d splice %-2d term %-2d parts %d" % (
        n("connectors"), n("wires"), n("cables"), cores, n("splices"), n("terminals"),
        sum(n(k) for k in d if k.endswith("Parts")))


print("=" * 78)
print("HARNESS FILES")
print("=" * 78)
for p in sorted(glob.glob("docs/harness/**/*.harness", recursive=True)):
    print("%-52s %s" % (p.replace("\\", "/"), gitdate(p)))
    print("    %s" % counts(p))

print()
print("=" * 78)
print("WIRING / IO DOCUMENTS")
print("=" * 78)
pats = ["*.md", "*.html", "docs/*.md", "docs/*.html", "docs/**/*.md", "docs/**/*.html",
        "apps/**/*.html", "archive/**/*.md", "archive/**/*.html"]
seen = set()
rows = []
for pat in pats:
    for p in glob.glob(pat, recursive=True):
        q = p.replace("\\", "/")
        if q in seen or "node_modules" in q or "research-hub" in q:
            continue
        seen.add(q)
        low = q.lower()
        if not any(k in low for k in ("wiring", "harness", "schematic", "diagram",
                                      "electrical", "io-", "io_", "can-", "power",
                                      "truth", "face", "audit", "led")):
            continue
        rows.append((gitdate(q), q, os.path.getsize(q)))
for d, q, sz in sorted(rows):
    print("%s  %-62s %6d B" % (d, q, sz))

print()
print("=" * 78)
print("CONSOLIDATION PLAN SECTIONS")
print("=" * 78)
plan = "docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md"
lines = io.open(plan, encoding="utf-8").read().split("\n")
cur = None
body = []
for ln in lines + ["## EOF"]:
    if ln.startswith("## "):
        if cur:
            txt = "\n".join(body)
            mark = "SETTLED" if "Settled" in txt else ""
            opens = txt.count("\n- ") if "### Open" in txt else 0
            print("%-62s %-8s open~%d" % (cur[:62], mark, opens))
        cur = ln[3:].strip()
        body = []
    else:
        body.append(ln)
