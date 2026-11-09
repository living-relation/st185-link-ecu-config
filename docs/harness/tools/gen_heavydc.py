"""harness.design copy of ST185-HeavyDC (battery cables), file "ST185-HeavyDC Rev D" (viewer only; the master is the source).
Usage: python gen_heavydc.py <repo> <out_dir>   (needs <out>/lib_hdc.json = a dump of part library 5LO8, get_part_library)
Writes <out>/hdc.json (whole document, wires routed with genroute.py) and <out>/hdc_lib_ops.json (part-library add ops).
Built on the gen_engc.py pattern (README "harness.design"): connectors 240 wide, each pin its own master end text, bundle
lengths from HeavyDC's own Route 1 tree (Dan's approved placement, 2026-11-04), checked here against the master
est_length_mm. The RADLOK pass-through pair (`w_rl_pos` / `w_rln`, blank length, Dan D2) is the firewall connector itself:
no wire is drawn; each cabin RADLOK plug is MATED to its engine plug (Dan 2026-11-05), so the harness is two pieces joined
by the two mates, drawn nose to nose. The engine-bay jump bus bar (Blue Sea 2104) is one splice per stud (SP-JUMP-1 .. -4)
joined by INTEGRAL links in stud order, and the alternator fuse block (Blue Sea MRBF 5191) is the INTEGRAL link "MRBF fuse
(Blue Sea 5191)" from stud 3 to its output stud SP-ALT-FUSE (Dan 2026-11-07, N61 a); an INTEGRAL link is drawn as a wire with
no part, no length check and no bundle path: the splices it joins share one stub and location, as gen_cabin.py's bus-plug
bridges join two pins of one plug (0 mm). The POWER box studs are ring terminals named by their stud, each carrying its bar's global signal
("POWER box NEG bar", "POWER box + bar"; Dan N64 a). Stops if a length differs from the master or the file passes 100 connections (plan
limit). gen_engc.py runs on import, so its helpers are not imported."""
import sys, os, json, re, collections, math, csv
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
H = B.Harness('ST185-harness')
NAME, TITLE, REV, DATE = 'HeavyDC', 'ST185-HeavyDC', 'D', '2026-11-07'
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
# the RADLOK pass-through (Dan D2 2026-11-04): a blank-length row joining the two halves of one firewall connector is the
# connector itself, not a wire to cut: not drawn, listed in a note (build_drawings.is_connector_pass)
PT = [r for r in ROWS if r['wire_id'] and B.is_connector_pass(r)]
LINKS = [r for r in ROWS if r['wire_id'] and B.is_integral(r)]     # bar copper / the MRBF fuse block (Dan N55 a): no length
W = [r for r in ROWS if r['wire_id'] and not B.is_connector_pass(r) and not B.is_integral(r)]
assert all(r['est_length_mm'] for r in W), 'a HeavyDC wire has no length: %s' % [r['wire_id'] for r in W if not r['est_length_mm']]
SPARE = [r for r in ROWS if not r['wire_id']]
PASS = [r for r in ALL if r['harness'] != NAME and NAME in (r.get('passes_through') or '')]
assert not any(r['cable'] for r in W), 'HeavyDC has a cable now: draw it as gen_cabin.py does (cores, shield, cores without ends)'
PARTS_CSV = {p['part_number']: p for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8'))}
LIB = json.load(open(os.path.join(OUT, 'lib_hdc.json')))['parts']
def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
def col(c): return c if c in COLORS else "Gray"
# display stripes on +12 V wires, one per circuit (README "Display stripes"; tracing only, the master stays plain red)
STRIPE = {'BAT': ('White', 'battery + (kill switch, POWER box, starter, alternator, jump bus bar, jump post)'), 'FP': ('Orange', 'fuel pump feed')}

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
NEW = {   # library 5LO8 parts this generator added (manufacturer / description come from harness-parts.csv)
    # Blue Sea PowerBar 600A jump bus bar (Dan N15 a 2026-11-05): 4 studs 1-4 like the master pins, a lug per stud
    '2104': {"id": "cp_bluesea_2104", "url": "https://www.bluesea.com/products/2104", "hasShell": False, "numberOfCavities": 4,
             "configurations": [{"id": "cfg", "accessories": [{"id": "cfg-1", "type": "ContactPart", "partId": "ct_lug_stud"}]}]},
}
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
    if cpart and c in B.BOX_CAVITIES:     # a new fuse box with its library part: every landing of the box drawing, vacant seats N/C
        assert set(pins) <= set(B.BOX_CAVITIES[c]), (c, set(pins) - set(B.BOX_CAVITIES[c])); pins = list(B.BOX_CAVITIES[c])
    if cpart and cpart.get('numberOfCavities'): assert len(pins) == cpart['numberOfCavities'], (c, pins, cpart['numberOfCavities'])
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
            if here:      # a HeavyDC spare: its sealing plug from the master (TBD -> none)
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
def stud_splice(i): return bool(B.STUD_SPLICE.match(i))     # a bar stud drawn as a splice: no splice part (its lugs are TBD)
def tkey(r, s):
    t, i, p, nm = r[s + '_type'], r[s + '_id'], r[s + '_pin'], r[s + '_name']
    if t == 'terminal': return i
    return '%s-%s' % (i, p) + (' cowl' if 'cowl lead' in nm.lower() and i == 'W1' else '')
def tlabel(r, s):
    t, i, p, nm = r[s + '_type'], r[s + '_id'], r[s + '_pin'], r[s + '_name']
    if t == 'terminal': return nm if B.BOX_RING.match(i) else i     # a box ring: its stud name, box first (Dan N64 a)
    if i == 'W1': return 'W1 pin %s (%s)' % (p, 'factory cowl lead' if 'cowl lead' in nm.lower() else 'washer motor')
    # a front device's lead names its device, the master's name before "<id> pin", code in parentheses (B22):
    # "LH headlamp (H1) pin 3 (factory lead)" (Dan 2026-11-03); cabin leads (IE1, J/B No.1, IG2, R/B No.4: master
    # name "OEM ...") name the device in their pin text instead
    # a lead whose own master name gives no device (A5 pin 4 "OEM A5, factory Y-R lead") takes it from another end of
    # the same OEM id ("A/C pressure switch A5 pin 1"; DECISIONS A/C paragraph)
    if i in DEVNAME: return '%s (%s) pin %s (factory lead)' % (DEVNAME[i], i, p)
    return '%s pin %s (factory lead)' % (i, p)
DEVNAME = {}
for r in W:
    for s in ('from', 'to'):
        if r[s + '_type'] == 'OEM':
            m = re.match(r'(.+?) %s pin ' % re.escape(r[s + '_id']), r[s + '_name'])
            if m and not m.group(1).startswith('OEM'): DEVNAME.setdefault(r[s + '_id'], m.group(1))
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice':
        tp = r[s + '_terminal_pn']; pid = None if stud_splice(i) else part_id('spliceParts', SPLP.get(tp, tp))
        sp = splices.setdefault(i, {"id": "s_" + sid(i), "label": i})
        if pid: sp['partId'] = pid
        return {"id": sp['id'], "handle": "Splice"}
    if t in ('terminal', 'OEM'):
        k, nm = tkey(r, s), r[s + '_name'].lower()
        ty = 'Ring' if ('ring' in nm or 'stud' in nm or 'bolt' in nm or 'post' in nm) else 'Loose'
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
# INTEGRAL links (Dan N55 a / N61 a): splice to splice, no part, labelled with what they are (the bar copper, "MRBF fuse (Blue Sea 5191)")
link_ids = set()
for r in LINKS:
    lb = '%s: %s' % (r['wire_id'], r['from_desc'])
    wires.append({"id": "w_" + sid(r['wire_id']), "source": end(r, 'from'), "target": end(r, 'to'), "color": "Gray", "identLabel": lb})
    wire_row[lb] = r; link_ids.add(lb)
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
    else: next(cv for cv in comp[i]['cavities'] if cv['id'] == hd)['signal'] = '; '.join(ds)   # a stud cavity lists every lug's text
# a POWER box ring terminal carries its bar's global signal, so every stud on one bar reads as one net (Dan N64 a)
for r in W:
    for s in ('from', 'to'):
        if B.ring_signal(r, s): comp['t_' + sid(tkey(r, s))]['signal'] = B.ring_signal(r, s)
# the notes that sit on an end's row, known before placing so each end gets room for its text (Dan N99 a): OEM splice notes
# (README "Pin text", Dan 2026-11-04 Y6 / N16 a; a blank colour gets no note and is listed) and a connector's N/C / spare note
oem_col, oem_txt, oem_skip = {}, {}, []
for r in W:
    for s, c in B.oem_splices(r):
        tid = 't_' + sid(tkey(r, s))
        if not c: oem_skip.append('%s %s %s' % (r['wire_id'], r[s + '_id'], r[s + '_pin'])); continue
        assert oem_col.setdefault(tid, c) == c, (tid, oem_col[tid], c)
        oem_txt.setdefault(tid, B.oem_splice_note(r, s, c))     # full note (Dan N16 a); a shared tap keeps its first text
CONN_NOTE = collections.OrderedDict()
BOX_SEATS = set(B._seat_map()) | {'LOGIC'}     # box guts are not drawn (Dan R1 a): no spare / N/C notes for box seats
for c, lst in other_owned.items():
    if c in BOX_SEATS: continue
    by = collections.defaultdict(list)
    for pin, own in lst: by[own].append(pin)
    CONN_NOTE[c] = '%s: N/C cavities belong to other harnesses - ' % c + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(by.items()))
spares = collections.defaultdict(list)
for r in SPARE: spares[r['from_id']].append(r['from_pin'])
for c, pins in spares.items():
    if c in BOX_SEATS: continue
    t = '%s: pins %s are HeavyDC spares (not used).' % (c, ', '.join(sorted(pins, key=pkey)))
    CONN_NOTE[c] = t + ' ' + CONN_NOTE[c] if c in CONN_NOTE else t

# ================================================================== schematic: trunk / cabin ends left, engine bay right
def node_of(nm): return conns.get(nm) or terms.get(nm)
# trunk and glove-box ends left (outer column: kill switch, trunk relay block, fuel pump relay, POWER box studs; inner column:
# battery posts, ground points), the RADLOK firewall pairs in the middle (cabin plug, mated to its engine plug: Dan 2026-11-05,
# a mate, not a wire), engine-bay ends right
BOX_T = sorted({tkey(r, s) for r in W for s in ('from', 'to') if r[s + '_type'] == 'terminal' and B.BOX_RING.match(r[s + '_id'])})
LEFT = [['KILL-SW', 'BATT-RELAY-BLOCK', 'K-FP'] + BOX_T,
        ['BATT-POS', 'T-TRUNK-NEG', 'GND-IG', 'GND-ID']]
MID = [(r['from_id'], r['to_id']) for r in PT]          # (cabin plug, engine plug), POS before NEG
MID.sort(key=lambda m: ('NEG' in m[0], m[0]))
RIGHT = [['T-STARTER-B', 'T-ALT-B', 'JUMP-POST'],
         ['T-ENG-BLOCK']]
LEFT = [[n for n in g if node_of(n)] for g in LEFT]
RIGHT = [[n for n in g if node_of(n)] for g in RIGHT]
placed = [n for g in LEFT + RIGHT for n in g] + [n for m in MID for n in m]
assert sorted(placed) == sorted(set(conns) | set(terms)), (set(conns) | set(terms)) ^ set(placed)
def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
def tap_plug(nm):     # factory leads of one plug (H1-1, H1-2, ...) stack touching, like the cavities of a connector
    m = re.match(r'(.*)-\d+( cowl)?$', nm); return m.group(1) if m else nm
def span(nm):         # an end's box with its label tag and the notes on its row (build_drawings.end_span)
    n = node_of(nm)
    return B.end_span(n, [oem_txt[n['id']]] if n['id'] in oem_txt else [CONN_NOTE[nm]] if nm in CONN_NOTE else [])
def stack(names, x, y0, skip=()):
    """one column, top at y0: 30 between parts, factory leads of one plug touching; never a part (with its label and notes)
    on a row in skip. Where an end has text (a terminal's label tag, a note on its row) the step grows to keep it clear of
    the next end (Dan N99 a, 2026-11-08: spread out only where the text is)"""
    y, prev = y0, None
    for nm in names:
        n = node_of(nm); sp = span(nm); top, bot = B.span_rows(sp)
        if prev is not None:
            pn = node_of(prev)
            y += max(h(pn) + (0 if 'cavities' not in n and 'cavities' not in pn and tap_plug(nm) == tap_plug(prev) else 30),
                     B.text_step(span(prev), sp))
        while any(y + top < r < y + bot for r in skip): y += 30
        n['schematicPosition'] = {"x": x, "y": y}; prev = nm
    return y + h(node_of(prev)) if prev else y0
# compact (README "Schematic", Dan 2026-11-02): the cabin end is two columns, the fuse / relay boxes and kill switch outside,
# the factory cabin taps inside; a box pin's wire runs out between the taps (no tap sits on a used box row)
XO = -90 - 240 - 180     # the 180 gap holds the OEM splice notes of the cabin taps (below), clear of the box column
stack(LEFT[0], XO, 0)
box_rows = {n['schematicPosition']['y'] + 30 * (i + 1) + 15 for nm in LEFT[0] for n in [node_of(nm)] if 'cavities' in n
            for i, cv in enumerate(n['cavities']) if not cv.get('notConnected')} | \
           {node_of(nm)['schematicPosition']['y'] + 15 for nm in LEFT[0] if 'cavities' not in node_of(nm)}   # a box ring terminal's row
LEFT_BOTTOM = max(stack(LEFT[1], -90, 0, box_rows), max(node_of(nm)['schematicPosition']['y'] + h(node_of(nm)) for nm in LEFT[0]))
# the firewall column: each cabin RADLOK plug takes its wire on its left (from the boxes), its mated engine plug sends its wire
# right (to the engine bay); the pair sits on one row so the mate line is short and level; genroute reads `_exit`
MX = 150 + 30 * 8                  # 8 lanes between the inner left column and the cabin plugs
for k, (cab, eng) in enumerate(MID):
    y = 300 + 150 * k
    conns[cab]['schematicPosition'] = {"x": MX, "y": y}; conns[cab]['_exit'] = 'L'
    conns[eng]['schematicPosition'] = {"x": MX + 360, "y": y}; conns[eng]['_exit'] = 'R'
mates = [{"id": "m_" + sid(r['wire_id']), "sourceId": conns[r['from_id']]['id'], "targetId": conns[r['to_id']]['id']} for r in PT]
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
SPX = MX + 360 + 240 + 120          # (no splices) right of the firewall column
for n in inl:
    if '_row' in n: n['schematicPosition'] = {"x": SPX, "y": n['_row'] - 15}
n_right = sum(1 for w in wires if w['source']['id'] in RIGHT_IDS or w['target']['id'] in RIGHT_IDS)
DEVX = (SPX + 150 + 30 * n_right) // 30 * 30          # room for one lane per conductor that lands on the front column
def place_right(devx):
    y = 15     # device rows sit half a grid off the cabin rows, so no front pin shares a row with a cabin pin or splice
    for g in RIGHT:       # side order, top level with the left column (Dan 2026-11-02: not pushed down to its feeders)
        y = stack(g, devx, y) + 60
    for n in pending:   # a splice with only front ends sits just left of the front column, on the row of its top front pin
        rys = [cav_y(NODES[o['id']], o['handle']) for w, x, o in links[n['id']] if o['id'] in RIGHT_IDS]
        if rys: n['schematicPosition'] = {"x": devx - 240, "y": min(rys) - 15}
    # a bar stud splice with no front end (jump bar studs 1 and 3): beside its linked neighbour, on the nearest free row of the column
    for it in range(len(pending)):
        for n in pending:
            if 'schematicPosition' in n and n['schematicPosition']['x'] == devx - 240: continue
            nb = [INLN[o['id']]['schematicPosition']['y'] for w, x, o in links[n['id']] if o['id'] in INLN
                  and INLN[o['id']].get('schematicPosition', {}).get('x') == devx - 240]
            if not nb: continue
            busy = {m['schematicPosition']['y'] for m in pending if m is not n and m.get('schematicPosition', {}).get('x') == devx - 240}
            yy = min((v for v in range(-15, 6000, 30) if v not in busy), key=lambda v: (abs(v - (min(nb) - 30)), v))
            n['schematicPosition'] = {"x": devx - 240, "y": yy}
    assert all(n.get('schematicPosition', {}).get('x') == devx - 240 for n in pending), [n['label'] for n in pending]
    return y - 60
import copy, genroute
def route_cost(devx):    # (unrouted wires, wires that need two lanes) with the front column at devx
    place_right(devx)
    R_, segs_, res_ = genroute.run(copy.deepcopy({"connectors": list(conns.values()), "terminals": list(terms.values()),
                                                  "splices": list(splices.values()), "wires": wires}))
    return (sum(1 for s in segs_ if res_.get(s['k']) is None), sum(1 for v in res_.values() if v and len(v) > 2))
base = route_cost(DEVX)
# compact (Dan 2026-11-02): the narrowest lane field that routes as cleanly, with the splice column (where the cabin side
# meets the engine bay) kept inside the centre third of the page (Dan 2026-11-02 (J1))
DMIN = int(XO + (SPX + 15 - XO) / 0.6 - 240 + 29) // 30 * 30
for devx in range(max(SPX + 360, DMIN), DEVX, 30):
    if route_cost(devx) <= base: DEVX = devx; break
print('front column x', DEVX, 'routing (unrouted, two-lane wires)', base)
RIGHT_BOTTOM = place_right(DEVX)
TOPS = [node_of(g[0])['schematicPosition']['y'] for g in (LEFT[0], LEFT[1], RIGHT[0])]
MID_IDS = {conns[n]['id'] for m in MID for n in m}
print('schematic top y: left', TOPS[:2], '| right', TOPS[2], '| bottom left', LEFT_BOTTOM, 'right', RIGHT_BOTTOM, '| width', XO, '..', DEVX + 240)
assert TOPS[0] == TOPS[1] == TOPS[2] - 15, TOPS
for n in inl: n.pop('_row', None)
notes = []
# the jump bus bar: what its stud splices and INTEGRAL links are (Dan 2026-11-07)
if LINKS:
    p = splices['SP-JUMP-1']['schematicPosition'] if 'SP-JUMP-1' in splices else {"x": DEVX, "y": 0}
    notes.append({"id": "n_jumpbar", "width": 360, "schematicPosition": {"x": DEVX + 270, "y": RIGHT_BOTTOM + 60},
                  "text": "Jump bus bar (Blue Sea PowerBar 600A 2104): one splice per stud, SP-JUMP-1 .. SP-JUMP-4, each with its own lug; "
                          "neighbours joined by INTEGRAL links (the bar's own copper) in stud order - the 1-4 numbering's order along the bar "
                          "is not recorded. Stud 3 carries the Blue Sea MRBF terminal fuse block 5191 with the 175 A fuse 5186, drawn as the "
                          "INTEGRAL link 'MRBF fuse (Blue Sea 5191)' to its output stud SP-ALT-FUSE, where the alternator lead w_alt lands "
                          "(Dan 2026-11-07, N61 a). INTEGRAL links: no length, not bought by the cut list (Dan N55 a)."})
# OEM splice notes (README "Pin text", Dan 2026-11-04 Y6): every wire spliced onto a factory wire gets a note on that wire,
# "Splice to OEM wire <colour> - <OEM code> pin <n>, <circuit>, <place>" (build_drawings.oem_splice_note, Dan N16 a); it sits on the
# wire's row just outside its factory-lead end (a cabin tap: left of it, text right-aligned; a front lead: right of it), so
# it covers no lane; genroute.py keeps wires out of it. A blank colour gets no note and is listed (texts: oem_txt, above).
OEMW = 360                       # the full N16 a note at harness.design's widest note (60-360): about 50 characters a line, three lines
for tid, c in oem_col.items():
    p = NODES[tid]['schematicPosition']; left = tid in LEFT_IDS
    notes.append({"id": "n_oem_" + tid, "text": oem_txt[tid], "width": OEMW, "alignment": "Right" if left else "Left",
                  "schematicPosition": {"x": p['x'] - OEMW if left else p['x'] + NODES[tid]['width'], "y": p['y']}})
print('OEM splice notes', len(oem_col), '| blank colour, no note:', ', '.join(oem_skip) or 'none')
for c, txt in CONN_NOTE.items():      # N/C and spare notes (texts above): beside the box column, or right of the front column
    n = conns[c]
    notes.append({"id": "n_" + sid(c), "text": txt, "width": 360, "schematicPosition": {"x": XO - 390 if c in other_owned and n['id'] in LEFT_IDS else DEVX + 270, "y": n['schematicPosition']['y']}})
for sname, sp in splices.items():     # a splice shared with another harness: say where its other legs are
    oth = sorted({(r['harness'], r['wire_id']) for r in ALL if r['harness'] != NAME and r['wire_id']
                  and any(r[s + '_type'] == 'splice' and r[s + '_id'] == sname for s in ('from', 'to'))})
    if oth:
        notes.append({"id": "n_" + sid(sname), "width": 360, "schematicPosition": {"x": DEVX + 270, "y": sp['schematicPosition']['y']},
                      "text": '%s: its other legs are in other harnesses - %s (the splice is drawn here with its HeavyDC leg only).'
                              % (sname, '; '.join('%s see %s' % (w, h_) for h_, w in oth))})
pass_by = collections.defaultdict(list)
for r in PASS: pass_by[r['harness']].append(r['wire_id'])
pt_txt = '; '.join('%s (%s %s to %s %s)' % (r['wire_id'], r['from_id'], r['from_pin'], r['to_id'], r['to_pin']) for r in PT)
notes.append({"id": "n_title", "width": 360, "schematicPosition": {"x": XO - 390, "y": -390},
              "text": TITLE + " Rev " + REV + " (" + DATE + ", HeavyDC's own Route 1 tree from Dan's approved placement 2026-11-04, Dan's format rules): "
                      "the battery cables (trunk battery, kill switch, trunk relay block feed, POWER box studs, ground points ID / IG, the RADLOK "
                      "firewall pair, starter, alternator, engine block stud, jump bus bar, jump post; the jump bus bar is one splice per stud joined by "
                      "INTEGRAL links, and the alternator lead ends on the output stud of its 175 A fuse block, the INTEGRAL link 'MRBF fuse "
                      "(Blue Sea 5191)' from bar stud 3, Dan 2026-11-07). The POWER box studs are ring terminals named by their stud, each "
                      "carrying its bar's signal (Dan N64 a). Viewer copy generated from docs/harness/MASTER-wirelist.csv "
                      "(harness = HeavyDC) by docs/harness/tools/gen_heavydc.py; never a source. Schematic: trunk and glove-box ends left (boxes and "
                      "kill switch outside, battery posts and ground points inside), the RADLOK firewall pairs in the middle, engine-bay ends right. Each pin shows its own "
                      "master end text. Shared connectors are drawn whole; cavities wired by other harnesses are N/C with a note. The RADLOK "
                      "pass-through is the firewall connector itself, no cable to cut or buy (Dan D2): " + pt_txt + ", drawn as a mate between "
                      "the cabin and engine plugs (Dan 2026-11-05), not a wire. Wires of other "
                      "harnesses that only pass through HeavyDC are not drawn: " + '; '.join('%s see %s' % (', '.join(v), k) for k, v in sorted(pass_by.items())) +
                      ". Layout: a formboard of the Route 1 tree in two pieces mated at the RADLOK plugs (cabin / trunk piece left, engine-bay "
                      "piece right of the firewall plugs), straight orthogonal bundles, front of car RIGHT, rear LEFT, driver side UP; the kill switch, trunk relay block, "
                      "fuel pump relay and battery posts share one trunk node (Dan D3); drawn length is not to scale; each part on a 100 mm "
                      "end-allowance stub; bundle lengths = the master est_length_mm."})
used_st = sorted({r['circuit_id'] for r in W if r['colour'] == 'Red'}, key=list(STRIPE).index)
notes.append({"id": "n_stripes", "width": 360, "schematicPosition": {"x": XO - 810, "y": -390},
              "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                      "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) + "."})

# ================================================================== layout (the Route 1 tree; lengths from the master's tree)
L = H.layout
node_items, inline_at, seen = collections.defaultdict(list), collections.defaultdict(list), set()
def cid_of(r, s):
    t = r[s + '_type']
    if t == 'connector': return conns[r[s + '_id']]['id']
    if t in ('terminal', 'OEM'): return terms[tkey(r, s)]['id']
    return splices[r[s + '_id']]['id']
for r in W + SPARE + LINKS:
    for s in ('from', 'to'):
        if not r[s + '_type']: continue
        cid = cid_of(r, s)
        if cid in seen: continue
        nd = H.place(r, s); assert nd, (r['wire_id'], s)
        seen.add(cid); (node_items if cid[:2] in ('c_', 't_') else inline_at)[nd].append(cid)
# INTEGRAL links (Dan N55 a) have no bundle path, as gen_cabin.py's bus-plug bridges: the splices one chain of links joins
# (the jump bar studs SP-JUMP-1 .. -4 and SP-ALT-FUSE) share ONE stub and location, so each link runs 0 mm; every real
# cable on those splices keeps its 100 mm stub plus its tree path
grp = {}
def gfind(x):
    while grp.get(x, x) != x: x = grp[x]
    return x
for r in LINKS:
    assert H.place(r, 'from') == H.place(r, 'to'), ('an INTEGRAL link whose ends sit on two tree nodes', r['wire_id'])
    a, b = gfind(cid_of(r, 'from')), gfind(cid_of(r, 'to'))
    if a != b: grp[b] = a
co_loc = {}      # splice id -> the linked splice whose stub and location it shares
for nd, items in inline_at.items():
    first = {}
    for cid in items: first.setdefault(gfind(cid), cid)
    co_loc.update({cid: first[gfind(cid)] for cid in items if first[gfind(cid)] != cid})
    inline_at[nd] = [cid for cid in items if cid not in co_loc]
MATE_ORDER = {conns[n]['id']: k for k, m in enumerate(MID) for n in m}
for nd in node_items: node_items[nd].sort(key=lambda c: MATE_ORDER.get(c, -1))
segs, hroute = collections.Counter(), {}
for r in W:
    p, mm = H.route(r); hroute[r['wire_id']] = mm
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
tree_nodes = {n for k in segs for n in k}
adj = collections.defaultdict(list)
for a, b, mm in L['segments']:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
# the harness may be a forest (Route 17, Dan 2026-11-02): the EB block strap is its own piece, and a part whose wires
# never leave its spot (A5 / SP-AC-PSW at the A/C amp) is a piece of one node; each piece must be a tree, drawn on its own
comp_of = {}
for s0 in sorted(tree_nodes, key=lambda n: (n != 'GB', n != 'RL_ENG', n)):
    if s0 in comp_of: continue
    comp_of[s0] = s0; st = [s0]
    while st:
        n = st.pop()
        for m, _ in adj[n]:
            if m not in comp_of: comp_of[m] = s0; st.append(m)
roots = list(dict.fromkeys(comp_of[n] for n in sorted(tree_nodes, key=lambda n: (n != 'GB', n != 'RL_ENG', n))))
for nd in list(node_items) + list(inline_at):
    if nd not in tree_nodes and nd not in roots: roots.append(nd); print('one-node piece', nd)
assert len(segs) == len(tree_nodes) - len([r for r in roots if r in tree_nodes]), 'a HeavyDC piece is not a tree'
assert roots[0] == 'GB', roots
parent = {}; seglen = {}; kids = collections.defaultdict(list)
for root in roots:
    parent[root] = None; todo = [root]
    while todo:
        n = todo.pop(0)
        for m, mm in adj[n]:
            if m not in parent: parent[m] = n; seglen[m] = mm; kids[n].append(m); todo.append(m)
print('pieces (roots):', roots)
for nd in list(node_items) + list(inline_at): assert nd in parent, nd
via = {n: [] for n in parent}
changed = True
while changed:      # fold pass-through nodes into bundle bend points
    changed = False
    for n in list(parent):
        if parent[n] is None or node_items.get(n) or inline_at.get(n) or len(kids[n]) != 1: continue
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
# formboard (README "harness.design", Dan 2026-11-02): the tree laid flat on a build table. Straight orthogonal bundles
# on the 30 grid, each branch at 90 degrees; front of the car RIGHT, rear LEFT, driver side UP (each branch heads the way its
# part of the car lies); drawn length is not to scale, every bundle keeps its tree length (= the master's).
# Each part sits on its 100 mm end-allowance stub, combed off the node; a node's extra branches never cross.
DV = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}
OPP = {'R': 'L', 'L': 'R', 'U': 'D', 'D': 'U'}
GAP, MINL, ISP, LBL = 60, 150, 60, 240        # clearance, shortest drawn bundle, comb pitch, room for a part's label
ALLC = {x['id']: x for x in list(conns.values()) + list(terms.values()) + inl}
STUB = L.get('end_allowance_mm', 100)
def sub_nodes(n): return [n] + [m for k in kids[n] for m in sub_nodes(k)]
def heading(n, c):     # screen vector from n towards the middle of c's part of the car (front right, driver up)
    pts = [L['nodes'][m]['xy'] for m in sub_nodes(c)]
    x0, y0 = L['nodes'][n]['xy']
    return (sum(p[0] for p in pts) / len(pts) - x0, -(sum(p[1] for p in pts) / len(pts) - y0))
def rect(a, b): return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
def hit(r, s, g=GAP): return r[0] - g < s[2] and s[0] - g < r[2] and r[1] - g < s[3] and s[1] - g < r[3]
def mv(p, o): return (p[0] + o[0], p[1] + o[1])
def mvr(r, o): return (r[0] + o[0], r[1] + o[1], r[2] + o[0], r[3] + o[1])
# the engine RADLOK plugs sit on the LEFT of their node, facing the cabin plugs they mate with (rear of the car LEFT)
ITEM_SIDE = {}
def lay(n, din):
    """n's piece of the tree with n at (0, 0): (rects, node positions, stubs {part id: (node, part xy, stub points)})."""
    free = [d for d in 'RULD' if din is None or d != OPP[din]]
    asg = {}
    for c in sorted(kids[n], key=lambda c: (-len(sub_nodes(c)), c)):
        v = heading(n, c); left = [d for d in free if d not in asg.values() and d != ITEM_SIDE.get(n)]
        assert left, ('more branches than directions at', n)
        asg[c] = max(left, key=lambda d: (DV[d][0] * v[0] + DV[d][1] * v[1]) / (math.hypot(*v) or 1))
    items = node_items.get(n, []) + inline_at.get(n, [])
    rects, P, S = [], {n: (0, 0)}, {}
    ray = [rect((-DV[din][0] * 90, -DV[din][1] * 90), (-DV[din][0] * 10 ** 6, -DV[din][1] * 10 ** 6))] if din else []   # the way in
    if items:
        left = [d for d in free if d not in asg.values()]
        assert left, ('no free side for the parts at', n)
        cd = ITEM_SIDE[n] if n in ITEM_SIDE else din if din in left else next(d for d in ('U', 'D', 'R', 'L') if d in left)
        k, (dx, dy) = len(items), DV[cd]
        if dy == 0:     # a column of parts across the end of a horizontal stub
            ys = [ISP * i - 30 * (k - 1) for i in range(k)]; xj = dx * 90
            for cid, yy in zip(items, ys):
                S[cid] = (n, (dx * 150, yy), [(xj, 0), (xj, yy)] if yy else [])
            rects += [rect((dx * 90, 0), (dx * 90, 0)), rect((xj, ys[0]), (dx * (150 + LBL), ys[-1]))]
        else:           # parts combed off a vertical spine, to the front (right) side
            for i, cid in enumerate(items):
                yy = dy * (120 + ISP * i); S[cid] = (n, (120, yy), [(0, yy)])
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
        S.update({cid: (nd, mv(q, o), [mv(p, o) for p in pts]) for cid, (nd, q, pts) in cs.items()})
    return rects, P, S
pos, stubs, allrects, ytop = {}, {}, [], None
for i, root in enumerate(roots):
    if i: ITEM_SIDE[root] = 'L'
    rr, P, S = lay(root, None)
    if i == 0: o = (0, 0)
    else:       # the engine-bay piece: its RADLOK plugs face the cabin plugs they mate with (Dan 2026-11-05), clear of the cabin piece
        pair = [(conns[c]['id'], conns[e]['id']) for c, e in MID if conns[e]['id'] in S and conns[c]['id'] in stubs]
        assert pair, 'a second layout piece that does not mate to the first: ' + root
        cab, eng = pair[0]
        o = (stubs[cab][1][0] + 600 - S[eng][1][0], stubs[cab][1][1] - S[eng][1][1])   # plug faces 120 apart, labels outside
        while any(hit(mvr(r, o), a) for r in rr for a in allrects): o = (o[0] + 30, o[1])
    allrects += [mvr(r, o) for r in rr]
    pos.update({m: mv(q, o) for m, q in P.items()})
    stubs.update({cid: (nd, mv(q, o), [mv(p, o) for p in pts]) for cid, (nd, q, pts) in S.items()})
xs = [r[0] for r in allrects] + [r[2] for r in allrects]
print('formboard width %d .. %d' % (min(xs), max(xs)))
assert all(v[0] % 30 == 0 and v[1] % 30 == 0 for v in pos.values())
bps = [{"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}} for n in parent]
bundles = []
for n, p in parent.items():
    if p is None: continue
    assert pos[n][0] == pos[p][0] or pos[n][1] == pos[p][1], (p, n)
    bundles.append({"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(seglen[n]), "unit": "mm"}})
INL_AT = {}
for cid, (nd, q, pts) in stubs.items():
    b = {"id": "bn_" + cid, "sourceId": "bp_" + sid(nd), "targetId": cid if cid[:2] in ('c_', 't_') else "bp_" + cid, "length": {"value": STUB, "unit": "mm"}}
    if pts: b['layoutPoints'] = [{"id": "%s_p%d" % (b['id'], i), "layoutPosition": {"x": x, "y": y}} for i, (x, y) in enumerate(pts)]
    bundles.append(b)
    ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
    if cid[:2] == 's_':
        bps.append({"id": "bp_" + cid, "layoutPosition": {"x": q[0], "y": q[1]}}); ALLC[cid]['locationId'] = "bp_" + cid; INL_AT[cid] = "bp_" + sid(nd)
for cid, rep in co_loc.items():     # a linked stud splice on its neighbour's stub (no bundle path for the link)
    ALLC[cid]['layoutPosition'] = dict(ALLC[rep]['layoutPosition']); ALLC[cid]['locationId'] = ALLC[rep]['locationId']; INL_AT[cid] = INL_AT[rep]
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
expect = {w['identLabel']: loc[w['source']['id']][1] + loc[w['target']['id']][1] + dist(loc[w['source']['id']][0], loc[w['target']['id']][0])
          for w in wires if w['identLabel'] not in link_ids}
bad = {k: (v, hroute[k], wire_row[k]['est_length_mm']) for k, v in expect.items() if not (v == hroute[k] == int(float(wire_row[k]['est_length_mm'] or -1)))}
assert not bad, 'routed length != tree route != master est_length_mm: %r' % bad
assert sorted(w['identLabel'] for w in wires if w['identLabel'] not in link_ids) == sorted(r['wire_id'] for r in W) and len(link_ids) == len(LINKS)
cav_n = collections.Counter((e['id'], e['handle']) for w in wires for e in (w['source'], w['target']) if e['id'].startswith('c_'))
cav_m = collections.Counter(("c_" + sid(r[s + '_id']), cav_of[(r[s + '_id'], r[s + '_pin'])]) for r in W for s in ('from', 'to') if r[s + '_type'] == 'connector')
# a stud (kill switch main stud) takes several cable lugs; every other cavity takes one wire (the POWER box studs are one ring each)
STUD_CAV = {('c_KILL_SW', 'KILL_SW.MAIN2')}
assert cav_n == cav_m and all(v == 1 or k in STUD_CAV for k, v in cav_n.items()), {k: v for k, v in cav_n.items() if v > 1}
doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG", "schematic": {"connectorWidth": 240, "terminalWidth": 240},
       "connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
       "wires": wires, "mates": mates, "branchPoints": bps, "bundles": bundles, "schematicNotes": notes}
for k, v in doc_parts.items():
    if v: doc[k] = list(v.values())
have = {p['id'] for k, v in doc.items() if k.endswith('Parts') for p in v}
refs = {x['partId'] for x in wires + inl + list(conns.values()) if x.get('partId')} | \
       {cv[k] for n in conns.values() for cv in n['cavities'] for k in ('contactPartId', 'cavityPlugPartId') if cv.get(k)} | \
       {a['partId'] for k, v in doc.items() if k.endswith('Parts') for p in v for c in p.get('configurations', []) for a in c.get('accessories', [])}
assert refs <= have, refs - have
assert len(wires) <= 100, 'HeavyDC passes the 100-connection plan limit (%d wires): split it by device (README)' % len(wires)
R_, segs_, res_ = genroute.run(doc)
unrouted = genroute.apply(doc, segs_, res_)
assert not unrouted, 'unrouted wires: %r' % unrouted
for n in conns.values(): n.pop('_exit', None)
B.relabel(doc)          # Dan's plain-label rules R1-R9 (2026-11-08), after placement so positions stay
print('empty connectors dropped (R5):', B.relabel.removed)
B.box_groups(doc)       # box seat ends as labelled terminals, no box groups, unused parts pruned (Dan R1 a)
json.dump(doc, open(os.path.join(OUT, 'hdc.json'), 'w'), indent=1)   # routed: upload as is (no separate genroute.py pass)
json.dump(lib_add, open(os.path.join(OUT, 'hdc_lib_ops.json'), 'w'), indent=1)
print('connectors', len(doc.get('connectors', [])), 'terminals', len(doc.get('terminals', [])), 'splices', len(doc.get('splices', [])), 'wires', len(doc.get('wires', [])), 'cables 0', 'bundles', len(bundles),
      'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect), '| lib adds', [o['value']['partNumber'] for o in lib_add],
      '| no library part (left unset):', sorted(missing))
