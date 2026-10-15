"""Gate: fuse box terminal holes (Dan's J2 = B, 2026-10-14, DECISIONS R94) - every crimped terminal fits its hole in the base, and no
wall between two holes is thinner than the printed minimum.
Reads what the Fusion build cut (cad/fusebox/rev7/fusebox_report.json "terminal_holes") and works out on its own, from the wire plan
(cad/fusebox/rev7/wiring_plan.json: the harness wire and terminal part at every cavity) and the TE terminal data in spec.py (TERM):
  H1  every cavity with a terminal has a hole (an 87a with no harness wire keeps its plain blade slot)
  H2  the hole takes the crimp barrel: barrel = max(wire insulation OD, the smallest insulation the terminal is made for) + the metal
      both sides, + 0.4 per side (an uninsulated terminal: the wire insulation still goes in)
  H3  the hole is at least HOLE['lead_in'] deep at its mouth
  W1  the wall between two separate holes is at least HOLE['min_wall'] (R73); thinner walls must be joined into one slot (Dan)
Information only: a wire thinner than its terminal's insulation range (the insulation barrel cannot grip it - OPEN-ITEMS row 121).
    python cad/fusebox/src/check_terminal_holes.py
    python cad/fusebox/src/check_terminal_holes.py --list   # every such end, with the RNF-100 build-up (spec.build_up) and the hole it
                                                            # would need (row 121 option A)
Claude Code, 2026-10-14.
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
    """(box, x, y) -> (part, wire OD, wires) from the plan's wires (not from its cavity summary)."""
    req = {}
    for w in plan['wires']:
        for e in w['ends']:
            a = e.get('at')
            if not a or e.get('box') not in ('LOGIC', 'POWER') or a.get('kind') == 'splice':
                continue
            k = (e['box'], round(a['x'], 2), round(a['y'], 2))
            part, od, ws = req.get(k, (e.get('part'), 0.0, []))
            req[k] = (part or e.get('part'), max(od, w['od']), ws + [w['wire']])
    return req


def main():
    rep = json.load(open(REPORT, encoding='utf-8'))
    plan = json.load(open(PLAN, encoding='utf-8'))
    holes = rep.get('terminal_holes') or {}
    bad, info, grip = [], [], []
    if not holes:
        print('check_terminal_holes: MISSING terminal_holes in %s - re-run the Fusion build (build_fusion.build(rev=7))' % os.path.relpath(REPORT, REPO))
        return 1
    built = {(b, round(h['x'], 2), round(h['y'], 2)): dict(h, box=b) for b, L in holes.items() for h in L}
    req = required(plan)
    for c in plan['cavities']:                       # spares and CAD jumpers too: the plan lists every cavity the bases cut
        k = (c['box'], round(c['x'], 2), round(c['y'], 2))
        if k not in req and c['hole_d']:
            req[k] = (c['part'], c['wire_od'], [])
    n_ok = 0
    for k, (part, od, ws) in sorted(req.items()):
        kind = next((c['kind'] for c in plan['cavities'] if (c['box'], round(c['x'], 2), round(c['y'], 2)) == k), '')
        if kind.endswith('87a') and not ws:
            info.append('%s %s: 87a with no harness wire - blade slot only, no barrel hole' % (k[0], next(c['cav'] for c in plan['cavities']
                        if (c['box'], round(c['x'], 2), round(c['y'], 2)) == k)))
            continue
        if part not in S.TERM:
            bad.append('H2 %s at (%.2f, %.2f): terminal %s has no TE data in spec.TERM' % (k[0], k[1], k[2], part))
            continue
        need = S.hole_d(part, od)
        h = built.get(k)
        if not h:
            bad.append('H1 %s at (%.2f, %.2f) (%s, %s): no hole' % (k[0], k[1], k[2], part, ', '.join(ws) or 'spare'))
            continue
        if h['d'] + TOL < need:
            bad.append('H2 %s %s: hole %.2f < crimp barrel %.2f + 2 x %.1f = %.2f (%s on a %.2f mm wire)' % (
                k[0], h['cav'], h['d'], S.barrel_od(part, od), S.HOLE['clr'], need, part, od))
        if h['z1'] - h['z0'] + TOL < S.HOLE['lead_in']:
            bad.append('H3 %s %s: hole %.2f deep < %.1f' % (k[0], h['cav'], h['z1'] - h['z0'], S.HOLE['lead_in']))
        lo = S.TERM[part]['ins'][0]
        if ws and od < lo:
            info.append('%s %s: %s on a %.2f mm wire, below the %.2f-%.2f mm insulation range of %s - its insulation barrel cannot grip it' % (
                k[0], h['cav'], ', '.join(ws), od, lo, S.TERM[part]['ins'][1], part))
            grip.append((k[0], h['cav'], ', '.join(ws), od, part, h['d']))
        n_ok += 1
    walls = []
    for b, L in holes.items():
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                a, c = L[i], L[j]
                if a['group'] == c['group']:
                    continue
                w = math.hypot(a['x'] - c['x'], a['y'] - c['y']) - (a['d'] + c['d']) / 2
                walls.append(w)
                if w + TOL < S.HOLE['min_wall']:
                    bad.append('W1 %s: %s to %s wall %.2f < %.1f (join them into one slot)' % (b, a['cav'], c['cav'], w, S.HOLE['min_wall']))
    slots = rep.get('terminal_slots', {})
    print('fuse box terminal holes (%s): %d holes checked, %d joined slots, thinnest wall between separate holes %.2f mm (min %.1f)' % (
        os.path.relpath(REPORT, REPO), n_ok, sum(len(v) for v in slots.values()), min(walls) if walls else float('nan'), S.HOLE['min_wall']))
    n_grip = sum(1 for x in info if 'cannot grip' in x)
    for x in info:
        if 'cannot grip' not in x:
            print('  info: ' + x)
    if n_grip:
        print('  info: %d wire end(s) thinner than their terminal\'s insulation range (OPEN-ITEMS row 121) - first: %s' % (
            n_grip, next(x for x in info if 'cannot grip' in x)))
    if '--list' in sys.argv[1:]:
        awg = {v: g for g, v in S.OD.items()}
        print('  box    cavity      wire                    AWG  OD    terminal   ins. range   build-up (est.)            OD    hole  needs')
        for (b, cav, ws, od, part, d) in sorted(grip):
            seq, d2 = S.build_up(part, od)
            need = S.hole_d(part, d2)
            print('  %-6s %-11s %-23s %-4s %.2f  %-10s %.2f-%.2f  %-26s %.2f  %.2f  %s' % (
                b, cav, ws, awg.get(od, '?'), od, part, S.TERM[part]['ins'][0], S.TERM[part]['ins'][1],
                ' + '.join(seq) if seq else 'none fits', d2, d, ('%.2f (+%.2f)' % (need, need - d)) if need > d + TOL else 'fits'))
    for x in bad:
        print('  FAIL: ' + x)
    if bad:
        print('check_terminal_holes: %d failure(s)' % len(bad))
        return 1
    print('check_terminal_holes: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
