"""Emit data/chartdata_r3.js - the round-three data block the report consumes."""
import json, os, math, sys
HERE = "/sessions/amazing-blissful-bell/mnt/projects/5sgte-intercooler-research"
sys.path.insert(0, HERE)
from unified_model import *

D = {}

# ---- 1. VE curves, all three, at the unified charge temperature ----------
ve = {"rpm": [], "prior": [], "report": [], "unified": [], "Z": [], "mps": [], "r1": []}
def ve_round1(rpm):
    x = (rpm-5500.0)/2600.0
    return max(0.70, min(1.03, 1.02 - 0.34*x*x - 0.06*max(0.0, x)))
for rpm in range(4500, 8201, 100):
    o = operating_point(rpm, 30.0, 0.706)
    ve["rpm"].append(rpm)
    ve["prior"].append(round(ve_prior(rpm), 4))
    ve["report"].append(round(ve_report(rpm, o["iat"]), 4))
    ve["unified"].append(round(o["ve"], 4))
    ve["r1"].append(round(ve_round1(rpm), 4))
    ve["Z"].append(round(mach_index(rpm, o["iat"]), 4))
    ve["mps"].append(round(mean_piston_speed(rpm), 2))
D["ve"] = ve

# ---- 2. power vs rpm: the three models side by side ---------------------
pw = {"rpm": [], "prior": [], "report": [], "unified": []}
K_PRIOR = 0.0029233
for rpm in range(3500, 8201, 100):
    o = operating_point(rpm, 30.0, 0.706)
    # prior research method: standard density x PR, sea level, 9.35 whp/lb-min
    f_prior = K_PRIOR*rpm*ve_prior(rpm)*((30+14.7)/14.7)
    f_prior = min(f_prior, 60.0)
    # report round-two method: fixed 50 C charge, 8.20 whp/lb-min
    p_man = P_AMB + 30*PSI
    rho50 = p_man*1000.0/(R*323.15)
    f_rep = DISP*(rpm/2.0)/60.0*ve_report(rpm, 50.0)*rho50*LBMIN
    f_rep = min(f_rep, 60.0*0.95)
    pw["rpm"].append(rpm)
    pw["prior"].append(round(f_prior*9.35))
    pw["report"].append(round(f_rep*8.20))
    pw["unified"].append(round(o["whp"]))
D["power"] = pw

# ---- 3. constant sensitivity grid ---------------------------------------
hero = operating_point(7500, 30.0, 0.706)
D["hero"] = dict(rpm=7500, lb=round(hero["lb"], 2), whp=round(hero["whp"]),
                 iat=round(hero["iat"], 1), pr=round(hero["pr"], 2),
                 tc=round(hero["tc"]), eps=round(hero["eps"], 3),
                 choke=round(hero["lb"]/60*100, 1), crank=round(hero["crank"]))
grid = []
for hp in (9.5, 10.0, 10.5, 11.0):
    grid.append([hp] + [round(hero["lb"]*hp*dt) for dt in (0.78, 0.80, 0.82, 0.85)])
D["sens"] = dict(grid=grid, dts=[0.78, 0.80, 0.82, 0.85],
                 lb=round(hero["lb"], 2))

# ---- 4. boost ladder for the 7163 ---------------------------------------
lad = []
for boost in (20, 22, 25, 28, 30, 32, 34):
    o = operating_point(7500, boost, 0.706)
    lad.append(dict(boost=boost, lb=round(o["lb"], 2), whp=round(o["whp"]),
                    iat=round(o["iat"], 1), pr=round(o["pr"], 2),
                    choke=round(o["lb"]/60*100, 1), over=o["pr"] > 3.6))
D["ladder"] = lad

# ---- 5. turbos on one model ---------------------------------------------
tr = []
for t in TURBOS:
    o30 = operating_point(7500, 30.0, t["eta_ref"])
    lb30 = min(o30["lb"], t["choke"]*0.98)
    best = None
    for b in [x*0.5 for x in range(40, 101)]:
        oc = operating_point(7500, b, t["eta_ref"])
        if oc["pr"] > t["pr_max"] or oc["lb"] > t["choke"]*0.98: break
        best = oc
    best = best or o30
    tr.append(dict(n=t["n"], choke=t["choke"], eta=round(t["eta_ref"], 3),
                   pr_max=t["pr_max"], spool=t["spool"], price=t["price"],
                   src=t["src"], dt=t["dt"], dc=t["dc"],
                   whp30=round(lb30*WHP_PER_LBMIN), iat30=round(o30["iat"], 1),
                   whpmax=round(best["whp"]), boostmax=round(best["boost"], 1),
                   ghost=("G25-770" in t["n"])))
D["turbos"] = tr

# ---- 6. cores ------------------------------------------------------------
cr = []
for k, c in CORES.items():
    o = operating_point(7500, 30.0, 0.706, core=c)
    vol = c["w"]*c["h"]*c["t"]*1000
    cr.append(dict(k=k, label=c["label"], vol=round(vol, 1), vf=round(o["vf"], 2),
                   eps=round(o["eps"], 3), iat=round(o["iat"], 1),
                   iatF=round(o["iat"]*9/5+32), whp=round(o["whp"]),
                   dTrad=round(o["dTrad"], 1), mass=round(vol*0.30, 1),
                   w=round(c["w"]*1000), h=round(c["h"]*1000), t=round(c["t"]*1000),
                   depthNeed=round(c["t"]*1000)+35))
D["cores"] = cr

# ---- 7. exhaust pulse windows -------------------------------------------
FIRE = {1: 0, 3: 180, 4: 360, 2: 540}
EVO, DUR = 135.0, 264.0
wins = {}
for c in (1, 2, 3, 4):
    s = (FIRE[c]+EVO) % 720.0
    segs = []
    a, b = s, s+DUR
    if b <= 720: segs.append([a, b])
    else: segs += [[a, 720], [0, b-720]]
    wins[str(c)] = segs
D["pulse"] = dict(win=wins, dur=DUR, evo=EVO, fire={str(k): v for k, v in FIRE.items()},
                  wrong=[[1, 2, 84], [3, 4, 84]], right=[[1, 4, 96], [2, 3, 96]])

# ---- 8. backpressure sweep ----------------------------------------------
bp = []
for emap in [1.0+0.1*i for i in range(0, 16)]:
    o = operating_point(7500, 30.0, 0.706,
                        ve_fn=lambda r, i, e=emap: ve_unified(r, i, emap=e))
    bp.append([round(emap, 2), round(o["ve"], 4), round(o["whp"])])
D["bp"] = bp

# ---- 9. spool comparison (modelled) -------------------------------------
def spool_curve(rpm, onset, target, width=1200):
    t = max(0.0, min(1.0, (rpm-(onset-width))/width))
    return target*(t*t*(3-2*t))
sp = {"rpm": [], "right": [], "wrong": []}
for rpm in range(2000, 6001, 100):
    sp["rpm"].append(rpm)
    sp["right"].append(round(spool_curve(rpm, 4000, 30.0), 2))
    sp["wrong"].append(round(spool_curve(rpm, 4400, 30.0), 2))
D["spool"] = sp

D["const"] = dict(disp=round(DISP*1e6, 1), pamb=round(P_AMB, 2), tamb=T_AMB,
                  hp=HP_PER_LBMIN, dt=DRIVETRAIN, whplb=round(WHP_PER_LBMIN, 2),
                  rodratio=round(ROD_RATIO, 3))

js = "var R3=" + json.dumps(D, separators=(",", ":")) + ";"
open(os.path.join(HERE, "data", "chartdata_r3.js"), "w").write(js)
print("wrote data/chartdata_r3.js  (%d bytes)" % len(js))
print("hero:", D["hero"])
print("cores:")
for c in D["cores"]:
    print("  %-24s vol %5.1f L  vf %4.2f  eps %.3f  IAT %5.1f C / %3d F  whp %3d  dTrad %4.1f  needs %d mm"
          % (c["k"], c["vol"], c["vf"], c["eps"], c["iat"], c["iatF"], c["whp"], c["dTrad"], c["depthNeed"]))
print("turbos:")
for t in D["turbos"]:
    print("  %-22s 30psi %3d whp  IAT %4.1f  ceiling %3d whp @ %4.1f psi  spool %d"
          % (t["n"], t["whp30"], t["iat30"], t["whpmax"], t["boostmax"], t["spool"]))
