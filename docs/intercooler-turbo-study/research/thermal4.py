"""
Corrected core-size study. thermal3.py held core face velocity constant while
varying depth, which cannot happen: a deeper core resists airflow, so less air
gets through it. This version couples face velocity to core depth and face area,
which is the honest comparison.

Air-side model:
  The bumper aperture supplies a fixed dynamic pressure. The mass of air that
  passes through the stack is set by that pressure against the core resistance.
  Core air-side dP scales roughly as (depth) x (face velocity)^1.8 for louvered
  bar-and-plate. Solving for the velocity that balances a fixed available dP:
      v_face  proportional to  (A_ref/A_face) x (t_ref/t)^(1/1.8)
  Reference: 610x300x75 core at 8.0 m/s face velocity at 100 km/h with a sealed duct.
"""
import math, json
exec(open(r"C:\projects\5sgte-intercooler-research\thermal3.py").read().split('print("="*80)')[0])

T_REF, A_REF, V_REF = 75.0, 610*300.0, 8.0

def vface_of(w_mm, h_mm, t_mm):
    return V_REF*(A_REF/(w_mm*h_mm))*(T_REF/t_mm)**(1/1.8)

def air_mass_rel(w_mm, h_mm, t_mm):
    """air mass through the stack relative to the base core"""
    v = vface_of(w_mm, h_mm, t_mm)
    return (v*w_mm*h_mm)/(V_REF*A_REF)

BOOST, RPM = 30, 7200
opts = [("610 x 300 x  75  (24x12x3)",   610,300, 75),
        ("610 x 300 x 100  (24x12x4)",   610,300,100),
        ("610 x 300 x 115  (24x12x4.5)", 610,300,115),
        ("610 x 340 x  75",              610,340, 75),
        ("610 x 340 x 100",              610,340,100),
        ("685 x 300 x  75",              685,300, 75),
        ("685 x 340 x  75",              685,340, 75),
        ("685 x 340 x 100",              685,340,100)]

print("="*92)
print("CORE SIZE STUDY - face velocity coupled to depth and face area")
print("G25-770 at 30 psi, 7200 rpm, 32 C ambient, 640 m")
print("="*92)
print("  core                          vol L  vface m/s  eps    IAT C   dIAT   rad air   Cmin side")
base = None
rows = []
for lab,w,hh,t in opts:
    v = vface_of(w,hh,t)
    r = solve(BOOST, RPM, w, hh, t, v)
    relm = air_mass_rel(w,hh,t)
    rad_rise = r["dTrad"]
    if base is None: base = (r["iat"], rad_rise)
    rows.append({"label":lab,"w":w,"h":hh,"t":t,"vol":round(r["vol"],1),
                 "vface":round(v,2),"eps":round(r["eps"],3),"iat":round(r["iat"],1),
                 "d_iat":round(r["iat"]-base[0],1),"rad_rise":round(rad_rise,1),
                 "d_rad":round(rad_rise-base[1],1),"air_rel":round(relm,3),
                 "cmin_cold":r["cmin_cold"]})
    print("  %-29s %5.1f    %5.2f    %.3f  %5.1f  %+5.1f    %+5.1f C   %s"
          % (lab, r["vol"], v, r["eps"], r["iat"], r["iat"]-base[0],
             rad_rise-base[1], "AMBIENT (starved)" if r["cmin_cold"] else "charge (healthy)"))

print()
print("  Reading this table:")
print("   - dIAT is how much cooler the charge gets. More negative is better.")
print("   - d rad air is how much HOTTER the air reaching the radiator gets. Positive is worse.")
print("   - A core is only worth its depth if the dIAT gain beats the radiator cost.")

print()
print("="*92)
print("THE TWO REAL OTS CANDIDATES, HEAD TO HEAD, AT THE NEW DESIGN POINT")
print("="*92)
cands = [("SpeedFactory SS-850  610 x 305 x 76", 610,305, 76, 524.68),
         ("Treadstone TR1245    559 x 318 x 114", 559,318,114, 549.00)]
for lab,w,hh,t,price in cands:
    v = vface_of(w,hh,t)
    r = solve(BOOST, RPM, w, hh, t, v)
    print("  %-38s  $%.2f" % (lab, price))
    print("      core volume        %.1f L" % r["vol"])
    print("      face velocity      %.2f m/s" % v)
    print("      effectiveness      %.3f" % r["eps"])
    print("      compressor out     %.0f C" % r["tc"])
    print("      intercooler out    %.1f C  (%.0f F)" % (r["iat"], r["iat"]*9/5+32))
    print("      air heated by IC   +%.1f C onto the radiator" % r["dTrad"])
    print("      Cmin side          %s" % ("AMBIENT - core is airflow-starved" if r["cmin_cold"] else "charge - healthy"))
    print()

print("="*92)
print("HOT-DAY AND TRACK CHECK on the recommended core")
print("="*92)
W,H,T = 610,305,76
print("  condition                                    vface  IAT C   IAT F   verdict")
for lab, b, rpm, ta, vf in [
        ("100 km/h, sealed duct, 32 C", 30,7200,32.0, vface_of(W,H,T)),
        ("100 km/h, sealed duct, 40 C", 30,7200,40.0, vface_of(W,H,T)),
        ("60 km/h, sealed duct, 32 C",  30,7200,32.0, vface_of(W,H,T)*0.60),
        ("30 km/h out of a corner, 32 C",30,7200,32.0, vface_of(W,H,T)*0.30),
        ("stationary, fan only, 32 C",  30,7200,32.0, 2.0),
        ("UNDUCTED at 100 km/h, 32 C",  30,7200,32.0, vface_of(W,H,T)*0.45)]:
    r = solve(b,rpm,W,H,T,vf,tamb=ta)
    verdict = "good" if r["iat"]<70 else ("marginal" if r["iat"]<90 else "pull timing")
    print("  %-42s %5.2f  %5.1f   %5.0f   %s" % (lab, vf, r["iat"], r["iat"]*9/5+32, verdict))

json.dump({"sizes":rows}, open(r"C:\projects\5sgte-intercooler-research\data\thermal4.json","w"), indent=1)
print("\nwrote data/thermal4.json")
