"""A bulkhead cavity must be wired on BOTH sides or neither.

bh_fw (ECU-cabin) and bh_eng (ECU-engine) are the two halves of one feedthrough.  If cavity 7
has a wire on the firewall side and nothing on the engine side, the circuit dead-ends
in the connector.  Added 2026-09-22 after fix_cavity_parts
turned up a 3-cavity and a 2-cavity mismatch.

A `dm_bh_<bulkhead>_<cavity>` dummy (EngineRoom-C draws the MRS pump's engine
halves this way) counts as that cavity. HARD gate since 2026-09-25.
"""
import json, glob, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model  # full_text: long label / signal text (full_text.json)

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
PAIRS = (("bh_fw", "bh_eng"),)

used = collections.defaultdict(set)
sig = {}
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = model.full_text(json.load(open(f, encoding="utf-8")), f)
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):          # ECU-engine runs bulkhead cavities
        conds += cb.get("cores", [])        # through cables, WheelSpeed is all
        if cb.get("shield"):                # cable - walking `wires` alone
            conds.append(cb["shield"])      # misses them
    for w in conds:
        for e in (w.get("source"), w.get("target")):
            if not e:
                continue
            nid = e["id"]
            if nid.startswith("dm_bh_"):
                # cross-reference dummy: dm_bh_eng_c36 in EngineRoom-C IS
                # bh_eng c36 - loom C draws the engine half on its own sheet
                bh, cav = nid[3:].rsplit("_", 1)
                used[bh].add(cav)
            else:
                used[nid].add(e.get("handle"))
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
sys.exit(1 if bad else 0)
