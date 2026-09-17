# -*- coding: utf-8 -*-
"""Round four, part two: sources and open questions."""
import os, io

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "intercooler-report.html")
h = io.open(SRC, encoding="utf-8").read()
n0 = len(h)
done = []


def swap(old, new, label):
    global h
    assert old in h, "MISSING ANCHOR: " + label
    h = h.replace(old, new, 1)
    done.append(label)


def cut(a, b):
    i = h.index(a)
    return h[i:h.index(b, i)]


# ---------------------------------------------------------------- sources
SRC_ADD = r"""<h3>Round four &mdash; official manufacturer data and purchase records</h3>
<div class="scroll"><table>
<thead><tr><th>Source</th><th>Used for</th><th>Quality</th></tr></thead>
<tbody>
<tr><td><b>BorgWarner EFR 7163 product sheet</b><br>
<code>borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7163-f.pdf</code></td>
<td>Compressor map: efficiency contour values 0.58 to 0.74, speed lines 44/84/111/132/150 krpm,
axis extents, wheel diameters, and the statement that the map applies to all 7163 units including
the 7163-G twin-scroll. &sect;25</td>
<td><span class="pill p-ok">Official manufacturer</span></td></tr>

<tr><td><b>BorgWarner EFR 7670 product sheet</b><br><code>.../efr-7670-b.pdf</code></td>
<td>Peak island 0.75, speed lines, wheel diameters. &sect;25.1</td>
<td><span class="pill p-ok">Official manufacturer</span></td></tr>

<tr><td><b>BorgWarner EFR 7064 product sheet</b><br><code>.../efr-7064-b.pdf</code></td>
<td>Peak island 0.76, speed lines, wheel diameters. &sect;25.1</td>
<td><span class="pill p-ok">Official manufacturer</span></td></tr>

<tr><td><b>BorgWarner EFR power range and rotor group chart</b><br>
<code>.../efr-power-range.pdf</code></td>
<td>Confirms the 7163-G is the 0.80 A/R T4 twin-scroll wastegated unit, complete turbo
11639880002, supercore 11637105000, housing 11631008002 &mdash; matching Dan's TurboKits
invoice. &sect;25.1</td>
<td><span class="pill p-ok">Official manufacturer</span></td></tr>

<tr><td><b>Mishimoto MMRAD-CEL-89 product listing</b></td>
<td>Radiator overall 714 &times; 439 &times; 64.5 mm, core 699 &times; 318 mm face and 51.8 mm
thick, two rows, 1.25 in ports. &sect;28.1</td>
<td><span class="pill p-ok">Vendor specification</span></td></tr>

<tr><td><b>Soara Performance product pages</b> &mdash; 3S-GTE dual plenum intake manifolds</td>
<td>Characterising the plenum: 75, 80 and 90 mm throttle-flange variants exist for the 3S-GTE,
hyperbolic bellmouths, stated 3 bar boost rating, gen2 and gen3-4-5 flange options. &sect;02</td>
<td><span class="pill p-warn">Manufacturer marketing</span> &mdash; no flow-bench data is
published, so the plenum is treated as "not a restriction" rather than quantified</td></tr>

<tr><td><b>Bosch 0 280 750 474 vendor listings</b> (UroTuning, FCP Euro, Pelican Parts,
autohausaz)</td>
<td>Cross-references to Porsche 997 605 115 01/03 and 99760511501, and to the VAG
022 133 062 series. All list it as a 74 mm throttle body; Dan's plate stamp of 745 is used
instead. &sect;10.1</td>
<td><span class="pill p-ok">Multiple independent vendors agree</span></td></tr>

<tr><td><b>Outsider Garage order #7870</b>, 5 January 2026</td>
<td>The three parts that fix the charge-pipe geometry: DBW manifold adapter $150, 3 inch HD clamp
throttle hose adapter $100, Bosch 74 mm e-throttle $225. &sect;10.1</td>
<td><span class="pill p-ok">Primary &mdash; Dan's own purchase record</span></td></tr>

<tr><td><b>Published community dyno results</b> &mdash; focusst.org (ZZP 480 whp), evolutionm.net
(Driven Fab Evo 9, 593 whp), miataturbo.net (Mazda BP), mr2oc.com and alltrac.net threads,
Link ECU forum</td>
<td>Bounding this model's output. &sect;26</td>
<td><span class="pill p-warn">Self-reported, mixed dyno types, publication bias toward good
results.</span> Used to answer "is the model in the right region", not "what will this car
make".</td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>What could not be obtained.</b> The official BorgWarner EFR 8374
sheet was not retrieved &mdash; repeated requests timed out. No official Garrett compressor map
has been read in any round of this work. Figures for the 8374 and for all three Garrett candidates
remain unverified and are flagged as such wherever they appear.</div>

"""
swap('<h2><span class="num">30</span>Sources</h2>',
     '<h2><span class="num">30</span>Sources</h2>\n' + SRC_ADD, "sources block")

# ---------------------------------------------------------------- open questions
old = cut('<section id="open">', '<footer>')
new = r"""<section id="open">
<h2><span class="num">31</span>Open questions and pending decisions</h2>
<p class="lede">Rewritten for round four. Items closed by the eight corrections have been moved to
the bottom. The list is ordered by how much it blocks other work.</p>

<h3>Blocking &mdash; nothing else can be finalised until these are answered</h3>
<ol class="q">
<li><b>Measure M1: the clear width of the CS bumper lower aperture</b>, inside edge to inside edge,
at the height the core will sit. This is now the <b>only</b> measurement still blocking the core
order &mdash; round four closed the depth question entirely (&sect;28.1) and the height question is
bounded by the radiator behind it. You need <b>&ge; 640 mm</b> for the recommended
610&nbsp;&times;&nbsp;305&nbsp;&times;&nbsp;102 core plus tank welds. <b>&ge; 720 mm</b> unlocks the
685 mm core, which &sect;28.4 shows is worth 2.5&nbsp;&deg;C of charge temperature for almost no
radiator penalty &mdash; the cheapest cooling on the list.</li>

<li><b>Verify the manifold pairing visually, once.</b> &sect;22 now rests on Dan's statement that
the manifold is 1+4&nbsp;/&nbsp;2+3. The arithmetic confirming that <i>this is the correct pairing</i>
is exact, but <b>nobody has traced the runners on the physical part.</b> Cylinders 1 and 4 should
enter one scroll at the turbine flange, 2 and 3 the other. Five minutes with a torch, and it must
happen <b>before the manifold is wrapped or lagged</b>.</li>

<li><b>Rebuild the G4X boost target table with a surge limit in it.</b> &sect;25.4 found that
holding 30 psi below about 2,750 rpm puts the compressor on or inside its surge line. The prior
research's <code>13_g4x_boost_target_table.csv</code> has no surge check in it and should not be
loaded. This is free to fix and much easier to set before the first tune than to diagnose
afterwards.</li>
</ol>

<h3>Needs a decision, but not blocking</h3>
<ol class="q" start="4">
<li><b>What rev limit do you want?</b> &sect;24 gives the whole band rather than a recommendation.
The honest summary: stock 7,000&nbsp;&rarr;&nbsp;7,200 rpm is worth about <b>8 whp</b> and costs
nothing; 7,200&nbsp;&rarr;&nbsp;7,500 is worth <b>3 whp</b> and costs a set of valve springs;
7,500&nbsp;&rarr;&nbsp;8,000 is worth <b>4 whp</b> and costs bearing and rod service life at
24.3&nbsp;m/s of mean piston speed. <b>The whole 1,000 rpm is worth less than the driveline
uncertainty.</b> Choose it for gearing and driveability, not for power.</li>

<li><b>Confirm the stock redline off your own tachometer and rev limiter.</b> This report uses
7,000 rpm for the Gen 2 3S-GTE. Round one used 6,650, which was never sourced. The number sets the
left-hand end of every table in &sect;24.</li>

<li><b>Is the LSD a clutch-plate unit or a helical / torque-biasing one?</b> &sect;27.1 shows this
changes the <i>sign</i> of one driveline term: a plate LSD with static preload makes the
steady-state loss worse, a helical is closer to neutral. It is worth about 0.7 percentage points
of driveline factor, or roughly 4 whp.</li>

<li><b>Accept the 390&ndash;430 whp band as the target?</b> &sect;24 and &sect;27 together put the
estimate at <b>401&ndash;427 whp at 7,500 rpm and 30 psi</b>, and <b>390&ndash;415 at the stock
7,000 rpm limit</b>. If that is not enough, the conversation changes from intercoolers to
displacement, and that is a different project. &sect;26 shows the model is 4&ndash;8% <i>below</i>
the nearest published comparable, so the band may be pessimistic.</li>

<li><b>Where does the boost-control solenoid bung go?</b> &sect;21.11 makes this a build note
rather than an open question, but it is not done: it needs a 1/8&nbsp;NPT bung in the
<b>cold-side charge pipe, pre-throttle</b>. Decide the position before the 3.0&nbsp;in cold pipe is
fabricated, because adding it afterwards means cutting a finished pipe.</li>

<li><b>Pusher fans: how many, and where?</b> &sect;28.5 recommends <b>one puller behind the
radiator if it fits</b>, one pusher between condenser and radiator if it does not, and
<b>no pusher on the condenser at all</b>. That last one is the change from what was planned. Check
clearance from the radiator to the crank pulley and timing cover before committing to shortening
the condenser.</li>
</ol>

<h3>Measurements that would replace a model with a fact</h3>
<ol class="q" start="10">
<li><b>Put the car on a dyno.</b> Everything in this report is an estimate. One session produces
the power figure, the drivetrain loss from a coast-down, and enough log to back-calculate VE. It
replaces three of the four largest uncertainties at once. <b>This is the single highest-value
action available.</b></li>

<li><b>Back-calculate VE from a logged pull.</b> Log MAP, IAT and injector duty on one third-gear
pull. Adjusted VE should land at 90&ndash;105%; if it does not, the model in &sect;24 is wrong and
should be rebuilt around the measurement.</li>

<li><b>Wire the An&nbsp;Volt&nbsp;6 charge IAT input.</b> Already planned in the ECU pinout, not
yet connected. It makes &sect;19.4, &sect;21.9 and the whole core-depth argument in &sect;28
checkable in one afternoon.</li>

<li><b>Log turbo shaft speed against MAP and airflow.</b> You have the EFR speed sensor on SI-3.
That puts a real operating point on the official map in &sect;25.2 and settles both the surge
crossover and the compressor efficiency at a stroke.</li>

<li><b>Measure exhaust backpressure.</b> One gauge before the turbine turns the EMAP/IMAP 1.6
assumption in &sect;22.2 into a number. If it reads 2.0 with a correctly paired manifold, the cause
is turbine housing A/R or wastegate sizing, and that is a different fix.</li>

<li><b>Measure drivetrain loss with a coast-down.</b> &sect;27 uses a 0.78&ndash;0.83 band from
general AWD data, not from this car. The band is worth &plusmn;13 whp and it is the largest single
unverified constant left.</li>
</ol>

<h3>Model uncertainty &mdash; stated, not resolved</h3>
<ol class="q" start="16">
<li><b>The surge and choke coordinates on the official 7163 map were digitised from a printed
plot</b>, not from BorgWarner's underlying data. Good to roughly &plusmn;1.5&nbsp;lb/min and
&plusmn;0.08&nbsp;PR. Treat the 2,750 rpm surge crossover in &sect;25.4 as
<b>&plusmn;250&nbsp;rpm</b>.</li>

<li><b>The efficiency surface in &sect;25 is a quadratic through thirteen printed contour
labels</b>, RMS 0.021. It cannot reproduce the sharp peak of the 0.74 island &mdash; the worst
residual, 0.039, is exactly there. At the design point the fit sits in a well-sampled region and is
trustworthy. Away from the labelled region it is extrapolation.</li>

<li><b>No official Garrett map has been read, in any round.</b> All three Garrett candidates'
efficiency figures are modelled. Do not use them to rank one Garrett against another. The official
EFR 8374 sheet was also not retrieved.</li>

<li><b>The radiator shadowing model in &sect;28.2 uses round-jet entrainment</b> to estimate how
much ambient air mixes into the intercooler's wake across the 203&ndash;254&nbsp;mm gap. That is a
free-jet correlation applied to a bounded space, so it probably <b>overestimates</b> the mixing.
The conclusion in &sect;28.3 does not depend on it, because that conclusion rests on the duty cycle
rather than on the mixing figure.</li>

<li><b>The charge-system fill time of 216&nbsp;ms assumes a 0.15&nbsp;kg/s spool-up flow and a 28%
core void fraction.</b> Both are estimates. Treat the absolute figure as &plusmn;30%. The
<i>differences</i> between pipe layouts in &sect;10.4 are reliable, because those are just volume
ratios.</li>

<li><b>The "350 whp" plenum threshold in the head-flow reference has no test data behind it</b> in
the supplied material. It is quoted from elsewhere. It no longer matters &mdash; the Soara plenum
is fitted &mdash; but it should not be treated as a measured number if it comes up again.</li>

<li><b>Two small, deliberate differences between the report's calculator and the &sect;21 model.</b>
See &sect;21.13. Neither changes a recommendation. Note also that the &sect;05 calculator still
defaults to a 76&nbsp;mm core; set the depth slider to 102&nbsp;mm to reproduce the round-four
numbers.</li>
</ol>

<h3>Closed by round four</h3>
<ul class="tight">
<li><s>Is the twin-scroll manifold paired wrong?</s> &mdash; no. It is 1+4 / 2+3 and correct.
&sect;22</li>
<li><s>Should the manifold be re-made?</s> &mdash; no. Recommendation withdrawn. &sect;22.3</li>
<li><s>Is the stock Gen 2 intake plenum a restriction above 350 whp?</s> &mdash; moot. A Soara
custom dual plenum is fitted. &sect;02, &sect;21.12</li>
<li><s>What pipe diameter into the throttle body?</s> &mdash; 3.0 in. The bought adapter decides
it. &sect;10.4</li>
<li><s>Is the 74.5 mm throttle body a restriction?</s> &mdash; no. Mach 0.078 at peak flow, using
26% of its capacity. &sect;10.2</li>
<li><s>Is the 1.7 mm step at the throttle worth machining out?</s> &mdash; no. 24 Pa, 0.24% of the
pressure-drop budget. &sect;10.3</li>
<li><s>Do the compressor maps come from BorgWarner?</s> &mdash; the prior ones did not, but they
were right anyway. The official sheet confirms the 7163's efficiency to within 0.013. &sect;25.3</li>
<li><s>Is there enough front-to-back room for a 102 mm core?</s> &mdash; yes, with 177&ndash;228 mm
to spare. Measurement M2 is closed. &sect;28.1</li>
<li><s>Does radiator shadowing rule out the deeper core?</s> &mdash; no, and round three
overweighted it. &sect;28.3</li>
<li><s>What do the drivetrain upgrades recover?</s> &mdash; almost nothing on a steady-state dyno,
about 2.4% in acceleration. &sect;27</li>
<li><s>Which prior research files can be trusted?</s> &mdash; three of twenty. &sect;29</li>
</ul>

<h3>Closed by round three</h3>
<ul class="tight">
<li><s>Which turbo?</s> &mdash; keep the EFR 7163. &sect;21.7</li>
<li><s>Displacement, 2.2 or 2.3 L?</s> &mdash; 2,188.8 cc. 87.5 mm bore. &sect;21.4</li>
<li><s>Which VE curve, and does it collapse?</s> &mdash; it tapers, it does not collapse; the
bottom end binds first. &sect;21.5</li>
<li><s>Where does the wastegate solenoid get its pressure?</s> &mdash; pre-throttle. &sect;21.11</li>
</ul>
</section>

"""
swap(old, new, "open questions")

io.open(SRC, "w", encoding="utf-8").write(h)
print("applied %d edits" % len(done))
for d in done:
    print("  -", d)
print("size %d -> %d" % (n0, len(h)))
