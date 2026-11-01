#!/usr/bin/env python
"""The ONE wiring check (DECISIONS R221). Reads, never writes the SoT.

The wiring source of truth is ONE file, docs/harness/MASTER-wirelist.csv: one row per physical wire (or spare cavity), with
its harness, both ends and the wire. sot/channels.csv holds the ECU channel settings only. This script checks them:

  F1  the master is the only committed wiring CSV under docs/harness, with exactly the master columns
  F2  every connector end has an ID, a name, a housing PN, a pin, a pin source and a terminal PN (TBD allowed - listed);
      every splice / terminal / OEM end has an ID and a name; pins are numbers or letters (BUS2-1, 87a, IN3 ...), never a sign
  F3  nets = splices only: a wire has a net exactly when it lands on a splice or a bussed DT plug, and the net names it
  F4  one wire per cavity (studs and splices excepted)
  E1  every ECU pin a wire lands on is a live pin in sot/channels.csv, and every live ECU pin there has a wire
  E2  the far ends of each ECU power / ground / Gnd Out / sensor-supply / screen pin are of the class the Link G4X guide
      allows (R212); the ECU power grounds join only each other and one wire to the POWER box NEG bar (R216)
  E3  ground classes (R213): low-voltage electronics never end on a chassis ground (known cases: PENDING)
  E4  an ECU output driving a relay lands on coil pin 85 (R219)
  S1  ECU-C 1 carries exactly one plain drain (R207)
  S2  a cable screen floats at the device: its one end is a splice, an ECU screen pin, a bulkhead / inline cavity or the
      VRC screen pin, never a device pin
  S3  every screen / drain reaches an ECU screen pin (A7, B17, C1), and no two of those pins meet
  M1  every DRB102 cavity and inline-pair cavity wired on one half is wired on the other
  M2  DRB102 contacts: size 16 cavities take 16-20 AWG, size 12 take 12-14 AWG, size 8 / 4 stay spare (TE drawing
      DRB12-102PXE-L018 rev C3); a contact the maker does not list for the housing fails (MAKER_CONTACTS)
  P1  a fuse-box end exists in the fuse-box design (cad/fusebox/rev7/wiring_plan.json, R204) with the same gauge
  R1  the approved route drawings (routes/*.html) lint clean (red lines unfilled, attributes sound, a top view after every
      figure, no overlapping labels); overlapping numbered markers are listed as warnings, since the routes are Dan's (R47)
  X1  XTREMEX-IO-TABLE.html's generated pin map is current with sot/channels.csv (--write-io-table rewrites it)

    python docs/harness/tools/check_wiring.py                 the gate (exit 1 on a finding)
    python docs/harness/tools/check_wiring.py --tbd           also list every TBD cell (what still needs a maker document)
    python docs/harness/tools/check_wiring.py --write-io-table rewrite the IO table's generated pin map
    python docs/harness/tools/check_wiring.py --self-test     prove each check fails on a broken copy (CI)
"""
import collections
import csv
import glob
import html
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(HARNESS))
MASTER = os.path.join(HARNESS, "MASTER-wirelist.csv")
CHANNELS = os.path.join(REPO, "sot", "channels.csv")
PLAN = os.path.join(REPO, "cad", "fusebox", "rev7", "wiring_plan.json")
PARTS = os.path.join(REPO, "docs", "sourcing", "harness-parts.csv")   # maker, description (AWG range) per part
IO_TABLE = os.path.join(REPO, "XTREMEX-IO-TABLE.html")
ROUTES = os.path.join(HARNESS, "routes")

COLS = ["harness", "circuit", "wire_id", "passes_through",
        "from_type", "from_id", "from_name", "from_housing_pn", "from_housing_extra", "from_pin", "from_pin_doc", "from_terminal_pn",
        "from_desc", "from_note",
        "to_type", "to_id", "to_name", "to_housing_pn", "to_housing_extra", "to_pin", "to_pin_doc", "to_terminal_pn",
        "to_desc", "to_note",
        "net", "cable", "cable_pn", "wire_pn", "gauge_awg", "colour",
        "oem_location", "oem_wire_colour", "oem_ewd_page", "oem_method", "route_branch", "est_length_mm", "notes"]
CHANNEL_COLS = ["owner", "channel", "conn", "pin", "label", "class", "dir", "type", "pullup", "status", "source", "notes"]
PIN_RE = re.compile(r"[A-Za-z0-9]+([ -][A-Za-z0-9]+)*")
ECU = {"ECU-A": "ecu_a", "ECU-B": "ecu_b", "ECU-C": "ecu_com"}
SCREEN_PINS = {("ECU-A", "7"), ("ECU-B", "17"), ("ECU-C", "1")}
GROUND_PINS = {("ECU-A", "25"), ("ECU-A", "34"), ("ECU-B", "25"), ("ECU-B", "34")}
NEG_BAR = "POWER-NEG-BAR"
# mated pairs: the two halves of one connector (cavity n mates cavity n)
MATES = {"DRB102-CABIN": "DRB102-ENGINE", "IX-WS-F-S": "IX-WS-F-P", "IX-WS-R-S": "IX-WS-R-P", "IX-FUEL-S": "IX-FUEL-P"}
MATES.update({v: k for k, v in list(MATES.items())})
# inside the VRC boxes the input screen pin is wired to the output screen pin (DECISIONS R31)
INTERNAL = [(("VRC-F-IN", "3"), ("VRC-F-OUT", "3")), (("VRC-R-IN", "3"), ("VRC-R-OUT", "3"))]
DRB_SIZE = {n: 16 for n in range(1, 103)}
DRB_SIZE.update({n: 12 for n in list(range(1, 9)) + list(range(95, 103))})
DRB_SIZE.update({48: 8, 49: 8, 54: 8, 55: 8, 43: 4, 60: 4})
DRB_RANGE = {16: (16, 20), 12: (12, 14)}
# fuse-box ends: master ID -> the id the fuse-box design uses
FB_IDS = {"LOGIC": "fb_logic", "POWER": "fb_power", "BATT-RELAY-BLOCK": "fb_batt", "POWER-STUDS": "pdb"}
FB_PIN = {"BAT": "BAT+", "ALT": "ALT/STR", "NEG": "GND", "BATT": "BATT +", "FP": "FP 40A"}
PLAN_GAUGE = {"53.5": "1/0"}     # the fuse-box design writes 1/0 battery cable as 53.5 (mm2, unit Metric)
ELECTRONICS = re.compile(r"\bLED\b|CAN[- ]?LAMBDA|cluster|RealDash|\bPi\b|CSB3|opto|alarm|valet|shock|status|buck converter|cruise", re.I)
CHASSIS = re.compile(r"^GND-|^T-AT-GND|^T-RL-GND|^ENG-GND|^T-ENG-BLOCK|^T-TRUNK-NEG|chassis", re.I)
QSG_ENDS = {   # far ends each ECU pin class may reach (R212)
    "gndout": re.compile(r"gnd|ground|return|rtn|\(-\)", re.I),
    "screen": re.compile(r"shield|screen|drain", re.I),
    "rail": re.compile(r"\+?\s?[58]\s?V|sensor|cam|pedal|cruise|supply|pull", re.I),
    "power": re.compile(r"relay|fuse|diode|\+12|12\s?V", re.I),
}
# Known violations waiting for their wiring fix (OPEN-ITEMS): printed, not failing; a fixed one must be removed.
PENDING = {"E3:w_at_gnd_a1", "E3:w_at_gnd_b1", "E3:w_at_gnd_b2", "E3:w_at_gnd_c1", "E3:w_led_gnd_out"}
STUD_IDS = re.compile(r"^(POWER-STUDS|KILL-SW|RADLOK-|JUMP-POST|BATT-RELAY-BLOCK)")   # studs: several lugs on one is normal


def read_csv(path, text=None):
    f = io.StringIO(text) if text is not None else open(path, encoding="utf-8", newline="")
    with f:
        r = csv.reader(f)
        head = next(r)
        return head, [dict(zip(head, row)) for row in r]


def ends(r):
    return (("from", "to"), ("to", "from"))


class Graph:
    """Electrical nodes of the master: a connector pin, a splice, a bussed plug, a stud, a cable screen. Mated halves and the
    VRC screen link are one node."""

    def __init__(self, rows):
        self.parent = {}
        self.rows = [r for r in rows if r["wire_id"]]
        for r in self.rows:
            a, b = self.key(r, "from"), self.key(r, "to")
            if a and b:
                self.join(a, b)
        for a, b in INTERNAL:
            self.join(("pin",) + a, ("pin",) + b)

    def key(self, r, s):
        t, i, p = r[s + "_type"], r[s + "_id"], r[s + "_pin"]
        if not i:
            return None
        if t == "connector":
            if i.startswith("BUS-"):
                return ("bus", i)
            return ("pin", min(i, MATES.get(i, i)), p)
        if t in ("splice", "cable screen"):
            return (t, i)
        if t == "terminal":     # a stud or lead end is a sink: lugs on one stud do not make one net
            return (t, i, r["wire_id"])
        return (t, i, p)

    def find(self, k):
        self.parent.setdefault(k, k)
        while self.parent[k] != k:
            self.parent[k] = self.parent[self.parent[k]]
            k = self.parent[k]
        return k

    def join(self, a, b):
        self.parent[self.find(a)] = self.find(b)

    def members(self):
        out = collections.defaultdict(list)
        for r in self.rows:
            k = self.key(r, "from") or self.key(r, "to")
            out[self.find(k)].append(r)
        return out


def far_ends(g, start_rows):
    """Every (row, side) end on the electrical node of these rows, except the ends themselves."""
    root = g.find(g.key(start_rows[0][0], start_rows[0][1]))
    out = []
    for r in g.rows:
        for s in ("from", "to"):
            k = g.key(r, s)
            if k and g.find(k) == root:
                out.append((r, s))
    return out


def check(rows, channels, head=None, ch_head=None, tracked=None, plan=None, lib=None, routes=True, io_table=True):
    bad, tbd, pend = [], collections.defaultdict(set), set()
    warn = []

    def fail(code, msg, key=None):
        k = "%s:%s" % (code, key) if key else None
        if k and k in PENDING:
            pend.add(k)
            return
        bad.append("%s %s" % (code, msg))

    wires = [r for r in rows if r["wire_id"]]
    # ---- F1
    if head is not None and head != COLS:
        fail("F1", "master columns differ from the master column list: %s" % [c for c in head if c not in COLS] or
             [c for c in COLS if c not in head])
    if tracked is not None:
        for f in tracked:
            if f.endswith(".csv") and os.path.basename(f) != "MASTER-wirelist.csv":
                fail("F1", "%s: the only committed wiring CSV is the master (N60)" % f)
    if ch_head is not None and ch_head != CHANNEL_COLS:
        fail("F1", "sot/channels.csv columns are %s, want the ECU settings only: %s" % (ch_head, CHANNEL_COLS))
    # ---- F2 / F3 / F4
    at = collections.defaultdict(list)
    for i, r in enumerate(rows):
        for s, o in ends(r):
            t, eid = r[s + "_type"], r[s + "_id"]
            if not t:
                continue
            where = "%s/%s %s end" % (r["harness"], r["wire_id"] or "spare", s)
            if not eid or not r[s + "_name"]:
                fail("F2", "%s has no ID or no name" % where)
            if t == "connector":
                for col in ("housing_pn", "pin", "pin_doc", "terminal_pn"):
                    v = r["%s_%s" % (s, col)]
                    if not v:
                        fail("F2", "%s %s has no %s" % (where, eid, col))
                    elif v == "TBD":
                        tbd[col].add("%s %s" % (eid, r[s + "_pin"]) if col != "housing_pn" else eid)
                if r[s + "_pin"] and not PIN_RE.fullmatch(r[s + "_pin"]):
                    fail("F2", "%s %s pin %r is not a number / letter" % (where, eid, r[s + "_pin"]))
                if r["wire_id"] and not eid.startswith("BUS-"):
                    at[(eid, r[s + "_pin"])].append(r["wire_id"])
                if r["wire_id"] and eid.startswith("BUS-"):
                    at[(eid, r[s + "_pin"])].append(r["wire_id"])
            elif t in ("OEM", "resistor", "diode"):
                if r[s + "_pin"] and not PIN_RE.fullmatch(r[s + "_pin"]):
                    fail("F2", "%s %s pin %r is not a number / letter" % (where, eid, r[s + "_pin"]))
                if t == "OEM" and r[s + "_pin_doc"] == "TBD":
                    tbd["pin_doc"].add("%s %s" % (eid, r[s + "_pin"]))
            elif t in ("terminal", "splice") and r[s + "_terminal_pn"] == "TBD":
                tbd["terminal_pn"].add(eid)
        if r["wire_id"]:
            sp = [r[s + "_id"] for s in ("from", "to") if r[s + "_type"] == "splice" or
                  (r[s + "_type"] == "connector" and r[s + "_id"].startswith("BUS-"))]
            got = [x.strip() for x in r["net"].split("/") if x.strip()]
            if sorted(set(sp)) != sorted(set(got)):
                fail("F3", "%s/%s net %r: nets are splices only - want %r" % (r["harness"], r["wire_id"], r["net"], " / ".join(sp)))
            for col in ("cable_pn", "wire_pn"):
                if r[col] == "TBD":
                    tbd[col].add(r["cable"] or r["wire_id"])
    for (eid, pin), ws in at.items():
        if len(ws) > 1 and not STUD_IDS.search(eid):
            fail("F4", "%s pin %s has %d wires: %s" % (eid, pin, len(ws), ", ".join(ws)))
    # ---- E1: ECU pins against channels.csv
    ch = {(c["conn"], c["pin"].lower()): c for c in channels if c["owner"] == "ECU"}
    live = {k for k, c in ch.items() if c["class"] not in ("nc", "spare", "N/A") and c["status"] == "set"}
    used = set()
    for r in wires:
        for s, o in ends(r):
            if r[s + "_type"] == "connector" and r[s + "_id"] in ECU:
                conn = ECU[r[s + "_id"]]
                k = (conn, "%s%s" % (conn[-1] if conn != "ecu_com" else "c", r[s + "_pin"]))
                used.add(k)
                if k not in ch:
                    fail("E1", "%s %s %s is not in channels.csv" % (r["wire_id"], r[s + "_id"], r[s + "_pin"]))
                elif k not in live:
                    fail("E1", "%s lands on %s %s, which channels.csv says is %s" % (r["wire_id"], r[s + "_id"], r[s + "_pin"],
                                                                                    ch[k]["class"]))
    for k in sorted(live - used):
        fail("E1", "channels.csv %s %s (%s) is live but the master has no wire on it" % (k[0], k[1], ch[k]["label"]))
    # ---- E2 / E3 / E4
    g = Graph(rows)
    comps = g.members()
    root_of = {}
    for root, rs in comps.items():
        for r in rs:
            root_of[r["wire_id"]] = root

    def node_ends(root):
        out = []
        for r in comps.get(root, []):
            for s in ("from", "to"):
                k = g.key(r, s)
                if k and g.find(k) == root:
                    out.append((r, s))
        return out

    for (cid, pin), cls in [(k, None) for k in []]:
        pass
    done = set()
    for r in wires:
        for s, o in ends(r):
            eid, pin = r[s + "_id"], r[s + "_pin"]
            if r[s + "_type"] != "connector" or eid not in ECU or (eid, pin) in done:
                continue
            done.add((eid, pin))
            c = ch.get((ECU[eid], "%s%s" % (ECU[eid][-1] if ECU[eid] != "ecu_com" else "c", pin)))
            if not c:
                continue
            kind = "gndout" if c["channel"] == "Gnd Out" else c["class"]
            if kind not in ("ground", "gndout", "screen", "rail", "power"):
                if c["dir"] == "out" and r[o + "_id"].startswith("K-") and r[o + "_pin"] != "85":
                    fail("E4", "%s drives relay %s on pin %s, not coil pin 85 (R219)" % (r["wire_id"], r[o + "_id"], r[o + "_pin"]))
                continue
            root = g.find(g.key(r, s))
            for x, xs in node_ends(root):
                xid, xpin, xt = x[xs + "_id"], x[xs + "_pin"], x[xs + "_type"]
                if (xid, xpin) == (eid, pin) or xt in ("splice", "cable screen") or xid.startswith("BUS-") or xid in MATES:
                    continue
                text = "%s %s %s" % (x[xs + "_desc"], x[xs + "_name"], x["circuit"])
                if kind == "ground":
                    if not ((xid, xpin) in GROUND_PINS or xid == NEG_BAR):
                        fail("E2", "ECU ground %s %s reaches %s %s (%s): the ECU grounds join only each other and the NEG bar (R216)"
                             % (eid, pin, xid, xpin, x[xs + "_desc"]))
                elif kind == "screen":
                    if (xid, xpin) not in SCREEN_PINS and not QSG_ENDS["screen"].search(text) and not xid.startswith("VRC-"):
                        fail("E2", "screen pin %s %s reaches %s %s (%s): drains only (R212)" % (eid, pin, xid, xpin, x[xs + "_desc"]))
                elif xt != "resistor" and not QSG_ENDS[kind].search(text):
                    fail("E2", "%s %s (%s) reaches %s %s (%s) (R212)" % (eid, pin, c["channel"], xid, xpin, x[xs + "_desc"]))
    STUDS = re.compile(r"^(POWER-STUDS|BATT-RELAY-BLOCK|KILL-SW|RADLOK|POWER-NEG-BAR|JUMP-POST)")
    for r in wires:
        for s, o in ends(r):
            if r[s + "_type"] == "terminal" and CHASSIS.search(r[s + "_id"] + " " + r[s + "_name"]):
                if STUDS.search(r[o + "_id"]):
                    continue        # a bar / stud bonded to chassis is not a device ground
                if r[o + "_type"] == "splice":
                    near = [(x, xs) for x, xs in node_ends(g.find(g.key(r, o)))]
                else:
                    near = [(r, o)]
                text = " ".join("%s %s %s" % (x[xs + "_id"], x[xs + "_name"], x[xs + "_desc"]) for x, xs in near)
                if ELECTRONICS.search(text):
                    fail("E3", "%s ends on chassis ground %s with low-voltage electronics on it: battery-negative bus only (R213)"
                         % (r["wire_id"], r[s + "_id"]), key=r["wire_id"])
    # ---- S1 / S2 / S3
    c1 = [r for r in wires if any(r[s + "_id"] == "ECU-C" and r[s + "_pin"] == "1" for s in ("from", "to"))]
    if len(c1) != 1 or (c1 and c1[0]["cable"]):
        fail("S1", "ECU-C 1 must carry exactly one plain drain wire, has %s" % [x["wire_id"] for x in c1])
    for r in wires:
        for s, o in ends(r):
            if r[s + "_type"] == "cable screen":
                ot, oid = r[o + "_type"], r[o + "_id"]
                ok = ot == "splice" or (oid, r[o + "_pin"]) in SCREEN_PINS or oid in MATES or oid.startswith("VRC-")
                if not ok:
                    fail("S2", "%s screen lands on %s %s: a screen floats at the device (R27)" % (r["wire_id"], oid, r[o + "_pin"]))
    screen_rows = [r for r in wires if r["colour"] == "Shield" or r["circuit"] == "SHLD" or
                   re.search(r"screen|shield|drain", r["from_desc"] + r["to_desc"], re.I)]
    for root in {root_of[r["wire_id"]] for r in screen_rows}:
        pins = {(x[xs + "_id"], x[xs + "_pin"]) for x, xs in node_ends(root)} & SCREEN_PINS
        if not pins:
            fail("S3", "screen net of %s reaches no ECU screen pin" % sorted({x["wire_id"] for x in comps[root]})[:4])
        if len(pins) > 1:
            fail("S3", "screen pins %s meet (A7, B17 and C1 never touch, R207)" % sorted(pins))
    # ---- M1 / M2
    wired = collections.defaultdict(set)
    for r in wires:
        for s, o in ends(r):
            if r[s + "_id"] in MATES:
                wired[r[s + "_id"]].add(r[s + "_pin"])
    for a, b in MATES.items():
        for p in sorted(wired[a] - wired[b], key=lambda x: (len(x), x)):
            fail("M1", "%s pin %s is wired, %s pin %s is not" % (a, p, b, p))
    lib_awg = {}
    for p in lib or []:
        m = re.search(r"(\d{1,2})-(\d{1,2}) AWG", p["description"]) or re.search(r"\b(\d{1,2}) ?AWG", p["description"])
        if m and p["part_number"]:   # a range ("16-20 AWG") or one size ("(18 AWG)", "20 AWG")
            lib_awg[p["part_number"]] = tuple(sorted((int(m.group(1)), int(m.groups()[-1]))))
    for r in rows:
        for s, o in ends(r):
            eid, pin = r[s + "_id"], r[s + "_pin"]
            if eid.startswith("DRB102") and pin.isdigit():
                size = DRB_SIZE.get(int(pin))
                if size is None:
                    fail("M2", "%s has no cavity %s" % (eid, pin))
                    continue
                if r["wire_id"]:
                    if size not in DRB_RANGE:
                        fail("M2", "%s cavity %s is size %d: stays spare" % (eid, pin, size))
                    elif r["gauge_awg"].isdigit() and not DRB_RANGE[size][0] <= int(r["gauge_awg"]) <= DRB_RANGE[size][1]:
                        fail("M2", "%s %s: %s AWG in a size-%d cavity (%d-%d AWG)" % (eid, pin, r["gauge_awg"], size, *DRB_RANGE[size]))
            if r["wire_id"] and r[s + "_type"] == "connector":
                hp, tp = r[s + "_housing_pn"], r[s + "_terminal_pn"]
                if hp in MAKER_CONTACTS and tp not in ("TBD", "") and tp not in MAKER_CONTACTS[hp]["contacts"]:
                    fail("M2", "%s %s: contact %s is not one %s lists for %s" % (eid, pin, tp, "the maker", hp))
                rng = lib_awg.get(tp)
                if rng and r["gauge_awg"].isdigit() and not rng[0] <= int(r["gauge_awg"]) <= rng[1]:
                    fail("M2", "%s %s (%s): %s AWG outside the contact %s range %d-%d AWG" % (eid, pin, r["wire_id"], r["gauge_awg"],
                                                                                         tp, rng[0], rng[1]))
    # ---- P1 fuse-box design
    if plan:
        plan_end = collections.defaultdict(list)
        for w in plan["wires"]:
            for e in w["ends"]:
                plan_end[(e["id"], e["des"])].append(w)
        for r in wires:
            for s, o in ends(r):
                eid = r[s + "_id"]
                old = FB_IDS.get(eid) or (eid.lower().replace("-", "_") if eid.startswith("K-") else None)
                if not old or r[s + "_type"] != "connector":
                    continue
                pin = FB_PIN.get(r[s + "_pin"], r[s + "_pin"]) if eid in ("POWER-STUDS", "BATT-RELAY-BLOCK") else r[s + "_pin"]
                ws = plan_end.get((old, pin))
                if not ws and old in ("fb_logic", "fb_power", "fb_batt", "pdb"):
                    fail("P1", "%s: fuse-box design has no wire at %s %s (R204)" % (r["wire_id"], eid, r[s + "_pin"]))
                elif ws and r["gauge_awg"] and r["gauge_awg"] not in {PLAN_GAUGE.get(str(w.get("gauge")), str(w.get("gauge"))) for w in ws}:
                    fail("P1", "%s: %s %s is %s AWG in the fuse-box design, %s AWG in the master (R204)" % (
                        r["wire_id"], eid, r[s + "_pin"], "/".join(sorted({PLAN_GAUGE.get(str(w.get("gauge")), str(w.get("gauge"))) for w in ws})), r["gauge_awg"]))
    # ---- R1 routes
    if routes:
        for f in sorted(glob.glob(os.path.join(ROUTES, "*.html"))):
            for x in route_lint(f):
                if "marker labels overlap" in x:
                    warn.append("R1 " + x)
                else:
                    fail("R1", x)
    # ---- X1 IO table
    if io_table:
        cur, new = io_table_texts(channels)
        if cur != new:
            fail("X1", "XTREMEX-IO-TABLE.html pin map is stale against sot/channels.csv: run --write-io-table")
    for k in sorted(PENDING - pend):
        fail("PENDING", "%s no longer violates: delete it from PENDING" % k)
    tbd["_warn"] = set(warn)
    return bad, tbd, pend


# ------------------------------------------------------------------------------------------------ routes lint (R47)
RED_STROKE = re.compile(r'stroke\s*=\s*"(#e00000|#ff0000|#c00000|#d00000|red)"', re.I)
ROUTE_TAG = re.compile(r'<(polyline|path)\b([^>]*)>', re.I)
ATTR_NAME = re.compile(r'([A-Za-z_][\w:-]*)\s*=\s*"')
MARKER = re.compile(r'<circle\b[^>]*\bcx="([\d.]+)"[^>]*\bcy="([\d.]+)"[^>]*\br="([\d.]+)"[^>]*/>\s*<text\b[^>]*>\s*\d+\s*</text>', re.I)
FIG_CAPTION = re.compile(r'<figcaption>\s*Fig\.\s*\S+', re.I)
TOPVIEW_CAPTION = re.compile(r'<figcaption>\s*Top view', re.I)


def route_lint(path):
    text = open(path, encoding="utf-8").read()
    name = os.path.basename(path)
    bad = []
    for m in ROUTE_TAG.finditer(text):
        if RED_STROKE.search(m.group(2)) and not re.search(r'fill\s*=\s*"none"', m.group(2)):
            bad.append('%s: red <%s> missing fill="none"' % (name, m.group(1)))
    for m in re.finditer(r'<(polyline|path|circle|text)\b([^>]*)>', text, re.I):
        names = ATTR_NAME.findall(m.group(2))
        if sorted({n for n in names if names.count(n) > 1}):
            bad.append("%s: <%s> repeats an attribute" % (name, m.group(1)))
        if m.group(2).count('"') % 2:
            bad.append("%s: <%s> has an unterminated quoted attribute" % (name, m.group(1)))
    figs = [m.start() for m in FIG_CAPTION.finditer(text)]
    tops = [m.start() for m in TOPVIEW_CAPTION.finditer(text)]
    for i, pos in enumerate(figs):
        nxt = figs[i + 1] if i + 1 < len(figs) else len(text)
        if "connector sheet" in text[pos:text.find("</figcaption>", pos)].lower():
            continue
        if not any(pos < t < nxt for t in tops):
            bad.append("%s: figure at offset %d has no top view before the next figure" % (name, pos))
    for svg in re.findall(r'<svg.*?</svg>', text, re.I | re.S):
        mk = [(float(a), float(b), float(c)) for a, b, c in MARKER.findall(svg)]
        for i in range(len(mk)):
            for j in range(i + 1, len(mk)):
                if abs(mk[i][0] - mk[j][0]) < mk[i][2] + mk[j][2] and abs(mk[i][1] - mk[j][1]) < mk[i][2] + mk[j][2]:
                    bad.append("%s: marker labels overlap near (%.0f,%.0f)" % (name, mk[i][0], mk[i][1]))
        boxes = []
        for m in re.finditer(r'<text\b([^>]*)>([^<]*)</text>', svg, re.I):
            a, label = m.group(1), re.sub(r'&\w+;', 'x', m.group(2)).strip()
            if 'text-anchor' in a or len(label) < 4:
                continue
            xm, ym, fm = (re.search(r'\b%s="([\d.]+)"' % k, a) for k in ("x", "y", "font-size"))
            if xm and ym and fm:
                x, y, fs = float(xm.group(1)), float(ym.group(1)), float(fm.group(1))
                boxes.append((x, y - fs, x + len(label) * fs * 0.55, y + fs * 0.25, label))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                p, q = boxes[i], boxes[j]
                if p[0] < q[2] and q[0] < p[2] and p[1] < q[3] and q[1] < p[3]:
                    bad.append("%s: text labels overlap: %r and %r" % (name, p[4][:30], q[4][:30]))
    return bad


# ------------------------------------------------------------------------------------------------ IO table (X1)
BEGIN, END = "<!-- SOT:BEGIN", "<!-- SOT:END -->"
IO_GROUP = [("Trigger", "trigger"), ("Temp", "temp"), ("An Volt", "volt"), ("Knock", "knock"), ("DI", "di"), ("Inj", "inj"),
            ("Ign", "ign"), ("Aux", "aux"), ("CAN", "can"), ("Comms", "can"), ("RS232", "can")]
IO_CONN = [("ecu_a", "Connector A", "A"), ("ecu_b", "Connector B", "B"), ("ecu_com", "Comms port", "C")]


def io_colour(r):
    if r["class"] in ("spare", "nc", "N/A"):
        return "tbd"
    if r["class"] in ("ground", "screen") or r["channel"] == "Gnd Out":
        return "gnd"
    if r["class"] in ("power", "rail"):
        return "pwr"
    for pre, g in IO_GROUP:
        if r["channel"].startswith(pre):
            return g
    return "pwr"


def io_block(rs):
    out = [BEGIN + " generated by docs/harness/tools/check_wiring.py --write-io-table from sot/channels.csv - do not hand-edit -->",
           '<h2>Pin map — every ECU pin, straight from <code>sot/channels.csv</code></h2>',
           '<p class="note">Generated. Numeric order, not the physical connector face. Grey = spare or not connected.</p>']
    for conn, title, letter in IO_CONN:
        rr = sorted([r for r in rs if r["conn"] == conn], key=lambda r: int(re.sub(r"\D", "", r["pin"]) or 0))
        out.append(f'<h3 class="pmh">{html.escape(title)} <span class="note">({len(rr)} pins)</span></h3>')
        out.append('<div class="pm">')
        for r in rr:
            p = "%s%s" % (letter, re.sub(r"\D", "", r["pin"]))
            out.append(f'  <div class="pmc pm-{io_colour(r)}" title="{html.escape(r["label"])} · {html.escape(r["status"])}">'
                       f'<b>{p}</b><span class="pmch">{html.escape(r["channel"])}</span>'
                       f'<span class="pmlb">{html.escape(r["label"])}</span></div>')
        out.append("</div>")
    out.append(END)
    return "\n".join(out)


def io_table_texts(channels):
    with open(IO_TABLE, encoding="utf-8", newline="") as f:
        doc = f.read()
    eol = "\r\n" if "\r\n" in doc else "\n"
    block = io_block([r for r in channels if r["owner"] == "ECU"]).replace("\n", eol)
    if BEGIN in doc and END in doc:
        new = doc.replace(doc[doc.index(BEGIN):doc.index(END) + len(END)], block)
    else:
        new = doc
    return doc, new


# ------------------------------------------------------------------------------------------------ main
def load_all():
    head, rows = read_csv(MASTER)
    ch_head, channels = read_csv(CHANNELS)
    plan = json.load(open(PLAN, encoding="utf-8")) if os.path.exists(PLAN) else None
    lib = read_csv(PARTS)[1] if os.path.exists(PARTS) else None
    try:
        tracked = subprocess.run(["git", "ls-files", "docs/harness"], cwd=REPO, capture_output=True, text=True).stdout.split()
    except OSError:
        tracked = None
    return head, rows, ch_head, channels, plan, lib, tracked


def self_test():
    head, rows, ch_head, channels, plan, lib, tracked = load_all()
    import copy
    base, _, _ = check(rows, channels, head, ch_head, tracked, plan, lib, routes=False, io_table=False)
    cases = []

    def mutate(name, code, fn):
        rs = copy.deepcopy(rows)
        fn(rs)
        got, _, _ = check(rs, channels, head, ch_head, None, plan, lib, routes=False, io_table=False)
        new = [x for x in got if x not in base]
        cases.append((name, any(x.startswith(code) for x in new)))

    def first(rs, f):
        return next(r for r in rs if r["wire_id"] and f(r))
    mutate("a pin written as a sign", "F2", lambda rs: first(rs, lambda r: r["to_id"] == "DRB102-CABIN").update(to_pin="+"))
    mutate("a net on a plain wire", "F3", lambda rs: first(rs, lambda r: not r["net"]).update(net="5V"))
    mutate("two wires in one cavity", "F4", lambda rs: first(rs, lambda r: r["from_id"] == "ECU-A" and r["from_pin"] == "1").update(
        from_pin="2"))
    mutate("a dead ECU pin wired", "E1", lambda rs: first(rs, lambda r: r["from_id"] == "ECU-A" and r["from_pin"] == "1").update(
        from_pin="18") if False else first(rs, lambda r: r["to_id"] == "ECU-B" and r["to_pin"] == "28").update(to_pin="1"))
    mutate("the ECU ground to chassis", "E2", lambda rs: first(rs, lambda r: r["to_id"] == NEG_BAR and r["from_id"] == "SP-GND-ECU")
           .update(to_id="GND-IF", to_name="Ground point IF"))
    mutate("a relay coil driven on 86", "E4", lambda rs: first(rs, lambda r: r["from_id"] == "K-FAN" and r["from_pin"] == "85")
           .update(from_pin="86"))
    mutate("a screen landed on a device pin", "S2", lambda rs: first(rs, lambda r: r["from_type"] == "cable screen").update(
        to_type="connector", to_id="MAP", to_pin="1"))
    mutate("a bulkhead cavity wired on one side", "M1", lambda rs: first(rs, lambda r: r["from_id"] == "DRB102-ENGINE").update(
        from_pin="5"))
    mutate("12 AWG in a size-16 cavity", "M2", lambda rs: first(rs, lambda r: r["to_id"] == "DRB102-CABIN" and r["to_pin"] == "21")
           .update(gauge_awg="12"))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("%-5s %s" % ("ok" if ok else "FAIL", n))
    print("%d self-test failure(s)." % len(bad))
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    head, rows, ch_head, channels, plan, lib, tracked = load_all()
    if "--write-io-table" in argv:
        cur, new = io_table_texts(channels)
        if cur != new:
            with open(IO_TABLE, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            print("rewrote the pin map in XTREMEX-IO-TABLE.html")
        return 0
    bad, tbd, pend = check(rows, channels, head, ch_head, tracked, plan, lib)
    nw = sum(1 for r in rows if r["wire_id"])
    print("master: %d rows (%d wires, %d spare cavities) in %d harnesses" % (len(rows), nw, len(rows) - nw,
                                                                            len({r["harness"] for r in rows})))
    warn = sorted(tbd.pop("_warn", []))
    print("TBD cells (need a maker document, never guessed): " + ", ".join("%s %d" % (k, len(v)) for k, v in sorted(tbd.items())))
    for x in warn:
        print("WARN", x, "(an approved route drawing: Dan's to change, R47)")
    if "--tbd" in argv:
        for k, v in sorted(tbd.items()):
            print("  %s:" % k)
            for x in sorted(v):
                print("    " + x)
    for k in sorted(pend):
        print("pending (known, OPEN-ITEMS):", k)
    for x in bad:
        print("FAIL", x)
    print("check_wiring: %s" % ("FAIL (%d)" % len(bad) if bad else "OK"))
    return 1 if bad else 0


MAKER_CONTACTS = {'DRB12-102PAE-L018': {'contacts': ['0460-202-16141',
                                    '0460-202-1631',
                                    '0460-002-1631',
                                    '0460-247-16141',
                                    '0460-247-1631',
                                    '0460-264-16141',
                                    '0460-215-16141',
                                    '0460-215-1631',
                                    '1060-16-0122',
                                    '1060-16-0144',
                                    '1060-16-0622',
                                    '1060-16-0644',
                                    '1060-16-0688',
                                    '1060-16-0988',
                                    '1060-16-1222',
                                    '1060-14-0122',
                                    '1060-14-0144',
                                    '0460-204-12141',
                                    '0460-220-1231',
                                    '0460-256-12233',
                                    '1060-12-0144',
                                    '1060-12-0166',
                                    '1060-12-0222'],
                       'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, "
                                 'DRC, DT, HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey '
                                 "TechForum 'Common Contacts for TE ICT Deutsch Housings', "
                                 'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read '
                                 '2026-10-14); size group per housing = the size its cavities take; DRB = size 16 and size '
                                 '12 pins'},
 'DRB16-102SAE-L018': {'contacts': ['0462-201-16141',
                                    '0462-201-1631',
                                    '0462-004-1631',
                                    '0462-221-1631',
                                    '0462-209-16141',
                                    '0462-209-1631',
                                    '1062-16-0122',
                                    '1062-16-0144',
                                    '1062-16-0622',
                                    '1062-16-0644',
                                    '1062-16-0988',
                                    '1062-16-1222',
                                    '1062-16-1422',
                                    '1062-16-1444',
                                    '1062-14-0122',
                                    '1062-14-0144',
                                    '0462-203-12141',
                                    '0462-210-1231',
                                    '1062-12-0144',
                                    '1062-12-0166',
                                    '1062-12-0222'],
                       'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, "
                                 'DRC, DT, HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey '
                                 "TechForum 'Common Contacts for TE ICT Deutsch Housings', "
                                 'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read '
                                 '2026-10-14); size group per housing = the size its cavities take; DRB = size 16 and size '
                                 '12 sockets'},
 'DT04-2P': {'contacts': ['0460-202-16141',
                          '0460-202-1631',
                          '0460-002-1631',
                          '0460-247-16141',
                          '0460-247-1631',
                          '0460-264-16141',
                          '0460-215-16141',
                          '0460-215-1631',
                          '1060-16-0122',
                          '1060-16-0144',
                          '1060-16-0622',
                          '1060-16-0644',
                          '1060-16-0688',
                          '1060-16-0988',
                          '1060-16-1222',
                          '1060-14-0122',
                          '1060-14-0144'],
             'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, DT, "
                       "HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum 'Common "
                       "Contacts for TE ICT Deutsch Housings', "
                       'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); size '
                       'group per housing = the size its cavities take; DT = size 16 pins'},
 'DT04-6P': {'contacts': ['0460-202-16141',
                          '0460-202-1631',
                          '0460-002-1631',
                          '0460-247-16141',
                          '0460-247-1631',
                          '0460-264-16141',
                          '0460-215-16141',
                          '0460-215-1631',
                          '1060-16-0122',
                          '1060-16-0144',
                          '1060-16-0622',
                          '1060-16-0644',
                          '1060-16-0688',
                          '1060-16-0988',
                          '1060-16-1222',
                          '1060-14-0122',
                          '1060-14-0144'],
             'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, DT, "
                       "HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum 'Common "
                       "Contacts for TE ICT Deutsch Housings', "
                       'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); size '
                       'group per housing = the size its cavities take; DT = size 16 pins'},
 'DT06-12SA': {'contacts': ['0462-201-16141',
                            '0462-201-1631',
                            '0462-004-1631',
                            '0462-221-1631',
                            '0462-209-16141',
                            '0462-209-1631',
                            '1062-16-0122',
                            '1062-16-0144',
                            '1062-16-0622',
                            '1062-16-0644',
                            '1062-16-0988',
                            '1062-16-1222',
                            '1062-16-1422',
                            '1062-16-1444',
                            '1062-14-0122',
                            '1062-14-0144'],
               'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, DT, "
                         'HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum '
                         "'Common Contacts for TE ICT Deutsch Housings', "
                         'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); '
                         'size group per housing = the size its cavities take; DT = size 16 sockets'},
 'DT06-2S': {'contacts': ['0462-201-16141',
                          '0462-201-1631',
                          '0462-004-1631',
                          '0462-221-1631',
                          '0462-209-16141',
                          '0462-209-1631',
                          '1062-16-0122',
                          '1062-16-0144',
                          '1062-16-0622',
                          '1062-16-0644',
                          '1062-16-0988',
                          '1062-16-1222',
                          '1062-16-1422',
                          '1062-16-1444',
                          '1062-14-0122',
                          '1062-14-0144'],
             'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, DT, "
                       "HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum 'Common "
                       "Contacts for TE ICT Deutsch Housings', "
                       'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); size '
                       'group per housing = the size its cavities take; DT = size 16 sockets'},
 'DT06-3S': {'contacts': ['0462-201-16141',
                          '0462-201-1631',
                          '0462-004-1631',
                          '0462-221-1631',
                          '0462-209-16141',
                          '0462-209-1631',
                          '1062-16-0122',
                          '1062-16-0144',
                          '1062-16-0622',
                          '1062-16-0644',
                          '1062-16-0988',
                          '1062-16-1222',
                          '1062-16-1422',
                          '1062-16-1444',
                          '1062-14-0122',
                          '1062-14-0144'],
             'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, DT, "
                       "HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum 'Common "
                       "Contacts for TE ICT Deutsch Housings', "
                       'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); size '
                       'group per housing = the size its cavities take; DT = size 16 sockets'},
 'DT06-6S': {'contacts': ['0462-201-16141',
                          '0462-201-1631',
                          '0462-004-1631',
                          '0462-221-1631',
                          '0462-209-16141',
                          '0462-209-1631',
                          '1062-16-0122',
                          '1062-16-0144',
                          '1062-16-0622',
                          '1062-16-0644',
                          '1062-16-0988',
                          '1062-16-1222',
                          '1062-16-1422',
                          '1062-16-1444',
                          '1062-14-0122',
                          '1062-14-0144'],
             'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, DT, "
                       "HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum 'Common "
                       "Contacts for TE ICT Deutsch Housings', "
                       'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); size '
                       'group per housing = the size its cavities take; DT = size 16 sockets'},
 'DTM06-4S': {'contacts': ['0462-201-20141',
                           '0462-201-2031',
                           '0462-005-20141',
                           '0462-005-2031',
                           '1062-20-0122',
                           '1062-20-0144',
                           '1062-20-0222',
                           '1062-20-0244',
                           '1062-20-0322',
                           '1062-20-0344',
                           '1062-20-0377',
                           '1062-20-0622'],
              'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings (DigiKey TechForum 'Common Contacts "
                        "for TE ICT Deutsch Housings', "
                        'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-15; page '
                        'covers the DT series including DTM); DTM06-xS = size 20 cavities (TE DEUTSCH ICT Connector Product '
                        "Guide Nov 2022, p.4 'DTM Series Configurations' 'DTM0*-6* 6 size 20' and p.8 'Contacts for DT "
                        "Series' size 20 socket 0462-201-20**); size 20 sockets only"},
 'DTM06-6S': {'contacts': ['0462-201-20141',
                           '0462-201-2031',
                           '0462-005-20141',
                           '0462-005-2031',
                           '1062-20-0122',
                           '1062-20-0144',
                           '1062-20-0222',
                           '1062-20-0244',
                           '1062-20-0322',
                           '1062-20-0344',
                           '1062-20-0377',
                           '1062-20-0622'],
              'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings (DigiKey TechForum 'Common Contacts "
                        "for TE ICT Deutsch Housings', "
                        'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-15; page '
                        'covers the DT series including DTM); DTM06-xS = size 20 cavities (TE DEUTSCH ICT Connector Product '
                        "Guide Nov 2022, p.4 'DTM Series Configurations' 'DTM0*-6* 6 size 20' and p.8 'Contacts for DT "
                        "Series' size 20 socket 0462-201-20**); size 20 sockets only"},
 'HD36-24-33SE': {'contacts': ['0462-201-20141',
                               '0462-201-2031',
                               '0462-005-20141',
                               '0462-005-2031',
                               '1062-20-0122',
                               '1062-20-0144',
                               '1062-20-0222',
                               '1062-20-0244',
                               '1062-20-0322',
                               '1062-20-0344',
                               '1062-20-0377',
                               '1062-20-0622'],
                  'source': "TE Connectivity 'Common Contacts' set for ICT DEUTSCH housings, stated for the AEC, DRB, DRC, "
                            'DT, HD10, HD30 (incl. HD34 / HD36), HDP20 and STRIKE series (as published on DigiKey TechForum '
                            "'Common Contacts for TE ICT Deutsch Housings', "
                            'https://forum.digikey.com/t/common-contacts-for-te-ict-deutsch-housings/466, read 2026-10-14); '
                            'size group per housing = the size its cavities take; HD36-24-33 (HD30 series) = size 20 '
                            'sockets'},
 'V23132-A2001-B200': {'contacts': ['282110-1', '(ring lug, 8 AWG, M6)'],
                       'source': "TE datasheet V23132-X0000-A001 (HCR 150, rev 1403, _research/datasheets), 'Connector "
                                 "Information': coil side AMP SUPERSEAL 1.5 receptacle 282080-1, seal 281934-2, contact "
                                 '282110-1; load side cable lug M6 on M6 screw terminals, max cable 25 mm2'}}   # contact PNs each maker lists per housing PN, with the source

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
