#!/usr/bin/env python3
"""Build the turbo-comparison and intercooler-report HTML from model JSON."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
IN = yaml.safe_load((HERE / "inputs.yaml").read_text())
MB = json.loads((HERE / "matchbot_results.json").read_text())
IC = json.loads((HERE / "ic_stack.json").read_text())
PW = json.loads((HERE / "power_limits.json").read_text())
AIR = json.loads((HERE / "airflow_demand.json").read_text())

CSS = """
:root{
 --bg:#0e1116; --bg2:#151a22; --card:#1a2029; --card2:#212936;
 --line:#2c3542; --tx:#e6edf5; --tx2:#9fb0c4; --tx3:#6f8098;
 --acc:#4ea3ff; --acc2:#38d39f; --warn:#ffb347; --bad:#ff6b6b;
 --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);
 font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px 90px}
header.hero{background:linear-gradient(160deg,#16202e 0%,#0e1116 70%);
 border-bottom:1px solid var(--line);padding:38px 0 30px}
.hero h1{margin:0 0 6px;font-size:30px;letter-spacing:-.4px}
.hero .sub{color:var(--tx2);max-width:820px}
.hero .meta{margin-top:12px;color:var(--tx3);font-size:12.5px;font-family:var(--mono)}
nav.toc{position:sticky;top:0;z-index:40;background:rgba(14,17,22,.94);
 backdrop-filter:blur(9px);border-bottom:1px solid var(--line);padding:9px 0}
nav.toc .wrap{display:flex;flex-wrap:wrap;gap:5px}
nav.toc a{color:var(--tx2);text-decoration:none;font-size:12.2px;padding:4px 9px;border-radius:5px}
nav.toc a:hover{background:var(--card2);color:var(--tx)}
section{margin:36px 0;scroll-margin-top:84px}
h2{font-size:22px;margin:0 0 8px}
h2 .num{color:var(--acc);font-family:var(--mono);font-size:15px;margin-right:8px}
.lede{color:var(--tx2);margin:0 0 16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:18px 20px;margin:14px 0}
.grid{display:grid;gap:12px}
.g2{grid-template-columns:1fr 1fr}
.g3{grid-template-columns:repeat(3,1fr)}
@media(max-width:860px){.g2,.g3{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:13.2px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--tx2);font-size:11.4px;text-transform:uppercase;letter-spacing:.5px;background:var(--bg2)}
td.n,th.n{text-align:right;font-family:var(--mono)}
.kpi{background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:12px 14px}
.kpi .lab{font-size:11px;color:var(--tx3);text-transform:uppercase;letter-spacing:.6px}
.kpi .val{font-size:24px;font-weight:660;font-family:var(--mono);color:var(--acc)}
.kpi .note{font-size:11.5px;color:var(--tx3)}
.callout{border-radius:9px;padding:12px 15px;margin:12px 0;border:1px solid}
.c-info{background:#0e1e2e;border-color:#1f4468;color:#c2ddf5}
.c-warn{background:#241c0c;border-color:#5a4416;color:#f4d9a4}
.c-good{background:#0d241c;border-color:#1c5240;color:#b6ecd6}
.eq{background:#101620;border-left:3px solid var(--acc);padding:10px 14px;font-family:var(--mono);font-size:13px;color:#cfe3fa}
.map{position:relative;display:inline-block;max-width:100%}
.map img{width:100%;height:auto;display:block;border-radius:8px}
.dot{position:absolute;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;
 border:2px solid #fff;font:10px/14px var(--mono);color:#081018;text-align:center;font-weight:700}
.d1{background:#4ea3ff}.d2{background:#38d39f}.d3{background:#ffb347}
.d4{background:#ff6b6b}.d5{background:#c084fc}.d6{background:#f472b6}
.note{font-size:12.5px;color:var(--tx3)}
a{color:var(--acc)}
"""

# MatchBot plots maps at 800×503; official JPEGs are ~907×653.
CAL = {
    "EFR_7064": {"xoff": 60, "yoff": 524, "xinc": 11.7, "yinc": -128, "w": 908, "h": 652, "dw": 800, "dh": 503,
                 "file": "model/maps/BorgWarner EFR 7064 Compressor Map.jpg", "code": "70s75"},
    "EFR_7163": {"xoff": 60, "yoff": 526, "xinc": 10.8, "yinc": -160.3, "w": 905, "h": 653, "dw": 800, "dh": 503,
                 "file": "model/maps/BorgWarner EFR 7163 Compressor Map.jpg", "code": "71x80"},
    "EFR_7670": {"xoff": 59, "yoff": 525, "xinc": 10.1, "yinc": -128, "w": 907, "h": 654, "dw": 800, "dh": 503,
                 "file": "model/maps/BorgWarner EFR 7670 Compressor Map.jpg", "code": "76s75"},
}


def dots_html(turbo_id, points):
    c = CAL[turbo_id]
    sx, sy = c["w"] / c["dw"], c["h"] / c["dh"]
    bits = []
    for i, p in enumerate(points, 1):
        lb = float(p["cor_lbmin"])
        pr = float(p["cpr"])
        left = (c["xoff"] + c["xinc"] * lb) * sx / c["w"] * 100
        top = (c["yoff"] + c["yinc"] * pr - c["yinc"]) * sy / c["h"] * 100
        bits.append(
            f'<span class="dot d{i}" style="left:{left:.2f}%;top:{top:.2f}%" title="P{i} {p["rpm"]} rpm">{i}</span>'
        )
    return "\n".join(bits)


def map_card(turbo_id, points):
    c = CAL[turbo_id]
    return f"""
<div class="card">
<h3>{turbo_id.replace('_', ' ')} — official BorgWarner map ({c['code']})</h3>
<div class="map">
<img src="{c['file']}" alt="{turbo_id} official compressor map">
{dots_html(turbo_id, points)}
</div>
<p class="note">Dots are the six MatchBot operating points (3000/15 → 8000/27).
Calibration is MatchBot's own xoff/xinc/yoff/yinc for this compressor, scaled
from the 800×503 display size to the official JPEG.</p>
</div>"""


def table(headers, rows):
    th = "".join(f'<th class="n">{h}</th>' if i else f"<th>{h}</th>" for i, h in enumerate(headers))
    body = []
    for row in rows:
        tds = []
        for i, cell in enumerate(row):
            cls = ' class="n"' if i else ""
            tds.append(f"<td{cls}>{cell}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="card"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def write_turbo():
    pts = MB["runs"][0]["points"]
    curve = PW["matchbot_curve"]
    rec = PW["turbo_fit"]["recommendation"]
    rows = []
    for p, c in zip(pts, curve):
        rows.append([
            f'{p["rpm"]} / {p["boost"]}',
            p["cor_lbmin"], p["cpr"], p["ce"],
            c["iat_c"], p["emp_psi"], p["dp_psi"], p["phi"], p["wg_pct"],
            c["pump_crank_bhp_matchbot"], c["e85_crank_bhp"], c["e85_whp"],
        ])
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EFR 7064 / 7163 / 7670 — MatchBot + official maps</title>
<style>{CSS}</style></head><body>
<header class="hero"><div class="wrap">
<h1>EFR 7064 vs 7163 vs 7670</h1>
<p class="sub">Official BorgWarner compressor maps with this 2.189 L 5S-GTE's
operating line. Turbine match from live MatchBot, using the tool's own field
help — not guessed TER / VE / BSFC.</p>
<p class="meta">ST185 · 2189 cc · HKS 264 · CR 8.5 · sea level · Pump-Gas
MatchBot case (E85 power from airflow × 11 hp/lb-min) · 2026-09-09</p>
</div></header>
<nav class="toc"><div class="wrap">
<a href="#verdict">Verdict</a><a href="#maps">Maps</a>
<a href="#matchbot">MatchBot table</a><a href="#method">Method</a>
<a href="intercooler-report.html">Intercooler report</a>
</div></nav>
<div class="wrap">
<section id="verdict">
<h2><span class="num">01</span>Verdict</h2>
<div class="grid g3">
<div class="kpi"><div class="lab">7064</div><div class="val" style="color:var(--bad)">No</div>
<div class="note">55 lb/min is the published 56 lb/min wall. Choke.</div></div>
<div class="kpi"><div class="lab">7163-G (current)</div><div class="val">Keep</div>
<div class="note">Road-car pick. Right side of a 60 lb/min map at redline. Mixed-flow 63 mm, 0.80 T4 twin.</div></div>
<div class="kpi"><div class="lab">7670-C</div><div class="val" style="color:var(--warn)">If top-end</div>
<div class="note">64 lb/min map still has island at 55 / PR 3.0. More inertia. Drive PDF's first pick.</div></div>
</div>
<div class="callout c-info">{rec}</div>
</section>
<section id="maps">
<h2><span class="num">02</span>Official maps + this engine's line</h2>
<p class="lede">These JPEGs are BorgWarner's MatchBot / catalog maps, not redraws.
{map_card("EFR_7064", pts)}
{map_card("EFR_7163", pts)}
{map_card("EFR_7670", pts)}
</section>
<section id="matchbot">
<h2><span class="num">03</span>MatchBot operating line</h2>
<p class="lede">Single turbo, 2.189 L, 75 °F, 0 ft, Pump Gas. VE is breathing VE
(90–105%). Restrictions square-law from 1.5 / 0.5 / 2.0 psi peak. CE left at
defaults then read off the islands. TE includes the official 10–15% twin-scroll
bonus at low rpm. TER set so engine dP matches the catalog example
(+6…−4 psi) and every point has a real wastegate fraction (no N/A, no NaN).
PHI 0.020–0.035 sits inside the EFR housing band (0.020–0.048). Wastegate
25–32% is inside the 40% internal-gate design intent. Port demand 16–23 mm
vs 36 mm on the C/G housings.</p>
{table(
    ["rpm / psi", "corr lb/min", "PR", "CE%", "IAT °C", "EMP psi", "dP", "PHI", "WG%",
     "pump crank", "E85 crank", "E85 WHP"],
    rows,
)}
<p class="note">Engine-side airflow/power is compressor-independent until CE is
refined from the islands. The maps above are what actually differentiates the
three turbos. MatchBot pump-gas hp uses official gasoline BSFC/AFR (the E85
dropdown overwrites VE — do not use it; see matchbot_procedure.md).</p>
</section>
<section id="method">
<h2><span class="num">04</span>Method</h2>
<div class="card">
<ul>
<li>Field help copied from MatchBot <code>?</code> pop-ups and <code>bot.js</code> v1.4.</li>
<li>Official maps: <a href="https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7064-b.pdf">7064-B</a>,
<a href="https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7163-f.pdf">7163-F</a>,
<a href="https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7670-b.pdf">7670-B</a>.</li>
<li>Inputs: <code>model/inputs.yaml</code>, case <code>model/matchbot_case.yaml</code>.</li>
<li>Driver: <code>model/run_matchbot.mjs</code> against the live tool.</li>
<li>Prior Drive PDF used 2164 cc / 7500 rpm and picked 7670-C. This run is 2189 cc / 8000 rpm and agrees on ranking.</li>
</ul>
</div>
</section>
</div></body></html>
"""
    dest = STUDY / "turbo-comparison.html"
    dest.write_text(html)
    print("wrote", dest)


def write_ic_report():
    pick = IC["pick"]
    cores = IC["cores_at_60mph"]
    soak = IC["soak_at_idle_4_5in"]
    rad = IC["radiator"]
    h = PW["headline"]
    kn = PW["knock"]
    pts = PW["matchbot_curve"]

    core_rows = [[
        f"{c['kind']} {c['thick_in']} in",
        c["effectiveness"], c["t_out_c"], c["charge_dp_psi"],
        c["metal_kg"], c["tau_recover_s"], c["tau_soak_s"], c["q_kw"],
    ] for c in cores]

    mb_rows = [[
        f'{p["rpm"]} / {p["boost_psi"]}',
        p["cor_lbmin"], p["pump_crank_bhp_matchbot"], p["e85_crank_bhp"], p["e85_whp"],
        p["iat_c"], p["dp_psi"],
    ] for p in pts]

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>5S-GTE ST185 — Intercooler, front stack, calculated power</title>
<style>{CSS}</style></head><body>
<header class="hero"><div class="wrap">
<h1>Intercooler, front stack, calculated power</h1>
<p class="sub">Rebuilt from one input file, official EFR maps, a valid MatchBot
turbine match, and a heat-exchanger model. Power is calculated. 91 and 93 MY
are mechanically identical.</p>
<p class="meta">ECU Link G4X XtremeX · Walbro F90000295 · flex DI 2 ·
turbo EFR 7163-G current · 2026-09-09</p>
</div></header>
<nav class="toc"><div class="wrap">
<a href="#headlines">Headlines</a>
<a href="#power">Power</a>
<a href="#turbo">Turbo</a>
<a href="#ic">Intercooler</a>
<a href="#stack">Front stack</a>
<a href="#pipes">Pipes</a>
<a href="#sources">Sources</a>
<a href="turbo-comparison.html">Map overlays</a>
</div></nav>
<div class="wrap">
<section id="headlines">
<h2><span class="num">01</span>Headlines</h2>
<div class="grid g3">
<div class="kpi"><div class="lab">E85 peak (calculated)</div>
<div class="val g">{h['e85_crank_bhp']} / {h['e85_whp']}</div>
<div class="note">crank BHP / WHP @ {h['e85_peak_rpm']} rpm / {h['e85_peak_boost_psi']} psi. 17% AWD loss.</div></div>
<div class="kpi"><div class="lab">Pump-gas MatchBot</div>
<div class="val">{h['pump_crank_bhp_matchbot']} / {h['pump_whp_matchbot']}</div>
<div class="note">crank / wheel at 6000 rpm / 30 psi using official gasoline BSFC.</div></div>
<div class="kpi"><div class="lab">Core pick</div>
<div class="val">4.5 in TF</div>
<div class="note">Tube-and-fin, ~27×12 in face. Bar-plate is the time-attack core, not the road-car core.</div></div>
</div>
<div class="callout c-warn">30 psi is the <b>max boost</b>, not a required operating point.
Street seed stays 18 psi. Redline is a band (7200–8000), not a single number.
93 pump is knock-limited around 22 psi until a logged pull says otherwise.
E85 is hardware-limited (turbo choke / IAT / turbine dP), not octane-limited.
Water/meth engages at ≥27 psi to hold that boost farther into the band.</div>
</section>

<section id="power">
<h2><span class="num">02</span>Calculated power</h2>
<p class="lede">Two methods, same air. Phase 1 is VE × CID × PR (eroded VE at
8000 = 0.82). MatchBot is the live tool with breathing VE 90–105% and
density-after-IC. They agree at the top: ~55 lb/min.</p>
{table(["rpm / psi", "corr lb/min", "pump crank", "E85 crank", "E85 WHP", "IAT °C", "engine dP"], mb_rows)}
<div class="grid g2">
<div class="card"><h3>93 pump</h3>
<p>{kn['pump_93']['why']}</p>
<p>Planning ceiling: <b>{kn['pump_93']['planning_boost_ceiling_psi']} psi</b>.</p></div>
<div class="card"><h3>E85 + water/meth ≥27 psi</h3>
<p>{kn['e85']['why']}</p>
<p>{kn['e85']['water_meth_effect']}</p></div>
</div>
<div class="eq">mdot = VE · (CID · RPM / 2 / 1728) · ρ · PR
crank = mdot · (10 hp/lb-min on 93, 11 on E85)
wheel = crank · (1 − 0.17)</div>
</section>

<section id="turbo">
<h2><span class="num">03</span>Turbo</h2>
<p class="lede">Full overlays live in <a href="turbo-comparison.html">turbo-comparison.html</a>.
Short version:</p>
<div class="grid g3">
<div class="card"><b>7064</b> — wrong compressor. 55 lb/min vs 56 published.</div>
<div class="card"><b>7163-G</b> — keep for a road car. 0.80 T4 twin, mixed-flow 63 mm. Redline point is on the right side of the map, not off it.</div>
<div class="card"><b>7670-C</b> — step up if you want 30 psi held to 7500+ in the island. Prior Drive PDF first pick, still valid on 2189 cc / 8000 rpm.</div>
</div>
<div class="callout c-good">Valid turbine match: PHI 0.020–0.035, wastegate 25–32%,
port 16–23 mm, engine dP +6 to −4 psi. The first MatchBot pass that used
blind All+ produced N/A wastegate and −35 dP — that run is discarded. See
<code>model/matchbot_procedure.md</code>.</div>
</section>

<section id="ic">
<h2><span class="num">04</span>Bar-plate vs tube-and-fin</h2>
<p class="lede">Same 27×12 in face, same 55 lb/min charge, same 60 mph stack
airflow. The difference is the core, not the size. Effectiveness is calibrated
into MatchBot's official "typical IC" high-speed band (85–90%). Thermal mass
and recovery come from aluminum volume × Cp / UA.</p>
{table(["core", "ε", "T_out °C", "dP psi", "metal kg", "recover s", "soak s", "Q kW"], core_rows)}
<div class="callout c-info">{pick['why']}</div>
<div class="grid g2">
<div class="card"><h3>Idle / traffic soak (4.5 in)</h3>
<p>Bar-plate {next(c for c in cores if c['kind']=='bar_plate' and c['thick_in']==4.5)['metal_kg']} kg
vs tube-fin {next(c for c in cores if c['kind']=='tube_fin' and c['thick_in']==4.5)['metal_kg']} kg.
After a pull the thicker metal store keeps heating the next charge slug until
ram air returns. Recovery τ is
{next(c for c in cores if c['kind']=='tube_fin' and c['thick_in']==4.5)['tau_recover_s']} s
tube-fin vs
{next(c for c in cores if c['kind']=='bar_plate' and c['thick_in']==4.5)['tau_recover_s']} s
bar-plate at 60 mph — the road-car number that matters,
because you are not at WOT 95% of the lap.</p></div>
<div class="card"><h3>What 4–5 in buys</h3>
<p>3 in tube-fin drops to ~61% ε on this face at 55 lb/min — too thin. 4.0–4.5 in
is where tube-fin enters the 85% band. 5 in still helps bar-plate more than
tube-fin (diminishing NTU). 4.5 in is the pick: fits the crash-bar depth the
user allowed, without paying bar-plate soak.</p></div>
</div>
</section>

<section id="stack">
<h2><span class="num">05</span>Front stack</h2>
<p class="lede">Order, front to back: {", ".join(pick['stack_order_front_to_back'])}.</p>
<div class="grid g2">
<div class="card"><h3>Half-width condenser</h3>
<p>60 mph radiator air: half-width <b>{rad['road_60mph']['half_condenser']['air_kg_s']} kg/s</b>
({rad['road_60mph']['half_condenser']['vs_need']}× need) vs full-width
{rad['road_60mph']['full_condenser']['air_kg_s']} kg/s
({rad['road_60mph']['full_condenser']['vs_need']}×). The half-width unit sits
passenger-side so the driver-side rad face sees ram air. A full condenser in
front of a racing rad is how these cars overheat with the AC on.</p></div>
<div class="card"><h3>Radiator + fans</h3>
<p>{pick['radiator']}. Two-row aluminum, Celica / 5S-class. Slim PWM pair
behind the core, not a thick OE clutch fan. Oil and trans coolers live
<i>off</i> the rad face (low in the opening or ducted) so they do not eat
the remaining air.</p></div>
</div>
</section>

<section id="pipes">
<h2><span class="num">06</span>Pipes and throttle body</h2>
<p class="lede">Unchanged recommendation from <a href="THROTTLE-BODY-PLUMBING-SPEC.md">THROTTLE-BODY-PLUMBING-SPEC.md</a>
— the clamp does not force 3 in through the whole system.</p>
<div class="grid g2">
<div class="kpi"><div class="lab">Hot side</div><div class="val">2.50 in</div>
<div class="note">OD × 0.065 wall. Past the turbine in the tight bay. ~0.44 psi over the run.</div></div>
<div class="kpi"><div class="lab">Cold side</div><div class="val">3.00 in</div>
<div class="note">SpeedFactory SS-850 outlet and Outsider Garage TB adapter are already 3 in. No transitions. Welded 3 in is slimmer than clamped 2.5 in.</div></div>
</div>
<p>End tanks: {pick['end_tanks']}.</p>
</section>

<section id="sources">
<h2><span class="num">07</span>Sources and what this replaces</h2>
<div class="card">
<ul>
<li><code>tune/engine_constants.yaml</code> — 2189 cc, 87.5×91, CR 8.5, HKS 264, F90000295, 7163-G, 8000 rev limit.</li>
<li>BorgWarner MatchBot field help + official EFR map PDFs / JPEGs.</li>
<li>Kays &amp; London NTU-ε; Incropera Colburn j/f (calibrated to MatchBot's 85–90% IC band).</li>
<li>Head-flow notes in <code>docs/5sgte-project-data/</code>.</li>
<li>This report replaces the previous six-way-inconsistent intercooler HTML
(FuryX leftovers, 25 vs 30 psi, 3 vs 4 in, 404 vs 600 hp). The
<code>research/</code> byte-identical copy is removed. Working calcs stay in
<code>model/</code>.</li>
</ul>
</div>
</section>
</div></body></html>
"""
    dest = STUDY / "intercooler-report.html"
    dest.write_text(html)
    print("wrote", dest)


if __name__ == "__main__":
    write_turbo()
    write_ic_report()
