"""harness.design copy of ST185-AB-cabin = the ECU harness, cabin half, in two documents (100-connection plan limit):
"ST185-AB-cabin 1 - sensor rails and screens Rev F" and "ST185-AB-cabin 2 - straight runs, power, taps and CAN Rev G".
Split rule (README "harness.design", one device, one file; Dan 2026-11-04 V1 a): the ECU plugs A, B, C and the bulkhead
DRB102-CABIN are drawn whole in both documents (each wires its own cavities; the others are N/C with a note); every other
device has all its AB-cabin wires in one document. Document 1 holds every wire joined (through devices, splices and
shielded cables) to the ECU sensor rails and screens: bus plugs BUS-5V, BUS-5V-2, BUS-GNDOUT-A / -B and splices SP-8V,
SP-SHIELD-A / -B, so the pedal, the wheel speed conditioner output plugs, the fuel level sender, the cam and fuel-level pull-ups and every core of
those shielded cables. Document 2 holds the rest: the plain ECU-to-bulkhead wires, ECU power and grounds, the relays and
new fuse boxes, the factory taps and CAN (ECU plug C joined AB-cabin, Dan 2026-11-04 V2 a). Viewer only; the master is
the source.
Usage: python gen_cabin.py <repo> <out_dir> <1|2>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library).
Writes <out>/abcab<doc>.json (whole document, wires not yet routed), abcab<doc>_lib_ops.json (part-library add ops) and
abcab<doc>_expect.json (routed length per wire id); then route it: python genroute.py <out>/abcab<doc>.json <out>/abcab<doc>_final.json.
Same rules and helpers' shape as gen_abeng.py (README "harness.design"): connectors and terminals 240 wide, each pin its own master
end text, display stripes on +12 V wires, parts from library 5LO8 (new ones from harness-parts.csv), shielded cables drawn as
cables, formboard layout, compact schematic (bulkhead and far ends left, cables beside them, splices middle, ECU side right).
Pin text (README "Pin text", Dan 2026-11-04): a splice (or bussed plug) whose other legs are in the other document or another
harness carries a label naming its signal and where those legs go ("to Dash, ECUMaster CSB3 (CSB3)"); no other splice gets a
signal label. A factory tap names the device, code, pin and the factory lead it is spliced onto; a new fuse / relay box end names
the box first ("New LOGIC fuse box, K-EPS-EN"; its fuse seats show the fuse). A part with no maker part number that is not
bought (ECU plug C, a generic round 6-pin plug, Dan 2026-11-04) is excludeFromBom. Lengths: the ST185-harness.layout.json tree
(the one car-mm model from the placement-editor seeds plus the glove-box breakout GB_T, the ECU splice point at the ECU plugs,
DECISIONS B8 "One mm model" / "A10 b by rule"), checked here against the master
est_length_mm. gen_abeng.py runs on import, so its helpers are not imported."""
import sys, os, json, re, collections, math, csv, copy
import formboard as FB
REPO, OUT, DOC = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert DOC in (1, 2), 'doc is 1 (sensor rails and screens) or 2 (straight runs, power, taps and CAN)'
sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
import build_drawings as B
import genroute
H = B.Harness('ST185-harness')
# each document keeps its own rev letter (a physical change = the next letter, Dan 2026-11-02). 2026-11-07 rebuild (Dan A4 a):
# doc 1 Rev C -> D (bus plug bridges br_*, Dan N57 a; flex fuel unshielded, N31 b), doc 2 Rev D -> E (cabin ground splice
# SP-CABIN-GND, N60 a; POWER box GND stud ring, N64 a; flex return, CAN trunk screen). 2026-11-09 rebuild: doc 1 Rev D -> E,
# doc 2 Rev E -> F (labels #569, grounds and shields #570, bussed caps R6, inline pairs dropped #580 / #590, box seats #594, CAN #597).
# 2026-11-12 rebuild (step 4): doc 1 Rev E -> F, doc 2 Rev F -> G (AB-cabin's editor-turn lengths of 2026-11-11 / 11-12: fuel sender
# leg, A/C amplifiers on their factory spots, kill switch lead after A1 b, the fuel pump relay coil feed; the wheel speed output
# plugs on the 2026-11-11 conditioner spots; the one mm cabin model #662; the ECU splice point at the ECU plugs A10 b #663; the
# outside air temp sensor wires now EngineRoom-C's, U4 a; 25 mm splice ends T7 b and ghost wires T4 a; library sync #664 / #665)
# Rev H of doc 2 (2026-11-12): its eight shared splices with one AB-cabin 2 leg (the A/C pressure switch and A/C sensor common
# splices, the six CAN tap splices) are Loose ends with their R10 notes, no one-wire splice (DECISIONS T3; one_leg_splices)
REVS, DATES = {1: 'F', 2: 'H'}, {1: '2026-11-12', 2: '2026-11-12'}
NAME, REV, DATE = 'AB-cabin', REVS[DOC], DATES[DOC]
TITLES = {1: 'ST185-AB-cabin 1 - sensor rails and screens', 2: 'ST185-AB-cabin 2 - straight runs, power, taps and CAN'}
SHORT = {1: 'AB-cabin 1', 2: 'AB-cabin 2'}
TITLE, OTHER = TITLES[DOC], TITLES[3 - DOC]     # the other file's name without its rev letter, so the notes never go stale (R10)
BHN = 'DRB102-CABIN'
SHARED = ('ECU-A', 'ECU-B', 'ECU-C', BHN)      # drawn whole in both documents (V1 a)
ALL = H.rows
ROWS = [r for r in ALL if r['harness'] == NAME]
W_ALL = [r for r in ROWS if r['wire_id']]
# the split: union every wire's devices (a shared plug is no link), splices and shielded cable; document 1 = the group(s)
# holding the sensor rails and screens, document 2 = the rest
SEEDS = ('BUS-5V', 'BUS-5V-2', 'BUS-GNDOUT-A', 'BUS-GNDOUT-B', 'SP-8V', 'BUS-SHIELD-A', 'SP-SHIELD-B')
def unit(r, s):
    i, t = r[s + '_id'], r[s + '_type']
    if not i or i in SHARED: return None
    return ('cable', i) if t == 'cable screen' else (t == 'OEM', i)
def units(r): return [u for u in (unit(r, 'from'), unit(r, 'to'), ('cable', r['cable']) if r['cable'] else None) if u]
_par = {}
def _find(x):
    _par.setdefault(x, x)
    while _par[x] != x: _par[x] = _par[_par[x]]; x = _par[x]
    return x
for r in W_ALL:
    us = units(r)
    for u in us: _find(u)
    for u in us[1:]: _par[_find(u)] = _find(us[0])
ONE = {_find((False, s)) for s in SEEDS if (False, s) in _par}
DOC_OF = {r['wire_id']: 1 if any(_find(u) in ONE for u in units(r)) else 2 for r in W_ALL}
assert DOC_OF == B.abcabin_doc_of(W_ALL), 'the AB-cabin split here and build_drawings.abcabin_doc_of (ghost-wire tags) disagree'
def doc_of(r): return DOC_OF[r['wire_id']]
DEV_DOCS = collections.defaultdict(set)
for r in W_ALL:
    for s in ('from', 'to'):
        if unit(r, s) and r[s + '_type'] != 'cable screen': DEV_DOCS[(r[s + '_type'], r[s + '_id'])].add(doc_of(r))
def is_splice(t, i): return t == 'splice' or i.startswith('BUS-')
assert all(is_splice(*k) for k, v in DEV_DOCS.items() if len(v) > 1), [k for k, v in DEV_DOCS.items() if len(v) > 1]
def spare_doc(c):      # a spare cavity is listed in the document that holds most of its plug's wires
    n = collections.Counter(doc_of(r) for r in W_ALL if c in (r['from_id'], r['to_id']))
    return max((1, 2), key=lambda d: (n[d], -d))
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
SPL = H.layout.get('splice_allowance_mm', STUB)     # a splice end's allowance (Dan T7 b, 2026-11-10: 25 mm; strip and solder)
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
    if not pn or pn.upper().startswith('TBD') or pn.startswith(('factory', 'in kit', 'pigtail', 'solder splice onto', 'none')): return None
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

# ------------------------------------------------------------------ names (README "Pin text", B22)
# a new fuse / relay box end names the box first, then the relay or fuse (Dan 2026-11-04); seats from sot/fuse-relay-map.csv
FRM = list(csv.DictReader(open(os.path.join(REPO, 'sot/fuse-relay-map.csv'), encoding='utf-8')))
BANK = {'B1': 'New POWER fuse box', 'B2': 'New LOGIC fuse box', 'B3': 'New trunk relay block', 'B4': 'New EPS relay (B4)'}
BOX_OF = {f['master_id']: BANK[f['bank']] for f in FRM if f['kind'] == 'relay' and f['master_id'].startswith('K-')}
BOX_WHOLE = {'POWER': BANK['B1'], 'LOGIC': BANK['B2'], 'BATT-RELAY-BLOCK': BANK['B3']}
FUSE = {(BANK[f['bank']], f['position']): f['circuit'] for f in FRM if f['kind'] == 'fuse' and f['circuit'] != '(vacant)'}
def fuse_text(box, pin):
    c = FUSE.get((box, pin))
    return (c + ' fuse' if re.search(r'\d A$', c) else c) if c else pin
def box_label(i, pin=None):
    if i in BOX_OF: return '%s, %s' % (BOX_OF[i], i)
    if i in BOX_WHOLE: return BOX_WHOLE[i] if pin is None else '%s, %s' % (BOX_WHOLE[i], fuse_text(BOX_WHOLE[i], pin))
    return None
# factory taps (Dan 2026-11-04): the device (the master's name), its code, the pin, and the factory lead it is spliced onto
OEMNAME = {'A15': 'A/C amplifier', 'A32': 'Auto A/C amplifier', 'A1': 'Ambient air temp sensor', 'JB1': 'J/B No.1',
           'IG2': 'Cowl-side factory plug', 'RB4': 'R/B No.4 starter relay', 'C16': 'Cruise control switch, combination switch plug B', 'A5': 'A/C pressure switch'}
OEMCODE = {}
# far ends of legs drawn elsewhere, named for a splice label (the master's device names, plain)
PLAIN = {'R-CRUISE': 'cruise ladder resistor', 'F-PI': 'RealDash Pi 5 A inline fuse', 'CSB3': 'ECUMaster CSB3',
         'T-CLUSTER-CAN': 'centre cluster CAN board', 'T-REALDASH-CAN': 'RealDash Pi USB-CAN adapter', 'OPTO-8': 'opto board'}
def oem_lead(r, s):
    """the factory lead an OEM end is spliced onto: its colour and job from the master (oem_method / oem_location)"""
    i, p = r[s + '_id'], r[s + '_pin']
    o = 'to' if s == 'from' else 'from'
    mine = r[o + '_type'] != 'OEM' or ('%s pin %s' % (i, p)) in r['oem_location']
    colour = r['oem_wire_colour'] if mine else ''
    m = re.search(r'onto the factory (\S.*?) lead', r['oem_method']) if mine else None
    if m and colour and m.group(1).startswith(colour): return 'the factory %s lead' % m.group(1)
    if colour:
        m = re.search(r'(?:^|[ ,(])%s(?: -|,) ([^(;]+)' % re.escape(colour), r['oem_location'])
        return 'the factory %s lead%s' % (colour, ' (%s)' % m.group(1).strip() if m else '')
    return 'the factory lead'
def oem_label(r, s):
    i, p = r[s + '_id'], r[s + '_pin']
    dev = '%s (%s) pin %s' % (OEMNAME.get(i, i), OEMCODE.get(i, i), p)
    how = (r[s + '_terminal_pn'] + ' ' + r['oem_method']).lower()
    return '%s, spliced onto %s' % (dev, oem_lead(r, s)) if ('splice' in how or 'solder onto' in how) else dev + ' (at its own plug)'
def plain(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if box_label(i, p if i in BOX_WHOLE else None): return box_label(i, p if i in BOX_WHOLE else None)
    if t == 'terminal' and B.BOX_RING.match(i): return 'New ' + r[s + '_name']
    if t == 'OEM': return '%s (%s)' % (OEMNAME.get(i, i), OEMCODE.get(i, i))
    if t == 'splice': return '%s (%s)' % (r[s + '_name'].split(' - ')[0], i)
    if t == 'cable screen':
        dev = next((plain(x, xs) for x in ALL if x['cable'] == i and x['colour'] != 'Shield' for xs in ('from', 'to')
                    if x[xs + '_type'] not in ('splice', 'cable screen')), i)
        return 'the screen of the cable to the %s' % dev
    return '%s (%s)' % (PLAIN[i], i) if i in PLAIN else (r[s + '_name'] or i)

# ------------------------------------------------------------------ connectors (drawn whole; other-document / harness cavities N/C)
def pkey(p):
    m = re.match(r'(\d+)$', p)
    return (0, int(m.group(1)), '') if m else (1, 0, p)
RELAY_ORDER = ['30', '85', '86', '87', '87a']
def pin_order(p, c='K-'): return (RELAY_ORDER.index(p) if c.startswith('K-') and p in RELAY_ORDER else 99, pkey(p))   # relays 30 85 86 87 87a
conn_ids = list(dict.fromkeys([c for c in SHARED] + [r[s + '_id'] for r in W for s in ('from', 'to') if r[s + '_type'] == 'connector']))
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
        mine_w = sorted([u for u in here if u[1] and doc_of(u[2]) == DOC], key=lambda u: B.is_integral(u[2]))   # the real wire's contact
        theirs_w = [u for u in here if u[1] and doc_of(u[2]) != DOC]
        if mine_w:
            r, s = mine_w[0][2], mine_w[0][3]
            ct = part_id('contactParts', r[s + '_terminal_pn'])
            if ct and ct != cfg_contact: cv['contactPartId'] = ct
        else:
            cv['notConnected'] = True
            if theirs_w:
                other_owned[c].append((p, SHORT[3 - DOC])); cv['cavityPlugPartId'] = None
            elif here and spare_doc(c) != DOC:
                other_owned[c].append((p, SHORT[3 - DOC] + ' (an AB-cabin spare, listed there)')); cv['cavityPlugPartId'] = None
            elif here:      # an AB-cabin spare: its sealing plug from the master (TBD -> none)
                pl = part_id('cavityPlugParts', here[0][2][here[0][3] + '_terminal_pn'])
                if pl and pl != cfg_plug: cv['cavityPlugPartId'] = pl
            else:
                owners = sorted({B.file_short(u[2]) for u in use[c].get(p, [])})     # the file, "AB-cabin 2" (DECISIONS B6)
                if owners: other_owned[c].append((p, '/'.join(owners))); cv['cavityPlugPartId'] = None
        cavs.append(cv)
    conns[c] = {"id": "c_" + sid(c), "label": box_label(c) or c, "cavities": cavs, "width": 240}
    if cpid: conns[c]['partId'] = cpid
cav_of = {(c, cv['designation']): cv['id'] for c, n in conns.items() for cv in n['cavities']}

# ------------------------------------------------------------------ other ends, wires, cables
terms, splices, resistors, diodes = (collections.OrderedDict() for _ in range(4))
SPLP = {'solder splice': 'GENERIC SOLDER SPLICE', 'crimp splice': 'GENERIC CRIMP SPLICE 14-10'}
spl_pn = collections.defaultdict(set)
OEM_T = {}        # terminal id of a factory lead -> its plug (A15-8, A15-9 ... stack touching on the schematic)
def tkey(r, s): return r[s + '_id'] + ('-' + r[s + '_pin'] if r[s + '_type'] == 'OEM' else '')
def tlabel(r, s):
    i = r[s + '_id']
    if r[s + '_type'] == 'terminal': return 'New ' + r[s + '_name'] if B.BOX_RING.match(i) else (box_label(i) or i)   # a box stud ring (Dan N64 a)
    return oem_label(r, s)
# a shared splice with only one leg in this file (its other legs are in another file) is no splice here: a Loose end with its
# R10 note and the 25 mm splice allowance (DECISIONS T3 / R10 / T7 b; build_drawings.one_leg_splices)
ONE = B.one_leg_splices(W, 'ST185-' + SHORT[DOC])
def end(r, s):
    t, i, p = r[s + '_type'], r[s + '_id'], r[s + '_pin']
    if t == 'connector': return {"id": "c_" + sid(i), "handle": cav_of[(i, p)]}
    if t == 'splice' and i in ONE:
        terms.setdefault(i, {"id": "t_" + sid(i), "label": r[s + '_name'] or i, "type": 'Loose', "width": 240})
        return {"id": "t_" + sid(i), "handle": "Terminal"}
    if t == 'splice':
        tp = r[s + '_terminal_pn']; spl_pn[i].add(SPLP.get(tp, tp))
        splices.setdefault(i, {"id": "s_" + sid(i), "label": i})
        return {"id": "s_" + sid(i), "handle": "Splice"}
    if t in ('terminal', 'OEM'):
        k, nm = tkey(r, s), r[s + '_name'].lower()
        ty = 'Ring' if ('ring' in nm or 'stud' in nm or 'bolt' in nm or ' bar' in nm) else 'Loose'
        terms.setdefault(k, {"id": "t_" + sid(k), "label": tlabel(r, s), "type": ty, "width": 240})
        if t == 'OEM': OEM_T["t_" + sid(k)] = i
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
LINK_IDS = set()     # INTEGRAL links (none in AB-cabin since Dan R6, 2026-11-08: a bussed plug is mated to its receptacle)
for r in W:
    a, b = end(r, 'from'), end(r, 'to')
    row_of[r['wire_id']] = r
    if B.is_integral(r):
        wires.append({"id": "w_" + sid(r['wire_id']), "source": a, "target": b, "color": "Gray", "identLabel": r['wire_id']})
        LINK_IDS.add(r['wire_id']); continue
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
    if B.is_integral(r): continue      # a cap bridge has no pin text of its own
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
# a POWER / LOGIC box ring terminal carries its bar's global signal, so every stud on one bar reads as one net (Dan N64 a)
for r in W:
    for s in ('from', 'to'):
        if B.ring_signal(r, s): comp['t_' + sid(tkey(r, s))]['signal'] = B.ring_signal(r, s)
for c, n in conns.items():      # a new fuse box seat shows its fuse (sot/fuse-relay-map.csv), after the box name on the plug
    if c in BOX_WHOLE:
        for cv in n['cavities']:
            if cv.get('signal'): cv['signal'] = fuse_text(BOX_WHOLE[c], cv['designation'])
    if c in conns and all(r[s + '_housing_pn'].startswith('none') for r in ALL for s in ('from', 'to') if r[s + '_id'] == c):
        n['excludeFromBom'] = True      # no maker part, not bought (ECU plug C, Dan 2026-11-04)
# a splice (or bussed plug) whose other legs are in the other document or another harness: its label names its signal and
# where those legs go (README "Pin text", Dan 2026-11-04); every other splice keeps its bare name
def drawn_here(r): return r['harness'] == NAME and r['wire_id'] and doc_of(r) == DOC
def ext_label(sp, own):
    away = collections.defaultdict(list)
    for r in ALL:
        if not r['wire_id'] or drawn_here(r) or B.is_removal(r): continue
        for s in ('from', 'to'):
            o = 'to' if s == 'from' else 'from'
            if r[s + '_id'] == sp and (r[s + '_type'] == 'splice' or sp.startswith('BUS-')):
                where = SHORT[3 - DOC] if r['harness'] == NAME else r['harness']
                nm = plain(r, o)
                if nm not in away[where]: away[where].append(nm)
    if not away: return None
    sig = own[0][0] if own else ''
    return '%s - %s; to %s' % (sp, sig, '; to '.join('%s, %s' % (k, ' / '.join(v)) for k, v in sorted(away.items())))
for sp, n in list(splices.items()) + [(c, n) for c, n in conns.items() if c.startswith('BUS-')]:
    own = []      # (the master end text at this splice, whether that wire runs to an ECU pin) for the wires drawn here
    for r in W:
        for s in ('from', 'to'):
            o = 'to' if s == 'from' else 'from'
            if r[s + '_id'] == sp and r[s + '_desc'] and not B.is_integral(r):     # the signal: the wire to an ECU pin, else to a splice, else the first
                own.append((r[s + '_desc'], 0 if r[o + '_id'].startswith('ECU-') else 1 if is_splice(r[o + '_type'], r[o + '_id']) else 2))
    own.sort(key=lambda x: x[1])
    lb = ext_label(sp, own)
    if lb: n['label'] = lb

# ================================================================== schematic: far ends left, cables, splices, ECU side right
# README "harness.design" (Dan 2026-11-01 / 11-02 / 11-03 N1 a): bulkhead (doc 1) or the far ends (doc 2) left, the cabin halves
# of the shielded runs as cables beside them, splices middle, the ECU plugs and ECU splice-point bus plugs right (doc 1: with
# every other non-bulkhead end); each wire horizontal with one 90 degree jog in its own lane; columns level at the top, the right
# column half a grid lower.
CID = {n['id']: c for c, n in conns.items()}
def place_of(cid):
    if cid in CID: return H.layout['place'].get(CID[cid])
    for r in W:
        for s in ('from', 'to'):
            if r[s + '_type'] in ('connector', 'terminal', 'OEM') and \
                    ("c_" + sid(r[s + '_id']) if r[s + '_type'] == 'connector' else "t_" + sid(tkey(r, s))) == cid:
                return H.place(r, s)
NODES = {n['id']: n for n in list(conns.values()) + list(terms.values())}
def is_ecu_side(n): return n['id'].startswith('c_') and place_of(n['id']) in ('ECU', 'SP')     # ECU plugs + the ECU splice-point bus plugs
# the bulkhead first, then the far ends grouped by where they sit in the car (glove box, the sill run, A/C, front, dash, pedal)
AREA = ['BH', 'GB', 'RHKICK', 'BATT', 'FUEL', 'ACAMP', 'EVAP', 'AMB', 'ECU', 'CSB3', 'VRC_F', 'VRC_R', 'JB1', 'PEDAL']
# a one-leg splice's Loose end sits across from its wire's far end, so the wire runs straight over like any other: far end on
# the left (a factory tap, the bulkhead) -> the end in the right column, far end an ECU plug -> the end in the left column
def far_ecu(sp):
    r, s = next((r, s) for r in W for s in ('from', 'to') if r[s + '_type'] == 'splice' and r[s + '_id'] == sp)
    o = 'to' if s == 'from' else 'from'
    return r[o + '_type'] == 'connector' and H.layout['place'].get(r[o + '_id']) in ('ECU', 'SP')
LOOSE_R = {'t_' + sid(i) for i in ONE if not far_ecu(i)}
LOOSE_L = {'t_' + sid(i) for i in ONE} - LOOSE_R
LEFT_IDS = sorted([i for i, n in NODES.items() if not is_ecu_side(n) and i not in LOOSE_R],
                  key=lambda i: (AREA.index(place_of(i)) if place_of(i) in AREA else 99, i.startswith('t_'), NODES[i]['label']))
DEV_IDS = {i for i in NODES if i not in LEFT_IDS}
def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
def cab_h(c): return 30 + 30 * len(cseq(c))
def tap_plug(i): return OEM_T.get(i, i)     # factory leads of one plug (A15-8, A15-9, ...) stack touching, like cavities
# OEM splice notes (texts here, placed below), known before placing so each tap gets room for its label and note (Dan N99 a)
oem_col, oem_txt, oem_skip = collections.OrderedDict(), {}, []
for r in W:
    for s, c in B.oem_splices(r):
        tid = 't_' + sid(tkey(r, s))
        if not c: oem_skip.append('%s %s %s' % (r['wire_id'], r[s + '_id'], r[s + '_pin'])); continue
        assert oem_col.setdefault(tid, c) == c, (tid, oem_col[tid], c)
        oem_txt.setdefault(tid, B.oem_splice_note(r, s, c))     # full note (Dan N16 a); a shared tap keeps its first text
for i, txt in ONE.items():      # a left one-leg splice end's R10 note sits where the OEM splice notes do (as gen_engc.py); a
    if 't_' + sid(i) not in LOOSE_R:     # right one's goes in the R10 note column (below)
        oem_col['t_' + sid(i)], oem_txt['t_' + sid(i)] = 'R10', txt
def span(i): return B.end_span(NODES[i], [oem_txt[i]] if i in oem_txt else [])
y, prev = 0, None
for i in LEFT_IDS:     # where an end has text (a label tag, a note on its row) the step grows to keep it clear (Dan N99 a)
    n = NODES[i]
    if prev is not None:
        y += max(h(NODES[prev]) + (0 if tap_plug(i) == tap_plug(prev) and 'cavities' not in n else
                                   (30 if place_of(i) == place_of(prev) else 60)), B.text_step(span(prev), span(i)))
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
# a cable with an end on the left column (the bulkhead or a far plug) sits beside the left column on the nearest run of empty
# rows, so no left pin's wire runs into it, and its splices sit on its core rows; the hops from the left pins to the cables each
# take a lane of their own between the two columns. A cable with no left end (the ECU CAN cable: ECU plug C to the CAN joins)
# sits right of the splices, on rows next to what feeds its splices from the left
CABLX = 240 + 30 * (3 + sum(1 for c in cables.values() for co in cseq(c) for e in ends(co) if e['id'] in LEFT_IDS))
def lefts_of(c, loose=False):     # a left one-leg splice end does not pull its cable over to the left column (it stood in
    return [cav_y(NODES[e['id']], e['handle']) for co in cseq(c) for e in ends(co)     # for a middle splice: the ECU CAN cable)
            if e['id'] in LEFT_IDS and (loose or e['id'] not in LOOSE_L)]
MID_CABS = [c for c in cables.values() if not lefts_of(c)]
def put_cable(c, want, x):
    global cab_rows
    k = cab_h(c) // 30
    tops = [m for m in range(0, LEFT_BOTTOM + 30 * 60, 30) if not any(m + 30 * j + 15 in used_rows | cab_rows for j in range(k))]
    top = min(tops, key=lambda m: (abs(m + 45 - want), m))
    c['schematicPosition'] = {"x": x, "y": top}
    cab_rows |= {top + 30 * j + 15 for j in range(k)}
for c in sorted([c for c in cables.values() if c not in MID_CABS], key=lambda c: min(lefts_of(c))):
    put_cable(c, min(lefts_of(c)), CABLX)
for c in MID_CABS:
    mine = {co['id'] for co in cseq(c)}
    inl = {e['id'] for co in cseq(c) for e in ends(co) if e['id'][:2] in ('s_', 'r_', 'd_')}
    feeds = []
    for cond in CONDS:
        es = ends(cond)
        if cond['id'] in mine or not any(e['id'] in inl for e in es): continue
        cc = cab_of.get(cond['id'])
        if cc is not None and 'schematicPosition' in cc: feeds.append(core_row(cc, cond))
        feeds += [cav_y(NODES[e['id']], e['handle']) for e in es if e['id'] in LEFT_IDS]
    loose = lefts_of(c, True)      # or beside its one-leg splice ends
    put_cable(c, min(feeds) if feeds else min(loose) if loose else LEFT_BOTTOM, 0)     # x is set once the splices are placed
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
for c in MID_CABS: c['schematicPosition']['x'] = (max([n['schematicPosition']['x'] for n in INL.values()] + [CABLX]) + 180) // 30 * 30
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
DEV_ORDER = sorted(DEV_IDS, key=lambda d: (d in LOOSE_R,      # one-leg splice ends below the ECU plugs
                                           sum(bary[d]) / len(bary[d]) if bary[d] else 10 ** 6, NODES[d]['label']))
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
XMAX = max([n['schematicPosition']['x'] for n in INL.values()] + [c['schematicPosition']['x'] for c in MID_CABS] + [CABLX])
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
def upload_ok(devx):     # the upload pass (genroute.py: its last-resort jogs, the OEM / R10 notes on their rows, the bussed
    place_right(devx)    # receptacles relabel adds) routes every conductor of this file
    d_ = copy.deepcopy(doc_now())
    d_['schematicNotes'] = [{"id": "n_oem_" + t, "width": 360, "text": "", "schematicPosition": {
        "x": NODES[t]['schematicPosition']['x'] - 360, "y": NODES[t]['schematicPosition']['y']}} for t in oem_col]
    B.relabel(d_, lib=LIB)
    R_, segs_, res_ = genroute.run(d_, loose=True)
    return not [s for s in segs_ if res_.get(s['k']) is None]
while ONE and not upload_ok(hi):     # widen a grid step at a time until it does (AB-cabin 2 Rev H, one-leg splice ends: 1560 -> 1650)
    hi += 30; print('  widen to', hi, flush=True); assert hi < 3000, 'no right column x routes the upload pass'
DEVX = hi
RIGHT_BOTTOM = place_right(DEVX)
print('right column x', DEVX, 'bottom', RIGHT_BOTTOM, '| left bottom', LEFT_BOTTOM, flush=True)

# ------------------------------------------------------------------ notes
spares = collections.defaultdict(list)
for r in SPARE_ALL:
    if r['from_id'] in conns and spare_doc(r['from_id']) == DOC: spares[r['from_id']].append((r['from_pin'], r['from_terminal_pn']))
left_txt, right_txt = [], []
BOX_SEATS = set(B._seat_map()) | {'LOGIC'}     # box guts are not drawn (Dan R1 a): no spare / N/C notes for box seats
for c in conns:
    if c in BOX_SEATS: continue
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
for c, n in conns.items():      # a plug with no maker part that is not bought: what it is and its pinout source, from the master
    if n.get('excludeFromBom'):
        r = next(r for r in ALL if r['from_id'] == c)
        right_txt.append('%s: %s; pinout from the %s; %s; left out of the BOM.' % (c, r['from_name'], r['from_pin_doc'], r['from_note']))
if NC_CORES:
    right_txt.append('Cable cores with no AB-cabin job (cut back and sealed under heat-shrink at both ends): %s.' % '; '.join(
        '%s %s' % (cab_of[co['id']]['label'], co['color'].lower()) for co in NC_CORES))
used_st = sorted({row_of[w['identLabel']]['circuit_id'] for w in wires if 'stripeColor' in w}, key=list(STRIPE).index)
head = [{"id": "n_title", "width": 360,
         "text": "%s Rev %s (%s). %s of the two AB-cabin files, the ECU harness cabin half: %s. The rest of AB-cabin is %s ('%s'). Split (Dan "
                 "2026-11-04, V1 a): the ECU plugs A, B, C and the bulkhead DRB102-CABIN are drawn whole in AB-cabin 1 and AB-cabin 2 "
                 "(cavities wired in the other file are N/C with a note); every other device has all its AB-cabin wires in one file. A "
                 "splice whose other legs are in another file is labelled with where they go and carries the R10 note (the other file, "
                 "where the splice sits, the EWD page, the other legs' far ends and colour); a wire spliced onto a factory wire carries the "
                 "full OEM splice note at its tap (Dan Y6, N16 a). Viewer copy "
                 "generated from docs/harness/MASTER-wirelist.csv (harness = AB-cabin) by docs/harness/tools/gen_cabin.py; never a source. "
                 "Schematic: %s left, the cabin halves of the shielded runs as cables beside them, splices middle, %s right; columns level "
                 "at the top (right column half a grid lower, N1 a). Each pin shows its own master end text.%s %s"
                 "Layout: a formboard of the ST185-harness.layout.json tree (the one car-mm model from the placement-editor seeds, glove-box "
                 "breakout GB_T, the ECU splice point at the ECU plugs, A10 b), front of car RIGHT, rear LEFT, "
                 "driver side UP; drawn 1:1 on A3 panels, every bundle at exactly its length, long runs folded as serpentines (Dan A25 a); each part on a 100 mm end-allowance stub (a splice on a 25 mm stub, Dan "
                 "T7 b); bundle lengths = the master est_length_mm." % (
                     TITLE, REV, DATE, SHORT[DOC], 'every wire on the ECU sensor rails and screens (+5 V, +8 V, Gnd Out bus plugs, shield '
                     'splices) with the pedal, the wheel speed conditioner output plugs, the fuel level sender, the cam and fuel-level pull-ups '
                     'and their shielded cables' if DOC == 1 else
                     'the plain ECU-to-bulkhead wires (injectors, coils, sensor signals with no cabin splice), ECU power and grounds, the '
                     'relays and new fuse boxes, the factory taps (A/C amplifiers, J/B No.1, IG2, R/B No.4), the fuel pump relay and kill switch '
                     'legs of the sill run '
                     'and CAN (ECU plug C)', SHORT[3 - DOC], OTHER,
                     'the bulkhead and the far ends', 'the ECU plugs and ECU splice-point bus plugs',
                     B.LOOSE_SENTENCE.rstrip() if ONE else '', B.GHOST_MARK)}]
if used_st:      # display stripes note, only when the part has a +12 V wire
    head.append({"id": "n_stripes", "width": 360,
         "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                 "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) +
                 ". Red cable cores keep their cable's colours."})
def est_h(t): return 30 * (2 + len(t) // 50)       # a 360-wide note: about 50 characters a line, one grid row a line
HEAD_Y = -30 * ((max(est_h(n['text']) for n in head) + 59) // 30)
for i, n in enumerate(head): n['schematicPosition'] = {"x": 390 * i, "y": HEAD_Y}
NOTES = list(head)
# OEM splice notes (README "Pin text", Dan 2026-11-04 Y6): every wire spliced onto a factory wire gets a note on that wire,
# "Splice to OEM wire <colour> - <OEM code> pin <n>, <circuit>, <place>" (build_drawings.oem_splice_note, Dan N16 a), on the wire's row
# just left of its factory tap (text right-aligned); genroute.py keeps the other wires out of it, so the left-to-left wires run
# down the outside left of the notes. A blank colour gets no note and is listed (texts: oem_txt, above).
OEMW = 360                       # the full N16 a note at harness.design's widest note (60-360): about 50 characters a line, three lines
for tid, c in oem_col.items():
    p = NODES[tid]['schematicPosition']; assert tid in LEFT_IDS, tid
    NOTES.append({"id": "n_oem_" + tid, "text": oem_txt[tid], "width": OEMW, "alignment": "Right",
                  "schematicPosition": {"x": p['x'] - OEMW, "y": p['y']}})
print('OEM splice notes', len(oem_col), '| blank colour, no note:', ', '.join(oem_skip) or 'none', flush=True)
N_LL = sum(1 for cond in CONDS if len([e for e in ends(cond) if e['id'] in LEFT_IDS]) == 2)   # left-to-left wires run down the outside
LL_X = -420 - (OEMW if oem_col else 0) - 30 * N_LL
if left_txt: NOTES.append({"id": "n_left", "width": 360, "text": ' '.join(left_txt), "schematicPosition": {"x": LL_X, "y": 0}})
if right_txt: NOTES.append({"id": "n_right", "width": 360, "text": ' '.join(right_txt), "schematicPosition": {"x": DEVX + 270, "y": 15}})
# R10 (DECISIONS B6): a splice whose other legs are in another file carries the R10 note, in its own column right of the notes,
# on the splice's row or the next free row below the note above it
r10_y = None
for sp, n in sorted(list(splices.items()) + [(i, terms[i]) for i in ONE if 't_' + sid(i) in LOOSE_R],
                    key=lambda kv: kv[1]['schematicPosition']['y']):
    t = ONE.get(sp) or B.r10_note(sp, 'ST185-' + SHORT[DOC])     # a right one-leg splice end: its R10 note, on its row
    if not t: continue
    y = n['schematicPosition']['y'] if r10_y is None else max(n['schematicPosition']['y'], r10_y)
    NOTES.append({"id": "n_r10_" + sid(sp), "width": 360, "text": t, "schematicPosition": {"x": DEVX + 270 + 390, "y": y}})
    r10_y = y + est_h(t) + 30

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
for c in SHARED:      # a shared plug with no wire in this part still sits at its spot on the formboard
    if conns[c]['id'] not in seen:
        nd = H.layout['place'][c]; seen.add(conns[c]['id']); node_items[nd].append(conns[c]['id'])
segs, hroute = collections.Counter(), {}
for r in W:
    p, mm = troute(r); hroute[r['wire_id']] = mm
    for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
# a node whose items are joined only to each other (a factory tap and its splice on the same node, e.g. the auto A/C amplifier
# A32 at ACAMP32 in part 2) has no wire run of its own: hang it on the tree by its layout path to the nearest node a wire uses
# (no wire counted on that path), so the formboard still reaches it (2026-11-12, library sync step: part 2 stopped on it)
used = {n for k in segs for n in k}
for n in sorted(set(node_items) | set(inline_at)):
    if n in used or not used: continue
    prev, todo = {n: None}, [n]
    while todo and not (set(todo) & used):
        nxt = []
        for x in todo:
            for m, _ in H.adj[x]:
                if m not in prev: prev[m] = x; nxt.append(m)
        todo = nxt
    hit = sorted(set(todo) & used)
    assert hit, ('no layout path to the tree', n)
    x = hit[0]
    while prev[x] is not None:
        k = tuple(sorted((x, prev[x]))); segs[k] = segs.get(k, 0); used |= set(k); x = prev[x]
tree_nodes = {n for k in segs for n in k} | set(node_items) | set(inline_at)
adj = collections.defaultdict(list)
for a, b, mm in H.layout['segments']:
    if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
ROOT = 'BH'
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
# car lies); every bundle keeps its tree length (= the master's); formboard.to_scale then redraws it 1:1 (Dan A25 a). Each part sits on its 100 mm
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
    b = {"id": "bn_" + cid, "sourceId": "bp_" + sid(nd), "targetId": cid if direct else "bp_" + cid, "length": {"value": SPL if cid[:2] == "s_" or cid[2:] in {sid(i) for i in ONE} else STUB, "unit": "mm"}}
    if pts: b['layoutPoints'] = [{"id": "%s_p%d" % (b['id'], i), "layoutPosition": {"x": x, "y": y}} for i, (x, y) in enumerate(pts)]
    bundles.append(b)
    ALLC[cid]['layoutPosition'] = {"x": q[0], "y": q[1]}
    if not direct:
        bps.append({"id": "bp_" + cid, "layoutPosition": {"x": q[0], "y": q[1]}}); ALLC[cid]['locationId'] = "bp_" + cid; INL_AT[cid] = "bp_" + sid(nd)
nodepar = {"bp_" + sid(n): ("bp_" + sid(p) if p else None) for n, p in parent.items()}
blen = {(b['sourceId'], b['targetId']): b['length']['value'] for b in bundles}
loc = {b['targetId']: (b['sourceId'], b['length']['value']) for b in bundles if b['targetId'][:2] in ('c_', 't_')}
loc.update({i: (INL_AT[i], SPL if i[:2] == 's_' else STUB) for i in INL})
def chain(bp):
    out = []
    while bp: out.append(bp); bp = nodepar[bp]
    return out
def dist(b1, b2):
    c1, c2 = chain(b1), chain(b2); common = next(x for x in c1 if x in c2)
    return sum(blen[(nodepar[x], x)] for c in (c1, c2) for x in c[:c.index(common)])

# ================================================================== checks and emit
expect = {lab(w): loc[w['source']['id']][1] + loc[w['target']['id']][1] + dist(loc[w['source']['id']][0], loc[w['target']['id']][0])
          for w in CONDS if 'target' in w and lab(w) not in LINK_IDS}
bad = {k: (v, hroute[k], row_of[k]['est_length_mm']) for k, v in expect.items() if not (v == hroute[k] == int(float(row_of[k]['est_length_mm'] or -1)))}
bad.update({lab(w): (None, hroute[lab(w)], row_of[lab(w)]['est_length_mm']) for w in CONDS if 'target' not in w
            and hroute[lab(w)] != int(float(row_of[lab(w)]['est_length_mm'] or -1))})
assert not bad, 'routed length != tree route != master est_length_mm: %r' % bad
assert sorted(lab(w) for w in CONDS) == sorted(r['wire_id'] for r in W) and len({lab(w) for w in CONDS}) == len(W)
cav_n = collections.Counter((e['id'], e['handle']) for w in CONDS if lab(w) not in LINK_IDS for e in ends(w) if e['id'].startswith('c_'))
cav_m = collections.Counter(("c_" + sid(r[s + '_id']), cav_of[(r[s + '_id'], r[s + '_pin'])]) for r in W if not B.is_integral(r)
                            for s in ('from', 'to') if r[s + '_type'] == 'connector')
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
B.relabel(doc, lib=LIB)          # Dan's plain-label rules R1-R9 (2026-11-08), after placement so positions stay
print('empty connectors dropped (R5):', B.relabel.removed)
B.box_groups(doc, B.BOX_GROUP_OUTSIDE.get('AB-cabin %d' % DOC, ()))     # box seat ends as labelled terminals, no box groups, unused parts pruned (Dan R1 a)
NGHOST = B.add_ghosts(doc, H, NAME)      # other harnesses' wires in these bundles (Dan T4 a)
assert NCONN + NGHOST <= 100, 'ghost wires push AB-cabin %d over the 100-connection limit' % DOC
B.fill_ghost_note(doc, NAME)      # the title note says which pass-through wires are drawn as ghosts; the heading notes placed again
head_now = [n for n in doc['schematicNotes'] if n['id'] in {h['id'] for h in head}]
HEAD_Y = -30 * ((max(est_h(n['text']) for n in head_now) + 59) // 30)
for n in head_now: n['schematicPosition']['y'] = HEAD_Y
FB.to_scale(doc)        # the 1:1 formboard (Dan A25 a): every bundle drawn at its set length, long runs folded
_fbad = FB.check(doc)
assert not _fbad, 'formboard: %r' % _fbad[:8]
print('formboard %dx%d mm, %d A3 panels' % FB.board(doc)[:3])
json.dump(doc, open(os.path.join(OUT, 'abcab%d.json' % DOC), 'w'), indent=1)
json.dump(lib_add, open(os.path.join(OUT, 'abcab%d_lib_ops.json' % DOC), 'w'), indent=1)
json.dump(expect, open(os.path.join(OUT, 'abcab%d_expect.json' % DOC), 'w'), indent=1)
print('doc', DOC, TITLE, 'Rev', REV, '| connectors', len(conns), 'terminals', len(terms), 'splices', len(splices), 'resistors', len(resistors),
      'diodes', len(diodes), 'wires', len(wires), 'cables', len(cables), 'conductors (connections)', NCONN, '+ ghosts', NGHOST, '(%d cores with no job)' % len(NC_CORES),
      'bundles', len(bundles), 'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect), 'routed +', len(CONDS) - len(expect),
      'one-ended screens | lib adds', [o['value']['partNumber'] for o in lib_add], '| no library part (left unset):', sorted(missing))
