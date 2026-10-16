"""SteveCAD audit v3 (2026-10-16) ported into the VRC and CSB3 Fusion documents (R74: their own documents, new versions only).
Every edit is a parametric change to the existing timeline (or one named feature added at its end), so the next export keeps it.
Idempotent: run it again and nothing changes. Run inside Fusion (Fusion MCP `fusion_mcp_execute`, featureType script):
    exec(open(r'<repo>/cad/enclosures/src/enclosure_fixes_v3.py').read(), {'__file__': r'<that path>', 'WHICH': 'vrc' | 'csb3'})
VRC (then run build_vrc_holder.py MODE 'build': the holder pockets follow the +1 bosses, it exports and saves):
  F01  tab slots 5.5 -> 6.6 x 10 (centres x +-26.3..+-29.7, y +-31.5)          F02  holder bosses top z 9.5 -> 10.5, tap drill 9.5 deep
  F04  the D30 LP-16 spotface cylinder runs in to x +-35.0 (depth face x +-41.5 kept): no feather edge at the R7.7 cavity corners
  F11  the 8 tab-to-body inside corners R3                                     F08  lid M3: already D2.5 x 9.5 + 118 deg, M3 x 8 (checked)
  OPEN-11 + Dan 2026-10-16 ("the enclosure vrc text is sideways and backwards"): IN / OUT read upright and unmirrored from outside,
       Arial Black 4.0 high (strokes about 0.9, a normal engraving cutter), 0.3 deep, under the LP-16 on each end face
CSB3 (exports its parts + the f3d, saves):
  F01  tab slots 5.5 -> 6.6 x 10 (centres x +-18.3..+-21.7, y +-41.5)           F08  standoff M3: D2.5 x 6.0 + point, M3 x 4.5
  F09  HD34 D-hole flat-to-arc corners R3 (flat at y 19.91 unchanged)          F11  tab corners R3 at x +-10, R1.9 at x +-30 (y +-35)
Claude Code, 2026-10-16.
"""
import adsk.core, adsk.fusion, math, os, json

app = adsk.core.Application.get()
VI = adsk.core.ValueInput
WHICH = globals().get('WHICH', 'vrc')
MAIN = r'C:\projects\active\st185-link-ecu-config'
REPORT = {'which': WHICH}


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def open_doc(name):
    for d in app.documents:
        if d.name.split(' v')[0] == name:
            d.activate()
            return d
    proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
    f = [f for f in proj.rootFolder.dataFiles if f.name == name][0]
    return app.documents.open(f, True)


def all_profiles(sk):
    c = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        c.add(sk.profiles.item(i))
    return c


def set_mm(param, v):
    """Set a model parameter to v mm (sign kept as given). Returns True when it changed."""
    old = param.value * 10.0
    if abs(old - v) < 1e-6:
        return False
    param.expression = '%g mm' % v
    return True


def slot_width(sk):
    ys = sorted(set(round(l.worldGeometry.startPoint.y * 10.0, 3) for l in sk.sketchCurves.sketchLines))
    return round(abs(ys[1] - ys[0]), 3) if len(ys) >= 2 else None


def healthy(f):
    return f.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState


def replace_cut(comp, f, prof, name):
    """With the timeline rolled to just before feature f: a new cut of the same distance from prof, then f is deleted and the new
    feature takes its name. (Setting f.profile there fails in Fusion with InternalValidationError curProfile.)"""
    d = f.extentOne.distance.value
    body = comp.bRepBodies.item(0)
    ei = comp.features.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setDistanceExtent(False, VI.createByReal(d))
    ei.participantBodies = [body]
    nf = comp.features.extrudeFeatures.add(ei)
    f.deleteMe()
    nf.name = name
    return nf


def redo_slots(des, comp, sk_name, ext_name, centres, w, L):
    """Redraw the tab slots w x L (long axis along x) in their own sketch and re-make the cut from it (timeline rolled to it)."""
    sk = comp.sketches.itemByName(sk_name)
    f = comp.features.extrudeFeatures.itemByName(ext_name)
    draw = abs((slot_width(sk) or 0) - w) > 1e-3
    if not draw and healthy(f):
        return 'already %.1f' % w
    f.timelineObject.rollTo(True)
    try:
        if draw:
            for c in [sk.sketchCurves.item(i) for i in range(sk.sketchCurves.count)]:
                c.deleteMe()
            a = (L - w) / 2.0
            for (cx, cy) in centres:
                A = sk.sketchCurves.sketchArcs
                a1 = A.addByCenterStartSweep(sk.modelToSketchSpace(P(cx + a, cy)), sk.modelToSketchSpace(P(cx + a, cy - w / 2)), math.pi)
                a2 = A.addByCenterStartSweep(sk.modelToSketchSpace(P(cx - a, cy)), sk.modelToSketchSpace(P(cx - a, cy + w / 2)), math.pi)
                Ln = sk.sketchCurves.sketchLines
                Ln.addByTwoPoints(a1.endSketchPoint, a2.startSketchPoint)
                Ln.addByTwoPoints(a2.endSketchPoint, a1.startSketchPoint)
        replace_cut(comp, f, all_profiles(sk), ext_name)
    finally:
        des.timeline.moveToEnd()
    return 'redrawn %d slots %.1f x %.1f' % (len(centres), w, L)


def edges_at(body, pts, z0, z1, tol=0.05):
    """Straight edges parallel to z through any (x, y) of pts, spanning z0..z1."""
    out = []
    for e in body.edges:
        g = e.geometry
        if not isinstance(g, adsk.core.Line3D):
            continue
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.x - b.x) > 1e-5 or abs(a.y - b.y) > 1e-5:
            continue
        x, y = a.x * 10.0, a.y * 10.0
        za, zb = sorted((a.z * 10.0, b.z * 10.0))
        if za < z0 - tol or zb > z1 + tol:
            continue
        if any(abs(x - px) < tol and abs(y - py) < tol for (px, py) in pts):
            out.append(e)
    return out


def fillet(comp, name, groups):
    """groups = [(edges, R)]; one constant-radius fillet feature named name (skipped when it exists)."""
    if any(comp.features.filletFeatures.item(i).name == name for i in range(comp.features.filletFeatures.count)):
        return 'exists'
    fi = comp.features.filletFeatures.createInput()
    n = 0
    for (edges, R) in groups:
        if not edges:
            continue
        c = adsk.core.ObjectCollection.create()
        for e in edges:
            c.add(e)
        fi.addConstantRadiusEdgeSet(c, VI.createByReal(R / 10.0), False)
        n += len(edges)
    if not n:
        return 'NO EDGES FOUND'
    f = comp.features.filletFeatures.add(fi)
    f.name = name
    return '%d edges' % n


def upright_text(des, comp, sk_name, ext_name, text, face_sign, yc, zc, h, box_w, box_h, font):
    """Replace the engraving text so it reads left to right, upright and not mirrored, seen from outside the end face at
    x = face_sign * |x|. The engraving sketches are on planes offset from YZ: sketch x = model -z, sketch y = model +y, normal +x.
    Seen from +x (IN end) a +90 deg turn of the text box gives baseline +y / up +z; seen from -x (OUT end) the text is also
    flipped horizontally, so baseline -y / up +z there."""
    sk = comp.sketches.itemByName(sk_name)
    f = comp.features.extrudeFeatures.itemByName(ext_name)
    t0 = sk.sketchTexts.item(0) if sk.sketchTexts.count else None
    if t0 is not None and t0.fontName == font and abs(t0.height * 10.0 - h) < 1e-6 and t0.isHorizontalFlip == (face_sign < 0) and healthy(f):
        return 'already upright'
    f.timelineObject.rollTo(True)
    try:
        for t in [sk.sketchTexts.item(i) for i in range(sk.sketchTexts.count)]:
            t.deleteMe()
        for c in [sk.sketchCurves.item(i) for i in range(sk.sketchCurves.count)]:
            c.deleteMe()
        xp = sk.referencePlane.geometry.origin.x * 10.0
        cen = sk.modelToSketchSpace(P(xp, yc, zc))
        # box laid out along the sketch x axis before the turn: box_w along x, box_h along y
        c1 = adsk.core.Point3D.create(cen.x - box_w / 20.0, cen.y - box_h / 20.0, 0)
        c2 = adsk.core.Point3D.create(cen.x + box_w / 20.0, cen.y + box_h / 20.0, 0)
        ti = sk.sketchTexts.createInput2(text, h / 10.0)
        ti.fontName = font
        ti.setAsMultiLine(c1, c2, adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                          adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
        ti.isHorizontalFlip = face_sign < 0
        st = sk.sketchTexts.add(ti)
        st.definition.rotate(math.pi / 2, adsk.fusion.TextBoxKeyPoints.MiddleTextBoxKeyPoint)
        replace_cut(comp, f, st, ext_name)
    finally:
        des.timeline.moveToEnd()
    return 'redone %r %s %.1f' % (text, font, h)


def export_all(des, prefix, folder, f3d_name):
    em = des.exportManager
    root = des.rootComponent
    files = {}
    for o in root.occurrences:
        o.isLightBulbOn = True
        for b in o.component.bRepBodies:
            b.isLightBulbOn = True
        n = o.component.name.replace(' ', '_').replace('(', '').replace(')', '')
        p = os.path.join(folder, '%s_part_%s.step' % (prefix, n))
        em.execute(em.createSTEPExportOptions(p, o.component))
        files[os.path.basename(p)] = os.path.getsize(p)
    p = os.path.join(folder, '%s_assembly.step' % prefix)
    em.execute(em.createSTEPExportOptions(p, root))
    files[os.path.basename(p)] = os.path.getsize(p)
    p = os.path.join(folder, f3d_name)
    em.execute(em.createFusionArchiveExportOptions(p, root))
    files[f3d_name] = os.path.getsize(p)
    return files


def vols(des):
    return {c.name: [round(b.volume * 1000.0, 1) for b in c.bRepBodies] for c in des.allComponents if c.bRepBodies.count}


# ================================================================ VRC
if WHICH == 'vrc':
    doc = open_doc('ST185-VRC-Enclosure')
    des = adsk.fusion.Design.cast(app.activeProduct)
    bc = [c for c in des.allComponents if c.name == 'VRC-Body'][0]
    ef = bc.features.extrudeFeatures
    REPORT['before'] = vols(des)
    REPORT['F01'] = redo_slots(des, bc, 'tab_slots', 'Extrude9', [(sx * 28.0, sy * 31.5) for sx in (-1, 1) for sy in (-1, 1)], 6.6, 10.0)
    # F04: the inside spotface cylinders start at x +-35 instead of +-38, same depth face (x +-41.5)
    ch = []
    for (pl, ex, x, d) in (('Plane3', 'Extrude7', 35.0, 6.5), ('Plane2', 'Extrude6', -35.0, -6.5)):
        plane = bc.constructionPlanes.itemByName(pl)
        ch.append(set_mm(plane.definition.offset, x))
        ch.append(set_mm(ef.itemByName(ex).extentOne.distance, d))
    REPORT['F04'] = 'spotface from x +-35 (changed %s)' % any(ch)
    # F11: tab-to-body inside corners (tab sides x +-18 / +-38 meet the body side y +-25), z 0..6
    b0 = bc.bRepBodies.item(0)
    REPORT['F11'] = fillet(bc, 'F11 tab corners R3', [(edges_at(b0, [(sx * x, sy * 25.0) for sx in (-1, 1) for sy in (-1, 1) for x in (18.0, 38.0)], 0.0, 6.0), 3.0)])
    # OPEN-11 + Dan: IN on the +x end, OUT on the -x end, under the LP-16 (its 25.5 face reaches down to z 8.25)
    REPORT['text_IN'] = upright_text(des, bc, 'engrave_IN', 'Extrude10', 'IN', 1, 0.0, 4.0, 4.0, 20.0, 5.0, 'Arial Black')
    REPORT['text_OUT'] = upright_text(des, bc, 'engrave_OUT', 'Extrude11', 'OUT', -1, 0.0, 4.0, 4.0, 20.0, 5.0, 'Arial Black')
    # F08 check (no change): the lid M3 tap drill
    h = bc.features.holeFeatures.itemByName('M3_lid_tapped (1)')
    REPORT['F08'] = 'lid M3 D%.2f x %.2f, tip %s' % (h.holeDiameter.value * 10, h.extentDefinition.distance.value * 10, h.tipAngle.expression)
    REPORT['after'] = vols(des)
    REPORT['health'] = [(it.name, it.healthState) for it in des.timeline if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]

# ================================================================ CSB3
if WHICH == 'csb3':
    doc = open_doc('ST185-CSB3-Enclosure')
    des = adsk.fusion.Design.cast(app.activeProduct)
    bc = [c for c in des.allComponents if c.name == 'CSB3-Body'][0]
    lc = [c for c in des.allComponents if c.name == 'CSB3-Lid'][0]
    REPORT['before'] = vols(des)
    REPORT['F01'] = redo_slots(des, bc, 'tab_slots', 'Extrude6', [(sx * 20.0, sy * 41.5) for sx in (-1, 1) for sy in (-1, 1)], 6.6, 10.0)
    h = bc.features.holeFeatures.itemByName('M3_csb3_tapped (1)')
    REPORT['F08'] = 'standoff M3 depth changed %s' % set_mm(h.extentDefinition.distance, 6.0)
    b0 = bc.bRepBodies.item(0)
    REPORT['F11'] = fillet(bc, 'F11 tab corners R3 / R1.9', [
        (edges_at(b0, [(sx * 10.0, sy * 35.0) for sx in (-1, 1) for sy in (-1, 1)], 0.0, 6.0), 3.0),
        (edges_at(b0, [(sx * 30.0, sy * 35.0) for sx in (-1, 1) for sy in (-1, 1)], 0.0, 6.0), 1.9)])
    l0 = lc.bRepBodies.item(0)
    fe = [e for e in edges_at(l0, [(-8.22, 19.91), (8.22, 19.91)], 50.0, 56.0, tol=0.1)]
    REPORT['F09'] = fillet(lc, 'F09 D-hole corners R3', [(fe, 3.0)])
    REPORT['after'] = vols(des)
    REPORT['health'] = [(it.name, it.healthState) for it in des.timeline if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    # F17: how much room the (envelope) board has - board / parts block to the HD34 rear and to the cavity walls
    root = des.rootComponent
    occ = {o.component.name: o for o in root.occurrences}
    mm_ = lambda a, b: round(app.measureManager.measureMinimumDistance(a, b).value * 10.0, 2)
    brd = occ['ECUMaster CSB3 (manual v2.1 p.4)'].bRepBodies
    REPORT['F17_room'] = dict(parts_to_HD34=mm_(brd.item(1), occ['HD34-24-33PE (envelope from TE CVM model)'].bRepBodies.item(0)),
                              board_to_body=mm_(brd.item(0), occ['CSB3-Body'].bRepBodies.item(0)))
    if globals().get('SAVE', True) and not REPORT['health']:
        REPORT['files'] = export_all(des, 'CSB3', os.path.join(MAIN, 'cad', 'enclosures', 'csb3'), 'ST185-CSB3-Enclosure.f3d')
        doc.save('SteveCAD audit v3: tab slots 6.6 (F01), standoff M3 6.0 + point (F08), D-hole corners R3 (F09), tab corners R3 / R1.9 (F11) '
                 '(Claude Code 2026-10-16)')
        REPORT['saved'] = True

# ================================================================ CSB3 lid loft (Dan 2026-10-16)
# Dan: "if the csb3 connector is too deep look for a similar one that is a shallow mount or low profile otherwise we can create a raised
# area or loft for the connector on the lid to move it a little bit further away without modifying the entire enclosure". No shallow
# HD30-family receptacle mates the HD36-24-33SE (TE lists the HD34-24-33PE jam-nut receptacle only), so: a round loft on the LID only,
# LOFT_H high, the HD34 panel (4.0) at its top, the D54 flange seat run up to it, the HD34 envelope moved up with it. Body unchanged.
LOFT_H, LOFT_D = 6.0, 62.0
if WHICH == 'csb3_loft':
    doc = open_doc('ST185-CSB3-Enclosure')
    des = adsk.fusion.Design.cast(app.activeProduct)
    lc = [c for c in des.allComponents if c.name == 'CSB3-Lid'][0]
    hc = [c for c in des.allComponents if c.name.startswith('HD34-24-33PE')][0]
    occ = {o.component.name: o for o in des.rootComponent.occurrences}
    REPORT['before'] = vols(des)
    mm_ = lambda a, b: round(app.measureManager.measureMinimumDistance(a, b).value * 10.0, 2)
    brd = occ['ECUMaster CSB3 (manual v2.1 p.4)'].bRepBodies
    REPORT['room_before'] = dict(parts_to_HD34=mm_(brd.item(1), occ[hc.name].bRepBodies.item(0)), board_to_HD34=mm_(brd.item(0), occ[hc.name].bRepBodies.item(0)))
    ef = lc.features.extrudeFeatures
    if ef.itemByName('CSB3 lid loft') is None:
        for i in range(lc.features.filletFeatures.count - 1, -1, -1):        # the D-hole corner radii are re-made on the taller cut below
            if lc.features.filletFeatures.item(i).name.startswith('F09'):
                lc.features.filletFeatures.item(i).deleteMe()
        e2, e3 = ef.itemByName('Extrude2'), ef.itemByName('Extrude3')         # D-hole cut, flange seat
        e2.timelineObject.rollTo(True)
        try:
            pin = lc.constructionPlanes.createInput()
            pin.setByOffset(lc.xYConstructionPlane, VI.createByReal(56.0 / 10.0))
            pl = lc.constructionPlanes.add(pin); pl.name = 'loft base'; pl.isLightBulbOn = False
            sk = lc.sketches.add(pl); sk.name = 'CSB3 lid loft'
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(0, 0, 56.0)), LOFT_D / 20.0)
            ei = ef.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            ei.setDistanceExtent(False, VI.createByReal(LOFT_H / 10.0))
            ei.participantBodies = [lc.bRepBodies.item(0)]
            ef.add(ei).name = 'CSB3 lid loft'
        finally:
            des.timeline.moveToEnd()
        set_mm(e2.extentOne.distance, 6.0 + LOFT_H)          # D-hole through lid + loft
        set_mm(e3.extentOne.distance, 2.0 + LOFT_H)          # D54 seat up to the panel under the loft top (panel stays 4.0)
        # the HD34 envelope up by LOFT_H: its profile sketch and the D-flat cut plane
        skh = hc.sketches.itemByName('HD34_profile')
        ents = adsk.core.ObjectCollection.create()
        for c in skh.sketchCurves:
            ents.add(c)
        v = skh.modelToSketchSpace(P(0, 0, LOFT_H)); o = skh.modelToSketchSpace(P(0, 0, 0))
        m = adsk.core.Matrix3D.create(); m.translation = adsk.core.Vector3D.create(v.x - o.x, v.y - o.y, v.z - o.z)
        skh.move(ents, m)
        fp = hc.constructionPlanes.itemByName('Plane1')
        set_mm(fp.definition.offset, fp.definition.offset.value * 10.0 + LOFT_H)
    l0 = lc.bRepBodies.item(0)
    REPORT['F09'] = fillet(lc, 'F09 D-hole corners R3', [(edges_at(l0, [(-8.22, 19.91), (8.22, 19.91)], 50.0, 56.0 + LOFT_H, tol=0.1), 3.0)])
    REPORT['after'] = vols(des)
    REPORT['health'] = [(it.name, it.healthState) for it in des.timeline if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    occ = {o.component.name: o for o in des.rootComponent.occurrences}
    brd = occ['ECUMaster CSB3 (manual v2.1 p.4)'].bRepBodies
    hb = occ[hc.name].bRepBodies.item(0)
    REPORT['room_after'] = dict(parts_to_HD34=mm_(brd.item(1), hb), board_to_HD34=mm_(brd.item(0), hb),
                                HD34_to_lid_clash=round(sum(0 for _ in [0]), 1))
    lb = l0.boundingBox
    REPORT['lid_top_z'] = round(lb.maxPoint.z * 10.0, 2)
    if globals().get('SAVE', True) and not REPORT['health']:
        REPORT['files'] = export_all(des, 'CSB3', os.path.join(MAIN, 'cad', 'enclosures', 'csb3'), 'ST185-CSB3-Enclosure.f3d')
        doc.save('Dan 2026-10-16: 6 mm loft on the lid for the HD34 (wire room over the CSB3 board), body unchanged (Claude Code 2026-10-16)')
        REPORT['saved'] = True

print(json.dumps(REPORT, indent=1))
