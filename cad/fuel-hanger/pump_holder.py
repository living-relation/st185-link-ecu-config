"""ST185 fuel hanger - option B geometry (Dan 2026-10-17). Library for build_holder.py, which builds the released parts
(saddle without key tongue + locating tab, filled strut saddle slot, chamfers/fillets last). Original study notes:
ST185 fuel hanger - option B final (Dan 2026-10-17): crescent saddle FH-105 D + spoked foot FH-104 E + strut FH-103 F.
build123d, 6061-T6.  Built FROM THE ASSEMBLY: frame u = along the strut face, n = toward the pump (strut front face n = 0,
back face n = -STRUT_T), z = into the tank (installed: flange on top, z grows downward).
Changes vs the 10-17 study option B (out/B0):
  * saddle: fills the strut face from edge to edge (flat back = mating face u 56.8..92.2), outline is the band's own
    path (strut back corners -> tangent lines -> R24.75 arc), so the band lies on it with no gaps; a 13.2 x 1.0 band
    channel follows that path (band 12.7 = fuel_hanger.BAND_W, SAE #24 worm-drive, + 0.5).  Saddle 17 tall (was 15)
    so the channel keeps 1.9 mm lips.  The study saddle's 2nd M4 tap (u 74.22) broke into the pump bore -> only one
    hole looked real.  Now 2 M4 flat-heads spread diagonally on the deep -u side + a 4 mm key tongue at u 86 that
    sits in a 2 mm deep slot in the strut: 3 points, cannot turn.
  * foot: M4 taps stay in its flat back face (n = 0, against the strut) but spread to u 63.5 / 76.2 (12.7 apart, was 10)
    + the same 4 mm key tongue at u 86, its strut slot runs out of the strut's bottom end.
  * strut: holes moved to match, 2 key slots added.  Flange G untouched.
All outlines are true lines/arcs (BuildSketch circles, rectangles, fillets); no shapely, no polygons -> no facets.
Fillets LAST, after every cut; failures skipped and listed."""
import json, math, os, sys
MY = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, MY)
import fuel_hanger as fh
from build123d import *
import pumpmount as pm
from pumpmount import un_plane, rect_un, circ_un, sk_round, foot_new, fillet_last, outer_top_bottom_edges, roundtrip, solid_of, cs_hole_from_back

OUT = MY
RHO = 2.70e-3
UP, PO, UL, ST = fh.UP, fh.PUMP_OFF, fh.U_STRUT_LOW, fh.STRUT_T
R_RUB = fh.CLAMP_BORE / 2            # 20.75 pump + rubber
WALL = 4.0; R_OUT = R_RUB + WALL     # crescent outer 24.75
CH_D = 1.0                           # channel depth
BAND_W, BAND_T = fh.BAND_W, fh.BAND_T
CH_W = BAND_W + 0.5                  # 13.2
ZC = 183.5                           # band centre (study B)
SZ = (ZC - 8.5, ZC + 8.5)            # saddle 175.0 .. 192.0 (17 tall)
CHZ = (ZC - CH_W / 2, ZC + CH_W / 2) # 176.9 .. 190.1
BZ = (ZC - BAND_W / 2, ZC + BAND_W / 2)
U0, U1 = UL - fh.STRUT_W / 2, UL + fh.STRUT_W / 2   # strut lower arm edges 56.22 .. 92.22
A_ = (U0, -ST); B_ = (U1, -ST)                      # strut back corners (band wraps them)
F_ = (U0, 0.0)                                      # strut front corner on the -u side (band wraps it too)
F2_ = (U1, 0.0)                                     # strut front corner on the +u side
STRUT_CH = 0.5                                      # B3: strut edges 0.5 x 45 chamfer
BC_ = (U1, -ST + STRUT_CH)                          # B4: where the taut band leaves the chamfered back +u strut edge
SADDLE = os.environ.get("SADDLE", "band")           # overhang = B1 (3.3 mm past the strut edge); flush = B2 (Dan 10-17)
def _b_side(r):
    """+u side of the band/saddle outline: (polygon points from the strut back corner, tangent point on circle r)"""
    if SADDLE == "flush":
        t, _ = tangent_pt(F2_, r, +1); return [B_, F2_, t], t
    if SADDLE == "band":
        # B4 (Dan 10-17): flat side out to the taut band line. Band leaves the strut's chamfered back +u edge at BC_ and runs
        # straight to the channel floor (r R_OUT-CH_D). Channel floor = that line; outer face = the line offset by CH_D
        # (constant 1.0 deep channel all the way to the strut face plane n = 0).
        rf = R_OUT - CH_D
        tf, _ = tangent_pt(BC_, rf, +1)
        dx, dy = tf[0] - BC_[0], tf[1] - BC_[1]; L = math.hypot(dx, dy); nx, ny = dy / L, -dx / L
        off = r - rf
        p0 = (BC_[0] + off * nx, BC_[1] + off * ny); pt = (tf[0] + off * nx, tf[1] + off * ny)
        return ([B_, p0, pt] if off > 1e-9 else [B_, BC_, tf]), pt
    t, _ = tangent_pt(B_, r, +1); return [B_, t], t
SAD_SCREWS = [(63.5, ZC + 5.0), (70.0, ZC - 5.0)]   # (u, z) M4 flat heads from the strut back
SAD_TAP = 8.0
KEY_U, KEY_W, KEY_H, SLOT_W, SLOT_D = 86.0, 3.95, 1.9, 4.0, 2.0
FOOT_Z = (285.3, 297.3); FOOT_SZ = 293.8
FOOT_SCREWS = [(63.5, FOOT_SZ), (76.2, FOOT_SZ)]
SKIP = {}

def tangent_pt(p, r, side):
    """tangent point on circle (UP, PO, r) from point p; side +1 = right (ccw from point), -1 = left"""
    dx, dy = p[0] - UP, p[1] - PO; d = math.hypot(dx, dy)
    phi = math.atan2(dy, dx); a = math.acos(r / d)
    t = phi + side * a
    return (UP + r * math.cos(t), PO + r * math.sin(t)), math.degrees(t)

def hull_region(sk_mode, r, z):
    """2D region: hull(strut back corners, circle r) drawn as circle + quad of tangent points (true arcs)"""
    bs, tb = _b_side(r)
    ta, _ = tangent_pt(F_, r, -1)
    circ_un(UP, PO, r, sk_mode)
    Polygon(A_, *bs, (UP, PO), ta, F_, align=None, mode=sk_mode)
    return ta, tb

def band_inner(sk_mode):
    """inside of the band: pump rubber r20.75 on the free side, channel floor r23.75 on the saddle, strut corners"""
    r = R_OUT - CH_D
    bs, tb = _b_side(r)
    tm = (UP - r, PO); tp = (UP + r, PO)
    a = math.acos(R_RUB / r)
    pp = (UP + R_RUB * math.cos(a), PO + R_RUB * math.sin(a)); pmn = (UP - R_RUB * math.cos(a), PO + R_RUB * math.sin(a))
    circ_un(UP, PO, R_RUB, sk_mode)
    with BuildSketch(mode=Mode.PRIVATE) as h:       # half disc r23.75 (strut side), local (u, n)
        circ_un(UP, PO, r); rect_un(UP - 40, PO, UP + 40, PO + 40, Mode.SUBTRACT)
    add(h.sketch, mode=sk_mode)
    Polygon(A_, *bs, (UP, PO), tm, F_, align=None, mode=sk_mode)
    Polygon((UP, PO), tp, pp, align=None, mode=sk_mode)
    Polygon((UP, PO), pmn, tm, align=None, mode=sk_mode)

def saddle():
    z0, z1 = SZ
    with BuildPart() as p:
        with BuildSketch(un_plane(z0)) as sk:
            hull_region(Mode.ADD, R_OUT, z0)
            rect_un(UP - 60, PO, UP + 60, PO + 60, Mode.SUBTRACT)     # strut-side half only
            rect_un(UP - 60, -20, UP + 60, 0, Mode.SUBTRACT)          # nothing behind the strut face
            circ_un(UP, PO, R_RUB, Mode.SUBTRACT)
            if SADDLE == "band":
                # the acute overhang tip on n = 0 (outer line meets the back face) gets R0.5 only, so the channel lip
                # survives right to the strut face plane; every other corner R1.5 as before
                _, pt = _b_side(R_OUT)
                tip = lambda v: abs(v.Y) < 1e-3 and v.X > U1 + 0.5      # local sketch coords: X = u, Y = n
                vs = sk.vertices()
                bad = 0
                for vv, rr in [(x, 1.5) for x in vs if not tip(x)] + [(x, 0.5) for x in vs if tip(x)]:
                    try:
                        fillet(sk.vertices().filter_by(lambda q: (Vector(q) - Vector(vv)).length < 1e-3), rr)
                    except Exception:
                        bad += 1
            else:
                bad = sk_round(sk, 1.5)
        extrude(amount=z1 - z0)
        # key tongue on the flat back (n 0 -> -1.9), full-round ends
        with BuildSketch(fh.strut_plane(0)):
            SlotCenterPoint((KEY_U, (z0 + z1) / 2), (KEY_U, z1 - 0.6 - KEY_W / 2), KEY_W)
        extrude(amount=KEY_H)
    part = p.part
    # band channel: everything outside the band's inner surface, over the channel height
    with BuildPart() as c:
        with BuildSketch(un_plane(CHZ[0])):
            rect_un(UP - 70, -1, UP + 70, PO + 1)
            band_inner(Mode.SUBTRACT)
        extrude(amount=CH_W)
    part = part - c.part
    for u, z in SAD_SCREWS:
        part = pm.hole_n(part, u, z, 0, SAD_TAP, fh.M4_TAP)
    return part, bad

LIP = os.environ.get("FOOT_LIP", "back")    # full = B1 (lip all round); back = B2 (Dan 10-17: back lip removed); none = no lip at all
N_CUT = 12.0                                # B2: no lip material closer than 12 mm to the strut face
SEAT = fh.PUMP_BOTTOM_Z                     # 290.3: pump bottom seats here (unchanged)

def foot_v2(z_lip0, z_bot, wall, windows, screws, lip="back", tap_depth=10.0):
    """foot_new (study B) with the lip cut back: floor (seat..z_bot) unchanged; lip ring only where n >= N_CUT
    (two side arms that wrap 33 deg past the pump centreline toward the strut), or no lip. True arcs only."""
    r_out = fh.FOOT_POCKET_D / 2 + wall
    hw = fh.FOOT_HOLE_D / 2
    back_u1 = UP + 8
    with BuildPart() as p:
        with BuildSketch(un_plane(SEAT)) as sk:          # floor (same as study B / B1)
            circ_un(UP, PO, r_out)
            rect_un(pm.U_BACK0 + 2, 0, back_u1, PO)
            rect_un(UP - 60, -10, UP + 60, 0, Mode.SUBTRACT)
            rect_un(UP - hw, PO, UP + hw, PO + 40, Mode.SUBTRACT)
            circ_un(UP, PO, hw, Mode.SUBTRACT)
            sk_round(sk, 2.0)
        extrude(amount=z_bot - SEAT)
        if lip != "none":
            with BuildSketch(un_plane(z_lip0)) as sk2:   # lip, strut side removed
                circ_un(UP, PO, r_out)
                rect_un(UP - hw, PO, UP + hw, PO + 40, Mode.SUBTRACT)
                circ_un(UP, PO, fh.FOOT_POCKET_D / 2, Mode.SUBTRACT)
                rect_un(UP - 60, -10, UP + 60, N_CUT if lip == "back" else 0, Mode.SUBTRACT)
                sk_round(sk2, 1.5)
            extrude(amount=SEAT - z_lip0)
    part = p.part
    ri, ro = hw + 2.5, fh.FOOT_POCKET_D / 2 - 0.5
    for mid, span in windows:
        with BuildPart() as w:
            with BuildSketch(un_plane(SEAT - 1)) as sk3:
                circ_un(UP, PO, ro)
                circ_un(UP, PO, ri, Mode.SUBTRACT)
                a0, a1 = math.radians(mid - span / 2), math.radians(mid + span / 2)
                ptsw = [(UP, PO)] + [(UP + 45 * math.cos(a0 + (a1 - a0) * k / 6), PO + 45 * math.sin(a0 + (a1 - a0) * k / 6)) for k in range(7)]
                Polygon(*ptsw, align=None, mode=Mode.INTERSECT)      # straight radial window sides; the arcs come from the circles
                rect_un(UP - 60, -10, UP + 60, 5.0, Mode.SUBTRACT)
                sk_round(sk3, min(2.0, (ro - ri) / 2 - 0.05))
            extrude(amount=z_bot - SEAT + 2)
        part = part - w.part
    for u, z in screws:
        part = pm.hole_n(part, u, z, 0, tap_depth, fh.M4_TAP)
    return part

def foot_z0():
    return FOOT_Z[0] if LIP != "none" else SEAT

def foot():
    if LIP == "full":
        ft = foot_new(FOOT_Z[0], FOOT_Z[1], 3.5, pm.SPIDER, FOOT_SCREWS)
        zt = FOOT_Z[0] + 1.7 + KEY_W / 2
    else:
        ft = foot_v2(FOOT_Z[0], FOOT_Z[1], 3.5, pm.SPIDER, FOOT_SCREWS, LIP)
        zt = SEAT + 0.5 + KEY_W / 2                  # back face is now floor-height only (7 mm): tongue 290.8 .. 297.3
    # key tongue: u 86, down to the foot bottom (runs out flush), round top end
    with BuildPart() as k:
        with BuildSketch(fh.strut_plane(0)):
            with Locations((KEY_U, (zt + FOOT_Z[1]) / 2)):
                Rectangle(KEY_W, FOOT_Z[1] - zt)
            with Locations((KEY_U, zt)):
                Circle(KEY_W / 2)
        extrude(amount=KEY_H)
    return ft + k.part

def strut():
    st = pm.strut_variant([(u, z, "M4cs") for u, z in SAD_SCREWS], [(u, z, "M4") for u, z in FOOT_SCREWS])
    with BuildPart() as s:
        with BuildSketch(fh.strut_plane(0)):          # saddle key slot (closed, R2 ends = 4 mm end mill)
            SlotCenterPoint((KEY_U, ZC), (KEY_U, SZ[1] - 0.5 - SLOT_W / 2), SLOT_W)
        extrude(amount=SLOT_D)
        zt = (FOOT_Z[0] + 1.6 if LIP == "full" else SEAT + 0.4) + SLOT_W / 2
        with BuildSketch(fh.strut_plane(0)):          # foot key slot, open out of the strut bottom
            with Locations((KEY_U, (zt + 301) / 2)):
                Rectangle(SLOT_W, 301 - zt)
            with Locations((KEY_U, zt)):
                Circle(SLOT_W / 2)
        extrude(amount=SLOT_D)
    return st - s.part

def band():
    with BuildPart() as b:
        with BuildSketch(un_plane(BZ[0])) as sk:
            band_inner(Mode.ADD)
            offset(amount=BAND_T, kind=Kind.INTERSECTION)
            band_inner(Mode.SUBTRACT)
        extrude(amount=BAND_W)
        wu, wn, wz = fh.WORM
        add(fh.block(UL - wu / 2, UL + wu / 2, -ST - BAND_T - wn, -ST - BAND_T, ZC - wz / 2, ZC + wz / 2))
    return b.part

def screws():
    """saddle: M4 x 12 flat head (ISO 10642, flush in the strut back); foot: M4 x 14 socket head (ISO 4762). Pictures/clearance only"""
    out = []
    for (u, z), L in [(s, 12.0) for s in SAD_SCREWS] + [(s, 14.0) for s in FOOT_SCREWS]:
        pl = Plane(origin=fh.W(u, -ST, z), z_dir=(fh.N[0], fh.N[1], 0))
        is_cs = (u, z) in SAD_SCREWS
        hd = pl * Cone(4.0, 2.0, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)) if is_cs else \
            Plane(origin=fh.W(u, -ST - 2.8, z), z_dir=(fh.N[0], fh.N[1], 0)) * Cylinder(3.5, 2.8, align=(Align.CENTER, Align.CENTER, Align.MIN))
        sh = pl * Cylinder(1.95, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
        out.append(hd + sh)
    return out

def fillet_batches(part, edges, r, tag, fallback=(0.5,)):
    """fillets LAST, in batches: try the whole set; if it fails split it in halves; a single edge that still fails at r
    and at each fallback radius is skipped and listed in SKIP[tag]. Edges are re-found on the current solid each time."""
    keys = [(e.center(), e.length) for e in edges]
    def find(cur, ks):
        out = []
        for c, L in ks:
            m = [x for x in cur.edges() if (x.center() - c).length < 0.02 and abs(x.length - L) < 0.02]
            if m: out.append(m[0])
        return out
    def go(cur, ks, rr):
        es = find(cur, ks)
        if not es: return cur, []
        try:
            res = fillet(es, rr)
            if res.is_valid: return res, []
        except Exception:
            pass
        if len(ks) == 1: return cur, ks
        h = len(ks) // 2
        cur, f1 = go(cur, ks[:h], rr); cur, f2 = go(cur, ks[h:], rr)
        return cur, f1 + f2
    cur, failed = go(part, keys, r)
    for rr in fallback:
        if not failed: break
        cur, failed2 = go(cur, failed, rr)
        done = len(failed) - len(failed2)
        if done: SKIP.setdefault(tag + " (info)", []).append(f"{done} edge(s) took R{rr} instead of R{r}")
        failed = failed2
    for c, L in failed:
        SKIP.setdefault(tag, []).append(f"skipped edge at {tuple(round(v, 1) for v in c)} (len {L:.1f})")
    return cur

def n_of(e):
    c = e.center(); return (c.X - fh.C[0]) * fh.N[0] + (c.Y - fh.C[1]) * fh.N[1]

def edges_off_back(part, z0, z1):
    """outer top/bottom edges, not the bore (rubber) edges and not the flat back (it sits on the strut)"""
    return [e for e in outer_top_bottom_edges(part, z0, z1)
            if (e.geom_type != GeomType.CIRCLE or abs(e.radius - R_RUB) > 0.05) and n_of(e) > 0.3]
