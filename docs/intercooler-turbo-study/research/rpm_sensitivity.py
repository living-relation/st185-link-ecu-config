"""
5S-GTE ST185 - RPM SENSITIVITY AND TURBO RE-RANK
Independent rebuild of the round-one turbo model (data/turbo3.py).

Purpose: the round-one table reported every candidate as pressure-ratio-limited at
6650 rpm with 34-43 psi of boost. This script tests whether that is a real physical
result or an artefact of the volumetric-efficiency curve that was assumed.

All units SI internally. Output in the units Dan uses.
"""
import math, json

# ------------------------------------------------------------------ constants
R      = 287.05      # J/kg/K   specific gas constant, dry air
GAMMA  = 1.40
CP     = 1005.0
PSI    = 6.89476     # kPa per psi
LBMIN  = 2.20462*60  # kg/s -> lb/min

# ------------------------------------------------------------------ site
ALT_M   = 640.0                                        # 2,100 ft, Weaverville NC
P_AMB   = 101.325*(1-2.25577e-5*ALT_M)**5.25588        # kPa
T_AMB   = 32.0                                         # deg C design ambient
FILTER_LOSS = 0.97                                     # inlet restriction factor

# ------------------------------------------------------------------ engine
BORE   = 0.0875      # m
STROKE = 0.0910      # m
ROD    = 0.1380      # m   (stock 5S-FE / 3S-GTE rod, confirmed)
NCYL   = 4
DISP   = math.pi*(BORE/2)**2*STROKE*NCYL               # m^3  = 2.1888e-3
ROD_RATIO = ROD/STROKE                                 # 1.516

# intake valves: 3S-GTE, 2 per cylinder, 33.5 mm head diameter (Ferrea std listing)
IV_DIA = 0.0335
A_PISTON = math.pi*(BORE/2)**2
A_INTAKE = 2*math.pi*(IV_DIA/2)**2
CI       = 0.40      # inlet valve mean flow coefficient at useful lift (Taylor, typical 0.35-0.42)

DRIVETRAIN = 0.82    # AWD ST185 crank -> wheel
HP_PER_LBMIN = 10.0  # E85, good BSFC. Range 9.5-10.5.

def mean_piston_speed(rpm):
    return 2*STROKE*rpm/60.0

def sound_speed(tC):
    return math.sqrt(GAMMA*R*(tC+273.15))

def mach_index(rpm, iatC):
    """Taylor inlet Mach index Z = Ap*Up/(Ci*Ai*a). VE holds flat to about Z=0.5."""
    return A_PISTON*mean_piston_speed(rpm)/(CI*A_INTAKE*sound_speed(iatC))

# ---------------------------------------------------------------- VE models
def ve_round1(rpm):
    """The curve used in round one (data/turbo3.py). Peak 1.02 at 5500, steep falloff.
    Not derived from anything - it is the assumption under test."""
    x = (rpm-5500.0)/2600.0
    return max(0.70, min(1.03, 1.02 - 0.34*x*x - 0.06*max(0.0, x)))

def ve_mach(rpm, iatC=50.0, cam_peak_rpm=6200.0, emap_ratio=1.0):
    """Physically grounded: a broad cam/manifold breathing curve multiplied by the
    Taylor Mach-index rolloff, then a residual-gas penalty for exhaust backpressure.

    cam term  : shallow parabola, 3 percent loss per 2500 rpm off peak. A 4-valve
                head with aftermarket cams and an individual-runner-ish plenum is
                broad, not peaky.
    mach term : flat to Z=0.50, then falls 1.25 per unit Z (Taylor's measured trend:
                about 25 percent VE loss by Z=0.70).
    bp term   : residual dilution, 5 percent VE per unit of EMAP/IMAP above 1.0.
    """
    cam = 1.00 - 0.030*((rpm-cam_peak_rpm)/2500.0)**2
    Z   = mach_index(rpm, iatC)
    mach = 1.0 if Z <= 0.50 else max(0.45, 1.0 - 1.25*(Z-0.50))
    bp  = 1.0 - 0.05*max(0.0, emap_ratio-1.0)
    return max(0.40, cam*mach*bp)

# ---------------------------------------------------------------- flow
def flow_lbmin(rpm, boost_psi, ve, iatC=50.0):
    pman = P_AMB + boost_psi*PSI                       # kPa abs
    rho  = pman*1000.0/(R*(iatC+273.15))
    vdot = DISP*(rpm/2.0)/60.0*ve
    return vdot*rho*LBMIN, pman

def pressure_ratio(boost_psi):
    return (P_AMB + boost_psi*PSI)/(P_AMB*FILTER_LOSS)

def boost_for_flow(target_lbmin, rpm, vefn, iatC=50.0):
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = 0.5*(lo+hi)
        ve  = vefn(rpm)
        f,_ = flow_lbmin(rpm, mid, ve, iatC)
        if f < target_lbmin: lo = mid
        else: hi = mid
    return 0.5*(lo+hi)

def boost_for_pr(pr):
    return (pr*P_AMB*FILTER_LOSS - P_AMB)/PSI

# ---------------------------------------------------------------- candidates
# choke lb/min, usable PR ceiling, turbine wheel mm, turbine material, A/R, bearing, price
TURBOS = [
 ("EFR 7163 (current)",  60, 3.6, 63, "g-TiAl", 0.80, "ball",    2629, 71),
 ("EFR 7670",            67, 3.8, 70, "g-TiAl", 0.92, "ball",    2500, 76),
 ("EFR 8374",            79, 4.0, 74, "g-TiAl", 0.92, "ball",    2367, 83),
 ("EFR 9174",           105, 4.2, 74, "g-TiAl", 1.05, "ball",    3200, 91),
 ("Garrett G25-660",     64, 3.9, 54, "Inconel",0.92, "ball",    1750, 60),
 ("Garrett G25-770",     73, 4.1, 54, "Inconel",0.92, "ball",    1850, 62),
 ("Garrett G30-770",     77, 4.0, 55, "Inconel",1.01, "ball",    2050, 62),
 ("Garrett G30-900",     88, 4.2, 55, "Inconel",1.01, "ball",    2200, 65),
 ("Precision 6266 Gen2", 72, 3.9, 62, "Inconel",0.85, "journal", 1500, 62),
 ("Precision 6466 Gen2", 82, 4.1, 67, "Inconel",1.00, "journal", 1650, 64),
 ("Xona Rotor XR7169",   75, 4.2, 62, "Inconel",0.86, "ball",    2400, 62),
 ("Xona Rotor XR8267",   88, 4.3, 67, "Inconel",1.00, "ball",    2600, 67),
]
SPOOL = {"EFR 7163 (current)":4000, "EFR 7670":4825, "EFR 8374":5200, "EFR 9174":5446,
         "Garrett G25-660":4248, "Garrett G25-770":4307, "Garrett G30-770":4540,
         "Garrett G30-900":4540, "Precision 6266 Gen2":5169, "Precision 6466 Gen2":5959,
         "Xona Rotor XR7169":4897, "Xona Rotor XR8267":6100}

RHO = {"g-TiAl":3900.0, "Inconel":8000.0, "Al":2700.0}
CHOKE_DESIGN = 0.95   # never design past 95 percent of choke

REDLINES = [6650, 7200, 7800, 8400]

# ---------------------------------------------------------------- inertia
def inertia_turbine_only(dia_mm, mat):
    """Round-one model: J proportional to rho * D^5 (geometric similarity)."""
    return (RHO[mat]/RHO["g-TiAl"])*(dia_mm/63.0)**5

def inertia_with_compressor(dt_mm, mat, dc_mm, k_c=0.55):
    """Adds the compressor wheel. Aluminium, larger diameter, thinner section.
    J_total = rho_t*Dt^5 + k_c*rho_al*Dc^5, normalised so the EFR 7163 = 1.00."""
    def raw(dt, m, dc):
        return RHO[m]*(dt/63.0)**5 + k_c*RHO["Al"]*(dc/63.0)**5
    return raw(dt_mm, mat, dc_mm)/raw(63.0, "g-TiAl", 71.0)

# ================================================================== REPORT
out = {}
print("="*78)
print("SITE / ENGINE")
print("="*78)
print(f"  P_amb                {P_AMB:.2f} kPa   ({ALT_M:.0f} m)")
print(f"  Displacement         {DISP*1e6:.1f} cc")
print(f"  Rod ratio            {ROD_RATIO:.3f}  (138 mm rod / 91 mm stroke)")
print(f"  Piston area/valve    Ap/Ai = {A_PISTON/A_INTAKE:.3f}")
print()
print("  rpm    piston m/s   Mach idx Z   VE(round1)   VE(Mach model)   delta")
ve_tbl = []
for rpm in [5500,6000,6650,7000,7200,7500,7800,8100,8400]:
    z = mach_index(rpm, 50.0)
    v1, v2 = ve_round1(rpm), ve_mach(rpm)
    ve_tbl.append({"rpm":rpm,"mps":round(mean_piston_speed(rpm),2),"Z":round(z,3),
                   "ve_r1":round(v1,3),"ve_mach":round(v2,3)})
    print(f"  {rpm:5d}   {mean_piston_speed(rpm):8.2f}   {z:9.3f}   {v1:9.3f}   {v2:13.3f}   {(v2/v1-1)*100:+6.1f}%")
out["ve_table"] = ve_tbl

print()
print("="*78)
print("Q1. WHAT BOOST DOES THE EFR 7163 NEED AT 6650 RPM?")
print("="*78)
for label, vefn in [("round-1 VE curve", ve_round1), ("Mach-index VE", ve_mach)]:
    ve = vefn(6650)
    b_pr = boost_for_pr(3.6)
    f,_  = flow_lbmin(6650, b_pr, ve)
    print(f"  {label:20s}  VE={ve:.3f}   at its PR ceiling 3.60 -> {b_pr:.1f} psi -> "
          f"{f:.1f} lb/min -> {f*HP_PER_LBMIN:.0f} crank / {f*HP_PER_LBMIN*DRIVETRAIN:.0f} whp")
print()
for whp in [400, 431, 450, 500]:
    lb = whp/DRIVETRAIN/HP_PER_LBMIN
    b  = boost_for_flow(lb, 6650, ve_mach)
    print(f"  {whp:3d} whp at 6650 rpm needs {lb:5.1f} lb/min -> {b:5.1f} psi boost "
          f"(PR {pressure_ratio(b):.2f})")

print()
print("="*78)
print("Q2. FULL CANDIDATE TABLE vs REDLINE   (Mach-index VE, design cap 95% of choke)")
print("="*78)
rows = []
for name, choke, prcap, dt, mat, ar, brg, price, dc in TURBOS:
    rec = {"turbo":name,"choke":choke,"pr_cap":prcap,"turbine_mm":dt,"material":mat,
           "ar":ar,"bearing":brg,"price":price,"comp_mm":dc,
           "spool":SPOOL[name],
           "J_turbine_only":round(inertia_turbine_only(dt,mat),3),
           "J_with_comp":round(inertia_with_compressor(dt,mat,dc),3),
           "by_rpm":{}}
    for rpm in REDLINES:
        ve   = ve_mach(rpm)
        b_pr = boost_for_pr(prcap)
        f_pr,_ = flow_lbmin(rpm, b_pr, ve)
        f_ch = choke*CHOKE_DESIGN
        if f_pr <= f_ch:
            lim, f, b = "PR", f_pr, b_pr
        else:
            lim, f = "choke", f_ch
            b = boost_for_flow(f_ch, rpm, ve_mach)
        rec["by_rpm"][rpm] = {"ve":round(ve,3),"limit":lim,"lbmin":round(f,1),
                              "boost":round(b,1),"pr":round(pressure_ratio(b),2),
                              "crank":round(f*HP_PER_LBMIN),
                              "whp":round(f*HP_PER_LBMIN*DRIVETRAIN)}
    rows.append(rec)

hdr = "  %-21s" % "turbo"
for rpm in REDLINES: hdr += " | %-20s" % f"{rpm} rpm"
print(hdr)
print("  %-21s" % "" + (" | %-20s" % "whp  psi   limit")*len(REDLINES))
print("  " + "-"*(21+len(REDLINES)*23))
for r in rows:
    line = "  %-21s" % r["turbo"]
    for rpm in REDLINES:
        d = r["by_rpm"][rpm]
        line += " | %4d %5.1f  %-6s" % (d["whp"], d["boost"], d["limit"])
    print(line)

print()
print("  CROSSOVER: redline at which each turbo stops being pressure-ratio-limited")
for r in rows:
    cross = None
    for rpm in range(6000, 9001, 25):
        ve = ve_mach(rpm)
        f_pr,_ = flow_lbmin(rpm, boost_for_pr(r["pr_cap"]), ve)
        if f_pr > r["choke"]*CHOKE_DESIGN:
            cross = rpm; break
    r["crossover_rpm"] = cross
    print("    %-21s  %s" % (r["turbo"], f"{cross} rpm" if cross else "never below 9000 rpm"))

print()
print("="*78)
print("Q3. WHAT IS RAISING THE RPM LIMIT WORTH?")
print("="*78)
print("  turbo                  6650   7200    7800    | gain 6650->7200   6650->7800")
for r in rows:
    a = r["by_rpm"][6650]["whp"]; b = r["by_rpm"][7200]["whp"]; c = r["by_rpm"][7800]["whp"]
    r["gain_7200"] = b-a; r["gain_7800"] = c-a
    print("    %-21s %4d   %4d    %4d    | %+5d whp (%+4.1f%%)  %+5d whp (%+4.1f%%)"
          % (r["turbo"], a, b, c, b-a, (b/a-1)*100, c-a, (c/a-1)*100))

print()
print("  EFR 7163 alone, at a FIXED sensible 28 psi (not at its PR ceiling):")
fixed = []
for rpm in [6000,6650,7200,7800,8400]:
    ve = ve_mach(rpm)
    f,_ = flow_lbmin(rpm, 28.0, ve)
    f = min(f, 60*CHOKE_DESIGN)
    fixed.append({"rpm":rpm,"lbmin":round(f,1),"whp":round(f*HP_PER_LBMIN*DRIVETRAIN)})
    print(f"    {rpm} rpm  VE {ve:.3f}  {f:5.1f} lb/min  {f*HP_PER_LBMIN*DRIVETRAIN:5.0f} whp")
out["fixed_boost_7163"] = fixed

print()
print("  Boost needed to hold a FIXED 500 whp, as redline rises:")
brpm = []
for rpm in [6000,6650,7200,7800,8400]:
    lb = 500/DRIVETRAIN/HP_PER_LBMIN
    b  = boost_for_flow(lb, rpm, ve_mach)
    brpm.append({"rpm":rpm,"boost":round(b,1),"pr":round(pressure_ratio(b),2)})
    print(f"    {rpm} rpm -> {b:5.1f} psi  (PR {pressure_ratio(b):.2f})")
out["boost_500whp"] = brpm

print()
print("="*78)
print("Q4. MECHANICAL RPM CEILING")
print("="*78)
for rpm in REDLINES + [7500]:
    mps = mean_piston_speed(rpm)
    if   mps < 20: verd = "conservative, production-durable"
    elif mps < 22: verd = "street/track acceptable on forged rods"
    elif mps < 24: verd = "race-only, short service life"
    else:          verd = "not viable on this bottom end"
    print(f"  {rpm:5d} rpm -> {mps:5.2f} m/s mean piston speed  -  {verd}")

print()
print("="*78)
print("Q5. IS 600 WHP REAL?")
print("="*78)
for whp in [450,500,550,600,650]:
    lb = whp/DRIVETRAIN/HP_PER_LBMIN
    line = f"  {whp:3d} whp = {lb:5.1f} lb/min :"
    for rpm in [6650,7200,7800]:
        b = boost_for_flow(lb, rpm, ve_mach)
        line += f"   {rpm}rpm {b:5.1f}psi(PR{pressure_ratio(b):.2f})"
    print(line)

print()
print("="*78)
print("INERTIA MODEL - turbine only vs turbine + compressor")
print("="*78)
print("  turbo                  Dt   mat      Dc   J(turbine only)  J(with comp)  spool rpm")
for r in rows:
    print("    %-21s %3d  %-8s %3d   %11.3f    %10.3f    %5d"
          % (r["turbo"], r["turbine_mm"], r["material"], r["comp_mm"],
             r["J_turbine_only"], r["J_with_comp"], r["spool"]))

out["rows"] = rows
out["site"] = {"p_amb_kpa":round(P_AMB,2),"alt_m":ALT_M,"t_amb":T_AMB,
               "disp_cc":round(DISP*1e6,1),"rod_ratio":round(ROD_RATIO,3)}
out["redlines"] = REDLINES
json.dump(out, open(r"C:\projects\5sgte-intercooler-research\data\rpm_sensitivity.json","w"), indent=1)
print("\nwrote data/rpm_sensitivity.json")
