# 5S-GTE / EFR 7163 intercooler thermal model - independent sanity check
import math

# ---------- constants ----------
R = 287.05          # J/kg-K dry air
CP = 1005.0         # J/kg-K
GAMMA = 1.40
LB_PER_KG = 2.20462
CFM_PER_M3S = 2118.88

def C2K(c): return c + 273.15
def K2C(k): return k - 273.15

# ---------- site conditions ----------
# Weaverville NC, ~2100 ft (640 m). Std day P0=101325 Pa.
def p_ambient(alt_m):
    return 101325.0 * (1 - 2.25577e-5 * alt_m) ** 5.25588

ALT_M = 640.0
P_AMB = p_ambient(ALT_M)
print("Ambient pressure at %.0f m = %.1f kPa" % (ALT_M, P_AMB/1000))

# ---------- engine ----------
DISP_L = 2.2        # 5S block + 3S-GTE head hybrid, ~2.2 L
# (user has referred to it as 2.2 and 2.3 in different places - flag)

def mass_flow(disp_L, rpm, ve, map_kpa, iat_C):
    """4-stroke: volumetric flow = disp * rpm/2 ; density from MAP & IAT"""
    v_dot = disp_L/1000.0 * (rpm/2.0) / 60.0 * ve      # m^3/s at manifold cond.
    rho = (map_kpa*1000.0) / (R * C2K(iat_C))
    return v_dot * rho                                  # kg/s

def compressor_out_T(T_in_C, PR, eta_c):
    T1 = C2K(T_in_C)
    T2 = T1 * (1 + (PR ** ((GAMMA-1)/GAMMA) - 1)/eta_c)
    return K2C(T2)

def effectiveness(T_in_C, T_out_C, T_amb_C):
    return (T_in_C - T_out_C) / (T_in_C - T_amb_C)

def outlet_from_eff(T_in_C, T_amb_C, eps):
    return T_in_C - eps*(T_in_C - T_amb_C)

# ---------- design point ----------
BOOST_PSI = 25.0
T_AMB = 32.0            # deg C summer design, WNC
RPM = 7000
VE = 0.95
ETA_C = 0.74            # EFR 7163 near choke on E85 at this PR
IAT_TARGET = 45.0       # assumed post-IC for mass flow iteration

P_MAN_KPA = P_AMB/1000.0 + BOOST_PSI*6.89476
PR = (P_MAN_KPA) / (P_AMB/1000.0 * 0.97)   # 3% inlet restriction
print("\n=== DESIGN POINT ===")
print("Boost %.1f psi -> MAP %.1f kPa abs, PR = %.2f" % (BOOST_PSI, P_MAN_KPA, PR))

# iterate mass flow with IAT feedback
iat = IAT_TARGET
for _ in range(20):
    mdot = mass_flow(DISP_L, RPM, VE, P_MAN_KPA, iat)
    Tc = compressor_out_T(T_AMB, PR, ETA_C)
    iat_new = outlet_from_eff(Tc, T_AMB, 0.80)
    if abs(iat_new-iat) < 0.01: break
    iat = iat_new

print("mass flow = %.4f kg/s = %.1f lb/min" % (mdot, mdot*LB_PER_KG*60))
print("compressor outlet T = %.1f C (%.0f F)" % (Tc, Tc*9/5+32))
print("IC outlet @ eps=0.80: %.1f C (%.0f F)" % (iat, iat*9/5+32))

Q = mdot * CP * (Tc - iat)
print("Heat rejection Q = %.2f kW (%.0f BTU/hr)" % (Q/1000, Q*3.412))

# sensitivity: effectiveness sweep
print("\neps   T_out(C)  T_out(F)   Q(kW)")
for eps in [0.60,0.65,0.70,0.75,0.80,0.85,0.90]:
    To = outlet_from_eff(Tc, T_AMB, eps)
    q = mdot*CP*(Tc-To)
    print("%.2f   %6.1f    %6.0f   %6.2f" % (eps, To, To*9/5+32, q/1000))

# ---------- e-NTU cross-flow, both fluids unmixed ----------
def eps_crossflow_unmixed(NTU, Cr):
    if Cr <= 1e-6: return 1 - math.exp(-NTU)
    return 1 - math.exp((NTU**0.22 / Cr) * (math.exp(-Cr * NTU**0.78) - 1))

def ntu_required(eps, Cr, lo=0.01, hi=20.0):
    for _ in range(200):
        mid = (lo+hi)/2
        if eps_crossflow_unmixed(mid, Cr) < eps: lo = mid
        else: hi = mid
    return (lo+hi)/2

# cold-side (ambient) mass flow through the core
def cold_mdot(face_w_m, face_h_m, v_face_ms, T_amb_C, p_pa):
    rho = p_pa/(R*C2K(T_amb_C))
    return face_w_m*face_h_m*v_face_ms*rho

CORE_W = 0.610   # m  (24 in) - CSF 8067
CORE_H = 0.300   # m  (12 in)
CORE_T = 0.075   # m  (3 in)

print("\n=== e-NTU CHECK: CSF 8067 610 x 300 x 75 mm ===")
for v_face in [4.0, 8.0, 12.0, 16.0, 22.0]:   # m/s, ~9-50 mph through core
    mc = cold_mdot(CORE_W, CORE_H, v_face, T_AMB, P_AMB)
    Cc = mc*CP
    Ch = mdot*CP
    Cmin, Cmax = min(Cc,Ch), max(Cc,Ch)
    Cr = Cmin/Cmax
    # UA estimate: bar&plate ~ 180 W/m2K overall referenced to core volume-derived area
    # area density typical brazed CAC: ~ 900 m2/m3 total (both sides); use U*A form
    vol = CORE_W*CORE_H*CORE_T
    beta = 900.0            # m2/m3 heat transfer area density
    A = vol*beta
    # U rises with face velocity (air-side dominant); simple correlation U ~ U0*(v/10)^0.5
    U = 55.0*(v_face/10.0)**0.5   # W/m2K, air-side limited
    NTU = U*A/Cmin
    eps = eps_crossflow_unmixed(NTU, Cr)
    To = outlet_from_eff(Tc, T_AMB, eps)
    print("v_face %4.1f m/s (%4.1f mph): mc=%.3f kg/s Cr=%.2f NTU=%.2f eps=%.3f  Tout=%.1fC (%.0fF)"
          % (v_face, v_face*2.237, mc, Cr, NTU, eps, To, To*9/5+32))

# ---------- charge pipe velocity ----------
print("\n=== CHARGE PIPE VELOCITY ===")
def pipe_velocity(mdot_kgs, dia_in, p_kpa, T_C):
    rho = p_kpa*1000/(R*C2K(T_C))
    d = dia_in*0.0254
    a = math.pi*d*d/4
    v = mdot_kgs/(rho*a)
    return v, v*3.28084   # m/s, ft/s

print("HOT side (compressor outlet: P=%.0f kPa, T=%.0f C):" % (P_MAN_KPA*1.03, Tc))
for d in [2.0, 2.25, 2.5, 2.75, 3.0]:
    v_ms, v_fts = pipe_velocity(mdot, d, P_MAN_KPA*1.03, Tc)
    print("  %.2f in : %6.1f m/s  %6.0f ft/s" % (d, v_ms, v_fts))
print("COLD side (IC outlet: P=%.0f kPa, T=%.0f C):" % (P_MAN_KPA, iat))
for d in [2.0, 2.25, 2.5, 2.75, 3.0]:
    v_ms, v_fts = pipe_velocity(mdot, d, P_MAN_KPA, iat)
    print("  %.2f in : %6.1f m/s  %6.0f ft/s" % (d, v_ms, v_fts))

# volumetric flow for reference
rho_out = P_MAN_KPA*1000/(R*C2K(Tc))
print("volumetric @ compressor outlet = %.1f CFM" % (mdot/rho_out*CFM_PER_M3S))

# ---------- pressure drop estimate ----------
print("\n=== PRESSURE DROP ===")
def dp_pipe(mdot_kgs, dia_in, len_m, n_bends, p_kpa, T_C, f=0.02, k_bend=0.25):
    rho = p_kpa*1000/(R*C2K(T_C)); d = dia_in*0.0254
    a = math.pi*d*d/4; v = mdot_kgs/(rho*a)
    K = f*len_m/d + n_bends*k_bend
    return K*0.5*rho*v*v/6894.76   # psi

for d in [2.5, 2.75, 3.0]:
    dp = dp_pipe(mdot, d, 2.4, 6, P_MAN_KPA, (Tc+iat)/2)
    print("  piping dP @ %.2f in, 2.4 m, 6 bends: %.3f psi" % (d, dp))

# core dP: scale from Treadstone C1245 3.5in: 1142 CFM @ 1.5 psi
REF_CFM, REF_DP = 1142.0, 1.5
our_cfm = mdot/rho_out*CFM_PER_M3S
print("  our flow = %.0f CFM" % our_cfm)
print("  core dP (quadratic scale from Treadstone ref) = %.2f psi"
      % (REF_DP*(our_cfm/REF_CFM)**2))
# thinner/wider CSF 8067 has ~15% smaller internal area than C1245 3.5"
print("  CSF 8067 est. core dP = %.2f psi" % (REF_DP*(our_cfm/REF_CFM)**2 * 1.25))

# ---------- effect of dP on required PR / temp ----------
print("\n=== dP PENALTY ===")
for dp_total in [0.5, 1.0, 1.5, 2.0, 3.0]:
    p_needed = P_MAN_KPA + dp_total*6.89476
    pr2 = p_needed/(P_AMB/1000*0.97)
    t2 = compressor_out_T(T_AMB, pr2, ETA_C)
    print("  total dP %.1f psi -> PR %.2f, comp out %.1f C (+%.1f C), IC out @0.80 = %.1f C"
          % (dp_total, pr2, t2, t2-Tc, outlet_from_eff(t2, T_AMB, 0.80)))

# ---------- density / power sanity ----------
print("\n=== CHARGE DENSITY vs IAT ===")
for t in [30,40,50,60,70,80]:
    rho = P_MAN_KPA*1000/(R*C2K(t))
    print("  IAT %2d C: rho = %.3f kg/m3  (%.1f%% vs 40C)" % (t, rho, 100*rho/(P_MAN_KPA*1000/(R*C2K(40)))))

# fuel-based hp estimate check
print("\nAir mass %.1f lb/min -> ~%.0f crank hp at 10 hp per lb/min (E85 ~ 10.5)"
      % (mdot*LB_PER_KG*60, mdot*LB_PER_KG*60*10.0))
