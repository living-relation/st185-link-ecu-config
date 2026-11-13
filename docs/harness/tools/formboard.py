"""formboard.py - lay a generated harness.design document out as a true 1:1 formboard (Dan A25 a, 2026-11-12).

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
import math

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
    eps = TXT["margin"] + 1.0 if eps is None else eps
    ob = [(_pbb(p), p, w) for p, w in old.texts]
    for p, w in new.texts:
        bb = _pbb(p)
        for bb2, p2, w2 in ob:
            if w2 == w or bb2[0] >= bb[2] + eps or bb[0] >= bb2[2] + eps or bb2[1] >= bb[3] + eps or bb[1] >= bb2[3] + eps:
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

    textmode = "all"     # all: end labels and bundle texts kept clear while placing; labels: end labels only; none

    def node_texts(self, n, c, v):
        """n's details box when its centre is at c and its bundles lie along v (a branch point has none)"""
        e = self.el.get(n)
        if e is None or n in self.bps or self.textmode == "none": return []
        wl, ws = end_text_size(e, self.doc, self.s)
        box = end_box(c, detail_side(v, n in self.mated, e.get("layoutLabelPosition")), wl, ws, self.s)
        return [(box, n)] if box else []

    def bundle_texts(self, b, path, spoke=False):
        """b's length label and label pills along path (path from b's source to its target); an end stub's are kept clear in
        every mode but none"""
        if self.textmode == "none" or (self.textmode == "labels" and not spoke): return []
        return [(p, b["id"]) for p in bundle_texts(b, path, self.s, (b["sourceId"] in self.bps, b["targetId"] in self.bps))]

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
            q = (at[0] + math.cos(a) * L, at[1] + math.sin(a) * L)
            piece = Shape(); piece.segs.append((at, q, (n, c), b["id"]))
            if c not in T.bps: piece.nodes.append((q, c))
            piece.texts = T.node_texts(c, q, (at[0] - q[0], at[1] - q[1])) + \
                T.bundle_texts(b, [at, q] if b["sourceId"] == n else [q, at], spoke=True)
            allpos = dict(ps); allpos[c] = q
            return None if clash(piece, sh, allpos) is not None else (q, piece)
        # 1: each at the clear angle nearest its own
        sh1, ps1, pa1, ok = Shape(), dict(pos), {}, True
        sh1.add(shape)
        for c, b in spokes:
            got = None
            for j in range(0, 721):
                got = tryspoke(c, b, pref[c] + (j + 1) // 2 * (1 if j % 2 else -1) * 0.5, sh1, ps1)
                if got: break
            if not got: ok = False; break
            q, piece = got; sh1.add(piece); ps1[c] = q; pa1[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
        if not ok:
            # 2: spread them evenly, in their own order round n, over the angles a spoke alone could take
            Lmax = max(Ls.values())
            free = [a / 2.0 for a in range(720) if tryspoke(spokes[0][0], spokes[0][1], cut + a / 2.0, shape, pos) is not None
                    and all(tryspoke(c, b, cut + a / 2.0, shape, pos) for c, b in spokes if Ls[c] == Lmax)]
            if len(free) < len(spokes): return False
            orderd = sorted(spokes, key=lambda cb: rel(pref[cb[0]]))
            sh1, ps1, pa1, ok = Shape(), dict(pos), {}, True
            sh1.add(shape)
            k = len(orderd)
            for i, (c, b) in enumerate(orderd):
                tgt = free[min(len(free) - 1, int((i + 0.5) * len(free) / k))]
                got = None
                for j in range(0, 721):
                    got = tryspoke(c, b, cut + tgt + (j + 1) // 2 * (1 if j % 2 else -1) * 0.5, sh1, ps1)
                    if got: break
                if not got: return False
                q, piece = got; sh1.add(piece); ps1[c] = q; pa1[b["id"]] = [at, q] if b["sourceId"] == n else [q, at]
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
# The app sizes its text in the browser, so the boxes here are ESTIMATES from the text length, measured in the desktop app
# (CabinPower Rev F, 2026-11-13, annotation 0.5, then divided by 0.5): sizes below are layout units (px) at s = 1.
#  - an end's details (connector / terminal; component code: endpointDetailsPosition / previewOrientations): they sit on the
#    side AWAY from the node's bundles (sum of the vectors to each bundle's first point, the dominant axis wins: Left / Right
#    when |x| > |y| + 1, else Top / Bottom), or beside it while mated, or on layoutLabelPosition; Left / Right: one row,
#    the label box (small text, 2.34 per character + 6 padding) then the signal or part bar text (4.8 per character), 13 high,
#    starting 18 units from the node centre and vertically centred; Top / Bottom: the same two pieces, counted as stacked
#    (13 + 13 high) AND as wide as both side by side, so the estimate is never smaller than either way the app may draw it;
#  - a bundle's length label ("100 mm", 4.6 per character, 10 high) on the bundle at the middle of its drawn path, along it;
#  - a bundle label (the ghost tags' coloured "AB-cabin 2", 12.4 per character + 12, 28 high) along the bundle next to the
#    node it is drawn at;
#  - a layout note: its stored width (default 150) by its wrapped lines (6.5 per character, 18 per line, + 16).
# The boxes keep a small margin; two boxes of different owners must not overlap.
TXT = dict(lab_ch=2.34, lab_pad=6.0, sig_ch=4.8, row=13.0, gap=6.0, off=18.0, len_ch=4.6, len_h=10.0, pill_ch=12.4,
           pill_pad=12.0, pill_h=28.0, note_ch=6.5, note_line=18.0, note_pad=16.0, margin=1.0)


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
    if mated: side = {"Left": "Bottom", "Right": "Bottom", "Top": "Left", "Bottom": "Left"}[side]
    return side


def end_text_size(e, doc=None, s=1.0):
    """(label box width, text width) of a node's details at annotation scale s"""
    lab = e.get("label") or ""
    sig = e.get("signal") or ""
    if not sig and e.get("partId") and doc is not None: sig = _part_number(doc, e["partId"])
    wl = (len(lab) * TXT["lab_ch"] + TXT["lab_pad"]) * s if lab else 0.0
    ws = len(sig) * TXT["sig_ch"] * s
    return wl, ws


def end_box(c, side, wl, ws, s=1.0):
    """the details box of a node centred at c on that side"""
    if not (wl or ws): return None
    off, row, g = TXT["off"], TXT["row"] * s, TXT["gap"] * s
    w = wl + ws + (g if wl and ws else 0)
    if side in ("Left", "Right"):
        x0 = c[0] + off if side == "Right" else c[0] - off - w
        return _rect(x0 + w / 2, c[1], w, row)
    h = 2 * row + g
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


def bundle_texts(b, path, s=1.0, end_nodes=()):
    """the text boxes a bundle draws on the board: its length label, and its label pills"""
    out = []
    lw = len(_len_text(b)) * TXT["len_ch"] * s if b.get("length") else 0
    plen = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1))
    # a bundle shorter than its own length label (the 2 mm / 15 mm junction steps of a tree) cannot carry it clear of its
    # neighbours whatever the layout: it is left out of the gate and counted by short_length_labels()
    if b.get("length") and len(path) > 1 and plen >= lw + 4:
        c, u = _along(path, 0.5)
        if u[0] < 0 or (u[0] == 0 and u[1] < 0): u = (-u[0], -u[1])
        out.append(_rect(c[0], c[1], lw, TXT["len_h"] * s, *u))
    pills = []
    if b.get("separateLabels"):
        if b.get("label"): pills.append((b["label"], 0))
        if b.get("endLabel"): pills.append((b["endLabel"], 1))
    elif b.get("label") and not b.get("middleLabel"):
        pills += [(b["label"], 0), (b["label"], 1)]
    for text, end in pills:
        if not b.get("separateLabels") and end_nodes and end_nodes[end]: continue    # skipped at a branch point
        w, h = (len(text) * TXT["pill_ch"] + TXT["pill_pad"]) * s, TXT["pill_h"] * s
        p = path if end == 0 else path[::-1]
        L = sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)) or 1.0
        c, u = _along(p, min(0.5, (HALF + 2 + w / 2) / L))
        out.append(_rect(c[0], c[1], w, h, *u))
    return out


def short_length_labels(doc):
    """the bundles too short to carry their own length label (left out of the label gate; see bundle_texts)"""
    s = _scale(doc)
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    out = []
    for b in doc.get("bundles", []):
        if not b.get("length") or b["sourceId"] not in at or b["targetId"] not in at: continue
        p = bundle_path(doc, b, at)
        if sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)) < len(_len_text(b)) * TXT["len_ch"] * s + 4:
            out.append(b["id"])
    return out


def note_box(n, s=1.0):
    w = n.get("width") or 150
    per = max(1, int((w - TXT["note_pad"]) // TXT["note_ch"]))
    lines = sum(max(1, math.ceil(len(par) / per)) for par in (n.get("text") or "").split("\n"))
    h = lines * TXT["note_line"] + TXT["note_pad"]
    x, y = n["layoutPosition"]["x"], n["layoutPosition"]["y"]
    return _rect(x + w * s / 2, y + h * s / 2, w * s, h * s)


def text_boxes(doc):
    """[(owner, polygon, what)] for every text the layout view draws (estimated, see TXT)"""
    s = _scale(doc)
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    bps = {e["id"] for e in doc.get("branchPoints", [])}
    vec = {}
    out = []
    for b in doc.get("bundles", []):
        if b["sourceId"] not in at or b["targetId"] not in at: continue
        path = bundle_path(doc, b, at)
        for n, nxt in ((b["sourceId"], path[1]), (b["targetId"], path[-2])):
            v = vec.get(n, (0.0, 0.0)); vec[n] = (v[0] + nxt[0] - at[n][0], v[1] + nxt[1] - at[n][1])
        for poly in bundle_texts(b, path, s, (b["sourceId"] in bps, b["targetId"] in bps)):
            out.append((b["id"], poly, "bundle text"))
    mated = {x for m in doc.get("mates", []) or [] for x in (m["sourceId"], m["targetId"])}
    for k in ("connectors", "terminals"):
        for e in doc.get(k, []):
            if not e.get("layoutPosition"): continue
            side = detail_side(vec.get(e["id"], (0.0, 0.0)), e["id"] in mated, e.get("layoutLabelPosition"))
            wl, ws = end_text_size(e, doc, s)
            box = end_box(at[e["id"]], side, wl, ws, s)
            if box: out.append((e["id"], box, "label"))
    for n in doc.get("layoutNotes", []) or []:
        if n.get("layoutPosition"): out.append((n["id"], note_box(n, s), "note"))
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
                for dist in (45, 60, 75, 90, 120):
                    hit = None
                    for rot in (0, 30, -30, 60, -60, 90, -90):
                        u = _rot((d[0] / L, d[1] / L), rot)
                        q = (pos[a][0] + dist * u[0], pos[a][1] + dist * u[1])
                        piece = Shape(); piece.nodes = [(q, c)]
                        piece.texts = T.node_texts(c, q, (pos[a][0] - q[0], pos[a][1] - q[1]))
                        if clash(piece, shape, dict(pos, **{c: q})) is None:
                            hit = (q, piece); break
                    if hit: break
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
    bad += ["labels overlap: %s / %s" % ab for ab in label_overlaps(doc)]     # Dan 2026-11-13: every label readable
    return bad
