"""Close-up of the VRC board holder v2 (DECISIONS R126) in its box: section on the plane through one M6 screw axis - the countersunk
M6 x 12 (ISO 10642, RS PRO 266-8419, simplified model), the holder's clamp material and boss recess, the enclosure boss with its
D5.0 M6x1.0 tap drill, the board flush in its pocket and one snap tab. Run inside Fusion (Fusion MCP script runner) after
build_vrc_holder.py: copies the bodies from ST185-VRC-Enclosure into a scratch design that is never saved (closed without saving),
writes the raw PNG; the caller frames it (finish(raw, out)).
Claude Code, 2026-10-16.
"""
import adsk.core, adsk.fusion, os, sys, json

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config\cad\enclosures\src'
if SRC not in sys.path:
    sys.path.insert(0, SRC)
import vrc_holder_spec as S

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
BT = adsk.fusion.BooleanTypes


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def box(x0, y0, z0, x1, y1, z1):
    return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), adsk.core.Vector3D.create(1, 0, 0),
                        adsk.core.Vector3D.create(0, 1, 0), abs(x1 - x0) / 10.0, abs(y1 - y0) / 10.0, abs(z1 - z0) / 10.0))


def render(raw_png, screw=0):
    src = [d for d in app.documents if d.name.startswith('ST185-VRC-Enclosure')]
    if not src:
        raise RuntimeError('open ST185-VRC-Enclosure first')
    sd = adsk.fusion.Design.cast(src[0].products.itemByProductType('DesignProductType'))
    bodies = {}
    for o in sd.rootComponent.occurrences:
        for b in o.component.bRepBodies:
            bodies[b.name] = b
    sx, sy = S.SCREWS[screw]
    back = app.activeDocument
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)      # scratch, never saved
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = des.rootComponent
        alib = app.materialLibraries.itemByName('Fusion Appearance Library')

        def tint(base, name, rgb):
            a = des.appearances.addByCopy(alib.appearances.itemByName(base), name)
            for i in range(a.appearanceProperties.count):
                p_ = a.appearanceProperties.item(i)
                if isinstance(p_, adsk.core.ColorProperty) and p_.name in ('Color', 'Colour'):
                    p_.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    break
            return a
        AP = dict(al=alib.appearances.itemByName('Aluminum - Satin'), pa=tint('Plastic - Matte (Gray)', 'PA12 holder', (165, 168, 172)),
                  pcb=tint('Plastic - Glossy (Green)', 'PCB green', (20, 110, 50)), ic=tint('Plastic - Matte (Black)', 'IC', (30, 30, 32)),
                  steel=alib.appearances.itemByName('Steel - Satin'))
        keep = box(sx - 18, sy - 40, -1, sx + 12, sy, 26)          # the half on the -y side of the screw axis plane, around the screw
        # simplified ISO 10642 M6 x 12: 90 deg head D12 -> D6 (k 3.0), shank D6 to 12 from the head top; head flush with the block top
        zt = S.Z_TOP
        scr = tb.createCylinderOrCone(P(sx, sy, zt), 6.0 / 10.0, P(sx, sy, zt - 3.0), 3.0 / 10.0)
        tb.booleanOperation(scr, tb.createCylinderOrCone(P(sx, sy, zt - 2.99), 0.3, P(sx, sy, zt - S.SCREW_LEN), 0.3), BT.UnionBooleanType)
        tb.booleanOperation(scr, tb.createCylinderOrCone(P(sx, sy, zt + 0.01), 0.17, P(sx, sy, zt - 2.5), 0.17), BT.DifferenceBooleanType)  # hex socket (round)
        items = [('VRC-Body', AP['al']), ('VRC board holder', AP['pa']), ('VR module PCB', AP['pcb']), ('NCV1124 SO-8 envelope', AP['ic'])]
        for (n, ap) in items + [('screw', AP['steel'])]:
            b = scr if n == 'screw' else tb.copy(bodies[n])
            if not tb.booleanOperation(b, tb.copy(keep), BT.IntersectionBooleanType) or b.volume < 1e-9:
                continue
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            occ.component.name = n
            bb = occ.component.bRepBodies.add(b)
            bb.appearance = ap
        vp = app.activeViewport
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
        tgt = (sx - 4.0, sy, 9.0)
        cam.target = P(*tgt)
        cam.eye = P(tgt[0] + 25, tgt[1] + 150, tgt[2] + 30)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        cam.isFitView = False
        cam.viewExtents = 2.6
        vp.camera = cam
        vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
        vp.refresh()
        adsk.doEvents()
        os.makedirs(os.path.dirname(raw_png), exist_ok=True)
        vp.saveAsImageFile(raw_png, 1600, 1200)
    finally:
        doc.close(False)
        if back is not None:
            back.activate()
    return dict(png=raw_png, screw=[sx, sy])


def finish(raw_png, out_png):
    """Plain Python (not Fusion): display-bounds border, title, notes and key - the fuse box close-up style."""
    from PIL import Image, ImageDraw, ImageFont

    def font(sz, bold=False):
        for f in (('segoeuib.ttf' if bold else 'segoeui.ttf'), ('arialbd.ttf' if bold else 'arial.ttf'), 'DejaVuSans.ttf'):
            try:
                return ImageFont.truetype(f, sz)
            except OSError:
                continue
        return ImageFont.load_default()
    im = Image.open(raw_png).convert('RGB')
    W, H, B, BAR = im.size[0], im.size[1], 10, 132
    page = Image.new('RGB', (W + 2 * B, H + 2 * B + BAR), (246, 246, 242))
    page.paste(im, (B, B + BAR))
    d = ImageDraw.Draw(page)
    d.rectangle([0, 0, page.size[0] - 1, page.size[1] - 1], outline=(40, 44, 52), width=B)
    d.rectangle([B - 1, B + BAR - 1, B + W, B + BAR + H], outline=(20, 24, 30), width=2)
    d.text((B + 18, B + 10), 'VRC board holder v2 in the box - section through one M6 screw (DECISIONS R126, N4 heights R131)', fill=(20, 24, 30), font=font(30, True))
    d.text((B + 18, B + 50), '%s flush in a 90 deg countersink D%.1f; %.1f mm of PA12 clamped over the boss; %.1f mm of thread engaged.' % (
        S.SCREW_PN, S.CSK_D, S.Z_TOP - S.CSK_DEPTH - (S.FLOOR_Z + S.RECESS_H), S.SCREW_LEN - (S.Z_TOP - S.FLOOR_Z - S.BOSS2_H)), fill=(70, 74, 80), font=font(19))
    d.text((B + 18, B + 74), 'Enclosure boss D%.0f x %.1f high, drill D%.1f x %.1f deep - TAP M6x1.0 later (1.0 floor left, sealed).' % (
        S.BOSS2_D, S.BOSS2_H, S.PILOT_D, S.PILOT_DEPTH), fill=(70, 74, 80), font=font(19))
    d.text((B + 18, B + 98), 'Board flush in its pocket (+0.4 a side), held by 4 snap tabs; wires solder on the top. Screw shown simplified.',
           fill=(70, 74, 80), font=font(19))
    keys = [((180, 182, 186), '6061-T6 enclosure body (boss + tap drill)'), ((165, 168, 172), 'PA12 holder block'), ((20, 110, 50), 'VR module PCB'),
            ((150, 150, 150), 'M6 countersunk screw')]
    y = B + BAR + H - 34 * len(keys) - 14
    for col, lab in keys:
        d.rectangle([B + 12, y - 4, B + 44 + 11 * len(lab), y + 26], fill=(250, 250, 248))
        d.rectangle([B + 18, y + 2, B + 36, y + 20], fill=col, outline=(20, 24, 30))
        d.text((B + 44, y), lab, fill=(20, 24, 30), font=font(20))
        y += 34
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    page.save(out_png, optimize=True)
    return out_png


def run(_context: str):
    print(json.dumps(render(os.path.join(os.environ.get('TEMP', r'C:\Temp'), 'vrc_holder_v2_closeup_raw.png'))))
