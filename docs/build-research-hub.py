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
import sys
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
                 "build. ECU wiring docs that were also in this tree have been retired.",
    },
    {
        "dir": "harness",
        "title": "Harness & Wiring",
        "blurb": "Current harnesses live under rebuild/ (A/B cabin, A/B engine, CAN, EngineRoom-C, "
                 "WheelSpeed front/rear, RearFuel, ClusterLED, AntiTheft, RearLights). Buy list and per-wire build sheet "
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
        "dir": "../cad",
        "title": "CAD (custom parts)",
        "blurb": "Every custom-part CAD model, one folder per part (index of all models: cad/README.md): bus bar (five saved designs), "
                 "fuse/relay box plan, VRC and CSB3 enclosures, DRB102 firewall plate. Pages, "
                 "renders and build scripts are in git; model files (STEP, STL, .f3d) are local only.",
    },
    {
        "dir": "research",
        "title": "Research & part picks",
        "blurb": "Dated research, part-pick and audit pages - latest of each topic only. "
                 "A decision they led to is recorded in DECISIONS / OPEN-ITEMS, and that record wins.",
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
ASSET_SUFFIXES = {".png", ".svg", ".webp", ".jpg", ".jpeg", ".pdf", ".ico",
                  ".f3d", ".stl", ".step", ".stp"}
SKIP_NAMES = {"package-lock.json", "package.json"}
SKIP_PATTERNS = [re.compile(r"\.bak\.html$"), re.compile(r"^__pycache__$")]

# A readable file sitting directly in a topic folder is a deliverable; anything
# deeper (research/, data/) is the working trail behind it. These two lists
# override that inference where the layout lies.
FORCE_RESEARCH: set[str] = set()
FORCE_DELIVERABLE: set[str] = {
    "docs/sourcing/README.md",
    "docs/enclosures/README.md",
    "cad/README.md",
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


# --- Project status (docs/OPEN-ITEMS.md is the only source of the numbers) ---
TRACKER = DOCS / "OPEN-ITEMS.md"
# Area column -> Status bucket. Rows in the tracker's "Setup-time" table count as
# "Tune-ECU setup-time" (RealDash rows stay RealDash). Names must match the Status table.
AREA_BUCKET = {
    "Wiring": "Harness wiring", "Harness": "Harness wiring", "Held WS4": "Harness wiring",
    "Research": "Harness wiring", "Parts": "Parts", "CAN": "CAN", "RealDash": "RealDash",
    "Tooling": "Housekeeping", "Docs": "Housekeeping", "Housekeeping": "Housekeeping",
}
SETUP_BUCKET = "Tune-ECU setup-time"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _inline(s: str) -> str:
    """Escape a tracker cell; `code` spans become <code>."""
    return re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", html.escape(s))


def load_status() -> dict | None:
    """Read the Status section (bucket table + numbered blockers) and the open rows."""
    if not TRACKER.is_file():
        return None
    text = TRACKER.read_text(encoding="utf-8", errors="replace")
    tables = parse_md_tables(text)
    status = next((t for t in tables if t["columns"][:2] == ["Bucket", "Open"]), None)
    if not status:
        return None
    m = re.search(r"^## Status[^\n]*\n(.*?)^\| # \|", text, re.S | re.M)
    blockers = re.findall(r"^\d+\. (.+)$", m.group(1), re.M) if m else []
    groups = {r[0]: [] for r in status["rows"]}
    for t in tables:
        if t["columns"][:2] != ["#", "Area"]:
            continue
        setup = t["title"].lower().startswith("setup-time")
        for r in t["rows"]:
            rid, area, item, owner, _src, st = r[:6]
            if st.startswith(("Closed", "Merged")):
                continue
            b = area if (setup and area == "RealDash") else SETUP_BUCKET if setup                 else AREA_BUCKET.get(area, "Housekeeping")
            groups.setdefault(b, []).append(
                {"id": rid, "item": item, "owner": owner, "status": st})
    buckets = []
    for name, n, words, zones in (r[:4] for r in status["rows"]):
        found = len(groups.get(name, []))
        if str(found) != n:
            print(f"WARNING: OPEN-ITEMS Status says {name} = {n}, rows count {found}",
                  file=sys.stderr)
        ids = [z.strip() for z in zones.split(",") if z.strip() not in ("", "-")]
        for z in ids:
            if z not in CAR_ZONES:
                print(f"WARNING: OPEN-ITEMS Status zone '{z}' ({name}) is not a car zone",
                      file=sys.stderr)
        buckets.append({"name": name, "open": n, "words": words, "zones": ids,
                        "rows": groups.get(name, [])})
    return {"buckets": buckets, "blockers": blockers}


# Top view of the car, nose up. The outline is the All Trac/4WD plan view on page IN-15
# ("Vehicle lift and support locations") of the Toyota Celica repair manual, traced to its outer
# silhouette only (no chassis, no glass) and scaled to viewBox 0 0 200 400. Zones are that
# silhouette cut into bands along the car (nose = top); the Status table in OPEN-ITEMS names
# them in its "Car zones" column. Each zone: label, SVG path, label position.
CAR_OUTLINE = (
    'M115.9 10.5 L100.7 10.0 L75.4 11.8 L56.1 15.5 L46.0 19.6 L41.0 23.8 L35.9 31.6 L31.8 45.4 L28.5 63.8 L26.7 86.7 L28.1 125.3 L27.6 136.4 L26.3 140.0 L27.6 145.1 L27.2 247.6 L25.8 249.4 L25.3 253.5 L27.2 258.1 L27.2 274.2 L25.8 283.4 L25.8 304.5 L28.5 323.8 L30.4 355.5 L33.6 370.2 L37.3 376.2 L41.0 379.9 L47.4 383.6 L69.0 388.2 L90.6 390.0 L116.3 389.5 L135.6 386.8 L150.8 383.1 L156.7 379.9 L162.7 373.9 L165.9 367.0 L168.2 354.6 L170.5 322.5 L172.4 312.8 L173.7 296.3 L173.3 277.4 L171.9 264.6 L172.4 144.2 L173.3 141.0 L172.4 137.3 L172.4 118.4 L174.2 104.2 L174.7 83.1 L172.8 59.6 L170.1 45.8 L165.5 31.6 L161.8 25.2 L158.1 21.5 L151.2 17.4 L141.6 14.6 Z'
)
CAR_ZONES = {
    'bay': ('Engine bay',
        'M39.1 26.1 L35.9 31.6 L33.6 38.5 L28.5 63.8 L26.7 86.7 L27.6 117.5 L172.8 117.5 L174.2 104.2 L174.2 73.9 L172.8 59.6 L170.1 45.8 L165.5 31.6 L161.8 25.2 L158.1 21.5 L44.2 21.0 Z',
        (100, 70)),
    'firewall': ('Firewall / bulkheads',
        'M27.6 118.0 L27.6 134.5 L172.4 134.5 L172.8 118.0 Z',
        (100, 129)),
    'dash': ('Dash / cabin front',
        'M26.3 140.0 L27.6 145.1 L27.6 169.0 L172.4 169.0 L172.4 144.2 L173.3 141.0 L172.4 135.0 L27.6 135.0 Z',
        (70, 154)),
    'glove': ('Glove box (fuse box)',
        'M103.0 139.1 L103.0 165.3 L162.3 165.3 L162.3 139.1 Z',
        (134, 154)),
    'floor': ('Cabin floor / sills',
        'M27.6 169.4 L27.2 244.8 L171.9 244.8 L172.4 169.4 Z',
        (100, 208)),
    'trunk': ('Trunk (battery, kill switch)',
        'M27.2 245.3 L25.3 252.2 L27.2 258.1 L27.2 274.2 L25.8 283.4 L25.8 304.5 L26.7 313.3 L172.4 312.8 L173.7 285.7 L171.9 264.6 L171.9 245.3 Z',
        (100, 280)),
    'rear': ('Rear / hatch',
        'M26.7 313.7 L28.5 323.8 L29.9 351.4 L32.7 367.5 L37.3 376.2 L43.7 381.7 L153.5 381.7 L160.9 376.2 L165.5 368.4 L168.2 354.6 L171.9 313.7 Z',
        (100, 348)),
}


def car_svg() -> str:
    parts = "".join(
        f'<g class="zone" data-zone="{zid}" tabindex="-1"><title>{html.escape(label)}</title>'
        f'<path d="{d}"/><text x="{xy[0]}" y="{xy[1]}" text-anchor="middle">'
        f'{html.escape(label.split(" (")[0].split(" / ")[0])}</text></g>'
        for zid, (label, d, xy) in CAR_ZONES.items())
    return (
        '<svg class="car" viewBox="0 0 200 400" role="img" '
        'aria-label="Top view outline of the Celica, nose up, with the zones the open items touch">'
        f'<path class="body" d="{CAR_OUTLINE}"/>{parts}</svg>')


CAR_JS = """
(function () {
  var root = document.getElementById("status");
  if (!root) return;
  var rows = root.querySelectorAll("tr[data-zones]");
  var legend = root.querySelector(".car-legend");
  var picked = null, hover = null;
  function show() {
    var r = hover || picked, on = r ? r.dataset.zones.split(" ").filter(Boolean) : [];
    root.querySelectorAll(".zone").forEach(function (z) {
      z.classList.toggle("on", on.indexOf(z.dataset.zone) >= 0);
    });
    rows.forEach(function (x) { x.classList.toggle("sel", x === r); });
    legend.textContent = !r ? "Tap or hover a bucket to light up where it lives on the car."
      : on.length ? r.dataset.label + ": " + on.map(function (id) {
          return root.querySelector('.zone[data-zone="' + id + '"] title').textContent; }).join(", ")
      : r.dataset.label + ": nothing on the car";
  }
  rows.forEach(function (r) {
    r.addEventListener("mouseenter", function () { hover = r; show(); });
    r.addEventListener("mouseleave", function () { hover = null; show(); });
    r.addEventListener("click", function (e) {
      if (e.target.closest("a")) return;
      picked = picked === r ? null : r; show();
    });
  });
  show();
})();
"""


def status_html(st: dict | None) -> str:
    """Static top-of-page table plus one anchored row group per bucket."""
    if not st:
        return ""
    body = "".join(
        f'<tr data-zones="{" ".join(b["zones"])}" data-label="{html.escape(b["name"])}">'
        f'<td><a href="#items-{_slug(b["name"])}">{html.escape(b["name"])}</a></td>'
        f'<td class="num">{html.escape(b["open"])}</td><td>{_inline(b["words"])}</td></tr>'
        for b in st["buckets"])
    blockers = "".join(f"<li>{_inline(x)}</li>" for x in st["blockers"])
    groups = ""
    for b in st["buckets"]:
        rows = "".join(
            f'<tr><td class="num">{html.escape(r["id"])}</td><td>{_inline(r["item"][:240])}'
            f'{"&hellip;" if len(r["item"]) > 240 else ""}</td>'
            f'<td>{html.escape(r["owner"])}</td><td>{html.escape(r["status"])}</td></tr>'
            for r in b["rows"])
        groups += (
            f'<details class="items" id="items-{_slug(b["name"])}" open>'
            f'<summary>{html.escape(b["name"])} &middot; {html.escape(b["open"])} open</summary>'
            f'<div class="twrap"><table class="data"><thead><tr><th>#</th><th>Item</th>'
            f'<th>Owner</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'</details>')
    return (
        '<section class="board" id="status">\n<h2>Open work by area</h2>\n'
        '<p class="blurb">Big picture, read from the <code>Status</code> section of '
        '<a href="../docs/OPEN-ITEMS.md">docs/OPEN-ITEMS.md</a> (the one tracker). '
        'Click a bucket for its open rows.</p>\n'
        '<div class="statusrow"><div class="twrap"><table class="data statustbl"><thead><tr>'
        '<th>Bucket</th><th>Open</th>'
        f'<th>In plain words</th></tr></thead><tbody>{body}</tbody></table></div>\n'
        f'<figure class="carfig">{car_svg()}<figcaption class="car-legend"></figcaption>'
        '</figure></div>\n'
        f'<h3 id="blockers">What blocks progress</h3>\n<ol class="blockers">{blockers}</ol>\n'
        f'<h3 id="open-items">Open rows by bucket</h3>\n{groups}\n'
        f'<script>{CAR_JS}</script>\n</section>\n')


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


# --- "Project status" page section for Dan (built from repo files at build time) ---
QUESTIONS = DOCS / "status" / "questions.json"
CAD_INDEX = REPO / "cad" / "README.md"
ROUTES = DOCS / "harness" / "routes"
RECENT_PRS = 15


def _plain(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s).replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def load_questions() -> dict:
    """Open questions for Dan: docs/status/questions.json (kept current by Dispatch)."""
    try:
        data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"WARNING: {QUESTIONS.name} unreadable: {e}", file=sys.stderr)
        return {"updated": "", "questions": []}
    qs = []
    for q in data.get("questions", []):
        if not isinstance(q, dict) or not q.get("id") or not q.get("text"):
            print(f"WARNING: skipped malformed question {q!r}", file=sys.stderr)
            continue
        qs.append({
            "id": str(q["id"]), "topic": str(q.get("topic", "")), "text": str(q["text"]),
            "options": [{"value": str(o.get("value", "")), "label": str(o.get("label", "")),
                         "recommended": bool(o.get("recommended"))}
                        for o in q.get("options", []) if isinstance(o, dict)],
        })
    return {"updated": str(data.get("updated", "")), "questions": qs}


def load_routes() -> list[dict]:
    """Approval state of each route drawing, read from its own status text.

    Order of evidence: a `Status (Dan, date):` box, then an APPROVED title, then an
    `Approved` box, then a `Your decision:` box (still waiting on Dan). Otherwise unmarked.
    """
    out = []
    files = sorted(ROUTES.glob("ROUTE-*.html"),
                   key=lambda p: int(re.search(r"ROUTE-(\d+)", p.name).group(1)))
    for p in files:
        src = p.read_text(encoding="utf-8", errors="replace")
        num = int(re.search(r"ROUTE-(\d+)", p.name).group(1))
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
        title = _plain(h1.group(1)) if h1 else p.stem
        boxes = [_plain(m) for m in
                 re.findall(r'<div class="(?:box|banner)"[^>]*>(.*?)</div>', src, re.S)]
        status_box = next((b for b in boxes if b.startswith("Status (")), "")
        approved_box = next((b for b in boxes if re.match(r"Approved\b", b)), "")
        decision_box = next((b for b in boxes if b.startswith("Your decision:")), "")
        state, note = "unmarked", ""
        if status_box:
            m = re.match(r"Status \(([^)]*)\):\s*(.*)", status_box)
            state = "approved" if m and m.group(2).upper().startswith("APPROVED") else "note"
            note = f"{m.group(1)}: {m.group(2)}" if m else status_box
        elif "APPROVED" in title:
            state, note = "approved", title
        elif approved_box:
            state, note = "approved", approved_box
        elif decision_box:
            state, note = "waiting", decision_box
        out.append({"num": num, "title": re.sub(r"^Route \d+\s*[—-]\s*", "", title)[:80],
                    "file": p.name, "state": state, "note": note[:220]})
    return out


MODEL_EXT = {".step", ".stp", ".stl", ".f3d", ".f3z"}
CAD_MANIFEST = REPO / "cad" / "model-files.json"
# Where the heavy (gitignored) model files live on Dan's PC; shown as the "full local path".
DAN_ROOT = "C:/projects/active/st185-link-ecu-config"
HANGER_RUN = Path("C:/projects/active/fairsolid/runs/fuel_hanger_billet_1014")
# Trimetric pictures (DECISIONS R83): rendered by cad/render_trimetric.py, sources + dates here.
TRIMETRICS = REPO / "cad" / "trimetrics.json"
# GitHub Pages serves docs/ only; the page swaps "../" links and images to these on github.io.
GH_BLOB = "https://github.com/living-relation/st185-link-ecu-config/blob/main/"
GH_RAW = "https://raw.githubusercontent.com/living-relation/st185-link-ecu-config/main/"


def _main_checkout() -> Path:
    """The main checkout holds the gitignored model files; a worktree has only tracked ones."""
    try:
        out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=REPO,
                             capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        return (REPO / out).resolve().parent
    except Exception:
        return REPO


def _model_names(d: Path) -> list[str]:
    return sorted(p.name for p in d.iterdir() if p.suffix.lower() in MODEL_EXT) if d.is_dir() else []


def scan_model_files() -> dict:
    """Model files found on THIS disk: every cad/ folder holding STEP/STL/f3d, plus the
    newest rev folder of the Fairsolid fuel hanger run. {} when none are present (CI)."""
    found: dict[str, list[str]] = {}
    for root in {REPO, _main_checkout()}:
        cad = root / "cad"
        if not cad.is_dir():
            continue
        for d in [cad, *[p for p in cad.rglob("*") if p.is_dir()]]:
            names = _model_names(d)
            if names:
                rel = d.relative_to(root).as_posix()
                found[rel] = sorted(set(found.get(rel, [])) | set(names))
    if HANGER_RUN.is_dir():
        revs = sorted((p for p in HANGER_RUN.glob("rev*") if re.fullmatch(r"rev\d+", p.name)),
                      key=lambda p: int(p.name[3:]))
        latest = revs[-1] if revs else HANGER_RUN
        names = _model_names(latest)
        if names:
            found[latest.as_posix()] = names
    return found


def load_model_manifest() -> tuple[dict, str]:
    """Model file lists: refreshed from disk when the files are here (a local build; commit
    cad/model-files.json), otherwise the tracked copy (the bot's build has no heavy files)."""
    found = scan_model_files()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if found:
        old = {}
        try:
            old = json.loads(CAD_MANIFEST.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if old.get("files") != found:
            CAD_MANIFEST.write_text(
                json.dumps({"generated": today, "files": found}, indent=1) + "\n", encoding="utf-8")
            print(f"updated {CAD_MANIFEST.relative_to(REPO)} - commit it with this change")
            return found, today
        return found, old.get("generated", today)
    try:
        old = json.loads(CAD_MANIFEST.read_text(encoding="utf-8"))
        return old.get("files", {}), old.get("generated", "")
    except (OSError, ValueError):
        return {}, ""


def _row_dirs(cell: str) -> list[str]:
    """Folder paths named in a README 'Local model files' cell: `cad/...` or `C:\\...`."""
    out = []
    for tok in re.findall(r"`([^`]+)`", cell):
        t = tok.replace("\\", "/").rstrip("/")
        if (t.startswith("cad/") or re.match(r"[A-Za-z]:/", t)) and "." not in t.rsplit("/", 1)[-1]:
            out.append(t)
    return out


def load_cad() -> dict:
    """CAD models from cad/README.md, their summary links and local file lists, plus
    warnings for anything on disk that the README does not cover."""
    warnings: list[str] = []
    files, generated = load_model_manifest()
    rows: list[dict] = []
    text = ""
    if CAD_INDEX.is_file():
        text = CAD_INDEX.read_text(encoding="utf-8", errors="replace")
        # Raw split, not parse_md_tables: that helper strips the backticks the paths sit in.
        # Cells are read by column name, so a new column never shifts the others.
        lines = text.splitlines()
        for n, ln in enumerate(lines):
            if ln.startswith("| Model |"):
                head = [c.strip() for c in ln.strip().strip("|").split("|")]
                for row in lines[n + 2:]:
                    if not row.startswith("|"):
                        break
                    cells = [c.strip() for c in row.strip().strip("|").split("|")]
                    if len(cells) >= 5:
                        rows.append(dict(zip(head, cells)))
                break
    if not rows:
        warnings.append("cad/README.md has no model table.")
    models, claimed = [], set()
    for r in rows:
        model, status = _plain(r.get("Model", "")), _plain(r.get("Status / rev", ""))
        summary, local = r.get("Summary page", ""), r.get("Local model files", "")
        selected = _plain(r.get("Selected for build", "")).lower() == "yes"
        links = [("../cad/" + h if not re.match(r"[A-Za-z]:|https?:|\.\./", h) else h, lbl)
                 for lbl, h in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", summary)]
        links += [(tok, tok) for tok in re.findall(r"`([A-Za-z]:[^`]+\.(?:md|html))`", summary)]
        if not links and _plain(summary).lower().startswith("same page") and models:
            links = models[-1]["links"]   # "same page" = the row above's summary page
        dirs = _row_dirs(local)
        folders = []
        for d in dirs:
            claimed.add(d)
            if re.match(r"[A-Za-z]:/", d):
                # External run folder: README must name the newest rev folder on disk.
                latest = next((k for k in files if re.match(r"[A-Za-z]:/", k)
                               and k.startswith(d.rsplit("/rev", 1)[0])), "")
                if latest and latest.rstrip("/") != d:
                    warnings.append(f"{model}: README names {d}, newest on disk is {latest}.")
                    claimed.add(latest)
                    d = latest
                shown = d
            else:
                shown = f"{DAN_ROOT}/{d}"
            names = files.get(d, [])
            if not names:
                warnings.append(f"{model}: README lists {d} but no model files were found there.")
            folders.append({"path": shown, "names": names})
        pics = [{"src": "cad/" + src, "alt": html.unescape(alt)} for src, alt in
                re.findall(r'<img src="([^"]+)" alt="([^"]*)"', r.get("Trimetric", ""))]
        if not pics and dirs:
            warnings.append(f"{model}: no trimetric picture in cad/README.md (DECISIONS R83).")
        for pic in pics:
            if not (REPO / pic["src"]).is_file():
                warnings.append(f"{model}: trimetric {pic['src']} is missing - run cad/render_trimetric.py.")
        models.append({"model": model, "status": status[:260], "links": links, "pics": pics,
                       "selected": selected,
                       "folders": folders, "note": _plain(local) if not dirs else ""})
    if rows and not any(m["selected"] for m in models):
        warnings.append("cad/README.md marks no model 'Selected for build' (DECISIONS R77).")
    f3d_text = text
    for d, names in sorted(files.items()):
        if d not in claimed:
            warnings.append(f"Model files in {d} ({len(names)} files) have no row in cad/README.md.")
            continue
        for n in names:
            if n.lower().endswith(".f3d") and n not in f3d_text:
                warnings.append(f"{d}/{n} is not named in cad/README.md.")
    trim = load_trimetrics(warnings)
    chosen = {p["src"] for m in models if m["selected"] for p in m["pics"]}
    package = load_power_package(text, trim, chosen, warnings)
    views = load_power_views(text, warnings)
    for w in warnings:
        print(f"WARNING (CAD index): {w}", file=sys.stderr)
    return {"models": models, "warnings": warnings, "manifest": generated,
            "trimetrics": trim, "package": package, "views": views}


def load_trimetrics(warnings: list[str]) -> dict:
    """cad/trimetrics.json, keyed by PNG path. On a PC with the STEP files, warn when a
    source STEP is newer than the date its picture was rendered from (R83)."""
    try:
        meta = json.loads(TRIMETRICS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        warnings.append("cad/trimetrics.json is missing - run cad/render_trimetric.py.")
        return {}
    out = {}
    for mid, m in meta.items():
        out[m["png"]] = {**m, "id": mid}
        for src, stamp in m.get("sources", {}).items():
            f = Path(src)
            if f.is_file() and int(f.stat().st_mtime) > stamp:
                warnings.append(f"Trimetric {m['png']} is older than {src} - re-run "
                                f"cad/render_trimetric.py --only {mid}.")
    return out


def load_power_package(text: str, trim: dict, chosen: set[str], warnings: list[str]) -> list[dict]:
    """cad/README.md "Power distribution package" table (R84) with a parts count per member:
    a parts CSV (pieces = qty_need) or `model:<id>` (solids in the assembly STEP). Only
    models marked "Selected for build" (R77) count; any other member is dropped with a warning."""
    members = []
    lines = text.splitlines()
    for n, ln in enumerate(lines):
        if ln.startswith("| Member |"):
            for row in lines[n + 2:]:
                if not row.startswith("|"):
                    break
                c = [x.strip() for x in row.strip().strip("|").split("|")]
                if len(c) < 4:
                    continue
                png = "cad/" + c[1].strip("`")
                if png not in chosen:
                    warnings.append(f"Power package: {_plain(c[0])} ({png}) is not a model marked "
                                    "'Selected for build' in cad/README.md - left out (R77, R84).")
                    continue
                per_car = _intish(c[2]) or 1
                src = c[3].strip("`")
                lines_n = pieces = 0
                if src.startswith("model:"):
                    m = next((t for t in trim.values() if t["id"] == src[6:]), None)
                    if m:
                        lines_n, pieces = m.get("part_types", 0), m.get("solids", 0)
                    basis = "solids in the assembly STEP (no BOM yet)"
                else:
                    rows = _csv_rows(REPO / "cad" / src) if (REPO / "cad" / src).is_file() else []
                    lines_n = len(rows)
                    pieces = sum(_intish(r.get("qty_need")) for r in rows)
                    basis = f"cad/{src}"
                if not lines_n:
                    warnings.append(f"Power package: no parts found for {_plain(c[0])} ({src}).")
                members.append({"name": _plain(c[0]), "png": png, "per_car": per_car,
                                "lines": lines_n, "pieces": pieces * per_car, "basis": basis})
            break
    if not members:
        warnings.append("cad/README.md has no Power distribution package table (R84).")
    return members


def load_power_views(text: str, warnings: list[str]) -> list[dict]:
    """cad/README.md "Power package views" table: extra renders of the selected boxes (side views,
    exploded, underneath, the typical arrangement), shown under the package on the hub."""
    views = []
    lines = text.splitlines()
    for n, ln in enumerate(lines):
        if ln.startswith("| View |"):
            for row in lines[n + 2:]:
                if not row.startswith("|"):
                    break
                c = [x.strip() for x in row.strip().strip("|").split("|")]
                if len(c) < 2:
                    continue
                png = "cad/" + c[1].strip("`")
                if not (REPO / png).is_file():
                    warnings.append(f"Power package view {png} is missing.")
                    continue
                views.append({"caption": _plain(c[0]), "png": png})
            break
    return views


def cad_files_html(folders: list[dict]) -> str:
    e = html.escape
    out = ""
    for f in folders:
        names = f["names"]
        key = names if f.get("all") else [
            n for n in names if n.lower().endswith((".f3d", ".f3z")) or "assembly" in n.lower()]
        rest = [n for n in names if n not in key]
        counts = Counter(Path(n).suffix.lower().lstrip(".") for n in rest)
        more = ", ".join(f"{c} {k.upper()}" for k, c in sorted(counts.items()))
        lines = "".join(f"<li><code>{e(f['path'])}/{e(n)}</code></li>" for n in key)
        out += (f'<div class="cadf"><code>{e(f["path"])}/</code><ul>{lines}</ul>'
                + (f'<span class="muted">+ {len(rest)} part files in that folder ({e(more)})</span>'
                   if rest else "") + "</div>")
    return out


def _img(src: str, alt: str) -> str:
    """A repo image from docs/: relative path locally; on github.io (Pages serves docs/ only)
    the page script swaps it to the raw GitHub copy via data-gh."""
    e = html.escape
    return (f'<img src="../{e(src)}" data-gh="{e(src)}" alt="{e(alt)}" loading="lazy" '
            f'width="900" height="640">')


def _pic_folders(folders: list[dict], pic: dict, trim: dict) -> list[dict]:
    """For a row with several pictures (the three fuse boxes share one folder), show the
    files that picture was rendered from (their common name prefix) plus the .f3d / assembly."""
    srcs = [Path(k).name for k in trim.get(pic["src"], {}).get("sources", {})]
    if len(srcs) < 2:
        return folders
    pre = srcs[0][:next((i for i, ch in enumerate(zip(*srcs)) if len(set(ch)) > 1), len(srcs[0]))]
    if not pre:
        return folders
    return [{**f, "all": True, "names": [n for n in f["names"] if n.startswith(pre)
                            or n.lower().endswith((".f3d", ".f3z")) or "assembly" in n.lower()]}
            for f in folders]


def cad_gallery_html(cadd: dict) -> str:
    """R77: the models selected for the build first, highlighted; every other version folded
    into a greyed "Superseded / alternatives - not used" section."""
    sel = [c for c in cadd["models"] if c["selected"]]
    old = [c for c in cadd["models"] if not c["selected"]]
    n_old = sum(len(c["pics"]) or 1 for c in old)
    return (
        '<h4 class="selhead">Selected for build</h4>\n<p class="muted">The one version of each '
        'item being built (column "Selected for build" in <code>cad/README.md</code>, DECISIONS R77). '
        'Build from these files.</p>\n'
        f'<div class="cadgrid">{_cad_cards(sel, cadd, True)}</div>\n'
        f'<details class="cadold"><summary>Superseded / alternatives - not used ({n_old})</summary>'
        '<p class="muted">Older revisions and designs that were not picked. Kept for reference '
        'only - do not build from these.</p>'
        f'<div class="cadgrid">{_cad_cards(old, cadd, False)}</div></details>\n')


def _cad_cards(models: list[dict], cadd: dict, selected: bool) -> str:
    """One card per trimetric picture (a row with no model kept gets a card without one)."""
    e = html.escape
    out = ""
    badge = ('<span class="selbadge">SELECTED FOR BUILD</span>' if selected
             else '<span class="oldbadge">NOT USED</span>')
    for c in models:
        links = " ".join(
            f'<a href="{e(h)}">{e(lbl)}</a>' if not re.match(r"[A-Za-z]:", h) else f"<code>{e(h)}</code>"
            for h, lbl in c["links"]) or "&mdash;"
        for pic in c["pics"] or [None]:
            folders = _pic_folders(c["folders"], pic, cadd["trimetrics"]) if pic else c["folders"]
            files = cad_files_html(folders) or f'<span class="muted">{e(c["note"] or "none kept")}</span>'
            meta = cadd["trimetrics"].get(pic["src"], {}) if pic else {}
            when = (f'<span class="muted">Rendered {e(meta["rendered"])} from the STEP.</span>'
                    if meta.get("rendered") else "")
            title = pic["alt"] if pic and len(c["pics"]) > 1 else c["model"]
            sub = f' <span class="muted">({e(c["model"])})</span>' if title != c["model"] else ""
            out += (f'<div class="cadcard{" sel" if selected else " old"}">'
                    f'{_img(pic["src"], title) if pic else ""}'
                    f'<div class="cadbody">{badge}<b>{e(title)}</b>{sub}<p>{e(c["status"])}</p>'
                    f'<p>Summary: {links}</p><div class="cadpath">True location:{files}</div>'
                    f'{when}</div></div>')
    return out


def power_package_html(cadd: dict) -> str:
    """DECISIONS R84: the power distribution package, always shown as one, with a parts total."""
    e = html.escape
    mem = cadd["package"]
    if not mem:
        return ""
    cards = "".join(
        f'<div class="pkgitem">{_img(m["png"], m["name"])}<b>{e(m["name"])}</b>'
        f'<span class="muted">{m["per_car"]} per car &middot; {m["pieces"]} pcs</span></div>'
        for m in mem)
    rows = "".join(
        f'<tr><td>{e(m["name"])}</td><td class="num">{m["per_car"]}</td><td class="num">{m["lines"]}</td>'
        f'<td class="num">{m["pieces"]}</td><td class="muted"><code>{e(m["basis"])}</code></td></tr>'
        for m in mem)
    lines = sum(m["lines"] for m in mem)
    pieces = sum(m["pieces"] for m in mem)
    units = sum(m["per_car"] for m in mem)
    return (
        '<div class="pkg" id="power-package"><h3>Power distribution package</h3>'
        f'<p class="muted">The whole package as one (DECISIONS R84): {len(mem)} designs, {units} units '
        f'in the car, <b>{pieces} parts</b> ({lines} part lines). Members: <code>cad/README.md</code> '
        '"Power distribution package". A fuse box counts every line of its parts list (fuses, relays, '
        'terminals, copper, printed parts); a model with no BOM yet counts the solids in its '
        'assembly STEP.</p>'
        f'<div class="pkggrid">{cards}</div>'
        '<div class="twrap"><table class="data"><thead><tr><th>Member</th><th>Per car</th>'
        '<th>Part lines</th><th>Pieces (car)</th><th>Counted from</th></tr></thead>'
        f'<tbody>{rows}<tr><td><b>Total</b></td><td class="num"><b>{units}</b></td>'
        f'<td class="num"><b>{lines}</b></td><td class="num"><b>{pieces}</b></td><td></td></tr>'
        '</tbody></table></div>' + power_views_html(cadd) + '</div>')


def power_views_html(cadd: dict) -> str:
    """The "Power package views" pictures (cad/README.md), one card each."""
    e = html.escape
    vs = cadd.get("views") or []
    if not vs:
        return ""
    cards = "".join(
        f'<div class="pkgitem"><a href="../{e(v["png"])}">{_img(v["png"], v["caption"])}</a>'
        f'<span class="muted">{e(v["caption"])}</span></div>' for v in vs)
    return ('<h4>Views: sides, exploded, underneath, typical arrangement</h4>'
            '<p class="muted">From <code>cad/README.md</code> "Power package views". Tap a picture for full size.</p>'
            f'<div class="pkggrid">{cards}</div>')


def load_recent_prs() -> list[dict]:
    """Last merged PR titles on main (squash merges end in "(#N)"). Empty without git."""
    try:
        out = subprocess.run(
            ["git", "log", "--first-parent", "-n", "200", "--format=%cs\t%s"],
            cwd=REPO, capture_output=True, text=True, timeout=20, check=True).stdout
    except Exception as e:
        print(f"WARNING: git log unavailable, no recent changes: {e}", file=sys.stderr)
        return []
    prs = []
    for line in out.splitlines():
        date, _, subj = line.partition("\t")
        m = re.search(r"\(#(\d+)\)\s*$", subj)
        if m and not subj.startswith("Auto-regenerate"):
            prs.append({"date": date, "title": subj[:m.start()].strip(), "num": m.group(1)})
        if len(prs) >= RECENT_PRS:
            break
    return prs


def load_project_status(status: dict | None) -> dict:
    dan = []
    for b in (status or {}).get("buckets", []):
        rows = [r for r in b["rows"] if r["owner"].strip().lower() in ("daniel", "dan")]
        if rows:
            dan.append({"name": b["name"], "rows": rows})
    return {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "questions": load_questions(), "dan_items": dan, "routes": load_routes(),
        "cad": load_cad(), "prs": load_recent_prs(),
    }


def project_status_html(ps: dict) -> str:
    e = html.escape
    qs = ps["questions"]["questions"]
    if qs:
        qhtml = ""
        for q in qs:
            opts = ""
            for o in q["options"]:
                tag = ' <span class="tag">recommended</span>' if o["recommended"] else ""
                opts += (f'<li class="{"rec" if o["recommended"] else ""}">'
                         f'<b>{e(o["value"])}</b> {e(o["label"])}{tag}</li>')
            qhtml += (f'<div class="q"><div class="qh"><b>{e(q["id"])}</b>'
                      f'<span class="muted"> &middot; {e(q["topic"])}</span></div>'
                      f'<p>{e(q["text"])}</p><ul class="opts">{opts}</ul></div>')
        qhtml += ('<p class="howto"><b>How to answer:</b> reply in the Dispatch chat with the '
                  'question ID and the letter, e.g. <code>Z9: A</code>. Write-ins are fine.</p>')
    else:
        qhtml = '<p class="muted">No open questions right now.</p>'
    upd = ps["questions"]["updated"]
    upd_txt = f", updated {e(upd)}" if upd else ""

    dan = ""
    for g in ps["dan_items"]:
        rows = "".join(
            f'<tr><td class="num">{e(r["id"])}</td><td>{_inline(r["item"][:240])}'
            f'{"&hellip;" if len(r["item"]) > 240 else ""}</td><td>{e(r["status"])}</td></tr>'
            for r in g["rows"])
        dan += (f'<details class="items" open><summary>{e(g["name"])} &middot; {len(g["rows"])}'
                '</summary><div class="twrap"><table class="data"><thead><tr><th>#</th>'
                f'<th>Item</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>'
                '</details>')
    dan = dan or '<p class="muted">Nothing open for Dan.</p>'

    label = {"approved": "Approved", "waiting": "Decision box open", "note": "Note",
             "unmarked": "No status"}
    routes = "".join(
        f'<tr><td class="num">{r["num"]}</td>'
        f'<td><a href="harness/routes/{e(r["file"])}">{e(r["title"])}</a></td>'
        f'<td><span class="pill {r["state"]}">{label[r["state"]]}</span></td>'
        f'<td class="muted">{e(r["note"])}</td></tr>' for r in ps["routes"])
    cadd = ps["cad"]
    warn = "".join(f"<li>{e(w)}</li>" for w in cadd["warnings"])
    cwarn = ('<div class="cadwarn"><b>CAD index is out of date:</b><ul>' + warn + "</ul>"
             "Fix <code>cad/README.md</code> (and run the builder locally to refresh "
             "<code>cad/model-files.json</code>).</div>") if warn else ""
    cad = cad_gallery_html(cadd)
    package = power_package_html(cadd)
    pr_url = "https://github.com/living-relation/st185-link-ecu-config/pull/"
    prs = "".join(
        f'<li><span class="muted">{e(p["date"])}</span> {e(p["title"])} '
        f'<a href="{pr_url}{p["num"]}">#{p["num"]}</a></li>' for p in ps["prs"]
    ) or '<li class="muted">Git history was not available when this page was built.</li>'
    return (
        '<section class="board pstatus" id="project-status">\n<h2>Project status</h2>\n'
        f'<p class="blurb">Built {e(ps["built"])} from the repo. Nothing here is typed by '
        'hand except the questions. Route status is read from each drawing\'s own status box; '
        'a route with an open decision box may have been approved later, so check the history '
        'in <a href="OPEN-ITEMS.md">OPEN-ITEMS</a>.</p>\n'
        '<h3>Open questions for Dan</h3>\n<p class="muted">From '
        f'<code>docs/status/questions.json</code>{upd_txt}.</p>\n{qhtml}\n'
        f'<h3>Dan&rsquo;s open items</h3>\n{dan}\n'
        '<h3>Route drawings</h3>\n<div class="twrap"><table class="data"><thead><tr><th>#</th>'
        '<th>Route</th><th>Status</th><th>From the drawing</th></tr></thead>'
        f'<tbody>{routes}</tbody></table></div>\n'
        '<h3 id="cad-models">CAD models</h3>\n<p class="muted">Every custom CAD model, one trimetric '
        'each (same camera for all, rendered from the STEP by <code>cad/render_trimetric.py</code>; '
        'DECISIONS R83), from <code>cad/README.md</code> (the one CAD index). The paths are the '
        '<b>true location</b> of the STEP, STL and Fusion <code>.f3d</code> files: they are '
        'gitignored and live on Dan&rsquo;s PC, not in GitHub. '
        f'File list last refreshed {e(cadd["manifest"] or "never")}.</p>\n{cwarn}\n'
        f'{package}\n{cad}'
        f'<h3>Recently merged</h3>\n<ul class="prs">{prs}</ul>\n</section>\n')


PSTATUS_CSS = """
  .topnav { display:flex; gap:8px; flex-wrap:wrap; margin:0 0 18px; }
  .topnav a { padding:8px 14px; border:1px solid var(--line); border-radius:999px;
    background:var(--panel); color:var(--ink); text-decoration:none; font-weight:600; }
  .pstatus .q { border:1px solid var(--line); background:var(--panel); border-radius:8px;
    padding:10px 14px; margin:10px 0; }
  .pstatus .qh { font-size:15px; } .pstatus .q p { margin:6px 0; }
  .pstatus .opts { list-style:none; margin:6px 0 0; padding:0; }
  .pstatus .opts li { padding:6px 8px; border-radius:6px; margin:3px 0; background:var(--chip); }
  .pstatus .opts li.rec { background:var(--ok-soft); border-left:4px solid var(--ok); }
  .pstatus .tag { font-size:11px; color:var(--ok); font-weight:700; text-transform:uppercase; }
  .pstatus .howto { background:var(--info-soft); padding:8px 12px; border-radius:6px; }
  .pstatus .muted { color:var(--muted); }
  .pstatus .pill { padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700;
    white-space:nowrap; background:var(--chip); }
  .pstatus .pill.approved { background:var(--ok-soft); color:var(--ok); }
  .pstatus .pill.waiting { background:var(--warn-soft); color:var(--warn); }
  .pstatus .prs { padding-left:18px; } .pstatus .prs li { margin:4px 0; }
  .pstatus .cadwarn { background:var(--warn-soft); border:2px solid var(--warn); color:var(--ink);
    padding:8px 14px; border-radius:6px; margin:8px 0; }
  .pstatus .cadf { margin:0 0 8px; font-size:12px; word-break:break-all; }
  .pstatus .cadf ul { margin:2px 0 2px 16px; padding:0; }
  .pstatus .cadgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px; margin:10px 0; }
  .pstatus .cadcard { border:1px solid var(--line); background:var(--panel); border-radius:8px; overflow:hidden; min-width:0; }
  .pstatus .cadcard img, .pstatus .pkgitem img { display:block; width:100%; height:auto; background:#fff; }
  .pstatus .cadbody { padding:8px 12px 12px; } .pstatus .cadbody p { margin:6px 0; }
  .pstatus .cadpath { font-size:12px; margin:6px 0; }
  .pstatus .selhead { margin:14px 0 2px; color:var(--ok); }
  .pstatus .cadcard.sel { border:3px solid var(--ok); box-shadow:0 0 0 3px var(--ok-soft); }
  .pstatus .selbadge, .pstatus .oldbadge { display:inline-block; font-size:11px; font-weight:800;
    letter-spacing:.04em; padding:2px 8px; border-radius:999px; margin:0 0 6px; }
  .pstatus .selbadge { background:var(--ok); color:#fff; }
  .pstatus .oldbadge { background:var(--chip); color:var(--muted); }
  .pstatus .cadbody .selbadge + b, .pstatus .cadbody .oldbadge + b { display:block; }
  .pstatus details.cadold { margin:16px 0; border:1px dashed var(--line); border-radius:8px; padding:6px 12px; }
  .pstatus details.cadold > summary { cursor:pointer; font-weight:700; color:var(--muted); padding:4px 0; }
  .pstatus .cadcard.old { opacity:.6; } .pstatus .cadcard.old img { filter:grayscale(1); }
  .pstatus .pkg { border:2px solid var(--line); border-radius:10px; padding:4px 14px 12px; margin:12px 0 18px; }
  .pstatus .pkggrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:10px; margin:8px 0 12px; }
  .pstatus .pkgitem { border:1px solid var(--line); border-radius:8px; overflow:hidden; background:var(--panel);
    display:flex; flex-direction:column; gap:2px; padding-bottom:8px; }
  .pstatus .pkgitem b, .pstatus .pkgitem span { padding:0 10px; font-size:13px; }
  @media (max-width:640px) { .pstatus td, .pstatus th { font-size:13px; }
    .pstatus .cadgrid { grid-template-columns:1fr; } .pstatus .pkggrid { grid-template-columns:1fr 1fr; } }
"""

# On GitHub Pages only docs/ is served: send "../" links to GitHub and "../" images to raw.
PAGES_JS = """
(function () {
  if (!/github\\.io$/.test(location.hostname)) return;
  var BLOB = %s, RAW = %s;
  document.querySelectorAll('img[data-gh]').forEach(function (i) { i.src = RAW + i.dataset.gh; });
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="../"]');
    if (!a) return;
    ev.preventDefault();
    window.open(BLOB + a.getAttribute('href').replace(/^(\\.\\.\\/)+/, ''), a.target || '_self');
  });
})();
""" % (json.dumps(GH_BLOB), json.dumps(GH_RAW))


def build() -> dict:
    topics = []
    seen_dirs = {t["dir"] for t in TOPICS}
    extra = sorted(
        (d.name for d in DOCS.iterdir()
         if d.is_dir() and d.name not in seen_dirs
         and not d.name.startswith(".") and d.name not in ("__pycache__", "status")),
        key=str.lower,
    )
    spec = TOPICS + [{"dir": d, "title": d.replace("-", " ").title(), "blurb": ""} for d in extra]

    digests: dict[str, list[str]] = {}
    for t in spec:
        tdir = (DOCS / t["dir"]).resolve()
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
    status = load_status()
    return {"topics": topics, "dupes": dupes, "parts": load_parts(), "status": status,
            "pstatus": load_project_status(status)}


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
  .statusrow { display:flex; gap:18px; align-items:flex-start; flex-wrap:wrap; margin:0 0 14px; }
  .statusrow .twrap { flex:1 1 380px; max-height:none; }
  table.statustbl tbody tr { cursor:pointer; }
  table.statustbl tr.sel td { background:var(--accent-soft); }
  .carfig { margin:0; flex:0 0 190px; text-align:center; }
  svg.car { width:190px; height:auto; display:block; margin:0 auto; overflow:visible; }
  svg.car .body { fill:var(--panel); stroke:var(--muted); stroke-width:1.6; }
  svg.car .zone path { fill:transparent; stroke:var(--line);
    stroke-width:1; transition:stroke .15s, fill .15s, filter .15s; }
  svg.car .zone text { font-size:8px; fill:var(--muted); pointer-events:none; }
  svg.car .zone.on path { fill:var(--accent-soft); stroke:var(--accent);
    stroke-width:2; filter:drop-shadow(0 0 3px var(--accent)) drop-shadow(0 0 8px var(--accent)); }
  svg.car .zone.on text { fill:var(--accent); font-weight:600; }
  .car-legend { font-size:11.5px; color:var(--muted); margin-top:6px; min-height:2.6em; }
  details.items { margin:0 0 12px; }
  details.items summary { cursor:pointer; font-weight:600; margin:0 0 6px; }
  ol.blockers { margin:0 0 14px; padding-left:20px; font-size:13px; }
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
  document.getElementById("topic-nav").innerHTML = (DATA.status ? `<a href="#status">Status</a>` : "") + DATA.topics.map(t =>
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
        + HUB_CSS + PSTATUS_CSS
        + "</style>\n</head>\n<body>\n<div class=\"wrap\">\n<header>\n"
        f"<h1>ST185 Research Hub</h1>\n"
        f"<p class=\"sub\">Sources last updated {html.escape(latest)} &middot; "
        f"{total_read} readable documents of {total_all} files across "
        f"{len(data['topics'])} topics &middot; "
        f"{stats.get('buy_lines', 0)} buy lines / "
        f"{stats.get('onhand_skus', 0)} on-hand SKUs &middot; regenerate with "
        f"<code>python docs/build-research-hub.py</code></p>\n"
        "</header>\n\n"
        "<nav class=\"topnav\"><a href=\"#project-status\">Project status</a>"
        "<a href=\"#status\">Open work by area</a><a href=\"#topic-nav\">Research docs</a></nav>\n"
        + project_status_html(data["pstatus"]) + "\n"
        + status_html(data.get("status")) + "\n"
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
        + "\n" + PAGES_JS
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
