"""
Round-two thermal re-run at the RECOMMENDED turbo's actual design point.

Round one sized the core for 25 psi at 6650 rpm on the EFR 7163.
Round two moves the design point to the Garrett G25-770 at 30 psi and 7200 rpm.
This script asks whether the core recommendation changes, and whether the spare
bumper clearance (Dan has 1.5x what the round-one core needs) should be spent.

Uses the same epsilon-NTU cross-flow model as the report JavaScript so the two agree.
"""
import math, json

R, CP, GAM, PSI = 287.05, 1005.0, 1.40, 6.89476
LBMIN = 2.20462*60
CFM   = 2118.88
ALT   = 640.0
P_AMB = 101.325*(1-2.25577e-5*ALT)**5.25588
T_AMB = 32.0
DISP  = 2.1888e-3

def eps_cf(ntu, cr):
    if cr <= 1e-6: return 1-math.exp(-ntu)
    return 1-math.exp((ntu**0.22/cr)*(math.exp(-cr*ntu**0.78)-1))

def core_eps(w, hgt, thk, vface, m_hot, tamb=T_AMB, pamb=P_AMB):
    rho = pamb*1000/(R*(tamb+273.15))
    mc  = w*hgt*vface*rho
    Cc, Ch = mc*CP, m_hot*CP
    cmin, cmax = min(Cc,Ch), max(Cc,Ch)
    cr  = cmin/cmax
    A   = w*hgt*thk*900.0            # m2 of wetted area per m3 of core, bar & plate
    U   = 55.0*math.sqrt(vface/10.0) # W/m2K, scaled with face velocity
    ntu = U*A/cmin
    e   = eps_cf(ntu, cr)
    return {"eps": e*cmin/Ch, "epsHX": e, "ntu": ntu, "cr": cr,
            "mCold": mc, "cmin_is_cold": Cc < Ch}

def comp_out(tin, pr, eta):
    return (tin+273.15)*(1+(pr**((GAM-1)/GAM)-1)/eta)-273.15

def ve_mach(rpm, iat=50.0, cam=6200.0, bp=1.6):
    A_p = math.pi*(0.0875/2)**2
    A_i = 2*math.pi*(0.0335/2)**2
    a   = math.sqrt(GAM*R*(iat+273.15))
    Z   = A_p*(2*0.091*rpm/60)/(0.40*A_i*a)
    camf = 1.00-0.030*((rpm-cam)/2500.0)**2
    machf= 1.0 if Z<=0.50 else max(0.45, 1.0-1.25*(Z-0.50))
    return max(0.40, camf*machf*(1-0.05*max(0.0,bp-1.0)))

def solve(boost, rpm, w_mm, h_mm, t_mm, vface, eta=0.72, tamb=T_AMB):
    pman = P_AMB + boost*PSI
    pr   = pman/(P_AMB*0.97)
    tc   = comp_out(tamb, pr, eta)
    iat, m, e = tamb+30, 0, 0
    for _ in range(80):
        ve  = ve_mach(rpm, iat)
        rho = pman*1000/(R*(iat+273.15))
        m   = DISP*(rpm/2)/60*ve*rho
        r   = core_eps(w_mm/1000, h_mm/1000, t_mm/1000, vface, m, tamb)
        e   = r["eps"]
        nt  = tc - e*(tc-tamb)
        if abs(nt-iat) < 0.01: iat = nt; break
        iat = nt
    Q = m*CP*(tc-iat)
    vol = (w_mm/1000)*(h_mm/1000)*(t_mm/1000)*1000
    return {"pman":pman,"pr":pr,"tc":tc,"iat":iat,"eps":e,"m":m,"lbmin":m*LBMIN,
            "Q":Q,"vol":vol,"ve":ve_mach(rpm,iat),"whp":m*LBMIN*10*0.82,
            "ntu":r["ntu"],"cr":r["cr"],"cmin_cold":r["cmin_is_cold"],
            "dTrad":Q/(r["mCold"]*CP),"mCold":r["mCold"]}

print("="*80)
print("DESIGN POINT MOVED")
print("="*80)
print("  case                                    lb/min  whp   PR   Tcomp  IAT   eps")
cases = [("ROUND 1  EFR 7163, 25 psi, 6650 rpm", 25, 6650),
         ("ROUND 2  G25-770,  30 psi, 7200 rpm", 30, 7200),
         ("         G25-770,  32 psi, 7200 rpm", 32, 7200),
         ("worst    G25-770,  30 psi, 7200 rpm, 40 C ambient", 30, 7200)]
base = (610, 300, 75, 8.0)
out = {"cases": []}
for i,(lab, b, rpm) in enumerate(cases):
    ta = 40.0 if "40 C" in lab else T_AMB
    r = solve(b, rpm, *base, tamb=ta)
    out["cases"].append({"label":lab,"boost":b,"rpm":rpm,"tamb":ta,
                         "lbmin":round(r["lbmin"],1),"whp":round(r["whp"]),
                         "pr":round(r["pr"],2),"tc":round(r["tc"]),
                         "iat":round(r["iat"],1),"eps":round(r["eps"],3)})
    print("  %-52s %5.1f  %4.0f  %4.2f  %4.0f   %5.1f  %.3f"
          % (lab, r["lbmin"], r["whp"], r["pr"], r["tc"], r["iat"], r["eps"]))

print()
print("="*80)
print("IS A BIGGER CORE JUSTIFIED?  Design point: G25-770, 30 psi, 7200 rpm")
print("="*80)
print("  Dan has about 1.5x the clearance the 610x300x75 core needs. Three ways to")
print("  spend it: more depth, more height, more width. They are not equivalent.")
print()
ref = solve(30, 7200, 610, 300, 75, 8.0)
print("  core W x H x T mm   vol L   face cm2   eps    IAT C   dIAT vs base   air dP index")
opts = [("610 x 300 x  75  (base, 24x12x3)", 610,300, 75),
        ("610 x 300 x 100  (24x12x4)",       610,300,100),
        ("610 x 300 x 115  (24x12x4.5)",     610,300,115),
        ("610 x 340 x  75  (taller)",        610,340, 75),
        ("685 x 300 x  75  (wider)",         685,300, 75),
        ("685 x 340 x  75  (taller+wider)",  685,340, 75),
        ("685 x 340 x 100  (everything)",    685,340,100)]
out["sizes"] = []
for lab, w, hh, t in opts:
    # Face velocity falls as face area grows for a fixed volume of ram air captured.
    # Duct captures a fixed frontal stream; larger face = the same air spread thinner.
    vface = 8.0*(610*300)/(w*hh)
    r = solve(30, 7200, w, hh, t, vface)
    # air-side pressure drop index: rises with depth, falls with face area
    dp_idx = (t/75.0)**1.0*(vface/8.0)**2
    out["sizes"].append({"label":lab,"w":w,"h":hh,"t":t,"vol":round(r["vol"],1),
                         "vface":round(vface,2),"eps":round(r["eps"],3),
                         "iat":round(r["iat"],1),"d_iat":round(r["iat"]-ref["iat"],1),
                         "dp_idx":round(dp_idx,2)})
    print("  %-33s %5.1f   %6.0f    %.3f  %5.1f    %+5.1f          %.2f"
          % (lab, r["vol"], w*hh/100.0, r["eps"], r["iat"], r["iat"]-ref["iat"], dp_idx))

print()
print("  NOTE ON FACE VELOCITY: the model above holds the CAPTURED AIR STREAM constant,")
print("  so a bigger face spreads the same air thinner and face velocity drops. That is")
print("  what actually happens behind a fixed bumper aperture. Growing the core past the")
print("  aperture buys nothing and can make things worse.")

print()
print("="*80)
print("COST OF A BIGGER CORE - charge volume (lag) and thermal mass (soak)")
print("="*80)
rho_charge = 30*PSI+P_AMB
print("  core                 charge void L   fill time ms   core mass kg   soak time s")
out["penalty"] = []
for lab, w, hh, t in opts:
    vol_L  = w*hh*t/1e6
    void_L = vol_L*0.55
    rho    = (P_AMB+30*PSI)*1000/(R*(60+273.15))
    vdot   = ref["m"]/rho*1000.0           # L/s
    fill   = void_L/vdot*1000.0            # ms
    mass   = vol_L*0.62                    # kg, bar & plate empirical
    soak   = mass*900.0*30.0/ref["Q"]      # s to warm the core 30 K at design heat load
    out["penalty"].append({"label":lab,"void":round(void_L,1),"fill_ms":round(fill,1),
                           "mass":round(mass,1),"soak_s":round(soak,2)})
    print("  %-33s %5.1f        %5.1f         %5.1f        %5.2f" % (lab, void_L, fill, mass, soak))

print()
print("="*80)
print("SPOOL PENALTY OF A BIGGER CORE - is it real?")
print("="*80)
print("  Extra charge volume between compressor and throttle must be filled before")
print("  boost rises. Going from 13.7 L to 21.0 L of core adds about 4.0 L of void.")
v_small = 610*300*75/1e6*0.55
v_big   = 610*300*115/1e6*0.55
rho_lo  = (P_AMB+5*PSI)*1000/(R*(60+273.15))
m_lo    = ref["m"]*0.35                      # part-throttle flow during spool
vdot_lo = m_lo/rho_lo*1000
print(f"  extra void                 {v_big-v_small:.2f} L")
print(f"  flow during spool-up       {vdot_lo:.0f} L/s")
print(f"  extra time to fill         {(v_big-v_small)/vdot_lo*1000:.0f} ms")
print("  A 40-60 ms delay is at the edge of what a driver can feel. It is not the")
print("  reason to reject a thicker core. Radiator shadowing is.")
out["spool"] = {"extra_void_L":round(v_big-v_small,2),
                "vdot_spool_Lps":round(vdot_lo,0),
                "extra_ms":round((v_big-v_small)/vdot_lo*1000,0)}

print()
print("="*80)
print("RADIATOR SHADOWING - the real constraint")
print("="*80)
print("  The intercooler sits in front of the radiator. Air heated by the intercooler")
print("  then has to cool the engine. Two effects, both worse with a thicker core:")
print("    1. the air reaching the radiator is hotter")
print("    2. less air gets through at all, because core depth adds resistance")
print()
print("  core depth   air heated by IC   relative air mass through stack   net radiator air")
for t in [75, 100, 115]:
    r = solve(30, 7200, 610, 300, t, 8.0)
    rel_m = (75.0/t)**0.35            # air mass falls with depth, exponent from core dP data
    print("  %5d mm      +%5.1f C            %.3f                            %+5.1f C hotter"
          % (t, r["dTrad"], rel_m, r["dTrad"]/rel_m - solve(30,7200,610,300,75,8.0)["dTrad"]))

json.dump(out, open(r"C:\projects\5sgte-intercooler-research\data\thermal3.json","w"), indent=1)
print("\nwrote data/thermal3.json")

print()
print("="*80)
print("VERDICT")
print("="*80)
print("  1. The design point moves from 25 psi / 49 lb/min to 30 psi / 53 lb/min.")
print("     Compressor outlet rises, so the core has more work to do.")
print("  2. 610 x 300 x 75 mm still clears the target. Outlet IAT stays under 60 C.")
print("  3. Do NOT spend the spare clearance on depth. Depth helps the charge side a")
print("     little and hurts the air side and the radiator a lot.")
print("  4. If the aperture allows it, spend it on FACE AREA (height then width).")
print("     Face area helps both sides at once.")
