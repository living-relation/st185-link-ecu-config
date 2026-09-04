"""
ROUND SIX - two items from the original brief that were dropped during the r3-r5 rewrites.

  A. Oil cooler placement: behind the intercooler, in front of it, or a corner / fender feed.
     Quantified against the same design point and the same constants as unified_model_r4.
  B. The CS bumper crash bar (1 x 1 in aluminium, across the front of the aperture) folded
     into the duct design rather than treated as an obstruction to remove.

Emits data/r6_data.js for the report charts.
"""
import math, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
R, CP, GAMMA, PSI = 287.05, 1005.0, 1.40, 6.89476
ALT_M, T_AMB = 640.0, 32.0
P_AMB = 101.325 * (1 - 2.25577e-5 * ALT_M) ** 5.25588
def C2K(c): return c + 273.15
def F(c): return c * 9 / 5 + 32

# ---- design point, taken from unified_model_r4 so the two agree ----
CORE_W, CORE_H, CORE_T = 0.610, 0.305, 0.102     # m
Q_IC   = 55.4e3        # W rejected by the intercooler, sustained WOT climb
IAT    = 68.3          # C, charge temp leaving the IC at the design point
TCOMP  = 216.0         # C, compressor outlet
RAD_UA = 9.21e3        # W/K, radiator UA from the model
Q_ENG  = 95.0e3        # W engine heat to coolant at sustained WOT (approx 0.9 x crank kW)

def eps_cf(ntu, cr):
    if cr <= 1e-6: return 1 - math.exp(-ntu)
    return 1 - math.exp((ntu ** 0.22 / cr) * (math.exp(-cr * ntu ** 0.78) - 1))

def ic_solve(t_in_air, vface=7.81):
    """IC effectiveness and outlet IAT for a given INLET AIR temperature to the core."""
    rho = P_AMB * 1000 / (R * C2K(t_in_air))
    mc = CORE_W * CORE_H * vface * rho
    m_charge = 50.0 / (2.20462 * 60)             # kg/s at the design point
    Cc, Ch = mc * CP, m_charge * CP
    cmin, cmax = min(Cc, Ch), max(Cc, Ch)
    A = CORE_W * CORE_H * CORE_T * 900.0
    U = 55.0 * math.sqrt(vface / 10.0)
    e = eps_cf(U * A / cmin, cmin / cmax) * cmin / Ch
    t_out = TCOMP - e * (TCOMP - t_in_air)
    return e, t_out, mc, m_charge * CP * (TCOMP - t_out)

print("=" * 74)
print("A. OIL COOLER PLACEMENT")
print("=" * 74)
eps0, iat0, m_cold, q0 = ic_solve(T_AMB)
print("baseline: IC breathing %.0f C -> eps %.3f, IAT %.1f C (%.0f F), Q %.1f kW"
      % (T_AMB, eps0, iat0, F(iat0), q0 / 1000))
print("ambient mass flow through the core face: %.2f kg/s" % m_cold)

# Chase Bays 10-row, ~250 x 190 mm core. Heat rejection at sustained load.
Q_OIL = 9.0e3
A_OIL = 0.250 * 0.190
print("\nChase Bays 10-row oil cooler: %.2f m2 face, rejecting ~%.1f kW sustained"
      % (A_OIL, Q_OIL / 1000))

rows = []

# --- OPTION A: behind the intercooler, inside its shadow -------------------
dT_ic = Q_IC / (m_cold * CP)                    # air heated by the IC
m_oil_A = m_cold * (A_OIL / (CORE_W * CORE_H))  # share of the IC's exit flow it intercepts
dT_oil_A = Q_OIL / (m_oil_A * CP)
t_rad_A = T_AMB + dT_ic + Q_OIL / (m_cold * CP)
print("\n--- OPTION A: BEHIND the intercooler (in its shadow) ---")
print("  charge-air penalty                 : none (it is downstream of the charge path)")
print("  air entering the oil cooler        : %.1f C (already heated %.1f C by the IC)"
      % (T_AMB + dT_ic, dT_ic))
print("  oil cooler's own rise              : +%.1f C over its own frontal area" % dT_oil_A)
print("  radiator inlet air                 : %.1f C  (+%.1f C vs a clean corner feed)"
      % (t_rad_A, t_rad_A - (T_AMB + dT_ic)))
# coolant temp consequence
dT_avail_A = 95.0 - t_rad_A
dT_avail_C = 95.0 - (T_AMB + dT_ic)
print("  driving dT for 95 C coolant        : %.1f K  (vs %.1f K) = %.0f%% less cooling capacity"
      % (dT_avail_A, dT_avail_C, 100 * (1 - dT_avail_A / dT_avail_C)))
print("  oil cooler effectiveness penalty   : it sees %.0f C air, not %.0f C -> roughly"
      % (T_AMB + dT_ic, T_AMB))
oil_eff_pen = (120 - (T_AMB + dT_ic)) / (120 - T_AMB)
print("                                       %.0f%% of the oil-side dT it would have in a corner"
      % (100 * oil_eff_pen))
rows.append(dict(opt="A. Behind the IC", charge=0.0, rad=t_rad_A - (T_AMB + dT_ic),
                 oil_eff=100 * oil_eff_pen, verdict="works, but costs the radiator"))

# --- OPTION B: in front of / stacked with the intercooler ------------------
dT_pre = Q_OIL / (m_cold * CP)
epsB, iatB, _, qB = ic_solve(T_AMB + dT_pre)
print("\n--- OPTION B: IN FRONT OF / stacked with the intercooler ---")
print("  IC now breathes                    : %.1f C instead of %.1f C" % (T_AMB + dT_pre, T_AMB))
print("  charge-air penalty                 : IAT %.1f C -> %.1f C  = +%.1f C"
      % (iat0, iatB, iatB - iat0))
print("  radiator inlet air                 : %.1f C  (+%.1f C)"
      % (T_AMB + dT_pre + Q_IC / (m_cold * CP), dT_pre))
print("  ** worst option: it penalises the charge AND the radiator **")
rows.append(dict(opt="B. In front of the IC", charge=iatB - iat0, rad=dT_pre,
                 oil_eff=100.0, verdict="worst - penalises both"))

# --- OPTION C: corner or fender well, own feed ----------------------------
print("\n--- OPTION C: front corner or fender well, own feed, outside the IC footprint ---")
print("  charge-air penalty                 : none")
print("  radiator penalty                   : none")
print("  oil cooler inlet air               : %.0f C ambient - full effectiveness" % T_AMB)
print("  cost                               : ~1.5 m more -10AN line each way, a duct, a mount")
rows.append(dict(opt="C. Corner / fender well", charge=0.0, rad=0.0, oil_eff=100.0,
                 verdict="RECOMMENDED"))

print("\n  >>> RECOMMENDATION: OPTION C.")
print("  >>> Option B costs %.1f C of charge temperature, which is worth roughly %.0f whp."
      % (iatB - iat0, (iatB - iat0) * 0.55))
print("  >>> Option A costs the radiator %.1f K of driving dT at exactly the moment you need it"
      % (t_rad_A - (T_AMB + dT_ic)))
print("  >>> (sustained climb). Option C costs about $80 of line and a weekend of ducting.")
print("  >>> If C is impossible, take A over B - never put it in the charge cooler's inlet air.")

# ---------------------------------------------------------------------------
print("\n" + "=" * 74)
print("B. THE CS CRASH BAR IN THE DUCT DESIGN")
print("=" * 74)
BAR = 0.0254                                    # 1 in square section
APERTURE_W, APERTURE_H = 0.700, 0.230           # typical CS lower aperture, measured range
mouth_area = APERTURE_W * APERTURE_H
blocked = BAR * APERTURE_W
print("aperture assumed %.0f x %.0f mm = %.4f m2 (Dan reports 1.5x the required clearance)"
      % (APERTURE_W * 1000, APERTURE_H * 1000, mouth_area))
print("bar: %.1f mm square, spanning the full width, %.4f m2 of projected area"
      % (BAR * 1000, blocked))
print("geometric blockage: %.1f%% of the mouth" % (100 * blocked / mouth_area))

# A square bar is a bluff body: drag coefficient ~2.05 vs ~1.2 for a round tube of the
# same width, and it sheds a wake roughly 2-3 diameters wide.
CD_SQ, CD_ROUND, CD_FAIR = 2.05, 1.20, 0.45
wake_w = 2.5 * BAR
print("\nwake: a square section sheds a wake ~2.5x its height = %.0f mm tall," % (wake_w * 1000))
print("      so the EFFECTIVE blockage is nearer %.1f%% of the mouth, not %.1f%%."
      % (100 * wake_w * APERTURE_W / mouth_area, 100 * blocked / mouth_area))
eff_block = wake_w * APERTURE_W / mouth_area
print("\nrecovered face velocity if the bar is faired vs left bare:")
for cd, lab in [(CD_SQ, "bare square bar (as delivered)"),
                (CD_ROUND, "corners radiused ~6 mm"),
                (CD_FAIR, "teardrop fairing bonded on")]:
    # momentum loss through the mouth scales with cd * blockage
    loss = cd * (blocked / mouth_area)
    v_ratio = math.sqrt(max(0.05, 1 - loss))
    e, t, _, _ = ic_solve(T_AMB, vface=7.81 * v_ratio)
    print("  %-32s Cd %.2f  face vel x%.3f  IAT %.1f C  (%+.1f C)"
          % (lab, cd, v_ratio, t, t - iat0))

print("""
DUCT DESIGN RULES WITH THE BAR IN PLACE
  1. Do NOT remove it. It is the CS bumper's mounting structure and it is 1 in of aluminium
     in front of your only radiator. Removing it to gain %.0f%% mouth area is a bad trade.
  2. Put the bar OUTSIDE the duct mouth, not inside it. Start the duct lip behind the bar so
     the bar sits in free stream and its wake has 40-60 mm to re-attach before the lip.
  3. If the bar has to cross the mouth, radius or fair it. A 6 mm radius on the leading
     corners takes Cd from 2.05 to about 1.2 for the cost of a file and an hour.
  4. Split the duct around it. If the bar crosses the mouth horizontally, treat the mouth as
     two openings and give each its own gentle diffuser - do not let one feed starve.
  5. Seal to the bar, not around it. Where the duct meets the bar, run the foam seal onto the
     bar face. A 25 mm gap along a 700 mm bar is 0.0175 m2 of bypass - %.0f%% of the mouth.
""" % (100 * blocked / mouth_area, 100 * (0.025 * 0.700) / mouth_area))

json.dump({"oil": rows,
           "bar": {"blockage_pct": round(100 * blocked / mouth_area, 1),
                   "eff_blockage_pct": round(100 * eff_block, 1),
                   "cd": {"square": CD_SQ, "radiused": CD_ROUND, "faired": CD_FAIR}},
           "dp": {"iat0": round(iat0, 1), "eps0": round(eps0, 3),
                  "dT_ic": round(dT_ic, 1), "t_rad_A": round(t_rad_A, 1),
                  "iatB": round(iatB, 1)}},
          open(os.path.join(HERE, "data", "r6_data.json"), "w"), indent=1)
print("wrote data/r6_data.json")
