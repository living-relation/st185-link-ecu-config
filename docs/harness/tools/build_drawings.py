#!/usr/bin/env python
"""Our own harness drawings, generated from the ONE master wire list (DECISIONS R220 / R221).

A drawing set is one or more harnesses of docs/harness/MASTER-wirelist.csv drawn as one: its layout spec
`tools/<set>.layout.json` names them (`"harnesses": [...]`) and holds the physical tree; `tools/<set>.revs.json` is its rev
log. Combining one more harness later = add it to `harnesses` (and its branches to the tree), then re-run. It writes, to
docs/harness/drawings/, three PDFs `<set>-schematic.pdf`, `<set>-layout.pdf`, `<set>-pinout.pdf`. Each grouped section is its own
page (Dan, 2026-10-25: the single sheets hid the wires). A schematic page holds at most six wires, each in its own line
colour, so one wire can be followed without mixing it up with the one beside it. The label still carries that wire's gauge
and colour. A section that does not fit continues on the next page of that same section; a wire is drawn whole on one page.
Each page has its own title block and rev log.

  1. SCHEMATIC    the wires grouped by job (through the bulkhead, the ECU splice point, cabin branches, shield
                  drains). Every connector, bus, splice and end is a pinout table (pin | signal); every wire is drawn
                  point to point from its pin row to its other pin row on its own track, named on the run and labelled
                  at both ends with its id, gauge, colour and ident bands. A crossing bumps over the other wire. A wire
                  the list says is built with another harness is dashed.
  2. LAYOUT       the approved route drawing for that harness (docs/harness/routes/). Routes 1 and 8-15 are the signed
                  SVG figures (Routes 2-7 removed, Dan 2026-10-26: wrong). Routes 16 and 17 are the approved lines drawn on 1993 EWD p.36. A harness with no route file
                  falls back to the physical tree (front of the car to the right, driver side up): every segment with its
                  length, its wire count and the DR-25 size. Not to scale.
  3. PINOUT       one table per connector, bus, splice and end (never split): every pin, its wire, gauge, colour,
                  bands, signal, other end and estimated cut length; spare pins take a sealing plug.

and, untracked, docs/harness/out/<set>-pinout.xlsx (the same table) and a thumbnail. The PDF carries the digest of its
inputs in its Keywords. Title block and rev log per R200.

The read-back (R224 step 4, R225): --check also reads the committed pinout and schematic PDFs back (PyMuPDF text and
band-chip extraction) and compares every wire with the master: both ends (connector and pin), gauge, colour and ident
bands, plus every spare pin. Any difference fails, whatever the inputs digest says.

    python docs/harness/tools/build_drawings.py [set]          write (needs PyMuPDF + openpyxl)
    python docs/harness/tools/build_drawings.py --check [set]  fail if a drawing set is stale against its inputs, a wire
                                                              end is not on the layout, or the sheets read back differ
                                                              from the master (needs PyMuPDF, CI pins pymupdf==1.28.0)

Nothing on these sheets is placed or typed by hand except the layout tree (node positions, segment lengths) and the
rev log; the scripts never write into the master.
"""
import base64
import collections
import csv
import glob
import hashlib
import html
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(HARNESS))
MASTER = os.path.join(HARNESS, "MASTER-wirelist.csv")
DRAWINGS = os.path.join(HARNESS, "drawings")
OUT = os.path.join(HARNESS, "out")        # untracked (.gitignore): xlsx views, thumbnails

STYLE = "own-drawings v5 (one colour per wire, approved routes)"
PW, PH = 1224.0, 792.0                     # the current page (set_page); a readable page is tabloid, 17 x 11 in
PAGE_MAX_W, PAGE_MAX_H = 1224.0, 792.0     # a section spills onto another page of that section past this size
M = 18.0                                   # page margin
TB_W, TB_H = 372.0, 128.0                  # title block (bottom right)
INK = (0.08, 0.13, 0.24)
GREY = (0.55, 0.57, 0.62)
LIGHT = (0.93, 0.94, 0.96)
AGENT = re.compile(r"claude|grok|stevecad|fairsolid|agent|unknown|cursor|codex", re.I)
WIRE_RGB = {"Red": (0.78, 0.16, 0.16), "Black": (0.1, 0.1, 0.1), "Orange": (0.93, 0.45, 0.0), "Blue": (0.12, 0.38, 0.8),
            "White": (0.55, 0.55, 0.55), "Green": (0.18, 0.55, 0.25), "Yellow": (0.85, 0.68, 0.0), "Shield": (0.45, 0.45, 0.45)}
# One colour per wire on a schematic page. The wire's own colour stays in the label; these exist so two orange wires
# are not the same line. Six, because a page holds six wires.
TRACE = [(0.78, 0.08, 0.12), (0.08, 0.28, 0.82), (0.00, 0.48, 0.22), (0.90, 0.42, 0.00), (0.48, 0.12, 0.66), (0.08, 0.08, 0.08)]
ABBR = {"Red": "RED", "Black": "BLK", "Orange": "ORN", "Blue": "BLU", "White": "WHT", "Green": "GRN", "Yellow": "YEL",
        "Shield": "SCREEN", "": "-"}
BAND_RGB = {"Blue": (0.12, 0.38, 0.8), "Yellow": (0.95, 0.8, 0.1), "White": (1, 1, 1)}
# M22759/16 nominal finished OD (mm) by AWG, for the bundle size (est); a cable core counts as its cable
OD = {24: 1.17, 22: 1.32, 20: 1.57, 18: 1.85, 16: 2.11, 14: 2.41, 12: 2.97, 10: 3.81, 8: 5.08}
CABLE_OD = 4.5
# DR-25 heat-shrink sizes in the part library: (part number, expanded ID, recovered ID) in mm
DR25 = [("DR-25-3/16-0", 4.8, 2.4), ("DR-25-1/4-0", 6.4, 3.2), ("DR-25-3/8-0", 9.53, 4.8), ("DR-25-1/2-0", 12.7, 6.4),
        ("DR-25-3/4-0", 19.0, 9.5), ("DR-25-1-0", 25.4, 12.8), ("DR-25-1-1/2-0", 38.1, 19.0), ("DR-25-2-0", 51.0, 25.4)]


# ------------------------------------------------------------------------------------------------ inputs
def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def master_rows():
    """The master as rows, with the field names the drawing code uses (from_conn = the end ID ...)."""
    with open(MASTER, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for s in ("from", "to"):
            r[s + "_conn"], r[s + "_conn_name"] = r[s + "_id"], r[s + "_name"]
        r["circuit_id"] = r["circuit"]
    return rows


def own_harnesses():
    """Every drawing set: one per tools/<set>.layout.json."""
    return sorted(os.path.basename(p)[:-len(".layout.json")] for p in
                  __import__("glob").glob(os.path.join(HERE, "*.layout.json")))


def pending_harnesses():
    drawn = set()
    for s in own_harnesses():
        drawn |= set(load(os.path.join(HERE, "%s.layout.json" % s)).get("harnesses", [s]))
    return sorted({r["harness"] for r in master_rows()} - drawn)


def set_harnesses(h):
    return load(os.path.join(HERE, "%s.layout.json" % h)).get("harnesses", [h])


def rows_for(h, rows=None):
    """Every wire row of the set (owned by one of its harnesses, or passing through one) plus its spare rows."""
    hs = set(set_harnesses(h))
    out = []
    for r in rows if rows is not None else master_rows():
        if r["wire_id"] and (r["harness"] in hs or hs & set(x.strip() for x in r["passes_through"].split("/"))):
            out.append(r)
        elif not r["wire_id"] and r["harness"] in hs:
            out.append(r)
    return out


SHEETS = [("schematic", "SCH", "Schematic - every wire, grouped by job"),
          ("layout", "LAY", "Layout - top view, segment lengths, wire counts, DR-25 sizes"),
          ("pinout", "PIN", "Pinout tables - every pin of every connector, bus, splice and end")]


def paths(h):
    return {"dir": DRAWINGS, "pdfs": [os.path.join(DRAWINGS, "%s-%s.pdf" % (h, k)) for k, _, _ in SHEETS],
            "xlsx": os.path.join(OUT, "%s-pinout.xlsx" % h), "thumb": os.path.join(OUT, "%s-thumb.png" % h),
            "layout": os.path.join(HERE, "%s.layout.json" % h), "revs": os.path.join(HERE, "%s.revs.json" % h)}


def digest(h):
    """What the drawing set is made from: its master rows, the layout, the rev log, this script."""
    p = paths(h)
    hs = hashlib.sha256()
    with open(MASTER, encoding="utf-8", newline="") as f:
        head = next(csv.reader(f))
    for r in rows_for(h):
        hs.update(json.dumps([r.get(c, "") for c in head], ensure_ascii=False).encode("utf-8"))
    for f in (p["layout"], p["revs"], os.path.abspath(__file__)):
        with open(f, "rb") as fh:
            hs.update(fh.read().replace(b"\r\n", b"\n"))
    hs.update(STYLE.encode())
    return hs.hexdigest()[:16]


def pdf_digest(path):
    """The inputs digest a drawing PDF was made from (its Keywords field), without a PDF library."""
    if not os.path.exists(path):
        return ""
    m = re.search(rb"/Keywords\s*\(inputs ([0-9a-f]{16})\)", open(path, "rb").read())
    return m.group(1).decode() if m else ""


# ------------------------------------------------------------------------------------------------ the model
class Harness:
    def __init__(self, h):
        self.h = h
        self.set = set(set_harnesses(h))
        self.p = paths(h)
        self.layout = load(self.p["layout"])
        self.revs = load(self.p["revs"])
        allrows = master_rows()
        self.rows = rows_for(h, allrows)
        self.wires = [r for r in self.rows if r["wire_id"]]
        self.spares = [r for r in self.rows if not r["wire_id"]]
        # a node's home = the harness whose rows use it most (a node is drawn once, in its home)
        use = collections.defaultdict(collections.Counter)
        self.name, self.housing = {}, {}
        for r in allrows:
            for s in ("from", "to"):
                i = r[s + "_id"]
                if i:
                    use[i][r["harness"]] += 1
                    self.name.setdefault(i, r[s + "_name"])
                    if r[s + "_housing_pn"] and r[s + "_housing_pn"] != "TBD":
                        self.housing.setdefault(i, r[s + "_housing_pn"])
        self.home = {i: sorted(c.items(), key=lambda x: (-x[1], x[0]))[0][0] for i, c in use.items()}
        self.problems = []
        self.tree()

    # --- what an end is ------------------------------------------------------------------------------
    def end_key(self, r, s):
        t, c = r[s + "_type"], r[s + "_conn"]
        if t == "cable screen":
            return ("screen", c)
        if t == "OEM":   # a factory tap is its locator AND its name: two taps on one locator (W1 motor / cowl lead) stay apart
            return ("oem", c + "|" + r[s + "_pin"] + "|" + r[s + "_name"])
        return (t, c)

    def local(self, r, s):
        """True when this end is drawn in this set (else it is the far end on another harness)."""
        t, c = r[s + "_type"], r[s + "_conn"]
        if t == "cable screen":
            return True
        if t == "OEM":
            return r["harness"] in self.set
        return self.home.get(c) in self.set

    def owner_of(self, r, s):
        return self.home.get(r[s + "_conn"], "")

    def kind(self, key):
        t, c = key
        if t == "connector":
            if c.startswith("BUS-"):
                return "bus"
            if c.startswith("ECU-"):
                return "ecu"
            return "conn"
        return {"splice": "splice", "resistor": "part", "diode": "part", "terminal": "term", "oem": "oem",
                "screen": "screen"}.get(t, "conn")

    def title(self, key, r=None, s=None):
        t, c = key
        if t == "oem":
            return (r[s + "_conn_name"] if r else c.split("|")[0])
        if t == "screen":
            return "%s cable screen (floats at the device end)" % c
        nm = (r[s + "_name"] if r is not None else self.name.get(c, "")) or ""
        return "%s - %s" % (c, nm) if nm and not nm.startswith(c) else (nm or c)

    def part_no(self, c):
        return self.housing.get(c, "")

    # --- the layout tree ---------------------------------------------------------------------------------
    def tree(self):
        L = self.layout
        self.adj = {n: [] for n in L["nodes"]}
        for a, b, mm in L["segments"]:
            if a not in self.adj or b not in self.adj:
                self.problems.append("layout segment %s-%s names an unknown node" % (a, b))
                continue
            self.adj[a].append((b, mm))
            self.adj[b].append((a, mm))

    def place(self, r, s):
        t, c = r[s + "_type"], r[s + "_conn"]
        if t == "OEM":
            name = c + " " + r[s + "_conn_name"]
            for pat, node in self.layout.get("place_oem", []):
                if pat in name:
                    return node
            return None
        return self.layout["place"].get(c)

    def path(self, a, b):
        if a == b:
            return [a]
        prev, todo = {a: None}, [a]
        while todo:
            n = todo.pop(0)
            for m, _ in self.adj.get(n, []):
                if m not in prev:
                    prev[m] = n
                    todo.append(m)
        if b not in prev:
            return None
        out = [b]
        while out[-1] != a:
            out.append(prev[out[-1]])
        return out[::-1]

    def seg_len(self, a, b):
        return next(mm for m, mm in self.adj[a] if m == b)

    def route(self, r):
        a, b = self.place(r, "from"), self.place(r, "to")
        for s, n in (("from", a), ("to", b)):
            if n is None:
                self.problems.append("%s: %s end %s %s is not placed on the layout (add it to %s.layout.json place)" % (
                    r["wire_id"], s, r[s + "_type"], r[s + "_conn"], self.h))
        if a is None or b is None:
            return None, None
        p = self.path(a, b)
        if p is None:
            self.problems.append("%s: no layout path from %s to %s" % (r["wire_id"], a, b))
            return None, None
        mm = sum(self.seg_len(x, y) for x, y in zip(p, p[1:])) + 2 * self.layout.get("end_allowance_mm", 100)
        return p, mm


def od(r):
    if r["cable"]:
        return CABLE_OD
    g = r["gauge_awg"]
    return OD.get(int(g), 1.6) if g.isdigit() else 1.6


def dr25_for(bundle_mm):
    for pn, exp, rec in DR25:
        if exp >= bundle_mm * 1.15 and rec <= bundle_mm:
            return pn
    return next((pn for pn, exp, rec in DR25 if exp >= bundle_mm * 1.15), DR25[-1][0])


# ------------------------------------------------------------------------------------------------ checks
def check(h):
    H = Harness(h)
    bad = list(H.problems)
    for r in H.wires:
        H.route(r)
    bad += [x for x in H.problems if x not in bad]
    revs = H.revs.get("revs", [])
    if not revs or revs[0].get("rev") != "A":
        bad.append("rev log has no Rev A (R200)")
    for rv in revs:
        if not rv.get("by", "").strip() or AGENT.search(rv.get("by", "")):
            bad.append("rev %s BY %r is blank or an agent name (R200: the requester's initials)" % (rv.get("rev"), rv.get("by")))
    want = digest(h)
    for p in H.p["pdfs"]:
        have = pdf_digest(p)
        if have != want:
            bad.append("%s is stale (inputs %s, made from %s): run build_drawings.py %s"
                       % (os.path.basename(p), want, have or "none", h))
    for name in wirelist_harnesses(H):
        have, want_wl = xlsx_digest(wirelist_path(name)), wirelist_digest(H, name)
        if have != want_wl:
            bad.append("%s is stale (inputs %s, made from %s): run build_drawings.py %s"
                       % (os.path.basename(wirelist_path(name)), want_wl, have or "none", h))
        else:
            bad += wirelist_readback(name)
    for p in glob.glob(os.path.join(DRAWINGS, "%s-*.pdf" % h)):
        if p not in H.p["pdfs"]:
            bad.append("%s is not one of the three sheets of the set (delete it)" % os.path.basename(p))
    return bad + readback(H)


# ------------------------------------------------------------------------------------------------ read-back (R224 step 4)
GREY_INT = (round(GREY[0] * 255) << 16) | (round(GREY[1] * 255) << 8) | round(GREY[2] * 255)
CUT = "..."                                # what Sheet.fit leaves at the end of a cut text


def _spans(page):
    """Every text span on a sheet: (x, baseline y, x end, size, bold, grey, text)."""
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                t = "".join(c["c"] for c in s["chars"]).strip()
                if t:
                    out.append((s["origin"][0], s["origin"][1], s["bbox"][2], round(s["size"], 1), "Bold" in s["font"],
                                s["color"] == GREY_INT, t))
    return out


def _chips(page):
    """Every ident-band chip on a sheet: (x0, y1, colour name), from the filled 4.2 pt squares band_chips draws."""
    names = {tuple(round(c, 2) for c in v): k for k, v in BAND_RGB.items()}
    out = []
    for d in page.get_drawings():
        r, f = d.get("rect"), d.get("fill")
        if f and r is not None and abs(r.width - 4.2) < 0.3 and abs(r.height - 4.2) < 0.3:
            k = names.get(tuple(round(c, 2) for c in f))
            if k:
                out.append((r.x0, r.y1, k))
    return out


def _bands_at(chips, x0, x1, y):
    return "-".join(k for x, yy, k in sorted(c for c in chips if x0 <= c[0] < x1 and abs(c[1] - y) < 0.6))


def _names_end(title, r, s):
    """Does a table / block title name this end of master row r? Connector, splice and part titles start with the end ID;
    a factory tap's title is its name (a title cut short on the sheet ends in '...')."""
    title = re.sub(r"\s+\(on ST185-[^)]*\)$", "", title)
    if r[s + "_type"] == "OEM":
        name = r[s + "_name"]
        return title == name or (title.endswith(CUT) and name.startswith(title[:-len(CUT)]))
    return title == r[s + "_id"] or title.startswith(r[s + "_id"] + " ")


def _same_or_cut(seen, want):
    return seen == want or (seen.endswith(CUT) and want.startswith(seen[:-len(CUT)]))


def _read_pinout(path, fitz):
    """Every pinout page read back: one dict per table row (the table title plus every column), from the text alone."""
    doc = fitz.open(path)
    rows, bad = [], []
    for page in doc:
        got, page_bad = _read_pinout_page(page)
        rows.extend(got)
        bad.extend(page_bad)
    doc.close()
    return rows, bad


def _read_pinout_page(page):
    """One pinout page."""
    sp, chips = _spans(page), _chips(page)
    names = [n for n, _ in TABLE_COLS]
    heads = [s for s in sp if s[4] and s[3] == 5.4 and s[6] == names[0]]
    titles = [s for s in sp if s[4] and s[3] == 7.0]
    frames = [d["rect"] for d in page.get_drawings() if d.get("rect") is not None and not d.get("fill") and d["rect"].width > 200]
    rows, bad = [], []
    for hx, hy, *_ in heads:
        # the table's own column headers are the first ones from its PIN header rightward; it ends with its last column
        cand = sorted((s[0], s[6]) for s in sp if s[4] and s[3] == 5.4 and abs(s[1] - hy) < 0.3 and s[0] >= hx - 0.5)
        cols = cand[:len(names)]
        right = cols[-1][0] + dict(PIN_COLS)[names[-1]] + 4
        above = [t for t in titles if abs(t[0] - hx) < 0.5 and t[1] < hy]
        below = [t[1] for t in titles if abs(t[0] - hx) < 0.5 and t[1] > hy]
        if [c[1] for c in cols] != names or not above:
            bad.append("pinout sheet: a table at x %.0f y %.0f has columns %s, not %s" % (hx, hy, [c[1] for c in cols], names))
            continue
        title = max(above, key=lambda t: t[1])[6]
        box = [f for f in frames if abs(f.x0 + 4 - hx) < 0.6 and f.y0 < hy < f.y1]     # the table's own frame ends it
        stop = min([f.y1 for f in box] + below + [page.rect.height])
        xs = [c[0] for c in cols]
        cells = collections.defaultdict(dict)
        for x, y, *_rest in sp:
            text = _rest[-1]
            if hy + 0.5 < y < stop - 1 and xs[0] - 0.5 <= x < right:
                i = max(j for j, cx in enumerate(xs) if cx <= x + 0.5)
                cells[round(y, 1)][names[i]] = (cells[round(y, 1)].get(names[i], "") + " " + text).strip()
        bx = names.index("BANDS")
        for y in sorted(cells):
            row = {n: cells[y].get(n, "") for n in names}
            row["BANDS"] = _bands_at(chips, xs[bx] - 0.5, xs[bx + 1], y)
            row["_table"], row["_y"] = title, y
            rows.append(row)
    return rows, bad


def _read_schematic(path, fitz):
    """Every schematic page read back: the wire labels (id, gauge, colour, bands) and every pinout-block row (block title,
    pin, wire id)."""
    doc = fitz.open(path)
    labels, ends = [], []
    for page in doc:
        lab, end = _read_schematic_page(page)
        labels.extend(lab)
        ends.extend(end)
    doc.close()
    return labels, ends


def _read_schematic_page(page):
    """One schematic page."""
    sp, chips = _spans(page), _chips(page)
    labels = []
    for x, y, xe, size, bold, grey, t in sp:
        if size == 5.0 and not bold and not grey:
            labels.append((t, _bands_at(chips, xe, xe + 4.8 * 4 + 4, y + 0.4)))
    titles = [s for s in sp if s[4] and s[3] == 6.5]
    pins = [s for s in sp if s[4] and s[3] == 6.0]
    ends = []
    for x, y, xe, size, bold, grey, t in sp:
        if size == 5.0 and grey and not bold:
            pin = [p for p in pins if abs(p[1] - y) < 0.3 and x - 220 < p[0] < x]
            if not pin:
                continue
            px = max(pin, key=lambda p: p[0])
            above = [s for s in titles if abs(s[0] - px[0]) < 0.5 and s[1] < y]
            if above:
                ends.append((t, max(above, key=lambda s: s[1])[6], "" if px[6] == "-" else px[6]))
    return labels, ends


def readback(H):
    """R224 step 4: read the committed pinout and schematic sheets back and compare every wire with the master."""
    try:
        import fitz
    except ImportError:
        return ["read-back needs PyMuPDF (python -m pip install pymupdf==1.28.0)"]
    pin_pdf, sch_pdf = H.p["pdfs"][2], H.p["pdfs"][0]
    if not (os.path.exists(pin_pdf) and os.path.exists(sch_pdf)):
        return ["read-back: the pinout / schematic sheet is missing: run build_drawings.py %s" % H.h]
    bad = []
    prows, pbad = _read_pinout(pin_pdf, fitz)
    bad += pbad
    labels, ends = _read_schematic(sch_pdf, fitz)
    ids = {r["wire_id"] for r in H.wires}
    by_wire = collections.defaultdict(list)
    for row in prows:
        by_wire[row["WIRE"]].append(row)
    lab_by = collections.defaultdict(list)
    for t, bands in labels:
        lab_by[t.split()[0]].append((t, bands))
    end_by = collections.defaultdict(list)
    for t, title, pin in ends:
        if t.endswith(CUT):
            hit = [i for i in ids if i.startswith(t[:-len(CUT)])]
            t = hit[0] if len(hit) == 1 else t
        end_by[t].append((title, pin))
    for r in H.wires:
        w = r["wire_id"]
        bands, gauge, colour = r["ident_bands"], r["gauge_awg"], r["colour"]
        # pinout sheet: one row per end, in that end's table, at its pin
        got = list(by_wire.get(w, []))
        for s, o in (("from", "to"), ("to", "from")):
            where = "%s %s pin %s" % (s, r[s + "_id"], r[s + "_pin"] or "-")
            hit = next((x for x in got if _names_end(x["_table"], r, s) and x["PIN"] == r[s + "_pin"]), None)
            if hit is None:
                bad.append("%s: pinout sheet has no row for its %s end (sheet rows: %s)" % (
                    w, where, ["%s / pin %s" % (x["_table"][:40], x["PIN"] or "-") for x in got] or "none"))
                continue
            got.remove(hit)
            for col, want in (("AWG", gauge), ("COLOUR", colour), ("BANDS", bands)):
                if hit[col] != want:
                    bad.append("%s: pinout sheet %s %s %r, master %r" % (w, where, col, hit[col], want))
            other = (r[o + "_name"] or r[o + "_id"]) + ((" pin " + r[o + "_pin"]) if r[o + "_pin"] else "")
            if not _same_or_cut(hit["OTHER END"], other):
                bad.append("%s: pinout sheet %s OTHER END %r, master %r" % (w, where, hit["OTHER END"], other))
        for x in got:
            bad.append("%s: pinout sheet has an extra row in %s pin %s" % (w, x["_table"][:40], x["PIN"] or "-"))
        # schematic sheet: a label at each end (id, gauge, colour, bands) and a row in each end's block at its pin
        want_lab = ("%s  screen" % w) if colour == "Shield" else ("%s  %s %s" % (w, gauge, ABBR.get(colour, colour[:3].upper())))
        labs = lab_by.get(w, [])
        if len(labs) != 2 or any(" ".join(t.split()) != " ".join(want_lab.split()) or b != bands for t, b in labs):
            bad.append("%s: schematic wire labels %s, master %r + bands %r (one at each end)" % (w, labs, want_lab, bands))
        seen = list(end_by.get(w, []))
        for s in ("from", "to"):
            hit = next((x for x in seen if _names_end(x[0], r, s) and x[1] == r[s + "_pin"]), None)
            if hit is None:
                bad.append("%s: schematic has no row for its %s end %s pin %s (sheet rows: %s)" % (
                    w, s, r[s + "_id"], r[s + "_pin"] or "-", seen or "none"))
            else:
                seen.remove(hit)
        for x in seen:
            bad.append("%s: schematic has an extra end row %s pin %s" % (w, x[0][:40], x[1] or "-"))
    for w in sorted(set(by_wire) - ids - {""}):
        bad.append("%s: on the pinout sheet but not a wire of the set in the master" % w)
    for w in sorted(set(lab_by) - ids):
        bad.append("%s: wire label on the schematic but not a wire of the set in the master" % w)
    for w in sorted(set(end_by) - ids):
        bad.append("%s: schematic block row but not a wire of the set in the master" % w)
    # spare pins: each one a row with no wire in its end's table
    spare_rows = list(by_wire.get("", []))
    for r in H.spares:
        hit = next((x for x in spare_rows if _names_end(x["_table"], r, "from") and x["PIN"] == r["from_pin"]), None)
        if hit is None:
            bad.append("spare %s pin %s: no spare row on the pinout sheet" % (r["from_id"], r["from_pin"]))
        else:
            spare_rows.remove(hit)
    for x in spare_rows:
        bad.append("pinout sheet: %s pin %s has no wire, and the master has no spare row for it" % (x["_table"][:40], x["PIN"]))
    if len(bad) > 60:
        bad = bad[:60] + ["read-back: %d more finding(s) not shown" % (len(bad) - 60)]
    print("   read-back: %d wires, %d spares; pinout sheet %d rows, schematic %d labels / %d end rows: %s"
          % (len(H.wires), len(H.spares), len(prows), len(labels), len(ends), "OK" if not bad else "%d finding(s)" % len(bad)))
    return ["read-back: " + b for b in bad]


# ------------------------------------------------------------------------------------------------ drawing helpers
class Sheet:
    def __init__(self, doc, fitz):
        self.fitz = fitz
        self.page = doc.new_page(width=PW, height=PH)
        self.doc = doc

    def text(self, x, y, s, size=6.5, font="helv", color=INK, align=0, w=None):
        """Single line at baseline y. align: 0 left, 1 centre, 2 right (w = box width for 1 / 2)."""
        if w is not None and align:
            tw = self.fitz.get_text_length(s, fontname=font, fontsize=size)
            x = x + (w - tw) / (2 if align == 1 else 1)
        self.page.insert_text((x, y), s, fontsize=size, fontname=font, color=color)

    def tl(self, s, size=6.5, font="helv"):
        return self.fitz.get_text_length(s, fontname=font, fontsize=size)

    def fit(self, s, w, size=6.5, font="helv"):
        if self.tl(s, size, font) <= w:
            return s
        while s and self.tl(s + "...", size, font) > w:
            s = s[:-1]
        return s + "..."

    def rect(self, x0, y0, x1, y1, color=INK, fill=None, width=0.6):
        self.page.draw_rect(self.fitz.Rect(x0, y0, x1, y1), color=color, fill=fill, width=width)

    def line(self, pts, color=INK, width=0.6, dashes=None):
        sh = self.page.new_shape()
        for a, b in zip(pts, pts[1:]):
            sh.draw_line(a, b)
        sh.finish(color=color, width=width, dashes=dashes, closePath=False)
        sh.commit()

    def dot(self, x, y, r=1.6, color=INK):
        self.page.draw_circle((x, y), r, color=color, fill=color)


def title_block(S, H, sheet_no, sheets, what, dwg=""):
    revs = H.revs["revs"]
    cur = revs[-1]
    x0, y0 = PW - M - TB_W, PH - M - TB_H
    S.rect(x0, y0, PW - M, PH - M, width=1.0)
    # rev log (top part)
    rh = 9.0
    S.rect(x0, y0, PW - M, y0 + 12, fill=LIGHT)
    S.text(x0 + 4, y0 + 8.5, "REVISIONS", 6.5, "hebo")
    cols = [(x0 + 4, "REV"), (x0 + 30, "DATE"), (x0 + 80, "BY"), (x0 + 104, "DESCRIPTION")]
    y = y0 + 21
    for x, s in cols:
        S.text(x, y, s, 5.5, "hebo")
    for rv in revs[-4:]:
        y += rh
        S.text(cols[0][0], y, rv["rev"], 6)
        S.text(cols[1][0], y, rv["date"], 6)
        S.text(cols[2][0], y, rv["by"], 6)
        S.text(cols[3][0], y, S.fit(rv["what"], PW - M - cols[3][0] - 4, 6), 6)
    yb = y0 + 66
    S.line([(x0, yb), (PW - M, yb)], width=0.8)
    S.text(x0 + 4, yb + 12, S.fit(H.revs["title"], TB_W - 8, 9, "hebo"), 9, "hebo")
    S.text(x0 + 4, yb + 22, S.fit(what, TB_W - 8, 6.5), 6.5)
    S.line([(x0, yb + 27), (PW - M, yb + 27)], width=0.5)
    cells = [("DRAWING NO.", "%s%s" % (H.h if H.h.startswith("ST185-") else "ST185-" + H.h, dwg), 110), ("REV", cur["rev"], 30), ("SHEET", "%d OF %d" % (sheet_no, sheets), 52),
             ("SIZE", "%d x %d mm" % (round(PW / 72 * 25.4), round(PH / 72 * 25.4)), 64), ("DRAWN", revs[0]["by"], 34),
             ("DATE", cur["date"], 82)]
    x = x0
    for lab, val, w in cells:
        S.text(x + 3, yb + 34, lab, 4.8, "hebo", GREY)
        S.text(x + 3, yb + 45, val, 7.5, "hebo")
        x += w
        if x < PW - M - 1:
            S.line([(x, yb + 27), (x, yb + 50)], width=0.4)
    S.line([(x0, yb + 50), (PW - M, yb + 50)], width=0.5)
    S.text(x0 + 4, yb + 58, S.fit("ST185 Celica (living-relation) - generated by docs/harness/tools/build_drawings.py from "
                                  "docs/harness/MASTER-wirelist.csv; not to scale", TB_W - 8, 5), 5, color=GREY)
    # frame
    S.rect(M, M, PW - M, PH - M, width=1.2)


def band_chips(S, x, y, bands):
    for b in bands:
        S.rect(x, y - 4.2, x + 4.2, y, color=INK, fill=BAND_RGB.get(b, (1, 1, 1)), width=0.3)
        x += 4.8
    return x


# ------------------------------------------------------------------------------------------------ 1. layout sheet
def layout_keep(H, harness):
    """Nodes, segments and end ids the wires of one harness actually run through."""
    nodes, segs, ends = set(), set(), set()
    for r in H.wires:
        if r["harness"] != harness:
            continue
        for s in ("from", "to"):
            if r[s + "_conn"]:
                ends.add(r[s + "_conn"])
        p, _mm = H.route(r)
        if not p:
            continue
        nodes.update(p)
        for a, b in zip(p, p[1:]):
            segs.add(tuple(sorted((a, b))))
    return nodes, segs, ends


def layout_page_size(n_nodes, n_seg):
    """Tabloid, grown only so the segment table ends above the title block."""
    ty = M + 50 + 11 + 8.5 * n_seg + 14 + 8 * n_nodes + 14 + 7.5 * 8
    return 1224.0, max(792.0, ty + 24 + TB_H + M)


def layout_sheet(S, H, harness=None, keep_nodes=None, keep_segs=None, keep_ends=None):
    L = H.layout
    nodes = L["nodes"] if keep_nodes is None else {k: v for k, v in L["nodes"].items() if k in keep_nodes}
    seg_src = L["segments"] if keep_segs is None else [s for s in L["segments"] if tuple(sorted((s[0], s[1]))) in keep_segs]
    wires = H.wires if harness is None else [r for r in H.wires if r["harness"] == harness]
    seg_od = {}
    count = {}
    for r in wires:
        p, mm = H.route(r)
        if not p:
            continue
        for a, b in zip(p, p[1:]):
            k = tuple(sorted((a, b)))
            count[k] = count.get(k, 0) + 1
            seg_od[k] = seg_od.get(k, 0.0) + od(r) ** 2
    # drawing area: the left of the sheet; the 0-100 frame is stretched to it on each axis (not to scale)
    ax0, ay0, ax1, ay1 = M + 40, M + 70, PW - M - 500, PH - M - 50
    xs = [v["xy"][0] for v in nodes.values()]
    ys = [v["xy"][1] for v in nodes.values()]
    sx = (ax1 - ax0) / (max(xs) - min(xs) or 1)
    sy = (ay1 - ay0) / (max(ys) - min(ys) or 1)

    def at(n):
        x, y = nodes[n]["xy"]
        # top view: +x = toward the front (right), +y = driver side (up on the sheet)
        return (ax0 + (x - min(xs)) * sx, ay1 - (y - min(ys)) * sy)

    head = ("LAYOUT - ST185-%s - " % harness) if harness else "LAYOUT - "
    head += "top view, front of the car to the RIGHT, driver side UP (R140 / R153). Not to scale; lengths in mm (estimates until measured at the car)."
    S.text(M + 8, M + 16, S.fit(head, PW - 2 * M - 16, 8, "hebo"), 8, "hebo")
    S.text(M + 8, M + 27, "Each segment: length | wires in it | DR-25 heat-shrink size for its bundle (est. from the wire ODs). "
           "Lengths per wire (path + %d mm at each end) are in the pinout table." % L.get("end_allowance_mm", 100), 6.5)
    S.text(ax1 - 40, M + 50, "FRONT  -->", 7, "hebo", GREY)
    S.text(M + 8, M + 50, "^ DRIVER SIDE (LH) at the top  /  PASSENGER SIDE (RH) at the bottom v", 6.5, "hebo", GREY)
    table = []
    for a, b, mm in seg_src:
        k = tuple(sorted((a, b)))
        n = count.get(k, 0)
        bundle = 1.2 * math.sqrt(seg_od.get(k, 0.0)) if n else 0
        cov = dr25_for(bundle) if n else "-"
        (x0, y0), (x1, y1) = at(a), at(b)
        S.line([(x0, y0), (x1, y1)], color=(0.35, 0.37, 0.42), width=max(1.2, min(9.0, 1.0 + n * 0.12)))
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        lab = "%d mm | %d | %s" % (mm, n, cov.replace("-0", "").replace("DR-25-", "DR25 "))
        w = S.tl(lab, 5.8, "hebo")
        S.rect(mx - w / 2 - 2, my - 6, mx + w / 2 + 2, my + 2.5, color=None, fill=(1, 1, 1))
        S.text(mx - w / 2, my, lab, 5.8, "hebo")
        table.append((a, b, mm, n, "%.1f" % bundle if n else "-", cov))
    placed = {}
    for c, n in L["place"].items():
        placed.setdefault(n, []).append(c)
    for n, v in nodes.items():
        x, y = at(n)
        if v.get("end"):
            S.rect(x - 4, y - 4, x + 4, y + 4, fill=(1, 1, 1), width=1.0)
        else:
            S.dot(x, y, 2.4)
        head = S.fit("%s  %s" % (n, v.get("short", v["label"])), 200, 6.5, "hebo")
        names = sorted({short_name(H, c) for c in placed.get(n, []) if keep_ends is None or c in keep_ends})
        lines = wrap(S, ", ".join(names), 190, 5.2)[:3] if names else []
        side = v.get("lab", "right")
        w = max([S.tl(head, 6.5, "hebo")] + [S.tl(ln, 5.2) for ln in lines])
        lx, ly = {"right": (x + 7, y - 4), "left": (x - 7 - w, y - 4), "below": (x - 10, y + 14),
                  "above": (x - 10, y - 12 - 6 * len(lines))}[side]
        S.rect(lx - 1.5, ly - 7, lx + w + 1.5, ly + 1.5 + 6 * len(lines), color=None, fill=(1, 1, 1))
        S.text(lx, ly, head, 6.5, "hebo")
        for i, ln in enumerate(lines):
            S.text(lx, ly + 7 + i * 6, ln, 5.2, color=GREY)
    # segment table on the right
    tx = PW - M - 360
    ty = M + 50
    S.text(tx, ty, "SEGMENTS", 7.5, "hebo")
    heads = [("FROM", 0), ("TO", 62), ("MM", 124), ("WIRES", 150), ("BUNDLE", 178), ("DR-25", 214)]
    ty += 11
    for s, dx in heads:
        S.text(tx + dx, ty, s, 5.5, "hebo")
    for a, b, mm, n, bd, cov in table:
        ty += 8.5
        for s, dx in ((a, 0), (b, 62), (str(mm), 124), (str(n), 150), (bd, 178), (cov, 214)):
            S.text(tx + dx, ty, s, 5.8)
    ty += 14
    S.text(tx, ty, "NODES", 7.5, "hebo")
    for n, v in nodes.items():
        ty += 8
        S.text(tx, ty, S.fit("%s  %s" % (n, v["label"]), 300, 5.5), 5.5)
    ty += 14
    for ln in wrap(S, "The ECU splice point (SP) is ONE place by the ECU plugs (Dan 2026-10-19): +5 V on BUS-5V + BUS-5V-2, "
                      "Gnd Out A24 on BUS-GNDOUT-A, B22 on BUS-GNDOUT-B (bussed DEUTSCH DT, DECISIONS R169 parts), +8 V, switched "
                      "12 V, the A5 feed and the ECU power ground soldered there. The ECU ground runs alone to the POWER box NEG bar "
                      "(R216).", 300, 5.8):
        S.text(tx, ty, ln, 5.8)
        ty += 7.5


def short_name(H, c):
    """The short drawn name of a node: SP- / BUS- token of a splice, the tag of a connector, else its id."""
    return c


def wrap(S, s, w, size, font="helv"):
    out, cur = [], ""
    for word in s.split(" "):
        t = (cur + " " + word).strip()
        if S.tl(t, size, font) <= w:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------ 2. schematic sheets
GROUPS = [("bulkhead", "THROUGH THE BULKHEAD - every wire that lands on the DRB102 (signals, sensor rails, feeds)"),
          ("power", "ECU SPLICE POINT - power, grounds and sensor rails (bussed DT plugs, soldered splices, NEG bar)"),
          ("cabin", "CABIN BRANCHES - pedal, wheel-speed inlines, fuel level, A/C, IG2 / start taps, relay coils, other harnesses"),
          ("shield", "SHIELD DRAINS - screens to A7 / B17 (R207), CAN screen to the CAN trunk")]
AB = ("AB-cabin", "AB-engine")   # the ECU harness (R220): its cabin wires are drawn by job, its engine wires as one panel
ROW_H = 8.6
HEAD_H = 19.0
GAP_B = 7.0
COL_TOP = M + 44
COL_BOT = PH - M - TB_H - 8


def set_page(w, h, title_block=True):
    """Every drawing function reads the page size from these globals; set them before drawing a page."""
    global PW, PH, COL_BOT, LEFT_BOT, RIGHT_BOT
    PW, PH = float(w), float(h)
    COL_BOT = PH - M - TB_H - 8
    LEFT_BOT = PH - M - 54
    RIGHT_BOT = (PH - M - TB_H - 8) if title_block else LEFT_BOT


def group_of(H, r):
    """The schematic panel of a wire: the ECU harness's cabin wires by job (GROUPS), every other harness one panel each
    (`h:<harness>`, titled from the layout's `panel_titles`)."""
    if r["harness"] not in AB[:1]:
        return "h:" + r["harness"]
    ends = [(r[s + "_type"], r[s + "_conn"]) for s in ("from", "to")]
    if r["colour"] == "Shield" or r["circuit_id"] == "SHLD" or (re.search(r"screen|shield|drain", r["from_desc"] + r["to_desc"], re.I)
                                                               and r["colour"] in ("Black", "Shield")):
        return "shield"
    kinds = {H.kind(H.end_key(r, s)) for s in ("from", "to")}
    power = "bus" in kinds or any(c in ("SP-8V", "SP-SW12", "SP-A5", "SP-GND-ECU", "D-IG2-WAKE", "POWER-NEG-BAR")
                                  for _, c in ends)
    if power and not any(c == "DRB102-CABIN" for _, c in ends):
        return "power"
    if any(c in ("DRB102-CABIN", "DRB102-ENGINE") for _, c in ends):
        return "bulkhead"
    return "cabin"


def side_of(H, key):
    """0 = left column (ECU plugs and the splice-type nodes), 1 = right column (everything else)."""
    return 0 if H.kind(key) in ("ecu", "bus", "splice", "part") else 1


def pin_sort(p):
    m = re.match(r"([A-Za-z +/-]*?)(\d+)(.*)", p or "")
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (p or "", 0, "")


class Block:
    def __init__(self, key, title, sub, ext):
        self.key, self.title, self.sub, self.ext = key, title, sub, ext
        self.rows = []      # (pin, desc, rowid)
        self.y = 0.0
        self.x0 = self.x1 = 0.0

    def height(self):
        return HEAD_H + ROW_H * len(self.rows)


def choose_sides(H, rows):
    """Block -> 0 (left column) / 1 (right column), so that as many wires as possible run across the centre: a local
    max-cut from a start of ECU plugs and splice-type nodes on the left. The ECU plugs end up on the left."""
    keys = {}
    edges = []
    for r in rows:
        a, b = H.end_key(r, "from"), H.end_key(r, "to")
        keys[a] = keys[b] = None
        edges.append((a, b))
    side = {k: side_of(H, k) for k in keys}
    for _ in range(30):
        moved = False
        for k in sorted(keys, key=lambda k: order_key(H, k)):
            same = sum(1 for a, b in edges if k in (a, b) and side[a] == side[b] and a != b)
            cross = sum(1 for a, b in edges if k in (a, b) and side[a] != side[b])
            if same > cross:
                side[k] = 1 - side[k]
                moved = True
        if not moved:
            break
    ecu = [side[k] for k in side if H.kind(k) == "ecu"]
    if ecu and sum(ecu) * 2 > len(ecu):
        side = {k: 1 - v for k, v in side.items()}
    return side


LEFT_BOT = PH - M - 54          # the left column runs down to the legend
RIGHT_BOT = PH - M - TB_H - 8   # the right column stops above the title block


LANE = 92.0      # label lane beside a table: id, gauge, colour, bands
TRK = 16.0       # track pitch in the outer channels
STEP = 16.0      # minimum centre-track pitch; a page holds few wires so the real gap is wider
LW, RW = 200.0, 214.0
MAX_SCH_WIRES = 6   # more than this and same-colour wires cannot be followed through the channel


def section_order(H):
    """Schematic / pinout sections: the ECU cabin job groups, then one section per other harness."""
    titles = H.layout.get("panel_titles", {})
    order = list(GROUPS)
    rest = [x for x in AB if x != AB[0]] + sorted({r["harness"] for r in H.rows} - set(AB))
    for name in rest:
        order.append(("h:" + name, titles.get(name, "ST185-%s - every wire of this harness" % name).upper()))
    return order


def row_group(H, r):
    """The section a pinout row belongs to. AB-cabin spare pins sit on the cabin page."""
    if r["wire_id"]:
        return group_of(H, r)
    return "cabin" if r["harness"] == AB[0] else "h:" + r["harness"]


def arrange_schematic(H, rows):
    """Column positions and a track per wire. Track assignment depends on the row heights, not on the page width."""
    bl = blocks_for(H, rows)
    sides = choose_sides(H, rows)
    left = sorted([b for k, b in bl.items() if sides[k] == 0], key=lambda b: order_key(H, b.key))
    right = [b for k, b in bl.items() if sides[k] == 1]
    y = COL_TOP
    for b in left:
        b.y = y
        y += b.height() + GAP_B
    rowy = {}
    for b in left:
        for j, (pin, desc, rid) in enumerate(b.rows):
            rowy[rid] = b.y + HEAD_H + ROW_H * (j + 0.5)
    partner = {}
    for r in rows:
        for s, o in (("from", "to"), ("to", "from")):
            if (r["wire_id"], o) in rowy:
                partner.setdefault(H.end_key(r, s), []).append(rowy[(r["wire_id"], o)])
    right.sort(key=lambda b: (sum(partner.get(b.key, [1e6])) / len(partner.get(b.key, [1])), order_key(H, b.key)))
    y = COL_TOP
    for b in right:
        b.y = y
        y += b.height() + GAP_B
    for b in right:
        for j, (pin, desc, rid) in enumerate(b.rows):
            rowy[rid] = b.y + HEAD_H + ROW_H * (j + 0.5)
    blk = {rid: b for b in left + right for pin, desc, rid in b.rows}
    jobs = []
    for r in rows:
        a, z = blk[(r["wire_id"], "from")], blk[(r["wire_id"], "to")]
        ya, yz = rowy[(r["wire_id"], "from")], rowy[(r["wire_id"], "to")]
        sa, sz = sides[a.key], sides[z.key]
        jobs.append(["C" if sa != sz else ("L" if sa == 0 else "R"), r, a, z, ya, yz, 0])
    ntr = {}
    for ch in ("C", "L", "R"):
        js = sorted([j for j in jobs if j[0] == ch], key=lambda j: (min(j[4], j[5]), max(j[4], j[5])))
        ends = []
        for j in js:
            lo, hi = min(j[4], j[5]) - 2.5, max(j[4], j[5]) + 2.5
            t = next((ti for ti, e in enumerate(ends) if e < lo), None)
            if t is None:
                ends.append(hi)
                t = len(ends) - 1
            else:
                ends[t] = hi
            j[6] = t
        ntr[ch] = len(ends)
    return {"left": left, "right": right, "jobs": jobs, "ntr": ntr, "sides": sides}


def schematic_need(lay):
    """Page size that keeps centre tracks at STEP. Not clamped to the readable page."""
    ntr = lay["ntr"]
    outer_l = (ntr["L"] * TRK + 8 + LANE) if ntr["L"] else 0
    outer_r = (ntr["R"] * TRK + 8 + LANE) if ntr["R"] else 0
    center = (ntr["C"] + 1) * STEP if ntr["C"] else 36.0
    w = 2 * (M + 8) + outer_l + outer_r + LW + RW + 2 * LANE + center
    content = COL_TOP
    for b in lay["left"] + lay["right"]:
        content = max(content, b.y + b.height())
    return w, content + 36 + TB_H + M


def pack_schematic(H, rows):
    """Split one section into pages that stay inside the readable sheet. Each page draws its wires whole."""
    ordered = sorted(rows, key=lambda r: (r["from_id"], pin_sort(r["from_pin"]), r["to_id"], r["wire_id"]))
    pages, cur = [], []
    for r in ordered:
        trial = cur + [r]
        w, h = schematic_need(arrange_schematic(H, trial))
        if cur and (len(trial) > MAX_SCH_WIRES or w > PAGE_MAX_W + 0.5 or h > PAGE_MAX_H + 0.5):
            pages.append(cur)
            cur = [r]
        else:
            cur = trial
    if cur:
        pages.append(cur)
    return pages


def schematic_sheet(S, H, title, i, n, rows, lay=None, with_legend=True):
    if lay is None:
        lay = arrange_schematic(H, rows)
    left, right = lay["left"], lay["right"]
    jobs, ntr, sides = lay["jobs"], lay["ntr"], lay["sides"]
    outer_l = (ntr["L"] * TRK + 8 + LANE) if ntr["L"] else 0
    outer_r = (ntr["R"] * TRK + 8 + LANE) if ntr["R"] else 0
    lx0 = M + 8 + outer_l
    rx1 = PW - M - 8 - outer_r
    rx0 = rx1 - RW
    for b in left:
        b.x0, b.x1 = lx0, lx0 + LW
    for b in right:
        b.x0, b.x1 = rx0, rx1
    for b in left + right:
        draw_block(S, H, b)
    cx0, cx1 = lx0 + LW + LANE, rx0 - LANE
    step = (cx1 - cx0) / (ntr["C"] + 1) if ntr["C"] else STEP
    if ntr["C"] and step < STEP - 0.05:
        print("PROBLEM centre tracks %.2f pt apart on %s (need %.1f)" % (step, title, STEP))
    drawn = []
    for ch, r, a, z, ya, yz, t in jobs:
        if ch == "C":
            tx = cx0 + step * (t + 1)
        elif ch == "L":
            tx = lx0 - LANE - 6 - TRK * t
        else:
            tx = rx1 + LANE + 6 + TRK * t
        drawn.append((ch, r, a, z, ya, yz, tx))
    for i, (ch, r, a, z, ya, yz, tx) in enumerate(drawn):
        dashed = "[3 2] 0" if r["harness"] not in H.set else None
        col = TRACE[i % len(TRACE)]
        width = 1.6 if r["colour"] != "Shield" else 1.15
        others = [ox for och, _or, _oa, _oz, _oya, _oyz, ox in drawn if och == ch and abs(ox - tx) > 0.5]
        if ch == "C":
            (la, ly), (lz, lyz) = ((a, ya), (z, yz)) if sides[a.key] == 0 else ((z, yz), (a, ya))
            jump_run(S, la.x1, ly, tx, ly, others, col, width, dashed)
            stroke(S, [(tx, ly), (tx, lyz)], col, width, dashed)
            jump_run(S, tx, lyz, lz.x0, lyz, others, col, width, dashed)
            wire_id_on(S, r["wire_id"], tx, ly, lyz, col)
            wire_label(S, r, la.x1 + 3, ly - 1.4)
            wire_label(S, r, lz.x0 - LANE + 3, lyz - 1.4)
        elif ch == "L":
            jump_run(S, a.x0, ya, tx, ya, others, col, width, dashed)
            stroke(S, [(tx, ya), (tx, yz)], col, width, dashed)
            jump_run(S, tx, yz, z.x0, yz, others, col, width, dashed)
            wire_id_on(S, r["wire_id"], tx, ya, yz, col)
            wire_label(S, r, a.x0 - LANE + 3, ya - 1.4)
            wire_label(S, r, z.x0 - LANE + 3, yz - 1.4)
        else:
            jump_run(S, a.x1, ya, tx, ya, others, col, width, dashed)
            stroke(S, [(tx, ya), (tx, yz)], col, width, dashed)
            jump_run(S, tx, yz, z.x1, yz, others, col, width, dashed)
            wire_id_on(S, r["wire_id"], tx, ya, yz, col)
            wire_label(S, r, a.x1 + 3, ya - 1.4)
            wire_label(S, r, z.x1 + 3, yz - 1.4)
    S.text(M + 8, M + 16, S.fit("%s%s" % (title, "" if n == 1 else "  (part %d of %d)" % (i, n)), PW - 2 * M - 16, 8, "hebo"), 8, "hebo")
    if with_legend:
        legend(S, PH - M - TB_H - 14)


def stroke(S, pts, col, width, dashed):
    """A white halo under the coloured stroke, so a crossing reads as two wires and not one blob."""
    S.line(pts, (1, 1, 1), width + 2.6, dashed)
    S.line(pts, col, width, dashed)


def jump_run(S, x0, y0, x1, y1, obstacles, col, width, dashed):
    """Straight run, with a bump where it crosses another wire's track. Horizontal or vertical."""
    if abs(y0 - y1) < 0.5:
        horizontal, fixed, a, b = True, y0, x0, x1
    elif abs(x0 - x1) < 0.5:
        horizontal, fixed, a, b = False, x0, y0, y1
    else:
        stroke(S, [(x0, y0), (x1, y1)], col, width, dashed)
        return
    direction = 1 if b >= a else -1
    gap, bump = 6.0, 8.0
    stops = sorted(obstacles, key=lambda v: (v - a) * direction)
    stops = [v for v in stops if (v - a) * direction > gap + 2 and (b - v) * direction > gap + 2]
    cur = a

    def seg(p, q):
        if abs(p - q) < 0.4:
            return
        if horizontal:
            stroke(S, [(p, fixed), (q, fixed)], col, width, dashed)
        else:
            stroke(S, [(fixed, p), (fixed, q)], col, width, dashed)

    def hop(v):
        pre, post = v - direction * gap, v + direction * gap
        if horizontal:
            stroke(S, [(pre, fixed), (v, fixed - bump), (post, fixed)], col, width, dashed)
        else:
            stroke(S, [(fixed, pre), (fixed + bump, v), (fixed, post)], col, width, dashed)

    for v in stops:
        seg(cur, v - direction * gap)
        hop(v)
        cur = v + direction * gap
    seg(cur, b)


def wire_id_on(S, text, x, y0, y1, col):
    """The wire id just left of the vertical run, clear of the pin labels on the right of that run."""
    lo, hi = min(y0, y1), max(y0, y1)
    size = 8
    tw = S.tl(text, size, "hebo")
    if hi - lo < tw + 8:
        return
    mid = (lo + hi) / 2.0
    S.page.insert_text((x - size - 2, mid + tw / 2.0), text, fontsize=size, fontname="hebo", color=col, rotate=90)


def wire_label(S, r, x, y, w=LANE - 6):
    g = r["gauge_awg"] or ""
    lab = ("%s  %s %s" % (r["wire_id"], g, ABBR.get(r["colour"], r["colour"][:3].upper()))) if r["colour"] != "Shield" \
        else "%s  screen" % r["wire_id"]
    bands = [b for b in r["ident_bands"].split("-") if b]
    size = 5.0
    lab = S.fit(lab, w - 4.8 * len(bands) - 2, size)
    S.text(x, y, lab, size, color=INK)
    band_chips(S, x + S.tl(lab, size) + 2, y + 0.4, bands)


def order_key(H, key):
    k = H.kind(key)
    rank = {"ecu": 0, "bus": 1, "splice": 2, "part": 3, "conn": 4, "term": 5, "oem": 6, "screen": 7}.get(k, 8)
    if key in (("connector", "DRB102-CABIN"), ("connector", "DRB102-ENGINE")):
        rank = 3.5
    return (rank, key[1])


def blocks_for(H, rows):
    blocks = {}
    for r in rows:
        for s in ("from", "to"):
            key = H.end_key(r, s)
            if key not in blocks:
                ext = not H.local(r, s)
                title = H.title(key, r, s)
                if ext:
                    own = H.owner_of(r, s)
                    title = "%s  (on ST185-%s)" % (title, own) if own else title
                pn = H.part_no(key[1]) if key[0] == "connector" else ""
                blocks[key] = Block(key, title, pn, ext)
            blocks[key].rows.append((r[s + "_pin"] or ("" if key[0] != "splice" else ""), r[s + "_desc"], (r["wire_id"], s)))
    for b in blocks.values():
        b.rows.sort(key=lambda x: pin_sort(x[0]))
    return blocks


def draw_block(S, H, b):
    x0, x1, y = b.x0, b.x1, b.y
    head_fill = (0.86, 0.87, 0.89) if b.ext else LIGHT
    S.rect(x0, y, x1, y + b.height(), width=0.7)
    S.rect(x0, y, x1, y + HEAD_H, fill=head_fill, width=0.7)
    S.text(x0 + 3, y + 8, S.fit(b.title, x1 - x0 - 6, 6.5, "hebo"), 6.5, "hebo")
    sub = b.sub or {"splice": "solder splice (node)", "part": "inline part", "term": "end", "oem": "factory lead tap",
                    "screen": "cable screen", "bus": "bussed DT plug"}.get(H.kind(b.key), "")
    S.text(x0 + 3, y + 16, S.fit(sub, x1 - x0 - 6, 5.2), 5.2, color=GREY)
    yy = y + HEAD_H
    pinw = max([30.0] + [S.tl(pin, 6, "hebo") + 7 for pin, _, _ in b.rows])   # a pin is never cut
    for j, (pin, desc, rid) in enumerate(b.rows):
        if j % 2:
            S.rect(x0 + 0.4, yy, x1 - 0.4, yy + ROW_H, color=None, fill=(0.975, 0.98, 0.985))
        S.text(x0 + 3, yy + 6.3, S.fit(pin or "-", pinw - 4, 6, "hebo"), 6, "hebo")
        S.text(x0 + pinw, yy + 6.3, S.fit(desc, x1 - x0 - pinw - 52, 6), 6)
        S.text(x1 - 50, yy + 6.3, S.fit(rid[0], 48, 5), 5, color=GREY)
        yy += ROW_H
    S.line([(x0 + pinw - 3, y + HEAD_H), (x0 + pinw - 3, y + b.height())], width=0.3)


def legend(S, y):
    x = M + 8
    S.text(x, y, "WIRE COLOURS (R209):", 5.5, "hebo")
    x += 72
    for c in ("Red", "Black", "Orange", "Blue", "White", "Green", "Yellow"):
        S.line([(x, y - 2), (x + 14, y - 2)], WIRE_RGB[c], 1.4)
        S.text(x + 16, y, ABBR[c], 5.5)
        x += 40
    S.text(x + 6, y, "IDENT BANDS (R87):", 5.5, "hebo")
    x += 72
    for b in ("Blue", "Yellow", "White"):
        band_chips(S, x, y, [b])
        S.text(x + 6, y, b, 5.5)
        x += 34
    S.line([(x + 8, y - 2), (x + 26, y - 2)], INK, 0.6, "[3 2] 0")
    S.text(x + 29, y, "built with another harness", 5.5)
    x += 145
    S.text(x, y, "line colour = one wire on this page; the label has the wire colour", 5.5)


# ------------------------------------------------------------------------------------------------ 3. pinout
PIN_COLS = [("END", 150), ("PIN", 34), ("WIRE", 78), ("AWG", 24), ("COLOUR", 38), ("BANDS", 40), ("SIGNAL", 150),
            ("OTHER END", 250), ("LEN MM", 36), ("BUILT WITH", 72), ("CIRCUIT", 50)]


def table_sub(H, key, r, s):
    """The line under a pinout table's name: what the end is and its maker part numbers (TBD where not confirmed)."""
    t, i = key
    if t == "connector":
        hp = r[s + "_housing_pn"] or "TBD"
        ex = r[s + "_housing_extra"]
        return "housing %s%s  |  contacts %s  |  pins per %s" % (hp, ("  + " + ex) if ex else "", r[s + "_terminal_pn"] or "TBD",
                                                              r[s + "_pin_doc"] or "TBD")
    return {"splice": "splice: %s" % (r[s + "_terminal_pn"] or "solder splice"), "terminal": "terminal %s" % (r[s + "_terminal_pn"] or "TBD"),
            "oem": "factory lead tap (EWD locator in the signal)", "screen": "cable screen",
            "resistor": "inline resistor %s" % (r[s + "_housing_pn"] or "TBD"),
            "diode": "inline diode %s" % (r[s + "_housing_pn"] or "TBD")}.get(t, "")


def pinout_rows(H):
    out = []
    for r in H.wires:
        p, mm = H.route(r)
        for s, o in (("from", "to"), ("to", "from")):
            if not H.local(r, s):
                continue
            key = H.end_key(r, s)
            oth = (r[o + "_conn_name"] or r[o + "_conn"]) + ((" pin " + r[o + "_pin"]) if r[o + "_pin"] else "")
            out.append({"END": H.title(key, r, s), "_sub": table_sub(H, key, r, s), "PIN": r[s + "_pin"], "WIRE": r["wire_id"],
                        "AWG": r["gauge_awg"],
                        "COLOUR": r["colour"], "BANDS": r["ident_bands"], "SIGNAL": r[s + "_desc"], "OTHER END": oth,
                        "LEN MM": str(mm or ""), "BUILT WITH": "ST185-" + r["harness"], "CIRCUIT": r["circuit_id"],
                        "_g": row_group(H, r), "_k": (order_key(H, key), pin_sort(r[s + "_pin"]))})
    for r in H.spares:
        key = H.end_key(r, "from")
        out.append({"END": H.title(key, r, "from"), "_sub": table_sub(H, key, r, "from"), "PIN": r["from_pin"], "WIRE": "",
                    "AWG": "", "COLOUR": "", "BANDS": "",
                    "SIGNAL": r["from_desc"], "OTHER END": "", "LEN MM": "", "BUILT WITH": "", "CIRCUIT": "",
                    "_g": row_group(H, r), "_k": (order_key(H, key), pin_sort(r["from_pin"]))})
    out.sort(key=lambda x: x["_k"])
    return out


TABLE_COLS = [c for c in PIN_COLS if c[0] != "END"]   # one table per end: its name is the table header
TABLE_W = sum(w for _, w in TABLE_COLS) + 8


def size_pin_column(fitz, prow):
    """The PIN column fits the longest pin of the set, so a pin is never cut on the sheet."""
    global TABLE_COLS, TABLE_W
    w = max([34.0] + [math.ceil(fitz.get_text_length(r["PIN"], fontname="hebo", fontsize=5.8)) + 8 for r in prow])
    TABLE_COLS = [(n, w if n == "PIN" else cw) for n, cw in TABLE_COLS]
    TABLE_W = sum(cw for _, cw in TABLE_COLS) + 8
T_HEAD, T_COLS, T_ROW, T_GAP = 20.0, 10.0, 8.4, 12.0


def pinout_tables(H, prow):
    """[(end title, sub, [rows])] in pinout order, one per connector / bus / splice / end."""
    out = []
    for row in prow:
        if not out or out[-1][0] != row["END"]:
            out.append((row["END"], row["_sub"], []))
        out[-1][2].append(row)
    return out


def table_h(tb):
    return T_HEAD + T_COLS + T_ROW * len(tb[2])


def pinout_page_plan(tables):
    """Flow a section's tables down one column of a tabloid page. A table is never split; a tall table grows its page."""
    chrome_top = M + 44
    chrome_bot = M + TB_H + 12
    usable = PAGE_MAX_H - chrome_top - chrome_bot
    pages, col, used = [], [], 0.0

    def flush():
        nonlocal col, used
        if col:
            pages.append((col, PAGE_MAX_W, PAGE_MAX_H))
        col, used = [], 0.0

    for i, tb in enumerate(tables):
        th = table_h(tb) + T_GAP
        if col and used + th > usable + 1e-6:
            flush()
        if not col and th > usable:
            pages.append(([i], PAGE_MAX_W, chrome_top + chrome_bot + th))
            continue
        col.append(i)
        used += th
    flush()
    return pages


def pinout_sheet(S, tables, cols, banner):
    S.text(M + 8, M + 16, S.fit(banner, PW - 2 * M - 16, 8, "hebo"), 8, "hebo")
    S.text(M + 8, M + 27, "Length = layout path + end allowance (estimate until measured). Built with = the harness that builds "
           "that wire (a wire passing through is built with its owner). A pin with no wire takes a sealing plug.", 6)
    for ci, col in enumerate(cols):
        x0 = M + 8 + ci * (TABLE_W + 16)
        y = M + 44
        for i in col:
            title, sub, rows = tables[i]
            x1 = x0 + TABLE_W
            S.rect(x0, y, x1, y + table_h(tables[i]), width=0.7)
            S.rect(x0, y, x1, y + T_HEAD, fill=LIGHT, width=0.7)
            S.text(x0 + 4, y + 8.5, S.fit(title, TABLE_W - 8, 7, "hebo"), 7, "hebo")
            S.text(x0 + 4, y + 16.5, S.fit(sub, TABLE_W - 8, 5.4), 5.4, color=GREY)
            yy = y + T_HEAD + 7.5
            x = x0 + 4
            for name, w in TABLE_COLS:
                S.text(x, yy, name, 5.4, "hebo", GREY)
                x += w
            yy = y + T_HEAD + T_COLS
            for j, row in enumerate(rows):
                if j % 2:
                    S.rect(x0 + 0.4, yy, x1 - 0.4, yy + T_ROW, color=None, fill=(0.975, 0.98, 0.985))
                x = x0 + 4
                for name, w in TABLE_COLS:
                    val = row[name]
                    if name == "BANDS":
                        band_chips(S, x, yy + 6.2, [b for b in val.split("-") if b])
                    else:
                        bold = name == "PIN"
                        S.text(x, yy + 6.2, S.fit(val, w - 4, 5.8, "hebo" if bold else "helv"), 5.8, "hebo" if bold else "helv")
                    x += w
                yy += T_ROW
            y += table_h(tables[i]) + T_GAP


def write_xlsx(H, prow, path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "Pinout"
    heads = [n for n, _ in PIN_COLS]
    ws.append(heads)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="14213D")
    for row in prow:
        ws.append([row[h] for h in heads])
    for i, (n, w) in enumerate(PIN_COLS):
        ws.column_dimensions[chr(65 + i)].width = max(8, w / 5.2)
    ws.freeze_panes = "C2"
    ws2 = wb.create_sheet("Layout segments")
    ws2.append(["From", "To", "Length mm"])
    for a, b, mm in H.layout["segments"]:
        ws2.append([a, b, mm])
    for c in ws2[1]:
        c.font = Font(bold=True)
    tmp = io.BytesIO()
    wb.save(tmp)
    with open(path, "wb") as f:
        f.write(tmp.getvalue())


# ------------------------------------------------------------------------------------------------ per-harness wire lists
# One From / To wire list per harness (Dan 2026-10-26), generated from the master like every other view. Column names
# follow the harness.design Excel-import example (Wire, From, From Pin, To, To Pin, Signal, Colour, Gauge (AWG), Length (mm);
# Connectors sheet Connector, Part Number: docs.harness.design/guides/excel-import), then the build detail.
WIRELISTS = os.path.join(HARNESS, "wirelists")
WL_COLS = [("Wire", 14), ("From", 20), ("From Pin", 9), ("To", 20), ("To Pin", 9), ("Splice", 24), ("Branch", 11),
           ("Signal", 30), ("Colour", 9),
           ("Ident bands", 22), ("Gauge (AWG)", 8), ("Length (mm)", 9), ("Wire Type", 17), ("Cable", 15),
           ("Cable Part Number", 20), ("From Contact PN", 17), ("To Contact PN", 17), ("From Device", 38),
           ("To Device", 38), ("Circuit", 10), ("Built With", 14), ("Net", 18), ("Continues", 50), ("Route Branch", 34),
           ("OEM Ref", 40), ("Notes", 60)]
AWG_MM2 = {"4": 21.15, "6": 13.3, "8": 8.37, "10": 5.26, "12": 3.31, "14": 2.08, "16": 1.31, "18": 0.823, "20": 0.519,
           "22": 0.324, "24": 0.205}


def wirelist_harnesses(H):
    return [x for x in H.layout.get("wirelists", []) if x in H.set]


def wirelist_path(name):
    return os.path.join(WIRELISTS, "ST185-%s-wirelist.xlsx" % name)


def wirelist_digest(H, name):
    """The whole master (trunks and Continues read other harnesses' rows too), this script and the harness name."""
    hs = hashlib.sha256()
    with open(MASTER, "rb") as fh:
        hs.update(fh.read().replace(b"\r\n", b"\n"))
    with open(os.path.abspath(__file__), "rb") as fh:
        hs.update(fh.read().replace(b"\r\n", b"\n"))
    hs.update(name.encode())
    return hs.hexdigest()[:16]


def xlsx_digest(path):
    if not os.path.exists(path):
        return ""
    from openpyxl import load_workbook
    m = re.match(r"inputs ([0-9a-f]{16})", load_workbook(path, read_only=True).properties.keywords or "")
    return m.group(1) if m else ""


BULKHEAD_MATE = {"DRB102-CABIN": "DRB102-ENGINE", "DRB102-ENGINE": "DRB102-CABIN"}
NC = ("NC, floats", "NC")
SOURCE = re.compile(r"^(LOGIC|POWER|JB\d|RB\d|BUS-|GND|ENG-GND)")   # fuse / relay boxes, J/B, buses, ground points


def _end(r, s):
    """One wire end as (connector, pin): never a splice and never a blank pin (DECISIONS "Wire lists")."""
    t, i, pin = r[s + "_type"], r[s + "_id"], r[s + "_pin"]
    if t == "cable screen":
        return NC
    if not pin:
        pin = {"terminal": "Lug"}.get(t, "TBD")
    return i, pin


class SpliceNets:
    """Every splice of the master, the wires that land in it, and which one is its trunk (DECISIONS "Wire lists")."""

    def __init__(self, rows):
        self.at = collections.defaultdict(list)          # splice -> [(row, side at the splice)]
        for r in rows:
            for side in ("from", "to"):
                if r[side + "_type"] == "splice":
                    self.at[r[side + "_id"]].append((r, side))
        self._trunk = {}

    @staticmethod
    def other(side):
        return "to" if side == "from" else "from"

    def trunk(self, sp):
        """The heaviest wire if one is heavier than the rest, else the one ECU pin wire, else the one bulkhead wire,
        else the one link to another splice, else the one wire to a power or ground source, else the one factory tap,
        else the longest, else the first by wire ID (DECISIONS "Wire lists" rule 4)."""
        if sp in self._trunk:
            return self._trunk[sp]
        ws = sorted(self.at[sp], key=lambda x: x[0]["wire_id"])

        def far(x):
            r, side = x
            o = self.other(side)
            return r[o + "_type"], r[o + "_id"]

        def one(cands):
            return cands[0] if len(cands) == 1 else None
        g = [(AWG_MM2.get(x[0]["gauge_awg"], 0.0), x) for x in ws]
        top = max(v for v, _x in g) if g else 0
        pick = one([x for v, x in g if v == top and top > 0]) if sum(1 for v, _x in g if v == top) == 1 else None
        pick = pick or one([x for x in ws if far(x)[1].startswith("ECU-")])
        pick = pick or one([x for x in ws if far(x)[1] in BULKHEAD_MATE])
        pick = pick or one([x for x in ws if far(x)[0] == "splice"])
        pick = pick or one([x for x in ws if SOURCE.match(far(x)[1])])
        pick = pick or one([x for x in ws if far(x)[0] == "OEM"])
        if not pick:
            lens = [(int(x[0]["est_length_mm"] or 0), x) for x in ws]
            best = max(v for v, _x in lens) if lens else 0
            pick = one([x for v, x in lens if v == best and best > 0])
        self._trunk[sp] = pick or ws[0]
        return self._trunk[sp]

    def far_end(self, sp, via, seen=()):
        """Where a leg into `sp` reaches through the trunk: (connector, pin) or "legs of SP-x", plus the splices passed."""
        r, side = self.trunk(sp)
        if r["wire_id"] == via["wire_id"]:
            return ("legs of %s" % sp, "-"), [sp]
        o = self.other(side)
        if r[o + "_type"] == "splice" and r[o + "_id"] not in seen:
            end, path = self.far_end(r[o + "_id"], r, seen + (sp,))
            return end, [sp] + path
        return _end(r, o), [sp]


def wirelist_rows(H, name, nets=None):
    """Every wire of one harness (its own rows plus the wires of other harnesses that pass through it), Option A:
    From / To are connectors or devices only; the Splice and Branch columns carry the splices."""
    allrows = [r for r in master_rows() if r["wire_id"]]
    nets = nets or SpliceNets(allrows)
    by_pin = collections.defaultdict(list)
    for r in allrows:
        for side in ("from", "to"):
            by_pin[(r[side + "_id"], r[side + "_pin"])].append((r, side))

    def owned(r):
        return r["harness"] == name or name in [x.strip() for x in r["passes_through"].split("/")]
    wires = [r for r in H.rows if r["wire_id"] and owned(r)]

    def continues(r, ends, splices):
        out = []
        for c, pin in ends:
            mate = BULKHEAD_MATE.get(c)
            for m, side in by_pin.get((mate, pin), []) if mate else []:
                oc, op = _end(m, SpliceNets.other(side)) if m[SpliceNets.other(side) + "_type"] != "splice" else \
                    ("splice", m[SpliceNets.other(side) + "_id"])
                out.append("%s %s at %s %s, to %s %s" % ("ST185-" + m["harness"], m["wire_id"], mate, pin, oc, op))
        for sp in splices:
            other = sorted({x["harness"] for x, _s in nets.at[sp]} - {name})
            if other:
                out.append("%s also joins %s" % (sp, ", ".join("ST185-" + h for h in other)))
        return "; ".join(out)
    first = {"AB-cabin": ["ECU-A", "ECU-B"], "AB-engine": ["DRB102-ENGINE"]}.get(name, [])
    out = []
    for r in wires:
        ft, tt = r["from_type"], r["to_type"]
        side_dev = None
        if ft == "splice" and tt == "splice":
            fr, to = ("legs of %s" % r["from_id"], "-"), ("legs of %s" % r["to_id"], "-")
            splices, branch, dev, oth = [r["from_id"], r["to_id"]], "link", None, None
            fc = tc = "solder splice"
            fd, td = r["from_name"], r["to_name"]
        elif "splice" in (ft, tt):
            sp_side = "from" if ft == "splice" else "to"
            dev = SpliceNets.other(sp_side)
            sp = r[sp_side + "_id"]
            t_row, _t_side = nets.trunk(sp)
            if t_row["wire_id"] == r["wire_id"]:
                fr, to, splices, branch = ("legs of %s" % sp, "-"), _end(r, dev), [sp], "trunk"
                fc, tc = "solder splice", r[dev + "_terminal_pn"]
                fd, td = r[sp_side + "_name"], r[dev + "_name"]
            else:
                to, splices = nets.far_end(sp, r)
                fr, branch = _end(r, dev), ("drain" if r[dev + "_type"] == "cable screen" else "leg")
                fc, tc = r[dev + "_terminal_pn"], "solder splice " + sp
                fd, td = r[dev + "_name"], "via %s" % " > ".join(splices)
        else:
            fr, to, splices = _end(r, "from"), _end(r, "to"), []
            branch = "drain" if "cable screen" in (ft, tt) else ("core" if r["cable"] else "wire")
            fc, tc, fd, td = r["from_terminal_pn"], r["to_terminal_pn"], r["from_name"], r["to_name"]
            if tt == "cable screen" or ft == "cable screen":
                if ft == "cable screen":
                    fr, to, fc, tc, fd, td = to, fr, tc, fc, td, fd
        if r["cable"] and branch in ("leg", "trunk"):
            branch += " core"
        sig = r["from_desc"] or r["to_desc"]
        notes = [x for x in (r["from_note"], r["to_note"], r["notes"]) if x]
        if branch.startswith("drain") and NC in (fr, to):
            notes.insert(0, "Screen floats at this end: cut back and seal under heat-shrink")
        oem = "; ".join(x for x in (r["oem_location"], r["oem_wire_colour"] and "OEM colour " + r["oem_wire_colour"],
                                    r["oem_ewd_page"] and "EWD " + r["oem_ewd_page"], r["oem_method"]) if x)
        out.append({"Wire": r["wire_id"], "From": fr[0], "From Pin": fr[1], "To": to[0], "To Pin": to[1],
                    "Splice": " > ".join(splices), "Branch": branch, "Signal": sig,
                    "Colour": r["colour"], "Ident bands": r["ident_bands"], "Gauge (AWG)": r["gauge_awg"],
                    "Length (mm)": r["est_length_mm"] or "TBD", "Wire Type": r["wire_pn"] or ("(cable core)" if r["cable"] else "TBD"),
                    "Cable": r["cable"], "Cable Part Number": r["cable_pn"], "From Contact PN": fc, "To Contact PN": tc,
                    "From Device": fd, "To Device": td, "Circuit": r["circuit"], "Built With": "ST185-" + r["harness"],
                    "Net": r["net"] or r["circuit"], "Continues": continues(r, [fr, to], splices),
                    "Route Branch": r["route_branch"], "OEM Ref": oem, "Notes": " | ".join(notes)})

    def key(d):
        f = d["From"]
        return (first.index(f) if f in first else len(first) + (1 if f.startswith(("legs of", "NC")) else 0), f,
                pin_sort(d["From Pin"]), d["Wire"])
    out.sort(key=key)
    return wires, out


def wirelist_ends(H, name, wires):
    """Connectors sheet (every end the harness touches) and Splices sheet (wires joined, total copper)."""
    ends, splices = collections.OrderedDict(), collections.OrderedDict()
    for r in wires:
        for s in ("from", "to"):
            t, i = r[s + "_type"], r[s + "_id"]
            if not i:
                continue
            e = ends.setdefault(i, {"Connector": i, "Part Number": "", "Type": t, "Name": r[s + "_name"], "Extras": "",
                                    "Pin Numbering": "", "Contacts": set(), "Wires": 0})
            e["Wires"] += 1
            if r[s + "_housing_pn"] and not e["Part Number"]:
                e["Part Number"] = r[s + "_housing_pn"]
            if r[s + "_housing_extra"] and not e["Extras"]:
                e["Extras"] = r[s + "_housing_extra"]
            if r[s + "_pin_doc"] and not e["Pin Numbering"]:
                e["Pin Numbering"] = r[s + "_pin_doc"]
            if r[s + "_terminal_pn"]:
                e["Contacts"].add(r[s + "_terminal_pn"])
            if t == "splice":
                sp = splices.setdefault(i, {"Splice": i, "Location / job": r[s + "_name"], "Method": r[s + "_terminal_pn"],
                                            "Wires": [], "mm2": 0.0})
                sp["Wires"].append("%s (%s AWG)" % (r["wire_id"], r["gauge_awg"] or "screen"))
                sp["mm2"] += AWG_MM2.get(r["gauge_awg"], 0.0)
    spare = collections.Counter(r["from_id"] for r in H.spares if r["harness"] == name)
    order = {"connector": 0, "OEM": 1, "terminal": 2, "splice": 3, "resistor": 4, "diode": 5, "cable screen": 6}
    conns = []
    for e in sorted(ends.values(), key=lambda e: (order.get(e["Type"], 9), e["Connector"])):
        e = dict(e)
        e["Contacts"] = ", ".join(sorted(e["Contacts"]))
        e["Spare Cavities"] = spare.get(e["Connector"], 0)
        conns.append(e)
    nets = SpliceNets([r for r in master_rows() if r["wire_id"]])
    sps = [{"Splice": v["Splice"], "Trunk": nets.trunk(v["Splice"])[0]["wire_id"], "Location / job": v["Location / job"],
            "Method": v["Method"], "Wires Joined": len(v["Wires"]),
            "Total Copper (mm2)": round(v["mm2"], 2), "Wires": ", ".join(v["Wires"])} for v in splices.values()]
    spares = [{"Connector": r["from_id"], "Cavity": r["from_pin"], "Plug / Contact": r["from_terminal_pn"],
               "Note": r["from_desc"] or r["notes"]} for r in sorted(
                   (r for r in H.spares if r["harness"] == name), key=lambda r: (r["from_id"], pin_sort(r["from_pin"])))]
    return conns, sps, spares


def wirelist_readback(name):
    """Read a committed wire list back against the master (Option A, DECISIONS "Wire lists"): every wire once, both
    device ends with their pins, gauge, colour and bands; From / To never a splice and never blank; one trunk per splice."""
    from openpyxl import load_workbook
    path = wirelist_path(name)
    ws = load_workbook(path, read_only=True)["Wires"]
    it = ws.iter_rows(values_only=True)
    head = list(next(it))
    rows = [dict(zip(head, ["" if v is None else str(v) for v in r])) for r in it]
    allrows = [r for r in master_rows() if r["wire_id"]]
    splices = {r[s + "_id"] for r in allrows for s in ("from", "to") if r[s + "_type"] == "splice"}
    want = {r["wire_id"]: r for r in allrows
            if r["harness"] == name or name in [x.strip() for x in r["passes_through"].split("/")]}
    bad, seen, trunks = [], collections.Counter(), collections.Counter()
    tag = os.path.basename(path)
    for d in rows:
        w = d.get("Wire", "")
        seen[w] += 1
        m = want.get(w)
        if not m:
            bad.append("%s: %s is not a wire of %s in the master" % (tag, w, name))
            continue
        for e in ("From", "To"):
            if d[e] in splices or not d[e] or not d[e + " Pin"]:
                bad.append("%s: %s %s is a splice or blank (%r / %r)" % (tag, w, e, d[e], d[e + " Pin"]))
        ends = {(d["From"], d["From Pin"]), (d["To"], d["To Pin"])}
        col = [x.strip() for x in d["Splice"].split(">") if x.strip()]
        for s in ("from", "to"):
            t = m[s + "_type"]
            if t == "splice" and m[s + "_id"] not in col:
                bad.append("%s: %s Splice column misses %s" % (tag, w, m[s + "_id"]))
            elif t == "cable screen" and NC not in ends:
                bad.append("%s: %s screen end is not 'NC, floats'" % (tag, w))
            elif t not in ("splice", "cable screen") and (m[s + "_id"], m[s + "_pin"] or "Lug") not in ends:
                bad.append("%s: %s lost its end %s %s" % (tag, w, m[s + "_id"], m[s + "_pin"]))
        for col_name, key in (("Gauge (AWG)", "gauge_awg"), ("Colour", "colour"), ("Ident bands", "ident_bands")):
            if d[col_name] != m[key]:
                bad.append("%s: %s %s %r, master %r" % (tag, w, col_name, d[col_name], m[key]))
        if d["Branch"].startswith("trunk"):
            trunks[d["Splice"]] += 1
    bad += ["%s: %s listed %d times" % (tag, w, n) for w, n in seen.items() if n > 1]
    bad += ["%s: %s missing" % (tag, w) for w in sorted(set(want) - set(seen))]
    bad += ["%s: %s has %d trunks" % (tag, sp, n) for sp, n in trunks.items() if n > 1]
    return bad


def write_wirelist(H, name):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    path = wirelist_path(name)
    dg = wirelist_digest(H, name)
    if xlsx_digest(path) == dg:
        return None
    wires, rows = wirelist_rows(H, name)
    conns, sps, spares = wirelist_ends(H, name, wires)
    wb = Workbook()
    head_font, head_fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="14213D")

    def sheet(ws, cols, data):
        ws.append([c for c, _w in cols])
        for c in ws[1]:
            c.font, c.fill = head_font, head_fill
            c.alignment = Alignment(wrap_text=True, vertical="top")
        for d in data:
            ws.append([d.get(c, "") for c, _w in cols])
        for i, (_c, w) in enumerate(cols, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        ws.freeze_panes = "B2"
        ws.auto_filter.ref = ws.dimensions
    ws = wb.active
    ws.title = "Wires"
    sheet(ws, WL_COLS, rows)
    sheet(wb.create_sheet("Connectors"), [("Connector", 18), ("Part Number", 20), ("Type", 12), ("Name", 50), ("Extras", 30),
                                          ("Contacts", 30), ("Wires", 7), ("Spare Cavities", 9), ("Pin Numbering", 50)], conns)
    sheet(wb.create_sheet("Splices"), [("Splice", 20), ("Trunk", 16), ("Location / job", 60), ("Method", 16), ("Wires Joined", 9),
                                       ("Total Copper (mm2)", 11), ("Wires", 80)], sps)
    sheet(wb.create_sheet("Spare Cavities"), [("Connector", 18), ("Cavity", 9), ("Plug / Contact", 20), ("Note", 50)], spares)
    key = wb.create_sheet("Key")
    for line in ("ST185-%s wire list - generated from docs/harness/MASTER-wirelist.csv by build_drawings.py; edit the master, "
                 "never this file." % name,
                 "One row per wire segment, From end to To end. A splice (SP-...) is its own end: one row per wire into it.",
                 "Colour = insulation colour (harness.design colour names). Ident bands = printed MIL-STD-681 band code.",
                 "Length (mm) = the master's estimate; TBD until the tape-measure pass (OPEN-ITEMS row 165).",
                 "Built With = the harness that owns the wire; a wire owned by another harness passes through this one.",
                 "Option A (DECISIONS 'Wire lists'): From / To are only connectors or devices with their pin, never a splice. "
                 "Splice = the splice(s) the wire lands in; Branch = wire, core, leg, trunk, link or drain.",
                 "A leg's To is where its trunk lands (through any link splices); a trunk or link end in a splice reads 'legs of SP-x'.",
                 "'NC, floats' = a shield drain left unconnected at that end. Pin 'Lug' = a ring or spade lug on a stud.",
                 "Continues = where the wire carries on in another harness file (the mated bulkhead pin, or a shared splice).",
                 "Contact PN 'solder splice' / 'solder onto the factory lead' = no contact; TBD = not confirmed by a maker document.",
                 "Wires: %d   Connectors / ends: %d   Splices: %d   Spare cavities: %d" % (len(rows), len(conns), len(sps), len(spares))):
        key.append([line])
    key.column_dimensions["A"].width = 140
    wb.properties.title = "ST185-%s wire list" % name
    wb.properties.creator = "build_drawings.py"
    wb.properties.keywords = "inputs %s" % dg
    os.makedirs(WIRELISTS, exist_ok=True)
    tmp = io.BytesIO()
    wb.save(tmp)
    with open(path, "wb") as f:
        f.write(tmp.getvalue())
    return path


# ------------------------------------------------------------------------------------------------ approved route figures (layout pages)
ROUTES_FOR = {
    "HeavyDC": ["ROUTE-1-HEAVYDC.html"],
    "EngineRoom-C": ["ROUTE-17-FRONT.html"],
    "AB-engine": ["ROUTE-16-ENGINE-MAIN.html"],
    "CAN": ["ROUTE-8-CAN.html"],
    "WheelSpeed-Front": ["ROUTE-9-WHEELSPEED-FRONT.html"],
    "WheelSpeed-Rear": ["ROUTE-10-WHEELSPEED-REAR.html"],
    "RearFuel": ["ROUTE-11-REARFUEL.html"],
    "CSB3": ["ROUTE-12-CSB3.html"],
    "ClusterLED": ["ROUTE-13-CLUSTERLED.html"],
    "AntiTheft": ["ROUTE-14-ANTITHEFT.html"],
    "RearLights": ["ROUTE-15-REARLIGHTS.html"],
}
_SVG_TAG = re.compile(r"<(image|polyline|polygon|circle|text|rect)\b([^>]*?)/?>(?:(.*?)</\1>)?", re.S)


def _css_rgb(value):
    if not value or value == "none":
        return None
    h = value.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return None


def _attr(raw):
    return {k: html.unescape(v) for k, v in re.findall(r'([\w:-]+)="([^"]*)"', raw)}


def route_figures(path):
    """Every SVG figure in an approved route file: the drawing Dan signed, not a new layout."""
    text = open(path, encoding="utf-8").read()
    out = []
    for part in re.split(r"<figure\b[^>]*>", text)[1:]:
        body = part.split("</figure>", 1)[0]
        cap = re.search(r"<figcaption>(.*?)</figcaption>", body, re.S)
        caption = re.sub(r"<[^>]+>", "", html.unescape(cap.group(1))).strip() if cap else ""
        caption = re.sub(r"\s+", " ", caption)
        for svg in re.finditer(r"<svg\b([^>]*)>(.*?)</svg>", body, re.S):
            box = re.search(r'viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"', svg.group(1))
            if not box:
                continue
            ops = []
            for tag in _SVG_TAG.finditer(svg.group(2)):
                ops.append((tag.group(1), _attr(tag.group(2)), tag.group(3) or ""))
            if ops:
                out.append({"box": tuple(float(v) for v in box.groups()), "ops": ops, "caption": caption,
                            "file": os.path.basename(path)})
    return out


# Routes 16 and 17 store polylines in PDF points of this page (origin top-left, y down, the same space PyMuPDF draws in).
EWD_PDF = os.path.join(os.path.dirname(REPO), "st185-celica-repair-manual", "manuals-electrical",
                       "Connector__Ground_and_Splice.pdf")
EWD_PAGE = (612.0, 792.0)  # letter; page 1 is printed p.36, the 3S-GTE engine compartment
ROUTE_COLOUR = {"red": (0.82, 0.06, 0.08), "cyan": (0.00, 0.55, 0.70), "blue": (0.10, 0.28, 0.82),
                "yellow": (0.78, 0.58, 0.00), "purple": (0.48, 0.12, 0.62), "green": (0.05, 0.48, 0.22),
                "orange": (0.90, 0.40, 0.00)}
_RUN_COLOUR = ["red", "blue", "orange", "green", "purple", "cyan"]


def route_json_figure(path):
    """Routes 16 and 17: one approved drawing, the EWD page with every signed line on it."""
    text = open(path, encoding="utf-8").read()
    found = re.search(r'<script type="application/json" id="route-data">(.*?)</script>', text, re.S)
    if not found:
        return None
    data = json.loads(found.group(1))
    lines, marks = [], []
    for r in data.get("routes") or []:
        lines.append({"name": "%s  %s" % (r["n"], r["name"]), "n": str(r["n"]), "colour": r.get("colour", "red"),
                      "pts": r["path"], "dash": False})
        for extra in r.get("low_behind_engine") or []:
            lines.append({"name": "%s  %s, low behind the engine" % (r["n"], r["name"]), "n": str(r["n"]),
                          "colour": r.get("colour", "red"), "pts": extra, "dash": True})
        for end_name, pt in (r.get("ends") or {}).items():
            marks.append({"n": "", "name": end_name, "at": pt})
    for i, (name, pts) in enumerate((data.get("runs") or {}).items()):
        lines.append({"name": name, "n": name.split()[0], "colour": _RUN_COLOUR[i % len(_RUN_COLOUR)],
                      "pts": pts, "dash": False})
    for d in data.get("devices") or []:
        if "REMOVED" in d.get("name", ""):
            continue
        marks.append({"n": str(d.get("n", "")), "name": d["name"], "at": d["at"]})
    if not lines and not marks:
        return None
    return {"file": os.path.basename(path), "caption": data.get("base", ""), "lines": lines, "marks": marks,
            "page": EWD_PAGE}


def route_pages(path):
    """The approved pages of one route file. SVG figures win; 16 and 17 are the JSON overlay."""
    figs = route_figures(path)
    if figs:
        return figs
    overlay = route_json_figure(path)
    return [overlay] if overlay else []


def _paint_route_figure(S, fig, dest):
    vx, vy, vw, vh = fig["box"]
    scale = min(dest.width / vw, dest.height / vh)
    ox = dest.x0 + (dest.width - vw * scale) / 2.0
    oy = dest.y0 + (dest.height - vh * scale) / 2.0

    def xy(x, y):
        return (ox + (float(x) - vx) * scale, oy + (float(y) - vy) * scale)

    for kind, a, inner in fig["ops"]:
        if kind == "image":
            href = a.get("href") or a.get("xlink:href") or ""
            if "base64," not in href:
                continue
            ix, iy = float(a.get("x", vx)), float(a.get("y", vy))
            iw, ih = float(a.get("width", vw)), float(a.get("height", vh))
            x0, y0 = xy(ix, iy)
            x1, y1 = xy(ix + iw, iy + ih)
            flip = a.get("transform", "").startswith("matrix(-1")
            try:
                S.page.insert_image(S.fitz.Rect(x0, y0, x1, y1), stream=base64.b64decode(href.split(",", 1)[1]),
                                    rotate=180 if flip else 0)
            except Exception:
                continue
        elif kind in ("polyline", "polygon"):
            pts = [xy(*p.split(",")) for p in a.get("points", "").split() if "," in p]
            if len(pts) < 2:
                continue
            col = _css_rgb(a.get("stroke")) or _css_rgb(a.get("fill")) or (0.88, 0, 0)
            fill = _css_rgb(a.get("fill")) if kind == "polygon" else None
            sw = float(a.get("stroke-width", "1") or 1) * scale
            op = float(a.get("opacity", "1") or 1)
            dash = a.get("stroke-dasharray")
            dashes = None if not dash else "[%s] 0" % " ".join(str(float(n) * scale) for n in dash.split())
            sh = S.page.new_shape()
            if kind == "polygon":
                sh.draw_polyline(pts)
            else:
                for p, q in zip(pts, pts[1:]):
                    sh.draw_line(p, q)
            sh.finish(color=col, fill=fill, width=max(0.4, sw), dashes=dashes, stroke_opacity=op,
                      fill_opacity=op if fill else 0, closePath=(kind == "polygon"))
            sh.commit()
        elif kind == "circle":
            c = xy(a.get("cx", 0), a.get("cy", 0))
            rad = float(a.get("r", 4)) * scale
            fill = _css_rgb(a.get("fill"))
            stroke = _css_rgb(a.get("stroke")) or fill or INK
            S.page.draw_circle(c, rad, color=stroke, fill=fill, width=max(0.4, float(a.get("stroke-width", 1)) * scale))
        elif kind == "text":
            body = re.sub(r"<[^>]+>", "", html.unescape(inner)).strip()
            if not body or "x" not in a:
                continue
            size = max(4.0, float(a.get("font-size", 12)) * scale)
            font = "hebo" if a.get("font-weight") == "bold" else "helv"
            x, y = xy(a["x"], a["y"])
            tw = S.tl(body, size, font)
            anchor = a.get("text-anchor", "start")
            if anchor == "middle":
                x -= tw / 2.0
            elif anchor == "end":
                x -= tw
            S.page.insert_text((x, y), body, fontsize=size, fontname=font, color=_css_rgb(a.get("fill")) or INK)
        elif kind == "rect":
            fill = _css_rgb(a.get("fill"))
            if not fill or fill == (1, 1, 1):
                continue
            x, y = xy(a.get("x", 0), a.get("y", 0))
            x2, y2 = xy(float(a.get("x", 0)) + float(a.get("width", 0)), float(a.get("y", 0)) + float(a.get("height", 0)))
            S.rect(x, y, x2, y2, color=fill, fill=fill, width=0.2)


def _paint_route_overlay(S, fig, dest):
    """The EWD page, then the approved lines in the same point space, with the key beside it."""
    pw, ph = fig["page"]
    legend_w = 250.0
    scale = min((dest.width - legend_w) / pw, dest.height / ph)
    ox, oy = dest.x0, dest.y0 + (dest.height - ph * scale) / 2.0
    box = S.fitz.Rect(ox, oy, ox + pw * scale, oy + ph * scale)
    if not os.path.exists(EWD_PDF):
        raise SystemExit("route overlay needs the EWD page: %s" % EWD_PDF)
    src = S.fitz.open(EWD_PDF)
    pix = src[0].get_pixmap(matrix=S.fitz.Matrix(2, 2), alpha=False)
    src.close()
    S.page.insert_image(box, pixmap=pix)

    def xy(x, y):
        return (ox + float(x) * scale, oy + float(y) * scale)

    for line in fig["lines"]:
        pts = [xy(p[0], p[1]) for p in line["pts"]]
        if len(pts) < 2:
            continue
        col = ROUTE_COLOUR.get(line["colour"], (0.8, 0, 0))
        sh = S.page.new_shape()
        for a, b in zip(pts, pts[1:]):
            sh.draw_line(a, b)
        sh.finish(color=col, width=max(1.5, 2.4 * scale), dashes="[5 3] 0" if line["dash"] else None, closePath=False)
        sh.commit()
        if line["n"]:
            x, y = pts[0]
            S.page.insert_text((x + 3, y - 2), line["n"][:3], fontsize=7, fontname="hebo", color=col)
    for m in fig["marks"]:
        x, y = xy(m["at"][0], m["at"][1])
        S.page.draw_rect(S.fitz.Rect(x - 3.2, y - 3.2, x + 3.2, y + 3.2), color=INK, fill=(1, 0.92, 0.3), width=0.5)
        if m["n"]:
            S.page.insert_text((x + 4.5, y + 2), m["n"], fontsize=6, fontname="hebo", color=INK)
    lx = box.x1 + 10
    y = dest.y0 + 12
    S.text(lx, y, "APPROVED LINES", 7, "hebo")
    y += 12
    for line in fig["lines"]:
        col = ROUTE_COLOUR.get(line["colour"], (0.8, 0, 0))
        S.line([(lx, y - 2), (lx + 16, y - 2)], col, 1.8, "[3 2] 0" if line["dash"] else None)
        S.text(lx + 20, y, S.fit(line["name"], dest.x1 - lx - 24, 6), 6)
        y += 11
    if fig["marks"]:
        y += 6
        S.text(lx, y, "DEVICES", 7, "hebo")
        y += 12
        for m in fig["marks"]:
            label = ("%s  %s" % (m["n"], m["name"])) if m["n"] else m["name"]
            S.text(lx, y, S.fit(label, dest.x1 - lx - 4, 5.5), 5.5)
            y += 9
            if y > dest.y1 - 4:
                break


def layout_route_page(S, harness, route_file, fig, i, n):
    who = route_file.replace(".html", "").replace("-", " ")
    S.text(M + 8, M + 16, S.fit("LAYOUT - ST185-%s - %s, as approved (%d of %d)" % (harness, who, i, n),
                                PW - 2 * M - 16, 8, "hebo"), 8, "hebo")
    if fig.get("caption"):
        S.text(M + 8, M + 28, S.fit(fig["caption"], PW - 2 * M - 16, 6), 6, color=GREY)
    dest = S.fitz.Rect(M + 6, M + 36, PW - M - 6, PH - M - TB_H - 8)
    if fig.get("lines") is not None:
        _paint_route_overlay(S, fig, dest)
    else:
        _paint_route_figure(S, fig, dest)


# ------------------------------------------------------------------------------------------------ build
def _part_label(title, i, n):
    return title if n == 1 else "%s  (part %d of %d)" % (title, i, n)


def _save_pdf(doc, path, H, what):
    doc.set_metadata({"title": "%s - %s" % (H.revs["title"], what), "author": H.revs["revs"][0]["by"],
                      "subject": H.revs["subtitle"], "keywords": "inputs %s" % digest(H.h), "creator": "build_drawings.py",
                      "producer": "PyMuPDF", "creationDate": "", "modDate": ""})
    doc.save(path, garbage=3, deflate=True)


def build(h):
    import fitz
    H = Harness(h)
    for r in H.wires:
        H.route(r)
    if H.problems:
        for p in H.problems:
            print("PROBLEM", p)
        raise SystemExit("not written: %d problem(s)" % len(H.problems))
    os.makedirs(H.p["dir"], exist_ok=True)
    sections = section_order(H)
    # each page is finished (title block included) before the next page is made: PyMuPDF page handles go stale
    sch = fitz.open()
    sch_plan = []
    for _g, title in sections:
        rows = [r for r in H.wires if group_of(H, r) == _g]
        if not rows:
            continue
        for part in pack_schematic(H, rows):
            sch_plan.append((title, part))
    counts = collections.Counter(t for t, _part in sch_plan)
    seen = collections.Counter()
    for i, (title, rows) in enumerate(sch_plan, 1):
        seen[title] += 1
        lay = arrange_schematic(H, rows)
        need_w, need_h = schematic_need(lay)
        set_page(max(PAGE_MAX_W, need_w), max(PAGE_MAX_H, need_h))
        S = Sheet(sch, fitz)
        schematic_sheet(S, H, title, seen[title], counts[title], rows, lay)
        title_block(S, H, i, len(sch_plan), _part_label(title, seen[title], counts[title]), "-" + SHEETS[0][1])
    laydoc = fitz.open()
    lay_plan = []
    for name in set_harnesses(H.h):
        for route in ROUTES_FOR.get(name, []):
            figs = route_pages(os.path.join(HARNESS, "routes", route))
            for fi, fig in enumerate(figs, 1):
                lay_plan.append((name, route, fig, fi, len(figs)))
        if not ROUTES_FOR.get(name):
            nodes, segs, ends = layout_keep(H, name)
            if nodes:
                lay_plan.append((name, None, (nodes, segs, ends), 1, 1))
    for i, (name, route, fig, fi, fn) in enumerate(lay_plan, 1):
        set_page(1224.0, 792.0)
        S = Sheet(laydoc, fitz)
        if route:
            layout_route_page(S, name, route, fig, fi, fn)
            what = "Layout - ST185-%s - %s" % (name, route.replace(".html", ""))
        else:
            nodes, segs, ends = fig
            layout_sheet(S, H, name, nodes, segs, ends)
            what = "Layout - ST185-%s" % name
        title_block(S, H, i, len(lay_plan), what, "-" + SHEETS[1][1])
    prow = pinout_rows(H)
    size_pin_column(fitz, prow)
    pindoc = fitz.open()
    pin_plan = []
    for g, title in sections:
        sub = [r for r in prow if r["_g"] == g]
        if not sub:
            continue
        tables = pinout_tables(H, sub)
        for col, w, hh in pinout_page_plan(tables):
            pin_plan.append((title, tables, col, w, hh))
    counts = collections.Counter(t for t, _tables, _col, _w, _hh in pin_plan)
    seen = collections.Counter()
    for i, (title, tables, col, w, hh) in enumerate(pin_plan, 1):
        seen[title] += 1
        set_page(w, hh)
        S = Sheet(pindoc, fitz)
        pinout_sheet(S, tables, [col], _part_label(title, seen[title], counts[title]))
        title_block(S, H, i, len(pin_plan), _part_label(title, seen[title], counts[title]), "-" + SHEETS[2][1])
    docs = (sch, laydoc, pindoc)
    for i, ((_k, _code, what), doc) in enumerate(zip(SHEETS, docs)):
        _save_pdf(doc, H.p["pdfs"][i], H, what)
    lay = laydoc[0]
    pix = lay.get_pixmap(matrix=fitz.Matrix(360 / lay.rect.width, 360 / lay.rect.width))
    os.makedirs(OUT, exist_ok=True)
    pix.save(H.p["thumb"])
    write_xlsx(H, prow, H.p["xlsx"])
    for name in wirelist_harnesses(H):
        wl = write_wirelist(H, name)
        if wl:
            print("wrote", os.path.relpath(wl, REPO))
    print("wrote %s (%s), %s, %s" % (
        ", ".join(os.path.relpath(p, REPO) for p in H.p["pdfs"]),
        ", ".join("%s %d pages" % (name, doc.page_count) for (name, _c, _w), doc in zip(SHEETS, docs)),
        os.path.relpath(H.p["xlsx"], REPO), os.path.relpath(H.p["thumb"], REPO)))


# ------------------------------------------------------------------------------------------------ DRB102 insert-face map
DRB_PNG = os.path.join(DRAWINGS, "DRB102-bulkhead-map.png")
DRB_COLS = [list(range(102, 94, -1)), list(range(94, 82, -1)), list(range(82, 70, -1)), [70, 69, 68, 67, None, 66, 65, 64, 63],
            [62, 61, 60, 59, 58], [57, 56, 55, 54, 53, 52], [51, 50, 49, 48, 47, 46], [45, 44, 43, 42, 41],
            [40, 39, 38, 37, None, 36, 35, 34, 33], list(range(32, 20, -1)), list(range(20, 8, -1)), list(range(8, 0, -1))]
DRB_SIZE = {**{i: 12 for i in list(range(1, 9)) + list(range(95, 103))}, 48: 8, 49: 8, 54: 8, 55: 8, 43: 4, 60: 4}
DRB_FILL = {"spare": "FFFFFF", "can": "2E7D32", "shield": "9E9E9E", "power": "C62828", "signal": "7CB342", "output": "00838F",
            "ground": "424242", "supply": "EF6C00", "coil": "6A1B9A", "injector": "1565C0"}
DRB_LEGEND = [("spare", "Spare"), ("can", "CAN"), ("shield", "Shield drain"), ("power", "+12 V power"), ("signal", "Sensor signal"),
              ("output", "Output / actuator"), ("ground", "Ground / sensor return"), ("supply", "Sensor supply +5/+8 V"),
              ("coil", "Coil trigger"), ("injector", "Injector drive")]
DRB_RADIUS = {16: 22, 12: 27, 8: 34, 4: 40}


def drb_kind(desc, circuit):
    d = desc.lower()
    if "shield" in d or "screen" in d:
        return "shield"
    if re.search(r"\bgnd\b|ground", d):
        return "ground"
    if circuit == "CAN":
        return "can"
    if re.match(r"coil \d", d):
        return "coil"
    if re.match(r"injector \d", d):
        return "injector"
    if re.match(r"\+\s?[58] ?v", d):
        return "supply"
    if re.search(r"\+\s?12 ?v|12v|fuse|relay k_|battery \+", d):
        return "power"
    if re.search(r"etb motor [+-]|boost|pump speed|relay coil", d):
        return "output"
    return "signal"


def drb_cavities(rows):
    """cavity -> (short text, kind, size) from the master's DRB102 ends (both halves share the number)."""
    out = {}
    for r in rows:
        if not r["wire_id"]:
            continue
        for s in ("from", "to"):
            if r[s + "_id"] in ("DRB102-CABIN", "DRB102-ENGINE") and r[s + "_pin"].isdigit():
                d = r[s + "_desc"]
                out.setdefault(int(r[s + "_pin"]), (d.split("-> ")[-1], drb_kind(d, r["circuit"])))
    return out


def drb_digest(rows):
    return hashlib.sha256((STYLE + json.dumps(sorted(drb_cavities(rows).items()))).encode("utf-8")).hexdigest()[:16]


def drb_png_digest(path):
    """The digest stored in the png's Description text chunk, or ''."""
    import struct
    import zlib
    try:
        data = open(path, "rb").read()
    except OSError:
        return ""
    pos = 8
    while pos + 8 <= len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"tEXt" and body.startswith(b"Description\0"):
            return body.split(b"\0", 1)[1].decode("latin-1")
        if typ == b"zTXt" and body.startswith(b"Description\0"):
            return zlib.decompress(body.split(b"\0", 1)[1][1:]).decode("latin-1")
        pos += 12 + n
    return ""


def drb_render(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    cav = drb_cavities(rows)
    W, H = 1720, 1380
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    ax.text(W / 2, 40, "DRB102 firewall bulkhead - insert face (TE drawing view) - from docs/harness/MASTER-wirelist.csv",
            ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(436, 107, "Left wedgelock half (52-102)", ha="center", fontsize=13)
    ax.text(1278, 107, "Right wedgelock half (1-51)", ha="center", fontsize=13)
    ax.plot([857, 857], [135, 1175], color="black", linestyle="--", linewidth=1.2)
    xs = [85 + i * 140 for i in range(12)]
    step, mid = 85, 647
    for ci, col in enumerate(DRB_COLS):
        top = mid - (len(col) - 1) * step / 2
        for k, n in enumerate(col):
            if n is None:
                continue
            short, kd = cav.get(n, ("spare", "spare"))
            y = top + k * step
            ax.add_patch(Circle((xs[ci], y), DRB_RADIUS[DRB_SIZE.get(n, 16)], facecolor="#" + DRB_FILL[kd], edgecolor="black",
                                linewidth=1.5, zorder=2))
            ax.text(xs[ci], y, str(n), ha="center", va="center", fontsize=11, fontweight="bold",
                    color="black" if kd in ("spare", "signal") else "white", zorder=3)
            if kd != "spare":
                ax.text(xs[ci], y + 31, short[:26], ha="center", va="center", fontsize=7, zorder=3)
    for i, (k, label) in enumerate(DRB_LEGEND):
        x, y = 85 + (i % 5) * 318, 1232 + (i // 5) * 59
        ax.add_patch(Circle((x, y), 18, facecolor="#" + DRB_FILL[k], edgecolor="black", linewidth=1.5))
        ax.text(x + 30, y, label, va="center", fontsize=12)
    ax.text(W - 40, 1330, "Circle size = contact size\n(size 4 > 8 > 12 > 16)", ha="right", va="center", fontsize=11)
    fig.savefig(path, dpi=100, metadata={"Description": drb_digest(rows)})
    plt.close(fig)


def main(argv):
    check_mode = "--check" in argv
    want = [a for a in argv if not a.startswith("-")]
    hs = want or own_harnesses()
    rows = master_rows()
    if check_mode:
        bad = []
        for h in hs:
            b = check(h)
            print("%s: %s" % (h, "drawing set current, every wire end on the layout" if not b else "%d finding(s)" % len(b)))
            for x in b:
                print("   FAIL", x)
            bad += b
        if drb_png_digest(DRB_PNG) != drb_digest(rows):
            bad.append("DRB102-bulkhead-map.png is stale against the master")
            print("   FAIL DRB102-bulkhead-map.png is stale against the master: run build_drawings.py")
        if not want and pending_harnesses():
            print("pending (not in a drawing set yet): %s" % ", ".join(pending_harnesses()))
        print("build_drawings --check: %s" % ("FAIL" if bad else "OK"))
        return 1 if bad else 0
    for h in hs:
        build(h)
    if drb_png_digest(DRB_PNG) != drb_digest(rows):
        drb_render(rows, DRB_PNG)
        print("wrote", os.path.relpath(DRB_PNG, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
