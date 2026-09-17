import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\projects\5sgte-intercooler-research\intercooler-report.html"
h = io.open(P, encoding="utf-8").read()
n0 = len(h)

# ---- replace the whole open-questions section body -------------------------
start = h.find('<section id="open">')
end   = h.find('</section>', start) + len('</section>')
assert start > 0 and end > start

NEW_OPEN = '''<section id="open">
<h2><span class="num">21</span>Open questions and pending decisions</h2>
<p class="lede">Updated for round two. Seven of the original twelve are now closed by the build inputs
you confirmed. What is left is listed in the order it blocks work.</p>

<h3>Blocking &mdash; nothing else can be finalised until these are answered</h3>
<ol class="q">
<li><b>Measure M1&ndash;M4 in &sect;13.</b> Still the single largest unknown in this report. Every core in
&sect;19 is contingent on a clear aperture. Specifically needed: clear width behind the bumper skin, clear
height, available depth ahead of the A/C condenser, and the position of the 1&times;1 in crash bar relative to
the core face. The SpeedFactory SS-850 needs about 640 mm of clear width for the core plus room either side
for the tubes; the Treadstone TR1245 needs 762 mm overall and is the one most likely to fail.</li>
<li><b>Are you replacing the turbo, or keeping the EFR 7163?</b> This is the decision the whole of &sect;17
exists to support, and it forks the build. Keeping it caps you at about 456 whp with no headroom. Fitting
the G25-770 costs $1,850, gives up 307 rpm of spool and unlocks about 540 whp. Both are coherent. The
intercooler recommendation is the same either way.</li>
<li><b>What is the actual power target, now that 600 whp is off the table?</b> &sect;17.6 says the honest
street and track number is 420&ndash;480 whp and the race ceiling is about 540. Which of those you are
building for changes the bottom-end spec, the boost target and the fuel system margin.</li>
<li><b>What redline are you willing to run?</b> 7,200 rpm is the recommendation. 7,500 is the outer limit
and needs valve springs. Confirm which, because it sets the cam choice and the ECU limiter.</li>
</ol>

<h3>Needs a decision, but not blocking</h3>
<ol class="q" start="5">
<li><b>Port size &mdash; go to 3.0 in piping, or step down at the tanks?</b> Every assembled intercooler in
&sect;19 has 3.0 in ports. &sect;10 specifies 2.5 in piping. A short reducer at each tank is acceptable and
costs little pressure. Moving the whole charge system to 3.0 in is cleaner but slows charge velocity at
part throttle. Recommendation: <b>step down at the tanks</b>, but it is your call.</li>
<li><b>Is the bottom end built, and to what spec?</b> Nothing in the file set states the rod, piston or
bearing spec. 30 psi on a 1.52 rod ratio 2.19 L is not a stock-internals proposition. Rods, pistons and
head studs need to be confirmed before any of the boost numbers here are safe to run.</li>
<li><b>External or internal wastegate?</b> &sect;17.8 flags that the G25-770's 54 mm turbine will run high
exhaust manifold pressure at 60+ lb/min. An external gate helps materially. It is also a manifold and
packaging decision that has not been made.</li>
<li><b>Radiator &mdash; staying stock?</b> The whole SS-850-over-TR1245 argument in &sect;19.3 rests on the
cooling system having no margin to give away. If a thicker radiator is going in, the TR1245 becomes the
better intercooler and that section should be re-read.</li>
<li><b>Who builds the duct?</b> This is now the highest-value fabrication job on the car, worth about
27 &deg;C. &sect;18.3 recommends spending the shop machine time here instead of on billet end tanks. It still
needs someone to actually do it.</li>
</ol>

<h3>Model uncertainty &mdash; things I could not resolve from data</h3>
<ol class="q" start="10">
<li><b>The VE curve is the weakest link in &sect;17.</b> Everything about the rpm answer flows from it. It is
derived from the Taylor Mach index rather than assumed, which is an improvement, but it has not been
validated against a dyno sheet for this specific combination. <b>The single best thing you can do to check
this report is a logged 3rd-gear pull</b> with MAP, rpm and a mass-flow estimate. That would pin VE directly.</li>
<li><b>The exhaust backpressure term is a guess.</b> Headline numbers use an exhaust-to-intake pressure ratio
of 1.6. The true figure depends on the turbine housing, manifold and wastegate, none of which are settled.
The band from 1.0 to 2.0 moves peak power by about &plusmn;25 whp. A pressure sensor in the exhaust manifold
would close this.</li>
<li><b>Turbine wheel diameters for the Precision and Xona units are unverified.</b> &sect;17.7 explains why:
those model numbers describe the compressor, not the turbine, and the round-one data set may have used them
as turbine sizes. Their inertia figures should not be trusted. It does not change the recommendation, because
neither is the pick.</li>
<li><b>Compressor pressure-ratio ceilings are read off published maps, not measured.</b> The "usable PR" for
each turbo is the top of its efficiency island as published. Real-world usable ceiling depends on inlet
temperature and how much efficiency you are willing to give up. Treat these as &plusmn;0.2 PR.</li>
<li><b>10 hp per lb/min is a rule of thumb.</b> On E85 with good combustion it is defensible; the real range
is 9.5&ndash;10.5, which is &plusmn;5% on every power figure in this report.</li>
<li><b>Validation plan &mdash; agreed?</b> Log ambient, MAP, charge-pipe IAT (An Volt 6), manifold IAT and
ethanol content through a 3rd-gear pull. That single log checks the VE model, the intercooler effectiveness
and the pressure drop budget at once. I can write the analysis script when you have data.</li>
</ol>

<h3>Closed since round one</h3>
<p class="note">Displacement (2.19 L confirmed) &middot; injector size (1400 cc confirmed) &middot; throttle body
(electronic, confirmed) &middot; A/C (staying, not in the way) &middot; oil cooler location (fender well or front
corner, outside the intercooler footprint) &middot; crash bar (1&times;1 in aluminium, room around it) &middot;
end tank manufacture (buy assembled &mdash; &sect;18) &middot; tube-and-fin (commercially moot, &sect;06).</p>
</section>'''

h = h[:start] + NEW_OPEN + h[end:]

# ---- append round-two sources ---------------------------------------------
ss = h.find('<section id="sources">')
se = h.find('</section>', ss)
assert ss > 0
EXTRA = '''
<h3>Round two &mdash; turbo, redline and end tank sources</h3>
<div class="scroll"><table>
<thead><tr><th>Claim</th><th>Source</th><th>Confidence</th></tr></thead>
<tbody>
<tr><td>3S-GTE intake valve diameter 33.5 mm standard</td>
<td>Ferrea Competition Plus intake valve listing, 33.5 mm STD, Toyota MR2 3S-GTE (Real Street Performance)</td>
<td><span class="pill p-ok">High</span> vendor part spec</td></tr>
<tr><td>Connecting rod 138 mm; 5S crank stroke 91 mm; rod ratio 1.51&ndash;1.52</td>
<td>HP Academy engine-building forum thread "Worth sacrificing rod ratio for extra stroke? Toyota 3S vs 5SGTE";
corroborated by JE Pistons 252064 and CP SC7451 listings for 5S-FE block / 3S-GTE head, 87.5 mm bore, 91 mm stroke, 138 mm rod</td>
<td><span class="pill p-ok">High</span> three independent listings agree</td></tr>
<tr><td>Stock 3S-GTE valve springs float around 7,500&ndash;7,600 rpm; builders report 7,500 rpm at 25 psi</td>
<td>MR2 Owners Club and mr2.com forum threads on raising the 3S-GTE rev limit</td>
<td><span class="pill p-warn">Medium</span> enthusiast reports, no bench data</td></tr>
<tr><td>5S-FE block claimed capable of 8,000&ndash;8,500 rpm; 98+ block has thicker walls</td>
<td>alltrac.net and toyotanation build threads</td>
<td><span class="pill p-bad">Low</span> anecdote. Treated as a claim, not a basis. The report caps at 7,200&ndash;7,500 on mean piston speed instead.</td></tr>
<tr><td>Taylor inlet Mach index: VE flat below Z &asymp; 0.5, falling above</td>
<td>Standard internal-combustion-engine text result (Taylor, <i>The Internal-Combustion Engine in Theory and Practice</i>)</td>
<td><span class="pill p-ok">High</span> textbook</td></tr>
<tr><td>End tank type ratings: plastic 2.5/5, stamped 3/5, cut-and-weld 4.5/5, cast 5/5; cast tanks allow CFD-designed internal diverters</td>
<td>Mishimoto engineering blog, "We Rate The 4 Types of Intercooler End Tanks"</td>
<td><span class="pill p-warn">Medium</span> vendor, and they sell cast tanks. Directionally consistent with the Garrett manifold-shape guidance in &sect;08.</td></tr>
<tr><td>SpeedFactory SS-850, SKU SF-06-089, 24&times;12&times;3 in bar &amp; plate, side in / side out, hand-formed 5052-H3 TIG-welded tanks, 600&ndash;850 hp, $524.68</td>
<td>Real Street Performance product listing, retrieved August 2026</td>
<td><span class="pill p-ok">High</span> live listing with in-stock price</td></tr>
<tr><td>Treadstone TR1245, 22&times;12.5&times;4.5 in bar &amp; plate, cast tanks with divided inlet, 3 in ports, 1,469 CFM, 1.5 psi drop, $549.00</td>
<td>Real Street Performance product listing and Treadstone product page, retrieved August 2026</td>
<td><span class="pill p-ok">High</span> live listing with in-stock price</td></tr>
<tr><td>Treadstone TR8, 22&times;7.8&times;3.5 in core, 28 in overall, 2.5 in ports, 750 CFM, 500 hp, &lt;2 psi drop</td>
<td>Treadstone product listings via multiple resellers</td>
<td><span class="pill p-warn">Medium</span> spec consistent across resellers, price varies</td></tr>
<tr><td>6061-T651 plate at about $7.50/lb in small quantity; 160 cm&sup3;/min roughing MRR; 5 cm&sup2;/min finishing rate</td>
<td>Author's estimate for a rigid VMC in aluminium. Not a quote.</td>
<td><span class="pill p-warn">Medium</span> the go/no-go conclusion holds across a 2&times; error either way</td></tr>
<tr><td>Turbo choke flow, pressure-ratio ceilings, spool thresholds, prices for all twelve candidates</td>
<td>Carried forward unchanged from the round-one turbo research
(<code>data/turbo_ranked.json</code>, <code>data/turbo_data.json</code>, <code>data/turbo3.py</code>)</td>
<td><span class="pill p-warn">Medium</span> not re-verified in round two; see open question 12</td></tr>
</tbody></table></div>
<p class="note"><b>Round-two computation.</b> Every number in &sect;16&ndash;&sect;19 is produced by scripts in this
folder and can be re-run: <code>rpm_sensitivity.py</code> (redline sweep, crossover, inertia),
<code>rpm_sens2.py</code> (VE sensitivity band, fixed-boost comparison, head-to-head),
<code>thermal3.py</code> and <code>thermal4.py</code> (design-point re-run, core size study with face
velocity coupled to depth), <code>endtank.py</code> (billet cost and machining time),
<code>make_chartdata.py</code> (the data block the charts read).</p>
'''
h = h[:se] + EXTRA + h[se:]

io.open(P, "w", encoding="utf-8", newline="").write(h)
print("report: %d -> %d bytes" % (n0, len(h)))
print("open-questions rewritten:", "Round two, August 2026" in h or "Updated for round two" in h)
print("round-two sources added:", "Ferrea Competition Plus" in h)
