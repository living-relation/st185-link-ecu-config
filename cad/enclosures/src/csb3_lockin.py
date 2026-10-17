"""CSB3 lock-in supports + M8 set screw seal (Dan 2026-10-16, DECISIONS R133) ported into the CSB3 Fusion document
(R74: the existing document ST185-CSB3-Enclosure, new version only; no test documents).
Every edit is a parametric change to the existing timeline or a named feature added at its end, so the next export keeps it.
Idempotent: run it again and nothing changes. Run inside Fusion (Fusion MCP `fusion_mcp_execute`, featureType script):
    exec(open(r'<repo>/cad/enclosures/src/csb3_lockin.py').read(), {'__file__': r'<that path>', 'SAVE': True})
Changes (positions (13.5, 13.5) and (-13.5, -13.5), board underside z 18.0 unchanged):
  L1  PCB standoffs Keystone 25510 + M3 studs -> Cat. 8847 L = 10.0 metric nylon lock-in supports (4.00 holes, 1.57 PCB / 1.57 chassis,
      body D6.0, snap heads 4.83 / 3.18 long; boss top z 8.0 + L 10 = board z 18.0, so the board height is unchanged)
  L2  boss sketch D7 -> D10; the M3 tap hole + thread (F08) suppressed, i.e. filled
  L3  D4.0 through the 1.57 boss top (z 6.43 .. 8.00); D6.5 relief from the bottom face up to the plate underside (z 0 .. 6.43)
  L4  D6.8 tap drill + M8x1.25 thread from the bottom face, 4.32 deep (3.5 pitches; the snap head tip is at z 4.82)
      MACHINING: thread mill or bottoming tap from below (a through tap cannot pass the D6.5 relief above)
  L5  seal: M8x1.25x6 ISO 4026 set screw + thread sealant, tip at z 4.0 (never past 4.32), 2.0 proud of the bottom face
  L6  PCB stand-in holes D3.5 -> D4.0
Grok Bot, 2026-10-16 (from the build123d reference in C:\\projects\\_scratch\\st185_csb3_lockin*_1016).
"""
import adsk.core, adsk.fusion, math, os, json

app = adsk.core.Application.get()
VI = adsk.core.ValueInput
MAIN = r'C:\projects\active\st185-link-ecu-config'
POS = [(13.5, 13.5), (-13.5, -13.5)]
BOSS_D, HOLE_D, PLATE, BOSS_TOP = 10.0, 4.0, 1.57, 8.0
RELIEF_D, TAP_D, THREAD_DEPTH = 6.5, 6.8, 4.32
SCREW_L, SCREW_TIP, SCREW_HEX, SCREW_HEX_DEPTH = 6.0, 4.0, 4.0, 3.5
SCREW_MINOR = 6.6   # in-thread part modelled at the M8 internal minor diameter (6.647), clear of the D6.8 bore
SUP_L, SUP_D, SUP_TOP, SUP_BOT, SUP_SHANK = 10.0, 6.0, 4.83, 3.18, 3.9
PCB_Z = BOSS_TOP + SUP_L
REPORT = {}


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


def set_circles(sk, d):
    n = 0
    for c in sk.sketchCurves.sketchCircles:
        if abs(c.radius * 20.0 - d) > 1e-6:
            c.radius = d / 20.0
            n += 1
    return n


def plane_at(comp, z, name):
    p = comp.constructionPlanes.itemByName(name)
    if p is None:
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xYConstructionPlane, VI.createByReal(z / 10.0))
        p = comp.constructionPlanes.add(pi)
        p.name = name
        p.isLightBulbOn = False
    return p


def circles_sketch(comp, plane, name, d, z):
    sk = comp.sketches.itemByName(name)
    if sk is None:
        sk = comp.sketches.add(plane)
        sk.name = name
        for (x, y) in POS:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x, y, z)), d / 20.0)
    return sk


def extrude(comp, name, sk, op, dist, bodies=None, prof_filter=None):
    ef = comp.features.extrudeFeatures
    f = ef.itemByName(name)
    if f is not None:
        return f, 'exists'
    profs = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        if prof_filter is None or prof_filter(pr):
            profs.add(pr)
    ei = ef.createInput(profs, op)
    ei.setDistanceExtent(False, VI.createByReal(dist / 10.0))
    if bodies is not None:
        ei.participantBodies = bodies
    f = ef.add(ei)
    f.name = name
    return f, 'added'


def vols(des):
    return {c.name: [round(b.volume * 1000.0, 1) for b in c.bRepBodies] for c in des.allComponents if c.bRepBodies.count}


def export_all(des, prefix, folder, f3d_name):
    em = des.exportManager
    root = des.rootComponent
    files = {}
    for o in root.occurrences:
        o.isLightBulbOn = True
        for b in o.component.bRepBodies:
            b.isLightBulbOn = True
        n = o.component.name.replace(' ', '_').replace('(', '').replace(')', '').replace('=', '')
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


doc = open_doc('ST185-CSB3-Enclosure')
des = adsk.fusion.Design.cast(app.activeProduct)
des.timeline.moveToEnd()
C = {c.name: c for c in des.allComponents}
bc = C['CSB3-Body']
pcb = C['ECUMaster CSB3 (manual v2.1 p.4)']
REPORT['before'] = vols(des)
CUT, JOIN, NEW = (adsk.fusion.FeatureOperations.CutFeatureOperation, adsk.fusion.FeatureOperations.JoinFeatureOperation,
                  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

# L2: bosses D10, old M3 tap + thread filled (suppressed)
REPORT['L2_boss'] = 'D%g (%d circles changed)' % (BOSS_D, set_circles(bc.sketches.itemByName('bosses'), BOSS_D))
for (coll, n) in ((bc.features.threadFeatures, 'Thread2'), (bc.features.holeFeatures, 'M3_csb3_tapped (1)')):
    f = coll.itemByName(n)
    if f is not None and not f.timelineObject.isSuppressed:
        f.timelineObject.isSuppressed = True
REPORT['L2_M3'] = 'suppressed'

# L3 / L4: bores from the bottom face (body xy plane, z 0)
body = bc.bRepBodies.item(0)
z0 = bc.xYConstructionPlane
sk = circles_sketch(bc, z0, 'L3 lock-in D4.0 thru', HOLE_D, 0.0)
REPORT['L3_hole'] = extrude(bc, 'L3 lock-in D4.0 thru boss top', sk, CUT, BOSS_TOP, [body])[1]
sk = circles_sketch(bc, z0, 'L3 relief D6.5', RELIEF_D, 0.0)
REPORT['L3_relief'] = extrude(bc, 'L3 relief D6.5 to plate underside', sk, CUT, BOSS_TOP - PLATE, [body])[1]
sk = circles_sketch(bc, z0, 'L4 M8 tap drill D6.8', TAP_D, 0.0)
f, st = extrude(bc, 'L4 M8 tap drill D6.8 x 4.32 from below', sk, CUT, THREAD_DEPTH, [body])
REPORT['L4_drill'] = st
tf = bc.features.threadFeatures
if tf.itemByName('L4 M8x1.25 from below - thread mill or bottoming tap') is None:
    faces = [fc for fc in f.sideFaces if isinstance(fc.geometry, adsk.core.Cylinder) and abs(fc.geometry.radius * 20.0 - TAP_D) < 1e-3]
    q = tf.threadDataQuery
    ti = adsk.fusion.ThreadInfo.create(False, True, 'ISO Metric profile', 'M8x1.25', '6H', True)
    for fc in faces:
        tin = tf.createInput(fc, ti)
        tin.isModeled = False
        tin.isFullLength = True
        t = tf.add(tin)
        t.name = 'L4 M8x1.25 from below - thread mill or bottoming tap' if tf.itemByName('L4 M8x1.25 from below - thread mill or bottoming tap') is None else 'L4 M8x1.25 from below (2)'
    REPORT['L4_thread'] = '%d faces' % len(faces)
else:
    REPORT['L4_thread'] = 'exists'

# L6: PCB stand-in holes D4.0
REPORT['L6_pcb'] = '%d circles changed' % set_circles(pcb.sketches.itemByName('csb3_pcb'), HOLE_D)

# L1: the standoff component becomes the 8847 lock-in supports (body D6.0 z 8 .. 18, snap heads as D3.9 envelopes)
so = C.get('Standoffs Keystone 25510 x2') or C.get('Lock-in supports Cat 8847 L10 x2')
so.name = 'Lock-in supports Cat 8847 L10 x2'
for n in ('Sketch1', 'Sketch2'):
    set_circles(so.sketches.itemByName(n), SUP_D)
pl = so.constructionPlanes.itemByName('Plane1')
skb = circles_sketch(so, pl, 'L1 chassis snap head', SUP_SHANK, BOSS_TOP)
REPORT['L1_bot'] = extrude(so, 'L1 chassis snap head 3.18', skb, JOIN, -SUP_BOT, [so.bRepBodies.item(i) for i in range(so.bRepBodies.count)])[1]
plt = plane_at(so, PCB_Z, 'L1 board plane z18')
skt = circles_sketch(so, plt, 'L1 board snap head', SUP_SHANK, PCB_Z)
REPORT['L1_top'] = extrude(so, 'L1 board snap head 4.83', skt, JOIN, SUP_TOP, [so.bRepBodies.item(i) for i in range(so.bRepBodies.count)])[1]

# L5: the M8x6 ISO 4026 set screws (own component, modelled at the minor diameter inside the thread)
scn = 'Set screws M8x1.25x6 ISO 4026 x2'
sc = C.get(scn)
if sc is None:
    occ = des.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    sc = occ.component
    sc.name = scn
    p0 = plane_at(sc, SCREW_TIP - SCREW_L, 'screw end z-2')
    s1 = circles_sketch(sc, p0, 'screw proud D8', 8.0, SCREW_TIP - SCREW_L)
    extrude(sc, 'screw proud 2.0', s1, NEW, SCREW_L - SCREW_TIP)
    s2 = circles_sketch(sc, sc.xYConstructionPlane, 'screw in thread minor dia', SCREW_MINOR, 0.0)
    extrude(sc, 'screw in thread 4.0', s2, NEW, SCREW_TIP)
    bodies = [sc.bRepBodies.item(i) for i in range(sc.bRepBodies.count)]
    cf = sc.features.combineFeatures
    for (x, y) in POS:
        bs = [b for b in sc.bRepBodies if abs((b.boundingBox.minPoint.x + b.boundingBox.maxPoint.x) * 5.0 - x) < 0.5]
        if len(bs) == 2:
            tc = adsk.core.ObjectCollection.create(); tc.add(bs[1])
            cf.add(cf.createInput(bs[0], tc))
    s3 = sc.sketches.add(p0); s3.name = 'screw hex socket 4'
    for (x, y) in POS:
        c = s3.modelToSketchSpace(P(x, y, SCREW_TIP - SCREW_L))
        r = SCREW_HEX / math.sqrt(3) / 10.0
        pts = [adsk.core.Point3D.create(c.x + r * math.cos(k * math.pi / 3), c.y + r * math.sin(k * math.pi / 3), 0) for k in range(7)]
        for k in range(6):
            s3.sketchCurves.sketchLines.addByTwoPoints(pts[k], pts[k + 1])
    hexes = lambda pr: pr.areaProperties().area * 100.0 < 20.0
    extrude(sc, 'screw hex socket 3.5', s3, CUT, SCREW_HEX_DEPTH, [sc.bRepBodies.item(i) for i in range(sc.bRepBodies.count)], hexes)
    REPORT['L5_screws'] = 'added'
else:
    REPORT['L5_screws'] = 'exists'
for s_ in sc.sketches:
    if s_.name.startswith('screw in thread'):
        set_circles(s_, SCREW_MINOR); s_.name = 'screw in thread minor dia'

REPORT['after'] = vols(des)
REPORT['health'] = [(it.name, it.healthState) for it in des.timeline if not it.isSuppressed and it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]

# checks: interference between the parts that touch (exact B-rep intersection volume, mm3)
occ = {o.component.name: o for o in des.rootComponent.occurrences}
def bodies_of(n):
    return [occ[n].bRepBodies.item(i) for i in range(occ[n].bRepBodies.count)]
tbm = adsk.fusion.TemporaryBRepManager.get()
def iv(a, b):
    try:
        x = tbm.copy(a); tbm.booleanOperation(x, tbm.copy(b), adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return round(x.volume * 1000.0, 4)
    except Exception:
        return 0.0
B = bodies_of('CSB3-Body')[0]
S = bodies_of('Lock-in supports Cat 8847 L10 x2'); K = bodies_of(scn); PB = bodies_of('ECUMaster CSB3 (manual v2.1 p.4)')
REPORT['interference'] = dict(body_support=sum(iv(B, s) for s in S), body_screw=sum(iv(B, k) for k in K),
                              support_screw=sum(iv(s, k) for s in S for k in K), pcb_support=sum(iv(PB[0], s) for s in S),
                              parts_support=sum(iv(PB[1], s) for s in S))
mm_ = lambda a, b: round(app.measureManager.measureMinimumDistance(a, b).value * 10.0, 2)
REPORT['screw_tip_to_snap_head'] = min(mm_(s, k) for s in S for k in K)
REPORT['board_z'] = round(PB[0].boundingBox.minPoint.z * 10.0, 2)
if globals().get('SAVE', True) and not REPORT['health'] and not any(REPORT['interference'].values()):
    REPORT['files'] = export_all(des, 'CSB3', os.path.join(MAIN, 'cad', 'enclosures', 'csb3'), 'ST185-CSB3-Enclosure.f3d')
    doc.save('Dan 2026-10-16 (R133): Cat. 8847 L10 lock-in supports, D10 bosses with D4.0 thru 1.57 top, D6.5 relief + M8x1.25 x 4.32 '
             'from below sealed by M8x6 ISO 4026 set screws, PCB holes D4.0 (Grok Bot 2026-10-16)')
    REPORT['saved'] = True
print(json.dumps(REPORT, indent=1))