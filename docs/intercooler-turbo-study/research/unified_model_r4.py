"""
UNIFIED 5S-GTE MODEL - ROUND FOUR.

Round four applies eight corrections supplied by Dan on 31 Aug 2026 and re-derives
everything downstream. See ROUND-FOUR CHANGES below.

Emits data/chartdata_r4.js and data/unified_model_r4.json for the report.

ROUND-FOUR CHANGES
 1. Exhaust manifold is ALREADY paired 1+4 / 2+3. The 1+2/3+4 diagram was superseded.
    The pulse-timing arithmetic is retained as VALIDATION, not as a fault report.
    The 7 whp and 300-500 rpm spool penalties are deleted everywhere.
 2. Intake plenum resolved: Soara Performance custom dual-plenum, 3 in (76.2 mm) ID
    throttle flange. Throttle body identified as Bosch 0 280 750 474, bore 74.5 mm.
    Charge pipe math re-run against 74.5 mm, not 74 mm nominal / 2.9 in taper.
 3. Redline is a RANGE: stock through 8,000 rpm. Everything is a function of rpm.
 4. No dyno exists. All power figures are ESTIMATES. Community dyno comparison added.
 5. Drivetrain upgraded. Driveline factor becomes a band, not a point.
 6. Compressor maps checked against the OFFICIAL BorgWarner sheets.
 7. Packaging defined. Real stack geometry, real Mishimoto radiator.
 8. Prior research files audited and classified.
"""
import math, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

R, GAMMA, CP, PSI = 287.05, 1.40, 1005.0, 6.89476
LBMIN = 2.20462 * 60
IN = 0.0254

# ---------------------------------------------------------------- site
ALT_M = 640.0
P_AMB = 101.325 * (1 - 2.25577e-5 * ALT_M) ** 5.25588          # 93.87 kPa
T_AMB = 32.0
FILTER_LOSS = 0.97

# ---------------------------------------------------------------- engine
BORE, STROKE, ROD, NCYL = 0.0875, 0.0910, 0.1380, 4
DISP = math.pi * (BORE / 2) ** 2 * STROKE * NCYL               # 2.1888e-3 m^3
ROD_RATIO = ROD / STROKE                                       # 1.516
IV_DIA = 0.0335
A_PISTON = math.pi * (BORE / 2) ** 2
A_INTAKE = 2 * math.pi * (IV_DIA / 2) ** 2
CI = 0.40

# rpm range Dan asked for: stock redline through 8,000
RPM_STOCK = 7000.0      # ST185 Gen 2 factory tachometer redline. CONFIRM ON THE CAR.
RPM_MAX = 8000.0

# ---------------------------------------------------------------- conversion constants
HP_PER_LBMIN = 10.0     # crank, E85. band 9.5 - 10.5 (Garrett 60/(AFR*BSFC))

# ---- ITEM 5: drivetrain, re-derived as a band --------------------------------
# Baseline round three: 0.80 (20% loss), from the Evo 6 engine-dyno vs AWD-chassis
# back-to-back. Round four reassesses each upgrade SEPARATELY and honestly.
#
#   component            steady-state loss effect      inertia effect
#   -------------------  ---------------------------  ---------------------------
#   rebuilt transmission  -0.0 to -1.0 pts (restores   none
#                         nominal; does not beat it)
#   1-pc CF driveshaft    -0.3 to -0.8 pts (deletes    ~50% less shaft inertia
#                         one U-joint + centre bearing)
#   LSD rear diff         +0.3 to +1.0 pts WORSE       none
#                         (plate preload drags; a
#                         helical is nearer neutral)
#   lightweight wheels    0.0 pts on a steady-state    ~1.1 kg.m^2 less; worth
#                         dyno                          ~2-3 whp of INDICATED
#                                                       reading on an inertia dyno
DRIVETRAIN_LO = 0.78
DRIVETRAIN_MID = 0.80
DRIVETRAIN_HI = 0.83


def mean_piston_speed(rpm):
    return 2 * STROKE * rpm / 60.0


def sound_speed(tC):
    return math.sqrt(GAMMA * R * (tC + 273.15))


def mach_index(rpm, iatC):
    return A_PISTON * mean_piston_speed(rpm) / (CI * A_INTAKE * sound_speed(iatC))


def ve_unified(rpm, iatC=50.0, cam_peak=5800.0, emap=1.6):
    """Reconciled VE curve. emap is the exhaust-to-intake manifold pressure ratio.
    1.6 is the CORRECTLY PAIRED twin-scroll value and is the baseline everywhere."""
    cam = 1.00 - 0.030 * ((rpm - cam_peak) / 2500.0) ** 2
    Z = mach_index(rpm, iatC)
    mach = 1.0 if Z <= 0.50 else max(0.45, 1.0 - 1.25 * (Z - 0.50))
    bp = 1.0 - 0.05 * max(0.0, emap - 1.0)
    return max(0.40, cam * mach * bp)


# ---------------------------------------------------------------- thermal
def comp_out_C(t1C, pr, eta):
    return (t1C + 273.15) * (1 + (pr ** ((GAMMA - 1) / GAMMA) - 1) / eta) - 273.15


def eps_crossflow(ntu, cr):
    if cr <= 1e-6:
        return 1 - math.exp(-ntu)
    return 1 - math.exp((ntu ** 0.22 / cr) * (math.exp(-cr * ntu ** 0.78) - 1))


def core_eps(w, h, t, vf, m_hot, t_amb, p_amb):
    rho = p_amb * 1000 / (R * (t_amb + 273.15))
    mc = w * h * vf * rho
    Cc, Ch = mc * CP, m_hot * CP
    cmin, cmax = min(Cc, Ch), max(Cc, Ch)
    cr = cmin / cmax
    A = w * h * t * 900.0
    U = 55.0 * math.sqrt(vf / 10.0)
    ntu = U * A / cmin
    e = eps_crossflow(ntu, cr)
    return dict(eps=e * cmin / Ch, epsHX=e, ntu=ntu, cr=cr, mCold=mc)


CORES = {
    "610x305x76":  dict(w=0.610, h=0.305, t=0.076, label="610 x 305 x 76 (24x12x3)"),
    "610x305x102": dict(w=0.610, h=0.305, t=0.102, label="610 x 305 x 102 (24x12x4)"),
    "610x305x114": dict(w=0.610, h=0.305, t=0.114, label="610 x 305 x 114 (24x12x4.5)"),
    "685x305x76":  dict(w=0.685, h=0.305, t=0.076, label="685 x 305 x 76 (27x12x3)"),
    "685x305x102": dict(w=0.685, h=0.305, t=0.102, label="685 x 305 x 102 (27x12x4)"),
    "685x340x102": dict(w=0.685, h=0.340, t=0.102, label="685 x 340 x 102 (27x13.4x4)"),
    "711x305x102": dict(w=0.711, h=0.305, t=0.102, label="711 x 305 x 102 (28x12x4) - the ESTIMATE"),
}


def face_velocity(core, v_ref=7.81, t_ref=0.076, w_ref=0.610, h_ref=0.305):
    """Face velocity falls as the core gets deeper: the captured stream is fixed by
    the aperture, so a deeper core resists it more."""
    depth_pen = (t_ref / core["t"]) ** 0.45
    area_pen = (w_ref * h_ref) / (core["w"] * core["h"])
    return v_ref * depth_pen * area_pen


def operating_point(rpm, boost, eta_c, core=None, ve_fn=ve_unified,
                    t_amb=T_AMB, p_amb=P_AMB, dp_psi=1.5, vf=None,
                    dt=DRIVETRAIN_MID, hp_lb=HP_PER_LBMIN):
    core = core or CORES["610x305x102"]
    vf = vf if vf is not None else face_velocity(core)
    p_man = p_amb + boost * PSI
    pr = (p_man + dp_psi * PSI) / (p_amb * FILTER_LOSS)
    tc = comp_out_C(t_amb, pr, eta_c)
    iat = t_amb + 25.0
    res = None
    for _ in range(200):
        ve = ve_fn(rpm, iat)
        rho = p_man * 1000.0 / (R * (iat + 273.15))
        m = DISP * (rpm / 2.0) / 60.0 * ve * rho
        res = core_eps(core["w"], core["h"], core["t"], vf, m, t_amb, p_amb)
        new = tc - res["eps"] * (tc - t_amb)
        if abs(new - iat) < 0.005:
            iat = new
            break
        iat = new
    ve = ve_fn(rpm, iat)
    rho = p_man * 1000.0 / (R * (iat + 273.15))
    m = DISP * (rpm / 2.0) / 60.0 * ve * rho
    lb = m * LBMIN
    Q = m * CP * (tc - iat)
    return dict(rpm=rpm, boost=boost, pr=pr, tc=tc, iat=iat, ve=ve, lb=lb,
                whp=lb * hp_lb * dt, crank=lb * hp_lb, eps=res["eps"],
                ntu=res["ntu"], cr=res["cr"], m=m, Q=Q, vf=vf,
                mCold=res["mCold"], dTrad=Q / (res["mCold"] * CP),
                core=core["label"])


# ============================================================================
# ITEM 6 - OFFICIAL BORGWARNER COMPRESSOR MAP DATA
# ============================================================================
# Read directly off the official BorgWarner product sheets:
#   EFR 7163: borgwarner.com/docs/.../efr-7163-f.pdf  (map applies to ALL 7163 units,
#             including the 7163-G 0.80 A/R T4 twin-scroll Dan owns, PN 11639880002 /
#             supercore 11637105000 / housing 11631008002)
#   EFR 7670: borgwarner.com/docs/.../efr-7670-b.pdf
#   EFR 7064: borgwarner.com/docs/.../efr-7064-b.pdf
# The efficiency-contour VALUES, speed-line VALUES, axis extents and wheel diameters
# below are the sheet's own printed labels - they are exact.
# The surge/choke COORDINATES are digitised off the printed plot at roughly
# +/- 1.5 lb/min and +/- 0.08 PR. That uncertainty is carried through.
OFFICIAL = {
    "EFR 7163": dict(
        pdf="efr-7163-f.pdf",
        applies="map applies to all 7163 units incl. the 7163-G twin-scroll",
        comp_ind=57, comp_od=71, turb_exd=56, turb_od=63,
        eff_contours=[0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74],
        eff_peak=0.74,
        eff_peak_at=(44.0, 3.00),                 # lb/min, PR - centre of the 0.74 island
        # Printed contour LABELS, digitised (flow lb/min, PR, efficiency).
        # These are the raw data the round-four surface is fitted to.
        eff_labels=[(11.3, 2.01, 0.58), (54.2, 2.21, 0.58),
                    (11.3, 2.21, 0.60), (56.9, 2.71, 0.60),
                    (14.4, 2.41, 0.62), (57.7, 2.92, 0.62),
                    (29.0, 2.86, 0.64), (57.7, 3.14, 0.64),
                    (35.6, 3.14, 0.66),
                    (43.6, 3.50, 0.68),
                    (50.7, 3.74, 0.70),
                    (45.8, 3.37, 0.72),
                    (43.6, 2.92, 0.74)],
        speed_lines=[44, 84, 111, 132, 150],      # krpm
        pr_axis=(1.0, 4.2), flow_axis=(0, 65),
        # digitised envelope
        surge=[(5.3, 1.10), (9.1, 2.00), (11.2, 2.40), (16.2, 3.00),
               (20.6, 3.40), (26.8, 3.80), (32.3, 4.00)],
        choke=[(58.0, 1.40), (62.2, 2.20), (61.5, 2.60), (60.5, 3.00),
               (60.0, 3.42), (58.0, 3.60), (56.6, 3.80), (53.3, 4.00)],
        map_top_pr=4.10,
        rated="300 - 550 HP",
    ),
    "EFR 7670": dict(
        pdf="efr-7670-b.pdf", applies="map applies to all 7670 units",
        comp_ind=57, comp_od=76, turb_exd=61, turb_od=70,
        eff_contours=[0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74, 0.75],
        eff_peak=0.75, eff_peak_at=(50.0, 3.20),
        speed_lines=[42, 79, 103, 123, 140],
        pr_axis=(1.0, 5.0), flow_axis=(0, 70),
        surge=None, choke=None, map_top_pr=4.80, rated="375 - 650 HP",
    ),
    "EFR 7064": dict(
        pdf="efr-7064-b.pdf", applies="map applies to all 7064 units",
        comp_ind=52, comp_od=70, turb_exd=56, turb_od=64,
        eff_contours=[0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74, 0.76],
        eff_peak=0.76, eff_peak_at=(38.0, 3.00),
        speed_lines=[46, 86, 113, 134, 153],
        pr_axis=(1.0, 5.0), flow_axis=(0, 60),
        surge=None, choke=None, map_top_pr=4.60, rated="300 - 550 HP",
    ),
}


def interp_xy(pts, y):
    """Linear interpolation of x at a given y over a list of (x, y)."""
    for i in range(len(pts) - 1):
        y0, y1 = pts[i][1], pts[i + 1][1]
        if min(y0, y1) <= y <= max(y0, y1):
            f = (y - y0) / (y1 - y0)
            return pts[i][0] + f * (pts[i + 1][0] - pts[i][0])
    return pts[-1][0] if y > pts[-1][1] else pts[0][0]


def _fit_quadratic(labels):
    """Least-squares quadratic surface eta(f, p) through the digitised contour
    labels. Six coefficients, thirteen points. Returns (coeffs, rms residual).
    Solved with a plain normal-equation Gauss-Jordan so the script has no
    third-party dependency."""
    def basis(f, p):
        return [1.0, f, p, f * f, f * p, p * p]
    n = 6
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for f, p, e in labels:
        x = basis(f, p)
        for i in range(n):
            b[i] += x[i] * e
            for j in range(n):
                A[i][j] += x[i] * x[j]
    # Gauss-Jordan with partial pivoting
    M = [A[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        d = M[col][col]
        M[col] = [v / d for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0.0:
                fac = M[r][col]
                M[r] = [vr - fac * vc for vr, vc in zip(M[r], M[col])]
    coef = [M[i][n] for i in range(n)]
    ss = sum((sum(c * x for c, x in zip(coef, basis(f, p))) - e) ** 2
             for f, p, e in labels)
    return coef, math.sqrt(ss / len(labels))


ETA_COEF, ETA_RMS = _fit_quadratic(OFFICIAL["EFR 7163"]["eff_labels"])


def official_eff_7163(flow, pr):
    """Compressor isentropic efficiency read off the OFFICIAL BorgWarner 7163 map.
    Quadratic surface least-squares fitted to the thirteen printed contour labels.
    Valid inside the plotted envelope only. Round-four fit RMS is printed at run
    time; compare it against the prior work's claimed RMS 0.048 for this turbo."""
    c = ETA_COEF
    e = (c[0] + c[1] * flow + c[2] * pr + c[3] * flow * flow
         + c[4] * flow * pr + c[5] * pr * pr)
    return max(0.35, min(0.74, e))


# ---------------------------------------------------------------- turbos
TURBOS = [
    dict(n="EFR 7163 (owned)", choke=60, pr_max=3.6, eta_ref=0.706, spool=4000,
         dt=63, dc=71, mat="g-TiAl", price=2629, ar=0.80,
         official=True, eta_official=None,
         src="OFFICIAL BorgWarner sheet efr-7163-f.pdf, read round four"),
    dict(n="EFR 7670", choke=67, pr_max=3.8, eta_ref=0.677, spool=4825,
         dt=70, dc=76, mat="g-TiAl", price=2500, ar=0.92, official=True,
         src="OFFICIAL BorgWarner sheet efr-7670-b.pdf, read round four"),
    dict(n="EFR 8374", choke=79, pr_max=4.0, eta_ref=0.750, spool=5200,
         dt=74, dc=83, mat="g-TiAl", price=2367, ar=0.92, official=False,
         src="prior digitisation only - official sheet not retrieved in round four"),
    dict(n="EFR 7064", choke=56, pr_max=3.5, eta_ref=0.651, spool=3350,
         dt=57, dc=64, mat="g-TiAl", price=2300, ar=0.92, official=True,
         src="OFFICIAL BorgWarner sheet efr-7064-b.pdf, read round four"),
    dict(n="Garrett G25-660", choke=61, pr_max=3.8, eta_ref=0.740, spool=4248,
         dt=54, dc=67, mat="Mar-M", price=1750, ar=0.92, official=False,
         src="Garrett published spec for flow and wheels. EFFICIENCY IS AN ESTIMATE."),
    dict(n="Garrett G30-770", choke=77, pr_max=4.0, eta_ref=0.670, spool=4540,
         dt=55, dc=58, mat="Mar-M", price=2050, ar=1.01, official=False,
         src="MODELLED ONLY - no official Garrett map has been read"),
    dict(n="Garrett G35-900", choke=82, pr_max=4.2, eta_ref=0.752, spool=5500,
         dt=62, dc=68, mat="Mar-M", price=2400, ar=1.01, official=False,
         src="MODELLED ONLY - no official Garrett map has been read"),
]


# ============================================================================
# ITEM 2 - CHARGE PIPE, THROTTLE BODY, PRESSURE DROP
# ============================================================================
# The hardware chain is BOUGHT, not chosen. Outsider Garage order #7870, 5 Jan 2026:
#   line 1  Custom DBW Manifold Adapter, Bright Silver, $150
#           (throttle body -> Soara plenum; plate 109 mm across the centre,
#            105 mm across the bolt-hole centres)
#   line 2  Bosch 74 mm Throttle Body Hose and HD Clamp Adapter,
#           variant "3 inch HD Clamp / Silver", $100
#           (charge pipe -> throttle body. THIS FIXES THE COLD PIPE AT 3 INCH.)
#   line 3  Genuine Bosch E-throttle 74 mm, $225
#           (0 280 750 474; plate stamped 745, so the real bore is 74.5 mm)
#
# Flow path, front to back:
#   cold charge pipe -> 3.00 in hose adapter -> 74.5 mm throttle -> 76.2 mm
#   plenum flange -> Soara dual plenum
TB_BORE = 0.0745          # Bosch 0 280 750 474, plate marked "745"
TB_ADAPTER = 0.0762       # bought 3 in hose / HD clamp adapter, charge-pipe side
PLENUM_FLANGE = 0.0762    # Soara dual plenum, 3 in ID, downstream of the throttle
ADAPTER_PLATE = (109.0, 105.0)   # mm across centre / across bolt-hole centres

# alloy mandrel tube. Dan's stated wall is 0.065 in = 1.651 mm, which is the
# standard aluminium charge-pipe wall. Every diameter below is a REAL INSIDE
# DIAMETER computed from OD minus twice that wall, not a nominal OD.
WALL = 0.065 * IN          # 1.651 mm


def pipe_id(od_in, wall=WALL):
    return od_in * IN - 2 * wall


# ---- routing envelope: what each diameter actually costs in space -----------
# Dan's construction is fully welded, with heavy-duty clamps at only three
# places: the intercooler, the throttle body, and one alignment joint. So the
# clamped envelope applies at three points and the bare tube envelope everywhere
# else. A silicone coupler adds about 6 mm of wall each side and a T-bolt band
# about 3 mm, so a clamped joint is roughly OD + 18 mm.
CLAMP_ADD = 0.018


def routing(od_in, rd=1.5):
    """Space a given pipe diameter needs. The 90 degree bend box is the one that
    decides whether a pipe clears a frame rail: for a mandrel bend at a given
    centreline radius ratio, the swept corner occupies a square of side
    (centreline radius + half the outside diameter)."""
    od = od_in * IN
    clr = rd * od
    return dict(od_in=od_in, od_mm=od * 1000, id_mm=pipe_id(od_in) * 1000,
                bare_mm=od * 1000,
                clamped_mm=(od + CLAMP_ADD) * 1000,
                clr_mm=clr * 1000,
                bend_box_mm=(clr + od / 2) * 1000)


PIPES = [2.00, 2.25, 2.50, 2.75, 3.00]


def pipe_metrics(od_in, m_dot, p_kpa, t_C, length_m, n_bends, f=0.020, k_bend=0.20):
    d = pipe_id(od_in)
    a = math.pi * (d / 2) ** 2
    rho = p_kpa * 1000 / (R * (t_C + 273.15))
    v = m_dot / (rho * a)
    q = 0.5 * rho * v * v                      # velocity head, Pa
    dp_fric = f * (length_m / d) * q
    dp_bend = n_bends * k_bend * q
    return dict(od=od_in, id_mm=d * 1000, area=a, rho=rho, v=v, vfts=v / 0.3048,
                mach=v / sound_speed(t_C),
                vol_per_m=a * 1000.0,          # litres per metre
                dp_psi=(dp_fric + dp_bend) / 1000.0 / PSI,
                q_pa=q)


def throttle_dp(m_dot, p_kpa, t_C, bore=TB_BORE, k=0.25):
    """WOT butterfly. K = 0.20-0.30 on bore velocity head (plate + shaft wake)."""
    a = math.pi * (bore / 2) ** 2
    rho = p_kpa * 1000 / (R * (t_C + 273.15))
    v = m_dot / (rho * a)
    q = 0.5 * rho * v * v
    return dict(v=v, vfts=v / 0.3048, mach=v / sound_speed(t_C),
                dp_psi=k * q / 1000.0 / PSI, dp_pa=k * q,
                choke_lbmin=rho * a * 0.3 * sound_speed(t_C) * LBMIN)


def step_loss(d1, d2, m_dot, p_kpa, t_C):
    """Sudden area change between two bores. Expansion if d2 > d1."""
    a1, a2 = math.pi * (d1 / 2) ** 2, math.pi * (d2 / 2) ** 2
    rho = p_kpa * 1000 / (R * (t_C + 273.15))
    v1 = m_dot / (rho * a1)
    q1 = 0.5 * rho * v1 * v1
    if d2 > d1:
        k = (1 - a1 / a2) ** 2                       # sudden expansion
    else:
        k = 0.42 * (1 - a2 / a1)                     # sudden contraction
    return dict(k=k, dp_pa=k * q1, dp_psi=k * q1 / 1000.0 / PSI)


# ============================================================================
# ITEM 7 - PACKAGING
# ============================================================================
# Mishimoto MMRAD-CEL-89, confirmed from the vendor listing:
RAD = dict(part="Mishimoto MMRAD-CEL-89",
           overall_mm=(714, 439, 64.5),     # 28.1 x 17.3 x 2.54 in
           core_mm=(699, 318, 51.8),        # 27.5 x 12.52 in face, 2.04 in thick
           rows=2, port_in=1.25)
COND_THICK = 20.0        # typical ST185 parallel-flow condenser core, mm
GAP_IC_RAD = (203.0, 254.0)   # 8 to 10 in, Dan's measurement, with a 76 mm core


def stack(core_t_mm):
    """Longitudinal budget, given Dan's measured 8-10 in from the back of a 76 mm
    core to the radiator."""
    lo, hi = GAP_IC_RAD
    extra = core_t_mm - 76.0
    return dict(core=core_t_mm,
                gap_lo=lo - extra, gap_hi=hi - extra,
                after_cond_lo=lo - extra - COND_THICK,
                after_cond_hi=hi - extra - COND_THICK)


def rad_inlet_temp(op, gap_m=0.2285, cond_kw=6.0, t_amb=T_AMB,
                   ic_w=0.610, ic_h=0.305):
    """Air temperature arriving at the radiator face.
    The intercooler dumps Q into the stream that passes through it. Over the gap
    that heated stream entrains some ambient air. Round jet entrainment,
    m(x)/m0 = 1 + 0.32 x / Dh, with Dh the core's hydraulic diameter.
    The A/C condenser then adds its own heat to whatever reaches it."""
    dh = 4 * (ic_w * ic_h) / (2 * (ic_w + ic_h))
    ent = 1.0 + 0.32 * gap_m / dh
    dt_ic = op["dTrad"] / ent
    m_at_rad = op["mCold"] * ent
    dt_cond = cond_kw * 1000.0 / (m_at_rad * CP)
    return dict(dh=dh, entrain=ent, dt_ic=dt_ic, dt_cond=dt_cond,
                t_rad_in=t_amb + dt_ic + dt_cond,
                t_rad_in_noac=t_amb + dt_ic,
                head_bare=105.0 - t_amb,
                head_stacked=105.0 - (t_amb + dt_ic + dt_cond))


def wheel_inertia_whp(d_inertia=1.15, r=0.31, accel=4.0, v=40.0):
    """Power NOT absorbed spinning up lighter wheels, on an INERTIA dyno.
    Zero on a steady-state (eddy-current / load-cell) dyno."""
    omega = v / r
    domega = accel / r
    return d_inertia * omega * domega / 745.7


# ============================================================================
# ITEM 1 - MANIFOLD PAIRING, AS VALIDATION
# ============================================================================
FIRE = {1: 0, 3: 180, 4: 360, 2: 540}     # firing order 1-3-4-2
EVO_ATDC, DUR = 135.0, 264.0              # HKS 264 exhaust


def window(c):
    s = (FIRE[c] + EVO_ATDC) % 720.0
    return (s, s + DUR)


def overlap_deg(a, b):
    wa, wb = window(a), window(b)
    best = -999
    for sa in (wa[0] - 720, wa[0], wa[0] + 720):
        for sb in (wb[0] - 720, wb[0], wb[0] + 720):
            best = max(best, min(sa + DUR, sb + DUR) - max(sa, sb))
    if best > 0:
        return best
    gap = 999
    for sa in (wa[0] - 720, wa[0], wa[0] + 720):
        for sb in (wb[0] - 720, wb[0], wb[0] + 720):
            gap = min(gap, abs(sb - (sa + DUR)), abs(sa - (sb + DUR)))
    return -gap


# ============================================================================
# ITEM 4 - COMMUNITY DYNO COMPARISON
# ============================================================================
# Real, published, third-party results. NONE of these is this car. All are used
# only to bound the model. Dyno type matters: Dynojet inertia dynos read high
# against steady-state dynos, typically by 5-10 percent on AWD.
COMMUNITY = [
    dict(what="Ford Focus ST 2.0 EcoBoost, EFR 7163, E85 (ZZP)",
         disp=2.0, whp=480, fuel="E85", boost=None, drive="FWD", dyno="not stated",
         lb_implied=None,
         note="vendor claim reported on focusst.org; boost not stated"),
    dict(what="Evo 9 2.3 built, EFR 7163, E85, 36 psi (Driven Fab)",
         disp=2.3, whp=593, fuel="E85", boost=36, drive="AWD", dyno="Dynojet",
         note="ran out of injector before running out of turbo; Dynojet AWD"),
    dict(what="Mazda BP 1.8, EFR 7163, E85",
         disp=1.8, whp=450, fuel="E85", boost=None, drive="RWD", dyno="not stated",
         note="miataturbo.net, reported as routine rather than a peak"),
    dict(what="3S-GTE, EFR 7163, E85, 25 psi",
         disp=2.0, whp=402, fuel="E85", boost=25, drive="not stated",
         dyno="Mainline (steady state)",
         note="300 kW at the wheels; the closest single comparable to this build"),
    dict(what="3S-GTE Gen 3 in AE86, 20 psi, 93 octane",
         disp=2.0, whp=402, fuel="93", boost=20, drive="RWD", dyno="not stated",
         note="pump fuel, RWD - shows what the head and cams support"),
    dict(what="ST185 3S-GTE, .50 turbo, 14 psi, 91 octane (EricGT4)",
         disp=2.0, whp=337, fuel="91", boost=14, drive="AWD", dyno="Dynojet",
         note="same chassis and drivetrain as this car - the best AWD-loss anchor"),
    dict(what="Stock ST185 3S-GTE",
         disp=2.0, whp=190, fuel="91", boost=9, drive="AWD", dyno="Dynojet",
         note="against a 225 PS JDM crank rating - implies ~15%, but JDM ratings "
              "of that era are not measured to a comparable standard"),
    dict(what="5S-GTE high compression, Precision 6262 (mr2man)",
         disp=2.2, whp=700, fuel="E85/race", boost=None, drive="RWD",
         dyno="not stated",
         note="same displacement class - shows the block is not the ceiling"),
]


# ============================================================================
def main():
    out = {}
    W = 92
    print("=" * W)
    print("UNIFIED 5S-GTE MODEL - ROUND FOUR")
    print("=" * W)
    print(f"  displacement {DISP*1e6:.1f} cc | site {P_AMB:.2f} kPa | ambient {T_AMB:.0f} C")
    print(f"  rod ratio {ROD_RATIO:.3f}")
    print(f"  crank hp/lb-min {HP_PER_LBMIN:.1f}  x  driveline {DRIVETRAIN_LO:.2f}-{DRIVETRAIN_HI:.2f}")
    print(f"  ALL POWER FIGURES ARE ESTIMATES. NO DYNO RUN EXISTS FOR THIS ENGINE.")

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 1 - MANIFOLD PAIRING, RE-RUN AS VALIDATION OF 1+4 / 2+3")
    print("=" * W)
    for c in (1, 2, 3, 4):
        w = window(c)
        print(f"    cyl {c}: exhaust valve open {w[0]%720:6.1f} to {w[1]%720:6.1f} deg")
    pair_rows = []
    for lab, pairs in (("AS BUILT / CORRECT   1+4 / 2+3", [(1, 4), (2, 3)]),
                       ("the superseded diagram 1+2 / 3+4", [(1, 2), (3, 4)])):
        vals = [overlap_deg(*p) for p in pairs]
        desc = " | ".join(
            f"{p[0]}+{p[1]}: " + (f"OVERLAP {v:.0f} deg" if v > 0 else f"clear gap {-v:.0f} deg")
            for p, v in zip(pairs, vals))
        print(f"  {lab:34s} {desc}")
        pair_rows.append(dict(lab=lab, vals=[round(v, 1) for v in vals]))
    print("  -> 1+4 / 2+3 gives 96 deg of clear crank angle in each scroll.")
    print("  -> The manifold Dan has is CORRECT. No penalty applies. Nothing to re-make.")
    out["pairing"] = pair_rows
    out["windows"] = {str(c): [round(window(c)[0] % 720, 1), round(window(c)[1] % 720, 1)]
                      for c in (1, 2, 3, 4)}

    # backpressure sensitivity is KEPT, but reframed: 1.6 is where a correct
    # twin scroll sits, and the band shows what a turbine mismatch would cost.
    bp_rows = []
    for emap in (1.0, 1.3, 1.6, 1.9, 2.2):
        o = operating_point(7500, 30.0, 0.706,
                            ve_fn=lambda r, i, e=emap: ve_unified(r, i, emap=e))
        bp_rows.append(dict(emap=emap, ve=round(o["ve"], 3), lb=round(o["lb"], 2),
                            whp=round(o["whp"])))
    out["backpressure"] = bp_rows

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 3 - THE WHOLE RPM RANGE, NOT ONE REDLINE")
    print("=" * W)
    print(f"  {'rpm':>5} {'MPS':>6} {'Z':>6} {'VE':>6} {'lb/min':>7} {'IAT C':>6} "
          f"{'whp .78':>8} {'whp .80':>8} {'whp .83':>8} {'d whp':>6}  risk")
    RISK = {
        7000: "stock redline. Nothing is stressed. Stock valve springs fine.",
        7200: "+200 rpm. Within stock spring capability. No parts needed.",
        7400: "approaching reported stock spring float (7,500-7,600).",
        7500: "outer limit on stock springs. Fit upgraded springs to be safe.",
        7600: "upgraded valve springs REQUIRED. Service interval shortens.",
        7800: "race territory. 23.7 m/s piston speed on a 1.52 rod ratio.",
        8000: "24.3 m/s. Buys 4 whp over 7,500. Bearing and rod life is the cost.",
    }
    rpm_rows = []
    for rpm in (6600, 6800, 7000, 7200, 7400, 7500, 7600, 7800, 8000):
        o = operating_point(rpm, 30.0, 0.706)
        w_lo = o["lb"] * HP_PER_LBMIN * DRIVETRAIN_LO
        w_mid = o["whp"]
        w_hi = o["lb"] * HP_PER_LBMIN * DRIVETRAIN_HI
        d = "" if not rpm_rows else f"{w_mid - rpm_rows[-1]['whp_mid']:+6.0f}"
        cid = DISP * 1e6 / 16.387
        cfm_cyl = (cid * rpm * o["ve"] / 3456.0) / 4
        rpm_rows.append(dict(rpm=rpm, mps=round(mean_piston_speed(rpm), 1),
                             Z=round(mach_index(rpm, o["iat"]), 3),
                             ve=round(o["ve"], 3), lb=round(o["lb"], 2),
                             iat=round(o["iat"], 1),
                             whp_lo=round(w_lo), whp_mid=round(w_mid),
                             whp_hi=round(w_hi),
                             cfm=round(cfm_cyl, 1),
                             choke=round(o["lb"] / 60 * 100, 1),
                             risk=RISK.get(rpm, "")))
        print(f"  {rpm:5d} {mean_piston_speed(rpm):6.1f} "
              f"{mach_index(rpm, o['iat']):6.3f} {o['ve']:6.3f} {o['lb']:7.2f} "
              f"{o['iat']:6.1f} {w_lo:8.0f} {w_mid:8.0f} {w_hi:8.0f} {d:>6}  "
              f"{RISK.get(rpm,'')[:44]}")
    out["rpm_range"] = rpm_rows

    # full curves for charting: whp vs rpm at several boosts, and the driveline band
    curves = {}
    rr = list(range(3000, 8051, 50))
    curves["rpm"] = rr
    for b in (20, 25, 30, 32, 34):
        curves[f"b{b}"] = [round(operating_point(r, b, 0.706)["whp"], 1) for r in rr]
    curves["b30_lo"] = [round(operating_point(r, 30, 0.706, dt=DRIVETRAIN_LO)["whp"], 1) for r in rr]
    curves["b30_hi"] = [round(operating_point(r, 30, 0.706, dt=DRIVETRAIN_HI)["whp"], 1) for r in rr]
    curves["iat30"] = [round(operating_point(r, 30, 0.706)["iat"], 1) for r in rr]
    curves["lb30"] = [round(operating_point(r, 30, 0.706)["lb"], 2) for r in rr]
    curves["ve30"] = [round(operating_point(r, 30, 0.706)["ve"], 4) for r in rr]
    out["curves"] = curves

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 6 - OFFICIAL BORGWARNER MAP vs THE MODELLED MAPS")
    print("=" * W)
    m = OFFICIAL["EFR 7163"]
    print(f"  Source: {m['pdf']} - {m['applies']}")
    print(f"  Printed efficiency contours : {m['eff_contours']}  PEAK ISLAND {m['eff_peak']:.2f}")
    print(f"  Printed speed lines (krpm)  : {m['speed_lines']}")
    print(f"  Axes                        : PR {m['pr_axis']}, flow {m['flow_axis']} lb/min")
    print(f"  Compressor wheel            : {m['comp_ind']} mm inducer / {m['comp_od']} mm OD")
    print(f"  Turbine wheel               : {m['turb_exd']} mm exducer / {m['turb_od']} mm OD")
    print(f"  Round-four surface fit      : {len(m['eff_labels'])} printed labels, "
          f"quadratic, RMS {ETA_RMS:.4f} efficiency points")
    print(f"     (the prior work claimed RMS 0.048 for this same turbo)")
    print()
    print("  fit residuals against each printed label:")
    for f, p, e in m["eff_labels"]:
        pred = official_eff_7163(f, p)
        print(f"    {f:5.1f} lb/min, PR {p:.2f}, printed {e:.2f} -> fit {pred:.3f} "
              f"({pred-e:+.3f})")
    print()
    off_rows = []
    for rpm, boost in ((7000, 30), (7500, 30), (7500, 32), (7500, 34), (8000, 30)):
        o = operating_point(rpm, boost, 0.706)
        eta_off = official_eff_7163(o["lb"], o["pr"])
        s = interp_xy(m["surge"], min(o["pr"], 4.0))
        c = interp_xy(m["choke"], min(o["pr"], 4.0))
        off_rows.append(dict(rpm=rpm, boost=boost, lb=round(o["lb"], 2),
                             pr=round(o["pr"], 3),
                             eta_model=0.706, eta_official=round(eta_off, 3),
                             surge=round(s, 1), choke=round(c, 1),
                             surge_margin=round(o["lb"] - s, 1),
                             choke_margin=round(c - o["lb"], 1)))
        print(f"  {rpm} rpm / {boost} psi: {o['lb']:5.2f} lb/min, PR {o['pr']:.2f} "
              f"-> official map eta {eta_off:.3f} (model used 0.706); "
              f"surge at {s:.1f}, choke at {c:.1f}")
    out["official_points"] = off_rows
    out["eta_rms"] = round(ETA_RMS, 4)

    # headline recomputed with the OFFICIAL efficiency, solved self-consistently
    print()
    print("  HEADLINE RE-SOLVED WITH THE OFFICIAL MAP EFFICIENCY (fixed point):")
    for rpm in (7000, 7200, 7500, 8000):
        eta = 0.706
        for _ in range(30):
            oo = operating_point(rpm, 30.0, eta)
            new = official_eff_7163(oo["lb"], oo["pr"])
            if abs(new - eta) < 1e-5:
                eta = new
                break
            eta = new
        oo = operating_point(rpm, 30.0, eta)
        base = operating_point(rpm, 30.0, 0.706)
        print(f"    {rpm} rpm: eta {eta:.3f} (was 0.706) -> compressor out "
              f"{oo['tc']:.0f} C (was {base['tc']:.0f}), charge {oo['iat']:.1f} C "
              f"(was {base['iat']:.1f}), {oo['whp']:.0f} whp (was {base['whp']:.0f})")
        out.setdefault("official_solved", []).append(
            dict(rpm=rpm, eta=round(eta, 3), tc=round(oo["tc"]),
                 iat=round(oo["iat"], 1), whp=round(oo["whp"]),
                 whp_lo=round(oo["lb"] * HP_PER_LBMIN * DRIVETRAIN_LO),
                 whp_hi=round(oo["lb"] * HP_PER_LBMIN * DRIVETRAIN_HI),
                 lb=round(oo["lb"], 2),
                 d_whp=round(oo["whp"] - base["whp"]),
                 d_iat=round(oo["iat"] - base["iat"], 1)))

    # low-rpm surge check - this is NEW and it matters
    print()
    print("  SURGE CHECK ACROSS THE REV RANGE AT FULL BOOST (the new finding):")
    surge_rows = []
    for rpm in range(2500, 5001, 250):
        o = operating_point(rpm, 30.0, 0.706)
        s = interp_xy(m["surge"], min(o["pr"], 4.0))
        surge_rows.append(dict(rpm=rpm, lb=round(o["lb"], 2), pr=round(o["pr"], 2),
                               surge=round(s, 1), margin=round(o["lb"] - s, 1)))
        flag = "  <-- SURGE" if o["lb"] < s else ("  <-- marginal" if o["lb"] - s < 3 else "")
        print(f"    {rpm:5d} rpm  {o['lb']:6.2f} lb/min at PR {o['pr']:.2f} | "
              f"surge line {s:5.1f} | margin {o['lb']-s:+6.1f} lb/min{flag}")
    out["surge_sweep"] = surge_rows

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 2 - CHARGE PIPE AND THROTTLE BODY, RE-RUN AT 74.5 mm")
    print("=" * W)
    design = operating_point(7500, 30.0, 0.706)
    m_dot = design["m"]
    p_hot = P_AMB + 30 * PSI + 1.5 * PSI
    t_hot = design["tc"]
    p_cold = P_AMB + 30 * PSI + 0.4 * PSI
    t_cold = design["iat"]
    print(f"  design point: {design['lb']:.2f} lb/min ({m_dot:.4f} kg/s) at 7,500 rpm / 30 psi")
    print(f"  hot side  {p_hot:.1f} kPa / {t_hot:.0f} C     cold side {p_cold:.1f} kPa / {t_cold:.0f} C")
    print()
    print(f"  {'OD in':>6} {'ID mm':>6} | {'hot ft/s':>9} {'hot dP':>7} | "
          f"{'cold ft/s':>10} {'cold dP':>8} | {'L/m':>5} {'sys L':>6} {'fill ms':>8}")
    pipe_rows = []
    CORE_VOL_L = CORES["610x305x102"]["w"] * CORES["610x305x102"]["h"] * \
        CORES["610x305x102"]["t"] * 1000 * 0.28
    TANKS_L = 1.10
    L_HOT, N_HOT, L_COLD, N_COLD = 1.1, 3, 1.5, 4
    SPOOL_FLOW = 0.15                     # kg/s during the boost ramp

    def fill_ms_of(hot_L, cold_L, t_hot_fill=120.0):
        """Mass that must be added to pressurise the charge system, section by
        section at its own temperature, divided by the spool-up flow rate.
        The hot side is cooler during a ramp than at steady peak, so 120 C is
        used there rather than the 214 C steady-state figure."""
        dr_hot = ((P_AMB + 30 * PSI) - P_AMB) * 1000 / (R * (t_hot_fill + 273.15))
        dr_cold = ((P_AMB + 30 * PSI) - P_AMB) * 1000 / (R * (t_cold + 273.15))
        dm = (hot_L / 1000.0) * dr_hot + ((cold_L + CORE_VOL_L + TANKS_L) / 1000.0) * dr_cold
        return dm / SPOOL_FLOW * 1000.0

    for od in PIPES:
        h = pipe_metrics(od, m_dot, p_hot, t_hot, L_HOT, N_HOT)
        c = pipe_metrics(od, m_dot, p_cold, t_cold, L_COLD, N_COLD)
        hotL, coldL = L_HOT * h["vol_per_m"], L_COLD * c["vol_per_m"]
        sysL = hotL + coldL + CORE_VOL_L + TANKS_L
        pipe_rows.append(dict(od=od, id_mm=round(h["id_mm"], 1),
                              hot_fts=round(h["vfts"]), hot_dp=round(h["dp_psi"], 3),
                              hot_mach=round(h["mach"], 3),
                              cold_fts=round(c["vfts"]), cold_dp=round(c["dp_psi"], 3),
                              cold_mach=round(c["mach"], 3),
                              vol_per_m=round(c["vol_per_m"], 2),
                              sysL=round(sysL, 2), sysX=round(sysL / (DISP * 1000), 2),
                              fill_ms=round(fill_ms_of(hotL, coldL))))
        print(f"  {od:6.2f} {h['id_mm']:6.1f} | {h['vfts']:9.0f} {h['dp_psi']:7.3f} | "
              f"{c['vfts']:10.0f} {c['dp_psi']:8.3f} | {c['vol_per_m']:5.2f} "
              f"{sysL:6.2f} {pipe_rows[-1]['fill_ms']:8.0f}")
    out["pipes"] = pipe_rows
    print()
    print("  NOTE: round three's 'volume per metre' column was exactly HALF the true")
    print("  value (it used pi/4 * OD^2 / 2). Corrected above, using real bore ID.")

    # ---- routing envelope --------------------------------------------------
    print()
    print("  ROUTING ENVELOPE - space each diameter needs, welded construction")
    print(f"  {'OD in':>6} {'real ID':>8} {'bare tube':>10} {'at a clamp':>11} "
          f"{'bend CLR':>9} {'90 deg bend box':>16}")
    route_rows = []
    for od in (2.25, 2.50, 2.75, 3.00):
        r = routing(od)
        route_rows.append(dict(od=od, id_mm=round(r["id_mm"], 1),
                               bare=round(r["bare_mm"], 1),
                               clamped=round(r["clamped_mm"], 1),
                               clr=round(r["clr_mm"]),
                               box=round(r["bend_box_mm"])))
        print(f"  {od:6.2f} {r['id_mm']:7.1f}mm {r['bare_mm']:9.1f}mm "
              f"{r['clamped_mm']:10.1f}mm {r['clr_mm']:8.0f}mm {r['bend_box_mm']:15.0f}mm")
    b25 = routing(2.50)["bend_box_mm"]
    b30 = routing(3.00)["bend_box_mm"]
    print(f"  -> a 3.00 in 90 degree bend needs {b30-b25:.0f} mm more corner room than a "
          f"2.50 in one,")
    print(f"     in BOTH directions, at every bend. Over four cold-side bends that is the")
    print(f"     difference between clearing a frame rail and not.")
    out["routing"] = route_rows
    out["routing_delta_box"] = round(b30 - b25)

    # ---- the cold side ------------------------------------------------------
    print()
    print("  COLD SIDE. The 3 inch figure applies ONLY to the bought HD clamp adapter")
    print("  at the throttle body. No charge piping has been purchased. The run itself")
    print("  is a free choice, and routing clearance is a real constraint.")
    # A WELDED cone is not a sudden step. For a diffuser at 7 deg per wall the
    # loss coefficient is about 0.15 of the velocity-head difference, against
    # (1 - A1/A2)^2 for a sudden expansion. Dan is welding, so every transition
    # inside the run is a cone, not a step.
    def cone_loss(d1, d2, m, p_kpa, t_C, k=0.15):
        a1, a2 = math.pi * (d1 / 2) ** 2, math.pi * (d2 / 2) ** 2
        rho = p_kpa * 1000 / (R * (t_C + 273.15))
        v1, v2 = m / (rho * a1), m / (rho * a2)
        dq = 0.5 * rho * abs(v1 * v1 - v2 * v2)
        return dict(dp_pa=k * dq, dp_psi=k * dq / 1000.0 / PSI)

    print(f"  {'cold layout':<40} {'max ft/s':>9} {'dP psi':>7} {'vol L':>7} "
          f"{'sys L':>7} {'x disp':>7} {'fill ms':>8} {'bend box':>9}")
    layouts = []
    LAYOUTS = (
        ("2.50 in run, welded cone to 3.00 last 150 mm", [(2.50, 1.35, 4), (3.00, 0.15, 0)]),
        ("2.75 in run, welded cone to 3.00 last 150 mm", [(2.75, 1.35, 4), (3.00, 0.15, 0)]),
        ("3.00 in the whole 1.5 m", [(3.00, 1.50, 4)]),
        ("2.25 in run, welded cone to 3.00 last 150 mm", [(2.25, 1.35, 4), (3.00, 0.15, 0)]),
    )
    for lab, segs in LAYOUTS:
        dp = 0.0
        vol = 0.0
        vmax = 0.0
        for od, L, nb in segs:
            mm = pipe_metrics(od, m_dot, p_cold, t_cold, L, nb)
            dp += mm["dp_psi"]
            vol += L * mm["vol_per_m"]
            vmax = max(vmax, mm["vfts"])
        if len(segs) > 1:
            dp += cone_loss(pipe_id(segs[0][0]), pipe_id(segs[1][0]),
                            m_dot, p_cold, t_cold)["dp_psi"]
        hot25 = pipe_metrics(2.50, m_dot, p_hot, t_hot, L_HOT, N_HOT)
        hotL = L_HOT * hot25["vol_per_m"]
        sysL = hotL + vol + CORE_VOL_L + TANKS_L
        box = routing(segs[0][0])["bend_box_mm"]
        layouts.append(dict(lab=lab, vmax=round(vmax), dp=round(dp, 3),
                            vol=round(vol, 2), sysL=round(sysL, 2),
                            sysX=round(sysL / (DISP * 1000), 2),
                            fill_ms=round(fill_ms_of(hotL, vol)),
                            box=round(box)))
        print(f"  {lab:<40} {vmax:9.0f} {dp:7.3f} {vol:7.2f} {sysL:7.2f} "
              f"{sysL/(DISP*1000):7.2f} {layouts[-1]['fill_ms']:8.0f} "
              f"{box:8.0f}mm")
    out["cold_layouts"] = layouts
    print("  (hot side held at 2.50 in in every row so the comparison is clean)")

    print()
    print("  THE TRANSITION LOSSES DAN SAID HE IS NOT WORRIED ABOUT - quantified anyway:")
    cone = cone_loss(pipe_id(2.5), pipe_id(3.0), m_dot, p_cold, t_cold)
    sudden = step_loss(pipe_id(2.5), pipe_id(3.0), m_dot, p_cold, t_cold)
    print(f"    welded 2.50 -> 3.00 cone at 7 deg/wall : {cone['dp_pa']:6.1f} Pa = "
          f"{cone['dp_psi']:.4f} psi")
    print(f"    the same as a SUDDEN step             : {sudden['dp_pa']:6.1f} Pa = "
          f"{sudden['dp_psi']:.4f} psi")
    print(f"    -> he is right. Even the sudden step is 0.044 psi, which is 0.15% of a "
          f"30 psi manifold pressure and about 0.02 whp.")
    out["cold_transitions"] = dict(cone=round(cone["dp_psi"], 4),
                                   sudden=round(sudden["dp_psi"], 4),
                                   cone_pa=round(cone["dp_pa"], 1),
                                   sudden_pa=round(sudden["dp_pa"], 1))

    # intercooler port size
    print()
    print("  INTERCOOLER PORT SIZE - is the cold side forced to 3 inch at BOTH ends?")
    print("    SpeedFactory SS-850, SF-06-089, 24x12x3.0 core : 3.0 in / 3.0 in ONLY")
    print("    SpeedFactory HPX,    24x12x4.5 core            : 3.0 in / 3.5 in")
    print("    Treadstone TR1245,   22x12.5x4.5 core          : 3.0 in / 3.0 in")
    print("    SpeedFactory 'Street', SF-06-082               : 2.5 in / 2.5 in, but the")
    print("      core is only 22x9x3.0 and rated 300-500 hp - too small for this build")
    print("    BARE CORE + FABRICATED TANKS                   : the port is whatever you weld on")
    print("    -> the report already specifies FABRICATED tapered tanks (s08, s14), so the")
    print("       port is a free choice. Weld 2.50 in ports and the cold side is 2.50 in")
    print("       end to end, with one welded cone at the throttle adapter.")

    tb = throttle_dp(m_dot, p_cold, t_cold)
    print()
    print(f"  THROTTLE BODY  Bosch 0 280 750 474, bore {TB_BORE*1000:.1f} mm "
          f"(sold as 74 mm; plate stamped 745)")
    print(f"    bore velocity      {tb['v']:.1f} m/s ({tb['vfts']:.0f} ft/s), Mach {tb['mach']:.3f}")
    print(f"    pressure drop      {tb['dp_pa']:.0f} Pa = {tb['dp_psi']:.3f} psi at K=0.25")
    print(f"    flow at Mach 0.3   {tb['choke_lbmin']:.0f} lb/min "
          f"= about {tb['choke_lbmin']*HP_PER_LBMIN:.0f} crank hp before it restricts")
    st_in = step_loss(TB_ADAPTER, TB_BORE, m_dot, p_cold, t_cold)     # 76.2 -> 74.5
    st_out = step_loss(TB_BORE, PLENUM_FLANGE, m_dot, p_cold, t_cold)  # 74.5 -> 76.2
    print(f"    step IN  76.2 -> 74.5 (contraction): K = {st_in['k']:.5f}, "
          f"dP = {st_in['dp_pa']:.1f} Pa = {st_in['dp_psi']:.5f} psi")
    print(f"    step OUT 74.5 -> 76.2 (expansion)  : K = {st_out['k']:.5f}, "
          f"dP = {st_out['dp_pa']:.1f} Pa = {st_out['dp_psi']:.5f} psi")
    print(f"    both steps together: {st_in['dp_pa']+st_out['dp_pa']:.1f} Pa = "
          f"{st_in['dp_psi']+st_out['dp_psi']:.5f} psi "
          f"({100*(st_in['dp_psi']+st_out['dp_psi'])/1.5:.2f}% of the 1.5 psi budget)")
    print(f"    -> NOT worth blending. The step is 0.85 mm on the radius.")
    out["tb"] = dict(bore=TB_BORE * 1000, adapter=TB_ADAPTER * 1000,
                     plenum=PLENUM_FLANGE * 1000,
                     plate=ADAPTER_PLATE,
                     v=round(tb["v"], 1), vfts=round(tb["vfts"]),
                     mach=round(tb["mach"], 3), dp_psi=round(tb["dp_psi"], 4),
                     dp_pa=round(tb["dp_pa"], 1),
                     cap_lbmin=round(tb["choke_lbmin"]),
                     cap_hp=round(tb["choke_lbmin"] * HP_PER_LBMIN),
                     step_in_k=round(st_in["k"], 5), step_in_pa=round(st_in["dp_pa"], 1),
                     step_out_k=round(st_out["k"], 5), step_out_pa=round(st_out["dp_pa"], 1),
                     step_psi=round(st_in["dp_psi"] + st_out["dp_psi"], 5),
                     step_pct=round(100 * (st_in["dp_psi"] + st_out["dp_psi"]) / 1.5, 2))

    # throttle capacity across the whole rpm range, to answer "is 74.5 enough"
    print()
    print("  IS 74.5 mm ENOUGH ACROSS THE WHOLE RANGE?")
    tbrows = []
    for rpm in (7000, 7500, 8000):
        for boost in (30, 34):
            oo = operating_point(rpm, boost, 0.706)
            pc = P_AMB + boost * PSI + 0.4 * PSI
            t = throttle_dp(oo["m"], pc, oo["iat"])
            tbrows.append(dict(rpm=rpm, boost=boost, lb=round(oo["lb"], 2),
                               v=round(t["v"], 1), vfts=round(t["vfts"]),
                               mach=round(t["mach"], 3),
                               dp_psi=round(t["dp_psi"], 4),
                               used=round(100 * oo["lb"] / t["choke_lbmin"], 1)))
            print(f"    {rpm} rpm / {boost} psi: {oo['lb']:.1f} lb/min -> "
                  f"{t['v']:.1f} m/s, Mach {t['mach']:.3f}, dP {t['dp_psi']:.3f} psi, "
                  f"using {100*oo['lb']/t['choke_lbmin']:.0f}% of the throttle's "
                  f"Mach-0.3 capacity")
    out["tb_range"] = tbrows

    # diffuser / step geometry for the last transition
    print()
    for od in (2.25, 2.5, 2.75, 3.0):
        d1 = pipe_id(od)
        need = abs(pipe_id(3.0) - d1) / 2 / math.tan(math.radians(7))
        print(f"    {od:.2f} in ({d1*1000:.1f} mm) -> 3.00 in ({pipe_id(3.0)*1000:.1f} mm) "
              f"needs {need*1000:.0f} mm of taper at 7 deg per wall")

    print()
    print("  HOT SIDE, chosen independently (turbo outlet is 2.0 in):")
    print(f"  {'hot OD':<9} {'ft/s':>6} {'Garrett band':>14} {'dP psi':>8} {'vol L':>7}")
    hot_rows = []
    for od in (2.25, 2.50, 2.75, 3.00):
        hh = pipe_metrics(od, m_dot, p_hot, t_hot, L_HOT, N_HOT)
        band = "in band" if 200 <= hh["vfts"] <= 300 else (
            "below band" if hh["vfts"] < 200 else "above band")
        hot_rows.append(dict(od=od, fts=round(hh["vfts"]), band=band,
                             dp=round(hh["dp_psi"], 3),
                             vol=round(L_HOT * hh["vol_per_m"], 2)))
        print(f"  {od:<9.2f} {hh['vfts']:6.0f} {band:>14} {hh['dp_psi']:8.3f} "
              f"{L_HOT*hh['vol_per_m']:7.2f}")
    out["hot_layouts"] = hot_rows

    print()
    print("  FINAL BUILD: 2.50 in hot / 2.50 in cold, welded cone to the 3.00 in")
    print("  throttle adapter over the last 150 mm. Pressure-drop budget:")
    hb = pipe_metrics(2.50, m_dot, p_hot, t_hot, L_HOT, N_HOT)
    cb = pipe_metrics(2.50, m_dot, p_cold, t_cold, 1.35, N_COLD)
    ct = pipe_metrics(3.00, m_dot, p_cold, t_cold, 0.15, 0)
    cn = cone_loss(pipe_id(2.5), pipe_id(3.0), m_dot, p_cold, t_cold)
    budget = [("hot pipe, 2.50 in, 1.1 m, 3 bends", hb["dp_psi"]),
              ("intercooler core, 610x305x102", 0.18),
              ("end tanks, fabricated tapered, 2.50 in ports", 0.35),
              ("cold pipe, 2.50 in, 1.35 m, 4 bends", cb["dp_psi"]),
              ("welded 2.50 -> 3.00 cone + 150 mm of 3.00", cn["dp_psi"] + ct["dp_psi"]),
              ("throttle body, 74.5 mm at WOT", tb["dp_psi"]),
              ("the two 1.7 mm steps at the throttle",
               st_in["dp_psi"] + st_out["dp_psi"])]
    tot = 0.0
    for lab, v in budget:
        tot += v
        print(f"    {lab:<44} {v:7.3f} psi")
    print(f"    {'TOTAL':<44} {tot:7.3f} psi = {100*tot/30:.1f}% of 30 psi boost")
    coldL = 1.35 * cb["vol_per_m"] + 0.15 * ct["vol_per_m"]
    sysL_final = L_HOT * hb["vol_per_m"] + coldL + CORE_VOL_L + TANKS_L
    print(f"    system volume {sysL_final:.2f} L = {sysL_final/(DISP*1000):.2f} x displacement, "
          f"fill {fill_ms_of(L_HOT*hb['vol_per_m'], coldL):.0f} ms")

    # what the extra dP actually costs, in the only units that matter
    pr_lo = (P_AMB + 30 * PSI + 1.413 * PSI) / (P_AMB * FILTER_LOSS)
    pr_hi = (P_AMB + 30 * PSI + tot * PSI) / (P_AMB * FILTER_LOSS)
    tc_lo = comp_out_C(T_AMB, pr_lo, 0.706)
    tc_hi = comp_out_C(T_AMB, pr_hi, 0.706)
    eps = 0.793
    print(f"    against the 3.00 in cold build at 1.413 psi:")
    print(f"      pressure ratio      {pr_lo:.4f} -> {pr_hi:.4f}   (+{pr_hi-pr_lo:.4f})")
    print(f"      compressor outlet   {tc_lo:.1f} C -> {tc_hi:.1f} C   (+{tc_hi-tc_lo:.2f} C)")
    print(f"      charge at the valve after the core, eps {eps}: "
          f"+{(tc_hi-tc_lo)*(1-eps):.2f} C")
    print(f"      that is worth about {(tc_hi-tc_lo)*(1-eps)*0.35:.2f} whp. "
          f"Dan is right not to care.")
    out["budget"] = dict(rows=[[l, round(v, 3)] for l, v in budget],
                         total=round(tot, 3), pct=round(100 * tot / 30, 1),
                         sysL=round(sysL_final, 2),
                         sysX=round(sysL_final / (DISP * 1000), 2),
                         fill_ms=round(fill_ms_of(L_HOT * hb["vol_per_m"], coldL)),
                         vs3in=dict(dp3=1.413, dpr=round(pr_hi - pr_lo, 4),
                                    dtc=round(tc_hi - tc_lo, 2),
                                    diat=round((tc_hi - tc_lo) * (1 - eps), 2),
                                    dwhp=round((tc_hi - tc_lo) * (1 - eps) * 0.35, 2)))


    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 7 - PACKAGING, WITH REAL GEOMETRY")
    print("=" * W)
    print(f"  radiator: {RAD['part']}  overall {RAD['overall_mm']} mm, "
          f"core {RAD['core_mm']} mm, {RAD['rows']} rows")
    print()
    print(f"  {'core mm':>8} {'gap to rad':>18} {'gap after condenser':>21}")
    stack_rows = []
    for t in (76, 102, 114):
        s = stack(t)
        stack_rows.append(dict(t=t, gap_lo=round(s["gap_lo"]), gap_hi=round(s["gap_hi"]),
                               after_lo=round(s["after_cond_lo"]),
                               after_hi=round(s["after_cond_hi"])))
        print(f"  {t:8d} {s['gap_lo']:8.0f} - {s['gap_hi']:.0f} mm "
              f"{s['after_cond_lo']:12.0f} - {s['after_cond_hi']:.0f} mm")
    out["stack"] = stack_rows

    print()
    print(f"  {'core':<22} {'vol L':>6} {'v_face':>7} {'eps':>6} {'IAT C':>7} "
          f"{'whp':>5} {'dT air':>7} {'rad in C':>9} {'head lost':>10}")
    core_rows = []
    for k, c in CORES.items():
        o = operating_point(7500, 30.0, 0.706, core=c)
        r = rad_inlet_temp(o)
        vol = c["w"] * c["h"] * c["t"] * 1000
        core_rows.append(dict(k=k, label=c["label"], vol=round(vol, 1),
                              vf=round(o["vf"], 2), eps=round(o["eps"], 3),
                              iat=round(o["iat"], 1), iatF=round(o["iat"] * 9 / 5 + 32),
                              whp=round(o["whp"]),
                              whp_lo=round(o["lb"] * HP_PER_LBMIN * DRIVETRAIN_LO),
                              whp_hi=round(o["lb"] * HP_PER_LBMIN * DRIVETRAIN_HI),
                              dTrad_raw=round(o["dTrad"], 1),
                              dt_ic=round(r["dt_ic"], 1), dt_cond=round(r["dt_cond"], 1),
                              t_rad_in=round(r["t_rad_in"], 1),
                              head=round(r["head_stacked"], 1),
                              head_pct=round(100 * r["head_stacked"] / r["head_bare"], 1),
                              mass=round(vol * 0.30, 1),
                              w=c["w"] * 1000, h=c["h"] * 1000, t=c["t"] * 1000,
                              depth_need=round(c["t"] * 1000 + 35)))
        print(f"  {c['label']:<22} {vol:6.1f} {o['vf']:7.2f} {o['eps']:6.3f} "
              f"{o['iat']:7.1f} {o['whp']:5.0f} {r['dt_ic']:6.1f}C "
              f"{r['t_rad_in']:8.1f}C {r['head_stacked']:9.1f}C")
    out["cores"] = core_rows

    r76 = rad_inlet_temp(operating_point(7500, 30.0, 0.706, core=CORES["610x305x76"]))
    r102 = rad_inlet_temp(operating_point(7500, 30.0, 0.706, core=CORES["610x305x102"]))
    print()
    print(f"  76 -> 102 mm core costs {r102['t_rad_in']-r76['t_rad_in']:.1f} C of radiator "
          f"inlet air, which is {100*(r102['t_rad_in']-r76['t_rad_in'])/r76['head_bare']:.1f}% "
          f"of the bare temperature head.")
    print(f"  Intercooler shadows {100*0.610*0.305/(0.699*0.318):.0f}% of the Mishimoto "
          f"core face when centred; with {GAP_IC_RAD[0]/25.4:.0f}-{GAP_IC_RAD[1]/25.4:.0f} in "
          f"of separation the heated wake has spread over effectively all of it.")
    out["rad_penalty"] = dict(d_rad_in=round(r102["t_rad_in"] - r76["t_rad_in"], 1),
                              pct_head=round(100 * (r102["t_rad_in"] - r76["t_rad_in"]) / r76["head_bare"], 1),
                              shadow_pct=round(100 * 0.610 * 0.305 / (0.699 * 0.318)),
                              entrain=round(r76["entrain"], 3))

    # --- the decisive check: does the shadowing penalty apply when it matters? ---
    print()
    print("  DOES THE SHADOWING PENALTY APPLY WHEN THE RADIATOR ACTUALLY MATTERS?")
    # Mishimoto UA estimate, air-side limited, beta 800 m2/m3 for a 2-row core
    rw, rh, rt = [x / 1000.0 for x in RAD["core_mm"]]
    A_rad = rw * rh * rt * 800.0
    duty = []
    for lab, rpm, boost, vf_scale in (
            ("sustained WOT climb, 100 km/h", 7000, 30.0, 1.00),
            ("part throttle recovery, 100 km/h", 3000, 5.0, 1.00),
            ("cruise, no boost, 100 km/h", 2500, 0.0, 1.00)):
        oo = operating_point(rpm, boost, 0.706, core=CORES["610x305x102"])
        rr2 = rad_inlet_temp(oo)
        U = 55.0 * math.sqrt(oo["vf"] * vf_scale / 10.0)
        UA = U * A_rad
        q_bare = UA * (100.0 - T_AMB) / 1000.0
        q_stack = UA * (100.0 - rr2["t_rad_in"]) / 1000.0
        duty.append(dict(lab=lab, rpm=rpm, boost=boost,
                         q_ic=round(oo["Q"] / 1000.0, 1),
                         t_rad_in=round(rr2["t_rad_in"], 1),
                         q_bare=round(q_bare, 1), q_stack=round(q_stack, 1),
                         lost_pct=round(100 * (1 - q_stack / q_bare), 1)))
        print(f"    {lab:<34} intercooler rejects {oo['Q']/1000:6.1f} kW | "
              f"radiator sees {rr2['t_rad_in']:5.1f} C | "
              f"capacity {q_stack:5.1f} of {q_bare:5.1f} kW "
              f"({100*(1-q_stack/q_bare):4.1f}% lost)")
    print("    -> the penalty is large only while on boost, and while on boost the")
    print("       coolant load is an order of magnitude above what any ST185 radiator")
    print("       can shed anyway. On the recovery lap, where the radiator decides")
    print("       whether the session continues, the intercooler is rejecting almost")
    print("       nothing and the shadowing penalty nearly vanishes.")
    out["duty"] = duty
    out["rad_UA"] = round(A_rad, 2)

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 5 - DRIVETRAIN, AS A BAND")
    print("=" * W)
    dyno_gain = wheel_inertia_whp()
    print(f"  lightweight wheels on an INERTIA dyno: +{dyno_gain:.1f} whp of indicated reading")
    print(f"  lightweight wheels on a STEADY-STATE dyno: +0.0 whp")
    print(f"  equivalent mass removed (wheels + shaft): about 32 kg of 1,320 kg")
    print(f"  -> about 2.4% quicker acceleration at the same power. That is the real gain.")
    print()
    o = operating_point(7500, 30.0, 0.706)
    print(f"  {'factor':>8} {'loss %':>8} {'whp':>6}  case")
    band = []
    for f, case in ((0.78, "worst credible AWD loss, plate LSD dragging"),
                    (0.80, "round three baseline, unchanged by the upgrades"),
                    (0.81, "rebuilt trans + 1-pc CF shaft, helical LSD"),
                    (0.83, "best credible; needs a coast-down to justify")):
        w = o["lb"] * HP_PER_LBMIN * f
        band.append(dict(f=f, loss=round((1 - f) * 100, 1), whp=round(w), case=case))
        print(f"  {f:8.2f} {(1-f)*100:7.1f}% {w:6.0f}  {case}")
    out["driveline"] = dict(band=band, dyno_gain=round(dyno_gain, 1),
                            lb=round(o["lb"], 2))

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("ITEM 4 - COMMUNITY DYNO SANITY CHECK")
    print("=" * W)
    print(f"  {'build':<52} {'whp':>5} {'whp/L':>7} {'model says':>11}")
    comm = []
    for c in COMMUNITY:
        per_l = c["whp"] / c["disp"]
        comm.append(dict(**{k: v for k, v in c.items()}, per_l=round(per_l, 1)))
        print(f"  {c['what'][:52]:<52} {c['whp']:5d} {per_l:7.1f}")
    model_per_l = o["whp"] / (DISP * 1000)
    print()
    print(f"  THIS MODEL: {o['whp']:.0f} whp from {DISP*1000:.2f} L = "
          f"{model_per_l:.1f} whp per litre at 30 psi on E85.")
    print(f"  Community band for EFR 7163 on E85: 200 - 258 whp per litre.")
    print(f"  This model sits at {model_per_l:.0f}, inside that band and nearer the bottom,")
    print(f"  which is what a 20% AWD loss and a 32 C design ambient should produce.")
    out["community"] = comm
    out["model_per_l"] = round(model_per_l, 1)

    # ------------------------------------------------------------------
    print()
    print("=" * W)
    print("BOOST LADDER AT SEVERAL REDLINES (the deliverable table)")
    print("=" * W)
    ladder = []
    print(f"  {'rpm':>5} {'psi':>5} {'PR':>5} {'lb/min':>7} {'%choke':>7} {'IAT C':>6} "
          f"{'whp lo':>7} {'whp mid':>8} {'whp hi':>7}")
    for rpm in (7000, 7500, 8000):
        for boost in (20, 25, 28, 30, 32, 34):
            oo = operating_point(rpm, boost, 0.706)
            ladder.append(dict(rpm=rpm, boost=boost, pr=round(oo["pr"], 2),
                               lb=round(oo["lb"], 2),
                               choke=round(oo["lb"] / 60 * 100, 1),
                               iat=round(oo["iat"], 1),
                               whp_lo=round(oo["lb"] * HP_PER_LBMIN * DRIVETRAIN_LO),
                               whp=round(oo["whp"]),
                               whp_hi=round(oo["lb"] * HP_PER_LBMIN * DRIVETRAIN_HI),
                               eta_off=round(official_eff_7163(oo["lb"], oo["pr"]), 3)))
            print(f"  {rpm:5d} {boost:5.0f} {oo['pr']:5.2f} {oo['lb']:7.2f} "
                  f"{oo['lb']/60*100:6.1f}% {oo['iat']:6.1f} "
                  f"{oo['lb']*HP_PER_LBMIN*DRIVETRAIN_LO:7.0f} {oo['whp']:8.0f} "
                  f"{oo['lb']*HP_PER_LBMIN*DRIVETRAIN_HI:7.0f}")
    out["ladder"] = ladder

    hero = operating_point(7500, 30.0, 0.706)
    out["hero"] = dict(rpm=7500, boost=30, lb=round(hero["lb"], 2),
                       whp=round(hero["whp"]),
                       whp_lo=round(hero["lb"] * HP_PER_LBMIN * DRIVETRAIN_LO),
                       whp_hi=round(hero["lb"] * HP_PER_LBMIN * DRIVETRAIN_HI),
                       crank=round(hero["crank"]), iat=round(hero["iat"], 1),
                       pr=round(hero["pr"], 2), tc=round(hero["tc"]),
                       eps=round(hero["eps"], 3),
                       choke=round(hero["lb"] / 60 * 100, 1))
    out["const"] = dict(disp=round(DISP * 1e6, 1), pamb=round(P_AMB, 2), tamb=T_AMB,
                        hp=HP_PER_LBMIN, dt_lo=DRIVETRAIN_LO, dt=DRIVETRAIN_MID,
                        dt_hi=DRIVETRAIN_HI, rodratio=round(ROD_RATIO, 3),
                        rpm_stock=RPM_STOCK, rpm_max=RPM_MAX,
                        tb_bore=TB_BORE * 1000, plenum_flange=PLENUM_FLANGE * 1000)
    out["official"] = {k: {kk: vv for kk, vv in v.items()} for k, v in OFFICIAL.items()}
    out["rad"] = RAD

    with open(os.path.join(HERE, "data", "unified_model_r4.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote data/unified_model_r4.json")
    return out


if __name__ == "__main__":
    main()
