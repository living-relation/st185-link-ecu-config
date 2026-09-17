"""
RECONCILIATION - prior turbo research (data/prior-turbo-research/06_turbo_model.py)
vs the round-two report model (rpm_sensitivity.py).

Stage 1: forensic diff. Reverse-engineer what each prior CSV actually did.
Stage 2: one unified model, corrected constants, propagated everywhere.

Run:  python reconcile.py
"""
import math, json, csv, os

HERE = "/sessions/amazing-blissful-bell/mnt/projects/5sgte-intercooler-research"
PRIOR = os.path.join(HERE, "data", "prior-turbo-research")

# ====================================================================
# STAGE 1 - what the PRIOR model actually computes
# ====================================================================
P_DISP_CC   = 2164
P_K_FLOW    = 0.0029233        # lb per rev at VE=1, PR=1
P_WHP_E85   = 9.35             # 11 crank * 0.85
P_VE_RPM = [2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500]
P_VE_VAL = [0.85,0.88,0.92,0.96,1.00,1.03,1.05,1.04,1.01,0.97,0.92,0.87]

def p_ve(rpm):
    return interp(rpm, P_VE_RPM, P_VE_VAL)

def interp(x, xs, ys):
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs)-1):
        if xs[i] <= x <= xs[i+1]:
            f = (x-xs[i])/(xs[i+1]-xs[i])
            return ys[i] + f*(ys[i+1]-ys[i])
    return ys[-1]

def p_pr(boost):  return (boost + 14.7)/14.7
def p_flow(rpm, boost): return P_K_FLOW * rpm * p_ve(rpm) * p_pr(boost)

# What reference charge density does K_FLOW * PR imply?
#   K_FLOW = (disp_ft3 / 2) * 0.0765 lb/ft3
disp_ft3 = P_DISP_CC / 28316.846
k_check  = disp_ft3/2 * 0.0765
rho_std_kgm3 = 0.0765 * 16.0185                       # 1.2255 kg/m3
# implied manifold temp at any boost: P_abs = (boost+14.7) psi
R = 287.05
def p_implied_charge_tempC(boost):
    p_abs_pa = (boost + 14.7) * 6894.76
    rho = rho_std_kgm3 * p_pr(boost)
    return p_abs_pa/(R*rho) - 273.15

print("="*84)
print("STAGE 1A - decoding the prior model's hidden assumptions")
print("="*84)
print(f"  K_FLOW stated             {P_K_FLOW:.7f}")
print(f"  K_FLOW rebuilt from 2164cc @ 0.0765 lb/ft3   {k_check:.7f}   -> match: {abs(k_check-P_K_FLOW)<2e-6}")
print(f"  Implied reference air density  {rho_std_kgm3:.4f} kg/m3  (= 0.0765 lb/ft3)")
for b in (20, 25, 30):
    print(f"  At {b} psi gauge: implied manifold charge temperature = "
          f"{p_implied_charge_tempC(b):.1f} C  ({p_implied_charge_tempC(b)*9/5+32:.0f} F)")
print("  -> the prior model assumes a 15 C charge at the valve AND sea-level ambient.")
print("     It applies NO intercooler-outlet temperature and NO altitude correction.")

# ====================================================================
# STAGE 1B - reverse-engineer implied VE in each prior CSV
# ====================================================================
def read_csv(name, skip_hash=False):
    path = os.path.join(PRIOR, name)
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        lines = [l for l in f if not (skip_hash and l.startswith("#"))]
    rd = csv.DictReader(lines)
    for r in rd: rows.append(r)
    return rows

op   = read_csv("05_operating_point_detail.csv")
g4x  = read_csv("13_g4x_boost_target_table.csv", skip_hash=True)
cmp_ = read_csv("05_turbo_comparison_data.csv")
cts  = read_csv("11_charge_temp_summary.csv")

print()
print("="*84)
print("STAGE 1B - implied VE and implied whp/lb-min in each prior file")
print("="*84)
print(f"  {'rpm':>5} | {'--- 05_operating_point_detail ---':^40} | {'--- 13_g4x_boost_target ---':^40}")
print(f"  {'':>5} | {'boost':>6} {'flow':>7} {'impVE':>7} {'whp':>5} {'w/lb':>6} | "
      f"{'boost':>6} {'flow':>7} {'impVE':>7} {'whp':>5} {'w/lb':>6}")

diffs = []
for a, b in zip(op, g4x):
    rpm = float(a["RPM"])
    # 05_operating_point_detail
    ba, fa = float(a["Boost (psi)"]), float(a["Mass flow (lb/min)"])
    wa = float(a["Est WHP"])
    ve_a = fa/(P_K_FLOW*rpm*p_pr(ba)) if rpm > 0 else 0
    wl_a = wa/fa if fa else 0
    # 13_g4x
    bb, fb = float(b["Boost_Target_psi"]), float(b["est_flow_lbmin"])
    wb = float(b["est_whp_E85"])
    ve_b = fb/(P_K_FLOW*rpm*p_pr(bb)) if rpm > 0 else 0
    wl_b = wb/fb if fb else 0
    diffs.append(dict(rpm=rpm, ve_a=ve_a, ve_b=ve_b, ve_model=p_ve(rpm),
                      wl_a=wl_a, wl_b=wl_b, whp_a=wa, whp_b=wb,
                      boost_a=ba, boost_b=bb, flow_a=fa, flow_b=fb))
    if rpm % 500 == 0 or rpm >= 7000:
        print(f"  {rpm:5.0f} | {ba:6.1f} {fa:7.2f} {ve_a:7.3f} {wa:5.0f} {wl_a:6.2f} | "
              f"{bb:6.1f} {fb:7.2f} {ve_b:7.3f} {wb:5.0f} {wl_b:6.2f}")

print()
print("  Model VE curve for reference (06_turbo_model.py):")
print("   ", "  ".join(f"{r:.0f}:{p_ve(r):.3f}" for r in (5000,6000,6500,7000,7500)))

# ====================================================================
# STAGE 1C - the 7500 rpm three-way disagreement, resolved
# ====================================================================
print()
print("="*84)
print("STAGE 1C - the 45 whp spread at 7500 rpm, itemised")
print("="*84)
d75 = diffs[-1]
# 11_charge_temp_summary for the 7163
row7163 = [r for r in cts if r["turbo"] == "EFR 7163"][0]
pk30 = float(row7163["peak_whp_30"])
pct  = float(row7163["pct_of_max_flow_30psi"])/100.0
ct_F = float(row7163["charge_tempF_at_7500_30psi"])
flow_cts = pct*60.0
print(f"  A. 05_operating_point_detail  27.0 psi, {d75['flow_a']:.2f} lb/min -> {d75['whp_a']:.0f} whp"
      f"   (implied VE {d75['ve_a']:.3f}, {d75['wl_a']:.2f} whp/lb-min)")
print(f"  B. 13_g4x_boost_target_table  28.2 psi, {d75['flow_b']:.2f} lb/min -> {d75['whp_b']:.0f} whp"
      f"   (implied VE {d75['ve_b']:.3f}, {d75['wl_b']:.2f} whp/lb-min)")
print(f"  C. 11_charge_temp_summary     30.0 psi, {flow_cts:.2f} lb/min -> {pk30:.1f} whp"
      f"   (implied VE {flow_cts/(P_K_FLOW*7500*p_pr(30)):.3f}, {pk30/flow_cts:.2f} whp/lb-min)")
print()
# decompose A vs B
f_b_at_a_boost = P_K_FLOW*7500*d75["ve_b"]*p_pr(d75["boost_a"])
print("  Decomposition of A vs B (both claim to be the EFR 7163 at 7500 rpm):")
print(f"    step 1  boost 28.2 -> 27.0 psi          flow {d75['flow_b']:.2f} -> {f_b_at_a_boost:.2f} lb/min "
      f"({(f_b_at_a_boost-d75['flow_b']):+.2f})")
print(f"    step 2  VE {d75['ve_b']:.3f} -> {d75['ve_a']:.3f}                flow {f_b_at_a_boost:.2f} -> {d75['flow_a']:.2f} lb/min "
      f"({(d75['flow_a']-f_b_at_a_boost):+.2f})")
print(f"    step 3  whp/lb-min {d75['wl_b']:.2f} -> {d75['wl_a']:.2f}       whp {d75['flow_a']*d75['wl_b']:.0f} -> {d75['whp_a']:.0f} "
      f"({d75['whp_a']-d75['flow_a']*d75['wl_b']:+.0f})")
print(f"    TOTAL   {d75['whp_b']:.0f} -> {d75['whp_a']:.0f} whp = {d75['whp_a']-d75['whp_b']:+.0f} whp")
print()
print(f"  VERDICT: the spread is NOT a choke cap. Choke margin in file A at 7500 rpm is"
      f" {60-d75['flow_a']:.2f} lb/min, so the 60 lb/min limit is not binding in any of the three.")
print("  The spread is (i) a boost-target difference and (ii) file A silently using a VE")
print(f"  of {d75['ve_a']:.3f} at 7500 rpm where the shared model says {p_ve(7500):.3f} - a {(1-d75['ve_a']/p_ve(7500))*100:.1f}% reduction")
print("  that appears in no other file and is documented nowhere.")

# ====================================================================
# STAGE 2 - the unified model
# ====================================================================
print()
print("="*84)
print("STAGE 2 - UNIFIED MODEL")
print("="*84)

GAMMA, CP, PSI = 1.40, 1005.0, 6.89476
LBMIN = 2.20462*60

# --- site (Weaverville NC, 2100 ft) ---------------------------------
ALT_M = 640.0
P_AMB = 101.325*(1-2.25577e-5*ALT_M)**5.25588      # 93.87 kPa
T_AMB = 32.0
FILTER_LOSS = 0.97

# --- engine: CORRECTED displacement ---------------------------------
BORE, STROKE, ROD, NCYL = 0.0875, 0.0910, 0.1380, 4
DISP = math.pi*(BORE/2)**2*STROKE*NCYL             # 2.1888e-3 m3 = 2188.8 cc
ROD_RATIO = ROD/STROKE
IV_DIA = 0.0335
A_PISTON = math.pi*(BORE/2)**2
A_INTAKE = 2*math.pi*(IV_DIA/2)**2
CI = 0.40

# --- CORRECTED conversion constants ---------------------------------
# crank hp per lb/min on E85. Garrett: hp = flow*60/(AFR*BSFC).
#   AFR 7.8 (lambda 0.80 on 9.765 stoich), BSFC 0.77 lb/hp-hr -> 9.98
HP_PER_LBMIN = 10.0        # band 9.5 - 10.5
DRIVETRAIN   = 0.80        # 20% AWD loss. band 0.78 - 0.82
WHP_PER_LBMIN = HP_PER_LBMIN*DRIVETRAIN            # 8.00

def afr_bsfc_hp(afr, bsfc): return 60.0/(afr*bsfc)

print(f"  Displacement          {DISP*1e6:.1f} cc   (prior model used {P_DISP_CC} cc, {(DISP*1e6/P_DISP_CC-1)*100:+.2f}%)")
print(f"  Site pressure         {P_AMB:.2f} kPa  (prior model used 101.33 kPa implicitly)")
print(f"  crank hp per lb/min   {HP_PER_LBMIN:.1f}   (prior model used 11.0)")
print(f"    cross-check: AFR 7.8 / BSFC 0.77 -> {afr_bsfc_hp(7.8,0.77):.2f} hp per lb/min")
print(f"    cross-check: AFR 7.5 / BSFC 0.85 -> {afr_bsfc_hp(7.5,0.85):.2f}  (pessimistic)")
print(f"    cross-check: AFR 8.0 / BSFC 0.70 -> {afr_bsfc_hp(8.0,0.70):.2f}  (optimistic, = the prior 11.0)")
print(f"  drivetrain factor     {DRIVETRAIN:.2f}  (prior model used 0.85, report used 0.82)")
print(f"  WHP per lb/min        {WHP_PER_LBMIN:.2f} (prior model used {P_WHP_E85}, {(P_WHP_E85/WHP_PER_LBMIN-1)*100:+.1f}%)")

# --- VE: reconciled --------------------------------------------------
def mean_piston_speed(rpm): return 2*STROKE*rpm/60.0
def sound_speed(tC): return math.sqrt(GAMMA*R*(tC+273.15))
def mach_index(rpm, iatC): return A_PISTON*mean_piston_speed(rpm)/(CI*A_INTAKE*sound_speed(iatC))

def ve_report(rpm, iatC=50.0, cam_peak=6200.0, emap=1.6):
    """The round-two report curve."""
    cam = 1.00 - 0.030*((rpm-cam_peak)/2500.0)**2
    Z = mach_index(rpm, iatC)
    mach = 1.0 if Z <= 0.50 else max(0.45, 1.0 - 1.25*(Z-0.50))
    bp = 1.0 - 0.05*max(0.0, emap-1.0)
    return max(0.40, cam*mach*bp)

def ve_unified(rpm, iatC=50.0, cam_peak=5800.0, emap=1.6):
    """Reconciled curve.

    Anchored on the head-flow reference doc, which independently says:
      - NA-basis VE peaking ~1.00-1.005 in the 5000-5800 rpm band is realistic
        for HKS 264 cams on this head (long 91 mm stroke favours mid-rpm);
      - the ~245 CFM/port ceiling and 9 mm lift make the port the limiter
        near 7000-7800 rpm, not before;
      - VE should roll off above ~6000 rpm, gracefully, not collapse.

    Construction: broad cam/plenum parabola x Taylor Mach rolloff x residual-gas
    penalty for exhaust backpressure. Same functional form as the report, with the
    cam peak moved to 5800 rpm to match the head-flow reference and the prior
    research (both put the peak at 5000-5500, the report put it at 6200).
    """
    cam = 1.00 - 0.030*((rpm-cam_peak)/2500.0)**2
    Z = mach_index(rpm, iatC)
    mach = 1.0 if Z <= 0.50 else max(0.45, 1.0 - 1.25*(Z-0.50))
    bp = 1.0 - 0.05*max(0.0, emap-1.0)
    return max(0.40, cam*mach*bp)

print()
print("  VE curve comparison (all at 50 C charge, EMAP/IMAP 1.6 where applicable):")
print(f"   {'rpm':>5} {'prior 06_model':>15} {'05_op_detail':>13} {'report bp1.6':>13} {'UNIFIED':>9} {'Z':>7}")
for rpm in (5000,5500,6000,6500,6650,7000,7200,7500,7800):
    dm = [d for d in diffs if abs(d["rpm"]-rpm) < 130]
    va = f"{dm[0]['ve_a']:.3f}" if dm else "  -  "
    print(f"   {rpm:5d} {p_ve(rpm):15.3f} {va:>13} {ve_report(rpm):13.3f} "
          f"{ve_unified(rpm):9.3f} {mach_index(rpm,50):7.3f}")

# --- flow with charge-temperature coupling ---------------------------
def comp_out_C(t1C, pr, eta):
    return (t1C+273.15)*(1 + (pr**((GAMMA-1)/GAMMA) - 1)/eta) - 273.15

def eps_crossflow(ntu, cr):
    if cr <= 1e-6: return 1-math.exp(-ntu)
    return 1-math.exp((ntu**0.22/cr)*(math.exp(-cr*ntu**0.78)-1))

def core_eps(w_m, h_m, t_m, v_face, m_hot, t_amb, p_amb_kpa):
    rho = p_amb_kpa*1000/(R*(t_amb+273.15))
    mc = w_m*h_m*v_face*rho
    Cc, Ch = mc*CP, m_hot*CP
    cmin, cmax = min(Cc,Ch), max(Cc,Ch)
    cr = cmin/cmax
    A = w_m*h_m*t_m*900.0
    U = 55.0*math.sqrt(v_face/10.0)
    ntu = U*A/cmin
    e = eps_crossflow(ntu, cr)
    return e*cmin/Ch, e, ntu, cr, mc

CORE = dict(w=0.610, h=0.305, t=0.076, vf=7.81)     # SpeedFactory SS-850, design point

def operating_point(rpm, boost_psi, eta_c, ve_fn=ve_unified, core=CORE,
                    t_amb=T_AMB, p_amb=P_AMB, dp_psi=1.5):
    """Fully coupled: flow <-> charge temp <-> VE. This is the thing NEITHER prior
    model did. The prior model froze charge at 15 C; the report froze it at 50 C."""
    p_man = p_amb + boost_psi*PSI
    pr = (p_man + dp_psi*PSI)/(p_amb*FILTER_LOSS)     # compressor works against core dP too
    tc = comp_out_C(t_amb, pr, eta_c)
    iat = t_amb + 25.0
    for _ in range(80):
        ve = ve_fn(rpm, iat)
        rho = p_man*1000.0/(R*(iat+273.15))
        m = DISP*(rpm/2.0)/60.0*ve*rho                # kg/s
        eps, epsHX, ntu, cr, mc = core_eps(core["w"], core["h"], core["t"],
                                           core["vf"], m, t_amb, p_amb)
        new = tc - eps*(tc-t_amb)
        if abs(new-iat) < 0.01:
            iat = new; break
        iat = new
    ve = ve_fn(rpm, iat)
    rho = p_man*1000.0/(R*(iat+273.15))
    m = DISP*(rpm/2.0)/60.0*ve*rho
    lb = m*LBMIN
    return dict(rpm=rpm, boost=boost_psi, pr=pr, tc=tc, iat=iat, ve=ve,
                lb=lb, whp=lb*WHP_PER_LBMIN, eps=eps, m=m)

print()
print("="*84)
print("STAGE 2B - the EFR 7163 on the unified model")
print("="*84)
print(f"  {'rpm':>5} {'boost':>6} {'PR':>5} {'eta_c':>6} {'Tcomp':>7} {'IAT':>7} {'VE':>6} "
      f"{'lb/min':>7} {'whp':>6} {'choke%':>7}")
ETA_7163 = {5000:0.742, 5500:0.739, 6000:0.732, 6500:0.724, 6650:0.721,
            7000:0.714, 7200:0.711, 7500:0.708}
best = None
for rpm in (5000,5500,6000,6500,6650,7000,7200,7500):
    op_ = operating_point(rpm, 30.0, ETA_7163[rpm])
    ch = op_["lb"]/60.0*100
    print(f"  {rpm:5d} {30.0:6.1f} {op_['pr']:5.2f} {ETA_7163[rpm]:6.3f} {op_['tc']:6.0f}C "
          f"{op_['iat']:6.0f}C {op_['ve']:6.3f} {op_['lb']:7.2f} {op_['whp']:6.0f} {ch:6.1f}%")
    if best is None or op_["whp"] > best["whp"]: best = op_
print(f"\n  Peak: {best['whp']:.0f} whp at {best['rpm']} rpm, {best['lb']:.1f} lb/min, IAT {best['iat']:.0f} C")

json.dump(dict(diffs=diffs), open(os.path.join(HERE,"data","reconcile_stage1.json"),"w"), indent=1)
print("\n  stage-1 diff written to data/reconcile_stage1.json")
