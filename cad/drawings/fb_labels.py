"""Fuse box label data for the assembly drawings (DECISIONS R189 / R190), from the source-of-truth chain, never invented:
  - fuse and relay names: cad/fusebox/src/spec.py (MINI_COLS fuse positions, MICRO_POS micro relay positions)
  - what each one serves and every harness wire that lands in the box: cad/fusebox/rev7/wiring_plan.json (wiring_sim.py, read from
    the docs/harness/rebuild/*.harness files) for the cavity and the far end; the far end's printed name is the SHORT name the harness
    drawing shows (the .harness file itself: a terminal / splice `label`, or a connector's label + cavity designation + signal; R124 /
    R156), so the drawing says what the harness drawing says.
The LOGIC box sits at the assembly origin (box-local = assembly mm, checked 2026-10-18: every fuse and relay solid of
ST185_fusebox_rev7_assembly.step is at its spec.py position). The battery relay block lugs are matched to their wire by position.
Claude Code, 2026-10-18."""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'cad', 'fusebox', 'src'))
import spec as S  # noqa: E402

PLAN = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wiring_plan.json')
REB = os.path.join(REPO, 'docs', 'harness', 'rebuild')
RELAY_NAMES = {'HEAD LH': 'k_hl', 'HEAD RH': 'k_hr', 'horn': 'k_horn'}
PIN = {'c1': '30', 'c2': '85', 'c3': '86', 'c4': '87', 'c5': '87a'}


def _harness_names():
    """(drawing, id) -> short printed name of every terminal / splice / connector cavity in the harness drawings (an id can be in two
    drawings - each side of a broken-off wire - so names are kept per drawing)."""
    out = {}
    for fn in sorted(glob.glob(os.path.join(REB, '*.harness'))):
        d = json.load(open(fn, encoding='utf-8'))
        f = os.path.basename(fn)[6:-8]
        for t in d.get('terminals', []) + d.get('splices', []):
            if t.get('label'):
                out[(f, t['id'])] = t['label']
        for c in d.get('connectors', []):
            nm = c.get('label') or c.get('name') or c['id']
            for cv in c.get('cavities', []):
                txt = nm + ' ' + (cv.get('designation') or cv['id'])
                if cv.get('signal'):
                    txt += ' - ' + cv['signal']
                out[(f, c['id'], cv['id'])] = txt
    return out


def _far(w, e, names):
    o = [x for x in w['ends'] if x is not e]
    if not o:
        return None
    o = o[0]
    f = w['file']
    return names.get((f, o['id'], o['cav'])) or names.get((f, o['id'])) or (o.get('des') or o['id'])


def _wires(box):
    plan = json.load(open(PLAN, encoding='utf-8'))
    names = _harness_names()
    rows = []
    for w in plan['wires']:
        for e in w['ends']:
            if e['box'] != box or e['id'].startswith('sp_'):
                continue        # a splice in the front channel is part of the harness, not a box connection point
            far = _far(w, e, names)
            rows.append(dict(id=e['id'], cav=e['cav'], des=e['des'], at=e.get('at'), far=far, wire=w['wire'], file=w['file']))
    return rows


def _relay_pos():
    """rid -> (x, y) of each LOGIC micro relay."""
    out, k = {}, 0
    for cx in S.MICRO_COLS:
        for cy in S.MICRO_Y:
            nm, pn, _ = S.MICRO_POS[k]
            k += 1
            if pn:
                out[RELAY_NAMES.get(nm, nm)] = (cx, cy)
    return out


def logic_fuse_labels(fuse_items, z=60.0):
    """[{item, at, text}] one per LOGIC mini fuse, from spec.MINI_COLS and what its output feeds (wiring_plan)."""
    feeds = {}
    for r in _wires('LOGIC'):
        if r['id'] == 'fb_logic' and r['des'].startswith('BUS') and not r['des'].endswith('IN'):
            feeds.setdefault(r['des'], r['far'])
    out = []
    for (col, i, nm, amps, cx, y) in S.mini_list():
        des = '%s-%d' % (col, i + 1)
        a = ('%g' % amps) + 'A'
        it = fuse_items.get(amps)
        if it is None:
            continue
        out.append(dict(item=it, at=(cx, y, z), text='%s %s %s' % (des, nm, a)))
    return out


def logic_relay_labels(relay_item, z=72.0):
    rp = _relay_pos()
    serves = {'k_hl': 'HEAD LH', 'k_hr': 'HEAD RH', 'k_horn': 'HORN', 'k_etb': 'ETB POWER', 'k_acc': 'A/C CLUTCH',
              'k_eps_en': 'EPS ENABLE', 'k_rev': 'REVERSE LAMPS'}       # spec.MICRO_POS names, spelled out
    return [dict(item=relay_item, at=(x, y, z), text='%s (%s)' % (rid, serves.get(rid, rid))) for rid, (x, y) in rp.items()]


def logic_wire_labels(term_item_for, z=40.0, kind=None):
    """[{item, at, text}] one per harness wire end at a LOGIC cavity, anchored on the terminal in that cavity (seen from below).
    term_item_for(x, y) -> BOM item number of the terminal at that cavity. kind: 'fuse' or 'relay' to split the sheets."""
    out = []
    for r in _wires('LOGIC'):
        at = r['at']
        if not at:
            continue
        if r['id'] == 'fb_logic':
            here = r['des']
            if kind == 'relay':
                continue
        else:
            here = '%s %s' % (r['id'], PIN.get(r['cav'], r['cav']))
            if kind == 'fuse':
                continue
        it = term_item_for(at['x'], at['y'])
        if it is None:
            continue
        out.append(dict(item=it, at=(at['x'], at['y'], z), text='%s > %s' % (here, r['far'])))
    return out


BATT_POINTS = {   # battery relay block connection points in the assembly (lug / plug centres, ST185_fusebox_rev7_assembly.step 2026-10-18)
    ('fb_batt', 'in'): (12.85, -144.0, 46.0),     # feed lug on the M6 feed stud (bar bolt x 20)
    ('fb_batt', 'fp'): (75.39, -144.0, 46.5),     # FP 40A fuse out: lug on the pad bolt (x 68)
    ('k_fp', 'c1'): (120.82, -144.0, 46.5),       # HCR150 terminal 3 (30)
    ('k_fp', 'c4'): (153.08, -144.0, 46.5),       # HCR150 terminal 5 (87)
    ('k_fp', 'c2'): (105.6, -158.12, 34.0),       # coil plug 282080-1 (85 / 86)
    ('k_fp', 'c3'): (105.6, -158.12, 34.0),
}


def batt_wire_labels(lug_item, plug_item):
    names = _harness_names()
    out = []
    for r in _wires('BATT'):
        p = BATT_POINTS.get((r['id'], r['cav']))
        if not p:
            continue
        here = names.get((r['file'], r['id'], r['cav'])) if r['id'] == 'fb_batt' else 'k_fp %s' % PIN.get(r['cav'], r['cav'])
        out.append(dict(item=plug_item if r['cav'] in ('c2', 'c3') else lug_item, at=p, text='%s > %s' % (here, r['far'])))
    return out


# ---------- POWER box (ST185-FB-100P, 2026-10-19). Box-local + spec.PLACE['POWER'] = assembly mm (the top-nut holder solid sits at its
# spec position: checked 2026-10-19). Fuse / relay names: spec.AMI_ROWS, IN_RELAY; what each serves and every wire end: wiring_plan.json
# (the far end's printed name, as above); the bus studs: spec.REV7 pos_studs / neg_studs.
POWER_SERVES = {   # AMI position -> what its output feeds, from the far end of its wire in ST185-CabinPower (wiring_plan.json)
    'IN-1': 'HEATER RELAY k_htr', 'IN-2': 'EFI RELAY k_efi', 'IN-3': 'START RELAY k_str', 'IN-4': 'RAD FAN RELAY k_fan',
    'IN-5': 'COND FAN RELAY k_fan2', 'IN-6': 'POWER WINDOW RELAY k_pwr', 'OUT-1': 'LOGIC BOX BUS 1', 'OUT-2': 'RETRACT RELAY (IE1-3)',
    'OUT-3': 'IGNITION SW AM1 (IE1-10)', 'OUT-4': 'IGNITION SW AM2 (IE1-17)', 'OUT-5': 'J/B 1 MAIN B+ (1I-1)', 'OUT-6': 'EHPS PUMP RELAY 30'}
POWER_RELAYS = {'k_htr': 'HEATER BLOWER', 'k_efi': 'EFI', 'k_str': 'STARTER', 'k_fan': 'RADIATOR FAN', 'k_fan2': 'CONDENSER FAN',
                'k_pwr': 'POWER WINDOWS'}
GND_STUD = (('Battery negative', 'BAT-'), ('RADLOK negative', 'RADLOK-'), ('ground point ID', 'GND ID'), ('ground point IG', 'GND IG'))


def _p(x, y, z):
    px, py = S.PLACE['POWER']
    return (x + px, y + py, z)


def power_ami_points():
    """'IN-n' / 'OUT-n' -> (fuse centre, output lug centre) in assembly mm; spare positions left out."""
    st, out = S.STRAP, {}
    for row, sg in (('IN', -1), ('OUT', 1)):
        for i, (nm, a) in enumerate(S.AMI_ROWS[row]):
            if a is None:
                continue
            y = S.AMI_Y0 + i * S.AMI_PITCH
            ear = S.POWER['x_bar'] + sg * (S.AMI_IN_OFF + S.AMI['c'])
            out['%s-%d' % (row, i + 1)] = dict(name=nm, amps=a, fuse=_p(ear - sg * S.AMI['c'] / 2, y, S.POWER['bar_top'] + 4.0),
                                               lug=_p(ear + sg * st['lug'], y, st['z_bl'] - 2.0))
    return out


def power_fuse_labels():
    """[{at, text}] one per AMI fuse and the ACPS mini fuse (R189)."""
    out = [dict(at=p['fuse'], text='%s %s %dA - %s' % (k, p['name'], p['amps'], POWER_SERVES.get(k, p['name'])))
           for k, p in power_ami_points().items()]
    acps = [r['at'] for r in _wires('POWER') if r['id'] == 'fb_power' and r['cav'].startswith('acps') and r['at']]
    if acps:
        out.append(dict(at=_p(sum(a['x'] for a in acps) / len(acps), acps[0]['y'], S.POWER['bar_top']), text='ACPS %dA - A/C PRESSURE SWITCH' % S.ACPS[1], kind='ATM'))
    return out


def power_relay_labels(z=60.0):
    """[{at, text}] one per POWER relay, at the mean of its pin positions (R189)."""
    pts = {}
    for r in _wires('POWER'):
        if r['id'] in POWER_RELAYS and r['at']:
            pts.setdefault(r['id'], []).append((r['at']['x'], r['at']['y']))
    return [dict(at=_p(sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v), z), text='%s (%s)' % (rid, POWER_RELAYS[rid]))
            for rid, v in sorted(pts.items())]


def power_wire_labels():
    """[{at, text, side}] one per harness wire end in the POWER box (R190): side 'top' (bus studs, seen with the cover off) or
    'bottom' (relay terminals, ACPS, the AMI output lugs on the C-strap studs, seen from below with the pan off)."""
    names, ami, out = _harness_names(), power_ami_points(), []
    pos = {nm: _p(S.POWER['x_bar'], y, S.POWER['bar_top'] + 4.0) for y, nm, _h in S.REV7['pos_studs']}
    neg = {nm: _p(x, S.REV7['neg_bar']['yc'], S.POWER['bar_top']) for x, nm, *_r in S.REV7['neg_studs']}
    for r in _wires('POWER'):
        here, side, at = None, 'bottom', None
        if r['id'] == 'fb_power' and r['des'].startswith('AMI'):
            k = r['des'].split()[1]
            at, here = ami[k]['lug'], r['des']
        elif r['id'] == 'fb_power':
            at, here = _p(r['at']['x'], r['at']['y'], 20.0), r['des']
        elif r['id'] in POWER_RELAYS:
            at, here = _p(r['at']['x'], r['at']['y'], 20.0), '%s %s' % (r['id'], PIN.get(r['cav'], r['cav']))
        elif r['id'] == 'pdb':
            side = 'top'
            if r['des'] == 'BAT+':
                at = pos['BAT+ IN']
            elif r['des'] == 'ALT/STR':
                at = pos['RADLOK+']
            else:
                key = [s for f, s in GND_STUD if f.lower() in (r['far'] or '').lower()]
                at = neg[key[0]] if key else None
            here = names.get((r['file'], 'pdb', r['cav'])) or 'pdb ' + r['des']
        elif r['id'].startswith('t_pdb_gnd'):
            side, at, here = 'top', neg['GND'], names.get((r['file'], r['id'])) or r['id']
        if at is None:
            continue
        out.append(dict(at=at, side=side, text='%s > %s' % (here, r['far'])))
    return out


if __name__ == '__main__':
    for r in _wires('LOGIC') + _wires('BATT'):
        print(r['id'], r['cav'], r['des'], '>', r['far'])
