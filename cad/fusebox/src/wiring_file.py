"""Fuse box wiring build files (BACKLOG row 107, Dan 2026-11-14: "one graphical wiring file per box ... he builds from it").

One PDF per box (POWER, LOGIC, trunk battery relay block) plus a PNG of every page, in cad/fusebox/rev<N>/:
  page 1  SEATS, top view: every fuse and relay seat with what plugs in (rating / part number, circuit); empty seats SPARE.
  page 2  WIRES, seen from below (the side the box is wired from): every wire drawn on its in-box path to its terminal,
          in its insulation colour, with a number at the terminal and at the exit.
  page 3+ WIRE TABLE: number, wire, gauge and colour, both ends in plain names, the terminal part and its crimp tool at
          each end (Dan: list the crimp tool with each crimp contact).
Nothing is drawn by hand: the paths, terminals, gauges and colours come from cad/fusebox/rev<N>/wiring_plan.json
(wiring_sim.py: the master wire list, read-only, + spec.BOX_WIRES), the seats from spec.py (rev 8) and
sot/fuse-relay-map.csv, the lid labels from fusebox_report.json (the Fusion build).

  python cad/fusebox/src/wiring_file.py            # writes the three PDFs and their PNG pages
Claude Code, 2026-11-22.
"""
import csv, json, os, re, sys, textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REV_DIR = os.path.join(REPO, 'cad', 'fusebox', 'rev%d' % S.REV)
PLAN = json.load(open(os.path.join(REV_DIR, 'wiring_plan.json'), encoding='utf-8'))
REPORT = json.load(open(os.path.join(REV_DIR, 'fusebox_report.json'), encoding='utf-8'))
SOT = list(csv.DictReader(open(os.path.join(REPO, 'sot', 'fuse-relay-map.csv'), encoding='utf-8')))
MODEL = 'Fusion ST185_fusebox_rev7 v60 = models folder st185_fusebox_1101 revE'      # the model this plan and report belong to
PAGE = (17.0, 11.0)
DPI = 150
COL = {'Red': '#d42a2a', 'Black': '#1a1a1a', 'White': '#ffffff', 'Yellow': '#f0c400'}
BOXES = {'POWER': ('power', 'POWER box (glove box)', 'B1'), 'LOGIC': ('logic', 'LOGIC box (glove box)', 'B2'),
         'BATT': ('battrelay', 'Battery relay block (trunk)', 'B3')}

# Terminal -> (what it is, crimp tool). A tool is named only where a maker or distributor listing was read (source in the
# text); everything else is TBD with the reason, never a guess (DECISIONS A81).
TBD_TE = 'TBD (TE tooling list for this contact not read: te.com "Compatible Parts & Tooling" did not load)'
K05 = 'Klauke K05 hand tool, hexagonal crimp, 6 - 50 mm2 (RS 398-2270 listing; confirm the die mark = the lug code number)'
ERGO = ('TE ERGOCRIMP frame 539635-1 + MCP 2.8 receptacle die set 539722-2 or 539723-2 (RS 876-2175 / 876-2144 listings); '
        'which die for this wire size: TBD (TE die sheet not read)')
TERMINAL = {
    '42281-1': ('TE FASTON .250 receptacle, 18-14 AWG', TBD_TE),
    '280919-2': ('TE FASTIN-FASTON .187 receptacle, 20-15 AWG', TBD_TE),
    '280756-4': ('TE FASTON .375 receptacle, 12-10 AWG', TBD_TE),
    '280755-4': ('TE FASTON .375 receptacle, 10-7 AWG', TBD_TE),
    '63467-1': ('TE FASTIN-FASTON .250 receptacle, 14-10 AWG', TBD_TE),
    '1-968849-1': ('TE MCP 2.8 receptacle, 20-18 AWG', ERGO),
    '1-968851-1': ('TE MCP 2.8 receptacle, 16-14 AWG', ERGO),
    '282110-1': ('TE Superseal 1.5 receptacle contact', TBD_TE),
    '36161': ('TE PIDG ring, 12-10 AWG, M5', TBD_TE),
    '320572': ('TE PIDG ring, 22-16 AWG, M8', TBD_TE),
    '320554': ('TE PIDG ring, 22-16 AWG, M4', TBD_TE),
    '53941-1': ('TE ring, 16-14 AWG, M4', TBD_TE),
    'PV10-56R': ('Panduit ring, 12-10 AWG, M8', 'TBD (Panduit tool list not read)'),
    '1R6': ('Klauke tubular lug 6 mm2, M6', K05), '2R5': ('Klauke tubular lug 10 mm2, M5', K05),
    '3R5': ('Klauke tubular lug 16 mm2, M5', K05), '6R8': ('Klauke tubular lug 50 mm2, M8', K05),
}
FAR_TOOL = [(r'^046[02]-\d{3}-(20|16|12)\d', 'DEUTSCH HDT-48-00 (as PROJECT-BOM)')]
SPLICE_TOOL = 'none: solder joint, then TE ATUM-6/2 adhesive heat shrink (heat gun), DECISIONS A20 a'


def pn_key(part):
    return re.sub(r'^(TE|Klauke|Panduit)\s+', '', part or '').strip()


def term_text(part, far=False):
    """'part (what) | crimp tool' for one wire end."""
    if not part:
        return ('outside this box', 'see the harness wire list for this end') if far else ('-', '-')
    k = pn_key(part)
    if k in TERMINAL:
        return ('%s  %s' % (k, TERMINAL[k][0]), TERMINAL[k][1])
    for pat, tool in FAR_TOOL:
        if re.search(pat, k):
            return (k, tool)
    return (k, 'see the harness parts list (PROJECT-BOM crimp tool column)')


def nat(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]


def sot_row(bank, pos):
    for r in SOT:
        if r['bank'] == bank and r['position'] == pos:
            return r
    return None


# ---------------------------------------------------------------- seats (what plugs in where)
CAVS = {}
for _c in PLAN['cavities']:
    CAVS.setdefault(_c['box'], {})[_c['cav']] = _c
LIDS = {k.split('_')[0]: v for k, v in REPORT['labels'].items()}          # 'Logic' / 'Power' / 'BattRelay' -> etched texts, build order
RB_Y = S.RB['y_b'] - S.HCR['term_y']                                       # battery block power line (stud axis)
RB_PT = {'in': (S.RB['x_stud'], RB_Y), 'fp_in': (S.RB['x_ami_in'], RB_Y), 'fp': (S.RB['x_ami_in'] + S.AMI['c'], RB_Y),
         '3': (S.RB['x_t3'], RB_Y), '5': (S.RB['x_t3'] + S.HCR['term_pitch'], RB_Y)}


RELAY_PN = {nm: pn for (nm, pn, own) in S.MICRO_POS if pn}
RELAY_PN.update({k.upper().replace('_', '-'): v[0] for k, v in S.RELAY_PN.items() if v[0]})       # 'k_efi' -> 'K-EFI'
LID_CHECK = []                                                           # (box, seat, lid text, what the seat map says) where they disagree


def relay_text(box, bank, pos, lid):
    """(plug in, part number, circuit, spare) of a relay seat: the seat map (sot) says which relay sits there, spec its part."""
    r = sot_row(bank, pos)
    if r and r['status'] == 'seated':
        pn = RELAY_PN.get(r['master_id'])
        if lid == 'SPARE':
            LID_CHECK.append((box, pos, lid, r['master_id']))
        return ('relay %s' % r['master_id'], ('TE ' + pn) if pn else 'TBD - no part in spec', r['circuit'], False)
    if lid != 'SPARE':
        LID_CHECK.append((box, pos, lid, 'spare seat'))
    m = re.search(r'spare: ([^;"]+)', (r or {}).get('notes', ''))
    return ('SPARE - leave empty', '-', 'spare seat' + ((' (%s)' % m.group(1)) if m else ''), True)


def fuse_lid_check(box, code, lid, amps, r):
    want = 'SPARE' if not amps else '%g' % amps
    if (not amps and lid not in ('SPARE', 'SP')) or (amps and not re.search(r'(^| )%s ?A?$' % re.escape(want), lid)):
        LID_CHECK.append((box, code, lid, 'spare seat' if not amps else '%g A' % amps))
    if amps and r and not re.search(r'(^|[^0-9.])%s A' % re.escape(want), r['circuit'] + ' ' + r['notes']):
        LID_CHECK.append((box, code, lid, 'seat map row does not state %g A' % amps))


def ami_xy(row, i):
    sgn = -1 if row == 'IN' else 1
    x_in = S.POWER['x_bar'] + sgn * S.AMI_IN_OFF
    x_out = x_in + sgn * S.AMI['c']
    return x_in, x_out, x_out + sgn * S.STRAP['lug'], S.AMI_Y0 + i * S.AMI_PITCH


def atm(amps):
    return 'ATM-%s' % ('7-1/2' if amps == 7.5 else '%g' % amps)


def fuse_circuit(box, code, r):
    """sot circuit + what the fuse's output wire says it feeds (the wire's signal name in the master)."""
    for w in PLAN['wires']:
        for e in w['ends']:
            if e['box'] == box and (e.get('des') == code or e.get('cav') == code) and e.get('sig'):
                return '%s - %s' % (r['circuit'], e['sig'])
    return r['circuit']


def seats(box):
    """[dict(code, shape=('rect', x0, y0, x1, y1) | ('pt', x, y), lid, plug, pn, circuit, spare)] in box coordinates."""
    out = []
    if box == 'LOGIC':
        lid = LIDS['Logic']
        for i, (nm, pn, own) in enumerate(S.MICRO_POS):
            c = CAVS[box]['M%d 87' % (i + 1)]
            plug, pnt, circ, sp = relay_text(box, 'B2', 'M%d' % (i + 1), lid[i])
            out.append(dict(code='M%d' % (i + 1), shape=('rect', c['x'] - S.MICRO['x'] / 2, c['y'] - 1 - S.MICRO['y'] / 2, c['x'] + S.MICRO['x'] / 2, c['y'] - 1 + S.MICRO['y'] / 2),
                            lid=lid[i], plug=plug, pn=pnt, circuit=circ, spare=sp))
        k = len(S.MICRO_POS)
        for col in ('BUS1', 'BUS2'):
            for n, (nm, amps) in enumerate(S.MINI_COLS[col][1], 1):
                code = '%s-%d' % (col, n)
                if code not in CAVS[box]:
                    continue                                              # not a seat in the model
                a, b = CAVS[box][code], CAVS[box][code + ' IN']
                r = sot_row('B2', code)
                fuse_lid_check(box, code, lid[k], amps, r)
                out.append(dict(code=code, shape=('rect', min(a['x'], b['x']) - 1.4, a['y'] - 1.9, max(a['x'], b['x']) + 1.4, a['y'] + 1.9), lid=lid[k],
                                plug=('mini fuse %g A' % amps) if amps else 'SPARE - leave empty', pn=atm(amps) if amps else '-',
                                circuit=(fuse_circuit(box, code, r) if r else 'spare seat') if amps else 'spare seat', spare=not amps))
                k += 1
        for col, x in (('BUS1', sum(REPORT['logic_jumpers']['strips']['BUS1']['x']) / 2), ('BUS2', sum(REPORT['logic_jumpers']['strips']['BUS2']['x']) / 2)):
            out.append(dict(code=col + ' feed', shape=('pt', x, S.FEED[col]['y']), lid=col, plug='feed stud on the %s strip (under the deck)' % col, pn='M5',
                            circuit={'BUS1': 'Bus 1 feed: from POWER box AMI OUT-1 (BUS1 50 A fuse), %d AWG', 'BUS2': 'Bus 2 feed: from the EFI main relay K-EFI terminal 30 (POWER box R2), %d AWG'}[col] % S.FEEDS[col][1], spare=False))
    elif box == 'POWER':
        lid = LIDS['Power']
        for i, (nm, pn, own) in enumerate(S.F7_POS):
            if nm == 'ACPS':
                a, b = CAVS[box]['ACPS'], CAVS[box]['ACPS IN']
                out.append(dict(code='ACPS', shape=('rect', min(a['x'], b['x']) - 1.4, a['y'] - 1.9, max(a['x'], b['x']) + 1.4, a['y'] + 1.9), lid=lid[i],
                                plug='SPARE - leave empty', pn='-', circuit='spare mini fuse seat', spare=True))
                continue
            c = CAVS[box]['R%d 30' % (i + 1)]
            cx = c['x'] + S.F7_PINS['30'][1]
            plug, pnt, circ, sp = relay_text(box, 'B1', 'R%d' % (i + 1), lid[i])
            out.append(dict(code='R%d' % (i + 1), shape=('rect', cx - S.F7['body'] / 2, c['y'] - S.F7['body'] / 2, cx + S.F7['body'] / 2, c['y'] + S.F7['body'] / 2),
                            lid=lid[i], plug=plug, pn=pnt, circuit=circ, spare=sp))
        k = len(S.F7_POS)
        for row in ('IN', 'OUT'):
            for i in range(S.AMI_SLOTS[row]):
                nm, amps = S.AMI_ROWS[row][i]
                x_in, x_out, x_lug, y = ami_xy(row, i)
                r = sot_row('B1', 'AMI %s-%d' % (row, i + 1))
                fuse_lid_check(box, 'AMI %s-%d' % (row, i + 1), lid[k], amps, r)
                out.append(dict(code='AMI %s-%d' % (row, i + 1), shape=('rect', min(x_in, x_out) - 4, y - 6, max(x_in, x_out) + 4, y + 6), lid=lid[k],
                                plug=('AMI bolt-down fuse %d A' % amps) if amps else 'SPARE - leave empty', pn=('AMI-%d' % amps) if amps else '-',
                                circuit=(r['circuit'] if r else 'TBD - no sot row') if amps else 'spare seat', spare=not amps))
                k += 1
        for (y, nm, h) in S.REV7['pos_studs']:
            out.append(dict(code=nm if nm != 'SPARE' else 'SPARE M8', shape=('pt', S.POWER['x_bar'], y), lid=nm if nm != 'SPARE' else 'SPARE M8',
                            plug='M8 stud on the + bar', pn='M8', circuit={'BAT+ IN': 'battery + in (1/0)', 'RADLOK+': 'RADLOK + (alternator / starter, 1/0)'}.get(nm, 'reserved: audio amplifier (no lug yet)'), spare=nm == 'SPARE'))
        for (x, nm, h, g) in S.REV7['neg_studs']:
            out.append(dict(code=nm, shape=('pt', x, S.REV7['neg_bar']['yc']), lid=nm, plug='M8 stud on the NEG bar', pn='M8',
                            circuit='ground, %s' % ('1/0 cable' if g == '1/0' else '3 small rings (ECU ground, K-ON coil, cabin ground)'), spare=False))
    else:
        lid = LIDS['BattRelay']
        out.append(dict(code='BATT +', shape=('pt',) + RB_PT['in'], lid=lid[0], plug='M6 stud on the copper bar', pn='M6', circuit='battery + in (10 AWG from the kill switch)', spare=False))
        r = sot_row('B3', 'FP')
        fuse_lid_check(box, 'FP', lid[1], S.RB['fuse'][1], r)
        out.append(dict(code='FP', shape=('rect', RB_PT['fp_in'][0] - 4, RB_Y - 6, RB_PT['fp'][0] + 4, RB_Y + 6), lid=lid[1], plug='AMI bolt-down fuse %d A' % S.RB['fuse'][1],
                        pn='AMI-%d' % S.RB['fuse'][1], circuit=r['circuit'] if r else 'TBD - no sot row', spare=False))
        r = sot_row('B3', 'K1')
        cx = (RB_PT['3'][0] + RB_PT['5'][0]) / 2
        out.append(dict(code='K1', shape=('rect', cx - S.HCR['body_x'] / 2, S.RB['y_b'], cx + S.HCR['body_x'] / 2, S.RB['y_b'] + S.HCR['body_y']), lid=lid[2],
                        plug='relay %s (TE HCR150), load studs marked 3 and 5' % (r['master_id'] if r else ''), pn='TE 1416010-1', circuit=r['circuit'] if r else 'TBD - no sot row', spare=False))
    return out


# ---------------------------------------------------------------- wires
NEG = {'NEG-GND': 'GND', 'NEG-ID': 'GND ID', 'NEG-IG': 'GND IG', 'NEG-RADLOK': 'RADLOK-', 'NEG-BAT': 'BAT-'}
POS = {'BAT+': 'BAT+ IN', 'ALT/STR': 'RADLOK+'}
XY_CAV = {(c['box'], round(c['x'], 2), round(c['y'], 2)): c['cav'] for c in PLAN['cavities']}


def end_place(box, e):
    """(seat / stud code, pin text, (x, y) or None) of one wire end inside this box."""
    at = e.get('at')
    if at and at.get('kind') == 'splice':
        return ('splice ' + e['id'].upper().replace('SP_', 'SP-'), 'in-box solder splice', (at['x'], at['y']))
    if at:
        cav = XY_CAV.get((box, round(at['x'], 2), round(at['y'], 2)), e['des'] or e['cav'])
        seat, _, pin = cav.partition(' ')
        return (seat, 'fuse input (its own input wire, not the bus strip)' if pin == 'IN' else ('terminal ' + pin) if pin else 'fuse output', (at['x'], at['y']))
    des, cav = e['des'], e['cav']
    if box == 'POWER':
        m = re.match(r'AMI (IN|OUT)-(\d+)', des)
        if m:
            x_in, x_out, x_lug, y = ami_xy(m.group(1), int(m.group(2)) - 1)
            return (des, 'fuse output lug stud (M5)', (x_lug, y))
        for k, nm in NEG.items():
            if cav.startswith(k):
                x = [x_ for (x_, n_, h_, g_) in S.REV7['neg_studs'] if n_ == nm][0]
                return (nm, 'NEG bar stud (M8)' + (', ring %s of 3' % cav[-1] if k == 'NEG-GND' else ''), (x, S.REV7['neg_bar']['yc']))
        if des in POS:
            y = [y_ for (y_, n_, h_) in S.REV7['pos_studs'] if n_ == POS[des]][0]
            return (POS[des], '+ bar stud (M8)', (S.POWER['x_bar'], y))
    if box == 'LOGIC' and des in ('BUS1', 'BUS2'):
        return (des + ' feed', 'strip feed stud (M5)', (sum(REPORT['logic_jumpers']['strips'][des]['x']) / 2, S.FEED[des]['y']))
    if box == 'BATT':
        if e['id'] == 'fb_batt':
            return ('BATT +', 'bar stud (M6)', RB_PT['in']) if cav == 'in' else ('FP', 'fuse output pad stud (M5)', RB_PT['fp'])
        if cav in ('c1', 'c4'):
            return ('K1', 'terminal %s = relay stud %s (M6)' % (des, '3' if cav == 'c1' else '5'), RB_PT['3' if cav == 'c1' else '5'])
        return ('K1', 'terminal %s, coil plug (Superseal 1.5)' % des, None)
    return (des or cav, 'TBD - end not placed by the plan', None)


def box_wires(box):
    """Every wire with an end in this box: number, the ends here, the far end, the in-box path."""
    rows = []
    for w in PLAN['wires']:
        here = [e for e in w['ends'] if e['box'] == box]
        if not here:
            continue
        far = [e for e in w['ends'] if e['box'] != box]
        path = [bp for bp in w.get('box_paths', []) if bp['box'] == box]
        rows.append(dict(w=w, here=[(e,) + end_place(box, e) for e in here], far=far, path=path[0]['pts'] if path else None,
                         lane=path[0].get('lane') if path else None))
    rows.sort(key=lambda r: (nat(r['here'][0][1]), nat(r['here'][0][2]), r['w']['wire']))
    for n, r in enumerate(rows, 1):
        r['n'] = n
    return rows


# ---------------------------------------------------------------- drawing helpers
def box_size(box):
    b = REPORT['boxes_mm'][{'POWER': 'POWER', 'LOGIC': 'LOGIC', 'BATT': 'BATTRELAY'}[box]]
    return b['L'], b['D']


def view(box, below):
    """Box (x, y) -> page (u, v). LOGIC is turned so its long side lies along the page; 'below' mirrors across the page height."""
    if box == 'LOGIC':
        return (lambda x, y: (y, x)) if below else (lambda x, y: (y, -x))
    return (lambda x, y: (x, -y)) if below else (lambda x, y: (x, y))


def header(fig, title, sub):
    fig.patches.append(Rectangle((0, 0.945), 1, 0.055, transform=fig.transFigure, fc='#1c1c1c', ec='none'))
    fig.text(0.012, 0.972, title, color='w', fontsize=16, fontweight='bold', va='center')
    fig.text(0.012, 0.932, sub, color='#222222', fontsize=8.5, va='center')
    fig.text(0.012, 0.012, 'Generated by cad/fusebox/src/wiring_file.py from wiring_plan.json (master wire list + spec.BOX_WIRES), spec.py rev %d and sot/fuse-relay-map.csv. '
             'Model: %s. Never edit by hand: re-run the script.' % (S.REV, MODEL), fontsize=6.5, color='#444444')


def fit(ax, pts, pad=6.0):
    us, vs = [p[0] for p in pts], [p[1] for p in pts]
    u0, u1, v0, v1 = min(us) - pad, max(us) + pad, min(vs) - pad, max(vs) + pad
    bb = ax.get_position()
    w_in, h_in = bb.width * PAGE[0], bb.height * PAGE[1]
    k = min(w_in / (u1 - u0), h_in / (v1 - v0))                 # inches per mm
    cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
    ax.set_xlim(cu - w_in / k / 2, cu + w_in / k / 2)
    ax.set_ylim(cv - h_in / k / 2, cv + h_in / k / 2)
    ax.set_aspect('equal')
    ax.axis('off')
    return k * 72.0                                               # points per mm


def table(fig, rect, cols, widths, rows, fs=7.0, chips=None):
    """Draw rows top-down in rect; returns the number of rows drawn."""
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    w_in, h_in = rect[2] * PAGE[0], rect[3] * PAGE[1]
    lh = fs * 1.30 / 72.0 / h_in
    xs = [sum(widths[:i]) for i in range(len(widths))]
    nch = [max(4, int(w * w_in * 72.0 / (fs * 0.61)) - 1) for w in widths]
    y = 1.0
    ax.add_patch(Rectangle((0, y - 1.7 * lh), 1, 1.7 * lh, fc='#1c1c1c', ec='none'))
    for x, c in zip(xs, cols):
        ax.text(x + 0.004, y - 0.85 * lh, c, fontsize=fs, color='w', fontweight='bold', va='center')
    y -= 1.7 * lh
    done = 0
    for i, row in enumerate(rows):
        cells = [textwrap.wrap(str(c), n) or [''] for c, n in zip(row, nch)]
        h = (max(len(c) for c in cells) + 0.6) * lh
        if y - h < 0:
            break
        ax.add_patch(Rectangle((0, y - h), 1, h, fc='#f1f1f1' if i % 2 == 0 else '#ffffff', ec='#bbbbbb', lw=0.3))
        if chips and chips[i]:
            ax.add_patch(Rectangle((xs[1] - 0.012, y - h + 0.15 * lh), 0.008, h - 0.3 * lh, fc=COL.get(chips[i], '#888888'), ec='#222222', lw=0.4))
        for x, c in zip(xs, cells):
            for j, ln in enumerate(c):
                ax.text(x + 0.004, y - (j + 0.8) * lh, ln, fontsize=fs, va='center', color='#111111')
        y -= h
        done += 1
    return done


def bubble(ax, u, v, n, colour, r, fs):
    dark = colour in ('Red', 'Black')
    ax.add_patch(Circle((u, v), r, fc=COL.get(colour, '#888888'), ec='#000000', lw=0.6, zorder=6))
    ax.text(u, v, str(n), fontsize=fs, ha='center', va='center_baseline', color='w' if dark else 'k', fontweight='bold', zorder=7)


def outline(ax, box, T, below):
    L, D = box_size(box)
    cs = [T(0, 0), T(L, 0), T(L, D), T(0, D), T(0, 0)]
    ax.plot([c[0] for c in cs], [c[1] for c in cs], color='#333333', lw=1.6, zorder=1)
    return cs


def draw_seats(ax, box, T, ss, fs, ghost=False):
    for s in ss:
        if s['shape'][0] == 'rect':
            (u0, v0), (u1, v1) = T(s['shape'][1], s['shape'][2]), T(s['shape'][3], s['shape'][4])
            fc = 'none' if ghost else ('#e3e3e3' if s['spare'] else '#cfe3ff')
            ax.add_patch(Rectangle((min(u0, u1), min(v0, v1)), abs(u1 - u0), abs(v1 - v0), fc=fc, ec='#666666' if ghost else '#1f3d7a', lw=0.5 if ghost else 0.9, ls='--' if ghost else '-', zorder=2))
            if ghost:
                ax.text(min(u0, u1) + 0.4, max(v0, v1) + 0.3, s['code'], fontsize=fs * 0.85, color='#555555', va='bottom', zorder=2)
            else:
                small = min(abs(u1 - u0), abs(v1 - v0)) < 8
                ax.text((u0 + u1) / 2, (v0 + v1) / 2, s['code'] if small else '%s\n%s' % (s['code'], 'SPARE' if s['spare'] else s['lid']), fontsize=fs * (0.8 if small else 1.0),
                        ha='center', va='center', rotation=90 if small and abs(v1 - v0) > abs(u1 - u0) else 0, color='#666666' if s['spare'] else '#0b1f4d', fontweight='bold', zorder=3)
        else:
            u, v = T(s['shape'][1], s['shape'][2])
            ax.add_patch(Circle((u, v), 3.2 if not ghost else 2.6, fc='none' if ghost else ('#e3e3e3' if s['spare'] else '#ffd9a8'), ec='#7a4a00', lw=0.9, ls='--' if ghost else '-', zorder=2))
            ax.text(u, v + (4.2 if not ghost else 3.4), s['code'], fontsize=fs * 0.9, ha='center', va='bottom', color='#7a4a00', fontweight='bold', zorder=3)


def page_seats(pdf, box, ss, pngs):
    slug, name, bank = BOXES[box]
    fig = plt.figure(figsize=PAGE)
    header(fig, '%s rev %d - page 1: SEATS, what plugs in where' % (name, S.REV), 'TOP view, cover off. Blue = fitted, grey = SPARE (leave empty). The second line in a seat is the name etched in the lid.')
    ax = fig.add_axes([0.012, 0.04, 0.50, 0.875])
    T = view(box, False)
    cs = outline(ax, box, T, False)
    fit(ax, cs, pad=10.0)
    draw_seats(ax, box, T, ss, 6.5 if box != 'BATT' else 8.5)
    L, D = box_size(box)
    if box == 'BATT':
        for k in ('3', '5'):
            u, v = T(*RB_PT[k])
            ax.add_patch(Circle((u, v), 3.2, fc='#ffd9a8', ec='#7a4a00', lw=0.9, zorder=4))
            ax.text(u, v - 4.4, 'stud ' + k, fontsize=8, ha='center', va='top', color='#7a4a00', fontweight='bold')
    ex = {'LOGIC': T(L / 2, -9), 'POWER': T(-9, D / 2), 'BATT': T(L / 2, -7)}[box]
    ax.text(ex[0], ex[1], {'LOGIC': 'wire exit side', 'POWER': 'wire exit side', 'BATT': 'feed in at the left end, pump and coil out at the right end'}[box], fontsize=8, ha='center', va='center',
            rotation=90 if box != 'BATT' else 0, color='#aa0000', fontweight='bold')
    rows = [[s['code'], s['lid'], s['plug'], s['pn'], s['circuit']] for s in ss]
    n = table(fig, [0.52, 0.04, 0.47, 0.875], ['Seat', 'Lid', 'Plug in', 'Part no.', 'Circuit'], [0.11, 0.11, 0.30, 0.14, 0.34], rows, fs=7.2 if len(rows) > 24 else 8.5)
    assert n == len(rows), 'seat table does not fit: %d of %d' % (n, len(rows))
    save(pdf, fig, slug, pngs)


def save(pdf, fig, slug, pngs):
    pdf.savefig(fig)
    fn = os.path.join(REV_DIR, 'fusebox-wiring-%s_p%d.png' % (slug, len(pngs) + 1))
    fig.savefig(fn, dpi=DPI)
    pngs.append(fn)
    plt.close(fig)


# ---------------------------------------------------------------- page 2: the wires
def gauge_text(w):
    return '%g AWG' % w['gauge'] if w['unit'] == 'AWG' else '1/0 AWG (%g mm2)' % w['gauge']


def page_wires(pdf, box, ss, rows, pngs):
    slug, name, bank = BOXES[box]
    below = box != 'BATT'
    fig = plt.figure(figsize=PAGE)
    header(fig, '%s rev %d - page 2: WIRES, where each one lands' % (name, S.REV),
           ('Seen from BELOW, belly pan off (the side you wire from; mirror of page 1). ' if below else 'TOP view (the lugs bolt on from the top). Wire lines here are straight, between the real studs. ')
           + 'Line colour = insulation, thickness = gauge, number = wire table.')
    ax = fig.add_axes([0.012, 0.085, 0.976, 0.835])
    T = view(box, below)
    L, D = box_size(box)
    cs = outline(ax, box, T, below)
    r, fs = {'LOGIC': (1.75, 5.6), 'POWER': (2.7, 6.5), 'BATT': (3.4, 9.0)}[box]
    paths = [x for x in rows if x['path']]
    exits = [x for x in paths if min(x['path'][-1][0], x['path'][-1][1]) < -20]      # leaves the box (tails end 30 mm out)
    ext = [T(-48, 0), T(-48, D)] if box == 'POWER' else [T(0, -52), T(L, -52)] if box == 'LOGIC' else [T(-34, 0), T(L + 34, D)]
    k = fit(ax, cs + ext, pad=5.0)
    draw_seats(ax, box, T, ss, fs, ghost=True)
    for c in CAVS.get(box, {}).values():                                           # cut cavities with no wire: spare
        if not c['wires'] and not c['source'].startswith('CAD jumper'):
            u, v = T(c['x'], c['y'])
            ax.add_patch(Rectangle((u - 0.8, v - 0.8), 1.6, 1.6, fc='#dddddd', ec='#888888', lw=0.4, zorder=3))
    if box == 'LOGIC':                                                             # the fuse input jumpers to the bus strips
        for col, st in REPORT['logic_jumpers']['strips'].items():
            (u0, v0), (u1, v1) = T(st['x'][0], st['y'][0]), T(st['x'][1], st['y'][1])
            ax.add_patch(Rectangle((min(u0, u1), min(v0, v1)), abs(u1 - u0), abs(v1 - v0), fc='#e8b27a', ec='#7a4a00', lw=0.6, zorder=2))
            ax.text((u0 + u1) / 2, (v0 + v1) / 2, '%s copper strip' % col, fontsize=5.5, ha='center', va='center', color='#4a2c00', zorder=3)
        for c in CAVS[box].values():
            if c['source'].startswith('CAD jumper'):
                col = c['cav'].split('-')[0]
                xs = sum(REPORT['logic_jumpers']['strips'][col]['x']) / 2
                (u0, v0), (u1, v1) = T(c['x'], c['y']), T(xs, c['y'])
                ax.plot([u0, u1], [v0, v1], color=COL['Red'], lw=1.3, zorder=4, solid_capstyle='round')
                ax.add_patch(Rectangle((u0 - 0.9, v0 - 0.9), 1.8, 1.8, fc='#ffffff', ec=COL['Red'], lw=0.8, zorder=5))
                ax.text(u0, v0, 'J', fontsize=4.2, ha='center', va='center_baseline', color=COL['Red'], fontweight='bold', zorder=6)
    for x in paths:                                                                # the wires, on their in-box paths
        pts = [T(p[0], p[1]) for p in x['path']]
        lw = 0.9 + 0.38 * x['w']['od']
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color='#000000', lw=lw + 0.9, zorder=4, solid_capstyle='round', solid_joinstyle='round')
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=COL.get(x['w']['colour'], '#888888'), lw=lw, zorder=4.5, solid_capstyle='round', solid_joinstyle='round')
    for sp in PLAN['splices']:
        if sp['box'] == box:
            (u0, v0), (u1, v1) = T(*sp['p0'][:2]), T(*sp['p1'][:2])
            ax.plot([u0, u1], [v0, v1], color='#3a3a3a', lw=5.0, zorder=5, solid_capstyle='round')
            ax.annotate('in-box solder splice %s' % sp['id'].upper().replace('SP_', 'SP-'), ((u0 + u1) / 2, (v0 + v1) / 2), xytext=((u0 + u1) / 2 + 6, max(c[1] for c in cs) + 5.5 + (4 if 'acc' in sp['id'] else 0)),
                        fontsize=7, color='#000000', fontweight='bold', arrowprops=dict(arrowstyle='-', color='#000000', lw=0.7), zorder=8)
    if box == 'BATT':                                                              # straight lines between the real studs
        cx = (RB_PT['3'][0] + RB_PT['5'][0]) / 2 + S.HCR['body_x'] / 2
        coil = 0
        for x in rows:
            ps = [e[3] for e in x['here']]
            if len(ps) == 1 and ps[0] is None:
                p = (cx, S.RB['y_b'] + 12 + 9 * coil)
                coil += 1
                x['here'][0] = x['here'][0][:3] + (p,)
                seg = [p, (L + 30, p[1])]
            elif len(ps) == 2:
                seg = ps
            else:
                seg = [(-30, ps[0][1]), ps[0]] if ps[0][0] < L / 2 else [ps[0], (L + 30, ps[0][1])]
            x['stub'] = seg[-1] if seg[-1][0] > L else seg[0] if seg[0][0] < 0 else None
            pts = [T(*p) for p in seg]
            lw = 0.9 + 0.38 * x['w']['od']
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color='#000000', lw=lw + 0.9, zorder=4, solid_capstyle='round')
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=COL.get(x['w']['colour'], '#888888'), lw=lw, zorder=4.5, solid_capstyle='round')
            if x['stub']:
                u, v = T(*x['stub'])
                bubble(ax, u, v, x['n'], x['w']['colour'], r, fs)
        for kk in ('3', '5'):
            u, v = T(*RB_PT[kk])
            ax.text(u, v - 5.5, 'relay stud ' + kk, fontsize=8, ha='center', va='top', color='#7a4a00', fontweight='bold')
        u, v = T(cx - 2.0, S.RB['y_b'] + 27)
        ax.text(u, v, 'coil plug on the relay\n(Superseal 1.5, 2 pins;\nplace on the relay: see the\nrenders, not to scale here)', fontsize=7.5, ha='right', va='bottom', color='#333333')
    for x in rows:                                                                 # both ends here but no path in the plan: show the connection
        ps = [e[3] for e in x['here'] if e[3] is not None]
        if below and not x['path'] and len(ps) == 2:
            pts = [T(*q) for q in ps]
            ax.plot([q[0] for q in pts], [q[1] for q in pts], color=COL.get(x['w']['colour'], '#888888'), lw=1.6, ls=(0, (4, 2)), zorder=4)
    used = {}
    for x in rows:                                                                 # a numbered dot on every terminal
        for (e, seat, pin, pos) in x['here']:
            if pos is None or seat.startswith('splice'):
                continue
            i = used.get(pos, 0)
            used[pos] = i + 1
            u, v = T(*pos)
            bubble(ax, u + (0 if box != 'POWER' else 0), v + i * 2.15 * r, x['n'], x['w']['colour'], r, fs)
    if exits:                                                                      # the same numbers again where the wires leave the box
        ends = sorted(((T(x['path'][-1][0], x['path'][-1][1]), x) for x in exits), key=lambda t: t[0][1])
        ncol = 3
        step = max(2.35 * r / ncol, (ends[-1][0][1] - ends[0][0][1]) / max(1, len(ends) - 1))
        mid = (ends[-1][0][1] + ends[0][0][1]) / 2
        for i, ((u, v), x) in enumerate(ends):
            ur, vr = u - 5.0 - 2.5 * r * (i % ncol), mid + (i - (len(ends) - 1) / 2) * step
            ax.plot([u, ur], [v, vr], color='#555555', lw=0.4, zorder=5)
            bubble(ax, ur, vr, x['n'], x['w']['colour'], r, fs)
        for exi in PLAN['exits']:
            if exi['box'] == box and box == 'LOGIC':
                u, v = T(*((exi['lane'], -30) if box == 'LOGIC' else (-30, exi['lane'])))
                ax.text(u + 27.0, v, 'exit notch\n%d wire%s' % (exi['wires'], '' if exi['wires'] == 1 else 's'), fontsize=5.5, color='#aa0000', rotation=90, ha='center', va='center', zorder=8,
                        bbox=dict(fc='#ffffff', ec='none', pad=0.6, alpha=0.85))
    notes = ['Dashed = seat outline (seat code beside it). Grey square = cut cavity with no wire (SPARE).']
    if box == 'LOGIC':
        notes.append('J = fuse input jumper: a short red Tefzel wire from the fuse input terminal to the copper strip (M4 ring lug); see the wire table.')
        notes.append('A number on BUS1 feed / BUS2 feed = the box-to-box cable from the POWER box lands on that strip stud.')
    if box == 'POWER':
        notes.append('Dashed coloured line = a cable inside the box between a fuse lug and its relay: the connection only, its real bends are in the wired renders.')
        notes.append('A number on a stud with no line = that cable leaves its stud straight out of the box (heavy cables and AMI fuse outputs); routes: fusebox_power_wired_*.png.')
    for i, t in enumerate(notes):
        fig.text(0.012, 0.045 + 0.016 * (len(notes) - 1 - i), t, fontsize=7.5, color='#222222')
    save(pdf, fig, slug, pngs)


# ---------------------------------------------------------------- page 3+: the wire table
def far_text(box, e):
    if e['box'] and e['box'] != box:
        seat, pin, pos = end_place(e['box'], e)
        return '%s: %s, %s' % (BOXES[e['box']][1], seat, pin)
    return ', '.join(t for t in (e.get('name') or e['id'], ('pin ' + e['cav']) if e['cav'] else '', e.get('sig') or '') if t)


def tool_cell(part, far=False):
    what, tool = term_text(part, far)
    return '%s. Crimp tool: %s' % (what, tool.split(' (')[0].split(';')[0])


def table_rows(box, ss, rows):
    by = {s['code']: s for s in ss}
    out, chips = [], []
    for x in rows:
        e, seat, pin, pos = x['here'][0]
        s = by.get(seat)
        here = '%s, %s%s' % (seat, pin, (' - %s' % s['circuit']) if s and not seat.startswith(('AMI', 'BUS', 'FP', 'BATT')) or (s and 'feed' in seat) else '')
        if len(x['here']) == 2:
            e2, seat2, pin2, pos2 = x['here'][1]
            other, part2 = 'same box: %s, %s' % (seat2, pin2), e2['part']
            if seat2.startswith('splice'):
                t2 = SPLICE_TOOL
            else:
                t2 = tool_cell(part2)
        else:
            f = x['far'][0]
            other = far_text(box, f)
            t2 = SPLICE_TOOL if (f.get('at') or {}).get('kind') == 'splice' else tool_cell(f['part'], far=True)
        t1 = SPLICE_TOOL if seat.startswith('splice') else tool_cell(e['part'])
        out.append([x['n'], '%s %s' % (gauge_text(x['w']), x['w']['colour']), here, t1, other, t2, x['w']['wire']])
        chips.append(x['w']['colour'])
    if box == 'LOGIC':
        lj = REPORT['logic_jumpers']
        ring = {nm: pn for pn, nms in lj['ring_lugs'].items() for nm in nms}
        for c in sorted(CAVS[box].values(), key=lambda c: nat(c['cav'])):
            if c['source'].startswith('CAD jumper'):
                col, n = c['cav'].split(' ')[0].split('-')
                nm = S.MINI_COLS[col][1][int(n) - 1][0]
                out.append(['J', '%d AWG Red (Tefzel), about 60 mm' % lj['gauges'][nm], '%s-%s, fuse input' % (col, n), tool_cell(c['part']),
                            'same box: %s copper strip, M4 stud beside the fuse' % col, tool_cell(ring[nm]), 'box model (input jumper)'])
                chips.append('Red')
    return out, chips


def page_tables(pdf, box, ss, rows, pngs):
    slug, name, bank = BOXES[box]
    trs, chips = table_rows(box, ss, rows)
    cols = ['No.', 'Wire', 'End in this box', 'Terminal there + crimp tool', 'Other end', 'Terminal there + crimp tool', 'Wire list ID']
    widths = [0.035, 0.085, 0.19, 0.235, 0.20, 0.175, 0.08]
    i, page = 0, 3
    while i < len(trs):
        fig = plt.figure(figsize=PAGE)
        header(fig, '%s rev %d - page %d: WIRE TABLE' % (name, S.REV, page), 'No. = the number on page 2. J = fuse input jumper. One crimp per wire end; SPARE seats get no wire.')
        n = table(fig, [0.012, 0.04, 0.976, 0.875], cols, widths, trs[i:], fs=7.0, chips=chips[i:])
        assert n > 0
        i += n
        last = i >= len(trs)
        save(pdf, fig, slug, pngs)
        page += 1
    used = sorted({pn_key(e['part']) for x in rows for (e, s_, p_, q_) in x['here'] if e['part']} | ({'320554', '53941-1'} if box == 'LOGIC' else set()))
    fig = plt.figure(figsize=PAGE)
    header(fig, '%s rev %d - page %d: TERMINALS AND CRIMP TOOLS' % (name, S.REV, page), 'TBD = no maker tooling document read yet; never crimp with a guessed die.')
    tr = [[k, TERMINAL[k][0] if k in TERMINAL else 'TBD - not in the terminal table', TERMINAL[k][1] if k in TERMINAL else 'TBD'] for k in used]
    tr.append(['ATUM-6/2', 'TE adhesive-lined heat shrink over each in-box solder splice', SPLICE_TOOL])
    n = table(fig, [0.012, 0.04, 0.976, 0.875], ['Terminal', 'What it is', 'Crimp tool (source)'], [0.10, 0.30, 0.60], tr, fs=9.0)
    assert n == len(tr)
    save(pdf, fig, slug, pngs)


def main():
    for box in ('POWER', 'LOGIC', 'BATT'):
        slug = BOXES[box][0]
        ss, rows, pngs = seats(box), box_wires(box), []
        for f in os.listdir(REV_DIR):
            if re.match(r'fusebox-wiring-%s_p\d+\.png$' % slug, f):
                os.remove(os.path.join(REV_DIR, f))
        with PdfPages(os.path.join(REV_DIR, 'fusebox-wiring-%s.pdf' % slug), metadata={'CreationDate': None, 'ModDate': None, 'Title': '%s rev %d wiring' % (BOXES[box][1], S.REV)}) as pdf:
            page_seats(pdf, box, ss, pngs)
            page_wires(pdf, box, ss, rows, pngs)
            page_tables(pdf, box, ss, rows, pngs)
        print('%s: %d seats (%d spare), %d wires, %d pages -> fusebox-wiring-%s.pdf' % (box, len(ss), sum(s['spare'] for s in ss), len(rows), len(pngs), slug))


def lid_report():
    print('lid labels against the seat map and spec rev %d: %d differ' % (S.REV, len(LID_CHECK)))
    for row in LID_CHECK:
        print('  %s %s: lid "%s", seat map / spec: %s' % row)
    return len(LID_CHECK)


if __name__ == '__main__':
    main()
    sys.exit(1 if lid_report() else 0)
