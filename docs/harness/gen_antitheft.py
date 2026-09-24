"""SUPERSEDED 2026-09-24 - do not rerun. rebuild/ST185-AntiTheft.harness is now
the finished DT-housing version edited in harness.design (mEnr); running this
would put the old TBD housings back.

A simple, generic aftermarket alarm harness - example only.

Daniel: "make a simple harness diagram for a generic anti theft device or use
one of the items you listed for me as an example."

Modelled on a basic one-way alarm of the Viper 3105V / Avital 3100LX class.
Every housing is marked TBD on purpose - the point of this drawing is the
FUNCTIONS and how they land on our build, not a committed part choice.  Swap in
the real housings once a module is bought.

How it ties into what we have:

  * The alarm does NOT cut the starter with its own relay.  Our starter is
    switched by k_str on the Link's Aux 8 / A26.  The alarm's ground-when-armed
    output drives a G4X DIGITAL INPUT instead, and the G4X anti-theft function
    does the fuel and ignition cut.  Link's own spec sheet lists this:
    "Anti-Theft control through digital inputs, over CAN or both".
    One less relay, and the cut happens inside the ECU where it cannot be
    hot-wired around.
  * The alarm keeps the door / hood / trunk pin switches and the siren.  Those
    are its job, not the ECU's.
  * NO RELAY OR FUSE IN THE ENGINE BAY.  The siren lives in the bay but its
    relay-free +12V output comes from the cabin block.
  * A shock/tilt sensor replaces the OEM glass-break sensor that used to sit
    under the driver's seat.  Modern shock sensors cover glass break and do not
    false-trigger on thunder.

Written 2026-09-22.  Folds into ST185-CabinAccessory in the Option C pass.
"""
import json, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "rebuild", "ST185-AntiTheft.harness")

G = 30  # layout grid


def P(col, row):
    return {"x": col * G, "y": row * G}


MAIN = [
    ("c1", "1", "+12V CONSTANT - from cabin fuse block, 5A. Alarm must stay live with the key off."),
    ("c2", "2", "GROUND - cabin chassis stud, same stud as the rest of the accessory loom"),
    ("c3", "3", "IGNITION SENSE - +12V key-on, tells the alarm the car is running"),
    ("c4", "4", "SIREN + - switched +12V out, 2A. Siren is in the bay, this feed comes from the cabin."),
    ("c5", "5", "PARKING LIGHT OUT - flashes the park lamps on trigger. Drive the OEM circuit through a relay in the CABIN block, not a bay relay."),
    ("c6", "6", "DOOR TRIGGER IN - negative. OEM door courtesy switches."),
    ("c7", "7", "HOOD PIN IN - negative"),
    ("c8", "8", "TRUNK PIN IN - negative"),
    ("c9", "9", "IMMOBILISER OUT - grounds when armed. Goes to a G4X DIGITAL INPUT, not a starter-kill relay. The ECU does the fuel and ignition cut."),
    ("c10", "10", "STATUS LED +"),
    ("c11", "11", "VALET / PROGRAM SWITCH"),
    ("c12", "12", "SHOCK SENSOR TRIGGER IN - negative, from the sensor's signal pin"),
]

doc = {
    "$schema": "https://docs.harness.design/files/harness/schema/v0.9.json",
    "$docs": "https://docs.harness.design/files/harness/editing-guide.md",
    "version": 0.9,
    "lengthUnit": "mm",
    "connectors": [
        {"id": "alarm", "label": "Alarm module - main harness (generic, 12-way)",
         "width": 270, "partId": "cp_alarm_main",
         "schematicPosition": P(14, 2), "layoutPosition": P(14, 2),
         "cavities": [{"id": i, "designation": g, "signal": s} for i, g, s in MAIN]},

        {"id": "shock", "label": "Shock / tilt sensor (replaces the OEM glass-break sensor)",
         "width": 270, "partId": "cp_alarm_shock",
         "schematicPosition": P(26, 14), "layoutPosition": P(26, 14),
         "cavities": [
             {"id": "c1", "designation": "1", "signal": "+12V from alarm module"},
             {"id": "c2", "designation": "2", "signal": "Ground"},
             {"id": "c3", "designation": "3", "signal": "Trigger out - negative pulse on impact"}]},

        {"id": "siren", "label": "Siren (engine bay)", "width": 210,
         "partId": "cp_alarm_2w",
         "schematicPosition": P(26, 4), "layoutPosition": P(26, 4),
         "cavities": [
             {"id": "c1", "designation": "1", "signal": "+12V switched from alarm c4"},
             {"id": "c2", "designation": "2", "signal": "Ground - bay chassis stud"}]},

        {"id": "led_sts", "label": "Status LED (dash)", "width": 210,
         "partId": "cp_alarm_2w",
         "schematicPosition": P(26, 8), "layoutPosition": P(26, 8),
         "cavities": [
             {"id": "c1", "designation": "1", "signal": "LED anode, from alarm c10"},
             {"id": "c2", "designation": "2", "signal": "LED cathode to ground. Current limiting: CONFIRM whether the module limits internally."}]},

        {"id": "valet", "label": "Valet / program switch (hidden)", "width": 210,
         "partId": "cp_alarm_2w",
         "schematicPosition": P(26, 11), "layoutPosition": P(26, 11),
         "cavities": [
             {"id": "c1", "designation": "1", "signal": "Switch, from alarm c11"},
             {"id": "c2", "designation": "2", "signal": "Ground"}]},

        {"id": "dm_ecu_di", "label": "G4X spare DIGITAL INPUT - channel TBD",
         "width": 270, "partId": None,
         "schematicPosition": P(2, 16), "layoutPosition": P(2, 16),
         "cavities": [{"id": "c1", "signal": "G4X Anti-Theft input. Link spec: 'Anti-Theft control through digital inputs, over CAN or both'. DI accepts a ground-switched input directly - enable the 4k7 pull-up. Pick the channel from the IO table."}]},
    ],

    "splices": [
        {"id": "sp_at_gnd", "schematicPosition": P(20, 18), "layoutPosition": P(20, 18)},
    ],

    "terminals": [
        {"id": "t_at_12v", "type": "Loose", "width": 270,
         "signal": "+12V CONSTANT, 5A from the cabin fuse block. NOT the engine bay.",
         "schematicPosition": P(2, 2), "layoutPosition": P(2, 2)},
        {"id": "t_at_ig", "type": "Loose", "width": 270,
         "signal": "+12V IGNITION from the cabin fuse block",
         "schematicPosition": P(2, 5), "layoutPosition": P(2, 5)},
        {"id": "t_at_gnd", "type": "Ring", "width": 270,
         "signal": "Cabin chassis ground stud",
         "schematicPosition": P(20, 22), "layoutPosition": P(20, 22)},
        {"id": "t_at_door", "type": "Loose", "width": 270,
         "signal": "OEM door courtesy switches - negative when a door opens",
         "schematicPosition": P(2, 8), "layoutPosition": P(2, 8)},
        {"id": "t_at_hood", "type": "Loose", "width": 270,
         "signal": "Hood pin switch - ADD ONE, the car has no factory hood pin",
         "schematicPosition": P(2, 11), "layoutPosition": P(2, 11)},
        {"id": "t_at_trunk", "type": "Loose", "width": 270,
         "signal": "Trunk pin switch",
         "schematicPosition": P(2, 13), "layoutPosition": P(2, 13)},
        {"id": "t_at_park", "type": "Loose", "width": 270,
         "signal": "Park lamp flash - to a relay in the CABIN block, never a bay relay",
         "schematicPosition": P(26, 1), "layoutPosition": P(26, 1)},
    ],

    "wires": [
        w for w in [
            {"id": "w_at_12v", "color": "Red", "source": {"id": "t_at_12v", "handle": "Terminal"}, "target": {"id": "alarm", "handle": "c1"}},
            {"id": "w_at_gnd", "color": "Black", "source": {"id": "alarm", "handle": "c2"}, "target": {"id": "sp_at_gnd", "handle": "Splice"}},
            {"id": "w_at_gnd_out", "color": "Black", "source": {"id": "sp_at_gnd", "handle": "Splice"}, "target": {"id": "t_at_gnd", "handle": "Terminal"}},
            {"id": "w_at_ig", "color": "Pink", "source": {"id": "t_at_ig", "handle": "Terminal"}, "target": {"id": "alarm", "handle": "c3"}},
            {"id": "w_at_siren", "color": "Brown", "source": {"id": "alarm", "handle": "c4"}, "target": {"id": "siren", "handle": "c1"}},
            {"id": "w_at_siren_g", "color": "Black", "source": {"id": "siren", "handle": "c2"}, "target": {"id": "sp_at_gnd", "handle": "Splice"}},
            {"id": "w_at_park", "color": "White", "source": {"id": "alarm", "handle": "c5"}, "target": {"id": "t_at_park", "handle": "Terminal"}},
            {"id": "w_at_door", "color": "Green", "source": {"id": "t_at_door", "handle": "Terminal"}, "target": {"id": "alarm", "handle": "c6"}},
            {"id": "w_at_hood", "color": "Green", "source": {"id": "t_at_hood", "handle": "Terminal"}, "target": {"id": "alarm", "handle": "c7"}},
            {"id": "w_at_trunk", "color": "Green", "source": {"id": "t_at_trunk", "handle": "Terminal"}, "target": {"id": "alarm", "handle": "c8"}},
            {"id": "w_at_immob", "color": "Violet", "source": {"id": "alarm", "handle": "c9"}, "target": {"id": "dm_ecu_di", "handle": "c1"}},
            {"id": "w_at_led", "color": "Orange", "source": {"id": "alarm", "handle": "c10"}, "target": {"id": "led_sts", "handle": "c1"}},
            {"id": "w_at_led_g", "color": "Black", "source": {"id": "led_sts", "handle": "c2"}, "target": {"id": "sp_at_gnd", "handle": "Splice"}},
            {"id": "w_at_valet", "color": "Gray", "source": {"id": "alarm", "handle": "c11"}, "target": {"id": "valet", "handle": "c1"}},
            {"id": "w_at_valet_g", "color": "Black", "source": {"id": "valet", "handle": "c2"}, "target": {"id": "sp_at_gnd", "handle": "Splice"}},
            {"id": "w_at_shk_sig", "color": "Blue", "source": {"id": "shock", "handle": "c3"}, "target": {"id": "alarm", "handle": "c12"}},
            {"id": "w_at_shk_12v", "color": "Red", "source": {"id": "alarm", "handle": "c1"}, "target": {"id": "shock", "handle": "c1"}},
            {"id": "w_at_shk_g", "color": "Black", "source": {"id": "shock", "handle": "c2"}, "target": {"id": "sp_at_gnd", "handle": "Splice"}},
        ]
    ],

    "connectorParts": [
        {"id": "cp_alarm_main", "partNumber": "TBD - alarm module main harness plug",
         "manufacturer": "TBD", "gender": "Female", "hasShell": False, "numberOfCavities": 12,
         "description": "12-way main harness plug on a basic one-way alarm module (Viper 3105V / Avital 3100LX class, ~$60-80). EXAMPLE ONLY - pin order and housing vary by module. Most come with a flying lead harness already terminated, in which case there is nothing to crimp and this becomes a splice list."},
        {"id": "cp_alarm_shock", "partNumber": "TBD - 3-way shock sensor plug",
         "manufacturer": "TBD", "gender": "Female", "hasShell": False, "numberOfCavities": 3,
         "description": "3-way plug for a dual-stage shock / tilt sensor (Directed 508D class, ~$30). Replaces the OEM glass-break sensor that lived under the driver's seat. Dual-stage gives a warning chirp on a light knock and full trigger on a real hit."},
        {"id": "cp_alarm_2w", "partNumber": "TBD - generic 2-way",
         "manufacturer": "TBD", "gender": "Female", "hasShell": False, "numberOfCavities": 2,
         "description": "Generic sealed 2-way for the siren, status LED and valet switch. Use DT06-2S for the siren (engine bay, needs the seal); the LED and valet switch are in the cabin and can be anything."},
    ],

    "schematicNotes": [
        {"id": "note_at_scope",
         "schematicPosition": P(2, 24),
         "text": "GENERIC ANTI-THEFT - EXAMPLE DRAWING\n"
                 "Housings are TBD on purpose. The point here is the functions and\n"
                 "how they land on our build, not a committed part choice.\n"
                 "Folds into ST185-CabinAccessory in the Option C restructure."},
        {"id": "note_at_immob",
         "schematicPosition": P(2, 28),
         "text": "THE ALARM DOES NOT CUT THE STARTER.\n"
                 "Our starter is switched by k_str on the Link's Aux 8 / A26. The\n"
                 "alarm's ground-when-armed output drives a G4X DIGITAL INPUT and the\n"
                 "ECU's own anti-theft function does the fuel and ignition cut.\n"
                 "Link XtremeX spec: 'Anti-Theft control through digital inputs,\n"
                 "over CAN or both'. One less relay, and the cut sits inside the ECU\n"
                 "where it cannot be hot-wired around.\n"
                 "DI accepts a ground-switched input directly - enable the 4k7 pull-up."},
        {"id": "note_at_bay",
         "schematicPosition": P(2, 34),
         "text": "NO RELAY OR FUSE IN THE ENGINE BAY.\n"
                 "The siren is in the bay but its feed comes from the cabin block.\n"
                 "The park-lamp flash output drives a relay in the CABIN block."},
    ],
}

json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("wrote", OUT)
print("%d connectors, %d wires, %d terminals" %
      (len(doc["connectors"]), len(doc["wires"]), len(doc["terminals"])))
