"""Data for the assembly wiring diagrams: reads the SoT chain and the box spec, never the layout of a drawing.

Sources (DECISIONS R45: the .harness looms are NOT a source of truth):
  * sot/channels.csv ........ pin-level facts of every relay cavity (cross-check)
  * docs/harness/interfaces.json  OEM flying leads = every splice into the factory loom (EWD connector, pin, colour, page, method)
  * cad/fusebox/src/spec.py .. the fuse / relay list of the three assemblies (AMI_ROWS, MINI_COLS, MICRO_POS, F7_POS)
  * docs/harness/rebuild/*.harness  ONLY for the wire facts the SoT does not hold (wire id, gauge, insulation colour, ident bands,
    the label of each far end) - and every wire read from there is cross-checked against the SoT / spec; a mismatch is LISTED
    (MISMATCHES.md), never guessed away.
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'docs', 'harness'))
sys.path.insert(0, os.path.join(REPO, 'cad', 'fusebox', 'src'))
from model import full_text    # noqa: E402
import spec as S               # noqa: E402

REB = os.path.join(REPO, 'docs', 'harness', 'rebuild')
POWER_ENT = {'fb_power', 'pdb', 'k_htr', 'k_efi', 'k_str', 'k_fan', 'k_fan2', 'k_pwr'}
LOGIC_ENT = {'fb_logic', 'k_hl', 'k_hr', 'k_horn', 'k_etb', 'k_acc', 'k_eps_en', 'k_rev', 'sp_hl', 'sp_hr'}
BATT_ENT = {'fb_batt', 'k_fp'}


def box_of_ent(eid):
    if eid in POWER_ENT or eid.startswith('t_pdb_gnd'):
        return 'POWER'
    if eid in LOGIC_ENT:
        return 'LOGIC'
    if eid in BATT_ENT:
        return 'BATT'
    return None


def load():
    """-> (ents, wires). ents[(file, id)] = (kind, obj, cavity dict); wires = list of dicts with resolved ends."""
    ents, wires = {}, []
    for fn in sorted(glob.glob(os.path.join(REB, '*.harness'))):
        d = full_text(json.load(open(fn, encoding='utf-8')), fn)
        name = os.path.basename(fn)[6:-8]
        wp = {p['id']: p for p in d.get('wireParts', [])}
        for kind, key in (('conn', 'connectors'), ('term', 'terminals'), ('splice', 'splices')):
            for o in d.get(key, []):
                ents[(name, o['id'])] = (kind, o, {c['id']: c for c in o.get('cavities', [])})
        for w in d['wires']:
            g = wp.get(w.get('partId'), {}).get('gauge', {})
            ends = []
            for side in ('source', 'target'):
                e = w[side]
                kind, obj, cavs = ents.get((name, e['id']), (None, {}, {}))
                cv = cavs.get(e.get('handle'), {})
                ends.append(dict(ent=e['id'], handle=e.get('handle'), kind=kind, des=cv.get('designation') or '',
                                 sig=cv.get('signal') or obj.get('signal') or '', label=obj.get('label') or '', file=name))
            wires.append(dict(id=w['id'], file=name, colour=w.get('color') or 'Red', bands=w.get('identColors') or [],
                              gauge=g.get('value'), unit=g.get('unit'), ends=ends))
    return ents, wires


def colour_text(w):
    return w['colour'] + (' (' + '-'.join(w['bands']) + ')' if w['bands'] else '')


def gauge_text(w):
    if w['gauge'] is None:
        return 'AWG ?'
    return ('%g mm2' % w['gauge']) if w['unit'] == 'Metric' else ('%g AWG' % w['gauge'])


def short(s, n=90):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '...'


def far_text(end):
    """R156 far-end text: where THAT end lands. A terminal / splice carries it as its label; a connector end is
    '<what it is> pin <designation>'."""
    if end['kind'] in ('term', 'splice'):
        return end['label']
    name = end['label'].split(' - ')[0]
    return '%s pin %s' % (name, end['des'] or end['handle'])


def box_wires(wires):
    """Every wire with at least one end inside POWER / LOGIC / BATT."""
    out = []
    for w in wires:
        bx = [box_of_ent(e['ent']) for e in w['ends']]
        if any(bx):
            out.append(dict(w, boxes=bx))
    return out


def fuse_list(ents):
    """LOGIC mini fuses and POWER AMI fuses as the SoT chain names them (harness cavity designation + signal text)."""
    res = {'LOGIC': [], 'POWER_IN': [], 'POWER_OUT': []}
    lg = ents[('CabinPower', 'fb_logic')][1]
    for c in lg['cavities']:
        m = re.match(r'(BUS[12])-(\d+)( IN)?$', c['designation'])
        if m:
            sig = c.get('signal') or ''
            mm = re.search(r'ATM-([\d.]+) (\w+)', sig)
            res['LOGIC'].append(dict(cav=c['id'], des=c['designation'], bus=m.group(1), n=int(m.group(2)), is_in=bool(m.group(3)),
                                     amps=mm.group(1) if mm else None, name=mm.group(2) if mm else None, sig=sig))
    pw = ents[('CabinPower', 'fb_power')][1]
    for c in pw['cavities']:
        m = re.match(r'AMI (IN|OUT)-(\d+)$', c['designation'])
        if m:
            mm = re.match(r'AMI-(\d+) (\w+)', c.get('signal') or '')
            res['POWER_' + m.group(1)].append(dict(cav=c['id'], des=c['designation'], n=int(m.group(2)),
                                                  amps=mm.group(1) if mm else None, name=mm.group(2) if mm else None,
                                                  sig=c.get('signal') or ''))
    for k in res:
        res[k].sort(key=lambda r: (r.get('n', 0), r.get('is_in', False)))
    return res


def sot_rows():
    return list(csv.DictReader(open(os.path.join(REPO, 'sot', 'channels.csv'), encoding='utf-8')))


def oem_leads():
    reg = json.load(open(os.path.join(REPO, 'docs', 'harness', 'interfaces.json'), encoding='utf-8'))
    return reg['flyingLeads']


def cross_check(ents, wires, fuses):
    """Mismatches between the SoT chain / spec and the harness wires the diagrams draw, as a list of strings."""
    bad = []
    bw = box_wires(wires)
    spec_mini = {}
    for col, (cx, lst) in S.MINI_COLS.items():
        for nm, a in lst:
            if a is not None:
                spec_mini[(col, nm)] = a
    seen = set()
    for f in fuses['LOGIC']:
        if f['is_in']:
            continue
        key = (f['bus'], f['name'])
        seen.add(key)
        if key not in spec_mini:
            bad.append('LOGIC %s: harness cavity %s has no spec.MINI_COLS entry' % (f['des'], f['name']))
        elif float(f['amps']) != float(spec_mini[key]):
            bad.append('LOGIC %s %s: harness %s A vs spec.MINI_COLS %s A' % (f['des'], f['name'], f['amps'], spec_mini[key]))
    for key in spec_mini:
        if key not in seen:
            bad.append('LOGIC %s %s: in spec.MINI_COLS, no harness cavity' % key)
    for row in ('IN', 'OUT'):
        sp = {nm: a for nm, a in S.AMI_ROWS[row] if a is not None}
        hs = {f['name']: int(f['amps']) for f in fuses['POWER_' + row]}
        for nm, a in sp.items():
            if nm not in hs:
                bad.append('POWER AMI %s %s: in spec.AMI_ROWS, no harness cavity' % (row, nm))
            elif hs[nm] != a:
                bad.append('POWER AMI %s %s: harness %s A vs spec %s A' % (row, nm, hs[nm], a))
        for nm in hs:
            if nm not in sp:
                bad.append('POWER AMI %s %s: harness cavity, not in spec.AMI_ROWS' % (row, nm))
    ends = {}
    for w in wires:
        for e in w['ends']:
            ends.setdefault((e['ent'], e['handle']), []).append(w['id'])
    for r in sot_rows():
        if r['owner'] != 'PWR' or not r['conn'].startswith('k_') or r['conn'] == 'k_eps':
            continue
        if not ends.get((r['conn'], r['pin'])) and r['pin'] != 'c5':
            bad.append('SoT %s %s %s (%s): no harness wire lands on it' % (r['conn'], r['pin'], r['channel'], r['net']))
    for w in bw:
        if w['gauge'] is None:
            bad.append('wire %s: no gauge' % w['id'])
    return bad
