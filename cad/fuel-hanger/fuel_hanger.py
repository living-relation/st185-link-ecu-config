"""Billet 6061-T6 fuel pump hanger for the ST185.  2026-10-17 release, from the fairsolid build123d source rev 7 / rev 8.

Flange rev G (Dan 2026-10-17, N6 decision = option 2): the bolt-on lug block of fairsolid rev 7 is MACHINED INTEGRAL with the top flange
(one 6061 billet, part "flange"). Deleted: the 2 M5 block screws (rev G blind / rev 8 tapped through) and the 2 dowel holes.
The flange keeps exactly its 13 original through-holes (2 AN bulkheads, 2 isolated electrical studs, 9 flange screws);
no new hole opens on the outside (sealing) face. Strut, valve, pass-through positions and the 2 x dia 6.6 M6 strut
cross-holes are unchanged. Fillets are applied LAST, after every cut. Edge breaks are a drawing note (not modelled).
Rev letters: each part model's letter = its count of releases (fairsolid rev folders where it changed), A first, skip I, L, O, Q:
flange G, strut E, foot D, saddle C, lug block A (obsolete). Evidence: cad/DRAWING-REVS.md.

Rev 3c (Dan): the JXSS035 fittings are fuel-cell BULKHEADS (male AN both ends, hex + sealing washer outside,
sealing washer + nut inside), so the plate gets plain clearance holes, not tapped ports. Every pass-through
(2 bulkheads + 2 Radium 17-0048 isolated electrical studs: pump + and pump -) has a flat sealing spot face on BOTH sides
(Ra 1.6, edges broken 0.3, no burrs). Plate 7.8 thick, spot faces 0.4 deep -> 7.0 at every hole: inside the
Radium stud window (0.262-0.322") and plate + 2 washers = ~11 mm bulkhead grip. Fittings are not modelled;
only keep-out envelopes (nut socket / hose end, stud terminal) for fit checks.

Rev 3b (Dan's answers): his bulkheads are generic JXSS035 AN8 / AN6 tank fittings, male AN flare on top and an
ORB straight thread on the tank side with a nylon washer. The plate gets SAE J1926-1 ports tapped from the
outside (-8 = 3/4-16, -6 = 9/16-18), full thread depth per the EPCO J1926 table, in an 18 mm outside boss.
Under each top port a coaxial -6 ORB port opens on an inside boss: the feed takes a Radium 20-1000-0685
swivel banjo (6AN ORB -> 8.5 mm barb, aimed at the pump), the return a Radium 14-0291 (6AN ORB -> 8.5 mm
barb, pointing down). Pump outlet is 10 mm off the pump axis (option B), pump turned so it faces the feed;
its Radium 20-0598 carries a Radium 14-0296 (6AN female -> 8.5 mm barb). Lower dia 50 section is 28 tall.

Rev 3: RaceFlux (Improved Racing) BMM-08 / BMM-06 male-male bulkheads with BN nuts and HWA PTFE seal
washers on both faces; Dan's Radium 20-0598 check valve sits on the pump outlet (6AN male) and a -6 hose
runs to an FM-08-06 reducer (-8 female -> -6 male) on the -8 bulkhead.

Rev 2: Radium double-sided male bulkheads with jam nuts (Radium 14-0272 for the -6 return; Radium lists no
-8 male bulkhead, so the -8 is a generic AN832-8 style placeholder), 1/4" panel at the fittings, Radium
20-0534-08 check valve stack hung under the -8 bulkhead, 3/8" submersible hose to the pump, -6 return hose.

Frame: Fairsolid run pump_hanger_1009 canonical frame (scan only rotated/moved, never scaled).
+Z points INTO the tank. The OEM steel flange's tank-side face (gasket face) is at z = SEAL_Z.

Kept from the scan (measured in measure.py / loops.py / m2.py):
  flange OD, flange centre, gasket face height, 9 bolt holes (angle + radius), pump axis (from the
  OEM bottom cradle), pump bottom height, electrical pass-through position. (The fuel level sender is a separate part, not on this hanger.)
Changed:
  OEM feed/return tubes removed. -8 AN (feed) and -6 AN (return) tank fittings screw into SAE J1926-1
  ports in an 18 mm outside boss (rev 3b). Bent steel channel replaced by a flat 1/4" 6061 strut, billet
  saddle clamps and a billet foot sized for the Walbro F90000295 (39 mm body / 50 mm lower body,
  131 mm long, maker listing).

Run (WSL, handbuilt-models venv):
  ~/projects/handbuilt-models/.venv/bin/python hanger_billet.py
Writes hanger_*.step / .stl (each billet part, plus the assembly) and hanger_report.json.
"""
import json, math, os
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
IN = 25.4

# ---- interfaces kept from the scan (mm, deg) ----------------------------------------------
C = (2.3, 68.8)            # flange centre (circle fit of the flange edge, z 0.8-3.2)
P = (61.9, 3.2)            # pump axis (circle fit of the OEM bottom C-cradle, z 289-303)
SEAL_Z = 3.8               # tank-side (gasket) face of the OEM flange
FLANGE_R = 60.0            # OEM flange OD 119.7-120.0 -> 120
BOLT_BC_R = 48.6           # 9 holes, radius 48.2-49.5 measured, median 48.6
BOLT_D = 5.5               # measured 5.0-5.9 -> 5.5 (M5 stud clearance), check against the tank studs
BOLT_ANG = [-154.7, -105.1, -55.3, -31.1, -6.3, 73.9, 104.1, 154.6, 179.8]   # from flange centre, +X = 0
PUMP_BOTTOM_Z = 290.3      # OEM pump seat: upward face of the OEM bottom cradle, z 290.0-290.5 (rev 4)

# ---- billet top plate ----------------------------------------------------------------------
RIM_T = 5.0                # flange rim at the bolt circle (OEM 3.8; +1.2 mm, check stud length)
PLATE_T = 7.8              # plate thickness (z SEAL_Z-7.8 .. SEAL_Z)
SPOT_DEPTH = 0.4           # sealing spot faces, both sides -> 7.0 left at every pass-through
BOLT_SPOT_D = 12.0         # outside spot face at each bolt hole, down to RIM_T (M5 nut + socket)
EDGE_BREAK = 0.3           # break on every sealing-face edge (hole edge + spot-face rim), both sides
EDGE_CH = 0.5              # flange OD edge break

# ---- pass-throughs: (id, rel XY, hole dia, spot face dia, keep-out radius for nut socket / terminal, what) ----
# bulkhead holes: Duolok AN bulkhead union panel drills (3/4-16: 49/64", 9/16-18: 37/64");
# stud hole: Radium 17-0048 "Drilled Hole Diameter: 0.220-0.234 (15/64 drill)", material 0.262-0.322".
# sealing spot faces (both sides) >= sealing-washer OD: -8 washer ~25.3 -> dia 30; -6 washer ~20 -> dia 24;
# stud insulator / lower insulating washer + #10-32 nut -> dia 16. Positions: placement.json (place.py, scipy DE).
PASS = [
    ("P1", (22.46, -10.42), 49 / 64 * IN, 30.0, 16.6, "-8 AN bulkhead (feed), 3/4-16"),
    ("P2", (26.07, 20.01), 37 / 64 * IN, 24.0, 13.9, "-6 AN bulkhead (return), 9/16-18"),
    ("S1", (2.81, 15.86), 0.228 * IN, 16.0, 8.0, "isolated stud: pump +"),
    ("S2", (0.62, 35.37), 0.228 * IN, 16.0, 8.0, "isolated stud: pump -"),
]
FEED_XY = PASS[0][1]
RET_XY = PASS[1][1]
INSIDE_KEEPOUT_H = 45.0    # depth below the gasket face kept clear for hose ends / nuts / terminals

# ---- pump outlet and Radium 20-0598 (fit check only) ------------------------------------------
ENGAGE = 12.0
ADP_TIP_ABOVE_CAN = 60.0          # 20-0598 6AN tip above the pump can top: envelope seated on the outlet nipple (photo-scaled; pump cap not modelled)
ADP_AN_L, ADP_HEX, ADP_HEX_L, ADP_BASE_D, ADP_BASE_L = 13.5, 22.2, 29.5, 30.0, 7.0   # photo-scaled, placeholder
PUMP_OUTLET_OFF = 10.0            # Dan: outlet 10 mm off the pump axis (option B); pump turned to face the feed

# ---- rev 6 lightening (Dan: relief in the hanger base and arm, open the pump foot, no sharp points) ----
PLATE_RELIEF_D = 3.0        # tank-side relief pocket depth in the top plate (7.8 -> 4.8 web)
PLATE_RELIEF_R = 40.0       # relief stays inside this radius (gasket/bolt ring untouched)
PLATE_RELIEF_WALL = 3.0     # wall to every seal spot face, lug base (+ fillet) and bolt spot face
TOOL_R = 4.0                # min inside radius of every pocket/slot (8 mm cutter)
STRUT_SLOT_W = (10.0, 14.0) # lightening pocket width: diagonal, lower arm
STRUT_POCKET_FLOOR = 2.5   # rev 7: blind pockets from the strut back face, 2.5 floor left (Dan: nothing machined through)
FOOT_POCKET_DEPTH = 5.0    # rev 7: blind kidney pockets from the foot bottom (8.7 floor -> 3.7 left under the seat)
FOOT_SIDE_WALL = 3.0       # rev 7: radial side holes stop 3 mm short of the inlet bore
# rev 7 bolt-on lug block (Dan: bolt the mounting block on instead of machining it from the plate)
BLOCK_BASE_N0 = -27.5      # base flange reaches back to n = -27.5 (behind the upright)
BLOCK_BASE_T = 8.0         # base flange thickness on the plate's tank face
BLOCK_BASE_HALF_W = 23.0   # base flange half-width along u (upright stays +-LUG_W/2)
BLOCK_SCREWS = [(-9.0, -20.2), (9.0, -20.2)]    # 2x M5 SHCS down into blind tapped holes in the plate (u, n)
BLOCK_DOWELS = [(-18.5, -20.2), (18.5, -20.2)]  # 2x dia 4 dowel pins (u, n)
PLATE_TAP_DEPTH = 6.0      # M5 tap drill 4.2 x 6.0 deep from the tank face: 1.8 left to the outside face
DOWEL_DEPTH = 4.0
STRUT_SLOT_LOW_Z = (206.0, 278.0)   # lower-arm slot between the saddle screws and the foot screws
FOOT_ROUND = 4.0            # foot plan outline: every convex corner R4 (no sharp points)
FOOT_SIDE_HOLES = (4.5, 3.5) # radial drilled side windows into the inlet bore: dia, +-offset (2 per side)
FOOT_FLOOR_WIN = (17.5, 24.0, 30.0)   # floor kidney windows: r_in, r_out, arc span deg (through the cup floor)

# ---- strut, clamps, foot --------------------------------------------------------------------
STRUT_T = 0.25 * IN        # 1/4" 6061 plate
STRUT_W = 36.0             # width along the strut plane
PUMP_OFF = 27.0            # pump axis distance from the strut face
SIDE = -1                  # which way the strut plane is turned from the C->P line (+1/-1)
STRUT_LOW_OFF = 10.2       # rev 4: OEM lower channel centre is 10.2 mm off the pump axis, toward the plate centre (scan)
Z_BEND1, Z_BEND2 = SEAL_Z + 30.0, 110.0   # rev 4: diagonal from the lug top to z 110, like the OEM strut (was 55 -> 130)
BEND_R = 15.0
LUG_T, LUG_H, LUG_W = 8.0, 30.0, 36.0     # rev 2: 8 thick (was 12) to make room for the -6 behind it
LUG_FILLET = 3.0
LUG_BOLT_D = 6.6           # 2x M6
CLAMP_Z = [(175.0, 201.0)]   # rev 4: one clamp (Dan). Scan shows no OEM body clamp (only the bottom cradle), so it sits on the upper body just below the outlet
CLAMP_BORE = 41.5          # 39 body + 1.25 mm rubber strip each side
# rev 5 low-profile clamp (Dan: the bolted ears stuck out into the tank baffles): narrow saddle on the strut side
# + a stainless worm-drive hose-clamp band (12.7 wide, SAE #24 size, 27-51 mm range) around pump + saddle + strut,
# worm housing behind the strut. Nothing sits more than ~3 mm outside the pump body except on the strut side.
SADDLE_N = PUMP_OFF - 6.0  # saddle depth from the strut face (stops 6 mm short of the pump axis plane)
SADDLE_U_PLUS = 22.0       # saddle edge on the free side, from the pump axis (pump radius 19.5 + 2.5)
BAND_W, BAND_T = 12.7, 0.6 # worm-drive band width / thickness
BAND_Z = (176.5, 189.2)    # band position on the saddle (below the saddle screws)
SADDLE_SCREW_Z = 196.0     # saddle screws from the strut back, above the band
WORM = (26.0, 9.0, 15.0)   # worm housing envelope: along the band (u), radial (n), along z (placeholder, SAE #24 clamp)
CLAMP_HALF_W = 38.0   # ear screws at +-33, clear of the ring-to-ear fillet so the heads sit flat
STRAP_T = 5.0
M5_TAP, M5_CLR = 4.2, 5.5
FOOT_Z = (283.0, 299.0)   # bottom 299 (OEM cradle bottom 302)
FOOT_SCREW_Z = 295.0
M4_TAP, M4_CLR = 3.3, 4.5
FOOT_POCKET_D = 51.0       # 50 lower body + rubber
FOOT_HOLE_D = 30.0         # inlet / sock opening, open toward the free side (C-shape like OEM)

# ---- pump: Walbro F90000295 (maker listing: 131 long, 39 main body, 50 lower body, 11 outlet) ---
PUMP_L, PUMP_D, PUMP_LOW_D, PUMP_LOW_L, OUTLET_D, OUTLET_L = 131.0, 39.0, 50.0, 28.0, 11.0, 12.0   # Dan: dia 50 section 28 tall

# ----------------------------------------------------------------------------------------------
dx, dy = P[0] - C[0], P[1] - C[1]
dist = math.hypot(dx, dy)
theta = SIDE * math.asin(PUMP_OFF / dist)
a0 = math.atan2(dy, dx)
D = (math.cos(a0 + theta), math.sin(a0 + theta))           # strut plane direction (u)
N = (-D[1], D[0])                                          # strut normal
if (dx * N[0] + dy * N[1]) < 0:                            # make +N point toward the pump
    N = (-N[0], -N[1])
UP = dx * D[0] + dy * D[1]                                 # pump position along u
U_STRUT_LOW = UP - STRUT_LOW_OFF                           # lower strut centre (OEM channel sits off the pump axis)
STRUT_SCREW_U = (U_STRUT_LOW - 10.0, U_STRUT_LOW + 10.0)    # clamp / foot screws through the lower strut



def un_xy(u, n):
    return (u * D[0] + n * N[0], u * D[1] + n * N[1])          # relative to C


Z_OUT = SEAL_Z - PLATE_T                                        # outside face of the plate
CAN_TOP = PUMP_BOTTOM_Z - PUMP_L + OUTLET_L
Z_ADP_TIP = CAN_TOP - ADP_TIP_ABOVE_CAN                         # Radium 20-0598 6AN tip (points at the plate)
_o = Vector(C[0] + FEED_XY[0] - P[0], C[1] + FEED_XY[1] - P[1], 0).normalized()
O = (P[0] + PUMP_OUTLET_OFF * _o.X, P[1] + PUMP_OUTLET_OFF * _o.Y)   # pump outlet axis (pump rotated to face the feed)


def W(u, n, z):
    """strut coordinates (u along the plane, n toward the pump, z) -> frame xyz"""
    return Vector(C[0] + u * D[0] + n * N[0], C[1] + u * D[1] + n * N[1], z)


def strut_plane(n):
    # local x = u, local y = world +Z, local z = -N (so extrusions go away from the pump)
    return Plane(origin=W(0, n, 0), x_dir=(D[0], D[1], 0), z_dir=(-N[0], -N[1], 0))


def rel(xy):
    return Vector(C[0] + xy[0], C[1] + xy[1], 0)


def block(u0, u1, n0, n1, z0, z1):
    pl = strut_plane(n1)
    with BuildPart() as b:
        with BuildSketch(pl):
            with Locations(((u0 + u1) / 2, (z0 + z1) / 2)):
                Rectangle(u1 - u0, z1 - z0)
        extrude(amount=n1 - n0)
    return b.part


def hole_n(part, u, z, n0, n1, d):
    """drill along N through n0..n1 at (u, z)"""
    pl = strut_plane(n1)
    with BuildPart() as h:
        with BuildSketch(pl):
            with Locations((u, z)):
                Circle(d / 2)
        extrude(amount=n1 - n0)
    return part - h.part


def shp_to_faces(geom, to_xy, z):
    """shapely (Multi)Polygon in some 2D frame -> list of build123d faces at height z (holes kept)"""
    from shapely.geometry import MultiPolygon
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    faces = []
    for pg in polys:
        if pg.is_empty or pg.area < 1.0:
            continue
        outer = [Vector(*to_xy(x, y), z) for x, y in list(pg.exterior.coords)[:-1]]
        f = Face(Wire.make_polygon(outer, close=True))
        for hole in pg.interiors:
            hw = [Vector(*to_xy(x, y), z) for x, y in list(hole.coords)[:-1]]
            f = f - Face(Wire.make_polygon(hw, close=True))
        faces += f.faces() if hasattr(f, "faces") else [f]
    return faces


def plate_relief():
    """tank-side relief pocket: free area inside PLATE_RELIEF_R, away from seal faces, lug and bolt spot faces"""
    from shapely.geometry import Point, Polygon as SPoly
    from shapely.ops import unary_union
    keep = [Point(xy).buffer(sp / 2 + PLATE_RELIEF_WALL, 64) for _, xy, _, sp, _, _ in PASS]
    lug = [un_xy(u, n) for u, n in [(-BLOCK_BASE_HALF_W, BLOCK_BASE_N0), (BLOCK_BASE_HALF_W, BLOCK_BASE_N0), (BLOCK_BASE_HALF_W, -STRUT_T), (-BLOCK_BASE_HALF_W, -STRUT_T)]]
    keep.append(SPoly(lug).buffer(PLATE_RELIEF_WALL, join_style=2))     # bolt-on block footprint
    for a in BOLT_ANG:
        r = math.radians(a)
        keep.append(Point(BOLT_BC_R * math.cos(r), BOLT_BC_R * math.sin(r)).buffer(BOLT_SPOT_D / 2 + PLATE_RELIEF_WALL, 64))
    region = Point(0, 0).buffer(PLATE_RELIEF_R, 128).difference(unary_union(keep))
    region = region.buffer(-TOOL_R).buffer(TOOL_R)          # rounds every inside corner of the pocket to the cutter radius
    faces = shp_to_faces(region, lambda x, y: (C[0] + x, C[1] + y), SEAL_Z - PLATE_RELIEF_D)
    cut = None
    for f in faces:
        sol = extrude(f, amount=PLATE_RELIEF_D + 1, dir=(0, 0, 1))
        cut = sol if cut is None else cut + sol
    return cut, region.area


# ---- 1. top plate -----------------------------------------------------------------------------
SKIPPED_FILLETS = []


def flange():
    """flange rev G: top plate + L block (upright + base) as ONE billet. Order: solids -> holes/pockets -> chamfer -> fillets."""
    part = Pos(C[0], C[1], Z_OUT) * Cylinder(FLANGE_R, PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = part + block(-LUG_W / 2, LUG_W / 2, -STRUT_T - LUG_T, -STRUT_T, SEAL_Z, SEAL_Z + LUG_H)
    part = part + block(-BLOCK_BASE_HALF_W, BLOCK_BASE_HALF_W, BLOCK_BASE_N0, -STRUT_T, SEAL_Z, SEAL_Z + BLOCK_BASE_T)
    # outside bolt spot faces (rim 5.0 at the bolt circle)
    for a in BOLT_ANG:
        r = math.radians(a)
        part = part - Pos(C[0] + BOLT_BC_R * math.cos(r), C[1] + BOLT_BC_R * math.sin(r), Z_OUT - 1) * \
            Cylinder(BOLT_SPOT_D / 2, PLATE_T - RIM_T + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 4 pass-throughs: clearance hole + 0.4 sealing spot face both sides
    for pid, xy, hole, spot, _, _ in PASS:
        at = rel(xy)
        part = part - zcyl(at, hole, Z_OUT - 1, SEAL_Z + 1)
        part = part - zcyl(at, spot, Z_OUT - 1, Z_OUT + SPOT_DEPTH)
        part = part - zcyl(at, spot, SEAL_Z - SPOT_DEPTH, SEAL_Z + 1)
    # 9 flange screw holes (only through the plate / rim)
    for a in BOLT_ANG:
        r = math.radians(a)
        part = part - Pos(C[0] + BOLT_BC_R * math.cos(r), C[1] + BOLT_BC_R * math.sin(r), Z_OUT - 1) * \
            Cylinder(BOLT_D / 2, PLATE_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # tank-side relief pocket (3 mm off the block footprint, seal faces and bolt spot faces)
    relief, _ = plate_relief()
    if relief is not None:
        part = part - relief
    # 2 x dia 6.6 M6 strut cross-holes through the upright (along N)
    for u in (-LUG_W / 2 + 8, LUG_W / 2 - 8):
        part = hole_n(part, u, SEAL_Z + LUG_H / 2 + 3, -STRUT_T - LUG_T - 1, -STRUT_T + 1, LUG_BOLT_D)
    # flange OD break (0.5 chamfer)
    rim = [e for e in part.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - FLANGE_R) < 0.01]
    try:
        part = chamfer(rim, EDGE_CH)
    except Exception as ex:
        SKIPPED_FILLETS.append(f"flange OD chamfer 0.5: {ex}")
    # ---- fillets LAST ----
    zt = SEAL_Z + BLOCK_BASE_T
    def un(e):
        c = e.center()
        return ((c.X - C[0]) * D[0] + (c.Y - C[1]) * D[1], (c.X - C[0]) * N[0] + (c.Y - C[1]) * N[1])
    inner = []
    for e in part.edges().filter_by(GeomType.LINE):
        if abs(e.center().Z - zt) > 0.01:
            continue
        u, n = un(e)
        if abs(n - (-STRUT_T - LUG_T)) < 0.01 and abs(u) < LUG_W / 2 + 0.01:
            inner.append(("upright back / base R3", e))
        elif abs(abs(u) - LUG_W / 2) < 0.01 and -STRUT_T - LUG_T - 0.01 < n < -STRUT_T + 0.01:
            inner.append(("upright side / base R3", e))
    try:
        part = fillet([e for _, e in inner], LUG_FILLET)
    except Exception:
        for nm, e in inner:                       # one at a time; skip and list the ones that fail
            try:
                ee = [x for x in part.edges() if (x.center() - e.center()).length < 0.01 and abs(x.length - e.length) < 0.01]
                part = fillet(ee, LUG_FILLET)
            except Exception as ex:
                SKIPPED_FILLETS.append(f"{nm} at {tuple(round(v, 1) for v in e.center())}: {ex}")
    print("fillets: %d edges selected, skipped: %s" % (len(inner), SKIPPED_FILLETS or "none"))
    return part


def keepouts():
    """inside-tank keep-out cylinders for nut sockets / hose ends / stud terminals (fit check only)"""
    k = None
    for pid, xy, hole, spot, r, _ in PASS:
        c = zcyl(rel(xy), 2 * r, SEAL_Z, SEAL_Z + INSIDE_KEEPOUT_H)
        k = c if k is None else k + c
    return k


# ---- 2. strut ----------------------------------------------------------------------------------
def strut():
    u_lo0, u_hi0 = -STRUT_W / 2, STRUT_W / 2
    u_lo1, u_hi1 = U_STRUT_LOW - STRUT_W / 2, U_STRUT_LOW + STRUT_W / 2
    zb = FOOT_Z[1]
    zs = SEAL_Z + LUG_FILLET + 0.5                     # clear of the lug-base fillet
    pts = [(u_lo0, zs), (u_hi0, zs), (u_hi0, Z_BEND1), (u_hi1, Z_BEND2), (u_hi1, zb),
           (u_lo1, zb), (u_lo1, Z_BEND2 + 12), (u_lo0, Z_BEND1 + 12)]
    pl = strut_plane(0)
    with BuildPart() as s:
        with BuildSketch(pl) as sk:
            Polygon(*pts, align=None)
            fillet(sk.vertices().filter_by_position(Axis.Y, zs + 1, zb - 1, inclusive=(False, False)), BEND_R)
        extrude(amount=STRUT_T)
    part = s.part
    # rev 6: lightening through-slots (R = half width, stadium ends)
    a0 = Vector((u_lo0 + u_hi0) / 2, Z_BEND1 + 6, 0)
    a1 = Vector(U_STRUT_LOW, Z_BEND2 + 6, 0)
    t = 0.30, 0.78
    s0 = a0 + (a1 - a0) * t[0]
    s1 = a0 + (a1 - a0) * t[1]
    slots = [(s0, s1, STRUT_SLOT_W[0]),
             (Vector(U_STRUT_LOW, STRUT_SLOT_LOW_Z[0], 0), Vector(U_STRUT_LOW, STRUT_SLOT_LOW_Z[1], 0), STRUT_SLOT_W[1])]
    depth = STRUT_T - STRUT_POCKET_FLOOR
    pk = strut_plane(-STRUT_T + depth)                  # pocket from the back face (n = -STRUT_T), floor toward the pump
    for q0, q1, w in slots:
        with BuildPart() as sl:
            with BuildSketch(pk):
                SlotCenterPoint(((q0.X + q1.X) / 2, (q0.Y + q1.Y) / 2), (q1.X, q1.Y), w)
            extrude(amount=depth + 1)
        part = part - sl.part
    # lug bolts
    for u in (-LUG_W / 2 + 8, LUG_W / 2 - 8):
        part = hole_n(part, u, SEAL_Z + LUG_H / 2 + 3, -STRUT_T - 1, 1, LUG_BOLT_D)
    # clamp + foot screws (M5 clearance through the strut)
    for u in STRUT_SCREW_U:
        part = hole_n(part, u, SADDLE_SCREW_Z, -STRUT_T - 1, 1, M5_CLR)
    for u in STRUT_SCREW_U:
        part = hole_n(part, u, FOOT_SCREW_Z, -STRUT_T - 1, 1, M4_CLR)
    return part


# ---- 3. clamps: saddle (on the strut) + strap -------------------------------------------------
def pump_axis_cyl(d, z0, z1):
    return Pos(P[0], P[1], z0) * Cylinder(d / 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def saddle(z0, z1):
    """narrow saddle between strut and pump: dia 41.5 bore for the rubber-wrapped pump, band groove, 2 screws from the strut"""
    u0 = U_STRUT_LOW - STRUT_W / 2
    part = block(u0, UP + SADDLE_U_PLUS, 0, SADDLE_N, z0, z1)
    part = part - pump_axis_cyl(CLAMP_BORE, z0 - 1, z1 + 1)
    for u in STRUT_SCREW_U:               # tapped from the strut side
        part = hole_n(part, u, SADDLE_SCREW_Z, 0, 12, M5_TAP)
    return part


def band_envelope():
    """worm-drive band around pump + saddle + strut, worm housing behind the strut (fit check only)"""
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    u0 = U_STRUT_LOW - STRUT_W / 2
    r_in = CLAMP_BORE / 2
    inner = unary_union([Point(UP, PUMP_OFF).buffer(r_in, 128),
                         box(u0, -STRUT_T, UP + SADDLE_U_PLUS, SADDLE_N)]).convex_hull
    outer = inner.buffer(BAND_T, join_style=2)
    ring = outer.difference(inner)
    pts = [(x, y) for x, y in list(ring.exterior.coords)[:-1]]
    hole = [(x, y) for x, y in list(ring.interiors[0].coords)[:-1]]
    pl = strut_plane(0)
    # the strut plane maps local (u, z) -> world; build the band in a horizontal plane instead
    def w(u, n):
        p = W(u, n, 0)
        return (p.X, p.Y)
    with BuildPart() as b:
        with BuildSketch(Plane.XY.offset(BAND_Z[0])):
            Polygon(*[w(u, n) for u, n in pts], align=None)
            Polygon(*[w(u, n) for u, n in hole], align=None, mode=Mode.SUBTRACT)
        extrude(amount=BAND_Z[1] - BAND_Z[0])
    band = b.part
    # worm housing behind the strut, centred on the lower strut
    wu, wn, wz = WORM
    zc = (BAND_Z[0] + BAND_Z[1]) / 2
    band += block(U_STRUT_LOW - wu / 2, U_STRUT_LOW + wu / 2, -STRUT_T - BAND_T - wn, -STRUT_T - BAND_T, zc - wz / 2, zc + wz / 2)
    return band


# ---- 4. foot ---------------------------------------------------------------------------------
def foot():
    """rev 6: rounded plan outline (no points), side windows into the inlet bore, floor kidney windows,
    back-pad pockets from below; pump still seats on a ring around the inlet"""
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    z0, z1 = FOOT_Z
    r = FOOT_POCKET_D / 2 + 6
    u_back0 = U_STRUT_LOW - STRUT_W / 2
    plan = unary_union([Point(UP, PUMP_OFF).buffer(r, 128), box(u_back0, 0, UP + SADDLE_U_PLUS, PUMP_OFF)])
    plan = plan.difference(box(UP - FOOT_HOLE_D / 2, PUMP_OFF, UP + FOOT_HOLE_D / 2, PUMP_OFF + r + 5))   # sock opening
    plan = plan.difference(Point(UP, PUMP_OFF).buffer(FOOT_HOLE_D / 2, 128))                            # inlet bore
    plan = plan.buffer(-FOOT_ROUND).buffer(FOOT_ROUND)       # round every convex corner R4 (kills the points)
    plan = plan.buffer(FOOT_ROUND).buffer(-FOOT_ROUND)       # and every concave corner R4 (cutter)
    to_xy = lambda u, n: (W(u, n, 0).X, W(u, n, 0).Y)
    faces = shp_to_faces(plan, to_xy, z0)
    part = None
    for f in faces:
        sol = extrude(f, amount=z1 - z0, dir=(0, 0, 1))
        part = sol if part is None else part + sol
    part = part - pump_axis_cyl(FOOT_POCKET_D, z0 - 1, PUMP_BOTTOM_Z)
    # floor kidney windows (through the cup floor), away from the sock opening (+n) and the strut (-n)
    from shapely.geometry import Polygon as SPoly
    ri, ro, span = FOOT_FLOOR_WIN
    for mid in (50.0, 130.0, -50.0, -130.0):              # degrees from +u toward +n... measured in the (u, n) plane
        angs = [math.radians(mid - span / 2 + span * k / 24) for k in range(25)]
        ring = [(UP + ro * math.cos(a), PUMP_OFF + ro * math.sin(a)) for a in angs] + \
               [(UP + ri * math.cos(a), PUMP_OFF + ri * math.sin(a)) for a in reversed(angs)]
        h = (ro - ri) / 2 - 0.01
        kid = SPoly(ring).buffer(-h).buffer(h, resolution=32)      # full-radius ends (R = half the slot width)
        for f in shp_to_faces(kid, to_xy, z1 - FOOT_POCKET_DEPTH):
            part = part - extrude(f, amount=FOOT_POCKET_DEPTH + 1, dir=(0, 0, 1))      # blind, from the bottom face
    # radial drilled side windows (2 per free side) from the outer face into the inlet bore, mid-slab
    zc = (PUMP_BOTTOM_Z + z1) / 2
    dia, off = FOOT_SIDE_HOLES
    for sgn in (1.0, -1.0):                                 # along +-u (the two free sides)
        for dn in (-off, off):
            start = W(UP + sgn * (FOOT_HOLE_D / 2 + FOOT_SIDE_WALL), PUMP_OFF + dn, zc)   # blind: stops short of the inlet bore
            pl = Plane(origin=start, z_dir=(sgn * D[0], sgn * D[1], 0))
            with BuildPart() as w:
                with BuildSketch(pl):
                    Circle(dia / 2)
                extrude(amount=r + 10)
            part = part - w.part
    part = part.intersect(block(UP - r - 10, UP + r + 10, 0, PUMP_OFF + r + 10, z0 - 1, z1 + 1))   # nothing behind the strut face
    for u in STRUT_SCREW_U:
        part = hole_n(part, u, FOOT_SCREW_Z, 0, 10, M4_TAP)
    return part


# ---- bought parts, for pictures and clearance only --------------------------------------------
def hexagon(af, h, at, z0):
    with BuildPart() as hx:
        with BuildSketch(Plane.XY.offset(z0)):
            with Locations(at):
                RegularPolygon(af / math.sqrt(3), 6)
        extrude(amount=h)
    return hx.part


def zcyl(at, d, z0, z1):
    return Pos(at.X, at.Y, z0) * Cylinder(d / 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def check_valve_envelope():
    """Radium 20-0598 on the pump outlet: placeholder envelope for fit checks only"""
    o = Vector(O[0], O[1], 0)
    adp = zcyl(o, 14.0, Z_ADP_TIP, Z_ADP_TIP + ADP_AN_L)
    adp += hexagon(ADP_HEX, ADP_HEX_L, (o.X, o.Y), Z_ADP_TIP + ADP_AN_L)
    adp += zcyl(o, ADP_BASE_D, Z_ADP_TIP + ADP_AN_L + ADP_HEX_L, Z_ADP_TIP + ADP_AN_L + ADP_HEX_L + ADP_BASE_L)
    return adp


def pump():
    p = pump_axis_cyl(PUMP_LOW_D, PUMP_BOTTOM_Z - PUMP_LOW_L, PUMP_BOTTOM_Z)
    p += pump_axis_cyl(PUMP_D, CAN_TOP, PUMP_BOTTOM_Z - PUMP_LOW_L)
    p += zcyl(Vector(O[0], O[1], 0), OUTLET_D, PUMP_BOTTOM_Z - PUMP_L, CAN_TOP)          # outlet 10 mm off axis
    return p


if __name__ == "__main__":
    parts = {"flange": flange()}
    parts["strut"] = strut()
    for i, (z0, z1) in enumerate(CLAMP_Z):
        parts[f"saddle{i+1}"] = saddle(z0, z1)
    parts["foot"] = foot()
    bought = {"check_valve_radium_20-0598": check_valve_envelope(),
              "pump_f90000295": pump()}
    bought["inside_keepouts"] = keepouts()
    bought["band_clamp_worm_drive"] = band_envelope()
    cv_info = {pid: {"rel_xy": [round(xy[0], 2), round(xy[1], 2)], "hole": round(h, 2), "spot": sp, "what": w}
               for pid, xy, h, sp, _, w in PASS}
    cv_info["pump_outlet_xy"] = [round(O[0], 1), round(O[1], 1)]
    rep = {"ports": cv_info, "strut_dir": D, "strut_normal": N, "pump_u": UP, "parts": {}, "clear": {}}
    for dct in (parts, bought):
        for k in dct:
            if isinstance(dct[k], ShapeList):
                print("note:", k, "came out as", len(dct[k]), "pieces")
                dct[k] = Compound(children=list(dct[k]))
    for k, s in list(parts.items()) + list(bought.items()):
        export_step(s, os.path.join(HERE, f"fuel-hanger-{k}.step"))
        bb = s.bounding_box()
        rep["parts"][k] = {"volume_cm3": round(s.volume / 1000, 2), "mass_g": round(s.volume * 2.70e-3, 0),
                           "valid": s.is_valid, "solids": len(s.solids()),
                           "bbox": [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)]}
    # clearances: every pair (minimum distance; 0 = touching or overlapping)
    names = list(parts) + list(bought)
    allp = {**parts, **bought}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = allp[a].distance_to(allp[b])
            ov = (allp[a] & allp[b]).volume if d < 1e-6 else 0.0
            if d < 3.0:
                rep["clear"][f"{a}|{b}"] = {"min_gap_mm": round(d, 2), "overlap_mm3": round(ov, 2)}
    billet = Compound(children=list(parts.values()))
    export_step(billet, os.path.join(HERE, "fuel-hanger-assembly.step"))
    full = Compound(children=list(parts.values()) + list(bought.values()))
    rep["skipped_fillets"] = SKIPPED_FILLETS
    rep["billet_mass_g"] = round(sum(v["mass_g"] for k, v in rep["parts"].items() if k in parts), 0)
    json.dump(rep, open(os.path.join(HERE, "fuel-hanger-report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))
