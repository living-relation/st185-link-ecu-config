"""2026-10-18 assembly drawing pass (DECISIONS R184 - R197) on top of aspecs.py: ST185-FH-100, ST185-FB-100L, ST185-FB-100B.
Drawing-only changes (the models changed first, R196): plain machinist notes (R191 / R192 / R195, no envelope wording R184),
primary-only balloons in the assembled views (R193), the hidden screws pulled out in an exploded view with dotted lines (R186 / R194),
and for the fuse boxes a label sheet naming what every fuse and relay feeds (R189) plus label sheets with the harness drawing's name of
every wire that lands in the box, at its terminal (R190; cad/drawings/fb_labels.py, from the SoT chain).
Held for Dan (Dispatch 2026-10-18): FB-100P (N36 may change the strap), CSB3-100 (HD34 STEP), VRC-100 (LP-16 STEP), DRB-100 (TE STEPs).
Claude Code, 2026-10-18."""
import numpy as np
from build123d import Axis, GeomType
import aspecs
import fb_labels as L
from specs_1018 import TOL, REV

TERM_NOTES = ['TERMINALS GO IN FROM UNDER THE DECK, CONTACT BOX FIRST, UNTIL THE LANCE CLICKS. PULL THE WIRE BACK GENTLY TO CHECK IT '
              'HOLDS (TE 114-2025 3.6, 114-20021 3.7).',
              'KEEP HARNESS TIES AT LEAST 38 mm BELOW THE DECK, AND DO NOT BEND THE WIRES HARD TO ONE SIDE AT THE DECK (TE 114-20021 3.7 C).']


def _by(items, pn=None, desc=None):
    for it in items:
        if (pn and it['pn'] == pn) or (desc and desc in it['desc']):
            return it
    raise KeyError(pn or desc)


def _screw_out(s, dist):
    """offset that pulls a screw straight out of its hole by dist: along its shank axis, toward its head."""
    cyl = [f for f in s.faces() if f.geom_type == GeomType.CYLINDER]
    f = min(cyl, key=lambda f: f.radius) if cyl else None
    if f is None:
        return (0, 0, dist)
    ax = np.array(tuple(f.axis_of_rotation.direction))
    d = np.array(tuple(s.center())) - np.array(tuple(f.center()))     # the head end holds more of the mass
    return tuple(ax * dist * (1 if d @ ax >= 0 else -1))


def fuel_hanger():
    sp = aspecs.ASM['fuel_hanger']()
    it = sp['items']
    for i in it:
        if i['item'] in (1, 2, 3, 4, 8):
            i['primary'] = True
    custom = [(n, s, _screw_out(s, 60.0)) for n in (5, 6) for s in _by(it, desc=('SADDLE SCREW' if n == 5 else 'FOOT SCREW'))['shapes']]
    sp['exploded'] = dict(label='EXPLODED VIEW - SCREWS PULLED OUT', custom=custom, balloon=[5, 6, 7],
                          base=[i['item'] for i in it if i.get('shapes') and i['item'] not in (5, 6)])
    sp['notes'] = ['SHOWN AS INSTALLED (FLANGE ON TOP). OVERALL SIZES ARE FOR REFERENCE.',
                   'ORDER: 1) FIT THE TANK BULKHEAD NUTS. 2) BOLT THE STRUT TO THE FLANGE LUG (ITEM 9). 3) SCREW THE FOOT (ITEM 3) ON WITH '
                   '2 ITEM 6 SCREWS AND MEDIUM THREADLOCKER. 4) PUSH THE PUMP INTO THE FOOT.',
                   'SADDLE (ITEM 4): PUSH IT TOWARD THE STRUT SO ITS TAB SITS ON THE STRUT SIDE FACE, THEN TIGHTEN THE 2 ITEM 5 SCREWS TO '
                   '2 N·m WITH LOCTITE 243. THE BAND CLAMP (ITEM 7) GOES IN THE SADDLE CHANNEL.']
    sp.update(tol=TOL, rev=REV['ST185-FH-100'])
    return sp


CIRCUIT = {   # what each LOGIC fuse feeds, in words (from its cavity in ST185-CabinPower, wiring_plan.json)
    'EFI86': 'EFI RELAY COIL', 'HL': 'HEAD LH RELAY', 'HR': 'HEAD RH RELAY', 'HZ': 'HAZARD + HORN', 'DM': 'DOME LIGHT',
    'WL': 'DOOR LOCK / TILT', 'ALM': 'ALARM', 'ALMS': 'ALARM SHOCK SENSOR', 'ALTS': 'ALTERNATOR SENSE', 'ETB': 'ETB RELAY',
    'LAM': 'CAN-LAMBDA', 'SW12': 'SWITCHED 12 V RAIL', 'COP': 'IGNITION COILS', 'INJ': 'INJECTORS', 'CSB': 'CSB3 SWITCH BOARD',
    'DEV': 'CLUSTER + REALDASH', 'EPSEN': 'EPS ENABLE RELAY', 'ACC': 'A/C CLUTCH RELAY', 'ALMIG': 'ALARM IGNITION SENSE',
    'MRS': 'EHPS PUMP ENABLE', 'B30': 'START REQUEST (ECU B30)'}


def _term_item_for(items, pns):
    pts = [(np.array(tuple(s.center()))[:2], i['item']) for i in items if i['pn'] in pns for s in (i.get('shapes') or [])]

    def f(x, y):
        d, it = min(((np.linalg.norm(p - (x, y)), it) for p, it in pts), key=lambda t: t[0])
        return it if d < 3.0 else None
    return f


UNDER = ((1, -1.55, -1.15), (0, 0, 1))      # trimetric from below: the parts that go in from under the deck face the viewer


def _along_bolt(shapes, bolts, dist):
    """(shape, offset) for each shape: pulled out along the axis of its nearest bolt, toward that bolt's head."""
    axes = [(np.array(tuple(b.center())), np.array(_screw_out(b, 1.0))) for b in bolts]
    out = []
    for s in shapes:
        c = np.array(tuple(s.center()))
        _, ax = min(axes, key=lambda t: np.linalg.norm(t[0] - c))
        out.append((s, tuple(ax * dist)))
    return out


def _logic_steps(it):
    """FB-100L install steps (R186 / R194: every part shown where it can be seen; the hidden ones pulled out, dotted lines)."""
    n = lambda pn: _by(it, pn=pn)['item']
    base, strips, pem4, pem5, lim = n('ST185-FB-105'), n('ST185-FB-115/-116'), n('PEM S-M4-2ZI'), n('PEM SS-M5-2ZI'), n('EFC 10S00056')
    terms = [n(p) for p in ('280919-2', '42281-1', '1-968849-1', '1-968851-1')]
    flug, fbolt, jlug, jwire, jwash, jbolt = n('Klauke 2R5'), n('RS 287-3921'), n('320554'), n('M22759/16-14-2'), n('RS 231-0691'), n('RS 287-3915')
    fuses = [i['item'] for i in it if i['pn'].startswith('ATM-') and i.get('shapes')]
    relay, pan, cover = n('4-1904124-2'), n('ST185-FB-106'), n('ST185-FB-107')
    sh = lambda i: next(x for x in it if x['item'] == i)['shapes']
    c = lambda i, d: [(i, s, v) for s, v in d]
    def _away(s, ref, dist):   # along the nut's own axis, away from the strip it sits in (the side it is pressed in from)
        v = np.array(_screw_out(s, 1.0))
        c, r0 = np.array(tuple(s.center())), min((np.array(tuple(x.center())) for x in ref), key=lambda q: np.linalg.norm(q - np.array(tuple(s.center()))))
        return tuple(v * dist * (1 if (c - r0) @ v >= 0 else -1))
    nuts_out = [(i, s, _away(s, sh(strips), 18.0)) for i in (pem4, pem5) for s in sh(i)]
    feed = c(fbolt, _along_bolt(sh(fbolt), sh(fbolt), 40.0)) + c(flug, _along_bolt(sh(flug), sh(fbolt), 20.0))
    jump = (c(jbolt, _along_bolt(sh(jbolt), sh(jbolt), 45.0)) + c(jwash, _along_bolt(sh(jwash), sh(jbolt), 32.0))
            + c(jlug, _along_bolt(sh(jlug), sh(jbolt), 20.0)) + [(jwire, s, (0, 0, -55.0)) for s in sh(jwire)])
    held = [base, strips, pem4, pem5, lim]
    return [
        dict(no=1, title='PRESS A PEM NUT INTO EVERY STRIP HOLE', base=[strips], custom=nuts_out),
        dict(no=2, title='LIMITERS; STRIPS IN FROM THE REAR TILL THE HOOK CLICKS', base=[base],
             move=[(lim, (0, 0, -25)), (strips, (0, 60, 0)), (pem4, (0, 60, 0)), (pem5, (0, 60, 0))], balloon_base=[base]),
        dict(no=3, title='TERMINALS UP INTO THE CAVITIES', subtitle='EXPLODED, SEEN FROM BELOW (NOT TO SCALE)', base=held, move=[(t, (0, 0, -30)) for t in terms],
             view=UNDER, balloon_base=[]),
        dict(no=4, title='FEED LUGS ON THE M5 x 10 FEED BOLTS', subtitle='EXPLODED, SEEN FROM BELOW (NOT TO SCALE)', base=held + terms, custom=feed, view=UNDER, balloon_base=[]),
        dict(no=5, title='JUMPERS: WIRE, LUG, WASHER, M4 x 8 BOLT', subtitle='EXPLODED, SEEN FROM BELOW (NOT TO SCALE)', base=held + terms + [flug, fbolt],
             custom=jump, view=UNDER, balloon_base=[]),
        dict(no=6, title='FUSES AND RELAYS IN FROM THE TOP', base=held + terms + [flug, fbolt, jwire, jlug, jwash, jbolt],
             move=[(f, (0, 0, 45)) for f in fuses] + [(relay, (0, 0, 55))], balloon_base=[]),
        dict(no=7, title='BELLY PAN AND COVER', base=held + terms + fuses + [relay, flug, fbolt, jwire, jlug, jwash, jbolt],
             move=[(pan, (0, 0, -50)), (cover, (0, 0, 70))], balloon_base=[]),
    ]


def fb_logic():
    sp = aspecs.ASM['fb_logic']()
    it = sp['items']
    base, cover, pan = (_by(it, pn=p) for p in ('ST185-FB-105', 'ST185-FB-107', 'ST185-FB-106'))
    strips = _by(it, pn='ST185-FB-115/-116')
    for i in (base, cover):
        i['primary'] = True
    sp['iso_balloons'] = {'open': [base['item'], strips['item']]}
    fuse_items = {a: _by(it, pn=p)['item'] for a, p in ((2, 'ATM-2'), (5, 'ATM-5'), (7.5, 'ATM-7-1/2'), (10, 'ATM-10'), (15, 'ATM-15'),
                                                       (20, 'ATM-20'))}
    fl = L.logic_fuse_labels(fuse_items)
    for f in fl:
        nm = f['text'].split()[1]
        f['text'] += ' - ' + CIRCUIT.get(nm, nm)
    relay = _by(it, pn='4-1904124-2')['item']
    tif = _term_item_for(it, ('1-968849-1', '1-968851-1', '42281-1', '280919-2'))
    hide_under = [cover['item'], pan['item']]
    sp['label_views'] = [
        dict(title='WHAT EACH FUSE AND RELAY FEEDS (COVER OFF)', view='top', hide=[cover['item']], labels=fl + L.logic_relay_labels(relay)),
        dict(title='HARNESS WIRES AT THE FUSES - SEEN FROM BELOW, BELLY PAN OFF', view='bottom', hide=hide_under, text_h=1.8,
             wires=[dict(w, item=w['item']) for w in L.logic_wire_labels(tif, kind='fuse')]),
        dict(title='HARNESS WIRES AT THE RELAYS - SEEN FROM BELOW, BELLY PAN OFF', view='bottom', hide=hide_under, text_h=1.8,
             wires=[dict(w, item=w['item']) for w in L.logic_wire_labels(tif, kind='relay')]),
    ]
    sp['stage_sheets'] = [_logic_steps(it)]
    sp['notes'] = ['OVERALL SIZES ARE FOR REFERENCE.',
                   'PARTS THAT SHARE ONE MODEL (THE MICRO RELAYS, LUGS, JUMPER WIRES) ARE BALLOONED ON THE FIRST ITEM OF THEIR GROUP.',
                   'USE THE M5 x 10 FEED BOLT, NOT A SHORTER ONE: ITS TIP GOES 1.7 INTO THE SPINE AND LOCKS THE STRIP.',
                   'SHEET 2: WHAT EACH FUSE AND RELAY FEEDS. SHEETS 3 AND 4: THE HARNESS WIRE AT EACH TERMINAL, NAMED AS ON THE HARNESS '
                   'DRAWINGS.'] + TERM_NOTES
    sp.update(tol=TOL, rev=REV['ST185-FB-100L'])
    return sp


def fb_br():
    sp = aspecs.ASM['fb_br']()
    it = sp['items']
    base, cover = _by(it, pn='ST185-FB-108'), _by(it, pn='ST185-FB-109')
    for i in (base, cover):
        i['primary'] = True
    relay, fuse = _by(it, pn='1416010-1'), _by(it, pn='AMI-40')
    lug, plug = _by(it, desc='RING LUG'), _by(it, pn='282080-1')
    sp['iso_balloons'] = {'open': [base['item'], relay['item']]}
    sp['label_views'] = [dict(title='WHAT THE FUSE AND RELAY FEED, AND THE HARNESS WIRE AT EACH CONNECTION (COVER OFF)', view='top',
                              hide=[cover['item']], text_h=1.8,
                              labels=[dict(item=fuse['item'], index=0, text='FP 40A - FUEL PUMP RELAY 30'),
                                      dict(item=relay['item'], index=0, text='k_fp FUEL PUMP RELAY (HCR150)')],
                              wires=L.batt_wire_labels(lug['item'], plug['item']))]
    sp['notes'] = ['OVERALL SIZES ARE FOR REFERENCE.',
                   'PARTS THAT SHARE ONE MODEL (LUGS, NUTS, BOLTS, LIMITERS) ARE BALLOONED ON THE FIRST ITEM OF THEIR GROUP.',
                   'BAR AND PAD: PUSH EACH ONE DOWN PAST THE SNAP HOOKS UNTIL IT CLICKS, THEN BOLT IT.',
                   'SHEET 2: WHAT THE FUSE AND RELAY FEED, AND THE HARNESS WIRE AT EACH CONNECTION, NAMED AS ON THE HARNESS DRAWINGS.']
    sp.update(tol=TOL, rev=REV['ST185-FB-100B'])
    return sp


ASM = {'fuel_hanger': fuel_hanger, 'fb_logic': fb_logic, 'fb_br': fb_br}
