"""ST185 fuel hanger, option B pump holder (Dan 2026-10-17, approved B9): builds the three machined holder parts and the assembly.

    FH-103 strut  Rev F  pump_holder.strut() (saddle + foot screw/key features), every convex edge broken 0.5 x 45 (chamfers last),
                          then the saddle key slot is filled (front face flat again; no new edges, so no new chamfers)
    FH-104 foot   Rev E  pump_holder.foot() with the lip cut back to two side arms, R0.8 top-edge fillets last
    FH-105 saddle Rev D  pump_holder.saddle() band-line variant, NO key tongue, plus the band tab that hangs down along the
                          strut +u side face and LOCATES the saddle there (zero-gap slip fit); R1 fillets last
    FH-101 flange Rev G  unchanged: fuel_hanger.flange()

Writes (all STEP gitignored per R67, plain names, no rev letters): fuel-hanger-strut.step, fuel-hanger-foot.step,
fuel-hanger-saddle.step, fuel-hanger-assembly.step (flange + strut + saddle + foot), ref_band_clamp_worm_drive.step (taut band
at the band centre), ref_screws_M4.step, and holder-report.json (masses, skipped fillets/chamfers, clearances, contacts, band path,
2 g hand check). Run with the repo's build123d venv:  python cad/fuel-hanger/build_holder.py
Ported from the 2026-10-17 scratch study (b3.py strut chamfers, pumpB.py foot B2, b9.py saddle tab); geometry identical.
"""
import os, sys, json, math
os.environ.setdefault("SADDLE", "band"); os.environ.setdefault("FOOT_LIP", "back")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pump_holder as pb
import pumpmount as pm
from build123d import *
from pumpmount import solid_of, roundtrip, un_plane

fh = pb.fh
OUT = HERE
D, N = fh.D, fh.N
NV = Vector(N[0], N[1], 0); DV = Vector(D[0], D[1], 0); ZV = Vector(0, 0, 1)
U1, ST, SZ = pb.U1, pb.ST, pb.SZ
CH = 0.5                       # strut edge break, uniform, every convex edge
def un(p): return ((p.X - fh.C[0]) * D[0] + (p.Y - fh.C[1]) * D[1], (p.X - fh.C[0]) * N[0] + (p.Y - fh.C[1]) * N[1], p.Z)
def r1(t): return tuple(round(v, 2) for v in t)
def vol(x): return x.volume if x is not None else 0.0
def where(e):
    u, n, z = un(e.position_at(0.5)); return f"u {u:.1f} n {n:.2f} z {z:.1f} (len {e.length:.1f})"
def P(*a): print("##", *a, flush=True)

def classify(part):
    faces = part.faces(); fe = [(f, f.edges()) for f in faces]
    out = {"convex": [], "concave": [], "tangent": [], "seam/other": []}
    for e in part.edges():
        fs = [f for f, es in fe if any(e.is_same(x) for x in es)]
        if len(fs) != 2: out["seam/other"].append(e); continue
        p = e.position_at(0.5)
        n1, n2 = fs[0].normal_at(p), fs[1].normal_at(p)
        if n1.get_angle(n2) < 3.0: out["tangent"].append(e); continue
        d = (n1 - n2).normalized() * 0.02
        o1, o2 = part.is_inside(p + d), part.is_inside(p - d)
        if not o1 and not o2: out["convex"].append(e)
        elif o1 and o2: out["concave"].append(e)
        else: out["seam/other"].append(e)
    return out

SKIP = {}
def chamfer_batches(part, edges, c, tag):
    """chamfer the whole set; on failure split in halves; single edges that fail are skipped + listed."""
    keys = [(e.position_at(0.5), e.length) for e in edges]; lost = []
    def find(cur, ks):
        es, miss = [], []; ce = cur.edges()
        for p, L in ks:
            v = Vertex(p.X, p.Y, p.Z)
            m = [x for x in ce if x.distance_to(v) < 2e-3 and x.length > 0.05]
            if m: es.append(min(m, key=lambda x: abs(x.length - L)))
            else: miss.append((p, L))
        return es, miss
    def go(cur, ks):
        es, miss = find(cur, ks); lost.extend(miss)
        if not es: return cur, []
        try:
            res = chamfer(es, c)
            if res.is_valid and len(res.solids()) == 1: return res, []
        except Exception:
            pass
        if len(ks) == 1: return cur, ks
        h = len(ks) // 2
        cur, f1 = go(cur, ks[:h]); cur, f2 = go(cur, ks[h:]); return cur, f1 + f2
    cur, failed = go(part, keys)
    for p, L in failed:
        u, n, z = un(p); SKIP.setdefault(tag, []).append(f"u {u:.1f} n {n:.2f} z {z:.1f} (len {L:.1f})")
    for p, L in lost:
        u, n, z = un(p); SKIP.setdefault(tag + " - edge consumed by a neighbouring chamfer", []).append(f"u {u:.1f} n {n:.2f} z {z:.1f} (len {L:.1f})")
    return cur

def find_e(cur, ks):
    out = []
    for c, L in ks:
        m = [x for x in cur.edges() if (x.center() - c).length < 0.02 and abs(x.length - L) < 0.02]
        if m: out.append(m[0])
    return out
def try_ok(part, ks, r):
    """run the fillet in a forked child first: OCC can segfault on a bad edge set, the child absorbs the crash"""
    pid = os.fork()
    if pid == 0:
        try:
            res = fillet(find_e(part, ks), r); os._exit(0 if (res.is_valid and len(res.solids()) == 1) else 1)
        except BaseException:
            os._exit(1)
    _, stt = os.waitpid(pid, 0)
    return os.WIFEXITED(stt) and os.WEXITSTATUS(stt) == 0
def safe_fillet(part, edges, r, tag, fallback=(0.5,)):
    ks = [(e.center(), e.length) for e in edges]
    def go(cur, ks, rr):
        if not find_e(cur, ks): return cur, []
        if try_ok(cur, ks, rr): return fillet(find_e(cur, ks), rr), []
        if len(ks) == 1: return cur, ks
        h = len(ks) // 2
        cur, f1 = go(cur, ks[:h], rr); cur, f2 = go(cur, ks[h:], rr); return cur, f1 + f2
    cur, failed = go(part, ks, r)
    for rr in fallback:
        if not failed: break
        cur, f2 = go(cur, failed, rr)
        if len(failed) - len(f2): SKIP.setdefault(tag + " (info)", []).append(f"{len(failed) - len(f2)} edge(s) took R{rr} instead of R{r}")
        failed = f2
    for c, L in failed:
        u, n, z = un(c); SKIP.setdefault(tag, []).append(f"u {u:.1f} n {n:.2f} z {z:.1f} (len {L:.1f})")
    return cur

rep = {"build": "build_holder.py (option B, approved B9 2026-10-17)", "parts": {}}

# ================= FH-104 foot Rev E (two side arms), fillets last =================
P("foot")
pm.SKIPPED.clear(); pb.SKIP.clear()
ft = pb.foot()
r_out = fh.FOOT_POCKET_D / 2 + 3.5
def n_of(e): return pb.n_of(e)
def r_of(e):
    c = e.center(); u = (c.X - fh.C[0]) * fh.D[0] + (c.Y - fh.C[1]) * fh.D[1]; return math.hypot(u - pb.UP, n_of(e) - pb.PO)
fe = [e for e in pm.outer_top_bottom_edges(ft, pb.FOOT_Z[0], pb.FOOT_Z[0]) if n_of(e) > 0.3]
fe += [e for e in pm.outer_top_bottom_edges(ft, pb.SEAT, pb.SEAT) if n_of(e) > 0.3 and n_of(e) < pb.N_CUT - 0.1
       and r_of(e) > r_out - 4.0 and abs(e.center().Z - pb.SEAT) < 0.01]
ft = solid_of(pb.fillet_batches(ft, fe, 0.8, "foot top edges R0.8", fallback=(0.5, 0.3)))
SKIP.update(pb.SKIP); SKIP.update(pm.SKIPPED)

# ================= FH-103 strut Rev F =================
P("strut")
st0 = solid_of(pb.strut())
cls = classify(st0)
st3 = solid_of(chamfer_batches(st0, cls["convex"], CH, f"strut chamfer {CH} x 45"))
SLOT_Z = (pb.ZC - (pb.SZ[1] - 0.5 - pb.SLOT_W / 2 - pb.ZC) - pb.SLOT_W / 2, pb.SZ[1] - 0.5)
OV = 0.8                       # fill oversize all round: covers the slot + its 0.5 rim chamfer, stays in solid plate
with BuildPart() as fp:
    with BuildSketch(fh.strut_plane(0)):
        SlotCenterPoint((pb.KEY_U, pb.ZC), (pb.KEY_U, pb.SZ[1] - 0.5 - pb.SLOT_W / 2), pb.SLOT_W + 2 * OV)
    extrude(amount=pb.SLOT_D + 0.1)
fill = fp.part
fill_zone = fh.block(pb.KEY_U - 4, pb.KEY_U + 4, -ST - 1, 1, SLOT_Z[0] - 2, SLOT_Z[1] + 2)
st = solid_of((st3 + fill).clean())
cls_st = classify(st)
inzone = lambda q: abs(q[0] - pb.KEY_U) < 4 and abs(q[1]) < 3 and SLOT_Z[0] - 2 < q[2] < SLOT_Z[1] + 2
rep["strut"] = dict(chamfer=f"{CH} x 45 deg on every convex edge", convex_edges=len(cls["convex"]),
                    concave_edges_not_chamfered=len(cls["concave"]), saddle_key_slot="filled (unused since FH-105 D)",
                    slot_volume_filled_mm3=round(vol(st) - vol(st3), 1),
                    new_edges_in_filled_slot_zone=[where(e) for e in cls_st["convex"] + cls_st["concave"] if inzone(un(e.center()))],
                    foot_key_slot_distance_to_fill_mm=round(ft.distance_to(fill_zone), 2))

# ================= FH-105 saddle Rev D: no key tongue, locating band tab, fillets last =================
P("saddle")
tf, _ = pb.tangent_pt(pb.BC_, pb.R_OUT - pb.CH_D, +1)
ddx, ddy = tf[0] - pb.BC_[0], tf[1] - pb.BC_[1]
def L_at(n): return (pb.BC_[0] + ddx * (n - pb.BC_[1]) / ddy, n)
s_ = math.atan2(ddy, ddx)
G = 0.0                        # zero-gap locating contact on the strut +u side face (slip fit, toleranced on the drawings)
R_T = 1.0                      # bullnose radius, tangent to the band line and to the tab inner face
Ui = U1 + G
nin = (-math.sin(s_), math.cos(s_)); nout = (-nin[0], -nin[1])
apex_n = pb.BC_[1] + (Ui - pb.BC_[0]) * math.tan(s_)
CU = Ui + R_T; CN = pb.BC_[1] + (R_T - (CU - pb.BC_[0]) * nin[0]) / nin[1]
T1 = (Ui, CN); T2 = (CU + R_T * nout[0], CN + R_T * nout[1])
am = math.hypot(Ui - CU, apex_n - CN); MID = (CU + R_T * (Ui - CU) / am, CN + R_T * (apex_n - CN) / am)
P0 = (Ui, 0.4); P3 = L_at(0.4)
with BuildPart() as tp:
    with BuildSketch(un_plane(SZ[0])):
        with BuildLine():
            Line(P0, T1); ThreePointArc(T1, MID, T2); Line(T2, P3); Line(P3, P0)
        make_face()
    extrude(amount=SZ[1] - SZ[0])
tab = solid_of(tp.part)
sad_raw, bad = pb.saddle()
sad_raw = solid_of(sad_raw - fh.block(pb.KEY_U - 4, pb.KEY_U + 4, -4, 0.0, SZ[0] - 1, SZ[1] + 1))   # key tongue removed
sad_t = solid_of(sad_raw + tab).clean()
pm.SKIPPED.clear(); pb.SKIP.clear()
def is_tab_edge(e):
    u, n, z = un(e.center()); return u > Ui - 0.05 and n < -0.05 and (abs(z - SZ[0]) < 0.01 or abs(z - SZ[1]) < 0.01)
tab_e = [e for e in classify(sad_t)["convex"] if is_tab_edge(e)]
sad_a = solid_of(safe_fillet(sad_t, tab_e, 1.0, "saddle tab top/bottom R1"))      # tab edges first, then the saddle R1 set
sad = solid_of(pb.fillet_last(sad_a, pb.edges_off_back(sad_a, *SZ), 1.0, "saddle top/bottom R1"))
SKIP.update(pm.SKIPPED)
if bad: SKIP["saddle 2D corner rounds (sketch)"] = [f"{bad} sketch corner(s) not rounded"]
rep["tab"] = dict(z=SZ, width_z_mm=SZ[1] - SZ[0], gap_to_strut_side_mm=G, inner_face_u=round(Ui, 2),
                  band_line_angle_from_u_deg=round(math.degrees(s_), 1), bullnose_r=R_T, tangent_on_inner_face_uv=r1(T1),
                  tangent_on_band_line_uv=r1(T2), flat_bearing_mm2_approx=round((-T1[1] - 0.5) * (SZ[1] - SZ[0] - 2), 1),
                  tab_edges_filleted_R1=len(tab_e))

# ================= export =================
P("export")
for k, pn, rv, s in (("strut", "FH-103", "F", st), ("foot", "FH-104", "E", ft), ("saddle", "FH-105", "D", sad)):
    fn = f"fuel-hanger-{k}.step"; bb = s.bounding_box()
    rep["parts"][k] = dict(pn=pn, rev=rv, file=fn, mass_g=round(s.volume * pb.RHO, 1), volume_mm3=round(s.volume, 2), valid=s.is_valid,
                           solids=len(s.solids()), bbox=[round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)],
                           step=roundtrip(s, os.path.join(OUT, fn)))
rep["skipped_fillets_and_chamfers"] = SKIP
sc = pb.screws()
export_step(Compound(children=sc), os.path.join(OUT, "ref_screws_M4.step"))
flange = fh.flange(); pump = fh.pump(); keep = fh.keepouts(); valve = fh.check_valve_envelope()
export_step(Compound(children=[flange, st, sad, ft]), os.path.join(OUT, "fuel-hanger-assembly.step"))

# ================= checks =================
P("checks")
EPS = 0.02
def contact(a, b, vec):
    v0 = vol(a & b) if a.distance_to(b) < 1e-6 else 0.0
    v1 = vol(a & (Pos(vec.X * EPS, vec.Y * EPS, 0) * b)); return round((v1 - v0) / EPS, 1)
tabpart = sad & fh.block(U1 + 0.01, U1 + 10, -ST - 1, -0.01, SZ[0] - 1, SZ[1] + 1)
rep["contact_mm2"] = {"saddle on strut front face": contact(st, sad, -NV), "foot on strut front face": contact(st, ft, -NV),
                      "flange on strut back face": contact(st, flange, NV), "tab gap to strut +u side face (mm)": round(tabpart.distance_to(st), 3)}
rep["saddle_install_slide_on_along_minus_n_overlap_mm3_at_lift_mm"] = {str(t): round(vol(st & (Pos(NV.X * t, NV.Y * t, 0) * sad)), 3) for t in (0.02, 0.5, 1.0, 2.0, 5.0, 10.0)}
def section_pts(shape, z, step=0.05):
    sec = shape & (Plane.XY.offset(z) * Rectangle(2000, 2000)); pts = []
    for e in sec.edges():
        n = max(2, int(e.length / step))
        for i in range(n + 1):
            u, nn, _ = un(e.position_at(i / n)); pts.append((u, nn))
    return pts
def hull(Pp):
    Pp = sorted(set((round(a, 5), round(b, 5)) for a, b in Pp))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in Pp:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 1e-9: lo.pop()
        lo.append(p)
    for p in reversed(Pp):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 1e-9: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
a = pb.BC_; b = L_at(0.0); smp = []
for k in range(121):
    q = (a[0] + (b[0] - a[0]) * k / 120, a[1] + (b[1] - a[1]) * k / 120); g_ = None
    for i in range(300):
        t = i * 0.01; w = fh.W(q[0] + nin[0] * t, q[1] + nin[1] * t, pb.ZC)
        if st.is_inside(w) or sad.is_inside(w): g_ = round(t, 2); break
    smp.append((r1(q), g_))
first_tab = next((p for p, g_ in smp[3:] if g_ is not None and g_ <= 0.03), None)
rep["band_on_tab"] = dict(band_leaves_strut_at_uv=r1(a), first_tab_contact_uv=first_tab,
                          free_span_mm=round(math.hypot(first_tab[0] - a[0], first_tab[1] - a[1]), 2) if first_tab else None,
                          max_gap_band_to_surface_mm=max((g_ for _, g_ in smp if g_ is not None), default=None))
pump_pts = [(pb.UP + pb.R_RUB * math.cos(t), pb.PO + pb.R_RUB * math.sin(t)) for t in [i * math.pi / 180 for i in range(360)]]
Hb = hull(section_pts(st, pb.ZC) + section_pts(sad, pb.ZC) + pump_pts)
Hb2 = [Hb[0]] + [p for i, p in enumerate(Hb[1:], 1) if math.hypot(p[0] - Hb[i - 1][0], p[1] - Hb[i - 1][1]) > 0.04]
with BuildPart() as bp:
    with BuildSketch(un_plane(pb.BZ[0])):
        Polygon(*Hb2, align=None); offset(amount=pb.BAND_T, kind=Kind.INTERSECTION); Polygon(*Hb2, align=None, mode=Mode.SUBTRACT)
    extrude(amount=pb.BAND_W)
    wu, wn, wz = fh.WORM
    add(fh.block(pb.UL - wu / 2, pb.UL + wu / 2, -pb.ST - pb.BAND_T - wn, -pb.ST - pb.BAND_T, pb.ZC - wz / 2, pb.ZC + wz / 2))
band = bp.part
export_step(band, os.path.join(OUT, "ref_band_clamp_worm_drive.step"))
allp = {"flange": flange, "strut": st, "saddle": sad, "foot": ft, "pump": pump, "valve": valve, "keepouts": keep, "band(taut)": band, "screws": Compound(children=sc)}
clear = {}; nm = list(allp)
for i, a_ in enumerate(nm):
    for c in nm[i + 1:]:
        if {a_, c} & {"strut", "band(taut)", "saddle", "foot"} == set(): continue
        dd = allp[a_].distance_to(allp[c]); ov = vol(allp[a_] & allp[c]) if dd < 1e-6 else 0.0
        if dd < 3.0: clear[f"{a_}|{c}"] = dict(min_gap_mm=round(dd, 2), overlap_mm3=round(ov, 3))
rep["clearance_under_3mm"] = clear
hc = json.load(open(os.path.join(HERE, "holder-handcheck.json")))
A_ = hc["assumptions"]; J = hc["joints"]["saddle FH-105 / strut"]
Fz = A_["load_N"]; Pre = A_["preload_N"]; mu = A_["mu"]
rep["saddle_location_2g"] = dict(pump_mass_kg=A_.get("pump_mass_kg"), load_N=Fz, friction_capacity_N=round(2 * Pre * mu, 0),
                                 SF_slip_z=round(2 * Pre * mu / Fz, 1), SF_spin=J["SF_friction"],
                                 if_friction_lost_screw_shear_MPa=round(Fz / 2 / (math.pi / 4 * 3.141 ** 2), 2),
                                 note="no key: u by the tab on the strut +u side face, z by 2 x M4 preload (torque + threadlocker on the drawing)")
rep["holder_mass_g"] = round(rep["parts"]["saddle"]["mass_g"] + rep["parts"]["foot"]["mass_g"], 1)
json.dump(rep, open(os.path.join(OUT, "holder-report.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
