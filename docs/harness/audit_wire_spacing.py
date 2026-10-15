"""Wire spacing in both views. Schematic (Daniel, 2026-10-14, DECISIONS R86): parallel wires never
overlap and run at least 3 line thicknesses apart. Layout (Daniel, 2026-10-15, DECISIONS R107):
"no overlaps or hidden wires. parallel runs need space between them unless they terminate at the
same connector or device".

    python docs/harness/audit_wire_spacing.py [--all] [loom ...]

Paths come from `wire_paths.py`, which repeats the harness.design app's own routing (stubs, the
45-degree auto dog-leg, straight lines through `layoutPoints`). Wires are drawn 3 units wide, so
two wire centre lines that run parallel must be at least 3 * 3 + 3 = 12 units apart (a clear gap
of three line widths).

  W1  two lines (wires or cable-core sections) that run parallel (within 10 degrees) come closer
      than 12 units for more than 2 units of length. Two lines that share an end (same element and
      handle: a splice, a multi-wire terminal, one cavity) are not compared within 24 units of that
      end, where they must meet. The two halves of one cable core (core/source, core/target) are
      one conductor and are not compared with each other.

  W2  LAYOUT view: bundles (centre lines through their layoutPoints, layout_geometry.py) are the
      runs. Two bundles that share no end node and run parallel (within 10 degrees) come closer
      than LAYOUT_MIN (one 30-unit grid square) for more than 2 units of length. Two bundles that
      end at the same connector or terminal (a device) may run together (Dan's exception) and are
      not compared. Two bundles that only share a branch point split there: they are compared only
      for lying on top of each other (same line, sharing a stretch).

Re-route the schematic with `python docs/harness/route_wires.py <file>` (writes `layoutPoints`);
re-place the layout with `python docs/harness/layout_tree.py <loom> --write`; then check.
Exit 1 on any finding. Prints the first 15 findings per loom unless --all.
"""
import math
import sys

import layout_geometry as lg
import model
import wire_paths

MIN_CENTRE = 3 * wire_paths.LINE_WIDTH + wire_paths.LINE_WIDTH   # 12
PARALLEL_DEG = 10.0
SHARED_END_RADIUS = 24
MIN_RUN = 2.0
STEP = 1.0
LAYOUT_MIN = 30
DEVICE_KINDS = ("connectors", "terminals")


def _segs(d):
    ns = wire_paths.nodes(d)
    out = []
    for lid, s, t, pts in wire_paths.lines(d, ns):
        if not pts:
            continue
        ends = {s: pts[0], t: pts[-1]}
        for p, q in zip(pts, pts[1:]):
            if p != q:
                out.append((lid, ends, p, q))
    return out


def _angle(p, q):
    a = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) % 180
    return a


def _dist_pt_seg(x, y, p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((x - p[0]) * dx + (y - p[1]) * dy) / L2))
    return math.hypot(x - p[0] - t * dx, y - p[1] - t * dy)


def _close_run(a, b, skip, limit=MIN_CENTRE):
    """Length of segment a lying within MIN_CENTRE of segment b, and one such point."""
    (p, q), (r, s) = a, b
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(1, int(L / STEP))
    run, at = 0.0, None
    for i in range(n + 1):
        x = p[0] + (q[0] - p[0]) * i / n
        y = p[1] + (q[1] - p[1]) * i / n
        if any(math.hypot(x - c[0], y - c[1]) < SHARED_END_RADIUS for c in skip):
            continue
        if _dist_pt_seg(x, y, r, s) < limit - 1e-9:
            run += L / n
            at = at or (x, y)
    return run, at


def check(loom, d):
    segs = _segs(d)
    boxes = []
    for lid, ends, p, q in segs:
        boxes.append((min(p[0], q[0]) - MIN_CENTRE, min(p[1], q[1]) - MIN_CENTRE,
                      max(p[0], q[0]) + MIN_CENTRE, max(p[1], q[1]) + MIN_CENTRE, _angle(p, q)))
    hits = {}
    for i in range(len(segs)):
        la, ea, pa, qa = segs[i]
        bi = boxes[i]
        for j in range(i + 1, len(segs)):
            lb, eb, pb, qb = segs[j]
            if la.split("/")[0] == lb.split("/")[0]:      # same wire, or both halves of one core
                continue
            bj = boxes[j]
            if bi[0] > bj[2] or bj[0] > bi[2] or bi[1] > bj[3] or bj[1] > bi[3]:
                continue
            da = abs(bi[4] - bj[4])
            if min(da, 180 - da) > PARALLEL_DEG:
                continue
            skip = [ea[k] for k in ea if k in eb]
            run, at = _close_run((pa, qa), (pb, qb), skip)
            if run > MIN_RUN:
                key = tuple(sorted((la, lb)))
                if key not in hits or hits[key][0] < run:
                    hits[key] = (run, at)
    return ["W1 %s: %s and %s run parallel closer than %d for %.0f near (%.0f, %.0f)"
            % (loom, k[0], k[1], MIN_CENTRE, r, at[0], at[1]) for k, (r, at) in sorted(hits.items())]


def check_layout(loom, d):
    g = lg.geometry(d)
    segs = [(bid, p, q) for bid, pts in g["segments"].items() for p, q in zip(pts, pts[1:]) if p != q]
    hits = {}
    for i, (a, p, q) in enumerate(segs):
        for b, r, s in segs[i + 1:]:
            if a == b:
                continue
            shared = set(g["ends"][a]) & set(g["ends"][b])
            if any(g["kind"].get(n) in DEVICE_KINDS for n in shared):
                continue                          # end at the same connector / device: may run together
            if shared:
                if lg.segs_overlap(p, q, r, s):
                    hits[tuple(sorted((a, b)))] = ("lie on top of each other", p)
                continue
            da = abs(_angle(p, q) - _angle(r, s))
            if min(da, 180 - da) > PARALLEL_DEG:
                continue
            if min(p[0], q[0]) - LAYOUT_MIN > max(r[0], s[0]) or min(r[0], s[0]) - LAYOUT_MIN > max(p[0], q[0]) or                min(p[1], q[1]) - LAYOUT_MIN > max(r[1], s[1]) or min(r[1], s[1]) - LAYOUT_MIN > max(p[1], q[1]):
                continue
            run, at = _close_run((p, q), (r, s), [], LAYOUT_MIN)
            run2, at2 = _close_run((r, s), (p, q), [], LAYOUT_MIN)
            if max(run, run2) > MIN_RUN:
                hits[tuple(sorted((a, b)))] = ("run parallel closer than %d for %.0f" % (LAYOUT_MIN, max(run, run2)),
                                               at or at2)
    return ["W2 %s: layout bundles %s and %s %s near (%.0f, %.0f)" % (loom, k[0], k[1], m, at[0], at[1])
            for k, (m, at) in sorted(hits.items())]


def main(argv):
    show_all = "--all" in argv
    only = [a for a in argv if not a.startswith("-")]
    total = 0
    for loom, d in model.docs().items():
        if only and loom not in only:
            continue
        bad = check(loom, d) + check_layout(loom, d)
        total += len(bad)
        for line in (bad if show_all else bad[:15]):
            print(line)
        if len(bad) > 15 and not show_all:
            print("   ... %s: %d more (--all)" % (loom, len(bad) - 15))
    print("audit_wire_spacing: %d finding(s)" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
