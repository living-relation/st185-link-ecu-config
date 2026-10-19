"""CSB3 and VRC enclosure assemblies with the makers' own connector models (DECISIONS R184: every bought part is the maker's model,
never an envelope). Each maker STEP goes where the old placeholder connector body was:

  CSB3  TE HD34-24-33PE (cad/vendor/te/HD34-24-33PE): TE's frame already matches the placeholder (it was made from the same TE
        model): moved up 84.16, no turn - flange under the lid's 4.0 panel, D-flat to +y.
  VRC   CNLINKO LP-16-C05SX-02-101 (cad/vendor/cnlinko, exported from Dan's Fusion copy), one in each end wall (IN +x, OUT -x):
        connector axis = its model's y, front (mating end, dust cap) outward; turned 90 deg about z so the cap hangs down; the back
        of the cap tether ring (model y 2.1) on the wall's outer face (x = +-45.0); axis at z 21.0 (vrc_holder_spec.LP16_AXIS_Z).
        The model's jam nut sits 0.5 behind the tether ring (a thin panel) and is fused to the body; our wall is 3.5 thick, so the
        nut is cut out as its own body (the hex between y 2.6 and 6.6, outside its M18 x 1.5 thread, D18.0) and moved 3.0 back onto
        the wall's inner face. The nut ships as a separate part, so this is where it is screwed to. The body inside the wall (the core
        left where the nut was) is trimmed to the panel-hole shape it passes through: D18.0 with flats 16.4 apart, top and bottom
        (CNLINKO hole D18.5, flats 16.5 +0.2/0, PLAN-notes). Nothing else is changed.

The Fusion documents ST185-CSB3-Enclosure / ST185-VRC-Enclosure stay the master: `place` writes each connector, already in the
box's frame, as <box>/<BOX>_part_<connector>.step; `fusion_real_connectors.py` imports those into the Fusion document in place of
the placeholder bodies and re-exports the assembly; `check` then reads that Fusion export and reports every overlap between the
connector bodies and our parts (body, lid, O-ring, board holder, VR board, CSB3 board, set screws, supports). It must be 0.

Run (WSL, handbuilt-cad .venv; build123d), <cad dir> = the main checkout's cad/:
    ~/projects/handbuilt-cad/.venv/bin/python -I cad/enclosures/src/real_connectors.py place|check <cad dir> [csb3] [vrc]
Claude Code, 2026-10-19.
"""
import json
import os
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, import_step, export_step

MODE, CAD = sys.argv[1], sys.argv[2]
JOBS = sys.argv[3:] or ['csb3', 'vrc']
ENC = os.path.join(CAD, 'enclosures')
VEND = os.path.join(CAD, 'vendor')

HD34 = ('te', 'HD34-24-33PE', 'c-hd34-24-33pe-a-3d.stp')
LP16 = ('cnlinko', 'LP-16-C05SX-02-101', 'LP-16-C05SX-02-101.step')
HD34_Z = 84.16                 # TE frame -> CSB3 frame (the placeholder's own offset)
LP16_RING_BACK = 2.1           # LP-16 model: back face of the cap tether ring (lands on the wall's outer face)
LP16_NUT = (2.6, 6.6)          # LP-16 model: jam nut faces
LP16_THREAD_R = 18.0 / 2       # CNLINKO: M18 x 1.5 body thread (the nut's bore)
LP16_FLAT = 16.4 / 2           # body flats in the panel hole (hole flats 16.5 +0.2/0)
WALL_X, WALL_T, AXIS_Z = 45.0, 3.5, 21.0


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
    return a.label or 'assembly', out


def maker(spec):
    return import_step(os.path.join(VEND, *spec)).solids()


def vol(a, b):
    r = a.intersect(b)
    return sum(s.volume for s in r.solids()) if r else 0.0


def bbox(c):
    b = c.bounding_box()
    return [round(v, 2) for v in (*b.min, *b.max)]


def write(path, label, shapes):
    for x in shapes:
        x.label = label
    export_step(Compound(children=shapes, label=label), path)


def check(asm, prefixes):
    """overlap (mm3) of every connector body with every other body of the exported assembly."""
    _, parts = leaves(asm)
    conn = [(n, s) for n, s in parts if n.startswith(prefixes)]
    rest = [(n, s) for n, s in parts if not n.startswith(prefixes)]
    rep = {}
    for n, s in conn:
        for m, t in rest:
            key = '%s / %s' % (n, m)
            rep[key] = round(rep.get(key, 0.0) + vol(s, t), 3)
    return {'connector_bodies': sorted({n for n, _ in conn}), 'connector_mm3': round(sum(s.volume for _, s in conn), 1),
            'bodies': len(parts), 'overlap_mm3': rep, 'max_overlap_mm3': max(rep.values() or [0.0])}


def lp16_split():
    """the LP-16 model as (body, nut): nut = the hex outside the M18 thread between its faces; the body inside the wall = the D-flat
    profile of the panel hole it passes through."""
    s = maker(LP16)
    assert len(s) == 1, 'LP-16 model: expected one solid'
    s = s[0]

    def slab(y0, y1, w=40.0, h=40.0):
        return Pos(0, (y0 + y1) / 2, 0) * Box(w, y1 - y0, h)

    def rod(y0, y1):
        return Pos(0, (y0 + y1) / 2, 0) * Rot(90, 0, 0) * Cylinder(LP16_THREAD_R, y1 - y0)
    n0, n1 = LP16_NUT
    w0, w1 = LP16_RING_BACK, LP16_RING_BACK + WALL_T
    nut_zone = slab(n0, n1) - rod(n0, n1)
    wall_trim = slab(w0, w1) - (rod(w0, w1) & slab(w0, w1, h=2 * LP16_FLAT))
    keep = Box(200, 200, 200) - (nut_zone + wall_trim)      # intersect, not cut: cutting this STEP leaves pieces behind
    return s.intersect(keep).solids(), s.intersect(nut_zone).solids()


def place_csb3():
    hd = [Pos(0, 0, HD34_Z) * s for s in maker(HD34)]
    out = os.path.join(ENC, 'csb3', 'CSB3_part_HD34-24-33PE.step')
    write(out, 'HD34-24-33PE', hd)
    return {'out': out, 'bbox': bbox(Compound(hd)), 'mm3': round(sum(s.volume for s in hd), 1)}


def place_vrc():
    body, nut = lp16_split()
    nut = [Pos(0, WALL_T - (LP16_NUT[0] - LP16_RING_BACK), 0) * s for s in nut]     # nut front face on the wall's inner face
    rep = {'nut_mm3': round(sum(s.volume for s in nut), 1)}
    for side, sgn in (('IN', 1), ('OUT', -1)):
        # model y (axis, front = -y) -> world -x for IN (+x wall) / +x for OUT; model z stays z (cap hangs down)
        loc = Pos(sgn * (WALL_X + LP16_RING_BACK), 0, AXIS_Z) * Rot(0, 0, 90 * sgn)
        shapes = [loc * s for s in body + nut]
        out = os.path.join(ENC, 'vrc', 'VRC_part_LP16-%s_LP-16-C05SX-02-101.step' % side)
        write(out, 'LP16-%s LP-16-C05SX-02-101' % side, shapes)
        rep[side] = {'out': out, 'bbox': bbox(Compound(shapes)), 'mm3': round(sum(s.volume for s in shapes), 1)}
    return rep


REP = {}
for job in JOBS:
    if MODE == 'place':
        REP[job] = place_csb3() if job == 'csb3' else place_vrc()
    else:
        REP[job] = check(os.path.join(ENC, job, job.upper() + '_assembly.step'), ('HD34',) if job == 'csb3' else ('LP16',))
print(json.dumps(REP, indent=1))
