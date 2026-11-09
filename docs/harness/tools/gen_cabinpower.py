"""harness.design copy of ST185-CabinPower, file "ST185-CabinPower Rev A" (viewer only; the master is the source).
Usage: python gen_cabinpower.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library, filtered
to the parts these harnesses use). Writes <out>/cabinpower.json (whole document, already routed with genroute.py: upload as is),
cabinpower_lib_ops.json and cabinpower_expect.json. Built by gen_dash.build (same rules: README "harness.design"; plain labels
R1-R9 by build_drawings.relabel; text spacing, Dan N99 a): the cabin power harness in the glove box and across the dash - the
POWER box stud rings (battery feed, AMI fuses, NEG bar) and the LOGIC fuse and relay box (a device group, Dan N81 a; each wire
drawn as a wire end at its seat or stud, Dan 2026-11-07), the box relays and the relays beside it (K-*, RLY-DRL), the switched
+12 V bus plug, the factory feeds to J/B No.1, cowl plug IE1 / splice I2, R/B No.4 and the pop-up relay R8 (LH and RH kick),
the headlamp, horn, hazard and DRL circuits (DECISIONS "Headlamps, DRL and pop-ups"), the DRL switch left of the steering wheel
and the alarm feed ties (CabinPower's legs of the AntiTheft feed splices). Route: the CabinPower tree of ST185-harness.layout.json
(N120 redo, approved as is by Dan 2026-11-08); every routed length = the master."""
import sys
import gen_dash

CABINPOWER = dict(
    name='CabinPower', title='ST185-CabinPower', rev='A', date='2026-11-09', stem='cabinpower', script='gen_cabinpower.py', root='GB',
    scope="the cabin power harness (glove box and across the dash): the POWER box stud rings (battery feed, AMI fuses, NEG bar) and "
          "the LOGIC fuse and relay box, the box relays and the relays beside it, the switched +12 V bus plug, the factory feeds to "
          "J/B No.1, cowl plug IE1 / splice I2, R/B No.4 and the pop-up relay R8, the headlamp, horn, hazard and DRL circuits "
          "(DECISIONS \"Headlamps, DRL and pop-ups\"), the DRL switch left of the steering wheel and the alarm feed ties (CabinPower's "
          "legs of the AntiTheft feed splices).",
    left_words='the boxes and factory ends (the POWER box stud rings, the LOGIC fuse and relay box, the switched +12 V bus plug, '
               'the factory feeds at J/B No.1, IE1 / I2, R/B No.4 and R8 with their splice notes)',
    left=lambda t, i: t in ('terminal', 'OEM') or i in ('LOGIC', 'BUS-SW12'),
    area=['GB', 'RHKICK', 'JB1', 'DRL_SW', 'ALARM'],
    # formboard comb groups at the glove-box node (view only, Dan 2026-11-08 "separate the two fuse boxes a little more"):
    # 0 = POWER box ends (AMI / NEG stud rings, its relays), 1 = LOGIC box ends (box, bus plug, Bus studs, its relays, the DRL cut
    # relay beside it), 2 = the rest (splices, resistor, diodes); a gap between groups, every stub still 100 mm
    comb_group=lambda t, i, box_of: (0 if i.startswith('T-PWR-') or box_of.get(i) == 'New POWER fuse box' else
                                     1 if (i.startswith('T-LOG-') or i in ('LOGIC', 'RLY-DRL') or 'BUS-SW12' in i
                                           or box_of.get(i) == 'New LOGIC fuse box') else 2),
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
    # relay socket, its contact and the micro relay; written to cabinpower_lib_ops.json, not applied to the library
    new_parts={'12110539': ('connectorParts', {"id": "cp_delphi_12110539", "gender": "Female", "hasShell": False, "numberOfCavities": 5}),
               '12129409-L': ('contactParts', {"id": "ct_delphi_12129409_l", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                               "minGauge": {"value": 16, "unit": "AWG"}, "maxGauge": {"value": 14, "unit": "AWG"}}),
               '4-1904124-3': ('connectorParts', {"id": "cp_rly_micro_co_res", "hasShell": False, "numberOfCavities": 5}),
               '220R 1W': ('resistorParts', {"id": "rp_220r_1w", "resistance": 220, "resistanceUnit": "ohm"}),
               'M22759/16-16-9': ('wireParts', {"id": "m16_16_9", "color": "White", "gauge": {"unit": "AWG", "value": 16}})},
)

if __name__ == '__main__':
    gen_dash.build(sys.argv[1], sys.argv[2], CABINPOWER)
