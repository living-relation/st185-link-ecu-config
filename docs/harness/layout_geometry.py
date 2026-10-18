"""Shared LAYOUT-view geometry for render_layout.py and audit_layout.py (DECISIONS R107).

Facts used (https://docs.harness.design/files/harness/positioning.md, bundles.md): layout positions
are the top-left corner of a node, every layout node is 30 x 30, bundles join nodes (connectors,
terminals, branch points) through optional layoutPoints. Read off the app (Dan's 2026-10-15
screenshot): a connector or terminal shows its label to the right of the node, cut to about
LABEL_CHARS characters, about LABEL_W units long; bundles enter a terminal from its left. Label
size is an estimate - look at the drawing in the app.
"""
NODE = 30
LABEL_CHARS = 32
LABEL_W = 330          # node + gap + cut label, in layout units
SPLICE_W = 30          # splices / resistors / diodes: the node only (no label shown)
KINDS = ("connectors", "terminals", "branchPoints", "splices", "resistors", "diodes")


def text_of(kind, x):
    if kind == "connectors":
        t = x.get("label") or x.get("id")
    elif kind == "terminals":
        t = x.get("label") or x.get("signal") or x.get("id")   # R156: the label is the visible name
    else:
        return ""
    return t if len(t) <= LABEL_CHARS else t[:LABEL_CHARS] + "..."


def geometry(d):
    """boxes: id -> (x0, y0, x1, y1) node + label; centre: id -> node centre; segments: bundle id ->
    polyline (centre to centre through layoutPoints); locations: splice id -> location centre."""
    g = {"boxes": {}, "centre": {}, "kind": {}, "text": {}, "segments": {}, "lengths": {},
         "locations": {}, "ends": {}}
    for k in KINDS:
        for x in d.get(k, []):
            p = x.get("layoutPosition")
            if not p:
                continue
            w = NODE if k == "branchPoints" else (LABEL_W if k in ("connectors", "terminals") else SPLICE_W)
            g["boxes"][x["id"]] = (p["x"], p["y"], p["x"] + w, p["y"] + NODE)
            g["centre"][x["id"]] = (p["x"] + NODE / 2, p["y"] + NODE / 2)
            g["kind"][x["id"]] = k
            g["text"][x["id"]] = text_of(k, x)
    for k in ("splices", "resistors", "diodes"):
        for x in d.get(k, []):
            if x.get("locationId") in g["centre"] and x["id"] in g["centre"]:
                g["locations"][x["id"]] = g["centre"][x["locationId"]]
    for b in d.get("bundles", []):
        a, z = g["centre"].get(b["sourceId"]), g["centre"].get(b["targetId"])
        if not a or not z:
            continue
        mid = [(q["layoutPosition"]["x"] + NODE / 2, q["layoutPosition"]["y"] + NODE / 2)
               for q in b.get("layoutPoints", []) if q.get("layoutPosition")]
        g["segments"][b["id"]] = [a] + mid + [z]
        g["ends"][b["id"]] = (b["sourceId"], b["targetId"])
        g["lengths"][b["id"]] = (b.get("length") or {}).get("value")
    return g


def seg_hits_box(p, q, box, pad=0):
    """True if segment p-q passes through box (Liang-Barsky clip)."""
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
            continue
        t = qq / pp
        if pp < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


def segs_overlap(p, q, r, s, tol=1.0):
    """True if two segments lie on one line and share a stretch longer than tol (one hides the other)."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    if abs(cross(p, q, r)) > tol * max(1.0, abs(q[0] - p[0]) + abs(q[1] - p[1])) or \
       abs(cross(p, q, s)) > tol * max(1.0, abs(q[0] - p[0]) + abs(q[1] - p[1])):
        return False
    ax = 0 if abs(q[0] - p[0]) >= abs(q[1] - p[1]) else 1
    a0, a1 = sorted((p[ax], q[ax]))
    b0, b1 = sorted((r[ax], s[ax]))
    return min(a1, b1) - max(a0, b0) > tol


def boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
