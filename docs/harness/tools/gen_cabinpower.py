"""harness.design copy of ST185-CabinPower, file "ST185-CabinPower Rev F" (Rev F 2026-11-13: the DRL cut relay RLY-DRL sits in a GEP FRH-A12 relay holder on its FRH-A12-MB-B2 flat bracket in the glove box beside the POWER box (Dan A30 a; library 5LO8 part, no new parts); Rev E 2026-11-12: the high-beam output splice, with one CabinPower leg, is a Loose end with its R10 note, no one-wire splice (DECISIONS T3; build_drawings.one_leg_splices); Rev D 2026-11-12: after T3 (#667) the three alarm feeds are whole AntiTheft wires that only pass through, so CabinPower has no alarm feed ties (w_at_12v_tie_cp, w_at_12v_shk_tie_cp, w_at_ig_tie_cp) and no alarm splices; R10 notes on the shared splices; the SW12 bus plug spare cavity 6 with its sealing plug; Rev C 2026-11-12: CabinPower's editor turn (approved as is: every length from its seed, the DRL switch / pop-up relay branches), the A/C clutch relay wire to the A/C amplifier on its factory spot, the dash high-beam LED fed from the high-beam output by Dash (A2 b: R-HB and its wires gone, the IE1 R-L leg a removal row), the one mm cabin model (#662), 25 mm splice ends (T7 b), ghost wires (T4 a), library sync (#664 / #665); Rev B 2026-11-09: the three alarm feeds follow the moved alarm spot, 1012 -> 1214 mm; viewer only; the master is the source).
Usage: python gen_cabinpower.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library, filtered
to the parts these harnesses use). Writes <out>/cabinpower.json (whole document, already routed with genroute.py: upload as is),
cabinpower_lib_ops.json and cabinpower_expect.json. Built by gen_dash.build (same rules: README "harness.design"; plain labels
R1-R9 by build_drawings.relabel; text spacing, Dan N99 a): the cabin power harness in the glove box and across the dash - the
POWER box stud rings (battery feed, AMI fuses, NEG bar) and the LOGIC fuse and relay box (no device group: each wire ends at a
labelled seat or stud terminal and the box insides are not drawn, Dan R1 a 2026-11-09), the relays beside the POWER box (K-EPS, RLY-DRL), the switched
+12 V bus plug, the factory feeds to J/B No.1, cowl plug IE1 / splice I2, R/B No.4 and the pop-up relay R8 (LH and RH kick),
the headlamp, horn, hazard and DRL circuits (DECISIONS "Headlamps, DRL and pop-ups"), the DRL switch left of the steering wheel
(the three alarm feeds pass through as AntiTheft ghost wires, T3). Route: the CabinPower tree of ST185-harness.layout.json
(its placement-editor seed in the one car-mm model, approved as is by Dan 2026-11-12); every routed length = the master."""
import sys
import gen_dash

CABINPOWER = dict(
    name='CabinPower', title='ST185-CabinPower', rev='F', date='2026-11-13', stem='cabinpower', script='gen_cabinpower.py', root='GB',
    scope="the cabin power harness (glove box and across the dash): the POWER box stud rings (battery feed, AMI fuses, NEG bar) and "
          "the LOGIC fuse and relay box (its relay seats drawn as labelled wire ends; box insides not drawn, Dan R1 a), the relays "
          "beside it, the switched +12 V bus plug, the factory feeds to "
          "J/B No.1, cowl plug IE1 / splice I2, R/B No.4 and the pop-up relay R8, the headlamp, horn, hazard and DRL circuits "
          "(DECISIONS \"Headlamps, DRL and pop-ups\") and the DRL switch left of the steering wheel; the three alarm feeds only pass "
          "through (AntiTheft wires, T3).",
    left_words='the boxes and factory ends (the POWER box stud rings, the LOGIC fuse and relay box, the switched +12 V bus plug, '
               'the factory feeds at J/B No.1, IE1 / I2, R/B No.4 and R8 with their splice notes)',
    left=lambda t, i: t in ('terminal', 'OEM') or i in ('LOGIC', 'BUS-SW12'),
    area=['GB', 'RHKICK', 'JB1', 'DRL_SW', 'ALARM'],
    # formboard comb groups at the glove-box node (view only, Dan 2026-11-08 "separate the two fuse boxes a little more"):
    # 0 = POWER box ends (AMI / NEG stud rings, its relays, the DRL cut relay in its FRH-A12 holder beside it, A30 a), 1 = LOGIC box ends (box, Bus studs, its relays), 2 = harness parts
    # beside the LOGIC box, outside its group outline (the switched +12 V bus plug and its bussed receptacle;
    # Dan 2026-11-09: "there's not any bussed plugs in the fuse boxes"), 3 = the rest (splices, resistor, diodes); a gap
    # between groups, every stub still 100 mm
    comb_group=lambda t, i, box_of: (0 if i.startswith('T-PWR-') or i == 'RLY-DRL' or box_of.get(i) == 'New POWER fuse box' else
                                     1 if (i.startswith('T-LOG-') or i == 'LOGIC' or box_of.get(i) == 'New LOGIC fuse box') else
                                     2 if 'BUS-SW12' in i else 3),
    comb_pad={1: 60},       # one empty slot before the LOGIC box ends, where the bus plug used to sit: the box group stays in place

    oem_name={'JB1': 'J/B No.1', 'IE1': 'Cowl plug IE1', 'I2': 'Cowl splice I2', 'R8': 'Pop-up relay R8', 'RB4': 'R/B No.4'},
    # display stripes on +12 V wires, one per circuit (README "Display stripes"; colour is for viewing only)
    stripe={'SW12': ('White', 'switched +12 V bus (relay coils)'), 'EFI': ('Orange', 'EFI relay'), 'ETB': ('Green', 'ETB relay'),
            'HL': ('Yellow', 'low beam'), 'HR': ('Blue', 'high beam'), 'HZ': ('Violet', 'hazard / horn'), 'ALM': ('White', 'alarm +12 V'),
            'ALMS': ('Orange', 'shock sensor +12 V'), 'LAM': ('Pink', 'ignition-on relay feed'), 'ON': ('Pink', 'ignition-on relay coil'),
            'EPSEN': ('Brown', 'power steering enable'), 'ACC': ('Tan', 'A/C clutch relay'), 'ALMIG': ('Green', 'alarm ignition +12 V'),
            'FAN': ('Maroon', 'radiator fan relay'), 'FAN2': ('Gray', 'condenser fan relay'), 'BUS1': ('Black', 'LOGIC Bus 1 feed'),
            'EPS': ('Brown', 'power steering pump relay'), 'HHI': ('Blue', 'high beam out'), 'LHB': ('Blue', 'high beam LED feed'),
            'DRL': ('Yellow', 'DRL'), 'DM': ('Violet', 'dome feed to J/B No.1'), 'RTR': ('Pink', 'pop-up relay feed'),
            'AM1': ('Orange', 'AM1 feed to IE1'), 'AM2': ('Green', 'AM2 feed to IE1'), 'JB1': ('White', 'J/B No.1 main feed'),
            'HTR': ('Tan', 'R/B No.4 heater feed')},
    # parts not yet in library 5LO8 (maker and description from harness-parts.csv); the same shapes gen_engc.py uses for the DRL cut
    # relay holder's contact (the holder FRH-A12 is in the library, A30 a) and the micro relay; written to cabinpower_lib_ops.json, not applied to the library
    new_parts={'12129409-L': ('contactParts', {"id": "ct_delphi_12129409_l", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                               "minGauge": {"value": 16, "unit": "AWG"}, "maxGauge": {"value": 14, "unit": "AWG"}}),
               '4-1904124-3': ('connectorParts', {"id": "cp_rly_micro_co_res", "hasShell": False, "numberOfCavities": 5}),
               'M22759/16-16-9': ('wireParts', {"id": "m16_16_9", "color": "White", "gauge": {"unit": "AWG", "value": 16}}),
               # the DRL switch (Dan K1 a, #586): Arcolectric R13112AAAA round rocker, 2 quick-connect tabs, TE 280919-2 receptacles
               'R13112AAAA': ('connectorParts', {"id": "cp_arc_r13112aaaa", "gender": "Male", "hasShell": False, "numberOfCavities": 2}),
               '280919-2': ('contactParts', {"id": "ct_te_280919_2", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                             "minGauge": {"value": 20, "unit": "AWG"}, "maxGauge": {"value": 15, "unit": "AWG"}})},
)

if __name__ == '__main__':
    gen_dash.build(sys.argv[1], sys.argv[2], CABINPOWER)
