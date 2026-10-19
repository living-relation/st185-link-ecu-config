"""R181 insertion sweep of the LOGIC bus strips past their rear snap hooks (Dan's drawing markup 2026-10-18, spec.STRIP_HOLD).
Each strip with its PEM nuts slides in along -y from behind the box (the way it is fitted). In 0.1 mm steps near the ends (1.0 between):
the rigid base (everything but the hook arm + tooth) must never be hit, and the least lift of the hook that clears the strip is recorded -
it must rise smoothly (no step over 0.25 per 0.1, i.e. no self-locking flat), stay within the hook's design deflection, and be 0 at the
end (the tooth has dropped behind the strip). Run inside Fusion on the built ST185_fusebox_rev7 document (Fusion MCP execute_python):
    exec(open(r'<repo>/cad/fusebox/src/sweep_logic_strips.py').read(), {'REPORT': r'<repo>/cad/fusebox/rev7/fusebox_report.json',
                                                                     'OUTF': r'<repo>/cad/fusebox/rev7/strip_sweep.json'})
Claude Code, 2026-10-18.
"""
import adsk.core, adsk.fusion, json, math
app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
tb = adsk.fusion.TemporaryBRepManager.get()
BT = adsk.fusion.BooleanTypes
occ = {o.component.name: o for o in des.rootComponent.occurrences}
rep = json.load(open(REPORT))['strip_hold']
base = tb.copy(occ['Logic_Base_PA12_printed'].bRepBodies.item(0))
def box(x0, y0, z0, x1, y1, z1):
    o = adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20, (y0+y1)/20, (z0+z1)/20), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), abs(x1-x0)/10, abs(y1-y0)/10, abs(z1-z0)/10)
    return tb.createBox(o)
def mv(b, dy=0.0, dz=0.0):
    c = tb.copy(b); m = adsk.core.Matrix3D.create(); m.translation = adsk.core.Vector3D.create(0, dy/10, dz/10); tb.transform(c, m); return c
def ovl(a, b):
    c = tb.copy(a)
    try:
        tb.booleanOperation(c, b, BT.IntersectionBooleanType)
        return c.volume * 1000
    except Exception:
        return 0.0
strips = [b for b in occ['Logic_Strip_Logic_CuC110_25p4x3p2_on_edge'].bRepBodies]
nuts = [b for nm in ('Logic_Nut_PEM_S-M4-2ZI', 'Logic_Nut_PEM_SS-M5-2ZI') for b in occ[nm].bRepBodies]
out = {}
for st in strips:
    bb = st.boundingBox
    x0, x1, y0, y1 = bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10
    col = 'BUS1' if x0 < 28 else 'BUS2'
    hk = rep[col]['rear_hook']
    mov = tb.copy(st)
    for n in nuts:
        nb = n.boundingBox
        if x0 - 3 < nb.minPoint.x*10 < x1 + 3 and y0 <= nb.minPoint.y*10 <= y1:
            tb.booleanOperation(mov, tb.copy(n), BT.UnionBooleanType)
    # flex region: the arm + tooth + post (post is rigid, but it lies above the strip path - keep it in rigid); arm from catch to post
    cy, za = hk['catch_y'], hk['tooth_z'][1]
    fz = box(x0 - 0.5 - 0.05, cy - 0.05, hk['tooth_z'][0] - 0.05, x1 + 0.5 + 0.05, cy + hk['arm_mm'], za + hk['t'] + 0.05)
    flex = tb.copy(base); tb.booleanOperation(flex, tb.copy(fz), BT.IntersectionBooleanType)
    rigid = tb.copy(base); tb.booleanOperation(rigid, tb.copy(fz), BT.DifferenceBooleanType)
    hits, lifts = [], []
    travel = (y1 - y0) + hk['arm_mm'] + 6.0
    d = travel
    while d >= -0.001:
        m = mv(mov, dy=d)
        v = ovl(m, rigid)
        if v > 1e-3: hits.append([round(d, 2), round(v, 4)])
        # least lift of the flex part that clears the strip (0.05 steps)
        L = 0.0
        while L <= 3.0 and ovl(m, mv(flex, dz=L)) > 1e-4:
            L += 0.05
        lifts.append([round(d, 2), round(L, 2)])
        d -= 1.0 if (d > 6.0 and d < travel - hk["arm_mm"] - 6) else 0.1
    jumps = [ [lifts[i][0], round(lifts[i+1][1]-lifts[i][1], 2)] for i in range(len(lifts)-1) if lifts[i+1][1]-lifts[i][1] > 0.25 ]
    out[col] = dict(rigid_hits=hits[:10], n_hits=len(hits), max_lift=max(l for _, l in lifts), final_lift=lifts[-1][1],
                    lift_jumps_over_0p25=jumps[:10], profile=[l for l in lifts if l[1] > 0][:12] + [l for l in lifts if l[1] > 0][-6:])
open(OUTF, "w").write(json.dumps(out, indent=1))
