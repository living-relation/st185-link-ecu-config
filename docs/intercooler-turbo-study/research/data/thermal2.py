# Part 2: heat soak thermal mass, core-volume sweep, FPI trade, verification cases
import math, json
R=287.05; CP=1005.0; GAMMA=1.4
def C2K(c): return c+273.15
P_AMB = 101325.0*(1-2.25577e-5*640.0)**5.25588

def mdot_f(disp_L, rpm, ve, map_kpa, iat_C):
    return disp_L/1000.0*(rpm/2.0)/60.0*ve*(map_kpa*1000.0)/(R*C2K(iat_C))
def Tc_f(Tin, PR, eta):
    return C2K(Tin)*(1+(PR**((GAMMA-1)/GAMMA)-1)/eta)-273.15

BOOST=25.0; TAMB=32.0; RPM=7000; VE=0.95; ETA=0.74
PMAN = P_AMB/1000 + BOOST*6.89476
PR = PMAN/(P_AMB/1000*0.97)
mdot = mdot_f(2.2,RPM,VE,PMAN,62.0)
Tc = Tc_f(TAMB,PR,ETA)

# ---- heat soak / thermal mass ----
# Core mass: bar&plate ~ 2.05 kg per L of core volume; tube&fin ~ 1.35 kg/L (aluminium+voids)
# c_p aluminium 900 J/kg-K
print("=== THERMAL MASS / HEAT SOAK ===")
print("core            vol(L)  mass(kg)  C_th(kJ/K)  dT-per-pull(C)  t63(s)@steady")
for name, W,H,T, dens in [
    ("CSF 8067 B&P 610x300x75", .610,.300,.075, 2.05),
    ("CSF 8047 B&P 560x300x90", .560,.300,.090, 2.05),
    ("CSF 8045 B&P 635x300x90", .635,.300,.090, 2.05),
    ("Tube&fin equiv 610x300x75", .610,.300,.075, 1.35),
    ("Tube&fin 610x300x90",      .610,.300,.090, 1.35),
]:
    vol=W*H*T; m=vol*1000*dens/1000*1000  # kg  (vol m3 -> L via *1000, *dens kg/L)
    m = vol*1000*dens
    Cth = m*900.0
    # one 8 s WOT pull dumps Q*t into core; assume 55% absorbed by metal (rest to air)
    Q = mdot*CP*(Tc-62.0)
    dT = 0.55*Q*8.0/Cth
    # time constant with UA_air ~ 3.0 kW/K at 25 m/s face velocity for this size
    UA = 3000.0*(vol/0.0137)
    t63 = Cth/UA
    print("%-26s %5.2f  %7.2f   %8.2f   %10.1f   %8.1f" % (name, vol*1000, m, Cth/1000, dT, t63))

# ---- core volume sweep -> outlet IAT ----
def eps_cf(NTU,Cr):
    if Cr<=1e-6: return 1-math.exp(-NTU)
    return 1-math.exp((NTU**0.22/Cr)*(math.exp(-Cr*NTU**0.78)-1))

print("\n=== CORE VOLUME SWEEP (fixed 300mm H, 75mm T, varying width) @ 12 m/s face ===")
rows=[]
for W in [0.35,0.40,0.45,0.50,0.55,0.61,0.65,0.70]:
    H,T=0.300,0.075; vol=W*H*T
    v=12.0; rho=P_AMB/(R*C2K(TAMB))
    mc=W*H*v*rho; Cc=mc*CP; Ch=mdot*CP
    Cmin=min(Cc,Ch); Cr=Cmin/max(Cc,Ch)
    A=vol*900.0; U=55.0*(v/10)**0.5
    NTU=U*A/Cmin; e=eps_cf(NTU,Cr)
    To=Tc-e*(Tc-TAMB)
    rows.append({"w_mm":round(W*1000),"vol_L":round(vol*1000,2),"eps":round(e,3),
                 "Tout_C":round(To,1),"Tout_F":round(To*9/5+32)})
    print("  W=%3.0f mm vol=%.2f L eps=%.3f Tout=%.1f C (%.0f F)"%(W*1000,vol*1000,e,To,To*9/5+32))

print("\n=== EFFECTIVENESS vs FACE VELOCITY (CSF 8067) ===")
face=[]
for v in [2,4,6,8,10,12,14,16,18,20,22,25,28]:
    W,H,T=.610,.300,.075; vol=W*H*T
    rho=P_AMB/(R*C2K(TAMB)); mc=W*H*v*rho
    Cc=mc*CP; Ch=mdot*CP; Cmin=min(Cc,Ch); Cr=Cmin/max(Cc,Ch)
    A=vol*900.0; U=55.0*(v/10)**0.5
    e=eps_cf(U*A/Cmin,Cr); To=Tc-e*(Tc-TAMB)
    face.append({"v_ms":v,"mph":round(v*2.237,1),"eps":round(e,3),"Tout_C":round(To,1)})
    print("  %4.0f m/s (%4.1f mph) eps=%.3f Tout=%.1f C"%(v,v*2.237,e,To))

print("\n=== FPI vs AIR-SIDE dP (normalised, exponent 1.0 on FPI, v^1.8) ===")
for fpi in [10,12,14,16,18,20,22]:
    dp_rel = (fpi/16.0)**1.05
    q_rel  = (fpi/16.0)**0.55
    print("  %2d FPI: dP rel %.2f  Q rel %.2f  Q/dP %.2f" % (fpi, dp_rel, q_rel, q_rel/dp_rel))

print("\n=== SYSTEM dP BUDGET (2.5 in cold, 2.25 in hot, CSF 8067) ===")
def dp_pipe(m,d_in,L,nb,p_kpa,T,f=0.02,k=0.25):
    rho=p_kpa*1000/(R*C2K(T)); d=d_in*0.0254; a=math.pi*d*d/4; v=m/(rho*a)
    return (f*L/d+nb*k)*0.5*rho*v*v/6894.76
hot = dp_pipe(mdot,2.25,1.1,3,PMAN*1.03,Tc)
cold= dp_pipe(mdot,2.50,1.5,4,PMAN,62.0)
rho_out=PMAN*1000/(R*C2K(Tc)); cfm=mdot/rho_out*2118.88
core = 1.5*(cfm/1142.0)**2*1.25
tanks= 0.35     # cast tapered tanks, side in/out, measured-typical
tot = hot+cold+core+tanks
print("  hot pipe 2.25in : %.2f psi"%hot)
print("  cold pipe 2.50in: %.2f psi"%cold)
print("  core            : %.2f psi"%core)
print("  end tanks       : %.2f psi (typical cast tapered, side-in/side-out)"%tanks)
print("  TOTAL           : %.2f psi  (%.1f%% of %.0f psi boost)"%(tot,100*tot/BOOST,BOOST))

print("\n=== OFF-DESIGN VERIFICATION CASES ===")
for label,boost,rpm,tamb,eta in [
    ("street 15psi 5000rpm 25C",15,5000,25,0.76),
    ("summer track 25psi 7000rpm 32C",25,7000,32,0.74),
    ("hot day 28psi 7500rpm 35C",28,7500,35,0.72),
    ("cool 22psi 6500rpm 15C",22,6500,15,0.76)]:
    pm = P_AMB/1000+boost*6.89476; pr=pm/(P_AMB/1000*0.97)
    tc = Tc_f(tamb,pr,eta); m=mdot_f(2.2,rpm,0.95,pm,tamb+20)
    to = tc-0.85*(tc-tamb)
    print("  %-32s mdot=%.1f lb/min PR=%.2f Tcomp=%.0fC Tout(0.85)=%.0fC (%.0fF) Q=%.1f kW"
          %(label,m*2.20462*60,pr,tc,to,to*9/5+32,m*CP*(tc-to)/1000))

json.dump({"volume_sweep":rows,"face_velocity":face},
          open(r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs\model_data.json","w"),indent=1)
print("\nwrote model_data.json")
