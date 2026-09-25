"""Bulkhead mating check - A cabin mates A engine, B cabin mates B engine.

    python docs/harness/audit_mating.py

Every loom is its own drawing, so nothing in harness.design joins the two halves
of a bulkhead. This script does. For each bulkhead cavity it traces the cabin-side
conductor back to the ECU pin it serves (through splices, one net at a time) and
checks, against sot/channels.csv:

  M1  a cavity used on one half is used on the other half too (no dead ends).
  M2  a signal crosses on the bulkhead of its own loom: an ECU pin whose SoT
      loom is A crosses on bulkhead A, loom B on bulkhead B.
  M3  screens stay in their own loom: a drain on bulkhead A reaches SHIELD_A
      (A7) only, a drain on bulkhead B reaches SHIELD_B (B17) only.
  M4  SHIELD_A and SHIELD_B are never joined anywhere in any drawing.
  M5  one cavity, one ECU signal: a cavity never reaches two different
      signal-class ECU pins.

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
SHIELD = {("ecu_a", "a7"): "A", ("ecu_b", "b17"): "B"}

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

# M2 / M3 / M5 - trace cabin halves back to ECU pins
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
                if SHIELD[k] != letter:
                    bad.append("M3 %s: %s %s drain reaches %s %s (SHIELD_%s) - bulkhead %s "
                               "screens go to SHIELD_%s only" % (loom, n[1], n[2], k[0], k[1],
                                                                 SHIELD[k], letter, letter))
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

# M4 - shields never bridged
for loom, g in graphs.items():
    a = ("ECU", "ecu_a", "a7")
    if a in g and ("ecu_b", "b17") in reach(g, a):
        bad.append("M4 %s: SHIELD_A (A7) and SHIELD_B (B17) are joined - never bridge them" % loom)

for line in bad:
    print(line)
print("\n%d mating finding(s)." % len(bad))
sys.exit(1 if bad else 0)
