"""Fallback LAYOUT snapshot of a .harness file, for review away from the app (the layout twin of
render_schematic.py).

The real snapshot is the app's own export (harness.design desktop, Main Menu > Export > PDF,
Layout page). This renderer is NOT an app export: bundles are straight lines between node centres
(through any layoutPoints), every node is a 30 x 30 box (https://docs.harness.design/files/harness/
positioning.md "in the layout view, every node type is 30 x 30"), labels sit to the right of the
node and are cut at the app's width (layout_geometry.LABEL_CHARS), splices and resistors with a
locationId get a dashed arrow to their location, and each bundle carries its length.

    python docs/harness/render_layout.py rebuild/ST185-A-cabin.harness out.png [--scale 0.5]

Needs Pillow (local tool, not used by any gate).
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import layout_geometry as lg

KIND_FILL = {"connectors": (40, 90, 160), "terminals": (90, 90, 90), "branchPoints": (150, 150, 150),
             "splices": (170, 110, 20), "resistors": (120, 40, 140), "diodes": (120, 40, 140)}


def font(size):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def render(path, out, scale=0.5):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    g = lg.geometry(d)
    xs = [b[0] for b in g["boxes"].values()] + [b[2] for b in g["boxes"].values()]
    ys = [b[1] for b in g["boxes"].values()] + [b[3] for b in g["boxes"].values()]
    pad = 90
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad - 60, max(xs) + pad, max(ys) + pad
    s = scale
    im = Image.new("RGB", (int((x1 - x0) * s) + 1, int((y1 - y0) * s) + 1), "white")
    dr = ImageDraw.Draw(im)
    f_lab, f_len, f_t = font(max(7, int(16 * s))), font(max(7, int(14 * s))), font(max(12, int(40 * s)))

    def P(x, y):
        return ((x - x0) * s, (y - y0) * s)

    for gx in range(int(x0 // 30) * 30, int(x1), 30):
        if gx % 150 == 0:
            dr.line([P(gx, y0), P(gx, y1)], fill=(238, 238, 238))
    for gy in range(int(y0 // 30) * 30, int(y1), 30):
        if gy % 150 == 0:
            dr.line([P(x0, gy), P(x1, gy)], fill=(238, 238, 238))
    for sp, (lx, ly) in g["locations"].items():
        a = g["centre"][sp]
        dr.line([P(*a), P(lx, ly)], fill=(200, 140, 40), width=1)
    for bid, pts in g["segments"].items():
        dr.line([P(*p) for p in pts], fill=(60, 60, 60), width=max(2, int(5 * s)))
        L = g["lengths"].get(bid)
        if L:
            (ax, ay), (bx, by) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
            dr.text(P((ax + bx) / 2 + 4, (ay + by) / 2 - 22), "%g mm" % L, fill=(30, 110, 30), font=f_len)
    for nid, (bx0, by0, bx1, by1) in g["boxes"].items():
        kind = g["kind"][nid]
        dr.rectangle([P(bx0, by0), P(bx0 + 30, by0 + 30)], fill=KIND_FILL.get(kind, (0, 0, 0)))
        txt = g["text"].get(nid)
        if txt:
            dr.text(P(bx0 + 36, by0 + 4), txt, fill=(0, 0, 0), font=f_lab)
    dr.text((10, 6), "%s - fallback layout snapshot (straight bundles; not the app's PDF export)"
            % os.path.basename(path), fill=(0, 0, 0), font=f_t)
    im.save(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    sc = 0.5
    if "--scale" in a:
        i = a.index("--scale")
        sc = float(a[i + 1])
        del a[i:i + 2]
    render(a[0], a[1], sc)
