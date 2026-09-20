"""Bulkhead A and B occupancy, and what the shield pass will cost.

Plan 6.3 rule 1 and 6.27 rule 5: every shield gets its OWN bulkhead pin, passing
through the connector rather than landing on its shell. Today they share one pin
after a splice. This counts what is used, what is free, and whether the shields fit.

    python docs/harness/bulkhead_pins.py
"""
import json, io, os, collections

R = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(R, "rebuild")
CAP = {"bh_a_fw": 47, "bh_a_eng": 47, "bh_b_fw": 21, "bh_b_eng": 21}
SHIELDED = ["crank", "cam", "knock1", "wss_fl", "wss_fr", "wss_rl", "wss_rr"]


def main():
    used = collections.defaultdict(set)
    declared = {}
    for fn in sorted(os.listdir(SRC)):
        d = json.load(io.open(os.path.join(SRC, fn), encoding="utf-8"))
        for c in d.get("connectors", []):
            if c.get("id") in CAP:
                declared[c["id"]] = len(c.get("cavities", []))
        for w in d.get("wires", []):
            for side in ("source", "target"):
                e = w.get(side) or {}
                if e.get("id") in CAP:
                    used[e["id"]].add(e.get("handle"))
        # dummies name the real pin they stand in for
        for c in d.get("connectors", []):
            cid = c.get("id", "")
            if not cid.startswith("dm_"):
                continue
            for real in CAP:
                if cid.startswith("dm_" + real + "_"):
                    used[real].add(cid[len("dm_" + real + "_"):])

    print("%-12s %5s %5s %5s   %s" % ("bulkhead", "cap", "used", "free", "state"))
    print("-" * 62)
    free = {}
    for b in ("bh_a_fw", "bh_a_eng", "bh_b_fw", "bh_b_eng"):
        cap = CAP[b]
        u = len(used[b])
        free[b] = cap - u
        print("%-12s %5d %5d %5d   %d cavities drawn"
              % (b, cap, u, cap - u, declared.get(b, 0)))

    print()
    print("Shields needing their own pin: %d" % len(SHIELDED))
    for s in SHIELDED:
        print("   ", s)
    print()
    a_free = min(free["bh_a_fw"], free["bh_a_eng"])
    b_free = min(free["bh_b_fw"], free["bh_b_eng"])
    print("Usable pairs free:  bulkhead A %d   bulkhead B %d   total %d"
          % (a_free, b_free, a_free + b_free))
    need = len(SHIELDED)
    print("Shields need %d. %s" % (need, "FITS" if a_free + b_free >= need
                                   else "DOES NOT FIT"))
    print()
    print("A shield crossing needs a pin on BOTH halves of its bulkhead, so the")
    print("usable count is the smaller of the two halves - that is what is shown.")


if __name__ == "__main__":
    main()
