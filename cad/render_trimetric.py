"""One trimetric PNG per custom CAD model, same camera and style for all (DECISIONS R83).

Headless: reads each model's STEP (never Fusion, R74), tessellates it with OCP and paints
it with a fixed orthographic trimetric camera. Writes cad/<model>/trimetric*.png (tracked,
small) and cad/trimetrics.json (source files + their mtimes, to tell
when a STEP is newer than its picture).

Two stages: OCP (build123d venv) tessellates, VTK (--vtk-python, default ~/simvenv) draws.
On dansPC run it in WSL with the handbuilt-cad venv, from the repo root (WSL paths):

  ~/projects/handbuilt-cad/.venv/bin/python cad/render_trimetric.py \
      --src /mnt/c/projects/active/st185-link-ecu-config [--only fusebox-power ...]

--src is the checkout that holds the gitignored STEP files (the main checkout); the PNGs
go to the checkout this script sits in. The fuel hanger is read from the newest revN
folder of the Fairsolid run (--hanger-run).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
HANGER_RUN = "/mnt/c/projects/_archive/2026-10-17-fairsolid/fairsolid/runs/fuel_hanger_billet_1014"  # archived 2026-10-17 (Fairsolid now in handbuilt-cad)

# id -> (output png relative to repo, STEP globs relative to --src; "HANGER/" = newest hanger rev)
MODELS = {
    "busbar-A":       ("cad/busbar/design-A/trimetric.png",      ["cad/busbar/design-A/A_ASSEMBLY.step"]),
    "busbar-A-rev3":  ("cad/busbar/design-A-rev3/trimetric.png", ["cad/busbar/design-A-rev3/A_rev3_ASSEMBLY.step"]),
    "busbar-B":       ("cad/busbar/design-B/trimetric.png",      ["cad/busbar/design-B/B_ASSEMBLY.step"]),
    "busbar-B-rev2":  ("cad/busbar/design-B-rev2/trimetric.png", ["cad/busbar/design-B-rev2/B_rev2_ASSEMBLY.step"]),
    "busbar-B-rev3":  ("cad/busbar/design-B-rev3/trimetric.png", ["cad/busbar/design-B-rev3/B_rev3_ASSEMBLY.step"]),
    "fusebox-power":  ("cad/fusebox/trimetric-power.png",     ["cad/fusebox/Power_*.step"]),
    "fusebox-logic":  ("cad/fusebox/trimetric-logic.png",     ["cad/fusebox/Logic_*.step"]),
    "fusebox-battrelay": ("cad/fusebox/trimetric-battrelay.png", ["cad/fusebox/BattRelay_*.step"]),
    "enclosure-vrc":  ("cad/enclosures/vrc/trimetric.png",    ["cad/enclosures/vrc/VRC_assembly.step"]),
    # printed board holder of the VRC box (OPEN-ITEMS row 97, K7), shown with the board in it
    "enclosure-vrc-holder": ("cad/enclosures/vrc/trimetric-holder.png", ["cad/enclosures/vrc/VRC_part_VRC-Board-Holder.step",
                             "cad/enclosures/vrc/VRC_part_OpenLogicEFI_NCV1124_VR_module_RevB3.step"]),
    "enclosure-csb3": ("cad/enclosures/csb3/trimetric.png",   ["cad/enclosures/csb3/CSB3_assembly.step"]),
    "drb102-plate":   ("cad/drb102-plate/trimetric.png",      ["cad/drb102-plate/DRB102-firewall-plate-assembly.step"]),
    "fuel-hanger":    ("cad/fuel-hanger/trimetric.png",       ["cad/fuel-hanger/fuel-hanger-assembly.step"]),   # in-repo since 2026-10-17
    # rev 7 option (E2 = A): POWER box with the bus bar in it; its LOGIC box and battery block are rev 6's pictures
    "fusebox-rev7-power": ("cad/fusebox/rev7/trimetric-power.png", ["cad/fusebox/rev7/Power_*.step"]),
    # rev 7 LOGIC: the 3 mm clearance fix (Bus 2 + relay columns 2.5 mm outboard, box 81.5 wide); rev 6's LOGIC picture is history
    "fusebox-rev7-logic": ("cad/fusebox/rev7/trimetric-logic.png", ["cad/fusebox/rev7/Logic_*.step"]),
    # rev 7 battery relay block: R122 cover-screw bosses (3; none at the rear catch by the relay flange) - rev 6's picture is history
    "fusebox-rev7-battrelay": ("cad/fusebox/rev7/trimetric-battrelay.png", ["cad/fusebox/rev7/BattRelay_*.step"]),
    # Package renders (R84): every member together. "path@x,y" = place that STEP with its bounding box corner at
    # (x, y), z from 0 (the fuse box assembly STEP is already laid out in place).
    "package-rev6":   ("cad/fusebox/package-rev6.png", ["cad/fusebox/ST185_fusebox_rev6_assembly.step",
                       "cad/busbar/design-B-rev3/B_rev3_ASSEMBLY.step@0,280",
                       "cad/enclosures/vrc/VRC_assembly.step@400,-170", "cad/enclosures/vrc/VRC_assembly.step@400,-70",
                       "cad/enclosures/csb3/CSB3_assembly.step@400,30"]),
    "package-rev7":   ("cad/fusebox/rev7/package-rev7.png", ["cad/fusebox/rev7/ST185_fusebox_rev7_assembly.step",
                       "cad/enclosures/vrc/VRC_assembly.step@400,-170", "cad/enclosures/vrc/VRC_assembly.step@400,-70",
                       "cad/enclosures/csb3/CSB3_assembly.step@400,30"]),
}
# Models drawn upside down in their STEP: turned 180 deg about X so they show as installed.
FLIP_X = {"fuel-hanger"}   # modelled flange-down; in the tank the flange is on top

# Fixed camera: orthographic, looking from front-right-above, three unequal axis scales.
VIEW = np.array([0.62, -0.95, 0.70])
LIGHT = np.array([0.35, -0.55, 0.95])
PX = (900, 640)
BG = "#ffffff"

# Colour by part name (labels survive in our STEP exports); fallback palette by size.
MATERIALS = [
    # loaded fuse box assemblies (package renders): cables, relays and fuses first, so "cu" / "a2" below do not catch them
    (r"harness_wires", "#d9b43c"),
    (r"wire_feed|wire_", "#b8443a"),
    (r"relay_te|_relay_|coilplug|hcr150", "#26282b"),
    (r"fuse_ami_orange", "#ee7a1c"), (r"fuse_ami_ltgreen", "#7fd07a"), (r"fuse_ami_red", "#cc3333"),
    (r"fuse_ami_yellow", "#e6cc3a"), (r"fuse_atm", "#3d6fc4"),
    (r"cu|copper|c110|bar_power|pad_out|strip_logic", "#c8794a"),
    (r"board.holder", "#8f918c"),        # printed PA12 VRC board holder (before "board" / "plate" catch it)
    (r"al6061|_bar_|6061|billet|plate|strut|saddle|foot|lug_block|strap", "#a9b4bf"),
    (r"brass|insert", "#c9a64a"),
    (r"bolt|screw|a2|iso|standoff|keystone|nut|setscrew|clamp", "#7d8590"),
    (r"oring|o-ring|seal|nbr", "#2b2b2b"),
    (r"cover|lid", "#5b6f86"),
    (r"pump|check_valve|walbro", "#3c4a5a"),
    (r"lp16|hd34|connector|receptacle|lp-16", "#3a3a3a"),
    (r"pcb|board|module|ncv|carrier|csb3_manual|ecumaster", "#2f7d4a"),
    (r"printed|asa|pa12|body|base|pan|locator|plug", "#464b52"),
]
FALLBACK = ["#4b5563", "#a9b4bf", "#5b6f86", "#c8794a", "#7d8590", "#2f7d4a"]


def _newest_hanger(run: str) -> str:
    revs = [p for p in glob.glob(os.path.join(run, "rev*")) if re.fullmatch(r"rev\d+", os.path.basename(p))]
    return max(revs, key=lambda p: int(os.path.basename(p)[3:])) if revs else run


def sources(model: str, src: str, hanger_run: str, placed: bool = False) -> list:
    """STEP paths for a model; placed=True gives (path, (x, y) or None) pairs ("path@x,y" in MODELS)."""
    out = []
    for g in MODELS[model][1]:
        g, _, at = g.partition("@")
        xy = tuple(float(v) for v in at.split(",")) if at else None
        pat = g.replace("HANGER/", _newest_hanger(hanger_run) + "/") if g.startswith("HANGER/") else os.path.join(src, g)
        out += [(p, xy) if placed else p for p in sorted(glob.glob(pat))]
    return out


def _colour(name: str, i: int) -> str:
    n = name.lower()
    for rx, c in MATERIALS:
        if re.search(rx, n):
            return c
    return FALLBACK[i % len(FALLBACK)]


def _solids(path: str):
    """(name, solid) for every solid in a STEP file; the name is the file stem plus the
    assembly labels above the solid (labels sit on the assembly children, not the solids)."""
    from build123d import import_step

    def walk(node, names):
        lbl = getattr(node, "label", "") or ""
        names = names + ([lbl] if lbl and lbl not in ("_Unsaved_", "COMPOUND") else [])
        kids = list(getattr(node, "children", ()) or ())
        if not kids:
            return [(" ".join(names), s) for s in node.solids()]
        return [x for k in kids for x in walk(k, names)]

    return walk(import_step(path), [Path(path).stem])


def _tris(solid, tol: float) -> np.ndarray:
    try:
        verts, faces = solid.tessellate(tol, 0.4)
    except AttributeError:       # a face OCC cannot mesh (seen on a few wire / torus bodies of the loaded assemblies): per face
        verts, faces = [], []
        for fc in solid.faces():
            try:
                v_, f_ = fc.tessellate(tol, 0.4)
            except AttributeError:
                continue
            faces += [tuple(i + len(verts) for i in t) for t in f_]
            verts += list(v_)
    v = np.array([(p.X, p.Y, p.Z) for p in verts], dtype=float)
    f = np.array(faces, dtype=int)
    return v[f] if len(f) else np.zeros((0, 3, 3))


def tessellate(model: str, src: str, hanger_run: str, tmp: str) -> dict:
    """Stage 1 (OCP venv): STEP -> triangles + one colour per triangle, saved as .npz."""
    from matplotlib.colors import to_rgb
    placed = sources(model, src, hanger_run, placed=True)
    files = sorted({f for f, _ in placed})
    if not files:
        return {"model": model, "error": "no STEP found"}
    solids = []
    for f, xy in placed:
        ss = _solids(f)
        if xy is not None:      # package render: move this file's solids so its box corner sits at (x, y), z from 0
            from build123d import Location
            bb = [s.bounding_box() for _, s in ss]
            mn = [min(b.min.X for b in bb), min(b.min.Y for b in bb), min(b.min.Z for b in bb)]
            ss = [(n, s.moved(Location((xy[0] - mn[0], xy[1] - mn[1], -mn[2])))) for n, s in ss]
        solids += ss
    solids.sort(key=lambda t: -t[1].volume)   # stable fallback colours run to run
    lo = np.full(3, np.inf); hi = np.full(3, -np.inf)
    for _, s in solids:
        b = s.bounding_box()
        lo = np.minimum(lo, [b.min.X, b.min.Y, b.min.Z]); hi = np.maximum(hi, [b.max.X, b.max.Y, b.max.Z])
    tol = float(np.linalg.norm(hi - lo)) / 1200.0
    tris, cols = [], []
    for i, (name, s) in enumerate(solids):
        t = _tris(s, tol)
        tris.append(t); cols.append(np.tile(to_rgb(_colour(name, i)), (len(t), 1)))
    tris = np.concatenate(tris)
    if model in FLIP_X:
        tris[..., 1:] *= -1
    npz = os.path.join(tmp, model + ".npz")
    np.savez_compressed(npz, tris=tris, cols=np.concatenate(cols))
    win = lambda p: re.sub(r"^/mnt/([a-z])/", lambda m: m.group(1).upper() + ":/", p)
    return {"model": model, "npz": npz, "png": MODELS[model][0], "solids": len(solids),
            "part_types": len({n for n, _ in solids}),
            "extent_mm": [round(float(x), 1) for x in hi - lo],
            "sources": {win(f): int(os.path.getmtime(f)) for f in files},
            "rendered": date.today().isoformat()}


def draw(npz: str, out: str, label: str) -> None:
    """Stage 2 (VTK venv): z-buffered flat-shaded orthographic trimetric, fixed camera."""
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    from PIL import Image
    d = np.load(npz); t = d["tris"].reshape(-1, 3); c = (d["cols"] * 255).astype(np.uint8)
    pts = vtk.vtkPoints(); pts.SetData(numpy_to_vtk(t.astype(np.float64), deep=True))
    n = len(t) // 3
    ids = np.hstack([np.full((n, 1), 3), np.arange(3 * n).reshape(n, 3)]).astype(np.int64).ravel()
    cells = vtk.vtkCellArray(); cells.ImportLegacyFormat(numpy_to_vtkIdTypeArray(ids, deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    # Per-vertex colours (each triangle owns its 3 vertices): cell scalars do not draw on WSL GL.
    ca = numpy_to_vtk(np.repeat(c, 3, axis=0), deep=True); ca.SetName("rgb"); pd.GetPointData().SetScalars(ca)
    m = vtk.vtkPolyDataMapper(); m.SetInputData(pd); m.SetColorModeToDirectScalars(); m.SetScalarModeToUsePointData()
    a = vtk.vtkActor(); a.SetMapper(m)
    pr = a.GetProperty(); pr.SetInterpolationToFlat(); pr.SetAmbient(0.30); pr.SetDiffuse(0.75); pr.SetSpecular(0.08)
    pr.BackfaceCullingOff()
    r = vtk.vtkRenderer(); r.AddActor(a); r.SetBackground(1, 1, 1)
    r.SetTwoSidedLighting(True); r.AutomaticLightCreationOff()
    for pos, k in ((LIGHT, 0.85), (np.array([-0.6, 0.3, 0.4]), 0.30)):
        li = vtk.vtkLight(); li.SetLightTypeToSceneLight(); li.SetPositional(False)
        li.SetPosition(*pos); li.SetFocalPoint(0, 0, 0); li.SetIntensity(k); r.AddLight(li)
    # Fit the projected outline: same margin for every model, Z up.
    v = VIEW / np.linalg.norm(VIEW)
    rt = np.cross([0, 0, 1.0], v); rt /= np.linalg.norm(rt); up = np.cross(v, rt)
    px, py = t @ rt, t @ up
    ctr = rt * (px.min() + px.max()) / 2 + up * (py.min() + py.max()) / 2 + v * (t @ v).mean()
    cam = r.GetActiveCamera(); cam.ParallelProjectionOn()
    cam.SetFocalPoint(*ctr); cam.SetPosition(*(ctr + v * 5000)); cam.SetViewUp(*up)
    cam.SetParallelScale(1.08 * max((py.max() - py.min()) / 2, (px.max() - px.min()) / 2 * PX[1] / PX[0]))
    r.ResetCameraClippingRange()
    txt = vtk.vtkTextActor(); txt.SetInput(label); txt.SetPosition(12, 10)
    tp = txt.GetTextProperty(); tp.SetFontSize(18); tp.SetColor(0.33, 0.33, 0.33); r.AddViewProp(txt)
    w = vtk.vtkRenderWindow(); w.SetOffScreenRendering(1); w.AddRenderer(r); w.SetSize(*PX)
    w.SetMultiSamples(8); w.Render()
    f = vtk.vtkWindowToImageFilter(); f.SetInput(w); f.SetInputBufferTypeToRGB(); f.ReadFrontBufferOff(); f.Update()
    png = vtk.vtkPNGWriter(); png.SetFileName(out + ".raw.png"); png.SetInputConnection(f.GetOutputPort()); png.Write()
    img = Image.open(out + ".raw.png").convert("RGB")
    img.quantize(colors=128, method=Image.Quantize.MEDIANCUT).save(out, optimize=True)
    os.remove(out + ".raw.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=str(REPO), help="checkout holding the gitignored STEP files")
    ap.add_argument("--hanger-run", default=HANGER_RUN)
    ap.add_argument("--vtk-python", default=os.path.expanduser("~/simvenv/bin/python"),
                    help="python with vtk + Pillow for stage 2")
    ap.add_argument("--only", nargs="*", choices=sorted(MODELS), help="render just these models")
    ap.add_argument("--draw", nargs=3, metavar=("NPZ", "PNG", "LABEL"), help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.draw:
        draw(*a.draw); return
    import subprocess, tempfile
    todo = a.only or list(MODELS)
    meta_path = REPO / "cad" / "trimetrics.json"
    meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
    with tempfile.TemporaryDirectory() as tmp,             ProcessPoolExecutor(max_workers=min(len(todo), os.cpu_count() or 4)) as ex:
        for r in ex.map(tessellate, todo, [a.src] * len(todo), [a.hanger_run] * len(todo), [tmp] * len(todo)):
            if "error" in r:
                print(f"{r['model']}: {r['error']}", file=sys.stderr); continue
            out = REPO / r["png"]; out.parent.mkdir(parents=True, exist_ok=True)
            ext = r["extent_mm"]
            subprocess.run([a.vtk_python, __file__, "--draw", r["npz"], str(out),
                            f"{ext[0]:.0f} x {ext[1]:.0f} x {ext[2]:.0f} mm"], check=True)
            print(f"{r['model']}: {r['png']} ({r['solids']} solids, {out.stat().st_size // 1024} KB)")
            meta[r["model"]] = {k: v for k, v in r.items() if k not in ("model", "npz")}
    meta_path.write_text(json.dumps(dict(sorted(meta.items())), indent=1) + "\n")


if __name__ == "__main__":
    main()
