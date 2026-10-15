"""Re-place a drawing's LAYOUT view as an overhead view that follows its approved route
(DECISIONS R107, Dan 2026-10-15). Moves layoutPosition only - no wire, bundle, length, part,
colour, band or schematic change (R90).

The bundles of one harness form a tree. It is drawn as a tidy tree read left to right (R42):
  - x = towards the back of the car (the route top views have the front on the left),
  - up = passenger (RH) side, down = driver (LH) side, as in the route top views,
  - a branch point keeps its main run straight on its own row; side branches fan out above or
    below, each in its own band of rows, so no bundle, node or label lands on another (Y1-Y3),
  - a node that shows a label (connector, terminal) keeps its row to itself: its (at most two)
    children drop straight up and down from it, so no bundle runs over the label,
  - all children of a node share one x, set by the longest child bundle (a bundle keeps its
    `length`; only the canvas spacing follows it, roughly as its square root).
Splices, resistors and diodes (no bundle; they sit at their locationId) and loose nodes go on the
nearest free grid spot next to their location.

Hints per drawing: layout_hints.json - root (the front-most node), and per node the children
that go "up" / "down" (inner to outer) or "main"; "main_last": true places a hub's side branches
first, in one column, and carries the main run on past their labels (CabinPower's two hubs). A terminal broken off toward another harness
takes that harness's side from "toward" unless a node hint says otherwise.

    python docs/harness/layout_tree.py A-cabin [--write | --out DIR]

Without --write it only prints the audit_layout.py / L1 result for the new positions (--out DIR
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


def toward(d, n, rules):
    for x in d.get("terminals", []):
        if x["id"] == n:
            m = re.search(r"ST185-([A-Za-z0-9-]+)", x.get("signal") or "")
            if m:
                return rules.get(m.group(1))
    return None


def layout(d, hint):
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
