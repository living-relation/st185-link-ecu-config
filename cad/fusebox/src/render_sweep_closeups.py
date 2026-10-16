"""Before / after close-ups of the biggest groups of the R127 wall sweep (DECISIONS R128, Dan 2026-10-16: "fix the ones you found as long
as they don't alter the function and installability of the parts"), and the two "base from below" views of the summary page.
Run inside Fusion (Fusion MCP script runner): render(step_dir, tag) imports the printed parts' STEP files from step_dir (the old build's
cad/fusebox/rev7 for 'before', the new one for 'after') into a scratch design that is closed without saving (R74) and writes raw PNGs to
rev7/renders/closeups/raw/. finish() (plain Python) pairs them into rev7/renders/closeups/sweep_<id>.png and frames the base views.
    render(r'C:\\projects\\active\\st185-link-ecu-config\\cad\\fusebox\\rev7', 'before')
Claude Code, 2026-10-16.
"""
import os, json

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config\cad\fusebox\src'
OUT = os.path.join(os.path.dirname(SRC), 'rev7')
# id, part, world target (mm), view direction (from the target toward the eye), extent (mm), title, after-note
VIEWS = [
    ('logic_under', 'Logic_Base_PA12_printed', (42.0, 80.0, 36.0), (-0.45, -0.75, -1.0), 120.0,
     'LOGIC base from below: towers, collars and guide walls',
     'One solid block under the deck, as the POWER box (R127); cavities and slots are the only cuts. 229 -> 324 cm3.'),
    ('logic_cavities', 'Logic_Base_PA12_printed', (45.0, 50.0, 36.0), (-0.35, -0.6, -1.0), 42.0,
     'LOGIC fuse and micro relay cavities from below: slivers between the cavities',
     'Blade slots only above the seat; strips under 2.0 between openings cut; overlapping slanted guide walls left out; no 87a slot on NO relays.'),
    ('legs', 'Power_Base_PA12_printed', (190.0, -8.0, 16.0), (-0.7, -1.0, -0.65), 55.0,
     'Mounting leg (all 8): hollow buttress, knife edge where the socket cut its sloped wall',
     'Solid buttress - outside, foot, M6 hole and socket unchanged.'),
    ('battrelay', 'BattRelay_Base_PA12_printed', (62.0, -130.0, 8.0), (-0.5, -1.0, 0.95), 120.0,
     'Battery relay block base: ribbed relay platform and fuse pedestal (2.5 ribs), 3.0 rim',
     'Solid platform and pedestal (same outline and heights), rim 4.0 inward. 125 -> 170 cm3.'),
]
# R127 amendment (Dan 2026-10-16): the curved bend saddles back, and the outer walls grown outward
AMEND = [
    ('saddle', 'Power_Base_PA12_printed', (197.0, 97.0, 22.0), (-0.75, -1.0, -0.55), 42.0,
     'Bend saddle (R4 feed): #268 cut the curve flat at the 30 cavity wall',
     'Curve and lips back as before #268, carried by the block above; only near the top a radial cut clears the cavity mouth by 2.0 (no sliver).'),
    ('outer_wall', 'Power_Base_PA12_printed', (163.5, 61.0, 34.0), (-1.0, -0.45, -0.7), 36.0,
     'Outer wall beside a relay cavity (your markup): 3.0 skirt standing alone where the pan groove runs behind it',
     'Skirt grown OUTWARD to 4.3 (3.0 left behind the deepest catch pocket); inside, the cavities, groove and pan fit are unchanged.'),
]
BASES = [   # after only: the summary page's "base from below" figures
    ('fusebox_logic_base_holes.png', 'Logic_Base_PA12_printed', (42.0, 90.0, 30.0), (-0.45, -0.75, -1.0), 230.0,
     'LOGIC base from below (R128): one solid block under the deck - the R120 cavities, joined slots, guide walls, J4 channel floor'),
    ('fusebox_power_base_holes.png', 'Power_Base_PA12_printed', (250.0, 120.0, 25.0), (-0.45, -0.75, -1.0), 330.0,
     'POWER base from below (R127 / R128): one solid block under the deck - cavities, hex pockets, bend saddles, guide walls'),
]
W_IMG, H_IMG = 1300, 1100


def render(step_dir, tag, out_dir=OUT, bases=False, views=None):
    import adsk.core, adsk.fusion
    app = adsk.core.Application.get()
    raw = os.path.join(out_dir, 'renders', 'closeups', 'raw')
    os.makedirs(raw, exist_ok=True)
    back = app.activeDocument
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)      # scratch, never saved
    out = []
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = des.rootComponent
        im = app.importManager
        alib = app.materialLibraries.itemByName('Fusion Appearance Library')
        ap = des.appearances.addByCopy(alib.appearances.itemByName('Plastic - Matte (Gray)'), 'PA12 MJF light')
        for i in range(ap.appearanceProperties.count):
            q = ap.appearanceProperties.item(i)
            if isinstance(q, adsk.core.ColorProperty) and q.name in ('Color', 'Colour'):
                q.value = adsk.core.Color.create(170, 174, 178, 255)
                break
        occ_of = {}
        jobs = BASES if bases else (views or VIEWS)
        for part in sorted(set(v[1] for v in jobs)):
            n0 = root.occurrences.count
            im.importToTarget(im.createSTEPImportOptions(os.path.join(step_dir, part + '.step')), root)
            occ_of[part] = [root.occurrences.item(i) for i in range(n0, root.occurrences.count)]
            for o in occ_of[part]:
                for b in o.component.bRepBodies:
                    b.appearance = ap
        vp = app.activeViewport
        vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
        for (k, part, tgt, d, ext) in [v[:5] for v in jobs]:
            for p_, occs in occ_of.items():
                for o in occs:
                    o.isLightBulbOn = (p_ == part)
            cam = vp.camera
            cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
            cam.target = adsk.core.Point3D.create(tgt[0] / 10.0, tgt[1] / 10.0, tgt[2] / 10.0)
            cam.eye = adsk.core.Point3D.create((tgt[0] + 400 * d[0]) / 10.0, (tgt[1] + 400 * d[1]) / 10.0, (tgt[2] + 400 * d[2]) / 10.0)
            cam.upVector = adsk.core.Vector3D.create(0, 0, 1 if d[2] > 0 else -1)
            cam.isFitView = False
            cam.viewExtents = ext / 10.0
            vp.camera = cam
            vp.refresh()
            adsk.doEvents()
            fn = os.path.join(raw, ('sweep_%s_%s.png' % (k, tag)) if not bases else k)
            vp.saveAsImageFile(fn, W_IMG, H_IMG)
            out.append(fn)
    finally:
        doc.close(False)
        if back is not None:
            back.activate()
    return out


def finish(out_dir=OUT, views=None, bases=True):
    """Plain Python: framed before | after pairs (renders/closeups/sweep_<id>.png) and the two framed base views (rev7/)."""
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
    for (k, _p, _t, _d, _e, title, note) in (views or VIEWS):
        a = Image.open(os.path.join(d, 'raw', 'sweep_%s_before.png' % k)).convert('RGB')
        b = Image.open(os.path.join(d, 'raw', 'sweep_%s_after.png' % k)).convert('RGB')
        B, BAR, G = 10, 110, 16
        W = a.size[0] + b.size[0] + G
        page = Image.new('RGB', (W + 2 * B, a.size[1] + 2 * B + BAR + 44), (246, 246, 242))
        page.paste(a, (B, B + BAR + 44))
        page.paste(b, (B + a.size[0] + G, B + BAR + 44))
        dr = ImageDraw.Draw(page)
        dr.rectangle([0, 0, page.size[0] - 1, page.size[1] - 1], outline=(40, 44, 52), width=B)
        dr.text((B + 18, B + 10), title, fill=(20, 24, 30), font=font(28, True))
        dr.text((B + 18, B + 52), note, fill=(70, 74, 80), font=font(19))
        dr.text((B + 18, B + 80), 'Printed part only. Wall sweep, DECISIONS R128 (R127 applied everywhere).', fill=(110, 114, 120), font=font(16))
        for (x0, lab, col) in ((B, 'BEFORE (#%s)' % ('270' if views else '268'), (190, 60, 50)), (B + a.size[0] + G, 'AFTER (%s)' % ('R127 amendment' if views else 'R128'), (40, 140, 70))):
            dr.text((x0 + 14, B + BAR + 6), lab, fill=col, font=font(26, True))
        fn = os.path.join(d, 'sweep_%s.png' % k)
        page.save(fn, optimize=True)
        res.append(fn)
    for (k, _p, _t, _d, _e, title) in (BASES if bases else ()):
        a = Image.open(os.path.join(d, 'raw', k)).convert('RGB')
        page = Image.new('RGB', (a.size[0], a.size[1] + 48 + 40), (28, 30, 34))
        page.paste(a, (0, 48))
        dr = ImageDraw.Draw(page)
        dr.text((14, 8), title, fill=(255, 255, 255), font=font(24, True))
        dr.text((14, a.size[1] + 56), 'Printed part only, from below. Claude Code, 2026-10-16.', fill=(220, 220, 220), font=font(18))
        fn = os.path.join(out_dir, k)
        page.save(fn, optimize=True)
        res.append(fn)
    return res


def run(_context: str):
    print(json.dumps(render(os.environ.get('SWEEP_STEPS', OUT), os.environ.get('SWEEP_TAG', 'after'))))
