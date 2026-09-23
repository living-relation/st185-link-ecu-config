"""Ambient temp sensor and A/C pressure switch into loom C, both to the A/C amp.

Daniel: "Ac switch is read by ac amp, not ECU. Scrap that path, move or include
it in loom c, to go to ac amp." and "Pull the ambient sensor diagram and add it
to loom c."

Verified against the ST185 Electrical Wiring Diagram (the factory book, same one
docs/electrical/ewd-snips came from).  Its parts-location list gives the auto
A/C sensor set, and every one of them feeds the A/C AMPLIFIER, not the ECU:

    A 1   A/C Ambient Temp. Sensor      engine compartment (behind front bumper)
    A 5   A/C Pressure SW               engine compartment
    A 23  A/C Room Temp. Sensor         cabin
    A 24  A/C Solar Sensor              cabin, on the dash top
    A 26  A/C Thermistor                evaporator
    A 27  A/C Water Temp. Sensor

A1 and A5 are the two that live in the engine bay, so they are loom C's to carry
to the cabin.  The A/C amplifier itself is a dash module and appears here as a
cross-reference dummy - the real connector is drawn on the cabin loom.

WHAT IS NOT KNOWN YET, and is marked TBD rather than invented:
  * the A/C amp pin numbers for either circuit
  * the sensor and switch connector part numbers
  * whether the pressure switch is 2-wire (dual) or 3-wire (trinary) on this car
Both need the A/C system CIRCUIT page.  The parts-location list names the
components but the circuit page is not in our snips yet.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
p = os.path.join(R, "ST185-EngineRoom-C.harness")
d = json.load(open(p, encoding="utf-8"))

TBD = ("Connector PN TBD - needs the A/C system circuit page. The parts-location "
       "list in the ST185 EWD names the component but not its connector.")

NEW_CONN = [
    {"id": "amb_temp", "label": "A/C Ambient Temp Sensor (EWD A1, behind front bumper)",
     "width": 270, "partId": "cp_amb_temp",
     "schematicPosition": {"x": 180, "y": 2400}, "layoutPosition": {"x": 180, "y": 2400},
     "cavities": [
         {"id": "c1", "designation": "1",
          "signal": "Ambient temp signal -> A/C amplifier. Thermistor, 2-wire. "
                    "NOT an ECU input - the ECU has no use for outside air temp."},
         {"id": "c2", "designation": "2",
          "signal": "Ambient temp sensor return -> A/C amplifier. The amp supplies "
                    "its own sensor ground; do NOT tie this to chassis or to Gnd Out."}]},
    {"id": "ac_press", "label": "A/C Pressure Switch (EWD A5, engine compartment)",
     "width": 270, "partId": "cp_ac_press",
     "schematicPosition": {"x": 180, "y": 2580}, "layoutPosition": {"x": 180, "y": 2580},
     "cavities": [
         {"id": "c1", "designation": "1", "signal": "A/C pressure switch -> A/C amplifier"},
         {"id": "c2", "designation": "2", "signal": "A/C pressure switch return -> A/C amplifier"},
         {"id": "c3", "designation": "3",
          "signal": "Third pole IF this is a trinary (hi/lo + fan). CONFIRM 2-wire "
                    "vs 3-wire from the A/C circuit page before crimping."}]},
    {"id": "dm_acamp", "label": "A/C Amplifier (dash module - wired on the cabin loom)",
     "width": 270,
     "schematicPosition": {"x": 900, "y": 2400}, "layoutPosition": {"x": 900, "y": 2400},
     "cavities": [
         {"id": "c1", "signal": "Ambient temp in - A/C AMP PIN TBD"},
         {"id": "c2", "signal": "Ambient temp return - A/C AMP PIN TBD"},
         {"id": "c3", "signal": "A/C pressure switch in - A/C AMP PIN TBD"},
         {"id": "c4", "signal": "A/C pressure switch return - A/C AMP PIN TBD"},
         {"id": "c5", "signal": "A/C pressure switch 3rd pole if fitted - A/C AMP PIN TBD"}]},
]

NEW_PARTS = [
    {"id": "cp_amb_temp", "partNumber": "TBD - ambient temp sensor connector",
     "manufacturer": "Toyota", "gender": "Female", "hasShell": False, "numberOfCavities": 2,
     "description": "2-way for the A/C ambient temp thermistor, EWD A1, mounted behind "
                    "the front bumper. " + TBD},
    {"id": "cp_ac_press", "partNumber": "TBD - A/C pressure switch connector",
     "manufacturer": "Toyota", "gender": "Female", "hasShell": False, "numberOfCavities": 3,
     "description": "A/C pressure switch, EWD A5, engine compartment. Drawn 3-way for a "
                    "trinary; drop to 2-way if the circuit page shows a dual switch. " + TBD},
]

NEW_WIRES = [
    ("w_amb_sig", "amb_temp", "c1", "dm_acamp", "c1", "Yellow"),
    ("w_amb_rtn", "amb_temp", "c2", "dm_acamp", "c2", "Yellow"),
    ("w_acp_1", "ac_press", "c1", "dm_acamp", "c3", "Blue"),
    ("w_acp_2", "ac_press", "c2", "dm_acamp", "c4", "Blue"),
    ("w_acp_3", "ac_press", "c3", "dm_acamp", "c5", "Blue"),
]

byid = {c["id"] for c in d["connectors"]}
for c in NEW_CONN:
    if c["id"] not in byid:
        d["connectors"].append(c)
        print("+ connector %s" % c["id"])
lib = {q["id"] for q in d.setdefault("connectorParts", [])}
for q in NEW_PARTS:
    if q["id"] not in lib:
        d["connectorParts"].append(q)
        print("+ part %s" % q["id"])
have = {w["id"] for w in d["wires"]}
for wid, sc, sh, tc, th, col in NEW_WIRES:
    if wid not in have:
        d["wires"].append({"id": wid, "color": col,
                           "source": {"id": sc, "handle": sh},
                           "target": {"id": tc, "handle": th}})
        print("+ wire %-12s %s.%s -> %s.%s" % (wid, sc, sh, tc, th))

note = ("A/C IS THE A/C AMPLIFIER'S, NOT THE ECU'S\n"
        "Verified in the ST185 factory EWD parts-location list. The auto A/C\n"
        "sensor set all feeds the A/C amplifier:\n"
        "  A 1  Ambient Temp Sensor    engine bay, behind the front bumper  <- loom C\n"
        "  A 5  A/C Pressure Switch    engine bay                           <- loom C\n"
        "  A 23 Room Temp Sensor       cabin\n"
        "  A 24 Solar Sensor           cabin, dash top\n"
        "  A 26 Thermistor             evaporator\n"
        "  A 27 Water Temp Sensor\n"
        "The ECU sees none of these. Its only A/C tie is Aux 4 / A18, the A/C\n"
        "kill output into the amp.\n"
        "OPEN: A/C amp pin numbers, both connector part numbers, and whether the\n"
        "pressure switch is 2-wire or 3-wire. All need the A/C system CIRCUIT\n"
        "page - the parts-location list names the parts but not the wiring.")
notes = d.setdefault("schematicNotes", [])
if not any("A/C IS THE A/C AMPLIFIER" in (n.get("text") or "") for n in notes):
    notes.append({"id": "note_acamp", "text": note,
                  "schematicPosition": {"x": 180, "y": 2760}})
    print("+ schematic note")

json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
