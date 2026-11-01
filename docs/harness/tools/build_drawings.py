#!/usr/bin/env python
"""The harness layout trees and per-harness wire lists, from the ONE master wire list (DECISIONS B5 / B6).

Harnesses are BUILT in harness.design (Dan 2026-11-01); this script makes no drawings. The layout and schematic PDFs it
used to write are retired (git history keeps them). What it still does, for the master and the other scripts:

  1. LAYOUT TREE  `tools/<set>.layout.json` (nodes, xy, segments, place / place_oem) plus `route_trees` built from the
                  approved route data (Routes 16 / 17; B8): every wire end is placed, every wire is routed, and the
                  master `est_length_mm` must equal its tree length. harness.design generators import `Harness` /
                  `route()` from here for the same tree.
  2. WIRE LISTS   the per-harness wire lists in docs/harness/wirelists/ (Option A, DECISIONS "Wire lists"), read back.
  3. DRB102 MAP   docs/harness/drawings/DRB102-bulkhead-map.png (insert face, from the master); build_pin_chart.py reads
                  DRB_COLS / DRB_SIZE.
  Also: `od()` / `dr25_for()` give the DR-25 size per segment for docs/sourcing/build_project_bom.py.

    python docs/harness/tools/build_drawings.py [set]          write the wire lists and the DRB102 map
    python docs/harness/tools/build_drawings.py --check [set]  fail if a wire end is not on the tree, a length is off,
                                                              or a wire list / the DRB102 map is stale
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

STYLE = "own-drawings v5 (one colour per wire, approved routes)"   # part of the DRB102 map digest: do not change
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


def paths(h):
    return {"dir": DRAWINGS, "layout": os.path.join(HERE, "%s.layout.json" % h)}


# ------------------------------------------------------------------------------------------------ the model
class Harness:
    def __init__(self, h):
        self.h = h
        self.set = set(set_harnesses(h))
        self.p = paths(h)
        self.layout = load(self.p["layout"])
        add_route_trees(self.layout)
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
    for name in wirelist_harnesses(H):
        have, want_wl = xlsx_digest(wirelist_path(name)), wirelist_digest(H, name)
        if have != want_wl:
            bad.append("%s is stale (inputs %s, made from %s): run build_drawings.py %s"
                       % (os.path.basename(wirelist_path(name)), want_wl, have or "none", h))
        else:
            bad += wirelist_readback(name)
    for p in glob.glob(os.path.join(DRAWINGS, "%s-*.pdf" % h)):
        bad.append("%s: drawing PDFs are retired (Dan 2026-11-01; harnesses are built in harness.design): delete it"
                   % os.path.basename(p))
    return bad


def pin_sort(p):
    m = re.match(r"([A-Za-z +/-]*?)(\d+)(.*)", p or "")
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (p or "", 0, "")


# ------------------------------------------------------------------------------------------------ per-harness wire lists
# One From / To wire list per harness (Dan 2026-10-26), generated from the master like every other view. Column names
# follow the harness.design Excel-import example (Wire, From, From Pin, To, To Pin, Signal, Colour, Gauge (AWG), Length (mm);
# Connectors sheet Connector, Part Number: docs.harness.design/guides/excel-import), then the build detail.
WIRELISTS = os.path.join(HARNESS, "wirelists")
WL_COLS = [("Wire", 14), ("From", 20), ("From Pin", 9), ("To", 20), ("To Pin", 9), ("Splice", 24), ("Branch", 11),
           ("Signal", 30), ("Colour", 9), ("Gauge (AWG)", 8), ("Length (mm)", 9), ("Wire Type", 17), ("Cable", 15),
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
                    "Colour": r["colour"], "Gauge (AWG)": r["gauge_awg"],
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
    device ends with their pins, gauge and colour; From / To never a splice and never blank; one trunk per splice."""
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
        for col_name, key in (("Gauge (AWG)", "gauge_awg"), ("Colour", "colour")):
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
                 "Colour = insulation colour (harness.design colour names). No ident bands (Dan 2026-10-31).",
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


# ------------------------------------------------------------------------------------------------ layout trees from a route file
# DECISIONS B8 (Dan 2026-10-28): a route file's devices and runs are the one definition of where each device sits and
# which line it hangs on; lengths from a route map = map length x 5.3 mm per EWD point (the 96 mm cylinder spacing)
# + 300 mm drop for a low-mounted part (device "low": true), an estimate until measured at the car.
MM_PER_PT = 5.3
DROP_MM = 300
MIN_BREAKOUT_MM = 152   # a connector part-way along a line sits at least 6 in off it; the last one on a line may end it
JOIN_PT = 15.0   # a line or branch end this close to another line joins it


def _seg_proj(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy
    t = 0.0 if not ll else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ll))
    q = (a[0] + t * dx, a[1] + t * dy)
    return math.hypot(p[0] - q[0], p[1] - q[1]), q


def _along(pts, p):
    """(gap, distance along pts) of point p projected onto the polyline pts."""
    best, run = None, 0.0
    for a, b in zip(pts, pts[1:]):
        gap, q = _seg_proj(p, a, b)
        if best is None or gap < best[0] - 1e-9:
            best = (gap, run + math.hypot(q[0] - a[0], q[1] - a[1]))
        run += math.hypot(b[0] - a[0], b[1] - a[1])
    return best


def _pt_at(pts, dist):
    run = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if run + L >= dist - 1e-9:
            t = 0.0 if not L else (dist - run) / L
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        run += L
    return tuple(pts[-1])


def route_data(name):
    """The route data of a route file in docs/harness/routes/ (its `route-data` JSON)."""
    text = open(os.path.join(HARNESS, "routes", name), encoding="utf-8").read()
    return json.loads(re.search(r'<script type="application/json" id="route-data">(.*?)</script>', text, re.S).group(1))


def route_lines(data):
    """A route file's lines by id: Route 16 routes L1-L9, the low parts of route 9 (L9b starter, L9c alternator) and its
    runs; Route 17 runs by their first word (10-13, RH, F1-F21; the second run 11, the siren branch, is 11b)."""
    lines = {}
    for r in data.get("routes") or []:
        lines["L%s" % r["n"]] = [tuple(p) for p in r["path"]]
        for k, extra in enumerate(r.get("low_behind_engine") or []):
            lines["L%s%s" % (r["n"], "bcdefg"[k])] = [tuple(p) for p in extra]
    for name, pts in (data.get("runs") or {}).items():
        k = name.split()[0]
        while k in lines:
            k += "b"
        lines[k] = [tuple(p) for p in pts]
    return lines


def add_route_trees(L):
    """Add to the layout the tree of each route file named in its `route_trees` (one definition, DECISIONS B8).

    Each entry: {"route": file in docs/harness/routes/, "harness": the harness it carries}, and either
    - "root": the bulkhead node (Route 16): the root sits at the start of line L1; a device of the harness, or one whose
      node other harnesses' segments reach, joins the line it is on; a device's node is its layout `place` node; or
    - "roots": {line: cabin node} (Route 17: run 10 starts at the RH fender exit, run 11 at the driver kick), with
      "with": other route files whose lines this tree may also use (Route 16 line 6 for the A/C), "line_from": {line:
      line it hangs on} where the route data names none, "devices": {device n: node} for the route's own devices and
      {"<file>#<n>": {"node", "ids"}} for a device of a "with" file, and "prefix" so its junction nodes are its own.
    Every other line or branch joins the line its end lies closest to; a device joins the line it is on (a stub when it
    sits off it). Only the parts that lead to a device of the tree are kept.
    """
    for spec in L.get("route_trees", []):
        legacy = "roots" not in spec
        data = route_data(spec["route"])
        lines = route_lines(data)
        num = lambda f: "Route " + re.search(r"ROUTE-(\d+)", f).group(1)
        src = {k: num(spec["route"]) for k in lines}
        hint = dict(data.get("line_from") or {}, **(data.get("run_from") or {}))
        devs = []
        for d in data.get("devices") or []:
            if legacy:
                devs.append(dict(d, _route=num(spec["route"])))
            elif str(d.get("n")) in spec.get("devices", {}):
                devs.append(dict(d, _route=num(spec["route"]), _node=spec["devices"][str(d["n"])], _ids=[]))
        for f in spec.get("with", []):
            other = route_data(f)
            for k, pts in route_lines(other).items():
                if k in lines:
                    raise SystemExit("route_trees: line %s is in both %s and %s" % (k, spec["route"], f))
                lines[k], src[k] = pts, num(f)
            hint.update(other.get("line_from") or {}, **(other.get("run_from") or {}))
            for d in other.get("devices") or []:
                pick = spec.get("devices", {}).get("%s#%s" % (f, d.get("n")))
                if pick:
                    devs.append(dict(d, _route=num(f), _node=pick["node"], _ids=pick.get("ids", [])))
        hint.update(spec.get("line_from") or {})
        roots = {"L1": spec["root"]} if legacy else spec["roots"]
        pre = spec.get("prefix", "")
        root_pt = lines["L1"][0] if legacy else None
        # a main line that passes the root (route 9 by the bulkhead) is split there into two lines that start at it
        for k in [k for k in lines if legacy and k.startswith("L") and k != "L1"]:
            pts = lines[k]
            gap, d = _along(pts, root_pt)
            total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
            if gap <= JOIN_PT and 1.0 < d < total - 1.0:
                q, run, head, tail = _pt_at(pts, d), 0.0, [], []
                for a, b in zip(pts, pts[1:]):
                    (head if run + math.hypot(b[0] - a[0], b[1] - a[1]) <= d else tail).append(b)
                    run += math.hypot(b[0] - a[0], b[1] - a[1])
                lines[k] = [q] + tail
                lines[k + "-in"] = [q] + head[::-1] + [pts[0]]
                src[k + "-in"] = src[k]
        # join order: each line hangs on the line (or the root) its nearer end lies closest to
        parent = {k: (None, 0.0, 0.0, "start") for k in roots}
        todo = [k for k in lines if k not in roots]
        for k in todo[:] if legacy else []:
            if math.hypot(lines[k][0][0] - root_pt[0], lines[k][0][1] - root_pt[1]) <= JOIN_PT and "-in" not in k \
                    and any(x == k + "-in" for x in lines):
                parent[k] = (None, 0.0, math.hypot(lines[k][0][0] - root_pt[0], lines[k][0][1] - root_pt[1]), "start")
                parent[k + "-in"] = (None, 0.0, parent[k][2], "start")
                todo.remove(k)
                todo.remove(k + "-in")
        while todo:
            best = None
            for k in todo:
                for end in ("start", "end"):
                    p = lines[k][0] if end == "start" else lines[k][-1]
                    for j in parent:
                        want_j = hint.get(k.split("-")[0])
                        if want_j and j.split("-")[0] != want_j:   # the route data (or the layout) names the line it hangs on
                            continue
                        if k.startswith("L") and not j.startswith("L") and not want_j:   # a main line hangs on a main line
                            continue
                        gap, d = _along(lines[j], p)
                        if best is None or gap < best[0]:
                            best = (gap, k, j, d, end)
            if best is None:
                break
            gap, k, j, d, end = best
            if gap > JOIN_PT:
                break
            parent[k] = (j, d, gap, end)
            todo.remove(k)
        # events along each line: where children join and where devices sit (distance from the line's own root end)
        def from_root(k, d):
            j, _, _, end = parent[k]
            total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(lines[k], lines[k][1:]))
            return d if end == "start" else total - d
        ev = collections.defaultdict(list)
        for k, (j, d, gap, end) in parent.items():
            if j is not None:
                ev[j].append((from_root(j, d), "line", k, gap))
        place = L.setdefault("place", {})
        want, used = set(), set()
        linked = {n for seg in L["segments"] for n in seg[:2]}   # nodes other harnesses' segments already reach
        for dev in devs:
            if legacy:
                ids = [x.strip() for x in str(dev.get("id", dev["name"])).split("/")]
                node = place.get(ids[0]) or ids[0]
                if spec["harness"] not in dev.get("harness", "") and node not in linked:
                    continue
                if node in used:   # two devices placed on one old node (MR-S plugs B / C) get a node each
                    node = ids[0].replace("-", "_")
            else:
                ids, node = dev["_ids"], dev["_node"]
            used.add(node)
            on = dev["on"] if dev.get("on") in parent else min(parent, key=lambda k: _along(lines[k], dev["at"])[0])
            gap, d = _along(lines[on], dev["at"])
            ev[on].append((from_root(on, d), "dev", node, gap, dev))
            for i in ids:
                place[i] = node
            want.add(on)
        # keep only the lines that lead to a device
        keep = set()
        for k in want:
            while k is not None and k not in keep:
                keep.add(k)
                k = parent[k][0]
        nodes, segs = L["nodes"], L["segments"]
        first_seg = len(segs)
        fx = lambda p: [round(90 + (p[1] - 160) * 0.35, 1), round((p[0] - 170) * 100.0 / 220.0, 1)]
        if legacy:
            nodes[spec["root"]]["xy"] = fx(root_pt)
        def build(k, start_node):
            here, at = start_node, 0.0
            items = sorted((e for e in ev[k] if e[1] == "dev" or e[2] in keep), key=lambda e: (e[0], e[1]))
            n_j = 0
            for i_e, e in enumerate(items):
                step = max(0.0, e[0] - at) * MM_PER_PT
                if e[1] == "line":
                    n_j += 1
                    jn = "%sJ_%s_%d" % (pre, k, n_j)
                    nodes[jn] = {"xy": fx(_pt_at(lines[k] if parent[k][3] == "start" else lines[k][::-1], e[0])),
                                 "label": "%s %s: %s joins" % (src[k], k, e[2]), "short": "%s / %s" % (k, e[2])}
                    segs.append([here, jn, int(round(step))])
                    here, at = jn, e[0]
                    if e[3] * MM_PER_PT < 1:
                        build(e[2], jn)
                    else:
                        build_stub(e[2], jn, e[3])
                else:
                    node, gap, dev = e[2], e[3], e[4]
                    drop = DROP_MM if dev.get("low") else 0
                    old = nodes.get(node, {})
                    nodes[node] = {"xy": fx(dev["at"]), "end": True, "short": old.get("short", dev["name"]),
                                   "label": "%s (%s device %s on %s%s)" % (
                                       dev["name"], dev["_route"], dev["n"], k, ", low: +%d mm drop" % drop if drop else "")}
                    stub = gap * MM_PER_PT + drop
                    if i_e < len(items) - 1:   # the line goes on past it: a breakout of at least 6 in (Dan 2026-10-29)
                        stub = max(stub, MIN_BREAKOUT_MM)
                    if stub >= 1:
                        tap = "%sT_%s_%s" % (pre, k, node)
                        nodes[tap] = {"xy": fx(_pt_at(lines[k] if parent[k][3] == "start" else lines[k][::-1], e[0])),
                                      "label": "%s %s: %s stub" % (src[k], k, node), "short": ""}
                        segs.append([here, tap, int(round(step))])
                        segs.append([tap, node, int(round(stub))])
                        here, at = tap, e[0]
                    else:
                        segs.append([here, node, int(round(step))])
                        here, at = node, e[0]
        def build_stub(k, jn, gap):
            sub = "%sS_%s" % (pre, k)
            nodes[sub] = {"xy": nodes[jn]["xy"], "label": "%s %s joins (%.0f mm gap)" % (src[k], k, gap * MM_PER_PT),
                          "short": ""}
            segs.append([jn, sub, int(round(gap * MM_PER_PT))])
            build(k, sub)
        start = spec.get("root")
        if spec.get("root_drop_mm"):   # the bulkhead sits this far above where the trunk meets the firewall (Dan 2026-10-29)
            start = "J_%s_drop" % spec["root"]
            nodes[start] = {"xy": nodes[spec["root"]]["xy"], "label": "Route 16: trunk meets the firewall below the bulkhead",
                            "short": ""}
            segs.append([spec["root"], start, int(spec["root_drop_mm"])])
        for k in [k for k, v in parent.items() if v[0] is None]:
            if k in keep:
                if k in roots:
                    build(k, start if legacy else roots[k])
                else:
                    build_stub(k, start, parent[k][2])
        # splices, resistors and cable screens whose old node is gone sit where their wires part: the deepest node
        # common to the paths from the root to every other end of their wires (the root itself is the trunk end; a
        # "roots" tree looks only at its own segments, so its cabin ends count as the root end)
        top = [spec["root"]] if legacy else list(roots.values())
        up, todo = {n: None for n in top}, list(top)
        adj = collections.defaultdict(list)
        for a, b, _ in (segs if legacy else segs[first_seg:]):
            adj[a].append(b)
            adj[b].append(a)
        while todo:
            n = todo.pop(0)
            for m in adj[n]:
                if m not in up:
                    up[m] = n
                    todo.append(m)
        def chain(n):
            out = []
            while n is not None:
                out.append(n)
                n = up.get(n)
            return out[::-1]
        rows = [r for r in master_rows() if r["wire_id"] and spec["harness"] in (r["harness"], r["passes_through"])]
        def at(r, s):   # a "roots" tree also places factory ends (by `place_oem`, as Harness.place does)
            if legacy or r[s + "_type"] != "OEM":
                return place.get(r[s + "_id"])
            return next((n for pat, n in L.get("place_oem", []) if pat in r[s + "_id"] + " " + r[s + "_name"]), None)
        for _ in range(4):
            for c in sorted({r[s + "_id"] for r in rows for s in ("from", "to") if legacy or r[s + "_type"] != "OEM"}
                            | {r["cable"] for r in rows if r["cable"]}):
                if not c or place.get(c) in nodes:
                    continue
                ends = set()
                for r in rows:
                    for s, o in (("from", "to"), ("to", "from")):
                        if r[s + "_id"] == c or r["cable"] == c:
                            n = at(r, o)
                            if n in up and n not in top:
                                ends.add(n)
                if not ends:   # a cable screen whose only other end is the bulkhead sits with its cable
                    cab = {place.get(r["cable"]) for r in rows if c in (r["from_id"], r["to_id"]) and r["cable"]}
                    ends = {n for n in cab if n in up and n not in top}
                if not ends:
                    continue
                chains = [chain(n) for n in ends]
                common = [x for x in zip(*chains) if len(set(x)) == 1]
                place[c] = common[-1][0] if common else top[0]


# ------------------------------------------------------------------------------------------------ build
def build(h):
    """Route every wire on the layout tree (lengths, problems), then write the per-harness wire lists."""
    H = Harness(h)
    for r in H.wires:
        H.route(r)
    if H.problems:
        for p in H.problems:
            print("PROBLEM", p)
        raise SystemExit("not written: %d problem(s)" % len(H.problems))
    for name in wirelist_harnesses(H):
        wl = write_wirelist(H, name)
        if wl:
            print("wrote", os.path.relpath(wl, REPO))


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
