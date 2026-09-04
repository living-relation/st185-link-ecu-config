import math
IN=25.4
mdot=45.7*0.45359237/60          # 45.7 lb/min design point
R=287.05
Ph,Th,muh=274000.0,453.15,2.55e-5   # hot side: 274 kPa, 180 C
Pc,Tc,muc=266000.0,335.15,2.02e-5   # cold side: 266 kPa,  62 C
rh=Ph/(R*Th); rc=Pc/(R*Tc)
LH,NBH=1.1,3      # hot run 1.1 m, 3 bends
LC,NBC=1.5,4      # cold run 1.5 m, 4 bends

def run(d_mm,rho,mu,L,nb):
    d=d_mm/1000; A=math.pi/4*d*d; v=(mdot/rho)/A
    Re=rho*v*d/mu; eps=0.0015e-3; f=0.02
    for _ in range(80): f=(-2*math.log10(eps/(3.7*d)+2.51/(Re*math.sqrt(f))))**-2
    dP=((f*L/d)+0.20*nb)*0.5*rho*v*v/6894.757
    return v*3.28084, Re, f, dP, A*1000

print("design point: mdot=%.4f kg/s | rho_hot=%.3f | rho_cold=%.3f kg/m3"%(mdot,rh,rc))
print("all diameters below are INSIDE diameters at 0.065 in wall\n")
print("%-8s %-9s | %-24s | %-24s | %s"%("OD","ID","HOT  1.1 m / 3 bends","COLD 1.5 m / 4 bends","volume"))
print("-"*104)
res={}
for od in (2.5,2.75,3.0):
    idmm=(od-0.130)*IN
    vh,_,_,ph,_=run(idmm,rh,muh,LH,NBH)
    vc,_,_,pc,A=run(idmm,rc,muc,LC,NBC)
    res[od]=(idmm,vh,ph,vc,pc,A)
    print("%-8s %-9s | %6.1f ft/s  dP %5.3f psi | %6.1f ft/s  dP %5.3f psi | %.2f L/m"
          %('%.2f in'%od,'%.2f mm'%idmm,vh,ph,vc,pc,A))
print()
print("Garrett guidance band is 200-300 ft/s; below ~100 ft/s the pipe is mostly dead volume.\n")

print("=== total pipe pressure drop, hot + cold ===")
for od in (2.5,2.75,3.0):
    idmm,vh,ph,vc,pc,A=res[od]
    print("  %.2f in : %.3f psi   (%.2f%% of 25 psi boost)"%(od,ph+pc,(ph+pc)/25*100))
print()
print("=== mixed build: 2.5 hot + 2.5 cold vs 2.5 hot + 3.0 cold ===")
print("  2.5 hot %.3f + 2.5 cold %.3f = %.3f psi"%(res[2.5][2],res[2.5][4],res[2.5][2]+res[2.5][4]))
print("  2.5 hot %.3f + 3.0 cold %.3f = %.3f psi"%(res[2.5][2],res[3.0][4],res[2.5][2]+res[3.0][4]))
print("  2.5 hot %.3f + 2.75 cold %.3f = %.3f psi"%(res[2.5][2],res[2.75][4],res[2.5][2]+res[2.75][4]))
