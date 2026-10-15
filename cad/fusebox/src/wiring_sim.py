"""Wire simulation for the selected fuse boxes (POWER rev 7, LOGIC, battery relay block): EVERY harness wire that lands in a
box (ST185-CabinPower, -HeavyDC, -EngineRoom-C, -RearFuel ...), at its real cavity, with its real gauge OD, insulation colour,
ident bands and terminal part, routed under the deck into the bundle of its exit (the CAD lanes, which set the belly pan exits)
with the bend rule (3 x OD where the wire is tied into its bundle, FAA AC 43.13-1B 11-96).
Pure Python (no Fusion): it writes the plan (cad/fusebox/rev7/wiring_plan.json, read by render_wired_rev7.py inside Fusion)
and the numbers that need no geometry (wires per box, bundle sizes against the exits, two wires in one terminal, terminal part
differences). The Fusion script adds the geometric checks (wire through plastic, cover, fuse / relay pull, wire to wire).
    python cad/fusebox/src/wiring_sim.py            # writes the plan + prints the summary
Claude Code, 2026-10-14.
"""
import json, glob, os, re, math, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REB = os.path.join(REPO, 'docs', 'harness', 'rebuild')
OUT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wiring_plan.json')
CAD_REPORT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'fusebox_report.json')

OD = dict(S.OD)
OD[16] = OD.get(16, 2.06)
METRIC_OD = {53.5: OD['1/0']}            # 1/0 SGX, 53.5 mm2
MM2 = {20: 0.52, 18: 0.82, 16: 1.31, 14: 2.08, 12: 3.31, 10: 5.26, 8: 8.37, 6: 13.3}
TERM_RANGE = {'1241388-2': (0.5, 1.0), '880398-2': (1.0, 2.5), '42281-1': (0.8, 2.0), '2293255-1': (0.51, 1.65),
              '280756-4': (3.31, 5.26), '280755-4': (6.0, 10.0), '62998-2': (5.0, 8.0)}     # mm2, from the parts list / harness part text
RELAY_NAMES = {'HEAD LH': 'k_hl', 'HEAD RH': 'k_hr', 'horn': 'k_horn', 'k_etb': 'k_etb', 'k_acc': 'k_acc', 'k_eps_en': 'k_eps_en', 'k_rev': 'k_rev',
               'heater': 'k_htr', 'k_efi': 'k_efi', 'k_str': 'k_str', 'k_fan': 'k_fan', 'k_fan2': 'k_fan2', 'power': 'k_pwr'}
PIN = {'30': 'c1', '85': 'c2', '86': 'c3', '87': 'c4', '87a': 'c5'}


def od_of(g, unit):
    if unit == 'Metric':
        return METRIC_OD.get(g, 13.6)
    return OD[int(g)]


def awg_mm2(g, unit):
    return g if unit == 'Metric' else MM2[int(g)]


# ------------------------------------------------------------------ cavity positions (box-local mm; POWER / LOGIC frames as the build)
def logic_cavities():
    cav = {}
    for col, (cx, fuses) in S.MINI_COLS.items():
        sd = S.MINI_IN[col]
        for i, (nm, amps) in enumerate(fuses):
            y = S.MINI_Y0 + i * S.MINI['pitch']
            d = '%s-%d' % (col, i + 1)
            cav[d] = dict(x=cx - sd * 3.0, y=y, lane=('L', round(cx - sd * 3.0, 2)), kind='fuse out', name=nm)
            cav[d + ' IN'] = dict(x=cx + sd * 3.0, y=y, lane=('L', round(cx - sd * 3.0, 2)), kind='fuse in', name=nm)
    k = 0
    for cx in S.MICRO_COLS:
        for cy in S.MICRO_Y:
            nm, pn, own = S.MICRO_POS[k]
            k += 1
            if not pn:
                continue
            rid = RELAY_NAMES[nm]
            for (u, v, tn) in ((0, -8.0, '30'), (0, 8.0, '87'), (0, 0, '87a'), (-4.5, 0, '85'), (4.5, 0, '86')):
                cav[(rid, PIN[tn])] = dict(x=cx + u, y=cy + v, lane=('L', cx), kind='micro ' + tn, name=rid)
    return cav


def power_relays():
    out = []
    for i, nm in enumerate(S.IN_RELAY):
        if nm == 'SPARE':
            continue
        cx = S.F7_X[1] if i % 2 == 0 else S.F7_X[0]
        cy = S.AMI_Y0 + i * S.AMI_PITCH
        out.append(dict(i=i, name=nm, rid=RELAY_NAMES[nm], cx=cx, cy=cy, B=(nm == S.RELAY_B['pos'])))
    return out


def power_cavities():
    cav = {}
    acps_y = S.ACPS_Y
    for r in power_relays():
        cx, cy = r['cx'], r['cy']
        pins = [('87', cx - 7.65, cy, cy), ('30', cx + 10.25, cy, None), ('85', cx + 0.25, cy - 8.45, cy - 9.0), ('86', cx + 0.25, cy + 8.45, cy + 9.0)]
        if r['B']:
            pins.append(('87a', cx - S.RELAY_B['v87a'], cy, cy))
        for (tn, x, y, lane) in pins:
            if lane is not None and (abs(lane - acps_y) < 1.0 or abs(lane - (S.AMI_Y0 - 9.0)) < 0.1):
                lane = acps_y                      # the heater 85 joins the ACPS lane (as the CAD)
            cav[(r['rid'], PIN[tn])] = dict(x=x, y=y, lane=('P', lane) if lane is not None else None, kind='F7 ' + tn, name=r['rid'])
    cav['ACPS IN'] = dict(x=S.F7_X[0] - 3.0, y=acps_y, lane=('P', acps_y), kind='acps in', name='ACPS')
    cav['ACPS'] = dict(x=S.F7_X[0] + 3.0, y=acps_y, lane=('P', acps_y), kind='acps out', name='ACPS')
    return cav


# ------------------------------------------------------------------ harness wires per box
def box_of(ent):
    i, lab = ent['id'], (ent.get('label') or '') + ' ' + (ent.get('signal') or '')
    if i in ('fb_power', 'pdb') or i.startswith('t_pdb_gnd'):
        return 'POWER'
    if i == 'fb_logic':
        return 'LOGIC'
    if i in ('fb_batt', 'k_fp'):
        return 'BATT'
    m = re.search(r'seated in the (POWER|LOGIC) box', lab)
    return m.group(1) if m else None


def harness_wires():
    rows = {}
    for fn in sorted(glob.glob(os.path.join(REB, '*.harness'))):
        d = json.load(open(fn, encoding='utf-8'))
        name = os.path.basename(fn)[6:-8]
        wp = {p['id']: p for p in d.get('wireParts', [])}
        cp = {p['id']: p for p in d.get('contactParts', [])}
        tp = {p['id']: p for p in d.get('terminalParts', [])}
        ents = {c['id']: ('conn', c, {cv['id']: cv for cv in c.get('cavities', [])}) for c in d.get('connectors', [])}
        ents.update({t['id']: ('term', t, {}) for t in d.get('terminals', [])})
        for w in d['wires']:
            ends = []
            for side in ('source', 'target'):
                e = w[side]
                ent = ents.get(e['id'])
                if not ent:
                    ends.append(dict(id=e['id'], cav=e.get('handle'), box=None, part=None, des=''))
                    continue
                kind, obj, cavs = ent
                cv = cavs.get(e.get('handle'), {})
                if kind == 'conn':
                    pp = cp.get(cv.get('contactPartId'))
                else:
                    pp = tp.get(obj.get('partId'))
                ends.append(dict(id=e['id'], cav=e.get('handle'), box=box_of(obj), part=pp.get('partNumber') if pp else None,
                                 des=cv.get('designation') or '', sig=(cv.get('signal') or obj.get('signal') or '')[:90]))
            if not any(x['box'] for x in ends):
                continue
            p = wp.get(w.get('partId'), {})
            g = p.get('gauge', {})
            rows[w['id']] = dict(wire=w['id'], file=name, colour=w.get('color') or 'Red', bands=w.get('identColors') or [],
                                 gauge=g.get('value'), unit=g.get('unit'), od=od_of(g.get('value'), g.get('unit')), ends=ends)
    return list(rows.values())


# ------------------------------------------------------------------ the plan
def fallback_part(box, end, gauge, unit):
    """Terminal part when the harness cavity names none: the box parts lists."""
    i, des = end['id'], end['des']
    if box == 'LOGIC' and i == 'fb_logic':
        return '1241388-2' if unit == 'AWG' and gauge >= 18 else '880398-2'
    if i == 'fb_power' and des.startswith('AMI'):
        return 'Klauke 3R5MS' if gauge == 6 else ('TE 36161' if gauge == 12 else 'Klauke 2R5')
    if i == 'pdb':
        return 'Klauke 6R8'
    if i in ('k_fp', 'fb_batt'):
        return 'Klauke 1R6'
    return None


def plan():
    wires = harness_wires()
    lc, pc = logic_cavities(), power_cavities()
    out_wires, notes = [], []
    term_load = collections.defaultdict(list)       # (box, conn, cav) -> wires (two wires in one terminal)
    for w in wires:
        ends = []
        for e in w['ends']:
            if not e['box']:
                ends.append(dict(e, at=None))
                continue
            at = None
            if e['id'] == 'fb_logic' and e['des'].startswith('BUS') and e['cav'] not in ('b1', 'b2'):
                at = lc.get(e['des'])
            elif e['box'] == 'LOGIC' and e['id'].startswith('k_'):
                at = lc.get((e['id'], e['cav']))
            elif e['box'] == 'POWER' and e['id'].startswith('k_'):
                at = pc.get((e['id'], e['cav']))
            elif e['id'] == 'fb_power' and e['cav'] in ('acps', 'acps_in'):
                at = pc['ACPS' if e['cav'] == 'acps' else 'ACPS IN']
            part = e['part'] or fallback_part(e['box'], e, w['gauge'], w['unit'])
            ends.append(dict(e, at=at, part=part, part_from='harness' if e['part'] else 'parts list'))
            term_load[(e['box'], e['id'], e['cav'])].append(w)
        w2 = dict(w, ends=ends)
        boxes = [e['box'] for e in ends if e['box']]
        w2['kind'] = ('internal' if len(boxes) == 2 and boxes[0] == boxes[1] else 'cross-box' if len(boxes) == 2 else 'external')
        out_wires.append(w2)
    # two wires crimped into one terminal: total cross-section against the terminal's range
    doubles = []
    for (bx, cid, cv), ws in term_load.items():
        if len(ws) < 2:
            continue
        part = next((e['part'] for w in out_wires if w['wire'] == ws[0]['wire'] for e in w['ends'] if e['id'] == cid and e['cav'] == cv), None)
        tot = sum(awg_mm2(w['gauge'], w['unit']) for w in ws)
        rng = TERM_RANGE.get(part)
        doubles.append(dict(box=bx, cavity='%s %s' % (cid, cv), wires=[w['wire'] for w in ws], mm2=round(tot, 2), part=part,
                            range=rng, over=bool(rng and tot > rng[1]) if part != 'Klauke 6R8' else False))
    return out_wires, doubles


def bundle_d(ods):
    return ods[0] if len(ods) == 1 else 1.2 * math.sqrt(sum(o * o for o in ods))


# ------------------------------------------------------------------ paths (box-local mm; z from the mount face)
PAN_TOP = S.PAN['z0'] + S.PAN['t']           # 4.0: belly pan floor top
BUNDLE_Z0 = PAN_TOP + 0.8                    # bundle bottom (as the CAD lanes)
EXIT_S = -30.0                               # every tail ends 30 mm past the box edge (as the CAD stubs)
LOOP_Y, LOOP_Z = -28.0, 30.0                 # LOGIC out-and-back loops turn here, over the other tails
JUMP_Z = S.LOGIC['z_d'] - 12.0               # LOGIC direct jumpers under the deck (over the bundles, under the cavities)
FRAME = {'LOGIC': ('x', 'y'), 'POWER': ('y', 'x')}     # (lateral axis, along axis); every exit is toward - along


def r_sup(od):
    """Centre-line bend radius where the wire is tied into its bundle: 3 x OD inside (FAA AC 43.13-1B 11-96)."""
    return max(3.0 * od + od / 2, 4.0)


def r_free(od):
    return 10.0 * od + od / 2


def pt(box, lat, along, z):
    return (lat, along, z) if FRAME[box][0] == 'x' else (along, lat, z)


def pack_u(members, wd):
    """Pack the wires into the exit's U-notch (round bottom of width wd on the pan floor, straight sides, open top): each wire,
    first joiner first, goes to the lowest free spot (then the most central), 0.2 mm off the notch and 0.15 off the next wire.
    Returns the top of the stack (z)."""
    zc, rn = PAN_TOP + wd / 2, wd / 2 - 0.2
    placed = []
    for m in members:
        r = m['od'] / 2
        best = None
        for iz in range(0, 400):
            z = PAN_TOP + 0.2 + r + iz * 0.1
            for il in range(0, int(rn * 20) + 1):
                for sgn in ((1,) if il == 0 else (1, -1)):
                    u = sgn * il * 0.05
                    inside = (abs(u) + r <= rn) if z >= zc else (math.hypot(u, z - zc) + r <= rn)
                    if not inside:
                        continue
                    if any(math.hypot(u - u2, z - z2) < r + r2 + 0.15 for (u2, z2, r2) in placed):
                        continue
                    best = (u, z)
                    break
                if best:
                    break
            if best:
                break
        m['slot'] = best
        placed.append((best[0], best[1], r))
    return max(z + r for (u, z, r) in placed)


def pack(members, width=None):
    """members (sorted: first joiner first) -> slot (lateral offset, z) for each, rows bottom-up; the first joiners lie lowest,
    so a later wire always comes down on top. Inside a row the slots follow the cavities' lateral order (fewer crossings).
    width: the exit notch (the bundle stacks higher rather than wider than its notch)."""
    ods = [m['od'] for m in members]
    W = max(width if width else 1.25 * bundle_d(sorted(ods, reverse=True)), max(ods))
    rows, cur, wsum = [], [], 0.0
    for m in members:
        if cur and wsum + m['od'] + 0.25 > W:
            rows.append(cur)
            cur, wsum = [], 0.0
        cur.append(m)
        wsum += m['od'] + 0.25
    if cur:
        rows.append(cur)
    z = BUNDLE_Z0
    for row in rows:
        h = max(m['od'] for m in row)
        row.sort(key=lambda m: m['lat_c'])
        width = sum(m['od'] + 0.25 for m in row) - 0.25
        u = -width / 2
        for m in row:
            m['slot'] = (u + m['od'] / 2, z + m['od'] / 2)
            u += m['od'] + 0.25
        z += h + 0.25
    return z - BUNDLE_Z0                    # bundle height


def riser(box, m, L0, z_d):
    """Cavity -> straight down -> one bend toward the exit, easing sideways into its slot -> 30 mm past the box edge."""
    R = r_sup(m['od'])
    dl, zs = m['slot']
    lat_c, s_c = m['lat_c'], m['s_c']
    k = max(3.0 * R, 10.0)
    s2 = max(s_c - k, EXIT_S + 6.0)
    return [pt(box, lat_c, s_c, z_d - 0.2), pt(box, lat_c, s_c, zs), pt(box, L0 + dl, s2, zs), pt(box, L0 + dl, EXIT_S, zs)], R


def seg_pt_dist(a, b, p):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(ax + t * dx - p[0], ay + t * dy - p[1])


def strip_blocks():
    """Plan rectangles (x0, y0, x1, y1) a LOGIC jumper at JUMP_Z cannot pass: each strip with its jumper lugs (palm to the
    sleeve on the input line), as the build places them."""
    out = []
    for col, (cx, fuses) in S.MINI_COLS.items():
        sd = S.MINI_IN[col]
        xin = cx + sd * 3.0
        xpm = xin + sd * S.JLUG['ax']
        face = xpm + sd * S.JLUG['t'] / 2
        y0, y1 = S.STRIP_Y[col]
        out.append((min(face, face + sd * S.STRIP['t']), y0, max(face, face + sd * S.STRIP['t']), y1))      # the strip
        for i, (nm, amps) in enumerate(fuses):                                                            # each jumper lug
            if amps and i < S.STUDS[col]:
                y = S.MINI_Y0 + i * S.MINI['pitch']
                xs = (face, xin - sd * S.JLUG['sleeve'] / 2)
                out.append((min(xs), y - S.JLUG['ring'] / 2, max(xs), y + S.JLUG['ring'] / 2))
    return out


def direct_jumper(a, b, od, risers):
    """LOGIC fuse -> relay (no strip in between): under the deck at JUMP_Z, the dog-leg with the fewest riser hits."""
    cands = [[a, b], [a, (b[0], a[1]), b], [a, (a[0], b[1]), b]]
    y0, y1 = min(a[1], b[1]) - 25.0, max(a[1], b[1]) + 25.0
    x0, x1 = min(a[0], b[0]) - 25.0, max(a[0], b[0]) + 25.0
    for k in range(int(y1 - y0) * 2 + 1):            # a dog-leg along y, every 0.5 mm
        ym = y0 + 0.5 * k
        cands.append([a, (a[0], ym), (b[0], ym), b])
    for k in range(int(x1 - x0) * 2 + 1):            # or along x
        xm = x0 + 0.5 * k
        cands.append([a, (xm, a[1]), (xm, b[1]), b])
    for i in range(0, int(x1 - x0) + 1, 2):          # two dog-legs (x then y), 2 mm grid
        for j in range(0, int(y1 - y0) + 1, 2):
            xm, ym = x0 + i, y0 + j
            cands.append([a, (xm, a[1]), (xm, ym), (b[0], ym), b])
            cands.append([a, (a[0], ym), (xm, ym), (xm, b[1]), b])
    best = None
    blocks = strip_blocks()
    R = r_sup(od)
    for c in cands:
        segs = [math.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1]) for i in range(len(c) - 1)]
        if min(segs) < 0.01:
            continue
        hits = 1000 if any(L_ < 2 * R + 0.5 for L_ in segs) else 0     # every bend needs its room (3 x OD): two bends per segment
        for i in range(len(c) - 1):                  # the copper strips stand up to z 31.3, above JUMP_Z: no crossing them
            (xa, ya), (xb, yb) = c[i], c[i + 1]
            n = int(max(abs(xb - xa), abs(yb - ya)) / 0.5) + 1
            if any(bx0 - od / 2 - 0.3 < xa + (xb - xa) * t / n < bx1 + od / 2 + 0.3 and by0 - od / 2 - 0.3 < ya + (yb - ya) * t / n < by1 + od / 2 + 0.3
                   for t in range(n + 1) for (bx0, by0, bx1, by1) in blocks):
                hits += 100
                break
        for (p, odp) in risers:
            if math.hypot(p[0] - a[0], p[1] - a[1]) < 0.5 or math.hypot(p[0] - b[0], p[1] - b[1]) < 0.5:
                continue
            for i in range(len(c) - 1):
                if seg_pt_dist(c[i], c[i + 1], p) < (od + odp) / 2 + 0.3:
                    hits += 1
                    break
        L = sum(math.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1]) for i in range(len(c) - 1))
        if any(not (7.0 <= x_ <= S.LOGIC['L'] - 7.0 and 7.0 <= y_ <= S.D - 7.0) for (x_, y_) in c):
            continue                                  # stays inside the box
        if best is None or (hits, L) < best[0]:
            best = ((hits, L), c)
    (hits, _), c = best
    z_d = S.LOGIC['z_d']
    pts = [(a[0], a[1], z_d - 0.2)] + [(x, y, JUMP_Z) for (x, y) in c] + [(b[0], b[1], z_d - 0.2)]
    return pts, hits


def main():
    wires, doubles = plan()
    per_box = collections.Counter()
    for w in wires:
        for e in w['ends']:
            if e['box']:
                per_box[e['box']] += 1
    strip_x = {c: S.MINI_COLS[c][0] for c in S.MINI_COLS}
    ZD = {'LOGIC': S.LOGIC['z_d'], 'POWER': S.POWER['z_d']}
    # ---- classify: LOGIC internal wires that must cross a strip loop out of the front exit and back in
    for w in wires:
        ats = [e for e in w['ends'] if e.get('at')]
        w['ats'] = ats
        w['loop'] = w['direct'] = False
        if w['kind'] == 'internal' and len(ats) == 2 and all(e['box'] == 'LOGIC' for e in ats):
            xs = sorted(e['at']['x'] for e in ats)
            crosses = any(xs[0] < sx < xs[1] for sx in (strip_x['BUS1'] + 6.0, strip_x['BUS2'] - 6.0))
            w['loop'], w['direct'] = crosses, not crosses
    # ---- lane members (one per wire end that leaves through an exit)
    lanes = collections.defaultdict(list)
    for w in wires:
        if w['direct']:
            continue
        for e in w['ats']:
            if e['at']['lane'] is None:
                continue
            box = e['box']
            lat_ax, al_ax = FRAME[box]
            lanes[(box, e['at']['lane'][1])].append(dict(wire=w['wire'], od=w['od'], end='%s %s' % (e['id'], e['cav']), box=box,
                                                        lat_c=e['at'][lat_ax], s_c=e['at'][al_ax]))
    cad = json.load(open(CAD_REPORT, encoding='utf-8'))
    cad_lanes = {(b, round(l['at'], 2)): l for b, L in cad['lanes'].items() for l in L}
    exits, box_paths = [], collections.defaultdict(list)
    for (box, L0), ms in sorted(lanes.items()):
        ms.sort(key=lambda m: -m['s_c'])                 # farthest from the exit joins first (lowest slots)
        d = bundle_d(sorted([m['od'] for m in ms], reverse=True))
        c = cad_lanes.get((box, round(L0, 2)))
        cad_d = c['d'] if c else None
        opening = round(cad_d + 1.6, 2) if cad_d else None
        top = pack_u(ms, opening) if opening else BUNDLE_Z0 + pack(ms)
        wall_top = ZD[box] + S.PAN['over']            # the notch is open up to the pan wall top
        exits.append(dict(box=box, lane=L0, wires=len(ms), d=round(d, 2), stack_top=round(top, 2), pan_wall_top=wall_top, deck=ZD[box],
                          cad_wires=c['wires'] if c else 0, cad_d=cad_d, opening=opening, margin=round(opening - d, 2) if opening else None,
                          fits=bool(opening and top <= ZD[box] - 1.0), what=[m['end'] for m in ms]))
        for m in ms:
            pts, R = riser(box, m, L0, ZD[box])
            box_paths[m['wire']].append(dict(box=box, lane=L0, slot=m['slot'], pts=pts, R=R, end=m['end']))
    # ---- LOGIC loops: join the two tails with a U over the other tails, outside the front edge
    for w in wires:
        if not w['loop']:
            continue
        a, b = box_paths[w['wire']]
        pa, pb = a['pts'], b['pts']
        za, zb = pa[-1][2], pb[-1][2]
        xa, xb = pa[-1][0], pb[-1][0]
        ease = lambda p_: (p_[0], max(p_[1], -10.0), p_[2])        # the easing point stays inside -10, the U starts at -18
        u = [(xa, -18.0, za), (xa, LOOP_Y, LOOP_Z), (xb, LOOP_Y, LOOP_Z), (xb, -18.0, zb)]
        box_paths[w['wire']] = [dict(box='LOGIC', lane=[a['lane'], b['lane']], R=a['R'], loop=True,
                                     pts=pa[:2] + [ease(pa[2])] + u + [ease(pb[2])] + list(reversed(pb[:2])))]
    # ---- LOGIC direct jumpers under the deck
    risers = []
    used = {}
    for w in wires:
        for e in w['ats']:
            if e['box'] == 'LOGIC':
                used[(e['at']['x'], e['at']['y'])] = w['od']
    risers += [((x, y), od) for (x, y), od in used.items()]
    for col, (cx, fuses) in S.MINI_COLS.items():            # the 14 AWG input jumpers (CAD), one per stud with a fuse
        for i, (nm, amps) in enumerate(fuses):
            if amps and i < S.STUDS[col]:
                risers.append(((cx + S.MINI_IN[col] * 3.0, S.MINI_Y0 + i * S.MINI['pitch']), OD[S.JUMPER_AWG]))
    jumper_hits = {}
    for w in wires:
        if not w['direct']:
            continue
        a, b = w['ats']
        pts, hits = direct_jumper((a['at']['x'], a['at']['y']), (b['at']['x'], b['at']['y']), w['od'], risers)
        jumper_hits[w['wire']] = hits
        box_paths[w['wire']] = [dict(box='LOGIC', lane=None, pts=pts, R=r_sup(w['od']), direct=True)]
    for w in wires:
        w['box_paths'] = box_paths.get(w['wire'], [])
        w.pop('ats', None)
    res = dict(per_box_wire_ends=per_box, kinds=collections.Counter(w['kind'] for w in wires), wires=wires, doubles=doubles,
               loops=[w['wire'] for w in wires if w['loop']], direct=jumper_hits, exits=exits,
               constants=dict(EXIT_S=EXIT_S, BUNDLE_Z0=BUNDLE_Z0, LOOP_Y=LOOP_Y, LOOP_Z=LOOP_Z, JUMP_Z=JUMP_Z))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1, default=list)
    print('wire ends per box:', dict(per_box), '| wires:', dict(res['kinds']))
    print('LOGIC wires that loop out of the front exit and back in (they cannot cross the strips):', res['loops'])
    print('LOGIC direct jumpers under the deck (riser hits):', jumper_hits)
    for d_ in doubles:
        print('two wires in one terminal: %(box)s %(cavity)s %(wires)s = %(mm2)s mm2 in %(part)s range %(range)s over=%(over)s' % d_)
    for x in exits:
        print('exit %-5s lane %6.2f: %2d wires (round bundle d %.1f) | notch %s wide (CAD %s wires) | packed in the U: top z %.1f, deck %.1f -> %s' % (
            x['box'], x['lane'], x['wires'], x['d'], x['opening'], x['cad_wires'], x['stack_top'], x['deck'], 'fits' if x['fits'] else 'DOES NOT FIT'))
    print('wrote', os.path.relpath(OUT, REPO))


if __name__ == '__main__':
    main()
