# -*- coding: utf-8 -*-
"""Round five, part two: package combinations, turbo inlet, sensor placement numbers."""
import math, json, importlib.util
spec = importlib.util.spec_from_file_location("um", "unified_model_r4.py")
um = importlib.util.module_from_spec(spec); spec.loader.exec_module(um)

R, PSI = 287.05, 6.89476
P_AMB, T_AMB = 93.87, 32.0
RPM, BOOST, ETA, PR_CEIL = 7500, 30.0, 0.706, 3.6
WALL = 0.065
L_HOT, N_HOT, L_COLD, N_COLD = 1.10, 3, 1.50, 4
CORE_DP_REF = 1.5
BASE = dict(w=0.590, h=0.305, t=0.102, label="590x305x102")
op0 = um.operating_point(RPM, BOOST, ETA, core=BASE, dp_psi=CORE_DP_REF)
MDOT = op0["m"]; P_MAN = P_AMB + BOOST * PSI

def leg(od, L, nb, T, P, mdot):
    d = (od - 2 * WALL) * 0.0254
    A = math.pi * d * d / 4
    rho = P * 1000 / (R * (T + 273.15))
    v = mdot / (rho * A)
    dp = (0.02 * L / d + nb * 0.25) * 0.5 * rho * v * v / 6894.76
    return dict(v=v, fts=v * 3.28084, dp=dp, vol=A * L * 1000, rho=rho, A=A)

def core_dp(t_mm):
    """core+tank loss scales roughly with depth"""
    return CORE_DP_REF * (t_mm / 102.0) ** 0.6

def package(hot_od, cold_od, w, h, t, label, note):
    c = dict(w=w / 1000, h=h / 1000, t=t / 1000, label=label)
    cdp = core_dp(t)
    for _ in range(30):
        probe = um.operating_point(RPM, BOOST, ETA, core=c, dp_psi=cdp)
        hl = leg(hot_od, L_HOT, N_HOT, probe["tc"], P_MAN + cdp * PSI, probe["m"])
        cl = leg(cold_od, L_COLD, N_COLD, probe["iat"], P_MAN, probe["m"])
        new = cdp + 0  # core loss fixed; total below
        break
    total = hl["dp"] + cl["dp"] + cdp
    op = um.operating_point(RPM, BOOST, ETA, core=c, dp_psi=total)
    hl = leg(hot_od, L_HOT, N_HOT, op["tc"], P_MAN + cdp * PSI, op["m"])
    cl = leg(cold_od, L_COLD, N_COLD, op["iat"], P_MAN, op["m"])
    total = hl["dp"] + cl["dp"] + cdp
    op = um.operating_point(RPM, BOOST, ETA, core=c, dp_psi=total)
    fixed = w * h * t / 1e6 * 0.27 + 2.3
    sysL = hl["vol"] + cl["vol"] + fixed
    rho_lo = P_AMB * 1000 / (R * (60 + 273.15))
    m_hi = hl["vol"] / 1000 * hl["rho"] + (cl["vol"] + fixed) / 1000 * cl["rho"]
    fill = (m_hi - sysL / 1000 * rho_lo) / (0.45 * op["m"]) * 1000
    lo, hi = 20.0, 40.0
    for _ in range(50):
        b = (lo + hi) / 2
        pr = um.operating_point(RPM, b, ETA, core=c, dp_psi=total)["pr"]
        if pr < PR_CEIL: lo = b
        else: hi = b
    return dict(label=label, note=note, hot=hot_od, cold=cold_od, w=w, h=h, t=t,
                hot_fts=round(hl["fts"]), cold_fts=round(cl["fts"]),
                dp=round(total, 2), pr=round(op["pr"], 3), iat=round(op["iat"], 1),
                whp=round(op["whp"]), whp_lo=round(op["lb"] * 9.5 * 0.78),
                whp_hi=round(op["lb"] * 10.5 * 0.82),
                sysL=round(sysL, 1), fill=round(fill), cap=round(lo, 1))

PKG = [
 package(2.50, 2.50, 590, 305, 102, "Recommended package",
         "2.50 in both sides, 2.50 in ports, 102 mm core at the measured aperture."),
 package(2.50, 2.50, 440, 305, 102, "Narrow aperture",
         "Same pipework. Only the core width changes. This is what a 460 mm opening gets you."),
 package(2.50, 2.50, 685, 305, 102, "Wide aperture",
         "Same pipework, widest core worth building. Needs a 705 mm opening."),
 package(2.50, 2.50, 590, 305, 76, "Thin core",
         "The 3 in core. Cheapest, most available, and gives away 4 whp and 6 degrees."),
 package(2.50, 2.50, 590, 305, 114, "Thick core",
         "4.5 in core. Buys 2 whp and costs the radiator the same again. Not worth it."),
 package(2.25, 2.25, 590, 305, 102, "Small pipe",
         "Smallest fill time in the set, but no pressure-ratio margin left at 30 psi."),
 package(3.00, 3.00, 590, 305, 102, "Big pipe, 3 in ports",
         "Lowest loss, most volume, hardest route. Ports must be built to 3 in to match."),
 package(2.50, 3.00, 590, 305, 102, "Step up after the core",
         "The myth. Recovers nothing, adds volume. Shown only to price it."),
]
json.dump(PKG, open("/tmp/pkg.json", "w"))

# ---------------------------------------------------------------- turbo inlet
T_IN = 40.0
rho_in = P_AMB * 1000 / (R * (T_IN + 273.15))
a_snd = math.sqrt(1.4 * R * (T_IN + 273.15))
inlet = []
for od in (2.50, 3.00, 3.50, 4.00):
    d = (od - 2 * WALL) * 0.0254
    A = math.pi * d * d / 4
    v = MDOT / (rho_in * A)
    dp = (0.02 * 0.5 / d + 1 * 0.25) * 0.5 * rho_in * v * v / 6894.76
    inlet.append(dict(od=od, id_mm=round(d * 1000, 1), v=round(v, 1),
                      fts=round(v * 3.28084), mach=round(v / a_snd, 3),
                      dp=round(dp, 3)))
# what inlet depression costs
dep = []
for d_psi in (0.0, 0.25, 0.5, 1.0, 1.5):
    p_in = (P_AMB - d_psi * PSI)
    pr = (P_MAN + 2.84 * PSI) / (p_in * 0.97)
    tc = um.comp_out_C(T_AMB, pr, ETA)
    dep.append(dict(dp=d_psi, p_in=round(p_in, 1), pr=round(pr, 3),
                    tc=round(tc), over=pr > PR_CEIL))
cfm = MDOT / rho_in * 2118.88

extra = dict(pkg=PKG, inlet=inlet, dep=dep, cfm=round(cfm),
             lbmin=round(MDOT * 2.20462 * 60, 1), t_in=T_IN,
             mdot=round(MDOT, 4))
open("r5_extra.js", "w").write("var R5X=" + json.dumps(extra, separators=(",", ":")) + ";\n")

print("%-24s %-5s %-5s %-16s %5s %6s %5s %5s %5s %5s"
      % ("package", "hot", "cold", "core", "dP", "PR", "IAT", "whp", "fill", "cap"))
for p in PKG:
    print("%-24s %-5.2f %-5.2f %-16s %5.2f %6.3f %5.1f %5d %5d %5.1f"
          % (p["label"], p["hot"], p["cold"], "%dx%dx%d" % (p["w"], p["h"], p["t"]),
             p["dp"], p["pr"], p["iat"], p["whp"], p["fill"], p["cap"]))
print()
print("turbo inlet at %.1f lb/min, %d CFM, %.0f C:" % (extra["lbmin"], extra["cfm"], T_IN))
for i in inlet:
    print("  %.2f in (ID %.1f) -> %d ft/s, Mach %.3f, %.3f psi over 0.5 m + 1 bend"
          % (i["od"], i["id_mm"], i["fts"], i["mach"], i["dp"]))
print()
print("cost of inlet depression:")
for d in dep:
    print("  %.2f psi -> inlet %.1f kPa, PR %.3f, comp out %d C  %s"
          % (d["dp"], d["p_in"], d["pr"], d["tc"], "OVER THE 3.6 CEILING" if d["over"] else ""))
