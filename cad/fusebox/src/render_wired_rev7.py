"""Wired fuse boxes (Dan, 2026-10-14: "aren't there going to be more wires in these? can you simulate that?"): EVERY harness
wire that lands in POWER rev 7, LOGIC and the battery relay block, from cad/fusebox/rev7/wiring_plan.json (wiring_sim.py:
real cavity, gauge OD, insulation colour, ident bands, the CAD lanes with the bend rule), drawn as Tmp_ bodies in the open
ST185_fusebox_rev7 document, then
  - checks: every wire against the printed parts (through plastic / the cover closing), against the pull path of every fuse
    and relay, against the bare copper and steel, and wire against wire;
  - renders (with the wires in place): per box exploded, underneath, long side, short end, routing (from below); the glove
    box and trunk arrangement with the boxes cabled together.
RENDER + CHECK ONLY: never saves (R74) - close the document without saving afterwards. Raw PNGs + labels.json + the check
report go to RAW; then   python cad/fusebox/src/label_views_rev7.py cad/fusebox/rev7 [RAW]   and the report is copied to
cad/fusebox/rev7/wiring_report.json (check_clearance.py reads it).
Claude Code, 2026-10-14.
"""
import adsk.core, adsk.fusion, math, os, sys, json, tempfile, importlib

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config\cad\fusebox\src'
PLAN = os.path.join(os.path.dirname(SRC), 'rev7', 'wiring_plan.json')
RAW = os.path.join(tempfile.gettempdir(), 'st185_rev7_wired')
ONLY = None           # e.g. {'logic_wired_routing.png'} while iterating
CHECK = True
app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
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
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def cyl(p0, p1, d):
    return tb.createCylinderOrCone(P(*p0), d / 20.0, P(*p1), d / 20.0)


WARN = []


def halfspace(C, d):
    t = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    u = nrm(cross(d, t))
    return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P(*add(C, mul(d, 1500.0))), V(*d), V(*u), 300.0, 300.0, 300.0))


def fillet(pts, R, name):
    """Polyline -> pieces with a bend at every corner; R = one centre radius or one per corner."""
    Rs = R if isinstance(R, (list, tuple)) else [R] * max(1, len(pts) - 2)
    pieces, cur, tans, tprev = [], pts[0], [], 0.0
    for i in range(1, len(pts) - 1):
        Pc, r = pts[i], Rs[i - 1]
        a, b = nrm(sub(Pc, pts[i - 1])), nrm(sub(pts[i + 1], Pc))
        th = math.acos(max(-1.0, min(1.0, dot(a, b))))
        t = r * math.tan(th / 2) if th > 1e-6 else 0.0
        if ln(sub(Pc, pts[i - 1])) + 1e-6 < tprev + t:
            WARN.append('%s: segment %d too short for its bends (%.1f < %.1f)' % (name, i, ln(sub(Pc, pts[i - 1])), tprev + t))
        if th < 1e-6:
            tprev = 0.0
            continue
        S = sub(Pc, mul(a, t))
        n = nrm(sub(b, mul(a, dot(a, b))))
        pieces.append(('line', cur, S))
        pieces.append(('arc', add(S, mul(n, r)), n, a, th, r))
        cur = add(Pc, mul(b, t))
        tans += [(S, a), (cur, b)]
        tprev = t
    if ln(sub(pts[-1], pts[-2])) + 1e-6 < tprev:
        WARN.append('%s: last segment too short' % name)
    pieces.append(('line', cur, pts[-1]))
    return pieces, tans


def tube(pieces, od):
    out = []
    for pc in pieces:
        if pc[0] == 'line':
            if ln(sub(pc[2], pc[1])) > 0.05:
                out.append(cyl(pc[1], pc[2], od))
            continue
        _, C, n, a, th, r = pc
        tor = tb.createTorus(P(0, 0, 0), V(*[c + 0.0 for c in cross(n, a)]), r / 10.0, od / 20.0)   # at the origin: createTorus ignores
        e = math.radians(0.3)                                                                       # its centre on a +-Z axis
        a_ = sub(mul(a, math.cos(e)), mul(n, math.sin(e)))
        b_ = add(mul(n, math.sin(th + e)), mul(a, math.cos(th + e)))
        ok = tb.booleanOperation(tor, halfspace((0, 0, 0), a_), INTER) and tb.booleanOperation(tor, halfspace((0, 0, 0), mul(b_, -1.0)), INTER)
        mt = adsk.core.Matrix3D.create()
        mt.translation = V(C[0] / 10.0, C[1] / 10.0, C[2] / 10.0)
        tb.transform(tor, mt)
        if not ok or tor.volume < 1e-7:
            WARN.append('bend piece failed (R %.1f, %.0f deg)' % (r, math.degrees(th)))
            continue
        out.append(tor)
    return out


def bands_on(p_end, d_in, od, colours, start=0.3, w=2.0, pitch=2.4):
    return [(cyl(add(p_end, mul(d_in, start + k * pitch)), add(p_end, mul(d_in, start + k * pitch + w)), od + 0.7), c)
            for k, c in enumerate(colours)]


def sleeve(p, d, od):
    s = cyl(sub(p, mul(d, 7.0)), add(p, mul(d, 7.0)), od + 6.0)
    tb.booleanOperation(s, cyl(sub(p, mul(d, 8.0)), add(p, mul(d, 8.0)), od - 0.2), SUBTR)
    return s


def run(_context: str):
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import spec as S
    importlib.reload(S)
    plan = json.load(open(PLAN, encoding='utf-8'))
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
        for b in o.bRepBodies:
            b.isLightBulbOn = True
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
    RGB = {'Red': (200, 22, 22), 'Black': (28, 28, 30), 'White': (238, 238, 232), 'Brown': (112, 62, 26), 'Blue': (30, 85, 205),
           'Yellow': (245, 210, 20), 'Green': (30, 150, 60), 'Violet': (130, 60, 180), 'Gray': (140, 140, 140), 'Orange': (240, 120, 20)}
    C = {k: col('W ' + k, v) for k, v in RGB.items()}
    C.update({'loom': col('W loom grey', (120, 122, 126), 'Plastic - Matte (Gray)'), 'clamp': col('W clamp', (45, 45, 48), 'Plastic - Matte (Gray)'),
              'shelf': col('W shelf', (196, 186, 166), 'Plastic - Matte (Gray)')})
    occ = {o.component.name: o for o in root.occurrences}

    def tmp(name, items, opacity=None):
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

    # ---- CAD cables kept (feeds, OUT row, 1/0, relay feeds, LOGIC jumpers): real colours. The CAD tail bundles and the single
    # battery coil lead are replaced by the simulated wires.
    OUTC = {43: 'Red', 61: 'Red', 79: 'White', 97: 'Brown', 115: 'White', 133: 'Red', 178: 'Red', 202: 'Red'}

    def paint(oname, fn):
        for b in occ[oname].bRepBodies:
            bb = b.boundingBox
            c = fn(bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.x * 10, bb.maxPoint.y * 10, bb.maxPoint.z * 10)
            if c is None:
                b.isLightBulbOn = False
            else:
                b.appearance = C[c]
    paint('Power_Wire_feed', lambda x0, y0, z0, x1, y1, z1: OUTC[min(OUTC, key=lambda k: abs(k - (y0 + y1) / 2))] if x1 > 365 else ('Black' if y1 > 270 else 'Red'))
    paint('Logic_Wire_feed', lambda *a: 'Red')
    paint('BattRelay_Wire_feed', lambda x0, y0, z0, x1, y1, z1: None if y1 < -158 else 'Red')
    for n in ('Power_Harness_wires', 'Logic_Harness_wires'):
        occ[n].isLightBulbOn = False
        for b in occ[n].bRepBodies:
            b.isLightBulbOn = False
    HIDE = {'Power_Harness_wires', 'Logic_Harness_wires'}

    # ---- the simulated wires, one Tmp_ component per box (box-local -> world: S.PLACE)
    PL = {'POWER': S.PLACE['POWER'], 'LOGIC': S.PLACE['LOGIC'], 'BATT': S.PLACE['BATTRELAY']}
    W = {'POWER': [], 'LOGIC': [], 'BATT': []}
    BANDS = {'POWER': [], 'LOGIC': [], 'BATT': []}
    meta = {}
    for w in plan['wires']:
        colour = w['colour'] if w['colour'] in C else 'Red'
        for k, bp in enumerate(w['box_paths']):
            box = bp['box']
            off = (PL[box][0], PL[box][1], 0.0)
            pts = [add(tuple(p), off) for p in bp['pts']]
            pcs, _ = fillet(pts, bp['R'], w['wire'])
            bodies = tube(pcs, w['od'])
            W[box].append((w['wire'] + ('#%d' % k if k else ''), bodies, colour))
            meta[w['wire'] + ('#%d' % k if k else '')] = dict(box=box, od=w['od'], colour=colour, gauge=w['gauge'], end=bp.get('end'))
            BANDS[box] += bands_on(pts[0], nrm(sub(pts[1], pts[0])), w['od'], w['bands'])
            if bp.get('loop') or bp.get('direct'):
                BANDS[box] += bands_on(pts[-1], nrm(sub(pts[-2], pts[-1])), w['od'], w['bands'])
    # battery block coil plug: 85 (white) and 86 (red), 18 AWG, side by side where the CAD drew one lead
    BX, BY = S.PLACE['BATTRELAY']
    od18 = S.OD[18]
    for (wid, colr, dz, bands) in (('w_fp85_h', 'White', -(od18 / 2 + 0.15), ['White', 'White', 'Blue']), ('w_fp86_h', 'Red', od18 / 2 + 0.15, ['Blue'])):
        pts = [(103.0, -161.0, 24.5 + dz), (103.0, -169.0, 24.5 + dz), (214.0, -169.0, 24.5 + dz)]
        W['BATT'].append((wid, tube(fillet(pts, 3 * od18 + od18 / 2, wid)[0], od18), colr))      # 3 x OD (tied at the plug)
        meta[wid] = dict(box='BATT', od=od18, colour=colr, gauge=18, end='k_fp coil plug')
        BANDS['BATT'] += bands_on(pts[0], (0, -1, 0), od18, bands)
    # J3 / J4 (R94): the HL / HR splices in the LOGIC front channel (est size: solder splice + adhesive heat shrink over)
    own_sp = {}
    for w in plan['wires']:
        for e in w['ends']:
            if e['id'] in ('sp_hl', 'sp_hr'):
                own_sp.setdefault(e['id'], set()).add(w['wire'])
    for sp in plan.get('splices', []):
        off = (PL[sp['box']][0], PL[sp['box']][1], 0.0)
        W[sp['box']].append((sp['id'], [cyl(add(tuple(sp['p0']), off), add(tuple(sp['p1']), off), sp['od'])], 'clamp'))
        meta[sp['id']] = dict(box=sp['box'], od=sp['od'], colour='clamp', gauge=None, end='splice (%s)' % sp['basis'])
    for box in W:
        o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        o.component.name = 'Tmp_W_' + box
        for (wid, bodies, colr) in W[box]:
            for k_, b in enumerate(bodies):
                bb = o.component.bRepBodies.add(b)
                bb.name = '%s~%d' % (wid, k_)           # unique: Fusion renames duplicates "name (1)"
                bb.appearance = C[colr]
        occ[o.component.name] = o
        tmp('WB_' + box, BANDS[box])
    BOXPRE = {'POWER': 'Power_', 'LOGIC': 'Logic_', 'BATT': 'BattRelay_'}

    # ================================================================ checks
    rep = dict(warn=WARN, through_printed=[], cover=[], pull=[], wire_wire=dict(pairs=0, overlaps=[], min_mm=None),
               bare_metal_touch=[], live_to_live={}, wires_drawn={b: len(W[b]) for b in W})
    if CHECK:
        mm = app.measureManager

        def bbox(b):
            bb = b.boundingBox
            return (bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.x * 10, bb.maxPoint.y * 10, bb.maxPoint.z * 10)

        def near(a, b, g=0.6):
            return all(a[i] - g <= b[i + 3] and b[i] - g <= a[i + 3] for i in range(3))

        def mind(A, B):
            return min(mm.measureMinimumDistance(x, y).value * 10 for x in A for y in B)
        wb = {}                                   # wire -> (bodies, bbox)
        for box in W:
            groups = {}
            for b in occ['Tmp_W_' + box].bRepBodies:
                groups.setdefault(b.name.split('~')[0], []).append(b)
            for wid, bl in groups.items():
                bbs = [bbox(b) for b in bl]
                wb[wid] = (box, bl, tuple(min(x[i] for x in bbs) for i in range(3)) + tuple(max(x[i + 3] for x in bbs) for i in range(3)))
        printed, metal, pullers = {}, {}, {}
        for o in root.occurrences:
            n = o.component.name
            for box, pre in BOXPRE.items():
                if not n.startswith(pre):
                    continue
                kd = n[len(pre):]
                for b in o.bRepBodies:
                    if kd.startswith(('Base', 'Cover', 'Pan')):
                        printed.setdefault(box, []).append((kd.split('_')[0], b, bbox(b)))
                    elif kd.startswith(('Bar', 'Pad', 'Strip', 'Strap', 'Standoff', 'Lug', 'LugBolt', 'EarBolt', 'BarBolt', 'SetScrew', 'Nut', 'Washer', 'FlangeBolt')):
                        metal.setdefault(box, []).append((kd, b, bbox(b)))
                    elif kd.startswith(('Fuse', 'Relay')):
                        pullers.setdefault(box, []).append((kd, b, bbox(b)))
        for wid, (box, bl, bxw) in wb.items():
            for (kd, b, bxp) in printed.get(box, []):
                if near(bxw, bxp) and mind(bl, [b]) < 0.05:
                    (rep['cover'] if kd == 'Cover' else rep['through_printed']).append((wid, kd))
            for (kd, b, bxm) in metal.get(box, []):
                if near(bxw, bxm):
                    d = mind(bl, [b])
                    if d < 0.3:
                        rep['bare_metal_touch'].append((wid, kd, round(d, 2)))
        # pull path: each fuse / relay body's footprint, from its bottom to 150 mm above (it lifts straight up)
        cad_cables = []
        for n in ('Power_Wire_feed', 'Logic_Wire_feed', 'Logic_Wire_jumper_14AWG', 'BattRelay_Wire_feed'):
            cad_cables += [(n, b) for b in occ[n].bRepBodies if b.isLightBulbOn]
        env_o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        env_o.component.name = 'Tmp_PullEnvelopes'
        for box, L in pullers.items():
            for (kd, b, bxp) in L:
                if 'HCR150' in kd:     # fit audit 2026-10-18: the HCR150 is bolted down, not plugged in - its lugs and coil plug come off first
                    continue
                ob = adsk.core.OrientedBoundingBox3D.create(P((bxp[0] + bxp[3]) / 2, (bxp[1] + bxp[4]) / 2, bxp[2] + 75.0 + 0.5), V(1, 0, 0), V(0, 1, 0),
                                                           (bxp[3] - bxp[0]) / 10.0, (bxp[4] - bxp[1]) / 10.0, 15.0)
                e = env_o.component.bRepBodies.add(tb.createBox(ob)).createForAssemblyContext(env_o)
                eb = bbox(e)
                for wid, (wbox, bl, bxw) in wb.items():
                    if near(bxw, eb, 0.0) and mind(bl, [e]) < 0.01:
                        rep['pull'].append((box + ' ' + kd, wid))
                for (cn, cb) in cad_cables:
                    if near(bbox(cb), eb, 0.0) and mm.measureMinimumDistance(cb, e).value < 0.001:
                        rep['pull'].append((box + ' ' + kd, cn))
        env_o.deleteMe()
        # wire against wire, same box
        ids = list(wb)
        mn = None
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                A, B = wb[ids[i]], wb[ids[j]]
                if A[0] != B[0] or not near(A[2], B[2], 0.5):
                    continue
                if ids[j] in own_sp.get(ids[i], ()) or ids[i] in own_sp.get(ids[j], ()):
                    continue                                 # a wire ends inside its own splice
                rep['wire_wire']['pairs'] += 1
                d = mind(A[1], B[1])
                mn = d if mn is None else min(mn, d)
                if d < 0.01:
                    rep['wire_wire']['overlaps'].append((ids[i], ids[j]))
        rep['wire_wire']['min_mm'] = round(mn, 2) if mn is not None else None
    rep['warn'] = WARN

    # ================================================================ renders
    LABELS = {}

    def show(pred):
        for o in root.occurrences:
            n = o.component.name
            o.isLightBulbOn = bool(pred(n)) and n not in HIDE

    def place(off):
        for o in root.occurrences:
            m = adsk.core.Matrix3D.create()
            d = off.get(o.component.name)
            if d:
                m.translation = V(d[0] / 10.0, d[1] / 10.0, d[2] / 10.0)
            o.transform2 = m

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
        LABELS[fn] = []
        for (p3, text) in labels:
            p2 = vp.modelToViewSpace(P(*p3))
            LABELS[fn].append([round(p2.x * k_img, 1), round(p2.y * k_img, 1), text])

    kind = lambda n: n.split('_', 1)[1]
    PX = S.PLACE['POWER'][0]
    BOXES = {
        'power': ('Power_', 'POWER', (PX + 90.0, 121.0, 30.0), (1, 0, 0.36), (0, -1, 0.36)),
        'logic': ('Logic_', 'LOGIC', (40.0, 90.0, 30.0), (-1, 0, 0.36), (-0.55, -1, 0.3)),
        'battrelay': ('BattRelay_', 'BATT', (BX + 92.0, BY + 46.0, 25.0), (0, -1, 0.36), (-1, -0.5, 0.3)),
    }
    LB = {   # a few labels per box (world points)
        'logic': [((30.0, S.CHANNEL['y'], S.CHANNEL['floor'][1]), 'J4: front channel - HL, HR, ETB cross in front of the spine, inside the box'),
                  ((34.0, S.CHANNEL['y_sp'], S.CHANNEL['z']['HR'] + 2.5), 'J3: HL and HR splices in the channel (one wire per fuse terminal)'),
                  ((sum(S.PAN_RIB['x']) / 2, 60.0, S.PAN_RIB['z_top']), 'J2: pan rib between the Bus 1 wires and the strip bolt heads'),
                  ((S.MINI_COLS['BUS1'][0] - S.MINI_BLADE_X, -30.0, 9.0), 'Bus 1 exit: %d wires' % next(x['wires'] for x in plan['exits'] if x['box'] == 'LOGIC' and abs(x['lane'] - (S.MINI_COLS['BUS1'][0] - S.MINI_BLADE_X)) < 0.01))],
        'power': [((PX - 30.0, 43.0, 8.0), 'relay + ACPS wires: 21 into 12 bundles out of the inboard end')],
        'battrelay': [((214.0, -169.0, 24.5), 'coil plug: 85 white + 86 red, 18 AWG')],
    }
    for key, (pre, box, tgt, e_long, e_end) in BOXES.items():
        mine = lambda n, pre=pre, box=box: n.startswith(pre) or n in ('Tmp_W_' + box, 'Tmp_WB_' + box)
        show(mine)
        place({})
        shot('%s_wired_side_long.png' % key, e_long, tgt, labels=LB.get(key, []))
        shot('%s_wired_side_end.png' % key, e_end, tgt, labels=LB.get(key, []))
        show(lambda n: mine(n) and not (n.startswith(pre) and kind(n).startswith('Pan')))
        shot('%s_wired_under.png' % key, (-0.6, -1.0, -0.75), tgt, ortho=False, ext=1.15, labels=LB.get(key, []))
        show(lambda n: mine(n) and not (n.startswith(pre) and kind(n).startswith(('Pan', 'Cover'))))
        shot('%s_wired_routing.png' % key, (0.0, 0.0, -1.0), tgt, ortho=True, ext=1.15, labels=LB.get(key, []))
        show(mine)
        off = {}
        for o in root.occurrences:
            n = o.component.name
            if not n.startswith(pre):
                continue
            kd = kind(n)
            if kd.startswith('Cover'):
                off[n] = (0, 0, 160)
            elif kd.startswith(('Relay', 'Fuse', 'SPARE', 'Nut')) and not kd.startswith('Relay_TE_HCR150'):
                off[n] = (0, 0, 90)
            elif kd.startswith('Pan'):
                off[n] = (0, 0, -110)
        place(off)
        shot('%s_wired_explode.png' % key, (-0.6, -1.0, 0.45), tgt, ortho=False, ext=1.1, labels=LB.get(key, []))
        place({})

    # ================================================================ arrangement, glove box (LOGIC 55 mm inboard: bend room)
    LX = -55.0
    m = adsk.core.Matrix3D.create()
    m.translation = V(LX / 10.0, 0, 0)
    for o in root.occurrences:
        if o.component.name.startswith('Logic_') or o.component.name in ('Tmp_W_LOGIC', 'Tmp_WB_LOGIC'):
            o.transform2 = m
    OD10, PXE = 13.6, 370.5
    R10 = 3 * OD10 + OD10 / 2
    rf = lambda od: 10 * od + od / 2
    rs = lambda od: max(3 * od + od / 2, 4.0)
    arr, clamps, labels = [], [], []

    def cable(name, pts, od, colour, R, label=None, at=None, clamp=False, v='FRT', bands=()):
        pcs, tans = fillet(pts, R, name)
        arr.append((name, tube(pcs, od), colour))
        if bands:
            clamps.extend(bands_on(pts[0], nrm(sub(pts[1], pts[0])), od, list(bands), start=2.0, w=4.0, pitch=6.0))
        if clamp:
            clamps.extend((sleeve(p, d, od), 'clamp') for (p, d) in tans)
        if label:
            labels.append((at or pts[-1], label, v))
    cable('BATpos', [(PXE, 178, 61.5), (420, 178, 61.5), (420, 178, -120), (420, 520, -120)], OD10, 'Red', R10, 'H1 BAT+ (1/0 red) to the battery', (420, 178, -30), True, 'R')
    cable('RADpos', [(PXE, 202, 61.5), (440, 202, 61.5), (440, 202, 170), (440, -110, 170)], OD10, 'Red', R10, 'H3 RADLOK+ (1/0 red) to the RH firewall', (440, 60, 170), True)
    cable('BATneg', [(175, 273, 61.5), (175, 400, 61.5), (175, 400, -150), (380, 400, -150), (380, 520, -150)], OD10, 'Black', R10, 'H2 BAT- (1/0 black)', (175, 400, -60), True, 'R')
    cable('RADneg', [(198, 273, 61.5), (198, 375, 61.5), (500, 375, 61.5), (500, 375, 170), (500, -110, 170)], OD10, 'Black', R10, 'H6a RADLOK- (1/0 black)', (500, 150, 170), True)
    cable('GNDID', [(221, 273, 61.5), (221, 350, 61.5), (221, 350, -100), (-150, 350, -100)], OD10, 'Black', R10, 'H7 GND ID (1/0 black) to the left kick', (-140, 350, -100), True)
    cable('GNDIG', [(244, 273, 61.5), (244, 325, 61.5), (244, 325, -70), (395, 325, -70)], OD10, 'Black', R10, 'H7 GND IG (1/0 black) to the right kick', (340, 325, -70), True, 'R')
    xt = {61: 434.5, 79: 442.5, 97: 450.5, 115: 462.0, 133: 472.0}
    for y, (nm, od) in {61: ('RTR', 3.61), 79: ('AM1', 5.13), 97: ('AM2', 3.61), 115: ('JB1', 6.43), 133: ('EPS', 5.13)}.items():
        z = 13.75 if y == 115 else 13.0
        cable('OUT_' + nm, [(PXE, y, z), (xt[y], y, z), (xt[y], -70, z)], od, OUTC[y], rf(od))
    labels.append(((450.0, -20.0, 13.0), 'AMI OUT row (RTR, AM1, AM2, JB1, EPS) forward to the dash harness', 'FT'))
    cb1, cb2 = S.MINI_COLS['BUS1'][0], S.MINI_COLS['BUS2'][0]
    xb1, xb2 = cb1 + 2.15 + LX, cb2 - 2.15 + LX                  # LOGIC Bus 1 (front) / Bus 2 (rear) feed lug lines
    zf1 = S.FEED['BUS1']['z']                                    # J4 (R94): the Bus 1 feed lug sits lower (z 13)
    cable('Bus1', [(PXE, 43, 13), (426.4, 43, 13), (426.4, -110, 13), (260, -110, 40), (xb1, -110, 40), (xb1, -48, zf1), (xb1, -30, zf1)], 5.13, 'Red', rf(5.13),
          'Bus 1 feed (8 AWG red): POWER BUS1 50 A -> LOGIC front', (150, -110, 40), v='FT', bands=['White', 'Blue', 'White'])
    # breakouts that leave the looms: from each wire's own slot at its box's exit (wiring_plan)
    slot_end = {}
    for w in plan['wires']:
        for bp in w['box_paths']:
            if bp.get('loop') or bp.get('direct'):
                continue
            p = bp['pts'][-1]
            off = (PL[bp['box']][0] + (LX if bp['box'] == 'LOGIC' else 0.0), PL[bp['box']][1], 0.0)
            slot_end[(w['wire'], bp['box'])] = add(tuple(p), off)
    wcol = {w['wire']: (w['colour'], w['od'], w['bands']) for w in plan['wires']}
    s = slot_end[('w77_cp', 'POWER')]
    cable('Bus2', [s, (92, s[1], s[2]), (92, 130, 50), (92, 300, 50), (xb2, 300, 50), (xb2, 250, 13), (xb2, 211, 13)], 3.61, 'Red', rf(3.61),
          'Bus 2 feed (10 AWG red): k_efi 30 -> LOGIC rear', (92, 230, 50))
    s, e = slot_end[('w_k_efi_86_cp', 'LOGIC')], slot_end[('w_k_efi_86_cp', 'POWER')]
    cable('efi86', [s, (s[0], -60, s[2]), (s[0], -80, 30), (96, -80, 30), (96, e[1], 30), e], wcol['w_k_efi_86_cp'][1], 'Red', rf(1.85),
          'k_efi 86 (18 AWG red): LOGIC EFI86 5 A -> POWER k_efi', (40, -80, 30), v='FT')
    stub = (263.5, 273.0, 57.2)
    s = slot_end[('w_rev_85_cp', 'LOGIC')]
    cable('krev85', [s, (s[0], -75, s[2]), (s[0], -95, 40), (106, -95, 40), (106, 317, 40), (263.5, 317, 40), (263.5, 290, 58.4), (263.5, 273, 58.4)], 1.57, 'Black', rf(1.57),
          'k_rev 85 (20 AWG black): LOGIC -> POWER NEG bar ring', (106, 200, 40), v='RT')
    s = slot_end[('w_htr_87a_cp', 'POWER')]
    cable('htr87a', [s, (118, s[1], s[2]), (118, s[1] + 12, 30), (118, 311, 30), (262.3, 311, 30), (262.3, 290, 56.6), (262.3, 273, 56.6)], 2.41, 'Black', rs(2.41),
          'k_htr 87a + k_pwr 85 (black): out of the inboard end, round to the NEG bar ring', (118, 200, 30), v='RT')
    s = slot_end[('w_pwr_85_cp', 'POWER')]
    cable('pwr85', [s, (122, s[1], s[2]), (122, s[1] + 10, 30), (122, 305, 30), (264.7, 305, 30), (264.7, 288, 56.6), (264.7, 273, 56.6)], 1.85, 'Black', rs(1.85))
    BREAK = {('w77_cp', 'POWER'), ('w_k_efi_86_cp', 'LOGIC'), ('w_k_efi_86_cp', 'POWER'), ('w_rev_85_cp', 'LOGIC'), ('w_htr_87a_cp', 'POWER'), ('w_pwr_85_cp', 'POWER')}
    # looms: what is left of each exit bundle, grey, forward to the dash (POWER: -x then forward at x 75)
    for ex in plan['exits']:
        box, L0 = ex['box'], ex['lane']
        ms = [(wid, wcol[wid][1]) for (wid, b) in slot_end if b == box and (wid, b) not in BREAK and
              any(bp.get('lane') == L0 and bp['box'] == box and not bp.get('loop') for w in plan['wires'] if w['wire'] == wid for bp in w['box_paths'])]
        if not ms:
            continue
        ods = sorted([o for _, o in ms], reverse=True)
        d = ods[0] if len(ods) == 1 else 1.2 * math.sqrt(sum(o * o for o in ods))
        z = plan['constants']['BUNDLE_Z0'] + d / 2
        if box == 'POWER':
            cable('loom_P%d' % L0, [(130.0, L0, z), (75.0, L0, z), (75.0, -200.0, z)], d, 'loom', rf(max(ods)) + d / 2 - max(ods) / 2)
        else:
            cable('loom_L%d' % L0, [(L0 + LX, -30.0, z), (L0 + LX, -200.0, z)], d, 'loom', 1.0)
    labels.append(((75, -160, 7), 'POWER relay + ACPS tails: loom forward to the dash (CabinPower)', 'FT'))
    labels.append(((S.MINI_COLS['BUS1'][0] - S.MINI_BLADE_X + LX, -160, 8.4), 'LOGIC tails: 4 looms forward (CabinPower)', 'FT'))
    labels.append(((440, 202, 109.1), 'P-clamp each side of every 1/0 bend (3 x OD supported)', 'FRT'))
    for (name, bodies, colour) in arr:
        tmp('Arr_' + name, [(b, colour) for b in bodies])
    tmp('Arr_clamps', clamps)
    tmp('Arr_shelf', [(tb.createBox(adsk.core.OrientedBoundingBox3D.create(P(132.5, 115, -2), V(1, 0, 0), V(0, 1, 0), 52.5, 35.0, 0.4)), 'shelf')], opacity=0.45)
    labels.append(((-100, 250, 0), 'glove-box shelf (stand-in: the real mount spot is still to be measured)', 'FRT'))
    LV = lambda k: [(p, t) for (p, t, v) in labels if k in v]
    TRUNK = ('Tmp_Arr_fp_feed', 'Tmp_Arr_fp_pump', 'Tmp_Arr_fp_coil85', 'Tmp_Arr_fp_coil86', 'Tmp_Arr_floor', 'Tmp_W_BATT', 'Tmp_WB_BATT')
    GLOVE = lambda n: not n.startswith('BattRelay_') and n not in TRUNK and n != 'Tmp_PullEnvelopes'
    show(GLOVE)
    tgtA = (175.0, 150.0, 20.0)
    shot('arr_glove_wired.png', (-0.55, -1.0, 0.75), tgtA, ortho=False, ext=1.25, labels=LV('F'))
    shot('arr_glove_wired_rear.png', (0.75, 1.0, 0.45), tgtA, ortho=False, ext=1.25, labels=LV('R'))
    shot('arr_glove_wired_top.png', (0.0, 0.0, 1.0), tgtA, ortho=True, ext=1.15, labels=LV('T'))
    show(lambda n: GLOVE(n) and not (n.startswith(('Power_', 'Logic_')) and kind(n).startswith(('Cover', 'Pan'))))
    shot('arr_glove_wired_open.png', (-0.55, -1.0, 0.75), tgtA, ortho=False, ext=1.2,
         labels=[(p, t) for (p, t, v) in labels if 'Bus' in t or 'k_efi 86' in t])
    # ================================================================ trunk
    tcab = []
    for (name, pts, od, colour, R, label) in (
            ('fp_feed', [(-30, -145.1, 42.7), (-75, -145.1, 42.7), (-75, -270, 12)], 3.61, 'Red', rf(3.61), 'from the kill switch MAIN 2: 10 AWG red'),
            ('fp_pump', [(214, -145.1, 43.5), (262, -145.1, 43.5), (262, -20, 12)], 3.61, 'Red', rf(3.61), 'to the fuel pump (RearFuel): 10 AWG red'),
            ('fp_coil85', [(214, -169.0, 24.5 - (od18 / 2 + 0.15)), (238, -169.0, 23.4), (238, -270, 10)], od18, 'White', rf(od18), 'coil 85 (white) + 86 (red), 18 AWG: to A-cabin A19 / +12 V'),
            ('fp_coil86', [(214, -169.0, 24.5 + (od18 / 2 + 0.15)), (242, -169.0, 25.6), (242, -270, 12)], od18, 'Red', rf(od18), None)):
        tmp('Arr_' + name, [(b, colour) for b in tube(fillet(pts, R, name)[0], od)])
        if label:
            tcab.append((pts[-1] if name != 'fp_coil85' else (238, -215, 13), label))
    tmp('Arr_floor', [(tb.createBox(adsk.core.OrientedBoundingBox3D.create(P(95, -150, -2), V(1, 0, 0), V(0, 1, 0), 42.0, 28.0, 0.4)), 'shelf')], opacity=0.45)
    show(lambda n: n.startswith('BattRelay_') or n in TRUNK)
    shot('arr_trunk_wired.png', (-0.6, -1.0, 0.7), (110.0, -150.0, 20.0), ortho=False, ext=1.2, labels=tcab)
    place({})
    rep['meta'] = meta
    json.dump({'labels': LABELS, 'img': IMG}, open(os.path.join(RAW, 'labels.json'), 'w'), indent=1)
    json.dump(rep, open(os.path.join(RAW, 'wiring_checks.json'), 'w'), indent=1)
    print(json.dumps({k: (v if k != 'meta' else len(v)) for k, v in rep.items()})[:6000])
