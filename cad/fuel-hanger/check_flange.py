import os, sys, json, math
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import *
import fuel_hanger as h
import os
S = os.path.dirname(os.path.abspath(__file__)) + "/"
f = import_step(S + "fuel-hanger-flange.step")
out = {}
sol = f.solids(); out["solids"] = len(sol); out["valid"] = f.is_valid
v0 = h.flange().volume; out["vol_model_cm3"] = round(v0/1000, 3); out["vol_step_cm3"] = round(f.volume/1000, 3)
out["roundtrip_dvol_pct"] = round(abs(f.volume - v0)/v0*100, 4)
def holes(z):
    s = f & (Pos(h.C[0], h.C[1], z) * Box(200, 200, 0.02)); r = set()
    for fc in s.faces():
        if abs(fc.normal_at().Z) < 0.9: continue
        for w in fc.inner_wires():
            bb = w.bounding_box(); r.add((round(bb.size.X, 2), round((bb.min.X+bb.max.X)/2, 1), round((bb.min.Y+bb.max.Y)/2, 1)))
    return r
a, b, c = holes(h.Z_OUT + 0.2), holes(h.Z_OUT + h.PLATE_T/2), holes(h.SEAL_Z - 0.2)
k = lambda s: {(x, y) for _, x, y in s}
th = sorted([t for t in b if (t[1], t[2]) in k(a) and (t[1], t[2]) in k(c)], key=lambda t: -t[0])
out["through_holes"] = len(th); out["through_list"] = th
out["outside_face_openings"] = len(a)
st = import_step(S + "fuel-hanger-strut.step"); cv = import_step(S + "fuel-hanger-check_valve_radium_20-0598.step")
out["valve_to_strut_mm"] = round(cv.distance_to(st), 2); out["valve_to_flange_mm"] = round(cv.distance_to(f), 2)
out["flange_strut_gap"] = round(f.distance_to(st), 3); out["flange_strut_overlap_mm3"] = round(((f & st).volume if (f & st) is not None else 0.0), 3)
# M6 holes aligned: strut hole and upright hole coaxial -> check line through both is clear
for u in (-h.LUG_W/2+8, h.LUG_W/2-8):
    p0 = h.W(u, -h.STRUT_T-h.LUG_T-2, h.SEAL_Z+h.LUG_H/2+3); p1 = h.W(u, 2, h.SEAL_Z+h.LUG_H/2+3)
    cyl = Solid.make_cylinder(2.5, (p1-p0).length, Plane(origin=p0, z_dir=(p1-p0).normalized()))
    i1 = f & cyl; i2 = st & cyl
    out[f"m6_u{u:+.0f}_bolt_path_overlap_mm3"] = [round(i1.volume,3) if i1 else 0.0, round(i2.volume,3) if i2 else 0.0]
bb = f.bounding_box(); out["bbox"] = [round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2)]
out["mass_g_6061"] = round(f.volume*2.70e-3, 1)
json.dump(out, open(S + "checks_revH.json", "w"), indent=1, default=str); print(json.dumps(out, indent=1, default=str))
