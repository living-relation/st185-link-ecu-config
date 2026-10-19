"""R181 insertion sweep of the POWER C-straps (ST185-FB-117) straight down into their wells, after Dan's N36 = A (2026-10-18:
the lug end moved away from the bend, so the bottom leg and the well are longer) and N37 (2026-10-19: lug end = PEM FHS-M5-12 flush
stud, top end = DIN 934 nut in the printed holder inside the C). The strap with its stud, top nut and holder (it goes in as one) comes
down from 45 mm above its seat in 1.0 mm steps (0.1 within 6 mm of the hook and of the seat); the rigid base (everything but the
strap's own snap hook: its arm and the hook head over the lip ends) must never be hit, and the least OUTWARD shift of the hook that
clears the strap is recorded - it must grow smoothly (no step over 0.25 per 0.1 mm), stay within the hook's design deflection, and be
0 at the seat (the hook has snapped back over the lips). Run inside Fusion on the built ST185_fusebox_rev7 document:
    exec(open(r'<repo>/cad/fusebox/src/sweep_power_straps.py').read(), {'REPORT': r'<repo>/cad/fusebox/rev7/fusebox_report.json',
         'OUTF': r'<repo>/cad/fusebox/rev7/strap_sweep.json', 'NAMES': ['HTR', 'JB1']})
Claude Code, 2026-10-18.
"""
import adsk.core, adsk.fusion, json
app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
tb = adsk.fusion.TemporaryBRepManager.get()
BT = adsk.fusion.BooleanTypes
occ = {o.component.name: o for o in des.rootComponent.occurrences}
rep = json.load(open(REPORT))
names = globals().get('NAMES', ['HTR', 'JB1'])
base = tb.copy(occ['Power_Base_PA12_printed'].bRepBodies.item(0))
P0 = 'Power_Strap_Out'


def box(x0, y0, z0, x1, y1, z1):
    o = adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0 + x1) / 20, (y0 + y1) / 20, (z0 + z1) / 20),
                                               adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                                               abs(x1 - x0) / 10, abs(y1 - y0) / 10, abs(z1 - z0) / 10)
    return tb.createBox(o)


def mv(b, dx=0.0, dz=0.0):
    c = tb.copy(b); m = adsk.core.Matrix3D.create(); m.translation = adsk.core.Vector3D.create(dx / 10, 0, dz / 10); tb.transform(c, m); return c


def ovl(a, b):
    c = tb.copy(a)
    try:
        tb.booleanOperation(c, b, BT.IntersectionBooleanType)
        return c.volume * 1000
    except Exception:
        return 0.0


straps = [b for o in occ.values() if o.component.name.startswith(P0) for b in o.bRepBodies]
nuts = [b for o in occ.values() if o.component.name.startswith(('Power_Stud_PEM', 'Power_Nut_DIN934', 'Power_NutHolder')) for b in o.bRepBodies]
out = {}
for tab in [t for t in rep['strap_tabs'] if t['name'] in names]:
    y = tab['y']
    st = min(straps, key=lambda b: abs((b.boundingBox.minPoint.y + b.boundingBox.maxPoint.y) * 5 - y))
    sb = st.boundingBox
    sx0, sx1, sz1 = sb.minPoint.x * 10, sb.maxPoint.x * 10, sb.maxPoint.z * 10
    mov = tb.copy(st)
    for n in nuts:
        nb = n.boundingBox
        if abs((nb.minPoint.y + nb.maxPoint.y) * 5 - y) < 1 and sx0 - 5 < (nb.minPoint.x + nb.maxPoint.x) * 5 < sx1 + 5:
            tb.booleanOperation(mov, tb.copy(n), BT.UnionBooleanType)
    a0, a1 = tab['arm']
    out_s = -1.0 if (a0 + a1) / 2 < (sx0 + sx1) / 2 else 1.0           # outward = away from the strap
    lip_end = sx0 if out_s < 0 else sx1
    hw = 6.0 + 1.0
    fz = box(a0 - 1.0, y - hw, 34.9, a1 + 1.0, y + hw, 70.0)            # the arm
    hx = sorted((a1 if out_s < 0 else a0, lip_end - out_s * 1.7))
    tb.booleanOperation(fz, box(hx[0], y - hw, sz1 - 0.1, hx[1], y + hw, 70.0), BT.UnionBooleanType)   # the hook head over the lips
    flex = tb.copy(base); tb.booleanOperation(flex, tb.copy(fz), BT.IntersectionBooleanType)
    rigid = tb.copy(base); tb.booleanOperation(rigid, tb.copy(fz), BT.DifferenceBooleanType)
    hits, lifts, d = [], [], 45.0
    while d >= -0.001:
        m = mv(mov, dz=d)
        v = ovl(m, rigid)
        if v > 1e-3:
            hits.append([round(d, 2), round(v, 4)])
        L = 0.0
        while L <= 3.0 and ovl(m, mv(flex, dx=out_s * L)) > 1e-4:
            L += 0.05
        lifts.append([round(d, 2), round(L, 2)])
        near = d < 6.0 or (lifts and lifts[-1][1] > 0) or (len(lifts) > 1 and lifts[-2][1] > 0)
        d -= 0.1 if near else 1.0
    jumps = [[lifts[i][0], round(lifts[i + 1][1] - lifts[i][1], 2)] for i in range(len(lifts) - 1) if lifts[i + 1][1] - lifts[i][1] > 0.25]
    out[tab['row'] + ' ' + tab['name']] = dict(y=y, rigid_hits=hits[:10], n_hits=len(hits), max_hook_shift=max(l for _, l in lifts),
                                               final_shift=lifts[-1][1], shift_jumps_over_0p25=jumps[:10],
                                               profile=[l for l in lifts if l[1] > 0][:8] + [l for l in lifts if l[1] > 0][-4:])
open(OUTF, 'w').write(json.dumps(out, indent=1))
