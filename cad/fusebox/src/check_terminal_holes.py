"""Gate: fuse box terminal holes (Dan's J2 = B, 2026-10-14, DECISIONS R94; sized from the terminal, R120, Dan 2026-10-15) - every crimped
terminal goes up through its hole in the base, and no wall between two holes is thinner than the printed minimum.
Works out on its own, from the wire plan (cad/fusebox/rev7/wiring_plan.json: the harness wire and terminal part at every cavity) and the
TE terminal data in spec.py (TERM, from the TE customer drawings), what every hole must be, and checks it against what the Fusion build cut
(cad/fusebox/rev7/fusebox_report.json "terminal_holes"):
  H1  every cavity with a terminal has a hole (an 87a with no harness wire keeps its plain blade slot)
  H2  R120: the hole passes the WIDEST part pushed through it - the crimped terminal: slot = max(head, crimped barrel) each way + HOLE['clr']
      per side, the long side along the blade (spec.slot). Never sized from the wire: wire OD only has to be smaller, and always is.
  H3  the hole is at least HOLE['lead_in'] deep at its mouth
  W1  the wall between two separate holes is at least HOLE['min_wall'] (R73); thinner walls must be joined into one slot (Dan). Checked
      on the R120 slots from the plan (needs no Fusion) and on the built holes.
  G1  R120 / M6 = A: every wire thinner than its terminal's insulation range has an RNF-100 build-up that brings it into range (spec.build_up)
A build from before R120 (round holes, report key "d") cannot pass H2: its holes are listed as RECUT for the next rev 7 rebuild
(build_fusion.build(rev=7)) and the gate stays green; once the build writes R120 slots ("sx" / "sy") H2 is hard.
    python cad/fusebox/src/check_terminal_holes.py
    python cad/fusebox/src/check_terminal_holes.py --list   # every hole: built, R120 slot, what governs it, the build-up sleeve
Claude Code, 2026-10-14; R120 2026-10-15.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REPORT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'fusebox_report.json')
PLAN = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wiring_plan.json')
TOL = 0.005


def required(plan):
    """(box, x, y) -> dict(part, od, wires, kind, cav) for every cavity the bases cut (harness wires, CAD jumpers, spares)."""
    req = {}
    for w in plan['wires']:
        for e in w['ends']:
            a = e.get('at')
            if not a or e.get('box') not in ('LOGIC', 'POWER') or a.get('kind') == 'splice':
                continue
            k = (e['box'], round(a['x'], 2), round(a['y'], 2))
            r = req.setdefault(k, dict(part=e.get('part'), od=0.0, wires=[]))
            r['part'] = r['part'] or e.get('part')
            r['od'] = max(r['od'], w['od'])
            r['wires'].append(w['wire'])
    out = {}
    for c in plan['cavities']:
        k = (c['box'], round(c['x'], 2), round(c['y'], 2))
        if k in req:
            out[k] = dict(req[k], kind=c['kind'], cav=c['cav'])
        elif c.get('slot'):
            out[k] = dict(part=c['part'], od=c['wire_od'], wires=[], kind=c['kind'], cav=c['cav'])
    return out


def wall(a, b):
    """Printed wall between two axis-aligned slots (x, y, sx, sy); negative = they overlap."""
    gx = abs(a[0] - b[0]) - (a[2] + b[2]) / 2
    gy = abs(a[1] - b[1]) - (a[3] + b[3]) / 2
    if gx < 0 and gy < 0:
        return max(gx, gy)
    if gx < 0 or gy < 0:
        return max(gx, gy)
    return math.hypot(gx, gy)


def groups(rects):
    """Union-find over slots closer than min_wall: [(box, [names])] of the joined ones, and the thinnest wall between separate slots."""
    out, thin = [], float('inf')
    by_box = {}
    for r in rects:
        by_box.setdefault(r[0], []).append(r)
    for b, L in by_box.items():
        par = list(range(len(L)))

        def root(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                w = wall(L[i][2:], L[j][2:])
                if w + TOL < S.HOLE['min_wall']:
                    par[root(i)] = root(j)
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                if root(i) != root(j):
                    thin = min(thin, wall(L[i][2:], L[j][2:]))
        g = {}
        for i, r in enumerate(L):
            g.setdefault(root(i), []).append(r[1])
        out += [(b, v) for v in g.values() if len(v) > 1]
    return out, thin


def main():
    rep = json.load(open(REPORT, encoding='utf-8'))
    plan = json.load(open(PLAN, encoding='utf-8'))
    holes = rep.get('terminal_holes') or {}
    bad, info, recut, rows = [], [], [], []
    if not holes:
        print('check_terminal_holes: MISSING terminal_holes in %s - re-run the Fusion build (build_fusion.build(rev=7))' % os.path.relpath(REPORT, REPO))
        return 1
    built = {(b, round(h['x'], 2), round(h['y'], 2)): dict(h, box=b) for b, L in holes.items() for h in L}
    r120_built = all('sx' in h for L in holes.values() for h in L)
    need_rects = []
    n_ok = 0
    for k, r in sorted(required(plan).items()):
        part, od, ws, kind = r['part'], r['od'], r['wires'], r['kind']
        if kind.endswith('87a') and not ws:
            info.append('%s %s: 87a with no harness wire - blade slot only, no terminal hole' % (k[0], r['cav']))
            continue
        if part not in S.TERM:
            bad.append('H2 %s %s: terminal %s has no TE data in spec.TERM' % (k[0], r['cav'], part))
            continue
        lo = S.TERM[part]['ins'][0]
        seq = None
        if ws and od < lo:
            seq, _ = S.build_up(part, od)
            if not seq:
                bad.append('G1 %s %s: %s on a %.2f mm wire, below the %.2f mm floor of %s, and no RNF-100 build-up fits' % (
                    k[0], r['cav'], ', '.join(ws), od, lo, part))
        sx, sy = S.slot(part, od, kind)
        need_rects.append((k[0], r['cav'], k[1], k[2], sx, sy))
        env, head = S.envelope(part, od), S.TERM[part]['head']
        gov = 'head' if env == tuple(head) else 'head W, barrel H' if env[0] == head[0] else 'barrel'
        h = built.get(k)
        if not h:
            bad.append('H1 %s %s (%s, %s): no hole' % (k[0], r['cav'], part, ', '.join(ws) or 'spare'))
            continue
        if 'sx' in h:
            if h['sx'] + TOL < sx or h['sy'] + TOL < sy:
                bad.append('H2 %s %s: hole %.2f x %.2f < terminal %s %.2f x %.2f' % (k[0], r['cav'], h['sx'], h['sy'], part, sx, sy))
            have = '%.2f x %.2f' % (h['sx'], h['sy'])
        else:
            recut.append((k[0], r['cav']))
            have = 'round %.2f' % h['d']
        if h['z1'] - h['z0'] + TOL < S.HOLE['lead_in']:
            bad.append('H3 %s %s: hole %.2f deep < %.1f' % (k[0], r['cav'], h['z1'] - h['z0'], S.HOLE['lead_in']))
        rows.append((k[0], r['cav'], part, od, S.crimp_od(part, od), ' + '.join(seq) if seq else '-', have, sx, sy, gov))
        n_ok += 1
    joined, thin = groups(need_rects)
    if thin + TOL < S.HOLE['min_wall']:
        bad.append('W1 R120 slots: a wall of %.2f < %.1f between separate slots' % (thin, S.HOLE['min_wall']))
    if r120_built:
        _, bthin = groups([(b, h['cav'], h['x'], h['y'], h['sx'], h['sy']) for b, L in holes.items() for h in L])
        if bthin + TOL < S.HOLE['min_wall']:
            bad.append('W1 built: a wall of %.2f < %.1f between separate holes (join them into one slot)' % (bthin, S.HOLE['min_wall']))
    n_sl = sum(1 for x in rows if x[5] != '-')
    print('fuse box terminal holes (%s): %d holes checked against the R120 terminal slots, %d joined slots, thinnest wall between '
          'separate slots %.2f mm (min %.1f); %d wire ends carry an RNF-100 build-up' % (
              os.path.relpath(REPORT, REPO), n_ok, len(joined), thin, S.HOLE['min_wall'], n_sl))
    for x in info:
        print('  info: ' + x)
    if recut:
        print('  RECUT: %d of %d holes in the current build are round crimp-barrel holes from before R120 - every one is recut to its terminal '
              'slot at the next rev 7 rebuild (build_fusion.build(rev=7)); --list shows each' % (len(recut), n_ok))
    if '--list' in sys.argv[1:]:
        print('  box    cavity       terminal   wire  crimp OD  build-up                   built        R120 slot x x y   governed by')
        for (b, cav, part, od, cod, sq, have, sx, sy, gov) in rows:
            print('  %-6s %-12s %-10s %.2f  %.2f      %-26s %-12s %5.2f x %5.2f    %s' % (b, cav, part, od, cod, sq, have, sx, sy, gov))
        print('  joined slots: ' + '; '.join('%s %s' % (b, ' + '.join(v)) for b, v in joined))
    for x in bad:
        print('  FAIL: ' + x)
    if bad:
        print('check_terminal_holes: %d failure(s)' % len(bad))
        return 1
    print('check_terminal_holes: OK' + (' (holes RECUT pending the rev 7 rebuild)' if recut else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
