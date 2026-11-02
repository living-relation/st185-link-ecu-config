"""harness.design copy of ST185-EngineRoom-C = harness C, document lD37 (viewer only; the master is the source).
Usage: python gen_engc.py <repo> <out_dir>   (needs <out>/lib_engc.json = a dump of part library 5LO8, get_part_library)
Writes <out>/ld37.json (whole document, wires not yet routed) and <out>/ld37_lib_ops.json (part-library add ops); then
route it: python genroute.py <out>/ld37.json <out>/ld37_final.json. Same rules as gen_cabin.py (README "harness.design"):
connectors 240 wide, each pin its own master end text, ground studs drawn on their side of the car (LH at EB, RH at EA),
bundle lengths from the Route 17 tree (checked here against the master est_length_mm). gen_cabin.py runs on import, so its
helpers are not imported; the tree, routes and lengths come from build_drawings.Harness."""
import sys, os, json, re, collections, math, csv
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
H = B.Harness('ST185-harness')
NAME, TITLE = 'EngineRoom-C', 'ST185-EngineRoom-C'
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
W = [r for r in ROWS if r['wire_id']]
SPARE = [r for r in ROWS if not r['wire_id']]
PASS = [r for r in ALL if r['harness'] != NAME and NAME in (r.get('passes_through') or '')]
assert not any(r['cable'] for r in W), 'EngineRoom-C has a cable now: draw it as gen_cabin.py does (cores, shield, cores without ends)'
PARTS_CSV = {p['part_number']: p for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8'))}
LIB = json.load(open(os.path.join(OUT, 'lib_engc.json')))['parts']
def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
def col(c): return c if c in COLORS else "Gray"
# display stripes on +12 V wires, one per circuit (README "Display stripes"; tracing only, the master stays plain red)
STRIPE = {'RTM': ('White', 'retract motor feeds'), 'HHI': ('Blue', 'high beam'), 'HLO': ('Green', 'low beam'),
          'CLR': ('Violet', 'clearance and marker lamps'), 'TURN': ('Light Blue', 'front turn lamps'), 'WIP': ('Black', 'wiper'),
          'WSH': ('Orange', 'washer'), 'HZ': ('Brown', 'horns'), 'ACC': ('Gray', 'A/C clutch'), 'FAN': ('Pink', 'radiator fan'),
          'FAN2': ('Light Green', 'condenser fan'), 'HL': ('Tan', 'LH headlight feed'), 'HR': ('Maroon', 'RH headlight feed'),
          'DM': ('Light Gray', 'dome (DM)'), 'WL': ('Black', 'door lock (WL)'), 'EPS': ('Light Yellow', 'steering pump'),
          'ALTIG': ('Yellow', 'alternator IG')}

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
NEW = {'52-45780': {"id": "cp_longacre_52_45780", "hasShell": False, "numberOfCavities": 4}}   # kill switch: 4 stud terminals
def part_id(kind, pn):
    """library part id for this part number (a NEW part is added from harness-parts.csv); None for TBD / factory / unknown."""
    if not pn or pn.upper().startswith('TBD') or pn.startswith('factory'): return None
    p = next((p for p in LIB[kind] if p.get('partNumber') == pn), None)
    if p: return use_lib(kind, p)
    if pn not in NEW or pn not in PARTS_CSV: missing.add((kind, pn)); return None
    c = PARTS_CSV[pn]
    p = dict(NEW[pn], partNumber=pn, manufacturer=c['manufacturer'], description=c['description'])
    LIB[kind].append(p); lib_add.append({"op": "add", "collection": kind, "value": p})
    return use_lib(kind, p)

# ------------------------------------------------------------------ connectors (drawn whole; other-harness cavities N/C + note)
def pkey(p):
    m = re.match(r'(\d+)$', p)
    return (0, int(m.group(1)), '') if m else (1, 0, p)
RELAY_ORDER = ['30', '85', '86', '87', '87a']
conn_ids = list(dict.fromkeys(r[s + '_id'] for r in W + SPARE for s in ('from', 'to') if r[s + '_type'] == 'connector'))
use, housing = collections.defaultdict(dict), {}
for r in ALL:
    for s in ('from', 'to'):
        c = r[s + '_id']
        if r[s + '_type'] == 'connector' and c in conn_ids:
            use[c].setdefault(r[s + '_pin'], []).append((r['harness'], r['wire_id'], r, s))
            if r[s + '_housing_pn'] and r[s + '_housing_pn'] != 'TBD': housing.setdefault(c, r[s + '_housing_pn'])
conns, other_owned = collections.OrderedDict(), collections.defaultdict(list)
for c in conn_ids:
    cpid = part_id('connectorParts', housing.get(c))
    cpart = doc_parts['connectorParts'].get(cpid) if cpid else None
    pins = sorted(use[c], key=lambda p: (RELAY_ORDER.index(p) if p in RELAY_ORDER else 99, pkey(p)))
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
            if here:      # an EngineRoom-C spare: its sealing plug from the master (TBD -> none)
                pl = part_id('cavityPlugParts', here[0][2][here[0][3] + '_terminal_pn'])
                if pl and pl != cfg_plug: cv['cavityPlugPartId'] = pl
            else:
                owners = sorted({u[0] for u in use[c].get(p, [])})
                if owners: other_owned[c].append((p, '/'.join(owners))); cv['cavityPlugPartId'] = None
        cavs.append(cv)
    conns[c] = {"id": "c_" + sid(c), "label": c, "cavities": cavs, "width": 240}
    if cpid: conns[c]['partId'] = cpid
cav_of = {(c, cv['designation']): cv['id'] for c, n in conns.items() for cv in n['cavities']}

# ------------------------------------------------------------------ other ends, wires
terms, splices = collections.OrderedDict(), collections.OrderedDict()
SPLP = {'solder splice': 'GENERIC SOLDER SPLICE', 'crimp splice': 'GENERIC CRIMP SPLICE 14-10'}
def tkey(r, s):
    t, i, p, nm = r[s + '_type'], r[s + '_id'], r[s + '_pin'], r[s + '_name']
    if t == 'terminal': return i
    return '%s-%s' % (i, p) + (' cowl' if 'cowl lead' in nm.lower() and i == 'W1' else '')
def tlabel(r, s):
    t, i, p, nm = r[s + '_type'], r[s + '_id'], r[s + '_pin'], r[s + '_name']
    if t == 'terminal': return i
    if i == 'W1': return 'W1 pin %s (%s)' % (p, 'factory cowl lead' if 'cowl lead' in nm.lower() else 'washer motor')
    return '%s pin %s (factory lead)' % (i, p)
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice':
        tp = r[s + '_terminal_pn']; pid = part_id('spliceParts', SPLP.get(tp, tp))
        sp = splices.setdefault(i, {"id": "s_" + sid(i), "label": i})
        if pid: sp['partId'] = pid
        return {"id": sp['id'], "handle": "Splice"}
    if t in ('terminal', 'OEM'):
        k, nm = tkey(r, s), r[s + '_name'].lower()
        ty = 'Ring' if ('ring' in nm or 'stud' in nm or 'bolt' in nm) else 'Loose'
        terms.setdefault(k, {"id": "t_" + sid(k), "label": tlabel(r, s), "type": ty, "width": 240})
        return {"id": "t_" + sid(k), "handle": "Terminal"}
    raise SystemExit('end type %r (%s)' % (t, r['wire_id']))
wires, wire_row = [], {}
for r in W:
    w = {"id": "w_" + sid(r['wire_id']), "source": end(r, 'from'), "target": end(r, 'to'), "color": col(r['colour']), "identLabel": r['wire_id']}
    wp = part_id('wireParts', r['wire_pn'])
    if wp: w['partId'] = wp
    if r['colour'] == 'Red': w['stripeColor'] = STRIPE[r['circuit_id']][0]   # a new +12 V circuit needs a STRIPE entry
    wires.append(w); wire_row[r['wire_id']] = r
# pin text (Dan 2026-11-01): each end shows its own master end description; a stud lists every description that lands on it
desc = collections.defaultdict(list)
for w in wires:
    r = wire_row[w['identLabel']]
    for s, e in (('from', w['source']), ('to', w['target'])):
        if e['handle'] != 'Splice' and r[s + '_desc'] and r[s + '_desc'] not in desc[(e['id'], e['handle'])]:
            desc[(e['id'], e['handle'])].append(r[s + '_desc'])
comp = {n['id']: n for n in list(conns.values()) + list(terms.values())}
for (i, hd), ds in desc.items():
    if i.startswith('t_'): comp[i]['signal'] = '; '.join(ds)
    else: next(cv for cv in comp[i]['cavities'] if cv['id'] == hd)['signal'] = ds[0]

# ================================================================== schematic: cabin ends left, splices middle, front right
def node_of(nm): return conns.get(nm) or terms.get(nm)
LEFT = [['LOGIC', 'K-EPS', 'K-ACC', 'K-FAN', 'K-FAN2', 'K-HL', 'K-HR', 'KILL-SW'],
        ['IE1-6', 'IE1-13', 'IE1-20', 'JB1-1H-5', 'IE1-7', 'IE1-8', 'IE1-9', 'IE1-14', 'IE1-15', 'IE1-16', 'IE1-11', 'IE1-18',
         'JB1-1H-4', 'JB1-1H-6', 'JB1-1H-8', 'JB1-2', 'RB2-2', 'RB4-2', 'IG2-16', 'W1-1 cowl', 'W1-2 cowl']]
# front devices by side of the car, driver (LH) side up: a ground stud sits with the side its wires go to (EB LH, EA RH)
RIGHT = [['H1-1', 'H1-2', 'H1-3', 'R2-1', 'R2-2', 'R2-3', 'R2-4', 'R2-5', 'F7-1', 'F7-2', 'F7-3', 'F5-1', 'F5-2', 'GND-EB', 'GND-EB-2'],
         ['F9-1', 'F9-2', 'F9-3', 'F9-4', 'HORN-LH', 'HORN-RH', 'FAN-RAD', 'FAN-RAD-GND', 'FAN-COND', 'FAN-COND-GND', 'A4-4', 'A5-1',
          'ALT-PLUG', 'MRS-A', 'MRS-B', 'MRS-C', 'T-ENG-BLOCK-2', 'T-ENG-BLOCK-3'],
         ['GND-EA', 'H2-1', 'H2-2', 'H2-3', 'R3-1', 'R3-2', 'R3-3', 'R3-4', 'R3-5', 'F8-1', 'F8-2', 'F8-3', 'F6-1', 'F6-2', 'W1-1', 'W1-2']]
LEFT = [[n for n in g if node_of(n)] for g in LEFT]
RIGHT = [[n for n in g if node_of(n)] for g in RIGHT]
placed = [n for g in LEFT + RIGHT for n in g]
assert sorted(placed) == sorted(set(conns) | set(terms)), (set(conns) | set(terms)) ^ set(placed)
def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
y = 0
for gi, g in enumerate(LEFT):
    y += 90 if gi else 0
    for nm in g:
        n = node_of(nm); n['schematicPosition'] = {"x": -90, "y": y}; y += h(n) + (60 if 'cavities' in n else 30)
LEFT_BOTTOM = y
NODES = {n['id']: n for n in list(conns.values()) + list(terms.values())}
LEFT_IDS = {node_of(n)['id'] for g in LEFT for n in g}
RIGHT_IDS = {node_of(n)['id'] for g in RIGHT for n in g}
def cav_y(n, handle):
    if 'cavities' not in n: return n['schematicPosition']['y'] + 15
    return n['schematicPosition']['y'] + 30 * ([cv['id'] for cv in n['cavities']].index(handle) + 1) + 15
used_rows, deg = set(), collections.Counter()
for w in wires:
    for e in (w['source'], w['target']):
        if e['id'] in LEFT_IDS: deg[(e['id'], e['handle'])] += 1; used_rows.add(cav_y(NODES[e['id']], e['handle']))
inl = list(splices.values()); INLN = {n['id']: n for n in inl}
links = collections.defaultdict(list)
for w in wires:
    for x, o in ((w['source'], w['target']), (w['target'], w['source'])):
        if x['id'].startswith('s_'): links[x['id']].append((w, x, o))
def left_row_of(e): return cav_y(NODES[e['id']], e['handle']) if e['id'] in LEFT_IDS else None
taken = set()
def free_row(want):
    yy = min((v for v in range(15, max(LEFT_BOTTOM, 4000), 30) if v not in used_rows and v not in taken), key=lambda v: (abs(v - want), v))
    taken.add(yy); return yy
pending = []
for n in inl:      # a splice fed by one left pin sits on that pin's row (a straight wire)
    st = next((left_row_of(o) for w, x, o in links[n['id']] if left_row_of(o) is not None and deg[(o['id'], o['handle'])] == 1
               and left_row_of(o) not in taken), None)
    if st is not None: taken.add(st); n['_row'] = st
    else: pending.append(n)
for it in range(6):
    left = []
    for n in pending:
        ys = [INLN[o['id']]['_row'] for w, x, o in links[n['id']] if o['id'] in INLN and '_row' in INLN[o['id']]]
        lys = [left_row_of(o) for w, x, o in links[n['id']] if left_row_of(o) is not None]
        if lys: n['_row'] = free_row(min(lys))
        elif ys: n['_row'] = free_row(sum(ys) // len(ys))
        else: left.append(n)
    pending = left
SPX = 150 + 30 * 14 + 120          # 14 lanes between the left column and the splices
for n in inl:
    if '_row' in n: n['schematicPosition'] = {"x": SPX, "y": n['_row'] - 15}
n_right = sum(1 for w in wires if w['source']['id'] in RIGHT_IDS or w['target']['id'] in RIGHT_IDS)
DEVX = (SPX + 150 + 30 * n_right) // 30 * 30          # room for one lane per conductor that lands on the front column
def partner_y(n):
    ys = []
    for w in wires:
        for a, b in ((w['source'], w['target']), (w['target'], w['source'])):
            if a['id'] != n['id']: continue
            if b['id'] in LEFT_IDS: ys.append(cav_y(NODES[b['id']], b['handle']))
            elif b['id'] in INLN and 'schematicPosition' in INLN[b['id']]: ys.append(INLN[b['id']]['schematicPosition']['y'] + 15)
    return ys
y = 0
for gi, g in enumerate(RIGHT):
    y += 90 if gi else 0
    for nm in g:          # keep the side order; drop a device level with what feeds it when that is lower
        n = node_of(nm); ys = partner_y(n)
        y = max(y, (min(ys) - (45 if 'cavities' in n else 15)) // 30 * 30 if ys else y)
        n['schematicPosition'] = {"x": DEVX, "y": y}; y += h(n) + (60 if 'cavities' in n else 30)
for n in pending:   # a splice with only front ends sits just left of the front column, on the row of its top front pin
    rys = [cav_y(NODES[o['id']], o['handle']) for w, x, o in links[n['id']] if o['id'] in RIGHT_IDS]
    n['schematicPosition'] = {"x": DEVX - 240, "y": min(rys) - 15}
for n in inl: n.pop('_row', None)
notes = []
for c, lst in other_owned.items():
    n = conns[c]; by = collections.defaultdict(list)
    for pin, own in lst: by[own].append(pin)
    txt = '%s: N/C cavities belong to other harnesses - ' % c + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(by.items()))
    notes.append({"id": "n_" + sid(c), "text": txt, "width": 360, "schematicPosition": {"x": -480 if n['id'] in LEFT_IDS else DEVX + 270, "y": n['schematicPosition']['y']}})
spares = collections.defaultdict(list)
for r in SPARE: spares[r['from_id']].append(r['from_pin'])
for c, pins in spares.items():
    t = '%s: pins %s are EngineRoom-C spares (sealing plug TBD in the master).' % (c, ', '.join(sorted(pins, key=pkey)))
    ex = next((x for x in notes if x['id'] == 'n_' + sid(c)), None)
    if ex: ex['text'] = t + ' ' + ex['text']
    else: notes.append({"id": "n_" + sid(c), "text": t, "width": 360, "schematicPosition": {"x": DEVX + 270, "y": conns[c]['schematicPosition']['y']}})
pass_by = collections.defaultdict(list)
for r in PASS: pass_by[r['harness']].append(r['wire_id'])
notes.append({"id": "n_title", "width": 360, "schematicPosition": {"x": -480, "y": -390},
              "text": TITLE + ", Rev 5 (2026-11-01, Route 17 tree, Dan's format rules). Viewer copy generated from docs/harness/MASTER-wirelist.csv "
                      "(harness = EngineRoom-C) by docs/harness/tools/gen_engc.py; never a source. Schematic: fuse / relay boxes, kill switch and "
                      "factory cabin taps left, splices middle, front devices right by side of the car (driver / LH side up, RH down); each "
                      "ground stud sits with the side its wires go to (EB LH, EA RH). Each pin shows its own master end text. Shared "
                      "connectors are drawn whole; cavities wired by other harnesses are N/C with a note. Wires of other harnesses that only "
                      "pass through EngineRoom-C are not drawn: " + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(pass_by.items())) +
                      ". Layout: the ST185-harness tree from Route 17 (runs 10 / 11 / 11b; A/C, alternator plug, MR-S pump and block stud via "
                      "Route 16 lines; EA / EB on Route 17 devices 24 / 25, the EB bolt drawn twice for the block strap), front LEFT, driver side "
                      "up; each part on a 100 mm end-allowance stub; bundle lengths = the master est_length_mm."})
used_st = sorted({r['circuit_id'] for r in W if r['colour'] == 'Red'}, key=list(STRIPE).index)
notes.append({"id": "n_stripes", "width": 360, "schematicPosition": {"x": -900, "y": -390},
              "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                      "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) + "."})

# ================================================================== layout (the Route 17 tree; lengths from the master's tree)
L = H.layout
node_items, inline_at, seen = collections.defaultdict(list), collections.defaultdict(list), set()
def cid_of(r, s):
    t = r[s + '_type']
    if t == 'connector': return conns[r[s + '_id']]['id']
    if t in ('terminal', 'OEM'): return terms[tkey(r, s)]['id']
    return splices[r[s + '_id']]['id']
for r in W + SPARE:
    for s in ('from', 'to'):
        if not r[s + '_type']: continue
        cid = cid_of(r, s)
        if cid in seen: continue
        nd = H.place(r, s); assert nd, (r['wire_id'], s)
        seen.add(cid); (node_items if cid[:2] in ('c_', 't_') else inline_at)[nd].append(cid)
segs, hroute = collections.Counter(), {}
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
assert len(segs) == len({n for k in segs for n in k}) - 1, 'harness C layout is not a tree'
root = 'GB'; parent = {root: None}; seglen = {}; todo = [root]; kids = collections.defaultdict(list)
while todo:
    n = todo.pop(0)
    for m, mm in adj[n]:
        if m not in parent: parent[m] = n; seglen[m] = mm; kids[n].append(m); todo.append(m)
for nd in list(node_items) + list(inline_at): assert nd in parent, nd
via = {n: [] for n in parent}
changed = True
while changed:      # fold pass-through nodes into bundle bend points
    changed = False
    for n in list(parent):
        if n == root or node_items.get(n) or inline_at.get(n) or len(kids[n]) != 1: continue
        c = kids[n][0]; p = parent[n]
        seglen[c] += seglen[n]; parent[c] = p; via[c] = via[n] + [n] + via[c]
        kids[p] = [c if x == n else x for x in kids[p]]
        del parent[n], seglen[n], kids[n]; changed = True; break
for n in [n for n in parent if parent[n] and seglen[n] == 0]:   # a 0 mm segment is no bundle: merge its node into its parent
    p = parent[n]
    for c in kids[n]: parent[c] = p; via[c] = via[n] + [n] + via[c]
    kids[p] = [x for x in kids[p] if x != n] + kids[n]
    node_items[p] += node_items.pop(n, []); inline_at[p] += inline_at.pop(n, [])
    print('0 mm segment', p, '-', n, ': merged into', p)
    del parent[n], seglen[n], kids[n], via[n]
SCX, SCY = 27, 24
def lpos(n):
    x, yy = L['nodes'][n]['xy']
    return (int(round((130 - x) * SCX / 30)) * 30, int(round((100 - yy) * SCY / 30)) * 30)
pos = {}
for n in parent:     # a place drawn twice (the EB bolt: stud GND_EB and strap lug GND_EB_S) sits one grid step apart
    q = lpos(n)
    while q in pos.values(): q = (q[0], q[1] + 30)
    pos[n] = q
bps = [{"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}} for n in parent]
bundles = []
for n, p in parent.items():
    if p is None: continue
    bn = {"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(seglen[n]), "unit": "mm"}}
    ch = [pos[p]] + [lpos(m) for m in via[n]] + [pos[n]]
    changed = True
    while changed:            # drop repeated points and A-B-A spikes left by rounding to the 30 grid
        changed = False
        for i in range(len(ch) - 1):
            if ch[i] == ch[i + 1]: del ch[i + 1]; changed = True; break
        else:
            for i in range(len(ch) - 2):
                if ch[i] == ch[i + 2]: del ch[i + 1:i + 3]; changed = True; break
    if ch[1:-1]: bn['layoutPoints'] = [{"id": "%s_p%d" % (bn['id'], i), "layoutPosition": {"x": q[0], "y": q[1]}} for i, q in enumerate(ch[1:-1])]
    bn['_ch'] = ch; bundles.append(bn)
TREESEG = [s for b in bundles for s in zip(b['_ch'], b['_ch'][1:])]
for b in bundles: b.pop('_ch')
occupied = set(pos.values())
ALLC = {x['id']: x for x in list(conns.values()) + list(terms.values()) + inl}
STUB = L.get('end_allowance_mm', 100)
def sdist(q, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]; ll = vx * vx + vy * vy or 1
    u = max(0, min(1, ((q[0] - a[0]) * vx + (q[1] - a[1]) * vy) / ll))
    return math.hypot(q[0] - a[0] - u * vx, q[1] - a[1] - u * vy)
def arrangements(n, k):
    x0, y0 = pos[n]; out = []
    for sx in (1, -1):     # a column (or two) beside the node
        out.append((sx, 0, [(x0 + sx * (120 + 270 * (i // 6)), y0 + int((i % 6 - (min(6, k - i // 6 * 6) - 1) / 2) * 60 // 30) * 30) for i in range(k)]))
    for sy in (1, -1):     # a grid of 3 wide above / below
        out.append((0, sy, [(x0 + int((i % 3 - (min(3, k - i // 3 * 3) - 1) / 2) * 210 // 30) * 30, y0 + sy * (120 + 60 * (i // 3))) for i in range(k)]))
    return out
INL_AT = {}
for n in parent:
    items = node_items.get(n, []); best = None
    for sx, sy, pts in arrangements(n, max(len(items), 1)):
        clr = min([sdist(q, a, b) for q in pts for a, b in TREESEG if pos[n] not in (a, b)] +
                  [math.hypot(q[0] - v[0], q[1] - v[1]) for q in pts for v in occupied if v != pos[n]] + [999])
        sc = (min(clr, 150), sx != 0)
        if best is None or sc > best[0]: best = (sc, sx, sy, pts)
    _, dx, dy, pts = best
    for cid, q in zip(items, pts):
        q = list(q)
        while tuple(q) in occupied: q[1] += 30
        occupied.add(tuple(q)); ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
        bundles.append({"id": "bn_" + cid, "sourceId": "bp_" + sid(n), "targetId": cid, "length": {"value": STUB, "unit": "mm"}})
    sx = int(round(dx)) or (-1 if pos[n][0] > 2000 else 1)
    ins = inline_at.get(n, [])
    for i, cid in enumerate(ins):     # inline parts sit by their node, opposite their stubs, each on its own 100 mm stub
        cc, row = divmod(i, 5); m = min(5, len(ins) - cc * 5)
        q = [pos[n][0] - sx * (60 + 180 * cc), pos[n][1] + int((row - (m - 1) / 2) * 30 // 30) * 30]
        while tuple(q) in occupied or (q[0] - sx * 60, q[1]) in occupied: q[1] += 30
        occupied.add(tuple(q)); occupied.add((q[0] - sx * 60, q[1]))
        bps.append({"id": "bp_" + cid, "layoutPosition": {"x": q[0], "y": q[1]}})
        bundles.append({"id": "bn_" + cid, "sourceId": "bp_" + sid(n), "targetId": "bp_" + cid, "length": {"value": STUB, "unit": "mm"}})
        ALLC[cid]['layoutPosition'] = {"x": q[0] - sx * 60, "y": q[1]}; ALLC[cid]['locationId'] = "bp_" + cid
        INL_AT[cid] = "bp_" + sid(n)
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
loc = {b['targetId']: (b['sourceId'], b['length']['value']) for b in bundles if b['targetId'][:2] in ('c_', 't_')}
loc.update({x['id']: (INL_AT[x['id']], STUB) for x in inl})
def chain(bp):
    out = []
    while bp: out.append(bp); bp = nodepar[bp]
    return out
def dist(b1, b2):
    c1, c2 = chain(b1), chain(b2); common = next(x for x in c1 if x in c2)
    return sum(blen[(nodepar[x], x)] for c in (c1, c2) for x in c[:c.index(common)])

# ================================================================== checks and emit
expect = {w['identLabel']: loc[w['source']['id']][1] + loc[w['target']['id']][1] + dist(loc[w['source']['id']][0], loc[w['target']['id']][0]) for w in wires}
bad = {k: (v, hroute[k], wire_row[k]['est_length_mm']) for k, v in expect.items() if not (v == hroute[k] == int(float(wire_row[k]['est_length_mm'] or -1)))}
assert not bad, 'routed length != tree route != master est_length_mm: %r' % bad
assert sorted(w['identLabel'] for w in wires) == sorted(r['wire_id'] for r in W) and len({w['identLabel'] for w in wires}) == len(W)
cav_n = collections.Counter((e['id'], e['handle']) for w in wires for e in (w['source'], w['target']) if e['id'].startswith('c_'))
cav_m = collections.Counter(("c_" + sid(r[s + '_id']), cav_of[(r[s + '_id'], r[s + '_pin'])]) for r in W for s in ('from', 'to') if r[s + '_type'] == 'connector')
assert cav_n == cav_m and all(v == 1 for v in cav_n.values()), {k: v for k, v in cav_n.items() if v > 1}
doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG", "schematic": {"connectorWidth": 240, "terminalWidth": 240},
       "connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
       "wires": wires, "branchPoints": bps, "bundles": bundles, "schematicNotes": notes}
for k, v in doc_parts.items():
    if v: doc[k] = list(v.values())
have = {p['id'] for k, v in doc.items() if k.endswith('Parts') for p in v}
refs = {x['partId'] for x in wires + inl + list(conns.values()) if x.get('partId')} | \
       {cv[k] for n in conns.values() for cv in n['cavities'] for k in ('contactPartId', 'cavityPlugPartId') if cv.get(k)} | \
       {a['partId'] for k, v in doc.items() if k.endswith('Parts') for p in v for c in p.get('configurations', []) for a in c.get('accessories', [])}
assert refs <= have, refs - have
json.dump(doc, open(os.path.join(OUT, 'ld37.json'), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'ld37_lib_ops.json'), 'w'), indent=1)
print('connectors', len(conns), 'terminals', len(terms), 'splices', len(splices), 'wires', len(wires), 'cables 0', 'bundles', len(bundles),
      'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect), '| lib adds', [o['value']['partNumber'] for o in lib_add],
      '| no library part (left unset):', sorted(missing))
