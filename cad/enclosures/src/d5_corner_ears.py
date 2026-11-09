"""CSB3 / VRC enclosure release with Dan's D5 a1 corner ears (2026-11-08) and PA12 MJF (2026-11-09).

Builds the new body and lid of each box from the revA Fusion exports in the models folder (B26):
  - fills the old M3 tap holes in the body and the old countersunk holes in the lid
  - adds a 2.5 mm ear at each corner of the body rim and lid, outside the revA outer wall only (the O-ring
    groove and the cavity stay as revA), so the lid screw axes move out to
    CSB3 (+-32.5, +-32.5) and VRC (+-42.5, +-22.5)
  - body: 4 x 3.99 x 8 deep bores for SPIROL 150419 M3 heat-set inserts, each on a 10 mm boss
  - lid: 4 x 3.45 through, 90 deg countersink to 7.0 for ISO 10642 M3 (Accu SSK-M3-12-A2)
Connectors, tabs, cavities, the O-ring groove and the M6 / M8 holes do not move.

Writes the part and assembly STEPs to --out (never into the repo; they are filed in the models folder) and
the tracked geometry report cad/enclosures/d5_report.json that check_drawings_current.py fingerprints.

    $CAD_PY cad/enclosures/src/d5_corner_ears.py --csb3 <models>/st185_csb3-enclosure_1101/revA \
        --vrc <models>/st185_vrc-enclosure_1101/revA --hardware <bought-part STEPs> --out <work dir>
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from build123d import Axis, Box, Compound, Cone, Cylinder, GeomType, Pos, export_step, fillet, import_step

REPORT = Path(__file__).resolve().parents[1] / "d5_report.json"

OLD = {"csb3": (31.1, 31.1), "vrc": (41.1, 21.1)}
NEW = {"csb3": (32.5, 32.5), "vrc": (42.5, 22.5)}
HALF = {"csb3": (35.0, 35.0), "vrc": (45.0, 25.0)}
RIM_Z = {"csb3": 50.0, "vrc": 39.0}
LID_TOP = {"csb3": 56.0, "vrc": 45.0}
BOSS_Z0 = {"csb3": 38.0, "vrc": 27.0}
EAR = 2.5
EAR_REACH = 8.0
BORE_D = 3.99
BORE_DEPTH = 8.0
BOSS_D = 10.0
LID_HOLE_D = 3.45
CSK_D = 7.0
CORNER_R = 3.0
OLD_TAP_FILL_D = 2.9
OLD_TAP_DEPTH = 10.2
OLD_CSK_FILL_D = 7.2
INSERT_LEN = 5.74
M3_LEN = 12.0
M6_LEN = 14.0
HOLDER_SCREW_TOP = 17.5
SET_SCREW_Z = -2.0
SET_SCREWS = ((13.5, 13.5), (-13.5, -13.5))


def corners(xy):
    x, y = xy
    return [(sx * x, sy * y) for sx in (1, -1) for sy in (1, -1)]


def one_solid(shape):
    solids = list(shape.solids())
    if len(solids) != 1:
        raise RuntimeError(f"expected 1 solid, got {len(solids)}")
    return solids[0]


def column(d, z0, z1):
    return Pos(0, 0, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def slab(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def ear(x, y, half, z0, z1):
    hx, hy = half
    xs = sorted((math.copysign(max(abs(x) - EAR_REACH, 0), x), math.copysign(hx + EAR, x)))
    ys = sorted((math.copysign(max(abs(y) - EAR_REACH, 0), y), math.copysign(hy + EAR, y)))
    return slab(*xs, *ys, z0, z1)


def countersink(z_top):
    h = (CSK_D - LID_HOLE_D) / 2
    return Pos(0, 0, z_top - h / 2) * Cone(LID_HOLE_D / 2, CSK_D / 2, h)


def outline(box, z0, z1):
    """The revA outer wall (box corners R3) as a prism: ears add material only outside it."""
    hx, hy = HALF[box]
    prism = Pos(0, 0, (z0 + z1) / 2) * Box(2 * hx, 2 * hy, z1 - z0)
    return fillet(prism.edges().filter_by(Axis.Z), CORNER_R)


def build_body(src, box):
    body = one_solid(import_step(src))
    top = RIM_Z[box]
    for x, y in corners(OLD[box]):
        body += Pos(x, y, 0) * column(OLD_TAP_FILL_D, top - OLD_TAP_DEPTH, top)
    wall = outline(box, BOSS_Z0[box] - 0.1, top + 0.1)
    for x, y in corners(NEW[box]):
        body += ear(x, y, HALF[box], BOSS_Z0[box], top) - wall
        body += (Pos(x, y, 0) * column(BOSS_D, BOSS_Z0[box], top)) - wall
        body -= Pos(x, y, 0) * column(BORE_D, top - BORE_DEPTH, top + 0.2)
    return one_solid(body)


def build_lid(src, box):
    lid = one_solid(import_step(src))
    z0, z1 = RIM_Z[box], LID_TOP[box]
    wall = outline(box, z0 - 0.1, z1 + 0.1)
    for x, y in corners(OLD[box]):
        lid += (Pos(x, y, 0) * column(OLD_CSK_FILL_D, z0, z1)) & wall
    for x, y in corners(NEW[box]):
        lid += ear(x, y, HALF[box], z0, z1) - wall
        lid -= Pos(x, y, 0) * column(LID_HOLE_D, z0 - 0.2, z1 + 0.2)
        lid -= Pos(x, y, 0) * countersink(z1)
    return one_solid(lid)


def placed(step, spots, z, label):
    model = one_solid(import_step(step))
    out = Compound(children=[Pos(x, y, z) * model for x, y in spots])
    out.label = label
    return out


def part(step, label):
    shape = import_step(step)
    shape.label = label
    return shape


def holes(solid):
    """Vertical holes up to 8 mm across: (|x|, |y|, diameter, z0, z1), one row per hole size and place."""
    rows = set()
    for face in solid.faces():
        if face.geom_type != GeomType.CYLINDER or not face.radius or face.radius > 4.0:
            continue
        ax = face.axis_of_rotation
        if abs(ax.direction.Z) < 0.99:
            continue
        bb = face.bounding_box()
        rows.add((round(abs(ax.position.X), 2), round(abs(ax.position.Y), 2), round(2 * face.radius, 2),
                  round(bb.min.Z, 2), round(bb.max.Z, 2)))
    return [list(r) for r in sorted(rows)]


def geometry(solid):
    bb = solid.bounding_box()
    return {"solids": len(list(solid.solids())), "volume_mm3": round(solid.volume, 1),
            "bbox": [round(v, 2) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)],
            "holes": holes(solid)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csb3", type=Path, required=True, help="CSB3 revA folder (models folder)")
    ap.add_argument("--vrc", type=Path, required=True, help="VRC revA folder (models folder)")
    ap.add_argument("--hardware", type=Path, required=True, help="folder with the bought-part STEPs")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    hw = a.hardware
    m3, insert = hw / "Accu_SSK-M3-12-A2.step", hw / "SPIROL_150419_ENVELOPE.step"
    out_c, out_v = a.out / "csb3", a.out / "vrc"
    out_c.mkdir(parents=True, exist_ok=True)
    out_v.mkdir(parents=True, exist_ok=True)

    cb = build_body(a.csb3 / "CSB3_part_CSB3-Body.step", "csb3")
    cl = build_lid(a.csb3 / "CSB3_part_CSB3-Lid.step", "csb3")
    vb = build_body(a.vrc / "VRC_part_VRC-Body.step", "vrc")
    vl = build_lid(a.vrc / "VRC_part_VRC-Lid.step", "vrc")
    cb.label, cl.label, vb.label, vl.label = "CSB3-Body", "CSB3-Lid", "VRC-Body", "VRC-Lid"
    export_step(cb, out_c / "CSB3_part_CSB3-Body.step")
    export_step(cl, out_c / "CSB3_part_CSB3-Lid.step")
    export_step(vb, out_v / "VRC_part_VRC-Body.step")
    export_step(vl, out_v / "VRC_part_VRC-Lid.step")

    csb3 = Compound(children=[
        cb, cl,
        part(hw / "Parker_2-039_installed_CSB3.step", "ORING-AS568-039"),
        part(a.csb3 / "CSB3_part_ECUMaster_CSB3_manual_v2.1_p.4.step", "ECUMaster_CSB3"),
        part(a.csb3 / "CSB3_part_Lock-in_supports_Cat_8847_L10_x2.step", "Lock-in_supports_Cat_8847_L10_x2"),
        part(a.csb3 / "CSB3_part_HD34-24-33PE.step", "HD34-24-33PE_TE"),
        placed(hw / "Accu_SSF-M8-6-A2.step", SET_SCREWS, SET_SCREW_Z, "Set_screws_Accu_SSF-M8-6-A2"),
        placed(insert, corners(NEW["csb3"]), RIM_Z["csb3"] - INSERT_LEN, "SPIROL_150419"),
    ])
    holder = a.vrc / "VRC_part_VRC-Board-Holder.step"
    bosses = sorted({(round(f.axis_of_rotation.position.X, 2), round(f.axis_of_rotation.position.Y, 2))
                     for f in vb.faces() if f.geom_type == GeomType.CYLINDER and f.radius and abs(f.radius - 5.5) < 0.01})
    if len(bosses) != 2:
        raise RuntimeError(f"expected 2 holder bosses, found {bosses}")
    vrc = Compound(children=[
        vb, vl,
        part(hw / "Parker_2-039_installed_VRC.step", "ORING-AS568-039"),
        part(holder, "VRC_board_holder__printed_"),
        part(a.vrc / "VRC_part_OpenLogicEFI_NCV1124_VR_module_RevB3.step", "OpenLogicEFI_NCV1124_VR_module_RevB3"),
        part(a.vrc / "VRC_part_LP16-IN_LP-16-C05SX-02-101.step", "LP16-IN_CNLINKO_LP-16-C05SX-02-101"),
        part(a.vrc / "VRC_part_LP16-OUT_LP-16-C05SX-02-101.step", "LP16-OUT_CNLINKO_LP-16-C05SX-02-101"),
        placed(insert, corners(NEW["vrc"]), RIM_Z["vrc"] - INSERT_LEN, "SPIROL_150419"),
    ])
    export_step(csb3, out_c / "CSB3_assembly.step")
    export_step(vrc, out_v / "VRC_assembly.step")

    report = {
        "about": "CSB3 / VRC D5 a1 geometry from cad/enclosures/src/d5_corner_ears.py. Bodies and lids are PA12 MJF. Issued drawings are regenerated from these parts.",
        "parts": {"CSB3-Body": geometry(cb), "CSB3-Lid": geometry(cl), "VRC-Body": geometry(vb), "VRC-Lid": geometry(vl)},
        "vrc_holder_bosses": [list(b) for b in bosses],
    }
    REPORT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report["parts"], indent=1))


if __name__ == "__main__":
    main()
