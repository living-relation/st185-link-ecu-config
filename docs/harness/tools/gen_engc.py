"""harness.design copy of ST185-EngineRoom-C = harness C, file "ST185-EngineRoom-C Rev I" (Rev I 2026-11-12: EngineRoom-C's editor-turn lengths of 2026-11-12 (the A/C pressure switch on Dan's spot; the alternator wires behind the engine on the engine harness trunk start, A6 b), the A/C pressure switch signal to the switch's own plug (A5 fix), the kill switch lead after A1 b, the one mm cabin model (#662), library sync (#664 / #665); Rev H 2026-11-11: splice ends on 25 mm stubs, Dan T7 b, and ghost pass-through wires, Dan T4 a; Rev G 2026-11-10: outside air temp sensor wires owned here, U4 a; trunk start, belt-end drop and block ground leg follow Dan's 2026-11-10 AB-engine routes; Rev F 2026-11-09: Dan's 2026-11-01 device spots restored, route redraw, Dan Z10 b; viewer only; the master is the source).
Usage: python gen_engc.py <repo> <out_dir>   (needs <out>/lib_engc.json = a dump of part library 5LO8, get_part_library)
Writes <out>/ld37.json (whole document, wires not yet routed) and <out>/ld37_lib_ops.json (part-library add ops); then
route it: python genroute.py <out>/ld37.json <out>/ld37_final.json. Same rules as gen_cabin.py (README "harness.design"):
connectors 240 wide, each pin its own master end text, ground studs drawn on their side of the car (LH at EB, RH at EA),
bundle lengths from EngineRoom-C's part of the layout tree (Route 17 node names; checked here against the master est_length_mm). gen_cabin.py runs on import, so its
helpers are not imported; the tree, routes and lengths come from build_drawings.Harness."""
import sys, os, json, re, collections, math, csv
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
H = B.Harness('ST185-harness')
NAME, TITLE, REV, DATE = 'EngineRoom-C', 'ST185-EngineRoom-C', 'I', '2026-11-12'
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
W = [r for r in ROWS if r['wire_id']]
assert not [r['wire_id'] for r in W if B.is_integral(r) or any(B.ring_signal(r, s) for s in ('from', 'to'))], 'EngineRoom-C has an INTEGRAL link or a fuse-box ring terminal now: draw it as gen_heavydc.py / gen_cabin.py do (no length check, the ring carries its bar signal, Dan N55 a / N64 a)'
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
          'FAN2': ('Light Green', 'condenser fan'), 'HL': ('Tan', 'low beams (K-HL)'), 'HR': ('Maroon', 'RH headlight feed'),
          'EPS': ('Light Yellow', 'steering pump'), 'DRL': ('Light Gray', 'DRL feed (K-DRL, RLY-DRL)'),
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
NEW = {'52-45780': {"id": "cp_longacre_52_45780", "hasShell": False, "numberOfCavities": 4},   # kill switch: 4 stud terminals
       # DRL cut relay RLY-DRL (Dan N90 a): Delphi Metri-Pack 280 relay socket, 5 ways (30, 85, 86, 87, 87a), and its contact
       '12110539': {"id": "cp_delphi_12110539", "gender": "Female", "hasShell": False, "numberOfCavities": 5},
       '12129409-L': {"id": "ct_delphi_12129409_l", "type": "Crimp", "gender": "Socket", "contactColor": "Silver",
                      "minGauge": {"value": 16, "unit": "AWG"}, "maxGauge": {"value": 14, "unit": "AWG"}},
       # horn relay K-HORN (LOGIC box, excludeFromBom with the box, N81 a): TE micro relay, 1 form C, 5 blades
       '4-1904124-3': {"id": "cp_rly_micro_co_res", "hasShell": False, "numberOfCavities": 5}}
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
    RELAY_ORDER = ['30', '85', '86', '87', '87a']    # a relay socket is drawn whole: blades with no wire here N/C (as gen_dash)
    if cpart and set(pins) <= set(RELAY_ORDER) and len(pins) < cpart['numberOfCavities'] <= len(RELAY_ORDER):
        pins = RELAY_ORDER[:cpart['numberOfCavities']]
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
            if not m: m = re.match(r'(.+?) %s\b' % re.escape(r[s + '_id']), r[s + '_name'])   # "Ambient air temp sensor A1 (front ...)"
            if m and not m.group(1).startswith('OEM'): DEVNAME.setdefault(r[s + '_id'], m.group(1))
# a wire that continues into another harness file ends on a Loose terminal with its R10 note (DECISIONS R10, Dan 2026-11-09:
# no one-wire splice); key = the master end id, value = (terminal label, note)
R10 = {'SP-AC-SG': ('A/C sensor common splice (in AB-cabin 2)',
                    'to ST185-AB-cabin 2 - straight runs, power, taps and CAN; behind the glove box at the auto A/C amplifier; '
                    '1993 TIS EWD p.211-212; A/C sensor common splice SP-AC-SG, joined to auto A/C amplifier A32 pin 15 (SG) '
                    'by wire w_amb_sg; spliced onto Yellow')}
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if i in R10:
        terms.setdefault(i, {"id": "t_" + sid(i), "label": R10[i][0], "type": "Loose", "width": 240})
        return {"id": "t_" + sid(i), "handle": "Terminal"}
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
# the notes that sit on an end's row, known before placing so each end gets room for its text (Dan N99 a): OEM splice notes
# (README "Pin text", Dan 2026-11-04 Y6 / N16 a; a blank colour gets no note and is listed) and a connector's N/C / spare note
oem_col, oem_txt, oem_skip = {}, {}, []
for r in W:
    for s, c in B.oem_splices(r):
        tid = 't_' + sid(tkey(r, s))
        if not c: oem_skip.append('%s %s %s' % (r['wire_id'], r[s + '_id'], r[s + '_pin'])); continue
        assert oem_col.setdefault(tid, c) == c, (tid, oem_col[tid], c)
        oem_txt.setdefault(tid, B.oem_splice_note(r, s, c))     # full note (Dan N16 a); a shared tap keeps its first text
for k, (lab, txt) in R10.items():     # R10 notes sit where the OEM splice notes do
    if k in terms: oem_col['t_' + sid(k)], oem_txt['t_' + sid(k)] = 'R10', txt
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
    t = '%s: pins %s are EngineRoom-C spares (sealing plug TBD in the master).' % (c, ', '.join(sorted(pins, key=pkey)))
    CONN_NOTE[c] = t + ' ' + CONN_NOTE[c] if c in CONN_NOTE else t

# ================================================================== schematic: cabin ends left, splices middle, front right
def node_of(nm): return conns.get(nm) or terms.get(nm)
LEFT = [['LOGIC', 'K-EPS', 'K-ACC', 'K-FAN', 'K-FAN2', 'K-HL', 'K-HR', 'K-HORN', 'K-DRL', 'RLY-DRL', 'KILL-SW'],
        ['IE1-6', 'IE1-13', 'IE1-20', 'JB1-1H-5', 'IE1-7', 'IE1-8', 'IE1-9', 'IE1-14', 'IE1-15', 'IE1-16', 'IE1-18',
         'JB1-1H-4', 'JB1-1H-6', 'JB1-1H-8', 'RB4-AC-2', 'IG2-16', 'W1-1 cowl', 'W1-2 cowl', 'A32-6', 'SP-AC-SG']]
# a factory tap's key is '<locator>-<pin id>' with the master's own pin id (R/B No.4 'AC-2', J/B No.1 '1H-5'; phase 2)
# front devices by side of the car, driver (LH) side up: a ground stud sits with the side its wires go to (EB LH, EA RH)
RIGHT = [['H1-1', 'H1-2', 'H1-3', 'H1-DRL', 'H1-TURN', 'R2-1', 'R2-2', 'R2-3', 'R2-4', 'R2-5', 'F7-1', 'F7-2', 'F7-3', 'F5-1', 'F5-2', 'GND-EB', 'GND-EB-2'],
         ['F9-1', 'F9-2', 'F9-3', 'F9-4', 'HORN-LH', 'HORN-RH', 'FAN-RAD', 'FAN-RAD-GND', 'FAN-COND', 'FAN-COND-GND', 'A4-4', 'A5-1', 'A5-4',
          'ALT-PLUG', 'MRS-A', 'MRS-B', 'MRS-C', 'T-ENG-BLOCK-2', 'A1-1', 'A1-2'],
         ['GND-EA', 'H2-1', 'H2-2', 'H2-3', 'H2-DRL', 'H2-TURN', 'R3-1', 'R3-2', 'R3-3', 'R3-4', 'R3-5', 'F8-1', 'F8-2', 'F8-3', 'F6-1', 'F6-2', 'W1-1', 'W1-2']]
LEFT = [[n for n in g if node_of(n)] for g in LEFT]
RIGHT = [[n for n in g if node_of(n)] for g in RIGHT]
placed = [n for g in LEFT + RIGHT for n in g]
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
XO = -90 - 240 - 360     # the 360 gap holds the OEM splice notes (N16 a full text) of the cabin taps (below), clear of the box column
stack(LEFT[0], XO, 0)
box_rows = {n['schematicPosition']['y'] + 30 * (i + 1) + 15 for nm in LEFT[0] for n in [node_of(nm)]
            for i, cv in enumerate(n['cavities']) if not cv.get('notConnected')}
LEFT_BOTTOM = max(stack(LEFT[1], -90, 0, box_rows), max(node_of(nm)['schematicPosition']['y'] + h(node_of(nm)) for nm in LEFT[0]))
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
def place_right(devx):
    y = 15     # device rows sit half a grid off the cabin rows, so no front pin shares a row with a cabin pin or splice
    for g in RIGHT:       # side order, top level with the left column (Dan 2026-11-02: not pushed down to its feeders)
        y = stack(g, devx, y) + 60
    for n in pending:   # a splice with only front ends sits just left of the front column, on the row of its top front pin
        rys = [cav_y(NODES[o['id']], o['handle']) for w, x, o in links[n['id']] if o['id'] in RIGHT_IDS]
        n['schematicPosition'] = {"x": devx - 240, "y": min(rys) - 15}
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
print('schematic top y: left', TOPS[:2], '| right', TOPS[2], '| bottom left', LEFT_BOTTOM, 'right', RIGHT_BOTTOM, '| width', XO, '..', DEVX + 240)
assert TOPS[0] == TOPS[1] == TOPS[2] - 15, TOPS
for n in inl: n.pop('_row', None)
notes = []
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
        t = ('%s: its other legs are in other harnesses - %s (the splice is drawn here with its EngineRoom-C leg only).'
             % (sname, '; '.join('%s see %s' % (w, h_) for h_, w in oth)))
        def clear(x, y):    # no other note's text where this one would sit (Dan N99 a)
            return not any(abs(o['schematicPosition']['x'] - x) < 360 and abs(o['schematicPosition']['y'] - y) < (B.note_h(o['text']) + B.note_h(t)) / 2 + 5
                           for o in notes)
        y0 = sp['schematicPosition']['y']     # on the splice's row, else beside the front-column notes, else a little lower
        x, y = next(((x, y0 + dy) for dy in range(0, 181, 30) for x in (DEVX + 270, DEVX + 270 + 390) if clear(x, y0 + dy)), (None, y0))
        if x is None: x = DEVX + 270 + 390; print('note overlap left:', sname)
        notes.append({"id": "n_" + sid(sname), "width": 360, "schematicPosition": {"x": x, "y": y}, "text": t})
notes.append({"id": "n_title", "width": 360, "schematicPosition": {"x": XO - 390, "y": -390},
              "text": TITLE + " Rev " + REV + " (" + DATE + ", EngineRoom-C's part of the layout tree: Dan's device spots with his 2026-11-12 save, the alternator behind the engine (A6 b), Dan's format rules). Viewer copy generated from docs/harness/MASTER-wirelist.csv "
                      "(harness = EngineRoom-C) by docs/harness/tools/gen_engc.py; never a source. Schematic: cabin ends left (fuse / relay boxes and kill switch "
                      "outside, factory cabin taps inside), splices middle, front devices right by side of the car (driver / LH side up, RH down), columns level at the top; each "
                      "ground stud sits with the side its wires go to (EB LH, EA RH). Each pin shows its own master end text. Shared "
                      "connectors are drawn whole; cavities wired by other harnesses are N/C with a note. " + B.GHOST_MARK +
                      "Layout: a formboard of EngineRoom-C's part of the layout tree (run 10 from the RH fender exit, the A/C pressure switch on it; run 11 the wiper from the "
                      "LH pass-through; the alternator plug off the engine harness trunk start, behind the engine (Route 16 L1, A6 b); EA / EB on Route 17 "
                      "devices 24 / 25, the EB bolt drawn twice for the block strap, which is its own piece below), "
                      "straight orthogonal bundles, front of car RIGHT, rear LEFT, driver side UP; drawn length is not to scale; each part on a 100 mm "
                      "end-allowance stub (a splice on a 25 mm stub, Dan T7 b); bundle lengths = the master est_length_mm."})
used_st = sorted({r['circuit_id'] for r in W if r['colour'] == 'Red'}, key=list(STRIPE).index)
notes.append({"id": "n_stripes", "width": 360, "schematicPosition": {"x": XO - 810, "y": -390},
              "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                      "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) + "."})

# ================================================================== layout (the Route 17 tree; lengths from the master's tree)
L = H.layout
node_items, inline_at, seen = collections.defaultdict(list), collections.defaultdict(list), set()
def cid_of(r, s):
    t = r[s + '_type']
    if t == 'connector': return conns[r[s + '_id']]['id']
    if t in ('terminal', 'OEM'): return terms[tkey(r, s)]['id']
    if r[s + '_id'] in R10: return terms[r[s + '_id']]['id']
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
adj = collections.defaultdict(list)
for a, b, mm in L['segments']:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
# the harness may be a forest (Route 17, Dan 2026-11-02): the EB block strap is its own piece, and a part whose wires
# never leave its spot is a piece of one node; each piece must be a tree, drawn on its own
comp_of = {}
for s0 in sorted(tree_nodes, key=lambda n: (n != 'GB', n)):
    if s0 in comp_of: continue
    comp_of[s0] = s0; st = [s0]
    while st:
        n = st.pop()
        for m, _ in adj[n]:
            if m not in comp_of: comp_of[m] = s0; st.append(m)
roots = list(dict.fromkeys(comp_of[n] for n in sorted(tree_nodes, key=lambda n: (n != 'GB', n))))
for nd in list(node_items) + list(inline_at):
    if nd not in tree_nodes and nd not in roots: roots.append(nd); print('one-node piece', nd)
assert len(segs) == len(tree_nodes) - len([r for r in roots if r in tree_nodes]), 'a harness C piece is not a tree'
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
SPL = L.get('splice_allowance_mm', STUB)     # a splice end's allowance (Dan T7 b, 2026-11-10: 25 mm; strip and solder)
R10T = {'t_' + sid(k) for k in R10}     # an R10 Loose terminal stands in for a splice end, so it gets the splice allowance
def sub_nodes(n): return [n] + [m for k in kids[n] for m in sub_nodes(k)]
def heading(n, c):     # screen vector from n towards the middle of c's part of the car (front right, driver up)
    pts = [L['nodes'][m]['xy'] for m in sub_nodes(c)]
    x0, y0 = L['nodes'][n]['xy']
    return (sum(p[0] for p in pts) / len(pts) - x0, -(sum(p[1] for p in pts) / len(pts) - y0))
def rect(a, b): return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
def hit(r, s, g=GAP): return r[0] - g < s[2] and s[0] - g < r[2] and r[1] - g < s[3] and s[1] - g < r[3]
def mv(p, o): return (p[0] + o[0], p[1] + o[1])
def mvr(r, o): return (r[0] + o[0], r[1] + o[1], r[2] + o[0], r[3] + o[1])
def lay(n, din):
    """n's piece of the tree with n at (0, 0): (rects, node positions, stubs {part id: (node, part xy, stub points)})."""
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
        assert left, ('no free side for the parts at', n)
        cd = din if din in left else next(d for d in ('U', 'D', 'R', 'L') if d in left)
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
    rr, P, S = lay(root, None)
    if i == 0: o = (0, 0)
    else:       # a separate piece (the EB block strap, the A/C amp taps) sits below the main harness
        o = (min(r[0] for r in allrects) - min(r[0] for r in rr) + 600 * (i - 1), max(r[3] for r in allrects) - min(r[1] for r in rr) + 240)
        o = (o[0] // 30 * 30, o[1] // 30 * 30)
    allrects += [mvr(r, o) for r in rr]
    pos.update({m: mv(q, o) for m, q in P.items()})
    stubs.update({cid: (nd, mv(q, o), [mv(p, o) for p in pts]) for cid, (nd, q, pts) in S.items()})
xs = [r[0] for r in allrects] + [r[2] for r in allrects]
ent = [pos[n][0] for n in ('RFG',) if n in pos]
if ent: print('formboard width %d .. %d, RH fender grommet (harness entry) at %.0f%% of the width' % (min(xs), max(xs), 100 * (ent[0] - min(xs)) / (max(xs) - min(xs))))
assert all(v[0] % 30 == 0 and v[1] % 30 == 0 for v in pos.values())
bps = [{"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}} for n in parent]
bundles = []
for n, p in parent.items():
    if p is None: continue
    assert pos[n][0] == pos[p][0] or pos[n][1] == pos[p][1], (p, n)
    bundles.append({"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(seglen[n]), "unit": "mm"}})
INL_AT = {}
for cid, (nd, q, pts) in stubs.items():
    b = {"id": "bn_" + cid, "sourceId": "bp_" + sid(nd), "targetId": cid if cid[:2] in ('c_', 't_') else "bp_" + cid, "length": {"value": SPL if cid[:2] == "s_" or cid in R10T else STUB, "unit": "mm"}}
    if pts: b['layoutPoints'] = [{"id": "%s_p%d" % (b['id'], i), "layoutPosition": {"x": x, "y": y}} for i, (x, y) in enumerate(pts)]
    bundles.append(b)
    ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
    if cid[:2] == 's_':
        bps.append({"id": "bp_" + cid, "layoutPosition": {"x": q[0], "y": q[1]}}); ALLC[cid]['locationId'] = "bp_" + cid; INL_AT[cid] = "bp_" + sid(nd)
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
loc = {b['targetId']: (b['sourceId'], b['length']['value']) for b in bundles if b['targetId'][:2] in ('c_', 't_')}
loc.update({x['id']: (INL_AT[x['id']], SPL if x['id'][:2] == 's_' else STUB) for x in inl})
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
B.relabel(doc, lib=LIB)          # Dan's plain-label rules R1-R9 (2026-11-08), after placement so positions stay
print('empty connectors dropped (R5):', B.relabel.removed)
B.box_groups(doc)       # box seat ends as labelled terminals, no box groups, unused parts pruned (Dan R1 a)
NGHOST = B.add_ghosts(doc, H, NAME)      # other harnesses' wires in these bundles (Dan T4 a)
assert len(W) + NGHOST <= 100, 'ghost wires push EngineRoom-C over the 100-connection limit'
B.fill_ghost_note(doc, NAME)      # the title note says which pass-through wires are drawn as ghosts
print('ghost wires', NGHOST)
json.dump(doc, open(os.path.join(OUT, 'ld37.json'), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'ld37_lib_ops.json'), 'w'), indent=1)
print('connectors', len(doc.get('connectors', [])), 'terminals', len(doc.get('terminals', [])), 'splices', len(doc.get('splices', [])), 'wires', len(doc.get('wires', [])), 'cables 0', 'bundles', len(bundles),
      'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect), '| lib adds', [o['value']['partNumber'] for o in lib_add],
      '| no library part (left unset):', sorted(missing))
