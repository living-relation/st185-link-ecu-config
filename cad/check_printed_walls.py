"""Wall and attachment check of the printed fuse box parts (DECISIONS R127, Dan 2026-10-15: "check all boxes for walls 1.95mm thick or
less. check all boxes for floating or nearly floating features or cantilevers attached by less than 3mm thick material"):
  W  walls > 1.95 mm: the part is cut in planes every STEP mm along x, y and z; in every section the material thinner than 1.95 mm is
     what an opening (shrink by 0.975, grow back by 0.975, mitred corners down to 60 deg) takes away. Exact in the plane, so a 2.0 mm
     wall passes and a 1.95 mm one fails. Sections through the same spot merge into one 3-D spot; a spot seen in one section only is a
     plane grazing a curved face (the bottom of a saddle arc) and is dropped.
  A  attached by >= 3 mm: voxels of PITCH mm, opened with a cube of ~3 mm. Material that survives is the >= 3 mm "body". A thin
     piece (< 3 mm) that meets the body in ONE place only is a cantilever attached by less than 3 mm (a thin wall held at two or more
     places, or a part that is all thin like a cover or pan, is a wall and is left to W); a thick piece that meets the main body only
     through thin material is attached by less than 3 mm too.
  Covers, belly pans and the R1 clip are shells of the R73 2.5 / 2.0 wall (no >= 3 mm body to hang anything from): A does not apply,
  W checks them. A thin piece standing less than SKIN mm proud of the >= 3 mm body is the voxel skin of a sloped or tapered face (the
  angular legs), not a cantilever, and is not listed (the count is kept as attach_skin).
EXEMPT (R127 sweep, Dan 2026-10-16: "fix the ones you found as long as they don't alter the function and installability of the parts"): the
build records a box round every spot that has to stay thin (fusebox_report.json "wall_exempt", reasons in spec.WALL_EXEMPT); a W piece
or A spot inside one is not listed but counted under its name ("exempt").
Writes cad/fusebox/rev7/wall_check.json (tracked; check_printed_solid.py S4 / S5 reads it, CI has no STL) and prints every spot.
Run in WSL with the handbuilt-models venv (trimesh, shapely, scipy, PIL), from the repo root, --src = the checkout with the STLs:
    ~/projects/handbuilt-models/.venv/bin/python cad/check_printed_walls.py --src /mnt/c/projects/active/st185-link-ecu-config
Claude Code, 2026-10-15.
"""
import argparse, json, os, sys, time
import numpy as np
import trimesh
from shapely.geometry import LineString, Polygon, box as sbox
from shapely.ops import polygonize, unary_union

WALL, ATTACH = 1.95, 3.0          # mm: fail at or under WALL; attachment under ATTACH
STEP, PITCH = 0.5, 0.2            # mm: section spacing (W), voxel size (A)
MIN_AREA = 0.3                    # mm2: smaller W pieces in a section are tessellation noise on curved faces
MIN_VOL = 2.0                     # mm3: smaller A pieces are voxel noise
SNAP = 1e-4                       # mm: section segment ends closer than this are one point
SKIN = 1.5                        # mm: a thin piece must stand at least this far out of the >= 3 mm body to be a cantilever
SHELLS = ('_Cover_', '_Pan_', '_Retainer_')
FUSEBOX = 'cad/fusebox/rev7'
PARTS = ['Power_Base_PA12_printed', 'Power_Pan_PA12_printed', 'Power_Cover_PA12_printed', 'Power_Retainer_R1_PA12_printed',
         'Logic_Base_PA12_printed', 'Logic_Pan_PA12_printed', 'Logic_Cover_PA12_printed',
         'BattRelay_Base_PA12_printed', 'BattRelay_Cover_PA12_printed']


def section(m, axis, c):
    """Material polygon of the section of mesh m by the plane axis = c, in the plane's (u, v) coordinates."""
    n = np.zeros(3)
    n[axis] = 1.0
    o = np.zeros(3)
    o[axis] = c
    segs = trimesh.intersections.mesh_plane(m, n, o)
    if len(segs) == 0:
        return None
    k = [i for i in range(3) if i != axis]
    # R127 sweep: snap segment ends that are the same mesh point (within SNAP) to one point - rounding alone left a ring open now and
    # then, and polygonize then dropped that whole outline from the section (whole layers of a solid leg went missing in A)
    from scipy.spatial import cKDTree
    pts = segs[:, :, k].reshape(-1, 2)
    par = np.arange(len(pts))
    for i, j in sorted(cKDTree(pts).query_pairs(SNAP)):
        ri, rj = i, j
        while par[ri] != ri:
            ri = par[ri]
        while par[rj] != rj:
            rj = par[rj]
        if ri != rj:
            par[max(ri, rj)] = min(ri, rj)
    for i in range(len(par)):
        r = i
        while par[r] != r:
            r = par[r]
        par[i] = r
    pts = pts[par].reshape(-1, 2, 2)
    lines = [LineString(q) for q in pts if np.linalg.norm(q[0] - q[1]) > 1e-9]
    region = None
    for p in polygonize(lines):
        p = Polygon(p.exterior)
        region = p if region is None else region.symmetric_difference(p)      # even-odd: holes come out
    if region is None or region.is_empty:
        return None
    # spikes / slits under 0.04 mm where two cut faces of the solid meet (tessellation, 0.01 cut overlaps) are below what MJF can
    # print (~0.08): a 0.02 opening and closing removes them
    return region.buffer(0).buffer(-0.02, join_style=2).buffer(0.04, join_style=2).buffer(-0.02, join_style=2)


def thin_pieces(region, r=WALL / 2):
    opened = region.buffer(-r, join_style=2, mitre_limit=2.0).buffer(r, join_style=2, mitre_limit=2.0)
    thin = region.difference(opened).buffer(-0.01, join_style=2).buffer(0.01, join_style=2)   # drop round-off slivers along shared edges
    return [g for g in getattr(thin, 'geoms', [thin]) if g.geom_type == 'Polygon' and g.area >= MIN_AREA]


def walls(m, allow=(), seen=None):
    """W: [(x0, x1, y0, y1, z0, z1, n sections, min width estimate)] 3-D spots thinner than WALL. A piece inside an `allow` box
    (key, box) is left out and counted in seen[key]."""
    lo, hi = m.bounds
    pcs = []
    for axis in range(3):
        k = [i for i in range(3) if i != axis]
        for c in np.arange(lo[axis] + STEP / 2 + 0.0137, hi[axis], STEP):
            reg = section(m, axis, c)
            if reg is None:
                continue
            for g in thin_pieces(reg):
                b = g.bounds
                bb = [0.0] * 6
                bb[2 * k[0]], bb[2 * k[0] + 1], bb[2 * k[1]], bb[2 * k[1] + 1] = b[0], b[2], b[1], b[3]
                bb[2 * axis], bb[2 * axis + 1] = c - STEP / 2, c + STEP / 2
                bb.append(axis)
                k_ = next((key for (key, b) in allow if inside(bb, b)), None)
                if k_ is not None:
                    if seen is not None:
                        seen[k_] = seen.get(k_, 0) + 1
                    continue
                pcs.append(bb)
    # a real wall shows in 2+ sections; 1 = a plane grazing a curved face. R127 amendment: a spot seen by ONE axis family only, in under
    # 4 sections, is planes grazing a square edge whose other face is nearly parallel to them (the top of a bend saddle's curve where the
    # radial cut meets it) - sections along the other axes see solid there
    return [g[:7] for g in cluster(pcs) if g[6] >= 2 and not (len(g[7]) == 1 and g[6] < 4)]


def cluster(boxes, tol=0.6):
    par = list(range(len(boxes)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if all(a[2 * d] - tol <= b[2 * d + 1] and b[2 * d] - tol <= a[2 * d + 1] for d in range(3)):
                par[f(i)] = f(j)
    out = {}
    for i, b in enumerate(boxes):
        g = out.setdefault(f(i), [1e9, -1e9, 1e9, -1e9, 1e9, -1e9, 0, set()])
        for d in range(3):
            g[2 * d] = min(g[2 * d], b[2 * d])
            g[2 * d + 1] = max(g[2 * d + 1], b[2 * d + 1])
        g[6] += 1
        if len(b) > 6:
            g[7].add(b[6])
    return sorted(out.values(), key=lambda g: -g[6])


def voxels(m):
    """Solid occupancy at PITCH (z layers rasterised from the sections) and the grid origin."""
    from PIL import Image, ImageDraw
    lo, hi = m.bounds
    nx, ny, nz = (np.ceil((hi - lo) / PITCH).astype(int) + 2)
    org = lo - PITCH
    vol = np.zeros((nx, ny, nz), bool)
    for iz in range(nz):
        z = org[2] + (iz + 0.5) * PITCH
        if z <= lo[2] or z >= hi[2]:
            continue
        reg = section(m, 2, z)
        if reg is None:
            continue
        im = Image.new('1', (nx, ny), 0)
        dr = ImageDraw.Draw(im)
        for g in getattr(reg, 'geoms', [reg]):
            if g.geom_type != 'Polygon':
                continue
            dr.polygon([((x - org[0]) / PITCH - 0.5, (y - org[1]) / PITCH - 0.5) for x, y in g.exterior.coords], fill=1)
            for h in g.interiors:
                dr.polygon([((x - org[0]) / PITCH - 0.5, (y - org[1]) / PITCH - 0.5) for x, y in h.coords], fill=0)
        vol[:, :, iz] = np.array(im, bool).T
    return vol, org


skin = [0]


def attachments(m):
    """A: [(kind, x0, x1, y0, y1, z0, z1, volume mm3)] features attached by less than ATTACH."""
    from scipy import ndimage
    vol, org = voxels(m)
    k = int(round(ATTACH / PITCH)) - 1          # 14 voxels = 2.8: a 3.0 wall (15-16 voxels) survives, a 2.5 one (12-13) does not
    core = vol.astype(np.uint8)
    for ax in range(3):
        core = ndimage.minimum_filter1d(core, k, axis=ax, mode='constant', cval=0)
    for ax in range(3):
        core = ndimage.maximum_filter1d(core, k, axis=ax, mode='constant', cval=0)
    core = core.astype(bool) & vol
    thin = vol & ~core
    out = []

    def bbox(sl):
        return [float(org[d] + sl[d].start * PITCH) for d in range(3)], [float(org[d] + sl[d].stop * PITCH) for d in range(3)]
    if core.sum() < 0.1 * vol.sum():                         # all thin (a cover, a pan, a clip): walls only, W checks them
        return None
    if core.any():
        cl, nc = ndimage.label(core)
        sizes = np.bincount(cl.ravel())
        sizes[0] = 0
        main = int(np.argmax(sizes))
        for i, sl in enumerate(ndimage.find_objects(cl), 1):
            v = sizes[i] * PITCH ** 3
            if i != main and v >= MIN_VOL:
                a, b = bbox(sl)
                out.append(('thick piece held only by thin material', a[0], b[0], a[1], b[1], a[2], b[2], round(v, 1)))
        tl, nt = ndimage.label(thin)
        edge = ndimage.binary_dilation(thin) & core             # body voxels a thin piece touches
        pl, npl = ndimage.label(edge, structure=np.ones((3, 3, 3), bool))
        pairs = set()
        for ax in range(3):
            for sh in (1, -1):
                t2 = np.roll(tl, sh, axis=ax)
                hit = (pl > 0) & (t2 > 0)
                pairs.update(zip(t2[hit].tolist(), pl[hit].tolist()))
        patches = {}
        for t, p in pairs:
            patches.setdefault(t, set()).add(p)
        tsz = np.bincount(tl.ravel())
        objs = ndimage.find_objects(tl)
        skin[0] = 0
        pad = int(SKIN / PITCH) + 2

        def proud(t):           # the parts of thin piece t standing >= SKIN out of the >= 3 mm body: [(slices, volume mm3)]
            sl = tuple(slice(max(0, q.start - pad), q.stop + pad) for q in objs[t - 1])
            pm = (tl[sl] == t) & (ndimage.distance_transform_edt(~core[sl]) * PITCH >= SKIN)
            lab, n = ndimage.label(pm)
            szs = np.bincount(lab.ravel())
            return [(tuple(slice(sl[d].start + o[d].start, sl[d].start + o[d].stop) for d in range(3)), szs[i] * PITCH ** 3)
                    for i, o in enumerate(ndimage.find_objects(lab), 1) if szs[i] * PITCH ** 3 >= MIN_VOL]
        for t, ps in patches.items():
            v = tsz[t] * PITCH ** 3
            if len(ps) != 1 or v < MIN_VOL:
                continue
            pr = proud(t)
            if not pr:
                skin[0] += 1
                continue
            for (o, pv) in pr:       # each proud part on its own (a long skin piece is located by the bits that stand out)
                a, b = bbox(o)
                out.append(('thin piece held at one place (cantilever)', a[0], b[0], a[1], b[1], a[2], b[2], round(pv, 1)))
    return out


def exempt(name, src):
    """R127 sweep: (key, box) of every spot the build recorded as having to stay thin (fusebox_report.json "wall_exempt")."""
    rp = os.path.join(src, FUSEBOX, 'fusebox_report.json')
    ex = json.load(open(rp)).get('wall_exempt', []) if os.path.isfile(rp) else []
    return [(e['key'], e['box'], e.get('only')) for e in ex if e['part'] == name]


def allowed(name, src):
    """Named thin features that are not walls: the R1 retainer clip's snap barbs (spec.RETAINER barb x barb_h, at the top of each leg)."""
    if 'Retainer' not in name:
        return []
    sys.path.insert(0, os.path.join(src, 'cad', 'fusebox', 'src'))
    import spec as S
    RT = S.RETAINER
    rr = json.load(open(os.path.join(src, FUSEBOX, 'fusebox_report.json')))['retainers']['POWER'][0]
    sx, sy = S.PLACE['POWER']
    zt = S.POWER['z_d'] + RT['leg_h']
    out = []
    for (lx, ly) in rr['legs']:
        r = RT['leg'][0] / 2 + RT['barb'] + 0.6
        out.append(('snap barb at leg (%.1f, %.1f), %.1f x %.1f (R123)' % (lx, ly, RT['barb'], RT['barb_h']),
                    [lx + sx - r, lx + sx + r, ly + sy - RT['leg'][1], ly + sy + RT['leg'][1], zt - RT['barb_h'] - 0.6, zt + 0.6]))
    return out


def inside(g, b, tol=0.0):
    return all(b[2 * d] - tol <= g[2 * d] and g[2 * d + 1] <= b[2 * d + 1] + tol for d in range(3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='.')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    res = {'rule': 'R127: walls > %.2f mm (W, sections every %.1f mm), features attached by >= %.1f mm (A, voxels %.2f mm)' % (WALL, STEP, ATTACH, PITCH),
           'parts': {}}
    outp = os.path.join(a.src, FUSEBOX, 'wall_check.json')
    if a.only and os.path.isfile(outp):
        res = json.load(open(outp))
    for name in PARTS:
        if a.only and name not in a.only.split(','):
            continue
        p = os.path.join(a.src, FUSEBOX, name + '.stl')
        if not os.path.isfile(p):
            print('%s: no STL' % name)
            continue
        t0 = time.time()
        m = trimesh.load(p, force='mesh')
        allow = allowed(name, a.src)
        ex = exempt(name, a.src)
        seen = {}
        w = walls(m, [(k_, b_) for (k_, b_, o_) in ex if o_ != 'A'], seen)
        at = None if any(k in name for k in SHELLS) else attachments(m)
        if at:
            keep = []
            for x in at:
                k_ = next((key for (key, b, o_) in ex if inside(x[1:7], b, 2 * PITCH)), None)     # voxel boxes: 2 voxels of slack
                if k_ is None:
                    keep.append(x)
                else:
                    seen['A ' + k_] = seen.get('A ' + k_, 0) + 1
            at = keep
        w = [g for g in w if not any(inside(g, b) for (_, b) in allow)]
        res['parts'][name] = dict(allowed=[r for (r, _) in allow], attach_checked=at is not None, volume_cm3=round(m.volume / 1000, 1),
                                  exempt=seen, attach_skin=skin[0] if at is not None else 0,
                                  walls=[dict(at=[round(v, 1) for v in g[:6]], sections=g[6]) for g in w],
                                  attach=[dict(kind=x[0], at=[round(v, 1) for v in x[1:7]], vol_mm3=x[7]) for x in (at or [])])
        print('%s  (%.1f cm3, %.0f s): %d thin-wall spot(s), %s attachment spot(s)%s; exempt %s' % (name, m.volume / 1000, time.time() - t0, len(w),
              'n/a (shell / all thin)' if at is None else len(at), ('; allowed: ' + ', '.join(r for (r, _) in allow)) if allow else '', seen))
        for g in w[:40]:
            print('   W  x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  (%d sections)' % tuple(g))
        for x in (at or [])[:40]:
            print('   A  %s: x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  %.1f mm3' % x)
    json.dump(res, open(outp, 'w'), indent=1)
    print('wrote', outp)


if __name__ == '__main__':
    sys.exit(main())
