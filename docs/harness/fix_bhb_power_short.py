"""Get switched 12V off the two analog sensor pins it was shorted onto.

Found 2026-09-23 by audit_bh_collisions.py.  Bulkhead B c7 and c8 each carried
TWO unrelated circuits, because the A files and the B files both write to
bulkhead B and neither can see the other:

    bh_b c7   A files: ecu_b.b15  An Volt 6, oil pressure SIGNAL
              B files: sp_sw12    switched 12V, injector POWER
    bh_b c8   A files: ecu_b.b16  An Volt 7, fuel pressure SIGNAL
              B files: sp_sw12    switched 12V, COP POWER

That is battery voltage on two analog inputs the moment the key turns.  It would
take out An Volt 6 and 7 and put 12V down the oil and fuel pressure signal lines.

Daniel's call: power moves, signals stay.  Power belongs on the size 12 pins
anyway - c1 to c4 are size 12 (25 A, contact 0460-220-1231) and were spare.

    injector 12V  ->  bh_b c1
    COP 12V       ->  bh_b c2
    oil P signal  ->  bh_b c7   unchanged
    fuel P signal ->  bh_b c8   unchanged
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
MOVE = {"w_inj_pwr_c": ("bh_b_fw", "c7", "c1"),
        "w_cop_pwr_c": ("bh_b_fw", "c8", "c2"),
        "w_inj_pwr_e": ("bh_b_eng", "c7", "c1"),
        "w_cop_pwr_e": ("bh_b_eng", "c8", "c2")}
NAME = {"c1": "Switched 12V - INJECTOR power feed (size 12, 25A)",
        "c2": "Switched 12V - COP / ignition coil power feed (size 12, 25A)"}

for fn in ("ST185-B-ECU.harness", "ST185-B-engine.harness"):
    p = os.path.join(R, fn)
    d = json.load(open(p, encoding="utf-8"))
    hit = False
    for w in d.get("wires", []):
        if w["id"] not in MOVE:
            continue
        conn, old, new = MOVE[w["id"]]
        for end in ("source", "target"):
            e = w.get(end)
            if e and e.get("id") == conn and e.get("handle") == old:
                e["handle"] = new
                hit = True
                print("%-16s %-14s %s %s -> %s" % (fn[6:-8], w["id"], conn, old, new))
    if hit:
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# c1 and c2 now carry a contact, not a plug, on BOTH halves and in EVERY copy.
for fn in os.listdir(R):
    if not fn.endswith(".harness"):
        continue
    p = os.path.join(R, fn)
    d = json.load(open(p, encoding="utf-8"))
    hit = False
    for c in d.get("connectors", []):
        if c["id"] not in ("bh_b_fw", "bh_b_eng"):
            continue
        for cv in c.get("cavities", []):
            if cv["id"] not in NAME:
                continue
            cv["signal"] = NAME[cv["id"]]
            cv.pop("cavityPlugPartId", None)
            cv["contactPartId"] = "ct_hdp12p" if c["id"].endswith("_fw") else "ct_hdp12s"
            hit = True
    if hit:
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("cavities updated in", fn[6:-8])
