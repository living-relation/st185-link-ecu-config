"""Prove the rebuilt looms carry the same connections as the live files.

Compares every wire endpoint before and after the rebuild. Dummy blocks are
resolved back to the real node and pin they stand in for, so a net that now
spans two files still compares equal to the single wire it came from.

    python docs/harness/verify_rebuild.py

Exit 0 and "MATCH" means every connection survived. Anything else is printed
with the wire id so it can be chased.
"""
import json, io, os, sys

R = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, "rebuild")

LIVE = ["ST185-Signal.harness", "ST185-Power.harness",
        "ST185-CAN.harness", "ST185-EngineRoom-C.harness"]

# ClusterLED is a new loom migrated from CLUSTER-LED-DIAGRAM.html, not derived
# from any live .harness file, so it has no "before" to compare against.
SKIP = ("ClusterLED",)


def rebuilt_files():
    return sorted(f for f in os.listdir(OUT) if not any(s in f for s in SKIP))

# Differences the rebuild is supposed to introduce. Anything outside this list
# is a real fault.
EXPECT_GONE = {
    "w_mrs_relay_req": "deleted per 6.16 - the pump does not switch its own relay",
    "w23": "renamed w_cam_pullup_8v and rewired to bridge 8V to the signal",
    "w20_e": "renamed w_cam_pullup_sig and rewired to the ECU side",
    "w20_c": "deleted - duplicate cam path to a9; the signal runs on pin 29",
    "w_rlp": "RADLOK copy renamed w_rl_pos; the id collided with wheel speed",
}
EXPECT_NEW = {
    "w_eps_trig": "6.16 ECU-driven EPS relay trigger, Ign 6 / ecu_b.b12",
    "w_rl_pos": "RADLOK positive pair, renamed out of the w_rlp collision",
    "w_cam_pullup_8v": "cam pull-up, ECU 8V a6 to resistor",
    "w_cam_pullup_sig": "cam pull-up, resistor to Trigger 2 a9",
}


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def endpoints(doc, resolve=None):
    out = {}
    for w in doc.get("wires", []):
        pair = []
        for side in ("source", "target"):
            e = w.get(side) or {}
            nid, pin = e.get("id"), e.get("handle")
            if resolve and nid in resolve:
                nid, pin = resolve[nid]
            pair.append("%s.%s" % (nid, pin))
        out[w.get("id")] = frozenset(pair)
    return out


def main():
    if not os.path.isdir(OUT):
        print("no rebuild/ directory - run rebuild_looms.py --write first")
        return 1

    before = {}
    node_ids = set()
    for fn in LIVE:
        d = load(os.path.join(R, fn))
        # Same w_rlp collision the rebuild fixes - apply it here too, or this
        # comparison silently drops one of the two wires exactly as the repo did.
        if fn == "ST185-EngineRoom-C.harness":
            for w in d.get("wires", []):
                if w.get("id") == "w_rlp":
                    w["id"] = "w_rl_pos"
        before.update(endpoints(d))
        for key in ("connectors", "splices", "terminals", "resistors",
                    "diodes", "branchPoints", "groups"):
            node_ids |= {e.get("id") for e in d.get(key, [])}

    # Map every dummy block back to the real node and pin it represents.
    resolve = {}
    for fn in rebuilt_files():
        d = load(os.path.join(OUT, fn))
        for c in d.get("connectors", []):
            cid = c.get("id", "")
            if not cid.startswith("dm_"):
                continue
            rest = cid[3:]
            hit = None
            for n in node_ids:                 # longest match wins - ids contain _
                if rest.startswith(n + "_") and (hit is None or len(n) > len(hit)):
                    hit = n
            if hit:
                resolve[cid] = (hit, rest[len(hit) + 1:])
            else:
                print("  ! could not resolve dummy", cid)

    after = {}
    for fn in rebuilt_files():
        after.update(endpoints(load(os.path.join(OUT, fn)), resolve))

    gone = set(before) - set(after)
    new = set(after) - set(before)
    changed = {w for w in set(before) & set(after) if before[w] != after[w]}

    ok = True
    print("wires before %d   after %d" % (len(before), len(after)))
    print("-" * 64)
    for w in sorted(gone):
        if w in EXPECT_GONE:
            print("  expected gone  %-20s %s" % (w, EXPECT_GONE[w]))
        else:
            ok = False
            print("  LOST           %-20s %s" % (w, sorted(before[w])))
    for w in sorted(new):
        if w in EXPECT_NEW:
            print("  expected new   %-20s %s" % (w, EXPECT_NEW[w]))
        else:
            ok = False
            print("  UNEXPECTED     %-20s %s" % (w, sorted(after[w])))
    for w in sorted(changed):
        ok = False
        print("  CHANGED        %-20s" % w)
        print("      was %s" % sorted(before[w]))
        print("      now %s" % sorted(after[w]))
    print("-" * 64)
    print("MATCH - every connection survived" if ok
          else "MISMATCH - see the lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
