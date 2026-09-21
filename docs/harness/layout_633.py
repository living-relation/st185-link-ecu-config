"""Apply the section 6.33 diagram layout standard to every rebuild file.

6.33, restated:

   REAR of car                              FIREWALL      ENGINE BAY + FRONT
  +----------------------------------------------------------------------+
  |  rear driver-side items         +------+------+                      | DRIVER
  |                        +------+ | BH-A | BH-A |  engine bay AND      | (top)
  |                        | ECU  | |cabin | eng  |  front-of-car        |
  |  ----------------------| A  B |-+      >    <  +----------------------|
  |                        +------+ | BH-B | BH-B |  driver top,         | PASS
  |  rear passenger-side items      |cabin | eng  |  passenger bottom    | (bottom)
  |                                 +------+------+                      |
  +----------------------------------------------------------------------+

Columns left to right:
  0 rear   1 cabin-far  2 cabin-near  3 ECU-A  4 ECU-B
  5 BH cabin pair   6 BH engine pair
  7 engine-rear  8 engine-mid  9 engine-front  10 front of car

Within every column: driver-side items on top, centre in the middle,
passenger-side items on the bottom.

Node side assignments come from ZONE below.  LHD car, transverse engine with
the transaxle on the DRIVER side and the timing/accessory belt end on the
PASSENGER side.  Any assignment marked '?' in the comment is a readability
call, not a verified physical position - it does not feed lengths.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")

# column index -> x
COL_X = {0: 0, 1: 620, 2: 1080, 3: 1620, 4: 2080,
         5: 2680, 6: 3220, 7: 3860, 8: 4420, 9: 4980, 10: 5560}

D, C, P = 0, 1, 2          # driver / centre / passenger

# node id -> (column, side)
ZONE = {
    # ---- rear of car -------------------------------------------------
    "fuellvl":    (0, C),
    "fuelpump":   (0, C),
    "wss_rl":     (0, D),
    "wss_rr":     (0, P),
    "sp_shield_rear": (0, C),

    # ---- cabin, far from ECU ----------------------------------------
    "cruise_stalk": (1, D),
    "ign_sw":       (1, D),
    "clutch_sw":    (1, D),
    "brake_sw":     (1, D),
    "start_req":    (1, D),
    "aps":          (1, D),        # pedal box, driver footwell
    "cl_c11":       (1, D),        # cluster, driver
    "cl_c12":       (1, D),
    "led_board":    (1, D),
    "oem_jb1_1i":   (1, D),        # left kick
    "oem_jb1_1h":   (1, D),
    "oem_ie1":      (1, D),
    "oem_rb2":      (1, D),
    "acamp":        (1, C),        # A/C amp, centre dash
    "ecu_com":      (1, C),
    "oem_rb4":      (1, P),        # right kick, by glove box
    "pdb":          (1, P),        # glove box
    "pmu":          (1, P),

    # ---- cabin, near ECU (relays, fuse block, splices) ---------------
    "csb3io":   (2, C),
    "fusebox":  (2, P),
    "k_efi":    (2, P),
    "k_etb":    (2, P),
    "k_fp":     (2, P),
    "k_fan":    (2, P),
    "k_fan2":   (2, P),
    "k_str":    (2, P),
    "sp_12v":     (2, C),
    "sp_sw12":    (2, C),
    "sp_5v":      (2, C),
    "sp_8v":      (2, C),
    "sp_gndout":  (2, C),
    "sp_chassis": (2, C),
    "sp_canh":    (2, C),
    "sp_canl":    (2, C),
    "sp_shield_cab": (2, C),

    # ---- ECU ---------------------------------------------------------
    "ecu_a": (3, C),
    "ecu_b": (4, C),

    # ---- bulkheads ---------------------------------------------------
    "bh_a_fw":  (5, D),
    "bh_b_fw":  (5, P),
    "bh_a_eng": (6, D),
    "bh_b_eng": (6, P),

    # ---- engine bay, rear band (firewall side) -----------------------
    # Sides below are Daniel's, from the car, 2026-09-21 - not inferred.
    "knock1":   (7, C),        # centre, rear of block
    "iat":      (7, C),        # manifold, centre near firewall, rear of block
    "etb":      (7, C),        # intake manifold is at the rear, so ETB is too
    "map":      (7, C),
    "oilp":     (7, D),        # driver side of bay, at the firewall
    "fuelp":    (7, D),        # driver side of bay, at the firewall
    "flex":     (7, D),        # driver side of bay, at the firewall
    "turbospd": (7, D),
    "lambda":   (7, D),
    "boost":    (7, D),
    "clntp":    (7, D),
    "reverse_sw": (7, D),      # transaxle, driver side
    "k_eps":    (7, D),
    "mrs_pwr":  (7, D),
    "mrs_en":   (7, D),
    "mrs_ctrl": (7, D),
    "sp_shield_eng":  (7, C),
    "sp_chassis_eng": (7, C),
    "sp_gndout_eng":  (7, C),
    "sp_5v_eng":      (7, C),
    "sp_sw12_eng":    (7, C),
    "sp_inj_eng":     (7, C),
    "sp_cop_eng":     (7, C),

    # ---- engine bay, mid band (head: injectors, coils) ---------------
    "inj1": (8, C), "inj2": (8, C), "inj3": (8, C), "inj4": (8, C),
    "cop1": (8, C), "cop2": (8, C), "cop3": (8, C), "cop4": (8, C),
    "crank": (8, P),           # passenger side - Daniel, from the car
    "cam":   (8, P),           # ASSUMED with crank at the timing end. NOT confirmed
    "ect":   (8, D),           # driver side water outlet
    "oilt":  (8, D),

    # ---- engine bay, front band --------------------------------------
    "cpiat":  (9, D),          # charge pipe, driver side, front of bay

    # ---- front of car -------------------------------------------------
    "rad_fan":   (10, C),
    "fan2":      (10, C),
    "wss_fl":    (10, D),
    "wss_fr":    (10, P),
    "jump_pos":  (10, D),

    # ---- heavy DC pass-throughs sit with the bulkheads ---------------
    "rl_pos_fw":  (5, C), "rl_neg_fw":  (5, C),
    "rl_pos_eng": (6, C), "rl_neg_eng": (6, C),

    # ---- OEM engine-room junction blocks -----------------------------
    "oem_jb2_2a": (7, P), "oem_jb2_2d": (7, P), "oem_jb2_2e": (7, P),

    # ---- ring terminals / studs --------------------------------------
    "t_trunk_pos": (0, C), "t_trunk_neg": (0, C),
    "t_batt_pos":  (0, C), "t_batt_neg":  (0, C),
    "t_gnd_id": (1, D),          # left kick panel
    "t_gnd_ig": (1, P),          # right kick, R/B4 set bolt
    "t_starter_b":  (9, D),      # driver side, FRONT of block / trans
    "starter_trigger": (9, D),
    "t_eng_block":  (7, D),
    "eng_gnd_ring": (7, D),
    "t_alt_b":      (8, P),      # passenger side, rear of block
    "t_gnd_eb": (10, D),         # left front fender
    "t_gnd_ea": (10, P),         # right front fender
    "batt_ring": (0, C), "chassis_ring": (2, C),
    "t_cluster_can": (1, C), "t_realdash_can": (1, C),

    # VR conditioners live in the cabin, near the ECU (6.30 enclosures).
    "vr1_ch1p": (2, D), "vr1_ch1n": (2, D), "vr1_ch2p": (2, D),
    "vr1_ch2n": (2, D), "vr1_out1": (2, D), "vr1_out2": (2, D),
    "vr1_5v": (2, D), "vr1_gnd": (2, D),
    "vr2_ch1p": (2, P), "vr2_ch1n": (2, P), "vr2_ch2p": (2, P),
    "vr2_ch2n": (2, P), "vr2_out1": (2, P), "vr2_out2": (2, P),
    "vr2_5v": (2, P), "vr2_gnd": (2, P),

    # 6.35 conditioner enclosures, both in the cabin near the ECU
    "vrc_f_inl": (2, D), "vrc_f_inr": (2, D), "vrc_f_out": (2, D),
    "vrc_r_inl": (2, P), "vrc_r_inr": (2, P), "vrc_r_out": (2, P),
}

# A 6.15 dummy block stands in for a real part on another drawing.  Put it in
# the column of the thing it represents so the drawing still reads correctly.
DUMMY_COL = [
    ("dm_ecu_a", (3, C)), ("dm_ecu_b", (4, C)),
    ("dm_bh_a_fw", (5, D)), ("dm_bh_b_fw", (5, P)),
    ("dm_bh_a_eng", (6, D)), ("dm_bh_b_eng", (6, P)),
    ("dm_fusebox", (2, P)), ("dm_k_", (2, P)), ("dm_csb", (2, C)),
    ("dm_sp_shield_cab", (2, C)), ("dm_sp_sw12_", (2, C)),
    # The _eng entries MUST stay above the bare ones - first prefix match wins,
    # and "dm_sp_5v" would otherwise swallow "dm_sp_5v_eng".
    ("dm_sp_chassis_eng", (7, C)), ("dm_sp_gndout_eng", (7, C)),
    ("dm_sp_5v_eng", (7, C)),
    ("dm_sp_gndout", (2, C)), ("dm_sp_5v", (2, C)), ("dm_sp_chassis", (2, C)),
]

GAP = 140
ROW = 34          # pixels per cavity row, close enough for spacing
HEAD = 96


def zone_of(nid):
    if nid in ZONE:
        return ZONE[nid]
    for pre, z in DUMMY_COL:
        if nid.startswith(pre):
            return z
    return None


def height(n):
    return HEAD + ROW * max(1, len(n.get("cavities", []) or [1]))


MOJIBAKE = {
    "â€”": "-",   # em dash that went through cp1252
    "â€“": "-",   # en dash
    "â€™": "'",   # right single quote
    "â€œ": '"',
    "â€\u009d": '"',
    "Î©": "ohm",
    "Â°": "deg",
}


def demojibake(obj):
    """Text that was encoded UTF-8 then read back as cp1252 comes out as
    'ΓÇö' style garbage.  Put it back to plain ASCII so the app shows the
    label the drawing is supposed to have."""
    n = 0
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                new = v
                for bad, good in MOJIBAKE.items():
                    new = new.replace(bad, good)
                if new != v:
                    obj[k] = new
                    n += 1
            else:
                n += demojibake(v)
    elif isinstance(obj, list):
        for v in obj:
            n += demojibake(v)
    return n


WIDTHS = [60, 90, 150, 210, 270, 390]


COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue",
          "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Light Yellow",
          "Light Green", "Light Blue", "Light Gray", "Transparent", "Shield"}


def split_colors(doc):
    """v0.9 has no striped colours.  'Green/Yellow' is a hard reject - the
    stripe goes in its own stripeColor field."""
    n = 0
    for key in ("wires", "cables"):
        for w in doc.get(key, []):
            c = w.get("color")
            if not c or c in COLORS:
                continue
            base, _, stripe = c.partition("/")
            base, stripe = base.strip(), stripe.strip()
            w["color"] = base if base in COLORS else "White"
            if stripe in COLORS:
                w["stripeColor"] = stripe
            n += 1
            for core in w.get("cores", []):
                cc = core.get("color")
                if cc and cc not in COLORS:
                    b, _, s = cc.partition("/")
                    core["color"] = b.strip() if b.strip() in COLORS else "White"
                    if s.strip() in COLORS:
                        core["stripeColor"] = s.strip()
                    n += 1
    return n


def snap_widths(doc):
    """v0.9 accepts only 60/90/150/210/270/390 for width.  Anything else is a
    hard reject on upload, so round up to the next legal step."""
    n = 0
    for key in ("connectors", "terminals", "splices", "schematicNotes"):
        for item in doc.get(key, []):
            w = item.get("width")
            if w in (None,) or w in WIDTHS:
                continue
            item["width"] = next((x for x in WIDTHS if x >= w), 390)
            n += 1
    return n


def place(doc):
    """Return (placed, unknown) after writing schematic + layout positions."""
    nodes = list(doc.get("connectors", []))
    # splices and ring terminals carry positions too
    splices = list(doc.get("splices", [])) + list(doc.get("terminals", []))
    cols = {}
    unknown = []
    for n in nodes + splices:
        z = zone_of(n.get("id", ""))
        if z is None:
            unknown.append(n.get("id"))
            z = (2, C)                      # park it near the ECU, visible
        cols.setdefault(z[0], []).append((z[1], n))

    # ECU A and B, and the two bulkhead pairs, share a top edge so they line
    # up the way 6.33 draws them.
    for col in sorted(cols):
        items = cols[col]
        items.sort(key=lambda t: (t[0], t[1].get("id", "")))
        y = 0
        if col in (3, 4):
            y = 600                          # ECU pair sits left of centre
        if col in (5, 6):
            y = 0
        for side, n in items:
            n["schematicPosition"] = {"x": COL_X[col], "y": y}
            n["layoutPosition"] = {"x": COL_X[col], "y": y}
            y += height(n) + GAP

    # A resistor belongs beside the part it is fitted at, so follow its
    # locationId rather than giving it a zone of its own.
    where = {}
    for n in nodes + splices:
        where[n.get("id")] = n.get("schematicPosition")
    for r in doc.get("resistors", []):
        anchor = where.get(r.get("locationId")) or {"x": COL_X[2], "y": 0}
        pos = {"x": anchor["x"] + 200, "y": anchor["y"] - 120}
        r["schematicPosition"] = pos
        r["layoutPosition"] = dict(pos)

    # A cable is a schematic-only node that sits between the things its cores
    # join, so park it at the midpoint of its endpoints.
    for cb in doc.get("cables", []):
        xs, ys = [], []
        conductors = list(cb.get("cores", []))
        if cb.get("shield"):
            conductors.append(cb["shield"])
        for core in conductors:
            for end in ("source", "target"):
                e = core.get(end)
                if e and where.get(e.get("id")):
                    xs.append(where[e["id"]]["x"])
                    ys.append(where[e["id"]]["y"])
        if xs:
            cb["schematicPosition"] = {"x": sum(xs) // len(xs),
                                       "y": sum(ys) // len(ys)}

    # Wire routing points were hand-placed against the OLD coordinates.  They
    # are now elbows pointing at empty space, so drop them and let the app
    # route straight.
    for w in doc.get("wires", []):
        w.pop("layoutPoints", None)
    for c in doc.get("cables", []):
        c.pop("layoutPoints", None)

    # Notes were anchored to the old grid too.  Stack them in a banner above
    # the drawing instead of leaving them on top of connectors.
    ny = -1400
    for note in doc.get("schematicNotes", []):
        note["schematicPosition"] = {"x": 0, "y": ny}
        ny += 260
    return len(nodes) + len(splices), unknown


def main():
    files = sys.argv[1:] or sorted(f for f in os.listdir(SRC)
                                   if f.endswith(".harness"))
    total_unknown = []
    for fn in files:
        p = os.path.join(SRC, fn)
        with open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
        fixed = demojibake(doc) + snap_widths(doc) + split_colors(doc)
        n, unk = place(doc)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        print("%-30s %3d nodes placed, %d text fixes%s" % (
            fn, n, fixed, ("  UNPLACED: " + ", ".join(unk)) if unk else ""))
        total_unknown += unk
    if total_unknown:
        print("\nNodes with no zone entry (parked near the ECU):")
        for u in sorted(set(total_unknown)):
            print("   " + u)
    else:
        print("\nEvery node has a zone. 6.33 applied.")


if __name__ == "__main__":
    main()
