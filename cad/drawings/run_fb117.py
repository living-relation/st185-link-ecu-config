"""ST185-FB-117 - POWER output copper C-strap (DECISIONS R155, N14 = B): shop drawing of the formed strap + its flat blank.

The formed strap is the Fusion model (cad/fusebox/rev7/Power_Strap_Out_CuC110_15x3_C.step, 14 identical straps; the OUT-row JB1 one is
taken and moved to the strap frame: x = 0 at the AMI ear stud (top PEM), + toward the web; z = 0 at the bottom leg underside). The flat
blank to its right is made here with build123d from spec.strap_blank() (the same numbers the Fusion build uses), finished length, before
the two bends. Both go into one drawing model (<work>/src/st185_fb117/ST185-FB-117_model.step; a copy beside the Fusion STEP).
Run in WSL with the handbuilt-cad venv, from the repo root:

    ST185_WORK=<work dir> ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_fb117.py

-> <work>/out/st185_fb117/ST185-FB-117.pdf / .dxf, <work>/previews/ST185-FB-117_sh1.png / _sh2.png. Sheet 2 (handbuilt-cad DRAWING-RULES 31)
= 4 install steps: stud pressed in, bent, nut + holder (ST185-FB-118) into the C, dropped into its well in the base (cut down to one well). Rev log: cad/fusebox/rev7/ST185-FB-117.REVLOG.md.
FB117_MODEL_ONLY=1 writes the two model STEPs only (R196 / R197: models first, drawings after):
  ST185-FB-117_model.step  - the formed strap and its flat blank, each with its PEM FHS-M5-12 flush stud at the lug end (N37, 2026-10-19);
  ST185-FB-117_stages.step - the steps, one named solid per piece: S1 (y 0) blank with the stud below its hole, head side down; S2 (y -40)
      stud pressed flush; S3 (y -80) bent; S4 (y -120) the DIN 934 top nut and its printed holder pulled 25 out of the C's open side.
The stud is built from PEM Bulletin FH p. FH-5 (spec.STRAP_STUD), the nut from DIN 934, the holder from spec.NUT_HOLDER (as build_fusion).
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
from specs_1018 import TOL  # noqa: E402  (tolerance block without the edge-break line, R191)
import part  # noqa: E402
from build123d import Box, Compound, Cylinder, Location, Pos, RegularPolygon, export_step, extrude, import_step  # noqa: E402

REV7 = os.path.join(REPO, 'cad', 'fusebox', 'rev7')
JOB = 'st185_fb117'
ST, BL, SD, TN, NH = S.STRAP, S.strap_blank(), S.STRAP_STUD, S.STRAP_TOP_NUT, S.NUT_HOLDER
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
    for xh, dh in ((BL['pem_top'], BL['hole_top']), (BL['pem_bottom'], BL['hole_lug'])):    # N37: 5.5 clearance (top), 5.0 FHS stud (lug)
        b -= Pos(FX + xh, 0, t / 2) * Cylinder(dh / 2, t + 2)
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


def stud(x, y, z_face, out):
    """PEM FHS-M5-12 flush-head stud, head flush in the face at z_face (its head sits in the copper and is not drawn); the shank runs
    L along `out` (+1 / -1 in z) through the 5.0 hole and out of the other face."""
    return Pos(x, y, z_face + out * SD['L'] / 2) * Cylinder(SD['d'] / 2, SD['L'])


def flat_stud(x_top, y=0.0, drop=0.0):
    """The lug-end stud on a flat blank whose top end is at x_top: head flush in the underside (= the inside of the C), shank up; drop =
    gap below (loose, before pressing)."""
    return stud(x_top + BL['pem_bottom'], y, -drop, +1)


def formed_stud():
    """The lug-end stud on the formed strap (strap frame): head flush in the bottom leg's inside face (z t), shank down under the leg."""
    return stud(ST['lug'], 0.0, ST['t'], -1)


def top_nut(dx=0.0):
    """DIN 934 M5 top nut (RS 527-268) under the top leg at the ear stud, flats facing +-x, its top on the copper; dx = pulled out of the C."""
    zn = S.POWER['bar_top'] - ST['z_bl'] - ST['t']
    n = Pos(dx, 0, zn - TN['m'] / 2) * extrude(RegularPolygon(TN['s'] / 2, 6, major_radius=False, rotation=30), TN['m'] / 2, both=True)
    return n - Pos(dx, 0, zn - TN['m'] / 2) * Cylinder(2.5, TN['m'] + 2)


def holder(dx=0.0):
    """The printed top-nut holder (Power_NutHolder_PA12_printed, build_fusion nut_holder) in the strap frame, dx = pulled out of the C."""
    zn, zb = S.POWER['bar_top'] - ST['z_bl'] - ST['t'], ST['t']
    xo, xb_ = -(SD['edge'] - ST['lug']), ST['web'][0] - ST['ri'] - NH['bend_clr']
    col = Pos(dx + (xo + xb_) / 2, 0, (zb + zn) / 2) * Box(xb_ - xo, 2 * NH['y_half'], zn - zb)
    col += Pos(dx + (xo + ST['web'][0]) / 2, 0, sum(NH['web_z']) / 2 - ST['z_bl']) * Box(ST['web'][0] - xo, 2 * NH['y_half'], NH['web_z'][1] - NH['web_z'][0])
    zp = zn - TN['m'] - NH['clr']
    col -= Pos(dx, 0, (zp + zn + 1) / 2) * extrude(RegularPolygon(TN['s'] / 2 + NH['clr'], 6, major_radius=False, rotation=30), (zn + 1 - zp) / 2, both=True)
    zr = zp - NH['bore_below']
    col -= Pos(dx, 0, (zr + zn) / 2) * Cylinder(NH['bore'] / 2, zn - zr)
    col -= Pos(dx + (xb_ + 1.0) / 2, 0, (zr + zn) / 2) * Box(xb_ + 1.0, NH['bore'], zn - zr)
    return col


def blank(x_top, y=0.0, extra=0.0):
    """flat() moved to (x_top, y); extra = length left on at the top end (the as-cut blank)."""
    b = flat().moved(Location((x_top - FX, y, 0)))
    if extra:
        b += Pos(x_top - extra / 2, y, BL['t'] / 2) * Box(extra, BL['w'], BL['t'])
    return b


def base_at_strap():
    """The POWER base (FB-101) cut down to the block round the OUT-row JB1 well, in the strap frame (as formed()): sheet 2, step 4."""
    b = import_step(os.path.join(REV7, 'Power_Base_PA12_printed.step')).solids()[0]
    px, py = S.PLACE['POWER']
    y_jb1 = S.AMI_Y0 + [n for n, _a in S.AMI_ROWS['OUT']].index('JB1') * S.AMI_PITCH + py
    x_out = S.POWER['x_bar'] + S.AMI_IN_OFF + S.AMI['c'] + px
    b = b.moved(Location((-x_out, -y_jb1, -ST['z_bl'])))
    keep = Pos(10.0, 0, 15.0) * Box(56.0, 2 * S.AMI_PITCH - 4.0, 60.0)
    return b.intersect(keep).solids()


def named(shape, name):
    shape.label = name
    return shape


def model_steps():
    """Write ST185-FB-117_model.step and ST185-FB-117_stages.step into <work>/src/st185_fb117 and beside the Fusion STEP."""
    src = os.path.join('src', JOB)
    os.makedirs(src, exist_ok=True)
    parts = [named(formed(), 'STRAP_FORMED'), named(formed_stud(), 'STUD_%s_FORMED' % SD['pn'])]
    parts += [named(flat(), 'BLANK_FINISHED'), named(flat_stud(FX), 'STUD_%s_FLAT' % SD['pn'])]
    mdl = os.path.join(src, 'ST185-FB-117_model.step')
    export_step(Compound(children=parts, label='ST185-FB-117'), mdl)
    # N37: nothing is trimmed any more (no clinch nut at the top end); steps: stud beside its hole, stud pressed, bent, top nut + holder in
    st = [named(blank(FX, 0.0), 'S1_BLANK'), named(flat_stud(FX, 0.0, drop=15.0), 'S1_STUD_LOOSE')]
    st += [named(blank(FX, -40.0), 'S2_BLANK'), named(flat_stud(FX, -40.0), 'S2_STUD_PRESSED')]
    st += [named(formed().moved(Location((0, -80.0, 0))), 'S3_STRAP_BENT'), named(formed_stud().moved(Location((0, -80.0, 0))), 'S3_STUD')]
    st += [named(formed().moved(Location((0, -120.0, 0))), 'S4_STRAP'), named(formed_stud().moved(Location((0, -120.0, 0))), 'S4_STUD'),
           named(top_nut(-25.0).moved(Location((0, -120.0, 0))), 'S4_TOP_NUT_DIN934'), named(holder(-25.0).moved(Location((0, -120.0, 0))), 'S4_NUT_HOLDER')]
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
    xbl0 = ST['lug'] - SD['edge']
    hw, hl = BL['w'] / 2, BL['w_low'] / 2
    sp = dict(project=specs.PROJECT_NAME, drawn=specs.DRAWN_BY, job=JOB, file=mdl, process='machined', single=False, offset=(0, 0, 0),
              rotate=[], pn='ST185-FB-117', rev='D',      # model D (N37, #330); drawing pass 2026-10-19 (R196)
              title='POWER OUTPUT C-STRAP 3 x 15 (FORMED + FLAT BLANK)',
              material='C110 COPPER, TINNED', ordinates=False, overall=False, max_hole_groups=1,
              source='Power_Strap_Out_CuC110_15x3_C.step (Fusion) + flat blank from spec.strap_blank() (build123d)',
              hidden=False, revlog=os.path.join(REV7, 'ST185-FB-117.REVLOG.md'),
              radius_text={ST['ri']: 'R1 INSIDE', ST['ri'] + ST['t']: 'skip'},
              dims=[
                  # formed strap, front view (x along the legs, z up)
                  ('lin', 'front', (x0, 0, zt), (xwo, 0, zt), 'h', 'above'),
                  ('lin', 'front', (x0, 0, zt), (0, 0, zt), 'h', 'above', {'tier': 2, 'text': '6.5 (TOP HOLE)'}),
                  ('lin', 'front', (xbl0, 0, 0), (xwo, 0, 0), 'h', 'below'),
                  ('lin', 'front', (xbl0, 0, 0), (ST['lug'], 0, 0), 'h', 'below', {'tier': 2, 'text': '7.2 (LUG STUD)'}),
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
              tol=TOL,
              notes=[
                  'C110 TINNED COPPER FROM 3 x 15 BAR (BOPAODAO B09Z7NBLDK). 14 PER CAR. KEEP THE TIN ON THE CLAMP FACES.',
                  'SAW %.2f LONG. DRILL ⌀%.1f AT THE TOP HOLE, ⌀%.1f +0.08/0 AT THE LUG HOLE.' % (BL['cut_length'], BL['hole_top'], BL['hole_lug']),
                  'SLOTS 0.5 WIDE, 3.5 - 4.0 EACH SIDE OF CENTRE, %.2f TO %.2f; NOTCH 3.5 - 7.5 TO %.2f; FILE TO %.1f WIDE FROM %.2f TO THE END.'
                  % (BL['kerf']['x'][0], BL['kerf']['x'][1], BL['notch']['x'][1], BL['w_low'], BL['low_from']),
                  'PRESS THE PEM %s STUD IN FROM THE INSIDE FACE UNTIL ITS HEAD IS FLUSH. NOTHING IS TRIMMED.' % SD['pn'],
                  'BEND 2 x 90 DEG, R%.1f INSIDE, AT %.2f AND %.2f FROM THE TOP END; BEND 1 ON THE TONGUE ONLY. CHECK THE FIRST PART.'
                  % (ST['ri'], BL['bend_centres'][0], BL['bend_centres'][1]),
                  'FIRST PART: M5 FLANGE NUT ON THE STUD AT 6 N·m; THE STUD MUST NOT TURN OR PUSH OUT. SCRAP THAT PART. ASSEMBLY: SHEET 2.',
              ],
              stage_items=[
                  dict(item=1, pn='ST185-FB-117', desc='C-STRAP', shapes=[formed()]),
                  dict(item=2, pn='PEM ' + SD['pn'], desc='FLUSH STUD', shapes=[formed_stud()]),
                  dict(item=3, pn='RS 527-268', desc='HEX NUT M5 DIN 934', shapes=[top_nut()]),
                  dict(item=4, pn='ST185-FB-118', desc='TOP-NUT HOLDER', shapes=[holder()]),
                  dict(item=5, pn='ST185-FB-101', desc='POWER BOX BASE (PART)', shapes=base_at_strap()),
              ],
              stage_sheets=[[
                  dict(no=1, title='PRESS THE STUD IN FROM THE INSIDE FACE', subtitle='FLAT BLANK, EXPLODED (NOT TO SCALE)',
                       custom=[(1, flat(), (0, 0, 0)), (2, flat_stud(FX), (0, 0, -15.0))]),
                  dict(no=2, title='STUD FLUSH, THEN BEND 2 x 90 DEG', subtitle='NOTHING IS TRIMMED (NOT TO SCALE)',
                       custom=[(1, formed(), (0, 0, 0)), (2, formed_stud(), (0, 0, 0))]),
                  dict(no=3, title='NUT INTO THE HOLDER, HOLDER INTO THE C', subtitle='EXPLODED (NOT TO SCALE)', base=[1, 2],
                       custom=[(4, holder(), (-25.0, 0, 0)), (3, top_nut(), (-25.0, 0, 15.0))]),
                  dict(no=4, title='DROP THE STRAP STRAIGHT DOWN INTO ITS WELL', subtitle='EXPLODED, BASE CUT DOWN TO ONE WELL (NOT TO SCALE)',
                       base=[5], custom=[(1, formed(), (0, 0, 70.0)), (2, formed_stud(), (0, 0, 70.0)), (3, top_nut(), (0, 0, 70.0)),
                                         (4, holder(), (0, 0, 70.0))]),
              ]])
    os.makedirs('out/' + JOB, exist_ok=True)
    stats = part.make_part(sp, 'out/%s/ST185-FB-117.pdf' % JOB, 'out/%s/ST185-FB-117.dxf' % JOB, 'previews/ST185-FB-117')
    print('OK', stats)


if __name__ == '__main__':
    main()
