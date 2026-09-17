"""Round five data block. Emits r5_data.js.
Two questions only: charge pipe diameter, and core dimensions as a function of
the (still unmeasured) bumper aperture width."""
import math, json, importlib.util

spec = importlib.util.spec_from_file_location("um", "unified_model_r4.py")
um = importlib.util.module_from_spec(spec); spec.loader.exec_module(um)

R, PSI = 287.05, 6.89476
P_AMB, T_AMB = 93.87, 32.0
RPM, BOOST, ETA = 7500, 30.0, 0.706
PR_CEIL = 3.6
WALL = 0.065                      # inch
L_HOT, N_HOT = 1.10, 3            # metres, 90 deg bends
L_COLD, N_COLD = 1.50, 4
CORE_DP = 1.5                     # psi, core + end tanks at the design point
BASE = dict(w=0.610, h=0.305, t=0.102, label="610x305x102")

op0 = um.operating_point(RPM, BOOST, ETA, core=BASE, dp_psi=CORE_DP)
MDOT = op0["m"]
P_MAN = P_AMB + BOOST * PSI

def pipe_case(od, mdot, t_hot, t_cold, p_man):
    idin = od - 2 * WALL
    d = idin * 0.0254
    A = math.pi * d * d / 4
    rho_h = (p_man + CORE_DP * PSI) * 1000 / (R * (t_hot + 273.15))
    rho_c = p_man * 1000 / (R * (t_cold + 273.15))
    vh, vc = mdot / (rho_h * A), mdot / (rho_c * A)
    Kh = 0.02 * L_HOT / d + N_HOT * 0.25
    Kc = 0.02 * L_COLD / d + N_COLD * 0.25
    dph = Kh * 0.5 * rho_h * vh ** 2 / 6894.76
    dpc = Kc * 0.5 * rho_c * vc ** 2 / 6894.76
    volh, volc = A * L_HOT * 1000, A * L_COLD * 1000
    return dict(od=od, idin=idin, id_mm=d * 1000, A=A,
                vh=vh, hot_fts=vh * 3.28084, vc=vc, cold_fts=vc * 3.28084,
                dph=dph, dpc=dpc, dp=dph + dpc, volh=volh, volc=volc,
                vol=volh + volc, rho_h=rho_h, rho_c=rho_c)

# core + tank internal charge volume, held constant across pipe sizes
CORE_L = 0.610 * 0.305 * 0.102 * 1000 * 0.27      # ~27% of envelope is charge passage
TANK_L = 2 * 1.15
FIXED_L = CORE_L + TANK_L

pipes = []
for od in (2.25, 2.50, 2.75, 3.00):
    c = pipe_case(od, MDOT, op0["tc"], op0["iat"], P_MAN)
    sysdp = c["dp"] + CORE_DP
    op = um.operating_point(RPM, BOOST, ETA, core=BASE, dp_psi=sysdp)
    sysL = c["vol"] + FIXED_L
    # mass that must be pushed in to take the system from atmospheric to boost
    rho_lo = P_AMB * 1000 / (R * (60 + 273.15))
    m_hi = (c["volh"] / 1000) * c["rho_h"] + ((c["volc"] + FIXED_L) / 1000) * c["rho_c"]
    m_lo = (sysL / 1000) * rho_lo
    fill_ms = (m_hi - m_lo) / (0.45 * MDOT) * 1000
    # highest boost the turbo can still hold with this plumbing loss
    lo, hi = 20.0, 40.0
    for _ in range(60):
        b = (lo + hi) / 2
        probe = um.operating_point(RPM, b, ETA, core=BASE, dp_psi=CORE_DP)
        sd = c["dp"] * (probe["m"] / MDOT) ** 2 + CORE_DP
        if um.operating_point(RPM, b, ETA, core=BASE, dp_psi=sd)["pr"] < PR_CEIL:
            lo = b
        else:
            hi = b
    cap = um.operating_point(RPM, lo, ETA, core=BASE,
                             dp_psi=c["dp"] * (probe["m"] / MDOT) ** 2 + CORE_DP)
    pipes.append(dict(od=od, id_in=round(c["idin"], 3), id_mm=round(c["id_mm"], 1),
                      hot_ms=round(c["vh"], 1), hot_fts=round(c["hot_fts"]),
                      cold_ms=round(c["vc"], 1), cold_fts=round(c["cold_fts"]),
                      dp_hot=round(c["dph"], 2), dp_cold=round(c["dpc"], 2),
                      dp=round(c["dp"], 2), sysdp=round(sysdp, 2),
                      vol_hot=round(c["volh"], 2), vol_cold=round(c["volc"], 2),
                      vol=round(c["vol"], 2), sysL=round(sysL, 1),
                      fill_ms=round(fill_ms), pr=round(op["pr"], 3),
                      pr_margin=round(PR_CEIL - op["pr"], 3),
                      iat=round(op["iat"], 1), whp=round(op["whp"]),
                      boost_cap=round(lo, 1), whp_cap=round(cap["whp"])))

# ---------------------------------------------------------------- cores
def core_case(w, h, t):
    c = dict(w=w / 1000, h=h / 1000, t=t / 1000, label="%dx%dx%d" % (w, h, t))
    o = um.operating_point(RPM, BOOST, ETA, core=c, dp_psi=1.5 + 1.34)
    Q = o["Q"]
    dt_ic = Q / (o["mCold"] * 1005.0) / 1.18          # jet entrainment over the gap
    return dict(w=w, h=h, t=t, vol=round(w * h * t / 1e6, 1), vf=round(o["vf"], 2),
                eps=round(o["eps"], 3), iat=round(o["iat"], 1),
                iatF=round(o["iat"] * 9 / 5 + 32), whp=round(o["whp"]),
                whp_lo=round(o["lb"] * 9.5 * 0.78), whp_hi=round(o["lb"] * 10.5 * 0.82),
                mass=round(w * h * t / 1e6 * 0.30, 1),
                t_rad=round(T_AMB + dt_ic + 3.7, 1), depth_need=t + 35)

sweep = [core_case(w, 305, t) for w in (420, 440, 490, 540, 590, 640, 685, 711)
         for t in (76, 102, 114)]

# aperture bands -> core width = aperture - 20 mm, taken at the low end of the band
BANDS = [(0, 459, 420, 114), (460, 509, 440, 102), (510, 559, 490, 102),
         (560, 609, 540, 102), (610, 659, 590, 102), (660, 709, 640, 102),
         (710, 9999, 685, 102)]
aperture = []
for lo, hi, w, t in BANDS:
    c = core_case(w, 305, t)
    aperture.append(dict(lo=lo, hi=hi, band=("under %d" % (hi + 1)) if lo == 0 else
                         ("%d or more" % lo if hi > 900 else "%d to %d" % (lo, hi)),
                         **c))

heights = [core_case(590, h, 102) for h in (255, 280, 305, 330, 355)]
depths = [core_case(590, 305, t) for t in (64, 76, 89, 102, 114, 127)]

# exhaust valve windows, unwrapped into drawable segments
raw = {1: (135.0, 399.0), 2: (675.0, 219.0), 3: (315.0, 579.0), 4: (495.0, 39.0)}
win = {}
for k, (a, b) in raw.items():
    win[str(k)] = [[a, b]] if b > a else [[a, 720.0], [0.0, b]]

data = dict(
    design=dict(rpm=RPM, boost=BOOST, eta=ETA, pr_ceiling=PR_CEIL,
                mdot=round(MDOT, 4), lb=round(op0["lb"], 1), tc=round(op0["tc"], 1),
                iat=round(op0["iat"], 1), p_man=round(P_MAN, 1),
                l_hot=L_HOT, n_hot=N_HOT, l_cold=L_COLD, n_cold=N_COLD,
                wall=WALL, core_dp=CORE_DP, fixed_L=round(FIXED_L, 1)),
    pipes=pipes, sweep=sweep, aperture=aperture, heights=heights, depths=depths,
    win=win)

open("r5_data.js", "w").write("var R5=" + json.dumps(data, separators=(",", ":")) + ";\n")
print("pipes")
for p in pipes:
    print("  %.2f in  ID %.1f  hot %d ft/s  cold %d ft/s  dP %.2f  vol %.2f L  "
          "sys %.1f L  fill %d ms  PR %.3f (margin %.3f)  boost cap %.1f psi"
          % (p["od"], p["id_mm"], p["hot_fts"], p["cold_fts"], p["dp"], p["vol"],
             p["sysL"], p["fill_ms"], p["pr"], p["pr_margin"], p["boost_cap"]))
print("aperture")
for a in aperture:
    print("  %-14s -> %d x %d x %d   %.1f L  eps %.3f  IAT %.1f C  %d whp  rad air %.1f C"
          % (a["band"], a["w"], a["h"], a["t"], a["vol"], a["eps"], a["iat"],
             a["whp"], a["t_rad"]))
