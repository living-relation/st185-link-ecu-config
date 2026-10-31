"""Self-test for the M3 docs gates: PR-body Rows line + the Needs Dan table.

    python .github/scripts/test_docs_gates.py      exit 0 = every case behaved as expected
"""
import sys
import tempfile
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

# --- Needs Dan table in OPEN-ITEMS (R119) ---
real = (ROOT / "docs" / "OPEN-ITEMS.md").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "docs"))
from needs_dan import open_questions  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    t = Path(d) / "t.md"
    hdr = "| ID | Topic | Question | Options | Recommended |\n|---|---|---|---|---|\n"
    t.write_text(hdr, encoding="utf-8")
    check("needs-dan: header only = nothing open", open_questions(t) == [])
    t.write_text(hdr + "| M6 | topic | Do it; really? | A) yes; B) no, ok | B |\n"
                 "| M7 | topic | Which? | A) one; B) two; C) three | A if it fits, else C |\n", encoding="utf-8")
    q = open_questions(t)
    check("needs-dan: row parsed with options and recommended (one, or several by circumstance)",
          len(q) == 2 and q[0]["id"] == "M6" and q[0]["text"] == "Do it; really?"
          and [o["value"] for o in q[0]["options"]] == ["A", "B"]
          and [o["recommended"] for o in q[0]["options"]] == [False, True]
          and [o["recommended"] for o in q[1]["options"]] == [True, False, True])
# The real table may hold open questions (it is where they live, R119); each must parse
# with an ID, at least two options and at least one recommended (several when circumstances differ).
check("needs-dan: real tracker has the section and every open question parses",
      "| ID | Topic | Question | Options | Recommended |" in real
      and all(q["id"] and len(q["options"]) >= 2
              and sum(o["recommended"] for o in q["options"]) >= 1 for q in open_questions()))
check("needs-dan: questions.json is gone", not (ROOT / "docs" / "status" / "questions.json").exists())

print(f"\n{fails} failure(s).")
sys.exit(1 if fails else 0)
