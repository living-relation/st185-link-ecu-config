"""Build ST185-ClusterLED.harness from the content of CLUSTER-LED-DIAGRAM.html.

A separate loom: warning and status indicators in the cluster display, driven by
body and engine events - park brake, oil pressure, charge, turn, high beam.
Nothing here is invented; every pin, colour and path below is stated in the HTML.
What the HTML does NOT state is recorded as a schematic note, not guessed at.

Schema notes (v0.9, learned by rejection): wire `color` is a fixed enum with no
striped values, so stripes live in the cavity text; wires take no `signal` key;
cavities take no `description`; `width` is one of 60/90/150/210/270/390;
connectors take no `notes`.

    python docs/harness/gen_cluster_led.py
"""
import json, io, os

R = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, "rebuild", "ST185-ClusterLED.harness")


def cav(cid, desig, signal):
    return {"id": cid, "designation": desig, "signal": signal}


def wire(wid, s, sh, t, th, color):
    return {"id": wid, "color": color,
            "source": {"id": s, "handle": sh}, "target": {"id": t, "handle": th}}


def note(nid, x, y, text):
    return {"id": nid, "schematicPosition": {"x": x, "y": y},
            "width": 390, "text": text}


doc = {
    "$schema": "https://docs.harness.design/files/harness/schema/v0.9.json",
    "$docs": "https://docs.harness.design/files/harness/editing-guide.md",
    "version": 0.9,
    "lengthUnit": "mm",
    "connectors": [
        {"id": "cl_c11", "label": "OEM cluster connector C11",
         "schematicPosition": {"x": 120, "y": 120},
         "layoutPosition": {"x": 120, "y": 120}, "width": 270,
         "cavities": [
             cav("c2", "2", "Turn L (G-B) - flasher LH stub"),
             cav("c11", "11", "Turn R (G-Y) - flasher RH stub"),
             cav("c12", "12", "High beam (R-L) - body residual feed"),
         ]},
        {"id": "cl_c12", "label": "OEM cluster connector C12",
         "schematicPosition": {"x": 120, "y": 480},
         "layoutPosition": {"x": 120, "y": 480}, "width": 270,
         "cavities": [
             cav("c1", "1", "Park brake (R-G) - grounds via OEM P1 / B2"),
             cav("c8", "8", "Alt L (Y) - charge-lamp drive"),
             cav("c9", "9", "IG +12 (B-O) - charge LED anode side"),
         ]},
        {"id": "led_board", "label": "Cluster LED indicator board",
         "schematicPosition": {"x": 720, "y": 240},
         "layoutPosition": {"x": 720, "y": 240}, "width": 210,
         "cavities": [
             cav("hb", "HB", "High beam LED"),
             cav("tl", "TL", "Turn L LED"),
             cav("tr", "TR", "Turn R LED"),
             cav("pk", "PK", "Park brake LED"),
             cav("chg_a", "CHG+", "Charge LED anode, IG side"),
             cav("chg_k", "CHG-", "Charge LED cathode, to alternator L"),
             cav("oil_k", "OIL-", "Oil LED cathode, sunk by the CSB low-side"),
         ]},
        {"id": "dm_csb_ls", "label": "CSB-LS",
         "schematicPosition": {"x": 720, "y": 700}, "width": 150,
         "cavities": [cav("c1", "1", "CSB low-side out - dummy, owned by CAN loom")]},
    ],
    "wires": [
        wire("w_led_hb", "cl_c11", "c12", "led_board", "hb", "Red"),
        wire("w_led_tl", "cl_c11", "c2", "led_board", "tl", "Green"),
        wire("w_led_tr", "cl_c11", "c11", "led_board", "tr", "Green"),
        wire("w_led_pk", "cl_c12", "c1", "led_board", "pk", "Red"),
        wire("w_led_chg_ig", "cl_c12", "c9", "led_board", "chg_a", "Black"),
        wire("w_led_chg_l", "led_board", "chg_k", "cl_c12", "c8", "Yellow"),
        wire("w_led_oil", "dm_csb_ls", "c1", "led_board", "oil_k", "White"),
    ],
    "schematicNotes": [
        note("n_src", 120, 900,
             "ST185 cluster LED loom. A separate circuit from the cluster itself - "
             "warning and status indicators only. Migrated 2026-09-19 from "
             "docs/electrical/CLUSTER-LED-DIAGRAM.html, which was the only record "
             "of these connections."),
        note("n_stripe", 560, 900,
             "Stripe colours live in the cavity text - the schema colour list has no "
             "striped values. C11-2 G-B, C11-11 G-Y, C11-12 R-L, C12-1 R-G, "
             "C12-8 Y, C12-9 B-O."),
        note("n_chg", 120, 1120,
             "Charge LED is a series path: IG +12 (C12-9) to LED to alternator L "
             "(C12-8). ON when the regulator grounds L (not charging), OFF when L "
             "sits near battery volts. Alternator S is a battery sense line, NOT a "
             "lamp - do not wire it here."),
        note("n_oil", 560, 1120,
             "Oil LED is CAN-driven, no discrete sense wire. Link sets Low Oil "
             "Press 2 on 0x3F1 bit4; PCLink packs the CSB low-side on 0x643. The "
             "CSB sinks the cathode; the anode goes to +12 IG."),
        note("n_open", 120, 1340,
             "NOT YET DETERMINED - do not build until settled. 1) The common ground "
             "or return for the high beam, turn L and turn R LEDs; the source "
             "diagram does not state it. 2) Whether the LED board carries its own "
             "current-limiting resistors or the loom must. 3) The oil LED anode feed "
             "(+12 IG) - stated as existing but no pin given. Park brake grounds "
             "through the OEM P1 / B2 path, so it needs no return here."),
    ],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(doc, f, indent=2, ensure_ascii=False)
print("wrote %s  %d wires, %d connectors, %d notes"
      % (os.path.basename(OUT), len(doc["wires"]), len(doc["connectors"]),
         len(doc["schematicNotes"])))
