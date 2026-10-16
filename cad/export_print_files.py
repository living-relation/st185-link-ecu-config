"""Standalone print files for the parts Dan prints himself on the HP MJF printer (PA12): STEP + STL + 3MF, mm, one body, placed on the
build plate (lowest face on z = 0, centred on x / y) in its print orientation. Run inside Fusion (Fusion MCP script runner):
    export(PARTS)        # or run() below
Each part is read from the STEP its own build already exported (the model stays in its own Fusion document - ST185_fusebox_rev7,
ST185-VRC-Enclosure - so no editable Fusion file is added, R74): the STEP is imported into a scratch design that is never saved and is
closed without saving at the end. The print files go in a print/ folder next to the model's other CAD files (gitignored, local only).
Check them with cad/check_print_files.py (WSL, trimesh).
Claude Code, 2026-10-15 (Dan: "make sure that the retainer clip exists as its own file that I can 3D print in a mjf printer. also produce
the VRC PCB holder that goes inside the enclosure as a separate file").
"""
import adsk.core, adsk.fusion, os, json

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config'
# name, source STEP (relative to the checkout that holds the CAD files), print folder, rotation about X (deg) for the print orientation
PARTS = [
    ('ST185_R1_retainer_clip_PA12', 'cad/fusebox/rev7/Power_Retainer_R1_PA12_printed.step', 'cad/fusebox/rev7/print', 0.0),
    ('ST185_VRC_board_holder_PA12', 'cad/enclosures/vrc/VRC_part_VRC-Board-Holder.step', 'cad/enclosures/vrc/print', 0.0),
]


def export(parts, root_dir=REPO):
    app = adsk.core.Application.get()
    back = app.activeDocument
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)       # scratch, never saved
    out = []
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent
        im, em, tb = app.importManager, design.exportManager, adsk.fusion.TemporaryBRepManager.get()
        for (name, src, dst, rot_x) in parts:
            src_p, dst_d = os.path.join(root_dir, src), os.path.join(root_dir, dst)
            os.makedirs(dst_d, exist_ok=True)
            n0 = root.occurrences.count
            im.importToTarget(im.createSTEPImportOptions(src_p), root)
            bodies = []
            for i in range(n0, root.occurrences.count):
                c = root.occurrences.item(i).component
                bodies += [c.bRepBodies.item(k) for k in range(c.bRepBodies.count)]
                for oc in c.allOccurrences:
                    bodies += [oc.component.bRepBodies.item(k) for k in range(oc.component.bRepBodies.count)]
            if len(bodies) != 1:
                raise RuntimeError('%s: %d bodies in %s - a print file must be one body' % (name, len(bodies), src))
            b = tb.copy(bodies[0])
            if rot_x:
                m = adsk.core.Matrix3D.create()
                m.setToRotation(rot_x * 3.141592653589793 / 180.0, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
                tb.transform(b, m)
            bb = b.boundingBox
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(-(bb.minPoint.x + bb.maxPoint.x) / 2, -(bb.minPoint.y + bb.maxPoint.y) / 2, -bb.minPoint.z)
            tb.transform(b, m)
            for i in range(root.occurrences.count - 1, n0 - 1, -1):
                root.occurrences.item(i).deleteMe()
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            occ.component.name = name
            body = occ.component.bRepBodies.add(b)
            body.name = name
            files = {}
            p = os.path.join(dst_d, name + '.step')
            em.execute(em.createSTEPExportOptions(p, occ.component)); files['step'] = p
            p = os.path.join(dst_d, name + '.stl')
            so = em.createSTLExportOptions(body, p)
            so.isBinaryFormat = True
            so.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(so); files['stl'] = p
            p = os.path.join(dst_d, name + '.3mf')
            co = em.createC3MFExportOptions(body, p)
            co.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(co); files['3mf'] = p
            bb = body.boundingBox
            out.append(dict(name=name, source=src, lumps=body.lumps.count, shells=sum(l.shells.count for l in body.lumps),
                            volume_cm3=round(body.volume, 3), size_mm=[round((bb.maxPoint.x - bb.minPoint.x) * 10, 2),
                            round((bb.maxPoint.y - bb.minPoint.y) * 10, 2), round((bb.maxPoint.z - bb.minPoint.z) * 10, 2)], files=files))
            occ.deleteMe()
    finally:
        doc.close(False)        # discard the scratch design
        if back is not None:
            back.activate()
    return out


def run(_context: str):
    print(json.dumps(export(PARTS), indent=1))
