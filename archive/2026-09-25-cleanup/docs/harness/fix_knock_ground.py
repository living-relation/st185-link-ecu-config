"""Knock 1 SIG- off the shield ground and onto sensor ground.

Daniel, 2026-09-23: "No signals or power may flow over any shield ground ever!
Never! ... The knock sensor has to be connected to the knock input, and power or
ground out (however it works). Then, since it's shielded, the drain wire goes to
shield ground at the ECU."

He is right and I had it wrong.  w12_c ran knock 1's SIG- return from bulkhead A
c6 onto ECU-A A7, which is Shield/Gnd.  That is signal return current sitting on
the screen's only ground reference.

Verified before moving it - Link staff (Adamw), forums.linkecu.com topic 17263,
asked directly whether a knock sensor's second wire goes to sensor ground or
shield/ground on a G4X:

    "Either is fine. The 'Gnd Out' and 'Shield/Gnd' pins are both sensor ground."

So Gnd Out is an approved landing and there is no reason to keep the return on
the screen reference.  After this:

    knock1 c1  SIG+   -> bulkhead A c27 -> ECU-B B9  (Knock 1)
    knock1 c2  SIG-   -> bulkhead A c6  -> sp_gndout -> Gnd Out A24 / B22
    cable screen      -> bulkhead A c35 -> sp_shield_cab -> A7 / B17, drain only

sp_gndout lives in ST185-B-ECU today (it is moving to A-ECU in the Option C
pass); the wire is re-pointed at whichever file holds it.
"""
import json, os, glob

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

# where does sp_gndout live right now?
home = None
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    if any(s["id"] == "sp_gndout" for s in d.get("splices", [])):
        home = f
        break
if home is None:
    raise SystemExit("sp_gndout not found - has it been renamed?")
print("sp_gndout lives in", os.path.basename(home))

p = os.path.join(R, "ST185-A-ECU.harness")
d = json.load(open(p, encoding="utf-8"))
w = next((x for x in d["wires"] if x["id"] == "w12_c"), None)
if w is None:
    raise SystemExit("w12_c not found - already fixed?")

print("before  w12_c  %s.%s -> %s.%s" % (w["source"]["id"], w["source"]["handle"],
                                         w["target"]["id"], w["target"]["handle"]))

if os.path.basename(home) == "ST185-A-ECU.harness":
    target = {"id": "sp_gndout", "handle": "Splice"}
else:
    # cross-reference dummy, same convention as the rest of the build
    dm = "dm_sp_gndout_Splice"
    if not any(c["id"] == dm for c in d["connectors"]):
        d["connectors"].append({
            "id": dm, "label": "Sensor Gnd Out splice (wired on %s)"
                                % os.path.basename(home)[6:-8],
            "width": 270,
            "schematicPosition": {"x": 1380, "y": 300},
            "layoutPosition": {"x": 1380, "y": 300},
            "cavities": [{"id": "c1", "signal":
                          "Gnd Out sensor ground rail -> ECU-A A24 / ECU-B B22. "
                          "Knock 1 SIG- lands here, NOT on A7. A7 is shield "
                          "ground and carries drains only."}]})
        print("added   %s cross-reference" % dm)
    target = {"id": dm, "handle": "c1"}

# Set BOTH ends explicitly. The wire ran ecu_a.a7 <-> bh_a_fw.c6 and the ECU end
# is the one that moves; do not assume which of source/target held which.
w["source"] = {"id": "bh_a_fw", "handle": "c6"}
w["target"] = target
w["color"] = "Black"
w.pop("stripeColor", None)
print("after   w12_c  %s.%s -> %s.%s" % (w["source"]["id"], w["source"]["handle"],
                                         w["target"]["id"], w["target"]["handle"]))
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
