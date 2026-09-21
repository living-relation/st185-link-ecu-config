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
    # w_rlp is NOT listed here: the id collided across files, and the verifier
    # applies the same rename to `before`, so both sides compare cleanly.
    # 6.12: shields are never connected at the device end. Every drain landing
    # on a device shell goes; the run to the ECU stays.
    "w_drain_crank": "device-end drain removed - shields float at the device",
    "w_drain_cam": "device-end drain removed - shields float at the device",
    "w_drain_knock1": "device-end drain removed - shields float at the device",
    "w_drain_wss_fl": "device-end drain removed - shields float at the device",
    "w_drain_wss_fr": "device-end drain removed - shields float at the device",
    "w_drain_wss_rl": "device-end drain removed - shields float at the device",
    "w_drain_wss_rr": "device-end drain removed - shields float at the device",

    # ---- wheel speed rebuilt as cables, 6.30 / 6.31 / 6.35 ----------------
    # Every one of these is replaced by a core of the same net in a shielded
    # cable. The right-hand column is the core that took it over, so this table
    # is the mapping, not an excuse.
    "w_flp":   "-> cab_fl_p    (wss_fl c1 to VRC Front IN-L c1)",
    "w50":     "-> cab_fl_n    (wss_fl c2 to VRC Front IN-L c2)",
    "w_frp_c": "-> cab_fr_p    (was wss_fr c1 via bulkhead A 28; 6.31 removes the bulkhead)",
    "w_frp_e": "-> cab_fr_p    (engine half of the same bulkhead hop, now one cable)",
    "w53_c":   "-> cab_fr_n    (was wss_fr c2 via bulkhead A 11; bulkhead removed)",
    "w53_e":   "-> cab_fr_n    (engine half of the same hop)",
    "w_rlp":   "-> cab_rl_p    (wss_rl c1 to VRC Rear IN-L c1)",
    "w58":     "-> cab_rl_n    (wss_rl c2 to VRC Rear IN-L c2)",
    "w_rrp":   "-> cab_rr_p    (wss_rr c1 to VRC Rear IN-R c1)",
    "w61":     "-> cab_rr_n    (wss_rr c2 to VRC Rear IN-R c2)",
    "w51_e":   "-> cab_fout_l  (FL output; previously DEAD-ENDED at a bulkhead dummy "
               "and never reached an ECU pin. Now lands ECU-A A23)",
    "w54_e":   "-> cab_fout_r  (FR output; same dead end, now lands ECU-B B21)",
    "w59":     "-> cab_rout_l  (RL output to ECU-B B20)",
    "w62":     "-> cab_rout_r  (RR output to ECU-B B19)",
    "w_vr1_5v_from_ecu5v": "-> cab_fout_5v  (supply MOVED from sp_5v_eng to the cabin "
                           "sp_5v - the box is in the cabin now)",
    "w_vr2_5v_from_ecu5v": "-> cab_rout_5v  (same move to cabin sp_5v)",
    "w56":     "-> cab_fout_gnd (ground MOVED from sp_gndout_eng to cabin sp_gndout)",
    "w64":     "-> cab_rout_gnd (same move to cabin sp_gndout)",
    "w_drain_rear": "-> cab_rout_sh (rear screen now runs inside the output cable to "
                    "the cabin shield splice)",
}
EXPECT_NEW = {
    "w_eps_trig": "6.16 ECU-driven EPS relay trigger, Ign 6 / ecu_b.b12",
    "w_rl_pos": "RADLOK positive pair, renamed out of the w_rlp collision",
    "w_cam_pullup_8v": "cam pull-up, ECU 8V a6 to resistor",
    "w_cam_pullup_sig": "cam pull-up, resistor to Trigger 2 a9",
    # 6.30 screens. These are genuinely new conductors, not renames - the old
    # file had no sensor-cable screen at all, only device-end drains that 6.27
    # deleted. Each lands on the conditioner box shell and FLOATS at the sensor,
    # which is why it has one endpoint.
    "cab_fl_sh": "FL sensor screen, floats at the sensor, 360 deg on VRC Front IN-L",
    "cab_fr_sh": "FR sensor screen, floats at the sensor, 360 deg on VRC Front IN-R",
    "cab_rl_sh": "RL sensor screen, floats at the sensor, 360 deg on VRC Rear IN-L",
    "cab_rr_sh": "RR sensor screen, floats at the sensor, 360 deg on VRC Rear IN-R",
    "cab_fout_sh": "front output screen, VRC Front OUT shell to the cabin shield "
                   "splice - the single ground point for the front pair",
}
# A connection that legitimately moved to a different pin.
EXPECT_CHANGED = {
    "w_mrs_e": "mrs_ctrl slot c1 -> c2, so the cavity matches the pin 2 it has "
               "always been labelled. Same net, same wire, corrected slot.",
}


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def endpoints(doc, resolve=None):
    """Every conductor in the document, keyed by id.

    Cable cores count. They carry real connections, and a verifier that only
    read `wires` would have called the whole wheel-speed rebuild a data loss
    while the replacement cores sat right there unexamined.
    """
    out = {}

    def add(cond):
        pair = []
        for side in ("source", "target"):
            e = cond.get(side) or {}
            nid, pin = e.get("id"), e.get("handle")
            if nid is None:
                continue          # a screen may legitimately land at one end
            if resolve and nid in resolve:
                nid, pin = resolve[nid]
            pair.append("%s.%s" % (nid, pin))
        out[cond.get("id")] = frozenset(pair)

    for w in doc.get("wires", []):
        add(w)
    for cb in doc.get("cables", []):
        for core in cb.get("cores", []):
            add(core)
        if cb.get("shield"):
            add(cb["shield"])
    for tw in doc.get("twistedWires", []):
        for w in tw.get("wires", []):
            add(w)
    return out


def replacement_of(reason):
    """EXPECT_GONE reasons of the form '-> cab_fl_p (...)' name the conductor
    that took the connection over. Pull the id back out so we can prove it
    actually exists."""
    reason = reason.strip()
    if not reason.startswith("->"):
        return None
    return reason[2:].strip().split()[0]


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

    # Conductors named as the replacement for a deleted wire are expected new.
    replacements = {}
    for w, reason in EXPECT_GONE.items():
        r = replacement_of(reason)
        if r:
            replacements.setdefault(r, []).append(w)

    ok = True
    print("conductors before %d   after %d" % (len(before), len(after)))
    print("-" * 64)
    for w in sorted(gone):
        if w in EXPECT_GONE:
            print("  expected gone  %-20s %s" % (w, EXPECT_GONE[w]))
            # Saying "replaced by X" is worthless if X is not there.
            r = replacement_of(EXPECT_GONE[w])
            if r and r not in after:
                ok = False
                print("      ! REPLACEMENT MISSING - %s does not exist" % r)
        else:
            ok = False
            print("  LOST           %-20s %s" % (w, sorted(before[w])))
    for w in sorted(new):
        if w in EXPECT_NEW:
            print("  expected new   %-20s %s" % (w, EXPECT_NEW[w]))
        elif w in replacements:
            print("  replaces       %-20s %s" % (w, ", ".join(sorted(replacements[w]))))
        else:
            ok = False
            print("  UNEXPECTED     %-20s %s" % (w, sorted(after[w])))
    # A wire that was MEANT to be deleted but is still there produces no diff at
    # all, so check for it explicitly - that is how the shield drains slipped
    # through the first time.
    for w in sorted(set(EXPECT_GONE) & set(after)):
        ok = False
        print("  STILL PRESENT   %-20s should have gone: %s"
              % (w, EXPECT_GONE[w]))
    for w in sorted(changed):
        if w in EXPECT_CHANGED:
            print("  expected move  %-20s %s" % (w, EXPECT_CHANGED[w]))
            continue
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
