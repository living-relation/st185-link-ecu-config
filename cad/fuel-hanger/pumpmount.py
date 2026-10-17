"""ST185 fuel hanger - pump holder helpers (saddle FH-105 + foot FH-104), from the 2026-10-17 study. build123d.
Library only: sketch helpers in the strut frame (u, n, z), the study foot/strut builders, fillet_last (failures skipped and
listed), STEP round trip. Reuses fuel_hanger.py (flange G, strut base geometry, envelopes) unchanged.
The parts are built by build_holder.py (via pump_holder.py)."""
import json, math, os, sys
MYDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MYDIR)
import fuel_hanger as fh
from fuel_hanger import *          # noqa
from shapely.geometry import Point, box, Polygon as SPoly
from shapely.ops import unary_union

OUT = MYDIR
RHO = 2.70e-3
UP, PO, UL = fh.UP, fh.PUMP_OFF, fh.U_STRUT_LOW
R_RUB = fh.CLAMP_BORE / 2          # 20.75 pump + rubber
U_BACK0 = UL - fh.STRUT_W / 2      # 56.2 strut lower edge
U_BACK1 = UL + fh.STRUT_W / 2      # 92.2
SKIPPED = {}

def to_xy(u, n):
    p = W(u, n, 0); return (p.X, p.Y)

def prism(geom, z0, z1):
    part = None
    for f in shp_to_faces(geom, to_xy, z0):
        s = extrude(f, amount=z1 - z0, dir=(0, 0, 1))
        part = s if part is None else part + s
    return part

def round2d(g, r):
    return g.buffer(-r).buffer(r).buffer(r).buffer(-r)

def cs_hole_from_back(part, u, z, d_clr=4.5, d_head=8.4, depth=None):
    """M4 flat-head: clearance through the strut + 90 deg countersink from the strut back (n = -STRUT_T)"""
    part = hole_n(part, u, z, -fh.STRUT_T - 1, 1, d_clr)
    h = (d_head - d_clr) / 2
    pl = Plane(origin=W(u, -fh.STRUT_T, z), z_dir=(N[0], N[1], 0))
    cone = pl * Cone(d_head / 2, d_clr / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part - cone

def fillet_last(part, edges, r, tag, fallback=(0.5,)):
    if not edges:
        return part
    for rr in (r,) + tuple(fallback):
        try:
            out = fillet(edges, rr)
            if rr != r:
                SKIPPED.setdefault(tag + " (info)", []).append(f"R{r} failed on the whole set, R{rr} applied")
            return out
        except Exception:
            pass
    try:
        raise RuntimeError
    except Exception:
        out = part
        for e in edges:
            try:
                ee = [x for x in out.edges() if (x.center() - e.center()).length < 0.01]
                out = fillet(ee, fallback[-1])
            except Exception as ex:
                SKIPPED.setdefault(tag, []).append(f"R{fallback[-1]} at {tuple(round(v,1) for v in e.center())}: {type(ex).__name__}")
        return out

def outer_top_bottom_edges(part, z0, z1, keep=lambda e: True):
    es = []
    for e in part.edges():
        c = e.center()
        if (abs(c.Z - z0) < 0.01 or abs(c.Z - z1) < 0.01) and keep(e):
            es.append(e)
    return es

# ---------------- strut variants (copy of fh.strut with parametrised holes) ----------------
def strut_variant(saddle_holes, foot_holes, zb=None):
    """saddle_holes / foot_holes: list of (u, z, kind) kind = 'M5' clearance, 'M4' clearance, 'M4cs' countersunk"""
    S = fh.STRUT_T
    u_lo0, u_hi0 = -fh.STRUT_W / 2, fh.STRUT_W / 2
    u_lo1, u_hi1 = UL - fh.STRUT_W / 2, UL + fh.STRUT_W / 2
    zb = zb or fh.FOOT_Z[1]
    zs = fh.SEAL_Z + fh.LUG_FILLET + 0.5
    pts = [(u_lo0, zs), (u_hi0, zs), (u_hi0, fh.Z_BEND1), (u_hi1, fh.Z_BEND2), (u_hi1, zb),
           (u_lo1, zb), (u_lo1, fh.Z_BEND2 + 12), (u_lo0, fh.Z_BEND1 + 12)]
    pl = strut_plane(0)
    with BuildPart() as s:
        with BuildSketch(pl) as sk:
            Polygon(*pts, align=None)
            fillet(sk.vertices().filter_by_position(Axis.Y, zs + 1, zb - 1, inclusive=(False, False)), fh.BEND_R)
        extrude(amount=S)
    part = s.part
    a0 = Vector((u_lo0 + u_hi0) / 2, fh.Z_BEND1 + 6, 0); a1 = Vector(UL, fh.Z_BEND2 + 6, 0)
    s0 = a0 + (a1 - a0) * 0.30; s1 = a0 + (a1 - a0) * 0.78
    slots = [(s0, s1, fh.STRUT_SLOT_W[0]),
             (Vector(UL, fh.STRUT_SLOT_LOW_Z[0], 0), Vector(UL, fh.STRUT_SLOT_LOW_Z[1], 0), fh.STRUT_SLOT_W[1])]
    depth = S - fh.STRUT_POCKET_FLOOR
    pk = strut_plane(-S + depth)
    for q0, q1, w in slots:
        with BuildPart() as sl:
            with BuildSketch(pk):
                SlotCenterPoint(((q0.X + q1.X) / 2, (q0.Y + q1.Y) / 2), (q1.X, q1.Y), w)
            extrude(amount=depth + 1)
        part = part - sl.part
    for u in (-fh.LUG_W / 2 + 8, fh.LUG_W / 2 - 8):
        part = hole_n(part, u, fh.SEAL_Z + fh.LUG_H / 2 + 3, -S - 1, 1, fh.LUG_BOLT_D)
    for u, z, kind in saddle_holes + foot_holes:
        if kind == "M5":
            part = hole_n(part, u, z, -S - 1, 1, fh.M5_CLR)
        elif kind == "M4":
            part = hole_n(part, u, z, -S - 1, 1, fh.M4_CLR)
        else:
            part = cs_hole_from_back(part, u, z)
    return part

# ---------------- true-arc sketch helpers: plane local x = u, local y = n ----------------
def un_plane(z):
    return Plane(origin=(fh.C[0], fh.C[1], z), x_dir=(D[0], D[1], 0), z_dir=(0, 0, 1))

def sk_round(sk, r):
    """2D fillet every vertex of the sketch (convex + concave = cutter radius); skip the ones that fail"""
    vs = sk.vertices()
    try:
        fillet(vs, r)
        return 0
    except Exception:
        bad = 0
        for v in vs:
            try:
                fillet(sk.vertices().filter_by(lambda x: (Vector(x) - Vector(v)).length < 1e-3), r)
            except Exception:
                bad += 1
        return bad

def rect_un(u0, n0, u1, n1, mode=Mode.ADD):
    with Locations(((u0 + u1) / 2, (n0 + n1) / 2)):
        Rectangle(u1 - u0, n1 - n0, mode=mode)

def circ_un(u, n, r, mode=Mode.ADD):
    with Locations((u, n)):
        Circle(r, mode=mode)

# ---------------- saddles ----------------
def saddle_current():
    return fh.saddle(*fh.CLAMP_Z[0])

TRIM_N = 15.0    # was SADDLE_N 21: the 17 deg knife-edge horns where the bore met n 21 are gone (35 deg, 5 mm flat)
def saddle_trim(z0, z1):
    """current plan (strut face -> n 21, u strut edge -> pump + 22) minus the bore, corners R2"""
    with BuildPart() as p:
        with BuildSketch(un_plane(z0)) as sk:
            rect_un(U_BACK0, 0, UP + fh.SADDLE_U_PLUS, TRIM_N)
            circ_un(UP, PO, R_RUB, Mode.SUBTRACT)
            sk_round(sk, 1.5)
        extrude(amount=z1 - z0)
    return p.part

def saddle_crescent(z0, z1, screw_us, wall=4.0, pad_n=13.0):
    """crescent hugging the strut side of the pump (4 wall over the rubber) + a pad on the strut face for the screws"""
    with BuildPart() as p:
        with BuildSketch(un_plane(z0)) as sk:
            circ_un(UP, PO, R_RUB + wall)
            rect_un(UP - 40, PO, UP + 40, PO + 40, Mode.SUBTRACT)       # keep the strut-side half only
            rect_un(min(screw_us) - 6.5, 0, max(screw_us) + 6.5, pad_n)
            rect_un(UP - 60, -10, UP + 60, 0, Mode.SUBTRACT)              # nothing behind the strut face
            circ_un(UP, PO, R_RUB, Mode.SUBTRACT)
            sk_round(sk, 1.5)
        extrude(amount=z1 - z0)
    return p.part

def saddle_from(part, screws, tap_d, tap_depth):
    for u, z in screws:
        part = hole_n(part, u, z, 0, tap_depth, tap_d)
    return part

# ---------------- feet ----------------
def foot_current():
    return fh.foot()

def wedge_un(mid_deg, span_deg, r=45.0):
    a0, a1 = math.radians(mid_deg - span_deg / 2), math.radians(mid_deg + span_deg / 2)
    pts = [(UP, PO)] + [(UP + r * math.cos(a0 + (a1 - a0) * k / 6), PO + r * math.sin(a0 + (a1 - a0) * k / 6)) for k in range(7)]
    Polygon(*pts, align=None)

WINDOW_AREA = []
def foot_new(z_lip0, z_bot, wall, windows, screws, tap_depth=10.0, back_u1=None):
    """pump seats on z = PUMP_BOTTOM_Z (unchanged). lip z_lip0..seat locates the dia 50 lower body (0.5 radial gap).
    floor seat..z_bot: ring + back pad on the strut face, inlet bore dia 30 + sock opening toward +n.
    windows: list of (mid_deg, span_deg) through-windows in the floor annulus (deg in (u, n) from +u; -90 = strut)."""
    seat = fh.PUMP_BOTTOM_Z
    r_out = fh.FOOT_POCKET_D / 2 + wall
    hw = fh.FOOT_HOLE_D / 2
    back_u1 = back_u1 or UP + 8
    with BuildPart() as p:
        with BuildSketch(un_plane(seat)) as sk:          # floor
            circ_un(UP, PO, r_out)
            rect_un(U_BACK0 + 2, 0, back_u1, PO)
            rect_un(UP - 60, -10, UP + 60, 0, Mode.SUBTRACT)
            rect_un(UP - hw, PO, UP + hw, PO + 40, Mode.SUBTRACT)
            circ_un(UP, PO, hw, Mode.SUBTRACT)
            sk_round(sk, 2.0)
        extrude(amount=z_bot - seat)
        with BuildSketch(un_plane(z_lip0)) as sk2:       # lip
            circ_un(UP, PO, r_out)
            rect_un(U_BACK0 + 2, 0, back_u1, PO)
            rect_un(UP - 60, -10, UP + 60, 0, Mode.SUBTRACT)
            rect_un(UP - hw, PO, UP + hw, PO + 40, Mode.SUBTRACT)
            circ_un(UP, PO, fh.FOOT_POCKET_D / 2, Mode.SUBTRACT)
            sk_round(sk2, 1.5)
        extrude(amount=seat - z_lip0)
    part = p.part
    if windows:
        ri, ro = hw + 2.5, fh.FOOT_POCKET_D / 2 - 0.5     # windows stay inside the lip pocket: no notch in the lip
        for mid, span in windows:                  # one window per sketch (multi-face sketch INTERSECT drops faces)
            with BuildPart() as w:
                with BuildSketch(un_plane(seat - 1)) as sk3:
                    circ_un(UP, PO, ro)
                    circ_un(UP, PO, ri, Mode.SUBTRACT)
                    a0, a1 = math.radians(mid - span / 2), math.radians(mid + span / 2)
                    pts = [(UP, PO)] + [(UP + 45 * math.cos(a0 + (a1 - a0) * k / 6), PO + 45 * math.sin(a0 + (a1 - a0) * k / 6)) for k in range(7)]
                    Polygon(*pts, align=None, mode=Mode.INTERSECT)
                    rect_un(UP - 60, -10, UP + 60, 5.0, Mode.SUBTRACT)              # >= 5 mm floor left at the strut face
                    if sk3.sketch.area < 4.0:
                        continue
                    sk_round(sk3, min(2.0, (ro - ri) / 2 - 0.05))
                extrude(amount=z_bot - seat + 2)
            WINDOW_AREA.append(round(sk3.sketch.area, 1))
            part = part - w.part
    for u, z in screws:
        part = hole_n(part, u, z, 0, tap_depth, fh.M4_TAP)
    return part

# ---------------- band envelope for any saddle profile ----------------
def band_for(g, z0, z1):
    hull = unary_union([Point(UP, PO).buffer(R_RUB, 64), g, box(U_BACK0, -fh.STRUT_T, U_BACK1, 0)]).convex_hull
    ring = hull.buffer(fh.BAND_T, join_style=2).difference(hull)
    band = prism(ring, z0, z1)
    wu, wn, wz = fh.WORM
    zc = (z0 + z1) / 2
    band += block(UL - wu / 2, UL + wu / 2, -fh.STRUT_T - fh.BAND_T - wn, -fh.STRUT_T - fh.BAND_T, zc - wz / 2, zc + wz / 2)
    return band

# ---------------- options ----------------
SPIDER = [(-62, 46), (-13, 26), (193, 26)]
SPIDER_C = [(-55, 40), (-13, 26), (193, 26)]   # C keeps the M4 tap at u 84.2: window pulled 7 deg off it     # big floor windows; spokes left toward the strut, the sides and the sock edges
def crescent_shp(su, wall=4.0, pad_n=13.0):
    ring = Point(UP, PO).buffer(R_RUB + wall, 64).intersection(box(UP - 40, -1, UP + 40, PO))
    return unary_union([ring, box(min(su) - 6.5, 0, max(su) + 6.5, pad_n)]).intersection(box(UP - 60, 0, UP + 60, 60))

def build(opt):
    S5 = [(u, fh.SADDLE_SCREW_Z) for u in fh.STRUT_SCREW_U]
    F4 = [(u, fh.FOOT_SCREW_Z) for u in fh.STRUT_SCREW_U]
    if opt == "current":
        sad = saddle_current(); ft = foot_current(); st = fh.strut()
        g = box(U_BACK0, 0, UP + fh.SADDLE_U_PLUS, fh.SADDLE_N).difference(Point(UP, PO).buffer(R_RUB, 128))
        band = band_for(g, *fh.BAND_Z); zs = fh.CLAMP_Z[0]; zf = (fh.FOOT_Z[0], fh.FOOT_Z[1])
        note = "fairsolid rev 7 / repo: saddle 26 tall + 7.3 lip / 8.7 floor foot"
    elif opt == "A":     # same shapes, shorter; screws flush under the band
        zs = (176.0, 192.0); bz = (177.65, 190.35); zsc = 184.0
        su = [64.22, 74.22]
        g = box(U_BACK0, 0, UP + fh.SADDLE_U_PLUS, TRIM_N)
        sad = saddle_from(saddle_trim(*zs), [(u, zsc) for u in su], fh.M4_TAP, 12.0)
        zf = (285.3, 297.3); fz = 293.8; fu = [64.22, 74.22]
        ft = foot_new(zf[0], zf[1], 3.5, [(-55, 34), (-12, 20), (192, 20)], [(u, fz) for u in fu])
        st = strut_variant([(u, zsc, "M4cs") for u in su], [(u, fz, "M4") for u in fu])
        band = band_for(g, *bz)
        note = "same shapes, shorter: saddle 16 tall, M4 flat-heads flush under the band; foot lip 5 / floor 7, through windows"
    elif opt == "B":     # crescent saddle + spider foot
        zs = (176.0, 191.0); bz = (177.15, 189.85); zsc = 183.5
        su = [64.22, 74.22]
        g = crescent_shp(su)
        sad = saddle_from(saddle_crescent(*zs, su), [(u, zsc) for u in su], fh.M4_TAP, 10.0)
        zf = (285.3, 297.3); fz = 293.8; fu = [64.22, 74.22]
        ft = foot_new(zf[0], zf[1], 3.5, SPIDER, [(u, fz) for u in fu])
        st = strut_variant([(u, zsc, "M4cs") for u in su], [(u, fz, "M4") for u in fu])
        band = band_for(g, *bz)
        note = "crescent saddle 15 tall hugging the pump + spider foot (ring, spokes, open floor)"
    elif opt == "C":     # strut untouched: keep the M5 saddle screws at z 196 and M4 foot screws at z 295
        zs = (178.0, 201.0); bz = (178.8, 191.5)
        su = list(fh.STRUT_SCREW_U)
        g = crescent_shp(su)
        sad = saddle_from(saddle_crescent(*zs, su), S5, fh.M5_TAP, 12.0)
        zf = (285.3, 299.0)
        ft = foot_new(zf[0], zf[1], 3.5, SPIDER_C, F4)
        st = fh.strut()
        band = band_for(g, *bz)
        note = "strut unchanged (stays E): crescent saddle 23 tall on the existing M5 holes, spider foot on the existing M4 holes"
    # fillets LAST: R1 on the saddle's top/bottom outer edges (band + rubber contact), foot lip top edge R0.8
    if opt != "current":
        sad = fillet_last(sad, [e for e in outer_top_bottom_edges(sad, *zs)
                                if e.geom_type != GeomType.CIRCLE or abs(e.radius - R_RUB) > 0.05], 1.0, f"{opt} saddle")
        ft = fillet_last(ft, [e for e in outer_top_bottom_edges(ft, zf[0], zf[0])], 0.8, f"{opt} foot lip top")
    return dict(saddle=sad, foot=ft, strut=st, band=band, zs=zs, zf=zf, note=note)

def solid_of(s):
    return Compound(children=list(s)) if isinstance(s, ShapeList) else s

def roundtrip(s, path):
    export_step(s, path)
    r = import_step(path)
    return dict(solids=len(r.solids()), valid=r.is_valid, vol_diff_pct=round(abs(r.volume - s.volume) / s.volume * 100, 4))
