# -*- coding: utf-8 -*-
"""Inject the round-three reconciliation and manifold sections into the report,
and correct every downstream number, chart and calculator default."""
import os, re, json, io

HERE = "/sessions/amazing-blissful-bell/mnt/projects/5sgte-intercooler-research"
REPORT = os.path.join(HERE, "intercooler-report.html")
html = io.open(REPORT, encoding="utf-8").read()
r3js = io.open(os.path.join(HERE, "data", "chartdata_r3.js"), encoding="utf-8").read()
D = json.loads(r3js[len("var R3="):-1])

orig_len = len(html)
def must(old, new, n=1, label=""):
    global html
    c = html.count(old)
    assert c == n, "PATCH FAIL [%s]: found %d, expected %d\n%r" % (label, c, n, old[:120])
    html = html.replace(old, new)

# ====================================================================
# 1. TOC
# ====================================================================
must('<a href="#sources">Sources</a><a href="#open">Open Questions</a>',
     '<a href="#recon" style="color:#ffb347">Reconciliation</a>'
     '<a href="#manifold" style="color:#ffb347">Manifold</a>'
     '<a href="#sources">Sources</a><a href="#open">Open Questions</a>',
     label="toc")

# ====================================================================
# 2. Executive summary - round three banner
# ====================================================================
old_banner = '''<div class="callout c-bad" style="margin-top:14px"><b>Round two, August 2026 &mdash; read &sect;16 first.</b>'''
new_banner = '''<div class="callout c-bad" style="margin-top:14px">
<b>Round three, 30 August 2026 &mdash; read <a href="#recon">&sect;21</a> before anything else.</b>
A body of earlier turbo research was supplied after this report was written. Reconciling the two
changed five conclusions:
<b>(1)</b> The power number falls to <b>404 whp</b> at 7,500 rpm and 30 psi. Both earlier answers
(this report's 420&ndash;480, the prior research's 466&ndash;517) were built on constants that do not
survive checking. <a href="#recon">&sect;21.1</a>
<b>(2)</b> The <b>Garrett G25-770 recommendation is withdrawn.</b> That part does not appear in
Garrett's catalogue, and at the boost this engine will actually run it would buy nothing anyway.
<b>Keep the EFR 7163 you already own.</b> <a href="#recon">&sect;21.7</a>
<b>(3)</b> The core grows from 76 mm to <b>102 mm deep</b>. Worth 9 &deg;C and 7 whp, and you have
the clearance. <a href="#recon">&sect;21.8</a>
<b>(4)</b> Your <b>twin-scroll manifold is paired wrong</b> &mdash; 1+2 / 3+4 instead of 1+4 / 2+3.
Independently verified. It costs roughly 7 whp and 400 rpm of spool. <a href="#manifold">&sect;22</a>
<b>(5)</b> The <b>wastegate solenoid must be fed pre-throttle</b>, not from the manifold distribution
block. <a href="#recon">&sect;21.11</a></div>

<div class="callout c-warn" style="margin-top:10px"><b>Round two, August 2026 &mdash; read &sect;16 first.</b>'''
must(old_banner, new_banner, label="summary banner")

# ---- recommended specification block --------------------------------
must('<div class="specline"><span class="k">Core size (W &times; H &times; T)</span><span class="v">610 &times; 300 &times; 75&nbsp;mm &nbsp;(24 &times; 12 &times; 3&nbsp;in)</span></div>',
     '<div class="specline"><span class="k">Core size (W &times; H &times; T)</span>'
     '<span class="v">610 &times; 305 &times; <b>102</b>&nbsp;mm &nbsp;(24 &times; 12 &times; 4&nbsp;in) '
     '<span class="note">&mdash; revised in &sect;21.8</span></span></div>',
     label="spec core size")

must('<div class="specline"><span class="k">Predicted outlet IAT</span><span class="v">52&ndash;57&nbsp;&deg;C (126&ndash;135&nbsp;&deg;F) at 25&nbsp;psi, 32&nbsp;&deg;C ambient, 60&nbsp;mph</span></div>',
     '<div class="specline"><span class="k">Predicted outlet IAT</span>'
     '<span class="v">70&nbsp;&deg;C (157&nbsp;&deg;F) at 30&nbsp;psi, 32&nbsp;&deg;C ambient, 60&nbsp;mph '
     '<span class="note">&mdash; 79 &deg;C on the 76 mm core</span></span></div>',
     label="spec IAT")

must('<div class="specline"><span class="k">Turbo</span><span class="v">Garrett G25-770, 0.92 A/R turbine housing, ~$1,850</span></div>',
     '<div class="specline"><span class="k">Turbo</span><span class="v">'
     '<s style="opacity:.5">Garrett G25-770, 0.92 A/R, ~$1,850</s> &nbsp;&rarr;&nbsp; '
     '<b>keep the EFR 7163 you own</b> <span class="note">(&sect;21.7)</span></span></div>',
     label="spec turbo")

# ---- KPI tiles -------------------------------------------------------
old_kpi = '''<div class="grid g4">
<div class="kpi"><div class="lab">Peak air mass flow</div><div class="val">45.7</div>
<div class="note">lb/min &mdash; 25 psi, 7000 rpm, 32 &deg;C</div></div>
<div class="kpi"><div class="lab">Compressor outlet temp</div><div class="val w">180</div>
<div class="note">&deg;C (356 &deg;F) at PR 2.92, &eta;<sub>c</sub> 0.74</div></div>
<div class="kpi"><div class="lab">Heat to reject</div><div class="val">40</div>
<div class="note">kW (137,000 BTU/hr) at &epsilon; = 0.80</div></div>
<div class="kpi"><div class="lab">Turbo headroom</div><div class="val g">76%</div>
<div class="note">45.7 of the EFR 7163's 60 lb/min</div></div>
</div>'''
new_kpi = '''<div class="grid g4">
<div class="kpi"><div class="lab">Peak air mass flow</div><div class="val">%(lb).1f</div>
<div class="note">lb/min &mdash; 30 psi, 7,500 rpm, 32 &deg;C, charge-temp coupled</div></div>
<div class="kpi"><div class="lab">Wheel horsepower</div><div class="val">%(whp)d</div>
<div class="note">whp on E85 &mdash; %(crank)d crank. Band 384&ndash;424. &sect;21.1</div></div>
<div class="kpi"><div class="lab">Compressor outlet temp</div><div class="val w">%(tc)d</div>
<div class="note">&deg;C (%(tcF)d &deg;F) at PR %(pr).2f, &eta;<sub>c</sub> 0.706</div></div>
<div class="kpi"><div class="lab">Turbo headroom</div><div class="val g">%(choke).0f%%</div>
<div class="note">%(lb).1f of the EFR 7163's 60 lb/min &mdash; it is not used up</div></div>
</div>''' % dict(lb=D["hero"]["lb"], whp=D["hero"]["whp"], crank=D["hero"]["crank"],
                 tc=D["hero"]["tc"], tcF=round(D["hero"]["tc"]*9/5+32),
                 pr=D["hero"]["pr"], choke=D["hero"]["choke"])
must(old_kpi, new_kpi, label="kpi tiles")

# ====================================================================
# 3. Round-two recommendation block in section 17 -> mark superseded
# ====================================================================
must('<h3>Round-two recommendation</h3>',
     '<div class="callout c-bad"><b>Superseded by &sect;21.</b> The block below is kept so the change '
     'is visible. Every number in it was computed with a fixed 50&nbsp;&deg;C charge temperature and '
     '10.0&nbsp;&times;&nbsp;0.82 hp per lb/min. &sect;21 solves charge temperature simultaneously with '
     'airflow and revises the drivetrain factor to 0.80.</div>\n<h3>Round-two recommendation</h3>',
     label="17 rec superseded")

# ====================================================================
# 4. NEW SECTION 21 - RECONCILIATION
# ====================================================================
def turbo_rows():
    out = []
    for t in D["turbos"]:
        ghost = t["ghost"]
        keep = t["n"].startswith("EFR 7163")
        cls = ' style="background:rgba(255,107,107,.07)"' if ghost else (
              ' style="background:rgba(56,211,159,.07)"' if keep else '')
        nm = t["n"] + (' <span class="pill p-bad">not a real part</span>' if ghost else
                       (' <span class="pill p-ok">keep this</span>' if keep else ''))
        out.append(
          '<tr%s><td>%s</td><td class="num">%d</td><td class="num">%.3f</td>'
          '<td class="num">%d</td><td class="num">%.0f &deg;C</td><td class="num">%d</td>'
          '<td class="num">%.1f psi</td><td class="num">%d</td><td class="note">%s</td></tr>'
          % (cls, nm, t["choke"], t["eta"], t["whp30"], t["iat30"], t["whpmax"],
             t["boostmax"], t["spool"], t["src"]))
    return "\n".join(out)

def core_rows():
    out = []
    base = [c for c in D["cores"] if c["t"] == 76 and c["w"] == 610][0]
    for c in D["cores"]:
        pick = (c["w"] == 610 and c["t"] == 102)
        wide = (c["w"] == 711)
        cls = ' style="background:rgba(56,211,159,.09)"' if pick else (
              ' style="background:rgba(255,107,107,.07)"' if wide else '')
        tag = (' <span class="pill p-ok">recommended</span>' if pick else
               (' <span class="pill p-bad">too wide</span>' if wide else ''))
        d_iat = c["iat"]-base["iat"]; d_whp = c["whp"]-base["whp"]
        d_rad = c["dTrad"]-base["dTrad"]
        out.append(
          '<tr%s><td>%d &times; %d &times; %d<br><span class="note">%s</span>%s</td>'
          '<td class="num">%.1f L</td><td class="num">%.2f m/s</td><td class="num">%.3f</td>'
          '<td class="num">%.1f &deg;C<br><span class="note">%d &deg;F</span></td>'
          '<td class="num" style="color:%s">%+.1f</td>'
          '<td class="num">%d</td><td class="num" style="color:%s">%+d</td>'
          '<td class="num" style="color:%s">%+.1f &deg;C</td>'
          '<td class="num">%d mm</td></tr>'
          % (cls, c["w"], c["h"], c["t"], c["label"], tag, c["vol"], c["vf"], c["eps"],
             c["iat"], c["iatF"],
             "#4fe0aa" if d_iat < 0 else "#9fb0c4", d_iat,
             c["whp"], "#4fe0aa" if d_whp > 0 else "#9fb0c4", d_whp,
             "#ff8f8f" if d_rad > 1 else "#9fb0c4", d_rad,
             c["depthNeed"]))
    return "\n".join(out)

def ladder_rows():
    out = []
    for l in D["ladder"]:
        over = l["over"]
        cls = ' style="background:rgba(255,107,107,.07)"' if over else (
              ' style="background:rgba(56,211,159,.09)"' if l["boost"] == 30 else '')
        v = ('<span class="pill p-bad">past the 7163\'s PR ceiling of 3.6</span>' if over else
             ('<span class="pill p-ok">design point</span>' if l["boost"] == 30 else
              '<span class="pill p-info">within the map</span>'))
        out.append('<tr%s><td class="num">%d</td><td class="num">%.2f</td><td class="num">%.1f</td>'
                   '<td class="num">%.0f%%</td><td class="num">%.0f &deg;C</td>'
                   '<td class="num"><b>%d</b></td><td>%s</td></tr>'
                   % (cls, l["boost"], l["pr"], l["lb"], l["choke"], l["iat"], l["whp"], v))
    return "\n".join(out)

def sens_rows():
    out = []
    for row in D["sens"]["grid"]:
        hp = row[0]
        cells = ""
        for i, dt in enumerate(D["sens"]["dts"]):
            v = row[i+1]
            mark = ""
            if hp == 10.0 and dt == 0.80: mark = ' style="background:rgba(56,211,159,.18);font-weight:700"'
            elif hp == 11.0 and dt == 0.85: mark = ' style="background:rgba(255,107,107,.18)"'
            elif hp == 10.0 and dt == 0.82: mark = ' style="background:rgba(255,179,71,.14)"'
            cells += '<td class="num"%s>%d</td>' % (mark, v)
        note = {9.5: "pessimistic BSFC", 10.0: "<b>resolved</b>", 10.5: "optimistic",
                11.0: "prior research"}[hp]
        out.append('<tr><td class="num">%.1f</td>%s<td class="note">%s</td></tr>' % (hp, cells, note))
    return "\n".join(out)

SEC21 = '''
<!-- ============ 21 RECONCILIATION ============ -->
<section id="recon">
<h2><span class="num">21</span>Reconciliation &mdash; this report vs the prior turbo research</h2>
<p class="lede">A body of earlier turbo work was supplied after this report was finished:
a shared physics model (<code>06_turbo_model.py</code>), five data files, a cylinder-head flow
reference, and fifteen charts. All of it is preserved in
<code>data/prior-turbo-research/</code>. It contradicts this report in places, and in three places
it contradicts itself. This section works through every disagreement, says which side is right,
and shows the arithmetic.</p>

<div class="callout c-info"><b>How to read this section.</b> Each item states the disagreement,
the resolution, and the evidence. Where the two bodies of work cannot be separated from the data
available, that is said plainly rather than resolved by preference. Terms are defined in brackets
on first use.</div>

<h3 id="r210">21.0 &nbsp;The single error that explains most of the gap</h3>
<p class="note">Before the item-by-item list, one finding underlies items 1, 2, 3 and 9.
<code>06_turbo_model.py</code> computes airflow as</p>
<div class="eq">lb/min = K &times; RPM &times; VE &times; PR       K = 0.0029233,  PR = (boost + 14.7) / 14.7</div>
<p class="note">Rebuilding K from its parts shows what it contains:
<code>K = (2164&nbsp;cc &divide; 2) &times; 0.0765&nbsp;lb/ft&sup3;</code>. That density,
0.0765&nbsp;lb/ft&sup3;, is dry air at <b>15&nbsp;&deg;C and sea level</b>. Multiplying it by
pressure ratio and nothing else means the model is assuming the air arriving at the intake valve
is at 15&nbsp;&deg;C, at every boost level, forever.</p>

<div class="callout c-bad"><b>The prior model has no charge temperature in it and no altitude in it.</b>
Working the implied manifold temperature back out of <code>K &times; PR</code> returns exactly
15&nbsp;&deg;C at 20, 25 and 30 psi alike. The real charge temperature at this car's design point
is about <b>79&nbsp;&deg;C</b> after a 610&nbsp;&times;&nbsp;305&nbsp;&times;&nbsp;76&nbsp;mm core
at 32&nbsp;&deg;C ambient. Air at 79&nbsp;&deg;C is <b>18% less dense</b> than air at 15&nbsp;&deg;C.
The prior model also uses 14.7 psi as ambient, which is sea level; Weaverville is 93.87&nbsp;kPa
(13.61&nbsp;psi). Together those two omissions inflate every flow figure in the prior research by
roughly 15%, and every power figure by the same 15% again on top of the conversion-constant error
in item 3.</div>

<div class="chartbox"><h4>The same engine, the same 30 psi, three models</h4>
<div id="ch_r3_power"></div>
<div class="legend">
<span><i style="background:#ff6b6b"></i>Prior research &mdash; 15 &deg;C charge, sea level, 9.35 whp/lb-min</span>
<span><i style="background:#ffb347"></i>This report, round two &mdash; fixed 50 &deg;C charge, 8.20 whp/lb-min</span>
<span><i style="background:#38d39f"></i>Round three &mdash; charge temperature solved with airflow, 8.00 whp/lb-min</span>
</div>
<p class="note" style="margin-top:9px">At 7,500 rpm the three answers are <b>542</b>, <b>441</b> and
<b>404</b> whp. The gap is not a modelling nuance. It is the difference between assuming the
intercooler works perfectly, assuming it works well, and calculating what it actually does.</p></div>

<h3 id="r211">21.1 &nbsp;Item 1 &mdash; what the EFR 7163 actually makes</h3>
<div class="scroll"><table>
<thead><tr><th>Source</th><th class="num">Claim</th><th>Basis</th></tr></thead>
<tbody>
<tr><td>This report, &sect;17</td><td class="num">420&ndash;480 whp street/track<br>~540 whp race ceiling</td>
<td>Fixed 50 &deg;C charge; 10.0 crank hp/lb-min &times; 0.82 drivetrain; turbo run to its
pressure-ratio ceiling of 3.6 at 6,650 rpm</td></tr>
<tr><td>Prior research, <code>05_operating_point_detail</code></td><td class="num">466 whp</td>
<td>15 &deg;C implied charge, sea level, 9.35 whp/lb-min, and an undocumented VE curve
7&ndash;15% below the shared model's</td></tr>
<tr><td>Prior research, <code>13_g4x_boost_target_table</code></td><td class="num">511 whp</td>
<td>Same as above but with the shared model's VE curve</td></tr>
<tr><td>Prior research, <code>11_charge_temp_summary</code></td><td class="num">516.9 whp</td>
<td>Same again, with a charge-temperature density derate referenced to 122 &deg;F</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Resolved</b></td>
<td class="num"><b>404 whp</b><br><span class="note">band 384&ndash;424</span></td>
<td>7,500 rpm, 30 psi, E85, 32 &deg;C ambient, 2,100 ft, charge temperature solved simultaneously
with airflow, 10.0 crank hp/lb-min &times; 0.80 drivetrain</td></tr>
</tbody></table></div>

<div class="rec"><h3>The one number, with its assumptions visible</h3>
<div class="specline"><span class="k">Wheel horsepower</span><span class="v"><b>404 whp</b> (505 crank) on E85</span></div>
<div class="specline"><span class="k">At</span><span class="v">7,500 rpm, 30 psi gauge, EFR 7163</span></div>
<div class="specline"><span class="k">Air mass flow</span><span class="v">50.5 lb/min &mdash; 84% of the 7163's 60 lb/min choke line</span></div>
<div class="specline"><span class="k">Pressure ratio</span><span class="v">3.42, against the 7163's usable ceiling of 3.6</span></div>
<div class="specline"><span class="k">Charge temp at the valve</span><span class="v">79 &deg;C (174 &deg;F) on the 76 mm core, 70 &deg;C (157 &deg;F) on the 102 mm core</span></div>
<div class="specline"><span class="k">Ambient</span><span class="v">32 &deg;C, 93.87 kPa, 100 km/h with sealed ducting</span></div>
<div class="specline"><span class="k">Conversion</span><span class="v">10.0 crank hp per lb/min &times; 0.80 AWD drivetrain = 8.00 whp per lb/min</span></div>
<div class="specline"><span class="k">Exhaust backpressure</span><span class="v">EMAP/IMAP 1.6 assumed &mdash; see &sect;22, your manifold is probably worse</span></div>
</div>

<div class="callout c-good"><b>The important correction is not the number. It is that the EFR 7163 is
not used up.</b> This report said it was "simultaneously at both of its limits." That was an artefact
of running it to a pressure ratio of 3.6 at 6,650 rpm with an assumed 50&nbsp;&deg;C charge. Solved
properly, at 30 psi the 7163 sits at <b>84% of its choke line</b> and a pressure ratio of
<b>3.42 against a 3.6 ceiling</b>. It has headroom in both directions. See &sect;21.7.</div>

<div class="chartbox"><h4>The EFR 7163 across the boost range, at 7,500 rpm</h4>
<div id="ch_r3_ladder"></div>
<div class="legend">
<span><i style="background:#38d39f"></i>Wheel horsepower</span>
<span><i style="background:#ffb347"></i>Charge temperature at the valve, &deg;C</span>
<span><i style="background:#4ea3ff"></i>Percentage of the 60 lb/min choke line</span>
<span><i style="background:#ff6b6b;height:2px"></i>Pressure-ratio ceiling 3.6, reached at 32.6 psi</span>
</div></div>

<div class="scroll"><table>
<thead><tr><th class="num">Boost</th><th class="num">PR</th><th class="num">lb/min</th>
<th class="num">% of choke</th><th class="num">Charge temp</th><th class="num">whp</th><th>Verdict</th></tr></thead>
<tbody>
''' + ladder_rows() + '''
</tbody></table></div>

<h3 id="r212">21.2 &nbsp;Item 2 &mdash; why the prior research contradicts itself</h3>
<p class="note">Three files describe the same turbo at 7,500 rpm and disagree by 45&nbsp;whp.
The cause is not the choke cap. It is that <b>three different volumetric efficiency curves are in
circulation inside one body of work</b>, and none of the files says which one it is using.
<span class="def" title="Volumetric efficiency: the fraction of the cylinder's swept volume the
engine fills each cycle, measured against a stated reference density.">Volumetric efficiency (VE)</span>
was reverse-engineered out of each file by dividing its stated flow by
<code>K &times; RPM &times; PR</code>.</p>

<div class="scroll"><table>
<thead><tr><th>File</th><th class="num">Boost</th><th class="num">Flow</th>
<th class="num">Implied VE at 7,500</th><th class="num">whp per lb/min</th><th class="num">whp</th></tr></thead>
<tbody>
<tr><td><code>06_turbo_model.py</code> <span class="note">the shared model everything imports</span></td>
<td class="num">&mdash;</td><td class="num">&mdash;</td><td class="num">0.870</td><td class="num">9.35</td><td class="num">&mdash;</td></tr>
<tr><td><code>05_turbo_comparison_data.csv</code></td><td class="num">30.0</td><td class="num">58.00</td>
<td class="num">0.870 <span class="pill p-ok">matches</span></td><td class="num">9.35</td><td class="num">542</td></tr>
<tr><td><code>13_g4x_boost_target_table.csv</code></td><td class="num">28.2</td><td class="num">55.70</td>
<td class="num">0.871 <span class="pill p-ok">matches</span></td><td class="num">9.17</td><td class="num">511</td></tr>
<tr><td><code>11_charge_temp_summary.csv</code></td><td class="num">30.0</td><td class="num">58.02</td>
<td class="num">0.870 <span class="pill p-ok">matches</span></td><td class="num">8.91</td><td class="num">516.9</td></tr>
<tr style="background:rgba(255,107,107,.09)"><td><code>05_operating_point_detail.csv</code></td>
<td class="num">27.0</td><td class="num">50.07</td>
<td class="num"><b>0.805</b> <span class="pill p-bad">does not match</span></td><td class="num">9.31</td><td class="num">466</td></tr>
</tbody></table></div>

<p class="note"><b>The 45 whp, itemised.</b> Taking <code>13_g4x</code> at 511 whp as the start point
and walking to <code>05_operating_point_detail</code> at 466 whp:</p>
<div class="eq">boost 28.2 &rarr; 27.0 psi          flow 55.70 &rarr; 54.14 lb/min   <span class="cm">&minus;1.56 lb/min</span>
VE   0.871 &rarr; 0.805           flow 54.14 &rarr; 50.07 lb/min   <span class="cm">&minus;4.07 lb/min  &lt;-- the real cause</span>
whp/lb-min 9.17 &rarr; 9.31       whp  459 &rarr; 466              <span class="cm">+7 whp</span>
                                 TOTAL 511 &rarr; 466 whp = &minus;45 whp</div>

<div class="callout c-warn"><b>It is not a choke cap, and the guess that it was is wrong.</b>
At 7,500 rpm <code>05_operating_point_detail</code> reports a choke margin of 9.93&nbsp;lb/min
against the 7163's 60&nbsp;lb/min line. The compressor limit is not binding in <i>any</i> of the
three files. <b>The whole spread is a VE curve that one file uses and never declares.</b>
That file's implied VE is 8&ndash;15% below the shared model's across the entire rev range, not just
at the top: 0.888 against 1.050 at 5,000 rpm, 0.805 against 0.870 at 7,500.</div>

<h4>Which one is right?</h4>
<p class="note"><b>Neither, and that is the useful answer.</b> The shared model's VE curve peaks at
1.05 at 5,000 rpm. The supplied cylinder-head flow reference, written by the same body of work,
independently says a peak "near 1.005 at 5500 rpm... is realistic and slightly optimistic" on an
NA basis. So the prior research contains three VE peaks &mdash; 1.05, 1.005 and 0.892 &mdash; in
three documents that were meant to agree. The reconciled curve in &sect;21.5 is built from the head-flow
reference and the Taylor Mach index, and lands at 0.970 peak, 0.938 at 7,500.</p>

<h3 id="r213">21.3 &nbsp;Item 3 &mdash; the conversion constants</h3>
<p class="note">The prior model uses <code>WHP_PER_LBMIN_E85 = 9.35</code>, built as 11 crank hp per
lb/min times a 0.85 drivetrain factor. Both halves were challenged. Both fail.</p>

<h4>Crank horsepower per lb/min on E85</h4>
<p class="note">Garrett's published relation is
<span class="def" title="Wa = HP / (AFR x BSFC / 60), rearranged. BSFC is brake specific fuel
consumption, the pounds of fuel burned per horsepower per hour.">
<code>hp per lb/min = 60 &divide; (AFR &times; BSFC)</code></span>. E85 stoichiometric is about 9.7:1,
and a boosted engine runs richer than that:</p>
<div class="eq">AFR 8.0, BSFC 0.70   &rarr;  10.7 hp/lb-min   <span class="cm">optimistic. This is where 11 comes from.</span>
AFR 7.8, BSFC 0.77   &rarr;  10.0 hp/lb-min   <span class="cm">published typical E85 turbo BSFC</span>
AFR 7.5, BSFC 0.85   &rarr;   9.4 hp/lb-min   <span class="cm">conservative</span></div>
<p class="note"><b>Resolved: 10.0.</b> The challenge was correct &mdash; 11 sits at the very top of the
credible range and requires a BSFC of 0.70 on E85, which is better than published turbocharged E85
figures of 0.77&ndash;0.90.</p>

<h4>Drivetrain loss</h4>
<p class="note">This is the bigger error, and the challenge was right that 15% is low for all-wheel drive.</p>
<div class="scroll"><table>
<thead><tr><th>Evidence</th><th class="num">Implied loss</th><th>Quality</th></tr></thead>
<tbody>
<tr><td>Community consensus, Subaru AWD</td><td class="num">20&ndash;25%</td>
<td><span class="pill p-warn">Anecdotal but very widely reported</span></td></tr>
<tr><td>Community consensus, Mitsubishi Evo AWD</td><td class="num">20&ndash;30%</td>
<td><span class="pill p-warn">Anecdotal</span></td></tr>
<tr><td>Evo 6, same engine on an engine dyno and then an AWD chassis dyno</td><td class="num">23%</td>
<td><span class="pill p-ok">Measured, back-to-back &mdash; the strongest single data point</span></td></tr>
<tr><td>Stock ST185, 189.7 whp on an AWD Dynojet, against the JDM 225 PS rating</td>
<td class="num">~15%</td>
<td><span class="pill p-bad">Weak.</span> JDM ratings of that era were not measured to a comparable
standard, and Dynojet AWD figures read high. Cannot be used to set a factor.</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Resolved for the ST185 GT-Four</b></td>
<td class="num"><b>20%</b> (factor 0.80)</td>
<td>Transverse transaxle with a transfer gearset, viscous centre differential and a rear
differential. More parasitic than front-wheel drive, slightly less than a longitudinal Subaru.
Band 18&ndash;22%.</td></tr>
</tbody></table></div>

<div class="chartbox"><h4>How much the two contested constants alone move the answer</h4>
<div id="ch_r3_sens"></div>
<p class="note" style="margin-top:9px">Same airflow &mdash; 50.5 lb/min &mdash; in every cell. Only the
conversion changes. <b>This one choice spans 374 to 472 whp, a 98 whp range, on identical physics.</b>
It is the largest single source of disagreement between the two bodies of work.</p></div>

<div class="scroll"><table>
<thead><tr><th class="num">Crank hp per lb/min</th><th class="num">&times; 0.78</th><th class="num">&times; 0.80</th>
<th class="num">&times; 0.82</th><th class="num">&times; 0.85</th><th>Note</th></tr></thead>
<tbody>
''' + sens_rows() + '''
</tbody></table></div>

<h3 id="r214">21.4 &nbsp;Item 4 &mdash; displacement</h3>
<div class="scroll"><table>
<thead><tr><th>Source</th><th class="num">Displacement</th><th>Status</th></tr></thead>
<tbody>
<tr><td><code>06_turbo_model.py</code></td><td class="num">2,164 cc</td>
<td><span class="pill p-bad">Wrong.</span> That is the stock 5S-FE 87.0 mm bore.</td></tr>
<tr><td>Head-flow reference document</td><td class="num">2,188.8 cc</td>
<td><span class="pill p-ok">Correct</span> &mdash; the same body of research already had it right in one file</td></tr>
<tr><td>This report</td><td class="num">2,188.8 cc</td><td><span class="pill p-ok">Correct</span></td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Resolved</b></td><td class="num"><b>2,188.8 cc</b></td>
<td>87.5 mm bore &times; 91.0 mm stroke &times; 4. Confirmed bore.</td></tr>
</tbody></table></div>
<p class="note"><b>Effect: +1.15% on airflow and therefore on power</b> &mdash; about +4.6 whp at the
design point. Real, corrected, and the smallest of the errors in this section. Worth noting that the
prior research contained both the right and the wrong figure in different files.</p>

<h3 id="r215">21.5 &nbsp;Item 5 &mdash; the VE curve and the redline</h3>
<p class="note">This report's round one claimed VE collapses above 6,650 rpm. The prior research models
a flat-ish curve to a 7,500 rpm ceiling. The head-flow reference says the ports are not limiting until
roughly 7,800. These are three different stories about the same engine.</p>

<div class="chartbox"><h4>Four VE curves, one engine</h4>
<div id="ch_r3_ve"></div>
<div class="legend">
<span><i style="background:#6f8098"></i>This report, round one &mdash; collapses. No source was ever cited.</span>
<span><i style="background:#ff6b6b"></i>Prior research <code>06_turbo_model.py</code> &mdash; peaks 1.05 at 5,000</span>
<span><i style="background:#ffb347"></i>This report, round two &mdash; Mach rolloff, cam peak 6,200</span>
<span><i style="background:#38d39f"></i>Round three, reconciled &mdash; cam peak 5,800</span>
<span><i style="background:#c58cff;height:1px"></i>Taylor Mach index Z, right axis</span>
</div>
<p class="note" style="margin-top:9px">The reconciled curve moves the cam peak from 6,200 to
5,800&nbsp;rpm, because both the head-flow reference and the prior research put it at 5,000&ndash;5,500,
and a 91&nbsp;mm stroke with 264&deg; cams genuinely does favour the midrange. Above 7,000 rpm it sits
between the two prior curves.</p></div>

<h4>What actually limits the redline &mdash; three candidates, tested separately</h4>
<div class="scroll"><table>
<thead><tr><th class="num">Redline</th><th class="num">Mean piston speed</th><th class="num">Mach index Z</th>
<th class="num">Port demand<br>per cylinder</th><th class="num">VE</th><th class="num">whp at 30 psi</th>
<th class="num">Gain</th><th>What binds</th></tr></thead>
<tbody>
<tr><td class="num">6,650</td><td class="num">20.2 m/s</td><td class="num">0.461</td><td class="num">62 CFM</td>
<td class="num">0.967</td><td class="num">375</td><td class="num">&mdash;</td>
<td><span class="pill p-ok">Nothing.</span> Head, VE and bottom end all have margin.</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td class="num"><b>7,200</b></td><td class="num">21.8 m/s</td>
<td class="num">0.496</td><td class="num">67 CFM</td><td class="num">0.961</td><td class="num">398</td>
<td class="num">+23</td><td><span class="pill p-ok">Recommended.</span> Bottom end is the first thing
to become uncomfortable, and it is not yet uncomfortable.</td></tr>
<tr><td class="num">7,500</td><td class="num">22.8 m/s</td><td class="num">0.516</td><td class="num">68 CFM</td>
<td class="num">0.938</td><td class="num">404</td><td class="num">+29</td>
<td><span class="pill p-warn">Outer limit.</span> Bottom end. Needs upgraded valve springs.</td></tr>
<tr><td class="num">7,800</td><td class="num">23.7 m/s</td><td class="num">0.536</td><td class="num">69 CFM</td>
<td class="num">0.908</td><td class="num">407</td><td class="num">+32</td>
<td><span class="pill p-bad">Not worth it.</span> +3 whp over 7,500 for a large durability cost.</td></tr>
<tr><td class="num">8,000</td><td class="num">24.3 m/s</td><td class="num">0.550</td><td class="num">69 CFM</td>
<td class="num">0.889</td><td class="num">408</td><td class="num">+33</td>
<td><span class="pill p-bad">No.</span> +1 whp over 7,800.</td></tr>
</tbody></table></div>

<div class="callout c-good"><b>The three stories are reconcilable, and each was partly right.</b>
<ul class="tight">
<li><b>The head is not the limit.</b> The Taylor Mach index stays under 0.55 to 8,000 rpm, and the
per-cylinder port demand peaks at 69&nbsp;CFM against a measured stock Gen&nbsp;2 port capacity of
about 245&nbsp;CFM at 28&nbsp;inches of water. The head-flow reference is right, and round one of this
report was wrong to have VE collapse.</li>
<li><b>The VE is not the limit either, but it does taper.</b> It falls from 0.967 at 6,650 to 0.938 at
7,500 &mdash; a real taper, not a collapse. That taper is enough to make rpm above 7,500 worthless:
7,500&nbsp;&rarr;&nbsp;7,800 buys 3 whp, and 7,800&nbsp;&rarr;&nbsp;8,000 buys 1.</li>
<li><b>The bottom end is the limit.</b> Rod ratio 1.516 (138 mm rod, 91 mm stroke) with 22.8 m/s mean
piston speed at 7,500 rpm and 30 psi of manifold pressure. This is a durability constraint, not a
power constraint, and it is the only one of the three that actually binds.</li>
</ul>
<b>One recommendation: 7,200 rpm, with 7,500 as an outer limit if you fit better valve springs.</b>
The rod-ratio argument in &sect;17.5 survives intact. What changes is the reason it survives: not
because the engine stops breathing, but because there is nothing left to gain by the time the bottom
end starts to complain.</div>

<h3 id="r216">21.6 &nbsp;Item 6 &mdash; which compressor maps the numbers actually rest on</h3>
<p class="note">This one matters because the answer is <b>mixed, and the two halves of every row in the
prior research come from different models with different ambient assumptions.</b></p>

<div class="scroll"><table>
<thead><tr><th>Quantity</th><th>Where it comes from</th><th>Ambient assumed</th><th>Trustworthiness</th></tr></thead>
<tbody>
<tr><td><b>Flow and whp</b> in <code>05_turbo_comparison_data</code>,
<code>05_operating_point_detail</code>, <code>13_g4x_boost_target_table</code></td>
<td><code>06_turbo_model.py</code> &mdash; its own header calls the maps "MODELED approximations...
NOT traced from the official BorgWarner map contours"</td>
<td class="num">15 &deg;C, sea level</td>
<td><span class="pill p-bad">Low.</span> And the <code>COMP_MAPS</code> efficiency field in that file
is broken: evaluated at the 7163's own operating point it returns 27% isentropic efficiency, where the
same body of work quotes 70.6% elsewhere. That block is effectively dead code.</td></tr>
<tr><td><b>Compressor efficiency and charge temperature</b> in
<code>11_charge_temp_summary</code> and <code>13_g4x</code>, for the four <b>EFR</b> turbos</td>
<td>The surfaces in <code>10_official_maps_digitized.png</code> &mdash; fitted to digitized labels
off the official BorgWarner sheets</td>
<td class="num">25 &deg;C, with a real intercooler (&epsilon; 0.75, &Delta;p 1.5 psi)</td>
<td><span class="pill p-warn">Medium.</span> Genuinely anchored on official data, but the fit residuals
are 0.010 to 0.048 efficiency points, and <b>the 7163 has the worst fit of the four at RMS 0.048</b>
&mdash; which is the turbo the headline number depends on.</td></tr>
<tr style="background:rgba(255,107,107,.09)"><td><b>The two Garrett rows</b> in
<code>11_charge_temp_summary</code> (G30-770, G35-900)</td>
<td>Nothing official. No Garrett map was digitized anywhere in the supplied work.</td>
<td class="num">&mdash;</td>
<td><span class="pill p-bad">None.</span> Those efficiency figures are modelled, and the file does not
say so.</td></tr>
</tbody></table></div>

<div class="callout c-bad"><b>Stated plainly: the digitization was never folded back into the shared
model.</b> <code>06_turbo_model.py</code> still carries its own warning to "verify against the official
PDF maps before finalizing boost targets," and it still contains the modelled Gaussian maps. The later
digitization in chart 10 produced better efficiency numbers that reached two of the five data files but
never reached the model that computes the flow. So the prior research's final numbers are a mixture:
<b>airflow from an unverified model at 15&nbsp;&deg;C, efficiency from official maps at 25&nbsp;&deg;C.</b>
Those cannot both be true of the same operating point.</div>

<div class="callout c-info"><b>What round three rests on.</b> Compressor isentropic efficiency for
the four EFR turbos is taken from the digitized official surfaces &mdash; that is the best data available
and it is genuinely official-derived. Everything else (displacement, site pressure, VE, charge
temperature, conversion) is recomputed here. The Garrett efficiencies are flagged as estimates in the
table in &sect;21.7 and should not be used to separate two candidates.</div>

<h3 id="r217">21.7 &nbsp;Item 7 &mdash; the turbo recommendation, withdrawn and replaced</h3>

<div class="callout c-bad"><b>The Garrett G25-770 does not appear in Garrett's catalogue.</b>
Garrett's published G-Series line is G25-550 and G25-660 in the G25 frame, and G25-585 and G25-700 in
G-Series&nbsp;II. The <b>770</b> rating belongs to the <b>G30</b> frame &mdash; the G30-770, which uses a
58&nbsp;mm compressor, not the G25's 54&nbsp;mm. A small number of reseller pages carry a "G25-770"
title, which is either a listing error or a re-badge. <b>More damaging than the name:</b> the real
G25-660's published maximum flow is <b>61 lb/min</b>. This report assigned its "G25-770" a choke line of
<b>73 lb/min</b> &mdash; 20% above the entire G25 frame's actual ceiling, and the flow figure was doing
most of the work in the recommendation. The recommendation is withdrawn on that ground alone.</div>

<div class="chartbox"><h4>Every candidate on one model, at the boost this engine will actually run</h4>
<div id="ch_r3_turbo"></div>
<div class="legend">
<span><i style="background:#38d39f"></i>whp at 30 psi, 7,500 rpm &mdash; what you will drive</span>
<span><i style="background:#4ea3ff"></i>whp at that turbo's own ceiling &mdash; what you will not drive</span>
<span><i style="background:#ffb347"></i>Spool threshold, right axis</span>
</div>
<p class="note" style="margin-top:9px">At 30 psi the eight candidates span <b>401 to 406 whp</b>.
That is a 5 whp spread across turbos costing $1,750 to $2,629. Below the choke line every compressor
moves the same air at the same pressure &mdash; the only differences are compressor efficiency, which
shows up as charge temperature, and spool.</p></div>

<div class="scroll"><table>
<thead><tr><th>Turbo</th><th class="num">Choke</th><th class="num">&eta;<sub>c</sub></th>
<th class="num">whp<br>@30 psi</th><th class="num">Charge<br>temp</th>
<th class="num">whp at its<br>own ceiling</th><th class="num">Boost<br>to get there</th>
<th class="num">Spool</th><th>Where the efficiency figure comes from</th></tr></thead>
<tbody>
''' + turbo_rows() + '''
</tbody></table></div>

<div class="rec"><h3>Resolved turbo recommendation</h3>
<div class="specline"><span class="k">Recommendation</span><span class="v"><b>Keep the BorgWarner EFR 7163 you already own.</b></span></div>
<div class="specline"><span class="k">Why</span><span class="v">At 30 psi it makes 404 whp against 401&ndash;406 for every alternative</span></div>
<div class="specline"><span class="k">Spool advantage</span><span class="v">4,000 rpm &mdash; 250 rpm earlier than the G25-660, 540 earlier than the G30-770, 1,200 earlier than the EFR 8374</span></div>
<div class="specline"><span class="k">Headroom it still has</span><span class="v">84% of choke, PR 3.42 of 3.6. Good to 32.6 psi and about 419 whp.</span></div>
<div class="specline"><span class="k">Money saved</span><span class="v">$1,850&ndash;$2,400 not spent on a turbo</span></div>
<div class="specline"><span class="k">Spend it on</span><span class="v">The 102 mm core (&sect;21.8), the ducting, and re-making the manifold (&sect;22)</span></div>
</div>

<div class="callout c-warn"><b>The honest argument against keeping it.</b> Two things would change this.
<b>(1)</b> If you decide you want more than about 420 whp, the 7163 genuinely cannot do it &mdash; past
32.6 psi you are off the top of its map, and then the EFR 8374 or Garrett G35-900 is the answer, both
of which run 75% compressor efficiency where the 7163 runs 70.6%, worth about 3&nbsp;&deg;C of charge
temperature. <b>(2)</b> The 7163's efficiency figure has the worst map fit of the four EFRs
(RMS 0.048, &sect;21.6). If it is really running 66% rather than 70.6%, the charge temperature is about
5&nbsp;&deg;C higher than modelled here and the case for a bigger, more efficient compressor strengthens.
<b>Neither is a reason to buy now.</b> Log the turbo speed sensor and the charge IAT on the An&nbsp;Volt&nbsp;6
input, run the 7163 at 30 psi, and decide with data.</div>

<div class="callout c-info"><b>On the &sect;17 claim that the 8374 and G35-900 run better compressor
efficiency &mdash; that is correct, and it does feed the intercooler.</b> 75.0% and 75.2% against 70.6%
for the 7163 and 67.0% for the G30-770. At the design point that is worth about <b>3&nbsp;&deg;C</b> of
charge temperature, which is roughly 2 whp. It is a real effect, correctly identified in the prior
research, and it is much smaller than the 9&nbsp;&deg;C the core depth change in &sect;21.8 is worth.
<b>Compressor efficiency is not a reason to change turbos on this engine. Core depth is a reason to
change cores.</b></div>

<h3 id="r218">21.8 &nbsp;Item 8 &mdash; the intercooler size mismatch</h3>
<p class="note">The prior research's pressure-reference diagram labels the intercooler
<b>28 &times; 12 &times; 4 inch</b> (711 &times; 305 &times; 102 mm). This report recommends
610 &times; 305 &times; 76 mm. Both cannot be right, and it turns out <b>each is right about one
dimension</b>.</p>

<div class="scroll"><table>
<thead><tr><th>Core (W &times; H &times; T, mm)</th><th class="num">Volume</th><th class="num">Face velocity</th>
<th class="num">&epsilon;</th><th class="num">Charge temp out</th><th class="num">&Delta; vs 76 mm</th>
<th class="num">whp</th><th class="num">&Delta; whp</th>
<th class="num">Extra heat<br>onto radiator</th><th class="num">Depth<br>needed</th></tr></thead>
<tbody>
''' + core_rows() + '''
</tbody></table></div>

<div class="chartbox"><h4>Charge cooling gained against radiator air lost &mdash; round three</h4>
<div id="ch_r3_core"></div>
<p class="note" style="margin-top:9px">Down is cooler charge air. Right is hotter air reaching the
radiator. The 610&nbsp;&times;&nbsp;305&nbsp;&times;&nbsp;102 sits at the knee: it captures most of the
available charge cooling before the radiator penalty accelerates.</p></div>

<div class="rec"><h3>Resolved core recommendation</h3>
<div class="specline"><span class="k">Core</span><span class="v"><b>610 &times; 305 &times; 102 mm</b> (24 &times; 12 &times; 4 in) bar and plate, single pass</span></div>
<div class="specline"><span class="k">Against the 76 mm core</span><span class="v">9.2 &deg;C cooler charge, +7 whp, +8.0 &deg;C onto the radiator, +1.5 kg</span></div>
<div class="specline"><span class="k">Predicted at 30 psi / 7,500 rpm</span><span class="v">&epsilon; 0.793, outlet 70 &deg;C (157 &deg;F)</span></div>
<div class="specline"><span class="k">Front-to-back space needed</span><span class="v">137 mm (102 core + 25 duct + 10 mounting) &mdash; you measured about 165 mm available</span></div>
<div class="specline"><span class="k">Assembled option</span><span class="v">SpeedFactory HPX 610 &times; 305 &times; 114 mm, ~$650 &mdash; already surveyed in &sect;19.1, needs 149 mm</span></div>
<div class="specline"><span class="k">Reject</span><span class="v">711 mm width. See below.</span></div>
</div>

<div class="callout c-bad"><b>Reject the 28-inch width, keep the 4-inch depth.</b>
<ul class="tight">
<li><b>Width.</b> A 711 mm core needs a clear aperture of roughly 740 mm once tank welds are counted.
<b>The ST185 radiator is only 712 mm overall.</b> A core wider than the radiator behind it shadows
everything and gains nothing &mdash; and measurement M1 in &sect;13 sets the requirement at
&ge;&nbsp;640 mm for the 610 mm core, which is already the thing to verify. The 28-inch figure looks
like an early placeholder that was never checked against this chassis.</li>
<li><b>Depth.</b> Here the prior research is right and this report was wrong. 102 mm buys 9.2 &deg;C
and 7 whp. You have the clearance &mdash; about 1.5&times; what the 76 mm core needs &mdash; and this is
the single cheapest 7 whp in the whole build.</li>
<li><b>What it costs.</b> +8.0 &deg;C onto the radiator inlet, +1.5 kg, and about 21 ms of extra
charge-system fill time on spool-up, which is below what a driver detects. On a 35-year-old AWD car
retaining its A/C condenser the radiator penalty is the thing to watch, not the mass.</li>
<li><b>Going wider as well buys almost nothing.</b> 711 &times; 305 &times; 102 lands at 66.4 &deg;C
against 69.6 for 610 &times; 305 &times; 102 &mdash; 3.2 &deg;C for 101 mm of extra width that will not fit.</li>
</ul></div>

<h3 id="r219">21.9 &nbsp;Item 9 &mdash; the charge temperature cross-check</h3>
<p class="note">The prior research predicts 130&ndash;135&nbsp;&deg;F (54&ndash;57&nbsp;&deg;C) at the
manifold. This report predicted 76&nbsp;&deg;C (169&nbsp;&deg;F). Both claim to be post-intercooler
numbers, so one of them has to be wrong.</p>

<div class="scroll"><table>
<thead><tr><th>Case</th><th class="num">Ambient</th><th class="num">Site pressure</th>
<th class="num">PR</th><th class="num">Compressor out</th><th class="num">&epsilon;</th>
<th class="num">Charge temp out</th></tr></thead>
<tbody>
<tr><td>Prior research as published</td><td class="num">25 &deg;C</td><td class="num">101.3 kPa</td>
<td class="num">3.04</td><td class="num">183 &deg;C</td><td class="num">0.75</td>
<td class="num">64 &deg;C / <b>148 &deg;F</b></td></tr>
<tr><td>Same, at Weaverville's ambient only</td><td class="num">32 &deg;C</td><td class="num">101.3 kPa</td>
<td class="num">3.04</td><td class="num">192 &deg;C</td><td class="num">0.75</td>
<td class="num">72 &deg;C / 161 &deg;F</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Round three, full design point</b></td>
<td class="num">32 &deg;C</td><td class="num">93.87 kPa</td><td class="num">3.42</td>
<td class="num">214 &deg;C</td><td class="num">0.742</td>
<td class="num"><b>79 &deg;C / 174 &deg;F</b> <span class="note">(76 mm core)</span></td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Round three, on the recommended 102 mm core</b></td>
<td class="num">32 &deg;C</td><td class="num">93.87 kPa</td><td class="num">3.42</td>
<td class="num">214 &deg;C</td><td class="num">0.793</td>
<td class="num"><b>70 &deg;C / 157 &deg;F</b></td></tr>
</tbody></table></div>

<div class="callout c-good"><b>Resolved, and both sides were partly right.</b>
<ul class="tight">
<li>The prior research's 130&ndash;135&nbsp;&deg;F <b>is</b> a genuine post-intercooler number &mdash;
the concern that it might have been a compressor-outlet figure is unfounded. It reproduces exactly
from its own stated inputs.</li>
<li>But those inputs are <b>25&nbsp;&deg;C ambient and sea-level pressure</b>, not this car's
32&nbsp;&deg;C and 93.87&nbsp;kPa. Altitude is the larger of the two effects: it pushes the pressure
ratio from 3.04 to 3.42 at the same gauge boost, which adds about 22&nbsp;&deg;C to the compressor
outlet before the intercooler sees it.</li>
<li><b>This report's 76&nbsp;&deg;C was the closer of the two answers</b>, and the corrected figure is
79&nbsp;&deg;C on the core it recommended, or <b>70&nbsp;&deg;C on the 102 mm core now recommended</b>.</li>
<li>Note that the prior research applied a 25&nbsp;&deg;C ambient to its <i>thermal</i> chart while its
<i>airflow</i> model assumed 15&nbsp;&deg;C charge air &mdash; the internal inconsistency described in
&sect;21.6.</li>
</ul></div>

<h3 id="r2110">21.10 &nbsp;Item 10 &mdash; exhaust manifold pairing</h3>
<p class="note">This is large enough to have its own section. <b>The prior research is correct and the
finding is verified independently.</b> See <a href="#manifold">&sect;22</a>.</p>

<h3 id="r2111">21.11 &nbsp;Item 11 &mdash; boost control plumbing</h3>
<div class="callout c-good"><b>The prior research is right, the reasoning is sound, and this is now a
build note.</b></div>
<p class="note"><b>The rule:</b> feed the MAC 46A boost-control solenoid from a
<b>pre-throttle</b> charge-pressure source &mdash; a 1/8 NPT bung in the charge pipe between the
intercooler and the throttle body. Do <b>not</b> feed it from the billet distribution block on the
intake manifold.</p>

<h4>Why, checked step by step</h4>
<div class="scroll"><table>
<thead><tr><th class="num">#</th><th>Step</th><th>Sound?</th></tr></thead>
<tbody>
<tr><td class="num">1</td><td>The Turbosmart GenV IWG75 <b>Twin Port</b> actuator has two chambers. The
top port assists opening; the bottom port assists holding closed against boost. A twin-port actuator
needs positive pressure on the bottom port to hold the gate shut above spring pressure.</td>
<td><span class="pill p-ok">Correct</span> &mdash; this is what makes twin-port different from single-port,
and your invoice confirms a TS-0620-4012 Twin Port with a 14 psi spring.</td></tr>
<tr><td class="num">2</td><td>The MAC 46A four-port solenoid distributes its supply pressure between
those two chambers. It cannot create pressure; it can only route what it is fed.</td>
<td><span class="pill p-ok">Correct</span></td></tr>
<tr><td class="num">3</td><td>On a lift or a shift the throttle closes. Manifold pressure goes to
vacuum within milliseconds. The charge pipe upstream of the throttle stays pressurised.</td>
<td><span class="pill p-ok">Correct</span> &mdash; that pressure difference is the entire reason a
blow-off valve exists.</td></tr>
<tr><td class="num">4</td><td>If the solenoid is fed from the manifold, both actuator chambers lose
supply at that moment. The actuator spring shuts the wastegate fully while the turbo is still
spinning near its previous speed.</td><td><span class="pill p-ok">Correct</span></td></tr>
<tr><td class="num">5</td><td>On re-application the gate is already shut and the solenoid has no
pressure yet to modulate with, so boost overshoots before control authority returns.</td>
<td><span class="pill p-ok">Correct.</span> This is a well-documented failure mode. It is worst on
twin-port internal gates, exactly what you have.</td></tr>
</tbody></table></div>

<div class="rec"><h3>Build note &mdash; boost control plumbing</h3>
<div class="specline"><span class="k">Solenoid supply</span><span class="v">1/8 NPT bung in the <b>cold-side charge pipe</b>, between intercooler outlet and throttle body</span></div>
<div class="specline"><span class="k">Solenoid</span><span class="v">MAC 46A four-port &mdash; port A to actuator top, port B to actuator bottom, vent to a filter</span></div>
<div class="specline"><span class="k">Do NOT use</span><span class="v">The billet distribution block on the intake manifold, for this one job</span></div>
<div class="specline"><span class="k">The distribution block still feeds</span><span class="v">G4X MAP sensor, fuel pressure regulator 1:1 reference, blow-off valve signal, boost gauge &mdash; all of which <i>want</i> manifold pressure</span></div>
<div class="specline"><span class="k">Symptom if you get it wrong</span><span class="v">Boost spikes on the 2&ndash;3 and 3&ndash;4 upshifts and after any partial lift. It will look like a tuning problem. It is a plumbing problem.</span></div>
</div>

<h3 id="r2112">21.12 &nbsp;What could not be resolved from the data</h3>
<div class="callout c-warn"><b>Stated rather than decided.</b>
<ul class="tight">
<li><b>Compressor efficiency for the two Garrett candidates.</b> No official Garrett map was digitized
anywhere in the supplied work, and the G30-770 and G35-900 efficiency figures in
<code>11_charge_temp_summary</code> are modelled. They are used here only to show that the choice does
not matter at 30 psi, not to rank the Garretts against each other.</li>
<li><b>The 7163's own compressor efficiency.</b> The digitized fit has RMS 0.048 efficiency points on
that turbo &mdash; the worst of the four. A true 66% instead of 70.6% would put the charge about
5&nbsp;&deg;C hotter than modelled. Only a log of turbo speed against MAP and IAT settles it.</li>
<li><b>Which VE curve is real.</b> Three appear in the prior research (peaks of 1.05, 1.005, 0.892) and
two in this report. The reconciled curve is defensible from the head-flow data and the Mach index, but
it is still a model. <b>Back-calculating VE from logged MAP, IAT and injector duty is a one-afternoon
job and it would replace this entire argument with a measurement.</b></li>
<li><b>Drivetrain loss.</b> 20% is a considered choice from AWD data generally, not a measurement of
this car. The one ST185-specific dyno figure found implies about 15%, but it is not a usable data
point. A coast-down on a chassis dyno would settle it, and the answer moves the headline power by
&plusmn;20 whp.</li>
<li><b>Whether the intake plenum is a limit.</b> The head-flow reference notes the stock Gen 2 plenum
is documented to "struggle with flow above 350 whp." No plenum appears in the 64 invoices. At 404 whp
this is a live question and it is not addressed anywhere in either body of work.</li>
</ul></div>
</section>
'''

# ====================================================================
# 5. NEW SECTION 22 - MANIFOLD
# ====================================================================
SEC22 = '''
<!-- ============ 22 MANIFOLD ============ -->
<section id="manifold">
<h2><span class="num">22</span>The twin-scroll manifold is paired wrong</h2>
<p class="lede">The prior research says your twin-scroll manifold pairs cylinders <b>1+2 / 3+4</b>, and
that the correct pairing is <b>1+4 / 2+3</b>. This was checked independently, from firing order and cam
duration alone, without reference to the prior work. <b>It is correct.</b></p>

<div class="callout c-bad"><b>Verified.</b> On a 1-3-4-2 firing order with the HKS 264&deg; exhaust cam,
pairing 1+2 and 3+4 puts <b>84&deg; of crank angle where both cylinders in a scroll have their exhaust
valves open at once</b>. Pairing 1+4 and 2+3 gives a <b>96&deg; clear gap</b> in each scroll with no
overlap at all. The prior research's figures reproduce exactly.</div>

<h3>22.1 &nbsp;The arithmetic, from first principles</h3>
<p class="note">Nothing here needs a simulation. Firing order and exhaust duration are enough.</p>
<div class="eq">firing order 1-3-4-2, so power strokes begin at:   cyl 1 = 0&deg;   cyl 3 = 180&deg;   cyl 4 = 360&deg;   cyl 2 = 540&deg;
HKS 264 exhaust cam: 264&deg; duration, exhaust valve opens about 135&deg; after firing TDC

  cyl 1 exhaust open   135&deg; &rarr; 399&deg;
  cyl 3 exhaust open   315&deg; &rarr; 579&deg;
  cyl 4 exhaust open   495&deg; &rarr; 759&deg;  (= 495&deg; &rarr; 720&deg; and 0&deg; &rarr; 39&deg;)
  cyl 2 exhaust open   675&deg; &rarr; 939&deg;  (= 675&deg; &rarr; 720&deg; and 0&deg; &rarr; 219&deg;)

<span class="cm">Two cylinders 180&deg; apart in the cycle:  264 &minus; 180 = 84&deg; of OVERLAP
Two cylinders 360&deg; apart in the cycle:  360 &minus; 264 = 96&deg; of CLEAR GAP</span>

YOUR PAIRING   1+2  are 180&deg; apart &rarr; 84&deg; overlap      3+4  are 180&deg; apart &rarr; 84&deg; overlap
CORRECT        1+4  are 360&deg; apart &rarr; 96&deg; gap          2+3  are 360&deg; apart &rarr; 96&deg; gap</div>

<p class="note">The general rule, which matches published twin-scroll guidance: pair the cylinder that
fires <b>first</b> with the one that fires <b>third</b>, and the <b>second</b> with the <b>fourth</b>.
On 1-3-4-2 that is 1 with 4, and 3 with 2. Your manifold pairs adjacent-in-time cylinders instead,
which is the one arrangement that guarantees collision.</p>

<div class="chartbox"><h4>Exhaust valve events, both pairings</h4>
<div id="ch_pulse"></div>
<div class="legend">
<span><i style="background:#4ea3ff"></i>Cyl 1</span><span><i style="background:#38d39f"></i>Cyl 2</span>
<span><i style="background:#ff6b6b"></i>Cyl 3</span><span><i style="background:#ffb347"></i>Cyl 4</span>
</div>
<p class="note" style="margin-top:9px">Each bar is one cylinder's exhaust valve open period across a
full 720&deg; cycle. In the upper panel the two bars sharing a scroll overlap. In the lower panel they
do not, and there is 96&deg; of clear crank angle between them.</p></div>

<h3>22.2 &nbsp;What the wrong pairing actually costs</h3>
<p class="note">The purpose of a divided turbine housing is to keep the
<span class="def" title="Blowdown: the first, high-pressure phase of exhaust, when the cylinder is still
well above manifold pressure and gas leaves at sonic velocity. It carries most of the energy the turbine
extracts.">blowdown pulse</span> from one cylinder away from another cylinder that is still trying to
empty. When both cylinders in a scroll are open together, the opening cylinder's blowdown pressurises
the scroll while its neighbour is mid-stroke, and that pressure pushes back into the neighbour's
cylinder.</p>

<div class="scroll"><table>
<thead><tr><th>Effect</th><th class="num">Size</th><th>Why</th><th>Confidence</th></tr></thead>
<tbody>
<tr><td><b>Exhaust backpressure</b><br><span class="note">EMAP/IMAP ratio</span></td>
<td class="num">1.6 &rarr; 2.0<br><span class="note">roughly</span></td>
<td>A mis-paired divided housing behaves close to a single-scroll housing of the same total area, but
keeps the divider's wetted area and flow restriction. It gets the losses of a divided housing without
the benefit.</td><td><span class="pill p-warn">Medium</span> &mdash; directionally certain, magnitude modelled</td></tr>
<tr><td><b>Peak power</b></td><td class="num">&minus;7 whp<br><span class="note">at 7,500 rpm, 30 psi</span></td>
<td>Higher exhaust manifold pressure raises residual exhaust gas left in the cylinder, which displaces
fresh charge. Modelled at 5% VE loss per unit of EMAP/IMAP above 1.0.</td>
<td><span class="pill p-warn">Medium</span></td></tr>
<tr><td><b>Spool threshold</b></td><td class="num">300&ndash;500 rpm later</td>
<td>Pulse energy is what spins the turbine below the boost threshold, and pulse separation is what
preserves it. This is the effect twin-scroll exists for, and it is the one being forfeited.
Published back-to-back twin vs single scroll testing puts the difference at 300&ndash;500 rpm of onset
and 8&ndash;15% of torque under the knee.</td>
<td><span class="pill p-ok">High</span> &mdash; this is the biggest and best-supported effect</td></tr>
<tr><td><b>Knock margin and exhaust valve temperature</b></td><td class="num">Not quantified</td>
<td>Higher residual fraction means a hotter, more knock-prone charge. On E85 with a flex sensor this is
a smaller problem than it would be on pump gas, but it is not nothing.</td>
<td><span class="pill p-neu">Directional only</span></td></tr>
</tbody></table></div>

<div class="chartbox"><h4>Exhaust backpressure against power &mdash; where your manifold sits</h4>
<div id="ch_bp"></div>
<div class="legend">
<span><i style="background:#38d39f"></i>whp at 7,500 rpm, 30 psi</span>
<span><i style="background:#4ea3ff"></i>Correctly paired twin scroll, EMAP/IMAP ~1.6</span>
<span><i style="background:#ff6b6b"></i>Mis-paired, behaving as single scroll, ~2.0</span>
</div>
<p class="note" style="margin-top:9px">This is the same 1.0&ndash;2.0 backpressure band &sect;17 flagged as
worth &plusmn;25 whp. Round three narrows it: the realistic move from a correctly paired to a mis-paired
manifold is 1.6 &rarr; 2.0, which is <b>7 whp</b>, not 25. <b>The power loss is small. The spool loss
is the one that matters.</b></p></div>

<div class="chartbox"><h4>What 400 rpm of spool delay looks like from the driver's seat</h4>
<div id="ch_spoolpair"></div>
<div class="legend">
<span><i style="background:#38d39f"></i>Correctly paired 1+4 / 2+3 &mdash; full boost ~4,000 rpm</span>
<span><i style="background:#ff6b6b"></i>As built 1+2 / 3+4 &mdash; full boost ~4,400 rpm</span>
</div>
<p class="note" style="margin-top:9px">At 3,500 rpm the correctly paired manifold is making about
9 psi more. That is the difference between a turbo that is already working when you come out of a corner
and one that is still waking up.</p></div>

<h3>22.3 &nbsp;Recommendation</h3>
<div class="rec"><h3>Re-make the manifold</h3>
<div class="specline"><span class="k">Verdict</span><span class="v"><b>Yes &mdash; re-pair the runners to 1+4 / 2+3.</b></span></div>
<div class="specline"><span class="k">Primary reason</span><span class="v">Spool. 300&ndash;500 rpm, on a street car, is the most noticeable change available anywhere in this build.</span></div>
<div class="specline"><span class="k">Secondary reason</span><span class="v">About 7 whp, and lower exhaust valve temperature</span></div>
<div class="specline"><span class="k">What it does NOT change</span><span class="v">The turbo choice. See below.</span></div>
<div class="specline"><span class="k">Cheaper alternative</span><span class="v">If re-making is not practical, fitting an <b>undivided</b> 0.80 A/R T4 housing recovers most of the loss &mdash; you stop paying the divider's restriction for a benefit you are not receiving. It gives up the spool that a correct twin scroll would have given.</span></div>
<div class="specline"><span class="k">Do it before</span><span class="v">Any dyno tuning. Tuning around a manifold you intend to change wastes the session.</span></div>
</div>

<div class="callout c-good"><b>It does not change the turbo recommendation, and here is why that
matters.</b> The mis-pairing makes the <i>current</i> turbo feel lazier than it is. If you tuned the car
as it stands, concluded the EFR 7163 spools too late, and bought a bigger turbo to fix it, you would be
solving the wrong problem &mdash; every larger candidate spools <i>later</i> still. <b>Fix the manifold
first, then judge the turbo.</b> With correct pairing the 7163's 4,000 rpm threshold is the earliest of
any candidate on the list, and the case for keeping it in &sect;21.7 gets stronger, not weaker.</div>

<div class="callout c-warn"><b>What is uncertain here.</b> The 84&deg;/96&deg; geometry is exact
arithmetic and not in doubt. The <b>consequences</b> are modelled: the 1.6&nbsp;&rarr;&nbsp;2.0
backpressure shift is an informed estimate, not a measurement, and the 300&ndash;500 rpm spool figure is
taken from published twin-versus-single-scroll comparisons on other engines, not from this one. The
direction is certain. The magnitudes are worth &plusmn;50%. <b>You have a 5-bar MAP sensor and a turbo
speed sensor already; adding an exhaust backpressure gauge before and after the change would turn this
whole section into a measurement.</b></div>
</section>
'''

must('<!-- ============ 16 SOURCES ============ -->', SEC21 + SEC22 +
     '\n<!-- ============ 16 SOURCES ============ -->', label="insert 21+22")

# renumber sources/open sections
must('<h2><span class="num">20</span>Sources</h2>', '<h2><span class="num">23</span>Sources</h2>',
     label="sources num")

io.open(REPORT, "w", encoding="utf-8").write(html)
print("sections injected: %d -> %d bytes (+%d)" % (orig_len, len(html), len(html)-orig_len))
