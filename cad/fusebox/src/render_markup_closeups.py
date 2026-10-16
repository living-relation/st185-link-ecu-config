"""Before / after close-ups of the six spots Dan marked on the R1 retainer close-ups (2026-10-15 markup, DECISIONS R127: "fix the items
i marked here"). Same view direction as closeup_c2_r1_retainer_exploded.png (POWER base cropped round R1, clip 22 mm down), zoomed on
each spot; printed parts only (no terminals or wires, so nothing hides the walls). Run inside Fusion (Fusion MCP script runner) once on
the old build (tag 'before') and once after the rebuild (tag 'after'): it copies the bodies out of ST185_fusebox_rev7 into a scratch
design that is closed without saving (R74) and writes raw PNGs to rev7/renders/closeups/raw/. finish() (plain Python) pairs them.
    render(r'...\\cad\\fusebox\\rev7', 'before')
Claude Code, 2026-10-15.
"""
import json, os, sys

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config\cad\fusebox\src'
if SRC not in sys.path:
    sys.path.insert(0, SRC)
import spec as S

EYE = (-110.0, -150.0, -95.0)             # closeup_c2 camera direction (from below, -x -y side)
DZ_CLIP = -22.0                           # the clip drawn 22 mm down, as in closeup_c2
# world points on each marked spot's view ray (picked on closeup_c2: 13.0 px / mm round its centre), what Dan circled
SPOTS = [
    ('m1', (202.6, 35.3, 32.1), 'Small square stub beside a terminal collar'),
    ('m2', (215.0, 41.9, 7.3), 'Clip: curved sliver and hooked tab where the saddle notch met the R1 30 wire hole'),
    ('m3', (164.0, 58.7, 39.8), 'Thin standing wall strip at a cavity edge'),
    ('m4', (211.6, 33.3, 24.7), 'Thin curved sliver beside the R1 30 terminal (bend saddle shaved by the cavity)'),
    ('m5', (190.2, 45.1, 30.9), 'Thin webs and ledges between the cavity towers'),
    ('m6', (184.3, 55.3, 21.6), 'Bend saddle: cable groove between two 1.5 mm lips, and a thin rib on the wall'),
]
EXTENT = 15.0
W_IMG, H_IMG = 1200, 1200


def render(out_dir, tag):
    import adsk.core, adsk.fusion
    app = adsk.core.Application.get()
    tb = adsk.fusion.TemporaryBRepManager.get()
    BT = adsk.fusion.BooleanTypes

    def P(x, y, z):
        return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)

    def box(x0, y0, z0, x1, y1, z1):
        return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), adsk.core.Vector3D.create(1, 0, 0),
                            adsk.core.Vector3D.create(0, 1, 0), abs(x1 - x0) / 10.0, abs(y1 - y0) / 10.0, abs(z1 - z0) / 10.0))
    raw = os.path.join(out_dir, 'renders', 'closeups', 'raw')
    os.makedirs(raw, exist_ok=True)
    src_doc = [d for d in app.documents if d.name.split(' v')[0] == 'ST185_fusebox_rev7']
    if not src_doc:
        raise RuntimeError('open ST185_fusebox_rev7 first')
    src = adsk.fusion.Design.cast(src_doc[0].products.itemByProductType('DesignProductType'))
    bodies = {o.component.name: o.component.bRepBodies.item(0) for o in src.rootComponent.occurrences if o.component.bRepBodies.count}
    rr = json.load(open(os.path.join(out_dir, 'fusebox_report.json'), encoding='utf-8'))['retainers']['POWER'][0]
    p_ = rr['plate']
    sx_, sy_ = S.PLACE['POWER']
    cx_, cy_ = (p_[0] + p_[3]) / 2 + sx_, (p_[1] + p_[4]) / 2 + sy_
    z_d = S.POWER['z_d']
    back = app.activeDocument
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)      # scratch, never saved
    out = []
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = des.rootComponent
        alib = app.materialLibraries.itemByName('Fusion Appearance Library')

        def tint(base, name, rgb):
            a = des.appearances.addByCopy(alib.appearances.itemByName(base), name)
            for i in range(a.appearanceProperties.count):
                q = a.appearanceProperties.item(i)
                if isinstance(q, adsk.core.ColorProperty) and q.name in ('Color', 'Colour'):
                    q.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    break
            return a
        base = tb.copy(bodies['Power_Base_PA12_printed'])
        tb.booleanOperation(base, box(cx_ - 34, cy_ - 30, z_d - 8 - 20, cx_ + 34, cy_ + 30, S.POWER['z_t'] + 1), BT.IntersectionBooleanType)
        clip = tb.copy(bodies['Power_Retainer_R1_PA12_printed'])
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, 0, DZ_CLIP / 10.0)
        tb.transform(clip, m)
        for (n, b, ap) in (('Power base', base, tint('Plastic - Matte (Gray)', 'PA12 MJF light', (170, 174, 178))),
                           ('R1 retainer clip', clip, tint('Plastic - Matte (Gray)', 'PA12 clip blue', (70, 120, 200)))):
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            occ.component.name = n
            occ.component.bRepBodies.add(b).appearance = ap
        vp = app.activeViewport
        vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
        for (k, tgt, _t) in SPOTS:
            cam = vp.camera
            cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
            cam.target = P(*tgt)
            cam.eye = P(tgt[0] + EYE[0], tgt[1] + EYE[1], tgt[2] + EYE[2])
            cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
            cam.isFitView = False
            cam.viewExtents = EXTENT / 10.0
            vp.camera = cam
            vp.refresh()
            adsk.doEvents()
            fn = os.path.join(raw, 'markup_%s_%s.png' % (k, tag))
            vp.saveAsImageFile(fn, W_IMG, H_IMG)
            out.append(fn)
    finally:
        doc.close(False)
        if back is not None:
            back.activate()
    return out


def finish(out_dir, notes=None):
    """Plain Python: one framed before | after image per spot, rev7/renders/closeups/markup_<id>_before_after.png. notes = {id: after text}."""
    from PIL import Image, ImageDraw, ImageFont

    def font(sz, bold=False):
        for f in (('segoeuib.ttf' if bold else 'segoeui.ttf'), ('arialbd.ttf' if bold else 'arial.ttf'), 'DejaVuSans.ttf'):
            try:
                return ImageFont.truetype(f, sz)
            except OSError:
                continue
        return ImageFont.load_default()
    d = os.path.join(out_dir, 'renders', 'closeups')
    res = []
    for (k, _tgt, title) in SPOTS:
        a = Image.open(os.path.join(d, 'raw', 'markup_%s_before.png' % k)).convert('RGB')
        b = Image.open(os.path.join(d, 'raw', 'markup_%s_after.png' % k)).convert('RGB')
        B, BAR, G = 10, 110, 16
        W = a.size[0] + b.size[0] + G
        page = Image.new('RGB', (W + 2 * B, a.size[1] + 2 * B + BAR + 44), (246, 246, 242))
        page.paste(a, (B, B + BAR + 44))
        page.paste(b, (B + a.size[0] + G, B + BAR + 44))
        dr = ImageDraw.Draw(page)
        dr.rectangle([0, 0, page.size[0] - 1, page.size[1] - 1], outline=(40, 44, 52), width=B)
        dr.text((B + 18, B + 10), 'Markup %s: %s' % (k.upper(), title), fill=(20, 24, 30), font=font(28, True))
        dr.text((B + 18, B + 52), (notes or {}).get(k, ''), fill=(70, 74, 80), font=font(19))
        dr.text((B + 18, B + 80), 'POWER base round R1 from below (closeup_c2 view), clip 22 mm down. DECISIONS R127.', fill=(110, 114, 120), font=font(16))
        for (x0, lab, col) in ((B, 'BEFORE (#266)', (190, 60, 50)), (B + a.size[0] + G, 'AFTER (R127)', (40, 140, 70))):
            dr.text((x0 + 14, B + BAR + 6), lab, fill=col, font=font(26, True))
        fn = os.path.join(d, 'markup_%s_before_after.png' % k)
        page.save(fn, optimize=True)
        res.append(fn)
    return res


def run(_context: str):
    print(json.dumps(render(os.path.join(os.path.dirname(SRC), 'rev7'), os.environ.get('MARKUP_TAG', 'before'))))
