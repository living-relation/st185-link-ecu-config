"""Emit the JS data block that the report's new charts consume."""
import math, json
exec(open(r"C:\projects\5sgte-intercooler-research\rpm_sensitivity.py").read().split("# ================================================================== REPORT")[0])

VE = lambda r: ve_mach(r, 50.0, 6200.0, 1.6)      # headline: likely backpressure
REDL = [6650, 7200, 7800, 8400]

rows = []
for name, choke, prcap, dt, mat, ar, brg, price, dc in TURBOS:
    rec = {"n":name,"choke":choke,"pr":prcap,"dt":dt,"mat":mat,"ar":ar,"brg":brg,
           "price":price,"dc":dc,"spool":SPOOL[name],
           "j1":round(inertia_turbine_only(dt,mat),3),
           "j2":round(inertia_with_compressor(dt,mat,dc),3),"r":{}}
    for rpm in REDL:
        ve = VE(rpm); bpr = boost_for_pr(prcap)
        fpr,_ = flow_lbmin(rpm,bpr,ve); fch = choke*0.95
        if fpr <= fch: lim,f,b = "PR",fpr,bpr
        else:
            lim,f = "choke",fch
            b = boost_for_flow(fch,rpm,VE)
        rec["r"][rpm] = {"lim":lim,"lb":round(f,1),"b":round(b,1),
                         "whp":round(f*10*0.82),"pr":round(pressure_ratio(b),2)}
    cross = None
    for rpm in range(6000,9001,25):
        fpr,_ = flow_lbmin(rpm, boost_for_pr(prcap), VE(rpm))
        if fpr > choke*0.95: cross = rpm; break
    rec["cross"] = cross
    # continuous power-vs-rpm curve for the chart
    curve = []
    for rpm in range(5500,8601,100):
        ve = VE(rpm); bpr = boost_for_pr(prcap)
        f,_ = flow_lbmin(rpm,bpr,ve)
        curve.append([rpm, round(min(f,choke*0.95)*10*0.82)])
    rec["curve"] = curve
    rows.append(rec)

vecurves = {"rpm":[], "r1":[], "m10":[], "m16":[], "m20":[], "Z":[], "mps":[]}
for rpm in range(5000,8701,100):
    vecurves["rpm"].append(rpm)
    vecurves["r1"].append(round(ve_round1(rpm),4))
    vecurves["m10"].append(round(ve_mach(rpm,50,6200,1.0),4))
    vecurves["m16"].append(round(ve_mach(rpm,50,6200,1.6),4))
    vecurves["m20"].append(round(ve_mach(rpm,50,6200,2.0),4))
    vecurves["Z"].append(round(mach_index(rpm,50.0),4))
    vecurves["mps"].append(round(mean_piston_speed(rpm),2))

boostcurves = {}
for whp in [400,450,500,550,600]:
    lb = whp/0.82/10.0
    boostcurves[whp] = [[rpm, round(boost_for_flow(lb,rpm,VE),1)] for rpm in range(5500,8601,100)]

data = {"turbos":rows,"ve":vecurves,"boost":boostcurves,"redlines":REDL,
        "pamb":round(P_AMB,2)}
js = "var TD=" + json.dumps(data, separators=(",",":")) + ";"
open(r"C:\projects\5sgte-intercooler-research\data\chartdata.js","w").write(js)
print("wrote data/chartdata.js  (%d bytes)" % len(js))
print()
print("HEADLINE TABLE (VE with EMAP/IMAP = 1.6)")
print("  turbo                 " + "".join("| %-17s" % f"{r} rpm" for r in REDL) + "| crossover")
for r in rows:
    line = "  %-21s" % r["n"]
    for rpm in REDL:
        d = r["r"][rpm]
        line += "| %4d whp %4.1f %-5s" % (d["whp"], d["b"], d["lim"])
    line += "| %s" % (r["cross"] or ">9000")
    print(line)
print()
print("GAINS from raising the redline")
for r in rows:
    a,b,c = r["r"][6650]["whp"], r["r"][7200]["whp"], r["r"][7800]["whp"]
    print("  %-21s 6650=%4d  7200=%4d (%+d, %+.1f%%)  7800=%4d (%+d)"
          % (r["n"],a,b,b-a,(b/a-1)*100,c,c-a))
