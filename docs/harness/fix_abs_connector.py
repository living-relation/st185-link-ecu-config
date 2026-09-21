"""Replace the placeholder OEM ABS connector with real Deutsch DT parts.

Daniel: re-terminate the ABS sensors on DT/DTM, both ends.

DT over DTM for a wheel arch. DTM is smaller and takes 22 AWG, but these four
runs live behind the wheels in road spray and salt, and DT is the tougher shell
with the better seal. The cost of that choice is the wire gauge:

    DT size 16 contacts are 16-20 AWG. 22 AWG will not crimp reliably.

So the ABS sensor cable goes to 20 AWG, up from the 22 AWG in 6.30. Same lesson
as the AMPSEAL contacts in 6.37 - the contact decides the wire, not the other
way round.

Ends, following the usual Deutsch sensor convention:

    sensor pigtail  DT04-2P  receptacle, PIN contacts,    wedgelock W2P
    harness side    DT06-2S  plug,       SOCKET contacts, wedgelock W2S

The sensor is passive, so there is no live-pin argument either way; this is just
the convention, and keeping it means a DT sensor lead from anywhere else on the
car plugs straight in.
"""
import json, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
p = os.path.join(SRC, "ST185-WheelSpeed.harness")

with open(p, encoding="utf-8") as fh:
    d = json.load(fh)

# Harness-side connector on each sensor run.
for c in d["connectors"]:
    if c["id"].startswith("wss_"):
        c["partId"] = "cp_dt2s_abs"

d["connectorParts"] = [x for x in d["connectorParts"] if x["id"] != "cp_abs2"]
d["connectorParts"] += [
    {"id": "cp_dt2s_abs", "partNumber": "DT06-2S", "manufacturer": "Deutsch (TE)",
     "gender": "Female", "hasShell": False, "numberOfCavities": 2,
     "configurations": [{"id": "cfg", "lockPartId": "lp_w2s",
                         "contactPartId": "ct_dt16s"}],
     "description": "DT 2-way plug, harness side of the ABS wheel speed sensor. "
                    "Mates to DT04-2P on the sensor pigtail. Size 16 contacts, "
                    "16-20 AWG - the sensor cable is 20 AWG for this reason."},
    {"id": "cp_dt2p_abs", "partNumber": "DT04-2P", "manufacturer": "Deutsch (TE)",
     "gender": "Male", "hasShell": False, "numberOfCavities": 2,
     "configurations": [{"id": "cfg", "lockPartId": "lp_w2p",
                         "contactPartId": "ct_dt16p"}],
     "description": "DT 2-way receptacle, SENSOR side. Goes on the ABS sensor "
                    "pigtail when it is re-terminated. Not wired on this drawing - "
                    "listed so it reaches the buy list."},
    {"id": "lp_w2s", "partNumber": "W2S", "manufacturer": "Deutsch (TE)",
     "description": "Wedgelock for DT06-2S"},
    {"id": "lp_w2p", "partNumber": "W2P", "manufacturer": "Deutsch (TE)",
     "description": "Wedgelock for DT04-2P"},
]

d.setdefault("contactParts", [])
d["contactParts"] += [
    {"id": "ct_dt16s", "partNumber": "0462-201-16141", "manufacturer": "Deutsch (TE)",
     "gender": "Socket", "type": "Crimp",
     "maxGauge": {"unit": "AWG", "value": 16}, "minGauge": {"unit": "AWG", "value": 20},
     "description": "DT size 16 solid socket, 16-20 AWG. Harness side. Same contact "
                    "already used on the DT/DTM sensor connectors elsewhere."},
    {"id": "ct_dt16p", "partNumber": "0460-202-16141", "manufacturer": "Deutsch (TE)",
     "gender": "Pin", "type": "Crimp",
     "maxGauge": {"unit": "AWG", "value": 16}, "minGauge": {"unit": "AWG", "value": 20},
     "description": "DT size 16 solid pin, 16-20 AWG. Sensor pigtail side."},
]

# 6.30 said 22 AWG. The DT contact will not take it.
for cp in d.get("cableParts", []):
    if cp["id"] == "cab_2c_sh":
        cp["description"] = ("2-core twisted, overall foil + braid screen, 20 AWG. "
                             "Sensor to conditioner. 20 AWG NOT 22 - the DT size 16 "
                             "contact is 16-20 AWG and will not crimp 22 reliably. "
                             "Cable is generic in BOMs per 6.24.")

with open(p, "w", encoding="utf-8") as fh:
    json.dump(d, fh, indent=2)

print("ABS connectors -> DT06-2S harness side / DT04-2P sensor side")
print("cable bumped 22 -> 20 AWG to suit the DT size 16 contact")
