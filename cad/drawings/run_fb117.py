"""ST185-FB-117 - POWER output copper C-strap (DECISIONS R155, N14 = B): shop drawing of the formed strap + its flat blank.

The formed strap is the Fusion model (cad/fusebox/rev7/Power_Strap_Out_CuC110_15x3_C.step, 14 identical straps; the OUT-row JB1 one is
taken and moved to the strap frame: x = 0 at the AMI ear stud (top PEM), + toward the web; z = 0 at the bottom leg underside). The flat
blank to its right is made here with build123d from spec.strap_blank() (the same numbers the Fusion build uses), finished length, before
the two bends. Both go into one drawing model (<work>/src/st185_fb117/ST185-FB-117_model.step; a copy beside the Fusion STEP).
Run in WSL with the handbuilt-cad venv, from the repo root:

    ST185_WORK=<work dir> ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_fb117.py

-> <work>/out/st185_fb117/ST185-FB-117.pdf / .dxf, <work>/previews/ST185-FB-117_sh1.png. Rev log: cad/fusebox/rev7/ST185-FB-117.REVLOG.md.
FB117_MODEL_ONLY=1 writes the two model STEPs only (R196 / R197: models first, drawings after):
  ST185-FB-117_model.step  - the formed strap and its flat blank, each with its 2 PEM CLSS-M5-2 nuts pressed (heads inside the C);
  ST185-FB-117_stages.step - how the nuts go in, one named solid per piece (Dan's drawing markup 2026-10-18): row 1 (y 0) the blank as
      cut with the nuts beside their holes, head down (step 1); row 2 (y -40) both nuts pressed, the 0.6 trim piece its own solid
      'TRIM_OFFCUT' (step 2); row 3 (y -80) trimmed, ready to bend (step 3).
The nut is built from PEM Bulletin CL p. CL-5 (spec.STRAP_PEM: head E x T, shank C x A, M5 bore D1) - PEM's STEP needs a sign-up (R163).
Claude Code, 2026-10-17; nuts + stages 2026-10-18.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'cad', 'fusebox', 'src'))
import spec as S  # noqa: E402

_TK = os.environ.get('HANDBUILT_CAD') or os.path.expanduser('~/projects/handbuilt-cad')   # drawing engine (as run_one.py)
for _d in ('tools', 'tools/checks', 'tools/render', 'drawing'):
    sys.path.insert(0, os.path.join(_TK, _d))
sys.path.insert(0, HERE)
if os.environ.get('ST185_WORK'):
    os.chdir(os.environ['ST185_WORK'])
os.makedirs('previews', exist_ok=True)
import specs  # noqa: E402,F401  (title block project / drawn-by)
import part  # noqa: E402
from build123d import Box, Compound, Cylinder, Location, Pos, export_step, import_step  # noqa: E402

REV7 = os.path.join(REPO, 'cad', 'fusebox', 'rev7')
JOB = 'st185_fb117'
ST, BL, PM = S.STRAP, S.strap_blank(), S.STRAP_PEM
FX = 30.0                      # flat blank: its top end at x = FX, beside the formed strap in both views


def formed():
    sols = import_step(os.path.join(REV7, 'Power_Strap_Out_CuC110_15x3_C.step')).solids()
    px, py = S.PLACE['POWER']
    y_jb1 = S.AMI_Y0 + [n for n, _a in S.AMI_ROWS['OUT']].index('JB1') * S.AMI_PITCH + py
    x_out = S.POWER['x_bar'] + S.AMI_IN_OFF + S.AMI['c'] + px

    def ctr(s):
        b = s.bounding_box()
        return (b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2
    s = min(sols, key=lambda s_: abs(ctr(s_)[1] - y_jb1) + (0 if ctr(s_)[0] > x_out - 20 else 1e3))
    return s.moved(Location((-x_out, -y_jb1, -ST['z_bl'])))


def flat():
    L, w, t = BL['length'], BL['w'], BL['t']
    b = Pos(FX + L / 2, 0, t / 2) * Box(L, w, t)
    for xh in (BL['pem_top'], BL['pem_bottom']):
        b -= Pos(FX + xh, 0, t / 2) * Cylinder(BL['pem_hole'] / 2, t + 2)
    for sy in (1, -1):
        k0, k1 = BL['kerf']['x']
        ya, yb = BL['kerf']['y']
        b -= Pos(FX + (k0 + k1) / 2, sy * (ya + yb) / 2, t / 2) * Box(k1 - k0, yb - ya, t + 2)
        n0, n1 = BL['notch']['x']
        ya, yb = BL['notch']['y']
        b -= Pos(FX + (n0 + n1) / 2, sy * (ya + yb + 1) / 2, t / 2) * Box(n1 - n0, yb - ya + 1, t + 2)
        lo = BL['low_from']
        b -= Pos(FX + (lo + L) / 2 + 0.5, sy * (BL['w_low'] / 2 + 0.45), t / 2) * Box(L - lo + 1, 0.9, t + 2)
    return b


def pem(x, y, z_face, head_down=True):
    """PEM CLSS-M5-2 pressed into a strap face at z_face: head (E x T) on the face, shank (C x A) into the copper, M5 bore."""
    s = -1 if head_down else 1                         # the side the head is on
    head = Pos(x, y, z_face + s * PM['T'] / 2) * Cylinder(PM['E'] / 2, PM['T'])
    shank = Pos(x, y, z_face - s * PM['A'] / 2) * Cylinder(PM['C'] / 2, PM['A'])
    n = head + shank
    return n - Pos(x, y, z_face) * Cylinder(PM['D1'] / 2, 2 * (PM['T'] + PM['A']) + 2)


def flat_nuts(x_top, y=0.0, drop=0.0):
    """The 2 nuts on a flat blank whose finished top end is at x_top (heads on the underside = the inside of the C); drop = gap below."""
    return [pem(x_top + xh, y, -drop) for xh in (BL['pem_top'], BL['pem_bottom'])]


def formed_nuts():
    """Nuts on the formed strap (strap frame): top nut under the top leg at the ear stud, lug nut on the bottom leg, heads inside the C."""
    zt = S.POWER['bar_top'] - ST['z_bl']
    return [pem(0.0, 0.0, zt - ST['t'], head_down=True), pem(ST['lug'], 0.0, ST['t'], head_down=False)]


def blank(x_top, y=0.0, extra=0.0):
    """flat() moved to (x_top, y); extra = length left on at the top end (the as-cut blank)."""
    b = flat().moved(Location((x_top - FX, y, 0)))
    if extra:
        b += Pos(x_top - extra / 2, y, BL['t'] / 2) * Box(extra, BL['w'], BL['t'])
    return b


def named(shape, name):
    shape.label = name
    return shape


def model_steps():
    """Write ST185-FB-117_model.step and ST185-FB-117_stages.step into <work>/src/st185_fb117 and beside the Fusion STEP."""
    src = os.path.join('src', JOB)
    os.makedirs(src, exist_ok=True)
    tr = ST['trim']
    parts = [named(formed(), 'STRAP_FORMED')] + [named(n, 'PEM_%s_FORMED_%d' % (PM['pn'], i + 1)) for i, n in enumerate(formed_nuts())]
    parts += [named(flat(), 'BLANK_FINISHED')] + [named(n, 'PEM_%s_FLAT_%d' % (PM['pn'], i + 1)) for i, n in enumerate(flat_nuts(FX))]
    mdl = os.path.join(src, 'ST185-FB-117_model.step')
    export_step(Compound(children=parts, label='ST185-FB-117'), mdl)
    st = [named(blank(FX, 0.0, tr), 'S1_BLANK_AS_CUT')]
    st += [named(n, 'S1_PEM_%d_LOOSE' % (i + 1)) for i, n in enumerate(flat_nuts(FX, 0.0, drop=10.0))]
    st += [named(blank(FX, -40.0), 'S2_BLANK'), named(Pos(FX - tr / 2, -40.0, BL['t'] / 2) * Box(tr, BL['w'], BL['t']), 'S2_TRIM_OFFCUT')]
    st += [named(n, 'S2_PEM_%d_PRESSED' % (i + 1)) for i, n in enumerate(flat_nuts(FX, -40.0))]
    st += [named(blank(FX, -80.0), 'S3_BLANK_TRIMMED')] + [named(n, 'S3_PEM_%d' % (i + 1)) for i, n in enumerate(flat_nuts(FX, -80.0))]
    stg = os.path.join(src, 'ST185-FB-117_stages.step')
    export_step(Compound(children=st, label='ST185-FB-117 stages'), stg)
    for f in (mdl, stg):
        shutil.copy(f, os.path.join(REV7, os.path.basename(f)))
    return mdl, stg


def main():
    mdl, stg = model_steps()
    if os.environ.get('FB117_MODEL_ONLY'):
        print('model only:', mdl, stg)
        return
    x0, L = -ST['top_in'], BL['length']
    zt = S.POWER['bar_top'] - ST['z_bl']            # top of the top leg in the strap frame (40.5)
    xwo, xlip = ST['web'][1], ST['web'][1] + ST['lip']
    xbl0 = ST['lug'] - PM['edge']
    hw, hl = BL['w'] / 2, BL['w_low'] / 2
    sp = dict(project=specs.PROJECT_NAME, drawn=specs.DRAWN_BY, job=JOB, file=mdl, process='machined', single=False, offset=(0, 0, 0),
              rotate=[], pn='ST185-FB-117', rev='A.01',   # A.01 (R147 clerical): N15 proof-test note
              title='POWER OUTPUT C-STRAP 3 x 15 (FORMED + FLAT BLANK)',
              material='C110 COPPER, TINNED', ordinates=False, overall=False, max_hole_groups=1,
              source='Power_Strap_Out_CuC110_15x3_C.step (Fusion) + flat blank from spec.strap_blank() (build123d)',
              hidden=False, revlog=os.path.join(REV7, 'ST185-FB-117.REVLOG.md'),
              radius_text={ST['ri']: 'R1 INSIDE', ST['ri'] + ST['t']: 'skip'},
              dims=[
                  # formed strap, front view (x along the legs, z up)
                  ('lin', 'front', (x0, 0, zt), (xwo, 0, zt), 'h', 'above'),
                  ('lin', 'front', (x0, 0, zt), (0, 0, zt), 'h', 'above', {'tier': 2, 'text': '6.5 (TOP PEM)'}),
                  ('lin', 'front', (xbl0, 0, 0), (xwo, 0, 0), 'h', 'below'),
                  ('lin', 'front', (xbl0, 0, 0), (ST['lug'], 0, 0), 'h', 'below', {'tier': 2, 'text': '7.1 (LUG PEM)'}),
                  ('lin', 'front', (x0, 0, 0), (x0, 0, zt), 'v', 'left'),
                  # formed strap, top view
                  ('lin', 'top', (xwo, -hw, 0), (xlip, -hw, 0), 'h', 'below', {'text': '2.0 LIPS'}),
                  ('lin', 'top', (x0, -hw, zt), (x0, hw, zt), 'v', 'left'),
                  # flat blank, top view (x from its top end)
                  ('lin', 'top', (FX, hw, 0), (FX + L, hw, 0), 'h', 'above', {'text': '%.2f FLAT' % L}),
                  ('lin', 'top', (FX, hw, 0), (FX + BL['pem_bottom'], hw, 0), 'h', 'above', {'tier': 2}),
                  ('lin', 'top', (FX, -hw, 0), (FX + BL['low_from'], -hw, 0), 'h', 'below', {'tier': 2}),
                  ('lin', 'top', (FX + L, -hl, 0), (FX + L, hl, 0), 'v', 'right'),
                  ('lin', 'top', (FX, -hw, 0), (FX + BL['kerf']['x'][0], -hw, 0), 'h', 'below', {'tier': 3, 'text': '%.2f KERF START' % BL['kerf']['x'][0]}),
              ],
              notes=[
                  'C110 TINNED, CUT FROM 3 x 15 BAR (BOPAODAO B09Z7NBLDK). QTY 14 PER CAR (EVERY POWER AMI POSITION; THE IN ROW TURNS IT 180 DEG).',
                  'BLANK: SAW %.2f LONG (%.1f OVER AT THE TOP END), DRILL 2X ⌀6.35 +0.08/0 (PEM %s); 2X KERF 0.5 WIDE AT 3.5 - 4.0 '
                  'EACH SIDE OF CL, %.2f TO %.2f, THEN NOTCH 3.5 - 7.5 TO %.2f; MILL / FILE BOTH EDGES TO %.1f FROM %.2f TO THE BOTTOM END.'
                  % (BL['cut_length'], ST['trim'], PM['pn'], BL['kerf']['x'][0], BL['kerf']['x'][1], BL['notch']['x'][1], BL['w_low'], BL['low_from']),
                  'PRESS BOTH NUTS (HEADS INSIDE THE C), THEN TRIM THE TOP END BACK TO 6.5 FROM THE TOP NUT (PEM EDGE 7.1 WHILE PRESSING).',
                  'BEND 2X 90 DEG ROUND R%.1f INSIDE, BEND CL %.2f AND %.2f FROM THE TOP END (K %.2f, %.2f PER BEND); BEND 1 ON THE TONGUE ONLY, LIPS STAY '
                  'FLAT. CHECK THE FIRST PART.' % (ST['ri'], BL['bend_centres'][0], BL['bend_centres'][1], BL['k'], BL['bend_allowance']),
                  'FIRST ARTICLE (N15): ONE SAMPLE STRAP, M5 x 10 INTO EACH NUT AT 6 N.m (1.5 x 4 N.m); NUT MUST NOT TURN OR PUSH OUT; SCRAP IT. '
                  'BREAK EDGES 0.2-0.4 (R138), KEEP TIN ON CLAMP FACES.',
              ])
    os.makedirs('out/' + JOB, exist_ok=True)
    stats = part.make_part(sp, 'out/%s/ST185-FB-117.pdf' % JOB, 'out/%s/ST185-FB-117.dxf' % JOB, 'previews/ST185-FB-117')
    print('OK', stats)


if __name__ == '__main__':
    main()
