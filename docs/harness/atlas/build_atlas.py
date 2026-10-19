#!/usr/bin/env python
"""ST185 connector atlas: 11x17 (tabloid) landscape PDF generated from the wire lists.

Every connector of all harnesses (cavity circles, number inside, short signal under it, fill = function)
plus every OEM junction box / plug / ground point we tap (outline, factory colour, what our wire does, EWD page).
Nothing is placed by hand: everything comes from docs/harness/wirelist/*-wirelist.csv and *-connectors.csv.

  python docs/harness/atlas/build_atlas.py           write ST185-connector-atlas.pdf (+ .inputs.txt)
  python docs/harness/atlas/build_atlas.py --check   fail if the PDF is stale against the wire lists (no PyMuPDF needed)

Needs PyMuPDF to write (pip install pymupdf). Only the DRB102 is drawn as its real maker insert face (TE drawing view);
the part library has no cavity positions for the other connectors, so they are numbered grids with the true cavity
count (pin order, not the maker face). The wire lists are the only truth.
"""
import csv
import glob
import hashlib
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WL = os.path.normpath(os.path.join(HERE, '..', 'wirelist'))
OUT = os.path.join(HERE, 'ST185-connector-atlas.pdf')
SIDE = os.path.join(HERE, 'ST185-connector-atlas.inputs.txt')

PW, PH = 1224.0, 792.0          # 17 x 11 in at 72 pt
MX, TOP, BOT = 18.0, 40.0, 50.0  # margins, header band, footer (legend) band
GAP = 8.0

# fill colours by function (same palette as the approved DRB102 face map)
PAL = [('spare', 'Spare', '#ffffff'), ('can', 'CAN', '#2e7d32'), ('shield', 'Shield drain', '#9e9e9e'),
       ('p12', '+12 V power', '#c62828'), ('sig', 'Sensor signal', '#7cb342'), ('out', 'Output / actuator', '#00838f'),
       ('gnd', 'Ground / sensor return', '#424242'), ('sup', 'Sensor supply +5/+8 V', '#ef6c00'),
       ('coil', 'Coil trigger', '#6a1b9a'), ('inj', 'Injector drive', '#1565c0'), ('other', 'Other / lighting / misc', '#b0bec5')]
FILL = {k: c for k, _, c in PAL}
DARK = {'can', 'p12', 'out', 'gnd', 'coil', 'inj', 'sup'}
OEMC = {'B': '#1b1b1b', 'W': '#f4f4f4', 'R': '#c62828', 'G': '#2e9d4f', 'L': '#2f6fd6', 'Y': '#f2c200', 'O': '#ee7a00',
        'V': '#7b3fa0', 'BR': '#8b5a2b', 'GR': '#8a8a8a', 'P': '#e58fb4', 'LG': '#9fd36b', 'SB': '#6ec1e4'}
INK = '#14213d'

# DRB102 insert face, 12 columns (TE drawing view); sizes: 12 on 1-8 / 95-102, 8 on 48 49 54 55, 4 on 43 60, rest 16
COLS = [list(range(102, 94, -1)), list(range(94, 82, -1)), list(range(82, 70, -1)), [70, 69, 68, 67, None, 66, 65, 64, 63],
        [62, 61, 60, 59, 58], [57, 56, 55, 54, 53, 52], [51, 50, 49, 48, 47, 46], [45, 44, 43, 42, 41],
        [40, 39, 38, 37, None, 36, 35, 34, 33], list(range(32, 20, -1)), list(range(20, 8, -1)), list(range(8, 0, -1))]
SIZE = {**{i: 12 for i in list(range(1, 9)) + list(range(95, 103))}, 48: 8, 49: 8, 54: 8, 55: 8, 43: 4, 60: 4}
RAD = {4: 15.0, 8: 12.5, 12: 10.5, 16: 9.0}


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rd(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- input hash (stale check)
def input_files():
    fs = []
    for pat in ('*-wirelist.csv', '*-connectors.csv', '*-mates.csv'):
        fs += glob.glob(os.path.join(WL, pat))
    fs.append(os.path.abspath(__file__))
    return sorted(fs)


def inputs_hash():
    h = hashlib.sha256()
    for f in input_files():
        h.update(os.path.basename(f).encode())
        with open(f, 'rb') as fh:
            h.update(fh.read().replace(b'\r\n', b'\n'))
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- data
def fn_of(desc):
    d = (desc or '').lower()
    if not d.strip() or d.startswith('spare'):
        return 'spare'
    if 'shield' in d or 'drain' in d:
        return 'shield'
    if re.search(r'\bcan\b|canh|canl', d):
        return 'can'
    if 'injector' in d:
        return 'inj'
    if 'coil' in d and ('trigger' in d or 'igt' in d):
        return 'coil'
    if re.search(r'\bgnd\b|ground|return|\bneg\b|earth', d):
        return 'gnd'
    if re.search(r'\+\s?(5|8)\s?v|sensor supply|5 v|8 v', d):
        return 'sup'
    if re.search(r'\+\s?12|12 v|b\+|battery|feed|ign|ig2|sw12|\bam[12]\b|power|fuse|\bacc\b|\+v', d):
        return 'p12'
    if re.search(r'relay|coil|motor|pump|solenoid|drive|horn|siren|fan|output|lamp|light|\(-\)|kill|enable|actuator|led|cancel', d):
        return 'out'
    if re.search(r'signal|sensor|temp|pressure|speed|spd|input|switch|level|sense|crank|cam|map|knock', d):
        return 'sig'
    return 'other'


def load():
    conns, order = {}, []
    for f in sorted(glob.glob(os.path.join(WL, '*-connectors.csv'))):
        for r in rd(f):
            if r['conn_id'] in conns:
                raise SystemExit('duplicate conn_id %s' % r['conn_id'])
            r['pins'] = {}
            r['n'] = int(r['cavities'] or 0)
            conns[r['conn_id']] = r
            order.append(r['conn_id'])
    for cid in order:   # a bussed cap has no wire rows of its own: it shows its plug's cavities
        c = conns[cid]
        m = conns.get(c['mates_with'].split(' ')[0])
        if m and 'cap' in c['name'].lower() and not c['pins']:
            c['cap_of'] = None
            c['_mate'] = m
    taps, grounds = [], {}
    for f in sorted(glob.glob(os.path.join(WL, '*-wirelist.csv'))):
        for r in rd(f):
            for s, o in (('from', 'to'), ('to', 'from')):
                t, cid, pin = r[s + '_type'], r[s + '_conn'], r[s + '_pin'].strip()
                desc = r[s + '_desc'] or r['net_name']
                if t == 'connector' and cid in conns:
                    conns[cid]['pins'].setdefault(pin, [])
                    if desc not in conns[cid]['pins'][pin]:
                        conns[cid]['pins'][pin].append(desc)
                if t == 'OEM':
                    taps.append(dict(r, side=s, oside=o))
                if t == 'terminal' and re.search(r'ground (point|stud|bolt)|EWD ground', r[s + '_conn_name'], re.I) \
                        and 'POWER box' not in r[s + '_conn_name']:
                    grounds.setdefault(r[s + '_conn_name'], []).append(dict(r, side=s, oside=o))
    for c in conns.values():
        if c.get('_mate'):
            c['cap_of'] = c['_mate']['pins']
    return conns, order, taps, grounds


def far_end(r, o):
    t = r[o + '_type']
    nm = r[o + '_conn_name'] or r[o + '_conn']
    if t == 'connector':
        return '%s pin %s' % (nm, r[o + '_pin'])
    return nm


def cav_list(c):
    """Cavity labels of a connector: a true numbered range when the pins say so, else the pins in use."""
    used = list(c['pins'])
    n = c['n']
    nums = [p for p in used if p.isdigit()]
    if used and len(nums) == len(used) and max(map(int, nums)) <= n:
        return [str(i) for i in range(1, n + 1)]
    m = [re.fullmatch(r'([A-Za-z]+)(\d+)', p) for p in used]
    if used and all(m) and len({x.group(1) for x in m}) == 1 and max(int(x.group(2)) for x in m) <= n:
        return ['%s%d' % (m[0].group(1), i) for i in range(1, n + 1)]
    if not used and n:
        return [str(i) for i in range(1, n + 1)]
    def key(p):
        return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', p)]
    return sorted(used, key=key) if all(p.isdigit() for p in used) else used


# ---------------------------------------------------------------- drawing helpers
class Pg:
    def __init__(self, doc):
        self.p = doc.new_page(width=PW, height=PH)

    def text(self, x, y, s, fs=6.0, bold=False, col=INK, anchor='l'):
        import fitz
        fnt = 'hebo' if bold else 'helv'
        w = fitz.get_text_length(s, fontname=fnt, fontsize=fs)
        if anchor == 'c':
            x -= w / 2
        elif anchor == 'r':
            x -= w
        self.p.insert_text((x, y), s, fontsize=fs, fontname=fnt, color=rgb(col) if isinstance(col, str) else col)
        return w

    def rect(self, x, y, w, h, fill=None, line=INK, lw=0.5, r=None):
        import fitz
        self.p.draw_rect(fitz.Rect(x, y, x + w, y + h), color=rgb(line) if line else None,
                         fill=rgb(fill) if fill else None, width=lw, radius=r)

    def circle(self, x, y, r, fill, lw=0.7):
        import fitz
        self.p.draw_circle(fitz.Point(x, y), r, color=rgb(INK), fill=rgb(fill), width=lw)

    def line(self, x1, y1, x2, y2, col=INK, lw=0.5, dash=None):
        import fitz
        self.p.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2), color=rgb(col), width=lw, dashes=dash)


def tw(s, fs, bold=False):
    import fitz
    return fitz.get_text_length(s, fontname='hebo' if bold else 'helv', fontsize=fs)


def wrap(s, width, fs, maxl=3, bold=False):
    words, lines, cur = (s or '').split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if tw(t, fs, bold) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > maxl:
        lines = lines[:maxl]
        l = lines[-1]
        while tw(l + '...', fs, bold) > width and len(l) > 1:
            l = l[:-1]
        lines[-1] = l.rstrip() + '...'
    return lines


def cavity(pg, cx, cy, label, fn, r=9.0, desc='', pitch=54.0, nlines=3):
    fill = FILL[fn]
    short = len(label) <= 3
    if short:
        pg.circle(cx, cy, r, fill)
        pg.text(cx, cy + 2.6, label, 7.0, True, '#ffffff' if fn in DARK else '#000000', 'c')
        ytxt = cy + r + 7.0
    else:
        w = pitch - 6
        fs = 6.2
        while tw(label, fs, True) > w - 4 and fs > 4.2:
            fs -= 0.2
        pg.rect(cx - w / 2, cy - 7, w, 14, fill=fill, lw=0.7, r=0.25)
        pg.text(cx, cy + 2.2, label, fs, True, '#ffffff' if fn in DARK else '#000000', 'c')
        ytxt = cy + 15.0
    for i, ln in enumerate(wrap(desc, pitch - 3, 5.6, nlines)):
        pg.text(cx, ytxt + i * 6.4, ln, 5.6, False, '#000000', 'c')


# ---------------------------------------------------------------- blocks: (w, h, draw(pg, x, y))
PX, PYN = 54.0, 3


def conn_block(c, descs=None, note=''):
    labels = cav_list(c)
    n = len(labels)
    if descs is None and not c['pins'] and c.get('cap_of'):
        descs = c['cap_of']
    rows = max(1, math.ceil(n / 8))
    cols = max(1, math.ceil(n / rows))
    ph = 2 * 9.0 + 6 + PYN * 6.4 + 4
    head = 26.0
    w = max(cols * PX + 8, 150.0)
    h = head + rows * ph + 8
    sub = '%s  |  %s  |  %d cavities%s  |  numbered grid (true count)' % (
        c['part_number'] if len(c['part_number']) < 48 else c['part_number'][:45] + '...', c['harness'], c['n'],
        '' if n == c['n'] else ', %d in use' % n)
    w = max(w, min(tw(sub, 6.0) + 12, 420))

    def draw(pg, x, y):
        pg.rect(x, y, w, h, fill='#fbfcfe', lw=0.8, r=0.02)
        pg.text(x + 5, y + 11, wrap(c['name'], w - 8, 9.0, 1, True)[0], 9.0, True)
        for i, ln in enumerate(wrap(sub, w - 8, 6.0, 1)):
            pg.text(x + 5, y + 20, ln, 6.0, False, '#444444')
        for i, lb in enumerate(labels):
            rr, cc = divmod(i, cols)
            cx = x + 4 + PX / 2 + cc * PX
            cy = y + head + 10 + rr * ph
            ds = c['pins'].get(lb)
            if descs is not None:
                ds = descs.get(lb) or ds
            d = ' / '.join(ds) if ds else ''
            f = fn_of(d)
            cavity(pg, cx, cy, lb, f, 9.0, '' if f == 'spare' else d, PX)
        if note:
            pg.text(x + w - 4, y + h - 3, note, 5.5, False, '#666666', 'r')
    return w, h, draw


def drb_block(conns):
    bh = [c for c in conns.values() if c['n'] == 102 and c['part_number'].upper().startswith('DRB1')]
    if not bh:
        return None
    descs = {}
    for c in sorted(bh, key=lambda c: ('eng' in c['conn_id'], c['conn_id'])):
        for p, ds in c['pins'].items():
            descs.setdefault(p, ds)
    dx, dy = 56.0, 47.0
    w, h = 12 * dx + 40, 12 * dy + 58

    def draw(pg, x, y):
        pg.rect(x, y, w, h, fill='#fbfcfe', lw=0.8, r=0.01)
        pg.text(x + 8, y + 15, 'DRB102 firewall bulkhead - insert face (TE drawing view)', 11.0, True)
        pg.text(x + 8, y + 26, 'DRB12-102PAE (cabin) / DRB16-102SAE (engine bay)  |  harnesses: %s  |  circle size = contact size (4 > 8 > 12 > 16)'
                % ', '.join(sorted({c['harness'] for c in bh})), 6.5, False, '#444444')
        pg.text(x + 3 * dx + 20, y + 40, 'Left wedgelock half (52-102)', 8, True, '#333333', 'c')
        pg.text(x + 9 * dx + 20, y + 40, 'Right wedgelock half (1-51)', 8, True, '#333333', 'c')
        x0, y0 = x + 20 + dx / 2, y + 48
        for ci, col in enumerate(COLS):
            off = (12 - len(col)) / 2.0
            for ri, pin in enumerate(col):
                if pin is None:
                    continue
                d = ' / '.join(descs.get(str(pin), []))
                f = fn_of(d)
                cavity(pg, x0 + ci * dx, y0 + 12 + (off + ri) * dy, str(pin), f,
                       RAD[SIZE.get(pin, 16)], '' if f == 'spare' else d, dx, 3)
        xs = x + 20 + 6 * dx
        pg.line(xs, y + 46, xs, y + h - 6, '#555555', 0.8, '[3 3] 0')
    return w, h, draw, [c['name'] for c in bh]


def parse_colour(s):
    m = re.match(r'([A-Z]{1,2})(?:-([A-Z]{1,2}))?\b', (s or '').strip())
    return (m.group(1), m.group(2)) if m else (None, None)


def oem_chip(pg, x, y, code, w=24.0, h=9.0):
    base, stripe = parse_colour(code)
    pg.rect(x, y, w, h, fill=OEMC.get(base, '#cccccc'), lw=0.5)
    if stripe:
        pg.rect(x + w * 0.4, y, w * 0.2, h, fill=OEMC.get(stripe, '#cccccc'), line=None, lw=0)
        pg.rect(x, y, w, h, fill=None, lw=0.5)
    if not base:
        pg.text(x + w / 2, y + 6.5, '?', 6, True, '#000000', 'c')


OW = 386.0


def oem_row(r):
    """One tap row. Returns (height, draw)."""
    pin = r['pin']
    fac = wrap(r['func'], 118, 6.0, 3)
    ours = [(r['our'], True), (r['far'], False)] + [(l, False) for l in wrap(r['ewd'], 196, 5.6, 3)]
    ours = [(t, b) for t, b in ours if t]
    wl = []
    for t, b in ours:
        wl += [(l, b) for l in wrap(t, 196, 6.0 if b or t == r['far'] else 5.6, 2, b)]
    nl = max(len(fac), len(wl), 2)
    h = nl * 7.0 + 6

    def draw(pg, x, y):
        pg.rect(x, y, OW - 8, h, fill='#ffffff', lw=0.4)
        pg.circle(x + 12, y + 11, 7.0, '#ffffff')
        pg.text(x + 12, y + 13.4, pin[:4], 6.4 if len(pin) <= 2 else 5.0, True, '#000000', 'c')
        oem_chip(pg, x + 22, y + 6.5, r['colour'])
        pg.text(x + 34, y + 20.5, (r['colour'] or '?').split(' ')[0][:6], 5.4, True, '#333333', 'c')
        for i, l in enumerate(fac):
            pg.text(x + 50, y + 8 + i * 7.0, l, 6.0)
        pg.line(x + 171, y + 3, x + 171, y + h - 3, '#999999', 0.4)
        for i, (l, b) in enumerate(wl):
            pg.text(x + 176, y + 8 + i * 7.0, l, 6.0 if b or l.startswith(('to ', '<-')) else 5.6, b,
                    '#000000' if b else '#333333')
    return h, draw


def short(s, n=90):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def tap_row(t, plug_pin=None):
    s, o = t['side'], t['oside']
    pin = t[s + '_pin'] or ''
    m = re.match(r'(.*?)-(\d+)$', pin)
    plug, p = (m.group(1), m.group(2)) if m else (None, pin)
    if len(p) > 3 or not re.match(r'^[A-Za-z0-9]+$', p):
        p = (re.match(r'\d+', p) or [None])[0] or '-'
    loc = t['oem_location']
    func = loc.split(' - ', 1)[1] if ' - ' in loc else (t[s + '_desc'] or loc)
    func = re.sub(r'^[A-Z]{1,2}(?:-[A-Z]{1,2})?, ', '', func)
    func = re.sub(r'\s*\((?:EWD|1993|1990|1992)[^)]*\)\s*$', '', func).strip()
    colc = t['oem_wire_colour'] or ''
    ewd = 'EWD %s' % t['oem_ewd_page'] if t['oem_ewd_page'] else 'EWD page TBD'
    meth = short(t['oem_method'], 56)
    gauge = (t['gauge_awg'] + ' AWG ' if t['gauge_awg'] else '') + (t['colour'] or '')
    return dict(plug=plug, pin=p or '-', colour=colc, func=short(func, 80),
                our='our %s: %s' % (t['wire_id'], gauge.strip()), far='to ' + short(far_end(t, o), 52) + ' (' + short(t[o + '_desc'] or t['net_name'], 34) + ')',
                ewd='%s; %s' % (ewd, meth))


def oem_blocks_split(title, sub, rows, maxh=640.0):
    """oem_block, cut into several blocks when the rows would not fit one page."""
    chunks, cur, h = [], [], 40.0
    for r in rows:
        rh = oem_row(r)[0] + 3 + (12 if (not cur or cur[-1]['plug'] != r['plug']) and r['plug'] else 0)
        if cur and h + rh > maxh:
            chunks.append(cur)
            cur, h = [], 40.0
        cur.append(r)
        h += rh
    chunks.append(cur)
    return [('oem', title, oem_block(title + (' (%d of %d)' % (i + 1, len(chunks)) if len(chunks) > 1 else ''), sub, c))
            for i, c in enumerate(chunks)]


def oem_block(title, sub, rows):
    """Junction-box outline with plug groups and tap rows."""
    plugs = []
    for r in rows:
        if r['plug'] not in [p for p, _ in plugs]:
            plugs.append((r['plug'], []))
        dict(plugs)[r['plug']].append(r)
    parts = []
    h = 38.0
    for pl, rs in plugs:
        hh = 12.0 if pl else 0.0
        items = [oem_row(r) for r in rs]
        parts.append((pl, hh, items))
        h += hh + sum(i[0] + 3 for i in items) + 4

    def draw(pg, x, y):
        pg.rect(x, y, OW, h, fill='#f4f7fb', lw=1.3, r=0.025)
        pg.rect(x + 4, y + 4, OW - 8, 24, fill='#dfe6f1', lw=0.5)
        pg.text(x + 8, y + 15, title, 9.5, True)
        pg.text(x + 8, y + 24, sub, 6.0, False, '#333333')
        yy = y + 32
        for pl, hh, items in parts:
            if pl:
                pg.text(x + 8, yy + 8, ('Plug ' + pl) if len(pl) <= 3 else pl, 7.2, True, '#14213d')
                pg.line(x + 8, yy + 10.5, x + OW - 8, yy + 10.5, '#14213d', 0.4)
                yy += hh
            for ih, idraw in items:
                idraw(pg, x + 4, yy)
                yy += ih + 3
            yy += 4
    return OW, h, draw


def oem_blocks(taps, grounds):
    boxes = [('jb1', 'J/B No.1 junction block', 'left kick panel; factory box KEPT; we splice factory leads of plugs 1F / 1H / 1I; cabin side'),
             ('ie1', 'IE1 cowl plug', 'left kick panel, cowl side; engine-room main REMOVED, we tap the cowl-side leads'),
             ('rb2', 'Old R/B No.2 position', 'left kick panel; relay block REMOVED, its factory leads stay in the loom'),
             ('rb4', 'Old R/B No.4 position', 'right kick panel; relay block REMOVED, its factory leads stay in the loom'),
             ('jb3', 'J/B No.3 (plug 3B)', 'behind the combination meter; OEM junction block KEPT'),
             ('ig2', 'IG2 plug', 'under the ECU, cowl side; engine-side wire removed, we tap the cowl-side leads')]

    def box_of(c):
        if re.match(r'J/B( No\.)?\s?1', c):
            return 'jb1'
        for k, pre in (('ie1', 'IE1'), ('rb2', 'R/B2'), ('rb4', 'R/B'), ('jb3', 'J/B3'), ('ig2', 'IG2')):
            if c.startswith(pre):
                return k
        return None
    groups, dev = {}, {}
    for t in taps:
        c = t[t['side'] + '_conn']
        k = box_of(c)
        (groups.setdefault(k, []) if k else dev.setdefault(c, [])).append(t)
    out = []
    for k, title, sub in boxes:
        rows = [tap_row(t) for t in groups.get(k, [])]
        if not rows:
            continue
        for r in rows:
            if r['plug'] is None:
                m = re.search(r'\b(1[A-Z])\b', ' '.join(t['oem_location'] for t in groups[k]))
                r['plug'] = (m.group(1) if (k == 'jb1' and m) else 'Leads / pins')
        rows.sort(key=lambda r: (r['plug'], int(r['pin']) if r['pin'].isdigit() else 99))
        out += oem_blocks_split(title, sub, rows)
    gr = []
    for name in sorted(grounds):
        for t in grounds[name]:
            s, o = t['side'], t['oside']
            gr.append(dict(plug=re.sub(r'\s*\(.*', '', name)[:46], pin='GND', colour='B',
                           func=short(re.search(r'\((.*)\)', name).group(1) if '(' in name else name, 60),
                           our='our %s: %s %s' % (t['wire_id'], t['gauge_awg'] + ' AWG' if t['gauge_awg'] else '', t['colour']),
                           far='from ' + short(far_end(t, o), 52), ewd='ring terminal on the factory ground / stud'))
    if gr:
        out += oem_blocks_split('Body ground points we use', 'factory ground studs and bolts; each gets a ring terminal', gr)
    for c in sorted(dev):
        rows = [tap_row(t) for t in dev[c]]
        rows.sort(key=lambda r: int(r['pin']) if r['pin'].isdigit() else 99)
        for r in rows:
            r['plug'] = None
        t0 = dev[c][0]
        nm = re.split(r'\s+pin\s|\s*[,;(]', re.sub(r'^OEM\s+', '', t0[t0['side'] + '_conn_name'] or c))[0]
        out += oem_blocks_split(short(nm, 44), '%s  |  device plug / lead tapped by our harness' % c.replace(' (factory)', ''), rows)
    return out


# ---------------------------------------------------------------- layout
AREAS = [('ecu', 'ECU AND BULKHEAD'), ('cabin', 'CABIN'), ('engine', 'ENGINE BAY'), ('fuse', 'FUSE BOXES, RELAYS AND HEAVY DC'),
         ('oem', 'OEM JUNCTION BOXES AND SPLICE POINTS'), ('rear', 'REAR')]


def area_of(c):
    h = c['harness']
    if c['name'].upper().startswith('ECU'):
        return 'ecu'
    if h in ('CabinPower', 'HeavyDC'):
        return 'fuse'
    if h in ('A-engine', 'B-engine', 'EngineRoom-C', 'WheelSpeed-Front'):
        return 'engine'
    if h in ('RearFuel', 'RearLights', 'WheelSpeed-Rear'):
        return 'rear'
    return 'cabin'


def pack(blocks):
    """Shelf-pack blocks onto pages. blocks: [(kind, name, (w,h,draw))] -> pages [[(x,y,block)]]."""
    bw, bh = PW - 2 * MX, PH - TOP - BOT
    pages, cur, x, y, rowh = [], [], 0.0, 0.0, 0.0
    for b in blocks:
        w, h = b[2][0], b[2][1]
        if h > bh or w > bw:
            raise SystemExit('block %s too big for a page (%.0f x %.0f)' % (b[1], w, h))
        if x + w > bw + 0.1:
            x, y, rowh = 0.0, y + rowh + GAP, 0.0
        if y + h > bh:
            pages.append(cur)
            cur, x, y, rowh = [], 0.0, 0.0, 0.0
        cur.append((x, y, b))
        x += w + GAP
        rowh = max(rowh, h)
    if cur:
        pages.append(cur)
    return pages


def build_pages(conns, order, taps, grounds):
    by_area = {k: [] for k, _ in AREAS}
    drb = drb_block(conns)
    for cid in order:
        c = conns[cid]
        if c['n'] == 102 and c['part_number'].upper().startswith('DRB1'):
            continue
        mate = c['mates_with']
        note = ('mates ' + mate) if mate else ''
        by_area[area_of(c)].append(('conn', c['name'], conn_block(c, note=short(note, 40))))
    if drb:
        by_area['ecu'].insert(0, ('drb', 'DRB102 bulkhead', drb[:3]))
    for b in oem_blocks(taps, grounds):
        by_area['oem'].append(b)
    for k in by_area:   # ECU first, then the rest by size so shelves pack tight
        if k not in ('ecu',):
            by_area[k].sort(key=lambda b: -b[2][1] // 60)
    pages = []
    for k, title in AREAS:
        if not by_area[k]:
            continue
        pp = pack(by_area[k])
        for i, p in enumerate(pp):
            pages.append((k, title + (' (%d of %d)' % (i + 1, len(pp)) if len(pp) > 1 else ''), p))
    return pages


def legend(pg):
    y = PH - BOT + 6
    pg.line(MX, y - 2, PW - MX, y - 2, '#999999', 0.5)
    x = MX
    step = (PW - 2 * MX) / len(PAL)
    for k, lab, col in PAL:
        pg.circle(x + 8, y + 10, 6.5, col)
        pg.text(x + 18, y + 12.5, lab, 7.2)
        x += step
    pg.text(MX, y + 25, 'Fill = function (keyword rule on the wire-list description). Circle size = contact size (DRB102 only). '
            'Only the DRB102 is its real maker insert face; every other connector is a numbered grid with the true cavity count '
            '(pin order, not the maker face view). Wire lists are the truth. Spare = no wire on that cavity.', 6.3, False, '#444444')


def render():
    import fitz
    conns, order, taps, grounds = load()
    pages = build_pages(conns, order, taps, grounds)
    ih = inputs_hash()
    N = len(pages) + 1
    doc = fitz.open()
    # page 1: title block + index
    pg = Pg(doc)
    pg.rect(MX, MX, PW - 2 * MX, PH - MX - 6, fill=None, lw=1.2)
    pg.text(MX + 14, 60, 'ST185 CELICA - CONNECTOR ATLAS', 26, True)
    pg.text(MX + 14, 82, 'Every connector of all 15 harnesses, and every OEM junction box / plug / ground point we splice into.', 11, False, '#333333')
    pg.text(MX + 14, 96, 'Generated from docs/harness/wirelist/*.csv by docs/harness/atlas/build_atlas.py. Never edit the PDF; change the wire list and regenerate.', 8.5, False, '#555555')
    init = 'DG'
    p = os.path.join(os.path.expanduser('~'), '.drawing-initials')
    if os.path.exists(p):
        init = open(p, encoding='utf-8').read().strip().splitlines()[0] or init
    tb = [('DRAWN', init), ('SHEETS', '%d (11 x 17 in landscape)' % N), ('REV', 'A'), ('SOURCE HASH', ih),
          ('PROJECT', 'st185-link-ecu-config')]
    x = MX + 14
    for k, v in tb:
        pg.rect(x, 110, 205, 30, fill='#f4f7fb', lw=0.7)
        pg.text(x + 5, 120, k, 6.5, False, '#555555')
        pg.text(x + 5, 134, v, 9.5, True)
        x += 210
    pg.text(MX + 14, 168, 'PAGE INDEX', 12, True)
    y = 184
    colx = [MX + 14, MX + 14 + 585]
    ci, ycol = 0, y
    for i, (k, title, items) in enumerate(pages, start=2):
        names = [b[1] for _, _, b in items]
        lines = wrap(', '.join(names), 520, 7.2, 3)
        need = 13 + len(lines) * 8.6 + 5
        if ycol + need > PH - 150 and ci == 0:
            ci, ycol = 1, y
        pg.text(colx[ci], ycol, 'p.%d  %s' % (i, title), 9.0, True)
        for j, ln in enumerate(lines):
            pg.text(colx[ci] + 14, ycol + 11 + j * 8.6, ln, 7.2, False, '#222222')
        ycol += need
    pg.text(MX + 14, PH - 118, 'HOW TO READ', 10, True)
    for j, ln in enumerate(['Cavity circle: number inside, short signal label under it, fill = function (legend below). White = spare.',
                            'Connector title: name, maker part number, harness, true cavity count. "mates X" names the other half.',
                            'OEM boxes: outline of the factory box; each row = factory pin, factory wire colour, what the factory lead does, '
                            'what our wire does and where it goes, EWD page and splice method.',
                            'Factory wire colours use the Toyota codes: B black, W white, R red, G green, L blue, Y yellow, O orange, BR brown, GR grey, P pink, LG light green; second letter = stripe.']):
        pg.text(MX + 14, PH - 104 + j * 10, ln, 7.6, False, '#222222')
    legend(pg)
    pg.text(PW - MX, PH - 10, 'ST185-connector-atlas | page 1 of %d | src %s' % (N, ih), 6.5, False, '#666666', 'r')
    for i, (k, title, items) in enumerate(pages, start=2):
        pg = Pg(doc)
        pg.rect(MX - 6, 14, PW - 2 * MX + 12, 22, fill='#14213d', lw=0)
        pg.text(MX + 2, 30, title, 14, True, '#ffffff')
        pg.text(PW - MX - 2, 30, 'ST185 connector atlas   p.%d / %d' % (i, N), 9, False, '#ffffff', 'r')
        for x, y, b in items:
            b[2][2](pg, MX + x, TOP + y)
        legend(pg)
        pg.text(PW - MX, PH - 10, 'ST185-connector-atlas | page %d of %d | src %s' % (i, N, ih), 6.5, False, '#666666', 'r')
    doc.set_metadata({'title': 'ST185 connector atlas', 'author': 'DG', 'subject': 'generated from wire lists',
                      'keywords': 'inputs=' + ih})
    doc.save(OUT, deflate=True, garbage=3)
    with open(SIDE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(ih + '\n')
    print('wrote %s (%d pages, inputs %s)' % (os.path.relpath(OUT), N, ih))


def check():
    if not (os.path.exists(OUT) and os.path.exists(SIDE)):
        print('FAIL: ST185-connector-atlas.pdf / .inputs.txt missing; run docs/harness/atlas/build_atlas.py')
        return 1
    have = open(SIDE, encoding='utf-8').read().strip()
    want = inputs_hash()
    if have != want:
        print('FAIL: connector atlas is stale (wire lists or generator changed): have %s, want %s. '
              'Run python docs/harness/atlas/build_atlas.py and commit the PDF.' % (have, want))
        return 1
    print('connector atlas is current (%s)' % want)
    return 0


if __name__ == '__main__':
    if '--check' in sys.argv:
        sys.exit(check())
    render()
