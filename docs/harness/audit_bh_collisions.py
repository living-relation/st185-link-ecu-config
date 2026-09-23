"""One bulkhead cavity, one circuit. Two different nets on one pin is a short.

Found 2026-09-23 while applying Daniel's rule "verify pin signal names against
the signal source, and the ECU pin it's assigned to".  Bulkhead B c7 and c8 each
had TWO unrelated circuits landing on them from different files - an analog
sensor signal from the A files and a switched 12V power feed from the B files.
Nobody noticed because no file sees both halves at once.

A cavity is over-subscribed when the conductors landing on it, on ONE half, do
not all belong to the same net.  Grouped by half so a legitimate mated pair
(cabin side + engine side of the same circuit) does not trip it.
"""
import json, glob, os, sys, collections

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
BH = {"bh_a_fw", "bh_a_eng", "bh_b_fw", "bh_b_eng"}

hits = collections.defaultdict(list)   # (bulkhead, cavity) -> [(loom, wire, other end)]
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    loom = os.path.basename(f)[6:-8]
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):
        conds += cb.get("cores", [])
        if cb.get("shield"):
            conds.append(cb["shield"])
    for w in conds:
        s, t = w.get("source"), w.get("target")
        for e, o in ((s, t), (t, s)):
            if e and e.get("id") in BH:
                hits[(e["id"], e.get("handle"))].append(
                    (loom, w["id"], "%s.%s" % (o.get("id"), o.get("handle"))
                     if o else "?"))

bad = 0
for (bh, cav), rows in sorted(hits.items(),
                              key=lambda kv: (kv[0][0], int(kv[0][1][1:]))):
    if len(rows) < 2:
        continue
    # more than one conductor on one half of a bulkhead = two circuits sharing a pin
    print("%s %s has %d conductors on the SAME half:" % (bh, cav, len(rows)))
    for loom, wid, other in rows:
        print("      %-13s %-16s -> %s" % (loom, wid, other))
    bad += 1
print()
print("%d over-subscribed bulkhead cavities." % bad)
sys.exit(1 if bad else 0)
