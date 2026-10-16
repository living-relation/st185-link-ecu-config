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
      its WALL_BASELINE. The baseline is what the gate found on 2026-10-15 and Dan has not marked yet: lower it when spots get fixed.
  S2  Mesh: when the exported STL files are on this PC (heavy CAD is gitignored; CI has none), each STL's triangles form one connected
      piece (triangles joined by shared vertices). Skipped, with a note, when a file is missing.
    python cad/fusebox/src/check_printed_solid.py [--stl-dir DIR ...]
Claude Code, 2026-10-15.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REPORT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'fusebox_report.json')
# selected parts (cad/README.md "Selected for build") -> folder of their STL: rev 7 POWER + LOGIC, battery block files from rev 6 (unchanged)
PARTS = {
    'Power_Base_PA12_printed': 'rev7', 'Power_Pan_PA12_printed': 'rev7', 'Power_Cover_PA12_printed': 'rev7',
    'Logic_Base_PA12_printed': 'rev7', 'Logic_Pan_PA12_printed': 'rev7', 'Logic_Cover_PA12_printed': 'rev7',
    'BattRelay_Base_PA12_printed': '.', 'BattRelay_Cover_PA12_printed': '.',
}
MAIN = r'C:\projects\active\st185-link-ecu-config'   # heavy files live in the main checkout (AGENTS.md "Project files stay in this repo")
WALLS = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wall_check.json')
# R127 baseline: (thin-wall spots, attachment spots) per part found by check_printed_walls.py on 2026-10-15, not fixed (Dan: "don't go
# looking for more yet i can probably find them for you faster") - may only go down
WALL_BASELINE = {
    'Power_Base_PA12_printed': (56, 28), 'Power_Pan_PA12_printed': (2, 19), 'Power_Cover_PA12_printed': (48, 8),
    'Power_Retainer_R1_PA12_printed': (0, 0), 'Logic_Base_PA12_printed': (232, 27), 'Logic_Pan_PA12_printed': (2, 1),
    'Logic_Cover_PA12_printed': (46, 9), 'BattRelay_Base_PA12_printed': (4, 5), 'BattRelay_Cover_PA12_printed': (16, 8),
}
# the spots Dan marked on 2026-10-15 (closeup_c2), world mm boxes that must stay clear: the R1 cavity group under the deck (M1, M5),
# the R1 and R2 bend saddles (M4, M6), and the whole R1 clip (M2)
MARKED = {'Power_Base_PA12_printed': [(191.0, 225.0, 30.0, 56.0, 26.0, 38.5), (218.0, 236.0, 36.0, 50.0, 10.0, 32.0), (188.0, 206.0, 54.0, 68.0, 10.0, 32.0)],
          'Power_Retainer_R1_PA12_printed': [(-1e3, 1e3, -1e3, 1e3, -1e3, 1e3)]}


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


def main(argv):
    dirs = [a for i, a in enumerate(argv) if i and argv[i - 1] == '--stl-dir']
    bad, notes = [], []
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
        ok = p['bodies'] == 1 and p['lumps'] == 1 and p['shells'] == 1
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
        wc = json.load(open(WALLS, encoding='utf-8'))['parts']
        for name, (bw, ba) in WALL_BASELINE.items():
            w = wc.get(name)
            if w is None:
                bad.append('S4 %s: not in wall_check.json - re-run cad/check_printed_walls.py' % name)
                continue
            v = (pp.get(name) or {}).get('volume_cm3')
            if v is not None and abs(v - w['volume_cm3']) > 0.3:
                bad.append('S4 %s: wall_check.json is stale (%.1f cm3, the build %.1f) - re-run cad/check_printed_walls.py' % (name, w['volume_cm3'], v))
                continue
            mk = MARKED.get(name)
            hits = [x for x in w['walls'] + w['attach'] if any(all(b[2 * d] <= x['at'][2 * d + 1] and x['at'][2 * d] <= b[2 * d + 1] for d in range(3)) for b in mk or [])]
            bad.extend('S4 %s: %s at %s - inside a spot Dan marked (R127)' % (name, x.get('kind', 'wall <= 1.95'), x['at']) for x in hits)
            nw, na = len(w['walls']), len(w['attach'])
            (notes if nw <= bw else bad).append('S4 %s: %d spot(s) with a wall <= 1.95 mm (baseline %d, not marked yet)' % (name, nw, bw))
            if w.get('attach_checked', True):
                (notes if na <= ba else bad).append('S5 %s: %d feature(s) attached by < 3 mm (baseline %d, not marked yet)' % (name, na, ba))
            else:
                notes.append('S5 %s: all thin (no >= 3 mm body) - walls only' % name)
    roots = dirs or [os.path.join(REPO, 'cad', 'fusebox'), os.path.join(MAIN, 'cad', 'fusebox')]
    for name, sub in PARTS.items():
        path = next((os.path.join(r, sub, name + '.stl') for r in roots if os.path.isfile(os.path.join(r, sub, name + '.stl'))), None)
        if path is None and dirs:
            path = next((os.path.join(r, name + '.stl') for r in roots if os.path.isfile(os.path.join(r, name + '.stl'))), None)
        if path is None:
            notes.append('S2 %s: no STL on this PC - mesh check skipped' % name)
            continue
        ps = pieces(stl_triangles(path))
        if len(ps) == 1:
            notes.append('S2 %s: one connected mesh (%d triangles)' % (name, ps[0][0]))
        else:
            bad.append('S2 %s: %d separate pieces - floating: %s' % (name, len(ps), '; '.join(
                '%d tris at x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (g[0], g[1][0], g[2][0], g[1][1], g[2][1], g[1][2], g[2][2]) for g in ps[1:9])
                + (' ...' if len(ps) > 9 else '')))
    for n in notes:
        print('  ok   ' + n)
    for b in bad:
        print('  FAIL ' + b)
    print('check_printed_solid: %s (%d fail)' % ('FAIL' if bad else 'PASS', len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
