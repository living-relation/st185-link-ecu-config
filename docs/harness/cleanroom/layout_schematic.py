"""Schematic layout for the clean-room A-cabin build (DECISIONS R200 ideas, Dan 2026-10-19).

Placement: parts stand where their wires run square and short.
  - ECU-A in the middle; its pins go LEFT (cabin ends: relays, A/C, pedal, front WS, grounds)
    or RIGHT (engine side: bulkhead, buses, splices that feed the bulkhead).
  - The DRB102 bulkhead is a rotated bar above ECU-A: an ECU wire into it is one square corner
    (the app's own rule for a rotated end facing a plain one). The sensor buses and the LOGIC-box
    feeds sit ABOVE the bar, so their wires enter it from the top and never cross the ECU wires.
  - A wire end level with its ECU pin (relay coils, the A/C cancel tap) draws as a straight line.
  - A splice sits beside the ECU pin it serves.
Squaring: a wire the app would draw with a diagonal (or through a part) gets the fewest routing
points that make it square and clear - R200: "Routing points are ok to get the last ones square".
`metrics()` reports crossings, diagonal stretches and lines through parts.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import wire_paths as wp  # noqa: E402

GRID = 30
ECU_W = 390
TERM_W = 390
NOTE_W = 270

# left side, x of the terminal column and of everything further out
X_TERM = -1110          # terminals (390 wide) end at -720
X_NOTE = X_TERM - 30 - NOTE_W
X_SPL = -330            # left splices
X_CAB = X_NOTE - 150    # cables
X_DEV = X_CAB - 420     # pedal / front WS inline tables
BAR_X = int(os.environ.get("CR_BAR_X", 900))   # bulkhead bar (rotated): x0 and top y, height 390;
BAR_Y = int(os.environ.get("CR_BAR_Y", 300))   # mid-height: ECU pins above enter from the top, below from the bottom
RIGHT = BAR_X + 30 * 102 + 180               # buses and feeds sit past the end of the bar

# Positions chosen by search() for the movable groups (bus plugs, LOGIC-box feeds); a trial
# run can override them through the CR_OVERRIDE environment variable (JSON).
import json  # noqa: E402
OVERRIDE = {"bus_gnd_bha_p": [1740, 1080], "bus_5v_bha_p": [2460, -480], "br_w_cop_pwr_c": [450, -330],
            "br_w_eps_rly": [2820, 1290], "br_w_inj_pwr_c": [450, -390], "sp_sw12": [480, 150],
            "sp_8v": [480, 180], "sp_trig2": [600, 270], "cam_pullup": [540, 270]}
OVERRIDE.update(json.loads(os.environ.get("CR_OVERRIDE", "{}")))


def row_y(k):
    """centre y of ECU-A row k (0-based) when ECU-A sits at y = 0."""
    return GRID * (k + 1.5)


def _ecu_rows(doc):
    ecu = next(c for c in doc["connectors"] if c["id"] == "ecu_a")
    return {cav.get("designation"): i for i, cav in enumerate(ecu["cavities"])}


def _peer(doc, node):
    """For a terminal / splice: the ECU-A pin designation it is wired to directly, if any."""
    rows = _ecu_rows(doc)
    ecu = next(c for c in doc["connectors"] if c["id"] == "ecu_a")
    cid = {cav["id"]: cav.get("designation") for cav in ecu["cavities"]}
    for w in doc["wires"]:
        for a, b in (("source", "target"), ("target", "source")):
            if w[a]["id"] == node and w[b]["id"] == "ecu_a":
                return rows[cid[w[b]["handle"]]]
    return None


def place(doc, attach=None):
    attach = attach or {}
    notes = {n["id"]: n for n in doc.get("schematicNotes", [])}
    pos = {}

    def put(nid, x, y):
        pos[nid] = (int(x), int(y))

    put("ecu_a", 0, 0)
    put("bh_a_fw", BAR_X, BAR_Y)
    # above the bar: buses (their caps beside them) and the LOGIC-box / EHPS feeds
    put("bus_gnd_bha_p", RIGHT, BAR_Y - 420)
    put("bus_gnd_bha_r", RIGHT + 330, BAR_Y - 420)
    put("bus_5v_bha_p", RIGHT, BAR_Y + 480)
    put("bus_5v_bha_r", RIGHT + 330, BAR_Y + 480)
    put("br_w_inj_pwr_c", RIGHT, BAR_Y - 720)
    put("br_w_cop_pwr_c", RIGHT, BAR_Y - 660)
    put("br_w_fb_mrs_en", RIGHT, BAR_Y - 840)
    put("br_w_eps_rly", RIGHT, BAR_Y - 780)
    # right splices + cam pull-up, level with their ECU pins
    put("sp_shield_a", 480, row_y(_peer(doc, "sp_shield_a")) - 15)
    # cam +8 V and cam signal splices with the pull-up between them, left of ECU-A (a part right of
    # ECU-A would stand in the bulkhead fan)
    put("sp_8v", X_SPL - 120, row_y(_peer(doc, "sp_8v")) - 15)
    put("sp_trig2", X_SPL - 120, row_y(_peer(doc, "sp_trig2")) - 15)
    put("cam_pullup", X_SPL - 240, row_y(_peer(doc, "sp_8v")) + 15)
    # left: ends level with their ECU pins
    for tid in ("fl_acamp_act", "br_w_fp85", "br_w81", "br_w_str85", "br_w76", "br_w_fan85"):
        put(tid, X_TERM, row_y(_peer(doc, tid)) - 15)
    # left splices level with their ECU pins (two columns so neighbours never touch)
    put("sp_sw12", X_SPL, row_y(_peer(doc, "sp_sw12")) - 15)
    put("sp_gndout", X_SPL, row_y(_peer(doc, "sp_gndout")) - 15)
    put("sp_chassis", X_SPL - 120, row_y(_peer(doc, "sp_chassis")) - 15)
    put("sp_5v", X_SPL, row_y(_peer(doc, "sp_5v")) - 15)
    # switched +12 V ends, above ECU-A on the left
    put("br_w_fb_sw12", X_TERM, -150)
    put("br_w_rail_sw12_b_c", X_TERM, -90)
    # ground ends below ECU-A on the left
    for i, tid in enumerate(("chassis_ring", "br_w_b25", "br_w_b34", "br_w_lamg_b", "br_w_csbg")):
        put(tid, X_TERM, 1170 + 60 * i)
    put("br_w_rail_5v_b_c", X_TERM, 1470)
    # pedal and front WS inline, far left, with their cables between them and the ECU
    put("aps", X_DEV, 330)
    put("cab_aps", X_CAB, 330)
    put("sp_5v_2", X_SPL - 300, 300)
    put("br_w39", X_DEV, 600)
    put("br_w_cru_5v", X_DEV - 450, 240)
    put("ix_ws_front_p", X_DEV, 780)
    put("cab_fspur", X_CAB, 780)
    put("cab_fspur_fr_ac", X_CAB, 1020)
    put("br_cab_fspur_r", X_DEV - 450, 1050)
    put("br_cab_fspur_fr_sh", X_DEV - 450, 1110)
    # A/C block, top left: pressure-switch splice with its three ends
    put("sp_ac_psw", X_TERM - 420, -510)
    put("br_ac_psw", X_TERM - 900, -570)
    put("fl_acamp_psw", X_TERM - 900, -450)
    put("br_w_acc86", X_TERM, -510)

    for k, v in OVERRIDE.items():  # positions found by search() (frozen below), or a trial
        if k in pos:
            put(k, *v)
        if k + "_r" in pos and k.endswith("_p"):
            pass
    for plug, cap in (("bus_gnd_bha_p", "bus_gnd_bha_r"), ("bus_5v_bha_p", "bus_5v_bha_r")):
        put(cap, pos[plug][0] + 330, pos[plug][1])  # a bussed cap stands beside its plug
    for coll in ("connectors", "terminals", "splices", "resistors", "cables"):
        for el in doc.get(coll, []):
            x, y = pos[el["id"]]
            el["schematicPosition"] = {"x": x, "y": y}
            el.pop("rotated", None)
            if el["id"] in ("ecu_a",):
                el["width"] = ECU_W
            elif el["id"] == "bh_a_fw":
                el["width"] = 390
                el["rotated"] = True
            elif coll == "terminals":
                el["width"] = TERM_W
            elif coll == "connectors":
                el["width"] = 270

    _place_notes(doc, notes, attach)
    route(doc)


def _note_h(note):
    per_line = max(1, note["width"] // 7)  # about 7 px a character
    lines = sum(-(-max(len(p), 1) // per_line) for p in note["text"].split("\n"))
    return GRID * -(-(lines * 18 + 20) // GRID)


# ends whose note goes on the left although their wire leaves to the right (the space right of
# them carries the +5 V bus line)
NOTE_LEFT = set()


def _wire_from_left(doc, ns, node):
    for w in doc.get("wires", []):
        for a, b in (("source", "target"), ("target", "source")):
            if w[a]["id"] == node and w[b]["id"] in ns:
                return ns[w[b]["id"]].x < ns[node].x
    return ns[node].x > 0


def _place_notes(doc, notes, attach):
    """End notes in a column just outside their end (left of a left-side end, right of an end
    above the bar), stacked so none overlaps; free notes top left."""
    ns = wp.nodes(doc)
    stacks = {}
    for node, nid in sorted(attach.items(), key=lambda kv: ns[kv[0]].y if kv[0] in ns else 0):
        n, el = notes[nid], ns.get(node)
        if el is None:
            continue
        # beside the end, on the side away from its wire
        right = _wire_from_left(doc, ns, node) and node not in NOTE_LEFT
        x = el.x + el.w + GRID if right else el.x - GRID - n["width"]
        if node == "aps":
            x, y0 = el.x, el.y - 3 * GRID
        else:
            y0 = el.y
        y = max(y0, stacks.get(x, -10 ** 9))
        n["schematicPosition"] = {"x": x, "y": y}
        stacks[x] = y + _note_h(n) + GRID
    free = [n for n in notes.values() if n["id"] not in attach.values()]
    y = -960  # above the A/C block
    for n in free:
        n["schematicPosition"] = {"x": X_DEV - 450, "y": y}
        y += _note_h(n) + GRID


# ---------------------------------------------------------------- squaring and metrics
def _segs(poly):
    return list(zip(poly, poly[1:])) if poly else []


def _diag(poly):
    return any(abs(q[0] - p[0]) > 0.5 and abs(q[1] - p[1]) > 0.5 for p, q in _segs(poly))


def _boxes(doc, ns):
    out = []
    for k, n in ns.items():
        x0, y0, x1, y1 = n.box()
        out.append((k, (x0, y0, x1, y1)))
    for nt in doc.get("schematicNotes", []):
        p = nt["schematicPosition"]
        out.append((nt["id"], (p["x"], p["y"], p["x"] + nt["width"], p["y"] + _note_h(nt))))
    return out


def _seg_hits_box(p, q, b):
    x0, y0, x1, y1 = b[0] + 2, b[1] + 2, b[2] - 2, b[3] - 2
    if abs(p[1] - q[1]) < 0.5:  # horizontal
        return y0 < p[1] < y1 and min(p[0], q[0]) < x1 and max(p[0], q[0]) > x0
    if abs(p[0] - q[0]) < 0.5:
        return x0 < p[0] < x1 and min(p[1], q[1]) < y1 and max(p[1], q[1]) > y0
    return False


def _through(poly, boxes, ends):
    return sum(1 for k, b in boxes if k not in ends for p, q in _segs(poly) if _seg_hits_box(p, q, b))


def _cross(a, b):
    """count proper crossings between two square polylines (shared points excluded)."""
    n = 0
    for p, q in _segs(a):
        for r, s in _segs(b):
            ph, rh = abs(p[1] - q[1]) < 0.5, abs(r[1] - s[1]) < 0.5
            if ph == rh:
                continue
            h, v = ((p, q), (r, s)) if ph else ((r, s), (p, q))
            x, y = v[0][0], h[0][1]
            if min(h[0][0], h[1][0]) < x < max(h[0][0], h[1][0]) and min(v[0][1], v[1][1]) < y < max(v[0][1], v[1][1]):
                n += 1
    return n


def _overlap(a, b):
    """length two lines share running on top of each other (collinear)."""
    t = 0
    for p, q in _segs(a):
        for r, s in _segs(b):
            if abs(p[1] - q[1]) < 0.5 and abs(r[1] - s[1]) < 0.5 and abs(p[1] - r[1]) < 0.5:
                t += max(0, min(max(p[0], q[0]), max(r[0], s[0])) - max(min(p[0], q[0]), min(r[0], s[0])))
            if abs(p[0] - q[0]) < 0.5 and abs(r[0] - s[0]) < 0.5 and abs(p[0] - r[0]) < 0.5:
                t += max(0, min(max(p[1], q[1]), max(r[1], s[1])) - max(min(p[1], q[1]), min(r[1], s[1])))
    return t


def _length(poly):
    return sum(abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in _segs(poly))


def _conductors(doc):
    """(owner dict, key for its points, source end, target end, net key) for every drawn line."""
    out = []
    for w in doc.get("wires", []):
        out.append((w, "layoutPoints", w["source"], w["target"]))
    for c in doc.get("cables", []):
        for co in c["cores"] + ([c["shield"]] if c.get("shield") else []):
            for end, key in (("source", "sourceLayoutPoints"), ("target", "targetLayoutPoints")):
                if co.get(end):
                    out.append((co, key, {"id": c["id"], "handle": co["id"]}, co[end]))
    return out


def _nets(doc):
    parent = {}

    def f(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            k = parent[k]
        return k

    def key(e):
        return (e["id"],) if e["handle"] in ("Splice",) else (e["id"], e["handle"])
    for w in doc.get("wires", []):
        parent[f(key(w["source"]))] = f(key(w["target"]))
    for c in doc.get("cables", []):
        for co in c["cores"] + ([c["shield"]] if c.get("shield") else []):
            ends = [key(co[e]) for e in ("source", "target") if co.get(e)] + [(c["id"], co["id"])]
            for a, b in zip(ends, ends[1:]):
                parent[f(a)] = f(b)
    return lambda e: f(key(e))


def _pt(x, y):
    return {"schematicPosition": {"x": int(x - 15), "y": int(y - 15)}}


def _snap(v):
    return GRID * round((v - 15) / GRID) + 15


def _outs(ns, e, other):
    """points just outside an end, on the side the app draws it leaving (half-grid); a splice
    has no side, so all four."""
    n = ns[e["id"]]
    c = wp.handle_center(n, e["handle"])
    side = wp.handle_side(n, e["handle"], c, other)
    loc = wp.handle_location(n, e["handle"], c, side)
    steps = {"L": [(-60, 0)], "R": [(60, 0)], "T": [(0, -60)], "B": [(0, 60)]}.get(
        side, [(-60, 0), (60, 0), (0, -60), (0, 60)])
    return [(_snap(loc[0] + dx), _snap(loc[1] + dy)) for dx, dy in steps]


# Trial only (CR_DODGE=1): also add routing points to lines that are already square, to dodge
# crossings. R200 does not allow that, so the drawing is never built this way.
DODGE = os.environ.get("CR_DODGE") == "1"


def route(doc):
    """Give every line that the app would draw diagonal (or through a part) the fewest routing
    points that make it square and clear; greedy, longest lines first."""
    ns = wp.nodes(doc)
    boxes = _boxes(doc, ns)
    net = _nets(doc)
    cons = _conductors(doc)
    for owner, key, *_ in cons:
        owner.pop(key, None)
    done = []  # (net, polyline)
    part_boxes = [(k, b) for k, b in boxes if k in ns]

    def score(poly, ends, n):
        if poly is None or _diag(poly):
            return None
        thr = _through(poly, boxes, ends)
        cr = sum(_cross(poly, p) for nn, p in done if nn != n)
        ov = sum(_overlap(poly, p) for nn, p in done if nn != n)
        return thr * 100000 + cr * 2000 + ov * 20 + _length(poly) + 60 * (len(poly) - 2)

    order = sorted(cons, key=lambda c: -_length(wp.path(ns, c[2], c[3], None) or []))
    for owner, key, s, t in order:
        n = net(t)
        ends = {s["id"], t["id"]}
        bare = wp.path(ns, s, t, None)
        best, best_pts = score(bare, ends, n), None
        if bare is not None and not _diag(bare) and not _through(bare, part_boxes, ends) and not DODGE:
            # already square and clear: R200 allows routing points only to square a line
            done.append((n, bare))
            continue
        P = wp.handle_center(ns[s["id"]], s["handle"])
        V = wp.handle_center(ns[t["id"]], t["handle"])
        xs = sorted({_snap(v) for v in [P[0], V[0]] + [P[0] + d for d in range(-1200, 1230, 60)]
                     + [V[0] + d for d in range(-1200, 1230, 60)]})
        ys = sorted({_snap(v) for v in [P[1], V[1]] + [P[1] + d for d in range(-1200, 1230, 60)]
                     + [V[1] + d for d in range(-1200, 1230, 60)]})
        cands = [[(P[0], V[1])], [(V[0], P[1])]]
        cands += [[(cx, P[1]), (cx, V[1])] for cx in xs]
        cands += [[(P[0], cy), (V[0], cy)] for cy in ys]
        # around an obstacle: out of each end, then over / under (or left / right of) it
        for ls in _outs(ns, s, V):
            for lt in _outs(ns, t, P):
                cands += [[(ls[0], P[1]), (ls[0], cy), (lt[0], cy), (lt[0], V[1])] for cy in ys]
                cands += [[(P[0], ls[1]), (cx, ls[1]), (cx, lt[1]), (V[0], lt[1])] for cx in xs]
        for pts in cands:
            pts = [(_snap(x), _snap(y)) for x, y in pts]
            poly = wp.path(ns, s, t, [_pt(*p) for p in pts])
            sc = score(poly, ends, n)
            if sc is not None and (best is None or sc < best):
                best, best_pts = sc, pts
        if best_pts:
            owner[key] = [dict(_pt(*p), id="%s_rp%d" % (owner["id"], i + 1)) for i, p in enumerate(best_pts)]
        done.append((n, wp.path(ns, s, t, owner.get(key))))


def metrics(doc):
    ns = wp.nodes(doc)
    boxes = _boxes(doc, ns)
    net = _nets(doc)
    lines = []
    for owner, key, s, t in _conductors(doc):
        lines.append((owner["id"], net(t), {s["id"], t["id"]}, wp.path(ns, s, t, owner.get(key)), len(owner.get(key) or [])))
    cross = sum(_cross(a[3], b[3]) for a, b in itertools.combinations(lines, 2) if a[1] != b[1])
    diag = sum(1 for l in lines if _diag(l[3]))
    thr = sum(1 for l in lines if _through(l[3], [(k, b) for k, b in boxes if not k.startswith("n_")], l[2]))
    thr_notes = sum(1 for l in lines if _through(l[3], [(k, b) for k, b in boxes if k.startswith("n_")], l[2]))
    pts = sum(l[4] for l in lines)
    xs = [b[0] for _, b in boxes] + [b[2] for _, b in boxes]
    ys = [b[1] for _, b in boxes] + [b[3] for _, b in boxes]
    return {"lines": len(lines), "crossings": cross, "diagonal_lines": diag, "lines_through_parts": thr,
            "lines_through_notes": thr_notes, "routing_points": pts, "lines_with_points": sum(1 for l in lines if l[4]),
            "width": max(xs) - min(xs), "height": max(ys) - min(ys),
            "wire_length": int(sum(_length(l[3]) for l in lines))}
