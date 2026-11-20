"""Section renders of the keyed twist-lock terminal seats (spec.TWIST, Dan 2026-11-16, BACKLOG row 107). Run inside Fusion after
build_fusion.build(OUT, rev=8): copies the built POWER base out of the open ST185_fusebox_rev7 document into a scratch design that is
never saved (closed without saving, R74), cuts the sections there and adds the crimped terminal on its real wire, sized from
spec.twist_env (box, crimped wire barrel, insulation barrel on the RNF-100 build-up, wire) - simple boxes and cylinders at those sizes,
not maker CAD (TE's STEP shows the insulation wings open, uncrimped). One terminal is shown PASSING (turned 90 deg, R, half way through
the slot) and one SEATED (S, box ends on the ledge, in its recess). Writes raw PNGs to OUT/renders/twistlock/raw/.
    render(r'...\\cad\\fusebox\\rev8', relay='R2')
Claude Code, 2026-11-16.
"""
import adsk.core, adsk.fusion, math, os, sys, json

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config\cad\fusebox\src'
if SRC not in sys.path:
    sys.path.insert(0, SRC)
import spec as S

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
BT = adsk.fusion.BooleanTypes
W_IMG, H_IMG = 1600, 1200


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def box(x0, y0, z0, x1, y1, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    o = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), adsk.core.Vector3D.create(1, 0, 0),
                                              adsk.core.Vector3D.create(0, 1, 0), (x1 - x0) / 10.0, (y1 - y0) / 10.0, (z1 - z0) / 10.0)
    return tb.createBox(o)


def cyl(p0, p1, d):
    return tb.createCylinderOrCone(P(*p0), d / 20.0, P(*p1), d / 20.0)


def bo(a, b, op):
    if not tb.booleanOperation(a, b, {'u': BT.UnionBooleanType, 's': BT.DifferenceBooleanType, 'i': BT.IntersectionBooleanType}[op]):
        raise RuntimeError('boolean %s failed' % op)
    return a


def cut_half(body, axis, at, keep_below=True, big=2000.0):
    lo, hi = (at, at + big) if keep_below else (at - big, at)
    b = {'x': (lo, -big, -big, hi, big, big), 'y': (-big, lo, -big, big, hi, big)}[axis]
    try:
        bo(body, box(*b), 's')
    except RuntimeError:
        return None
    return body if body.volume > 1e-9 else None


def render(out_dir, relay='R2', box_name='POWER'):
    S.use_rev(8)
    raw = os.path.join(out_dir, 'renders', 'twistlock', 'raw')
    os.makedirs(raw, exist_ok=True)
    plan = json.load(open(os.path.join(out_dir, 'wiring_plan.json'), encoding='utf-8'))
    cav = {(c['box'], c['cav']): c for c in plan['cavities']}
    src_doc = [d for d in app.documents if d.name.split(' v')[0] == 'ST185_fusebox_rev7']
    if not src_doc:
        raise RuntimeError('open ST185_fusebox_rev7 first')
    src = adsk.fusion.Design.cast(src_doc[0].products.itemByProductType('DesignProductType'))
    base0 = next(o.component.bRepBodies.item(0) for o in src.rootComponent.occurrences
                 if o.component.name == '%s_Base_PA12_printed' % box_name.capitalize())
    base0 = tb.copy(base0)
    tdoc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)      # scratch, never saved
    tdoc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    alib = app.materialLibraries.itemByName('Fusion Appearance Library')

    def tint(base, name, rgb):
        a = design.appearances.itemByName(name)
        if a is None:
            a = design.appearances.addByCopy(alib.appearances.itemByName(base), name)
            for i in range(a.appearanceProperties.count):
                p_ = a.appearanceProperties.item(i)
                if isinstance(p_, adsk.core.ColorProperty) and p_.name in ('Color', 'Colour'):
                    p_.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    break
        return a
    AP = dict(pa12=tint('Plastic - Matte (Gray)', 'PA12 MJF light', (170, 174, 178)), tin=alib.appearances.itemByName('Steel - Satin'),
              cu=alib.appearances.itemByName('Copper - Raw'), wire=tint('Plastic - Glossy (Red)', 'Wire red', (200, 40, 30)),
              sl=tint('Plastic - Matte (Black)', 'RNF-100', (30, 30, 30)))
    vp = app.activeViewport

    def clear():
        for i in range(root.occurrences.count - 1, -1, -1):
            root.occurrences.item(i).deleteMe()

    def add(name, b, ap):
        if b is None:
            return
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        bb = occ.component.bRepBodies.add(b)
        bb.appearance = ap

    def shot(fn, target, eye, extent):
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
        cam.target = P(*target)
        cam.eye = P(target[0] + eye[0], target[1] + eye[1], target[2] + eye[2])
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        cam.isFitView = False
        cam.viewExtents = extent / 10.0
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(raw, fn), W_IMG, H_IMG)

    sx_, sy_ = S.PLACE[box_name]
    zt = (S.LOGIC if box_name == 'LOGIC' else S.POWER)['z_t']
    allc = [dict(d) for d in plan['cavities']]

    def terminal(c, rot, dz):
        """Crimped terminal on its real wire in cavity c: contact end at the seat + dz, turned 90 deg when rot (R). Returns bodies."""
        E = S.twist_env(c['part'], c['wire_od'], c.get('awg'))
        side = S.lance_side(c, allc)
        x, y = c['x'] + sx_, c['y'] + sy_
        zs = zt - S.seat_gap(c['part'], c['kind'], True) + dz
        ax = S.BLADE_AXIS[c['kind']] if not rot else ('y' if S.BLADE_AXIS[c['kind']] == 'x' else 'x')
        yb = E['yb']

        def rb(p, z0, z1, hollow=None):     # part (u half, v lo, v hi) -> world box
            u = p[0]
            h0, h1 = sorted((-side * (p[1] - yb), -side * (p[2] - yb)))
            b = box(x - u, y + h0, z0, x + u, y + h1, z1) if ax == 'x' else box(x + h0, y - u, z0, x + h1, y + u, z1)
            if hollow:
                t = hollow
                bo(b, box(x - u + t, y + h0 + t, z0 - 1, x + u - t, y + h1 - t, z1 + 1) if ax == 'x' else
                   box(x + h0 + t, y - u + t, z0 - 1, x + h1 - t, y + u - t, z1 + 1), 's')
            return b
        Lb = E['Lb']
        R_ = S.REAL[c['part']]
        t = S.TERM[c['part']]['t'] or S.T_EST
        ins = E['ins']
        vc = (ins[1] + ins[2]) / 2 - yb                 # insulation barrel centre off the blade line (model v)
        hc = -side * vc
        cx, cy = (x, y + hc) if ax == 'x' else (x + hc, y)
        cod = S.crimp_od(c['part'], c['wire_od'])
        out = [('Receptacle box', rb(E['box'], zs - Lb, zs, t), AP['tin']),
               ('Wire barrel (crimped)', rb(E['wire'], zs - R_['wz'][1], zs - Lb), AP['tin']),
               ('Insulation barrel (crimped)', cyl((cx, cy, zs - R_['L']), (cx, cy, zs - R_['iz'][0]), ins[2] - ins[1]), AP['tin']),
               ('Conductor', cyl((cx, cy, zs - R_['wz'][1] - 0.3), (cx, cy, zs - Lb + 0.3), R_['d'] * 0.8), AP['cu'])]
        if cod > c['wire_od'] + 1e-6:
            out.append(('RNF-100 build-up', cyl((cx, cy, zs - R_['L'] - 8.0), (cx, cy, zs - R_['iz'][0] + 0.2), cod), AP['sl']))
        out.append(('Wire', cyl((cx, cy, zs - R_['L'] - 25.0), (cx, cy, zs - R_['wz'][1] - 0.5), c['wire_od']), AP['wire']))
        return out

    c85, c86 = cav[(box_name, relay + ' 85')], cav[(box_name, relay + ' 86')]
    for c in (c85, c86):
        c['box'] = box_name
    x85, y85, y86 = c85['x'] + sx_, c85['y'] + sy_, c86['y'] + sy_
    z_seat = zt - S.seat_gap(c85['part'], c85['kind'], True)
    base = tb.copy(base0)
    bo(base, box(x85 - 14, y85 - 10, zt - 30, x85 + 14, y86 + 10, zt + 1), 'i')
    shots = []
    # (1) the plane x = the coil-terminal line, through both coil seats: 85 PASSING (turned 90 deg, half way up the slot), 86 SEATED
    clear()
    sec = ('x', x85, True)
    add('Base (section)', cut_half(tb.copy(base), *sec), AP['pa12'])
    for (n, b, a) in terminal(c85, True, -6.0) + terminal(c86, False, 0.0):
        add(n, cut_half(b, *sec), a)
    shots.append(('twistlock_1_section_85_passing_86_seated.png', ((x85, (y85 + y86) / 2, z_seat - 8), (150, 0, 15), 42.0)))
    shot(shots[-1][0], *shots[-1][1])
    # (2) the plane y = 86 centre: the seated box ends on the ledge either side of the slot, in the recess
    clear()
    sec2 = ('y', y86, True)
    add('Base (section)', cut_half(tb.copy(base), *sec2), AP['pa12'])
    for (n, b, a) in terminal(c86, False, 0.0):
        add(n, cut_half(b, *sec2), a)
    shots.append(('twistlock_2_section_86_seated_on_ledge.png', ((x85, y86, z_seat - 8), (0, 150, 15), 30.0)))
    shot(shots[-1][0], *shots[-1][1])
    # (3) the same plane through 85: the turned box passing up the slot (the slot is only as wide as the crimped barrels)
    clear()
    sec3 = ('y', y85, True)
    add('Base (section)', cut_half(tb.copy(base), *sec3), AP['pa12'])
    for (n, b, a) in terminal(c85, True, -6.0):
        add(n, cut_half(b, *sec3), a)
    shots.append(('twistlock_3_section_85_passing_slot.png', ((x85, y85, z_seat - 8), (0, 150, 15), 30.0)))
    shot(shots[-1][0], *shots[-1][1])
    # (5) as (2) with the relay's coil blade in: TE F7 data sheet V23134 rev 2607 p.3, 6.3 x 0.8, 11 long below the body base (the body
    # base sits on the deck top), so the blade tip shows how far it reaches into the receptacle box (spec.blade_engage)
    clear()
    add('Base (section)', cut_half(tb.copy(base), *sec2), AP['pa12'])
    for (n, b, a) in terminal(c86, False, 0.0):
        add(n, cut_half(b, *sec2), a)
    bl = S.TWIST['blade_len'][c86['kind']]
    x86 = c86['x'] + sx_
    blade = box(x86 - 3.15, y86 - 0.4, zt - bl, x86 + 3.15, y86 + 0.4, zt + 3.0) if S.BLADE_AXIS[c86['kind']] == 'x' else \
        box(x86 - 0.4, y86 - 3.15, zt - bl, x86 + 0.4, y86 + 3.15, zt + 3.0)
    add('Relay coil blade 6.3 x 0.8 (F7)', cut_half(blade, 'y', y86 + 0.01, True), AP['cu'])
    add('Relay body (base on the deck top)', cut_half(box(x86 - 6.0, y86 - 6.0, zt, x86 + 6.0, y86 + 6.0, zt + 4.0), *sec2), AP['sl'])
    shots.append(('twistlock_5_section_86_blade_engaged.png', ((x85, y86, z_seat - 4), (0, 150, 15), 30.0)))
    shot(shots[-1][0], *shots[-1][1])
    # (4) from below, no section: the slot (R) and the recess (S) cross, the seated 86 box resting across its slot
    clear()
    add('Base', tb.copy(base), AP['pa12'])
    for (n, b, a) in terminal(c86, False, 0.0):
        add(n, b, a)
    shots.append(('twistlock_4_from_below.png', ((x85, (y85 + y86) / 2, z_seat - 12), (20, 25, -150), 40.0)))
    shot(shots[-1][0], *shots[-1][1])
    tdoc.close(False)
    src_doc[0].activate()
    info = dict(relay=relay, box=box_name, z_seat=round(z_seat, 2), c85=c85.get('twist'), c86=c86.get('twist'),
                wire_85=c85['wire_od'], wire_86=c86['wire_od'], files=[s_[0] for s_ in shots],
                engage=S.blade_engage(c86['part'], c86['kind'], True), gap=round(S.TWIST['d_r'] + S.TWIST['lift'], 2), d_r=S.TWIST['d_r'])
    json.dump(info, open(os.path.join(raw, 'twistlock_render.json'), 'w'), indent=1)
    return info
