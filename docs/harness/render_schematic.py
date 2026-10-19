"""Fallback schematic snapshot of a .harness file, for review away from the app (Daniel reviews
drawings from his phone).

The real snapshot is the app's own export: harness.design desktop, Main Menu > Export > PDF,
Schematic page (https://docs.harness.design/feature/export#pdf). That export is GUI-only, so this
renderer exists for agents and CI that cannot drive the app. It is NOT an app export: node faces
are simplified (id, part label, cavity rows) and wire colours are this renderer's own (DECISIONS
): one darker display colour per circuit (interfaces.json identBands) or, for a harness not
yet banded, per electrical net, so parallel circuits are told apart. The insulation colour is in
the app and the build list. Ident bands (identColors, R87) are drawn at both wire ends. Wires
follow the app's own paths (`wire_paths.py`), 3 units wide.

    python docs/harness/render_schematic.py rebuild/ST185-CabinPower.harness out.png [--scale 1.0]

Needs Pillow (local tool, not used by any gate).
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import wire_paths



# display colours (our choice): dark, far apart, none of them the light ident band colours
DISPLAY = [(20, 60, 160), (170, 25, 25), (20, 120, 50), (110, 35, 150), (150, 80, 10), (0, 115, 125),
           (200, 90, 0), (95, 100, 20), (165, 20, 110), (60, 60, 60), (40, 100, 200), (120, 20, 40),
           (0, 90, 70), (80, 50, 130), (140, 110, 0), (30, 30, 90)]
BAND = {"Blue": (40, 90, 230), "Yellow": (250, 210, 0), "White": (255, 255, 255)}


def _circuit_keys(d, fn):
    """wire id -> colour key: its identBands circuit, else its electrical net."""
    key = {}
    try:
        import model
        reg = model.registry()
        name = next((h for h, f in model.harness_files(reg).items()
                     if os.path.basename(f) == os.path.basename(fn)), None)
        for c, v in ((reg.get("identBands") or {}).get(name) or {}).items():
            for wid in v.get("wires", []):
                key[wid] = c
    except Exception:
        pass
    joins = {n["id"] for k in ("splices", "terminals") for n in d.get(k, [])}
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x
    conds = list(d.get("wires", []))
    for c in d.get("cables", []):
        conds += c.get("cores", []) + ([c["shield"]] if c.get("shield") else [])
    conds = [w for w in conds if w.get("source") and w.get("target")]   # a screen may float at one end
    for w in conds:
        if not (w.get("source") and w.get("target")):   # a screen left open at one end
            continue
        a, b = [(e["id"],) if e["id"] in joins else (e["id"], e.get("handle")) for e in (w["source"], w["target"])]
        parent[find(a)] = find(b)
    for w in conds:
        e = w.get("source") or w["target"]
        key.setdefault(w["id"], find((e["id"],) if e["id"] in joins else (e["id"], e.get("handle"))))
    return key


def _along(pts, dist):
    """the point `dist` along the polyline, and the segment direction there."""
    for a, b in zip(pts, pts[1:]):
        L = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        if L and dist <= L:
            return (a[0] + (b[0] - a[0]) * dist / L, a[1] + (b[1] - a[1]) * dist / L)
        dist -= L
    return pts[-1]


def _bands(dr, pts, colours, T, scale, lw):
    """ident bands at both ends, band 1 nearest the terminal (R87): 8 units each, 3 apart."""
    total = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in zip(pts, pts[1:]))
    for run in (pts, pts[::-1]):
        for k, c in enumerate(colours):
            s0, s1 = 4 + 11 * k, 12 + 11 * k
            if s1 > total / 2:
                break
            seg = [_along(run, s0 + (s1 - s0) * i / 8.0) for i in range(9)]
            dr.line([T(*q) for q in seg], fill=(0, 0, 0), width=lw + max(4, round(6 * scale)), joint="curve")
            seg = [_along(run, s0 + 1 + (s1 - s0 - 2) * i / 8.0) for i in range(9)]
            dr.line([T(*q) for q in seg], fill=BAND.get(c, (200, 200, 200)), width=lw + max(2, round(4 * scale)), joint="curve")


def _font(name, size):
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def render(fn, out, scale=1.0, title=None):
    d = json.load(open(fn, encoding="utf-8"))
    ns = wire_paths.nodes(d)
    boxes = [n.box() for n in ns.values()]
    notes = []
    for nt in d.get("schematicNotes", []):
        p = nt["schematicPosition"]
        w = nt.get("width") or 270
        lines = []
        for l in (nt.get("text") or "").split("\n"):
            step = max(1, int(w / 6.2))
            lines += [l[i:i + step] for i in range(0, max(1, len(l)), step)]
        h = 12 + 13 * len(lines)
        notes.append((p["x"], p["y"], w, h, lines))
        boxes.append((p["x"], p["y"], p["x"] + w, p["y"] + h))
    for lid, s_, t_, pts in wire_paths.lines(d, ns):
        for p in pts or ():
            boxes.append((p[0], p[1], p[0], p[1]))
    pad = 90
    x0 = min(b[0] for b in boxes) - pad
    y0 = min(b[1] for b in boxes) - pad - 40
    W = int((max(b[2] for b in boxes) - x0 + pad) * scale)
    H = int((max(b[3] for b in boxes) - y0 + pad) * scale)
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)
    f = _font("arial.ttf", max(7, int(10 * scale)))
    fb = _font("arialbd.ttf", max(7, int(10 * scale)))
    ft = _font("arialbd.ttf", max(14, int(22 * scale)))

    def T(x, y):
        return ((x - x0) * scale, (y - y0) * scale)

    for x, y, w, h, lines in notes:
        dr.rectangle([T(x, y), T(x + w, y + h)], fill=(255, 249, 220), outline=(200, 180, 100))
        for k, l in enumerate(lines):
            dr.text(T(x + 4, y + 5 + 13 * k), l, fill=(40, 40, 40), font=f)
    for n in ns.values():
        b = n.box()
        if n.kind == "splice":
            dr.ellipse([T(b[0] + 8, b[1] + 8), T(b[2] - 8, b[3] - 8)], fill=(20, 20, 20))
            continue
        dr.rectangle([T(b[0], b[1]), T(b[2], b[3])], fill=(244, 247, 252), outline=(60, 80, 120))
        lab = n.el.get("label") or n.el.get("signal") or n.id
        chars = int((b[2] - b[0]) / 6)
        if n.kind == "connector":
            dr.rectangle([T(b[0], b[1]), T(b[2], b[1] + 30)], fill=(214, 225, 242), outline=(60, 80, 120))
            dr.text(T(b[0] + 4, b[1] + 3), n.id, fill="black", font=fb)
            dr.text(T(b[0] + 4, b[1] + 16), lab[:chars], fill=(50, 50, 50), font=f)
            if not n.rot:
                for k, c in enumerate(n.el["cavities"]):
                    yy = b[1] + 30 * (k + 1)
                    dr.line([T(b[0], yy), T(b[2], yy)], fill=(205, 212, 225))
                    txt = "%s  %s" % (c.get("designation", c["id"]), c.get("signal", ""))
                    dr.text(T(b[0] + 4, yy + 9), txt[:chars], fill=(30, 30, 30), font=f)
        elif n.kind == "terminal":
            dr.text(T(b[0] + 4, b[1] + 3), n.id, fill="black", font=fb)
            dr.text(T(b[0] + 4, b[1] + 16), lab[:chars], fill=(50, 50, 50), font=f)
        else:
            dr.text(T(b[0] + 2, b[1] + 3), n.kind, fill="black", font=f)
            if n.el.get("label"):                      # R156: a named LED / resistor
                dr.text(T(b[0] - 20, b[1] - 13), n.el["label"], fill=(50, 50, 50), font=f)
    owners = {w["id"]: w for w in d.get("wires", [])}
    for c in d.get("cables", []):
        for co in c.get("cores", []) + ([c["shield"]] if c.get("shield") else []):
            owners[co["id"]] = co
    keys = _circuit_keys(d, fn)
    order = {}
    for k in keys.values():
        order.setdefault(k, DISPLAY[len(order) % len(DISPLAY)])
    lw = max(1, round(wire_paths.LINE_WIDTH * scale))
    drawn = []
    for lid, s, t, pts in wire_paths.lines(d, ns):
        if not pts:
            continue
        wid = lid.split("/")[0]
        dr.line([T(*p) for p in pts], fill=order.get(keys.get(wid), (0, 0, 0)), width=lw, joint="curve")
        drawn.append((pts, owners.get(wid, {}).get("identColors") or []))
    for pts, ic in drawn:
        if ic and len(pts) > 1:
            _bands(dr, pts, ic, T, scale, lw)
    dr.text((10, 8), title or ("%s - fallback snapshot (app wire paths; display colour per circuit; not the app's PDF export)"
                               % os.path.basename(fn)), fill="black", font=ft)
    im.save(out)
    return im.size


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    sc = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
    if "--scale" in sys.argv:
        a = [x for x in a if x != sys.argv[sys.argv.index("--scale") + 1]]
    print(render(a[0], a[1], sc))
