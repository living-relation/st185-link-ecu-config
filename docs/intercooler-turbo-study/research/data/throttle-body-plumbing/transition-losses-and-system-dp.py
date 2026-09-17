import math
IN=25.4
mdot=45.7*0.45359237/60; R=287.05
rc=266000/(R*335.15); rh=274000/(R*453.15)
def v(d_mm,rho):
    A=math.pi/4*(d_mm/1000)**2; return (mdot/rho)/A, A
d25=(2.5-0.130)*IN; d275=(2.75-0.130)*IN; d30=(3.0-0.130)*IN

print("=== COLD SIDE: 3.0 in IC outlet -> 2.5 in pipe -> 3.0 in throttle adapter ===")
v3,A3=v(d30,rc); v25,A25=v(d25,rc)
# contraction into the pipe at the intercooler outlet
Ksharp=0.5*(1-A25/A3)
dp_sharp=Ksharp*0.5*rc*v25**2/6894.757
print("  1) contraction 3.0 -> 2.5 at IC outlet")
print("     sharp-edged, K=%.3f          : %.4f psi"%(Ksharp,dp_sharp))
for inc,K in ((30,0.06),(20,0.04),(14,0.03)):
    print("     conical %2d deg incl, K=%.2f    : %.4f psi"%(inc,K,K*0.5*rc*v25**2/6894.757))
# expansion back out at the throttle
sud=0.5*rc*v25**2*(1-A25/A3)**2/6894.757
print("  2) expansion 2.5 -> 3.0 at throttle")
print("     sudden step                   : %.4f psi"%sud)
print("     7 deg cone (K=0.14)           : %.4f psi"%(0.14*sud))
tot=0.03*0.5*rc*v25**2/6894.757 + 0.14*sud
print("  both transitions done properly    : %.4f psi TOTAL"%tot)
print()
print("=== SYSTEM PRESSURE DROP against the 1.5 psi target ===")
core=0.18; tanks=0.35
opts=[("2.5 hot + 2.5 cold (welded, 2 transitions)",0.442,0.446,tot),
      ("2.5 hot + 3.0 cold (welded, 0 cold transitions)",0.442,0.198,0.0),
      ("2.75 hot + 2.75 cold",0.288,0.291,tot),
      ("3.0 hot + 3.0 cold",0.196,0.198,0.0)]
for name,ph,pc,tr in opts:
    t=ph+pc+tr+core+tanks
    print("  %-48s %.2f psi  (%.1f%% of 25 psi)"%(name,t,t/25*100))
print()
print("=== hot side: EFR 2.0 in outlet -> pipe -> 3.0 in IC inlet ===")
for od,lab in ((2.5,'2.5 in'),(3.0,'3.0 in')):
    dp=(od-0.130)*IN
    vv,AA=v(dp,rh)
    print("  %s pipe: %.1f ft/s ; expansion from 2.0 in comp outlet is a step UP either way"%(lab,vv*3.28084))
