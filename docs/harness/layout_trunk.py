"""Re-place a drawing's LAYOUT view keeping its trunk shape, so nothing hides anything (DECISIONS
R107, Dan 2026-10-15). Moves layoutPosition only, and drops the layoutPoints of bundles it re-places
- no wire, bundle, length, part, colour, band or schematic change (R90).

layout_tree.py lays a whole drawing out as one left-to-right tree. That straightens a harness whose
route is not a straight line (EngineRoom-C runs along the RH side and then down across the front:
a U in the top view). This script keeps such a drawing's trunk as drawn and re-lays only the fans:
  - the trunk is every node whose subtree (seen from the root) has more than `fan_max` nodes; each
    trunk bundle keeps its current direction on the canvas (right / left / up / down, snapped to
    the nearest axis; "dir" in the hint overrides one), so the drawing keeps its route shape,
  - every smaller subtree hanging off a trunk node is a fan: it is laid out by layout_tree.py's
    tidy tree to the RIGHT of its trunk node (node labels show to the right, so a fan that grows
    right never runs a bundle over a label, and the layout reads left to right, L1),
  - trunk nodes are placed one by one walking out from the root, each as close to its parent as
    the 30-unit grid allows while its own fan, its trunk bundle and its node clear everything
    already placed (nodes, labels, bundles: the audit_layout.py Y1-Y3 / W2 rules plus a margin).
Splices, resistors and diodes (no bundle) go next to their location as in layout_tree.py.

Hints: layout_hints.json, same entry as layout_tree.py plus "mode": "trunk", optional
"fan_max" (default 14) and "dir": {node: "right" | "left" | "up" | "down" | "up-right" | "down-right"} for the bundle from a
trunk node's parent to it.

    python docs/harness/layout_trunk.py EngineRoom-C [--write | --out DIR]
"""
import json
import math
import os
import sys

import audit_layout
import layout_geometry as lg
import layout_tree as lt
import model

G = lt.G
PAD = lt.PAD
SEG_PAD = lt.SEG_PAD
# fan shapes tried at each step, in order: as layout_tree lays it, without a run on the trunk
# node's own row, then every fan up, every fan down
VARIANTS = ((True, None), (False, None), (False, "up"), (False, "down"))
STUB = 1500    # how far a trunk bundle's way is kept clear of its own node's fans
DIRS = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1),
        # 45 degrees: a trunk that leaves a connector towards the front (right) would run over
        # the connector's own label (Y5), which shows to its right
        "up-right": (1, -1), "down-right": (1, 1)}


def subtree_sizes(adj, root):
    size, order, todo = {}, [], [(root, None)]
    parent = {root: None}
    while todo:
        n, p = todo.pop()
        order.append(n)
        for m, _ in adj.get(n, []):
            if m != p:
                parent[m] = n
                todo.append((m, n))
    for n in reversed(order):
        size[n] = 1 + sum(size[m] for m, _ in adj.get(n, []) if m != parent[n])
    return size, parent


def fan_shape(d, adj, kinds, n, kids, hint, straight=True, side=None, inc=None, guards=()):
    """Tidy-tree positions of n's fans relative to n (n at 0, 0), from layout_tree.layout on a copy
    of the drawing cut down to n and those fans. inc: vector from n to its trunk parent; guards:
    vectors along n's other trunk bundles - the fans keep clear of both (labels show to the right
    of their node, so with the front on the right they would otherwise lie across them)."""
    keep, todo = {n}, list(kids)
    while todo:
        a = todo.pop()
        keep.add(a)
        todo += [m for m, _ in adj.get(a, []) if m not in keep]
    sub = {k: [x for x in d.get(k, []) if x["id"] in keep] for k in lg.KINDS}
    sub["bundles"] = [b for b in d.get("bundles", []) if b["sourceId"] in keep and b["targetId"] in keep]
    nodes = dict(hint.get("fan_nodes", {}))
    if not straight:
        nodes[n] = dict(nodes.get(n, {}), main=None)    # no fan on the trunk node's own row
    if side:
        nodes[n] = dict(nodes.get(n, {}), main=None, **{side: list(kids)})   # every fan on one side
    h = {"root": n, "toward": hint.get("toward", {}), "nodes": nodes, "inc": inc, "guards": list(guards),
         "grow": hint.get("fan_grow", "left")}
    pos = lt.layout(sub, h)
    ox, oy = pos[n]
    return {m: (x - ox, y - oy) for m, (x, y) in pos.items()}


def box_of(kinds, n, x, y):
    w = lg.LABEL_W if kinds.get(n) in ("connectors", "terminals") else lg.NODE
    return (x, y, x + w, y + lg.NODE)


def grow(b, e):
    return (b[0] - e, b[1] - e, b[2] + e, b[3] + e)


def centre(p):
    return (p[0] + lg.NODE / 2, p[1] + lg.NODE / 2)


def parallel_close(p, q, r, s):
    """W2: parallel (10 deg) and closer than one grid square for more than 2 units."""
    def ang(a, b):
        return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180
    da = abs(ang(p, q) - ang(r, s))
    if min(da, 180 - da) > 10:
        return False
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(1, int(L / 2))
    run = 0.0
    for i in range(n + 1):
        x, y = p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n
        dx, dy = s[0] - r[0], s[1] - r[1]
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((x - r[0]) * dx + (y - r[1]) * dy) / L2))
        if math.hypot(x - r[0] - t * dx, y - r[1] - t * dy) < lg.NODE - 1e-9:
            run += L / n
    return run > 2


def clashes(placed, new, kinds):
    """placed / new: (boxes {node: box}, segs [(p, q, a, z)]). True if new hits placed."""
    pb, ps = placed
    nb, ns = new
    for a, ba in nb.items():
        for b, bb in pb.items():
            if lg.boxes_overlap(grow(ba, PAD), grow(bb, PAD)):
                return True
    for segs, boxes in ((ns, pb), (ps, nb)):
        for p, q, a, z in segs:
            for n, b in boxes.items():
                if n in (a, z):
                    continue
                if lg.seg_hits_box(p, q, b, SEG_PAD):
                    return True
    for p, q, a, z in ns:
        for r, s, c, e in ps:
            shared = {a, z} & {c, e}
            if shared:
                if lg.segs_overlap(p, q, r, s):
                    return True
                continue
            if lt.cross(p, q, r, s) or parallel_close(p, q, r, s):
                return True
    return False


def self_clash(B, S):
    """True if a fan shape hides part of itself: a bundle over one of its own nodes or labels, or
    two of its bundles on one line."""
    for p, q, a, z in S:
        if any(lg.seg_hits_box(p, q, b) for n, b in B.items() if n not in (a, z)):
            return True
    for i, (p, q, a, z) in enumerate(S):
        if any(lg.segs_overlap(p, q, r, s) for r, s, _, _ in S[i + 1:]):
            return True
    return False


def layout(d, hint):
    adj = lt.tree(d)
    kinds = {x["id"]: k for k in lg.KINDS for x in d.get(k, [])}
    old = {x["id"]: (x["layoutPosition"]["x"], x["layoutPosition"]["y"])
           for k in lg.KINDS for x in d.get(k, []) if x.get("layoutPosition")}
    root = hint["root"]
    fan_max = hint.get("fan_max", 14)
    size, parent = subtree_sizes(adj, root)
    over = hint.get("dir", {})

    def direction(n):
        if n in over:
            return DIRS[over[n]]
        dx = old[n][0] - old[parent[n]][0]
        dy = old[n][1] - old[parent[n]][1]
        if abs(dx) >= abs(dy):
            return (1 if dx >= 0 else -1, 0)
        return (0, 1 if dy >= 0 else -1)

    pos = {}
    placed = ({}, [])

    shapes = {}

    def cluster(n, x, y, variant):
        """n at (x, y) plus its fans: (positions, boxes, segments). straight: the fan's main run
        may go on along n's own row."""
        kids = [m for m, _ in adj.get(n, []) if m != parent[n] and size[m] <= fan_max]
        if (n, variant) not in shapes:
            straight, side = variant
            inc = None
            if parent[n] is not None:
                ux, uy = direction(n)
                inc = (-ux * STUB, -uy * STUB)
            guards = [(direction(m)[0] * STUB, direction(m)[1] * STUB)
                      for m, _ in adj.get(n, []) if m != parent[n] and size[m] > fan_max]
            shapes[n, variant] = fan_shape(d, adj, kinds, n, kids, hint, straight, side, inc, guards)                 if kids else {n: (0, 0)}
        rel = shapes[n, variant]
        P = {m: (x + rx, y + ry) for m, (rx, ry) in rel.items()}
        B = {m: box_of(kinds, m, *p) for m, p in P.items()}
        S = []
        for b in d.get("bundles", []):
            a, z = b["sourceId"], b["targetId"]
            if a in P and z in P:
                S.append((centre(P[a]), centre(P[z]), a, z))
        return P, B, S

    def stubs(n, x, y):
        """a long stub along every trunk bundle that leaves n, so n's own fans keep out of its way"""
        return [(centre((x, y)), centre((x + direction(m)[0] * STUB, y + direction(m)[1] * STUB)), n, m)
                for m, _ in adj.get(n, []) if m != parent[n] and size[m] > fan_max]

    def fits_self(n, x, y, B, S, edge=None):
        own = ({m: b for m, b in B.items() if m != n}, S)
        return not self_clash(B, S) and \
            not clashes(own, ({}, stubs(n, x, y) + ([edge] if edge else [])), kinds)

    rx, ry = old[root]
    for variant in VARIANTS:
        P, B, S = cluster(root, rx, ry, variant)
        if fits_self(root, rx, ry, B, S):
            break
    pos.update(P)
    placed = (dict(B), list(S))
    todo = [m for m, _ in adj.get(root, []) if size[m] > fan_max]
    while todo:
        n = todo.pop(0)
        ux, uy = direction(n)
        px, py = pos[parent[n]]
        # the trunk bundles still to place keep their way clear too: their stubs from their placed
        # parents (fans now open towards the parent side, so a sibling's fan could block them)
        pending = ({}, [s for m in todo for s in stubs(parent[m], *pos[parent[m]]) if s[3] == m])
        hit = None
        for k in range(2, 400):
            x, y = px + ux * k * G, py + uy * k * G
            edge = (centre((px, py)), centre((x, y)), parent[n], n)
            for variant in VARIANTS:
                P, B, S = cluster(n, x, y, variant)
                if fits_self(n, x, y, B, S, edge) and not clashes(placed, (B, S + [edge]), kinds)                         and not clashes(pending, (B, S + [edge]), kinds):
                    hit = True
                    break
            if hit:
                break
        else:
            if os.environ.get("LT_DEBUG"):
                x, y = px + ux * 20 * G, py + uy * 20 * G
                edge = (centre((px, py)), centre((x, y)), parent[n], n)
                for variant in VARIANTS:
                    P, B, S = cluster(n, x, y, variant)
                    print("  ", n, variant, "self:", self_clash(B, S),
                          "own:", clashes(({m: b for m, b in B.items() if m != n}, S), ({}, stubs(n, x, y) + [edge]), kinds),
                          "placed:", clashes(placed, (B, S + [edge]), kinds), file=sys.stderr)
            raise SystemExit("layout_trunk: no room for %s" % n)
        pos.update(P)
        placed[0].update(B)
        placed[1].extend(S + [edge])
        todo += [m for m, _ in adj.get(n, []) if m != parent[n] and size[m] > fan_max]
    return pos


def main(argv):
    import audit_drawing_rules
    import audit_wire_spacing
    write = "--write" in argv
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    looms = [a for a in argv if not a.startswith("--") and a != out]
    with open(lt.HINTS, encoding="utf-8") as f:
        hints = json.load(f)
    files = model.harness_files()
    rc = 0
    for loom in looms:
        path = os.path.join(model.REB, files[loom])
        mtime = os.path.getmtime(path)
        with open(path, "rb") as f:
            nl = "\r\n" if b"\r\n" in f.read(4096) else "\n"
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        hint = dict(hints[loom])
        ends = {b["id"]: b["targetId"] for b in d.get("bundles", [])}
        hint["loose"] = dict({x["id"]: ends[x["locationId"]] for k in ("splices", "resistors", "diodes")
                              for x in d.get(k, []) if x.get("locationId") in ends},  # on a bundle
                             **hint.get("loose", {}))
        pos = layout(d, hint)
        lt.apply(d, pos, hint)
        for b in d.get("bundles", []):
            if b.get("layoutPoints") and (b["sourceId"] in pos or b["targetId"] in pos):
                del b["layoutPoints"]
        bad = audit_layout.check(loom, d) + audit_wire_spacing.check_layout(loom, d) + \
            [b for b in audit_drawing_rules.check(loom, d) if b.startswith(("L1", "G1"))]
        for b in bad:
            print(b)
        print("%s: %d layout finding(s)" % (loom, len(bad)))
        rc |= bool(bad)
        if write or out:
            if os.path.getmtime(path) != mtime:
                raise SystemExit("%s changed on disk while re-placing - not written" % path)
            lt.write_atomic(os.path.join(out, files[loom]) if out else path, d, nl)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
