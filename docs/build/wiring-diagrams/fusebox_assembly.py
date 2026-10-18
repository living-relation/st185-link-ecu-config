"""Sheet 1, part 2: the LOGIC box, the battery relay block and the page assembly (POWER box is in fusebox_sheet.py)."""
import wd_data as D
from wd_svg import Svg, INK
from fusebox_sheet import (Sheet, build_power, route_power, W, XL_EDGE, XR_EDGE, PITCH)

LB = dict(rl=110.0, rw=28.0, f1=176.0, fw=22.0, s1=206.0, s2=218.0, f2=226.0, rr=276.0)
PN = {'k_hl': '5-1393292-8', 'k_hr': '5-1393292-8', 'k_horn': '4-1904124-3', 'k_etb': '4-1904124-2', 'k_acc': '6-1419137-4',
      'k_eps_en': '6-1419137-4', 'k_rev': '6-1419137-4'}
CROSS_LOGIC = {'w_hc_fb', 'w77_cp', 'w_k_efi_86_cp', 'w_rev_85_cp'}


def fuse_box(sh, x, y, f):
    sv = sh.svg
    sh.part_box(x, y - 4.5, LB['fw'], 9, None)
    sv.text(x + LB['fw'] / 2, y - 0.5, '%s %s A' % (f['des'], f['amps']), 1.8, 'middle', bold=True)
    sv.text(x + LB['fw'] / 2, y + 2.8, f['name'], 1.9, 'middle')


def relay_box(sh, rid, title, side, y_top, ext, intl, int_gap=5.0, min_h=24.0):
    """Micro relay. ext = [(handle, pin)] on the outward edge, intl = [(handle, pin)] on the inward edge.
    Returns (rect height, y of the middle)."""
    n = max(len(ext), 1)
    h = max(14 + (n - 1) * 8.8, min_h)
    x = LB['rl'] if side == 'L' else LB['rr']
    sh.part_box(x, y_top, LB['rw'], h, rid, title)
    sh.svg.text(x + LB['rw'] / 2, y_top + 8.4, 'TE ' + PN[rid], 1.6, 'middle', fill='#444')
    mid = y_top + h / 2
    xo, xi = (x, x + LB['rw']) if side == 'L' else (x + LB['rw'], x)
    for i, (hid, pin) in enumerate(ext):
        y = mid + (i - (len(ext) - 1) / 2) * 8.8
        sh.pin_dot(rid, hid, xo, y, pin, 'L' if side == 'L' else 'R')
    for i, (hid, pin) in enumerate(intl):
        y = mid + (i - (len(intl) - 1) / 2) * (int_gap if len(intl) > 1 else 0)
        sh.pin_dot(rid, hid, xi, y, pin, 'R' if side == 'L' else 'L')
    return h, mid


def build_logic(sh, top):
    sv = sh.svg
    byn = {(f['bus'], f['name']): f for f in sh.fuses['LOGIC'] if not f['is_in']}
    pos = {}

    def fuse_pins(f, x_out, x_in, y):
        sh.pin_dot('fb_logic', f['cav'], x_out, y, '', 'L')
        sh.pin_dot('fb_logic_in', f['cav'], x_in, y, '', 'R')

    # ---------------- left column: EFI86 fuse, relay band (HL, HR, ETB), exit fuses
    y = top + 24
    f = byn[('BUS1', 'EFI86')]
    fuse_box(sh, LB['f1'], y, f)
    fuse_pins(f, LB['f1'], LB['f1'] + LB['fw'], y)
    pos['b1_first'] = y
    y += 12
    band = {}
    for rid, title, nm, ext, intl in (('k_hl', 'HEAD LH', 'HL', [('c2', '85'), ('c4', '87')], [('c1', '30'), ('c3', '86')]),
                                      ('k_hr', 'HEAD RH', 'HR', [('c2', '85'), ('c4', '87')], [('c1', '30'), ('c3', '86')]),
                                      ('k_etb', 'ETB power', 'ETB', [('c2', '85'), ('c3', '86'), ('c4', '87')], [('c1', '30')])):
        h, mid = relay_box(sh, rid, title, 'L', y, ext, intl, int_gap=(16.0 if rid in ('k_hl', 'k_hr') else 5.0), min_h=(30.0 if rid in ('k_hl', 'k_hr') else 24.0))
        f = byn[('BUS1', nm)]
        fuse_box(sh, LB['f1'], mid, f)
        fuse_pins(f, LB['f1'], LB['f1'] + LB['fw'], mid)
        band[rid] = (y, h, mid)
        y += h + 5
    for nm in ('HZ', 'DM', 'WL', 'ALM', 'ALMS', 'ALTS'):
        f = byn[('BUS1', nm)]
        fuse_box(sh, LB['f1'], y + 4, f)
        fuse_pins(f, LB['f1'], LB['f1'] + LB['fw'], y + 4)
        pos['b1_last'] = y + 4
        y += PITCH
    left_bottom = y
    pos['band_l'] = band
    # ---------------- right column: relays (REV, HORN, ACC, EPS EN), MRS, exit fuses, B30
    y = top + 24
    for rid, title, nm, ext, intl in (('k_rev', 'REVERSE', None, [('c1', '30'), ('c2', '85'), ('c3', '86'), ('c4', '87')], []),
                                      ('k_horn', 'HORN', None, [('c1', '30'), ('c2', '85'), ('c3', '86'), ('c4', '87')], []),
                                      ('k_acc', 'A/C clutch', 'ACC', [('c2', '85'), ('c3', '86'), ('c4', '87')], [('c1', '30')]),
                                      ('k_eps_en', 'EPS enable', 'EPSEN', [('c2', '85'), ('c3', '86')], [('c1', '30'), ('c4', '87')])):
        h, mid = relay_box(sh, rid, title, 'R', y, ext, intl)
        if nm:
            f = byn[('BUS2', nm)]
            yf = sh.pin[(rid, 'c1')][1]
            fuse_box(sh, LB['f2'], yf, f)
            sh.pin_dot('fb_logic_in', f['cav'], LB['f2'], yf, '', 'L')
            sh.pin_dot('fb_logic', f['cav'], LB['f2'] + LB['fw'], yf, '', 'R')
            pos.setdefault('b2_first', yf)
        band[rid] = (y, h, mid)
        y += h + 5
    f = byn[('BUS2', 'MRS')]
    ym = y + 8
    sh.part_box(LB['f2'], ym - 8.5, LB['fw'], 17, None)
    sv.text(LB['f2'] + LB['fw'] / 2, ym - 0.5, '%s %s A' % (f['des'], f['amps']), 1.8, 'middle', bold=True)
    sv.text(LB['f2'] + LB['fw'] / 2, ym + 2.8, 'MRS', 1.9, 'middle')
    sh.pin_dot('fb_logic', 'mrsin', LB['f2'] + LB['fw'], ym - 4.4, 'IN', 'R')
    sh.pin_dot('fb_logic', 'mrs', LB['f2'] + LB['fw'], ym + 4.4, 'OUT', 'R')
    y = ym + 8.5 + 5
    for nm in ('LAM', 'SW12', 'COP', 'INJ', 'CSB', 'DEV', 'ALMIG'):
        f = byn[('BUS2', nm)]
        fuse_box(sh, LB['f2'], y + 4, f)
        sh.pin_dot('fb_logic_in', f['cav'], LB['f2'], y + 4, '', 'L')
        sh.pin_dot('fb_logic', f['cav'], LB['f2'] + LB['fw'], y + 4, '', 'R')
        y += PITCH
    f = byn[('BUS2', 'B30')]
    y += 6
    ym = y + 8
    sh.part_box(LB['f2'], ym - 8.5, LB['fw'], 17, None)
    sv.text(LB['f2'] + LB['fw'] / 2, ym - 0.5, '%s %s A' % (f['des'], f['amps']), 1.8, 'middle', bold=True)
    sv.text(LB['f2'] + LB['fw'] / 2, ym + 2.8, 'B30', 1.9, 'middle')
    sh.pin_dot('fb_logic', 'b30in', LB['f2'] + LB['fw'], ym - 4.4, 'IN', 'R')
    sh.pin_dot('fb_logic', 'b30', LB['f2'] + LB['fw'], ym + 4.4, 'OUT', 'R')
    pos['b2_last'] = ym
    y = ym + 8.5 + 4
    bottom = max(left_bottom, y) + 6
    for nm, xs, y0, y1, hid in (('BUS 1 (permanent)', LB['s1'], pos['b1_first'] - 9, pos['b1_last'] + 6, 'b1'),
                                ('BUS 2 (switched, k_efi 30)', LB['s2'], pos['b2_first'] - 9, pos['b2_last'] + 9, 'b2')):
        sv.rect(xs - 1.2, y0, 2.4, y1 - y0, fill='#b87333', stroke='#5a3510', sw=0.3)
        sv.text(xs + (-2.6 if hid == 'b1' else 3.8), (y0 + y1) / 2, nm + ' strip', 2.0, 'middle', rot=-90, bold=True)
        sh.pin[('fb_logic', hid)] = (xs, y0)
        sv.circle(xs, y0, 0.9, fill=INK)
    sh.box_outline(XL_EDGE, top, XR_EDGE, bottom, 'LOGIC BOX', 'glove box, inboard - Bus 1 / Bus 2 mini-fuse strips and 7 micro relays - rev 7')
    sh.logic_pos = pos
    return bottom


def route_logic(sh):
    sv = sh.svg
    p = sh.pin
    pos = sh.logic_pos
    for f in sh.fuses['LOGIC']:
        if f['is_in']:
            continue
        a = p.get(('fb_logic_in', f['cav']))
        if not a:
            continue
        xs = LB['s1'] if f['bus'] == 'BUS1' else LB['s2']
        sv.thin([a, (xs, a[1])], stroke='#7a5a2a', sw=0.35, dash='1.2 0.8')
    for rid, wf, w30, w86, nm in (('k_hl', 'w_hl_cp', 'w_hl_30_cp', 'w_hl_86_cp', 'HL'), ('k_hr', 'w_hr_cp', 'w_hr_30_cp', 'w_hr_86_cp', 'HR')):
        y0, h, mid = pos['band_l'][rid]
        f = next(f for f in sh.fuses['LOGIC'] if not f['is_in'] and f['bus'] == 'BUS1' and f['name'] == nm)
        a = p[('fb_logic', f['cav'])]
        xd = LB['rl'] + LB['rw'] + 10
        sv.circle(xd, mid, 1.1, fill=INK, layer='over')
        sh.route(wf, [a, (xd, mid)], label_at=((a[0] + xd) / 2, mid, False))
        c30, c86 = p[(rid, 'c1')], p[(rid, 'c3')]
        sh.route(w30, [(xd, mid), (xd, c30[1]), c30], label_at=(LB['rl'] + LB['rw'] + 2, c30[1], False), label_dy=-1.4, anchor='start')
        sh.route(w86, [(xd, mid), (xd, c86[1]), c86], label_at=(LB['rl'] + LB['rw'] + 2, c86[1], False), label_dy=6.2, anchor='start')
        sv.text(xd + 1.8, mid + 3.6, 'sp_' + rid[2:], 1.6, fill='#222')
    f = next(f for f in sh.fuses['LOGIC'] if not f['is_in'] and f['bus'] == 'BUS1' and f['name'] == 'ETB')
    sh.route('w_fb_k_etb_30_cp', [p[('fb_logic', f['cav'])], p[('k_etb', 'c1')]])
    for wid, nm, rid in (('w_fb_k_acc_30_cp', 'ACC', 'k_acc'), ('w_fb_k_eps_en_30_cp', 'EPSEN', 'k_eps_en')):
        f = next(f for f in sh.fuses['LOGIC'] if not f['is_in'] and f['bus'] == 'BUS2' and f['name'] == nm)
        sh.route(wid, [p[('fb_logic', f['cav'])], p[(rid, 'c1')]])
    a, b = p[('k_eps_en', 'c4')], p[('fb_logic', 'mrsin')]
    xl = (LB['f2'] + LB['fw'] + LB['rr']) / 2
    sh.route('w_k_eps_en_87_cp', [a, (xl, a[1]), (xl, b[1]), b], label_at=(xl, (a[1] + b[1]) / 2 + 2, True))
    for f in sh.fuses['LOGIC']:
        if f['is_in'] and f['cav'] not in ('mrsin', 'b30in'):
            continue
        hid = f['cav']
        side = 'L' if f['bus'] == 'BUS1' else 'R'
        for w in sh.wire_for('fb_logic', hid):
            if w['id'] in sh.drawn or w['id'] in CROSS_LOGIC:
                continue
            px, py = p[('fb_logic', hid)]
            sh.exit_wire(side, px, py, w['id'], ('fb_logic', hid))
    for rid, side in (('k_hl', 'L'), ('k_hr', 'L'), ('k_etb', 'L'), ('k_rev', 'R'), ('k_horn', 'R'), ('k_acc', 'R'), ('k_eps_en', 'R')):
        for hid in ('c1', 'c2', 'c3', 'c4'):
            for w in sh.wire_for(rid, hid):
                if w['id'] in sh.drawn or w['id'] in CROSS_LOGIC:
                    continue
                px, py = p[(rid, hid)]
                sh.exit_wire(side, px, py, w['id'], (rid, hid))


def build_batt(sh, top):
    sv = sh.svg
    y = top + 30
    x_stud, x_fuse, x_rel = 132.0, 178.0, 240.0
    sh.part_box(x_stud, y - 8, 30, 16, None)
    sv.text(x_stud + 15, y - 1.2, 'BATT+ stud', 2.0, 'middle', bold=True)
    sv.text(x_stud + 15, y + 2.6, 'M6 on the bar', 1.8, 'middle')
    sh.pin_dot('fb_batt', 'in', x_stud, y, '', 'L')
    sv.line(x_stud + 30, y, x_fuse, y, sw=0.8, stroke='#b87333')
    sh.part_box(x_fuse, y - 6, 34, 12, None)
    sv.text(x_fuse + 17, y - 0.8, 'AMI FP 40 A', 2.0, 'middle', bold=True)
    sv.text(x_fuse + 17, y + 3.0, 'fuel pump fuse', 1.8, 'middle')
    sh.pin_dot('fb_batt', 'fp', x_fuse + 34, y, '', 'R')
    sh.part_box(x_rel, y - 12, 42, 44, 'k_fp', 'HCR150 fuel pump relay')
    sv.text(x_rel + 21, y + 8.5, 'TE 1416010-1', 1.7, 'middle', fill='#444')
    sh.pin_dot('k_fp', 'c1', x_rel, y, '30', 'L')
    sh.pin_dot('k_fp', 'c2', x_rel, y + 14, '85', 'L')
    sh.pin_dot('k_fp', 'c3', x_rel, y + 23, '86', 'L')
    sh.pin_dot('k_fp', 'c4', x_rel + 42, y, '87', 'R')
    bottom = y + 40
    sh.box_outline(XL_EDGE, top, XR_EDGE, bottom, 'BATTERY RELAY BLOCK',
                   'trunk, passenger side between the rear wall and the battery - fuel pump relay and its fuse (rev 7)')
    return bottom


def route_batt(sh):
    p = sh.pin
    a = p[('fb_batt', 'fp')]
    sh.route('w_fp_30', [a, (a[0] + 8, a[1]), p[('k_fp', 'c1')]])
    for hid, side in (('c2', 'L'), ('c3', 'L'), ('c4', 'R')):
        for w in sh.wire_for('k_fp', hid):
            if w['id'] in sh.drawn:
                continue
            px, py = p[('k_fp', hid)]
            sh.exit_wire(side, px, py, w['id'], ('k_fp', hid))
    for w in sh.wire_for('fb_batt', 'in'):
        px, py = p[('fb_batt', 'in')]
        sh.exit_wire('L', px, py, w['id'], ('fb_batt', 'in'))


def build(ents, wires, fuses):
    sh = Sheet(ents, wires, fuses)
    sh.svg = Svg(W, 800.0, 'ST185 fuse box assemblies - wiring block diagram')
    sv = sh.svg
    bot_p = build_power(sh, 34.0)
    top_l = bot_p + 26
    bot_l = build_logic(sh, top_l)
    bot_b = build_batt(sh, bot_l + 14)
    route_power(sh)
    route_logic(sh)
    route_batt(sh)
    p = sh.pin
    g1, g2 = bot_p + 9, bot_p + 17
    a = p[('k_efi', 'c1')]
    b2 = p[('fb_logic', 'b2')]
    sh.route('w77_cp', [a, (a[0] - 8, a[1]), (a[0] - 8, g2), (b2[0], g2), b2], label_at=(150, g2, False), label_dy=-0.6)
    e86 = p[('fb_logic', 'efi86')]
    c3 = p[('k_efi', 'c3')]
    sh.route('w_k_efi_86_cp', [e86, (a[0] - 5.5, e86[1]), (a[0] - 5.5, c3[1]), c3], label_at=(a[0] - 5.5, (e86[1] + bot_p) / 2 + 20, True))
    o1 = p[('fb_power', 'out1')]
    b1 = p[('fb_logic', 'b1')]
    sh.route('w_hc_fb', [o1, (o1[0] + 9, o1[1]), (o1[0] + 9, g1), (b1[0], g1), b1], label_at=(236, g1, False), label_dy=-0.6)
    k85 = p[('k_rev', 'c2')]
    gn = p[('t_pdb_gnd_rev', 'x')]
    yd = gn[1] + 7
    sh.route('w_rev_85_cp', [k85, (k85[0] + 3, k85[1]), (k85[0] + 3, yd), (gn[0], yd), gn], label_at=(k85[0] + 3, (yd + k85[1]) / 2 + 40, True))
    sh.flush_labels()
    ly = bot_b + 12
    sv.text(XL_EDGE, ly, 'How to read', 2.8, bold=True)
    sv.wire([(XL_EDGE, ly + 5), (XL_EDGE + 14, ly + 5)], 'Red')
    sv.text(XL_EDGE + 17, ly + 5.8, 'one wire, drawn in its insulation colour; the label is "wire id | gauge | colour (ident bands)"', 2.1)
    sv.text(XL_EDGE, ly + 11, 'A line that crosses another with a gap does not connect to it. A dot is a pin or stud. The brown bar is a copper bus bar / strip.', 2.1)
    sv.text(XL_EDGE, ly + 16, 'A wire that leaves the assembly ends at the stub; the text after "->" is where that far end lands (DECISIONS R156). Overhead block view, not to scale.', 2.1)
    sv.text(XL_EDGE, ly + 21, 'Rows are grouped for readable wires, not in physical order: every fuse and relay carries its cavity number (BUS1-n, BUS2-n, AMI IN-n, AMI OUT-n).', 2.1)
    sv.h = ly + 28
    sh.cuts = [(0, bot_p + 28), (bot_p + 14, bot_l + 18), (bot_l + 2, sv.h)]
    sv.text(XL_EDGE, 14, 'ST185 FUSE BOX ASSEMBLIES - WIRING BLOCK DIAGRAM', 5.0, bold=True)
    sv.text(XL_EDGE, 21, 'POWER box + LOGIC box (glove box) and battery relay block (trunk). Sources: sot/channels.csv, cad/fusebox/src/spec.py, docs/harness/interfaces.json.', 2.2)
    sv.text(XL_EDGE, 26.5, 'Generated by docs/build/wiring-diagrams/build_wiring_diagrams.py - do not edit by hand.', 2.0, fill='#555')
    sv.text(W - 10, 14, 'FRONT of car', 2.4, 'end', bold=True)
    sv.line(W - 40, 20, W - 10, 20, sw=0.5)
    return sh
