"""Schematic wire paths as the harness.design app draws them.

A wire in a .harness file stores no path, only its two ends and optional `layoutPoints`
(schematic waypoints, https://docs.harness.design/files/harness/wiring.md). The app computes the
drawn path. This module repeats that computation so the spacing gate (`audit_wire_spacing.py`)
and the router (`route_wires.py`) see the same lines Daniel sees. Source: the desktop app's own
routing code (`getPointsForLayoutPointLine`, `getHandleCenter`, `getHandleLocation`,
`getHandlePosition`, `getNonRotatedWidthForElement`; harness.design desktop, read 2026-10-14):

  - a handle's centre is the node's mid-width at the cavity row (cavity k: y + 30 * (k + 1.5));
    terminals, splices, diode / resistor ends: y + 15. Rotated nodes swap the axes.
  - a cavity / terminal / cable-core handle faces Right (or Left) toward the first waypoint, or
    the other end when there is none; rotated nodes face Bottom / Top. Diode / resistor ends are
    fixed Left / Right; a splice has no side.
  - the wire starts at the handle location: centre +- (width / 2 + 10) on that side (a cable:
    +- width / 2; a splice: its centre).
  - unless the next point already lies straight ahead, a stub of 31 runs out the side, snapped to
    the half-grid (15 + 30 n).
  - no waypoints: horizontal ends get a 45-degree dog-leg when the run is wider than tall, a
    rotated end facing a plain one gets one corner; otherwise a straight line between the stubs.
    With waypoints: straight lines stub -> each waypoint centre (position + 15) -> stub.
  - schematic wires are drawn 3 units wide (`lineWidth: 3`).
"""
GRID = 30
HALF = 15
LINE_WIDTH = 3
WIDTH = {"xs": 60, "md": 150}


def snap_between(v):
    return GRID * round((v - HALF) / GRID) + HALF


class Node:
    __slots__ = ("id", "kind", "x", "y", "w", "h", "rot", "el")

    def __init__(self, nid, kind, x, y, w, h, rot, el):
        self.id, self.kind, self.x, self.y, self.w, self.h, self.rot, self.el = nid, kind, x, y, w, h, rot, el

    def box(self):
        return (self.x, self.y, self.x + (self.h if self.rot else self.w), self.y + (self.w if self.rot else self.h))


def nodes(d):
    """id -> Node for every schematic element a wire can end on (plus notes, as obstacles)."""
    out = {}
    for c in d.get("connectors", []):
        p = c.get("schematicPosition") or c.get("layoutPosition")
        h = GRID + GRID * len(c.get("cavities", [])) + (GRID if c.get("shell") else 0)
        out[c["id"]] = Node(c["id"], "connector", p["x"], p["y"], c.get("width") or WIDTH["md"], h, bool(c.get("rotated")), c)
    for t in d.get("terminals", []):
        p = t.get("schematicPosition") or t.get("layoutPosition")
        out[t["id"]] = Node(t["id"], "terminal", p["x"], p["y"], t.get("width") or WIDTH["md"], GRID, bool(t.get("rotated")), t)
    for s in d.get("splices", []):
        p = s.get("schematicPosition") or s.get("layoutPosition")
        out[s["id"]] = Node(s["id"], "splice", p["x"], p["y"], GRID, GRID, False, s)
    for k in ("diodes", "resistors"):
        for s in d.get(k, []):
            p = s.get("schematicPosition") or s.get("layoutPosition")
            out[s["id"]] = Node(s["id"], k[:-1], p["x"], p["y"], GRID, GRID, bool(s.get("rotated")), s)
    for c in d.get("cables", []):
        p = c["schematicPosition"]
        h = GRID + GRID * len(c.get("cores", [])) + (GRID if c.get("shield") else 0)
        out[c["id"]] = Node(c["id"], "cable", p["x"], p["y"], WIDTH["xs"], h, bool(c.get("rotated")), c)
    for t in d.get("twistedWires", []):
        p = t["schematicPosition"]
        out[t["id"]] = Node(t["id"], "twisted", p["x"], p["y"], WIDTH["xs"], GRID + GRID * len(t["wires"]), bool(t.get("rotated")), t)
    return out


def row_offset(n, handle):
    if handle in ("Terminal", "Splice", "Left", "Right"):
        return HALF
    if n.kind == "connector":
        el = n.el
        if el.get("shell") and handle == el["shell"]["id"]:
            return GRID * (len(el["cavities"]) + 1.5)
        ids = [c["id"] for c in el["cavities"]]
        return GRID * (ids.index(handle) + 1.5) if handle in ids else 0
    if n.kind == "cable":
        el = n.el
        if el.get("shield") and handle == el["shield"]["id"]:
            return GRID * (len(el["cores"]) + 1.5)
        ids = [c["id"] for c in el["cores"]]
        return GRID * (ids.index(handle) + 1.5) if handle in ids else 0
    if n.kind == "twisted":
        ids = [c["id"] for c in n.el["wires"]]
        return GRID * (ids.index(handle) + 1.5) if handle in ids else 0
    return 0


def handle_center(n, handle):
    d = row_offset(n, handle)
    return (n.x + d, n.y + n.w / 2) if n.rot else (n.x + n.w / 2, n.y + d)


def handle_side(n, handle, center, other):
    """'L', 'R', 'T', 'B' or None (a splice)."""
    if handle == "Splice":
        return None
    if handle == "Left":
        return "B" if n.rot else "L"
    if handle == "Right":
        return "T" if n.rot else "R"
    if n.rot:
        return "B" if other[1] > center[1] else "T"
    return "R" if other[0] > center[0] else "L"


def handle_location(n, handle, center, side):
    if handle == "Splice" or side is None:
        return center
    off = n.w / 2 if n.kind in ("cable", "twisted") else n.w / 2 + 10
    x, y = center
    return {"L": (x - off, y), "R": (x + off, y), "T": (x, y - off), "B": (x, y + off)}[side]


def _ahead(p, side, q):
    return {"R": q[1] == p[1] and q[0] > p[0], "L": q[1] == p[1] and q[0] < p[0],
            "B": q[0] == p[0] and q[1] > p[1], "T": q[0] == p[0] and q[1] < p[1]}.get(side, False)


def _stub(p, side, q):
    if side is None or _ahead(p, side, q):
        return None
    dx, dy = {"L": (-(GRID + 1), 0), "R": (GRID + 1, 0), "T": (0, -(GRID + 1)), "B": (0, GRID + 1)}[side]
    return (snap_between(p[0] + dx), snap_between(p[1] + dy))


def _toward(side, a, b):
    return {"L": b[0] < a[0], "R": b[0] > a[0], "T": b[1] < a[1], "B": b[1] > a[1]}.get(side, True)


def _auto(I, L, w, x):
    """The no-waypoint shortcut; None means 'straight between the stubs'."""
    N, E = abs(L[0] - x[0]), abs(L[1] - x[1])
    hs, vs = I in ("L", "R"), I in ("T", "B")
    ht, vt = w in ("L", "R"), w in ("T", "B")
    if not (_toward(I, L, x) and _toward(w, x, L)):
        return None
    if hs and ht:
        if L[1] == x[1]:
            return []
        if N <= E:
            return None
        e = 1 if L[0] < x[0] else -1
        t = (N - E) / 2
        return [(L[0] + e * t, L[1]), (x[0] - e * t, x[1])]
    if vs and vt:
        if L[0] == x[0]:
            return []
        if E <= N:
            return None
        e = 1 if L[1] < x[1] else -1
        t = (E - N) / 2
        return [(L[0], L[1] + e * t), (x[0], x[1] - e * t)]
    if (hs and vt) or (vs and ht):
        i = L if vs else x
        r = L if hs else x
        return [(i[0], r[1])]
    if I is None and ht:
        if N > E:
            e = 1 if L[0] > x[0] else -1
            return [(x[0] + e * (N - E), x[1])]
        return [(L[0], x[1])]
    if I is None and vt:
        if E > N:
            e = 1 if L[1] > x[1] else -1
            return [(x[0], x[1] + e * (E - N))]
        return [(x[0], L[1])]
    if w is None and hs:
        if N > E:
            e = 1 if x[0] > L[0] else -1
            return [(L[0] + e * (N - E), L[1])]
        return [(x[0], L[1])]
    if w is None and vs:
        if E > N:
            e = 1 if x[1] > L[1] else -1
            return [(L[0], L[1] + e * (E - N))]
        return [(L[0], x[1])]
    return None


def path(ns, src, tgt, layout_points):
    """Drawn polyline [(x, y), ...] for one conductor line, or None if an end is missing."""
    a, b = ns.get(src["id"]), ns.get(tgt["id"])
    if not a or not b:
        return None
    wps = [(p["schematicPosition"]["x"] + HALF, p["schematicPosition"]["y"] + HALF) for p in (layout_points or [])]
    P, V = handle_center(a, src["handle"]), handle_center(b, tgt["handle"])
    f = wps[0] if wps else V
    y = wps[-1] if wps else P
    I, w = handle_side(a, src["handle"], P, f), handle_side(b, tgt["handle"], V, y)
    C, B = handle_location(a, src["handle"], P, I), handle_location(b, tgt["handle"], V, w)
    T, S = _stub(C, I, f), _stub(B, w, y)
    L, X = T or C, S or B
    M = _auto(I, L, w, X) if not wps else None
    pts = [C] + M + [B] if M is not None else [p for p in [C, T] + wps + [S, B] if p is not None]
    out = [pts[0]]
    for p in pts[1:]:
        if p != out[-1]:
            out.append(p)
    return out


def lines(d, ns=None):
    """(line id, source end, target end, polyline) for every wire and every cable-core section.
    Ends are (element id, handle). A cable core is two lines: cable -> source end, cable -> target
    end (the app's `conductorLineForConductorSection`)."""
    ns = ns or nodes(d)
    for w in d.get("wires", []):
        yield w["id"], (w["source"]["id"], w["source"]["handle"]), (w["target"]["id"], w["target"]["handle"]), \
            path(ns, w["source"], w["target"], w.get("layoutPoints"))
    for c in d.get("cables", []):
        for co in c.get("cores", []) + ([c["shield"]] if c.get("shield") else []):
            for end, key in (("source", "sourceLayoutPoints"), ("target", "targetLayoutPoints")):
                if co.get(end):
                    s = {"id": c["id"], "handle": co["id"]}
                    yield "%s/%s" % (co["id"], end), (c["id"], co["id"]), (co[end]["id"], co[end]["handle"]), \
                        path(ns, s, co[end], co.get(key))
    # twistedWires: none in ST185; add them here (same section rule as cables) if one is drawn.
