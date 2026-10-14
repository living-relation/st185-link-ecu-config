"""Build the ST185 fuse + relay boxes (rev 4: base + snap-on cover, open underneath; LOGIC box, POWER box, battery
relay block) in the existing Fusion fusebox document, export every part, render, check clearance, interference and
every cable bend.
Run inside Fusion (Fusion MCP script runner):  build(out_dir)
Same toolkit as rev 3 (TemporaryBRepManager bodies, one component per part, every occurrence placed in the root with an
identity transform; bodies are moved with tb.transform before they are added). Rounded shells are built from boxes,
cylinders and tori (no fillet features). Labels are sketch text cut into the cover top (the only features used).
R74: never makes a new document - it opens the existing fusebox document (rev 3, renamed rev 4) and saves a new version.
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
DOC = 'ST185_fusebox_rev4'                                 # rev 4: base + snap cover, open bottom
DOC_OLD = ('ST185_fusebox_rev3', 'ST185_fusebox_rev2')     # the same Fusion document before the renames (R74)


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


def slot_x(x0, x1, cy, z0, z1, w):
    s = box(x0, cy - w / 2, z0, x1, cy + w / 2, z1)
    bo(s, cylz(x0, cy, z0, z1, w), 'u')
    bo(s, cylz(x1, cy, z0, z1, w), 'u')
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
    """Quarter of a torus about the y axis (centre cx, cy, cz; centre-line radius Rc; tube dia d).
    quad = (sx, sz): which quadrant of the x-z plane, e.g. (-1, -1) = toward -x and -z from the centre."""
    t = torus(cx, cy, cz, V(0, 1, 0), Rc, d / 2)
    sx, sz = quad
    q = box(cx, cy - d, cz, cx + sx * (Rc + d), cy + d, cz + sz * (Rc + d))
    return bo(t, q, 'i')


def open_doc():
    names = (DOC,) + DOC_OLD
    for i in range(app.documents.count):
        dd = app.documents.item(i)
        if dd.isSaved and dd.name.split(' v')[0] in names:
            return dd
    proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
    for f in proj.rootFolder.dataFiles:
        if f.name in names:
            return app.documents.open(f, True)
    raise RuntimeError('fusebox document not found - R74: do not create a new one')


def build(out_dir, save=True):
    os.makedirs(out_dir, exist_ok=True)
    doc = open_doc()
    doc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    for i in range(root.occurrences.count - 1, -1, -1):
        root.occurrences.item(i).deleteMe()
    report = {'bends': [], 'labels': {}}

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
        'tin': tint('Aluminum - Satin', 'Tinned copper', (200, 200, 190)),
        'wire_bk': tint('Plastic - Glossy (Red)', 'Wire black', (40, 40, 40)),
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
    l5 = S.LIMITER_M5
    LG = S.LEG
    SO = S.STANDOFF

    def bend_row(where, awg, path, r_inside, supported, note):
        od = S.OD[awg]
        need = (3.0 if supported else 10.0) * od
        report['bends'].append(dict(where=where, awg=str(awg), od=od, path=path, r_inside=r_inside, need=round(need, 1),
                                    rule='3 x OD, supported' if supported else '10 x OD', ok=(r_inside is None) or r_inside >= need - 1e-6, note=note))

    # ------------------------------------------------------------------ shared pieces of a glove-box base / cover
    def legs_and_ears(L, z_d, tray_parts, lims, rear_x=None):
        """Four legs (z 0 -> z_d) at the corners (rear pair at rear_x if given, clear of cables leaving the rear) with ears
        pointing -y (front) / +y (rear), each ear an M5 hole + brass limiter."""
        r = LG['d'] / 2
        rx_ = rear_x or (r, L - r)
        for (cx, cy, sy) in ((r, r, -1), (L - r, r, -1), (rx_[0], S.D - r, 1), (rx_[1], S.D - r, 1)):
            tray_parts.append(cylz(cx, cy, 0, z_d + 0.01, LG['d']))
            ey0 = cy if sy > 0 else cy - LG['ear_len'] - r
            ey1 = cy + LG['ear_len'] + r if sy > 0 else cy
            ear = box(cx - LG['ear_w'] / 2, ey0, 0, cx + LG['ear_w'] / 2, ey1, LG['ear_t'])
            bo(ear, cylz(cx, cy + sy * (r + LG['ear_len'] / 2), 0, LG['ear_t'], LG['ear_w']), 'u')
            for gx in (cx - LG['ear_w'] / 2, cx + LG['ear_w'] / 2 - S.RIB):                      # gussets up the leg
                bo(ear, box(gx, ey0, 0, gx + S.RIB, ey1, LG['gusset_h']), 'u')
            hx, hy = cx, cy + sy * (r + LG['ear_len'] / 2)
            bo(ear, cylz(hx, hy, -1, LG['gusset_h'] + 1, LG['hole']), 's')
            bo(ear, cylz(hx, hy, LG['ear_t'], LG['gusset_h'] + 1, 13.0), 's')                    # socket clearance above the ear
            tray_parts.append(ear)
            lims.append(bo(cylz(hx, hy, 0, l5['l'], l5['od']), cylz(hx, hy, -1, l5['l'] + 1, l5['id']), 's'))

    def snap_xs(L):
        return (L * 0.25, L * 0.75)

    def base_shell(L, z_d, z_t, extra_parts):
        """Deck: top plate + perimeter skirt (rounded plan), open underneath; the skirt carries the snap pockets."""
        R = S.BASE_R
        plate = rrect(0, 0, L, S.D, z_t - S.PLATE, z_t, R)
        skirt = rrect(0, 0, L, S.D, z_d, z_t - S.PLATE + 0.01, R)
        bo(skirt, rrect(S.SKIRT, S.SKIRT, L - S.SKIRT, S.D - S.SKIRT, z_d - 1, z_t, R - S.SKIRT), 's')
        return union_all([plate, skirt] + extra_parts)

    def base_snap_cuts(L, z_t):
        zc = z_t - S.SNAP['z_from_top']
        cuts = []
        for x in snap_xs(L):
            for y in (0.0, S.D):
                cuts.append(cyl((x - S.SNAP['w'] / 2 - 0.5, y, zc), (x + S.SNAP['w'] / 2 + 0.5, y, zc), S.SNAP['bump'] + 0.2))
        return cuts

    def cover(L, D, z_t, z_top, notches, label_list, pre, sh, x0=0.0, y0=0.0, R=None, over=None):
        """Rounded snap-on cover over a base L x D (base outline from (x0, y0)). notches = [(axis, pos, centre_u, z_top_of_notch, width)]:
        a U-notch open at the bottom edge in the end (axis 'x') or side (axis 'y') wall. Returns the occurrence."""
        g, t = W_CL, CV['t']
        R = CV['R'] if R is None else R
        zb = z_t - (CV['over'] if over is None else over)
        out = rtop(x0 - g - t, y0 - g - t, x0 + L + g + t, y0 + D + g + t, zb, z_top, R, CV['r'])
        inn = rtop(x0 - g, y0 - g, x0 + L + g, y0 + D + g, zb - 1, z_top - t, R - t, CV['r'] - t)
        bo(out, inn, 's')
        sw = S.SNAP
        zc = z_t - sw['z_from_top']
        for x in snap_xs(L):
            for (yf, sy) in ((y0 - g, -1), (y0 + D + g, 1)):                    # inner face of the front / rear wall
                for dx in (-1, 1):                                              # two slots free the tongue
                    xs = x0 + x + dx * (sw['w'] / 2 + sw['slot'] / 2)
                    ya, yb_ = (yf - t - 1, yf + 1) if sy < 0 else (yf - 1, yf + t + 1)
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
        oc = comp(pre + 'Cover_PA12_printed', out, AP['pa12'], MAT['pa'], sh)
        etch(oc, label_list, z_top, sh)
        return oc

    # ================================================================== POWER box
    def build_power():
        PW = S.POWER
        L, xb, z_d, z_t, btop = PW['L'], PW['x_bar'], PW['z_d'], PW['z_t'], PW['bar_top']
        sh = S.PLACE['POWER']
        pre = 'Power_'
        bz0 = btop - S.BAR_T
        pz0 = btop - S.PAD['t']                                  # = LUG top + standoff
        lz = S.LUG_Z
        ami = []
        for row, sgn in (('IN', -1), ('OUT', +1)):
            for i in range(S.AMI_SLOTS[row]):
                name, amps = S.AMI_ROWS[row][i]
                y = S.AMI_Y0 + i * S.AMI_PITCH
                x_in = xb + sgn * S.AMI_IN_OFF
                ami.append(dict(row=row, i=i, name=name, amps=amps, y=y, x_in=x_in, x_out=x_in + sgn * S.AMI['c'], sgn=sgn))
        PD = S.PAD

        def pad_box(a, z0, z1, grow=0.0):
            xa = a['x_out'] - a['sgn'] * PD['inner']
            xb_ = a['x_out'] + a['sgn'] * PD['outer']
            return box(min(xa, xb_) - grow, a['y'] - PD['w'] / 2 - grow, z0, max(xa, xb_) + grow, a['y'] + PD['w'] / 2 + grow, z1)

        # relays: IN-row fuse i -> relay i, its terminal 30 on the fuse line
        relays = []
        for i, nm in enumerate(S.IN_RELAY):
            cx = S.F7_X[1] if i % 2 == 0 else S.F7_X[0]
            cy = S.AMI_Y0 + i * S.AMI_PITCH + 10.25
            pn, own = S.RELAY_PN[nm]
            relays.append(dict(i=i, name=nm, pn=pn, own=own, cx=cx, cy=cy, B=(nm == S.RELAY_B['pos'])))
        acps = (S.F7_X[0], S.ACPS_Y)
        Rc = S.R_SADDLE + S.OD[8] / 2            # wire centre-line radius of the relay feeds (largest wire, 8 AWG)

        # ---- base (deck) parts under the plate
        parts, lims = [], []
        T = S.TOWER
        for r in relays:
            parts.append(cbox(r['cx'], r['cy'], z_d, z_t - S.PLATE + 0.01, 17.0 + 2.8 + 2 * T, 17.9 + 3.2 + 2 * T + (2.0 if r['B'] else 0)))
        parts.append(cbox(acps[0], acps[1], z_d, z_t - S.PLATE + 0.01, 6.0 + 3.0 + 2 * T, 4.6 + 2 * T))
        for a in ami:                                            # standoff bosses (hex hole = anti-rotation)
            parts.append(cylz(a['x_out'], a['y'], z_d, z_t - S.PLATE + 0.01, SO['af'] / math.cos(math.radians(30)) + 2 * S.CLR + 5.0))
        bar_bolts = [(a['x_in'], a['y'], 5) for a in ami] + [(xb, S.IN_STUD_Y, 8)]
        for (bx_, by_, m) in bar_bolts:                          # head bosses under the bar
            parts.append(cylz(bx_, by_, z_d, z_t - S.PLATE + 0.01, HD[m]['af'] / math.cos(math.radians(30)) + 2 * S.CLR + 5.0))
        for x in (S.F7_X[0] + 15.0, xb - 20.0, xb + 20.0):      # ribs along y under the plate
            parts.append(box(x - S.RIB / 2, S.SKIRT, z_d, x + S.RIB / 2, S.D - S.SKIRT, z_t - S.PLATE + 0.01))
        for y in (S.AMI_Y0 - 9.0 + k * 36.0 for k in range(4)):  # ribs along x, between fuse lines (no wire under them)
            parts.append(box(S.SKIRT, y - S.RIB / 2, z_d, L - S.SKIRT, y + S.RIB / 2, z_t - S.PLATE + 0.01))
        # saddles: one per relay feed, the inside of its bend (R_SADDLE), hanging under the deck, with side lips
        saddles = []
        for a in ami:
            if a['row'] != 'IN' or not a['amps']:
                continue
            r = relays[a['i']]
            od = S.OD[S.AMI_AWG[a['name']]]
            ccx, ccz = r['cx'] + S.R_SADDLE + od / 2, S.LUG_C + S.R_SADDLE + od / 2      # every feed hugs its saddle: inside radius = R_SADDLE
            rs = S.R_SADDLE - 0.2                                                       # 0.2 clear of the wire in the model
            core = bo(cyl((ccx, a['y'] - od / 2 - 0.5, ccz), (ccx, a['y'] + od / 2 + 0.5, ccz), 2 * rs),
                      box(ccx - rs - 1, a['y'] - 10, ccz - rs - 1, ccx, a['y'] + 10, ccz), 'i')
            for sy in (-1, 1):
                lip = bo(cyl((ccx, a['y'] + sy * (od / 2 + 0.5), ccz), (ccx, a['y'] + sy * (od / 2 + 2.0), ccz), 2 * (S.R_SADDLE + od * 0.75)),
                         box(ccx - S.R_SADDLE - od - 2, a['y'] - 10, ccz - S.R_SADDLE - od - 2, ccx, a['y'] + 10, ccz), 'i')
                bo(core, lip, 'u')
            bo(core, box(ccx - rs, a['y'] - od / 2 - 2.0, ccz - 0.01, ccx, a['y'] + od / 2 + 2.0, z_d + 0.5), 'u')     # hangs from the deck, clear of the vertical wire
            saddles.append(core)
        parts += saddles
        # outboard comb: fins between the straight OUT-row cables where they leave under the end of the deck
        for k in range(S.AMI_SLOTS['OUT'] + 1):
            y = S.AMI_Y0 + (k - 0.5) * S.AMI_PITCH
            parts.append(box(xb + 44.0, y - 1.0, 3.0, L - S.SKIRT + 0.01, y + 1.0, z_d + 0.01))
        legs_and_ears(L, z_d, parts, lims)
        deck = base_shell(L, z_d, z_t, parts)
        cuts = base_snap_cuts(L, z_t)
        B_ = S.BAR
        cuts.append(box(xb - B_['w'] / 2 - S.CLR, B_['y0'] - S.CLR, bz0, xb + B_['w'] / 2 + S.CLR, B_['y1'] + S.CLR, z_t + 1))
        for a in ami:
            cuts.append(pad_box(a, pz0, z_t + 1, S.CLR))
            xc = (a['x_in'] + a['x_out']) / 2
            cuts.append(cbox(xc, a['y'], btop + S.AMI['ear_t'] / 2 - S.AMI['body_h'] / 2 - 0.6, z_t + 1, S.AMI['body_l'] + 1, S.AMI['body_w'] + 1))
            cuts.append(hexz(a['x_out'], a['y'], z_d - 1, pz0 + 0.01, SO['af'] + 2 * S.CLR))          # standoff, through
        for (bx_, by_, m) in bar_bolts:
            cuts.append(hexz(bx_, by_, z_d - 1, bz0 + 0.01, HD[m]['af'] + 2 * S.CLR))                  # head pocket, from below
            cuts.append(cylz(bx_, by_, z_d - 1, bz0 + 1, m + 0.5))
        for r in relays:   # Mini ISO cavities (F7 bottom view: 30 / 87 blades along x, 85 / 86 along y), through the deck
            pins = [(0, 7.65, 11.5, 3.2), (0, -10.25, 11.5, 3.2), (-8.45, -0.25, 2.8, 8.3), (8.45, -0.25, 2.8, 8.3)]
            if r['B']:
                pins.append((0, S.RELAY_B['v87a'], 8.3, 2.8))
            for (u, v, lx, ly) in pins:
                cuts.append(cbox(r['cx'] + u, r['cy'] + v, z_d - 1, z_t + 1, lx, ly))
        for dx in (-3.0, 3.0):
            cuts.append(cbox(acps[0] + dx, acps[1], z_d - 1, z_t + 1, 3.0, 4.6))
        sub_all(deck, cuts)
        comp(pre + 'Base_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_brass', lims, AP['brass'], MAT['brass'], sh)

        # ---- copper, standoffs, bolts
        bar = box(xb - B_['w'] / 2, B_['y0'], bz0, xb + B_['w'] / 2, B_['y1'], btop)
        bo(bar, cylz(xb, S.IN_STUD_Y, bz0 - 1, btop + 1, 8.5), 's')
        pads = []
        for a in ami:
            bo(bar, cylz(a['x_in'], a['y'], bz0 - 1, btop + 1, 5.5), 's')
            p = pad_box(a, pz0, btop)
            bo(p, cylz(a['x_out'], a['y'], pz0 - 1, btop + 1, 5.5), 's')
            pads.append(p)
        comp(pre + 'Bar_Power_%s_25x6p35' % BM['name'], bar, AP['tin'], MAT['cu'], sh)
        comp(pre + 'Pad_Out_%s_15x3' % BM['name'], pads, AP['tin'], MAT['cu'], sh)
        comp(pre + 'Standoff_M5_FF_hex8_L40_brass', [bo(hexz(a['x_out'], a['y'], lz + 2.0, pz0, SO['af']), cylz(a['x_out'], a['y'], lz, pz0 + 1, 4.2), 's')
                                                     for a in ami], AP['brass'], MAT['brass'], sh)
        z_ear = btop + S.AMI['ear_t']
        studs = [union_all([hexz(bx_, by_, bz0 - HD[m]['k'], bz0, HD[m]['af']), cylz(bx_, by_, bz0, btop + (12.0 if m == 5 else 16.0), float(m))])
                 for (bx_, by_, m) in bar_bolts]
        studs += [cylz(a['x_out'], a['y'], pz0 - 6.0, z_ear + 5.0, 5.0) for a in ami]                                   # M5 set screw on top
        studs += [union_all([hexz(a['x_out'], a['y'], lz - HD[5]['k'], lz, HD[5]['af']), cylz(a['x_out'], a['y'], lz, lz + 10.0, 5.0)])
                  for a in ami if a['amps']]                                                                           # M5x10 under the lug
        nuts = [hexz(a['x_in'], a['y'], z_ear, z_ear + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami]
        nuts += [hexz(a['x_out'], a['y'], z_ear, z_ear + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami]
        nuts.append(hexz(xb, S.IN_STUD_Y, btop + M8['t'], btop + M8['t'] + S.M8_NUT['h'], S.M8_NUT['af']))
        comp(pre + 'Bolt_SetScrew_ISO4017_A2', studs, AP['al'], MAT['ss'], sh)
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

        # ---- lugs + cables: OUT row straight out +x under the deck end; IN row straight -x, one bend up round its saddle
        lugs, wires = [], []
        for a in ami:
            if a['amps'] is None:
                continue
            awg = S.AMI_AWG[a['name']]
            od = S.OD[awg]
            lg = S.LUG_6AWG if awg == 6 else LUG
            t, e = ring_lug(a['x_out'], a['y'], lz, lg['b'], 5.5, lg['t'], lg['d4'], (a['sgn'], 'x'), lg['l'] - lg['tip'])
            lugs.append(t)
            if a['row'] == 'OUT':
                wires.append(cyl(e, (L + 30.0, a['y'], e[2]), od))
                bend_row('POWER AMI %s %s (%dA) -> harness' % (a['row'], a['name'], a['amps']), awg, 'straight out under the outboard end, lug axis',
                         None, False, 'no bend in the box; first bend in the harness: >= %.0f supported (P-clamp each side) or >= %.0f free' % (3 * od, 10 * od))
            else:
                r = relays[a['i']]
                rcw = S.R_SADDLE + od / 2
                cz = e[2] + rcw
                w_ = cyl(e, (r['cx'] + rcw, a['y'], e[2]), od)
                bo(w_, quarter_bend(r['cx'] + rcw, a['y'], cz, rcw, od, (-1, -1)), 'u')
                if z_d - 0.2 - cz > 0.1:
                    bo(w_, cyl((r['cx'], a['y'], cz), (r['cx'], a['y'], z_d - 0.2), od), 'u')
                wires.append(w_)
                bend_row('POWER AMI IN %s (%dA) -> %s terminal 30' % (a['name'], a['amps'], r['name']), awg,
                         'straight %.0f mm, then 90 deg up round the printed saddle into the cavity' % (e[0] - r['cx'] - rcw),
                         S.R_SADDLE, True, 'saddle R%.0f under the deck sets and supports the bend' % S.R_SADDLE)
        t, e = ring_lug(xb, S.IN_STUD_Y, btop, M8['b'], 8.4, M8['t'], M8['d4'], (1, 'x'), M8['l'] - M8['tip'], barrel=19.0)
        lugs.append(t)
        wires.append(cyl(e, (L + 30.0, S.IN_STUD_Y, e[2]), S.OD['1/0']))
        bend_row('POWER 1/0 input (M8 on the bar)', '1/0', 'straight in through the cover end notch, lug axis', None, False,
                 'no bend in the box; first bend outside >= %.0f supported / >= %.0f free' % (3 * S.OD['1/0'], 10 * S.OD['1/0']))
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_stub', wires, AP['wire'], None, sh)
        bend_row('POWER relay terminals (85 / 86 / 87 / 87a), largest %d AWG' % S.RELAY_OUT_AWG, S.RELAY_OUT_AWG,
                 'straight down out of the cavity, bend under the deck', round(z_d - S.OD[S.RELAY_OUT_AWG] / 2 - 2.0, 1), True,
                 'room under the deck before the mount face; tie each bend to the saddle row / comb')

        # ---- cover
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
        labels.append(('1/0 IN', xb + 24.0, S.IN_STUD_Y, S.LABEL['h_ami']))
        labels.append(('POWER', xb - 50.0, 6.0, 5.0))
        cover(L, S.D, z_t, z_top, [('x', L + W_CL + CV['t'] / 2, S.IN_STUD_Y, btop + M8['d4'] / 2 + S.OD['1/0'] / 2 + 1.5, S.OD['1/0'] + 2.0)],
              labels, pre, sh)
        return dict(L=L, D=S.D, H=z_top, z_d=z_d, z_t=z_t, cover_top=z_top, Rc=Rc)

    # ================================================================== LOGIC box
    def build_logic():
        LGc = S.LOGIC
        L, z_d, z_t, s_top = LGc['L'], LGc['z_d'], LGc['z_t'], LGc['strip_top']
        sh = S.PLACE['LOGIC']
        pre = 'Logic_'
        lz = S.LUG_Z
        ST, SF = S.STRIP, S.STRIP_FEED
        s_bot = s_top - ST['t']
        mini, micro = [], []
        for col, (cx, fuses) in S.MINI_COLS.items():
            for i, (nm, amps) in enumerate(fuses):
                mini.append((col, nm, amps, cx, S.MINI_Y0 + i * S.MINI['pitch']))
        k = 0
        for cx in S.MICRO_COLS:
            for cy in S.MICRO_Y:
                nm, pn, own = S.MICRO_POS[k]
                k += 1
                micro.append((nm, pn, own, cx, cy))

        def strip_y1(n):
            return S.MINI_Y0 + (n - 1) * S.MINI['pitch'] + 6

        feeds = []
        for col, (cx, fuses) in S.MINI_COLS.items():
            y1 = strip_y1(len(fuses)) + SF['ext'][col]
            feeds.append((col, cx, y1, y1 - SF['hole_from_end']))
        parts, lims = [], []
        T = S.TOWER
        for (col, cx, y1, yh) in feeds:
            parts.append(box(cx - S.MINI['l'] / 2 - T, S.MINI_Y0 - 6.4 - T, z_d, cx + S.MINI['l'] / 2 + T, y1 + 0.4 + T, z_t - S.PLATE + 0.01))
        for (nm, pn, own, cx, cy) in micro:
            parts.append(cbox(cx, cy, z_d, z_t - S.PLATE + 0.01, 11.6 + 2 * T, 18.6 + 2 * T))
        legs_and_ears(L, z_d, parts, lims, rear_x=(45.0, L - LG['d'] / 2))     # Bus 1 / Bus 2 feeds leave the rear at x 12.5 / 27
        deck = base_shell(L, z_d, z_t, parts)
        cuts = base_snap_cuts(L, z_t)
        for (col, nm, amps, cx, y) in mini:      # 2 x 2.8 mm receptacles per mini fuse
            for dx in (-3.0, 3.0):
                cuts.append(cbox(cx + dx, y, z_d - 1, z_t + 1, 3.0, 4.6))
        for (nm, pn, own, cx, cy) in micro:      # approximate pattern from TE 1308028; set exactly in detail work
            for (u, v, lx, ly) in ((0, 8.0, 8.3, 2.6), (0, -8.0, 8.3, 2.6), (-4.5, 0, 2.6, 6.8), (4.5, 0, 2.6, 6.8), (0, 0, 2.6, 4.0)):
                cuts.append(cbox(cx + u, cy + v, z_d - 1, z_t + 1, lx, ly))
        for (col, cx, y1, yh) in feeds:          # strip pocket open underneath (strip goes in from below), standoff hex through
            cuts.append(box(cx - ST['w'] / 2 - S.CLR, S.MINI_Y0 - 6 - S.CLR, z_d - 1, cx + ST['w'] / 2 + S.CLR, y1 + S.CLR, s_top + S.CLR))
            cuts.append(hexz(cx, yh, s_top - 0.01, s_top + HD[5]['k'] + 0.3, HD[5]['af'] + 2 * S.CLR))        # feed bolt head above the strip
            cuts.append(cylz(cx, yh, s_top, z_t + 1, 9.0))
        sub_all(deck, cuts)
        comp(pre + 'Base_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_brass', lims, AP['brass'], MAT['brass'], sh)
        strips, hw, lugs, wires = [], [], [], []
        for (col, cx, y1, yh) in feeds:
            st = box(cx - ST['w'] / 2, S.MINI_Y0 - 6, s_bot, cx + ST['w'] / 2, y1, s_top)
            bo(st, cylz(cx, yh, s_bot - 1, s_top + 1, 5.5), 's')
            strips.append(st)
            hw.append(union_all([hexz(cx, yh, s_top, s_top + HD[5]['k'], HD[5]['af']), cylz(cx, yh, s_bot - 6.0, s_top, 5.0)]))     # M5 bolt down into the standoff
            hw.append(union_all([hexz(cx, yh, lz - HD[5]['k'], lz, HD[5]['af']), cylz(cx, yh, lz, lz + 10.0, 5.0)]))                 # M5 up through the lug
            awg = S.FEEDS[col][1]
            od = S.OD[awg]
            t, e = ring_lug(cx, yh, lz, LUG['b'], 5.5, LUG['t'], LUG['d4'], (1, 'y'), LUG['l'] - LUG['tip'])
            lugs.append(t)
            wires.append(cyl(e, (cx, S.D + 30.0, e[2]), od))
            bend_row('LOGIC %s feed (from %s)' % (col, S.FEEDS[col][0]), awg, 'straight out under the rear edge, lug axis', None, False,
                     'no bend in the box; first bend in the harness: >= %.0f supported or >= %.0f free' % (3 * od, 10 * od))
        comp(pre + 'Strip_Logic_%s_10x3' % BM['name'], strips, AP['tin'], MAT['cu'], sh)
        comp(pre + 'Standoff_M5_FF_hex8_L25_brass', [bo(hexz(cx, yh, lz + 2.0, s_bot, SO['af']), cylz(cx, yh, lz, s_bot + 1, 4.2), 's') for (col, cx, y1, yh) in feeds],
             AP['brass'], MAT['brass'], sh)
        comp(pre + 'FeedBolt_M5_ISO4017_A2', hw, AP['al'], MAT['ss'], sh)
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_stub', wires, AP['wire'], None, sh)
        bend_row('LOGIC fuse / micro relay receptacles, largest %d AWG' % S.LOGIC_MAX_AWG, S.LOGIC_MAX_AWG, 'straight down out of the cavity, bend under the deck',
                 round(z_d - S.OD[S.LOGIC_MAX_AWG] / 2 - 2.0, 1), True, 'room under the deck before the mount face')
        by_amp = {}
        for (col, nm, amps, cx, y) in mini:
            if amps is not None:
                by_amp.setdefault(amps, []).append(cbox(cx, y, z_t, z_t + S.MINI['h_above'], S.MINI['l'], S.MINI['w']))
        for amps, bodies in by_amp.items():
            comp(pre + 'Fuse_ATM_%sA' % str(amps).replace('.', 'p'), bodies, MINI_AP[amps], MAT['abs'], sh)
        comp(pre + 'Relay_TE_MicroA_V23074', [cbox(cx, cy, z_t, z_t + S.MICRO['h'], S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy) in micro if pn],
             AP['black'], MAT['abs'], sh)
        comp(pre + 'SPARE_positions', [cbox(cx, cy, z_t, z_t + 1.0, S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy) in micro if not pn], AP['spare'], None, sh)
        z_top = z_t + 25.4 + CV['clear'] + CV['t']          # micro relay 25.4 max (TE 1308028)
        short = {'HEAD LH': 'HEAD L', 'HEAD RH': 'HEAD R', 'horn': 'HORN', 'k_etb': 'ETB', 'k_acc': 'A/C', 'k_eps_en': 'EPS EN', 'k_rev': 'REV', 'SPARE': 'SPARE'}
        labels = [(short[nm], cx, cy, S.LABEL['h_micro']) for (nm, pn, own, cx, cy) in micro]
        labels += [(('%s %s' % (nm, ('%g' % amps))) if amps else 'SP', cx, y, S.LABEL['h_mini']) for (col, nm, amps, cx, y) in mini]
        labels += [(col, cx, S.MINI_Y0 - 11.0, S.LABEL['h_mini']) for (col, cx, y1, yh) in feeds]
        labels.append(('LOGIC', 54.0, 168.0, 5.0))
        cover(L, S.D, z_t, z_top, [], labels, pre, sh)
        return dict(L=L, D=S.D, H=z_top, z_d=z_d, z_t=z_t, cover_top=z_top)

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
        # ---- base: rounded floor plate, low rim on the long sides only (ends open), relay platform, pedestal, 2 tabs
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
        for y in (tsy - Bb['w'] / 2 + 1.25, tsy, tsy + Bb['w'] / 2 - 1.25):              # pedestal ribs under bar + pad
            parts.append(box(Bb['x0'], y - S.RIB / 2, fl - 0.01, Bb['x1'], y + S.RIB / 2, bz0))
            parts.append(box(a_out - S.PAD['inner'], y - S.RIB / 2, fl - 0.01, a_out + S.PAD['outer'], y + S.RIB / 2, pz0))
        rb_bolts = [(xst, 6, bz0), (a_in, 5, bz0), (a_out, 5, pz0)]
        for (px, m, zu) in rb_bolts:
            parts.append(cylz(px, tsy, fl - 0.01, zu, HD[m]['af'] / math.cos(math.radians(30)) + 2 * S.CLR + 5.0))
        for sy in (-1, 1):                                                          # the two tabs, one per long side, mid-length
            y0 = -LG['ear_len'] if sy < 0 else Dr
            tab = box(R['tabs_x'] - LG['ear_w'] / 2, y0, 0, R['tabs_x'] + LG['ear_w'] / 2, y0 + LG['ear_len'] + 0.01, LG['ear_t'])
            hy = -LG['ear_len'] / 2 if sy < 0 else Dr + LG['ear_len'] / 2
            bo(tab, cylz(R['tabs_x'], hy, 0, LG['ear_t'], LG['ear_w']), 'u')
            bo(tab, cylz(R['tabs_x'], hy, -1, LG['ear_t'] + 1, LG['hole']), 's')     # plain 6 mm tab: the cover skirt stops just above it
            parts.append(tab)
            lims.append(bo(cylz(R['tabs_x'], hy, 0, l5['l'], l5['od']), cylz(R['tabs_x'], hy, -1, l5['l'] + 1, l5['id']), 's'))
        base = union_all([base] + parts)
        cuts = []
        for x in hxs:                                   # flange bolt: limiter 4.6 under the flange, M6 nut captured from below
            cuts.append(cylz(x, fy, 5.4, zf + 1, LM['od'] + 2 * S.CLR))
            cuts.append(hexz(x, fy, -1, 5.4, 10.0 + 2 * S.CLR))
            lims.append(bo(cylz(x, fy, 5.4, zf, LM['od']), cylz(x, fy, 5.3, zf + 1, LM['id']), 's'))
        for (px, m, zu) in rb_bolts:                    # bolt heads captured in hex pockets under the copper (dropped in from the top)
            cuts.append(hexz(px, tsy, zu - HD[m]['k'] - 0.3, zu + 0.01, HD[m]['af'] + 2 * S.CLR))
        for x in snap_xs(Lr):
            for y in (0.0, Dr):
                cuts.append(cyl((x - S.SNAP['w'] / 2 - 0.5, y, R['rim'] - 3.0), (x + S.SNAP['w'] / 2 + 0.5, y, R['rim'] - 3.0), S.SNAP['bump'] + 0.2))
        sub_all(base, cuts)
        comp(pre + 'Base_PA12_printed', base, AP['pa12_lt'], MAT['pa'], sh)
        comp(pre + 'Limiter_brass', lims, AP['brass'], MAT['brass'], sh)
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
        bo(rel, box(gcx - 5.0, yb - H_['plug_to'], tz0, gcx + 5.0, yb + 0.01, tz0 + 9.0), 'u')       # Superseal 1.5 2-pole coil plug
        comp(pre + 'Relay_TE_HCR150_1416010-1', rel, AP['black'], MAT['abs'], sh)
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
        studs = [union_all([hexz(px, tsy, zu - HD[m]['k'], zu, HD[m]['af']), cylz(px, tsy, zu, btop + 12.0, float(m))]) for (px, m, zu) in rb_bolts]
        studs += [union_all([hexz(x, fy, zf + H_['flange_t'], zf + H_['flange_t'] + 4.0, 10.0), cylz(x, fy, 0.5, zf + H_['flange_t'], 6.0)]) for x in hxs]
        nuts = [hexz(a_in, tsy, lug_z, lug_z + S.M5_NUT['h'], S.M5_NUT['af']), hexz(a_out, tsy, lug_z + 2.0, lug_z + 2.0 + S.M5_NUT['h'], S.M5_NUT['af']),
                hexz(xst, tsy, btop + 2.0, btop + 2.0 + 5.2, 10.0)] + [hexz(x, fy, 0.2, 5.4, 10.0) for x in hxs]
        comp(pre + 'Bolt_M5_M6_ISO4017_A2', studs, AP['al'], MAT['ss'], sh)
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
        cy_ = yb - H_['plug_to']                         # coil lead: out of the plug toward -y, one R6 turn to +x, along the front to the +x end
        rcl = 7.0
        yl, zl = cy_ - rcl - 1.0, tz0 + 4.5
        cw = cyl((gcx, cy_, zl), (gcx, yl + rcl, zl), odc)
        tq = torus(gcx + rcl, yl + rcl, zl, V(0, 0, 1), rcl, odc / 2)
        bo(tq, box(gcx - odc, yl - odc, zl - odc, gcx + rcl, yl + rcl, zl + odc), 'i')
        bo(cw, tq, 'u')
        bo(cw, cyl((gcx + rcl, yl, zl), (Lr + 30.0, yl, zl), odc), 'u')
        wires.append(cw)
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_stub', wires, AP['wire'], None, sh)
        bend_row('BATTERY feed in (kill switch load side) -> M6 stud', R['awg_feed'], 'straight in at the open -x end, lug axis', None, False,
                 'no bend in the block; first bend outside >= %.0f supported / >= %.0f free' % (3 * odf, 10 * odf))
        bend_row('BATTERY AMI 40 out -> HCR150 terminal 3', R['awg_feed'], 'one straight jumper, both lugs at the terminal height', None, True,
                 'no bend (the AMI pedestal puts its lug level with terminal 3)')
        bend_row('BATTERY HCR150 terminal 5 -> pump', R['awg_pump'], 'straight out the open +x end, lug axis', None, False,
                 'no bend in the block; first bend outside >= %.0f supported / >= %.0f free' % (3 * odp, 10 * odp))
        bend_row('BATTERY coil lead (Superseal plug) -> Link Aux 3', R['awg_coil'], 'one 90 deg turn, then along the front to the +x end',
                 round(rcl - odc / 2, 1), True, 'held by the plug and the cover notch; 3 x OD = %.1f' % (3 * odc))
        # ---- cover: Blue Sea 7720-style low pillow, end breakouts only
        z_top = zf + H_['depth'] + CV['clear'] + CV['t']
        notches = [('x', -W_CL - CV['t'] / 2, tsy, e_in[2] + odf / 2 + 2.0, 9.0), ('x', Lr + W_CL + CV['t'] / 2, tsy, e3[2] + odp / 2 + 2.0, 9.0),
                   ('x', Lr + W_CL + CV['t'] / 2, yl, zl + odc / 2 + 1.5, 5.0)]
        labels = [('BATT +', xst, tsy + 20.0, 4.5), ('FP 40A', (a_in + a_out) / 2, tsy, 4.0), ('K_FP  FUEL PUMP', rx, yb + 26.0, 5.0),
                  ('3', xs[0], tsy, 4.0), ('5', xs[1], tsy, 4.0), ('PUMP', Lr - 16.0, tsy + 20.0, 4.5), ('COIL', Lr - 16.0, yl + 8.0, 3.5)]
        g, t_ = W_CL, CV['t']
        zb = LG['ear_t'] + 0.5
        out = rtop(-g - t_, -g - t_, Lr + g + t_, Dr + g + t_, zb, z_top, 12.95, 6.0)
        inn = rtop(-g, -g, Lr + g, Dr + g, zb - 1, z_top - t_, 10.45, 3.5)
        bo(out, inn, 's')
        sw = S.SNAP
        zc = R['rim'] - 3.0
        for x in snap_xs(Lr):
            for (yf, sy) in ((-g, -1), (Dr + g, 1)):
                for dx in (-1, 1):
                    xs_ = x + dx * (sw['w'] / 2 + sw['slot'] / 2)
                    bo(out, box(xs_ - sw['slot'] / 2, yf - t_ - 1 if sy < 0 else yf - 1, zb - 1, xs_ + sw['slot'] / 2, yf + 1 if sy < 0 else yf + t_ + 1, zb + sw['len']), 's')
                bo(out, cyl((x - sw['w'] / 2 + 0.5, yf, zc), (x + sw['w'] / 2 - 0.5, yf, zc), sw['bump']), 'u')
        for (axis, pos, u, zn, wd) in notches:
            n = box(pos - 6, u - wd / 2, zb - 1, pos + 6, u + wd / 2, zn - wd / 2)
            bo(n, cyl((pos - 6, u, zn - wd / 2), (pos + 6, u, zn - wd / 2), wd), 'u')
            bo(out, n, 's')
        oc = comp(pre + 'Cover_PA12_printed', out, AP['pa12'], MAT['pa'], sh)
        etch(oc, labels, z_top, sh)
        return dict(L=Lr, D=Dr, H=z_top, L_with_tabs=Lr, D_with_tabs=Dr + 2 * LG['ear_len'])

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
    lug_bs = bodies('Power_Lug_')
    in_lug = max(lug_bs, key=lambda lb: lb.volume)
    out_lugs = [lb for lb in lug_bs if lb is not in_lug]
    so = bodies('Power_Standoff_')
    rb_lugs = bodies('BattRelay_Lug_')
    report['live_clearance'] = {
        'pad_to_pad_min_mm': min(neigh),
        'bar_to_pad_min_mm': min(dist(bodies('Power_Bar_')[0], pb) for pb in pad_bs),
        'input_lug_to_pad_min_mm': min(dist(in_lug, pb) for pb in pad_bs),
        'under_deck_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(out_lugs) for l2 in out_lugs[i_ + 1:]),
        'standoff_to_standoff_min_mm': min(dist(s1, s2) for i_, s1 in enumerate(so) for s2 in so[i_ + 1:]),
        'logic_strip_to_strip_mm': dist(*bodies('Logic_Strip_')[:2]),
        'logic_feed_lug_to_lug_mm': dist(*bodies('Logic_Lug_')[:2]),
        'battrelay_bar_to_pad_mm': dist(bodies('BattRelay_Bar_')[0], bodies('BattRelay_Pad_')[0]),
        'battrelay_relay_lug_to_lug_mm': dist(rb_lugs[2], rb_lugs[3]),
    }
    # every cable stub against every printed part (a wire through plastic = a bad route)
    wire_hits = []
    for wpre in ('Power_', 'Logic_', 'BattRelay_'):
        for wb in bodies(wpre + 'Wire_stub'):
            for pb in bodies(wpre + 'Base_') + bodies(wpre + 'Cover_'):
                d = dist(wb, pb)
                if d <= 0.0:
                    wire_hits.append((wpre + 'Wire', pb.parentComponent.name, d))
    report['wire_to_printed_contact'] = wire_hits
    printed = {}
    for o in root.occurrences:
        n = o.component.name
        if n.endswith('_printed'):
            ob = mm.getOrientedBoundingBox(o.bRepBodies.item(0), V(1, 0, 0), V(0, 1, 0))
            vol = sum(b.volume for b in o.bRepBodies)
            printed[n] = dict(size_mm=[round(ob.length * 10, 1), round(ob.width * 10, 1), round(ob.height * 10, 1)], volume_cm3=round(vol, 1),
                              mass_g_pa12=round(vol * 1.01, 0), bodies=o.bRepBodies.count)
    report['printed_parts'] = printed
    report['boxes_mm'] = {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in sizes.items()}
    report['bar_metal'] = S.BAR_METAL
    coll = adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        nm = o.component.name.split('_', 1)[1]
        if not nm.startswith(('Wire_', 'Bolt_', 'Nut_', 'Lug_', 'FeedBolt_', 'Standoff_', 'Limiter_')):
            coll.add(o)
    try:
        ir = design.analyzeInterference(design.createInterferenceInput(coll))
        report['interference'] = [(r.entityOne.parentComponent.name if hasattr(r.entityOne, 'parentComponent') else str(r.entityOne),
                                   r.entityTwo.parentComponent.name if hasattr(r.entityTwo, 'parentComponent') else str(r.entityTwo),
                                   round(r.interferenceBody.volume * 1000, 3)) for r in ir]
    except Exception as ex:   # report, do not hide
        report['interference_error'] = str(ex)
    report['mass_g'] = {o.component.name: round(o.component.physicalProperties.mass * 1000, 1) for o in root.occurrences
                        if o.component.name.split('_', 1)[1].startswith(('Bar', 'Pad', 'Strip'))}

    # ------------------------------------------------------------------ exports
    em = design.exportManager
    exported = []
    for o in root.occurrences:
        n = o.component.name
        if n.endswith('_printed') or n.split('_', 1)[1].startswith(('Bar_', 'Pad_', 'Strip_')):
            p = os.path.join(out_dir, '%s.step' % n)
            em.execute(em.createSTEPExportOptions(p, o.component))
            exported.append(os.path.basename(p))
        if n.endswith('_printed'):
            p = os.path.join(out_dir, '%s.stl' % n)
            so_ = em.createSTLExportOptions(o, p)
            so_.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(so_)
            exported.append(os.path.basename(p))
    p = os.path.join(out_dir, '%s_assembly.step' % DOC)
    em.execute(em.createSTEPExportOptions(p, root))
    exported.append(os.path.basename(p))
    em.execute(em.createFusionArchiveExportOptions(os.path.join(out_dir, '%s.f3d' % DOC)))
    exported.append('%s.f3d' % DOC)
    report['exported'] = exported

    # ------------------------------------------------------------------ images
    vp = app.activeViewport
    VO = adsk.core.ViewOrientations

    def show(pred):
        for o in root.occurrences:
            o.isLightBulbOn = bool(pred(o.component.name))

    def shot(fn, eye=None, target=(150.0, 60.0, 30.0), orient=None):
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
        vp.saveAsImageFile(os.path.join(out_dir, fn), 1800, 1100)

    def kind(n):
        return n.split('_', 1)[1]

    LOADED = lambda n: not kind(n).startswith('Cover')
    EMPTY = lambda n: kind(n).startswith(('Base', 'Limiter', 'Bar', 'Pad', 'Strip', 'Standoff'))
    GLOVE = lambda n: not n.startswith('BattRelay_')
    BATT = lambda n: n.startswith('BattRelay_')
    show(GLOVE)
    shot('fusebox_render_iso_closed.png', eye=(-300, -480, 380), target=(140.0, 90.0, 30.0))
    show(lambda n: GLOVE(n) and LOADED(n))
    shot('fusebox_render_iso_open.png', eye=(-300, -480, 380), target=(140.0, 90.0, 30.0))
    shot('fusebox_render_iso_open_rear.png', eye=(320, 480, 380), target=(140.0, 90.0, 30.0))
    shot('fusebox_render_under.png', eye=(-260, -420, -230), target=(140.0, 90.0, 20.0))
    show(lambda n: GLOVE(n) and EMPTY(n))
    shot('fusebox_render_iso_empty.png', eye=(-300, -480, 380), target=(140.0, 90.0, 30.0))
    shot('fusebox_render_top_empty.png', orient=VO.TopViewOrientation)
    show(lambda n: n.startswith('Power_') and (kind(n).startswith(('Base', 'Wire', 'Lug', 'Standoff', 'Bolt', 'Limiter'))))
    shot('fusebox_render_power_bends.png', eye=(-120, -330, -150), target=(165.0, 80.0, 15.0))
    show(lambda n: BATT(n))
    shot('battrelay_render_iso_closed.png', eye=(-220, -300, 260), target=(92.0, -110.0, 20.0))
    show(lambda n: BATT(n) and LOADED(n))
    shot('battrelay_render_iso_open.png', eye=(-220, -300, 260), target=(92.0, -110.0, 20.0))
    show(lambda n: BATT(n) and EMPTY(n))
    shot('battrelay_render_iso_empty.png', eye=(-220, -300, 260), target=(92.0, -110.0, 20.0))
    show(lambda n: True)

    if save:
        try:
            if doc.dataFile.name != DOC:
                doc.dataFile.name = DOC
                report['renamed_document_to'] = DOC
        except Exception as ex:   # report, do not hide
            report['rename_error'] = str(ex)
        doc.save('rev 4: base + snap cover, open bottom, bend radius, etched labels (Claude Code 2026-10-14)')
    with open(os.path.join(out_dir, 'fusebox_report.json'), 'w') as f:
        json.dump(report, f, indent=1)
    return report
