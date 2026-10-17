"""Re-place a drawing's LAYOUT view as an overhead view that follows its approved route
(DECISIONS R107, R140: front of the car on the RIGHT, Dan 2026-10-16). Moves layoutPosition only -
no wire, bundle, length, part, colour, band or schematic change (R90).

The bundles of one harness form a tree. It is drawn as a tidy tree read right to left (R42 / L1:
no branch doubles back):
  - the root (the front-most node) is at the right; x falls towards the back of the car,
  - up = passenger (RH) side, down = driver (LH) side, as in the route top views,
  - a branch point keeps its main run straight on its own row; side branches fan out above or
    below, each in its own band of rows, so no bundle, node or label lands on another (Y1-Y3),
  - the app shows a connector / terminal label to the RIGHT of its node, i.e. towards the parent
    (front-left drawings had their children drop straight up and down from a labelled node for
    that reason; right to left they leave away from it). So a labelled node never takes its
    parent's row (it is never the main run), its bundle comes in steeply enough to reach the node
    without crossing its own label (audit_layout.py Y5), and a fan with a labelled child sits a
    label's width left of its parent, so no child label covers the parent,
  - all children of a node share one x, set by the longest child bundle (a bundle keeps its
    `length`; only the canvas spacing follows it, roughly as its square root).
Splices, resistors and diodes (no bundle; they sit at their locationId) and loose nodes go on the
nearest free grid spot next to their location.

Hints per drawing: layout_hints.json - root (the front-most node, placed at the right), and per node the children
that go "up" / "down" (inner to outer) or "main"; "main_last": true places a hub's side branches
first, in one column, and carries the main run on past their labels (CabinPower's two hubs). A terminal broken off toward another harness
takes that harness's side from "toward" unless a node hint says otherwise.

    python docs/harness/layout_tree.py A-cabin [--write | --out DIR]
    python docs/harness/layout_tree.py --mirror RearFuel [--write | --out DIR]

--mirror only flips the drawing left to right as it is (node and bundle layout points; for the
hand-laid drawings without a hint, and those whose bundle points Dan kept), so a front-left drawing
becomes front-right; it does not re-place anything. Without --write it only prints the audit_layout.py / L1 result for the new positions (--out DIR
writes the re-placed copy there instead, for render_layout.py).
"""
import json
import math
import os
import re
import sys

import layout_geometry as lg
import model

HERE = os.path.dirname(os.path.abspath(__file__))
HINTS = os.path.join(HERE, "layout_hints.json")
G = 30
PAD = 14       # free margin around every node and label: rows 60 apart pass, 30 apart do not
SEG_PAD = 10   # and a bundle keeps this much more clear of any node or label it does not end at
MAX_REACH = 1350  # staircase: no end further out than this (audit_layout.py Y4: no long diagonal)
STEP_CLEAR = 60   # staircase: a later bundle passes this far left of a nearer labelled end's node
MAX_INV = 1.3     # staircase: a bundle into a labelled end is steep enough to reach the node
                  # under its label (label_box: 17 right of the centre, +-9, plus 2: 15 / 11)


def cross(p, q, r, s):
    """True if segments p-q and r-s properly cross."""
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 1e-9) - (v < -1e-9)
    return o(p, q, r) * o(p, q, s) < 0 and o(r, s, p) * o(r, s, q) < 0


def dx_for(length):
    if not length:
        return 3 * G
    return G * max(3, min(12, round(2 + math.sqrt(length) / 5)))


def tree(d):
    """node -> [(neighbour, bundle length)]; two bundles between the same two nodes (a group that
    ends at the same connector, allowed to run together) count once."""
    adj = {}
    for b in d.get("bundles", []):
        L = (b.get("length") or {}).get("value")
        for a, z in ((b["sourceId"], b["targetId"]), (b["targetId"], b["sourceId"])):
            have = adj.setdefault(a, [])
            if z not in [m for m, _ in have]:
                have.append((z, L))
    return adj


def labelled(kinds, n):
    return kinds.get(n) in ("connectors", "terminals")


def label_box(b):
    """the label part of a node box made by box() (node + label + PAD): right of the node."""
    return (b[0] + PAD + lg.NODE + 2, b[1] + PAD + 6, b[2] - PAD, b[3] - PAD - 6)


def mirror(d):
    """flip the layout left to right about its own middle, on the grid: every node's centre and
    every bundle layout point mirrored (the label stays to the right of its node)."""
    pts = [x["layoutPosition"] for k in lg.KINDS for x in d.get(k, []) if x.get("layoutPosition")]
    pts += [q["layoutPosition"] for b in d.get("bundles", []) for q in b.get("layoutPoints", [])
            if q.get("layoutPosition")]
    if not pts:
        return
    s = min(p["x"] for p in pts) + max(p["x"] for p in pts)
    s -= s % G
    for p in pts:
        p["x"] = s - p["x"]


def toward(d, n, rules):
    for x in d.get("terminals", []):
        if x["id"] == n:
            m = re.search(r"ST185-([A-Za-z0-9-]+)", x.get("signal") or "")
            if m:
                return rules.get(m.group(1))
    return None


def warn(msg):
    print("layout_tree: " + msg, file=sys.stderr)


def layout(d, hint):
    if hint.get("grow") == "right":
        return layout_right(d, hint)
    adj = tree(d)
    kinds = {x["id"]: k for k in lg.KINDS for x in d.get(k, [])}
    root = hint["root"]
    nodes_hint = hint.get("nodes", {})
    rules = hint.get("toward", {})
    pos = {}
    size = {}

    def count(n, parent):
        size[n] = 1 + sum(count(m, n) for m, _ in adj.get(n, []) if m != parent)
        return size[n]

    count(root, None)

    def side_of(n, parent):
        """majority side of the leaves under n (by 'toward'), else None."""
        votes = {"up": 0, "down": 0}
        todo = [(n, parent)]
        while todo:
            a, p = todo.pop()
            kids = [m for m, _ in adj.get(a, []) if m != p]
            if not kids:
                s = toward(d, a, rules)
                if s in votes:
                    votes[s] += 1
            todo += [(m, a) for m in kids]
        if votes["up"] != votes["down"]:
            return "up" if votes["up"] > votes["down"] else "down"
        return None

    def box(n, x, y):
        w = lg.LABEL_W if labelled(kinds, n) else lg.NODE
        return (x - PAD, y - PAD, x + w + PAD, y + lg.NODE + PAD)

    def shifted(shape, dy, dx=0):
        bx = [(n, (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)) for n, b in shape[0]]
        sg = [((p[0] + dx, p[1] + dy), (q[0] + dx, q[1] + dy), a, z) for p, q, a, z in shape[1]]
        return bx, sg

    def grow(b, e=SEG_PAD):
        return (b[0] - e, b[1] - e, b[2] + e, b[3] + e)

    def clash(P, S, edge, guard=()):
        """True if shape S (with the new edge joining it) collides with placed shape P; `guard`
        segments (the way in from the parent) must stay clear of S's nodes and labels."""
        pb, ps = P
        sb, ss = S
        for p, q in guard:
            if any(lg.seg_hits_box(p, q, grow(c)) for _, c in sb):
                return "c1"
            if lg.segs_overlap(p, q, edge[0], edge[1]):
                return "c1"     # a fan bundle along the way in from the parent
        for _, b in sb:
            if any(lg.boxes_overlap(b, c) for _, c in pb):
                return "c2"
        for p, q, a, z in ss + [edge]:
            for n, c in pb:
                if n not in (a, z) and lg.seg_hits_box(p, q, grow(c)):
                    return "c3 %s-%s hits %s %s" % (a, z, n, tuple(int(v) for v in c))
            if any(cross(p, q, r, s) for r, s, a2, z2 in ps if not {a, z} & {a2, z2}):
                return "c4"
        for p, q, a, z in ps:
            if any(lg.seg_hits_box(p, q, grow(c)) for n, c in sb if n not in (a, z)):
                return "c5"
        p, q, a, z = edge
        if any(lg.segs_overlap(p, q, r, s) for r, s, a2, z2 in ps if {a, z} & {a2, z2}):
            return "c6"         # two bundles out of one node on one line: one hides the other (Y3)
        for n, c in pb + sb:
            if n in (a, z) and labelled(kinds, n) and lg.seg_hits_box(p, q, label_box(c), 2):
                return "c7"     # the edge would run over its own end's label (Y5)
        if any(lg.seg_hits_box(p, q, grow(c)) for n, c in sb if n not in (a, z)):
            return "c8"
        return False

    def staircase(n, x, y, side, combs, shape, guard):
        """labelled ends of n on one side, as a staircase out from n: the first straight above /
        below n, each next one further out and further left, so the bundle to a later end passes
        to the LEFT of every nearer end instead of over its label (the label shows to the right
        of its node). Row distance r_i grows by 2 grid rows per end; the inverse slope starts at 0
        (or 0.5 / 1 when something already runs straight up / down from n) and grows by
        STEP_CLEAR / r_i, so at r_i the next bundle is STEP_CLEAR left of end i; every bundle stays
        steep enough (MAX_INV) to reach its own node under its label (Y5). Falls back to
        staircase_greedy(). Returns (shape, end -> spot) or None."""
        c = (x + lg.NODE / 2, y + lg.NODE / 2)
        for inv0, base in ((v, b) for v in (0.0, 0.5, 1.0) for b in range(3, 400)):
            spots, inv = [], inv0
            for i in range(len(combs)):
                r = (base + 2 * i) * G
                spots.append((x - G * round(r * inv / G), y + side * r))
                inv += STEP_CLEAR / r
            if inv - STEP_CLEAR / r > MAX_INV or r > MAX_REACH:
                continue
            trial = shape
            for m, (px, py) in zip(combs, spots):
                S2 = ([(m, box(m, px, py))], [])
                edge = (c, (px + lg.NODE / 2, py + lg.NODE / 2), n, m)
                if clash(trial, S2, edge, guard):
                    break
                trial = (trial[0] + S2[0], trial[1] + [edge])
            else:
                return trial, dict(zip(combs, spots))
        return staircase_greedy(n, x, y, side, combs, shape, guard)

    def staircase_greedy(n, x, y, side, combs, shape, guard):
        """fallback for staircase(): each end takes the nearest
        free spot at least 2 rows further out than the one before and no further right, so the
        bundle to a later end passes to the LEFT of every nearer end instead of over its label
        (labels show to the right of their node). Every bundle stays steep enough (MAX_INV) to
        reach its own node under its label (Y5). Returns (shape, end -> spot) or None."""
        c = (x + lg.NODE / 2, y + lg.NODE / 2)
        trial, spots = shape, {}
        row, col = 1, x
        for m in combs:
            hit = None
            for r in range(row + 2, 400):
                for px in range(col, col - 24 * G - 1, -G):
                    if x - px > MAX_INV * r * G:
                        break
                    py = y + side * r * G
                    S2 = ([(m, box(m, px, py))], [])
                    edge = (c, (px + lg.NODE / 2, py + lg.NODE / 2), n, m)
                    if not clash(trial, S2, edge, guard):
                        hit = (px, py, S2, edge)
                        break
                if hit:
                    break
            if not hit:
                return None
            px, py, S2, edge = hit
            trial = (trial[0] + S2[0], trial[1] + [edge])
            spots[m] = (px, py)
            row, col = abs(py - y) // G, px
        return trial, spots

    def place(n, parent, x, y, inc=None):
        """place n's subtree with n at (x, y); return its shape (boxes, segments). inc: the vector
        from n to its parent (the bundle in from the parent runs along it); n's own fans keep out
        of its way."""
        pos[n] = (x, y)
        kids = [(m, L) for m, L in adj.get(n, []) if m != parent]
        shape = ([(n, box(n, x, y))], [])
        if not kids:
            return shape
        h = nodes_hint.get(n, {})
        ids = [m for m, _ in kids]
        main = h.get("main")
        if main is None and "main" not in h:
            plain = [m for m in ids if not labelled(kinds, m)     # a label on the row would hide the run
                     and m not in h.get("up", []) + h.get("down", [])]
            main = max(plain, key=lambda m: (size[m], m)) if plain else None
        if main is not None and labelled(kinds, main):
            main = None       # its label would lie along the run from n: it goes to a side instead
        ups = [m for m in h.get("up", []) if m in ids]
        downs = [m for m in h.get("down", []) if m in ids]
        rest = [m for m in ids if m != main and m not in ups and m not in downs]
        if labelled(kinds, n) and main is None and len(rest) == 2 and not (ups or downs):
            ups, downs, rest = [rest[0]], [rest[1]], []
        out = None if not inc or not inc[1] else ("down" if inc[1] < 0 else "up")
        # a side a trunk bundle runs straight along (layout_trunk guards) takes no fan
        blocked = {("down" if v[1] > 0 else "up") for v in hint.get("guards", []) + [inc or (0, 0)]
                   if parent is None and abs(v[1]) > abs(v[0])}
        flip = {"up": "down", "down": "up"}
        if out in blocked:
            out = flip[out] if flip[out] not in blocked else None
        for m in sorted(rest, key=lambda m: (size[m], m)):
            # a side branch fans outward, away from the bundle that comes in from its parent
            s = out or toward(d, m, rules) or side_of(m, n)
            if s == "up":
                ups.append(m)
            elif s == "down":
                downs.append(m)
            elif len(ups) <= len(downs):
                ups.append(m)
            else:
                downs.append(m)
        xk = x - max(dx_for(L) for _, L in kids)
        fan = max(len(ups), len(downs))
        if fan >= 4:      # a wide fan opens out so its bundles stay apart near the branch point
            xk = min(xk, x - G * min(20, 2 * fan))
        xl = min(xk, x - lg.LABEL_W - G)    # far enough left that a child's label stays clear of n
        c = (x + lg.NODE / 2, y + lg.NODE / 2)
        guard = [(c, (c[0] + v[0], c[1] + v[1])) for v in ([inc] if inc else []) +
                 (hint.get("guards", []) if parent is None else [])]
        last = h.get("main_last")      # the main run goes on past the side branches' labels
        # each child's own subtree is laid out once, at a base spot; the two arrangements below
        # only shift those shapes, so trying both costs no second layout
        base, sides = {}, []
        for side, kids_s in ((-1, ups), (1, downs)):
            combs = [m for m in kids_s if labelled(kinds, m) and len(adj.get(m, [])) == 1]
            others = [m for m in kids_s if m not in combs]
            for m in others:
                x0 = xl if labelled(kinds, m) else xk
                base[m] = (x0, place(m, n, x0, 0, (15 * G, -side * 15 * G)))
            sides.append((side, others, combs))
        if main:
            xm = min(x - dx_for(dict(kids)[main]), xl - lg.LABEL_W - 2 * G) if last else xk
            base[main] = (xm, place(main, n, xm, y, (3 * G, 0)))

        def arrange(main_first, ends_first):
            """main_first: the main run on its spot first and the side branches round it (as the
            front-left drawings were made); else the side branches first and the main run slid
            left until its subtree clears them (its own ends' labels reach back over n's column).
            ends_first: on each side the staircase of labelled ends before the other branches, or
            after them. Returns (failed placements, shape, child -> (dx, dy), labelled end -> spot)."""
            sh, offs, spots, fails = shape, {}, {}, 0

            def put_main(sh, slide):
                xm, S = base[main]
                for j in range(400):
                    S2 = shifted(S, 0, -j * G)
                    edge = (c, (xm - j * G + lg.NODE / 2, c[1]), n, main)
                    if slide and not clash(sh, S2, edge):
                        break
                    # main first: far enough left that no label of its subtree reaches n's column,
                    # which keeps a way out for the side branches
                    if not slide and all(b[2] <= x - PAD for m2, b in S2[0] if m2 != main):
                        break
                else:
                    if os.environ.get("LT_DEBUG"):
                        warn("  %s: main %s slide: %s" % (n, main, clash(sh, S2, edge)))
                    S2, edge, j = S, (c, (xm + lg.NODE / 2, c[1]), n, main), 0
                    offs[main] = (0, 0)
                    return (sh[0] + S2[0], sh[1] + S2[1] + [edge]), 1
                offs[main] = (-j * G, 0)
                return (sh[0] + S2[0], sh[1] + S2[1] + [edge]), 0

            if main and main_first:
                sh, f = put_main(sh, False)
                fails += f
            for side, others, combs in sides:
                for step in (("ends", "others") if ends_first else ("others", "ends")):
                    if step == "ends":
                        if combs:
                            got = staircase(n, x, y, side, combs, sh, guard)
                            if got is None:
                                fails += 1
                                if os.environ.get("LT_DEBUG"):
                                    warn("  %s first=%s: staircase %s %s" % (n, main_first, side, combs))
                                got = (sh, {m: (xl, y + side * (3 + 2 * i) * G) for i, m in enumerate(combs)})
                            sh, sp = got
                            spots.update(sp)
                    else:
                        for m in others:
                            x0, S = base[m]
                            tried = set()
                            for k in range(1, 400):
                                dy = y + side * k * G
                                S2 = shifted(S, dy)
                                edge = (c, (x0 + lg.NODE / 2, dy + lg.NODE / 2), n, m)
                                why = clash(sh, S2, edge, guard)
                                turn = round(math.degrees(math.atan2(y - dy, x - x0)) / 10)
                                if why == "c8" and turn not in tried and len(tried) < 6:
                                    # the bundle in hits m's own fans: lay m's subtree out again with
                                    # its guard along this bundle
                                    tried.add(turn)
                                    S = place(m, n, x0, 0, (x - x0, y - dy))
                                    base[m] = (x0, S)
                                    S2 = shifted(S, dy)
                                    why = clash(sh, S2, edge, guard)
                                if not why:
                                    break
                            else:
                                fails += 1
                                if os.environ.get("LT_DEBUG"):
                                    warn("  %s first=%s: side %s -> %s: %s" % (n, main_first, side, m, clash(sh, shifted(S, y + side * 60 * G), (c, (x0 + 15, y + side * 60 * G + 15), n, m), guard)))
                            offs[m] = (0, dy)
                            sh = (sh[0] + S2[0], sh[1] + S2[1] + [edge])
            if main and not main_first:
                sh, f = put_main(sh, True)
                fails += f
            return fails, sh, offs, spots

        tries = [(mf, ef) for mf in ((False,) if last else (True, False)) for ef in (False, True)]
        best = None
        for t in tries:
            got = arrange(*t)
            if not got[0]:
                break
            if best is None or got[0] < best[0]:
                best = (got[0], t)
        else:
            got = arrange(*best[1])     # again: a child may have been laid out again meanwhile
        fails, shape, offs, spots = got
        if fails:
            warn("%d bundle(s) out of %s found no free spot" % (fails, n))
        for m, (dx, dy) in offs.items():
            move(m, n, dy, dx)
        pos.update(spots)
        return shape

    def move(n, parent, dy, dx=0):
        todo = [(n, parent)]
        while todo:
            a, p = todo.pop()
            pos[a] = (pos[a][0] + dx, pos[a][1] + dy)
            todo += [(m, a) for m, _ in adj.get(a, []) if m != p]

    place(root, None, 0, 0, hint.get("inc"))
    missing = [n for n in adj if n not in pos]
    if missing:
        raise SystemExit("bundle graph is not one tree from %s: %s" % (root, missing[:5]))
    return pos


def layout_right(d, hint):
    """the tree grown to the RIGHT of its root (hint "grow": "right"): for a drawing whose root is
    its rear-most node, e.g. an engine loom from the firewall bulkhead forward. Labels show to the
    right, away from each parent, so this is the plain tidy tree the front-left drawings used:
    side branches fan up / down, a labelled node keeps its row and its (at most two) children
    drop straight up and down from it."""
    adj = tree(d)
    kinds = {x["id"]: k for k in lg.KINDS for x in d.get(k, [])}
    root = hint["root"]
    nodes_hint = hint.get("nodes", {})
    rules = hint.get("toward", {})
    pos = {}
    size = {}

    def count(n, parent):
        size[n] = 1 + sum(count(m, n) for m, _ in adj.get(n, []) if m != parent)
        return size[n]

    count(root, None)

    def side_of(n, parent):
        """majority side of the leaves under n (by 'toward'), else None."""
        votes = {"up": 0, "down": 0}
        todo = [(n, parent)]
        while todo:
            a, p = todo.pop()
            kids = [m for m, _ in adj.get(a, []) if m != p]
            if not kids:
                s = toward(d, a, rules)
                if s in votes:
                    votes[s] += 1
            todo += [(m, a) for m in kids]
        if votes["up"] != votes["down"]:
            return "up" if votes["up"] > votes["down"] else "down"
        return None

    def box(n, x, y):
        w = lg.LABEL_W if labelled(kinds, n) else lg.NODE
        return (x - PAD, y - PAD, x + w + PAD, y + lg.NODE + PAD)

    def shifted(shape, dy):
        bx = [(n, (b[0], b[1] + dy, b[2], b[3] + dy)) for n, b in shape[0]]
        sg = [((p[0], p[1] + dy), (q[0], q[1] + dy), a, z) for p, q, a, z in shape[1]]
        return bx, sg

    def grow(b, e=SEG_PAD):
        return (b[0] - e, b[1] - e, b[2] + e, b[3] + e)

    def clash(P, S, edge):
        """True if shape S (with the new edge joining it) collides with placed shape P."""
        pb, ps = P
        sb, ss = S
        for _, b in sb:
            if any(lg.boxes_overlap(b, c) for _, c in pb):
                return True
        for p, q, a, z in ss + [edge]:
            if any(lg.seg_hits_box(p, q, grow(c)) for n, c in pb if n not in (a, z)):
                return True
            if any(cross(p, q, r, s) for r, s, a2, z2 in ps if not {a, z} & {a2, z2}):
                return True
        for p, q, a, z in ps:
            if any(lg.seg_hits_box(p, q, grow(c)) for n, c in sb if n not in (a, z)):
                return True
        p, q, a, z = edge
        if any(lg.seg_hits_box(p, q, grow(c)) for n, c in sb if n not in (a, z)):
            return True
        return False

    def place(n, parent, x, y):
        """place n's subtree with n at (x, y); return its shape (boxes, segments)."""
        pos[n] = (x, y)
        kids = [(m, L) for m, L in adj.get(n, []) if m != parent]
        shape = ([(n, box(n, x, y))], [])
        if not kids:
            return shape
        h = nodes_hint.get(n, {})
        ids = [m for m, _ in kids]
        main = h.get("main")
        if main is None and not labelled(kinds, n) and "main" not in h:
            main = max(ids, key=lambda m: (size[m], m))
        ups = [m for m in h.get("up", []) if m in ids]
        downs = [m for m in h.get("down", []) if m in ids]
        rest = [m for m in ids if m != main and m not in ups and m not in downs]
        if labelled(kinds, n) and len(kids) == 2 and not (ups or downs):
            ups, downs, rest = [rest[0]], [rest[1]], []
        for m in sorted(rest, key=lambda m: (size[m], m)):
            s = toward(d, m, rules) or side_of(m, n)
            if s == "up":
                ups.append(m)
            elif s == "down":
                downs.append(m)
            elif len(ups) <= len(downs):
                ups.append(m)
            else:
                downs.append(m)
        xk = x + max(dx_for(L) for _, L in kids)
        fan = max(len(ups), len(downs))
        if fan >= 4:      # a wide fan opens out so its bundles stay apart near the branch point
            xk = max(xk, x + G * min(20, 2 * fan))
        if labelled(kinds, n) and len(kids) <= 2:
            xk = x      # drop straight up / down, clear of the label on n's row
        c = (x + lg.NODE / 2, y + lg.NODE / 2)
        last = h.get("main_last")      # side branches first, the main run goes on past their labels
        if main and not last:
            sb, ss = place(main, n, xk, y)
            shape = (shape[0] + sb, shape[1] + ss + [(c, (xk + lg.NODE / 2, c[1]), n, main)])
        for side, kids_s in ((-1, ups), (1, downs)):
            for m in kids_s:
                S = place(m, n, xk, 0)
                for k in range(1, 400):
                    dy = y + side * k * G
                    S2 = shifted(S, dy)
                    edge = (c, (xk + lg.NODE / 2, dy + lg.NODE / 2), n, m)
                    if not clash(shape, S2, edge):
                        break
                move(m, n, dy)
                shape = (shape[0] + S2[0], shape[1] + S2[1] + [edge])
        if main and last:
            xm = max(x + dx_for(dict(kids)[main]), xk + lg.LABEL_W + 2 * G)
            sb, ss = place(main, n, xm, y)
            shape = (shape[0] + sb, shape[1] + ss + [(c, (xm + lg.NODE / 2, c[1]), n, main)])
        return shape

    def move(n, parent, dy):
        todo = [(n, parent)]
        while todo:
            a, p = todo.pop()
            pos[a] = (pos[a][0], pos[a][1] + dy)
            todo += [(m, a) for m, _ in adj.get(a, []) if m != p]

    place(root, None, 0, 0)
    missing = [n for n in adj if n not in pos]
    if missing:
        raise SystemExit("bundle graph is not one tree from %s: %s" % (root, missing[:5]))
    return pos


def apply(d, pos, hint):
    org = hint.get("origin", [0, 0])
    for k in lg.KINDS:
        for x in d.get(k, []):
            if x["id"] in pos:
                px, py = pos[x["id"]]
                x["layoutPosition"] = {"x": int(px + org[0]), "y": int(py + org[1])}
    place_loose(d, hint)


def place_loose(d, hint):
    """splices / resistors / diodes at their location, loose nodes (no bundle) at their hint, on
    free spots."""
    near = hint.get("loose", {})
    inbund = {b[k] for b in d.get("bundles", []) for k in ("sourceId", "targetId")}
    todo = [(k, x) for k in ("branchPoints", "terminals", "connectors", "splices", "resistors", "diodes")
            for x in d.get(k, []) if x["id"] not in inbund]
    for _, x in todo:
        x["layoutPosition"] = None
    for k, x in todo:
        g = lg.geometry(d)
        anchor = near.get(x["id"]) or x.get("locationId")
        if anchor in g["centre"]:
            ax, ay = g["centre"][anchor]
            ax, ay = ax - 15, ay - 15
        else:
            ax, ay = min(b[0] for b in g["boxes"].values()), min(b[1] for b in g["boxes"].values()) - 120
        w = lg.LABEL_W if k in ("terminals", "connectors") else lg.SPLICE_W
        best = None
        for r in range(1, 40):
            for i in range(-r, r + 1):
                for j in range(-r, r + 1):
                    if max(abs(i), abs(j)) != r:
                        continue
                    px, py = ax + i * G, ay + j * G
                    box = (px - G, py - G, px + w + G, py + 2 * G)   # one free grid unit around it
                    if any(lg.boxes_overlap(box, b) for b in g["boxes"].values()):
                        continue
                    if any(lg.seg_hits_box(p, q, box) for pts in g["segments"].values()
                           for p, q in zip(pts, pts[1:])):
                        continue
                    dist = math.hypot(i, j)
                    if best is None or dist < best[0]:
                        best = (dist, px, py)
            if best:
                break
        x["layoutPosition"] = {"x": int(best[1]), "y": int(best[2])}


def write_atomic(path, d, newline="\n"):
    """temp file then rename, so the desktop app never reads half a file; 2-space JSON in the
    file's own key order and line ending (some drawings are stored CRLF)."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline=newline) as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def main(argv):
    import audit_layout
    import audit_drawing_rules
    write = "--write" in argv
    flip = "--mirror" in argv
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    looms = [a for a in argv if not a.startswith("--") and a != out]
    with open(HINTS, encoding="utf-8") as f:
        hints = json.load(f)
    files = model.harness_files()
    for loom in looms:
        path = os.path.join(model.REB, files[loom])
        mtime = os.path.getmtime(path)
        with open(path, "rb") as f:
            nl = "\r\n" if b"\r\n" in f.read(4096) else "\n"
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if flip:
            mirror(d)
        else:
            pos = layout(d, hints[loom])
            apply(d, pos, hints[loom])
        bad = audit_layout.check(loom, d) + [b for b in audit_drawing_rules.check(loom, d)
                                             if b.startswith(("L1", "G1"))]
        for b in bad:
            print(b)
        print("%s: %d layout finding(s)" % (loom, len(bad)))
        if write:
            if os.path.getmtime(path) != mtime:
                raise SystemExit("%s changed on disk while re-placing - not written" % path)
            write_atomic(path, d, nl)
        elif out:
            write_atomic(os.path.join(out, files[loom]), d, nl)


if __name__ == "__main__":
    main(sys.argv[1:])
