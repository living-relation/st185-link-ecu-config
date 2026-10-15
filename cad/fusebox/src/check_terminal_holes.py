"""Gate: fuse box terminal cavities (Dan's J2 = B, 2026-10-14, DECISIONS R94; hole rule R120 and self-locking terminals R121, Dan
2026-10-15) - every crimped terminal goes up through its hole in the base and snaps in, and no wall between two cavities is thinner than
the printed minimum.
Works out on its own, from the wire plan (cad/fusebox/rev7/wiring_plan.json: the harness wire and terminal part at every cavity) and the
TE terminal data in spec.py (TERM, LOCK), what every cavity must be, and checks it against what the Fusion build cut
(cad/fusebox/rev7/fusebox_report.json "terminal_holes"):
  H1  every cavity with a terminal has a hole (an 87a with no harness wire keeps its plain blade slot)
  H2  R120: the hole = the largest cross-section along the insertion axis of everything that passes through - contact box, crimped
      barrels on the THICKEST insulation the terminal accepts, the wire behind them (880398-2: its stop flange) - + HOLE['clr'] per side
      (spec.hole); every zone above it as spec.zones. Today's wire is never the size: it (and its RNF-100 build-up) only has to fit (S1).
  H3  the hole is at least HOLE['lead_in'] deep at its mouth
  L1  R121: a terminal with a locking lance keeps at least one ledge (the box-sized stretch under a window the lance springs into, the
      lance reaching past the ledge edge by >= LOCK_MIN) that no neighbouring cavity is joined onto; a terminal with no lance (dimple) is
      listed as PENDING (open question M8)
  W1  every wall between two cavities, zone by zone where they share a height, is at least HOLE['min_wall'] (R73) - or the two are
      joined into one (Dan: "join the two slots into one"); joins in the box / window zones (the relay and fuse pin spacing) are listed
  S1  the wire, with its RNF-100 build-up, fits the hole
  G1  R120 / M6 = A: every wire thinner than its terminal's insulation range has an RNF-100 build-up that brings it into range
A build from before R121 (report holes without "zones") cannot pass H2: its holes are listed as RECUT for the next rev 7 rebuild
(build_fusion.build(rev=7)) and the gate stays green, and an L1 cavity left with no ledge is listed as RESOLVE (a layout / question to settle
before that rebuild); once the build writes the zones both are hard.
    python cad/fusebox/src/check_terminal_holes.py
    python cad/fusebox/src/check_terminal_holes.py --list   # every cavity: built, R120 hole, the lock zones, the build-up sleeve
Claude Code, 2026-10-14; R120 / R121 2026-10-15.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REPORT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'fusebox_report.json')
PLAN = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wiring_plan.json')
TOL = 0.005
LOCK_MIN = 0.3     # mm the lance tip reaches past the ledge edge, at the worst clearance


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
        elif c.get('hole'):
            out[k] = dict(part=c['part'], od=c['wire_od'], wires=[], kind=c['kind'], cav=c['cav'])
    return out


def gap(a, b):
    """Printed wall between two axis-aligned rects (x0, x1, y0, y1); negative = they overlap."""
    gx = max(a[0] - b[1], b[0] - a[1])
    gy = max(a[2] - b[3], b[2] - a[3])
    return math.hypot(gx, gy) if gx > 0 and gy > 0 else max(gx, gy)


def absz(c, z):
    return (c['x'] + z[2], c['x'] + z[3], c['y'] + z[4], c['y'] + z[5])


def joins(cavs):
    """Pairs of cavities closer than min_wall in any two zones that share a height: ([(box, a, b, wall, upper?)], thinnest wall kept)."""
    out, thin = [], float('inf')
    for i in range(len(cavs)):
        for j in range(i + 1, len(cavs)):
            a, b = cavs[i], cavs[j]
            if a['box'] != b['box'] or math.hypot(a['x'] - b['x'], a['y'] - b['y']) > 40:
                continue
            worst, up = float('inf'), False
            for za in a['zs']:
                for zb in b['zs']:
                    lo_a, lo_b = -1e9 if za[0] is None else za[0], -1e9 if zb[0] is None else zb[0]
                    if min(za[1], zb[1]) <= max(lo_a, lo_b):
                        continue
                    g = gap(absz(a, za), absz(b, zb))
                    if g < worst:
                        worst, up = g, (za[0] is not None and zb[0] is not None)
            if worst + TOL < S.HOLE['min_wall']:
                out.append((a['box'], a['cav'], b['cav'], worst, up))
            else:
                thin = min(thin, worst)
    return out, thin


def ledges(c, joined_with):
    """(window sides, sides kept) of a lance terminal: a side ('-x', '+y' ...) is lost when a cavity joined onto it lies mostly that way."""
    box_, win = c['zs'][-2], c['zs'][-1]
    sides = [s for s, d in (('-x', box_[2] - win[2]), ('+x', win[3] - box_[3]), ('-y', box_[4] - win[4]), ('+y', win[5] - box_[5])) if d > TOL]
    keep = []
    for s in sides:
        k, sg = ('x', -1) if s == '-x' else ('x', 1) if s == '+x' else ('y', -1) if s == '-y' else ('y', 1)
        o = 'y' if k == 'x' else 'x'
        if not any(sg * (n[k] - c[k]) > 0 and abs(n[k] - c[k]) >= abs(n[o] - c[o]) for n in joined_with):
            keep.append(s)
    return sides, keep


def main():
    rep = json.load(open(REPORT, encoding='utf-8'))
    plan = json.load(open(PLAN, encoding='utf-8'))
    holes = rep.get('terminal_holes') or {}
    bad, info, recut, pending, rows, resolve = [], [], [], [], [], []
    if not holes:
        print('check_terminal_holes: MISSING terminal_holes in %s - re-run the Fusion build (build_fusion.build(rev=7))' % os.path.relpath(REPORT, REPO))
        return 1
    built = {(b, round(h['x'], 2), round(h['y'], 2)): dict(h, box=b) for b, L in holes.items() for h in L}
    cavs = []
    n_ok = 0
    for k, r in sorted(required(plan).items()):
        part, od, ws, kind = r['part'], r['od'], r['wires'], r['kind']
        if kind.endswith('87a') and not ws:
            info.append('%s %s: 87a with no harness wire - blade slot only, no terminal cavity' % (k[0], r['cav']))
            continue
        if part not in S.TERM or part not in S.LOCK:
            bad.append('H2 %s %s: terminal %s has no TE data in spec.TERM / LOCK' % (k[0], r['cav'], part))
            continue
        lo = S.TERM[part]['ins'][0]
        seq = None
        if ws and od < lo:
            seq, _ = S.build_up(part, od)
            if not seq:
                bad.append('G1 %s %s: %s on a %.2f mm wire, below the %.2f mm floor of %s, and no RNF-100 build-up fits' % (
                    k[0], r['cav'], ', '.join(ws), od, lo, part))
        hx, hy = S.hole(part, kind)
        cod = S.crimp_od(part, od)
        if cod + 2 * S.HOLE['clr'] > min(hx, hy) + TOL:
            bad.append('S1 %s %s: wire / build-up %.2f does not fit the %.2f x %.2f hole' % (k[0], r['cav'], cod, hx, hy))
        c = dict(box=k[0], x=k[1], y=k[2], kind=kind, part=part, cav=r['cav'])
        cavs.append(c)
        h = built.get(k)
        if not h:
            bad.append('H1 %s %s (%s, %s): no hole' % (k[0], r['cav'], part, ', '.join(ws) or 'spare'))
            continue
        c['built'] = h
        rows.append([k[0], r['cav'], part, od, cod, ' + '.join(seq) if seq else '-', None, hx, hy, ''])
        c['row'] = rows[-1]
        n_ok += 1
    allc = [dict(box=c['box'], x=c['x'], y=c['y'], kind=c['kind']) for c in plan['cavities']]
    for c in cavs:
        c['zs'] = S.zones(c['part'], c['kind'], S.lance_side(c, allc))
        h = c.get('built')
        if not h:
            continue
        if 'zones' in h:
            for zb, zr in zip(h['zones'], c['zs']):
                if any(abs(a_ - b_) > TOL and (abs(a_) < abs(b_)) for a_, b_ in zip(zb[2:], zr[2:])):
                    bad.append('H2 %s %s: zone %s built %s < %s' % (c['box'], c['cav'], zr[:2], zb[2:], [round(v, 2) for v in zr[2:]]))
            c['row'][6] = '%.2f x %.2f' % (h['zones'][0][3] - h['zones'][0][2], h['zones'][0][5] - h['zones'][0][4])
        else:
            recut.append((c['box'], c['cav']))
            c['row'][6] = ('round %.2f' % h['d']) if 'd' in h else '%.2f x %.2f' % (h['sx'], h['sy'])
        if h['z1'] - h['z0'] + TOL < S.HOLE['lead_in']:
            bad.append('H3 %s %s: hole %.2f deep < %.1f' % (c['box'], c['cav'], h['z1'] - h['z0'], S.HOLE['lead_in']))
    joined, thin = joins(cavs)
    by = {(c['box'], c['cav']): c for c in cavs}
    partners = {}
    for (b, a_, c_, w, up) in joined:
        partners.setdefault((b, a_), []).append(by[(b, c_)])
        partners.setdefault((b, c_), []).append(by[(b, a_)])
    shared = [(b, a_, c_, w) for (b, a_, c_, w, up) in joined if up]
    for c in cavs:
        L_ = S.LOCK[c['part']]
        if L_['kind'] != 'lance':
            pending.append((c['box'], c['cav'], c['part']))
            c.get('row', [0] * 10)[9] = 'NO LANCE - pending M8'
            continue
        sides, keep = ledges(c, partners.get((c['box'], c['cav']), []))
        if L_['out'] - S.HOLE['clr'] + TOL < LOCK_MIN:
            bad.append('L1 %s %s: %s lance reaches %.2f past its ledge (min %.1f)' % (c['box'], c['cav'], c['part'], L_['out'] - S.HOLE['clr'], LOCK_MIN))
        if not keep:
            resolve.append('L1 %s %s: %s has no ledge left (window %s, every side joined to a neighbour)' % (c['box'], c['cav'], c['part'], '/'.join(sides)))
        if 'row' in c:
            c['row'][9] = 'lance, ledge %s%s' % ('/'.join(keep) or 'NONE', (' (%s lost)' % '/'.join(x for x in sides if x not in keep)) if len(keep) < len(sides) else '')
    n_sl = sum(1 for x in rows if x[5] != '-')
    print('fuse box terminal cavities (%s): %d checked against R120 holes + R121 lance locks; %d pairs joined (%d of them in the box / '
          'lance zones: the relay / fuse pin spacing), thinnest wall between separate cavities %.2f mm (min %.1f); %d wire ends carry an '
          'RNF-100 build-up' % (os.path.relpath(REPORT, REPO), n_ok, len(joined), len(shared), thin, S.HOLE['min_wall'], n_sl))
    for x in info:
        print('  info: ' + x)
    if pending:
        print('  PENDING: %d cavities hold a terminal with no locking lance (%s) - cannot self-lock (R121) until question M8 is answered' % (
            len(pending), ', '.join(sorted({p for _, _, p in pending}))))
    if recut:
        print('  RECUT: %d of %d cavities in the current build are from before R120 / R121 - every one is recut to its zones at the next '
              'rev 7 rebuild (build_fusion.build(rev=7)); --list shows each' % (len(recut), n_ok))
    if '--list' in sys.argv[1:]:
        print('  box    cavity       terminal   wire  crimp OD  build-up                   built        R120 hole x x y   lock')
        for (b, cav, part, od, cod, sq, have, hx, hy, lock) in rows:
            print('  %-6s %-12s %-10s %.2f  %.2f      %-26s %-12s %5.2f x %5.2f    %s' % (b, cav, part, od, cod, sq, have, hx, hy, lock))
        print('  joined pairs: ' + '; '.join('%s %s + %s (%.2f%s)' % (b, a_, c_, w, ', lock zones' if up else '') for (b, a_, c_, w, up) in joined))
    zbuilt = any('zones' in h for L in holes.values() for h in L)
    for x in resolve:
        if zbuilt:
            bad.append(x)
        else:
            print('  RESOLVE before the rebuild: ' + x)
    for x in bad:
        print('  FAIL: ' + x)
    if bad:
        print('check_terminal_holes: %d failure(s)' % len(bad))
        return 1
    print('check_terminal_holes: OK' + (' (cavities RECUT pending the rev 7 rebuild)' if recut else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
