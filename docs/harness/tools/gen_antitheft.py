"""harness.design copy of ST185-AntiTheft, file "ST185-AntiTheft Rev D" (Rev D 2026-11-12: AntiTheft's editor turn (approved as is, the tree already its seed), the one mm cabin model (#662: the immobiliser lead), 25 mm splice ends (T7 b), ghost wires (T4 a), library sync (#664 / #665); Rev C 2026-11-09: route redraw, Dan Z10 b / Z13 b: alarm spot and ground ring on Dan's 2026-11-08 spots, siren along the firewall, hood pin lead down the LH side to the front centre; Rev B: labels, siren lengths #575, box seats R1 a; viewer only; the master is the source).
Usage: python gen_antitheft.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library, filtered
to the parts these harnesses use). Writes <out>/antitheft.json (whole document, already routed with genroute.py: upload as is),
antitheft_lib_ops.json and antitheft_expect.json. Built by gen_dash.build (same rules: README "harness.design"; text spacing,
Dan N99 a): the alarm-ready tap points (Dan 2026-11-06: no alarm picked, so no alarm module or accessories are drawn), each
signal from its real source to its labelled node AL-* at the alarm spot: the constant and ignition feeds (one whole wire each
from its LOGIC box fuse seat, riding CabinPower's glove-box bundle; T3), the door trigger from the factory tap
T-AT-DOOR (J/B No.1 1B-11 R-W, written as a terminal in the master: its label and full OEM splice note come from the shared
helpers as a J/B No.1 tap), the hood trigger pull-wire to the front centre (LH side, with the siren leads), the ECU immobiliser input (ECU-B pin 27, Dan B18 a;
ECU-B drawn whole, its other cavities N/C with a note), the siren pull-wires to the bay (B19) and the alarm ground ring
T-AT-GND (Dan N43 b). The reserved hazard-flash node AL-HAZ (Dan N47) has no wire and is named in a note, not drawn."""
import sys
import gen_dash

ANTITHEFT = dict(
    name='AntiTheft', title='ST185-AntiTheft', rev='D', date='2026-11-12', stem='antitheft', script='gen_antitheft.py', root='ECU',
    scope="the alarm-ready tap points (Dan 2026-11-06: no alarm picked, so no alarm module, siren, shock sensor, status LED, valet switch "
          "or hood pin switch is drawn): each signal the alarm will need runs from its real source to a labelled, capped node AL-* at "
          "the alarm spot - constant +12 V AL-12V (LOGIC ALM 5 A) and AL-12V-SHK (LOGIC ALMS 2 A), ignition AL-IGN (LOGIC ALMIG 2 A), "
          "door trigger AL-DOOR (factory tap T-AT-DOOR, J/B No.1 1B-11 R-W; trunk pin dropped, Dan N41 a), hood trigger AL-HOOD "
          "(pull-wire to the front-centre end AL-HOOD-BAY, down the LH side), immobiliser AL-IMMOB (ECU plug B pin 27, Dan B18 a), ground AL-GND, siren "
          "AL-SIREN with its pull-wires to the bay (AL-SIREN-BAY, AL-SIREN-GND-BAY, B19); the ground ring terminal T-AT-GND at the "
          "alarm, to a chassis point Dan picks at install (Dan N43 b, a named exception to B10).",
    left_words='the sources (ECU plug B, the J/B No.1 door tap, the bay ends of the pull-wires)',
    left=lambda t, i: i in ('ECU-B', 'T-AT-DOOR', 'AL-SIREN-BAY', 'AL-SIREN-GND-BAY', 'AL-HOOD-BAY'),
    area=['ECU', 'JB1', 'SIREN', 'C_RHC'],
    oem_name={'JB1': 'J/B No.1'},
    tap_terms={'T-AT-DOOR': ('JB1', '1B-11')},      # master: "OEM door courtesy switch line (R-W) at J/B No.1 connector 1B pin 11"
    stripe={'ALM': ('White', 'alarm constant +12 V (LOGIC ALM 5 A)'), 'ALMS': ('Orange', 'shock sensor +12 V (LOGIC ALMS 2 A)'),
            'ALMIG': ('Green', 'alarm ignition +12 V (LOGIC ALMIG 2 A)'), 'SIREN': ('Yellow', 'siren + pull-wire')},
)

if __name__ == '__main__':
    gen_dash.build(sys.argv[1], sys.argv[2], ANTITHEFT)
