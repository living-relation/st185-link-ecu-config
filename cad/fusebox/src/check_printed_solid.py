"""Gate: every printed fuse box part is ONE connected solid - no floating rib, guide wall, saddle or boss (Dan 2026-10-15: "the little
ribs and the wire radius runners are just floating", DECISIONS R101).
Two checks, both must pass:
  S1  Fusion: every *_printed component of the selected boxes (POWER rev 7, LOGIC rev 7, battery relay block) has exactly one body,
      one lump and one shell (cad/fusebox/rev7/fusebox_report.json "printed_parts" - written by build_fusion.build(rev=7); a union of
      two pieces that do not touch stays ONE body with two lumps, so the body count alone cannot see it).
  S3  Not floating: every hanging feature the build lists (guide walls under the deck, POWER bend saddles) has at least
      spec.FLOAT_BACKING of its top face on solid printed material ("feature_support" after). A piece that touches the base only at
      its ends passes S1 / S2 but still bridges a gap; that is what Dan saw (his marks were 5-15 % backed). Features between that and
      fully backed are listed, not changed (Dan: "i like them as they are. just fix the floating pieces i mentioned").
  S4  Walls > 1.95 mm and S5 features attached by >= 3 mm (R127, Dan 2026-10-15): read from cad/fusebox/rev7/wall_check.json, written
      by cad/check_printed_walls.py (WSL, needs the STLs; CI has none). Fails when the file is missing or stale (a part's volume differs
      from the build report), when anything is found in the spots Dan marked and R127 fixed (MARKED), or when a part has more spots than
      its WALL_BASELINE. R128 (Dan 2026-10-16: "fix the ones you found as long as they don't alter the function and installability of
      the parts"): the baseline is 0 everywhere - every spot that has to stay thin is a named exemption (spec.WALL_EXEMPT, boxes recorded
      by the build), listed with its count, never a number to hide behind.
      R151 (Dan 2026-10-17: "Minimum thickness for walls is for critical or structural features, and doesn't apply to everything. If
      something is questionable or unclear, it should be flagged for change or approval."): each spot is classed by wall_classes.py.
      S4 / S5 FAIL on structural spots (the marked spots, attachments, legs / block under the deck, mount ears, outer skins, walls at
      the terminals, shell side walls) over the baseline, and on any marked-spot hit as before. Non-structural and questionable spots
      are FLAGGED - printed as 'flag' lines and listed in cad/fusebox/rev7/WALL-FLAGS.md for Dan to change or approve - and never
      fail or vanish. wall_check.json must carry the classes (its flagged counts match this gate's own classing) and WALL-FLAGS.md
      must match, or the run fails as stale.
  S2  Mesh: when the exported STL files are on this PC (heavy CAD is gitignored; CI has none), each STL's triangles form one connected
      piece (triangles joined by shared vertices), and no edge is shared by more than two triangles (a zero-thickness joint: two pieces
      meeting only along a line, SteveCAD sweep C3). Skipped, with a note, when a file is missing.
  S6  Gaps (SteveCAD sweep C1, Dan 2026-10-16: the 0.375 mm POWER base slots "FILL SOLID"): MJF needs >= GAP_MIN (0.5 mm) between two
      faces of one part or the powder fuses / stays trapped. From the same STL: every pair of opposite, axis-aligned faces that face each
      other across empty space closer than GAP_MIN fails, closer than GAP_FLAG (0.6) is listed. Skipped, with a note, when the STL is
      missing. Spots inside a 'label' exemption box (the strokes of the etched cover text, R137) are counted, not failed.
    python cad/fusebox/src/check_printed_solid.py [--stl-dir DIR ...]
Claude Code, 2026-10-15; S6 2026-10-17.
"""
import bisect, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S
import wall_classes as WCL
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REPORT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'fusebox_report.json')
# selected parts (cad/README.md "Selected for build") -> folder of their STL: rev 7 POWER, LOGIC and battery relay block
PARTS = {
    'Power_Base_PA12_printed': 'rev7', 'Power_Pan_PA12_printed': 'rev7', 'Power_Cover_PA12_printed': 'rev7',
    'Logic_Base_PA12_printed': 'rev7', 'Logic_Pan_PA12_printed': 'rev7', 'Logic_Cover_PA12_printed': 'rev7',
    'BattRelay_Base_PA12_printed': 'rev7', 'BattRelay_Cover_PA12_printed': 'rev7',
    'Power_NutHolder_PA12_printed': 'rev7',     # N37 (2026-10-19): the C-strap top-nut holder (one printed file; 14 per box)
}
MULTI = {}   # parts printed as several separate pieces in one file (none)
MAIN = r'C:\projects\active\st185-link-ecu-config'   # heavy files live in the main checkout (AGENTS.md "Project files stay in this repo")
WALLS = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wall_check.json')
FLAGS_MD = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'WALL-FLAGS.md')
# R127 / R128 baseline: (thin-wall spots, attachment spots) per part outside the named exemptions - 0 after the R128 sweep (2026-10-16);
# it may only go down, so it stays 0. R151: it counts STRUCTURAL spots; non-structural / questionable ones are flagged, not counted.
WALL_BASELINE = {n: (0, 0) for n in (
    'Power_Base_PA12_printed', 'Power_Pan_PA12_printed', 'Power_Cover_PA12_printed', 'Power_Retainer_R1_PA12_printed',
    'Logic_Base_PA12_printed', 'Logic_Pan_PA12_printed', 'Logic_Cover_PA12_printed', 'BattRelay_Base_PA12_printed', 'BattRelay_Cover_PA12_printed',
    'Power_NutHolder_PA12_printed')}
# the spots Dan marked on 2026-10-15 (closeup_c2), world mm boxes that must stay clear: the R1 cavity group under the deck (M1, M5),
# the R1 and R2 bend saddles (M4, M6), and the whole R1 clip (M2) - kept in wall_classes.FEATURES (R151), structural
MARKED = WCL.MARKED


def stl_triangles(path):
    """Vertex triples of an STL (binary or ASCII), rounded to 1 um so shared corners match."""
    data = open(path, 'rb').read()
    tris = []
    if len(data) >= 84 and 84 + 50 * struct.unpack('<I', data[80:84])[0] == len(data):
        n = struct.unpack('<I', data[80:84])[0]
        for i in range(n):
            v = struct.unpack('<9f', data[84 + 50 * i + 12:84 + 50 * i + 48])
            tris.append(tuple((round(v[k], 3), round(v[k + 1], 3), round(v[k + 2], 3)) for k in (0, 3, 6)))
    else:
        cur = []
        for line in data.decode('ascii', 'replace').splitlines():
            w = line.split()
            if w and w[0] == 'vertex':
                cur.append(tuple(round(float(x), 3) for x in w[1:4]))
                if len(cur) == 3:
                    tris.append(tuple(cur))
                    cur = []
    return tris


def pieces(tris):
    """Connected pieces of a triangle mesh: [(triangles, bounding box)] largest first."""
    vid, par = {}, []

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    tv = []
    for t in tris:
        ids = []
        for p in t:
            if p not in vid:
                vid[p] = len(par)
                par.append(len(par))
            ids.append(vid[p])
        tv.append(ids)
        a = f(ids[0])
        for j in ids[1:]:
            b = f(j)
            if a != b:
                par[b] = a
    grp = {}
    for t, ids in zip(tris, tv):
        g = grp.setdefault(f(ids[0]), [0, [1e9] * 3, [-1e9] * 3])
        g[0] += 1
        for p in t:
            for k in range(3):
                g[1][k] = min(g[1][k], p[k])
                g[2][k] = max(g[2][k], p[k])
    return sorted(grp.values(), key=lambda g: -g[0])


def nonmanifold(tris):
    """S2 (SteveCAD sweep C3): mesh edges shared by more than two triangles - two pieces of a solid meeting only along a line (a
    zero-thickness joint, e.g. two cavity corners touching edge to edge). [(p, q, faces)]."""
    e = {}
    for (a, b, c) in tris:
        for (u, v) in ((a, b), (b, c), (c, a)):
            k = (u, v) if u < v else (v, u)
            e[k] = e.get(k, 0) + 1
    return [(k[0], k[1], n) for k, n in e.items() if n > 2]


GAP_MIN, GAP_FLAG = 0.5, 0.6    # S6: HP MJF least gap between two faces of one part (fail below 0.5, list below 0.6)
GAP_EXEMPT = ('label',)          # exemption keys whose boxes hold open etched strokes, not powder traps


def _area(poly):
    return abs(sum(poly[i - 1][0] * p[1] - p[0] * poly[i - 1][1] for i, p in enumerate(poly))) / 2.0


def _tri_overlap(a, b):
    """Overlap area of two 2D triangles: Sutherland-Hodgman clip of a by the inside half-plane of each edge of b."""
    cr = (b[1][0] - b[0][0]) * (b[2][1] - b[0][1]) - (b[1][1] - b[0][1]) * (b[2][0] - b[0][0])
    if abs(cr) < 1e-12:
        return 0.0
    sgn = 1.0 if cr > 0 else -1.0
    poly = list(a)
    for i in range(3):
        p, q = b[i], b[(i + 1) % 3]

        def side(r):            # > 0 inside b (left of p->q for a counter-clockwise b)
            return sgn * ((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
        out = []
        for j, r in enumerate(poly):
            s_ = poly[j - 1]
            fr, fs = side(r), side(s_)
            if (fr >= 0) != (fs >= 0):
                t = fs / (fs - fr)
                out.append((s_[0] + t * (r[0] - s_[0]), s_[1] + t * (r[1] - s_[1])))
            if fr >= 0:
                out.append(r)
        poly = out
        if len(poly) < 3:
            return 0.0
    return _area(poly)


def gaps(tris, lo=GAP_FLAG, min_area=0.05):
    """S6: narrow gaps between opposite axis-aligned faces of one mesh. A face's outward normal comes from its vertex order (STL
    right-hand rule). Two faces facing each other (normals pointing at one another) closer than lo, whose projections overlap by
    more than min_area mm2, bound a gap of empty space. Returns [(gap, axis, (x0, x1, y0, y1, z0, z1))] merged per gap and axis."""
    faces = {k: {+1: [], -1: []} for k in range(3)}
    for t in tris:
        ux, uy, uz = (t[1][i] - t[0][i] for i in range(3))
        vx, vy, vz = (t[2][i] - t[0][i] for i in range(3))
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        ln = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5
        if ln < 1e-9:
            continue
        for k in range(3):
            if abs(n[k]) / ln > 0.999:
                o = [i for i in range(3) if i != k]
                faces[k][1 if n[k] > 0 else -1].append((t[0][k], [(p[o[0]], p[o[1]]) for p in t], t))
                break
    found = []
    for k in range(3):
        neg = sorted(faces[k][-1], key=lambda f: f[0])
        cs = [f[0] for f in neg]
        for (c, tri2, t) in faces[k][+1]:            # +k face at c: empty space above it; a -k face just above closes the gap
            i = bisect.bisect_right(cs, c + 1e-4)
            while i < len(neg) and cs[i] < c + lo:
                c2, tri2b, t2 = neg[i]
                if min(max(p[0] for p in tri2), max(p[0] for p in tri2b)) > max(min(p[0] for p in tri2), min(p[0] for p in tri2b)) and \
                   min(max(p[1] for p in tri2), max(p[1] for p in tri2b)) > max(min(p[1] for p in tri2), min(p[1] for p in tri2b)):
                    if _tri_overlap(tri2, tri2b) > min_area:
                        pts = list(t) + list(t2)
                        bb = []
                        for d in range(3):
                            if d == k:
                                bb += [c, c2]
                            else:
                                o = [p[d] for p in pts]
                                bb += [min(o), max(o)]
                        found.append((round(c2 - c, 3), k, tuple(round(v, 2) for v in bb)))
                i += 1
    merged = {}
    for (g, k, bb) in found:                          # one entry per (gap, axis, face coordinate): union of the boxes
        key = (g, k, bb[2 * k])
        m = merged.get(key)
        merged[key] = bb if m is None else tuple(min(m[j], bb[j]) if j % 2 == 0 else max(m[j], bb[j]) for j in range(6))
    out = []
    for (g, k, _), bb in sorted(merged.items()):      # split each union into separate spots (boxes that do not touch)
        out.append((g, k, bb))
    return _split(out)


def _split(items):
    """Merge boxes of one (gap, axis) that touch; keep apart those that do not."""
    res = []
    for (g, k, bb) in items:
        for r in res:
            if r[0] == g and r[1] == k and all(r[2][2 * d] <= bb[2 * d + 1] + 0.01 and bb[2 * d] <= r[2][2 * d + 1] + 0.01 for d in range(3)):
                r[2] = [min(r[2][j], bb[j]) if j % 2 == 0 else max(r[2][j], bb[j]) for j in range(6)]
                break
        else:
            res.append([g, k, list(bb)])
    return [(g, k, tuple(round(v, 2) for v in bb)) for (g, k, bb) in res]


def wall_findings(wcj, pp, rep, flags_md=None):
    """S4 / S5 from a wall_check.json dict (R127 / R128 / R151). Returns (bad, notes, flags): structural spots over the baseline and
    marked-spot hits are bad; non-structural / questionable spots are flags (reported for Dan, never failed)."""
    bad, notes, flags = [], [], []
    wc = wcj['parts']
    for name, (bw, ba) in WALL_BASELINE.items():
        w = wc.get(name)
        if w is None:
            bad.append('S4 %s: not in wall_check.json - re-run cad/check_printed_walls.py' % name)
            continue
        v = (pp.get(name) or {}).get('volume_cm3')
        if v is not None and abs(v - w['volume_cm3']) > max(0.3, 0.0005 * v):    # STL tessellation of round faces (the 14 standoff collars) loses ~0.3 cm3
            bad.append('S4 %s: wall_check.json is stale (%.1f cm3, the build %.1f) - re-run cad/check_printed_walls.py' % (name, w['volume_cm3'], v))
            continue
        mk = MARKED.get(name)
        hits = [x for x in w['walls'] + w['attach'] if any(all(b[2 * d] <= x['at'][2 * d + 1] and x['at'][2 * d] <= b[2 * d + 1] for d in range(3)) for b in mk or [])]
        bad.extend('S4 %s: %s at %s - inside a spot Dan marked (R127)' % (name, x.get('kind', 'wall <= 1.95'), x['at']) for x in hits)
        cls = WCL.classify_part(name, w, rep)
        sw = [x for (k, x, c, _) in cls if k == 'W' and c == WCL.STRUCTURAL]
        sa = [x for (k, x, c, _) in cls if k == 'A' and c == WCL.STRUCTURAL]
        fl = [(k, x, c, why) for (k, x, c, why) in cls if c in WCL.FLAGGED]
        flags.extend('%s %s: %s at %s - %s' % (c, name, 'wall <= 1.95' if k == 'W' else x.get('kind', 'attachment < 3'), x['at'], why)
                     for (k, x, c, why) in fl)
        if w.get('flagged') is None:
            bad.append('S4 %s: wall_check.json has no R151 classes - re-run cad/check_printed_walls.py --classify' % name)
        elif w['flagged'] != len(fl):
            bad.append('S4 %s: wall_check.json flags %d spot(s), this gate classes %d - stale, re-run cad/check_printed_walls.py --classify' % (
                name, w['flagged'], len(fl)))
        nw, na = len(w['walls']), len(w['attach'])
        (notes if len(sw) <= bw else bad).append('S4 %s: %d structural spot(s) with a wall <= 1.95 mm (baseline %d), %d flagged, %d in all%s' % (
            name, len(sw), bw, sum(1 for f in fl if f[0] == 'W'), nw, ''.join(
                '; exempt %s x%d' % (k, v) for k, v in sorted((w.get('exempt') or {}).items()))))
        bad.extend('S4 %s: structural wall <= 1.95 at %s - %s' % (name, x['at'], why) for (k, x, c, why) in cls
                   if k == 'W' and c == WCL.STRUCTURAL and len(sw) > bw)
        unknown = [k for k in (w.get('exempt') or {}) if k.replace('A ', '', 1) not in S.WALL_EXEMPT]
        bad.extend('S4 %s: exemption "%s" has no reason in spec.WALL_EXEMPT' % (name, k) for k in unknown)
        if w.get('attach_checked', True):
            (notes if len(sa) <= ba else bad).append('S5 %s: %d structural feature(s) attached by < 3 mm (baseline %d), %d flagged, %d in all' % (
                name, len(sa), ba, sum(1 for f in fl if f[0] == 'A'), na))
        else:
            notes.append('S5 %s: all thin (no >= 3 mm body) - walls only' % name)
    if flags_md is not None:
        want = WCL.flag_lines(wc, rep)
        got = [l[2:] for l in flags_md.splitlines() if l.startswith('- ') and l != '- none']
        if got != want:
            bad.append('S4 cad/fusebox/rev7/WALL-FLAGS.md is stale (%d listed, %d flagged) - re-run cad/check_printed_walls.py --classify' % (len(got), len(want)))
    else:
        bad.append('S4 no cad/fusebox/rev7/WALL-FLAGS.md - re-run cad/check_printed_walls.py --classify')
    notes.append('S4 / S5 R151: %d spot(s) flagged for Dan (cad/fusebox/rev7/WALL-FLAGS.md) - change or approve' % len(flags))
    return bad, notes, flags


def main(argv):
    dirs = [a for i, a in enumerate(argv) if i and argv[i - 1] == '--stl-dir']
    bad, notes, flags = [], [], []
    rep = json.load(open(REPORT, encoding='utf-8'))
    pp = rep.get('printed_parts') or {}
    for name in PARTS:
        if name.startswith('BattRelay_') and name not in pp:
            notes.append('S1 %s: not in the rev 7 report (battery block built by rev 6) - mesh check only' % name)
            continue
        p = pp.get(name)
        if p is None:
            bad.append('S1 %s: missing from printed_parts - re-run build_fusion.build(rev=7)' % name)
            continue
        if 'lumps' not in p:
            bad.append('S1 %s: no lump / shell count in the report - re-run build_fusion.build(rev=7)' % name)
            continue
        n_ = MULTI.get(name, 1)
        ok = p['bodies'] == n_ and p['lumps'] == n_ and p['shells'] == n_
        (notes if ok else bad).append('S1 %s: %d body, %d lump, %d shell%s' % (name, p['bodies'], p['lumps'], p['shells'],
                                                                               '' if ok else ' - FLOATING PIECE'))
    fs = rep.get('feature_support')
    if not fs:
        bad.append('S3 no feature_support in the report - re-run build_fusion.build(rev=7)')
    for bx, L in (fs or {}).items():
        weak = [f for f in L if f.get('after', 0.0) < S.FLOAT_BACKING]
        part = [f for f in L if S.FLOAT_BACKING <= f.get('after', 0.0) < 0.999]
        n_web = sum(1 for f in L if f['web'])
        if weak:
            bad.extend('S3 %s %s at %s: FLOATING - top face %.0f %% backed' % (bx, f['kind'], f['at'], 100 * f.get('after', 0.0)) for f in weak)
        else:
            notes.append('S3 %s: %d hanging features, none floating (%d joined: %s)' % (
                bx, len(L), n_web, ', '.join('%s at %s' % (f['kind'], f['at']) for f in L if f['web']) or '-'))
        notes.extend('S3 %s %s at %s: %.0f %% backed - attached, left as it is' % (bx, f['kind'], f['at'], 100 * f['after']) for f in part)
    if not os.path.isfile(WALLS):
        bad.append('S4 no cad/fusebox/rev7/wall_check.json - run cad/check_printed_walls.py (WSL) after the build')
    else:
        md = open(FLAGS_MD, encoding='utf-8').read() if os.path.isfile(FLAGS_MD) else None
        b_, n_, flags = wall_findings(json.load(open(WALLS, encoding='utf-8')), pp, rep, md)
        bad += b_
        notes += n_
    roots = dirs or [os.path.join(REPO, 'cad', 'fusebox'), os.path.join(MAIN, 'cad', 'fusebox')]
    for name, sub in PARTS.items():
        path = next((os.path.join(r, sub, name + '.stl') for r in roots if os.path.isfile(os.path.join(r, sub, name + '.stl'))), None)
        if path is None and dirs:
            path = next((os.path.join(r, name + '.stl') for r in roots if os.path.isfile(os.path.join(r, name + '.stl'))), None)
        if path is None:
            notes.append('S2 / S6 %s: no STL on this PC - mesh and gap checks skipped' % name)
            continue
        tris = stl_triangles(path)
        ps = pieces(tris)
        ex = [e['box'] for e in rep.get('wall_exempt') or [] if e['part'] == name and e['key'] in GAP_EXEMPT]
        g_in, g_ex = [], 0
        for (g, k, bb) in gaps(tris):
            if any(all(b[2 * d] - 0.05 <= bb[2 * d] and bb[2 * d + 1] <= b[2 * d + 1] + 0.05 for d in range(3)) for b in ex):
                g_ex += 1
            else:
                g_in.append((g, k, bb))
        g_bad = [x for x in g_in if x[0] < GAP_MIN]
        bad.extend('S6 %s: %.3f mm gap (< %.1f, MJF powder fuses / traps) across %s at x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
            name, g, GAP_MIN, 'xyz'[k], *bb) for (g, k, bb) in g_bad)
        (bad if g_bad else notes).append('S6 %s: %d gap(s) < %.1f mm, %d between %.1f and %.1f%s%s' % (
            name, len(g_bad), GAP_MIN, len(g_in) - len(g_bad), GAP_MIN, GAP_FLAG,
            ''.join('; flag %.3f across %s at x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (g, 'xyz'[k], *bb) for (g, k, bb) in g_in if g >= GAP_MIN),
            '; exempt label x%d' % g_ex if g_ex else ''))
        nm_ = nonmanifold(tris)
        bad.extend('S2 %s: zero-thickness joint (edge on %d faces) at %s - %s' % (name, n_, a_, b_) for (a_, b_, n_) in nm_[:12])
        if len(ps) == MULTI.get(name, 1):
            notes.append('S2 %s: %d connected mesh piece(s) (%d triangles), %d zero-thickness edges' % (name, len(ps), sum(g[0] for g in ps), len(nm_)))
        else:
            bad.append('S2 %s: %d separate pieces - floating: %s' % (name, len(ps), '; '.join(
                '%d tris at x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (g[0], g[1][0], g[2][0], g[1][1], g[2][1], g[1][2], g[2][2]) for g in ps[1:9])
                + (' ...' if len(ps) > 9 else '')))
    for n in notes:
        print('  ok   ' + n)
    for f in flags:
        print('  flag ' + f)
    for b in bad:
        print('  FAIL ' + b)
    print('check_printed_solid: %s (%d fail, %d flagged for Dan)' % ('FAIL' if bad else 'PASS', len(bad), len(flags)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
