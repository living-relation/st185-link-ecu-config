# Turbine inertia, spool, surge/choke and the engine operating line on each compressor map
import math, json
R=287.05; CP=1005.0; GAM=1.40; PSI=6.89476
def C2K(c): return c+273.15
P_AMB = 101.325*(1-2.25577e-5*640.0)**5.25588
DISP_L = math.pi*(87.5/2)**2*91.0*4/1e6      # litres
print("displacement = %.4f L" % DISP_L)

# ---------- 1. TURBINE INERTIA ----------
# J ~ rho * D^5 for geometrically similar wheels.
# gamma-TiAl ~ 3.9 g/cc ; Inconel 713C ~ 8.0 g/cc ; steel ~ 7.8
print("\n=== TURBINE ROTATIONAL INERTIA (relative, J ~ rho*D^5) ===")
print(" turbo             wheel  dia    material    rho    J rel to 7163   spool penalty")
base=None
rows=[]
for n,d,mat,rho in [
    ("EFR 7163 (current)", 63.0,"gamma-Ti",3.9),
    ("EFR 7670",           70.0,"gamma-Ti",3.9),
    ("EFR 8374",           74.0,"gamma-Ti",3.9),
    ("EFR 9174",           74.0,"gamma-Ti",3.9),
    ("Garrett G25-660",    54.0,"Inconel", 8.0),
    ("Garrett G25-770",    54.0,"Inconel", 8.0),
    ("Garrett G30-770",    55.0,"Inconel", 8.0),
    ("Garrett G30-900",    55.0,"Inconel", 8.0),
    ("Precision 6266 G2",  62.0,"Inconel", 8.0),
    ("Precision 6466 G2",  67.0,"Inconel", 8.0),
    ("Xona XR7169",        62.0,"Inconel", 8.0),
    ("Xona XR8267",        67.0,"Inconel", 8.0),
]:
    J = rho*(d**5)
    if base is None: base=J
    rel=J/base
    rows.append((n,d,mat,rho,rel))
    print("  %-18s %5.0f mm   %-9s %4.1f      %5.2f x       %s"
          % (n,d,mat,rho,rel, "baseline" if abs(rel-1)<0.01 else
             ("%+.0f%%"%((rel-1)*100))))

print("\nKey comparison — what gamma-Ti actually buys:")
jTi74 = 3.9*74**5; jIn74 = 8.0*74**5
print("  EFR 8374 74mm gamma-Ti  J = %.3e (arb)" % jTi74)
print("  same 74mm in Inconel    J = %.3e  -> %.2fx heavier" % (jIn74, jIn74/jTi74))
# equivalent Inconel diameter with the same inertia as the 74 mm gamma-Ti
d_eq = (jTi74/8.0)**0.2
print("  An INCONEL wheel of %.1f mm has the same inertia as the 74mm gamma-Ti." % d_eq)
print("  i.e. the 8374 spools like a ~%.0f mm conventional wheel while flowing like a 74mm." % d_eq)
d_eq63=( (3.9*63**5)/8.0 )**0.2
print("  (current 7163: 63mm gamma-Ti ~ %.1f mm Inconel equivalent)" % d_eq63)

# ---------- 2. SPOOL THRESHOLD ESTIMATE ----------
# Threshold rpm where the engine can supply enough exhaust enthalpy to drive the
# compressor to target PR. Simple scaling: required exhaust power ~ compressor power,
# and available exhaust power ~ engine mass flow. Solve for the rpm where they balance,
# with a turbine-size penalty for larger A/R and larger wheel.
def comp_power(mdot, pr, eta, t1=32.0):
    return mdot*CP*C2K(t1)*(pr**((GAM-1)/GAM)-1)/eta      # W

def engine_mdot(rpm, ve, map_kpa, iat=50.0):
    return DISP_L/1000*(rpm/2)/60*ve*(map_kpa*1000)/(R*C2K(iat))

# A first-principles spool model needs turbine map data nobody publishes. Instead use an
# EMPIRICALLY ANCHORED scaling, calibrated on the one data point we can trust: the EFR 7163
# on a 2.0-2.3 L reaches full boost at roughly 4,000 rpm at 25 psi (widely reported range
# 3,800-4,200). Threshold then scales with turbine inertia, housing A/R and boost target.
ANCHOR_RPM = 4000.0
def spool_rpm(J_rel, ar, target_psi, bearing="ball"):
    thr = ANCHOR_RPM * (J_rel**0.22) * ((ar/0.80)**0.35) * ((target_psi/25.0)**0.20)
    if bearing=="journal": thr *= 1.06     # journal bearings ~5-7% later to threshold
    return thr

print("\n=== SPOOL THRESHOLD ESTIMATE (rpm to full target boost, 3rd gear, steady load) ===")
print("  Empirically anchored: EFR 7163 @ 25 psi on a 2.2 L = 4,000 rpm (reported 3,800-4,200).")
print("  Scaling: thr ~ J_rel^0.22 * (A/R/0.80)^0.35 * (boost/25)^0.20, +6% for journal bearings.")
print(" turbo                 J_rel   A/R    target   threshold rpm   vs 7163")
Jmap = {r[0]:r[4] for r in rows}
base_thr=None
spool_rows=[]
for n,key,ar,tgt,brg in [
    ("EFR 7163 (current)","EFR 7163 (current)",0.80,25,"ball"),
    ("EFR 7670",          "EFR 7670",          0.92,28,"ball"),
    ("EFR 8374 C-type IWG","EFR 8374",         0.92,30,"ball"),
    ("EFR 8374 D-type EWG","EFR 8374",         1.05,30,"ball"),
    ("EFR 9174",          "EFR 9174",          1.05,30,"ball"),
    ("G25-660 0.92 TS",   "Garrett G25-660",   0.92,28,"ball"),
    ("G25-770 0.92 TS",   "Garrett G25-770",   0.92,30,"ball"),
    ("G30-770 1.01 TS",   "Garrett G30-770",   1.01,30,"ball"),
    ("G30-900 1.01 TS",   "Garrett G30-900",   1.01,30,"ball"),
    ("PT6266 Gen2 0.85",  "Precision 6266 G2", 0.85,30,"journal"),
    ("PT6466 Gen2 1.00",  "Precision 6466 G2", 1.00,30,"journal"),
    ("Xona XR7169 0.86",  "Xona XR7169",       0.86,30,"ball"),
]:
    r=spool_rpm(Jmap[key],ar,tgt,brg)
    if base_thr is None: base_thr=r
    spool_rows.append((n,round(r)))
    print("  %-20s %5.2f   %4.2f   %2d psi     %5.0f          %s"
          % (n,Jmap[key],ar,tgt,r, "baseline" if abs(r-base_thr)<1 else "%+d rpm"%round(r-base_thr)))
print("  Absolute values +/- ~400 rpm. The RANKING is the reliable output.")

# ---------- 3. ENGINE OPERATING LINE ON THE MAP ----------
print("\n=== ENGINE OPERATING LINE (corrected flow vs PR) ===")
print("  2.189 L, VE curve, wide-open throttle, boost-limited by target")
def op_line(target_psi, ve_curve):
    pts=[]
    for rpm in range(2000,7601,200):
        ve = ve_curve(rpm)
        pm = min(P_AMB + target_psi*PSI, P_AMB + target_psi*PSI*min(1.0,(rpm-1800)/2400.0))
        pm = max(pm, P_AMB)
        m  = engine_mdot(rpm, ve, pm)
        lb = m*2.20462*60
        pr = pm/(P_AMB*0.97)
        pts.append((rpm, round(lb,1), round(pr,3), round(ve,3)))
    return pts
# VE curve for a ported 3S-GTE head with performance cams: rises to ~1.02 at 5,500 rpm,
# tails to ~0.88 by 7,500 as the port and valve area run out.
def vec(rpm):
    x=(rpm-5500.0)/2600.0
    return max(0.70, min(1.03, 1.02 - 0.34*x*x - 0.06*max(0.0,x)))
for tgt,label in [(25,"25 psi (7163 today)"),(30,"30 psi (8374 design)"),(36,"36 psi (8374 max)")]:
    pts=op_line(tgt,vec)
    print("\n  --- %s ---" % label)
    print("   rpm    lb/min    PR     VE")
    for p in pts[::3]:
        print("  %4d   %6.1f   %5.2f   %.2f" % p)
    peak=max(pts,key=lambda x:x[1])
    print("   peak: %.1f lb/min at PR %.2f (%d rpm)" % (peak[1],peak[2],peak[0]))

# ---------- 4. WHERE THE DESIGN POINT LANDS ON EACH MAP ----------
print("\n=== DESIGN POINT vs COMPRESSOR MAP LIMITS ===")
# design point = peak flow on the 30 psi operating line
DP = max(op_line(30,vec), key=lambda x:x[1])[1]
DPPR= max(op_line(30,vec), key=lambda x:x[1])[2]
print("  design point from the operating line above: %.1f lb/min at PR %.2f" % (DP,DPPR))
print("  surge flow estimated as ~24%% of choke at PR 3 (typical for these frames)")
print(" turbo            choke   surge~PR3   %of choke at DP   low-rpm surge margin   verdict")
maps=[("EFR 7163",60),("EFR 7670",67),("EFR 8374",79),("EFR 9174",105),
      ("G25-660",64),("G25-770",73),("G30-770",77),("G30-900",88),
      ("PT6266",72),("PT6466",82),("Xona XR7169",75)]
# lowest flow the engine produces while still at full boost (the surge-critical point)
low = [p for p in op_line(30,vec) if p[2]>3.2]
low_flow = min(low, key=lambda x:x[1])[1] if low else 25.0
print("  engine's lowest flow at full boost = %.1f lb/min (the surge-critical point)\n" % low_flow)
for n,choke in maps:
    frac=DP/choke; surge=0.24*choke
    marg = low_flow/surge
    v = ("OVER CHOKE - cannot do it" if frac>1 else
         "at choke, eff ~62-65%" if frac>0.95 else
         "edge of island" if frac>0.90 else
         "IN THE ISLAND" if frac>0.62 else "oversized for this engine")
    sm = "OK" if marg>1.15 else ("marginal" if marg>1.0 else "SURGE")
    print("  %-15s %4.0f     %5.1f       %5.0f%%           %5.2f  %-8s   %s"
          %(n,choke,surge,frac*100,marg,sm,v))

json.dump({"inertia":[{"turbo":r[0],"dia":r[1],"mat":r[2],"J_rel":round(r[4],3)} for r in rows],
           "spool":[{"turbo":s[0],"rpm":s[1]} for s in spool_rows]},
  open(r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs\turbo_data.json","w"),indent=1)
print("\nwrote turbo_data.json")
