"""A bulkhead cavity must be wired on BOTH sides or neither.

bh_a_fw and bh_a_eng are the two halves of one feedthrough.  If cavity 7 has a
wire on the firewall side and nothing on the engine side, the circuit dead-ends
in the connector.  Same for bulkhead B.  Added 2026-09-22 after fix_cavity_parts
turned up a 3-cavity and a 2-cavity mismatch.
"""
import json, glob, os, collections

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
PAIRS = (("bh_a_fw", "bh_a_eng"), ("bh_b_fw", "bh_b_eng"))

used = collections.defaultdict(set)
sig = {}
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):          # A-engine runs 7 bulkhead cavities
        conds += cb.get("cores", [])        # through cables, WheelSpeed is all
        if cb.get("shield"):                # cable - walking `wires` alone
            conds.append(cb["shield"])      # misses them
    for w in conds:
        for e in (w.get("source"), w.get("target")):
            if e:
                used[e["id"]].add(e.get("handle"))
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            if cv.get("signal"):
                sig.setdefault((c["id"], cv["id"]), cv["signal"])

bad = 0
for a, b in PAIRS:
    for side, other in ((a, b), (b, a)):
        only = sorted(used[side] - used[other], key=lambda x: int(x[1:]))
        for cv in only:
            print("%-10s %-4s wired, %s %-4s is not   %s"
                  % (side, cv, other, cv, sig.get((side, cv), "")))
            bad += 1
print()
print("%d cavities wired on one side of a bulkhead only." % bad)
