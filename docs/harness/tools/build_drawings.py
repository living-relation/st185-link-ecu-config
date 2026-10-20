#!/usr/bin/env python
"""Our own harness drawings, generated from the ONE master wire list (DECISIONS R220 / R221).

A drawing set is one or more harnesses of docs/harness/MASTER-wirelist.csv drawn as one: its layout spec
`tools/<set>.layout.json` names them (`"harnesses": [...]`) and holds the physical tree; `tools/<set>.revs.json` is its rev
log. Combining one more harness later = add it to `harnesses` (and its branches to the tree), then re-run. It writes, to
docs/harness/drawings/, THREE single-page PDFs `<set>-schematic.pdf`, `<set>-layout.pdf`, `<set>-pinout.pdf` (Dan, 2026-10-19: "one big sheet for the schematics one big
sheet for the layout view and one big sheet for the pinout tables just by themselves"). Each sheet is sized to what it holds
and grows as harnesses join the set; nothing is split across sheets; each has its own title block and rev log.

  1. SCHEMATIC    the wires grouped by job (through the bulkhead, the ECU splice point, cabin branches, shield
                  drains), one whole panel per job. Every connector, bus, splice and end is a pinout table (pin |
                  signal); every wire is drawn point to point from its pin row to its other pin row on its own
                  track, labelled at both ends with its id, gauge, colour and ident bands. A wire the list says is
                  built with another harness is dashed.
  2. LAYOUT       the physical trunk and branches as a top view (front of the car to the right, driver side up,
                  R140 / R153): every segment with its length, its wire count and the DR-25 size for its bundle;
                  the branch points, the ECU splice point, the bulkhead and every end. Not to scale.
  3. PINOUT       one table per connector, bus, splice and end (never split): every pin, its wire, gauge, colour,
                  bands, signal, other end and estimated cut length; spare pins take a sealing plug.

and, untracked, docs/harness/out/<set>-pinout.xlsx (the same table) and a thumbnail. The PDF carries the digest of its
inputs in its Keywords, so --check needs no PDF library. Title block and rev log per R200.

    python docs/harness/tools/build_drawings.py [set]          write (needs PyMuPDF + openpyxl)
    python docs/harness/tools/build_drawings.py --check [set]  fail if a drawing set is stale against its inputs,
                                                              or a wire end is not on the layout (no PyMuPDF)

Nothing on these sheets is placed or typed by hand except the layout tree (node positions, segment lengths) and the
rev log; the scripts never write into the master.
"""
import collections
import csv
import glob
import hashlib
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

STYLE = "own-drawings v2 (three big sheets)"
PW, PH = 1224.0, 792.0                     # the current page (set_page); a schematic panel is PANEL_W wide
PANEL_W = 1224.0
M = 18.0                                   # page margin
TB_W, TB_H = 372.0, 128.0                  # title block (bottom right)
INK = (0.08, 0.13, 0.24)
GREY = (0.55, 0.57, 0.62)
LIGHT = (0.93, 0.94, 0.96)
AGENT = re.compile(r"claude|grok|stevecad|fairsolid|agent|unknown|cursor|codex", re.I)
WIRE_RGB = {"Red": (0.78, 0.16, 0.16), "Black": (0.1, 0.1, 0.1), "Orange": (0.93, 0.45, 0.0), "Blue": (0.12, 0.38, 0.8),
            "White": (0.55, 0.55, 0.55), "Green": (0.18, 0.55, 0.25), "Yellow": (0.85, 0.68, 0.0), "Shield": (0.45, 0.45, 0.45)}
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
        if t == "OEM":
            return ("oem", c + "|" + r[s + "_pin"])
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
    for p in glob.glob(os.path.join(DRAWINGS, "%s-*.pdf" % h)):
        if p not in H.p["pdfs"]:
            bad.append("%s is not one of the three sheets of the set (delete it)" % os.path.basename(p))
    return bad


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
    cells = [("DRAWING NO.", "ST185-%s%s" % (H.h, dwg), 110), ("REV", cur["rev"], 30), ("SHEET", "%d OF %d" % (sheet_no, sheets), 52),
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
def layout_sheet(S, H):
    L = H.layout
    nodes = L["nodes"]
    seg_w = {}
    seg_od = {}
    count = {}
    for r in H.wires:
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

    S.text(M + 8, M + 16, "LAYOUT - top view, front of the car to the RIGHT, driver side UP (R140 / R153). Not to scale; "
           "lengths in mm (estimates until measured at the car).", 8, "hebo")
    S.text(M + 8, M + 27, "Each segment: length | wires in it | DR-25 heat-shrink size for its bundle (est. from the wire ODs). "
           "Lengths per wire (path + %d mm at each end) are in the pinout table." % L.get("end_allowance_mm", 100), 6.5)
    S.text(ax1 - 40, M + 50, "FRONT  -->", 7, "hebo", GREY)
    S.text(M + 8, M + 50, "^ DRIVER SIDE (LH) at the top  /  PASSENGER SIDE (RH) at the bottom v", 6.5, "hebo", GREY)
    table = []
    for a, b, mm in L["segments"]:
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
        names = sorted({short_name(H, c) for c in placed.get(n, [])})
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
TRK = 3.2        # track pitch in the outer channels


def schematic_sheet(S, H, title, i, n, rows, with_legend=True):
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
    # channel jobs and tracks (tracks depend only on the row heights)
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
    LW, RW = 200.0, 214.0
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
    step = min(4.0, (cx1 - cx0) / (ntr["C"] + 1)) if ntr["C"] else 4.0
    for ch, r, a, z, ya, yz, t in jobs:
        dashed = "[3 2] 0" if r["harness"] != H.h else None
        col = WIRE_RGB.get(r["colour"], INK)
        width = 0.55 if r["colour"] != "Shield" else 0.45
        if ch == "C":
            (la, ly), (lz, lyz) = ((a, ya), (z, yz)) if sides[a.key] == 0 else ((z, yz), (a, ya))
            tx = cx0 + step * (t + 1)
            S.line([(la.x1, ly), (tx, ly), (tx, lyz), (lz.x0, lyz)], col, width, dashed)
            wire_label(S, r, la.x1 + 3, ly - 1.4)
            wire_label(S, r, lz.x0 - LANE + 3, lyz - 1.4)
        elif ch == "L":
            tx = lx0 - LANE - 6 - TRK * t
            S.line([(a.x0, ya), (tx, ya), (tx, yz), (z.x0, yz)], col, width, dashed)
            wire_label(S, r, a.x0 - LANE + 3, ya - 1.4)
            wire_label(S, r, z.x0 - LANE + 3, yz - 1.4)
        else:
            tx = rx1 + LANE + 6 + TRK * t
            S.line([(a.x1, ya), (tx, ya), (tx, yz), (z.x1, yz)], col, width, dashed)
            wire_label(S, r, a.x1 + 3, ya - 1.4)
            wire_label(S, r, z.x1 + 3, yz - 1.4)
    S.text(M + 8, M + 16, "%s%s" % (title, "" if n == 1 else "  (part %d of %d)" % (i, n)), 8, "hebo")
    if with_legend:
        legend(S, PH - M - 40)


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
    if key == ("connector", "DRB102-CABIN"):
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
    pinw = 30.0
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
                        "_k": (order_key(H, key), pin_sort(r[s + "_pin"]))})
    for r in H.spares:
        key = H.end_key(r, "from")
        out.append({"END": H.title(key, r, "from"), "_sub": table_sub(H, key, r, "from"), "PIN": r["from_pin"], "WIRE": "",
                    "AWG": "", "COLOUR": "", "BANDS": "",
                    "SIGNAL": r["from_desc"], "OTHER END": "", "LEN MM": "", "BUILT WITH": "", "CIRCUIT": "",
                    "_k": (order_key(H, key), pin_sort(r["from_pin"]))})
    out.sort(key=lambda x: x["_k"])
    return out


TABLE_COLS = [c for c in PIN_COLS if c[0] != "END"]   # one table per end: its name is the table header
TABLE_W = sum(w for _, w in TABLE_COLS) + 8
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


def pack(heights, k):
    """Split heights (in order) into at most k columns of about even height; -> [[index ...]]."""
    target = max(max(heights), sum(heights) / k)
    cols, cur, h = [], [], 0.0
    for i, x in enumerate(heights):
        # start a new column when this item's middle would pass the target (keeps the columns even, order kept)
        if cur and h + x / 2 > target + 1e-6 and len(cols) < k - 1:
            cols.append(cur)
            cur, h = [], 0.0
        cur.append(i)
        h += x
    cols.append(cur)
    return cols


def best_pack(heights, col_w, extra_w, extra_h, kmax=8):
    """The column count whose sheet is closest to the ISO aspect (1.414 : 1, landscape)."""
    best = None
    for k in range(1, min(kmax, len(heights)) + 1):
        cols = pack(heights, k)
        w = extra_w + len(cols) * col_w
        h = extra_h + max(sum(heights[i] for i in c) for c in cols)
        score = abs(w / h - 1.414)
        if best is None or score < best[0] - 1e-9:
            best = (score, cols, w, h)
    return best[1], best[2], best[3]


def pinout_size(tables):
    hs = [table_h(tb) + T_GAP for tb in tables]
    cols, w, h = best_pack(hs, TABLE_W + 16, 2 * M + 16, M + 44 + TB_H + 30 + M)
    return cols, w, h


def pinout_sheet(S, tables, cols):
    S.text(M + 8, M + 16, "PINOUT TABLES - one table per connector, bus plug, splice and end of the set; every pin, the wire on "
           "it and where its other end lands", 8, "hebo")
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


# ------------------------------------------------------------------------------------------------ build
def panel_height(H, rows):
    bl = blocks_for(H, rows)
    sides = choose_sides(H, rows)
    cols = [0.0, 0.0]
    for k, b in bl.items():
        cols[sides[k]] += b.height() + GAP_B
    return COL_TOP + max(cols) + 16


def schematic_big(doc, fitz, H):
    """Each job group drawn whole as one panel (a temporary page), then the panels placed in columns on ONE sheet."""
    panels = []
    tmp = fitz.open()
    for g, title in GROUPS:
        rows = [r for r in H.wires if group_of(H, r) == g]
        if not rows:
            continue
        ph = panel_height(H, rows)
        set_page(PANEL_W, ph, title_block=False)
        S = Sheet(tmp, fitz)
        schematic_sheet(S, H, title, 1, 1, rows, with_legend=False)
        panels.append((len(tmp) - 1, ph))
    GAPP = 14.0
    cols, w, h = best_pack([p[1] + GAPP for p in panels], PANEL_W + GAPP, 2 * M + 8, M + 44 + 30 + TB_H + 20 + M)
    set_page(w, h)
    S = Sheet(doc, fitz)
    S.text(M + 8, M + 16, "SCHEMATIC - every wire of the set, grouped by job; neat, not to scale", 8, "hebo")
    S.text(M + 8, M + 27, "Tables are pinouts (pin | signal) of the pins each panel uses; the PINOUT TABLES sheet has every pin. "
           "Wire label: id  AWG  colour  [ident bands]. Dashed = built with the harness named in its table; grey header = an "
           "end on another harness.", 6)
    legend(S, M + 38)
    for ci, col in enumerate(cols):
        x0 = M + 4 + ci * (PANEL_W + GAPP)
        y = M + 44
        for i in col:
            pno, ph = panels[i]
            r = fitz.Rect(x0, y, x0 + PANEL_W, y + ph)
            S.page.show_pdf_page(r, tmp, pno)
            S.rect(r.x0, r.y0, r.x1, r.y1, color=GREY, width=0.5)
            y += ph + GAPP
    return S


def layout_size(H):
    n, nseg = len(H.layout["nodes"]), len(H.layout["segments"])
    aw = max(860.0, 46.0 * n)
    w = M + 40 + aw + 500 + M
    h = max(M + 70 + aw * 0.62 + 50 + M,
            M + 61 + 8.5 * nseg + 14 + 8 * n + 14 + 6 * 7.5 + 30 + TB_H + M)
    return w, h


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
    prow = pinout_rows(H)
    doc = fitz.open()
    # each sheet is finished (title block included) before the next page is made: PyMuPDF page handles go stale
    S = schematic_big(doc, fitz, H)
    title_block(S, H, 1, 1, SHEETS[0][2], "-" + SHEETS[0][1])
    set_page(*layout_size(H))
    S = Sheet(doc, fitz)
    layout_sheet(S, H)
    title_block(S, H, 1, 1, SHEETS[1][2], "-" + SHEETS[1][1])
    tables = pinout_tables(H, prow)
    cols, w, hh = pinout_size(tables)
    set_page(w, hh)
    S = Sheet(doc, fitz)
    pinout_sheet(S, tables, cols)
    title_block(S, H, 1, 1, SHEETS[2][2], "-" + SHEETS[2][1])
    # three separate drawings, one page each (Dan: one big sheet per view)
    for i, (k, code, what) in enumerate(SHEETS):
        one = fitz.open()
        one.insert_pdf(doc, from_page=i, to_page=i)
        one.set_metadata({"title": "%s - %s" % (H.revs["title"], what), "author": H.revs["revs"][0]["by"],
                          "subject": H.revs["subtitle"], "keywords": "inputs %s" % digest(h), "creator": "build_drawings.py",
                          "producer": "PyMuPDF", "creationDate": "", "modDate": ""})
        one.save(H.p["pdfs"][i], garbage=3, deflate=True)
    # hub thumbnail: the layout sheet, 360 px wide (as the loom tiles)
    lay = doc[1]
    pix = lay.get_pixmap(matrix=fitz.Matrix(360 / lay.rect.width, 360 / lay.rect.width))
    os.makedirs(OUT, exist_ok=True)
    pix.save(H.p["thumb"])
    write_xlsx(H, prow, H.p["xlsx"])
    print("wrote %s (%s), %s, %s" % (", ".join(os.path.relpath(p, REPO) for p in H.p["pdfs"]),
                                               ", ".join("%d x %d mm" % (round(p.rect.width / 72 * 25.4), round(p.rect.height / 72 * 25.4))
                                                         for p in doc),
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
