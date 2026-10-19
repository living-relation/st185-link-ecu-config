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


if __name__ == '__main__':
    for r in _wires('LOGIC') + _wires('BATT'):
        print(r['id'], r['cav'], r['des'], '>', r['far'])
