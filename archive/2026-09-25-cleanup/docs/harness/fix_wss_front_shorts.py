#!/usr/bin/env python3
"""Delete two leftover front wheel-speed runs that were shorting the VR
conditioner outputs at the ECU.

ECU A23 and B21 each had TWO conductors on them:

    A23   A-ECU w51_c  (bh_a_fw c10 -> A23)   and  WheelSpeed cab_fout_l
    B21   A-ECU w54_c  (bh_a_fw c12 -> B21)   and  WheelSpeed cab_fout_r

w51_c and w54_c are what is left of the old direct path, from before the
NCV1124 conditioner went in. Their engine halves (w51_e, w54_e) were already
retired into cab_fout_l / cab_fout_r when the conditioner arrived - the cabin
halves were simply never removed, so each front channel arrived at its ECU pin
twice: once as the conditioner's clean square wave, and once from a bulkhead
cavity whose other half is not wired to anything. Two outputs on one input.

Deleting them frees bh_a c10 and c12 on both halves.

What this does NOT do, and what is now visibly missing: the two FRONT wheel
sensors sit outside the cabin, so their raw VR pairs have to cross the firewall
to reach the conditioner, and no drawing shows that crossing. WheelSpeed runs
wss_fl and wss_fr straight into the conditioner inputs with no bulkhead at all.
That crossing needs pins - 3 cavities per channel, two cores and a screen - and
which bulkhead they land on is Daniel's call, because it turns on whether a raw
VR pair belongs to the ECU pin it eventually feeds (FL is A23 on loom A, FR is
B21 on loom B, so they would split across two bulkheads) or to the conditioner
that owns both of them (one bulkhead, both pairs together).
"""
import json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent / "rebuild"
DROP = {"w51_c", "w54_c"}
FREED = {("bh_a_fw", "c10"), ("bh_a_fw", "c12"),
         ("bh_a_eng", "c10"), ("bh_a_eng", "c12")}

for path in sorted(R.glob("*.harness")):
    d = json.loads(path.read_text(encoding="utf-8"))
    before = len(d.get("wires", []))
    d["wires"] = [w for w in d.get("wires", []) if w["id"] not in DROP]
    gone = before - len(d["wires"])
    touched = gone > 0
    for c in d.get("connectors", []):
        for cav in c.get("cavities", []):
            if (c["id"], cav["id"]) in FREED and cav.get("signal") != "spare":
                cav["signal"] = "spare"
                touched = True
    if touched:
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print("%-28s dropped %d wire(s)" % (path.name, gone))
