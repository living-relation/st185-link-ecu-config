"""Wire routing points and layout spacing. Schematic (Daniel, 2026-10-16, DECISIONS R141): no wire
routing points unless he asks - harness.design auto-routes every wire. Layout (Daniel, 2026-10-15,
DECISIONS R107): "no overlaps or hidden wires. parallel runs need space between them unless they
terminate at the same connector or device".

    python docs/harness/audit_wire_spacing.py [--all] [loom ...]

  RP1 SCHEMATIC: a wire carries routing points (`layoutPoints`, the white crosses the app shows on
      hover) and is not on ROUTING_POINTS_ALLOWED. Strip them with
      `python docs/harness/strip_routing_points.py --write`. Bundle layout points are not routing
      points of a wire and are not checked here. A cable core or shield keeps its routing points
      in `sourceLayoutPoints` / `targetLayoutPoints` (the legs from the cable to each end, v1.2
      schema); those are routing points too (G2 / G3 found them 2026-10-17) and count the same,
      except in the drawings still on CORE_POINTS_PENDING.

  W1  RETIRED 2026-10-16 (R141 replaces R86): it held hand-placed right-angle wire paths 3 line
      widths apart; the app's auto-routing is preferred now. `route_wires.py`, which wrote those
      paths, is deleted (git history).

  W2  LAYOUT view: bundles (centre lines through their layoutPoints, layout_geometry.py) are the
      runs. Two bundles that share no end node and run parallel (within 10 degrees) come closer
      than LAYOUT_MIN (one 30-unit grid square) for more than 2 units of length. Two bundles that
      end at the same connector or terminal (a device) may run together (Dan's exception) and are
      not compared. Two bundles that only share a branch point split there: they are compared only
      for lying on top of each other (same line, sharing a stretch).

Re-place the layout with `python docs/harness/layout_tree.py <loom> --write`; then check.
Exit 1 on any finding. Prints the first 15 findings per loom unless --all.
"""
import math
import sys

import layout_geometry as lg
import model

# loom -> wire ids that may keep routing points. Only wires Dan asks for, after the overall layout
# is set (R141); empty until he does.
ROUTING_POINTS_ALLOWED = {}
# Drawings whose cable cores / shields still carry routing points: listed, not failed, until the
# group relabelling that drawing (DECISIONS R156 split) strips them. Only ever shrinks.
CORE_POINTS_PENDING = {"A-cabin", "B-cabin", "A-engine", "B-engine", "CSB3"}
CORE_KEYS = ("sourceLayoutPoints", "targetLayoutPoints")


def routed(d):
    """(kind, id, element, key) for every element that can carry wire routing points: a wire's
    layoutPoints, and the two legs of every cable core and shield."""
    for x in d.get("wires", []):
        yield "wire", x["id"], x, "layoutPoints"
    for cb in d.get("cables", []):
        for co in cb.get("cores", []) + ([cb["shield"]] if cb.get("shield") else []):
            for k in CORE_KEYS:
                yield "core", co.get("id") or cb["id"], co, k

PARALLEL_DEG = 10.0
MIN_RUN = 2.0
STEP = 1.0
LAYOUT_MIN = 30
DEVICE_KINDS = ("connectors", "terminals")


def _angle(p, q):
    a = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) % 180
    return a


def _dist_pt_seg(x, y, p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((x - p[0]) * dx + (y - p[1]) * dy) / L2))
    return math.hypot(x - p[0] - t * dx, y - p[1] - t * dy)


def _close_run(a, b, limit):
    """Length of segment a lying within `limit` of segment b, and one such point."""
    (p, q), (r, s) = a, b
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(1, int(L / STEP))
    run, at = 0.0, None
    for i in range(n + 1):
        x = p[0] + (q[0] - p[0]) * i / n
        y = p[1] + (q[1] - p[1]) * i / n
        if _dist_pt_seg(x, y, r, s) < limit - 1e-9:
            run += L / n
            at = at or (x, y)
    return run, at


def check_routing_points(loom, d, pending=False):
    keep = ROUTING_POINTS_ALLOWED.get(loom, set())
    out = []
    for kind, xid, x, k in routed(d):
        if x.get(k) and xid not in keep and (kind == "wire") != pending:
            out.append("RP1 %s: %s %s carries %d routing point(s) in %s (R141: none unless Dan asks)"
                       % (loom, kind, xid, len(x[k]), k))
    return out


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
            run, at = _close_run((p, q), (r, s), LAYOUT_MIN)
            run2, at2 = _close_run((r, s), (p, q), LAYOUT_MIN)
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
        bad = check_routing_points(loom, d) + check_layout(loom, d)
        if loom not in CORE_POINTS_PENDING:
            bad += check_routing_points(loom, d, pending=True)
        else:
            later = check_routing_points(loom, d, pending=True)
            if later:
                print("   pending %s: %d cable core / shield leg(s) with routing points (CORE_POINTS_PENDING)"
                      % (loom, len(later)))
        total += len(bad)
        for line in (bad if show_all else bad[:15]):
            print(line)
        if len(bad) > 15 and not show_all:
            print("   ... %s: %d more (--all)" % (loom, len(bad) - 15))
    print("audit_wire_spacing: %d finding(s)" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
