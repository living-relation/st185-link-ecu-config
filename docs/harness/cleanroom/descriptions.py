"""Plain wire descriptions for the one-time migration (extract_wirelist.py, DECISIONS R201).

A row's description is what the wire is FOR, in plain words, the same at both ends, and at most
20 characters: build_harness.py writes it as the cavity signal (audit_destinations.py D3, Dan's
brief 2026-10-19: never the Link's generic pin names). A circuit that runs through a mated
connector (DRB102 bulkhead, inline DT pair) has ONE description on both sides (N40 1); an
existing list (the A-cabin pilot) gives its circuits' descriptions first.

DESC holds the descriptions written by hand, by wire id; anything not in it is built from the
SoT label of the ECU pin, else from the drawing's pin text. Once the CSVs exist this file is not
read again: the CSV is the source.
"""
import re

MAX = 20

# ECU pins (loom B, comms) -> plain description (A pins come from the A-cabin list)
ECU_DESC = {
    ("ecu_b", "B5"): "ETB motor +12 V", ("ecu_b", "B6"): "Oil temp signal",
    ("ecu_b", "B7"): "Charge temp signal", ("ecu_b", "B9"): "Knock sensor signal",
    ("ecu_b", "B10"): "A/C clutch relay (-)", ("ecu_b", "B12"): "EPS enable relay (-)",
    ("ecu_b", "B13"): "Cond fan relay (-)", ("ecu_b", "B15"): "Oil pressure signal",
    ("ecu_b", "B16"): "Fuel pressure signal", ("ecu_b", "B17"): "Shield drain B",
    ("ecu_b", "B18"): "ETB motor +", ("ecu_b", "B19"): "Rear right wheel spd",
    ("ecu_b", "B20"): "Rear left wheel spd", ("ecu_b", "B21"): "Front right whl spd",
    ("ecu_b", "B22"): "Sensor ground B", ("ecu_b", "B23"): "Coolant press signal",
    ("ecu_b", "B24"): "Fuel level signal", ("ecu_b", "B25"): "ECU power ground",
    ("ecu_b", "B26"): "ETB motor -", ("ecu_b", "B27"): "Anti-theft input",
    ("ecu_b", "B28"): "Ignition sw sense", ("ecu_b", "B29"): "Gearbox speed signal",
    ("ecu_b", "B30"): "Start request", ("ecu_b", "B31"): "A/C request button",
    ("ecu_b", "B32"): "Evap temp signal", ("ecu_b", "B33"): "Pedal 2 signal sub",
    ("ecu_b", "B34"): "ECU power ground",
    ("ecu_com", "C1"): "Comms port ground", ("ecu_com", "C3"): "CAN 1 high",
    ("ecu_com", "C4"): "CAN 1 low",
}

# by wire id: written by hand where the automatic text is unclear or too long
DESC = {
    # B-cabin
    "w_rev_sw_c": "Reverse sw +12 V out", "w12_c": "Knock sensor (-)", "w_shc_knock1": "Knock sensor shield",
    "w_shc_etbm": "ETB motor shield", "w_shc_vss": "Gearbox speed shield", "w_start": "Start request",
    "w_ac_btn_hi": "A/C btn divider mid", "w_ac_btn_lo": "A/C btn divider mid", "w_ac_btn_gnd": "A/C btn divider gnd",
    "w_evap_5v": "+5 V evap pull-up", "w44": "+5 V fuel lvl pullup", "wc_h_bh_bc": "CAN H to CAN-Lambda",
    "wc_l_bh_bc": "CAN L to CAN-Lambda", "w_evap_pu": "Evap pull-up 2.2k", "w43": "Fuel lvl pull-up",
    "w_gnd_b_c19": "Gnd oil/clnt/temps", "w_gnd_b_c21": "Gnd fuel press + VSS", "w_gnd_bhb_trunk": "Sensor ground B",
    "w_rev_feed_c": "Back-up sw +12 V in", "w_rev_coil_c": "Reverse relay coil+", "w_sw7_c": "Reverse to opto in 2",
    "cab_canbh_bc_sh": "CAN-Lambda shield", "w_shd_can_bc": "CAN shields to B17", "w_ac_btn_in": "A/C switch V-G in",
    "w_evap_rtn": "Evap thermistor gnd", "w_evap_sig": "Evap thermistor sig",
    # CabinPower
    "w_k_fp_86_cp": "Fuel pump rly coil+", "w_k_fan_86_cp": "Rad fan rly coil+", "w_k_etb_86_cp": "ETB relay coil+",
    "w_k_str_86_cp": "Start relay coil+", "w_k_fan2_86_cp": "Cond fan rly coil+", "w_k_eps_86_cp": "EHPS relay coil+",
    "w_k_eps_en_86_cp": "EPS enable coil+", "w_k_efi_86_cp": "EFI relay coil+", "w_fb_k_etb_30_cp": "ETB relay +12 V in",
    "w_hl_cp": "Head LH +12 V feed", "w_hr_cp": "Head RH +12 V feed", "w_hz_cp": "Haz-horn +12 V feed",
    "w_at_12v_tie_cp": "Alarm +12 V", "w_at_12v_shk_tie_cp": "Shock sensor +12 V", "w_lam12_cp": "CAN-Lambda +12 V",
    "w_cp_sw12_in": "Switched +12 V feed", "w_dev_cp": "Dash devices +12 V", "w_fb_k_eps_en_30_cp": "EPS enable +12 V in",
    "w_fb_k_acc_30_cp": "A/C clutch +12 V in", "w_at_ig_tie_cp": "Alarm ignition +12V", "w_htr_87_cp": "Heater relay feed",
    "w_fb_k_efi_87_cp": "EFI relay feed", "w_fb_k_str_87_cp": "Start relay feed", "w_fb_k_fan_87_cp": "Rad fan relay feed",
    "w_fb_k_fan2_87_ac": "Cond fan relay feed", "w_pwr_87_cp": "Power relay feed", "w_hc_fb": "LOGIC Bus 1 feed",
    "w_fb_k_eps_30_ac": "EHPS relay feed", "w77_cp": "LOGIC Bus 2 feed", "w_eps_pwr_bc": "EHPS pump +12 V",
    "w_k_eps_en_87_cp": "EPS enable out", "w_hl_85_cp": "Head LH coil (-)", "w_hr_85_cp": "Head RH coil (-)",
    "w_head_coil_cp": "Headlight coil (-)", "w_horn_85_cp": "Horn relay coil (-)", "w_pmu_horn_cp": "Horn +12 V out",
    "w_htr_30_cp": "Heater relay out", "w_htr_85_cp": "Heater relay coil-", "w_htr_87a_cp": "Heater relay NC gnd",
    "w_pwr_85_cp": "Power relay coil-", "w_rev_85_cp": "Reverse relay coil-", "w_rev_87_cp": "Back-up lamps +12 V",
    "w_rev_gauge_cp": "GAUGE 15A feed", "w_start_in_cp": "Start sw ST1 feed", "w_pwr_86_cp": "Power relay coil+",
    "w_htr_86_cp": "Heater relay coil+", "w_hl_30_cp": "Head LH relay feed", "w_hl_86_cp": "Head LH relay coil+",
    "w_hr_30_cp": "Head RH relay feed", "w_hr_86_cp": "Head RH relay coil+", "w_rb4_cp": "Blower motor +",
    "w_htr_acps": "ACPS fuse feed", "w_haz_cp": "Hazard feed", "w_horn_30_cp": "Horn relay feed",
    "w_horn_86_cp": "Horn relay coil+", "w_rev_30_cp": "Reverse relay feed",
    # A-engine
    "w219": "+12 V boost sol", "w112": "Coil 1 +12 V", "w113": "Coil 2 +12 V", "w114": "Coil 3 +12 V", "w115": "Coil 4 +12 V",
    "w_cop1g": "Coil 1 ground", "w_cop2g": "Coil 2 ground", "w_cop3g": "Coil 3 ground", "w_cop4g": "Coil 4 ground",
    "w4": "Gnd coolant temp", "w127": "Gnd throttle sensor", "w217": "+12 V flex fuel", "w47": "Gnd flex fuel",
    "w6": "Gnd intake temp", "w211": "Injector 1 +12 V", "w212": "Injector 2 +12 V", "w213": "Injector 3 +12 V",
    "w214": "Injector 4 +12 V", "w_strl": "Starter solenoid S", "w27": "Gnd MAP sensor", "w_eng_gnd": "Coil ground",
    # B-engine
    "w36": "Gnd coolant press", "w10": "Gnd charge temp", "w33": "Gnd fuel pressure", "w_lamg_be": "CAN-Lambda ground",
    "w30": "Gnd oil pressure", "w8": "Gnd oil temp", "w_vss_gnd": "Gnd gearbox speed", "w_rail_gnd_b_e": "Gnd oil/charge temp",
    "w_lam12_be": "CAN-Lambda +12 V",
    # CAN
    "cab_can_ecu_sh": "ECU CAN shield", "wc_term1": "ECU 120R CAN H", "wc_term2": "ECU 120R CAN L",
    "wc_term3": "Lambda 120R CAN H", "wc_term4": "Lambda 120R CAN L", "wc_h_csb": "CAN H to CSB3", "wc_l_csb": "CAN L to CSB3",
    "wc_h_clu": "CAN H to cluster", "wc_l_clu": "CAN L to cluster", "wc_h_rd": "CAN H to RealDash Pi",
    "wc_l_rd": "CAN L to RealDash Pi", "wc_h_lam_pin": "CAN H to CAN-Lambda", "wc_l_lam_pin": "CAN L to CAN-Lambda",
    "w_dev_clu": "Cluster +12 V", "w_dev_rd": "RealDash Pi +12 V", "cab_can_clu_sh": "Cluster CAN shield",
    "cab_can_csb_sh": "CSB3 CAN shield", "cab_can_rd_sh": "Pi CAN shield", "w_gnd_clu": "Cluster ground",
    "w_gnd_rd": "RealDash Pi ground",
    # EngineRoom-C
   
    "w_pdb_jb1": "J/B1 main feed",
    "w_pdb_am1": "AM1 feed to IE1", "w_pdb_am2": "AM2 feed to IE1",
    "w_eps_gnd": "EHPS pump ground", "w_fan_pwr": "Rad fan +12 V", "w_fan_gnd": "Rad fan ground",
    "w_fan2_pwr": "Cond fan +12 V", "w_fan2_gnd": "Cond fan ground",
    "w_rb2": "Power window feed", "w_gnd_id": "POWER box gnd to ID", "w_gnd_ig": "POWER box gnd to IG",
    "w_gnd_eb": "Block strap to EB", "w_acp_1": "A/C press sw feed", "w_acc_clutch": "A/C clutch +12 V",
    "w_pmu_rtr": "Retract relay feed", "w_pmu_dome": "DOME feed to J/B1",
    "w_pmu_hl": "Head LH +12 V out", "w_pmu_hr": "Head RH +12 V out", "w_horn_lh": "Horn LH +12 V",
    "w_horn_rh": "Horn RH +12 V", "w_horn_lh_g": "Horn LH ground", "w_horn_rh_g": "Horn RH ground",
    "w_rb2_wl": "Door lock feed", "w_clr": "Clearance lamp feed", "w_clr_f7": "LH clearance +",
    "w_clr_f8": "RH clearance +", "w_turn_f7": "LH front turn +", "w_turn_f8": "RH front turn +",
    "w_f7_gnd": "LH front lamp gnd", "w_f8_gnd": "RH front lamp gnd", "w_hl_low_h1": "LH low-beam return",
    "w_hl_low_h2": "RH low-beam return", "w_hl_low": "Low-beam return", "w_hl_high_h1": "LH high-beam return",
    "w_hl_high_h2": "RH high-beam return", "w_hl_high": "High-beam return", "w_rtr_r2_4": "LH retract motor 4",
    "w_rtr_r2_4_p": "LH retract motor 4", "w_rtr_r2_2": "LH retract motor 2", "w_rtr_r3_2": "RH retract motor 2",
    "w_rtr_r3_4": "RH retract motor 4", "w_rtr_r3_4_p": "RH retract motor 4", "w_rtr_close": "Retract close limit",
    "w_rtr_close_r2": "Retract close limit", "w_rtr_close_r3": "Retract close limit", "w_rtr_open": "Retract open limit",
    "w_rtr_open_r2": "Retract open limit", "w_rtr_open_r3": "Retract open limit", "w_rtr_gnd_r2": "LH retract ground",
    "w_rtr_gnd_r2_t": "LH retract ground", "w_rtr_gnd_r3": "RH retract ground", "w_rtr_gnd_r3_t": "RH retract ground",
    "w_wip_b": "Wiper +B", "w_wip_hi": "Wiper HIGH", "w_wip_lo": "Wiper LOW", "w_wip_park": "Wiper park sw",
    "w_wash_pos": "Washer motor +12 V", "w_wash_neg": "Washer switch side",
    "w_alt_l_c": "Alt L charge lamp", "w_alt_s_c": "Alt S battery sense",
    # HeavyDC
    "w_trunk_pos": "Battery + main", "w_ks_h1": "Battery + to POWER", "w_trunk_neg": "Battery - main",
    "w_h3_radlok_pos": "Starter feed (H3)", "w_h6a_radlok_neg": "Engine ground (H6a)", "w_rl_pos": "Starter feed",
    "w_rlp_str": "Starter feed", "w_alt": "Alternator B+", "w_jump": "Jump post feed", "w_rln": "Engine ground",
    "w_rln_blk": "Engine ground",
    "w_ig_ks_in": "Alt IG to kill sw", "w_ig_ks_out": "Alt IG excite",
    "w_fp_30": "Fuel pump rly feed", "w_fp_feed": "Battery relay box +",
    # ClusterLED
    "w_hb_a": "High beam LED +", "w_hb_k": "High beam LED gnd", "w_tl_a": "Turn LH LED +", "w_tl_k": "Turn LH LED gnd",
    "w_tr_a": "Turn RH LED +", "w_tr_k": "Turn RH LED gnd", "w_led_gnd_out": "LED common ground",
    "w_pk_a": "Park brake LED +", "w_pk_k": "Park brake sw (-)", "w_chg_a": "Charge LED +", "w_chg_k": "Charge lamp drive",
    "w_oil_a": "Oil LED +", "w_oil_k": "Oil LED sink (CSB3)", "w_ig_tap": "LED IG +12 V",
    # CSB3
    "w_an2": "Cruise ladder", "w_sw2": "Cruise MAIN on", "w_cru_gnd": "Cruise stalk ground", "w_sw5": "Clutch pedal sw",
    "w_sw6": "Brake on +12 V", "w_cru_sig": "Cruise ladder",
    "w_cru_ladder_out": "Cruise ladder", "w_csb12": "CSB3 +12 V", "w_csbg": "CSB3 ground",
    "w_opto_inc": "Opto COM ground",
    "w_opto_out1": "Brake to CSB3 S7", "w_opto_out2": "Reverse to CSB3 S8", "w_opto_outc": "Opto out ground",
    "w_opto_vcc": "Opto +5 V",
   
    # RearLights
    "w_rl_tail": "Tail lamp feed", "w_rl_tail_r11_c2": "Tail LH +", "w_rl_tail_r11_c3": "Rear marker LH +",
    "w_rl_tail_r12_c2": "Tail RH +", "w_rl_tail_r12_c3": "Rear marker RH +", "w_rl_tail_l1_c1": "Licence light +",
    "w_rl_stop": "Stop lamp feed", "w_rl_stop_r11_c1": "Stop LH +", "w_rl_stop_r12_c1": "Stop RH +",
    "w_rl_stop_h6_c1": "High stop lamp +", "w_rl_turn_l": "Turn LH rear +", "w_rl_turn_r": "Turn RH rear +",
    "w_rl_rev_r11_c4": "Back-up LH +", "w_rl_rev_r12_c4": "Back-up RH +",
    "w_rl_gnd_r11_c5": "Rear lamp LH gnd", "w_rl_gnd_r12_c5": "Rear lamp RH gnd", "w_rl_gnd_l1_c2": "Licence light gnd",
    "w_rl_gnd_h6_c2": "High stop lamp gnd", "w_rl_gnd_bl": "Rear lamps ground",
    # RearFuel
    "w_fpg": "Fuel pump ground", "w_fpump_r": "Fuel pump +12 V",
    # AntiTheft
    "w_at_gnd_a1": "Alarm ground", "w_at_siren": "Siren +", "w_at_park": "Park lamp flash", "w_at_led": "Status LED +",
    "w_at_valet": "Valet switch", "w_at_gnd_b2": "Status LED gnd", "w_at_gnd_b1": "Shock sensor ground",
    "w_at_shk_sig": "Shock trigger", "w_at_gnd_a2": "Siren ground", "w_at_gnd_c1": "Valet switch ground",
    "w_at_12v_shk": "Shock sensor +12 V", "w_at_12v": "Alarm +12 V", "w_at_door": "Door trigger",
    "w_at_hood": "Hood trigger", "w_at_ig": "Alarm ignition +12V", "w_at_park_tie": "Park lamp flash",
    "w_at_trunk": "Trunk trigger", "w_at_door_tie": "Door trigger", "w_at_hood_tie": "Hood trigger",
    "w_at_trunk_tie": "Trunk trigger",
    # WheelSpeed
    "cab_rl_p": "RL wheel speed +", "cab_rl_n": "RL wheel speed -", "cab_rr_p": "RR wheel speed +",
    "cab_rr_n": "RR wheel speed -", "cab_rl_sh": "RL sensor shield", "cab_rr_sh": "RR sensor shield",
    "_TXY7m": "Rear sensor shields", "cab_fl_p": "FL wheel speed +", "cab_fl_n": "FL wheel speed -",
    "cab_fr_p": "FR wheel speed +", "cab_fr_n": "FR wheel speed -", "cab_fl_sh": "FL sensor shield",
    "cab_fr_sh": "FR sensor shield", "e7gavP": "Front sensor shields",
}

# Clerical fixes made in the migration (listed in the Phase 1 report): wire id -> {column: value}.
FIX = {
    # the cluster / Pi CAN drop is ONE drawn terminal for both CAN wires: each wire gets its own pin
    "wc_h_clu": {"to_pin": "CANH"}, "wc_l_clu": {"to_pin": "CANL"},
    "wc_h_rd": {"to_pin": "CANH"}, "wc_l_rd": {"to_pin": "CANL"},
}

WORDS = [  # long words -> short ones, in order
    (r"\bsensor\b", "sens"), (r"\bground\b", "gnd"), (r"\bsignal\b", "sig"), (r"\bpressure\b", "press"),
    (r"\btemperature\b", "temp"), (r"\bswitched\b", "sw"), (r"\bswitch\b", "sw"), (r"\brelay\b", "rly"),
    (r"\bsupply\b", "feed"), (r"\bconnector\b", "plug"), (r"\bleft\b", "L"), (r"\bright\b", "R"),
]


def fit(text):
    text = re.sub(r"\s+", " ", (text or "").strip())
    for pat, rep in WORDS:
        if len(text) <= MAX:
            break
        text = re.sub(pat, rep, text, flags=re.I)
    return text if len(text) <= MAX else text[:MAX].rstrip()


def auto(r, ends):
    """A first description from the SoT / drawing text of the row's ends."""
    for e in ends:
        if e["type"] == "connector" and (e["conn"], e["pin"]) in ECU_DESC:
            return ECU_DESC[(e["conn"], e["pin"])]
    devs = [e for e in ends if e["type"] == "connector" and e["conn"] not in
            ("ecu_a", "ecu_b", "ecu_com", "bh_a_fw", "bh_b_fw", "bh_a_eng", "bh_b_eng")
            and not e["conn"].startswith(("ix_", "bus_"))]
    for e in devs:
        sig = e.get("signal") or ""
        if sig:
            return "%s %s" % (sig, e["name"]) if len(sig) < 12 else sig
    for e in ends:
        if e.get("signal"):
            return e["signal"]
    for e in ends:
        if e["type"] in ("OEM", "terminal") and e.get("label"):
            return e["label"].split(" - ")[-1]
    for e in ends:
        if e["type"] == "splice":
            return e.get("label", "").split(" - ")[-1]
    return r["wire_id"]


def describe(rows, dw):
    """Set from_desc / to_desc on every wire row: one text per circuit through mated pins."""
    import wirelist as WL
    ctx = WL.Ctx()
    parent = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            k = parent[k]
        return k

    wired = [r for r in rows if r["wire_id"]]
    for i, r in enumerate(wired):
        find(i)
        for s in ("from", "to"):
            conn, pin = r[s + "_conn"], r[s + "_pin"]
            if r[s + "_type"] == "connector" and (conn in WL.DRB102 or conn in ctx.mate):
                k = ctx.pin_node(conn, pin)
                parent[find(i)] = find(k)
    groups = {}
    for i, r in enumerate(wired):
        groups.setdefault(find(i), []).append(r)
    for g in groups.values():
        fixed = [r["from_desc"] for r in g if r.get("from_desc")]
        hand = [DESC[r["wire_id"]] for r in g if r["wire_id"] in DESC]
        if fixed:
            text = fixed[0]
        elif hand:
            text = hand[0]
        else:
            cands = [auto(r, r["_ends"]) for r in g if "_ends" in r]
            ecu = [c for r, c in zip(g, cands) if any(e["type"] == "connector" and e["conn"] in ECU_HOSTS
                                                      for e in r.get("_ends", ()))]
            text = fit((ecu or cands or [g[0]["wire_id"]])[0])
        for r in g:
            if not r.get("from_desc"):
                r["from_desc"] = r["to_desc"] = text
    for r in rows:
        for k, v in FIX.get(r["wire_id"], {}).items():
            r[k] = v


ECU_HOSTS = ("ecu_a", "ecu_b", "ecu_com")
