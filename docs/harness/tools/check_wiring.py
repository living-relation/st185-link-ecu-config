#!/usr/bin/env python
"""The ONE wiring check (DECISIONS R221). Reads, never writes the SoT.

The wiring source of truth is ONE file, docs/harness/MASTER-wirelist.csv: one row per physical wire (or spare cavity), with
its harness, both ends and the wire. sot/channels.csv holds the ECU channel settings only. This script checks them:

  F1  the master is the only hand-edited wiring CSV under docs/harness, with exactly the master columns; the only other
      wiring CSV allowed is a generated wire list docs/harness/wirelists/ST185-<harness>-wirelist.csv (Dan B2 a; written
      and read back by build_drawings.py)
  F2  every connector end has an ID, a name, a housing PN, a pin, a pin source and a terminal PN (TBD allowed - listed);
      every splice / terminal / OEM end has an ID and a name; pins are numbers or letters (BUS2-1, 87a, IN3 ...), never a sign
  F3  nets = splices only: a wire has a net exactly when it lands on a splice or a bussed DT plug, and the net names it
  F4  one wire per cavity (studs and splices excepted; an INTEGRAL bridge of a bussed plug is no wire)
  I1  an INTEGRAL row (Dan N55 a, 2026-11-07: a bus bar's copper, the MRBF fuse block) has no length and no gauge and joins
      two splices; a bussed plug has no pin-to-pin bridge (Dan R6, 2026-11-08)
  B1  every used pin of a bussed plug (BUS-*) carries the same signal name (Dan R6, 2026-11-08: the plug is drawn mated to its
      bussed receptacle, no bridges); every real wire has a wire_label that says what it is for, never its wire id (Dan R2)
  B2  no wire ends on a bussed receptacle (DT04-xxPA-P021, a cap with its pins tied inside): wires land only on the bussed
      plug half DT06-xxSA (Dan 2026-11-09)
  B3  each half of a mated pair is named by its own part number (Dan A37, 2026-11-13): a bussed plug end (BUS-*) is named
      "<circuit> plug <its DT06 part> (<where>)", never "bus plug" or "bussed" (only the bussed receptacle is); the two
      bulkhead halves never share one name
  E1  every ECU pin a wire lands on is a live pin in sot/channels.csv, and every live ECU pin there has a wire
  E2  the far ends of each ECU power / ground / Gnd Out / sensor-supply / screen pin are of the class the Link G4X guide
      allows (R212); the ECU power grounds join only each other and one wire to the POWER box NEG bar (R216)
  E3  ground classes (R213): low-voltage electronics never end on a chassis ground (known cases: PENDING); a wire tagged
      factory ground (N83 a) with its 1993 EWD page may, on a body ground stud GND-*, unless it has CAN / ECU / sensor ties
  E4  an ECU output driving a relay lands on coil pin 85 (R219)
  S1  ECU-C 1 carries exactly one screen, the ECU CAN cable's own (R207; Dan 2026-11-08)
  S2  a cable screen floats at the device: its one end is a splice, a bussed plug, an ECU screen pin, a bulkhead / inline
      cavity or the VRC screen pin, never a device pin
  S3  every screen / drain reaches an ECU screen pin (A7, B17, C1), and no two of those pins meet
  M1  every DRB102 cavity and inline-pair cavity wired on one half is wired on the other
  M2  DRB102 contacts: size 16 cavities take 16-20 AWG, size 12 take 12-14 AWG, size 8 / 4 stay spare (TE drawing
      DRB12-102PXE-L018 rev C3); a contact the maker does not list for the housing fails (MAKER_CONTACTS)
  P1  a fuse-box end exists in the fuse-box design (cad/fusebox/rev8/wiring_plan.json, R204) with the same gauge; a POWER /
      LOGIC box ring terminal (T-PWR-* / T-LOG-*, "<bar or fuse>, <stud> stud", on a stud with several rings ending
      ", ring <n> of <m>", Dan N64 a, 2026-11-08) names a stud of the box design
      (cad/fusebox/src/spec.py REV7 neg_studs / pos_studs, AMI_ROWS, FEEDS): a 1/0 stud takes one 1/0 lug, the small GND stud
      up to 3 small rings, the + bar spare stud none, and every other bar stud is used
  D1  From / To direction (S8 a, DECISIONS B8): From is the end nearer the power or signal source - hubs, then the
      bulkhead / RADLOK / cowl plugs, then bus plugs and splices, then resistors and diodes, then devices (the per-harness
      wire lists are held to the same rule by build_drawings.py --check, T8 b)
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
PLAN = os.path.join(REPO, "cad", "fusebox", "rev8", "wiring_plan.json")
PARTS = os.path.join(REPO, "docs", "sourcing", "harness-parts.csv")   # maker, description (AWG range) per part
IO_TABLE = os.path.join(REPO, "XTREMEX-IO-TABLE.html")
ROUTES = os.path.join(HARNESS, "routes")

COLS = ["harness", "circuit", "wire_id", "passes_through",
        "from_type", "from_id", "from_name", "from_housing_pn", "from_housing_extra", "from_pin", "from_pin_doc", "from_terminal_pn",
        "from_desc", "from_note",
        "to_type", "to_id", "to_name", "to_housing_pn", "to_housing_extra", "to_pin", "to_pin_doc", "to_terminal_pn",
        "to_desc", "to_note",
        "net", "cable", "cable_pn", "wire_pn", "gauge_awg", "colour",
        "oem_location", "oem_wire_colour", "oem_ewd_page", "oem_method", "route_branch", "est_length_mm", "notes", "wire_label"]
CHANNEL_COLS = ["owner", "channel", "conn", "pin", "label", "class", "dir", "type", "pullup", "status", "source", "notes"]
PIN_RE = re.compile(r"[A-Za-z0-9]+([ -][A-Za-z0-9]+)*")
ECU = {"ECU-A": "ecu_a", "ECU-B": "ecu_b", "ECU-C": "ecu_com"}
SCREEN_PINS = {("ECU-A", "7"), ("ECU-B", "17"), ("ECU-C", "1")}
GROUND_PINS = {("ECU-A", "25"), ("ECU-A", "34"), ("ECU-B", "25"), ("ECU-B", "34")}
NEG_BAR = re.compile(r"^T-PWR-NEG-")      # the ring terminals on the POWER box battery-negative bar (Dan N64 a)
BOX_RING = re.compile(r"^T-(PWR|LOG)-")     # a ring terminal on a POWER / LOGIC box stud (Dan N64 a, 2026-11-07)
SPEC_DIR = os.path.join(REPO, "cad", "fusebox", "src")   # the frozen box design: read only
# mated pairs: the two halves of one connector (cavity n mates cavity n)
MATES = {"DRB102-CABIN": "DRB102-ENGINE"}  # wheel speed inline pairs (Dan J1 a) and the fuel level inline pair (Dan N1 a) dropped, 2026-11-08
MATES.update({v: k for k, v in list(MATES.items())})
# inside the VRC boxes the input screen pin is wired to the output screen pin (DECISIONS R31)
INTERNAL = [(("VRC-F-IN", "3"), ("VRC-F-OUT", "5")), (("VRC-R-IN", "3"), ("VRC-R-OUT", "5"))]  # OUT screen = pin 5 (CAD BOM, Dan G2 a 2026-11-08)
DRB_SIZE = {n: 16 for n in range(1, 103)}
DRB_SIZE.update({n: 12 for n in list(range(1, 9)) + list(range(95, 103))})
DRB_SIZE.update({48: 8, 49: 8, 54: 8, 55: 8, 43: 4, 60: 4})
DRB_RANGE = {16: (16, 20), 12: (12, 14)}
# fuse-box ends: master ID -> the id the fuse-box design uses
FB_IDS = {"LOGIC": "fb_logic", "POWER": "fb_power", "BATT-RELAY-BLOCK": "fb_batt"}
FB_PIN = {"BATT": "BATT +", "FP": "FP 40A"}
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
# E3:w_at_gnd_a1 is permanent, not pending: the alarm ground lead (node AL-GND to ring terminal T-AT-GND) is the named B10
# exception (DECISIONS "Grounds (B10)", Dan N43 b); the accessory grounds went with the accessories (alarm-ready tap points,
# Dan 2026-11-06). Factory-load grounds are not listed here: they carry the FACTORY_GND tag in the master note (DECISIONS
# "Grounds (B10)", Dan N83 a). The A/C amp coolant-OK ground w_ac_cool_gnd on ground point IG is the named N103 exception
# (Dan 2026-11-08); E3 passes it (no low-voltage electronics text on its ends).
PENDING = {"E3:w_at_gnd_a1"}
# A factory load, or a part that replaces one, keeps that load's factory ground point (Dan N83 a): the master note carries
# the tag and the 1993 EWD page; E3 accepts it on a body ground stud, never with CAN / ECU / sensor ties.
FACTORY_GND = re.compile(r"factory ground \(N83 a\)", re.I)
FACTORY_PAGE = re.compile(r"\b1993 EWD p\.\s?\d+", re.I)
BODY_GND = re.compile(r"^GND-")
TIED = re.compile(r"\bCAN\b|CAN[- ]?LAMBDA|\bECU\b|sensor|RealDash|\bPi\b|CSB3|opto|cruise|buck converter", re.I)
STUD_IDS = re.compile(r"^(KILL-SW|RADLOK-|JUMP-POST|BATT-RELAY-BLOCK)")   # studs: several lugs on one is normal
sys.path.insert(0, HERE)
from build_drawings import s8_rank          # noqa: E402  the From / To order (S8 a): one definition
from build_drawings import is_integral      # noqa: E402  (Dan N55 a): part of a bought part, not a wire; one definition


def box_studs():
    """{(signal, stud): kind} from the frozen box design (cad/fusebox/src/spec.py), kind '1/0', 'small', 'spare', 'fuse' or
    'feed'; None when the design is not on disk."""
    if not os.path.exists(os.path.join(SPEC_DIR, "spec.py")):
        return None
    sys.path.insert(0, SPEC_DIR)
    try:
        import spec as S
    finally:
        sys.path.remove(SPEC_DIR)
    out = {}
    for _x, nm, _h, g in S.REV7["neg_studs"]:
        out[("POWER box NEG bar", nm)] = g
    for _y, nm, h in S.REV7["pos_studs"]:
        out[("POWER box + bar", nm)] = "1/0" if h else "spare"
    for row, fuses in S.AMI_ROWS.items():
        for n, (nm, _a) in enumerate(fuses[:S.AMI_SLOTS[row]], 1):
            if nm != "SP":
                out[("POWER box AMI %s-%d fuse" % (row, n), "output")] = "fuse"
    for bus in S.FEEDS:
        out[("LOGIC box Bus %s" % bus[-1], "feed")] = "feed"
    return out


RING_NAME = re.compile(r"^(.+), (.+) stud(?:, ring \d+ of \d+)?$")   # "..., GND stud, ring 1 of 3" (2026-11-08)


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


# the generated per-harness wire lists (build_drawings.py writes and --check reads them back; F1, Dan B2 a)
WIRELIST_CSV = re.compile(r"docs/harness/wirelists/ST185-[A-Za-z0-9-]+-wirelist\.csv")


def check(rows, channels, head=None, ch_head=None, tracked=None, plan=None, lib=None, routes=True, io_table=True, studs=None):
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
            if f.endswith(".csv") and os.path.basename(f) != "MASTER-wirelist.csv" and not WIRELIST_CSV.fullmatch(f):
                fail("F1", "%s: the only hand-edited wiring CSV is the master (N60); the one other kind is a generated "
                     "docs/harness/wirelists/ST185-<harness>-wirelist.csv (Dan B2 a)" % f)
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
                if r["wire_id"] and not is_integral(r):
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
    # ---- I1 INTEGRAL rows (Dan N55 a, 2026-11-07) / B1 bussed plugs: one signal name, no bridges; wire labels (Dan R2 / R6, 2026-11-08)
    for r in wires:
        if not is_integral(r):
            continue
        ft, tt, fi, ti = r["from_type"], r["to_type"], r["from_id"], r["to_id"]
        if r["est_length_mm"] or r["gauge_awg"] or r["cable"]:
            fail("I1", "%s is INTEGRAL: it has no length, gauge or cable (Dan N55 a)" % r["wire_id"])
        if ft == tt == "splice" and fi != ti:
            continue
        fail("I1", "%s is INTEGRAL but joins %s %s to %s %s: only two splices (a bussed plug has no pin-to-pin bridge, Dan R6)" % (
            r["wire_id"], fi, r["from_pin"], ti, r["to_pin"]))
    for bus in sorted({r[s + "_id"] for r in wires for s in ("from", "to") if r[s + "_id"].startswith("BUS-")}):
        sigs = sorted({r[s + "_desc"] for r in wires for s in ("from", "to") if r[s + "_id"] == bus})
        if len(sigs) != 1:
            fail("B1", "%s: every used pin of a bussed plug carries the same signal name (Dan R6), found %s" % (bus, sigs))
    # B2 (Dan 2026-11-09): a bussed receptacle (DT04-12PA-P021 / DT04-08PA-P021) is a cap with its pins tied inside: wires land
    # only on the plug half (DT06-12SA / DT06-08SA); no wire ends on the receptacle
    for r in wires:
        for s in ("from", "to"):
            eid, hp = r[s + "_id"], (r[s + "_housing_pn"] or "")
            if eid.upper().endswith("RCPT") or re.match(r"DT04-\d+PA-P021", hp) or (
                    eid.startswith("BUS-") and not re.match(r"DT06-\d+SA", hp)):
                fail("B2", "%s %s end on %s (%s): wires land only on the bussed plug half DT06-xxSA, never on the bussed "
                     "receptacle (Dan 2026-11-09)" % (r["wire_id"], s, eid, hp))
    # B3 (Dan A37, 2026-11-13): each half of a mated pair is named by its own part number; only the bussed half (the DT04-xxPA-P021
    # receptacle, drawn by build_drawings.relabel) is called bussed, so the plug half's name says "plug <its DT06 part>" and never
    # "bus plug" or "bussed"; two mated master ends (the RADLOK pairs) never share one name
    for r in wires:
        for s in ("from", "to"):
            eid, nm, hp = r[s + "_id"], r[s + "_name"] or "", r[s + "_housing_pn"] or ""
            if eid.startswith("BUS-") and ("plug %s" % hp not in nm or re.search(r"\bbus(sed)?\b", nm, re.I)):
                fail("B3", "%s %s end %s is named %r: a bussed pair's plug half is named by its own part number, "
                     "'<circuit> plug %s (<where>)', never 'bus plug' or 'bussed' (Dan A37)" % (r["wire_id"], s, eid, nm, hp))
    end_name = {r[s + "_id"]: r[s + "_name"] for r in wires for s in ("from", "to") if r[s + "_id"]}
    for a, b in MATES.items():
        if a < b and a in end_name and end_name.get(a) == end_name.get(b):
            fail("B3", "mated halves %s and %s share the name %r (Dan A37)" % (a, b, end_name[a]))
    for r in wires:
        if (r["wire_pn"] or "").startswith("none"):
            continue      # a removal row is no wire to label
        lb = (r.get("wire_label") or "").strip()
        if not lb or lb == r["wire_id"] or re.search(r"\b(w|wc|cab|br)_[a-z0-9_]+\b", lb):
            fail("B1", "%s: wire_label %r must say what the wire is for, never its wire id (Dan R2)" % (r["wire_id"], lb))
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
                    if not ((xid, xpin) in GROUND_PINS or NEG_BAR.match(xid)):
                        fail("E2", "ECU ground %s %s reaches %s %s (%s): the ECU grounds join only each other and the NEG bar (R216)"
                             % (eid, pin, xid, xpin, x[xs + "_desc"]))
                elif kind == "screen":
                    if (xid, xpin) not in SCREEN_PINS and not QSG_ENDS["screen"].search(text) and not xid.startswith("VRC-"):
                        fail("E2", "screen pin %s %s reaches %s %s (%s): drains only (R212)" % (eid, pin, xid, xpin, x[xs + "_desc"]))
                elif xt != "resistor" and not QSG_ENDS[kind].search(text):
                    fail("E2", "%s %s (%s) reaches %s %s (%s) (R212)" % (eid, pin, c["channel"], xid, xpin, x[xs + "_desc"]))
    STUDS = re.compile(r"^(BATT-RELAY-BLOCK|KILL-SW|RADLOK|JUMP-POST|SP-JUMP-|T-PWR-|T-LOG-)")
    for r in wires:
        tag = FACTORY_GND.search(r["notes"])
        if tag and not any(r[s + "_type"] == "terminal" and BODY_GND.match(r[s + "_id"]) for s in ("from", "to")):
            fail("E3", "%s is tagged factory ground but ends on no body ground stud GND-* (N83 a)" % r["wire_id"], key=r["wire_id"])
        if tag and not FACTORY_PAGE.search(r["notes"]):
            fail("E3", "%s is tagged factory ground without its 1993 EWD page (N83 a)" % r["wire_id"], key=r["wire_id"])
        for s, o in ends(r):
            if r[s + "_type"] == "terminal" and CHASSIS.search(r[s + "_id"] + " " + r[s + "_name"]):
                if STUDS.search(r[o + "_id"]):
                    continue        # a bar / stud bonded to chassis is not a device ground
                if r[o + "_type"] == "splice":
                    near = [(x, xs) for x, xs in node_ends(g.find(g.key(r, o)))]
                else:
                    near = [(r, o)]
                text = " ".join("%s %s %s" % (x[xs + "_id"], x[xs + "_name"], x[xs + "_desc"]) for x, xs in near)
                if tag and BODY_GND.match(r[s + "_id"]):
                    if TIED.search(text):
                        fail("E3", "%s is tagged factory ground but has CAN / ECU / sensor ties: battery-negative bus only (N83 a)"
                             % r["wire_id"], key=r["wire_id"])
                    continue        # a factory-load ground on its factory point (DECISIONS "Grounds (B10)", Dan N83 a)
                if ELECTRONICS.search(text):
                    fail("E3", "%s ends on chassis ground %s with low-voltage electronics on it: battery-negative bus only (R213)"
                         % (r["wire_id"], r[s + "_id"]), key=r["wire_id"])
    # ---- S1 / S2 / S3
    c1 = [r for r in wires if any(r[s + "_id"] == "ECU-C" and r[s + "_pin"] == "1" for s in ("from", "to"))]
    if len(c1) != 1 or (c1 and c1[0]["cable"] and c1[0]["colour"] != "Shield"):
        fail("S1", "ECU-C 1 must carry exactly one screen: the ECU CAN cable's own screen (Dan 2026-11-08), has %s"
             % [x["wire_id"] for x in c1])
    for r in wires:
        for s, o in ends(r):
            if r[s + "_type"] == "cable screen":
                ot, oid = r[o + "_type"], r[o + "_id"]
                ok = ot == "splice" or (oid, r[o + "_pin"]) in SCREEN_PINS or oid in MATES or oid.startswith("VRC-") or \
                    oid.startswith("BUS-")   # a bussed plug joins its pins like a splice (the shield bus plug, Dan N104 a)
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
            if r["wire_id"] and r[s + "_type"] == "connector" and not is_integral(r):   # a cap bridge has no contact (I1)
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
                ring = RING_NAME.match(r[s + "_name"]) if r[s + "_type"] == "terminal" and BOX_RING.match(eid) else None
                if ring:     # a box ring terminal -> the design's end: the bar studs are pdb BAT+ / ALT/STR / GND (Dan N64 a)
                    sig, stud = ring.groups()
                    m = re.match(r"POWER box AMI (IN|OUT)-(\d+) fuse$|LOGIC box Bus ([12])$", sig)
                    if sig == "POWER box NEG bar":
                        old, pin = "pdb", "GND"
                    elif sig == "POWER box + bar":
                        old, pin = "pdb", {"BAT+ IN": "BAT+", "RADLOK+": "ALT/STR"}.get(stud, stud)
                    elif m and m.group(1):
                        old, pin = "fb_power", "AMI %s-%s" % (m.group(1), m.group(2))
                    elif m:
                        old, pin = "fb_logic", "BUS" + m.group(3)
                    else:
                        fail("P1", "%s: %s names no POWER / LOGIC box bar or fuse (Dan N64 a)" % (r["wire_id"], r[s + "_name"]))
                        continue
                    if pin == "GND" and stud == "GND":
                        continue    # the small GND stud: the box design lists the old relay grounds (frozen spares, B27), not these
                else:
                    old = FB_IDS.get(eid) or (eid.lower().replace("-", "_") if eid.startswith("K-") else None)
                    if not old or r[s + "_type"] != "connector":
                        continue
                    pin = FB_PIN.get(r[s + "_pin"], r[s + "_pin"]) if eid == "BATT-RELAY-BLOCK" else r[s + "_pin"]
                ws = plan_end.get((old, pin))
                if not ws and old in ("fb_logic", "fb_power", "fb_batt", "pdb"):
                    fail("P1", "%s: fuse-box design has no wire at %s %s (R204)" % (r["wire_id"], eid, r[s + "_pin"]))
                elif ws and r["gauge_awg"] and r["gauge_awg"] not in {PLAN_GAUGE.get(str(w.get("gauge")), str(w.get("gauge"))) for w in ws}:
                    fail("P1", "%s: %s %s is %s AWG in the fuse-box design, %s AWG in the master (R204)" % (
                        r["wire_id"], eid, r[s + "_pin"], "/".join(sorted({PLAN_GAUGE.get(str(w.get("gauge")), str(w.get("gauge"))) for w in ws})), r["gauge_awg"]))
    # ---- P1 box ring terminals against the box design's studs (cad/fusebox/src/spec.py; Dan N64 a / N65 a, N60 a)
    if studs:
        on = collections.defaultdict(list)
        for r in wires:
            for s in ("from", "to"):
                eid = r[s + "_id"]
                if r[s + "_type"] != "terminal" or not BOX_RING.match(eid):
                    continue
                m = RING_NAME.match(r[s + "_name"])
                key = m.groups() if m else None
                if key not in studs:
                    fail("P1", "%s: ring %s %r is no stud of the box design (spec.py REV7 / AMI_ROWS / FEEDS; Dan N64 a)"
                         % (r["wire_id"], eid, r[s + "_name"]))
                    continue
                on[key].append((r, s))
        rid = collections.Counter(r[s + "_id"] for v in on.values() for r, s in v)
        for t, n in rid.items():
            if n > 1:
                fail("P1", "ring terminal %s takes %d wires: one ring per wire (Dan N65 a)" % (t, n))
        for key, kind in sorted(studs.items()):
            got = on.get(key, [])
            want = {"1/0": (1, 1), "small": (1, 3), "spare": (0, 0)}.get(kind, (0, 1))
            if not want[0] <= len(got) <= want[1]:
                fail("P1", "%s, %s stud carries %d ring(s); the box design takes %s (spec.py; Dan N60 a)" % (
                    key[0], key[1], len(got), "%d-%d" % want if want[0] != want[1] else str(want[0])))
            for r, s in got:
                if kind == "1/0" and r["gauge_awg"] != "1/0":
                    fail("P1", "%s: %s AWG on the 1/0 stud %s, %s" % (r["wire_id"], r["gauge_awg"], *key))
                if kind == "small" and r["gauge_awg"] == "1/0":
                    fail("P1", "%s: a 1/0 cable on the small GND stud" % r["wire_id"])
    # ---- D1 the From / To rule (S8 a, Dan 2026-11-10): one definition, build_drawings.s8_rank
    for r in wires:
        a, b = s8_rank(r["from_type"], r["from_id"]), s8_rank(r["to_type"], r["to_id"])
        if a > b:
            fail("D1", "%s runs %s -> %s: From is the end nearer the power or signal source, To the device end (S8 a): "
                 "swap every from_* / to_* column of the row" % (r["wire_id"], r["from_id"], r["to_id"]), r["wire_id"])
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
    return head, rows, ch_head, channels, plan, lib, tracked, box_studs()


def self_test():
    head, rows, ch_head, channels, plan, lib, tracked, studs = load_all()
    import copy
    base, _, _ = check(rows, channels, head, ch_head, tracked, plan, lib, routes=False, io_table=False, studs=studs)
    cases = []

    def mutate(name, code, fn):
        rs = copy.deepcopy(rows)
        fn(rs)
        got, _, _ = check(rs, channels, head, ch_head, None, plan, lib, routes=False, io_table=False, studs=studs)
        new = [x for x in got if x not in base]
        cases.append((name, any(x.startswith(code) for x in new)))

    def first(rs, f):
        return next(r for r in rs if r["wire_id"] and f(r))

    def at_end(rs, ident, at_pin=None, **upd):
        """change the end of the first wire that lands on `ident` (and `pin`), whichever side it is (S8 a, 2026-11-10:
        From / To follow the source rule, so a test never assumes a side); keys in `upd` are written without the side prefix"""
        for r in rs:
            for sd in ("from", "to"):
                if r["wire_id"] and r[sd + "_id"] == ident and (at_pin is None or r[sd + "_pin"] == at_pin):
                    r.update({sd + "_" + k: v for k, v in upd.items()})
                    return r
        raise StopIteration(ident)
    mutate("a pin written as a sign", "F2", lambda rs: at_end(rs, "DRB102-CABIN", pin="+"))
    mutate("a net on a plain wire", "F3", lambda rs: first(rs, lambda r: not r["net"]).update(net="5V"))
    mutate("two wires in one cavity", "F4", lambda rs: at_end(rs, "ECU-A", "1", pin="2"))
    mutate("a dead ECU pin wired", "E1", lambda rs: at_end(rs, "ECU-B", "28", pin="1"))
    def ecu_gnd(rs):
        r = first(rs, lambda r: {r["from_id"], r["to_id"]} & {"SP-GND-ECU"} and (NEG_BAR.match(r["to_id"]) or NEG_BAR.match(r["from_id"])))
        sd = "to" if NEG_BAR.match(r["to_id"]) else "from"
        r.update({sd + "_id": "GND-IF", sd + "_name": "Ground point IF"})
    mutate("the ECU ground to chassis", "E2", ecu_gnd)
    mutate("an INTEGRAL link with a length", "I1", lambda rs: first(rs, lambda r: is_integral(r) and "splice" in (r["from_type"], r["to_type"]))
           .update(est_length_mm="200"))
    mutate("a bussed plug pin with its own signal name", "B1", lambda rs: at_end(rs, "BUS-SW12", desc="Fuel pump relay coil +"))
    mutate("a wire labelled with its wire id", "B1", lambda rs: first(rs, lambda r: r["wire_id"] == "w67").update(wire_label="w67"))
    mutate("a wire on the bussed receptacle", "B2", lambda rs: at_end(rs, "BUS-SW12", housing_pn="DT04-12PA-P021"))
    mutate("a bussed pair's plug half called a bus plug", "B3", lambda rs: at_end(rs, "BUS-SW12", name="Switched +12 V bus plug (glove box)"))
    mutate("a bussed pair's plug half named without its part number", "B3", lambda rs: at_end(rs, "BUS-5V-2", name="+5 V sensor supply plug (ECU splice point)"))
    mutate("both bulkhead halves with one name", "B3", lambda rs: [r.update({sd + "_name": "Firewall bulkhead connector"})
           for r in rs for sd in ("from", "to") if r[sd + "_id"] in ("DRB102-CABIN", "DRB102-ENGINE")])
    mutate("a pin-to-pin bridge on a bussed plug", "I1", lambda rs: rs.append(dict(first(rs, lambda r: r["wire_id"] == "w67"),
           wire_id="br_x", wire_pn="INTEGRAL", gauge_awg="", est_length_mm="", from_id="BUS-5V", from_type="connector", from_pin="1",
           to_id="BUS-5V", to_type="connector", to_pin="2")))
    mutate("a ring on a stud the box design does not have", "P1", lambda rs: at_end(rs, "T-PWR-NEG-BAT", name="POWER box NEG bar, BAT2 stud"))
    mutate("two lugs on one 1/0 stud", "P1", lambda rs: at_end(rs, "T-PWR-NEG-ID", name="POWER box NEG bar, GND IG stud", id="T-PWR-NEG-IG2"))
    mutate("a fourth ring on the small GND stud", "P1", lambda rs: [first(rs, lambda r, w=w: r["wire_id"] == w)
           .update(to_type="terminal", to_id="T-PWR-NEG-GND-%d" % n, to_name="POWER box NEG bar, GND stud", net="")
           for n, w in ((4, "w_flex_ret_c"), (5, "w_lamg_ac"))])  # 2 + 2 rings since the K-ON ground left with the box insides (R1 a); w_can_gnd gone (T1 a)
    mutate("a relay coil driven on 86", "E4", lambda rs: at_end(rs, "K-FAN", "85", pin="86"))
    def screen_on_pin(rs):
        r = first(rs, lambda r: "cable screen" in (r["from_type"], r["to_type"]))
        sd = "to" if r["from_type"] == "cable screen" else "from"
        r.update({sd + "_type": "connector", sd + "_id": "MAP", sd + "_pin": "1"})
    mutate("a screen landed on a device pin", "S2", screen_on_pin)
    mutate("a bulkhead cavity wired on one side", "M1", lambda rs: at_end(rs, "DRB102-ENGINE", pin="5"))
    mutate("an LED ground on chassis without the factory-ground tag", "E3", lambda rs: first(
        rs, lambda r: r["wire_id"] == "w_led_gnd_c13").update(to_type="terminal", to_id="GND-ID",
                                                                to_name="Ground stud ID, LH kick panel", notes=""))
    mutate("the factory-ground tag on CAN / ECU / sensor ties", "E3", lambda rs: first(
        rs, lambda r: r["wire_id"] == "w_fan_gnd").update(to_desc="CAN-Lambda sensor ground"))
    mutate("the factory-ground tag without a 1993 EWD page", "E3", lambda rs: first(
        rs, lambda r: r["wire_id"] == "w_fan_gnd").update(notes="factory ground (N83 a): radiator fan to EA"))
    mutate("the factory-ground tag off a body ground stud", "E3", lambda rs: first(
        rs, lambda r: r["wire_id"] == "w_f5_gnd").update(from_id="T-ENG-BLOCK-3", from_name="Engine block ground stud, lug 3"))
    def turn_round(rs):
        r = first(rs, lambda r: r["from_id"].startswith("ECU-") and r["to_id"] == "DRB102-CABIN")
        r.update({k: r[("to_" if k.startswith("from_") else "from_") + k.split("_", 1)[1]] for k in list(r)
                  if k.startswith(("from_", "to_"))})
    mutate("a wire written device end first (bulkhead -> ECU plug)", "D1", turn_round)
    mutate("12 AWG in a size-16 cavity", "M2", lambda rs: at_end(rs, "DRB102-CABIN", "21").update(gauge_awg="12"))
    for name, extra, want in (("a stray wiring CSV under docs/harness", "docs/harness/extra-wires.csv", True),
                              ("a CSV in wirelists/ not named like a wire list", "docs/harness/wirelists/notes.csv", True),
                              ("a generated wire list CSV (allowed)", "docs/harness/wirelists/ST185-Test-wirelist.csv", False)):
        got, _, _ = check(rows, channels, head, ch_head, list(tracked or []) + [extra], plan, lib, routes=False, io_table=False,
                          studs=studs)
        new = [x for x in got if x not in base]
        cases.append((name, any(x.startswith("F1") for x in new) == want))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("%-5s %s" % ("ok" if ok else "FAIL", n))
    print("%d self-test failure(s)." % len(bad))
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    head, rows, ch_head, channels, plan, lib, tracked, studs = load_all()
    if "--write-io-table" in argv:
        cur, new = io_table_texts(channels)
        if cur != new:
            with open(IO_TABLE, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            print("rewrote the pin map in XTREMEX-IO-TABLE.html")
        return 0
    bad, tbd, pend = check(rows, channels, head, ch_head, tracked, plan, lib, studs=studs)
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


MAKER_CONTACTS = {'AT06-2S-RD01': {'contacts': ['AT62-201-16141',
                               'AT62-201-1631',
                               'AT62-209-16141',
                               'AT62-209-1631',
                               'AT62-201-16141-22',
                               'AT62-201-1631-22',
                               'AT62-201-16NKIT'],
                  'source': "Amphenol Sine Systems drawing AT06-2S-RD01 rev A5 (contact size 16, 14-20 AWG, AW2S "
                            "wedge; https://www.farnell.com/cad/3324071.pdf) and Amphenol 'Machined and Stamped & "
                            "Formed Contacts for use with A Series Products' (updated 08-2023; machined size 16 "
                            "sockets; https://onlinecomponents.com/upload/globalresourcefiles/a-series-contacts.pdf, "
                            "read 2026-11-03)"},
 'DRB12-102PAE-L018': {'contacts': ['0460-202-16141',
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
