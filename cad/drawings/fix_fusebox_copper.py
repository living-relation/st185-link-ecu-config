import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
"""Fusebox rev7 (PRE-SWEEP, models\\st185_fusebox_1015\\rev1) copper + Power_Base fixes.
F05  NEG bar end stud 263.5 -> 260.5 (centre-to-end 5.5 -> 8.5 = 1.0 x D(8.5)); base hex pocket moved with it,
     tip-to-tip web to the x=244 pocket bridged (no thin PA12 web); nut 2.5 mm clear of the x=270.5 wall.
F19/D3 M8 stud clearance 8.5 -> 9.0, BattRelay M6 6.5 -> 6.6 (ISO 273 medium).
F07  LOGIC strip holes at tap drill: M4 4.0 -> 3.3, M5 5.0 -> 4.2 (thread length = 3.2 strip, see FIXES OPEN).
F10/D6 machined copper: 0.3 x 45 deg edge break on every edge (bars, pads, strips)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__)); pass
from build123d import *
import feat, fxlib
O = 'orig/fusebox_rev7/'; N = 'out/fusebox_rev7/'
LOG = {}
CH = 0.3

def rehole(sol, rules, move=None):
    """rules: {old_dia: new_dia}; move: {(x,y): (nx,ny)} for Z through holes."""
    hs, _, _ = feat.analyze(sol)
    plugs, cuts, log = [], [], []
    for h in hs:
        d0 = round(h['dia'], 2)
        if d0 not in rules or not h['through']: continue
        base = h['base']; dv = h['d']; lo, hi = h['lo'], h['hi']
        p0 = Vector(*[base[i] + dv[i] * lo for i in range(3)]); L = hi - lo
        ax = Vector(*dv)
        plugs.append(Solid.make_cylinder(d0 / 2 + 0.05, L, Plane(origin=p0, z_dir=ax)))
        c = Vector(*[base[i] + dv[i] * (lo + hi) / 2 for i in range(3)])
        nc = c
        if move:
            for (mx, my), (nx, ny) in move.items():
                if abs(c.X - mx) < 0.05 and abs(c.Y - my) < 0.05: nc = Vector(nx, ny, c.Z)
        q0 = nc - ax * (L / 2 + 1)
        cuts.append(Solid.make_cylinder(rules[d0] / 2, L + 2, Plane(origin=q0, z_dir=ax)))
        log.append(dict(axis=h['axis'], at=[round(c.X, 2), round(c.Y, 2), round(c.Z, 2)], new_at=[round(nc.X, 2), round(nc.Y, 2), round(nc.Z, 2)], old=d0, new=rules[d0]))
    s = sol
    if plugs: s = s.fuse(*plugs).clean()
    if cuts: s = s.cut(*cuts).clean()
    s, n = fxlib.one(s); assert n == 1
    return s, log

def edge_break(sol, d=CH):
    try:
        r = sol.chamfer(d, None, sol.edges())
        r, n = fxlib.one(r)
        if n == 1 and r.is_valid: return r, 'all %d edges' % len(sol.edges())
    except Exception as e:
        pass
    return sol, 'FAILED (left sharp)'

def do(name, rules=None, move=None):
    c = import_step(O + name + '.step')
    out, info = [], []
    for s0 in c.solids():
        s, log = rehole(s0, rules or {}, move)
        s, eb = edge_break(s)
        out.append(s); info.append(dict(valid=s.is_valid, v0=round(s0.volume, 2), v1=round(s.volume, 2), holes=log, edge_break=eb))
    export_step(out[0] if len(out) == 1 else Compound(out), N + name + '.step')
    LOG[name] = info
    print(name, [(i['valid'], i['v0'], i['v1'], len(i['holes']), i['edge_break']) for i in info])
    return out

do('Power_BarNeg_CuC110_25x6p35_L105', {8.5: 9.0}, {(263.5, 205.0): (260.5, 205.0)})
do('Power_Bar_Power_CuC110_25x6p35_POS_bus_L226', {8.5: 9.0})
do('BattRelay_Bar_Power_CuC110_25x6p35', {6.5: 6.6})
do('BattRelay_Pad_Out_CuC110_15x3')
do('Power_Pad_Out_CuC110_15x3')
do('Logic_Strip_Logic_CuC110_25p4x3p2_on_edge', {4.0: 3.3, 5.0: 4.2})

# ---- Power_Base: move the NEG end hex pocket with the stud
b0 = import_step(O + 'Power_Base_PA12_printed.step').solids()[0]
def hexprism(cx, cy, z0, z1, af=13.8):
    r = af / math.sqrt(3)
    pts = [(cx + r * math.cos(math.radians(60 * k)), cy + r * math.sin(math.radians(60 * k))) for k in range(6)]
    return extrude(Plane(origin=(0, 0, z0)) * Polygon(*pts, align=None), amount=z1 - z0).solids()[0]
fill = hexprism(263.5, 205.0, 32.0, 48.16)
b = b0.fuse(fill, tol=1e-4).clean()
b, n = fxlib.one(b); assert n == 1
newp = hexprism(260.5, 205.0, 31.9, 48.2)
bridge = Solid.make_box(3.3, 4.6, 16.3, Plane(origin=(250.6, 202.7, 31.9)))   # leaves >= 3.2 mm PA12 where the hex flanks diverge
seat = Solid.make_box(14.9, 26.2, 0.1, Plane(origin=(254.5, 191.9, 48.15)))   # keep the bar seat floor at z 48.15 over the old pocket
b = fxlib.fuzzy_cut(b, [newp, bridge, seat], 1e-5)
b, n = fxlib.one(b); assert n == 1
export_step(b, N + 'Power_Base_PA12_printed.step'); export_stl(b, N + 'Power_Base_PA12_printed.stl')
LOG['Power_Base_PA12_printed'] = [dict(valid=b.is_valid, v0=round(b0.volume, 2), v1=round(b.volume, 2), change='hex pocket 263.5 -> 260.5, bridge to 244 pocket')]
print('base', b.is_valid, round(b0.volume, 1), round(b.volume, 1))
json.dump(LOG, open('logs/fix_fusebox_copper.json', 'w'), indent=1)
