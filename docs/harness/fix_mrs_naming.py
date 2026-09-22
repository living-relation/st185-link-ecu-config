"""One device, not two: the MR-S EHPS pump.

k_eps, mrs_pwr, mrs_ctrl and mrs_en are four nodes belonging to ONE device - the
MR-S (ZZW30) electro-hydraulic power steering pump, with its control module bolted
to the pump and its relay mounted beside it in the bay. The old labels read like
"EPS" and "MRS" were separate things, and at least one summary table treated them
that way.

Names them consistently and adds the GroupPart that records the device. The
editing tools cannot create the Group itself - do that in the app and assign
gp_mrs_ehps to it.

Run from docs/harness:  python fix_mrs_naming.py
"""
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "rebuild", "ST185-EngineRoom-C.harness")

LABELS = {
    "k_eps":    u"MR-S EHPS pump relay (HCR150, engine bay)",
    "mrs_pwr":  u"MR-S EHPS pump - A, main power (90980-12068)",
    "mrs_ctrl": u"MR-S EHPS pump - B, signal (PN not yet identified)",
    "mrs_en":   u"MR-S EHPS pump - C, ignition (90980-10942)",
}

GROUP = {
    "id": "gp_mrs_ehps",
    "partNumber": u"MR-S ZZW30 EHPS pump",
    "manufacturer": u"Toyota",
    "description": (
        u"Electro-hydraulic power steering pump from the MR-S (ZZW30). One device, "
        u"mounted in the engine bay with its control module bolted to the pump. "
        u"Presents three connectors - A main power, B signal, C ignition - and is "
        u"switched by k_eps, an HCR150 mounted beside it. Group k_eps, mrs_pwr, "
        u"mrs_ctrl and mrs_en together and assign this part. See "
        u"docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md."),
}

HDR = (u"NEW ENGINE-ROOM LOADS - MR-S EHPS pump (one device: relay + 3 connectors) "
       u"and both uprated fans")

d = json.load(io.open(P, encoding="utf-8"))

for c in d.get("connectors", []):
    if c.get("id") in LABELS:
        c["label"] = LABELS[c["id"]]

gp = d.setdefault("groupParts", [])
if not any(p.get("id") == GROUP["id"] for p in gp):
    gp.append(dict(GROUP))

for n in d.get("schematicNotes", []):
    if n.get("id") == "shdr_3":
        n["text"] = HDR

with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("renamed 4 MR-S EHPS nodes and added gp_mrs_ehps")
