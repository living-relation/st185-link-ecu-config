"""harness.design copies of the two wheel speed harnesses, files "ST185-WheelSpeed-Front Rev B" and "ST185-WheelSpeed-Rear Rev B" (Rev B 2026-11-09: screen-end drawing #593, box seats R1 a)
(viewer only; the master is the source).
Usage: python gen_wheelspeed.py <repo> <out_dir> [Front|Rear]   (needs <out>/lib.json = a dump of part library 5LO8,
get_part_library, filtered to the parts these harnesses use). Writes <out>/wheelspeed_front.json / wheelspeed_rear.json (whole
document, already routed with genroute.py: upload as is) with their _lib_ops / _expect files. Built by gen_dash.build (same rules:
README "harness.design"; plain labels R1-R9; text spacing, Dan N99 a): each harness is the two sensor cables (Raychem 2-core
shielded 55A1821-20-6/9-9) from the wheel speed sensors' own plugs to the VR conditioner's IN plug (CNLINKO LP-16-J05PE-02-001,
pins per the CAD BOM, Dan G2 a), the screens joined at the conditioner by the shield splice and on to IN pin 3, floating at the
sensors (DECISIONS "VR conditioner boxes (R31, R34)"). The OUT plug is AB-cabin's end (Dan J1 a, 2026-11-08: no inline pair).
Route: the WheelSpeed trees of ST185-harness.layout.json (wheel speed editor, approved by Dan 2026-11-11, Y2 a / Y3 a); every
routed length = the master."""
import sys
import gen_dash

COMMON = dict(
    rev='B', date='2026-11-09', script='gen_wheelspeed.py',
    left_words='the VR conditioner IN plug (the conditioner by the ECU)',
    stripe={},
    screen_note='joined at the conditioner by the shield splice and on to the IN plug pin 3; cut back and sealed under heat-shrink '
                'at the sensor end, where they float (DECISIONS "VR conditioner boxes (R31, R34)").',
    # the VR conditioner plug is not in library 5LO8 yet (maker and description from harness-parts.csv); solder cups, so no
    # crimp contact part; written to the _lib_ops file, not applied to the library
    new_parts={'LP-16-J05PE-02-001': ('connectorParts', {"id": "cp_cnlinko_lp16_j05pe", "gender": "Female", "hasShell": False,
                                                         "numberOfCavities": 5})},
)

FRONT = dict(
    COMMON, name='WheelSpeed-Front', title='ST185-WheelSpeed-Front', stem='wheelspeed_front',
    scope="the front wheel speed sensor cables: FL and FR sensors (their own 2-way plugs) to the front VR conditioner IN plug by the "
          "ECU, each a Raychem 2-core shielded cable, the screens joined at the conditioner and on to IN pin 3, floating at the "
          "sensors; FL leaves through the LH fender pass-through, FR through the RH fender exit, each to the sensor plug on its knuckle.",
    left=lambda t, i: i == 'VRC-F-IN',
    root='VRC_F', area=['VRC_F', 'WSF_LP', 'WSF_RX'],
)

REAR = dict(
    COMMON, name='WheelSpeed-Rear', title='ST185-WheelSpeed-Rear', stem='wheelspeed_rear',
    scope="the rear wheel speed sensor cables: RL and RR sensors (their own 2-way plugs) to the rear VR conditioner IN plug by the "
          "ECU, each a Raychem 2-core shielded cable on the factory route: under the dash to the LH kick (joint IF1), back along the "
          "LH floor, RR crossing under the front edge of the rear seat; the screens joined at the conditioner and on to IN pin 3, floating at the sensors.",
    left=lambda t, i: i == 'VRC-R-IN',
    root='VRC_R', area=['VRC_R', 'WSR_K', 'WSR_S'],
)

if __name__ == '__main__':
    which = sys.argv[3] if len(sys.argv) > 3 else 'Front'
    gen_dash.build(sys.argv[1], sys.argv[2], FRONT if which == 'Front' else REAR)
