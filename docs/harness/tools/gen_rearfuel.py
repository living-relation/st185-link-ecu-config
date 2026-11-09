"""harness.design copy of ST185-RearFuel, file "ST185-RearFuel Rev A" (viewer only; the master is the source).
Usage: python gen_rearfuel.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library, filtered
to the parts these harnesses use). Writes <out>/rearfuel.json (whole document, already routed with genroute.py: upload as is),
rearfuel_lib_ops.json and rearfuel_expect.json. Built by gen_dash.build (same rules: README "harness.design"; plain labels R1-R9;
text spacing, Dan N99 a): the fuel pump circuit in the trunk - the fuel pump relay (K-FP), a seat in the trunk relay block (a box, Dan S1 a: its wires end at labelled seat
terminals, the relay itself is not drawn) with its coil
feed from the switched +12 V bus plug by the LOGIC box (riding AB-cabin's sill run), the pump +12 V straight from the relay to the
pump (Dan 2026-11-08) and the pump ground to factory ground point BL, back panel centre (Dan N97 a). The fuel level sender is
AB-cabin's end since the inline pair was dropped (Dan N1 a). Route: the RearFuel tree of ST185-harness.layout.json (N120 redraw,
approved as is by Dan O1 a 2026-11-09); every routed length = the master."""
import sys
import gen_dash

REARFUEL = dict(
    name='RearFuel', title='ST185-RearFuel', rev='A', date='2026-11-09', stem='rearfuel', script='gen_rearfuel.py', root='GB',
    scope="the fuel pump circuit: the fuel pump relay (K-FP) seat in the trunk relay block (box insides not drawn), its coil feed from the switched +12 V bus "
          "plug by the LOGIC box (riding the cabin harness's sill run), the pump +12 V straight from the relay to the pump, and the "
          "pump ground to factory ground point BL, back panel centre. The fuel level sender belongs to the cabin harness.",
    left_words='the switched +12 V bus plug (glove box) and the trunk relay block seat (fuel pump relay K-FP)',
    left=lambda t, i: i in ('BUS-SW12', 'K-FP'),     # K-FP: the trunk relay block seat ends (box_seat_ends keeps the spot)
    area=['GB', 'BATT', 'PUMP', 'RPANEL'],
    # display stripes on +12 V wires, one per circuit (README "Display stripes"; colour is for viewing only)
    stripe={'SW12': ('White', 'switched +12 V bus (relay coil)'), 'FP': ('Yellow', 'fuel pump +12 V')},
)

if __name__ == '__main__':
    gen_dash.build(sys.argv[1], sys.argv[2], REARFUEL)
