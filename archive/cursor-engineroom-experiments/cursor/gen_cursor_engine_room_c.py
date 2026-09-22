#!/usr/bin/python3
"""New Cursor engine-room C drawings. Does not modify existing .harness files.

Free-plan cap is 100 connections per file, so this writes three documents:

  ST185-cursor-EngineRoom-C-heavy-dc.harness
  ST185-cursor-EngineRoom-C-oem-inject.harness
  ST185-cursor-EngineRoom-C-loads.harness

Regenerate: python3 docs/harness/gen_cursor_engine_room_c.py
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_URL = "https://docs.harness.design/files/harness/schema/v0.9.json"
DOCS_URL = "https://docs.harness.design/files/harness/editing-guide.md"
SCHEMA_PATH = Path("/tmp/harness-schema.json")
OUT_DIR = Path(__file__).resolve().parent

W = 270
N = 390


def pos(x, y):
    return {"x": x, "y": y}


def gauge(awg):
    return {"unit": "AWG", "value": awg}


def cav(i, desig, signal, contact, plug=None, nc=False):
    d = {
        "id": f"c{i}",
        "designation": str(desig),
        "signal": signal,
        "contactPartId": None if nc and plug else contact,
    }
    if nc:
        d["notConnected"] = True
        if plug:
            d["cavityPlugPartId"] = plug
            d["contactPartId"] = None
    return d


def conn(cid, label, x, y, cavities, part_id, width=W):
    return {
        "id": cid,
        "label": label,
        "width": width,
        "partId": part_id,
        "schematicPosition": pos(x, y),
        "layoutPosition": pos(x, y + 3000),
        "cavities": cavities,
    }


def term(tid, typ, signal, x, y, part_id, width=210):
    return {
        "id": tid,
        "type": typ,
        "signal": signal,
        "width": width,
        "partId": part_id,
        "schematicPosition": pos(x, y),
        "layoutPosition": pos(x, y + 3000),
    }


def splice(sid, x, y, part_id="sp_solder"):
    return {
        "id": sid,
        "partId": part_id,
        "schematicPosition": pos(x, y),
        "layoutPosition": pos(x, y + 3000),
    }


def wire(wid, color, src, sh, tgt, th, part_id, stripe=None):
    w = {
        "id": wid,
        "color": color,
        "partId": part_id,
        "source": {"id": src, "handle": sh},
        "target": {"id": tgt, "handle": th},
    }
    if stripe:
        w["stripeColor"] = stripe
    return w


def note(nid, text, x, y, width=N, color=None):
    n = {"id": nid, "text": text, "width": width, "schematicPosition": pos(x, y)}
    if color:
        n["color"] = color
    return n


def mate(mid, a, b):
    return {"id": mid, "sourceId": a, "targetId": b}


def wp(pid, pn, mfr, desc, color, awg):
    return {
        "id": pid,
        "partNumber": pn,
        "manufacturer": mfr,
        "description": desc,
        "color": color,
        "gauge": gauge(awg),
    }


def cpart(pid, pn, mfr, desc, cavities=None, gender=None):
    d = {"id": pid, "partNumber": pn, "manufacturer": mfr, "description": desc}
    if cavities:
        d["numberOfCavities"] = cavities
    if gender:
        d["gender"] = gender
    return d


def ct(pid, pn, mfr, desc, gender, lo, hi):
    return {
        "id": pid,
        "partNumber": pn,
        "manufacturer": mfr,
        "description": desc,
        "gender": gender,
        "type": "Crimp",
        "minGauge": gauge(lo),
        "maxGauge": gauge(hi),
    }


def tpart(pid, pn, mfr, desc, typ, lo, hi):
    return {
        "id": pid,
        "partNumber": pn,
        "manufacturer": mfr,
        "description": desc,
        "type": typ,
        "minGauge": gauge(lo),
        "maxGauge": gauge(hi),
    }


# Shared library — real PNs from this repo's Power/BOM where they exist;
# added parts are named with manufacturer + function when the housing is OEM or TBD.
CONTACTS = [
    ct("ct_radsok", "RADSOK 5.7mm 2 AWG", "Amphenol",
       "RADSOK contact supplied with RL00571-35", "Socket", 2, 2),
    ct("ct_sicma28", "15324724", "Aptiv",
       "Sicma 2.8 female, 12-14 AWG, 25 A — PMU-16 high-side outputs", "Socket", 12, 14),
    ct("ct_sicma15", "282403-1", "TE Connectivity",
       "Superseal 1.5 / Sicma 1.5 female, 18-20 AWG — PMU CAN, IGN, GND pin", "Socket", 18, 20),
    ct("ct_iso_pwr", "280756-4", "TE Connectivity",
       "250-series female 12-10 AWG — Micro ISO 30/87 (on hand extra list)", "Socket", 10, 12),
    ct("ct_iso_coil", "180360-0", "TE Connectivity",
       "6.3 mm female 20-16 AWG — Micro ISO coil 85/86", "Socket", 16, 20),
    ct("ct_hcr_pwr", "HCR150-PWR-8AWG", "TE Connectivity",
       "HCR 150 power contact 8-10 AWG for 30/87 — confirm kit with TE for V23132-A2001-B200",
       "Socket", 8, 10),
    ct("ct_hcr_coil", "HCR150-COIL", "TE Connectivity",
       "HCR 150 coil contact 16-20 AWG for 85/86 — confirm kit with TE", "Socket", 16, 20),
    ct("ct_dthd8s", "0462-203-08141", "TE DEUTSCH",
       "Size 8 solid SOCKET, 8-10 AWG, 60 A — OWNED (qty 9)", "Socket", 8, 10),
    ct("ct_toy_pwr", "Sumitomo 090 8mm F", "Sumitomo",
       "Large 090 female 8-10 AWG for 90980-12068 EPS power (pigtail 82998-12500)",
       "Socket", 8, 10),
    ct("ct_toy_ts", "TS 2.3 (090 type)", "Sumitomo",
       "Toyota/Denso 2.3 mm female — J/B dummy header and 90980-10942 / 10897",
       "Socket", 16, 20),
    ct("ct_midi", "MIDI-M8-RING", "Littelfuse",
       "M8 ring on MIDI/ANL fuse holder stud, 2-4 AWG", "Socket", 2, 4),
    ct("ct_pdb_ring", "LCA2-14-Q", "Panduit",
       "2 AWG copper lug, 1/4 in / M8 stud — PDB and battery posts", "Socket", 2, 2),
    ct("ct_fuse_in", "968855-1", "TE Connectivity",
       "TE 2141029-1 fuse-box hard-wire contact, 12-10 AWG", "Socket", 10, 12),
    ct("ct_dtm20s", "0462-201-2031", "TE DEUTSCH",
       "Size 20 solid SOCKET, 20 AWG — CAN tap DTM", "Socket", 20, 20),
]
PLUGS = [
    cpart("pl_sz8", "114018-ZZ", "TE DEUTSCH", "Sealing plug, size 8, white"),
    cpart("pl_sz16", "114017", "TE DEUTSCH", "Sealing plug, size 16, white"),
    cpart("pl_sz20", "0413-204-2005", "TE DEUTSCH", "Sealing plug, size 20, red"),
    cpart("pl_toy", "(OEM cavity plug)", "Toyota", "Blank cavity in reused OEM J/B2 plug"),
]
TERMINAL_PARTS = [
    tpart("tp_ring2_m8", "LCA2-14-Q", "Panduit", "2 AWG ring, M8 / 1/4 in stud, jump lug", "Ring", 2, 2),
    tpart("tp_ring4_m8", "LCA4-14-L", "Panduit", "4 AWG ring, M8 stud — 160 A alt B+", "Ring", 4, 4),
    tpart("tp_ring8_m8", "LCA8-14-L", "Panduit", "8 AWG ring, M8 stud — EPS / fan grounds", "Ring", 8, 8),
    tpart("tp_ring2_m6", "LCA2-10-Q", "Panduit", "2 AWG ring, M6 stud — PMU-16 battery stud", "Ring", 2, 2),
    tpart("tp_qc_ig", "640903-1", "TE Connectivity", "Faston 6.3 mm tap for IG-ON / Aux coil leads",
          "QuickConnectFemale", 16, 18),
]
SPLICE_PARTS = [
    {"id": "sp_solder", "partNumber": "D-181-32", "manufacturer": "TE Raychem",
     "description": "Solder-sleeve splice, sealed, 12-18 AWG family",
     "minGauge": gauge(12), "maxGauge": gauge(18)},
    {"id": "sp_heavy", "partNumber": "B-106-11", "manufacturer": "TE Raychem",
     "description": "Heavy solder-sleeve / crimp splice, 8-4 AWG",
     "minGauge": gauge(4), "maxGauge": gauge(8)},
]
WIRES_COMMON = [
    wp("wp_2r", "TXL-2-RED", "generic", "2 AWG TXL / welding cable, battery and RADLOK", "Red", 2),
    wp("wp_2b", "TXL-2-BLK", "generic", "2 AWG TXL / welding cable, battery negative", "Black", 2),
    wp("wp_4r", "TXL-4-RED", "generic", "4 AWG TXL, 160 A alternator B+ to starter", "Red", 4),
    wp("wp_8r", "TXL-8-RED", "generic", "8 AWG TXL, EPS pump and uprated fans +", "Red", 8),
    wp("wp_8b", "TXL-8-BLK", "generic", "8 AWG TXL, EPS pump and uprated fans −", "Black", 8),
    wp("wp_10r", "TXL-10-RED", "generic", "10 AWG TXL, AM1/AM2/OEM-HOT body feeds", "Red", 10),
    wp("wp_12r", "TXL-12-RED", "generic", "12 AWG TXL, HEAD / DOME / HAZ PMU outputs", "Red", 12),
    wp("wp_14w", "TXL-14-WHT", "generic", "14 AWG TXL, AM1 (factory W)", "White", 14),
    wp("wp_14br", "TXL-14-BRN", "generic", "14 AWG TXL, AM2 (factory B–R)", "Brown", 14),
    wp("wp_18b", "TXL-18-BLK", "generic", "18 AWG TXL, grounds and relay coils −", "Black", 18),
    wp("wp_18r", "TXL-18-RED", "generic", "18 AWG TXL, relay coils + / EPS enable", "Red", 18),
    wp("wp_20w", "TXL-20-WHT", "generic", "20 AWG TXL, CAN 1 tap", "White", 20),
    wp("wp_20g", "TXL-20-GRN", "generic", "20 AWG TXL, CAN 1 L tap", "Green", 20),
]


def dump(name, title, drawing, connectors, terminals, wires, notes, extra):
    doc = {
        "$schema": SCHEMA_URL,
        "$docs": DOCS_URL,
        "version": 0.9,
        "lengthUnit": "mm",
        "gaugeUnit": "AWG",
        "titleBlock": {
            "company": "ST185 TrackCluster",
            "title": title,
            "drawingNumber": drawing,
            "date": "2026-09-17",
            "drawnBy": "cursor",
        },
        "wires": wires,
        "connectors": connectors,
        "terminals": terminals,
        "splices": extra.get("splices", []),
        "mates": extra.get("mates", []),
        "schematicNotes": notes,
        "connectorParts": extra["connectorParts"],
        "contactParts": CONTACTS,
        "cavityPlugParts": PLUGS,
        "terminalParts": TERMINAL_PARTS,
        "spliceParts": SPLICE_PARTS,
        "wireParts": WIRES_COMMON,
    }
    ids = []
    for key in ("wires", "connectors", "terminals", "splices", "mates", "schematicNotes",
                "connectorParts", "contactParts", "cavityPlugParts", "terminalParts",
                "spliceParts", "wireParts"):
        ids.extend(x["id"] for x in doc.get(key, []))
    assert len(ids) == len(set(ids)), f"{name}: duplicate ids"

    cavs = {c["id"]: {cv["id"] for cv in c["cavities"]} for c in connectors}
    terms = {t["id"] for t in terminals}
    sps = {s["id"] for s in extra.get("splices", [])}
    for w in wires:
        for end in ("source", "target"):
            nid, h = w[end]["id"], w[end]["handle"]
            if h == "Terminal":
                assert nid in terms, f"{name} {w['id']} {end} missing terminal {nid}"
            elif h == "Splice":
                assert nid in sps, f"{name} {w['id']} {end} missing splice {nid}"
            else:
                assert nid in cavs, f"{name} {w['id']} {end} missing connector {nid}"
                assert h in cavs[nid], f"{name} {w['id']} {end} {nid}.{h}"
        assert w.get("partId"), f"{name} {w['id']} missing wire part"

    for c in connectors:
        assert c.get("partId"), f"{name} {c['id']} missing connector part"
        for cv in c["cavities"]:
            if cv.get("notConnected"):
                assert cv.get("cavityPlugPartId"), f"{name} {c['id']}.{cv['id']} NC needs plug"
            else:
                assert cv.get("contactPartId"), f"{name} {c['id']}.{cv['id']} live cavity needs contact"

    for t in terminals:
        assert t.get("partId"), f"{name} {t['id']} missing terminal part"

    assert len(wires) <= 100, f"{name} has {len(wires)} wires"

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(doc)

    path = OUT_DIR / name
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.name:52} connectors={len(connectors):2} wires={len(wires):2} "
          f"terminals={len(terminals):2} splices={len(extra.get('splices', [])):2}")


def heavy_dc():
    plugs = []  # no unused cavities
    connectors = [
        conn("pdb", "Cabin PDB (glove box) — heavy DC studs", 0, 180, [
            cav(1, "BAT+", "From trunk + / ANL 200 A out", "ct_pdb_ring"),
            cav(2, "ALT/STR", "To RADLOK +  (starter / 160 A alt)", "ct_pdb_ring"),
            cav(3, "FUSE IN", "To TE 2141029-1 IN (Power file F1–F13)", "ct_pdb_ring"),
            cav(4, "GND", "Cabin ground bus / RADLOK −", "ct_pdb_ring"),
        ], "cp_pdb"),
        conn("anl_main", "ANL 200 A (PDB charge/start feed)", -360, 180, [
            cav(1, "IN", "From trunk battery +", "ct_midi"),
            cav(2, "OUT", "To PDB BAT+", "ct_midi"),
        ], "cp_anl200", width=210),
        conn("rl_pos_fw", "RADLOK + firewall", 360, -60, [
            cav(1, "1", "heavy DC +", "ct_radsok"),
        ], "cp_rl_red", width=210),
        conn("rl_pos_eng", "RADLOK + engine", 720, -60, [
            cav(1, "1", "heavy DC +", "ct_radsok"),
        ], "cp_rl_red", width=210),
        conn("rl_neg_fw", "RADLOK − firewall", 360, 180, [
            cav(1, "1", "heavy DC −", "ct_radsok"),
        ], "cp_rl_blk", width=210),
        conn("rl_neg_eng", "RADLOK − engine", 720, 180, [
            cav(1, "1", "heavy DC −", "ct_radsok"),
        ], "cp_rl_blk", width=210),
        conn("jump_pos", "Engine-bay jump post", 1080, -240, [
            cav(1, "1", "Tied to starter B+", "ct_pdb_ring"),
        ], "cp_jump", width=210),
        conn("fb_in", "TE 2141029-1 fuse block IN", 360, 420, [
            cav(1, "IN", "Cabin fuse block battery feed", "ct_fuse_in"),
        ], "cp_fusebox", width=210),
    ]
    terminals = [
        term("t_trunk_pos", "Ring", "Trunk battery +  (jump lug)", -720, -60, "tp_ring2_m8"),
        term("t_trunk_neg", "Ring", "Trunk battery −  (jump lug)", -720, 180, "tp_ring2_m8"),
        term("t_starter", "Ring", "Starter B+ post, jump lug", 1080, -60, "tp_ring2_m8"),
        term("t_alt", "Ring", "160 A alternator B+ (does not recross firewall)", 1440, -60, "tp_ring4_m8"),
        term("t_block", "Ring", "Engine block ground stud, jump lug", 1080, 180, "tp_ring2_m8"),
    ]
    wires = [
        wire("W1", "Red", "t_trunk_pos", "Terminal", "anl_main", "c1", "wp_2r"),
        wire("W2", "Red", "anl_main", "c2", "pdb", "c1", "wp_2r"),
        wire("W3", "Black", "t_trunk_neg", "Terminal", "pdb", "c4", "wp_2b"),
        wire("W4", "Red", "pdb", "c2", "rl_pos_fw", "c1", "wp_2r"),
        wire("W5", "Red", "rl_pos_fw", "c1", "rl_pos_eng", "c1", "wp_2r"),
        wire("W6", "Red", "rl_pos_eng", "c1", "t_starter", "Terminal", "wp_2r"),
        wire("W7", "Red", "t_alt", "Terminal", "t_starter", "Terminal", "wp_4r"),
        wire("W8", "Red", "t_starter", "Terminal", "jump_pos", "c1", "wp_2r"),
        wire("W9", "Black", "pdb", "c4", "rl_neg_fw", "c1", "wp_2b"),
        wire("W10", "Black", "rl_neg_fw", "c1", "rl_neg_eng", "c1", "wp_2b"),
        wire("W11", "Black", "rl_neg_eng", "c1", "t_block", "Terminal", "wp_2b"),
        wire("W12", "Red", "pdb", "c3", "fb_in", "c1", "wp_2r"),
    ]
    notes = [
        note("n0", "ST185 cursor Engine Room C — HEAVY DC. Trunk battery, glove-box PDB, "
             "RADLOK 5.7 mm through the firewall, starter B+, 160 A alt, jump post. "
             "Does not redraw OEM looms.", -720, -420, N, "Orange"),
        note("n1", "2 AWG is enough for cranking. 160 A continuous charge may need 1/0 + 8 mm "
             "RADLOK — do not order a second 5.7 mm pair until that is decided.", -720, -540, N, "Orange"),
        note("h0", "TRUNK", -720, -240, 210, "Green"),
        note("h1", "GLOVE BOX", -360, -240, 210, "Green"),
        note("h2", "FIREWALL", 360, -240, 210, "Orange"),
        note("h3", "ENGINE", 1080, -420, 210, "Red"),
    ]
    extra = {
        "mates": [mate("m_rlp", "rl_pos_fw", "rl_pos_eng"), mate("m_rln", "rl_neg_fw", "rl_neg_eng")],
        "connectorParts": [
            cpart("cp_pdb", "PDB-M8x8", "TBD",
                  "8-stud power distribution block, M8, 150–250 A bus, glove box", 8),
            cpart("cp_anl200", "ANL-200 + holder", "Littelfuse",
                  "ANL 200 A fuse + M8 holder on PDB charge/start feed", 2),
            cpart("cp_rl_red", "RL00571-35 red shell", "Amphenol",
                  "RADLOK 5.7 mm RADSOK bulkhead, red, 2 AWG / 25 mm²", 1),
            cpart("cp_rl_blk", "RL00571-35 black shell", "Amphenol",
                  "RADLOK 5.7 mm RADSOK bulkhead, black, 2 AWG / 25 mm²", 1),
            cpart("cp_jump", "jump-post-M8", "TBD", "Engine-bay jump / accessory post on starter B+ net", 1),
            cpart("cp_fusebox", "2141029-1", "TE Connectivity",
                  "Fuse box assembly, hard wired — OWNED. This drawing only lands IN.", 1, "Female"),
        ],
        "splices": [],
    }
    dump("ST185-cursor-EngineRoom-C-heavy-dc.harness",
         "ST185 cursor Engine Room C — heavy DC (trunk / PDB / RADLOK / starter / alt)",
         "ER-C-CURSOR-HEAVY-DC", connectors, terminals, wires, notes, extra)


def oem_inject():
    pmu_cavs = []
    # O1-O10 25A Sicma 2.8; O11-O16 15A; then GND, IGN, CAN
    labels = [
        (1, "O1", "HEAD LH -> J/B2 2A-3 / 2D-2", False),
        (2, "O2", "HEAD RH -> J/B2 2A-6 / 2D-6", False),
        (3, "O3", "HAZ-HORN -> 2E-3 PROBE vs AM2 first", False),
        (4, "O4", "DOME -> J/B2 2E-4", False),
        (5, "O5", "RTR -> 2E-2 PROBE vs AM1 first", False),
    ]
    for i in range(6, 17):
        labels.append((i, f"O{i}", f"PMU output {i} unused in this loom", True))
    labels += [
        (17, "GND", "PMU chassis / PDB ground", False),
        (18, "IGN", "Switch-on enable (pin 7 family) after AM2 restore", False),
        (19, "CANH", "CAN 1 H — tap existing bus, no third 120 ohm", False),
        (20, "CANL", "CAN 1 L", False),
    ]
    for i, des, sig, nc in labels:
        contact = "ct_sicma28" if i <= 16 else "ct_sicma15"
        pmu_cavs.append(cav(i, des, sig, contact, plug="pl_sz16", nc=nc))

    connectors = [
        conn("pdb", "Cabin PDB — body-feed studs", -360, 180, [
            cav(1, "BODY+", "From heavy-DC PDB BAT+ stud", "ct_pdb_ring"),
            cav(2, "GND", "From heavy-DC PDB GND stud", "ct_pdb_ring"),
        ], "cp_pdb", width=210),
        conn("f_hot", "MIDI 50 A OEM HOT (1I-1)", 0, -60, [
            cav(1, "IN", "Always-hot to J/B1", "ct_midi"),
            cav(2, "OUT", "To OEM 1I pin 1", "ct_midi"),
        ], "cp_midi50", width=210),
        conn("f_am1", "MIDI 40 A AM1 (replaces FL AM1)", 0, 180, [
            cav(1, "IN", "AM1 supply", "ct_midi"),
            cav(2, "OUT", "To OEM IE1 pin 10", "ct_midi"),
        ], "cp_midi40", width=210),
        conn("f_am2", "MIDI 30 A AM2 (replaces FL AM2)", 0, 420, [
            cav(1, "IN", "AM2 supply", "ct_midi"),
            cav(2, "OUT", "To OEM IE1 pin 17", "ct_midi"),
        ], "cp_midi30", width=210),
        conn("f_pmu", "ANL 150 A PMU-16 M6 input", 0, 660, [
            cav(1, "IN", "From PDB BODY+", "ct_midi"),
            cav(2, "OUT", "To PMU M6 stud", "ct_midi"),
        ], "cp_anl150", width=210),
        conn("pmu", "ECUMaster PMU-16 harness plug", 360, 180, pmu_cavs, "cp_pmu", width=390),
        conn("can_tap", "CAN 1 tap (existing bus)", 720, 660, [
            cav(1, "H", "Twisted with L — 1 Mbit/s, no extra terminator", "ct_dtm20s"),
            cav(2, "L", "Twisted with H", "ct_dtm20s"),
        ], "cp_dtm2", width=210),
        conn("oem_1i", "OEM J/B1 1I (left kick) — pin 1 only", 1080, -60, [
            cav(1, "1", "Always-hot B into STOP / ECU-B / DEFOGGER / tail-relay B+", "ct_toy_ts"),
        ], "cp_oem_1i", width=270),
        conn("oem_ie1", "OEM IE1 (left kick ER main ↔ cowl)", 1080, 180, [
            cav(10, "10", "W  AM1 to ignition I9-4", "ct_toy_ts"),
            cav(17, "17", "B–R AM2 to ignition I9-10", "ct_toy_ts"),
        ], "cp_oem_ie1", width=270),
        conn("oem_2a", "OEM J/B2 2A dummy header (ER main)", 1080, 420, [
            cav(2, "2", "CDS FAN — DO NOT REFEED", "ct_toy_ts", "pl_toy", True),
            cav(3, "3", "15A HEAD LH (inner circuit p.21)", "ct_toy_ts"),
            cav(4, "4", "RDI FAN — DO NOT REFEED", "ct_toy_ts", "pl_toy", True),
            cav(5, "5", "Engine main 87 — Link EFI in Power", "ct_toy_ts", "pl_toy", True),
            cav(6, "6", "15A HEAD RH (inner circuit p.21)", "ct_toy_ts"),
        ], "cp_oem_2a"),
        conn("oem_2d", "OEM J/B2 2D dummy header (ER main)", 1080, 780, [
            cav(1, "1", "Unused in inner circuit", "ct_toy_ts", "pl_toy", True),
            cav(2, "2", "HEAD LH twin of 2A-3 — dummy jumper required", "ct_toy_ts"),
            cav(3, "3", "Headlight relay coil — unused, PMU switches lamps", "ct_toy_ts", "pl_toy", True),
            cav(5, "5", "Rad fan relay coil — unused", "ct_toy_ts", "pl_toy", True),
            cav(6, "6", "HEAD RH twin of 2A-6 — dummy jumper required", "ct_toy_ts"),
        ], "cp_oem_2d"),
        conn("oem_2e", "OEM J/B2 2E dummy header (ER main)", 1440, 420, [
            cav(2, "2", "PROBE: inner p.21 = RTR; starting p.48 = AM1 with 2E-5", "ct_toy_ts"),
            cav(3, "3", "PROBE: inner p.21 = HAZ-HORN; starting p.48 = AM2 with 2E-6", "ct_toy_ts"),
            cav(4, "4", "20A DOME — not on AM1/AM2 pass-through", "ct_toy_ts"),
            cav(5, "5", "AM1 pass-through — do not PMU-feed; restored at IE1-10", "ct_toy_ts", "pl_toy", True),
            cav(6, "6", "AM2 / engine-main related — restored at IE1-17", "ct_toy_ts", "pl_toy", True),
            cav(7, "7", "Headlight relay — unused", "ct_toy_ts", "pl_toy", True),
            cav(8, "8", "15A EFI — unused, cabin k_efi", "ct_toy_ts", "pl_toy", True),
        ], "cp_oem_2e"),
        conn("oem_rb4", "OEM R/B4 (right kick, by glove box)", 1440, 0, [
            cav(1, "HTR1", "40A HEATER fuse input (housing pins 1–2)", "ct_toy_ts"),
            cav(2, "HTR2", "Heater fuse output — stays OEM, do not overlay", "ct_toy_ts", "pl_toy", True),
            cav(3, "STR", "OEM starter relay — isolate, Link k_str owns start", "ct_toy_ts", "pl_toy", True),
        ], "cp_oem_rb4"),
        conn("oem_rb2", "OEM R/B2 (left kick) 30A POWER", 1440, 180, [
            cav(1, "PWR1", "30A POWER fuse input (housing pins 1–2)", "ct_toy_ts"),
            cav(2, "PWR2", "Power fuse output — stays OEM", "ct_toy_ts", "pl_toy", True),
        ], "cp_oem_rb2", width=210),
    ]
    terminals = [
        term("t_pmu_m6", "Ring", "PMU-16 M6 battery stud", 360, -60, "tp_ring2_m6"),
        term("t_gnd_id", "Ring", "OEM ground ID — left kick panel", 1800, 180, "tp_ring2_m8"),
        term("t_gnd_ig", "Ring", "OEM ground IG — R/B4 set bolt", 1800, 0, "tp_ring2_m8"),
        term("t_ig_on", "QuickConnectFemale",
             "IG-ON tap after AM2 restore (J/B1 1H-7 B–O / I9 IG2) — tap only, do not overlay",
             360, 660, "tp_qc_ig"),
    ]
    splices = [
        splice("sp_body", 0, -240, "sp_heavy"),
        splice("sp_gnd", 360, 900, "sp_solder"),
        splice("sp_hl", 720, 300, "sp_solder"),
        splice("sp_hr", 720, 480, "sp_solder"),
    ]
    wires = [
        wire("W1", "Red", "pdb", "c1", "sp_body", "Splice", "wp_10r"),
        wire("W2", "Red", "sp_body", "Splice", "f_hot", "c1", "wp_10r"),
        wire("W3", "White", "f_hot", "c2", "oem_1i", "c1", "wp_14w"),
        wire("W4", "Red", "sp_body", "Splice", "f_am1", "c1", "wp_10r"),
        wire("W5", "White", "f_am1", "c2", "oem_ie1", "c10", "wp_14w"),
        wire("W6", "Red", "sp_body", "Splice", "f_am2", "c1", "wp_10r"),
        wire("W7", "Brown", "f_am2", "c2", "oem_ie1", "c17", "wp_14br", "Red"),
        wire("W8", "Red", "sp_body", "Splice", "f_pmu", "c1", "wp_10r"),
        wire("W9", "Red", "f_pmu", "c2", "t_pmu_m6", "Terminal", "wp_2r"),
        wire("W10", "Red", "sp_body", "Splice", "oem_rb4", "c1", "wp_10r"),
        wire("W11", "Red", "sp_body", "Splice", "oem_rb2", "c1", "wp_10r"),
        wire("W12", "Black", "pdb", "c2", "sp_gnd", "Splice", "wp_2b"),
        wire("W13", "Black", "sp_gnd", "Splice", "t_gnd_id", "Terminal", "wp_2b"),
        wire("W14", "Black", "sp_gnd", "Splice", "t_gnd_ig", "Terminal", "wp_2b"),
        wire("W15", "Black", "sp_gnd", "Splice", "pmu", "c17", "wp_18b"),
        wire("W16", "Red", "pmu", "c1", "sp_hl", "Splice", "wp_12r"),
        wire("W17", "Red", "sp_hl", "Splice", "oem_2a", "c3", "wp_12r"),
        wire("W18", "Red", "sp_hl", "Splice", "oem_2d", "c2", "wp_12r"),
        wire("W19", "Red", "pmu", "c2", "sp_hr", "Splice", "wp_12r"),
        wire("W20", "Red", "sp_hr", "Splice", "oem_2a", "c6", "wp_12r"),
        wire("W21", "Red", "sp_hr", "Splice", "oem_2d", "c6", "wp_12r"),
        wire("W22", "Red", "pmu", "c4", "oem_2e", "c4", "wp_12r"),
        wire("W23", "Red", "pmu", "c3", "oem_2e", "c3", "wp_12r"),
        wire("W24", "Red", "pmu", "c5", "oem_2e", "c2", "wp_12r"),
        wire("W25", "Red", "t_ig_on", "Terminal", "pmu", "c18", "wp_18r"),
        wire("W26", "White", "pmu", "c19", "can_tap", "c1", "wp_20w"),
        wire("W27", "Green", "pmu", "c20", "can_tap", "c2", "wp_20g"),
    ]
    notes = [
        note("n0", "ST185 cursor Engine Room C — OEM INJECTION. Kick-panel J/Bs stay. "
             "Unplug engine-bay J/B2 and F11. Probe 2E-2 / 2E-3 vs IE1 before landing PMU O5 / O3.",
             -360, -420, N, "Red"),
        note("n1", "Primary restores: 1I-1 always-hot, IE1-10 AM1, IE1-17 AM2, R/B4 heater in, "
             "R/B2 POWER in, grounds ID + IG. Dummy header recreates 2A-3↔2D-2 and 2A-6↔2D-6.",
             -360, -540, N, "Orange"),
        note("h0", "GLOVE BOX FUSES", -360, -240, 270, "Green"),
        note("h1", "PMU-16", 360, -240, 210, "Blue"),
        note("h2", "OEM KICK / J/B2", 1080, -240, 270, "Red"),
    ]
    extra = {
        "splices": splices,
        "mates": [],
        "connectorParts": [
            cpart("cp_pdb", "PDB-M8x8", "TBD", "Same glove-box PDB as heavy-DC drawing (body studs)", 2),
            cpart("cp_midi50", "MIDI-50 + holder", "Littelfuse", "MIDI 50 A, J/B1 always-hot", 2),
            cpart("cp_midi40", "MIDI-40 + holder", "Littelfuse", "MIDI 40 A AM1 (was F11 40A FL AM1)", 2),
            cpart("cp_midi30", "MIDI-30 + holder", "Littelfuse", "MIDI 30 A AM2 (was F11 30A FL AM2)", 2),
            cpart("cp_anl150", "ANL-150 + holder", "Littelfuse", "ANL 150 A on PMU-16 M6 stud feed", 2),
            cpart("cp_pmu", "PMU-16", "ECUMaster",
                  "10×25 A + 6×15 A high-side, 150 A total, M6 stud + 39-way. This plug models 20 cavities used here.",
                  20),
            cpart("cp_dtm2", "DTM06-2S", "TE DEUTSCH", "DTM 2-way socket — CAN 1 tap", 2, "Female"),
            cpart("cp_oem_1i", "(OEM 1I plug)", "Toyota", "Factory J/B1 1I harness plug — reuse, pin 1 only", 1),
            cpart("cp_oem_ie1", "(OEM IE1 plug)", "Toyota", "Factory IE1 joiner — land pins 10 and 17 only", 2),
            cpart("cp_oem_2a", "(OEM 2A plug)", "Toyota", "Factory J/B2 2A engine-room-main plug, dummy header", 5),
            cpart("cp_oem_2d", "(OEM 2D plug)", "Toyota", "Factory J/B2 2D engine-room-main plug, dummy header", 5),
            cpart("cp_oem_2e", "(OEM 2E plug)", "Toyota", "Factory J/B2 2E engine-room-main plug, dummy header", 7),
            cpart("cp_oem_rb4", "(OEM R/B4)", "Toyota", "Right-kick R/B No.4 — heater fuse input + isolate starter", 3),
            cpart("cp_oem_rb2", "(OEM R/B2)", "Toyota", "Left-kick R/B No.2 — 30A POWER fuse input", 2),
        ],
    }
    dump("ST185-cursor-EngineRoom-C-oem-inject.harness",
         "ST185 cursor Engine Room C — OEM kick-panel / J/B2 injection + PMU-16",
         "ER-C-CURSOR-OEM-INJECT", connectors, terminals, wires, notes, extra)


def loads():
    connectors = [
        conn("fb", "TE 2141029-1 taps used by Engine Room C", 0, 180, [
            cav(1, "IN", "From heavy-DC PDB FUSE IN (already drawn there)", "ct_fuse_in"),
            cav(2, "F5", "30 A radiator fan relay 30 — size up if fan peak > 30 A", "ct_fuse_in"),
            cav(3, "F6", "20 A condenser fan relay 30 — size up if fan peak > 20 A", "ct_fuse_in"),
            cav(4, "F7", "60 A EPS pump relay 30", "ct_fuse_in"),
            cav(5, "F13", "7.5 A MRS EPS enable, ignition-switched", "ct_fuse_in"),
        ], "cp_fusebox"),
        conn("k_eps", "EPS pump relay harness socket (HCR 150)", 360, 0, [
            cav(1, "30", "Fused +12 V in (F7 60 A)", "ct_hcr_pwr"),
            cav(2, "85", "Coil − pump relay-request (90980-10897 pin 6)", "ct_hcr_coil"),
            cav(3, "86", "Coil + IG-switched 12 V", "ct_hcr_coil"),
            cav(4, "87", "+12 V out, passenger fender to pump", "ct_hcr_pwr"),
            cav(5, "87a", "not used", "ct_hcr_pwr", "pl_sz8", True),
        ], "cp_hcr_sock"),
        conn("k_fan", "Rad fan relay harness socket (Micro ISO)", 360, 360, [
            cav(1, "30", "Fused +12 V in (F5, size to fan peak)", "ct_iso_pwr"),
            cav(2, "85", "Coil − Aux 5 / A29 low-side", "ct_iso_coil"),
            cav(3, "86", "Coil + IG-switched 12 V", "ct_iso_coil"),
            cav(4, "87", "+12 V out to rad fan, core support", "ct_iso_pwr"),
            cav(5, "87a", "not used", "ct_iso_pwr", "pl_sz8", True),
        ], "cp_iso_kit"),
        conn("k_fan2", "Condenser fan relay harness socket (Micro ISO)", 360, 720, [
            cav(1, "30", "Fused +12 V in (F6, size to fan peak)", "ct_iso_pwr"),
            cav(2, "85", "Coil − Ign 5 / B13, diode-suppressed relay", "ct_iso_coil"),
            cav(3, "86", "Coil + IG-switched 12 V", "ct_iso_coil"),
            cav(4, "87", "+12 V out to condenser fan", "ct_iso_pwr"),
            cav(5, "87a", "not used", "ct_iso_pwr", "pl_sz8", True),
        ], "cp_iso_kit"),
        conn("mrs_pwr", "MRS EPS pump power 90980-12068", 1080, 0, [
            cav(1, "1", "12 V from k_eps 87, 8 AWG, passenger ABS trough", "ct_toy_pwr"),
            cav(2, "2", "GND, 8 AWG to engine block (not EA)", "ct_toy_pwr"),
        ], "cp_mrs_pwr"),
        conn("mrs_en", "MRS EPS enable 90980-10942", 1080, 240, [
            cav(1, "1", "IG-switched 7.5 A F13", "ct_toy_ts"),
            cav(2, "2", "unused on this application", "ct_toy_ts", "pl_toy", True),
        ], "cp_mrs_en", width=210),
        conn("mrs_ctrl", "MRS EPS control 90980-10897", 1080, 480, [
            cav(1, "1", "unused here — do not guess", "ct_toy_ts", "pl_toy", True),
            cav(2, "2", "Speed signal — owned by ST185-Signal.harness, do not double-wire",
                "ct_toy_ts", "pl_toy", True),
            cav(3, "3", "unused here", "ct_toy_ts", "pl_toy", True),
            cav(4, "4", "unused here", "ct_toy_ts", "pl_toy", True),
            cav(5, "5", "unused here", "ct_toy_ts", "pl_toy", True),
            cav(6, "6", "Relay request (pump grounds this when it wants F7/k_eps)", "ct_toy_ts"),
        ], "cp_mrs_ctrl"),
        conn("rad_b", "Uprated rad fan B+ DTHD size 8", 1440, 360, [
            cav(1, "1", "From k_fan 87, 8 AWG", "ct_dthd8s"),
        ], "cp_dthd8", width=210),
        conn("rad_g", "Uprated rad fan GND DTHD size 8", 1440, 480, [
            cav(1, "1", "To OEM ground EA", "ct_dthd8s"),
        ], "cp_dthd8", width=210),
        conn("fan2_b", "Uprated condenser fan B+ DTHD size 8", 1440, 720, [
            cav(1, "1", "From k_fan2 87, 8 AWG", "ct_dthd8s"),
        ], "cp_dthd8", width=210),
        conn("fan2_g", "Uprated condenser fan GND DTHD size 8", 1440, 840, [
            cav(1, "1", "To OEM ground EA", "ct_dthd8s"),
        ], "cp_dthd8", width=210),
        conn("iso_fan", "Micro ISO socket kit (k_fan)", 720, 360, [
            cav(1, "30", "Mates k_fan 30", "ct_iso_pwr"),
            cav(2, "85", "Mates k_fan 85", "ct_iso_coil"),
            cav(3, "86", "Mates k_fan 86", "ct_iso_coil"),
            cav(4, "87", "Mates k_fan 87", "ct_iso_pwr"),
            cav(5, "87a", "not used", "ct_iso_pwr", "pl_sz8", True),
        ], "cp_iso_kit"),
        conn("iso_fan2", "Micro ISO socket kit (k_fan2)", 720, 720, [
            cav(1, "30", "Mates k_fan2 30", "ct_iso_pwr"),
            cav(2, "85", "Mates k_fan2 85", "ct_iso_coil"),
            cav(3, "86", "Mates k_fan2 86", "ct_iso_coil"),
            cav(4, "87", "Mates k_fan2 87", "ct_iso_pwr"),
            cav(5, "87a", "not used", "ct_iso_pwr", "pl_sz8", True),
        ], "cp_iso_kit"),
    ]
    # The ISO kits ARE the harness-side of the relays — having both k_fan (relay)
    # and iso_fan (socket) double-counts 30/87. User asked every connector to have
    # contacts; mates map kit to relay. Wires land on the kits, relays are device-side.
    # Simpler and correct: wires on k_fan cavities, kits are the partId of k_fan
    # (1-1904045-6). Remove duplicate iso_fan connectors to avoid unmapped second
    # set of cavities.
    connectors = [c for c in connectors if c["id"] not in ("iso_fan", "iso_fan2")]

    terminals = [
        term("t_pdb_in", "Ring", "From heavy-DC PDB FUSE IN / TE 2141029-1 IN",
             -360, 180, "tp_ring2_m8"),
        term("t_ig_sw", "QuickConnectFemale",
             "IG-switched 12 V (EFI main 87 / restored AM2 path) for relay coils 86",
             0, -60, "tp_qc_ig"),
        term("t_aux5", "QuickConnectFemale", "To Link Aux 5 / Superseal A29 (low-side fan coil)",
             0, 480, "tp_qc_ig"),
        term("t_ign5", "QuickConnectFemale", "To Link Ign 5 / Superseal B13 (condenser fan coil)",
             0, 840, "tp_qc_ig"),
        term("t_block", "Ring", "Engine block stud — EPS pump ground", 1800, 0, "tp_ring8_m8"),
        term("t_ea", "Ring", "OEM ground EA — right front fender, fan grounds", 1800, 480, "tp_ring8_m8"),
    ]
    splices = [
        splice("sp_86", 180, 240, "sp_solder"),
        splice("sp_ea", 1620, 600, "sp_heavy"),
    ]
    wires = [
        wire("W0", "Red", "t_pdb_in", "Terminal", "fb", "c1", "wp_2r"),
        wire("W1", "Red", "fb", "c4", "k_eps", "c1", "wp_8r"),
        wire("W2", "Red", "fb", "c2", "k_fan", "c1", "wp_10r"),
        wire("W3", "Red", "fb", "c3", "k_fan2", "c1", "wp_10r"),
        wire("W4", "Red", "fb", "c5", "mrs_en", "c1", "wp_18r"),
        wire("W5", "Red", "k_eps", "c4", "mrs_pwr", "c1", "wp_8r"),
        wire("W6", "Black", "mrs_pwr", "c2", "t_block", "Terminal", "wp_8b"),
        wire("W7", "Red", "k_fan", "c4", "rad_b", "c1", "wp_8r"),
        wire("W8", "Black", "rad_g", "c1", "sp_ea", "Splice", "wp_8b"),
        wire("W9", "Red", "k_fan2", "c4", "fan2_b", "c1", "wp_8r"),
        wire("W10", "Black", "fan2_g", "c1", "sp_ea", "Splice", "wp_8b"),
        wire("W11", "Black", "sp_ea", "Splice", "t_ea", "Terminal", "wp_8b"),
        wire("W12", "Red", "t_ig_sw", "Terminal", "sp_86", "Splice", "wp_18r"),
        wire("W13", "Red", "sp_86", "Splice", "k_eps", "c3", "wp_18r"),
        wire("W14", "Red", "sp_86", "Splice", "k_fan", "c3", "wp_18r"),
        wire("W15", "Red", "sp_86", "Splice", "k_fan2", "c3", "wp_18r"),
        wire("W16", "Black", "mrs_ctrl", "c6", "k_eps", "c2", "wp_18b"),
        wire("W17", "Black", "t_aux5", "Terminal", "k_fan", "c2", "wp_18b"),
        wire("W18", "Black", "t_ign5", "Terminal", "k_fan2", "c2", "wp_18b"),
    ]
    notes = [
        note("n0", "ST185 cursor Engine Room C — NEW LOADS. EPS 8 AWG in the vacated ABS trough. "
             "Uprated fans 8 AWG / DTHD size 8 on the core support. A/C clutch stays on A/B. "
             "Relay 30/86 live in the glove box; 87 runs are this loom.", -360, -240, N, "Blue"),
        note("n1", "k_fan / k_fan2 use TE 1-1904045-6 Micro ISO kits (contacts 280756-4 / 180360-0). "
             "k_eps uses HCR 150 mating hardware — confirm receptacle PN with TE before order. "
             "Fan housings are DTHD06-1-8S (8 AWG), not DT06-2S.", -360, -360, N, "Orange"),
        note("h0", "GLOVE BOX", 0, -60, 210, "Green"),
        note("h1", "RELAYS", 360, -180, 210, "Orange"),
        note("h2", "ENGINE ROOM", 1080, -180, 270, "Red"),
    ]
    extra = {
        "splices": splices,
        "mates": [],
        "connectorParts": [
            cpart("cp_fusebox", "2141029-1", "TE Connectivity",
                  "Fuse box assembly, hard wired — OWNED. This drawing lands F5/F6/F7/F13/IN only.", 5),
            cpart("cp_hcr_sock", "HCR 150 mating hardware", "TE Connectivity",
                  "Harness receptacle for V23132-A2001-B200 — confirm PN with TE before order. Contacts listed separately.",
                  5, "Female"),
            cpart("cp_iso_kit", "1-1904045-6", "TE Connectivity",
                  "Micro ISO relay connector kit (harness-side socket for V23074). Need 2 (fan + condenser).",
                  5, "Female"),
            cpart("cp_rly_hcr150_dev", "V23132-A2001-B200", "TE Connectivity",
                  "HCR 150 relay device (not a harness connector). Listed so the BOM stays complete."),
            cpart("cp_rly_cod_dev", "6-1419137-4", "TE Connectivity",
                  "V23074-A2001-A403 Micro ISO 1 form C diode — device. Need 2. Socket is 1-1904045-6."),
            cpart("cp_mrs_pwr", "90980-12068", "Toyota / Sumitomo",
                  "MR-S EHPS pump main power. OWNED. Pigtail 82998-12500.", 2),
            cpart("cp_mrs_en", "90980-10942", "Toyota / Sumitomo",
                  "MR-S EHPS pump enable. OWNED.", 2),
            cpart("cp_mrs_ctrl", "90980-10897", "Toyota / Sumitomo",
                  "MR-S EHPS pump control. OWNED. Pin 6 = relay request; pin 2 speed stays on Signal.",
                  6),
            cpart("cp_dthd8", "DTHD06-1-8S", "TE DEUTSCH",
                  "DTHD 1-way plug, size 8, 8-10 AWG — uprated fan power/ground", 1, "Female"),
        ],
    }
    dump("ST185-cursor-EngineRoom-C-loads.harness",
         "ST185 cursor Engine Room C — EPS pump and uprated fans",
         "ER-C-CURSOR-LOADS", connectors, terminals, wires, notes, extra)


if __name__ == "__main__":
    heavy_dc()
    oem_inject()
    loads()
