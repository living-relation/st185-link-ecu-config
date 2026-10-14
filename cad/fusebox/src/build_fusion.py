"""Build the ST185 fuse + relay boxes (rev 3: LOGIC box, POWER box, battery relay block) in the existing Fusion
fusebox document, export every part, render, check isolation and interference.
Run inside Fusion (Fusion MCP script runner):  build(out_dir)
Same toolkit as cad/busbar/src/build_fusion.py (TemporaryBRepManager bodies, one component per part, all
instances placed in the root - never via proxy transform overrides; bodies are moved with tb.transform before they
are added). R74: never makes a new document - it opens the existing fusebox document and saves a new version.
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
DOC = 'ST185_fusebox_rev3'               # rev 3: two boxes + battery relay block (R75)
DOC_OLD = ('ST185_fusebox_rev2',)        # the same Fusion document before the rename (R74: reuse, no new docs)


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
    """Stadium along x, round ends centred at x0 and x1."""
    s = box(x0, cy - w / 2, z0, x1, cy + w / 2, z1)
    bo(s, cylz(x0, cy, z0, z1, w), 'u')
    bo(s, cylz(x1, cy, z0, z1, w), 'u')
    return s


def slot_y(cx, y0, y1, z0, z1, w):
    """Stadium along y, round ends centred at y0 and y1."""
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


def ring_lug(x, y, z, b, hole, t, d4, along, length, down=False, barrel=9.0):
    """Tubular ring lug lying flat at z: round palm at (x, y), barrel (d4, last 9 mm) along +-x or +-y.
    along = (+1|-1, 'x'|'y'); down = barrel below the palm (lug screwed on from underneath). Returns (body, barrel end)."""
    sgn, ax = along
    zc = z + t - d4 / 2 if down else z + d4 / 2
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


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    doc = open_doc()
    doc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    for i in range(root.occurrences.count - 1, -1, -1):
        root.occurrences.item(i).deleteMe()
    report = {}

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
        'al': ap('Aluminum - Satin'), 'al_bar': ap('Aluminum - Brushed Linear'),
        'black': ap('Plastic - Matte (Black)'), 'brass': ap('Brass - Matte'), 'cu': ap('Copper - Raw'),
        'wire': ap('Plastic - Glossy (Red)'),
        'orange': tint('Plastic - Glossy (Red)', 'AMI orange', (240, 120, 20)),
        'ltgreen': tint('Plastic - Glossy (Green)', 'AMI lt green', (130, 220, 120)),
        'red': ap('Plastic - Glossy (Red)'), 'yellow': ap('Plastic - Glossy (Yellow)'),
        'spare': tint('Plastic - Matte (Gray)', 'Spare position', (200, 200, 200)),
        'pa12': tint('Plastic - Matte (Gray)', 'PA12 MJF grey', (95, 98, 102)),
        'pa12_lt': tint('Plastic - Matte (Gray)', 'PA12 MJF light', (150, 154, 158)),
        'tin': tint('Aluminum - Satin', 'Tinned copper', (200, 200, 190)),
    }
    MINI_AP = {2: tint('Plastic - Glossy (Grey)', 'ATM 2A grey', (150, 150, 150)), 5: tint('Plastic - Glossy (Red)', 'ATM 5A tan', (205, 170, 120)),
               7.5: tint('Plastic - Glossy (Red)', 'ATM 7.5A brown', (120, 70, 40)), 10: ap('Plastic - Glossy (Red)'),
               15: ap('Plastic - Glossy (Blue)'), 20: ap('Plastic - Glossy (Yellow)')}
    MAT = {'al': mlib.materials.itemByName('Aluminum 6061'), 'pa': mlib.materials.itemByName('Nylon 6/6'),   # PA12 stand-in
           'cu': mlib.materials.itemByName('Copper'), 'brass': mlib.materials.itemByName('Brass'),
           'ss': mlib.materials.itemByName('Stainless Steel AISI 304'), 'abs': mlib.materials.itemByName('ABS Plastic')}
    BM = S.METAL[S.BAR_METAL]
    is_cu = S.BAR_METAL.startswith('Cu')
    AP_BAR = AP['tin'] if is_cu else AP['al_bar']
    MAT_BAR = MAT['cu'] if is_cu else MAT['al']

    def comp(cname, bodies, appearance=None, material=None, shift=(0.0, 0.0)):
        bl = bodies if isinstance(bodies, list) else [bodies]
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
        return occ

    W, F, D = S.WALL, S.FLOOR, S.D
    BZ0 = S.BAR_TOP - S.BAR_T                          # 46.65: bar underside (1/4" stock)
    PZ0 = S.BAR_TOP - S.PAD['t']                       # 50: pad underside (3 mm stock) - pad top level with the bar top
    LUG, M8 = S.LUG_M5, S.LUG_M8
    HOLE_OFF = 17.0          # wire hole through the deck, from the output stud, just past the lug barrel
    WIRE_D = 6.0
    gz = S.BAR_TOP + M8['d4'] / 2                      # 1/0 lug lies on top of the bar (no machined inset, R76)
    IN3, E, l5 = S.INSERT_M3, S.EAR, S.LIMITER_M5
    HD = S.HEAD
    occs = {}                                          # lids, hidden for the open renders

    def bolt_up(x, y, z_under, m, length):
        """ISO 4017 hex bolt pointing up, head under the metal (top of head at z_under)."""
        h = HD[m]
        return union_all([hexz(x, y, z_under - h['k'], z_under, h['af']), cylz(x, y, z_under, z_under + length, float(m))])

    def head_pocket(x, y, z_under, m):
        """Printed hex pocket that captures a bolt head (anti-rotation only; the clamp is metal to metal)."""
        h = HD[m]
        return hexz(x, y, z_under - h['k'] - 0.3, z_under + 0.01, h['af'] + 2 * S.CLR)

    # ------------------------------------------------------------------ derived positions (common x axis, rev 2 numbers)
    ami = []
    for row, sgn in (('IN', -1), ('OUT', +1)):
        for i in range(S.AMI_SLOTS[row]):
            name, amps = S.AMI_ROWS[row][i]
            y = S.AMI_Y0 + i * S.AMI_PITCH
            x_in = S.BAR['x'] + sgn * S.AMI_IN_OFF
            ami.append(dict(row=row, i=i, name=name, amps=amps, y=y, x_in=x_in, x_out=x_in + sgn * S.AMI['c'], sgn=sgn))
    PD = S.PAD

    def pad_box(a, z0, z1, grow=0.0):
        xa = a['x_out'] - a['sgn'] * PD['inner']
        xb = a['x_out'] + a['sgn'] * PD['outer']
        return box(min(xa, xb) - grow, a['y'] - PD['w'] / 2 - grow, z0, max(xa, xb) + grow, a['y'] + PD['w'] / 2 + grow, z1)

    ACPS_POS = (S.F7_COLS[1], S.F7_ROWS[3])
    f7, micro, mini = [], [], []
    k = 0
    for cx in S.F7_COLS:
        for cy in S.F7_ROWS:
            nm, pn, own = S.F7_POS[k]
            k += 1
            if nm != 'ACPS':
                f7.append((nm, pn, own, cx, cy))
    k = 0
    for cx in S.MICRO_COLS:
        for cy in S.MICRO_Y:
            nm, pn, own = S.MICRO_POS[k]
            k += 1
            micro.append((nm, pn, own, cx, cy))
    for col, (cx, fuses) in S.MINI_COLS.items():
        for i, (nm, amps) in enumerate(fuses):
            mini.append((col, nm, amps, cx, S.MINI_Y0 + i * S.MINI['pitch']))
    SF = S.STRIP_FEED

    def strip_y1(n):
        return S.MINI_Y0 + (n - 1) * S.MINI['pitch'] + 6 + SF['ext']

    # ================================================================== one glove-box box (LOGIC or POWER)
    def build_box(key):
        bx = S.BOXES[key]
        X0, X1 = bx['x0'], bx['x1']
        sh = (bx['place'][0] - X0, bx['place'][1])
        pre = key.capitalize() + '_'
        power = key == 'POWER'
        xi0, xi1, yi0, yi1 = X0 + W, X1 - W, W, D - W
        lid_screws = [(xi0 + 3.2, yi0 + 3.2), (xi1 - 3.2, yi0 + 3.2), (xi0 + 3.2, yi1 - 3.2), (xi1 - 3.2, yi1 - 3.2)]

        def corner(sx, sy):
            return (xi0 if sx < (X0 + X1) / 2 else xi1), (yi0 if sy < D / 2 else yi1)

        # ---- tray (PA12, open top: no trapped powder)
        tray = box(X0, 0, 0, X1, D, S.LID_Z)
        bo(tray, box(xi0, yi0, S.DECK_Z0, xi1, yi1, S.LID_Z + 1), 's')
        bo(tray, box(xi0 + 3, yi0, F, xi1 - 3, yi1 - 3, S.DECK_Z0 + 0.01), 's')    # cable bay: 3 mm deck ledges ends + rear
        we = S.WIRE_EXIT
        bo(tray, box(X0 + 10, -1, we['z0'], X1 - 10, W + 1, we['z1']), 's')         # forward wire exit (grommet strip)
        if power:
            bo(tray, cyl((X1 - W - 1, S.IN_STUD_Y, gz), (X1 + 1, S.IN_STUD_Y, gz), S.IN_GROMMET['d']), 's')   # 1/0 entry
        for (sx, sy) in lid_screws:                                                  # r7 corner bosses, M3 heat-set insert
            cx, cy = corner(sx, sy)
            bo(tray, bo(cylz(cx, cy, F, S.LID_Z, 14.0), box(xi0, yi0, F, xi1, yi1, S.LID_Z), 'i'), 'u')
            bo(tray, cylz(sx, sy, S.LID_Z - IN3['depth'], S.LID_Z + 1, IN3['hole']), 's')
        for (px, py) in bx['posts']:                                                 # deck posts, M3 insert on top
            bo(tray, cylz(px, py, F - 0.01, S.PLATE_Z0, S.POST_D), 'u')
            bo(tray, cylz(px, py, S.PLATE_Z0 - IN3['depth'], S.PLATE_Z0 + 1, IN3['hole']), 's')
        lims = []
        for ex0 in (X0 - E['len'], X1):
            for ey in bx['ears_y']:
                ear = box(ex0, ey - E['w'] / 2, 0, ex0 + E['len'], ey + E['w'] / 2, E['t'])
                for gy in (ey - E['w'] / 2, ey + E['w'] / 2 - S.RIB):                   # gussets back to the wall
                    bo(ear, box(ex0, gy, 0, ex0 + E['len'], gy + S.RIB, E['gusset_h']), 'u')
                bo(ear, cylz(ex0 + E['len'] / 2, ey, -1, E['gusset_h'] + 1, E['hole']), 's')
                bo(tray, ear, 'u')
                lims.append(bo(cylz(ex0 + E['len'] / 2, ey, 0, l5['l'], l5['od']), cylz(ex0 + E['len'] / 2, ey, -1, l5['l'] + 1, l5['id']), 's'))
        comp(pre + 'Tray_PA12_printed', tray, AP['pa12'], MAT['pa'], sh)

        # ---- lid (PA12, ribbed on top)
        Lw = X1 - X0
        LR = S.LID_RIB
        zt = S.LID_Z + S.LID_T
        lid = box(X0, 0, S.LID_Z, X1, D, zt)
        n = max(1, int(Lw // LR['pitch']))
        for i in range(1, n + 1):
            x = X0 + i * Lw / (n + 1)
            bo(lid, box(x - LR['w'] / 2, 6, zt - 0.01, x + LR['w'] / 2, D - 6, zt + LR['h']), 'u')
        m = int(D // LR['pitch'])
        for j in range(1, m + 1):
            y = j * D / (m + 1)
            bo(lid, box(X0 + 6, y - LR['w'] / 2, zt - 0.01, X1 - 6, y + LR['w'] / 2, zt + LR['h']), 'u')
        for rb in (box(X0 + 6, 6, zt - 0.01, X1 - 6, 6 + LR['w'], zt + LR['h']), box(X0 + 6, D - 6 - LR['w'], zt - 0.01, X1 - 6, D - 6, zt + LR['h']),
                   box(X0 + 6, 6, zt - 0.01, X0 + 6 + LR['w'], D - 6, zt + LR['h']), box(X1 - 6 - LR['w'], 6, zt - 0.01, X1 - 6, D - 6, zt + LR['h'])):
            bo(lid, rb, 'u')                                                          # perimeter rib
        for (sx, sy) in lid_screws:
            bo(lid, cylz(sx, sy, S.LID_Z - 1, S.H + 1, 3.4), 's')
        occs[pre + 'Lid'] = comp(pre + 'Lid_PA12_printed', lid, AP['pa12'], MAT['pa'], sh)
        screws = [union_all([cylz(sx, sy, S.LID_Z - 6, zt, 3.0), cylz(sx, sy, zt, zt + 1.65, 5.5)]) for (sx, sy) in lid_screws]
        occs[pre + 'LidScrew'] = comp(pre + 'LidScrew_M3x8_ISO7380', screws, AP['al'], MAT['ss'], sh)

        B = S.BAR
        # every metal joint is a plain drilled hole + an M5 / M8 hex bolt from below (head captured in the deck) - R76
        bar_bolts = [(a['x_in'], a['y'], 5) for a in ami] + [(B['x'], S.IN_STUD_Y, 8)] if power else []
        pad_bolts = [(a['x_out'], a['y'], 5) for a in ami] if power else []
        # ---- deck (PA12): 8 mm plate + skirt + cavity towers + ribs, open underneath (powder runs out)
        cl = S.PCLR
        dx0, dx1, dy0, dy1 = xi0 + cl, xi1 - cl, yi0 + cl, yi1 - cl
        sk, T = S.SKIRT, S.TOWER
        parts = [box(dx0, dy0, S.PLATE_Z0, dx1, dy1, S.DECK_Z1),
                 box(dx0, dy0, S.DECK_Z0, dx1, dy0 + sk, S.PLATE_Z0 + 0.01), box(dx0, dy1 - sk, S.DECK_Z0, dx1, dy1, S.PLATE_Z0 + 0.01),
                 box(dx0, dy0, S.DECK_Z0, dx0 + sk, dy1, S.PLATE_Z0 + 0.01), box(dx1 - sk, dy0, S.DECK_Z0, dx1, dy1, S.PLATE_Z0 + 0.01)]
        for rx in S.DECK_RIBS_X:
            if dx0 < rx < dx1:
                parts.append(box(rx - S.RIB / 2, dy0, S.DECK_Z0, rx + S.RIB / 2, dy1, S.PLATE_Z0 + 0.01))
        if power:
            parts.append(cbox(ACPS_POS[0], ACPS_POS[1], S.DECK_Z0, S.PLATE_Z0 + 0.01, 6.0 + 3.0 + 2 * T, 4.6 + 2 * T))
            for (nm, pn, own, cx, cy) in f7:
                parts.append(cbox(cx, cy, S.DECK_Z0, S.PLATE_Z0 + 0.01, 17.0 + 2.8 + 2 * T, 17.9 + 3.2 + 2 * T))
            for (bx_, by_, m) in bar_bolts + pad_bolts:   # bosses under the head pockets (the plate alone is too thin)
                parts.append(cylz(bx_, by_, S.PLATE_Z0 - 4.5, S.PLATE_Z0 + 0.01, HD[m]['af'] + 7.0))
        else:
            for col, (cx, fuses) in S.MINI_COLS.items():
                parts.append(box(cx - S.MINI['l'] / 2 - T, S.MINI_Y0 - 6.4 - T, S.DECK_Z0, cx + S.MINI['l'] / 2 + T,
                                 strip_y1(len(fuses)) + 0.4 + T, S.PLATE_Z0 + 0.01))
            for cx in S.MICRO_COLS:
                for cy in S.MICRO_Y:
                    parts.append(cbox(cx, cy, S.DECK_Z0, S.PLATE_Z0 + 0.01, 11.6 + 2 * T, 18.6 + 2 * T))
        deck = union_all(parts)
        cuts = []
        for (sx, sy) in lid_screws:                                                   # clear the corner bosses
            cx, cy = corner(sx, sy)
            cuts.append(cylz(cx, cy, S.DECK_Z0 - 1, S.DECK_Z1 + 1, 14.0 + 2 * cl))
        for (px, py) in bx['posts']:                                                 # deck screws: M3 into the post inserts
            cuts.append(cylz(px, py, S.DECK_Z0 - 1, S.PLATE_Z0, S.POST_D + 2 * cl))
            cuts.append(cylz(px, py, S.PLATE_Z0 - 1, S.DECK_Z1 + 1, 3.4))
            cuts.append(cylz(px, py, S.DECK_Z1 - 3.5, S.DECK_Z1 + 1, 6.5))
        if power:
            cuts.append(box(B['x'] - B['w'] / 2 - S.CLR, B['y0'] - S.CLR, BZ0, B['x'] + B['w'] / 2 + S.CLR, B['y1'] + S.CLR, S.DECK_Z1 + 1))
            for a in ami:
                cuts.append(pad_box(a, PZ0, S.DECK_Z1 + 1, S.CLR))
                xc = (a['x_in'] + a['x_out']) / 2                                     # AMI body relief
                cuts.append(cbox(xc, a['y'], S.BAR_TOP + S.AMI['ear_t'] / 2 - S.AMI['body_h'] / 2 - 0.6, S.DECK_Z1 + 1,
                                 S.AMI['body_l'] + 1, S.AMI['body_w'] + 1))
                cuts.append(cylz(a['x_out'] + a['sgn'] * HOLE_OFF, a['y'], S.DECK_Z0 - 1, S.DECK_Z1 + 1, 9.0))   # wire hole
            cuts += [head_pocket(bx_, by_, BZ0, m) for (bx_, by_, m) in bar_bolts] + [head_pocket(bx_, by_, PZ0, m) for (bx_, by_, m) in pad_bolts]
            for dx in (-3.0, 3.0):
                cuts.append(cbox(ACPS_POS[0] + dx, ACPS_POS[1], S.DECK_Z0 - 1, S.DECK_Z1 + 1, 3.0, 4.6))
            for (nm, pn, own, cx, cy) in f7:      # Mini ISO cavities (F7 bottom view: 30 / 87 blades along x, 85 / 86 along y)
                pins = [(0, 7.65, 11.5, 3.2), (0, -10.25, 11.5, 3.2), (-8.45, -0.25, 2.8, 8.3), (8.45, -0.25, 2.8, 8.3)]
                if nm == S.RELAY_B['pos']:        # Power Relay B 1 form C: 87a (6.3 blade, across) between 85 and 86
                    pins.append((0, S.RELAY_B['v87a'], 8.3, 2.8))
                for (u, v, lx, ly) in pins:
                    cuts.append(cbox(cx + u, cy + v, S.DECK_Z0 - 1, S.DECK_Z1 + 1, lx, ly))
        else:
            for (col, nm, amps, cx, y) in mini:   # 2 x 2.8 mm receptacles per mini fuse
                for dx in (-3.0, 3.0):
                    cuts.append(cbox(cx + dx, y, S.DECK_Z0 - 1, S.DECK_Z1 + 1, 3.0, 4.6))
            for (nm, pn, own, cx, cy) in micro:   # approximate pattern from TE 1308028; set exactly in detail work
                for (u, v, lx, ly) in ((0, 8.0, 8.3, 2.6), (0, -8.0, 8.3, 2.6), (-4.5, 0, 2.6, 6.8), (4.5, 0, 2.6, 6.8), (0, 0, 2.6, 4.0)):
                    cuts.append(cbox(cx + u, cy + v, S.DECK_Z0 - 1, S.DECK_Z1 + 1, lx, ly))
            for col, (cx, fuses) in S.MINI_COLS.items():
                y1 = strip_y1(len(fuses))         # strip pocket, open underneath (strips slide in from below)
                ST = S.STRIP
                cuts.append(box(cx - ST['w'] / 2 - S.CLR, S.MINI_Y0 - 6 - S.CLR, S.DECK_Z0 - 1, cx + ST['w'] / 2 + S.CLR, y1 + S.CLR, ST['z1'] + S.CLR))
                yh = y1 - SF['hole_from_end']     # feed lug under the strip end: trough open to the cable bay
                cuts.append(box(cx - LUG['b'] / 2 - 1, yh - LUG['b'] / 2 - 1, S.DECK_Z0 - 1, cx + LUG['b'] / 2 + 1, y1 + 14.0, ST['z1'] - ST['t'] + 0.01))
                h5 = HD[5]                        # feed bolt head sits ABOVE the strip end, captured in a hex pocket in the deck
                cuts.append(hexz(cx, yh, ST['z1'] - 0.01, ST['z1'] + h5['k'] + 0.3, h5['af'] + 2 * S.CLR))
        sub_all(deck, cuts)
        comp(pre + 'Deck_PA12_printed', deck, AP['pa12_lt'], MAT['pa'], sh)

        # ---- conductors + hardware
        lugs, wires = [], []
        if power:
            bar = box(B['x'] - B['w'] / 2, B['y0'], BZ0, B['x'] + B['w'] / 2, B['y1'], S.BAR_TOP)      # plain cut + drilled flat bar
            bo(bar, cylz(B['x'], S.IN_STUD_Y, BZ0 - 1, S.BAR_TOP + 1, 8.5), 's')
            pads = []
            for a in ami:
                bo(bar, cylz(a['x_in'], a['y'], BZ0 - 1, S.BAR_TOP + 1, 5.5), 's')
                p = pad_box(a, PZ0, S.BAR_TOP)    # plain cut piece of 3 x 15 stock, one 5.5 hole
                bo(p, cylz(a['x_out'], a['y'], PZ0 - 1, S.BAR_TOP + 1, 5.5), 's')
                pads.append(p)
            comp(pre + 'Bar_Power_%s_25x6p35' % BM['name'], bar, AP_BAR, MAT_BAR, sh)
            comp(pre + 'Pad_Out_%s_15x3' % BM['name'], pads, AP_BAR, MAT_BAR, sh)
            z_ear = S.BAR_TOP + S.AMI['ear_t']
            studs = [bolt_up(a['x_in'], a['y'], BZ0, 5, 16.0) for a in ami] + [bolt_up(a['x_out'], a['y'], PZ0, 5, 16.0) for a in ami]
            studs.append(bolt_up(B['x'], S.IN_STUD_Y, BZ0, 8, 20.0))
            nuts = [hexz(a['x_in'], a['y'], z_ear, z_ear + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami]
            for a in ami:
                zn = z_ear + (LUG['t'] if a['amps'] else 0.0)
                nuts.append(hexz(a['x_out'], a['y'], zn, zn + S.M5_NUT['h'], S.M5_NUT['af']))
            nuts.append(hexz(B['x'], S.IN_STUD_Y, S.BAR_TOP + M8['t'], S.BAR_TOP + M8['t'] + S.M8_NUT['h'], S.M8_NUT['af']))
            comp(pre + 'Bolt_M5x16_M8x20_ISO4017_A2', studs, AP['al'], MAT['ss'], sh)
            comp(pre + 'Nut_Keps_M5_M8_A2', nuts, AP['al'], MAT['ss'], sh)
            for a in ami:                         # Klauke 2R5 output lugs on top of the fuse ear, wire down through the deck
                if a['amps'] is None:
                    continue
                t, e = ring_lug(a['x_out'], a['y'], z_ear, LUG['b'], 5.5, LUG['t'], LUG['d4'], (a['sgn'], 'x'), LUG['l'] - LUG['tip'])
                lugs.append(t)
                xh = a['x_out'] + a['sgn'] * HOLE_OFF
                w_ = cyl(e, (xh, a['y'], e[2]), WIRE_D)
                bo(w_, cylz(xh, a['y'], S.DECK_Z0 - 8, e[2], WIRE_D), 'u')
                bo(w_, tb.createSphere(P(xh, a['y'], e[2]), WIRE_D / 20.0), 'u')
                wires.append(w_)
            t, e = ring_lug(B['x'], S.IN_STUD_Y, S.BAR_TOP, M8['b'], 8.4, M8['t'], M8['d4'], (1, 'x'), M8['l'] - M8['tip'], barrel=19.0)
            lugs.append(t)                        # 1/0 input lug (Klauke 6R8) on top of the bar
            comp(pre + 'Cable_1-0_input', cyl(e, (X1 + 25, S.IN_STUD_Y, e[2]), 13.0), AP['black'], None, sh)
            comp(pre + 'Grommet_1-0', bo(cyl((X1 - W - 2, S.IN_STUD_Y, gz), (X1 + 2, S.IN_STUD_Y, gz), S.IN_GROMMET['d']),
                                         cyl((X1 - W - 3, S.IN_STUD_Y, gz), (X1 + 3, S.IN_STUD_Y, gz), 13.0), 's'), AP['black'], None, sh)
            by_col = {}
            for a in ami:
                if a['amps'] is None:
                    continue
                xa, xb = sorted((a['x_in'], a['x_out']))
                ear = slot_x(xa, xb, a['y'], S.BAR_TOP, S.BAR_TOP + S.AMI['ear_t'], S.AMI['ear_w'])
                for x in (xa, xb):
                    bo(ear, cylz(x, a['y'], S.BAR_TOP - 1, S.BAR_TOP + 2, S.AMI['hole']), 's')
                zc = S.BAR_TOP + S.AMI['ear_t'] / 2
                body = cbox((xa + xb) / 2, a['y'], zc - S.AMI['body_h'] / 2, zc + S.AMI['body_h'] / 2, S.AMI['body_l'], S.AMI['body_w'])
                bo(body, ear, 'u')
                by_col.setdefault(S.AMI_COLOUR[a['amps']], []).append(body)
            for colr, bodies in by_col.items():
                comp(pre + 'Fuse_AMI_%s' % colr, bodies, AP[colr], MAT['abs'], sh)
            comp(pre + 'Fuse_ATM_10A', cbox(ACPS_POS[0], ACPS_POS[1], S.DECK_Z1, S.DECK_Z1 + S.MINI['h_above'], S.MINI['l'], S.MINI['w']), MINI_AP[10], MAT['abs'], sh)
            RBd = S.RELAY_B
            comp(pre + 'Relay_TE_F7_V23134', [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + S.F7['h'], S.F7['body'], S.F7['body'])
                                               for (nm, pn, own, cx, cy) in f7 if pn and nm != RBd['pos']], AP['black'], MAT['abs'], sh)
            comp(pre + 'Relay_TE_PowerB_V23234_CO', [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + RBd['h'], RBd['body'], RBd['body'])
                                                      for (nm, pn, own, cx, cy) in f7 if nm == RBd['pos']], AP['black'], MAT['abs'], sh)
            comp(pre + 'SPARE_positions', [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + 1.0, S.F7['body'], S.F7['body'])
                                           for (nm, pn, own, cx, cy) in f7 if not pn], AP['spare'], None, sh)
        else:
            strips, fscrews = [], []
            for col, (cx, fuses) in S.MINI_COLS.items():
                y1 = strip_y1(len(fuses))
                yh = y1 - SF['hole_from_end']
                ST = S.STRIP
                zs0 = ST['z1'] - ST['t']
                st = box(cx - ST['w'] / 2, S.MINI_Y0 - 6, zs0, cx + ST['w'] / 2, y1, ST['z1'])      # plain cut 10 x 3 strip
                bo(st, cylz(cx, yh, zs0 - 1, ST['z1'] + 1, 5.5), 's')
                strips.append(st)
                # feed lug (Klauke 2R5) under the strip, barrel to the rear, wire drops into the cable bay
                t, e = ring_lug(cx, yh, zs0 - LUG['t'], LUG['b'], 5.5, LUG['t'], LUG['d4'], (1, 'y'), LUG['l'] - LUG['tip'], down=True)
                lugs.append(t)
                w_ = cyl(e, (cx, e[1] + 4, e[2]), WIRE_D)
                bo(w_, cylz(cx, e[1] + 4, S.DECK_Z0 - 10, e[2], WIRE_D), 'u')
                bo(w_, tb.createSphere(P(cx, e[1] + 4, e[2]), WIRE_D / 20.0), 'u')
                wires.append(w_)
                zn = zs0 - LUG['t']               # M5 x 16 bolt down: head above the strip, nut under the lug
                fscrews.append(union_all([hexz(cx, yh, ST['z1'], ST['z1'] + HD[5]['k'], HD[5]['af']), cylz(cx, yh, ST['z1'] - 16.0, ST['z1'], 5.0),
                                          hexz(cx, yh, zn - S.M5_NUT['h'], zn, S.M5_NUT['af'])]))
            comp(pre + 'Strip_Logic_%s_10x3' % BM['name'], strips, AP_BAR, MAT_BAR, sh)
            comp(pre + 'FeedBolt_M5x16_ISO4017_nut', fscrews, AP['al'], MAT['ss'], sh)
            by_amp = {}
            for (col, nm, amps, cx, y) in mini:
                if amps is not None:
                    by_amp.setdefault(amps, []).append(cbox(cx, y, S.DECK_Z1, S.DECK_Z1 + S.MINI['h_above'], S.MINI['l'], S.MINI['w']))
            for amps, bodies in by_amp.items():
                comp(pre + 'Fuse_ATM_%sA' % str(amps).replace('.', 'p'), bodies, MINI_AP[amps], MAT['abs'], sh)
            comp(pre + 'Relay_TE_MicroA_V23074', [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + S.MICRO['h'], S.MICRO['x'], S.MICRO['y'])
                                                   for (nm, pn, own, cx, cy) in micro if pn], AP['black'], MAT['abs'], sh)
            comp(pre + 'SPARE_positions', [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + 1.0, S.MICRO['x'], S.MICRO['y'])
                                           for (nm, pn, own, cx, cy) in micro if not pn], AP['spare'], None, sh)
        comp(pre + 'Limiter_brass', lims, AP['brass'], MAT['brass'], sh)
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_stub', wires, AP['wire'], None, sh)

    # ================================================================== battery relay block (trunk): HCR150 + AMI 40 fuse
    def build_relay_block():
        R, H_ = S.RB, S.HCR
        pre = 'BattRelay_'
        sh = R['place']
        Lr, Dr, fl, wl, LZ = R['L'], R['D'], R['floor'], R['wall'], R['lid_z']
        xi0, xi1, yi0, yi1 = wl, Lr - wl, wl, Dr - wl
        rx, ry = R['relay_xy']
        ty = ry - H_['body_y'] / 2                     # terminal edge of the relay body
        fy = ty + H_['hole_z']                          # flange hole line
        hxs = (rx - H_['holes'] / 2, rx + H_['holes'] / 2)
        Bb = R['bar']
        bz0, bz1 = Bb['z0'], Bb['z0'] + Bb['t']
        ami_in, ami_out = R['ami_in_y'], R['ami_in_y'] + S.AMI['c']
        tz0, tz1 = R['term_z']
        txs = (rx - H_['term_pitch'] / 2, rx + H_['term_pitch'] / 2)   # terminal 3 (fused feed), terminal 5 (pump)
        tsy = ty - H_['term_to'] / 2                    # M6 screw centre on the terminal blocks
        lid_screws = [(xi0 + 3.2, yi0 + 3.2), (xi1 - 3.2, yi0 + 3.2), (xi0 + 3.2, yi1 - 3.2), (xi1 - 3.2, yi1 - 3.2)]
        lims = []
        # ---- tray: floor + walls + ribs under the bar and pad + lid bosses + ears + grommet holes
        tray = box(0, 0, 0, Lr, Dr, LZ)
        bo(tray, box(xi0, yi0, fl, xi1, yi1, LZ + 1), 's')
        for (sx, sy) in lid_screws:
            cx = xi0 if sx < Lr / 2 else xi1
            cy = yi0 if sy < Dr / 2 else yi1
            bo(tray, bo(cylz(cx, cy, fl - 0.01, LZ, 14.0), box(xi0, yi0, 0, xi1, yi1, LZ), 'i'), 'u')
            bo(tray, cylz(sx, sy, LZ - IN3['depth'], LZ + 1, IN3['hole']), 's')
        pz0 = bz1 - S.PAD['t']                          # pad (3 mm stock) top level with the bar top
        ped_y1 = ami_out + S.PAD['outer']
        nr = R['pedestal_ribs']
        for k_ in range(nr):
            x = Bb['x'] - Bb['w'] / 2 + 1.25 + k_ * (Bb['w'] - 2.5) / (nr - 1)
            bo(tray, box(x - S.RIB / 2, Bb['y0'], fl - 0.01, x + S.RIB / 2, Bb['y1'], bz0), 'u')
            bo(tray, box(x - S.RIB / 2, ami_out - S.PAD['inner'], fl - 0.01, x + S.RIB / 2, ped_y1, pz0), 'u')
        rb_bolts = [(Bb['x'], R['in_stud_y'], 6, bz0), (Bb['x'], ami_in, 5, bz0), (Bb['x'], ami_out, 5, pz0)]
        for (px, py, m, zu) in rb_bolts:                # bolt bosses: hex head captured, bolt up through the copper
            bo(tray, cylz(px, py, fl - 0.01, zu, HD[m]['af'] + 6.0), 'u')
            bo(tray, head_pocket(px, py, zu, m), 's')
        LM = R['lim_m6']
        for x in hxs:                                   # relay flange bolts: M6 through the flange + a brass limiter into the trunk floor
            bo(tray, cylz(x, fy, -1, fl + 1, LM['od'] + 2 * S.CLR), 's')
            lims.append(bo(cylz(x, fy, 0, fl, LM['od']), cylz(x, fy, -1, fl + 1, LM['id']), 's'))
        for ey in R['ears_y']:                          # two ears at the fuse end
            ear = box(-E['len'], ey - E['w'] / 2, 0, 0.01, ey + E['w'] / 2, E['t'])
            for gy in (ey - E['w'] / 2, ey + E['w'] / 2 - S.RIB):
                bo(ear, box(-E['len'], gy, 0, 0.01, gy + S.RIB, E['gusset_h']), 'u')
            bo(ear, cylz(-E['len'] / 2, ey, -1, E['gusset_h'] + 1, E['hole']), 's')
            bo(tray, ear, 'u')
            lims.append(bo(cylz(-E['len'] / 2, ey, 0, l5['l'], l5['od']), cylz(-E['len'] / 2, ey, -1, l5['l'] + 1, l5['id']), 's'))
        gin_z = bz1 + 5.0
        bo(tray, cyl((-1, R['in_stud_y'], gin_z), (wl + 1, R['in_stud_y'], gin_z), 16.0), 's')       # battery feed in (end wall)
        gout = (txs[1], tz1 + 6.0)
        bo(tray, cyl((gout[0], -1, gout[1]), (gout[0], wl + 1, gout[1]), 14.0), 's')             # pump feed out (front wall)
        gcoil = (rx - H_['body_x'] / 2 + 8.0, tz0 + 4.5)
        bo(tray, cyl((gcoil[0], -1, gcoil[1]), (gcoil[0], wl + 1, gcoil[1]), 10.0), 's')           # coil lead (Link Aux 3) out
        comp(pre + 'Tray_PA12_printed', tray, AP['pa12'], MAT['pa'], sh)
        # ---- lid
        LR = S.LID_RIB
        zt = LZ + S.LID_T
        lid = box(0, 0, LZ, Lr, Dr, zt)
        for x in (Lr / 3, 2 * Lr / 3):
            bo(lid, box(x - LR['w'] / 2, 6, zt - 0.01, x + LR['w'] / 2, Dr - 6, zt + LR['h']), 'u')
        bo(lid, box(6, Dr / 2 - LR['w'] / 2, zt - 0.01, Lr - 6, Dr / 2 + LR['w'] / 2, zt + LR['h']), 'u')
        for rb in (box(6, 6, zt - 0.01, Lr - 6, 6 + LR['w'], zt + LR['h']), box(6, Dr - 6 - LR['w'], zt - 0.01, Lr - 6, Dr - 6, zt + LR['h']),
                   box(6, 6, zt - 0.01, 6 + LR['w'], Dr - 6, zt + LR['h']), box(Lr - 6 - LR['w'], 6, zt - 0.01, Lr - 6, Dr - 6, zt + LR['h'])):
            bo(lid, rb, 'u')
        for (sx, sy) in lid_screws:
            bo(lid, cylz(sx, sy, LZ - 1, zt + LR['h'] + 1, 3.4), 's')
        occs[pre + 'Lid'] = comp(pre + 'Lid_PA12_printed', lid, AP['pa12'], MAT['pa'], sh)
        occs[pre + 'LidScrew'] = comp(pre + 'LidScrew_M3x8_ISO7380', [union_all([cylz(sx, sy, LZ - 6, zt, 3.0), cylz(sx, sy, zt, zt + 1.65, 5.5)])
                                                                       for (sx, sy) in lid_screws], AP['al'], MAT['ss'], sh)
        # ---- HCR150 envelope from the TE drawing: body on its flange face, two M6 terminal blocks, coil plug
        rel = box(rx - H_['body_x'] / 2, ty, fl, rx + H_['body_x'] / 2, ty + H_['body_y'], fl + H_['depth'])
        flg = box(hxs[0] - 8.0, fy - 9.0, fl, hxs[1] + 8.0, fy + 9.0, fl + H_['flange_t'])
        for x in hxs:
            bo(flg, cylz(x, fy, fl - 1, fl + H_['flange_t'] + 1, H_['hole_d']), 's')
        bo(rel, flg, 'u')
        for x in txs:
            tbk = box(x - H_['term_w'] / 2, ty - H_['term_to'], tz0, x + H_['term_w'] / 2, ty + 0.01, tz1)
            bo(tbk, cylz(x, tsy, tz1 - 8.0, tz1 + 0.1, 5.0), 's')
            bo(rel, tbk, 'u')
        bo(rel, box(gcoil[0] - 5.0, ty - H_['plug_to'], tz0, gcoil[0] + 5.0, ty + 0.01, tz0 + 9.0), 'u')    # Superseal 1.5 2-pole plug
        comp(pre + 'Relay_TE_HCR150_1416010-1', rel, AP['black'], MAT['abs'], sh)
        # ---- bar + pad + AMI 40 + studs, nuts
        bar = box(Bb['x'] - Bb['w'] / 2, Bb['y0'], bz0, Bb['x'] + Bb['w'] / 2, Bb['y1'], bz1)       # plain cut + drilled
        bo(bar, cylz(Bb['x'], R['in_stud_y'], bz0 - 1, bz1 + 1, 6.5), 's')
        bo(bar, cylz(Bb['x'], ami_in, bz0 - 1, bz1 + 1, 5.5), 's')
        pad = box(Bb['x'] - S.PAD['w'] / 2, ami_out - S.PAD['inner'], pz0, Bb['x'] + S.PAD['w'] / 2, ped_y1, bz1)
        bo(pad, cylz(Bb['x'], ami_out, pz0 - 1, bz1 + 1, 5.5), 's')
        comp(pre + 'Bar_Power_%s_25x6p35' % BM['name'], bar, AP_BAR, MAT_BAR, sh)
        comp(pre + 'Pad_Out_%s_15x3' % BM['name'], pad, AP_BAR, MAT_BAR, sh)
        fe = slot_y(Bb['x'], ami_in, ami_out, bz1, bz1 + S.AMI['ear_t'], S.AMI['ear_w'])
        for y in (ami_in, ami_out):
            bo(fe, cylz(Bb['x'], y, bz1 - 1, bz1 + 2, S.AMI['hole']), 's')
        ze = bz1 + S.AMI['ear_t'] / 2
        fb = cbox(Bb['x'], (ami_in + ami_out) / 2, ze - S.AMI['body_h'] / 2, ze + S.AMI['body_h'] / 2, S.AMI['body_w'], S.AMI['body_l'])
        bo(fb, fe, 'u')
        comp(pre + 'Fuse_AMI_ltgreen', fb, AP['ltgreen'], MAT['abs'], sh)
        lug_z = bz1 + S.AMI['ear_t']
        studs = [bolt_up(px, py, zu, m, {5: 16.0, 6: 16.0}[m]) for (px, py, m, zu) in rb_bolts]
        nuts = [hexz(Bb['x'], ami_in, lug_z, lug_z + S.M5_NUT['h'], S.M5_NUT['af']),
                hexz(Bb['x'], ami_out, lug_z + 2.0, lug_z + 2.0 + S.M5_NUT['h'], S.M5_NUT['af']),
                hexz(Bb['x'], R['in_stud_y'], bz1 + 2.0, bz1 + 2.0 + 5.2, 10.0)]
        comp(pre + 'Bolt_M5x16_M6x16_ISO4017_A2', studs, AP['al'], MAT['ss'], sh)
        comp(pre + 'Nut_Keps_M5_M6_A2', nuts, AP['al'], MAT['ss'], sh)
        comp(pre + 'Limiter_brass', lims, AP['brass'], MAT['brass'], sh)
        # ---- lugs + wire stubs: battery feed in (end wall), AMI out -> relay 3, relay 5 -> pump (front wall)
        lugs, wires = [], []
        t, e = ring_lug(Bb['x'], R['in_stud_y'], bz1, 13.0, 6.5, 2.0, 8.5, (-1, 'x'), 17.0)
        lugs.append(t)
        wires.append(cyl(e, (-25.0, e[1], e[2]), 9.0))
        t, e = ring_lug(Bb['x'], ami_out, lug_z, 12.0, 5.5, 2.0, 7.0, (1, 'x'), 16.0)
        lugs.append(t)
        tr, er = ring_lug(txs[0], tsy, tz1, 12.0, 6.5, 2.0, 7.0, (-1, 'x'), 14.0)
        lugs.append(tr)
        w_ = cyl(e, (e[0] + 6, e[1], e[2]), WIRE_D)
        for p0, p1 in ((( e[0] + 6, e[1], e[2]), (e[0] + 6, er[1], e[2])), ((e[0] + 6, er[1], e[2]), (e[0] + 6, er[1], er[2])), ((e[0] + 6, er[1], er[2]), er)):
            bo(w_, tb.createSphere(P(*p0), WIRE_D / 20.0), 'u')
            bo(w_, cyl(p0, p1, WIRE_D), 'u')
        wires.append(w_)
        t, e2 = ring_lug(txs[1], tsy, tz1, 12.0, 6.5, 2.0, 7.0, (-1, 'y'), 14.0)
        lugs.append(t)
        wires.append(cyl(e2, (e2[0], -25.0, e2[2]), WIRE_D))
        comp(pre + 'Lug_Klauke', lugs, AP['cu'], None, sh)
        comp(pre + 'Wire_stub', wires, AP['wire'], None, sh)

    build_box('LOGIC')
    build_box('POWER')
    build_relay_block()

    # ------------------------------------------------------------------ checks
    mm = app.measureManager

    def dist(b1, b2):
        return round(mm.measureMinimumDistance(b1, b2).value * 10, 2)

    def bodies(prefix):
        return [b for o in root.occurrences if o.component.name.startswith(prefix) for b in o.bRepBodies]

    def short(n):
        return n.split('_', 1)[1]

    bar_b = bodies('Power_Bar_')[0]
    pad_bs = bodies('Power_Pad_')
    pad_by_pos = {}
    for pb in pad_bs:
        c = pb.boundingBox
        pad_by_pos[(round((c.minPoint.x + c.maxPoint.x) * 5), round((c.minPoint.y + c.maxPoint.y) * 5))] = pb
    keys = sorted(pad_by_pos)
    neigh = [dist(pad_by_pos[k1], pad_by_pos[k2]) for k1 in keys for k2 in keys
             if k1 < k2 and abs(k1[0] - k2[0]) < 5 and abs(abs(k1[1] - k2[1]) - S.AMI_PITCH) < 1]
    lug_bs = bodies('Power_Lug_')
    in_lug = max(lug_bs, key=lambda lb: lb.volume)
    out_lugs = [lb for lb in lug_bs if lb is not in_lug]
    sb = bodies('Logic_Strip_')
    rb_lugs = bodies('BattRelay_Lug_')
    report['live_clearance'] = {
        'pad_to_pad_min_mm': min(neigh),
        'bar_to_pad_min_mm': min(dist(bar_b, pb) for pb in pad_bs),
        'input_lug_to_pad_min_mm': min(dist(in_lug, pb) for pb in pad_bs),
        'output_lug_to_lug_min_mm': min(dist(l1, l2) for i_, l1 in enumerate(out_lugs) for l2 in out_lugs[i_ + 1:]
                                        if abs(l1.boundingBox.minPoint.x - l2.boundingBox.minPoint.x) < 0.5),
        'logic_strip_to_strip_mm': dist(sb[0], sb[1]),
        'battrelay_bar_to_pad_mm': dist(bodies('BattRelay_Bar_')[0], bodies('BattRelay_Pad_')[0]),
        'battrelay_relay_lug_to_lug_mm': dist(rb_lugs[2], rb_lugs[3]),
    }
    printed = {}
    for o in root.occurrences:
        n = o.component.name
        if n.endswith('_printed'):
            bbs = [b.boundingBox for b in o.bRepBodies]
            lo = [min(getattr(q.minPoint, k) for q in bbs) for k in 'xyz']
            hi = [max(getattr(q.maxPoint, k) for q in bbs) for k in 'xyz']
            vol = sum(b.volume for b in o.bRepBodies)
            printed[n] = dict(size_mm=[round((hi[i] - lo[i]) * 10, 1) for i in range(3)],
                              volume_cm3=round(vol, 1), mass_g_pa12=round(vol * 1.01, 0))
    report['printed_parts'] = printed
    report['boxes_mm'] = {k: dict(L=b['x1'] - b['x0'], D=S.D, H=S.H, L_with_ears=b['x1'] - b['x0'] + 2 * E['len'])
                          for k, b in S.BOXES.items()}
    report['boxes_mm']['BATTRELAY'] = dict(L=S.RB['L'], D=S.RB['D'], H=S.RB['lid_z'] + S.LID_T + S.LID_RIB['h'], L_with_ears=S.RB['L'] + E['len'])
    report['footprint_mm2'] = {k: round(v['L'] * v['D'], 0) for k, v in report['boxes_mm'].items()}
    report['bar_metal'] = S.BAR_METAL
    coll = adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        if not short(o.component.name).startswith(('Wire_', 'Cable_', 'Grommet_', 'LidScrew', 'Bolt_', 'Nut_', 'Lug_', 'FeedBolt_')):
            coll.add(o)
    try:
        ir = design.analyzeInterference(design.createInterferenceInput(coll))
        report['interference'] = [(r.entityOne.parentComponent.name if hasattr(r.entityOne, 'parentComponent') else str(r.entityOne),
                                   r.entityTwo.parentComponent.name if hasattr(r.entityTwo, 'parentComponent') else str(r.entityTwo),
                                   round(r.interferenceBody.volume * 1000, 3)) for r in ir]
    except Exception as ex:   # report, do not hide
        report['interference_error'] = str(ex)
    report['mass_g'] = {o.component.name: round(o.component.physicalProperties.mass * 1000, 1) for o in root.occurrences
                        if short(o.component.name).startswith(('Bar', 'Pad', 'Strip'))}

    # ------------------------------------------------------------------ exports
    em = design.exportManager
    exported = []
    for o in root.occurrences:
        n = o.component.name
        if n.endswith('_printed') or short(n).startswith(('Bar_', 'Pad_', 'Strip_')):
            p = os.path.join(out_dir, '%s.step' % n)
            em.execute(em.createSTEPExportOptions(p, o.component))
            exported.append(os.path.basename(p))
        if n.endswith('_printed'):
            p = os.path.join(out_dir, '%s.stl' % n)
            so = em.createSTLExportOptions(o, p)
            so.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(so)
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

    def shot(fn, orient=None, eye=None, target=(200.0, 10.0, 30.0)):
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

    shot('fusebox_render_iso_closed.png', eye=(-300, -480, 380))
    for o in occs.values():
        o.isLightBulbOn = False
    shot('fusebox_render_iso_open.png', eye=(-300, -480, 380))
    shot('fusebox_render_iso_open_rear.png', eye=(320, 480, 380))
    shot('fusebox_render_top_open.png', VO.TopViewOrientation)
    vis = {}
    for o in root.occurrences:                       # the battery relay block alone
        vis[o.entityToken] = o.isLightBulbOn
        if not o.component.name.startswith('BattRelay_'):
            o.isLightBulbOn = False
    shot('battrelay_render_iso_open.png', eye=(-170, -260, 230), target=(75.0, -115.0, 20.0))
    for o in root.occurrences:
        o.isLightBulbOn = vis[o.entityToken]
    for o in occs.values():
        o.isLightBulbOn = True

    try:
        if doc.dataFile.name != DOC:
            doc.dataFile.name = DOC
            report['renamed_document_to'] = DOC
    except Exception as ex:   # report, do not hide
        report['rename_error'] = str(ex)
    doc.save('rev 3.1: tinned copper flat-bar stock, bolts from below (Claude Code 2026-10-14)')
    with open(os.path.join(out_dir, 'fusebox_report.json'), 'w') as f:
        json.dump(report, f, indent=1)
    return report
