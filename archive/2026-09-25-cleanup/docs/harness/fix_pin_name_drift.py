#!/usr/bin/env python3
"""One bulkhead cavity, one name, in every drawing that draws either half.

Daniel, 2026-09-23: "Bh connector pins must be named exactly the same across a
mating pair. A cabin = A engine bay, B cabin = B engine bay. No pins should get
different names on any two mating connectors."

Six cavities drifted because two files described the same pin from their own
point of view. The screens are the clearest case: the cabin copy said
"terminates at the ECU" and the engine copy said "floats at the sensor". Both
are true and neither belongs in a cavity name - which end a screen terminates
at is a property of the screen, and it lives in docs/SHIELD-RULES.md and in
sot/channels.csv. The cavity gets the plain circuit name.

bh_b c14 drifted the other way: A-ECU and A-engine still called it "spare (size
16)" after the B files put the MRS enable on it.
"""
import json, pathlib

R = pathlib.Path(__file__).resolve().parent / "rebuild"

NAMES = {
    "bh_a_fw":  {"c33": "Crank VR screen", "c34": "Cam Hall screen"},
    "bh_a_eng": {"c33": "Crank VR screen", "c34": "Cam Hall screen"},
    "bh_b_fw":  {"c14": "MRS EPS pump logic enable (F13 7.5A, ignition-switched)"},
    "bh_b_eng": {"c14": "MRS EPS pump logic enable (F13 7.5A, ignition-switched)"},
}

for path in sorted(R.glob("*.harness")):
    d = json.loads(path.read_text(encoding="utf-8"))
    hits = []
    for c in d.get("connectors", []):
        want = NAMES.get(c["id"])
        if not want:
            continue
        for cav in c.get("cavities", []):
            new = want.get(cav["id"])
            if new and cav.get("signal") != new:
                hits.append("%s %s: %r -> %r" % (c["id"], cav["id"],
                                                 cav.get("signal"), new))
                cav["signal"] = new
    if hits:
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(path.name)
        for h in hits:
            print("   ", h)
