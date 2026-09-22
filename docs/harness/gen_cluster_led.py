"""Generate ST185-ClusterLED.harness.

Rewritten 2026-09-22. The first version drew one lumped seven-cavity "Cluster LED
indicator board", which told you nothing about how any single LED is wired. Daniel
asked twice for each LED shown individually, so each is now a diode with real
polarity, wired anode and cathode.

Six LEDs: high beam, turn L, turn R, park brake, charge, oil.

What is known is drawn. What is not is drawn as a named dead end - the common
return (t_led_gnd) and the +12V IG anode feed (t_led_12v) - so the gap is visible
at the node where it lives instead of hiding in a note.

Run from docs/harness:  python gen_cluster_led.py
"""
import json, io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "rebuild", "ST185-ClusterLED.harness")


def conn(cid, label, width, cavities, x, y):
    return {"id": cid, "label": label, "width": width,
            "cavities": cavities,
            "schematicPosition": {"x": x, "y": y},
            "layoutPosition": {"x": x, "y": y}}


def cav(cid, designation, signal):
    return {"id": cid, "designation": designation, "signal": signal}


def led(did, y):
    return {"id": did, "partId": "dp_led", "anodeOnRight": False,
            "schematicPosition": {"x": 450, "y": y},
            "layoutPosition": {"x": 450, "y": y}}


def wire(wid, src, sh, tgt, th, color, stripe=None):
    w = {"id": wid, "color": color,
         "source": {"id": src, "handle": sh},
         "target": {"id": tgt, "handle": th}}
    if stripe:
        w["stripeColor"] = stripe
    return w


def note(nid, text, x, y, color=None, width=390):
    n = {"id": nid, "text": text, "width": width,
         "schematicPosition": {"x": x, "y": y}}
    if color:
        n["color"] = color
    return n


doc = {
    "version": 0.9,
    "diodeParts": [{
        "id": "dp_led",
        "partNumber": "(generic indicator LED - type TBD)",
        "manufacturer": "TBD",
        "description": "Cluster warning indicator LED. Colour, package and forward "
                       "current not yet chosen. Current limiting is an OPEN item - "
                       "either the LED board carries its own resistors or the loom must.",
    }],
    "connectors": [
        conn("cl_c11", "OEM cluster connector C11", 390, [
            cav("c2",  "2",  "Turn L (G-B) - flasher LH stub"),
            cav("c11", "11", "Turn R (G-Y) - flasher RH stub"),
            cav("c12", "12", "High beam (R-L) - body residual feed"),
        ], 0, 90),
        conn("cl_c12", "OEM cluster connector C12", 390, [
            cav("c1", "1", "Park brake (R-G) - grounds via OEM P1 / B2"),
            cav("c8", "8", "Alt L (Y) - charge-lamp drive"),
            cav("c9", "9", "IG +12 (B-O) - charge LED anode side"),
        ], 0, 300),
        conn("dm_csb_ls", "CSB-LS", 210, [
            cav("c1", "1", "ECUMaster CSB3 low-side output, L1-L4 - channel TBD "
                           "(see ST185-A-ECU C10 cavities 23-26, and CAN 0x643), "
                           "wired on ST185-A-ECU"),
        ], 900, 690),
    ],
    "diodes": [led("d_hb", 90), led("d_tl", 210), led("d_tr", 330),
               led("d_pk", 450), led("d_chg", 570), led("d_oil", 690)],
    "splices": [
        {"id": "sp_led_gnd", "schematicPosition": {"x": 690, "y": 210},
         "layoutPosition": {"x": 690, "y": 210}},
        {"id": "sp_led_12v", "schematicPosition": {"x": 240, "y": 570},
         "layoutPosition": {"x": 240, "y": 570}},
    ],
    "terminals": [
        {"id": "t_led_gnd", "type": "Ring", "width": 210,
         "signal": "LED common return - DESTINATION NOT CONFIRMED (open item)",
         "schematicPosition": {"x": 900, "y": 210},
         "layoutPosition": {"x": 900, "y": 210}},
        {"id": "t_led_12v", "type": "Loose", "width": 210,
         "signal": "+12V IG to LED anodes - SOURCE PIN NOT IDENTIFIED (open item)",
         "schematicPosition": {"x": 0, "y": 570},
         "layoutPosition": {"x": 0, "y": 570}},
    ],
    "wires": [
        wire("w_hb_a", "cl_c11", "c12", "d_hb", "Left", "Red"),
        wire("w_hb_k", "d_hb", "Right", "sp_led_gnd", "Splice", "Black"),
        wire("w_tl_a", "cl_c11", "c2", "d_tl", "Left", "Green"),
        wire("w_tl_k", "d_tl", "Right", "sp_led_gnd", "Splice", "Black"),
        wire("w_tr_a", "cl_c11", "c11", "d_tr", "Left", "Green"),
        wire("w_tr_k", "d_tr", "Right", "sp_led_gnd", "Splice", "Black"),
        wire("w_led_gnd_out", "sp_led_gnd", "Splice", "t_led_gnd", "Terminal", "Black"),
        wire("w_12v_in", "t_led_12v", "Terminal", "sp_led_12v", "Splice", "Red"),
        wire("w_pk_a", "sp_led_12v", "Splice", "d_pk", "Left", "Red"),
        wire("w_pk_k", "d_pk", "Right", "cl_c12", "c1", "Red", "Green"),
        wire("w_chg_a", "cl_c12", "c9", "d_chg", "Left", "Black", "Orange"),
        wire("w_chg_k", "d_chg", "Right", "cl_c12", "c8", "Yellow"),
        wire("w_oil_a", "sp_led_12v", "Splice", "d_oil", "Left", "Red"),
        wire("w_oil_k", "d_oil", "Right", "dm_csb_ls", "c1", "White"),
    ],
    "schematicNotes": [
        note("n_src",
             "ST185 cluster LED loom. A separate circuit from the cluster itself - "
             "warning and status indicators only. Migrated 2026-09-19 from "
             "docs/electrical/CLUSTER-LED-DIAGRAM.html, which was the only record "
             "of these connections.", 0, -1180),
        note("n_stripe",
             "Stripe colours live in the cavity text - the schema colour list has no "
             "striped values. C11-2 G-B, C11-11 G-Y, C11-12 R-L, C12-1 R-G, C12-8 Y, "
             "C12-9 B-O.", 420, -1180),
        note("n_chg",
             "Charge LED is a series path: IG +12 (C12-9) to LED to alternator L "
             "(C12-8). ON when the regulator grounds L (not charging), OFF when L "
             "sits near battery volts. Alternator S is a battery sense line, NOT a "
             "lamp - do not wire it here.", 840, -1180),
        note("n_oil",
             "Oil LED is CAN-driven, no discrete sense wire. Link sets Low Oil Press 2 "
             "on 0x3F1 bit4; PCLink packs the CSB low-side on 0x643. The CSB sinks the "
             "cathode; the anode goes to +12 IG.", 1260, -1180),
        note("n_open",
             "STILL OPEN - do not build these two. 1) Where the LED common return "
             "actually lands. The three feed-side LEDs (high beam, turn L, turn R) are "
             "drawn joining at sp_led_gnd and running to t_led_gnd; a local chassis "
             "ground is the obvious answer but the source diagram does not say, so "
             "t_led_gnd has no destination yet. 2) The +12V IG anode feed for the park "
             "brake and oil LEDs - stated as existing, no pin given, drawn as "
             "t_led_12v. 3) Current limiting: whether the LED board carries its own "
             "resistors or the loom must. No resistors are drawn. Park brake grounds "
             "through the OEM P1 / B2 path, which is why its cathode goes to C12-1 and "
             "not to the common return.", 0, -360),
    ],
}

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(doc, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote rebuild/ST185-ClusterLED.harness - 6 individual LEDs, 14 wires")
