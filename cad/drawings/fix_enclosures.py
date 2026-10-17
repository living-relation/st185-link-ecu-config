import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
"""Pass 1: decided geometry fixes on VRC / CSB3 / DRB102 (scratch copies only).
F01 tab slots 5.5 -> 6.6 (ISO 273 medium M6), slot length 10 kept.
F08 rev2 hole corrections re-applied (M3 tap drill 2.5, 1.5-2xD thread; DRB M5 drill 4.2 x 10).
D1  DRB 4x 6.35 -> 6.6 THRU.
F02/D2 VRC M6 holder boss +1.0 (z 9.5 -> 10.5), drill re-cut flat to z 1.0; holder pockets deepened 1.0 (z 9.7 -> 10.7).
F04 VRC spotface feather edge: Ø30 spotface cylinder extended inboard to x = +/-35 so it clears the R7.7 corner fillets.
F09 CSB3 lid D-hole flat-to-arc corners: R3 cutter fillet (flat position unchanged)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from build123d import *
import holefix, fxlib
O = 'orig/'; N = 'out/'; T = 'logs/tmp/'
os.makedirs(T, exist_ok=True)
for d in ('vrc', 'vrc/print', 'csb3', 'drb102'): os.makedirs(N + d, exist_ok=True)
LOG = {}
M3LID = dict(old=2.528, new=2.5, through=False, depth=9.5, thread='M3x0.5-6H x 8 deep', purpose='lid screw ISO 10642 M3x12', oldlen=9.24)
M3SO = dict(old=2.528, new=2.5, through=False, depth=6.0, thread='M3x0.5-6H x 4.5 deep', purpose='Keystone 25510 standoff stud', oldlen=5.5)

def slots(sol, xs, y, z0=-1, z1=10):
    cuts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            a, b = sorted((sx * xs[0], sx * xs[1]))
            cuts.append(fxlib.stadium_cut(a, b, sy * y, 3.3, z0, z1))
    return sol.cut(*cuts).clean()

# ---------------- VRC body
v0 = import_step(O + 'vrc/VRC_part_VRC-Body.step').solids()[0]
s, _, hl = holefix.fix(O + 'vrc/VRC_part_VRC-Body.step', T + 'vrc_h.step', [M3LID])
s = slots(s, (26.3, 29.7), 31.5)                                     # was centres 25.75..30.25 r2.75
boss = [Solid.make_cylinder(5.5, 1.0, Plane(origin=(x, y, 9.5))) for x, y in ((-20.7, -9.5), (20.7, 9.5))]
drill = [Solid.make_cylinder(2.5, 10.5, Plane(origin=(x, y, 1.0))) for x, y in ((-20.7, -9.5), (20.7, 9.5))]
s = s.fuse(*boss).clean().cut(*drill).clean()
sf = [Solid.make_cylinder(15.0, 3.05, Plane(origin=(sx * 35.0, 0, 21.0), z_dir=(sx, 0, 0))) for sx in (-1, 1)]
s = fxlib.fuzzy_cut(s, sf, 1e-5)
s, n = fxlib.one(s); assert n == 1, n
# F11: R3 on the 8 tab-to-body vertical inside corners (x +/-18 / +/-38, y +/-25, z 0-6)
def vedges(sol, xs, yabs, zmax=7):
    return [e for e in sol.edges() if e.geom_type == GeomType.LINE and abs(e.tangent_at(0.5).Z) > 0.99 and e.center().Z < zmax
            and any(abs(abs(e.center().X) - x) < 0.01 for x in xs) and abs(abs(e.center().Y) - yabs) < 0.01]
s = s.fillet(3.0, vedges(s, (18, 38), 25)); s, n = fxlib.one(s); assert n == 1
export_step(s, N + 'vrc/VRC_part_VRC-Body.step')
LOG['VRC-Body'] = dict(valid=s.is_valid, v0=v0.volume, v1=s.volume, holes=hl)

# ---------------- VRC holder (+ print copy, z-5)
h0 = import_step(O + 'vrc/VRC_part_VRC-Board-Holder.step').solids()[0]
pk = [Solid.make_cylinder(5.9, 1.05, Plane(origin=(x, y, 9.65))) for x, y in ((-20.7, -9.5), (20.7, 9.5))]
h = h0.cut(*pk).clean(); h, n = fxlib.one(h); assert n == 1
export_step(h, N + 'vrc/VRC_part_VRC-Board-Holder.step'); export_stl(h, N + 'vrc/VRC_part_VRC-Board-Holder.stl')
hp = h.translate((0, 0, -5.0))
export_step(hp, N + 'vrc/print/ST185_VRC_board_holder_PA12.step'); export_stl(hp, N + 'vrc/print/ST185_VRC_board_holder_PA12.stl')
try:
    m = Mesher(); m.add_shape(hp); m.write(N + 'vrc/print/ST185_VRC_board_holder_PA12.3mf')
except Exception as e: print('3mf failed', e)
LOG['VRC-Board-Holder'] = dict(valid=h.is_valid, v0=h0.volume, v1=h.volume)

# ---------------- CSB3 body
c0 = import_step(O + 'csb3/CSB3_part_CSB3-Body.step').solids()[0]
c, _, hl = holefix.fix(O + 'csb3/CSB3_part_CSB3-Body.step', T + 'csb3_h.step', [M3LID, M3SO])
c = slots(c, (18.3, 21.7), 41.5)                                     # was centres 17.75..22.25 r2.75
c, n = fxlib.one(c); assert n == 1
# F11: tab-to-body inside corners: R3 at x +/-10; R1.9 at x +/-30 (only a 2.0 ledge to the R3 body corner there)
c = c.fillet(3.0, vedges(c, (10,), 35)); c, n = fxlib.one(c)
c = c.fillet(1.9, vedges(c, (30,), 35)); c, n = fxlib.one(c); assert n == 1
export_step(c, N + 'csb3/CSB3_part_CSB3-Body.step')
LOG['CSB3-Body'] = dict(valid=c.is_valid, v0=c0.volume, v1=c.volume, holes=hl)

# ---------------- CSB3 lid D-hole corners
l0 = import_step(O + 'csb3/CSB3_part_CSB3-Lid.step').solids()[0]
ed = [e for e in l0.edges() if e.geom_type == GeomType.LINE and abs(abs(e.center().X) - 8.22) < 0.05 and abs(e.center().Y - 19.91) < 0.05]
print('lid corner edges', len(ed), [round(e.length, 2) for e in ed])
l = l0.fillet(3.0, ed); l, n = fxlib.one(l); assert n == 1
export_step(l, N + 'csb3/CSB3_part_CSB3-Lid.step')
LOG['CSB3-Lid'] = dict(valid=l.is_valid, v0=l0.volume, v1=l.volume, edges=len(ed))

# ---------------- DRB plate
d0 = import_step(O + 'drb102/DRB102-firewall-plate.step').solids()[0]
d, _, hl = holefix.fix(O + 'drb102/DRB102-firewall-plate.step', N + 'drb102/DRB102-firewall-plate.step',
    [dict(old=4.2, new=4.2, through=False, depth=10.0, thread='M5x0.8-6H x 7.5 deep', purpose='firewall M5 screws'),
     dict(old=6.35, new=6.6, through=True, purpose='DRBF-1A flange M6, ISO 273 medium')])
LOG['DRB102-plate'] = dict(valid=d.is_valid, v0=d0.volume, v1=d.volume, holes=hl)
json.dump(LOG, open('logs/fix_enclosures.json', 'w'), indent=1, default=str)
for k, v in LOG.items(): print(k, v['valid'], round(v['v0'], 1), '->', round(v['v1'], 1), len(v.get('holes', [])))
