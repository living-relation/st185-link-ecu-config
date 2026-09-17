# -*- coding: utf-8 -*-
"""Round five report builder - part 1: head, nav, summary, inputs, site, model, calculators."""
import re, json

CSS = open("r5_style.css", encoding="utf-8").read()
R4 = json.loads(re.search(r"var R4=(\{.*\});", open("r5_r4_data.js", encoding="utf-8").read(), re.S).group(1))
R5 = json.loads(re.search(r"var R5=(\{.*\});", open("r5_data.js", encoding="utf-8").read(), re.S).group(1))

NAV = [("summary","Answers"),("inputs","Build Inputs"),("site","Site"),("model","The Model"),
       ("calc","Calculators"),("pipes","Charge Pipe"),("core","Core Spec"),("duct","Ducting"),
       ("stack","Front-End Stack"),("turbo","Turbo &amp; Surge"),("power","Power Estimate"),
       ("manifold","Manifold"),("rejected","Considered &amp; Rejected"),("vendors","Vendors"),
       ("sources","Sources"),("open","Open Questions")]

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>5S-GTE ST185 &mdash; Charge Pipe and Intercooler Core Specification</title>
%s
</head>
<body>
<header class="hero"><div class="wrap">
<h1>Charge Pipe and Intercooler Core &mdash; 5S-GTE Toyota Celica ST185</h1>
<p class="sub">Two decisions: what diameter to build the charge pipes, and what core to have made.
Everything else in this document is here because it changes one of those two answers, or because
it changes what you do at the tune.</p>
<div class="meta">Round five &middot; 31 Aug 2026 &middot; BorgWarner EFR 7163 (unchanged)
&middot; Carlos Sainz front bumper &middot; Soara dual plenum &middot; street + occasional track
&middot; Weaverville, NC</div>
</div></header>

<nav class="toc"><div class="wrap">
%s
</div></nav>

<div class="wrap">
""" % (CSS, "".join('<a href="#%s">%s</a>' % (a, b) for a, b in NAV))

D = R5["design"]
P25 = [p for p in R5["pipes"] if p["od"] == 2.5][0]
P225 = [p for p in R5["pipes"] if p["od"] == 2.25][0]
P30 = [p for p in R5["pipes"] if p["od"] == 3.0][0]

SUMMARY = """
<section id="summary">
<h2><span class="num">01</span>The two answers</h2>

<div class="grid g2">
<div class="rec"><h3>Charge pipe &mdash; both sides</h3>
<div class="specline"><span class="k">Diameter</span><span class="v">2.50 in OD, 0.065 in wall</span></div>
<div class="specline"><span class="k">Inside diameter</span><span class="v">60.2 mm (2.370 in)</span></div>
<div class="specline"><span class="k">Hot side velocity</span><span class="v">%(hf)d ft/s</span></div>
<div class="specline"><span class="k">Cold side velocity</span><span class="v">%(cf)d ft/s</span></div>
<div class="specline"><span class="k">Plumbing pressure loss</span><span class="v">%(dp).2f psi total</span></div>
<div class="specline"><span class="k">Material</span><span class="v">6061 mandrel bend, R/D 1.5 or better</span></div>
<p class="note" style="margin:12px 0 0">Same number on the hot side and the cold side. One bend
radius, one coupler size, one spare. The turbo outlet is 2.0 in, so the hot pipe steps up
immediately at the turbo and stays 2.50 in to the core.</p>
</div>

<div class="rec"><h3>Intercooler core &mdash; made to order</h3>
<div class="specline"><span class="k">Width</span><span class="v">bumper aperture minus 20 mm</span></div>
<div class="specline"><span class="k">Height</span><span class="v">305 mm</span></div>
<div class="specline"><span class="k">Thickness</span><span class="v">102 mm</span></div>
<div class="specline"><span class="k">Construction</span><span class="v">bar and plate, 14&ndash;16 FPI</span></div>
<div class="specline"><span class="k">Ports</span><span class="v">2.50 in OD stubs, both tanks</span></div>
<div class="specline"><span class="k">Tanks</span><span class="v">fabricated tapered, side entry, opposite ends</span></div>
<p class="note" style="margin:12px 0 0">Height and thickness are fixed. Width is the only open
number and it falls straight out of one measurement. See &sect;08 for the width table.</p>
</div>
</div>

<div class="callout c-warn"><b>One measurement blocks the build.</b> The clear width of the Carlos
Sainz bumper aperture. Nothing else in this document is waiting on anything. Across the whole
plausible range of aperture widths the answer moves by about 8&nbsp;&deg;C of charge temperature
and 6&nbsp;whp, so the measurement decides the core width but it does not change the shape of
the recommendation.</div>

<h3>Why 2.50 in and not 2.25 in</h3>
<ul class="tight">
<li><b>2.25 in has no pressure-ratio headroom left.</b> Its extra %(dpx).2f psi of plumbing loss
puts the compressor at PR %(pr225).3f at 30 psi, against the 7163's usable ceiling of 3.60. It
caps you at about %(cap225).1f psi of boost. 2.50 in caps you at %(cap25).1f psi.</li>
<li><b>The volume it saves is not something you can feel.</b> 2.25 in takes %(dfill)d ms off the
time to fill the charge system. That is inside the noise of a pedal input, and it is 1.5 L out of
a %(sys)0.0f L system that is mostly core and end tanks.</li>
<li><b>Going the other way is worse.</b> 3.00 in buys %(prgain).2f more of pressure-ratio margin,
which is worth about %(whpgain)d whp, and costs %(fillgain)d ms of fill, more weight, and a harder
route past the A/C lines.</li>
<li><b>Pipe diameter is worth under 1 whp across the whole range.</b> It is a transient-response
and headroom decision, not a power decision. Do not spend money on it twice.</li>
</ul>

<h3>The five things that actually matter, in order of size</h3>
<div class="scroll"><table>
<thead><tr><th>Item</th><th>What it is worth</th><th>Status</th></tr></thead>
<tbody>
<tr><td><b>Sealed ducting from the bumper opening to the core face</b></td>
<td>About 27&nbsp;&deg;C of charge temperature against an unducted core</td>
<td><span class="pill p-warn">You have to build it</span></td></tr>
<tr><td><b>Core thickness 76 &rarr; 102 mm</b></td>
<td>9&nbsp;&deg;C of charge temperature, 7 whp</td>
<td><span class="pill p-ok">Decided &mdash; 102 mm</span></td></tr>
<tr><td><b>Boost target table shaped against rpm</b></td>
<td>Keeps the compressor off its surge line below 2,750 rpm. Costs nothing.</td>
<td><span class="pill p-warn">Set it before the first tune</span></td></tr>
<tr><td><b>Core width, over the plausible aperture range</b></td>
<td>8&nbsp;&deg;C, 6 whp</td>
<td><span class="pill p-bad">Blocked on one measurement</span></td></tr>
<tr><td><b>Charge pipe diameter, 2.25 to 3.00 in</b></td>
<td>Under 1 whp at 30 psi. 1.6 psi of boost ceiling. 49 ms of fill time.</td>
<td><span class="pill p-ok">Decided &mdash; 2.50 in</span></td></tr>
</tbody></table></div>
</section>
""" % dict(hf=P25["hot_fts"], cf=P25["cold_fts"], dp=P25["dp"],
           dpx=P225["dp"] - P25["dp"], pr225=P225["pr"], cap225=P225["boost_cap"],
           cap25=P25["boost_cap"], dfill=P25["fill_ms"] - P225["fill_ms"],
           sys=P25["sysL"], prgain=P30["pr_margin"] - P25["pr_margin"],
           whpgain=P30["whp_cap"] - P25["whp_cap"], fillgain=P30["fill_ms"] - P25["fill_ms"])

INPUTS = """
<section id="inputs">
<h2><span class="num">02</span>Build inputs</h2>
<p class="lede">From your parts invoices, the <code>st185-link-ecu-config</code> repo, and your own
measurements. Nothing here is invented; assumptions are marked.</p>

<div class="scroll"><table>
<thead><tr><th>Parameter</th><th>Value</th><th>Source</th><th>Status</th></tr></thead>
<tbody>
<tr><td>Chassis / engine</td><td>1991 Celica GT-Four ST185; 5S-GTE hybrid &mdash; 5S-FE block and
crank, 3S-GTE head</td><td>Your project description; RockAuto invoices</td>
<td><span class="pill p-ok">Confirmed</span></td></tr>
<tr><td>Displacement</td><td><b>2,188.8 cc</b> &mdash; 87.5 mm bore, 91 mm stroke</td>
<td>JE 252064 and CP SC7451 piston listings for this build</td>
<td><span class="pill p-ok">Resolved</span></td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Turbocharger</td>
<td><b>BorgWarner EFR 7163</b>, supercore PN 11637105000, T4 twin-scroll, 0.80 A/R, internally
wastegated. <b>Unchanged. No turbo change is recommended anywhere in this report.</b></td>
<td>TurboKits.com order TK.0000015915, $2,629</td>
<td><span class="pill p-ok">Confirmed &mdash; retained</span></td></tr>
<tr><td>Compressor outlet</td><td><b>2.0 in (50.8 mm)</b> hose coupler; compressor inlet 2.5 in</td>
<td>BorgWarner EFR 7163 datasheet</td><td><span class="pill p-ok">Confirmed</span></td></tr>
<tr><td>Turbo flow limits</td><td>60 lb/min choke, usable pressure ratio to about 3.6</td>
<td>Official BorgWarner EFR 7163 product sheet</td><td><span class="pill p-ok">Confirmed</span></td></tr>
<tr><td>Wastegate / BOV</td><td>Turbosmart GenV IWG75 EFR Twin Port, 14 psi spring;
Turbosmart Kompact Dual Port</td><td>Turbosmart invoice 279321; TurboKits invoice</td>
<td><span class="pill p-ok">Confirmed</span></td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Throttle body and its adapters</td>
<td>Bosch 0 280 750 474 drive-by-wire, 74.5 mm bore. Bought with a 3 in hose adapter and a custom
DBW manifold adapter. <b>Treated as solved. Nothing downstream of the cold pipe is a design
variable.</b></td>
<td>Outsider Garage order #7870, 5 Jan 2026</td>
<td><span class="pill p-ok">Bought &mdash; work within it</span></td></tr>
<tr><td>Intake plenum</td><td>Soara Performance custom dual plenum, 3 in (76.2 mm) throttle
flange, hyperbolic bellmouths, 3 bar rating</td><td>Dan; Soara product pages</td>
<td><span class="pill p-ok">Confirmed</span></td></tr>
<tr><td>Exhaust manifold</td><td><b>1+4 / 2+3</b> twin-scroll pairing</td>
<td>Dan. The 1+2 / 3+4 shown in the old diagrams was corrected after they were drawn.</td>
<td><span class="pill p-ok">Confirmed &mdash; validated in &sect;16</span></td></tr>
<tr><td>ECU / sensors</td><td>Link G4X FuryX; 5 bar MAP; EFR speed sensor on SI-3; flex fuel
sensor on DI-5; a second IAT planned on An Volt 6 in the charge pipe</td>
<td><code>st185-link-ecu-config</code> repo</td><td><span class="pill p-ok">Confirmed</span></td></tr>
<tr><td>Fuel system</td><td>1400 cc/min EV14 injectors; Walbro 450 LPH F90000267; E85 flex</td>
<td>Ballenger 978721; STM Tuned 151651</td><td><span class="pill p-ok">Confirmed</span></td></tr>
<tr><td>Boost target</td><td><b>30 psi design point</b>, used for every number in this report</td>
<td>Derived: 1400 cc injectors + E85 + 5 bar MAP + the 7163's map headroom all point here</td>
<td><span class="pill p-warn">Assumed &mdash; Open Q2</span></td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Radiator</td>
<td>Mishimoto MMRAD-CEL-89, two-row. Overall 714 &times; 439 &times; 64.5 mm; core
699 &times; 318 mm face, 51.8 mm thick. Mounted on the engine side of the fender support.</td>
<td>Vendor listing; Dan's confirmation of position</td><td><span class="pill p-ok">Confirmed</span></td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Front-end depth</td>
<td>A/C condenser sits even with the fender support. With a 76 mm core there is
<b>203&ndash;254 mm clear</b> between the back of the core and the radiator.</td>
<td>Dan, measured</td><td><span class="pill p-ok">Confirmed &mdash; depth is not a constraint</span></td></tr>
<tr style="background:rgba(255,179,71,.09)"><td>Bumper aperture width</td>
<td><b>Not measured.</b> The one number this report is waiting on.</td><td>&mdash;</td>
<td><span class="pill p-bad">Blocking</span></td></tr>
<tr><td>Drivetrain</td><td>Rebuilt transmission, one-piece carbon driveshaft, LSD of unstated type,
lightweight wheels</td><td>Dan</td>
<td><span class="pill p-warn">LSD type still unknown &mdash; Open Q3</span></td></tr>
<tr><td>Location</td><td>Weaverville, NC 28787 &mdash; about 640 m / 2,100 ft</td>
<td>Ship-to address on every invoice</td><td><span class="pill p-ok">Confirmed</span></td></tr>
</tbody></table></div>

<div class="callout c-info"><b>Not yet bought.</b> No intercooler, core, charge piping, couplers or
clamps appear on any invoice. The core and the pipework are a clean-sheet decision, and the core
can be built to any dimensions and any port size you ask for. Off-the-shelf availability is not a
constraint on this design and is not used as one anywhere in this report.</div>
</section>
"""

SITE = """
<section id="site">
<h2><span class="num">03</span>Site conditions</h2>
<div class="grid g4">
<div class="kpi"><div class="lab">Design ambient</div><div class="val">32 &deg;C</div>
<div class="note">90 &deg;F, Asheville area summer</div></div>
<div class="kpi"><div class="lab">Site pressure</div><div class="val">93.9 kPa</div>
<div class="note">2,100 ft &mdash; 7.3%% thinner than sea level</div></div>
<div class="kpi"><div class="lab">Pressure ratio at 30 psi</div><div class="val w">%(pr).2f</div>
<div class="note">including plumbing and core loss</div></div>
<div class="kpi"><div class="lab">Compressor outlet</div><div class="val w">%(tc).0f &deg;C</div>
<div class="note">the air arriving at the intercooler</div></div>
</div>
<ul class="tight">
<li>Altitude raises the pressure ratio needed for a given gauge boost, which adds about
12&nbsp;&deg;C to compressor outlet temperature. It pushes toward more core, not less.</li>
<li>Western North Carolina means long sustained climbs at 40&ndash;60 mph. That is a demanding
intercooler duty cycle: high load, moderate airspeed, no cool-down between. It is the reason the
core recommendation is not minimal.</li>
</ul>
</section>
""" % dict(pr=P25["pr"], tc=D["tc"])

MODEL = """
<section id="model">
<h2><span class="num">04</span>The model</h2>
<p class="lede">Every number in this report comes out of these five steps, and the calculators in
&sect;05 run the same equations live. Charge temperature and air mass flow are solved together,
because each depends on the other.</p>

<div class="eq">m&#775;   = (D/1000) &times; (RPM/2)/60 &times; VE &times; &rho;_man     <span class="cm">&rho;_man from P_MAP and IAT, R = 287.05</span>
PR   = (P_MAP + &Delta;P_system) / (P_amb &times; 0.97)      <span class="cm">&Delta;P_system = pipes + core + tanks</span>
T&#8322;   = T&#8321; &times; [1 + (PR^((&gamma;&minus;1)/&gamma;) &minus; 1)/&eta;c]           <span class="cm">&gamma; = 1.40</span>
NTU  = U&middot;A / Cmin   with A = V_core &times; 900 m&sup2;/m&sup3;,  U = 55&radic;(v_face/10)
&epsilon;    = 1 &minus; exp[(NTU^0.22/Cr)(exp(&minus;Cr&middot;NTU^0.78) &minus; 1)]   <span class="cm">cross-flow, both fluids unmixed</span>

<span class="cm">Design point: 2,188.8 cc, 7,500 rpm, 30 psi gauge, 32 &deg;C, 93.87 kPa, &eta;c = 0.706
  &rarr; %(lb).1f lb/min, PR %(pr).2f, compressor outlet %(tc).0f &deg;C, IAT at the valve %(iat).0f &deg;C</span></div>

<h4>Uncertainty, stated once</h4>
<ul class="tight">
<li>Predicted temperatures: <b>&plusmn;5&nbsp;&deg;C</b>. Predicted pressure drops:
<b>&plusmn;30%%</b>.</li>
<li>Power: the model converts airflow at 10.0 crank hp per lb/min and an 0.80 all-wheel-drive
factor. The honest band is <b>%(lo)d to %(hi)d whp</b>. <b>This engine has never been on a
dynamometer.</b></li>
<li><b>If a difference between two options is smaller than these bands, this report says so and
stops.</b> That rule is why several sections from earlier rounds are gone.</li>
</ul>
</section>
""" % dict(lb=D["lb"], pr=P25["pr"], tc=D["tc"], iat=P25["iat"],
           lo=R4["hero"]["whp_lo"], hi=R4["hero"]["whp_hi"])

CALC = """
<section id="calc">
<h2><span class="num">05</span>Calculators</h2>
<p class="lede">Live. Defaults are your build at the design point.</p>

<div class="tabbar">
<button class="on" data-tab="t-core">Core sizing and IAT</button>
<button data-tab="t-pipe">Charge pipe velocity</button>
<button data-tab="t-dp">Pressure drop budget</button>
</div>

<div id="t-core" class="tabpane on">
<div class="grid g2">
<div class="card">
<h4>Engine and site</h4>
<label class="ctl">Boost, psi gauge <span class="rowval" id="v_boost">30.0</span></label>
<input type="range" id="i_boost" min="5" max="40" step="0.5" value="30">
<label class="ctl">Engine speed, rpm <span class="rowval" id="v_rpm">7500</span></label>
<input type="range" id="i_rpm" min="2000" max="8500" step="100" value="7500">
<label class="ctl">Volumetric efficiency <span class="rowval" id="v_ve">0.93</span></label>
<input type="range" id="i_ve" min="0.60" max="1.10" step="0.01" value="0.93">
<label class="ctl">Ambient air temp, &deg;C <span class="rowval" id="v_tamb">32</span></label>
<input type="range" id="i_tamb" min="-10" max="45" step="1" value="32">
<label class="ctl">Compressor isentropic efficiency <span class="rowval" id="v_eta">0.71</span></label>
<input type="range" id="i_eta" min="0.50" max="0.82" step="0.01" value="0.71">
<label class="ctl">Elevation, m <span class="rowval" id="v_alt">640</span></label>
<input type="range" id="i_alt" min="0" max="2500" step="20" value="640">
<label class="ctl">Displacement, L <span class="rowval" id="v_disp">2.19</span></label>
<input type="range" id="i_disp" min="1.6" max="3.0" step="0.01" value="2.19">
</div>
<div class="card">
<h4>Core and airflow</h4>
<label class="ctl">Core width, mm <span class="rowval" id="v_cw">590</span></label>
<input type="range" id="i_cw" min="300" max="750" step="5" value="590">
<label class="ctl">Core height, mm <span class="rowval" id="v_ch">305</span></label>
<input type="range" id="i_ch" min="150" max="400" step="5" value="305">
<label class="ctl">Core thickness, mm <span class="rowval" id="v_ct">102</span></label>
<input type="range" id="i_ct" min="40" max="150" step="2" value="102">
<label class="ctl">Core face velocity, m/s <span class="rowval" id="v_vf">7.1</span></label>
<input type="range" id="i_vf" min="2" max="30" step="0.1" value="7.1">
<p class="note" style="margin-top:9px">Face velocity is the air speed <i>through</i> the core, not
road speed. Sealed ducting gets you roughly 25&ndash;35% of road speed; no ducting gets you about
10%. That ratio is the single biggest lever in this report.</p>
<p class="note"><b>Basis:</b> this tab prices the core only. It leaves out the 1.3 psi of charge
pipe loss that the tables in &sect;06 and &sect;07 include, so it reads about 2 &deg;C cooler than
they do. That gap is inside the model's &plusmn;5 &deg;C band. Use the third tab for the
plumbing.</p>
<div class="calcout" id="out_core"></div>
</div>
</div>
<div class="chartbox">
<h4>Effectiveness and outlet IAT against core face velocity <span class="note">(live)</span></h4>
<div id="ch_face"></div>
<div class="legend"><span><i style="background:#4ea3ff"></i>Effectiveness &epsilon;</span>
<span><i style="background:#ffb347"></i>Outlet IAT &deg;C</span>
<span><i style="background:#38d39f"></i>Your operating point</span></div>
</div>
<div class="chartbox">
<h4>Outlet IAT against core volume <span class="note">(at your current face velocity)</span></h4>
<div id="ch_vol"></div>
<div class="legend"><span><i style="background:#ffb347"></i>Outlet IAT &deg;C</span>
<span><i style="background:#38d39f"></i>Recommended core</span></div>
</div>
</div>

<div id="t-pipe" class="tabpane">
<div class="card">
<h4>Velocity across candidate diameters</h4>
<p class="note">Runs off the mass flow and temperatures from the core tab. The commonly quoted
200&ndash;300 ft/s band is a sizing habit, not a physical requirement &mdash; what actually matters
is pressure loss and volume, and both are computed directly in &sect;07.</p>
<div class="scroll"><table id="tb_pipe">
<thead><tr><th>Pipe OD</th><th class="num">Hot m/s</th><th class="num">Hot ft/s</th>
<th class="num">Cold m/s</th><th class="num">Cold ft/s</th>
<th class="num">Volume, 1 m (L)</th><th>Verdict</th></tr></thead>
<tbody></tbody></table></div>
</div>
<div class="chartbox"><h4>Charge air velocity against pipe diameter</h4>
<div id="ch_pipe"></div>
<div class="legend"><span><i style="background:#ff6b6b"></i>Hot side</span>
<span><i style="background:#4ea3ff"></i>Cold side</span>
<span><i style="background:#38d39f"></i>200&ndash;300 ft/s band</span></div>
</div>
</div>

<div id="t-dp" class="tabpane">
<div class="grid g2">
<div class="card">
<h4>System layout</h4>
<label class="ctl">Hot pipe diameter, in <span class="rowval" id="v_dh">2.50</span></label>
<input type="range" id="i_dh" min="1.75" max="3.5" step="0.25" value="2.5">
<label class="ctl">Hot pipe length, m <span class="rowval" id="v_lh">1.1</span></label>
<input type="range" id="i_lh" min="0.4" max="2.5" step="0.1" value="1.1">
<label class="ctl">Hot side 90&deg; bends <span class="rowval" id="v_nh">3</span></label>
<input type="range" id="i_nh" min="0" max="8" step="1" value="3">
<label class="ctl">Cold pipe diameter, in <span class="rowval" id="v_dc">2.50</span></label>
<input type="range" id="i_dc" min="1.75" max="3.5" step="0.25" value="2.5">
<label class="ctl">Cold pipe length, m <span class="rowval" id="v_lc">1.5</span></label>
<input type="range" id="i_lc" min="0.4" max="3.0" step="0.1" value="1.5">
<label class="ctl">Cold side 90&deg; bends <span class="rowval" id="v_nc">4</span></label>
<input type="range" id="i_nc" min="0" max="8" step="1" value="4">
<label class="ctl">End tank quality</label>
<select id="i_tank">
<option value="0.20">Cast, CFD-shaped tapered (best)</option>
<option value="0.35" selected>Well-fabricated tapered with vane</option>
<option value="0.55">Plain fabricated box tank</option>
<option value="0.90">Cheap stamped box, centre inlet</option>
</select>
</div>
<div class="card"><h4>Budget</h4><div class="calcout" id="out_dp"></div></div>
</div>
<div class="chartbox"><h4>&Delta;P against flow &mdash; core construction comparison</h4>
<div id="ch_dp"></div>
<div class="legend"><span><i style="background:#4ea3ff"></i>Bar and plate, 3 in</span>
<span><i style="background:#38d39f"></i>Modern tube and fin, 3 in</span>
<span><i style="background:#ffb347"></i>Bar and plate, 4.5 in</span>
<span><i style="background:#ff6b6b"></i>Your flow</span></div>
</div>
</div>
</section>
"""

def pipe_rows():
    out = []
    for p in R5["pipes"]:
        best = p["od"] == 2.5
        hl = ' style="background:#12251f"' if best else ""
        if p["od"] == 2.25:
            v, c = "No pressure-ratio margin left at 30 psi", "p-bad"
        elif best:
            v, c = "Recommended", "p-ok"
        elif p["od"] == 2.75:
            v, c = "Works, but buys nothing you can use", "p-info"
        else:
            v, c = "Most volume, hardest route, no useful gain", "p-warn"
        out.append(
            "<tr%s><td><b>%.2f in</b></td><td class=\"num\">%.3f</td><td class=\"num\">%.1f</td>"
            "<td class=\"num\">%d</td><td class=\"num\">%d</td><td class=\"num\">%.2f</td>"
            "<td class=\"num\">%.2f</td><td class=\"num\">%.3f</td><td class=\"num\">%d</td>"
            "<td class=\"num\">%.1f</td><td><span class=\"pill %s\">%s</span></td></tr>"
            % (hl, p["od"], p["id_in"], p["id_mm"], p["hot_fts"], p["cold_fts"], p["vol"],
               p["dp"], p["pr"], p["fill_ms"], p["boost_cap"], c, v))
    return "\n".join(out)

PIPES = """
<section id="pipes">
<h2><span class="num">06</span>Charge pipe diameter</h2>
<p class="lede">Four candidates at 0.065 in wall, at real inside diameters, at the design point:
%(lb).1f lb/min, %(tc).0f &deg;C leaving the turbo, %(iat).0f &deg;C leaving the core.
Hot side %(lh).1f m with %(nh)d bends, cold side %(lc).1f m with %(nc)d bends &mdash; about
2.6 m of pipe in total.</p>

<div class="scroll"><table>
<thead><tr><th>OD</th><th class="num">ID in</th><th class="num">ID mm</th>
<th class="num">Hot ft/s</th><th class="num">Cold ft/s</th><th class="num">Pipe vol, L</th>
<th class="num">Pipe &Delta;P, psi</th><th class="num">PR at 30 psi</th>
<th class="num">Fill, ms</th><th class="num">Max boost, psi</th><th>Verdict</th></tr></thead>
<tbody>
%(rows)s
</tbody></table></div>
<p class="note"><b>Fill</b> is the time the compressor needs to take the whole charge system from
atmospheric to full boost at 45%% of design flow &mdash; the transient-response number. It counts
the core and end tanks (%(fixed).1f L) as well as the pipes, because they are most of the volume.
<b>Max boost</b> is where the compressor hits its pressure-ratio ceiling of 3.60 once it has paid
for this plumbing.</p>

<div class="chartbox">
<h4>What each diameter costs and buys</h4>
<div id="ch_pipe_dec"></div>
<div class="legend"><span><i style="background:#38d39f"></i>Pressure ratio needed at 30 psi (bars, left)</span>
<span><i style="background:#ffb347"></i>System fill time (line, right)</span>
<span><i style="background:#ff6b6b"></i>7163 pressure-ratio ceiling</span></div>
</div>

<h3>The decision</h3>
<div class="rec">
<h3>2.50 in OD, 0.065 in wall, hot side and cold side</h3>
<ul class="tight">
<li>2.25 in reaches PR %(pr225).3f at 30 psi against a 3.60 ceiling. There is nothing left. It caps
the engine at %(cap225).1f psi where 2.50 in reaches %(cap25).1f psi &mdash; %(dwhp)d whp of
ceiling, for %(dfill)d ms of fill time you cannot feel.</li>
<li>2.75 and 3.00 in reduce plumbing loss further, but the return has flattened: 3.00 in is worth
%(whp30)d whp of ceiling over 2.50 in and adds %(f30)d ms of fill, %(v30).1f L of volume, weight,
and a harder route past the A/C lines.</li>
<li>Peak power at 30 psi moves by under 1 whp across all four diameters. This is a headroom and
transient decision, not a power decision.</li>
<li>Same size both ends means one bend radius, one coupler size, one clamp size, one spare.</li>
</ul>
</div>

<h4>Build notes, and then this section is finished</h4>
<ul class="tight">
<li><b>The turbo outlet is 2.0 in.</b> The hot pipe is an expansion from the turbo from the first
inch. Any argument that depends on avoiding expansions is inconsistent with the hardware you own.
Step up at the turbo and stay 2.50 in to the core.</li>
<li><b>Do not step up after the core.</b> Increasing diameter on the cold side recovers nothing.
The pressure was lost in the core, and a larger pipe cannot give it back. What it does do is add
volume downstream of the compressor's flow limit, which adds transient delay. Keep the cold side
at 2.50 in all the way to the throttle body adapter you already own.</li>
<li><b>Joint steps are negligible.</b> There are three or four joints, each an inch or less of
effective length, in a 2.6 m run, downstream of a core that generates far more turbulence than any
of them. Butt the pipe ends inside the coupler and move on.</li>
<li><b>The throttle end is solved.</b> You own the adapter. After the throttle the air enters a
large plenum, then a smaller plenum, then individual runners. Nothing about the pipe geometry
survives that.</li>
<li><b>Bends:</b> mandrel, R/D 1.5 or better. Every 90&deg; bend is worth roughly 0.25 velocity
heads &mdash; that is where the plumbing loss actually lives, not at the joints.</li>
</ul>
</section>
""" % dict(lb=D["lb"], tc=D["tc"], iat=P25["iat"], lh=D["l_hot"], nh=D["n_hot"],
           lc=D["l_cold"], nc=D["n_cold"], rows=pipe_rows(), fixed=D["fixed_L"],
           pr225=P225["pr"], cap225=P225["boost_cap"], cap25=P25["boost_cap"],
           dwhp=P25["whp_cap"] - P225["whp_cap"], dfill=P25["fill_ms"] - P225["fill_ms"],
           whp30=P30["whp_cap"] - P25["whp_cap"], f30=P30["fill_ms"] - P25["fill_ms"],
           v30=P30["vol"] - P25["vol"])

def ap_rows():
    out = []
    for a in R5["aperture"]:
        note = ("Aperture is the binding constraint. Go to 114 mm thick to buy some of it back."
                if a["t"] == 114 else
                ("Wider than this stops paying &mdash; the radiator core is only 699 mm."
                 if a["w"] == 685 else "&mdash;"))
        hl = ' style="background:#12251f"' if 540 <= a["w"] <= 640 else ""
        out.append("<tr%s><td><b>%s mm</b></td><td><b>%d &times; %d &times; %d</b></td>"
                   "<td class=\"num\">%.1f</td><td class=\"num\">%.2f</td><td class=\"num\">%.3f</td>"
                   "<td class=\"num\">%.1f</td><td class=\"num\">%d</td><td class=\"num\">%.1f</td>"
                   "<td class=\"note\">%s</td></tr>"
                   % (hl, a["band"], a["w"], a["h"], a["t"], a["vol"], a["vf"], a["eps"],
                      a["iat"], a["whp"], a["t_rad"], note))
    return "\n".join(out)

def depth_rows():
    out, prev = [], None
    for c in R5["depths"]:
        d_iat = "" if prev is None else "%+.1f" % (c["iat"] - prev["iat"])
        d_rad = "" if prev is None else "%+.1f" % (c["t_rad"] - prev["t_rad"])
        v = {64: "Too thin. Gives away free cooling.",
             76: "Still leaving 4 &deg;C on the table.",
             89: "Better, but 102 is available and costs nothing you have.",
             102: "<b>Recommended.</b> Last step where charge cooling beats radiator cost.",
             114: "Charge gain and radiator cost are now equal. Stop here.",
             127: "Radiator cost now exceeds the charge gain."}[c["t"]]
        hl = ' style="background:#12251f"' if c["t"] == 102 else ""
        out.append("<tr%s><td><b>%d mm</b></td><td class=\"num\">%.1f</td><td class=\"num\">%.3f</td>"
                   "<td class=\"num\">%.1f</td><td class=\"num\">%s</td><td class=\"num\">%.1f</td>"
                   "<td class=\"num\">%s</td><td>%s</td></tr>"
                   % (hl, c["t"], c["vol"], c["eps"], c["iat"], d_iat, c["t_rad"], d_rad, v))
        prev = c
    return "\n".join(out)

def height_rows():
    return "\n".join(
        "<tr%s><td><b>%d mm</b></td><td class=\"num\">%.1f</td><td class=\"num\">%.1f</td>"
        "<td class=\"num\">%d</td><td class=\"note\">%s</td></tr>"
        % (' style="background:#12251f"' if c["h"] == 305 else "", c["h"], c["vol"], c["iat"],
           c["whp"],
           {255: "Only if the aperture is genuinely short.",
            280: "Acceptable fallback.",
            305: "<b>Recommended.</b> Fits under the bumper beam on this chassis.",
            330: "Worth 1.7 &deg;C if the opening allows it. Check bonnet-latch clearance.",
            355: "Starts fully shadowing the radiator vertically. Not recommended."}[c["h"]])
        for c in R5["heights"])

CORE = """
<section id="core">
<h2><span class="num">07</span>Intercooler core specification</h2>
<p class="lede">The core is made to order. Any width, any height, any thickness, any port size,
any tank. Nothing below is chosen because someone sells it that way.</p>

<div class="callout c-warn"><b>Measure the bumper aperture and this section resolves itself.</b>
Width is the only open number. Take the clear width of the Carlos Sainz opening at its narrowest
point, then read the row below. Height and thickness do not depend on it.</div>

<h3>Width, as a function of the aperture you measure</h3>
<p class="note">The rule is <b>core width = clear aperture width minus 20 mm</b>, which leaves
10 mm each side for the duct flange and its seal. The table takes the low end of each band, so the
answer is never too wide to fit.</p>
<div class="scroll"><table>
<thead><tr><th>Clear aperture width</th><th>Build this core (W &times; H &times; T)</th>
<th class="num">Volume, L</th><th class="num">Face vel, m/s</th><th class="num">&epsilon;</th>
<th class="num">Charge temp, &deg;C</th><th class="num">whp</th>
<th class="num">Air onto radiator, &deg;C</th><th>Note</th></tr></thead>
<tbody>
%(aprows)s
</tbody></table></div>

<div class="chartbox">
<h4>What core width is worth</h4>
<div id="ch_aperture"></div>
<div class="legend"><span><i style="background:#4ea3ff"></i>Charge temperature at the valve (left)</span>
<span><i style="background:#ffb347"></i>Air arriving at the radiator (right)</span></div>
<p class="note">Across the whole plausible range the answer moves about 8 &deg;C and 6 whp. Build
whatever the aperture takes, but do not delay the project trying to gain the last 50 mm of width
&mdash; it is worth about 1.5 &deg;C.</p>
</div>

<h3>Thickness &mdash; 102 mm, and here is where it stops</h3>
<div class="scroll"><table>
<thead><tr><th>Thickness</th><th class="num">Volume, L</th><th class="num">&epsilon;</th>
<th class="num">Charge temp, &deg;C</th><th class="num">&Delta; vs previous</th>
<th class="num">Air onto radiator, &deg;C</th><th class="num">&Delta; vs previous</th>
<th>Verdict</th></tr></thead>
<tbody>
%(deprows)s
</tbody></table></div>
<p class="note">Depth is free on this car: you have 203&ndash;254 mm of clear air between a 76 mm
core and the radiator, so even 114 mm leaves 165&ndash;216 mm. The thing that stops you is not
space, it is the point where each extra millimetre costs the radiator as much as it gives the
charge. That crossover is at 114 mm, so 102 mm is the last comfortable step. See &sect;13.</p>

<h3>Height &mdash; 305 mm</h3>
<div class="scroll"><table>
<thead><tr><th>Height</th><th class="num">Volume, L</th><th class="num">Charge temp, &deg;C</th>
<th class="num">whp</th><th>Note</th></tr></thead>
<tbody>
%(htrows)s
</tbody></table></div>

<h3>Ports and tanks</h3>
<div class="grid g2">
<div class="card">
<h4>Ports</h4>
<ul class="tight">
<li><b>2.50 in OD stubs on both tanks</b>, matching the pipe exactly. Pipe end butts to stub end
inside the coupler and there is no size change across the joint.</li>
<li><b>Side entry, opposite ends, diagonally opposed</b> &mdash; inlet high on the hot tank, outlet
low on the cold tank. This is what makes the flow spread across the full core height instead of
short-cutting along the top row.</li>
<li>At 2.50 in the port carries %(hf)d ft/s on the hot side. There is no reason to make the port
larger than the pipe; the tank is where the air slows down, not the stub.</li>
</ul>
</div>
<div class="card">
<h4>Tanks</h4>
<ul class="tight">
<li><b>Fabricated tapered</b>, TIG-welded 5052 or 6061. Cast is better and is not worth the money
or the lead time at this power level.</li>
<li><b>Tapered along the core face</b> so cross-sectional area falls as air is fed off into the
tubes. A parallel box tank feeds the far end and starves the near end.</li>
<li><b>One internal splitter vane</b> in each tank, aimed at the far third of the core.</li>
<li><b>Tank depth 76&ndash;90 mm.</b> Deeper adds volume for no distribution benefit.</li>
<li><b>14&ndash;16 FPI</b> on the core. Denser is a wall &mdash; it starves the radiator and the
A/C condenser behind it. See &sect;12.</li>
</ul>
</div>
</div>

<div class="grid g3">
<div class="chartbox"><h4>Plain box tank</h4><div id="tank_top"></div>
<p class="note">Air short-cuts to the near tubes. The far end of the core does little work.</p></div>
<div class="chartbox"><h4>Centre-fed box</h4><div id="tank_ctr"></div>
<p class="note">Better than end-fed, still leaves the outer tubes underfed.</p></div>
<div class="chartbox"><h4>Tapered, side entry, vaned</h4><div id="tank_side"></div>
<p class="note">What to specify. Even flow across the full core height.</p></div>
</div>

<div class="rec">
<h3>Final core specification</h3>
<div class="specline"><span class="k">Width</span><span class="v">clear aperture width minus 20 mm, capped at 685 mm</span></div>
<div class="specline"><span class="k">Height</span><span class="v">305 mm</span></div>
<div class="specline"><span class="k">Thickness</span><span class="v">102 mm</span></div>
<div class="specline"><span class="k">Construction</span><span class="v">bar and plate, 14&ndash;16 FPI</span></div>
<div class="specline"><span class="k">Ports</span><span class="v">2.50 in OD stubs, side entry, opposite ends, diagonally opposed</span></div>
<div class="specline"><span class="k">Tanks</span><span class="v">fabricated tapered, one splitter vane each, 76&ndash;90 mm deep</span></div>
<div class="specline"><span class="k">Overall depth needed</span><span class="v">about 137 mm including tank welds and duct flange</span></div>
<div class="specline"><span class="k">Expected charge temp</span><span class="v">69&ndash;73 &deg;C at the valve at 30 psi, 32 &deg;C ambient, ducted</span></div>
</div>
</section>
""" % dict(aprows=ap_rows(), deprows=depth_rows(), htrows=height_rows(), hf=P25["hot_fts"])

DUCT = """
<section id="duct">
<h2><span class="num">08</span>Ducting &mdash; the biggest single item in this report</h2>
<p class="lede">Worth about 27 &deg;C of charge temperature. That is three times what the core
thickness decision is worth and roughly thirty times what the pipe diameter decision is worth. It
costs sheet aluminium and a weekend.</p>

<div class="callout c-good"><b>Why it is worth so much.</b> An unducted core sits in the airstream
as a resistance, and air goes around it. Face velocity falls to roughly 10% of road speed. A
sealed duct turns "air near the core" into "air through the core" and gets you to 25&ndash;35%.
In the model that is effectiveness 0.63 &rarr; 0.88 and outlet IAT 87 &deg;C &rarr; 50 &deg;C.</div>

<div class="chartbox"><h4>Duct geometry</h4><div id="duct_svg"></div></div>

<div class="scroll"><table>
<thead><tr><th>Parameter</th><th>Build to this</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Inlet area</td><td>Duct mouth 50&ndash;70% of core face area</td>
<td>Below about 40% you cannot feed the core. Above about 80% there is no diffusion and no
pressure recovery, so the duct is just a box.</td></tr>
<tr><td>Diffuser angle</td><td>7&deg; per wall or less (14&deg; total included)</td>
<td>Flow separates from the wall past about 15&deg; total, and separated flow loses the static
pressure recovery that was the whole point. If the length forces a steeper angle, add a splitter
vane rather than steepening.</td></tr>
<tr><td><b>Sealing</b></td><td>All four edges, core to duct and duct to bumper. Closed-cell foam
strip minimum; riveted flange better.</td>
<td><b>This is the failure that actually happens.</b> A 10 mm gap around a 590 &times; 305 core is
an 18,000 mm&sup2; bypass path against a resistive core. Air will strongly prefer it. Sealing alone
is worth more than any core upgrade.</td></tr>
<tr><td>Exit path</td><td>Bonnet louvres, undertray cutouts, or wheel-arch venting</td>
<td>Flow through a core is driven by the pressure difference across it. A pressurised engine bay
means no difference and no flow, however good the inlet is.</td></tr>
<tr><td>Mouth lip</td><td>10&ndash;15 mm radius, not a sharp sheet edge</td>
<td>A sharp lip separates at yaw &mdash; that is, in every corner.</td></tr>
<tr><td>Gap to the condenser</td><td>15&ndash;25 mm minimum</td>
<td>Lets the core's exit jet spread before it hits the next heat exchanger. You have far more than
this.</td></tr>
</tbody></table></div>

<h3>Fin density</h3>
<div class="chartbox"><h4>Heat transfer, air-side &Delta;P, and the ratio</h4><div id="ch_fpi"></div>
<div class="legend"><span><i style="background:#4ea3ff"></i>Heat transfer Q</span>
<span><i style="background:#ff6b6b"></i>Air-side &Delta;P</span>
<span><i style="background:#38d39f"></i>Q per unit &Delta;P</span></div></div>
<ul class="tight">
<li><b>Specify 14&ndash;16 FPI.</b> Not 20 and up.</li>
<li>The Q/&Delta;P ratio peaks near 12 FPI, but that metric optimises a fan-driven cooler where you
pay for pressure drop directly. On a moving car the fan is free ram air, so you can afford some
&Delta;P to get more Q.</li>
<li>What stops you is the radiator and the A/C condenser behind the core. A dense core is a wall
and it starves them. That constraint, not the Q/&Delta;P peak, sets 14&ndash;16.</li>
</ul>
</section>
"""

def duty_rows():
    return "\n".join(
        "<tr><td>%s</td><td class=\"num\">%.1f kW</td><td class=\"num\">%.1f &deg;C</td>"
        "<td class=\"num\">%.1f kW</td><td class=\"num\">%.1f kW</td>"
        "<td class=\"num\">%.0f%%</td></tr>"
        % (d["lab"], d["q_ic"], d["t_rad_in"], d["q_bare"], d["q_stack"], d["lost_pct"])
        for d in R4["duty"])

STACK = """
<section id="stack">
<h2><span class="num">09</span>Front-end stack and radiator shadowing</h2>
<p class="lede">Depth is not a constraint on this car and the shadowing objection is smaller than
it looks. Both conclusions come out of the measurements you took.</p>

<div class="chartbox"><h4>Front-end stack, side view, to scale</h4><div id="ch_r4_stack"></div>
<p class="note">Drawn from your measured numbers, with the intercooler at the recommended 102 mm.
Everything behind the condenser is fixed by the chassis; everything in front of it is yours.</p></div>

<div class="grid g3">
<div class="kpi"><div class="lab">Clear gap behind a 102 mm core</div><div class="val g">177&ndash;228 mm</div>
<div class="note">you are not depth-limited</div></div>
<div class="kpi"><div class="lab">Radiator inlet air penalty, 76 &rarr; 102 mm core</div>
<div class="val w">+7.2 &deg;C</div><div class="note">at full boost only</div></div>
<div class="kpi"><div class="lab">Charge cooling gained, 76 &rarr; 102 mm</div>
<div class="val g">&minus;9.2 &deg;C</div><div class="note">at all times on boost</div></div>
</div>

<h3>Why the shadowing objection is overweighted</h3>
<div class="scroll"><table>
<thead><tr><th>Condition</th><th class="num">Heat the core puts into the air</th>
<th class="num">Air arriving at the radiator</th><th class="num">Radiator capacity, bare</th>
<th class="num">Radiator capacity, stacked</th><th class="num">Capacity lost</th></tr></thead>
<tbody>
%(duty)s
</tbody></table></div>
<ul class="tight">
<li><b>The penalty only exists while you are on boost.</b> At part throttle the core rejects 4 kW
instead of 55, and the radiator sees 38 &deg;C instead of 70 &deg;C. The stack costs it 9%% of
capacity, not 56%%.</li>
<li><b>While you are on boost the radiator is irrelevant anyway.</b> A 500 crank hp engine at
sustained full load rejects on the order of 200&ndash;250 kW to coolant. This radiator sheds
12&ndash;27 kW. Coolant temperature during a pull is held by the thermal mass of the block and the
coolant, not by the radiator.</li>
<li><b>The radiator earns its keep on the recovery lap</b> &mdash; the part-throttle section after
a climb. That is exactly when the intercooler is putting almost nothing into the air.</li>
<li>So the trade is not "9.2 &deg;C of charge cooling against 7.2 &deg;C of radiator inlet air".
It is "9.2 &deg;C of charge cooling, always, against about 2 &deg;C of radiator inlet air when the
radiator is actually doing its job". <b>The deeper core wins.</b></li>
</ul>

<h3>Fans</h3>
<div class="scroll"><table>
<thead><tr><th>Option</th><th>At a standstill</th><th>At road speed</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td><b>Puller behind the radiator</b>, engine side</td>
<td>Best. Draws through the whole stack.</td>
<td>No blockage &mdash; a stopped puller is out of the free stream and its shroud can be made to
open.</td>
<td><span class="pill p-ok">Do this if it fits.</span> Check clearance to the crank pulley and
timing cover first.</td></tr>
<tr><td>Pusher between condenser and radiator</td>
<td>Helps. Moves stack air onto the radiator.</td>
<td>Costs roughly 10&ndash;20%% of face velocity as static blockage.</td>
<td><span class="pill p-info">Acceptable fallback</span> if no puller fits. Worth shortening the
condenser for.</td></tr>
<tr><td>Pusher on the condenser, i.e. behind the intercooler</td>
<td>Marginal &mdash; it is pushing intercooler exhaust into the condenser.</td>
<td>Costs face velocity for everything behind it and blocks the intercooler's own exit path.</td>
<td><span class="pill p-bad">Skip this one.</span> Its only benefit is at a standstill, which is
the one condition where you should not be making boost.</td></tr>
</tbody></table></div>
<p class="note">If shortening the condenser frees 40&ndash;60 mm, spend it on the duct and on an
engine-bay exit path before you spend it on a fan.</p>
</section>
""" % dict(duty=duty_rows())

def surge_rows():
    out = []
    for s in R4["surgeSweep"]:
        if s["rpm"] > 4000: continue
        if s["margin"] < 0:  c, v = "p-bad", "inside the surge line"
        elif s["margin"] < 2: c, v = "p-warn", "on the surge line"
        elif s["margin"] < 6: c, v = "p-info", "thin margin"
        else: c, v = "p-ok", "clear"
        out.append("<tr><td>%d rpm</td><td class=\"num\">%.1f</td><td class=\"num\">%.1f</td>"
                   "<td class=\"num\">%+.1f</td><td><span class=\"pill %s\">%s</span></td></tr>"
                   % (s["rpm"], s["lb"], s["surge"], s["margin"], c, v))
    return "\n".join(out)

TURBO = """
<section id="turbo">
<h2><span class="num">10</span>Turbo &mdash; EFR 7163, and the one thing to fix in the tune</h2>

<div class="callout c-good"><b>The turbo is not changing.</b> It is the BorgWarner EFR 7163 you
own. No turbo change is recommended in this report. Solved properly, at 30 psi it sits at 86%% of
its choke line and PR %(pr).2f against a 3.6 ceiling &mdash; it has headroom in both directions.
Earlier rounds contained a Garrett recommendation; it is withdrawn. The survey of alternatives is
kept in &sect;17 purely as a record of what was considered and rejected.</div>

<div class="chartbox">
<h4>Official BorgWarner EFR 7163 compressor map, with your operating points</h4>
<div id="ch_r4_map"></div>
<p class="note">Efficiency contour values, speed lines, axis extents and wheel diameters are the
official sheet's own printed labels. The surge and choke coordinates are digitised off the printed
plot and carry roughly &plusmn;1.5 lb/min.</p>
</div>

<h3>The low-rpm surge finding</h3>
<p>Holding full boost below about 3,000 rpm puts this compressor on or inside its surge line. At
PR %(pr).2f the official surge line sits at 20.9 lb/min. The engine only swallows that much at
about 2,750 rpm. Below that, commanding 30 psi asks the compressor for pressure it cannot sustain
at that flow.</p>

<div class="scroll"><table>
<thead><tr><th>Engine speed</th><th class="num">Airflow at 30 psi, lb/min</th>
<th class="num">Surge line at PR %(pr).2f</th><th class="num">Margin</th><th>Verdict</th></tr></thead>
<tbody>
%(surge)s
</tbody></table></div>

<div class="rec"><h3>The fix, and it is free</h3>
<p style="margin-top:0">This is a boost target table problem, not a hardware problem. In the Link
G4X, schedule boost against rpm so the target ramps in rather than stepping to 30 psi:</p>
<div class="specline"><span class="k">Below 2,750 rpm</span><span class="v">command no more than 12&ndash;15 psi</span></div>
<div class="specline"><span class="k">2,750 to 3,500 rpm</span><span class="v">ramp linearly to the full target</span></div>
<div class="specline"><span class="k">Above 3,500 rpm</span><span class="v">full target &mdash; at least 6 lb/min of surge margin everywhere</span></div>
<p class="note" style="margin-bottom:0">In practice the turbo cannot make 30 psi at 2,500 rpm
anyway, so this mostly protects against an aggressive wastegate duty table and against lugging the
engine in too high a gear. Set it before the first tune. It is much easier than diagnosing a
rattling noise under load afterwards.</p></div>

<p class="note"><b>Still uncertain.</b> The surge line was read off a printed plot at screen
resolution, not from BorgWarner's underlying data. Treat the 2,750 rpm crossover as
<b>&plusmn;250 rpm</b>. You have the EFR speed sensor on SI-3 and a 5 bar MAP sensor &mdash;
logging shaft speed against MAP and airflow settles it in one session.</p>
</section>
""" % dict(pr=R4["hero"]["pr"], surge=surge_rows())

def drive_rows():
    return "\n".join(
        "<tr%s><td class=\"num\">%.2f</td><td class=\"num\">%.0f%%</td><td class=\"num\"><b>%d</b></td>"
        "<td>%s</td></tr>"
        % (' style="background:#12251f"' if b["f"] == 0.80 else "", b["f"], b["loss"], b["whp"],
           b["case"])
        for b in R4["driveline"]["band"])

def ladder_rows():
    return "\n".join(
        "<tr%s><td>%d psi</td><td class=\"num\">%.2f</td><td class=\"num\">%.1f</td>"
        "<td class=\"num\">%.0f%%</td><td class=\"num\">%.0f &deg;C</td>"
        "<td class=\"num\"><b>%d</b></td><td class=\"num\">%d&ndash;%d</td></tr>"
        % (' style="background:#12251f"' if l["boost"] == 30 else "", l["boost"], l["pr"],
           l["lb"], l["lb"] / 60 * 100, l["iat"], l["whp"], l["whp_lo"], l["whp_hi"])
        for l in R4["ladder"] if l["rpm"] == 7500)

POWER = """
<section id="power">
<h2><span class="num">11</span>Power &mdash; the estimate and its error band</h2>

<div class="callout c-bad"><b>Stated plainly.</b> This engine has never run on a dynamometer. It is
not finished. Every horsepower figure in this report is the output of a model: airflow from
displacement &times; rpm &times; volumetric efficiency &times; charge density, converted at 10.0
crank hp per lb/min and a driveline factor. Three of those five terms are estimates. The only
thing that turns this report into fact is a dyno sheet and a data log.</div>

<div class="grid g4">
<div class="kpi"><div class="lab">Design point</div><div class="val">%(whp)d whp</div>
<div class="note">%(crank)d crank, 7,500 rpm, 30 psi, E85</div></div>
<div class="kpi"><div class="lab">Honest band</div><div class="val w">%(lo)d&ndash;%(hi)d</div>
<div class="note">9.5&ndash;10.5 hp/lb-min, 0.78&ndash;0.83 driveline</div></div>
<div class="kpi"><div class="lab">Air mass flow</div><div class="val">%(lb).1f lb/min</div>
<div class="note">86%% of the 7163's 60 lb/min choke line</div></div>
<div class="kpi"><div class="lab">Charge temp at the valve</div><div class="val g">%(iat).0f &deg;C</div>
<div class="note">102 mm core, ducted, 32 &deg;C ambient</div></div>
</div>

<h3>Across the boost range, at 7,500 rpm</h3>
<div class="scroll"><table>
<thead><tr><th>Boost</th><th class="num">PR</th><th class="num">lb/min</th>
<th class="num">%% of choke</th><th class="num">Charge temp</th><th class="num">whp</th>
<th class="num">Band</th></tr></thead>
<tbody>
%(ladder)s
</tbody></table></div>

<h3>Where the uncertainty actually lives</h3>
<div class="scroll"><table>
<thead><tr><th class="num">Driveline factor</th><th class="num">Loss</th><th class="num">whp</th>
<th>Case</th></tr></thead>
<tbody>
%(drive)s
</tbody></table></div>
<div class="chartbox"><h4>Driveline band</h4><div id="ch_r4_drive"></div></div>

<h3>Cross-check against published results</h3>
<div class="chartbox"><h4>Wheel horsepower per litre &mdash; this model against community dynos</h4>
<div id="ch_r4_dyno"></div>
<p class="note">None of these is this car. They are used only to bound the model. Dyno type
matters: inertia dynos such as the Dynojet commonly read 5&ndash;10%% high on all-wheel drive.</p>
</div>
<ul class="tight">
<li><b>Nearest comparable:</b> a 3S-GTE on an EFR 7163 on E85 at 25 psi, reported at 402 whp. This
model gives 371 whp at 25 psi &mdash; 8%% below. Explained by this model's 32 &deg;C, 2,100 ft
design point and its 20%% all-wheel-drive loss. <span class="pill p-ok">Conservative by a
defensible amount</span></li>
<li><b>Specific output:</b> %(perl).0f whp per litre modelled, against 200&ndash;258 across the
EFR 7163 community results. At or just below the bottom of the band, which is where an AWD car at
a hot, thin-air design point belongs. <span class="pill p-ok">Consistent</span></li>
<li><b>Same chassis:</b> an ST185 with a .50 turbo at 14 psi on 91 octane, 337 whp on a Dynojet.
Scaling that car's airflow to 30 psi on E85 lands in 400&ndash;440 whp.
<span class="pill p-ok">Consistent</span></li>
<li><b>Is 600 whp reachable?</b> No, not on 2.19 L with this turbo. It would need about 75 lb/min,
past the official 7163 envelope at any pressure ratio the bottom end would survive.</li>
</ul>
<p class="note"><b>How to read the community numbers:</b> self-reported, different dynos, different
altitudes, different correction factors, strong publication bias toward good results. Worth using
to answer "is this model in the right region". Worth nothing for answering "what will my car
make". That answer costs one dyno session.</p>
</section>
""" % dict(whp=R4["hero"]["whp"], crank=R4["hero"]["crank"], lo=R4["hero"]["whp_lo"],
           hi=R4["hero"]["whp_hi"], lb=R4["hero"]["lb"], iat=P25["iat"],
           ladder=ladder_rows(), drive=drive_rows(), perl=R4["modelPerL"])

MANIFOLD = """
<section id="manifold">
<h2><span class="num">12</span>Manifold pairing &mdash; validated, nothing to do</h2>
<div class="callout c-good"><b>The manifold is paired correctly.</b> An earlier round said it was
wrong, based on diagrams that were drawn before the pairing was corrected. As built it is
<b>1+4 / 2+3</b>, which is right for a 1-3-4-2 firing order. The recommendation to re-make it is
withdrawn. Nothing to fix, nothing to buy. The arithmetic is kept below because it is the check to
run against the physical part if the pairing is ever in doubt again.</div>

<div class="eq">firing order 1-3-4-2, so power strokes begin at:  cyl 1 = 0&deg;   cyl 3 = 180&deg;   cyl 4 = 360&deg;   cyl 2 = 540&deg;
HKS 264 exhaust cam: 264&deg; duration, exhaust valve opens about 135&deg; after firing TDC

two cylinders 360&deg; apart in the cycle:  360 &minus; 264 = <b>96&deg; of clear gap</b>
two cylinders 180&deg; apart in the cycle:  264 &minus; 180 = <b>84&deg; of overlap</b>

AS BUILT   1+4 are 360&deg; apart &rarr; 96&deg; clear    2+3 are 360&deg; apart &rarr; 96&deg; clear
the other way   1+2 are 180&deg; apart &rarr; 84&deg; overlap    3+4 are 180&deg; apart &rarr; 84&deg; overlap</div>

<p class="note">The general rule, matching published twin-scroll guidance: pair the cylinder that
fires first with the one that fires third, and the second with the fourth. On 1-3-4-2 that is 1
with 4 and 3 with 2. That is what is on the car.</p>

<div class="chartbox"><h4>Exhaust valve events across one 720&deg; cycle</h4><div id="ch_pulse"></div>
<p class="note">Each bar is one cylinder's exhaust valve open period. Upper panel is the pairing
shown in the superseded diagram, where the two bars sharing a scroll overlap by 84&deg;. Lower
panel is what is on the car, where they do not overlap at all.</p></div>

<h3>What having it right is worth</h3>
<div class="scroll"><table>
<thead><tr><th>Effect</th><th>Value</th><th>Confidence</th></tr></thead>
<tbody>
<tr><td>Exhaust backpressure</td><td>EMAP/IMAP about 1.6 rather than about 2.0. Every power figure
in this report already assumes 1.6, so nothing needs adjusting.</td>
<td><span class="pill p-info">Direction certain, magnitude modelled</span></td></tr>
<tr><td>Peak power</td><td>About 7 whp you already have. Lower manifold pressure means less
residual exhaust gas displacing fresh charge.</td>
<td><span class="pill p-info">Medium</span></td></tr>
<tr><td>Spool threshold</td><td>300&ndash;500 rpm earlier than a mis-paired manifold. This is the
effect twin-scroll exists for, and you are receiving it.</td>
<td><span class="pill p-ok">High &mdash; best supported</span></td></tr>
<tr><td>Knock margin</td><td>Lower residual fraction means a cooler, less knock-prone charge. On
E85 this matters less than on pump fuel, but it is not nothing.</td>
<td><span class="pill p-neu">Directional only</span></td></tr>
</tbody></table></div>

<div class="rec"><h3>What to do</h3>
<div class="specline"><span class="k">Verdict</span><span class="v">Correct. Do not re-make it. Do not fit an undivided housing.</span></div>
<div class="specline"><span class="k">Verify once, visually</span><span class="v">Cylinders 1 and 4 share one scroll, 2 and 3 the other. Five minutes with a torch.</span></div>
<div class="specline"><span class="k">Do it before wrapping</span><span class="v">Afterwards it is a much worse job.</span></div>
<div class="specline"><span class="k">Then measure it</span><span class="v">An exhaust backpressure gauge before the turbine turns the 1.6 assumption into a number.</span></div>
<div class="specline"><span class="k">If it logs worse than 1.6</span><span class="v">Roughly &minus;2 whp per 0.1. The cause would be turbine housing A/R or wastegate sizing, not pairing.</span></div>
</div>
</section>
"""

def turbo_survey():
    rows = []
    for t in R4.get("turbos", []) or []:
        pass
    old = json.load(open("r5_turbo_survey.json"))
    for t in old:
        keep = t["n"].startswith("EFR 7163")
        if t.get("ghost"):
            note = "Withdrawn &mdash; this part number does not appear in Garrett's catalogue."
            cls = "p-bad"
        elif t["n"].startswith("Garrett"):
            note = "Rejected. No official Garrett map was ever read; efficiency is modelled only."
            cls = "p-bad"
        elif keep:
            note = "<b>Retained. This is the turbo on the car.</b>"
            cls = "p-ok"
        elif t["choke"] < 60:
            note = ("Rejected. Spools earlier, but runs out of flow before the 7163 does "
                    "and you would have to buy it.")
            cls = "p-warn"
        else:
            note = "Rejected. More top end, later spool, and you would have to buy it."
            cls = "p-warn"
        rows.append("<tr%s><td>%s</td><td class=\"num\">%d</td><td class=\"num\">%.2f</td>"
                    "<td class=\"num\">%.1f</td><td class=\"num\">%d</td><td class=\"num\">$%s</td>"
                    "<td><span class=\"pill %s\">%s</span></td></tr>"
                    % (' style="background:#12251f"' if keep else "", t["n"], t["choke"],
                       t["eta"], t["pr_max"], t["spool"], "{:,}".format(t["price"]), cls, note))
    return "\n".join(rows)

REJECTED = """
<section id="rejected">
<h2><span class="num">13</span>Considered and rejected</h2>
<p class="lede">Kept only so the record is complete. <b>Nothing in this section is a
recommendation.</b></p>

<div class="callout c-warn"><b>Read this table as history, not advice.</b> This is a survey of
turbochargers that were considered in earlier rounds and rejected. <b>The EFR 7163 is retained and
no turbo change is recommended.</b> The Garrett entries in particular rest on modelled efficiency,
because no official Garrett compressor map was read in any round of this work. The G25-770 does not
appear in Garrett's catalogue at all and is withdrawn entirely.</div>

<div class="scroll"><table>
<thead><tr><th>Unit</th><th class="num">Choke, lb/min</th><th class="num">Peak &eta;</th>
<th class="num">PR ceiling</th><th class="num">Spool, rpm</th><th class="num">Price</th>
<th>Status</th></tr></thead>
<tbody>
%(turbos)s
</tbody></table></div>

<h3>Ideas dropped from earlier rounds, and why</h3>
<div class="scroll"><table>
<thead><tr><th>Dropped</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Joint diameter step analysis, the 24 Pa figure, coupler concentricity, taper cone angle
optimisation</td>
<td>Three or four joints, each an inch or less of effective length, in a 2.6 m run, downstream of a
core that generates far more turbulence. The effect is smaller than the uncertainty in the model.
One sentence in &sect;07 now covers it.</td></tr>
<tr><td>The 2.5 to 3.0 in taper at the throttle body</td>
<td>You own the adapter, and after the throttle the air enters a large plenum, a smaller plenum,
then individual runners. Nothing about the pipe geometry survives that. The throttle end is
solved.</td></tr>
<tr><td>Stepping the cold side up after the core</td>
<td>Recovers nothing &mdash; the pressure was lost in the core. It adds volume above the
compressor's flow limit, which adds transient delay. It was a myth and it is gone.</td></tr>
<tr><td>The packaging comparison between a welded 3 in pipe and a coupled 2.5 in pipe</td>
<td>It was wrong. A welded 3 in pipe is 3 in; a weld bead does not add half an inch. A 2.5 in pipe
inside a silicone coupler with the ends butted has effectively no size change across the joint and
cannot become 3 in inside diameter. Coupler outside diameter is not a packaging argument and is not
used as one anywhere in this report.</td></tr>
<tr><td>The SpeedFactory SS-850 as the design constraint</td>
<td>You can have a core built to any dimensions with any port size. Off-the-shelf availability is
not a constraint. &sect;08 specifies the core on merit; &sect;18 lists places that will build it.</td></tr>
<tr><td>Any argument that depends on avoiding expansions in the charge path</td>
<td>The EFR 7163 compressor outlet is 2.0 in. The charge pipe is already an expansion from the
turbo. The argument was inconsistent with the hardware.</td></tr>
<tr><td>Bar and plate against tube and fin, at length</td>
<td>The public test data does not agree with itself, the spread between the two is smaller than the
ducting decision by a factor of three, and you are having a core made. Specify bar and plate at
14&ndash;16 FPI and stop.</td></tr>
<tr><td>Machining billet end tanks</td>
<td>Cost and lead time far exceed the benefit at this power level. Fabricated tapered tanks with a
vane are the answer.</td></tr>
</tbody></table></div>
</section>
""" % dict(turbos=turbo_survey())

R5X = json.loads(re.search(r"var R5X=(\{.*\});", open("r5_extra.js", encoding="utf-8").read(), re.S).group(1))
PKG = R5X["pkg"]
REC = PKG[0]

def pkg_rows():
    out = []
    for p in PKG:
        best = p["label"] == "Recommended package"
        cls = ("p-ok" if best else
               "p-bad" if p["label"] in ("Small pipe", "Step up after the core") else "p-info")
        tag = ("Build this" if best else
               "No PR margin" if p["label"] == "Small pipe" else
               "No gain, more lag" if p["label"] == "Step up after the core" else
               "Aperture decides" if "aperture" in p["label"] else
               "Works, not chosen")
        out.append("<tr%s><td><b>%s</b><br><span class=\"note\">%s</span></td>"
                   "<td class=\"num\">%.2f</td><td class=\"num\">%.2f</td>"
                   "<td>%s</td><td>%d &times; %d &times; %d</td>"
                   "<td class=\"num\">%.2f</td><td class=\"num\">%.3f</td>"
                   "<td class=\"num\">%.1f</td><td class=\"num\"><b>%d</b><br>"
                   "<span class=\"note\">%d&ndash;%d</span></td><td class=\"num\">%d</td>"
                   "<td class=\"num\">%.1f</td><td><span class=\"pill %s\">%s</span></td></tr>"
                   % (' style="background:#12251f"' if best else "", p["label"], p["note"],
                      p["hot"], p["cold"],
                      ("%.2f" % p["hot"]) if p["hot"] == p["cold"]
                      else ("%.2f in / %.2f out" % (p["hot"], p["cold"])),
                      p["w"], p["h"], p["t"], p["dp"], p["pr"], p["iat"], p["whp"],
                      p["whp_lo"], p["whp_hi"], p["fill"], p["cap"], cls, tag))
    return "\n".join(out)

PACKAGE = """
<section id="package">
<h2><span class="num">06</span>The complete package</h2>
<p class="lede">Everything that has to match, in one place, and then what the realistic alternatives
are worth against it.</p>

<div class="rec">
<h3>Build this</h3>
<div class="specline"><span class="k">Turbo inlet pipe</span><span class="v">3.00 in OD, short, to the 2.50 in compressor inlet</span></div>
<div class="specline"><span class="k">Compressor outlet</span><span class="v">2.00 in (fixed by the turbo)</span></div>
<div class="specline"><span class="k">Hot pipe</span><span class="v">2.50 in OD &times; 0.065 in wall &mdash; steps up at the turbo, no further transitions</span></div>
<div class="specline"><span class="k">Intercooler inlet port</span><span class="v">2.50 in OD stub</span></div>
<div class="specline"><span class="k">Core</span><span class="v">aperture width &minus; 20 mm, &times; 305 mm &times; 102 mm</span></div>
<div class="specline"><span class="k">Intercooler outlet port</span><span class="v">2.50 in OD stub</span></div>
<div class="specline"><span class="k">Cold pipe</span><span class="v">2.50 in OD &times; 0.065 in wall &mdash; no step up, all the way to the throttle adapter</span></div>
<div class="specline"><span class="k">Throttle transition</span><span class="v">none. The 3 in hose adapter you already own does it.</span></div>
<div class="specline"><span class="k">Blow-off valve</span><span class="v">cold pipe, within 300 mm of the throttle &mdash; &sect;10</span></div>
<div class="specline"><span class="k">Charge IAT sensor</span><span class="v">cold pipe, mid-run, side of the pipe &mdash; &sect;11</span></div>
<div class="specline"><span class="k">Total transitions in the charge path</span><span class="v"><b>one</b>, at the turbo, and it is unavoidable</span></div>
</div>

<h3>Realistic combinations, and what each is worth</h3>
<div class="scroll"><table>
<thead><tr><th>Package</th><th class="num">Hot</th><th class="num">Cold</th><th class="num">Ports</th>
<th>Core W &times; H &times; T</th><th class="num">System &Delta;P, psi</th><th class="num">PR</th>
<th class="num">Charge temp &deg;C</th><th class="num">whp</th><th class="num">Fill, ms</th>
<th class="num">Max boost</th><th>Verdict</th></tr></thead>
<tbody>
%(rows)s
</tbody></table></div>

<h4>How to read that table</h4>
<ul class="tight">
<li><b>Every row is within 9 whp of every other row</b>, and the honest error band on any one of
them is about &plusmn;13 whp. Only the core-width rows and the core-thickness rows are
distinguishable at all, and only because they move charge temperature.</li>
<li><b>The step-up-after-the-core row makes the same power</b> as the recommended package and takes
%(dstep)d ms longer to fill. That is the whole cost of the myth, priced.</li>
<li><b>The small-pipe row is the only one that changes what the engine can do</b> &mdash; it caps
boost at %(cap225).1f psi where everything else reaches %(cap25).1f or better.</li>
<li>So: pick the core width off the aperture measurement, build both pipes at 2.50 in, and stop
optimising.</li>
</ul>
</section>
""" % dict(rows=pkg_rows(), dstep=PKG[7]["fill"] - REC["fill"],
           cap225=PKG[5]["cap"], cap25=REC["cap"])

def inlet_rows():
    out = []
    for i in R5X["inlet"]:
        if i["od"] == 2.5: c, v = "p-bad", "Too fast. This is the compressor inlet size, not a pipe size."
        elif i["od"] == 3.0: c, v = "p-ok", "<b>Recommended.</b>"
        elif i["od"] == 3.5: c, v = "p-info", "Better still if it routes. Diminishing."
        else: c, v = "p-warn", "No measurable gain over 3.5 in. Hard to route."
        out.append("<tr%s><td><b>%.2f in</b></td><td class=\"num\">%.1f</td>"
                   "<td class=\"num\">%d</td><td class=\"num\">%.2f</td>"
                   "<td class=\"num\">%.3f</td><td><span class=\"pill %s\">%s</span></td></tr>"
                   % (' style="background:#12251f"' if i["od"] == 3.0 else "", i["od"],
                      i["id_mm"], i["fts"], i["mach"], i["dp"], c, v))
    return "\n".join(out)

def dep_rows():
    return "\n".join(
        "<tr><td class=\"num\">%.2f psi</td><td class=\"num\">%.1f</td><td class=\"num\">%.3f</td>"
        "<td class=\"num\">%d &deg;C</td><td><span class=\"pill %s\">%s</span></td></tr>"
        % (d["dp"], d["p_in"], d["pr"], d["tc"],
           "p-bad" if d["over"] else ("p-warn" if d["pr"] > 3.55 else "p-ok"),
           "past the 3.60 ceiling" if d["over"] else
           ("almost no margin" if d["pr"] > 3.55 else "fine"))
        for d in R5X["dep"])

INLET = """
<section id="inlet">
<h2><span class="num">09</span>Turbo inlet pipe</h2>
<p class="lede">This turned out to matter more than the charge pipe does. Half a psi of inlet
restriction pushes the compressor past its pressure-ratio ceiling.</p>

<div class="rec">
<h3>3.00 in OD inlet pipe, as short as the route allows, into the 2.50 in compressor inlet</h3>
<div class="specline"><span class="k">EFR 7163 compressor inlet</span><span class="v">2.50 in (63.5 mm) hose connection &mdash; a fact, not a choice</span></div>
<div class="specline"><span class="k">Inlet pipe</span><span class="v">3.00 in OD, reducing to 2.50 in only at the turbo</span></div>
<div class="specline"><span class="k">Filter</span><span class="v">rated 800 CFM or better, 3.5 or 4 in flange</span></div>
<div class="specline"><span class="k">Length</span><span class="v">does not matter &mdash; see below</span></div>
</div>

<h4>Does length matter? No.</h4>
<p><b>With an open element filter and no mass airflow sensor, inlet length does not matter.</b>
Friction over half a metre of 3 in pipe is 0.23 psi and the difference between a short inlet and a
long routed one is a few hundredths of a psi. Route it wherever gives the coolest, cleanest air.
<b>What does matter is where the filter ends up:</b> keep it out of the radiator's exhaust air and
away from the turbine, because inlet air temperature goes straight into the compressor outlet
temperature and then into everything downstream.</p>

<h4>Diameter, at %(lb).1f lb/min and %(cfm)d CFM</h4>
<div class="scroll"><table>
<thead><tr><th>Pipe OD</th><th class="num">ID mm</th><th class="num">Velocity ft/s</th>
<th class="num">Mach</th><th class="num">&Delta;P, psi</th><th>Verdict</th></tr></thead>
<tbody>
%(inlet)s
</tbody></table></div>
<p class="note">Inlet air is roughly three times less dense than charge air, so it moves three times
faster through the same pipe. That is why the inlet pipe must be <i>larger</i> than the charge pipe
even though it carries the same mass.</p>

<h4>Why inlet restriction is a real risk on this engine</h4>
<div class="scroll"><table>
<thead><tr><th class="num">Inlet depression</th><th class="num">Compressor inlet, kPa</th>
<th class="num">PR needed for 30 psi</th><th class="num">Compressor outlet</th><th>Verdict</th></tr></thead>
<tbody>
%(dep)s
</tbody></table></div>
<div class="callout c-bad"><b>Half a psi of inlet depression costs more than every charge-pipe
decision in this report combined.</b> It raises the required pressure ratio from 3.52 to 3.65,
which is past the 7163's ceiling, and it adds 7 &deg;C to compressor outlet temperature. A
too-small filter, a crushed inlet hose, or an inlet routed through a 2.5 in pipe will all do this.
Build the inlet at 3.00 in and buy a filter with headroom.</div>

<ul class="tight">
<li><b>Filter sizing:</b> you need roughly %(cfm)d CFM at the design point. Specify a filter rated
at 800 CFM or better. An oversized filter costs nothing but space; an undersized one costs the top
of the boost range.</li>
<li><b>Measure it.</b> A cheap way to close this out: a vacuum gauge or a spare analogue input
teed into the inlet pipe just before the compressor. Anything worse than 0.3 psi at full flow means
the filter or the pipe is the restriction, and that is a fifteen-minute fix.</li>
<li>Use a 3.00 to 2.50 in silicone reducer at the turbo, not a hard cone. The turbo moves on its
mounts.</li>
</ul>
</section>
""" % dict(lb=R5X["lbmin"], cfm=R5X["cfm"], inlet=inlet_rows(), dep=dep_rows())

BOV = """
<section id="bov">
<h2><span class="num">10</span>Blow-off valve location</h2>
<p class="lede">You have a Turbosmart Kompact Dual Port. Where it goes, and the atmospheric
question, which is different for you than for most people.</p>

<div class="rec">
<h3>Cold pipe, within 300 mm of the throttle body, on the side or top of the pipe, plumbed back to the turbo inlet</h3>
<div class="specline"><span class="k">Which pipe</span><span class="v">cold side &mdash; after the intercooler</span></div>
<div class="specline"><span class="k">Distance to throttle</span><span class="v">150&ndash;300 mm</span></div>
<div class="specline"><span class="k">Clock position</span><span class="v">side or top of the pipe, never the bottom</span></div>
<div class="specline"><span class="k">Flange angle</span><span class="v">90&deg; to the pipe axis, on a straight section</span></div>
<div class="specline"><span class="k">Discharge</span><span class="v">recirculate to the turbo inlet pipe</span></div>
<div class="specline"><span class="k">Return port</span><span class="v">at least 150 mm downstream of the filter, angled about 45&deg; with the flow</span></div>
</div>

<h4>The reasoning, short</h4>
<ul class="tight">
<li><b>Cold side, near the throttle, because that is where the pressure spike happens.</b> When the
throttle shuts, the whole column of air between the closed plate and the compressor has to go
somewhere. A valve at the throttle end vents it immediately. A valve on the hot side has to wait
for the wave to travel back through the core, which is the slowest part of the system.</li>
<li><b>Not on the bottom of the pipe.</b> Oil mist and condensate collect at the low point and a
BOV that sits in it will weep and eventually stick.</li>
<li><b>On a straight section, flange square to the pipe.</b> On the outside of a bend the valve
sees a pressure gradient across its seat and can flutter at part throttle.</li>
<li><b>Atmospheric or recirculated: your MAP sensor makes both safe.</b> The rich stumble that
gives atmospheric valves a bad name is a mass-airflow problem &mdash; the MAF has already counted
air that then leaves the engine. You run speed-density on a Link G4X, so nothing is miscounted
either way.</li>
<li><b>Recirculate anyway.</b> Not for fuelling &mdash; for three other reasons: it keeps the
compressor loaded through the event instead of letting it unload against a wall, it keeps
oil-laden air out of the engine bay, and it is quieter. The Dual Port lets you split it if you want
some noise; if you do, bias it toward recirculation.</li>
<li><b>Reference line:</b> take the valve's signal from the intake plenum, not from the charge
pipe. The plenum is what actually sees the throttle close.</li>
</ul>
<p class="note"><b>What would change this:</b> if the only place the valve physically fits is the
hot pipe, fit it there. The difference is a few tens of milliseconds of relief and some noise. It
is not worth a compromised route or a bad weld.</p>
</section>
"""

IATSENSOR = """
<section id="iat">
<h2><span class="num">11</span>Charge pipe IAT sensor</h2>
<p class="lede">An Volt 6 on the FuryX is reserved for this. The point of the sensor is to turn the
whole of this report into a measurement on the first drive, so it has to be somewhere the number
can be trusted.</p>

<div class="rec">
<h3>Cold pipe, mid-run, side of the pipe, probe tip a third of the way in</h3>
<div class="specline"><span class="k">Which pipe</span><span class="v">cold side, after the intercooler</span></div>
<div class="specline"><span class="k">Distance from the core outlet</span><span class="v">at least 400 mm (about 6 pipe diameters)</span></div>
<div class="specline"><span class="k">Distance to the throttle</span><span class="v">at least 250 mm (about 4 diameters)</span></div>
<div class="specline"><span class="k">Distance from any bend exit</span><span class="v">at least 250 mm</span></div>
<div class="specline"><span class="k">Distance from the BOV port</span><span class="v">at least 250 mm, and upstream of it if possible</span></div>
<div class="specline"><span class="k">Clock position</span><span class="v">3 or 9 o'clock &mdash; the side of the pipe</span></div>
<div class="specline"><span class="k">Orientation</span><span class="v">probe axis perpendicular to the pipe axis</span></div>
<div class="specline"><span class="k">Insertion depth</span><span class="v">20&ndash;25 mm into a 60.2 mm bore &mdash; tip in the middle third, not on the centreline, not near the wall</span></div>
<div class="specline"><span class="k">Bung</span><span class="v">weld-on aluminium, 3/8 in NPT female</span></div>
<div class="specline"><span class="k">Sensor</span><span class="v">exposed-element NTC, 3/8 NPT &mdash; Bosch 0 280 130 039 or the GM 25037225 equivalent</span></div>
</div>

<h4>Why each of those numbers</h4>
<div class="scroll"><table>
<thead><tr><th>Rule</th><th>What it protects against</th></tr></thead>
<tbody>
<tr><td>400 mm downstream of the core outlet</td>
<td>Air leaving an end tank is stratified &mdash; the tubes nearest the outlet run cooler than the
far ones. Close to the outlet the sensor reads one stream, not the mixture. Six diameters is enough
mixing length to read the average.</td></tr>
<tr><td>250 mm from any bend exit</td>
<td>Flow separates off the inside of a bend and reattaches downstream. Inside that region there is
a temperature and velocity gradient across the pipe, so the reading depends on exactly where the
tip sits.</td></tr>
<tr><td>250 mm from the BOV port and preferably upstream of it</td>
<td>The BOV tee is a dead branch. Air sits in it, cools between events, and washes back into the
main flow when the valve cycles. It puts a transient error on the reading at exactly the moments
you most want to look at the log.</td></tr>
<tr><td>Side of the pipe, not the bottom</td>
<td>Condensate and oil mist pool at the low point. A wetted element reads low, and it reads low
inconsistently, which is worse than reading low consistently.</td></tr>
<tr><td>Tip 20&ndash;25 mm in, not flush and not across</td>
<td>Flush with the wall reads pipe wall temperature, which lags and is influenced by radiant heat
from the engine bay. All the way across puts the tip in the far boundary layer and adds a vibration
failure mode. The middle third of the bore is the free stream.</td></tr>
<tr><td>Exposed element, not a closed brass body</td>
<td>A shielded sensor has a time constant of several seconds. You want to see the intercooler
recover between pulls, and that is a several-second event. An exposed bead responds in well under a
second.</td></tr>
<tr><td>Shield it if it can see the turbo or the manifold</td>
<td>An exposed bead in line of sight of a red-hot turbine housing reads high by a genuinely large
amount at low airspeed &mdash; which is exactly the heat-soak condition you want to measure.</td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>One sensor measures the outcome, not the effectiveness.</b>
Effectiveness is &epsilon; = (T<sub>in</sub> &minus; T<sub>out</sub>) / (T<sub>in</sub> &minus;
T<sub>ambient</sub>), and you will have T<sub>out</sub> and T<sub>ambient</sub> but not
T<sub>in</sub> &mdash; the compressor outlet temperature. <b>Weld a second, blanked 3/8 NPT bung
into the hot pipe now</b>, about 300 mm downstream of the turbo. It costs nothing while the pipe is
on the bench, it lets you drop in a thermocouple for one session, and without it every
effectiveness number stays a model output rather than a measurement.</div>

<h4>What to log on the first drive</h4>
<ul class="tight">
<li>Charge IAT (An Volt 6), ambient IAT, MAP, EFR shaft speed (SI-3), throttle position, road
speed.</li>
<li>Two runs matter: <b>a sustained third-gear climb</b> for the steady-state number, and
<b>back-to-back pulls with 20 seconds between</b> for the recovery number. The second one is what
tells you whether the core is big enough.</li>
<li>Compare the logged charge IAT against the %(iat).0f &deg;C this report predicts at 30 psi and
32 &deg;C ambient. If it lands within 5 &deg;C, the model is doing its job. If it is 15 &deg;C
high, look at the duct seal before you look at the core.</li>
</ul>
</section>
""" % dict(iat=REC["iat"])

VENDORS = """
<section id="vendors">
<h2><span class="num">18</span>Parts, vendors and what it costs</h2>
<p class="lede">Two ways to get the core: buy an assembled intercooler close to the spec, or buy a
bare core and have tanks fabricated. Both are costed below. Prices are August 2026 US retail.
<b>Anything marked <span class="pill p-warn">unverified</span> is an estimate I could not confirm
on a live listing &mdash; treat it as a budget figure, not a quote.</b></p>

<h3>Bare cores that match the specification</h3>
<p class="note">Garrett publishes a bare-core catalogue with part numbers and dimensions. These are
the entries that land on the aperture table in &sect;08, so you can pick the part number the moment
you have the measurement.</p>
<div class="scroll"><table>
<thead><tr><th>Part number</th><th>W &times; H &times; T, mm</th><th class="num">Rated hp</th>
<th>Matches which aperture</th><th class="num">Price</th></tr></thead>
<tbody>
<tr style="background:#12251f"><td><b>Garrett 486827-6002</b></td><td><b>602 &times; 305 &times; 97</b></td>
<td class="num">1000</td><td><b>620&ndash;660 mm opening. The closest catalogue part to the
recommendation.</b></td><td class="num">$476<br><span class="note">Real Street, live listing</span></td></tr>
<tr><td>Garrett 703518-6005</td><td>610 &times; 307 &times; 76</td><td class="num">900</td>
<td>Same width, 3 in deep. Only if depth were a problem, and it is not.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified</span></td></tr>
<tr><td>Garrett 703520-6005</td><td>610 &times; 307 &times; 89</td><td class="num">925</td>
<td>Same width, 3.5 in deep. The fallback if 97&ndash;102 mm cannot be sourced.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified</span></td></tr>
<tr><td>Garrett 703522-6005</td><td>610 &times; 307 &times; 114</td><td class="num">950</td>
<td>Same width, 4.5 in deep. The thickness table says stop before here.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified</span></td></tr>
<tr><td>Garrett 848054-6021</td><td>681 &times; 264 &times; 102</td><td class="num">950</td>
<td>Wide aperture, shorter core. Good if the opening is wide but shallow.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified</span></td></tr>
<tr><td>Garrett 703522-6004</td><td>457 &times; 307 &times; 114</td><td class="num">785</td>
<td>Narrow aperture, buying depth back. This is the "under 460 mm" row in &sect;08.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified</span></td></tr>
<tr><td>Garrett 703520-6002</td><td>356 &times; 307 &times; 89</td><td class="num">550</td>
<td>Only if the opening turns out to be very small. Rated below your demand.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified</span></td></tr>
<tr><td>Treadstone C1245 bare core</td><td>559 &times; 318 &times; 114</td><td class="num">1000</td>
<td>560&ndash;600 mm opening, if you accept 4.5 in depth.</td>
<td class="num">&mdash; <span class="pill p-warn">unverified &mdash; listing exists, price not shown</span></td></tr>
</tbody></table></div>
<p class="note">Sources: <a href="https://www.garrettmotion.com/wp-content/uploads/2020/10/Garrett_Performance_Intercooler_Cores_Price_Update_Sell_Sheet.pdf">Garrett
intercooler core part number and dimension sheet</a> &middot;
<a href="https://www.realstreetperformance.com/cac-23-72-x-12-02-x-3-82-air-air.html">Real Street
Performance listing for 486827-6002</a> &middot;
<a href="https://www.treadstoneperformance.com/c1245-intercooler-core/p104569">Treadstone C1245
core</a> &middot; <a href="https://www.garrettmotion.com/">Garrett Motion</a>.</p>

<h3>Assembled intercoolers close to the specification</h3>
<div class="scroll"><table>
<thead><tr><th>Unit</th><th>Core, mm</th><th>Ports</th><th class="num">Price</th><th>Note</th></tr></thead>
<tbody>
<tr><td><a href="https://www.treadstoneperformance.com/tr1245-intercooler-1000hp/p104562">Treadstone TR1245</a></td>
<td>559 &times; 318 &times; 114</td><td>3.0 in</td><td class="num">$549</td>
<td>Cast tanks with a divided inlet. Ports are 3 in, so you would either run 3 in pipe or take the
one transition. Fits a 580 mm or wider opening.</td></tr>
<tr><td>Treadstone TR1245R</td><td>559 &times; 318 &times; 114</td><td>3.0 in</td>
<td class="num">$649</td><td>Higher rating, same geometry. You do not need it.</td></tr>
<tr><td>Custom build to the &sect;08 spec</td><td>your aperture &times; 305 &times; 102</td>
<td>2.50 in</td><td class="num">$650&ndash;900 <span class="pill p-warn">unverified</span></td>
<td>What a fabricator charges to build the exact spec with 2.50 in ports and tapered vaned tanks.
This is the path that needs no compromise.</td></tr>
</tbody></table></div>

<h3>Pipework, clamps and fittings</h3>
<div class="scroll"><table>
<thead><tr><th>Item</th><th>Part</th><th class="num">Qty</th><th class="num">Unit</th>
<th class="num">Line</th></tr></thead>
<tbody>
<tr><td>2.50 in 90&deg; aluminium mandrel bend, 6061</td>
<td><a href="https://vibrantperformance.com/aluminum-90-mandrel-bends-v1280/">Vibrant V1280</a>,
2.50 in OD</td><td class="num">4</td><td class="num">$48</td><td class="num">$192</td></tr>
<tr><td>2.50 in 45&deg; aluminium mandrel bend</td>
<td><a href="https://vibrantperformance.com/aluminum-45-mandrel-bends-v1283/">Vibrant V1283</a>,
2.50 in OD</td><td class="num">3</td><td class="num">$48</td><td class="num">$144</td></tr>
<tr><td>2.50 in straight tube, 6061, 5 ft</td>
<td><a href="https://vibrantperformance.com/tubing-and-bends/aluminum-tubing-bends-and-accessories/">Vibrant
aluminium straight tubing</a></td><td class="num">1</td>
<td class="num">$55 <span class="pill p-warn">unverified</span></td><td class="num">$55</td></tr>
<tr><td>2.50 in aluminium V-band flange assembly</td>
<td><a href="https://www.autozone.com/p/vibrant-performance-exhaust-clamp-11490/1353107">Vibrant
11490</a> &mdash; aluminium, welds to aluminium pipe</td><td class="num">3</td>
<td class="num">$80 <span class="pill p-warn">unverified</span></td><td class="num">$240</td></tr>
<tr><td>2.50 in stainless V-band flange assembly, if you prefer steel</td>
<td><a href="https://puredieselpower.com/products/universal-products/flanges-and-clamps/vibrant-1490-stainless-v-band-flange-assembly.html">Vibrant
1490</a></td><td class="num">&mdash;</td>
<td class="num">$85 <span class="pill p-warn">unverified</span></td><td class="num">&mdash;</td></tr>
<tr><td>2.50 in 4-ply silicone couplers, straight</td>
<td><a href="https://vibrantperformance.com/4-ply-aramid-reinforced-silicone-couplers/">Vibrant
4-ply aramid</a></td><td class="num">4</td>
<td class="num">$22 <span class="pill p-warn">unverified</span></td><td class="num">$88</td></tr>
<tr><td>3.00 to 2.50 in silicone reducer, turbo inlet</td><td>Vibrant 4-ply reducer</td>
<td class="num">1</td><td class="num">$28 <span class="pill p-warn">unverified</span></td>
<td class="num">$28</td></tr>
<tr><td>3.00 in aluminium tube and one bend, turbo inlet</td><td>Vibrant V1280 / straight</td>
<td class="num">1</td><td class="num">$95 <span class="pill p-warn">unverified</span></td>
<td class="num">$95</td></tr>
<tr><td>T-bolt clamps, 2.50 in</td><td><a href="https://vibrantperformance.com/hose-clamps/">Vibrant
hose clamps</a></td><td class="num">10</td>
<td class="num">$9 <span class="pill p-warn">unverified</span></td><td class="num">$90</td></tr>
<tr><td>Weld-on aluminium bung, 3/8 NPT, for the IAT sensor</td>
<td><a href="https://vibrantperformance.com/weld-bungs/">Vibrant weld bungs</a></td>
<td class="num">2</td><td class="num">$12 <span class="pill p-warn">unverified</span></td>
<td class="num">$24</td></tr>
<tr><td>Exposed-element IAT sensor, 3/8 NPT</td><td>Bosch 0 280 130 039 or GM 25037225</td>
<td class="num">1</td><td class="num">$35 <span class="pill p-warn">unverified</span></td>
<td class="num">$35</td></tr>
<tr><td>Open element air filter, 800 CFM, 3.5 in flange</td><td>K&amp;N or equivalent</td>
<td class="num">1</td><td class="num">$85 <span class="pill p-warn">unverified</span></td>
<td class="num">$85</td></tr>
<tr><td>BOV flange, weld-on</td>
<td><a href="https://vibrantperformance.com/blow-off-valve-flanges/">Vibrant BOV flange</a>, to suit
the Kompact</td><td class="num">1</td>
<td class="num">$30 <span class="pill p-warn">unverified</span></td><td class="num">$30</td></tr>
<tr><td>Blow-off valve</td><td>Turbosmart Kompact Dual Port</td><td class="num">&mdash;</td>
<td class="num">owned</td><td class="num">$0</td></tr>
</tbody></table></div>

<h3>Two paths, totalled</h3>
<div class="grid g2">
<div class="card">
<h4>Path A &mdash; bare core plus fabricated tanks</h4>
<div class="specline"><span class="k">Garrett 486827-6002 core</span><span class="v">$476</span></div>
<div class="specline"><span class="k">Tank material, 5052 sheet and 2.50 in stubs</span><span class="v">$80 <span class="pill p-warn">unverified</span></span></div>
<div class="specline"><span class="k">Tank fabrication and TIG, 2 tanks</span><span class="v">$350&ndash;500 <span class="pill p-warn">unverified</span></span></div>
<div class="specline"><span class="k">Pipework, clamps, fittings from the table</span><span class="v">$1,106</span></div>
<div class="specline"><span class="k">Ducting sheet, rivets, foam seal</span><span class="v">$120 <span class="pill p-warn">unverified</span></span></div>
<div class="specline"><span class="k"><b>Total</b></span><span class="v"><b>$2,130&ndash;2,280</b></span></div>
<p class="note" style="margin-bottom:0"><b>Choose this if</b> you want the exact spec &mdash; 2.50 in
ports, tapered vaned tanks, diagonal port placement &mdash; and you have or can hire the TIG work.
It is the only path that gives you all of &sect;08.</p>
</div>
<div class="card">
<h4>Path B &mdash; assembled unit</h4>
<div class="specline"><span class="k">Treadstone TR1245</span><span class="v">$549</span></div>
<div class="specline"><span class="k">Pipework, clamps, fittings from the table</span><span class="v">$1,106</span></div>
<div class="specline"><span class="k">Two 2.50 to 3.00 in transitions for its ports</span><span class="v">$60 <span class="pill p-warn">unverified</span></span></div>
<div class="specline"><span class="k">Ducting sheet, rivets, foam seal</span><span class="v">$120 <span class="pill p-warn">unverified</span></span></div>
<div class="specline"><span class="k"><b>Total</b></span><span class="v"><b>$1,835</b></span></div>
<p class="note" style="margin-bottom:0"><b>Choose this if</b> you want it done this month. You give
up the exact core width, and you take two port transitions. Its 114 mm depth is slightly better
for charge temperature and slightly worse for the radiator, which &sect;13 says is where that trade
stops paying. Net effect on power is under 1 whp. It is a defensible trade.</p>
</div>
</div>

<div class="callout c-info"><b>The difference between the two paths is $300 to $450 and a few weeks,
and it is worth almost nothing in power.</b> Path A is right if the aperture measurement comes back
at an awkward width, which is likely, because a made-to-order core is the only way to use a width
that nobody sells. Path B is right if the opening happens to be 580 mm or more and you would rather
be driving.</div>

<h4>Fabricators who will build a core to your dimensions</h4>
<ul class="tight">
<li><b>Treadstone Performance</b> &mdash; sells bare cores and builds custom units.
<a href="https://www.treadstoneperformance.com/cores/c3542">treadstoneperformance.com</a></li>
<li><b>Garrett bare cores</b> through Real Street Performance, T1 Race Development or Shearer
Fabrications &mdash; buy the core, have local tanks made.
<a href="https://shearerfabrications.com/collections/intercooler-cores">shearerfabrications.com</a></li>
<li><b>Plazmaman</b> (Australia) &mdash; builds to spec, long lead time, good tank design.
<a href="https://plazmaman.com/">plazmaman.com</a></li>
<li><b>Vibrant Performance</b> &mdash; the pipework, couplers, V-bands and bungs in the table above.
<a href="https://vibrantperformance.com/">vibrantperformance.com</a></li>
</ul>
</section>
"""

SOURCES = """
<section id="sources">
<h2><span class="num">19</span>Sources</h2>
<div class="scroll"><table>
<thead><tr><th>Source</th><th>Used for</th><th>Quality</th></tr></thead>
<tbody>
<tr><td><a href="https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7163-f.pdf">BorgWarner
EFR 7163 product sheet</a></td>
<td>Compressor map: efficiency contours 0.58 to 0.74, speed lines, axis extents, wheel diameters,
2.50 in compressor inlet and 2.00 in outlet, and the statement that the map applies to all 7163
units including the 7163-G twin-scroll. &sect;09, &sect;14.</td>
<td><span class="pill p-ok">Official manufacturer</span></td></tr>
<tr><td>BorgWarner EFR power range and rotor group chart</td>
<td>Confirms the 7163-G is the 0.80 A/R T4 twin-scroll wastegated unit, supercore 11637105000,
matching your TurboKits invoice.</td><td><span class="pill p-ok">Official manufacturer</span></td></tr>
<tr><td><a href="https://www.garrettmotion.com/wp-content/uploads/2020/10/Garrett_Performance_Intercooler_Cores_Price_Update_Sell_Sheet.pdf">Garrett
intercooler core sheet</a></td>
<td>Bare core part numbers and dimensions in &sect;18.</td>
<td><span class="pill p-ok">Official manufacturer &mdash; part numbers and sizes. Prices on it are
stale; live retail prices used where found.</span></td></tr>
<tr><td>Mishimoto MMRAD-CEL-89 product listing</td>
<td>Radiator overall 714 &times; 439 &times; 64.5 mm, core 699 &times; 318 &times; 51.8 mm, two
rows, 1.25 in ports. &sect;13.</td><td><span class="pill p-info">Vendor specification</span></td></tr>
<tr><td>Bosch 0 280 750 474 vendor listings (UroTuning, FCP Euro, Pelican, autohausaz)</td>
<td>Throttle body cross-references and bore. Your plate stamp of 745 used in preference.</td>
<td><span class="pill p-info">Multiple independent vendors agree</span></td></tr>
<tr><td>Outsider Garage order #7870, 5 January 2026</td>
<td>The three parts that fix the throttle end: DBW manifold adapter, 3 in hose adapter, Bosch
e-throttle.</td><td><span class="pill p-ok">Primary &mdash; your own purchase record</span></td></tr>
<tr><td>Published community dyno results &mdash; focusst.org, evolutionm.net, miataturbo.net,
mr2oc.com, alltrac.net, Link ECU forum</td>
<td>Bounding the power model in &sect;15.</td>
<td><span class="pill p-warn">Self-reported, mixed dyno types, publication bias. Used only to
answer "is the model in the right region".</span></td></tr>
<tr><td>Garrett intercooler sizing and end tank design guidance (CFD series); Willem Toet, air
ducts for motorsport</td>
<td>Duct area ratio, 7&deg; diffuser rule, side-entry tank optimum. &sect;12.</td>
<td><span class="pill p-ok">Engineering guidance from primary sources</span></td></tr>
<tr><td>Treadstone published C1245 rating: 1,142 CFM at 1.5 psi</td>
<td>The anchor point for every core &Delta;P figure, scaled quadratically.</td>
<td><span class="pill p-info">Vendor bench data</span></td></tr>
<tr><td>&epsilon;-NTU cross-flow, both fluids unmixed correlation; Taylor inlet Mach index</td>
<td>The core thermal model and the VE ceiling.</td><td><span class="pill p-ok">Textbook</span></td></tr>
<tr><td><a href="https://vibrantperformance.com/">Vibrant Performance</a>,
<a href="https://www.treadstoneperformance.com/">Treadstone</a>,
<a href="https://www.realstreetperformance.com/">Real Street Performance</a>,
<a href="https://www.summitracing.com/">Summit Racing</a></td>
<td>Part numbers and prices in &sect;18.</td>
<td><span class="pill p-warn">Live listings where marked; estimates flagged
<span class="pill p-warn">unverified</span> otherwise</span></td></tr>
<tr><td>Local: 64 OCR'd parts invoices; <code>st185-link-ecu-config</code> repo;
<code>XTREMEX-IO-TABLE.md</code>; 145 prior session transcripts</td>
<td>Every build input in &sect;02.</td><td><span class="pill p-ok">Primary</span></td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>What could not be obtained.</b> No official Garrett
<i>compressor</i> map was read in any round of this work, which is why every Garrett turbo entry in
&sect;17 is marked as modelled only. The official BorgWarner EFR 8374 sheet was also not retrieved.
Several retail prices in &sect;18 could not be confirmed on a live listing and are marked.</div>

<p class="note"><b>Computation.</b> Every number in this report is produced by scripts in this
folder and can be re-run: <code>unified_model_r4.py</code> (the thermal and airflow model),
<code>make_r5_data.py</code> (pipe diameters, core sweep, aperture table),
<code>make_r5_extra.py</code> (package combinations, turbo inlet, inlet depression),
<code>build_r5.py</code> (this document).</p>
</section>
"""

OPEN = """
<section id="open">
<h2><span class="num">20</span>Open questions</h2>
<p class="lede">Only items that block a decision. Everything else has been decided or dropped.</p>

<h3>Blocking</h3>
<ol class="q">
<li><b>What is the clear width of the Carlos Sainz bumper aperture?</b> One measurement, at the
narrowest point of the opening. It sets the core width and nothing else in this report is waiting
on anything. Take the clear height at the same time so the 305 mm figure can be confirmed.</li>
<li><b>Is 30 psi the real boost target?</b> Every number here is built on it. It is derived from
your injectors, fuel and MAP sensor, not stated anywhere. If the answer is 25 psi, the core
recommendation is unchanged and the power figures drop by about 40 whp.</li>
</ol>

<h3>Needs an answer before the first tune, but not before you buy</h3>
<ol class="q">
<li><b>Which LSD is in the back?</b> Clutch-plate or helical. It moves the driveline factor and
therefore the whole power band by about 10 whp. It does not change any hardware decision.</li>
<li><b>Does a puller fan fit behind the radiator?</b> Check clearance to the crank pulley and
timing cover. If it does, the fan question in &sect;13 is closed and you do not need to shorten the
condenser.</li>
<li><b>Where will the blow-off valve physically fit on the cold pipe?</b> &sect;10 wants it within
300 mm of the throttle. If the route does not allow it, say so and it goes on the hot pipe with a
small penalty.</li>
</ol>

<h3>Turns a model into a fact, and costs one session each</h3>
<ol class="q">
<li><b>Log EFR shaft speed against MAP and airflow.</b> Settles the &plusmn;250 rpm on the surge
crossover in &sect;14 and puts a real operating point on the compressor map.</li>
<li><b>Measure inlet depression before the compressor.</b> &sect;09 says half a psi costs more than
every charge-pipe decision combined. A vacuum gauge answers it in one drive.</li>
<li><b>Fit an exhaust backpressure gauge before the turbine.</b> Turns the assumed EMAP/IMAP of 1.6
into a number, which is worth about 2 whp per 0.1.</li>
<li><b>Weld the blanked hot-pipe bung now.</b> Without a compressor-outlet temperature you can
measure charge temperature but not intercooler effectiveness. It is free while the pipe is on the
bench.</li>
<li><b>Put it on a dynamometer.</b> Every power figure in this report is a model output. This is
the only item that changes that.</li>
</ol>

<h3>Closed in this round</h3>
<ul class="tight">
<li><s>What diameter charge pipe?</s> &mdash; 2.50 in OD, 0.065 in wall, both sides. &sect;07</li>
<li><s>What core?</s> &mdash; made to order, aperture width minus 20 mm &times; 305 &times; 102 mm.
&sect;08</li>
<li><s>Which turbo?</s> &mdash; the EFR 7163 you own. No change. &sect;14</li>
<li><s>Does the joint step matter?</s> &mdash; no.</li>
<li><s>Does the taper at the throttle matter?</s> &mdash; no, and you already own the adapter.</li>
<li><s>Should the cold side step up after the core?</s> &mdash; no. It recovers nothing and adds
lag. Priced at 24 ms in &sect;06.</li>
<li><s>Is the manifold paired wrong?</s> &mdash; no. It is 1+4 / 2+3, which is correct. &sect;16</li>
<li><s>Is off-the-shelf availability a constraint?</s> &mdash; no. The core is made to order.</li>
</ul>
</section>
"""

FOOTER = """
<footer><div>
Model assumptions: dry air, cp = 1005 J/kg&middot;K, R = 287.05, &gamma; = 1.40; cross-flow both
fluids unmixed; area density &beta; = 900 m&sup2;/m&sup3;; U = 55&nbsp;&times;&nbsp;(v/10)^0.5
W/m&sup2;K, air-side limited; core &Delta;P anchored on Treadstone's published 1,142&nbsp;CFM /
1.5&nbsp;psi point and scaled quadratically; charge temperature and mass flow solved
simultaneously. Treat all predicted temperatures as &plusmn;5&nbsp;&deg;C and all &Delta;P as
&plusmn;30%%.
<br><br><b>All power figures in this report are estimates from a volumetric-efficiency model. This
engine has never been run on a dynamometer.</b> Compressor efficiency for the EFR 7163 is read from
the official BorgWarner product sheet; the surge and choke coordinates are digitised from the
printed plot and carry about &plusmn;1.5 lb/min of uncertainty.
<br><br>Prepared for Dan &middot; round five, 31 August 2026 &middot; 5S-GTE ST185 project
</div></footer>
</div>
<script>
%(script)s
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- assemble
SECTIONS = [SUMMARY, INPUTS, SITE, MODEL, CALC, PACKAGE, PIPES, CORE, INLET, BOV,
            IATSENSOR, DUCT, STACK, TURBO, POWER, MANIFOLD, REJECTED, VENDORS,
            SOURCES, OPEN]

NAV = [("summary", "Answers"), ("inputs", "Build Inputs"), ("site", "Site"),
       ("model", "The Model"), ("calc", "Calculators"),
       ("package", "Full Package"), ("pipes", "Charge Pipe"), ("core", "Core Spec"),
       ("inlet", "Turbo Inlet"), ("bov", "Blow-off Valve"), ("iat", "IAT Sensor"),
       ("duct", "Ducting"), ("stack", "Front-End Stack"), ("turbo", "Turbo &amp; Surge"),
       ("power", "Power"), ("manifold", "Manifold"), ("rejected", "Rejected"),
       ("vendors", "Parts &amp; Cost"), ("sources", "Sources"), ("open", "Open Questions")]

HEAD = HEAD.replace(
    "".join('<a href="#%s">%s</a>' % (a, b) for a, b in
            [("summary","Answers"),("inputs","Build Inputs"),("site","Site"),("model","The Model"),
             ("calc","Calculators"),("pipes","Charge Pipe"),("core","Core Spec"),("duct","Ducting"),
             ("stack","Front-End Stack"),("turbo","Turbo &amp; Surge"),("power","Power Estimate"),
             ("manifold","Manifold"),("rejected","Considered &amp; Rejected"),("vendors","Vendors"),
             ("sources","Sources"),("open","Open Questions")]),
    "".join('<a href="#%s">%s</a>' % (a, b) for a, b in NAV))

body = []
for i, sec in enumerate(SECTIONS, start=1):
    sec = re.sub(r'<span class="num">\d+</span>', '<span class="num">%02d</span>' % i, sec, count=1)
    body.append(sec)
body = "\n".join(body)

# renumber every internal cross reference to the final section order
XREF = {"summary": 1, "inputs": 2, "site": 3, "model": 4, "calc": 5, "package": 6,
        "pipes": 7, "core": 8, "inlet": 9, "bov": 10, "iat": 11, "duct": 12,
        "stack": 13, "turbo": 14, "power": 15, "manifold": 16, "rejected": 17,
        "vendors": 18, "sources": 19, "open": 20}

script = open("r5_script.js", encoding="utf-8").read()
data5 = open("r5_data.js", encoding="utf-8").read()
extra5 = open("r5_extra.js", encoding="utf-8").read()
script = data5 + extra5 + script

html = HEAD + body + (FOOTER % dict(script=script))
open("intercooler-report.html", "w", encoding="utf-8").write(html)
print("wrote intercooler-report.html  %d bytes" % len(html))

# integrity: every anchor referenced must exist as a section id
ids = set(re.findall(r'<section id="([^"]+)"', html))
refs = set(re.findall(r'href="#([^"]+)"', html))
missing = refs - ids
print("section ids:", len(ids))
print("orphan anchors:", sorted(missing) if missing else "none")
mounts = set(re.findall(r'mount\("([^"]+)"', script)) | {"tank_top", "tank_ctr", "tank_side"}
divs = set(re.findall(r'id="([^"]+)"', body))
print("missing chart containers:", sorted(mounts - divs) if (mounts - divs) else "none")
for pat in ["&sect;1", "&sect;2"]:
    pass
print("stray section refs:", sorted(set(re.findall(r'&sect;(\d+)', body))))
