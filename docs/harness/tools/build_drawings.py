#!/usr/bin/env python
"""The harness layout trees and per-harness wire lists, from the ONE master wire list (DECISIONS B5 / B6).

Harnesses are BUILT in harness.design (Dan 2026-11-01); this script makes no drawings. The layout and schematic PDFs it
used to write are retired (git history keeps them). What it still does, for the master and the other scripts:

  1. LAYOUT TREE  `tools/<set>.layout.json` (nodes, xy, segments, place / place_oem) plus `route_trees` built from the
                  approved route data (Routes 16 / 17; B8): every wire end is placed and every wire is routed. The tree
                  is the ONLY length source (Dan N69 a): for each harness in PLACED the master `est_length_mm` is the
                  tree length, written by --write-lengths, never by hand, and --check fails on any difference; a
                  harness not in PLACED keeps its estimate. An INTEGRAL row (`is_integral`: a bus bar's copper, the
                  MRBF fuse block; Dan N55 a) and a through-connector pair (`is_connector_pass`, the
                  RADLOK pairs) have both ends placed but no length. harness.design generators import `Harness` /
                  `route()` from here for the same tree.
  2. WIRE LISTS   the per-harness wire lists in docs/harness/wirelists/ (Option A, DECISIONS "Wire lists"): an .xlsx and
                  a .csv (the Wires sheet, master ids and names) per harness, removal rows skipped (`is_removal`); both
                  are read back by --check. The CSV is the only wiring CSV besides the master (check_wiring F1, Dan B2 a).
  3. DRB102 MAP   docs/harness/drawings/DRB102-bulkhead-map.png (insert face, from the master); build_pin_chart.py reads
                  DRB_COLS / DRB_SIZE.
  Also: `od()` / `dr25_for()` give the DR-25 size per segment for docs/sourcing/build_project_bom.py.

    python docs/harness/tools/build_drawings.py [set]          write the wire lists and the DRB102 map
    python docs/harness/tools/build_drawings.py --check [set]  fail if a wire end is not on the tree, a PLACED harness's
                                                              master length differs from its tree length, or a wire
                                                              list / the DRB102 map is stale
    python docs/harness/tools/build_drawings.py --lengths [harness ...]        the before -> after list (default PLACED;
                                                              any harness, for its lengths step); writes nothing
    python docs/harness/tools/build_drawings.py --write-lengths [harness ...]  write it into the master (PLACED only, after
                                                              Dan OKs the list, L2 a), then rewrite the wire lists
    python docs/harness/tools/build_drawings.py --self-test    prove the length check fails on a broken copy (CI)
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


def is_removal(r):
    """A removal row: a factory wire taken OUT of the car, back to its last live point (B5 "no row, no cut"; README
    "What stays and what goes"). Marked by `oem_method` "remove ..." and `wire_pn` "none (removed)", no gauge or length.
    check_wiring.py audits it; no generator builds, routes, sizes or buys it."""
    return (r.get("oem_method") or "").strip().lower().startswith("remove") or \
        (r.get("wire_pn") or "").startswith("none (removed)")


def is_integral(r):
    """An INTEGRAL row (Dan N55 a, 2026-11-07): a link that is part of a bought part, not a wire to cut - a bus bar's copper
    between two stud splices, the MRBF fuse block between bar stud 3 and its output stud (a bussed plug has no bridge since
    Dan R6, 2026-11-08). `wire_pn` INTEGRAL: no length, no route, no BOM or cut-list line, no length check."""
    return (r.get("wire_pn") or "") == "INTEGRAL"


# a fuse-box end (Dan N64 a, 2026-11-07): one ring terminal per wire on a POWER / LOGIC box stud, named "<bar or fuse>, <stud> stud"
BOX_RING = re.compile(r"^T-(PWR|LOG)-")
# a stud of a bought bar drawn as a splice (the engine-bay jump bar 2104 studs and the MRBF fuse block 5191 output stud, Dan
# 2026-11-07): each wire end on it is its own lug (its terminal_pn), and its neighbours join through INTEGRAL links
STUD_SPLICE = re.compile(r"^SP-(JUMP-\d|ALT-FUSE)$")


def ring_signal(r, s):
    """The global signal of a fuse-box ring terminal: the part of its master name before ", " ("POWER box NEG bar", "POWER box
    + bar", "LOGIC box Bus 1", "POWER box AMI OUT-3 fuse"); every stud on one bar shares it, so harness.design reads them as one
    net (Dan N64 a). None for any other end."""
    if r[s + "_type"] != "terminal" or not BOX_RING.match(r[s + "_id"]):
        return None
    return r[s + "_name"].split(", ")[0]


# Which master ids belong to which fuse box (box ring terminals, the LOGIC fuse slots, the box relays). Since Dan R1 a
# (2026-11-09) the harness files draw no box groups (box_groups); relabel uses this only to name a relay's box.
# (old group id, name, old group part, member test)
BOX_GROUPS = (
    ("gFB100P", "POWER box (ST185-FB-100P)", "gp_fb_100p",
     lambda i: i.startswith("T-PWR-") or i in ("K-EFI", "K-FAN", "K-FAN2")),
    ("gFB100L", "LOGIC box (ST185-FB-100L)", "gp_fb_100l",
     lambda i: i == "LOGIC" or i.startswith("T-LOG-") or i in ("K-HL", "K-HR", "K-HORN", "K-ETB", "K-ACC", "K-EPS-EN", "K-ON", "K-DRL", "K-POD")),
)
# box_groups' old `outside` argument (Dan N80 a); no groups since R1 a, kept so the callers stay unchanged
BOX_GROUP_OUTSIDE = {"AB-cabin 2": ("K-ACC",)}


def _seat_map():
    """sot/fuse-relay-map.csv: box relay master id -> (box name, seat); the LOGIC fuse outputs by their slot."""
    rows = list(csv.DictReader(open(os.path.join(os.path.dirname(MASTER), "..", "..", "sot", "fuse-relay-map.csv"), encoding="utf-8")))
    box = {"B1": "POWER box", "B2": "LOGIC box", "B3": "Trunk relay block"}   # B3: Dan S1 a 2026-11-09
    return {r["master_id"]: (box[r["bank"]], r["position"]) for r in rows if r["bank"] in box and r["kind"] == "relay"}


def box_seat_ends(doc):
    """Fuse box guts are not drawn (Dan 2026-11-09, "you're not drawing the fuse box guts"; 2026-11-07 "draw each wire as a wire
    end coming to the box"; DECISIONS "Bus bars and fuse box ends"): a box relay (a relay seated in the POWER / LOGIC box) and the
    LOGIC fuse outputs are no connectors in a harness file. Each harness wire that lands on one ends on its own terminal,
    labelled box, seat and terminal ("LOGIC box seat M8, terminal 86 - DRL relay (K-DRL)"), drawn where that cavity was (its
    pin sits where the cavity pin sat, so every route stays); in the layout the terminals sit on a branch point at the old
    connector spot, on the same stub, so no routed length changes. A relay outside the boxes (K-EPS, RLY-DRL) stays; the trunk relay block is a box too (K-FP, Dan S1 a 2026-11-09)."""
    seats = _seat_map()
    sid_ = lambda s: re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    conds = doc.get("wires", []) + [q for c in doc.get("cables", []) for q in c["cores"] + ([c["shield"]] if "shield" in c else [])]
    keep = []
    for c in doc.get("connectors", []):
        mid = c["id"][2:].replace("_", "-") if c["id"].startswith("c_") else None
        if mid not in seats and mid != "LOGIC":
            keep.append(c)
            continue
        box, seat = seats.get(mid, ("LOGIC box", None))
        p, lp = c.get("schematicPosition"), c.get("layoutPosition")
        bp = None
        if lp is not None:
            bp = "bp_" + c["id"][2:] + "_seat"
            doc.setdefault("branchPoints", []).append({"id": bp, "layoutPosition": dict(lp)})
            for b in doc.get("bundles", []):
                for k in ("sourceId", "targetId"):
                    if b.get(k) == c["id"]:
                        b[k] = bp
        for i, cv in enumerate(c["cavities"]):
            ends = [e for w in conds for e in (w.get("source"), w.get("target")) if e and e["id"] == c["id"] and e["handle"] == cv["id"]]
            if not ends:
                continue
            d = cv.get("designation", "")
            tid = "t_%s__%s" % (c["id"][2:], sid_(d))
            lab = ("%s seat %s, terminal %s - %s" % (box, seat, d, c.get("label", mid)) if seat
                   else "%s fuse output %s" % (box, d))
            t = {"id": tid, "type": "Loose", "label": lab, "width": c.get("width", 240)}     # the contact is a box part
            if p is not None:
                t["schematicPosition"] = {"x": p["x"], "y": p["y"] + 30 * (i + 1)}
            if lp is not None:
                # a terminal cannot sit on a branch point: each seat end hangs off the old connector spot on its own 0 mm
                # bundle, so every routed length stays the stub length (lengths = master)
                n_at = sum(1 for b in doc.get("bundles", []) if b.get("sourceId") == bp and b["id"].startswith("b_seat_"))
                t["layoutPosition"] = {"x": lp["x"] + 30 * (n_at + 1), "y": lp["y"]}
                doc.setdefault("bundles", []).append({"id": "b_seat_" + tid[2:], "sourceId": bp, "targetId": tid, "length": {"value": 0, "unit": "mm"}})
            doc.setdefault("terminals", []).append(t)
            for e in ends:
                e["id"], e["handle"] = tid, "Terminal"
    doc["connectors"] = keep
    gone = {c["id"] for c in doc.get("connectors", [])}
    doc["mates"] = [m for m in doc.get("mates", []) if m["sourceId"] in gone and m["targetId"] in gone] if "mates" in doc else None
    if doc.get("mates") is None:
        doc.pop("mates", None)
    return doc


def prune_parts(doc):
    """Drop every document part nothing uses any more (a box relay, its socket contacts, a mount): a part stays only if some
    element (or a kept part's configuration accessory) refers to it, so the BOM shows no quantity-0 rows (Dan R1 a, 2026-11-09)."""
    def ids(x, out):
        if isinstance(x, dict):
            for k, v in x.items():
                if (k == "partId" or k.endswith("PartId")) and isinstance(v, str):
                    out.add(v)
                else:
                    ids(v, out)
        elif isinstance(x, list):
            for v in x:
                ids(v, out)
        return out
    # a connector part's default contact (a ContactPart accessory) counts only for a used cavity with no contact of its own;
    # when every such cavity names its own contact, the default would be a quantity-0 BOM row, so this document's copy of the
    # part drops it (the part library is not touched)
    for p in doc.get("connectorParts", []):
        users = [c for c in doc.get("connectors", []) if c.get("partId") == p["id"]]
        if any(not cv.get("notConnected") and not cv.get("contactPartId") for c in users for cv in c.get("cavities", [])):
            continue
        for cfg in p.get("configurations", []):
            cfg["accessories"] = [a for a in cfg.get("accessories", []) if a.get("type") != "ContactPart"]
        p["configurations"] = [cfg for cfg in p.get("configurations", []) if cfg["accessories"]]
        if not p["configurations"]:
            del p["configurations"]
    refs = ids({k: v for k, v in doc.items() if not k.endswith("Parts")}, set())
    parts = {p["id"]: p for k, v in doc.items() if k.endswith("Parts") for p in v}
    todo = list(refs & set(parts))
    while todo:             # a kept part keeps its configuration accessories (contacts, plugs, locks, mounts)
        p = parts[todo.pop()]
        for c in p.get("configurations", []):
            for a in c.get("accessories", []):
                if a.get("partId") in parts and a["partId"] not in refs:
                    refs.add(a["partId"])
                    todo.append(a["partId"])
    for k in [k for k in doc if k.endswith("Parts")]:
        doc[k] = [p for p in doc[k] if p["id"] in refs]
        if not doc[k]:
            del doc[k]
    return doc


def box_groups(doc, outside=()):
    """The fuse boxes in a generated harness file (Dan R1 a, 2026-11-09: box insides live only in the box CAD model; the harness
    stops at the box). No device groups any more: box_seat_ends turns each box relay / LOGIC fuse output end into a labelled
    terminal, the box stud rings stay plain terminals, and nothing box-related is excludeFromBom, so every harness wire counts in
    the app's lengths and BOM. prune_parts then drops the parts nothing uses. `outside` is kept for the callers (unused)."""
    box_seat_ends(doc)
    prune_parts(doc)
    return doc


def ungroup(doc):
    """genroute.py: lift every group member to the root under the id the rest of the document uses for it ("<group id>-<id>",
    cavities too), so the router sees every node; regroup() puts them back. Returns what regroup() needs."""
    saved = []
    for g in doc.get("groups", []):
        keep = {}
        for key, ns in g["document"].items():
            for n in ns:
                m = dict(n, id=g["id"] + "-" + n["id"])
                if "cavities" in n:
                    m["cavities"] = [dict(cv, id=g["id"] + "-" + cv["id"]) for cv in n["cavities"]]
                doc.setdefault(key, []).append(m)
            keep[key] = [g["id"] + "-" + n["id"] for n in ns]
        saved.append((g, keep))
    return saved


def regroup(doc, saved):
    """Undo ungroup(): each lifted member goes back into its group under its own id (positions as they are now)."""
    for g, keep in saved:
        pre = g["id"] + "-"
        for key, ids in keep.items():
            byid = {n["id"]: n for n in doc[key]}
            out = []
            for q in ids:
                n = byid[q]
                m = dict(n, id=q[len(pre):])
                if "cavities" in n:
                    m["cavities"] = [dict(cv, id=cv["id"][len(pre):]) for cv in n["cavities"]]
                out.append(m)
            g["document"][key] = out
            doc[key] = [n for n in doc[key] if n["id"] not in set(ids)]
            if not doc[key]:
                del doc[key]
    return doc


# ------------------------------------------------------------------------------------------------ plain labels (Dan 2026-11-08)
# DECISIONS "harness.design files (B6)" R1-R9: a connector / splice / terminal is named in plain words (the master's
# <end>_name, no internal code), a pin shows its basic signal (the master's <end>_desc, one name per net), a wire label says
# what that wire is for (the master's wire_label, never its id), notes never repeat a label, no empty connectors, a bussed plug
# is drawn mated to its bussed receptacle (no bridges), ring terminals carry their maker part. relabel() applies them to a
# generated document after placement, so positions stay as placed.
OEM_DEV = {'JB1': 'J/B No.1', 'IE1': 'Cowl plug IE1', 'IG2': 'Cowl plug IG2', 'II1': 'Cowl plug II1', 'RB4': 'R/B No.4',
           'I2': 'Cowl splice I2', 'C13': 'Cluster plug C13 (B)', 'C14': 'Cluster plug C14 (C)', 'C16': 'Combination switch plug C16 (B)',
           'C17': 'Cruise clutch switch C17', 'S9': 'Stop lamp switch S9', 'R10': 'Dimmer R10', 'A15': 'A/C amplifier A15',
           'A32': 'A/C amplifier A32', 'A1': 'Ambient temp sensor A1', 'A4': 'A/C compressor A4', 'A5': 'A/C pressure switch A5',
           'H1': 'LH headlamp H1', 'H2': 'RH headlamp H2', 'F5': 'LH side marker F5', 'F6': 'RH side marker F6',
           'F7': 'LH front turn lamp F7', 'F8': 'RH front turn lamp F8', 'F9': 'Wiper motor F9', 'R2': 'LH pop-up motor R2',
           'R3': 'RH pop-up motor R3', 'W1': 'Washer motor W1', 'R8': 'Pop-up relay R8'}
CABLE_NAMES = {'CAB-RSPUR': 'Rear wheel speed cable (cabin)', 'CAB-ETBS': 'Throttle sensor cable', 'CAB-CAN-CSB': 'Switch board CAN cable',
               'CAB-CAN-CLU': 'Cluster CAN cable', 'CAB-CAN-RD': 'RealDash Pi CAN cable', 'CAB-TURBO-C': 'Turbo speed cable (cabin)',
               'CAB-ETBS-C': 'Throttle sensor cable (cabin)', 'CAB-CAM-C': 'Cam sensor cable (cabin)', 'CAB-APS1': 'Pedal sensor 1 cable',
               'CAB-APS2': 'Pedal sensor 2 cable', 'CAB-FSPUR': 'Front wheel speed cable (cabin)', 'CAB-CAM': 'Cam sensor cable',
               'CAB-TURBO': 'Turbo speed cable', 'CAB-CRANK-C': 'Crank sensor cable (cabin)', 'CAB-KNOCK1-C': 'Knock sensor cable (cabin)',
               'CAB-ETBM-C': 'Throttle motor cable (cabin)', 'CAB-CANBH-BC': 'CAN-Lambda CAN cable (cabin)', 'CAB-CRANK': 'Crank sensor cable',
               'CAB-ETBM-AE': 'Throttle motor cable', 'CAB-KNOCK1': 'Knock sensor cable', 'CAB-LAMCAN-BE': 'CAN-Lambda CAN cable',
               'CAB-CAN-ECU': 'ECU CAN cable', 'CAB-CAN-T2': 'CAN trunk cable, switch board to cluster',
               'CAB-CAN-T3': 'CAN trunk cable, cluster to Pi', 'CAB-RL': 'RL wheel speed sensor cable', 'CAB-RR': 'RR wheel speed sensor cable',
               'CAB-FL': 'FL wheel speed sensor cable', 'CAB-FR': 'FR wheel speed sensor cable'}
# the mating bussed receptacle of each bussed DT plug (Dan R6; TE DEUTSCH, the master's housing_extra "(bussed receptacle)";
# Del City DT bussed receptacles "One 12-Pin Buss" / "One 8-Pin Buss"; mates with standard DT plugs). Its wedgelock is TBD by the
# TE drawing, so the part carries no accessory.
BUSSED_RCPT = {12: {"id": "cp_dt04_12pa_p021", "partNumber": "DT04-12PA-P021", "manufacturer": "TE Connectivity DEUTSCH",
                    "description": "CONNECTOR, RECEPTACLE, DT, 12 POS, BUSSED (ONE 12-PIN BUSS), KEY A", "gender": "Male",
                    "hasShell": False, "numberOfCavities": 12,
                    "url": "https://www.digikey.com/en/products/detail/te-connectivity-deutsch-connectors/DT04-12PA-P021/9923072"},
               8: {"id": "cp_dt04_08pa_p021", "partNumber": "DT04-08PA-P021", "manufacturer": "TE Connectivity DEUTSCH",
                   "description": "CONNECTOR, RECEPTACLE, DT, 8 POS, BUSSED (ONE 8-PIN BUSS), KEY A", "gender": "Male",
                   "hasShell": False, "numberOfCavities": 8}}


def _sid(s):
    return re.sub(r'[^A-Za-z0-9]', '_', s)


def oem_short(i, p, cowl=False):
    """A factory lead's terminal label (R4 short, R1 plain): device words, its 1993 code, the pin - "Cluster plug C14 (C) pin 8"."""
    if i == 'JB1' and '-' in p:
        return 'J/B No.1 %s pin %s' % tuple(p.split('-', 1))
    if i == 'W1':
        return 'Washer motor W1 pin %s (%s)' % (p, 'cowl lead' if cowl else 'at the motor')
    if i in ('H1', 'H2') and p in ('DRL', 'TURN'):
        return '%s %s lead' % (OEM_DEV[i], 'DRL' if p == 'DRL' else 'turn')
    return '%s pin %s' % (OEM_DEV.get(i, i), p)


def short_oem_note(t):
    """R4: an OEM splice note stops at the factory wire and where it lands: "Splice to OEM wire Y - cluster plug C14 (C) pin 8"."""
    if not t.startswith('Splice to OEM wire '):
        return t
    head, _, rest = t.partition(' - ')
    return head + (' - ' + rest.split(', ')[0] if rest else '')


def relabel(doc, rows=None):
    """Apply Dan's 2026-11-08 label rules (R1-R9, DECISIONS "harness.design files (B6)") to a generated document in place,
    after placement: plain names, wire labels, short notes, bussed receptacles mated to their plugs, no empty connectors,
    ring terminal parts. Returns doc."""
    rows = rows if rows is not None else master_rows()
    names, oem, label_of, ring_pn = {}, {}, {}, collections.defaultdict(set)
    for r in rows:
        if r.get('wire_id') and r.get('wire_label'):
            label_of[r['wire_id']] = r['wire_label']
        for s in ('from', 'to'):
            i, t = r[s + '_id'], r[s + '_type']
            if not i:
                continue
            if t == 'OEM':
                oem[_sid('%s-%s' % (i, r[s + '_pin']))] = oem_short(i, r[s + '_pin'])
                oem[_sid('%s-%s cowl' % (i, r[s + '_pin']))] = oem_short(i, r[s + '_pin'], True)
            elif r[s + '_name']:
                names.setdefault(_sid(i), r[s + '_name'])
            if t == 'terminal' and r.get('wire_id') and not is_integral(r):
                ring_pn[_sid(i)].add(r[s + '_terminal_pn'])
    names[_sid('T-AT-DOOR')] = 'Door switch line, J/B No.1 1B pin 11'
    def boxed(mid):
        for gid, gname, gp, test in BOX_GROUPS:
            if test(mid):
                return gname.split(' (')[0]
    ids = {_sid(r[s + '_id']): r[s + '_id'] for r in rows for s in ('from', 'to') if r[s + '_id']}
    removed = set()
    # connectors: plain names; a box relay says which box it sits in; drop a connector with no wired cavity (R5)
    mated = {m[k] for m in doc.get('mates', []) for k in ('sourceId', 'targetId')}
    keep = []
    for c in doc.get('connectors', []):
        cid = c['id']
        if cid.endswith('_MATE'):
            base = names.get(cid[2:-5])
            c['label'] = '%s, plug-in part' % base if base else c['label']
        elif cid.startswith('c_') and cid[2:] in names:
            nm, mid = names[cid[2:]], ids.get(cid[2:], '')
            box = boxed(mid) if mid.startswith('K-') else None
            code = mid if mid.startswith(RELAY_CODE) and mid not in nm else None      # Dan 2026-11-08: relays keep their code
            extra = ', '.join(x for x in (code, box) if x)
            c['label'] = '%s (%s)' % (nm, extra) if extra else nm
        if c.get('cavities') and all(cv.get('notConnected') for cv in c['cavities']) and cid not in mated:
            removed.add(cid)
            continue
        keep.append(c)
    doc['connectors'] = keep
    for key in ('splices', 'diodes', 'resistors'):
        for n in doc.get(key, []):
            nm = names.get(n['id'][2:])
            if not nm:
                continue
            away = re.findall(r'; to ([^,;]+),', n.get('label') or '')
            n['label'] = nm + (' (continues in %s)' % ' and '.join(dict.fromkeys(a.strip() for a in away)) if away else '')
    for cab in doc.get('cables', []):
        k = ids.get(cab['id'][4:], cab.get('label'))
        cab['label'] = CABLE_NAMES.get(k, cab.get('label'))
    tparts = {}
    for t in doc.get('terminals', []):
        tid = t['id'][2:]
        if tid in oem:
            t['label'] = oem[tid]
        else:
            base = next((b for b in sorted(names, key=len, reverse=True) if tid == b or tid.startswith(b + '_')), None)
            if base:
                rest = tid[len(base):].strip('_')
                t['label'] = names[base] + (' (%s)' % ('CAN H' if rest.startswith('CAN_H') else 'CAN L' if rest.startswith('CAN_L') else '')
                                            if rest.startswith(('CAN_H', 'CAN_L')) else '')
                pns = {p for p in ring_pn.get(base, ()) if p and not p.upper().startswith(('TBD', 'FLYING', 'INTEGRAL'))}
                if t.get('type') == 'Ring' and len(pns) == 1:      # R7: the ring terminal's maker part (one PN on that stud)
                    pn = pns.pop()
                    tparts.setdefault(pn, {"id": "tp_" + _sid(pn).lower(), "partNumber": pn, "type": "Ring",
                                           "description": "Ring terminal %s (master terminal_pn)" % pn})
                    t['partId'] = tparts[pn]['id']
        if '; ' in (t.get('signal') or ''):      # R3: one signal type per stud, never a list of what lands on it
            t['signal'] = t['signal'].split('; ')[0]
    if tparts:
        have = {p['id'] for p in doc.get('terminalParts', [])}
        doc.setdefault('terminalParts', []).extend(p for p in tparts.values() if p['id'] not in have)
    for w in doc.get('wires', []):      # R2: a wire label says what that wire is for
        il = w.get('identLabel') or ''
        key = il if il in label_of else il.split(': ')[0]      # an INTEGRAL link reads "<id>: <text>" (gen_heavydc)
        if key in label_of:
            w['identLabel'] = label_of[key]
    # R6: a bussed plug, mated to its bussed receptacle; every pin one global signal (the bus), no bridges
    for c in list(doc.get('connectors', [])):
        mid = ids.get(c['id'][2:], '')
        if not mid.startswith('BUS-'):
            continue
        n = len(c['cavities'])
        part = BUSSED_RCPT.get(n)
        if not part:
            continue
        if not any(p['id'] == part['id'] for p in doc.get('connectorParts', [])):
            doc.setdefault('connectorParts', []).append(dict(part))
        for cv in c['cavities']:
            if cv.get('signal'):
                cv['global'] = True
        rid = c['id'] + '_RCPT'
        rc = {"id": rid, "label": "%s, bussed receptacle" % names.get(c['id'][2:], mid), "width": c.get('width', 240), "partId": part['id'],
              "cavities": [{"id": "%s_RCPT.%d" % (c['id'][2:], k), "designation": str(k)} for k in range(1, n + 1)]}
        if 'schematicPosition' in c:
            rc['schematicPosition'] = {"x": c['schematicPosition']['x'] + 330, "y": c['schematicPosition']['y']}
        if 'layoutPosition' in c:
            lp, other = c['layoutPosition'], None
            for b in doc.get('bundles', []):
                o = b['targetId'] if b['sourceId'] == c['id'] else b['sourceId'] if b['targetId'] == c['id'] else None
                if o:
                    other = next((x.get('layoutPosition') for k in ('branchPoints', 'connectors', 'terminals', 'splices')
                                  for x in doc.get(k, []) if x['id'] == o), None)
                    pts = b.get('layoutPoints') or []
                    if pts:     # a bent stub: face away from the bend next to the plug, not the far node (Dan 2026-11-09)
                        other = (pts[-1] if b['targetId'] == c['id'] else pts[0])['layoutPosition']
                    break
            dx, dy = (lp['x'] - other['x'], lp['y'] - other['y']) if other else (1, 0)
            ux, uy = (1 if dx > 0 else -1 if dx < 0 else 0), (1 if dy > 0 else -1 if dy < 0 else 0)
            if abs(dx) >= abs(dy): uy = 0
            else: ux = 0
            rc['layoutPosition'] = {"x": lp['x'] + 150 * (ux or 1 if not uy else 0), "y": lp['y'] + 150 * uy}
        doc['connectors'].append(rc)
        doc.setdefault('mates', []).append({"id": "m_" + c['id'][2:] + "_RCPT", "sourceId": c['id'], "targetId": rid})
    # notes: R4 short OEM splice notes; plain names for codes; nothing about a removed connector
    code_ids = sorted({i for i in ids.values() if '-' in i and _sid(i) in names}, key=len, reverse=True)
    gone = {ids.get(x[2:], x) for x in removed}
    for key in ('schematicNotes', 'layoutNotes'):
        for nt in doc.get(key, []):
            t = short_oem_note(nt.get('text') or '')
            tid = nt['id'][len('n_oem_t_'):] if nt['id'].startswith('n_oem_t_') else None
            if tid in oem and t.startswith('Splice to OEM wire '):      # "Splice to OEM wire Y - cluster plug C14 (C) pin 8"
                lab = oem[tid]
                lab = lab[0].lower() + lab[1:] if len(lab) > 1 and lab[1].islower() else lab
                t = '%s - %s' % (t.split(' - ')[0], lab)
            if gone:
                parts = re.split(r'(?<=[.]) (?=[A-Z0-9][A-Za-z0-9-]*: )', t)
                t = ' '.join(p for p in parts if not any(p.startswith(g + ':') for g in gone))
            if nt['id'] != 'n_title':      # the title note is the file's own story; every other note names parts in plain words
                for i in code_ids:
                    t = re.sub(r'(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])' % re.escape(i), names[_sid(i)], t)
                t = re.sub(r'(?<![A-Za-z0-9_])(?:w|wc|cab)_[a-z0-9_]+(?![A-Za-z0-9_])',
                           lambda m: '"%s"' % label_of[m.group(0)] if m.group(0) in label_of else m.group(0), t)
                t = re.sub(r'(?:^|(?<=\. ))(.+?): \1[,;] ', r'\1: ', t)      # R4: never the label twice
            nt['text'] = t
    if removed:      # a dropped connector takes its stub bundle with it (sweep 5, 2026-11-10: gen_cabin left bn_c_ECU_C)
        doc['bundles'] = [b for b in doc.get('bundles', []) if b['sourceId'] not in removed and b['targetId'] not in removed]
    relabel.removed = sorted(removed)      # the empty connectors dropped (R5), for the generator's report
    return doc


# B9 6 in OEM pigtails: the new wire is spliced onto the factory lead at these front devices (lamps, pop-ups, ambient
# sensor, wiper; README "What stays and what goes"), even where an older oem_method says "terminated at the device's plug"
PIGTAIL_DEVICES = {'H1', 'H2', 'R2', 'R3', 'F5', 'F6', 'F7', 'F8', 'F9', 'A1'}


def oem_splices(r):
    """The OEM ends of a wire that is spliced onto a factory wire, with that wire's colour code from `oem_wire_colour`:
    [(side, colour)], colour '' when the master gives none (README "Pin text": the note `Splice to OEM wire X-X`, Dan
    2026-11-04 Y6). An end counts when its own method splices or solders onto a factory lead, or it is a B9 pigtail
    device. Two OEM ends: `oem_wire_colour` / `oem_method` are "from / to"; one value for two ends belongs to the end
    `oem_location` names. A device's own plug (A4, A5, the washer motor W1) is no splice."""
    if is_removal(r) or not r.get('wire_id'):
        return []
    sides = [s for s in ('from', 'to') if r[s + '_type'] == 'OEM']
    cols = [c.strip() for c in (r.get('oem_wire_colour') or '').split(' / ')]
    meths = [m.strip() for m in (r.get('oem_method') or '').split(' / ')]
    split = len(sides) == 2 and len(meths) == 2
    def spliced(k, s):
        # per end: its half of a "from / to" method, else (two OEM ends, one method) its own terminal text
        how = (meths[k] if split else (r[s + '_terminal_pn'] or '') + ('' if len(sides) == 2 else ' ' + meths[0])).lower()
        return r[s + '_id'] in PIGTAIL_DEVICES or 'splice' in how or 'solder onto' in how
    ends = [(k, s) for k, s in enumerate(sides) if spliced(k, s)]
    out = []
    for k, s in ends:
        if len(sides) == 2 and len(cols) == 2: col = cols[k]
        elif len(sides) == 2 and len(ends) == 2:      # one colour, two spliced ends: the end oem_location names
            col = cols[0] if ('%s pin %s' % (r[s + '_id'], r[s + '_pin'])) in (r.get('oem_location') or '') else ''
        else: col = cols[0]
        col = re.sub(r'\s*\(.*\)$', '', col).strip()
        out.append((s, col if re.match(r'^[A-Z]{1,2}(-[A-Z]{1,2})?$', col) else ''))
    return out


_PLACE = re.compile(r'kick|dash|cowl|glove|ECU|column|steering|pedal|fender|corner|firewall|panel|cluster|centre|center|'
                    r'under|behind|front|rear|trunk|console', re.I)


def oem_splice_note(r, s, col):
    """The full OEM splice note for end `s` of row `r` (README "Pin text", Dan 2026-11-05 N16 a): `Splice to OEM wire X-X`,
    then the OEM connector / housing code (1993), the OEM pin, what the factory wire is and where the splice sits, e.g.
    `Splice to OEM wire G-Y - cluster plug C13 (B) pin 11, turn RH indicator, behind the cluster`. Built from the end's own
    master fields (`<s>_id`, `<s>_pin`, `<s>_name`, `<s>_desc`) and its half of `oem_location`; a part the master does not
    give reads TBD."""
    oid, pin, name = r[s + '_id'], r[s + '_pin'], r[s + '_name']
    sides = [x for x in ('from', 'to') if r[x + '_type'] == 'OEM']
    segs = [g.strip() for g in (r.get('oem_location') or '').split(' / ')] if len(sides) == 2 else [r.get('oem_location') or '']
    seg = segs[0]
    if len(sides) == 2 and len(segs) == 2:
        mine = [g for g in segs if '%s pin %s' % (oid, pin) in g or ' %s ' % oid in ' %s ' % g]
        seg = mine[0] if len(mine) == 1 else segs[sides.index(s)]
    # code and pin: J/B and R/B cavities are "<plug>-<pin>" / "<fuse>-<pin>" in the master
    if oid == 'JB1' and '-' in pin:
        code, pin = 'J/B No.1 ' + pin.split('-')[0], pin.split('-', 1)[1]
    elif oid == 'RB4':
        m = re.search(r'pin (\d+)', name)
        code, pin = 'R/B No.4', (m.group(1) if m else pin)
    else:
        m = re.search(re.escape(oid) + r' (\([A-Z]\))', name)
        code = oid + (' ' + m.group(1) if m else '')
    # the device words before the code ("cluster plug", "LH headlamp"); none for the J/B / R/B cavities
    pre = (' ' + name + ' ').split(' ' + oid + ' ')[0] if (' ' + oid + ' ') in (' ' + name + ' ') else re.sub(r'\spin \d.*$', '', name)
    pre = re.sub(r'\([^)]*\)', '', re.sub(r'^OEM\b', '', pre.strip()))
    pre = re.sub(r'\s+', ' ', pre).strip(' ,')
    if oid in ('JB1', 'RB4'): pre = ''
    what_where = (pre + ' ' if pre else '') + code + ' pin ' + pin
    # what the factory wire is: oem_location after " - ", less its cite, colour and side remarks; else the end's own text
    circ = seg.split(' - ', 1)[1] if ' - ' in seg else ''
    circ = re.split(r'[;:]', circ)[0]
    circ = re.sub(r'\s*\([^)]*(EWD|p\.\d)[^)]*\)', '', circ)
    circ = re.sub(r'^[A-Z]{1,2}(-[A-Z]{1,2})?,\s*', '', circ).strip(' ,')
    loc = ''
    parts = [p.strip() for p in circ.split(',')]
    if len(parts) > 1 and _PLACE.search(parts[-1]):
        circ, loc = ', '.join(parts[:-1]), parts[-1]
    if not circ: circ = (r.get(s + '_desc') or '').strip() or 'TBD'
    # where: a place in the end's name, else in oem_location after the code, else a B9 pigtail, else TBD
    if not loc:
        for p in re.findall(r'\(([^)]*)\)', name):
            if _PLACE.search(p) and not re.fullmatch(r'[A-Z]', p): loc = p; break
    for txt in (seg, name):
        if loc: break
        m = re.search(r'(?:%s|pin \S+)(?: pin \S+)?(?: [A-Z]{2,3})?,\s*([^,;]+)' % re.escape(oid), txt)
        if m and _PLACE.search(m.group(1)): loc = m.group(1).split(' - ')[0].strip()
    if not loc and oid in ('C12', 'C13', 'C14'): loc = 'behind the cluster'
    if not loc and oid in PIGTAIL_DEVICES: loc = 'at the device, 6 in OEM pigtail'
    return 'Splice to OEM wire %s - %s, %s, %s' % (col, what_where, circ, loc or 'location TBD')


# Schematic text sizes in harness.design (measured in the app, Dan N99 a, 2026-11-08): a terminal's label tag sits 25 px
# above its 30-high box (a connector's label is inside its header row); a note's text (xs font, line height 14.4 px, 0.6 em
# padding top and bottom) is centred on its 30-high row, about 50 characters a line at the widest width, 360.
LABEL_H, LINE_H = 25, 14.4


def note_lines(text, width=360):
    """Estimated number of text lines of a schematic note (word-wrapped, about 50 characters a line at width 360)."""
    import textwrap
    return max(1, len(textwrap.wrap(text or '', max(10, width * 50 // 360))))


def note_h(text, width=360):
    """Estimated drawn height (px) of a schematic note, its text plus the 0.6 em padding above and below."""
    return LINE_H * (note_lines(text, width) + 1)


def end_span(node, notes=()):
    """An end's extent relative to its y, as ((top, bottom) of its box with a terminal's label tag above it, (top, bottom)
    of the text of the notes on its top row or None, (top, bottom) of a label tag wider than the box or None). The notes
    (an OEM splice note, a connector's N/C note) sit in their own column beside the end, their text centred on its top row;
    a terminal's label tag is centred over its box, about 30 + 5.3 px a character wide, so a long one reaches into the
    note column."""
    box = (0, 30 + 30 * len(node['cavities']) + (30 if node.get('shell') else 0)) if 'cavities' in node else (-LABEL_H, 30)
    txt = None
    for t in notes:
        half = LINE_H * note_lines(t) / 2
        txt = (min(15 - half, txt[0]), max(15 + half, txt[1])) if txt else (15 - half, 15 + half)
    wide = 'cavities' not in node and 30 + 5.3 * len(node.get('label') or '') > node.get('width', 150) + 20
    return box, txt, ((-LABEL_H, -4) if wide else None)


def text_step(prev_span, span, gap=5, note_gap=8, tag_gap=3):
    """The smallest grid step (a multiple of 30) from one stacked end's y to the next's that keeps their boxes and label
    tags `gap` apart, their notes' text `note_gap` apart and a wide label tag `tag_gap` clear of the note above it (Dan
    N99 a, 2026-11-08: spread out only where the text is)."""
    (b1, t1, _), (b2, t2, w2) = prev_span, span
    need = b1[1] - b2[0] + gap
    if t1 and t2: need = max(need, t1[1] - t2[0] + note_gap)
    if t1 and w2: need = max(need, t1[1] - w2[0] + tag_gap)
    return int(math.ceil(need / 30.0)) * 30


def span_rows(span):
    """(top, bottom) of everything an end draws (box, label tag, note text), for keeping other wires' rows out of it."""
    parts = [p for p in span if p]
    return min(p[0] for p in parts), max(p[1] for p in parts)


# A new fuse box's harness wire landings, in cavity order, for its harness.design part (library 5LO8): the box drawing's
# "harness wires at the fuses" sheet is the source. LOGIC (B2): ST185-FB-100L rev V.01 sheet 3 (models folder
# st185_fusebox_1101 revB = cad/fusebox rev 7): the two M5 bus feed lugs, the 21 mini fuse outputs, the two own fuse inputs.
BOX_CAVITIES = {'LOGIC': ['BUS1'] + ['BUS1-%d' % i for i in range(1, 11)] + ['BUS2'] + ['BUS2-%d' % i for i in range(1, 10)] +
                ['BUS2-12', 'BUS2-12 IN', 'BUS2-13', 'BUS2-13 IN']}


def master_rows(removed=False):
    """The master as rows, with the field names the drawing code uses (from_conn = the end ID ...). Removal rows are
    left out (they are not wires to build) unless `removed` is set."""
    with open(MASTER, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if removed or not is_removal(r)]
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
            name = (c + " " + r[s + "_conn_name"]).lower()      # plain names (Dan 2026-11-08) start with a capital
            for pat, node in self.layout.get("place_oem", []):
                if pat.lower() in name:
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
        if is_integral(r):      # both ends must still be placed (a splice reached only by links too); no route, no length
            return [], None
        if a is None or b is None:
            return None, None
        p = self.path(a, b)
        if p is None:
            self.problems.append("%s: no layout path from %s to %s" % (r["wire_id"], a, b))
            return None, None
        end = self.layout.get("end_allowance_mm", 100)      # termination and service loop at a connector / terminal end
        spl = self.layout.get("splice_allowance_mm", end)    # strip and solder at a splice end (Dan T7 b, 2026-11-10: 25 mm)
        mm = sum(self.seg_len(x, y) for x, y in zip(p, p[1:])) + sum(spl if r[e + "_type"] == "splice" and not STUD_SPLICE.match(r[e + "_id"]) else end for e in ("from", "to"))
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


# ------------------------------------------------------------------------------------------------ master lengths from the tree
# PLACED (Dan N69 a, 2026-11-07; DECISIONS "Placement and lengths (B8)"): the harnesses Dan has placed whose lengths step
# (OPEN-ITEMS row 183 phase 4, Dan L2 a) is done. Their master `est_length_mm` is the tree length, written only by
# --write-lengths, and --check fails on any difference. A harness joins here at its lengths step, once Dan OKs its
# before -> after list (--lengths <harness>); until then it keeps its estimate. AntiTheft joined 2026-11-07 (Dan N70 a).
# CabinPower joined 2026-11-08 (Dan approved the N120 seed layout as is; H1 a). RearFuel joined 2026-11-09 (Dan O1 a).
PLACED = ("AB-cabin", "AB-engine", "EngineRoom-C", "HeavyDC", "Dash", "AntiTheft", "CabinPower", "WheelSpeed-Front",
          "WheelSpeed-Rear", "RearFuel")
LENGTH_COL = "est_length_mm"


def is_connector_pass(r):
    """A row joining the two halves of one through-connector (the RADLOK cabin / engine plug pairs `w_rl_pos` / `w_rln`,
    Dan D2 2026-11-04): it is the connector itself, not a wire to cut, so it has no length (blank in the master)."""
    return (r["from_type"] == r["to_type"] == "connector" and r["from_id"] != r["to_id"]
            and r["from_housing_pn"] not in ("", "TBD") and r["from_housing_pn"] == r["to_housing_pn"])


def _mm_text(v):
    return "" if v in (None, "") else str(int(round(float(v))))


def tree_lengths(H, only=PLACED):
    """[(wire_id, harness, master, tree)] for every wire owned by a harness in `only`: the master `est_length_mm` and the
    tree length as the master writes it (route(): tree path + `end_allowance_mm` at each end); '' for an INTEGRAL row or
    a through-connector pair (no length); None when the wire does not route (H.problems says why)."""
    out = []
    for r in H.wires:
        if r["harness"] not in only:
            continue
        if is_integral(r) or is_connector_pass(r):
            tree = ""
        else:
            tree = H.route(r)[1]
            tree = None if tree is None else _mm_text(tree)
        out.append((r["wire_id"], r["harness"], r[LENGTH_COL].strip(), tree))
    return out


def length_changes(H, only=PLACED):
    """The rows of tree_lengths() whose master length is not the tree length (unrouted wires left to H.problems)."""
    return [x for x in tree_lengths(H, only) if x[3] is not None and _mm_text(x[2] or None) != x[3]]


def _field_spans(line):
    """(start, end) of each field of one CSV line, quotes kept, so one field is replaced without re-quoting the rest."""
    spans, i, n = [], 0, len(line)
    while True:
        j = i
        if j < n and line[j] == '"':
            j += 1
            while True:
                k = line.index('"', j)
                if k + 1 < n and line[k + 1] == '"':
                    j = k + 2
                    continue
                j = k + 1
                break
        while j < n and line[j] != ",":
            j += 1
        spans.append((i, j))
        if j >= n:
            return spans
        i = j + 1


def set_master_lengths(text, new):
    """The master text with `est_length_mm` set per {wire_id: mm text}; only that field of those lines changes (line
    endings and every other field's quoting kept). Fails if a wire id is not found or a line is not one whole record."""
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    head = next(csv.reader([lines[0]]))
    wi, li = head.index("wire_id"), head.index(LENGTH_COL)
    left = dict(new)
    for k, line in enumerate(lines[1:], 1):
        if not line:
            continue
        rec = next(csv.reader([line]))
        if len(rec) != len(head):
            raise SystemExit("master line %d is not one whole record (%d fields): not written" % (k + 1, len(rec)))
        if rec[wi] in left:
            a, b = _field_spans(line)[li]
            lines[k] = line[:a] + left.pop(rec[wi]) + line[b:]
    if left:
        raise SystemExit("not written: wire id(s) not in the master: %s" % ", ".join(sorted(left)))
    return eol.join(lines)


def lengths_list(changes):
    for wid, hn, before, after in changes:
        print("   %-16s %-22s %6s -> %s" % (hn, wid, before or "(blank)", after or "(blank)"))


def lengths_run(argv):
    """--lengths [harness ...]: print the before -> after list (default PLACED; any harness for its lengths step, L2 a).
    --write-lengths [harness ...]: write it into the master (PLACED harnesses only), then rewrite the wire lists."""
    write = "--write-lengths" in argv
    hs = tuple(a for a in argv if not a.startswith("-")) or PLACED
    unknown = [h for h in hs if h not in {r["harness"] for r in master_rows()}]
    if unknown:
        raise SystemExit("no such harness in the master: %s" % ", ".join(unknown))
    if write and set(hs) - set(PLACED):
        raise SystemExit("not written: %s not in PLACED; add it there once Dan OKs its before -> after list (L2 a, N69 a)"
                         % ", ".join(sorted(set(hs) - set(PLACED))))
    changes, problems = [], []
    for s in own_harnesses():
        if not set(hs) & set(set_harnesses(s)):
            continue
        H = Harness(s)
        changes += length_changes(H, hs)
        problems += H.problems
    for p in problems:
        print("PROBLEM", p)
    print("master lengths from the tree (%s): %d change(s)" % (", ".join(hs), len(changes)))
    lengths_list(changes)
    if not write or not changes:
        return 1 if problems else 0
    if problems:
        raise SystemExit("not written: %d problem(s)" % len(problems))
    with open(MASTER, encoding="utf-8", newline="") as f:
        text = f.read()
    # Build the new text first, then swap it in: a failure leaves the master untouched (it used to be emptied).
    new_text = set_master_lengths(text, {wid: after for wid, hn, before, after in changes})
    if not new_text.strip():
        raise SystemExit("not written: the new master text is empty")
    tmp = MASTER + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)
    os.replace(tmp, MASTER)
    print("wrote", os.path.relpath(MASTER, REPO))
    for s in own_harnesses():
        build(s)
    return 0


# ------------------------------------------------------------------------------------------------ checks
def check(h):
    H = Harness(h)
    bad = list(H.problems)
    for r in H.wires:
        H.route(r)
    bad += [x for x in H.problems if x not in bad]
    for wid, hn, before, after in length_changes(H):
        bad.append("%s (%s): master est_length_mm %s, tree length %s - lengths come from the tree only (N69 a): show Dan "
                   "the list (build_drawings.py --lengths), then --write-lengths" % (wid, hn, before or "blank", after or "blank"))
    for name in wirelist_harnesses(H):
        gen = wirelist_rows(H, name)[1]
        have, want_wl = xlsx_digest(wirelist_path(name)), wirelist_digest(H, name)
        if have != want_wl:
            bad.append("%s is stale (inputs %s, made from %s): run build_drawings.py %s"
                       % (os.path.basename(wirelist_path(name)), want_wl, have or "none", h))
        tag = os.path.basename(wirelist_csv_path(name))
        have_csv, _csv_rows = read_wirelist_csv(name)
        if have_csv != wirelist_csv_text(gen):
            bad.append("%s is %s: run build_drawings.py %s" % (tag, "stale" if have_csv else "missing", h))
        bad += wirelist_readback(name, gen, tag)
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
# Dan C1 b (2026-11-08, DECISIONS B22): nothing Dan reads carries a code. "Wire" is the wire label (what the wire is for),
# From / To / Splice are plain names; only relay codes stay, after the name (fuse box seats and pins are pins). The master
# ids ride along in "_"-prefixed keys that the CSV / xlsx never print, for the read-back.
WL_COLS = [("Wire", 30), ("From", 34), ("From Pin", 9), ("To", 34), ("To Pin", 9), ("Splice", 30), ("Branch", 11),
           ("Signal", 30), ("Colour", 9), ("Gauge (AWG)", 8), ("Length (mm)", 9), ("Wire Type", 17), ("Cable", 15),
           ("Cable Part Number", 20), ("From Contact PN", 17), ("To Contact PN", 17), ("Built With", 14),
           ("Continues", 50), ("Route Branch", 34), ("OEM Ref", 40), ("Notes", 60)]
RELAY_CODE = ("K-", "RLY-")


def plain_names(rows):
    """master id -> the name Dan reads: the master <end>_name, a relay's code after it (Dan 2026-11-08)."""
    out = {}
    for r in rows:
        for s in ("from", "to"):
            i, p = r[s + "_id"], r[s + "_pin"]
            if not i:
                continue
            n = r[s + "_name"] or i
            n = "%s (%s)" % (n, i) if i.startswith(RELAY_CODE) and i not in n else n
            out.setdefault(i, n)
            out.setdefault((i, p), n)      # a factory id whose ends sit in different spots (A5 pin 4, I2) is named per pin
    return out


def plain_text(t, names, labels):
    """Notes in plain words: master ids (other than relays) -> names, wire ids -> their labels in quotes."""
    if not t:
        return t
    for i in sorted((i for i in names if isinstance(i, str) and "-" in i and not i.startswith(RELAY_CODE)), key=len, reverse=True):
        if i in t:
            t = re.sub(r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])" % re.escape(i), names[i], t)
    return re.sub(r"(?<![A-Za-z0-9_])(?:w|wc|cab|br)_[a-z0-9_]+(?![A-Za-z0-9_])",
                  lambda m: '"%s"' % labels[m.group(0)] if m.group(0) in labels else m.group(0), t)


AWG_MM2 = {"1/0": 53.5, "2": 33.6, "4": 21.15, "6": 13.3, "8": 8.37, "10": 5.26, "12": 3.31, "14": 2.08, "16": 1.31, "18": 0.823, "20": 0.519,
           "22": 0.324, "24": 0.205}


def wirelist_harnesses(H):
    return [x for x in H.layout.get("wirelists", []) if x in H.set]


def wirelist_path(name):
    return os.path.join(WIRELISTS, "ST185-%s-wirelist.xlsx" % name)


def wirelist_csv_path(name):
    return os.path.join(WIRELISTS, "ST185-%s-wirelist.csv" % name)


def wirelist_csv_text(rows):
    """The Wires sheet as CSV: the same columns, master ids and names, LF line ends (F1 allows only this generated CSV
    besides the master; Dan B2 a). Removal rows never reach it (master_rows skips them)."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, [c for c, _w in WL_COLS], lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for d in rows:
        w.writerow({k: ("" if v is None else v) for k, v in d.items()})
    return buf.getvalue()


def read_wirelist_csv(name):
    """(text with LF line ends, rows) of the committed CSV, or (None, None)."""
    path = wirelist_csv_path(name)
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read().replace("\r\n", "\n")
    return text, list(csv.DictReader(io.StringIO(text)))


def write_wirelist_csv(H, name):
    text = wirelist_csv_text(wirelist_rows(H, name)[1])
    if read_wirelist_csv(name)[0] == text:
        return None
    os.makedirs(WIRELISTS, exist_ok=True)
    with open(wirelist_csv_path(name), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return wirelist_csv_path(name)


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

# The From / To rule (DECISIONS B8 "S8 a", Dan 2026-11-10; wire lists T8 b, Dan 2026-11-11): From = the end nearer the
# power or signal source, To = the device end. The one definition: check_wiring D1 holds the master to it, the wire
# lists are written by it (wirelist_rows) and read back against it (wirelist_readback).
S8_HUB = re.compile(r"^(ECU-|BATT-POS$|T-TRUNK-NEG$|LOGIC$|T-PWR-|K-|RLY-|BATT-RELAY-BLOCK$|KILL-SW$|JUMP-POST$|F-PI$"
                    r"|JB\d|RB\d|GND-|IE$|T-AT-GND$|T-ENG-BLOCK|T-ALT-B$)")
S8_PASS = re.compile(r"^(DRB102-|RADLOK-|IE1$|IG2$|II1$|EA1$|I2$|I9$)")


def s8_rank(t, i):
    """Where an end (its master type and id) stands in the S8 a order; the lower rank is From. 0 hubs (ECU plugs, battery
    posts, POWER / LOGIC boxes and studs, relays, trunk relay block, kill switch, jump post, inline fuse, factory J/B /
    R/B, ground points and studs, alternator B+), 1 firewall bulkhead, RADLOK plugs, factory cowl plugs / cowl splices,
    2 bus plugs and splices, 3 resistors and diodes, 4 devices (a floating cable screen is a device end)."""
    if t == "splice":
        return 2
    if S8_HUB.match(i):
        return 0
    if S8_PASS.match(i):
        return 1
    if i.startswith("BUS-"):
        return 2
    return 3 if t in ("resistor", "diode") else 4


def s8_types(rows):
    """End id -> master type, plus how a wire-list end reads ("legs of <splice>" is a splice, 'NC, floats' a screen)."""
    types = {r[s + "_id"]: r[s + "_type"] for r in rows for s in ("from", "to") if r[s + "_id"]}

    def rank(i):
        if i.startswith("legs of "):
            return 2
        return 4 if i == NC[0] else s8_rank(types.get(i, ""), i)
    return rank


def s8_master_first(m, fr, to):
    """True when the wire-list ends (fr, to) stand in their master row's own order: the tie-break of S8 a ("a wire whose
    two ends rank the same keeps its order"). A leg's far end stands on the splice side of its master row."""
    for s, mine, other in (("from", fr, to), ("to", to, fr)):
        if m[s + "_type"] == "splice":
            leg = ("legs of %s" % m[s + "_id"], "-")
            if leg in (mine, other) and mine != other:
                return mine == leg
        elif m[s + "_type"] != "cable screen" and _end(m, s) in (mine, other) and mine != other:
            return mine == _end(m, s)
    return True


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
        else the one link to another splice, else the one wire to a power or ground source, else the one wire to a relay
        (the relay's output feeding the splice, e.g. K-HR 87 into SP-HR-HI; sweep 9), else the one factory tap,
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
        pick = pick or one([x for x in ws if far(x)[1].startswith("K-")])
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
    names = plain_names(allrows)
    labels = {r["wire_id"]: (r.get("wire_label") or r["from_desc"] or r["to_desc"] or r["wire_id"]) for r in allrows}

    def nm(i, pin=None):
        """An end as Dan reads it: plain name ("legs of <splice name>"; 'NC, floats' stays)."""
        if i.startswith("legs of "):
            return "legs of " + names.get(i[8:], i[8:])
        return names.get((i, pin), names.get(i, i))

    def continues(r, ends, splices):
        out = []
        for c, pin in ends:
            mate = BULKHEAD_MATE.get(c)
            for m, side in by_pin.get((mate, pin), []) if mate else []:
                o = SpliceNets.other(side)
                oc, op = _end(m, o) if m[o + "_type"] != "splice" else ("splice", m[o + "_id"])
                far = ("%s pin %s" % (nm(oc, op), op)) if oc != "splice" else names.get(op, op)
                out.append('ST185-%s "%s" at %s pin %s, to %s' % (m["harness"], labels[m["wire_id"]], nm(mate), pin, far))
        for sp in splices:
            other = sorted({x["harness"] for x, _s in nets.at[sp]} - {name})
            if other:
                out.append("%s also joins %s" % (names.get(sp, sp), ", ".join("ST185-" + h for h in other)))
        return "; ".join(out)
    first = {"AB-cabin": ["ECU-A", "ECU-B"], "AB-engine": ["DRB102-ENGINE"]}.get(name, [])
    rank = s8_types(allrows)
    out = []
    for r in wires:
        ft, tt = r["from_type"], r["to_type"]
        side_dev = None
        if ft == "splice" and tt == "splice":
            fr, to = ("legs of %s" % r["from_id"], "-"), ("legs of %s" % r["to_id"], "-")
            splices, branch, dev, oth = [r["from_id"], r["to_id"]], "link", None, None
            fc = tc = "INTEGRAL" if is_integral(r) else "solder splice"
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
            branch = "drain" if "cable screen" in (ft, tt) else ("core" if r["cable"] else ("link" if is_integral(r) else "wire"))
            fc, tc, fd, td = r["from_terminal_pn"], r["to_terminal_pn"], r["from_name"], r["to_name"]
        # T8 b (Dan 2026-11-11): every row reads source end first, by the master's own rule (S8 a); a tie keeps the
        # master row's order
        if (rank(fr[0]), not s8_master_first(r, fr, to)) > (rank(to[0]), False):
            fr, to, fc, tc, fd, td = to, fr, tc, fc, td, fd
        if r["cable"] and branch in ("leg", "trunk"):
            branch += " core"
        sig = r["from_desc"] or r["to_desc"]
        notes = [x for x in (r["from_note"], r["to_note"], r["notes"]) if x]
        if branch.startswith("drain") and NC in (fr, to):
            notes.insert(0, "Screen floats at this end: cut back and seal under heat-shrink")
        oem = "; ".join(x for x in (r["oem_location"], r["oem_wire_colour"] and "OEM colour " + r["oem_wire_colour"],
                                    r["oem_ewd_page"] and "EWD " + r["oem_ewd_page"], r["oem_method"]) if x)
        fc, tc = plain_text(fc, names, labels), plain_text(tc, names, labels)
        out.append({"Wire": labels[r["wire_id"]], "From": nm(*fr), "From Pin": fr[1], "To": nm(*to), "To Pin": to[1],
                    "Splice": " > ".join(names.get(s, s) for s in splices), "Branch": branch, "Signal": sig,
                    "Colour": r["colour"], "Gauge (AWG)": r["gauge_awg"],
                    "Length (mm)": "none (INTEGRAL)" if is_integral(r) else (r["est_length_mm"] or "TBD"), "Wire Type": r["wire_pn"] or ("(cable core)" if r["cable"] else "TBD"),
                    "Cable": CABLE_NAMES.get(r["cable"], r["cable"] and "shielded cable"), "Cable Part Number": r["cable_pn"],
                    "From Contact PN": fc, "To Contact PN": tc, "Built With": "ST185-" + r["harness"],
                    "Continues": continues(r, [fr, to], splices),
                    "Route Branch": plain_text(r["route_branch"], names, labels), "OEM Ref": plain_text(oem, names, labels),
                    "Notes": plain_text(" | ".join(notes), names, labels),
                    "_wire": r["wire_id"], "_from": fr[0], "_from_pin": fr[1], "_to": to[0], "_to_pin": to[1],
                    "_splices": list(splices)})

    def key(d):
        f = d["_from"]
        return (first.index(f) if f in first else len(first) + (1 if f.startswith(("legs of", "NC")) else 0), d["From"],
                pin_sort(d["From Pin"]), d["Wire"], d["_wire"])
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
                sp["Wires"].append((r["wire_id"], r["gauge_awg"] or "screen"))
                sp["mm2"] += AWG_MM2.get(r["gauge_awg"], 0.0)
    allrows = [r for r in master_rows() if r["wire_id"]]
    names = plain_names(allrows + list(H.spares))      # Dan C1 b: plain names only (relay codes after the name)
    labels = {r["wire_id"]: (r.get("wire_label") or r["from_desc"] or r["to_desc"] or r["wire_id"]) for r in allrows}
    spare = collections.Counter(r["from_id"] for r in H.spares if r["harness"] == name)
    order = {"connector": 0, "OEM": 1, "terminal": 2, "splice": 3, "resistor": 4, "diode": 5, "cable screen": 6}
    conns = []
    for e in sorted(ends.values(), key=lambda e: (order.get(e["Type"], 9), names.get(e["Connector"], e["Connector"]))):
        e = dict(e)
        e["Contacts"] = ", ".join(sorted(e["Contacts"]))
        e["Spare Cavities"] = spare.get(e["Connector"], 0)
        e["Connector"] = names.get(e["Connector"], e["Connector"])
        conns.append(e)
    nets = SpliceNets(allrows)
    sps = [{"Splice": names.get(v["Splice"], v["Splice"]), "Trunk": labels[nets.trunk(v["Splice"])[0]["wire_id"]],
            "Method": v["Method"], "Wires Joined": len(v["Wires"]), "Total Copper (mm2)": round(v["mm2"], 2),
            "Wires": ", ".join('"%s" (%s AWG)' % (labels[w], g) for w, g in v["Wires"])} for v in splices.values()]
    spares = [{"Connector": names.get(r["from_id"], r["from_id"]), "Cavity": r["from_pin"], "Plug / Contact": r["from_terminal_pn"],
               "Note": r["from_desc"] or r["notes"]} for r in sorted(
                   (r for r in H.spares if r["harness"] == name), key=lambda r: (r["from_id"], pin_sort(r["from_pin"])))]
    return conns, sps, spares


def wirelist_readback(name, rows, tag=None):
    """Check a generated wire list against the master (Option A, DECISIONS "Wire lists"): every wire once, both
    device ends with their pins, gauge and colour; From / To never a splice and never blank; one trunk per splice;
    From is the source end (S8 a / T8 b).
    `rows` are wirelist_rows() rows: since Dan C1 b the printed columns are plain names, so the check reads the master
    ids the rows carry in their "_" keys; the committed CSV / xlsx are held equal to these rows by --check."""
    path = wirelist_path(name)
    rows = [dict(d, Wire=d["_wire"], From=d["_from"], To=d["_to"], Splice=" > ".join(d["_splices"]),
                 **{"From Pin": d["_from_pin"], "To Pin": d["_to_pin"]}) for d in rows]
    allrows = [r for r in master_rows() if r["wire_id"]]
    splices = {r[s + "_id"] for r in allrows for s in ("from", "to") if r[s + "_type"] == "splice"}
    want = {r["wire_id"]: r for r in allrows
            if r["harness"] == name or name in [x.strip() for x in r["passes_through"].split("/")]}
    bad, seen, trunks = [], collections.Counter(), collections.Counter()
    rank = s8_types(allrows)
    tag = tag or os.path.basename(path)
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
        fr, to = (d["From"], d["From Pin"]), (d["To"], d["To Pin"])
        if (rank(fr[0]), not s8_master_first(m, fr, to)) > (rank(to[0]), False):
            bad.append("%s: %s reads %s -> %s: From is the source end (S8 a / T8 b: hubs, then bulkhead and cowl plugs, "
                       "then bus plugs and splices, then resistors and diodes, then devices; a tie keeps the master's "
                       "order)" % (tag, w, fr[0], to[0]))
        ends = {fr, to}
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
    sheet(wb.create_sheet("Connectors"), [("Connector", 44), ("Part Number", 20), ("Type", 12), ("Extras", 30),
                                          ("Contacts", 30), ("Wires", 7), ("Spare Cavities", 9), ("Pin Numbering", 50)], conns)
    sheet(wb.create_sheet("Splices"), [("Splice", 40), ("Trunk", 30), ("Method", 16), ("Wires Joined", 9),
                                       ("Total Copper (mm2)", 11), ("Wires", 80)], sps)
    sheet(wb.create_sheet("Spare Cavities"), [("Connector", 40), ("Cavity", 9), ("Plug / Contact", 20), ("Note", 50)], spares)
    key = wb.create_sheet("Key")
    for line in ("ST185-%s wire list - generated from docs/harness/MASTER-wirelist.csv by build_drawings.py; edit the master, "
                 "never this file." % name,
                 "Wire = what the wire is for (its label). Names are plain words; only relays keep their code after the name "
                 "(Dan 2026-11-08). Fuse box seats, studs and pins keep their numbers.",
                 "One row per wire segment, From end to To end. From = the end nearer the power or signal source, To = the "
                 "device end (Dan 2026-11-11, the master's rule): fuse / relay boxes, ECU plugs, relays, battery and ground "
                 "points first, then the firewall bulkhead and factory cowl plugs, then bus plugs and splices, then "
                 "resistors and diodes, then devices.",
                 "Colour = insulation colour (harness.design colour names). No ident bands (Dan 2026-10-31).",
                 "Length (mm) = the master's estimate; TBD until the tape-measure pass (OPEN-ITEMS row 165).",
                 "Built With = the harness that owns the wire; a wire owned by another harness passes through this one.",
                 "Option A (DECISIONS 'Wire lists'): From / To are only connectors or devices with their pin, never a splice. "
                 "Splice = the splice(s) the wire lands in; Branch = wire, core, leg, trunk, link or drain.",
                 "A leg's splice end reads as where its trunk lands (through any link splices): its From when that is the source "
                 "end, else its To; a trunk or link end in a splice reads 'legs of <splice name>'.",
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
            if dev.get("moved_to"):   # moved to another harness's own map (Route 16 HeavyDC ends -> Route 1, Dan B6 b)
                continue
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
                    # the line goes on past it: a breakout of at least 6 in (Dan 2026-10-29); a device at the end of the
                    # Route 16 trunk itself gets it too, as no sensor is wired 0 mm from the trunk (Dan W4 c, 2026-11-10)
                    if i_e < len(items) - 1 or (legacy and k in roots):
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
        rows = [r for r in master_rows() if r["wire_id"] and (spec["harness"] == r["harness"] or spec["harness"] in [x.strip() for x in r["passes_through"].split("/")])]
        def at(r, s):   # a "roots" tree also places factory ends (by `place_oem`, as Harness.place does)
            if legacy or r[s + "_type"] != "OEM":
                return place.get(r[s + "_id"])
            return next((n for pat, n in L.get("place_oem", []) if pat in r[s + "_id"] + " " + r[s + "_name"]), None)
        for _ in range(4):
            # only joins move (splices, resistors, diodes, cable screens): a device end of another harness's wire that
            # passes through this tree (T5 a) keeps its own place
            for c in sorted({r[s + "_id"] for r in rows for s in ("from", "to") if (legacy or r[s + "_type"] != "OEM")
                             and (r["harness"] == spec["harness"] or r[s + "_type"] in ("splice", "resistor", "diode", "cable screen"))}
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



# ------------------------------------------------------------------------------------------------ ghost wires (Dan T4 a)
# Every harness.design file shows the other harnesses' wires that pass through its bundles (Dan T4 a, 2026-11-10): each as a
# ghost wire in its real colour between two Loose terminals left out of the BOM, one where it joins this file's bundles and one
# where it leaves, each on a short stub whose end carries a coloured tag naming the file the wire belongs to. With strands=True
# (AB-engine, near the 100-connection limit) one ghost strand per other harness and path instead, named "<file> x<n>".
GHOST_COLOUR = {"AB-cabin": "Blue", "AB-engine": "Violet", "EngineRoom-C": "Orange", "CabinPower": "Red", "Dash": "Green",
                "AntiTheft": "Pink", "HeavyDC": "Black", "RearFuel": "Tan", "WheelSpeed-Front": "Gray", "WheelSpeed-Rear": "Gray"}   # app colour names (labels take no hex)
GHOST_DX = 150        # a ghost terminal sits this far right of its branch point, one row (30) per ghost below it
GHOST_SNAP = 10.0     # layout-node units (about 120-150 mm on the car)
_PART_COLOURS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon"}
ABCABIN_SEEDS = ('BUS-5V', 'BUS-5V-2', 'BUS-GNDOUT-A', 'BUS-GNDOUT-B', 'SP-8V', 'BUS-SHIELD-A', 'SP-SHIELD-B')
ABCABIN_SHARED = ('ECU-A', 'ECU-B', 'ECU-C', 'DRB102-CABIN')


def abcabin_doc_of(rows):
    """AB-cabin's split into two harness.design files (Dan 2026-11-04, V1 a): union every wire's devices (a shared plug is no
    link), splices and shielded cable; document 1 = the group(s) holding the sensor rails and screens, document 2 = the rest.
    Returns {wire_id: 1 or 2} for the AB-cabin wires in rows."""
    W = [r for r in rows if r["harness"] == "AB-cabin" and r["wire_id"]]
    def unit(r, s):
        i, t = r[s + "_id"], r[s + "_type"]
        if not i or i in ABCABIN_SHARED:
            return None
        return ("cable", i) if t == "cable screen" else (t == "OEM", i)
    def units(r):
        return [u for u in (unit(r, "from"), unit(r, "to"), ("cable", r["cable"]) if r["cable"] else None) if u]
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for r in W:
        us = units(r)
        for u in us:
            find(u)
        for u in us[1:]:
            par[find(u)] = find(us[0])
    one = {find((False, s)) for s in ABCABIN_SEEDS if (False, s) in par}
    return {r["wire_id"]: 1 if any(find(u) in one for u in units(r)) else 2 for r in W}


def ghost_file(r, doc_of=None):
    """the harness.design file a master wire is drawn in (name without its rev letter, R10)"""
    if r["harness"] == "AB-cabin":
        d = (doc_of or abcabin_doc_of(master_rows())).get(r["wire_id"], 2)
        return "ST185-AB-cabin %d" % d
    return "ST185-" + r["harness"]


def add_ghosts(doc, H, host, strands=False, rows=None):
    """Add the ghost wires of `host` to a finished document (after placement, routing, relabel); returns how many conductors
    were added. Ghost ids start w_gh_ / t_gh_ / bn_gh_, so a length check against the master skips them."""
    rows = rows if rows is not None else master_rows()
    doc_of = abcabin_doc_of(rows)
    bps = {b["id"]: b for b in doc.get("branchPoints", [])}
    # another harness's tree may run along the same line with its own nodes (EngineRoom-C on Route 16 line 6): a path node
    # with no branch point of its own here takes the nearest branch point drawn here (layout node xy, within GHOST_SNAP)
    nodes = H.layout["nodes"]
    by_sid = {_sid(n): n for n in nodes}
    bp_xy = [(b, nodes[by_sid[b[3:]]]["xy"]) for b in bps if b[3:] in by_sid and nodes[by_sid[b[3:]]].get("xy")]
    def host_bp(n):
        if "bp_" + _sid(n) in bps:
            return "bp_" + _sid(n)
        xy = nodes.get(n, {}).get("xy")
        if not xy or not bp_xy:
            return None
        b, q = min(bp_xy, key=lambda t: (t[1][0] - xy[0]) ** 2 + (t[1][1] - xy[1]) ** 2)
        return b if (q[0] - xy[0]) ** 2 + (q[1] - xy[1]) ** 2 <= GHOST_SNAP ** 2 else None
    found = []
    for r in rows:
        if not r["wire_id"] or r["harness"] == host or host not in [x.strip() for x in r["passes_through"].split("/")]:
            continue
        p, _ = H.route(r)
        on = [b for b in (host_bp(n) for n in (p or [])) if b]
        if len(on) < 2 or on[0] == on[-1]:
            print("ghost: %s has no run through %s's bundles, not drawn" % (r["wire_id"], host))
            continue
        found.append((r, on[0], on[-1]))
    if not found:
        return 0
    groups = collections.OrderedDict()
    for r, a, b in found:
        key = (r["harness"], a, b) if strands else (r["wire_id"],)
        groups.setdefault(key, []).append((r, a, b))
    xs = [n["schematicPosition"]["x"] for k in ("connectors", "terminals", "splices", "cables", "resistors", "diodes")
          for n in doc.get(k, []) if n.get("schematicPosition")]
    ys = [n["schematicPosition"]["y"] + 30 + 30 * len(n.get("cavities", n.get("cores", []))) for k in
          ("connectors", "terminals", "splices", "cables", "resistors", "diodes") for n in doc.get(k, []) if n.get("schematicPosition")]
    x0, y = (min(xs) // 30) * 30, ((max(ys) + 150) // 30) * 30
    doc.setdefault("schematicNotes", []).append({
        "id": "n_ghosts", "width": 360, "schematicPosition": {"x": x0, "y": y - 60},
        "text": "Ghost wires: other harnesses' wires in these bundles (not built with this harness)."})
    # one ghost terminal per branch point and owner file, every ghost wire of that file lands on it (a tidy tag, no row per wire)
    terms, sch_rows = collections.OrderedDict(), collections.Counter()
    taken = [(n["layoutPosition"]["x"], n["layoutPosition"]["y"]) for k_ in ("connectors", "terminals", "splices", "resistors", "diodes")
             for n in doc.get(k_, []) if n.get("layoutPosition")]
    def term(bp, owner, fname, side):
        key = (bp, fname)
        if key not in terms:
            k = sum(1 for (b, _f) in terms if b == bp)
            q = bps[bp]["layoutPosition"]
            ty = q["y"] + 30 * (k + 1)      # one row per tag; a row another tag (or part) already uses nearby moves down
            while any(abs(ox - (q["x"] + GHOST_DX)) < 420 and oy == ty for ox, oy in taken):
                ty += 30
            taken.append((q["x"] + GHOST_DX, ty))
            tid = "t_gh_%s_%s" % (_sid(bp[3:]), _sid(fname.replace("ST185-", "")))
            x = x0 if side == "a" else x0 + 660
            terms[key] = {"id": tid, "type": "Loose", "label": fname.replace("ST185-", ""), "signal": "", "width": 240,
                          "excludeFromBom": True, "_n": 0, "_owner": owner,
                          "schematicPosition": {"x": x, "y": y + 30 * sch_rows[x]},
                          "layoutPosition": {"x": q["x"] + GHOST_DX, "y": ty}}
            sch_rows[x] += 1
            # a square stub: out along the comb line beside the branch point, then across to the terminal
            doc.setdefault("bundles", []).append({
                "id": "bn_" + tid[2:], "sourceId": bp, "targetId": tid, "length": {"value": 100, "unit": "mm"},
                "layoutPoints": [{"id": "bn_%s_p0" % tid[2:], "layoutPosition": {"x": q["x"] + 30, "y": q["y"]}},
                                 {"id": "bn_%s_p1" % tid[2:], "layoutPosition": {"x": q["x"] + 30, "y": ty}}],
                "separateLabels": True, "label": "", "endLabel": fname.replace("ST185-", ""),
                "endLabelColor": GHOST_COLOUR.get(owner, "Gray")})
        terms[key]["_n"] += 1
        return terms[key]["id"]
    n_added = 0
    for key, items in groups.items():
        r, a, b = items[0]
        owner, fname = r["harness"], ghost_file(r, doc_of)
        gid = _sid("%s_%s_%s" % (owner, a, b)) if strands else _sid(r["wire_id"])
        label = ("%s x%d" % (fname.replace("ST185-", ""), len(items))) if strands else (r.get("wire_label") or r["wire_id"])
        colour = GHOST_COLOUR.get(owner, "Gray") if strands else (r["colour"] if r["colour"] in _PART_COLOURS else "Gray")
        ta, tb = term(a, owner, fname, "a"), term(b, owner, fname, "b")
        doc.setdefault("wires", []).append({"id": "w_gh_%s" % gid, "source": {"id": ta, "handle": "Terminal"},
                                            "target": {"id": tb, "handle": "Terminal"}, "color": colour, "identLabel": label})
        n_added += 1
    for t in terms.values():
        nw = t.pop("_n"); t["signal"] = "%d %s wire%s (not built here)" % (nw, t["label"], "" if nw == 1 else "s")
        t.pop("_owner")
        doc.setdefault("terminals", []).append(t)
    return n_added

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
        for wl in (write_wirelist(H, name), write_wirelist_csv(H, name)):
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


def self_test():
    """Prove the N69 a length check fails on a broken copy (in memory; nothing is written). CI runs it."""
    cases = []
    H = Harness(own_harnesses()[0])
    base = length_changes(H)
    cases.append(("the committed master matches the tree for every placed harness", base == []))
    def flagged(mutate, only=PLACED):
        rows = {r["wire_id"]: r for r in H.wires}
        saved = {k: dict(v) for k, v in rows.items()}
        mutate(rows)
        got = {x[0] for x in length_changes(H, only)} - {x[0] for x in base}
        for k, v in saved.items():
            rows[k].update(v)
        return got
    plain = lambda h: next(r for r in H.wires if r["harness"] == h and not is_integral(r) and not is_connector_pass(r))
    w = plain(PLACED[0])
    cases.append(("a placed wire 1 mm off its tree length",
                  flagged(lambda rs: rs[w["wire_id"]].update(est_length_mm=str(int(float(w["est_length_mm"])) + 1))) == {w["wire_id"]}))
    cases.append(("a placed wire with a blank length", flagged(lambda rs: rs[w["wire_id"]].update(est_length_mm="")) == {w["wire_id"]}))
    link = next(r for r in H.wires if r["harness"] in PLACED and is_integral(r))
    cases.append(("an INTEGRAL link given a length",
                  flagged(lambda rs: rs[link["wire_id"]].update(est_length_mm="200")) == {link["wire_id"]}))
    pt = [r for r in H.wires if r["harness"] in PLACED and is_connector_pass(r)]
    cases.append(("the RADLOK pass-through pair stays blank", len(pt) == 2 and not {r["wire_id"] for r in pt} & {x[0] for x in base}))
    other = next((r for r in H.wires if r["harness"] not in PLACED and not is_integral(r) and r["est_length_mm"]), None)
    cases.append(("a harness not placed yet keeps its estimate", other is None or not flagged(
        lambda rs: rs[other["wire_id"]].update(est_length_mm=str(int(float(other["est_length_mm"])) + 7)))))
    with open(MASTER, encoding="utf-8", newline="") as f:
        text = f.read()
    rows = list(csv.reader(io.StringIO(text, newline="")))
    head = rows[0]
    wi, li = head.index("wire_id"), head.index(LENGTH_COL)
    q = next(r for r in rows[1:] if r[wi] and r[li] and '"' in text.split("\n")[rows.index(r)])
    same = set_master_lengths(text, {q[wi]: q[li]})
    new = set_master_lengths(text, {q[wi]: "12345"})
    got = list(csv.reader(io.StringIO(new, newline="")))
    want = [list(r) for r in rows]
    want[rows.index(q)][li] = "12345"
    diff_lines = [k for k, (a, b) in enumerate(zip(text.split("\n"), new.split("\n"))) if a != b]
    cases.append(("--write-lengths changes only that one field (quoting and line endings kept)",
                  same == text and got == want and diff_lines == [rows.index(q)] and new.count("\r\n") == text.count("\r\n")))
    # box guts are not drawn (Dan 2026-11-09, R1 a): the LOGIC fuse outputs and box relays become box seat ends (terminals)
    doc = {"connectors": [{"id": "c_LOGIC", "layoutPosition": {"x": 0, "y": 0}, "schematicPosition": {"x": 0, "y": 0},
                           "cavities": [{"id": "LOGIC.BUS2_3", "designation": "BUS2-3"}]},
                          {"id": "c_K_ACC", "label": "A/C clutch relay (K-ACC)", "cavities": [{"id": "K_ACC.87", "designation": "87"}]},
                          {"id": "c_K_EPS", "cavities": [{"id": "K_EPS.87"}]}, {"id": "c_ECU_A", "cavities": [{"id": "ECU_A.1"}]}],
           "terminals": [{"id": "t_T_PWR_NEG_GND_1"}],
           "wires": [{"id": "w1", "source": {"id": "c_LOGIC", "handle": "LOGIC.BUS2_3"}, "target": {"id": "c_ECU_A", "handle": "ECU_A.1"}},
                     {"id": "w2", "source": {"id": "t_T_PWR_NEG_GND_1", "handle": "Terminal"}, "target": {"id": "c_K_ACC", "handle": "K_ACC.87"}}],
           "bundles": [{"id": "b1", "sourceId": "bp1", "targetId": "c_LOGIC"}]}
    doc["connectors"][1]["partId"] = "cp_rly"
    doc["connectors"][3]["partId"] = "cp_ecu"
    doc["connectorParts"] = [{"id": "cp_rly", "configurations": [{"accessories": [{"type": "ContactPart", "partId": "ct_rly"}]}]},
                             {"id": "cp_ecu", "configurations": [{"accessories": [{"type": "ContactPart", "partId": "ct_ecu"}]}]}]
    doc["contactParts"] = [{"id": "ct_rly"}, {"id": "ct_ecu"}]
    g = box_groups(json.loads(json.dumps(doc)), outside=("K-ACC",))
    seat = {t["id"]: t.get("label") for t in g["terminals"]}
    cases.append(("box_groups (R1 a): no groups, nothing excludeFromBom, K-EPS a drawn relay, no box connector left",
                  "groups" not in g and "groupParts" not in g and sorted(c["id"] for c in g["connectors"]) == ["c_ECU_A", "c_K_EPS"]
                  and not any(n.get("excludeFromBom") for k in ("connectors", "terminals") for n in g.get(k, []))
                  and seat.get("t_K_ACC__87") == "LOGIC box seat M5, terminal 87 - A/C clutch relay (K-ACC)"))
    cases.append(("box_groups: seat ends take the wire on 'Terminal'; box ring terminal stays a plain terminal",
                  g["wires"][0]["source"] == {"id": "t_LOGIC__BUS2_3", "handle": "Terminal"}
                  and g["wires"][1]["source"]["id"] == "t_T_PWR_NEG_GND_1"
                  and g["wires"][1]["target"] == {"id": "t_K_ACC__87", "handle": "Terminal"} and g["bundles"][0]["targetId"] == "bp_LOGIC_seat"))
    cases.append(("prune_parts: the removed relay's part and its contact go; a used part keeps its accessory",
                  [p["id"] for p in g["connectorParts"]] == ["cp_ecu"] and [p["id"] for p in g["contactParts"]] == ["ct_ecu"]))
    doc["connectors"][3]["cavities"][0]["contactPartId"] = "ct_own"     # every used cavity names its own contact
    doc["contactParts"].append({"id": "ct_own"})
    g = box_groups(json.loads(json.dumps(doc)))
    cases.append(("prune_parts: a default contact no cavity uses leaves the part's copy (no quantity-0 BOM row)",
                  sorted(p["id"] for p in g["contactParts"]) == ["ct_own"]
                  and "configurations" not in next(p for p in g["connectorParts"] if p["id"] == "cp_ecu")))
    # the From / To rule on the wire lists (S8 a / T8 b): the generated rows pass, a row turned round fails
    s8 = lambda found: [x for x in found if "From is the source end" in x]
    for hn in own_harnesses():
        Hn = Harness(hn)
        for name in wirelist_harnesses(Hn):
            gen = wirelist_rows(Hn, name)[1]
            leg = next((d for d in gen if d["Branch"].startswith("leg") and d["_to"] not in (d["_from"], NC[0])), None)
            if not leg:
                continue

            def turned(d):
                return dict(d, _from=d["_to"], _from_pin=d["_to_pin"], _to=d["_from"], _to_pin=d["_from_pin"])
            cases.append(("wire list %s: every row reads source end first (S8 a / T8 b)" % name,
                          not s8(wirelist_readback(name, gen, name))))
            cases.append(("wire list %s: a leg row turned round (device first) is caught" % name,
                          len(s8(wirelist_readback(name, [turned(d) if d is leg else d for d in gen], name))) == 1))
    cases.append(("wire list From / To cases ran", any(n.startswith("wire list ") for n, _ok in cases)))
    # rule 4 (sweep 9): equal gauges, no box / J/B / bus / ground wire: the one relay output wire is the trunk, not the longest
    def _w(i, ft, fi, tt, ti, mm):
        return {"wire_id": i, "from_type": ft, "from_id": fi, "to_type": tt, "to_id": ti, "gauge_awg": "14",
                "est_length_mm": str(mm)}
    nets_t = SpliceNets([_w("w_k", "connector", "K-X", "splice", "SP-X", 125), _w("w_l", "splice", "SP-X", "OEM", "H1", 3053),
                         _w("w_r", "splice", "SP-X", "OEM", "H2", 1982), _w("w_d", "splice", "SP-X", "diode", "D-X", 1227)])
    cases.append(("splice trunk: the one relay output wire beats the longest (rule 4)",
                  nets_t.trunk("SP-X")[0]["wire_id"] == "w_k"))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("%-5s %s" % ("ok" if ok else "FAIL", n))
    print("%d self-test failure(s)." % len(bad))
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--lengths" in argv or "--write-lengths" in argv:
        return lengths_run(argv)
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
