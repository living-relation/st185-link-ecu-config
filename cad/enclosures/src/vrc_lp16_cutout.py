"""VRC body: the two LP-16 panel cutouts become the maker's double-D hole (Dan's markup 2026-10-18).
CNLINKO LP-16-xxxSX-02-1xxx drawing (sheet 1, "Mounting hole size"): D18.5 +0.2/0 round, two flats 16.5 +0.2/0 apart,
flats horizontal (top and bottom), centred on the hole: 8.25 from the centre to each flat. Max panel 4.5 (wall here 3.5).
Was a single D (one flat at the top, 16.5 from the flat to the far side of the circle).
Parametric: the existing `LP16_D_cutout` sketch (YZ plane, centre z 21) is redrawn in place; its symmetric cut (Extrude5)
still runs through both end walls, so IN and OUT stay the same. Idempotent: run it again and nothing changes.
Run inside Fusion (Fusion MCP execute_python):
    exec(open(r'<repo>/cad/enclosures/src/vrc_lp16_cutout.py').read(), {'__file__': r'<that path>'})
Exports the body / assembly STEP and the f3d to the main checkout's cad/enclosures/vrc/ (R67) and saves the document (R74).
Claude Code, 2026-10-18.
"""
import adsk.core, adsk.fusion, math, os, json

app = adsk.core.Application.get()
MAIN = r'C:\projects\active\st185-link-ecu-config'
OUT = os.path.join(MAIN, 'cad', 'enclosures', 'vrc')
DOC = 'ST185-VRC-Enclosure'
HOLE_D, FLATS = 18.5, 16.5          # CNLINKO LP-16 SX mounting hole (Dan's numbers match the maker drawing)
ZC = 21.0                           # LP-16 axis height (vrc_holder_spec.LP16_AXIS_Z)
REPORT = {}


def cm(v):
    return v / 10.0


def open_doc(name):
    for d in app.documents:
        if d.name.split(' v')[0] == name:
            d.activate()
            return d
    proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
    f = [f for f in proj.rootFolder.dataFiles if f.name == name][0]
    return app.documents.open(f, True)


def flats_now(sk):
    """z of every straight edge in the sketch (world mm)."""
    return sorted(round(l.worldGeometry.startPoint.z * 10.0, 3) for l in sk.sketchCurves.sketchLines)


doc = open_doc(DOC)
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent
body_occ = [o for o in root.occurrences if o.component.name == 'VRC-Body'][0]
bc = body_occ.component
sk = bc.sketches.itemByName('LP16_D_cutout')
CUT_NAME = 'LP16_double_D'
cuts = [f for f in bc.features.extrudeFeatures if f.name in ('Extrude5', CUT_NAME)]
cut = cuts[0]
REPORT['before'] = {'cut': cut.name, 'flats_z': flats_now(sk), 'body_cm3': round(bc.bRepBodies.item(0).volume, 3)}

want = [round(ZC - FLATS / 2, 3), round(ZC + FLATS / 2, 3)]
if cut.name != CUT_NAME or flats_now(sk) != want:
    # Fusion will not re-point a cut at a redrawn sketch (curProfile), so: roll back to just before the old cut,
    # redraw the sketch, delete the old cut and put a new symmetric through-cut (same 100 mm) in its place.
    tl = des.timeline
    cut.timelineObject.rollTo(True)
    old = list(sk.sketchCurves)
    r, h = HOLE_D / 2, FLATS / 2
    half = math.sqrt(r * r - h * h)
    W = adsk.core.Point3D.create
    m = sk.transform.copy(); m.invert()

    def sp(y, z):                       # world (y, z) on the x = 0 plane -> sketch point
        p = W(0, cm(y), cm(z)); p.transformBy(m); return p
    arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines
    ap = arcs.addByThreePoints(sp(half, ZC + h), sp(r, ZC), sp(half, ZC - h))      # +y side
    an = arcs.addByThreePoints(sp(-half, ZC - h), sp(-r, ZC), sp(-half, ZC + h))   # -y side

    def end_at(y, z):
        q = sp(y, z)
        return min([ap.startSketchPoint, ap.endSketchPoint, an.startSketchPoint, an.endSketchPoint],
                   key=lambda s: s.geometry.distanceTo(q))
    lines.addByTwoPoints(end_at(-half, ZC + h), end_at(half, ZC + h))              # flat at the top
    lines.addByTwoPoints(end_at(-half, ZC - h), end_at(half, ZC - h))              # flat at the bottom
    for c in old:
        c.deleteMe()
    body = bc.bRepBodies.item(0)
    cut.deleteMe()
    ci = bc.features.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
    ci.setSymmetricExtent(adsk.core.ValueInput.createByString('100 mm'), True)
    ci.participantBodies = [body]
    cut = bc.features.extrudeFeatures.add(ci)
    cut.name = CUT_NAME
    tl.moveToEnd()
    REPORT['redrawn'] = True
REPORT['profiles'] = sk.profiles.count
REPORT['cut_ok'] = cut.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
REPORT['after'] = {'body_cm3': round(bc.bRepBodies.item(0).volume, 3)}

# measure the finished hole on the body: highest / lowest planar face inside the hole at the +x wall
b = bc.bRepBodies.item(0)
zs = []
for f in b.faces:
    g = f.geometry
    if g.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType and abs(abs(g.normal.z) - 1) < 1e-6:
        bb = f.boundingBox
        if bb.maxPoint.x * 10 > 41.0 and abs(bb.minPoint.y * 10) < 9.3 and abs(bb.maxPoint.y * 10) < 9.3 and 11 < bb.minPoint.z * 10 < 31:
            zs.append(round(bb.minPoint.z * 10, 3))
REPORT['flat_faces_z_at_IN_wall'] = sorted(set(zs))

if globals().get('EXPORT', True) and REPORT['cut_ok']:
    em = des.exportManager
    files = {}
    for o in root.occurrences:
        o.isLightBulbOn = True
        for bb in o.component.bRepBodies:
            bb.isLightBulbOn = True

    def step(path, comp):
        em.execute(em.createSTEPExportOptions(path, comp))
        files[os.path.basename(path)] = os.path.getsize(path)
    step(os.path.join(OUT, 'VRC_part_VRC-Body.step'), bc)
    step(os.path.join(OUT, 'VRC_assembly.step'), root)
    em.execute(em.createFusionArchiveExportOptions(os.path.join(OUT, 'ST185-VRC-Enclosure.f3d'), root))
    files['ST185-VRC-Enclosure.f3d'] = os.path.getsize(os.path.join(OUT, 'ST185-VRC-Enclosure.f3d'))
    REPORT['files'] = files
    if globals().get('SAVE', True):
        REPORT['saved'] = doc.save('Dan markup 2026-10-18: LP-16 cutouts double-D (D18.5, flats 16.5 apart, top + bottom) per the CNLINKO '
                                   'LP-16-xxxSX-02-1xxx drawing (Claude Code 2026-10-18)')
print(json.dumps(REPORT, indent=1))
