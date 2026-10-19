"""ST185-DRB-100 assembly: the DRB102 firewall plate with TE's own connector models (DECISIONS R184: every bought part is the
maker's model, never an envelope). Replaces the three envelope boxes that build_DRB102_plate.py draws for its clearance checks.

Inputs (all local, gitignored, R67):
  the plate script's assembly STEP (plate, O-ring, 1 mm firewall reference, flange screw heads) - its envelope connector bodies
  and socket keep-out are dropped and rebuilt here; a previous output of this script is also accepted (idempotent)
  cad/vendor/te/DRB12-102PAE-L018, DRB16-102SAE-L018, DRBF-1A (TE customer view models, cad/vendor/INDEX.md)

How the TE parts go together (TE application spec 114-151021 rev A, 3.8 steps 1-5, p.18-19): the DRBF-1A flange sits on the
cabin face of the 6.0 web with its sleeve through the panel cutout to the plug side; the DRB12 receptacle snaps into the flange
from the cabin side; the DRB16 plug goes over the sleeve from the engine side and is pulled home by its jackscrew.
  flange    - moved up until it touches the plate (contact search): its seal bead tip lands on the web's cabin face (z 0)
  receptacle- seated on the flange's hard stop (contact search in the flange frame: -7.28)
  plug      - turned face down (180 deg about Y, which keeps its wide polarising slot on the receptacle post's thick side)
              and lowered until its centre slot bottoms on the receptacle post (the groove bottom then sits 0.22 off the sleeve top)
Known overlaps between TE's own models, reported and left as TE drew them: the plug model has no keyways for the flange's
4 key ribs; the flange's 2 mounting-clip arms are drawn unflexed (0.5 into the receptacle wall); the plug jackscrew runs into
the receptacle post (M6 threaded insert not drawn as a hole).

Run (WSL, handbuilt-cad .venv; build123d):
    ~/projects/handbuilt-cad/.venv/bin/python -I cad/drb102-plate/build_DRB102_assembly.py <cad dir> [out.step]
<cad dir> = the main checkout's cad/ (plate assembly + cad/vendor). Default out = <cad dir>/drb102-plate/DRB102-firewall-plate-assembly.step.
Claude Code, 2026-10-19.
"""
import json
import os
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, import_step, export_step

CAD = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(CAD, 'drb102-plate', 'DRB102-firewall-plate-assembly.step')
SRC = os.path.join(CAD, 'drb102-plate', 'DRB102-firewall-plate-assembly.step')
TE = os.path.join(CAD, 'vendor', 'te')
KEEP = ('plate_6061', 'te_screw_heads', 'firewall_ref_1mm', 'oring_AS568_261')
REC, PLUG, FLANGE = 'TE_DRB12-102PAE-L018', 'TE_DRB16-102SAE-L018', 'TE_DRBF-1A'
REC_SEAT = -7.28        # receptacle in the flange frame: hard stop (contact search, 2026-10-19)
POST_TOP = 0.0          # receptacle model: top of the centre post (M6 insert boss), its own frame
PLUG_SLOT = 9.80        # plug model: centre slot bottom, behind the plug face
PLUG_REAR = 39.42       # plug model: jackscrew hex end, behind the plug face
WEB = 6.0               # plate web (build_DRB102_plate.py)


def leaves(path):
    a = import_step(path)
    out = []

    def walk(n):
        kids = list(getattr(n, 'children', []) or [])
        if kids:
            for c in kids:
                walk(c)
        else:
            out.extend((n.label or '', s) for s in n.solids())
    walk(a)
    return a.label or 'DRB102_firewall_assy', out


def te(pn, f):
    return Compound(import_step(os.path.join(TE, pn, f)).solids())


def vol(a, b):
    r = a.intersect(b)
    return sum(s.volume for s in r.solids()) if r else 0.0


name, parts = leaves(SRC)
kept = [(n, s) for n, s in parts if n.startswith(KEEP)]
assert {n for n, _ in kept} >= set(KEEP), 'plate assembly is missing %s' % (set(KEEP) - {n for n, _ in kept})
plate = Compound([s for n, s in kept if n == 'plate_6061'])

R = te('DRB12-102PAE-L018', 'c-drb12-102pae-l018-99-3d.stp')
P = te('DRB16-102SAE-L018', 'c-drb16-102sae-l018-99-3d.stp')
F = te('DRBF-1A', 'c-drbf-1a-99-3d.stp')

# flange: highest lift with no overlap with the plate (bisection, 0.005)
lo, hi = 0.0, 30.0
assert vol(Pos(0, 0, lo) * F, plate) == 0.0
while hi - lo > 0.005:
    m = (lo + hi) / 2
    lo, hi = (m, hi) if vol(Pos(0, 0, m) * F, plate) == 0.0 else (lo, m)
FZ = round(lo, 3)
plug_face = REC_SEAT + POST_TOP - PLUG_SLOT                       # flange frame
place = {FLANGE: Pos(0, 0, FZ) * F,
         REC: Pos(0, 0, FZ + REC_SEAT) * R,
         PLUG: Pos(0, 0, FZ + plug_face) * Rot(0, 180, 0) * P}
rear = FZ + plug_face + PLUG_REAR
keepout = Pos(0, 0, rear + 75.0) * Cylinder(12.5, 150.0)           # M8 socket on the jackscrew, straight out

rep = {'flange_lift': FZ, 'plug_face_z': round(FZ + plug_face, 3), 'plug_rear_z': round(rear, 3), 'ours_vs_TE': {}, 'TE_vs_TE': {}}
ours = {n: Compound([s for m, s in kept if m == n]) for n in KEEP}
for a, sa in ours.items():
    for b, sb in place.items():
        rep['ours_vs_TE']['%s / %s' % (a, b)] = round(vol(sa, sb), 3)
for a, b in ((FLANGE, REC), (FLANGE, PLUG), (REC, PLUG)):
    r = place[a].intersect(place[b])
    rep['TE_vs_TE']['%s / %s' % (a, b)] = [dict(vol=round(s.volume, 2), bbox=[round(v, 2) for v in (*s.bounding_box().min, *s.bounding_box().max)])
                                           for s in (r.solids() if r else [])]
fb = place[FLANGE].bounding_box()
rep['flange_bbox'] = [round(v, 2) for v in (*fb.min, *fb.max)]
rep['plug_bbox'] = [round(v, 2) for v in (*place[PLUG].bounding_box().min, *place[PLUG].bounding_box().max)]
rep['receptacle_bbox'] = [round(v, 2) for v in (*place[REC].bounding_box().min, *place[REC].bounding_box().max)]

kids = []
for n, s in kept:
    s.label = n
    kids.append(s)
for n, c in place.items():
    for s in c.solids():
        s.label = n
        kids.append(s)
keepout.label = 'socket_keepout'
kids.append(keepout)
export_step(Compound(children=kids, label=name), OUT)
rep['out'] = OUT
print(json.dumps(rep, indent=1))
