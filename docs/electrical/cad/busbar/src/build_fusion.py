"""Build one ST185 bus-bar design in a new Fusion document and export every part.
Run inside Fusion (via the Fusion MCP script runner):  build('A', out_dir)  /  build('B', out_dir)
Claude Code, 2026-10-13.
"""
import adsk.core, adsk.fusion, math, os, sys, json, importlib

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\_scratch\st185-busbar\src'
if SRC not in sys.path:
    sys.path.insert(0, SRC)
import spec
importlib.reload(spec)

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
BT = adsk.fusion.BooleanTypes
OPS = {'u': BT.UnionBooleanType, 's': BT.DifferenceBooleanType, 'i': BT.IntersectionBooleanType}


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def V(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


def bo(target, tool, op):
    ok = tb.booleanOperation(target, tool, OPS[op])
    if not ok:
        raise RuntimeError('boolean %s failed' % op)
    return target


def box(x0, y0, z0, x1, y1, z1):
    obb = adsk.core.OrientedBoundingBox3D.create(
        P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), V(1, 0, 0), V(0, 1, 0),
        abs(x1 - x0) / 10.0, abs(y1 - y0) / 10.0, abs(z1 - z0) / 10.0)
    return tb.createBox(obb)


def rbox(cx, cy, z0, z1, L, W, ang):
    a = math.radians(ang)
    obb = adsk.core.OrientedBoundingBox3D.create(
        P(cx, cy, (z0 + z1) / 2), V(math.cos(a), math.sin(a), 0), V(-math.sin(a), math.cos(a), 0),
        L / 10.0, W / 10.0, (z1 - z0) / 10.0)
    return tb.createBox(obb)


def cyl(p0, p1, d, d1=None):
    return tb.createCylinderOrCone(P(*p0), d / 20.0, P(*p1), (d if d1 is None else d1) / 20.0)


def cylz(x, y, z0, z1, d):
    return cyl((x, y, z0), (x, y, z1), d)


def hexz(x, y, z0, z1, af):
    h = rbox(x, y, z0, z1, af * 2, af, 0)
    for ang in (60, 120):
        bo(h, rbox(x, y, z0, z1, af * 2, af, ang), 'i')
    return h


def slot(cx, cy, z0, z1, length, width):
    s = box(cx - (length - width) / 2, cy - width / 2, z0, cx + (length - width) / 2, cy + width / 2, z1)
    bo(s, cylz(cx - (length - width) / 2, cy, z0, z1, width), 'u')
    bo(s, cylz(cx + (length - width) / 2, cy, z0, z1, width), 'u')
    return s


def slot_y(cx, cy, z0, z1, length, width):
    s = box(cx - width / 2, cy - (length - width) / 2, z0, cx + width / 2, cy + (length - width) / 2, z1)
    bo(s, cylz(cx, cy - (length - width) / 2, z0, z1, width), 'u')
    bo(s, cylz(cx, cy + (length - width) / 2, z0, z1, width), 'u')
    return s


def union_all(bodies):
    b0 = bodies[0]
    for b in bodies[1:]:
        bo(b0, b, 'u')
    return b0


def lib_item(lib_name, kind, name):
    lib = app.materialLibraries.itemByName(lib_name)
    if lib is None:
        return None
    coll = lib.appearances if kind == 'app' else lib.materials
    return coll.itemByName(name)


def M(x=0.0, y=0.0, z=0.0, rot=0.0):
    m = adsk.core.Matrix3D.create()
    if rot:
        m.setToRotation(rot, V(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
    m.translation = V(x / 10.0, y / 10.0, z / 10.0)
    return m


def land_top(design, bar, y):
    if 'lands' in bar:
        for (y0, y1, top) in bar['lands']:
            if y0 <= y <= y1:
                return top
    return bar['field_top']


def build(name, out_dir):
    d = {'A': spec.A, 'B': spec.B, 'B_rev2': spec.B2, 'A_rev3': spec.A3, 'B_rev3': spec.B3}[name]
    os.makedirs(out_dir, exist_ok=True)
    doc_name = 'ST185_busbar_%s' % name
    doc = None
    for i in range(app.documents.count):
        dd = app.documents.item(i)
        if dd.isSaved and dd.name.split(' v')[0] == doc_name:
            doc = dd
    if doc is None:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    for i in range(root.occurrences.count - 1, -1, -1):      # rebuild in place
        root.occurrences.item(i).deleteMe()

    ap_body = lib_item('Fusion Appearance Library', 'app', 'Plastic - Matte (Black)')
    ap_cover = lib_item('Fusion Appearance Library', 'app', 'Plastic - Matte (Gray)')
    ap_al = lib_item('Fusion Appearance Library', 'app', 'Aluminum - Satin')
    ap_ss = lib_item('Fusion Appearance Library', 'app', 'Stainless Steel - Satin')
    ap_red = lib_item('Fusion Appearance Library', 'app', 'Plastic - Matte (Red)')
    ap_blue = lib_item('Fusion Appearance Library', 'app', 'Plastic - Matte (Blue)')
    ap_yel = lib_item('Fusion Appearance Library', 'app', 'Plastic - Matte (Yellow)')
    m_abs = lib_item('Fusion Material Library', 'mat', 'ABS Plastic')       # stand-in density for ASA
    m_al = lib_item('Fusion Material Library', 'mat', 'Aluminum 6061')
    m_ss = lib_item('Fusion Material Library', 'mat', 'Stainless Steel AISI 304')

    def new_comp(cname, bodies, appearance=None, material=None, opacity=None, m=None, parent=None):
        occs = (parent or root).occurrences
        occ = occs.addNewComponent(m or adsk.core.Matrix3D.create())
        c = occ.component
        c.name = cname
        for b in bodies:
            bb = c.bRepBodies.add(b)
            bb.name = cname
            if appearance is not None:
                bb.appearance = appearance
            if opacity is not None and hasattr(bb, 'opacity'):
                bb.opacity = opacity
        if material is not None:
            c.material = material
        return occ

    cache = {}

    def place(key, parent, m, make, appearance=None, material=None, opacity=None):
        """First call builds the component at m; later calls add another occurrence of it."""
        # every instance lives directly in the root: nested instances needed transform overrides, which the saved
        # document lost (instances fell back onto the first one) even though the exports were right
        if key in cache:
            cache[key][1] += 1
            o = root.occurrences.addExistingComponent(cache[key][0], adsk.core.Matrix3D.create())
            o.transform2 = m
            return o
        occ = new_comp(key, make(), appearance, material, opacity, m, root)
        occ.transform2 = m
        cache[key] = [occ.component, 1]
        return occ

    def bar_top(bar):
        return (min(t_ for (_, _, t_) in bar['lands']) if 'lands' in bar else bar['field_top']) + RAISE

    def bar_at(x, y):
        return [bb for bb in d['bars'] if bb['x0'] < x < bb['x1'] and bb['y0'] <= y <= bb['y1']][0]

    def set_vis(prefix, on):
        for o_ in root.occurrences:
            if o_.component.name.startswith(prefix):
                o_.isLightBulbOn = on

    F = spec.FLOOR
    MP = d.get('metal_pockets', False)
    RAISE = d.get('bar_raise', 0.0)
    BS = spec.BAR_SCREW
    body_d = d['body']
    W = body_d['wall']
    CW = spec.COVER_WALL
    ceil = d['ceiling']
    report = dict(design=name, parts={}, studs=[], ports=[])

    # ---------------- aluminium bars
    bar_occs = {}
    for bar in d['bars']:
        if 'lands' in bar:
            parts = [box(bar['x0'], y0, F, bar['x1'], y1, top + RAISE) for (y0, y1, top) in bar['lands']]
        else:
            parts = [box(bar['x0'], bar['y0'], F, bar['x1'], bar['y1'], bar['field_top'] + RAISE)]
            parts += [box(bx0, bar['y0'], F, bx1, bar['y1'], bar['block_top']) for (bx0, bx1) in bar['blocks']]
        b = union_all(parts)
        for (x, y, lug, ex, pole, label) in d['studs']:
            if pole != bar['pole']:
                continue
            size = spec.LUGS[lug]['stud']
            bt = spec.BOLT[size]
            top = land_top(d, bar, y)
            bo(b, cylz(x, y, F - 1, top + 1, bt['hole']), 's')
            bo(b, hexz(x, y, F - 0.1, F + bt['k'] + spec.POCKET_EXTRA, bt['s'] + spec.POCKET_CLEAR), 's')
            if MP:   # anti-rotation lug pocket machined into the Al: ring + tongue slot to the edge + barrel relief
                edge = bar['y0'] if ex < 0 else bar['y1']
                zt = top + RAISE + 0.1
                bo(b, cylz(x, y, top, zt, spec.pocket_ring(lug)), 's')
                w = spec.pocket_slot(lug)
                bo(b, box(x - w / 2, y, top, x + w / 2, edge + ex * 1, zt), 's')
                tw = spec.trough_w(lug)
                bo(b, box(x - tw / 2, y + ex * spec.pocket_ring(lug) / 2, spec.trough_floor(lug, top), x + tw / 2, edge + ex * 1, zt), 's')
        for (x, y) in d.get('bar_screws', []):
            if bar['x0'] < x < bar['x1'] and bar['y0'] <= y <= bar['y1']:
                seat = bar_top(bar) - BS['seat_below_top']
                bo(b, cylz(x, y, seat, 100, BS['cbore_d']), 's')
                bo(b, cylz(x, y, F - 0.1, seat + 0.1, BS['hole']), 's')
                bo(b, cylz(x, y, F - 0.1, F + BS['recess_h'], BS['recess_d']), 's')
        for (x, y, lpole, llabel) in d.get('links', []):
            if lpole == bar['pole']:
                bt = spec.BOLT['M8']
                bo(b, cylz(x, y, F - 1, 100, bt['hole']), 's')
                bo(b, hexz(x, y, F - 0.1, F + bt['k'] + spec.POCKET_EXTRA, bt['s'] + spec.POCKET_CLEAR), 's')
        for rl in d.get('reliefs', []):        # clearance for a link fuse body passing over this bar
            if rl['pole'] == bar['pole']:
                bo(b, box(rl['x0'], rl['y0'], rl['z'], rl['x1'], rl['y1'], 100), 's')
        for (x, y) in d['holddowns']:
            if bar['x0'] < x < bar['x1'] and bar['y0'] < y < bar['y1']:
                bo(b, cylz(x, y, F - 0.1, F + 10, 4.2), 's')       # M5 tapped, 10 deep
        for (x, fy, dr, pole, label) in d['ports']:
            if pole != bar['pole']:
                continue
            pp = d['port']
            bo(b, cyl((x, fy - dr * 1.0, pp['zc']), (x, fy + dr * pp['depth'], pp['zc']), pp['bore']), 's')
            for s_off in pp['screws']:
                bo(b, cylz(x, fy + dr * s_off, pp['zc'], bar['block_top'] + 0.1, 8.0), 's')   # M8 tapped (+ coil insert)
        bar_occs[bar['pole']] = new_comp('Bar_%s_Al6061' % bar['pole'], [b], ap_al, m_al)

    # ---------------- printed lug-locator plates (anti-rotation pockets, through to the Al face)
    T = spec.POCKET['T']
    CL = spec.CLAMP

    def clamp_info(cx, cy):
        """bar, Al land top under the tab, nearest bar edge y, direction from bar edge to the clamp"""
        best = None
        for bar in d['bars']:
            if not bar['x0'] < cx < bar['x1']:
                continue
            yc = min(max(cy, bar['y0']), bar['y1'])
            dist = abs(cy - yc)
            if best is None or dist < best[0]:
                best = (dist, bar, yc)
        _, bar, yc = best
        top = land_top(d, bar, yc) if 'lands' in bar else bar['field_top']
        return bar, top, yc, (1 if cy > yc else -1)
    loc_occs = []
    for bar in ([] if MP else d['bars']):
        studs = [s_ for s_ in d['studs'] if s_[4] == bar['pole']]
        if not studs:
            continue
        if 'lands' in bar:
            parts = [box(bar['x0'] + 0.3, y0_, top_, bar['x1'] - 0.3, y1_, top_ + T) for (y0_, y1_, top_) in bar['lands']]
            lands = sorted(bar['lands'])
            for (la, lb) in zip(lands, lands[1:]):       # riser up the step joins the two levels
                lo, hi = min(la[2], lb[2]), max(la[2], lb[2])
                yb = la[1]
                ys = (yb - 1.5, yb) if la[2] < lb[2] else (yb, yb + 1.5)
                parts.append(box(bar['x0'] + 0.3, ys[0], lo - 0.01, bar['x1'] - 0.3, ys[1], hi + T))
        else:
            xs = [bar['x0']]
            for (bx0, bx1) in sorted(bar['blocks']):
                xs += [bx0, bx1]
            xs.append(bar['x1'])
            segs = [(a_, b_) for a_, b_ in zip(xs[0::2], xs[1::2]) if b_ - a_ > 1]
            parts = [box(a_ + 0.3, bar['y0'] + 0.3, bar['field_top'], b_ - 0.3, bar['y1'] - 0.3, bar['field_top'] + T)
                     for (a_, b_) in segs if any(a_ < st[0] < b_ for st in studs)]
        lp = union_all(parts)
        for (cx, cy) in d['clamps']:                      # hold-down tabs reaching out over the printed fingers / ledges
            cbar, ctop, cyedge, cdir = clamp_info(cx, cy)
            if cbar is not bar:
                continue
            ya_, yb_ = sorted((cyedge - cdir * 1.0, cy + cdir * CL['tab_reach']))
            bo(lp, box(cx - CL['tab_w'] / 2, ya_, ctop, cx + CL['tab_w'] / 2, yb_, ctop + T), 'u')
            bo(lp, cylz(cx, cy, ctop - 0.1, ctop + T + 0.1, 4.5), 's')
        for (x, y, lug, ex, pole, label) in studs:
            top = land_top(d, bar, y)
            edge = bar['y0'] if ex < 0 else bar['y1']
            bo(lp, cylz(x, y, top - 0.1, top + T + 0.1, spec.pocket_ring(lug)), 's')
            w = spec.pocket_slot(lug)
            bo(lp, box(x - w / 2, y, top - 0.1, x + w / 2, edge + ex * 2, top + T + 0.1), 's')
        loc_occs.append(new_comp('Locator_%s_printed_ASA' % bar['pole'], [lp], ap_body, m_abs))

    # ---------------- printed base / body
    x0, x1, y0, y1 = body_d['x0'], body_d['x1'], body_d['y0'], body_d['y1']
    body = box(x0, y0, 0, x1, y1, F)
    for fl in d['flanges']:
        f = box(fl['x0'], fl['y0'], 0, fl['x1'], fl['y1'], 6.0)
        bo(body, f, 'u')
    rim = box(x0, y0, F - 0.01, x1, y1, spec.RIM_TOP)
    bo(rim, box(x0 + W, y0 + W, F - 0.1, x1 - W, y1 - W, spec.RIM_TOP + 0.1), 's')
    bo(body, rim, 'u')
    for bar in d['bars']:   # locating frame around each bar, 3 mm tall
        fr = box(bar['x0'] - 1.7, bar['y0'] - 1.7, F - 0.01, bar['x1'] + 1.7, bar['y1'] + 1.7, F + 3)
        bo(fr, box(bar['x0'] - 0.2, bar['y0'] - 0.2, F - 0.1, bar['x1'] + 0.2, bar['y1'] + 0.2, F + 3.1), 's')
        bo(body, fr, 'u')
    # printed boss under each bar screw: rises into the bar-underside recess, takes a BLIND insert, solid floor below
    for (x, y) in d.get('bar_screws', []):
        bo(body, cylz(x, y, F - 0.01, F + BS['recess_h'] - BS['boss_gap'], BS['boss_d']), 'u')
    # barrel troughs beyond the bar edge: set each wire's exit direction, side walls keep the barrels apart
    for bar in ([] if MP else d['bars']):
        for ex in (-1, 1):
            side = [s_ for s_ in d['studs'] if s_[4] == bar['pole'] and s_[3] == ex]
            if not side:
                continue
            top = land_top(d, bar, side[0][1])
            zx0 = max(bar['x0'], min(s_[0] for s_ in side) - 10)
            zx1 = min(bar['x1'], max(s_[0] for s_ in side) + 10)
            ya, yb = (y0 + W - 0.01, bar['y0'] - 0.2) if ex < 0 else (bar['y1'] + 0.2, y1 - W + 0.01)
            blk = box(zx0, ya, F - 0.01, zx1, yb, top)          # finger tops flush with the Al face; locator tabs sit on them
            for (x, y, lug, ex_, pole, label) in side:
                tw = spec.trough_w(lug)
                bo(blk, box(x - tw / 2, ya - 0.1, spec.trough_floor(lug, top), x + tw / 2, yb + 0.1, top + T + 0.1), 's')
            bo(body, blk, 'u')
    # pole barrier wall, full height to the cover ceiling
    bar_d = d['barrier']
    t = bar_d['thk'] / 2
    if bar_d['axis'] == 'x':
        wall = box(bar_d['at'] - t, y0 + CW + 0.3, F - 0.01, bar_d['at'] + t, y1 - CW - 0.3, ceil)
    else:
        wall = box(x0 + CW + 0.3, bar_d['at'] - t, F - 0.01, x1 - CW - 0.3, bar_d['at'] + t, ceil)
    bo(body, wall, 'u')
    yr_in = y1 - CW - 0.3
    for xw in d.get('xwalls', []):        # wall between NEG and the universal bar
        bo(body, box(xw['x'] - xw['thk'] / 2, bar_d['at'], F - 0.01, xw['x'] + xw['thk'] / 2, yr_in, ceil), 'u')
    NZ0, NW = d.get('notch_z0', 18.0), 22.0   # strap notch (rev 3: deep enough for an AMG fuse body), 22 wide
    plug_boxes = {}
    for nt in d.get('notches', []):
        if nt['wall'] == 'main':
            nb = (nt['at'] - NW / 2, bar_d['at'] - t - 0.1, NZ0, nt['at'] + NW / 2, bar_d['at'] + t + 0.1, ceil + 0.1)
            pbx = (nt['at'] - NW / 2 + 0.2, bar_d['at'] - t + 0.2, NZ0 + 0.2, nt['at'] + NW / 2 - 0.2, bar_d['at'] + t - 0.2, ceil - 0.2)
        else:
            xw = d['xwalls'][0]
            nb = (xw['x'] - xw['thk'] / 2 - 0.1, nt['at'] - NW / 2, NZ0, xw['x'] + xw['thk'] / 2 + 0.1, nt['at'] + NW / 2, ceil + 0.1)
            pbx = (xw['x'] - xw['thk'] / 2 + 0.2, nt['at'] - NW / 2 + 0.2, NZ0 + 0.2, xw['x'] + xw['thk'] / 2 - 0.2, nt['at'] + NW / 2 - 0.2, ceil - 0.2)
        bo(body, box(*nb), 's')
        plug_boxes[nt['name']] = pbx
    if d.get('stow'):                     # insulated stow slot for the link strap (strap on edge)
        st_ = d['stow']
        rail = box(st_['x0'], st_['y0'], F - 0.01, st_['x1'], st_['y1'], st_['z1'])
        yc_ = (st_['y0'] + st_['y1']) / 2 - 0.5
        L_ = d['strap']['pitch'] + d['strap']['w'] + 1.0
        bo(rail, box(-L_ / 2 + (st_['x0'] + st_['x1']) / 2, yc_ - st_['slot_w'] / 2, st_['slot_z0'],
                     L_ / 2 + (st_['x0'] + st_['x1']) / 2, yc_ + st_['slot_w'] / 2, st_['z1'] + 0.1), 's')
        bo(body, rail, 'u')
    if d.get('plug_park'):                # park socket for the notch plug that is out
        pk = d['plug_park']
        park = box(pk['x0'], pk['y0'], F - 0.01, pk['x1'], pk['y1'], pk['z1'])
        sx0, sx1, sy0, sy1 = pk['slot']
        bo(park, box(sx0, sy0, pk['slot_z0'], sx1, sy1, pk['z1'] + 0.1), 's')
        bo(body, park, 'u')
    for (bx, by) in d['bosses']:
        bo(body, cylz(bx, by, F - 0.01, ceil, 12.0), 'u')
        bo(body, cylz(bx, by, ceil - 10, ceil + 0.1, 5.6), 's')          # M4 heat-set insert
    for (cx, cy) in d['clamps']:                       # printed pad under each tab + BLIND heat-set insert hole
        cbar, ctop, cyedge, cdir = clamp_info(cx, cy)
        ya_, yb_ = sorted((cyedge + cdir * 0.2, cy + cdir * (CL['tab_reach'] + 0.5)))
        bo(body, box(cx - CL['tab_w'] / 2, ya_, F - 0.01, cx + CL['tab_w'] / 2, yb_, ctop), 'u')
    for (cx, cy) in d['clamps']:
        cbar, ctop, cyedge, cdir = clamp_info(cx, cy)
        bo(body, cylz(cx, cy, ctop - CL['hole_depth'], ctop + 0.1, CL['hole']), 's')
    for (x, y) in d.get('bar_screws', []):
        btop = F + BS['recess_h'] - BS['boss_gap']
        bo(body, cylz(x, y, btop - BS['insert_hole_depth'], btop + 0.1, CL['hole']), 's')
    for fl in d['flanges']:
        for (sx, sy) in fl['slots']:
            bo(body, slot_y(sx, sy, -0.1, 6.1, spec.MOUNT['slot_len'], spec.MOUNT['slot_w']), 's')   # M6 slot along y
    for (hx, hy) in d['holddowns']:
        bo(body, cylz(hx, hy, -0.1, F + 0.1, 5.5), 's')
        bo(body, cyl((hx, hy, -0.01), (hx, hy, 2.45), 10.4, 5.5), 's')  # 90 deg countersink, M5 ISO 10642
    new_comp('Body_printed_ASA', [body], ap_body, m_abs)
    if d.get('strap'):
        sp = d['strap']
        inst = sp['installed']
        lk = {l_[2]: (l_[0], l_[1]) for l_ in d['links']}
        top_l = bar_top(d['bars'][0])
        if inst:
            (ax, ay), (bx_, by_) = lk[inst[0]], lk[inst[1]]
        else:
            st_ = d['stow']
            ax, ay = (st_['x0'] + st_['x1']) / 2 - sp['pitch'] / 2, (st_['y0'] + st_['y1']) / 2 - 0.5
            bx_, by_ = ax + sp['pitch'], ay

        def make_strap():
            r_ = sp['w'] / 2
            sb = union_all([cylz(0, 0, 0, sp['t'], sp['w']), cylz(sp['pitch'], 0, 0, sp['t'], sp['w']),
                            box(0, -r_, 0, sp['pitch'], r_, sp['t'])])
            for xx in (0, sp['pitch']):
                bo(sb, cylz(xx, 0, -0.1, sp['t'] + 0.1, sp['hole']), 's')
            return [sb]
        ang = math.atan2(by_ - ay, bx_ - ax)
        place('LinkStrap_6061_6x20_P50', None, M(ax, ay, top_l, ang), make_strap, ap_al, m_al)
        installed_notch = None
        if inst:
            other = inst[1] if inst[0] == 'UNI' else inst[0]
            installed_notch = 'N' if other == 'NEG' else 'P'
        for nm, pbx in plug_boxes.items():
            if nm == installed_notch:
                # this plug is out: it sits in the park socket
                pk = d['plug_park']
                sx0, sx1, sy0, sy1 = pk['slot']
                h_ = pbx[5] - pbx[2]
                pb_ = box((sx0 + sx1) / 2 - 10.8, (sy0 + sy1) / 2 - 1.8, pk['slot_z0'], (sx0 + sx1) / 2 + 10.8, (sy0 + sy1) / 2 + 1.8, pk['slot_z0'] + h_)
            else:
                pb_ = box(*pbx)
            new_comp('NotchPlug_%s_printed_ASA' % nm, [pb_], ap_body, m_abs)

    # ---------------- cover
    cov = box(x0, y0, spec.RIM_TOP, x1, y1, ceil + spec.COVER_TOP)
    bo(cov, box(x0 + CW, y0 + CW, spec.RIM_TOP - 0.1, x1 - CW, y1 - CW, ceil), 's')
    for (x, y, lug, ex, pole, label) in d['studs']:
        L = spec.LUGS[lug]
        bar = [bb for bb in d['bars'] if bb['pole'] == pole][0]
        zt = land_top(d, bar, y) + L['d4'] + 1
        wy0, wy1 = (y0 - 0.1, y0 + CW + 0.1) if ex < 0 else (y1 - CW - 0.1, y1 + 0.1)
        bo(cov, box(x - L['b'] / 2 - 1, wy0, spec.RIM_TOP - 0.1, x + L['b'] / 2 + 1, wy1, zt), 's')
    for (x, fy, dr, pole, label) in d['ports']:
        pp = d['port']
        wy0, wy1 = (y0 - 0.1, y0 + CW + 0.1) if dr > 0 else (y1 - CW - 0.1, y1 + 0.1)
        bo(cov, box(x - 11, wy0, spec.RIM_TOP - 0.1, x + 11, wy1, pp['zc'] + 11), 's')
    for (bx, by) in d['bosses']:
        bo(cov, cylz(bx, by, ceil - 0.1, ceil + spec.COVER_TOP + 0.1, 4.5), 's')
    ztop = ceil + spec.COVER_TOP
    for (pole, mx, my) in d['marks']:
        bo(cov, box(mx - 6, my - 1.5, ztop - 0.01, mx + 6, my + 1.5, ztop + 1), 'u')
        if pole == 'POS':
            bo(cov, box(mx - 1.5, my - 6, ztop - 0.01, mx + 1.5, my + 6, ztop + 1), 'u')
    cover_occ = new_comp('Cover_printed_ASA', [cov], ap_cover, m_abs)

    # ---------------- etched terminal tags in the cover top (name / gauge + stud or port bore / wire-exit opening)
    cc = cover_occ.component
    cbody = cc.bRepBodies.item(0)
    topf = None
    for f in cbody.faces:
        ok, nrm = f.evaluator.getNormalAtPoint(f.pointOnFace)
        if nrm.z > 0.99 and abs(f.pointOnFace.z - ztop / 10.0) < 1e-4 and (topf is None or f.area > topf.area):
            topf = f
    sk = cc.sketches.add(topf)
    sk.name = 'Etched terminal tags'
    tags = [(s_[0], s_[1], spec.etch_lines(d, stud=s_)) for s_ in d['studs']]
    tags += [(p_[0], p_[1] + p_[2] * 14.0, spec.etch_lines(d, port=p_)) for p_ in d['ports']]
    tags += [(l_[0], l_[1], [l_[3], 'M8 link stud', 'strap 6x20']) for l_ in d.get('links', [])]
    tags += [(e_[0], e_[1], e_[2]) for e_ in d.get('extra_tags', [])]
    eh = spec.ETCH['height']
    for (tx, ty, lines) in tags:
        c0 = sk.modelToSketchSpace(P(tx - 9.5, ty - 2.0 * eh, ztop))
        c1 = sk.modelToSketchSpace(P(tx + 9.5, ty + 2.0 * eh, ztop))
        c0.z = 0
        c1.z = 0
        ti = sk.sketchTexts.createInput2(chr(10).join(lines), eh / 10.0)
        ti.setAsMultiLine(c0, c1, adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                          adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
        ti.fontName = 'Arial'
        st = sk.sketchTexts.add(ti)
        ei = cc.features.extrudeFeatures.createInput(st, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-spec.ETCH['depth'] / 10.0))
        ei.participantBodies = [cbody]
        cc.features.extrudeFeatures.add(ei)
    sk.isVisible = False
    report['etched_tags'] = [dict(x=t[0], y=t[1], text=' / '.join(t[2])) for t in tags]

    # ---------------- stainless hardware
    hw_parent = None                       # hardware sits in the root (see place())

    def make_bolt(size, L):
        def f():
            bt = spec.BOLT[size]
            hb = hexz(0, 0, 0, bt['k'], bt['s'])
            bo(hb, cylz(0, 0, bt['k'] - 0.01, bt['k'] + L, float(size[1:])), 'u')
            return [hb]
        return f

    for (x, y, lug, ex, pole, label) in d['studs']:
        size = spec.LUGS[lug]['stud']
        bar = [bb for bb in d['bars'] if bb['pole'] == pole][0]
        top = land_top(d, bar, y)
        L = spec.bolt_len(size, top - F)
        place('Bolt_ISO4017_%sx%d_A2' % (size, L), hw_parent, M(x, y, F), make_bolt(size, L), ap_ss, m_ss)
        report['studs'].append(dict(x=x, y=y, lug=lug, lug_src=spec.LUGS[lug]['src'], size=size, bolt='ISO 4017 %sx%d A2-70' % (size, L),
                                    land_top=top, stud_top=F + spec.BOLT[size]['k'] + L, exit='front (-y)' if ex < 0 else 'rear (+y)',
                                    pole=pole, label=label))
    if d['ports']:
        pp = d['port']

        def make_ss():
            ss = cylz(0, 0, 0, pp['screw_len'], 8.0)
            bo(ss, hexz(0, 0, pp['screw_len'] - 4, pp['screw_len'] + 0.1, 4.0), 's')   # 4 mm hex socket
            return [ss]
        for (x, fy, dr, pole, label) in d['ports']:
            bar = [bb for bb in d['bars'] if bb['pole'] == pole][0]
            for s_off in pp['screws']:
                place('SetScrew_ISO4029_M8x%d_A2' % pp['screw_len'], hw_parent, M(x, fy + dr * s_off, bar['block_top'] - pp['screw_len']), make_ss, ap_ss, m_ss)
            report['ports'].append(dict(x=x, face_y=fy, pole=pole, label=label, bore=pp['bore'], depth=pp['depth'],
                                        exit='front (-y)' if dr > 0 else 'rear (+y)'))
    ap_brass = lib_item('Fusion Appearance Library', 'app', 'Brass - Polished') or ap_yel

    def make_clamp():
        sc = cylz(0, 0, -CL['len'], 0.01, 4.0)
        bo(sc, cylz(0, 0, 0, CL['head_k'], CL['head_d']), 'u')
        return [sc]

    def make_insert():
        i_ = cylz(0, 0, -CL['insert_len'], 0, CL['hole'])
        bo(i_, cylz(0, 0, -CL['insert_len'] - 0.1, 0.1, 4.0), 's')
        return [i_]
    for (x, y, lpole, llabel) in d.get('links', []):
        bar = bar_at(x, y)
        L = spec.bolt_len('M8', bar_top(bar) - F)
        place('Bolt_ISO4017_M8x%d_A2' % L, hw_parent, M(x, y, F), make_bolt('M8', L), ap_ss, m_ss)
        report.setdefault('links', []).append(dict(x=x, y=y, pole=lpole, label=llabel, bolt='ISO 4017 M8x%d A2-70' % L))
    for (x, y) in d.get('bar_screws', []):
        bar = bar_at(x, y)
        seat = bar_top(bar) - BS['seat_below_top']
        place('BarScrew_ISO7380_M4x10_A2', hw_parent, M(x, y, seat), make_clamp, ap_ss, m_ss)
        place('HeatSetInsert_M4x8.1_brass', hw_parent, M(x, y, F + BS['recess_h'] - BS['boss_gap']), make_insert, ap_brass, None)
    for (cx, cy) in d['clamps']:
        cbar, ctop, cyedge, cdir = clamp_info(cx, cy)
        place('ClampScrew_ISO7380_M4x10_A2', hw_parent, M(cx, cy, ctop + T), make_clamp, ap_ss, m_ss)
        place('HeatSetInsert_M4x8.1_brass', hw_parent, M(cx, cy, ctop), make_insert, ap_brass, None)
    MT = spec.MOUNT

    def make_mount():
        w_ = cylz(0, 0, 0, MT['washer_t'], MT['washer_od'])
        bo(w_, cylz(0, 0, MT['washer_t'] - 0.01, MT['washer_t'] + MT['head_k'], MT['head_d']), 'u')
        bo(w_, cylz(0, 0, -16.0, 0.01, 6.0), 'u')
        return [w_]
    for fl in d['flanges']:
        for (sx, sy) in fl['slots']:
            # worst case: screw at the slot end nearest the middle of the part
            sy_in = sy - (MT['slot_len'] - MT['slot_w']) / 2 * (1 if sy > 0 else -1)
            place('REF_MountScrew_ISO7380_M6x16_A2', hw_parent, M(sx, sy_in, 6.0), make_mount, ap_ss, m_ss)
    hw = {k: v for k, v in cache.items() if k.startswith(('Bolt_', 'SetScrew_', 'ClampScrew_', 'BarScrew_', 'HeatSetInsert_', 'REF_Mount'))}

    # ---------------- keep-out envelopes (reference only, not parts)
    ko_parent = None
    for (x, y, lug, ex, pole, label) in d['studs']:
        L = spec.LUGS[lug]
        bar = [bb for bb in d['bars'] if bb['pole'] == pole][0]
        e = abs((bar['y0'] if ex < 0 else bar['y1']) - y)        # stud to bar edge, along the exit

        def make_ko(L=L, e=e):
            k = cylz(0, 0, 0, L['d4'], L['b'])
            bo(k, box(-L['b'] / 2, -e, 0, L['b'] / 2, 0, L['d4']), 'u')
            bo(k, box(-L['d4'] / 2, -(L['l'] - L['b'] / 2), -L['d4'] / 2, L['d4'] / 2, -e + 0.01, L['d4'] / 2), 'u')
            bo(k, cylz(0, 0, -0.1, L['d4'] + 0.1, L['d2']), 's')
            return [k]
        place('KEEPOUT_%s_lug_Klauke_%s_e%.0f' % (pole, lug, e), ko_parent, M(x, y, land_top(d, bar, y), 0 if ex < 0 else math.pi), make_ko,
              {'POS': ap_red, 'NEG': ap_blue}.get(pole, lib_item('Fusion Appearance Library', 'app', 'Plastic - Matte (Green)')), None, 0.45)
    if d['ports']:
        pp = d['port']
        for (x, fy, dr, pole, label) in d['ports']:
            place('KEEPOUT_ferrule_Weidmueller_H50-25', ko_parent, M(x, fy, pp['zc'], 0 if dr > 0 else math.pi),
                  lambda: [cyl((0, 0, 0), (0, spec.FERRULE['length'], 0), spec.FERRULE['collar'])], ap_yel, None, 0.6)

    # ---------------- mass / size report
    def props(c):
        pr = c.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        return dict(mass_g=round(pr.mass * 1000, 1), volume_cm3=round(pr.volume, 2))

    for occ in root.occurrences:
        c = occ.component
        if c.name.startswith(('Bar_', 'Body_', 'Cover_', 'Locator_', 'NotchPlug_', 'LinkStrap_')):
            report['parts'][c.name] = props(c)
    for k, (c, n) in hw.items():
        report['parts'][k] = dict(qty=n, **props(c))
    bb = None
    for o in root.allOccurrences:          # the part itself only (no reference mount screws / keep-outs)
        if o.component.name.startswith(('Bar_', 'Body_', 'Cover_', 'Locator_', 'Bolt_', 'NotchPlug_', 'LinkStrap_')):
            if bb is None:
                bb = o.boundingBox.copy()
            else:
                bb.combine(o.boundingBox)
    report['overall_mm'] = [round((bb.maxPoint.x - bb.minPoint.x) * 10, 1), round((bb.maxPoint.y - bb.minPoint.y) * 10, 1),
                            round((bb.maxPoint.z - bb.minPoint.z) * 10, 1)]

    # ---------------- exports
    em = design.exportManager
    set_vis('KEEPOUT_', False)
    exported = []

    def step(fn, geom):
        p = os.path.join(out_dir, fn)
        em.execute(em.createSTEPExportOptions(p, geom))
        exported.append(fn)

    def stl(fn, geom):
        p = os.path.join(out_dir, fn)
        o = em.createSTLExportOptions(geom, p)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(o)
        exported.append(fn)

    for occ in root.occurrences:
        c = occ.component
        if c.name.startswith(('Bar_', 'Body_', 'Cover_', 'Locator_', 'NotchPlug_', 'LinkStrap_')):
            step('%s_%s.step' % (name, c.name), c)
        if c.name.endswith('_ASA'):
            stl('%s_%s.stl' % (name, c.name), c)
    for k, (c, n) in hw.items():
        step('%s_%s.step' % (name, k), c)
    step('%s_ASSEMBLY.step' % name, root)
    em.execute(em.createFusionArchiveExportOptions(os.path.join(out_dir, 'ST185_busbar_%s.f3d' % name)))
    exported.append('ST185_busbar_%s.f3d' % name)
    report['exported'] = exported

    # ---------------- images
    vp = app.activeViewport

    def shot(fn, orient):
        cam = vp.camera
        cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()
        vp.saveAsImageFile(os.path.join(out_dir, fn), 1600, 1000)

    VO = adsk.core.ViewOrientations
    shot('%s_render_iso_cover.png' % name, VO.IsoTopRightViewOrientation)
    cover_occ.isLightBulbOn = False
    shot('%s_render_pockets.png' % name, VO.IsoTopRightViewOrientation)
    set_vis('KEEPOUT_', True)
    shot('%s_render_iso_open.png' % name, VO.IsoTopRightViewOrientation)
    shot('%s_render_top_open.png' % name, VO.TopViewOrientation)
    cover_occ.isLightBulbOn = True

    # ---------------- electrical isolation check: conductors vs mounting face / mounting screws (straight line, cover off)
    mm = app.measureManager
    conductors, mounts, plastics = [], [], []
    for o in root.allOccurrences:
        n = o.component.name
        for b in o.bRepBodies:
            if n.startswith(('Bar_', 'Bolt_', 'SetScrew_', 'BarScrew_', 'LinkStrap_')) or (MP and n.startswith('HeatSetInsert_')):
                conductors.append((n, b))
            elif n.startswith('REF_Mount'):
                mounts.append((n, b))
            elif n.startswith('Body_'):
                plastics.append(b)
    pb = plastics[0]
    bottom = max([f for f in pb.faces if abs(f.pointOnFace.z) < 1e-6 and f.evaluator.getNormalAtPoint(f.pointOnFace)[1].z < -0.99],
                 key=lambda f: f.area)
    iso = dict(to_mount_face=[], to_mount_screw=[])
    for (n, b) in conductors:
        iso['to_mount_face'].append((n, round(mm.measureMinimumDistance(b, bottom).value * 10, 2)))
        iso['to_mount_screw'].append((n, round(min(mm.measureMinimumDistance(b, mb).value for _, mb in mounts) * 10, 2)))
    iso['min_to_mount_face'] = min(v for _, v in iso['to_mount_face'])
    iso['min_to_mount_screw'] = min(v for _, v in iso['to_mount_screw'])
    iso['worst_face'] = min(iso['to_mount_face'], key=lambda t: t[1])
    iso['worst_screw'] = min(iso['to_mount_screw'], key=lambda t: t[1])
    del iso['to_mount_face'], iso['to_mount_screw']
    report['isolation'] = iso

    # ---------------- section renders (temporary cut copies, removed before save)
    def section(fn, axis, at, orient):
        tops = [o for o in root.occurrences]
        vis = {o.entityToken: o.isLightBulbOn for o in tops}
        sec = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sec.component.name = 'SECTION_tmp'
        big = 1000.0
        keep = (box(-big, at, -big, big, big, big) if axis == 'y' else box(at, -big, -big, big, big, big))
        for o in root.allOccurrences:
            n = o.component.name
            if n.startswith(('KEEPOUT_', 'SECTION_')) or o.component.bRepBodies.count == 0:
                continue
            for b in o.bRepBodies:
                c = tb.copy(b)
                if not tb.booleanOperation(c, tb.copy(keep), BT.IntersectionBooleanType) or c.lumps.count == 0:
                    continue
                nb = sec.component.bRepBodies.add(c)
                nb.appearance = b.appearance
        for o in tops:
            if o is not sec:
                o.isLightBulbOn = False
        sec.isLightBulbOn = True
        shot(fn, orient)
        sec.deleteMe()
        for o in root.occurrences:
            if o.entityToken in vis:
                o.isLightBulbOn = vis[o.entityToken]
    if d.get('sections'):
        for i_, (ax_, at_, view_, cap_) in enumerate(d['sections']):
            fn_ = ['%s_section_mount.png', '%s_section_clamp.png', '%s_section_link.png'][i_] % name
            section(fn_, ax_, at_, VO.FrontViewOrientation if view_ == 'front' else VO.LeftViewOrientation)
    else:
        section('%s_section_mount.png' % name, 'y', d['section_y'], VO.FrontViewOrientation)
        section('%s_section_clamp.png' % name, 'x', d['section_x'], VO.LeftViewOrientation)
    set_vis('KEEPOUT_', False)

    if doc.isSaved:
        doc.save('rebuild %s (Claude Code)' % name)
    else:
        proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
        doc.saveAs(doc_name, proj.rootFolder, 'ST185 glove-box +/- bus bar, design %s (Claude Code 2026-10-13)' % name, '')
    with open(os.path.join(out_dir, '%s_report.json' % name), 'w') as f:
        json.dump(report, f, indent=1)
    return report
