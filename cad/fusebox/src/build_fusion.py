"""Build the ST185 glove-box fuse + relay box in a new Fusion document, export every part, render, check isolation.
Run inside Fusion (Fusion MCP script runner):  build(out_dir)
Same toolkit as cad/busbar/src/build_fusion.py (TemporaryBRepManager bodies, one component per part, all
instances placed in the root - never via proxy transform overrides). Claude Code, 2026-10-14.
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
DOC = 'ST185_fusebox_rev1'


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


def union_all(bodies):
    b0 = bodies[0]
    for b in bodies[1:]:
        bo(b0, b, 'u')
    return b0


def sub_all(target, tools):
    for t in tools:
        bo(target, t, 's')
    return target


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
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
        'al': ap('Aluminum - Satin'), 'al_bar': ap('Aluminum - Brushed Linear'), 'deck': ap('Plastic - Matte (Gray)'),
        'black': ap('Plastic - Matte (Black)'), 'brass': ap('Brass - Matte'), 'cu': ap('Copper - Raw'),
        'white': ap('Plastic - Matte (White)'), 'wire': ap('Plastic - Glossy (Red)'),
        'orange': tint('Plastic - Glossy (Red)', 'AMI orange', (240, 120, 20)),
        'ltgreen': tint('Plastic - Glossy (Green)', 'AMI lt green', (130, 220, 120)),
        'red': ap('Plastic - Glossy (Red)'), 'yellow': ap('Plastic - Glossy (Yellow)'),
        'nylon': tint('Plastic - Matte (White)', 'Nylon natural', (235, 228, 205)),
        'spare': tint('Plastic - Matte (Gray)', 'Spare position', (200, 200, 200)),
    }
    MINI_AP = {2: tint('Plastic - Glossy (Grey)', 'ATM 2A grey', (150, 150, 150)), 5: tint('Plastic - Glossy (Red)', 'ATM 5A tan', (205, 170, 120)),
               7.5: tint('Plastic - Glossy (Red)', 'ATM 7.5A brown', (120, 70, 40)), 10: ap('Plastic - Glossy (Red)'),
               15: ap('Plastic - Glossy (Blue)'), 20: ap('Plastic - Glossy (Yellow)')}
    MAT = {'al': mlib.materials.itemByName('Aluminum 6061'), 'pa': mlib.materials.itemByName('Nylon 6/6'),
           'ss': mlib.materials.itemByName('Stainless Steel AISI 304'), 'abs': mlib.materials.itemByName('ABS Plastic')}

    def comp(cname, bodies, appearance=None, material=None):
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c = occ.component
        c.name = cname
        for b in (bodies if isinstance(bodies, list) else [bodies]):
            bb = c.bRepBodies.add(b)
            bb.name = cname
            if appearance is not None:
                bb.appearance = appearance
        if material is not None:
            c.material = material
        return occ

    W, F = S.WALL, S.FLOOR
    L, D = S.L, S.D
    xi0, xi1, yi0, yi1 = W, L - W, W, D - W           # inner pocket
    BZ0 = S.BAR_TOP - S.BAR_T                          # 47: bar / pad underside

    # ------------------------------------------------------------------ derived positions
    ami = []    # dict(row, i, name, amps, y, x_in, x_out, sgn)
    for row, sgn in (('IN', -1), ('OUT', +1)):
        for i in range(S.AMI_SLOTS[row]):
            name, amps = S.AMI_ROWS[row][i]
            y = S.AMI_Y0 + i * S.AMI_PITCH
            x_in = S.BAR['x'] + sgn * S.AMI_IN_OFF
            ami.append(dict(row=row, i=i, name=name, amps=amps, y=y, x_in=x_in, x_out=x_in + sgn * S.AMI['c'], sgn=sgn))
    LUG = S.LUG_M5
    HOLE_OFF = 15.0          # wire hole through the deck, from the output stud, away from the bar
    WIRE_D = 6.0

    def lug_end(a):          # barrel end x
        return a['x_out'] + a['sgn'] * (LUG['l'] - LUG['tip'])

    # ------------------------------------------------------------------ 1. tray (6061, machined)
    tray = box(0, 0, 0, L, D, S.LID_Z)
    bo(tray, box(xi0, yi0, S.DECK_Z0, xi1, yi1, S.LID_Z + 1), 's')                  # upper pocket: full inner
    bo(tray, box(xi0 + 3, yi0, F, xi1 - 3, yi1 - 3, S.DECK_Z0 + 0.01), 's')         # cable bay: 3 mm deck ledges ends + rear
    we = S.WIRE_EXIT
    bo(tray, box(we['x0'], -1, we['z0'], we['x1'], W + 1, we['z1']), 's')           # forward wire exit (grommet strip)
    gz = S.BAR_TOP - S.LUG_M8['t'] + S.LUG_M8['d4'] / 2
    bo(tray, cyl((L - W - 1, S.IN_STUD_Y, gz), (L + 1, S.IN_STUD_Y, gz), S.IN_GROMMET['d']), 's')   # 1/0 entry
    for (sx, sy) in S.LID_SCREWS:                                                     # r7 corner bosses, M3 tapped
        cx = xi0 if sx < L / 2 else xi1
        cy = yi0 if sy < D / 2 else yi1
        boss = bo(cylz(cx, cy, F, S.LID_Z, 14.0), box(xi0, yi0, F, xi1, yi1, S.LID_Z), 'i')
        bo(tray, boss, 'u')
        bo(tray, cylz(sx, sy, S.LID_Z - 10, S.LID_Z + 1, 2.5), 's')
    E = S.EAR
    for ex0 in (-E['len'], L):
        for ey in E['ys']:
            ear = box(ex0, ey - E['w'] / 2, 0, ex0 + E['len'], ey + E['w'] / 2, E['t'])
            bo(ear, cylz(ex0 + E['len'] / 2 if ex0 > 0 else -E['len'] / 2, ey, -1, E['t'] + 1, E['hole']), 's')
            bo(tray, ear, 'u')
    tray_occ = comp('Tray_Al6061', tray, AP['al'], MAT['al'])

    # ------------------------------------------------------------------ 2. lid
    lid = box(0, 0, S.LID_Z, L, D, S.LID_Z + S.LID_T)
    for (sx, sy) in S.LID_SCREWS:
        bo(lid, cylz(sx, sy, S.LID_Z - 1, S.H + 1, 3.4), 's')
    lid_occ = comp('Lid_Al6061', lid, AP['al'], MAT['al'])
    screws = [union_all([cylz(sx, sy, S.LID_Z - 8, S.H, 3.0), cylz(sx, sy, S.H, S.H + 1.65, 5.5)]) for (sx, sy) in S.LID_SCREWS]
    lid_screw_occ = comp('LidScrew_M3x10_ISO7380', screws, AP['al'], MAT['ss'])

    # ------------------------------------------------------------------ 3. printed deck (PA6-GF)
    cl = 0.2
    deck = box(xi0 + cl, yi0 + cl, S.DECK_Z0, xi1 - cl, yi1 - cl, S.DECK_Z1)
    for (sx, sy) in S.LID_SCREWS:                       # clear the corner bosses
        cx = xi0 if sx < L / 2 else xi1
        cy = yi0 if sy < D / 2 else yi1
        bo(deck, cylz(cx, cy, S.DECK_Z0 - 1, S.DECK_Z1 + 1, 15.0), 's')
    cuts = []
    # bar + pads pockets
    B = S.BAR
    cuts.append(box(B['x'] - B['w'] / 2 - S.CLR, B['y0'] - S.CLR, BZ0, B['x'] + B['w'] / 2 + S.CLR, B['y1'] + S.CLR, S.DECK_Z1 + 1))
    PD = S.PAD
    def pad_box(a, z0, z1, grow=0.0):
        xa = a['x_out'] - a['sgn'] * PD['inner']
        xb = a['x_out'] + a['sgn'] * PD['outer']
        return box(min(xa, xb) - grow, a['y'] - PD['w'] / 2 - grow, z0, max(xa, xb) + grow, a['y'] + PD['w'] / 2 + grow, z1)
    for a in ami:
        cuts.append(pad_box(a, BZ0, S.DECK_Z1 + 1, S.CLR))
        xc = (a['x_in'] + a['x_out']) / 2                                       # AMI body relief
        cuts.append(cbox(xc, a['y'], S.BAR_TOP + S.AMI['ear_t'] / 2 - S.AMI['body_h'] / 2 - 0.6, S.DECK_Z1 + 1,
                         S.AMI['body_l'] + 1, S.AMI['body_w'] + 1))
        xh = a['x_out'] + a['sgn'] * HOLE_OFF                                   # barrel trough + wire hole
        cuts.append(box(min(a['x_out'], xh), a['y'] - (LUG['d4'] + 1) / 2, S.DECK_Z1 - 4, max(a['x_out'], xh), a['y'] + (LUG['d4'] + 1) / 2, S.DECK_Z1 + 1))
        cuts.append(cylz(xh, a['y'], S.DECK_Z0 - 1, S.DECK_Z1 + 1, 9.0))
    # M8 lug trough beyond the bar edge
    M8 = S.LUG_M8
    cuts.append(box(B['x'] + B['w'] / 2, S.IN_STUD_Y - (M8['b'] / 2 + S.CLR), S.BAR_TOP - M8['t'] - 0.5, L, S.IN_STUD_Y + (M8['b'] / 2 + S.CLR), S.DECK_Z1 + 1))
    # mini fuse cavities (2 x 2.8 mm receptacles each, approx 6 mm apart) + logic bus strips (Al 8 x 4) under each column
    mini = []
    for col, (cx, fuses) in S.MINI_COLS.items():
        for i, (nm, amps) in enumerate(fuses):
            y = S.MINI_Y0 + i * S.MINI['pitch']
            mini.append((col, nm, amps, cx, y))
            for dx in (-3.0, 3.0):
                cuts.append(cbox(cx + dx, y, S.DECK_Z0 - 1, S.DECK_Z1 + 1, 3.0, 4.6))
    ACPS_POS = (S.F7_COLS[1], S.F7_ROWS[3])
    for dx in (-3.0, 3.0):
        cuts.append(cbox(ACPS_POS[0] + dx, ACPS_POS[1], S.DECK_Z0 - 1, S.DECK_Z1 + 1, 3.0, 4.6))
    # F7 cavities (TE F7 bottom view: 30 / 87 blades along x, 85 / 86 along y)
    f7 = []
    k = 0
    for cx in S.F7_COLS:
        for cy in S.F7_ROWS:
            nm, pn, own = S.F7_POS[k]
            k += 1
            if nm == 'ACPS':
                continue
            f7.append((nm, pn, own, cx, cy))
            for (u, v, lx, ly) in ((0, 7.65, 11.5, 3.2), (0, -10.25, 11.5, 3.2), (-8.45, -0.25, 2.8, 8.3), (8.45, -0.25, 2.8, 8.3)):
                cuts.append(cbox(cx + u, cy + v, S.DECK_Z0 - 1, S.DECK_Z1 + 1, lx, ly))
    # micro relay cavities (approximate pattern from TE 1308028; set exactly in detail work)
    micro = []
    k = 0
    for cx in S.MICRO_COLS:
        for cy in S.MICRO_Y:
            nm, pn, own = S.MICRO_POS[k]
            k += 1
            micro.append((nm, pn, own, cx, cy))
            for (u, v, lx, ly) in ((0, 8.0, 8.3, 2.6), (0, -8.0, 8.3, 2.6), (-4.5, 0, 2.6, 6.8), (4.5, 0, 2.6, 6.8), (0, 0, 2.6, 4.0)):
                cuts.append(cbox(cx + u, cy + v, S.DECK_Z0 - 1, S.DECK_Z1 + 1, lx, ly))
    sub_all(deck, cuts)
    deck_occ = comp('Deck_PA6GF_printed', deck, AP['deck'], MAT['pa'])

    # ------------------------------------------------------------------ 4. conductors
    bar = box(B['x'] - B['w'] / 2, B['y0'], BZ0, B['x'] + B['w'] / 2, B['y1'], S.BAR_TOP)
    bo(bar, slot_x(B['x'] - (M8['tip'] - M8['b'] / 2) - 0.0, B['x'] + 40, S.IN_STUD_Y, S.BAR_TOP - M8['t'], S.BAR_TOP + 1, M8['b'] + 2 * S.CLR), 's')
    bo(bar, cylz(B['x'], S.IN_STUD_Y, BZ0 - 1, S.BAR_TOP + 1, 8.0), 's')
    pads = []
    for a in ami:
        bo(bar, cylz(a['x_in'], a['y'], BZ0 - 1, S.BAR_TOP + 1, 5.0), 's')
        p = pad_box(a, BZ0, S.BAR_TOP)
        # ring-lug inset (bus bar design B style, machined in the Al): round end at the stud, open outer end
        bo(p, box(min(a['x_out'], a['x_out'] + a['sgn'] * 40), a['y'] - (LUG['b'] / 2 + S.CLR), S.BAR_TOP - LUG['t'],
                  max(a['x_out'], a['x_out'] + a['sgn'] * 40), a['y'] + (LUG['b'] / 2 + S.CLR), S.BAR_TOP + 1), 's')
        bo(p, cylz(a['x_out'], a['y'], S.BAR_TOP - LUG['t'] - 0.01, S.BAR_TOP + 1, LUG['b'] + 2 * S.CLR), 's')   # round end of the inset
        bo(p, cylz(a['x_out'], a['y'], BZ0 - 1, S.BAR_TOP + 1, 5.0), 's')
        pads.append(p)
    # logic bus strips inside the deck (embedded, Al 8 x 4)
    strips = []
    for col, (cx, fuses) in S.MINI_COLS.items():
        n = len(fuses)
        strips.append(box(cx - 4, S.MINI_Y0 - 6, 40.0, cx + 4, S.MINI_Y0 + (n - 1) * S.MINI['pitch'] + 6, 44.0))
    bar_occ = comp('Bar_Power_Al6061_25x6', bar, AP['al_bar'], MAT['al'])
    pad_occ = comp('Pad_Out_Al6061', pads, AP['al_bar'], MAT['al'])
    strip_occ = comp('Strip_Logic_Al6061_8x4', strips, AP['al_bar'], MAT['al'])

    # studs + nuts (M5 A2 set-screw studs, Keps nuts; M8 input stud)
    stud_top = S.BAR_TOP + S.AMI['ear_t'] + S.M5_NUT['h'] + 1.5
    studs = [cylz(a['x_in'], a['y'], BZ0, stud_top, 5.0) for a in ami] + [cylz(a['x_out'], a['y'], BZ0, stud_top, 5.0) for a in ami]
    studs.append(cylz(B['x'], S.IN_STUD_Y, BZ0, S.BAR_TOP + 1.6 + S.M8_NUT['h'] + 2.5, 8.0))
    nuts = [hexz(x, a['y'], S.BAR_TOP + S.AMI['ear_t'], S.BAR_TOP + S.AMI['ear_t'] + S.M5_NUT['h'], S.M5_NUT['af']) for a in ami for x in (a['x_in'], a['x_out'])]
    nuts.append(hexz(B['x'], S.IN_STUD_Y, S.BAR_TOP + 1.6, S.BAR_TOP + 1.6 + S.M8_NUT['h'], S.M8_NUT['af']))
    stud_occ = comp('Stud_M5_M8_A2', studs, AP['al'], MAT['ss'])
    nut_occ = comp('Nut_Keps_M5_M8_A2', nuts, AP['al'], MAT['ss'])

    # ring lugs (Cu tin) in the insets, barrel + wire stub down through the deck
    lugs, wires = [], []
    for a in ami:
        if a['amps'] is None:
            continue
        z0 = S.BAR_TOP - LUG['t']
        x_end_t = a['x_out'] + a['sgn'] * (LUG['l'] - LUG['tip'] - 9.0)     # palm end; barrel 9 mm
        t = box(min(a['x_out'], x_end_t), a['y'] - LUG['b'] / 2, z0, max(a['x_out'], x_end_t), a['y'] + LUG['b'] / 2, S.BAR_TOP)
        bo(t, cylz(a['x_out'], a['y'], z0, S.BAR_TOP, LUG['b']), 'u')
        bo(t, cylz(a['x_out'], a['y'], z0 - 1, S.BAR_TOP + 1, 5.5), 's')
        bz = z0 + LUG['d4'] / 2
        bo(t, cyl((x_end_t, a['y'], bz), (lug_end(a), a['y'], bz), LUG['d4']), 'u')
        lugs.append(t)
        xh = a['x_out'] + a['sgn'] * HOLE_OFF
        w_ = cyl((lug_end(a), a['y'], bz), (xh, a['y'], bz), WIRE_D)
        bo(w_, cylz(xh, a['y'], S.DECK_Z0 - 8, bz, WIRE_D), 'u')
        bo(w_, tb.createSphere(P(xh, a['y'], bz), WIRE_D / 20.0), 'u')
        wires.append(w_)
    # 1/0 input lug (Klauke 6R8) in the bar inset, cable out through the outboard wall
    z0 = S.BAR_TOP - M8['t']
    x_t1 = B['x'] + (M8['l'] - M8['tip'] - 19.0)
    t = box(B['x'], S.IN_STUD_Y - M8['b'] / 2, z0, x_t1, S.IN_STUD_Y + M8['b'] / 2, S.BAR_TOP)
    bo(t, cylz(B['x'], S.IN_STUD_Y, z0, S.BAR_TOP, M8['b']), 'u')
    bo(t, cylz(B['x'], S.IN_STUD_Y, z0 - 1, S.BAR_TOP + 1, 8.4), 's')
    bo(t, cyl((x_t1, S.IN_STUD_Y, gz), (B['x'] + M8['l'] - M8['tip'], S.IN_STUD_Y, gz), M8['d4']), 'u')
    lugs.append(t)
    cable = cyl((B['x'] + M8['l'] - M8['tip'], S.IN_STUD_Y, gz), (L + 25, S.IN_STUD_Y, gz), 13.0)
    grommet = bo(cyl((L - W - 2, S.IN_STUD_Y, gz), (L + 2, S.IN_STUD_Y, gz), S.IN_GROMMET['d']), cyl((L - W - 3, S.IN_STUD_Y, gz), (L + 3, S.IN_STUD_Y, gz), 13.0), 's')
    lug_occ = comp('Lug_Klauke_2R5_6R8', lugs, AP['cu'])
    wire_occ = comp('Wire_stub', wires, AP['wire'])
    cable_occ = comp('Cable_1-0_input', cable, AP['black'])
    grom_occ = comp('Grommet_1-0', grommet, AP['black'])

    # AMI fuses
    by_col = {}
    for a in ami:
        if a['amps'] is None:
            continue
        xa, xb = sorted((a['x_in'], a['x_out']))
        ear = slot_x(xa, xb, a['y'], S.BAR_TOP, S.BAR_TOP + S.AMI['ear_t'], S.AMI['ear_w'])
        bo(ear, box(xa - 6, a['y'] - 10, S.BAR_TOP - 1, xa - (S.AMI['L'] - S.AMI['c']) / 2, a['y'] + 10, S.BAR_TOP + 2), 's')
        bo(ear, box(xb + (S.AMI['L'] - S.AMI['c']) / 2, a['y'] - 10, S.BAR_TOP - 1, xb + 6, a['y'] + 10, S.BAR_TOP + 2), 's')
        for x in (xa, xb):
            bo(ear, cylz(x, a['y'], S.BAR_TOP - 1, S.BAR_TOP + 2, S.AMI['hole']), 's')
        zc = S.BAR_TOP + S.AMI['ear_t'] / 2
        body = cbox((xa + xb) / 2, a['y'], zc - S.AMI['body_h'] / 2, zc + S.AMI['body_h'] / 2, S.AMI['body_l'], S.AMI['body_w'])
        bo(body, ear, 'u')
        by_col.setdefault(S.AMI_COLOUR[a['amps']], []).append(body)
    for colr, bodies in by_col.items():
        comp('Fuse_AMI_%s' % colr, bodies, AP[colr], MAT['abs'])

    # mini fuses (ATM), body above the deck
    by_amp = {}
    for (col, nm, amps, cx, y) in mini + [('ACPS', 'ACPS', 10, ACPS_POS[0], ACPS_POS[1])]:
        if amps is None:
            continue
        by_amp.setdefault(amps, []).append(cbox(cx, y, S.DECK_Z1, S.DECK_Z1 + S.MINI['h_above'], S.MINI['l'], S.MINI['w']))
    for amps, bodies in by_amp.items():
        comp('Fuse_ATM_%sA' % str(amps).replace('.', 'p'), bodies, MINI_AP[amps], MAT['abs'])

    # relays: used = black, spare position = grey dummy outline (flat cap, not a part)
    f7_used = [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + S.F7['h'], S.F7['body'], S.F7['body']) for (nm, pn, own, cx, cy) in f7 if pn]
    f7_spare = [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + 1.0, S.F7['body'], S.F7['body']) for (nm, pn, own, cx, cy) in f7 if not pn]
    mi_used = [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + S.MICRO['h'], S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy) in micro if pn]
    mi_spare = [cbox(cx, cy, S.DECK_Z1, S.DECK_Z1 + 1.0, S.MICRO['x'], S.MICRO['y']) for (nm, pn, own, cx, cy) in micro if not pn]
    comp('Relay_TE_F7_V23134', f7_used, AP['black'], MAT['abs'])
    comp('Relay_TE_MicroA_V23074', mi_used, AP['black'], MAT['abs'])
    comp('SPARE_positions', f7_spare + mi_spare, AP['spare'])

    # isolators: nylon shoulder washers on each ear, above and below (box floats ISO t off the mount face)
    I = S.ISO
    isos = []
    for ex in (-E['len'] / 2, L + E['len'] / 2):
        for ey in E['ys']:
            lo = bo(cylz(ex, ey, -I['t'], 0, I['od']), cylz(ex, ey, -I['t'] - 1, 1, I['id']), 's')
            up = union_all([cylz(ex, ey, E['t'], E['t'] + I['t'], I['od']), cylz(ex, ey, 0.2, E['t'], I['sleeve_od'])])
            bo(up, cylz(ex, ey, -1, E['t'] + I['t'] + 1, I['id']), 's')
            isos += [lo, up]
    iso_occ = comp('Isolator_nylon_shoulder_washer', isos, AP['nylon'], MAT['pa'])
    mount = [box(-30, -10, -I['t'] - 3, L + 30, D + 10, -I['t'])]
    mount_occ = comp('REF_MountFace_body', mount, AP['black'])
    mount_occ.isLightBulbOn = False

    # ------------------------------------------------------------------ checks
    mm = app.measureManager
    cond = []
    for o in root.occurrences:
        n = o.component.name
        if n.startswith(('Bar_', 'Pad_', 'Strip_', 'Stud_', 'Nut_', 'Lug_', 'Fuse_AMI')):
            for b in o.bRepBodies:
                cond.append((n, b))
    tray_b = tray_occ.bRepBodies.item(0)
    lid_b = lid_occ.bRepBodies.item(0)
    mount_b = mount_occ.bRepBodies.item(0)
    iso_r = {}
    iso_r['min_conductor_to_tray_mm'] = round(min(mm.measureMinimumDistance(b, tray_b).value for _, b in cond) * 10, 2)
    iso_r['min_conductor_to_lid_mm'] = round(min(mm.measureMinimumDistance(b, lid_b).value for _, b in cond) * 10, 2)
    iso_r['tray_to_mount_face_mm'] = round(mm.measureMinimumDistance(tray_b, mount_b).value * 10, 2)
    report['isolation'] = iso_r
    # interference: every solid pair that should not touch (cheap: deck vs everything above it, conductors vs relays)
    bb = root.boundingBox
    report['outer_mm'] = dict(L=S.L, D=S.D, H=S.H, L_with_ears=S.L + 2 * E['len'],
                              bbox=[round((bb.maxPoint.x - bb.minPoint.x) * 10, 1), round((bb.maxPoint.y - bb.minPoint.y) * 10, 1), round((bb.maxPoint.z - bb.minPoint.z) * 10, 1)])
    report['footprint_mm2'] = S.L * S.D
    ints = []
    for o in root.occurrences:
        if o.component.name.startswith(('REF_', 'Wire_', 'Cable_', 'Grommet_', 'LidScrew', 'Stud_', 'Nut_', 'Lug_')):
            continue
        ints.append(o)
    coll = adsk.core.ObjectCollection.create()
    for o in ints:
        coll.add(o)
    try:
        ir = design.analyzeInterference(design.createInterferenceInput(coll))
        report['interference'] = [(r.entityOne.parentComponent.name if hasattr(r.entityOne, 'parentComponent') else str(r.entityOne),
                                   r.entityTwo.parentComponent.name if hasattr(r.entityTwo, 'parentComponent') else str(r.entityTwo),
                                   round(r.interferenceBody.volume * 1000, 3)) for r in ir]
    except Exception as ex:   # report, do not hide
        report['interference_error'] = str(ex)

    # masses
    report['mass_g'] = {o.component.name: round(o.component.physicalProperties.mass * 1000, 1) for o in root.occurrences
                        if o.component.name.startswith(('Tray', 'Lid', 'Deck', 'Bar', 'Pad', 'Strip'))}

    # ------------------------------------------------------------------ exports
    em = design.exportManager
    exported = []
    for o in root.occurrences:
        n = o.component.name
        if n.startswith(('REF_', 'Wire_', 'Cable_')):
            continue
        if n.startswith(('Tray', 'Lid_', 'Deck', 'Bar_', 'Pad_', 'Strip_')):
            p = os.path.join(out_dir, '%s.step' % n)
            em.execute(em.createSTEPExportOptions(p, o.component))
            exported.append(os.path.basename(p))
        if n.startswith('Deck'):
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

    def shot(fn, orient=None, eye=None):
        cam = vp.camera
        if eye is not None:
            cx, cy, cz = S.L / 2, S.D / 2, 40
            cam.target = P(cx, cy, cz)
            cam.eye = P(cx + eye[0], cy + eye[1], cz + eye[2])
            cam.upVector = V(0, 0, 1)
        else:
            cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()
        vp.saveAsImageFile(os.path.join(out_dir, fn), 1800, 1100)

    shot('fusebox_render_iso_closed.png', eye=(-260, -420, 330))
    lid_occ.isLightBulbOn = False
    lid_screw_occ.isLightBulbOn = False
    shot('fusebox_render_iso_open.png', eye=(-260, -420, 330))
    shot('fusebox_render_iso_open_rear.png', eye=(300, 420, 330))
    shot('fusebox_render_top_open.png', VO.TopViewOrientation)

    def section(fn, axis, at, orient):
        sec = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sec.component.name = 'SECTION_tmp'
        big = 1000.0
        keep = box(-big, at, -big, big, big, big) if axis == 'y' else box(at, -big, -big, big, big, big)
        vis = {}
        for o in list(root.occurrences):
            if o is sec:
                continue
            vis[o.entityToken] = o.isLightBulbOn
            if o.isLightBulbOn:
                for b in o.component.bRepBodies:
                    c = tb.copy(b)
                    if tb.booleanOperation(c, tb.copy(keep), BT.IntersectionBooleanType) and c.lumps.count > 0:
                        nb = sec.component.bRepBodies.add(c)
                        nb.appearance = b.appearance
            o.isLightBulbOn = False
        shot(fn, orient)
        sec.deleteMe()
        for o in root.occurrences:
            if o.entityToken in vis:
                o.isLightBulbOn = vis[o.entityToken]

    section('fusebox_section_power.png', 'y', S.AMI_Y0 + 2 * S.AMI_PITCH, VO.FrontViewOrientation)
    section('fusebox_section_logic.png', 'y', S.MICRO_Y[1], VO.FrontViewOrientation)
    lid_occ.isLightBulbOn = True
    lid_screw_occ.isLightBulbOn = True

    proj = [pj for pj in app.data.dataProjects if pj.name == 'Default Project'][0]
    doc.saveAs(DOC, proj.rootFolder, 'ST185 glove-box fuse + relay box rev 1 (Claude Code 2026-10-14)', '')
    with open(os.path.join(out_dir, 'fusebox_report.json'), 'w') as f:
        json.dump(report, f, indent=1)
    return report
