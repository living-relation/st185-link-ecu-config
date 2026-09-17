"""Builds data/chartdata_r4.js - the data block embedded in the round-four report."""
import json, os, math, io, contextlib
import unified_model_r4 as M

HERE = os.path.dirname(os.path.abspath(__file__))

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    out = M.main()
CONSOLE = buf.getvalue()

R4 = {}
R4["const"] = out["const"]
R4["hero"] = out["hero"]
R4["rpmRange"] = out["rpm_range"]
R4["ladder"] = out["ladder"]
R4["cores"] = out["cores"]
R4["pipes"] = out["pipes"]
R4["tb"] = out["tb"]
R4["tbRange"] = out["tb_range"]
R4["coldLayouts"] = out["cold_layouts"]
R4["coldTransitions"] = out["cold_transitions"]
R4["routing"] = out["routing"]
R4["routingDeltaBox"] = out["routing_delta_box"]
R4["hotLayouts"] = out["hot_layouts"]
R4["budget"] = out["budget"]
R4["stack"] = out["stack"]
R4["duty"] = out["duty"]
R4["driveline"] = out["driveline"]
R4["community"] = out["community"]
R4["officialPoints"] = out["official_points"]
R4["officialSolved"] = out["official_solved"]
R4["surgeSweep"] = out["surge_sweep"]
R4["radPenalty"] = out["rad_penalty"]
R4["etaRms"] = out["eta_rms"]
R4["pairing"] = out["pairing"]
R4["windows"] = out["windows"]
R4["bp"] = out["backpressure"]
R4["modelPerL"] = out["model_per_l"]
R4["rad"] = out["rad"]

# ---- power / airflow / charge temp as continuous functions of rpm -------------
c = out["curves"]
R4["curves"] = dict(rpm=c["rpm"], b20=c["b20"], b25=c["b25"], b30=c["b30"],
                    b32=c["b32"], b34=c["b34"],
                    b30lo=c["b30_lo"], b30hi=c["b30_hi"],
                    iat30=c["iat30"], lb30=c["lb30"], ve30=c["ve30"])

# ---- official 7163 compressor map, rebuilt as drawable geometry --------------
off = M.OFFICIAL["EFR 7163"]
mapd = dict(surge=off["surge"], choke=off["choke"],
            prAxis=off["pr_axis"], flowAxis=off["flow_axis"],
            speedLines=off["speed_lines"], contours=off["eff_contours"],
            labels=off["eff_labels"], peak=off["eff_peak"],
            peakAt=off["eff_peak_at"], topPr=off["map_top_pr"],
            pdf=off["pdf"], rms=out["eta_rms"],
            compInd=off["comp_ind"], compOd=off["comp_od"])

# efficiency grid so the report can draw the fitted islands
gf = [x for x in range(4, 67, 2)]
gp = [round(1.0 + 0.1 * i, 2) for i in range(0, 33)]
grid = []
for p in gp:
    row = []
    for f in gf:
        row.append(round(M.official_eff_7163(f, p), 4))
    grid.append(row)
mapd["gridF"] = gf
mapd["gridP"] = gp
mapd["grid"] = grid

# operating locus: 30 psi from 2,500 to 8,000 rpm
locus = []
for rpm in range(2500, 8001, 100):
    o = M.operating_point(rpm, 30.0, 0.706)
    locus.append([rpm, round(o["lb"], 2), round(o["pr"], 3)])
mapd["locus30"] = locus
# and a rpm-scheduled boost target that stays out of surge
sched = []
for rpm in range(2000, 8001, 250):
    tgt = 30.0
    for b in [x * 0.5 for x in range(4, 61)]:
        o = M.operating_point(rpm, b, 0.706)
        s = M.interp_xy(off["surge"], min(o["pr"], 4.0))
        if o["lb"] - s >= 4.0:
            tgt = min(30.0, b)
    # walk up from low boost until surge margin is lost
    best = 0.0
    for b in [x * 0.5 for x in range(4, 61)]:
        o = M.operating_point(rpm, b, 0.706)
        s = M.interp_xy(off["surge"], min(o["pr"], 4.0))
        if o["lb"] - s >= 4.0 and b <= 30.0:
            best = b
    sched.append([rpm, round(best, 1)])
mapd["surgeSafeBoost"] = sched
R4["map"] = mapd

# ---- packaging geometry for the dimensioned drawing --------------------------
R4["pack"] = dict(
    radOverall=M.RAD["overall_mm"], radCore=M.RAD["core_mm"],
    radPart=M.RAD["part"], radRows=M.RAD["rows"],
    condThick=M.COND_THICK,
    gapLo=M.GAP_IC_RAD[0], gapHi=M.GAP_IC_RAD[1],
    icW=610, icH=305,
)

js = "var R4=" + json.dumps(R4, separators=(",", ":")) + ";\n"
with open(os.path.join(HERE, "data", "chartdata_r4.js"), "w") as f:
    f.write(js)
with open(os.path.join(HERE, "data", "r4_console.txt"), "w") as f:
    f.write(CONSOLE)
print("wrote data/chartdata_r4.js  (%d bytes)" % len(js))
print("wrote data/r4_console.txt")
