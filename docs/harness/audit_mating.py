"""Bulkhead mating check - A cabin mates A engine, B cabin mates B engine.

    python docs/harness/audit_mating.py

Every loom is its own drawing, so nothing in harness.design joins the two halves
of a bulkhead. This script does. For each bulkhead cavity it traces the cabin-side
conductor back to the ECU pin it serves (through splices, one net at a time) and
checks, against sot/channels.csv:

  M1  a cavity used on one half is used on the other half too (no dead ends).
  M2  a signal crosses on the bulkhead of its own loom: an ECU pin whose SoT
      loom is A crosses on bulkhead A, loom B on bulkhead B.
  M5  one cavity, one ECU signal: a cavity never reaches two different
      signal-class ECU pins.
  M6  loom C has no bulkhead: the front wheel-speed drops (fender sub-loom of
      loom C) never land on a bulkhead cavity.
  M7  a device connector drawn on two looms has each cavity wired on one loom
      only (one cavity, one circuit).
  M8  the DRB102 physical cavity map (docs/harness/DRB102-CAVITY-MAP.md): every
      bulkhead cavity's `designation` is its real DRB102 cavity number, the same
      on both halves of its bulkhead; A and B together use each of the 102
      physical cavities exactly once; and the contact or sealing plug in each
      cavity is the size TE's drawing gives that cavity. Only live cavities count here:
      each drawing shows all 102 and marks the other section's cavities N/C
      (audit_shared_connectors.py checks those).

Shared rails (+5V, +8V, Gnd Out) are exempt from M2: loom B has no +5V pin, so
it borrows A32 by design. Pin *names* across each mating pair are checked by
audit_pin_names.py (rule 2); this file checks what the pins are wired to.
"""
import collections, csv, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REB = os.path.join(HERE, "rebuild")
SOT = os.path.join(HERE, "..", "..", "sot", "channels.csv")
PAIRS = {"bh_a_fw": "bh_a_eng", "bh_b_fw": "bh_b_eng"}
LETTER = {"bh_a_fw": "A", "bh_a_eng": "A", "bh_b_fw": "B", "bh_b_eng": "B"}
SHIELD = {("ecu_a", "a7"), ("ecu_b", "b17")}

with open(SOT, newline="", encoding="utf-8") as f:
    SOTROWS = {(r["conn"], r["pin"]): r for r in csv.DictReader(f) if r["owner"] == "ECU"}

bad = []


def conductors(d):
    for w in d.get("wires", []):
        yield w
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co
        if cb.get("shield"):
            yield cb["shield"]


def ecu_key(e):
    nid, h = e.get("id", ""), e.get("handle")
    if nid in ("ecu_a", "ecu_b"):
        return (nid, h)
    if nid.startswith(("dm_ecu_a_", "dm_ecu_b_")):
        p = nid.split("_")
        return ("ecu_" + p[2], p[3])
    return None


def node(e):
    """Graph node for one conductor end. Splices are one node whatever the
    handle; connector cavities are node+handle."""
    nid = e.get("id", "")
    k = ecu_key(e)
    if k:
        return ("ECU",) + k
    if nid.startswith("dm_bh_"):
        bh, cav = nid[3:].rsplit("_", 1)
        return ("C", bh, cav)
    if nid.startswith("sp_") or e.get("handle") == "Splice":
        return ("SP", nid)
    return ("C", nid, e.get("handle"))


used = collections.defaultdict(lambda: collections.defaultdict(list))  # conn -> cav -> [loom/wire]
graphs = {}
for path in sorted(glob.glob(os.path.join(REB, "*.harness"))):
    loom = os.path.basename(path)[6:-8]
    d = json.load(open(path, encoding="utf-8"))
    g = collections.defaultdict(set)
    for c in conductors(d):
        s, t = c.get("source") or {}, c.get("target") or {}
        if not s or not t:
            for e in (s, t):
                if e.get("id") in LETTER:
                    used[e["id"]][e.get("handle")].append("%s/%s" % (loom, c["id"]))
            continue
        a, b = node(s), node(t)
        g[a].add(b)
        g[b].add(a)
        for e in (s, t):
            n = node(e)
            if n[0] == "C" and n[1] in LETTER:
                used[n[1]][n[2]].append("%s/%s" % (loom, c["id"]))
    graphs[loom] = g


def reach(g, start):
    """ECU pins reachable from a bulkhead cavity without passing through another
    bulkhead cavity or a device cavity (splices are transparent)."""
    seen, out, todo = {start}, set(), [start]
    while todo:
        n = todo.pop()
        for m in g.get(n, ()):
            if m in seen:
                continue
            seen.add(m)
            if m[0] == "ECU":
                out.add(m[1:])
            elif m[0] == "SP":
                todo.append(m)
    return out


# M1 - both halves used
for fw, eng in PAIRS.items():
    for cav in sorted(set(used[fw]) | set(used[eng]), key=lambda x: int(str(x)[1:] or 0)):
        if bool(used[fw].get(cav)) != bool(used[eng].get(cav)):
            side, other = (fw, eng) if used[fw].get(cav) else (eng, fw)
            bad.append("M1 %s %s wired (%s), %s %s is not"
                       % (side, cav, ", ".join(used[side][cav]), other, cav))

# M2 / M5 - trace cabin halves back to ECU pins
for loom, g in graphs.items():
    for n in list(g):
        if n[0] != "C" or n[1] not in ("bh_a_fw", "bh_b_fw"):
            continue
        letter = LETTER[n[1]]
        pins = reach(g, n)
        sig = set()
        for k in pins:
            r = SOTROWS.get(k)
            if not r:
                continue
            if k in SHIELD:
                continue
            if r["class"] == "signal":
                sig.add(k)
                if r["loom"] in ("A", "B") and r["loom"] != letter:
                    bad.append("M2 %s: %s %s carries %s (%s.%s, loom %s) - it must cross "
                               "on bulkhead %s" % (loom, n[1], n[2], r["net"], k[0], k[1],
                                                   r["loom"], r["loom"]))
        if len(sig) > 1:
            bad.append("M5 %s: %s %s reaches %d signal pins: %s"
                       % (loom, n[1], n[2], len(sig), ", ".join("%s.%s" % k for k in sorted(sig))))

# M6 - loom C has no bulkhead: the front wheel-speed drops (a fender sub-loom
# of loom C, Daniel 2026-09-25) must never land on a bulkhead cavity.
LOOM_C_ENDS = {"wss_fl", "wss_fr"}
for path in sorted(glob.glob(os.path.join(REB, "*.harness"))):
    d = json.load(open(path, encoding="utf-8"))
    for c in conductors(d):
        ids = {(c.get(k) or {}).get("id", "") for k in ("source", "target")}
        if ids & LOOM_C_ENDS and any(i in LETTER or i.startswith("dm_bh_") for i in ids):
            bad.append("M6 %s: %s puts a front wheel-speed drop on a bulkhead - loom C "
                       "leaves through the fender, not a bulkhead" % (os.path.basename(path), c["id"]))
    for cn in d.get("connectors", []):
        if cn["id"] in LETTER:
            for cv in cn.get("cavities", []):
                t = cv.get("signal") or ""
                if "wheel speed" in t.lower() or "wss" in t.lower():
                    bad.append("M6 %s: %s %s is named %r - no wheel-speed circuit crosses a "
                               "bulkhead" % (os.path.basename(path), cn["id"], cv["id"], t))

# M7 - a device connector drawn on two looms: each cavity is wired on one
# loom only. Found 2026-09-25: ST185-CAN put CAN H/L on the CAN-Lambda's
# pins 1/2 while ST185-B-engine fed the same pins +12V and ground.
cav_owner = collections.defaultdict(set)
for path in sorted(glob.glob(os.path.join(REB, "*.harness"))):
    loom = os.path.basename(path)[6:-8]
    d = json.load(open(path, encoding="utf-8"))
    for c in conductors(d):
        for e in (c.get("source") or {}, c.get("target") or {}):
            nid = e.get("id", "")
            if not nid or nid in LETTER or nid.startswith(("dm_", "sp_", "ecu_")) \
                    or e.get("handle") in ("Splice", "Terminal", "Left", "Right", None):
                continue
            cav_owner[(nid, e["handle"])].add(loom)
for (nid, cav), looms in sorted(cav_owner.items()):
    if len(looms) > 1:
        bad.append("M7 %s %s is wired on %d looms (%s) - one cavity, one circuit"
                   % (nid, cav, len(looms), ", ".join(sorted(looms))))

# M8 - DRB102 physical cavity map. Cavity sizes from TE customer drawing
# DRB12-102PXE-L018 rev C3 (insert face): size 12 = 1-8 and 95-102, size 8 = 48, 49,
# 54, 55, size 4 = 43 and 60, size 16 = the other 80. Two wedgelock halves, 1-51 and
# 52-102. bh_a_* and bh_b_* each draw all 102; A / B are sections (ECU letter), not wedgelock halves.
DRB_SIZE = {n: 16 for n in range(1, 103)}
DRB_SIZE.update({n: 12 for n in list(range(1, 9)) + list(range(95, 103))})
DRB_SIZE.update({48: 8, 49: 8, 54: 8, 55: 8, 43: 4, 60: 4})
PART_SIZE = {"ct_hdp16p": 16, "ct_hdp16s": 16, "ct_hdp12p": 12, "ct_hdp12s": 12,
             "pl_sz16": 16, "pl_114017": 16, "pl_sz12": 12, "pl_sz8": 8, "pl_sz4": 4}
desig = {}   # bulkhead id -> {cavity id: physical number}
for path in sorted(glob.glob(os.path.join(REB, "*.harness"))):
    d = json.load(open(path, encoding="utf-8"))
    for cn in d.get("connectors", []):
        if cn["id"] not in LETTER:
            continue
        m = desig.setdefault(cn["id"], {})
        for cv in cn.get("cavities", []):
            if cv.get("notConnected") and not cv.get("cavityPlugPartId"):
                continue          # the other section's cavity, live on the other loom (audit_shared_connectors.py)
            num = str(cv.get("designation", ""))
            if not num.isdigit() or int(num) not in DRB_SIZE:
                bad.append("M8 %s %s designation %r is not a DRB102 cavity number (1-102)"
                           % (cn["id"], cv["id"], num))
                continue
            m[cv["id"]] = int(num)
            part = cv.get("contactPartId") or cv.get("cavityPlugPartId")
            if PART_SIZE.get(part) != DRB_SIZE[int(num)]:
                bad.append("M8 %s %s (DRB cavity %s, size %d) holds %s - not a size-%d part"
                           % (cn["id"], cv["id"], num, DRB_SIZE[int(num)], part, DRB_SIZE[int(num)]))
for fw, eng in PAIRS.items():
    if desig.get(fw) != desig.get(eng):
        diff = sorted(set(desig.get(fw, {}).items()) ^ set(desig.get(eng, {}).items()))
        bad.append("M8 %s and %s disagree on the cavity map: %s" % (fw, eng, diff[:6]))
phys = collections.Counter(desig.get("bh_a_fw", {}).values())
phys.update(desig.get("bh_b_fw", {}).values())
for n in sorted(DRB_SIZE):
    if phys[n] != 1:
        bad.append("M8 DRB102 cavity %d is used %d times across bulkheads A and B (must be 1)"
                   % (n, phys[n]))

for line in bad:
    print(line)
print("\n%d mating finding(s)." % len(bad))
sys.exit(1 if bad else 0)
