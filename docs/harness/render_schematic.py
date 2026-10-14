"""Render a .harness schematic to PNG for review away from the app (Daniel reviews drawings from
his phone). Wires are drawn on the paths the harness.design app draws (`wire_paths.py`), 3 units
wide, in their insulation colour with the stripe on top. It is NOT an app export: node faces are
simplified (id, part label, cavity rows); prefer the app's Export > PDF when the app can be driven.

    python docs/harness/render_schematic.py rebuild/ST185-CabinPower.harness out.png [--scale 1.0]

Needs Pillow (local tool, not used by any gate).
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import wire_paths

COL = {"Red": (200, 30, 30), "Black": (20, 20, 20), "Green": (20, 140, 40), "White": (165, 165, 165),
       "Violet": (130, 40, 170), "Orange": (230, 120, 0), "Yellow": (205, 175, 0), "Gray": (110, 110, 110),
       "Brown": (120, 70, 20), "Blue": (30, 60, 200), "Pink": (230, 100, 160), "Shield": (90, 90, 90),
       "Transparent": (185, 185, 185)}


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
    owners = {w["id"]: w for w in d.get("wires", [])}
    for c in d.get("cables", []):
        for co in c.get("cores", []) + ([c["shield"]] if c.get("shield") else []):
            owners[co["id"]] = co
    for lid, s, t, pts in wire_paths.lines(d, ns):
        if not pts:
            continue
        w = owners.get(lid.split("/")[0], {})
        lw = max(1, round(wire_paths.LINE_WIDTH * scale))
        dr.line([T(*p) for p in pts], fill=COL.get(w.get("color"), (0, 0, 0)), width=lw, joint="curve")
        if w.get("stripeColor"):
            dr.line([T(*p) for p in pts], fill=COL.get(w["stripeColor"], (0, 0, 0)), width=max(1, lw // 3))
    dr.text((10, 8), title or ("%s - schematic from the file (harness.design wire routing; not an app export)"
                               % os.path.basename(fn)), fill="black", font=ft)
    im.save(out)
    return im.size


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    sc = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
    if "--scale" in sys.argv:
        a = [x for x in a if x != sys.argv[sys.argv.index("--scale") + 1]]
    print(render(a[0], a[1], sc))
