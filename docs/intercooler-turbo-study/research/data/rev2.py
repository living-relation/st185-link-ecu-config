# Sensitivity of the 600 whp conclusion + fuel system + NEW intercooler design point
import math, json
R=287.05; CP=1005.0; GAM=1.40; PSI=6.89476
def C2K(c): return c+273.15
def F(c): return c*9/5+32
P_AMB = 101.325*(1-2.25577e-5*640.0)**5.25588
DISP_L = math.pi*(87.5/2)**2*91.0*4/1e6
def vec(rpm):
    x=(rpm-5500.0)/2600.0
    return max(0.70,min(1.03,1.02-0.34*x*x-0.06*max(0.0,x)))
def boost_for_flow(lb,rpm,iat=50.0):
    lo,hi=0.0,140.0
    for _ in range(90):
        mid=(lo+hi)/2
        pm=P_AMB+mid*PSI
        f=DISP_L/1000*(rpm/2)/60*vec(rpm)*(pm*1000)/(R*C2K(iat))*2.20462*60
        if f<lb: lo=mid
        else: hi=mid
    pm=P_AMB+(lo+hi)/2*PSI
    return (lo+hi)/2, pm/(P_AMB*0.97)

print("=== SENSITIVITY: does the 600 whp conclusion survive optimistic assumptions? ===")
print(" drivetrain loss   hp/lb-min   lb/min needed   boost @6600   PR    verdict")
for loss in [0.12,0.15,0.18,0.21]:
    for hpl in [10.0,10.5,11.0]:
        lb=600/(1-loss)/hpl
        b,pr=boost_for_flow(lb,6600)
        v="plausible" if b<=38 else ("very hard" if b<=45 else "no")
        print("      %2d%%           %.1f          %5.1f        %5.1f psi   %.2f   %s"
              %(loss*100,hpl,lb,b,pr,v))
print("\n>>> Even at 12% loss and 11 hp/lb-min (both optimistic), 600 whp still needs 41 psi.")
print(">>> The conclusion is robust: 600 whp is not a sensible target for this engine.\n")

print("=== FUEL SYSTEM HEADROOM (E85, 1400 cc injectors, Walbro 450) ===")
# E85 stoich 9.765, BSFC ~0.62 lb/hp-hr on E85 at lambda 0.78
for whp in [400,450,480,500,600]:
    crank=whp/0.82
    lbhr = crank*0.62                       # fuel lb/hr
    cc_min = lbhr*454/60/0.785              # E85 SG 0.785 -> cc/min total
    per_inj = cc_min/4
    duty = per_inj/1400*100
    lph = cc_min*60/1000
    print("  %3d whp (%4.0f crank): fuel %5.1f lb/hr, %4.0f cc/min/inj, duty %4.1f%%, pump %5.1f L/h  %s"
          %(whp,crank,lbhr,per_inj,duty,lph,
            "OK" if duty<85 else "INJECTORS MAXED" ))
print("  Walbro 450 F90000267 at 60 psi / 13.5 V flows ~380-400 L/h on E85 (derated from 450).")

print("\n=== NEW INTERCOOLER DESIGN POINT ===")
def eps_cf(n,cr):
    if cr<=1e-6: return 1-math.exp(-n)
    return 1-math.exp((n**0.22/cr)*(math.exp(-cr*n**0.78)-1))
def solve(W,H,T,vface,boost,rpm,tamb,eta):
    pm=P_AMB+boost*PSI; pr=pm/(P_AMB*0.97)
    tc=C2K(tamb)*(1+(pr**((GAM-1)/GAM)-1)/eta)-273.15
    iat=60.0
    for _ in range(80):
        m=DISP_L/1000*(rpm/2)/60*vec(rpm)*(pm*1000)/(R*C2K(iat))
        rho=P_AMB*1000/(R*C2K(tamb)); mc=W*H*vface*rho
        Cc=mc*CP; Ch=m*CP; cmin=min(Cc,Ch); cr=cmin/max(Cc,Ch)
        A=W*H*T*900.0; U=55.0*(vface/10)**0.5
        e=eps_cf(U*A/cmin,cr)*cmin/Ch
        n=tc-e*(tc-tamb)
        if abs(n-iat)<0.005: iat=n; break
        iat=n
    return m,pr,tc,e,iat,m*CP*(tc-iat)

print("\n  OLD design point (EFR 7163, 25 psi, 2.2 L assumed):")
m,pr,tc,e,iat,Q = solve(.610,.300,.075,12.0,25,7000,32,0.74)
print("    %.1f lb/min  PR %.2f  Tcomp %.0f C  eps %.3f  IAT %.1f C (%.0f F)  Q %.1f kW"
      %(m*2.20462*60,pr,tc,e,iat,F(iat),Q/1000))

print("\n  NEW design point (EFR 8374, 36 psi, 2.189 L, eta_c 0.76 in the island):")
for lbl,W,H,T in [("CSF 8067  610x300x75",.610,.300,.075),
                  ("CSF 8047  560x300x90",.560,.300,.090),
                  ("CSF 8046  635x300x115",.635,.300,.115),
                  ("CSF 8045  635x300x90",.635,.300,.090),
                  ("bigger    700x330x90",.700,.330,.090)]:
    m,pr,tc,e,iat,Q = solve(W,H,T,12.0,36,6600,32,0.76)
    print("    %-22s %.1f lb/min PR %.2f Tcomp %.0f C eps %.3f IAT %.1f C (%.0f F) Q %.1f kW"
          %(lbl,m*2.20462*60,pr,tc,e,iat,F(iat),Q/1000))

print("\n  Worst case (44 psi, 35 C ambient, eta_c 0.72):")
for lbl,W,H,T in [("CSF 8067  610x300x75",.610,.300,.075),
                  ("CSF 8046  635x300x115",.635,.300,.115)]:
    m,pr,tc,e,iat,Q = solve(W,H,T,12.0,44,6600,35,0.72)
    print("    %-22s %.1f lb/min PR %.2f Tcomp %.0f C eps %.3f IAT %.1f C (%.0f F) Q %.1f kW"
          %(lbl,m*2.20462*60,pr,tc,e,iat,F(iat),Q/1000))

print("\n=== IS A BIGGER CORE JUSTIFIED NOW (1.5x clearance available)? ===")
print("  core                     vol L   eps    IAT C   dIAT vs 8067   mass kg   dVolume L")
base=None
for lbl,W,H,T,dens in [("CSF 8067 610x300x75",.610,.300,.075,2.05),
                       ("CSF 8047 560x300x90",.560,.300,.090,2.05),
                       ("CSF 8045 635x300x90",.635,.300,.090,2.05),
                       ("CSF 8046 635x300x115",.635,.300,.115,2.05),
                       ("CSF 8173 560x300x115",.560,.300,.115,2.05),
                       ("custom  700x330x90",.700,.330,.090,2.05)]:
    m,pr,tc,e,iat,Q = solve(W,H,T,12.0,36,6600,32,0.76)
    vol=W*H*T*1000; mass=W*H*T*1000*dens; internal=vol*0.28
    if base is None: base=(iat,internal)
    print("  %-24s %5.2f  %.3f  %5.1f      %+5.1f        %5.1f     %+5.2f"
          %(lbl,vol,e,iat,iat-base[0],mass,internal-base[1]))

print("\n=== OIL COOLER PLACEMENT PENALTY ===")
m,pr,tc,e,iat,Q = solve(.610,.300,.075,12.0,36,6600,32,0.76)
mc = .610*.300*12.0*(P_AMB*1000/(R*C2K(32)))
print("  ambient air through the IC core: %.2f kg/s" % mc)
Qoil = 9000.0     # 10-row cooler rejecting ~9 kW at sustained load
dT_pre = Qoil/(mc*CP)
print("  10-row oil cooler rejects ~%.0f kW at sustained load" % (Qoil/1000))
print("\n  OPTION A - oil cooler BEHIND the intercooler (in its shadow):")
print("    no charge-air penalty (it is downstream), but it dumps %.0f kW into air already"%(Qoil/1000))
print("    heated %.1f C by the IC -> the RADIATOR then sees +%.1f C on top of that"
      %(Q/(mc*CP), dT_pre))
print("    net: radiator inlet air = 32 + %.1f + %.1f = %.1f C"
      %(Q/(mc*CP),dT_pre,32+Q/(mc*CP)+dT_pre))
print("\n  OPTION B - oil cooler IN FRONT of / stacked with the intercooler:")
mm,prr,tcc,ee,iatt,QQ = solve(.610,.300,.075,12.0,36,6600,32+dT_pre,0.76)
print("    IC now breathes %.1f C air instead of 32 C -> outlet IAT %.1f C (was %.1f C) = +%.1f C"
      %(32+dT_pre,iatt,iat,iatt-iat))
print("    WORST option: preheats the charge air AND the radiator.")
print("\n  OPTION C - fender well or front corner, own feed, OUTSIDE the IC footprint:")
print("    zero charge-air penalty, zero radiator penalty. Costs ducting and lines.")
print("    RECOMMENDED.")
print("\n  Penalty summary: behind-IC costs the radiator +%.1f C inlet air;" % dT_pre)
print("  in-front-of-IC costs the charge +%.1f C IAT. Corner/fender costs neither."%(iatt-iat))
