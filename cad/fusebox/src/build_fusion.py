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


def cone(p0, d0, p1, d1):
    return tb.createCylinderOrCone(P(*p0), d0 / 20.0, P(*p1), d1 / 20.0)


def sphere(p, d):
    return tb.createSphere(P(*p), d / 20.0)


def hexz(x, y, z0, z1, af, rot=0):
    """Hex prism along z; rot 0 = corners on the x axis, rot 90 = flats facing +-x."""
    h = rbox(x, y, z0, z1, af * 2, af, rot)
    for ang in (60, 120):
        bo(h, rbox(x, y, z0, z1, af * 2, af, rot + ang), 'i')
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


def ring_lug(x, y, z, b, hole, t, d4, along, length, barrel=9.0, up=False):
    """Tubular lug lying flat, palm underside at z, round palm at (x, y), barrel (d4) along +-x or +-y.
    up=True: palm UP against a face above it (R155 strap: the lug bolted under the strap's bottom leg) - the barrel hangs below the
    palm, its top level with the palm top. Returns (body, barrel end point at the barrel centre line)."""
    sgn, ax = along
    zc = (z + t - d4 / 2) if up else (z + d4 / 2)
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


def root_fillets(x0, y0, x1, y1, zb, r, sides='xy', ends=None):
    """Concave fillets of radius r along the bottom edges of a wall standing on a face at zb (wall footprint x0..x1, y0..y1).
    sides 'x': along the wall's two long faces normal to x (a wall running in y); 'y': normal to y; 'xy': all four.
    Markup 2026-10-17 (Dan 23-31, DECISIONS R159): every free-standing printed wall gets a root fillet so it cannot snap off its base."""
    out = []
    if 'x' in sides:
        for (xf, sg) in ((x0, -1), (x1, 1)):
            f = box(min(xf, xf + sg * r), y0, zb - 0.01, max(xf, xf + sg * r), y1, zb + r)
            bo(f, cyl((xf + sg * r, y0 - 1, zb + r), (xf + sg * r, y1 + 1, zb + r), 2 * r), 's')
            out.append(f)
    if 'y' in sides:
        for (yf, sg) in ((y0, -1), (y1, 1)):
            f = box(x0, min(yf, yf + sg * r), zb - 0.01, x1, max(yf, yf + sg * r), zb + r)
            bo(f, cyl((x0 - 1, yf + sg * r, zb + r), (x1 + 1, yf + sg * r, zb + r), 2 * r), 's')
            out.append(f)
    return out


def bundle_d(ods):
    """Bundle diameter for wires of the given ODs (one wire: its OD; more: 1.2 x the root of the summed squares)."""
    return ods[0] if len(ods) == 1 else 1.2 * math.sqrt(sum(o * o for o in ods))


def pillars(hs, bridges, root_, min_attach=3.0):
    """R127 (Dan 2026-10-15 markup: "small floating square stub"): where three or more cavities join into one opening, the pairwise
    bridge cuts leave small pillars of PA12 standing inside it, hanging from the material above. Per joined group and per height band,
    every material island enclosed by the opening (2-D, on a grid of the zone edges) whose narrower side is under min_attach is
    returned as a box (z_lo, z_hi, x0, x1, y0, y1) to cut. Bands with the same island merge into one box."""
    groups = {}
    for i, h in enumerate(hs):
        groups.setdefault(root_(i), []).append(h)
    out = []
    for g, mem in groups.items():
        if len(mem) < 2:
            continue
        rects = [z for h in mem for z in h['abs']] + bridges.get(g, [])
        zb = sorted(set(round(v, 4) for r in rects for v in (r[0], r[1])))
        open_ = {}
        for za, zc in zip(zb, zb[1:]):
            act = [r for r in rects if r[0] <= za + 1e-6 and r[1] >= zc - 1e-6]
            if len(act) < 2:
                continue
            xs = sorted(set([r[2] for r in act] + [r[3] for r in act]))
            ys = sorted(set([r[4] for r in act] + [r[5] for r in act]))
            nx, ny = len(xs) - 1, len(ys) - 1
            hole = [[any(r[2] <= (xs[a] + xs[a + 1]) / 2 <= r[3] and r[4] <= (ys[b] + ys[b + 1]) / 2 <= r[5] for r in act) for b in range(ny)] for a in range(nx)]
            seen = [[False] * ny for _ in range(nx)]
            found = set()
            for a0 in range(nx):
                for b0 in range(ny):
                    if hole[a0][b0] or seen[a0][b0]:
                        continue
                    stack, comp, edge = [(a0, b0)], [], False
                    seen[a0][b0] = True
                    while stack:
                        a, b = stack.pop()
                        comp.append((a, b))
                        if a in (0, nx - 1) or b in (0, ny - 1):
                            edge = True            # reaches the outside of the opening: the body, not an island
                        for (da, db) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            c, d = a + da, b + db
                            if 0 <= c < nx and 0 <= d < ny and not hole[c][d] and not seen[c][d]:
                                seen[c][d] = True
                                stack.append((c, d))
                    if edge:
                        continue
                    bx = (xs[min(a for a, _ in comp)], xs[max(a for a, _ in comp) + 1], ys[min(b for _, b in comp)], ys[max(b for _, b in comp) + 1])
                    if min(bx[1] - bx[0], bx[3] - bx[2]) < min_attach:
                        found.add(tuple(round(v, 4) for v in bx))
            for bx in found:
                if bx in open_ and abs(open_[bx][1] - za) < 1e-6:
                    open_[bx][1] = zc
                else:
                    if bx in open_:
                        out.append((open_[bx][0], open_[bx][1]) + bx)
                    open_[bx] = [za, zc]
            for bx in [k for k, v in open_.items() if abs(v[1] - zc) > 1e-6]:
                out.append((open_[bx][0], open_[bx][1]) + bx)
                del open_[bx]
        out.extend((v[0], v[1]) + bx for bx, v in open_.items())
    return out


def strips(hs, bridges, root_, extra, min_wall=2.0):
    """R127 sweep (Dan 2026-10-16: "fix the ones you found"): the join rule of R120 (two cavities closer than min_wall join) applied to
    whatever is left after the pairwise bridges - per joined group (and per cavity next to the belly-pan groove, `extra` = the groove
    rects) and per height band, on a grid of the zone edges, every run of material cells between two openings in the same row (x) or
    column (y) that is narrower than min_wall is returned as a box (z_lo, z_hi, x0, x1, y0, y1) to cut. Bands with the same strip merge."""
    groups = {}
    for i, h in enumerate(hs):
        groups.setdefault(root_(i), []).append(h)
    out = []
    for g, mem in groups.items():
        rects = [z for h in mem for z in h['abs']] + bridges.get(g, [])
        gx0, gx1 = min(r[2] for r in rects) - 3.0, max(r[3] for r in rects) + 3.0
        gy0, gy1 = min(r[4] for r in rects) - 3.0, max(r[5] for r in rects) + 3.0
        ex = [(e[0], e[1], max(e[2], gx0), min(e[3], gx1), max(e[4], gy0), min(e[5], gy1)) for e in extra
              if e[2] < gx1 and e[3] > gx0 and e[4] < gy1 and e[5] > gy0]
        if len(mem) < 2 and not ex:
            continue
        allr = rects + ex
        zb = sorted(set(round(v, 4) for r in allr for v in (r[0], r[1])))
        open_ = {}
        for za, zc in zip(zb, zb[1:]):
            act = [r for r in allr if r[0] <= za + 1e-6 and r[1] >= zc - 1e-6]
            if len(act) < 2 or not any(r in act for r in rects):
                act = []
            xs = sorted(set([r[2] for r in act] + [r[3] for r in act]))
            ys = sorted(set([r[4] for r in act] + [r[5] for r in act]))
            nx, ny = max(len(xs) - 1, 0), max(len(ys) - 1, 0)
            hole = [[any(r[2] <= (xs[a] + xs[a + 1]) / 2 <= r[3] and r[4] <= (ys[b] + ys[b + 1]) / 2 <= r[5] for r in act) for b in range(ny)] for a in range(nx)]
            found = set()
            for (n1, n2, cell, ax) in ((nx, ny, lambda i, j: hole[i][j], 'x'), (ny, nx, lambda i, j: hole[j][i], 'y')):
                cs = xs if ax == 'x' else ys
                os_ = ys if ax == 'x' else xs
                for j in range(n2):
                    i = 0
                    while i < n1:
                        if cell(i, j):
                            i += 1
                            continue
                        k = i
                        while k < n1 and not cell(k, j):
                            k += 1
                        if i > 0 and k < n1 and cs[k] - cs[i] < min_wall - 1e-6:      # material run between two openings
                            found.add(tuple(round(v, 4) for v in ((cs[i], cs[k], os_[j], os_[j + 1]) if ax == 'x' else (os_[j], os_[j + 1], cs[i], cs[k]))))
                        i = k
            for bx in found:
                if bx in open_ and abs(open_[bx][1] - za) < 1e-6:
                    open_[bx][1] = zc
                else:
                    if bx in open_:
                        out.append((open_[bx][0], open_[bx][1]) + bx)
                    open_[bx] = [za, zc]
            for bx in [k for k, v in open_.items() if abs(v[1] - zc) > 1e-6]:
                out.append((open_[bx][0], open_[bx][1]) + bx)
                del open_[bx]
        out.extend((v[0], v[1]) + bx for bx, v in open_.items())
    return out


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


def build(out_dir, save=True, renders=True, rev=6, msg=None):
    REV[0] = rev
    R7 = S.REV7 if rev == 7 else None
    DIM = {'D': S.D, 'snaps_rear': None,   # rev 7: the POWER box is deeper; the shared shell / pan / cover helpers read DIM
           'so': S.SKIRT_OUT if rev == 7 else 0.0}   # R127 amendment: the skirt grows OUTWARD by so (inner face, cavities, pan fit unchanged)
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
        """J2 = B (Dan 2026-10-14, R94); hole rule R120 and self-locking terminals R121 (Dan 2026-10-15): every terminal cavity is cut
        zone by zone from the plan (S.zones, written into wiring_plan.json by wiring_sim.py): from under the deck the R120 hole - the
        largest cross-section of everything that passes (contact box, barrels on the THICKEST insulation, the wire, 880398-2's stop
        flange) + CLR per side - up to the terminal's neck; above it the box-sized ledge and the lance window up to the seat (receptacle
        top HOLE['top_gap'] under the deck top; the blade slot above, narrower than the box, is the stop the other way). Two cavities
        with less than min_wall between zones at the same height join into one (Dan: "join the two slots into one"), bridged across the
        gap over the heights they share. A collar of min_wall round every cavity outline keeps the tower wall >= 2.0 (R73) - unioned with
        the towers, hanging from the deck plate (not floating, R101). Short guide walls hang under the deck between neighbouring holes
        (Dan: "short separators or walls ... to help guide wires straight out"); the cavities are cut through them. 87a cavities get a
        cavity only when a harness wire lands there.
        R101 (Dan 2026-10-15: "the little ribs ... are just floating. fill in the gaps between relay positions under the ribs"; then "i
        like them as they are. just fix the floating pieces i mentioned"): a FLOATING guide wall (less than S.FLOAT_BACKING of its top
        face on a cavity tower - it crosses the gap between two relay positions) gets a web of its own footprint from its top up into
        the deck plate. Every other wall is left exactly as it was.
        Returns (cuts, guide walls + webs + collars) and records every cavity for check_terminal_holes.py."""
        if not PLAN7:
            return [], []
        HO, G = S.HOLE, S.GUIDE
        hs = [dict(c) for c in PLAN7['cavities'] if c['box'] == box_name and c.get('zones')
              and not (c['kind'].endswith('87a') and c['source'] != 'harness')]
        z0 = z_d - G['h'] - 1.0
        for h in hs:
            zs_ = z_t - S.seat_gap(h['part'], h['kind'])  # fit audit 2026-10-18: seat depth by relay type (spec.SEAT_GAP)
            T = S.TERM[h['part']]
            h['z1'] = round(zs_, 2)
            h['est'] = T['t'] is None or h['part'] in S.HEAD_EST or S.LOCK[h['part']].get('est', False)
            h['abs'] = []                                   # (z_lo, z_hi, x0, x1, y0, y1) in box coordinates
            for (dlo, dhi, x0_, x1_, y0_, y1_) in h['zones']:
                lo, hi = (z0 if dlo is None else max(z0, zs_ + dlo)), zs_ + dhi
                if hi > lo + 0.01:
                    h['abs'].append((lo, hi, h['x'] + x0_, h['x'] + x1_, h['y'] + y0_, h['y'] + y1_))
            h['sx'] = max(z[3] for z in h['abs']) - min(z[2] for z in h['abs'])
            h['sy'] = max(z[5] for z in h['abs']) - min(z[4] for z in h['abs'])

        def fin_clip(fd, box_name, feet):
            """A guide wall (cx, cy, length, t, angle) shortened to stay inside the belly pan's inner faces (it hangs below the deck,
            where the pan wall slides up), or None when it crosses a retainer clip plate (R123 B: the plate is under there) or is left
            under 2 mm long."""
            Lb = (S.LOGIC if box_name == 'LOGIC' else S.POWER)['L']
            m_ = S.SKIRT + 2 * W_CL + PN['t']                     # pan inner face + a clearance
            xi0, xi1, yi0, yi1 = m_, Lb - m_, m_, DIM['D'] - m_
            cx, cy, ln, t_, ang = fd
            ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            ends = []
            for sg in (-1, 1):
                k = ln / 2
                for (c0, u, lo, hi) in ((cx, ux, xi0, xi1), (cy, uy, yi0, yi1)):
                    if abs(u) > 1e-9:
                        lim = ((hi if sg * u > 0 else lo) - c0) / (sg * u) - t_ / 2
                        k = min(k, lim)
                ends.append(k)
            if ends[0] + ends[1] < 2.0:
                return None
            ncx, ncy = cx + (ends[1] - ends[0]) / 2 * ux, cy + (ends[1] - ends[0]) / 2 * uy
            r_ = (ends[0] + ends[1]) / 2 + t_
            for (fx0, fx1, fy0, fy1) in feet:
                if fx0 - r_ < ncx < fx1 + r_ and fy0 - r_ < ncy < fy1 + r_:
                    return None
            return (ncx, ncy, ends[0] + ends[1], t_, ang)

        def rgap_(p, q):  # printed wall between two rects (x0, x1, y0, y1); negative = overlap
            gx, gy = max(p[0] - q[1], q[0] - p[1]), max(p[2] - q[3], q[2] - p[3])
            return math.hypot(gx, gy) if gx > 0 and gy > 0 else max(gx, gy)

        def gap_(a, b):   # thinnest wall between two cavities over the heights they share, and the zone pairs under min_wall
            w_, under = 1e9, []
            for za in a['abs']:
                for zb in b['abs']:
                    lo, hi = max(za[0], zb[0]), min(za[1], zb[1])
                    if hi <= lo:
                        continue
                    g = rgap_(za[2:], zb[2:])
                    w_ = min(w_, g)
                    if g < HO['min_wall']:
                        under.append((lo, hi, za[2:], zb[2:], g))
            return w_, under
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
                if d > 40:
                    continue
                w_, under = gap_(a, b)
                if under:
                    edges.append((i, j, under))
                    par[root_(i)] = root_(j)
                elif d < G['reach']:
                    near_.append((i, j, d))
        cuts = [box(z[2], z[4], z[0], z[3], z[5], z[1]) for h in hs for z in h['abs']]
        all_z = [z for h in hs for z in h['abs']]

        def diagonal_solid(p, q, lo, hi, gx, gy, clip_=False, e=0.05):
            """Sweep C1 / C3: leave the bridge between diagonal zones p, q (x0, x1, y0, y1) out? Yes when its narrow side is under GAP_OPEN,
            or when at one of the two zone corners it would meet, both off-diagonal neighbours of that corner are PA12 (no other zone cut
            there over these heights) - the void would then meet itself along an edge."""
            if min(gx, gy) < S.GAP_OPEN:
                return True
            if clip_:           # the R123 retainer clip's leg pockets (cut below) open these corners
                return False
            zm = (lo + hi) / 2
            act = [z for z in all_z if z[0] <= zm <= z[1]]
            sx = 1 if q[0] >= p[1] else -1
            sy = 1 if q[2] >= p[3] else -1
            for (cx_, cy_) in ((p[1] if sx > 0 else p[0], p[3] if sy > 0 else p[2]), (q[0] if sx > 0 else q[1], q[2] if sy > 0 else q[3])):
                pts = [(cx_ + sx * e, cy_ - sy * e), (cx_ - sx * e, cy_ + sy * e)]
                if not any(z[2] <= px_ <= z[3] and z[4] <= py_ <= z[5] for (px_, py_) in pts for z in act):
                    return True
            return False
        bridges = {}
        for (i, j, under) in edges:
            for (lo, hi, p, q, g) in under:
                if g <= 0:
                    continue                                # the zones already overlap
                ox = min(p[1], q[1]) - max(p[0], q[0])      # > 0: the zones overlap in x (side by side in y), < 0: x gap
                oy = min(p[3], q[3]) - max(p[2], q[2])
                clip_ = all(c_['cav'].split()[0] in S.RETAIN.get(box_name, []) for c_ in (hs[i], hs[j]))   # R123 clip: its leg pockets open the corners
                if REV[0] == 7 and ox <= 0 and oy <= 0 and diagonal_solid(p, q, lo, hi, -ox, -oy, clip_):
                    # SteveCAD sweep C1 / C3 (Dan 2026-10-16: "FILL SOLID"): diagonal neighbours (apart in x AND in y) whose bridge would be a
                    # slit under GAP_OPEN (POWER R2 - R7 85 / 86 to 87: 0.3 / 0.375, under MJF's 0.5 least gap), or would touch a cavity only
                    # along a corner edge with nothing else cut round it (a zero-thickness joint: LOGIC Bus 2 outputs to the micro relay 85,
                    # x 48.1), get no bridge - that corner stays solid. Other diagonal bridges (R1 30 to 85 / 86) are kept as they were.
                    report.setdefault('diagonal_joins_solid', {}).setdefault(box_name, []).append(
                        [a_['cav'] for a_ in (hs[i], hs[j])] + [round(g, 2), round(lo, 2), round(hi, 2)])
                    continue
                xs_ = sorted([max(p[0], q[0]), min(p[1], q[1])]) if ox > 0 else sorted([min(p[1], q[1]), max(p[0], q[0])])
                ys_ = sorted([max(p[2], q[2]), min(p[3], q[3])]) if oy > 0 else sorted([min(p[3], q[3]), max(p[2], q[2])])
                if REV[0] == 7:   # S6: a bridge whose opening (the zones' shared length) is under GAP_OPEN would be a powder-trap throat
                    for (rng, o_) in ((xs_, ox), (ys_, oy)):
                        if 0 < o_ < S.GAP_OPEN:
                            m_ = (rng[0] + rng[1]) / 2
                            rng[0], rng[1] = m_ - S.GAP_OPEN / 2, m_ + S.GAP_OPEN / 2
                            report.setdefault('bridge_throats_opened', {}).setdefault(box_name, []).append(
                                [a_['cav'] for a_ in (hs[i], hs[j])] + [round(o_, 3), round(lo, 2), round(hi, 2)])
                cuts.append(box(xs_[0], ys_[0], lo, xs_[1], ys_[1], hi))
                bridges.setdefault(root_(i), []).append((lo, hi, xs_[0], xs_[1], ys_[0], ys_[1]))
        islands = []
        for (lo, hi, x0_, x1_, y0_, y1_) in pillars(hs, bridges, root_):
            cuts.append(box(x0_, y0_, lo, x1_, y1_, hi))
            islands.append([round(v, 2) for v in (x0_, y0_, lo, x1_, y1_, hi)])
        report.setdefault('cavity_islands_cut', {})[box_name] = islands
        if REV[0] == 7:   # R127 sweep: strips under min_wall left between two openings of a joined group, or between a cavity and the pan groove
            Lb, Db = (S.LOGIC if box_name == 'LOGIC' else S.POWER)['L'], DIM['D']
            m_, zg_ = S.SKIRT + 2 * W_CL + PN['t'], z_d + PN['over'] + W_CL
            ring = [(z_d - 1, zg_, -1.0, m_, -1.0, Db + 1), (z_d - 1, zg_, Lb - m_, Lb + 1, -1.0, Db + 1),
                    (z_d - 1, zg_, -1.0, Lb + 1, -1.0, m_), (z_d - 1, zg_, -1.0, Lb + 1, Db - m_, Db + 1)]
            st_ = strips(hs, bridges, root_, ring, HO['min_wall'])
            for (lo, hi, x0_, x1_, y0_, y1_) in st_:
                cuts.append(box(x0_ - 0.01, y0_ - 0.01, lo, x1_ + 0.01, y1_ + 0.01, hi))
            report.setdefault('cavity_strips_cut', {})[box_name] = [[round(v, 2) for v in s_] for s_ in st_]
            for z in [z for h in hs for z in h['abs']]:   # sweep 2026-10-17: a 2.0 - 3.0 strip left between a cavity and the pan groove (kept: under 2.0 is cut)
                lo_, hi_ = max(z[0], z_d), min(z[1], zg_)
                if hi_ <= lo_:
                    continue
                for (gp_, bx_) in ((z[2] - m_, (m_, z[2], z[4], z[5])), (Lb - m_ - z[3], (z[3], Lb - m_, z[4], z[5])),
                                   (z[4] - m_, (z[2], z[3], m_, z[4])), (Db - m_ - z[5], (z[2], z[3], z[5], Db - m_))):
                    if HO['min_wall'] <= gp_ < 3.0:
                        exempt('%s_Base_PA12_printed' % box_name.capitalize(), 'groove strip', bx_[0] - 0.3, bx_[1] + 0.3, bx_[2] - 0.3, bx_[3] + 0.3,
                               lo_ - 0.3, hi_ + 0.3, S.PLACE[box_name], only='A')
        cuts += groove_join((S.LOGIC if box_name == 'LOGIC' else S.POWER)['L'], z_d, [z for h in hs for z in h['abs']])
        collars = []
        if plate_b is not None:
            for h in hs:      # R73: min_wall round every cavity, from the deck underside up into the deck plate
                x0_, x1_ = min(z[2] for z in h['abs']), max(z[3] for z in h['abs'])
                y0_, y1_ = min(z[4] for z in h['abs']), max(z[5] for z in h['abs'])
                m = HO['min_wall']
                collars.append(box(x0_ - m, y0_ - m, z_d, x1_ + m, y1_ + m, plate_b + 0.01))
        clip_feet = []
        for rel in S.RETAIN.get(box_name, []):    # R123 B: printed retainer clip under a relay whose terminals cannot self-lock
            rh = [h for h in hs if h['cav'].split()[0] == rel]
            if not rh:
                continue
            RT, m = S.RETAINER, HO['min_wall']
            x0_, x1_ = min(z[2] for h in rh for z in h['abs']) - m, max(z[3] for h in rh for z in h['abs']) + m
            y0_, y1_ = min(z[4] for h in rh for z in h['abs']) - m, max(z[5] for h in rh for z in h['abs']) + m
            ztop = min(zs_ - (S.TERM[h['part']]['L'] or S.L_EST) for h in rh) - RT['play']    # under the lowest terminal end
            plate = box(x0_, y0_, ztop - RT['t'], x1_, y1_, ztop)
            clip_feet.append((x0_ - RT['clr'], x1_ + RT['clr'], y0_ - RT['clr'], y1_ + RT['clr']))
            for h in rh:            # threaded onto the wires before crimping: bare wire + clr (the build-up ends inside the barrel)
                dh_ = S.retainer_hole(h['part'], h['wire_od'])[0]
                bo(plate, cylz(h['x'], h['y'], ztop - RT['t'] - 1, ztop + 1, dh_), 's')
                if REV[0] == 7:     # markup 2026-10-17 (Dan 23-26: "terminals need to fit through these holes. Or need slots for the wires"):
                    # each hole runs on as a slot of the same width to the plate's -y edge - the clip slides onto the finished wires from the
                    # front, and the slot still stops the crimped insulation barrel (larger than the slot)
                    bo(plate, box(h['x'] - dh_ / 2, y0_ - 1.0, ztop - RT['t'] - 1, h['x'] + dh_ / 2, h['y'], ztop + 1), 's')
                    report.setdefault('retainer_slots', []).append([h['cav'], round(dh_, 2), round(S.retainer_hole(h['part'], h['wire_od'])[1], 2)])
            lw, ld = RT['leg']
            long_x = (x1_ - x0_) >= (y1_ - y0_)
            d0, d1 = RT['leg_shift'].get(rel, (0.0, 0.0))
            ext = max(0.0, lw - m) + 0.5   # fit audit 2026-10-18 (+ 0.5: the plate strip past the outer wire slot stays >= 2.0, R127): the leg's inner face on the hole-zone edge (a 2.5 leg in the 2.0 band stood 0.5 inside it;
            # the turned R1 30 terminal's insulation barrel reached it) - the plate grows by ext on those two ends to carry the leg
            if ext > 0 and long_x:     # only the two end strips (the wire holes / slots stay open)
                bo(plate, box(x0_ - ext, y0_, ztop - RT['t'], x0_ + 0.01, y1_, ztop), 'u')
                bo(plate, box(x1_ - 0.01, y0_, ztop - RT['t'], x1_ + ext, y1_, ztop), 'u')
            elif ext > 0:
                bo(plate, box(x0_, y0_ - ext, ztop - RT['t'], x1_, y0_ + 0.01, ztop), 'u')
                bo(plate, box(x0_, y1_ - 0.01, ztop - RT['t'], x1_, y1_ + ext, ztop), 'u')
            legs = [((x0_ + m - lw / 2, (y0_ + y1_) / 2 + d0), -1), ((x1_ - m + lw / 2, (y0_ + y1_) / 2 + d1), 1)] if long_x else                    [(((x0_ + x1_) / 2 + d0, y0_ + m - lw / 2), -1), (((x0_ + x1_) / 2 + d1, y1_ - m + lw / 2), 1)]
            for ((lx, ly), sg) in legs:
                sx_, sy_ = (lw, ld) if long_x else (ld, lw)
                zt_ = z_d + RT['leg_h']
                bo(plate, box(lx - sx_ / 2, ly - sy_ / 2, ztop - 0.01, lx + sx_ / 2, ly + sy_ / 2, zt_), 'u')     # leg up into the collar
                bx_ = (lx + sg * (sx_ / 2), lx + sg * (sx_ / 2 + RT['barb'])) if long_x else (lx - sx_ / 2, lx + sx_ / 2)
                by_ = (ly - sy_ / 2, ly + sy_ / 2) if long_x else (ly + sg * (sy_ / 2), ly + sg * (sy_ / 2 + RT['barb']))
                bo(plate, box(min(bx_), min(by_), zt_ - RT['barb_h'], max(bx_), max(by_), zt_), 'u')          # barb, outward
                c_ = RT['clr']           # pocket in a boss on the collar: leg + clr, the barb's undercut at its top
                collars.append(box(lx - sx_ / 2 - c_ - RT['boss'] - (RT['barb'] if long_x else 0), ly - sy_ / 2 - c_ - RT['boss'] - (0 if long_x else RT['barb']),
                                   z_d, lx + sx_ / 2 + c_ + RT['boss'] + (RT['barb'] if long_x else 0), ly + sy_ / 2 + c_ + RT['boss'] + (0 if long_x else RT['barb']),
                                   plate_b + 0.01))
                pk = [lx - sx_ / 2 - c_, lx + sx_ / 2 + c_, ly - sy_ / 2 - c_, ly + sy_ / 2 + c_]
                cuts.append(box(pk[0], pk[2], z_d - 1, pk[1], pk[3], zt_ + 0.3))
                for h in rh:        # R127: a pocket closer than min_wall to a cavity runs on into it (no thin wall hanging between them)
                    for z in h['abs']:
                        lo_, hi_ = max(z[0], z_d - 1), min(z[1], zt_ + 0.3)
                        if hi_ <= lo_:
                            continue
                        for (k0, k1, o0, o1) in ((0, 1, 2, 3), (2, 3, 0, 1)):
                            if min(pk[o1], z[2 + o1]) - max(pk[o0], z[2 + o0]) <= 0:
                                continue            # no overlap side by side
                            for (e, f, sg) in ((pk[k1], z[2 + k0], 1), (pk[k0], z[2 + k1], -1)):
                                g_ = (f - e) * sg
                                if 0 < g_ < m:
                                    q = list(pk)
                                    q[k1 if sg > 0 else k0] = f + sg * 0.01
                                    cuts.append(box(q[0], q[2], lo_, q[1], q[3], hi_))
                                    report.setdefault('retainer_pocket_joins', []).append([h['cav'], round(g_, 2), round(lo_, 2), round(hi_, 2)])
                cuts.append(box(min(bx_) - c_, min(by_) - c_, zt_ - RT['barb_h'] - 0.3, max(bx_) + c_, max(by_) + c_, zt_ + 0.3))
            band = box(x0_ - 50, y0_ - 50, ztop - RT['t'] - 1.0, x1_ + 50, y1_ + 50, z_d - 0.01)
            for sp in (support or []):          # notch the PLATE round what hangs under the deck there (the feed-cable bend saddles);
                t_ = tb.copy(sp)                # only below the deck - the legs go up into their collar pockets and stay whole
                try:
                    bo(t_, tb.copy(band), 'i')
                except RuntimeError:            # nothing of it below the deck
                    continue
                if t_.volume > 1e-9:    # R127: notch = its bounding box + clr, a plain rectangle (no curved sliver or hooked tab)
                    bb_ = t_.boundingBox
                    bo(plate, box(bb_.minPoint.x * 10 - RT['clr'], bb_.minPoint.y * 10 - RT['clr'], ztop - RT['t'] - 1,
                                  bb_.maxPoint.x * 10 + RT['clr'], bb_.maxPoint.y * 10 + RT['clr'], ztop + 0.5), 's')
            comp('%s_Retainer_%s_PA12_printed' % (box_name.capitalize(), rel), plate, AP['pa12_pan'], MAT['pa'], S.PLACE[box_name])
            report.setdefault('retainers', {}).setdefault(box_name, []).append(dict(
                relay=rel, cavities=[h['cav'] for h in rh], plate=[round(v, 2) for v in (x0_, y0_, ztop - RT['t'], x1_, y1_, ztop)],
                holes=[[h['cav'], round(S.retainer_hole(h['part'], h['wire_od'])[0], 2)] for h in rh], legs=[[round(lx, 2), round(ly, 2)] for ((lx, ly), _) in legs],
                vol_cm3=round(((x1_ - x0_) * (y1_ - y0_) * RT['t'] + 2 * lw * ld * (RT['leg_h'] + z_d - ztop)) / 1000.0, 2)))
        gid = {}
        grp_ = {}
        for i, h in enumerate(hs):
            grp_.setdefault(root_(i), []).append(h)
        for mem_ in grp_.values():       # the lip over a joined opening spans its cavities
            if len(mem_) > 1:
                exempt('%s_Base_PA12_printed' % box_name.capitalize(), 'seat lip', min(z[2] for h in mem_ for z in h['abs']) - HO['min_wall'],
                       max(z[3] for h in mem_ for z in h['abs']) + HO['min_wall'], min(z[4] for h in mem_ for z in h['abs']) - HO['min_wall'],
                       max(z[5] for h in mem_ for z in h['abs']) + HO['min_wall'], zs_ - 0.3, z_t + 0.1, S.PLACE[box_name])
        for i, h in enumerate(hs):
            h['group'] = gid.setdefault(root_(i), len(gid))
            exempt('%s_Base_PA12_printed' % box_name.capitalize(), 'seat lip', min(z[2] for z in h['abs']) - HO['min_wall'],
                   max(z[3] for z in h['abs']) + HO['min_wall'], min(z[4] for z in h['abs']) - HO['min_wall'], max(z[5] for z in h['abs']) + HO['min_wall'],
                   zs_ - 0.3, z_t + 0.1, S.PLACE[box_name])
        fins, fin_d = [], []
        for (i, j, d) in near_:
            a, b = hs[i], hs[j]
            if a['group'] == b['group']:
                continue
            ang = math.degrees(math.atan2(b['y'] - a['y'], b['x'] - a['x'])) + 90.0
            t_fin = G['t']
            if REV[0] == 7 and (abs(a['y'] - b['y']) < 1e-6 or abs(a['x'] - b['x']) < 1e-6):
                # N21 / fit audit 2026-10-18: holes 4.0 or less apart (the MCP 2.8 sockets at the 8.1 mini fuse pitch: 3.5) - the wall fills the gap
                # (the holes trim it) instead of a 2.0 fin standing alone in it (R127 A: a lone 2.0 fin hangs by its top only)
                gap_ = (abs(a['x'] - b['x']) - (a['sx'] + b['sx']) / 2) if abs(a['y'] - b['y']) < 1e-6 else (abs(a['y'] - b['y']) - (a['sy'] + b['sy']) / 2)
                if 0 < gap_ <= 4.0:
                    t_fin = gap_ + 0.4
            fd = ((a['x'] + b['x']) / 2, (a['y'] + b['y']) / 2, max(a['sx'], a['sy'], b['sx'], b['sy']) + 2.0, t_fin, ang)
            fd = fin_clip(fd, box_name, clip_feet)
            if fd is None:
                continue
            fin_d.append(fd)
        if REV[0] == 7:    # R127 sweep: a slanted guide wall that crosses or touches a straight one (a diagonal neighbour pair, e.g. a fuse's
            # input and the next fuse's output) only adds triangular slivers and slanted tips sticking out of the straight wall - it is left out
            def straight(fd):
                return abs(math.sin(math.radians(2 * fd[4]))) < 1e-6

            def on(p, fd):
                u, v = p[0] - fd[0], p[1] - fd[1]
                c, s_ = math.cos(math.radians(fd[4])), math.sin(math.radians(fd[4]))
                return abs(u * c + v * s_) <= fd[2] / 2 + 0.01 and abs(-u * s_ + v * c) <= fd[3] / 2 + 0.01
            def pts(fd):     # points along the wall's middle line, end to end
                c, s_ = math.cos(math.radians(fd[4])), math.sin(math.radians(fd[4]))
                return [(fd[0] + c * fd[2] * f, fd[1] + s_ * fd[2] * f) for f in (-0.5, -0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5)]
            keep = [fd for fd in fin_d if straight(fd) or not any(straight(f2) and on(p_, f2) for f2 in fin_d for p_ in pts(fd))]
            report.setdefault('guide_walls_redundant', {})[box_name] = len(fin_d) - len(keep)
            fin_d = keep
        if REV[0] == 7:    # N21 / fit audit 2026-10-18 (S6): a straight wall whose end stops under 0.5 short of a crossing straight wall runs on into it
            def _ext(fd, others):
                c, s_ = round(math.cos(math.radians(fd[4])), 6), round(math.sin(math.radians(fd[4])), 6)
                if abs(c * s_) > 1e-6:
                    return fd
                along_x = abs(c) > 0.5            # this wall's length runs along x (else along y)
                lo, hi = (fd[0] - fd[2] / 2, fd[0] + fd[2] / 2) if along_x else (fd[1] - fd[2] / 2, fd[1] + fd[2] / 2)
                across = fd[1] if along_x else fd[0]
                for f2 in others:
                    c2, s2 = round(math.cos(math.radians(f2[4])), 6), round(math.sin(math.radians(f2[4])), 6)
                    if abs(c2 * s2) > 1e-6 or (abs(c2) > 0.5) == along_x:
                        continue                   # only a perpendicular straight wall
                    pos2, span2 = (f2[0], f2[1]) if along_x else (f2[1], f2[0])    # its position along our axis, its centre across
                    if across + fd[3] / 2 < span2 - f2[2] / 2 or across - fd[3] / 2 > span2 + f2[2] / 2:
                        continue                   # no overlap across our thickness
                    if 0 < (pos2 - f2[3] / 2) - hi < 0.5:
                        hi = pos2 - f2[3] / 2 + 0.05
                    elif 0 < lo - (pos2 + f2[3] / 2) < 0.5:
                        lo = pos2 + f2[3] / 2 - 0.05
                    else:
                        continue
                    report.setdefault('guide_walls_joined', {}).setdefault(box_name, 0)
                    report['guide_walls_joined'][box_name] += 1
                mid, L_ = (lo + hi) / 2, hi - lo
                return (mid, fd[1], L_, fd[3], fd[4]) if along_x else (fd[0], mid, L_, fd[3], fd[4])
            fin_d = [_ext(fd, [f2 for f2 in fin_d if f2 is not fd]) for fd in fin_d]

            def _touch(f1, f2):       # footprints (centre, length, thickness, angle) overlap - corner test both ways
                def corners(f):
                    c, s_ = math.cos(math.radians(f[4])), math.sin(math.radians(f[4]))
                    return [(f[0] + c * u * f[2] / 2 - s_ * v * f[3] / 2, f[1] + s_ * u * f[2] / 2 + c * v * f[3] / 2) for u in (-1, 1) for v in (-1, 1)]
                return any(on(p_, f2) for p_ in corners(f1)) or any(on(p_, f1) for p_ in corners(f2))
            lone = [fd for fd in fin_d if not straight(fd) and not any(_touch(fd, f2) for f2 in fin_d if f2 is not fd)]
            if lone:   # a slanted guide wall touching no other wall: its square ends cut on the slant read as sub-2.0 wedges (R127) - left out
                report.setdefault('guide_walls_lone_slanted_dropped', {})[box_name] = [[round(fd[0], 1), round(fd[1], 1)] for fd in lone]
                fin_d = [fd for fd in fin_d if fd not in lone]
        kept_fd = []
        for fd in fin_d:
            f_ = rbox(fd[0], fd[1], z_d - G['h'], z_d + 0.01, fd[2], fd[3], fd[4])
            if REV[0] == 7 and abs(math.sin(math.radians(2 * fd[4]))) > 1e-6:
                # R127 sweep: a slanted guide wall that the cavities cut into a stub shorter than min_wall is left out
                t_ = tb.copy(f_)
                fb = t_.boundingBox
                for c_ in cuts:
                    cb = c_.boundingBox
                    if cb.minPoint.x < fb.maxPoint.x and cb.maxPoint.x > fb.minPoint.x and cb.minPoint.y < fb.maxPoint.y and cb.maxPoint.y > fb.minPoint.y                             and cb.minPoint.z < fb.maxPoint.z and cb.maxPoint.z > fb.minPoint.z:
                        try:
                            bo(t_, tb.copy(c_), 's')
                        except RuntimeError:
                            pass
                small = G['t'] * G['h'] * HO['min_wall'] / 1000.0            # cm3
                if any(l_.volume < small for l_ in t_.lumps):
                    report.setdefault('guide_walls_stub_dropped', {}).setdefault(box_name, []).append([round(fd[0], 1), round(fd[1], 1)])
                    continue
            fins.append(f_)
            kept_fd.append(fd)
        fin_d = kept_fd
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
        report['terminal_holes'][box_name] = [dict(cav=h['cav'], kind=h['kind'], x=h['x'], y=h['y'], sx=round(h['sx'], 3), sy=round(h['sy'], 3),
                                                   zones=h['zones'], z0=round(z_d, 2), z1=h['z1'], group=h['group'], part=h['part'],
                                                   wire_od=h['wire_od'], source=h['source'], est=h['est'])
                                              for h in hs]
        report['terminal_slots'][box_name] = [sorted(h['cav'] for h in hs if h['group'] == g) for g in range(len(gid))
                                              if sum(1 for h in hs if h['group'] == g) > 1]
        report['guide_walls'][box_name] = dict(n=len(fins), t=G['t'], h=G['h'], world_shift=sh_, webs=len(webs))
        return cuts, fins + webs + collars

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

    def edge_break(occ, d=None):
        """F10 / D6 (SteveCAD v3, Dan 2026-10-16: copper is machined): a d x 45 deg chamfer on every edge of every body of a copper
        part, hole rims included - one chamfer feature per body. A body Fusion cannot chamfer whole is counted in the report as failed."""
        d = S.CU_BREAK if d is None else d
        c = occ.component
        done, failed = 0, 0
        for bi in range(c.bRepBodies.count):
            b = c.bRepBodies.item(bi)
            edges = adsk.core.ObjectCollection.create()
            for e in b.edges:
                edges.add(e)
            ci = c.features.chamferFeatures.createInput2()
            ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, adsk.core.ValueInput.createByReal(d / 10.0), False)
            try:
                c.features.chamferFeatures.add(ci)
                done += 1
            except Exception:
                failed += 1
        report.setdefault('edge_break', {})[c.name] = dict(d=d, bodies=done, failed=failed)
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
        bb_ = body.boundingBox      # the PA12 between letter strokes: the cover's top layer, as deep as the text
        exempt(c.name, 'label', bb_.minPoint.x * 10, bb_.maxPoint.x * 10, bb_.minPoint.y * 10, bb_.maxPoint.y * 10, z_top - S.LABEL['depth7'] - 0.6, z_top + 0.4)
        ex = c.features.extrudeFeatures
        ei = ex.createInput(coll, adsk.fusion.FeatureOperations.CutFeatureOperation)
        # R127 sweep (rev 7): 0.5 deep leaves the 2.5 cover top 2.0 under every letter (0.6 left 1.9); MJF engraving needs >= 0.5
        depth = S.LABEL['depth7'] if REV[0] == 7 else S.LABEL['depth']
        ei.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-depth / 10.0))
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

    def exempt(part, key, x0, x1, y0, y1, z0, z1, sh=(0.0, 0.0), only=None):
        """R127 sweep (rev 7): a named spot that stays thin because the part needs it (S.WALL_EXEMPT[key] says why). cad/check_printed_walls.py
        drops the wall pieces / attachment spots that lie inside this box (world coordinates) and lists them by name instead."""
        if REV[0] == 7:
            report.setdefault('wall_exempt', []).append(dict(part=part, key=key, only=only, box=[round(v, 2) for v in (
                x0 + sh[0], x1 + sh[0], y0 + sh[1], y1 + sh[1], z0, z1)]))

    def deck_tab(xe, ye, n, z_t, btop, part, sh, standing=None, w=None):
        """R146 bar hold-down snap tab (spec.BAR_TAB) at the point (xe, ye) on a bar edge, n = outward axis normal (+-1, 0) / (0, +-1).
        Deck tab: the arm is the pocket wall freed by a U slot `root` deep; standing = (z_floor, s0): a free arm standing on the floor s0
        out from the bar edge (battery block, the bar on its pedestal). The hook reaches `over` past the bar edge, 0.1 over the bar top,
        45 deg lead-in. Returns (cuts, bodies to add)."""
        TB = dict(S.BAR_TAB)
        s0 = (S.CLR + TB['slot']) if standing is None else standing[1]     # deck tab: a slot on the bar side too, so the arm flexes its whole length
        if standing is not None:
            TB['t'] = TB['t_stand']
            if REV[0] == 7:
                TB['w'] = TB['w_stand']     # markup 2026-10-17 (Dan 23-06: "make these 2 tabs bigger")
        if w is not None:
            TB['w'] = w
        hw = TB['w'] / 2

        def bx(sa, sb, ua, ub, za, zb):          # box in (s along n, u along the edge, z)
            if n[0]:
                xs = (xe + n[0] * sa, xe + n[0] * sb)
                return box(min(xs), ye + ua, za, max(xs), ye + ub, zb)
            ys = (ye + n[1] * sa, ye + n[1] * sb)
            return box(xe + ua, min(ys), za, xe + ub, max(ys), zb)
        zr = (z_t - TB['root']) if standing is None else standing[0]
        cuts_ = []
        if standing is None:
            cuts_ += [bx(S.CLR - 0.01, s0 + TB['t'] + TB['slot'], -hw - TB['slot'], hw + TB['slot'], zr, z_t + 1)]   # slot ring round the arm
        zh0 = btop + (S.HOOK_GAP if REV[0] == 7 else 0.1)    # markup 2026-10-17 (R157): the hook bears on the copper, no gap
        zh1 = zh0 + TB['hook_t']
        arm = bx(s0, s0 + TB['t'], -hw, hw, zr - 0.01, zh1)                 # rooted at the slot bottom (deck) / on the floor
        hook = bx(-TB['over'], s0 + TB['t'], -hw, hw, zh0, zh1)
        sx_, sy_ = (n[0], n[1])
        if REV[0] == 7:     # lead-in at TB['lead'] deg from the vertical (HP: 35 - 40), from the tip's bottom edge + 0.3 up
            ta_ = math.tan(math.radians(TB['lead']))
            half_cut(hook, (xe - sx_ * TB['over'], ye - sy_ * TB['over'], zh0 + 0.3), (-sx_, -sy_, ta_))
        else:
            half_cut(hook, (xe - sx_ * TB['over'], ye - sy_ * TB['over'], zh0 + 0.3), (-sx_, -sy_, 1.0))    # lead-in on the bar side
        bo(arm, hook, 'u')
        L_ = (zh0 - zr)
        d_ = TB['over'] + (S.CLR if REV[0] == 7 else 0.0)   # the hook tip has to move out to the bar edge (+ the pocket clearance, worst)
        I_ = TB['w'] * TB['t'] ** 3 / 12.0
        report.setdefault('bar_tabs', []).append(dict(part=part, at=[round(xe, 1), round(ye, 1)], n=list(n), arm_mm=round(L_, 1), deflection_mm=round(d_, 2),
                                                      strain_pct=round(100 * 1.5 * TB['t'] * d_ / L_ ** 2, 2), limit_pct=S.SNAP_EPS, t=TB['t'], w=TB['w'],
                                                      over=TB['over'], hook_t=TB['hook_t'], gap=round(zh0 - btop, 2),
                                                      push_N=round(3 * S.PA12['E'] * I_ * d_ / L_ ** 3, 1)))
        lo_ = [-TB['over'] - 0.3, s0 + TB['t'] + TB['slot'] + 0.3]
        e_ = bx(lo_[0], lo_[1], -hw - TB['slot'] - 0.3, hw + TB['slot'] + 0.3, zr - 0.3, zh1 + 0.3).boundingBox
        exempt(part, 'bar snap tab', e_.minPoint.x * 10, e_.maxPoint.x * 10, e_.minPoint.y * 10, e_.maxPoint.y * 10, e_.minPoint.z * 10, e_.maxPoint.z * 10, sh)
        return cuts_, [arm]

    def groove_join(L, z_d, rects, reach=0.01):
        """R127 sweep (rev 7): a cut (zlo, zhi, x0, x1, y0, y1) that comes closer than min_wall to the groove inside the skirt where the
        belly-pan wall slides up runs on into it over the groove height - no sliver of PA12 left standing between them (the pan wall
        and the cavity keep their sizes; the pan still slides straight up)."""
        if REV[0] != 7:
            return []
        m, zg, mw = S.SKIRT + 2 * W_CL + PN['t'], z_d + PN['over'] + W_CL, S.HOLE['min_wall']
        out = []
        for (lo, hi, x0, x1, y0, y1) in rects:
            lo_, hi_ = max(lo, z_d - 1.0), min(hi, zg)
            if hi_ <= lo_:
                continue
            for (gap, b) in ((x0 - m, (m - 0.01, x0 + reach, y0, y1)), (L - m - x1, (x1 - reach, L - m + 0.01, y0, y1)),
                             (y0 - m, (x0, x1, m - 0.01, y0 + reach)), (DIM['D'] - m - y1, (x0, x1, y1 - reach, DIM['D'] - m + 0.01))):
                if 0 < gap < mw:
                    out.append(box(b[0], b[2], lo_, b[1], b[3], hi_))
                    report.setdefault('groove_joins', []).append([round(v, 2) for v in (x0, x1, y0, y1, lo_, hi_, gap)])
        return out

    def slot_z0(box_name, x, y, z_d, z_t, l_min):
        """R127 sweep (rev 7): bottom of a relay / fuse blade slot. Where an R120 terminal cavity is cut under the pin, the slot is only the
        part above the receptacle seat (the cavity below is the R120 hole; the old full-height slot only shaved slivers off its walls).
        Where no terminal sits (an 87a with no wire), it is as deep as the blade can reach - the shortest receptacle that relay's other
        blades seat in (l_min) - and solid below."""
        if REV[0] != 7:
            return z_d - 1
        for h in report['terminal_holes'].get(box_name, []):
            if abs(h['x'] - x) < 1.0 and abs(h['y'] - y) < 1.0:
                return z_t - S.seat_gap(h['part'], h['kind']) - 0.01
        return z_t - S.HOLE['top_gap'] - l_min

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
        if wall and REV[0] != 7:    # R127 sweep (rev 7): solid buttress - the hollow one left a knife edge where the socket cut its
            # sloped wall and held the foot by sloped 3.0 walls only; the outside, the foot, the hole and the socket are unchanged
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
        front = DIM.get('snaps_front') or snap_xs(L)
        return [(x, 0.0) for x in front] + [(x, DIM['D']) for x in rear]

    def xcatch_screw_y(y):
        return y + S.SCREW['off'] if y < DIM['D'] / 2 else y - S.SCREW['off']

    def xcatch_cuts(L, z_t, part, sh):
        """Markup 2026-10-17 (Dan 23-30, R158): cover catches on the END faces (x) too - the pocket for the cover bump in the skirt's outer
        face and, where it fits, the R122 heat-set insert beside it (toward the middle of the face)."""
        out = []
        zc = z_t - S.SNAP['z_from_top']
        zi = z_t - S.SCREW['z_from_top']
        hw = S.SNAP['w'] / 2 + 0.5 + S.HOLE['min_wall']
        for (face, y, screw) in DIM.get('xcatch', ()):
            sg = -1 if face == '-x' else 1
            xo = -DIM['so'] if sg < 0 else L + DIM['so']
            out.append(cyl((xo, y - S.SNAP['w'] / 2 - 0.5, zc), (xo, y + S.SNAP['w'] / 2 + 0.5, zc), S.SNAP['bump'] + 0.2))
            xi = (S.SKIRT + 0.1) if sg < 0 else (L - S.SKIRT - 0.1)
            exempt(part, 'cover catch pocket', min(xo - sg * 0.1, xi), max(xo - sg * 0.1, xi), y - hw, y + hw,
                   zc - S.SNAP['bump'] / 2 - 2.2, zc + S.SNAP['bump'] / 2 + 2.2, sh)
            if screw:
                ys = xcatch_screw_y(y)
                out.append(cyl((xo + sg * 0.5, ys, zi), (xo - sg * S.SCREW['ins_depth'], ys, zi), S.SCREW['d_ins']))
                exempt(part, 'cover screw insert', min(xo + sg * 0.1, xo - sg * (S.SCREW['ins_depth'] + 2.6)), max(xo + sg * 0.1, xo - sg * (S.SCREW['ins_depth'] + 2.6)),
                       ys - S.SCREW['d_ins'] / 2 - 2.2, ys + S.SCREW['d_ins'] / 2 + 2.2, zi - S.SCREW['d_ins'] / 2 - 2.2, zi + S.SCREW['d_ins'] / 2 + 2.2, sh)
        return out

    def screw_points(L, faces, outward=False):
        """R122: (x, face y, inward sign) of the optional backup screw beside each cover catch, `off` toward the middle of the wall
        (outward=True: toward the end - the battery block, where the relay flange sits by the middle of the rear rim)."""
        out = []
        for (x, yface) in faces:
            xs = x + S.SCREW['off'] if (x < L / 2) != outward else x - S.SCREW['off']
            out.append((xs, yface, 1 if yface == 0.0 else -1))
        return out

    def screw_bosses(L, D, z_t, wall, z_lo, z_hi, faces, outward=False):
        """R122: the insert bosses - boss_w wide, boss_depth in from the inner face of a `wall` thick side, z_lo..z_hi (joined to the deck
        plate or the floor: never floating, R101)."""
        SC = S.SCREW
        out = []
        for (xs, yf, sg) in screw_points(L, faces, outward):
            yi = wall if sg > 0 else D - wall
            out.append(box(xs - SC['boss_w'] / 2, min(yi, yi + sg * SC['boss_depth']) - (0.01 if sg < 0 else 0), z_lo,
                           xs + SC['boss_w'] / 2, max(yi, yi + sg * SC['boss_depth']) + (0.01 if sg > 0 else 0), z_hi))
        return out

    def screw_inserts(L, D, zc, faces, outward=False):
        """R122: the heat-set insert holes, from the outer face inward (d_ins, ins_depth deep)."""
        SC = S.SCREW
        so = DIM['so']            # R127 amendment: from the outer face, which moved out by so
        return [cyl((xs, (-so if sg > 0 else D + so) - sg * 0.5, zc), (xs, (-so if sg > 0 else D + so) + sg * SC['ins_depth'], zc), SC['d_ins'])
                for (xs, yf, sg) in screw_points(L, faces, outward)]

    def base_shell(L, z_d, z_t, extra_parts):
        """Deck: top plate + perimeter skirt (rounded plan), open underneath; the skirt carries the snap pockets."""
        R, so = S.BASE_R, DIM['so']
        plate = rrect(-so, -so, L + so, DIM['D'] + so, z_t - S.PLATE, z_t, R + so)
        skirt = rrect(-so, -so, L + so, DIM['D'] + so, z_d, z_t - S.PLATE + 0.01, R + so)
        bo(skirt, rrect(S.SKIRT, S.SKIRT, L - S.SKIRT, DIM['D'] - S.SKIRT, z_d - 1, z_t, R - S.SKIRT), 's')
        zsc = z_t - S.SCREW['z_from_top']           # R122: insert bosses beside the cover catches, hanging from the deck plate
        bosses = screw_bosses(L, DIM['D'], z_t, S.SKIRT, zsc - S.SCREW['boss_h'] / 2, z_t - S.PLATE + 0.01, cover_catches(L))
        return union_all([plate, skirt] + extra_parts + bosses)

    def base_snap_cuts(L, z_t, z_d, pan_faces, part='', sh=(0.0, 0.0)):
        """Pockets in the skirt: for the cover catches (outer face, near the top) and the belly-pan catches (inner face,
        near the bottom). Also clears the ring inside the skirt where the pan wall slides up."""
        zc = z_t - S.SNAP['z_from_top']
        hw, D_ = S.SNAP['w'] / 2 + 0.5 + S.HOLE['min_wall'], DIM['D']
        for (x, y) in cover_catches(L):
            exempt(part, 'cover catch pocket', x - hw, x + hw, (-DIM['so'] - 0.1 if y == 0.0 else D_ - S.SKIRT - 0.1), (S.SKIRT + 0.1 if y == 0.0 else D_ + DIM['so'] + 0.1),
                   zc - S.SNAP['bump'] / 2 - 2.2, zc + S.SNAP['bump'] / 2 + 2.2, sh)
        zi_ = z_t - S.SCREW['z_from_top']
        for (xs_, yf_, sg_) in screw_points(L, cover_catches(L)):
            ya_ = -DIM['so'] if sg_ > 0 else D_ + DIM['so']       # the outer face
            exempt(part, 'cover screw insert', xs_ - S.SCREW['d_ins'] / 2 - 2.2, xs_ + S.SCREW['d_ins'] / 2 + 2.2, min(ya_ - 0.1, ya_ + sg_ * (S.SCREW['ins_depth'] + 2.6)),
                   max(ya_ + 0.1, ya_ + sg_ * (S.SCREW['ins_depth'] + 2.6)), zi_ - S.SCREW['d_ins'] / 2 - 2.2, zi_ + S.SCREW['d_ins'] / 2 + 2.2, sh)
        zq_ = z_d + PN['over'] / 2
        for (axis, pos) in pan_snaps(L, pan_faces):
            for far in (0, 1):
                if axis == 'y':
                    exempt(part, 'pan catch pocket', pos - hw, pos + hw, (-0.1 if not far else D_ - S.SKIRT - 1.5), (S.SKIRT + 1.5 if not far else D_ + 0.1),
                           z_d - 1.1, zq_ + S.SNAP['bump'] / 2 + 2.2, sh)
                else:
                    exempt(part, 'pan catch pocket', (-0.1 if not far else L - S.SKIRT - 1.5), (S.SKIRT + 1.5 if not far else L + 0.1), pos - hw, pos + hw,
                           z_d - 1.1, zq_ + S.SNAP['bump'] / 2 + 2.2, sh)
        cuts = screw_inserts(L, DIM['D'], z_t - S.SCREW['z_from_top'], cover_catches(L))     # R122 heat-set insert holes
        cuts += xcatch_cuts(L, z_t, part, sh)
        for (x, y) in cover_catches(L):
            yo_ = y - DIM['so'] if y == 0.0 else y + DIM['so']      # the outer face (R127 amendment: moved out by so)
            cuts.append(cyl((x - S.SNAP['w'] / 2 - 0.5, yo_, zc), (x + S.SNAP['w'] / 2 + 0.5, yo_, zc), S.SNAP['bump'] + 0.2))
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

    def belly_pan(L, z_d, faces, exits, pre, sh, rib=None, reliefs=(), walls=(), box_name=None):
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
        part_ = pre + 'Pan_PA12_printed'
        for (axis, pos) in pan_snaps(L, faces):
            for side in (0, 1):
                a0, a1 = pos - sw['w'] / 2 - sw['slot'] - 1.0, pos + sw['w'] / 2 + sw['slot'] + 1.0
                if axis == 'y':
                    yf = y0 if side == 0 else y1
                    exempt(part_, 'pan snap tongue', a0, a1, yf - sw['bump'] / 2 - 0.3 - (t if side else 0), yf + sw['bump'] / 2 + 0.3 + (0 if side else t),
                           ztop - sw['len'] - 1.0, ztop + 0.1, sh)
                else:
                    xf = x0 if side == 0 else x1
                    exempt(part_, 'pan snap tongue', xf - sw['bump'] / 2 - 0.3 - (t if side else 0), xf + sw['bump'] / 2 + 0.3 + (0 if side else t), a0, a1,
                           ztop - sw['len'] - 1.0, ztop + 0.1, sh)
        joins = []
        if REV[0] == 7:   # R127 sweep: between two exit notches in one wall closer than min_wall the wall is cut away, centre to centre,
            # down to the higher notch bottom (the notches keep their own U shape, so no wire comes closer to the pan)
            ex_ = sorted(exits, key=lambda e: (e[0], e[4], e[1]))
            for e1, e2 in zip(ex_, ex_[1:]):
                if e1[0] == e2[0] and e1[4] == e2[4] and (e2[1] - e2[3] / 2) - (e1[1] + e1[3] / 2) < S.HOLE['min_wall']:
                    joins.append((e1[0], e1[1], e2[1], max(e1[2], e2[2]), e1[4]))
                    report.setdefault('pan_exits_joined', []).append(pre + '%s %.1f-%.1f' % (e1[0], e1[1], e2[1]))
        for (axis, u, zb_, wd, side) in exits:
            lo_, hi_ = (y0, y1) if axis == 'x' else (x0, x1)
            if u - wd / 2 < lo_ + R or u + wd / 2 > hi_ - R:      # R127 sweep: an exit notch that runs into a rounded corner of the pan
                if axis == 'x':
                    xw_ = x0 + t / 2 if side < 0 else x1 - t / 2
                    exempt(part_, 'notch at corner', xw_ - 4.1, xw_ + 4.1, u - wd / 2 - 3.0, u + wd / 2 + 3.0, zb_ - 0.1, ztop + 0.1, sh)
                else:
                    yw_ = y0 + t / 2 if side < 0 else y1 - t / 2
                    exempt(part_, 'notch at corner', u - wd / 2 - 3.0, u + wd / 2 + 3.0, yw_ - 4.1, yw_ + 4.1, zb_ - 0.1, ztop + 0.1, sh)
            if REV[0] == 7 and PN['z0'] + 0.01 < zb_ < PN['z0'] + t - 0.01:
                # R127 sweep: a notch that dips into the floor - the floor under it is thickened downward to min_wall (inside the legs' plane)
                pad_z0 = max(0.5, zb_ - S.HOLE['min_wall'])
                if axis == 'x':
                    xw_ = x0 if side < 0 else x1
                    bo(pan, box(min(xw_, xw_ - side * (wd / 2 + 4)), u - wd / 2 - 2, pad_z0, max(xw_, xw_ - side * (wd / 2 + 4)), u + wd / 2 + 2, PN['z0'] + 0.01), 'u')
                else:
                    yw_ = y0 if side < 0 else y1
                    bo(pan, box(u - wd / 2 - 2, min(yw_, yw_ - side * (wd / 2 + 4)), pad_z0, u + wd / 2 + 2, max(yw_, yw_ - side * (wd / 2 + 4)), PN['z0'] + 0.01), 'u')
                report.setdefault('pan_floor_pads', []).append(pre + '%s %.1f' % (axis, u))
            if axis == 'x':
                xw = x0 + t / 2 if side < 0 else x1 - t / 2
                n = box(xw - 4, u - wd / 2, zb_ + wd / 2, xw + 4, u + wd / 2, ztop + 1)
                bo(n, cyl((xw - 4, u, zb_ + wd / 2), (xw + 4, u, zb_ + wd / 2), wd), 'u')
            else:
                yw = y0 + t / 2 if side < 0 else y1 - t / 2
                n = box(u - wd / 2, yw - 4, zb_ + wd / 2, u + wd / 2, yw + 4, ztop + 1)
                bo(n, cyl((u, yw - 4, zb_ + wd / 2), (u, yw + 4, zb_ + wd / 2), wd), 'u')
            bo(pan, n, 's')
        for (axis, u1, u2, zb_, side) in joins:
            if axis == 'x':
                xw = x0 + t / 2 if side < 0 else x1 - t / 2
                bo(pan, box(xw - 4, u1, zb_, xw + 4, u2, ztop + 1), 's')
            else:
                yw = y0 + t / 2 if side < 0 else y1 - t / 2
                bo(pan, box(u1, yw - 4, zb_, u2, yw + 4, ztop + 1), 's')
        if rib:      # J2 = B (R94): a rib standing on the pan floor (rib = (x0, x1, y0, y1, z_top))
            bo(pan, box(rib[0], rib[2], PN['z0'] + t - 0.01, rib[1], rib[3], rib[4]), 'u')
        for (wx0, wx1, wy0, wy1, wz) in walls:   # markup 2026-10-17 (23-12 / 23-33): wire-group walls on the pan floor, root fillets both sides
            bo(pan, box(wx0, wy0 - 0.01, PN['z0'] + t - 0.01, wx1, wy1, wz), 'u')
            for f_ in root_fillets(wx0, wy0, wx1, wy1 - S.FILLET_R, PN['z0'] + t, S.FILLET_R, 'x'):
                bo(pan, f_, 'u')
            report.setdefault('logic_group_walls', []).append([round(v, 2) for v in (wx0, wx1, wy0, wy1, wz)])
        for (ya, yb, depth) in reliefs:   # J2 = B: the +x wall's inner face cut back `depth` over y ya..yb (the 86 wires drop 1 mm from it)
            bo(pan, box(x1 - t - 0.01, ya, PN['z0'] + t, x1 - t + depth, yb, ztop + 1.0), 's')
        if PLAN7 and box_name:   # fit audit 2026-10-18: a terminal's R120 hole zone (crimped barrels + 0.4) that runs into a pan wall's inner face
            # cuts that face back to the zone edge over the zone's width - never below HOLE min_wall 2.0 (R73); deeper is reported, not cut
            mw_ = S.HOLE['min_wall']
            for c in PLAN7['cavities']:
                if c['box'] != box_name or not c.get('zones') or (c['kind'].endswith('87a') and c['source'] != 'harness'):
                    continue
                zb_ = c['zones'][0]
                ax0, ax1, ay0, ay1 = c['x'] + zb_[2], c['x'] + zb_[3], c['y'] + zb_[4], c['y'] + zb_[5]
                for (need, cut_, side) in ((x0 + t - ax0, lambda d_: box(x0 + t - d_, ay0, PN['z0'] + t, x0 + t + 0.01, ay1, ztop + 1.0), '-x'),
                                           (ax1 - (x1 - t), lambda d_: box(x1 - t - 0.01, ay0, PN['z0'] + t, x1 - t + d_, ay1, ztop + 1.0), '+x'),
                                           (y0 + t - ay0, lambda d_: box(ax0, y0 + t - d_, PN['z0'] + t, ax1, y0 + t + 0.01, ztop + 1.0), '-y'),
                                           (ay1 - (y1 - t), lambda d_: box(ax0, y1 - t - 0.01, PN['z0'] + t, ax1, y1 - t + d_, ztop + 1.0), '+y')):
                    if need <= 0 or (side in ('-x', '+x') and (ay1 < y0 or ay0 > y1)) or (side in ('-y', '+y') and (ax1 < x0 or ax0 > x1)):
                        continue
                    if need <= t - mw_:
                        bo(pan, cut_(need), 's')
                        report.setdefault('pan_terminal_relief', []).append(dict(box=box_name, cav=c['cav'], wall=side, kind='relief', depth=round(need, 2)))
                        continue
                    # deeper than the wall can give: a notch open at the wall top down to 0.5 under the terminal's end (as the JB1 lug-tongue notch);
                    # the base skirt still closes the outside
                    zl_ = (S.LOGIC if box_name == 'LOGIC' else S.POWER)['z_t'] - S.seat_gap(c['part'], c['kind']) - (S.TERM[c['part']]['L'] or S.L_EST) - 0.5
                    nb_ = {'-x': (x0 - 1.0, ay0, x0 + t + 0.01, ay1), '+x': (x1 - t - 0.01, ay0, x1 + 1.0, ay1),
                           '-y': (ax0, y0 - 1.0, ax1, y0 + t + 0.01), '+y': (ax0, y1 - t - 0.01, ax1, y1 + 1.0)}[side]
                    zn_ = max(zl_, PN['z0'] + t + 1.0)
                    bo(pan, box(nb_[0], nb_[1], zn_, nb_[2], nb_[3], ztop + 1.0), 's')
                    ax_w, sd_w = ('x', -1 if side == '-x' else 1) if side[1] == 'x' else ('y', -1 if side == '-y' else 1)
                    lo_n, hi_n = (ay0, ay1) if ax_w == 'x' else (ax0, ax1)
                    for (e_ax, e_u, e_zb, e_wd, e_sd) in exits:    # R127 join: a wall sliver under min_wall to a wire-exit notch is cut away
                        if e_ax != ax_w or e_sd != sd_w:
                            continue
                        for (g0, g1) in ((e_u + e_wd / 2, lo_n), (hi_n, e_u - e_wd / 2)):
                            if -0.01 <= g1 - g0 < mw_:
                                jb_ = (nb_[0], g0 - 0.01, nb_[2], g1 + 0.01) if ax_w == 'x' else (g0 - 0.01, nb_[1], g1 + 0.01, nb_[3])
                                bo(pan, box(jb_[0], jb_[1], max(zn_, e_zb + e_wd / 2), jb_[2], jb_[3], ztop + 1.0), 's')
                                report.setdefault('pan_exits_joined', []).append(pre + 'terminal %s - exit %.1f' % (c['cav'], e_u))
                    report.setdefault('pan_terminal_relief', []).append(dict(box=box_name, cav=c['cav'], wall=side, kind='notch', need=round(need, 2),
                                                                              z=[round(zl_, 2), round(ztop, 2)], width=round(nb_[3] - nb_[1] if side[1] == 'x' else nb_[2] - nb_[0], 2)))
        return comp(pre + 'Pan_PA12_printed', pan, AP['pa12_pan'], MAT['pa'], sh)

    def cover(L, D, z_t, z_top, notches, label_list, pre, sh, vents=(), ribs=None, side_vents=(), x0=0.0, y0=0.0, R=None, r=None,
              zb=None, zc=None, inner_R=None, inner_r=None, screw_z=None, screw_out=False, screw_faces=None):
        """Rounded snap-on cover over a base L x D (base outline from (x0, y0)). notches = [(axis, pos, centre_u, z_top_of_notch, width)]:
        a U-notch open at the bottom edge in the end (axis 'x') or side (axis 'y') wall. Rev 5: bumper band round the bottom,
        vertical ribs on the walls (ribs = {'y': [x...], 'x': [y...]}), vent slots through the top (vents = [(x, y, along)])
        and the walls (side_vents = [(face, u, z)]). Returns the occurrence."""
        so = DIM['so']
        g, t = W_CL + so, CV['t']        # R127 amendment: the base outline moved out by so - the cover follows, same clearances
        R = (CV['R'] if R is None else R) + so
        r = CV['r'] if r is None else r
        inner_R = inner_R + so if inner_R is not None else None
        notches = [(ax, (pos + so if pos > (x0 + L / 2 if ax == 'x' else y0 + D / 2) else pos - so), u, zn, wd) for (ax, pos, u, zn, wd) in notches]
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
        zs_ = z_t - S.SCREW['z_from_top'] if screw_z is None else screw_z
        part_ = pre + 'Cover_PA12_printed'
        for (face, y, screw) in DIM.get('xcatch', ()):    # markup 2026-10-17 (R158): catches in the end walls
            sg = -1 if face == '-x' else 1
            xf = x0 - g if sg < 0 else x0 + L + g          # inner face of the end wall
            for dy in (-1, 1):
                ys_ = y0 + y + dy * (sw['w'] / 2 + sw['slot'] / 2)
                xa_, xb3 = (xf - t - bo_ - 1, xf + 1) if sg < 0 else (xf - 1, xf + t + bo_ + 1)
                bo(out, box(xa_, ys_ - sw['slot'] / 2, zb - 1, xb3, ys_ + sw['slot'] / 2, zb + sw['len']), 's')
            bo(out, cyl((xf, y0 + y - sw['w'] / 2 + 0.5, zc), (xf, y0 + y + sw['w'] / 2 - 0.5, zc), sw['bump']), 'u')
            xa_, xb3 = (xf - t - bo_ - 0.1, xf + sw['bump'] / 2 + 0.3) if sg < 0 else (xf - sw['bump'] / 2 - 0.3, xf + t + bo_ + 0.1)
            exempt(part_, 'cover snap tongue', xa_, xb3, y0 + y - sw['w'] / 2 - sw['slot'] - 1.0, y0 + y + sw['w'] / 2 + sw['slot'] + 1.0, zb - 0.1, zb + sw['len'] + 1.0, sh)
            if screw:
                ys = y0 + xcatch_screw_y(y)
                bo(out, cyl((xf + sg * (t + bo_ + 1), ys, zs_), (xf - sg * 1.0, ys, zs_), S.SCREW['d_clear']), 's')
                xa_, xb3 = (xf - t - bo_ - 0.1, xf + 0.1) if sg < 0 else (xf - 0.1, xf + t + bo_ + 0.1)
                exempt(part_, 'cover screw hole', xa_, xb3, ys - S.SCREW['d_clear'] / 2 - 2.2, ys + S.SCREW['d_clear'] / 2 + 2.2,
                       min(zb - 0.1, zs_ - S.SCREW['d_clear'] / 2 - 2.2), zs_ + S.SCREW['d_clear'] / 2 + 2.2, sh)
        for (x, yface) in cover_catches(L):
            yf = y0 - g if yface == 0.0 else y0 + D + g
            ya, yb_ = (yf - t - bo_ - 0.1, yf + sw['bump'] / 2 + 0.3) if yface == 0.0 else (yf - sw['bump'] / 2 - 0.3, yf + t + bo_ + 0.1)
            exempt(part_, 'cover snap tongue', x0 + x - sw['w'] / 2 - sw['slot'] - 1.0, x0 + x + sw['w'] / 2 + sw['slot'] + 1.0, ya, yb_, zb - 0.1, zb + sw['len'] + 1.0, sh)
        for (xs, yface, sg) in screw_points(L, screw_faces if screw_faces is not None else cover_catches(L), screw_out):
            yf = y0 - g if yface == 0.0 else y0 + D + g
            ya, yb_ = (yf - t - bo_ - 0.1, yf + 0.1) if yface == 0.0 else (yf - 0.1, yf + t + bo_ + 0.1)
            exempt(part_, 'cover screw hole', x0 + xs - S.SCREW['d_clear'] / 2 - 2.2, x0 + xs + S.SCREW['d_clear'] / 2 + 2.2, ya, yb_,
                   min(zb - 0.1, zs_ - S.SCREW['d_clear'] / 2 - 2.2), zs_ + S.SCREW['d_clear'] / 2 + 2.2, sh)
        for (xs, yface, sg) in screw_points(L, screw_faces if screw_faces is not None else cover_catches(L), screw_out):    # R122: clearance hole for the optional backup screw
            yf = y0 - g if yface == 0.0 else y0 + D + g
            bo(out, cyl((x0 + xs, yf - sg * (t + bo_ + 1), zs_), (x0 + xs, yf + sg * 1.0, zs_), S.SCREW['d_clear']), 's')
        for (axis, pos, u, zn, wd) in notches:
            lo_, hi_ = (y0, y0 + D) if axis == 'x' else (x0, x0 + L)
            if u - wd / 2 < lo_ - g - t + R or u + wd / 2 > hi_ + g + t - R:      # R127 sweep: a notch that runs into a rounded corner
                if axis == 'x':
                    exempt(part_, 'notch at corner', pos - 6.1, pos + 6.1, u - wd / 2 - 3.0, u + wd / 2 + 3.0, zb - 0.1, zn + 0.6, sh)
                else:
                    exempt(part_, 'notch at corner', u - wd / 2 - 3.0, u + wd / 2 + 3.0, pos - 6.1, pos + 6.1, zb - 0.1, zn + 0.6, sh)
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

    def markup_1017_power(L, D7, z_d, z_t, btop, xb, B_, NB, ami, sh):
        """Dan's markup 2026-10-17 on the POWER base (DECISIONS R157 - R160). Returns the printed bodies to add to the base:
        (1) lug pockets (23-18 / 23-27 / 23-31) - walls + raised floor where every bus lug's tongue / barrel leaves the copper;
        (2) the NEG front wall (23-31 'add more wall here') and root fillets on it and on the R7 barrier (23-31 'strengthening ... ALL walls');
        (3) the under-deck isolation ribs between the strap stations, both rows (23-27 T walls / 23-33 tall features), widened to a pocket
            at every palm-up output lug, tied by a bottom rail at the far end of each row."""
        PK, R7_, fr = S.POCKET, S.REV7, S.FILLET_R
        out, rep_ = [], report.setdefault('markup_1017', {})
        so, x_end = DIM['so'], L + DIM['so'] - 0.01
        z_fl = btop - PK['under']                                  # pocket floor, under the palm underside
        # ---- (1a) POS bus lugs: tongue out +x over the deck - walls b + 2 clr apart, x from the bar pocket edge to the base edge
        bpe = xb + B_['w'] / 2 + S.CLR
        lugs_ = [y_ for (y_, nm, h_) in R7_['pos_studs'] if nm != 'SPARE']
        hw_ = S.LUG_M8['b'] / 2 + PK['clr']
        zt_ = z_t + S.POS_WALL_H
        walls = []
        for k, y_ in enumerate(lugs_):
            out.append(box(bpe, y_ - hw_, z_t - 0.01, x_end, y_ + hw_, z_fl))                       # floor under the tongue / barrel
            lo, hi = (y_ - hw_ - PK['wall'], y_ - hw_), (y_ + hw_, y_ + hw_ + PK['wall'])
            x0_lo = bpe if k else 147.4                         # BAT+ front wall starts behind the bar tab at y 164 (its arm is the palm's wall there)
            walls += [(x0_lo, lo), (bpe, hi)]
        seen = set()
        for (x0_, (ya, yb)) in walls:
            key = (round(ya, 2), round(yb, 2))
            if key in seen:
                continue
            seen.add(key)
            out.append(box(x0_, ya, z_t - 0.01, x_end, yb, zt_))
        # root fillets on the outer faces only (the pocket faces carry the raised floor; a fillet there would press on the palm edge)
        out += root_fillets(147.4, lugs_[0] - hw_ - PK['wall'], x_end, lugs_[0] - hw_, z_t, fr, 'y')[:1]
        out += root_fillets(bpe, lugs_[-1] + hw_, x_end, lugs_[-1] + hw_ + PK['wall'], z_t, fr, 'y')[1:]
        rep_['pos_pockets'] = dict(lugs=lugs_, slot=round(2 * hw_, 2), wall=PK['wall'], floor=round(z_fl, 2), wall_top=zt_, x=[round(bpe, 2), round(x_end, 2)])
        # ---- (1b) NEG bus lugs: tongues out +y past the bar's rear edge - walls between the tongues (one ground node, R135: 2.2 where 3 is not there)
        neg = [(x_, S.LUG_M8['b'] if g_ == '1/0' else R7_['small_ring_b']) for (x_, nm, h_, g_) in R7_['neg_studs']]
        y0_ = NB['yc'] + B_['w'] / 2 + S.CLR
        y1_ = D7 + so - 0.01
        zn_ = btop + S.LUG_M8['t'] + PK['h_over_palm']
        out.append(box(S.SKIRT - 0.01, y0_, z_t - 0.01, R7_['barrier'][0] + 0.01, y1_, z_fl))   # floor under every tongue
        nw = []
        for (xa, ba), (xc, bc) in zip(neg, neg[1:]):
            f0, f1 = xa + ba / 2 + PK['clr'], xc - bc / 2 - PK['clr']
            if f1 - f0 >= PK['wall_min']:
                out.append(box(f0, y0_, z_fl - 0.01, f1, y1_, zn_))
                nw.append([round(f0, 2), round(f1, 2)])
                exempt('Power_Base_PA12_printed', 'lug pocket wall', f0 - 0.3, f1 + 0.3, y0_ - 0.3, y1_ + 0.3, z_fl - 0.5, zn_ + 0.3, sh, only='A')
            else:
                rep_.setdefault('neg_pocket_shared', []).append(dict(x=[xa, xc], gap=round(f1 - f0, 2)))
        x_lo, x_hi = neg[0][0] - neg[0][1] / 2 - PK['clr'], neg[-1][0] + neg[-1][1] / 2 + PK['clr']
        out.append(box(-so, y0_, z_fl - 0.01, x_lo, y1_, zn_))                                   # outer walls: skirt side, out to the base edge ...
        out.append(box(x_hi, y0_, z_fl - 0.01, R7_['barrier'][1], y1_, zn_))                       # ... and barrier side, the barrier's full width
        rep_['neg_pockets'] = dict(walls=nw, outer=[round(x_lo, 2), round(x_hi, 2)], floor=round(z_fl, 2), top=round(zn_, 2), y=[round(y0_, 2), round(y1_, 2)])
        # ---- (2) NEG front wall + root fillets, R7 barrier root fillets
        NW = S.NEG_FRONT_WALL
        wy0, wy1 = NW['y']
        bx0, bx1 = R7_['barrier']
        out.append(box(NW['x0'], wy0, z_t - 0.01, bx0 + 0.01, wy1, z_t + R7_['barrier_h']))
        out += root_fillets(NW['x0'], wy0, bx0, wy1, z_t, fr, 'y')
        out += root_fillets(bx0, 168.0, bx1, D7 - S.SKIRT, z_t, 1.5, 'x')[1:]                    # +x side: 1.5 keeps 0.4 off the POS bar pocket
        out += root_fillets(bx0, 168.0, bx1, NB['yc'] - B_['w'] / 2 - S.CLR - 0.4, z_t, fr, 'x')[:1]   # -x side: in front of the NEG bar only
        rep_['neg_front_wall'] = dict(y=list(NW['y']), x=[NW['x0'], bx0], top=z_t + R7_['barrier_h'], fillet=fr)
        # ---- (3) under-deck isolation ribs + output-lug palm pockets, both rows
        FN = S.FIN
        c_ = S.STRAP['clr']
        pan_in = L - S.SKIRT - W_CL - PN['t']
        rows = {}
        for a in ami:
            rows.setdefault(a['row'], []).append(a)
        fins_rep = {}
        for row, al in rows.items():
            al = sorted(al, key=lambda a: a['y'])
            s_ = al[0]['sgn']
            g0 = al[0]['g']
            if s_ > 0:
                xr = (g0['x_bl0'] - c_ - 1.0, pan_in - FN['pan_gap'])
            else:
                xr = (al[0]['x_lug'] - (S.LUG_M5['l'] - S.LUG_M5['tip']) - 0.3, g0['x_bl0'] + c_ + 1.0)
            bw = [(S.LUG_6AWG if a['amps'] and S.AMI_AWG[a['name']] == 6 else S.LUG_M5)['b'] for a in al]
            ys_ = [a['y'] for a in al]
            pitch = ys_[1] - ys_[0]
            fl = []
            for k in range(len(al) + 1):
                yf = ys_[0] - pitch / 2 + k * pitch
                out.append(box(xr[0], yf - FN['t'] / 2, FN['z0'], xr[1], yf + FN['t'] / 2, z_d + 0.01))
                lo_ = ys_[k - 1] + bw[k - 1] / 2 + PK['clr'] if k > 0 else yf - FN['t'] / 2
                hi_ = ys_[k] - bw[k] / 2 - PK['clr'] if k < len(al) else yf + FN['t'] / 2
                out.append(box(xr[0], lo_, FN['palm_z'][0], xr[1], hi_, FN['palm_z'][1]))
                fl.append([round(yf, 2), round(lo_, 2), round(hi_, 2)])
            fins_rep[row] = dict(x=[round(v, 2) for v in xr], ribs=fl, t=FN['t'], z=[FN['z0'], z_d], palm_z=list(FN['palm_z']))
        rep_['under_deck_ribs'] = fins_rep
        # everything stays inside the base's rounded plan outline (the NEG pockets run to the rear face, into its rounded corner)
        ol = rrect(-so, -so, L + so, D7 + so, -5.0, 200.0, S.BASE_R + so)
        for b_ in out:
            bo(b_, tb.copy(ol), 'i')
        return out

    # ================================================================== POWER box
    def build_power():
        PW = S.POWER
        L, xb, z_d, z_t, btop = PW['L'], PW['x_bar'], PW['z_d'], PW['z_t'], PW['bar_top']
        sh = S.PLACE['POWER']
        pre = 'Power_'
        D7 = R7['D'] if R7 else S.D                              # rev 7: + the bus zone at the rear
        DIM['D'] = D7
        DIM['snaps_rear'] = R7['cover_snaps_rear'] if R7 else None
        if R7:   # markup 2026-10-17 (Dan 23-30: "the larger the base, the more holding tabs it needs"): spec.POWER_CATCHES
            PC = S.POWER_CATCHES
            DIM['snaps_front'] = PC['-y']
            DIM['snaps_rear'] = PC['+y']
            DIM['xcatch'] = [('-x', y_, True) for y_ in PC['-x']] + [('+x', y_, False) for y_ in PC['+x']]
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
        ST = S.STRAP
        if R7:   # R155 (N14 = B): every position is a copper C-strap; the lug is bolted palm-up under its bottom leg
            for a in ami:
                s_, xo_ = a['sgn'], a['x_out']
                a['x_lug'] = xo_ + s_ * ST['lug']
                a['lz'] = ST['z_bl'] - LUG['t']                  # palm underside (LUG_M5 / LUG_6AWG palms are both 2.0)
                a['g'] = dict(x_tl0=xo_ - s_ * ST['top_in'], x_wi=xo_ + s_ * ST['web'][0], x_wo=xo_ + s_ * ST['web'][1],
                              x_lip=xo_ + s_ * (ST['web'][1] + ST['lip']), x_bl0=a['x_lug'] - s_ * S.STRAP_PEM['edge'], ro=ST['ri'] + ST['t'])
            report['straps'] = dict(z_bl=ST['z_bl'], lug_palm_underside=ST['z_bl'] - LUG['t'], top=(btop - ST['t'], btop), z_d=z_d, z_t=z_t,
                                    numbers=S.strap_numbers({a['name']: (a['amps'], S.AMI_AWG[a['name']]) for a in ami if a['amps']}),
                                    pem=S.STRAP_PEM['pn'], positions=len(ami))
        else:
            for a in ami:
                a['x_lug'] = a['x_out']
            report['standoffs']['POWER'] = dict(IN=SO['long'], OUT=SO['long'], in_lug_z=S.LUG_Z, out_lug_z=PW['out_lug_z'], z_d=z_d, z_t=z_t,
                                                plate_bottom=plate_b, pad_bottom=pz0)
        lug_c = (ST['z_bl'] - LUG['d4'] / 2) if R7 else S.LUG_C      # IN-row barrel centre (every relay feed lug is a Klauke 2R5 in the CAD)
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
        parts.append(cbox(acps[0], acps[1], z_d, plate_b + 0.01, 2 * S.MINI_BLADE_X + 3.0 + 2 * T, 4.6 + 2 * T))   # N21: 8.1 blade pitch
        if not R7:
            for a in ami:                                        # rev 6: standoff bosses, both rows (hex hole = anti-rotation)
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
            ccx, ccz = r['x30'] + S.R_SADDLE + od / 2, lug_c + S.R_SADDLE + od / 2
            rs = S.R_SADDLE - 0.2
            lw_ = od / 2 + 0.5 + S.HOLE['min_wall']      # R127: lips (and the saddle back) 2.0 thick, not 1.5
            core = bo(cyl((ccx, a['y'] - od / 2 - 0.5, ccz), (ccx, a['y'] + od / 2 + 0.5, ccz), 2 * rs),
                      box(ccx - rs - 1, a['y'] - 10, ccz - rs - 1, ccx, a['y'] + 10, ccz), 'i')
            for sy in (-1, 1):
                lip = bo(cyl((ccx, a['y'] + sy * (od / 2 + 0.5), ccz), (ccx, a['y'] + sy * lw_, ccz), 2 * (S.R_SADDLE + od * 0.6)),
                         box(ccx - S.R_SADDLE - od - 2, a['y'] - 10, ccz - S.R_SADDLE - od - 2, ccx, a['y'] + 10, ccz), 'i')
                bo(core, lip, 'u')
            top_ = box(ccx - rs, a['y'] - lw_, ccz - 0.01, ccx, a['y'] + lw_, z_d + 0.5)
            if R7:   # R101 (Dan 2026-10-15: "add material under the radius runners"): the saddle's back runs on up into the deck plate
                c0 = backing(top_, z_d + 0.5, U_sad)
                if c0 < S.FLOAT_BACKING:    # floating: carry it up into the deck plate
                    top_ = box(ccx - rs, a['y'] - lw_, ccz - 0.01, ccx, a['y'] + lw_, plate_b + 0.01)
                    after = backing(top_, plate_b + 0.01, [box(0, 0, plate_b, L, D7, z_t)])
                else:
                    after = c0
                report['feature_support'].setdefault('POWER', []).append(dict(
                    kind='saddle', at=[round(ccx - rs / 2, 1), round(a['y'], 1)], before=round(c0, 3), web=c0 < S.FLOAT_BACKING,
                    after=round(after, 3)))
            bo(core, top_, 'u')
            for sy in (-1, 1):   # sweep 2026-10-17: the 2.0 lips (R127 amendment keeps both) meet the saddle core along its whole curve
                ya_, yb_ = a['y'] + sy * (od / 2 + 0.5), a['y'] + sy * lw_
                exempt(pre + 'Base_PA12_printed', 'saddle lip', ccx - S.R_SADDLE - od - 2.3, ccx + 0.3, min(ya_, yb_) - 0.3, max(ya_, yb_) + 0.3,
                       ccz - S.R_SADDLE - od - 2.3, z_d + 0.3, sh, only='A')
            # R127 amendment (Dan 2026-10-16: "i liked the curved saddles. you should've kept those, just supported them underneath and cut out the
            # thin walls near the top"): the saddle keeps its whole curve and both lips (as before #268) and is carried by the block above it
            # (R101 back up into the deck plate); only near the top, where the relay's 30 cavity comes down into it, the saddle is cut away
            # across its full width from the cavity's lower end up and to min_wall past the cavity's +x wall - no thin wall or sliver left
            # between the curve and the cavity. Under the R1 retainer clip the cut also clears the clip's wire hole by min_wall + clr.
            c30 = next((c for c in PLAN7['cavities'] if c['box'] == 'POWER' and c['cav'] == 'R%d 87' % (a['i'] + 1)), None)   # the far blade (real 87) takes the AMI feed (spec.POWER_ROLE_POS) if PLAN7 else None
            if c30:
                mw = S.HOLE['min_wall']
                x_cut = c30['x'] + max(max(abs(z_[2]), abs(z_[3])) for z_ in c30['zones']) + mw
                if 'R%d' % (a['i'] + 1) in S.RETAIN.get('POWER', []):
                    x_cut = max(x_cut, c30['x'] + S.retainer_hole(c30['part'], c30['wire_od'])[0] / 2 + mw + S.RETAINER['clr'] + 0.05)
                z_cut = z_d - S.GUIDE['h'] - 1.0          # the cavity's lower end under the deck (crimp_holes z0)
                if c30['part'] in S.REAL:                  # R163: the real terminal hangs below the deck - the saddle stays clear of all of it
                    z_cut = min(z_cut, z_t - S.seat_gap(c30['part'], c30['kind']) - S.REAL[c30['part']]['L'] - 0.5)
                    report.setdefault('saddle_vs_terminal', []).append(dict(relay='R%d' % (a['i'] + 1), terminal_end_z=round(z_t - S.seat_gap(c30['part'], c30['kind']) - S.REAL[c30['part']]['L'], 2),
                                                                           bend_top_z=round(ccz, 2), straight_wire_mm=round(z_t - S.seat_gap(c30['part'], c30['kind']) - S.REAL[c30['part']]['L'] - ccz, 2)))
                x_cav = c30['x'] + max(max(abs(z_[2]), abs(z_[3])) for z_ in c30['zones'])
                if x_cut > ccx - rs - od:
                    # the cut's lower face is the radial plane through the saddle centre and the cavity's lower +x corner: it meets the
                    # curve square (no knife edge) and passes under the cavity's lower end across its width (no sliver under the cavity)
                    rm = box(ccx - rs - od - 5, a['y'] - 30, z_cut - 25, x_cut, a['y'] + 30, plate_b + 1)
                    dx_, dz_ = ccx - x_cav, ccz - z_cut
                    n_ = (dz_, 0.0, -dx_)
                    if (ccx - x_cav) * n_[0] + (ccz - rs - z_cut) * n_[2] < 0:
                        n_ = (-n_[0], 0.0, -n_[2])                # point at the lower (lug) end of the curve: that side stays
                    half_cut(rm, (x_cav, a['y'], z_cut), n_)
                    bo(core, rm, 's')
                    report.setdefault('saddle_top_cut', []).append(dict(relay='R%d' % (a['i'] + 1), x_cut=round(x_cut, 2), z_cut=round(z_cut, 2),
                                                                        through=[round(x_cav, 2), round(z_cut, 2)]))
            saddles.append(core)
        parts += saddles
        if R7:   # R127 (Dan 2026-10-15: "imagine you started with a solid block of material and machined away only the stuff necessary"):
            # under the deck plate the base is ONE solid block inside the skirt, from the deck underside up - the towers, collars, bosses
            # and ribs it replaces are inside it; only the needed cuts (cavities, hex pockets, clip-leg pockets, pan groove) come out of it
            parts.append(rrect(S.SKIRT - 0.01, S.SKIRT - 0.01, L - S.SKIRT + 0.01, D7 - S.SKIRT + 0.01, z_d, plate_b + 0.01, S.BASE_R - S.SKIRT + 0.01))
        z_leg = z_t - CV['over'] - 1.0
        # rev 7: no foot under the NEG cables - the rear inboard foot moves round to the inboard end, behind the harness exits
        leg_at = [('-y', 30.0), ('-y', L - 30.0), ('+y', L - 30.0), ('-x', D7 - 30.0)] if R7 else [(f, u) for f in ('-y', '+y') for u in (30.0, L - 30.0)]
        feet = [angular_leg(f, u, L, D7, z_leg, parts, lims) for (f, u) in leg_at]
        holes_p, fins_p = crimp_holes('POWER', z_d, z_t, parts, plate_b)
        deck = base_shell(L, z_d, z_t, parts + fins_p)
        cuts = base_snap_cuts(L, z_t, z_d, 'y', pre + 'Base_PA12_printed', sh) + holes_p
        B_ = dict(S.BAR, y1=R7['bar_y1']) if R7 else S.BAR       # rev 7: the POS bar runs on into the bus zone
        cuts.append(box(xb - B_['w'] / 2 - S.CLR, B_['y0'] - S.CLR, bz0, xb + B_['w'] / 2 + S.CLR, B_['y1'] + S.CLR, z_t + 1))
        if R7:
            cuts.append(box(NB['x0'] - S.CLR, NB['yc'] - B_['w'] / 2 - S.CLR, bz0, NB['x1'] + S.CLR, NB['yc'] + B_['w'] / 2 + S.CLR, z_t + 1))
        strap_arms = []
        for a in ami:
            if not R7:
                cuts.append(pad_box(a, pz0, z_t + 1, S.CLR))
            xc = (a['x_in'] + a['x_out']) / 2
            zb_ami = btop + S.AMI['ear_t'] / 2 - S.AMI['body_h'] / 2 - 0.6
            if R7:   # R127 sweep: the fuse-body recess floor level with the pad seat (0.4 under the body, was 0.6) - no 0.2 shelf between them
                zb_ami = max(zb_ami, pz0)
            cuts.append(cbox(xc, a['y'], zb_ami, z_t + 1, S.AMI['body_l'] + 1, S.AMI['body_w'] + 1))
            if not R7:                                           # rev 6: plain hex bore for the 40 mm standoff
                cuts.append(hexz(a['x_out'], a['y'], z_d - 1, pz0 + 0.01, SO['af'] + 2 * S.CLR, 90))
                continue
            # R155 (N14 = B): the strap drops in from above - bottom leg and web through the WELL, top leg and lips into the SEAT pocket.
            # The seat pocket floor (bar_top - t, the old pad seat) under the lips is the ledge = DOWN stop; it runs on 1.0 past the lip
            # ends to the hook slot (no sliver between them). The hook over the lip ends = UP stop.
            g, s_, y_ = a['g'], a['sgn'], a['y']
            c_, hw_ = ST['clr'], ST['w'] / 2
            T_ = S.STRAP_TAB[a['row']]
            x_slot = g['x_lip'] + s_ * ST['ledge']                # inner face of the hook slot (the ledge band ends here)
            # buildability review 2026-10-18 (R181): the bottom leg ends 0.1 past the top leg (PEM edge 7.1 vs top_in 6.5 + lug 0.5), and it
            # drops through this pocket on the way in - start the pocket at whichever leg end reaches further, so it passes with the full clr
            x_end_ = g['x_bl0'] if s_ * g['x_bl0'] < s_ * g['x_tl0'] else g['x_tl0']
            xs_ = sorted((x_end_ - s_ * c_, x_slot + s_ * 0.01))
            cuts.append(box(xs_[0], y_ - hw_ - c_, btop - ST['t'], xs_[1], y_ + hw_ + c_, z_t + 1))
            xw_ = sorted((g['x_bl0'] - s_ * c_, g['x_wo'] + s_ * c_))
            hl_ = ST['w_low'] / 2                                 # web + bottom leg are 14.2: the walls between wells are 3.2
            cuts.append(box(xw_[0], y_ - hl_ - c_, z_d - 1, xw_[1], y_ + hl_ + c_, btop - ST['t'] + 0.01))
            cuts += groove_join(L, z_d, [(z_d - 1, btop - ST['t'], xw_[0], xw_[1], y_ - hl_ - c_, y_ + hl_ + c_)], 0.01)
            th_, zh0_ = T_['w'] / 2, btop + S.HOOK_GAP          # markup 2026-10-17 (R157): the hook bears on the lips
            zh1_ = zh0_ + T_['hook_t']
            tip_ = g['x_lip'] - s_ * T_['over']
            if a['row'] == 'OUT':                                 # the skirt is the arm: two side slots + the inner slot, from the root up
                a0_, a1_ = L - S.SKIRT, L + S.SKIRT_OUT
                for sy_ in (1, -1):
                    ya_, yb_ = sorted((y_ + sy_ * th_, y_ + sy_ * (th_ + T_['slot'])))
                    cuts.append(box(a0_ - T_['slot'], ya_, T_['root'], a1_ + 1.0, yb_, z_t + 1))
                cuts.append(box(a0_ - T_['slot'], y_ - th_ - T_['slot'], T_['root'], a0_, y_ + th_ + T_['slot'], z_t + 1))
                arm_ = box(a0_, y_ - th_, z_t - 0.01, a1_, y_ + th_, zh1_)          # post on the freed skirt, up to the hook
                hook_ = box(tip_, y_ - th_, zh0_, a0_ + 0.01, y_ + th_, zh1_)
                ex_ = (tip_ - 0.3, a1_ + 1.3)
            else:                                                 # an arm cut free in the deck block by a slot ring
                a1_ = x_slot + s_ * T_['slot']
                a0_ = a1_ + s_ * T_['t']
                xr_ = sorted((a0_ + s_ * T_['slot'], x_slot))
                cuts.append(box(xr_[0], y_ - th_ - T_['slot'], T_['root'], xr_[1], y_ + th_ + T_['slot'], z_t + 1))
                xa_ = sorted((a0_, a1_))
                arm_ = box(xa_[0], y_ - th_, T_['root'] - 0.01, xa_[1], y_ + th_, zh1_)
                xh_ = sorted((a1_, tip_))
                hook_ = box(xh_[0] - 0.01, y_ - th_, zh0_, xh_[1], y_ + th_, zh1_)
                ex_ = (min(xr_[0], tip_) - 0.3, max(xr_[1], tip_) + 0.3)
            # R181 (buildability review 2026-10-18): lead-in T_['lead'] deg from the vertical from T_['lead_z'] above the underside (the R157
            # bar-tab rule), reaching past the lip end - the lips cam the hook out all the way (was 0.9 x 45 deg: the lip landed on a flat top)
            half_cut(hook_, (tip_, y_, zh0_ + T_['lead_z']), (-s_, 0.0, math.tan(math.radians(T_['lead']))))
            bo(arm_, hook_, 'u')
            strap_arms.append(arm_)
            exempt(pre + 'Base_PA12_printed', 'strap snap tab', min(ex_), max(ex_), y_ - th_ - T_['slot'] - 0.3, y_ + th_ + T_['slot'] + 0.3,
                   T_['root'] - 0.3, zh1_ + 0.3, sh)
            L_ = zh0_ - T_['root']
            t_ = abs(a1_ - a0_)
            report.setdefault('strap_tabs', []).append(dict(row=a['row'], name=a['name'], y=y_, arm=[round(min(a0_, a1_), 2), round(max(a0_, a1_), 2)],
                                                            arm_mm=round(L_, 1), t=round(t_, 2), strain_pct=round(150 * t_ * T_['over'] / L_ ** 2, 2),
                                                            push_N=round(3 * S.PA12['E'] * T_['w'] * t_ ** 3 / 12 * T_['over'] / L_ ** 3, 1)))
        for (bx_, by_, m) in bar_bolts:
            cuts.append(hexz(bx_, by_, z_d - 1, bz0 + 0.01, HD[m]['af'] + 2 * S.CLR))
            af_ = HD[m]['af'] + 2 * S.CLR    # R127 sweep: the head goes in from below; under the head a pocket near the groove runs into it
            cuts += groove_join(L, z_d, [(z_d - 1, bz0 - HD[m]['k'] - 1.0, bx_ - af_ / math.sqrt(3.0), bx_ + af_ / math.sqrt(3.0), by_ - af_ / 2, by_ + af_ / 2)],
                                af_ / math.sqrt(3.0))
            cuts.append(cylz(bx_, by_, z_d - 1, bz0 + 1, m + 0.5))
        # F05 (SteveCAD v3): two head pockets in one row closer than min_wall tip to tip (the moved NEG GND stud and the x 84 stud) are
        # joined by a relief across the tips, so no PA12 sliver is left between them (it would be 0.56); the bar seat floor is unchanged
        for i1, (x1_, y1_, m1) in enumerate(bar_bolts):
            for (x2_, y2_, m2) in bar_bolts[i1 + 1:]:
                if abs(y1_ - y2_) > 0.01 or m1 != m2:
                    continue
                tip = (HD[m1]['af'] + 2 * S.CLR) / math.sqrt(3.0)
                gap = abs(x2_ - x1_) - 2 * tip
                if 0 < gap < S.HOLE['min_wall']:
                    hw = 2.3
                    xa_, xb3 = sorted((x1_, x2_))
                    cuts.append(box(xa_ + tip - hw / math.sqrt(3.0) - 0.05, y1_ - hw, z_d - 1, xb3 - tip + hw / math.sqrt(3.0) + 0.05, y1_ + hw, bz0 + 0.01))
                    report.setdefault('pocket_reliefs', []).append(dict(x=[round(xa_, 2), round(xb3, 2)], y=round(y1_, 2), gap=round(gap, 2)))
        for r in relays:   # Mini ISO cavities, turned 90 deg: (u, v) of the F7 bottom view -> x = cx - v, y = cy + u
            P_ = S.RELAY_B_PINS if r['B'] else S.F7_PINS     # fit audit 2026-10-18 (TE V23134 rev 2607 p.3): 30 turned 90 deg to 87, coil line at the maker's offset
            pins = [P_['30'] + (3.2, 11.5), P_['87'] + (11.5, 3.2), P_['85'] + (2.8, 8.3), P_['86'] + (2.8, 8.3)]
            if r['B']:
                pins.append(P_['87a'] + (8.3, 2.8))
                x7_ = r['cx'] - S.RELAY_B['v87a']     # sweep 2026-10-17: the PA12 between the 87a cavity and the 85 / 86 cavities (pin spacing)
                # fit audit 2026-10-18: the web now runs from the turned 30 slot (v +7.65, 11.5 along x) to the 87 slot (v -10.25) - the box covers it
                exempt(pre + 'Base_PA12_printed', 'relay cavity web', r['cx'] - P_['30'][1] - 3.5, r['cx'] - P_['87'][1] - 1.5, r['cy'] - 8.0, r['cy'] + 8.0,
                       z_d - 0.5, z_t + 0.1, sh, only='A')
            for (u, v, lx, ly) in pins:
                zs0 = slot_z0('POWER', r['cx'] - v, r['cy'] + u, z_d, z_t, S.TERM['42281-1']['L'])
                cuts.append(cbox(r['cx'] - v, r['cy'] + u, zs0, z_t + 1, ly, lx))
                cuts += groove_join(L, z_d, [(zs0, z_t + 1, r['cx'] - v - ly / 2, r['cx'] - v + ly / 2, r['cy'] + u - lx / 2, r['cy'] + u + lx / 2)])
        for dx in (-S.MINI_BLADE_X, S.MINI_BLADE_X):
            cuts.append(cbox(acps[0] + dx, acps[1], slot_z0('POWER', acps[0] + dx, acps[1], z_d, z_t, S.TERM['1-968851-1']['L']), z_t + 1, *S.MINI_SLOT))
        # rev 6: the OUT-row lugs sit on 40 mm standoffs at the IN-row height, under the skirt: no skirt notches (belly pan exits below)
        tabs_add = []
        if R7:   # R146 (Dan N5): snap tabs that hold the POS and NEG bars down - the POS bar's front end and its -x edge before the barrier,
            # the NEG bar's front edge between the studs
            hb_ = B_['w'] / 2
            # markup 2026-10-17 (Dan 23-19 "NEED MORE HOLD DOWN TABS", one per arrow): POS bar both edges at the front end (y 22) and its +x edge
            # beside the BAT+ lug (y 164) and at the rear end (y 230); NEG bar front edge at its -x end (x 9) and by the GND stud (x 98). The
            # arrow on the NEG rear edge between RADLOK- and GND ID has no room: the lug tongues there are 3.0 apart (Dan's rule) - listed.
            for (xe_, ye_, n_) in [(xb, B_['y0'], (0, -1)), (xb - hb_, 163.8, (-1, 0)),
                                   (26.5, NB['yc'] - hb_, (0, -1)), (72.5, NB['yc'] - hb_, (0, -1)),
                                   (xb - hb_, 22.0, (-1, 0)), (xb + hb_, 22.0, (1, 0)), (xb + hb_, 164.0, (1, 0)), (xb + hb_, 230.0, (1, 0)),
                                   (9.0, NB['yc'] - hb_, (0, -1)), (98.0, NB['yc'] - hb_, (0, -1))]:
                c_, a_ = deck_tab(xe_, ye_, n_, z_t, btop, pre + 'Base_PA12_printed', sh)
                cuts += c_
                tabs_add += a_
            # card item 13 (Dan 22-59: "the other copper plates and bars ... will just fall out", R157): the NEG bar's rear edge - a snap arm
            # in every gap between two lug tongues that is >= POCKET wall_min (the arm stands in for the R160 pocket wall at the edge)
            neg_rings = []
            ng_ = [(x_, S.LUG_M8['b'] if g_ == '1/0' else R7['small_ring_b']) for (x_, nm, h_, g_) in R7['neg_studs']]
            for (xa_, ba_), (xc_, bc_) in zip(ng_, ng_[1:]):
                f0_, f1_ = xa_ + ba_ / 2 + S.POCKET['clr'], xc_ - bc_ / 2 - S.POCKET['clr']
                if f1_ - f0_ >= S.POCKET['wall_min']:
                    c_, a_ = deck_tab((f0_ + f1_) / 2, NB['yc'] + hb_, (0, 1), z_t, btop, pre + 'Base_PA12_printed', sh, w=f1_ - f0_)
                    cuts += c_
                    neg_rings += c_
                    tabs_add += a_
        sub_all(deck, cuts)
        if R7:
            for b_ in markup_1017_power(L, D7, z_d, z_t, btop, xb, B_, NB, ami, sh):
                for r_ in neg_rings:                     # the NEG rear arms' slot rings stay open through the pocket floor / walls
                    try:
                        bo(b_, tb.copy(r_), 's')
                    except RuntimeError:
                        pass
                bo(deck, b_, 'u')
        for b_ in strap_arms + tabs_add:
            bo(deck, b_, 'u')
        comp(pre + 'Base_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_steel_M6', lims, AP['al'], MAT['ss'], sh)

        # ---- copper, standoffs, bolts
        bar = box(xb - B_['w'] / 2, B_['y0'], bz0, xb + B_['w'] / 2, B_['y1'], btop)
        for (bx_, by_, m) in (m8_pos if R7 else [(xb, S.IN_STUD_Y, 8)]):
            bo(bar, cylz(bx_, by_, bz0 - 1, btop + 1, S.CLEAR[8]), 's')     # F19: ISO 273 medium (was 8.5)
        pads = []
        for a in ami:
            bo(bar, cylz(a['x_in'], a['y'], bz0 - 1, btop + 1, S.CLEAR[5]), 's')
            if R7:
                continue
            p = pad_box(a, pz0, btop)
            bo(p, cylz(a['x_out'], a['y'], pz0 - 1, btop + 1, S.CLEAR[5]), 's')
            pads.append(p)

        def strap_body(a):
            """R155 C-strap (spec.STRAP): top leg + two bends round ri + web + bottom leg, 3 x 15; the web is `neck` wide for `slit` under the
            top leg and the wings either side carry on flat past the web as the lips; PEM mounting holes at the ear stud and the lug bolt."""
            g, s_, y_ = a['g'], a['sgn'], a['y']
            t_, w_, ri_, ro_ = ST['t'], ST['w'], ST['ri'], g['ro']
            y0_, y1_ = y_ - w_ / 2, y_ + w_ / 2
            yl0_, yl1_ = y_ - ST['w_low'] / 2, y_ + ST['w_low'] / 2   # web + bottom leg, milled to 14.2
            zt_, zb_, zn_ = btop, ST['z_bl'], btop - ST['t']
            xc_ = g['x_wo'] - s_ * ro_                           # centre of both bends

            def xb(xa, xb2, za, zb2, ya=y0_, yb=y1_):
                return box(min(xa, xb2), ya, min(za, zb2), max(xa, xb2), yb, max(za, zb2))

            def bend(cz, sz):
                ring = cyl((xc_, y0_, cz), (xc_, y1_, cz), 2 * ro_)
                bo(ring, cyl((xc_, y0_ - 1, cz), (xc_, y1_ + 1, cz), 2 * ri_), 's')
                return bo(ring, xb(xc_, xc_ + s_ * (ro_ + 1), cz, cz + sz * (ro_ + 1), y0_ - 1, y1_ + 1), 'i')
            def bend_l(cz, sz):
                ring = cyl((xc_, yl0_, cz), (xc_, yl1_, cz), 2 * ro_)
                bo(ring, cyl((xc_, yl0_ - 1, cz), (xc_, yl1_ + 1, cz), 2 * ri_), 's')
                return bo(ring, xb(xc_, xc_ + s_ * (ro_ + 1), cz, cz + sz * (ro_ + 1), yl0_ - 1, yl1_ + 1), 'i')
            body = union_all([xb(g['x_tl0'], xc_, zn_, zt_), xb(g['x_wi'], g['x_wo'], zb_ + ro_, zt_ - ro_, yl0_, yl1_),
                              xb(g['x_bl0'], xc_, zb_, zb_ + t_, yl0_, yl1_), bend(zt_ - ro_, +1), bend_l(zb_ + ro_, -1)])
            for sy_ in (1, -1):                                  # neck + lips
                ya_, yb_ = sorted((y_ + sy_ * ST['neck'] / 2, y_ + sy_ * (w_ / 2 + 1)))
                bo(body, xb(xc_, g['x_wo'] + s_ * 1.0, zn_ - ST['slit'], zt_ + 1, ya_, yb_), 's')
                ya_, yb_ = sorted((y_ + sy_ * (ST['neck'] / 2 + ST['kerf']), y_ + sy_ * w_ / 2))     # the lip, a saw kerf off the tongue
                bo(body, xb(xc_, g['x_lip'], zn_, zt_, ya_, yb_), 'u')
            bo(body, cylz(a['x_out'], y_, zn_ - 1, zt_ + 1, S.STRAP_PEM['hole']), 's')
            bo(body, cylz(a['x_lug'], y_, zb_ - 1, zb_ + t_ + 1, S.STRAP_PEM['hole']), 's')
            return body

        def pem_nut(x, y, z_face, down):
            """PEM CLSS-M5-2: head E x T on the face away from the clamped part (shank flush in the copper, not drawn); M5 bore."""
            PM = S.STRAP_PEM
            z0, z1 = (z_face - PM['T'], z_face) if down else (z_face, z_face + PM['T'])
            return bo(cylz(x, y, z0, z1, PM['E']), cylz(x, y, z0 - 1, z1 + 1, 5.0), 's')
        if R7:
            comp(pre + 'Strap_Out_%s_15x3_C' % BM['name'], [strap_body(a) for a in ami], AP['tin'], MAT['cu'], sh)   # edge breaks: a drawing note (R138)
            comp(pre + 'Nut_PEM_%s' % S.STRAP_PEM['pn'], [pem_nut(a['x_out'], a['y'], btop - ST['t'], True) for a in ami]
                 + [pem_nut(a['x_lug'], a['y'], ST['z_bl'] + ST['t'], False) for a in ami], AP['al'], MAT['ss'], sh)
        edge_break(comp(pre + ('Bar_Power_%s_25x6p35%s' % (BM['name'], '_POS_bus_L226' if R7 else '')), bar, AP['tin'], MAT['cu'], sh))
        if R7:            # NEG bar: same 1" x 1/4" stock on flat, M8 holes
            nbar = box(NB['x0'], NB['yc'] - B_['w'] / 2, bz0, NB['x1'], NB['yc'] + B_['w'] / 2, btop)
            for (bx_, by_, m) in m8_neg:
                bo(nbar, cylz(bx_, by_, bz0 - 1, btop + 1, S.CLEAR[8]), 's')
            edge_break(comp(pre + 'BarNeg_%s_25x6p35_L105' % BM['name'], nbar, AP['tin'], MAT['cu'], sh))
        z_ear = btop + S.AMI['ear_t']
        if not R7:
            edge_break(comp(pre + 'Pad_Out_%s_15x3' % BM['name'], pads, AP['tin'], MAT['cu'], sh))
            comp(pre + 'Standoff_M5_FF_hex8_L%d_brass' % SO['long'], [bo(hexz(a['x_out'], a['y'], a['lz'] + 2.0, pz0, SO['af'], 90),
                                                                         cylz(a['x_out'], a['y'], a['lz'], pz0 + 1, 4.2), 's')
                                                                      for a in ami], AP['brass'], MAT['brass'], sh)       # rev 6 (B5): one 40 mm standoff, both rows
            comp(pre + 'SetScrew_ISO4026_A2', [cylz(a['x_out'], a['y'], pz0 - S.SETSCREW['in_so'], pz0 - S.SETSCREW['in_so'] + S.SETSCREW['l'], 5.0) for a in ami],
                 AP['al'], MAT['ss'], sh)
        else:             # R155: M5 x 10 down through the AMI ear into the top PEM nut (fused positions)
            comp(pre + 'EarBolt_ISO4017_A2', [union_all([hexz(a['x_out'], a['y'], z_ear, z_ear + HD[5]['k'], HD[5]['af']),
                                                         cylz(a['x_out'], a['y'], z_ear - 10.0, z_ear, 5.0)]) for a in ami if a['amps']], AP['al'], MAT['ss'], sh)
        comp(pre + 'BarBolt_ISO4017_A2', [union_all([hexz(bx_, by_, bz0 - HD[m]['k'], bz0, HD[m]['af']), cylz(bx_, by_, bz0, bz0 + S.BOLT_L[m], float(m))])
                                          for (bx_, by_, m) in bar_bolts], AP['al'], MAT['ss'], sh)
        comp(pre + 'LugBolt_ISO4017_A2', [union_all([hexz(a['x_lug'], a['y'], a['lz'] - HD[5]['k'], a['lz'], HD[5]['af']),
                                                     cylz(a['x_lug'], a['y'], a['lz'], a['lz'] + 10.0, 5.0)])
                                          for a in ami if a['amps']], AP['al'], MAT['ss'], sh)      # M5 x 10 both rows (R155: up into the bottom PEM nut)
        nuts = [hexz(a['x_in'], a['y'], z_ear, z_ear + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami]
        if not R7:
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
        if not R7:   # markup 2026-10-17 (Dan 23-29 "what is this?"): the grey 1 mm square was a CAD marker for the empty relay spot, not a part - gone
            comp(pre + 'SPARE_positions', [cbox(r['cx'], r['cy'], z_t, z_t + 1.0, S.F7['body'], S.F7['body']) for r in relays if not r['pn']], AP['spare'], None, sh)

        # ---- lugs + cables: OUT row straight out +x under the deck plate; IN row straight -x, one bend up round its saddle
        lugs, wires = [], []
        for a in ami:
            if a['amps'] is None:
                continue
            awg = S.AMI_AWG[a['name']]
            od = S.OD[awg]
            lg = S.LUG_6AWG if awg == 6 else LUG
            t, e = ring_lug(a['x_lug'], a['y'], a['lz'], lg['b'], 5.5, lg['t'], lg['d4'], (a['sgn'], 'x'), lg['l'] - lg['tip'], up=bool(R7))
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
        for dx in (-S.MINI_BLADE_X, S.MINI_BLADE_X):
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
                zc_ = (a['lz'] + lg['t'] - lg['d4'] / 2) if R7 else (a['lz'] + lg['d4'] / 2)     # barrel centre (R155: palm-up lug)
                if a['x_lug'] + (lg['l'] - lg['tip'] - 9.0) > wall_in:      # the flat tongue reaches the pan wall (JB1 3R5): notch round the tongue
                    wd = 2 * max(math.hypot(lg['b'] / 2 + 0.6, 1.0), lg['d4'] / 2 + 0.6, S.OD[awg] / 2 + 0.6)
                    zb_ = (min(a['lz'] + 1.0, zc_) if R7 else a['lz'] + 1.0) - wd / 2
                else:
                    wd = max(lg['d4'], S.OD[awg]) + 1.2
                    zb_ = zc_ - wd / 2
                pan_exits.append(('x', a['y'], zb_, wd, 1))
        belly_pan(L, z_d, 'y', pan_exits, pre, sh, box_name='POWER')
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
        DIM.pop('snaps_front', None)
        DIM.pop('xcatch', None)
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
        for (col, i, nm, amps, cx, y_) in S.mini_list():      # markup 2026-10-17: spares deleted, the rest on spec.MINI_GRID
            n += 1
            mini.append((col, nm, amps, cx, y_, n, i))
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
            xin = cx + sd * S.MINI_BLADE_X                      # input blade / jumper line
            xpm = xin + sd * JL['ax']                           # lug palm mid-plane
            face = xpm + sd * JL['t'] / 2                       # strip face the palms sit on
            x0, x1 = sorted((face, face + sd * ST['t']))
            strips[col] = dict(cx=cx, sd=sd, xin=xin, xpm=xpm, face=face, x0=x0, x1=x1, y0=S.STRIP_Y[col][0], y1=S.STRIP_Y[col][1])
        sx_lo = strips['BUS1']['x1']                            # gap between the strips
        sx_hi = strips['BUS2']['x0']
        spx = (sx_lo + sx_hi) / 2
        studs = []                                              # (col, i, y, z, fuse name or None)
        for (col, nm, amps, cx, y, n_, i) in mini:
            if not S.mini_stud(col, i):
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
            ys_ = [y_ for (c_, i_, n_, a_, x_, y_) in S.mini_list() if c_ == col]
            parts.append(box(cx - S.MINI['l'] / 2 - T, min(ys_) - 6.4 - T, z_d, cx + S.MINI['l'] / 2 + T, max(ys_) + 6.4 + T, plate_b + 0.01))
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
            exempt(pre + 'Base_PA12_printed', 'strip lip', min(xa, spx) - 0.1, max(xb_, spx) + 0.1, v['y0'] - 0.6, v['y1'] + 0.6, lip_z0 - 0.1, lip_z1 + 0.1, sh)
        if REV[0] == 7:   # card item 13 (Dan 22-59, R157): the strips rest on the lips (DOWN); a rail on the spine bears on their top edges (UP),
            # 0 gap; they still slide in along the lips. 0.3 off each strip's lug face (the jumper sleeves come up there).
            rail_t = 3.71    # fit audit 2026-10-18: 3.4 left a 0.3 powder gap (S6) under the block at z 35.0 - the rail now fuses into it
            for c_, v in strips.items():
                xa_, xb3 = (v['x0'] + 0.3, spx) if c_ == 'BUS1' else (spx, v['x1'] - 0.3)
                bo(spine, box(xa_, v['y0'] - 0.5, s_z1 + S.HOOK_GAP, xb3, v['y1'] + 0.5, s_z1 + S.HOOK_GAP + rail_t), 'u')
            report.setdefault('strip_rail', dict(z=[s_z1 + S.HOOK_GAP, s_z1 + S.HOOK_GAP + rail_t], gap=S.HOOK_GAP))
        parts.append(spine)
        if REV[0] == 7:   # J4 = B (R94): the printed channel floor across the front (over the Bus 1 feed lug), joined to the spine
            CH = S.CHANNEL
            parts.append(box(CH['floor_x'][0], CH['floor_y'][0], CH['floor'][0], spx + SP['t'] / 2 + 0.01, CH['floor_y'][1], CH['floor'][1]))
            parts.append(box(spx + SP['t'] / 2 - 0.01, CH['floor_y'][0], CH['floor'][0], CH['floor_x'][1], CH['wide_y'], CH['floor'][1]))
            # R127 sweep (Dan 2026-10-16: "fix the ones you found"): the POWER solid block, here too - under the deck plate the base is ONE
            # solid block inside the skirt from the deck underside up (towers, collars and the thin pieces between them are inside it);
            # nothing runs there (every wire leaves its cavity straight down below z_d), cavities and pin slots are the only cuts
            parts.append(rrect(S.SKIRT - 0.01, S.SKIRT - 0.01, L - S.SKIRT + 0.01, S.D - S.SKIRT + 0.01, z_d, plate_b + 0.01, S.BASE_R - S.SKIRT + 0.01))
        z_leg = z_t - CV['over'] - 1.0
        feet = [angular_leg(f, u, L, S.D, z_leg, parts, lims) for f in ('-x', '+x') for u in (30.0, S.D - 30.0)]
        holes_l, fins_l = crimp_holes('LOGIC', z_d, z_t, parts, plate_b)
        deck = base_shell(L, z_d, z_t, parts + fins_l)
        cuts = base_snap_cuts(L, z_t, z_d, 'x', pre + 'Base_PA12_printed', sh) + holes_l
        for (col, nm, amps, cx, y, n_, i) in mini:              # 2 x 2.8 mm receptacles per mini fuse (input + output)
            for dx in (-S.MINI_BLADE_X, S.MINI_BLADE_X):         # N21: 8.1 blade pitch, MCP 2.8 receptacles, slot = blade + 0.2 / 0.4 a side
                zs0 = slot_z0('LOGIC', cx + dx, y, z_d, z_t, S.TERM['1-968851-1']['L'])
                cuts.append(cbox(cx + dx, y, zs0, z_t + 1, *S.MINI_SLOT))
                cuts += groove_join(L, z_d, [(zs0, z_t + 1, cx + dx - S.MINI_SLOT[0] / 2, cx + dx + S.MINI_SLOT[0] / 2, y - S.MINI_SLOT[1] / 2, y + S.MINI_SLOT[1] / 2)])
        for (nm, pn, own, cx, cy, k_) in micro:                 # approximate pattern from TE 1308028; set exactly in detail work
            MP_ = S.MICRO_PINS             # fit audit 2026-10-18: TE V23074 rev 1119 p.3 pattern; 87a is a 4.8 blade like 85 / 86 (slot 6.8 long)
            bt_, c2_ = 0.8 + 2 * S.CLR, 2 * S.CLR    # fit audit 2026-10-18: blade slots = blade + R120 clr a side (0.8 x 6.3 / 4.8, TE V23074 p.3): with the
            # 280919-2 seated 3.2 down (spec.SEAT_GAP) the slots are 3.2 deep, and the old 2.6-wide slots left 1.9 webs between 85 / 87a / 86 (now 2.9)
            for (u, v, lx, ly) in (MP_['87'] + (6.3 + c2_, bt_), MP_['30'] + (6.3 + c2_, bt_), MP_['85'] + (bt_, 4.8 + c2_), MP_['86'] + (bt_, 4.8 + c2_), MP_['87a'] + (bt_, 4.8 + c2_)):
                if REV[0] == 7 and (u, v) == MP_['87a'] and pn in S.MICRO_NO:
                    continue            # R127 sweep: a normally-open micro relay has no 87a blade - no slot, solid there
                zs0 = slot_z0('LOGIC', cx + u, cy + v, z_d, z_t, S.TERM['280919-2']['L'])
                if (u, v) == MP_['87a']:
                    exempt(pre + 'Base_PA12_printed', '87a slot', cx - 4.5, cx + 4.5, cy + MP_['87'][1] + 1.9, cy + v + ly / 2 + 0.6, zs0 - 0.1, z_t + 0.1, sh)   # from the 87 cavity edge (joined)
                    # fit audit 2026-10-18: TE's pitch leaves 1.95 between the 87 receptacle and the 87a blade - the slot runs on into the 87
                    # cavity (its R121 box zone edge + 0.05) so no 0.56 PA12 sliver stands between them (R127 join; the 87a blade is bare)
                    c87_ = next((c for c in (PLAN7 or {}).get('cavities', []) if c['box'] == 'LOGIC' and abs(c['x'] - cx) < 0.01
                                 and abs(c['y'] - (cy + MP_['87'][1])) < 0.01 and c['kind'] == 'micro 87' and c.get('zones')), None)
                    if c87_:
                        y87_ = c87_['y'] + max(z_[5] for z_ in c87_['zones'][1:]) - 0.05
                        cuts.append(box(cx + u - lx / 2, y87_, zs0, cx + u + lx / 2, cy + v - ly / 2 + 0.01, z_t + 1))
                        report.setdefault('micro_87a_join', []).append([nm, round(cy + v - ly / 2 - y87_, 2)])
                cuts.append(cbox(cx + u, cy + v, zs0, z_t + 1, lx, ly))
                cuts += groove_join(L, z_d, [(zs0, z_t + 1, cx + u - lx / 2, cx + u + lx / 2, cy + v - ly / 2, cy + v + ly / 2)])
            exempt(pre + 'Base_PA12_printed', 'relay cavity web', cx - 6.0, cx + 6.0, cy - 6.0, cy + 6.0, z_d - 0.5, z_t + 0.1, sh, only='A')
            if REV[0] == 7:          # fit audit 2026-10-18 (R128): under the deck the web left between the 30 crimp hole and the 87 wire exit is 1.48
                # (30 and 87 now 8 apart, TE pitch) - a thin strip hanging below the deck plate: cut it (the 2.06 wall in the deck stays)
                c30_ = next((c for c in (PLAN7 or {}).get('cavities', []) if c['box'] == 'LOGIC' and abs(c['x'] - cx) < 0.01
                             and abs(c['y'] - (cy + MP_['30'][1])) < 0.01 and c.get('zones')), None)
                if c30_:
                    y30_ = c30_['y'] + c30_['zones'][0][5]
                    cuts.append(box(cx - 5.2, cy + MP_['30'][1] + 2.95, z_d - 4.5, cx + 5.2, cy + MP_['87'][1] - 2.9, z_d - 0.01))   # to the 30 exit edge (y - 5.05)
                    report.setdefault('micro_underdeck_strip_cut', []).append([nm, round(y30_, 2), round(cy - 2.9, 2)])
        for s_ in studs:                                        # bolt tips pass the spine
            cuts.append(cyl((sx_lo - 1.0, s_['y'], s_['z']), (sx_hi + 1.0, s_['y'], s_['z']), JB['m'] + 1.6))
        if REV[0] == 7:   # R127 sweep: two bolt-tip passes at one y closer than min_wall (Bus 1 low row / Bus 2 high row) become one slot
            for s1 in studs:
                for s2 in studs:
                    d_ = JB['m'] + 1.6
                    if s1 is not s2 and abs(s1['y'] - s2['y']) < 0.01 and s1['z'] < s2['z'] and 0 < (s2['z'] - s1['z']) - d_ < S.HOLE['min_wall']:
                        cuts.append(box(sx_lo - 1.0, s1['y'] - d_ / 2, s1['z'], sx_hi + 1.0, s1['y'] + d_ / 2, s2['z']))
                        report.setdefault('spine_pass_joins', []).append(round(s1['y'], 1))
        for col, f in S.FEED.items():
            cuts.append(cyl((sx_lo - 1.0, f['y'], f['z']), (sx_hi + 1.0, f['y'], f['z']), 5.0 + 1.6))
        sub_all(deck, cuts)
        comp(pre + 'Base_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_steel_M6', lims, AP['al'], MAT['ss'], sh)

        # ---- copper strips: N2 (Dan 2026-10-16, OPEN-3 = A) a PEM self-clinching nut at every stud (M4) and feed (M5), pressed into its
        # mounting hole from the lug face so the head stands on the far face, in the gap between the strips (spec.PEM)
        sbodies, pem = [], {4: [], 5: []}
        for col, v in strips.items():
            st = box(v['x0'], v['y0'], s_z0, v['x1'], v['y1'], s_z1)
            far = v['face'] + v['sd'] * ST['t']
            holes_ = [(s_['y'], s_['z'], JB['m']) for s_ in studs if s_['col'] == col] + [(S.FEED[col]['y'], S.FEED[col]['z'], 5)]
            for (y_, z_, m_) in holes_:
                N_ = S.PEM[m_]
                bo(st, cyl((v['x0'] - 1, y_, z_), (v['x1'] + 1, y_, z_), N_['hole']), 's')
                assert min(z_ - s_z0, s_z1 - z_, y_ - v['y0'], v['y1'] - y_) >= N_['edge'] - 1e-6, 'PEM edge distance %s %.1f %.1f' % (col, y_, z_)
                nut = union_all([cyl((far, y_, z_), (far + v['sd'] * N_['T'], y_, z_), N_['E']),
                                 cyl((far - v['sd'] * N_['A'], y_, z_), (far, y_, z_), N_['hole'] - 0.03)])
                bo(nut, cyl((far - v['sd'] * (N_['A'] + 1), y_, z_), (far + v['sd'] * (N_['T'] + 1), y_, z_), float(m_)), 's')
                pem[m_].append(nut)
            sbodies.append(st)
        edge_break(comp(pre + 'Strip_Logic_%s_25p4x3p2_on_edge' % BM['name'], sbodies, AP['tin'], MAT['cu'], sh))
        for m_, nl in pem.items():
            comp(pre + 'Nut_PEM_%s' % S.PEM[m_]['pn'], nl, AP['al'], MAT['ss'], sh)
        report['pem_nuts'] = {S.PEM[m_]['pn']: len(nl) for m_, nl in pem.items()}

        # ---- jumper lugs, bolts, washers, jumpers (straight down from the input cavity into the lug barrel)
        jl, jb, jw, jwire = [], [], [], []
        jl_pn = {}
        for s_ in studs:
            v = strips[s_['col']]
            sd, y, z = v['sd'], s_['y'], s_['z']
            if s_['fuse']:      # markup 2026-10-17: the jumper is sized by its own fuse (spec.jumper); the strip stays where JLUG puts it
                awg_j, rcp_j, pn_j, JL = S.jumper(s_['amps'])
                od_j = S.OD[awg_j]
                jl_pn.setdefault(pn_j, []).append(s_['fuse'])
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
                bend_row('LOGIC %s %s input jumper (%d AWG)' % (s_['col'], s_['fuse'], awg_j), awg_j,
                         'straight down from the input receptacle into its PIDG lug barrel (%.1f mm of wire between them)' % (z_d - zb1),
                         None, True, 'no bend: the lug barrel is right under the input blade')
        comp(pre + 'Lug_TE_PIDG_53941-1_320554', jl, AP['cu'], None, sh)
        report['logic_jumpers']['ring_lugs'] = jl_pn
        report['logic_jumpers']['gauges'] = {s_['fuse']: S.jumper(s_['amps'])[0] for s_ in studs if s_['fuse']}
        comp(pre + 'LugBolt_M4x8_A2', jb, AP['al'], MAT['ss'], sh)
        comp(pre + 'Washer_DIN127B_M4', jw, AP['al'], MAT['ss'], sh)
        comp(pre + 'Wire_jumper_14AWG', jwire, AP['wire'], None, sh)

        # ---- feeds: Klauke 2R5 on the strip's lug face, M5 x 10 into the PEM nut in the strip (R129); wire straight out (BUS1 front, BUS2 rear)
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
        if REV[0] != 7:   # markup 2026-10-17 (23-29): the same CAD-only spare markers (not parts) are gone here too
            comp(pre + 'SPARE_positions', [cbox(cx, cy, z_t, z_t + 1.0, S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy, k_) in micro if not pn], AP['spare'], None, sh)

        # ---- harness: one load wire per fuse (output blade), MRS / B30 inputs, 5 per micro relay; bundles to the front edge
        tails = []
        skip = S.CHANNEL_CAD_SKIP if REV[0] == 7 else ()     # J4 = B: these run in the front channel (the wired views draw them)
        for (col, nm, amps, cx, y, n_, i) in mini:
            if not amps or nm in skip:
                continue
            sd = S.MINI_IN[col]
            lane = cx - sd * S.MINI_BLADE_X
            tails.append(dict(x=lane, y=y, awg=S.MINI_AWG[amps], what=nm, lane=lane))
            if i in S.MINI_OWN_IN.get(col, ()):                          # own input (MRS, B30): a harness wire, not a jumper
                tails.append(dict(x=cx + sd * S.MINI_BLADE_X, y=y, awg=S.MINI_AWG[amps], what=nm + ' in', lane=lane))
        for (nm, pn, own, cx, cy, k_) in micro:
            if not pn:
                continue
            for (u, v, awg, tn) in [S.MICRO_PINS[t_] + (S.COIL_AWG if t_ in ('85', '86') else S.MICRO_LOAD_AWG, t_) for t_ in ('30', '87', '87a', '85', '86')]:
                if tn == '87a' and pn in S.MICRO_NO:
                    continue                                     # NO relays: no 87a contact
                if '%s %s' % (nm, tn) in skip or (tn == '87a' and REV[0] == 7):
                    continue                                     # rev 7: no harness wire on any 87a (wiring_plan.json)
                tails.append(dict(x=cx + u, y=cy + v, awg=awg, what='%s %s' % (nm, tn), lane=cx))
        exits = harness_tails(tails, lambda t_: t_['lane'], z_d, 'y', 0.0, pre, sh, 'LOGIC')
        pan_exits = [('y', u, zb_, wd, -1) for (u, zb_, wd) in exits] + pan_feed
        if REV[0] == 7:   # J2 = B (R94): rib between the Bus 1 output wires and the Bus 1 strip bolt heads; reliefs at the outboard relay column
            # markup 2026-10-17 (23-12 / 23-33): a wire-group wall half way between the bundle edges of two neighbouring lanes - the two micro
            # relay columns, and micro column 1 / the Bus 2 outputs - from the pan's front wall back past the last relay
            ln_ = {round(e[0], 2): e[2] - 1.6 for e in exits}
            GW = S.LOGIC_GROUP_WALLS
            y_front = S.SKIRT + W_CL + PN['t'] - 0.01
            gw = []
            for (la, lb) in ((S.MINI_COLS['BUS2'][0] + S.MINI_BLADE_X, S.MICRO_COLS[0]), (S.MICRO_COLS[0], S.MICRO_COLS[1])):
                xm_ = ((la + ln_[round(la, 2)] / 2) + (lb - ln_[round(lb, 2)] / 2)) / 2
                gw.append((xm_ - GW['t'] / 2, xm_ + GW['t'] / 2, y_front, GW['y1'], GW['z_top']))
            belly_pan(L, z_d, 'x', pan_exits, pre, sh, rib=(S.PAN_RIB['x'][0], S.PAN_RIB['x'][1], S.PAN_RIB['y'][0], S.PAN_RIB['y'][1], S.PAN_RIB['z_top']),
                      reliefs=[(cy + S.MICRO_PINS['86'][1] - S.PAN_RELIEF['fwd'], cy + S.MICRO_PINS['86'][1] + S.PAN_RELIEF['back'], S.PAN_RELIEF['depth']) for cy in S.MICRO_Y], walls=gw, box_name='LOGIC')   # fit audit: at the real 86 pin (coil row +6)
        else:
            belly_pan(L, z_d, 'x', pan_exits, pre, sh)
        bend_row('LOGIC fuse / micro relay receptacles, largest %d AWG' % S.LOGIC_MAX_AWG, S.LOGIC_MAX_AWG, 'straight down out of the cavity, one bend into its bundle (rows above)',
                 3.0 * S.OD[S.LOGIC_MAX_AWG], True, 'one bundle per fuse column / relay column, straight to the front edge')

        z_top = z_t + 25.4 + CV['clear'] + CV['t']          # micro relay 25.4 max (TE 1308028)
        short = {'HEAD LH': 'HEAD L', 'HEAD RH': 'HEAD R', 'horn': 'HORN', 'k_etb': 'ETB', 'k_acc': 'A/C', 'k_eps_en': 'EPS EN', 'k_rev': 'REV', 'SPARE': 'SPARE'}
        labels = [(short[nm], cx, cy, S.LABEL['h_micro']) for (nm, pn, own, cx, cy, k_) in micro]           # rev 4 etched names, unchanged
        labels += [(('%s %s' % (nm, ('%g' % amps))) if amps else 'SP', cx, y, S.LABEL['h_mini']) for (col, nm, amps, cx, y, n_, i) in mini]
        labels += [(col, cx, S.MINI_GRID['y0'] - 11.0, S.LABEL['h_mini']) for col, (cx, fuses) in S.MINI_COLS.items()]
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
        DIM['D'], DIM['snaps_rear'] = Dr, None             # built after POWER: do not inherit its rear catch positions (cover_catches)
        DIM['so'] = S.RIM_OUT if REV[0] == 7 else 0.0     # R127 amendment: the rim grows outward (3.0 left behind the cover catch pocket)
        so_ = DIM['so']
        zf = 10.0                                          # relay flange face (raised 6 on bosses: captured nut + limiter under it)
        tz0, tz1 = zf + 10.0, zf + 30.0                    # terminal blocks (TE side view: 10 back from the flange face, 20 tall)
        x3 = R['x_t3']
        rx = x3 - H_['term_x0']                           # fit audit 2026-10-18: relay centre = flange-hole midpoint, terminal 3 1.95 to its +x (TE STEP)
        xs = (x3, x3 + H_['term_pitch'])                   # terminal 3 (fused feed), terminal 5 (pump)
        yb = R['y_b']
        tsy = yb - H_['term_y']                            # fit audit 2026-10-18: the real stud axis (TE STEP), was term_to / 2                        # the power line
        hxs = (rx - H_['holes'] / 2, rx + H_['holes'] / 2)
        fy = yb + H_['hole_z']
        Bb = R['bar']
        btop = tz1 - S.AMI['ear_t']                         # AMI ear top = terminal top: the jumper lug lies at the terminal height
        bz0 = btop - Bb['t']
        RP = S.RB_PAD
        R7b = REV[0] == 7                                   # markup 2026-10-17 (Dan 23-06): the out pad grows to the bar width, 3.2 stock
        pad_t = RP['t'] if R7b else S.PAD['t']
        pz0 = btop - pad_t
        a_in, a_out = R['x_ami_in'], R['x_ami_in'] + S.AMI['c']
        pad_x = (a_out + RP['x0'], a_out + RP['x1']) if R7b else (a_out - S.PAD['inner'], a_out + S.PAD['outer'])
        pad_w = RP['w'] if R7b else S.PAD['w']
        xst = R['x_stud']
        LM = R['lim_m6']
        parts, lims = [], []
        # ---- base: rounded floor plate, low rim on the long sides only (ends open), relay platform, ONE fuse pedestal, 2 END tabs
        base = rrect(-so_, -so_, Lr + so_, Dr + so_, 0, fl, 10.0 + so_)
        rim = rrect(-so_, -so_, Lr + so_, Dr + so_, fl - 0.01, R['rim'], 10.0 + so_)
        rw_ = 4.0 if REV[0] == 7 else 3.0     # R127 sweep: rim 4.0 (inward) - a 3.0 wall round the R10 corners was not >= 3 everywhere
        bo(rim, rrect(rw_, rw_, Lr - rw_, Dr - rw_, 0, R['rim'] + 1, 10.0 - rw_), 's')
        rb_faces = [(x, y) for y in (0.0, Dr) for x in snap_xs(Lr) if (x, y) not in S.SCREW_SKIP_RB(Lr, Dr)]
        rb_zs = (fl + R['rim']) / 2                         # R122: insert bosses standing on the floor against the rim, beside each catch
        parts += screw_bosses(Lr, Dr, R['rim'], 3.0, fl - 0.01, R['rim'], rb_faces, outward=True)
        bo(rim, box(-1, 16.0, 0, 22.0, Dr - 16.0, R['rim'] + 1), 's')            # open -x end
        bo(rim, box(Lr - 22.0, 16.0, 0, Lr + 1, Dr - 16.0, R['rim'] + 1), 's')   # open +x end
        parts += [rim]
        px0, px1 = rx - H_['body_x'] / 2, rx + H_['body_x'] / 2
        plat = box(hxs[0] - 8.0, yb, fl - 0.01, hxs[1] + 8.0, yb + H_['body_y'], zf)          # relay platform: perimeter + ribs
        solid_rb = REV[0] == 7     # R127 sweep: platform and fuse pedestal are solid blocks (their 2.5 ribs were attached by < 3 mm)
        if not solid_rb:
            bo(plat, box(hxs[0] - 8.0 + 2.5, yb + 2.5, fl, hxs[1] + 8.0 - 2.5, yb + H_['body_y'] - 2.5, zf + 1), 's')
        parts.append(plat)
        for x in ((px0 + 15.0, rx, px1 - 15.0) if not solid_rb else ()):
            parts.append(box(x - S.RIB / 2, yb, fl - 0.01, x + S.RIB / 2, yb + H_['body_y'], zf))
        for x in hxs:
            parts.append(cylz(x, fy, fl - 0.01, zf, 18.0))
        # fuse pedestal (rev 5: the bar's and the pad's risers joined into one ribbed block - point 8 asked what they were)
        pw = Bb['w'] / 2 + 1.0
        ped = box(Bb['x0'] - 1.0, tsy - pw, fl - 0.01, pad_x[1] + 1.0, tsy + pw, bz0)
        if not solid_rb:
            bo(ped, box(Bb['x0'] + 1.5, tsy - pw + 2.5, fl, a_out + S.PAD['outer'] - 1.5, tsy + pw - 2.5, bz0 + 1), 's')
        else:   # solid: the same outline up to under the bar, and a riser under the pad up to the pad (pad top = bar top, the pad is thinner)
            bo(ped, box(pad_x[0] - 1.0, tsy - pw, fl, pad_x[1] + 1.0, tsy + pw, pz0), 'u')
        parts.append(ped)
        for y in ((tsy - Bb['w'] / 2 + 1.25, tsy, tsy + Bb['w'] / 2 - 1.25) if not solid_rb else ()):    # ribs under bar + pad
            parts.append(box(Bb['x0'], y - S.RIB / 2, fl - 0.01, Bb['x1'], y + S.RIB / 2, bz0))
            parts.append(box(a_out - S.PAD['inner'], y - S.RIB / 2, fl - 0.01, a_out + S.PAD['outer'], y + S.RIB / 2, pz0))
        for x in ((a_out - S.PAD['inner'], a_out + S.PAD['outer'] - S.RIB) if not solid_rb else ()):
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
                yo_ = y - so_ if y == 0.0 else y + so_
                cuts.append(cyl((x - S.SNAP['w'] / 2 - 0.5, yo_, R['rim'] - 3.0), (x + S.SNAP['w'] / 2 + 0.5, yo_, R['rim'] - 3.0), S.SNAP['bump'] + 0.2))
                exempt(pre + 'Base_PA12_printed', 'cover catch pocket', x - S.SNAP['w'] / 2 - 2.5, x + S.SNAP['w'] / 2 + 2.5, (-so_ - 0.1 if y == 0.0 else Dr - 4.6),
                       (4.6 if y == 0.0 else Dr + so_ + 0.1), R['rim'] - 3.0 - S.SNAP['bump'] / 2 - 2.2, R['rim'] + 0.1, sh)
        for (xs_, yf_, sg_) in screw_points(Lr, rb_faces, True):
            ya_ = -so_ if sg_ > 0 else Dr + so_                 # the outer face
            exempt(pre + 'Base_PA12_printed', 'cover screw insert', xs_ - S.SCREW['d_ins'] / 2 - 2.2, xs_ + S.SCREW['d_ins'] / 2 + 2.2,
                   min(ya_ - 0.1, ya_ + sg_ * (S.SCREW['ins_depth'] + 2.6)), max(ya_ + 0.1, ya_ + sg_ * (S.SCREW['ins_depth'] + 2.6)),
                   rb_zs - S.SCREW['d_ins'] / 2 - 2.2, R['rim'] + 0.1, sh)
        cuts += screw_inserts(Lr, Dr, rb_zs, rb_faces, outward=True)
        rb_cradle_rep = []

        def rb_cradles():
            """Markup 2026-10-17 (23-18 / 23-31, R160): a printed cradle under the barrel of every battery block ring lug where it leaves its
            copper / terminal - a floor block from the base floor to under the barrel and two walls d4 + 2 x trough apart - so the lug cannot
            turn when its nut is torqued: the battery feed lug off the bar's -x end, the AMI out lug past the pad, the pump lug off terminal 5.
            (Terminal 3's lug barrel sits over the HCR150 coil plug, so it gets none - listed.) Root fillets on the walls' outer faces."""
            PK, d4, wt = S.POCKET, 7.0, 3.0
            hw = d4 / 2 + PK['trough']
            out = []
            for (nm, xa, xb2, z_palm) in (('feed', -DIM['so'] + 0.5, Bb['x0'] - S.CLR, btop), ('ami_out', pad_x[1] + S.CLR, a_out + 20.0, btop + S.AMI['ear_t']),
                                          ('pump', xs[1] + H_['term_w'] / 2 + S.CLR, xs[1] + 17.0, tz1)):
                z_fl = z_palm - PK['under']
                zw = z_palm + d4 / 2 + 1.0
                out.append(box(xa, tsy - hw - wt, fl - 0.01, xb2, tsy + hw + wt, z_fl))
                for sg in (-1, 1):
                    ya, yb2 = sorted((tsy + sg * hw, tsy + sg * (hw + wt)))
                    out.append(box(xa, ya, z_fl - 0.01, xb2, yb2, zw))
                    out += root_fillets(xa, ya, xb2, yb2, z_fl, 1.5, 'y')[(1 if sg > 0 else 0):(2 if sg > 0 else 1)]
                rb_cradle_rep.append(dict(lug=nm, x=[round(xa, 2), round(xb2, 2)], trough=round(2 * hw, 2), floor=round(z_fl, 2), wall_top=round(zw, 2)))
            rw2 = 4.0                                         # the long-side rim (R128: 4.0): root fillets on its inner bottom edge (23-31)
            out += root_fillets(22.0, -DIM['so'], Lr - 22.0, rw2, fl, S.FILLET_R, 'y')[1:]
            out += root_fillets(22.0, Dr - rw2, Lr - 22.0, Dr + DIM['so'], fl, S.FILLET_R, 'y')[:1]
            return out

        rb_tabs = []
        if REV[0] == 7:   # R146 (Dan N5): snap tabs on both long edges of the bar, between the M6 stud lug and the AMI ear; the bar sits on its
            # pedestal (1.0 wider each side), so each arm stands free on the floor, BAR_TAB gap off the pedestal
            for sy_ in (-1, 1):
                c_, a_ = deck_tab(29.0, tsy + sy_ * Bb['w'] / 2, (0, sy_), fl, btop, pre + 'Base_PA12_printed', sh, standing=(fl, 1.0 + S.BAR_TAB['gap']))
                rb_tabs += a_
                # markup 2026-10-17 (Dan 23-06: "make pad larger and add hold down tabs"): the same standing tab on each long edge of the pad
                c_, a_ = deck_tab(a_out + RP['tab_x'], tsy + sy_ * pad_w / 2, (0, sy_), fl, btop, pre + 'Base_PA12_printed', sh,
                                  standing=(fl, (pw - pad_w / 2) + S.BAR_TAB['gap']))
                rb_tabs += a_
            rb_tabs += rb_cradles()
        sub_all(base, cuts)
        for b_ in rb_tabs:
            bo(base, b_, 'u')
        comp(pre + 'Base_PA12_printed', base, AP['pa12_lt'], MAT['pa'], sh)
        report.setdefault('markup_1017', {})['battrelay'] = dict(pad=dict(x=[round(v, 2) for v in pad_x], w=pad_w, t=pad_t, stock=RP['stock']),
                                                                out_bolt=RP['bolt_out'], cradles=rb_cradle_rep)
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
        # fit audit 2026-10-18 (R163): the relay in the assembly is TE's own STEP (cad/vendor/te/1416010-1), seated on its flange face at zf with its
        # flange holes on the bosses; the box envelope above stays only as the fallback when the vendor file is missing
        real_hcr = None
        hdir = next((os.path.join(d_, 'te', '1416010-1') for d_ in (os.path.join(os.path.dirname(os.path.dirname(SRC)), 'vendor'), S.VENDOR_DIR_MAIN)
                     if os.path.isdir(os.path.join(d_, 'te', '1416010-1'))), None)
        if hdir:
            stp = [f_ for f_ in os.listdir(hdir) if f_.lower().endswith('.stp')]
            if stp:
                tocc = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                app.importManager.importToTarget(app.importManager.createSTEPImportOptions(os.path.join(hdir, stp[0])), tocc.component)
                hb_ = [tb.copy(b_) for b_ in tocc.component.bRepBodies] + [tb.copy(b_) for o_ in tocc.component.allOccurrences for b_ in o_.component.bRepBodies]
                tocc.deleteMe()
                m_ = adsk.core.Matrix3D.create()     # model: flange face -Y at y -5.98, holes x +-42 / z -39.5, studs x 1.95 / 18.95 (spec.HCR term_x0)
                m_.setWithCoordinateSystem(P(rx, yb - 26.0, zf + 5.98), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 0, 1),
                                           adsk.core.Vector3D.create(0, -1, 0))
                for b_ in hb_:
                    tb.transform(b_, m_)
                real_hcr = hb_
                report.setdefault('battrelay', {})['hcr150_model'] = 'cad/vendor/te/1416010-1/' + stp[0]
        comp(pre + 'Relay_TE_HCR150_1416010-1', real_hcr if real_hcr else rel, AP['black'], MAT['abs'], sh)
        if real_hcr:   # fit audit 2026-10-18: TE's STEP has the coil connector at x -30.5 .. -11.3 / z 20.1 .. 40.1 (box frame), its tip 20.2 out of the
            # body face; the mated plug (TE 282080-1, its housing drawing not on disk) runs from that tip to y_b - plug_to as before (5.8 long, UNVERIFIED)
            gcx, gcz = rx - 20.9, zf + 5.98 + 14.1
            plug_y0, plug_y1 = yb - H_['plug_to'], yb - H_['term_to'] - 0.05
        else:
            gcz, plug_y0, plug_y1 = tz0 + 4.5, yb - H_['plug_to'], yb - 0.05
        comp(pre + 'CoilPlug_TE_Superseal_282080-1', box(gcx - 5.0, plug_y0, gcz - 4.5, gcx + 5.0, plug_y1, gcz + 4.5), AP['black'], MAT['abs'], sh)
        # ---- copper + fuse + hardware
        bar = box(Bb['x0'], tsy - Bb['w'] / 2, bz0, Bb['x1'], tsy + Bb['w'] / 2, btop)
        bo(bar, cylz(xst, tsy, bz0 - 1, btop + 1, S.CLEAR[6]), 's')     # F19: ISO 273 medium (was 6.5)
        bo(bar, cylz(a_in, tsy, bz0 - 1, btop + 1, S.CLEAR[5]), 's')
        pad = box(pad_x[0], tsy - pad_w / 2, pz0, pad_x[1], tsy + pad_w / 2, btop)
        bo(pad, cylz(a_out, tsy, pz0 - 1, btop + 1, S.CLEAR[5]), 's')
        edge_break(comp(pre + 'Bar_Power_%s_25x6p35' % BM['name'], bar, AP['tin'], MAT['cu'], sh))
        edge_break(comp(pre + ('Pad_Out_%s_25p4x3p2' if R7b else 'Pad_Out_%s_15x3') % BM['name'], pad, AP['tin'], MAT['cu'], sh))
        fe = slot_x(a_in, a_out, tsy, btop, btop + S.AMI['ear_t'], S.AMI['ear_w'])
        for x in (a_in, a_out):
            bo(fe, cylz(x, tsy, btop - 1, btop + 2, S.AMI['hole']), 's')
        ze = btop + S.AMI['ear_t'] / 2
        fb = cbox((a_in + a_out) / 2, tsy, ze - S.AMI['body_h'] / 2, ze + S.AMI['body_h'] / 2, S.AMI['body_l'], S.AMI['body_w'])
        bo(fb, fe, 'u')
        comp(pre + 'Fuse_AMI_ltgreen', fb, AP['ltgreen'], MAT['abs'], sh)
        lug_z = btop + S.AMI['ear_t']                    # = tz1
        bl_ = lambda px, m: 16.0 if m == 6 else (RP['bolt_out'] if (R7b and abs(px - a_out) < 0.01) else S.BOLT_L[5])   # 22-59: FP 40A out M5 x 12
        comp(pre + 'BarBolt_M5_M6_ISO4017_A2', [union_all([hexz(px, tsy, zu - HD[m]['k'], zu, HD[m]['af']), cylz(px, tsy, zu, zu + bl_(px, m), float(m))]) for (px, m, zu) in rb_bolts],
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
        yl, zl = cy_ - rcl - 1.0, gcz                    # fit audit 2026-10-18: at the real connector's height
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
                   zc=R['rim'] - 3.0, inner_R=10.45, inner_r=3.5, ribs={'y': [22.0, Lr - 22.0], 'x': [50.0, 80.0]}, screw_z=rb_zs, screw_out=True, screw_faces=rb_faces)
        return dict(L=Lr, D=Dr, H=z_top, L_with_tabs=Lr + 2 * (LG['ear_len'] + 6.0), D_with_tabs=Dr, tabs=tabs,
                    parts=dict(bar=((Bb['x0'] + Bb['x1']) / 2, tsy, btop), pad=(a_out + 2.0, tsy, btop), fuse=((a_in + a_out) / 2, tsy, btop + 4),
                               ped=(30.0, tsy - pw, bz0 - 8.0), relay=(rx, yb + 22.0, zf + 40.0), plug=(gcx, yb - H_['plug_to'] + 2, tz0 + 9.0)))

    sizes = {'LOGIC': build_logic(), 'POWER': build_power(), 'BATTRELAY': build_relay_block()}

    def place_terminals():
        """R163 (Dan 2026-10-18, card item 13: "why are there no terminals in the assembly models?" - they were never built; only
        render_closeups.py drew stand-ins in a scratch design): the maker's own STEP (spec.VENDOR_TERM) of the terminal the wiring plan puts
        in every cavity, seated: contact end on the seat (deck top - HOLE top_gap, R121), blade width along the cavity's blade axis, the
        locking lance toward the side its R121 window opens (W lances: both sides, either way round). One component per box and part."""
        if not PLAN7:
            return
        cands = [os.path.join(os.path.dirname(os.path.dirname(SRC)), 'vendor'), S.VENDOR_DIR_MAIN]
        vdir = next((d for d in cands if os.path.isdir(os.path.join(d, 'te'))), None)    # a worktree's cad/vendor holds only INDEX.md
        rep_ = report.setdefault('terminals', {'placed': {}, 'missing': []})
        if vdir is None:
            rep_['missing'].append('no cad/vendor folder')
            return
        src = {}
        tmp_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        im = app.importManager
        for pn, (mk, fn, yb, dn) in S.VENDOR_TERM.items():
            f = os.path.join(vdir, mk, pn, fn)
            if not os.path.exists(f):
                rep_['missing'].append(pn)
                continue
            n0 = tmp_occ.component.bRepBodies.count + sum(o.component.bRepBodies.count for o in tmp_occ.component.allOccurrences)
            im.importToTarget(im.createSTEPImportOptions(f), tmp_occ.component)
            bl = [b_ for b_ in tmp_occ.component.bRepBodies] + [b_ for o in tmp_occ.component.allOccurrences for b_ in o.component.bRepBodies]
            src[pn] = [tb.copy(b_) for b_ in bl[n0:]]
            zmx = max(b_.boundingBox.maxPoint.z for b_ in src[pn]) * 10    # the contact end = the model's top (MCP models stand 0.55 proud of Z 0)
            mz = adsk.core.Matrix3D.create()
            mz.translation = V(0, 0, -zmx / 10.0)
            for b_ in src[pn]:
                tb.transform(b_, mz)
            if pn in S.REAL:      # R163: TE's model shows the barrels OPEN - trim them to the crimped envelope the cavity is sized for
                E_, R_ = S.real_env(pn), S.REAL[pn]
                bw_, wz_, iz_ = E_['box'][0], R_['wz'][0], R_['iz'][0]
                env = union_all([box(-20, -20, -wz_, 20, 20, 5), box(-E_['wire'][0], -5, -iz_, E_['wire'][0], E_['wire'][2], -wz_ + 0.01),
                                 box(-E_['ins'][0], E_['ins'][1] - 0.5, -R_['L'] - 2, E_['ins'][0], E_['ins'][2], -iz_ + 0.01)])
                keep = []
                for b_ in src[pn]:
                    try:
                        bo(b_, tb.copy(env), 'i')
                        keep.append(b_)
                    except RuntimeError:
                        pass
                src[pn] = keep
        tmp_occ.deleteMe()
        zt = {'LOGIC': S.LOGIC['z_t'], 'POWER': S.POWER['z_t']}
        by = {}
        for c in PLAN7['cavities']:
            if c['box'] not in zt or not c.get('zones') or (c['kind'].endswith('87a') and c['source'] != 'harness'):
                continue
            pn = c['part']
            if pn in S.PLACE_HOLD:
                rep_.setdefault('held', {})[c['box'] + ' ' + c['cav']] = S.PLACE_HOLD[pn]
                continue
            if pn not in src:
                rep_['missing'].append('%s %s %s' % (c['box'], c['cav'], pn))
                continue
            wax = S.BLADE_AXIS[c['kind']]
            zs, (zb, zl) = c['zones'], (c['zones'][-2], c['zones'][-1])
            if wax == 'x':      # H axis = y: the window side is where the last zone reaches further out
                side = 1 if zl[5] > zb[5] + 1e-6 else (-1 if zl[4] < zb[4] - 1e-6 else 1)
                eW, eH = (1.0, 0.0, 0.0), (0.0, -side, 0.0)      # model +Y (away from the lance) -> -side
            else:
                side = 1 if zl[3] > zb[3] + 1e-6 else (-1 if zl[2] < zb[2] - 1e-6 else 1)
                eW, eH = (0.0, 1.0, 0.0), (-side, 0.0, 0.0)
            eZ = (0.0, 0.0, 1.0)
            det = eW[0] * (eH[1] * eZ[2] - eH[2] * eZ[1]) - eW[1] * (eH[0] * eZ[2] - eH[2] * eZ[0]) + eW[2] * (eH[0] * eZ[1] - eH[1] * eZ[0])
            if det < 0:
                eW = tuple(-v for v in eW)                       # keep it a rotation (the terminal is symmetric across its blade width)
            yb = S.REAL[pn]['box'][1] / 2 if pn in S.REAL else S.VENDOR_TERM[pn][2]     # the blade line = the box's Y centre (real_zones uses it)
            sx_, sy_ = S.PLACE[c['box']]
            org = (c['x'] + sx_ - eH[0] * yb, c['y'] + sy_ - eH[1] * yb, zt[c['box']] - S.seat_gap(pn, c['kind']))
            m = adsk.core.Matrix3D.create()
            m.setWithCoordinateSystem(P(*org), V(*eW), V(*eH), V(*eZ))
            for b_ in src[pn]:
                t_ = tb.copy(b_)
                tb.transform(t_, m)
                by.setdefault((c['box'], pn), []).append(t_)
            rep_['placed'][c['box'] + ' ' + c['cav']] = pn
        for (bx_, pn), bl in by.items():
            comp(('Power_' if bx_ == 'POWER' else 'Logic_') + 'Terminal_TE_%s' % pn, bl, AP['brass'], MAT['brass'])
        rep_['count'] = len(rep_['placed'])
        rep_['source'] = {pn: dict(file='cad/vendor/%s/%s/%s' % (v[0], pn, v[1]), url=S.TE_DOC % (v[3], pn)) for pn, v in S.VENDOR_TERM.items()}
    place_terminals()

    # ------------------------------------------------------------------ checks
    mm = app.measureManager

    def dist(b1, b2):
        return round(mm.measureMinimumDistance(b1, b2).value * 10, 2)

    def bodies(name):
        return [b for o in root.occurrences if o.component.name.startswith(name) for b in o.bRepBodies]

    pad_bs = bodies('Power_Pad_') or bodies('Power_Strap_')      # R155 (rev 7): the copper strap is the output conductor
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
    sk = 'strap' if bodies('Power_Strap_') else 'pad'
    report['live_clearance'] = {
        '%s_to_%s_min_mm' % (sk, sk): min(neigh),
        'bar_to_%s_min_mm' % sk: min(dist(bodies('Power_Bar_')[0], pb) for pb in pad_bs),
        'input_lug_to_%s_min_mm' % sk: min(dist(il, pb) for il in in_lugs for pb in pad_bs),
        'under_deck_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(out_lugs) for l2 in out_lugs[i_ + 1:]),
        'logic_strip_to_strip_mm': dist(*bodies('Logic_Strip_')[:2]),
        'logic_feed_lug_to_lug_mm': dist(*bodies('Logic_Lug_Klauke')[:2]),
        'battrelay_bar_to_pad_mm': dist(bodies('BattRelay_Bar_')[0], bodies('BattRelay_Pad_')[0]),
        'battrelay_relay_lug_to_lug_mm': dist(rb_lugs[2], rb_lugs[3]),
        'pan_to_nearest_live_power_mm': min(dist(bodies('Power_Pan_')[0], b) for b in bodies('Power_LugBolt_') + bodies('Power_Lug_') + so
                                            + bodies('Power_Strap_') + bodies('Power_Nut_PEM_')),
    }
    if so:
        report['live_clearance']['standoff_to_standoff_min_mm'] = min(dist(s1, s2) for i_, s1 in enumerate(so) for s2 in so[i_ + 1:])
    else:   # R155: every live part of one strap station (strap, PEM nuts, ear / lug bolts, lug) against the next station's (Dan's 3 mm)
        st_live = bodies('Power_Strap_') + bodies('Power_Nut_PEM_') + bodies('Power_EarBolt_') + bodies('Power_LugBolt_') + lug_bs
        yc_ = lambda b_: (b_.boundingBox.minPoint.y + b_.boundingBox.maxPoint.y) * 5
        xs_ = lambda b_: (b_.boundingBox.minPoint.x + b_.boundingBox.maxPoint.x) * 5 > (S.PLACE['POWER'][0] + S.POWER['x_bar'])
        stn = lambda b_: (xs_(b_), int(round((yc_(b_) - S.PLACE['POWER'][1] - S.AMI_Y0) / S.AMI_PITCH)))
        report['live_clearance']['strap_station_to_station_min_mm'] = min(
            dist(b1, b2) for i_, b1 in enumerate(st_live) for b2 in st_live[i_ + 1:] if stn(b1)[0] == stn(b2)[0] and abs(stn(b1)[1] - stn(b2)[1]) == 1)
    if bus_lugs:          # rev 7 bus zone: lug to lug on each bar (Dan's 3 mm), NEG parts to POS parts, to the barrier
        pos_live = bodies('Power_Lug_BusPos') + bodies('Power_Bar_Power')
        neg_live = bodies('Power_Lug_BusNeg') + bodies('Power_BarNeg_')
        bp_, bn_ = bodies('Power_Lug_BusPos'), bodies('Power_Lug_BusNeg')
        yc_neg = (S.REV7['neg_bar']['yc'] + S.PLACE['POWER'][1]) / 10.0
        neg_nuts_ = [b_ for b_ in bodies('Power_Nut_') if abs((b_.boundingBox.minPoint.y + b_.boundingBox.maxPoint.y) / 2 - yc_neg) < 0.05
                     and (b_.boundingBox.maxPoint.y - b_.boundingBox.minPoint.y) > 1.2]
        report['live_clearance'].update({
            'bus_pos_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(bp_) for l2 in bp_[i_ + 1:]),
            'bus_neg_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(bn_) for l2 in bn_[i_ + 1:]),
            # N3 (Dan 2026-10-16): the NEG M8 nuts too - nut to nut on the NEG bar, and the end nut to the printed barrier wall
            'bus_neg_nut_to_nut_min_mm': min(dist(n1, n2) for i_, n1 in enumerate(neg_nuts_) for n2 in neg_nuts_[i_ + 1:]),
            'bus_neg_nut_to_barrier_mm': min(dist(n_, bodies('Power_Base_')[0]) for n_ in neg_nuts_),
            'bus_neg_to_pos_min_mm': min(dist(a_, b_) for a_ in neg_live for b_ in pos_live),
            'bus_pos_lug_to_out_%s_min_mm' % sk: min(dist(l1, pb) for l1 in bp_ for pb in pad_bs),
        })
    # rev 6 (C4): the jumper lugs - lug to lug on each strip (Dan's 3 mm), every jumper part to plastic and to the harness wires
    jl_bs = bodies('Logic_Lug_TE_PIDG')
    jpart = jl_bs + bodies('Logic_LugBolt_') + bodies('Logic_Washer_') + bodies('Logic_Lug_Klauke') + bodies('Logic_Nut_PEM_')
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
        'logic_pem_nut_to_other_strip_min_mm': min(sorted(dist(nb, sb) for sb in strip_bs)[1] for nb in bodies('Logic_Nut_PEM_')),
    })
    # rev 7 (3 mm gate): every Bus 1 live part against every Bus 2 live part (sides of the spine)
    spx_ = sizes['LOGIC']['spine_x'] + S.PLACE['LOGIC'][0]
    lg_live = strip_bs + bodies('Logic_LugBolt_') + bodies('Logic_Washer_') + bodies('Logic_Lug_TE') + bodies('Logic_Lug_Klauke') + bodies('Logic_Nut_PEM_')   # N2: + the PEM nuts
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
        if not nm.startswith(('Wire_', 'Harness_', 'BarBolt_', 'SetScrew_', 'LugBolt_', 'EarBolt_', 'StripBolt_', 'FlangeBolt_', 'Nut_', 'Lug_', 'Standoff_', 'Limiter_')):
            coll.add(o)
    try:
        ir = design.analyzeInterference(design.createInterferenceInput(coll))
        report['interference'] = [(r.entityOne.parentComponent.name if hasattr(r.entityOne, 'parentComponent') else str(r.entityOne),
                                   r.entityTwo.parentComponent.name if hasattr(r.entityTwo, 'parentComponent') else str(r.entityTwo),
                                   round(r.interferenceBody.volume * 1000, 3)) for r in ir]
    except Exception as ex:   # report, do not hide
        report['interference_error'] = str(ex)
    report['mass_g'] = {o.component.name: round(o.component.physicalProperties.mass * 1000, 1) for o in root.occurrences
                        if o.component.name.split('_', 1)[1].startswith(('Bar_', 'BarNeg_', 'Pad_', 'Strip_', 'Strap_'))}

    # ------------------------------------------------------------------ exports
    em = design.exportManager
    exported = []
    for o in root.occurrences:
        n = o.component.name
        if n.endswith('_printed') or n.split('_', 1)[1].startswith(('Bar_', 'BarNeg_', 'Pad_', 'Strip_', 'Strap_')):
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
            doc.save(msg or 'rev 7 rebuild (Claude Code)')
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
    EMPTY = lambda n: kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'Strip', 'Standoff', 'Strap', 'Nut_PEM'))
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
    WIRING = lambda n: kind(n).startswith(('Wire', 'Harness', 'Lug', 'Bar', 'Pad', 'Strip', 'Standoff', 'Strap', 'Nut_PEM', 'Relay', 'Fuse', 'SPARE', 'LugBolt', 'EarBolt', 'Washer'))
    ST7 = REV[0] == 7     # R155: copper straps instead of pads + standoffs
    PX = S.PLACE['POWER'][0]
    show(lambda n: n.startswith('Power_') and WIRING(n))
    shot('fusebox_render_routing_power.png', eye=(-200, -330, -200), target=(PX + 90.0, 90.0, 25.0), callouts=[
        (1, (PX + 10.0, 52.0, 8.0), 'harness bundles to the inboard edge'), (2, (PX + 92.25, 61.0, 10.0), 'relay feed: lug under its copper strap' if ST7 else 'relay feed: lug on the 40 mm standoff'),
        (3, (PX + 62.0, 61.0, 20.0), 'feed bends up R16 into terminal 30'), (4, (PX + 164.75, 97.0, 11.0), 'OUT lug under its copper strap' if ST7 else 'OUT lug on the 40 mm standoff'),
        (5, (PX + S.POWER['L'] + 20.0, 97.0, 13.0), 'OUT cables straight out the end'), (6, (PX + S.POWER['L'] + 20.0, sizes['POWER']['in_y'], S.POWER['bar_top'] + 8.0), '1/0 battery feed in')]
        + ([(7, (PX + 50.0, S.REV7['neg_bar']['yc'] + 40.0, S.POWER['bar_top'] + 8.0), 'NEG bus: grounds straight out the rear')] if REV[0] == 7 else []))
    show(lambda n: n.startswith('Logic_') and WIRING(n))
    c1, c2 = S.MINI_COLS['BUS1'][0], S.MINI_COLS['BUS2'][0]
    shot('fusebox_render_routing_logic.png', eye=(-230, -330, -200), target=(40.0, 90.0, 20.0), callouts=[
        (1, (c1 - 3.0, 60.0, 8.0), 'Bus 1 fuse wires'), (2, (c2 + 3.0, 60.0, 8.0), 'Bus 2 fuse wires'), (3, (S.MICRO_COLS[0], 40.0, 10.0), 'micro relay wires, inboard column'),
        (4, (S.MICRO_COLS[1], 40.0, 10.0), 'micro relay wires, outboard column'), (5, (40.0, -20.0, 8.0), 'all leave the front edge'),
        (6, (c1 + 3.0, 52.1, 28.0), 'fuse input jumpers drop straight into their lugs'), (7, ((c1 + c2) / 2, 70.0, 30.0), 'bus strips on edge, printed spine between'),
        (8, (c1 + 2.15, -15.0, 22.0), 'Bus 1 feed in at the front'), (9, (c2 - 2.15, S.D + 15.0, 13.0), 'Bus 2 feed in at the rear')])
    show(lambda n: n.startswith('Power_') and kind(n).startswith(('Base', 'Wire', 'Lug', 'Standoff', 'Strap', 'Nut_PEM', 'LugBolt', 'Limiter', 'Harness')))
    shot('fusebox_render_power_bends.png', eye=(-120, -330, -150), target=(PX + 70.0, 80.0, 15.0))

    # ---- exploded / install steps, POWER (point 4)
    pw = 'Power_'
    ex_p = {}
    for n in names(pw):
        kd = kind(n)
        dz = {'Cover': 270, 'Relay': 185, 'SPARE': 185, 'Fuse_ATM': 185, 'Fuse_AMI': 125, 'Nut_PEM': 55, 'Nut': 150, 'SetScrew': 95, 'EarBolt': 175,
              'BarBolt': -40, 'Bar': 55, 'Pad': 55, 'Strap': 55, 'Standoff': -85, 'LugBolt': -150, 'Lug_Bus': 100, 'Lug': -120, 'Pan': -200}
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
        (3, c_of('Fuse_AMI_ltgreen'), 'AMI fuses on the studs'), (4, c_of('Nut_Keps'), 'Keps nuts, 4 Nm max'),
        (5, c_of('EarBolt') if ST7 else c_of('SetScrew'), 'M5 x 10 ear bolts into the strap PEM nuts' if ST7 else 'M5 set screws (studs)'),
        (6, c_of('Bar'), 'copper bar 25 x 6.35'),
        (7, c_of('Strap') if ST7 else c_of('Pad'), 'copper C-straps 15 x 3 (14), PEM nuts pressed in' if ST7 else 'output pads 15 x 3'),
        (8, c_of('Base'), 'base (deck on 4 angular legs)'), (9, c_of('BarBolt'), 'bar bolts up from below')]
        + ([] if ST7 else [(10, c_of('Standoff_M5_FF_hex8_L40'), 'standoffs 40 mm (both rows, one part)')]) + [
        (11, c_of('Lug'), 'cable lugs'), (12, c_of('LugBolt'), 'M5 x 10 lug bolts'), (13, c_of('Pan'), 'belly pan (snaps on)')], **eye_ex)
    # steps 1-3
    place({})
    show(lambda n: n.startswith(pw) and kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'BarBolt', 'Standoff', 'SetScrew', 'Strap', 'Nut_PEM')))
    place({n: (0, 0, 35) for n in names(pw, 'Bar', 'Pad', 'SetScrew', 'Strap', 'Nut_PEM')} | {n: (0, 0, -30) for n in names(pw, 'BarBolt')}
          | {n: (0, 0, -45) for n in names(pw, 'Standoff')})
    shot('fusebox_power_step1.png', callouts=[
        (1, c_of('Bar'), 'lay the bar in its pocket'),
        (2, c_of('Strap') if ST7 else c_of('Pad'), 'drop the 14 copper straps into their wells (PEM nuts already pressed in): the lips '
                                                  'rest on the ledge, the hook snaps over them' if ST7 else 'lay the 14 pads in theirs'),
        (3, c_of('BarBolt'), 'bar bolts up through the hex head pockets')]
        + ([] if ST7 else [(4, c_of('Standoff_M5_FF_hex8_L40'), '40 mm standoffs up into the hex holes, both rows'),
                           (5, c_of('SetScrew'), 'set screw down through each pad into its standoff')]) + [
        (6, c_of('Base'), 'base, right way up')], eye=(-360, -560, 90), target=(pxp + 90.0, 90.0, 25.0))
    place({n: (0, 0, -40) for n in names(pw, 'Lug', 'LugBolt', 'Wire', 'Harness')})
    show(lambda n: n.startswith(pw) and kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'BarBolt', 'Standoff', 'SetScrew', 'Strap', 'Nut_PEM', 'Lug', 'LugBolt', 'Wire', 'Harness')))
    shot('fusebox_power_step2.png', callouts=[
        (1, c_of('Harness', dz=0), 'crimp, push each terminal up into its cavity (wire side)'),
        (2, (pxp + 92.25, 79.0, 8.0 - 40.0), 'relay feed lug palm-up under its strap (M5 x 10 into the PEM nut)' if ST7 else 'relay feed lug on its long standoff (M5 x 10)'),
        (3, (pxp + 62.0, 79.0, 30.0 - 40.0), 'feed round its saddle into terminal 30'),
        (4, (pxp + 164.75, 115.0, 11.0 - 40.0), 'OUT lug palm-up under its strap (M5 x 10)' if ST7 else 'OUT lug on its standoff (M5 x 10)'),
        (5, (pxp - 20.0, 88.0, 8.0 - 40.0), 'tie the bundles; they leave the inboard end')],
        eye=(-260, -420, -300), target=(pxp + 90.0, 90.0, 10.0))
    place({n: (0, 0, 45) for n in names(pw, 'Relay', 'SPARE', 'Fuse', 'Nut_Keps', 'EarBolt')})
    show(lambda n: n.startswith(pw) and not kind(n).startswith(('Cover', 'Pan')))
    shot('fusebox_power_step3.png', callouts=[
        (1, c_of('Fuse_AMI_ltgreen'), 'AMI fuses on the studs'),
        (2, c_of('Nut_Keps'), 'Keps nuts on the bar studs, M5 x 10 ear bolts into the straps: 4 Nm max' if ST7 else 'Keps nuts, 4 Nm max'),
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
        (6, l_of('Lug_TE'), 'input jumper lugs, TE PIDG 53941-1'), (7, l_of('LugBolt_M4'), 'M4 x 8 + spring washer into the PEM nut in the strip'),
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
