"""Rev 7 extra views (Dan, 2026-10-14: "show me more images of the new fuse boxes ... 2 sides, cable routing, how they'll look
connected together in a typical arrangement"): side views of the 3 boxes (one long side, one short end, real wire colours + ident
bands from the harness drawings) and the typical arrangement (glove box: POWER rev 7 + LOGIC with every cable run on, bend rule,
P-clamps on the 1/0 bends; trunk: the battery relay block and its cables). RENDER ONLY: opens nothing new, adds Tmp_ parts and
recolours cables in the open ST185_fusebox_rev7 document and never saves it (R74) - close it without saving afterwards.
Run inside Fusion with ST185_fusebox_rev7 open (any script runner; Fusion's built-in MCP server works), then
    python cad/fusebox/src/label_views_rev7.py cad/fusebox/rev7
to put the labels on. Wire colours / bands: ST185-CabinPower, -EngineRoom-C, -HeavyDC. CHECK = True also measures every added
cable against every other part (last run: no clash under 1 mm, no bend too tight for its segment). Claude Code, 2026-10-14.
"""
import adsk.core, adsk.fusion, math, os, json, tempfile

RAW = os.path.join(tempfile.gettempdir(), 'st185_rev7_views')    # raw PNGs + labels.json, read by label_views_rev7.py
ONLY = None          # e.g. {'arr_glove_closed.png'} while iterating
CHECK = True
app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
UNION = adsk.fusion.BooleanTypes.UnionBooleanType
SUBTR = adsk.fusion.BooleanTypes.DifferenceBooleanType
INTER = adsk.fusion.BooleanTypes.IntersectionBooleanType


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def V(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def ln(a): return math.sqrt(dot(a, a))
def nrm(a): return mul(a, 1.0 / ln(a))


def cyl(p0, p1, d):
    return tb.createCylinderOrCone(P(*p0), d / 20.0, P(*p1), d / 20.0)


# ------------------------------------------------------------------ cable paths
WARN = []


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def halfspace(C, d):
    """Big box on the +d side of the plane through C."""
    t = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    u = nrm(cross(d, t))
    obb = adsk.core.OrientedBoundingBox3D.create(P(*add(C, mul(d, 1500.0))), V(*d), V(*u), 300.0, 300.0, 300.0)
    return tb.createBox(obb)


def fillet(pts, R, name):
    """Polyline -> pieces: ('line', p0, p1) and ('arc', C, n, a, th), a bend of centre radius R at every corner.
    Returns (pieces, tangent points)."""
    pieces, cur = [], pts[0]
    out, tans, tprev = [pts[0]], [], 0.0
    for i in range(1, len(pts) - 1):
        Pc = pts[i]
        a, b = nrm(sub(Pc, pts[i - 1])), nrm(sub(pts[i + 1], Pc))
        th = math.acos(max(-1.0, min(1.0, dot(a, b))))
        t = R * math.tan(th / 2) if th > 1e-6 else 0.0
        if ln(sub(Pc, pts[i - 1])) + 1e-6 < tprev + t:
            WARN.append('%s: segment %d too short for the bends (%.1f < %.1f)' % (name, i, ln(sub(Pc, pts[i - 1])), tprev + t))
        if th < 1e-6:
            out.append(Pc)
            tprev = 0.0
            continue
        S = sub(Pc, mul(a, t))
        n = nrm(sub(b, mul(a, dot(a, b))))
        C = add(S, mul(n, R))
        pieces.append(('line', cur, S))
        pieces.append(('arc', C, n, a, th))
        cur = add(Pc, mul(b, t))
        k = max(3, int(math.ceil(math.degrees(th) / 7.5)))
        for j in range(k + 1):
            ph = th * j / k
            out.append(add(C, add(mul(n, -R * math.cos(ph)), mul(a, R * math.sin(ph)))))
        tans.append((S, a))
        tans.append((add(Pc, mul(b, t)), b))
        tprev = t
    if ln(sub(pts[-1], pts[-2])) + 1e-6 < tprev:
        WARN.append('%s: last segment too short' % name)
    out.append(pts[-1])
    pieces.append(('line', cur, pts[-1]))
    return pieces, tans


def tube(pieces, od, R):
    """Straight cylinders + torus sectors (one body each)."""
    out = []
    for pc in pieces:
        if pc[0] == 'line':
            if ln(sub(pc[2], pc[1])) > 0.05:
                out.append(cyl(pc[1], pc[2], od))
        else:
            _, C, n, a, th = pc
            # built at the origin, then moved: createTorus ignores its centre when the axis is exactly +-Z
            tor = tb.createTorus(P(0, 0, 0), V(*[c + 0.0 for c in cross(n, a)]), R / 10.0, od / 20.0)
            e = math.radians(0.3)          # cut planes 0.3 deg outside the bend: never on the torus seam, 0.2 mm overlap
            a_ = sub(mul(a, math.cos(e)), mul(n, math.sin(e)))
            b_ = add(mul(n, math.sin(th + e)), mul(a, math.cos(th + e)))
            ok1 = tb.booleanOperation(tor, halfspace((0, 0, 0), a_), INTER)
            ok2 = tb.booleanOperation(tor, halfspace((0, 0, 0), mul(b_, -1.0)), INTER)
            mt = adsk.core.Matrix3D.create()
            mt.translation = V(C[0] / 10.0, C[1] / 10.0, C[2] / 10.0)
            tb.transform(tor, mt)
            if not (ok1 and ok2) or tor.volume < 1e-6:
                WARN.append('bend piece failed (R %.1f, %.0f deg)' % (R, math.degrees(th)))
            out.append(tor)
    return out


def bands_on(p_end, d_in, od, colours, start=4.0):
    """Ident bands on a wire: from p_end going along d_in (unit, into the wire)."""
    out = []
    for k, c in enumerate(colours):
        s0 = start + k * 6.0
        out.append((cyl(add(p_end, mul(d_in, s0)), add(p_end, mul(d_in, s0 + 4.0)), od + 0.9), c))
    return out


def sleeve(p, d, od):
    s = cyl(sub(p, mul(d, 7.0)), add(p, mul(d, 7.0)), od + 6.0)
    tb.booleanOperation(s, cyl(sub(p, mul(d, 8.0)), add(p, mul(d, 8.0)), od - 0.2), SUBTR)
    return s


def run(_context: str):
    os.makedirs(RAW, exist_ok=True)
    doc = [d for d in app.documents if d.isSaved and d.dataFile and d.dataFile.name == 'ST185_fusebox_rev7'][0]
    doc.activate()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    vp = app.activeViewport
    k_img = 1800 / float(vp.width)
    IMG = (1800, int(round(vp.height * k_img)))
    for i in range(root.occurrences.count - 1, -1, -1):
        if root.occurrences.item(i).component.name.startswith('Tmp_'):
            root.occurrences.item(i).deleteMe()
    for o in root.occurrences:
        o.transform2 = adsk.core.Matrix3D.create()

    alib = app.materialLibraries.itemByName('Fusion Appearance Library')

    def col(name, rgb, base='Plastic - Glossy (Red)'):
        a = des.appearances.itemByName(name)
        if a is None:
            a = des.appearances.addByCopy(alib.appearances.itemByName(base), name)
            for i in range(a.appearanceProperties.count):
                p = a.appearanceProperties.item(i)
                if isinstance(p, adsk.core.ColorProperty) and p.name in ('Color', 'Colour'):
                    p.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    break
        return a
    C = {'Red': col('W Red', (200, 22, 22)), 'Black': col('W Black', (28, 28, 30)), 'White': col('W White', (238, 238, 232)),
         'Brown': col('W Brown', (112, 62, 26)), 'Blue': col('W Blue', (30, 85, 205)), 'Yellow': col('W Yellow', (245, 210, 20)),
         'loom': col('W loom grey', (120, 122, 126), 'Plastic - Matte (Gray)'), 'clamp': col('W clamp', (45, 45, 48), 'Plastic - Matte (Gray)'),
         'shelf': col('W shelf', (196, 186, 166), 'Plastic - Matte (Gray)')}

    occ = {o.component.name: o for o in root.occurrences}

    def paint(oname, fn):
        for b in occ[oname].bRepBodies:
            bb = b.boundingBox
            b.appearance = C[fn(bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.x * 10, bb.maxPoint.y * 10, bb.maxPoint.z * 10)]
    OUTC = {43: 'Red', 61: 'Red', 79: 'White', 97: 'Brown', 115: 'White', 133: 'Red', 178: 'Red', 202: 'Red'}

    def pw(x0, y0, z0, x1, y1, z1):
        if x1 > 365:
            return OUTC[min(OUTC, key=lambda k: abs(k - (y0 + y1) / 2))]
        return 'Black' if y1 > 270 else 'Red'
    paint('Power_Wire_feed', pw)
    paint('Power_Harness_wires', lambda *a: 'loom')
    paint('Logic_Harness_wires', lambda *a: 'loom')
    paint('Logic_Wire_feed', lambda *a: 'Red')
    paint('BattRelay_Wire_feed', lambda x0, y0, z0, x1, y1, z1: 'White' if y1 < -158 else 'Red')

    def tmp(name, items, opacity=None):
        """items = [(TemporaryBRep body, colour key)] -> one Tmp_ component."""
        if not items:
            return None
        o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        o.component.name = 'Tmp_' + name
        for b, c in items:
            bb = o.component.bRepBodies.add(b)
            bb.appearance = C[c]
            if opacity is not None:
                bb.opacity = opacity
        occ[o.component.name] = o
        return o

    # ---- ident bands on the box stubs (R87: the circuit's bands at every end)
    band_items = []
    PXE = 370.5            # POWER OUT / POS stub ends (30 past the outboard edge)
    OUTB = {43: ('BUS1', 5.13, ['White', 'Blue', 'White']), 61: ('RTR', 3.61, ['Yellow'] * 3), 79: ('AM1', 5.13, ['Yellow', 'Yellow', 'White']),
            97: ('AM2', 3.61, ['Yellow', 'White', 'Blue']), 115: ('JB1', 6.43, []), 133: ('EPS', 5.13, ['Blue'] * 3)}
    OUTZ = {43: 13.0, 61: 13.0, 79: 13.0, 97: 13.0, 115: 13.75, 133: 13.0}
    for y, (nm, od, bc) in OUTB.items():
        band_items += bands_on((PXE, y, OUTZ[y]), (-1, 0, 0), od, bc)
    tmp('Bands_P', band_items)
    tmp('Bands_L', bands_on((15.65, -30.0, 22.0), (0, 1, 0), 5.13, ['White', 'Blue', 'White'])      # LOGIC Bus 1 feed (w_hc_fb)
        + bands_on((32.85, 211.0, 13.0), (0, -1, 0), 3.61, ['Blue', 'Yellow']))                    # LOGIC Bus 2 feed (w77_cp)
    tmp('Bands_B', bands_on((-30.0, -145.1, 42.7), (1, 0, 0), 3.61, ['White', 'White', 'Blue'])    # battery feed (w_fp_feed)
        + bands_on((214.0, -145.1, 43.5), (-1, 0, 0), 3.61, ['White', 'White', 'Blue'])           # pump (w_fp87_h)
        + bands_on((214.0, -165.4, 24.5), (-1, 0, 0), 1.57, ['White', 'White', 'Blue']))          # coil 85 (w_fp85_h)

    LABELS = {}
    VO = adsk.core.ViewOrientations

    def show(pred):
        for o in root.occurrences:
            o.isLightBulbOn = bool(pred(o.component.name))

    def shot(fn, eye_dir, target, ortho=True, ext=1.2, labels=()):
        if ONLY and fn not in ONLY:
            return
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType if ortho else adsk.core.CameraTypes.PerspectiveCameraType
        d = nrm(eye_dir)
        cam.target = P(*target)
        cam.eye = P(*add(target, mul(d, 1500.0)))
        cam.upVector = V(0, 0, 1) if abs(d[2]) < 0.97 else V(0, 1, 0)
        cam.isFitView = True
        vp.camera = cam
        cam = vp.camera
        cam.isFitView = False
        cam.viewExtents = cam.viewExtents * ext
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RAW, fn), IMG[0], IMG[1])
        pts = []
        for (pt, text) in labels:
            p2 = vp.modelToViewSpace(P(*pt))
            pts.append([round(p2.x * k_img, 1), round(p2.y * k_img, 1), text])
        LABELS[fn] = pts

    # ================================================================ side views (stubs only, real colours)
    PW = lambda n: n.startswith('Power_') or n == 'Tmp_Bands_P'
    LG = lambda n: n.startswith('Logic_') or n == 'Tmp_Bands_L'
    BT = lambda n: n.startswith('BattRelay_') or n == 'Tmp_Bands_B'
    tgtP = (250.0, 121.0, 40.0)
    L_POUT = [((PXE, 43, 13), 'BUS1 50 A out: 8 AWG red, bands W-B-W, to LOGIC Bus 1'), ((PXE, 61, 13), 'RTR 30 A: 10 AWG red, Y-Y-Y'),
              ((PXE, 79, 13), 'AM1 40 A: 8 AWG white, Y-Y-W'), ((PXE, 97, 13), 'AM2 30 A: 10 AWG brown, Y-W-B'),
              ((PXE, 115, 13.75), 'JB1 60 A: 6 AWG white'), ((PXE, 133, 13), 'EPS 60 A: 8 AWG red, B-B-B (to k_eps)')]
    L_PPOS = [((PXE, 178, 61.5), 'H1 BAT+ IN: 1/0 red, Klauke 6R8 on M8'), ((PXE, 202, 61.5), 'H3 RADLOK+: 1/0 red, Klauke 6R8 on M8')]
    L_PNEG = [((175, 273, 61.5), 'H2 BAT-: 1/0 black'), ((198, 273, 61.5), 'H6a RADLOK-: 1/0 black'), ((221, 273, 61.5), 'H7 GND ID: 1/0 black'),
              ((244, 273, 61.5), 'H7 GND IG: 1/0 black'), ((263.5, 273, 57.2), 'relay grounds k_htr 87a / k_pwr 85 / k_rev 85: 14 / 18 / 20 AWG black, M8 rings')]
    L_PLOOM = [((130, 35, 7), 'relay + ACPS tails: 12 bundles out the inboard end, under the deck (colours inside: CabinPower)')]
    show(PW)
    shot('power_side_long.png', (1, 0, 0.36), tgtP, labels=L_POUT + L_PPOS + L_PNEG)
    shot('power_side_end.png', (0, -1, 0.36), tgtP, labels=[((PXE, 43, 13), 'AMI OUT row, 6 cables under the skirt (BUS1, RTR, AM1, AM2, JB1, EPS)'),
                                                        ((PXE, 178, 61.5), 'H1 BAT+ IN + H3 RADLOK+: 1/0 red on the + bar')] + L_PLOOM)
    tgtL = (40.0, 90.0, 40.0)
    L_L = [((15.65, -30, 22), 'Bus 1 feed in: 8 AWG red, W-B-W (from POWER BUS1 50 A)'), ((32.85, 211, 13), 'Bus 2 feed in: 10 AWG red, B-Y (from k_efi 87)'),
           ((10.5, -30, 8.4), 'fuse tails, Bus 1 column (10 wires)'), ((38, -30, 8.7), 'fuse tails, Bus 2 column (13 wires)'),
           ((49, -30, 9.9), 'micro relay tails, inboard column (21 wires)'), ((67.5, -30, 8.4), 'micro relay tails, outboard column (10 wires)')]
    show(LG)
    shot('logic_side_long.png', (-1, 0, 0.36), tgtL, labels=L_L)
    shot('logic_side_end.png', (-0.55, -1, 0.3), tgtL, labels=L_L)
    tgtB = (92.0, -129.0, 25.0)
    L_B = [((-30, -145.1, 42.7), 'feed in from the kill switch MAIN 2: 10 AWG red, W-W-B'), ((214, -145.1, 43.5), 'k_fp 87 to the fuel pump: 10 AWG red, W-W-B'),
           ((214, -165.4, 24.5), 'coil plug: 85 white W-W-B / 86 red B, 18 AWG (CAD draws one lead)')]
    show(BT)
    shot('battrelay_side_long.png', (0, -1, 0.36), tgtB, labels=L_B)
    shot('battrelay_side_end.png', (-1, -0.5, 0.3), tgtB, labels=L_B[:1] + L_B[2:])

    # ================================================================ typical arrangement, glove box
    LX = -55.0                                   # LOGIC moved 55 mm inboard: a channel for the POWER box tails (bend room)
    m = adsk.core.Matrix3D.create()
    m.translation = V(LX / 10.0, 0, 0)
    for o in root.occurrences:
        if o.component.name.startswith('Logic_') or o.component.name == 'Tmp_Bands_L':
            o.transform2 = m
    OD10 = 13.6
    R10 = 3 * OD10 + OD10 / 2                    # 1/0: 3 x OD inside, supported (P-clamp each side of every bend)
    Rf = lambda od: 10 * od + od / 2             # free bend: 10 x OD inside (FAA AC 43.13-1B 11-96)
    cables, clamps, arr_bands, labels = [], [], [], []

    def cable(name, pts, od, colour, R, bands=(), label=None, lab_at=-1, clamp=False, at=None, v='FRT'):
        cl, tans = fillet(pts, R, name)
        cables.append((name, tube(cl, od, R), colour, pts[0], pts[-1]))
        if bands:
            arr_bands.extend(bands_on(pts[0], nrm(sub(pts[1], pts[0])), od, list(bands), start=2.0))
        if clamp:
            for (p, d) in tans:
                clamps.append((sleeve(p, d, od), 'clamp'))
        if label:
            labels.append((at or pts[lab_at], label, v))
    # heavy cables out of the bus zone (1/0, supported 3 x OD bends)
    cable('BATpos', [(PXE, 178, 61.5), (420, 178, 61.5), (420, 178, -120), (420, 520, -120)], OD10, 'Red', R10, label='H1 BAT+ (1/0 red): down past the shelf, back along the RH sill to the battery', clamp=True, at=(420, 178, -30), v='RT')
    cable('RADpos', [(PXE, 202, 61.5), (440, 202, 61.5), (440, 202, 170), (440, -110, 170)], OD10, 'Red', R10, label='H3 RADLOK+ (1/0 red): up and forward to the RH firewall', clamp=True, at=(440, 60, 170))
    cable('BATneg', [(175, 273, 61.5), (175, 400, 61.5), (175, 400, -150), (380, 400, -150), (380, 520, -150)], OD10, 'Black', R10,
          label='H2 BAT- (1/0 black): with H1 to the battery', clamp=True, at=(175, 400, -60), v='RT')
    cable('RADneg', [(198, 273, 61.5), (198, 375, 61.5), (500, 375, 61.5), (500, 375, 170), (500, -110, 170)], OD10, 'Black', R10,
          label='H6a RADLOK- (1/0 black): to the RH firewall', clamp=True, at=(500, 150, 170))
    cable('GNDID', [(221, 273, 61.5), (221, 350, 61.5), (221, 350, -100), (-150, 350, -100)], OD10, 'Black', R10,
          label='H7 GND ID (1/0 black): across to the left kick panel', clamp=True, at=(-140, 350, -100))
    cable('GNDIG', [(244, 273, 61.5), (244, 325, 61.5), (244, 325, -70), (395, 325, -70)], OD10, 'Black', R10,
          label='H7 GND IG (1/0 black): to the right kick (ex-R/B4 bolt)', clamp=True, at=(340, 325, -70), v='RT')
    sg = 1.2 * math.sqrt(2.41 ** 2 + 1.85 ** 2 + 1.57 ** 2)
    cable('GNDsmall', [(263.5, 273, 57.2), (263.5, 300, 57.2), (263.5, 300, -40), (-60, 300, -40)], sg, 'Black', Rf(2.41),
          label='relay grounds k_htr 87a / k_pwr 85 / k_rev 85 (black): into the CabinPower loom', at=(120, 300, -40), v='RT')
    # AMI OUT row: out the outboard end, each turns forward (outboard of the one before)
    xt = {43: 426.4, 61: 434.5, 79: 442.5, 97: 450.5, 115: 462.0, 133: 472.0}
    OUTL = {61: 'RTR 30 A (10 AWG red)', 79: 'AM1 40 A (8 AWG white)', 97: 'AM2 30 A (10 AWG brown)', 115: 'JB1 60 A (6 AWG white)', 133: 'EPS 60 A (8 AWG red) to k_eps'}
    for y, (nm, od, bc) in OUTB.items():
        if nm == 'BUS1':
            continue
        cable('OUT_' + nm, [(PXE, y, OUTZ[y]), (xt[y], y, OUTZ[y]), (xt[y], -70, OUTZ[y])], od, OUTC[y], Rf(od), label=OUTL[y] + ': forward to the dash harness', at=(xt[y], -20, OUTZ[y]), v='FT')
    # Bus 1: POWER BUS1 50 A out -> round the front of the POWER box, over the looms -> LOGIC Bus 1 feed (front)
    xb1 = 15.65 + LX
    cable('Bus1', [(PXE, 43, 13), (426.4, 43, 13), (426.4, -110, 13), (260, -110, 40), (xb1, -110, 40), (xb1, -48, 22), (xb1, -30, 22)], 5.13, 'Red', Rf(5.13),
          bands=['White', 'Blue', 'White'], label='Bus 1 feed (8 AWG red, w_hc_fb): POWER BUS1 50 A -> LOGIC front', at=(150, -110, 40), v='FT')
    # Bus 2: k_efi 87 (POWER inboard tail at y 61) -> up over the other tails -> round the rear -> LOGIC Bus 2 feed (rear)
    xb2 = 32.85 + LX
    cable('Bus2', [(130, 61, 6.3), (92, 61, 6.3), (92, 130, 50), (92, 300, 50), (xb2, 300, 50), (xb2, 250, 13), (xb2, 211, 13)], 3.61, 'Red', Rf(3.61),
          bands=['Blue', 'Yellow'], label='Bus 2 feed (10 AWG red, w77_cp): k_efi 87 -> LOGIC rear', at=(92, 230, 50))
    # harness tails -> the CabinPower loom (forward)
    lanes = [(35.0, 4.5, 7.1, 2.41), (43.0, 6.5, 8.1, 5.13), (52.0, 2.7, 6.1, 1.57), (70.0, 2.7, 6.1, 1.57), (79.0, 3.0, 6.3, 2.97),
             (88.0, 2.7, 6.1, 1.57), (97.0, 5.1, 7.4, 5.13), (106.0, 2.7, 6.1, 1.57), (115.0, 5.1, 7.4, 5.13), (124.0, 2.7, 6.1, 1.57),
             (133.0, 3.6, 6.6, 3.61), (142.0, 1.6, 5.6, 1.57)]
    for (y, d, z, odmax) in lanes:
        cable('PL_%d' % y, [(130, y, z), (75, y, z), (75, -200, z)], d, 'loom', Rf(odmax) + d / 2 - odmax / 2)
    labels.append(((75, -160, 7), 'POWER relay + ACPS tails: one loom forward to the dash (CabinPower)', 'FT'))
    for (x, d, z) in ((10.5, 7.2, 8.4), (38.0, 7.9, 8.75), (49.0, 10.1, 9.85), (67.5, 7.1, 8.35)):
        cable('LL_%d' % x, [(x + LX, -30, z), (x + LX, -200, z)], d, 'loom', 1.0)
    labels.append(((10.5 + LX, -160, 8.4), 'LOGIC fuse + relay tails: 4 bundles forward (CabinPower)', 'FT'))
    shelf = tb.createBox(adsk.core.OrientedBoundingBox3D.create(P(132.5, 115, -2), V(1, 0, 0), V(0, 1, 0), 52.5, 35.0, 0.4))

    for (name, bl, colour, p0, p1) in cables:
        tmp('Cable_' + name, [(b, colour) for b in bl])
    tmp('Bands_arr', arr_bands)
    tmp('Clamps', clamps)
    tmp('Shelf', [(shelf, 'shelf')], opacity=0.45)
    labels.append(((440, 202, 109.1), 'P-clamp each side of every 1/0 bend (bend 3 x OD = 41 mm, supported)', 'FRT'))
    labels.append(((-100, 250, 0), 'glove-box shelf (stand-in: the real mount spot is still to be measured)', 'FRT'))

    TRUNK = ['Tmp_Cable_fp_feed', 'Tmp_Cable_fp_pump', 'Tmp_Cable_fp_coil', 'Tmp_Floor', 'Tmp_Bands_B']
    GLOVE = lambda n: not n.startswith('BattRelay_') and n not in TRUNK
    show(GLOVE)
    tgtA = (175.0, 150.0, 20.0)
    LV = lambda k: [(p, t) for (p, t, v) in labels if k in v]
    shot('arr_glove_closed.png', (-0.55, -1.0, 0.75), tgtA, ortho=False, ext=1.25, labels=LV('F'))
    shot('arr_glove_rear.png', (0.75, 1.0, 0.45), tgtA, ortho=False, ext=1.25, labels=LV('R'))
    show(lambda n: GLOVE(n) and not n.split('_', 1)[1].startswith(('Cover', 'Pan')))
    shot('arr_glove_open.png', (-0.55, -1.0, 0.75), tgtA, ortho=False, ext=1.25,
         labels=[(p, t) for (p, t, v) in labels if 'Bus' in t] + [((16.5 + LX, 52.1, 30.0), 'LOGIC: 14 AWG fuse input jumpers to the bus strips (inside the box)'),
                                                        ((275.8, 120.0, 55.0), 'POWER: AMI fuses straight on the + bar (rev 7)')])
    show(lambda n: GLOVE(n))
    shot('arr_glove_top.png', (0.0, 0.0, 1.0), tgtA, ortho=True, ext=1.15, labels=LV('T'))

    # ================================================================ typical arrangement, trunk (battery relay block)
    tcab = []
    cables2 = []

    def cable2(name, pts, od, colour, R, bands, label, at=None):
        cl, tans = fillet(pts, R, name)
        cables2.append((name, tube(cl, od, R), colour, pts[0], pts[-1]))
        tcab.append((at or pts[-1], label))
    cable2('fp_feed', [(-30, -145.1, 42.7), (-75, -145.1, 42.7), (-75, -270, 12)], 3.61, 'Red', Rf(3.61), None,
           'from the kill switch MAIN 2 (battery box): 10 AWG red, W-W-B')
    cable2('fp_pump', [(214, -145.1, 43.5), (262, -145.1, 43.5), (262, -20, 12)], 3.61, 'Red', Rf(3.61), None,
           'to the fuel pump (RearFuel): 10 AWG red, W-W-B')
    cable2('fp_coil', [(214, -165.4, 24.5), (240, -165.4, 24.5), (240, -270, 10)], 1.85, 'White', Rf(1.85), None,
           'coil leads 85 white / 86 red (18 AWG): to A-cabin A19 (Aux 3) + 12 V', at=(240, -215, 13))
    for (name, bl, colour, p0, p1) in cables2:
        tmp('Cable_' + name, [(b, colour) for b in bl])
    floor = tb.createBox(adsk.core.OrientedBoundingBox3D.create(P(95, -150, -2), V(1, 0, 0), V(0, 1, 0), 42.0, 28.0, 0.4))
    tmp('Floor', [(floor, 'shelf')], opacity=0.45)
    tcab.append(((20, -262, 0), 'trunk floor, passenger side between the rear wall and the battery (stand-in)'))
    show(lambda n: n.startswith('BattRelay_') or n in ('Tmp_Bands_B', 'Tmp_Floor') or n in ['Tmp_Cable_' + c[0] for c in cables2])
    shot('arr_trunk.png', (-0.6, -1.0, 0.7), (110.0, -150.0, 20.0), ortho=False, ext=1.2, labels=tcab)

    # ================================================================ clash check (temp cables vs everything else)
    rep = {'warn': WARN, 'clash': []}
    if CHECK:
        mm = app.measureManager
        others = []
        for o in root.occurrences:
            n = o.component.name
            if n.startswith(('Tmp_Bands', 'Tmp_Clamps', 'Tmp_Shelf', 'Tmp_Floor')):
                continue
            for b in o.bRepBodies:
                others.append((n, b))
        trunk_names = set(TRUNK)
        for (name, bl, colour, p0, p1) in cables + cables2:
            in_trunk = 'Tmp_Cable_' + name in trunk_names
            mine_all = list(occ['Tmp_Cable_' + name].bRepBodies)
            for (n, b) in others:
                if n == 'Tmp_Cable_' + name:
                    continue
                if in_trunk != (n.startswith('BattRelay_') or n in trunk_names):
                    continue              # the two scenes are apart in the car
                if name.startswith(('PL_', 'LL_')) and n.startswith(('Tmp_Cable_PL_', 'Tmp_Cable_LL_')):
                    continue              # tails tied into one loom
                bb = b.boundingBox
                ins = lambda q: all(bb.minPoint.asArray()[i] * 10 - 0.6 <= q[i] <= bb.maxPoint.asArray()[i] * 10 + 0.6 for i in range(3))
                if (ins(p0) or ins(p1)) and ('Wire' in n or 'Harness' in n):
                    continue              # its own stub
                d = min(mm.measureMinimumDistance(mine, b).value * 10 for mine in mine_all)
                if d < 1.0:
                    rep['clash'].append((name, n, round(d, 2)))
    json.dump({'labels': LABELS, 'img': IMG, 'report': rep}, open(os.path.join(RAW, 'labels.json'), 'w'), indent=1)
    print(json.dumps(rep))
