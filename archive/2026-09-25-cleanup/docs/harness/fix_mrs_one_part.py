"""One device, one part, ten labelled pins - no Group.

Daniel: "Why create a group? Just create a part with the correct number of total
pins (both used and not used) and give the pins specific labels so I know which
connector is which on EPS housing."

The MR-S (ZZW30) EHPS pump is one device with its controller bolted to it.  It
presents three plugs:

    A   90980-12068   2 pins   main power, 8 AWG
    B   90980-10897   6 pins   signal (pigtail 82998-12440, Sumitomo TS090 family)
    C   90980-10942   2 pins   ignition / enable

That is ten pins in total.  They are now one connector, mrs_eps, with the housing
letter in every designation and in every signal, so the drawing says which plug a
wire goes to without needing a Group - which the MCP tools cannot create anyway.

The relay k_eps stays separate: it is an HCR150 bolted beside the pump, not part
of the pump housing.

Contacts are not stamped.  A comes with the 8 AWG pigtail and B with 82998-12440;
both are on hand.  Written 2026-09-22.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
p = os.path.join(R, "ST185-EngineRoom-C.harness")
d = json.load(open(p, encoding="utf-8"))

PART = {
    "id": "cp_mrs_eps",
    "partNumber": "MR-S ZZW30 EHPS pump - A 90980-12068 / B 90980-10897 / C 90980-10942",
    "manufacturer": "Toyota / Sumitomo",
    "gender": "Female",
    "hasShell": False,
    "numberOfCavities": 10,
    "description": "Electro-hydraulic power steering pump from the MR-S (ZZW30), "
                   "controller bolted to the pump. THREE separate housings on the "
                   "device, drawn here as one 10-pin part so the pin labels say which "
                   "housing each wire lands in: A 90980-12068 2-way main power (8 AWG), "
                   "B 90980-10897 6-way signal (pigtail 82998-12440, Sumitomo TS090 "
                   "family), C 90980-10942 2-way ignition. All three on hand. Switched "
                   "by k_eps, an HCR150 mounted beside it - that is a separate part.",
}

CAV = [
    ("a1", "A-1", "[A 90980-12068 pin 1] +12V from k_eps 87, 8 AWG, passenger fender"),
    ("a2", "A-2", "[A 90980-12068 pin 2] GND, 8 AWG to engine block / EB"),
    ("b1", "B-1", "[B 90980-10897 pin 1] not used"),
    ("b2", "B-2", "[B 90980-10897 pin 2] SPD Out - speed-pulse output to ECU-A A27"),
    ("b3", "B-3", "[B 90980-10897 pin 3] not used"),
    ("b4", "B-4", "[B 90980-10897 pin 4] not used"),
    ("b5", "B-5", "[B 90980-10897 pin 5] not used"),
    ("b6", "B-6", "[B 90980-10897 pin 6] relay request out - NOT WIRED. 6.16 moved the "
                  "EPS relay trigger to the ECU (Ign 6 / ecu_b B12). Kept for reference."),
    ("c1", "C-1", "[C 90980-10942 pin 1] IG-switched, F13 7.5A - pump enable"),
    ("c2", "C-2", "[C 90980-10942 pin 2] not used"),
]

NEW = {
    "id": "mrs_eps",
    "label": "MR-S EHPS pump (A power / B signal / C ignition)",
    "width": 270,
    "partId": "cp_mrs_eps",
    "cavities": [{"id": i, "designation": g, "signal": s} for i, g, s in CAV],
}

# where each old node's cavity now lives
REMAP = {("mrs_pwr", "c1"): ("mrs_eps", "a1"),
         ("mrs_pwr", "c2"): ("mrs_eps", "a2"),
         ("mrs_ctrl", "c2"): ("mrs_eps", "b2"),
         ("mrs_en", "c1"): ("mrs_eps", "c1")}
OLD = {"mrs_pwr", "mrs_ctrl", "mrs_en"}

old = [c for c in d["connectors"] if c["id"] in OLD]
pos = old[0].get("layoutPosition") or {"x": 0, "y": 0}
NEW["layoutPosition"] = dict(pos)
NEW["schematicPosition"] = dict(old[0].get("schematicPosition") or pos)

d["connectors"] = [c for c in d["connectors"] if c["id"] not in OLD]
d["connectors"].append(NEW)
print("replaced %s with one 10-pin mrs_eps" % ", ".join(sorted(OLD)))

for w in d["wires"]:
    for end in ("source", "target"):
        e = w.get(end)
        if e and (e.get("id"), e.get("handle")) in REMAP:
            cid, cav = REMAP[(e["id"], e["handle"])]
            print("  %-16s %s.%s -> %s.%s" % (w["id"], e["id"], e["handle"], cid, cav))
            e["id"], e["handle"] = cid, cav

lib = d.setdefault("connectorParts", [])
lib = [q for q in lib if q["id"] not in ("cp_mrs_pwr", "cp_mrs_ctrl", "cp_mrs_en")]
if not any(q["id"] == PART["id"] for q in lib):
    lib.append(PART)
d["connectorParts"] = lib

# the Group part is what Daniel said not to bother with
before = len(d.get("groupParts", []))
d["groupParts"] = [g for g in d.get("groupParts", []) if g["id"] != "gp_mrs_ehps"]
if not d["groupParts"]:
    d.pop("groupParts", None)
if before:
    print("dropped groupPart gp_mrs_ehps - the part number and pin labels carry it now")

json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
