#!/usr/bin/env python
"""ST185 connector atlas: 11x17 (tabloid) landscape PDF generated from the wire lists.

Every connector of all harnesses (cavity circles, number inside, short signal under it, fill = function)
plus every OEM junction box and plug we tap (real face view, factory wire, our harness wire).
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
import json
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
    fs.append(os.path.join(HERE, '..', 'cleanroom', 'drb102_outputs.py'))
    fs.append(os.path.join(HERE, 'oem-plugs.json'))
    fs += glob.glob(os.path.join(HERE, 'oem-faces', '*.png'))
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
    taps = []
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
    for c in conns.values():
        if c.get('_mate'):
            c['cap_of'] = c['_mate']['pins']
    return conns, order, taps


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


def cavity(pg, cx, cy, label, fn, r=9.0, desc='', pitch=54.0, nlines=3, fill=None):
    fill = fill or FILL[fn]
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
    """The DRB102 insert face. Cavity data, function kinds, colours, sizes and short labels come from the
    master generator (cleanroom/drb102_outputs.py) so this face is the same as DRB102-bulkhead-map.png."""
    bh = [c for c in conns.values() if c['n'] == 102 and c['part_number'].upper().startswith('DRB1')]
    if not bh:
        return None
    sys.path.insert(0, os.path.join(HERE, '..', 'cleanroom'))
    import drb102_outputs as D
    lists = {os.path.basename(f)[:-len('-wirelist.csv')]: rd(f) for f in sorted(glob.glob(os.path.join(WL, '*-wirelist.csv')))}
    rows = {r['cavity']: r for r in D.table(lists)}
    dx, dy = 90.0, 53.0
    w, h = 12 * dx + 40, 12 * dy + 58
    rad = {k: v * 0.46 for k, v in D.RADIUS.items()}

    def draw(pg, x, y):
        pg.rect(x, y, w, h, fill='#fbfcfe', lw=0.8, r=0.01)
        pg.text(x + 8, y + 15, 'DRB102 firewall bulkhead - insert face (TE drawing view) - same face as DRB102-bulkhead-map.png', 11.0, True)
        pg.text(x + 8, y + 26, 'DRB12-102PAE (cabin) / DRB16-102SAE (engine bay)  |  harnesses: %s  |  circle size = contact size (4 > 8 > 12 > 16)'
                % ', '.join(sorted({c['harness'] for c in bh})), 6.5, False, '#444444')
        pg.text(x + 3 * dx + 20, y + 40, 'Left wedgelock half (52-102)', 8, True, '#333333', 'c')
        pg.text(x + 9 * dx + 20, y + 40, 'Right wedgelock half (1-51)', 8, True, '#333333', 'c')
        x0, y0 = x + 20 + dx / 2, y + 48
        for ci, col in enumerate(D.COLS):
            off = (12 - len(col)) / 2.0
            for ri, pin in enumerate(col):
                if pin is None:
                    continue
                r = rows[pin]
                k = r['kind']
                cavity(pg, x0 + ci * dx, y0 + 12 + (off + ri) * dy, str(pin), 'sig' if k in ('spare', 'signal') else 'gnd',
                       rad[r['size']], '' if k == 'spare' else r['short'], dx, 3, fill='#' + D.FILL[k])
        xs = x + 20 + 6 * dx
        pg.line(xs, y + 46, xs, y + h - 6, '#555555', 0.8, '[3 3] 0')
    return w, h, draw, [c['name'] for c in bh]


def short(s, n=90):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


# ---------------------------------------------------------------- OEM junction box / plug pages (v2)
OEMD = json.load(open(os.path.join(HERE, 'oem-plugs.json'), encoding='utf-8'))
PAGE_W, PAGE_H = PW - 2 * MX, PH - TOP - BOT
OUR = {'Green': '#2e9d4f', 'Red': '#c62828', 'White': '#f4f4f4', 'Black': '#1b1b1b', 'Blue': '#2f6fd6', 'Yellow': '#f2c200',
       'Orange': '#ee7a00', 'Violet': '#7b3fa0', 'Brown': '#8b5a2b', 'Gray': '#8a8a8a', 'Pink': '#e58fb4'}
RH = 38.0                       # tap row height
XF, XPIN, XOEM, XSIG, XDIV, XOUR, XPILL, XHAR = 6.0, 262.0, 282.0, 374.0, 596.0, 604.0, 812.0, 982.0
FW = 244.0                      # face column width
BMAX, BWMAX = 190.0, 600.0     # band mode: max face height / width
FMAX = 120.0                    # face image max height


def lum(h):
    r, g, b = rgb(h)
    return 0.299 * r + 0.587 * g + 0.114 * b


def pill(pg, x, y, base, stripe, label, w, h=22.0, fs=12.0, table=None):
    """Wire colour pill: base colour with the label inside, stripe colour as a block at the right end."""
    table = table or OEMC
    bc = table.get(base, '#cccccc')
    sw = w * 0.34 if stripe else 0.0
    pg.rect(x, y, w - sw, h, fill=bc, lw=0.8)
    if stripe:
        pg.rect(x + w - sw, y, sw, h, fill=table.get(stripe, '#cccccc'), lw=0.8)
    pg.text(x + (w - sw) / 2, y + h / 2 + fs * 0.35, label, fs, True, '#ffffff' if lum(bc) < 0.55 else '#000000', 'c')


def band_chips(pg, x, y, bands):
    for i, b in enumerate(bands):
        pg.rect(x + i * 11, y, 9.0, 22.0, fill=OUR.get(b, '#cccccc'), lw=0.6)


def oem_code(s):
    m = re.match(r'\s*([A-Z]{1,2})(?:-([A-Z]{1,2}))?\b', s or '')
    return (m.group(1), m.group(2)) if m else (None, None)


def tap_row(t):
    s, o = t['side'], t['oside']
    pin = t[s + '_pin'] or ''
    m = re.match(r'(.*?)-(\d+)$', pin)
    plug, p = (m.group(1), m.group(2)) if m else (None, pin)
    if len(p) > 3 or not re.match(r'^[A-Za-z0-9]+$', p):
        p = (re.search(r'\d+', p) or [None])[0] or '-'
    loc = t['oem_location']
    func = loc.split(' - ', 1)[1] if ' - ' in loc else (t[s + '_desc'] or loc)
    func = re.sub(r'^[A-Z]{1,2}(?:-[A-Z]{1,2})?, ', '', func)
    func = re.sub(r'\s*\((?:EWD|1993|1990|1992)[^)]*\)\s*$', '', func).strip()
    func = re.sub(r';.*$', '', func).strip()
    func = re.sub(r'\s*\((?:EWD|1993|1990|1992)[^)]*\)', '', func)
    func = func.split(' / ')[0].strip()
    far = t[o + '_conn_name'] or t[o + '_conn']
    desc = t[o + '_desc'] or t['net_name'] or ''
    far0 = re.sub(r'\s*\(.*', '', far)
    fe = '%s pin %s' % (far0, t[o + '_pin']) if t[o + '_type'] == 'connector' else far0
    return dict(plug=plug, pin=p or '-', ocol=oem_code(t['oem_wire_colour']), func=short(func, 90), wire=t['wire_id'],
                awg=t['gauge_awg'], desc=short(desc, 70), colour=t['colour'], stripe=t['stripe'],
                bands=[b for b in (t['ident_bands'] or '').split('-') if b], harness=t['harness'],
                leg=t['route_branch'] or '', far=short(fe, 44))


def draw_row(pg, x, y, r):
    pg.rect(x + XPIN - 22, y, PAGE_W - XPIN + 18, RH - 3, fill='#ffffff', lw=0.5)
    pg.circle(x + XPIN, y + RH / 2 - 1.5, 13.0, '#ffffff', 1.0)
    pin = r['pin'][:4]
    pg.text(x + XPIN, y + RH / 2 + 3.4, pin, 13.0 if len(pin) <= 2 else 9.0, True, '#000000', 'c')
    b, st = r['ocol']
    pill(pg, x + XOEM, y + 6, b, st, '-'.join(c for c in (b, st) if c) or '?', 84.0)
    for i, ln in enumerate(wrap(r['func'], 218, 12.0, 2, True)):
        pg.text(x + XSIG, y + 15 + i * 13.0, ln, 12.0, True)
    pg.line(x + XDIV - 4, y + 3, x + XDIV - 4, y + RH - 6, '#999999', 0.5)
    pg.text(x + XOUR, y + 15, '%s  %s' % (r['wire'], (r['awg'] + ' AWG') if r['awg'] else ''), 12.0, True)
    for ln in wrap(r['desc'], 200, 10.0, 1):
        pg.text(x + XOUR, y + 28, ln, 10.0, False, '#222222')
    pill(pg, x + XPILL, y + 6, r['colour'], r['stripe'], '-'.join(c for c in (r['colour'], r['stripe']) if c), 118.0, 22.0, 11.0, OUR)
    band_chips(pg, x + XPILL + 123, y + 6, r['bands'])
    pg.text(x + XHAR, y + 14, r['harness'], 12.0, True)
    leg = r['leg'] or 'toward ' + r['far']
    for i, ln in enumerate(wrap(leg, 206, 9.5, 2)):
        pg.text(x + XHAR, y + 25 + i * 10.5, ln, 9.5, False, '#222222' if r['leg'] else '#666666')


def is_band(info):
    """Wide face views go in a centred band above the rows; narrow ones sit beside them."""
    p = os.path.join(HERE, info['face']) if info.get('face') else None
    if not (p and os.path.exists(p)):
        return False
    import fitz
    pm = fitz.Pixmap(p)
    return pm.width / pm.height > 1.7


def face_size(info):
    """(image width, image height) of the face crop, or None."""
    p = os.path.join(HERE, info['face']) if info.get('face') else None
    if not (p and os.path.exists(p)):
        return None
    import fitz
    pm = fitz.Pixmap(p)
    asp = pm.width / pm.height
    if is_band(info):
        h = min(BMAX, BWMAX / asp)
        return h * asp, h
    w, h = FW, FW / asp
    if h > FMAX:
        w, h = FMAX * asp, FMAX
    return w, h


def note_lines(info):
    notes = []
    if info.get('housing_pn') or info.get('terminal_pn'):
        notes.append('Housing %s / terminal %s' % (info.get('housing_pn') or '-', info.get('terminal_pn') or '-'))
    else:
        c = info.get('rm_candidates')
        notes.append('Housing / terminal PN: not matched' + (
            '; RM1022E %s housings p.%d-%d (confirm shape)' % (c['text'], c['pages'][0], c['pages'][1]) if c else ''))
    src = info.get('src') or info
    if src.get('doc'):
        notes.append('Source: %s p.%s%s' % (src['doc'], src.get('page'), ' (printed %s)' % src['printed'] if src.get('printed') else ''))
    return [ln for n in notes for ln in wrap(n, FW, 7.8, 3)]


def face_h(info):
    fs = face_size(info)
    return 24 + (fs[1] + 5 if fs else 52) + 9 * len(note_lines(info)) + 6


def face_band(pg, x, y, info, caption):
    """Wide face: caption, image and notes centred across the page."""
    import fitz
    cx = x + PAGE_W / 2
    pg.text(cx, y + 15, caption, 14.0, True, '#14213d', 'c')
    fs = face_size(info)
    pg.p.insert_image(fitz.Rect(cx - fs[0] / 2, y + 22, cx + fs[0] / 2, y + 22 + fs[1]), filename=os.path.join(HERE, info['face']))
    pg.rect(cx - fs[0] / 2, y + 22, fs[0], fs[1], fill=None, line='#999999', lw=0.4)
    yy = y + 22 + fs[1] + 5
    for ln in note_lines(info):
        pg.text(cx, yy + 8, ln, 7.8, False, '#333333', 'c')
        yy += 9


def face_col(pg, x, y, info, caption):
    pg.text(x + XF, y + 14, wrap(caption, FW, 13.0, 1, True)[0], 13.0, True, '#14213d')
    yy = y + 20
    fs = face_size(info)
    if fs:
        import fitz
        pg.p.insert_image(fitz.Rect(x + XF, yy, x + XF + fs[0], yy + fs[1]), filename=os.path.join(HERE, info['face']))
        pg.rect(x + XF, yy, fs[0], fs[1], fill=None, line='#999999', lw=0.4)
        yy += fs[1] + 5
    else:
        pg.rect(x + XF, yy, FW, 46, fill='#f4f4f4', lw=0.6, line='#999999')
        for i, ln in enumerate(wrap('No connector face view in the repair-manual app (the EWD shows only the part position)', FW - 12, 8.5, 3)):
            pg.text(x + XF + 6, yy + 13 + i * 10, ln, 8.5, False, '#555555')
        yy += 52
    for ln in note_lines(info):
        pg.text(x + XF, yy + 8, ln, 7.8, False, '#333333')
        yy += 9


def app_url(doc, page):
    return '%s#open=%s&page=%s' % (OEMD['app_base'], doc, page)


HEAD = 100.0


def oem_pages(title, sub, doc, page, sections):
    """A box = centered header + plug sections (face on the left, tap rows on the right); split over pages when full.
    sections: [(caption, info, rows)]. Returns [('oem', name, (w, h, draw))]."""
    avail = PAGE_H - HEAD - 8
    pagesl, cur, used = [], [], 0.0
    for cap, info, rows in sections:
        fh = face_h(info)
        i = 0
        while True:
            band = is_band(info)
            bh = fh if band else 0.0
            room = avail - used
            n = int((room - 6 - bh) // RH)
            if cur and (n < 2 or room < fh + 4 or (len(rows) - i > n and n < 3)):
                pagesl.append(cur)
                cur, used, room = [], 0.0, avail
                n = int((room - 6 - bh) // RH)
            chunk = rows[i:i + max(n, 1)]
            h = bh + len(chunk) * RH + 6 if band else max(len(chunk) * RH + 6, fh)
            cur.append((cap, info, chunk, h, i > 0))
            used += h + 4
            i += len(chunk)
            if i >= len(rows):
                break
    if cur:
        pagesl.append(cur)
    out = []
    for pi, secs in enumerate(pagesl):
        tt = title + (' (%d of %d)' % (pi + 1, len(pagesl)) if len(pagesl) > 1 else '')

        def draw(pg, x, y, secs=secs, tt=tt):
            import fitz
            pg.rect(x, y, PAGE_W, PAGE_H, fill='#f4f7fb', lw=1.3, r=0.01)
            cx = x + PAGE_W / 2
            pg.text(cx, y + 30, tt, 24.0, True, '#14213d', 'c')
            pg.text(cx, y + 48, sub, 12.0, False, '#333333', 'c')
            if doc:
                u = app_url(doc, page)
                w = pg.text(cx, y + 64, 'Repair-manual app, location page: ' + u, 10.0, True, '#1a4fd0', 'c')
                pg.p.insert_link({'kind': fitz.LINK_URI, 'from': fitz.Rect(cx - w / 2, y + 55, cx + w / 2, y + 68), 'uri': u})
                pg.text(cx, y + 76, 'start the app server first: ' + OEMD['app_launch'], 7.5, False, '#555555', 'c')
            yy = y + 84
            for xx, lab in ((XPIN - 12, 'PIN'), (XOEM, 'FACTORY WIRE'), (XSIG, 'FACTORY SIGNAL (FSM / EWD)'),
                            (XOUR, 'OUR WIRE (as on the harness drawing)'), (XPILL, 'OUR COLOUR'), (XHAR, 'HARNESS  /  LEG TO GRAB')):
                pg.text(x + xx, yy + 8, lab, 8.5, True, '#555555')
            yy += 14
            for cap, info, chunk, h, cont in secs:
                pg.line(x + 4, yy - 2, x + PAGE_W - 4, yy - 2, '#14213d', 0.8)
                capt = cap + (' (cont.)' if cont else '')
                if is_band(info):
                    face_band(pg, x, yy, info, capt)
                    ry = yy + face_h(info) + 2
                else:
                    face_col(pg, x, yy, info, capt)
                    ry = yy + 2
                for r in chunk:
                    draw_row(pg, x, ry, r)
                    ry += RH
                yy += h + 4
        out.append(('oem', tt, (PAGE_W, PAGE_H, draw)))
    return out


def oem_blocks(taps):
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

    def uniq(rows):
        seen, out = set(), []
        for r in rows:
            key = (r['plug'], r['pin'], r['wire'])
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out
    out = []
    for k in ('jb1', 'ie1', 'rb2', 'rb4', 'jb3', 'ig2'):
        if not groups.get(k):
            continue
        bx = OEMD['boxes'][k]
        rows = []
        for t in groups[k]:
            r = tap_row(t)
            txt = ' '.join([t['oem_location'], t[t['side'] + '_conn'], t[t['side'] + '_pin']])
            if k == 'jb1':
                m = re.search(r'\b(1[A-I])\b', txt)
                r['plug'] = r['plug'] or (m.group(1) if m else 'Leads')
            elif k == 'jb3':
                r['plug'] = r['plug'] or '3B'
            elif k == 'rb4':
                r['plug'] = 'starter' if 'starter' in txt.lower() else 'heater'
            elif k == 'rb2':
                r['plug'] = 'RB2'
            else:
                r['plug'] = k.upper()
            rows.append(r)
        rows = uniq(rows)
        rows.sort(key=lambda r: (r['plug'], int(r['pin']) if r['pin'].isdigit() else 99))
        secs = []
        for pl in sorted({r['plug'] for r in rows}):
            info = OEMD['plugs'].get('%s:%s' % (k, pl)) or {'caption': 'Plug ' + pl}
            secs.append((info.get('caption', 'Plug ' + pl), info, [r for r in rows if r['plug'] == pl]))
        out += oem_pages(bx['title'], bx['sub'], bx['doc'], bx['page'], secs)
    secs = []
    for c in sorted(dev):
        info = dict(OEMD['devices'].get(c, {}))
        code = info.get('code') or c
        rows = uniq([dict(tap_row(t), plug=None) for t in dev[c]])
        rows.sort(key=lambda r: int(r['pin']) if r['pin'].isdigit() else 99)
        t0 = dev[c][0]
        nm = re.split(r'\s+pin\s|\s*[,;(]', re.sub(r'^OEM\s+', '', t0[t0['side'] + '_conn_name'] or c))[0]
        title = '%s  %s' % (code, info.get('name') or short(nm, 40))
        if code == 'C11' and 'clutch' not in c.lower():
            title = 'C11  (cluster-side plug, code check)'
        if info.get('doc'):
            info['src'] = {'doc': info['doc'], 'page': info['page'], 'printed': info['printed']}
        secs.append((short(title, 60), info, rows))
    out += oem_pages('OEM device plugs we tap', 'Factory component connectors (the leads stay on the car). Source pages: 1993 EWD wiring routing, in the repair-manual app.',
                     None, None, secs)
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
    if h in ('ECU-engine', 'EngineRoom-C', 'WheelSpeed-Front'):
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


def build_pages(conns, order, taps):
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
    for b in oem_blocks(taps):
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
    conns, order, taps = load()
    pages = build_pages(conns, order, taps)
    ih = inputs_hash()
    N = len(pages) + 1
    doc = fitz.open()
    # page 1: title block + index
    pg = Pg(doc)
    pg.rect(MX, MX, PW - 2 * MX, PH - BOT - MX - 2, fill=None, lw=1.2)
    pg.text(MX + 14, 60, 'ST185 CELICA - CONNECTOR ATLAS', 26, True)
    pg.text(MX + 14, 82, 'Every connector of all 15 harnesses, and every OEM junction box / plug we splice into.', 11, False, '#333333')
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
                            'OEM pages: header = factory box + link to its location page in the repair-manual app; left = real plug face view; '
                            'row = pin, factory wire colour, factory signal (FSM/EWD), then OUR wire, colour, harness and leg to grab.',
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
