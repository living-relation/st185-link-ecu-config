"""Rebuild ST185-WheelSpeed from scratch.

The old file was wrong against Daniel's own rules in four ways:
  - wss_fr routed through bulkhead A pins 11/28, but 6.31 says no bulkhead for
    any wheel VR sensor
  - FL/FR outputs stopped at bulkhead dummies and never reached an ECU pin
  - the two VR conditioners were bare ring terminals, not the 6.30 enclosures
  - there were no cables at all, so no shields existed in the file

What this builds instead (6.30, 6.31, 6.35):

  wss_fl ---2c+shield--->|IN-L            |
                         |  FRONT VRC BOX |---4c+shield---> ECU (A23, B21)
  wss_fr ---2c+shield--->|IN-R        OUT |

  wss_rl ---2c+shield--->|IN-L            |
                         |  REAR VRC BOX  |---4c+shield---> ECU (B20, B19)
  wss_rr ---2c+shield--->|IN-R        OUT |

Shield path, end to end and grounded exactly once:

  sensor end FLOATS -> cable screen -> IN connector shell -> metal enclosure ->
  OUT connector shell -> cable screen -> cabin shield splice -> ECU shield gnd

That is why these are the only shelled connectors on the car (6.35). Everywhere
else 6.27 holds: cable-only screens, no shell, floating at the device.

TWO THINGS THAT WILL BITE ON THE BENCH IF FORGOTTEN:
  1. The enclosure must NOT touch chassis. It is part of the screen, not a
     ground. Mount it on nylon hardware.
  2. The PCB must NOT touch the enclosure. Nylon standoffs. The board grounds
     through the output cable, the shell carries the screen, and the two never
     meet.

No bulkhead connectors anywhere in this harness. The sensor cables pass the
firewall through a rubber grommet, which keeps each screen unbroken.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rebuild", "ST185-WheelSpeed.harness")

# ECU landings. From XTREMEX-IO-TABLE.html.
ECU = {
    "fl": ("dm_ecu_a_a23", "ECU-A A23", "DI 3 - Wheel Speed FL"),
    "fr": ("dm_ecu_b_b21", "ECU-B B21", "DI 4 - Wheel Speed FR"),
    "rl": ("dm_ecu_b_b20", "ECU-B B20", "DI 5 - Wheel Speed RL"),
    "rr": ("dm_ecu_b_b19", "ECU-B B19", "DI 6 - Wheel Speed RR"),
}

DUMMY_NOTE = "Dummy - real part on the owning drawing, 6.15"


def dummy(did, label):
    return {"id": did, "label": label, "width": 150,
            "cavities": [{"id": "c1", "designation": "1", "signal": DUMMY_NOTE}]}


def sensor(sid, label, note):
    return {"id": sid, "label": label, "width": 210, "partId": "cp_abs2",
            "cavities": [{"id": "c1", "designation": "1", "signal": "VR+ " + note},
                         {"id": "c2", "designation": "2", "signal": "VR- " + note}]}


def vrc_in(cid, label, wheel):
    """4-way female M8, shieldable. Two contacts used, two spare, screen on the
    shell. binder 86 6618 1121 00004."""
    return {"id": cid, "label": label, "width": 270, "partId": "cp_m8_4f",
            "shell": {"id": "shell", "signal": "Screen from %s, 360 deg to the enclosure" % wheel},
            "cavities": [
                {"id": "c1", "designation": "1", "signal": "VR+ in (%s)" % wheel},
                {"id": "c2", "designation": "2", "signal": "VR- in (%s)" % wheel},
                {"id": "c3", "designation": "3", "notConnected": True},
                {"id": "c4", "designation": "4", "notConnected": True}]}


def vrc_out(cid, label, left, right):
    """4-way male M8, shieldable. binder 86 6319 1121 00004."""
    return {"id": cid, "label": label, "width": 270, "partId": "cp_m8_4m",
            "shell": {"id": "shell", "signal": "Screen onward to the ECU shield ground"},
            "cavities": [
                {"id": "c1", "designation": "1", "signal": "+5V from ECU sensor supply"},
                {"id": "c2", "designation": "2", "signal": "Sensor ground"},
                {"id": "c3", "designation": "3", "signal": "Conditioned pulse out (%s)" % left},
                {"id": "c4", "designation": "4", "signal": "Conditioned pulse out (%s)" % right}]}


def sensor_cable(cid, wheel, sens, box_in):
    """Two twisted cores plus an overall screen. The screen lands on the box
    shell only - it FLOATS at the sensor (6.27), so it has no target."""
    return {"id": cid, "partId": "cab_2c_sh", "schematicPosition": {"x": 0, "y": 0},
            "cores": [
                {"id": cid + "_p", "color": "White", "twistedWithNext": True,
                 "source": {"id": sens, "handle": "c1"},
                 "target": {"id": box_in, "handle": "c1"}},
                {"id": cid + "_n", "color": "Green",
                 "source": {"id": sens, "handle": "c2"},
                 "target": {"id": box_in, "handle": "c2"}}],
            "shield": {"id": cid + "_sh", "color": "Shield",
                       "source": {"id": box_in, "handle": "shell"}}}


def out_cable(cid, box_out, left_key, right_key):
    """Four cores plus an overall screen. This screen DOES land at both ends -
    box shell to the cabin shield splice - because that is what makes the run
    continuous from sensor to ECU with a single ground point at the ECU."""
    l_id = ECU[left_key][0]
    r_id = ECU[right_key][0]
    return {"id": cid, "partId": "cab_4c_sh", "schematicPosition": {"x": 0, "y": 0},
            "cores": [
                {"id": cid + "_5v", "color": "Orange",
                 "source": {"id": "dm_sp_5v_Splice", "handle": "c1"},
                 "target": {"id": box_out, "handle": "c1"}},
                {"id": cid + "_gnd", "color": "Black",
                 "source": {"id": "dm_sp_gndout_Splice", "handle": "c1"},
                 "target": {"id": box_out, "handle": "c2"}},
                {"id": cid + "_l", "color": "Blue",
                 "source": {"id": box_out, "handle": "c3"},
                 "target": {"id": l_id, "handle": "c1"}},
                {"id": cid + "_r", "color": "Violet",
                 "source": {"id": box_out, "handle": "c4"},
                 "target": {"id": r_id, "handle": "c1"}}],
            "shield": {"id": cid + "_sh", "color": "Shield",
                       "source": {"id": box_out, "handle": "shell"},
                       "target": {"id": "dm_sp_shield_cab_Splice", "handle": "c1"}}}


doc = {
    "$schema": "https://docs.harness.design/files/harness/schema/v0.9.json",
    "version": 0.9,
    "lengthUnit": "mm",
    "connectors": [
        sensor("wss_fl", "ABS Wheel Speed FL", "(front left)"),
        sensor("wss_fr", "ABS Wheel Speed FR", "(front right)"),
        sensor("wss_rl", "ABS Wheel Speed RL", "(rear left)"),
        sensor("wss_rr", "ABS Wheel Speed RR", "(rear right)"),

        vrc_in("vrc_f_inl", "VRC Front - IN-L", "FL"),
        vrc_in("vrc_f_inr", "VRC Front - IN-R", "FR"),
        vrc_out("vrc_f_out", "VRC Front - OUT", "FL", "FR"),

        vrc_in("vrc_r_inl", "VRC Rear - IN-L", "RL"),
        vrc_in("vrc_r_inr", "VRC Rear - IN-R", "RR"),
        vrc_out("vrc_r_out", "VRC Rear - OUT", "RL", "RR"),

        dummy("dm_ecu_a_a23", "ECU-A-a23"),
        dummy("dm_ecu_b_b21", "ECU-B-b21"),
        dummy("dm_ecu_b_b20", "ECU-B-b20"),
        dummy("dm_ecu_b_b19", "ECU-B-b19"),
        dummy("dm_sp_5v_Splice", "sp_5v-Splice"),
        dummy("dm_sp_gndout_Splice", "sp_gndout-Splice"),
        dummy("dm_sp_shield_cab_Splice", "sp_shield_cab-Splice"),
    ],
    "wires": [],
    "cables": [
        sensor_cable("cab_fl", "FL", "wss_fl", "vrc_f_inl"),
        sensor_cable("cab_fr", "FR", "wss_fr", "vrc_f_inr"),
        sensor_cable("cab_rl", "RL", "wss_rl", "vrc_r_inl"),
        sensor_cable("cab_rr", "RR", "wss_rr", "vrc_r_inr"),
        out_cable("cab_fout", "vrc_f_out", "fl", "fr"),
        out_cable("cab_rout", "vrc_r_out", "rl", "rr"),
    ],
    "schematicNotes": [
        {"id": "n_scope", "width": 390, "schematicPosition": {"x": 0, "y": 0},
         "text": "WHEEL SPEED - STANDALONE HARNESS. No bulkhead connectors anywhere "
                 "in this drawing (6.31). Sensor cables cross the firewall through a "
                 "rubber grommet so each screen stays unbroken. Front pair rides the "
                 "fenders with loom C; rear pair rides with the fuel pump and level "
                 "sender."},
        {"id": "n_shield", "width": 390, "color": "Orange",
         "schematicPosition": {"x": 0, "y": 0},
         "text": "SHIELD, END TO END, GROUNDED ONCE (6.30). Sensor end floats. Screen "
                 "lands 360 deg on the IN connector shell, crosses the metal enclosure, "
                 "leaves on the OUT connector shell, and grounds only at the ECU shield "
                 "pin via the cabin shield splice."},
        {"id": "n_iso", "width": 390, "color": "Red",
         "schematicPosition": {"x": 0, "y": 0},
         "text": "TWO ISOLATION RULES. 1. The enclosure must not touch chassis - it is "
                 "part of the screen, not a ground. Nylon mounting hardware. 2. The PCB "
                 "must not touch the enclosure - nylon standoffs. The board grounds "
                 "through the output cable only. If either is bonded, the screen picks "
                 "up supply-ground noise and it will read as a flaky sensor."},
        {"id": "n_coat", "width": 390, "color": "Red",
         "schematicPosition": {"x": 0, "y": 0},
         "text": "MASK THE THREE CONNECTOR LANDINGS BEFORE POWDER COAT. The binder "
                 "shielding plate needs bare metal against the panel. A coated landing "
                 "silently breaks the screen."},
    ],
    "connectorParts": [
        {"id": "cp_abs2", "partNumber": "(OEM 2-way)", "manufacturer": "Toyota",
         "gender": "Female", "hasShell": False, "numberOfCavities": 2,
         "description": "OEM ST185 ABS wheel speed sensor connector. Two wires only - "
                        "the sensor has no shield pin, which is why the screen floats "
                        "at this end. Confirm the exact housing against the car before "
                        "ordering mates."},
        {"id": "cp_m8_4f", "partNumber": "86 6618 1121 00004", "manufacturer": "binder",
         "gender": "Female", "hasShell": True, "numberOfCavities": 4,
         "description": "M8 4-way female panel mount, shieldable, THT, IP67, M10x0.75 "
                        "front fastened. 4.0 A, 50 V AC / 60 V DC, -40 to +85 C. Screen "
                        "terminates on the shielding plate against the panel, so the "
                        "panel must be bare metal. VR conditioner enclosure inputs."},
        {"id": "cp_m8_4m", "partNumber": "86 6319 1121 00004", "manufacturer": "binder",
         "gender": "Male", "hasShell": True, "numberOfCavities": 4,
         "description": "M8 4-way male panel mount, shieldable, THT, IP67, front "
                        "fastened. Same ratings as the female. Male so a sensor lead "
                        "cannot be plugged into the output by mistake."},
    ],
    "cableParts": [
        {"id": "cab_2c_sh", "partNumber": "(generic)", "manufacturer": "generic",
         "description": "2-core twisted, overall foil + braid screen, 22 AWG. Sensor to "
                        "conditioner. Cable is generic in BOMs per 6.24.",
         "cores": [{"id": "k1", "color": "White"}, {"id": "k2", "color": "Green"}]},
        {"id": "cab_4c_sh", "partNumber": "(generic)", "manufacturer": "generic",
         "description": "4-core, overall foil + braid screen, 22 AWG. Conditioner to "
                        "ECU. Cable is generic in BOMs per 6.24.",
         "cores": [{"id": "k1", "color": "Orange"}, {"id": "k2", "color": "Black"},
                   {"id": "k3", "color": "Blue"}, {"id": "k4", "color": "Violet"}]},
    ],
}

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)

n_cores = sum(len(c["cores"]) + (1 if c.get("shield") else 0) for c in doc["cables"])
print("wrote %s" % OUT)
print("  connectors %d  cables %d  conductors %d"
      % (len(doc["connectors"]), len(doc["cables"]), n_cores))
