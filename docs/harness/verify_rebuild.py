"""Prove the rebuilt looms carry the same connections as the live files.

Compares every wire endpoint before and after the rebuild. Dummy blocks are
resolved back to the real node and pin they stand in for, so a net that now
spans two files still compares equal to the single wire it came from.

    python docs/harness/verify_rebuild.py

Exit 0 and "MATCH" means every connection survived. Anything else is printed
with the wire id so it can be chased.
"""
import json, io, os, sys

R = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, "rebuild")
# The pre-split baseline moved into legacy-prebuild/ on 2026-09-22. It is frozen;
# this diff against it is the only reason it still exists.
LEGACY = os.path.join(R, "legacy-prebuild")

LIVE = ["ST185-Signal.harness", "ST185-Power.harness",
        "ST185-CAN.harness", "ST185-EngineRoom-C.harness"]

# ClusterLED is a new loom migrated from CLUSTER-LED-DIAGRAM.html, not derived
# from any live .harness file, so it has no "before" to compare against.
SKIP = ("ClusterLED", "AntiTheft")


def rebuilt_files():
    return sorted(f for f in os.listdir(OUT) if not any(s in f for s in SKIP))

# Differences the rebuild is supposed to introduce. Anything outside this list
# is a real fault.
EXPECT_GONE = {
    # 2026-09-25: the RADLOK heavy-DC pair was drawn on the B looms AND on
    # EngineRoom-C. Daniel: loom C owns it. Same path lives there as
    # w_pdb_rlp / w_rl_pos / w_rlp_str / w_alt / w_pdb_rln / w_rln / w_rln_blk.
    "w_hv_batt_fw": "deleted - heavy DC is loom C's (w_pdb_rlp)",
    "w_hv_gnd_fw": "deleted - heavy DC is loom C's (w_pdb_rln)",
    "w_hv_batt_eng": "deleted - heavy DC is loom C's (w_rlp_str)",
    "w_hv_gnd_eng": "deleted - heavy DC is loom C's (w_rln_blk)",
    "w_hv_alt": "deleted - heavy DC is loom C's (w_alt)",
    "w_mrs_relay_req": "deleted per 6.16 - the pump does not switch its own relay",
    "w23": "renamed w_cam_pullup_8v and rewired to bridge 8V to the signal",
    "w20_e": "renamed w_cam_pullup_sig and rewired to the ECU side",
    "w20_c": "deleted - duplicate cam path to a9; the signal runs on pin 29",
    # 2026-09-24: the cabin halves of the pre-conditioner front wheel-speed runs.
    # Their engine halves were retired into cab_fout_l / cab_fout_r when the
    # NCV1124 went in, but these two survived, so A23 and B21 each had the
    # conditioner output AND a bulkhead cavity landing on them. Two outputs on
    # one input. bh_a c10 and c12 are spare again.
    "w51_c": "deleted - left A23 with two sources; the conditioner output is "
             "cab_fout_l and this was the old direct path",
    "w54_c": "deleted - left B21 with two sources; same, cab_fout_r",
    # 2026-09-25: the CAN pair was drawn twice across bulkhead A c30/c31 - once
    # here and once in ST185-CAN (wc_h_bh / wc_l_bh / wc_h_lam / wc_l_lam, same
    # cavities, same ends). ST185-CAN is the only CAN drawing now.
    "w_can_bh0_c": "deleted - duplicate of ST185-CAN wc_h_ecu/wc_h_bh",
    "w_can_bh1_c": "deleted - duplicate of ST185-CAN wc_l_ecu/wc_l_bh",
    "w_can_bh0_e": "deleted - duplicate of ST185-CAN wc_h_lam",
    "w_can_bh1_e": "deleted - duplicate of ST185-CAN wc_l_lam",
    # w_rlp is NOT listed here: the id collided across files, and the verifier
    # applies the same rename to `before`, so both sides compare cleanly.
    # 6.12: shields are never connected at the device end. Every drain landing
    # on a device shell goes; the run to the ECU stays.
    # 2026-09-22, 6.32 finished: the shared c1 drain and the engine-bay collector
    # splice are retired. Each screen crosses on its own pin instead, c33/c34/c35,
    # wired on both halves, straight to the cabin shield splice.
    "w_drain_bh_c": "shared c1 drain retired - every screen has its own pin now",
    "w_drain_bh_e": "shared c1 drain retired - sp_shield_eng collector removed with it",
    "w_sh_crank": "-> w_shc_crank (now runs through to the cabin, not to a collector)",
    "w_sh_cam": "-> w_shc_cam (same)",
    "w_sh_knock1": "-> w_shc_knock1 (same)",
    "w_drain_crank": "device-end drain removed - shields float at the device",
    "w_drain_cam": "device-end drain removed - shields float at the device",
    "w_drain_knock1": "device-end drain removed - shields float at the device",
    "w_drain_wss_fl": "device-end drain removed - shields float at the device",
    "w_drain_wss_fr": "device-end drain removed - shields float at the device",
    "w_drain_wss_rl": "device-end drain removed - shields float at the device",
    "w_drain_wss_rr": "device-end drain removed - shields float at the device",

    # ---- wheel speed rebuilt as cables, 6.30 / 6.31 / 6.35 ----------------
    # Every one of these is replaced by a core of the same net in a shielded
    # cable. The right-hand column is the core that took it over, so this table
    # is the mapping, not an excuse.
    "w_flp":   "-> cab_fl_p    (wss_fl c1 to VRC Front IN-L c1)",
    "w50":     "-> cab_fl_n    (wss_fl c2 to VRC Front IN-L c2)",
    "w_frp_c": "-> cab_fr_p    (was wss_fr c1 via bulkhead A 28; 6.31 removes the bulkhead)",
    "w_frp_e": "-> cab_fr_p    (engine half of the same bulkhead hop, now one cable)",
    "w53_c":   "-> cab_fr_n    (was wss_fr c2 via bulkhead A 11; bulkhead removed)",
    "w53_e":   "-> cab_fr_n    (engine half of the same hop)",
    "w_rlp":   "-> cab_rl_p    (wss_rl c1 to VRC Rear IN-L c1)",
    "w58":     "-> cab_rl_n    (wss_rl c2 to VRC Rear IN-L c2)",
    "w_rrp":   "-> cab_rr_p    (wss_rr c1 to VRC Rear IN-R c1)",
    "w61":     "-> cab_rr_n    (wss_rr c2 to VRC Rear IN-R c2)",
    "w51_e":   "-> cab_fout_l  (FL output; previously DEAD-ENDED at a bulkhead dummy "
               "and never reached an ECU pin. Now lands ECU-A A23)",
    "w54_e":   "-> cab_fout_r  (FR output; same dead end, now lands ECU-B B21)",
    "w59":     "-> cab_rout_l  (RL output to ECU-B B20)",
    "w62":     "-> cab_rout_r  (RR output to ECU-B B19)",
    "w_vr1_5v_from_ecu5v": "-> cab_fout_5v  (supply MOVED from sp_5v_eng to the cabin "
                           "sp_5v - the box is in the cabin now)",
    "w_vr2_5v_from_ecu5v": "-> cab_rout_5v  (same move to cabin sp_5v)",
    "w56":     "-> cab_fout_gnd (ground MOVED from sp_gndout_eng to cabin sp_gndout)",
    "w64":     "-> cab_rout_gnd (same move to cabin sp_gndout)",
    "w_drain_rear": "-> cab_rout_sh (rear screen now runs inside the output cable to "
                    "the cabin shield splice)",

    # ---- engine shielded sensors become cables, 6.27 rule 4 ---------------
    # Same endpoints, same net - the wire is now a core inside a screened cable
    # so the screen has somewhere to live.
    "w200_e":      "-> cab_crank_c1  (crank signal, unchanged endpoints)",
    "w_cam_sig_e": "-> cab_cam_c2    (cam signal, unchanged endpoints)",
    "w205_e":      "-> cab_knock1_c1 (knock SIG+, unchanged endpoints)",
    "w12_e":       "-> cab_knock1_c2 (knock SIG-, unchanged endpoints)",
    # 2026-09-25 finish pass (Daniel's decisions 2 and 3).
    "w65": "deleted - it fed sp_12v straight off the battery stud with no fuse; sp_12v is fed by F8 (w_fb_ecu)",
    "w_radg": "deleted - duplicate of w_fan_gnd (rad fan ground was drawn twice); the ring-lug ground stays",
    "w_fan2g": "deleted - duplicate of w_fan2_gnd (condenser fan ground drawn twice)",
    "w_mrsg": "deleted - duplicate of w_eps_gnd (EPS pump ground drawn twice)",
}
EXPECT_NEW = {
    "w_hc_fb": "2026-09-25: 50 A feed HCFB H1 -> FB1 IN; the mini fuse module is now fed from the high-current fuse block",
    "cab_fout_fr_sh": "FR conditioned output screen on its own cable, to sp_shield_b / B17; floats at the VRC (Daniel 2026-09-25)",
    "w_eps_trig": "6.16 ECU-driven EPS relay trigger, Ign 6 / ecu_b.b12",
    "w_rl_pos": "RADLOK positive pair, renamed out of the w_rlp collision",
    "w_cam_pullup_8v": "cam pull-up, ECU 8V a6 to resistor",
    "w_cam_pullup_sig": "cam pull-up, resistor to Trigger 2 a9",
    # 6.30 screens. These are genuinely new conductors, not renames - the old
    # file had no sensor-cable screen at all, only device-end drains that 6.27
    # deleted. Each lands on the conditioner box shell and FLOATS at the sensor,
    # which is why it has one endpoint.
    "cab_fl_sh": "FL sensor screen, floats at the sensor, 360 deg on VRC Front IN-L",
    "cab_fr_sh": "FR sensor screen, floats at the sensor, 360 deg on VRC Front IN-R",
    "cab_rl_sh": "RL sensor screen, floats at the sensor, 360 deg on VRC Rear IN-L",
    "cab_rr_sh": "RR sensor screen, floats at the sensor, 360 deg on VRC Rear IN-R",
    "cab_fout_sh": "front output screen, VRC Front OUT shell to the cabin shield "
                   "splice - the single ground point for the front pair",

    # 6.32 engine screens. Each floats at the sensor (one endpoint) and crosses
    # the firewall on its OWN bulkhead pin - first choice, because the pins are
    # there: 16 free pairs on A.
    "cab_crank_sh":  "crank screen, floats at the sensor, bulkhead A c33",
    "cab_cam_sh":    "cam screen, floats at the sensor, bulkhead A c34",
    "cab_knock1_sh": "knock screen, floats at the sensor, bulkhead B c18",
    # 2026-09-22: the engine-bay collector splice is gone. Each screen now runs on
    # its own bulkhead pin all the way to sp_shield_cab, which is the single ECU
    # termination SHIELD-RULES 6.27 rule 2 asks for. The old shared c1 drain went
    # with it - both halves of c1 are spare.
    "w_shc_crank":  "crank screen, bulkhead A c33 through to the cabin shield splice",
    "w_shc_cam":    "cam screen, bulkhead A c34 through to the cabin shield splice",
    "w_shc_knock1": "knock screen, bulkhead B c18 through to the cabin shield splice",
    # 2026-09-23: the two engine-bay A/C sensors join loom C. Verified in the
    # ST185 EWD parts-location list - A1 ambient temp and A5 pressure switch both
    # feed the A/C AMPLIFIER, not the ECU. Pins still TBD, see the drawing note.
    # 2026-09-24: the VSS was never wired - b29 was notConnected with no signal,
    # so it existed only in XTREMEX-IO-TABLE.html. Daniel: "Vss is used for
    # actual vehicle speed. Don't delete." Three wires per his 2026-09-18 lock
    # (gearbox 3-wire 12V Toyota VSS). Separate from the wheel-speed inputs,
    # which are traction control only.
    "w_vss_12v": "VSS +12V off the engine switched-12V rail, new",
    "w_vss_gnd": "VSS ground off the engine sensor-ground rail, new",
    "w_vss_sig_e": "VSS signal -> bulkhead B c15, engine half, new",
    "w_vss_sig_c": "VSS signal bulkhead B c15 -> ECU-B B29 (DI 8), cabin half, new",
    "w_amb_sig": "A/C ambient temp sensor (EWD A1) -> A/C amplifier, new in loom C",
    "w_amb_rtn": "same, sensor return",
    "w_acp_1": "A/C pressure switch (EWD A5) -> A/C amplifier, new in loom C",
    "w_acp_2": "same, return",
    "w_acp_3": "same, third pole if the switch is a trinary",
    # 2026-09-25: one wire per contact. harness.design sums the wires in a
    # contact, and a Superseal 1.0 / size-20 socket takes one 20 AWG wire.
    "w_trig2_pin": "ECU-A A9 to sp_trig2 - the cam signal and its pull-up meet at the splice",
    "w_fl_sig_pin": "sp_fl_sig to ECU-B B24 - the fuel level signal and its pull-up meet at the splice",
    "wc_h_lam_pin": "sp_canh_lam to CAN-Lambda c4 - bus and end terminator meet at the splice",
    "wc_l_lam_pin": "sp_canl_lam to CAN-Lambda c3 - bus and end terminator meet at the splice",
    "w_cru_ladder_out": "pass 2: splice to CSB3 A2. The stalk signal and the pull-up "
                        "used to land on the same cavity, which is a short. They now "
                        "meet at sp_cruise_ladder and one wire carries the ladder in.",
}
# A connection that legitimately moved to a different pin.
EXPECT_CHANGED = {
    # 2026-09-25 finish pass. Toyota/Denso COP plug 90980-11885: 1 +B, 2 IGF,
    # 3 IGT, 4 GND. The drawings had 1 GND / 2 IGT / 4 12V.
    "w112": "COP1 +B moved c4 -> c1 (Denso COP pin 1 = +B)",
    "w113": "COP2 +B moved c4 -> c1",
    "w114": "COP3 +B moved c4 -> c1",
    "w115": "COP4 +B moved c4 -> c1",
    "w_cop1g": "COP1 ground moved c1 -> c4 (Denso COP pin 4 = GND)",
    "w_cop2g": "COP2 ground moved c1 -> c4",
    "w_cop3g": "COP3 ground moved c1 -> c4",
    "w_cop4g": "COP4 ground moved c1 -> c4",
    "w120_e": "COP1 IGT moved c2 -> c3 (Denso COP pin 3 = IGT; pin 2 IGF unused)",
    "w121_e": "COP2 IGT moved c2 -> c3",
    "w122_e": "COP3 IGT moved c2 -> c3",
    "w123_e": "COP4 IGT moved c2 -> c3",
    "w218": "turbo speed sensor supply moved sp_sw12_eng -> sp_5v_eng (Garrett-style sensor: +5 V supply, 12 V lead is gauge-only)",
    "w77": "EFI main relay 87 now lands on FB1 SW IN (switched bus for F9-F11) instead of sp_sw12, so every switched load is fused",
    "w_fb_in": "battery feed now lands on the high-current fuse block HCFB IN; FB1 is fed 50 A from HCFB H1",
    "w_fb_k_fan_30": "rad fan relay 30 fed from HCFB H2 (40 A AMI); mini fuses stop at 30 A and the 8 AWG wire is past the mini-fuse contact",
    "w_fb_k_fan2_30": "condenser fan relay 30 fed from HCFB H3 (30 A AMI), same reason",
    "w_fb_k_eps_30": "EPS relay 30 fed from HCFB H4 (60 A AMI) via dm_hcfb_h4; F7 60 A could not live on the mini fuse module",
    "w_fpg": "fuel pump ground to its own trunk stud t_trunk_fp_gnd (plan 6.41), off the ECU chassis splice",
    "w_fan_gnd": "rad fan ground leaves from its own single-pole DTHD size-8 plug rad_fan_g (DT size-16 contacts can't take 8 AWG)",
    # 2026-09-25: CAN H/L were on the CAN-Lambda power pins 1/2. Link QSG DTM4:
    # 1 Power, 2 GND, 3 CAN L, 4 CAN H. Moved to 4 (H) and 3 (L), terminator too.
    "wc_h_lam": "CAN H lambda c1 -> c4 (Link QSG pin 4 = CAN H); 2026-09-25 lands on "
                "sp_canh_lam, one wire per contact (wc_h_lam_pin carries it to c4)",
    "wc_l_lam": "CAN L lambda c2 -> c3 (Link QSG pin 3 = CAN L); 2026-09-25 via sp_canl_lam",
    "wc_term3": "end terminator follows CAN H to lambda c4; 2026-09-25 joins at sp_canh_lam",
    "wc_term4": "end terminator follows CAN L to lambda c3; 2026-09-25 joins at sp_canl_lam",
    # 2026-09-25: one wire per contact (see EXPECT_NEW). Same nets throughout.
    "wc_term1": "ECU-end terminator H leg moved off ecu_com c3 onto sp_canh (same net)",
    "wc_term2": "ECU-end terminator L leg moved off ecu_com c4 onto sp_canl (same net)",
    "w44": "fuel level pull-up +5V leg moved off ECU-A A32 onto sp_5v (same rail, B-ECU)",
    "w_cru_5v": "cruise ladder pull-up +5V leg moved off ECU-A A32 onto sp_5v (same rail)",
    "w_cam_pullup_8v": "cam pull-up +8V leg moved off ECU-A A6 onto sp_8v (same rail, B-ECU)",
    "w_cam_sig_c": "cam signal lands on sp_trig2; w_trig2_pin carries it to ECU-A A9",
    "w_cam_pullup_sig": "cam pull-up signal leg moved off ECU-A A9 onto sp_trig2",
    "w_fl_sig": "fuel level signal lands on sp_fl_sig; w_fl_sig_pin carries it to ECU-B B24",
    "w43": "fuel level pull-up leg moved off the sender pin onto sp_fl_sig at the ECU",
    # 2026-09-24. Daniel: "A sensor location must be based on link ECU docs and
    # ECU IO ... move knock to the harness that corresponds with the ECU knock
    # pin." Knock 1 is ECU B9, so it is a loom-B circuit, but all three of its
    # conductors crossed on bulkhead A. The screen was the tell: it crossed
    # bulkhead A and then terminated on SHIELD_B at the ECU. Now bh_b c16/c17/c18.
    "w205_c": "knock 1 SIG+ moved bh_a c27 -> bh_b c16; knock is ECU pin B9 so "
              "it crosses on bulkhead B",
    # The mirror of the same rule: Aux 7 is ECU A27, a loom-A pin, but its
    # speed-out to the MRS pump crossed on bulkhead B c13.
    "w_mrs_c": "Aux 7 MRS speed-out moved bh_b c13 -> bh_a c36; Aux 7 is ECU "
               "pin A27 so it crosses on bulkhead A",
    # 2026-09-22: the pump's three housings are one 10-pin part now, mrs_eps, with
    # the housing letter in every designation. Same wires, same pins, one node.
    #   mrs_pwr c1 -> a1   mrs_pwr c2 -> a2   mrs_ctrl c2 -> b2   mrs_en c1 -> c1
    "w_mrs_e": "mrs_ctrl c2 -> mrs_eps b2; the pump is one 10-pin part now. The "
               "slot was also corrected from c1 to c2 earlier, to match the pin 2 "
               "it has always been labelled. Same net, same wire.",
    # 2026-09-23. Daniel: "No signals or power may flow over any shield ground
    # ever! Never!" w12_c was knock 1's SIG- return sitting on ECU-A A7, which is
    # Shield/Gnd. Link staff (Adamw, forum 17263) confirm "the 'Gnd Out' and
    # 'Shield/Gnd' pins are both sensor ground", so Gnd Out is an approved
    # landing and the screen reference stays clean. Same net, correct pin.
    "w12_c": "knock 1 SIG- moved off ECU-A A7 (shield ground) onto the Gnd Out "
             "sensor ground rail. Nothing but drains may touch a shield ground.",
    # Loom A and loom B shield grounds must never be bridged - one splice fed
    # both a7 and b17. Split into sp_shield_a and sp_shield_b.
    "w_drain_ecu_a": "sp_shield_cab -> sp_shield_a; A and B shield grounds are "
                     "no longer bridged",
    "w_drain_ecu_b": "sp_shield_cab -> sp_shield_b; same",
    # 2026-09-23: bulkhead B c7 and c8 each carried TWO circuits - an analog
    # sensor signal from the A files and switched 12V from the B files. 12V on
    # An Volt 6 and 7. Power moved to the spare size-12 pins; signals unchanged.
    "w_inj_pwr_c": "2026-09-25 cabin end now fused on FB1 F11 (was sp_sw12). Earlier: injector 12V off bh_b c7 (shared with An Volt 6 oil P) onto "
                   "the spare size-12 c1",
    "w_cop_pwr_c": "2026-09-25 cabin end now fused on FB1 F10 (was sp_sw12). Earlier: COP 12V off bh_b c8 (shared with An Volt 7 fuel P) onto c2",
    "w_inj_pwr_e": "engine half of the same move, c7 -> c1",
    "w_cop_pwr_e": "engine half of the same move, c8 -> c2",
    "w_eps_pwr": "mrs_pwr c1 -> mrs_eps a1, the pump is one 10-pin part now",
    "w_eps_gnd": "mrs_pwr c2 -> mrs_eps a2, same",
    "w_mrsg": "mrs_pwr c2 -> mrs_eps a2, same",
    "w_hv_mrs_en_e": "mrs_en c1 -> mrs_eps c1, same",
    # Pass 2: CSB3 renumbered from the old ad-hoc 14-way to the real 33-way
    # HD36-24-33SE cavity map in 6.37 / 6.40. Same nets, new cavity numbers.
    "w_an2":     "cruise ladder now goes stalk -> sp_cruise_ladder (was a second wire "
                 "onto the same CSB3 cavity as the pull-up)",
    "w_cru_sig": "pull-up now goes r_cruise -> sp_cruise_ladder, same reason",
    "w_sw2":     "CSB3 6.37 map: cruise main on is S3, cavity 17 (was 9)",
    "w_sw3":     "CSB3 6.37 map: cruise set/accel is S4, cavity 18 (was 10)",
    "w_sw4":     "CSB3 6.37 map: cruise resume/decel is S5, cavity 19 (was 11)",
    "w_sw5":     "CSB3 6.37 map: clutch is S6, cavity 20 (was 12)",
    "w_sw6":     "CSB3 6.37 map: brake is S7, cavity 21 (was 13)",
    "w_sw7_c":   "CSB3 6.37 map: reverse is S8, cavity 22 (was 14)",
    "wc_h_csb":  "CSB3 6.37 map: CAN H is cavity 5 (was 3)",
    "wc_l_csb":  "CSB3 6.37 map: CAN L is cavity 6 (was 4)",
    # 2026-09-25: one cable per crimp lug. Several conductors shared one ring
    # terminal (harness.design sums them and no lug takes 1/0 + 2 + 2). Each
    # extra cable now has its own lug <terminal>_N on the SAME stud. Same net.
    "w_alt":      "own M10 lug (t_starter_b_2) on the starter B+ stud",
    "w_jump":     "own M10 lug (t_starter_b_3) on the starter B+ stud",
    "w_gnd_eb":   "own M10 lug (t_eng_block_2) on the engine block ground stud",
    "w_fan2_gnd": "own M8 lug (t_gnd_ea_2) on ground stud A; 2026-09-25 leaves from its own DTHD size-8 plug fan2_g",
}


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def endpoints(doc, resolve=None):
    """Every conductor in the document, keyed by id.

    Cable cores count. They carry real connections, and a verifier that only
    read `wires` would have called the whole wheel-speed rebuild a data loss
    while the replacement cores sat right there unexamined.
    """
    out = {}

    def add(cond):
        pair = []
        for side in ("source", "target"):
            e = cond.get(side) or {}
            nid, pin = e.get("id"), e.get("handle")
            if nid is None:
                continue          # a screen may legitimately land at one end
            if resolve and nid in resolve:
                nid, pin = resolve[nid]
            pair.append("%s.%s" % (nid, pin))
        out[cond.get("id")] = frozenset(pair)

    for w in doc.get("wires", []):
        add(w)
    for cb in doc.get("cables", []):
        for core in cb.get("cores", []):
            add(core)
        if cb.get("shield"):
            add(cb["shield"])
    for tw in doc.get("twistedWires", []):
        for w in tw.get("wires", []):
            add(w)
    return out


def replacement_of(reason):
    """EXPECT_GONE reasons of the form '-> cab_fl_p (...)' name the conductor
    that took the connection over. Pull the id back out so we can prove it
    actually exists."""
    reason = reason.strip()
    if not reason.startswith("->"):
        return None
    return reason[2:].strip().split()[0]


def main():
    if not os.path.isdir(OUT):
        print("no rebuild/ directory - run rebuild_looms.py --write first")
        return 1

    before = {}
    node_ids = set()
    for fn in LIVE:
        d = load(os.path.join(LEGACY, fn))
        # Same w_rlp collision the rebuild fixes - apply it here too, or this
        # comparison silently drops one of the two wires exactly as the repo did.
        if fn == "ST185-EngineRoom-C.harness":
            for w in d.get("wires", []):
                if w.get("id") == "w_rlp":
                    w["id"] = "w_rl_pos"
        before.update(endpoints(d))
        for key in ("connectors", "splices", "terminals", "resistors",
                    "diodes", "branchPoints", "groups"):
            node_ids |= {e.get("id") for e in d.get(key, [])}

    # Map every dummy block back to the real node and pin it represents.
    resolve = {}
    for fn in rebuilt_files():
        d = load(os.path.join(OUT, fn))
        for c in d.get("connectors", []):
            cid = c.get("id", "")
            if not cid.startswith("dm_"):
                continue
            rest = cid[3:]
            hit = None
            for n in node_ids:                 # longest match wins - ids contain _
                if rest.startswith(n + "_") and (hit is None or len(n) > len(hit)):
                    hit = n
            if hit:
                resolve[cid] = (hit, rest[len(hit) + 1:])
            else:
                print("  ! could not resolve dummy", cid)

    after = {}
    for fn in rebuilt_files():
        after.update(endpoints(load(os.path.join(OUT, fn)), resolve))

    gone = set(before) - set(after)
    new = set(after) - set(before)
    changed = {w for w in set(before) & set(after) if before[w] != after[w]}

    # Conductors named as the replacement for a deleted wire are expected new.
    replacements = {}
    for w, reason in EXPECT_GONE.items():
        r = replacement_of(reason)
        if r:
            replacements.setdefault(r, []).append(w)

    ok = True
    print("conductors before %d   after %d" % (len(before), len(after)))
    print("-" * 64)
    for w in sorted(gone):
        if w in EXPECT_GONE:
            print("  expected gone  %-20s %s" % (w, EXPECT_GONE[w]))
            # Saying "replaced by X" is worthless if X is not there.
            r = replacement_of(EXPECT_GONE[w])
            if r and r not in after:
                ok = False
                print("      ! REPLACEMENT MISSING - %s does not exist" % r)
        else:
            ok = False
            print("  LOST           %-20s %s" % (w, sorted(before[w])))
    for w in sorted(new):
        if w in EXPECT_NEW:
            print("  expected new   %-20s %s" % (w, EXPECT_NEW[w]))
        elif w in replacements:
            print("  replaces       %-20s %s" % (w, ", ".join(sorted(replacements[w]))))
        else:
            ok = False
            print("  UNEXPECTED     %-20s %s" % (w, sorted(after[w])))
    # A wire that was MEANT to be deleted but is still there produces no diff at
    # all, so check for it explicitly - that is how the shield drains slipped
    # through the first time.
    for w in sorted(set(EXPECT_GONE) & set(after)):
        ok = False
        print("  STILL PRESENT   %-20s should have gone: %s"
              % (w, EXPECT_GONE[w]))
    for w in sorted(changed):
        if w in EXPECT_CHANGED:
            print("  expected move  %-20s %s" % (w, EXPECT_CHANGED[w]))
            continue
        ok = False
        print("  CHANGED        %-20s" % w)
        print("      was %s" % sorted(before[w]))
        print("      now %s" % sorted(after[w]))
    print("-" * 64)
    print("MATCH - every connection survived" if ok
          else "MISMATCH - see the lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
