"""Clean-room build of ST185-A-cabin.harness (pilot, Dan's brief 2026-10-19).

One plain table, WIRES, says every wire: from (connector, pin) to (connector, pin), and what
the wire is for in plain words. The script writes that text as the cavity signal at BOTH ends
(propagate off), so every connector table reads like a pinout: pin | wire | description.

No wire joins another unless the table sends it to a real splice (SP-...). Wires that leave
this loom end at the REAL connector pin at the far end (relay socket, fuse box, ECU-B,
bulkhead), drawn whole with only our pins wired and the rest N/C (DECISIONS R10). Only four
wires end on a splice that sits in another loom; those end on a terminal named for that splice.

Inputs (read only):
  --geometry  pilot-4 A-cabin file (branch harness-views-cleanup): part definitions, the
              layout view (branch points, bundles, layout positions) and wire colours / parts.
  docs/harness/rebuild/ST185-{CabinPower,B-cabin,HeavyDC}.harness: the far-end connectors.
Pin facts: sot/channels.csv + docs/harness/DRB102-CAVITY-MAP.md + docs/harness/interfaces.json.

    python docs/harness/cleanroom/build_a_cabin.py --geometry p4.harness --out docs/harness/rebuild/ST185-A-cabin.harness
"""
import argparse
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout_schematic import POS, place  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REBUILD = os.path.join(HERE, "..", "rebuild")

# ---------------------------------------------------------------------------------------------
# Connectors. key -> (source file or None = geometry file, source id, label shown on the drawing)
# ---------------------------------------------------------------------------------------------
CONNECTORS = {
    "ecu_a":         (None, "ecu_a", "ECU-A  (Link G4X plug A, centre dash)"),
    "bh_a_fw":       (None, "bh_a_fw", "BULKHEAD  DRB102 receptacle (RH firewall)"),
    "aps":           (None, "aps", "PEDAL  accelerator pedal sensor (driver footwell)"),
    "ix_ws_front_p": (None, "ix_ws_front_p", "FRONT WS INLINE  to front VR conditioner (dash)"),
    "bus_5v_bha_p":  (None, "bus_5v_bha_p", "+5V BUS  DT06-8 plug (by bulkhead)"),
    "bus_5v_bha_r":  (None, "bus_5v_bha_r", "+5V BUS cap  DT04-8 bussed (on plug)"),
    "bus_gnd_bha_p": (None, "bus_gnd_bha_p", "SENSOR GND BUS  DT06-8 plug (by bulkhead)"),
    "bus_gnd_bha_r": (None, "bus_gnd_bha_r", "SENSOR GND BUS cap  DT04-8 bussed (on plug)"),
    "ecu_b":      ("ST185-B-cabin", "ecu_b", "ECU-B  (Link G4X plug B) - rest on ST185-B-cabin"),
    "k_efi":      ("ST185-CabinPower", "k_efi", "EFI MAIN RELAY  POWER box R2"),
    "k_str":      ("ST185-CabinPower", "k_str", "START RELAY  POWER box R3"),
    "k_fan":      ("ST185-CabinPower", "k_fan", "RAD FAN RELAY  POWER box R4"),
    "k_etb":      ("ST185-CabinPower", "k_etb", "ETB RELAY  LOGIC box M14"),
    "k_acc":      ("ST185-CabinPower", "k_acc", "A/C CLUTCH RELAY  LOGIC box M15"),
    "k_eps":      ("ST185-CabinPower", "k_eps", "EHPS PUMP RELAY  (glove box)"),
    "fb_logic":   ("ST185-CabinPower", "fb_logic", "LOGIC FUSE BOX  (glove box)"),
    "bus_sw12_p": ("ST185-CabinPower", "bus_sw12_p", "SW12 BUS  DT06-12 plug (glove box)"),
    "k_fp":       ("ST185-HeavyDC", "k_fp", "FUEL PUMP RELAY  K1 (trunk relay block)"),
}

# Ends that are not connectors. kind: splice / resistor / flying lead / ring / other-loom splice
SPLICES = {  # id -> label (all real splices named in the SoT / interfaces.json)
    "sp_5v": "Splice: +5 V sensor supply (ECU A32)",
    "sp_5v_2": "Splice: +5 V to pedal + cruise",
    "sp_8v": "Splice: +8 V cam sensor supply (ECU A6)",
    "sp_trig2": "Splice: cam signal + pull-up",
    "sp_gndout": "Splice: sensor ground (ECU A24)",
    "sp_sw12": "Splice: switched +12 V",
    "sp_chassis": "Splice: ECU power ground",
    "sp_shield_a": "Splice: loom A shield drains (ECU A7)",
}
TERMINALS = {  # id -> (geometry id to copy, label)
    "fl_acamp_act": ("fl_acamp_act", "Tap: A/C amp A18 pin 11 (ACT), factory G-Y wire"),
    "fl_ac_psw": ("fl_acamp_psw", "Tap: A/C pressure switch out, factory Y-R wire (A5 pin 4 to amp A18 pin 13)"),
    "chassis_ring": ("chassis_ring", "Ground ring M6, cabin chassis stud at ECU"),
    "x_sp_5v_b": ("br_w_rail_5v_b_c", "Joins splice SP-5V-B on ST185-B-cabin"),
    "x_sp_shield_b": ("br_cab_fspur_fr_sh", "Joins splice SP-SHIELD-B on ST185-B-cabin"),
    "x_r_cruise": ("br_w_cru_5v", "Joins cruise-switch ladder resistor on ST185-CSB3"),
    "x_sp_csb_gnd": ("br_w_csbg", "Joins CSB3 ground splice on ST185-CSB3"),
}

# ---------------------------------------------------------------------------------------------
# WIRES: id (kept from the old file so colour, gauge and ident bands carry over),
#        from (node, pin), to (node, pin), description.  pin None = splice / terminal / resistor.
# ---------------------------------------------------------------------------------------------
WIRES = [
    # ECU-A outputs and sensor signals straight to the bulkhead (DRB number = pin)
    ("w108_c", ("ecu_a", "A4"), ("bh_a_fw", "31"), "Injector 1 drive (-)"),
    ("w109_c", ("ecu_a", "A3"), ("bh_a_fw", "32"), "Injector 2 drive (-)"),
    ("w110_c", ("ecu_a", "A2"), ("bh_a_fw", "33"), "Injector 3 drive (-)"),
    ("w111_c", ("ecu_a", "A1"), ("bh_a_fw", "34"), "Injector 4 drive (-)"),
    ("w120_c", ("ecu_a", "A13"), ("bh_a_fw", "35"), "Coil 1 trigger (IGT)"),
    ("w121_c", ("ecu_a", "A12"), ("bh_a_fw", "36"), "Coil 2 trigger (IGT)"),
    ("w122_c", ("ecu_a", "A11"), ("bh_a_fw", "37"), "Coil 3 trigger (IGT)"),
    ("w123_c", ("ecu_a", "A10"), ("bh_a_fw", "38"), "Coil 4 trigger (IGT)"),
    ("w200_c", ("ecu_a", "A8"), ("bh_a_fw", "9"), "Crank sensor signal"),
    ("w16_c", ("ecu_a", "A30"), ("bh_a_fw", "17"), "Turbo speed sensor signal"),
    ("w48_c", ("ecu_a", "A31"), ("bh_a_fw", "21"), "Flex fuel sensor signal"),
    ("w128_c", ("ecu_a", "A22"), ("bh_a_fw", "24"), "Throttle position 1 (main)"),
    ("w129_c", ("ecu_a", "A33"), ("bh_a_fw", "25"), "Throttle position 2 (sub)"),
    ("w26_c", ("ecu_a", "A17"), ("bh_a_fw", "30"), "MAP sensor signal"),
    ("w103_c", ("ecu_a", "A21"), ("bh_a_fw", "39"), "Boost solenoid drive (-)"),
    ("w201_c", ("ecu_a", "A15"), ("bh_a_fw", "40"), "Coolant temp sensor signal"),
    ("w202_c", ("ecu_a", "A16"), ("bh_a_fw", "41"), "Intake air temp sensor signal"),
    ("w_mrs_c", ("ecu_a", "A27"), ("bh_a_fw", "44"), "EHPS pump speed signal"),
    # cam sensor: signal + 1.8k pull-up to +8 V meet at a real splice
    ("w_trig2_pin", ("ecu_a", "A9"), ("sp_trig2", None), "Cam sensor signal"),
    ("w_cam_sig_c", ("sp_trig2", None), ("bh_a_fw", "13"), "Cam sensor signal"),
    ("w_cam_pullup_sig", ("cam_pullup", "Right"), ("sp_trig2", None), "Cam signal pull-up"),
    ("w_cam_pullup_8v", ("sp_8v", None), ("cam_pullup", "Left"), "+8 V to cam pull-up"),
    ("w19", ("ecu_a", "A6"), ("sp_8v", None), "+8 V sensor supply"),
    ("w_rail_sp_8v_c", ("sp_8v", None), ("bh_a_fw", "12"), "+8 V to cam sensor"),
    # +5 V sensor supply (ECU A32)
    ("w67", ("ecu_a", "A32"), ("sp_5v", None), "+5 V sensor supply"),
    ("w_5v_bha_trunk", ("sp_5v", None), ("bus_5v_bha_p", "1"), "+5 V sensor supply"),
    ("w_rail_sp_5v_c", ("bus_5v_bha_p", "2"), ("bh_a_fw", "23"), "+5 V to throttle sensors"),
    ("w_5v_a_c39", ("bus_5v_bha_p", "3"), ("bh_a_fw", "28"), "+5 V to MAP sensor"),
    ("w_5v_a_c40", ("bus_5v_bha_p", "4"), ("bh_a_fw", "16"), "+5 V to turbo speed sensor"),
    ("w_5v_brail_c45", ("bus_5v_bha_p", "5"), ("bh_a_fw", "47"), "+5 V to oil pressure sensor"),
    ("w_5v_brail_c46", ("bus_5v_bha_p", "6"), ("bh_a_fw", "50"), "+5 V to fuel pressure sensor"),
    ("w_5v_brail_c47", ("bus_5v_bha_p", "7"), ("bh_a_fw", "51"), "+5 V to coolant pressure sensor"),
    ("w_5v_link", ("sp_5v", None), ("sp_5v_2", None), "+5 V to pedal + cruise"),
    ("w_rail_5v_b_c_ac", ("sp_5v", None), ("x_sp_5v_b", None), "+5 V to loom B sensors"),
    ("w_cru_5v_ac", ("sp_5v_2", None), ("x_r_cruise", None), "+5 V to cruise switch ladder"),
    # sensor ground (ECU A24)
    ("w68", ("ecu_a", "A24"), ("sp_gndout", None), "Sensor ground"),
    ("w_gnd_bha_trunk", ("sp_gndout", None), ("bus_gnd_bha_p", "1"), "Sensor ground"),
    ("w_rail_sp_gndout_c", ("bus_gnd_bha_p", "2"), ("bh_a_fw", "26"), "Sensor ground: IAT, throttle, coolant temp"),
    ("w_gnd_a_c41", ("bus_gnd_bha_p", "3"), ("bh_a_fw", "10"), "Sensor ground: crank"),
    ("w_gnd_a_c42", ("bus_gnd_bha_p", "4"), ("bh_a_fw", "14"), "Sensor ground: cam"),
    ("w_gnd_a_c43", ("bus_gnd_bha_p", "5"), ("bh_a_fw", "18"), "Sensor ground: turbo speed"),
    ("w_gnd_a_c44", ("bus_gnd_bha_p", "6"), ("bh_a_fw", "29"), "Sensor ground: flex fuel, MAP"),
    # switched +12 V
    ("w_fb_sw12", ("bus_sw12_p", "2"), ("sp_sw12", None), "Switched +12 V feed"),
    ("w78", ("sp_sw12", None), ("ecu_a", "A5"), "ECU main power +12 V"),
    ("w_rail_sp_sw12_c", ("sp_sw12", None), ("bh_a_fw", "20"), "Switched +12 V to boost solenoid, flex sensor"),
    ("w_rail_sw12_b_c_ac", ("sp_sw12", None), ("bh_a_fw", "90"), "Switched +12 V to gearbox speed sensor"),
    # fused feeds from the LOGIC box straight to the bulkhead
    ("w_inj_pwr_ac", ("fb_logic", "BUS2-4"), ("bh_a_fw", "1"), "Injector +12 V (fuse INJ 15 A)"),
    ("w_cop_pwr_ac", ("fb_logic", "BUS2-3"), ("bh_a_fw", "2"), "Ignition coil +12 V (fuse COP 15 A)"),
    ("w_fb_mrs_en", ("fb_logic", "BUS2-12"), ("bh_a_fw", "42"), "EHPS pump enable +12 V (fuse MRS 7.5 A)"),
    # ECU ground
    ("w70", ("ecu_a", "A25"), ("sp_chassis", None), "ECU power ground"),
    ("w_a34", ("ecu_a", "A34"), ("sp_chassis", None), "ECU power ground"),
    ("w_b25_ac", ("ecu_b", "B25"), ("sp_chassis", None), "ECU power ground"),
    ("w_b34_ac", ("ecu_b", "B34"), ("sp_chassis", None), "ECU power ground"),
    ("w_lamg_ac", ("bh_a_fw", "96"), ("sp_chassis", None), "CAN-Lambda ground"),
    ("w_csbg_ac", ("sp_chassis", None), ("x_sp_csb_gnd", None), "CSB3 + opto ground"),
    ("w66", ("sp_chassis", None), ("chassis_ring", None), "ECU ground to chassis"),
    # shield drains (one drain node, grounded only at ECU A7)
    ("w_drain_ecu_a", ("sp_shield_a", None), ("ecu_a", "A7"), "Shield drain"),
    ("w_shc_crank", ("bh_a_fw", "11"), ("sp_shield_a", None), "Crank sensor shield"),
    ("w_shc_cam", ("bh_a_fw", "15"), ("sp_shield_a", None), "Cam sensor shield"),
    ("w_shc_turbo", ("bh_a_fw", "19"), ("sp_shield_a", None), "Turbo speed sensor shield"),
    ("w_shc_flex", ("bh_a_fw", "22"), ("sp_shield_a", None), "Flex fuel sensor shield"),
    ("w_shc_etbs", ("bh_a_fw", "27"), ("sp_shield_a", None), "Throttle sensor shield"),
    # relay coils the ECU switches to ground
    ("w_fp85", ("ecu_a", "A19"), ("k_fp", "85"), "Fuel pump relay coil (-)"),
    ("w81", ("ecu_a", "A20"), ("k_etb", "85"), "ETB relay coil (-)"),
    ("w_str85", ("ecu_a", "A26"), ("k_str", "85"), "Start relay coil (-)"),
    ("w76", ("ecu_a", "A28"), ("k_efi", "85"), "EFI main relay coil (-)"),
    ("w_fan85", ("ecu_a", "A29"), ("k_fan", "85"), "Radiator fan relay coil (-)"),
    ("w_eps_rly", ("bh_a_fw", "56"), ("k_eps", "85"), "EHPS relay coil (-) from pump B5"),
    # A/C (R23 / S35): two point-to-point wires, no A/C splice in this loom
    ("w_ac_kill", ("ecu_a", "A18"), ("fl_acamp_act", None), "A/C compressor cancel"),
    ("w_acc86", ("fl_ac_psw", None), ("k_acc", "86"), "A/C clutch relay coil (+) via pressure switch"),
]

# Cable cores: (cable id, core id) -> (from, to, description). Same rules as WIRES.
CABLES = {
    "cab_aps": {
        "w_aps_vc1": (("aps", "4"), ("sp_5v_2", None), "+5 V to pedal sensor 1"),
        "w40": (("aps", "5"), ("sp_gndout", None), "Pedal sensor 1 ground"),
        "w38": (("aps", "6"), ("ecu_a", "A14"), "Pedal sensor 1 signal (main)"),
        "w210": (("aps", "1"), ("sp_5v_2", None), "+5 V to pedal sensor 2"),
        "w_aps_gnd2": (("aps", "2"), ("sp_gndout", None), "Pedal sensor 2 ground"),
        "w_aps_vpa2": (("aps", "3"), ("ecu_b", "B33"), "Pedal sensor 2 signal (sub)"),
        "cab_aps_sh": (None, ("sp_shield_a", None), "Pedal cable shield"),
    },
    "cab_fspur": {
        "cab_fspur_5v": (("ix_ws_front_p", "1"), ("sp_5v", None), "+5 V to front VR conditioner"),
        "cab_fspur_gnd": (("ix_ws_front_p", "2"), ("sp_gndout", None), "Front VR conditioner ground"),
        "cab_fspur_l": (("ix_ws_front_p", "3"), ("ecu_a", "A23"), "Front left wheel speed"),
        "cab_fspur_sh": (("ix_ws_front_p", "5"), ("sp_shield_a", None), "Front WS cable shield"),
    },
    "cab_fspur_fr_ac": {
        "cab_fspur_r_ac": (("ix_ws_front_p", "4"), ("ecu_b", "B21"), "Front right wheel speed"),
        "cab_fspur_fr_sh_ac": (None, ("x_sp_shield_b", None), "Front right WS shield"),
    },
}

# Old stub nodes in the layout view -> the real node that now sits there. None = drop the leg.
LAYOUT_SWAP = {
    "br_w76": "k_efi", "br_w_fp85": "k_fp", "br_w_fan85": "k_fan", "br_w81": "k_etb",
    "br_w_str85": "k_str", "br_w_acc86": "k_acc", "br_w_eps_rly": "k_eps",
    "br_w_fb_sw12": "bus_sw12_p", "br_w_fb_mrs_en": "fb_logic", "br_w_inj_pwr_c": None,
    "br_w_cop_pwr_c": None, "br_w39": None, "br_cab_fspur_r": None, "br_w_b25": None,
    "br_w_b34": None, "br_w_rail_sw12_b_c": None, "br_w_lamg_b": None,
    "br_w_rail_5v_b_c": "x_sp_5v_b", "br_cab_fspur_fr_sh": "x_sp_shield_b",
    "br_w_cru_5v": "x_r_cruise", "br_w_csbg": "x_sp_csb_gnd",
    "fl_acamp_psw": "fl_ac_psw", "fl_acamp_mg": None, "br_ac_mg": None, "br_ac_psw": None,
}

# Pilot-4 branch points that marked where a real connector sits -> that connector takes its place.
NODE_AT = {"bp_at_ecu_b": "ecu_b"}

PART_KEYS = ("partId", "contactPartId", "cavityPlugPartId", "cavitySealPartId")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def part_index(doc):
    return {p["id"]: (k, p) for k, v in doc.items() if k.endswith("Parts") for p in v}


def referenced_parts(obj):
    """Every part id an object (or a part) points at."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in PART_KEYS and isinstance(v, str):
                out.add(v)
            elif k == "partIds":
                out.update(v)
            else:
                out |= referenced_parts(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= referenced_parts(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    geo = load(a.geometry)
    src = {None: geo}
    for f in {s for s, _, _ in CONNECTORS.values() if s}:
        src[f] = load(os.path.join(REBUILD, f + ".harness"))

    out = {k: geo[k] for k in ("$schema", "$docs", "version", "lengthUnit", "pdfExportSettings")}
    out["titleBlock"] = dict(geo["titleBlock"], title="ST185-A-cabin - ECU plug A cabin loom (clean-room pilot)")
    parts_needed = {}  # part id -> source doc

    # --- connectors: copied whole; owned pins get the description, the rest of a far-end
    #     connector is N/C (it is wired in its own file)
    used = {}  # (node, pin designation) -> description
    def note(end, text):
        if end and end[1] is not None and end[0] in CONNECTORS:
            used[end] = text
    for wid, f, t, text in WIRES:
        note(f, text)
        note(t, text)
    for cores in CABLES.values():
        for f, t, text in cores.values():
            note(f, text)
            note(t, text)

    conns = []
    cav_id = {}
    for key, (sfile, sid, label) in CONNECTORS.items():
        sdoc = src[sfile]
        c = copy.deepcopy(next(x for x in sdoc["connectors"] if x["id"] == sid))
        c["label"] = label
        for i, cav in enumerate(c["cavities"]):
            des = cav.get("designation", str(i + 1))
            cav_id[(key, des)] = cav["id"]
            text = used.get((key, des))
            if text:
                cav["signal"] = text
                cav["propagate"] = False
                cav.pop("notConnected", None)
                if cav.get("cavityPlugPartId"):
                    cav.pop("cavityPlugPartId")
            else:
                # not wired here: N/C. Far-end connectors and the shared bulkhead are wired
                # in their own files; ECU-A / pedal / inline spares are real spares.
                for k in ("signal", "propagate", "contactPartId"):
                    cav.pop(k, None)
                cav["notConnected"] = True
                if sfile:
                    cav["cavityPlugPartId"] = None
        c.pop("wiringTable", None)
        conns.append(c)
        for p in referenced_parts(c):
            parts_needed.setdefault(p, sdoc)
    out["connectors"] = conns
    bhb = {cv.get("designation"): cv for cv in next(
        c for c in load(os.path.join(REBUILD, "ST185-B-cabin.harness"))["connectors"]
        if c["id"] == "bh_b_fw")["cavities"]}
    for cav in next(c for c in conns if c["id"] == "bh_a_fw")["cavities"]:
        if cav.get("signal") and not cav.get("contactPartId") and bhb.get(cav["designation"], {}).get("contactPartId"):
            cav["contactPartId"] = bhb[cav["designation"]]["contactPartId"]

    # one note per connector that is shared with another file (R10): where its other pins are wired
    out["schematicNotes"] = []
    for key, (sfile, sid, label) in CONNECTORS.items():
        if sfile and key not in ("k_efi", "k_str", "k_fan", "k_etb"):
            x, y, w = POS[key]
            out["schematicNotes"].append({"id": "n_see_" + key, "text": "N/C pins: see " + sfile,
                                          "schematicPosition": {"x": x, "y": y - 60}, "width": 270})
    out["schematicNotes"].append({"id": "n_see_relays", "text": "Relay sockets R2 / R3 / R4 / M14: only pin 85 is wired here. N/C pins: see ST185-CabinPower",
                                  "schematicPosition": {"x": -1260, "y": 720}, "width": 270})
    out["schematicNotes"].append({"id": "n_see_bh", "text": "Bulkhead = one DRB102. N/C pins: see ST185-B-cabin (section B) or spare",
                                  "schematicPosition": {"x": 1890, "y": -360}, "width": 390})

    # bussed caps: no wires; their cavities stay as the bus name (one node with the plug)
    for c in conns:
        if c["id"] in ("bus_5v_bha_r", "bus_gnd_bha_r"):
            name = "+5 V sensor supply bus" if "5v" in c["id"] else "Sensor ground bus"
            for cav in c["cavities"]:
                cav.pop("notConnected", None)
                cav["signal"] = name
                cav["propagate"] = False

    # --- splices, resistor, terminals (copied from the geometry file for parts and layout)
    gsp = {s["id"]: s for s in geo["splices"]}
    out["splices"] = []
    for sid, label in SPLICES.items():
        s = copy.deepcopy(gsp[sid])
        s["label"] = label
        out["splices"].append(s)
    out["resistors"] = copy.deepcopy(geo["resistors"])
    out["resistors"][0]["label"] = "Cam pull-up 1.8 k to +8 V"
    gt = {t["id"]: t for t in geo["terminals"]}
    out["terminals"] = []
    for tid, (gid, label) in TERMINALS.items():
        t = copy.deepcopy(gt[gid])
        t["id"], t["label"] = tid, label
        t.pop("signal", None)
        if tid.startswith("x_"):
            t["type"] = "Loose"
        out["terminals"].append(t)

    def end(e, text):
        node, pin = e
        if node in CONNECTORS:
            return {"id": node, "handle": cav_id[(node, pin)]}
        if node in SPLICES:
            return {"id": node, "handle": "Splice"}
        if node == "cam_pullup":
            return {"id": node, "handle": pin}
        return {"id": node, "handle": "Terminal"}

    # --- wires: colour / gauge part / ident bands kept from the old wire of the same id
    gw = {w["id"]: w for w in geo["wires"]}
    keep = ("color", "stripeColor", "identColors", "partId")
    out["wires"] = []
    for wid, f, t, text in WIRES:
        old = gw.get(wid) or gw["w_ac_psw_in"]
        w = {"id": wid, "source": end(f, text), "target": end(t, text)}
        w.update({k: old[k] for k in keep if k in old})
        out["wires"].append(w)

    out["cables"] = []
    for cb in geo["cables"]:
        cb = copy.deepcopy(cb)
        spec = CABLES[cb["id"]]
        for core in cb["cores"] + ([cb["shield"]] if cb.get("shield") else []):
            f, t, text = spec[core["id"]]
            for k in ("layoutPoints", "sourceLayoutPoints", "targetLayoutPoints"):
                core.pop(k, None)
            if f:
                core["source"] = end(f, text)
            else:
                core.pop("source", None)
            core["target"] = end(t, text)
        out["cables"].append(cb)

    out["mates"] = copy.deepcopy(geo["mates"])

    # terminal descriptions (a terminal has one wire: same text as that wire)
    for wid, f, t, text in WIRES:
        for e in (f, t):
            for term in out["terminals"]:
                if term["id"] == e[0]:
                    term["signal"] = text
    for cores in CABLES.values():
        for f, t, text in cores.values():
            for term in out["terminals"]:
                if f and term["id"] == f[0] or term["id"] == t[0]:
                    term["signal"] = text

    # --- layout view: pilot-4 geometry, stub legs re-pointed to the real node
    node_lp = {}
    for c in geo["connectors"] + geo["terminals"]:
        node_lp[c["id"]] = c.get("layoutPosition")
    for old, new in LAYOUT_SWAP.items():
        if new and new in CONNECTORS and CONNECTORS[new][0]:
            next(c for c in conns if c["id"] == new)["layoutPosition"] = node_lp[old]
    for t in out["terminals"]:
        gid = TERMINALS[t["id"]][0]
        t["layoutPosition"] = node_lp[gid]
    for bp in geo["branchPoints"]:
        if bp["id"] in NODE_AT:
            next(c for c in conns if c["id"] == NODE_AT[bp["id"]])["layoutPosition"] = bp["layoutPosition"]
    bundles = []
    for b in geo["bundles"]:
        b = copy.deepcopy(b)
        drop = False
        for k in ("sourceId", "targetId"):
            b[k] = NODE_AT.get(b[k], b[k])
            if b[k] in LAYOUT_SWAP:
                if LAYOUT_SWAP[b[k]] is None:
                    drop = True
                else:
                    b[k] = LAYOUT_SWAP[b[k]]
        if not drop:
            bundles.append(b)
    # branch points left as dead ends after dropping legs go too (repeat until stable)
    bps = {p["id"]: p for p in copy.deepcopy(geo["branchPoints"]) if p["id"] not in NODE_AT}
    while True:
        deg = {k: 0 for k in bps}
        for b in bundles:
            for k in ("sourceId", "targetId"):
                if b[k] in deg:
                    deg[b[k]] += 1
        dead = {k for k, n in deg.items() if n <= 1}
        if not dead:
            break
        bundles = [b for b in bundles if b["sourceId"] not in dead and b["targetId"] not in dead]
        for k in dead:
            bps.pop(k)
    out["bundles"] = bundles
    out["branchPoints"] = list(bps.values())
    for s in out["splices"]:
        if s.get("locationId") and s["locationId"] not in bps and s["locationId"] not in CONNECTORS:
            s.pop("locationId")
    if out["resistors"][0].get("locationId") not in bps:
        out["resistors"][0].pop("locationId", None)

    # --- schematic view
    place(out)

    # --- parts: everything referenced, copied from the file the component came from
    for coll in ("wires", "cables", "splices", "resistors", "terminals", "bundles", "branchPoints"):
        for p in referenced_parts(out[coll]):
            parts_needed.setdefault(p, geo)
    pidx = {id(d): part_index(d) for d in src.values()}
    parts = {}
    todo = list(parts_needed.items())
    while todo:
        pid, sdoc = todo.pop()
        if pid in parts or pid is None:
            continue
        hit = pidx[id(sdoc)].get(pid) or part_index(geo).get(pid)
        if not hit:
            raise SystemExit(f"part {pid} not found")
        parts[pid] = hit
        for q in referenced_parts(hit[1]):
            todo.append((q, sdoc))
    for coll, p in sorted(parts.values(), key=lambda kp: (kp[0], kp[1]["id"])):
        out.setdefault(coll, []).append(p)

    out = {k: v for k, v in out.items() if v != []}
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, a.out)
    print(f"wrote {a.out}: {len(out['wires'])} wires, "
          f"{sum(len(c['cores']) + bool(c.get('shield')) for c in out['cables'])} cable cores, "
          f"{len(out['connectors'])} connectors, {len(out['splices'])} splices")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    main()
