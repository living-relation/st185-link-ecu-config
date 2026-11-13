"""harness.design copy of ST185-Dash, file "ST185-Dash Rev E" (Rev E 2026-11-12: the reverse signal and high-beam output splices, each with one Dash leg, are Loose ends with their R10 notes, no one-wire splice (DECISIONS T3; build_drawings.one_leg_splices; the builder draws any such end this way); Rev D 2026-11-12: Dash's editor-turn lengths (2026-11-12), the one mm cabin model (#662), the ECU splice point at the ECU plugs (A10 b, #663), the high-beam LED fed straight from the high-beam output and spliced onto its pigtail (A2 b / A3), 25 mm splice ends (T7 b) and ghost wires (T4 a), library sync (#664 / #665); Rev C 2026-11-09: CAN trunk taps and 2-core drops, Dan P1 / T1 a; box seats as plain terminals, Dan R1 a; viewer only; the master is the source), and the shared builder
gen_antitheft.py uses for "ST185-AntiTheft" (one small cabin harness each, same rules).
Usage: python gen_dash.py <repo> <out_dir>   (needs <out>/lib.json = a dump of part library 5LO8, get_part_library, filtered
to the parts these harnesses use). Writes <out>/dash.json (whole document, wires already routed with genroute.py: upload as
is), dash_lib_ops.json (part-library add ops, not applied by the generator) and dash_expect.json (routed length per wire id).
Same rules and helpers' shape as gen_cabin.py (README "harness.design"): connectors and terminals 240 wide, each pin its own
master end text, display stripes on +12 V wires, parts from library 5LO8 (new ones from harness-parts.csv), shielded cables
drawn as cables (cores in the cable part's order, the screen to its trunk splice, floating at the device), formboard layout
of the ST185-harness.layout.json tree (DECISIONS B8, N120: route drawn by Claude, devices refined by Dan), compact schematic: sources left (factory
taps with their full OEM splice notes, the LOGIC box seats, the ECU splice-point bus plug, the inline fuse, ground studs),
splices and inline parts in the middle, the branch cables right of them, devices right. Text spacing (Dan N99 a, 2026-11-08):
each end in a column is stepped so its label tag and the note on its row never overlap the next end's (pitch = max(box +
label, note height) + gap, on the 30 grid); notes in the notes column are stacked by their text height. A splice shared with
another harness is drawn with this harness's legs only and gets a note naming the other harness and its wires; the fuse
box seats are plain labelled terminals, no box groups (build_drawings.box_groups, Dan R1 a). Lengths: every routed length must equal the master
est_length_mm (the harness is in build_drawings.PLACED), else it stops; it also stops past 100 connections (plan limit).
gen_cabin.py runs on import, so its helpers are not imported."""
import sys, os, json, re, collections, math, csv, copy

COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Shield"}
# text spacing (Dan N99 a, 2026-11-08): the shared helpers in build_drawings (LABEL_H, note_h, end_span, text_step); GAP_TXT is
# the gap text_step keeps between notes' text, used here for the notes column and the heading notes too
GAP_TXT = 8


def build(REPO, OUT, CFG):
    sys.path.insert(0, os.path.join(REPO, 'docs/harness/tools'))
    import build_drawings as B
    import genroute
    LABEL_H, end_span, text_step = B.LABEL_H, B.end_span, B.text_step
    def note_half(text): return B.note_h(text) / 2       # half a note's drawn height, about its row's centre
    def stack_notes(notes, x):
        """put notes (each with a wanted 'y') in one column at x, top down, so no note's text runs into the next one's"""
        last = prev = None
        for n in sorted(notes, key=lambda n: n['_want']):
            y = n.pop('_want'); off = y % 30
            if last is not None:
                lo = last + note_half(prev['text']) + GAP_TXT + note_half(n['text'])     # row centre to row centre
                y = max(y, int(math.ceil((lo - off) / 30.0)) * 30 + off)
            n['schematicPosition'] = {"x": x, "y": y}; last, prev = y, n
        return notes
    H = B.Harness('ST185-harness')
    NAME, TITLE, REV, DATE, STEM = CFG['name'], CFG['title'], CFG['rev'], CFG['date'], CFG['stem']
    assert NAME in B.PLACED, NAME + ' is not placed: its lengths are not the tree yet (DECISIONS B8)'
    ALL = H.rows
    ROWS = [r for r in ALL if r['harness'] == NAME]
    W = [r for r in ROWS if r['wire_id']]
    assert not any(B.is_integral(r) or B.is_connector_pass(r) for r in W), 'an INTEGRAL / pass-through row: draw it as gen_heavydc.py does'
    SPARE = [r for r in ROWS if not r['wire_id']]
    PASS = [r for r in ALL if r['harness'] != NAME and NAME in (r.get('passes_through') or '')]
    PARTS_CSV = {p['part_number']: p for p in csv.DictReader(open(os.path.join(REPO, 'docs/sourcing/harness-parts.csv'), encoding='utf-8'))}
    LIB = json.load(open(os.path.join(OUT, 'lib.json')))['parts']
    for k in ('lockParts', 'contactParts', 'connectorParts', 'cableParts', 'wireParts', 'spliceParts', 'cavityPlugParts', 'resistorParts',
              'diodeParts', 'terminalParts', 'mountParts'): LIB.setdefault(k, [])
    def sid(s): return re.sub(r'[^A-Za-z0-9]', '_', s)
    def col(c): return c if c in COLORS else "Gray"
    STRIPE = CFG['stripe']

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
    NEW = CFG.get('new_parts', {})
    ALIAS = {('resistorParts', '1k 1/4W'): '1.0k 1/4W'}     # Dan 2026-11-01: the library's 1.0k part (as gen_cabin.py)
    def part_id(kind, pn):
        if not pn or pn.upper().startswith('TBD') or pn.startswith(('factory', 'in kit', 'pigtail', 'solder splice onto', 'none',
                                                                     'flying lead', 'screw terminal', 'solder onto')): return None
        pn = ALIAS.get((kind, pn), pn)
        p = next((p for p in LIB[kind] if p.get('partNumber') == pn), None)
        if p: return use_lib(kind, p)
        if pn not in NEW or pn not in PARTS_CSV: missing.add((kind, pn)); return None
        k, shape = NEW[pn]; assert k == kind, (pn, k, kind)
        c = PARTS_CSV[pn]
        p = dict(shape, partNumber=pn, manufacturer=c['manufacturer'], description=c['description'])
        LIB[kind].append(p); lib_add.append({"op": "add", "collection": kind, "value": p})
        return use_lib(kind, p)

    # ------------------------------------------------------------------ names (README "Pin text", B22)
    FRM = list(csv.DictReader(open(os.path.join(REPO, 'sot/fuse-relay-map.csv'), encoding='utf-8')))
    BANK = {'B1': 'New POWER fuse box', 'B2': 'New LOGIC fuse box', 'B3': 'New trunk relay block', 'B4': 'New EPS relay (B4)'}
    BOX_OF = {f['master_id']: BANK[f['bank']] for f in FRM if f['kind'] == 'relay' and f['master_id'].startswith('K-')}
    BOX_WHOLE = {'POWER': BANK['B1'], 'LOGIC': BANK['B2'], 'BATT-RELAY-BLOCK': BANK['B3']}
    FUSE = {(BANK[f['bank']], f['position']): f['circuit'] for f in FRM if f['kind'] == 'fuse' and f['circuit'] != '(vacant)'}
    def fuse_text(box, pin):
        c = FUSE.get((box, pin))
        return (c + ' fuse' if re.search(r'\d A$', c) else c) if c else pin
    def box_label(i):
        if i in BOX_OF: return '%s, %s' % (BOX_OF[i], i)
        return BOX_WHOLE.get(i)
    OEMNAME = CFG.get('oem_name', {})
    TAP_TERMS = CFG.get('tap_terms', {})      # a factory tap the master writes as a terminal: (OEM code, pin)
    def oem_lead(r, s):
        o = 'to' if s == 'from' else 'from'
        i, p = r[s + '_id'], r[s + '_pin']
        mine = r[o + '_type'] != 'OEM' or ('%s pin %s' % (i, p)) in r['oem_location']
        colour = r['oem_wire_colour'] if mine else ''
        m = re.search(r'onto the factory (\S.*?) lead', r['oem_method']) if mine else None
        if m and colour and m.group(1).startswith(colour): return 'the factory %s lead' % m.group(1)
        if colour:
            m = re.search(r'(?:^|[ ,(])%s(?: -|,) ([^(;:]+)' % re.escape(colour), r['oem_location'])
            return 'the factory %s lead%s' % (colour, ' (%s)' % m.group(1).strip() if m else '')
        return 'the factory lead'
    def oem_label(r, s):
        i, p = r[s + '_id'], r[s + '_pin']
        how = (r[s + '_terminal_pn'] + ' ' + r['oem_method']).lower()
        dev = '%s (%s) pin %s' % (OEMNAME.get(i, i), i, p)
        return '%s, spliced onto %s' % (dev, oem_lead(r, s)) if ('splice' in how or 'solder' in how or 'tap' in how) else dev + ' (at its own plug)'
    def tap_row(r, s):
        """a factory tap the master writes as a terminal (T-AT-DOOR, J/B No.1 1B-11): the same row as an OEM end, so its label and
        OEM splice note come from the shared helpers"""
        code, pin = TAP_TERMS[r[s + '_id']]
        m = re.match(r'OEM (.+?) \(', r[s + '_name'])
        return dict(r, **{s + '_type': 'OEM', s + '_id': code, s + '_pin': pin, s + '_desc': m.group(1) if m else r[s + '_desc']})

    # ------------------------------------------------------------------ connectors (drawn whole; other-harness cavities N/C + note)
    def pkey(p):
        m = re.match(r'(\d+)$', p)
        return (0, int(m.group(1)), '') if m else (1, 0, p)
    wired = {r[s + '_id'] for r in W for s in ('from', 'to')}     # a connector with only spare rows here is not drawn (R5)
    conn_ids = list(dict.fromkeys(r[s + '_id'] for r in W + SPARE for s in ('from', 'to')
                                  if r[s + '_type'] == 'connector' and r[s + '_id'] in wired))
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
        pins = sorted(use[c], key=pkey)
        if cpart and cpart.get('numberOfCavities') and all(re.match(r'\d+$', p) and 1 <= int(p) <= cpart['numberOfCavities'] for p in pins):
            pins = [str(i) for i in range(1, cpart['numberOfCavities'] + 1)]
        if cpart and c in B.BOX_CAVITIES:     # a new fuse box with its library part: every landing of the box drawing, vacant seats N/C
            assert set(pins) <= set(B.BOX_CAVITIES[c]), (c, set(pins) - set(B.BOX_CAVITIES[c])); pins = list(B.BOX_CAVITIES[c])
        RELAY_ORDER = ['30', '85', '86', '87', '87a']    # a relay socket is drawn whole: its unused blades (87a) N/C
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
                if here:      # a spare of this harness: its sealing plug from the master (TBD -> none), or a socket with no wire
                    r0, s0 = here[0][2], here[0][3]
                    if 'socket installed' in (r0[s0 + '_desc'] or ''):     # board pad cavity (docs/enclosures/csb3-hd34-pinmap.csv)
                        ct = part_id('contactParts', r0[s0 + '_terminal_pn'])
                        if ct: cv['contactPartId'] = ct     # explicit: a socket, not the config's default sealing plug
                        cv['cavityPlugPartId'] = None
                    else:
                        pl = part_id('cavityPlugParts', r0[s0 + '_terminal_pn'])
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
    OEM_T = {}        # terminal id of a factory lead -> its plug (C13-2, C13-11 ... one plug)
    SCREEN_T = set()  # the loose sealed end of each one-ended cable screen (at the device)
    # a flying-lead end that takes two different signals (the cluster / Pi CAN board "CANH + CANL pins", no pin numbers in the
    # master) is drawn as one end per signal, so CAN H and CAN L never read as one net; a ring or stud keeps all its wires
    tdescs = collections.defaultdict(set)
    for r in W:
        for s in ('from', 'to'):
            if r[s + '_type'] == 'terminal': tdescs[r[s + '_id']].add(r[s + '_desc'])
    def is_ring(nm): return any(k in nm.lower() for k in ('ring', 'stud', 'bolt', ' bar'))
    SPLIT_T = {i for i, d in tdescs.items() if len(d) > 1 and not is_ring(next(r[s + '_name'] for r in W for s in ('from', 'to') if r[s + '_id'] == i))}
    def tkey(r, s):
        t, i = r[s + '_type'], r[s + '_id']
        if t == 'OEM': return i + '-' + r[s + '_pin']
        return i + ('|' + r[s + '_desc'] if i in SPLIT_T else '')
    def tlabel(r, s):
        i = r[s + '_id']
        if r[s + '_type'] == 'OEM': return oem_label(r, s)
        if i in TAP_TERMS: return oem_label(tap_row(r, s), s)
        if B.BOX_RING.match(i): return 'New ' + r[s + '_name']     # a box stud ring (Dan N64 a)
        if i in SPLIT_T: return '%s (%s)' % (i, r[s + '_desc'])
        return box_label(i) or i
    # a shared splice with only one leg in this file (its other legs are in other files) is no splice here: a Loose end with
    # its R10 note and the 25 mm splice allowance (DECISIONS T3 / R10 / T7 b; build_drawings.one_leg_splices)
    ONE = B.one_leg_splices(W, TITLE)
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
            k = tkey(r, s)
            terms.setdefault(k, {"id": "t_" + sid(k), "label": tlabel(r, s), "type": 'Ring' if is_ring(r[s + '_name']) else 'Loose', "width": 240})
            if t == 'OEM': OEM_T["t_" + sid(k)] = i
            return {"id": "t_" + sid(k), "handle": "Terminal"}
        if t in ('resistor', 'diode'):
            reg, kind, pre = (resistors, 'resistorParts', 'r_') if t == 'resistor' else (diodes, 'diodeParts', 'd_')
            if i not in reg:
                reg[i] = {"id": pre + sid(i), "label": i}
                pid = part_id(kind, r[s + '_housing_pn'])
                if pid: reg[i]['partId'] = pid
            return {"id": pre + sid(i), "handle": "PIN" + p}      # PIN1 / PIN2 -> Left / Right once placed
        if t == 'cable screen':     # the screen floats at that end: drawn as a loose, sealed end at the device, so it runs the
            k = 'scr|' + i          # whole cable with its cores in both views and never stops at nothing (Dan 2026-11-08)
            terms.setdefault(k, {"id": "t_" + sid(k), "label": r['to_name'] or 'Screen end, %s' % i,
                                 "signal": 'Cable screen: floats here, cut back and sealed under heat-shrink',
                                 "type": 'Loose', "width": 240})
            SCREEN_T.add("t_" + sid(k))
            return {"id": "t_" + sid(k), "handle": "Terminal"}
        raise SystemExit('end type %r (%s): add it to gen_dash.py' % (t, r['wire_id']))
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
    for c in cables.values():   # core order = the cable part's core order (matched by colour); a core with no job here is cut back
        order = [k['color'] for k in doc_parts['cableParts'][c['partId']]['cores']]     # and sealed, but still sits in the cable
        have = [co['color'] for co in c['cores']]
        assert all(have.count(x) <= order.count(x) for x in have), (c['label'], order, have)
        for x in order:
            if x not in have: c['cores'].append({"id": "co_%s_nc_%s" % (sid(c['label']), x.lower()), "color": x})
        c['cores'].sort(key=lambda co: order.index(co['color']))
    def cseq(c): return c['cores'] + ([c['shield']] if 'shield' in c else [])
    CONDS = wires + [co for c in cables.values() for co in cseq(c) if 'source' in co]
    NC_CORES = [co for c in cables.values() for co in cseq(c) if 'source' not in co]
    def lab(cond): return cond.get('identLabel') or cond['id'][3:]
    # pin text (Dan 2026-11-01): each end shows its own master end description; a stud lists every description that lands on it
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
    for r in W:      # a POWER / LOGIC box ring terminal carries its bar's global signal (Dan N64 a)
        for s in ('from', 'to'):
            if B.ring_signal(r, s): comp['t_' + sid(tkey(r, s))]['signal'] = B.ring_signal(r, s)
    for c, n in conns.items():      # a new fuse box seat shows its fuse (sot/fuse-relay-map.csv), after the box name on the plug
        if c in BOX_WHOLE:
            for cv in n['cavities']:
                if cv.get('signal'): cv['signal'] = fuse_text(BOX_WHOLE[c], cv['designation'])
    # the notes that sit on an end's row, known before placing so each end gets room for its text (Dan N99 a): the full OEM splice
    # notes (README "Pin text", Dan Y6 / N16 a, build_drawings.oem_splice_note; a blank colour gets no note and is listed)
    oem_col, oem_txt, oem_skip = collections.OrderedDict(), {}, []
    for r in W:
        for s, c in B.oem_splices(r) + [(s, r['oem_wire_colour']) for s in ('from', 'to') if r[s + '_id'] in TAP_TERMS]:
            q = tap_row(r, s) if r[s + '_id'] in TAP_TERMS else r
            tid = 't_' + sid(tkey(r, s))
            if not c: oem_skip.append('%s %s %s' % (r['wire_id'], r[s + '_id'], r[s + '_pin'])); continue
            assert oem_col.setdefault(tid, c) == c, (tid, oem_col[tid], c)
            oem_txt.setdefault(tid, B.oem_splice_note(q, s, c))     # a shared tap keeps its first text
    for i, txt in ONE.items():      # a one-leg shared splice's R10 note sits where the OEM splice notes do (as gen_engc.py)
        oem_col['t_' + sid(i)], oem_txt['t_' + sid(i)] = 'R10', txt

    # ================================================================== schematic: sources left, splices middle, cables, devices right
    # README "harness.design" (Dan 2026-11-01 / 11-02 / 11-03 N1 a): the sources left (factory taps, fuse box seats, bus plug,
    # inline fuse, ground studs), splices and inline parts middle, the branch cables right of them (their cores run from the trunk
    # splices out to the devices, like the real cables), devices right; each wire horizontal with one 90 degree jog in its own
    # lane; columns level at the top, the right column half a grid lower.
    INFO = {}      # node id -> (master type, master id, layout node)
    for r in W:
        for s in ('from', 'to'):
            e = end(r, s)
            if e and e['id'] not in INFO: INFO[e['id']] = (r[s + '_type'], r[s + '_id'], H.place(r, s))
    NODES = {n['id']: n for n in list(conns.values()) + list(terms.values())}
    AREA = CFG['area']
    def is_left(i): return INFO[i][0] == 'splice' or CFG['left'](INFO[i][0], INFO[i][1])     # a one-leg splice end: its rest is a source
    # by area of the car; in an area the factory taps first, then plugs, then other terminals (a tap feeding a plug in its own
    # area, the II1 tap to the Pi inline fuse, sits right above it)
    LEFT_IDS = sorted([i for i in NODES if is_left(i)],
                      key=lambda i: (INFO[i][0] == 'splice',      # one-leg splice ends at the bottom, below the sources
                                     AREA.index(INFO[i][2]) if INFO[i][2] in AREA else 99,
                                     0 if INFO[i][0] == 'OEM' else 1 if i.startswith('c_') else 2, NODES[i]['label']))
    DEV_IDS = {i for i in NODES if i not in LEFT_IDS}
    def h(n): return 30 + 30 * len(n['cavities']) if 'cavities' in n else 30
    def cab_h(c): return 30 + 30 * len(cseq(c))
    def tap_plug(i): return OEM_T.get(i, i)     # factory leads of one plug stack close, like cavities
    def span(i): return end_span(NODES[i], [oem_txt[i]] if i in oem_txt else [])
    y, prev = 0, None
    for i in LEFT_IDS:
        n = NODES[i]
        if prev is not None:
            y += max(h(NODES[prev]) + (0 if tap_plug(i) == tap_plug(prev) and 'cavities' not in n else
                                       (30 if INFO[i][2] == INFO[prev][2] else 60)), text_step(span(prev), span(i)))
        n['schematicPosition'] = {"x": 0, "y": y}; prev = i
    LEFT_BOTTOM = y + h(NODES[prev]) if prev else 0
    def cav_y(n, handle):
        if 'cavities' not in n: return n['schematicPosition']['y'] + 15
        return n['schematicPosition']['y'] + 30 * ([cv['id'] for cv in n['cavities']].index(handle) + 1) + 15
    def ends(cond): return [e for e in (cond.get('source'), cond.get('target')) if e]
    cab_of = {co['id']: c for c in cables.values() for co in cseq(c)}
    used_rows = {cav_y(NODES[e['id']], e['handle']) for cond in CONDS for e in ends(cond) if e['id'] in LEFT_IDS}
    taken, cab_rows = collections.defaultdict(set), set()
    def core_row(c, co): return c['schematicPosition']['y'] + 30 * (cseq(c).index(co) + 1) + 15
    N_LC = sum(1 for c in cables.values() for co in cseq(c) for e in ends(co) if e['id'] in LEFT_IDS)
    CABLX = 240 + 30 * (3 + N_LC)
    def put_cable(c, want):
        k = cab_h(c) // 30
        # a free row above and below each cable keeps its label clear of the next cable's
        tops = [m for m in range(0, LEFT_BOTTOM + 30 * 60, 30) if not any(m + 30 * j + 15 in used_rows for j in range(k))
                and not any(m + 30 * j + 15 in cab_rows for j in range(-1, k + 1))]
        top = min(tops, key=lambda m: (abs(m + 45 - want), m))
        c['schematicPosition'] = {"x": 0, "y": top}      # x is set once the splices are placed
        cab_rows.update(top + 30 * j + 15 for j in range(k))
    for c in cables.values():   # every branch cable sits right of the splices, on rows next to what feeds its trunk splices
        mine = {co['id'] for co in cseq(c)}
        inl = {e['id'] for co in cseq(c) for e in ends(co) if e['id'][:2] in ('s_', 'r_', 'd_')}
        feeds = []
        for cond in CONDS:
            es = ends(cond)
            if cond['id'] in mine or not any(e['id'] in inl for e in es): continue
            cc = cab_of.get(cond['id'])
            if cc is not None and 'schematicPosition' in cc: feeds.append(core_row(cc, cond))
            feeds += [cav_y(NODES[e['id']], e['handle']) for e in es if e['id'] in LEFT_IDS]
        # a core with a left end (the Pi feed from the inline fuse) runs straight: the cable sits with that core on the end's row
        lefts = [cav_y(NODES[e['id']], e['handle']) - 30 * cseq(c).index(co) for co in cseq(c) for e in ends(co) if e['id'] in LEFT_IDS]
        put_cable(c, lefts[0] if lefts else min(feeds) if feeds else LEFT_BOTTOM)
    N_CR = sum(1 for c in cables.values() for co in cseq(c) for e in ends(co) if e['id'] not in LEFT_IDS)
    PX = CABLX + 60 + 30 * max(4, N_CR // 2)       # a resistor / diode with one end on the left column
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
        if o and o['id'] in LEFT_IDS: return cav_y(NODES[o['id']], o['handle'])
        return None
    def free_row(want, x):
        bad = used_rows | cab_rows | taken[x]
        yy = min((v for v in range(15, max(LEFT_BOTTOM, 3000) + 3000, 30) if v not in bad), key=lambda v: (abs(v - want), v))
        taken[x].add(yy); return yy
    _y = 15     # provisional right column (label order) so a part fed only from the right finds its rows; re-placed below
    for d in sorted(DEV_IDS, key=lambda d: NODES[d]['label']): NODES[d]['schematicPosition'] = {"x": 10 ** 6, "y": _y}; _y += h(NODES[d]) + 30
    def cab_row_of(i):     # an inline part on a cable core's trunk end sits on that core's row (a straight hop to the cable)
        return next((core_row(cab_of[cond['id']], cond) for cond, e, o in links[i] if cond['id'] in cab_of), None)
    pending = []
    for n in INL.values():      # an inline part fed by one left pin (or a cable core) sits on that row: a straight wire
        x = PX if two(n['id']) else SPX
        cands = [cab_row_of(n['id'])] + [left_row(cond, o) for cond, e, o in links[n['id']] if left_row(cond, o) is not None
                                         and deg[(o['id'], o['handle'])] == 1]
        st = next((v for v in cands if v is not None and v not in taken[x]), None)
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
        if o['id'] in INL: n = INL[o['id']]; return n['_x'] if '_x' in n else n['schematicPosition']['x']
        return 10 ** 5      # a cable (right of the splices)
    for n in INL.values(): n['schematicPosition'] = {"x": n.pop('_x'), "y": n.pop('_row') - 15}
    CAB_X = (max([n['schematicPosition']['x'] for n in INL.values()] + [CABLX]) + 180) // 30 * 30
    for c in cables.values(): c['schematicPosition']['x'] = CAB_X
    for n in INL.values():
        if not two(n['id']): continue
        # handles: the end whose far side lies further left goes on Left; a diode keeps anode = pin 1 (anodeOnRight when flipped)
        es = [(e, other_x(o) if cond['id'] not in cab_of else 10 ** 5) for cond, e, o in links[n['id']]]
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
    # right column: ordered by the mean row of what feeds it, so lanes cross least (connectors may be reordered, pins never); an
    # end wired only to another right-column end (the alarm ground lead to its ring) sits just above that end
    bary = collections.defaultdict(list); partner = {}
    for cond in CONDS:
        es = ends(cond)
        for e in es:
            if e['id'] in DEV_IDS:
                c = cab_of.get(cond['id'])
                bary[e['id']] += [core_row(c, cond)] if c else [row_of_end(o) for o in es if o is not e and row_of_end(o) is not None]
                partner.update({e['id']: o['id'] for o in es if o is not e and o['id'] in DEV_IDS})
    DEV_ORDER = sorted([d for d in DEV_IDS if bary[d]], key=lambda d: (sum(bary[d]) / len(bary[d]), NODES[d]['label']))
    for d in sorted(d for d in DEV_IDS if not bary[d]):
        p = partner.get(d)
        DEV_ORDER.insert(DEV_ORDER.index(p) if p in DEV_ORDER else len(DEV_ORDER), d)
    def place_right(devx):
        y, prev = 15, None
        for d in DEV_ORDER:
            n = NODES[d]
            if prev is not None: y += max(h(NODES[prev]) + 30, text_step(end_span(NODES[prev]), end_span(n)))
            n['schematicPosition'] = {"x": devx, "y": y}; prev = d
        return y + h(NODES[prev]) if prev else 15
    def doc_now():
        return {"connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
                "resistors": list(resistors.values()), "diodes": list(diodes.values()), "wires": wires, "cables": list(cables.values())}
    def route_cost(devx):    # (unrouted conductors, conductors that need more than one lane) with the right column at devx
        place_right(devx)
        R_, segs_, res_ = genroute.run(copy.deepcopy(doc_now()))
        return (sum(1 for s in segs_ if res_.get(s['k']) is None), sum(1 for v in res_.values() if v and len(v) > 2))
    XMAX = max([n['schematicPosition']['x'] for n in INL.values()] + [CAB_X if cables else CABLX])
    n_right = sum(1 for cond in CONDS for e in ends(cond) if e['id'] in DEV_IDS)
    DEVX = (XMAX + 150 + 30 * n_right) // 30 * 30
    base = route_cost(DEVX)
    print('widest right column x', DEVX, 'routing (unrouted, multi-lane)', base, flush=True)
    lo, hi = XMAX + 300, DEVX        # compact (Dan 2026-11-02): the narrowest lane field that routes as cleanly
    while hi - lo > 30:
        mid = (lo + hi) // 60 * 30
        if route_cost(mid) <= base: hi = mid
        else: lo = mid
    DEVX = hi
    RIGHT_BOTTOM = place_right(DEVX)
    print('right column x', DEVX, 'bottom', RIGHT_BOTTOM, '| left bottom', LEFT_BOTTOM, flush=True)

    # ------------------------------------------------------------------ notes
    spares = collections.defaultdict(list)
    for r in SPARE:
        if r['from_type'] == 'connector' and r['from_id'] in conns: spares[r['from_id']].append((r['from_pin'], r['from_terminal_pn']))
    left_txt, right_txt = [], []
    BOX_SEATS = set(B._seat_map()) | {'LOGIC'}     # box guts are not drawn (Dan R1 a): no spare / N/C notes for box seats
    for c in conns:
        if c in BOX_SEATS: continue
        txt = []
        if spares.get(c):
            by = collections.defaultdict(list)
            for p, pl in spares[c]: by[pl if pl and pl != 'TBD' else 'TBD'].append(p)
            txt.append('%s: %s %s spares (spare cavity part from the master: %s).' % (
                c, ('pins %s are' if len(spares[c]) > 1 else 'pin %s is') % ', '.join(sorted((p for p, _ in spares[c]), key=pkey)), NAME,
                '; '.join('%s %s' % (k, ', '.join(sorted(v, key=pkey))) for k, v in sorted(by.items()))))
        if other_owned.get(c):
            by = collections.defaultdict(list)
            for pin, own in other_owned[c]: by[own].append(pin)
            txt.append('%s: N/C cavities are wired by other harnesses - %s.' % (c, '; '.join('%s see %s' % (', '.join(sorted(v, key=pkey)), k)
                                                                                for k, v in sorted(by.items()))))
        if txt: (left_txt if conns[c]['id'] in LEFT_IDS else right_txt).append(' '.join(txt))
    for r in SPARE:      # a reserved node with no wire (the alarm hazard-flash node, Dan N47): not drawn, named here
        if r['from_type'] == 'terminal':
            right_txt.append('%s: %s, reserved, no wire (not drawn).' % (r['from_id'], r['from_name'] or r['from_id']))
    if NC_CORES:
        right_txt.append('Cable cores with no %s job (cut back and sealed under heat-shrink at both ends): %s.' % (NAME, '; '.join(
            '%s %s' % (B.CABLE_NAMES.get(cab_of[co['id']]['label'], cab_of[co['id']]['label']), co['color'].lower()) for co in NC_CORES)))
    scr = [B.CABLE_NAMES.get(c['label'], c['label']) for c in cables.values()
           if 'shield' in c and c['shield'].get('target', {}).get('id') in SCREEN_T]
    if scr: right_txt.append('Cable screens %s: %s' % (', '.join(scr), CFG.get(      # CFG 'screen_note': a harness whose screens are not CAN
        'screen_note', 'spliced onto the CAN trunk screen at their branch point, cut back and sealed at the device end '
                       '(DECISIONS "CAN wiring (B17)", Dan 2026-11-07).')))
    # a splice shared with another harness file is drawn with this file's legs only; its note is the R10 note (DECISIONS B6 R10:
    # the other file, where the splice sits, the EWD pages, its other legs and their far ends, the colour spliced onto)
    shared = []
    for sname, sp in splices.items():
        t = B.r10_note(sname, TITLE)
        if t:
            shared.append({"id": "n_" + sid(sname), "width": 360, "_want": sp['schematicPosition']['y'],
                           "text": '%s (the splice is drawn here with its %s legs only).' % (t[:-1], NAME)})
    # a device pigtail the new wire is spliced onto (not a factory wire, so no OEM splice note): a pin note from the master end
    # detail on that end's row (Dan A3: the high-beam LED feed onto the LED's own 20 AWG pigtail)
    for r in W:
        for s in ('from', 'to'):
            if r[s + '_type'] == 'diode' and 'pigtail' in r[s + '_desc'] and 'splice' in r[s + '_terminal_pn']:
                n = INL['d_' + sid(r[s + '_id'])]
                shared.append({"id": "n_pin_" + sid(r[s + '_id']), "width": 360, "_want": n['schematicPosition']['y'],
                               "text": '%s pin %s: %s.' % (r[s + '_name'], r[s + '_pin'], re.sub(r'^Detail:\s*', '', r[s + '_note']).rstrip('.'))})
    used_st = sorted({row_of[w['identLabel']]['circuit_id'] for w in wires if 'stripeColor' in w}, key=list(STRIPE).index)
    head = [{"id": "n_title", "width": 360,
             "text": "%s Rev %s (%s): %s Viewer copy generated from docs/harness/MASTER-wirelist.csv (harness = %s) by docs/harness/tools/%s; "
                     "never a source. Schematic: %s left, splices and inline parts middle, %sdevices right; columns level at the top (right "
                     "column half a grid lower, N1 a); each end spaced so its label and notes clear the next (Dan N99 a). Each pin shows its "
                     "own master end text; a wire spliced onto a factory wire carries the full OEM splice note at its tap (Dan Y6, N16 a); a "
                     "splice shared with another harness file is drawn with its %s legs only and its note says where the rest goes (the "
                     "other file, where the splice sits, the EWD page, the other legs' far ends and colour; R10).%s Shared plugs "
                     "are drawn whole; cavities wired by other harnesses are N/C with a note. %s"
                     "Layout: a formboard of the ST185-harness.layout.json tree (route drawn by Claude, devices refined by Dan), straight orthogonal bundles, "
                     "front of car RIGHT, rear LEFT, driver side UP; drawn length is not to scale; each part on a 100 mm end-allowance "
                     "stub (a splice on a 25 mm stub, Dan T7 b); bundle lengths = the master est_length_mm." % (
                         TITLE, REV, DATE, CFG['scope'], NAME, CFG['script'], CFG['left_words'],
                         'the branch cables right of them, ' if cables else '', NAME, B.LOOSE_SENTENCE if ONE else '', B.GHOST_MARK)}]
    if used_st:      # display stripes note, only when the harness has a loose +12 V wire
        head.append({"id": "n_stripes", "width": 360,
             "text": "DISPLAY STRIPES ON +12 V WIRES ARE FOR TRACING ONLY (Dan 2026-11-01). Every +12 V wire is plain RED insulation, as in "
                     "the master wire list and BOM. Stripe per circuit: " + '; '.join('%s = %s' % (STRIPE[k][1], STRIPE[k][0]) for k in used_st) +
                     "." + (" Red cable cores keep their cable's colours." if cables else "")})
    # the heading notes sit above everything, their text clear of the top end's label tag (Dan N99 a)
    HEAD_Y = int(math.floor((-LABEL_H - GAP_TXT - 15 - max(note_half(n['text']) for n in head)) / 30.0)) * 30
    for i, n in enumerate(head): n['schematicPosition'] = {"x": 390 * i, "y": HEAD_Y}
    NOTES = list(head)
    OEMW = 360                       # the full N16 a note at harness.design's widest note (60-360)
    for tid in oem_col:
        p = NODES[tid]['schematicPosition']; assert tid in LEFT_IDS, tid
        NOTES.append({"id": "n_oem_" + tid, "text": oem_txt[tid], "width": OEMW, "alignment": "Right",
                      "schematicPosition": {"x": p['x'] - OEMW, "y": p['y']}})
    print('OEM splice notes', len(oem_col), '| blank colour, no note:', ', '.join(oem_skip) or 'none', flush=True)
    N_LL = sum(1 for cond in CONDS if len([e for e in ends(cond) if e['id'] in LEFT_IDS]) == 2)
    LL_X = -420 - (OEMW if oem_col else 0) - 30 * N_LL
    if left_txt: NOTES.append({"id": "n_left", "width": 360, "text": ' '.join(left_txt), "schematicPosition": {"x": LL_X, "y": 0}})
    col_r = ([{"id": "n_right", "width": 360, "text": ' '.join(right_txt), "_want": 15}] if right_txt else []) + shared
    NOTES += stack_notes(col_r, DEVX + 270)

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
        p, mm = H.route(r)
        assert p is not None, (r['wire_id'], H.problems[-1:])
        hroute[r['wire_id']] = mm
        for a, b in zip(p, p[1:]): segs[tuple(sorted((a, b)))] += 1
    tree_nodes = {n for k in segs for n in k} | set(node_items) | set(inline_at)
    adj = collections.defaultdict(list)
    for a, b, mm in H.layout['segments']:
        if tuple(sorted((a, b))) in segs: adj[a].append((b, mm)); adj[b].append((a, mm))
    ROOT = CFG['root']
    assert ROOT in tree_nodes, ROOT
    parent, slen, kids = {ROOT: None}, {}, collections.defaultdict(list)
    todo = [ROOT]
    while todo:
        n = todo.pop(0)
        for m, mm in adj[n]:
            if m not in parent: parent[m] = n; slen[m] = mm; kids[n].append(m); todo.append(m)
    assert tree_nodes <= set(parent), tree_nodes - set(parent)
    assert sum(len(v) for v in adj.values()) // 2 == len(parent) - 1, 'the segments this harness uses are not a tree'
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
    # 30 grid, each branch at 90 degrees; front of the car RIGHT, rear LEFT, driver side UP (each branch heads the way its part of
    # the car lies); drawn length is not to scale, every bundle keeps its tree length (= the master's). Each part sits on its
    # 100 mm end-allowance stub, combed off the node; a node whose four sides are all taken combs its parts along the way in.
    DV = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}
    OPP = {'R': 'L', 'L': 'R', 'U': 'D', 'D': 'U'}
    GAP, MINL, ISP, LBL = 60, 150, 60, 240        # clearance, shortest drawn bundle, comb pitch, room for a part's label
    GGAP = 180                                     # extra space between comb groups (CFG 'comb_group')
    ALLC = {x['id']: x for x in list(conns.values()) + list(terms.values()) + list(INL.values())}
    XY = H.layout['nodes']
    STUB = H.layout.get('end_allowance_mm', 100)
    SPL = H.layout.get('splice_allowance_mm', STUB)     # a splice end's allowance (Dan T7 b, 2026-11-10: 25 mm; strip and solder)
    LOOSE_T = {'t_' + sid(i) for i in ONE}     # a one-leg splice's Loose end stands in for the splice end: the splice allowance
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
        free = [d for d in 'RULD' if din is None or d != OPP[din]]
        asg = {}
        for c in sorted(kids[n], key=lambda c: (-len(sub_nodes(c)), c)):
            v = heading(n, c); left = [d for d in free if d not in asg.values()]
            assert left, ('more branches than directions at', n)
            asg[c] = max(left, key=lambda d: (DV[d][0] * v[0] + DV[d][1] * v[1]) / (math.hypot(*v) or 1))
        items = node_items.get(n, []) + inline_at.get(n, [])
        # optional comb groups (CFG 'comb_group', view only): the parts at one node combed group by group, with a clear gap
        # between groups (CabinPower: POWER box ends, then LOGIC box ends, then the rest; Dan 2026-11-08 "separate the two fuse
        # boxes a little more"); stubs keep their 100 mm length, so no routed length changes
        grp = {cid: (CFG['comb_group'](*(INFO[cid][:2] if cid in INFO else (None, cid)), BOX_OF) if 'comb_group' in CFG else 0)
               for cid in items}
        items = sorted(items, key=lambda cid: grp[cid])     # stable: keeps the master order inside a group
        gofs = [GGAP * sum(1 for a, b in zip(items, items[1:i + 1]) if grp[a] != grp[b]) for i in range(len(items))]
        pad = CFG.get('comb_pad', {})      # optional extra room before a group (view only), e.g. to keep a live group in place
        gofs = [g + sum(pad.get(x, 0) for x in sorted({grp[c] for c in items[:i + 1]})) for i, g in enumerate(gofs)]
        rects, P, S = [], {n: (0, 0)}, {}
        ray = [rect((-DV[din][0] * 90, -DV[din][1] * 90), (-DV[din][0] * 10 ** 6, -DV[din][1] * 10 ** 6))] if din else []
        if items:
            left = [d for d in free if d not in asg.values()]
            cd = (din if din in left else next(d for d in ('U', 'D', 'R', 'L') if d in left)) if left else OPP[din]
            k, (dx, dy) = len(items), DV[cd]
            if dy == 0:     # a column of parts across the end of a horizontal stub
                ys = [ISP * i - 30 * (k - 1) + gofs[i] for i in range(k)]; xj = dx * 90
                for cid, yy in zip(items, ys):
                    S[cid] = (n, (dx * 150, yy), [(xj, 0), (xj, yy)] if yy else [])
                rects += [rect((dx * 90, 0), (dx * 90, 0)), rect((xj, ys[0]), (dx * (150 + LBL), ys[-1]))]
            else:           # parts combed off a vertical spine, to the front (right) side
                for i, cid in enumerate(items):
                    yy = dy * (120 + ISP * i + gofs[i]); S[cid] = (n, (120, yy), [(0, yy)])
                last = 120 + ISP * (k - 1) + gofs[-1]
                rects += [rect((0, dy * 90), (0, dy * last)), rect((0, dy * 90), (120 + LBL, dy * (last + 30)))]
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
    allrects, pos, stubs = lay(ROOT, None)
    xs = [r[0] for r in allrects] + [r[2] for r in allrects]
    print('formboard width %d .. %d' % (min(xs), max(xs)))
    assert all(v[0] % 30 == 0 and v[1] % 30 == 0 for v in pos.values())
    bps = [{"id": "bp_" + sid(n), "layoutPosition": {"x": pos[n][0], "y": pos[n][1]}} for n in parent]
    bundles = []
    for n, p in parent.items():
        if p is None: continue
        assert pos[n][0] == pos[p][0] or pos[n][1] == pos[p][1], (p, n)
        bundles.append({"id": "bn_" + sid(n), "sourceId": "bp_" + sid(p), "targetId": "bp_" + sid(n), "length": {"value": int(slen[n]), "unit": "mm"}})
    INL_AT = {}
    for cid, (nd, q, pts) in stubs.items():
        direct = cid[:2] in ('c_', 't_')
        b = {"id": "bn_" + cid, "sourceId": "bp_" + sid(nd), "targetId": cid if direct else "bp_" + cid, "length": {"value": SPL if cid[:2] == "s_" or cid in LOOSE_T else STUB, "unit": "mm"}}
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
              for w in CONDS if 'target' in w}
    bad = {k: (v, hroute[k], row_of[k]['est_length_mm']) for k, v in expect.items() if not (v == hroute[k] == int(float(row_of[k]['est_length_mm'] or -1)))}
    bad.update({lab(w): (None, hroute[lab(w)], row_of[lab(w)]['est_length_mm']) for w in CONDS if 'target' not in w
                and hroute[lab(w)] != int(float(row_of[lab(w)]['est_length_mm'] or -1))})
    assert not bad, 'routed length != tree route != master est_length_mm: %r' % bad
    for w in CONDS:     # a one-ended screen: its expected length is its tree route (the screen runs the whole cable)
        if 'target' not in w: expect[lab(w)] = hroute[lab(w)]
    assert sorted(lab(w) for w in CONDS) == sorted(r['wire_id'] for r in W) and len({lab(w) for w in CONDS}) == len(W)
    cav_n = collections.Counter((e['id'], e['handle']) for w in CONDS for e in ends(w) if e['id'].startswith('c_'))
    cav_m = collections.Counter(("c_" + sid(r[s + '_id']), cav_of[(r[s + '_id'], r[s + '_pin'])]) for r in W
                                for s in ('from', 'to') if r[s + '_type'] == 'connector')
    assert cav_n == cav_m and all(v == 1 for v in cav_n.values()), {k: v for k, v in cav_n.items() if v > 1}
    NCONN = len(CONDS) + len(NC_CORES)
    assert NCONN <= 100, 'over the 100-connection plan limit: split by whole circuits into numbered documents (README)'
    doc = {"version": 1.3, "currency": "$", "lengthUnit": "mm", "gaugeUnit": "AWG", "schematic": {"connectorWidth": 240, "terminalWidth": 240},
           "connectors": list(conns.values()), "terminals": list(terms.values()), "splices": list(splices.values()),
           "resistors": list(resistors.values()), "diodes": list(diodes.values()), "wires": wires, "cables": list(cables.values()),
           "branchPoints": bps, "bundles": bundles, "schematicNotes": NOTES}
    if cables:     # the layout view draws a cable's cores one by one (a cable is schematic-only in harness.design): say they are one cable
        ys_ = [r[1] for r in allrects]
        doc['layoutNotes'] = [{"id": "n_lay_cables", "width": 360, "layoutPosition": {"x": min(xs) // 30 * 30, "y": (min(ys_) - 360) // 30 * 30},
            "text": "Shielded cables: the app draws each cable's cores one by one in this view. Each is ONE shielded cable in the build: "
                    + '; '.join('%s = %s (%s and its screen)' % (B.CABLE_NAMES.get(c['label'], c['label']), doc_parts['cableParts'][c['partId']].get('partNumber', c['partId']),
                                ', '.join(co['color'].lower() for co in c['cores'])) for c in cables.values())
                    + ". Each screen runs the whole cable and ends at its 'Screen end' (floats, cut back and sealed under heat-shrink)."}]
    for k, v in doc_parts.items():
        if v: doc[k] = list(v.values())
    for k in [k for k in doc if doc[k] == []]: del doc[k]
    have = {p['id'] for k, v in doc.items() if k.endswith('Parts') for p in v}
    refs = {x['partId'] for k in ('wires', 'splices', 'cables', 'connectors', 'resistors', 'diodes') for x in doc.get(k, []) if x.get('partId')} | \
           {cv[k] for n in doc['connectors'] for cv in n['cavities'] for k in ('contactPartId', 'cavityPlugPartId') if cv.get(k)} | \
           {a['partId'] for k, v in doc.items() if k.endswith('Parts') for p in v for c in p.get('configurations', []) for a in c.get('accessories', [])}
    assert refs <= have, refs - have
    R_, segs_, res_ = genroute.run(doc)
    # a wire with both ends on the left column (the II1 tap to the Pi inline fuse just below it): genroute runs it down the
    # outside left, through its tap's own OEM splice note; a short loop on the right side of the column keeps the note clear
    for s in segs_:
        if s['k'][0] != 'w' or s['P'][0] != s['Q'][0] or not all(e in LEFT_IDS for e in s['ends']): continue
        for x in range(255, 255 + 30 * 20, 30):
            pts = [s['P'], (x, s['P'][1]), (x, s['Q'][1]), s['Q']]
            if R_.free(pts, s['ends'], s['net']): R_.commit(pts, s['net']); res_[s['k']] = pts[1:-1]; break
    unrouted = genroute.apply(doc, segs_, res_)
    assert not unrouted, 'unrouted wires: %r' % unrouted
    B.relabel(doc, lib=LIB)          # Dan's plain-label rules R1-R9 (2026-11-08), after placement so positions stay
    print('empty connectors dropped (R5):', B.relabel.removed)
    B.box_groups(doc)       # box seat ends as labelled terminals, no box groups, unused parts pruned (Dan R1 a)
    NGHOST = B.add_ghosts(doc, H, NAME)      # other harnesses' wires in these bundles (Dan T4 a)
    assert NCONN + NGHOST <= 100, 'ghost wires push %s over the 100-connection limit' % NAME
    # the title note says which pass-through wires are drawn as ghosts (wire labels, never ids, B22); the heading notes are
    # placed again for the filled text, clear of the top end's label tag (Dan N99 a)
    B.fill_ghost_note(doc, NAME, label=lambda r: '"%s"' % (r.get('wire_label') or r['wire_id']))
    head_ids = {n['id'] for n in head}
    head_now = [n for n in doc['schematicNotes'] if n['id'] in head_ids]
    HEAD_Y = int(math.floor((-LABEL_H - GAP_TXT - 15 - max(note_half(n['text']) for n in head_now)) / 30.0)) * 30
    for n in head_now: n['schematicPosition']['y'] = HEAD_Y
    json.dump(doc, open(os.path.join(OUT, STEM + '.json'), 'w'), indent=1)   # routed: upload as is
    json.dump(lib_add, open(os.path.join(OUT, STEM + '_lib_ops.json'), 'w'), indent=1)
    json.dump(expect, open(os.path.join(OUT, STEM + '_expect.json'), 'w'), indent=1)
    n_ = lambda k: len(doc.get(k, []))
    print(TITLE, 'Rev', REV, '| connectors', n_('connectors'), 'terminals', n_('terminals'), 'splices', n_('splices'), 'resistors', n_('resistors'),
          'diodes', n_('diodes'), 'wires', n_('wires'), 'cables', len(cables), 'conductors (connections)', NCONN, '+ ghosts', NGHOST, '(%d cores with no job)' % len(NC_CORES),
          'bundles', len(bundles), 'bps', len(bps), 'DEVX', DEVX, '| lengths = master:', len(expect),
          '| lib adds (not applied)', [o['value']['partNumber'] for o in lib_add], '| no library part (left unset):', sorted(missing))
    return doc


# ---------------------------------------------------------------------------------------------- ST185-Dash (Dan B8 = a)
DASH = dict(
    name='Dash', title='ST185-Dash', rev='E', date='2026-11-12', stem='dash', script='gen_dash.py', root='ECU',
    scope="the Dash harness (was CAN + CSB3 + ClusterLED, Dan B8 = a): the cabin CAN trunk (Dan P1, T1 a) - one shielded trunk "
          "from ECU plug C past a tap splice at each node, ECUMaster CSB3 tap, then the cluster tap, then the RealDash Pi tap, then on "
          "through the firewall bulkhead to the CAN-Lambda (the ECU C - CSB3 tap and Pi tap - bulkhead legs are AB-cabin 2's; Dash has "
          "the two trunk legs between the taps), a 205 mm 2-core shielded drop from each tap to its node, and plain +12 V / ground "
          "wires per node (feeds LOGIC DEV 5 A, LOGIC CSB 5 A and the factory CIG & RADIO ACC lead through the 5 A inline fuse F-PI; "
          "each node ground to the cabin ground splice); the CSB3 plug, "
          "the 8-channel opto board, the cruise ladder resistor, the cruise switch, clutch switch, stop switch and dimmer taps; the "
          "cluster warning LEDs on the cluster plug taps, their common ground spliced onto the factory cluster ground C13 (B) pin 1 (to ground point ID; Dan N106 a / N83 a); the high-beam LED fed straight from the high-beam output splice SP-HR-HI by the LOGIC box, spliced onto the LED's own pigtail (Dan A2 b / A3).",
    left_words='the sources (factory taps, the LOGIC box seats, the ECU splice-point bus plug, the Pi inline fuse)',
    # a source end: a factory tap, a fuse box, a bus plug, the inline fuse (its OUT feeds the Pi branch cable, so it sits left of
    # the cables, just below the II1 tap that feeds it), a ground stud
    left=lambda t, i: t == 'OEM' or i in ('LOGIC', 'BUS-5V-2', 'F-PI', 'GND-ID'),
    area=['PI', 'CANJ', 'GB', 'SP', 'CLUSTER', 'COLUMN', 'PEDAL', 'JB1'],
    oem_name={'C13': 'Combination meter plug B', 'C14': 'Combination meter plug C', 'C16': 'Cruise control switch, combination switch plug B',
              'C17': 'Cruise control clutch switch', 'S9': 'Stop lamp switch', 'R10': 'Dimmer rheostat', 'II1': 'Cowl plug (old radio ACC feed)'},
    # display stripes on +12 V wires, one per circuit (README "Display stripes"); the LED IG feed circuits share one stripe
    stripe={'DEV': ('White', 'cluster feed (LOGIC DEV 5 A)'), 'CSB': ('Green', 'CSB3 feed (LOGIC CSB 5 A)'),
            'PI': ('Orange', 'RealDash Pi feed (factory CIG & RADIO ACC, 5 A inline fuse)'),
            'LIG': ('Yellow', 'LED IG +12 V (C14 pin 9 to the park brake, charge and oil LEDs)'), 'LCHG': ('Yellow', 'charge LED +'),
            'LOIL': ('Yellow', 'oil LED +'), 'LPK': ('Yellow', 'park brake LED +'),
            'LTL': ('Violet', 'turn LH LED +'), 'LTR': ('Pink', 'turn RH LED +'), 'LHB': ('Blue', 'high beam LED +'),
            'HLSENSE': ('Brown', 'lights-on sense (R10 TAIL)')},
    # parts not yet in library 5LO8 (maker and description from harness-parts.csv); written to <stem>_lib_ops.json, not applied
    new_parts={'0FHM0003ZXJB': ('connectorParts', {"id": "cp_0fhm0003zxjb", "hasShell": False, "numberOfCavities": 2})},
)

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], DASH)
