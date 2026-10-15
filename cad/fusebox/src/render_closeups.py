"""Close-up renders of the rev 7 fuse box design features from DECISIONS R120-R123 (Dan 2026-10-15: "also show me close up image
renderings of the new design features we put in the fuse boxes"). Run inside Fusion (Fusion MCP script runner) after
build_fusion.build(OUT, rev=7): it copies the built bodies out of the ST185_fusebox_rev7 document into a scratch design that is never
saved and is closed without saving at the end (no Fusion file is made or changed, R74), cuts the sections there, adds simplified terminal / insert / screw / sleeve models sized from
spec.py, and writes raw PNGs to OUT/renders/closeups/raw/. finish_closeups.py (plain Python) then adds the border, title and notes.
    render(r'...\\cad\\fusebox\\rev7')
The terminal, insert, screw and sleeve models are simplified (boxes and cylinders at the TE / spec sizes), not maker CAD.
Claude Code, 2026-10-15.
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
Z_D = {'LOGIC': S.LOGIC['z_d'], 'POWER': S.POWER['z_d']}
Z_T = {b: Z_D[b] + S.TOWER_H[b] for b in Z_D}


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
    """Section: remove everything on one side of the plane axis = at (keep the side below `at` when keep_below)."""
    lo, hi = (at, at + big) if keep_below else (at - big, at)
    b = {'x': (lo, -big, -big, hi, big, big), 'y': (-big, lo, -big, big, hi, big), 'z': (-big, -big, lo, big, big, hi)}[axis]
    try:
        bo(body, box(*b), 's')
    except RuntimeError:
        return None
    return body if body.volume > 1e-9 else None


def render(out_dir):
    raw = os.path.join(out_dir, 'renders', 'closeups', 'raw')
    os.makedirs(raw, exist_ok=True)
    src_doc = [d for d in app.documents if d.name.split(' v')[0] == 'ST185_fusebox_rev7']
    if not src_doc:
        raise RuntimeError('open ST185_fusebox_rev7 first (build_fusion.build(..., rev=7))')
    src = adsk.fusion.Design.cast(src_doc[0].products.itemByProductType('DesignProductType'))
    bodies = {o.component.name: o.component.bRepBodies.item(0) for o in src.rootComponent.occurrences if o.component.bRepBodies.count}
    tgt = [d for d in app.documents if not d.isSaved and d.name.startswith('Untitled')]
    made = not tgt
    tdoc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType) if made else tgt[0]   # scratch, never saved
    tdoc.activate()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    alib = app.materialLibraries.itemByName('Fusion Appearance Library')

    def tint(base, name, rgb, opacity=None):
        a = design.appearances.itemByName(name)
        if a is None:
            a = design.appearances.addByCopy(alib.appearances.itemByName(base), name)
            for i in range(a.appearanceProperties.count):
                p_ = a.appearanceProperties.item(i)
                if isinstance(p_, adsk.core.ColorProperty) and p_.name in ('Color', 'Colour'):
                    p_.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    break
        return a
    AP = dict(pa12=tint('Plastic - Matte (Gray)', 'PA12 MJF light', (170, 174, 178)), cover=tint('Plastic - Matte (Gray)', 'PA12 cover', (120, 124, 128)),
              clip=tint('Plastic - Matte (Gray)', 'PA12 clip blue', (70, 120, 200)), brass=alib.appearances.itemByName('Brass - Polished'),
              steel=alib.appearances.itemByName('Steel - Satin'), wire=tint('Plastic - Glossy (Red)', 'Wire red', (200, 40, 30)),
              wire2=tint('Plastic - Glossy (Red)', 'Wire yellow', (230, 190, 40)), sl1=tint('Plastic - Matte (Black)', 'RNF-100 3/32', (25, 25, 25)),
              sl2=tint('Plastic - Matte (Black)', 'RNF-100 1/8', (85, 85, 90)), lance=tint('Plastic - Glossy (Red)', 'Lance mark', (230, 120, 20)),
              cu=alib.appearances.itemByName('Copper - Raw'))
    vp = app.activeViewport
    notes = {}

    def clear():
        for i in range(root.occurrences.count - 1, -1, -1):
            root.occurrences.item(i).deleteMe()

    def add(name, b, ap):
        if b is None:
            return
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        bb = occ.component.bRepBodies.add(b)
        if ap is not None:
            bb.appearance = ap

    def shot(fn, target, eye, extent, up=(0, 0, 1)):
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
        cam.target = P(*target)
        cam.eye = P(target[0] + eye[0], target[1] + eye[1], target[2] + eye[2])
        cam.upVector = adsk.core.Vector3D.create(*up)
        cam.isFitView = False
        cam.viewExtents = extent / 10.0
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(raw, fn), W_IMG, H_IMG)
        return vp

    plan = json.load(open(os.path.join(out_dir, 'wiring_plan.json'), encoding='utf-8'))
    cav = {(c['box'], c['cav']): c for c in plan['cavities']}

    def terminal(c, box_name, section=None):
        """Simplified crimped terminal seated in cavity c (contact end at the seat, hanging down): contact box, lance(s), stop flange
        (880398-2), wire barrel, insulation barrel on the wire (+ its RNF-100 build-up), wire. Returns [(name, body, appearance)]."""
        part, kind = c['part'], c['kind']
        sx_, sy_ = S.PLACE[box_name]
        x, y = c['x'] + sx_, c['y'] + sy_
        zs = Z_T[box_name] - S.HOLE['top_gap']
        T, L_ = S.TERM[part], S.LOCK[part]
        Lt = T['L'] or S.L_EST
        (w, h) = T['head']
        bx, by = S._xy(w, h, kind)
        tip = L_.get('tip', 5.0)
        blen = L_['neck'] - 1.5 if part == '880398-2' else min(Lt * 0.45, L_['neck'] - 2.0)
        out = [('Terminal box', box(x - bx / 2, y - by / 2, zs - blen, x + bx / 2, y + by / 2, zs), AP['brass'])]
        if L_['kind'] == 'lance':
            o, lt = L_['out'], 0.4
            if L_['axis'] == 'W':
                ax, sides = ('x' if S.BLADE_AXIS[kind] == 'x' else 'y'), (-1, 1)
            else:
                ax, sides = ('y' if S.BLADE_AXIS[kind] == 'x' else 'x'), (S.lance_side(dict(c, box=box_name), [dict(d, box=d['box']) for d in plan['cavities']]),)
            for sg in sides:
                half = (bx if ax == 'x' else by) / 2
                a0, a1 = half - lt, half + o
                if ax == 'x':
                    lb = box(x + sg * a0, y - min(by, 2.4) / 2, zs - tip, x + sg * a1, y + min(by, 2.4) / 2, zs - tip + 2.2)
                else:
                    lb = box(x - min(bx, 2.4) / 2, y + sg * a0, zs - tip, x + min(bx, 2.4) / 2, y + sg * a1, zs - tip + 2.2)
                out.append(('Lance', lb, AP['lance']))
        if L_.get('flange'):
            fx, fy = S._xy(L_['flange'], h, kind)
            out.append(('Stop flange', box(x - fx / 2, y - fy / 2, zs - L_['neck'] - 0.8, x + fx / 2, y + fy / 2, zs - L_['neck']), AP['brass']))
        ins_len = 4.0
        out.append(('Wire barrel', box(x - 1.4, y - 1.0, zs - Lt + ins_len, x + 1.4, y + 1.0, zs - blen), AP['brass']))
        cod = S.crimp_od(part, c['wire_od'])
        out.append(('Insulation barrel', cyl((x, y, zs - Lt), (x, y, zs - Lt + ins_len), S.barrel_od(part, c['wire_od'])), AP['brass']))
        if cod > c['wire_od'] + 1e-6:
            out.append(('RNF-100 build-up', cyl((x, y, zs - Lt - 6.0), (x, y, zs - Lt + ins_len - 0.3), cod), AP['sl1']))
        out.append(('Wire', cyl((x, y, zs - Lt - 18.0), (x, y, zs - Lt + 1.0), c['wire_od']), AP['wire2']))
        if section:
            out = [(n, cut_half(b, *section), a) for (n, b, a) in out]
        return out

    # ---------------------------------------------------------------- (a) cavity half-sections, terminal seated
    for (fn, box_name, cv, title) in (('closeup_a1_cavity_880398-2.png', 'LOGIC', 'BUS2-4', '880398-2 (mini fuse output) - two side lances, 3.8 mm shoulder, stop flange'),
                                      ('closeup_a2_cavity_280919-2.png', 'LOGIC', 'M2 85', '280919-2 (micro relay coil, R123 swap) - one lance through the blade')):
        clear()
        c = cav[(box_name, cv)]
        sx_, sy_ = S.PLACE[box_name]
        x, y = c['x'] + sx_, c['y'] + sy_
        L_ = S.LOCK[c['part']]
        lance_ax = 'x' if S.BLADE_AXIS[c['kind']] == ('x' if L_['axis'] == 'W' else 'y') else 'y'
        cut_ax = 'y' if lance_ax == 'x' else 'x'          # the section plane contains the lance axis
        sec = (cut_ax, (y if cut_ax == 'y' else x), True)
        base = tb.copy(bodies['%s_Base_PA12_printed' % box_name.capitalize()])
        bo(base, box(x - 16, y - 16, Z_D[box_name] - 12, x + 16, y + 16, Z_T[box_name] + 1), 'i')
        add('Base (section)', cut_half(base, *sec), AP['pa12'])
        for (n, b, a) in terminal(c, box_name, sec):
            add(n, b, a)
        zc = (Z_D[box_name] + Z_T[box_name]) / 2 - 4
        eye = (0, 150, 22) if cut_ax == 'y' else (150, 0, 22)      # from the cut side, onto the section face
        shot(fn, (x, y, zc), eye, 44.0)
        notes[fn] = dict(title=title, cav='%s %s' % (box_name, cv), part=c['part'], hole=c['hole'], lock=L_)

    # ---------------------------------------------------------------- (b) LOGIC micro relay columns, top view
    clear()
    base = tb.copy(bodies['Logic_Base_PA12_printed'])
    add('Logic base', base, AP['pa12'])
    for n_, b_ in bodies.items():
        if n_.startswith('Logic_Strip') or n_.startswith('Logic_Limiter'):
            add(n_, tb.copy(b_), AP['cu'] if 'Strip' in n_ else AP['steel'])
    tgt_b = (S.LOGIC['L'] / 2, S.D / 2, Z_T['LOGIC'])
    v = shot('closeup_b_logic_micro_columns_top.png', tgt_b, (0, 0, 200), 190.0, up=(0, 1, 0))
    pts = {}
    for (k, xx) in (('old1', 51.5), ('new1', S.MICRO_COLS[0]), ('old2', 70.0), ('new2', S.MICRO_COLS[1]), ('edge_old', 81.5), ('edge_new', S.LOGIC['L'])):
        p0 = v.modelToViewSpace(P(xx, 10.0, Z_T['LOGIC']))
        p1 = v.modelToViewSpace(P(xx, 150.0, Z_T['LOGIC']))
        pts[k] = [round(p0.x, 1), round(p0.y, 1), round(p1.x, 1), round(p1.y, 1)]
    vw, vh = v.width, v.height
    notes['closeup_b_logic_micro_columns_top.png'] = dict(title='LOGIC micro relay columns 2.0 mm further out (R123)', lines=pts, view=[vw, vh])

    # ---------------------------------------------------------------- (c) heater relay R1 retainer clip, on + exploded
    rr = json.load(open(os.path.join(out_dir, 'fusebox_report.json'), encoding='utf-8'))['retainers']['POWER'][0]
    p_ = rr['plate']
    sx_, sy_ = S.PLACE['POWER']
    cx_, cy_ = (p_[0] + p_[3]) / 2 + sx_, (p_[1] + p_[4]) / 2 + sy_
    for (fn, dz) in (('closeup_c1_r1_retainer_on.png', 0.0), ('closeup_c2_r1_retainer_exploded.png', -22.0)):
        clear()
        base = tb.copy(bodies['Power_Base_PA12_printed'])
        bo(base, box(cx_ - 34, cy_ - 30, Z_D['POWER'] - 8, cx_ + 34, cy_ + 30, Z_T['POWER'] + 1), 'i')
        add('Power base', base, AP['pa12'])
        for cv in rr['cavities']:
            for (n, b, a) in terminal(cav[('POWER', cv)], 'POWER'):
                if dz and n in ('Wire', 'RNF-100 build-up'):
                    m = adsk.core.Matrix3D.create()
                    tb.transform(b, m)
                add(n, b, a)
        clip = tb.copy(bodies['Power_Retainer_R1_PA12_printed'])
        if dz:
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(0, 0, dz / 10.0)
            tb.transform(clip, m)
        add('R1 retainer clip', clip, AP['clip'])
        shot(fn, (cx_, cy_, Z_D['POWER'] - 6 + dz / 2), (-110, -150, -95), 78.0 if not dz else 92.0)
        notes[fn] = dict(title='Heater relay R1 retainer clip (R123 B) - %s' % ('snapped on, from below' if not dz else 'exploded: threaded on the wires, pushed up'), clip=rr)

    # ---------------------------------------------------------------- (d) lid catch + optional M3 insert and screw, section
    clear()
    L = S.LOGIC['L']
    xs = L * 0.25 + S.SCREW['off']
    zsc = Z_T['LOGIC'] - S.SCREW['z_from_top']
    keep = (xs - 14, -8, zsc - 16, xs + 14, 22, Z_T['LOGIC'] + 8)
    for (n_, ap_) in (('Logic_Base_PA12_printed', AP['pa12']), ('Logic_Cover_PA12_printed', AP['cover'])):
        b_ = tb.copy(bodies[n_])
        bo(b_, box(*keep), 'i')
        add(n_, cut_half(b_, 'x', xs, True), ap_)
    SC = S.SCREW
    ins = cyl((xs, -0.01, zsc), (xs, SC['ins_depth'] - 0.3, zsc), 4.6)
    bo(ins, cyl((xs, -1, zsc), (xs, SC['ins_depth'] + 1, zsc), 3.0), 's')
    add('M3 heat-set insert', cut_half(ins, 'x', xs, True), AP['brass'])
    yo = -(S.PCLR + S.COVER['t'] + S.RUG['band_out'])
    scr = cyl((xs, yo - 3.0, zsc), (xs, yo, zsc), SC['head_d'])
    bo(scr, cyl((xs, yo - 0.01, zsc), (xs, yo + 10.0, zsc), 3.0), 'u')
    add('M3 x 10 cap screw', cut_half(scr, 'x', xs, True), AP['steel'])
    shot('closeup_d_lid_catch_screw_section.png', (xs, 4.0, zsc - 2), (150, 0, 18), 34.0)
    notes['closeup_d_lid_catch_screw_section.png'] = dict(title='Cover catch + optional M3 backup screw into a heat-set insert (R122), section', screw=SC)

    # ---------------------------------------------------------------- (e) crimped terminal with the RNF-100 build-up, section
    clear()
    c = dict(cav[('POWER', 'R2 85')])
    od, part = c['wire_od'], c['part']
    seq, d2 = S.build_up(part, od)
    x, y, z0 = 0.0, 0.0, 0.0
    Lt, ins_len = S.TERM[part]['L'], 4.0
    layers = [('Wire', cyl((x, y, z0 - 22), (x, y, z0 + ins_len + 1.0), od), AP['wire2'])]
    d_ = od
    for k, sz in enumerate(seq or []):
        d_ = S.sleeved_od(d_, sz)
        layers.append(('%s build-up' % sz, cyl((x, y, z0 - 8 - 2 * k), (x, y, z0 + ins_len - 0.4), d_), AP['sl1'] if k == 0 else AP['sl2']))
    bar = cyl((x, y, z0), (x, y, z0 + ins_len), S.barrel_od(part, od))
    bo(bar, cyl((x, y, z0 - 1), (x, y, z0 + ins_len + 1), d_), 's')
    layers.append(('Insulation barrel (crimped)', bar, AP['brass']))
    layers.append(('Wire barrel', box(x - 1.4, y - 1.0, z0 + ins_len, x + 1.4, y + 1.0, z0 + ins_len + 5.0), AP['brass']))
    (w, h) = S.TERM[part]['head']
    layers.append(('Contact box', box(x - w / 2, y - h / 2, z0 + ins_len + 5.0, x + w / 2, y + h / 2, z0 + Lt), AP['brass']))
    for (n, b, a) in layers:
        add(n, cut_half(b, 'y', 0.0, True), a)
    shot('closeup_e_rnf100_buildup_section.png', (0, 0, 7.0), (0, 150, 20), 40.0)
    notes['closeup_e_rnf100_buildup_section.png'] = dict(title='Crimped %s on %.2f mm thin-wall wire with its RNF-100 build-up (%s) under the insulation barrel (R120)' % (
        part, od, ' + '.join(seq or [])), od=od, built_up=round(d2, 2), barrel=round(S.barrel_od(part, od), 2))
    clear()
    with open(os.path.join(raw, 'closeups.json'), 'w') as f:
        json.dump(notes, f, indent=1, default=str)
    src_doc[0].activate()
    if made:
        tdoc.close(False)       # the scratch design: discarded, never saved
    return notes


def run(_context: str):
    print(json.dumps(render(os.path.join(os.path.dirname(SRC), 'rev7')), default=str)[:3000])
