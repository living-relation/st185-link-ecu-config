"""harness.design copy of ST185-RearFuel, file "ST185-RearFuel Rev B" (Rev B 2026-11-12: RearFuel's editor-turn lengths of 2026-11-11 / 11-12: the trunk relay block on Dan's spot (Z3 b / Z4 b), the corridor route round the trunk's RH side and the back panel run inside the car (Z5 a), the fuel pump plug at the floor service hole (Z8 b); the one mm model (#662), library sync (#664 / #665); viewer only; the master is the source).
Usage: python gen_rearfuel.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library, filtered
to the parts these harnesses use). Writes <out>/rearfuel.json (whole document, already routed with genroute.py: upload as is),
rearfuel_lib_ops.json and rearfuel_expect.json. Built by gen_dash.build (same rules: README "harness.design"; plain labels R1-R9;
text spacing, Dan N99 a): the fuel pump circuit in the trunk - the fuel pump relay (K-FP), a seat in the trunk relay block (a box, Dan S1 a: its wires end at labelled seat
terminals, the relay itself is not drawn) with its coil
feed from the switched +12 V bus plug by the LOGIC box (riding AB-cabin's sill run), the pump +12 V straight from the relay to the
pump (Dan 2026-11-08) and the pump ground to factory ground point BL, back panel centre (Dan N97 a). The fuel level sender is
AB-cabin's end since the inline pair was dropped (Dan N1 a). Route: the RearFuel tree of ST185-harness.layout.json (its
placement-editor seed, approved by Dan Z3 b 2026-11-11, with Z5 a and Z8 b); every routed length = the master."""
import sys
import gen_dash

REARFUEL = dict(
    name='RearFuel', title='ST185-RearFuel', rev='B', date='2026-11-12', stem='rearfuel', script='gen_rearfuel.py', root='GB',
    scope="the fuel pump circuit: the fuel pump relay (K-FP) seat in the trunk relay block (box insides not drawn), its coil feed from the switched +12 V plug "
          "DT06-12SA by the LOGIC box (riding the cabin harness's sill run), the pump +12 V straight from the relay to the pump plug at the "
          "luggage-floor service hole (Dan Z8 b), and the pump ground to factory ground point BL, back panel centre; both run round the "
          "trunk's RH side and the back panel (Z5 a). The fuel level sender belongs to the cabin harness.",
    left_words='the switched +12 V plug DT06-12SA (glove box) and the trunk relay block seat (fuel pump relay K-FP)',
    left=lambda t, i: i in ('BUS-SW12', 'K-FP'),     # K-FP: the trunk relay block seat ends (box_seat_ends keeps the spot)
    area=['GB', 'BATT', 'PUMP', 'RPANEL'],
    # display stripes on +12 V wires, one per circuit (README "Display stripes"; colour is for viewing only)
    stripe={'SW12': ('White', 'switched +12 V bus (relay coil)'), 'FP': ('Yellow', 'fuel pump +12 V')},
)

if __name__ == '__main__':
    gen_dash.build(sys.argv[1], sys.argv[2], REARFUEL)
