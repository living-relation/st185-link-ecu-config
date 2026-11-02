"""harness.design copy of ST185-EngineRoom-C (viewer only; the master is the source).
Usage: python gen_engc.py <repo> <out_dir>   (needs <out>/lib_engc.json = a dump of part library 5LO8)
Writes <out>/engc.json, engc_lib_ops.json, engc_expect.json, engc_routes.json."""
import sys, os, json, re, collections, math, csv
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
H = B.Harness('ST185-harness')
NAME = 'EngineRoom-C'
TITLE = 'ST185-EngineRoom-C'
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
W = [r for r in ROWS if r['wire_id']]
SPARE = [r for r in ROWS if not r['wire_id']]
PASS = [r for r in ALL if r['harness'] != NAME and NAME in (r.get('passes_through') or '')]
PARTS_CSV = {p['part_number']: p for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8'))}
LIB = json.load(open(os.path.join(OUT, 'lib_engc.json')))['parts']
def lib_by_pn(kind, pn): return next((p for p in LIB[kind] if p.get('partNumber') == pn), None)
def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
def col(c): return c if c in COLORS else "Gray"

# ------------------------------------------------------------------ parts (library wins; new = from harness-parts.csv)
doc_parts = collections.defaultdict(dict)
lib_add = []
ACC = {'LockPart': 'lockParts', 'ContactPart': 'contactParts', 'CavityPlugPart': 'cavityPlugParts', 'MountPart': 'mountParts',
       'CavitySealPart': 'cavitySealParts', 'BootPart': 'bootParts', 'CoveringPart': 'coveringParts'}
def use_lib(kind, part):
    doc_parts[kind][part['id']] = json.loads(json.dumps(part))
    for cfg in part.get('configurations', []):
        for a in cfg.get('accessories', []):
            k = ACC[a['type']]
            ap = next((p for p in LIB[k] if p['id'] == a['partId']), None)
            assert ap, (part['id'], a)
            doc_parts[k][ap['id']] = json.loads(json.dumps(ap))
    return part['id']
def new_part(kind, part):
    assert part['partNumber'] in PARTS_CSV, part['partNumber']
    c = PARTS_CSV[part['partNumber']]
    part.setdefault('manufacturer', c['manufacturer']); part.setdefault('description', c['description'])
    LIB[kind].append(part); lib_add.append({"op": "add", "collection": kind, "value": part})
    return use_lib(kind, part)
def part_id(kind, pn, maker=None):
    if not pn or pn.upper().startswith('TBD') or pn.startswith('factory'):
        return None
    p = lib_by_pn(kind, pn)
    if p: return use_lib(kind, p)
    if pn not in PARTS_CSV: return None
    return maker(pn) if maker else None
def mk_wire(pn):
    m = re.match(r'J1128-TXL-(\d+)-([A-Z]+)$', pn)
    if m:
        g, c = int(m.group(1)), m.group(2).title()
        return new_part('wireParts', {"id": "j1128_%d_%s" % (g, c.lower()), "color": c, "gauge": {"unit": "AWG", "value": g}, "partNumber": pn})
    m = re.match(r'M22759/16-(\d+)-(\d)$', pn)
    g, c = int(m.group(1)), {'0': 'Black', '2': 'Red', '4': 'Yellow'}[m.group(2)]
    return new_part('wireParts', {"id": "m16_%d_%s" % (g, m.group(2)), "color": c, "gauge": {"unit": "AWG", "value": g}, "partNumber": pn})
def mk_contact(pn):
    if pn == '1-968851-1':
        return new_part('contactParts', {"id": "ct_1_968851_1", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                         "minGauge": {"unit": "AWG", "value": 16}, "maxGauge": {"unit": "AWG", "value": 14}, "partNumber": pn})
    if pn == '2R5':
        return new_part('contactParts', {"id": "ct_klauke_2r5", "type": "Other", "gender": "Socket", "contactColor": "Silver", "partNumber": pn})
    if pn == '82998-12500':
        return new_part('contactParts', {"id": "ct_82998_12500", "type": "Crimp", "gender": "Socket", "contactColor": "Silver", "partNumber": pn})
    raise SystemExit('no maker for contact ' + pn)
def mk_conn(pn):
    assert pn == '90980-10341'
    return new_part('connectorParts', {"id": "cp_toy_90980_10341", "gender": "Female", "hasShell": False, "numberOfCavities": 3, "partNumber": pn})
def mk_splice(pn):
    assert pn == 'D-436-38'
    return new_part('spliceParts', {"id": "spp_d436_38", "partNumber": pn})

# ------------------------------------------------------------------ connectors (drawn whole; other-harness cavities N/C + note)
def pkey(p):
    m = re.match(r'(\d+)$', p)
    return (0, int(m.group(1)), '') if m else (1, 0, p)
RELAY_ORDER = ['30', '85', '86', '87', '87a']
conn_ids = []
for r in W + SPARE:
    for s in ('from', 'to'):
        if r[s + '_type'] == 'connector' and r[s + '_id'] not in conn_ids:
            conn_ids.append(r[s + '_id'])
use = collections.defaultdict(dict)
housing = {}
for r in ALL:
    for s in ('from', 'to'):
        c = r[s + '_id']
        if r[s + '_type'] == 'connector' and c in conn_ids:
            use[c].setdefault(r[s + '_pin'], []).append((r['harness'], r['wire_id'], r, s))
            if r[s + '_housing_pn'] and r[s + '_housing_pn'] != 'TBD': housing.setdefault(c, r[s + '_housing_pn'])
NOPART = {}
conns = collections.OrderedDict(); other_owned = collections.defaultdict(list)
for c in conn_ids:
    hp = housing.get(c)
    cpid = part_id('connectorParts', hp, mk_conn) if hp and c not in NOPART else None
    cpart = doc_parts['connectorParts'].get(cpid) if cpid else None
    pins = sorted(use[c], key=lambda p: (RELAY_ORDER.index(p) if p in RELAY_ORDER else 99, pkey(p)))
    if cpart and cpart.get('numberOfCavities') and all(re.match(r'\d+$', p) and 1 <= int(p) <= cpart['numberOfCavities'] for p in pins):
        pins = [str(i) for i in range(1, cpart['numberOfCavities'] + 1)]
    if cpart: assert len(pins) == cpart['numberOfCavities'], (c, pins, cpart['numberOfCavities'])
    cfg_contact = cfg_plug = None
    if cpart:
        for a in (cpart.get('configurations') or [{}])[0].get('accessories', []):
            if a['type'] == 'ContactPart' and not a.get('rule') and not cfg_contact: cfg_contact = a['partId']
            if a['type'] == 'CavityPlugPart' and not a.get('rule') and not cfg_plug: cfg_plug = a['partId']
    cavs = []
    for p in pins:
        cv = {"id": "%s.%s" % (sid(c), sid(p)), "designation": p}
        here = [u for u in use[c].get(p, []) if u[0] == NAME]
        mine_w = [u for u in here if u[1]]
        if mine_w:
            r, s = mine_w[0][2], mine_w[0][3]
            ct = part_id('contactParts', r[s + '_terminal_pn'], mk_contact)
            if ct and ct != cfg_contact: cv['contactPartId'] = ct
        else:
            cv['notConnected'] = True
            if here:      # an EngineRoom-C spare: its sealing plug from the master (TBD -> none)
                pl = part_id('cavityPlugParts', here[0][2][here[0][3] + '_terminal_pn'])
                if pl and pl != cfg_plug: cv['cavityPlugPartId'] = pl
            else:
                owners = sorted({u[0] for u in use[c].get(p, [])})
                if owners:
                    other_owned[c].append((p, '/'.join(owners))); cv['cavityPlugPartId'] = None
        cavs.append(cv)
    conns[c] = {"id": "c_" + sid(c), "label": c, "cavities": cavs}
    if cpid: conns[c]['partId'] = cpid
cav_of = {(c, cv['designation']): cv['id'] for c, n in conns.items() for cv in n['cavities']}

# ------------------------------------------------------------------ other ends
terms, splices = collections.OrderedDict(), collections.OrderedDict()
SPL = part_id('spliceParts', 'GENERIC SOLDER SPLICE')
def tkey(r, s):
    t, i, p, nm = r[s + '_type'], r[s + '_id'], r[s + '_pin'], r[s + '_name']
    if t == 'terminal': return i
    k = '%s-%s' % (i, p)
    if 'cowl lead' in nm.lower() and i == 'W1': k += ' cowl'
    return k
def tlabel(r, s):
    t, i, p, nm = r[s + '_type'], r[s + '_id'], r[s + '_pin'], r[s + '_name']
    if t == 'terminal': return i
    if i == 'W1': return 'W1 pin %s (%s)' % (p, 'factory cowl lead' if 'cowl lead' in nm.lower() else 'washer motor')
    return '%s pin %s (factory lead)' % (i, p)
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice':
        tp = r[s + '_terminal_pn']
        pid = SPL if tp == 'solder splice' else (part_id('spliceParts', 'GENERIC CRIMP SPLICE 14-10') if tp == 'crimp splice' else part_id('spliceParts', tp, mk_splice))
        sp = splices.setdefault(i, {"id": "s_" + sid(i), "label": i})
        if pid: sp['partId'] = pid
        return {"id": "s_" + sid(i), "handle": "Splice"}
    if t in ('terminal', 'OEM'):
        k = tkey(r, s)
        nm = r[s + '_name'].lower()
        ty = 'Ring' if ('ring' in nm or 'stud' in nm or 'bolt' in nm) else 'Loose'
        terms.setdefault(k, {"id": "t_" + sid(k), "label": tlabel(r, s), "type": ty})
        return {"id": "t_" + sid(k), "handle": "Terminal"}
    raise SystemExit('end type ' + t)
wires, wire_row = [], {}
for r in W:
    a, b = end(r, 'from'), end(r, 'to')
    w = {"id": "w_" + sid(r['wire_id']), "source": a, "target": b, "color": col(r['colour']), "identLabel": r['wire_id']}
    wp = part_id('wireParts', r['wire_pn'], mk_wire)
    if wp: w['partId'] = wp
    wires.append(w); wire_row[r['wire_id']] = r

# ------------------------------------------------------------------ signals: one origin per net
par = {}
def f(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
def un(a, b): par[f(a)] = f(b)
def key(e): return (e['id'], e['handle']) if e['handle'] != 'Splice' else (e['id'],)
desc = {}
for w in wires:
    r = wire_row[w['identLabel']]
    for s, e in (('from', w['source']), ('to', w['target'])):
        desc.setdefault(key(e), r[s + '_desc'] or r[s + '_name'])
    un(key(w['source']), key(w['target']))
nets = collections.defaultdict(list)
for k in list(par): nets[f(k)].append(k)
SOURCES = {'c_POWER', 'c_POWER_STUDS', 'c_LOGIC', 'c_K_ACC', 'c_K_FAN', 'c_K_FAN2', 'c_K_HL', 'c_K_HR'}
def rank(k):
    i = k[0]
    if i in SOURCES: return 0
    if i.startswith('t_') and re.match(r't_(IE1|JB1|RB2|RB4|IG2|W1_\d_cowl)', i): return 1
    if i.startswith('c_'): return 2
    if i.startswith('t_'): return 3
    return 9
comp = {n['id']: n for n in list(conns.values()) + list(terms.values())}
for root, ks in nets.items():
    ks = [k for k in ks if rank(k) < 9]
    if not ks: continue
    k = min(ks, key=lambda k: (rank(k), k))
    sig = (desc.get(k) or '')[:40]
    if not sig: continue
    n = comp[k[0]]
    if k[0].startswith('t_'): n['signal'] = sig
    else: next(cv for cv in n['cavities'] if cv['id'] == k[1])['signal'] = sig

# ================================================================== schematic
def node_of(name): return conns.get(name) or terms.get(name)
LEFT_GROUPS = [['POWER', 'POWER-STUDS'], ['LOGIC'], ['K-ACC', 'K-FAN', 'K-FAN2', 'K-HL', 'K-HR'],
               ['IE1-3', 'IE1-10', 'IE1-17', 'IE1-6', 'IE1-13', 'IE1-20', 'JB1-1H-5', 'IE1-7', 'IE1-8', 'IE1-9', 'IE1-14', 'IE1-15', 'IE1-16',
                'IE1-11', 'IE1-18', 'JB1-1H-4', 'JB1-1H-6', 'JB1-1H-8', 'JB1-2', 'RB2-2', 'RB4-2', 'IG2-16', 'W1-1 cowl', 'W1-2 cowl'],
               ['GND-ID', 'GND-IG', 'GND-EA', 'GND-EB', 'T-ENG-BLOCK-2', 'T-ENG-BLOCK-3']]
RIGHT = ['ALT-PLUG', 'A4-4', 'A5-1', 'FAN-RAD', 'FAN-RAD-GND', 'FAN-COND', 'FAN-COND-GND', 'MRS-A', 'MRS-B', 'MRS-C',
         'F9-1', 'F9-2', 'F9-3', 'F9-4', 'W1-1', 'W1-2', 'R2-1', 'R2-2', 'R2-3', 'R2-4', 'R2-5', 'R3-1', 'R3-2', 'R3-3', 'R3-4', 'R3-5',
         'H1-1', 'H1-2', 'H1-3', 'H2-1', 'H2-2', 'H2-3', 'HORN-LH', 'HORN-RH', 'F7-1', 'F7-2', 'F7-3', 'F8-1', 'F8-2', 'F8-3']
LEFT_GROUPS = [[n for n in g if node_of(n)] for g in LEFT_GROUPS]
LEFT_GROUPS = [g for g in LEFT_GROUPS if g]
RIGHT = [n for n in RIGHT if node_of(n)]
placed_left = [n for g in LEFT_GROUPS for n in g]
assert set(placed_left) | set(RIGHT) == set(conns) | set(terms), (set(conns) | set(terms)) ^ (set(placed_left) | set(RIGHT))
NLP = 14
SPX = 210 + 30 * NLP + 120
LP = list(range(210, SPX - 60, 30))
EP = [SPX + 60, SPX + 90, SPX + 120]
MP = list(range(SPX + 150, SPX + 150 + 30 * 260, 30))
def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
notes = []
y = 0
for gi, g in enumerate(LEFT_GROUPS):
    if gi: y += 90
    for nm in g:
        n = node_of(nm); n['schematicPosition'] = {"x": 0, "y": y}
        y += h(n) + (60 if 'cavities' in n else 30)
LEFT_BOTTOM = y
NODES = {n['id']: n for n in list(conns.values()) + list(terms.values())}
LEFT_IDS = {node_of(n)['id'] for n in placed_left}
RIGHT_IDS = {node_of(n)['id'] for n in RIGHT}
def cav_y(n, handle):
    if 'cavities' not in n: return n['schematicPosition']['y'] + 15
    i = [cv['id'] for cv in n['cavities']].index(handle)
    return n['schematicPosition']['y'] + 30 * (i + 1) + 15
used_rows, deg = set(), collections.Counter()
for w in wires:
    for e in (w['source'], w['target']):
        if e['id'] in LEFT_IDS:
            deg[(e['id'], e['handle'])] += 1; used_rows.add(cav_y(NODES[e['id']], e['handle']))
inl = list(splices.values())
INLN = {n['id']: n for n in inl}
links = collections.defaultdict(list)
for w in wires:
    a, b = w['source'], w['target']
    for x, o in ((a, b), (b, a)):
        if x['id'].startswith('s_'): links[x['id']].append((w, x, o))
def left_row_of(e): return cav_y(NODES[e['id']], e['handle']) if e['id'] in LEFT_IDS else None
taken = set()
def free_row(want):
    cands = [yy for yy in range(15, max(LEFT_BOTTOM, 4000), 30) if yy not in used_rows and yy not in taken]
    yy = min(cands, key=lambda v: (abs(v - want), v)); taken.add(yy); return yy
pending = []
for n in inl:
    straight = None
    for w, x, o in links[n['id']]:
        ly = left_row_of(o)
        if ly is not None and deg[(o['id'], o['handle'])] == 1 and ly not in taken:
            straight = ly; break
    if straight is not None: taken.add(straight); n['_row'] = straight
    else: pending.append(n)
# right column first (rough rows) so a splice fed only from the right can sit near its devices
for it in range(6):
    left = []
    for n in pending:
        ys = [INLN[o['id']]['_row'] for w, x, o in links[n['id']] if o['id'] in INLN and '_row' in INLN[o['id']]]
        lys = [left_row_of(o) for w, x, o in links[n['id']] if left_row_of(o) is not None]
        if lys: n['_row'] = free_row(min(lys))
        elif ys: n['_row'] = free_row(sum(ys) // len(ys))
        else: left.append(n)
    pending = left
for n in splices.values():
    if '_row' in n: n['schematicPosition'] = {"x": SPX, "y": n['_row'] - 15}
def partner_y(n):
    ys = []
    for w in wires:
        for a, b in ((w['source'], w['target']), (w['target'], w['source'])):
            if a['id'] == n['id']:
                if b['id'] in LEFT_IDS: ys.append(cav_y(NODES[b['id']], b['handle']))
                elif b['id'] in INLN and 'schematicPosition' in INLN[b['id']]: ys.append(INLN[b['id']]['schematicPosition']['y'] + 15)
    return ys
# right column: devices sorted by the row of what feeds them (a device with nothing placed keeps its place after the one before)
kk, last = {}, 0
for i, nm in enumerate(RIGHT):
    ys = partner_y(node_of(nm)); last = min(ys) if ys else last + 0.1; kk[nm] = (last, i)
RIGHT.sort(key=lambda nm: kk[nm])
y = 15
for nm in RIGHT:
    n = node_of(nm)
    ys = partner_y(n)
    want = (min(ys) - 15 - (30 if 'cavities' in n else 0)) // 30 * 30 + 15 if ys else y
    y = max(y, want)
    n['schematicPosition'] = {"x": 0, "y": y}; y += h(n) + (60 if 'cavities' in n else 30)
for n in pending:
    rys = [cav_y(NODES[o['id']], o['handle']) for w, x, o in links[n['id']] if o['id'] in RIGHT_IDS]
    n['_row'] = free_row(min(rys)); n['schematicPosition'] = {"x": SPX, "y": n['_row'] - 15}
for n in splices.values(): n.pop('_row', None)
DEVX = None
def endpt(e):
    n = NODES.get(e['id']) or INLN.get(e['id'])
    p = n['schematicPosition']
    if e['id'].startswith('s_'): return (p['x'] + 15, p['y'] + 15, 0)
    yy = cav_y(n, e['handle'])
    if e['id'] in LEFT_IDS: return (p['x'] + 160, yy, 1)
    return (DEVX - 10, yy, -1)
busy = collections.defaultdict(list)
def lane(pool, y1, y2, lo, hi):
    a, b = min(y1, y2) - 14, max(y1, y2) + 14
    for x in pool:
        if lo < x < hi and all(b < u or a > v for u, v in busy[x]):
            busy[x].append((a, b)); return x
    raise SystemExit('no lane %r %s-%s in (%s,%s)' % (pool[:2], y1, y2, lo, hi))
def pool_for(ids):
    ids = set(ids)
    if any(i in RIGHT_IDS for i in ids): return MP
    if any(i in LEFT_IDS for i in ids): return LP
    return EP
def build(DEVXv):
    global DEVX
    DEVX = DEVXv
    busy.clear(); out = {}
    jobs = [(w, endpt(w['source']), endpt(w['target']), (w['source']['id'], w['target']['id'])) for w in wires]
    jobs.sort(key=lambda j: -abs(j[1][1] - j[2][1]))
    for cond, p1, p2, ids in jobs:
        if p1[1] == p2[1]: pts = []
        else:
            lo = max([p[0] + 20 for p in (p1, p2) if p[2] == 1] + [-10 ** 6])
            hi = min([p[0] - 20 for p in (p1, p2) if p[2] == -1] + [10 ** 6])
            for p in (p1, p2):
                if p[2] == 0:
                    o = p2 if p is p1 else p1
                    if o[0] >= p[0]: lo = max(lo, p[0] + 30)
                    else: hi = min(hi, p[0] - 30)
            try: x = lane(pool_for(ids), p1[1], p2[1], lo, hi)
            except SystemExit: x = lane(LP + EP + MP, p1[1], p2[1], lo, hi)
            pts = [{"x": x, "y": p1[1]}, {"x": x, "y": p2[1]}]
        out[cond['id']] = (pts, p1, p2)
    return out
res = build(SPX + 150 + 30 * 260)
maxlane = max([pts[0]['x'] for pts, a, b in res.values() if pts] + [SPX])
DEVXV = (maxlane + 120) // 30 * 30
res = build(DEVXV)
for nm in RIGHT: node_of(nm)['schematicPosition']['x'] = DEVX
def lp(pts, tag): return [{"id": "%s_s%d" % (tag, i), "schematicPosition": {"x": q['x'] - 15, "y": q['y'] - 15}} for i, q in enumerate(pts)]
for w in wires:
    pts, a, b = res[w['id']]
    if pts: w['layoutPoints'] = lp(pts, w['id'])
for c, lst in other_owned.items():
    n = conns[c]; p = n['schematicPosition']
    by = collections.defaultdict(list)
    for pin, own in lst: by[own].append(pin)
    txt = '%s: N/C cavities belong to other harnesses - ' % c + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(by.items()))
    if c in NOPART: txt += '. No part set: ' + NOPART[c] + ' (Dan to decide).'
    x = -420 if n['id'] in LEFT_IDS else DEVX + 270
    notes.append({"id": "n_" + sid(c), "text": txt, "width": 360, "schematicPosition": {"x": x, "y": p['y']}})
spares = collections.defaultdict(list)
for r in SPARE: spares[r['from_id']].append(r['from_pin'])
for c, pins in spares.items():
    n = conns[c]; p = n['schematicPosition']
    nid = "n_" + sid(c)
    t = '%s: pins %s are EngineRoom-C spares (sealing plug TBD in the master).' % (c, ', '.join(sorted(pins, key=pkey)))
    ex = next((x for x in notes if x['id'] == nid), None)
    if ex: ex['text'] = t + ' ' + ex['text']
    else: notes.append({"id": nid, "text": t, "width": 360, "schematicPosition": {"x": DEVX + 270, "y": p['y']}})
pass_by = collections.defaultdict(list)
for r in PASS: pass_by[r['harness']].append(r['wire_id'])
notes.append({"id": "n_title", "width": 420, "schematicPosition": {"x": -480, "y": -330},
              "text": TITLE + ", Rev 3 (2026-11-01, EA / EB on Route 17). Viewer copy generated from docs/harness/MASTER-wirelist.csv (harness = EngineRoom-C); never a source. "
                      "Schematic: fuse boxes, relays, factory cowl / kick-panel taps and ground studs left, splices middle, front devices right. "
                      "Shared connectors are drawn whole; cavities wired by other harnesses are N/C with a note. "
                      "Wires of other harnesses that only pass through EngineRoom-C are not drawn: " +
                      '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(pass_by.items())) + ". "
                      "Layout: the ST185-harness tree from Route 17 (runs 10 / 11 / 11b; ALT, MRS and block ground via Route 16; GND-EA / GND-EB on Route 17 devices 24 / 25), front LEFT, driver side up; each part on a 100 mm end-allowance stub."})

# ================================================================== layout
L = H.layout
node_items = collections.defaultdict(list); inline_at = collections.defaultdict(list); seen = set()
def cid_of(r, s):
    t = r[s + '_type']
    if t == 'connector': return conns[r[s + '_id']]['id']
    if t in ('terminal', 'OEM'): return terms[tkey(r, s)]['id']
    if t == 'splice': return splices[r[s + '_id']]['id']
for r in W + SPARE:
    for s in ('from', 'to'):
        if not r[s + '_type']: continue
        cid = cid_of(r, s)
        if cid in seen: continue
        nd = H.place(r, s); assert nd, (r['wire_id'], s)
        seen.add(cid)
        (node_items if cid[:2] in ('c_', 't_') else inline_at)[nd].append(cid)
segs = collections.Counter(); hroute = {}
for r in W:
    p, mm = H.route(r); hroute[r['wire_id']] = mm
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
tree_nodes = {n for k in segs for n in k}
for nd in list(node_items) + list(inline_at):   # a spare-only plug (MRS-B / MRS-C): join it to the nearest tree node
    if nd in tree_nodes: continue
    p = min((H.path(nd, x) for x in tree_nodes), key=len)
    print('spare-only node', nd, 'joined via', p)
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
adj = collections.defaultdict(list)
for a, b, mm in L['segments']:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
nseg = len(segs); nnode = len({n for k in segs for n in k})
print('tree check: segments', nseg, 'nodes', nnode, '(tree if segments = nodes - 1)')
root = 'GB'; parent = {root: None}; seglen = {}; todo = [root]; kids = collections.defaultdict(list)
while todo:
    n = todo.pop(0)
    for m, mm in adj[n]:
        if m not in parent: parent[m] = n; seglen[m] = mm; kids[n].append(m); todo.append(m)
for nd in list(node_items) + list(inline_at): assert nd in parent, nd
via = {n: [] for n in parent}
changed = True
while changed:
    changed = False
    for n in list(parent):
        if n == root or node_items.get(n) or inline_at.get(n): continue
        if len(kids[n]) == 1:
            c = kids[n][0]; p = parent[n]
            seglen[c] += seglen[n]; parent[c] = p; via[c] = via[n] + [n] + via[c]
            kids[p] = [c if x == n else x for x in kids[p]]
            del parent[n], seglen[n], kids[n]; changed = True; break
SCX, SCY = 27, 24
def lpos(n):
    x, yy = L['nodes'][n]['xy']
    return (int(round((130 - x) * SCX / 30)) * 30, int(round((100 - yy) * SCY / 30)) * 30)
bps, bundles = [], []
pos = {n: lpos(n) for n in parent}
STUB = L.get('end_allowance_mm', 100)
for n in parent: bps.append({"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}})
for n, p in parent.items():
    if p is None: continue
    bn = {"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(seglen[n]), "unit": "mm"}}
    ch = [pos[p]] + [lpos(m) for m in via[n]] + [pos[n]]
    changed2 = True
    while changed2:            # drop repeated points and A-B-A spikes left by rounding to the 30 grid
        changed2 = False
        for i in range(len(ch) - 1):
            if ch[i] == ch[i + 1]: del ch[i + 1]; changed2 = True; break
        else:
            for i in range(len(ch) - 2):
                if ch[i] == ch[i + 2]: del ch[i + 1:i + 3]; changed2 = True; break
    mids = ch[1:-1]
    if mids: bn['layoutPoints'] = [{"id": "%s_p%d" % (bn['id'], i), "layoutPosition": {"x": q[0], "y": q[1]}} for i, q in enumerate(mids)]
    bundles.append(bn)
occupied = set(pos.values())
ALLC = {x['id']: x for x in list(conns.values()) + list(terms.values()) + inl}
TREESEG = []
for n, p in parent.items():
    if p is None: continue
    bn = next(b for b in bundles if b['targetId'] == 'bp_' + sid(n))
    ch = [pos[p]] + [(q['layoutPosition']['x'], q['layoutPosition']['y']) for q in bn.get('layoutPoints', [])] + [pos[n]]
    TREESEG += list(zip(ch, ch[1:]))
def sdist(q, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]; ll = vx * vx + vy * vy or 1
    u = max(0, min(1, ((q[0] - a[0]) * vx + (q[1] - a[1]) * vy) / ll))
    return math.hypot(q[0] - a[0] - u * vx, q[1] - a[1] - u * vy)
def arrangements(n, k):
    x0, y0 = pos[n]; out = []
    for sx in (1, -1):
        pts = []
        for i in range(k):
            cc, row = divmod(i, 6); m = min(6, k - cc * 6)
            pts.append((x0 + sx * (120 + 270 * cc), y0 + int((row - (m - 1) / 2) * 60 // 30) * 30))
        out.append((sx, 0, pts))
    for sy in (1, -1):
        pts = []
        for i in range(k):
            row, cc = divmod(i, 3); m = min(3, k - row * 3)
            pts.append((x0 + int((cc - (m - 1) / 2) * 210 // 30) * 30, y0 + sy * (120 + 60 * row)))
        out.append((0, sy, pts))
    return out
INL_AT = {}
for n in parent:
    items = node_items.get(n, []); k = len(items); best = None
    for sx, sy, pts in arrangements(n, max(k, 1)):
        clr = min([sdist(q, a, b) for q in pts for a, b in TREESEG if pos[n] not in (a, b)] +
                  [math.hypot(q[0] - v[0], q[1] - v[1]) for q in pts for v in occupied if v != pos[n]] + [999])
        sc = (min(clr, 150), sx != 0)
        if best is None or sc > best[0]: best = (sc, sx, sy, pts)
    _, dx, dy, pts = best
    for cid, q in zip(items, pts):
        q = list(q)
        while tuple(q) in occupied: q[1] += 30
        occupied.add(tuple(q))
        ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
        bundles.append({"id": "bn_" + cid, "sourceId": "bp_" + sid(n), "targetId": cid, "length": {"value": STUB, "unit": "mm"}})
    if not dx: dx = -1 if pos[n][0] > 2000 else 1
    ins = inline_at.get(n, [])
    for i, cid in enumerate(ins):
        cc, row = divmod(i, 5); m = min(5, len(ins) - cc * 5); sx = int(round(dx)) or 1
        q = [pos[n][0] - sx * (60 + 180 * cc), pos[n][1] + int((row - (m - 1) / 2) * 30 // 30) * 30]
        while tuple(q) in occupied or (q[0] - sx * 60, q[1]) in occupied: q[1] += 30
        occupied.add(tuple(q)); occupied.add((q[0] - sx * 60, q[1]))
        sbp = "bp_" + cid
        bps.append({"id": sbp, "layoutPosition": {"x": q[0], "y": q[1]}})
        bundles.append({"id": "bn_" + cid, "sourceId": "bp_" + sid(n), "targetId": sbp, "length": {"value": STUB, "unit": "mm"}})
        ALLC[cid]['layoutPosition'] = {"x": q[0] - sx * 60, "y": q[1]}; ALLC[cid]['locationId'] = sbp
        INL_AT[cid] = "bp_" + sid(n)
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
loc = {}
for b in bundles:
    if b['targetId'][:2] in ('c_', 't_'): loc[b['targetId']] = (b['sourceId'], b['length']['value'])
for x in inl: loc[x['id']] = (INL_AT[x['id']], STUB)
def chain(bp):
    out = []
    while bp: out.append(bp); bp = nodepar[bp]
    return out
def dist(b1, b2):
    c1, c2 = chain(b1), chain(b2); common = next(x for x in c1 if x in c2); d = 0
    for c in (c1, c2):
        for x in c[:c.index(common)]: d += blen[(nodepar[x], x)]
    return d
expect = {}
for w in wires:
    (ba, la), (bb, lb) = loc[w['source']['id']], loc[w['target']['id']]
    expect[w['identLabel']] = la + lb + dist(ba, bb)
bad = {k: (v, hroute[k]) for k, v in expect.items() if v != hroute[k]}
print('expect != H.route:', bad)

# ================================================================== emit
doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG",
       "connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
       "wires": wires, "branchPoints": bps, "bundles": bundles, "schematicNotes": notes}
for k, v in doc_parts.items():
    if v: doc[k] = list(v.values())
json.dump(doc, open(os.path.join(OUT, 'engc.json'), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'engc_lib_ops.json'), 'w'), indent=1)
json.dump({k: [v[1], v[0], v[2]] for k, v in res.items()}, open(os.path.join(OUT, 'engc_routes.json'), 'w'))
json.dump({'expect': expect, 'master': {r['wire_id']: r['est_length_mm'] for r in W}}, open(os.path.join(OUT, 'engc_expect.json'), 'w'), indent=1)
print('connectors', len(conns), 'terminals', len(terms), 'splices', len(splices), 'wires', len(wires), 'bundles', len(bundles), 'bps', len(bps),
      'DEVX', DEVX, 'lib adds', [o['value']['partNumber'] for o in lib_add])
