"""2026-10-19 assembly drawing pass (DECISIONS R184 - R197) on top of aspecs.py: ST185-VRC-100, ST185-CSB3-100, ST185-DRB-100, the
three the 2026-10-18 pass held for the real connector models (#331: TE HD34-24-33PE, CNLINKO LP-16, TE DRB12 / DRBF-1A / DRB16).
Drawing-only on top of the merged models (R196): plain machinist notes (R191 / R192 / R195, no envelope wording R184, no pin /
socket note R185), primary-only balloons in the assembled views (R193), hidden screws ballooned in an exploded view (R186 / R194).
Claude Code, 2026-10-19."""
import aspecs
from aspecs_1018 import _by, UNDER
from specs_1018 import TOL

REV = {'ST185-VRC-100': 'G', 'ST185-CSB3-100': 'F', 'ST185-DRB-100': 'D'}
LID = 'TIGHTEN THE 4 M3 LID SCREWS A LITTLE AT A TIME, CRISS-CROSS. THE LID SITS METAL TO METAL ON THE RIM.'


def vrc():
    sp = aspecs.ASM['vrc']()
    it = sp['items']
    for i in it:
        if i['item'] in (1, 2):
            i['primary'] = True
    sp['notes'] = ['QTY 2 ASSEMBLIES PER CAR (FRONT + REAR).', LID, 'TIGHTEN EACH LP-16 REAR NUT TO 1.0 N·m.']
    sp.update(tol=TOL, rev=REV['ST185-VRC-100'])
    return sp


def csb3():
    sp = aspecs.ASM['csb3']()
    it = sp['items']
    for i in it:
        if i['item'] in (1, 2):
            i['primary'] = True
    for i in it:
        i['desc'] = i['desc'].replace(' (R133)', '')     # no rule numbers on the drawing (R195)
    for st in sp['stage_sheets'][0]:
        st.pop('note', None)
        if st['no'] == 2:       # the HD34 flange sits under the lid: it goes in from below
            st.update(title='HD34 RECEPTACLE UP INTO THE LID', subtitle='EXPLODED, SEEN FROM BELOW (NOT TO SCALE)', view=UNDER,
                      move=[(4, (0, 0, -55))])
    sp['notes'] = [LID]
    sp.update(tol=TOL, rev=REV['ST185-CSB3-100'])
    return sp


def drb():
    sp = aspecs.ASM['drb']()
    it = sp['items']
    for i in it:
        if i['item'] in (1, 4):
            i['primary'] = True
    sp['notes'] = ['THE PLATE BOLTS TO THE FIREWALL WITH 10 M5 SCREWS INTO ITS TAPPED HOLES.',
                   'FLANGE SCREWS: 2.26-2.82 N·m (20-25 IN-LB). JACKSCREW: TURN IT WITH AN M8 HEX SOCKET TO 3.38-3.95 N·m (30-35 IN-LB).']
    sp.update(tol=TOL, rev=REV['ST185-DRB-100'])
    return sp


ASM = {'vrc': vrc, 'csb3': csb3, 'drb': drb}


# ---------- ST185-FB-100P POWER box (Dispatch 2026-10-19: the C-strap set after #330 / R199; held in the 10-18 pass) ----------
import numpy as np
import fb_labels as L

_SKIP = ('ST185-FB-101', 'ST185-FB-102', 'ST185-FB-103')     # never the leader target of a label


def _nearest(items, at, only=None):
    """BOM item whose solid is nearest the point `at` (distance to the solid's bounding box), among items with shapes."""
    p = np.array(at, float)
    best = (1e9, None)
    for it in items:
        if not it.get('shapes') or it['pn'] in _SKIP or (only and not any(k in it['pn'] + '|' + it['desc'] for k in only)):
            continue
        for s in it['shapes']:
            b = s.bounding_box()
            lo, hi = np.array(tuple(b.min)), np.array(tuple(b.max))
            d = np.linalg.norm(np.maximum(0, np.maximum(lo - p, p - hi)))
            if d < best[0]:
                best = (d, it['item'])
    return best[1]


def fb_power():
    sp = aspecs.ASM['fb_power']()
    it = sp['items']
    base, cover, pan = (_by(it, pn=p) for p in ('ST185-FB-101', 'ST185-FB-103', 'ST185-FB-102'))
    strap = _by(it, pn='ST185-FB-117')
    for i in (base, cover):
        i['primary'] = True
    sp['iso_balloons'] = {'open': [base['item'], strap['item']]}
    fuses = [dict(item=_nearest(it, f['at'], ('AMI-', 'ATM-') if f.get('kind') != 'ATM' else ('ATM-',)), at=f['at'], text=f['text'])
             for f in L.power_fuse_labels()]
    relays = [dict(item=_nearest(it, r['at'], ('1414', '1393304', 'RELAY')), at=r['at'], text=r['text']) for r in L.power_relay_labels()]
    wires = L.power_wire_labels()
    top = [dict(w, item=_nearest(it, w['at'], ('6R8', '6432', '263-2205'))) for w in wires if w['side'] == 'top']
    bot = [w for w in wires if w['side'] == 'bottom']
    term = [dict(w, item=_nearest(it, w['at'], ('28075', '42281', '62998', '9688'))) for w in bot if not w['text'].startswith('AMI')]
    lugs = [dict(w, item=_nearest(it, w['at'], ('2R5', 'FHS-M5', '6432', 'ST185-FB-117'))) for w in bot if w['text'].startswith('AMI')]
    hide_under = [cover['item'], pan['item']]
    sp['label_views'] = [
        dict(title='WHAT EACH FUSE AND RELAY FEEDS (COVER OFF)', view='top', hide=[cover['item']], labels=fuses + relays),
        dict(title='HARNESS WIRES AT THE BUS STUDS (COVER OFF)', view='top', hide=[cover['item']], text_h=1.8, wires=top),
        dict(title='HARNESS WIRES AT THE C-STRAP LUGS AND THE ACPS FUSE - SEEN FROM BELOW, BELLY PAN OFF', view='bottom',
             hide=hide_under, text_h=1.8, wires=lugs + [w for w in term if w['text'].startswith('ACPS')]),
        dict(title='HARNESS WIRES AT THE RELAYS - SEEN FROM BELOW, BELLY PAN AND R1 CLIP OFF', view='bottom',
             hide=hide_under + [_by(it, pn='ST185-FB-104')['item']], text_h=1.8,
             wires=[w for w in term if not w['text'].startswith('ACPS')]),
    ]
    for st in sp['stage_sheets'][0]:
        st['title'] = st['title'].replace(' (NOTE 4)', '')
        if st['title'].startswith('TERMINALS'):     # they go in from under the deck: show the step from below (as FB-100L)
            st.update(view=UNDER, subtitle='EXPLODED, SEEN FROM BELOW (NOT TO SCALE)', balloon_base=[])
    sp['notes'] = ['SIZES IN BRACKETS ARE FOR REFERENCE. SHEETS 2 - 5: WHAT EACH FUSE AND RELAY FEEDS AND THE HARNESS WIRE AT EACH END.',
                   'PARTS THAT SHARE ONE MODEL (RELAYS, LUGS, NUTS, BOLTS) ARE BALLOONED ON THE FIRST ITEM OF THEIR GROUP.',
                   'M5 BOLTS AND NUTS: 4 N·m MAX (AMI FUSE SHEET).',
                   'C-STRAPS: BUILD THEM AS ST185-FB-117 SHEET 2, THEN PUSH EACH STRAIGHT DOWN INTO ITS WELL UNTIL THE HOOKS CLICK OVER THE LIPS.',
                   'TERMINALS GO UP FROM UNDER THE DECK UNTIL THE LANCE CLICKS; TUG THE WIRE TO CHECK (TE 114-2025 3.6, 114-20021 3.7).',
                   'TIE THE HARNESS NO CLOSER THAN 38 mm UNDER THE DECK; NO SHARP BENDS AT THE DECK (TE 114-20021 3.7 C).']
    sp.update(tol=TOL, rev='Z')
    return sp


ASM['fb_power'] = fb_power
