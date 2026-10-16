"""Check the standalone MJF print files (cad/export_print_files.py) - PA12 on Dan's HP printer, DECISIONS R73 / R101:
  P1  the STL and the 3MF are mm (size matches the expected part size) and agree with each other
  P2  one closed body: watertight, one connected shell, positive volume (nothing floating, R101)
  P3  walls >= 2.0 mm (R73): voxel morphology - every region narrower than 2.0 mm is listed; it fails unless the region is inside one
      of the part's named thin features (a snap barb, a deliberate flex arm is not a wall)
  P4  sits on the build plate: lowest point at z = 0
Run in WSL with the handbuilt-models venv (trimesh), from the repo root, --src = the checkout that holds the CAD files:
    ~/projects/handbuilt-models/.venv/bin/python cad/check_print_files.py --src /mnt/c/projects/active/st185-link-ecu-config
Claude Code, 2026-10-15.
"""
import argparse, os, sys, zipfile, re
import numpy as np
import trimesh

# name, print folder, expected size (mm, x y z, from the build), [(why, (x0, x1, y0, y1, z0, z1)) thin-feature exceptions, part frame]
PARTS = [
    # the clip plate itself (z 0-2) is the R123 design: a 2.0 plate whose wire holes and saddle notch leave narrower webs (Dan: walls >= 2.0
    # except the clip plate per R123); the legs and barbs above it are checked
    ('ST185_R1_retainer_clip_PA12', 'cad/fusebox/rev7/print', (31.87, 27.65, 8.39),
     [('clip plate (R123)', (-20.0, 20.0, -20.0, 20.0, -0.1, 2.05)),
      ('leg barbs (0.6 x 1.5 snap hooks, spec.RETAINER barb / barb_h)', (-20.0, 20.0, -20.0, 20.0, 8.39 - 1.6, 8.5))]),
    # snap lips: 0.7 x 0.8 hooks on the snap arms (vrc_holder_spec LIP_IN / LIP_H) - a hook, not a wall
    ('ST185_VRC_board_holder_PA12', 'cad/enclosures/vrc/print', (35.0, 31.0, 16.5),
     [('snap lips', (-9.6, -3.4, -12.3, 12.3, 15.6, 16.5))]),
]
MIN_WALL, MIN_REGION = 2.0, 0.5   # mm, mm3 (smaller specks are tessellation noise on curved faces)


def load_3mf(path):
    """(unit, mesh) from a 3MF: its 3D/3dmodel.model XML (vertices + triangles), read directly (no networkx needed)."""
    z = zipfile.ZipFile(path)
    x = z.read(next(n for n in z.namelist() if n.lower().endswith('.model'))).decode('utf-8')
    unit = (re.search(r'<model[^>]*\sunit="([^"]+)"', x) or [None, 'millimeter'])[1]
    v = np.array([[float(a), float(b), float(c)] for a, b, c in re.findall(r'<vertex\s+x="([^"]+)"\s+y="([^"]+)"\s+z="([^"]+)"', x)])
    f = np.array([[int(a), int(b), int(c)] for a, b, c in re.findall(r'<triangle\s+v1="(\d+)"\s+v2="(\d+)"\s+v3="(\d+)"', x)])
    return unit, trimesh.Trimesh(v, f, process=True)


def thin_regions(m, pitch=0.1, wall=MIN_WALL):
    """Regions thinner than `wall`: voxelize the solid (pitch mm), open it with a cube of `wall` (a cube keeps square corners, so box
    edges are not flagged); what the opening removes is material narrower than `wall` in some direction. Returns [(volume mm3, min
    corner, max corner)] per connected thin region, largest first."""
    from scipy import ndimage
    vg = m.voxelized(pitch).fill()
    solid = vg.matrix
    k = max(1, int(round(wall / pitch)) - 1)
    opened = ndimage.binary_opening(solid, structure=np.ones((k, k, k), bool))
    thin = solid & ~opened
    lab, n = ndimage.label(thin)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        cnt = int((lab[sl] == i).sum())
        lo = vg.indices_to_points(np.array([[s_.start for s_ in sl]]))[0]
        hi = vg.indices_to_points(np.array([[s_.stop - 1 for s_ in sl]]))[0]
        out.append((cnt * pitch ** 3, lo, hi))
    return sorted(out, key=lambda r: -r[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='.')
    a = ap.parse_args()
    bad = 0
    for (name, folder, size, excl) in PARTS:
        d = os.path.join(a.src, folder)
        stl = trimesh.load(os.path.join(d, name + '.stl'), force='mesh')
        unit3, m3 = load_3mf(os.path.join(d, name + '.3mf'))
        ext = stl.bounds[1] - stl.bounds[0]
        ok1 = np.allclose(ext, size, atol=0.15) and np.allclose(m3.bounds[1] - m3.bounds[0], ext, atol=0.15) and unit3 == 'millimeter'
        parts = stl.split(only_watertight=False)
        ok2 = stl.is_watertight and len(parts) == 1 and stl.volume > 0
        ok4 = abs(stl.bounds[0][2]) < 0.01
        regions = [r for r in thin_regions(stl) if r[0] >= MIN_REGION]
        for (_, (x0, x1, y0, y1, z0, z1)) in excl:
            regions = [r for r in regions if not (x0 <= r[1][0] and r[2][0] <= x1 and y0 <= r[1][1] and r[2][1] <= y1 and z0 <= r[1][2] and r[2][2] <= z1)]
        ok3 = not regions
        print('%s  (%s)' % (name, folder))
        print('  P1 %s size %.2f x %.2f x %.2f mm (STL), 3MF unit %s, %s; expected %s' % ('ok  ' if ok1 else 'FAIL', *ext, unit3,
              'same size' if np.allclose(m3.bounds[1] - m3.bounds[0], ext, atol=0.15) else 'DIFFERENT size', size))
        print('  P2 %s watertight %s, %d shell(s), volume %.3f cm3 (3MF %.3f)' % ('ok  ' if ok2 else 'FAIL', stl.is_watertight, len(parts),
              stl.volume / 1000, m3.volume / 1000))
        print('  P3 %s %d region(s) thinner than %.1f mm (voxel 0.1, regions >= %.1f mm3)%s' % ('ok  ' if ok3 else 'FAIL', len(regions), MIN_WALL,
              MIN_REGION, '' if not excl else '; allowed thin features: ' + ', '.join(e[0] for e in excl)))
        for (v, lo, hi) in regions[:30]:
            print('       %.1f mm3 in x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f' % (v, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
        print('  P4 %s lowest point z %.3f' % ('ok  ' if ok4 else 'FAIL', stl.bounds[0][2]))
        bad += (not ok1) + (not ok2) + (not ok3) + (not ok4)
    print('check_print_files: %s' % ('OK' if not bad else '%d failure(s)' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
