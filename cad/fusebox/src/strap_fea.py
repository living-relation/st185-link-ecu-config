"""FEA of the POWER strap snap hooks (DECISIONS R155, N14 = B): 100 N straight up on the hook underside, arm root fixed; PA12 HP MJF
(spec.PA12). Card rule: safety factor >= 2. Also reports how far the hook tip moves out (it must keep part of its `over` across the lip).

Builds the two arm shapes from spec.py (OUT: the freed base skirt; IN: the arm cut free in the deck block) with build123d, then runs the
handbuilt-cad quick FEA (Gmsh + CalculiX, C3D10). Run in WSL from the repo root:

    ~/projects/handbuilt-cad/.venv/bin/python cad/fusebox/src/strap_fea.py [work_dir]

work_dir (default _research/strap_fea, untracked) gets the STEP + solver files; the numbers go to cad/fusebox/rev7/strap_fea.json (tracked).
Claude Code, 2026-10-17.
"""
import json
import os
import subprocess
import sys

import numpy as np
from build123d import Box, Pos, export_step, Plane, BuildSketch, Polygon, extrude

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import spec as S  # noqa: E402

HB = os.environ.get('HANDBUILT_CAD') or os.path.expanduser('~/projects/handbuilt-cad')
SIM_PY = os.environ.get('SIM_PY') or os.path.expanduser('~/simvenv/bin/python')
LOAD_N = 100.0
BAR_LOAD_N = 20.0      # markup 2026-10-17: a bar hold-down hook (the bar is bolted at every stud; the hook holds its lift between them)


def bx(x0, y0, z0, x1, y1, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def geometry():
    """Arm + hook of each row in box coordinates (x along the box, z up). Returns {row: dict(solid, zh0, tip_x, sign)}; sign = +1 when
    the hook reaches toward +x from the arm (IN row), -1 toward -x (OUT row)."""
    PW, ST = S.POWER, S.STRAP
    btop, z_t = PW['bar_top'], PW['z_t']
    zh0 = btop + S.HOOK_GAP        # markup 2026-10-17 (R157): the hook bears on the lips
    out = {}
    for row, sgn in (('OUT', +1), ('IN', -1)):
        T = S.STRAP_TAB[row]
        x_out = PW['x_bar'] + sgn * S.AMI_IN_OFF + sgn * S.AMI['c']
        lip_end = x_out + sgn * (ST['web'][1] + ST['lip'])            # outer end of the lips
        tip = lip_end - sgn * T['over']                                # hook tip, over the lips
        hw = T['w'] / 2
        if row == 'OUT':
            a0, a1 = PW['L'] - S.SKIRT, PW['L'] + S.SKIRT_OUT          # the skirt is the arm
        else:
            a1 = lip_end - ST['ledge'] - T['slot']                     # ledge band past the lip end, then the slot
            a0 = a1 - T['t']
        zh1 = zh0 + T['hook_t']
        arm = bx(a0, -hw, T['root'], a1, hw, zh1)
        hx0, hx1 = (tip, a0) if row == 'OUT' else (a1, tip)
        hook = bx(hx0, -hw, zh0, hx1, hw, zh1)
        # 45 deg lead-in on the hook's top inner edge (the strap lips push the hook out on the way in)
        c = 0.9
        with BuildSketch(Plane.XZ) as sk:
            if row == 'OUT':
                Polygon((tip - 0.01, zh1 - c), (tip - 0.01, zh1 + 0.01), (tip + c, zh1 + 0.01), align=None)
            else:
                Polygon((tip + 0.01, zh1 - c), (tip + 0.01, zh1 + 0.01), (tip - c, zh1 + 0.01), align=None)
        cham = extrude(sk.sketch, hw + 1, both=True)
        solid = arm + hook - cham
        out[row] = dict(solid=solid, zh0=zh0, tip_x=tip, sign=-1 if row == 'OUT' else +1, arm=(round(a0, 2), round(a1, 2)), root=T['root'],
                        arm_len=round(zh0 - T['root'], 2), t=round(a1 - a0, 2), w=T['w'], over=T['over'], load=LOAD_N, d_ins=T['over'])
    # markup 2026-10-17 (R157): the bar hold-down hooks too - BAR = the POWER deck tab (arm cut free of the deck block), BAR_RB = the battery
    # block's standing tab. Frame: bar edge at x 0, bar at x < 0; the arm stands s0 out, its hook reaches `over` back over the bar. No lead-in
    # (conservative). Load BAR_LOAD_N up on the hook: the bar is bolted at every stud, so a hook only ever holds a bar's lift between studs.
    TB = S.BAR_TAB
    for row, (t_, w_, s0, zr) in (('BAR', (TB['t'], TB['w'], S.CLR + TB['slot'], PW['z_t'] - TB['root'])),
                                  ('BAR_RB', (TB['t_stand'], TB['w_stand'], 1.0 + TB['gap'], S.RB['floor']))):
        zb = btop if row == 'BAR' else (10.0 + 30.0 - S.AMI['ear_t'])        # battery block bar top = HCR150 terminal top - AMI ear (build_relay_block)
        z0 = zb + S.HOOK_GAP
        z1 = z0 + TB['hook_t']
        hw = w_ / 2
        solid = bx(s0, -hw, zr, s0 + t_, hw, z1) + bx(-TB['over'], -hw, z0, s0 + 0.01, hw, z1)
        out[row] = dict(solid=solid, zh0=z0, tip_x=-TB['over'], sign=-1, arm=(round(s0, 2), round(s0 + t_, 2)), root=zr, arm_len=round(z0 - zr, 2),
                        t=t_, w=w_, over=TB['over'], load=BAR_LOAD_N, d_ins=TB['over'] + S.CLR)
    return out


def displacements(fea_dir):
    lines = open(os.path.join(fea_dir, 'job.inp')).read().splitlines()
    i = lines.index('*NODE') + 1
    P = {}
    while not lines[i].startswith('*'):
        t = lines[i].split(',')
        P[int(t[0])] = [float(x) for x in t[1:4]]
        i += 1
    dat = open(os.path.join(fea_dir, 'job.dat')).read().split('stresses')[0].split('displacements')[1]
    U = {}
    for l in dat.splitlines()[1:]:
        t = l.split()
        if len(t) == 4:
            try:
                U[int(t[0])] = [float(x) for x in t[1:]]
            except ValueError:
                pass
    return P, U


def main(argv):
    work = argv[0] if argv else os.path.join(REPO, '_research', 'strap_fea')
    os.makedirs(work, exist_ok=True)
    res = {}
    for row, g in geometry().items():
        step = os.path.join(work, 'strap_tab_%s.step' % row)
        export_step(g['solid'], step)
        r = subprocess.run([SIM_PY, os.path.join(HB, 'tools', 'quick_fea.py'), step, '--fix', 'z:%g' % g['root'], '--load', 'z:%g' % g['zh0'],
                            '--force', '0,0,%g' % g['load'], '--E', str(S.PA12['E']), '--nu', str(S.PA12['nu']), '--yield', str(S.PA12['sy']),
                            '--size', '0.6'], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stdout + r.stderr)
        fd = os.path.splitext(step)[0] + '_fea'
        sm = json.load(open(os.path.join(fd, 'summary.json')))
        P, U = displacements(fd)
        tipn = [n for n, p in P.items() if abs(p[0] - g['tip_x']) < 0.05 and abs(p[2] - g['zh0']) < 0.05]
        open_ = float(np.mean([U[n][0] for n in tipn])) * -g['sign']        # + = the tip moves away from the lips
        up_ = float(np.mean([U[n][2] for n in tipn]))
        res[row] = dict(arm_x=g['arm'], arm_t=g['t'], w=g['w'], root_z=g['root'], arm_len=g['arm_len'], over=g['over'], load_N=g['load'],
                        peak_MPa=round(sm['peak_von_mises_MPa'], 1), p99_9_MPa=round(sm['von_mises_99_9pct_MPa'], 1),
                        SF=round(sm['safety_factor'], 2), SF_99_9=round(sm['safety_factor_99_9pct'], 2),
                        max_disp_mm=round(sm['max_displacement_mm'], 3), hook_tip_out_mm=round(open_, 3), hook_tip_up_mm=round(up_, 3),
                        overlap_left_mm=round(g['over'] - open_, 3), nodes=sm['nodes'],
                        insert=dict(strain_pct=round(150 * g['t'] * g['d_ins'] / g['arm_len'] ** 2, 2), limit_pct=S.SNAP_EPS, deflection_mm=g['d_ins'],
                                    push_N=round(3 * S.PA12['E'] * (g['w'] * g['t'] ** 3 / 12) * g['d_ins'] / g['arm_len'] ** 3, 1)))
        print(row, json.dumps(res[row]))
    res['note'] = ('CalculiX C3D10 linear static, PA12 E %g / nu %g, yield %g MPa (HP data sheet 4AA6-4895ENE); 100 N up spread over the hook '
                   'underside, arm root fixed; OUT row with the cover off (with it on the skirt cannot open). Card rule SF >= 2. BAR / BAR_RB: the bar hold-down '
                   'hooks, %g N up, hook bearing on the copper (R157). Insert strain 1.5 t y / L^2 against SNAP_EPS (HP MJF Handbook snap-fits: < 1/3 of '
                   'the elongation at yield, HP 5200 PA 12 TDS 8 %% Z).' % (S.PA12['E'], S.PA12['nu'], S.PA12['sy'], BAR_LOAD_N))
    with open(os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'strap_fea.json'), 'w') as f:
        json.dump(res, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
