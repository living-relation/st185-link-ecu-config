"""Clean-room build of ST185-A-cabin.harness (pilot, Dan's brief 2026-10-19).

One plain table, WIRES, says every wire: from (node, pin) to (node, pin) and what the wire is
for in plain words. That text is written as the cavity signal at BOTH ends (propagate off), so
every connector table reads like a pinout: pin | wire | description.

Wires join only at a splice the SoT names (SPLICES). A wire that carries on in another loom
ends on that loom's break end (the paired `breaks` in docs/harness/interfaces.json, which the
SoT gates trace across files); its terminal is labelled with where the wire goes next.

Inputs (read only):
  --geometry  pilot-4 A-cabin file (branch harness-views-cleanup): connector / splice /
              terminal part set-up, the whole layout view, and wire colours / gauge parts.
Pin facts: sot/channels.csv, docs/harness/DRB102-CAVITY-MAP.md, docs/harness/interfaces.json.

    python docs/harness/cleanroom/build_a_cabin.py --geometry p4.harness --out docs/harness/rebuild/ST185-A-cabin.harness
"""
import argparse
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout_schematic import metrics, place  # noqa: E402
from oem_ends import OEM_ENDS  # noqa: E402

# connector id -> name on the drawing
CONNECTORS = {
    "ecu_a": "ECU-A  Link G4X plug A (centre dash)",
    "bh_a_fw": "BULKHEAD  DRB102 receptacle (RH firewall)",
    "aps": "PEDAL  accelerator pedal sensor",
    "ix_ws_front_p": "FRONT WS INLINE  to front VR conditioner",
    "bus_5v_bha_p": "+5V BUS  DT06-8 plug (by bulkhead)",
    "bus_5v_bha_r": "+5V BUS cap  DT04-8 bussed",
    "bus_gnd_bha_p": "SENSOR GND BUS  DT06-8 plug (by bulkhead)",
    "bus_gnd_bha_r": "SENSOR GND BUS cap  DT04-8 bussed",
}

# splices the SoT names (interfaces.json / channels.csv notes) -> "<where> - <what it joins>"
SPLICES = {
    "sp_5v": "At ECU-A plug - SP-5V-A: +5 V sensor supply",
    "sp_5v_2": "At ECU-A plug - SP-5V-PEDAL: +5 V to pedal + cruise",
    "sp_8v": "At ECU-A plug - SP-8V: +8 V cam sensor supply",
    "sp_trig2": "At ECU-A plug - SP-CAM: cam signal + 1.8 k pull-up",
    "sp_gndout": "At ECU-A plug - SP-GNDOUT-A: sensor ground",
    "sp_sw12": "At ECU-A plug - SP-SW12: switched +12 V",
    "sp_chassis": "At ECU-A plug - SP-GND-CHASSIS: ECU power ground",
    "sp_shield_a": "6 mm behind ECU-A plug - SP-SHIELD-A: shield drains",
    "sp_ac_psw": "At A/C amp - SP-AC-PSW: A/C pressure switch output",
}

# wire ends that are not connectors -> (label on the drawing "<where it lands> - <what it is>",
# long text the gates read back through full_text.json).
# br_* = the wire carries on in another loom (break pair in interfaces.json);
# fl_* = tap into factory wiring (interfaces.json flyingLeads; long text keeps the EWD page).
def _br(label, other):
    return (label, label + " - continues on ST185-" + other)


TERMINALS = {
    "br_w76": _br("EFI main relay R2 pin 85, POWER box - EFI relay coil (-)", "CabinPower"),
    "br_w81": _br("ETB relay M14 pin 85, LOGIC box - ETB relay coil (-)", "CabinPower"),
    "br_w_str85": _br("Start relay R3 pin 85, POWER box - start relay coil (-)", "CabinPower"),
    "br_w_fan85": _br("Rad fan relay R4 pin 85, POWER box - fan relay coil (-)", "CabinPower"),
    "br_w_fp85": _br("Fuel pump relay K1 pin 85, trunk - fuel pump relay coil (-)", "HeavyDC"),
    "br_w_acc86": _br("A/C clutch relay M15 pin 86, LOGIC box - A/C relay coil (+)", "CabinPower"),
    "br_w_eps_rly": _br("EHPS relay pin 85, glove box - EHPS relay coil (-)", "CabinPower"),
    "br_w_fb_sw12": _br("SW12 bus plug pin 2, glove box - switched +12 V feed", "CabinPower"),
    "br_w_inj_pwr_c": _br("LOGIC box fuse INJ 15 A lead - injector +12 V", "CabinPower"),
    "br_w_cop_pwr_c": _br("LOGIC box fuse COP 15 A lead - coil +12 V", "CabinPower"),
    "br_w_fb_mrs_en": _br("LOGIC box fuse MRS 7.5 A lead - EHPS enable +12 V", "CabinPower"),
    "br_w_b25": _br("ECU-B pin B25 - ECU power ground", "B-cabin"),
    "br_w_b34": _br("ECU-B pin B34 - ECU power ground (2)", "B-cabin"),
    "br_w_lamg_b": _br("Bulkhead pin 96 - CAN-Lambda ground", "B-cabin"),
    "br_w_rail_sw12_b_c": _br("Bulkhead pin 90 - +12 V gearbox speed sensor", "B-cabin"),
    "br_w_rail_5v_b_c": _br("Splice SP-5V-B at ECU-B plug - +5 V loom B sensors", "B-cabin"),
    "br_cab_fspur_r": _br("ECU-B pin B21 - front right wheel speed", "B-cabin"),
    "br_cab_fspur_fr_sh": _br("Splice SP-SHIELD-B at ECU-B plug - FR wheel speed shield", "B-cabin"),
    "br_w39": _br("ECU-B pin B33 - pedal 2 signal (sub)", "B-cabin"),
    "br_w_cru_5v": _br("Cruise ladder resistor lead, centre console - +5 V cruise", "CSB3"),
    "br_w_csbg": _br("CSB3 ground splice, centre console - CSB3 + opto ground", "CSB3"),
    "br_ac_psw": _br("A/C pressure switch A5 pin 4, engine bay - pressure switch out", "EngineRoom-C"),
    "br_ac_mg": _br("A/C compressor A4 pin 3, engine bay - VC coil (unused)", "EngineRoom-C"),
    "fl_acamp_act": ("A/C amp A18 pin 11, factory G-Y lead - A/C cancel (ACT)",
                     "EWD 1992 EWD132U p.93/p.218 A18-11 G-Y ACT compressor cancel (1990 book locator A18; pin from 1992 A17-11) <- ECU Aux 4, ground = kill - solder sleeve into the factory G-Y lead at the A/C amplifier"),
    "fl_acamp_psw": ("A/C amp A18 pin 13, factory Y-R lead - pressure switch in",
                     "EWD 1990 p.152 A18-13 Y-R A/C pressure switch in <- A5-4 - solder sleeve into the factory Y-R lead at the A/C amplifier"),
    "fl_acamp_mg": ("A/C amp A18 pin 5, factory Y-B lead - VC coil out (unused)",
                    "EWD 1990 p.152 A18-5 Y-B magnetic clutch -> A4-3 - solder sleeve into the factory Y-B lead at the A/C amplifier"),
    "chassis_ring": ("Cabin chassis stud M6 at ECU - ECU ground ring", ""),
}

# Inline connector shared with ST185-WheelSpeed-Front: its pin text must match that half
# word for word (gate I5), so the front-WS circuits use that file's names.
WS_5V, WS_GND, WS_FL, WS_FR, WS_SH = ("VRC-F +5V", "VRC-F GND", "FL conditioned out",
                                     "FR conditioned out", "WS-F screen drain")

# id (kept from the old file: colour, gauge part, ident bands carry over),
# from (node, pin), to (node, pin), description. pin None = splice / terminal.
WIRES = [
    # ECU-A straight to the bulkhead (bulkhead pin = DRB102 cavity number)
    ("w108_c", ("ecu_a", "A4"), ("bh_a_fw", "31"), "Injector 1 drive (-)"),
    ("w109_c", ("ecu_a", "A3"), ("bh_a_fw", "32"), "Injector 2 drive (-)"),
    ("w110_c", ("ecu_a", "A2"), ("bh_a_fw", "33"), "Injector 3 drive (-)"),
    ("w111_c", ("ecu_a", "A1"), ("bh_a_fw", "34"), "Injector 4 drive (-)"),
    ("w120_c", ("ecu_a", "A13"), ("bh_a_fw", "35"), "Coil 1 trigger (IGT)"),
    ("w121_c", ("ecu_a", "A12"), ("bh_a_fw", "36"), "Coil 2 trigger (IGT)"),
    ("w122_c", ("ecu_a", "A11"), ("bh_a_fw", "37"), "Coil 3 trigger (IGT)"),
    ("w123_c", ("ecu_a", "A10"), ("bh_a_fw", "38"), "Coil 4 trigger (IGT)"),
    ("w200_c", ("ecu_a", "A8"), ("bh_a_fw", "9"), "Crank sensor signal"),
    ("w16_c", ("ecu_a", "A30"), ("bh_a_fw", "17"), "Turbo speed signal"),
    ("w48_c", ("ecu_a", "A31"), ("bh_a_fw", "21"), "Flex fuel signal"),
    ("w128_c", ("ecu_a", "A22"), ("bh_a_fw", "24"), "Throttle pos 1 main"),
    ("w129_c", ("ecu_a", "A33"), ("bh_a_fw", "25"), "Throttle pos 2 sub"),
    ("w26_c", ("ecu_a", "A17"), ("bh_a_fw", "30"), "MAP sensor signal"),
    ("w103_c", ("ecu_a", "A21"), ("bh_a_fw", "39"), "Boost solenoid (-)"),
    ("w201_c", ("ecu_a", "A15"), ("bh_a_fw", "40"), "Coolant temp signal"),
    ("w202_c", ("ecu_a", "A16"), ("bh_a_fw", "41"), "Intake temp signal"),
    ("w_mrs_c", ("ecu_a", "A27"), ("bh_a_fw", "44"), "EHPS pump speed"),
    # cam sensor: signal + 1.8 k pull-up to +8 V meet at a splice
    ("w_trig2_pin", ("ecu_a", "A9"), ("sp_trig2", None), "Cam sensor signal"),
    ("w_cam_sig_c", ("sp_trig2", None), ("bh_a_fw", "13"), "Cam sensor signal"),
    ("w_cam_pullup_sig", ("cam_pullup", "Right"), ("sp_trig2", None), "Cam pull-up 1.8k"),
    ("w_cam_pullup_8v", ("sp_8v", None), ("cam_pullup", "Left"), "+8 V to cam pull-up"),
    ("w19", ("sp_8v", None), ("ecu_a", "A6"), "+8 V sensor supply"),
    ("w_rail_sp_8v_c", ("sp_8v", None), ("bh_a_fw", "12"), "+8 V to cam sensor"),
    # +5 V sensor supply
    ("w67", ("ecu_a", "A32"), ("sp_5v", None), "+5 V sensor supply"),
    ("w_5v_bha_trunk", ("sp_5v", None), ("bus_5v_bha_p", "1"), "+5 V sensor supply"),
    ("w_rail_sp_5v_c", ("bus_5v_bha_p", "2"), ("bh_a_fw", "23"), "+5 V throttle sensor"),
    ("w_5v_a_c39", ("bus_5v_bha_p", "3"), ("bh_a_fw", "28"), "+5 V MAP sensor"),
    ("w_5v_a_c40", ("bus_5v_bha_p", "4"), ("bh_a_fw", "16"), "+5 V turbo speed"),
    ("w_5v_brail_c45", ("bus_5v_bha_p", "5"), ("bh_a_fw", "47"), "+5 V oil pressure"),
    ("w_5v_brail_c46", ("bus_5v_bha_p", "6"), ("bh_a_fw", "50"), "+5 V fuel pressure"),
    ("w_5v_brail_c47", ("bus_5v_bha_p", "7"), ("bh_a_fw", "51"), "+5 V coolant press"),
    ("w_5v_link", ("sp_5v", None), ("sp_5v_2", None), "+5 V pedal + cruise"),
    ("w_rail_5v_b_c_ac", ("sp_5v", None), ("br_w_rail_5v_b_c", None), "+5 V loom B sensors"),
    ("w_cru_5v_ac", ("sp_5v_2", None), ("br_w_cru_5v", None), "+5 V cruise ladder"),
    # sensor ground
    ("w68", ("ecu_a", "A24"), ("sp_gndout", None), "Sensor ground"),
    ("w_gnd_bha_trunk", ("sp_gndout", None), ("bus_gnd_bha_p", "1"), "Sensor ground"),
    ("w_rail_sp_gndout_c", ("bus_gnd_bha_p", "2"), ("bh_a_fw", "26"), "Gnd IAT/TPS/coolant"),
    ("w_gnd_a_c41", ("bus_gnd_bha_p", "3"), ("bh_a_fw", "10"), "Gnd crank sensor"),
    ("w_gnd_a_c42", ("bus_gnd_bha_p", "4"), ("bh_a_fw", "14"), "Gnd cam sensor"),
    ("w_gnd_a_c43", ("bus_gnd_bha_p", "5"), ("bh_a_fw", "18"), "Gnd turbo speed"),
    ("w_gnd_a_c44", ("bus_gnd_bha_p", "6"), ("bh_a_fw", "29"), "Gnd flex + MAP"),
    # switched +12 V
    ("w_fb_sw12", ("br_w_fb_sw12", None), ("sp_sw12", None), "Switched +12 V feed"),
    ("w78", ("sp_sw12", None), ("ecu_a", "A5"), "ECU main +12 V"),
    ("w_rail_sp_sw12_c", ("sp_sw12", None), ("bh_a_fw", "20"), "+12 V boost + flex"),
    ("w_rail_sw12_b_c_ac", ("sp_sw12", None), ("br_w_rail_sw12_b_c", None), "+12 V gearbox speed"),
    # fused feeds from the LOGIC box to the bulkhead
    ("w_inj_pwr_ac", ("br_w_inj_pwr_c", None), ("bh_a_fw", "1"), "Injector +12 V feed"),
    ("w_cop_pwr_ac", ("br_w_cop_pwr_c", None), ("bh_a_fw", "2"), "Coil +12 V feed"),
    ("w_fb_mrs_en", ("br_w_fb_mrs_en", None), ("bh_a_fw", "42"), "EHPS enable +12 V"),
    # ECU power ground
    ("w70", ("ecu_a", "A25"), ("sp_chassis", None), "ECU power ground"),
    ("w_a34", ("ecu_a", "A34"), ("sp_chassis", None), "ECU power ground"),
    ("w_b25_ac", ("sp_chassis", None), ("br_w_b25", None), "ECU power ground"),
    ("w_b34_ac", ("sp_chassis", None), ("br_w_b34", None), "ECU power ground"),
    ("w_lamg_ac", ("br_w_lamg_b", None), ("sp_chassis", None), "CAN-Lambda ground"),
    ("w_csbg_ac", ("sp_chassis", None), ("br_w_csbg", None), "CSB3 + opto ground"),
    ("w66", ("chassis_ring", None), ("sp_chassis", None), "ECU ground chassis"),
    # shield drains: one drain node, grounded only at ECU A7
    ("w_drain_ecu_a", ("sp_shield_a", None), ("ecu_a", "A7"), "Shield drain"),
    ("w_shc_crank", ("bh_a_fw", "11"), ("sp_shield_a", None), "Crank sensor shield"),
    ("w_shc_cam", ("bh_a_fw", "15"), ("sp_shield_a", None), "Cam sensor shield"),
    ("w_shc_turbo", ("bh_a_fw", "19"), ("sp_shield_a", None), "Turbo speed shield"),
    ("w_shc_flex", ("bh_a_fw", "22"), ("sp_shield_a", None), "Flex fuel shield"),
    ("w_shc_etbs", ("bh_a_fw", "27"), ("sp_shield_a", None), "Throttle shield"),
    # relay coils the ECU switches to ground
    ("w_fp85", ("br_w_fp85", None), ("ecu_a", "A19"), "Fuel pump relay (-)"),
    ("w81", ("br_w81", None), ("ecu_a", "A20"), "ETB relay coil (-)"),
    ("w_str85", ("br_w_str85", None), ("ecu_a", "A26"), "Start relay coil (-)"),
    ("w76", ("br_w76", None), ("ecu_a", "A28"), "EFI relay coil (-)"),
    ("w_fan85", ("br_w_fan85", None), ("ecu_a", "A29"), "Rad fan relay (-)"),
    ("w_eps_rly", ("br_w_eps_rly", None), ("bh_a_fw", "56"), "EHPS relay coil (-)"),
    # A/C (R23): each wire point to point; the one A/C splice is the SoT's sp_ac_psw
    ("w_ac_kill", ("ecu_a", "A18"), ("fl_acamp_act", None), "A/C cancel (ACT)"),
    ("w_ac_psw_in", ("br_ac_psw", None), ("sp_ac_psw", None), "A/C pressure sw out"),
    ("w_ac_psw_sw", ("fl_acamp_psw", None), ("sp_ac_psw", None), "A/C pressure sw out"),
    ("w_acc86", ("sp_ac_psw", None), ("br_w_acc86", None), "A/C clutch relay (+)"),
    ("w_ac_clutch_mg", ("fl_acamp_mg", None), ("br_ac_mg", None), "A/C VC coil (unused)"),
]

# cable cores: cable id -> core id -> (from, to, description)
CABLES = {
    "cab_aps": {
        "w_aps_vc1": (("aps", "4"), ("sp_5v_2", None), "+5 V pedal sensor 1"),
        "w40": (("aps", "5"), ("sp_gndout", None), "Pedal 1 ground"),
        "w38": (("aps", "6"), ("ecu_a", "A14"), "Pedal 1 signal main"),
        "w210": (("aps", "1"), ("sp_5v_2", None), "+5 V pedal sensor 2"),
        "w_aps_gnd2": (("aps", "2"), ("sp_gndout", None), "Pedal 2 ground"),
        "w_aps_vpa2": (("aps", "3"), ("br_w39", None), "Pedal 2 signal sub"),
        "cab_aps_sh": (None, ("sp_shield_a", None), "Pedal cable shield"),
    },
    "cab_fspur": {
        "cab_fspur_5v": (("ix_ws_front_p", "1"), ("sp_5v", None), WS_5V),
        "cab_fspur_gnd": (("ix_ws_front_p", "2"), ("sp_gndout", None), WS_GND),
        "cab_fspur_l": (("ix_ws_front_p", "3"), ("ecu_a", "A23"), WS_FL),
        "cab_fspur_sh": (("ix_ws_front_p", "5"), ("sp_shield_a", None), WS_SH),
    },
    "cab_fspur_fr_ac": {
        "cab_fspur_r_ac": (("ix_ws_front_p", "4"), ("br_cab_fspur_r", None), WS_FR),
        "cab_fspur_fr_sh_ac": (None, ("br_cab_fspur_fr_sh", None), "FR wheel spd shield"),
    },
}

# Dan N41 = B: DRAWN = initials of the person on Rev A (never changes); a rev's BY = initials of
# whoever asked for that change, never an agent name. On ST185 both are always DG.
DRAWN = "DG"
REV = "A"
REV_BY = "DG"
REV_NOTE = "clean-room rebuild from the master wire list (DECISIONS R201); pins as sot/channels.csv."

# The ONE general notes block: build notes a builder needs, plain words, at most five.
GENERAL_NOTES = [
    "Each table is a pinout: pin, wire, description. A wire has the same description at both ends.",
    "An end that says 'on ST185-<file>' is the same wire running on in that loom, not a join.",
    "Every shield drain is its own wire. Drains meet only at SP-SHIELD-A, 6 mm behind the ECU-A "
    "plug: the crank drain is crimped into A7, the others are soldered onto it.",
    "Sensor ground (ECU A24) never joins chassis ground or loom B sensor ground (ECU B22).",
    "Bulkhead pins marked N/C are section B (see ST185-B-cabin) or spares with a sealing plug.",
]

# Per-wire facts from the old big note blocks, added to that wire's end note.
END_EXTRA = {
    "br_w_fb_mrs_en": "Fuse fed from EPS enable relay k_eps_en pin 87 (ignition-switched).",
}

# Notes tied to a connector (drawn beside its table).
NODE_NOTES = {
    "n_pedal_length": ("aps", "Pedal branch length is a placeholder: measure at the car."),
}

ROUTING_KEYS = ("layoutPoints", "sourceLayoutPoints", "targetLayoutPoints")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_full_text(out):
    """full_text.json, A-cabin entry: the long text the gates read back (model.full_text) for
    what the drawing shows short. Wire ends: ["", long]. Bulkhead pins: [shown, A-engine's long
    text for the same cavity] - the two halves of the DRB102 show the same name."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "full_text.json")
    ft = load(path)
    eng = ft["ST185-A-engine.harness"]["connectors"]["bh_a_eng"]["cavities"]
    bh = next(c for c in out["connectors"] if c["id"] == "bh_a_fw")
    # the inline WS connector: same shown and long text as its WheelSpeed-Front half
    ws = ft["ST185-WheelSpeed-Front.harness"]["connectors"]["ix_ws_front_r"]["cavities"]
    ix = next(c for c in out["connectors"] if c["id"] == "ix_ws_front_p")
    ft["ST185-A-cabin.harness"] = {
        "connectors": {
            "bh_a_fw": {"cavities": {
                cav["id"]: [cav["signal"], eng[cav["id"]][1]]
                for cav in bh["cavities"] if cav.get("signal") and cav["id"] in eng}},
            "ix_ws_front_p": {"cavities": {
                cav["id"]: [cav["signal"], ws[cav["id"]][1]]
                for cav in ix["cavities"] if cav.get("signal") and cav["id"] in ws}}},
        "terminals": {tid: ["", long] for tid, (_, long) in TERMINALS.items() if long},
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ft, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    geo = load(a.geometry)
    out = copy.deepcopy(geo)  # parts, layout view, settings; everything below is rewritten
    out["titleBlock"] = dict(geo["titleBlock"], title="ST185-A-cabin - ECU plug A cabin loom",
                             drawingNumber="ST185-A-cabin rev %s" % REV, drawnBy=DRAWN)
    out["exportNotes"] = "Rev %s, BY %s: %s\n%s" % (REV, REV_BY, REV_NOTE, geo.get("exportNotes", ""))

    # every (node, pin) -> description, from the wire table
    text = {}
    for _, f, t, desc in WIRES:
        text[f] = text[t] = desc
    for cores in CABLES.values():
        for f, t, desc in cores.values():
            if f:
                text[f] = desc
            text[t] = desc

    # connectors: label + one description per wired pin, nothing on unwired pins
    cav_id = {}
    for c in out["connectors"]:
        c["label"] = CONNECTORS[c["id"]]
        for i, cav in enumerate(c["cavities"]):
            des = cav.get("designation", str(i + 1))
            cav_id[(c["id"], des)] = cav["id"]
            desc = text.get((c["id"], des))
            if desc:
                cav["signal"], cav["propagate"] = desc, False
            elif not cav.get("notConnected"):
                cav.pop("signal", None)
                cav.pop("propagate", None)
    for c in out["connectors"]:  # bussed caps carry no wire; their pins are the bus itself
        if c["id"].endswith("_r"):
            name = "+5 V sensor bus" if "5v" in c["id"] else "Sensor ground bus"
            for cav in c["cavities"]:
                if not cav.get("notConnected"):
                    cav["signal"], cav["propagate"] = name, False

    out["splices"] = [s for s in out["splices"] if s["id"] in SPLICES]
    for s in out["splices"]:
        s["label"] = SPLICES[s["id"]]
    out["resistors"][0]["label"] = "Cam pull-up 1.8 k to +8 V"
    out["terminals"] = [t for t in out["terminals"] if t["id"] in TERMINALS]
    for t in out["terminals"]:
        t["label"] = TERMINALS[t["id"]][0]  # R156: a wire end has a label and no signal
        t["width"] = 390
        t.pop("signal", None)

    def end(e):
        node, pin = e
        if node in CONNECTORS:
            return {"id": node, "handle": cav_id[(node, pin)]}
        if node in SPLICES:
            return {"id": node, "handle": "Splice"}
        if node == "cam_pullup":
            return {"id": node, "handle": pin}
        return {"id": node, "handle": "Terminal"}

    gw = {w["id"]: w for w in geo["wires"]}
    out["wires"] = []
    for wid, f, t, _ in WIRES:
        w = {"id": wid, "source": end(f), "target": end(t)}
        w.update({k: gw[wid][k] for k in ("color", "stripeColor", "identColors", "partId") if k in gw[wid]})
        out["wires"].append(w)
    for cb in out["cables"]:
        for core in cb["cores"] + ([cb["shield"]] if cb.get("shield") else []):
            f, t, _ = CABLES[cb["id"]][core["id"]]
            for k in ROUTING_KEYS:
                core.pop(k, None)
            if f:
                core["source"] = end(f)
            core["target"] = end(t)

    # schematic notes: a read-me, then EVERY note of the old drawing carried over (Dan
    # 2026-10-19: OEM ends keep their notes, no locator note dropped). An end note sits next to
    # its wire end; a factory end's note says where the tap is, the EWD page, colour and method.
    # Drawing rules (Dispatch for Dan 2026-10-19): ONE short general block of build notes; a
    # per-wire fact sits in that wire's end note; history lives in DECISIONS / git, never here.
    notes = [{"id": "n_general", "text": "\n".join(GENERAL_NOTES), "width": 390}]
    attach = {}
    for n in geo["schematicNotes"]:
        tid = n["id"][len("n_end_"):] if n["id"].startswith("n_end_") else None
        if tid and tid in TERMINALS:
            text = OEM_ENDS[tid]["short"] if tid in OEM_ENDS else n["text"]
            text = " ".join(x for x in (text, END_EXTRA.get(tid, "")) if x)
            attach[tid] = n["id"]
        elif tid:
            raise SystemExit("old end note %s has no end in this file" % n["id"])
        else:
            continue  # the old big blocks: their facts are in GENERAL_NOTES, END_EXTRA or the docs
        notes.append({"id": n["id"], "text": text, "width": 390 if len(text) > 200 else 270})
    for nid, (node, text) in NODE_NOTES.items():
        notes.append({"id": nid, "text": text, "width": 270})
        attach[node] = nid
    out["schematicNotes"] = notes
    place(out, attach)
    print("schematic:", metrics(out))

    write_full_text(out)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, a.out)
    print(f"wrote {a.out}: {len(out['wires'])} wires, "
          f"{sum(len(c['cores']) + bool(c.get('shield')) for c in out['cables'])} cable conductors, "
          f"{len(out['connectors'])} connectors, {len(out['splices'])} splices, {len(out['terminals'])} wire ends")


if __name__ == "__main__":
    main()
