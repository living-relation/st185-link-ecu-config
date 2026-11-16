"""formboard.py - the layout view of a generated harness.design document.

Since 2026-11-15 (Dan: "I don't want them in the formboard layout. I want them in the regular layout view with straight
runs instead of the snaked runs"; replaces A25 a) every generator calls `regular(doc)` and the gate `check_regular(doc)`
(the last section of this file): formboard mode OFF, straight square runs on the grid, not to scale, every text clear. The
text model (TXT, text_boxes, label_overlaps) is shared. The 1:1 formboard below (`to_scale`, `check`; Dan A25 a,
2026-11-12) is kept with its self-tests but no generator calls it.

The 1:1 formboard:

The generators (gen_abeng, gen_engc, gen_cabin, gen_dash and the files built on it, gen_heavydc) first place every part on
their orthogonal formboard (README "harness.design"); `to_scale(doc)` then redraws the layout view so that every bundle is
drawn at exactly its set length (the master / tree length, never changed), the way harness.design's formboard mode measures
it, and turns formboard mode on with A3 panels. `check(doc)` is the gate: every drawn bundle length equals its set length
within 1 mm and no two bundles cross or overlap.

How harness.design measures a formboard (app.harness.design, read 2026-11-12; docs.harness.design/feature/formboard and
/feature/local-files/json-format "formboard"): one layout unit is 0.75 mm (FORMBOARD_MM_PER_PX); a bundle's path runs
from its source node's centre (layoutPosition + 15, 15) through its layoutPoints (each + 15, 15) to its target node's centre;
its drawn length is that polyline with every corner rounded at the bundle's radius (formboard.defaultCornerRadius unless the
bundle sets its own): roundedPathLength below is the app's own formula. The app calls a bundle to scale when the two
lengths differ by less than 0.5 mm, and draws any other bundle, or one with no set length (0 mm counts as none), yellow
with black dashes. The panel grid is centred on layout (0, 0).

The drawing (view only: no wire, pin, length or part changes):
- the tree keeps the generator's topology and each branch keeps the direction the generator gave it (front of the car
  RIGHT, driver side UP); each branch bundle is a straight line of its true length, or, when it is long
  (> SNAKE_MM) or a straight line would hit another bundle, a serpentine: legs across the run, U-turns at the bend
  radius, so long trunks fold up and the board shrinks; branches still leave the run only at their own nodes, so the
  branch order along every trunk is the generator's;
- the end stubs (100 mm end allowances, 25 mm splice stubs) fan out round their node as straight spokes, each at the
  angle nearest the way the generator combed it that clears everything else;
- a box seat is no 0 mm bundle (the app flags 0 mm as no set length): build_drawings.box_groups gives every seat end its
  own copy of the seat stub instead, so every routed wire length stays the same;
- mated plugs (bussed receptacle caps, the CAN-Lambda terminator plug, the RADLOK firewall pairs) sit face to face.
"""
import collections
import math
import os

DEBUG = bool(os.environ.get("FB_DEBUG"))

MM_PER_UNIT = 0.75            # harness.design FORMBOARD_MM_PER_PX
HALF = 15                     # a layout node is 30 x 30; bundles run from its centre
RADIUS_MM = 30                # default bend radius (the app's metric default)
SNAKE_MM = 450                # a branch longer than this folds up into a serpentine
PANEL = {"A3": (420, 297)}    # mm, landscape
MARGIN_MM = 60                # room round the harness for labels
ANNOTATION = 0.5              # labels, notes and part bars at half size (the harness itself is always 1:1)
CLR = 6.0                     # units: closest two bundles may run (4.5 mm), away from a node they share
NODE_GAP = 16.0               # units: closest two part symbols may sit, centre to centre (a terminal is about 1 cm = 13 units)
SHARED_R = 60.0               # units: bundles leaving one node may touch within this of it (45 mm), as they fan out
STUB_SEP = 15.0               # degrees: closest two end stubs of one node may run when one is a splice stub (no symbol)
COL_PITCH = 26.0              # units: the least row pitch of a label column fan (its stubs' length labels clear each other)
# the glove-box breakouts (Dan A35, 2026-11-13): the LOGIC box's ends to the left of the breakout, the POWER box's (and K-EPS,
# RLY-DRL beside it) to the right, whatever way the generator combed them
PREFER = {"bp_GB_LOGIC": (-1.0, 0.0), "bp_GB_POWER": (1.0, 0.0), "bp_GB_PBAR": (1.0, 0.0), "bp_GB_KEPS": (1.0, 0.0),
          "bp_GB_DRL": (1.0, 0.0)}


# ------------------------------------------------------------------ the app's length formula (app.harness.design 1221)
def rounded_length(pts, r):
    a = len(pts)
    if a <= 1: return 0.0
    if a == 2: return math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
    cut, arc = [0.0] * a, [0.0] * a
    for i in range(1, a - 1):
        o, l, s = pts[i - 1], pts[i], pts[i + 1]
        d, u, c, g = o[0] - l[0], o[1] - l[1], s[0] - l[0], s[1] - l[1]
        p, f = math.hypot(d, u), math.hypot(c, g)
        if p == 0 or f == 0: continue
        h = math.acos(max(-1.0, min(1.0, (d * c + u * g) / (p * f))))
        m = math.tan(h / 2)
        if not math.isfinite(m) or m < 1e-8: continue
        y = min(r / m, p if i == 1 else p / 2, f if i == a - 2 else f / 2)
        v = y * m
        if v < .01: continue
        cut[i], arc[i] = y, v * (math.pi - h)
    tot = sum(math.hypot(pts[t + 1][0] - pts[t][0], pts[t + 1][1] - pts[t][1]) - cut[t] - cut[t + 1] for t in range(a - 1))
    return max(0.0, tot + sum(arc[1:a - 1]))


# ------------------------------------------------------------------ geometry helpers
def _seg_dist(p, q, a, b):
    def pd(x, s, t):
        dx, dy = t[0] - s[0], t[1] - s[1]; L = dx * dx + dy * dy
        if L == 0: return math.hypot(x[0] - s[0], x[1] - s[1])
        k = max(0.0, min(1.0, ((x[0] - s[0]) * dx + (x[1] - s[1]) * dy) / L))
        return math.hypot(x[0] - s[0] - k * dx, x[1] - s[1] - k * dy)
    def orient(o, s, t): return (s[0] - o[0]) * (t[1] - o[1]) - (s[1] - o[1]) * (t[0] - o[0])
    d1, d2, d3, d4 = orient(a, b, p), orient(a, b, q), orient(p, q, a), orient(p, q, b)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 and d2 and d3 and d4: return 0.0
    return min(pd(p, a, b), pd(q, a, b), pd(a, p, q), pd(b, p, q))

def _clip(p, q, at, r0):
    """the part of segment p-q further than r0 from the point `at` (p or q may be at it); None if nothing is left"""
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    if L == 0: return None
    if math.hypot(p[0] - at[0], p[1] - at[1]) < 1e-6:
        if L <= r0: return None
        k = r0 / L; return ((p[0] + k * (q[0] - p[0]), p[1] + k * (q[1] - p[1])), q)
    if math.hypot(q[0] - at[0], q[1] - at[1]) < 1e-6:
        if L <= r0: return None
        k = 1 - r0 / L; return (p, (p[0] + k * (q[0] - p[0]), p[1] + k * (q[1] - p[1])))
    return (p, q)


def _clip2(s, at, r0):
    """the part of segment s further than r0 from the point at (the segment ends on it or passes near one end)"""
    p, q = s
    dp, dq = math.hypot(p[0] - at[0], p[1] - at[1]), math.hypot(q[0] - at[0], q[1] - at[1])
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    if L == 0: return None
    if dp < r0 and dq < r0: return None
    if dp < r0:      # walk from p until r0 away
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            x = (p[0] + mid * (q[0] - p[0]), p[1] + mid * (q[1] - p[1]))
            if math.hypot(x[0] - at[0], x[1] - at[1]) < r0: lo = mid
            else: hi = mid
        return ((p[0] + hi * (q[0] - p[0]), p[1] + hi * (q[1] - p[1])), q)
    if dq < r0:
        r = _clip2((q, p), at, r0)
        return (r[1], r[0]) if r else None
    return s


class Shape:
    """drawn bundles (polylines tagged with their two end nodes) and part symbols, in one frame"""
    def __init__(self):
        self.segs, self.nodes, self.texts = [], [], []      # (p, q, ends, bundle id) ; (point, node id) ; (polygon, owner)
    def moved(self, o, rot=None):
        s = Shape()
        tf = (lambda p: (p[0] + o[0], p[1] + o[1]))
        s.segs = [(tf(p), tf(q), e, b) for p, q, e, b in self.segs]
        s.nodes = [(tf(p), n) for p, n in self.nodes]
        s.texts = [([tf(p) for p in poly], w) for poly, w in self.texts]
        return s
    def add(self, other):
        self.segs += other.segs; self.nodes += other.nodes; self.texts += other.texts
    def bbox(self):
        xs = [c for p, q, *_ in self.segs for c in (p[0], q[0])] + [p[0] for p, _ in self.nodes]
        ys = [c for p, q, *_ in self.segs for c in (p[1], q[1])] + [p[1] for p, _ in self.nodes]
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _bb(p, q, g): return (min(p[0], q[0]) - g, min(p[1], q[1]) - g, max(p[0], q[0]) + g, max(p[1], q[1]) + g)
def _bbhit(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def clash(new, old, pos, clr=CLR, gap=NODE_GAP, r0=None):
    """the first clash between two shapes (None if none): bundles closer than clr (ignoring the stretch next to a node they
    share), a bundle through a part symbol it does not end on, or two part symbols closer than gap"""
    r0 = r0 if r0 is not None else SHARED_R
    obb = [(_bb(p, q, clr), (p, q, e, b)) for p, q, e, b in old.segs]
    for p, q, e, b in new.segs:
        nb = _bb(p, q, clr)
        for ob, (a, c, e2, b2) in obb:
            if not _bbhit(nb, ob): continue
            s1, s2 = (p, q), (a, c)
            near = set(e) & set(e2)
            near |= {n for n in e for m in e2 if n in pos and m in pos and math.hypot(pos[n][0] - pos[m][0], pos[n][1] - pos[m][1]) < r0}
            near |= {m for n in e for m in e2 if n in pos and m in pos and math.hypot(pos[n][0] - pos[m][0], pos[n][1] - pos[m][1]) < r0}
            for n in near:
                at = pos[n]
                s1 = _clip2(s1, at, r0) if s1 else None
                s2 = _clip2(s2, at, r0) if s2 else None
            if s1 and s2 and _seg_dist(s1[0], s1[1], s2[0], s2[1]) < clr: return ('bundles', b, b2)
        for x, n in old.nodes:
            if n in e: continue
            if _bbhit(nb, (x[0] - gap / 2, x[1] - gap / 2, x[0] + gap / 2, x[1] + gap / 2)) and \
               _seg_dist(p, q, x, x) < gap / 2: return ('bundle through part', b, n)
    for x, n in new.nodes:
        for p, q, e, b in old.segs:
            if n in e: continue
            if _bbhit(_bb(p, q, gap / 2), (x[0], x[1], x[0], x[1])) and _seg_dist(p, q, x, x) < gap / 2:
                return ('part on bundle', n, b)
        for y, m in old.nodes:
            if m != n and abs(x[0] - y[0]) < gap and abs(x[1] - y[1]) < gap and math.hypot(x[0] - y[0], x[1] - y[1]) < gap:
                return ('parts', n, m)
    return text_clash(new, old)


def text_clash(new, old, eps=None):
    """the first two text boxes (of different owners) of new and old that overlap, or None (Dan 2026-11-13)"""
    if not new.texts or not old.texts: return None
    eps = TXT["margin"] + 1.0 if eps is None else eps     # placing keeps one unit more than the gate asks
    ob = [(_pbb(p), p, w) for p, w in old.texts]
    for p, w in new.texts:
        bb = _pbb(p)
        for bb2, p2, w2 in ob:
            if w2 == w or (FAN_OF.get(w) and FAN_OF.get(w) == FAN_OF.get(w2)) or bb2[0] >= bb[2] + eps or bb[0] >= bb2[2] + eps or bb2[1] >= bb[3] + eps or bb[1] >= bb2[3] + eps:
                continue
            if _poly_hit(_grow(p, eps / 2), _grow(p2, eps / 2)): return ('texts', w, w2)
    return None


# ------------------------------------------------------------------ reading a document's layout
NODE_KINDS = ("branchPoints", "connectors", "terminals")
INLINE_KINDS = ("splices", "resistors", "diodes")

def _centre(e): return (e["layoutPosition"]["x"] + HALF, e["layoutPosition"]["y"] + HALF)

def _mm(length):
    v, u = length["value"], length.get("unit", "mm")
    return v * {"mm": 1, "cm": 10, "m": 1000, "in": 25.4, "ft": 304.8, "yd": 914.4}[u]

def radius_units(doc, b=None):
    fb = doc.get("formboard") or {}
    r = (b or {}).get("radius") or fb.get("defaultCornerRadius") or {"value": RADIUS_MM, "unit": "mm"}
    return _mm(r) / MM_PER_UNIT

def bundle_path(doc, b, at=None):
    """the drawn path of bundle b (centre coords), as the app builds it"""
    if at is None:
        at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    pts = [at[b["sourceId"]]] + [(p["layoutPosition"]["x"] + HALF, p["layoutPosition"]["y"] + HALF) for p in b.get("layoutPoints") or []] + [at[b["targetId"]]]
    out = [pts[0]]
    for p in pts[1:]:
        if p != out[-1]: out.append(p)
    return out

def drawn_mm(doc, b, at=None):
    return rounded_length(bundle_path(doc, b, at), radius_units(doc, b)) * MM_PER_UNIT


# ------------------------------------------------------------------ the layout
class _Tree:
    def __init__(self, doc):
        self.doc = doc
        self.el = {e["id"]: e for k in NODE_KINDS for e in doc.get(k, [])}
        self.old = {i: _centre(e) for i, e in self.el.items() if e.get("layoutPosition")}
        self.bps = {e["id"] for e in doc.get("branchPoints", [])}   # junction dots: no symbol to keep clear
        self.adj = {}
        for b in doc.get("bundles", []):
            assert b.get("length") and _mm(b["length"]) > 0, "bundle %s has no set length (0 mm is none): fix the generator" % b["id"]
            for s, t in ((b["sourceId"], b["targetId"]), (b["targetId"], b["sourceId"])):
                self.adj.setdefault(s, []).append((t, b))
        ends = set(self.adj)
        up = {n: n for n in ends}
        def find(n):
            while up[n] != n: n = up[n]
            return n
        for b in doc.get("bundles", []): up[find(b["sourceId"])] = find(b["targetId"])
        for m in doc.get("mates", []) or []:      # a mate between two bundle ends joins two pieces (RADLOK pairs): one per pair
            if m["sourceId"] in ends and m["targetId"] in ends and find(m["sourceId"]) != find(m["targetId"]):
                up[find(m["sourceId"])] = find(m["targetId"])
                for s, t in ((m["sourceId"], m["targetId"]), (m["targetId"], m["sourceId"])):
                    self.adj.setdefault(s, []).append((t, None))
        self.R = radius_units(doc)
        self.s = ANNOTATION
        self.mated = {x for m in doc.get("mates", []) or [] for x in (m["sourceId"], m["targetId"])}
        self.shown = display_signals(doc)
        self.wcount = bundle_wire_counts(doc)
        self.crowded = {e for _, _, ends in over_capacity(doc).values() for e in ends}
        # an over-capacity fan's own texts (its ends' labels, their stubs' length labels) are let overlap each other while
        # placing (cannot_fit lists them); everything else is still kept clear of them
        FAN_OF.clear(); FAN_OF.update(fan_owners(doc))

    textmode = "all"     # all: end labels and bundle texts kept clear while placing; labels: end labels only; none

    def node_texts(self, n, c, v):
        """n's details box when its centre is at c and its bundles lie along v (a branch point has none)"""
        e = self.el.get(n)
        if e is None or n in self.bps or self.textmode == "none": return []
        wl, ws = end_text_size(e, self.doc, self.s, self.shown.get(n))
        mt = n in self.mated
        box = end_box(c, detail_side(v, mt, e.get("layoutLabelPosition")), wl, ws, self.s, e, v, mt)
        return [(box, n)] if box else []

    def bundle_texts(self, b, path, spoke=False):
        """b's length label and label pills along path (path from b's source to its target); an end stub's are kept clear in
        every mode but none"""
        if self.textmode == "none" or (self.textmode == "labels" and not spoke): return []
        return [(p, b["id"]) for p in bundle_texts(b, path, self.s, (b["sourceId"] in self.bps, b["targetId"] in self.bps), self.wcount.get(b["id"], 1))]

    def old_dir(self, n, c, b):
        """unit vector of the generator's first step from n towards c (its comb point or c itself)"""
        p0 = self.old[n]
        pts = [self.old[n]]
        if b is not None:
            lp = [(p["layoutPosition"]["x"] + HALF, p["layoutPosition"]["y"] + HALF) for p in b.get("layoutPoints") or []]
            if b["sourceId"] != n: lp = lp[::-1]
            pts += lp
        pts.append(self.old[c])
        for p in pts[1:]:
            d = (p[0] - p0[0], p[1] - p0[1]); L = math.hypot(*d)
            if L > 1e-6: return (d[0] / L, d[1] / L)
        return (1.0, 0.0)

    def old_end_dir(self, n, c):
        d = (self.old[c][0] - self.old[n][0], self.old[c][1] - self.old[n][1]); L = math.hypot(*d)
        return (d[0] / L, d[1] / L) if L > 1e-6 else (1.0, 0.0)


def _snake(u, o, k, A, s0, s1, side=0):
    """a serpentine along u reaching o: k legs across the run (side 0: legs from +A to -A, centred on the run; side +1 / -1:
    teeth out to that side and back), straight leads s0 / s1 at the ends"""
    v = (-u[1], u[0])
    P = lambda a, l: (u[0] * a + v[0] * l, u[1] * a + v[1] * l)
    p = (o - s0 - s1) / k
    pts = [P(0, 0), P(s0, 0)]
    if side == 0:
        sd = 1
        for i in range(k):
            x = s0 + i * p
            pts += [P(x, sd * A), P(x + p, sd * A)]
            sd = -sd
        pts += [P(s0 + k * p, 0)]
    else:
        for i in range(k):
            x = s0 + i * p
            pts += ([P(x, side * A), P(x + p, side * A)] if i % 2 == 0 else [P(x, 0), P(x + p, 0)])
        pts += [P(s0 + k * p, 0)]
    pts += [P(o, 0)]
    out = [pts[0]]
    for q in pts[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-9: out.append(q)
    # drop points mid-way along a straight run (the app drops them on save)
    clean = [out[0]]
    for a, b in zip(out[1:], out[2:] + [None]):
        if b is not None:
            c = clean[-1]
            if abs((a[0] - c[0]) * (b[1] - a[1]) - (a[1] - c[1]) * (b[0] - a[0])) < 1e-6: continue
        clean.append(a)
    return clean


AMAX = 360.0                  # units: widest serpentine leg, either side of the run (270 mm)
LEAD = 140.0                  # units: straight run out of a node before a serpentine starts (105 mm), clear of its end stubs

def _paths(L, u, R, snake_first):
    """candidate drawn paths for a branch of drawn length L along u: straight, then serpentines, most compact first"""
    straight = [[(0.0, 0.0), (u[0] * L, u[1] * L)]]
    snakes = []
    for s0 in (LEAD, 4 * LEAD, 8 * LEAD):    # a longer lead first runs the fold clear of a crowded node (Dan 2026-11-13 labels)
        if s0 + LEAD + 2 * R < L - 1: snakes += _snakes(L, u, R, s0)
    return (snakes + straight) if snake_first else (straight + snakes)


def _snakes(L, u, R, s0):
    snakes = []
    s1 = LEAD; pitch = 2 * R; amin = 2 * R
    o = s0 + s1 + pitch
    while o < L - 1:
        kmax = int((o - s0 - s1) // pitch)
        for side in (0, 1, -1):
            for k in range(kmax, 0, -1):
                if side and k % 2 == 0: continue          # a tooth pattern ends back on the run after an odd count
                f = lambda A: rounded_length(_snake(u, o, k, A, s0, s1, side), R) - L
                if f(amin) > 0: continue
                if f(AMAX) < 0: break
                lo, hi = amin, AMAX
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if f(mid) < 0: lo = mid
                    else: hi = mid
                snakes.append(_snake(u, o, k, (lo + hi) / 2, s0, s1, side))
                break
        o += pitch
    return snakes


def _rot(u, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (u[0] * c - u[1] * s, u[0] * s + u[1] * c)


def _layout(T):
    """every piece of the layout (the main tree first, then any separate piece such as a ground strap, stacked below it)"""
    left, roots = set(T.adj), []
    parent, kids, order = {}, {}, []
    while left:
        cand = [n for n in left if T.old.get(n) == (HALF, HALF)] or sorted(left, key=lambda n: (-len(T.adj[n]), n))
        root = cand[0]; roots.append(root)
        parent[root] = None; part = [root]
        for n in part:
            for c, b in T.adj[n]:
                if c in parent:
                    assert parent[n] and parent[n][0] == c, "the layout is not a tree at %s" % c
                    continue
                parent[c] = (n, b); kids.setdefault(n, []).append((c, b)); part.append(c)
        order += part; left -= set(part)
    size = {}
    for n in reversed(order): size[n] = 1 + sum(size[c] for c, _ in kids.get(n, []))
    R = T.R

    def column_fan(n, at, spokes, Ls, pref, din, shape, pos):
        """n's end stubs as two label columns: each end on its spoke's circle, left or right of n, at its own row (pitch = its
        label stack + margin, at least COL_PITCH so the stubs' length labels clear too), its label turned to read away from n;
        (shape, positions, paths) or None. Tries the generator's sides first, then all left / all right / balanced"""
        back = math.degrees(math.atan2(-din[1], -din[0])) if din is not None else None
        hgt = {c: max(COL_PITCH, end_text_size(T.el[c], T.doc, T.s, T.shown.get(c))[1] + 2 * TXT["margin"] + 2)
               for c, _ in spokes}
        def side0(c): return "Left" if math.cos(math.radians(pref[c])) < 0 else "Right"
        tries = [{c: side0(c) for c, _ in spokes}, {c: "Left" for c, _ in spokes}, {c: "Right" for c, _ in spokes}]
        bal, tot = {}, {"Left": 0.0, "Right": 0.0}
        for c, _ in sorted(spokes, key=lambda cb: math.sin(math.radians(pref[cb[0]]))):
            sd = min(tot, key=lambda k: tot[k]); bal[c] = sd; tot[sd] += hgt[c]
        tries.append(bal)
        if any(c in T.crowded for c, _ in spokes): tries = [bal] + tries[:3]     # over capacity: halve the squeeze
        was = {c: T.el[c].get("layoutLabelPosition") for c, _ in spokes}
        def undo():
            for c, v in was.items():
                if v is None: T.el[c].pop("layoutLabelPosition", None)
                else: T.el[c]["layoutLabelPosition"] = v
        for sides, start in [(sd_, st_) for sd_ in tries for st_ in ("want", "low")]:
            sh1, ps1, pa1, ok = Shape(), dict(pos), {}, True
            sh1.add(shape)
            for sd in ("Left", "Right"):
                grp = sorted([(c, b) for c, b in spokes if sides[c] == sd], key=lambda cb: math.sin(math.radians(pref[cb[0]])))
                if not grp: continue
                L = min(Ls[c] for c, _ in grp) - 2.0
                need = sum(hgt[c] for c, _ in grp)
                sgn = -1 if sd == "Left" else 1
                def blocked(y, Lc):     # the way in (n's parent bundle) and 15 degrees either side of it stay clear
                    if back is None: return False
                    a = math.degrees(math.atan2(y, sgn * math.sqrt(max(0.0, Lc * Lc - y * y))))
                    return abs((a - back + 180) % 360 - 180) < 15
                gap = sum(2.0 for yy in range(int(-L), int(L) + 1, 2) if blocked(yy, L))
                if need > 2 * L - gap and all(c in T.crowded for c, _ in grp):     # over capacity: squeeze the rows evenly
                    for c, _ in grp: hgt[c] *= (2 * L - gap) / need * 0.97
                    need = sum(hgt[c] for c, _ in grp)
                if need > 2 * L:
                    if DEBUG: print("column_fan %s %s: %d ends need %.0f, room %.0f" % (n, sd, len(grp), need, 2 * L))
                    ok = False; break
                want = sum(math.sin(math.radians(pref[c])) for c, _ in grp) / len(grp) * L
                y0 = -L if start == "low" else max(-L, min(L - need, want - need / 2))
                for c, b in grp:
                    Lc = Ls[c]
                    y, placed = y0 + hgt[c] / 2, None
                    while y <= Lc - 1 and placed is None:     # the next free row: past the way in and anything already here
                        if blocked(y, Lc): y += 2.0; continue
                        x = math.sqrt(max(0.0, Lc * Lc - y * y)) * sgn
                        q = (at[0] + x, at[1] + y)
                        e = T.el[c]
                        nat = detail_side((at[0] - q[0], at[1] - q[1]), c in T.mated)
                        if nat != sd: e["layoutLabelPosition"] = sd
                        else: e.pop("layoutLabelPosition", None)
                        piece = Shape(); piece.segs.append((at, q, (n, c), b["id"]))
                        if c not in T.bps: piece.nodes.append((q, c))
                        piece.texts = T.node_texts(c, q, (at[0] - q[0], at[1] - q[1])) + \
                            T.bundle_texts(b, [at, q] if b["sourceId"] == n else [q, at], spoke=True)
                        allpos = dict(ps1); allpos[c] = q
                        if clash(piece, sh1, allpos) is None: placed = (q, piece)
                        else: y += 2.0
                    if placed is None:
                        if DEBUG: print("column_fan %s %s (%s): no free row for %s (%d ends need %.0f of %.0f; last hit %s)" % (
                            n, sd, start, c, len(grp), need, 2 * L, clash(piece, sh1, allpos) if 'piece' in dir() else None))
                        ok = False; break
                    q, piece = placed
                    y0 = y + hgt[c] / 2
                    sh1.add(piece); ps1[c] = q; pa1[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
                if not ok: break
            if ok: return sh1, ps1, pa1
            undo()
        return None

    def spokes_at(shape, pos, paths, n, at, spokes, din):
        """fan n's end stubs (straight spokes of their true length) round it, in the order the generator combed them,
        spread over the clear angles; adds them to shape / pos / paths; False if they do not fit"""
        if not spokes: return True
        Ls = {c: _mm(b["length"]) / MM_PER_UNIT for c, b in spokes}
        pref = {}
        for c, b in spokes:
            u0 = T.old_end_dir(n, c); pref[c] = math.degrees(math.atan2(u0[1], u0[0]))
        cut = (math.degrees(math.atan2(-din[1], -din[0])) if din is not None else 180.0)   # the way in: the fan starts after it
        rel = lambda a: (a - cut) % 360.0
        def tryspoke(c, b, a_deg, sh, ps):
            a = math.radians(a_deg); L = Ls[c]
            if din is not None and (math.cos(a) * din[0] + math.sin(a) * din[1]) < -0.97: return None
            # a splice stub (no part symbol of its own to keep apart) stays STUB_SEP degrees off every other stub here
            for c2, _ in spokes:
                if c2 == c or c2 not in ps or (c not in T.bps and c2 not in T.bps): continue
                a2 = math.atan2(ps[c2][1] - at[1], ps[c2][0] - at[0])
                if abs((math.degrees(a - a2) + 180) % 360 - 180) < STUB_SEP: return None
            q = (at[0] + math.cos(a) * L, at[1] + math.sin(a) * L)
            piece = Shape(); piece.segs.append((at, q, (n, c), b["id"]))
            if c not in T.bps: piece.nodes.append((q, c))
            piece.texts = T.node_texts(c, q, (at[0] - q[0], at[1] - q[1])) + \
                T.bundle_texts(b, [at, q] if b["sourceId"] == n else [q, at], spoke=True)
            allpos = dict(ps); allpos[c] = q
            return None if clash(piece, sh, allpos) is not None else (q, piece)
        # 1: each at the clear angle nearest its own (an over-capacity fan goes straight to its evenly squeezed columns, 3)
        sh1, ps1, pa1, ok = Shape(), dict(pos), {}, True
        sh1.add(shape)
        crowded_fan = any(c in T.crowded for c, _ in spokes)
        for c, b in ([] if crowded_fan else spokes):
            got = None
            for j in range(0, 721):
                got = tryspoke(c, b, pref[c] + (j + 1) // 2 * (1 if j % 2 else -1) * 0.5, sh1, ps1)
                if got: break
            if not got: ok = False; break
            q, piece = got; sh1.add(piece); ps1[c] = q; pa1[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
        if crowded_fan: ok = False
        if not ok and not crowded_fan:
            # 2: spread them evenly, in their own order round n, over the angles a spoke alone could take
            Lmax = max(Ls.values())
            free = [a / 2.0 for a in range(720) if tryspoke(spokes[0][0], spokes[0][1], cut + a / 2.0, shape, pos) is not None
                    and all(tryspoke(c, b, cut + a / 2.0, shape, pos) for c, b in spokes if Ls[c] == Lmax)]
            ok = len(free) >= len(spokes)
            if ok:
                orderd = sorted(spokes, key=lambda cb: rel(pref[cb[0]]))
                sh1, ps1, pa1 = Shape(), dict(pos), {}
                sh1.add(shape)
                k = len(orderd)
                for i, (c, b) in enumerate(orderd):
                    tgt = free[min(len(free) - 1, int((i + 0.5) * len(free) / k))]
                    got = None
                    for j in range(0, 721):
                        got = tryspoke(c, b, cut + tgt + (j + 1) // 2 * (1 if j % 2 else -1) * 0.5, sh1, ps1)
                        if got: break
                    if not got: ok = False; break
                    q, piece = got; sh1.add(piece); ps1[c] = q; pa1[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
        if not ok:
            # 3: label columns (Dan 2026-11-13, real label sizes): the ends left and right of n, each on its spoke's circle at
            # its own row so the labels (turned to read away from n, layoutLabelPosition) stack one above the other
            # (the splice stubs, no label of their own, then take the clear angles left)
            labelled = [(c, b) for c, b in spokes if c not in T.bps]
            got = None
            for stubs_first in (True, False):
                sh0, ps0, pa0, good = Shape(), dict(pos), {}, True
                sh0.add(shape)
                def put_stubs(sh_, ps_, pa_):
                    stubs = [(c, b) for c, b in spokes if c in T.bps]
                    if not stubs: return True
                    # spread evenly over the angles each could take alone, in their own order round n; else one by one
                    free = sorted({a for c, b in stubs for a in range(0, 360, 2) if tryspoke(c, b, a, sh_, ps_)})
                    k = len(stubs)
                    orderd = sorted(stubs, key=lambda cb: rel(pref[cb[0]]))
                    if len(free) >= k:
                        for off in range(0, max(1, len(free) // k)):
                            sh2, ps2, pa2, good = Shape(), dict(ps_), {}, True
                            sh2.add(sh_)
                            for i, (c, b) in enumerate(orderd):
                                a0 = free[(off + i * len(free) // k) % len(free)]
                                g = None
                                for j in range(0, 21):
                                    g = tryspoke(c, b, a0 + (j + 1) // 2 * (1 if j % 2 else -1) * 1.0, sh2, ps2)
                                    if g: break
                                if not g: good = False; break
                                q, piece = g; sh2.add(piece); ps2[c] = q; pa2[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
                            if good:
                                sh_.segs[:] = sh2.segs; sh_.nodes[:] = sh2.nodes; sh_.texts[:] = sh2.texts
                                ps_.update(ps2); pa_.update(pa2)
                                return True
                    for c, b in stubs:
                        g = None
                        for j in range(0, 721):
                            g = tryspoke(c, b, pref[c] + (j + 1) // 2 * (1 if j % 2 else -1) * 0.5, sh_, ps_)
                            if g: break
                        if not g:
                            if DEBUG:
                                for a_ in range(0, 360, 45):
                                    a = math.radians(a_); q = (at[0] + math.cos(a) * Ls[c], at[1] + math.sin(a) * Ls[c])
                                    pc = Shape(); pc.segs.append((at, q, (n, c), b["id"]))
                                    pc.texts = T.bundle_texts(b, [at, q] if b["sourceId"] == n else [q, at], spoke=True)
                                    print("   stub %s at %d: %s" % (c, a_, clash(pc, sh_, dict(ps_, **{c: q}))))
                                print("spokes_at %s: no angle for the splice stub %s (stubs first: %s)" % (n, c, stubs_first))
                            return False
                        q, piece = g; sh_.add(piece); ps_[c] = q; pa_[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
                    return True
                if stubs_first and not put_stubs(sh0, ps0, pa0): continue
                col = column_fan(n, at, labelled, Ls, pref, din, sh0, ps0)
                if not col: continue
                sh0, ps1_, pa1_ = col; ps0.update(ps1_); pa0.update(pa1_)
                if not stubs_first and not put_stubs(sh0, ps0, pa0): continue
                got = (sh0, ps0, pa0); break
            if not got: return False
            sh1, ps1, pa1 = got
        shape.segs[:] = sh1.segs; shape.nodes[:] = sh1.nodes; shape.texts[:] = sh1.texts
        pos.update(ps1); paths.update(pa1)
        return True

    def place_branches(n, din, order_b, shape, pos, paths):
        """place n's branches (in this order) into shape / pos / paths; None, or the (child, bundle) that found no place"""
        used = []
        for c, b in order_b:
            L = (_mm(b["length"]) / MM_PER_UNIT) if b is not None else 60.0
            u0 = PREFER.get(c) or T.old_dir(n, c, b)
            ax = max([(1, 0), (-1, 0), (0, 1), (0, -1)], key=lambda d: d[0] * u0[0] + d[1] * u0[1])
            # the generator's direction first, then its two square turns, then every 15 degrees nearest it
            cands = [ax, _rot(ax, 90), _rot(ax, -90)]
            cands = [cands[0]] + sorted(cands[1:], key=lambda d: -(d[0] * u0[0] + d[1] * u0[1]))
            cands += sorted((_rot(ax, a) for a in range(15, 360, 15) if a not in (90, 270)), key=lambda d: -(d[0] * ax[0] + d[1] * ax[1]))
            if din is not None: cands = [d for d in cands if d[0] * din[0] + d[1] * din[1] > -0.9]
            cands = [d for d in cands if all(d[0] * e[0] + d[1] * e[1] < 0.95 for e in used)]
            done = None
            for attempt in (0, 1):     # 0: the child's piece as laid on its own; 1: re-laid round what is already here
                for ci, u in enumerate(cands if attempt == 0 or T.textmode == "all" else cands[:12]):
                    paths_u = _paths(L, u, R, L * MM_PER_UNIT > SNAKE_MM) if b is not None else [[(0.0, 0.0), (u[0] * L, u[1] * L)]]
                    for path in (paths_u if attempt == 0 or T.textmode == "all" else paths_u[:9]):
                        end = path[-1]
                        own = Shape()
                        if b is not None:
                            own.segs = [(path[i], path[i + 1], (n, c), b["id"]) for i in range(len(path) - 1)]
                            own.texts = T.bundle_texts(b, path if b["sourceId"] == n else path[::-1])
                        if attempt == 0:
                            sub, spos, spaths = lay(c, u)
                        else:
                            if clash(own, shape, dict(pos, **{c: end})) is not None: continue
                            here = Shape(); here.add(shape); here.add(own)
                            back = here.moved((-end[0], -end[1]))
                            bpos = {k: (v[0] - end[0], v[1] - end[1]) for k, v in pos.items()}
                            try: sub, spos, spaths = lay(c, u, (back, bpos))
                            except AssertionError: continue
                        piece = sub.moved(end)
                        piece.segs = [x for x in piece.segs if x[3] != '(in)']
                        allpos = dict(pos); allpos.update({m: (q[0] + end[0], q[1] + end[1]) for m, q in spos.items()})
                        if attempt == 1:     # already laid clear of everything here
                            done = (u, path, piece, spos, spaths, own); break
                        if clash(own, piece, allpos) is None and clash(piece, shape, allpos) is None and clash(own, shape, allpos) is None:
                            done = (u, path, piece, spos, spaths, own); break
                    if done: break
                if done: break
            if not done: return (c, b)
            u, path, piece, spos, spaths, own = done
            end = path[-1]; used.append(u)
            shape.add(piece); shape.add(own)
            pos.update({m: (q[0] + end[0], q[1] + end[1]) for m, q in spos.items()})
            paths.update({k: [(q[0] + end[0], q[1] + end[1]) for q in v] for k, v in spaths.items()})
            if b is not None: paths[b["id"]] = path if b["sourceId"] == n else path[::-1]
        return None

    memo = {}
    def lay(n, din, ctx=None):
        """n's piece of the tree with n at (0, 0): (shape, node positions, bundle paths). ctx: what is already drawn
        round n (in n's frame), so the piece is laid clear of it; without it the piece is laid on its own (and cached)"""
        if ctx is not None: return _lay(n, din, ctx)
        key = (n, None if din is None else (round(din[0], 6), round(din[1], 6)))
        if key not in memo: memo[key] = _lay(n, din, None)
        return memo[key]

    def _lay(n, din, ctx):
        shape, pos, paths = Shape(), {n: (0.0, 0.0)}, {}
        if ctx is not None:
            shape.add(ctx[0]); pos.update(ctx[1])
        elif din is not None:   # the way in, so nothing grows back over the parent's bundle
            shape.segs.append(((0.0, 0.0), (-din[0] * 400, -din[1] * 400), (n, parent[n][0]), '(in)'))
        nctx = (len(shape.segs), len(shape.nodes), set(pos), len(shape.texts))
        if n not in T.bps: shape.nodes.append(((0.0, 0.0), n))
        if din is not None: shape.texts += T.node_texts(n, (0.0, 0.0), (-din[0], -din[1]))
        ch = kids.get(n, [])
        spokes = [(c, b) for c, b in ch if b is not None and not kids.get(c) and _mm(b["length"]) <= 200]
        shorts = [(c, b) for c, b in ch if b is not None and kids.get(c) and _mm(b["length"]) / MM_PER_UNIT < SHARED_R
                  and all(x is not None and not kids.get(k) and _mm(x["length"]) <= 200 for k, x in kids[c])]
        branches = [(c, b) for c, b in ch if (c, b) not in spokes and (c, b) not in shorts]
        order_b = sorted(branches, key=lambda cb: -size[cb[0]])
        start = (Shape(), dict(pos), dict(paths)); start[0].add(shape)
        for retry in range(len(order_b) + 1):
            shape = Shape(); shape.add(start[0]); pos = dict(start[1]); paths = dict(start[2])
            stuck = place_branches(n, din, order_b, shape, pos, paths)
            if stuck is None: break
            assert retry < len(order_b), "no clear place for the branch %s -> %s (%s)" % (n, stuck[0], stuck[1] and stuck[1]["id"])
            order_b = [x for x in order_b if x[0] == stuck[0]] + [x for x in order_b if x[0] != stuck[0]]     # place the one that got stuck first, then the rest
        for c, b in shorts:     # a very short branch whose part(s) end right by n: its spokes are placed here, among n's
            L = _mm(b["length"]) / MM_PER_UNIT
            u0 = T.old_dir(n, c, b)
            done = None
            for j in range(0, 72):
                a = math.atan2(u0[1], u0[0]) + math.radians((j + 1) // 2 * (1 if j % 2 else -1) * 5)
                q = (math.cos(a) * L, math.sin(a) * L)
                if din is not None and (q[0] * din[0] + q[1] * din[1]) / L < -0.9: continue
                piece = Shape(); piece.segs.append(((0.0, 0.0), q, (n, c), b["id"]))
                piece.texts = T.node_texts(c, q, (-q[0], -q[1])) + \
                    T.bundle_texts(b, [(0.0, 0.0), q] if b["sourceId"] == n else [q, (0.0, 0.0)], spoke=True)
                allpos = dict(pos); allpos[c] = q
                if clash(piece, shape, allpos) is not None: continue
                tsh = Shape(); tsh.add(shape); tsh.add(piece); tpos = dict(allpos); tpaths = {}
                if spokes_at(tsh, tpos, tpaths, c, q, kids[c], (q[0] / L, q[1] / L)):
                    done = (tsh, tpos, tpaths); break
            assert done, "no clear place for the short branch %s -> %s (%s)" % (n, c, b["id"])
            shape, pos = done[0], done[1]; paths.update(done[2])
            paths[b["id"]] = [(0.0, 0.0), pos[c]] if b["sourceId"] == n else [pos[c], (0.0, 0.0)]
        assert spokes_at(shape, pos, paths, n, (0.0, 0.0), spokes, din), "no clear spokes at %s" % n
        if ctx is not None:     # hand back only n's own piece
            k0, k1, p0, k2 = nctx
            out = Shape(); out.segs = shape.segs[k0:]; out.nodes = shape.nodes[k1:]; out.texts = shape.texts[k2:]
            shape = out; pos = {k: v for k, v in pos.items() if k not in p0 or k == n}
        return shape, pos, paths

    shape, pos, paths = Shape(), {}, {}
    for root in roots:
        sh, ps, pt = lay(root, None)
        o = (0.0, 0.0)
        if shape.segs or shape.nodes:      # a separate piece: where it keeps the board smallest, clear of everything else
            a, b = shape.bbox(), sh.bbox()
            allp = dict(pos); allp.update(ps)
            best = None
            for x in range(int(a[0] - b[0]), int(a[2] - b[0] + 400), 50):
                for y in range(int(a[1] - b[1]), int(a[3] - b[1] + 400), 50):
                    area = (max(a[2], b[2] + x) - min(a[0], b[0] + x)) * (max(a[3], b[3] + y) - min(a[1], b[1] + y))
                    if best and area >= best[0]: continue
                    q = {k: (v[0] + x, v[1] + y) for k, v in ps.items()}
                    tp = dict(pos); tp.update(q)
                    if clash(sh.moved((x, y)), shape, tp, clr=4 * CLR, gap=4 * NODE_GAP) is None: best = (area, (x, y))
            o = best[1] if best else (a[0] - b[0], a[3] + 200 - b[1])
        shape.add(sh.moved(o))
        pos.update({k: (v[0] + o[0], v[1] + o[1]) for k, v in ps.items()})
        paths.update({k: [(q[0] + o[0], q[1] + o[1]) for q in v] for k, v in pt.items()})
    return roots[0], shape, pos, paths


# ------------------------------------------------------------------ text on the board (Dan 2026-11-13: every label readable)
# Everything that is not the harness is drawn at the annotation scale s (feature/formboard "How the formboard is scaled").
# Sizes MEASURED on the app's own Formboard Panels PDF export (1:1 mm; CabinPower Rev G and EngineRoom-C Rev L,
# 2026-11-13, annotation 0.5; Dan 2026-11-13 "no label may overlap another"), in layout units (px) at s = 1 (mm / 0.75 / s):
# text widths are the app's own Inter TTF advance widths (resources/app-server/public/fonts/Inter, within 2 % of the PDF);
#  - an end's details (connector / terminal; app code: endpointDetailsPosition, CONNECTOR_ / TERMINAL_DETAILS_SPACING):
#    the side AWAY from the node's bundles (sum of the vectors to each bundle's first point; Left / Right when
#    |x| > |y| + 1, else Top / Bottom), ABOVE (Left / Right ends) or RIGHT (Top / Bottom ends) while mated, or
#    layoutLabelPosition (a visual side); the details start 15 + spacing units from the node centre (NOT scaled):
#    spacing along the end's own axis 20 (Left / Right) or 12 / 15 (Top / Bottom, connector / terminal), across it 15 / 7
#    (Left / Right) or 5 / 2 (Top / Bottom); then, scaled: row 1, 26 high: a terminal's label box (Inter SemiBold 11.2 px
#    text + 12, 20 high) then, 8 on, its signal (Inter SemiBold 14 px); a connector's label (14 px, no box); row 2, only
#    for an end with a part (the canvas draws the part bar, the PDF does not): 4 below, 20 high, 38 + its part number
#    (Inter SemiBold 12 px) wide. Left / Right: the stack vertically centred on the node; Top / Bottom: centred across it;
#  - a bundle's length label ("100 mm", Inter Regular 12 px + 8, 16 high) at the middle of its drawn path, along it;
#  - a bundle label pill (the ghost tags' coloured "AB-cabin 2", Inter SemiBold 16 px + 14, 20 high) along the bundle next
#    to the node it is drawn at;
#  - a layout note: its stored width (default 150) by its wrapped lines (7.5 per character, 22 per line, + 16).
# Two boxes of different owners must not overlap (a 1 unit margin). Self-test: selftest_text_sizes() (the PDF values).
TXT = dict(id_px=11.2, id_pad=12.0, id_h=20.0, id_gap=8.0, sig_px=14.0, row=26.0, bar_gap=4.0, bar_h=20.0, bar_px=12.0,
           bar_fixed=38.0, centre=15.0, len_px=12.0, len_pad=8.0, len_h=16.0, pill_px=16.0, pill_k=1.07, pill_pad=14.0, pill_h=20.0,
           note_ch=7.5, note_line=22.0, note_pad=16.0, margin=1.0, back_reach=40.0)
SPACING = {"connector": dict(along_h=20.0, along_v=12.0, across_h=15.0, across_v=5.0),
           "terminal": dict(along_h=20.0, along_v=15.0, across_h=7.0, across_v=2.0)}
# Inter advance widths, 1/1000 em, for ASCII 32..126 (Inter-Regular.ttf / Inter-SemiBold.ttf shipped with the app)
_INTER = {
    "Regular": [281, 288, 466, 633, 642, 982, 644, 300, 365, 365, 501, 662, 288, 460, 288, 360, 631, 407, 610, 618, 646, 593, 620,
                566, 619, 620, 288, 302, 662, 662, 662, 511, 966, 690, 654, 730, 722, 601, 590, 746, 743, 269, 571, 672, 565, 903,
                753, 765, 639, 765, 644, 642, 646, 744, 690, 985, 682, 679, 629, 365, 360, 365, 471, 456, 323, 562, 612, 571, 612,
                583, 370, 613, 591, 242, 242, 549, 242, 876, 591, 600, 612, 612, 376, 528, 327, 591, 562, 818, 546, 562, 552, 426,
                332, 426, 662],
    "SemiBold": [252, 321, 523, 644, 650, 1004, 663, 326, 373, 373, 540, 673, 319, 465, 319, 379, 660, 423, 623, 636, 666, 612,
                 640, 576, 640, 640, 319, 329, 673, 673, 673, 544, 999, 728, 659, 737, 722, 606, 588, 749, 746, 277, 580, 703, 565,
                 922, 759, 769, 645, 773, 652, 650, 660, 736, 728, 1020, 720, 713, 652, 373, 379, 373, 481, 469, 351, 574, 624, 582,
                 624, 591, 389, 626, 612, 262, 262, 569, 262, 900, 612, 609, 624, 624, 397, 549, 353, 612, 587, 839, 569, 588, 566,
                 455, 359, 455, 673]}


def text_w(text, px, weight="SemiBold", tnum=False):
    """the app's width of text in Inter at px (a character outside ASCII counts as a wide 1000 / 1000 em); tnum: the
    length labels' tabular figures (every digit 644 / 1000 em, measured: "210 mm" 17.84 mm at 12 px x 0.5)"""
    t = _INTER[weight]
    return sum((644 if tnum and ch.isdigit() else t[ord(ch) - 32]) if 32 <= ord(ch) < 127 else 1000 for ch in text or "") * px / 1000.0


def _scale(doc):
    return (doc.get("formboard") or {}).get("annotationScale") or 1.0


def _rect(cx, cy, w, h, ux=1.0, uy=0.0):
    """an oriented rectangle (4 corners) centred on (cx, cy), w along (ux, uy)"""
    vx, vy = -uy, ux
    hw, hh = w / 2, h / 2
    return [(cx + ux * a * hw + vx * b * hh, cy + uy * a * hw + vy * b * hh) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _poly_hit(p, q, eps=0.0):
    """two convex polygons overlap (separating axis), by more than eps"""
    for poly in (p, q):
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            nx, ny = b[1] - a[1], a[0] - b[0]
            L = math.hypot(nx, ny)
            if L == 0: continue
            nx, ny = nx / L, ny / L
            pa = [x * nx + y * ny for x, y in p]; qa = [x * nx + y * ny for x, y in q]
            if max(pa) <= min(qa) + eps or max(qa) <= min(pa) + eps: return False
    return True


def _pbb(poly):
    xs, ys = [x for x, _ in poly], [y for _, y in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def _part_number(doc, pid):
    for k, v in doc.items():
        if k.endswith("Parts"):
            for p in v:
                if p.get("id") == pid: return p.get("partNumber") or ""
    return ""


def detail_side(v, mated=False, override=None):
    """which side of a node its details sit on; v = sum of the vectors from the node to each bundle's first point"""
    if override: return override
    if abs(v[0]) > abs(v[1]) + 1: side = "Left" if v[0] > 0 else "Right"
    else: side = "Top" if v[1] > 0 else "Bottom"
    # mated (app endpointDetailsPosition): a Left / Right end shows its details above it, a Top / Bottom end to its right
    if mated: side = {"Left": "Top", "Right": "Top", "Top": "Right", "Bottom": "Right"}[side]
    return side


def end_kind(e):
    return "connector" if "cavities" in e or "type" not in e else "terminal"


def display_signals(doc):
    """{terminal id: the signal text the app shows beside it}: its own signal, else every signal on its net joined by "/"
    (seen on the PDF: "Switched +12 V/Coil +" for a bare relay coil end on the switched +12 V bus); the net runs through
    wires, cable cores, splices, mated connectors (same cavity designation) and global signals of one name"""
    up = {}
    def find(a):
        up.setdefault(a, a)
        while up[a] != a:
            up[a] = up[up[a]]; a = up[a]
        return a
    def join(a, b): up[find(a)] = find(b)
    def key(end):
        h = end.get("handle")
        return end["id"] if h in (None, "Terminal", "Splice") else "%s:%s" % (end["id"], h)
    sig = {}
    for t in doc.get("terminals", []):
        find(t["id"])
        if t.get("signal"): sig[t["id"]] = t["signal"]
    cav = {}
    for c in doc.get("connectors", []):
        for x in c.get("cavities", []):
            k = "%s:%s" % (c["id"], x["id"]); find(k)
            cav.setdefault(c["id"], {})[x.get("designation")] = k
            if x.get("signal"):
                sig[k] = x["signal"]
                if x.get("global"): join(k, "global:" + x["signal"])
    for w in doc.get("wires", []):
        if w.get("source") and w.get("target"): join(key(w["source"]), key(w["target"]))
    for cb in doc.get("cables", []) or []:
        for core in cb.get("cores", []) or []:
            if core.get("source") and core.get("target"): join(key(core["source"]), key(core["target"]))
    for m in doc.get("mates", []) or []:
        a, b = cav.get(m["sourceId"], {}), cav.get(m["targetId"], {})
        for d in set(a) & set(b): join(a[d], b[d])
    net = {}
    for k, v in sig.items():
        r = find(k)
        if v not in net.setdefault(r, []): net[r].append(v)
    return {t["id"]: t.get("signal") or "/".join(net.get(find(t["id"]), [])) for t in doc.get("terminals", [])}


def end_text_size(e, doc=None, s=1.0, shown=None):
    """(width, height) of a node's details stack at annotation scale s: row 1 (a terminal's label box + its signal, or a
    connector's label) and, for an end with a part, row 2 (its part bar); (0, 0) when it shows nothing. shown: the
    terminal's signal text as the app shows it (display_signals), else its own signal"""
    kind = end_kind(e)
    lab, sig = e.get("label") or "", (shown if shown is not None else e.get("signal")) or ""
    if kind == "terminal":
        box = (text_w(lab, TXT["id_px"]) + TXT["id_pad"]) if lab else 0.0
        txt = text_w(sig, TXT["sig_px"]) if sig else 0.0
        w1 = box + txt + (TXT["id_gap"] if box and txt else 0.0)
    else:
        w1 = text_w(lab, TXT["sig_px"]) if lab else 0.0
    pn = _part_number(doc, e["partId"]) if e.get("partId") and doc is not None else ""
    w2 = (TXT["bar_fixed"] + text_w(pn, TXT["bar_px"])) if pn else 0.0
    if not (w1 or w2): return 0.0, 0.0
    h = TXT["row"] + ((TXT["bar_gap"] + TXT["bar_h"]) if w2 else 0.0)
    return max(w1, w2) * s, h * s


def end_box(c, side, wl, ws, s=1.0, e=None, v=(1.0, 0.0), mated=False, wmax=None):
    """the details box of a node centred at c on that side; wl, ws = end_text_size (width, height, already scaled); e and v
    (the end and its bundle vector) give the spacing the app keeps from the node; wmax: the width the app cuts a connector's
    label (any side) or a label above / below its node to, with "..." (the regular view: 240, measured in the app 2026-11-16)"""
    w, h = wl, ws
    if not (w and h): return None
    if wmax and (side in ("Top", "Bottom") or (e is not None and end_kind(e) == "connector")): w = min(w, wmax)
    sp = SPACING[end_kind(e) if e is not None else "terminal"]
    horiz = abs(v[0]) > abs(v[1]) + 1          # the end's own axis (its orientation)
    if mated: horiz = not horiz                 # details beside it, across its axis (measured 4.5 units nearer: allow 5)
    if side in ("Left", "Right"):
        off = TXT["centre"] + (sp["along_h"] if horiz else sp["across_h"])
    else:
        off = TXT["centre"] + (sp["along_v"] if not horiz else sp["across_v"])
    if mated: off -= 5.0
    # a connector's details on the side of its own bundle (the "back") sit beyond its part drawing: allow its reach
    back = e is not None and end_kind(e) == "connector" and e.get("layoutLabelPosition") and \
        side == {"Left": "Right", "Right": "Left", "Top": "Bottom", "Bottom": "Top"}[detail_side(v)]
    if back:
        w += TXT["back_reach"] if side in ("Left", "Right") else 0.0
        h += TXT["back_reach"] if side in ("Top", "Bottom") else 0.0
    if side in ("Left", "Right"):
        x0 = c[0] + off if side == "Right" else c[0] - off - w
        return _rect(x0 + w / 2, c[1], w, h)
    y0 = c[1] + off if side == "Bottom" else c[1] - off - h
    return _rect(c[0], y0 + h / 2, w, h)


def _along(pts, frac):
    """the point at frac of a polyline's length and the unit direction there"""
    segs = [(pts[i], pts[i + 1], math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])) for i in range(len(pts) - 1)]
    tot = sum(L for *_, L in segs) or 1.0
    want = tot * frac
    for a, b, L in segs:
        if L == 0: continue
        if want <= L or (a, b, L) == segs[-1]:
            k = min(1.0, want / L)
            return (a[0] + k * (b[0] - a[0]), a[1] + k * (b[1] - a[1])), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        want -= L
    return pts[0], (1.0, 0.0)


def _len_text(b):
    v = b["length"]["value"]
    return "%s %s" % (("%g" % v), b["length"].get("unit", "mm"))


def _mid_run(pts):
    """the middle of the straight run that holds a polyline's half-way point, and the unit direction of that run"""
    segs = [(pts[i], pts[i + 1], math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])) for i in range(len(pts) - 1)]
    want = sum(L for *_, L in segs) / 2.0
    for a, b, L in segs:
        if L and (want <= L or (a, b, L) == segs[-1]):
            return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        want -= L
    return pts[0], (1.0, 0.0)


REG_LEN_OFF, REG_LEN_H, REG_TOP_W = 15.0, 22.0, 240.0


def bundle_texts(b, path, s=1.0, end_nodes=(), n=1, board=True, kinds=None):
    """the text boxes a bundle draws on the board: its length label, and its label pills; n = wires through it. board=False:
    the regular view (formboard mode off), measured in the app's own drawing on 2026-11-16 (ST185-RearFuel Rev B, layout
    view DOM): the length label sits at the middle of the straight run that holds the path's half-way point (not at the
    half-way point itself), its centre 14 - 15 units off the line, 20 high ("100 mm" 54 wide, "2734 mm" 64: the TXT widths);
    a bundle label is small text on the bundle itself (Inter SemiBold about 8 px, 10 high: "AntiTheft" 37 wide), ending where
    the node symbol starts (ST185-AB-cabin 1 Rev F, 2026-11-16)"""
    out = []
    kinds = [] if kinds is None else kinds          # filled in step with the boxes: "len" (length label) or "tag" (label)
    lw = len_label_w(b, s) if b.get("length") else 0
    plen = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1))
    # a bundle too short for its length label to clear the hub (the 2 mm / 15 mm junction steps of a tree, the 25 mm splice
    # stubs: the label, centred on the bundle, reaches within 15 units of a node centre, inside the node symbol where every
    # bundle of that node meets) cannot carry it clear whatever the layout: left out of the gate, counted by
    # short_length_labels() (Dan 2026-11-13 real label sizes: a 25 mm stub's "25 mm" tag is 24 units long on a 33-unit stub)
    if b.get("length") and len(path) > 1 and plen >= lw + 2 * HALF:
        c, u = _along(path, 0.5) if board else _mid_run(path)
        # the text reads left to right (straight up when the bundle is vertical) and sits off the bundle on the text's
        # upper side, further for a thicker bundle; +-3 units across for the bundle thickness the model does not know
        d = u if u[0] > 1e-9 else ((-u[0], -u[1]) if u[0] < -1e-9 else (0.0, -1.0))
        off = len_label_offset(n) * s / 0.5 if board else REG_LEN_OFF
        out.append(_rect(c[0] + d[1] * off, c[1] - d[0] * off, lw, (TXT["len_h"] * s + (2.0 if n <= 2 else 6.0)) if board else REG_LEN_H, *d))
        kinds.append("len")
    pills = []
    if b.get("separateLabels"):
        if b.get("label"): pills.append((b["label"], 0))
        if b.get("endLabel"): pills.append((b["endLabel"], 1))
    elif b.get("label") and not b.get("middleLabel"):
        pills += [(b["label"], 0), (b["label"], 1)]
    for text, end in pills:
        if not b.get("separateLabels") and end_nodes and end_nodes[end]: continue    # skipped at a branch point
        w, h = (text_w(text, TXT["pill_px"]) * TXT["pill_k"] + TXT["pill_pad"]) * s, TXT["pill_h"] * s
        if not board: w, h = text_w(text, 8.0) + 2.0, 12.0
        p = path if end == 0 else path[::-1]
        L = sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)) or 1.0
        c, u = _along(p, min(0.5, (HALF + (2 if board else 0) + w / 2) / L))
        out.append(_rect(c[0], c[1], w, h, *u))
        kinds.append("tag")
    return out


def short_length_labels(doc):
    """the bundles too short to carry their own length label (left out of the label gate; see bundle_texts)"""
    s = _scale(doc)
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    out = []
    for b in doc.get("bundles", []):
        if not b.get("length") or b["sourceId"] not in at or b["targetId"] not in at: continue
        p = bundle_path(doc, b, at)
        if sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)) < len_label_w(b, s) + 2 * HALF:
            out.append(b["id"])
    return out


def bundle_wire_counts(doc):
    """{bundle id: wires routed through it} (each wire runs the tree path between its two ends; a splice, diode or resistor
    end sits on its locationId node); the drawn bundle grows with it, and the app sets its length label off to one side"""
    adj = {}
    for b in doc.get("bundles", []):
        adj.setdefault(b["sourceId"], []).append((b["targetId"], b["id"]))
        adj.setdefault(b["targetId"], []).append((b["sourceId"], b["id"]))
    loc = {e["id"]: e.get("locationId") for k in INLINE_KINDS for e in doc.get(k, [])}
    def node(end): return loc.get(end["id"]) or end["id"]
    def path(a, z):
        if a == z or a not in adj or z not in adj: return []
        prev, todo = {a: None}, [a]
        for n in todo:
            if n == z: break
            for m, bid in adj[n]:
                if m not in prev: prev[m] = (n, bid); todo.append(m)
        if z not in prev: return []
        out, n = [], z
        while prev[n]: out.append(prev[n][1]); n = prev[n][0]
        return out
    cnt = {}
    for w in doc.get("wires", []):
        if not (w.get("source") and w.get("target")): continue
        for bid in path(node(w["source"]), node(w["target"])): cnt[bid] = cnt.get(bid, 0) + 1
    return cnt


def len_label_offset(n):
    """how far (units, at s = 0.5) the app sets a length label's centre off its bundle's centre line, to the bundle's left
    (above a bundle drawn left to right): 10.1 for a one-wire stub, 14.4 - 16.1 for the 20 - 40 wire trunks (measured)"""
    return 8.6 + 1.5 * math.sqrt(max(1, n))


def len_label_w(b, s=1.0):
    """the width of a bundle's length label tag ("100 mm") at annotation scale s"""
    return (text_w(_len_text(b), TXT["len_px"], "Regular", True) + TXT["len_pad"]) * s


def selftest_text_sizes():
    """the text model against the sizes measured on the app's Formboard Panels PDF (CabinPower Rev G, 2026-11-13,
    annotation 0.5, mm at 1:1); [] when every one is within 3 %"""
    mm = lambda u: u * MM_PER_UNIT * 0.5
    bad = []
    def near(what, got, want, tol=0.03):
        if abs(got - want) > tol * want: bad.append("%s: model %.2f mm, PDF %.2f mm" % (what, got, want))
    near("length label '210 mm' text", mm(text_w("210 mm", TXT["len_px"], "Regular", True)), 17.84)
    near("length label tag height", mm(TXT["len_h"]), 6.00)
    near("length label tag '210 mm'", mm(text_w("210 mm", TXT["len_px"], "Regular", True) + TXT["len_pad"]), 20.85)
    near("signal 'Pop-up UP (to ground)'", mm(text_w("Pop-up UP (to ground)", TXT["sig_px"])), 57.10)
    near("connector label 'Pop-up diode 2 (DRL switch side)'", mm(text_w("Pop-up diode 2 (DRL switch side)", TXT["sig_px"])), 84.27)
    near("label box text 'LOGIC box seat M1, ...'", mm(text_w("LOGIC box seat M1, terminal 86 - Low-beam relay (K-HL, LOGIC box)", TXT["id_px"])), 138.01)
    near("label box 'LOGIC box seat M1, ...'", mm(text_w("LOGIC box seat M1, terminal 86 - Low-beam relay (K-HL, LOGIC box)", TXT["id_px"]) + TXT["id_pad"]), 142.52)
    near("label box height", mm(TXT["id_h"]), 7.50)
    near("pill text 'AB-cabin 2'", mm(text_w("AB-cabin 2", TXT["pill_px"]) * TXT["pill_k"]), 34.46)
    near("pill height", mm(TXT["pill_h"]), 7.50)
    # offsets are not scaled: a terminal's details 15 + 20 units beside its centre (26.25 mm), 15 + 15 above or below (22.5)
    near("terminal details beside, from the node centre", (TXT["centre"] + SPACING["terminal"]["along_h"]) * MM_PER_UNIT, 26.7)
    near("terminal details above, row centre", (TXT["centre"] + SPACING["terminal"]["along_v"]) * MM_PER_UNIT + mm(TXT["row"]) / 2, 27.4)
    near("connector details above, row centre", (TXT["centre"] + SPACING["connector"]["along_v"]) * MM_PER_UNIT + mm(TXT["row"]) / 2, 25.1)
    return bad


def note_box(n, s=1.0):
    w = n.get("width") or 150
    per = max(1, int((w - TXT["note_pad"]) // TXT["note_ch"]))
    lines = sum(max(1, math.ceil(len(par) / per)) for par in (n.get("text") or "").split("\n"))
    h = lines * TXT["note_line"] + TXT["note_pad"]
    x, y = n["layoutPosition"]["x"], n["layoutPosition"]["y"]
    return _rect(x + w * s / 2, y + h * s / 2, w * s, h * s)


R_INLINE = 90     # units: pitch of the inline parts (splices, resistors, diodes) that share one spot, one under the other


def inline_box(e, doc, c):
    """the text stack an inline part (splice, resistor, diode) draws ABOVE its symbol, centred on it: its label box and, with
    a part, its part bar over that (measured in the app's layout view, 2026-11-16, ST185-CabinPower Rev G: "Low-beam fuse
    splice" box 20 high ending 16 units above the symbol centre, the "GENERIC SOLDER SPLICE" bar 20 high 5 above the box)"""
    lab = e.get("label") or ""
    pn = _part_number(doc, e["partId"]) if e.get("partId") else ""
    w1 = (text_w(lab, TXT["id_px"]) + TXT["id_pad"]) if lab else 0.0
    w2 = (TXT["bar_fixed"] + text_w(pn, TXT["bar_px"])) if pn else 0.0
    if not (w1 or w2): return None
    h = (20.0 if w1 else 0.0) + (25.0 if w2 else 0.0)
    return _rect(c[0], c[1] - 16.0 - h / 2, max(w1, w2), h)


def text_boxes(doc):
    """[(owner, polygon, what)] for every text the layout view draws (estimated, see TXT)"""
    s = _scale(doc)
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    bps = {e["id"] for e in doc.get("branchPoints", [])}
    wc = bundle_wire_counts(doc)
    board = bool(doc.get("formboard"))
    vec = {}
    out = []
    for b in doc.get("bundles", []):
        if b["sourceId"] not in at or b["targetId"] not in at: continue
        path = bundle_path(doc, b, at)
        if len(path) < 2: continue      # drawn with no length (check_regular lists it)
        n0 = len(out)
        for n, nxt in ((b["sourceId"], path[1]), (b["targetId"], path[-2])):
            v = vec.get(n, (0.0, 0.0)); vec[n] = (v[0] + nxt[0] - at[n][0], v[1] + nxt[1] - at[n][1])
        kd = []
        for poly in bundle_texts(b, path, s, (b["sourceId"] in bps, b["targetId"] in bps), wc.get(b["id"], 1), board=board, kinds=kd):
            # the regular view: a bundle's tag is a text of its own, clear of that bundle's own length label too
            out.append((b["id"] + ("#tag" if not board and kd[len(out) - n0] == "tag" else ""), poly, "bundle text"))
    mated = {x for m in doc.get("mates", []) or [] for x in (m["sourceId"], m["targetId"])}
    if not board:      # a mated half with no bundle (a cap) takes its side from where its other half sits (above it, side by side)
        for m in doc.get("mates", []) or []:
            for a, c in ((m["sourceId"], m["targetId"]), (m["targetId"], m["sourceId"])):
                if a not in vec and a in at and c in at: vec[a] = (at[c][0] - at[a][0], at[c][1] - at[a][1])
    shown = display_signals(doc)
    for k in ("connectors", "terminals"):
        for e in doc.get(k, []):
            if not e.get("layoutPosition"): continue
            v, mt = vec.get(e["id"], (0.0, 0.0)), e["id"] in mated
            side = detail_side(v, mt, e.get("layoutLabelPosition"))
            wl, ws = end_text_size(e, doc, s, shown.get(e["id"]))
            box = end_box(at[e["id"]], side, wl, ws, s, e, v, mt, None if board else REG_TOP_W)
            if box: out.append((e["id"], box, "label"))
    if not board:      # the regular view: an inline part's label and part bar above its symbol
        for k in INLINE_KINDS:
            for e in doc.get(k, []):
                box = inline_box(e, doc, _centre(e)) if e.get("layoutPosition") else None
                if box: out.append((e["id"], box, "label"))
    for n in doc.get("layoutNotes", []) or []:
        if n.get("layoutPosition"): out.append((n["id"], note_box(n, s), "note"))
    return out


def over_capacity(doc):
    """{node: (label stack height needed, room, [its end ids])} for every node whose short end stubs carry more label rows
    than can ever stand clear round it. An end hangs within its stub length R of the node; every end label reads across
    (Left / Right) or sits above / below it, and all of one side's labels share the same x span, so they need their own rows:
    room = two columns of 2R + 25 plus a 25-unit row above and below each (generous, so a fan that can fit is never let off).
    Such a fan can only be cleared by a physical change (longer stubs) or a smaller annotation scale: Dan's call."""
    s = _scale(doc)
    el = {e["id"]: e for k in ("connectors", "terminals") for e in doc.get(k, [])}
    shown = display_signals(doc)
    adj = {}
    for b in doc.get("bundles", []):
        adj.setdefault(b["sourceId"], []).append((b["targetId"], b)); adj.setdefault(b["targetId"], []).append((b["sourceId"], b))
    out = {}
    for n, lst in adj.items():
        if n in el: continue
        leaves = [(c, b) for c, b in lst if c in el and len(adj.get(c, [])) == 1 and b.get("length") and _mm(b["length"]) <= 200]
        if len(leaves) < 6: continue
        R = max(_mm(b["length"]) for _, b in leaves) / MM_PER_UNIT
        need = sum(end_text_size(el[c], doc, s, shown.get(c))[1] + 2 * TXT["margin"] + 1 for c, _ in leaves)
        room = 2 * (2 * R + 25) + 4 * 25
        if need > room: out[n] = (round(need), round(room), sorted(c for c, _ in leaves))
    return out


def label_overlaps(doc, eps=None):
    """[(a, b)] pairs of text boxes of different owners that overlap (TXT margin): the label gate"""
    eps = TXT["margin"] if eps is None else eps
    boxes = [(o, p, w, _pbb(p)) for o, p, w in text_boxes(doc)]
    boxes.sort(key=lambda t: t[3][0])
    bad = []
    for i, (o, p, w, bb) in enumerate(boxes):
        for o2, p2, w2, bb2 in boxes[i + 1:]:
            if bb2[0] >= bb[2] + eps: break
            if o2 == o or bb2[1] >= bb[3] + eps or bb[1] >= bb2[3] + eps: continue
            if _poly_hit(_grow(p, eps / 2), _grow(p2, eps / 2)): bad.append(("%s %s" % (w, o), "%s %s" % (w2, o2)))
    return bad


def _grow(poly, d):
    cx, cy = sum(x for x, _ in poly) / 4, sum(y for _, y in poly) / 4
    out = []
    for x, y in poly:
        L = math.hypot(x - cx, y - cy) or 1.0
        out.append((x + (x - cx) / L * d * 1.42, y + (y - cy) / L * d * 1.42))
    return out


def _r2(v): return round(v + 0.0, 2)

def to_scale(doc, panel="A3", annotation=ANNOTATION):
    """redraw doc's layout view as a 1:1 formboard in place (view only) and turn formboard mode on; returns doc"""
    T = _Tree(doc)
    T.s = annotation
    for mode in ("all", "labels", "none"):     # every text kept clear while placing; else the end labels only; else none
        T.textmode = mode
        try:
            root, shape, pos, paths = _layout(T)
            break
        except AssertionError as e:      # repair_labels turns the end labels that still overlap afterwards
            if mode == "none": raise
            print("formboard: layout keeping %s texts clear failed (%s); trying with fewer" % (mode, e))
            T = _Tree(doc); T.s = annotation
    R = T.R
    bundles = {b["id"]: b for b in doc.get("bundles", [])}
    # mated plugs that carry no bundle (bussed receptacle caps, the CAN-Lambda terminator plug) sit against their plug
    extra = {}
    for m in doc.get("mates", []) or []:
        for a, c in ((m["sourceId"], m["targetId"]), (m["targetId"], m["sourceId"])):
            if a in pos and c not in pos and c in T.el:
                par = next((p for p, b in T.adj.get(a, []) if b is not None), None)
                d = (pos[a][0] - pos[par][0], pos[a][1] - pos[par][1]) if par else (1, 0)
                L = math.hypot(*d) or 1
                extra[c] = (pos[a][0] + 45 * d[0] / L, pos[a][1] + 45 * d[1] / L)
                # face to face with its plug, turned or moved out only as far as its label needs to stay clear (Dan 2026-11-13)
                # (a cap has no bundle, so its label sits where the gate puts it: text_boxes, bundle vector 0; turned to
                # another side, layoutLabelPosition, before the cap moves further out)
                ce, hit = T.el[c], None
                was_side = ce.get("layoutLabelPosition")
                for dist in (45, 60, 75, 90, 120, 160, 200, 260):
                    for rot in (0, 30, -30, 60, -60, 90, -90):
                        u = _rot((d[0] / L, d[1] / L), rot)
                        q = (pos[a][0] + dist * u[0], pos[a][1] + dist * u[1])
                        for side in (was_side, "Left", "Right", "Top", "Bottom"):
                            if side is None: ce.pop("layoutLabelPosition", None)
                            else: ce["layoutLabelPosition"] = side
                            piece = Shape(); piece.nodes = [(q, c)]
                            piece.texts = T.node_texts(c, q, (0.0, 0.0))
                            if clash(piece, shape, dict(pos, **{c: q})) is None:
                                hit = (q, piece); break
                        if hit: break
                    if hit: break
                if not hit:
                    if was_side is None: ce.pop("layoutLabelPosition", None)
                    else: ce["layoutLabelPosition"] = was_side
                if hit:
                    extra[c] = hit[0]; shape.add(hit[1])
    allpos = dict(pos); allpos.update(extra)
    # board: A3 panels, landscape or portrait (fewer panels), the harness and every text on it centred on the grid (the app
    # centres it on 0, 0); the layout notes stacked above it all, top left, each clear of the next
    xs = [p[0] for p in allpos.values()] + [q[0] for v in paths.values() for q in v] + [x for poly, _ in shape.texts for x, _ in poly]
    ys = [p[1] for p in allpos.values()] + [q[1] for v in paths.values() for q in v] + [y for poly, _ in shape.texts for _, y in poly]
    m = MARGIN_MM / MM_PER_UNIT
    top, left = min(ys), min(xs)
    for n in reversed(doc.get("layoutNotes", []) or []):
        n["layoutPosition"] = {"x": 0.0, "y": 0.0}
        h = _pbb(note_box(n, annotation))[3]
        top -= 20 + h
        n["_at"] = (left, top)
        xs += [left, left + (n.get("width") or 150) * annotation]; ys += [top]
    w, h = (max(xs) - min(xs) + 2 * m) * MM_PER_UNIT, (max(ys) - min(ys) + 2 * m) * MM_PER_UNIT
    pl, ps = PANEL[panel]
    best = None
    for orient, (pw, ph) in (("Landscape", (pl, ps)), ("Portrait", (ps, pl))):
        cols, rows = max(1, math.ceil(w / pw)), max(1, math.ceil(h / ph))
        if best is None or cols * rows < best[0]: best = (cols * rows, orient, pw, ph, cols, rows)
    _, orient, pw, ph, cols, rows = best
    off = (-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2)
    P = lambda p: (p[0] + off[0], p[1] + off[1])
    for i, p in allpos.items():
        q = P(p); T.el[i]["layoutPosition"] = {"x": _r2(q[0] - HALF), "y": _r2(q[1] - HALF)}
    for bid, path in paths.items():
        b = bundles[bid]
        inner = [P(q) for q in path[1:-1]]
        if inner:
            b["layoutPoints"] = [{"id": "%s_p%d" % (bid, i), "layoutPosition": {"x": _r2(q[0] - HALF), "y": _r2(q[1] - HALF)}} for i, q in enumerate(inner)]
        else:
            b.pop("layoutPoints", None)
        b.pop("radius", None)
    # inline parts sit on their location node; anything else keeps its offset from the nearest node it was by
    for k in INLINE_KINDS:
        for e in doc.get(k, []):
            if not e.get("layoutPosition"): continue
            if e.get("locationId") in T.el:
                e["layoutPosition"] = dict(T.el[e["locationId"]]["layoutPosition"])
            else:
                c = _centre(e)
                near = min((i for i in allpos if i in T.old), key=lambda i: math.hypot(T.old[i][0] - c[0], T.old[i][1] - c[1]))
                q = P(allpos[near]); d = (c[0] - T.old[near][0], c[1] - T.old[near][1])
                e["layoutPosition"] = {"x": _r2(q[0] + d[0] - HALF), "y": _r2(q[1] + d[1] - HALF)}
    for n in doc.get("layoutNotes", []) or []:     # notes above the harness, top left
        q = P(n.pop("_at"))
        n["layoutPosition"] = {"x": _r2(q[0]), "y": _r2(q[1])}
    doc["formboard"] = {"panelSize": panel, "panelOrientation": orient,
                        "panelWidth": {"value": pw, "unit": "mm"}, "panelHeight": {"value": ph, "unit": "mm"},
                        "rows": rows, "columns": cols, "defaultCornerRadius": {"value": RADIUS_MM, "unit": "mm"},
                        "annotationScale": annotation}
    if label_overlaps(doc):
        repair_labels(doc)
    fit_board(doc, panel)
    return doc


SIDES = ("Left", "Right", "Top", "Bottom")


def repair_labels(doc, rounds=6):
    """turn the details of an end whose label still overlaps another text to the side (layoutLabelPosition) that clears it,
    never making the count worse: the app's own per-end label side (editing guide, terminals / connectors)"""
    el = {e["id"]: e for k in ("connectors", "terminals") for e in doc.get(k, [])}
    for _ in range(rounds):
        bad = label_overlaps(doc)
        if not bad: return
        moved = False
        for a, b in bad:
            for x in (a, b):
                w, o = x.split(" ", 1)
                if w != "label" or o not in el: continue
                e = el[o]
                was = e.get("layoutLabelPosition")
                now = len(label_overlaps(doc))
                best = (now, was)
                for side in SIDES:
                    e["layoutLabelPosition"] = side
                    n = len(label_overlaps(doc))
                    if n < best[0]: best = (n, side)
                if best[1] is None: e.pop("layoutLabelPosition", None)
                else: e["layoutLabelPosition"] = best[1]
                if best[1] != was: moved = True; break
            else:
                continue
            break
        if not moved: return


def fit_board(doc, panel="A3"):
    """the panel grid round everything drawn (parts, bundles, every text), harness centred on it (the app centres on 0, 0)"""
    m = 20 / MM_PER_UNIT      # 20 mm clear round the outermost text or part
    xs, ys = [], []
    for k in NODE_KINDS + INLINE_KINDS:
        for e in doc.get(k, []):
            if e.get("layoutPosition"): xs += [e["layoutPosition"]["x"], e["layoutPosition"]["x"] + 2 * HALF]; ys += [e["layoutPosition"]["y"], e["layoutPosition"]["y"] + 2 * HALF]
    for b in doc.get("bundles", []):
        for p in b.get("layoutPoints") or []: xs.append(p["layoutPosition"]["x"] + HALF); ys.append(p["layoutPosition"]["y"] + HALF)
    for _, poly, _ in text_boxes(doc):
        x0, y0, x1, y1 = _pbb(poly); xs += [x0, x1]; ys += [y0, y1]
    off = (-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2)
    mv = lambda p: {"x": _r2(p["x"] + off[0]), "y": _r2(p["y"] + off[1])}
    for k in NODE_KINDS + INLINE_KINDS:
        for e in doc.get(k, []):
            if e.get("layoutPosition"): e["layoutPosition"] = mv(e["layoutPosition"])
    for b in doc.get("bundles", []):
        for p in b.get("layoutPoints") or []: p["layoutPosition"] = mv(p["layoutPosition"])
    for n in doc.get("layoutNotes", []) or []: n["layoutPosition"] = mv(n["layoutPosition"])
    w, h = (max(xs) - min(xs) + 2 * m) * MM_PER_UNIT, (max(ys) - min(ys) + 2 * m) * MM_PER_UNIT
    pl, ps = PANEL[panel]
    best = None
    for orient, (pw, ph) in (("Landscape", (pl, ps)), ("Portrait", (ps, pl))):
        cols, rows = max(1, math.ceil(w / pw)), max(1, math.ceil(h / ph))
        if best is None or cols * rows < best[0]: best = (cols * rows, orient, pw, ph, cols, rows)
    _, orient, pw, ph, cols, rows = best
    doc["formboard"].update({"panelOrientation": orient, "panelWidth": {"value": pw, "unit": "mm"},
                             "panelHeight": {"value": ph, "unit": "mm"}, "rows": rows, "columns": cols})
    return doc


def board(doc):
    fb = doc["formboard"]
    return (fb["columns"] * _mm(fb["panelWidth"]), fb["rows"] * _mm(fb["panelHeight"]), fb["columns"] * fb["rows"], fb)


def check(doc, tol_mm=1.0):
    """the formboard gate: [] when every bundle is drawn at its set length (within tol_mm, and inside the app's own 0.5 mm
    so none is flagged), no bundle has a 0 mm / missing length, no two bundles cross or overlap, no bundle runs through a
    part, and every part is on the panel grid; else a list of problems"""
    bad = []
    fb = doc.get("formboard")
    if not fb: return ["formboard mode is off"]
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    sh = Shape()
    for b in doc.get("bundles", []):
        if not b.get("length") or _mm(b["length"]) <= 0:
            bad.append("%s: no set length (drawn yellow / black dashed)" % b["id"]); continue
        d, s = drawn_mm(doc, b, at), _mm(b["length"])
        if abs(d - s) >= min(tol_mm, 0.5): bad.append("%s: drawn %.2f mm, set %.2f mm" % (b["id"], d, s))
        pts = bundle_path(doc, b, at)
        sh.segs += [(pts[i], pts[i + 1], (b["sourceId"], b["targetId"]), b["id"]) for i in range(len(pts) - 1)]
    bps = {e["id"] for e in doc.get("branchPoints", [])}
    sh.nodes = [(p, n) for n, p in at.items() if n not in bps]
    for i, (p, q, e, b) in enumerate(sh.segs):     # every bundle against every other one and against every part
        one, rest = Shape(), Shape()
        one.segs = [(p, q, e, b)]
        rest.segs = [s for s in sh.segs[i + 1:] if s[3] != b]
        rest.nodes = sh.nodes
        c = clash(one, rest, at, clr=CLR * 0.5, gap=NODE_GAP * 0.5, r0=SHARED_R)
        if c: bad.append("clash: %s" % (c,))
    pts = sorted(sh.nodes)
    for i, (p, n) in enumerate(pts):          # two part symbols on (nearly) one spot
        for q, m in pts[i + 1:]:
            if q[0] - p[0] >= NODE_GAP * 0.5: break
            if math.hypot(q[0] - p[0], q[1] - p[1]) < NODE_GAP * 0.5: bad.append("clash: ('parts', %r, %r)" % (n, m))
    W, H = fb["columns"] * _mm(fb["panelWidth"]) / MM_PER_UNIT, fb["rows"] * _mm(fb["panelHeight"]) / MM_PER_UNIT
    for n, p in at.items():
        if not (-W / 2 <= p[0] <= W / 2 and -H / 2 <= p[1] <= H / 2): bad.append("%s is off the panel grid" % n)
    for o, poly, what in text_boxes(doc):      # every text on the panels too
        x0, y0, x1, y1 = _pbb(poly)
        if x0 < -W / 2 or y0 < -H / 2 or x1 > W / 2 or y1 > H / 2: bad.append("%s %s is off the panel grid" % (what, o))
    # Dan 2026-11-13: every label readable. The one exception: two end labels of one over-capacity fan (over_capacity: more
    # label rows than its stubs can ever hold clear), listed by cannot_fit() and reported, never silent
    let = set(cannot_fit(doc))
    bad += ["labels overlap: %s / %s" % ab for ab in label_overlaps(doc) if ab not in let]
    return bad


FAN_OF = {}     # while to_scale lays a document out: text owner -> its over-capacity fan (fan_owners)


def fan_owners(doc):
    """{owner: fan node} for the ends of every over_capacity() fan and their own stubs"""
    fan = {e: n for n, (_, _, ends) in over_capacity(doc).items() for e in ends}
    for b in doc.get("bundles", []):     # each end's own stub (its length label) belongs to the fan too
        for x in (b["sourceId"], b["targetId"]):
            if x in fan: fan[b["id"]] = fan[x]
    return fan


def cannot_fit(doc):
    """the label overlaps the gate lets through: both texts belong to one over_capacity() fan (its ends, their stubs)"""
    fan = fan_owners(doc)
    if not fan: return []
    out = []
    for a, b in label_overlaps(doc):
        oa, ob = a.split(" ")[-1], b.split(" ")[-1]
        if fan.get(oa) and fan.get(oa) == fan.get(ob): out.append((a, b))
    return out


# ------------------------------------------------------------------ the regular layout view (Dan 2026-11-15)
# What every generator draws since 2026-11-15 (Dan: "I don't want them in the formboard layout. I want them in the regular
# layout view with straight runs instead of the snaked runs"; replaces A25 a): formboard mode OFF, no panel grid, the tree
# laid out the way the generators did before the 1:1 formboards: straight orthogonal bundles on the 30 grid, each branch
# at 90 degrees in the direction the generator gave it (front of the car RIGHT, driver side UP), drawn length NOT to
# scale (every bundle keeps its set length, the master's). The ends of a node are combed: one shared spine out of the
# node, each end on its own straight run off it, in the generator's order, the rows far enough apart and the runs long
# enough that every text (end label, part bar, length label, ghost tag) stands clear at full size (annotation scale 1,
# the calibrated sizes of TXT). A mated half (bussed receptacle cap, RADLOK partner, terminator plug) sits nose to nose
# beyond its plug. View only: no wire, pin, length or part changes.
GRID = 30
AXES = ((1, 0), (0, -1), (0, 1), (-1, 0))     # R, U, D, L (screen: y grows down)
R_LEAD = 60       # units: a comb's lead out of its node before the spine turns
R_PITCH = 60      # units: least pitch of a comb's rows (the generators' comb pitch)
R_FIRST = 120     # units: the first row of a comb whose spine runs straight on from its node
R_MINL = 150      # units: shortest drawn branch (the generators' MINL)
R_GAP = 24.0      # units: clear space between two bundles / parts that do not belong together
R_TGAP = 4.0      # units: clear space round a text
R_MATE = 60       # units: mated halves, centre to centre
R_LW = 2.0        # units: half the width a bundle line is kept clear at


def _mv(r, o): return (r[0] + o[0], r[1] + o[1], r[2] + o[0], r[3] + o[1]) + r[4:]

def _rgap(a, b):
    if a[5] == "xline" or b[5] == "xline": return 6.0 if a[5] == "text" or b[5] == "text" else 10.0
    return R_TGAP if a[5] == "text" or b[5] == "text" else R_GAP

def _rskip(a, b):
    """two drawn things that belong together: one owner, two bundle lines (or comb spines) out of one node, a bundle and
    the part it ends on. An xline (a piece of an anchored bundle of the car view, kept off its own end nodes) is kept clear
    of everything but other xlines and its own end parts"""
    if a[4] == b[4]: return True
    if a[5] == "xline" or b[5] == "xline":
        if a[5] == b[5]: return True
        return (b[5] == "node" and b[4] in a[6]) or (a[5] == "node" and a[4] in b[6])
    la, lb = a[5] in ("line", "spine"), b[5] in ("line", "spine")
    if la and lb and a[6] & b[6]: return True
    if b[5] == "node" and b[4] in a[6]: return True      # a bundle (or its own tag) and the part it ends on
    if a[5] == "node" and a[4] in b[6]: return True
    return False

def _rhit(a, b):
    if _rskip(a, b): return False
    g = _rgap(a, b)
    return a[0] - g < b[2] and b[0] - g < a[2] and a[1] - g < b[3] and b[1] - g < a[3]


def regular(doc, frame=None, layout_nodes=None):
    """redraw doc's layout view the regular way in place (view only): formboard mode off, ends combed with every text clear;
    returns doc. With frame (build_drawings.car_frame of the layout tree) and layout_nodes (its nodes; a branch point
    bp_<node> is that node): the car from above (Dan 2026-11-16), every branch point on its layout-editor spot at one
    uniform scale for the file (front RIGHT, driver side UP), each bundle a straight run on its editor route; only the ends
    and the nodes too close to their neighbour to show apart are combed round their spot. Without frame: the tree drawn as
    straight orthogonal bundles on the grid (the self-tests' toy documents)"""
    if frame is None: return _regular_once(doc)
    return _car_regular(doc, frame, layout_nodes)


def _regular_once(doc, car=None):
    doc.pop("formboard", None)
    T = _Tree(doc)
    T.s, T.textmode = 1.0, "all"
    for m in doc.get("mates", []) or []:      # a mated half with no bundle of its own (a cap) hangs on its plug
        for a, c in ((m["sourceId"], m["targetId"]), (m["targetId"], m["sourceId"])):
            if a in T.adj and c not in T.adj and c in T.el:
                T.adj.setdefault(a, []).append((c, None)); T.adj.setdefault(c, []).append((a, None)); break
    left, roots, parent, kids, order = set(T.adj), [], {}, {}, []
    while left:
        cand = sorted(n for n in left if T.old.get(n) == (HALF, HALF) and n in T.bps) or sorted(left, key=lambda n: (-len(T.adj[n]), n))
        root = cand[0]; roots.append(root)
        parent[root] = None; part = [root]
        for n in part:
            for c, b in T.adj[n]:
                if c in parent:
                    assert parent[n] and parent[n][0] == c, "the layout is not a tree at %s" % c
                    continue
                parent[c] = (n, b); kids.setdefault(n, []).append((c, b)); part.append(c)
        order += part; left -= set(part)
    size = {}
    for n in reversed(order): size[n] = 1 + sum(size[c] for c, _ in kids.get(n, []))
    # the car view: a spotted branch point far enough from its nearest anchored ancestor to show apart is anchored on its
    # spot (car mm times the file's scale); the rest (ends, splices, box breakouts, a tap on its device) are combed round it
    anch, SPOT, EXT = set(), {}, {}
    if car:
        kx = car["k"]
        SPOT = {n: (car["spot"][n][0] * kx, car["spot"][n][1] * kx) for n in car["spot"]}
        anc = {}
        for n in order:
            p = parent[n]
            a = anc.get(p[0]) if p else None
            if p is None and n not in SPOT:      # a piece whose root has no spot: on its first spotted node's spot
                rest = order[order.index(n) + 1:]
                nxt = next((i for i, m in enumerate(rest) if parent[m] is None), len(rest))
                near = next((m for m in rest[:nxt] if m in SPOT), None)
                SPOT[n] = SPOT[near] if near else (0.0, 0.0)
            if n in SPOT and (p is None or (p[1] is not None and (a is None or math.hypot(SPOT[n][0] - SPOT[a][0], SPOT[n][1] - SPOT[a][1]) >= car["dmin"]))):
                anch.add(n); anc[n] = n
            else:
                anc[n] = a
        # a cluster = an anchored node and the nodes combed round it. Its anchor moves to the spotted member with the most
        # runs to other clusters (a junction whose runs fan out in the car stays on its spot; the box breakouts beside it
        # are combed instead), and the cluster's own tree is re-rooted there
        cl = dict(anc)
        XE = [(parent[n][0], n, parent[n][1]) for n in order if parent[n] and parent[n][1] is not None and cl[parent[n][0]] != cl[n]]
        nx = collections.Counter(x for u, v, _ in XE for x in (u, v))
        members = {}
        for n in order: members.setdefault(cl[n], []).append(n)
        newp, newk, anch2 = {}, {}, set()
        for c0, mem in members.items():
            A = max((m for m in mem if m in SPOT), key=lambda m: (nx[m], m == c0, -mem.index(m)))
            anch2.add(A)
            ms = set(mem)
            newp[A] = None; todo = [A]
            for x in todo:
                for y, b in T.adj.get(x, []):
                    if y in ms and y not in newp:
                        newp[y] = (x, b); newk.setdefault(x, []).append((y, b)); todo.append(y)
            for m in mem: cl[m] = A
        assert set(newp) == set(parent), "car view: a cluster is not connected"
        parent.clear(); parent.update(newp); kids.clear(); kids.update(newk)
        o2 = []
        for c0 in members:      # each cluster's members parent first
            A = next(x for x in members[c0] if newp[x] is None)
            seq = [A]
            for x in seq: seq += [y for y, _ in newk.get(x, [])]
            o2 += seq
        order = o2
        anch = anch2
        size.clear()
        for n in reversed(order): size[n] = 1 + sum(size[c] for c, _ in kids.get(n, []))
        def _cv(a, b):
            d = (b[0] - a[0], b[1] - a[1]); L = math.hypot(*d)
            return (d[0] / L, d[1] / L) if L > 1e-6 else None
        for u, v, b in XE:      # the directions the runs between clusters leave their two nodes (car, first leg of the route)
            mid = car["via"](u, v, b)
            for x, q0, q1 in ((u, SPOT[u], mid[0] if mid else SPOT[v]), (v, SPOT[v], mid[-1] if mid else SPOT[u])):
                w = _cv(q0, q1)
                if w: EXT.setdefault(x, []).append(w)
        car["anch"], car["cl"], car["XE"] = anch, cl, XE
        car["xb"] = {b["id"]: (u, v, b) for u, v, b in XE}
    def clear_of(n, d):      # degrees between axis d and the nearest anchored bundle leaving n
        return min([math.degrees(math.acos(max(-1.0, min(1.0, d[0] * v[0] + d[1] * v[1])))) for v in EXT.get(n, [])] + [180.0])
    NO = frozenset()
    inl = {}      # spot -> the inline parts that sit on it (one under the other, R_INLINE apart, each with its texts above it)
    for k in INLINE_KINDS:
        for e in doc.get(k, []):
            if e.get("layoutPosition") and e.get("locationId") in T.el: inl.setdefault(e["locationId"], []).append(e)

    def label(n, v, side):
        e = T.el[n]
        e2 = {k: x for k, x in e.items() if k != "layoutLabelPosition"}
        if side: e2["layoutLabelPosition"] = side
        wl, ws = end_text_size(e2, doc, 1.0, T.shown.get(n))
        mt = n in T.mated
        return end_box((0.0, 0.0), detail_side(v, mt, side), wl, ws, 1.0, e2, v, mt, REG_TOP_W)

    def btexts(b, n, path):
        p = path if b["sourceId"] == n else path[::-1]
        kd = []
        qs = bundle_texts(b, p, 1.0, (b["sourceId"] in T.bps, b["targetId"] in T.bps), T.wcount.get(b["id"], 1), board=False, kinds=kd)
        return [_pbb(q) + (b["id"] + ("#tag" if k == "tag" else ""), "text", frozenset((b["sourceId"], b["targetId"]))) for q, k in zip(qs, kd)]

    memo = {}
    EXTRA, CUR = [], [None, 0]    # the car view: what is already drawn round the anchored node CUR being laid (its frame)
    sub_of = {}
    for n in reversed(order): sub_of[n] = frozenset([n]).union(*[sub_of[c] for c, _ in kids.get(n, [])])
    def lay(n, din, side=None):
        f = (car or {}).get("force") or {}
        fz = frozenset((k_, v) for k_, v in f.items() if (k_[0] if isinstance(k_, tuple) else k_) in sub_of.get(n, ()))
        key = (n, din, side, fz, n == CUR[0] and (CUR[0], CUR[1]))
        if key not in memo: memo[key] = _lay(n, din, side)
        return memo[key]

    def put(n, c, b, d, minl, allr):
        """c's piece on the straight bundle b from n along d: the shortest drawn length (grid, >= minl) at which the piece,
        the bundle and its texts are clear of allr; (length, rects, positions, paths, sides) or None"""
        sub, spos, spaths, ssides = lay(c, d)
        horiz = d[1] == 0
        sgn = d[0] if horiz else d[1]
        def tp(r):
            t0, t1, p0, p1 = (r[0], r[2], r[1], r[3]) if horiz else (r[1], r[3], r[0], r[2])
            return (t0, t1, p0, p1) if sgn > 0 else (-t1, -t0, p0, p1)
        E = [(tp(r), r) for r in allr]
        forb = []
        for a in sub:
            ta = tp(a)
            for tb, r in E:
                if _rskip(a, r): continue
                g = _rgap(a, r)
                if ta[2] - g < tb[3] and tb[2] - g < ta[3]: forb.append((tb[0] - g - ta[1], tb[1] + g - ta[0]))
        if b is not None:
            probe = (0, 0, 0, 0, b["id"], "line", frozenset((n, c)))
            for tb, r in E:
                if _rskip(probe, r): continue
                g = _rgap(probe, r)
                if -R_LW - g < tb[3] and tb[2] - g < R_LW and tb[1] + g > 0:
                    forb.append((tb[0] - g, 1e9))
                    if DEBUG: print("put %s -> %s along %s: the line is blocked from %d by %r" % (n, c, d, tb[0] - g, r))
        ln = minl
        while True:
            moved = True
            while moved:
                moved = False
                for lo, hi in forb:
                    if lo < ln < hi:
                        if hi >= 1e9: return None
                        ln = int(math.ceil(hi / GRID)) * GRID; moved = True
            if car and ln > CAR_PUT_MAX: return None
            o = (d[0] * ln, d[1] * ln)
            if b is None: tx = []; break
            tx = btexts(b, n, [(0, 0), o])
            if not any(_rhit(t, r) for t in tx for r in allr) and not any(_rhit(t, _mv(r, o)) for t in tx for r in sub) \
               and not any(_rhit(t, z) for t in tx for z in tx if t is not z): break
            ln += GRID
            if ln > (CAR_PUT_MAX if car else 90000): return None
        out = [_mv(r, o) for r in sub] + tx
        paths = {k: [(q[0] + o[0], q[1] + o[1]) for q in v] for k, v in spaths.items()}
        if b is not None:
            out.append((min(0, o[0]) - R_LW, min(0, o[1]) - R_LW, max(0, o[0]) + R_LW, max(0, o[1]) + R_LW, b["id"], "line", frozenset((n, c))))
            paths[b["id"]] = [(0, 0), o] if b["sourceId"] == n else [o, (0, 0)]
        return ln, out, {k: (v[0] + o[0], v[1] + o[1]) for k, v in spos.items()}, paths, ssides

    def comb(n, rows, cd):
        """n's ends as a comb along cd: one spine out of n, each end on its own straight run off it (a run is horizontal, so
        its end's label reads on beyond the part), rows in the generator's order; (rects, positions, paths, sides)"""
        horiz = cd[1] == 0
        pf = PREFER.get(n)
        sx = cd[0] if horiz else (-1 if pf and pf[0] < 0 else 1)
        if not horiz and car and (n, "rows") in car["force"]: sx = car["force"][(n, "rows")]     # the car view: rows turned
        old = T.old
        cross = (lambda c: old[c][1]) if horiz else (lambda c: cd[1] * old[c][1])
        rs = sorted(rows, key=lambda cb: (cross(cb[0]), sx * old[cb[0]][0], cb[0]))
        k = len(rs)
        # the generator's wider gap between two comb groups (CFG comb_group) is kept
        gaps = [0] + [R_PITCH + max(0, min(180, int(round((cross(q[0]) - cross(p[0]) - 60) / 30.0)) * GRID)) for p, q in zip(rs, rs[1:])]
        gaps0 = list(gaps)
        lw = max(len_label_w(b) for _, b in rs)
        lead = R_LEAD if horiz else 0
        F = 90
        for _ in range(900):
            cum = [sum(gaps[:i + 1]) for i in range(k)]
            if horiz:
                mid = int(round(cum[-1] / 2.0 / GRID)) * GRID
                ys = [c_ - mid for c_ in cum]
            else:
                ys = [cd[1] * (R_FIRST + c_) for c_ in cum]
            if k > 1 or not horiz:      # each row's length label on its own run, clear of the spine
                F = max(F, int(math.ceil((lead + max(abs(y) for y in ys) + lw + 16) / GRID)) * GRID)
            acc, built, redo = [], [], False
            for i, (c, b) in enumerate(rs):
                y = ys[i]
                if horiz:
                    part = (sx * (R_LEAD + F), y)
                    path = [(0, 0)] + ([(sx * R_LEAD, 0), (sx * R_LEAD, y)] if y else []) + [part]
                else:
                    part = (sx * F, y)
                    path = [(0, 0), (0, y), part]
                q0 = path[-2]
                own = btexts(b, n, path)
                tag_hit = next(((a, z) for a in own for z in own if a is not z and _rhit(a, z)), None)     # its tag on its own length label
                own.append((min(q0[0], part[0]) - R_LW, y - R_LW, max(q0[0], part[0]) + R_LW, y + R_LW, b["id"], "line", frozenset((n, c))))
                # a mated plug's label below it, its other half's above, so the two sit nose to nose: the row moves down
                # for that (up to 180) before another label side is tried
                opts, more = [None], []
                if c not in T.bps and c in T.mated:
                    opts, more = ["Bottom"], ["Top", None, "Right" if sx > 0 else "Left"]
                    if gaps[i] - gaps0[i] >= 180: opts, more = opts + more, []
                got, intra_ok = None, False
                for sd in opts + more:
                    if sd in more and intra_ok: break       # Bottom fits its own row: let the row move down first
                    sub, spos, spaths, ssides = lay(c, (sx, 0), sd)
                    subm = [_mv(r, part) for r in sub]
                    why = tag_hit or next(((a, s) for a in own for s in subm if _rhit(a, s)), None)
                    if why: continue
                    intra_ok = True
                    why = next(((a, r) for a in own + subm for r in acc if _rhit(a, r)), None)
                    if why: continue
                    got = (subm, spos, spaths, ssides); break
                if got is None:
                    if intra_ok and i: gaps[i] += GRID
                    else: F += GRID
                    redo = True; break
                acc += own + got[0]
                built.append((c, b, part, path, got))
            if redo: continue
            sp, me = [], frozenset((n,))
            if horiz and (k > 1 or ys[0]):
                x1 = sx * R_LEAD
                sp = [(min(0, x1) - R_LW, -R_LW, max(0, x1) + R_LW, R_LW, "comb:" + n, "spine", me),
                      (x1 - R_LW, min(ys + [0]) - R_LW, x1 + R_LW, max(ys + [0]) + R_LW, "comb:" + n, "spine", me)]
            elif not horiz:
                sp = [(-R_LW, min(ys + [0]) - R_LW, R_LW, max(ys + [0]) + R_LW, "comb:" + n, "spine", me)]
            sp.append((-GRID, -GRID, GRID, GRID, "comb:" + n, "spine", me))     # round n itself, where its other bundles leave
            if any(_rhit(a, s) for s in sp for a in acc if a[5] == "text"): F += GRID; continue
            sp.pop()
            pos, paths, sides = {}, {}, {}
            for c, b, part, path, (subm, spos, spaths, ssides) in built:
                pos.update({m: (q[0] + part[0], q[1] + part[1]) for m, q in spos.items()})
                paths.update({m: [(q[0] + part[0], q[1] + part[1]) for q in v] for m, v in spaths.items()})
                paths[b["id"]] = path if b["sourceId"] == n else path[::-1]
                sides.update(ssides)
            return sp + acc, pos, paths, sides
        raise AssertionError("no clear comb for the ends at %s (last: %s, run %d, %r)" % (n, c, F, why))

    def _lay(n, din, side):
        """n's piece of the tree with n at (0, 0), reached along din: (rects, node positions, bundle paths, label sides)"""
        rects, pos, paths, sides = [], {n: (0, 0)}, {}, {}
        ch = [(c, b) for c, b in kids.get(n, []) if c not in anch]      # an anchored child is drawn from its own spot
        back = (-din[0], -din[1]) if din else None
        rows = [(c, b) for c, b in ch if b is not None and (c not in T.bps or (not kids.get(c) and c not in EXT))]
        rowset = {c for c, _ in rows}
        branches = [(c, b) for c, b in ch if b is not None and c not in rowset]
        mates_ = [(c, b) for c, b in ch if b is None]
        pf = PREFER.get(n)
        pf = (int(pf[0]), int(pf[1])) if pf else None
        def assign(first):
            """a direction for each branch (the generator's, the nearest free one) and for the comb of n's ends; first: the
            comb takes that direction before the branches choose"""
            used = [back] if back else []
            if mates_: used.append(din or (1, 0))          # its mated half sits straight on
            if first: used.append(first)
            asg = {}
            # the car view: an axis within 45 degrees of an anchored bundle out of n is taken only when nothing else is free
            def frees():
                f = [d for d in AXES if d not in used]
                return [d for d in f if clear_of(n, d) >= 45] or f
            force = (car or {}).get("force", {})
            for c, b in sorted(branches, key=lambda cb: (-size[cb[0]], cb[0])):
                u0 = PREFER.get(c) or (din if (n not in T.bps and din) else T.old_dir(n, c, b))
                if car and c in SPOT and n in SPOT and not PREFER.get(c):      # towards its own spot in the car
                    dv = (SPOT[c][0] - SPOT[n][0], SPOT[c][1] - SPOT[n][1])
                    if math.hypot(*dv) > 1e-6: u0 = dv
                if car and (n, c) in force and force[(n, c)] in frees(): u0 = force[(n, c)]
                free = frees()
                assert free, "more branches than directions at %s" % n
                asg[c] = max(free, key=lambda d: d[0] * u0[0] + d[1] * u0[1]); used.append(asg[c])
            cd = first
            if rows and not cd:
                free = frees()
                assert free, "no free side for the ends at %s" % n
                upright = [d for d in ((0, -1), (0, 1)) if d in free]
                if car and force.get(n) in free: cd = force[n]
                elif pf in free: cd = pf
                elif pf and upright: cd = upright[0]          # an upright spine: its rows still run to the box's side (A35)
                elif din in free: cd = din
                elif car and EXT.get(n): cd = max(free, key=lambda d: (clear_of(n, d), -AXES.index(d)))
                else: cd = next(d for d in ((0, -1), (0, 1), (1, 0), (-1, 0)) if d in free)
                used.append(cd)
            return used, asg, cd
        used, asg, cd = assign(None)
        if rows and pf and cd == (-pf[0], -pf[1]) and pf != back and not mates_ and len(branches) < 3:
            used, asg, cd = assign(pf)        # a box's ends on the box's own side (A35), before its branches choose
        if n not in T.bps:
            rects.append((-HALF, -HALF, HALF, HALF, n, "node", NO))
            v = [0.0, 0.0]
            if back and parent[n] and parent[n][1] is not None: v = [back[0] * 100.0, back[1] * 100.0]
            for d in list(asg.values()) + ([cd] if cd else []):
                v[0] += d[0] * 100.0; v[1] += d[1] * 100.0
            if back and v == [0.0, 0.0]: v = [back[0] * 100.0, back[1] * 100.0]      # a cap: towards its other half
            box = label(n, (v[0], v[1]), side)
            if box: rects.append(_pbb(box) + (n, "text", NO))
            if side: sides[n] = side
        elif not ch:
            rects.append((-HALF, -HALF, HALF, HALF, n, "node", NO))     # an inline part's spot (splice, diode, resistor)
        for j, e in enumerate(inl.get(n, [])):
            if j: rects.append((-HALF, R_INLINE * j - HALF, HALF, R_INLINE * j + HALF, n, "node", NO))
            box = inline_box(e, doc, (0.0, float(R_INLINE * j)))
            if box: rects.append(_pbb(box) + (e["id"], "text", frozenset((n,))))
        def lane(d):      # the straight way out of n along d, kept free
            e = (d[0] * 1e6, d[1] * 1e6)
            return (min(0, e[0]) - R_LW, min(0, e[1]) - R_LW, max(0, e[0]) + R_LW, max(0, e[1]) + R_LW, "(lane)", "line", frozenset((n,)))
        ray = [lane(back)] if back else []      # the way in: nothing of this piece grows back over the parent's bundle
        def take(got):
            ln, out, ps, pa, sd = got
            rects.extend(out); pos.update(ps); paths.update(pa); sides.update(sd)
        if rows: take((0,) + comb(n, rows, cd))
        for c, b in mates_:
            got = put(n, c, None, din or (1, 0), R_MATE, rects + ray + (EXTRA if n == CUR[0] else []))
            assert got, "no clear place for the mated half %s of %s" % (c, n)
            take(got)
        todo = sorted(branches, key=lambda cb: (size[cb[0]], cb[0]))
        for j, (c, b) in enumerate(todo):
            got = None
            later = [lane(asg[x]) for x, _ in todo[j + 1:]]     # the ways out of the branches still to come stay free
            for d in [asg[c]] + [d for d in AXES if d not in used]:
                got = put(n, c, b, d, R_MINL, rects + ray + later + (EXTRA if n == CUR[0] else []))
                if got:
                    if d != asg[c]: used.append(d)
                    break
            assert got, "no clear place for the branch %s -> %s" % (n, c)
            take(got)
        return rects, pos, paths, sides

    RECTS, POS, PATHS, SIDES = [], {}, {}, {}
    if car:      # each cluster's piece round its anchor's spot, then the runs between clusters straight on their editor routes
        owner = {}
        force = car["force"]
        XE = car["XE"]
        xe_at = {}
        for u, v, b in XE:
            xe_at.setdefault(u, []).append((u, v, b)); xe_at.setdefault(v, []).append((u, v, b))
        def g30(q): return (int(round(q[0] / GRID)) * GRID, int(round(q[1] / GRID)) * GRID)
        def where(x, at=None):      # a node's drawn spot: placed, or this attempt's, or its own spot (an anchor: on the grid)
            if at and x in at: return at[x]
            if x in POS: return POS[x]
            return g30(SPOT[x]) if x in anch else SPOT[x]
        def xpath(u, v, b, at=None):
            return [where(u, at)] + list(car["via"](u, v, b)) + [where(v, at)]
        def xl_rects(u, v, b, at=None):
            """a run between two clusters as a chain of small boxes (off its two end nodes) and its length label"""
            pts = xpath(u, v, b, at)
            ends, out = frozenset((u, v)), []
            for a0, a1 in zip(pts, pts[1:]):
                L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
                for i in range(int(L // 12) + 1):
                    q = (a0[0] + (a1[0] - a0[0]) * i * 12 / (L or 1), a0[1] + (a1[1] - a0[1]) * i * 12 / (L or 1))
                    if min(math.hypot(q[0] - pts[0][0], q[1] - pts[0][1]), math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1])) < 40: continue
                    out.append((q[0] - R_LW, q[1] - R_LW, q[0] + R_LW, q[1] + R_LW, b["id"], "xline", ends))
            if b["sourceId"] != u: pts = pts[::-1]
            return out + btexts(b, b["sourceId"], pts)
        def near(rs, box, g=60):
            return [x for x in rs if x[0] < box[2] + g and box[0] - g < x[2] and x[1] < box[3] + g and box[1] - g < x[3]]
        def index(rs, c=240):
            g = {}
            for x in rs:
                for i in range(int(x[0] // c), int(x[2] // c) + 1):
                    for j in range(int(x[1] // c), int(x[3] // c) + 1): g.setdefault((i, j), []).append(x)
            return g, c
        def hits(rr, others):
            if not rr: return 0
            if isinstance(others, tuple):      # an index: each box against what lies in its cells
                g, c = others
                tot = 0
                for a in rr:
                    seen = set()
                    for i in range(int((a[0] - 30) // c), int((a[2] + 30) // c) + 1):
                        for j in range(int((a[1] - 30) // c), int((a[3] + 30) // c) + 1):
                            for x in g.get((i, j), ()):
                                if id(x) not in seen:
                                    seen.add(id(x))
                                    if _rhit(a, x): tot += 1
                return tot
            box = (min(x[0] for x in rr), min(x[1] for x in rr), max(x[2] for x in rr), max(x[3] for x in rr))
            cand = near(others, box)
            return sum(1 for a in rr for x in cand if _rhit(a, x))
        def piece_nodes(p):      # the nodes of a piece that comb ends or carry a branch
            return [m for m in p if kids.get(m)]
        PIECE, H0 = {}, {}
        sched = [n for n in order if n in anch]
        # every piece in turn, then once more each piece that still hits something, against everything drawn by then
        for n in sched + [None] + sched:
            if n is None:
                CUR[1] += 1; continue
            if n in H0 and not H0[n]: continue
            o = g30(SPOT[n])
            CUR[0] = n
            mem = {m for m in order if car["cl"][m] == n}
            # what is drawn already, and every run between clusters that does not touch this piece (from where its ends are)
            XL = [x for u, v, b in XE if u not in mem and v not in mem for x in xl_rects(u, v, b)]
            world = [x for m, rs in PIECE.items() if m != n for x in rs] + XL
            WI = index(world)
            EXTRA[:] = [_mv(x, (-o[0], -o[1])) for x in near(world, (o[0] - 3000, o[1] - 3000, o[0] + 3000, o[1] + 3000))]
            mine_x = [(u, v, b) for u, v, b in XE if u in mem or v in mem]
            def attempt():
                try: got = lay(n, None)
                except AssertionError: return None, 10 ** 9
                mine = [_mv(x, o) for x in got[0]]
                at = {k_: (q[0] + o[0], q[1] + o[1]) for k_, q in got[1].items()}
                # the runs that leave this piece, from where its nodes now sit
                fut = [x for u, v, b in mine_x for x in xl_rects(u, v, b, at)]
                return got, hits(mine, WI) + hits(fut, WI) + hits(fut, mine)
            got, h = attempt()
            if h:      # turn combs and local branches (a small beam search over the sides) while anything is hit
                keys = [key for m in sorted(mem) if kids.get(m) for key in
                        [m, (m, "rows")] + [(m, c) for c, _ in kids.get(m, []) if kids.get(c) or c in EXT]]
                vals = lambda key: (1, -1) if isinstance(key, tuple) and key[1] == "rows" else AXES
                base = {key: force.get(key) for key in keys}
                def with_(ch):
                    for key, d in ch.items(): force[key] = d
                    try: return attempt()
                    finally:
                        for key in ch:
                            if base[key] is None: force.pop(key, None)
                            else: force[key] = base[key]
                beam, top = [(h, {})], (h, {})
                for _depth in range(CAR_BEAM[1]):
                    new, seen = [], set()
                    for hb, ch in beam:
                        for key in keys:
                            for d in vals(key):
                                if ch.get(key, base[key]) == d: continue
                                ch2 = dict(ch); ch2[key] = d
                                sig = frozenset(ch2.items())
                                if sig in seen: continue
                                seen.add(sig)
                                g2, h2 = with_(ch2)
                                if g2 is None: continue
                                new.append((h2, ch2))
                                if h2 < top[0]: top = (h2, ch2)
                                if h2 == 0: break
                            if top[0] == 0: break
                        if top[0] == 0: break
                    if top[0] == 0 or not new: break
                    new.sort(key=lambda t: (t[0], len(t[1])))
                    beam = new[:CAR_BEAM[0]]
                if DEBUG: print("  beam %s: keys %s, %d -> %s" % (n, keys, h, top))
                if top[0] < h:
                    for key, d in top[1].items(): force[key] = d
                    got, h = attempt()
            if got is None:      # nothing clear of what is drawn round it: laid on its own (the final gate decides)
                CUR[0] = None
                got, h = attempt()
            assert got is not None, "no clear piece at %s" % n
            if DEBUG and h:
                mine = [_mv(x, o) for x in got[0]]
                at = {k_: (q[0] + o[0], q[1] + o[1]) for k_, q in got[1].items()}
                fut = [x for u, v, b in mine_x for x in xl_rects(u, v, b, at)]
                hp = collections.Counter((a[4], a[5], x[4], x[5]) for a in mine for x in near(world, a, 30) if _rhit(a, x))
                hp.update((a[4], a[5], x[4], x[5]) for a in fut for x in near(world + mine, a, 30) if _rhit(a, x))
                print("  piece %s: %d hits %s" % (n, h, hp.most_common(8)))
            r, p, pa, sd = got
            PIECE[n] = [_mv(x, o) for x in r]; H0[n] = h
            for k_ in p: owner[k_] = n
            for x in r: owner.setdefault(x[4], n)
            POS.update({k_: (v[0] + o[0], v[1] + o[1]) for k_, v in p.items()})
            PATHS.update({k_: [(q[0] + o[0], q[1] + o[1]) for q in v] for k_, v in pa.items()})
            for k_ in pa: owner.setdefault(k_, n)
            SIDES.update(sd)
        RECTS = [x for rs in PIECE.values() for x in rs]
        for u, v, b in XE:
            mid = [g30(q) for q in car["via"](u, v, b)]
            path = [POS[u]] + mid + [POS[v]]
            PATHS[b["id"]] = path if b["sourceId"] == u else path[::-1]
            owner[b["id"]] = car["cl"][v]
        car["owner"] = owner
        roots = []
    for root in roots:      # the main tree, then any separate piece (a ground strap) below it
        r, p, pa, sd = lay(root, None)
        o = (0, 0)
        if RECTS:
            a0, a3 = min(x[0] for x in RECTS), max(x[3] for x in RECTS)
            b0, b1 = min([x[0] for x in r] + [0]), min([x[1] for x in r] + [0])
            o = (int(math.floor((a0 - b0) / GRID)) * GRID, int(math.ceil((a3 + 150 - b1) / GRID)) * GRID)
        RECTS += [_mv(x, o) for x in r]
        POS.update({k: (v[0] + o[0], v[1] + o[1]) for k, v in p.items()})
        PATHS.update({k: [(q[0] + o[0], q[1] + o[1]) for q in v] for k, v in pa.items()})
        SIDES.update(sd)
    stray = [e["id"] for k in ("connectors", "terminals") for e in doc.get(k, []) if e.get("layoutPosition") and e["id"] not in POS]
    assert not stray, "parts that are not on the layout tree: %r" % stray
    old_lp = {i: (e["layoutPosition"]["x"], e["layoutPosition"]["y"]) for i, e in T.el.items() if e.get("layoutPosition")}
    for i, p in POS.items(): T.el[i]["layoutPosition"] = {"x": int(p[0]), "y": int(p[1])}
    bund = {b["id"]: b for b in doc.get("bundles", [])}
    for b in bund.values():
        b.pop("layoutPoints", None); b.pop("radius", None)
    for bid, path in PATHS.items():
        if len(path) > 2:
            bund[bid]["layoutPoints"] = [{"id": "%s_p%d" % (bid, i), "layoutPosition": {"x": int(q[0]), "y": int(q[1])}} for i, q in enumerate(path[1:-1])]
    for k in ("connectors", "terminals"):
        for e in doc.get(k, []):
            e.pop("layoutLabelPosition", None)
            if SIDES.get(e["id"]): e["layoutLabelPosition"] = SIDES[e["id"]]
    for k in INLINE_KINDS:      # inline parts sit on their location node; anything else keeps its offset from the node it was by
        for e in doc.get(k, []):
            if not e.get("layoutPosition"): continue
            if e.get("locationId") in T.el:
                at_ = T.el[e["locationId"]]["layoutPosition"]
                e["layoutPosition"] = {"x": at_["x"], "y": at_["y"] + R_INLINE * inl[e["locationId"]].index(e)}
            else:
                x, y = e["layoutPosition"]["x"], e["layoutPosition"]["y"]
                near = min((i for i in POS if i in old_lp), key=lambda i: math.hypot(old_lp[i][0] - x, old_lp[i][1] - y))
                e["layoutPosition"] = {"x": int(POS[near][0] + x - old_lp[near][0]), "y": int(POS[near][1] + y - old_lp[near][1])}
    top, leftx = min(x[1] for x in RECTS), int(math.floor(min(x[0] for x in RECTS) / GRID)) * GRID
    for nt in reversed(doc.get("layoutNotes", []) or []):     # the layout notes stacked above it all, top left
        nt["layoutPosition"] = {"x": 0, "y": 0}
        top = int(math.floor((top - 30 - _pbb(note_box(nt, 1.0))[3]) / GRID)) * GRID
        nt["layoutPosition"] = {"x": leftx, "y": top}
    if label_overlaps(doc): repair_labels(doc)
    return doc


CAR_K = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)   # layout units per car mm tried, smallest first
CAR_TRIES = 6                 # whole-file tries at one scale (each turns the combs named in the last one's problems)
CAR_END_MM = 120.0            # a route bend nearer a node than this is left out (the run goes straight in)
CAR_SIMPLIFY_MM = 40.0        # a route bend nearer than this to the straight line past it is left out (straight runs)
CAR_BEAM = (10, 4)            # beam width and depth of the comb / branch side search per piece
CAR_PUT_MAX = 1200            # units: the longest a combed branch is drawn in the car view (else it tries another side)
CAR_ON_SPOT = 0.8             # share of the spotted nodes drawn on their spots before a scale is taken
CAR_STATS = {}                # the last car layout: {"k": scale, "anchored": n, "local": [...], "tries": n}


def _simplify(pts, tol):
    """Douglas-Peucker: the bends of a polyline that stand more than tol off the straight run past them"""
    if len(pts) < 3: return list(pts)
    a, b = pts[0], pts[-1]
    i, dm = 0, -1.0
    for j in range(1, len(pts) - 1):
        d = _seg_dist(a, b, pts[j], pts[j])
        if d > dm: i, dm = j, d
    if dm <= tol: return [a, b]
    return _simplify(pts[:i + 1], tol)[:-1] + _simplify(pts[i:], tol)


def _car_regular(doc, frame, layout_nodes):
    """the car view (see regular): the smallest scale of CAR_K at which every end comb, label and run stands clear
    (check_regular with slanted runs); at each scale a crowded node's comb or branch is turned to its next side first"""
    import copy as _copy, re as _re
    spots_mm, route = frame
    rev = {"bp_" + _re.sub(r"[^A-Za-z0-9]", "_", n): n for n in layout_nodes}
    free = set(getattr(route, "free", ()))
    bps = {e["id"] for e in doc.get("branchPoints", [])}
    spot = {b: tuple(spots_mm[rev[b]]) for b in bps if b in rev and rev[b] in spots_mm and rev[b] not in free}
    vias, straight = {}, set()      # straight: anchored bundles drawn node to node (their route ran on top of another's)
    def via_mm(p, n, b):
        key = (p, n, b["id"])
        if b["id"] in straight: return []
        if key not in vias:
            r = route(rev[p], rev[n], _mm(b["length"])) if p in spot and n in spot else None
            mid = _simplify(r, CAR_SIMPLIFY_MM)[1:-1] if r else []
            # no bend right by a node: the run goes straight in (its last short jog would lie on the node's own comb)
            vias[key] = [q for q in mid if min(math.hypot(q[0] - r[0][0], q[1] - r[0][1]), math.hypot(q[0] - r[-1][0], q[1] - r[-1][1])) >= CAR_END_MM]
        return vias[key]
    last, tries, best, fallback = None, 0, None, None
    for k in ([float(os.environ["FB_K"])] if os.environ.get("FB_K") else CAR_K):
        force, turns, prev_bad = {}, collections.Counter(), None
        for _ in range(CAR_TRIES):
            tries += 1
            d = _copy.deepcopy(doc)
            car = {"k": k, "spot": spot, "dmin": R_MINL, "force": force,
                   "via": lambda p, n, b, k=k: [(q[0] * k, q[1] * k) for q in via_mm(p, n, b)]}
            try:
                _regular_once(d, car)
            except AssertionError as e:
                last = "k %g: %s" % (k, e); break
            bad = check_regular(d, square=False)
            if not bad:
                # on their spots: the anchored nodes and any other spotted node drawn within 60 mm (car) of its spot
                at = {e["id"]: _centre(e) for e in d.get("branchPoints", [])}
                onspot = sorted(m for m in spot if m in at and math.hypot(at[m][0] - HALF - spot[m][0] * k, at[m][1] - HALF - spot[m][1] * k) <= max(60 * k, 45))
                st = dict(k=k, anchored=len(onspot), spotted=len(spot), tries=tries, local=sorted(set(spot) - set(onspot)),
                          crossings=list(CROSSINGS), straight=sorted(straight))
                if fallback is None or len(onspot) > fallback[0]["anchored"]: fallback = (st, d)
                break
            last = "k %g: %s" % (k, bad[:4])
            if bad == prev_bad: break      # the turns changed nothing: the next scale
            prev_bad = bad
            if DEBUG: print("car k %g try %d: %d problems %s" % (k, _, len(bad), bad[:3]))
            if os.environ.get("FB_DUMP") and (best is None or len(bad) <= best[0] or os.environ.get("FB_K")):
                best = (len(bad), k)
                import json as _json
                _json.dump(d, open(os.environ["FB_DUMP"], "w"), indent=1)
            # two anchored bundles whose routes run on top of each other: the one with route bends drawn straight instead
            xb = {i: len(via_mm(*v)) for i, v in car["xb"].items()}
            more = False
            for msg in bad:
                m_ = _re.match(r"bundles cross or overlap: (\S+) / (\S+)$", msg)
                if m_ and m_.group(1) in xb and m_.group(2) in xb:
                    x = max((m_.group(1), m_.group(2)), key=lambda i: (xb[i], i))
                    if xb[x] and x not in straight: straight.add(x); more = True
            if more: continue
            # the anchored nodes whose pieces are in the problems: turn their combs (then a local branch) to the next side
            own, hit = car["owner"], []
            for msg in bad:
                for tok in _re.findall(r"[A-Za-z0-9_\-.:#]+", msg):
                    n = own.get(tok.split("#")[0])
                    if n is not None and n not in hit: hit.append(n)
            if not hit: break
            for n in hit:
                turns[n] += 1
                i = turns[n]
                force[n] = AXES[i % 4]
        if fallback and fallback[0]["anchored"] >= CAR_ON_SPOT * len(spot): break
    if fallback is None: raise AssertionError("car layout: nothing clear up to scale %g (%s)" % (CAR_K[-1], last))
    doc.clear(); doc.update(fallback[1])
    CAR_STATS.clear(); CAR_STATS.update(fallback[0])
    return doc


def line_text_hits(doc):
    """[(bundle, text owner)]: a bundle run through a text that is not its own, its end parts' or a bundle's sharing one of
    its ends (the car view's slanted runs; the square view keeps these clear while placing)"""
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    near = {}
    for b in doc.get("bundles", []):
        for x in (b["sourceId"], b["targetId"]): near.setdefault(x, set()).add(b["id"])
    onloc = {}
    for k in INLINE_KINDS:
        for e in doc.get(k, []):
            if e.get("locationId"): onloc.setdefault(e["locationId"], set()).add(e["id"])
    texts = [(o.split("#")[0], _pbb(p), p) for o, p, _ in text_boxes(doc)]
    out = []
    for b in doc.get("bundles", []):
        if b["sourceId"] not in at or b["targetId"] not in at: continue
        pts = bundle_path(doc, b, at)
        mine = {b["id"], b["sourceId"], b["targetId"]} | near.get(b["sourceId"], set()) | near.get(b["targetId"], set()) \
            | onloc.get(b["sourceId"], set()) | onloc.get(b["targetId"], set())
        for o, bb, poly in texts:
            if o in mine: continue
            for a, c in zip(pts, pts[1:]):
                if max(a[0], c[0]) < bb[0] - R_LW or min(a[0], c[0]) > bb[2] + R_LW or max(a[1], c[1]) < bb[1] - R_LW or min(a[1], c[1]) > bb[3] + R_LW:
                    continue
                if _poly_seg_hit(poly, a, c, R_LW): out.append((b["id"], o)); break
    return out


def _poly_seg_hit(poly, a, c, g):
    """a segment a-c within g of a convex polygon (or inside it)"""
    n = len(poly)
    for i in range(n):
        if _seg_dist(poly[i], poly[(i + 1) % n], a, c) < g: return True
    def inside(p):
        sg = 0
        for i in range(n):
            x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
            cr = (x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)
            if cr != 0:
                if sg == 0: sg = 1 if cr > 0 else -1
                elif (cr > 0) != (sg > 0): return False
        return True
    return inside(a) or inside(c)


def _after_common(p, q):
    """two paths out of one point: what is left of each after the run they share, and the point where they part"""
    p, q = list(p), list(q)
    while len(p) > 1 and len(q) > 1:
        da, db = (p[1][0] - p[0][0], p[1][1] - p[0][1]), (q[1][0] - q[0][0], q[1][1] - q[0][1])
        la, lb = math.hypot(*da), math.hypot(*db)
        if la < 1e-9: p = [p[0]] + p[2:]; continue
        if lb < 1e-9: q = [q[0]] + q[2:]; continue
        if abs(da[0] / la - db[0] / lb) > 1e-6 or abs(da[1] / la - db[1] / lb) > 1e-6: break
        m = min(la, lb)
        d = (p[0][0] + da[0] / la * m, p[0][1] + da[1] / la * m)
        p = [d] + (p[2:] if la - m < 1e-9 else p[1:])
        q = [d] + (q[2:] if lb - m < 1e-9 else q[1:])
        if abs(la - lb) > 1e-9: break
    return p, q, p[0]


def extent(doc):
    """(width, height) in layout units of everything the layout view draws (parts, bundles, texts)"""
    xs, ys = [], []
    for k in NODE_KINDS:
        for e in doc.get(k, []):
            if e.get("layoutPosition"): xs.append(e["layoutPosition"]["x"] + HALF); ys.append(e["layoutPosition"]["y"] + HALF)
    for _, poly, _ in text_boxes(doc):
        x0, y0, x1, y1 = _pbb(poly); xs += [x0, x1]; ys += [y0, y1]
    return (round(max(xs) - min(xs)), round(max(ys) - min(ys))) if xs else (0, 0)


CROSSINGS = []      # the last check_regular(square=False): runs that cross cleanly, as in the car


def _clean_cross(s1, s2, min_deg=20.0):
    """two segments that properly intersect at min_deg or more, each crossing point at least 30 units from every end"""
    (p, q), (a, b) = s1, s2
    d1, d2 = (q[0] - p[0], q[1] - p[1]), (b[0] - a[0], b[1] - a[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    L1, L2 = math.hypot(*d1), math.hypot(*d2)
    if not L1 or not L2 or abs(den) / (L1 * L2) < math.sin(math.radians(min_deg)): return False
    t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den
    u = ((a[0] - p[0]) * d1[1] - (a[1] - p[1]) * d1[0]) / den
    return 30.0 / L1 < t < 1 - 30.0 / L1 and 30.0 / L2 < u < 1 - 30.0 / L2


def check_regular(doc, square=True):
    """the regular layout gate: [] when formboard mode is off, every bundle has a set length and runs square (no slant), no
    two bundles cross or overlap (the end stubs of one node may share their comb spine out of it), none runs through a
    part, no two parts share a spot and no text overlaps another (label_overlaps, full-size text); else a list of problems.
    The 1:1 gates of check() (drawn = set length, panel grid) do not apply: drawn length is not to scale. square=False: the
    car view (Dan 2026-11-16), whose runs follow the editor routes at any angle; no bundle may run through a text instead
    (line_text_hits)"""
    bad = []
    CROSSINGS.clear()
    if doc.get("formboard"): bad.append("formboard mode is on")
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    bps = {e["id"] for e in doc.get("branchPoints", [])}
    deg, P = {}, {}
    for b in doc.get("bundles", []):
        for x in (b["sourceId"], b["targetId"]): deg[x] = deg.get(x, 0) + 1
    for b in doc.get("bundles", []):
        if not b.get("length") or _mm(b["length"]) <= 0: bad.append("%s: no set length" % b["id"])
        if b["sourceId"] not in at or b["targetId"] not in at:
            bad.append("%s: an end has no layout position" % b["id"]); continue
        pts = bundle_path(doc, b, at)
        if len(pts) < 2:
            bad.append("%s: drawn with no length" % b["id"]); continue
        if square and any(abs(p[0] - q[0]) > 1e-6 and abs(p[1] - q[1]) > 1e-6 for p, q in zip(pts, pts[1:])): bad.append("%s: a slanted run" % b["id"])
        P[b["id"]] = (b, pts)
    ids = sorted(P)
    inl_at = {e.get("locationId") for k in INLINE_KINDS for e in doc.get(k, [])}
    def is_run(b):       # a run between two junctions (not an end stub, not an inline part's stub)
        return all(z in bps and z not in inl_at for z in (b["sourceId"], b["targetId"]))
    def stub(b, s):      # b ends, away from s, where nothing else leaves
        return deg.get(b["targetId"] if b["sourceId"] == s else b["sourceId"], 0) == 1
    for i, x in enumerate(ids):
        bx, px = P[x]
        for y in ids[i + 1:]:
            by, py = P[y]
            shared = {bx["sourceId"], bx["targetId"]} & {by["sourceId"], by["targetId"]}
            qx, qy, keep = px, py, None
            if shared:
                s = sorted(shared)[0]
                qx = px if bx["sourceId"] == s else px[::-1]
                qy = py if by["sourceId"] == s else py[::-1]
                keep = qx[0]
                if stub(bx, s) and stub(by, s): qx, qy, keep = _after_common(qx, qy)
            hit, clean = False, True
            # the car view: two runs between branch points that share no node may cross cleanly (they pass over / under
            # each other in the car); listed in CROSSINGS, not failed
            trunk = not square and not shared and (is_run(bx) or is_run(by))
            for a0, a1 in zip(qx, qx[1:]):
                for c0, c1 in zip(qy, qy[1:]):
                    s1, s2 = (a0, a1), (c0, c1)
                    if keep is not None: s1, s2 = _clip2(s1, keep, 20.0), _clip2(s2, keep, 20.0)
                    if s1 and s2 and _seg_dist(s1[0], s1[1], s2[0], s2[1]) < CLR:
                        hit = True
                        if not (trunk and _clean_cross(s1, s2)): clean = False
            if hit and trunk and clean: CROSSINGS.append((x, y))
            elif hit: bad.append("bundles cross or overlap: %s / %s" % (x, y))
    parts = sorted((p, n) for n, p in at.items() if n not in bps)
    for x in ids:
        b, pts = P[x]
        for p, n in parts:
            if n in (b["sourceId"], b["targetId"]): continue
            if any(_seg_dist(a0, a1, p, p) < NODE_GAP / 2 for a0, a1 in zip(pts, pts[1:])): bad.append("%s runs through the part %s" % (x, n))
    for i, (p, n) in enumerate(parts):
        for q, m in parts[i + 1:]:
            if q[0] - p[0] >= NODE_GAP: break
            if math.hypot(q[0] - p[0], q[1] - p[1]) < NODE_GAP: bad.append("two parts on one spot: %s / %s" % (n, m))
    bad += ["labels overlap: %s / %s" % ab for ab in label_overlaps(doc)]
    if not square: bad += ["%s runs through the text of %s" % ab for ab in line_text_hits(doc)]
    return bad
