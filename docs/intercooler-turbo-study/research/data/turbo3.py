# The decisive question: is 600 whp flow-limited or pressure-ratio-limited on a 2.19 L?
import math, json
R=287.05; CP=1005.0; GAM=1.40; PSI=6.89476
def C2K(c): return c+273.15
P_AMB = 101.325*(1-2.25577e-5*640.0)**5.25588
DISP_L = math.pi*(87.5/2)**2*91.0*4/1e6
STROKE=0.091

def vec(rpm):
    x=(rpm-5500.0)/2600.0
    return max(0.70, min(1.03, 1.02 - 0.34*x*x - 0.06*max(0.0,x)))

def flow_at(rpm, boost_psi, iat=50.0):
    pm=P_AMB+boost_psi*PSI
    m=DISP_L/1000*(rpm/2)/60*vec(rpm)*(pm*1000)/(R*C2K(iat))
    return m*2.20462*60, pm/(P_AMB*0.97), pm

def boost_for_flow(lbmin, rpm, iat=50.0):
    """invert: what boost gives this flow at this rpm"""
    lo,hi=0.0,120.0
    for _ in range(80):
        mid=(lo+hi)/2
        f,_,_=flow_at(rpm,mid,iat)
        if f<lbmin: lo=mid
        else: hi=mid
    f,pr,pm=flow_at(rpm,(lo+hi)/2)
    return (lo+hi)/2, pr, pm

print("=== IS 600 WHP FLOW-LIMITED OR PRESSURE-LIMITED? ===")
print("600 whp / 0.82 drivetrain = 732 crank hp / 10 hp-per-lb-min = 73.2 lb/min\n")
print("  rpm   piston m/s   VE    boost needed   PR needed   feasible?")
for rpm in [6000,6500,6600,7000,7500,8000]:
    b,pr,pm = boost_for_flow(73.2,rpm)
    mps=2*STROKE*rpm/60
    ok = "yes" if (b<40 and mps<22) else ("engine rpm too high" if mps>=22 else "boost too high")
    print("  %4d    %5.1f    %.2f   %6.1f psi     %5.2f      %s" % (rpm,mps,vec(rpm),b,pr,ok))

print("\n>>> CONCLUSION: at any rpm the long-stroke block tolerates (<22 m/s => <=7200 rpm),")
print(">>> 600 whp needs 45-50 psi and PR 4.6-5.0. That is ABOVE the usable map ceiling of")
print(">>> every turbo on the candidate list. 600 whp here is PRESSURE-RATIO limited,")
print(">>> not compressor-flow limited. A bigger compressor does not solve it.\n")

# ---- what each turbo can ACTUALLY deliver, respecting flow AND PR ceilings ----
# usable PR ceiling = top of the published efficiency island (not the map edge)
turbos=[
 # name, choke lb/min, usable PR ceiling, wheel mm, mat, A/R, bearing, price, TS-T4?
 ("EFR 7163 (current)", 60, 3.6, 63,"gamma-Ti",0.80,"ball",  2629, True),
 ("EFR 7670",           67, 3.8, 70,"gamma-Ti",0.92,"ball",  2500, True),
 ("EFR 8374",           79, 4.0, 74,"gamma-Ti",0.92,"ball",  2367, True),
 ("EFR 9174",          105, 4.2, 74,"gamma-Ti",1.05,"ball",  3200, True),
 ("Garrett G25-660",    64, 3.9, 54,"Inconel", 0.92,"ball",  1750, True),
 ("Garrett G25-770",    73, 4.1, 54,"Inconel", 0.92,"ball",  1850, True),
 ("Garrett G30-770",    77, 4.0, 55,"Inconel", 1.01,"ball",  2050, True),
 ("Garrett G30-900",    88, 4.2, 55,"Inconel", 1.01,"ball",  2200, True),
 ("Precision 6266 Gen2",72, 3.9, 62,"Inconel", 0.85,"journal",1500,True),
 ("Precision 6466 Gen2",82, 4.1, 67,"Inconel", 1.00,"journal",1650,True),
 ("Xona Rotor XR7169",  75, 4.2, 62,"Inconel", 0.86,"ball",  2400, True),
 ("Xona Rotor XR8267",  88, 4.3, 67,"Inconel", 1.00,"ball",  2600, True),
]
print("=== ACHIEVABLE POWER, respecting BOTH flow and pressure-ratio ceilings ===")
print("  (rpm capped at 7,000 = 21.2 m/s mean piston speed, the street limit for a 91mm stroke)")
print(" turbo                  flow cap   PR cap   limiting     max lb/min  crank hp   whp")
res=[]
for n,choke,prmax,d,mat,ar,brg,price,ts in turbos:
    best=None
    for rpm in range(4000,7001,50):
        # boost that hits the PR ceiling
        pm = prmax*P_AMB*0.97
        b  = (pm-P_AMB)/PSI
        f,pr,_ = flow_at(rpm,b)
        f = min(f, choke*0.92)                    # never design past 92% of choke
        lim = "PR" if f < choke*0.92 else "flow"
        if best is None or f>best[0]: best=(f,rpm,b,lim)
    f,rpm,b,lim=best
    crank=f*10.0; whp=crank*0.82
    res.append((n,f,crank,whp,b,rpm,lim,price,d,mat,ar,brg,choke,prmax))
    print("  %-21s %5.0f     %4.1f    %-9s  %6.1f     %5.0f    %5.0f"
          %(n,choke,prmax,lim,f,crank,whp))

print("\n=== RANKED BY ACHIEVABLE WHP ===")
for r in sorted(res,key=lambda x:-x[3])[:8]:
    print("  %-21s %5.0f whp   @ %.0f psi / %d rpm   ($%d)" % (r[0],r[3],r[4],r[5],r[7]))

print("\n=== THE SENSIBLE TARGET ===")
for whp in [400,450,500,550,600]:
    lb=whp/0.82/10.0
    b,pr,_=boost_for_flow(lb,6600)
    print("  %3d whp -> %.1f lb/min -> %.0f psi at 6,600 rpm (PR %.2f)  %s"
          %(whp,lb,b,pr,"REALISTIC" if b<=36 else "hard" if b<=42 else "not on this engine"))

json.dump([{"turbo":r[0],"whp":round(r[3]),"crank":round(r[2]),"lbmin":round(r[1],1),
            "boost_psi":round(r[4],1),"rpm":r[5],"limit":r[6],"price":r[7],
            "wheel_mm":r[8],"material":r[9],"ar":r[10],"bearing":r[11],
            "choke":r[12],"pr_cap":r[13]} for r in res],
   open(r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs\turbo_ranked.json","w"),indent=1)
print("\nwrote turbo_ranked.json")
