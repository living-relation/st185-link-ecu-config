#!/usr/bin/env python3
"""Contract checks for docs/build-research-hub.py. Does not write research-hub.html."""

from __future__ import annotations

import csv
import json
import re
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load_hub():
    return runpy.run_path(str(DOCS / "build-research-hub.py"))


def parse_need_to_buy_counts(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    tables = []
    heading = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            heading = ln.lstrip("#").strip().lower()
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|\-]+$", lines[i + 1].strip()):
            i += 2
            rows = 0
            while i < len(lines) and lines[i].startswith("|"):
                rows += 1
                i += 1
            tables.append((heading, rows))
            continue
        i += 1
    buy = next((n for title, n in tables if "order these" in title or "short" in title), 0)
    covered = next((n for title, n in tables if "covered by stock" in title), 0)
    return buy, covered


def main() -> int:
    hub = load_hub()
    assert hub["first_sentence"]("One sentence. Two sentences.") == "One sentence."
    assert hub["first_sentence"]("") == ""

    data = hub["build"]()
    hub["require_parts_tables"](data)
    stats = data["parts"]["stats"]
    buy_md, covered_md = parse_need_to_buy_counts(DOCS / "harness" / "NEED-TO-BUY.md")
    onhand = list(csv.DictReader((DOCS / "sourcing" / "te-on-hand-bom.csv").read_text(encoding="utf-8-sig").splitlines()))
    build_rows = list(csv.DictReader((DOCS / "harness" / "HARNESS-BUILD-LIST.csv").read_text(encoding="utf-8-sig").splitlines()))

    assert stats["buy_lines"] == buy_md, (stats["buy_lines"], buy_md)
    assert stats["covered_lines"] == covered_md, (stats["covered_lines"], covered_md)
    assert stats["onhand_skus"] == len(onhand), (stats["onhand_skus"], len(onhand))
    assert stats["wire_count"] == len(build_rows), (stats["wire_count"], len(build_rows))
    assert all("caption" in t for t in data["topics"])

    html = hub["render"](data)
    assert "id=\"overview\"" in html
    assert "id=\"tiles\"" in html
    assert "data-filter-item" in html
    assert "function applyFilters" in html
    assert 'type="button" id="t-deliverable"' in html
    assert 'id="t-theme"' in html
    assert html.index('id="overview"') < html.index('id="out"')
    assert html.index('id="tiles"') < html.index('<main id="out">')
    assert 'aria-pressed="true">Deliverables' in html
    assert 'aria-pressed="true">Research' in html
    assert 'aria-pressed="true">Working files' in html
    toggle = html[html.index('class="toggle"'):html.index("filter-status")]
    assert "t-theme" not in toggle

    start = html.index("const DATA = ") + len("const DATA = ")
    embedded, _ = json.JSONDecoder().raw_decode(html[start:])
    assert embedded["parts"]["stats"]["buy_lines"] == stats["buy_lines"]
    assert "function applyFilters" in html
    assert "function render(" not in html
    assert re.search(r'setAttribute\("aria-pressed".*?applyFilters\(\)', html, re.S)

    print(
        "ok",
        len(data["topics"]),
        "topics",
        stats["buy_lines"],
        "buy",
        stats["onhand_skus"],
        "on-hand",
        stats["wire_count"],
        "wires",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
