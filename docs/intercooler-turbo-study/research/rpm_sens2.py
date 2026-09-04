"""Sensitivity: how much does exhaust backpressure and cam choice move the answer?
Also produces the street-boost comparison that drives the recommendation."""
import math, json
exec(open(r"C:\projects\5sgte-intercooler-research\rpm_sensitivity.py").read().split("# ================================================================== REPORT")[0])

print("="*78)
print("SENSITIVITY: VE band from exhaust backpressure (EMAP/IMAP) and cam peak")
print("="*78)
print("  rpm   | bp1.0 cam6200 | bp1.6 cam6200 | bp2.0 cam6200 | bp1.6 cam5800 | round-1")
for rpm in [6000,6650,7200,7800,8400]:
    a=ve_mach(rpm,50,6200,1.0); b=ve_mach(rpm,50,6200,1.6)
    c=ve_mach(rpm,50,6200,2.0); d=ve_mach(rpm,50,5800,1.6)
    print(f"  {rpm:5d} |    {a:.3f}      |    {b:.3f}      |    {c:.3f}      |    {d:.3f}      | {ve_round1(rpm):.3f}")

print()
print("  Power gain 6650 -> 7200 rpm under each VE assumption (PR-limited turbo, e.g. EFR 8374):")
for lab,fn in [("optimistic bp=1.0",lambda r:ve_mach(r,50,6200,1.0)),
               ("likely     bp=1.6",lambda r:ve_mach(r,50,6200,1.6)),
               ("pessimistic bp=2.0",lambda r:ve_mach(r,50,6200,2.0)),
               ("round-1 curve     ",ve_round1)]:
    b=boost_for_pr(4.0)
    f1,_=flow_lbmin(6650,b,fn(6650)); f2,_=flow_lbmin(7200,b,fn(7200))
    f3,_=flow_lbmin(7800,b,fn(7800))
    f1=min(f1,79*0.95); f2=min(f2,79*0.95); f3=min(f3,79*0.95)
    w=lambda f: f*HP_PER_LBMIN*DRIVETRAIN
    print(f"    {lab}:  {w(f1):4.0f} -> {w(f2):4.0f} whp ({w(f2)-w(f1):+5.0f}, {(f2/f1-1)*100:+5.1f}%)"
          f"   ->7800 {w(f3):4.0f} ({w(f3)-w(f1):+5.0f})")

print()
print("="*78)
print("STREET / TRACK OPERATING POINT - every turbo at the SAME boost")
print("="*78)
print("  This is the point Dan actually drives. Boost is set by what the bottom end and")
print("  the fuel tolerate, not by the compressor map.")
print()
for boost in [24,28,32]:
    print(f"  --- {boost} psi (PR {pressure_ratio(boost):.2f}) ---")
    print("    turbo                  6650 whp  7200 whp  |  spool rpm  |  headroom to choke")
    for name,choke,prcap,dt,mat,ar,brg,price,dc in TURBOS:
        r=[]
        for rpm in (6650,7200):
            f,_=flow_lbmin(rpm,boost,ve_mach(rpm,50,6200,1.6))
            r.append(min(f,choke*0.95))
        hd = (choke*0.95)/r[1]
        pr_ok = "ok" if pressure_ratio(boost)<=prcap else "OVER PR CAP"
        print("      %-21s   %4.0f      %4.0f    |   %5d    |  %4.2fx  %s"
              %(name,r[0]*10*0.82,r[1]*10*0.82,SPOOL[name],hd,pr_ok))
    print()

print("="*78)
print("HEAD-TO-HEAD: Garrett G25-770 vs BorgWarner EFR 8374 vs current EFR 7163")
print("="*78)
hh=[("EFR 7163 (current)",60,3.6,63,"g-TiAl",0.80,2629,71),
    ("Garrett G25-770",73,4.1,54,"Inconel",0.92,1850,62),
    ("EFR 8374",79,4.0,74,"g-TiAl",0.92,2367,83)]
print("  metric                    EFR 7163      G25-770       EFR 8374")
def line(lab, vals, fmt="%s"):
    print("  %-24s  %-12s  %-12s  %-12s" % (lab, fmt%vals[0], fmt%vals[1], fmt%vals[2]))
line("price USD",[2629,1850,2367],"$%d")
line("spool threshold rpm",[4000,4307,5200],"%d")
line("delta spool vs current",[0,307,1200],"%+d rpm")
line("turbine wheel mm",[63,54,74],"%d")
line("turbine material",["g-TiAl","Inconel","g-TiAl"])
line("J turbine only",[1.000,0.949,2.236],"%.3f")
line("J turbine+compressor",[1.000,0.769,2.214],"%.3f")
line("choke lb/min",[60,73,79],"%d")
line("usable PR ceiling",[3.6,4.1,4.0],"%.1f")
w=[]
for n,ch,pc,dt,mt,ar,pr_,dc in hh:
    b=boost_for_pr(pc); f,_=flow_lbmin(7200,b,ve_mach(7200,50,6200,1.6)); f=min(f,ch*0.95)
    w.append(round(f*10*0.82))
line("max whp @7200 (at PR cap)",w,"%d")
w2=[]
for n,ch,pc,dt,mt,ar,pr_,dc in hh:
    f,_=flow_lbmin(7200,28,ve_mach(7200,50,6200,1.6)); f=min(f,ch*0.95)
    w2.append(round(f*10*0.82))
line("whp @7200 @ 28 psi",w2,"%d")
print()
print("  Turbine flow check - EMAP risk. Corrected flow through the turbine at 60 lb/min:")
print("    A 54 mm turbine (G25) has less flow area than a 63 mm (7163) or 74 mm (8374).")
print("    Garrett publishes the G25 turbine as good to ~62 lb/min corrected before")
print("    backpressure climbs steeply. At 60+ lb/min the G25-770 in 0.92 A/R will run")
print("    higher EMAP than the EFR 8374. That is the real cost of its faster spool.")
