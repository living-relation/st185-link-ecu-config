"""Self-test for the M3 docs gates: PR-body Rows line + research-hub --strict.

    python .github/scripts/test_docs_gates.py      exit 0 = every case behaved as expected
"""
import importlib.util
import io
import os
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import check_pr_rows  # noqa: E402

fails = 0


def check(name: str, ok: bool) -> None:
    global fails
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'}  {name}")


# --- PR body Rows line ---
for body, want, name in [
    ("Summary\n\nRows: none\n", True, "Rows: none accepted"),
    ("Rows: 12, 34", True, "Rows: 12, 34 accepted"),
    ("Rows: 7", True, "Rows: 7 accepted"),
    ("", False, "empty body refused"),
    (None, False, "missing body refused"),
    ("Updated rows 12 and 34", False, "prose without a Rows: line refused"),
    ("Rows: maybe", False, "Rows: maybe refused"),
]:
    check(f"PR body: {name}", check_pr_rows.has_rows_line(body) == want)

# --- research hub --strict: count mismatch is collected (and fails main) ---
spec = importlib.util.spec_from_file_location("hub", ROOT / "docs" / "build-research-hub.py")
hub = importlib.util.module_from_spec(spec)
sys.modules["hub"] = hub  # dataclasses looks the module up by name
spec.loader.exec_module(hub)

real = hub.TRACKER.read_text(encoding="utf-8")
hub.COUNT_PROBLEMS.clear()
with redirect_stderr(io.StringIO()):
    hub.load_status()
check("hub: real tracker counts match", not hub.COUNT_PROBLEMS)

status = next(t for t in hub.parse_md_tables(real) if t["columns"][:2] == ["Bucket", "Open"])
row = status["rows"][0]
bad = real.replace(f"| {row[0]} | {row[1]} |", f"| {row[0]} | {int(row[1]) + 5} |", 1)
check("hub: test edit changed the tracker", bad != real)
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "OPEN-ITEMS.md"
    p.write_text(bad, encoding="utf-8")
    hub.TRACKER = p
    hub.COUNT_PROBLEMS.clear()
    with redirect_stderr(io.StringIO()):
        hub.load_status()
check("hub: wrong Status count is flagged", len(hub.COUNT_PROBLEMS) == 1)
sys.argv = ["x", "--strict"]
try:
    hub.main()
    check("hub: --strict exits 1 on a count problem", False)
except SystemExit as e:
    check("hub: --strict exits 1 on a count problem", bool(e.code))

# --- Needs Dan table in OPEN-ITEMS (R119) ---
sys.path.insert(0, str(ROOT / "docs"))
from needs_dan import open_questions  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    t = Path(d) / "t.md"
    hdr = "| ID | Topic | Question | Options | Recommended |\n|---|---|---|---|---|\n"
    t.write_text(hdr, encoding="utf-8")
    check("needs-dan: header only = nothing open", open_questions(t) == [])
    t.write_text(hdr + "| M6 | topic | Do it; really? | A) yes; B) no, ok | B |\n", encoding="utf-8")
    q = open_questions(t)
    check("needs-dan: row parsed with options and recommended",
          len(q) == 1 and q[0]["id"] == "M6" and q[0]["text"] == "Do it; really?"
          and [o["value"] for o in q[0]["options"]] == ["A", "B"]
          and [o["recommended"] for o in q[0]["options"]] == [False, True])
check("needs-dan: real tracker has the section and no open question",
      "| ID | Topic | Question | Options | Recommended |" in real and open_questions() == [])
check("needs-dan: questions.json is gone", not (ROOT / "docs" / "status" / "questions.json").exists())

print(f"\n{fails} failure(s).")
sys.exit(1 if fails else 0)
