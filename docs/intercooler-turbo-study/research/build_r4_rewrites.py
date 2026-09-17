# -*- coding: utf-8 -*-
"""Round-four rewrites of existing sections. Imported by build_r4.py."""

# ---------------------------------------------------------------- 10 PIPES
PIPES_NEW = r"""<section id="pipes">
<h2><span class="num">10</span>Charge pipe diameter &mdash; settled by the hardware</h2>

<div class="callout c-bad"><b>Rewritten in round four. This is no longer a decision.</b>
Round three recommended 2.5&nbsp;in both sides with a taper to 2.9&nbsp;in at the throttle.
That was written without knowing what had been bought. Outsider Garage order <b>#7870</b>,
5 January 2026, contains a <b>Bosch 74&nbsp;mm Throttle Body Hose and HD Clamp Adapter</b>
in the "<b>3 inch HD Clamp</b>" variant. The cold pipe therefore terminates at a
<b>3.0&nbsp;in (76.2&nbsp;mm) hose joint on a part that is already on the shelf.</b> The
question is not what diameter to run. It is where, if anywhere, to step down from it.</div>

<h3>10.1 &nbsp;The hardware chain, front to back</h3>
<div class="eq">cold charge pipe
  &rarr; <b>3.00 in (76.2 mm) hose and HD clamp adapter</b>   <span class="cm">Outsider Garage #7870 line 2, $100</span>
  &rarr; <b>Bosch 0 280 750 474 e-throttle, bore 74.5 mm</b>  <span class="cm">line 3, $225. Sold as "74 mm". Plate stamped 745.</span>
  &rarr; <b>Custom DBW manifold adapter plate</b>             <span class="cm">line 1, $150. 109 mm across the centre, 105 mm at the bolt centres.</span>
  &rarr; <b>Soara dual plenum, 3.00 in (76.2 mm) flange</b>
  &rarr; four runners with hyperbolic bellmouths

<span class="cm">two area changes exist in that chain, both 1.7 mm on diameter:</span>
  76.2 &rarr; 74.5 mm  at the throttle inlet   <span class="cm">sudden contraction</span>
  74.5 &rarr; 76.2 mm  at the plenum flange    <span class="cm">sudden expansion</span></div>

<p class="note">Both Bosch part numbers cross-reference the same casting: Porsche
997&nbsp;605&nbsp;115&nbsp;03 and VAG 022&nbsp;133&nbsp;062&nbsp;AJ. It is the drive-by-wire
throttle used on the Porsche 997 and Cayenne and on the VAG 3.6 FSI V6. Vendors list it as
74&nbsp;mm; the plate stamp of <b>745</b> is the real bore and is what this section uses.</p>

<h3>10.2 &nbsp;Is 74.5 mm enough?</h3>
<p class="note">A throttle body stops being transparent to flow when the velocity in its
bore approaches roughly <b>Mach 0.3</b>. Below that the loss is a small multiple of the
velocity head and does not scale badly. The check is arithmetic.</p>
<div class="scroll"><table id="t-r4tb">
<thead><tr><th class="num">rpm</th><th class="num">Boost</th><th class="num">Airflow</th>
<th class="num">Bore velocity</th><th class="num">Mach</th><th class="num">Pressure drop</th>
<th class="num">% of its Mach-0.3<br>capacity used</th></tr></thead>
<tbody></tbody></table></div>

<div class="callout c-good"><b>The throttle is not close to being a restriction.</b> At the
worst case in that table &mdash; 8,000 rpm at 34 psi &mdash; it runs <b>Mach 0.078</b> and
drops <b>0.05&nbsp;psi</b>. Its Mach-0.3 capacity is about <b>198&nbsp;lb/min</b>, which at
10 crank hp per lb/min is roughly <b>2,000 crank horsepower</b> of air. You are using about
a quarter of it. <b>Nothing about the rev-limit decision in &sect;24 is affected by the
throttle body.</b></div>

<h3>10.3 &nbsp;The 1.7 mm step &mdash; is it worth blending?</h3>
<div class="scroll"><table>
<thead><tr><th>Transition</th><th class="num">Type</th><th class="num">Loss coefficient K</th>
<th class="num">Pressure drop at peak flow</th><th class="num">% of the 1.5 psi budget</th></tr></thead>
<tbody>
<tr><td>76.2 &rarr; 74.5 mm, adapter into throttle</td><td class="num">sudden contraction</td>
<td class="num">0.0185</td><td class="num">22 Pa = <b>0.0032 psi</b></td><td class="num">0.21%</td></tr>
<tr><td>74.5 &rarr; 76.2 mm, throttle into plenum</td><td class="num">sudden expansion</td>
<td class="num">0.0020</td><td class="num">2.5 Pa = <b>0.0004 psi</b></td><td class="num">0.02%</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Both together</b></td><td class="num">&mdash;</td>
<td class="num">&mdash;</td><td class="num"><b>24 Pa = 0.0035 psi</b></td><td class="num"><b>0.24%</b></td></tr>
</tbody></table></div>

<div class="rec"><h3>Do not machine the step out</h3>
<div class="specline"><span class="k">Verdict</span><span class="v"><b>Leave it. It is 0.85 mm on the radius.</b></span></div>
<div class="specline"><span class="k">What it costs</span><span class="v">24 Pa at peak flow. That is 0.24% of the pressure-drop budget and about <b>0.008 whp</b>.</span></div>
<div class="specline"><span class="k">Why the expansion is even smaller</span><span class="v">A sudden expansion loss scales as (1 &minus; A<sub>1</sub>/A<sub>2</sub>)&sup2;. With an area ratio of 0.956 that squared term is 0.002 &mdash; effectively zero.</span></div>
<div class="specline"><span class="k">The one thing worth checking</span><span class="v">That the step is <b>concentric</b>. A 0.85 mm annular lip is nothing. A 1.7 mm lip on one side, from a mis-aligned adapter plate, is a real flow separation point and a place for the throttle plate to foul. Check alignment on assembly; do not reach for a die grinder.</span></div>
<div class="specline"><span class="k">Machining risk</span><span class="v">Blending the throttle bore means cutting an anodised aluminium casting that carries the plate bearings. The downside if it goes wrong is far larger than 24 Pa.</span></div>
</div>

<h3>10.4 &nbsp;Cold side &mdash; run 3.0 in, or step down and back up?</h3>
<p class="note">Design point 51.4&nbsp;lb/min (0.389&nbsp;kg/s) at 7,500 rpm and 30 psi.
Cold side at 303.5&nbsp;kPa and 70&nbsp;&deg;C, so &rho; = 3.05&nbsp;kg/m&sup3;. Lengths
1.5&nbsp;m with four 90&deg; bends. <b>All five layouts end at the same 3.0&nbsp;in
adapter</b>, so the comparison is only about what happens upstream of it.</p>
<div class="scroll"><table id="t-r4cold">
<thead><tr><th>Cold-side layout</th><th class="num">Peak velocity</th>
<th class="num">Pressure drop</th><th class="num">Pipe volume</th>
<th class="num">Total charge<br>system volume</th><th class="num">&times; displacement</th>
<th class="num">Boost fill time</th></tr></thead>
<tbody></tbody></table></div>

<div class="callout c-warn"><b>The stepping-down options are worse than they look, because
the table above leaves out the transitions.</b> The intercooler outlet tank will carry a
<b>3.0&nbsp;in port</b> &mdash; every assembled core surveyed in &sect;19.1 does &mdash; and
the throttle adapter is 3.0&nbsp;in. So a 2.5&nbsp;in cold run needs a
<b>3.0&nbsp;&rarr;&nbsp;2.5&nbsp;in contraction at the tank</b> and a
<b>2.5&nbsp;&rarr;&nbsp;3.0&nbsp;in expansion at the adapter</b>. Those two cost a further
<b>0.10&nbsp;psi</b>, which takes the 2.5&nbsp;in layout from 0.59 to <b>0.69&nbsp;psi</b>
against 0.25 for the straight 3.0&nbsp;in run. <b>You would be paying 0.44 psi and two extra
joints to save 22 milliseconds of boost fill time.</b></div>

<div class="rec"><h3>Cold side: 3.0 in for the whole run</h3>
<div class="specline"><span class="k">Diameter</span><span class="v"><b>3.0 in OD mandrel alloy</b>, 72.9 mm bore, the whole 1.5 m</span></div>
<div class="specline"><span class="k">Velocity there</span><span class="v">99 ft/s (30 m/s), Mach 0.081</span></div>
<div class="specline"><span class="k">Pressure drop</span><span class="v">0.25 psi &mdash; the lowest of any layout</span></div>
<div class="specline"><span class="k">Joints deleted</span><span class="v">Two. Both ends of the run are already 3.0 in hardware you own.</span></div>
<div class="specline"><span class="k">What it costs</span><span class="v">22 ms of extra boost fill time against a 2.5 in run, and 1.6 L of extra system volume</span></div>
<div class="specline"><span class="k">Transition into the throttle</span><span class="v"><b>None needed.</b> 72.9 mm pipe into a 76.2 mm hose adapter is a coupler joint, not a taper.</span></div>
</div>

<h3>10.5 &nbsp;Hot side &mdash; chosen independently</h3>
<p class="note">The hot side is a separate decision. It sees the same mass flow at
311&nbsp;kPa and 214&nbsp;&deg;C, so &rho; = 2.22&nbsp;kg/m&sup3; &mdash; about 27% less
dense than the cold side, which is why the same pipe runs faster and drops more pressure
there. Garrett's published guidance is to keep charge-pipe velocity in the
<b>200&ndash;300&nbsp;ft/s</b> band. Turbo outlet is 2.0&nbsp;in.</p>
<div class="scroll"><table id="t-r4hot">
<thead><tr><th class="num">Hot pipe OD</th><th class="num">Velocity</th>
<th class="num">Against Garrett's band</th><th class="num">Pressure drop<br>1.1 m, 3 bends</th>
<th class="num">Volume</th><th>Assessment</th></tr></thead>
<tbody></tbody></table></div>

<div class="rec"><h3>Hot side: 2.5 in</h3>
<div class="specline"><span class="k">Diameter</span><span class="v"><b>2.5 in OD mandrel alloy</b>, 60.2 mm bore, with a 2.0 &rarr; 2.5 in diffuser at the turbo outlet</span></div>
<div class="specline"><span class="k">Velocity there</span><span class="v">201 ft/s &mdash; the only option that lands inside Garrett's 200&ndash;300 ft/s band</span></div>
<div class="specline"><span class="k">Pressure drop</span><span class="v">0.59 psi. Going to 3.0 in would save 0.33 psi and add 1.5 L of volume.</span></div>
<div class="specline"><span class="k">Why not bigger</span><span class="v">0.33 psi of hot-side loss is worth about 0.3 &deg;C of charge temperature and under 1 whp. It is not worth 14 ms of fill time and a harder route past the turbine housing.</span></div>
<div class="specline"><span class="k">Parts commonality</span><span class="v">2.5 in is also the EFR's compressor <i>inlet</i> size, so couplers, clamps and spares are shared with the intake side</span></div>
<div class="specline"><span class="k">Heat</span><span class="v">This pipe runs past the turbine housing on a transverse 3S-GTE. Shield it or coat it. A smaller pipe is easier to route away from the hot side, which is a second reason not to go to 3.0 in here.</span></div>
</div>

<h3>10.6 &nbsp;So you are mixing diameters. Round three said not to.</h3>
<div class="callout c-warn"><b>Round three said "2.5 inch both sides. Do not mix." That
advice is now withdrawn, and it is worth being precise about why, because the reason is not
the one the forums give.</b>
<div class="scroll" style="margin-top:8px"><table>
<thead><tr><th>Claim</th><th>Status</th><th>Why</th></tr></thead>
<tbody>
<tr><td>"Run a bigger cold side because cold air is denser and flows better"</td>
<td><span class="pill p-bad">Still wrong</span></td>
<td>The mass flow is identical on both sides. Denser air moves <i>slower</i> for the same
pipe, so if anything the cold side needs <i>less</i> area, not more. The physics in round
three was correct.</td></tr>
<tr><td>"Run a smaller hot side to keep velocity up for spool"</td>
<td><span class="pill p-bad">Still wrong</span></td>
<td>Velocity in the charge pipe does nothing for spool. Pressure drop upstream of the
intercooler <i>hurts</i> spool, because the compressor has to make it up.</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>"Match the pipe to the hardware at each
end of the run"</b></td><td><span class="pill p-ok">This is the real reason</span></td>
<td>The cold run has 3.0&nbsp;in hardware at both ends &mdash; the intercooler outlet port
and the bought throttle adapter. The hot run starts at a 2.0&nbsp;in compressor outlet and
wants to stay in Garrett's velocity band. <b>Two different constraints, two different
answers.</b> Matching them deletes four transitions from the system.</td></tr>
</tbody></table></div>
<b>The layout that comes out of this is the same layout the folklore recommends. That is a
coincidence, and it is worth knowing that it is a coincidence</b> &mdash; because if you had
bought a 2.5&nbsp;in throttle adapter instead, the correct answer would have flipped to
2.5&nbsp;in cold and the folklore would still have said the same thing.</div>

<h3>10.7 &nbsp;System volume and throttle response</h3>
<div class="callout c-bad"><b>Correction to round three.</b> The volume-per-metre column in
round three was computed as <code>&pi;/4 &times; OD&sup2; &divide; 2</code>. The divide-by-two
has no justification, and the outside diameter is not the bore. <b>Every volume figure in
round three was roughly half the true value</b>, which made the system look far more
responsive than it is. Corrected below.</div>

<div class="eq">System volume, the recommended 2.5 in hot / 3.0 in cold build:
  hot pipe   1.1 m &times; 2.85 L/m  =   3.13 L    <span class="cm">2.5 in OD, 60.2 mm bore</span>
  cold pipe  1.5 m &times; 4.17 L/m  =   6.26 L    <span class="cm">3.0 in OD, 72.9 mm bore</span>
  core internal, 19.0 L envelope at ~28% void  =   5.32 L
  end tanks  2 &times; 0.55 L        =   1.10 L
  <span class="cm">-----------------------------------------------</span>
  TOTAL                          =  <b>15.81 L</b>   <span class="cm">= 7.22 x engine displacement</span>
                                                <span class="cm">round three reported 9.05 L, which was wrong</span>

Fill time to 30 psi, at a 0.15 kg/s spool-up flow, section by section
at that section's own density:      <b>216 ms</b>
  same build with a 2.5 in cold side:  194 ms      <span class="cm">22 ms quicker, 0.44 psi worse</span></div>

<p class="note">7.2&times; displacement is above the 3&ndash;5&times; figure usually quoted
as comfortable for a front-mount, and above the 6&times; figure usually quoted as the point
where lag becomes noticeable. <b>Those are rules of thumb, not measurements, and the physical
number is the 216 ms.</b> Two honest caveats: the 0.15&nbsp;kg/s ramp flow is an estimate,
and the core internal void fraction of 28% is a typical bar-and-plate figure rather than a
measured one for a specific core. Treat the 216&nbsp;ms as <b>&plusmn;30%</b>. What is not
in doubt is the <i>difference</i> between layouts, because that is just a volume ratio.</p>

<h3>10.8 &nbsp;Bends and routing</h3>
<ul class="tight">
<li><b>Mandrel bends only.</b> Crush bends neck the tube and create a permanent restriction.</li>
<li><b>Bend radius R/D &ge; 1.5.</b> For 3.0 in cold pipe that is a 114 mm centreline radius
minimum; for 2.5 in hot pipe, 95 mm.</li>
<li><b>Budget about 1% pressure loss per 90&deg; bend.</b> The model above uses a loss
coefficient of 0.20 per bend on the local velocity head, which is the same thing expressed
properly. Every bend you delete is free.</li>
<li><b>Keep the hot pipe away from the manifold and downpipe</b>, or wrap and coat it.</li>
<li><b>Blow-off valve on the cold side</b>, as close to the throttle as practical, so it
vents the whole 15.8&nbsp;L on lift. With a system this large that placement matters more
than it would on a smaller one.</li>
<li><b>Boost-control solenoid feed</b> goes in this pipe &mdash; a 1/8&nbsp;NPT bung in the
cold side, pre-throttle. See &sect;21.11. <b>Decide where before the pipe is fabricated.</b></li>
</ul>
</section>"""

# ---------------------------------------------------------------- 13 FITMENT
FIT_NEW = r"""<section id="fitment">
<h2><span class="num">13</span>Fitment &mdash; CS bumper packaging</h2>

<div class="callout c-good"><b>Rewritten in round four. Most of this is no longer guesswork.</b>
Round three dimensioned this section from a stock radiator spec and a forum anecdote, and
flagged four measurements as unknown. Dan has since defined the front end: a Mishimoto
MMRAD-CEL-89 radiator on the engine side of the fender support, the A/C condenser even with
the fender support, and <b>203&ndash;254&nbsp;mm (8&ndash;10 in) of clear space between the
back of a 76&nbsp;mm intercooler and the radiator</b>. Three of the four measurements are
answered. <b>The full geometry, the stack analysis and the revised core choice are in
&sect;28.</b> What remains below is the one thing still unmeasured.</div>

<div class="scroll"><table>
<thead><tr><th>#</th><th>Measurement</th><th>Round three status</th><th>Round four status</th></tr></thead>
<tbody>
<tr style="background:rgba(255,107,107,.09)"><td>M1</td>
<td><b>Clear width of the CS bumper lower aperture</b>, inside edge to inside edge, at the
height the core will sit</td>
<td>Unknown. Need &ge; 640 mm for a 610 mm core plus tank welds.</td>
<td><span class="pill p-bad">STILL UNKNOWN &mdash; and now the only thing blocking the core
order.</span> &ge; 640 mm buys the 610 mm core; &ge; 720 mm buys the 685 mm core, which
&sect;28.4 shows is worth 2.5 &deg;C for almost nothing.</td></tr>

<tr style="background:rgba(56,211,159,.09)"><td>M2</td>
<td>Front-to-back gap, bumper skin to A/C condenser</td>
<td>Unknown. Need &ge; 137 mm for a 102 mm core.</td>
<td><span class="pill p-ok">CLOSED.</span> There is 203&ndash;254 mm behind a 76 mm core, so
177&ndash;228 mm behind a 102 mm one. Depth is not a constraint and will not become one.</td></tr>

<tr><td>M3</td><td>Vertical clear height of the aperture</td>
<td>Unknown. Need &ge; 320 mm for a 305 mm core.</td>
<td><span class="pill p-warn">Still worth checking</span>, but the radiator core behind it is
only 318 mm tall, so a core taller than about 330 mm is shadowing rather than cooling.
A 305 mm core is the sensible height regardless.</td></tr>

<tr><td>M4</td><td>Where the oil cooler lives</td>
<td>Must not shadow the intercooler or condenser</td>
<td><span class="pill p-warn">Still open.</span> The Chase Bays 10-row competes for the same
opening. Give it its own feed in a lower corner or a wheel arch.</td></tr>

<tr style="background:rgba(56,211,159,.09)"><td>M5</td>
<td>Is the aperture wide enough to tempt you toward a 711 mm core?</td>
<td>Reject 711 mm &mdash; wider than the 712 mm radiator</td>
<td><span class="pill p-warn">The reason was wrong; the answer is unchanged.</span> The
Mishimoto is 714 mm overall with a 699 mm core, so 711 mm is not "wider than the radiator".
It is still not recommended, because 711 mm of core plus tank welds needs about 740 mm of
clear aperture and nothing suggests the CS bumper has it. See &sect;28.4.</td></tr>
</tbody></table></div>

<div class="chartbox"><h4>Front-end package, plan view (looking down)</h4>
<div id="fit_plan"></div></div>

<div class="chartbox"><h4>Front elevation &mdash; core vs radiator shadow</h4>
<div id="fit_front"></div></div>

<div class="callout c-warn"><b>The two drawings above are round-three geometry and are kept
for the front elevation only.</b> The side view in <b>&sect;28.1</b> is the round-four
drawing and it is the one dimensioned from Dan's actual measurements. Where they disagree,
&sect;28 is right.</div>

<h3>Stack order, front to back</h3>
<div class="eq">bumper skin
  &rarr; DUCT (sealed all four edges)        <span class="cm">still the highest-value item in this report</span>
  &rarr; INTERCOOLER  610 &times; 305 &times; 102
  &rarr; 177 - 228 mm of clear air           <span class="cm">measured. Far more than the 15-25 mm needed for the exit jet to spread.</span>
  &rarr; A/C CONDENSER                       <span class="cm">even with the fender support</span>
  &rarr; RADIATOR   Mishimoto, 699 x 318 core, 51.8 mm thick
  &rarr; FAN &rarr; engine bay (must vent!)</div>

<ul class="tight">
<li><b>Soft-mount everything.</b> Garrett explicitly recommends rubber isolation grommets
for air-to-air coolers, for vibration fatigue and to allow thermal expansion. A rigidly
bolted core cracks at the tank welds.</li>
<li><b>The crash bar is the usual casualty.</b> Alltrac forum reports on the ST205 water-to-air
conversion confirm the crash bar routinely gets sectioned or removed to fit a front heat
exchanger with the A/C condenser retained. Plan on fabricating a replacement tube brace.</li>
<li><b>Put the gap to work.</b> 177&ndash;228 mm is a lot of unused space. It is enough for a
proper diffuser behind the core, which lets the core's exit flow slow down and spread before
it reaches the condenser. That is worth more than a fan. See &sect;28.5.</li>
</ul>
</section>"""

# ---------------------------------------------------------------- 22 MANIFOLD
MAN_NEW = r"""<section id="manifold">
<h2><span class="num">22</span>The twin-scroll manifold is paired correctly</h2>

<div class="callout c-good"><b>Corrected in round four. This section previously said the
manifold was paired wrong. It is not.</b> The prior research described the manifold as
1+2&nbsp;/&nbsp;3+4, and round three built a fault report on that. Dan has since confirmed
that the pairing shown in the attached diagrams <b>was corrected after those diagrams were
made</b>, and the manifold as built is <b>1+4&nbsp;/&nbsp;2+3</b>. The attachment did not
reflect the change. <b>The recommendation to re-make the manifold is withdrawn. There is
nothing to fix and nothing to buy.</b></div>

<p class="lede">The pulse-timing arithmetic is kept below, because it is worth having for a
different reason: it is the check that <b>confirms 1+4 / 2+3 is the correct pairing for this
engine</b>, and it is the check to run against the physical part if the pairing is ever in
doubt again.</p>

<h3>22.1 &nbsp;The arithmetic, as validation</h3>
<p class="note">Nothing here needs a simulation. Firing order and exhaust duration are
enough.</p>
<div class="eq">firing order 1-3-4-2, so power strokes begin at:   cyl 1 = 0&deg;   cyl 3 = 180&deg;   cyl 4 = 360&deg;   cyl 2 = 540&deg;
HKS 264 exhaust cam: 264&deg; duration, exhaust valve opens about 135&deg; after firing TDC

  cyl 1 exhaust open   135&deg; &rarr; 399&deg;
  cyl 3 exhaust open   315&deg; &rarr; 579&deg;
  cyl 4 exhaust open   495&deg; &rarr; 759&deg;  (= 495&deg; &rarr; 720&deg; and 0&deg; &rarr; 39&deg;)
  cyl 2 exhaust open   675&deg; &rarr; 939&deg;  (= 675&deg; &rarr; 720&deg; and 0&deg; &rarr; 219&deg;)

<span class="cm">Two cylinders 360&deg; apart in the cycle:  360 &minus; 264 = 96&deg; of CLEAR GAP
Two cylinders 180&deg; apart in the cycle:  264 &minus; 180 = 84&deg; of OVERLAP</span>

AS BUILT       1+4  are 360&deg; apart &rarr; <b>96&deg; clear gap</b>    2+3  are 360&deg; apart &rarr; <b>96&deg; clear gap</b>
the other way  1+2  are 180&deg; apart &rarr; 84&deg; overlap        3+4  are 180&deg; apart &rarr; 84&deg; overlap</div>

<p class="note">The general rule, which matches published twin-scroll guidance: pair the
cylinder that fires <b>first</b> with the one that fires <b>third</b>, and the <b>second</b>
with the <b>fourth</b>. On 1-3-4-2 that is 1 with 4, and 3 with 2. <b>That is what is on the
car.</b></p>

<div class="chartbox"><h4>Exhaust valve events &mdash; the manifold as built, and the alternative</h4>
<div id="ch_pulse"></div>
<div class="legend">
<span><i style="background:#4ea3ff"></i>Cyl 1</span><span><i style="background:#38d39f"></i>Cyl 2</span>
<span><i style="background:#ff6b6b"></i>Cyl 3</span><span><i style="background:#ffb347"></i>Cyl 4</span>
</div>
<p class="note" style="margin-top:9px">Each bar is one cylinder's exhaust valve open period
across a full 720&deg; cycle. The <b>upper</b> panel is 1+2&nbsp;/&nbsp;3+4, where the two
bars sharing a scroll overlap by 84&deg;. The <b>lower</b> panel is
1+4&nbsp;/&nbsp;2+3 &mdash; <b>what is on the car</b> &mdash; where they do not overlap at
all and there is 96&deg; of clear crank angle between them.</p></div>

<h3>22.2 &nbsp;What the correct pairing is worth, since you already have it</h3>
<p class="note">Stated as a credit rather than a penalty, because that is what it is.</p>
<div class="scroll"><table>
<thead><tr><th>Effect</th><th class="num">Value of having it right</th><th>Why</th><th>Confidence</th></tr></thead>
<tbody>
<tr><td><b>Exhaust backpressure</b><br><span class="note">EMAP/IMAP ratio</span></td>
<td class="num">1.6 rather than about 2.0</td>
<td>A correctly divided housing keeps the blowdown pulse from one cylinder out of a
neighbour that is still emptying. A mis-paired one behaves close to a single-scroll housing
of the same total area while keeping the divider's wetted area and restriction &mdash; the
losses of a divided housing without the benefit. <b>Every power figure in this report already
assumes 1.6, so nothing needs adjusting.</b></td>
<td><span class="pill p-warn">Medium</span> &mdash; direction certain, magnitude modelled</td></tr>
<tr><td><b>Peak power</b></td><td class="num">about 7 whp you already have</td>
<td>Lower exhaust manifold pressure means less residual exhaust gas left in the cylinder to
displace fresh charge. Modelled at 5% VE loss per unit of EMAP/IMAP above 1.0.</td>
<td><span class="pill p-warn">Medium</span></td></tr>
<tr><td><b>Spool threshold</b></td><td class="num">300&ndash;500 rpm earlier than a
mis-paired manifold would give</td>
<td>Pulse energy is what spins the turbine below the boost threshold, and pulse separation
is what preserves it. This is the effect twin-scroll exists for, and you are receiving it.
Published back-to-back twin versus single scroll testing puts the difference at 300&ndash;500
rpm of onset and 8&ndash;15% of torque under the knee.</td>
<td><span class="pill p-ok">High</span> &mdash; the biggest and best-supported effect</td></tr>
<tr><td><b>Knock margin and exhaust valve temperature</b></td><td class="num">Not quantified</td>
<td>Lower residual fraction means a cooler, less knock-prone charge. On E85 with a flex
sensor this matters less than it would on pump fuel, but it is not nothing.</td>
<td><span class="pill p-neu">Directional only</span></td></tr>
</tbody></table></div>

<div class="chartbox"><h4>Exhaust backpressure against power &mdash; where your manifold sits</h4>
<div id="ch_bp"></div>
<div class="legend">
<span><i style="background:#38d39f"></i>whp at 7,500 rpm, 30 psi</span>
<span><i style="background:#4ea3ff"></i>Your manifold &mdash; correctly paired twin scroll, EMAP/IMAP ~1.6</span>
<span><i style="background:#ff6b6b"></i>What a mis-paired manifold would have cost, ~2.0</span>
</div>
<p class="note" style="margin-top:9px">The blue marker is where you are. The red marker is
where round three wrongly placed you. <b>The 7 whp between them is credit, not debt</b>, and
it is already inside every power figure in this report. The remaining spread on this chart
is turbine sizing and housing A/R, which is a separate question from pairing.</p></div>

<h3>22.3 &nbsp;What replaces the recommendation</h3>
<div class="rec"><h3>Nothing to do &mdash; but verify once, and then log it</h3>
<div class="specline"><span class="k">Verdict</span><span class="v"><b>The manifold is correct. Do not re-make it. Do not fit an undivided housing.</b></span></div>
<div class="specline"><span class="k">Money not spent</span><span class="v">A manifold re-make is typically $600&ndash;$1,500 in fabrication, plus the dyno session you would otherwise have wasted tuning around it</span></div>
<div class="specline"><span class="k">Verify once, visually</span><span class="v">Trace which two runners enter each scroll at the turbine flange. Cylinders <b>1 and 4</b> should share one scroll, <b>2 and 3</b> the other. Five minutes with a torch. Do it before the manifold is lagged or wrapped, because afterwards it is a much worse job.</span></div>
<div class="specline"><span class="k">Then measure it</span><span class="v">An exhaust backpressure gauge before the turbine turns the 1.6 assumption into a number. You already have the 5-bar MAP sensor for the other half of the ratio.</span></div>
<div class="specline"><span class="k">What changes if EMAP/IMAP is worse than 1.6</span><span class="v">Roughly &minus;2 whp per 0.1 above 1.6. If it logs at 2.0 with a correctly paired manifold, the cause is <b>turbine housing A/R or wastegate sizing</b>, not pairing &mdash; and that is a different fix.</span></div>
</div>

<div class="callout c-info"><b>The knock-on effect on the turbo decision, restated.</b>
Round three warned that judging the turbo on a mis-paired manifold would push you toward
buying a bigger one you do not need. That warning is now moot in one direction and sharper in
the other: <b>with correct pairing you are already getting the 7163's best spool behaviour.</b>
If it still feels lazy on the road, the cause is somewhere else &mdash; turbine housing A/R,
wastegate creep, or the boost target table &mdash; and buying a larger compressor would make
all three worse. The case for keeping the 7163 in &sect;21.7 is stronger than it was, not
weaker.</div>

<div class="callout c-warn"><b>What is still uncertain here.</b> The 84&deg;/96&deg; geometry
is exact arithmetic and is not in doubt. The <b>consequences</b> are modelled: the 1.6
backpressure figure is an informed estimate, not a measurement, and the 300&ndash;500 rpm
spool figure comes from published twin-versus-single-scroll comparisons on other engines, not
on this one. The direction is certain. The magnitudes are worth &plusmn;50%. Both become
facts with one backpressure gauge.</div>
</section>"""
