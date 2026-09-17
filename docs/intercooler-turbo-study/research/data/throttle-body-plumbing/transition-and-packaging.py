import math
IN=25.4
mdot=45.7*0.45359237/60; R=287.05
Pc,Tc=266000.0,335.15; rc=Pc/(R*Tc)

def vel(d_mm,rho=rc):
    A=math.pi/4*(d_mm/1000)**2
    return (mdot/rho)/A, A

print("=== TRANSITION CONE 2.5 -> 3.0 in, cold side, 0.065 wall ===")
d1=(2.5-0.130)*IN; d2=(3.0-0.130)*IN
v1,A1=vel(d1); v2,A2=vel(d2)
print("  inlet  ID %.2f mm  v %.1f ft/s"%(d1,v1*3.28084))
print("  outlet ID %.2f mm  v %.1f ft/s"%(d2,v2*3.28084))
for inc in (7,10,14):
    half=math.radians(inc/2)
    L=((d2-d1)/2)/math.tan(half)
    print("  %2d deg included -> cone length %.1f mm (%.2f in)"%(inc,L,L/IN))
# loss: sudden expansion (Borda-Carnot) vs shallow conical diffuser
sud=0.5*rc*v1**2*(1-A1/A2)**2/6894.757
print("\n  sudden step 2.5->3.0, no cone : %.4f psi"%sud)
for inc,K in ((7,0.14),(10,0.20),(14,0.30)):
    print("  conical diffuser, %2d deg incl : %.4f psi   (K=%.2f x ideal)"%(inc,K*sud,K))
print("\n  For reference, whole cold pipe at 2.5 in = 0.446 psi")
print("  So a 7 deg cone costs %.2f%% of the cold-side pipe loss."%(0.14*sud/0.446*100))

print("\n=== PACKAGING: outside diameter that must clear ===")
print("%-34s %-12s %-12s"%("item","mm","in"))
for od in (2.5,2.75,3.0):
    print("%-34s %-12.1f %-12.2f"%("bare welded pipe, %.2f in OD"%od, od*IN, od))
print()
# silicone coupler: 4-ply aramid wall ~5.5 mm
for od in (2.5,3.0):
    print("%-34s %-12.1f %-12.2f"%("+ 4-ply silicone coupler (%.1f in)"%od, od*IN+2*5.5, (od*IN+11)/IN))
for od in (2.5,3.0):
    print("%-34s %-12.1f %-12.2f"%("+ coupler + T-bolt clamp band (%.1f in)"%od, od*IN+2*5.5+2*3.0, (od*IN+17)/IN))
print()
print("T-bolt clamp trunnion/bolt sticks out a further ~20-25 mm on ONE side only.")
