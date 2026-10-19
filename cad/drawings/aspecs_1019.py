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
