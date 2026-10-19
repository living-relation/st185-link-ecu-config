"""Schematic positions for the clean-room A-cabin build: one hand-set table, 30-unit grid.

Reading order, left to right: cabin devices (relays, pedal, wheel-speed inline, ECU-B) ->
ECU-A -> splices / sensor buses -> bulkhead -> LOGIC fuse box. Each device sits level with
the ECU-A pins it is wired to, so a wire is short and the two tables it joins face each other.
"""

POS = {
    # connectors (top-left corner)
    "ecu_a": (0, 0, 390),
    "bh_a_fw": (1890, -270, 390),
    "bus_5v_bha_p": (1140, 840, 270),
    "bus_5v_bha_r": (1140, 1140, 270),
    "bus_gnd_bha_p": (1140, 1470, 270),
    "bus_gnd_bha_r": (1140, 1770, 270),
    "fb_logic": (2700, -270, 270),
    "k_eps": (2700, 1320, 270),
    "k_fp": (-900, 480, 270),
    "k_etb": (-900, 690, 270),
    "k_str": (-900, 900, 270),
    "k_efi": (-900, 1080, 270),
    "k_fan": (-900, 1260, 270),
    "aps": (-1260, -90, 270),
    "ix_ws_front_p": (-1260, 180, 270),
    "ecu_b": (-2400, -210, 270),
    "bus_sw12_p": (-900, -480, 270),
    "k_acc": (-1500, 1080, 270),
    # terminals
    "fl_acamp_act": (-900, 420, 390),
    "fl_ac_psw": (-2040, 1170, 390),
    "chassis_ring": (-900, 1500, 390),
    "x_sp_5v_b": (690, 1230, 390),
    "x_r_cruise": (-900, -630, 390),
    "x_sp_csb_gnd": (-900, 1560, 390),
    "x_sp_shield_b": (-2400, 900, 390),
    # splices, resistor, cables (30 x 30 / 60 wide)
    "sp_sw12": (-300, -150, None),
    "sp_8v": (720, 180, None),
    "cam_pullup": (840, 240, None),
    "sp_trig2": (1020, 270, None),
    "sp_shield_a": (720, -90, None),
    "sp_gndout": (720, 720, None),
    "sp_chassis": (-300, 1110, None),
    "sp_5v": (720, 960, None),
    "sp_5v_2": (-450, -390, None),
    "cab_aps": (-690, -90, None),
    "cab_fspur": (-690, 180, None),
    "cab_fspur_fr_ac": (-1620, 300, None),
}


def place(doc):
    for coll in ("connectors", "terminals", "splices", "resistors", "cables"):
        for el in doc.get(coll, []):
            x, y, w = POS[el["id"]]
            el["schematicPosition"] = {"x": x, "y": y}
            if w:
                el["width"] = w
            el.pop("rotated", None)
            if coll in ("splices", "resistors", "terminals", "connectors") and "layoutPosition" not in el:
                el["layoutPosition"] = {"x": x, "y": y}
