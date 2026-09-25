"""Loom A and loom B get their own shield ground. Never bridged.

Daniel: "Loom B has its own shield ground at ECU B, correct? Don't bridge loom A
and loom B shield grounds."

sp_shield_cab fed BOTH ecu_a.a7 and ecu_b.b17 off one splice, which is exactly
the bridge he does not want - it puts the two ECU shield references in parallel
through the harness and makes a loop.

After this:

    sp_shield_a  -> ecu_a.a7    crank screen, cam screen, front VRC output screen
    sp_shield_b  -> ecu_b.b17   knock 1 screen, rear VRC output screen

Each screen goes to the splice for the ECU ITS OWN SIGNAL lands on:

    crank   Trig 1  A8   -> A
    cam     Trig 2  A9   -> A
    knock1  Knock 1 B9   -> B
    rear VRC  RL B20, RR B19 -> B
    front VRC FL A23, FR B21 -> A   (split across ECUs; FL/A23 chosen. One
                                     screen gets one termination and it cannot
                                     be both. Flip to B if you prefer.)

Nothing but drains touch either splice - audit_pin_names.py enforces that.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

A_SCREENS = {"w_shc_crank", "w_shc_cam"}          # in ST185-A-ECU
B_SCREENS = {"w_shc_knock1"}

p = os.path.join(R, "ST185-A-ECU.harness")
d = json.load(open(p, encoding="utf-8"))

sp = {s["id"]: s for s in d.get("splices", [])}
old = sp.get("sp_shield_cab")
if old is None:
    raise SystemExit("sp_shield_cab already gone - already split?")
base = old.get("schematicPosition", {"x": 1080, "y": 1628})

d["splices"] = [s for s in d["splices"] if s["id"] != "sp_shield_cab"]
for sid, dy in (("sp_shield_a", 0), ("sp_shield_b", 120)):
    pos = {"x": base["x"], "y": base["y"] + dy}
    d["splices"].append({"id": sid, "schematicPosition": dict(pos),
                         "layoutPosition": dict(pos)})
    print("+ splice %s" % sid)

for w in d["wires"]:
    for end in ("source", "target"):
        e = w.get(end)
        if not e or e.get("id") != "sp_shield_cab":
            continue
        if w["id"] == "w_drain_ecu_a" or w["id"] in A_SCREENS:
            e["id"] = "sp_shield_a"
        elif w["id"] == "w_drain_ecu_b" or w["id"] in B_SCREENS:
            e["id"] = "sp_shield_b"
        else:
            raise SystemExit("unassigned screen on sp_shield_cab: " + w["id"])
        print("  %-16s -> %s" % (w["id"], e["id"]))

json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# WheelSpeed points at the old splice through a cross-reference dummy.
# Front output -> A, rear output -> B.
p = os.path.join(R, "ST185-WheelSpeed.harness")
d = json.load(open(p, encoding="utf-8"))
NEW = {"cab_fout_sh": ("dm_sp_shield_a_Splice", "sp_shield_a",
                       "Front VRC output screen -> sp_shield_a -> ECU-A A7. "
                       "DRAIN ONLY. Front pair is FL A23 / FR B21; one screen "
                       "gets one termination and A is chosen for FL."),
       "cab_rout_sh": ("dm_sp_shield_b_Splice", "sp_shield_b",
                       "Rear VRC output screen -> sp_shield_b -> ECU-B B17. "
                       "DRAIN ONLY. Rear pair is RL B20 / RR B19, both ECU-B.")}

byid = {c["id"]: c for c in d["connectors"]}
oldm = byid.get("dm_sp_shield_cab_Splice")
for cb in d.get("cables", []):
    sh = cb.get("shield")
    if not sh or sh["id"] not in NEW:
        continue
    dm, real, text = NEW[sh["id"]]
    if dm not in byid:
        pos = (oldm or {}).get("schematicPosition", {"x": 0, "y": 0})
        pos = {"x": pos["x"], "y": pos["y"] + (0 if real.endswith("a") else 120)}
        c = {"id": dm, "label": "%s (wired on ST185-A-ECU)" % real, "width": 270,
             "schematicPosition": dict(pos), "layoutPosition": dict(pos),
             "cavities": [{"id": "c1", "signal": text}]}
        d["connectors"].append(c)
        byid[dm] = c
        print("+ %s" % dm)
    for end in ("source", "target"):
        e = sh.get(end)
        if e and e.get("id") == "dm_sp_shield_cab_Splice":
            e["id"] = dm
            print("  %-16s -> %s" % (sh["id"], dm))

d["connectors"] = [c for c in d["connectors"] if c["id"] != "dm_sp_shield_cab_Splice"]
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("- dm_sp_shield_cab_Splice")
