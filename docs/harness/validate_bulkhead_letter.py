"""ECU looms follow the ECU connector letter, and no harness is drawn inside another
(docs/RECONCILIATION-RULES.md Rule 3).

ECU connector A -> cabin A -> bulkhead A -> engine A; connector B the same. A pin's
letter is its conn column in sot/channels.csv. A device's letter is the set of
signal-class ECU pins its cavities reach through splices, bulkheads, inline interfaces
and broken-off pairs (rails, grounds and screens do not give a device a letter).

  L1  a conductor on an ECU pin is on the ECU loom file of that pin's letter
  L2  a conductor on a bulkhead cavity is on the file of that bulkhead's letter
  L3  a conductor on a device cavity with a letter is on that letter's file (a cavity
      with no letter of its own - a supply or ground - takes the device's letter, and
      is free when the device has both)
  L4  a bulkhead cavity only serves its own letter: on the cabin side it reaches
      signal ECU pins of that connector only, on the engine side every device it feeds
      has that letter
  L5  a sensor rail of one connector (+5V, +8V, Gnd Out) reaches the other letter's file
      only where crossover (a) allows it
  L6  a wire that runs between two harness files is drawn broken off in both: every
      registered break (interfaces.json "breaks") has one end on each of two files, each
      end is a Loose terminal with no part and exactly one conductor, and each end's note
      names the other file (ST185-<harness>). An unregistered br_ terminal, or any
      cross-reference dummy (cp_xref) left on any drawing, fails. Inline connector pairs
      are the other legal break; validate_interfaces I7 checks their pins pair up.
  L7  one element, one drawing: no connector, splice, resistor, diode or terminal id is
      drawn on two files (broken-off ends excepted - they are the pair)

The allow-list is the rule's crossovers and nothing else:
  (a) +5V (A32) splices at ECU A in the cabin; its B leg leaves A-cabin broken off and
      runs on B-cabin to the B cabin loads, and the B-engine sensor +5V crosses on
      bulkhead A rail pins and spurs into B-engine through IX_B_RAIL (Daniel,
      2026-09-28). A bulkhead cavity on that rail may feed the other letter's devices
      (L4). Sensor ground stays per letter (A24 / B22, no harness tie).
  (b) ETB: relay trigger A20, H-bridge supply B5 from that relay's output; the B18 / B26
      motor wires leave B-engine as a short broken-off spur after bulkhead B and come
      into A-engine just after bulkhead A, to the throttle body drawn there
  (c) APS pedal: A14 / B33; all pedal wiring is in the cabin and breaks off A-cabin and
      B-cabin into ST185-APS-Pedal
  (d) injector rail (F11) and COP rail (F10) cross on bulkhead B c1 / c2 (size-12
      contacts; bulkhead A has none) and spur into A-engine the same way as (b)
      (Daniel, 2026-09-28)

Exit 1 on any finding.
"""
import collections
import sys

import model

ECU_LOOMS = {"A-cabin": "A", "B-cabin": "B", "A-engine": "A", "B-engine": "B"}
BH_LETTER = {"bh_a_fw": "A", "bh_a_eng": "A", "bh_b_fw": "B", "bh_b_eng": "B"}
WALK = ("SP", "BH", "IX", "BRK")

ALLOW = {
    "a": {"nets": {"P5V", "GNDOUT"}},
    "b": {"conductors": {"w124_e_ae", "w215_e_ae"}},
    "c": {"harness": "APS-Pedal"},
    "d": {"cavities": {("bh_b_eng", "c1"), ("bh_b_eng", "c2")}},
}

reg = model.registry()
g = model.Graph(reg)
sot = {(r["conn"], r["pin"]): r for r in model.sot_rows() if r["owner"] == "ECU"}
bad = []

for m in sorted(set(ECU_LOOMS) - set(g.docs)):
    bad.append("L0 ECU loom %s is not registered in interfaces.json" % m)


def ecu_end(e):
    nid, h = e.get("id", ""), e.get("handle")
    return (nid, h) if nid in ("ecu_a", "ecu_b") else None


def bh_end(e):
    nid, h = e.get("id", ""), e.get("handle")
    return (nid, h) if nid in BH_LETTER else None


def letters(n):
    out = set()
    for m in g.reach(n, stop=lambda x: x[0] not in WALK):
        if m[0] == "ECU" and m[1] in ("ecu_a", "ecu_b"):
            r = sot.get((m[1], m[2]))
            if r and r["class"] == "signal":
                out.add(m[1][-1].upper())
    return out


cav_letter, dev_letter = {}, collections.defaultdict(set)
for n in list(g.adj):
    if n[0] == "C":
        cav_letter[(n[1], n[2])] = letters(n)
        dev_letter[n[1]] |= cav_letter[(n[1], n[2])]


def device_letter(loom, e):
    n = g.node(loom, e)
    if n[0] != "C":
        return None, None
    own = cav_letter.get((n[1], n[2])) or set()
    return n[1], (own or dev_letter.get(n[1]) or set())


# L1 - L3
for loom, L in ECU_LOOMS.items():
    d = g.docs.get(loom)
    if not d:
        continue
    for cond, cable, screen in model.conductors(d):
        ends = [cond.get("source") or {}, cond.get("target") or {}]
        for conn, pin in [ecu_end(e) for e in ends if ecu_end(e)]:
            if conn[-1].upper() != L:
                bad.append("L1 %s: %s lands on %s.%s but is drawn on a %s file" % (loom, cond["id"], conn, pin, L))
        for bh, cav in [bh_end(e) for e in ends if bh_end(e)]:
            if BH_LETTER[bh] != L:
                bad.append("L2 %s: %s lands on %s %s but is drawn on a %s file" % (loom, cond["id"], bh, cav, L))
        if cond["id"] in ALLOW["b"]["conductors"]:
            continue
        for e in ends:
            dev, S = device_letter(loom, e)
            if dev and S and L not in S:
                bad.append("L3 %s: %s wires %s.%s (letter %s) on a %s file"
                           % (loom, cond["id"], dev, e.get("handle"), "/".join(sorted(S)), L))

# L4
land = collections.defaultdict(list)
for loom, d in g.docs.items():
    for cond, cable, screen in model.conductors(d):
        s, t = cond.get("source") or {}, cond.get("target") or {}
        for a, b in ((s, t), (t, s)):
            k = bh_end(a)
            if k and b.get("id"):
                land[k].append((loom, b))
for (bh, cav), fars in sorted(land.items()):
    L = BH_LETTER[bh]
    if (bh, cav) in ALLOW["d"]["cavities"]:
        continue
    rail_cav = False
    if bh.endswith("_eng"):
        for loom0, _ in fars[:1]:
            bnode = g.node(loom0, {"id": bh, "handle": cav})
            for m in g.reach(bnode, stop=lambda x: x[0] not in ("SP", "BH", "BRK")):
                r = sot.get((m[1], m[2])) if m[0] == "ECU" else None
                if r and r["class"] == "rail" and r["net"] in ALLOW["a"]["nets"]:
                    rail_cav = True
    for loom, far in fars:
        start = g.node(loom, far)
        net = {start} | g.reach(start, stop=lambda x: x[0] not in ("SP", "BRK"))
        for m in net:
            if bh.endswith("_fw") and m[0] == "ECU" and m[1] in ("ecu_a", "ecu_b"):
                r = sot.get((m[1], m[2]))
                if r and r["class"] == "signal" and m[1][-1].upper() != L:
                    bad.append("L4 %s %s reaches %s.%s %s - bulkhead %s carries connector %s only"
                               % (bh, cav, m[1], m[2], r["net"], L, L))
            if bh.endswith("_eng") and m[0] == "C" and not rail_cav:
                S = cav_letter.get((m[1], m[2])) or dev_letter.get(m[1]) or set()
                if S and L not in S:
                    bad.append("L4 %s %s feeds %s.%s (letter %s) - it must cross on bulkhead %s"
                               % (bh, cav, m[1], m[2], "/".join(sorted(S)), "/".join(sorted(S))))

# L5
rails = {k: r for k, r in sot.items() if r["class"] == "rail"}
for loom, L in ECU_LOOMS.items():
    d = g.docs.get(loom)
    if not d:
        continue
    for cond, cable, screen in model.conductors(d):
        ends = [g.node(loom, e) for e in (cond.get("source") or {}, cond.get("target") or {}) if e.get("id")]
        net = set()
        for n in ends:
            net |= {n} | g.reach(n, stop=lambda x: x[0] not in ("SP", "BRK"))
        for m in net:
            if m[0] == "ECU" and (m[1], m[2]) in rails and m[1][-1].upper() != L:
                r = rails[(m[1], m[2])]
                if r["net"] not in ALLOW["a"]["nets"]:
                    bad.append("L5 %s: %s is on %s (%s.%s) - only +5V and Gnd Out cross letters"
                               % (loom, cond["id"], r["net"], m[1], m[2]))

# L6 - broken-off pairs
registered = set()
for br in reg.get("breaks", []):
    ends = br.get("ends", [])
    if len(ends) != 2 or ends[0]["harness"] == ends[1]["harness"]:
        bad.append("L6 break %s needs one end on each of two files" % br["id"])
        continue
    for me, other in ((ends[0], ends[1]), (ends[1], ends[0])):
        registered.add((me["harness"], me["terminal"]))
        d = g.docs.get(me["harness"]) or {}
        t = next((x for x in d.get("terminals", []) if x["id"] == me["terminal"]), None)
        if not t:
            bad.append("L6 break %s: the %s end (%s) is missing" % (br["id"], me["harness"], me["terminal"]))
            continue
        if t.get("type") != "Loose" or t.get("partId"):
            bad.append("L6 break %s: %s/%s must be a Loose terminal with no part" % (br["id"], me["harness"], t["id"]))
        n = sum(1 for c, _, _ in model.conductors(d)
                for e in (c.get("source") or {}, c.get("target") or {}) if e.get("id") == t["id"])
        if n != 1:
            bad.append("L6 break %s: %s/%s carries %d conductors, want 1" % (br["id"], me["harness"], t["id"], n))
        if ("ST185-%s" % other["harness"]) not in (t.get("signal") or ""):
            bad.append("L6 break %s: %s/%s note does not name ST185-%s"
                       % (br["id"], me["harness"], t["id"], other["harness"]))
for loom, d in g.docs.items():
    for t in d.get("terminals", []):
        if t["id"].startswith("br_") and (loom, t["id"]) not in registered:
            bad.append("L6 %s/%s is a broken-off end with no registered partner" % (loom, t["id"]))
    for c in d.get("connectors", []):
        if model.is_xref(c):
            bad.append("L6 %s/%s is a cross-reference dummy - draw the wire broken off in both files" % (loom, c["id"]))

# L7 - one element, one drawing
seen = collections.defaultdict(list)
for loom, d in g.docs.items():
    for k in ("connectors", "splices", "resistors", "diodes", "terminals"):
        for x in d.get(k, []):
            if (loom, x["id"]) in registered:
                continue
            seen[x["id"]].append(loom)
for eid, looms in sorted(seen.items()):
    if len(looms) > 1:
        bad.append("L7 %s is drawn on %s - draw it once and break the wires off the other file"
                   % (eid, ", ".join(looms)))

print("ECU letter looms checked: %s; broken-off pairs: %d"
      % (", ".join(k for k in ECU_LOOMS if k in g.docs), len(reg.get("breaks", []))))
for line in sorted(set(bad)):
    print(line)
print("\n%d bulkhead-letter finding(s)." % len(set(bad)))
sys.exit(1 if bad else 0)
