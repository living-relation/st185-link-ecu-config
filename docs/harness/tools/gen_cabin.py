"""harness.design copy of ST185-AB-cabin (viewer only; the master is the source).
Usage: python gen_cabin.py <repo> <out_dir> <doc 1|2>   (1 = AB-cabin 1, bulkhead run; 2 = AB-cabin 2, dash)
Needs <out>/lib.json = a dump of the harness.design part library 5LO8 (get_part_library). Writes <out>/abcab<doc>.json
(whole document), abcab<doc>_lib_ops.json (library add ops), abcab<doc>_routes.json and abcab<doc>_expect.json
(expected routed length per wire id = sum of the bundle lengths on its layout path)."""
import sys, os, json, re, collections, math
REPO, OUT, DOC = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
H = B.Harness('ST185-harness')
NAME = 'AB-cabin'
ALL = H.rows                                   # every master row (with _conn / _conn_name)
ROWS = [r for r in ALL if r['harness'] == NAME]
W_ALL = [r for r in ROWS if r['wire_id']]
def doc_of(r): return 1 if 'DRB102-CABIN' in (r['from_id'], r['to_id']) else 2
TITLES = {1: 'ST185-AB-cabin 1 - bulkhead run', 2: 'ST185-AB-cabin 2 - dash'}
OTHER = TITLES[3 - DOC]
W = [r for r in W_ALL if doc_of(r) == DOC]
def spare_doc(c): return 1 if c == 'DRB102-CABIN' else 2
SPARE = [r for r in ROWS if not r['wire_id']]
PARTS_CSV = {}
import csv
for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8')):
    PARTS_CSV[p['part_number']] = p
LIB = json.load(open(os.path.join(OUT, 'lib.json')))['parts']   # dump of get_part_library 5LO8
def lib_by_pn(kind, pn):
    return next((p for p in LIB[kind] if p.get('partNumber') == pn), None)
def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
def col(c): return c if c in COLORS else "Gray"

# ------------------------------------------------------------------ parts (library wins; new = from harness-parts.csv)
doc_parts = collections.defaultdict(dict)      # kind -> id -> part
lib_add = []                                   # edit_part_library add ops
def use_lib(kind, part):
    doc_parts[kind][part['id']] = json.loads(json.dumps(part))
    for cfg in part.get('configurations', []):
        for a in cfg.get('accessories', []):
            k = {'LockPart': 'lockParts', 'ContactPart': 'contactParts', 'CavityPlugPart': 'cavityPlugParts', 'MountPart': 'mountParts',
                 'CavitySealPart': 'cavitySealParts', 'BootPart': 'bootParts', 'CoveringPart': 'coveringParts'}[a['type']]
            ap = next(p for p in LIB[k] if p['id'] == a['partId']) if any(p['id'] == a['partId'] for p in LIB[k]) else doc_parts[k].get(a['partId'])
            doc_parts[k][ap['id']] = json.loads(json.dumps(ap))
    return part['id']
def new_part(kind, part):
    assert part['partNumber'] in PARTS_CSV, part['partNumber']
    c = PARTS_CSV[part['partNumber']]
    part.setdefault('manufacturer', c['manufacturer']); part.setdefault('description', c['description'])
    LIB[kind].append(part); lib_add.append({"op": "add", "collection": kind, "value": part})
    return use_lib(kind, part)
def part_id(kind, pn, maker=None):
    """library part id for this part number (adding it from harness-parts.csv when missing); None for TBD / unknown."""
    if not pn or pn.upper().startswith('TBD') or pn in ('factory (OEM)',):
        return None
    if kind == 'resistorParts' and pn == '1k 1/4W': pn = '1.0k 1/4W'   # Dan 2026-11-01: the library's 1.0k part
    p = lib_by_pn(kind, pn)
    if p: return use_lib(kind, p)
    if pn not in PARTS_CSV: return None
    return maker(pn) if maker else None

def mk_wire(pn):
    m = re.match(r'J1128-TXL-(\d+)-([A-Z]+)$', pn)
    g, c = int(m.group(1)), m.group(2).title()
    return new_part('wireParts', {"id": "j1128_%d_%s" % (g, c.lower()), "color": c, "gauge": {"unit": "AWG", "value": g}, "partNumber": pn})
def mk_contact(pn):
    c = PARTS_CSV[pn]['description']
    if pn == '280919-2':
        return new_part('contactParts', {"id": "ct_280919_2", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                         "minGauge": {"unit": "AWG", "value": 20}, "maxGauge": {"unit": "AWG", "value": 15}, "partNumber": pn})
    if pn == '1-968849-1':
        return new_part('contactParts', {"id": "ct_1_968849_1", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                         "minGauge": {"unit": "AWG", "value": 20}, "maxGauge": {"unit": "AWG", "value": 18}, "partNumber": pn})
    if pn == '1-968851-1':
        return new_part('contactParts', {"id": "ct_1_968851_1", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                                         "minGauge": {"unit": "AWG", "value": 16}, "maxGauge": {"unit": "AWG", "value": 14}, "partNumber": pn})
    raise SystemExit('no maker for contact ' + pn)
def mk_res(pn):
    m = re.match(r'([\d.]+)(k|R)\s', pn)
    v = float(m.group(1)); u = 'kohm' if m.group(2) == 'k' else 'ohm'
    return new_part('resistorParts', {"id": "rp_" + sid(pn).lower(), "partNumber": pn, "resistance": v, "resistanceUnit": u,
                                      "power": 0.25, "powerUnit": "W"})
def mk_diode(pn):
    return new_part('diodeParts', {"id": "dp_1n5822", "partNumber": pn, "voltage": 40, "voltageUnit": "V", "current": 3, "currentUnit": "A"})
def mk_cable(pn):
    assert pn == '55A1811-20-9-9CS2275'
    return new_part('cableParts', {"id": "cp_55a1811_20_9", "color": "White", "shielded": True, "partNumber": pn,
                                   "cores": [{"id": "c55a1811_1", "color": "White", "gauge": {"unit": "AWG", "value": 20}}]})
def mk_conn(pn):
    assert pn == 'DT06-08SA'
    lock = lib_by_pn('lockParts', 'W8S') or None
    if not lock:
        new_part('lockParts', {"id": "lp_w8s", "partNumber": "W8S"}); lock = lib_by_pn('lockParts', 'W8S')
    return new_part('connectorParts', {"id": "cp_dt06_08sa", "gender": "Female", "hasShell": False, "numberOfCavities": 8, "partNumber": pn,
                                       "configurations": [{"id": "cp_dt06_08sa_cfg", "accessories": [
                                           {"id": "cp_dt06_08sa_cfg1", "type": "LockPart", "partId": lock['id']},
                                           {"id": "cp_dt06_08sa_cfg2", "type": "ContactPart", "partId": lib_by_pn('contactParts', '0462-201-16141')['id']},
                                           {"id": "cp_dt06_08sa_cfg3", "type": "CavityPlugPart", "partId": lib_by_pn('cavityPlugParts', '114017')['id']}]}]})

# ------------------------------------------------------------------ connectors (drawn whole; other-harness cavities N/C + note)
def pkey(p):
    m = re.match(r'(\d+)$', p)
    return (0, int(m.group(1)), '') if m else (1, 0, p)
RELAY_ORDER = ['30', '85', '86', '87', '87a']
conn_ids = []
for r in W:
    for s in ('from', 'to'):
        if r[s + '_type'] == 'connector' and r[s + '_id'] not in conn_ids:
            conn_ids.append(r[s + '_id'])
use = collections.defaultdict(dict)            # conn -> pin -> list of (harness, wire_id, row, side)
housing = {}
for r in ALL:
    for s in ('from', 'to'):
        c = r[s + '_id']
        if r[s + '_type'] == 'connector' and c in conn_ids:
            use[c].setdefault(r[s + '_pin'], []).append((r['harness'], r['wire_id'], r, s))
            if r[s + '_housing_pn'] and r[s + '_housing_pn'] != 'TBD': housing.setdefault(c, r[s + '_housing_pn'])
conns = collections.OrderedDict(); other_owned = collections.defaultdict(list)
for c in conn_ids:
    hp = housing.get(c)
    cpid = part_id('connectorParts', hp, mk_conn) if hp else None
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
        mine_w = [u for u in here if u[1] and doc_of(u[2]) == DOC]
        theirs_w = [u for u in here if u[1] and doc_of(u[2]) != DOC]
        if mine_w:
            r, s = mine_w[0][2], mine_w[0][3]
            ct = part_id('contactParts', r[s + '_terminal_pn'], mk_contact)
            if ct and ct != cfg_contact: cv['contactPartId'] = ct
        else:
            cv['notConnected'] = True
            if theirs_w:
                other_owned[c].append((p, OTHER)); cv['cavityPlugPartId'] = None
            elif here and spare_doc(c) != DOC:
                other_owned[c].append((p, OTHER + ' (spare, its plug)')); cv['cavityPlugPartId'] = None
            elif here:     # an AB-cabin spare: its sealing plug from the master
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
terms, splices, resistors, diodes = (collections.OrderedDict() for _ in range(4))
SPL = part_id('spliceParts', 'GENERIC SOLDER SPLICE')
inline_side = collections.defaultdict(dict)    # inline id -> pin -> handle (decided after schematic placement)
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice':
        splices.setdefault(i, {"id": "s_" + sid(i), "label": i, "partId": SPL}); return {"id": "s_" + sid(i), "handle": "Splice"}
    if t in ('terminal', 'OEM'):
        k = i + ('-' + p if t == 'OEM' else '')
        nm = r[s + '_name'].lower()
        ty = 'Ring' if ('ring' in nm or 'stud' in nm) else 'Loose'
        terms.setdefault(k, {"id": "t_" + sid(k), "label": k if t == 'terminal' else '%s pin %s (factory lead)' % (i, p), "type": ty})
        return {"id": "t_" + sid(k), "handle": "Terminal"}
    if t == 'resistor':
        resistors.setdefault(i, {"id": "r_" + sid(i), "label": i, "partId": part_id('resistorParts', r[s + '_housing_pn'], mk_res)})
        return {"id": "r_" + sid(i), "handle": "PIN" + p}
    if t == 'diode':
        diodes.setdefault(i, {"id": "d_" + sid(i), "label": i, "partId": part_id('diodeParts', r[s + '_housing_pn'], mk_diode)})
        return {"id": "d_" + sid(i), "handle": "PIN" + p}
    return None   # cable screen: floats
wires, cables = [], collections.OrderedDict()
wire_row = {}
for r in W:
    a, b = end(r, 'from'), end(r, 'to')
    if r['cable']:
        cpid = part_id('cableParts', r['cable_pn'], mk_cable)
        cab = cables.setdefault(r['cable'], {"id": "cab_" + sid(r['cable']), "label": r['cable'], "partId": cpid, "cores": []})
        if r['colour'] == 'Shield':
            sh = {"id": "sh_" + sid(r['wire_id']), "color": "Shield"}
            ends = [e for e in (a, b) if e]
            sh['source'] = ends[0]
            if len(ends) > 1: sh['target'] = ends[1]
            cab['shield'] = sh
        else:
            cab['cores'].append({"id": "co_" + sid(r['wire_id']), "color": col(r['colour']), "source": a, "target": b})
        wire_row[r['wire_id']] = r
        continue
    w = {"id": "w_" + sid(r['wire_id']), "source": a, "target": b, "color": col(r['colour']), "identLabel": r['wire_id']}
    wp = part_id('wireParts', r['wire_pn'], mk_wire)
    if wp: w['partId'] = wp
    wires.append(w); wire_row[r['wire_id']] = r
for c in cables.values():   # core order = the cable part's core order (matched by colour)
    cp = doc_parts['cableParts'][c['partId']]
    order = [k['color'] for k in cp['cores']]
    have = [co['color'] for co in c['cores']]
    for colr in order:      # a core with no cabin job (cut back and sealed) still sits in the cable
        if colr not in have: c['cores'].append({"id": "co_%s_nc_%s" % (sid(c['label']), colr.lower()), "color": colr})
    c['cores'].sort(key=lambda co: order.index(co['color']))
    assert [co['color'] for co in c['cores']] == order, (c['label'], order)

# ------------------------------------------------------------------ signals: one origin per net
par = {}
def f(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
def un(a, b): par[f(a)] = f(b)
def key(e): return (e['id'], e['handle']) if e['handle'] != 'Splice' else (e['id'],)
conds = [(w, wire_row[w['identLabel']]) for w in wires] + [(co, wire_row[co['id'][3:]] if co['id'][3:] in wire_row else None) for c in cables.values() for co in [q for q in c['cores'] if 'source' in q]]
desc = {}
for w in wires:
    r = wire_row[w['identLabel']]
    for s, e in (('from', w['source']), ('to', w['target'])):
        if e: desc.setdefault(key(e), r[s + '_desc'])
    un(key(w['source']), key(w['target']))
for c in cables.values():
    for co in [q for q in c['cores'] if 'source' in q]:
        un(key(co['source']), key(co['target']))
for r in W:
    if r['cable'] and r['colour'] != 'Shield':
        for s in ('from', 'to'):
            e = end(r, s)
            if e: desc.setdefault(key(e), r[s + '_desc'])
nets = collections.defaultdict(list)
for k in list(par): nets[f(k)].append(k)
def rank(k):
    i = k[0]
    if i == 'c_DRB102_CABIN': return 0
    if i.startswith('c_ECU'): return 2
    if i.startswith('c_'): return 1
    if i.startswith('t_'): return 3
    return 9
comp = {n['id']: n for n in list(conns.values()) + list(terms.values())}
# Dan 2026-11-01: every pin shows its own end text from the master (device pins say only the pin's job)
for k, sig in desc.items():
    if rank(k) >= 9 or not sig: continue
    n = comp.get(k[0])
    if not n: continue
    if k[0].startswith('t_'): n['signal'] = sig
    else:
        cv = next((cv for cv in n['cavities'] if cv['id'] == k[1]), None)
        if cv is not None and not cv.get('notConnected'): cv['signal'] = sig

# ================================================================== schematic
LEFT_GROUPS = [['DRB102-CABIN'],
               ['LOGIC', 'BUS-SW12', 'K-ACC', 'K-EPS', 'K-EPS-EN', 'K-FAN', 'K-FAN2', 'POWER-NEG-BAR'],
               ['K-FP'],
               ['A18-2', 'A18-8', 'A18-9', 'A18-11', 'A18-13', 'A18-18', 'A32-6', 'A32-15', 'A5-4', 'A1-1', 'A1-2'],
               ['IG2-4', 'IG2-13', 'JB1-1H-7'],
               ['IX-WS-F-S', 'IX-WS-R-S', 'APS-PEDAL'],
               ['OPTO-8', 'IX-FUEL-P']]
RIGHT = ['ECU-A', 'ECU-B', 'BUS-5V', 'BUS-5V-2', 'BUS-GNDOUT-A', 'BUS-GNDOUT-B']
def node_of(name): return conns.get(name) or terms.get(name)
LEFT_GROUPS = [[n for n in g if node_of(n)] for g in LEFT_GROUPS]
LEFT_GROUPS = [g for g in LEFT_GROUPS if g]
RIGHT = [n for n in RIGHT if n in conns]
placed_left = [n for g in LEFT_GROUPS for n in g]
assert set(placed_left) | set(RIGHT) == set(conns) | set(terms), (set(conns) | set(terms)) ^ (set(placed_left) | set(RIGHT))
NLP = 16
CABX = 210 + 30 * NLP + 30
SPX = CABX + 600
DRL, DRR = SPX - 150, SPX + 150
LP = list(range(210, CABX - 30, 30))
CP = list(range(CABX + 90, DRL - 30, 30))
DP = [SPX - 90, SPX - 60, SPX - 30]
EP = [SPX + 60, SPX + 90, SPX + 120]
MP = list(range(SPX + 390, SPX + 390 + 30 * 260, 30))
KP = [SPX + 240, SPX + 270]
def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
cab_dev = {}
for c in cables.values():
    cnt = collections.Counter(e['id'] for co in c['cores'] + ([c['shield']] if 'shield' in c else []) for e in (co.get('source'), co.get('target'))
                              if e and e['id'] in [node_of(n)['id'] for n in placed_left])
    cab_dev[c['id']] = cnt.most_common(1)[0][0]
def cab_h(c): return 30 + 30 * len(c['cores']) + (30 if 'shield' in c else 0)
y = 0; notes = []
for gi, g in enumerate(LEFT_GROUPS):
    if gi: y += 90
    for nm in g:
        n = node_of(nm)
        n['schematicPosition'] = {"x": 0, "y": y}
        bottom = y + h(n)
        cy = y
        for c in cables.values():
            if cab_dev[c['id']] == n['id'] and n['id'] != 'c_DRB102_CABIN':
                c['schematicPosition'] = {"x": CABX, "y": cy}; cy += cab_h(c) + 30
        bottom = max(bottom, cy - 30)
        y = bottom + (60 if 'cavities' in n else 30)
LEFT_BOTTOM = y
y = 15
for nm in RIGHT:
    n = conns[nm]; n['schematicPosition'] = {"x": 0, "y": y}; y += h(n) + 60
# the CAN cable sits by the bulkhead on N/C rows 86-89 (its cores are DRB 79 / 80 / 81)
CANCAB = cables.get('CAB-CANBH-BC')
if CANCAB: CANCAB['schematicPosition'] = {"x": CABX, "y": 30 * 86}
# Dan 2026-11-01 (row 171): the cabin halves of the shielded sensor runs are cables from the bulkhead to the ECU side;
# each sits beside the bulkhead at its own pins' rows, stacked without overlap
def _bh_rows(c):
    rows = []
    for co in [q for q in c['cores'] if 'source' in q] + ([c['shield']] if 'shield' in c else []):
        for e in (co.get('source'), co.get('target')):
            if e and e['id'] == 'c_DRB102_CABIN':
                cv = conns['DRB102-CABIN']['cavities']; rows.append([x['id'] for x in cv].index(e['handle']))
    return rows
_bot = -10**9
for c in sorted([c for c in cables.values() if 'schematicPosition' not in c and _bh_rows(c)], key=lambda c: min(_bh_rows(c))):
    y0 = conns['DRB102-CABIN']['schematicPosition']['y'] + 30 * min(_bh_rows(c))
    y0 = max(y0, _bot + 30); y0 -= y0 % 30
    c['schematicPosition'] = {"x": CABX, "y": y0}; _bot = y0 + cab_h(c)
NODES = {}
for n in list(conns.values()) + list(terms.values()): NODES[n['id']] = n
LEFT_IDS = {node_of(n)['id'] for n in placed_left}
RIGHT_IDS = {conns[n]['id'] for n in RIGHT}
# rows: left lattice rows (centre y = 30k + 15) that hold a wired left cavity or terminal
def cav_y(n, handle):
    if 'cavities' not in n: return n['schematicPosition']['y'] + 15
    i = [cv['id'] for cv in n['cavities']].index(handle)
    return n['schematicPosition']['y'] + 30 * (i + 1) + 15
all_conds = [w for w in wires] + [co for c in cables.values() for co in [q for q in c['cores'] if 'source' in q] + ([c['shield']] if 'shield' in c else [])]
used_rows = set()
deg = collections.Counter()
for w in all_conds:
    for e in (w.get('source'), w.get('target')):
        if e and e['id'] in LEFT_IDS:
            deg[(e['id'], e['handle'])] += 1
            used_rows.add(cav_y(NODES[e['id']], e['handle']))
for n in list(conns.values()) + list(terms.values()):
    if n['id'] in LEFT_IDS and 'cavities' in n:   # a left connector's N/C rows hold nothing, header row neither
        pass
for c in cables.values():
    p = c['schematicPosition']
    for k in range(cab_h(c) // 30): used_rows.add(p['y'] + 30 * k + 15)
# inline parts: rows and columns
inl = list(splices.values()) + list(resistors.values()) + list(diodes.values())
links = collections.defaultdict(list)            # inline id -> list of (conductor, its end key, other end)
for w in all_conds:
    a, b = w.get('source'), w.get('target')
    for x, o in ((a, b), (b, a)):
        if x and x['id'][:2] in ('s_', 'r_', 'd_'): links[x['id']].append((w, x, o))
def left_row_of(e):
    if e and e['id'] in LEFT_IDS: return cav_y(NODES[e['id']], e['handle'])
    if e and e['id'] in [c['id'] for c in cables.values()]: return None
    return None
taken = set()
def free_row(want):
    cands = [y for y in range(15, max(LEFT_BOTTOM, 4000), 30) if y not in used_rows and y not in taken]
    y = min(cands, key=lambda y: (abs(y - want), y)); taken.add(y); return y
# cable core rows for cores whose cable end is right of the cable (row of that core in the cable)
def core_row(c, co):
    seq = c['cores'] + ([c['shield']] if 'shield' in c else [])
    return c['schematicPosition']['y'] + 30 * (seq.index(co) + 1) + 15
cab_of = {co['id']: c for c in cables.values() for co in c['cores'] + ([c['shield']] if 'shield' in c else [])}
order = []
INLN = {n['id']: n for n in inl}
for n in inl:
    want, straight = None, None
    for w, x, o in links[n['id']]:
        ly = left_row_of(o)
        if w['id'] in cab_of:
            cy = core_row(cab_of[w['id']], w)
            if cy not in taken: straight = cy; break
            continue
        if ly is not None and deg[(o['id'], o['handle'])] == 1 and ly not in taken:
            straight = ly; break
        if ly is not None and want is None: want = ly
    order.append((0 if straight is not None else 1, straight or want or 0, n))
def right_y(o):
    if o and o['id'] in RIGHT_IDS:
        return cav_y(NODES[o['id']], o['handle'])
    return None
pending = []
for pri, yy, n in sorted(order, key=lambda t: (t[0], t[1])):
    if pri == 0: taken.add(yy); n['_row'] = yy
    else: pending.append((yy, n))
for it in range(6):          # place the rest near what they hang on: a left row, a placed splice, else a right row
    left = []
    for yy, n in pending:
        ys = [INLN[o['id']]['_row'] for w, x, o in links[n['id']] if o and o['id'] in INLN and '_row' in INLN[o['id']]]
        lys = [left_row_of(o) for w, x, o in links[n['id']] if left_row_of(o) is not None]
        rys = [right_y(o) for w, x, o in links[n['id']] if right_y(o) is not None]
        if lys: n['_row'] = free_row(min(lys))
        elif ys: n['_row'] = free_row(sum(ys) // len(ys))
        elif rys and it >= 2: n['_row'] = free_row(min(rys))
        elif it == 5: n['_row'] = free_row(0)
        else: left.append((yy, n))
    pending = left
# column per inline part
for n in splices.values(): n['schematicPosition'] = {"x": SPX, "y": n['_row'] - 15}
sp = splices.get('SP-CAM')
if sp and 'r_R_CAM_PULLUP' in [r['id'] for r in resistors.values()]: sp['schematicPosition']['x'] = SPX + 300   # the pull-up sits between SP-8V and SP-CAM
def other_x(o):
    if o is None: return None
    if o['id'] in LEFT_IDS: return 0
    if o['id'] in RIGHT_IDS: return 99999
    if o['id'].startswith('s_'): return NODES_ALL[o['id']]['schematicPosition']['x']
    return None
NODES_ALL = dict(NODES); NODES_ALL.update({s['id']: s for s in splices.values()})
for n in list(resistors.values()) + list(diodes.values()):
    ends = [(x['handle'], o) for w, x, o in links[n['id']]]
    xs = {hd: other_x(o) for hd, o in ends}
    leftish = any(v == 0 for v in xs.values())
    n['schematicPosition'] = {"x": DRL if leftish else DRR, "y": n['_row'] - 15}
    if n['id'] == 'r_R_CAM_PULLUP': n['schematicPosition']['x'] = SPX + 150
    # handle: the end further left goes on Left (a diode keeps anode = pin 1 on the side it lands; anodeOnRight if flipped)
    srt = sorted(ends, key=lambda t: (xs[t[0]] if xs[t[0]] is not None else 50000))
    hmap = {}
    if len(srt) == 1:
        hmap[srt[0][0]] = 'Right' if (xs[srt[0][0]] or 0) > n['schematicPosition']['x'] else 'Left'
    else:
        hmap[srt[0][0]] = 'Left'; hmap[srt[1][0]] = 'Right'
    if n['id'] == 'r_R_CAM_PULLUP': hmap = {'PIN1': 'Left', 'PIN2': 'Right'}
    if n['id'].startswith('d_'):
        if hmap.get('PIN1') == 'Right': n['anodeOnRight'] = True
    for w, x, o in links[n['id']]: x['handle'] = hmap[x['handle']]
for n in inl: n.pop('_row', None)
for c in cables.values():
    if c is not CANCAB: pass
# ---- end points: (x, y, facing)
INL = {n['id']: n for n in inl}
CAB = {c['id']: c for c in cables.values()}
def endpt(e, toward_x):
    n = NODES.get(e['id']) or INL.get(e['id'])
    p = n['schematicPosition']
    if e['id'].startswith('s_'): return (p['x'] + 15, p['y'] + 15, 0)
    if e['id'][:2] in ('r_', 'd_'): return ((p['x'] - 10, p['y'] + 15, -1) if e['handle'] == 'Left' else (p['x'] + 40, p['y'] + 15, 1))
    yy = cav_y(n, e['handle'])
    if e['id'] in LEFT_IDS: return (p['x'] + 160, yy, 1) if 'cavities' in n else (p['x'] + 160, yy, 1)
    return (DEVX - 10, yy, -1)
busy = collections.defaultdict(list)
def lane(pool, y1, y2, lo, hi, rev=False):
    a, b = min(y1, y2) - 14, max(y1, y2) + 14
    for x in (pool[::-1] if rev else pool):
        if lo < x < hi and all(b < u or a > v for u, v in busy[x]):
            busy[x].append((a, b)); return x
    raise SystemExit('no lane %r %s-%s in (%s,%s)' % (pool[:2], y1, y2, lo, hi))
DEVX = None
def pool_for(p1, p2, ids):
    ids = set(ids)
    if any(i in RIGHT_IDS for i in ids): return MP
    if ids & set(CAB) and any(i in LEFT_IDS for i in ids): return LP
    if ids & set(CAB): return CP
    if all(i in LEFT_IDS for i in ids): return LP
    if any(i in LEFT_IDS for i in ids): return LP
    xs = sorted(p[0] for p in (p1, p2))
    if any(i.startswith(('r_', 'd_')) for i in ids):
        return DP if xs[1] <= SPX + 15 and xs[0] >= DRL else (EP if xs[0] >= SPX else MP)
    return EP
plan = []    # (conductor, side key or None, p1, p2, pool, ids)
def want(cond, side, e1pt, e2pt, ids):
    plan.append((cond, side, e1pt, e2pt, pool_for(e1pt, e2pt, ids)))
def place_dev():
    pass
# right column x: decide after counting how many MP lanes are needed: first pass with a huge DEVX
for DEVX in (SPX + 240 + 30 * 260,):
    pass
def build(DEVXv):
    global DEVX
    DEVX = DEVXv
    busy.clear(); out = {}
    jobs = []
    for w in wires:
        a, b = w['source'], w['target']
        p1, p2 = endpt(a, None), endpt(b, None)
        jobs.append((w, None, p1, p2, (a['id'], b['id'])))
    for c in cables.values():
        p = c['schematicPosition']
        for co in [q for q in c['cores'] if 'source' in q] + ([c['shield']] if 'shield' in c else []):
            cy = core_row(c, co)
            for side, e in (('sourceLayoutPoints', co.get('source')), ('targetLayoutPoints', co.get('target'))):
                if not e: continue
                q = endpt(e, None)
                cpt = (p['x'] - 10, cy, -1) if q[0] < p['x'] else (p['x'] + 70, cy, 1)
                jobs.append((co, side, cpt, q, (c['id'], e['id'])))
    # longest vertical spans first get the inner lanes
    jobs.sort(key=lambda j: -abs(j[2][1] - j[3][1]))
    for cond, side, p1, p2, ids in jobs:
        if p1[1] == p2[1]:
            pts = []
        else:
            lo = max([p[0] + 20 for p in (p1, p2) if p[2] == 1] + [-10 ** 6])
            hi = min([p[0] - 20 for p in (p1, p2) if p[2] == -1] + [10 ** 6])
            for p in (p1, p2):     # a splice centre: keep the lane on the side the other end lies
                if p[2] == 0:
                    o = p2 if p is p1 else p1
                    if o[0] >= p[0]: lo = max(lo, p[0] + 30)
                    else: hi = min(hi, p[0] - 30)
            pool = pool_for(p1, p2, ids)
            try:
                x = lane(pool, p1[1], p2[1], lo, hi)
            except SystemExit:
                x = lane(LP + CP + DP + EP + KP + MP, p1[1], p2[1], lo, hi)
            pts = [{"x": x, "y": p1[1]}, {"x": x, "y": p2[1]}]
        out[(cond['id'], side)] = (pts, p1, p2)
    return out
res = build(SPX + 390 + 30 * 260)
maxlane = max([pts[0]['x'] for pts, a, b in res.values() if pts] + [SPX])
DEVXV = (maxlane + 120) // 30 * 30
res = build(DEVXV)
for nm in RIGHT: conns[nm]['schematicPosition']['x'] = DEVX
for n in conns.values(): n['width'] = 240          # Dan 2026-11-01: 8 grid units
for n in terms.values(): n['width'] = 240
for g in LEFT_GROUPS:
    for nm in g:
        nd = node_of(nm); nd['schematicPosition']['x'] -= 90   # keep the right edge (wire side) where it was
def lp(pts, tag): return [{"id": "%s_s%d" % (tag, i), "schematicPosition": {"x": q['x'] - 15, "y": q['y'] - 15}} for i, q in enumerate(pts)]
for w in wires:
    pts, a, b = res[(w['id'], None)]
    if pts: w['layoutPoints'] = lp(pts, w['id'])
for c in cables.values():
    for co in [q for q in c['cores'] if 'source' in q] + ([c['shield']] if 'shield' in c else []):
        for side in ('sourceLayoutPoints', 'targetLayoutPoints'):
            if (co['id'], side) in res:
                pts, cpt, q = res[(co['id'], side)]
                if pts: co[side] = lp(pts, co['id'] + ('_a' if side[0] == 's' else '_b'))   # listed from the cable outward
# notes: who owns the N/C cavities of a shared connector
for c, lst in other_owned.items():
    n = conns[c]; p = n['schematicPosition']
    by = collections.defaultdict(list)
    for pin, own in lst: by[own].append(pin)
    txt = '%s: N/C cavities belong to other harnesses - ' % c + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(by.items()))
    x = -420 if n['id'] in LEFT_IDS else DEVX + 210
    notes.append({"id": "n_" + sid(c), "text": txt, "width": 360, "schematicPosition": {"x": x, "y": p['y']}})
notes.append({"id": "n_title", "width": 360, "schematicPosition": {"x": -420, "y": -270},
              "text": TITLES[DOC] + ", Rev 1 (2026-11-01). Part %d of 2 of AB-cabin: %s. The rest of AB-cabin is in '%s'; connectors and splices shared by both are drawn whole here, cavities wired in the other part are N/C with a note. Viewer copy generated from docs/harness/MASTER-wirelist.csv (harness = AB-cabin); never a source. " % (DOC, 'every AB-cabin conductor with an end on the bulkhead DRB102-CABIN' if DOC == 1 else 'every AB-cabin conductor with no end on the bulkhead', OTHER) +
                      "Schematic: bulkhead and the other far ends left, splices middle, ECU plugs and ECU splice-point bus plugs right. "
                      "Layout: the ST185-harness.layout.json tree, bulkhead LEFT (front of the car left), driver side up; each part on a 100 mm end allowance stub."})

# ================================================================== layout
L = H.layout
end_nodes = {}
def place_end(r, s): return H.place(r, s)
node_items = collections.defaultdict(list)      # layout node -> component ids (connectors / terminals)
inline_at = collections.defaultdict(list)
seen = set()
for r in W:
    for s in ('from', 'to'):
        t = r[s + '_type']
        if not t or t == 'cable screen': continue
        nd = place_end(r, s)
        if t == 'connector': cid = conns[r[s + '_id']]['id']
        elif t in ('terminal', 'OEM'): cid = terms[r[s + '_id'] + ('-' + r[s + '_pin'] if t == 'OEM' else '')]['id']
        elif t == 'splice': cid = splices[r[s + '_id']]['id']
        elif t == 'resistor': cid = resistors[r[s + '_id']]['id']
        elif t == 'diode': cid = diodes[r[s + '_id']]['id']
        if cid in seen: continue
        seen.add(cid)
        (node_items if cid[:2] in ('c_', 't_') else inline_at)[nd].append(cid)
segs = collections.Counter()
for r in W:
    p, mm = H.route(r)
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
used = set(node_items) | set(inline_at) | {n for k in segs for n in k}
adj = collections.defaultdict(list)
for a, b, mm in L['segments']:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
root = 'BH' if 'BH' in adj else 'ECU'; parent = {root: None}; seglen = {}; todo = [root]; kids = collections.defaultdict(list)
while todo:
    n = todo.pop(0)
    for m, mm in adj[n]:
        if m not in parent: parent[m] = n; seglen[m] = mm; kids[n].append(m); todo.append(m)
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
    x, y = L['nodes'][n]['xy']
    return (int(round((130 - x) * SCX / 30)) * 30, int(round((100 - y) * SCY / 30)) * 30)
bps, bundles = [], []
pos = {n: lpos(n) for n in parent}
allpos = set(pos.values())
STUB = L.get('end_allowance_mm', 100)
for n in parent:
    bps.append({"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}})
for n, p in parent.items():
    if p is None: continue
    bn = {"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(seglen[n]), "unit": "mm"}}
    if via[n]: bn['layoutPoints'] = [{"id": "%s_p%d" % (bn['id'], i), "layoutPosition": {"x": lpos(m)[0], "y": lpos(m)[1]}} for i, m in enumerate(via[n])]
    bundles.append(bn)
# parts on stubs around their node, on the side away from the node's bundles
occupied = set()
for n in parent: occupied.add(pos[n])
def free_dir(n):
    angs = []
    nbrs = ([parent[n]] if parent[n] else []) + kids[n]
    for m in nbrs:
        q = lpos(via[m][0]) if (m in kids[n] and via[m]) else (lpos(via[n][-1]) if (m == parent[n] and via[n]) else pos[m])
        angs.append(math.atan2(q[1] - pos[n][1], q[0] - pos[n][0]))
    best = None
    for k in (0, 4):
        a = k * math.pi / 4
        d = min([abs((a - b + math.pi) % (2 * math.pi) - math.pi) for b in angs] or [math.pi])
        tip = (pos[n][0] + 200 * math.cos(a), pos[n][1] + 200 * math.sin(a))
        clr = min([math.hypot(tip[0] - q[0], tip[1] - q[1]) for m, q in pos.items() if m != n] or [999])
        sc = (d >= math.pi / 4 - 1e-6, min(clr, 300), d)
        if best is None or sc > best[0]: best = (sc, a)
    return best[1]
INL_AT = {}
ALLC = {}
for x in list(conns.values()) + list(terms.values()) + inl: ALLC[x['id']] = x
TREESEG = []
for n, p in parent.items():
    if p is None: continue
    ch = [pos[p]] + [lpos(m) for m in via[n]] + [pos[n]]
    TREESEG += list(zip(ch, ch[1:]))
def sdist(q, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]; ll = vx * vx + vy * vy or 1
    u = max(0, min(1, ((q[0] - a[0]) * vx + (q[1] - a[1]) * vy) / ll))
    return math.hypot(q[0] - a[0] - u * vx, q[1] - a[1] - u * vy)
def arrangements(n, k):
    x0, y0 = pos[n]
    out = []
    for sx in (1, -1):        # a column (or two) beside the node
        pts = []
        for i in range(k):
            cc, row = divmod(i, 6); m = min(6, k - cc * 6)
            pts.append((x0 + sx * (120 + 270 * cc), y0 + int((row - (m - 1) / 2) * 60 // 30) * 30))
        out.append((sx, 0, pts))
    for sy in (1, -1):        # a grid of 3 wide above / below
        pts = []
        for i in range(k):
            row, cc = divmod(i, 3); m = min(3, k - row * 3)
            pts.append((x0 + int((cc - (m - 1) / 2) * 210 // 30) * 30, y0 + sy * (120 + 60 * row)))
        out.append((0, sy, pts))
    return out
for n in parent:
    items = node_items.get(n, [])
    k = len(items)
    best = None
    for sx, sy, pts in arrangements(n, max(k, 1)):
        clr = min([sdist(q, a, b) for q in pts for a, b in TREESEG if pos[n] not in (a, b)] +
                  [math.hypot(q[0] - v[0], q[1] - v[1]) for q in pts for v in occupied if v != pos[n]] + [999])
        sc = (min(clr, 150), sx != 0)
        if best is None or sc > best[0]: best = (sc, sx, sy, pts)
    _, sxx, syy, pts = best
    dx, dy = sxx, syy
    for cid, q in zip(items, pts):
        q = list(q)
        while tuple(q) in occupied: q[1] += 30
        occupied.add(tuple(q))
        ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
        bundles.append({"id": "bn_" + cid, "sourceId": "bp_" + sid(n), "targetId": cid, "length": {"value": STUB, "unit": "mm"}})
    if not dx: dx = -1 if pos[n][0] > 2000 else 1
    ins = inline_at.get(n, [])
    for i, cid in enumerate(ins):     # inline parts sit by their node, opposite their stubs
        cc, row = divmod(i, 5)
        m = min(5, len(ins) - cc * 5)
        sx = int(round(dx)) or 1
        q = [pos[n][0] - sx * (60 + 180 * cc), pos[n][1] + int((row - (m - 1) / 2) * 30 // 30) * 30]
        while tuple(q) in occupied or (q[0] - sx * 60, q[1]) in occupied: q[1] += 30
        occupied.add(tuple(q)); occupied.add((q[0] - sx * 60, q[1]))
        # each inline part sits on its own 100 mm end-allowance stub (a branch point), like the plugs do
        sbp = "bp_" + cid
        bps.append({"id": sbp, "layoutPosition": {"x": q[0], "y": q[1]}})
        bundles.append({"id": "bn_" + cid, "sourceId": "bp_" + sid(n), "targetId": sbp, "length": {"value": STUB, "unit": "mm"}})
        ALLC[cid]['layoutPosition'] = {"x": q[0] - sx * 60, "y": q[1]}; ALLC[cid]['locationId'] = sbp
        INL_AT[cid] = "bp_" + sid(n)
# expected lengths per conductor: path of bundles
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
for c in list(conns.values()) + list(terms.values()):
    pass
loc = {}
for b in bundles:
    if b['targetId'][:2] in ('c_', 't_'): loc[b['targetId']] = (b['sourceId'], b['length']['value'])
for x in inl: loc[x['id']] = (INL_AT[x['id']], STUB)
def chain(bp):
    out = []
    while bp: out.append(bp); bp = nodepar[bp]
    return out
def dist(b1, b2):
    c1, c2 = chain(b1), chain(b2)
    common = next(x for x in c1 if x in c2)
    d = 0
    for c in (c1, c2):
        for x in c[:c.index(common)]:
            d += blen[(nodepar[x], x)]
    return d
expect = {}
for w in wires + [co for c in cables.values() for co in [q for q in c['cores'] if 'source' in q]]:
    a, b = w['source'], w['target']
    if not (a and b): continue
    (ba, la), (bb, lb) = loc[a['id']], loc[b['id']]
    lab = w.get('identLabel') or w['id'][3:]
    expect[lab] = la + lb + dist(ba, bb)

# ================================================================== emit
doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG", "schematic": {"connectorWidth": 240},
       "connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
       "resistors": list(resistors.values()), "diodes": list(diodes.values()), "wires": wires, "cables": list(cables.values()),
       "branchPoints": bps, "bundles": bundles, "schematicNotes": notes}
for k, v in doc_parts.items():
    if v: doc[k] = list(v.values())
for k in list(doc):
    if doc[k] == []: del doc[k]
for s in doc.get('splices', []) + doc.get('resistors', []) + doc.get('diodes', []):
    if s.get('partId') is None: s.pop('partId', None)
json.dump(doc, open(os.path.join(OUT, 'abcab%d.json' % DOC), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'abcab%d_lib_ops.json' % DOC), 'w'), indent=1)
json.dump({'%s|%s' % k: [v[1], v[0], v[2]] for k, v in res.items()}, open(os.path.join(OUT, 'abcab%d_routes.json' % DOC), 'w'))
json.dump(expect, open(os.path.join(OUT, 'abcab%d_expect.json' % DOC), 'w'), indent=1)
nconn = len(wires) + sum(len(c['cores']) + (1 if 'shield' in c else 0) for c in cables.values())
print('connectors', len(conns), 'terminals', len(terms), 'splices', len(splices), 'res', len(resistors), 'diodes', len(diodes),
      'wires', len(wires), 'cables', len(cables), 'conductors', nconn, 'bundles', len(bundles), 'bps', len(bps), 'DEVX', DEVX,
      'lib adds', [o['value']['partNumber'] for o in lib_add])
