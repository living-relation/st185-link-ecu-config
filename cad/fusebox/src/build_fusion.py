"""Build the ST185 fuse + relay boxes (rev 6 - rev 5 + Dan's parts answers C1 / C3 / C4 / B5 (DECISIONS R85); rev 5: base + snap-on cover + snap-on belly pan; LOGIC box, POWER box, battery
relay block) in the existing Fusion fusebox document, export every part, render (closed, open, EMPTY, underneath with and
without the belly pans, every cable to the box edge, exploded and step-by-step install views), check clearance,
interference and every cable bend, and record the screen position of every numbered callout for summary_html.py.
Run inside Fusion (Fusion MCP script runner):  build(out_dir)
Same toolkit as rev 3 / 4 (TemporaryBRepManager bodies, one component per part, every occurrence placed in the root with
an identity transform; bodies are moved with tb.transform before they are added). Rounded shells are built from boxes,
cylinders and tori (no fillet features); the angular legs are boxes cut by tilted half-spaces. Labels are sketch text cut
into the cover top (the only features used).
R74: never makes a new document - it opens the existing fusebox document (rev 5, renamed rev 6) and saves a new version.
Claude Code, 2026-10-14.
"""
import adsk.core, adsk.fusion, math, os, sys, json, importlib

SRC = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'C:\projects\active\st185-link-ecu-config\cad\fusebox\src'
if SRC not in sys.path:
    sys.path.insert(0, SRC)
import spec as S
importlib.reload(S)

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
BT = adsk.fusion.BooleanTypes
OPS = {'u': BT.UnionBooleanType, 's': BT.DifferenceBooleanType, 'i': BT.IntersectionBooleanType}
DOC = 'ST185_fusebox_rev6'                                                   # rev 6: Dan's parts answers on rev 5
DOC_OLD = ('ST185_fusebox_rev5', 'ST185_fusebox_rev4', 'ST185_fusebox_rev3', 'ST185_fusebox_rev2')  # the same Fusion document before the renames (R74)
DOC7 = 'ST185_fusebox_rev7'   # rev 7 (E2 = A, bus bar POS bar = the AMI bar): its own document, saved-as from rev 6 (2 of 10 Fusion slots in use)
REV = [6]                     # build(rev=7) builds rev 7; rev 6 output is unchanged


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def V(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


def bo(target, tool, op):
    if not tb.booleanOperation(target, tool, OPS[op]):
        raise RuntimeError('boolean %s failed' % op)
    return target


def box(x0, y0, z0, x1, y1, z1):
    obb = adsk.core.OrientedBoundingBox3D.create(
        P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), V(1, 0, 0), V(0, 1, 0),
        abs(x1 - x0) / 10.0, abs(y1 - y0) / 10.0, abs(z1 - z0) / 10.0)
    return tb.createBox(obb)


def cbox(cx, cy, z0, z1, lx, ly):
    return box(cx - lx / 2, cy - ly / 2, z0, cx + lx / 2, cy + ly / 2, z1)


def rbox(cx, cy, z0, z1, Lx, Wy, ang):
    a = math.radians(ang)
    obb = adsk.core.OrientedBoundingBox3D.create(
        P(cx, cy, (z0 + z1) / 2), V(math.cos(a), math.sin(a), 0), V(-math.sin(a), math.cos(a), 0),
        Lx / 10.0, Wy / 10.0, (z1 - z0) / 10.0)
    return tb.createBox(obb)


def cyl(p0, p1, d):
    return tb.createCylinderOrCone(P(*p0), d / 20.0, P(*p1), d / 20.0)


def cylz(x, y, z0, z1, d):
    return cyl((x, y, z0), (x, y, z1), d)


def hexz(x, y, z0, z1, af):
    h = rbox(x, y, z0, z1, af * 2, af, 0)
    for ang in (60, 120):
        bo(h, rbox(x, y, z0, z1, af * 2, af, ang), 'i')
    return h


def hex_x(x0, x1, y, z, af):
    """Hex prism along x (a bolt head lying on its side), across flats af."""
    h = None
    for ang in (0, 60, 120):
        a = math.radians(ang)
        obb = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, y, z), V(1, 0, 0), V(0, math.cos(a), math.sin(a)),
                                                     abs(x1 - x0) / 10.0, af * 2 / 10.0, af / 10.0)
        b = tb.createBox(obb)
        h = b if h is None else bo(h, b, 'i')
    return h


def slot_x(x0, x1, cy, z0, z1, w):
    s = box(x0, cy - w / 2, z0, x1, cy + w / 2, z1)
    bo(s, cylz(x0, cy, z0, z1, w), 'u')
    bo(s, cylz(x1, cy, z0, z1, w), 'u')
    return s


def slot_y(cx, y0, y1, z0, z1, w):
    s = box(cx - w / 2, y0, z0, cx + w / 2, y1, z1)
    bo(s, cylz(cx, y0, z0, z1, w), 'u')
    bo(s, cylz(cx, y1, z0, z1, w), 'u')
    return s


def union_all(bodies):
    b0 = bodies[0]
    for b in bodies[1:]:
        bo(b0, b, 'u')
    return b0


def sub_all(target, tools):
    for t in tools:
        bo(target, t, 's')
    return target


def move(bodies, dx, dy):
    m = adsk.core.Matrix3D.create()
    m.translation = V(dx / 10.0, dy / 10.0, 0)
    for b in bodies:
        tb.transform(b, m)
    return bodies


def torus(cx, cy, cz, axis, Rm, rm):
    """Torus at (cx, cy, cz). Built at the origin and moved: createTorus ignores its centre point when the axis is z
    (seen in this Fusion build, 2026-10-14)."""
    t = tb.createTorus(adsk.core.Point3D.create(0, 0, 0), axis, Rm / 10.0, rm / 10.0)
    m = adsk.core.Matrix3D.create()
    m.translation = V(cx / 10.0, cy / 10.0, cz / 10.0)
    tb.transform(t, m)
    return t


def rrect(x0, y0, x1, y1, z0, z1, R):
    """Prism with a rounded-rectangle plan (corner radius R)."""
    R = min(R, (x1 - x0) / 2 - 0.05, (y1 - y0) / 2 - 0.05)
    parts = [box(x0 + R, y0, z0, x1 - R, y1, z1), box(x0, y0 + R, z0, x1, y1 - R, z1)]
    for cx in (x0 + R, x1 - R):
        for cy in (y0 + R, y1 - R):
            parts.append(cylz(cx, cy, z0, z1, 2 * R))
    return union_all(parts)


def rtop(x0, y0, x1, y1, z0, z1, R, r):
    """Rounded-rectangle prism whose top edges are rounded with radius r (R > 2 r): boxes + cylinders + tori."""
    zc = z1 - r
    parts = [rrect(x0, y0, x1, y1, z0, zc, R), rrect(x0 + r, y0 + r, x1 - r, y1 - r, zc - 0.01, z1, R - r),
             cyl((x0 + R, y0 + r, zc), (x1 - R, y0 + r, zc), 2 * r), cyl((x0 + R, y1 - r, zc), (x1 - R, y1 - r, zc), 2 * r),
             cyl((x0 + r, y0 + R, zc), (x0 + r, y1 - R, zc), 2 * r), cyl((x1 - r, y0 + R, zc), (x1 - r, y1 - R, zc), 2 * r)]
    for cx in (x0 + R, x1 - R):
        for cy in (y0 + R, y1 - R):
            parts.append(torus(cx, cy, zc, V(0, 0, 1), R - r, r))
    return union_all(parts)


def half_cut(body, p, n):
    """Remove everything on the +n side of the plane through p (mm) with normal n (unit, any direction)."""
    nl = math.sqrt(sum(c * c for c in n))
    n = tuple(c / nl for c in n)
    ref = (0.0, 0.0, 1.0) if abs(n[2]) < 0.9 else (1.0, 0.0, 0.0)
    d1 = (n[1] * ref[2] - n[2] * ref[1], n[2] * ref[0] - n[0] * ref[2], n[0] * ref[1] - n[1] * ref[0])
    dl = math.sqrt(sum(c * c for c in d1))
    d1 = tuple(c / dl for c in d1)
    c = (p[0] + n[0] * 100.0, p[1] + n[1] * 100.0, p[2] + n[2] * 100.0)
    obb = adsk.core.OrientedBoundingBox3D.create(P(*c), V(*d1), V(*n), 100.0, 20.0, 100.0)
    return bo(body, tb.createBox(obb), 's')


def ring_lug(x, y, z, b, hole, t, d4, along, length, barrel=9.0):
    """Tubular lug lying flat, palm underside at z, round palm at (x, y), barrel (d4) along +-x or +-y.
    Returns (body, barrel end point at the barrel centre line)."""
    sgn, ax = along
    zc = z + d4 / 2
    if ax == 'x':
        x1 = x + sgn * (length - barrel)
        lug = box(min(x, x1), y - b / 2, z, max(x, x1), y + b / 2, z + t)
        p0, p1 = (x1, y, zc), (x + sgn * length, y, zc)
    else:
        y1 = y + sgn * (length - barrel)
        lug = box(x - b / 2, min(y, y1), z, x + b / 2, max(y, y1), z + t)
        p0, p1 = (x, y1, zc), (x, y + sgn * length, zc)
    bo(lug, cylz(x, y, z, z + t, b), 'u')
    bo(lug, cylz(x, y, z - 1, z + t + 1, hole), 's')
    bo(lug, cyl(p0, p1, d4), 'u')
    return lug, p1


def quarter_bend(cx, cy, cz, Rc, d, quad):
    """Quarter of a torus about the y axis (centre cx, cy, cz; centre-line radius Rc; tube dia d), bend in the x-z plane.
    quad = (sx, sz): which quadrant of the x-z plane, e.g. (-1, -1) = toward -x and -z from the centre."""
    t = torus(cx, cy, cz, V(0, 1, 0), Rc, d / 2)
    sx, sz = quad
    q = box(cx, cy - d, cz, cx + sx * (Rc + d), cy + d, cz + sz * (Rc + d))
    return bo(t, q, 'i')


def quarter_bend_yz(cx, cy, cz, Rc, d, quad):
    """Same, bend in the y-z plane (torus about the x axis). quad = (sy, sz)."""
    t = torus(cx, cy, cz, V(1, 0, 0), Rc, d / 2)
    sy, sz = quad
    q = box(cx - d, cy, cz, cx + d, cy + sy * (Rc + d), cz + sz * (Rc + d))
    return bo(t, q, 'i')


def bundle_d(ods):
    """Bundle diameter for wires of the given ODs (one wire: its OD; more: 1.2 x the root of the summed squares)."""
    return ods[0] if len(ods) == 1 else 1.2 * math.sqrt(sum(o * o for o in ods))


def doc_name():
    return DOC7 if REV[0] == 7 else DOC


def open_doc():
    names = ((DOC7,) if REV[0] == 7 else ()) + (DOC,) + DOC_OLD
    open_ = {app.documents.item(i).name.split(' v')[0]: app.documents.item(i) for i in range(app.documents.count) if app.documents.item(i).isSaved}
    for n in names:
        if n in open_:
            return open_[n]
    proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
    files = {f.name: f for f in proj.rootFolder.dataFiles}
    for n in names:                    # rev 7: its own document if saved already, else rev 6 (saved-as rev 7 at the end)
        if n in files:
            return app.documents.open(files[n], True)
    raise RuntimeError('fusebox document not found - R74: do not create a new one')


def build(out_dir, save=True, renders=True, rev=6):
    REV[0] = rev
    R7 = S.REV7 if rev == 7 else None
    DIM = {'D': S.D, 'snaps_rear': None}   # rev 7: the POWER box is deeper; the shared shell / pan / cover helpers read DIM
    os.makedirs(out_dir, exist_ok=True)
    doc = open_doc()
    doc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    for i in range(root.occurrences.count - 1, -1, -1):
        root.occurrences.item(i).deleteMe()
    report = {'bends': [], 'labels': {}, 'lanes': {}, 'callouts': {}, 'standoffs': {}, 'terminal_holes': {}, 'terminal_slots': {}, 'guide_walls': {}, 'feature_support': {}}
    PLAN7 = None
    if rev == 7:   # J2 = B (R94): the wire plan (wiring_sim.py) names the terminal and wire in every cavity
        PLAN7 = json.load(open(os.path.join(os.path.dirname(SRC), 'rev7', 'wiring_plan.json'), encoding='utf-8'))

    def backing(foot, z, support):
        """Share (0..1) of a feature's top face (footprint body foot, any z) that has solid printed material right above it (z .. z + 1)
        in the union of the support bodies - R101: a rib or saddle is only supported where this is 1."""
        slab = tb.copy(foot)
        bb = slab.boundingBox
        m = adsk.core.Matrix3D.create()
        m.translation = V(0, 0, z / 10.0 - bb.minPoint.z)
        tb.transform(slab, m)
        bo(slab, box(bb.minPoint.x * 10 - 1, bb.minPoint.y * 10 - 1, z, bb.maxPoint.x * 10 + 1, bb.maxPoint.y * 10 + 1, z + 1.0), 'i')
        v0 = slab.volume
        if v0 <= 0:
            return 1.0
        hit = 0.0
        for sp in support:
            t_ = tb.copy(slab)
            try:
                bo(t_, tb.copy(sp), 'i')
                hit += t_.volume
            except RuntimeError:   # no overlap
                pass
        return min(1.0, hit / v0)

    def support_union(parts):
        """One body of copies of the given parts (the parts themselves stay as they are)."""
        u = tb.copy(parts[0])
        for p_ in parts[1:]:
            bo(u, tb.copy(p_), 'u')
        return u

    def crimp_holes(box_name, z_d, z_t, support=None, plate_b=None):
        """J2 = B (Dan 2026-10-14, R94), sized from the terminal (R120, Dan 2026-10-15: "the holes ... should be made based on the widest
        part being inserted which would be the contact terminal itself"): every terminal hole in the base is a slot the crimped terminal
        goes up through - max(head, crimped barrel) each way + CLR per side, the long side along the blade (S.slot, TE drawing data in
        S.TERM) - from under the deck up to the receptacle seat (receptacle top HOLE['top_gap'] under the deck top). Two slots with less
        than min_wall between them join into one (Dan: "join the two slots into one"), bridged across the gap between them. Short guide walls hang under the deck between neighbouring holes (Dan:
        "short separators or walls ... to help guide wires straight out"); the bores are cut through them, so a wall never narrows a
        hole. 87a cavities get a bore only when a harness wire lands there (none today: next to 85 / 86 it would leave 0.4 mm).
        R101 (Dan 2026-10-15: "the little ribs ... are just floating. fill in the gaps between relay positions under the ribs"; then "i
        like them as they are. just fix the floating pieces i mentioned"): a FLOATING guide wall (less than S.FLOAT_BACKING of its top
        face on a cavity tower - it crosses the gap between two relay positions) gets a web of its own footprint from its top up into
        the deck plate. Every other wall is left exactly as it was.
        Returns (cuts, guide walls + webs) and records every hole for check_terminal_holes.py."""
        if not PLAN7:
            return [], []
        HO, G = S.HOLE, S.GUIDE
        hs = [dict(c) for c in PLAN7['cavities'] if c['box'] == box_name and c['slot']
              and not (c['kind'].endswith('87a') and c['source'] != 'harness')]
        for h in hs:
            T = S.TERM[h['part']]
            h['sx'], h['sy'] = h['slot']
            h['z1'] = round(z_t - HO['top_gap'], 2)
            h['est'] = T['t'] is None or h['part'] in S.HEAD_EST

        def gap_(a, b):   # printed wall between two axis-aligned slots; negative = overlap
            gx = abs(a['x'] - b['x']) - (a['sx'] + b['sx']) / 2
            gy = abs(a['y'] - b['y']) - (a['sy'] + b['sy']) / 2
            return math.hypot(gx, gy) if gx > 0 and gy > 0 else max(gx, gy)

        def span_(a, b, k, s_):   # bridge interval on one axis: the gap between the two slots, or their overlap
            lo = max(a[k] - a[s_] / 2, b[k] - b[s_] / 2)
            hi = min(a[k] + a[s_] / 2, b[k] + b[s_] / 2)
            return min(lo, hi), max(lo, hi)
        par = list(range(len(hs)))

        def root_(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        edges, near_ = [], []
        for i in range(len(hs)):
            for j in range(i + 1, len(hs)):
                a, b = hs[i], hs[j]
                d = math.hypot(a['x'] - b['x'], a['y'] - b['y'])
                if gap_(a, b) < HO['min_wall']:
                    edges.append((i, j, d))
                    par[root_(i)] = root_(j)
                elif d < G['reach']:
                    near_.append((i, j, d))
        z0 = z_d - G['h'] - 1.0
        cuts = [cbox(h['x'], h['y'], z0, h['z1'], h['sx'], h['sy']) for h in hs]
        for (i, j, d) in edges:
            a, b = hs[i], hs[j]
            if gap_(a, b) > 0:
                (x0_, x1_), (y0_, y1_) = span_(a, b, 'x', 'sx'), span_(a, b, 'y', 'sy')
                cuts.append(box(x0_, y0_, z0, x1_, y1_, min(a['z1'], b['z1'])))
        gid = {}
        for i, h in enumerate(hs):
            h['group'] = gid.setdefault(root_(i), len(gid))
        fins, fin_d = [], []
        for (i, j, d) in near_:
            a, b = hs[i], hs[j]
            if a['group'] == b['group']:
                continue
            ang = math.degrees(math.atan2(b['y'] - a['y'], b['x'] - a['x'])) + 90.0
            fd = ((a['x'] + b['x']) / 2, (a['y'] + b['y']) / 2, max(a['sx'], a['sy'], b['sx'], b['sy']) + 2.0, G['t'], ang)
            fin_d.append(fd)
            fins.append(rbox(fd[0], fd[1], z_d - G['h'], z_d + 0.01, fd[2], fd[3], fd[4]))
        webs, sup = [], []
        if support is not None and fins:
            U = [support_union(support)]
            for (f_, fd) in zip(fins, fin_d):
                c0 = backing(f_, z_d + 0.01, U)
                if c0 < S.FLOAT_BACKING:   # floating: the wall bridges a gap between two towers - web of its own footprint up into the deck plate
                    webs.append(rbox(fd[0], fd[1], z_d - 0.01, plate_b + 0.01, fd[2], fd[3], fd[4]))
                sup.append(dict(kind='guide wall', at=[round(fd[0], 1), round(fd[1], 1)], before=round(c0, 3), web=c0 < S.FLOAT_BACKING))
            U2 = [support_union(support + webs)] if webs else U
            for s_, f_ in zip(sup, fins):
                s_['after'] = round(backing(f_, z_d + 0.01, U2), 3)
        report['feature_support'].setdefault(box_name, []).extend(sup)
        sh_ = S.PLACE[box_name]
        report['terminal_holes'][box_name] = [dict(cav=h['cav'], kind=h['kind'], x=h['x'], y=h['y'], sx=h['sx'], sy=h['sy'], z0=round(z_d, 2), z1=h['z1'],
                                                   group=h['group'], part=h['part'], wire_od=h['wire_od'], source=h['source'], est=h['est'])
                                              for h in hs]
        report['terminal_slots'][box_name] = [sorted(h['cav'] for h in hs if h['group'] == g) for g in range(len(gid))
                                              if sum(1 for h in hs if h['group'] == g) > 1]
        report['guide_walls'][box_name] = dict(n=len(fins), t=G['t'], h=G['h'], world_shift=sh_, webs=len(webs))
        return cuts, fins + webs

    alib = app.materialLibraries.itemByName('Fusion Appearance Library')
    mlib = app.materialLibraries.itemByName('Fusion Material Library')

    def ap(name):
        return alib.appearances.itemByName(name)

    def tint(base, name, rgb):
        a = design.appearances.itemByName(name)
        if a is None:
            a = design.appearances.addByCopy(ap(base), name)
            for i in range(a.appearanceProperties.count):
                p = a.appearanceProperties.item(i)
                if isinstance(p, adsk.core.ColorProperty) and p.name in ('Color', 'Colour'):
                    p.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    break
        return a

    AP = {
        'al': ap('Aluminum - Satin'), 'black': ap('Plastic - Matte (Black)'), 'brass': ap('Brass - Matte'), 'cu': ap('Copper - Raw'),
        'wire': ap('Plastic - Glossy (Red)'),
        'orange': tint('Plastic - Glossy (Red)', 'AMI orange', (240, 120, 20)),
        'ltgreen': tint('Plastic - Glossy (Green)', 'AMI lt green', (130, 220, 120)),
        'red': ap('Plastic - Glossy (Red)'), 'yellow': ap('Plastic - Glossy (Yellow)'),
        'spare': tint('Plastic - Matte (Gray)', 'Spare position', (200, 200, 200)),
        'pa12': tint('Plastic - Matte (Gray)', 'PA12 MJF grey', (95, 98, 102)),
        'pa12_lt': tint('Plastic - Matte (Gray)', 'PA12 MJF light', (150, 154, 158)),
        'pa12_pan': tint('Plastic - Matte (Gray)', 'PA12 MJF pan', (120, 124, 128)),
        'tin': tint('Aluminum - Satin', 'Tinned copper', (200, 200, 190)),
        'harness': tint('Plastic - Glossy (Red)', 'Harness wire', (230, 200, 60)),
    }
    MINI_AP = {2: tint('Plastic - Glossy (Grey)', 'ATM 2A grey', (150, 150, 150)), 5: tint('Plastic - Glossy (Red)', 'ATM 5A tan', (205, 170, 120)),
               7.5: tint('Plastic - Glossy (Red)', 'ATM 7.5A brown', (120, 70, 40)), 10: ap('Plastic - Glossy (Red)'),
               15: ap('Plastic - Glossy (Blue)'), 20: ap('Plastic - Glossy (Yellow)')}
    MAT = {'pa': mlib.materials.itemByName('Nylon 6/6'),   # PA12 stand-in
           'cu': mlib.materials.itemByName('Copper'), 'brass': mlib.materials.itemByName('Brass'),
           'ss': mlib.materials.itemByName('Stainless Steel AISI 304'), 'abs': mlib.materials.itemByName('ABS Plastic')}
    BM = S.METAL[S.BAR_METAL]
    occs = {}

    def comp(cname, bodies, appearance=None, material=None, shift=(0.0, 0.0)):
        bl = bodies if isinstance(bodies, list) else [bodies]
        bl = [b for b in bl if b is not None]
        if not bl:
            return None
        move(bl, *shift)
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c = occ.component
        c.name = cname
        for b in bl:
            bb = c.bRepBodies.add(b)
            bb.name = cname
            if appearance is not None:
                bb.appearance = appearance
        if material is not None:
            c.material = material
        occs[cname] = occ
        return occ

    def etch(occ, labels, z_top, shift):
        """Cut every label 0.6 deep into the cover top. labels = [(text, x, y, h)] in the box's local frame."""
        c = occ.component
        body = c.bRepBodies.item(0)
        pin = c.constructionPlanes.createInput()
        pin.setByOffset(c.xYConstructionPlane, adsk.core.ValueInput.createByReal(z_top / 10.0))
        pl = c.constructionPlanes.add(pin)
        sk = c.sketches.add(pl)
        coll = adsk.core.ObjectCollection.create()
        for (txt, x, y, h) in labels:
            wx, wy = x + shift[0], y + shift[1]
            ti = sk.sketchTexts.createInput2(txt, h / 10.0)
            w = max(len(txt) * h * 0.95, h * 2) + 4.0
            ti.setAsMultiLine(adsk.core.Point3D.create((wx - w / 2) / 10.0, (wy - h * 0.8) / 10.0, 0),
                              adsk.core.Point3D.create((wx + w / 2) / 10.0, (wy + h * 0.8) / 10.0, 0),
                              adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                              adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            coll.add(sk.sketchTexts.add(ti))
        ex = c.features.extrudeFeatures
        ei = ex.createInput(coll, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-S.LABEL['depth'] / 10.0))
        ei.participantBodies = [body]
        ex.add(ei)
        sk.isVisible = False
        pl.isLightBulbOn = False
        report['labels'][c.name] = [t[0] for t in labels]

    W_CL = S.PCLR
    CV = S.COVER
    HD = S.HEAD
    LUG, M8 = S.LUG_M5, S.LUG_M8
    l6 = S.LIMITER_M6                    # rev 6 (C1): EFC 10S00056 M6 limiter in every foot / end tab
    LG = S.LEG
    SO = S.STANDOFF
    PN = S.PAN

    def bend_row(where, awg, path, r_inside, supported, note, room=None):
        od = S.OD[awg]
        need = (3.0 if supported else 10.0) * od
        ok = (r_inside is None) or r_inside >= need - 1e-6
        if room is not None:
            ok = ok and room >= 0.0
        report['bends'].append(dict(where=where, awg=str(awg), od=od, path=path, r_inside=r_inside, need=round(need, 1),
                                    rule='3 x OD, supported' if supported else '10 x OD', ok=ok, note=note))

    # ------------------------------------------------------------------ shared pieces
    def face_map(face, L, D):
        """(s outward, t along the face) -> world xy, for a face of an L x D outline: '-y' / '+y' / '-x' / '+x'."""
        if face == '-y':
            return lambda s, t: (t, -s), (0.0, -1.0), (1.0, 0.0)
        if face == '+y':
            return lambda s, t: (t, D + s), (0.0, 1.0), (1.0, 0.0)
        if face == '-x':
            return lambda s, t: (-s, t), (-1.0, 0.0), (0.0, 1.0)
        return lambda s, t: (L + s, t), (1.0, 0.0), (0.0, 1.0)

    def sbox(mp, s0, s1, t0, t1, z0, z1):
        a, b_ = mp(s0, t0), mp(s1, t1)
        return box(min(a[0], b_[0]), min(a[1], b_[1]), z0, max(a[0], b_[0]), max(a[1], b_[1]), z1)

    def angular_leg(face, u, L, D, z_top, parts, lims):
        """Rev 5 leg (Dan: angular, not round): hollow buttress on a skirt face at position u along it, 24 wide at the foot
        tapering to 16 at the top, outer face sloping out from 4 proud (top) to 18 (foot), flat foot with the M5 hole 22 out."""
        mp, nv, tv = face_map(face, L, D)
        wb, wt, wall = LG['w_bot'] / 2, LG['w_top'] / 2, LG['wall']

        def solid(off):
            b = sbox(mp, -S.SKIRT - (0 if off == 0 else 10), LG['out_slope'] - off, u - wb + off - u + u, u + wb - off, -1.0 if off else 0.0,
                     z_top - (off if off else 0))
            st, et = LG['out_top'], LG['out_slope']
            # slope: through (s = st, z = z_top) and (s = et, z = ear_t); normal (z_top - ear_t, et - st) in (s, z)
            ns, nz = z_top - LG['ear_t'], et - st
            ln = math.hypot(ns, nz)
            ns, nz = ns / ln, nz / ln
            px, py = mp(st, u)
            half_cut(b, (px - nv[0] * ns * off, py - nv[1] * ns * off, z_top - nz * off), (nv[0] * ns, nv[1] * ns, nz))
            for sg in (-1, 1):                       # tapered sides: (t = +-wb, z = 0) to (t = +-wt, z = z_top)
                at, az = sg * (wt - wb), z_top
                nt, nz2 = az * sg, -at * sg
                ln2 = math.hypot(nt, nz2)
                nt, nz2 = nt / ln2, nz2 / ln2
                qx, qy = mp(0.0, u + sg * wb)
                half_cut(b, (qx - tv[0] * nt * off, qy - tv[1] * nt * off, -nz2 * off), (tv[0] * nt, tv[1] * nt, nz2))
            return b
        leg = solid(0)
        if wall:
            inner = solid(wall)
            bo(inner, sbox(mp, 0.0, LG['out_slope'], u - wb, u + wb, -2.0, z_top + 1), 'i')   # pocket stays outside the skirt
            bo(leg, inner, 's')
        fo, fw = LG['foot_out'], LG['foot_w'] / 2
        foot = sbox(mp, LG['out_slope'] - 6.0, fo, u - fw, u + fw, 0.0, LG['ear_t'])
        hx, hy = mp(fo, u)
        bo(foot, cylz(hx, hy, 0.0, LG['ear_t'], 2 * fw), 'u')
        for sg in (-1, 1):                           # chamfered top edges of the foot (angular, not round)
            qx, qy = mp(fo, u + sg * fw)
            half_cut(foot, (qx, qy, LG['ear_t'] - 2.0), (tv[0] * sg, tv[1] * sg, 1.0))
        bo(leg, foot, 'u')
        bo(leg, cylz(hx, hy, -1, LG['ear_t'] + 1, LG['hole']), 's')
        bo(leg, cylz(hx, hy, LG['ear_t'], z_top + 1, LG['socket']), 's')    # socket clearance above the foot (M6 head)
        parts.append(leg)
        lims.append(bo(cylz(hx, hy, 0, l6['l'], l6['od']), cylz(hx, hy, -1, l6['l'] + 1, l6['id']), 's'))
        return (hx, hy)

    def snap_xs(L):
        return (L * 0.25, L * 0.75)

    def cover_catches(L):
        """(x, y face) of every cover catch: two on the front, two on the rear (rev 7 POWER: rear pair moved clear of the NEG cable notches)."""
        rear = DIM['snaps_rear'] or snap_xs(L)
        return [(x, 0.0) for x in snap_xs(L)] + [(x, DIM['D']) for x in rear]

    def base_shell(L, z_d, z_t, extra_parts):
        """Deck: top plate + perimeter skirt (rounded plan), open underneath; the skirt carries the snap pockets."""
        R = S.BASE_R
        plate = rrect(0, 0, L, DIM['D'], z_t - S.PLATE, z_t, R)
        skirt = rrect(0, 0, L, DIM['D'], z_d, z_t - S.PLATE + 0.01, R)
        bo(skirt, rrect(S.SKIRT, S.SKIRT, L - S.SKIRT, DIM['D'] - S.SKIRT, z_d - 1, z_t, R - S.SKIRT), 's')
        return union_all([plate, skirt] + extra_parts)

    def base_snap_cuts(L, z_t, z_d, pan_faces):
        """Pockets in the skirt: for the cover catches (outer face, near the top) and the belly-pan catches (inner face,
        near the bottom). Also clears the ring inside the skirt where the pan wall slides up."""
        zc = z_t - S.SNAP['z_from_top']
        cuts = []
        for (x, y) in cover_catches(L):
            if True:
                cuts.append(cyl((x - S.SNAP['w'] / 2 - 0.5, y, zc), (x + S.SNAP['w'] / 2 + 0.5, y, zc), S.SNAP['bump'] + 0.2))
        g, t = W_CL, PN['t']
        ring = rrect(S.SKIRT, S.SKIRT, L - S.SKIRT, DIM['D'] - S.SKIRT, z_d - 1, z_d + PN['over'] + g, S.BASE_R - S.SKIRT)
        bo(ring, rrect(S.SKIRT + 2 * g + t, S.SKIRT + 2 * g + t, L - S.SKIRT - 2 * g - t, DIM['D'] - S.SKIRT - 2 * g - t, z_d - 2,
                       z_d + PN['over'] + 2, S.BASE_R - S.SKIRT - 2 * g - t), 's')
        cuts.append(ring)
        zp = z_d + PN['over'] / 2
        for (axis, pos) in pan_snaps(L, pan_faces):
            if axis == 'y':
                cuts.append(cyl((pos - S.SNAP['w'] / 2 - 0.5, S.SKIRT, zp), (pos + S.SNAP['w'] / 2 + 0.5, S.SKIRT, zp), S.SNAP['bump'] + 0.2))
                cuts.append(cyl((pos - S.SNAP['w'] / 2 - 0.5, DIM['D'] - S.SKIRT, zp), (pos + S.SNAP['w'] / 2 + 0.5, DIM['D'] - S.SKIRT, zp), S.SNAP['bump'] + 0.2))
            else:
                cuts.append(cyl((S.SKIRT, pos - S.SNAP['w'] / 2 - 0.5, zp), (S.SKIRT, pos + S.SNAP['w'] / 2 + 0.5, zp), S.SNAP['bump'] + 0.2))
                cuts.append(cyl((L - S.SKIRT, pos - S.SNAP['w'] / 2 - 0.5, zp), (L - S.SKIRT, pos + S.SNAP['w'] / 2 + 0.5, zp), S.SNAP['bump'] + 0.2))
        return cuts

    def pan_snaps(L, faces):
        """Belly-pan catch positions: faces 'y' -> two on the front and two on the rear wall (at x), 'x' -> on the end walls (at y)."""
        if faces == 'y':
            return [('y', x) for x in snap_xs(L)]
        if REV[0] == 7:                       # J2 = B (R94): clear of the reliefs at the outboard micro relay column
            return [('x', y_) for y_ in S.PAN_SNAPS_X]
        return [('x', DIM['D'] * 0.3), ('x', DIM['D'] * 0.7)]

    def belly_pan(L, z_d, faces, exits, pre, sh, rib=None, reliefs=()):
        """Rev 5 (Dan: snap-on covers for every live point underneath): a shallow PA12 tray under the open bottom. Its wall
        slides PAN over mm up inside the skirt; 4 tongues catch in pockets in the skirt's inner face. exits = U-notches open
        at the top of the wall, where wires leave: (axis, u, z_bottom, width) - axis 'x' = an end wall (u = y), 'y' = front /
        rear wall (u = x); a 4th field picks the wall (-1 / +1)."""
        g, t = W_CL, PN['t']
        x0, y0, x1, y1 = S.SKIRT + g, S.SKIRT + g, L - S.SKIRT - g, DIM['D'] - S.SKIRT - g
        R = S.BASE_R - S.SKIRT - g
        ztop = z_d + PN['over']
        pan = rrect(x0, y0, x1, y1, PN['z0'], ztop, R)
        bo(pan, rrect(x0 + t, y0 + t, x1 - t, y1 - t, PN['z0'] + t, ztop + 1, R - t), 's')
        sw = S.SNAP
        zp = z_d + PN['over'] / 2
        for (axis, pos) in pan_snaps(L, faces):
            for side in (0, 1):
                if axis == 'y':
                    yf = y0 if side == 0 else y1
                    for dx in (-1, 1):
                        xs = pos + dx * (sw['w'] / 2 + sw['slot'] / 2)
                        bo(pan, box(xs - sw['slot'] / 2, yf - 1, ztop - sw['len'], xs + sw['slot'] / 2, yf + 1 + t * (1 if side == 0 else -1), ztop + 1)
                           if side == 0 else box(xs - sw['slot'] / 2, yf - t - 1, ztop - sw['len'], xs + sw['slot'] / 2, yf + 1, ztop + 1), 's')
                    bo(pan, cyl((pos - sw['w'] / 2 + 0.5, yf, zp), (pos + sw['w'] / 2 - 0.5, yf, zp), sw['bump']), 'u')
                else:
                    xf = x0 if side == 0 else x1
                    for dy in (-1, 1):
                        ys = pos + dy * (sw['w'] / 2 + sw['slot'] / 2)
                        bo(pan, box(xf - 1, ys - sw['slot'] / 2, ztop - sw['len'], xf + t + 1, ys + sw['slot'] / 2, ztop + 1) if side == 0 else
                           box(xf - t - 1, ys - sw['slot'] / 2, ztop - sw['len'], xf + 1, ys + sw['slot'] / 2, ztop + 1), 's')
                    bo(pan, cyl((xf, pos - sw['w'] / 2 + 0.5, zp), (xf, pos + sw['w'] / 2 - 0.5, zp), sw['bump']), 'u')
        for (axis, u, zb_, wd, side) in exits:
            if axis == 'x':
                xw = x0 + t / 2 if side < 0 else x1 - t / 2
                n = box(xw - 4, u - wd / 2, zb_ + wd / 2, xw + 4, u + wd / 2, ztop + 1)
                bo(n, cyl((xw - 4, u, zb_ + wd / 2), (xw + 4, u, zb_ + wd / 2), wd), 'u')
            else:
                yw = y0 + t / 2 if side < 0 else y1 - t / 2
                n = box(u - wd / 2, yw - 4, zb_ + wd / 2, u + wd / 2, yw + 4, ztop + 1)
                bo(n, cyl((u, yw - 4, zb_ + wd / 2), (u, yw + 4, zb_ + wd / 2), wd), 'u')
            bo(pan, n, 's')
        if rib:      # J2 = B (R94): a rib standing on the pan floor (rib = (x0, x1, y0, y1, z_top))
            bo(pan, box(rib[0], rib[2], PN['z0'] + t - 0.01, rib[1], rib[3], rib[4]), 'u')
        for (ya, yb, depth) in reliefs:   # J2 = B: the +x wall's inner face cut back `depth` over y ya..yb (the 86 wires drop 1 mm from it)
            bo(pan, box(x1 - t - 0.01, ya, PN['z0'] + t, x1 - t + depth, yb, ztop + 1.0), 's')
        return comp(pre + 'Pan_PA12_printed', pan, AP['pa12_pan'], MAT['pa'], sh)

    def cover(L, D, z_t, z_top, notches, label_list, pre, sh, vents=(), ribs=None, side_vents=(), x0=0.0, y0=0.0, R=None, r=None,
              zb=None, zc=None, inner_R=None, inner_r=None):
        """Rounded snap-on cover over a base L x D (base outline from (x0, y0)). notches = [(axis, pos, centre_u, z_top_of_notch, width)]:
        a U-notch open at the bottom edge in the end (axis 'x') or side (axis 'y') wall. Rev 5: bumper band round the bottom,
        vertical ribs on the walls (ribs = {'y': [x...], 'x': [y...]}), vent slots through the top (vents = [(x, y, along)])
        and the walls (side_vents = [(face, u, z)]). Returns the occurrence."""
        g, t = W_CL, CV['t']
        R = CV['R'] if R is None else R
        r = CV['r'] if r is None else r
        zb = z_t - CV['over'] if zb is None else zb
        zc = z_t - S.SNAP['z_from_top'] if zc is None else zc
        out = rtop(x0 - g - t, y0 - g - t, x0 + L + g + t, y0 + D + g + t, zb, z_top, R, r)
        RG = S.RUG
        bo_ = RG['band_out']
        band = rrect(x0 - g - t - bo_, y0 - g - t - bo_, x0 + L + g + t + bo_, y0 + D + g + t + bo_, zb, zb + RG['band_h'], R + bo_)
        bo(out, band, 'u')
        zr1 = z_top - r - 0.5
        for (face, us) in (ribs or {}).items():
            for u in us:
                if face == 'y':
                    for yy in (y0 - g - t, y0 + D + g + t):
                        sg = -1 if yy < y0 else 1
                        bo(out, box(x0 + u - RG['rib_w'] / 2, min(yy, yy + sg * RG['rib_out']) - (0.5 if sg > 0 else 0), zb + RG['band_h'] - 0.01,
                                    x0 + u + RG['rib_w'] / 2, max(yy, yy + sg * RG['rib_out']) + (0.5 if sg < 0 else 0), zr1), 'u')
                else:
                    for xx in (x0 - g - t, x0 + L + g + t):
                        sg = -1 if xx < x0 else 1
                        bo(out, box(min(xx, xx + sg * RG['rib_out']) - (0.5 if sg > 0 else 0), y0 + u - RG['rib_w'] / 2, zb + RG['band_h'] - 0.01,
                                    max(xx, xx + sg * RG['rib_out']) + (0.5 if sg < 0 else 0), y0 + u + RG['rib_w'] / 2, zr1), 'u')
        inn = rtop(x0 - g, y0 - g, x0 + L + g, y0 + D + g, zb - 1, z_top - t, R - t if inner_R is None else inner_R, r - t if inner_r is None else inner_r)
        bo(out, inn, 's')
        sw = S.SNAP
        for (x, yface) in cover_catches(L):
            for (yf, sy) in (((y0 - g, -1),) if yface == 0.0 else ((y0 + D + g, 1),)):   # inner face of the front / rear wall
                for dx in (-1, 1):                                              # two slots free the tongue
                    xs = x0 + x + dx * (sw['w'] / 2 + sw['slot'] / 2)
                    ya, yb_ = (yf - t - bo_ - 1, yf + 1) if sy < 0 else (yf - 1, yf + t + bo_ + 1)
                    bo(out, box(xs - sw['slot'] / 2, ya, zb - 1, xs + sw['slot'] / 2, yb_, zb + sw['len']), 's')
                bo(out, cyl((x0 + x - sw['w'] / 2 + 0.5, yf, zc), (x0 + x + sw['w'] / 2 - 0.5, yf, zc), sw['bump']), 'u')
        for (axis, pos, u, zn, wd) in notches:
            if axis == 'x':      # end wall at x = pos, notch centred on y = u
                n = box(pos - 6, u - wd / 2, zb - 1, pos + 6, u + wd / 2, zn - wd / 2)
                bo(n, cyl((pos - 6, u, zn - wd / 2), (pos + 6, u, zn - wd / 2), wd), 'u')
            else:                # side wall at y = pos, notch centred on x = u
                n = box(u - wd / 2, pos - 6, zb - 1, u + wd / 2, pos + 6, zn - wd / 2)
                bo(n, cyl((u, pos - 6, zn - wd / 2), (u, pos + 6, zn - wd / 2), wd), 'u')
            bo(out, n, 's')
        VT = S.VENT
        for (vx, vy, along) in vents:
            if along == 'y':
                bo(out, slot_y(x0 + vx, y0 + vy - VT['l'] / 2 + VT['w'] / 2, y0 + vy + VT['l'] / 2 - VT['w'] / 2, z_top - t - 2, z_top + 1, VT['w']), 's')
            else:
                bo(out, slot_x(x0 + vx - VT['l'] / 2 + VT['w'] / 2, x0 + vx + VT['l'] / 2 - VT['w'] / 2, y0 + vy, z_top - t - 2, z_top + 1, VT['w']), 's')
        for (face, u, zv) in side_vents:     # horizontal slots through a long wall (battery block: no top slots in the trunk)
            yy = y0 - g - t / 2 if face == '-y' else y0 + D + g + t / 2
            s_ = box(x0 + u - VT['l'] / 2 + VT['w'] / 2, yy - 6, zv - VT['w'] / 2, x0 + u + VT['l'] / 2 - VT['w'] / 2, yy + 6, zv + VT['w'] / 2)
            bo(s_, cyl((x0 + u - VT['l'] / 2 + VT['w'] / 2, yy - 6, zv), (x0 + u - VT['l'] / 2 + VT['w'] / 2, yy + 6, zv), VT['w']), 'u')
            bo(s_, cyl((x0 + u + VT['l'] / 2 - VT['w'] / 2, yy - 6, zv), (x0 + u + VT['l'] / 2 - VT['w'] / 2, yy + 6, zv), VT['w']), 'u')
            bo(out, s_, 's')
        oc = comp(pre + 'Cover_PA12_printed', out, AP['pa12'], MAT['pa'], sh)
        etch(oc, label_list, z_top, sh)
        return oc

    def harness_tails(tails, lane_of, z_d, along, exit_at, pre, sh, box_name):
        """Rev 5 cable routing to the box edge. tails = [dict(x, y, awg, what)]; lane_of(tail) -> lane key (a y for along 'x',
        an x for along 'y'). Each tail drops straight out of its cavity, bends at 3 x OD (supported: tied into its bundle)
        and runs in its lane's bundle toward -x / -y and on 30 mm past the box edge (exit_at = the edge coordinate).
        Returns the exits for the belly pan and records each lane."""
        lanes = {}
        for t_ in tails:
            lanes.setdefault(lane_of(t_), []).append(t_)
        bodies, exits = [], []
        pan_top = PN['z0'] + PN['t']
        for key in sorted(lanes):
            ts = lanes[key]
            ods = [S.OD[t_['awg']] for t_ in ts]
            d = bundle_d(ods)
            zl = pan_top + 0.8 + d / 2
            worst = 1e9
            joins = []
            for t_ in ts:
                od = S.OD[t_['awg']]
                Rc = 3.0 * od + od / 2
                zc = zl + Rc
                worst = min(worst, z_d - zc)
                if along == 'x':
                    w = cyl((t_['x'], t_['y'], z_d - 0.2), (t_['x'], t_['y'], zc), od)
                    bo(w, quarter_bend(t_['x'] - Rc, t_['y'], zc, Rc, od, (1, -1)), 'u')
                    joins.append((t_['x'] - Rc, od))
                else:
                    w = cyl((t_['x'], t_['y'], z_d - 0.2), (t_['x'], t_['y'], zc), od)
                    bo(w, quarter_bend_yz(t_['x'], t_['y'] - Rc, zc, Rc, od, (1, -1)), 'u')
                    joins.append((t_['y'] - Rc, od))
                bodies.append(w)
            joins.sort(key=lambda j: -j[0])
            acc = []
            xr_ = S.LANE_X.get((box_name, round(key, 2))) if REV[0] == 7 else None
            for k, (pos, od) in enumerate(joins):
                acc.append(od)
                nxt = joins[k + 1][0] if k + 1 < len(joins) else exit_at - 30.0
                if pos - nxt > 0.05:
                    dd = bundle_d(acc)
                    if xr_ is not None and along == 'y' and (key + dd / 2 > xr_[1] or key - dd / 2 < xr_[0]):   # J2: same area, inside S.LANE_X
                        x_lo, xm_ = xr_
                        W_ = xm_ - x_lo
                        H_ = W_ + (dd * dd - W_ * W_) * math.pi / 4.0 / W_ if dd > W_ else W_
                        xc_ = (x_lo + xm_) / 2
                        za, zb2 = zl - dd / 2 + W_ / 2, zl - dd / 2 + H_ - W_ / 2
                        bodies.append(cyl((xc_, pos + 0.5, za), (xc_, nxt, za), W_))
                        if zb2 > za + 0.05:
                            bodies.append(cyl((xc_, pos + 0.5, zb2), (xc_, nxt, zb2), W_))
                            bodies.append(box(xc_ - W_ / 2, min(pos + 0.5, nxt), za, xc_ + W_ / 2, max(pos + 0.5, nxt), zb2))
                    elif along == 'x':
                        bodies.append(cyl((pos + 0.5, key, zl), (nxt, key, zl), dd))
                    else:
                        bodies.append(cyl((key, pos + 0.5, zl), (key, nxt, zl), dd))
            exits.append((key, zl - d / 2 - 0.8, d + 1.6))
            if xr_ is not None and along == 'y':     # J2: the lane's own slot through the pan wall as well (the wires stack inside S.LANE_X)
                exits.append(((xr_[0] + xr_[1]) / 2, zl - d / 2 - 0.8, xr_[1] - xr_[0] + 1.6))
            report['lanes'].setdefault(box_name, []).append(dict(at=round(key, 1), wires=len(ts), d=round(d, 1), z=round(zl, 1),
                                                                 what=[t_['what'] for t_ in ts], room=round(worst, 1)))
            bend_row('%s harness bundle at %s %.0f (%d wires)' % (box_name, 'y' if along == 'x' else 'x', key, len(ts)),
                     max((t_['awg'] for t_ in ts), key=lambda a: S.OD[a]), 'down out of the cavity, one bend at 3 x OD into the bundle, '
                     'straight to the %s edge' % ('inboard' if along == 'x' else 'front'),
                     3.0 * max(ods), True, 'bundle %.1f mm; %.1f mm to spare under the deck; outside: bundle >= 10 x OD of its largest wire = %.0f'
                     % (d, worst, 10 * max(ods)), room=worst)
        comp(pre + 'Harness_wires', bodies, AP['harness'], None, sh)
        return exits

    # ================================================================== POWER box
    def build_power():
        PW = S.POWER
        L, xb, z_d, z_t, btop = PW['L'], PW['x_bar'], PW['z_d'], PW['z_t'], PW['bar_top']
        sh = S.PLACE['POWER']
        pre = 'Power_'
        D7 = R7['D'] if R7 else S.D                              # rev 7: + the bus zone at the rear
        DIM['D'] = D7
        DIM['snaps_rear'] = R7['cover_snaps_rear'] if R7 else None
        bz0 = btop - S.BAR_T
        pz0 = btop - S.PAD['t']                                  # = standoff top
        plate_b = z_t - S.PLATE
        ami = []
        for row, sgn in (('IN', -1), ('OUT', +1)):
            for i in range(S.AMI_SLOTS[row]):
                name, amps = S.AMI_ROWS[row][i]
                y = S.AMI_Y0 + i * S.AMI_PITCH
                x_in = xb + sgn * S.AMI_IN_OFF
                ami.append(dict(row=row, i=i, name=name, amps=amps, y=y, x_in=x_in, x_out=x_in + sgn * S.AMI['c'], sgn=sgn,
                                lz=S.LUG_Z if row == 'IN' else PW['out_lug_z'], so=SO['long']))
        report['standoffs']['POWER'] = dict(IN=SO['long'], OUT=SO['long'], in_lug_z=S.LUG_Z, out_lug_z=PW['out_lug_z'], z_d=z_d, z_t=z_t,
                                            plate_bottom=plate_b, pad_bottom=pz0)
        PD = S.PAD

        def pad_box(a, z0, z1, grow=0.0):
            xa = a['x_out'] - a['sgn'] * PD['inner']
            xb_ = a['x_out'] + a['sgn'] * PD['outer']
            return box(min(xa, xb_) - grow, a['y'] - PD['w'] / 2 - grow, z0, max(xa, xb_) + grow, a['y'] + PD['w'] / 2 + grow, z1)

        # relays (rev 5: turned 90 deg): IN-row fuse i -> relay i; terminal 30 on the fuse line, on the relay's +x side
        relays = []
        for i, nm in enumerate(S.IN_RELAY):
            cx = S.F7_X[1] if i % 2 == 0 else S.F7_X[0]
            cy = S.AMI_Y0 + i * S.AMI_PITCH
            pn, own = S.RELAY_PN[nm]
            relays.append(dict(i=i, name=nm, pn=pn, own=own, cx=cx, cy=cy, x30=cx + 10.25, B=(nm == S.RELAY_B['pos'])))
        acps = (S.F7_X[0], S.ACPS_Y)

        # ---- base (deck) parts under the plate
        parts, lims = [], []
        T = S.TOWER
        for r in relays:
            parts.append(cbox(r['cx'] + 1.3, r['cy'], z_d, plate_b + 0.01, 21.1 + 2 * T + (2.0 if r['B'] else 0), 19.7 + 2 * T))
        parts.append(cbox(acps[0], acps[1], z_d, plate_b + 0.01, 6.0 + 3.0 + 2 * T, 4.6 + 2 * T))
        for a in ami:                                            # standoff bosses, both rows (hex hole = anti-rotation)
            if True:
                parts.append(cylz(a['x_out'], a['y'], z_d, plate_b + 0.01, SO['af'] / math.cos(math.radians(30)) + 2 * S.CLR + 5.0))
        if R7:            # rev 7: the bus bar terminals - M8 on the POS bar (BAT+ IN, RADLOK+, spare) and on the NEG bar
            NB = R7['neg_bar']
            m8_pos = [(xb, y_, 8) for (y_, _n, _h) in R7['pos_studs']]
            m8_neg = [(x_, NB['yc'], 8) for (x_, _n, _h, _g) in R7['neg_studs']]
            bar_bolts = [(a['x_in'], a['y'], 5) for a in ami] + m8_pos + m8_neg
        else:
            bar_bolts = [(a['x_in'], a['y'], 5) for a in ami] + [(xb, S.IN_STUD_Y, 8)]
        for (bx_, by_, m) in bar_bolts:                          # head bosses under the bar
            parts.append(cylz(bx_, by_, z_d, plate_b + 0.01, HD[m]['af'] / math.cos(math.radians(30)) + 2 * S.CLR + 5.0))
        for x in (xb - 20.0, xb + 20.0):                         # ribs along y under the plate
            parts.append(box(x - S.RIB / 2, S.SKIRT, z_d, x + S.RIB / 2, D7 - S.SKIRT, plate_b + 0.01))
        for y in [S.AMI_Y0 - 9.0 + k * 36.0 for k in range(4)] + ([190.0, 214.0] if R7 else []):  # ribs along x, between fuse lines (rev 7: + the bus zone)
            parts.append(box(S.SKIRT, y - S.RIB / 2, z_d, L - S.SKIRT, y + S.RIB / 2, plate_b + 0.01))
        if R7:            # printed barrier wall between the NEG terminals and the POS bar, deck top to 20 above it (rev 7)
            parts.append(box(R7['barrier'][0], 168.0, z_t - 0.01, R7['barrier'][1], D7, z_t + R7['barrier_h']))
        saddles = []
        U_sad = [support_union(parts)] if R7 else None
        for a in ami:            # saddles: one per relay feed, the inside of its bend (R_SADDLE), hanging under the deck
            if a['row'] != 'IN' or not a['amps']:
                continue
            r = relays[a['i']]
            od = S.OD[S.AMI_AWG[a['name']]]
            ccx, ccz = r['x30'] + S.R_SADDLE + od / 2, S.LUG_C + S.R_SADDLE + od / 2
            rs = S.R_SADDLE - 0.2
            core = bo(cyl((ccx, a['y'] - od / 2 - 0.5, ccz), (ccx, a['y'] + od / 2 + 0.5, ccz), 2 * rs),
                      box(ccx - rs - 1, a['y'] - 10, ccz - rs - 1, ccx, a['y'] + 10, ccz), 'i')
            for sy in (-1, 1):
                lip = bo(cyl((ccx, a['y'] + sy * (od / 2 + 0.5), ccz), (ccx, a['y'] + sy * (od / 2 + 2.0), ccz), 2 * (S.R_SADDLE + od * 0.6)),
                         box(ccx - S.R_SADDLE - od - 2, a['y'] - 10, ccz - S.R_SADDLE - od - 2, ccx, a['y'] + 10, ccz), 'i')
                bo(core, lip, 'u')
            top_ = box(ccx - rs, a['y'] - od / 2 - 2.0, ccz - 0.01, ccx, a['y'] + od / 2 + 2.0, z_d + 0.5)
            if R7:   # R101 (Dan 2026-10-15: "add material under the radius runners"): the saddle's back runs on up into the deck plate
                c0 = backing(top_, z_d + 0.5, U_sad)
                if c0 < S.FLOAT_BACKING:    # floating: carry it up into the deck plate
                    top_ = box(ccx - rs, a['y'] - od / 2 - 2.0, ccz - 0.01, ccx, a['y'] + od / 2 + 2.0, plate_b + 0.01)
                    after = backing(top_, plate_b + 0.01, [box(0, 0, plate_b, L, D7, z_t)])
                else:
                    after = c0
                report['feature_support'].setdefault('POWER', []).append(dict(
                    kind='saddle', at=[round(ccx - rs / 2, 1), round(a['y'], 1)], before=round(c0, 3), web=c0 < S.FLOAT_BACKING,
                    after=round(after, 3)))
            bo(core, top_, 'u')
            saddles.append(core)
        parts += saddles
        z_leg = z_t - CV['over'] - 1.0
        # rev 7: no foot under the NEG cables - the rear inboard foot moves round to the inboard end, behind the harness exits
        leg_at = [('-y', 30.0), ('-y', L - 30.0), ('+y', L - 30.0), ('-x', D7 - 30.0)] if R7 else [(f, u) for f in ('-y', '+y') for u in (30.0, L - 30.0)]
        feet = [angular_leg(f, u, L, D7, z_leg, parts, lims) for (f, u) in leg_at]
        holes_p, fins_p = crimp_holes('POWER', z_d, z_t, parts, plate_b)
        deck = base_shell(L, z_d, z_t, parts + fins_p)
        cuts = base_snap_cuts(L, z_t, z_d, 'y') + holes_p
        B_ = dict(S.BAR, y1=R7['bar_y1']) if R7 else S.BAR       # rev 7: the POS bar runs on into the bus zone
        cuts.append(box(xb - B_['w'] / 2 - S.CLR, B_['y0'] - S.CLR, bz0, xb + B_['w'] / 2 + S.CLR, B_['y1'] + S.CLR, z_t + 1))
        if R7:
            cuts.append(box(NB['x0'] - S.CLR, NB['yc'] - B_['w'] / 2 - S.CLR, bz0, NB['x1'] + S.CLR, NB['yc'] + B_['w'] / 2 + S.CLR, z_t + 1))
        for a in ami:
            cuts.append(pad_box(a, pz0, z_t + 1, S.CLR))
            xc = (a['x_in'] + a['x_out']) / 2
            cuts.append(cbox(xc, a['y'], btop + S.AMI['ear_t'] / 2 - S.AMI['body_h'] / 2 - 0.6, z_t + 1, S.AMI['body_l'] + 1, S.AMI['body_w'] + 1))
            cuts.append(hexz(a['x_out'], a['y'], z_d - 1, pz0 + 0.01, SO['af'] + 2 * S.CLR))
        for (bx_, by_, m) in bar_bolts:
            cuts.append(hexz(bx_, by_, z_d - 1, bz0 + 0.01, HD[m]['af'] + 2 * S.CLR))
            cuts.append(cylz(bx_, by_, z_d - 1, bz0 + 1, m + 0.5))
        for r in relays:   # Mini ISO cavities, turned 90 deg: (u, v) of the F7 bottom view -> x = cx - v, y = cy + u
            pins = [(0, 7.65, 11.5, 3.2), (0, -10.25, 11.5, 3.2), (-8.45, -0.25, 2.8, 8.3), (8.45, -0.25, 2.8, 8.3)]
            if r['B']:
                pins.append((0, S.RELAY_B['v87a'], 8.3, 2.8))
            for (u, v, lx, ly) in pins:
                cuts.append(cbox(r['cx'] - v, r['cy'] + u, z_d - 1, z_t + 1, ly, lx))
        for dx in (-3.0, 3.0):
            cuts.append(cbox(acps[0] + dx, acps[1], z_d - 1, z_t + 1, 3.0, 4.6))
        # rev 6: the OUT-row lugs sit on 40 mm standoffs at the IN-row height, under the skirt: no skirt notches (belly pan exits below)
        sub_all(deck, cuts)
        comp(pre + 'Base_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_steel_M6', lims, AP['al'], MAT['ss'], sh)

        # ---- copper, standoffs, bolts
        bar = box(xb - B_['w'] / 2, B_['y0'], bz0, xb + B_['w'] / 2, B_['y1'], btop)
        for (bx_, by_, m) in (m8_pos if R7 else [(xb, S.IN_STUD_Y, 8)]):
            bo(bar, cylz(bx_, by_, bz0 - 1, btop + 1, 8.5), 's')
        pads = []
        for a in ami:
            bo(bar, cylz(a['x_in'], a['y'], bz0 - 1, btop + 1, 5.5), 's')
            p = pad_box(a, pz0, btop)
            bo(p, cylz(a['x_out'], a['y'], pz0 - 1, btop + 1, 5.5), 's')
            pads.append(p)
        comp(pre + ('Bar_Power_%s_25x6p35%s' % (BM['name'], '_POS_bus_L226' if R7 else '')), bar, AP['tin'], MAT['cu'], sh)
        if R7:            # NEG bar: same 1" x 1/4" stock on flat, M8 holes
            nbar = box(NB['x0'], NB['yc'] - B_['w'] / 2, bz0, NB['x1'], NB['yc'] + B_['w'] / 2, btop)
            for (bx_, by_, m) in m8_neg:
                bo(nbar, cylz(bx_, by_, bz0 - 1, btop + 1, 8.5), 's')
            comp(pre + 'BarNeg_%s_25x6p35_L105' % BM['name'], nbar, AP['tin'], MAT['cu'], sh)
        comp(pre + 'Pad_Out_%s_15x3' % BM['name'], pads, AP['tin'], MAT['cu'], sh)
        comp(pre + 'Standoff_M5_FF_hex8_L%d_brass' % SO['long'], [bo(hexz(a['x_out'], a['y'], a['lz'] + 2.0, pz0, SO['af']), cylz(a['x_out'], a['y'], a['lz'], pz0 + 1, 4.2), 's')
                                                                 for a in ami], AP['brass'], MAT['brass'], sh)       # rev 6 (B5): one 40 mm standoff, both rows
        z_ear = btop + S.AMI['ear_t']
        comp(pre + 'BarBolt_ISO4017_A2', [union_all([hexz(bx_, by_, bz0 - HD[m]['k'], bz0, HD[m]['af']), cylz(bx_, by_, bz0, btop + (12.0 if m == 5 else 16.0), float(m))])
                                          for (bx_, by_, m) in bar_bolts], AP['al'], MAT['ss'], sh)
        comp(pre + 'SetScrew_ISO4026_A2', [cylz(a['x_out'], a['y'], pz0 - 5.0, z_ear + 5.0, 5.0) for a in ami], AP['al'], MAT['ss'], sh)   # 5 into the standoff
        comp(pre + 'LugBolt_ISO4017_A2', [union_all([hexz(a['x_out'], a['y'], a['lz'] - HD[5]['k'], a['lz'], HD[5]['af']),
                                                     cylz(a['x_out'], a['y'], a['lz'], a['lz'] + 10.0, 5.0)])
                                          for a in ami if a['amps']], AP['al'], MAT['ss'], sh)      # M5 x 10 both rows (rev 6: 40 mm standoffs)
        nuts = [hexz(a['x_in'], a['y'], z_ear, z_ear + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami]
        nuts += [hexz(a['x_out'], a['y'], z_ear, z_ear + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami]
        for (bx_, by_, m) in ((m8_pos + m8_neg) if R7 else [(xb, S.IN_STUD_Y, 8)]):
            nuts.append(hexz(bx_, by_, btop + M8['t'], btop + M8['t'] + S.M8_NUT['h'], S.M8_NUT['af']))
        comp(pre + 'Nut_Keps_M5_M8_A2', nuts, AP['al'], MAT['ss'], sh)

        # ---- fuses + relays
        by_col = {}
        for a in ami:
            if a['amps'] is None:
                continue
            xa, xb2 = sorted((a['x_in'], a['x_out']))
            ear = slot_x(xa, xb2, a['y'], btop, btop + S.AMI['ear_t'], S.AMI['ear_w'])
            for x in (xa, xb2):
                bo(ear, cylz(x, a['y'], btop - 1, btop + 2, S.AMI['hole']), 's')
            zc = btop + S.AMI['ear_t'] / 2
            body = cbox((xa + xb2) / 2, a['y'], zc - S.AMI['body_h'] / 2, zc + S.AMI['body_h'] / 2, S.AMI['body_l'], S.AMI['body_w'])
            bo(body, ear, 'u')
            by_col.setdefault(S.AMI_COLOUR[a['amps']], []).append(body)
        for colr, bodies in by_col.items():
            comp(pre + 'Fuse_AMI_%s' % colr, bodies, AP[colr], MAT['abs'], sh)
        comp(pre + 'Fuse_ATM_10A', cbox(acps[0], acps[1], z_t, z_t + S.MINI['h_above'], S.MINI['l'], S.MINI['w']), MINI_AP[10], MAT['abs'], sh)
        RBd = S.RELAY_B
        comp(pre + 'Relay_TE_F7_V23134', [cbox(r['cx'], r['cy'], z_t, z_t + S.F7['h'], S.F7['body'], S.F7['body']) for r in relays if r['pn'] and not r['B']],
             AP['black'], MAT['abs'], sh)
        comp(pre + 'Relay_TE_PowerB_V23234_CO', [cbox(r['cx'], r['cy'], z_t, z_t + RBd['h'], RBd['body'], RBd['body']) for r in relays if r['B']],
             AP['black'], MAT['abs'], sh)
        comp(pre + 'SPARE_positions', [cbox(r['cx'], r['cy'], z_t, z_t + 1.0, S.F7['body'], S.F7['body']) for r in relays if not r['pn']], AP['spare'], None, sh)

        # ---- lugs + cables: OUT row straight out +x under the deck plate; IN row straight -x, one bend up round its saddle
        lugs, wires = [], []
        for a in ami:
            if a['amps'] is None:
                continue
            awg = S.AMI_AWG[a['name']]
            od = S.OD[awg]
            lg = S.LUG_6AWG if awg == 6 else LUG
            t, e = ring_lug(a['x_out'], a['y'], a['lz'], lg['b'], 5.5, lg['t'], lg['d4'], (a['sgn'], 'x'), lg['l'] - lg['tip'])
            lugs.append(t)
            if a['row'] == 'OUT':
                wires.append(cyl(e, (L + 30.0, a['y'], e[2]), od))
                bend_row('POWER AMI %s %s (%dA) -> harness' % (a['row'], a['name'], a['amps']), awg, 'straight out through the outboard end, under the skirt (belly pan exit), lug axis',
                         None, False, 'no bend in the box; first bend in the harness: >= %.0f supported (P-clamp each side) or >= %.0f free' % (3 * od, 10 * od))
            else:
                r = relays[a['i']]
                rcw = S.R_SADDLE + od / 2
                cz = e[2] + rcw
                w_ = cyl(e, (r['x30'] + rcw, a['y'], e[2]), od)
                bo(w_, quarter_bend(r['x30'] + rcw, a['y'], cz, rcw, od, (-1, -1)), 'u')
                if z_d - 0.2 - cz > 0.1:
                    bo(w_, cyl((r['x30'], a['y'], cz), (r['x30'], a['y'], z_d - 0.2), od), 'u')
                wires.append(w_)
                bend_row('POWER AMI IN %s (%dA) -> %s terminal 30' % (a['name'], a['amps'], r['name']), awg,
                         'straight %.0f mm, then 90 deg up round the printed saddle into the cavity' % (e[0] - r['x30'] - rcw),
                         S.R_SADDLE, True, 'saddle R%.0f under the deck sets and supports the bend' % S.R_SADDLE)
        if not R7:
            t, e = ring_lug(xb, S.IN_STUD_Y, btop, M8['b'], 8.4, M8['t'], M8['d4'], (1, 'x'), M8['l'] - M8['tip'], barrel=19.0)
            lugs.append(t)
            wires.append(cyl(e, (L + 30.0, S.IN_STUD_Y, e[2]), S.OD['1/0']))
            bend_row('POWER 1/0 input (M8 on the bar)', '1/0', 'straight in through the cover end notch, lug axis', None, False,
                     'no bend in the box; first bend outside >= %.0f supported / >= %.0f free' % (3 * S.OD['1/0'], 10 * S.OD['1/0']))
        else:             # rev 7 bus zone: 1/0 lugs dead straight out of the box (POS out the outboard end, NEG out the rear)
            bus_pos, bus_neg, neg_w = [], [], []
            for (y_, nm, h_) in R7['pos_studs']:
                if nm == 'SPARE':
                    continue
                t, e = ring_lug(xb, y_, btop, M8['b'], 8.4, M8['t'], M8['d4'], (1, 'x'), M8['l'] - M8['tip'], barrel=19.0)
                bus_pos.append(t)
                wires.append(cyl(e, (L + 30.0, y_, e[2]), S.OD['1/0']))
                bend_row('BUS POS %s (%s, 1/0, M8 on the POS bar)' % (nm, h_), '1/0', 'straight out through the cover end notch, lug axis', None, False,
                         'no bend in the box; first bend outside >= %.0f supported / >= %.0f free' % (3 * S.OD['1/0'], 10 * S.OD['1/0']))
            for (x_, nm, h_, g_) in R7['neg_studs']:
                if g_ == '1/0':
                    t, e = ring_lug(x_, NB['yc'], btop, M8['b'], 8.4, M8['t'], M8['d4'], (1, 'y'), M8['l'] - M8['tip'], barrel=19.0)
                    od, awg_s = S.OD['1/0'], '1/0'
                else:     # up to 3 small M8 rings stacked on one stud (CabinPower t_pdb_gnd_htr / _pwr / _rev); drawn as one ring + their bundle
                    t, e = ring_lug(x_, NB['yc'], btop, R7['small_ring_b'], 8.4, 1.0, 5.3, (1, 'y'), 28.0, barrel=12.0)
                    od, awg_s = bundle_d([S.OD[a_] for a_ in R7['small_awg']]), R7['small_awg'][0]
                bus_neg.append(t)
                neg_w.append(cyl(e, (x_, D7 + 30.0, e[2]), od))     # 119 (d): the NEG cables black, as the harness has them
                bend_row('BUS NEG %s (%s, %s, M8 on the NEG bar)' % (nm, h_, awg_s), awg_s, 'straight out through the cover rear notch, lug axis', None, False,
                         'no bend in the box; first bend outside >= %.0f supported / >= %.0f free' % (3 * S.OD[awg_s], 10 * S.OD[awg_s]))
            comp(pre + 'Lug_BusPos_Klauke6R8', bus_pos, AP['cu'], None, sh)
            comp(pre + 'Lug_BusNeg_Klauke6R8_PIDG', bus_neg, AP['cu'], None, sh)
            comp(pre + 'Wire_neg', neg_w, AP['black'], None, sh)
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_feed', wires, AP['wire'], None, sh)

        # ---- harness wires out of every relay / ACPS terminal, to the inboard edge (rev 5, point 5)
        tails = []
        for r in relays:
            if not r['pn']:
                continue
            a87 = S.RELAY87_AWG.get(r['name'], S.AMI_AWG[S.AMI_ROWS['IN'][r['i']][0]])
            tails.append(dict(x=r['cx'] - 7.65, y=r['cy'], awg=a87, what='%s 87' % r['name'], lane=r['cy']))
            if r['B']:
                tails.append(dict(x=r['cx'] - RBd['v87a'], y=r['cy'], awg=S.H87A_AWG, what='%s 87a' % r['name'], lane=r['cy']))
            for sg, tn in ((-1, '85'), (1, '86')):
                tails.append(dict(x=r['cx'] + 0.25, y=r['cy'] + sg * 8.45, awg=S.COIL_AWG, what='%s %s' % (r['name'], tn),
                                  lane=r['cy'] + sg * 9.0))
        for dx in (-3.0, 3.0):
            tails.append(dict(x=acps[0] + dx, y=acps[1], awg=S.ACPS_AWG, what='ACPS', lane=acps[1]))
        for t_ in tails:          # coil lanes half way between fuse lines; the heater 85 joins the ACPS lane
            if abs(t_['lane'] - acps[1]) < 1.0 or abs(t_['lane'] - (S.AMI_Y0 - 9.0)) < 0.1:
                t_['lane'] = acps[1]
        exits = harness_tails(tails, lambda t_: t_['lane'], z_d, 'x', 0.0, pre, sh, 'POWER')
        pan_exits = [('x', u, zb_, wd, -1) for (u, zb_, wd) in exits]
        for a in ami:            # rev 6: OUT-row lugs / cables leave under the skirt, through the belly pan's outboard wall
            if a['row'] == 'OUT' and a['amps']:
                awg = S.AMI_AWG[a['name']]
                lg = S.LUG_6AWG if awg == 6 else LUG
                wall_in = L - S.SKIRT - W_CL - PN['t'] - 0.5
                if a['x_out'] + (lg['l'] - lg['tip'] - 9.0) > wall_in:      # the flat tongue reaches the pan wall (JB1 3R5): notch round the tongue
                    wd = 2 * max(math.hypot(lg['b'] / 2 + 0.6, 1.0), lg['d4'] / 2 + 0.6, S.OD[awg] / 2 + 0.6)
                    zb_ = a['lz'] + 1.0 - wd / 2
                else:
                    wd = max(lg['d4'], S.OD[awg]) + 1.2
                    zb_ = a['lz'] + lg['d4'] / 2 - wd / 2
                pan_exits.append(('x', a['y'], zb_, wd, 1))
        belly_pan(L, z_d, 'y', pan_exits, pre, sh)
        bend_row('POWER relay terminals (85 / 86 / 87 / 87a), largest %d AWG' % S.RELAY_OUT_AWG, S.RELAY_OUT_AWG,
                 'straight down out of the cavity, one bend into its bundle (rows above)', 3.0 * S.OD[S.RELAY_OUT_AWG], True,
                 'bundles run where no feed wire runs (relays turned 90 deg)')

        # ---- cover: rev 4 etched names, unchanged (Dan 2026-10-14: "the lid labels were fine as they were"); vents (point 1), rugged band + ribs (point 6)
        tallest = max(z_t + RBd['h'], z_t + S.F7['h'])
        z_top = tallest + CV['clear'] + CV['t']
        labels = []
        for r in relays:
            labels.append(({'heater': 'HEATER', 'k_efi': 'EFI', 'k_str': 'STARTER', 'k_fan': 'FAN', 'k_fan2': 'FAN 2', 'power': 'WINDOWS',
                            'SPARE': 'SPARE'}[r['name']], r['cx'], r['cy'], S.LABEL['h_relay']))
        labels.append(('ACPS 10A', acps[0], acps[1], S.LABEL['h_ami']))
        for a in ami:
            xc = (a['x_in'] + a['x_out']) / 2
            labels.append((('%s %dA' % (a['name'], a['amps'])) if a['amps'] else 'SPARE', xc, a['y'], S.LABEL['h_ami']))
        if not R7:
            labels.append(('1/0 IN', xb + 24.0, S.IN_STUD_Y, S.LABEL['h_ami']))
        labels.append(('POWER', xb - 50.0, 6.0, 5.0))
        vents = [(x, y, 'y') for x in (31.0, 76.0, 172.0) for y in (34.0 + k * S.VENT['pitch'] for k in range(8)) if not (x == 172.0 and y < 30)]
        zn = btop + M8['d4'] / 2 + S.OD['1/0'] / 2 + 1.5
        if not R7:
            notches = [('x', L + W_CL + CV['t'] / 2, S.IN_STUD_Y, zn, S.OD['1/0'] + 2.0)]
            ribs = {'y': [15.0, 75.0, 105.0, L - 15.0], 'x': [34.0 + 36.0 * k for k in range(4)]}
        else:
            notches = [('x', L + W_CL + CV['t'] / 2, y_, zn, S.OD['1/0'] + 2.0) for (y_, nm, h_) in R7['pos_studs'] if nm != 'SPARE']
            for (x_, nm, h_, g_) in R7['neg_studs']:
                if g_ == '1/0':
                    notches.append(('y', D7 + W_CL + CV['t'] / 2, x_, zn, S.OD['1/0'] + 2.0))
                else:
                    sd = bundle_d([S.OD[a_] for a_ in R7['small_awg']])
                    notches.append(('y', D7 + W_CL + CV['t'] / 2, x_, btop + 2.65 + sd / 2 + 1.5, max(sd + 2.0, 7.0)))
            for (y_, nm, h_) in R7['pos_studs']:
                labels.append((nm if nm != 'SPARE' else 'SPARE M8', xb + 24.0, y_, S.LABEL['h_ami']))
            for (x_, nm, h_, g_) in R7['neg_studs']:
                labels.append((nm, x_, NB['yc'] - 17.0, 2.6))
            labels.append(('NEG BUS', 55.0, 176.0, 4.0))
            labels.append(('POS BUS', xb, 234.0, 3.0))
            ribs = {'y': [26.5, 49.5, 72.5, 140.0, L - 15.0], 'x': [34.0 + 36.0 * k for k in range(4)] + [190.0, 214.0]}
        cover(L, D7, z_t, z_top, notches, labels, pre, sh, vents=vents, ribs=ribs)
        DIM['D'], DIM['snaps_rear'] = S.D, None
        return dict(L=L, D=D7, H=z_top, z_d=z_d, z_t=z_t, cover_top=z_top, feet=feet, relays=relays, ami=ami, acps=acps,
                    in_y=(R7['pos_studs'][0][0] if R7 else S.IN_STUD_Y))

    # ================================================================== LOGIC box
    def build_logic():
        """Rev 6 (C4): the mini fuses stay; every fuse input is a 14 AWG jumper - TE 880398-2 receptacle in the input cavity,
        straight down into a TE PIDG 53941-1 ring lug bolted (M4 x 8 + spring washer) into its tapped bus strip. The two strips
        stand on edge between the fuse columns, back to back either side of a printed spine (lips under both strips); lugs
        alternate between two rows. Feed lugs (Klauke 2R5) bolt straight onto the strips (no standoffs in this box)."""
        LGc = S.LOGIC
        L, z_d, z_t = LGc['L'], LGc['z_d'], LGc['z_t']
        sh = S.PLACE['LOGIC']
        pre = 'Logic_'
        ST, JL, JB, JR, SP = S.STRIP, S.JLUG, S.JBOLT, S.JROW, S.SPINE
        plate_b = z_t - S.PLATE
        s_z0, s_z1 = S.STRIP_Z0, S.STRIP_Z0 + ST['h']
        mini, micro = [], []
        n = 0
        for col, (cx, fuses) in S.MINI_COLS.items():
            for i, (nm, amps) in enumerate(fuses):
                n += 1
                mini.append((col, nm, amps, cx, S.MINI_Y0 + i * S.MINI['pitch'], n, i))
        k = 0
        for cx in S.MICRO_COLS:
            for cy in S.MICRO_Y:
                nm, pn, own = S.MICRO_POS[k]
                k += 1
                micro.append((nm, pn, own, cx, cy, k))
        report['standoffs']['LOGIC'] = dict(feed=None, note='rev 6: no standoffs - the feed lugs bolt straight onto the strips', z_d=z_d, z_t=z_t)

        # ---- strips: lug face toward the column's input line
        strips = {}
        for col, (cx, fuses) in S.MINI_COLS.items():
            sd = S.MINI_IN[col]
            xin = cx + sd * 3.0                                 # input blade / jumper line
            xpm = xin + sd * JL['ax']                           # lug palm mid-plane
            face = xpm + sd * JL['t'] / 2                       # strip face the palms sit on
            x0, x1 = sorted((face, face + sd * ST['t']))
            strips[col] = dict(cx=cx, sd=sd, xin=xin, xpm=xpm, face=face, x0=x0, x1=x1, y0=S.STRIP_Y[col][0], y1=S.STRIP_Y[col][1])
        sx_lo = strips['BUS1']['x1']                            # gap between the strips
        sx_hi = strips['BUS2']['x0']
        spx = (sx_lo + sx_hi) / 2
        studs = []                                              # (col, i, y, z, fuse name or None)
        for (col, nm, amps, cx, y, n_, i) in mini:
            if i >= S.STUDS[col]:
                continue
            lower = (i % 2 == 0) == (col == 'BUS1')             # BUS1 even = lower row, BUS2 even = upper row (no tip meets a tip)
            z = JR['z_lo'] + (0.0 if lower else JR['dz'])
            studs.append(dict(col=col, i=i, y=y, z=z, fuse=nm if amps else None, amps=amps))
        report['logic_jumpers'] = dict(strips={c: dict(x=[round(v['x0'], 2), round(v['x1'], 2)], y=[v['y0'], v['y1']]) for c, v in strips.items()},
                                       spine_x=round(spx, 2), studs=len(studs), jumpers=sum(1 for s_ in studs if s_['fuse']),
                                       rows_z=[JR['z_lo'], JR['z_lo'] + JR['dz']])

        # ---- base
        parts, lims = [], []
        T = S.TOWER
        for col, (cx, fuses) in S.MINI_COLS.items():            # cavity tower over the whole fuse column
            yl = S.MINI_Y0 + (len(fuses) - 1) * S.MINI['pitch']
            parts.append(box(cx - S.MINI['l'] / 2 - T, S.MINI_Y0 - 6.4 - T, z_d, cx + S.MINI['l'] / 2 + T, yl + 6.4 + T, plate_b + 0.01))
        for (nm, pn, own, cx, cy, k_) in micro:
            parts.append(cbox(cx, cy, z_d, plate_b + 0.01, 11.6 + 2 * T, 18.6 + 2 * T))
        ylo = min(v['y0'] for v in strips.values()) - 1.0
        yhi = max(v['y1'] for v in strips.values()) + 1.0
        lip_z1 = s_z0 - 0.4
        lip_z0 = lip_z1 - SP['lip_t']
        spine = box(spx - SP['t'] / 2, ylo, lip_z0, spx + SP['t'] / 2, yhi, plate_b + 0.01)
        for c_, v in strips.items():                            # lips under each strip (the strips slide in from the rear)
            xa = v['x0'] + 0.8 if c_ == 'BUS1' else v['x0']
            xb_ = v['x1'] if c_ == 'BUS1' else v['x1'] - 0.8
            bo(spine, box(min(xa, spx), v['y0'] - 0.5, lip_z0, max(xb_, spx), v['y1'] + 0.5, lip_z1), 'u')
        parts.append(spine)
        if REV[0] == 7:   # J4 = B (R94): the printed channel floor across the front (over the Bus 1 feed lug), joined to the spine
            CH = S.CHANNEL
            parts.append(box(CH['floor_x'][0], CH['floor_y'][0], CH['floor'][0], spx + SP['t'] / 2 + 0.01, CH['floor_y'][1], CH['floor'][1]))
            parts.append(box(spx + SP['t'] / 2 - 0.01, CH['floor_y'][0], CH['floor'][0], CH['floor_x'][1], CH['wide_y'], CH['floor'][1]))
        z_leg = z_t - CV['over'] - 1.0
        feet = [angular_leg(f, u, L, S.D, z_leg, parts, lims) for f in ('-x', '+x') for u in (30.0, S.D - 30.0)]
        holes_l, fins_l = crimp_holes('LOGIC', z_d, z_t, parts, plate_b)
        deck = base_shell(L, z_d, z_t, parts + fins_l)
        cuts = base_snap_cuts(L, z_t, z_d, 'x') + holes_l
        for (col, nm, amps, cx, y, n_, i) in mini:              # 2 x 2.8 mm receptacles per mini fuse (input + output)
            for dx in (-3.0, 3.0):
                cuts.append(cbox(cx + dx, y, z_d - 1, z_t + 1, 3.0, 4.6))
        for (nm, pn, own, cx, cy, k_) in micro:                 # approximate pattern from TE 1308028; set exactly in detail work
            for (u, v, lx, ly) in ((0, 8.0, 8.3, 2.6), (0, -8.0, 8.3, 2.6), (-4.5, 0, 2.6, 6.8), (4.5, 0, 2.6, 6.8), (0, 0, 2.6, 4.0)):
                cuts.append(cbox(cx + u, cy + v, z_d - 1, z_t + 1, lx, ly))
        for s_ in studs:                                        # bolt tips pass the spine
            cuts.append(cyl((sx_lo - 1.0, s_['y'], s_['z']), (sx_hi + 1.0, s_['y'], s_['z']), JB['m'] + 1.6))
        for col, f in S.FEED.items():
            cuts.append(cyl((sx_lo - 1.0, f['y'], f['z']), (sx_hi + 1.0, f['y'], f['z']), 5.0 + 1.6))
        sub_all(deck, cuts)
        comp(pre + 'Base_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_steel_M6', lims, AP['al'], MAT['ss'], sh)

        # ---- copper strips (tapped M4 at every stud, M5 at the feed)
        sbodies = []
        for col, v in strips.items():
            st = box(v['x0'], v['y0'], s_z0, v['x1'], v['y1'], s_z1)
            for s_ in studs:
                if s_['col'] == col:
                    bo(st, cyl((v['x0'] - 1, s_['y'], s_['z']), (v['x1'] + 1, s_['y'], s_['z']), JB['m']), 's')
            f = S.FEED[col]
            bo(st, cyl((v['x0'] - 1, f['y'], f['z']), (v['x1'] + 1, f['y'], f['z']), 5.0), 's')
            sbodies.append(st)
        comp(pre + 'Strip_Logic_%s_25p4x3p2_on_edge' % BM['name'], sbodies, AP['tin'], MAT['cu'], sh)

        # ---- jumper lugs, bolts, washers, jumpers (straight down from the input cavity into the lug barrel)
        jl, jb, jw, jwire = [], [], [], []
        od_j = S.OD[S.JUMPER_AWG]
        for s_ in studs:
            v = strips[s_['col']]
            sd, y, z = v['sd'], s_['y'], s_['z']
            xa, xb_ = v['xpm'] - JL['t'] / 2, v['xpm'] + JL['t'] / 2
            if s_['fuse']:
                ring = cyl((xa, y, z), (xb_, y, z), JL['ring'])
                bo(ring, box(xa, y - 2.25, z, xb_, y + 2.25, z + JL['ring'] / 2 + JL['neck'] + 0.5), 'u')     # neck
                bo(ring, cyl((xa - 1, y, z), (xb_ + 1, y, z), JL['hole']), 's')
                zb0 = z + JL['ring'] / 2 + JL['neck']
                zb1 = z + JL['L'] - JL['ring'] / 2
                bo(ring, cylz(v['xin'], y, zb0, zb1, JL['sleeve']), 'u')
                jl.append(ring)
                jwire.append(cylz(v['xin'], y, zb1 - 0.5, z_d - 0.2, od_j))
                wx0 = v['xpm'] - sd * JL['t'] / 2                          # palm outer face (washer side)
                jw.append(bo(cyl((wx0, y, z), (wx0 - sd * JB['washer_t'], y, z), JB['washer_od']), cyl((wx0 + sd, y, z), (wx0 - sd * 2, y, z), JB['m'] + 0.2), 's'))
                xh = wx0 - sd * JB['washer_t']                              # under-head face
            else:
                continue                                                    # spare stud: tapped hole only - its bolt comes with its lug
            head = hex_x(min(xh, xh - sd * HD[4]['k']), max(xh, xh - sd * HD[4]['k']), y, z, HD[4]['af'])
            shank = cyl((xh, y, z), (xh + sd * JB['l'], y, z), float(JB['m']))
            jb.append(union_all([head, shank]))
            if s_['fuse']:
                bend_row('LOGIC %s %s input jumper (%d AWG)' % (s_['col'], s_['fuse'], S.JUMPER_AWG), S.JUMPER_AWG,
                         'straight down from the input receptacle into its PIDG lug barrel (%.1f mm of wire between them)' % (z_d - zb1),
                         None, True, 'no bend: the lug barrel is right under the input blade')
        comp(pre + 'Lug_TE_PIDG_53941-1', jl, AP['cu'], None, sh)
        comp(pre + 'LugBolt_M4x8_A2', jb, AP['al'], MAT['ss'], sh)
        comp(pre + 'Washer_DIN127B_M4', jw, AP['al'], MAT['ss'], sh)
        comp(pre + 'Wire_jumper_14AWG', jwire, AP['wire'], None, sh)

        # ---- feeds: Klauke 2R5 on the strip's lug face, M5 x 10 into the tapped strip; wire straight out (BUS1 front, BUS2 rear)
        flugs, fbolts, fwires, pan_feed = [], [], [], []
        for col, f in S.FEED.items():
            v = strips[col]
            sd = v['sd']
            awg = S.FEEDS[col][1]
            od = S.OD[awg]
            pa, pb = v['face'] - sd * LUG['t'], v['face']
            xpc = (pa + pb) / 2
            y, z, dy = f['y'], f['z'], f['dir']
            pa, pb = min(pa, pb), max(pa, pb)
            lg = cyl((pa, y, z), (pb, y, z), LUG['b'])
            bo(lg, box(min(pa, pb), min(y, y + dy * (LUG['l'] - LUG['tip'] - 9.0)), z - LUG['b'] / 2, max(pa, pb), max(y, y + dy * (LUG['l'] - LUG['tip'] - 9.0)), z + LUG['b'] / 2), 'u')
            bo(lg, cyl((pa - 1, y, z), (pb + 1, y, z), 5.5), 's')
            xbar = xpc - sd * (LUG['d4'] / 2 - LUG['t'] / 2)
            yb0, yb1 = y + dy * (LUG['l'] - LUG['tip'] - 9.0), y + dy * (LUG['l'] - LUG['tip'])
            bo(lg, cyl((xbar, yb0, z), (xbar, yb1, z), LUG['d4']), 'u')
            flugs.append(lg)
            yend = -30.0 if dy < 0 else S.D + 30.0
            fwires.append(cyl((xbar, yb1, z), (xbar, yend, z), od))
            xh = v['face'] - sd * LUG['t']
            fbolts.append(union_all([hex_x(min(xh, xh - sd * HD[5]['k']), max(xh, xh - sd * HD[5]['k']), y, z, HD[5]['af']),
                                     cyl((xh, y, z), (xh + sd * 10.0, y, z), 5.0)]))
            pan_feed.append(('y', xbar, z - max(LUG['d4'], od) / 2 - 0.6, max(LUG['d4'], od) + 1.2, dy))
            bend_row('LOGIC %s feed (from %s)' % (col, S.FEEDS[col][0]), awg, 'straight out the %s end, lug axis, under the skirt' % ('front' if dy < 0 else 'rear'),
                     None, False, 'no bend in the box; first bend in the harness: >= %.0f supported or >= %.0f free' % (3 * od, 10 * od))
        comp(pre + 'Lug_Klauke', flugs, AP['cu'], None, sh)
        comp(pre + 'LugBolt_M5x10_A2', fbolts, AP['al'], MAT['ss'], sh)
        comp(pre + 'Wire_feed', fwires, AP['wire'], None, sh)

        by_amp = {}
        for (col, nm, amps, cx, y, n_, i) in mini:
            if amps is not None:
                by_amp.setdefault(amps, []).append(cbox(cx, y, z_t, z_t + S.MINI['h_above'], S.MINI['l'], S.MINI['w']))
        for amps, bodies in by_amp.items():
            comp(pre + 'Fuse_ATM_%sA' % str(amps).replace('.', 'p'), bodies, MINI_AP[amps], MAT['abs'], sh)
        comp(pre + 'Relay_TE_MicroA_V23074', [cbox(cx, cy, z_t, z_t + S.MICRO['h'], S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy, k_) in micro if pn],
             AP['black'], MAT['abs'], sh)
        comp(pre + 'SPARE_positions', [cbox(cx, cy, z_t, z_t + 1.0, S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy, k_) in micro if not pn], AP['spare'], None, sh)

        # ---- harness: one load wire per fuse (output blade), MRS / B30 inputs, 5 per micro relay; bundles to the front edge
        tails = []
        skip = S.CHANNEL_CAD_SKIP if REV[0] == 7 else ()     # J4 = B: these run in the front channel (the wired views draw them)
        for (col, nm, amps, cx, y, n_, i) in mini:
            if not amps or nm in skip:
                continue
            sd = S.MINI_IN[col]
            lane = cx - sd * 3.0
            tails.append(dict(x=lane, y=y, awg=S.MINI_AWG[amps], what=nm, lane=lane))
            if i >= S.STUDS[col] + (1 if col == 'BUS2' else 0):           # own input (MRS, B30): a harness wire, not a jumper
                tails.append(dict(x=cx + sd * 3.0, y=y, awg=S.MINI_AWG[amps], what=nm + ' in', lane=lane))
        for (nm, pn, own, cx, cy, k_) in micro:
            if not pn:
                continue
            for (u, v, awg, tn) in ((0, -8.0, S.MICRO_LOAD_AWG, '30'), (0, 8.0, S.MICRO_LOAD_AWG, '87'), (0, 0, S.MICRO_LOAD_AWG, '87a'),
                                    (-4.5, 0, S.COIL_AWG, '85'), (4.5, 0, S.COIL_AWG, '86')):
                if tn == '87a' and pn in ('5-1393292-8', '4-1904124-3', '4-1904124-2'):
                    continue                                     # NO relays: no 87a contact
                if '%s %s' % (nm, tn) in skip or (tn == '87a' and REV[0] == 7):
                    continue                                     # rev 7: no harness wire on any 87a (wiring_plan.json)
                tails.append(dict(x=cx + u, y=cy + v, awg=awg, what='%s %s' % (nm, tn), lane=cx))
        exits = harness_tails(tails, lambda t_: t_['lane'], z_d, 'y', 0.0, pre, sh, 'LOGIC')
        pan_exits = [('y', u, zb_, wd, -1) for (u, zb_, wd) in exits] + pan_feed
        if REV[0] == 7:   # J2 = B (R94): rib between the Bus 1 output wires and the Bus 1 strip bolt heads; reliefs at the outboard relay column
            belly_pan(L, z_d, 'x', pan_exits, pre, sh, rib=(S.PAN_RIB['x'][0], S.PAN_RIB['x'][1], S.PAN_RIB['y'][0], S.PAN_RIB['y'][1], S.PAN_RIB['z_top']),
                      reliefs=[(cy - S.PAN_RELIEF['fwd'], cy + S.PAN_RELIEF['back'], S.PAN_RELIEF['depth']) for cy in S.MICRO_Y])
        else:
            belly_pan(L, z_d, 'x', pan_exits, pre, sh)
        bend_row('LOGIC fuse / micro relay receptacles, largest %d AWG' % S.LOGIC_MAX_AWG, S.LOGIC_MAX_AWG, 'straight down out of the cavity, one bend into its bundle (rows above)',
                 3.0 * S.OD[S.LOGIC_MAX_AWG], True, 'one bundle per fuse column / relay column, straight to the front edge')

        z_top = z_t + 25.4 + CV['clear'] + CV['t']          # micro relay 25.4 max (TE 1308028)
        short = {'HEAD LH': 'HEAD L', 'HEAD RH': 'HEAD R', 'horn': 'HORN', 'k_etb': 'ETB', 'k_acc': 'A/C', 'k_eps_en': 'EPS EN', 'k_rev': 'REV', 'SPARE': 'SPARE'}
        labels = [(short[nm], cx, cy, S.LABEL['h_micro']) for (nm, pn, own, cx, cy, k_) in micro]           # rev 4 etched names, unchanged
        labels += [(('%s %s' % (nm, ('%g' % amps))) if amps else 'SP', cx, y, S.LABEL['h_mini']) for (col, nm, amps, cx, y, n_, i) in mini]
        labels += [(col, cx, S.MINI_Y0 - 11.0, S.LABEL['h_mini']) for col, (cx, fuses) in S.MINI_COLS.items()]
        xm_ = sum(S.MICRO_COLS) / 2                     # between the micro relay columns (rev 6: 58.25)
        labels.append(('LOGIC', xm_, 168.0, 5.0))
        vents = [(x, y, 'y') for x in (spx, xm_) for y in (30.0 + k * S.VENT['pitch'] for k in range(7))]    # clear of the labels
        cover(L, S.D, z_t, z_top, [], labels, pre, sh, vents=vents, ribs={'y': [spx], 'x': [20.0, 50.0, 80.0, 110.0, 140.0, 165.0]})
        return dict(L=L, D=S.D, H=z_top, z_d=z_d, z_t=z_t, cover_top=z_top, feet=feet, spine_x=spx)

    # ================================================================== battery relay block (trunk)
    def build_relay_block():
        R, H_ = S.RB, S.HCR
        pre = 'BattRelay_'
        sh = S.PLACE['BATTRELAY']
        Lr, Dr, fl = R['L'], R['D'], R['floor']
        zf = 10.0                                          # relay flange face (raised 6 on bosses: captured nut + limiter under it)
        tz0, tz1 = zf + 10.0, zf + 30.0                    # terminal blocks (TE side view: 10 back from the flange face, 20 tall)
        x3 = R['x_t3']
        rx = x3 + H_['term_pitch'] / 2
        xs = (x3, x3 + H_['term_pitch'])                   # terminal 3 (fused feed), terminal 5 (pump)
        yb = R['y_b']
        tsy = yb - H_['term_to'] / 2                        # the power line
        hxs = (rx - H_['holes'] / 2, rx + H_['holes'] / 2)
        fy = yb + H_['hole_z']
        Bb = R['bar']
        btop = tz1 - S.AMI['ear_t']                         # AMI ear top = terminal top: the jumper lug lies at the terminal height
        bz0 = btop - Bb['t']
        pz0 = btop - S.PAD['t']
        a_in, a_out = R['x_ami_in'], R['x_ami_in'] + S.AMI['c']
        xst = R['x_stud']
        LM = R['lim_m6']
        parts, lims = [], []
        # ---- base: rounded floor plate, low rim on the long sides only (ends open), relay platform, ONE fuse pedestal, 2 END tabs
        base = rrect(0, 0, Lr, Dr, 0, fl, 10.0)
        rim = rrect(0, 0, Lr, Dr, fl - 0.01, R['rim'], 10.0)
        bo(rim, rrect(3, 3, Lr - 3, Dr - 3, 0, R['rim'] + 1, 7.0), 's')
        bo(rim, box(-1, 16.0, 0, 22.0, Dr - 16.0, R['rim'] + 1), 's')            # open -x end
        bo(rim, box(Lr - 22.0, 16.0, 0, Lr + 1, Dr - 16.0, R['rim'] + 1), 's')   # open +x end
        parts += [rim]
        px0, px1 = rx - H_['body_x'] / 2, rx + H_['body_x'] / 2
        plat = box(hxs[0] - 8.0, yb, fl - 0.01, hxs[1] + 8.0, yb + H_['body_y'], zf)          # relay platform: perimeter + ribs
        bo(plat, box(hxs[0] - 8.0 + 2.5, yb + 2.5, fl, hxs[1] + 8.0 - 2.5, yb + H_['body_y'] - 2.5, zf + 1), 's')
        parts.append(plat)
        for x in (px0 + 15.0, rx, px1 - 15.0):
            parts.append(box(x - S.RIB / 2, yb, fl - 0.01, x + S.RIB / 2, yb + H_['body_y'], zf))
        for x in hxs:
            parts.append(cylz(x, fy, fl - 0.01, zf, 18.0))
        # fuse pedestal (rev 5: the bar's and the pad's risers joined into one ribbed block - point 8 asked what they were)
        pw = Bb['w'] / 2 + 1.0
        ped = box(Bb['x0'] - 1.0, tsy - pw, fl - 0.01, a_out + S.PAD['outer'] + 1.0, tsy + pw, bz0)
        bo(ped, box(Bb['x0'] + 1.5, tsy - pw + 2.5, fl, a_out + S.PAD['outer'] - 1.5, tsy + pw - 2.5, bz0 + 1), 's')
        parts.append(ped)
        for y in (tsy - Bb['w'] / 2 + 1.25, tsy, tsy + Bb['w'] / 2 - 1.25):              # ribs under bar + pad
            parts.append(box(Bb['x0'], y - S.RIB / 2, fl - 0.01, Bb['x1'], y + S.RIB / 2, bz0))
            parts.append(box(a_out - S.PAD['inner'], y - S.RIB / 2, fl - 0.01, a_out + S.PAD['outer'], y + S.RIB / 2, pz0))
        for x in (a_out - S.PAD['inner'], a_out + S.PAD['outer'] - S.RIB):
            parts.append(box(x, tsy - S.PAD['w'] / 2, fl - 0.01, x + S.RIB, tsy + S.PAD['w'] / 2, pz0))
        rb_bolts = [(xst, 6, bz0), (a_in, 5, bz0), (a_out, 5, pz0)]
        for (px, m, zu) in rb_bolts:
            parts.append(cylz(px, tsy, fl - 0.01, zu, HD[m]['af'] / math.cos(math.radians(30)) + 2 * S.CLR + 5.0))
        tabs = []
        for face in ('-x', '+x'):                                                   # rev 5: tabs on the SHORT ends (point 3)
            mp, nv, tv = face_map(face, Lr, Dr)
            u = R['tab_y']
            fo, fw = LG['ear_len'] + 6.0, LG['ear_w'] / 2
            tab = sbox(mp, -6.0, fo, u - fw - 4.0, u + fw + 4.0, 0.0, LG['ear_t'])
            for sg in (-1, 1):                                                      # angular plan: tapered sides
                qx, qy = mp(0.0, u + sg * (fw + 4.0))
                ax_, ay_ = mp(fo, u + sg * fw)
                dxs, dys = ax_ - qx, ay_ - qy
                nx_, ny_ = (-dys, dxs) if sg * (tv[0] * (-dys) + tv[1] * dxs) > 0 else (dys, -dxs)
                half_cut(tab, (qx, qy, 0.0), (nx_, ny_, 0.0))
            ex_, ey_ = mp(fo, u)
            half_cut(tab, (ex_, ey_, LG['ear_t'] - 2.0), (nv[0], nv[1], 1.0))      # chamfered end
            hx, hy = mp(fo - 8.0, u)
            bo(tab, cylz(hx, hy, -1, LG['ear_t'] + 1, LG['hole']), 's')
            parts.append(tab)
            tabs.append((hx, hy))
            lims.append(bo(cylz(hx, hy, 0, l6['l'], l6['od']), cylz(hx, hy, -1, l6['l'] + 1, l6['id']), 's'))
        base = union_all([base] + parts)
        cuts = []
        zl0 = zf - LM['l']
        for x in hxs:                                   # flange bolt: limiter (EFC 10S00052, L 4) under the flange, M6 nut captured from below
            cuts.append(cylz(x, fy, zl0, zf + 1, LM['od'] + 2 * S.CLR))
            cuts.append(hexz(x, fy, -1, zl0, 10.0 + 2 * S.CLR))
            lims.append(bo(cylz(x, fy, zl0, zf, LM['od']), cylz(x, fy, zl0 - 0.1, zf + 1, LM['id']), 's'))
        for (px, m, zu) in rb_bolts:                    # bolt heads captured in hex pockets under the copper (dropped in from the top)
            cuts.append(hexz(px, tsy, zu - HD[m]['k'] - 0.3, zu + 0.01, HD[m]['af'] + 2 * S.CLR))
        for x in snap_xs(Lr):
            for y in (0.0, Dr):
                cuts.append(cyl((x - S.SNAP['w'] / 2 - 0.5, y, R['rim'] - 3.0), (x + S.SNAP['w'] / 2 + 0.5, y, R['rim'] - 3.0), S.SNAP['bump'] + 0.2))
        sub_all(base, cuts)
        comp(pre + 'Base_PA12_printed', base, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_steel_M6', lims, AP['al'], MAT['ss'], sh)
        # ---- HCR150 envelope from the TE drawing
        rel = box(px0, yb, zf, px1, yb + H_['body_y'], zf + H_['depth'])
        flg = box(hxs[0] - 8.0, fy - 9.0, zf, hxs[1] + 8.0, fy + 9.0, zf + H_['flange_t'])
        for x in hxs:
            bo(flg, cylz(x, fy, zf - 1, zf + H_['flange_t'] + 1, H_['hole_d']), 's')
        bo(rel, flg, 'u')
        for x in xs:
            tbk = box(x - H_['term_w'] / 2, yb - H_['term_to'], tz0, x + H_['term_w'] / 2, yb + 0.01, tz1)
            bo(tbk, cylz(x, tsy, tz1 - 8.0, tz1 + 0.1, 5.0), 's')
            bo(rel, tbk, 'u')
        gcx = px0 + 8.0
        comp(pre + 'Relay_TE_HCR150_1416010-1', rel, AP['black'], MAT['abs'], sh)
        comp(pre + 'CoilPlug_TE_Superseal_282080-1', box(gcx - 5.0, yb - H_['plug_to'], tz0, gcx + 5.0, yb - 0.05, tz0 + 9.0), AP['black'], MAT['abs'], sh)
        # ---- copper + fuse + hardware
        bar = box(Bb['x0'], tsy - Bb['w'] / 2, bz0, Bb['x1'], tsy + Bb['w'] / 2, btop)
        bo(bar, cylz(xst, tsy, bz0 - 1, btop + 1, 6.5), 's')
        bo(bar, cylz(a_in, tsy, bz0 - 1, btop + 1, 5.5), 's')
        pad = box(a_out - S.PAD['inner'], tsy - S.PAD['w'] / 2, pz0, a_out + S.PAD['outer'], tsy + S.PAD['w'] / 2, btop)
        bo(pad, cylz(a_out, tsy, pz0 - 1, btop + 1, 5.5), 's')
        comp(pre + 'Bar_Power_%s_25x6p35' % BM['name'], bar, AP['tin'], MAT['cu'], sh)
        comp(pre + 'Pad_Out_%s_15x3' % BM['name'], pad, AP['tin'], MAT['cu'], sh)
        fe = slot_x(a_in, a_out, tsy, btop, btop + S.AMI['ear_t'], S.AMI['ear_w'])
        for x in (a_in, a_out):
            bo(fe, cylz(x, tsy, btop - 1, btop + 2, S.AMI['hole']), 's')
        ze = btop + S.AMI['ear_t'] / 2
        fb = cbox((a_in + a_out) / 2, tsy, ze - S.AMI['body_h'] / 2, ze + S.AMI['body_h'] / 2, S.AMI['body_l'], S.AMI['body_w'])
        bo(fb, fe, 'u')
        comp(pre + 'Fuse_AMI_ltgreen', fb, AP['ltgreen'], MAT['abs'], sh)
        lug_z = btop + S.AMI['ear_t']                    # = tz1
        comp(pre + 'BarBolt_M5_M6_ISO4017_A2', [union_all([hexz(px, tsy, zu - HD[m]['k'], zu, HD[m]['af']), cylz(px, tsy, zu, btop + 12.0, float(m))]) for (px, m, zu) in rb_bolts],
             AP['al'], MAT['ss'], sh)
        comp(pre + 'FlangeBolt_M6_ISO4017_A2', [union_all([hexz(x, fy, zf + H_['flange_t'], zf + H_['flange_t'] + 4.0, 10.0), cylz(x, fy, 0.5, zf + H_['flange_t'], 6.0)]) for x in hxs],
             AP['al'], MAT['ss'], sh)
        nuts = [hexz(a_in, tsy, lug_z, lug_z + S.M5_NUT['h'], S.M5_NUT['af']), hexz(a_out, tsy, lug_z + 2.0, lug_z + 2.0 + S.M5_NUT['h'], S.M5_NUT['af']),
                hexz(xst, tsy, btop + 2.0, btop + 2.0 + 5.2, 10.0)] + [hexz(x, fy, zl0 - 5.4, zl0 - 0.2, 10.0) for x in hxs]
        comp(pre + 'Nut_M5_M6_A2', nuts, AP['al'], MAT['ss'], sh)
        # ---- lugs + cables, all on the power line y = tsy, all straight
        lugs, wires = [], []
        odf, odp, odc = S.OD[R['awg_feed']], S.OD[R['awg_pump']], S.OD[R['awg_coil']]
        t, e_in = ring_lug(xst, tsy, btop, 13.0, 6.5, 2.0, 7.0, (-1, 'x'), 16.0)
        lugs.append(t)
        wires.append(cyl(e_in, (-30.0, tsy, e_in[2]), odf))
        t, e1 = ring_lug(a_out, tsy, lug_z, 12.0, 5.5, 2.0, 7.0, (1, 'x'), 16.0)
        lugs.append(t)
        t, e2 = ring_lug(xs[0], tsy, tz1, 12.0, 6.5, 2.0, 7.0, (-1, 'x'), 16.0)
        lugs.append(t)
        wires.append(cyl(e1, e2, odf))
        t, e3 = ring_lug(xs[1], tsy, tz1, 12.0, 6.5, 2.0, 7.0, (1, 'x'), 16.0)
        lugs.append(t)
        wires.append(cyl(e3, (Lr + 30.0, tsy, e3[2]), odp))
        cy_ = yb - H_['plug_to']                         # coil leads: out of the plug toward -y, one turn to +x, along the front to the +x end
        rcl = 7.0
        yl, zl = cy_ - rcl - 1.0, tz0 + 4.5
        coil_w = []
        for k in range(R['n_coil']):                     # 119 (b): two 18 AWG leads side by side, bends on one centre (nested)
            dk = (k - (R['n_coil'] - 1) / 2) * (odc + 0.4)
            xk, rk = gcx + dk, rcl - dk
            cw = cyl((xk, cy_, zl), (xk, yl + rcl, zl), odc)
            tq = torus(gcx + rcl, yl + rcl, zl, V(0, 0, 1), rk, odc / 2)
            bo(tq, box(xk - odc, yl + rcl - rk - odc, zl - odc, gcx + rcl, yl + rcl, zl + odc), 'i')
            bo(cw, tq, 'u')
            bo(cw, cyl((gcx + rcl, yl + rcl - rk, zl), (Lr + 30.0, yl + rcl - rk, zl), odc), 'u')
            coil_w.append(cw)
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_feed', wires, AP['wire'], None, sh)
        comp(pre + 'Wire_coil', coil_w, AP['harness'], None, sh)
        bend_row('BATTERY feed in (kill switch load side) -> M6 stud', R['awg_feed'], 'straight in at the open -x end, lug axis', None, False,
                 'no bend in the block; first bend outside >= %.0f supported / >= %.0f free' % (3 * odf, 10 * odf))
        bend_row('BATTERY AMI 40 out -> HCR150 terminal 3', R['awg_feed'], 'one straight jumper, both lugs at the terminal height', None, True,
                 'no bend (the fuse pedestal puts its lug level with terminal 3)')
        bend_row('BATTERY HCR150 terminal 5 -> pump', R['awg_pump'], 'straight out the open +x end, lug axis', None, False,
                 'no bend in the block; first bend outside >= %.0f supported / >= %.0f free' % (3 * odp, 10 * odp))
        bend_row('BATTERY coil leads (Superseal plug, %d x %d AWG) -> Link Aux 3' % (R['n_coil'], R['awg_coil']), R['awg_coil'],
                 'one 90 deg turn, then along the front to the +x end', round(rcl - (R['n_coil'] - 1) / 2 * (odc + 0.4) - odc / 2, 1), True,
                 'held by the plug and the cover notch; 3 x OD = %.1f' % (3 * odc))
        # ---- cover: Blue Sea 7720-style low pillow, end breakouts only; rev 5: band, ribs, side vents, plain words
        z_top = zf + H_['depth'] + CV['clear'] + CV['t']
        notches = [('x', -W_CL - CV['t'] / 2, tsy, e_in[2] + odf / 2 + 2.0, 9.0), ('x', Lr + W_CL + CV['t'] / 2, tsy, e3[2] + odp / 2 + 2.0, 9.0),
                   ('x', Lr + W_CL + CV['t'] / 2, yl, zl + odc / 2 + 1.5, 5.0)]
        labels = [('BATT +', xst, tsy + 20.0, 4.5), ('FP 40A', (a_in + a_out) / 2, tsy, 4.0), ('K_FP  FUEL PUMP', rx, yb + 26.0, 5.0),   # rev 4 labels, unchanged
                  ('3', xs[0], tsy, 4.0), ('5', xs[1], tsy, 4.0), ('PUMP', Lr - 16.0, tsy + 20.0, 4.5), ('COIL', Lr - 16.0, yl + 8.0, 3.5)]
        zv = (6.5 + S.RUG['band_h'] + z_top - 6.0) / 2
        side_vents = [(f, u, z_) for f in ('-y', '+y') for u in (66.0, 84.0, 102.0, 120.0) for z_ in (zv - 4.0, zv + 4.0)]
        oc = cover(Lr, Dr, R['rim'], z_top, notches, labels, pre, sh, side_vents=side_vents, R=12.95, r=6.0, zb=LG['ear_t'] + 0.5,
                   zc=R['rim'] - 3.0, inner_R=10.45, inner_r=3.5, ribs={'y': [22.0, Lr - 22.0], 'x': [50.0, 80.0]})
        return dict(L=Lr, D=Dr, H=z_top, L_with_tabs=Lr + 2 * (LG['ear_len'] + 6.0), D_with_tabs=Dr, tabs=tabs,
                    parts=dict(bar=((Bb['x0'] + Bb['x1']) / 2, tsy, btop), pad=(a_out + 2.0, tsy, btop), fuse=((a_in + a_out) / 2, tsy, btop + 4),
                               ped=(30.0, tsy - pw, bz0 - 8.0), relay=(rx, yb + 22.0, zf + 40.0), plug=(gcx, yb - H_['plug_to'] + 2, tz0 + 9.0)))

    sizes = {'LOGIC': build_logic(), 'POWER': build_power(), 'BATTRELAY': build_relay_block()}

    # ------------------------------------------------------------------ checks
    mm = app.measureManager

    def dist(b1, b2):
        return round(mm.measureMinimumDistance(b1, b2).value * 10, 2)

    def bodies(name):
        return [b for o in root.occurrences if o.component.name.startswith(name) for b in o.bRepBodies]

    pad_bs = bodies('Power_Pad_')
    keys = sorted(pad_bs, key=lambda b: (round(b.boundingBox.minPoint.x), b.boundingBox.minPoint.y))
    neigh = [dist(p1, p2) for i_, p1 in enumerate(keys) for p2 in keys[i_ + 1:]
             if abs(p1.boundingBox.minPoint.x - p2.boundingBox.minPoint.x) < 0.5 and abs(p1.boundingBox.minPoint.y - p2.boundingBox.minPoint.y) < 2.0]
    lug_bs = bodies('Power_Lug_Klauke')
    bus_lugs = bodies('Power_Lug_Bus')
    if bus_lugs:          # rev 7: the 1/0 lugs are the bus terminals; every Lug_Klauke is under the deck
        in_lugs, out_lugs = bus_lugs, lug_bs
    else:
        in_lugs = [max(lug_bs, key=lambda lb: lb.volume)]
        out_lugs = [lb for lb in lug_bs if lb is not in_lugs[0]]
    so = bodies('Power_Standoff_')
    rb_lugs = bodies('BattRelay_Lug_')
    report['live_clearance'] = {
        'pad_to_pad_min_mm': min(neigh),
        'bar_to_pad_min_mm': min(dist(bodies('Power_Bar_')[0], pb) for pb in pad_bs),
        'input_lug_to_pad_min_mm': min(dist(il, pb) for il in in_lugs for pb in pad_bs),
        'under_deck_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(out_lugs) for l2 in out_lugs[i_ + 1:]),
        'standoff_to_standoff_min_mm': min(dist(s1, s2) for i_, s1 in enumerate(so) for s2 in so[i_ + 1:]),
        'logic_strip_to_strip_mm': dist(*bodies('Logic_Strip_')[:2]),
        'logic_feed_lug_to_lug_mm': dist(*bodies('Logic_Lug_Klauke')[:2]),
        'battrelay_bar_to_pad_mm': dist(bodies('BattRelay_Bar_')[0], bodies('BattRelay_Pad_')[0]),
        'battrelay_relay_lug_to_lug_mm': dist(rb_lugs[2], rb_lugs[3]),
        'pan_to_nearest_live_power_mm': min(dist(bodies('Power_Pan_')[0], b) for b in bodies('Power_LugBolt_') + bodies('Power_Lug_') + bodies('Power_Standoff_')),
    }
    if bus_lugs:          # rev 7 bus zone: lug to lug on each bar (Dan's 3 mm), NEG parts to POS parts, to the barrier
        pos_live = bodies('Power_Lug_BusPos') + bodies('Power_Bar_Power')
        neg_live = bodies('Power_Lug_BusNeg') + bodies('Power_BarNeg_')
        bp_, bn_ = bodies('Power_Lug_BusPos'), bodies('Power_Lug_BusNeg')
        report['live_clearance'].update({
            'bus_pos_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(bp_) for l2 in bp_[i_ + 1:]),
            'bus_neg_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(bn_) for l2 in bn_[i_ + 1:]),
            'bus_neg_to_pos_min_mm': min(dist(a_, b_) for a_ in neg_live for b_ in pos_live),
            'bus_pos_lug_to_out_pad_min_mm': min(dist(l1, pb) for l1 in bp_ for pb in pad_bs),
        })
    # rev 6 (C4): the jumper lugs - lug to lug on each strip (Dan's 3 mm), every jumper part to plastic and to the harness wires
    jl_bs = bodies('Logic_Lug_TE_PIDG')
    jpart = jl_bs + bodies('Logic_LugBolt_') + bodies('Logic_Washer_') + bodies('Logic_Lug_Klauke')
    jprinted = bodies('Logic_Base_') + bodies('Logic_Pan_')
    strip_bs = bodies('Logic_Strip_')
    spx0_ = sizes['LOGIC']['spine_x'] + S.PLACE['LOGIC'][0]
    side_ = lambda b_: (b_.boundingBox.minPoint.x + b_.boundingBox.maxPoint.x) * 5 < spx0_
    report['live_clearance'].update({
        # J1 = A (R94): the lugs on one strip are one circuit - same-strip pairs only (Bus 1 to Bus 2 is logic_bus1_to_bus2_min_mm)
        'logic_jumper_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(jl_bs) for l2 in jl_bs[i_ + 1:] if side_(l1) == side_(l2)),
        'logic_jumper_parts_to_printed_min_mm': min(dist(jp, pb) for jp in jpart for pb in jprinted),
        'logic_jumper_parts_to_harness_min_mm': min(dist(jp, hb) for jp in jpart + bodies('Logic_Wire_') for hb in bodies('Logic_Harness_')),
        'logic_strip_to_printed_min_mm': min(dist(sb, pb) for sb in strip_bs for pb in jprinted),
        'logic_bolt_to_other_strip_min_mm': min(sorted(dist(bb, sb) for sb in strip_bs)[1] for bb in bodies('Logic_LugBolt_')),
    })
    # rev 7 (3 mm gate): every Bus 1 live part against every Bus 2 live part (sides of the spine)
    spx_ = sizes['LOGIC']['spine_x'] + S.PLACE['LOGIC'][0]
    lg_live = strip_bs + bodies('Logic_LugBolt_') + bodies('Logic_Washer_') + bodies('Logic_Lug_TE') + bodies('Logic_Lug_Klauke')
    xc_ = lambda b_: (b_.boundingBox.minPoint.x + b_.boundingBox.maxPoint.x) * 5
    b1_, b2_ = [b_ for b_ in lg_live if xc_(b_) < spx_], [b_ for b_ in lg_live if xc_(b_) >= spx_]
    report['live_clearance']['logic_bus1_to_bus2_min_mm'] = min(dist(a_, c_) for a_ in b1_ for c_ in b2_)
    if REV[0] == 7:   # J2 / J4 (R94): the new printed parts against the live LOGIC parts (information: live to plastic)
        pan_b = bodies('Logic_Pan_')
        report['live_clearance']['logic_pan_rib_to_live_min_mm'] = min(dist(pb, lb) for pb in pan_b for lb in lg_live)
        report['live_clearance']['logic_base_to_live_min_mm'] = min(dist(bb, lb) for bb in bodies('Logic_Base_') for lb in lg_live)
    # every cable (feed and harness) against every printed part (a wire through plastic = a bad route)
    wire_hits = []
    for wpre in ('Power_', 'Logic_', 'BattRelay_'):
        for wb in bodies(wpre + 'Wire_') + bodies(wpre + 'Harness_'):
            for pb in bodies(wpre + 'Base_') + bodies(wpre + 'Cover_') + bodies(wpre + 'Pan_'):
                d = dist(wb, pb)
                if d <= 0.0:
                    wire_hits.append((wb.parentComponent.name, pb.parentComponent.name, d))
    report['wire_to_printed_contact'] = wire_hits
    printed = {}
    for o in root.occurrences:
        n = o.component.name
        if n.endswith('_printed'):
            ob = mm.getOrientedBoundingBox(o.bRepBodies.item(0), V(1, 0, 0), V(0, 1, 0))
            vol = sum(b.volume for b in o.bRepBodies)
            printed[n] = dict(size_mm=[round(ob.length * 10, 1), round(ob.width * 10, 1), round(ob.height * 10, 1)], volume_cm3=round(vol, 1),
                              mass_g_pa12=round(vol * 1.01, 0), bodies=o.bRepBodies.count,
                              lumps=sum(b.lumps.count for b in o.bRepBodies),          # R101: one lump = nothing floating (check_printed_solid.py)
                              shells=sum(l_.shells.count for b in o.bRepBodies for l_ in b.lumps))
    report['printed_parts'] = printed
    report['boxes_mm'] = {k: {kk: round(vv, 1) for kk, vv in v.items() if isinstance(vv, (int, float))} for k, v in sizes.items()}
    report['bar_metal'] = S.BAR_METAL
    coll = adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        nm = o.component.name.split('_', 1)[1]
        if not nm.startswith(('Wire_', 'Harness_', 'BarBolt_', 'SetScrew_', 'LugBolt_', 'StripBolt_', 'FlangeBolt_', 'Nut_', 'Lug_', 'Standoff_', 'Limiter_')):
            coll.add(o)
    try:
        ir = design.analyzeInterference(design.createInterferenceInput(coll))
        report['interference'] = [(r.entityOne.parentComponent.name if hasattr(r.entityOne, 'parentComponent') else str(r.entityOne),
                                   r.entityTwo.parentComponent.name if hasattr(r.entityTwo, 'parentComponent') else str(r.entityTwo),
                                   round(r.interferenceBody.volume * 1000, 3)) for r in ir]
    except Exception as ex:   # report, do not hide
        report['interference_error'] = str(ex)
    report['mass_g'] = {o.component.name: round(o.component.physicalProperties.mass * 1000, 1) for o in root.occurrences
                        if o.component.name.split('_', 1)[1].startswith(('Bar_', 'BarNeg_', 'Pad_', 'Strip_'))}

    # ------------------------------------------------------------------ exports
    em = design.exportManager
    exported = []
    for o in root.occurrences:
        n = o.component.name
        if REV[0] == 7 and n.startswith('BattRelay_'):   # rev 7: battery block part files are rev 6's (unchanged); LOGIC is re-exported (clearance fix)
            continue
        if n.endswith('_printed') or n.split('_', 1)[1].startswith(('Bar_', 'BarNeg_', 'Pad_', 'Strip_')):
            p = os.path.join(out_dir, '%s.step' % n)
            em.execute(em.createSTEPExportOptions(p, o.component))
            exported.append(os.path.basename(p))
        if n.endswith('_printed'):
            p = os.path.join(out_dir, '%s.stl' % n)
            so_ = em.createSTLExportOptions(o, p)
            so_.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(so_)
            exported.append(os.path.basename(p))
    p = os.path.join(out_dir, '%s_assembly.step' % doc_name())
    em.execute(em.createSTEPExportOptions(p, root))
    exported.append(os.path.basename(p))
    em.execute(em.createFusionArchiveExportOptions(os.path.join(out_dir, '%s.f3d' % doc_name())))
    exported.append('%s.f3d' % doc_name())
    report['exported'] = exported

    if renders:
        render_all(out_dir, root, report, sizes)

    if save and REV[0] == 7:   # rev 7: its own document (rev 6 stays as saved); save-as the first time, R74 slot check done (2 of 10 editable)
        if doc.dataFile.name == DOC7:
            doc.save('rev 7: R101 tightened - only the floating pieces Dan marked joined (5 LOGIC guide walls, 6 POWER saddles) (Claude Code 2026-10-15)')
        else:
            doc.saveAs(DOC7, doc.dataFile.parentFolder, 'rev 7: E2 = A - AMI fuses on the bus bar POS bar, NEG bar in the bus zone (Claude Code 2026-10-14)', '')
            report['saved_as'] = DOC7
    elif save:
        try:
            if doc.dataFile.name != DOC:
                doc.dataFile.name = DOC
                report['renamed_document_to'] = DOC
        except Exception as ex:   # report, do not hide
            report['rename_error'] = str(ex)
        doc.save('rev 6: Dan parts answers - M6 limiters (C1), mini fuse input jumpers on bus strips on edge (C4), one 40 mm standoff (B5) (Claude Code 2026-10-14)')
    with open(os.path.join(out_dir, 'fusebox_report.json'), 'w') as f:
        json.dump(report, f, indent=1)
    return report


# ====================================================================== renders
IMG_W = 1800


def render_all(out_dir, root, report, sizes):
    vp = app.activeViewport
    VO = adsk.core.ViewOrientations
    k_img = IMG_W / float(vp.width)
    img_h = int(round(vp.height * k_img))
    report['image_size'] = [IMG_W, img_h]

    def kind(n):
        return n.split('_', 1)[1]

    def show(pred):
        for o in root.occurrences:
            o.isLightBulbOn = bool(pred(o.component.name))

    def place(offsets):
        """offsets = {name -> (dx, dy, dz) mm}; every other occurrence back to identity."""
        for o in root.occurrences:
            m = adsk.core.Matrix3D.create()
            d = offsets.get(o.component.name)
            if d:
                m.translation = V(d[0] / 10.0, d[1] / 10.0, d[2] / 10.0)
            o.transform2 = m

    def shot(fn, eye=None, target=(150.0, 60.0, 30.0), orient=None, callouts=None):
        cam = vp.camera
        if eye is not None:
            cam.target = P(*target)
            cam.eye = P(target[0] + eye[0], target[1] + eye[1], target[2] + eye[2])
            cam.upVector = V(0, 0, 1)
        else:
            cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()
        vp.saveAsImageFile(os.path.join(out_dir, fn), IMG_W, img_h)
        if callouts:
            pts = []
            for (num, pt, text) in callouts:
                p2 = vp.modelToViewSpace(P(*pt))
                pts.append([num, round(p2.x * k_img, 1), round(p2.y * k_img, 1), text])
            report['callouts'][fn] = pts

    def occ_center(name, top=False):
        o = [x for x in root.occurrences if x.component.name == name]
        if not o:
            return None
        bb = o[0].boundingBox
        c = [(bb.minPoint.x + bb.maxPoint.x) * 5, (bb.minPoint.y + bb.maxPoint.y) * 5, (bb.minPoint.z + bb.maxPoint.z) * 5]
        if top:
            c[2] = bb.maxPoint.z * 10
        return tuple(c)

    def names(prefix, *kinds):
        return [o.component.name for o in root.occurrences if o.component.name.startswith(prefix) and (not kinds or kind(o.component.name).startswith(kinds))]

    LOADED = lambda n: not kind(n).startswith(('Cover', 'Pan'))
    EMPTY = lambda n: kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'Strip', 'Standoff'))
    GLOVE = lambda n: not n.startswith('BattRelay_')
    BATT = lambda n: n.startswith('BattRelay_')
    place({})
    iso = dict(eye=(-300, -480, 380), target=(170.0, 90.0, 30.0))
    show(GLOVE)
    shot('fusebox_render_iso_closed.png', **iso)
    shot('fusebox_render_iso_closed_rear.png', eye=(320, 480, 300), target=(170.0, 90.0, 30.0))
    show(lambda n: GLOVE(n) and LOADED(n))
    shot('fusebox_render_iso_open.png', **iso)
    show(lambda n: GLOVE(n) and EMPTY(n))
    shot('fusebox_render_iso_empty.png', **iso)
    shot('fusebox_render_top_empty.png', orient=VO.TopViewOrientation)
    show(lambda n: n.startswith('Power_') and not kind(n).startswith('Pan'))
    shot('fusebox_render_top_lid_power.png', orient=VO.TopViewOrientation)
    show(lambda n: n.startswith('Logic_') and not kind(n).startswith('Pan'))      # rev 7: LOGIC re-rendered (clearance fix); battery block stays rev 6's
    shot('fusebox_render_top_lid_logic.png', orient=VO.TopViewOrientation)
    show(GLOVE)
    shot('fusebox_render_under_pan.png', eye=(-260, -420, -260), target=(170.0, 90.0, 20.0))
    show(lambda n: GLOVE(n) and not kind(n).startswith('Pan'))
    shot('fusebox_render_under_open.png', eye=(-260, -420, -260), target=(170.0, 90.0, 20.0))
    WIRING = lambda n: kind(n).startswith(('Wire', 'Harness', 'Lug', 'Bar', 'Pad', 'Strip', 'Standoff', 'Relay', 'Fuse', 'SPARE', 'LugBolt', 'Washer'))
    PX = S.PLACE['POWER'][0]
    show(lambda n: n.startswith('Power_') and WIRING(n))
    shot('fusebox_render_routing_power.png', eye=(-200, -330, -200), target=(PX + 90.0, 90.0, 25.0), callouts=[
        (1, (PX + 10.0, 52.0, 8.0), 'harness bundles to the inboard edge'), (2, (PX + 92.25, 61.0, 10.0), 'relay feed: lug on the 40 mm standoff'),
        (3, (PX + 62.0, 61.0, 20.0), 'feed bends up R16 into terminal 30'), (4, (PX + 164.75, 97.0, 11.0), 'OUT lug on the 40 mm standoff'),
        (5, (PX + S.POWER['L'] + 20.0, 97.0, 13.0), 'OUT cables straight out the end'), (6, (PX + S.POWER['L'] + 20.0, sizes['POWER']['in_y'], S.POWER['bar_top'] + 8.0), '1/0 battery feed in')]
        + ([(7, (PX + 50.0, S.REV7['neg_bar']['yc'] + 40.0, S.POWER['bar_top'] + 8.0), 'NEG bus: grounds straight out the rear')] if REV[0] == 7 else []))
    show(lambda n: n.startswith('Logic_') and WIRING(n))
    c1, c2 = S.MINI_COLS['BUS1'][0], S.MINI_COLS['BUS2'][0]
    shot('fusebox_render_routing_logic.png', eye=(-230, -330, -200), target=(40.0, 90.0, 20.0), callouts=[
        (1, (c1 - 3.0, 60.0, 8.0), 'Bus 1 fuse wires'), (2, (c2 + 3.0, 60.0, 8.0), 'Bus 2 fuse wires'), (3, (S.MICRO_COLS[0], 40.0, 10.0), 'micro relay wires, inboard column'),
        (4, (S.MICRO_COLS[1], 40.0, 10.0), 'micro relay wires, outboard column'), (5, (40.0, -20.0, 8.0), 'all leave the front edge'),
        (6, (c1 + 3.0, 52.1, 28.0), 'fuse input jumpers drop straight into their lugs'), (7, ((c1 + c2) / 2, 70.0, 30.0), 'bus strips on edge, printed spine between'),
        (8, (c1 + 2.15, -15.0, 22.0), 'Bus 1 feed in at the front'), (9, (c2 - 2.15, S.D + 15.0, 13.0), 'Bus 2 feed in at the rear')])
    show(lambda n: n.startswith('Power_') and kind(n).startswith(('Base', 'Wire', 'Lug', 'Standoff', 'LugBolt', 'Limiter', 'Harness')))
    shot('fusebox_render_power_bends.png', eye=(-120, -330, -150), target=(PX + 70.0, 80.0, 15.0))

    # ---- exploded / install steps, POWER (point 4)
    pw = 'Power_'
    ex_p = {}
    for n in names(pw):
        kd = kind(n)
        dz = {'Cover': 270, 'Relay': 185, 'SPARE': 185, 'Fuse_ATM': 185, 'Fuse_AMI': 125, 'Nut': 150, 'SetScrew': 95, 'BarBolt': -40, 'Bar': 55,
              'Pad': 55, 'Standoff': -85, 'LugBolt': -150, 'Lug_Bus': 100, 'Lug': -120, 'Pan': -200}
        for kk, v in dz.items():
            if kd.startswith(kk):
                ex_p[n] = (0, 0, v)
                break
    pxp = PX
    show(lambda n: n.startswith(pw) and not kind(n).startswith(('Wire', 'Harness')))
    place(ex_p)
    eye_ex = dict(eye=(-330, -520, 220), target=(pxp + 90.0, 90.0, 60.0))

    def c_of(prefix_kind, dz=0.0, top=False):
        ns = [n for n in names(pw, prefix_kind)]
        if not ns:
            return (0, 0, 0)
        c = occ_center(ns[0], top)
        return (c[0], c[1], c[2] + dz)
    shot('fusebox_power_explode.png', callouts=[
        (1, c_of('Cover', top=True), 'cover (snaps on, 4 tongues)'), (2, c_of('Relay_TE_F7'), 'relays plug in from the top'),
        (3, c_of('Fuse_AMI_ltgreen'), 'AMI fuses on the studs'), (4, c_of('Nut'), 'Keps nuts, 4 Nm max'),
        (5, c_of('SetScrew'), 'M5 set screws (studs)'), (6, c_of('Bar'), 'copper bar 25 x 6.35'), (7, c_of('Pad'), 'output pads 15 x 3'),
        (8, c_of('Base'), 'base (deck on 4 angular legs)'), (9, c_of('BarBolt'), 'bar bolts up from below'),
        (10, c_of('Standoff_M5_FF_hex8_L40'), 'standoffs 40 mm (both rows, one part)'),
        (11, c_of('Lug'), 'cable lugs'), (12, c_of('LugBolt'), 'M5 x 10 lug bolts'), (13, c_of('Pan'), 'belly pan (snaps on)')], **eye_ex)
    # steps 1-3
    place({})
    show(lambda n: n.startswith(pw) and kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'BarBolt', 'Standoff', 'SetScrew')))
    place({n: (0, 0, 35) for n in names(pw, 'Bar', 'Pad', 'SetScrew')} | {n: (0, 0, -30) for n in names(pw, 'BarBolt')}
          | {n: (0, 0, -45) for n in names(pw, 'Standoff')})
    shot('fusebox_power_step1.png', callouts=[
        (1, c_of('Bar'), 'lay the bar in its pocket'), (2, c_of('Pad'), 'lay the 14 pads in theirs'),
        (3, c_of('BarBolt'), 'bar bolts up through the hex head pockets'), (4, c_of('Standoff_M5_FF_hex8_L40'), '40 mm standoffs up into the hex holes, both rows'),
        (5, c_of('SetScrew'), 'set screw down through each pad into its standoff'),
        (6, c_of('Base'), 'base, right way up')], eye=(-360, -560, 90), target=(pxp + 90.0, 90.0, 25.0))
    place({n: (0, 0, -40) for n in names(pw, 'Lug', 'LugBolt', 'Wire', 'Harness')})
    show(lambda n: n.startswith(pw) and kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'BarBolt', 'Standoff', 'SetScrew', 'Lug', 'LugBolt', 'Wire', 'Harness')))
    shot('fusebox_power_step2.png', callouts=[
        (1, c_of('Harness', dz=0), 'crimp, push each terminal up into its cavity (wire side)'),
        (2, (pxp + 92.25, 79.0, 8.0 - 40.0), 'relay feed lug on its long standoff (M5 x 10)'),
        (3, (pxp + 62.0, 79.0, 30.0 - 40.0), 'feed round its saddle into terminal 30'),
        (4, (pxp + 164.75, 115.0, 11.0 - 40.0), 'OUT lug on its standoff (M5 x 10)'),
        (5, (pxp - 20.0, 88.0, 8.0 - 40.0), 'tie the bundles; they leave the inboard end')],
        eye=(-260, -420, -300), target=(pxp + 90.0, 90.0, 10.0))
    place({n: (0, 0, 45) for n in names(pw, 'Relay', 'SPARE', 'Fuse', 'Nut')})
    show(lambda n: n.startswith(pw) and not kind(n).startswith(('Cover', 'Pan')))
    shot('fusebox_power_step3.png', callouts=[
        (1, c_of('Fuse_AMI_ltgreen'), 'AMI fuses on the studs'), (2, c_of('Nut'), 'Keps nuts, 4 Nm max'),
        (3, c_of('Relay_TE_F7'), 'relays plug in'), (4, c_of('Fuse_ATM'), 'ACPS mini fuse'),
        (5, (pxp + S.POWER['x_bar'] + 30.0, sizes['POWER']['in_y'], S.POWER['bar_top'] + 6.0), '1/0 lug on the M8 stud')], **eye_ex)
    place({n: (0, 0, 70) for n in names(pw, 'Cover')} | {n: (0, 0, -70) for n in names(pw, 'Pan')})
    show(lambda n: n.startswith(pw))
    shot('fusebox_power_step4.png', callouts=[
        (1, c_of('Pan'), 'belly pan snaps up into the skirt'), (2, c_of('Cover', top=True), 'cover snaps down over the deck'),
        (3, (sizes['POWER']['feet'][0][0] + pxp, sizes['POWER']['feet'][0][1], 3.0), 'M6 through each foot (4), steel limiter')], **eye_ex)
    place({})

    # ---- LOGIC explode
    lg = 'Logic_'
    ex_l = {}
    for n in names(lg):
        kd = kind(n)
        for kk, v in {'Cover': 200, 'Relay': 120, 'SPARE': 120, 'Fuse': 95, 'Strip_': -70, 'Lug_TE': -70, 'LugBolt_M4': -70, 'Washer': -70,
                      'Lug_Klauke': -70, 'LugBolt_M5': -70, 'Pan': -170}.items():
            if kd.startswith(kk):
                ex_l[n] = (0, 0, v)
                break
    show(lambda n: n.startswith(lg) and not kind(n).startswith(('Wire', 'Harness')))
    place(ex_l)

    def l_of(k_, top=False):
        ns = names(lg, k_)
        return occ_center(ns[0], top) if ns else (0, 0, 0)
    shot('fusebox_logic_explode.png', callouts=[
        (1, l_of('Cover', True), 'cover (snaps on)'), (2, l_of('Relay'), 'micro relays'), (3, l_of('Fuse_ATM_15A'), 'mini fuses'),
        (4, l_of('Base'), 'base: deck, cavity towers, spine between the strips'), (5, l_of('Strip_'), 'Bus 1 / Bus 2 strips on edge, slide in from the rear'),
        (6, l_of('Lug_TE'), 'input jumper lugs, TE PIDG 53941-1'), (7, l_of('LugBolt_M4'), 'M4 x 8 + spring washer into the tapped strip'),
        (8, l_of('Lug_Klauke'), 'feed lugs, M5 x 10 into the strip'), (9, l_of('Pan'), 'belly pan (snaps on)')],
        eye=(-330, -420, 240), target=(40.0, 90.0, 30.0))
    place({})
    if REV[0] == 7:
        show(lambda n: True)
        return

    # ---- battery block
    BX, BY = S.PLACE['BATTRELAY']
    bt = dict(eye=(-220, -300, 260), target=(BX + 92.0, BY + 46.0, 20.0))
    show(BATT)
    shot('battrelay_render_iso_closed.png', **bt)
    shot('battrelay_render_iso_closed_rear.png', eye=(240, 300, 220), target=(BX + 92.0, BY + 46.0, 20.0))
    shot('battrelay_render_under.png', eye=(-220, -300, -220), target=(BX + 92.0, BY + 46.0, 10.0))
    show(lambda n: BATT(n) and LOADED(n))
    shot('battrelay_render_iso_open.png', **bt)
    show(lambda n: BATT(n) and EMPTY(n))
    shot('battrelay_render_iso_empty.png', **bt)
    rb = 'BattRelay_'
    ex_b = {}
    for n in names(rb):
        kd = kind(n)
        for kk, v in {'Cover': 175, 'Relay': 85, 'CoilPlug': 85, 'FlangeBolt': 110, 'Nut': 62, 'Fuse': 45, 'Lug': 62, 'BarBolt': 12, 'Bar': 25, 'Pad': 25}.items():
            if kd.startswith(kk):
                ex_b[n] = (0, 0, v)
                break
    show(lambda n: BATT(n) and not kind(n).startswith('Wire'))
    place(ex_b)
    bp = sizes['BATTRELAY']['parts']

    def bw(p, dz):
        return (p[0] + BX, p[1] + BY, p[2] + dz)
    shot('battrelay_explode.png', callouts=[
        (1, (BX + 92.0, BY + 46.0, 175 + sizes['BATTRELAY']['H']), 'cover (snaps on) - the lid'),
        (2, bw(bp['relay'], 85), 'fuel pump relay, TE HCR150'), (3, bw(bp['plug'], 85), 'coil plug (Superseal 1.5)'),
        (4, bw(bp['fuse'], 45), 'AMI 40 A fuse'), (5, bw(bp['bar'], 25), 'copper bar: battery stud + fuse in'),
        (6, bw(bp['pad'], 25), 'copper pad: fuse out'), (7, bw(bp['ped'], 0), 'fuse pedestal (printed, part of the base)'),
        (8, (sizes['BATTRELAY']['tabs'][0][0] + BX, sizes['BATTRELAY']['tabs'][0][1] + BY, 4.0), 'end tab, M6 + steel limiter (one each end)')],
        eye=(-260, -330, 200), target=(BX + 92.0, BY + 46.0, 80.0))
    place({})
    show(lambda n: True)
