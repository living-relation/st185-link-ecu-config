"""Sheet 1: the three fuse box assemblies (POWER box, LOGIC box, battery relay block) as ONE block diagram.

Overhead block view, NOT to scale. Every wire is one line from its cavity to its other end; a wire that leaves the assembly
ends at a stub that names, in the R156 form, where THAT end lands. Positions are laid out for readability: rows of the same
kind keep their cavity numbers (printed on every part), but their order is not the physical order.
"""
import wd_data as D
from wd_svg import Svg, INK, GRID, BOXFILL, PARTFILL, WIRE, est_w, wrap

W = 412.0
XL_EDGE, XR_EDGE = 104.0, 308.0          # left / right edge of the assembly outlines
XL_TXT, XR_TXT = 98.0, 314.0             # label anchor (right-aligned on the left, left-aligned on the right)
LBL_W = 92.0
PITCH = 9.6                              # one exit label (3 lines)
FS_ID, FS_TXT, FS_PIN, FS_PART = 2.35, 2.15, 1.9, 2.3


class Sheet:
    def __init__(self, ents, wires, fuses):
        self.ents, self.fuses = ents, fuses
        self.wires = {w['id']: w for w in wires}
        self.pin = {}                     # (ent, handle) -> (x, y)
        self.drawn = set()
        self.exits = []                   # (side, y, wire id)
        self.svg = None
        self.late = []                    # wires drawn after the parts (cross / internal)

    # ------------------------------------------------------------------ small helpers
    def wire_for(self, ent, handle):
        out = [w for w in self.wires.values() if any(e['ent'] == ent and e['handle'] == handle for e in w['ends'])]
        return out

    def label_lines(self, w, far):
        head = '%s | %s | %s' % (w['id'], D.gauge_text(w), D.colour_text(w))
        return [(head, True)] + [(t, False) for t in wrap('-> ' + D.short(far, 200), LBL_W, FS_TXT, max_lines=2)]

    def exit_wire(self, side, px, py, wid, this_ent, far_override=None, slot_y=None, split_x=None):
        """A wire that leaves the assembly: line from the pin to the stub, 3-line label beyond it. With slot_y the wire
        dog-legs (vertical run at split_x) to its own label slot so several wires on one pin do not overlap."""
        w = self.wires[wid]
        self.drawn.add(wid)
        far_end = next(e for e in w['ends'] if not (e['ent'] == this_ent[0] and e['handle'] == this_ent[1]))
        far = far_override or D.far_text(far_end)
        x_end = XL_TXT if side == 'L' else XR_TXT - 2
        if slot_y is None:
            pts = [(px, py), (x_end, py)]
            ly = py
        else:
            pts = [(px, py), (split_x, py), (split_x, slot_y), (x_end, slot_y)]
            ly = slot_y
        self.svg.wire(pts, w['colour'])
        lines = self.label_lines(w, far)
        n = len(lines)
        y0 = ly - (n - 1) * 1.3 + 0.6
        for i, (t, b) in enumerate(lines):
            if side == 'L':
                self.svg.text(XL_TXT - 1.5, y0 + i * 2.6, t, FS_ID if b else FS_TXT, 'end', bold=b)
            else:
                self.svg.text(XR_TXT, y0 + i * 2.6, t, FS_ID if b else FS_TXT, 'start', bold=b)

    def route(self, wid, pts, label_at=None, label_dy=-1.9, anchor='middle'):
        """Internal / cross-box wire along explicit waypoints, with a short wire label."""
        w = self.wires[wid]
        self.drawn.add(wid)
        self.svg.wire(pts, w['colour'])
        self.late.append((wid, pts, label_at, label_dy, anchor))

    def flush_labels(self):
        for wid, pts, at, dy, anchor in self.late:
            w = self.wires[wid]
            if at is None:
                # longest segment
                best = max(range(len(pts) - 1), key=lambda i: abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]))
                a, b = pts[best], pts[best + 1]
                at = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, abs(b[1] - a[1]) > abs(b[0] - a[0]))
            x, y, vertical = at
            t1 = w['id']
            t2 = '%s %s' % (D.gauge_text(w), D.colour_text(w))
            if vertical:
                self.svg.text(x - 1.4, y, t1, 1.7, 'middle', rot=-90, fill='#222')
                self.svg.text(x + 2.3, y, t2, 1.7, 'middle', rot=-90, fill='#222')
            else:
                self.svg.text(x, y + dy - 2.0, t1, 1.7, anchor, fill='#222', bold=True)
                self.svg.text(x, y + dy, t2, 1.7, anchor, fill='#222')

    def part_box(self, x, y, w, h, title, sub=None, fill=PARTFILL):
        self.svg.rect(x, y, w, h, fill=fill, stroke=INK, sw=0.4, rx=0.8)
        if title:
            self.svg.text(x + w / 2, y + 3.2, title, FS_PART, 'middle', bold=True)
        if sub:
            self.svg.text(x + w / 2, y + 5.9, sub, 1.7, 'middle', fill='#444')

    def pin_dot(self, ent, handle, x, y, label, side):
        """Pin dot with its label inside the part (side 'L' = on the left edge, label to the right of the edge)."""
        self.pin[(ent, handle)] = (x, y)
        self.svg.circle(x, y, 0.8, fill=INK)
        if side == 'L':
            self.svg.text(x + 1.5, y + 0.7, label, FS_PIN)
        elif side == 'R':
            self.svg.text(x - 1.5, y + 0.7, label, FS_PIN, 'end')
        elif side == 'T':
            self.svg.text(x, y + 3.0, label, FS_PIN, 'middle')
        else:
            self.svg.text(x, y - 1.6, label, FS_PIN, 'middle')

    def box_outline(self, x0, y0, x1, y1, title, sub):
        self.svg.rect(x0, y0, x1 - x0, y1 - y0, fill=BOXFILL, stroke=INK, sw=0.7, rx=2.0, layer='back')
        self.svg.text(x0 + 3, y0 + 5.5, title, 3.6, bold=True)
        self.svg.text(x0 + 3, y0 + 9.4, sub, 2.1, fill='#334')


# ====================================================================================================== POWER box
PN = {'k_htr': '1-1414687-0', 'k_efi': '1-1414147-0', 'k_str': '1-1414147-0', 'k_fan': '1-1414147-0', 'k_fan2': '1-1393304-0', 'k_pwr': '1-1393304-0'}


def build_power(sh, top):
    sv = sh.svg
    by_in = {f['name']: f for f in sh.fuses['POWER_IN']}
    ids_in = [by_in[n] for n in ('STR', 'FAN', 'FAN2', 'PWR', 'HTR', 'EFI')]
    by_out = {f['name']: f for f in sh.fuses['POWER_OUT']}
    ids_out = [by_out[n] for n in ('RTR', 'AM1', 'AM2', 'JB1', 'EPS', 'BUS1')]
    relay_of = {'HTR': 'k_htr', 'EFI': 'k_efi', 'STR': 'k_str', 'FAN': 'k_fan', 'FAN2': 'k_fan2', 'PWR': 'k_pwr'}
    rnames = {'k_htr': 'R1 heater 1-form-C', 'k_efi': 'R2 EFI main', 'k_str': 'R3 starter', 'k_fan': 'R4 radiator fan',
              'k_fan2': 'R5 condenser fan', 'k_pwr': 'R6 power window'}
    x_rel, x_fin, x_bar, x_fout = 122.0, 190.0, 227.0, 240.0
    y_first = top + 30
    row_h = 33.0
    rows = {}
    for i, f in enumerate(ids_in):
        y = y_first + i * row_h
        rows[i] = y
        rid = relay_of[f['name']]
        # relay (outward pins 30 / 85 / 86 on the left edge, 87 / 87a on the right)
        sh.part_box(x_rel, y - 14, 32, 28, rid, rnames[rid])
        sv.text(x_rel + 16, y + 11.5, 'TE ' + PN[rid], 1.7, 'middle', fill='#444')
        
        for pin, dy, hid in (('30', -8.8, 'c1'), ('85', 0, 'c2'), ('86', 8.8, 'c3')):
            sh.pin_dot(rid, hid, x_rel, y + dy, pin, 'L')
        sh.pin_dot(rid, 'c4', x_rel + 32, y, '87', 'R')
        if rid == 'k_htr':
            sh.pin_dot(rid, 'c5', x_rel + 32, y + 8.8, '87a', 'R')
        # IN fuse
        sh.part_box(x_fin, y - 4.5, 24, 9, None)
        sv.text(x_fin + 12, y - 0.4, '%s %s A' % (f['des'].replace('AMI ', ''), f['amps']), 2.0, 'middle', bold=True)
        sv.text(x_fin + 12, y + 2.8, f['name'], 1.9, 'middle')
        sh.pin_dot('fb_power', f['cav'], x_fin, y, '', 'L')
        sv.line(x_fin + 24, y, x_bar, y, sw=0.8, stroke='#555')
    # bar
    y_bar0, y_bar1 = rows[0] - 8, rows[5] + 10
    sv.rect(x_bar - 1.2, y_bar0, 2.4, y_bar1 - y_bar0, fill='#b87333', stroke='#5a3510', sw=0.3)
    sv.text(x_bar, y_bar0 - 2.5, '+ BAR', 2.1, 'middle', bold=True)
    # OUT fuses
    outs = {f['name']: f for f in ids_out}
    for i, f in enumerate(ids_out):
        y = rows[i]
        sv.line(x_bar, y, x_fout, y, sw=0.8, stroke='#555')
        sh.part_box(x_fout, y - 4.5, 24, 9, None)
        sv.text(x_fout + 12, y - 0.4, '%s %s A' % (f['des'].replace('AMI ', ''), f['amps']), 2.0, 'middle', bold=True)
        sv.text(x_fout + 12, y + 2.8, f['name'], 1.9, 'middle')
        sh.pin_dot('fb_power', f['cav'], x_fout + 24, y, '', 'R')
    # ACPS mini fuse
    y_acps = rows[5] + row_h
    sh.part_box(x_fin - 4, y_acps - 4.5, 32, 9, None)
    sv.text(x_fin + 12, y_acps - 0.4, 'ACPS 10 A', 2.0, 'middle', bold=True)
    sv.text(x_fin + 12, y_acps + 2.8, 'mini ATM', 1.9, 'middle')
    sh.pin_dot('fb_power', 'acps_in', x_fin - 4, y_acps, 'IN', 'L')
    sh.pin_dot('fb_power', 'acps', x_fin + 28, y_acps, 'OUT', 'R')
    # studs: POS (BAT+, ALT/STR) and NEG bar (GND); their six exits stack on the right
    y_pos = y_acps + 24
    bx0, bx1 = x_fin - 16, x_fin + 76
    sh.part_box(bx0, y_pos - 7, bx1 - bx0, 14, None)
    sv.text(bx0 + 2, y_pos - 1.2, 'POWER + bar: M8 studs', 2.0, bold=True)
    sv.text(bx0 + 2, y_pos + 2.6, '(1/0 battery cable in; alternator / starter out)', 1.7, fill='#444')
    sh.pin_dot('pdb', 'c1', bx1, y_pos - 3.5, 'BAT+ c1', 'R')
    sh.pin_dot('pdb', 'c2', bx1, y_pos + 3.5, 'ALT/STR c2', 'R')
    sv.rect(x_bar - 1.2, y_bar1, 2.4, y_pos - 7 - y_bar1, fill='#b87333', stroke='#5a3510', sw=0.3)
    y_neg = y_pos + 32
    sh.part_box(bx0, y_neg - 7, bx1 - bx0, 14, None, fill='#e9edf3')
    sv.text(bx0 + 2, y_neg - 1.2, 'POWER NEG bar: M8 ground studs', 2.0, bold=True)
    sh.pin_dot('t_pdb_gnd_htr', 'x', bx0 + 8, y_neg - 7, 'k_htr 87a', 'T')
    sh.pin_dot('t_pdb_gnd_pwr', 'x', bx0 + 30, y_neg - 7, 'k_pwr 85', 'T')
    sh.pin_dot('t_pdb_gnd_rev', 'x', bx0 + 66, y_neg + 7, 'k_rev 85 (LOGIC)', 'B')
    sh.pin_dot('pdb', 'c8', bx1, y_neg, 'GND c8', 'R')
    bottom = y_neg + 38
    sh.box_outline(XL_EDGE, top, XR_EDGE, bottom, 'POWER BOX', 'glove box, outboard - AMI fuse bar (IN row feeds the relays, OUT row feeds the cabin) - rev 7')
    sh.rows_power = dict(bx0=bx0, bx1=bx1, rows=rows, y_acps=y_acps, y_pos=y_pos, y_neg=y_neg, x_rel=x_rel, x_fin=x_fin, x_bar=x_bar, x_fout=x_fout)
    return bottom


def route_power(sh):
    sv = sh.svg
    p = sh.pin
    r = sh.rows_power
    # IN fuse -> relay 87 (straight)
    for (fuse, rid, wid) in (('in1', 'k_htr', 'w_htr_87_cp'), ('in2', 'k_efi', 'w_fb_k_efi_87_cp'), ('in3', 'k_str', 'w_fb_k_str_87_cp'),
                             ('in4', 'k_fan', 'w_fb_k_fan_87_cp'), ('in5', 'k_fan2', 'w_fb_k_fan2_87_ac'), ('in6', 'k_pwr', 'w_pwr_87_cp')):
        a, b = p[('fb_power', fuse)], p[(rid, 'c4')]
        sh.route(wid, [b, a], label_dy=-1.2)
    # grounds to the NEG bar
    a, b = p[('k_pwr', 'c2')], p[('t_pdb_gnd_pwr', 'x')]
    yb = b[1] - 10
    sh.route('w_pwr_85_cp', [a, (a[0] - 5, a[1]), (a[0] - 5, yb), (b[0], yb), b], label_at=((a[0] - 5 + b[0]) / 2 + 8, yb, False), label_dy=-0.5)
    a, b = p[('k_htr', 'c5')], p[('t_pdb_gnd_htr', 'x')]
    yb = b[1] - 6
    sh.route('w_htr_87a_cp', [a, (a[0] + 5, a[1]), (a[0] + 5, yb), (b[0], yb), b], label_at=(a[0] + 5, rows_mid(sh), True))
    # exits: relay left pins
    for rid in ('k_htr', 'k_efi', 'k_str', 'k_fan', 'k_fan2', 'k_pwr'):
        for hid in ('c1', 'c2', 'c3'):
            for w in sh.wire_for(rid, hid):
                if w['id'] in sh.drawn or w['id'] in CROSS_POWER or w['id'] in ('w_pwr_85_cp',):
                    continue
                px, py = p[(rid, hid)]
                sh.exit_wire('L', px, py, w['id'], (rid, hid))
    # exits: OUT fuses
    for f in sh.fuses['POWER_OUT']:
        for w in sh.wire_for('fb_power', f['cav']):
            if w['id'] in sh.drawn or w['id'] in CROSS_POWER:
                continue
            px, py = p[('fb_power', f['cav'])]
            sh.exit_wire('R', px, py, w['id'], ('fb_power', f['cav']))
    for hid in ('acps_in', 'acps'):
        for w in sh.wire_for('fb_power', hid):
            px, py = p[('fb_power', hid)]
            sh.exit_wire('L' if hid == 'acps_in' else 'R', px, py, w['id'], ('fb_power', hid))
    slots = []
    k = 0
    base = r['y_pos'] - 14
    for hid in ('c1', 'c2', 'c8'):
        for w in sh.wire_for('pdb', hid):
            px, py = p[('pdb', hid)]
            sh.exit_wire('R', px, py, w['id'], ('pdb', hid), slot_y=base + k * PITCH, split_x=px + 5 + 2.2 * k)
            k += 1


def rows_mid(sh):
    r = sh.rows_power["rows"]
    return (r[1] + r[3]) / 2 + 20


CROSS_POWER = {"w_hc_fb", "w77_cp", "w_k_efi_86_cp", "w_rev_85_cp"}
