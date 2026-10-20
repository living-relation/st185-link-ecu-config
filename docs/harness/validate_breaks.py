"""Broken-off pairs and one element per drawing; the ECU harness owns the ECU and bulkhead wires.

Loom A and loom B are one harness since DECISIONS R220 (Dan 2026-10-19): ECU-cabin (ECU plugs A, B, C to
the cabin half of the DRB102 bulkhead) and ECU-engine (the engine half to the engine devices). The old
ECU-letter rule (A pins -> loom A files, B pins -> loom B files, crossovers a / b / c) is gone with it.

  E1  every conductor on an ECU plug A or B pin is drawn on ECU-cabin
  E2  every conductor on the bulkhead's cabin half (bh_fw) is on ECU-cabin, on its engine half (bh_eng)
      on ECU-engine
  L6  a wire that runs between two harness files is drawn broken off in both: every
      registered break (interfaces.json "breaks") has one end on each of two files, each
      end is a Loose terminal with no part and exactly one conductor, and each end's note
      names the other file (ST185-<harness>). An unregistered br_ terminal, or any
      cross-reference dummy (cp_xref) left on any drawing, fails. Inline connector pairs
      are the other legal break; validate_interfaces I7 checks their pins pair up.
  L7  one element, one drawing: no connector, splice, resistor, diode or terminal id is
      drawn on two files (broken-off ends excepted - they are the pair)

Exit 1 on any finding.
"""
import collections
import sys

import model

OWNER = {"ecu_a": "ECU-cabin", "ecu_b": "ECU-cabin", "bh_fw": "ECU-cabin", "bh_eng": "ECU-engine"}

reg = model.registry()
g = model.Graph(reg)
bad = []

for m in sorted(set(OWNER.values()) - set(g.docs)):
    bad.append("E0 ECU harness %s is not registered in interfaces.json" % m)

# E1 / E2
for loom, d in g.docs.items():
    for cond, cable, screen in model.conductors(d):
        for e in (cond.get("source") or {}, cond.get("target") or {}):
            own = OWNER.get(e.get("id", ""))
            if own and own != loom:
                bad.append("%s %s: %s lands on %s %s, which only %s wires" % (
                    "E2" if e["id"].startswith("bh_") else "E1", loom, cond["id"], e["id"], e.get("handle"), own))

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

print("ECU harness files: %s; broken-off pairs: %d"
      % (", ".join(sorted(set(OWNER.values()))), len(reg.get("breaks", []))))
for line in sorted(set(bad)):
    print(line)
print("\n%d break / ownership finding(s)." % len(set(bad)))
sys.exit(1 if bad else 0)
