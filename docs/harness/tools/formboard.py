"""formboard.py - lay a generated harness.design document out as a true 1:1 formboard (Dan A25 a, 2026-11-12; A44, 2026-11-15).

The generators (gen_abeng, gen_engc, gen_cabin, gen_dash and the files built on it, gen_heavydc) first place every part on
their own formboard; `to_car(doc, build_drawings.car_frame(layout), layout nodes)` then redraws the layout view as the car
looks from above on the layout-editor routes (Dan A44, 2026-11-15; below, "the car-frame formboard"), every bundle drawn at
exactly its set length (the master / tree length, never changed), the way harness.design's formboard mode measures it, and
turns formboard mode on (A1 landscape panels, at least 4 x 4). `check(doc)` is the gate: every drawn bundle length equals its
set length within 1 mm, no two bundles cross or overlap, nothing is off the panels and no label overlaps another (Dan
2026-11-13); `report` prints the board, the deviation from the editor spots and the service loops.

How harness.design measures a formboard (app.harness.design, read 2026-11-12; docs.harness.design/feature/formboard and
/feature/local-files/json-format "formboard"): one layout unit is 0.75 mm (FORMBOARD_MM_PER_PX); a bundle's path runs
from its source node's centre (layoutPosition + 15, 15) through its layoutPoints (each + 15, 15) to its target node's centre;
its drawn length is that polyline with every corner rounded at the bundle's radius (formboard.defaultCornerRadius unless the
bundle sets its own): roundedPathLength below is the app's own formula. The app calls a bundle to scale when the two
lengths differ by less than 0.5 mm, and draws any other bundle, or one with no set length (0 mm counts as none), yellow
with black dashes. The panel grid is centred on layout (0, 0).

The drawing (view only: no wire, pin, length or part changes):
- every branch point on its editor spot, every bundle along its editor route; slack taken up near the far end in one
  compact place (to_car, below);
- the end stubs (100 mm end allowances, 25 mm splice stubs) fan out round their node as straight spokes, or in label
  columns where they are many (_spokes_at);
- a box seat is no 0 mm bundle (the app flags 0 mm as no set length): build_drawings.box_groups gives every seat end its
  own copy of the seat stub instead, so every routed wire length stays the same;
- mated plugs (bussed receptacle caps, the CAN-Lambda terminator plug, the RADLOK firewall pairs) sit face to face.
"""
import itertools
import math
import os

DEBUG = bool(os.environ.get("FB_DEBUG"))

MM_PER_UNIT = 0.75            # harness.design FORMBOARD_MM_PER_PX
HALF = 15                     # a layout node is 30 x 30; bundles run from its centre
RADIUS_MM = 30                # default bend radius (the app's metric default)
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


def _self_clash(piece):
    """an end's own label against its own stub's length label (one piece, two owners): the gate checks those too"""
    if len(piece.texts) < 2: return False
    one = Shape(); one.texts = piece.texts[:1]
    rest = Shape(); rest.texts = piece.texts[1:]
    return text_clash(one, rest) is not None


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


def _rot(u, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (u[0] * c - u[1] * s, u[0] * s + u[1] * c)


def _column_fan(T, n, at, spokes, Ls, pref, din, shape, pos):
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
                    if clash(piece, sh1, allpos) is None and not _self_clash(piece): placed = (q, piece)
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

def _spokes_at(T, shape, pos, paths, n, at, spokes, din):
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
        return None if clash(piece, sh, allpos) is not None or _self_clash(piece) else (q, piece)
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
            col = _column_fan(T, n, at, labelled, Ls, pref, din, sh0, ps0)
            if not col: continue
            sh0, ps1_, pa1_ = col; ps0.update(ps1_); pa0.update(pa1_)
            if not stubs_first and not put_stubs(sh0, ps0, pa0): continue
            got = (sh0, ps0, pa0); break
        if not got: return False
        sh1, ps1, pa1 = got
    shape.segs[:] = sh1.segs; shape.nodes[:] = sh1.nodes; shape.texts[:] = sh1.texts
    pos.update(ps1); paths.update(pa1)
    return True


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


def end_box(c, side, wl, ws, s=1.0, e=None, v=(1.0, 0.0), mated=False):
    """the details box of a node centred at c on that side; wl, ws = end_text_size (width, height, already scaled); e and v
    (the end and its bundle vector) give the spacing the app keeps from the node"""
    w, h = wl, ws
    if not (w and h): return None
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


def bundle_texts(b, path, s=1.0, end_nodes=(), n=1):
    """the text boxes a bundle draws on the board: its length label, and its label pills; n = wires through it"""
    out = []
    lw = len_label_w(b, s) if b.get("length") else 0
    plen = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1))
    # a bundle too short for its length label to clear the hub (the 2 mm / 15 mm junction steps of a tree, the 25 mm splice
    # stubs: the label, centred on the bundle, reaches within 15 units of a node centre, inside the node symbol where every
    # bundle of that node meets) cannot carry it clear whatever the layout: left out of the gate, counted by
    # short_length_labels() (Dan 2026-11-13 real label sizes: a 25 mm stub's "25 mm" tag is 24 units long on a 33-unit stub)
    if b.get("length") and len(path) > 1 and plen >= lw + 2 * HALF:
        c, u = _along(path, 0.5)
        # the text reads left to right (straight up when the bundle is vertical) and sits off the bundle on the text's
        # upper side, further for a thicker bundle; +-3 units across for the bundle thickness the model does not know
        d = u if u[0] > 1e-9 else ((-u[0], -u[1]) if u[0] < -1e-9 else (0.0, -1.0))
        off = len_label_offset(n) * s / 0.5
        out.append(_rect(c[0] + d[1] * off, c[1] - d[0] * off, lw, TXT["len_h"] * s + (2.0 if n <= 2 else 6.0), *d))
    pills = []
    if b.get("separateLabels"):
        if b.get("label"): pills.append((b["label"], 0))
        if b.get("endLabel"): pills.append((b["endLabel"], 1))
    elif b.get("label") and not b.get("middleLabel"):
        pills += [(b["label"], 0), (b["label"], 1)]
    for text, end in pills:
        if not b.get("separateLabels") and end_nodes and end_nodes[end]: continue    # skipped at a branch point
        w, h = (text_w(text, TXT["pill_px"]) * TXT["pill_k"] + TXT["pill_pad"]) * s, TXT["pill_h"] * s
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


def text_boxes(doc):
    """[(owner, polygon, what)] for every text the layout view draws (estimated, see TXT)"""
    s = _scale(doc)
    at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
    bps = {e["id"] for e in doc.get("branchPoints", [])}
    wc = bundle_wire_counts(doc)
    vec = {}
    out = []
    for b in doc.get("bundles", []):
        if b["sourceId"] not in at or b["targetId"] not in at: continue
        path = bundle_path(doc, b, at)
        for n, nxt in ((b["sourceId"], path[1]), (b["targetId"], path[-2])):
            v = vec.get(n, (0.0, 0.0)); vec[n] = (v[0] + nxt[0] - at[n][0], v[1] + nxt[1] - at[n][1])
        for poly in bundle_texts(b, path, s, (b["sourceId"] in bps, b["targetId"] in bps), wc.get(b["id"], 1)):
            out.append((b["id"], poly, "bundle text"))
    mated = {x for m in doc.get("mates", []) or [] for x in (m["sourceId"], m["targetId"])}
    shown = display_signals(doc)
    for k in ("connectors", "terminals"):
        for e in doc.get(k, []):
            if not e.get("layoutPosition"): continue
            v, mt = vec.get(e["id"], (0.0, 0.0)), e["id"] in mated
            side = detail_side(v, mt, e.get("layoutLabelPosition"))
            wl, ws = end_text_size(e, doc, s, shown.get(e["id"]))
            box = end_box(at[e["id"]], side, wl, ws, s, e, v, mt)
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


def repair_spokes(doc, rounds=6):
    """an end (on a straight stub of its own) whose label still overlaps another text is swung round its node, each angle
    with each label side, to where the overlaps drop most and its stub clears every bundle and part (view only; the stub keeps
    its length)"""
    el = {e["id"]: e for k in ("connectors", "terminals") for e in doc.get(k, [])}
    stub = {}
    deg = {}
    for b in doc.get("bundles", []):
        deg[b["sourceId"]] = deg.get(b["sourceId"], 0) + 1; deg[b["targetId"]] = deg.get(b["targetId"], 0) + 1
    for b in doc.get("bundles", []):
        for end, node in ((b["targetId"], b["sourceId"]), (b["sourceId"], b["targetId"])):
            if end in el and not b.get("layoutPoints") and _mm(b["length"]) <= 200: stub[end] = (node, b)
    stub = {k: v for k, v in stub.items() if deg.get(k) == 1}
    cap = {}        # a plug's mated cap with no bundle of its own (bussed receptacle, terminator plug): it moves with the plug
    for m in doc.get("mates", []) or []:
        for a, c in ((m["sourceId"], m["targetId"]), (m["targetId"], m["sourceId"])):
            if a in stub and c in el and not deg.get(c): cap[a] = c
    capof = {c: a for a, c in cap.items()}
    mated = {x for m in doc.get("mates", []) or [] for x in (m["sourceId"], m["targetId"])} - set(cap) - set(capof)
    for _ in range(rounds):
        bad = label_overlaps(doc)
        if not bad: return
        now = len(bad)
        owners = []
        for a, b in bad:
            for x in (a, b):
                o = x.split(" ", 1)[1]
                o = capof.get(o, o)
                o = o if o in stub else next((k for k, (_, bb) in stub.items() if bb["id"] == o), None)
                if o and o not in owners: owners.append(o)
        moved = False
        for o in owners:
            if o in mated: continue
            node, b = stub[o]
            at = {e["id"]: _centre(e) for k in NODE_KINDS for e in doc.get(k, []) if e.get("layoutPosition")}
            c, L = at[node], _mm(b["length"]) / MM_PER_UNIT
            rest = Shape()
            for bb in doc["bundles"]:
                if bb["id"] == b["id"]: continue
                p = bundle_path(doc, bb, at)
                rest.segs += [(p[i], p[i + 1], (bb["sourceId"], bb["targetId"]), bb["id"]) for i in range(len(p) - 1)]
            bps = {e["id"] for e in doc.get("branchPoints", [])}
            rest.nodes = [(p, n) for n, p in at.items() if n not in bps and n != o]
            e = el[o]
            ce = el.get(cap.get(o))
            if ce is not None: rest.nodes = [x for x in rest.nodes if x[1] != ce["id"]]
            was = (dict(e["layoutPosition"]), e.get("layoutLabelPosition"),
                   dict(ce["layoutPosition"]) if ce else None, ce.get("layoutLabelPosition") if ce else None)
            best = (now,) + was
            def setside(x, side):
                if side is None: x.pop("layoutLabelPosition", None)
                else: x["layoutLabelPosition"] = side
            for ang in range(0, 360, 6):
                u = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
                q = (c[0] + u[0] * L, c[1] + u[1] * L)
                one = Shape(); one.segs = [(c, q, (node, o), b["id"])]; one.nodes = [(q, o)]
                qc = (q[0] + u[0] * 45, q[1] + u[1] * 45)
                if ce is not None: one.nodes.append((qc, ce["id"]))
                if clash(one, rest, dict(at, **{o: q}), clr=CLR, gap=NODE_GAP) is not None: continue
                e["layoutPosition"] = {"x": _r2(q[0] - HALF), "y": _r2(q[1] - HALF)}
                if ce is not None: ce["layoutPosition"] = {"x": _r2(qc[0] - HALF), "y": _r2(qc[1] - HALF)}
                for side in (None,) + SIDES:
                    setside(e, side)
                    for cside in ((None,) + SIDES if ce is not None else (None,)):
                        if ce is not None: setside(ce, cside)
                        k = len(label_overlaps(doc))
                        if k < best[0]: best = (k, dict(e["layoutPosition"]), side, dict(ce["layoutPosition"]) if ce else None, cside)
            e["layoutPosition"] = best[1]; setside(e, best[2])
            if ce is not None: ce["layoutPosition"] = best[3]; setside(ce, best[4])
            if best[0] < now: now = best[0]; moved = True
        if not moved: return


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


FAN_OF = {}     # while to_car lays a document out: text owner -> its over-capacity fan (fan_owners)


def fan_owners(doc):
    """{owner: fan node} for the ends of every over_capacity() fan and their own stubs"""
    oc = over_capacity(doc)
    fan = {e: n for n, (_, _, ends) in oc.items() for e in ends}
    for b in doc.get("bundles", []):     # each end's own stub (its length label) belongs to the fan too
        for x in (b["sourceId"], b["targetId"]):
            if x in fan: fan[b["id"]] = fan[x]
    hub = {}
    for b in doc.get("bundles", []):     # and, on the car-frame board (A44), the fan node's own way in, which the fan sits on
        if b["id"] not in fan:
            for x, y in ((b["sourceId"], b["targetId"]), (b["targetId"], b["sourceId"])):
                if x in oc: fan[b["id"]] = x; hub[y] = x
    for b in doc.get("bundles", []):     # and the ghost tags at the hub that way in comes from (A43 c: "ghost tags touching")
        for x, y in ((b["sourceId"], b["targetId"]), (b["targetId"], b["sourceId"])):
            if x in hub and y.startswith("t_gh_") and y not in fan: fan[y] = hub[x]; fan[b["id"]] = hub[x]
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


# ------------------------------------------------------------------ the car-frame formboard (Dan 2026-11-15)
# Dan 2026-11-15 (DECISIONS B6 "A44", replaces A25 a's "A3 panels" and "serpentines"): every formboard is A1 landscape panels,
# at least 4 rows x 4 columns (more where the editor route shape needs them: "the number of panels can expand as needed"),
# 30 mm bend radius, labels readable on an A1 print; the harness laid out as the car looks from above, 1:1, on the
# layout-editor routes (every device on its editor spot, every bundle along its editor route: the seeds' car-mm lines and
# the route files' engine-bay lines, front of the car RIGHT, driver side UP); a set length longer than its flat route (3D
# drops, end allowances, rounded corners) is taken up in one compact place near the bundle's far end: a short straight
# offset of its far end (up to OFFSET_MM), else one service loop (a square tooth off the route, the fewest teeth that fit);
# a set length shorter than the route pulls the far end in along it. No whole-trunk serpentines.
PANEL["A1"] = (841, 594)
CAR_PANEL = "A1"
MIN_ROWS, MIN_COLS = 4, 4     # the smallest grid (Dan 2026-11-15); more rows / columns only where the board needs them
CAR_ANNOTATION = (0.6, 0.55, 0.5)   # annotation scales tried per file, largest first; the first whose labels all stand
                              # clear is kept. At 0.6 the smallest text (11.2 px label box) prints 5.0 mm (cap height 3.7 mm,
                              # over the 3.5 mm ISO 3098 / ISO 5455 lettering minimum for A1); 0.5 (the app's 50 %) 4.2 mm
OFFSET_MM = 40.0              # a far end moved this far or less along its last leg takes up a small slack
TOOTH_K = 2.4                 # service loop width, in bend radii
HMAX = 420.0                  # units: deepest service loop tooth (315 mm); deeper slack takes more teeth side by side
LOOP_H = 240.0                # units: a tooth up to this deep (180 mm) is tried before a deeper one
BACKTRACK = int(os.environ.get("FB_BACKTRACK", 400))              # drawings tried again (another way for a branch) before a piece is given up
STATS = {}                    # the last to_car run: {"loops": [...], "offsets": [...], "pulled": [...], "moved": {...}}


def _dedupe(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-6: out.append(p)
    clean = [out[0]]     # the app drops points mid-way along a straight run on save
    for a, b in zip(out[1:], out[2:] + [None]):
        if b is not None:
            c = clean[-1]
            if abs((a[0] - c[0]) * (b[1] - a[1]) - (a[1] - c[1]) * (b[0] - a[0])) < 1e-6 * max(1.0, math.hypot(b[0] - c[0], b[1] - c[1])) ** 2 \
                    and (a[0] - c[0]) * (b[0] - a[0]) + (a[1] - c[1]) * (b[1] - a[1]) >= 0:
                continue
        clean.append(a)
    return clean


def _unit(p, q):
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    return ((q[0] - p[0]) / L, (q[1] - p[1]) / L) if L > 1e-9 else None


def _solve(f, lo, hi, n=60):
    """the x in [lo, hi] where the increasing f crosses 0 (f(lo) <= 0 <= f(hi))"""
    for _ in range(n):
        mid = (lo + hi) / 2
        if f(mid) < 0: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def _teeth(pts, i, s0, w, k, side, h):
    """pts with k square teeth of depth h on leg i (pts[i] -> pts[i + 1]), the first starting s0 along it, each w wide and
    w apart, on side +1 / -1 (left / right of the leg)"""
    p, q = pts[i], pts[i + 1]
    u = _unit(p, q); v = (-u[1] * side, u[0] * side)
    P = lambda a, l: (p[0] + u[0] * a + v[0] * l, p[1] + u[1] * a + v[1] * l)
    mid = []
    for j in range(k):
        a = s0 + j * 2 * w
        mid += [P(a, 0), P(a, h), P(a + w, h), P(a + w, 0)]
    return pts[:i + 1] + mid + pts[i + 1:]


def _fit(pts, need, R, prefer_end=True):
    """candidate drawn paths (each [(kind, path)]) for a bundle of drawn length need (units) along the route pts (its first point
    fixed): the route itself when it is already that long; the far end pulled in along it (route longer than need); the far end
    moved out along its last leg (a short slack); service loops on each leg, the far end's first, both sides, fewest teeth first"""
    pts = _dedupe(pts)
    have = rounded_length(pts, R) if len(pts) > 1 else 0.0
    out = []
    if len(pts) > 1 and abs(have - need) < 0.2:
        return [("route", pts)]
    if len(pts) > 1 and have > need:
        p0 = pts[0]
        f = lambda k: rounded_length([(p0[0] + k * (p[0] - p0[0]), p0[1] + k * (p[1] - p0[1])) for p in pts], R) - need
        k = _solve(f, 0.0, 1.0)
        return [("pulled", [(p0[0] + k * (p[0] - p0[0]), p0[1] + k * (p[1] - p0[1])) for p in pts])]
    slack = need - have
    if len(pts) > 1 and slack * MM_PER_UNIT <= OFFSET_MM:
        u = _unit(pts[-2], pts[-1])
        def moved(d): return pts[:-1] + [(pts[-1][0] + u[0] * d, pts[-1][1] + u[1] * d)]
        d = _solve(lambda d: rounded_length(moved(d), R) - need, 0.0, slack * 2 + 5)
        out.append(("offset", moved(d)))
    if len(pts) > 1 and next(_loops(pts, need, R), None) is not None:
        out.append(("loop", pts))       # the route as drawn; its service loop is placed last, where it has room (_loops)
    return out


def _loops(pts, need, R, prefer_end=True):
    """service loop candidates (kind "loop<k>", path) for the route pts taking up need: k square teeth on one leg, the far
    end's leg first, both sides; shallow teeth first (depth up to LOOP_H), then the fewest teeth"""
    w = TOOTH_K * R
    legs = list(range(len(pts) - 1))
    if prefer_end: legs = legs[::-1]
    deep = []
    for k in range(1, 7):
        for i in legs:
            L = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            e0 = 1.2 * R if i > 0 else max(1.2 * R, 60.0)       # room for the corner before (or the node's other bundles)
            e1 = 1.2 * R
            span = (2 * k - 1) * w
            if L < e0 + span + e1: continue
            room = L - e1 - span - e0
            steps = [L - e1 - span - j * 20.0 for j in range(int(room // 20.0) + 1)] + [e0]     # from the far end back
            for s0 in (steps if prefer_end else [e0 + room / 2, e0] + steps):
                for side in (1, -1):
                    f = lambda h: rounded_length(_teeth(pts, i, s0, w, k, side, h), R) - need
                    if f(HMAX) < 0: continue
                    h = _solve(f, 0.0, HMAX)
                    c = ("loop%d" % k, _teeth(pts, i, s0, w, k, side, h))
                    if h <= LOOP_H: yield c
                    else: deep.append(c)
    for c in deep: yield c


def _hairpins(pts, need, R, dirs):
    """service loops at the far end: the route, then a hairpin out along u and back (one U-turn of the bend radius), so the
    far end lands one hairpin width (2 bend radii) beside its spot; each direction, both sides ("loop1", path)"""
    pts = _dedupe(pts)
    P = pts[-1]
    w = 2.0 * R
    for u in dirs:
        if len(pts) > 1:
            u0 = _unit(pts[-2], P)
            if u0 and u[0] * u0[0] + u[1] * u0[1] < -0.5: continue      # not straight back over the route
        for side in (1, -1):
            v = (-u[1] * side, u[0] * side)
            mk = lambda h: pts + [(P[0] + u[0] * h, P[1] + u[1] * h), (P[0] + u[0] * h + v[0] * w, P[1] + u[1] * h + v[1] * w),
                                  (P[0] + v[0] * w, P[1] + v[1] * w)]
            f = lambda h: rounded_length(_dedupe(mk(h)), R) - need
            lo = R + 1.0
            if f(lo) > 0 or f(2 * HMAX) < 0: continue
            yield ("loop1", mk(_solve(f, lo, 2 * HMAX)))


def _straight_cands(p0, need, R, dirs, straight_mm=200):
    """a far end with no route room (its spot on its parent's, a drop): a straight bundle of the set length off p0, each
    direction; a long one (over straight_mm) gets a service loop on it instead of moving the far end its whole length"""
    out = []
    for u in dirs:
        if need * MM_PER_UNIT <= straight_mm:
            out.append(("offset", [p0, (p0[0] + u[0] * need, p0[1] + u[1] * need)]))
        else:
            Ls = 2 * 1.2 * R + TOOTH_K * R + 60.0
            for kind, path in _fit([p0, (p0[0] + u[0] * Ls, p0[1] + u[1] * Ls)], need, R):
                if kind == "loop": out.append((kind, path))
    return out


def to_car(doc, frame, layout_nodes, panel=CAR_PANEL, annotation=CAR_ANNOTATION, min_rows=MIN_ROWS, min_cols=MIN_COLS):
    """redraw doc's layout view in place (view only) as a 1:1 formboard laid out as the car looks from above, on the
    layout-editor routes (Dan 2026-11-15); frame = build_drawings.car_frame(layout) (spots, route); layout_nodes = the
    layout tree's nodes (a branch point bp_<node> is that node). Turns formboard mode on (A1 landscape, at least
    min_rows x min_cols panels, 30 mm bend radius, annotation scale). Returns doc; STATS says what was done."""
    import re as _re
    spots_mm, route = frame
    rev = {"bp_" + _re.sub(r"[^A-Za-z0-9]", "_", n): n for n in layout_nodes}
    pw, ph = PANEL[panel]
    doc["formboard"] = {"panelSize": panel, "panelOrientation": "Landscape", "panelWidth": {"value": pw, "unit": "mm"},
                        "panelHeight": {"value": ph, "unit": "mm"}, "rows": min_rows, "columns": min_cols,
                        "defaultCornerRadius": {"value": RADIUS_MM, "unit": "mm"}, "annotationScale": annotation}
    import copy as _copy
    best, errors = None, []
    scales = annotation if isinstance(annotation, (tuple, list)) else (annotation,)
    for ann in scales:
        for strat in STRATEGIES:
            for mode in ("all", "labels", "none"):
                d = _copy.deepcopy(doc)
                d["formboard"]["annotationScale"] = ann
                try:
                    st = _to_car_once(d, spots_mm, route, rev, ann, min_rows, min_cols, mode, strat)
                except AssertionError as e:
                    errors.append("%s %s %s: %s" % (ann, strat, mode, e)); continue
                dev = route_deviation(d, frame, layout_nodes)[1][0]
                score = (len(check(d)), dev, -ann)
                if best is None or score < best[0]: best = (score, d, st)
                break
            if best and best[0][0] == 0 and best[0][1] < 60: break
        if best and best[0][0] == 0: break
    if best is None:
        raise AssertionError("formboard: no car layout (%s)" % "; ".join(errors[-3:]))
    doc.clear(); doc.update(best[1])
    STATS.clear(); STATS.update(best[2]); STATS["errors"] = errors
    return doc


STRATEGIES = ({"defer": True}, {"defer": True, "loops_first": True}, {"defer": False}, {"defer": False, "loops_first": True},
              {"defer": True, "inline_loops": True}, {"defer": False, "inline_loops": True})


def _to_car_once(doc, spots_mm, route, rev, annotation, min_rows, min_cols, mode, strat):
    for k in ("connectors", "terminals"):      # label sides are chosen afresh (the layout does not depend on an old one)
        for e in doc.get(k, []): e.pop("layoutLabelPosition", None)
    T = _Tree(doc); T.s = annotation; T.textmode = mode
    got = _car_layout(T, spots_mm, route, rev, strat)
    pos, paths, stats = got
    R = T.R
    bundles = {b["id"]: b for b in doc.get("bundles", [])}
    shape = stats.pop("_shape")
    _mated_caps(T, pos, shape)
    for i, p in pos.items():
        if i in T.el: T.el[i]["layoutPosition"] = {"x": _r2(p[0] - HALF), "y": _r2(p[1] - HALF)}
    for bid, path in paths.items():
        b = bundles[bid]
        inner = path[1:-1]
        if inner:
            b["layoutPoints"] = [{"id": "%s_p%d" % (bid, i), "layoutPosition": {"x": _r2(q[0] - HALF), "y": _r2(q[1] - HALF)}} for i, q in enumerate(inner)]
        else:
            b.pop("layoutPoints", None)
        b.pop("radius", None)
    for k in INLINE_KINDS:     # inline parts sit on their location node
        for e in doc.get(k, []):
            if e.get("layoutPosition") and e.get("locationId") in T.el:
                e["layoutPosition"] = dict(T.el[e["locationId"]]["layoutPosition"])
    # layout notes: above the harness and every text, left aligned, each clear of the next (they never cover the harness)
    xs, ys = [], []
    for _, poly, what in text_boxes(doc):
        if what == "note": continue      # the notes themselves are placed here
        x0, y0, x1, y1 = _pbb(poly); xs += [x0, x1]; ys += [y0, y1]
    xs += [p[0] for p in pos.values()]; ys += [p[1] for p in pos.values()]
    xs += [q[0] for v in paths.values() for q in v]; ys += [q[1] for v in paths.values() for q in v]
    top, left = min(ys) - 30, min(xs)
    for n in reversed(doc.get("layoutNotes", []) or []):
        n["layoutPosition"] = {"x": 0.0, "y": 0.0}
        h = _pbb(note_box(n, annotation))[3]
        top -= h
        n["layoutPosition"] = {"x": _r2(left), "y": _r2(top)}
        top -= 20
    if label_overlaps(doc):
        repair_labels(doc)
    if label_overlaps(doc):
        repair_spokes(doc)
    fit_grid(doc, min_rows, min_cols)
    stats["mode"], stats["strategy"] = mode, strat
    return stats


def _mated_caps(T, pos, shape):
    """mated plugs that carry no bundle (bussed receptacle caps, the CAN-Lambda terminator plug) face to face with their plug,
    turned or moved out only as far as their label needs (Dan 2026-11-13)"""
    for m in T.doc.get("mates", []) or []:
        for a, c in ((m["sourceId"], m["targetId"]), (m["targetId"], m["sourceId"])):
            if a in pos and c not in pos and c in T.el:
                par = next((p for p, b in T.adj.get(a, []) if b is not None and p in pos), None)
                d = (pos[a][0] - pos[par][0], pos[a][1] - pos[par][1]) if par else (1, 0)
                L = math.hypot(*d) or 1
                ce, hit = T.el[c], None
                was_side = ce.get("layoutLabelPosition")
                for dist in (45, 60, 75, 90, 120, 160, 200, 260):
                    for rot in (0, 30, -30, 60, -60, 90, -90, 120, -120, 180):
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
                    hit = ((pos[a][0] + 45 * d[0] / L, pos[a][1] + 45 * d[1] / L), None)
                pos[c] = hit[0]
                if hit[1]: shape.add(hit[1])


def _car_layout(T, spots_mm, route, rev, strat=None):
    """(positions, bundle paths, stats) of the car-frame layout; AssertionError when a part finds no clear place"""
    R = T.R
    strat = strat or {}
    all_late = set()
    U = lambda p: (p[0] / MM_PER_UNIT, p[1] / MM_PER_UNIT)
    spot = {n: U(spots_mm[rev[n]]) for n in T.adj if n in rev and rev[n] in spots_mm}
    free = {n for n in spot if rev[n] in getattr(route, "free", ())}     # a borrowed spot (the glove-box breakouts, A35)
    bundles = [b for b in T.doc.get("bundles", [])]
    badj = {}
    for b in bundles:
        badj.setdefault(b["sourceId"], []).append((b["targetId"], b)); badj.setdefault(b["targetId"], []).append((b["sourceId"], b))
    # pieces (bundles only); each piece's root: its spotted node with the most bundles
    left, pieces = set(badj), []
    while left:
        nfree = {n for n in spot if rev[n] in getattr(route, "free", ())}
        cand = sorted([n for n in left if n in spot and n not in nfree],
                      key=lambda n: (-sum(1 for c, _ in badj[n] if c in spot), n)) or sorted(left)
        root = cand[0]
        order, parent = [root], {root: None}
        for n in order:
            for c, b in badj[n]:
                if c not in parent: parent[c] = (n, b); order.append(c)
        pieces.append((root, order, parent)); left -= set(order)
    pieces.sort(key=lambda p: -len(p[1]))
    shape, pos, paths = Shape(), {}, {}
    stats = {"loops": [], "offsets": [], "pulled": [], "moved": {}, "pieces": len(pieces)}
    mated = {}
    for m in T.doc.get("mates", []) or []:
        mated[m["sourceId"]] = m["targetId"]; mated[m["targetId"]] = m["sourceId"]

    def din_of(n):
        """unit vector of the drawn way into n from its parent (None for a root)"""
        for bid, p in paths.items():
            b = T.bundle[bid]
            if b["targetId"] == n and len(p) > 1: return _unit(p[-2], p[-1])
            if b["sourceId"] == n and len(p) > 1 and T.parent_of.get(n) == b["targetId"]: return _unit(p[1], p[0])
        return None

    T.bundle = {b["id"]: b for b in bundles}
    T.parent_of = {}
    pending = []      # bundles whose service loop is drawn last: (bundle, parent, child, route as drawn, set length)
    deferred = []     # the free breakouts, drawn after the first fans
    budget, fail = [0], [None]

    def snap():
        return (len(shape.segs), len(shape.nodes), len(shape.texts), dict(pos), dict(paths), dict(theta), len(pending),
                {k: list(v) for k, v in stats.items() if isinstance(v, list)})

    def restore(sv):
        shape.segs[sv[0]:] = []; shape.nodes[sv[1]:] = []; shape.texts[sv[2]:] = []
        pos.clear(); pos.update(sv[3]); paths.clear(); paths.update(sv[4]); theta.clear(); theta.update(sv[5])
        pending[sv[6]:] = []
        for k, v in sv[7].items(): stats[k] = v

    def grow(n, parent, late):
        """draw every spotted child branch of n (depth first); a child that finds no clear drawing sends the search back
        to try its parent's next drawing (BACKTRACK tries in all)"""
        kids = [c for c in parent if parent[c] and parent[c][0] == n and c in spot and c not in late]
        size = lambda c: sum(1 for x in parent if _is_below(x, c, parent))
        for c in sorted(kids, key=lambda c: -size(c)):
            why, ok = [], False
            for opt in options(c, parent, why):
                sv = snap()
                commit(c, parent, opt)
                if grow(c, parent, late): ok = True; break
                restore(sv)
                budget[0] -= 1
                if budget[0] <= 0: break
            if not ok:
                if DEBUG and not why[3:]:
                    cp = Shape(); cp.add(shape); STATS["_fail"] = (cp, dict(pos), (n, c), [])
                if fail[0] is None or not why:
                    fail[0] = (n, c, parent[c][1]["id"], why)
                return False
        return True
    theta = {}        # degrees each placed node's subtree is turned from the car
    def options(n, parent, why):
        """every clear way to draw n's bundle from its placed parent, best first (n's route as the editor draws it, then the
        far end moved a little, then the route turned about the parent): (kind, path, shape piece, turn)"""
        p, b = parent[n]
        need = _mm(b["length"]) / MM_PER_UNIT
        r = route(rev[p], rev[n], _mm(b["length"])) if (p in rev and n in rev) else None
        base = [U(q) for q in r] if r else [spot[p], spot[n]]
        th = theta.get(p, 0.0)      # a branch turned to clear another (below) turns its whole subtree with it
        pts = [(pos[p][0] + v[0], pos[p][1] + v[1]) for v in (_rot((q[0] - spot[p][0], q[1] - spot[p][1]), th) for q in base)]
        pts[0] = pos[p]
        if math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) < 1e-6 and len(_dedupe(pts)) < 2:
            cands = []
        else:
            cands = _fit(pts, need, R)
        # a far end with no room on its route: straight off its parent, first the way its own subtree lies
        sub = [x for x in parent if x in spot and _is_below(x, n, parent)]
        cx, cy = _rot((sum(spot[x][0] for x in sub) / len(sub) - spot[n][0] if sub else 0.0,
                       sum(spot[x][1] for x in sub) / len(sub) - spot[n][1] if sub else 0.0), th)
        dirs = []
        # first the widest gap between the parent's own routes (a breakout the top view does not draw leaves its run
        # square off it, clear of the run), then the way the far end's own subtree lies
        pd = []
        for c2, b2 in badj[p]:
            if c2 == n or c2 not in spot: continue
            r2 = route(rev[p], rev[c2], _mm(b2["length"])) if (p in rev and c2 in rev) else None
            q2 = [U(q) for q in r2] if r2 else [spot[p], spot[c2]]
            q2 = [q for q in q2 if math.hypot(q[0] - spot[p][0], q[1] - spot[p][1]) > 1e-6]
            if q2: pd.append(_rot(_unit(spot[p], q2[0]), th))
        if pd: dirs.append(_widest_gap(pd))
        if math.hypot(cx, cy) > 1: dirs.append((cx / math.hypot(cx, cy), cy / math.hypot(cx, cy)))
        dirs += [_rot((1.0, 0.0), a) for a in range(0, 360, 30)]
        din = din_of(p)
        if din is not None: dirs = [d for d in dirs if d[0] * din[0] + d[1] * din[1] > -0.8]
        hair = False
        if not cands or len(_dedupe(pts)) < 2 or math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) < 2 * R:
            if n not in free and need * MM_PER_UNIT > 200:     # a drop: a hairpin by its spot first, else straight out
                cands = cands + list(_hairpins([pos[p]], need, R, dirs))
            cands = cands + _straight_cands(pos[p], need, R, dirs, 2000 if n in free else 200)
            # no room for a loop there: the far end set out straight at its whole length (an offset near the end)
            cands = cands + _straight_cands(pos[p], need, R, dirs, 100000)
        elif any(k == "loop" for k, _ in cands):
            hair = True
            # no room for a loop on the route: the far end moved on along its last leg instead
            q = _dedupe(pts)
            u = _unit(q[-2], q[-1])
            if u:
                mv = lambda d: q[:-1] + [(q[-1][0] + u[0] * d, q[-1][1] + u[1] * d)]
                d = _solve(lambda d: rounded_length(mv(d), R) - need, 0.0, need * 2 + 10)
                cands = cands + [("offset", mv(d))]
        def shifted():
            """the route moved a little off whatever it runs into (a shared corridor drawn twice): its far part shifted
            sideways or along, nearest first; the first point stays on the parent"""
            for rr in (12.0, 24.0, 40.0, 60.0, 90.0, 130.0, 180.0):
                for a in range(0, 360, 45):
                    o = _rot((rr, 0.0), a)
                    sp = [pts[0]] + [(q[0] + o[0], q[1] + o[1]) for q in pts[1:]]
                    for c in _fit(sp, need, R): yield c + (0,)
            # routes that cross in the car (one over the other at another height) cannot cross on a flat board: the
            # route turned about its parent, the least turn first
            for a in (10, -10, 20, -20, 30, -30, 45, -45, 60, -60, 90, -90, 120, -120, 150, -150, 180):
                c0 = pts[0]
                sp = [c0] + [(c0[0] + v[0], c0[1] + v[1]) for v in (_rot((q[0] - c0[0], q[1] - c0[1]), a) for q in pts[1:])]
                for c in _fit(sp, need, R): yield c + (a,)
                for c in _straight_cands(pos[p], need, R, [_unit(c0, sp[-1])] if _unit(c0, sp[-1]) else [], 2000): yield c + (a,)
            if hair:      # last: a hairpin at the far end of the route as the editor draws it
                for c in _hairpins(pts, need, R, dirs): yield c + (0,)
        def expand(items):
            """with the inline-loops strategy a loop candidate is drawn with its teeth now (the search can back out of it)"""
            for kind, path, turn in items:
                if kind == "loop" and strat.get("inline_loops"):
                    for k2, p2 in itertools.islice(_loops(_dedupe(path), need, R), 24): yield (k2, p2, turn)
                else: yield (kind, path, turn)
        for kind, path, turn in expand(itertools.chain(((k, q, 0) for k, q in cands), shifted())):
            path = _dedupe(path)
            if len(path) < 2 or (kind != "loop" and abs(rounded_length(path, R) - need) > 0.5): continue
            own = Shape()
            own.segs = [(path[i], path[i + 1], (p, n), b["id"]) for i in range(len(path) - 1)]
            if n not in T.bps: own.nodes.append((path[-1], n))
            own.texts = [] if kind == "loop" else T.bundle_texts(b, path if b["sourceId"] == p else path[::-1])
            hit = clash(own, shape, dict(pos, **{n: path[-1]}))
            if hit is None: yield (kind, path, own, th + turn)
            elif len(why) < 3: why.append(hit)

    def commit(n, parent, opt):
        p, b = parent[n]
        kind, path, own, th = opt
        need = _mm(b["length"]) / MM_PER_UNIT
        theta[n] = th
        shape.add(own)
        pos[n] = path[-1]
        paths[b["id"]] = path if b["sourceId"] == p else path[::-1]
        if kind == "loop": pending.append((b, p, n, path, need))
        elif kind.startswith("loop"): stats["loops"].append((b["id"], int(kind[4:])))
        elif kind == "offset": stats["offsets"].append(b["id"])
        elif kind == "pulled": stats["pulled"].append(b["id"])

    for root, order, parent in pieces:
        # a piece joined to one already drawn by a mate (the RADLOK firewall pairs) is shifted so the mated plugs can face
        # each other; any other piece sits on its own spots
        shift = (0.0, 0.0)
        link = [(x, mated[x]) for x in order if x in mated and T.parent_of.get(mated[x]) in pos]
        if link and pos:
            a, b = link[0]
            pa = parent[a][0] if parent.get(a) else None
            need = sum(_mm(badj[x][0][1]["length"]) / MM_PER_UNIT for x in (a, b) if badj.get(x)) + 45.0
            if pa in spot:
                best = None
                for ang in range(0, 360, 15):
                    u = _rot((1.0, 0.0), ang)
                    sh = (pos[T.parent_of[b]][0] + u[0] * need - spot[pa][0], pos[T.parent_of[b]][1] + u[1] * need - spot[pa][1])
                    tr = Shape(); tr.nodes = [((spot[x][0] + sh[0], spot[x][1] + sh[1]), x) for x in order if x in spot and x not in T.bps]
                    for x in order:
                        if x in spot and parent[x] and parent[x][0] in spot:
                            tr.segs.append(((spot[parent[x][0]][0] + sh[0], spot[parent[x][0]][1] + sh[1]), (spot[x][0] + sh[0], spot[x][1] + sh[1]), (parent[x][0], x), parent[x][1]["id"]))
                    hitc = clash(tr, shape, dict(pos, **{x: (spot[x][0] + sh[0], spot[x][1] + sh[1]) for x in order if x in spot}), clr=4 * CLR, gap=4 * NODE_GAP)
                    cost = math.hypot(*sh) + (1e6 if hitc else 0)
                    if best is None or cost < best[0]: best = (cost, sh)
                shift = best[1]
        # the editor routes first; the free glove-box breakouts later (after the fans of the rest), wherever they have room
        late = {x for x in order if x in free and all(y in free or y not in spot for y in order if _is_below(y, x, parent))} \
            if strat.get("defer", True) else set()
        all_late.update(late)
        for n in order:
            if parent[n] and parent[n][0] not in late: T.parent_of[n] = parent[n][0]
        assert root in spot, "piece root %s has no editor spot" % root
        pos[root] = (spot[root][0] + shift[0], spot[root][1] + shift[1])
        if root not in T.bps: shape.nodes.append((pos[root], root))
        budget[0] = BACKTRACK
        assert grow(root, parent, late), "no clear drawing for the bundle %s -> %s (%s; first clashes %s)" % fail[0]
        for n in order:
            if n in late and parent[n][0] not in late: deferred.append((n, parent))
    # end stubs fanned round their nodes, the most crowded first; the way they lean: the generator's comb, else the widest gap
    fans = {}
    for root, order, parent in pieces:
        for n in order:
            if parent[n] and n not in spot:
                fans.setdefault(parent[n][0], []).append((n, parent[n][1]))
    def draw_loops():
        # service loops last, each where it has room (clear of every bundle, part and text already on the board)
        for b, p, n, base, need in sorted(pending, key=lambda x: -x[4]):
            shape.segs = [x for x in shape.segs if x[3] != b["id"]]
            done, why = None, []
            for kind, path in itertools.chain(_loops(base, need, R), _loops(base, need, R, prefer_end=False)):
                path = _dedupe(path)
                if abs(rounded_length(path, R) - need) > 0.5: continue
                own = Shape()
                own.segs = [(path[i], path[i + 1], (p, n), b["id"]) for i in range(len(path) - 1)]
                own.texts = T.bundle_texts(b, path if b["sourceId"] == p else path[::-1])
                hit = clash(own, shape, pos)
                if hit is None: done = (kind, path, own); break
                if len(why) < 3: why.append(hit)
            if not done and T.textmode != "none":       # no clear loop with its length label: without the label (the gate says)
                for kind, path in _loops(base, need, R):
                    path = _dedupe(path)
                    own = Shape(); own.segs = [(path[i], path[i + 1], (p, n), b["id"]) for i in range(len(path) - 1)]
                    if abs(rounded_length(path, R) - need) <= 0.5 and clash(own, shape, pos) is None: done = (kind, path, own); break
            assert done, "no room for the service loop of %s (%s -> %s; first clashes %s)" % (b["id"], p, n, why)
            kind, path, own = done
            shape.add(own)
            paths[b["id"]] = path if b["sourceId"] == p else path[::-1]
            stats["loops"].append((b["id"], int(kind[4:])))

    def lean(n, at):
        """point n's end stubs (T.old) the way they should lean: a mate's partner, a box's side (A35), else the widest gap"""
        dirs = [_unit(at, paths[b["id"]][1] if b["sourceId"] == n else paths[b["id"]][-2])
                for c, b in badj[n] if b["id"] in paths]
        gap_dir = _widest_gap([d for d in dirs if d])
        for c, b in fans[n]:
            pref = PREFER.get(n)
            if c in mated and T.parent_of.get(mated[c]) in pos:
                pref = _unit(at, pos[T.parent_of[mated[c]]]) or pref
            if pref is None: pref = gap_dir
            L = _mm(b["length"]) / MM_PER_UNIT
            T.old[c] = (T.old.get(n, (0.0, 0.0))[0] + pref[0] * L, T.old.get(n, (0.0, 0.0))[1] + pref[1] * L)

    def refan(n):
        """a device node whose ends cannot all stand clear where its route puts it: its bundle turned about its parent
        (its length kept), the least turn first, until the whole fan stands clear (the node then sits off its spot)"""
        p = T.parent_of.get(n)
        b = next((bb for c, bb in badj[n] if c == p), None)
        if b is None or b["id"] not in paths: return False
        cur = paths[b["id"]] if b["sourceId"] == p else paths[b["id"]][::-1]
        pend = next((i for i, x in enumerate(pending) if x[0]["id"] == b["id"]), None)
        base = Shape()
        base.segs = [x for x in shape.segs if x[3] != b["id"]]
        base.nodes = [x for x in shape.nodes if x[1] != n]
        base.texts = [x for x in shape.texts if x[1] != b["id"]]
        c0 = cur[0]
        for a in (15, -15, 30, -30, 45, -45, 60, -60, 90, -90, 120, -120, 150, -150, 180):
            path = [c0] + [(c0[0] + v[0], c0[1] + v[1]) for v in (_rot((q[0] - c0[0], q[1] - c0[1]), a) for q in cur[1:])]
            own = Shape()
            own.segs = [(path[i], path[i + 1], (p, n), b["id"]) for i in range(len(path) - 1)]
            if n not in T.bps: own.nodes.append((path[-1], n))
            own.texts = [] if pend is not None else T.bundle_texts(b, path if b["sourceId"] == p else path[::-1])
            if clash(own, base, dict(pos, **{n: path[-1]})) is not None: continue
            trial = Shape(); trial.add(base); trial.add(own)
            tpos, tpaths = dict(pos), dict(paths)
            tpos[n] = path[-1]; tpaths[b["id"]] = path if b["sourceId"] == p else path[::-1]
            was_paths = paths[b["id"]]; paths[b["id"]] = tpaths[b["id"]]
            lean(n, path[-1])
            ok = _spokes_at(T, trial, tpos, tpaths, n, path[-1], fans[n], _unit(path[-2], path[-1]))
            paths[b["id"]] = was_paths
            if ok:
                shape.segs[:] = trial.segs; shape.nodes[:] = trial.nodes; shape.texts[:] = trial.texts
                pos.update(tpos); paths.update(tpaths)
                if pend is not None: pending[pend] = (b, p, n, path, pending[pend][4])
                return True
        lean(n, pos[n])
        return False

    def do_fan(n):
        spokes = fans[n]
        at = pos[n]
        lean(n, at)
        was = T.textmode
        ok = _spokes_at(T, shape, pos, paths, n, at, spokes, din_of(n))
        tree_leaf = n in spot and T.parent_of.get(n) in pos and not any(c in spot for c, _ in badj[n] if c != T.parent_of[n])
        if not ok and tree_leaf and was == "all" and refan(n):
            ok = True; stats.setdefault("turned_for_labels", []).append(n)
        mode = was
        if not ok:
            for mode in [m for m in ("labels", "none") if ("all", "labels", "none").index(m) > ("all", "labels", "none").index(was)]:
                T.textmode = mode      # a fan that cannot keep every text clear keeps what it can (repair_labels, the gate after)
                ok = _spokes_at(T, shape, pos, paths, n, pos[n], spokes, din_of(n))
                if ok: break
            T.textmode = was
            if ok: stats.setdefault("fans_relaxed", []).append((n, mode))
        assert ok, "no clear spokes at %s (%d ends)" % (n, len(spokes))

    late_nodes = set(all_late)
    if strat.get("loops_first"): draw_loops()
    for n in sorted([x for x in fans if x not in late_nodes and x in pos], key=lambda n: -len(fans[n])):
        do_fan(n)
    for n, parent in deferred:
        T.parent_of[n] = parent[n][0]
        budget[0] = BACKTRACK
        fail[0] = None
        why = []
        opt = next(options(n, parent, why), None)
        assert opt, "no clear drawing for the bundle %s -> %s (%s; first clashes %s)" % (parent[n][0], n, parent[n][1]["id"], why)
        commit(n, parent, opt)
        assert grow(n, parent, set()), "no clear drawing for the bundle %s -> %s (%s; first clashes %s)" % fail[0]
    for n in sorted([x for x in fans if x in late_nodes], key=lambda n: -len(fans[n])):
        do_fan(n)
    if not strat.get("loops_first"): draw_loops()
    # how far each spotted node sits from its editor spot (the whole board moves as one, so the root's offset is none)
    for n, s in spot.items():
        if n in pos and n not in free: stats["moved"][n] = math.hypot(pos[n][0] - s[0], pos[n][1] - s[1]) * MM_PER_UNIT
    stats["_shape"] = shape
    return pos, paths, stats


def _is_below(x, n, parent):
    while x is not None:
        if x == n: return True
        x = parent[x][0] if parent.get(x) else None
    return False


def _widest_gap(dirs):
    """the unit vector in the middle of the widest angle between the given directions (any direction when there are none)"""
    if not dirs: return (1.0, 0.0)
    a = sorted(math.atan2(d[1], d[0]) for d in dirs)
    best = None
    for i, x in enumerate(a):
        y = a[(i + 1) % len(a)] + (2 * math.pi if i == len(a) - 1 else 0)
        if best is None or y - x > best[0]: best = (y - x, (x + y) / 2)
    return (math.cos(best[1]), math.sin(best[1]))


def fit_grid(doc, min_rows=MIN_ROWS, min_cols=MIN_COLS):
    """the panel grid (at least min_rows x min_cols panels of the doc's size, landscape) round everything drawn, centred on it"""
    fb = doc["formboard"]
    pw, ph = _mm(fb["panelWidth"]), _mm(fb["panelHeight"])
    m = 20 / MM_PER_UNIT
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
    fb.update({"panelOrientation": "Landscape", "columns": max(min_cols, math.ceil(w / pw)), "rows": max(min_rows, math.ceil(h / ph))})
    return doc


def route_deviation(doc, frame, layout_nodes):
    """{bp id: mm} how far each branch point with an editor spot sits from it, the board's own shift taken out (the median
    offset: most nodes sit exactly on their spots); plus (mean, max)"""
    import re as _re
    spots_mm, _ = frame
    rev = {"bp_" + _re.sub(r"[^A-Za-z0-9]", "_", n): n for n in layout_nodes}
    pts = []
    for e in doc.get("branchPoints", []):
        n = rev.get(e["id"])
        if n in spots_mm and e.get("layoutPosition") and n not in getattr(frame[1], "free", ()):
            c = _centre(e)
            pts.append((e["id"], (c[0] * MM_PER_UNIT, c[1] * MM_PER_UNIT), spots_mm[n]))
    if not pts: return {}, (0.0, 0.0)
    offs = [(d[0] - s[0], d[1] - s[1]) for _, d, s in pts]      # the board's shift: the offset most nodes share (medoid)
    ox, oy = min(offs, key=lambda o: sum(math.hypot(o[0] - q[0], o[1] - q[1]) for q in offs))
    dev = {i: math.hypot(d[0] - s[0] - ox, d[1] - s[1] - oy) for i, d, s in pts}
    return dev, (sum(dev.values()) / len(dev), max(dev.values()))


def report(doc, frame, layout_nodes):
    """the printed formboard metric (Dan 2026-11-15): board and panel grid, annotation scale, how far the branch points sit
    from their layout-editor spots (mean / max mm, the board's own shift taken out), the service loops of the last to_car run
    and the label overlaps left (the accepted over-capacity fan, A43 c)"""
    w, h, n, fb = board(doc)
    _, (mean, mx) = route_deviation(doc, frame, layout_nodes)
    loops = STATS.get("loops", [])
    return ("formboard %dx%d mm, %d rows x %d columns of A1 landscape panels, annotation %.2f; editor-route deviation mean %.0f mm, "
            "max %.0f mm; %d service loop(s) %s; %d offset end(s); label overlaps left %d (over-capacity fan)"
            % (w, h, fb["rows"], fb["columns"], fb.get("annotationScale", 1), mean, mx, len(loops),
               ", ".join("%s x%d" % lp for lp in loops), len(STATS.get("offsets", [])), len(cannot_fit(doc))))
