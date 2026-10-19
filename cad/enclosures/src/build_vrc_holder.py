"""VRC board holder v2 (Dan M9, DECISIONS R126 - supersedes the v1 holder / K7) built into the existing Fusion document ST185-VRC-Enclosure
(R74: no new document). Run inside Fusion (Fusion MCP `fusion_mcp_execute`, featureType script) with
    exec(open(r'<repo>/cad/enclosures/src/build_vrc_holder.py').read(), {'__file__': r'<that path>', 'MODE': 'build'})
MODE 'build': replaces the board and the holder with
  - "OpenLogicEFI NCV1124 VR module RevB3": the board from the maker's KiCad file (PCB, IC1 body; no header - leads solder on its top)
  - "VRC board holder (printed)": ONE extruded block, parametric sketches + extrudes (edit them in Fusion): flush board pocket, 4 snap
    tabs, solder reliefs, 2 x M6 countersinks + boss recesses
  and edits the enclosure body once: the 4 M3 floor bosses (Extrude8, M3_carrier_tapped, Thread2) suppressed, 2 M6 bosses + D5.0 tap
  drill added (M6_holder_bosses, M6_tap_drill). Then it checks the holder (one solid, no clash with anything in the box), exports the
  STEP / STL / f3d into the main checkout's cad/enclosures/vrc/ and saves the document (SAVE=False to review first).
MODE 'wires': adds the internal leads as Tmp_ bodies (vrc_holder_spec.wires(), 3 x OD bends), checks them against every
  part and each other, renders the snapshots, removes the Tmp_ bodies again and closes the document WITHOUT saving.
Numbers: vrc_holder_spec.py. Claude Code, 2026-10-15; v2 2026-10-16.
"""
import adsk.core, adsk.fusion, os, sys, json, math, importlib

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import vrc_holder_spec as S
importlib.reload(S)
MODE = globals().get('MODE', 'build')
MAIN = r'C:\projects\active\st185-link-ecu-config'
OUT = os.path.join(MAIN, 'cad', 'enclosures', 'vrc')
SNAP = globals().get('SNAP', os.path.join(MAIN, '_research', 'snapshots', '2026-10-15-vrc-holder'))
DOC = 'ST185-VRC-Enclosure'
HOLDER, MODULE = 'VRC board holder (printed)', 'OpenLogicEFI NCV1124 VR module RevB3'
OLD = ('Standoffs Keystone 25510', 'VRC carrier board', 'OpenLogicEFI NCV1124', 'VRC board holder', 'Tmp_')

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
VI = adsk.core.ValueInput
NEW, JOIN, CUT = (adsk.fusion.FeatureOperations.NewBodyFeatureOperation, adsk.fusion.FeatureOperations.JoinFeatureOperation,
                  adsk.fusion.FeatureOperations.CutFeatureOperation)
REPORT = {'mode': MODE}


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def V(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


def mm(v):
    return VI.createByReal(v / 10.0)


# ---------------------------------------------------------------- document
doc = None
for d in app.documents:
    if d.name.startswith(DOC):
        doc = d
if doc is None:
    for p in app.data.dataProjects:
        if p.name == 'Default Project':
            for i in range(p.rootFolder.dataFiles.count):
                f = p.rootFolder.dataFiles.item(i)
                if f.name == DOC:
                    doc = app.documents.open(f, True)
doc.activate()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent


def occ_named(prefix):
    return [o for o in root.occurrences if o.component.name.startswith(prefix)]


def box(cx, cy, cz, lx, ly, lz):
    return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P(cx, cy, cz), V(1, 0, 0), V(0, 1, 0), lx / 10.0, ly / 10.0, lz / 10.0))


def plane_z(comp, z):
    pin = comp.constructionPlanes.createInput()
    pin.setByOffset(comp.xYConstructionPlane, mm(z))
    pl = comp.constructionPlanes.add(pin)
    pl.isLightBulbOn = False
    return pl


def plane_x(comp, x):
    pin = comp.constructionPlanes.createInput()
    pin.setByOffset(comp.yZConstructionPlane, mm(x))
    pl = comp.constructionPlanes.add(pin)
    pl.isLightBulbOn = False
    return pl


def rrect(sk, cx, cy, w, h, r):
    """Rounded rectangle (lines + corner arcs) in model XY on a sketch parallel to XY."""
    L, A = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    zc = sk.origin.z * 10

    def p(x, y):
        return sk.modelToSketchSpace(P(x, y, zc))
    L.addByTwoPoints(p(x0 + r, y0), p(x1 - r, y0))
    L.addByTwoPoints(p(x1, y0 + r), p(x1, y1 - r))
    L.addByTwoPoints(p(x1 - r, y1), p(x0 + r, y1))
    L.addByTwoPoints(p(x0, y1 - r), p(x0, y0 + r))
    for (ccx, ccy, sx, sy) in ((x1 - r, y0 + r, x1 - r, y0), (x1 - r, y1 - r, x1, y1 - r), (x0 + r, y1 - r, x0 + r, y1), (x0 + r, y0 + r, x0, y0 + r)):
        A.addByCenterStartSweep(p(ccx, ccy), p(sx, sy), math.pi / 2)


def poly(sk, pts3):
    """Closed polygon through model points (on the sketch plane)."""
    L = sk.sketchCurves.sketchLines
    q = [sk.modelToSketchSpace(P(*p)) for p in pts3]
    for i in range(len(q)):
        L.addByTwoPoints(q[i], q[(i + 1) % len(q)])


def ext(comp, sk, dist, op, body=None, name=None, prof=None):
    pr = prof if prof is not None else sk.profiles.item(0)
    ei = comp.features.extrudeFeatures.createInput(pr, op)
    ei.setDistanceExtent(False, mm(dist))
    if body is not None and op != NEW:
        ei.participantBodies = [body]
    f = comp.features.extrudeFeatures.add(ei)
    if name:
        f.name = name
    return f


def all_profiles(sk):
    c = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        c.add(sk.profiles.item(i))
    return c


def base_bodies(comp, items):
    bf = comp.features.baseFeatures.add()
    bf.startEdit()
    out = []
    for b, n in items:
        nb = comp.bRepBodies.add(b, bf)
        nb.name = n
        out.append(nb)
    bf.finishEdit()
    return out


alib = app.materialLibraries.itemByName('Fusion Appearance Library')


def col(name, rgb, base='Plastic - Glossy (Red)'):
    a = des.appearances.itemByName(name)
    if a is None:
        a = des.appearances.addByCopy(alib.appearances.itemByName(base), name)
        for i in range(a.appearanceProperties.count):
            pr = a.appearanceProperties.item(i)
            if isinstance(pr, adsk.core.ColorProperty) and pr.name in ('Color', 'Colour'):
                pr.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                break
    return a


def world(o):
    return [o.bRepBodies.item(i) for i in range(o.bRepBodies.count)]


def vol_overlap(b1, b2):
    a = tb.copy(b1)
    tb.booleanOperation(a, tb.copy(b2), adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return a.volume * 1000.0 if a else 0.0   # cm3 -> mm3


def min_dist(b1, b2):
    try:
        return app.measureManager.measureMinimumDistance(b1, b2).value * 10.0
    except Exception:
        return None


# ================================================================ BUILD
if MODE == 'build':
    for o in list(root.occurrences):
        if o.component.name.startswith(OLD):
            o.deleteMe()

    # ---------------- the board, from the KiCad file (v2, R126: wires soldered on its top - no header fitted)
    mo = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    mc = mo.component
    mc.name = MODULE
    sk = mc.sketches.add(plane_z(mc, S.Z_BOARD))
    sk.name = 'PCB outline (KiCad Edge.Cuts)'
    rrect(sk, 0, 0, S.PCB_X, S.PCB_Y, S.PCB_R)
    ext(mc, sk, S.PCB_T, NEW, name='PCB')
    mc.bRepBodies.item(0).name = 'VR module PCB'
    so = S.SO8
    base_bodies(mc, [(box((so['x0'] + so['x1']) / 2, (so['y0'] + so['y1']) / 2, S.Z_TOP + so['h'] / 2, so['x1'] - so['x0'], so['y1'] - so['y0'], so['h']),
                      'NCV1124 SO-8 envelope')])
    green, black = col('VRC pcb green', (20, 110, 50)), col('VRC ic black', (30, 30, 32))
    for b in mc.bRepBodies:
        b.appearance = green if 'PCB' in b.name else black

    # ---------------- enclosure (VRC-Body, same document): v2 bosses (R126). The 4 M3 floor bosses of the v1 holder, their tapped
    # holes and thread are suppressed (kept in the timeline); 2 bosses under the holder screws with the M6 tap drill hole, added once.
    bo_ = occ_named('VRC-Body')[0]
    bc = bo_.component
    ef = bc.features.extrudeFeatures
    f8 = ef.itemByName('Extrude8')                              # 'bosses' sketch -> Extrude8 (4 x D7 x 3 M3 bosses)
    if f8 is not None and not f8.timelineObject.isSuppressed:
        f8.timelineObject.isSuppressed = True
    for coll in (bc.features.holeFeatures, bc.features.threadFeatures, ef):
        for i in range(coll.count):
            f = coll.item(i)
            if (f.name.startswith('M3_carrier_tapped') or f.name == 'Thread2') and not f.timelineObject.isSuppressed:
                f.timelineObject.isSuppressed = True
    REPORT['suppressed'] = [bc.features.item(i).name for i in range(bc.features.count) if bc.features.item(i).timelineObject.isSuppressed]
    body_b = bc.bRepBodies.item(0)
    # SteveCAD v3 (2026-10-16): Fusion names a second 'M6_holder_bosses' 'M6_holder_bosses (1)', so the old exact-name test let every
    # rerun add another boss + drill set (three sets were in the timeline). Keep the first set, delete the copies, and set its
    # height / drill depth from the spec every run (F02: boss top z 10.5, drill 9.5)
    def named(coll, stem):
        return [coll.item(i) for i in range(coll.count) if coll.item(i).name == stem or coll.item(i).name.startswith(stem + ' (')]
    for stem in ('M6_holder_bosses', 'M6_tap_drill'):
        fs = sorted(named(ef, stem), key=lambda f: f.timelineObject.index)
        for f in fs[1:]:
            sk_ = f.profile.item(0).parentSketch if isinstance(f.profile, adsk.core.ObjectCollection) else f.profile.parentSketch
            pl_ = sk_.referencePlane
            f.deleteMe(); sk_.deleteMe(); pl_.deleteMe()
            REPORT.setdefault('deleted_copies', []).append(stem)
    fb = named(ef, 'M6_holder_bosses')
    fd = named(ef, 'M6_tap_drill')
    if fb and fd:
        fb[0].extentOne.distance.expression = '%g mm' % S.BOSS2_H
        sk_ = fd[0].profile.item(0).parentSketch if isinstance(fd[0].profile, adsk.core.ObjectCollection) else fd[0].profile.parentSketch
        sk_.referencePlane.definition.offset.expression = '%g mm' % (S.FLOOR_Z + S.BOSS2_H)
        fd[0].extentOne.distance.expression = '%g mm' % -S.PILOT_DEPTH
        REPORT['bosses'] = 'top z %.1f, drill %.1f deep' % (S.FLOOR_Z + S.BOSS2_H, S.PILOT_DEPTH)
    if not fb:
        sk = bc.sketches.add(plane_z(bc, S.FLOOR_Z)); sk.name = 'M6_holder_bosses'
        for (x, y) in S.SCREWS:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x, y, S.FLOOR_Z)), S.BOSS2_D / 20.0)
        ext(bc, sk, S.BOSS2_H, JOIN, body_b, 'M6_holder_bosses', all_profiles(sk))
    if not fd:
        sk = bc.sketches.add(plane_z(bc, S.FLOOR_Z + S.BOSS2_H)); sk.name = 'M6_tap_drill'
        for (x, y) in S.SCREWS:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x, y, S.FLOOR_Z + S.BOSS2_H)), S.PILOT_D / 20.0)
        ext(bc, sk, -S.PILOT_DEPTH, CUT, body_b, 'M6_tap_drill', all_profiles(sk))

    # ---------------- the holder v2: one extruded block
    ho = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    hc = ho.component
    hc.name = HOLDER
    B = S.BLOCK
    z0 = B['z0']
    sk = hc.sketches.add(plane_z(hc, z0)); sk.name = 'block'
    X, Xn, Y, Yn = B['x'], B['x_notch'], B['y'], B['y_notch']
    poly(sk, [(-X, -Y, z0), (X, -Y, z0), (X, -Yn, z0), (Xn, -Yn, z0), (Xn, Yn, z0), (X, Yn, z0),
              (X, Y, z0), (-X, Y, z0), (-X, Yn, z0), (-Xn, Yn, z0), (-Xn, -Yn, z0), (-X, -Yn, z0)])
    ext(hc, sk, B['z1'] - z0, NEW, name='block')
    body = hc.bRepBodies.item(0)
    body.name = 'VRC board holder'
    # board pocket (board + FIT a side), flush: the board top is the block top
    sk = hc.sketches.add(plane_z(hc, S.Z_TOP)); sk.name = 'board pocket'
    rrect(sk, 0, 0, S.POCKET[0], S.POCKET[1], S.POCKET[2])
    ext(hc, sk, -S.PCB_T, CUT, body, 'board pocket')
    # N4: lead reliefs at the block ends, under the leads from the lowest LP-16 cups
    LR = S.LEAD_RELIEF
    sk = hc.sketches.add(plane_z(hc, B['z1'])); sk.name = 'lead reliefs'
    for sx in (-1, 1):
        poly(sk, [(sx * x_, sx * y_, B['z1']) for (x_, y_) in S.lead_relief()])
    ext(hc, sk, -(B['z1'] - LR['z']), CUT, body, 'lead reliefs', all_profiles(sk))
    # solder-tip reliefs under the two pin rows
    sk = hc.sketches.add(plane_z(hc, S.Z_BOARD)); sk.name = 'solder reliefs'
    for xr in (S.PIN_X[1], S.PIN_X[5]):
        p0 = sk.modelToSketchSpace(P(xr - S.RELIEF['w'] / 2, -S.RELIEF['l'] / 2, S.Z_BOARD))
        p1 = sk.modelToSketchSpace(P(xr + S.RELIEF['w'] / 2, S.RELIEF['l'] / 2, S.Z_BOARD))
        sk.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
    ext(hc, sk, -S.RELIEF['d'], CUT, body, 'solder reliefs', all_profiles(sk))
    # recesses over the enclosure's 2 bosses, clearance holes, 90 deg countersinks
    sk = hc.sketches.add(plane_z(hc, z0)); sk.name = 'boss recesses'
    for (x, y) in S.SCREWS:
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x, y, z0)), S.RECESS_D / 20.0)
    ext(hc, sk, S.RECESS_H, CUT, body, 'boss recesses', all_profiles(sk))
    sk = hc.sketches.add(plane_z(hc, B['z1'])); sk.name = 'M6 clearance'
    for (x, y) in S.SCREWS:
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x, y, B['z1'])), S.CLEAR / 20.0)
    ext(hc, sk, -(B['z1'] - z0), CUT, body, 'M6 clearance', all_profiles(sk))
    sk = hc.sketches.add(plane_z(hc, B['z1'])); sk.name = 'M6 countersinks'
    for (x, y) in S.SCREWS:
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x, y, B['z1'])), S.CSK_D / 20.0)
    ei = hc.features.extrudeFeatures.createInput(all_profiles(sk), CUT)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(mm(S.CSK_DEPTH)), adsk.fusion.ExtentDirections.NegativeExtentDirection,
                        VI.createByString('-45 deg'))
    ei.participantBodies = [body]
    hc.features.extrudeFeatures.add(ei).name = 'M6 countersinks'
    # snap tabs: slot behind each arm + slits at its ends (cut), then the lip with its lead-in on the arm (join)
    yi = S.POCKET[1] / 2
    yo = yi + S.TAB_T + S.TAB_GAP
    sk = hc.sketches.add(plane_z(hc, B['z1'])); sk.name = 'tab slots'
    for s_ in (1, -1):
        for (xa, xb) in S.TABS_X:
            for (q0, q1) in (((xa, s_ * (yi + S.TAB_T)), (xb, s_ * yo)),
                             ((xa - S.TAB_SLIT, s_ * yi), (xa, s_ * yo)),
                             ((xb, s_ * yi), (xb + S.TAB_SLIT, s_ * yo))):
                sk.sketchCurves.sketchLines.addTwoPointRectangle(sk.modelToSketchSpace(P(q0[0], q0[1], B['z1'])),
                                                                 sk.modelToSketchSpace(P(q1[0], q1[1], B['z1'])))
    ext(hc, sk, -(B['z1'] - S.TAB_Z0), CUT, body, 'tab slots', all_profiles(sk))
    zt, zl = S.Z_TOP, S.Z_TOP + S.LIP_GAP
    for (xa, xb) in S.TABS_X:
        sk = hc.sketches.add(plane_x(hc, xa)); sk.name = 'tab lips x %.1f' % xa
        for s_ in (1, -1):
            poly(sk, [(xa, s_ * (yi + S.TAB_T), zt), (xa, s_ * (yi + S.TAB_T), zl + S.LIP_H), (xa, s_ * yi, zl + S.LIP_H),
                      (xa, s_ * (yi - S.LIP_IN), zl), (xa, s_ * yi, zl), (xa, s_ * yi, zt)])
        ext(hc, sk, xb - xa, JOIN, body, 'tab lips x %.1f' % xa, all_profiles(sk))
    body.appearance = col('VRC holder PA12 grey', (150, 150, 146), 'Plastic - Matte (Gray)')
    try:
        mat = app.materialLibraries.itemByName('Fusion Material Library').materials.itemByName('Nylon 12')
        if mat:
            hc.material = mat
    except Exception:
        pass

    # ---------------- checks
    hb = ho.bRepBodies.item(0)
    REPORT['holder'] = dict(bodies=hc.bRepBodies.count, lumps=hb.lumps.count, shells=hb.shells.count,
                            volume_mm3=round(hb.volume * 1000, 1), solid=hb.isSolid,
                            bbox=[round(v * 10, 2) for v in (hb.boundingBox.minPoint.x, hb.boundingBox.minPoint.y, hb.boundingBox.minPoint.z,
                                                              hb.boundingBox.maxPoint.x, hb.boundingBox.maxPoint.y, hb.boundingBox.maxPoint.z)])
    clash, gaps = {}, {}
    others = [(o.component.name, b) for o in root.occurrences if o.component.name != HOLDER for b in world(o)]
    for n, b in others:
        v = vol_overlap(hb, b)
        if v > 1e-4:
            clash['%s | %s' % (n, b.name)] = round(v, 4)
        d = min_dist(hb, b)
        gaps['%s | %s' % (n, b.name)] = None if d is None else round(d, 2)
    REPORT['holder_clash_mm3'] = clash
    REPORT['holder_gap_mm'] = gaps
    mods = [(o.component.name, b) for o in root.occurrences if o.component.name == MODULE for b in world(o)]
    mclash = {}
    for n, b in mods:
        for n2, b2 in others:
            if n2 == MODULE:
                continue
            v = vol_overlap(b, b2)
            if v > 1e-4:
                mclash['%s / %s | %s' % (b.name, n2, b2.name)] = round(v, 4)
    REPORT['module_clash_mm3'] = mclash
    REPORT['screw'] = '%s: head flush at z %.1f, %.1f mm of thread from the boss top (z %.1f); tap drill D%.1f x %.1f deep (%s)' % (
        S.SCREW_PN, S.Z_TOP, S.SCREW_LEN - (S.Z_TOP - S.FLOOR_Z - S.BOSS2_H), S.FLOOR_Z + S.BOSS2_H, S.PILOT_D, S.PILOT_DEPTH, S.TAP)

    # ---------------- exports
    if not globals().get('EXPORT', True):
        print(json.dumps(REPORT, indent=1))
        raise SystemExit
    em = des.exportManager
    files = {}
    for o in root.occurrences:          # STEP skips hidden bodies (the lid body was hidden in v1)
        o.isLightBulbOn = True
        for b in o.component.bRepBodies:
            b.isLightBulbOn = True

    def step(path, comp):
        em.execute(em.createSTEPExportOptions(path, comp))
        files[os.path.basename(path)] = os.path.getsize(path)
    step(os.path.join(OUT, 'VRC_part_VRC-Board-Holder.step'), hc)
    step(os.path.join(OUT, 'VRC_part_OpenLogicEFI_NCV1124_VR_module_RevB3.step'), mc)
    step(os.path.join(OUT, 'VRC_part_VRC-Body.step'), bc)
    stl = em.createSTLExportOptions(ho, os.path.join(OUT, 'VRC_part_VRC-Board-Holder.stl'))
    stl.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    stl.isBinaryFormat = True
    em.execute(stl)
    files['VRC_part_VRC-Board-Holder.stl'] = os.path.getsize(os.path.join(OUT, 'VRC_part_VRC-Board-Holder.stl'))
    step(os.path.join(OUT, 'VRC_assembly.step'), root)
    em.execute(em.createFusionArchiveExportOptions(os.path.join(OUT, 'ST185-VRC-Enclosure.f3d'), root))
    files['ST185-VRC-Enclosure.f3d'] = os.path.getsize(os.path.join(OUT, 'ST185-VRC-Enclosure.f3d'))
    REPORT['files'] = files
    if globals().get('SAVE', True) and not (clash or mclash) and hb.lumps.count == 1 and hc.bRepBodies.count == 1:
        try:
            REPORT['saved'] = doc.save(globals().get('MSG', 'VRC board holder v2 (Dan M9, R126): one extruded block, flush board, 4 snap tabs, 2 x M6 csk; '
                                                     'body: 2 M6 bosses with D5.0 tap drill, the 4 M3 bosses suppressed'))
        except Exception as e:
            REPORT['saved'] = 'FAILED: %s' % e
    else:
        REPORT['saved'] = False

# ================================================================ WIRES + SNAPSHOTS
if MODE == 'wires':
    os.makedirs(SNAP, exist_ok=True)
    tmp_o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    tc = tmp_o.component
    tc.name = 'Tmp_internal leads M22759-16-20'
    items, segs = [], {}
    for name, pts in S.wires().items():
        sp, probs = S.smooth(pts)
        w = None
        for i in range(len(sp) - 1):
            if S._ln(S._sub(sp[i + 1], sp[i])) < 1e-3:
                continue
            c = tb.createCylinderOrCone(P(*sp[i]), S.OD / 20.0, P(*sp[i + 1]), S.OD / 20.0)
            w = c if w is None else (tb.booleanOperation(w, c, adsk.fusion.BooleanTypes.UnionBooleanType) and w)
            if 0 < i:
                tb.booleanOperation(w, tb.createSphere(P(*sp[i]), S.OD / 20.0), adsk.fusion.BooleanTypes.UnionBooleanType)
        items.append((w, name))
        segs[name] = probs
    wb = base_bodies(tc, items)
    cIN, cOUT, cDR = col('VRC lead IN blue', (30, 85, 205)), col('VRC lead OUT yellow', (245, 200, 20)), col('VRC drain grey', (150, 150, 150))
    for b in wb:
        b.appearance = cDR if b.name.startswith('drain') else (cIN if b.name.startswith('IN') else cOUT)
    # checks: every lead against every part (not its own cup / pin ends: the leads stop 0.3 short of the cup and beside the pin)
    hits, close = {}, {}
    parts = [(o.component.name, b) for o in root.occurrences if not o.component.name.startswith('Tmp_') for b in world(o)]
    for b in tmp_o.bRepBodies:
        for n, pb in parts:
            v = vol_overlap(b, pb)
            if v > 1e-4:
                hits['%s / %s | %s' % (b.name, n, pb.name)] = round(v, 4)
            d = min_dist(b, pb)
            if d is not None and d < 1.0:
                close['%s / %s | %s' % (b.name, n, pb.name)] = round(d, 2)
    ww = {}
    L = list(tmp_o.bRepBodies)
    for i, a in enumerate(L):
        for b in L[i + 1:]:
            v = vol_overlap(a, b)
            d = min_dist(a, b)
            ww['%s / %s' % (a.name, b.name)] = (round(v, 4), None if d is None else round(d, 2))
    REPORT['lead_clash_mm3'] = hits
    REPORT['lead_closer_than_1mm'] = close
    REPORT['lead_pairs_min_gap'] = min((d for v, d in ww.values() if d is not None), default=None)
    REPORT['lead_pairs_overlap'] = {k: v for k, (v, d) in ww.items() if v > 1e-4}
    REPORT['bend_problems'] = {k: v for k, v in segs.items() if v}
    REPORT['bend_radius_centre_mm'] = round(S.R_BEND, 2)

    # ---------------- snapshots
    vp = app.activeViewport
    occ = {o.component.name: o for o in root.occurrences}

    def show(names_off=(), body_opacity=None):
        for o in root.occurrences:
            o.isLightBulbOn = not any(o.component.name.startswith(n) for n in names_off)
        for o in root.occurrences:
            if o.component.name == 'VRC-Body':
                for b in o.component.bRepBodies:
                    b.opacity = 1.0 if body_opacity is None else body_opacity

    def shot(fn, d, target, ext=1.15, style=None):
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
        n = math.sqrt(sum(x * x for x in d))
        d = [x / n for x in d]
        cam.target = P(*target)
        cam.eye = P(*(t + k * 1500.0 for t, k in zip(target, d)))
        cam.upVector = V(0, 0, 1) if abs(d[2]) < 0.97 else V(0, 1, 0)
        cam.isFitView = True
        vp.camera = cam
        cam = vp.camera
        cam.isFitView = False
        cam.viewExtents = cam.viewExtents * ext
        vp.camera = cam
        vp.visualStyle = style if style is not None else adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
        vp.refresh()
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(SNAP, fn), 1600, 1150)
    lid_off = ('VRC-Lid', 'ORING')
    show(lid_off)
    shot('vrc_holder_open_iso.png', (0.62, -0.95, 0.9), (0, 0, 20))
    shot('vrc_holder_open_top.png', (0, 0, 1), (0, 0, 20))
    show(lid_off, body_opacity=0.25)
    shot('vrc_holder_side_xray.png', (0, -1, 0), (0, 0, 20))
    show(lid_off + ('VRC-Body', 'LP16', 'Tmp_'))
    shot('vrc_holder_with_board_iso.png', (0.62, -0.95, 0.8), (0, 0, 18))
    show(lid_off + ('VRC-Body', 'LP16', 'Tmp_', 'OpenLogicEFI'))
    shot('vrc_holder_part_iso.png', (0.62, -0.95, 0.8), (0, 0, 16))
    shot('vrc_holder_part_top.png', (0, 0, 1), (0, 0, 16))
    show(())
    for o in root.occurrences:
        if o.component.name == 'VRC-Body':
            for b in o.component.bRepBodies:
                b.opacity = 1.0
    REPORT['snapshots'] = sorted(f for f in os.listdir(SNAP) if f.endswith('.png'))
    tmp_o.deleteMe()
    if globals().get('CLOSE', True):
        doc.close(False)

print(json.dumps(REPORT, indent=1))
