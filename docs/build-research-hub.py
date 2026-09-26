#!/usr/bin/env python3
"""Generate docs/research-hub.html - a single navigable index of the repo's research.

Run from anywhere:  python docs/build-research-hub.py
Output is self-contained and opens from file:// with no server.

Do not commit the generated HTML — the "Regenerate research hub" Action owns it.
"""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import md5
from pathlib import Path
import subprocess

DOCS = Path(__file__).resolve().parent
REPO = DOCS.parent
OUT = DOCS / "research-hub.html"

# Topic order and framing. Directories not listed here are still picked up,
# appended in sorted order with a generic blurb.
TOPICS: list[dict] = [
    {
        "dir": "intercooler-turbo-study",
        "title": "Intercooler, Turbo & Charge Piping",
        "blurb": "Cold-side hardware study: core selection, turbo/redline choice, "
                 "manifold pairing, ducting, and charge-pipe sizing. Mechanical/thermal "
                 "scope, separate from the CAN/ECU config.",
    },
    {
        "dir": "5sgte-project-data",
        "title": "5S-GTE Build Data",
        "blurb": "Turbo-selection research and head airflow studies for the 5S-GTE hybrid "
                 "build. ECU wiring docs that were also in this tree have been retired to "
                 "archive/5sgte-project-data/ -- see archive/README.md for why.",
    },
    {
        "dir": "harness",
        "title": "Harness & Wiring",
        "blurb": "Current looms live under rebuild/ (A/B ECU+engine, CAN, EngineRoom-C, "
                 "ClusterLED, WheelSpeed, AntiTheft). Buy list and per-wire build sheet "
                 "are generated — do not hand-edit them.",
    },
    {
        "dir": "sourcing",
        "title": "On-hand parts",
        "blurb": "What is already owned. te-on-hand-bom.csv is the electrical stock list. "
                 "qty_ordered is an order upper bound, not a live shelf count. Check here "
                 "before speccing a new connector family.",
    },
    {
        "dir": "enclosures",
        "title": "Enclosure BOMs",
        "blurb": "CSB3 and VR-conditioner box buy lists. DigiKey PNs and STEP links live "
                 "in the CSVs — edit those, not a pretty table.",
    },
    {
        "dir": "electrical",
        "title": "Engine-room power redistribution",
        "blurb": "OEM kick-panel / J/B2 splice table and factory EWD snips for the "
                 "trunk-battery / glove-box PDB move. Partial engine-room C is in docs/harness/.",
    },
    {
        "dir": "devices",
        "title": "Sensors & Actuators",
        "blurb": "Per-device reference: part numbers, pinouts, calibrations and drive "
                 "types for every sensor and actuator on the car, plus the VR wheel-speed "
                 "conditioner. Pin assignments themselves live in XTREMEX-IO-TABLE.html.",
    },
    {
        "dir": "body",
        "title": "Body & packaging",
        "blurb": "Factory body-repair and KBA dimension snips used for routing and stack fit.",
    },
    {
        "dir": "vendor",
        "title": "Vendor Documentation",
        "blurb": "Official Link G4X / XtremeX manuals and spec sheets, plus rendered QSG "
                 "pages. These outrank every derived doc in this repo -- when a Link "
                 "document disagrees with ours, the Link document wins.",
    },
]

ROOT_NOTES = [
    "RECONCILIATION-RULES.md",
    "POWER-AND-COMMS-ARCHITECTURE.md",
    "HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md",
]

# Files matching these are working artifacts, not things you read.
SUPPORTING_SUFFIXES = {".py", ".js", ".json", ".csv", ".css", ".txt"}
ASSET_SUFFIXES = {".png", ".svg", ".webp", ".jpg", ".jpeg", ".pdf", ".ico"}
SKIP_NAMES = {"package-lock.json", "package.json"}
SKIP_PATTERNS = [re.compile(r"\.bak\.html$"), re.compile(r"^__pycache__$")]

# A readable file sitting directly in a topic folder is a deliverable; anything
# deeper (research/, data/) is the working trail behind it. These two lists
# override that inference where the layout lies.
FORCE_RESEARCH: set[str] = set()
FORCE_DELIVERABLE: set[str] = {
    "docs/sourcing/README.md",
    "docs/enclosures/README.md",
}

# Card-level markdown tables (sensor pins, plumbing BOM, splice tables).
# Full buy / on-hand / enclosure tables live in DATA.parts instead.
DOC_TABLE_MAX = 3
DOC_TABLE_ROWS = 24
SKIP_DOC_TABLES = {
    "docs/harness/NEED-TO-BUY.md",
}


@dataclass
class Doc:
    path: Path
    rel: str
    kind: str              # "deliverable" | "research" | "support" | "asset"
    title: str
    summary: str = ""
    sections: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    size: int = 0
    modified: str = ""
    digest: str = ""


def git_date(rel: str) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel],
            cwd=REPO, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def parse_md_tables(text: str) -> list[dict]:
    """Pull GitHub-style pipe tables, tagged with the nearest heading."""
    tables: list[dict] = []
    heading = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            heading = ln.lstrip("#").strip()
        if (
            ln.startswith("|")
            and i + 1 < len(lines)
            and re.match(r"^\|[\s:|\-]+$", lines[i + 1].strip())
        ):
            cols = [c.strip().strip("*`") for c in ln.strip().strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip().strip("*`") for c in lines[i].strip().strip("|").split("|")]
                while len(cells) < len(cols):
                    cells.append("")
                rows.append(cells[:len(cols)])
                i += 1
            if cols and rows:
                tables.append({"title": heading, "columns": cols, "rows": rows})
            continue
        i += 1
    return tables


def read_html(p: Path) -> tuple[str, str, list, list]:
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    title = strip_tags(m.group(1)) if m else p.stem
    secs = []
    anchors = [(m.start(), m.group(1))
               for m in re.finditer(r'<section[^>]*\bid="([^"]+)"', text, re.I)]
    for hm in re.finditer(r"<h2[^>]*>(.*?)</h2>", text, re.S | re.I):
        inner = hm.group(1)
        num = re.search(r'class="num"[^>]*>(.*?)</span>', inner, re.S | re.I)
        label = strip_tags(re.sub(r'<span class="num".*?</span>', "", inner, flags=re.S | re.I))
        if not label:
            continue
        prior = [a for pos, a in anchors if pos < hm.start()]
        secs.append({
            "label": f"{strip_tags(num.group(1))} {label}".strip() if num else label,
            "id": prior[-1] if prior else "",
        })
    pm = re.search(r"<p[^>]*>(.*?)</p>", text, re.S | re.I)
    summary = strip_tags(pm.group(1))[:280] if pm else ""
    return title, summary, secs, []


def read_md(p: Path) -> tuple[str, str, list, list]:
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    title, summary, secs = p.stem, "", []
    body_start = 0
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            title = ln[2:].strip()
            body_start = i + 1
            break
    para: list[str] = []
    for ln in lines[body_start:]:
        s = ln.strip()
        if not s:
            if para:
                break
            continue
        if s.startswith(("#", "|", ">", "-", "*", "```")):
            if para:
                break
            continue
        para.append(s)
    summary = " ".join(para)[:280]
    for ln in lines:
        if ln.startswith("## "):
            secs.append({"label": ln[3:].strip(), "id": ""})
    tables = []
    rel = p.relative_to(REPO).as_posix()
    if rel not in SKIP_DOC_TABLES:
        for raw in parse_md_tables(text)[:DOC_TABLE_MAX]:
            rows = raw["rows"][:DOC_TABLE_ROWS]
            tables.append({
                "title": raw["title"],
                "columns": [{"key": f"c{i}", "label": c} for i, c in enumerate(raw["columns"])],
                "rows": [
                    {f"c{i}": cell for i, cell in enumerate(row)}
                    for row in rows
                ],
                "truncated": len(raw["rows"]) > DOC_TABLE_ROWS,
                "source": rel,
            })
    return title, summary, secs, tables


def classify(p: Path, topic_dir: Path, rel: str) -> str:
    if p.suffix.lower() in ASSET_SUFFIXES:
        return "asset"
    if p.suffix.lower() in SUPPORTING_SUFFIXES:
        return "support"
    if rel in FORCE_DELIVERABLE:
        return "deliverable"
    if rel in FORCE_RESEARCH:
        return "research"
    return "deliverable" if p.parent == topic_dir else "research"


def collect(topic_dir: Path) -> list[Doc]:
    docs: list[Doc] = []
    for p in sorted(topic_dir.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not p.is_file():
            continue
        if p.name in SKIP_NAMES:
            continue
        if any(pat.search(p.name) or pat.search(p.parent.name) for pat in SKIP_PATTERNS):
            continue
        rel = p.relative_to(REPO).as_posix()
        kind = classify(p, topic_dir, rel)
        title, summary, secs, tables = p.stem, "", [], []
        if kind in ("deliverable", "research"):
            try:
                if p.suffix.lower() in {".html", ".htm"}:
                    title, summary, secs, tables = read_html(p)
                elif p.suffix.lower() == ".md":
                    title, summary, secs, tables = read_md(p)
            except Exception:
                pass
        stat = p.stat()
        docs.append(Doc(
            path=p, rel=rel, kind=kind, title=title, summary=summary,
            sections=secs, tables=tables, size=stat.st_size,
            modified=git_date(rel) or datetime.fromtimestamp(
                stat.st_mtime, timezone.utc).strftime("%Y-%m-%d"),
            digest=md5(p.read_bytes()).hexdigest()
            if kind in ("deliverable", "research") else "",
        ))
    return docs


def collect_root_notes() -> list[Doc]:
    docs = []
    for name in ROOT_NOTES:
        p = DOCS / name
        if not p.is_file():
            continue
        rel = p.relative_to(REPO).as_posix()
        title, summary, secs, tables = read_md(p)
        stat = p.stat()
        docs.append(Doc(
            path=p, rel=rel, kind="deliverable", title=title, summary=summary,
            sections=secs, tables=tables, size=stat.st_size,
            modified=git_date(rel) or datetime.fromtimestamp(
                stat.st_mtime, timezone.utc).strftime("%Y-%m-%d"),
            digest=md5(p.read_bytes()).hexdigest(),
        ))
    return docs


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} MB"


def _csv_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def _intish(value) -> int:
    s = str(value or "").replace(",", "").replace("*", "").strip()
    try:
        return int(float(s))
    except ValueError:
        return 0


def _table(tid: str, title: str, source: str, columns: list[dict],
           rows: list[dict], note: str = "") -> dict:
    return {
        "id": tid, "title": title, "source": source, "note": note,
        "columns": columns, "rows": rows,
    }


def load_buy_tables() -> dict[str, dict]:
    path = DOCS / "harness" / "NEED-TO-BUY.md"
    if not path.is_file():
        return {}
    raw_list = parse_md_tables(path.read_text(encoding="utf-8"))

    def _by_title(*needles: str) -> dict | None:
        for t in raw_list:
            title = t["title"].lower()
            if any(n.lower() in title for n in needles):
                return t
        return None

    out: dict[str, dict] = {}

    buy = _by_title("order these", "short")
    if buy:
        rows = []
        for cells in buy["rows"]:
            pad = cells + [""] * 6
            need, have, buy_qty = _intish(pad[3]), _intish(pad[4]), _intish(pad[5])
            rows.append({
                "pn": pad[0], "mfr": pad[1], "desc": pad[2],
                "need": need, "have": have, "buy": buy_qty, "status": "buy",
            })
        out["buy"] = _table(
            "buy", "Harness — order these", "docs/harness/NEED-TO-BUY.md",
            [
                {"key": "pn", "label": "Part number"},
                {"key": "mfr", "label": "Mfr"},
                {"key": "desc", "label": "Description"},
                {"key": "need", "label": "Need", "num": True},
                {"key": "have", "label": "Have", "num": True},
                {"key": "buy", "label": "Buy", "num": True},
            ],
            rows,
            "Generated by docs/harness/buylist.py from the rebuild/ looms. Do not hand-edit.",
        )

    covered = _by_title("covered by stock")
    if covered:
        rows = []
        for cells in covered["rows"]:
            pad = cells + [""] * 4
            need, have = _intish(pad[2]), _intish(pad[3])
            rows.append({
                "pn": pad[0], "desc": pad[1], "need": need, "have": have,
                "spare": max(0, have - need), "status": "covered",
            })
        out["covered"] = _table(
            "covered", "Harness — covered by stock", "docs/harness/NEED-TO-BUY.md",
            [
                {"key": "pn", "label": "Part number"},
                {"key": "desc", "label": "Description"},
                {"key": "need", "label": "Need", "num": True},
                {"key": "have", "label": "Have", "num": True},
                {"key": "spare", "label": "Spare", "num": True},
            ],
            rows,
            "Need is met by owned stock. Spare is have minus need.",
        )

    skip = _by_title("not purchased")
    if skip:
        rows = []
        for cells in skip["rows"]:
            pad = cells + [""] * 3
            rows.append({
                "pn": pad[0], "desc": pad[1], "qty": _intish(pad[2]),
                "status": "skip",
            })
        out["not_purchased"] = _table(
            "not_purchased", "Not purchased — OEM or kit-supplied",
            "docs/harness/NEED-TO-BUY.md",
            [
                {"key": "pn", "label": "Modelled as"},
                {"key": "desc", "label": "What it really is"},
                {"key": "qty", "label": "Qty", "num": True},
            ],
            rows,
        )
    return out


def load_onhand_table() -> dict | None:
    path = DOCS / "sourcing" / "te-on-hand-bom.csv"
    if not path.is_file():
        return None
    rows = []
    for r in _csv_rows(path):
        rows.append({
            "pn": (r.get("pn") or "").strip(),
            "desc": (r.get("description") or "").strip(),
            "qty": _intish(r.get("qty_ordered")),
            "family": (r.get("family") or "").strip(),
            "notes": (r.get("notes") or "").strip(),
            "status": "owned",
        })
    return _table(
        "onhand", "On-hand electrical BOM", "docs/sourcing/te-on-hand-bom.csv",
        [
            {"key": "pn", "label": "Part number"},
            {"key": "desc", "label": "Description"},
            {"key": "qty", "label": "Qty ordered", "num": True},
            {"key": "family", "label": "Family"},
            {"key": "notes", "label": "Notes"},
        ],
        rows,
        "qty_ordered is what was ordered, not a live shelf count. Confirm before a build.",
    )


def load_enclosure_tables() -> dict[str, dict]:
    out: dict[str, dict] = {}
    csb3 = DOCS / "enclosures" / "csb3-bom.csv"
    if csb3.is_file():
        rows = []
        for r in _csv_rows(csb3):
            rows.append({
                "item": r.get("item", ""),
                "role": r.get("role", ""),
                "mfr": r.get("mfr", ""),
                "pn": r.get("pn", ""),
                "qty": _intish(r.get("qty")),
                "stock": r.get("stock_note", ""),
                "buy_url": r.get("buy_url", ""),
                "notes": r.get("notes", ""),
                "status": "buy",
            })
        out["csb3"] = _table(
            "csb3", "CSB3 enclosure BOM", "docs/enclosures/csb3-bom.csv",
            [
                {"key": "item", "label": "Item"},
                {"key": "role", "label": "Role"},
                {"key": "mfr", "label": "Mfr"},
                {"key": "pn", "label": "PN"},
                {"key": "qty", "label": "Qty", "num": True},
                {"key": "stock", "label": "Stock note"},
                {"key": "buy_url", "label": "Buy"},
                {"key": "notes", "label": "Notes"},
            ],
            rows,
        )
    vr = DOCS / "enclosures" / "vr-conditioner-bom.csv"
    if vr.is_file():
        rows = []
        for r in _csv_rows(vr):
            rows.append({
                "item": r.get("item", ""),
                "role": r.get("role", ""),
                "mfr": r.get("mfr", ""),
                "pn": r.get("pn", ""),
                "qty_box": _intish(r.get("qty_per_box")),
                "qty_car": _intish(r.get("qty_car")),
                "stock": r.get("stock_note", ""),
                "buy_url": r.get("buy_url", ""),
                "notes": r.get("notes", ""),
                "status": "buy",
            })
        out["vr"] = _table(
            "vr", "VR conditioner enclosure BOM (×2 boxes)",
            "docs/enclosures/vr-conditioner-bom.csv",
            [
                {"key": "item", "label": "Item"},
                {"key": "role", "label": "Role"},
                {"key": "mfr", "label": "Mfr"},
                {"key": "pn", "label": "PN"},
                {"key": "qty_box", "label": "Per box", "num": True},
                {"key": "qty_car", "label": "Per car", "num": True},
                {"key": "stock", "label": "Stock note"},
                {"key": "buy_url", "label": "Buy"},
                {"key": "notes", "label": "Notes"},
            ],
            rows,
        )
    return out


def load_buildlist_summary() -> dict | None:
    path = DOCS / "harness" / "HARNESS-BUILD-LIST.csv"
    if not path.is_file():
        return None
    counts: Counter[str] = Counter()
    for r in _csv_rows(path):
        counts[r.get("File") or "—"] += 1
    rows = [{"loom": k, "wires": n, "status": "info"} for k, n in sorted(counts.items())]
    rows.append({"loom": "Total", "wires": sum(counts.values()), "status": "info"})
    return _table(
        "buildlist", "Per-wire build list — wires by loom",
        "docs/harness/HARNESS-BUILD-LIST.csv",
        [
            {"key": "loom", "label": "Loom"},
            {"key": "wires", "label": "Wires", "num": True},
        ],
        rows,
        "Generated by docs/harness/buildlist.py. Open the CSV for the full From/To sheet.",
    )


def load_parts() -> dict:
    tables: dict[str, dict] = {}
    tables.update(load_buy_tables())
    onhand = load_onhand_table()
    if onhand:
        tables["onhand"] = onhand
    tables.update(load_enclosure_tables())
    buildlist = load_buildlist_summary()
    if buildlist:
        tables["buildlist"] = buildlist

    buy_rows = tables.get("buy", {}).get("rows", [])
    covered_rows = tables.get("covered", {}).get("rows", [])
    onhand_rows = tables.get("onhand", {}).get("rows", [])
    stats = {
        "buy_lines": len(buy_rows),
        "buy_qty": sum(_intish(r.get("buy")) for r in buy_rows),
        "covered_lines": len(covered_rows),
        "onhand_skus": len(onhand_rows),
        "onhand_qty": sum(_intish(r.get("qty")) for r in onhand_rows),
        "enclosure_lines": len(tables.get("csb3", {}).get("rows", []))
                          + len(tables.get("vr", {}).get("rows", [])),
        "wire_count": (tables.get("buildlist", {}).get("rows") or [{}])[-1].get("wires", 0)
                      if "buildlist" in tables else 0,
    }
    topic_tables = {
        "harness": [k for k in ("buy", "covered", "buildlist") if k in tables],
        "sourcing": [k for k in ("onhand",) if k in tables],
        "enclosures": [k for k in ("csb3", "vr") if k in tables],
    }
    return {"stats": stats, "tables": tables, "topic_tables": topic_tables}


def _topic_rows(docs: list[Doc]) -> list[dict]:
    canonical: dict[str, str] = {}
    for d in sorted(docs, key=lambda x: x.rel.count("/")):
        if d.digest and d.digest not in canonical:
            canonical[d.digest] = d.rel
    rows = []
    for d in docs:
        row = d.__dict__ | {"path": None}
        row["mirror_of"] = (canonical.get(d.digest)
                            if d.digest and canonical.get(d.digest) != d.rel else None)
        rows.append(row)
    return rows


def build() -> dict:
    topics = []
    seen_dirs = {t["dir"] for t in TOPICS}
    extra = sorted(
        (d.name for d in DOCS.iterdir()
         if d.is_dir() and d.name not in seen_dirs
         and not d.name.startswith(".") and d.name != "__pycache__"),
        key=str.lower,
    )
    spec = TOPICS + [{"dir": d, "title": d.replace("-", " ").title(), "blurb": ""} for d in extra]

    digests: dict[str, list[str]] = {}
    for t in spec:
        tdir = DOCS / t["dir"]
        if not tdir.is_dir():
            continue
        docs = collect(tdir)
        for d in docs:
            if d.digest:
                digests.setdefault(d.digest, []).append(d.rel)
        rows = _topic_rows(docs)
        topics.append({
            "dir": t["dir"], "title": t["title"], "blurb": t["blurb"], "docs": rows,
            "counts": {
                k: sum(1 for r in rows if r["kind"] == k and not r["mirror_of"])
                for k in ("deliverable", "research", "support", "asset")
            },
        })

    notes = collect_root_notes()
    if notes:
        for d in notes:
            if d.digest:
                digests.setdefault(d.digest, []).append(d.rel)
        rows = _topic_rows(notes)
        topics.append({
            "dir": "notes",
            "title": "Project rules & architecture",
            "blurb": "Living repo-root notes. Dated VERIFY / AUDIT / FACES sheets stay "
                     "frozen records and are not indexed here.",
            "docs": rows,
            "counts": {
                k: sum(1 for r in rows if r["kind"] == k)
                for k in ("deliverable", "research", "support", "asset")
            },
        })

    dupes = {k: v for k, v in digests.items() if len(v) > 1}
    return {"topics": topics, "dupes": dupes, "parts": load_parts()}


HUB_CSS = """
  :root {
    --bg:#f7f7f5; --panel:#fff; --ink:#16171a; --muted:#6a6d75; --line:#e2e2df;
    --accent:#b4451f; --accent-soft:#fbeee8; --chip:#eeeeeb;
    --ok:#2f6f4e; --ok-soft:#e6f4ec; --warn:#8a5a12; --warn-soft:#fff4dc;
    --info:#355a8a; --info-soft:#e8f0fa;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg:#131417; --panel:#1b1c20; --ink:#e9e9ea; --muted:#9a9da5; --line:#2c2e34;
      --accent:#e8825a; --accent-soft:#2a1c16; --chip:#26282e;
      --ok:#7dcea0; --ok-soft:#1c2a22; --warn:#e8c07a; --warn-soft:#2a2316;
      --info:#8bb4e0; --info-soft:#1b2430;
    }
  }
  :root[data-theme="dark"] {
    --bg:#131417; --panel:#1b1c20; --ink:#e9e9ea; --muted:#9a9da5; --line:#2c2e34;
    --accent:#e8825a; --accent-soft:#2a1c16; --chip:#26282e;
    --ok:#7dcea0; --ok-soft:#1c2a22; --warn:#e8c07a; --warn-soft:#2a2316;
    --info:#8bb4e0; --info-soft:#1b2430;
  }
  * { box-sizing:border-box; }
  body { background:var(--bg); color:var(--ink); margin:0;
    font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:1180px; margin:0 auto; padding:28px 20px 80px; }
  header h1 { font-size:26px; margin:0 0 6px; letter-spacing:-.02em; }
  .sub { color:var(--muted); font-size:14px; margin:0 0 18px; }
  .bar { display:flex; gap:10px; flex-wrap:wrap; align-items:center;
    position:sticky; top:0; background:var(--bg); padding:12px 0; z-index:5;
    border-bottom:1px solid var(--line); margin-bottom:16px; }
  #q { flex:1; min-width:220px; padding:9px 12px; border:1px solid var(--line);
    border-radius:8px; background:var(--panel); color:var(--ink); font-size:14px; }
  #q:focus { outline:2px solid var(--accent); outline-offset:-1px; }
  .toggle { display:flex; gap:4px; flex-wrap:wrap; }
  .toggle button { padding:8px 11px; border:1px solid var(--line); background:var(--panel);
    color:var(--muted); border-radius:7px; cursor:pointer; font-size:13px; }
  .toggle button[aria-pressed="true"] { background:var(--accent-soft);
    border-color:var(--accent); color:var(--accent); font-weight:600; }
  .topic-nav { display:flex; gap:6px; flex-wrap:wrap; margin:0 0 18px; }
  .topic-nav a { font-size:12.5px; color:var(--muted); text-decoration:none;
    border:1px solid var(--line); background:var(--panel); padding:5px 9px; border-radius:999px; }
  .topic-nav a:hover, .topic-nav a:focus { color:var(--accent); border-color:var(--accent); }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
    gap:8px; margin:0 0 14px; }
  .stat { background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:10px 12px; }
  .stat b { display:block; font-size:22px; letter-spacing:-.03em; line-height:1.1; }
  .stat span { font-size:11.5px; color:var(--muted); }
  .bars { display:flex; height:10px; border-radius:99px; overflow:hidden;
    background:var(--chip); margin:0 0 18px; }
  .bars i { display:block; height:100%; }
  .bars .b-buy { background:var(--accent); }
  .bars .b-ok { background:var(--ok); }
  .bars .b-own { background:var(--info); }
  .board { background:var(--panel); border:1px solid var(--line); border-radius:12px;
    padding:14px 16px 16px; margin:0 0 28px; }
  .board h2 { font-size:18px; margin:0 0 4px; }
  .board .blurb { margin-bottom:12px; }
  .tabs { display:flex; gap:4px; flex-wrap:wrap; margin:0 0 12px; }
  .tabs button { padding:7px 11px; border:1px solid var(--line); background:var(--bg);
    color:var(--muted); border-radius:7px; cursor:pointer; font-size:13px; }
  .tabs button[aria-selected="true"] { background:var(--accent-soft); border-color:var(--accent);
    color:var(--accent); font-weight:600; }
  .twrap { overflow:auto; max-height:420px; border:1px solid var(--line); border-radius:8px; }
  table.data { width:100%; border-collapse:collapse; font-size:12.5px; }
  table.data th, table.data td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line);
    vertical-align:top; }
  table.data th { position:sticky; top:0; background:var(--panel); cursor:pointer;
    white-space:nowrap; font-size:11.5px; color:var(--muted); }
  table.data th:hover { color:var(--accent); }
  table.data tr:hover td { background:var(--chip); }
  table.data a { color:var(--accent); }
  .num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
  .pill { display:inline-block; font-size:10.5px; padding:1px 6px; border-radius:99px;
    background:var(--chip); color:var(--muted); }
  .pill.buy { background:var(--accent-soft); color:var(--accent); }
  .pill.covered, .pill.owned { background:var(--ok-soft); color:var(--ok); }
  .pill.skip { background:var(--warn-soft); color:var(--warn); }
  .pill.info { background:var(--info-soft); color:var(--info); }
  .tmeta { display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;
    font-size:12px; color:var(--muted); margin:0 0 8px; }
  .tmeta input { padding:5px 8px; border:1px solid var(--line); border-radius:6px;
    background:var(--bg); color:var(--ink); font-size:12.5px; min-width:180px; }
  .topic { margin:0 0 30px; }
  .topic > h2 { font-size:19px; margin:0 0 4px; letter-spacing:-.01em; }
  .blurb { color:var(--muted); font-size:13.5px; margin:0 0 12px; max-width:78ch; }
  .counts { font-size:12px; color:var(--muted); margin-bottom:12px; }
  .counts b { color:var(--ink); font-weight:600; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:14px 16px; margin-bottom:9px; }
  .card h3 { margin:0 0 4px; font-size:15px; font-weight:600; }
  .card h3 a { color:var(--ink); text-decoration:none; }
  .card h3 a:hover { color:var(--accent); text-decoration:underline; }
  .meta { font-size:11.5px; color:var(--muted); display:flex; gap:9px;
    flex-wrap:wrap; margin-bottom:6px; align-items:center; }
  .chip { background:var(--chip); padding:1.5px 7px; border-radius:20px;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; }
  .summary { font-size:13.5px; color:var(--muted); margin:0; max-width:78ch; }
  details.secs { margin-top:9px; }
  details.secs summary { cursor:pointer; font-size:12.5px; color:var(--accent);
    font-weight:600; user-select:none; }
  .seclist { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
    gap:2px 14px; margin:9px 0 0; padding:0; list-style:none; }
  .seclist a { font-size:12.5px; color:var(--muted); text-decoration:none;
    display:block; padding:2.5px 0; border-bottom:1px solid transparent; }
  .seclist a:hover { color:var(--accent); border-bottom-color:var(--line); }
  .support-wrap summary { cursor:pointer; font-size:13px; color:var(--muted); }
  .support-list { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
    gap:1px 14px; margin:10px 0 0; padding:0; list-style:none; }
  .support-list a { font-size:12px; color:var(--muted); text-decoration:none;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  .support-list a:hover { color:var(--accent); }
  .warn { background:var(--accent-soft); border:1px solid var(--accent);
    border-radius:9px; padding:12px 15px; margin-bottom:24px; font-size:13px; }
  .warn h3 { margin:0 0 6px; font-size:13.5px; color:var(--accent); }
  .warn ul { margin:0; padding-left:18px; }
  .warn code { font-size:11.5px; }
  footer { margin-top:44px; padding-top:16px; border-top:1px solid var(--line);
    color:var(--muted); font-size:12px; }
  .hidden { display:none !important; }
  code { font-size:12px; }
"""

HUB_JS = r"""
const esc = s => String(s ?? "").replace(/[&<>"]/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

const isUrl = s => /^https?:\/\//i.test(String(s || ""));
const on = id => document.getElementById(id).getAttribute("aria-pressed") === "true";

const tableState = {};
let activePartsTab = "buy";

function hayOf(obj) {
  return Object.values(obj || {}).join(" ").toLowerCase();
}

function cellHtml(col, row) {
  const v = row[col.key];
  if (v == null || v === "") return "";
  if (col.key === "buy_url" && isUrl(v)) {
    return `<a href="${esc(v)}" target="_blank" rel="noopener">open</a>`;
  }
  if (isUrl(v)) return `<a href="${esc(v)}" target="_blank" rel="noopener">${esc(v)}</a>`;
  if (col.key === "status") return `<span class="pill ${esc(v)}">${esc(v)}</span>`;
  return esc(v);
}

function renderOneTable(spec, inst) {
  if (!spec) return "";
  const key = inst || spec.id;
  const st = tableState[key] || (tableState[key] = {q: "", sort: "", dir: 1});
  const q = (st.q || "").toLowerCase();
  let rows = spec.rows.slice();
  if (q) rows = rows.filter(r => hayOf(r).includes(q));
  if (st.sort) {
    const col = spec.columns.find(c => c.key === st.sort);
    rows.sort((a, b) => {
      const av = a[st.sort], bv = b[st.sort];
      const cmp = col && col.num
        ? (Number(av) || 0) - (Number(bv) || 0)
        : String(av ?? "").localeCompare(String(bv ?? ""), undefined, {numeric: true});
      return cmp * st.dir;
    });
  }
  const heads = spec.columns.map(c => {
    const mark = st.sort === c.key ? (st.dir > 0 ? " ▲" : " ▼") : "";
    return `<th data-sort="${esc(c.key)}" class="${c.num ? "num" : ""}">${esc(c.label)}${mark}</th>`;
  }).join("");
  const body = rows.map(r => {
    const tds = spec.columns.map(c =>
      `<td class="${c.num ? "num" : ""}">${cellHtml(c, r)}</td>`).join("");
    return `<tr data-hay="${esc(hayOf(r))}">${tds}</tr>`;
  }).join("");
  return `
    <section class="tbl" data-tid="${esc(spec.id)}" data-inst="${esc(key)}"
             data-hay="${esc((spec.title + " " + spec.source).toLowerCase())}">
      <div class="tmeta">
        <div>
          <strong>${esc(spec.title)}</strong>
          <span class="chip">${esc(spec.source)}</span>
          <span>${rows.length} / ${spec.rows.length}</span>
        </div>
        <input class="tfilter" data-tid="${esc(spec.id)}" data-inst="${esc(key)}" type="search"
               placeholder="Filter this table…" value="${esc(st.q)}" autocomplete="off">
      </div>
      ${spec.note ? `<p class="blurb">${esc(spec.note)}</p>` : ""}
      <div class="twrap">
        <table class="data" data-tid="${esc(spec.id)}" data-inst="${esc(key)}">
          <thead><tr>${heads}</tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>
    </section>`;
}

function findSpec(id) {
  if (DATA.parts && DATA.parts.tables && DATA.parts.tables[id]) {
    return DATA.parts.tables[id];
  }
  for (const t of DATA.topics) {
    for (const d of t.docs) {
      for (let i = 0; i < (d.tables || []).length; i++) {
        if (`${d.rel}-${i}` === id) return {...d.tables[i], id};
      }
    }
  }
  return null;
}

function replaceTable(mount) {
  if (!mount || !mount.parentNode) return;
  const spec = findSpec(mount.dataset.tid);
  if (!spec) return;
  const inst = mount.dataset.inst || mount.dataset.tid;
  const filterEl = mount.querySelector(".tfilter");
  const focus = document.activeElement === filterEl;
  const start = focus ? filterEl.selectionStart : null;
  const wrap = document.createElement("div");
  wrap.innerHTML = renderOneTable(spec, inst).trim();
  const next = wrap.firstElementChild;
  mount.replaceWith(next);
  bindTables(next);
  if (focus) {
    const inp = next.querySelector(".tfilter");
    if (inp) { inp.focus(); if (start != null) inp.setSelectionRange(start, start); }
  }
}

function bindTables(root) {
  root.querySelectorAll(".tfilter").forEach(inp => {
    if (inp.dataset.bound) return;
    inp.dataset.bound = "1";
    inp.addEventListener("input", e => {
      const mount = e.currentTarget.closest(".tbl");
      const inst = e.currentTarget.dataset.inst || e.currentTarget.dataset.tid;
      tableState[inst] = tableState[inst] || {q: "", sort: "", dir: 1};
      tableState[inst].q = e.currentTarget.value;
      replaceTable(mount);
    });
  });
  root.querySelectorAll("th[data-sort]").forEach(th => {
    if (th.dataset.bound) return;
    th.dataset.bound = "1";
    th.addEventListener("click", e => {
      const mount = e.currentTarget.closest(".tbl");
      const inst = mount.dataset.inst || mount.dataset.tid;
      const key = e.currentTarget.dataset.sort;
      tableState[inst] = tableState[inst] || {q: "", sort: "", dir: 1};
      if (tableState[inst].sort === key) tableState[inst].dir *= -1;
      else { tableState[inst].sort = key; tableState[inst].dir = 1; }
      replaceTable(mount);
    });
  });
}

function docCard(d) {
  const secs = (d.sections || []).filter(s => s && s.label);
  const target = s => s.id
    ? `#${encodeURIComponent(s.id)}`
    : `#:~:text=${encodeURIComponent(s.label.replace(/^\d+\s+/, ""))}`;
  const tables = (d.tables || []).map((t, i) => {
    const spec = {...t, id: `${d.rel}-${i}`};
    return `<details class="secs" open><summary>${esc(t.title || "Table")}${
      t.truncated ? " (first rows)" : ""}</summary>${renderOneTable(spec, spec.id)}</details>`;
  }).join("");
  return `
  <article class="card" data-hay="${esc(
      (d.title + " " + d.rel + " " + secs.map(s => s.label).join(" ")
       + " " + (d.tables || []).map(t => t.title).join(" ")).toLowerCase())}">
    <h3><a href="../${esc(d.rel)}">${esc(d.title)}</a></h3>
    <div class="meta">
      <span class="chip">${esc(d.rel.replace(/^docs\//, ""))}</span>
      <span class="pill info">${esc(d.kind)}</span>
      <span>${esc(d.modified)}</span>
      <span>${esc(d.human_size)}</span>
      ${secs.length ? `<span>${secs.length} sections</span>` : ""}
      ${(d.tables || []).length ? `<span>${d.tables.length} tables</span>` : ""}
    </div>
    ${d.summary ? `<p class="summary">${esc(d.summary)}</p>` : ""}
    ${secs.length ? `<details class="secs"><summary>${secs.length} sections</summary>
      <ul class="seclist">${secs.map(s =>
        `<li><a href="../${esc(d.rel)}${target(s)}">${esc(s.label)}</a></li>`
      ).join("")}</ul></details>` : ""}
    ${tables}
  </article>`;
}

function partsHtml() {
  const P = DATA.parts || {};
  const S = P.stats || {};
  const tabs = [
    ["buy", "Buy list", P.tables.buy],
    ["onhand", "On hand", P.tables.onhand],
    ["covered", "Covered", P.tables.covered],
    ["enclosures", "Enclosure BOMs", null],
    ["skip", "Not purchased", P.tables.not_purchased],
  ].filter(t => t[2] || t[0] === "enclosures");
  const active = activePartsTab;
  const tabBtns = tabs.map(([id, label]) =>
    `<button type="button" data-tab="${id}" aria-selected="${id === active}">${label}</button>`
  ).join("");

  let body = "";
  if (active === "enclosures") {
    body = [P.tables.csb3, P.tables.vr].filter(Boolean)
      .map(t => renderOneTable(t, "board-" + t.id)).join("");
  } else if (P.tables[active]) {
    body = renderOneTable(P.tables[active], "board-" + active);
  }

  const buy = S.buy_lines || 0, cov = S.covered_lines || 0, own = S.onhand_skus || 0;
  const tot = buy + cov + own || 1;
  return `
    <section class="board" id="parts" data-hay="buy list on hand bom enclosure stock parts">
      <h2>Parts board</h2>
      <p class="blurb">Live tables from the CSV / generated buy-list sources of truth.
         Click a column to sort. Filter boxes search inside the open table.</p>
      <div class="stats">
        <div class="stat"><b>${S.buy_lines || 0}</b><span>buy lines · ${S.buy_qty || 0} pcs</span></div>
        <div class="stat"><b>${S.covered_lines || 0}</b><span>covered by stock</span></div>
        <div class="stat"><b>${S.onhand_skus || 0}</b><span>on-hand SKUs · ${S.onhand_qty || 0} ordered</span></div>
        <div class="stat"><b>${S.enclosure_lines || 0}</b><span>enclosure BOM lines</span></div>
        <div class="stat"><b>${S.wire_count || 0}</b><span>wires on the build list</span></div>
      </div>
      <div class="bars" title="buy / covered / on-hand SKUs">
        <i class="b-buy" style="width:${(buy / tot * 100).toFixed(1)}%"></i>
        <i class="b-ok" style="width:${(cov / tot * 100).toFixed(1)}%"></i>
        <i class="b-own" style="width:${(own / tot * 100).toFixed(1)}%"></i>
      </div>
      <div class="tabs">${tabBtns}</div>
      <div id="parts-body">${body}</div>
    </section>`;
}

function refreshParts() {
  const el = document.getElementById("parts-root");
  if (!el) return;
  el.innerHTML = partsHtml();
  el.querySelectorAll(".tabs button").forEach(b => {
    b.addEventListener("click", () => {
      el.querySelectorAll(".tabs button").forEach(x => x.setAttribute("aria-selected", "false"));
      b.setAttribute("aria-selected", "true");
      const tab = b.dataset.tab;
      activePartsTab = tab;
      const body = document.getElementById("parts-body");
      body.innerHTML = tab === "enclosures"
        ? [DATA.parts.tables.csb3, DATA.parts.tables.vr].filter(Boolean)
            .map(t => renderOneTable(t, "board-" + t.id)).join("")
        : renderOneTable(DATA.parts.tables[tab] || null, "board-" + tab);
      bindTables(body);
    });
  });
  bindTables(el);
}

function topicTables(dir) {
  const ids = (DATA.parts.topic_tables || {})[dir] || [];
  if (!ids.length) return "";
  return `<div class="topic-tables">${ids.map(id =>
    renderOneTable(DATA.parts.tables[id], `topic-${dir}-${id}`)).join("")}</div>`;
}

function renderNav() {
  document.getElementById("topic-nav").innerHTML = DATA.topics.map(t =>
    `<a href="#topic-${esc(t.dir)}">${esc(t.title)}</a>`
  ).join("") + `<a href="#parts">Parts board</a>`;
}

function render() {
  const show = {
    deliverable: on("t-deliverable"),
    research: on("t-research"),
    support: on("t-support"),
  };
  document.getElementById("out").innerHTML = DATA.topics.map(t => {
    const live = t.docs.filter(d => !d.mirror_of);
    const deliverables = live.filter(d => d.kind === "deliverable");
    const research = live.filter(d => d.kind === "research");
    const support = t.docs.filter(d => d.kind === "support" || d.kind === "asset");
    const mirrors = t.docs.filter(d => d.mirror_of);
    return `
    <section class="topic" id="topic-${esc(t.dir)}" data-topic="${esc(t.dir)}">
      <h2>${esc(t.title)}</h2>
      ${t.blurb ? `<p class="blurb">${esc(t.blurb)}</p>` : ""}
      <p class="counts"><b>${t.counts.deliverable}</b> deliverables &middot;
         <b>${t.counts.research}</b> research notes &middot;
         <b>${t.counts.support + t.counts.asset}</b> scripts &amp; assets${
         mirrors.length ? ` &middot; <b>${mirrors.length}</b> mirrored` : ""}</p>
      ${topicTables(t.dir)}
      ${show.deliverable ? deliverables.map(docCard).join("") : ""}
      ${show.research && research.length ? `
        <details class="support-wrap" open>
          <summary>${research.length} research notes</summary>
          <div>${research.map(docCard).join("")}</div>
        </details>` : ""}
      ${show.support && support.length ? `
        <details class="support-wrap" open>
          <summary>${support.length} working files</summary>
          <ul class="support-list">${support.map(d =>
            `<li data-hay="${esc(d.rel.toLowerCase())}"><a href="../${esc(d.rel)}">${
              esc(d.rel.split("/").slice(2).join("/") || d.rel)}</a></li>`
          ).join("")}</ul>
        </details>` : ""}
    </section>`;
  }).join("");
  document.querySelectorAll(".topic-tables").forEach(bindTables);
  document.querySelectorAll(".card .tbl").forEach(el => bindTables(el.parentElement));
  filter();
}

function filter() {
  const q = document.getElementById("q").value.trim().toLowerCase();
  document.querySelectorAll("[data-hay]").forEach(el => {
    el.classList.toggle("hidden", q && !el.dataset.hay.includes(q));
  });
  if (q) {
    document.querySelectorAll("[data-hay]:not(.hidden)").forEach(el => {
      let p = el.parentElement;
      while (p) {
        if (p.hasAttribute && p.hasAttribute("data-hay")) p.classList.remove("hidden");
        p = p.parentElement;
      }
    });
  }
  document.querySelectorAll(".topic").forEach(sec => {
    const anyVisible = sec.querySelector("[data-hay]:not(.hidden)");
    sec.classList.toggle("hidden", !!q && !anyVisible);
  });
}

function renderDupes() {
  const entries = Object.entries(DATA.dupes || {});
  if (!entries.length) return;
  document.getElementById("dupes").innerHTML = `
    <div class="warn">
      <h3>${entries.length} document${entries.length > 1 ? "s exist" : " exists"} in more than one place</h3>
      <ul>${entries.map(([, paths]) =>
        `<li>${paths.map(p => `<code>${esc(p)}</code>`).join(" = ")}</li>`).join("")}</ul>
    </div>`;
}

function applyTheme(theme) {
  if (theme) document.documentElement.setAttribute("data-theme", theme);
  else document.documentElement.removeAttribute("data-theme");
  const cur = document.documentElement.getAttribute("data-theme") || "auto";
  document.getElementById("t-theme").textContent = cur === "dark" ? "Light" : cur === "light" ? "Auto" : "Dark";
}

document.getElementById("q").addEventListener("input", filter);
["t-deliverable", "t-research", "t-support"].forEach(id => {
  document.getElementById(id).addEventListener("click", e => {
    const b = e.currentTarget;
    b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "true" ? "false" : "true");
    render();
  });
});
function readTheme() {
  try { return localStorage.getItem("hub-theme") || ""; }
  catch (err) { return ""; }
}
function writeTheme(theme) {
  try {
    if (theme) localStorage.setItem("hub-theme", theme);
    else localStorage.removeItem("hub-theme");
  } catch (err) { /* file:// or privacy mode */ }
}

document.getElementById("t-theme").addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : cur === "light" ? "" : "dark";
  writeTheme(next);
  applyTheme(next);
});

applyTheme(readTheme());
renderNav();
renderDupes();
refreshParts();
render();
"""


def embed_js_json(data: dict) -> str:
    """JSON for an inline <script>. Escape '<' so a CSV cell cannot close the tag."""
    return json.dumps(data, default=str, sort_keys=True).replace("<", "\\u003c")


def parse_embedded_data(html_text: str) -> dict:
    marker = "const DATA = "
    start = html_text.index(marker) + len(marker)
    data, _ = json.JSONDecoder().raw_decode(html_text[start:])
    return data


def require_parts_tables(data: dict) -> None:
    tables = (data.get("parts") or {}).get("tables") or {}
    if "buy" not in tables:
        raise SystemExit("research hub is missing the NEED-TO-BUY table")


def render(data: dict) -> str:
    dates = [d["modified"] for t in data["topics"] for d in t["docs"] if d.get("modified")]
    latest = max(dates) if dates else "unknown"
    payload = embed_js_json(data)
    total_read = sum(t["counts"]["deliverable"] + t["counts"]["research"]
                     for t in data["topics"])
    total_all = sum(len(t["docs"]) for t in data["topics"])
    stats = data.get("parts", {}).get("stats", {})

    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>ST185 Research Hub</title>\n<style>\n"
        + HUB_CSS
        + "</style>\n</head>\n<body>\n<div class=\"wrap\">\n<header>\n"
        f"<h1>ST185 Research Hub</h1>\n"
        f"<p class=\"sub\">Sources last updated {html.escape(latest)} &middot; "
        f"{total_read} readable documents of {total_all} files across "
        f"{len(data['topics'])} topics &middot; "
        f"{stats.get('buy_lines', 0)} buy lines / "
        f"{stats.get('onhand_skus', 0)} on-hand SKUs &middot; regenerate with "
        f"<code>python docs/build-research-hub.py</code></p>\n"
        "</header>\n\n"
        "<div class=\"bar\">\n"
        "  <input id=\"q\" type=\"search\" placeholder=\"Filter titles, sections, tables, or filenames&hellip;\"\n"
        "         autocomplete=\"off\">\n"
        "  <div class=\"toggle\">\n"
        "    <button id=\"t-deliverable\" aria-pressed=\"true\">Deliverables</button>\n"
        "    <button id=\"t-research\" aria-pressed=\"false\">Research trail</button>\n"
        "    <button id=\"t-support\" aria-pressed=\"false\">Working files</button>\n"
        "    <button id=\"t-theme\" type=\"button\">Dark</button>\n"
        "  </div>\n"
        "</div>\n\n"
        "<nav class=\"topic-nav\" id=\"topic-nav\"></nav>\n"
        "<div id=\"dupes\"></div>\n"
        "<div id=\"parts-root\"></div>\n"
        "<main id=\"out\"></main>\n\n"
        "<footer>\n"
        "  Built from <code>docs/</code> by <code>build-research-hub.py</code>.\n"
        "  Parts tables read <code>NEED-TO-BUY.md</code>, "
        "<code>te-on-hand-bom.csv</code>, and the enclosure CSVs.\n"
        "  Section links use the source document's own anchors where it has them.\n"
        "</footer>\n</div>\n\n<script>\nconst DATA = "
        + payload
        + ";\n"
        + HUB_JS
        + "\n</script>\n</body>\n</html>\n"
    )


def main() -> None:
    data = build()
    require_parts_tables(data)
    for t in data["topics"]:
        for d in t["docs"]:
            d["human_size"] = human_size(d["size"])
    OUT.write_text(render(data), encoding="utf-8")
    deliv = sum(t["counts"]["deliverable"] for t in data["topics"])
    research = sum(t["counts"]["research"] for t in data["topics"])
    total = sum(len(t["docs"]) for t in data["topics"])
    stats = data["parts"]["stats"]
    print(f"wrote {OUT.relative_to(REPO)}  "
          f"({len(data['topics'])} topics, {deliv} deliverables, "
          f"{research} research notes, {total} files, "
          f"{len(data['dupes'])} duplicate groups, "
          f"{stats['buy_lines']} buy / {stats['onhand_skus']} on-hand / "
          f"{stats['enclosure_lines']} enclosure)")


if __name__ == "__main__":
    main()
