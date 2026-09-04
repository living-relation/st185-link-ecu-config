# 600 whp requirement analysis for the 2.19 L 5S-GTE, and candidate turbo screening
import math

R=287.05; CP=1005.0; GAM=1.40; PSI=6.89476
def C2K(c): return c+273.15
P_AMB = 101.325*(1-2.25577e-5*640.0)**5.25588   # kPa at 2100 ft
BORE=87.5; STROKE=91.0
DISP_CC = math.pi*(BORE/2)**2*STROKE*4/1000.0
DISP_L  = DISP_CC/1000.0
print("=== ENGINE ===")
print("bore %.1f mm x stroke %.1f mm x 4 = %.1f cc = %.3f L" % (BORE,STROKE,DISP_CC,DISP_L))
print("site pressure %.2f kPa (640 m)" % P_AMB)

print("\n=== MEAN PISTON SPEED (the rpm ceiling nobody talks about) ===")
print(" rpm    m/s     ft/min   assessment")
for rpm in [6500,7000,7500,8000,8500,9000]:
    mps = 2*(STROKE/1000)*rpm/60
    a = ("comfortable" if mps<20 else "street limit" if mps<22 else
         "race only" if mps<25 else "grenade")
    print(" %4d  %5.1f   %6.0f   %s" % (rpm,mps,mps*196.85,a))

def mdot_for_power(whp, drivetrain_loss, hp_per_lbmin):
    crank = whp/(1-drivetrain_loss)
    return crank, crank/hp_per_lbmin          # crank hp, lb/min

def boost_needed(lbmin, rpm, ve, iat_C, disp_L=DISP_L):
    m = lbmin/(2.20462*60)                     # kg/s
    vdot = disp_L/1000*(rpm/2)/60*ve           # m3/s
    rho = m/vdot
    p_abs = rho*R*C2K(iat_C)/1000.0            # kPa
    return p_abs, p_abs-P_AMB, (p_abs-P_AMB)/PSI, p_abs/(P_AMB*0.97)

print("\n=== WHAT 600 WHP ACTUALLY REQUIRES ===")
print("AWD ST185 drivetrain loss: 18% typical for All-Trac (transfer case + centre diff + 2 diffs)")
print("E85 specific output: 10.0 hp per lb/min (rich, high-latent-heat, ~9.5-10.5 realistic)\n")
for whp in [450,500,550,600,650]:
    crank, lbmin = mdot_for_power(whp, 0.18, 10.0)
    print("  %3d whp -> %4.0f crank hp -> %.1f lb/min" % (whp,crank,lbmin))

print("\nBoost required for 600 whp (70.7 lb/min) vs rpm, VE=0.95, IAT=50 C:")
crank, LB600 = mdot_for_power(600, 0.18, 10.0)
print("  rpm   piston m/s   MAP abs   boost psi    PR     verdict")
for rpm in [6500,7000,7500,8000,8500]:
    pa,pg,psi,pr = boost_needed(LB600, rpm, 0.95, 50)
    mps = 2*(STROKE/1000)*rpm/60
    v = "OK" if psi<35 else ("hard" if psi<42 else "unrealistic")
    print("  %4d   %6.1f     %6.0f    %6.1f    %5.2f   %s" % (rpm,mps,pa,psi,pr,v))

print("\nSame, but VE=1.00 (ported head, good cams, well-tuned):")
for rpm in [7000,7500,8000]:
    pa,pg,psi,pr = boost_needed(LB600, rpm, 1.00, 50)
    print("  %4d rpm  MAP %.0f kPa  boost %.1f psi  PR %.2f" % (rpm,pa,psi,pr))

print("\n=== WHAT EACH CANDIDATE CAPS AT ===")
# max flow (lb/min) at choke, published; hp = flow * 10 (E85) at the wheels *0.82
cands = [
 ("EFR 6758 (smaller ref)",  49, 0.0),
 ("EFR 7163  <-- CURRENT",   60, 0.0),
 ("EFR 7670",                67, 0.0),
 ("EFR 8374",                79, 0.0),
 ("EFR 9174",               105, 0.0),
 ("Garrett G25-660",         64, 0.0),
 ("Garrett G25-770",         73, 0.0),
 ("Garrett G30-770",         77, 0.0),
 ("Garrett G30-900",         88, 0.0),
 ("Precision 6266 Gen2",     72, 0.0),
 ("Precision 6466 Gen2",     82, 0.0),
 ("Xona Rotor XR7169",       75, 0.0),
 ("Xona Rotor XR8267",       88, 0.0),
]
print(" turbo                      max lb/min   crank hp   ~whp (AWD -18%)   600whp?")
for n,f,_ in cands:
    ch = f*10.0; wh = ch*0.82
    print("  %-26s %5.0f       %5.0f      %5.0f            %s"
          % (n,f,ch,wh,"YES" if wh>=600 else "no"))

print("\n=== USABLE vs CHOKE ===")
print("Choke flow is a marketing number - efficiency there is ~62-65% and the turbo is")
print("screaming. Real design points sit at 88-92% of choke, inside the 70-76% island.")
print(" turbo                      choke   usable(0.90)   crank hp   ~whp")
for n,f,_ in cands:
    u=f*0.90; ch=u*10.0; wh=ch*0.82
    print("  %-26s %5.0f    %6.1f       %5.0f     %5.0f" % (n,f,u,ch,wh))
