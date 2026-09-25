"""Add the part definitions the lint found dangling.

These ids were referenced but never defined, so the BOM would have silently
come up short and the upload would reject.
"""
import json

RES = [
    ("rp_1k8", "1.8k 1/4W", "Cam Hall pull-up, +8V (A6) to Trig 2 (A9)"),
    ("rp_470", "470R 1/4W", "Fuel level sender pull-up to +5V (A32)"),
    ("rp_10k", "10k 1/4W", "Cruise ladder pull-up to +5V (A32)"),
]

MRS_CTRL = {
    "id": "cp_mrs_ctrl",
    "partNumber": "90980-10897",
    "manufacturer": "Toyota",
    "gender": "Female",
    "hasShell": False,
    "numberOfCavities": 6,
    "description": (
        "MR-S EHPS pump control connector B, pigtail 82998-12440. "
        "Sumitomo TS090 / Yazaki 090-II family, not a TE part. "
        "6 cavities, 2 used: pin 2 speed-pulse out, pin 6 relay-request out. "
        "Confirm against the pump in hand before ordering."
    ),
}


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def save(p, d):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)


p = "rebuild/ST185-A-ECU.harness"
d = load(p)
d.setdefault("resistorParts", [])
have = {x["id"] for x in d["resistorParts"]}
for rid, pn, desc in RES:
    if rid not in have:
        d["resistorParts"].append({"id": rid, "partNumber": pn,
                                   "manufacturer": "generic",
                                   "description": desc})
save(p, d)

p = "rebuild/ST185-EngineRoom-C.harness"
d = load(p)
if not any(x["id"] == "cp_mrs_ctrl" for x in d["connectorParts"]):
    d["connectorParts"].append(MRS_CTRL)
save(p, d)

print("missing parts added")
