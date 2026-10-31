"""Open questions for Dan: the "Needs Dan" table in docs/OPEN-ITEMS.md (DECISIONS R119).

One reader for every consumer (fusebox clearance check, fusebox summary):

    from needs_dan import open_questions
    open_questions()   # [{"id", "topic", "text", "options": [{"value","label","recommended"}]}]

Table shape (header row only = nothing open):

    | ID | Topic | Question | Options | Recommended |
    | M6 | topic | text     | A) label; B) label | A |

Recommended is one letter, or several when the circumstances differ ("A if the fit passes, else B";
Dan 2026-10-31): every standalone capital letter in the cell counts.

Standard library only.
"""
import re
from pathlib import Path

TRACKER = Path(__file__).resolve().parent / "OPEN-ITEMS.md"
_OPT = re.compile(r";\s*(?=[A-Z]\)\s)")


def _cells(line: str) -> list[str]:
    return [c.strip().strip("*`") for c in line.strip().strip("|").split("|")]


def open_questions(path: Path = TRACKER) -> list[dict]:
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    qs: list[dict] = []
    for i, ln in enumerate(lines):
        if not (ln.startswith("|") and [c.lower() for c in _cells(ln)[:3]] == ["id", "topic", "question"]):
            continue
        cols = [c.lower() for c in _cells(ln)]
        for row in lines[i + 2:]:
            if not row.startswith("|"):
                break
            c = dict(zip(cols, _cells(row) + [""] * len(cols)))
            if not c.get("id") or not c.get("question"):
                continue
            rec = set(re.findall(r"\b([A-Z])\b", c.get("recommended", "")))
            opts = []
            for part in _OPT.split(c.get("options", "")):
                m = re.match(r"([A-Z])\)\s*(.*)", part.strip())
                if m:
                    opts.append({"value": m.group(1), "label": m.group(2),
                                 "recommended": m.group(1) in rec})
            qs.append({"id": c["id"], "topic": c.get("topic", ""),
                       "text": c["question"], "options": opts})
        break
    return qs
