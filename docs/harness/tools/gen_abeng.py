"""harness.design copy of ST185-AB-engine = the ECU harness, engine-bay half, file "ST185-AB-engine Rev K" (Rev K 2026-11-12: Dan's 2026-11-12 editor save - his part spots, drops and overall routes, every sensor on its own spur, and every AB-engine length from the tree; the knock and coolant pressure sensors on their spots (A6 b / A8 b); the A/C pressure switch feed no longer passes through; library sync (#664 / #665); view only, edited in place 2026-11-12: the CAN-Lambda CAN cable and its CAN H / CAN L splices drawn by the CAN-Lambda, Dan A14 a; Rev J 2026-11-11: splice ends on 25 mm stubs, Dan T7 b, and one ghost strand per other harness, Dan T4 a; Rev I 2026-11-10: the CAN-Lambda end terminator is a bare 120 ohm resistor behind its plug, Dan S6 b; Rev H 2026-11-10: Dan's W4 c editor save - his part spots and overall routes, every sensor on its own spur off a shared branch, intake sensor branch added; Rev G 2026-11-09: route redraw, Dan Z10 b - 5 straight lines, each device breaks out of its nearest line, starter S on line 2; Rev F 2026-11-09: starter on the turbo-speed branch, Dan Y7 b; Rev E 2026-11-09: labels #569, screen-end drawing #593, CAN-Lambda end #597) (viewer only; the
master is the source). Usage: python gen_abeng.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8,
get_part_library). Writes <out>/abeng.json (whole document, wires not yet routed) and <out>/abeng_lib_ops.json (part-library
add ops); then route it: python genroute.py <out>/abeng.json <out>/abeng_final.json. Same rules and helpers' shape as
gen_engc.py (README "harness.design"): connectors 240 wide, each pin its own master end text, display stripes on +12 V wires,
parts from library 5LO8 (new ones from harness-parts.csv), formboard layout, compact schematic (bulkhead, splices, cables,
devices). Lengths: the Route 16 tree of `route_trees` alone (DECISIONS B8; HeavyDC has its own layout-tree segments since B6 b,
OPEN-ITEMS row 179), checked here against the master est_length_mm. gen_engc.py runs on import, so its helpers are not
imported."""
import sys, os, json, re, collections, math, csv, copy
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
import genroute
H = B.Harness('ST185-harness')
NAME, TITLE, REV, DATE = 'AB-engine', 'ST185-AB-engine', 'K', '2026-11-12'
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
W = [r for r in ROWS if r['wire_id']]
assert not [r['wire_id'] for r in W if B.is_integral(r) or any(B.ring_signal(r, s) for s in ('from', 'to'))], 'AB-engine has an INTEGRAL link or a fuse-box ring terminal now: draw it as gen_heavydc.py / gen_cabin.py do (no length check, the ring carries its bar signal, Dan N55 a / N64 a)'
# OEM splice notes (README "Pin text", Dan 2026-11-04 Y6): AB-engine has no factory-lead end today (every wire ends at a new
# plug or the bulkhead), so it gets none; one that appears must be drawn with its "Splice to OEM wire" note as gen_engc.py does
assert not [r['wire_id'] for r in W if B.oem_splices(r)], 'AB-engine has an OEM splice now: draw its factory lead and note as gen_engc.py does'
SPARE = [r for r in ROWS if not r['wire_id']]
PASS = [r for r in ALL if r['harness'] != NAME and NAME in (r.get('passes_through') or '')]
PARTS_CSV = {p['part_number']: p for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8'))}
LIB = json.load(open(os.path.join(OUT, 'lib.json')))['parts']
for k in ('lockParts', 'contactParts', 'connectorParts', 'cableParts', 'wireParts', 'spliceParts', 'cavityPlugParts'): LIB.setdefault(k, [])
def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
def col(c): return c if c in COLORS else "Gray"
# display stripes on +12 V wires, one per circuit (README "Display stripes"; tracing only, the master stays plain red). Cable
# cores keep their cable part's colours (a core's colour comes from its CablePart), so only loose red wires are striped.
STRIPE = {'INJ': ('Blue', 'injector feed'), 'COP': ('White', 'coil feed'), 'SW12': ('Green', 'switched +12 V (boost solenoid, flex fuel)'),
          'LAM': ('Violet', 'CAN-Lambda feed'), 'STR': ('Orange', 'starter S'), 'REV': ('Pink', 'reverse switch feed'),
          'EPSEN': ('Gray', 'steering pump enable')}

# ------------------------------------------------------------------ the tree: Route 16 alone (DECISIONS B8, row 179)
RAW = B.load(H.p['layout'])
LT = json.loads(json.dumps(RAW)); LT['route_trees'] = [s for s in RAW['route_trees'] if s['harness'] == NAME]
assert len(LT['route_trees']) == 1
_n0 = len(LT['segments']); B.add_route_trees(LT)
TREE = LT['segments'][_n0:]
tadj = collections.defaultdict(list)
for a, b, mm in TREE: tadj[a].append((b, mm)); tadj[b].append((a, mm))
assert len(TREE) == len(tadj) - 1, 'the AB-engine route tree is not a tree'
STUB = RAW.get('end_allowance_mm', 100)
SPL = RAW.get('splice_allowance_mm', STUB)     # a splice end's allowance (Dan T7 b, 2026-11-10: 25 mm; strip and solder)
def tpath(a, b):
    prev, todo = {a: None}, [a]
    while todo:
        n = todo.pop(0)
        for m, _ in tadj[n]:
            if m not in prev: prev[m] = n; todo.append(m)
    assert b in prev, (a, b)
    out = [b]
    while out[-1] != a: out.append(prev[out[-1]])
    return out[::-1]
def seglen(a, b): return next(mm for m, mm in tadj[a] if m == b)
def troute(r):
    p = tpath(H.place(r, 'from'), H.place(r, 'to'))
    return p, sum(seglen(x, y) for x, y in zip(p, p[1:])) + sum(SPL if r[e + '_type'] == 'splice' and not B.STUD_SPLICE.match(r[e + '_id']) else STUB for e in ('from', 'to'))

# ------------------------------------------------------------------ parts (library wins; new = from harness-parts.csv)
doc_parts, lib_add, missing = collections.defaultdict(dict), [], set()
ACC = {'LockPart': 'lockParts', 'ContactPart': 'contactParts', 'CavityPlugPart': 'cavityPlugParts', 'MountPart': 'mountParts',
       'CavitySealPart': 'cavitySealParts', 'BootPart': 'bootParts', 'CoveringPart': 'coveringParts'}
def use_lib(kind, part):
    doc_parts[kind][part['id']] = json.loads(json.dumps(part))
    for cfg in part.get('configurations', []):
        for a in cfg.get('accessories', []):
            ap = next((p for p in LIB[ACC[a['type']]] if p['id'] == a['partId']), None)
            assert ap, (part['id'], a)
            doc_parts[ACC[a['type']]][ap['id']] = json.loads(json.dumps(ap))
    return part['id']
# parts not yet in library 5LO8: the shape here, maker and description from harness-parts.csv (README "Parts"); an
# accessory names the part number it points at and gets the library's own id
NEW = {'AW2S': ('lockParts', {"id": "lp_aw2s"}),
       'AT62-201-1631': ('contactParts', {"id": "ct_at62_201_1631", "type": "Crimp", "gender": "Socket", "contactColor": "Gold",
                                          "minGauge": {"unit": "AWG", "value": 20}, "maxGauge": {"unit": "AWG", "value": 16}}),
       'AT06-2S-RD01': ('connectorParts', {"id": "cp_at06_2s_rd01", "gender": "Female", "hasShell": False, "numberOfCavities": 2,
                                           "color": "Gray", "_acc": [('LockPart', 'AW2S'), ('ContactPart', 'AT62-201-1631')]}),
       'AT04-2P-R120YEL': ('connectorParts', {"id": "cp_at04_2p_r120yel", "gender": "Male", "hasShell": False, "numberOfCavities": 2,
                                              "color": "Yellow"}),
       '354404': ('connectorParts', {"id": "cp_lowdoller_354404", "hasShell": False, "numberOfCavities": 3}),
       '90980-11250': ('connectorParts', {"id": "cp_toy_90980_11250", "gender": "Female", "hasShell": False, "numberOfCavities": 2}),
       '90980-11400': ('connectorParts', {"id": "cp_toy_90980_11400", "gender": "Female", "hasShell": False, "numberOfCavities": 1}),
       '5-965906-1': ('contactParts', {"id": "ct_5_965906_1", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                       "minGauge": {"unit": "AWG", "value": 20}, "maxGauge": {"unit": "AWG", "value": 18}}),
       # a Toyota repair wire: a sealed TS 2.3 socket on a lead, like the library's 82998-12500
       '82998-12440': ('contactParts', {"id": "ct_82998_12440", "type": "Crimp", "gender": "Socket", "contactColor": "Silver"}),
       # the CAN bus end 120 ohm resistor soldered across the CAN-Lambda splices (Dan S6 b, 2026-11-10)
       '120R 1/4W': ('resistorParts', {"id": "rp_120r"})}
def lib_pn(kind, pn): return next((p for p in LIB[kind] if p.get('partNumber') == pn), None)
def part_id(kind, pn):
    """library part id for this part number (a NEW part is added from harness-parts.csv); None for TBD / kit / unknown."""
    if not pn or pn.upper().startswith('TBD') or pn.startswith(('factory', 'in kit', 'pigtail', 'solder splice onto')): return None
    p = lib_pn(kind, pn)
    if p: return use_lib(kind, p)
    if pn not in NEW or pn not in PARTS_CSV: missing.add((kind, pn)); return None
    k, shape = NEW[pn]; assert k == kind, (pn, k, kind)
    c = PARTS_CSV[pn]
    p = {x: v for x, v in shape.items() if x != '_acc'}
    p.update(partNumber=pn, manufacturer=c['manufacturer'], description=c['description'])
    if shape.get('_acc'):
        acc = []
        for i, (ty, apn) in enumerate(shape['_acc']):
            aid = part_id(ACC[ty], apn); assert aid, apn
            acc.append({"id": "%s_cfg%d" % (p['id'], i + 1), "type": ty, "partId": aid})
        p['configurations'] = [{"id": p['id'] + "_cfg", "accessories": acc}]
    LIB[kind].append(p); lib_add.append({"op": "add", "collection": kind, "value": p})
    return use_lib(kind, p)

# ------------------------------------------------------------------ connectors (drawn whole; other-harness cavities N/C + note)
def pkey(p):
    m = re.match(r'(\d+)$', p)
    return (0, int(m.group(1)), '') if m else (1, 0, p)
conn_ids = list(dict.fromkeys(r[s + '_id'] for r in W + SPARE for s in ('from', 'to') if r[s + '_type'] == 'connector'))
use, housing, mates_pn = collections.defaultdict(dict), {}, {}
for r in ALL:
    for s in ('from', 'to'):
        c = r[s + '_id']
        if r[s + '_type'] == 'connector' and c in conn_ids:
            use[c].setdefault(r[s + '_pin'], []).append((r['harness'], r['wire_id'], r, s))
            if r[s + '_housing_pn'] and r[s + '_housing_pn'] != 'TBD': housing.setdefault(c, r[s + '_housing_pn'])
            m = re.search(r'\bmates (?:Amphenol |TE |Deutsch )?([A-Z0-9][A-Z0-9-]+[A-Z0-9])', r[s + '_note'] or '')
            if m and r['harness'] == NAME: mates_pn.setdefault(c, m.group(1))
conns, other_owned = collections.OrderedDict(), collections.defaultdict(list)
for c in conn_ids:
    cpid = part_id('connectorParts', housing.get(c))
    cpart = doc_parts['connectorParts'].get(cpid) if cpid else None
    pins = sorted(use[c], key=pkey)
    if cpart and cpart.get('numberOfCavities') and all(re.match(r'\d+$', p) and 1 <= int(p) <= cpart['numberOfCavities'] for p in pins):
        pins = [str(i) for i in range(1, cpart['numberOfCavities'] + 1)]
    if cpart: assert len(pins) == cpart['numberOfCavities'], (c, pins, cpart['numberOfCavities'])
    cfg_contact = cfg_plug = None
    for a in ((cpart or {}).get('configurations') or [{}])[0].get('accessories', []):
        if a['type'] == 'ContactPart' and not a.get('rule') and not cfg_contact: cfg_contact = a['partId']
        if a['type'] == 'CavityPlugPart' and not a.get('rule') and not cfg_plug: cfg_plug = a['partId']
    cavs = []
    for p in pins:
        cv = {"id": "%s.%s" % (sid(c), sid(p)), "designation": p}
        here = [u for u in use[c].get(p, []) if u[0] == NAME]
        mine_w = [u for u in here if u[1]]
        if mine_w:
            r, s = mine_w[0][2], mine_w[0][3]
            ct = part_id('contactParts', r[s + '_terminal_pn'])
            if ct and ct != cfg_contact: cv['contactPartId'] = ct
        else:
            cv['notConnected'] = True
            if here:      # an AB-engine spare: its sealing plug from the master (TBD -> none)
                pl = part_id('cavityPlugParts', here[0][2][here[0][3] + '_terminal_pn'])
                if pl and pl != cfg_plug: cv['cavityPlugPartId'] = pl
            else:
                owners = sorted({B.file_short(u[2]) for u in use[c].get(p, [])})     # the file, "AB-cabin 2" (DECISIONS B6)
                if owners: other_owned[c].append((p, '/'.join(owners))); cv['cavityPlugPartId'] = None
        cavs.append(cv)
    conns[c] = {"id": "c_" + sid(c), "label": c, "cavities": cavs, "width": 240}
    if cpid: conns[c]['partId'] = cpid
cav_of = {(c, cv['designation']): cv['id'] for c, n in conns.items() for cv in n['cavities']}
# a plug-in part the master names as the mate of one of our connectors ("mates Amphenol AT04-2P-R120YEL"): drawn mated to it
mate_conns, mates = collections.OrderedDict(), []
for c, pn in mates_pn.items():
    mp = part_id('connectorParts', pn); n = len(conns[c]['cavities'])
    mc = {"id": "c_%s_MATE" % sid(c), "label": "%s mate" % c, "width": 240,
          "cavities": [{"id": "%s_MATE.%s" % (sid(c), cv['designation']), "designation": cv['designation']} for cv in conns[c]['cavities']]}
    if mp:
        mc['partId'] = mp; assert doc_parts['connectorParts'][mp]['numberOfCavities'] == n, pn
    mate_conns[c] = mc
    mates.append({"id": "m_" + sid(c), "sourceId": conns[c]['id'], "targetId": mc['id']})

# ------------------------------------------------------------------ other ends, wires, cables
splices = collections.OrderedDict()
resistors = collections.OrderedDict()     # a resistor sits inline like a splice (Dan S6 b: the CAN end terminator)
SPLP = {'solder splice': 'GENERIC SOLDER SPLICE', 'crimp splice': 'GENERIC CRIMP SPLICE 14-10'}
spl_pn = collections.defaultdict(set)
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice':
        tp = r[s + '_terminal_pn']; spl_pn[i].add(SPLP.get(tp, tp))
        splices.setdefault(i, {"id": "s_" + sid(i), "label": i})
        return {"id": "s_" + sid(i), "handle": "Splice"}
    if t == 'resistor':
        if i not in resistors:
            resistors[i] = {"id": "r_" + sid(i), "label": i}
            pid = part_id('resistorParts', r[s + '_housing_pn'])
            if pid: resistors[i]['partId'] = pid
        return {"id": "r_" + sid(i), "handle": "Left" if p == '1' else "Right"}
    if t == 'cable screen': return None      # the screen floats at that end
    raise SystemExit('end type %r (%s): add it to gen_abeng.py' % (t, r['wire_id']))
wires, cables, row_of = [], collections.OrderedDict(), {}
for r in W:
    a, b = end(r, 'from'), end(r, 'to')
    row_of[r['wire_id']] = r
    if r['cable']:
        cab = cables.setdefault(r['cable'], {"id": "cab_" + sid(r['cable']), "label": r['cable'], "cores": []})
        cp = part_id('cableParts', r['cable_pn'])
        if cp: assert cab.get('partId', cp) == cp, r['cable']; cab['partId'] = cp
        co = {"id": "co_" + sid(r['wire_id']), "color": col(r['colour'])}
        for k, e in (('source', a), ('target', b)):
            if e: co[k] = e
        if r['colour'] == 'Shield':
            if 'source' not in co: co['source'] = co.pop('target')      # a screen with one end: that end is its source
            assert 'shield' not in cab, r['cable']; cab['shield'] = co
        else: assert a and b, r['wire_id']; cab['cores'].append(co)
        continue
    w = {"id": "w_" + sid(r['wire_id']), "source": a, "target": b, "color": col(r['colour']), "identLabel": r['wire_id']}
    wp = part_id('wireParts', r['wire_pn'])
    if wp: w['partId'] = wp
    if r['colour'] == 'Red': w['stripeColor'] = STRIPE[r['circuit_id']][0]   # a new +12 V circuit needs a STRIPE entry
    wires.append(w)
for i, pns in spl_pn.items():
    assert len(pns) == 1, (i, pns)
    pid = part_id('spliceParts', pns.pop())
    if pid: splices[i]['partId'] = pid
for c in cables.values():   # core order = the cable part's core order (matched by colour)
    order = [k['color'] for k in doc_parts['cableParts'][c['partId']]['cores']]
    assert sorted(co['color'] for co in c['cores']) == sorted(order), (c['label'], order, [co['color'] for co in c['cores']])
    c['cores'].sort(key=lambda co: order.index(co['color']))
def cseq(c): return c['cores'] + ([c['shield']] if 'shield' in c else [])
CONDS = wires + [co for c in cables.values() for co in cseq(c)]
def lab(cond): return cond.get('identLabel') or cond['id'][3:]
# pin text (Dan 2026-11-01): each end shows its own master end description (device pins say what the pin does; bulkhead and
# splice ends name the device - the master's text)
comp = {n['id']: n for n in conns.values()}
for cond in CONDS:
    r = row_of[lab(cond)]
    for s, k in (('from', 'source'), ('to', 'target')):
        e = end(r, s)
        if e and e['id'] in comp and r[s + '_desc']:
            cv = next(cv for cv in comp[e['id']]['cavities'] if cv['id'] == e['handle'])
            assert not cv.get('signal') or cv['signal'] == r[s + '_desc'], (cv['id'], cv.get('signal'), r[s + '_desc'])
            cv['signal'] = r[s + '_desc']

# ================================================================== schematic: bulkhead, splices, cables, devices right
# README "harness.design" (Dan 2026-11-01 / 11-02 (J1) / 11-03 N1 a): bulkhead near the centre third of the page, splices
# near the bulkhead, devices right of it; each wire horizontal with one 90 degree jog in its own lane; device rows half a grid
# below the bulkhead rows; both columns level at the top.
BHN = 'DRB102-ENGINE'; BH = conns[BHN]; BHID = BH['id']
BH['schematicPosition'] = {"x": 0, "y": 0}
DEV_IDS = {n['id'] for k, n in conns.items() if k != BHN}
NODES = {n['id']: n for n in list(conns.values()) + list(mate_conns.values())}
def h(n): return 30 + 30 * len(n['cavities'])
def cab_h(c): return 30 + 30 * len(cseq(c))
def cav_y(n, handle): return n['schematicPosition']['y'] + 30 * ([cv['id'] for cv in n['cavities']].index(handle) + 1) + 15
def ends(cond): return [e for e in (cond.get('source'), cond.get('target')) if e]
cab_of = {co['id']: c for c in cables.values() for co in cseq(c)}
for c in cables.values():
    dv = {e['id'] for co in cseq(c) for e in ends(co) if e['id'] in DEV_IDS}
    assert len(dv) <= 1, (c['label'], dv); c['_dev'] = dv.pop() if dv else None
# a cable with no device end whose every core ends on a splice, and those splices feed one device (the CAN-Lambda CAN pair and
# its CAN H / CAN L splices) is drawn by that device like the other shielded cables (Dan A14 a, 2026-11-12): the cable just
# left of the device column, its splices right of it on its core rows, the resistor between them by them (place_right)
VIA_SPL, VIA_RES, VCAB = {}, {}, collections.defaultdict(list)
for c in cables.values():
    sp = {e['id'] for co in c['cores'] for e in ends(co) if e['id'].startswith('s_')}
    if c['_dev'] or len(sp) != len(c['cores']): continue
    dv = {e['id'] for cond in CONDS for e in ends(cond) if e['id'] in DEV_IDS and any(x['id'] in sp for x in ends(cond))}
    if len(dv) != 1: continue
    c['_via'] = dv.pop(); VCAB[c['_via']].append(c)
    for i in sp: VIA_SPL[i] = c
    for cond in CONDS:
        es = ends(cond)
        for e in es:
            if e['id'].startswith('r_') and any(x['id'] in sp for x in es): VIA_RES[e['id']] = c
used_rows = {cav_y(BH, e['handle']) for cond in CONDS for e in ends(cond) if e['id'] == BHID}
taken, cab_rows = set(), set()
def core_row(c, co): return c['schematicPosition']['y'] + 30 * (cseq(c).index(co) + 1) + 15
# any other cable with no device end sits beside the bulkhead on the nearest run of empty bulkhead rows, so no bulkhead pin's
# wire runs into it; its splices sit on its core rows
CABLX = 240 + 270
for c in [c for c in cables.values() if not c['_dev'] and not c.get('_via')]:
    want = min(cav_y(BH, e['handle']) for co in cseq(c) for e in ends(co) if e['id'] == BHID)
    k = cab_h(c) // 30
    tops = [m for m in range(0, 30 * 104, 30) if not any(m + 30 * j + 15 in used_rows | cab_rows for j in range(k))]
    top = min(tops, key=lambda m: (abs(m + 45 - want), m))
    c['schematicPosition'] = {"x": CABLX, "y": top}
    cab_rows |= {top + 30 * j + 15 for j in range(k)}
LEFT_BOTTOM = h(BH)
SPX = CABLX + 60 + 150
SPX2 = SPX + 120          # a splice fed only by another splice sits right of it, on its row
links = collections.defaultdict(list)
for cond in CONDS:
    es = ends(cond)
    for x in es:
        if x['id'].startswith('s_'): links[x['id']].append((cond, x, next((o for o in es if o is not x), None)))
deg = collections.Counter((e['id'], e['handle']) for cond in CONDS for e in ends(cond) if e['id'] == BHID)
def left_row(cond, o):
    """the row a splice's feed comes in on: a bulkhead pin, or the core row of a cable beside the bulkhead"""
    c = cab_of.get(cond['id'])
    if c is not None and not c['_dev']: return core_row(c, cond)
    if o and o['id'] == BHID: return cav_y(BH, o['handle'])
    return None
def free_row(want, bad):
    yy = min((v for v in range(15, max(LEFT_BOTTOM, 4000), 30) if v not in bad), key=lambda v: (abs(v - want), v))
    bad.add(yy); return yy
INL = {n['id']: n for n in splices.values()}
pending, col2 = [], set()
for n in [n for n in splices.values() if n['id'] not in VIA_SPL]:      # a splice fed by one left pin (or a core of the bulkhead cable) sits on that row: a straight wire
    st = next((left_row(cond, o) for cond, x, o in links[n['id']] if left_row(cond, o) is not None
               and (cab_of.get(cond['id']) or deg[(o['id'], o['handle'])] == 1) and left_row(cond, o) not in taken), None)
    if st is not None: taken.add(st); n['_row'] = st; n['_x'] = SPX
    else: pending.append(n)
for it in range(6):
    left = []
    for n in pending:
        lys = [left_row(cond, o) for cond, x, o in links[n['id']] if left_row(cond, o) is not None]
        sps = [INL[o['id']] for cond, x, o in links[n['id']] if o and o['id'] in INL and '_row' in INL[o['id']]]
        if lys: n['_row'] = free_row(min(lys), used_rows | taken | cab_rows); taken.add(n['_row']); n['_x'] = SPX
        elif sps and sps[0]['_row'] not in col2: n['_row'] = sps[0]['_row']; col2.add(n['_row']); n['_x'] = SPX2
        elif sps: n['_row'] = free_row(sps[0]['_row'], col2 | used_rows); n['_x'] = SPX2
        else: left.append(n)
    pending = left
assert not pending, [n['label'] for n in pending]
for n in splices.values():
    if n['id'] not in VIA_SPL: n['schematicPosition'] = {"x": n.pop('_x'), "y": n.pop('_row') - 15}
for n in [n for n in resistors.values() if n['id'] not in VIA_RES]:      # a resistor between two splices: right of them, on the upper splice's row
    ys = [INL[e['id']]['schematicPosition']['y'] for cond in CONDS for e in ends(cond) if e['id'] in INL
          for o in ends(cond) if o['id'] == n['id']]
    n['schematicPosition'] = {"x": SPX2 + 120, "y": min(ys)}
def row_of_end(e):
    if e['id'] in VIA_SPL or e['id'] in VIA_RES: return None      # placed with their device (A14 a)
    if e['id'] == BHID: return cav_y(BH, e['handle'])
    if e['id'] in INL: return INL[e['id']]['schematicPosition']['y'] + 15
    if e['id'].startswith('r_'): return next(n for n in resistors.values() if n['id'] == e['id'])['schematicPosition']['y'] + 15
    return None
# devices: ordered by the mean row of what feeds them, so lanes cross least (connectors may be reordered, pins never)
bary = collections.defaultdict(list)
for cond in CONDS:
    es = ends(cond)
    for e in es:
        if e['id'] in DEV_IDS:
            bary[e['id']] += [row_of_end(o) for o in es if o is not e and row_of_end(o) is not None]
DEV_ORDER = sorted(DEV_IDS, key=lambda d: (sum(bary[d]) / len(bary[d]) if bary[d] else 10 ** 6, NODES[d]['label']))
RCAB = collections.defaultdict(list)
for c in cables.values():
    if c['_dev']: RCAB[c['_dev']].append(c)
CABR_OFF = 300          # a device's cable sits this far left of the device column, its rows on the bulkhead / splice rows,
MATE_OFF = 270          # half a grid above its device's rows (so cores that change order between cable and plug never overlap)
def place_right(devx):
    y = 15
    for d in DEV_ORDER:
        n = NODES[d]; n['schematicPosition'] = {"x": devx, "y": y}
        cy = y - 15
        for c in RCAB[d]: c['schematicPosition'] = {"x": devx - CABR_OFF, "y": cy}; cy += cab_h(c) + 30
        for c in VCAB[d]:   # A14 a: the cable's first core half a grid above the device pin its splice feeds, the splices on the core rows
            sp0 = next(e for e in ends(c['cores'][0]) if e['id'] in VIA_SPL)['id']
            pin = next(e for cond in CONDS for e in ends(cond) if e['id'] == d and any(x['id'] == sp0 for x in ends(cond)))
            vy = cav_y(n, pin['handle']) - 15 - 45
            c['schematicPosition'] = {"x": devx - CABR_OFF, "y": vy}
            for co in c['cores']:
                s_ = INL[next(e for e in ends(co) if e['id'] in VIA_SPL)['id']]
                s_['schematicPosition'] = {"x": devx - CABR_OFF + 120, "y": core_row(c, co) - 15}
            for rn in resistors.values():
                if VIA_RES.get(rn['id']) is c: rn['schematicPosition'] = {"x": devx - CABR_OFF + 180, "y": vy + cab_h(c) + 30}
            cy = max(cy, vy + cab_h(c) + 30)
        lbl = n['label']
        if lbl in mate_conns: mate_conns[lbl]['schematicPosition'] = {"x": devx + MATE_OFF, "y": y}
        y = max(y + h(n), cy - 15) + 30      # the next device stays on the device rows
    return y - 30
def doc_now():
    return {"connectors": list(conns.values()) + list(mate_conns.values()), "terminals": [], "splices": list(splices.values()),
            "resistors": list(resistors.values()), "wires": wires, "cables": list(cables.values())}
def route_cost(devx):    # (unrouted conductors, conductors that need more than one lane) with the device column at devx
    place_right(devx)
    R_, segs_, res_ = genroute.run(copy.deepcopy(doc_now()))
    return (sum(1 for s in segs_ if res_.get(s['k']) is None), sum(1 for v in res_.values() if v and len(v) > 2))
n_right = sum(1 for cond in CONDS for e in ends(cond) if e['id'] in DEV_IDS and cond['id'] not in cab_of) + \
          sum(1 for c in cables.values() if c['_dev'] for co in cseq(c) for e in ends(co) if e['id'] not in DEV_IDS)
DEVX = (SPX2 + 150 + 30 * n_right + CABR_OFF) // 30 * 30
base = route_cost(DEVX)
print('widest device column x', DEVX, 'routing (unrouted, multi-lane)', base, flush=True)
lo, hi = SPX2 + CABR_OFF + 300, DEVX        # compact (Dan 2026-11-02): the narrowest lane field that routes as cleanly
while hi - lo > 30:
    mid = (lo + hi) // 60 * 30
    if route_cost(mid) <= base: hi = mid
    else: lo = mid
    print('  try', mid, '->', 'ok' if hi == mid else 'worse', flush=True)
DEVX = hi
RIGHT_BOTTOM = place_right(DEVX)
def clear_of(x, y, me, g=30):      # a 30 x 30 node at (x, y) keeps a grid square clear of every other node
    for k in ('connectors', 'splices', 'resistors', 'cables'):
        for o in doc_now()[k]:
            if o['id'] == me or 'schematicPosition' not in o: continue
            ox, oy = o['schematicPosition']['x'], o['schematicPosition']['y']
            ow, oh = (60, cab_h(o)) if k == 'cables' else (30, 30) if k in ('splices', 'resistors') else (o.get('width', 150), h(o))
            if x - g < ox + ow and ox - g < x + 30 and y - g < oy + oh and oy - g < y + 30: return False
    return True
for rn in resistors.values():     # the resistor's spot: the nearest free spot by its splices where every conductor routes
    y0, best = rn['schematicPosition']['y'], None
    x0, dxs = (rn['schematicPosition']['x'], (0, -60, 60)) if rn['id'] in VIA_RES else (SPX2 + 120, (0, -120, 120, 240))
    for dx in dxs:
        for dy in (0, -60, 60, -90, 90, -120, 120, -180, 180):
            if rn['id'] in VIA_RES and not clear_of(x0 + dx, y0 + dy, rn['id']): continue
            rn['schematicPosition'] = {"x": x0 + dx, "y": y0 + dy}
            R_, segs_, res_ = genroute.run(copy.deepcopy(doc_now()))
            c = (sum(1 for s in segs_ if res_.get(s['k']) is None), sum(1 for v in res_.values() if v and len(v) > 2), abs(dx) + abs(dy))
            if best is None or c < best[0]: best = (c, dict(rn['schematicPosition']))
    rn['schematicPosition'] = best[1]
    print('resistor', rn['label'], 'at', best[1], 'routing (unrouted, multi-lane, offset)', best[0], flush=True)
print('device column x', DEVX, 'bottom', RIGHT_BOTTOM, '| bulkhead bottom', LEFT_BOTTOM, flush=True)

# ------------------------------------------------------------------ notes
notes, right_notes = [], []
spares = collections.defaultdict(list)
for r in SPARE: spares[r['from_id']].append((r['from_pin'], r['from_terminal_pn']))
BOX_SEATS = set(B._seat_map()) | {'LOGIC'}     # box guts are not drawn (Dan R1 a): no spare / N/C notes for box seats
for c in conns:
    if c in BOX_SEATS: continue
    txt = []
    if spares.get(c):
        by = collections.defaultdict(list)
        for p, pl in spares[c]: by[pl if pl and pl != 'TBD' else 'TBD'].append(p)
        txt.append('%s: %s %s (sealing plug from the master: %s).' % (
            c, ('pins %s are' if len(spares[c]) > 1 else 'pin %s is') % ', '.join(sorted((p for p, _ in spares[c]), key=pkey)),
            'AB-engine spares' if len(spares[c]) > 1 else 'an AB-engine spare',
            '; '.join('%s %s' % (k, ', '.join(sorted(v, key=pkey))) for k, v in sorted(by.items()))))
    if other_owned.get(c):
        by = collections.defaultdict(list)
        for pin, own in other_owned[c]: by[own].append(pin)
        txt.append('N/C cavities belong to other harnesses - ' + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(by.items())))
    if txt:
        nt = {"id": "n_" + sid(c), "text": ' '.join(txt), "width": 360}
        (notes if c == BHN else right_notes).append((nt, conns[c]))
for sname, sp in splices.items():     # a splice shared with another harness file: its R10 note (DECISIONS B6 R10)
    t = B.r10_note(sname, TITLE)
    if t:
        right_notes.append(({"id": "n_" + sid(sname), "width": 360,
                             "text": '%s (the splice is drawn here with its AB-engine legs only).' % t[:-1]}, sp))
for c, mc in mate_conns.items():
    pn = mates_pn[c]
    notes.append(({"id": "n_mate_" + sid(c), "width": 360, "text": "%s takes the plug-in %s (%s, %s), drawn mated to it; it carries no "
                   "wires (master note on %s)." % (c, pn, PARTS_CSV.get(pn, {}).get('manufacturer', '?'),
                                                   PARTS_CSV.get(pn, {}).get('description', '?'), c)}, None))
used_st = sorted({row_of[w['identLabel']]['circuit_id'] for w in wires if 'stripeColor' in w}, key=list(STRIPE).index)
head = [{"id": "n_title", "width": 360,
         "text": TITLE + " Rev " + REV + " (" + DATE + "): the ECU harness, engine-bay half (DRB102-ENGINE to every engine sensor and "
                 "actuator, CAN-Lambda with its bare 120 ohm end resistor behind the plug (Dan S6 b), MR-S plugs B / C, starter S). Viewer copy generated from "
                 "docs/harness/MASTER-wirelist.csv (harness = AB-engine) by docs/harness/tools/gen_abeng.py; never a source. Schematic: "
                 "bulkhead in the centre third, splices beside it, shielded cables by their device, devices right in feed order, columns "
                 "level at the top (device rows half a grid lower, N1 a). Each pin shows its own master end text. Connectors are drawn "
                 "whole; spare cavities are N/C with a note. " + B.GHOST_MARK +
                 "Layout: a formboard of the Route 16 tree (route_trees, Dan's 2026-11-12 save; the bulkhead 16 in above where the trunk meets the firewall), "
                 "straight orthogonal bundles, front of car RIGHT, rear LEFT, driver side UP; drawn length is not to scale; each part on "
                 "a 100 mm end-allowance stub (a splice on a 25 mm stub, Dan T7 b); bundle lengths = the master est_length_mm (HeavyDC's cables are on its own segments of "
                 "the layout tree, DECISIONS B6 b)."},
        {"id": "n_stripes", "width": 360,
         "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                 "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) +
                 ". Red cable cores keep their cable's colours."}]
# the bulkhead sits in the centre third of the page (J1): the notes fill the left third
RIGHT_EDGE = DEVX + (MATE_OFF if mate_conns else 0) + 240
if right_notes: RIGHT_EDGE = max(RIGHT_EDGE, DEVX + MATE_OFF * (2 if mate_conns else 1) + 360)
lefts = head + [n for n, _ in notes]
LEFT_EDGE = min(-390 * len(lefts), (3 * 0 - RIGHT_EDGE) // 2 // 30 * 30)
step = (-30 - 360 - LEFT_EDGE) // max(1, len(lefts) - 1) // 30 * 30 if len(lefts) > 1 else 0
for i, n in enumerate(lefts): n['schematicPosition'] = {"x": LEFT_EDGE + step * i, "y": -390 if n in head else 0}
if right_notes:      # one note right of the device column for every device-side note (separate ones would stack and overlap)
    right_notes = [({"id": "n_devices", "width": 360, "text": ' '.join(n['text'] for n, _ in right_notes),
                     "schematicPosition": {"x": DEVX + MATE_OFF * (2 if mate_conns else 1), "y": min(a['schematicPosition']['y'] for _, a in right_notes)}}, None)]
NOTES = lefts + [n for n, _ in right_notes]
print('schematic width %d .. %d, bulkhead at %.0f%% .. %.0f%%' % (LEFT_EDGE, RIGHT_EDGE, 100 * (0 - LEFT_EDGE) / (RIGHT_EDGE - LEFT_EDGE),
                                                                    100 * (240 - LEFT_EDGE) / (RIGHT_EDGE - LEFT_EDGE)))

# ================================================================== layout: the Route 16 tree as a formboard
node_items, inline_at, seen, outward = collections.defaultdict(list), collections.defaultdict(list), set(), {}
for r in W + SPARE:
    for s in ('from', 'to'):
        t = r[s + '_type']
        if not t or t == 'cable screen': continue
        cid = (conns[r[s + '_id']] if t == 'connector' else resistors[r[s + '_id']] if t == 'resistor' else splices[r[s + '_id']])['id']
        if cid in seen: continue
        nd = H.place(r, s); assert nd in tadj, (r['wire_id'], s, nd)
        seen.add(cid); (node_items if cid[:2] == 'c_' else inline_at)[nd].append(cid)
segs, hroute = collections.Counter(), {}
for r in W:
    p, mm = troute(r); hroute[r['wire_id']] = mm
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
tree_nodes = {n for k in segs for n in k} | set(node_items) | set(inline_at)
adj = collections.defaultdict(list)
for a, b, mm in TREE:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
ROOT = LT['route_trees'][0]['root']
parent, slen, kids = {ROOT: None}, {}, collections.defaultdict(list)
todo = [ROOT]
while todo:
    n = todo.pop(0)
    for m, mm in adj[n]:
        if m not in parent: parent[m] = n; slen[m] = mm; kids[n].append(m); todo.append(m)
assert tree_nodes <= set(parent), tree_nodes - set(parent)
first_hop = {}      # child -> the first tree node after its parent on the way to it (tells a line going on from a breakout)
changed = True
while changed:      # fold pass-through nodes into the bundle
    changed = False
    for n in list(parent):
        if parent[n] is None or node_items.get(n) or inline_at.get(n) or len(kids[n]) != 1: continue
        c = kids[n][0]; p = parent[n]
        slen[c] += slen[n]; parent[c] = p; first_hop[c] = first_hop.get(n, n)
        kids[p] = [c if x == n else x for x in kids[p]]
        del parent[n], slen[n], kids[n]; changed = True; break
for n in [n for n in parent if parent[n] and slen[n] == 0]:   # a 0 mm segment is no bundle: merge its node into its parent
    p = parent[n]
    for c in kids[n]: parent[c] = p
    kids[p] = [x for x in kids[p] if x != n] + kids[n]
    node_items[p] += node_items.pop(n, []); inline_at[p] += inline_at.pop(n, [])
    print('0 mm segment', p, '-', n, ': merged into', p)
    del parent[n], slen[n], kids[n]
# formboard (README "harness.design", Dan 2026-11-02): the tree laid flat on a build table. Straight orthogonal bundles
# on the 30 grid, each branch at 90 degrees; front of the car RIGHT, rear LEFT, driver side UP (each branch heads the way its
# part of the car lies); drawn length is not to scale, every bundle keeps its tree length (= the master's). Each part sits on
# its 100 mm end-allowance stub, combed off the node. Coil and injector breakouts all leave their line on the same side
# (parallel, Dan 2026-11-02 (J1)). A node whose four sides are all taken by bundles combs its parts along the way in.
DV = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}
OPP = {'R': 'L', 'L': 'R', 'U': 'D', 'D': 'U'}
GAP, MINL, ISP, LBL = 60, 150, 60, 240        # clearance, shortest drawn bundle, comb pitch, room for a part's label
ALLC = {x['id']: x for x in list(conns.values()) + list(splices.values()) + list(resistors.values())}
XY = LT['nodes']
def sub_nodes(n): return [n] + [m for k in kids[n] for m in sub_nodes(k)]
def family(c):      # 'COIL' / 'INJ' when c is the breakout of one ignition coil or one injector
    labs = [ALLC[i]['label'].split('-')[0] for m in sub_nodes(c) for i in node_items.get(m, []) + inline_at.get(m, [])]
    return labs[0] if len(labs) == 1 and labs[0] in ('COIL', 'INJ') else None
FAM = {}
def line_of(nd):     # the route line a junction / tap / stub node is on ('J_L7_3', 'T_L7_INJ1' -> 'L7'); None for a device node
    m = re.match(r'[JTS]_([^_]+)', nd); return m.group(1) if m else None
def breakout(n, c):  # c leaves n's line (a breakout) rather than carrying the line on
    return line_of(first_hop.get(c, c)) is None or line_of(first_hop.get(c, c)) != line_of(n)
def heading(n, c):     # screen vector from n towards the middle of c's part of the car (front right, driver up)
    pts = [XY[m]['xy'] for m in sub_nodes(c)]
    x0, y0 = XY[n]['xy']
    return (sum(p[0] for p in pts) / len(pts) - x0, -(sum(p[1] for p in pts) / len(pts) - y0))
def rect(a, b): return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
def hit(r, s, g=GAP): return r[0] - g < s[2] and s[0] - g < r[2] and r[1] - g < s[3] and s[1] - g < r[3]
def mv(p, o): return (p[0] + o[0], p[1] + o[1])
def mvr(r, o): return (r[0] + o[0], r[1] + o[1], r[2] + o[0], r[3] + o[1])
def lay(n, din):
    """n's piece of the tree with n at (0, 0): (rects, node positions, stubs {part id: (node, part xy, stub points, outward)})."""
    free = [d for d in 'RULD' if din is None or d != OPP[din]]
    asg = {}
    for c in sorted(kids[n], key=lambda c: (-len(sub_nodes(c)), breakout(n, c), c)):
        v = heading(n, c); left = [d for d in free if d not in asg.values()]
        assert left, ('more branches than directions at', n)
        fm = family(c) if breakout(n, c) else None
        if fm and FAM.get(fm) in left: asg[c] = FAM[fm]; continue
        asg[c] = max(left, key=lambda d: (DV[d][0] * v[0] + DV[d][1] * v[1]) / (math.hypot(*v) or 1))
        if fm and din and asg[c] != din: FAM.setdefault(fm, asg[c])
    items = node_items.get(n, []) + inline_at.get(n, [])
    rects, P, S = [], {n: (0, 0)}, {}
    ray = [rect((-DV[din][0] * 90, -DV[din][1] * 90), (-DV[din][0] * 10 ** 6, -DV[din][1] * 10 ** 6))] if din else []   # the way in
    if items:
        left = [d for d in free if d not in asg.values()]
        cd = (din if din in left else next(d for d in ('U', 'D', 'R', 'L') if d in left)) if left else OPP[din]
        k, (dx, dy) = len(items), DV[cd]
        if dy == 0:     # a column of parts across the end of a horizontal stub
            ys = [ISP * i - 30 * (k - 1) for i in range(k)]; xj = dx * 90
            for cid, yy in zip(items, ys):
                S[cid] = (n, (dx * 150, yy), [(xj, 0), (xj, yy)] if yy else [], (dx, 0))
            rects += [rect((dx * 90, 0), (dx * 90, 0)), rect((xj, ys[0]), (dx * (150 + LBL), ys[-1]))]
        else:           # parts combed off a vertical spine, to the front (right) side
            for i, cid in enumerate(items):
                yy = dy * (120 + ISP * i); S[cid] = (n, (120, yy), [(0, yy)], (1, 0))
            rects += [rect((0, dy * 90), (0, dy * (120 + ISP * (k - 1)))), rect((0, dy * 90), (120 + LBL, dy * (120 + ISP * (k - 1) + 30)))]
    for c in sorted(kids[n], key=lambda c: (len(sub_nodes(c)), c)):
        d = asg[c]; cr, cp, cs = lay(c, d)
        back = max([-(DV[d][0] * (r[0] if DV[d][0] > 0 else r[2]) + DV[d][1] * (r[1] if DV[d][1] > 0 else r[3])) for r in cr] + [0])
        ln = max(MINL, int(back + GAP + 29) // 30 * 30)
        while True:
            o = (DV[d][0] * ln, DV[d][1] * ln)
            cand = [mvr(r, o) for r in cr] + [rect((DV[d][0] * 90, DV[d][1] * 90), o)]
            if not any(hit(a, b) for a in cand for b in rects + ray): break
            ln += 30
        rects += cand
        P.update({m: mv(q, o) for m, q in cp.items()})
        S.update({cid: (nd, mv(q, o), [mv(p, o) for p in pts], ow) for cid, (nd, q, pts, ow) in cs.items()})
    return rects, P, S
allrects, pos, stubs = lay(ROOT, None)
xs = [r[0] for r in allrects] + [r[2] for r in allrects]
print('formboard width %d .. %d, bulkhead node at %.0f%% of the width' % (min(xs), max(xs), 100 * (pos[ROOT][0] - min(xs)) / (max(xs) - min(xs))))
assert all(v[0] % 30 == 0 and v[1] % 30 == 0 for v in pos.values())
bps = [{"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}} for n in parent]
bundles = []
for n, p in parent.items():
    if p is None: continue
    assert pos[n][0] == pos[p][0] or pos[n][1] == pos[p][1], (p, n)
    bundles.append({"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(slen[n]), "unit": "mm"}})
INL_AT = {}
for cid, (nd, q, pts, ow) in stubs.items():
    b = {"id": "bn_" + cid, "sourceId": "bp_" + sid(nd), "targetId": cid if cid[:2] == 'c_' else "bp_" + cid, "length": {"value": SPL if cid[:2] == "s_" else STUB, "unit": "mm"}}
    if pts: b['layoutPoints'] = [{"id": "%s_p%d" % (b['id'], i), "layoutPosition": {"x": x, "y": y}} for i, (x, y) in enumerate(pts)]
    bundles.append(b)
    ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
    if cid[:2] in ('s_', 'r_'):
        bps.append({"id": "bp_" + cid, "layoutPosition": {"x": q[0], "y": q[1]}}); ALLC[cid]['locationId'] = "bp_" + cid; INL_AT[cid] = "bp_" + sid(nd)
    lbl = ALLC[cid]['label']
    if lbl in mate_conns:    # the plug-in sits against its plug, on the far side of it from the stub
        mate_conns[lbl]['layoutPosition'] = {"x": q[0] + 150 * ow[0], "y": q[1] + 150 * ow[1]}
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
loc = {b['targetId']: (b['sourceId'], b['length']['value']) for b in bundles if b['targetId'][:2] == 'c_'}
loc.update({x['id']: (INL_AT[x['id']], SPL if x['id'][:2] == 's_' else STUB) for x in list(splices.values()) + list(resistors.values())})
def chain(bp):
    out = []
    while bp: out.append(bp); bp = nodepar[bp]
    return out
def dist(b1, b2):
    c1, c2 = chain(b1), chain(b2); common = next(x for x in c1 if x in c2)
    return sum(blen[(nodepar[x], x)] for c in (c1, c2) for x in c[:c.index(common)])

# ================================================================== checks and emit
expect = {lab(w): loc[w['source']['id']][1] + loc[w['target']['id']][1] + dist(loc[w['source']['id']][0], loc[w['target']['id']][0])
          for w in CONDS if 'target' in w}
bad = {k: (v, hroute[k], row_of[k]['est_length_mm']) for k, v in expect.items() if not (v == hroute[k] == int(float(row_of[k]['est_length_mm'] or -1)))}
bad.update({lab(w): (None, hroute[lab(w)], row_of[lab(w)]['est_length_mm']) for w in CONDS if 'target' not in w
            and hroute[lab(w)] != int(float(row_of[lab(w)]['est_length_mm'] or -1))})
assert not bad, 'routed length != tree route != master est_length_mm: %r' % bad
assert sorted(lab(w) for w in CONDS) == sorted(r['wire_id'] for r in W) and len({lab(w) for w in CONDS}) == len(W)
cav_n = collections.Counter((e['id'], e['handle']) for w in CONDS for e in ends(w) if e['id'].startswith('c_'))
cav_m = collections.Counter(("c_" + sid(r[s + '_id']), cav_of[(r[s + '_id'], r[s + '_pin'])]) for r in W for s in ('from', 'to') if r[s + '_type'] == 'connector')
assert cav_n == cav_m and all(v == 1 for v in cav_n.values()), {k: v for k, v in cav_n.items() if v > 1}
NCONN = len(CONDS)
assert NCONN <= 100, 'over the 100-connection plan limit: split by whole circuits into numbered documents (README)'
for c in cables.values(): c.pop('_dev'); c.pop('_via', None)
doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG", "schematic": {"connectorWidth": 240, "terminalWidth": 240},
       "connectors": list(conns.values()) + list(mate_conns.values()), "splices": list(splices.values()),
       "resistors": list(resistors.values()), "wires": wires,
       "cables": list(cables.values()), "mates": mates, "branchPoints": bps, "bundles": bundles, "schematicNotes": NOTES}
for k, v in doc_parts.items():
    if v: doc[k] = list(v.values())
for k in [k for k in doc if doc[k] == []]: del doc[k]
have = {p['id'] for k, v in doc.items() if k.endswith('Parts') for p in v}
refs = {x['partId'] for x in wires + list(splices.values()) + list(resistors.values()) + list(cables.values()) + doc['connectors'] if x.get('partId')} | \
       {cv[k] for n in doc['connectors'] for cv in n['cavities'] for k in ('contactPartId', 'cavityPlugPartId') if cv.get(k)} | \
       {a['partId'] for k, v in doc.items() if k.endswith('Parts') for p in v for c in p.get('configurations', []) for a in c.get('accessories', [])}
assert refs <= have, refs - have
B.relabel(doc, lib=LIB)          # Dan's plain-label rules R1-R9 (2026-11-08), after placement so positions stay
B.box_groups(doc)       # box seat ends as labelled terminals, no box groups, unused parts pruned (Dan R1 a)
NGHOST = B.add_ghosts(doc, H, NAME, strands=True)      # one ghost strand per other harness and path (Dan T4 a: AB-engine is near the limit)
assert NCONN + NGHOST <= 100, 'ghost strands push AB-engine over the 100-connection limit'
B.fill_ghost_note(doc, NAME)      # the title note says which pass-through wires are drawn as ghost strands
json.dump(doc, open(os.path.join(OUT, 'abeng.json'), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'abeng_lib_ops.json'), 'w'), indent=1)
json.dump(expect, open(os.path.join(OUT, 'abeng_expect.json'), 'w'), indent=1)
print('connectors', len(doc['connectors']), 'splices', len(splices), 'wires', len(wires), 'cables', len(cables), 'conductors (connections)', NCONN, '+ ghost strands', NGHOST,
      'bundles', len(bundles), 'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect), 'routed +', NCONN - len(expect),
      'one-ended screens | lib adds', [o['value']['partNumber'] for o in lib_add], '| no library part (left unset):', sorted(missing))
