import math
mdot=45.7*0.45359237/60; R=287.05
Ph,Th,muh=274000.0,453.15,2.55e-5
Pc,Tc,muc=266000.0,335.15,2.02e-5
rh=Ph/(R*Th); rc=Pc/(R*Tc)
def stat(d_mm,rho,mu,L,nb):
    d=d_mm/1000; A=math.pi/4*d*d; v=(mdot/rho)/A
    Re=rho*v*d/mu; eps=0.0015e-3; f=0.02
    for _ in range(80): f=(-2*math.log10(eps/(3.7*d)+2.51/(Re*math.sqrt(f))))**-2
    return v, Re, f, ((f*L/d)+0.20*nb)*0.5*rho*v*v/6894.757, A
plate=74.5
print('mdot=%.4f kg/s  rho_hot=%.4f  rho_cold=%.4f kg/m3'%(mdot,rh,rc))
print()
for w in [0.049,0.065,0.083]:
    idin=3.000-2*w; idmm=idin*25.4
    step=plate-idmm; ar=(plate/idmm)**2
    vh,Reh,fh,ph,_=stat(idmm,rh,muh,1.1,3)
    vc,Rec,fc,pc,A=stat(idmm,rc,muc,1.5,4)
    be=0.5*rc*vc**2*(1-(idmm/plate)**2)**2/6894.757
    print('wall %.3f in -> ID %.4f in = %.2f mm | step to 74.5 plate = +%.2f mm (%.2f/side, area +%.1f%%)'%(w,idin,idmm,step,step/2,(ar-1)*100))
    print('   hot  v=%.1f ft/s (%.1f m/s) Re=%.0f f=%.4f dP=%.3f psi'%(vh*3.28084,vh,Reh,fh,ph))
    print('   cold v=%.1f ft/s (%.1f m/s) Re=%.0f f=%.4f dP=%.3f psi | HOT+COLD=%.3f psi'%(vc*3.28084,vc,Rec,fc,pc,ph+pc))
    print('   Borda-Carnot expansion loss at plate step = %.5f psi | volume %.3f L/m'%(be,A*1000))
print()
for od,w,lab in [(2.5,0.065,'2.50 OD x .065'),(2.5,0.083,'2.50 OD x .083')]:
    d=(od-2*w)*25.4
    vh,_,_,ph,_=stat(d,rh,muh,1.1,3); vc,_,_,pc,A=stat(d,rc,muc,1.5,4)
    print('BASELINE %s: ID %.2f mm | hot %.1f ft/s | cold %.1f ft/s | dP %.3f psi | vol %.3f L/m'%(lab,d,vh*3.28084,vc*3.28084,ph+pc,A*1000))
print()
print('Area error if you size on OD not ID:')
print('  3.00 OD .065: %.1f%% ;  2.50 OD .065: %.1f%%'%(((76.2/72.898)**2-1)*100,((63.5/60.198)**2-1)*100))
print('Plate bore 74.5 mm = %.4f in ; 74.0 mm = %.4f in'%(74.5/25.4,74.0/25.4))
for w in [0.049,0.065,0.083]:
    print('  3.000 - 2*%.3f = %.4f in = %.3f mm'%(w,3.000-2*w,(3.000-2*w)*25.4))
