"""Snapshot views of the VRC board holder in the box, with the internal leads (OPEN-ITEMS row 97, K7). Headless, like
cad/render_trimetric.py (never a Fusion document, R74): reads VRC_assembly.step from the main checkout, leaves the lid
and O-ring off, adds the leads from vrc_holder_spec.wires() (M22759/16-20, OD 1.57, 3 x OD bends) as tubes, and draws
each view with render_trimetric.draw (its fixed style, a different camera per view).

WSL, from the repo root:
  ~/projects/handbuilt-cad/.venv/bin/python cad/enclosures/src/render_vrc_holder_views.py \
      --src /mnt/c/projects/active/st185-link-ecu-config --out <folder>
Claude Code, 2026-10-15.
"""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(REPO / "cad"))
import vrc_holder_spec as S          # noqa: E402
import render_trimetric as RT        # noqa: E402

LEAD = {"IN": (0.12, 0.33, 0.80), "OUT": (0.96, 0.78, 0.08), "drain": (0.55, 0.55, 0.55)}
# name -> (view direction, parts left out)
VIEWS = {
    "vrc_holder_open_iso.png": ((0.62, -0.95, 0.90), ("lid", "oring")),
    "vrc_holder_open_top.png": ((0.0, -0.02, 1.0), ("lid", "oring")),
    "vrc_holder_side_no_body.png": ((0.0, -1.0, 0.02), ("lid", "oring", "body")),
    "vrc_holder_leads_iso.png": ((0.62, -0.95, 0.70), ("lid", "oring", "body")),
    "vrc_holder_part_top.png": ((0.0, -0.02, 1.0), ("lid", "oring", "body", "lp16", "module", "leads")),
}


def tube(pts, r):
    from build123d import Solid, Vector, Location, Plane
    parts = []
    for a, b in zip(pts, pts[1:]):
        d = Vector(*b) - Vector(*a)
        if d.length < 1e-3:
            continue
        c = Solid.make_cylinder(r, d.length, plane=Plane(origin=a, z_dir=d))
        parts.append(c)
    for p in pts[1:-1]:
        parts.append(Solid.make_sphere(r).moved(Location(p)))
    return parts


def stage1(src, tmp):
    from matplotlib.colors import to_rgb
    solids = RT._solids(os.path.join(src, "cad/enclosures/vrc/VRC_assembly.step"))
    items = []
    for i, (n, s) in enumerate(sorted(solids, key=lambda t: -t[1].volume)):
        nl = n.lower()
        tag = ("lid" if "lid" in nl else "oring" if "oring" in nl or "o-ring" in nl else "body" if "vrc-body" in nl
               else "lp16" if "lp16" in nl else "holder" if "holder" in nl else "module" if "module" in nl or "ncv" in nl else "other")
        items.append((tag, s, to_rgb(RT._colour(n, i))))
    for name, pts in S.wires().items():
        sp, _ = S.smooth(pts)
        c = LEAD["drain" if name.startswith("drain") else ("IN" if name.startswith("IN") else "OUT")]
        for s in tube(sp, S.OD / 2):
            items.append(("leads", s, c))
    tol = 0.08
    out = {}
    for fn, (view, off) in VIEWS.items():
        tris, cols = [], []
        for tag, s, c in items:
            if tag in off:
                continue
            t = RT._tris(s, tol)
            tris.append(t); cols.append(np.tile(c, (len(t), 1)))
        npz = os.path.join(tmp, fn + ".npz")
        np.savez_compressed(npz, tris=np.concatenate(tris), cols=np.concatenate(cols))
        out[fn] = (npz, view)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vtk-python", default=os.path.expanduser("~/simvenv/bin/python"))
    ap.add_argument("--draw", nargs=4, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.draw:
        npz, png, label, view = a.draw
        RT.VIEW = np.array([float(x) for x in view.split(",")])
        RT.PX = (1200, 860)
        RT.draw(npz, png, label)
        return
    os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for fn, (npz, view) in stage1(a.src, tmp).items():
            label = "VRC board holder (K7) - leads M22759/16-20, bends 3 x OD; lid off"
            subprocess.run([a.vtk_python, __file__, "--src", a.src, "--out", a.out, "--draw", npz,
                            os.path.join(a.out, fn), label, ",".join(str(v) for v in view)], check=True)
            print(fn)


if __name__ == "__main__":
    main()
