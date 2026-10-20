"""Sheets 2..: one simple diagram for each OEM junction block / relay-block position / plug where we splice into the factory loom.

Per box: the OEM plugs we touch, ONLY the cavities we use (everything else is untouched factory wiring), the factory lead of each
cavity with its OEM wire colour and EWD page, the splice (ID, method, side) and OUR wire from the splice to its far end (wire id,
gauge, colour, R156 far-end text). Data: docs/harness/interfaces.json flyingLeads (the SoT of every splice into the factory loom);
wire facts from the looms (cross-checked, never a source of truth).
"""
import re
import wd_data as D
from wd_svg import Svg, INK, est_w, wrap

W = 420.0
ROW = 16.5
X_BOX0, X_BOX1 = 10.0, 128.0
X_CELL0, X_CELL1 = 15.0, 123.0
X_DOT = 168.0
X_STUB = 262.0          # our wire ends here, the far-end text starts
OEM = {'B': '#1b1b1b', 'W': '#f4f4f4', 'R': '#c62828', 'G': '#2e9d4f', 'L': '#2f6fd6', 'Y': '#f2c200', 'O': '#ee7a00', 'V': '#7b3fa0',
       'BR': '#8b5a2b', 'GR': '#8a8a8a', 'P': '#e58fb4', 'LG': '#9fd36b', 'SB': '#6ec1e4'}

SHEETS = [
    ('jb1', 'J/B No.1 - left kick panel', 'OEM junction block, KEPT (DECISIONS R12 / R61). We splice into the factory leads of three plugs: 1I (always-hot), 1H, 1F. '
            'Cabin side of the lead, left kick panel (EWD 1993 p.18-19, p.46, p.62).'),
    ('ie1', 'IE1 cowl plug - left kick panel', 'Engine-room <-> cowl plug at the left kick panel. The engine-room main is REMOVED (R12); we splice into the '
            'factory cowl-side lead of each pin we use (EWD 1993 p.31, p.116-117, p.130, p.148, p.185).'),
    ('rb2', 'Old R/B No.2 position - left kick panel', 'Relay block REMOVED (R12, R58). Its factory leads stay in the loom; we splice into the '
            'cowl-side lead where the relay pin was (EWD 1993 p.137-138, p.170).'),
    ('rb4', 'Old R/B No.4 position - right kick panel', 'Relay block REMOVED (R12). Its factory leads stay in the loom; we splice into the lead where the '
            'relay pin was (EWD 1993 p.66, p.215).'),
    ('jb3', 'J/B No.3 - behind the combination meter', 'OEM cowl junction block, KEPT. One splice: the GAUGE 15 A ignition lead (Mitchell 1993 Fig. 16, '
            'grid 63; 1992 p.132).'),
    ('ig2', 'IG2 plug - under the ECU, cowl side', 'Cabin plug under the ECU; the engine-side wire is removed. We splice into the cowl-side leads (EWD 1993 p.74-75).'),
    ('gnd', 'Kick-panel body grounds ID and IG', 'OEM body ground points kept (EWD ground index p.169 / p.171; docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md 5.2 / 5.3). '
            'A ring terminal goes on each factory ground bolt.'),
]


def sheet_of(lead):
    c, pin = lead['ewd']['connector'], str(lead['ewd'].get('pin'))
    if c.startswith('IE1'):
        return 'ie1', 'IE1', 'pin %s' % pin
    if c.startswith('IG2'):
        return 'ig2', 'IG2', 'pin %s' % pin
    if c.startswith('R/B2'):
        return 'rb2', 'old R/B No.2 (left kick)', pin
    if c.startswith('R/B4') or c.startswith('R/B No.4'):
        return 'rb4', 'old R/B No.4 (right kick)', ('starter relay socket lead, pin %s' % pin) if c.startswith('R/B No.4') else pin
    if c.startswith('J/B3'):
        return 'jb3', 'J/B No.3 plug 3B', 'pin %s' % pin.replace('3B-', '')
    m = re.match(r'J/B( No\.)?1 ?(1[A-Z])?', c)
    if m:
        plug = m.group(2)
        mm = re.match(r'(1[A-Z])-(\d+)', pin)
        if mm:
            return 'jb1', 'J/B No.1 plug ' + mm.group(1), 'pin ' + mm.group(2)
        return 'jb1', 'J/B No.1 plug ' + plug, 'pin %s' % pin
    return None, None, None


def oem_chip(sv, x, y, code, w=9.0, h=3.4):
    parts = [p for p in re.split(r'[-\s(]', code or '') if p]
    base = parts[0] if parts else '?'
    stripe = parts[1] if len(parts) > 1 and parts[1] in OEM else None
    sv.rect(x, y, w, h, fill=OEM.get(base, '#ccc'), stroke=INK, sw=0.25)
    if stripe:
        sv.rect(x + w * 0.42, y, w * 0.16, h, fill=OEM.get(stripe, '#ccc'), stroke='none', sw=0)
        sv.rect(x, y, w, h, fill='none', stroke=INK, sw=0.25)


def collect(ents, wires):
    """rows[sheet] = list of dict(plug, pin, lead, wires=[...])"""
    rows = {k: [] for k, *_ in SHEETS}
    other = []
    by_term = {}
    for w in wires:
        for e in w['ends']:
            by_term.setdefault((w['file'], e['ent']), []).append((w, e))
    for lead in D.oem_leads():
        key, plug, pin = sheet_of(lead)
        if not key:
            other.append(lead)
            continue
        term = (lead['harness'], lead['terminal'])
        found = [(w, e) for (w, e) in by_term.get(term, [])]
        out = []
        for w, e in found:
            far = next((x for x in w['ends'] if not (x['ent'] == e['ent'] and x['handle'] == e['handle'])), None)
            out.append(dict(w=w, far=far))
        rows[key].append(dict(plug=plug, pin=pin, lead=lead, term=ents.get(term), wires=out))
    for k in rows:
        rows[k].sort(key=lambda r: (r['plug'], int((re.findall(r'\d+', r['pin']) or ['0'])[-1])))
    # kick-panel body grounds (harness terminals; EWD point per the redistribution doc)
    for tid, plug, pin, page in (('t_gnd_id', 'Ground point ID (left kick panel)', 'body ground bolt', 'EWD p.169'),
                                 ('t_gnd_ig', 'Ground point IG (right kick panel)', 'body ground bolt', 'EWD p.171')):
        term = ('EngineRoom-C', tid)
        found = [(w, e) for (w, e) in by_term.get(term, [])]
        out = [dict(w=w, far=next(x for x in w['ends'] if not (x['ent'] == e['ent'] and x['handle'] == e['handle']))) for w, e in found]
        lead = dict(id=tid.upper(), ewd=dict(page=page, color='B (factory ground)', function='body ground, kept (OEM ring)',
                                              method='ring terminal on the factory ground bolt'), harness='EngineRoom-C', terminal=tid)
        rows['gnd'].append(dict(plug=plug, pin=pin, lead=lead, term=ents.get(term), wires=out))
    return rows, other


def build_sheet(key, title, intro, rows):
    n_w = sum(max(1, len(r['wires'])) for r in rows)
    plugs = []
    for r in rows:
        if r['plug'] not in plugs:
            plugs.append(r['plug'])
    H = 34 + n_w * ROW + len(plugs) * 13 + 24
    sv = Svg(W, max(H, 120), 'ST185 OEM junction - ' + title)
    sv.text(X_BOX0, 12, title.upper(), 4.6, bold=True)
    for i, t in enumerate(wrap(intro, W - 2 * X_BOX0, 2.3, max_lines=3)):
        sv.text(X_BOX0, 19 + i * 3.6, t, 2.3, fill='#222')
    y = 50.0
    top = y - 4
    sv.rect(X_BOX0, top, X_BOX1 - X_BOX0, 0, layer='back')
    y_start = y
    plug_blocks = []
    cur = None
    for r in rows:
        if r['plug'] != cur:
            cur = r['plug']
            sv.rect(X_CELL0, y - 1.0, X_CELL1 - X_CELL0, 7.0, fill='#dfe6f1', stroke=INK, sw=0.35)
            sv.text(X_CELL0 + 2, y + 3.8, cur, 2.7, bold=True)
            y += 9.0
        lead = r['lead']
        ewd = lead['ewd']
        col = (ewd.get('color') or '').split(' ')[0]
        wl = r['wires'] or [None]
        h = max(1, len(wl)) * ROW
        # cavity cell
        sv.rect(X_CELL0, y - 2.5, X_CELL1 - X_CELL0, h - 1.0, fill='#ffffff', stroke=INK, sw=0.3)
        sv.text(X_CELL0 + 2, y + 1.6, '%s' % r['pin'], 2.5, bold=True)
        oem_chip(sv, X_CELL0 + 24, y - 0.9, col)
        sv.text(X_CELL0 + 35, y + 1.6, col if col else 'OEM colour TBD', 2.3, bold=True)
        sv.text(X_CELL1 - 2, y + 1.6, ('EWD ' + ewd['page'].split(' (')[0].replace('1993 TIS EWD', '1993').replace('Mitchell 1993 overall wiring Fig. 16 (grid 63; 1992 p.132)', 'Mitchell Fig. 16'))[:34], 1.9, 'end', fill='#334')
        for i, t in enumerate(wrap(ewd.get('function', ''), X_CELL1 - X_CELL0 - 4, 1.9, max_lines=3)):
            sv.text(X_CELL0 + 2, y + 5.3 + i * 2.5, t, 1.9, fill='#222')
        # factory lead + splice + our wire(s)
        yl = y + 1.0
        for k, ww in enumerate(wl):
            ywire = yl + k * ROW
            sv.line(X_CELL1, yl, X_DOT, yl, stroke=OEM.get(col.split('-')[0], '#333'), sw=1.1) if k == 0 else None
            if k == 0:
                sv.line(X_CELL1, yl, X_DOT, yl, stroke='#111', sw=0.25)
                sv.text((X_CELL1 + X_DOT) / 2, yl - 1.4, 'factory lead %s' % col, 1.7, 'middle', fill='#333')
                sv.circle(X_DOT, yl, 1.5, fill=INK, layer='over')
                sv.text(X_DOT + 3, yl - 3.2, lead['id'], 2.3, bold=True)
                meth = (ewd.get('method') or '').strip()
                for i, t in enumerate(wrap(meth, X_STUB - X_DOT - 4, 1.9, max_lines=2)):
                    sv.text(X_DOT + 3, yl + 4.0 + i * 2.5, t, 1.9, fill='#222')
            if ww is None:
                sv.text(X_DOT + 3, yl + 0.5, 'NO WIRE IN THE LOOMS (see MISMATCHES.md)', 2.0, bold=True, fill='#b00020')
                continue
            w = ww['w']
            if k > 0:
                sv.wire([(X_DOT, yl), (X_DOT, ywire), (X_STUB, ywire)], w['colour'])
            else:
                sv.wire([(X_DOT, yl), (X_STUB, yl)], w['colour'])
            sv.text((X_DOT + X_STUB) / 2 + 12, ywire - 1.6, '%s | %s | %s' % (w['id'], D.gauge_text(w), D.colour_text(w)), 2.1, 'middle', bold=True)
            far = ww['far']
            ft = D.far_text(far) if far else '?'
            for i, t in enumerate(wrap('-> ' + D.short(ft, 220), W - X_STUB - 6, 2.1, max_lines=2)):
                sv.text(X_STUB + 3, ywire - 0.6 + i * 2.7 - 1.0, t, 2.1)
        y += h
    y_end = y
    sv.rect(X_BOX0, y_start - 18, X_BOX1 - X_BOX0, y_end - y_start + 18 + 4, fill='#f4f7fb', stroke=INK, sw=0.7, rx=2.0, layer='back')
    sv.text(X_BOX0 + 2, y_start - 12.0, 'OEM box: only the plugs / cavities we splice are drawn', 2.0, bold=True)
    sv.h = y_end + 14
    sv.text(X_BOX0, sv.h - 8, 'Generated by docs/build/wiring-diagrams/build_wiring_diagrams.py from docs/harness/interfaces.json (flyingLeads); wire facts from the looms. Every cavity not shown stays factory.', 1.9, fill='#555')
    sv.text(X_BOX0, sv.h - 4, 'Splice dot = our wire butt-spliced into the factory lead. Wire label: wire id | gauge | insulation colour (ident bands). Far end: DECISIONS R156 form.', 1.9, fill='#555')
    return sv


def build(ents, wires):
    rows, other = collect(ents, wires)
    out = {}
    for key, title, intro in SHEETS:
        if rows[key]:
            out[key] = build_sheet(key, title, intro, rows[key])
    return out, rows, other
