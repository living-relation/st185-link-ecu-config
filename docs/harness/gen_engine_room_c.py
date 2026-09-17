#!/usr/bin/env python3
"""Generate the partial Engine Room Harness C drawing.

Only new / upgraded / relocated feeds. OEM engine-room, cowl and dash looms stay
on the car; this file is the add-on plus the kick-panel / J/B2 injection points.
Regenerate: python3 docs/harness/gen_engine_room_c.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).with_name("ST185-EngineRoom-C.harness")


def pos(x, y):
    return {"x": x, "y": y}


def cav(i, desig, signal, **extra):
    d = {"id": f"c{i}", "designation": str(desig), "signal": signal}
    d.update(extra)
    return d


def conn(cid, label, x, y, cavities, part_id=None, width=240, lx=None, ly=None):
    c = {
        "id": cid,
        "label": label,
        "width": width,
        "schematicPosition": pos(x, y),
        "layoutPosition": pos(lx if lx is not None else x, ly if ly is not None else y + 3000),
        "cavities": cavities,
    }
    if part_id:
        c["partId"] = part_id
    return c


def term(tid, typ, signal, x, y, width=210):
    return {
        "id": tid,
        "type": typ,
        "signal": signal,
        "width": width,
        "schematicPosition": pos(x, y),
        "layoutPosition": pos(x, y + 3000),
    }


def wire(wid, color, src, sh, tgt, th, x1=None, y1=None, x2=None, y2=None):
    w = {
        "id": wid,
        "color": color,
        "source": {"id": src, "handle": sh},
        "target": {"id": tgt, "handle": th},
    }
    if x1 is not None:
        w["layoutPoints"] = [
            {"id": f"{wid}_r1", "schematicPosition": pos(x1, y1)},
            {"id": f"{wid}_r2", "schematicPosition": pos(x2, y2)},
        ]
    return w


def note(nid, text, x, y, width=420, color=None):
    n = {"id": nid, "text": text, "width": width, "schematicPosition": pos(x, y)}
    if color:
        n["color"] = color
    return n


def mate(mid, a, b):
    return {"id": mid, "sourceId": a, "targetId": b}


connectors = [
    conn("pdb", "Cabin PDB (glove box)", 0, 180, [
        cav(1, "BAT+", "Trunk battery + 2 AWG / 1/0"),
        cav(2, "ALT/STR", "To RADLOK +  (starter / 160 A alt)"),
        cav(3, "FUSE IN", "Cabin fuse block IN"),
        cav(4, "PMU M6", "PMU-16 battery stud"),
        cav(5, "OEM HOT", "Always-hot feed to J/B No.1 1I-1"),
        cav(6, "AM1", "40A fused AM1 to IE1-10 / I9-4"),
        cav(7, "AM2", "30A fused AM2 to IE1-17 / I9-10"),
        cav(8, "GND", "Cabin ground bus"),
    ], "cp_pdb", width=270),
    conn("pmu", "ECUMaster PMU-16", 0, 720, [
        cav(1, "M6", "Battery stud, 150 A total cap"),
        cav(2, "GND", "Chassis / PDB ground"),
        cav(3, "+12V SW", "Ignition switch-on (pin 7)"),
        cav(4, "O1 25A", "HEAD LH feed -> J/B2 2A-3 / 2D-2"),
        cav(5, "O2 25A", "HEAD RH feed -> J/B2 2A-6 / 2D-6"),
        cav(6, "O3 25A", "HAZ-HORN 15A bus -> J/B2 2E-3"),
        cav(7, "O4 25A", "DOME 20A bus -> J/B2 2E-4"),
        cav(8, "O5 25A", "RTR 30A bus -> J/B2 2E-2"),
        cav(9, "O8 15A", "Wiper park/brake (optional, unused yet)"),
        cav(10, "CANH", "CAN 1, 1 Mbit/s, no extra 120 ohm"),
        cav(11, "CANL", "CAN 1"),
    ], "cp_pmu", width=270),
    conn("k_eps", "EPS pump relay HCR150", 360, 180, [
        cav(1, "30", "Fused +12V in (F7 60A, Power file)"),
        cav(2, "85", "Coil - pump relay-request (Signal mrs_ctrl c3)"),
        cav(3, "86", "Coil + IG-switched 12V"),
        cav(4, "87", "+12V out, passenger fender to pump"),
        cav(5, "87a", "not used", notConnected=True),
    ], "cp_rly_hcr150", width=240),
    conn("k_fan", "Rad fan relay (uprated)", 360, 540, [
        cav(1, "30", "Fused +12V in (size to fan peak, not OEM 30A)"),
        cav(2, "85", "Coil - Aux 5 / A29"),
        cav(3, "86", "Coil + IG-switched 12V"),
        cav(4, "87", "+12V out to rad fan, engine-room C add-on"),
        cav(5, "87a", "not used", notConnected=True),
    ], "cp_rly_cod", width=240),
    conn("k_fan2", "Condenser fan relay (uprated)", 360, 900, [
        cav(1, "30", "Fused +12V in (size to fan peak, not OEM 20A)"),
        cav(2, "85", "Coil - Ign 5 / B13, diode-suppressed relay"),
        cav(3, "86", "Coil + IG-switched 12V"),
        cav(4, "87", "+12V out to condenser fan"),
        cav(5, "87a", "not used", notConnected=True),
    ], "cp_rly_cod", width=240),
    conn("rl_pos_fw", "RADLOK + firewall", 0, -240, [
        cav(1, "1", "heavy DC +"),
    ], "cp_rl_red", width=210),
    conn("rl_pos_eng", "RADLOK + engine", 720, -240, [
        cav(1, "1", "heavy DC +"),
    ], "cp_rl_red", width=210),
    conn("rl_neg_fw", "RADLOK - firewall", 0, 0, [
        cav(1, "1", "heavy DC -"),
    ], "cp_rl_blk", width=210),
    conn("rl_neg_eng", "RADLOK - engine", 720, 0, [
        cav(1, "1", "heavy DC -"),
    ], "cp_rl_blk", width=210),
    # OEM injection points - generic blocks, only the pins we land.
    conn("oem_jb2_2a", "OEM J/B2 2A (engine room main)", 1080, 180, [
        cav(2, "2", "30A CDS FAN out - DO NOT REFEED, fan moved to k_fan2", notConnected=True),
        cav(3, "3", "15A HEAD LH (inner circuit) - PMU O1"),
        cav(4, "4", "RDI FAN out - DO NOT REFEED, fan moved to k_fan", notConnected=True),
        cav(5, "5", "Engine main relay 87 - DO NOT REFEED, Link EFI in Power", notConnected=True),
        cav(6, "6", "15A HEAD RH (inner circuit) - PMU O2"),
    ], "cp_oem", width=270),
    conn("oem_jb2_2d", "OEM J/B2 2D (engine room main)", 1080, 540, [
        cav(2, "2", "15A HEAD LH twin of 2A-3 - dummy-header jumper"),
        cav(3, "3", "Headlight relay coil - unused, PMU switches the lamps", notConnected=True),
        cav(5, "5", "Rad fan relay coil - unused after fan move", notConnected=True),
        cav(6, "6", "15A HEAD RH twin of 2A-6 - dummy-header jumper"),
    ], "cp_oem", width=270),
    conn("oem_jb2_2e", "OEM J/B2 2E (engine room main)", 1080, 900, [
        cav(2, "2", "PROBE: inner cct = 30A RTR; starting p.48 = AM1 with 2E-5"),
        cav(3, "3", "PROBE: inner cct = 15A HAZ-HORN; starting p.48 = AM2 with 2E-6"),
        cav(4, "4", "20A DOME (inner circuit, not on AM1/AM2 path) - PMU O4"),
        cav(5, "5", "AM1 pass-through (starting p.48). Do not PMU-feed. Restored at IE1-10", notConnected=True),
        cav(6, "6", "AM2 / engine-main related. Do not PMU-feed. Restored at IE1-17", notConnected=True),
        cav(8, "8", "15A EFI - unused, Link EFI relay in cabin", notConnected=True),
    ], "cp_oem", width=270),
    conn("oem_jb1_1i", "OEM J/B1 1I (left kick, ER main)", 1440, 180, [
        cav(1, "1", "Always-hot B from FL ALT - PRIMARY J/B1 B+"),
    ], "cp_oem", width=270),
    conn("oem_jb1_1h", "OEM J/B1 1H (left kick, ER main)", 1440, 420, [
        cav(7, "7", "IG2 B-O from ignition switch - keep, do not overlay"),
        cav(8, "8", "Always-hot related bus"),
    ], "cp_oem", width=270),
    conn("oem_ie1", "OEM IE1 (left kick, ER main <-> cowl)", 1440, 720, [
        cav(10, "10", "W  AM1 to ignition I9-4"),
        cav(17, "17", "B-R AM2 to ignition I9-10"),
    ], "cp_oem", width=270),
    conn("oem_rb4", "OEM R/B4 (right kick, by glove box)", 1440, 1020, [
        cav(1, "HTR1", "40A HEATER fuse input"),
        cav(2, "HTR2", "Heater fuse output / heater relay 30"),
        cav(3, "STR", "OEM starter relay - isolate, Link k_str replaces"),
    ], "cp_oem", width=270),
    conn("oem_rb2", "OEM R/B2 (left kick)", 1440, 1320, [
        cav(1, "PWR1", "30A POWER fuse input"),
        cav(2, "PWR2", "Power fuse output / power main relay 30"),
    ], "cp_oem", width=270),
    conn("mrs_pwr", "MRS EPS pump power 90980-12068", 1800, 180, [
        cav(1, "1", "12V from k_eps 87, 8 AWG, passenger fender"),
        cav(2, "2", "GND, 8 AWG to engine block / EB"),
    ], "cp_mrs_pwr", width=270),
    conn("mrs_en", "MRS EPS enable 90980-10942", 1800, 420, [
        cav(1, "1", "IG-switched 7.5A F13"),
        cav(2, "2", "unused", notConnected=True),
    ], "cp_mrs_en", width=240),
    conn("rad_fan", "Uprated radiator fan", 1800, 720, [
        cav(1, "12V", "From k_fan 87, 8 AWG"),
        cav(2, "GND", "To EA / engine-room ground, 8 AWG"),
    ], "cp_fan", width=240),
    conn("fan2", "Uprated condenser fan", 1800, 960, [
        cav(1, "12V", "From k_fan2 87, 8 AWG"),
        cav(2, "GND", "To EA / engine-room ground, 8 AWG"),
    ], "cp_fan", width=240),
    conn("jump_pos", "Engine-bay jump post", 720, -480, [
        cav(1, "1", "Tied to starter B+ / RADLOK +"),
    ], "cp_jump", width=210),
]

terminals = [
    term("t_trunk_pos", "Ring", "Trunk battery +  (2 AWG or 1/0, jump lug)", -360, -240),
    term("t_trunk_neg", "Ring", "Trunk battery -  (2 AWG or 1/0, jump lug)", -360, 0),
    term("t_starter_b", "Ring", "Starter B+ post, jump lug, 2 AWG", 1080, -240),
    term("t_alt_b", "Ring", "160 A alternator B+, 4 AWG to starter B+", 1440, -240),
    term("t_eng_block", "Ring", "Engine block ground stud, 2 AWG, jump lug", 1080, 0),
    term("t_gnd_ea", "Ring", "OEM ground EA - right front fender", 1800, 1260),
    term("t_gnd_eb", "Ring", "OEM ground EB - left front fender", 1800, 1440),
    term("t_gnd_id", "Ring", "OEM ground ID - left kick panel", 1800, 1620),
    term("t_gnd_ig", "Ring", "OEM ground IG - R/B4 set bolt, right kick", 1800, 1800),
]

wires = [
    wire("w_trunk_pos", "Red", "t_trunk_pos", "Terminal", "pdb", "c1"),
    wire("w_trunk_neg", "Black", "t_trunk_neg", "Terminal", "pdb", "c8"),
    wire("w_pdb_rlp", "Red", "pdb", "c2", "rl_pos_fw", "c1"),
    wire("w_rlp", "Red", "rl_pos_fw", "c1", "rl_pos_eng", "c1"),
    wire("w_rlp_str", "Red", "rl_pos_eng", "c1", "t_starter_b", "Terminal"),
    wire("w_alt", "Red", "t_alt_b", "Terminal", "t_starter_b", "Terminal"),
    wire("w_jump", "Red", "t_starter_b", "Terminal", "jump_pos", "c1"),
    wire("w_pdb_rln", "Black", "pdb", "c8", "rl_neg_fw", "c1"),
    wire("w_rln", "Black", "rl_neg_fw", "c1", "rl_neg_eng", "c1"),
    wire("w_rln_blk", "Black", "rl_neg_eng", "c1", "t_eng_block", "Terminal"),
    # k_eps / k_fan 30 and 86 live in ST185-Power.harness (cabin fuse block).
    # This file only owns 87 -> engine-room loads and the OEM injection.
    wire("w_pdb_pmu", "Red", "pdb", "c4", "pmu", "c1"),
    wire("w_pmu_gnd", "Black", "pmu", "c2", "pdb", "c8"),
    wire("w_pdb_jb1", "White", "pdb", "c5", "oem_jb1_1i", "c1"),
    wire("w_pdb_am1", "White", "pdb", "c6", "oem_ie1", "c10"),
    wire("w_pdb_am2", "Brown", "pdb", "c7", "oem_ie1", "c17"),
    # Handles match cav(N) -> id cN. 2A-3 = HEAD LH, 2A-6 = HEAD RH (EWD p.21).
    wire("w_pmu_hl", "Red", "pmu", "c4", "oem_jb2_2a", "c3"),
    wire("w_pmu_hr", "Red", "pmu", "c5", "oem_jb2_2a", "c6"),
    wire("w_hl_twin", "Red", "oem_jb2_2a", "c3", "oem_jb2_2d", "c2"),
    wire("w_hr_twin", "Red", "oem_jb2_2a", "c6", "oem_jb2_2d", "c6"),
    # DOME 2E-4 is not on the AM1/AM2 pass-through. RTR 2E-2 and HAZ 2E-3 collide
    # with starting p.48 AM1/AM2 pins - land only after the on-car probe.
    wire("w_pmu_dome", "Red", "pmu", "c7", "oem_jb2_2e", "c4"),
    wire("w_pmu_horn", "Red", "pmu", "c6", "oem_jb2_2e", "c3"),
    wire("w_pmu_rtr", "Red", "pmu", "c8", "oem_jb2_2e", "c2"),
    wire("w_eps_pwr", "Red", "k_eps", "c4", "mrs_pwr", "c1"),
    wire("w_eps_gnd", "Black", "mrs_pwr", "c2", "t_eng_block", "Terminal"),
    wire("w_fan_pwr", "Red", "k_fan", "c4", "rad_fan", "c1"),
    wire("w_fan_gnd", "Black", "rad_fan", "c2", "t_gnd_ea", "Terminal"),
    wire("w_fan2_pwr", "Red", "k_fan2", "c4", "fan2", "c1"),
    wire("w_fan2_gnd", "Black", "fan2", "c2", "t_gnd_ea", "Terminal"),
    wire("w_rb4", "Red", "pdb", "c3", "oem_rb4", "c1"),
    wire("w_rb2", "Red", "pdb", "c3", "oem_rb2", "c1"),
    wire("w_gnd_id", "Black", "pdb", "c8", "t_gnd_id", "Terminal"),
    wire("w_gnd_ig", "Black", "pdb", "c8", "t_gnd_ig", "Terminal"),
    wire("w_gnd_eb", "Black", "t_eng_block", "Terminal", "t_gnd_eb", "Terminal"),
]

mates = [
    mate("m_rlp", "rl_pos_fw", "rl_pos_eng"),
    mate("m_rln", "rl_neg_fw", "rl_neg_eng"),
]

notes = [
    note("n_intro",
         "ENGINE ROOM HARNESS C - PARTIAL. Only new / upgraded / relocated feeds. "
         "Do not redraw the OEM engine-room, cowl or dash looms. Kick-panel J/B No.1, "
         "R/B No.2 / No.3 / No.4 stay. Unplug engine-bay J/B No.2 and F11; inject at "
         "the pins in the splice table (docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md).",
         -360, -720, 540),
    note("n_heavy",
         "HEAVY DC: trunk battery -> cabin PDB (glove box) -> RADLOK 5.7 mm through the "
         "firewall -> starter B+. 160 A alt B+ joins the starter post and does not recross. "
         "Jump lugs at trunk battery, PDB, starter, engine block, and the engine-bay jump post. "
         "2 AWG is OK for cranking; 160 A continuous charge may need 1/0 + 8 mm RADLOK - see the table.",
         -360, -960, 540, "Orange"),
    note("n_split",
         "EPS 12 V / GND ride the passenger fender in the vacated ABS actuator space. "
         "Fans ride the core-support run of the OEM engine-room main. A/C compressor clutch "
         "stays on engine harness A/B (Power/Signal files). Crash sensors and ABS solenoid "
         "are deleted - do not refeed 60A FL ABS, A7/A8, A11/A12, A37.",
         1080, -720, 540, "Green"),
    note("shdr_0", "TRUNK + GLOVE BOX", -360, -480, 270, "Green"),
    note("shdr_1", "FIREWALL RADLOK", 0, -480, 270, "Orange"),
    note("n_probe",
         "PROBE BEFORE CRIMPING 2E-2 / 2E-3. Starting + ignition (EWD p.48) puts AM1 on "
         "2E-2/2E-5 and AM2 on 2E-3/2E-6, then IE1-10 / IE1-17. Inner circuit (p.21) puts "
         "30A RTR on 2E-2 and 15A HAZ-HORN on 2E-3. If the unplugged 2E-2 shows continuity "
         "to IE1-10, that pin is AM1 - do not land PMU O5 there. Same for 2E-3 vs IE1-17 / AM2. "
         "HEAD 2A-3/2A-6 and DOME 2E-4 do not sit on that pass-through. Horn fallback is R/B5.",
         1080, -1020, 540, "Red"),
    note("shdr_2", "OEM INJECTION (keep J/Bs)", 1080, -60, 300, "Red"),
    note("shdr_3", "NEW ENGINE-ROOM LOADS", 1800, -60, 270, "Blue"),
]

parts = [
    {"id": "cp_pdb", "partNumber": "PDB-M8x8", "manufacturer": "TBD",
     "description": "8-stud power distribution block at glove box, M8, 150-250 A bus"},
    {"id": "cp_pmu", "partNumber": "PMU-16", "manufacturer": "ECUMaster",
     "description": "10x25A + 6x15A high-side, 150A total, M6 stud + 39-way. On CAN 1 at 1 Mbit/s, no third terminator."},
    {"id": "cp_rly_hcr150", "partNumber": "V23132-A2001-B200", "manufacturer": "TE Connectivity",
     "description": "HCR 150 12VDC 37 ohm / 3.9W, internal suppression. OWNED mating TBD."},
    {"id": "cp_rly_cod", "partNumber": "V23074 / 5-1393292-8", "manufacturer": "TE Connectivity",
     "description": "Micro ISO diode-suppressed relay, fan coils."},
    {"id": "cp_rl_red", "partNumber": "RL00571-35 red shell", "manufacturer": "Amphenol",
     "description": "RADLOK 5.7mm RADSOK bulkhead pair, red, 2 AWG / 25 mm2"},
    {"id": "cp_rl_blk", "partNumber": "RL00571-35 black shell", "manufacturer": "Amphenol",
     "description": "RADLOK 5.7mm RADSOK bulkhead pair, black, 2 AWG / 25 mm2"},
    {"id": "cp_oem", "partNumber": "(OEM block)", "manufacturer": "Toyota",
     "description": "Generic OEM block - only the pins this harness lands. No invented J/B internals."},
    {"id": "cp_mrs_pwr", "partNumber": "90980-12068", "manufacturer": "Toyota / Sumitomo",
     "description": "MR-S EHPS pump main power. OWNED."},
    {"id": "cp_mrs_en", "partNumber": "90980-10942", "manufacturer": "Toyota / Sumitomo",
     "description": "MR-S EHPS pump enable. OWNED."},
    {"id": "cp_fan", "partNumber": "DT06-2S", "manufacturer": "Deutsch",
     "description": "2-way sealed fan power. Confirm against the fan that is actually fitted."},
    {"id": "cp_jump", "partNumber": "jump-post-M8", "manufacturer": "TBD",
     "description": "Engine-bay jump / accessory post on starter B+ net."},
]

doc = {
    "$schema": "https://docs.harness.design/files/harness/schema/v0.9.json",
    "$docs": "https://docs.harness.design/files/harness/editing-guide.md",
    "version": 0.9,
    "lengthUnit": "mm",
    "wires": wires,
    "connectors": connectors,
    "terminals": terminals,
    "mates": mates,
    "schematicNotes": notes,
    "connectorParts": parts,
}

ids = []
for key in ("wires", "connectors", "terminals", "mates", "schematicNotes", "connectorParts"):
    ids.extend(x["id"] for x in doc[key])
assert len(ids) == len(set(ids)), "duplicate ids"

cavities = {}
for c in connectors:
    cavities[c["id"]] = {cv["id"] for cv in c["cavities"]}
term_ids = {t["id"] for t in terminals}
for w in wires:
    for end, key in (("source", "source"), ("target", "target")):
        e = w[key]
        nid, h = e["id"], e["handle"]
        if h == "Terminal":
            assert nid in term_ids, f"{w['id']} {end} terminal {nid} missing"
        else:
            assert nid in cavities, f"{w['id']} {end} connector {nid} missing"
            assert h in cavities[nid], f"{w['id']} {end} {nid}.{h} not a cavity (have {sorted(cavities[nid])})"

OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
print(f"wrote {OUT}  connectors={len(connectors)} wires={len(wires)} terminals={len(terminals)}")
