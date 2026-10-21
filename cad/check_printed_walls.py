"""Wall and attachment check of the printed fuse box parts (DECISIONS R127, Dan 2026-10-15: "check all boxes for walls 1.95mm thick or
less. check all boxes for floating or nearly floating features or cantilevers attached by less than 3mm thick material"):
  W  walls > 1.95 mm: the part is cut in planes every STEP mm along x, y and z; in every section the material thinner than 1.95 mm is
     what an opening (shrink by 0.975, grow back by 0.975, mitred corners down to 60 deg) takes away. Exact in the plane, so a 2.0 mm
     wall passes and a 1.95 mm one fails. Sections through the same spot merge into one 3-D spot; a spot seen in one section only is a
     plane grazing a curved face (the bottom of a saddle arc) and is dropped.
  A  attached by >= 3 mm: voxels of PITCH mm, opened with a cube of ~3 mm. Material that survives is the >= 3 mm "body". A thin
     piece (< 3 mm) that meets the body in ONE place only is a cantilever attached by less than 3 mm (a thin wall held at two or more
     places, or a part that is all thin like a cover or pan, is a wall and is left to W); a thick piece that meets the main body only
     through thin material is attached by less than 3 mm too.
  Covers, belly pans and the R1 clip are shells of the R73 2.5 / 2.0 wall (no >= 3 mm body to hang anything from): A does not apply,
  W checks them. A thin piece standing less than SKIN mm proud of the >= 3 mm body is the voxel skin of a sloped or tapered face (the
  angular legs), not a cantilever, and is not listed (the count is kept as attach_skin).
EXEMPT (R127 sweep, Dan 2026-10-16: "fix the ones you found as long as they don't alter the function and installability of the parts"): the
build records a box round every spot that has to stay thin (fusebox_report.json "wall_exempt", reasons in spec.WALL_EXEMPT); a W piece
or A spot inside one is not listed but counted under its name ("exempt").
CLASSES (DECISIONS R151, Dan 2026-10-17: "Minimum thickness for walls is for critical or structural features, and doesn't apply to
everything. If something is questionable or unclear, it should be flagged for change or approval."): every W / A spot gets a class from
cad/fusebox/src/wall_classes.py - structural (check_printed_solid.py S4 / S5 fail on it), non-structural or questionable (FLAGGED: listed
for Dan, never failed, never dropped). Each part also records its x / y / z 'bounds' and, for a base, its deck 'outline' (the map needs
them); the flag list for Dan goes to cad/fusebox/rev7/WALL-FLAGS.md.
Writes cad/fusebox/rev7/wall_check.json (tracked; check_printed_solid.py S4 / S5 reads it, CI has no STL) and prints every spot.
Detection is handbuilt-cad's generic tools/checks/check_printed_walls.py (HANDBUILT_CAD, default ~/projects/handbuilt-cad); this file
keeps st185's settings and outputs. Run in WSL with the handbuilt-cad venv (trimesh, shapely, scipy, PIL), from the repo root,
--src = the checkout with the STLs,
--out = the checkout to write into (default --src):
    ~/projects/handbuilt-cad/.venv/bin/python cad/check_printed_walls.py --src /mnt/c/projects/active/st185-link-ecu-config
--classify re-sorts the spots already in wall_check.json (after a FEATURES / map change) and records bounds / outline from the STLs,
without re-running W / A.
Claude Code, 2026-10-15.
"""
import argparse, importlib.util, json, os, subprocess, sys, time
import trimesh

# Detection (W sections, A voxels, every R127 fix) lives in handbuilt-cad's generic checker, tools/checks/check_printed_walls.py
# (universal wall check). This file keeps only st185's settings and glue: the parts, the R127 exemption boxes from the build report,
# the R1 snap barbs, the R151 classes and the outputs check_printed_solid.py S4 / S5 reads in CI (which has no STLs and no
# handbuilt-cad, and never runs this file). handbuilt-cad is found through HANDBUILT_CAD (default ~/projects/handbuilt-cad).
WALL, ATTACH = 1.95, 3.0          # mm: fail at or under WALL; attachment under ATTACH (R127)
STEP, PITCH = 0.5, 0.2            # mm: section spacing (W), voxel size (A)
OPTS = dict(step=STEP, pitch=PITCH,
            min_area=0.3,         # mm2: smaller W pieces in a section are tessellation noise on curved faces
            min_vol=2.0,          # mm3: smaller A pieces are voxel noise
            snap=1e-4,            # mm: section segment ends closer than this are one point
            despike=0.02,         # mm: spikes / slits under 0.04 where two cut faces meet are below what MJF prints (~0.08)
            sliver=0.01,          # mm: round-off slivers along shared edges
            graze=4,              # one axis family, under 4 sections = planes grazing a square edge (R127 amendment)
            skin=1.5,             # mm: a thin piece must stand this far out of the >= 3 mm body to be a cantilever
            cluster_tol=0.6)
SHELLS = ('_Cover_', '_Pan_', '_Retainer_')
FUSEBOX = 'cad/fusebox/rev7'
PARTS = ['Power_Base_PA12_printed', 'Power_Pan_PA12_printed', 'Power_Cover_PA12_printed', 'Power_Retainer_R1_PA12_printed',
         'Logic_Base_PA12_printed', 'Logic_Pan_PA12_printed', 'Logic_Cover_PA12_printed',
         'BattRelay_Base_PA12_printed', 'BattRelay_Cover_PA12_printed', 'Power_NutHolder_PA12_printed']
HB = None
# Oldest handbuilt-cad commit whose checker gives st185's results (handbuilt-cad #18, proved byte-identical in st185 #390).
# hb() needs handbuilt-cad checked out at exactly HB_COMMIT (override with HANDBUILT_CAD_COMMIT=<sha>). A newer checkout is
# opt-in only: HANDBUILT_CAD_ALLOW_NEWER=1 accepts any descendant of HB_COMMIT and prints the commit it used.
HB_COMMIT = '0c426f019a6b80172c766b9300c194fbec4154a3'


def hb():
    """handbuilt-cad's generic wall checker module (loaded on first use, under its own name)."""
    global HB
    if HB is None:
        root = os.path.expanduser(os.environ.get('HANDBUILT_CAD') or '~/projects/handbuilt-cad')
        path = os.path.join(root, 'tools', 'checks', 'check_printed_walls.py')
        if not os.path.isfile(path):
            raise SystemExit('handbuilt-cad wall checker not found at %s - set HANDBUILT_CAD to a handbuilt-cad checkout' % path)
        head = _hb_check_commit(root)
        # handbuilt-cad imports its own wall_classes (and puts its folder first on sys.path); keep st185's apart and put both
        # sys.modules and sys.path back exactly as they were, even if loading fails.
        mine, had_mine = sys.modules.get('wall_classes'), 'wall_classes' in sys.modules
        saved_path = list(sys.path)
        sys.modules.pop('wall_classes', None)
        try:
            sp = importlib.util.spec_from_file_location('hb_check_printed_walls', path)
            mod = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(mod)
        finally:
            sys.modules.pop('wall_classes', None)
            if had_mine:
                sys.modules['wall_classes'] = mine
            sys.path[:] = saved_path
        HB = mod
        print('handbuilt-cad wall checker: %s @ %s' % (path, head or 'unknown commit'))
    return HB


def _hb_check_commit(root):
    """handbuilt-cad's HEAD commit, after checking it is exactly the pin (HB_COMMIT or $HANDBUILT_CAD_COMMIT), or, only with
    HANDBUILT_CAD_ALLOW_NEWER=1, a descendant of the pin."""
    def git(*a):
        r = subprocess.run(['git', '-C', root] + list(a), capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    try:
        rc, head = git('rev-parse', 'HEAD')
    except OSError:
        raise SystemExit('git not found: cannot check the handbuilt-cad commit at %s' % root)
    if rc:
        raise SystemExit('%s is not a git checkout of handbuilt-cad (needed to check its commit)' % root)
    pin = os.environ.get('HANDBUILT_CAD_COMMIT') or HB_COMMIT
    if head.startswith(pin):
        return head
    if os.environ.get('HANDBUILT_CAD_ALLOW_NEWER') != '1':
        raise SystemExit('handbuilt-cad at %s is %s, not the pinned %s. Check out the pin (git -C %s checkout %s) or set '
                         'HANDBUILT_CAD_ALLOW_NEWER=1 to accept a newer commit' % (root, head[:12], pin[:12], root, pin[:12]))
    rc, _ = git('merge-base', '--is-ancestor', pin, 'HEAD')
    if rc == 1:
        raise SystemExit('handbuilt-cad at %s (%s) does not contain the pinned %s; pull it (git pull --ff-only)' % (root, head[:12], pin[:12]))
    if rc:
        shallow = git('rev-parse', '--is-shallow-repository')[1] == 'true'
        raise SystemExit('cannot check handbuilt-cad at %s against the pinned %s (git exit %d)%s' % (
            root, pin[:12], rc, ': it is a shallow clone without that commit; run git -C %s fetch --unshallow' % root if shallow
            else ': the pinned commit is not in this clone; run git -C %s fetch' % root))
    print('handbuilt-cad: HANDBUILT_CAD_ALLOW_NEWER=1, using %s (newer than the pinned %s)' % (head[:12], pin[:12]))
    return head


def section(m, axis, c):
    return hb().section(m, axis, c, OPTS['snap'], OPTS['despike'])


def walls(m, allow=(), seen=None):
    return hb().walls(m, WALL, STEP, allow, seen, OPTS)


def attachments(m, stats):
    return hb().attachments(m, ATTACH, PITCH, OPTS, stats)


def inside(g, b, tol=0.0):
    return hb().inside(g, b, tol)


def _wcl():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fusebox', 'src'))   # this checkout's spec / wall_classes
    import wall_classes
    return wall_classes


def exempt(name, src):
    """R127 sweep: (key, box) of every spot the build recorded as having to stay thin (fusebox_report.json "wall_exempt")."""
    rp = os.path.join(src, FUSEBOX, 'fusebox_report.json')
    ex = json.load(open(rp)).get('wall_exempt', []) if os.path.isfile(rp) else []
    return [(e['key'], e['box'], e.get('only')) for e in ex if e['part'] == name]


def allowed(name, src):
    """Named thin features that are not walls: the R1 retainer clip's snap barbs (spec.RETAINER barb x barb_h, at the top of each leg)."""
    if 'Retainer' not in name:
        return []
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fusebox', 'src'))   # this checkout's spec (--src may hold STLs only)
    import spec as S
    RT = S.RETAINER
    rr = json.load(open(os.path.join(src, FUSEBOX, 'fusebox_report.json')))['retainers']['POWER'][0]
    sx, sy = S.PLACE['POWER']
    zt = S.POWER['z_d'] + RT['leg_h']
    out = []
    for (lx, ly) in rr['legs']:
        r = RT['leg'][0] / 2 + RT['barb'] + 0.6
        out.append(('snap barb at leg (%.1f, %.1f), %.1f x %.1f (R123)' % (lx, ly, RT['barb'], RT['barb_h']),
                    [lx + sx - r, lx + sx + r, ly + sy - RT['leg'][1], ly + sy + RT['leg'][1], zt - RT['barb_h'] - 0.6, zt + 0.6]))
    return out


def extents(m, name, report):
    """R151 map inputs: the part's bounds and, for a base, the plan bounds of its outline without the legs, ears and end tabs: the
    section half way up the deck (POWER / LOGIC: deck block + skirt), or 2 mm above the 6 mm mount ears / end tabs (battery block rim;
    spec.LIMITER_M6 l = ear thickness)."""
    lo, hi = m.bounds
    out = dict(bounds=[round(float(v), 2) for v in (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])])
    if '_Base_' in name:
        WCL = _wcl()
        bx = (report.get('boxes_mm') or {}).get(WCL.box_of(name)) or {}
        z = (bx['z_d'] + bx['z_t']) / 2 if 'z_d' in bx and 'z_t' in bx else lo[2] + WCL.S.LIMITER_M6['l'] + 2.0
        reg = section(m, 2, z)
        if reg is not None and not reg.is_empty:
            b = reg.bounds
            out['outline'] = [round(float(v), 2) for v in (b[0], b[2], b[1], b[3])]
    return out


def classify_all(res, report, flags_md):
    """R151: class + why on every spot, the flagged count per part and in total, and WALL-FLAGS.md."""
    WCL = _wcl()
    total = 0
    for name, info in res['parts'].items():
        n = 0
        for (k, x, c, why) in WCL.classify_part(name, info, report):
            x['class'], x['why'] = c, why
            n += c in WCL.FLAGGED
        info['flagged'] = n
        total += n
    res['flagged'] = total
    lines = WCL.write_flags_md(flags_md, res['parts'], report)
    for l in lines:
        print('   FLAG ' + l)
    print('R151: %d spot(s) flagged for Dan (%s)' % (total, flags_md))
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='.')
    ap.add_argument('--out', default='')
    ap.add_argument('--only', default='')
    ap.add_argument('--classify', action='store_true')
    a = ap.parse_args()
    out = a.out or a.src
    rule = ('R127: walls > %.2f mm (W, sections every %.1f mm), features attached by >= %.1f mm (A, voxels %.2f mm); R151: fail on '
            'structural spots only, flag non-structural / questionable ones' % (WALL, STEP, ATTACH, PITCH))
    res = {'rule': rule, 'parts': {}}
    outp = os.path.join(out, FUSEBOX, 'wall_check.json')
    rp = os.path.join(out, FUSEBOX, 'fusebox_report.json')
    report = json.load(open(rp)) if os.path.isfile(rp) else {}
    if (a.only or a.classify) and os.path.isfile(outp):
        res = json.load(open(outp))
        res['rule'] = rule
    if a.classify:
        for name in res['parts']:
            p = os.path.join(a.src, FUSEBOX, name + '.stl')
            if os.path.isfile(p):
                res['parts'][name].update(extents(trimesh.load(p, force='mesh'), name, report))
            else:
                print('%s: no STL - bounds / outline not recorded' % name)
        classify_all(res, report, os.path.join(out, FUSEBOX, 'WALL-FLAGS.md'))
        json.dump(res, open(outp, 'w'), indent=1)
        print('wrote', outp)
        return 0
    for name in PARTS:
        if a.only and name not in a.only.split(','):
            continue
        p = os.path.join(a.src, FUSEBOX, name + '.stl')
        if not os.path.isfile(p):
            print('%s: no STL' % name)
            continue
        t0 = time.time()
        m = trimesh.load(p, force='mesh')
        allow = allowed(name, out)        # the build report of the checkout being written (--out): the STLs in --src may sit in a
        ex = exempt(name, out)            # main checkout whose own report lags behind (exemption boxes missing)
        seen = {}
        w = walls(m, [(k_, b_) for (k_, b_, o_) in ex if o_ != 'A'], seen)
        stats = {}
        at = None if any(k in name for k in SHELLS) else attachments(m, stats)
        if at:
            keep = []
            for x in at:
                k_ = next((key for (key, b, o_) in ex if inside(x[1:7], b, 2 * PITCH)), None)     # voxel boxes: 2 voxels of slack
                if k_ is None:
                    keep.append(x)
                else:
                    seen['A ' + k_] = seen.get('A ' + k_, 0) + 1
            at = keep
        w = [g for g in w if not any(inside(g, b) for (_, b) in allow)]
        res['parts'][name] = dict(allowed=[r for (r, _) in allow], attach_checked=at is not None, volume_cm3=round(m.volume / 1000, 1),
                                  **extents(m, name, report),
                                  exempt=seen, attach_skin=stats.get('skin', 0) if at is not None else 0,
                                  walls=[dict(at=[round(v, 1) for v in g[:6]], sections=g[6]) for g in w],
                                  attach=[dict(kind=x[0], at=[round(v, 1) for v in x[1:7]], vol_mm3=x[7]) for x in (at or [])])
        print('%s  (%.1f cm3, %.0f s): %d thin-wall spot(s), %s attachment spot(s)%s; exempt %s' % (name, m.volume / 1000, time.time() - t0, len(w),
              'n/a (shell / all thin)' if at is None else len(at), ('; allowed: ' + ', '.join(r for (r, _) in allow)) if allow else '', seen))
        for g in w[:40]:
            print('   W  x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  (%d sections)' % tuple(g))
        for x in (at or [])[:40]:
            print('   A  %s: x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  %.1f mm3' % x)
    classify_all(res, report, os.path.join(out, FUSEBOX, 'WALL-FLAGS.md'))
    json.dump(res, open(outp, 'w'), indent=1)
    print('wrote', outp)


if __name__ == '__main__':
    sys.exit(main())
