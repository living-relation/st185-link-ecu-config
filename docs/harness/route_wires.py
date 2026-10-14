"""Route every schematic wire of a .harness file on the half-grid so no two wires overlap
(Daniel, 2026-10-14, DECISIONS R86). Writes each wire's `layoutPoints` (cable cores:
`sourceLayoutPoints` / `targetLayoutPoints`). Node positions stay, except that a busy splice
with no room around it, or an inline node (cable, resistor, diode) drawn on or against another
node, is moved to the nearest
clear spot (schematic only).

    python docs/harness/route_wires.py rebuild/ST185-CabinPower.harness [...]   # write
    python docs/harness/route_wires.py --check rebuild/ST185-CabinPower.harness  # dry run
    (-v prints each routing round)

How: the harness.design app draws a wire as straight lines from the pin, through each waypoint
centre, to the far pin (`wire_paths.py`). Waypoints sit on the 30-unit grid, so their centres and
every pin row fall on the half-grid (15 + 30 n). Every wire is routed on that half-grid lattice,
right angles only (the hop that leaves or enters a splice may also slant, at 45 or 26.6 degrees,
so up to 16 wires fan into one splice from different directions):

  - a lattice edge carries one wire; a lattice point carries one wire, except that two wires may
    cross there straight through at right angles. So parallel runs are always >= 30 apart (the
    rule needs 12) and nothing overlaps.
  - points inside a node or note are blocked; points next to a node or on another pin's lead-out
    cost extra, so wires keep clear of other pins.
  - each pin may leave from either side of its node (the app picks the side from the first
    waypoint); a splice is reached from any free neighbour.
  - negotiated congestion (PathFinder): all wires are routed with soft penalties for sharing;
    clashing wires are ripped up and re-routed with rising penalties until nothing clashes.

Docs: https://docs.harness.design/files/harness/wiring.md (`layoutPoints`) and positioning.md
("avoid waypoints unless a route needs one" - with Daniel's spacing rule every route needs them;
only the lead-out points and corners are written). Gate: `audit_wire_spacing.py`.
"""
import heapq
import json
import math
import os
import sys

import audit_drawing_rules
import wire_paths as wp

G, H = wp.GRID, wp.HALF
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIAG = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
KNIGHT = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
SLANT = DIAG + KNIGHT        # only on the hop that leaves or enters a splice
BEND, CROSS, NEAR, PINROW = 4.0, 3.0, 2.0, 6.0


def note_box(n):
    w = n.get("width") or 270
    chars = max(1, w // 7)
    lines = sum(max(1, math.ceil(len(l) / chars)) for l in (n.get("text") or "").split("\n"))
    return w, 30 + 18 * lines


def to_lat(x, y):
    return (int(round((x - H) / G)), int(round((y - H) / G)))


def to_xy(p):
    return (p[0] * G + H, p[1] * G + H)


class Router:
    def __init__(self, d):
        self.d = d
        self.ns = wp.nodes(d)
        self.blocked = set()
        self.near = set()
        boxes = [n.box() for n in self.ns.values()]
        for nt in d.get("schematicNotes", []):
            p = nt["schematicPosition"]
            w, h = note_box(nt)
            boxes.append((p["x"], p["y"], p["x"] + w, p["y"] + h))
        m = 12
        lo = to_lat(min(b[0] for b in boxes), min(b[1] for b in boxes))
        hi = to_lat(max(b[2] for b in boxes), max(b[3] for b in boxes))
        self.lo, self.hi = (lo[0] - m, lo[1] - m), (hi[0] + m, hi[1] + m)
        for b in boxes:
            i0, j0 = math.ceil((b[0] - H) / G), math.ceil((b[1] - H) / G)
            i1, j1 = math.floor((b[2] - H) / G), math.floor((b[3] - H) / G)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    x, y = to_xy((i, j))
                    if b[0] < x < b[2] and b[1] < y < b[3]:
                        self.blocked.add((i, j))
            for i in range(i0 - 1, i1 + 2):
                for j in range(j0 - 1, j1 + 2):
                    self.near.add((i, j))
        self.edges = {}        # lattice edge -> [line ids]
        self.pts = {}          # lattice point -> [(line id, mode H / V / X, end key or None)]
        self.pinrows = set()
        self.hist, self.pres = {}, 0.6

    # ---- ends -------------------------------------------------------------------------------
    def ends(self, eid, handle):
        """[(lattice point, direction pointing away from the node, or None for a splice)]."""
        n = self.ns[eid]
        c = wp.handle_center(n, handle)
        b = n.box()
        if handle == "Splice":
            return [(to_lat(*c), None)]
        if n.rot:
            sides = {"Left": ["B"], "Right": ["T"]}.get(handle, ["T", "B"])
        else:
            sides = {"Left": ["L"], "Right": ["R"]}.get(handle, ["L", "R"])
        out = []
        for s in sides:
            if s == "L":
                out.append((to_lat(b[0] - H, c[1]), (-1, 0)))
            elif s == "R":
                out.append((to_lat(b[2] + H, c[1]), (1, 0)))
            elif s == "T":
                out.append((to_lat(c[0], b[1] - H), (0, -1)))
            else:
                out.append((to_lat(c[0], b[3] + H), (0, 1)))
        return out

    # ---- occupancy: soft while negotiating ---------------------------------------------------
    def _clash(self, p, mode, lid, keyset, endpoint):
        others = [u for u in self.pts.get(p, ()) if u[0] != lid
                  and not (endpoint and u[2] is not None and u[2] in keyset)]
        if not others or (len(others) == 1 and {mode, others[0][1]} == {"H", "V"}):
            return 0, bool(others)
        return len(others), True

    def _pt_cost(self, p, mode, lid, keyset, endpoint):
        n, crossed = self._clash(p, mode, lid, keyset, endpoint)
        h = self.hist.get(p, 0.0)
        return h + (self.pres * n * (1 + h) if n else (CROSS if crossed else 0.0))

    def _edge_cost(self, e, lid):
        n = sum(1 for u in self.edges.get(e, ()) if u != lid)
        h = self.hist.get(e, 0.0)
        return h + (self.pres * n * (1 + h) if n else 0.0)

    # ---- search -----------------------------------------------------------------------------
    def search(self, lid, starts, goals, keyset):
        goal = {g[0]: g for g in goals}
        gl = list(goal)

        def h(p):   # weighted (1.2) for speed; routes stay near-shortest
            return 1.2 * min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in gl)

        pq, best, prev = [], {}, {}
        for p, dr in starts:
            st = (p, dr)
            c0 = self._pt_cost(p, "X", lid, keyset, True)
            best[st], prev[st] = c0, None
            heapq.heappush(pq, (c0 + h(p), c0, st))
        while pq:
            _, gc, st = heapq.heappop(pq)
            if best.get(st, 1e18) < gc:
                continue
            p, din = st
            if p in goal and prev[st] is not None:
                return self._unwind(prev, st)
            first = prev[st] is None
            for dv in DIRS + SLANT:
                diag = dv in SLANT
                q = (p[0] + dv[0], p[1] + dv[1])
                if not (self.lo[0] <= q[0] <= self.hi[0] and self.lo[1] <= q[1] <= self.hi[1]):
                    continue
                if diag and not ((first and din is None) or (q in goal and goal[q][1] is None)):
                    continue
                if q in self.blocked and q not in goal:
                    continue
                cost = gc + math.hypot(*dv) + self._edge_cost((min(p, q), max(p, q)), lid)
                if not first:
                    straight = din == dv and not diag
                    cost += self._pt_cost(p, ("H" if dv[1] == 0 else "V") if straight else "X", lid, keyset, False)
                    if not straight:
                        cost += BEND
                elif din is not None and din != dv:
                    cost += BEND
                if q in goal:
                    cost += self._pt_cost(q, "X", lid, keyset, True)
                else:
                    cost += (NEAR if q in self.near else 0.0) + (PINROW if q in self.pinrows else 0.0)
                nst = (q, dv)
                if cost < best.get(nst, 1e18):
                    best[nst], prev[nst] = cost, st
                    heapq.heappush(pq, (cost + h(q), cost, nst))
        return None

    @staticmethod
    def _unwind(prev, st):
        out = []
        while st is not None:
            out.append(st[0])
            st = prev[st]
        return out[::-1]

    @staticmethod
    def modes(path):
        out = []
        for k, p in enumerate(path):
            if k in (0, len(path) - 1):
                out.append("X")
                continue
            a, b = path[k - 1], path[k + 1]
            d1, d2 = (p[0] - a[0], p[1] - a[1]), (b[0] - p[0], b[1] - p[1])
            out.append(("H" if d1[1] == 0 else "V") if d1 == d2 and d1 not in SLANT else "X")
        return out

    def commit(self, lid, path, keys):
        for a, b in zip(path, path[1:]):
            self.edges.setdefault((min(a, b), max(a, b)), []).append(lid)
        for k, (p, m) in enumerate(zip(path, self.modes(path))):
            ek = keys[0] if k == 0 else keys[1] if k == len(path) - 1 else None
            self.pts.setdefault(p, []).append((lid, m, ek))

    def uncommit(self, lid, path):
        for a, b in zip(path, path[1:]):
            self.edges[(min(a, b), max(a, b))].remove(lid)
        for p in set(path):
            self.pts[p] = [u for u in self.pts[p] if u[0] != lid]

    def conflicts(self):
        """(clashing line ids, overused edges / points)."""
        bad, over = set(), set()
        for e, ls in self.edges.items():
            if len(set(ls)) > 1:
                bad.update(ls)
                over.add(e)
        for p, us in self.pts.items():
            if len(us) < 2:
                continue
            if len(us) == 2 and {us[0][1], us[1][1]} == {"H", "V"}:
                continue
            for i, u in enumerate(us):
                for v in us[i + 1:]:
                    if u[0] != v[0] and not (u[2] is not None and u[2] == v[2]):
                        bad.update((u[0], v[0]))
                        over.add(p)
        return bad, over


def corners(path):
    return [path[k] for k in range(1, len(path) - 1)
            if (path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1])
            != (path[k + 1][0] - path[k][0], path[k + 1][1] - path[k][1])]


def jobs(d):
    """(line id, owner dict, layout key, source end, target end) - every wire and cable section."""
    for w in d.get("wires", []):
        yield w["id"], w, "layoutPoints", (w["source"]["id"], w["source"]["handle"]), (w["target"]["id"], w["target"]["handle"])
    for c in d.get("cables", []):
        for co in c.get("cores", []) + ([c["shield"]] if c.get("shield") else []):
            for end, key in (("source", "sourceLayoutPoints"), ("target", "targetLayoutPoints")):
                if co.get(end):
                    yield "%s/%s" % (co["id"], end), co, key, (c["id"], co["id"]), (co[end]["id"], co[end]["handle"])


def route(d, iters=80, log=None):
    """Negotiated-congestion routing. Returns ({line id: (owner, key, lattice path)}, [clashing])."""
    r = Router(d)
    js = [j for j in jobs(d) if j[3][0] in r.ns and j[4][0] in r.ns]
    for j in js:
        for e in (j[3], j[4]):
            for p, dv in r.ends(*e):
                if dv:
                    r.pinrows.update((p, (p[0] + dv[0], p[1] + dv[1])))

    def span(j):
        a = wp.handle_center(r.ns[j[3][0]], j[3][1])
        b = wp.handle_center(r.ns[j[4][0]], j[4][1])
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    byid = {j[0]: j for j in js}
    paths, unroutable = {}, set()
    todo = [j[0] for j in sorted(js, key=span)]
    for it in range(iters):
        for lid in todo:
            j = byid[lid]
            if lid in paths:
                r.uncommit(lid, paths.pop(lid))
            keys = (j[3], j[4])
            path = r.search(lid, r.ends(*j[3]), r.ends(*j[4]), set(keys))
            if path:
                r.commit(lid, path, keys)
                paths[lid] = path
            else:
                unroutable.add(lid)
        bad, over = r.conflicts()
        if log:
            log("  round %d: %d clashing" % (it + 1, len(bad)))
        if not bad:
            break
        for x in over:
            r.hist[x] = r.hist.get(x, 0.0) + 1.0
        r.pres *= 1.4
        todo = sorted(bad, key=lambda l: span(byid[l]))
    bad, _ = r.conflicts()
    return ({lid: (byid[lid][1], byid[lid][2], p) for lid, p in paths.items()},
            sorted(unroutable | bad))


def owner_is_splice(owner, key, which):
    """Is the start / end of this line a splice?"""
    if key == "layoutPoints":
        return (owner["source"] if which == "start" else owner["target"])["handle"] == "Splice"
    if which == "start":
        return False                        # a cable-core section starts at the cable
    return (owner["source"] if key == "sourceLayoutPoints" else owner["target"])["handle"] == "Splice"


def apply(result):
    for lid, (owner, key, path) in result.items():
        # the lead-out point next to a pin is always written: without it the app adds its own
        # stub and draws a diagonal. A splice end needs none (the line starts at its centre).
        pts = corners(path)
        if not owner_is_splice(owner, key, "start"):
            pts = [path[0]] + [p for p in pts if p != path[0]]
        if not owner_is_splice(owner, key, "end"):
            pts = [p for p in pts if p != path[-1]] + [path[-1]]
        base = lid.replace("/", "_")
        owner[key] = [{"id": "%s_lp%d" % (base, k + 1),
                       "schematicPosition": {"x": to_xy(p)[0] - H, "y": to_xy(p)[1] - H}}
                      for k, p in enumerate(pts)]


def free_splices(d):
    """Move a splice whose free neighbour points are fewer than its wires + 1 (or, with 4+ wires,
    that has anything within two lattice steps - three with 5+ wires, four with 7+; another splice's first ring
    counts as taken) to the nearest grid spot that is that clear (schematic only; its layout
    position is kept)."""
    deg, moved = {}, []
    for lid, owner, key, s, t in jobs(d):
        for e in (s, t):
            if e[1] == "Splice":
                deg[e[0]] = deg.get(e[0], 0) + 1

    def ring(p, k):
        return [(p[0] + i, p[1] + j) for i in range(-k, k + 1) for j in range(-k, k + 1) if (i, j) != (0, 0)]

    for sp in d.get("splices", []):
        n = deg.get(sp["id"], 0)
        if n < 3:
            continue
        r = Router(d)
        c = to_lat(sp["schematicPosition"]["x"] + H, sp["schematicPosition"]["y"] + H)
        r.blocked.discard(c)
        for o in d.get("splices", []):          # other splices keep their own first ring
            if o is not sp:
                oc = to_lat(o["schematicPosition"]["x"] + H, o["schematicPosition"]["y"] + H)
                r.blocked.update(ring(oc, 1))
        k = 4 if n >= 7 else 3 if n >= 5 else 2
        free = [q for q in ring(c, 1) if q not in r.blocked]
        if len(free) >= min(8, n + 1) and (n < 4 or not any(q in r.blocked for q in ring(c, k))):
            continue
        best = None
        for rad in range(1, 60):
            for i in range(-rad, rad + 1):
                for j in range(-rad, rad + 1):
                    p = (c[0] + i, c[1] + j)
                    if max(abs(i), abs(j)) != rad or p in r.blocked or any(q in r.blocked for q in ring(p, k)):
                        continue
                    if best is None or abs(i) + abs(j) < best[0]:
                        best = (abs(i) + abs(j), p)
            if best:
                break
        if best:
            sp.setdefault("layoutPosition", dict(sp["schematicPosition"]))
            x, y = to_xy(best[1])
            sp["schematicPosition"] = {"x": x - H, "y": y - H}
            moved.append(sp["id"])
    return moved


def free_inline(d):
    """Move an inline node (cable, resistor, diode) that sits on top of, or within 60 sideways /
    30 up-down of, another node or note to the nearest clear spot to the middle of its wire ends
    (schematic only). Closer than that, its lead-out points coincide with its neighbour's."""
    ends_of = {}
    for lid, owner, key, s, t in jobs(d):
        for a, b in ((s, t), (t, s)):
            ends_of.setdefault(a[0], []).append(b)
    for w in d.get("wires", []):
        for a, b in ((w["source"], w["target"]), (w["target"], w["source"])):
            ends_of.setdefault(a["id"], []).append((b["id"], b["handle"]))
    moved = []
    items = [(c, "cable") for c in d.get("cables", [])]
    items += [(x, "resistor") for x in d.get("resistors", [])] + [(x, "diode") for x in d.get("diodes", [])]
    for el, kind in items:
        ns = wp.nodes(d)
        me = ns[el["id"]]
        # the overlap gate's boxes (audit_drawing_rules G3; a little larger than the app's)
        others = [(x, y, x + w, y + h) for nid, x, y, w, h in audit_drawing_rules.boxes(d) if nid != el["id"]]
        others += [n.box() for n in ns.values() if n.id != el["id"]]
        bw, bh = me.box()[2] - me.box()[0], me.box()[3] - me.box()[1]

        def clear(x, y, gx, gy):
            return not any(x - gx < o[2] and o[0] < x + bw + gx and y - gy < o[3] and o[1] < y + bh + gy
                           for o in others)

        if clear(me.x, me.y, 2 * G, G):
            continue
        ends = [wp.handle_center(ns[e[0]], e[1]) for e in ends_of.get(el["id"], []) if e[0] in ns and e[0] != el["id"]]
        cx = sum(p[0] for p in ends) / len(ends) if ends else me.x
        cy = sum(p[1] for p in ends) / len(ends) if ends else me.y
        gx0, gy0 = G * round((cx - bw / 2) / G), G * round((cy - bh / 2) / G)
        best = None
        for rad in range(0, 150):
            for i in range(-rad, rad + 1):
                for j in range(-rad, rad + 1):
                    if max(abs(i), abs(j)) != rad:
                        continue
                    x, y = gx0 + G * i, gy0 + G * j
                    if clear(x, y, 3 * G, 2 * G) and (best is None or abs(i) + abs(j) < best[0]):
                        best = (abs(i) + abs(j), x, y)
            if best:
                break
        if best:
            if kind != "cable":         # resistors / diodes: keep the layout view where it was
                el.setdefault("layoutPosition", dict(el["schematicPosition"]))
            el["schematicPosition"] = {"x": best[1], "y": best[2]}
            moved.append(el["id"])
    return moved


def strip(d):
    for lid, owner, key, s, t in jobs(d):
        owner.pop(key, None)


def main(argv):
    check = "--check" in argv
    files = [a for a in argv if not a.startswith("-")]
    here = os.path.dirname(os.path.abspath(__file__))
    rc = 0
    for fn in files:
        path = fn if os.path.exists(fn) else os.path.join(here, fn)
        with open(path, encoding="utf-8", newline="") as f:
            raw = f.read()
        nl = "\r\n" if "\r\n" in raw else "\n"     # keep the file's own line endings
        d = json.loads(raw)
        strip(d)
        moved = free_inline(d) + free_splices(d)
        res, failed = route(d, log=print if "-v" in argv else None)
        apply(res)
        print("%s: %d routed, %d clashing%s%s" % (
            os.path.basename(path), len(res), len(failed),
            (": " + ", ".join(failed[:20])) if failed else "",
            ("; moved " + ", ".join(moved)) if moved else ""))
        rc |= bool(failed)
        if not check:
            out = json.dumps(d, indent=2, ensure_ascii=False) + ("\n" if raw.endswith("\n") else "")
            out = out.replace("\n", nl)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write(out)
            os.replace(tmp, path)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
