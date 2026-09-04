# -*- coding: utf-8 -*-
"""Round-four HTML section bodies. Imported by build_r4.py."""

# ============================================================ 23 WHAT CHANGED
S23 = r"""
<!-- ============ 23 ROUND FOUR ============ -->
<section id="r4">
<h2><span class="num">23</span>Round four &mdash; eight corrections, and what each one changed</h2>
<p class="lede">On 31 August 2026 Dan supplied eight corrections to the inputs, plus the
Gmail purchase records for the throttle body and its adapters. Everything downstream was
re-derived rather than patched. This section lists each change and its effect. The new
analysis is in &sect;24 to &sect;29.</p>

<div class="callout c-bad"><b>Read this first: there is no dyno figure anywhere in this
report.</b> The engine is not finished and has never been run on a dynamometer. Every
horsepower number here is an <b>estimate</b> from a volumetric-efficiency model, checked
against published dyno results for other cars with comparable turbochargers. Wherever this
report says "whp" it means "modelled whp". &sect;26 shows the comparison against real
published results and states how far apart they are.</div>

<div class="scroll"><table>
<thead><tr><th>#</th><th>Correction</th><th>What it changed</th><th class="num">Size of the change</th></tr></thead>
<tbody>
<tr><td class="num">1</td><td><b>Manifold is already paired 1+4 / 2+3</b><br>
<span class="note">The 1+2 / 3+4 diagram was superseded before it was attached.</span></td>
<td>&sect;22 rewritten from a fault report into a validation. The "re-make the manifold"
recommendation is <b>withdrawn</b>. The 7 whp and 300&ndash;500 rpm spool penalties are
deleted from every number, chart and conclusion. The mis-paired spool chart is deleted.</td>
<td class="num"><b>0 whp</b><br><span class="note">the headline already used the correctly
paired backpressure figure of 1.6, so no power number moves. What goes away is a job, a
cost and a spool penalty.</span></td></tr>

<tr><td class="num">2</td><td><b>Intake plenum resolved</b> &mdash; Soara Performance
custom dual plenum, 3 in flange. Throttle body identified from the part numbers and the
purchase record.</td>
<td>Closes the open question about the stock Gen 2 plenum. Charge-pipe recommendation
re-run against the real hardware. &sect;10 rewritten. The pipe diameter at the throttle is
no longer a choice.</td>
<td class="num"><b>0 whp</b><br><span class="note">it removes a risk, it does not add
power. Cold pipe changes from 2.5 in to 3.0 in.</span></td></tr>

<tr><td class="num">3</td><td><b>Redline is a range</b>, stock through 8,000 rpm</td>
<td>&sect;24 is new. Power, airflow, boost, charge temperature and mechanical risk are all
presented as functions of rpm. No single redline is recommended.</td>
<td class="num"><b>+15 whp</b><br><span class="note">across the whole 7,000&ndash;8,000
band, and 11 of those 15 arrive by 7,200</span></td></tr>

<tr><td class="num">4</td><td><b>No dyno exists</b></td>
<td>Every power figure relabelled as an estimate. &sect;26 is new: eight published
community dyno results for comparable builds, against this model.</td>
<td class="num">&mdash;<br><span class="note">model sits 4&ndash;8% below the nearest
comparable published result</span></td></tr>

<tr><td class="num">5</td><td><b>Drivetrain upgraded</b> &mdash; rebuilt gearbox, one-piece
carbon driveshaft, LSD, lightweight wheels</td>
<td>&sect;27 is new. The driveline factor becomes a band, 0.78&ndash;0.83, instead of the
single 0.80. Each component assessed separately, including the one that makes the loss
<i>worse</i>.</td>
<td class="num"><b>&plusmn;13 whp</b><br><span class="note">and about 2.4% quicker
acceleration, which is the real gain</span></td></tr>

<tr><td class="num">6</td><td><b>Compressor map provenance unknown</b></td>
<td>&sect;25 is new. The official BorgWarner sheets for the 7163, 7670 and 7064 were
retrieved and read. The 7163 map was digitised and re-fitted.</td>
<td class="num"><b>&minus;1 whp</b><br><span class="note">official efficiency at the design
point is 0.693 against the 0.706 the model used. The prior number is confirmed.</span></td></tr>

<tr><td class="num">7</td><td><b>Packaging defined</b> &mdash; Mishimoto radiator, condenser
position, 8&ndash;10 in of clear space behind the core</td>
<td>&sect;28 is new; &sect;13 rewritten with real geometry. Depth is no longer the
constraint. The radiator shadowing penalty is quantified properly and turns out to have
been <b>overweighted in round three</b>.</td>
<td class="num"><b>core stays 102 mm</b><br><span class="note">but for a different and
better reason than round three gave</span></td></tr>

<tr><td class="num">8</td><td><b>Prior research treated as suspect</b></td>
<td>&sect;29 is new: every file in <code>data/prior-turbo-research/</code> classified as
current, superseded or unverified, with the reason.</td>
<td class="num"><b>3 current<br>13 superseded<br>4 unverified</b></td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>Two errors of my own, found while re-deriving.</b>
<ul class="tight">
<li><b>The charge-pipe volume column in &sect;10 was wrong by a factor of two.</b> Round
three computed litres per metre as <code>&pi;/4 &times; OD&sup2; &divide; 2</code>. The
divide-by-two has no justification and the bore should have been the inside diameter, not
the outside. Every system-volume figure that followed was too small. Corrected in &sect;10:
the real system volume is <b>15.8 L</b>, not the 9.1 L round three reported.</li>
<li><b>The 711 mm core was rejected for a reason that no longer holds.</b> Round three said
a 711 mm core is wider than the 712 mm radiator behind it. The radiator is now known to be
the Mishimoto, which is 714 mm overall with a 699 mm core. The width objection is weaker
than stated. The core is still not recommended, but now on aperture grounds alone, and the
aperture is still unmeasured.</li>
</ul></div>
</section>
"""

# ============================================================ 24 RPM RANGE
S24 = r"""
<!-- ============ 24 RPM RANGE ============ -->
<section id="rpmrange">
<h2><span class="num">24</span>The rev range, presented as a range</h2>
<p class="lede">Round three recommended a single redline. Dan asked for the whole band
instead, stock through 8,000 rpm, so he can choose. Below is every quantity as a function
of rpm, with the mechanical risk stated at each step. <b>There is no recommendation in this
section, only numbers.</b></p>

<div class="callout c-info"><b>What "stock redline" means here.</b> The Gen 2 3S-GTE
tachometer redline is <b>7,000 rpm</b> with fuel cut a little above it. Round one of this
report used 6,650 rpm, which was an assumption and was never sourced.
<b>Confirm the number off your own tachometer and rev-limiter setting before using this
table</b> &mdash; it moves the left-hand end of everything below.</div>

<div class="chartbox"><h4>Wheel horsepower across the rev range, with the driveline band</h4>
<div id="ch_r4_rpm"></div>
<div class="legend">
<span><i style="background:rgba(56,211,159,.30)"></i>Driveline band, 0.78 to 0.83</span>
<span><i style="background:#38d39f"></i>30 psi, driveline 0.80</span>
<span><i style="background:#4ea3ff"></i>25 psi</span>
<span><i style="background:#6f8098"></i>20 psi</span>
<span><i style="background:#ffb347"></i>34 psi</span>
<span><i style="background:#c58cff;height:1px"></i>Charge temperature at the valve, right axis</span>
</div>
<p class="note" style="margin-top:9px">The green band is the same airflow converted with a
0.78 and a 0.83 driveline factor. <b>The band is wider than the entire gain from
7,000 to 8,000 rpm.</b> That is the honest shape of this problem: the rev-limit decision is
smaller than the uncertainty in how much the drivetrain eats.</p></div>

<h3>24.1 &nbsp;Every quantity, at every step</h3>
<div class="scroll"><table id="t-r4rpm">
<thead><tr><th class="num">Redline</th><th class="num">Mean piston<br>speed</th>
<th class="num">Mach<br>index Z</th><th class="num">VE</th>
<th class="num">Airflow</th><th class="num">% of the<br>60 lb/min line</th>
<th class="num">Charge<br>temp</th><th class="num">whp band<br>0.78 &ndash; 0.83</th>
<th class="num">Step</th><th>Mechanical risk at this step</th></tr></thead>
<tbody></tbody></table></div>
<p class="note">30 psi, E85, 32&nbsp;&deg;C ambient, 93.87&nbsp;kPa site pressure, on the
610&nbsp;&times;&nbsp;305&nbsp;&times;&nbsp;102&nbsp;mm core with sealed ducting at
100&nbsp;km/h. <b>Estimates. Not measurements.</b></p>

<h3>24.2 &nbsp;What binds, and where</h3>
<div class="scroll"><table>
<thead><tr><th>Constraint</th><th class="num">Binds at</th><th>Evidence</th><th>Confidence</th></tr></thead>
<tbody>
<tr><td><b>Cylinder head airflow</b></td><td class="num">above 8,000</td>
<td>Taylor inlet Mach index stays under 0.56 to 8,000 rpm. Per-cylinder port demand peaks
at 69&nbsp;CFM against a measured stock Gen&nbsp;2 port capacity of about 245&nbsp;CFM at
28&nbsp;inches of water. The head has a very large margin.</td>
<td><span class="pill p-ok">High</span></td></tr>
<tr><td><b>Intake plenum and throttle</b></td><td class="num">not binding</td>
<td>Resolved in round four. The Soara dual plenum replaces the stock Gen 2 casting, and
the 74.5&nbsp;mm throttle uses 26% of its own Mach-0.3 capacity at 8,000 rpm and 34 psi.
See &sect;10.</td><td><span class="pill p-ok">High</span></td></tr>
<tr><td><b>Volumetric efficiency</b></td><td class="num">tapers from 7,200</td>
<td>0.963 at 7,000, 0.958 at 7,200, 0.929 at 7,500, 0.880 at 8,000. A taper, not a
collapse. It is enough to flatten the power curve: 7,200&nbsp;&rarr;&nbsp;8,000 rpm is
worth <b>7 whp</b>.</td><td><span class="pill p-warn">Medium</span> &mdash; modelled from
the Mach index, not measured</td></tr>
<tr><td><b>Compressor choke</b></td><td class="num">not binding at 30 psi</td>
<td>86% of the 60&nbsp;lb/min line at 8,000 rpm. See &sect;25 for what the official map
actually shows.</td><td><span class="pill p-ok">High</span> &mdash; now from the official
sheet</td></tr>
<tr><td><b>Valve spring float</b></td><td class="num">7,500 &ndash; 7,600</td>
<td>Reported stock 3S-GTE figure. Builders report reaching 7,500 rpm on stock springs.
Above that you are buying springs.</td>
<td><span class="pill p-warn">Medium</span> &mdash; community reported, not tested here</td></tr>
<tr style="background:rgba(255,107,107,.07)"><td><b>Bottom end</b><br>
<span class="note">rod ratio and piston speed</span></td><td class="num"><b>this is the one
that binds</b></td>
<td>Rod ratio 1.516 (138&nbsp;mm rod on a 91&nbsp;mm stroke) is short. Mean piston speed is
21.2&nbsp;m/s at 7,000, 22.8 at 7,500 and 24.3 at 8,000. Above roughly 23&nbsp;m/s a
production-based block is in race-service territory, and this one is also carrying 30 psi
of manifold pressure.</td>
<td><span class="pill p-ok">High</span> on direction, <span class="pill p-warn">Medium</span>
on where exactly the line sits</td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>The honest summary of this section, without making the choice
for you.</b> Going from the stock 7,000 rpm limit to 7,200 buys about <b>8 whp</b> and costs
nothing. 7,200 to 7,500 buys <b>3 whp</b> and costs a set of valve springs. 7,500 to 8,000
buys <b>4 whp</b> and costs bearing and rod service life at 24.3&nbsp;m/s of piston speed.
<b>The whole 1,000 rpm is worth 15 whp, which is less than the driveline uncertainty in
&sect;27.</b> Whatever you pick, pick it for driveability and gearing reasons, not for the
power.</div>
</section>
"""

# ============================================================ 25 OFFICIAL MAP
S25 = r"""
<!-- ============ 25 OFFICIAL MAP ============ -->
<section id="officialmap">
<h2><span class="num">25</span>The official BorgWarner compressor map</h2>
<p class="lede">Dan did not know whether the compressor maps in the prior research came
from BorgWarner. They did not, in the sense that mattered: the maps inside
<code>06_turbo_model.py</code> are its author's own words &mdash; "MODELED
approximations... NOT traced from the official BorgWarner map contours". Round four went
and got the official sheets.</p>

<h3>25.1 &nbsp;What was retrieved</h3>
<div class="scroll"><table>
<thead><tr><th>Turbo</th><th>Official sheet</th><th>Status</th><th>What it gave</th></tr></thead>
<tbody>
<tr style="background:rgba(56,211,159,.09)"><td><b>EFR 7163</b> <span class="pill p-ok">the one you own</span></td>
<td><code>efr-7163-f.pdf</code></td><td><span class="pill p-ok">Retrieved and read</span></td>
<td>The sheet states the map applies to <b>all 7163 units</b>, which includes the
<b>7163-G</b> &mdash; 0.80 A/R, T4, twin scroll, part 11639880002, supercore 11637105000,
housing 11631008002. That is your part exactly.</td></tr>
<tr><td>EFR 7670</td><td><code>efr-7670-b.pdf</code></td>
<td><span class="pill p-ok">Retrieved and read</span></td>
<td>Peak efficiency island <b>0.75</b>, speed lines 42/79/103/123/140 krpm, flow axis to
70 lb/min, PR axis to 5.0. Compressor 57&nbsp;mm inducer / 76&nbsp;mm OD.</td></tr>
<tr><td>EFR 7064</td><td><code>efr-7064-b.pdf</code></td>
<td><span class="pill p-ok">Retrieved and read</span></td>
<td>Peak efficiency island <b>0.76</b>, speed lines 46/86/113/134/153 krpm, flow axis to
60 lb/min. Compressor 52&nbsp;mm inducer / 70&nbsp;mm OD.</td></tr>
<tr style="background:rgba(255,179,71,.09)"><td>EFR 8374</td><td>&mdash;</td>
<td><span class="pill p-warn">Not retrieved</span></td>
<td>The request timed out repeatedly. Its figures in this report still rest on the prior
digitisation and should be treated as <b>unverified</b>.</td></tr>
<tr style="background:rgba(255,107,107,.09)"><td>Garrett G25-660, G30-770, G35-900</td>
<td>&mdash;</td><td><span class="pill p-bad">None exists in this work</span></td>
<td>No official Garrett map has been read in any round. Their efficiency figures are
modelled. Do not use them to rank one Garrett against another.</td></tr>
</tbody></table></div>

<h3>25.2 &nbsp;What the official 7163 sheet actually prints</h3>
<div class="grid g4">
<div class="kpi"><div class="lab">Peak efficiency island</div><div class="val g">0.74</div>
<div class="note">printed contour, centred near 44 lb/min at PR 3.0</div></div>
<div class="kpi"><div class="lab">Maximum speed line</div><div class="val">150</div>
<div class="note">krpm. Lines at 44, 84, 111, 132, 150</div></div>
<div class="kpi"><div class="lab">Plotted flow axis</div><div class="val">65</div>
<div class="note">lb/min. Envelope reaches about 62 at PR 2.2</div></div>
<div class="kpi"><div class="lab">Plotted PR axis</div><div class="val">4.2</div>
<div class="note">envelope peaks near PR 4.1 at 45&ndash;50 lb/min</div></div>
</div>

<div class="chartbox"><h4>The official EFR 7163 map, with your operating line on it</h4>
<div id="ch_r4_map"></div>
<div class="legend">
<span><i style="background:#38d39f"></i>Operating line, 30 psi, 2,500 to 8,000 rpm</span>
<span><i style="background:#ff6b6b"></i>Surge line, digitised</span>
<span><i style="background:#4ea3ff"></i>Choke boundary, digitised</span>
<span><i style="background:#ffb347"></i>Design point, 7,500 rpm / 30 psi</span>
</div>
<p class="note" style="margin-top:9px">Efficiency shading is the round-four surface,
least-squares fitted to the thirteen printed contour labels. The contour <i>values</i>, the
speed-line <i>values</i> and the axis extents are exact &mdash; they are the sheet's own
printed text. The surge and choke <i>coordinates</i> are digitised off the printed plot and
are good to roughly &plusmn;1.5&nbsp;lb/min and &plusmn;0.08&nbsp;PR.</p></div>

<h3>25.3 &nbsp;Official versus modelled &mdash; the differences</h3>
<div class="scroll"><table>
<thead><tr><th>Quantity</th><th class="num">Prior research</th><th class="num">Official sheet</th>
<th>Verdict</th></tr></thead>
<tbody>
<tr style="background:rgba(56,211,159,.09)"><td>Compressor efficiency at the design point<br>
<span class="note">51.4 lb/min, PR 3.42</span></td>
<td class="num">0.706</td><td class="num"><b>0.693</b></td>
<td><span class="pill p-ok">Confirmed.</span> The prior figure is within 0.013 of the
official map. Re-solving the whole model with the official value changes the compressor
outlet by 3&nbsp;&deg;C, the charge temperature at the valve by <b>0.6&nbsp;&deg;C</b>, and
the power by <b>under 1 whp</b>. This was the largest single unverified input in the report
and it turns out to have been right.</td></tr>
<tr><td>Surface fit quality</td><td class="num">RMS 0.048<br><span class="note">claimed,
worst of the four</span></td><td class="num"><b>RMS 0.021</b></td>
<td>The round-four fit is a quadratic through thirteen printed labels. Worst single
residual is 0.039, at the peak of the 0.74 island &mdash; a quadratic cannot reproduce a
sharp peak. At the design point the fit sits in a well-sampled region.</td></tr>
<tr><td>Choke line</td><td class="num">flat 60 lb/min</td>
<td class="num">62 at PR 2.2<br>60 at PR 3.4<br>53 at PR 4.0</td>
<td><span class="pill p-warn">Slightly wrong in both directions.</span> A flat 60 is
pessimistic below PR 3, optimistic above PR 3.8. At your design point the two agree to
within 0.5 lb/min, so nothing moves.</td></tr>
<tr style="background:rgba(255,179,71,.09)"><td>Usable pressure-ratio ceiling</td>
<td class="num">3.6</td><td class="num"><b>about 4.1</b></td>
<td><span class="pill p-warn">The 3.6 figure is not on the sheet.</span> The official map
plots efficiency contours and the 150 krpm speed line up to about PR 4.1 at 45&ndash;50
lb/min. Where 3.6 came from is not documented anywhere in either body of work. What
actually limits you above 30 psi is shaft speed and the bottom end, not the map.</td></tr>
<tr><td>Compressor wheel</td><td class="num">71 mm OD</td>
<td class="num">57 mm inducer / 71 mm OD</td>
<td><span class="pill p-ok">Correct.</span> Turbine 56&nbsp;mm exducer / 63&nbsp;mm OD,
also correct.</td></tr>
</tbody></table></div>

<h3>25.4 &nbsp;The finding that is genuinely new: low-rpm surge</h3>
<div class="callout c-bad"><b>Holding full boost below about 3,000 rpm puts this compressor
on or inside its surge line.</b> This was invisible before, because no real surge line
existed in the prior work. At PR 3.42 the official surge line sits at
<b>20.9&nbsp;lb/min</b>. The engine only swallows that much at about 2,750 rpm. Below that,
commanding 30 psi asks the compressor to make pressure it cannot sustain at that flow, and
it will surge.</div>

<div class="scroll"><table id="t-r4surge">
<thead><tr><th class="num">rpm</th><th class="num">Engine airflow<br>at 30 psi</th>
<th class="num">Surge line<br>at PR 3.42</th><th class="num">Margin</th><th>Verdict</th></tr></thead>
<tbody></tbody></table></div>

<div class="callout c-good"><b>What to do about it, and it is free.</b> This is a boost
<i>target table</i> problem, not a hardware problem. In the Link G4X, schedule boost against
rpm so the target ramps in rather than stepping to 30 psi:
<ul class="tight" style="margin-top:6px">
<li>Below 2,750 rpm &mdash; do not command more than about 12&ndash;15 psi.</li>
<li>2,750 to 3,500 rpm &mdash; ramp linearly to the full target.</li>
<li>Above 3,500 rpm &mdash; full target, with at least 6&nbsp;lb/min of surge margin
everywhere.</li>
</ul>
In practice the turbo cannot make 30 psi at 2,500 rpm anyway, so this mostly protects you
against an aggressive wastegate duty table and against lugging the engine in too high a
gear. It costs nothing and it is the kind of thing that is much easier to set before the
first tune than to diagnose afterwards as a rattling noise under load.</div>

<div class="callout c-warn"><b>What is still uncertain.</b> The surge line was read off a
printed plot at screen resolution, not from BorgWarner's underlying data. Treat the
2,750&nbsp;rpm crossover as <b>&plusmn;250&nbsp;rpm</b>. You have the EFR speed sensor
wired to SI-3 and a 5-bar MAP sensor; logging shaft speed against MAP and airflow puts a
real operating point on this map and settles it in one session.</div>
</section>
"""

# ============================================================ 26 DYNO
S26 = r"""
<!-- ============ 26 DYNO COMPARISON ============ -->
<section id="dynocheck">
<h2><span class="num">26</span>Estimates, not measurements &mdash; the community cross-check</h2>
<div class="callout c-bad"><b>Stated plainly, because it matters more than any number in
this report.</b> This engine has never run on a dynamometer. It is not finished. Every
horsepower figure in every section is the output of a model:
airflow from displacement &times; rpm &times; volumetric efficiency &times; charge density,
converted at 10.0 crank hp per lb/min and a driveline factor. Three of those five terms are
estimates. <b>The only thing that turns this report into fact is a dyno sheet and a data
log.</b></div>

<h3>26.1 &nbsp;Published results for comparable builds</h3>
<p class="note">None of these is this car. They are used only to bound the model &mdash; to
show whether it is producing numbers that are plausible for this class of engine and
turbocharger, or numbers that are not. Dyno type matters: inertia dynos such as the Dynojet
read high against steady-state dynos, commonly by 5&ndash;10% on all-wheel drive.</p>
<div class="scroll"><table id="t-r4dyno">
<thead><tr><th>Build</th><th class="num">Displacement</th><th>Fuel</th>
<th class="num">Boost</th><th>Drive</th><th>Dyno</th><th class="num">whp</th>
<th class="num">whp per litre</th></tr></thead>
<tbody></tbody></table></div>

<div class="chartbox"><h4>Where this model sits against published results</h4>
<div id="ch_r4_dyno"></div>
<div class="legend">
<span><i style="background:#4ea3ff"></i>Published community result</span>
<span><i style="background:#38d39f"></i>This model, 30 psi, driveline 0.80</span>
<span><i style="background:rgba(56,211,159,.30)"></i>This model, driveline band 0.78 to 0.83</span>
</div>
<p class="note" style="margin-top:9px">Specific output in wheel horsepower per litre is the
fair comparison, because it removes displacement. It does <b>not</b> remove drivetrain type,
altitude, ambient temperature or dyno type, and those differences are why the bars are not
directly comparable to each other either.</p></div>

<h3>26.2 &nbsp;What the comparison says</h3>
<div class="scroll"><table>
<thead><tr><th>Check</th><th>Result</th><th>Reading</th></tr></thead>
<tbody>
<tr><td>The nearest single comparable &mdash; a 3S-GTE on an EFR 7163 on E85 at 25 psi,
reported at 300&nbsp;kW at the wheels</td>
<td class="num">402 whp measured<br>371 whp modelled at 25 psi</td>
<td>The model is <b>8% below</b> that car. Plausible causes, in order of likely size:
this model is set at 32&nbsp;&deg;C ambient and 93.87&nbsp;kPa site pressure where that car
was almost certainly at sea level and cooler; and this model applies a 20% all-wheel-drive
loss where that car's drivetrain is unknown. <span class="pill p-ok">Model is conservative,
by a defensible amount</span></td></tr>
<tr><td>Specific output</td><td class="num">188 whp per litre modelled<br>200&ndash;258
across the EFR 7163 community results</td>
<td>The model is at or just below the bottom of the observed band. That is the expected
place for a car carrying an all-wheel-drive loss and a hot, thin-air design point.
<span class="pill p-ok">Consistent</span></td></tr>
<tr><td>The same chassis and drivetrain &mdash; an ST185 with a .50 turbo at 14 psi on 91
octane, 337 whp on a Dynojet</td>
<td class="num">337 whp at 14 psi</td>
<td>Useful because the drivetrain is identical to yours. Scaling that car's airflow to
30 psi on E85 lands in the 400&ndash;440 whp region, which brackets this model's
390&ndash;430 band. <span class="pill p-ok">Consistent</span></td></tr>
<tr style="background:rgba(255,179,71,.09)"><td>The high outlier &mdash; a built 2.3 L Evo 9
on the same EFR 7163, E85, 36 psi, 593 whp on a Dynojet</td>
<td class="num">593 whp</td>
<td>That is 258 whp per litre and it implies roughly <b>63&nbsp;lb/min</b> through a turbo
this report treats as a 60&nbsp;lb/min unit. Either the Dynojet is reading high, or the
official choke line is conservative, or both. <b>It is a reason not to treat 60 lb/min as a
wall</b>, and a reason to distrust cross-dyno comparison generally.
<span class="pill p-warn">Informative, not usable</span></td></tr>
<tr><td>Is 600 whp reachable?</td><td class="num">No, not on 2.19 L with this turbo</td>
<td>600 whp at this driveline factor needs about 75&nbsp;lb/min, which is past the official
7163 envelope at any pressure ratio the bottom end would survive. The Evo above reached
593 whp from <b>2.3 L at 36 psi with a built bottom end</b>, which is the shape of what it
would take. <span class="pill p-bad">Unchanged from round three</span></td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>How to read all of this.</b> Community dyno numbers are
self-reported, from different dynos, at different altitudes, with different correction
factors, and with a strong publication bias toward good results. They are worth using to
answer "is this model in the right postcode" and worth nothing for answering "will my car
make 411 whp". The answer to the second question costs one dyno session.</div>
</section>
"""

# ============================================================ 27 DRIVETRAIN
S27 = r"""
<!-- ============ 27 DRIVETRAIN ============ -->
<section id="driveline">
<h2><span class="num">27</span>Drivetrain &mdash; what the upgrades actually recover</h2>
<p class="lede">Round three set the driveline factor at 0.80, a 20% loss, from a measured
Evo 6 engine-dyno against chassis-dyno comparison. Dan has since fitted a freshly rebuilt
gearbox, a one-piece carbon fibre driveshaft, an LSD rear differential and lightweight
racing wheels, and asked what that is worth. <b>The honest answer is: much less to the dyno
number than it is to the car.</b></p>

<div class="callout c-warn"><b>The distinction this whole section rests on.</b>
<span class="def" title="Steady-state loss: the fraction of engine power turned into heat by
friction in the gearbox, transfer case, differentials, bearings and seals. It is present
whether the car is accelerating or holding a constant speed.">Steady-state loss</span> and
<span class="def" title="Rotational inertia: the energy stored in spinning parts. It is
returned when the car decelerates, so it is not a loss at all - it is a tax on acceleration
only.">rotational inertia</span> are different things and only one of them shows up as a
lower dyno reading on a steady-state dynamometer. Reducing rotating mass makes a car
accelerate harder without making one more horsepower. Marketing copy routinely blurs the
two. This section does not.</div>

<h3>27.1 &nbsp;Each change, assessed separately</h3>
<div class="scroll"><table>
<thead><tr><th>Change</th><th class="num">Steady-state loss</th><th class="num">Rotational inertia</th>
<th>Reasoning</th><th>Confidence</th></tr></thead>
<tbody>
<tr><td><b>Freshly rebuilt transmission</b></td>
<td class="num" style="color:#4fe0aa">0 to &minus;1.0 pt</td><td class="num">none</td>
<td>New bearings, new seals and fresh fluid restore the gearbox to its nominal friction. A
worn transaxle with tired bearings and degraded oil genuinely does drag more. But a rebuild
returns you to as-designed &mdash; it does not beat the factory number. Claim the recovery
only if the old box was actually bad.</td>
<td><span class="pill p-warn">Medium</span></td></tr>

<tr><td><b>One-piece carbon fibre driveshaft</b></td>
<td class="num" style="color:#4fe0aa">&minus;0.3 to &minus;0.8 pt</td>
<td class="num" style="color:#4fe0aa">about half the shaft's inertia</td>
<td>The real steady-state gain is not the carbon. It is deleting the <b>centre support
bearing and one universal joint</b> that a two-piece shaft needs. Those are genuine friction
terms. The carbon itself buys inertia, which is an acceleration effect.</td>
<td><span class="pill p-warn">Medium</span> &mdash; published back-to-back dyno data on this
specific change is thin, and the figures that circulate are mostly vendor claims</td></tr>

<tr style="background:rgba(255,107,107,.07)"><td><b>LSD rear differential</b></td>
<td class="num" style="color:#ff8f8f">+0.3 to +1.0 pt<br><span class="note">WORSE</span></td>
<td class="num">none</td>
<td><b>This one goes the wrong way and it is usually left out.</b> A clutch-plate limited
slip differential carries static preload; that preload is friction, and it is present all
the time. A helical or torque-biasing unit is closer to neutral because it only generates
bias under torque. <b>Which type you fitted changes the sign of this row.</b></td>
<td><span class="pill p-warn">Medium</span> &mdash; and it depends on a detail not yet
stated</td></tr>

<tr><td><b>Lightweight racing wheels</b></td>
<td class="num">0.0 pt</td>
<td class="num" style="color:#4fe0aa">about 1.15 kg&middot;m&sup2;</td>
<td>Wheels do not add friction. On a <b>steady-state</b> dyno they change nothing at all.
On an <b>inertia</b> dyno such as a Dynojet they raise the indicated reading, because the
dyno infers power from drum acceleration and less of the engine's output is being spent
spinning the car's own wheels up. That is a measurement artefact, not power.</td>
<td><span class="pill p-ok">High</span></td></tr>
</tbody></table></div>

<h3>27.2 &nbsp;The two numbers that come out of it</h3>
<div class="grid g3">
<div class="kpi"><div class="lab">Change to steady-state dyno reading</div>
<div class="val">0 to +2%</div>
<div class="note">and it could be zero, or slightly negative with a plate LSD</div></div>
<div class="kpi"><div class="lab">Extra indicated whp on an inertia dyno</div>
<div class="val">+2.6</div>
<div class="note">from the wheels alone. Zero on a steady-state dyno.</div></div>
<div class="kpi"><div class="lab">Improvement in acceleration</div>
<div class="val g">about 2.4%</div>
<div class="note">about 32 kg of equivalent mass removed from 1,320 kg</div></div>
</div>

<div class="chartbox"><h4>The driveline band, and what it does to the headline</h4>
<div id="ch_r4_drive"></div>
<p class="note" style="margin-top:9px">Same airflow &mdash; 51.4 lb/min at 7,500 rpm and
30 psi &mdash; in every bar. Only the driveline factor changes. <b>The band is 26 whp
wide.</b> That is larger than the entire gain from raising the rev limit by 1,000 rpm, and
larger than the difference between any two turbochargers on the candidate list.</p></div>

<div class="scroll"><table id="t-r4drive">
<thead><tr><th class="num">Driveline factor</th><th class="num">Implied loss</th>
<th class="num">whp at 7,500 / 30 psi</th><th>Case</th></tr></thead>
<tbody></tbody></table></div>

<div class="rec"><h3>What to use, and what to stop claiming</h3>
<div class="specline"><span class="k">Use for planning</span><span class="v"><b>0.80</b>, unchanged from round three</span></div>
<div class="specline"><span class="k">Quote the band</span><span class="v"><b>0.78 to 0.83</b> &mdash; that is 401 to 427 whp at the design point</span></div>
<div class="specline"><span class="k">Do not claim</span><span class="v">That the driveshaft, LSD and wheels are worth a meaningful number of wheel horsepower. Two of the four changes are inertia-only and one of them makes the steady-state loss <i>worse</i>.</span></div>
<div class="specline"><span class="k">Do claim</span><span class="v">About 2.4% quicker acceleration at the same power, better traction out of corners from the LSD, and less unsprung mass. Those are the reasons to have done it.</span></div>
<div class="specline"><span class="k">One detail needed</span><span class="v">Is the LSD a <b>clutch-plate</b> unit with preload, or a <b>helical / torque-biasing</b> unit? It changes the sign of a whole row above.</span></div>
<div class="specline"><span class="k">How to settle it</span><span class="v">A coast-down on a chassis dyno. It is a ten-minute test and it replaces the single largest unverified constant in this report.</span></div>
</div>
</section>
"""

# ============================================================ 28 PACKAGING
S28 = r"""
<!-- ============ 28 PACKAGING ============ -->
<section id="packaging">
<h2><span class="num">28</span>Packaging, with the real geometry</h2>
<p class="lede">Round three's fitment section was guesswork bounded by a stock radiator
dimension and a forum anecdote. Dan has now defined the front end. This section replaces the
guesswork.</p>

<h3>28.1 &nbsp;The facts, as given</h3>
<div class="scroll"><table>
<thead><tr><th>Item</th><th>Fact</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Radiator</td><td><b>Mishimoto MMRAD-CEL-89</b>, two-row brazed aluminium.
Overall <b>714 &times; 439 &times; 64.5&nbsp;mm</b> (28.1 &times; 17.3 &times; 2.54 in).
Core <b>699 &times; 318&nbsp;mm face, 51.8&nbsp;mm thick</b> (2.04 in). 1.25 in inlet and
outlet. Mounted on the <b>engine side</b> of the fender support.</td>
<td>Vendor listing for the part; Dan's confirmation of the mounting position</td></tr>
<tr><td>A/C condenser</td><td>Sits <b>even with the fender support</b>, i.e. immediately
ahead of the radiator</td><td>Dan</td></tr>
<tr><td>Intercooler envelope</td><td>Owns <b>all</b> space from the front face of the
condenser forward to the bumper support</td><td>Dan</td></tr>
<tr style="background:rgba(56,211,159,.09)"><td><b>Clear gap behind the core</b></td>
<td>With a 76&nbsp;mm core there is <b>203 to 254&nbsp;mm</b> (8 to 10 in) from the back of
the intercooler to the radiator</td><td>Dan, measured</td></tr>
<tr><td>Fans</td><td>Willing to fit a shorter A/C condenser to make room for a pusher fan on
the radiator and a pusher fan on the condenser, without intruding on the intercooler space</td>
<td>Dan</td></tr>
</tbody></table></div>

<div class="callout c-good"><b>The first consequence: depth has stopped being a constraint.</b>
Round three's whole core-depth argument was framed around whether 137&nbsp;mm of front-to-back
space existed. It does, with room to spare. Even a 114&nbsp;mm core leaves
165&ndash;216&nbsp;mm of clear air behind it. <b>Measurement M2 from round three is closed.</b>
The remaining unknown is <b>width</b> &mdash; the CS bumper aperture &mdash; and that is
still unmeasured.</div>

<div class="chartbox"><h4>Front-end stack, side view, to scale</h4>
<div id="ch_r4_stack"></div>
<p class="note" style="margin-top:9px">Drawn from the numbers in the table above. The
intercooler depth is shown at the recommended 102&nbsp;mm. Everything behind the condenser
is fixed by the chassis; everything in front of it is yours.</p></div>

<h3>28.2 &nbsp;Radiator shadowing, now that the spacing is known</h3>
<p class="note">Round three treated radiator shadowing as the main argument against a
deeper core, and quoted the temperature rise of the air passing through the intercooler as
if all of it arrived at the radiator. With the gap known, that can be done properly.</p>

<div class="eq">intercooler face 610 &times; 305 mm  =  0.186 m&sup2;
radiator core   699 &times; 318 mm  =  0.222 m&sup2;      <span class="cm">the core shadows 84% of it if centred</span>

heat into the air stream    Q = m&#775;<sub>charge</sub> &middot; c<sub>p</sub> &middot; (T<sub>compressor out</sub> &minus; T<sub>charge</sub>)  =  55.4 kW at 30 psi
air mass through the core   m&#775;<sub>air</sub> = W &middot; H &middot; v<sub>face</sub> &middot; &rho;  =  1.32 kg/s
raw temperature rise        &Delta;T = Q / (m&#775;<sub>air</sub> &middot; c<sub>p</sub>)  =  41 &deg;C

<span class="cm">over the 203-254 mm gap the heated stream entrains ambient air.
Round-jet entrainment, m&#775;(x)/m&#775;&#8320; = 1 + 0.32 x / D<sub>h</sub>, with D<sub>h</sub> = 0.407 m:</span>
entrainment over 228 mm      1.18&times;      &rarr;  effective rise 35 &deg;C, not 41
A/C condenser adds           about 6 kW      &rarr;  a further 4 &deg;C when the A/C is on
<span class="cm">-------------------------------------------------------------------</span>
AIR ARRIVING AT THE RADIATOR  32 + 35 + 4  =  <b>70.5 &deg;C</b> on the 102 mm core
                              32 + 28 + 4  =  <b>63.3 &deg;C</b> on the 76 mm core</div>

<div class="callout c-warn"><b>So the deeper core does cost the radiator 7.2&nbsp;&deg;C of
inlet air.</b> Against a bare temperature head of 73&nbsp;&deg;C (a 105&nbsp;&deg;C coolant
target minus 32&nbsp;&deg;C ambient) that is <b>10% of the head</b>. Round three said
8&nbsp;&deg;C without a gap model behind it; the corrected figure is 7.2&nbsp;&deg;C. The
number barely moved. <b>What moved is the conclusion, and here is why.</b></div>

<h3>28.3 &nbsp;The duty-cycle check that reverses round three's reasoning</h3>
<div class="scroll"><table id="t-r4duty">
<thead><tr><th>Condition</th><th class="num">Heat the intercooler<br>puts into the air</th>
<th class="num">Air arriving at<br>the radiator</th><th class="num">Radiator capacity,<br>stacked vs bare</th>
<th class="num">Capacity lost</th></tr></thead>
<tbody></tbody></table></div>

<div class="callout c-good"><b>The shadowing objection was overweighted, and this is the
argument against my own round-three reasoning.</b>
<ul class="tight">
<li><b>The penalty only exists while you are on boost.</b> At part throttle the intercooler
rejects 4&nbsp;kW instead of 55, and the radiator sees 38&nbsp;&deg;C instead of
70&nbsp;&deg;C. The stack costs it <b>9%</b> of capacity, not 56%.</li>
<li><b>While you are on boost, the radiator is irrelevant anyway.</b> A 500 crank hp engine
at sustained full load rejects on the order of 200&ndash;250&nbsp;kW to coolant. This
radiator sheds 12&ndash;27&nbsp;kW. The coolant temperature during a pull is held by the
thermal mass of the engine block and the coolant itself, not by the radiator. No ST185
radiator, shadowed or not, changes that.</li>
<li><b>The radiator earns its keep on the recovery lap</b> &mdash; the cool-down between
pulls, the part-throttle section after a climb. That is exactly the condition where the
intercooler is putting almost nothing into the air.</li>
<li><b>Therefore:</b> the correct comparison is not "9.2&nbsp;&deg;C of charge cooling
against 7.2&nbsp;&deg;C of radiator inlet air at full load". It is "9.2&nbsp;&deg;C of charge
cooling, always, against 2&nbsp;&deg;C of radiator inlet air when the radiator is actually
doing its job". <b>The deeper core wins more clearly than round three allowed.</b></li>
</ul></div>

<h3>28.4 &nbsp;Core choice, against the real geometry</h3>
<div class="scroll"><table id="t-r4core">
<thead><tr><th>Core, W &times; H &times; T</th><th class="num">Volume</th>
<th class="num">Face<br>velocity</th><th class="num">&epsilon;</th>
<th class="num">Charge temp<br>at the valve</th><th class="num">whp band</th>
<th class="num">Air at the<br>radiator</th><th class="num">Clear gap<br>behind it</th>
<th>Verdict</th></tr></thead>
<tbody></tbody></table></div>

<div class="rec"><h3>Core recommendation, round four</h3>
<div class="specline"><span class="k">If the aperture takes 610 mm</span><span class="v"><b>610 &times; 305 &times; 102 mm</b> &mdash; unchanged from round three, but now for a better reason</span></div>
<div class="specline"><span class="k">If the aperture takes 685 mm</span><span class="v"><b>685 &times; 305 &times; 102 mm</b> &mdash; 2.5 &deg;C cooler charge for 0.8 &deg;C more onto the radiator. Face area is the cheapest cooling available.</span></div>
<div class="specline"><span class="k">Do not go past 102 mm deep</span><span class="v">114 mm buys 3.0 &deg;C more charge cooling for 3.0 &deg;C more radiator inlet air. That is the point where the trade stops being favourable.</span></div>
<div class="specline"><span class="k">Depth available</span><span class="v">177&ndash;228 mm of clear air behind a 102 mm core. You are not depth-limited and you will not be.</span></div>
<div class="specline"><span class="k">The only remaining unknown</span><span class="v"><b>Aperture width.</b> Measure it. Everything else in this section is now a fact.</span></div>
<div class="specline"><span class="k">On the 711 mm core</span><span class="v">Round three rejected it because it was wider than a 712 mm radiator. The Mishimoto is 714 mm overall with a 699 mm core, so that objection is weaker than stated. It is still not recommended, but now purely because the CS bumper aperture is unmeasured and 711 mm of core plus tank welds needs about 740 mm of clear opening.</span></div>
</div>

<h3>28.5 &nbsp;The pusher fans</h3>
<div class="callout c-bad"><b>A pusher fan mounted anywhere in this stack is moving air the
intercooler has already heated.</b> That is the thing to understand before deciding whether
to shorten the condenser to fit one.
<div class="scroll" style="margin-top:8px"><table>
<thead><tr><th>Option</th><th>At a standstill</th><th>At road speed</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td><b>Puller fan behind the radiator</b><br><span class="note">engine side, the normal place</span></td>
<td>Best. Draws through the whole stack.</td>
<td>No blockage &mdash; a stopped puller sits out of the free stream's path through the core
and its shroud can be designed to open.</td>
<td><span class="pill p-ok">Do this if it fits.</span> The radiator is on the engine side of
the fender support, so check clearance to the crank pulley and the timing cover first.</td></tr>
<tr><td><b>Pusher fan between condenser and radiator</b></td>
<td>Helps. Moves stack air onto the radiator.</td>
<td>Costs roughly 10&ndash;20% of face velocity as static blockage from the motor, hub and
shroud struts.</td>
<td><span class="pill p-warn">Acceptable fallback</span> if no puller fits. Worth shortening
the condenser for. Use a shrouded fan with opening flaps if you can get one.</td></tr>
<tr style="background:rgba(255,107,107,.07)"><td><b>Pusher fan on the condenser</b><br>
<span class="note">i.e. behind the intercooler</span></td>
<td>Marginal. It is pushing intercooler exhaust air into the condenser.</td>
<td>Costs face velocity for the condenser <i>and</i> the radiator behind it, and adds a
blockage into the intercooler's own exit path, which raises the intercooler's air-side
pressure drop and lowers its face velocity.</td>
<td><span class="pill p-bad">Do not.</span> This is the one to skip. It takes space, costs
airflow at every speed you actually drive at, and its only benefit is at a standstill, which
is the one condition where you should not be making boost anyway.</td></tr>
</tbody></table></div></div>

<div class="callout c-info"><b>What to do with the freed depth instead.</b> If you shorten
the condenser and end up with 40&ndash;60&nbsp;mm of spare longitudinal room, the highest
value use of it is not a fan. It is:
<ul class="tight" style="margin-top:6px">
<li><b>A sealed duct from the bumper opening to the intercooler face.</b> Still the single
highest-value item in this entire report &mdash; worth about 27&nbsp;&deg;C of charge
temperature against an unducted core, which is three times what the core depth decision is
worth.</li>
<li><b>A clear exit path out of the engine bay.</b> Air that cannot leave does not enter. A
stack this deep needs somewhere for the heated air to go, and on this chassis that usually
means venting the inner wing or the bonnet.</li>
<li><b>A 15&ndash;25 mm gap between the intercooler and the condenser</b>, so the core's exit
jet spreads before it hits the next heat exchanger. You already have far more than that.</li>
</ul></div>
</section>
"""

# ============================================================ 29 FILE AUDIT
S29 = r"""
<!-- ============ 29 FILE AUDIT ============ -->
<section id="audit">
<h2><span class="num">29</span>Audit of the prior research files</h2>
<p class="lede">Dan's instruction was to treat everything in
<code>data/prior-turbo-research/</code> as suspect. Each file is classified below.
<b>Superseded</b> means the method may be sound but the numbers rest on inputs now known to
be wrong. <b>Unverified</b> means the numbers may be right but nothing in the supplied work
establishes where they came from. <b>Current</b> means it survives round four intact.</p>

<div class="scroll"><table>
<thead><tr><th>File</th><th>Status</th><th>Reason, in one line</th></tr></thead>
<tbody>
<tr><td><code>01_airflow_demand_vs_ceilings.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Built on <code>06_turbo_model.py</code>, which assumes 15&nbsp;&deg;C charge air and sea
level; both are wrong for this car.</td></tr>

<tr><td><code>02_boost_vs_rpm_response.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Same model, same two wrong inputs; and the boost-versus-rpm shape now has to respect the
surge line in &sect;25.4, which it does not.</td></tr>

<tr><td><code>02_compressor_map.png</code></td>
<td><span class="pill p-warn">Unverified</span></td>
<td>A modelled Gaussian map, not the official BorgWarner contours. Replaced by &sect;25.</td></tr>

<tr><td><code>03_whp_vs_rpm_by_boost.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Same airflow model, plus the 11.0 &times; 0.85 conversion that &sect;21.3 rejected.</td></tr>

<tr><td><code>04_compressor_maps_operating_points.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Correct operating points would need the official envelope; these are plotted on the
modelled maps. Replaced by the overlay in &sect;25.2.</td></tr>

<tr><td><code>05_operating_point_detail.csv</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Uses an undeclared VE curve 8&ndash;15% below the shared model's, which is the entire
cause of the 45 whp disagreement itemised in &sect;21.2.</td></tr>

<tr><td><code>05_turbo_comparison_data.csv</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>542 whp at 7,500 rpm, from 15&nbsp;&deg;C charge air at sea level and 9.35 whp per
lb/min.</td></tr>

<tr><td><code>06_pressure_reference_map.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Carries the <b>28 &times; 12 &times; 4 inch</b> intercooler label. Dan has confirmed the
711&nbsp;mm width was an estimate, not a purchased part. Nothing downstream of that label
should be used.</td></tr>

<tr style="background:rgba(255,107,107,.09)"><td><code>06_turbo_model.py</code>
<span class="note">the shared model everything else imports</span></td>
<td><span class="pill p-bad">Superseded &mdash; and it is the root cause</span></td>
<td>Displacement 2,164&nbsp;cc instead of 2,188.8; no charge-temperature term at all; sea
level; and a <code>COMP_MAPS</code> efficiency block that returns 27% at the 7163's own
operating point, which is dead code the rest of the file silently works around.</td></tr>

<tr><td><code>07_hp_boost_chargetemp_per_turbo.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Mixes airflow from the 15&nbsp;&deg;C model with efficiency from a 25&nbsp;&deg;C
digitisation. Those two cannot describe the same operating point.</td></tr>

<tr><td><code>07_shakedown_ladder.png</code></td>
<td><span class="pill p-warn">Method current, numbers superseded</span></td>
<td>Ramping boost in steps and logging between them is the right procedure and should be
followed. The psi values on the ladder come from the superseded model.</td></tr>

<tr><td><code>08_efficiency_chargetemp_margin_auc.png</code></td>
<td><span class="pill p-warn">Unverified</span></td>
<td>The area-under-curve metric is not defined anywhere in the supplied work, so the ranking
it produces cannot be checked or reproduced.</td></tr>

<tr><td><code>09_estimated_dyno_comparison.png</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>Its own title says "estimated". It is model output drawn to look like dyno traces, which
is the specific thing Dan asked to have removed. Replaced by &sect;26, which uses published
third-party results and labels them as such.</td></tr>

<tr style="background:rgba(56,211,159,.09)"><td><code>10_official_maps_digitized.png</code></td>
<td><span class="pill p-ok">Current for the EFR 7163</span><br>
<span class="pill p-warn">Unverified for the rest</span></td>
<td>Round four retrieved the official BorgWarner sheet and re-read it. The digitised
efficiency for the 7163 at this car's operating point, <b>0.706</b>, is within
<b>0.013</b> of what the official map gives. That file was right. The Garrett entries in the
same family of charts remain unsupported.</td></tr>

<tr><td><code>11_charge_temp_summary.csv</code></td>
<td><span class="pill p-bad">Superseded</span></td>
<td>25&nbsp;&deg;C ambient at sea level. Reproduces its own 134&nbsp;&deg;F figure exactly
from its own inputs, so it is internally consistent &mdash; it is simply not this car's
design point. Two of its rows, the Garretts, have no map behind them at all.</td></tr>

<tr><td><code>12_efr7163_tuning_plan.png</code></td>
<td><span class="pill p-warn">Method current, numbers superseded</span></td>
<td>The staged approach is sound. The targets need rebuilding against &sect;24 and against
the surge limit in &sect;25.4.</td></tr>

<tr><td><code>13_g4x_boost_target_table.csv</code></td>
<td><span class="pill p-bad">Superseded &mdash; do not load this</span></td>
<td>Beyond the model errors, it commands boost at low rpm without a surge check.
&sect;25.4 shows the compressor is on its surge line below about 2,750 rpm at full boost.
Rebuild this table before it goes anywhere near the ECU.</td></tr>

<tr style="background:rgba(56,211,159,.09)"><td><code>14_exhaust_pulse_timing.png</code></td>
<td><span class="pill p-ok">Current</span></td>
<td>The 84&deg; / 96&deg; arithmetic is exact and was reproduced independently in &sect;22.
It is right, and it is the file that lets you <i>verify</i> the manifold rather than assume
it.</td></tr>

<tr><td><code>15_correct_twinscroll_routing.png</code></td>
<td><span class="pill p-warn">Correct as a reference, void as a fault report</span></td>
<td>The 1+4 / 2+3 routing it shows is correct and matches what Dan has built. Its framing
&mdash; that the manifold needs changing &mdash; is what round four withdraws.</td></tr>

<tr style="background:rgba(56,211,159,.09)"><td><code>3SGTE_Cylinder_Head_Flow_Data<br>_and_Test_Methodology__A_Reference.md</code></td>
<td><span class="pill p-ok">Current</span><br><span class="note">one claim now moot</span></td>
<td>The best file in the folder. Its port-flow anchors (~245&nbsp;CFM intake at 28 in on a
stock Gen&nbsp;2 head) and its NA-basis VE reasoning both survive and are used in &sect;24.
Its warning that the stock Gen&nbsp;2 plenum "struggles with flow above 350&nbsp;whp" is now
<b>moot</b> &mdash; the Soara dual plenum and 74.5&nbsp;mm throttle replace exactly the two
parts it flagged.</td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>The pattern, stated once.</b> Thirteen of the twenty files are
superseded, and twelve of those thirteen fail for the <b>same two reasons</b>: no charge
temperature in the airflow model, and sea-level pressure. Neither is a subtle modelling
choice. Both are visible in six lines of <code>06_turbo_model.py</code>. <b>A body of work
built on one shared model inherits that model's errors everywhere, including into files
that look independent.</b> The three files that survive are the three that do not depend on
it &mdash; the pulse-timing arithmetic, the routing diagram and the head-flow reference.</div>

<div class="callout c-info"><b>What this does not mean.</b> None of the above says the prior
work was careless. The pulse-timing finding was correct and independently verifiable. The
compressor efficiency digitisation was correct, and round four has now confirmed it against
the official sheet. The head-flow reference is careful, cites its sources, and flags its own
uncertainties &mdash; it is better than most of what this report is built on. <b>The failure
is architectural, not analytical:</b> a shared model with two unstated assumptions
propagated into every file that imported it, and no file declared which VE curve or which
ambient condition it was using.</div>
</section>
"""
