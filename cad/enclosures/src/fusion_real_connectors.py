"""Fusion side of the real-connector swap (DECISIONS R184): the CSB3 and VRC enclosure documents get the makers' connector models in
place of the placeholder bodies. `real_connectors.py place` writes the placed STEPs first (box frame, nothing to move here).

  ST185-CSB3-Enclosure: the 'HD34-24-33PE (envelope ...)' component (or an earlier import) is deleted; CSB3_part_HD34-24-33PE.step (TE model) is
      imported in its place. CSB3-Lid: TE's HD34 model keeps its pilot round (D42.86) for the first 0.12 above the flange, where
      TE's panel cutout (114-151014: D43.08, flat 41.45) has the flat, so the lid gets a D43.08 x 0.20 round relief at the
      flange seat face (z 58.0 -> 58.2); the flat starts 0.20 up. Lid model change (ST185-CSB3-102).
  ST185-VRC-Enclosure: the 'LP16-IN' / 'LP16-OUT' placeholder components are deleted; VRC_part_LP16-IN / -OUT
      _LP-16-C05SX-02-101.step (CNLINKO model, jam nut on the wall's inner face) are imported. Body, lid, holder unchanged.
Then the assembly STEP (and the changed part STEP) and the .f3d are exported to the main checkout (R67), the document is saved and
closed (R74). Idempotent: a second run replaces the imported connectors again and finds the relief already there.
Run inside Fusion (add-in execute_python, or Fusion MCP):
    JOBS = ['csb3', 'vrc']; exec(open(r'<repo>/cad/enclosures/src/fusion_real_connectors.py').read())
Claude Code, 2026-10-19.
"""
import adsk.core, adsk.fusion, os, json

app = adsk.core.Application.get()
MAIN = r'C:\projects\active\st185-link-ecu-config'
ENC = os.path.join(MAIN, 'cad', 'enclosures')
RELIEF_D, RELIEF_H, SEAT_Z = 43.08, 0.20, 58.0      # mm
REPORT = {}


def open_doc(name):
    for d in app.documents:
        if d.name.split(' v')[0] == name:
            d.activate()
            return d
    proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
    f = [f for f in proj.rootFolder.dataFiles if f.name == name][0]
    return app.documents.open(f, True)


def swap(root, old_prefixes, step_files, names):
    """replace the connector occurrences (the placeholders or an earlier import) with the placed maker STEPs."""
    rep = {'deleted': [], 'imported': []}
    for o in list(root.occurrences):
        if o.component.name.startswith(old_prefixes):
            rep['deleted'].append(o.component.name)
            o.deleteMe()
    for path, nm in zip(step_files, names):
        before = {o.entityToken for o in root.occurrences}
        opts = app.importManager.createSTEPImportOptions(path)
        app.importManager.importToTarget(opts, root)
        new = [o for o in root.occurrences if o.entityToken not in before]
        assert len(new) == 1, 'import of %s made %d occurrences' % (path, len(new))
        new[0].component.name = nm
        bb = new[0].boundingBox
        rep['imported'].append({'name': new[0].component.name, 'bodies': [b.name for c in [new[0].component] + [x.component for x in new[0].childOccurrences] for b in c.bRepBodies],
                                'bbox_mm': [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                                                       bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]})
    return rep


def lid_relief(root):
    occ = [o for o in root.occurrences if o.component.name == 'CSB3-Lid'][0]
    assert occ.transform2.isEqualTo(adsk.core.Matrix3D.create()), 'CSB3-Lid occurrence is not at the origin'
    lc = occ.component
    NAME = 'HD34 flat relief D43.08 x 0.2'
    if lc.features.extrudeFeatures.itemByName(NAME):
        return {'relief': 'already there'}
    body = lc.bRepBodies.item(0)
    v0 = body.volume
    pi = lc.constructionPlanes.createInput()
    pi.setByOffset(lc.xYConstructionPlane, adsk.core.ValueInput.createByReal(SEAT_Z / 10))
    pl = lc.constructionPlanes.add(pi)
    pl.name = 'HD34 flange seat z58'
    sk = lc.sketches.add(pl)
    sk.name = 'HD34_flat_relief'
    sk.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), RELIEF_D / 20)
    ei = lc.features.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(RELIEF_H / 10)),
                        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    ei.participantBodies = [body]
    f = lc.features.extrudeFeatures.add(ei)
    f.name = NAME
    return {'relief': NAME, 'healthy': f.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
            'lid_mm3_before': round(v0 * 1000, 2), 'lid_mm3_after': round(body.volume * 1000, 2)}


def export(des, folder, asm_name, parts, f3d):
    em = des.exportManager
    root = des.rootComponent
    for o in root.occurrences:
        o.isLightBulbOn = True
        for b in o.component.bRepBodies:
            b.isLightBulbOn = True
    files = {}

    def step(path, comp):
        em.execute(em.createSTEPExportOptions(path, comp))
        files[os.path.basename(path)] = os.path.getsize(path)
    step(os.path.join(folder, asm_name), root)
    for fn, cname in parts:
        step(os.path.join(folder, fn), [o for o in root.occurrences if o.component.name == cname][0].component)
    em.execute(em.createFusionArchiveExportOptions(os.path.join(folder, f3d), root))
    files[f3d] = os.path.getsize(os.path.join(folder, f3d))
    return files


for job in globals().get('JOBS', ['csb3', 'vrc']):
    if job == 'csb3':
        doc = open_doc('ST185-CSB3-Enclosure')
        des = adsk.fusion.Design.cast(app.activeProduct)
        root = des.rootComponent
        r = swap(root, ('HD34',), [os.path.join(ENC, 'csb3', 'CSB3_part_HD34-24-33PE.step')], ['HD34-24-33PE TE'])
        r.update(lid_relief(root))
        r['files'] = export(des, os.path.join(ENC, 'csb3'), 'CSB3_assembly.step', [('CSB3_part_CSB3-Lid.step', 'CSB3-Lid')],
                            'ST185-CSB3-Enclosure.f3d')
        r['saved'] = doc.save('Real TE HD34-24-33PE model in place of the envelope; lid D43.08 x 0.2 flat relief at the flange seat '
                              '(R184, Claude Code 2026-10-19)')
    else:
        doc = open_doc('ST185-VRC-Enclosure')
        des = adsk.fusion.Design.cast(app.activeProduct)
        root = des.rootComponent
        r = swap(root, ('LP16',), [os.path.join(ENC, 'vrc', 'VRC_part_LP16-%s_LP-16-C05SX-02-101.step' % s) for s in ('IN', 'OUT')],
                 ['LP16-IN CNLINKO LP-16-C05SX-02-101', 'LP16-OUT CNLINKO LP-16-C05SX-02-101'])
        r['files'] = export(des, os.path.join(ENC, 'vrc'), 'VRC_assembly.step', [], 'ST185-VRC-Enclosure.f3d')
        r['saved'] = doc.save('Real CNLINKO LP-16-C05SX-02-101 models (IN + OUT) in place of the envelopes (R184, Claude Code 2026-10-19)')
    r['occurrences'] = [o.component.name for o in root.occurrences]
    doc.close(False)
    REPORT[job] = r
print(json.dumps(REPORT, indent=1))
