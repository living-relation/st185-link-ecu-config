"""harness.design copy of ST185-AB-cabin = the ECU harness, cabin half, in two documents (100-connection plan limit):
"ST185-AB-cabin 1 - bulkhead run Rev A" (every AB-cabin conductor with an end on the bulkhead DRB102-CABIN) and
"ST185-AB-cabin 2 - dash Rev A" (the rest). Viewer only; the master is the source.
Usage: python gen_cabin.py <repo> <out_dir> <1|2>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library).
Writes <out>/abcab<doc>.json (whole document, wires not yet routed), abcab<doc>_lib_ops.json (part-library add ops) and
abcab<doc>_expect.json (routed length per wire id); then route it: python genroute.py <out>/abcab<doc>.json <out>/abcab<doc>_final.json.
Same rules and helpers' shape as gen_abeng.py (README "harness.design"): connectors and terminals 240 wide, each pin its own master
end text, display stripes on +12 V wires, parts from library 5LO8 (new ones from harness-parts.csv), shielded cables drawn as
cables, connectors and splices shared by both documents drawn whole in each (cavities wired in the other one N/C with a note),
formboard layout, compact schematic (bulkhead / far ends left, cables beside them, splices middle, ECU side right). Lengths: the
ST185-harness.layout.json tree (AB-cabin's placement-editor layout plus the glove-box breakout GB_T, DECISIONS B8), checked here
against the master est_length_mm. gen_abeng.py runs on import, so its helpers are not imported."""
import sys, os, json, re, collections, math, csv, copy
REPO, OUT, DOC = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert DOC in (1, 2), 'doc is 1 (bulkhead run) or 2 (dash)'
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
import genroute
H = B.Harness('ST185-harness')
NAME, REV, DATE = 'AB-cabin', 'A', '2026-11-03'
TITLES = {1: 'ST185-AB-cabin 1 - bulkhead run', 2: 'ST185-AB-cabin 2 - dash'}
TITLE, OTHER = TITLES[DOC], TITLES[3 - DOC] + ' Rev ' + REV
BHN = 'DRB102-CABIN'
def doc_of(r): return 1 if BHN in (r['from_id'], r['to_id']) else 2
def spare_doc(c): return 1 if c == BHN else 2      # a spare cavity is listed in the document of its plug's main run
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
W_ALL = [r for r in ROWS if r['wire_id']]
W = [r for r in W_ALL if doc_of(r) == DOC]
SPARE_ALL = [r for r in ROWS if not r['wire_id']]
PASS = [r for r in ALL if r['harness'] != NAME and NAME in (r.get('passes_through') or '')]
PARTS_CSV = {p['part_number']: p for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8'))}
LIB = json.load(open(os.path.join(OUT, 'lib.json')))['parts']
for k in ('lockParts', 'contactParts', 'connectorParts', 'cableParts', 'wireParts', 'spliceParts', 'cavityPlugParts', 'resistorParts',
          'diodeParts', 'terminalParts'): LIB.setdefault(k, [])
def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
def col(c): return c if c in COLORS else "Gray"
# display stripes on +12 V wires, one per circuit (README "Display stripes"; tracing only, the master stays plain red). Cable
# cores keep their cable part's colours, so only loose red wires are striped. Same colour per circuit as gen_abeng.py where the
# circuit crosses the bulkhead (INJ, COP, SW12, LAM, STR, REV, EPSEN).
STRIPE = {'INJ': ('Blue', 'injector feed'), 'COP': ('White', 'coil feed'), 'SW12': ('Green', 'switched +12 V (ECU A5, SW12 bus, fuel pump relay coil)'),
          'LAM': ('Violet', 'CAN-Lambda feed'), 'STR': ('Orange', 'starter S'), 'REV': ('Pink', 'reverse switch feed'),
          'EPSEN': ('Gray', 'steering pump enable'), 'ACC': ('Yellow', 'A/C clutch relay coil feed'), 'ETB': ('Brown', 'throttle motor feed'),
          'ALTIG': ('Black', 'alternator IG through the kill switch')}

# ------------------------------------------------------------------ the tree: ST185-harness.layout.json (DECISIONS B8)
STUB = H.layout.get('end_allowance_mm', 100)
def troute(r):
    p, mm = H.route(r)
    assert p is not None, (r['wire_id'], H.problems[-1:])
    return p, mm

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
NEW = {}
ALIAS = {('resistorParts', '1k 1/4W'): '1.0k 1/4W'}     # Dan 2026-11-01: the library's 1.0k part
def lib_pn(kind, pn): return next((p for p in LIB[kind] if p.get('partNumber') == pn), None)
def part_id(kind, pn):
    """library part id for this part number (a NEW part is added from harness-parts.csv); None for TBD / kit / unknown."""
    if not pn or pn.upper().startswith('TBD') or pn.startswith(('factory', 'in kit', 'pigtail', 'solder splice onto')): return None
    pn = ALIAS.get((kind, pn), pn)
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

# ------------------------------------------------------------------ connectors (drawn whole; other-document / harness cavities N/C)
def pkey(p):
    m = re.match(r'(\d+)$', p)
    return (0, int(m.group(1)), '') if m else (1, 0, p)
RELAY_ORDER = ['30', '85', '86', '87', '87a']
def pin_order(p, c='K-'): return (RELAY_ORDER.index(p) if c.startswith('K-') and p in RELAY_ORDER else 99, pkey(p))   # relays 30 85 86 87 87a
conn_ids = list(dict.fromkeys(r[s + '_id'] for r in W for s in ('from', 'to') if r[s + '_type'] == 'connector'))
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
    pins = sorted(use[c], key=lambda p: pin_order(p, c))
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
        mine_w = [u for u in here if u[1] and doc_of(u[2]) == DOC]
        theirs_w = [u for u in here if u[1] and doc_of(u[2]) != DOC]
        if mine_w:
            r, s = mine_w[0][2], mine_w[0][3]
            ct = part_id('contactParts', r[s + '_terminal_pn'])
            if ct and ct != cfg_contact: cv['contactPartId'] = ct
        else:
            cv['notConnected'] = True
            if theirs_w:
                other_owned[c].append((p, OTHER)); cv['cavityPlugPartId'] = None
            elif here and spare_doc(c) != DOC:
                other_owned[c].append((p, OTHER + ' (an AB-cabin spare, listed there)')); cv['cavityPlugPartId'] = None
            elif here:      # an AB-cabin spare: its sealing plug from the master (TBD -> none)
                pl = part_id('cavityPlugParts', here[0][2][here[0][3] + '_terminal_pn'])
                if pl and pl != cfg_plug: cv['cavityPlugPartId'] = pl
            else:
                owners = sorted({u[0] for u in use[c].get(p, [])})
                if owners: other_owned[c].append((p, '/'.join(owners))); cv['cavityPlugPartId'] = None
        cavs.append(cv)
    conns[c] = {"id": "c_" + sid(c), "label": c, "cavities": cavs, "width": 240}
    if cpid: conns[c]['partId'] = cpid
cav_of = {(c, cv['designation']): cv['id'] for c, n in conns.items() for cv in n['cavities']}

# ------------------------------------------------------------------ other ends, wires, cables
terms, splices, resistors, diodes = (collections.OrderedDict() for _ in range(4))
SPLP = {'solder splice': 'GENERIC SOLDER SPLICE', 'crimp splice': 'GENERIC CRIMP SPLICE 14-10'}
spl_pn = collections.defaultdict(set)
DEVNAME = {}      # a factory lead names its device, the master's name before "<id> pin" (README "Pin text", Dan 2026-11-03)
for r in W_ALL:
    for s in ('from', 'to'):
        if r[s + '_type'] == 'OEM':
            m = re.match(r'(.+?) %s pin ' % re.escape(r[s + '_id']), r[s + '_name'])
            if m and not m.group(1).startswith('OEM'): DEVNAME.setdefault(r[s + '_id'], m.group(1))
def tkey(r, s): return r[s + '_id'] + ('-' + r[s + '_pin'] if r[s + '_type'] == 'OEM' else '')
def tlabel(r, s):
    i, p = r[s + '_id'], r[s + '_pin']
    if r[s + '_type'] == 'terminal': return i
    if i in DEVNAME: return '%s (%s) pin %s (factory lead)' % (DEVNAME[i], i, p)
    return '%s pin %s (factory lead)' % (i, p)
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice':
        tp = r[s + '_terminal_pn']; spl_pn[i].add(SPLP.get(tp, tp))
        splices.setdefault(i, {"id": "s_" + sid(i), "label": i})
        return {"id": "s_" + sid(i), "handle": "Splice"}
    if t in ('terminal', 'OEM'):
        k, nm = tkey(r, s), r[s + '_name'].lower()
        ty = 'Ring' if ('ring' in nm or 'stud' in nm or 'bolt' in nm or ' bar' in nm) else 'Loose'
        terms.setdefault(k, {"id": "t_" + sid(k), "label": tlabel(r, s), "type": ty, "width": 240})
        return {"id": "t_" + sid(k), "handle": "Terminal"}
    if t in ('resistor', 'diode'):
        reg, kind, pre = (resistors, 'resistorParts', 'r_') if t == 'resistor' else (diodes, 'diodeParts', 'd_')
        if i not in reg:
            reg[i] = {"id": pre + sid(i), "label": i}
            pid = part_id(kind, r[s + '_housing_pn'])
            if pid: reg[i]['partId'] = pid
        return {"id": pre + sid(i), "handle": "PIN" + p}      # PIN1 / PIN2 -> Left / Right once placed
    if t == 'cable screen': return None      # the screen floats at that end
    raise SystemExit('end type %r (%s): add it to gen_cabin.py' % (t, r['wire_id']))
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
for c in cables.values():   # core order = the cable part's core order (matched by colour); a core with no cabin job (cut back
    order = [k['color'] for k in doc_parts['cableParts'][c['partId']]['cores']]     # and sealed at both ends) still sits in the cable
    have = [co['color'] for co in c['cores']]
    assert all(have.count(x) <= order.count(x) for x in have), (c['label'], order, have)
    for x in order:
        if x not in have: c['cores'].append({"id": "co_%s_nc_%s" % (sid(c['label']), x.lower()), "color": x})
    c['cores'].sort(key=lambda co: order.index(co['color']))
def cseq(c): return c['cores'] + ([c['shield']] if 'shield' in c else [])
CONDS = wires + [co for c in cables.values() for co in cseq(c) if 'source' in co]
NC_CORES = [co for c in cables.values() for co in cseq(c) if 'source' not in co]
def lab(cond): return cond.get('identLabel') or cond['id'][3:]
# pin text (Dan 2026-11-01): each end shows its own master end description (device pins say what the pin does; bulkhead, ECU
# and splice ends name the device - the master's text); a stud lists every description that lands on it
comp = {n['id']: n for n in list(conns.values()) + list(terms.values())}
tdesc = collections.defaultdict(list)
for cond in CONDS:
    r = row_of[lab(cond)]
    for s in ('from', 'to'):
        e = end(r, s)
        if not e or e['id'] not in comp or not r[s + '_desc']: continue
        if e['id'].startswith('t_'):
            if r[s + '_desc'] not in tdesc[e['id']]: tdesc[e['id']].append(r[s + '_desc'])
            continue
        cv = next(cv for cv in comp[e['id']]['cavities'] if cv['id'] == e['handle'])
        assert not cv.get('signal') or cv['signal'] == r[s + '_desc'], (cv['id'], cv.get('signal'), r[s + '_desc'])
        cv['signal'] = r[s + '_desc']
for i, ds in tdesc.items(): comp[i]['signal'] = '; '.join(ds)

# ================================================================== schematic: far ends left, cables, splices, ECU side right
# README "harness.design" (Dan 2026-11-01 / 11-02 / 11-03 N1 a): bulkhead (doc 1) or the far ends (doc 2) left, the cabin halves
# of the shielded runs as cables beside them, splices middle, the ECU plugs and ECU splice-point bus plugs right (doc 1: with
# every other non-bulkhead end); each wire horizontal with one 90 degree jog in its own lane; columns level at the top, the right
# column half a grid lower.
def place_of(cid):
    for r in W:
        for s in ('from', 'to'):
            if r[s + '_type'] in ('connector', 'terminal', 'OEM') and \
                    ("c_" + sid(r[s + '_id']) if r[s + '_type'] == 'connector' else "t_" + sid(tkey(r, s))) == cid:
                return H.place(r, s)
NODES = {n['id']: n for n in list(conns.values()) + list(terms.values())}
def is_ecu_side(n): return n['id'].startswith('c_') and place_of(n['id']) in ('ECU', 'SP')     # ECU plugs + the ECU splice-point bus plugs
if DOC == 1: LEFT_IDS = [conns[BHN]['id']]
else:
    # far ends grouped by where they sit in the car (glove box first, then the sill run, A/C, front, dash, pedal)
    AREA = ['GB', 'RHKICK', 'BATT', 'FUEL', 'ACAMP', 'EVAP', 'AMB', 'ECU', 'CSB3', 'DASH', 'JB1', 'PEDAL']
    LEFT_IDS = sorted([i for i, n in NODES.items() if not is_ecu_side(n)],
                      key=lambda i: (AREA.index(place_of(i)) if place_of(i) in AREA else 99, i.startswith('t_'), NODES[i]['label']))
DEV_IDS = {i for i in NODES if i not in LEFT_IDS}
def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
def cab_h(c): return 30 + 30 * len(cseq(c))
def tap_plug(i):      # factory leads of one plug (A18-8, A18-9, ...) stack touching, like the cavities of a connector
    m = re.match(r't_(.*)_[^_]+$', i); return m.group(1) if m and NODES[i]['label'].endswith('(factory lead)') else i
y, prev = 0, None
for i in LEFT_IDS:
    n = NODES[i]
    if prev is not None:
        y += h(NODES[prev]) + (0 if tap_plug(i) == tap_plug(prev) and 'cavities' not in n else
                               (30 if place_of(i) == place_of(prev) else 60))
    n['schematicPosition'] = {"x": 0, "y": y}; prev = i
LEFT_BOTTOM = y + h(NODES[prev])
def cav_y(n, handle):
    if 'cavities' not in n: return n['schematicPosition']['y'] + 15
    return n['schematicPosition']['y'] + 30 * ([cv['id'] for cv in n['cavities']].index(handle) + 1) + 15
def ends(cond): return [e for e in (cond.get('source'), cond.get('target')) if e]
cab_of = {co['id']: c for c in cables.values() for co in cseq(c)}
used_rows = {cav_y(NODES[e['id']], e['handle']) for cond in CONDS for e in ends(cond) if e['id'] in LEFT_IDS}
taken, cab_rows = collections.defaultdict(set), set()
def core_row(c, co): return c['schematicPosition']['y'] + 30 * (cseq(c).index(co) + 1) + 15
# every cable has an end on the left column (the bulkhead in doc 1, its far plug in doc 2): it sits beside the left column on the
# nearest run of empty rows, so no left pin's wire runs into it, and its splices sit on its core rows
# the hops from the left pins to the cables each take a lane of their own between the two columns
CABLX = 240 + 30 * (3 + sum(1 for c in cables.values() for co in cseq(c) for e in ends(co) if e['id'] in LEFT_IDS))
for c in sorted(cables.values(), key=lambda c: min(cav_y(NODES[e['id']], e['handle']) for co in cseq(c) for e in ends(co) if e['id'] in LEFT_IDS)):
    lefts = [cav_y(NODES[e['id']], e['handle']) for co in cseq(c) for e in ends(co) if e['id'] in LEFT_IDS]
    assert lefts, (c['label'], 'a cable with no end on the left column: add a placement rule')
    want, k = min(lefts), cab_h(c) // 30
    tops = [m for m in range(0, LEFT_BOTTOM + 30 * 60, 30) if not any(m + 30 * j + 15 in used_rows | cab_rows for j in range(k))]
    top = min(tops, key=lambda m: (abs(m + 45 - want), m))
    c['schematicPosition'] = {"x": CABLX, "y": top}
    cab_rows |= {top + 30 * j + 15 for j in range(k)}
N_CR = sum(1 for c in cables.values() for co in cseq(c) for e in ends(co) if e['id'] not in LEFT_IDS)
PX = CABLX + 60 + 30 * max(4, N_CR // 2)       # a resistor / diode with one end on the left column (lanes for the cable cores first)
SPX = PX + 150              # splices fed from the left column (or a cable core)
STEP = 180                  # a part fed only by another inline part sits this far right of it
INL = collections.OrderedDict((n['id'], n) for n in list(splices.values()) + list(resistors.values()) + list(diodes.values()))
def two(i): return i[:2] in ('r_', 'd_')
links = collections.defaultdict(list)
for cond in CONDS:
    es = ends(cond)
    for x in es:
        if x['id'] in INL: links[x['id']].append((cond, x, next((o for o in es if o is not x), None)))
deg = collections.Counter((e['id'], e['handle']) for cond in CONDS for e in ends(cond) if e['id'] in LEFT_IDS)
def left_row(cond, o):
    """the row an inline part's feed comes in on: a left pin, or the core row of a cable"""
    c = cab_of.get(cond['id'])
    if c is not None: return core_row(c, cond)
    if o and o['id'] in LEFT_IDS: return cav_y(NODES[o['id']], o['handle'])
    return None
def free_row(want, x):
    bad = used_rows | cab_rows | taken[x]
    yy = min((v for v in range(15, max(LEFT_BOTTOM, 3000) + 3000, 30) if v not in bad), key=lambda v: (abs(v - want), v))
    taken[x].add(yy); return yy
_y = 15     # provisional right column (label order) so a part fed only from the right finds its rows; re-placed below
for d in sorted(DEV_IDS, key=lambda d: NODES[d]['label']): NODES[d]['schematicPosition'] = {"x": 10 ** 6, "y": _y}; _y += h(NODES[d]) + 30
pending = []
for n in INL.values():      # an inline part fed by one left pin (or a cable core) sits on that row: a straight wire
    x = PX if two(n['id']) else SPX
    st = next((left_row(cond, o) for cond, e, o in links[n['id']] if left_row(cond, o) is not None
               and (cab_of.get(cond['id']) or deg[(o['id'], o['handle'])] == 1) and left_row(cond, o) not in taken[x]), None)
    if st is not None: taken[x].add(st); n['_row'] = st; n['_x'] = x
    else: pending.append(n)
for it in range(8):
    left = []
    for n in pending:
        lys = [left_row(cond, o) for cond, e, o in links[n['id']] if left_row(cond, o) is not None]
        sps = [INL[o['id']] for cond, e, o in links[n['id']] if o and o['id'] in INL and '_row' in INL[o['id']]]
        rys = [cav_y(NODES[o['id']], o['handle']) for cond, e, o in links[n['id']] if o and o['id'] in DEV_IDS]
        if lys:
            x = PX if two(n['id']) else SPX; n['_row'] = free_row(min(lys), x); n['_x'] = x
        elif sps:
            x = max(s['_x'] for s in sps) + STEP; want = sps[0]['_row']
            # a part on its feeding splice's row would block that splice's other wires to the right: it takes the next row
            if two(n['id']) and any(o and o['id'] not in LEFT_IDS and o['id'] != n['id'] for cond, e, o in links[sps[0]['id']]):
                taken[x].add(want)
            if want in taken[x] or want in used_rows | cab_rows: want = free_row(want, x)
            else: taken[x].add(want)
            n['_row'], n['_x'] = want, x
        elif rys and it >= 2: n['_row'] = free_row(sum(rys) / len(rys), SPX); n['_x'] = SPX
        elif it == 7: n['_row'] = free_row(0, SPX); n['_x'] = SPX
        else: left.append(n)
    pending = left
assert not pending, [n['label'] for n in pending]
def other_x(o):
    if o is None: return None
    if o['id'] in LEFT_IDS: return 0
    if o['id'] in DEV_IDS: return 10 ** 6
    n = INL[o['id']]; return n['_x'] if '_x' in n else n['schematicPosition']['x']
# a resistor / diode between two splices that sit left of it: the splice on its far side moves right of it, on its row
for n in [n for n in INL.values() if two(n['id'])]:
    sp = [o for cond, e, o in links[n['id']] if o and o['id'] in INL and INL[o['id']]['_x'] <= n['_x']]
    if len(sp) == 2:
        far = INL[sp[1]['id']]
        if not [1 for cond, e, o in links[far['id']] if o and o['id'] in INL and o['id'] != n['id']]:
            taken[far['_x']].discard(far['_row']); far['_x'] = n['_x'] + STEP + 30
            far['_row'] = n['_row'] if n['_row'] not in taken[far['_x']] else free_row(n['_row'], far['_x'])
            taken[far['_x']].add(far['_row'])
for n in INL.values(): n['schematicPosition'] = {"x": n.pop('_x'), "y": n.pop('_row') - 15}
for n in INL.values():
    if not two(n['id']): continue
    # handles: the end whose far side lies further left goes on Left; a diode keeps anode = pin 1 (anodeOnRight when flipped)
    es = [(e, other_x(o)) for cond, e, o in links[n['id']]]
    xs = {e['handle']: (v if v is not None else 0) for e, v in es}
    if len(xs) == 1:
        hd = next(iter(xs)); hmap = {hd: 'Right' if xs[hd] > n['schematicPosition']['x'] else 'Left'}
    else:
        a, b = sorted(xs, key=lambda k: (xs[k], k)); hmap = {a: 'Left', b: 'Right'}
    if n['id'].startswith('d_') and hmap.get('PIN1') == 'Right': n['anodeOnRight'] = True
    for e, v in es: e['handle'] = hmap[e['handle']]
def row_of_end(e):
    if e['id'] in LEFT_IDS: return cav_y(NODES[e['id']], e['handle'])
    if e['id'] in INL: return INL[e['id']]['schematicPosition']['y'] + 15
    return None
# right column: ordered by the mean row of what feeds it, so lanes cross least (connectors may be reordered, pins never)
bary = collections.defaultdict(list)
for cond in CONDS:
    es = ends(cond)
    for e in es:
        if e['id'] in DEV_IDS:
            c = cab_of.get(cond['id'])
            bary[e['id']] += [core_row(c, cond)] if c else [row_of_end(o) for o in es if o is not e and row_of_end(o) is not None]
DEV_ORDER = sorted(DEV_IDS, key=lambda d: (sum(bary[d]) / len(bary[d]) if bary[d] else 10 ** 6, NODES[d]['label']))
def place_right(devx):
    y = 15
    for d in DEV_ORDER:
        n = NODES[d]; n['schematicPosition'] = {"x": devx, "y": y}
        y += h(n) + 30
    return y - 30
def doc_now():
    return {"connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
            "resistors": list(resistors.values()), "diodes": list(diodes.values()), "wires": wires, "cables": list(cables.values())}
def route_cost(devx):    # (unrouted conductors, conductors that need more than one lane) with the right column at devx
    place_right(devx)
    R_, segs_, res_ = genroute.run(copy.deepcopy(doc_now()))
    return (sum(1 for s in segs_ if res_.get(s['k']) is None), sum(1 for v in res_.values() if v and len(v) > 2))
XMAX = max(n['schematicPosition']['x'] for n in INL.values()) if INL else CABLX
n_right = sum(1 for cond in CONDS for e in ends(cond) if e['id'] in DEV_IDS)
DEVX = (XMAX + 150 + 30 * n_right) // 30 * 30
base = route_cost(DEVX)
print('widest right column x', DEVX, 'routing (unrouted, multi-lane)', base, flush=True)
lo, hi = XMAX + 300, DEVX        # compact (Dan 2026-11-02): the narrowest lane field that routes as cleanly
while hi - lo > 30:
    mid = (lo + hi) // 60 * 30
    if route_cost(mid) <= base: hi = mid
    else: lo = mid
    print('  try', mid, '->', 'ok' if hi == mid else 'worse', flush=True)
DEVX = hi
RIGHT_BOTTOM = place_right(DEVX)
print('right column x', DEVX, 'bottom', RIGHT_BOTTOM, '| left bottom', LEFT_BOTTOM, flush=True)

# ------------------------------------------------------------------ notes
spares = collections.defaultdict(list)
for r in SPARE_ALL:
    if r['from_id'] in conns and spare_doc(r['from_id']) == DOC: spares[r['from_id']].append((r['from_pin'], r['from_terminal_pn']))
left_txt, right_txt = [], []
for c in conns:
    txt = []
    if spares.get(c):
        by = collections.defaultdict(list)
        for p, pl in spares[c]: by[pl if pl and pl != 'TBD' else 'TBD'].append(p)
        txt.append('%s: %s %s (sealing plug from the master: %s).' % (
            c, ('pins %s are' if len(spares[c]) > 1 else 'pin %s is') % ', '.join(sorted((p for p, _ in spares[c]), key=pkey)),
            'AB-cabin spares' if len(spares[c]) > 1 else 'an AB-cabin spare',
            '; '.join('%s %s' % (k, ', '.join(sorted(v, key=pkey))) for k, v in sorted(by.items()))))
    if other_owned.get(c):
        by = collections.defaultdict(list)
        for pin, own in other_owned[c]: by[own].append(pin)
        txt.append('%s: N/C cavities are wired elsewhere - %s.' % (c, '; '.join('%s see %s' % (', '.join(sorted(v, key=lambda p: pin_order(p, c))), k)
                                                                        for k, v in sorted(by.items()))))
    if txt: (left_txt if conns[c]['id'] in LEFT_IDS else right_txt).append(' '.join(txt))
for sname, sp in splices.items():     # a splice shared with the other document or another harness: say where its other legs are
    oth = sorted({(r['harness'] if r['harness'] != NAME else OTHER, r['wire_id']) for r in ALL if r['wire_id']
                  and (r['harness'] != NAME or doc_of(r) != DOC)
                  and any(r[s + '_type'] == 'splice' and r[s + '_id'] == sname for s in ('from', 'to'))})
    if oth:
        by = collections.defaultdict(list)
        for h_, w in oth: by[h_].append(w)
        right_txt.append('%s: its other legs are drawn elsewhere - %s.' % (sname, '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(by.items()))))
if NC_CORES:
    right_txt.append('Cable cores with no AB-cabin job (cut back and sealed under heat-shrink at both ends): %s.' % '; '.join(
        '%s %s' % (cab_of[co['id']]['label'], co['color'].lower()) for co in NC_CORES))
pass_by = collections.defaultdict(list)
for r in PASS: pass_by[r['harness']].append(r['wire_id'])
used_st = sorted({row_of[w['identLabel']]['circuit_id'] for w in wires if 'stripeColor' in w}, key=list(STRIPE).index)
head = [{"id": "n_title", "width": 360,
         "text": "%s Rev %s (%s). Part %d of 2 of AB-cabin, the ECU harness cabin half: %s. The rest of AB-cabin is '%s'; connectors "
                 "and splices shared by both are drawn whole in each, cavities wired in the other part are N/C with a note. Viewer copy "
                 "generated from docs/harness/MASTER-wirelist.csv (harness = AB-cabin) by docs/harness/tools/gen_cabin.py; never a source. "
                 "Schematic: %s left, the cabin halves of the shielded runs as cables beside them, splices middle, %s right; columns level "
                 "at the top (right column half a grid lower, N1 a). Each pin shows its own master end text. %s"
                 "Layout: a formboard of the ST185-harness.layout.json tree (AB-cabin's placement-editor layout, glove-box breakout GB_T), "
                 "straight orthogonal bundles, front of car RIGHT, rear LEFT, driver side UP; drawn length is not to scale; each part on a "
                 "100 mm end-allowance stub; bundle lengths = the master est_length_mm." % (
                     TITLE, REV, DATE, DOC, 'every AB-cabin conductor with an end on the bulkhead DRB102-CABIN' if DOC == 1 else
                     'every AB-cabin conductor with no end on the bulkhead (ECU splice point, glove-box relays and feeds, A/C taps, pedal, '
                     'wheel-speed and fuel inlines, the cabin-to-trunk sill run)', OTHER,
                     'the bulkhead' if DOC == 1 else 'the far ends (glove box, sill run, A/C taps, front, dash, pedal)',
                     'every other end (ECU plugs, ECU splice-point bus plugs, glove box, factory leads)' if DOC == 1 else
                     'the ECU plugs and ECU splice-point bus plugs',
                     ("Wires of other harnesses that ride AB-cabin, not drawn: " + '; '.join(
                         '%s see %s' % (', '.join(v), k) for k, v in sorted(pass_by.items())) + ". ") if pass_by else "")},
        {"id": "n_stripes", "width": 360,
         "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                 "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) +
                 ". Red cable cores keep their cable's colours."}]
def est_h(t): return 30 * (2 + len(t) // 50)       # a 360-wide note: about 50 characters a line, one grid row a line
HEAD_Y = -30 * ((max(est_h(n['text']) for n in head) + 59) // 30)
for i, n in enumerate(head): n['schematicPosition'] = {"x": 390 * i, "y": HEAD_Y}
NOTES = list(head)
N_LL = sum(1 for cond in CONDS if len([e for e in ends(cond) if e['id'] in LEFT_IDS]) == 2)   # left-to-left wires run down the outside
if left_txt: NOTES.append({"id": "n_left", "width": 360, "text": ' '.join(left_txt), "schematicPosition": {"x": -420 - 30 * N_LL, "y": 0}})
if right_txt: NOTES.append({"id": "n_right", "width": 360, "text": ' '.join(right_txt), "schematicPosition": {"x": DEVX + 270, "y": 15}})

# ================================================================== layout: the layout tree as a formboard
node_items, inline_at, seen = collections.defaultdict(list), collections.defaultdict(list), set()
for r in W:
    for s in ('from', 'to'):
        e = end(r, s)
        if e is None: continue
        cid = e['id']
        if cid in seen: continue
        nd = H.place(r, s); assert nd in H.adj, (r['wire_id'], s, nd)
        seen.add(cid); (node_items if cid[:2] in ('c_', 't_') else inline_at)[nd].append(cid)
segs, hroute = collections.Counter(), {}
for r in W:
    p, mm = troute(r); hroute[r['wire_id']] = mm
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
tree_nodes = {n for k in segs for n in k} | set(node_items) | set(inline_at)
adj = collections.defaultdict(list)
for a, b, mm in H.layout['segments']:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
ROOT = 'BH' if DOC == 1 else 'ECU'
assert ROOT in tree_nodes, ROOT
parent, slen, kids = {ROOT: None}, {}, collections.defaultdict(list)
todo = [ROOT]
while todo:
    n = todo.pop(0)
    for m, mm in adj[n]:
        if m not in parent: parent[m] = n; slen[m] = mm; kids[n].append(m); todo.append(m)
assert tree_nodes <= set(parent), tree_nodes - set(parent)
assert sum(len(v) for v in adj.values()) // 2 == len(parent) - 1, 'the segments this document uses are not a tree'
changed = True
while changed:      # fold pass-through nodes into the bundle
    changed = False
    for n in list(parent):
        if parent[n] is None or node_items.get(n) or inline_at.get(n) or len(kids[n]) != 1: continue
        c = kids[n][0]; p = parent[n]
        slen[c] += slen[n]; parent[c] = p
        kids[p] = [c if x == n else x for x in kids[p]]
        del parent[n], slen[n], kids[n]; changed = True; break
for n in [n for n in parent if parent[n] and slen[n] == 0]:   # a 0 mm segment is no bundle: merge its node into its parent
    p = parent[n]
    for c in kids[n]: parent[c] = p
    kids[p] = [x for x in kids[p] if x != n] + kids[n]
    node_items[p] += node_items.pop(n, []); inline_at[p] += inline_at.pop(n, [])
    print('0 mm segment', p, '-', n, ': merged into', p)
    del parent[n], slen[n], kids[n]
# formboard (README "harness.design", Dan 2026-11-02): the tree laid flat on a build table. Straight orthogonal bundles on the
# 30 grid, each branch at 90 degrees; front of the car RIGHT, rear LEFT, driver side UP (each branch heads the way its part of the
# car lies); drawn length is not to scale, every bundle keeps its tree length (= the master's). Each part sits on its 100 mm
# end-allowance stub, combed off the node. A node whose four sides are all taken by bundles combs its parts along the way in.
DV = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}
OPP = {'R': 'L', 'L': 'R', 'U': 'D', 'D': 'U'}
GAP, MINL, ISP, LBL = 60, 150, 60, 240        # clearance, shortest drawn bundle, comb pitch, room for a part's label
ALLC = {x['id']: x for x in list(conns.values()) + list(terms.values()) + list(INL.values())}
XY = H.layout['nodes']
def sub_nodes(n): return [n] + [m for k in kids[n] for m in sub_nodes(k)]
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
    for c in sorted(kids[n], key=lambda c: (-len(sub_nodes(c)), c)):
        v = heading(n, c); left = [d for d in free if d not in asg.values()]
        assert left, ('more branches than directions at', n)
        asg[c] = max(left, key=lambda d: (DV[d][0] * v[0] + DV[d][1] * v[1]) / (math.hypot(*v) or 1))
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
print('formboard width %d .. %d, root node at %.0f%% of the width' % (min(xs), max(xs), 100 * (pos[ROOT][0] - min(xs)) / ((max(xs) - min(xs)) or 1)))
assert all(v[0] % 30 == 0 and v[1] % 30 == 0 for v in pos.values())
bps = [{"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}} for n in parent]
bundles = []
for n, p in parent.items():
    if p is None: continue
    assert pos[n][0] == pos[p][0] or pos[n][1] == pos[p][1], (p, n)
    bundles.append({"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(slen[n]), "unit": "mm"}})
INL_AT = {}
for cid, (nd, q, pts, ow) in stubs.items():
    direct = cid[:2] in ('c_', 't_')
    b = {"id": "bn_" + cid, "sourceId": "bp_" + sid(nd), "targetId": cid if direct else "bp_" + cid, "length": {"value": STUB, "unit": "mm"}}
    if pts: b['layoutPoints'] = [{"id": "%s_p%d" % (b['id'], i), "layoutPosition": {"x": x, "y": y}} for i, (x, y) in enumerate(pts)]
    bundles.append(b)
    ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
    if not direct:
        bps.append({"id": "bp_" + cid, "layoutPosition": {"x": q[0], "y": q[1]}}); ALLC[cid]['locationId'] = "bp_" + cid; INL_AT[cid] = "bp_" + sid(nd)
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
loc = {b['targetId']: (b['sourceId'], b['length']['value']) for b in bundles if b['targetId'][:2] in ('c_', 't_')}
loc.update({i: (INL_AT[i], STUB) for i in INL})
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
NCONN = len(CONDS) + len(NC_CORES)
assert NCONN <= 100, 'over the 100-connection plan limit: split by whole circuits into numbered documents (README)'
doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG", "schematic": {"connectorWidth": 240, "terminalWidth": 240},
       "connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
       "resistors": list(resistors.values()), "diodes": list(diodes.values()), "wires": wires, "cables": list(cables.values()),
       "branchPoints": bps, "bundles": bundles, "schematicNotes": NOTES}
for k, v in doc_parts.items():
    if v: doc[k] = list(v.values())
for k in [k for k in doc if doc[k] == []]: del doc[k]
have = {p['id'] for k, v in doc.items() if k.endswith('Parts') for p in v}
refs = {x['partId'] for k in ('wires', 'splices', 'cables', 'connectors', 'resistors', 'diodes') for x in doc.get(k, []) if x.get('partId')} | \
       {cv[k] for n in doc['connectors'] for cv in n['cavities'] for k in ('contactPartId', 'cavityPlugPartId') if cv.get(k)} | \
       {a['partId'] for k, v in doc.items() if k.endswith('Parts') for p in v for c in p.get('configurations', []) for a in c.get('accessories', [])}
assert refs <= have, refs - have
json.dump(doc, open(os.path.join(OUT, 'abcab%d.json' % DOC), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'abcab%d_lib_ops.json' % DOC), 'w'), indent=1)
json.dump(expect, open(os.path.join(OUT, 'abcab%d_expect.json' % DOC), 'w'), indent=1)
print('doc', DOC, TITLE, 'Rev', REV, '| connectors', len(conns), 'terminals', len(terms), 'splices', len(splices), 'resistors', len(resistors),
      'diodes', len(diodes), 'wires', len(wires), 'cables', len(cables), 'conductors (connections)', NCONN, '(%d cores with no job)' % len(NC_CORES),
      'bundles', len(bundles), 'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect), 'routed +', len(CONDS) - len(expect),
      'one-ended screens | lib adds', [o['value']['partNumber'] for o in lib_add], '| no library part (left unset):', sorted(missing))
