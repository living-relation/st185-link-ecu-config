# -*- coding: utf-8 -*-
"""Applies round four to intercooler-report.html, in place."""
import os, re, shutil, io, json

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "intercooler-report.html")
BAK = os.path.join(HERE, "intercooler-report.round3.bak.html")

import build_r4_sections as S
import build_r4_rewrites as RW

if not os.path.exists(BAK):
    shutil.copy(SRC, BAK)

h = io.open(SRC, encoding="utf-8").read()
n_before = len(h)
changes = []


def cut(a, b):
    """Return the slice from marker a up to (not including) marker b."""
    i = h.index(a)
    j = h.index(b, i)
    return h[i:j]


def swap(old, new, label):
    global h
    assert old in h, "MISSING ANCHOR: " + label
    h = h.replace(old, new, 1)
    changes.append(label)


# --------------------------------------------------------------- 0. header
swap('<div class="meta">Prepared 30 Aug 2026 &middot; BorgWarner EFR 7163',
     '<div class="meta">Round four &middot; 31 Aug 2026 &middot; BorgWarner EFR 7163',
     "header date")
swap('&middot; street + occasional track &middot; Weaverville, NC',
     '&middot; Soara dual plenum &middot; street + occasional track &middot; Weaverville, NC',
     "header subtitle")

# --------------------------------------------------------------- 1. nav
swap('<a href="#recon" style="color:#ffb347">Reconciliation</a>'
     '<a href="#manifold" style="color:#ffb347">Manifold</a>'
     '<a href="#sources">Sources</a><a href="#open">Open Questions</a>',
     '<a href="#recon">Reconciliation</a><a href="#manifold">Manifold</a>'
     '<a href="#r4" style="color:#ffb347">Round Four</a>'
     '<a href="#rpmrange" style="color:#ffb347">Rev Range</a>'
     '<a href="#officialmap" style="color:#ffb347">Official Map</a>'
     '<a href="#dynocheck" style="color:#ffb347">Dyno Check</a>'
     '<a href="#driveline" style="color:#ffb347">Drivetrain</a>'
     '<a href="#packaging" style="color:#ffb347">Packaging</a>'
     '<a href="#audit" style="color:#ffb347">File Audit</a>'
     '<a href="#sources">Sources</a><a href="#open">Open Questions</a>',
     "nav")

# --------------------------------------------------------------- 2. exec summary
old_banner = cut('<div class="callout c-bad" style="margin-top:14px">',
                 '<div class="callout c-warn" style="margin-top:10px"><b>Round two')
new_banner = r"""<div class="callout c-bad" style="margin-top:14px">
<b>Round four, 31 August 2026 &mdash; read <a href="#r4">&sect;23</a> before anything else.</b>
Dan supplied eight corrections to the inputs, plus the purchase records for the throttle body
and its adapters. Everything downstream was re-derived. The five biggest consequences:
<b>(1)</b> <b>The exhaust manifold is already paired 1+4 / 2+3 and is correct.</b> &sect;22 is
rewritten from a fault report into a validation, and the "re-make the manifold" recommendation,
the 7 whp and the 300&ndash;500 rpm spool penalty are <b>withdrawn</b>. <a href="#manifold">&sect;22</a>
<b>(2)</b> <b>There is no dyno figure anywhere in this report.</b> Every power number is a
modelled estimate. &sect;26 checks the model against eight published community results.
<a href="#dynocheck">&sect;26</a>
<b>(3)</b> The power figure becomes a <b>band, not a point: 390&ndash;430 whp</b> across the
stock 7,000 rpm limit to 8,000 rpm, on a 0.78&ndash;0.83 driveline factor.
<a href="#rpmrange">&sect;24</a>
<b>(4)</b> The <b>official BorgWarner 7163 map</b> was retrieved and read. It confirms the prior
compressor efficiency to within 0.013 &mdash; and reveals that <b>holding full boost below about
2,750 rpm puts the compressor inside its surge line</b>. <a href="#officialmap">&sect;25</a>
<b>(5)</b> The <b>charge pipe is no longer a decision</b>. The bought throttle adapter is
3.0&nbsp;inch, so the cold side is 3.0&nbsp;in and the hot side is 2.5&nbsp;in.
<a href="#pipes">&sect;10</a></div>

<div class="callout c-warn" style="margin-top:10px">
<b>Round three, 30 August 2026 &mdash; partly superseded by round four.</b>
<b>(1)</b> The power number was resolved at 404 whp at 7,500 rpm and 30 psi. Round four puts it
at <b>411 whp on the recommended core</b>, with a band of 401&ndash;427 from the driveline factor
alone. <a href="#recon">&sect;21.1</a>
<b>(2)</b> The <b>Garrett G25-770 recommendation is withdrawn</b> &mdash; that part does not
appear in Garrett's catalogue. <b>Keep the EFR 7163.</b> <a href="#recon">&sect;21.7</a>
<b>(3)</b> The core grows from 76 mm to <b>102 mm deep</b>. Round four confirms this and gives a
better reason for it. <a href="#packaging">&sect;28</a>
<b>(4)</b> The claim that the twin-scroll manifold is paired wrong is <b>withdrawn</b>.
<a href="#manifold">&sect;22</a>
<b>(5)</b> The <b>wastegate solenoid must be fed pre-throttle</b>. Unchanged.
<a href="#recon">&sect;21.11</a></div>

"""
swap(old_banner, new_banner, "exec banner")

# lede
old_lede = cut('<p class="lede">Short version: buy a <b>610',
               '<div class="rec">\n<h3>Recommended specification</h3>')
new_lede = r"""<p class="lede">Short version: buy a <b>610 &times; 305 &times; 102&nbsp;mm
bar-and-plate core</b>, build it with <b>fabricated tapered side-in / side-out end tanks</b>, run
<b>2.5&nbsp;inch hot-side and 3.0&nbsp;inch cold-side piping</b> into the 3&nbsp;inch throttle
adapter you already own, and spend the real effort on the <b>ducting</b>. The core choice is worth
about nine degrees. The ducting is worth twenty-seven.</p>

<div class="callout c-bad" style="margin-top:4px"><b>Every horsepower figure in this report is an
estimate.</b> The engine is not finished and has never been on a dynamometer. The numbers come from
a volumetric-efficiency model, cross-checked against published dyno results for comparable
builds in <a href="#dynocheck">&sect;26</a>. Treat them as a design target, not a measurement.</div>

"""
swap(old_lede, new_lede, "exec lede")

# spec block
swap('<div class="specline"><span class="k">Hot-side pipe</span><span class="v">2.5&nbsp;in OD '
     '(2.0&nbsp;in turbo outlet &rarr; short diffuser)</span></div>\n'
     '<div class="specline"><span class="k">Cold-side pipe</span><span class="v">2.5&nbsp;in OD, '
     'taper to 2.9&nbsp;in at the throttle body only</span></div>',
     '<div class="specline"><span class="k">Hot-side pipe</span><span class="v">2.5&nbsp;in OD '
     '(2.0&nbsp;in turbo outlet &rarr; short diffuser) <span class="note">&mdash; 201 ft/s, in '
     'Garrett\'s band</span></span></div>\n'
     '<div class="specline"><span class="k">Cold-side pipe</span><span class="v"><b>3.0&nbsp;in OD '
     'the whole run</b> <span class="note">&mdash; fixed by the bought 3 in throttle adapter. '
     '&sect;10</span></span></div>\n'
     '<div class="specline"><span class="k">Throttle body</span><span class="v">Bosch 0 280 750 474, '
     '<b>74.5&nbsp;mm</b> bore <span class="note">&mdash; uses 26% of its capacity. Not a '
     'restriction.</span></span></div>\n'
     '<div class="specline"><span class="k">Intake plenum</span><span class="v">Soara Performance '
     'custom dual plenum, 3&nbsp;in flange <span class="note">&mdash; closes the stock-plenum '
     'question</span></span></div>',
     "spec pipes")
swap('<div class="specline"><span class="k">Predicted outlet IAT</span><span class="v">70&nbsp;&deg;C '
     '(157&nbsp;&deg;F) at 30&nbsp;psi, 32&nbsp;&deg;C ambient, 60&nbsp;mph '
     '<span class="note">&mdash; 79 &deg;C on the 76 mm core</span></span></div>\n'
     '<div class="specline"><span class="k">Predicted total &Delta;P</span><span class="v">'
     '1.4&ndash;1.7&nbsp;psi (~6% of 25&nbsp;psi boost)</span></div>',
     '<div class="specline"><span class="k">Predicted outlet IAT</span><span class="v">70&nbsp;&deg;C '
     '(157&nbsp;&deg;F) at 30&nbsp;psi, 32&nbsp;&deg;C ambient, 100&nbsp;km/h '
     '<span class="note">&mdash; 79 &deg;C on a 76 mm core</span></span></div>\n'
     '<div class="specline"><span class="k">Predicted total &Delta;P</span><span class="v">'
     '<b>1.41&nbsp;psi</b> (4.7% of 30&nbsp;psi boost) <span class="note">&mdash; itemised in '
     '&sect;10.7</span></span></div>\n'
     '<div class="specline"><span class="k">Charge system volume</span><span class="v">15.8&nbsp;L, '
     '7.2&times; displacement, 216&nbsp;ms fill <span class="note">&mdash; round three said 9.1 L '
     'and was wrong</span></span></div>\n'
     '<div class="specline"><span class="k">Rev limit</span><span class="v">Your choice, '
     '7,000&ndash;8,000. The whole band is worth 15 whp. <span class="note">&sect;24</span></span></div>',
     "spec iat")

# KPI grid
old_kpi = cut('<div class="grid g4">\n<div class="kpi"><div class="lab">Peak air mass flow</div>',
              '<h3>The five decisions, and the honest confidence in each</h3>')
new_kpi = r"""<div class="grid g4">
<div class="kpi"><div class="lab">Peak air mass flow</div><div class="val">51.4</div>
<div class="note">lb/min &mdash; 30 psi, 7,500 rpm, 32 &deg;C, charge-temp coupled. <b>Estimate.</b></div></div>
<div class="kpi"><div class="lab">Wheel horsepower</div><div class="val">401&ndash;427</div>
<div class="note">whp on E85 at 7,500 rpm. Band is the 0.78&ndash;0.83 driveline factor. <b>No dyno exists.</b> &sect;27</div></div>
<div class="kpi"><div class="lab">Compressor efficiency</div><div class="val g">0.693</div>
<div class="note">from the <b>official</b> BorgWarner 7163 map at this operating point. &sect;25</div></div>
<div class="kpi"><div class="lab">Turbo headroom</div><div class="val g">86%</div>
<div class="note">51.4 of the EFR 7163's 60 lb/min &mdash; and the official choke line is 60 at this pressure ratio</div></div>
</div>

<div class="grid g4">
<div class="kpi"><div class="lab">Charge temp at the valve</div><div class="val">70 &deg;C</div>
<div class="note">157 &deg;F on the 610&times;305&times;102 core, sealed duct, 100 km/h</div></div>
<div class="kpi"><div class="lab">Total pressure drop</div><div class="val g">1.41</div>
<div class="note">psi &mdash; 4.7% of boost. Throttle body contributes 0.047. &sect;10.7</div></div>
<div class="kpi"><div class="lab">Surge limit at full boost</div><div class="val w">2,750</div>
<div class="note">rpm. Below this, 30 psi is inside the compressor's surge line. &sect;25.4</div></div>
<div class="kpi"><div class="lab">Clear space behind the core</div><div class="val g">177&ndash;228</div>
<div class="note">mm, with a 102 mm core. Depth is not a constraint. &sect;28</div></div>
</div>

"""
swap(old_kpi, new_kpi, "exec kpis")

swap('<tr><td>Pipe diameter, mix or not</td><td><b>2.5&nbsp;in both, single taper at TB</b></td>',
     '<tr><td>Pipe diameter, mix or not</td><td><b>2.5&nbsp;in hot, 3.0&nbsp;in cold</b>'
     '<br><span class="note">changed in round four &mdash; the hardware decides it</span></td>',
     "decision table pipes")

# --------------------------------------------------------------- 3. build inputs
swap('<tr><td>Throttle body</td><td>Bosch 74 mm motorsport drive-by-wire, dual TPS</td>\n'
     '<td>Prior session <code>local_f8383d8c</code></td>\n'
     '<td><span class="pill p-info">Confirmed in chat, not in an invoice</span></td></tr>',
     r"""<tr style="background:rgba(56,211,159,.07)"><td>Throttle body</td>
<td><b>Bosch 0 280 750 474</b> drive-by-wire, dual TPS<br>
Porsche 997 605 115 03 / VAG 022 133 062 AJ<br>
<b>Bore 74.5 mm</b> &mdash; plate stamped "745". Sold as 74 mm.</td>
<td>Outsider Garage order <b>#7870</b>, 5 Jan 2026, $225. Part numbers read off the physical part.</td>
<td><span class="pill p-ok">Confirmed &mdash; invoice and part</span></td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Throttle body inlet adapter</td>
<td>Bosch 74 mm Throttle Body Hose and HD Clamp Adapter, variant
"<b>3 inch HD Clamp</b> / Silver"<br>
<span class="note">This is what fixes the cold pipe at 3.0 in. See &sect;10.</span></td>
<td>Outsider Garage #7870 line 2, $100</td>
<td><span class="pill p-ok">Confirmed</span></td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Throttle-to-plenum adapter</td>
<td>Custom DBW Manifold Adapter, Bright Silver.<br>
Manifold flange measures <b>109 mm across the centre</b>, tapering to <b>105 mm at the bolt-hole
centres</b>.</td>
<td>Outsider Garage #7870 line 1, $150; Dan's measurement;
<code>Custom-DBW-Manifold-Adapter_copy (1).pdf</code></td>
<td><span class="pill p-ok">Confirmed</span></td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Intake plenum</td>
<td><b>Soara Performance custom dual plenum</b>, 3S/5S, with a
<b>3 inch (76.2 mm) inside-diameter throttle flange</b>.<br>
<span class="note">Ukrainian maker; their published range covers 75, 80 and 90 mm throttle
flanges on the 3S-GTE, with hyperbolic bellmouths and a stated 3 bar boost rating.</span></td>
<td>Dan; Soara Performance product pages</td>
<td><span class="pill p-ok">Confirmed &mdash; closes Open Q6 from round three</span></td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Exhaust manifold pairing</td>
<td><b>1+4 / 2+3</b> &mdash; the correct pairing for a 1-3-4-2 firing order</td>
<td>Dan. The 1+2 / 3+4 pairing in the attached diagrams was corrected after those diagrams were
made; the attachment did not reflect it.</td>
<td><span class="pill p-ok">Confirmed by Dan &mdash; verify visually once, &sect;22.3</span></td></tr>""",
     "input: throttle/plenum/manifold")

swap('<tr><td>Radiator</td><td>ST185 alloy, core 690 &times; 325 &times; 40 mm; overall '
     '712 &times; 445 &times; 105 mm</td>\n'
     '<td>Speeding Parts ST185 alloy radiator spec</td>\n'
     '<td><span class="pill p-ok">Confirmed</span></td></tr>',
     r"""<tr style="background:rgba(56,211,159,.07)"><td>Radiator</td>
<td><b>Mishimoto MMRAD-CEL-89</b>, two-row brazed aluminium<br>
Overall <b>714 &times; 439 &times; 64.5 mm</b> (28.1 &times; 17.3 &times; 2.54 in)<br>
Core <b>699 &times; 318 mm face, 51.8 mm thick</b> (2.04 in), 1.25 in ports<br>
Mounted on the <b>engine side of the fender support</b></td>
<td>Vendor listing for the part; Dan's confirmation of the mounting position</td>
<td><span class="pill p-ok">Confirmed &mdash; replaces the generic ST185 alloy figure used in
rounds one to three</span></td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Front-end packaging</td>
<td>A/C condenser sits <b>even with the fender support</b>. The intercooler owns all space from
the condenser's front face forward to the bumper support. With a 76 mm core there is
<b>203&ndash;254 mm (8&ndash;10 in)</b> clear between the back of the core and the radiator.</td>
<td>Dan, measured</td>
<td><span class="pill p-ok">Confirmed &mdash; closes measurement M2. See &sect;28.</span></td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Transmission</td>
<td><b>Freshly rebuilt</b></td><td>Dan</td>
<td><span class="pill p-ok">Confirmed</span> &mdash; see &sect;27 for what it is worth</td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Driveshaft</td>
<td><b>One-piece carbon fibre</b><br><span class="note">deletes the centre support bearing and one
universal joint</span></td><td>Dan</td>
<td><span class="pill p-ok">Confirmed</span> &mdash; &sect;27</td></tr>

<tr style="background:rgba(255,179,71,.09)"><td>Rear differential</td>
<td><b>LSD</b> &mdash; type not yet stated</td><td>Dan</td>
<td><span class="pill p-warn">Clutch-plate or helical?</span> It changes the sign of a driveline
term. &sect;27.1</td></tr>

<tr style="background:rgba(56,211,159,.07)"><td>Wheels</td>
<td><b>Lightweight racing wheels</b></td><td>Dan</td>
<td><span class="pill p-ok">Confirmed</span> &mdash; acceleration, not steady-state power. &sect;27</td></tr>""",
     "input: radiator/packaging/drivetrain")

swap('<tr><td>Power target</td><td><b>~450 hp crank / ~380&ndash;400 whp on E85</b></td>',
     '<tr><td>Power target</td><td><b>390&ndash;430 whp estimated</b>, no dyno exists</td>',
     "input: power target label")

swap('<h4>Confirmed <em>not</em> yet purchased</h4>\n'
     '<p class="note">No intercooler, intercooler core, charge piping, silicone couplers, or intercooler\n'
     'clamps appear in any of the 64 invoices. This is a clean-sheet decision &mdash; nothing sunk.</p>',
     '<h4>Confirmed <em>not</em> yet purchased</h4>\n'
     '<p class="note">No intercooler, intercooler core, charge piping, silicone couplers or clamps '
     'appear in any invoice. The core and the pipework are still a clean-sheet decision. '
     '<b>The throttle body, its two adapters and the intake plenum are not</b> &mdash; those are '
     'bought, and &sect;10 works within them rather than around them.</p>',
     "input: not purchased")

# --------------------------------------------------------------- 4. section 10
old10 = cut('<section id="pipes">', '<!-- ============ 11 DP ============ -->')
swap(old10, RW.PIPES_NEW + "\n\n", "section 10 charge pipes")

# --------------------------------------------------------------- 5. section 11 numbers
swap('<p class="lede">Target: <b>&le; 1.5 psi total at peak flow</b>, which is 6% of 25 psi boost. My model\n'
     'puts the recommended build at 1.4&ndash;1.7 psi.</p>',
     '<p class="lede">Target: <b>&le; 1.5 psi total at peak flow</b>. The round-four build &mdash; '
     '2.5&nbsp;in hot, 3.0&nbsp;in cold, 610&times;305&times;102 core, 74.5&nbsp;mm throttle '
     '&mdash; comes to <b>1.41 psi</b>, which is 4.7% of 30 psi boost. Itemised in '
     '<a href="#pipes">&sect;10.7</a>.</p>\n'
     '<div class="callout c-info"><b>Round-four itemisation, replacing the four tiles below.</b> '
     'Hot pipe 2.5 in <b>0.586</b> &middot; core <b>0.180</b> &middot; end tanks <b>0.350</b> '
     '&middot; cold pipe 3.0 in <b>0.247</b> &middot; throttle body <b>0.047</b> &middot; the two '
     '1.7 mm steps <b>0.004</b> &nbsp;=&nbsp; <b>1.413 psi</b>. The hot side is now the largest '
     'single term, at 41% of the total, because it carries the least dense air.</div>',
     "section 11 lede")

swap('<div class="kpi"><div class="lab">Cold pipe, 2.5 in</div><div class="val">0.44</div>'
     '<div class="note">psi &mdash; 1.5 m, 4 bends</div></div>',
     '<div class="kpi"><div class="lab">Cold pipe, 3.0 in</div><div class="val g">0.25</div>'
     '<div class="note">psi &mdash; 1.5 m, 4 bends. Round four.</div></div>',
     "section 11 kpi cold")
swap('<div class="kpi"><div class="lab">Hot pipe, 2.5 in</div><div class="val">0.44</div>'
     '<div class="note">psi &mdash; 1.1 m, 3 bends</div></div>',
     '<div class="kpi"><div class="lab">Hot pipe, 2.5 in</div><div class="val w">0.59</div>'
     '<div class="note">psi &mdash; 1.1 m, 3 bends. Round four; round three under-read it.</div></div>',
     "section 11 kpi hot")
swap('<b>core is the smallest contributor</b> &mdash; about 12% of total loss. The piping and end tanks\n'
     'together account for ~80%.',
     '<b>core is nearly the smallest contributor</b> &mdash; about 13% of total loss. The piping and '
     'end tanks together account for ~84%, and the throttle body is 3%.',
     "section 11 callout")

# --------------------------------------------------------------- 6. section 13
old13 = cut('<section id="fitment">', '<!-- ============ 14 FINAL ============ -->')
swap(old13, RW.FIT_NEW + "\n\n", "section 13 fitment")

# --------------------------------------------------------------- 7. section 14
swap('<div class="specline"><span class="k">Core</span><span class="v">CSF #8067 bar &amp; plate<br>'
     '610 &times; 300 &times; 75 mm (24 &times; 12 &times; 3 in)<br>13.7 L, 850 hp rated, ~$329</span></div>',
     '<div class="callout c-warn" style="margin:-6px 0 16px"><b>Round-four corrections to this '
     'block.</b> Core depth is 102 mm (&sect;28.4). Cold pipe is 3.0 in, not 2.5 with a taper '
     '(&sect;10.4). Throttle body is 74.5 mm, not 74 (&sect;10.1). Predicted outlet is 70 &deg;C '
     'at 30 psi, not 55 &deg;C at 25 psi. Everything else below stands.</div>\n'
     '<div class="specline"><span class="k">Core</span><span class="v">Bar &amp; plate<br>'
     '<b>610 &times; 305 &times; 102 mm</b> (24 &times; 12 &times; 4 in)<br>19.0 L</span></div>',
     "final spec core")
swap('<div class="specline"><span class="k">Cold pipe</span><span class="v">2.5 in mandrel alloy<br>'
     '2.5 &rarr; 2.9 in taper, &le;7&deg;, last 150 mm into the 74 mm TB<br>'
     'BOV mounted close to the throttle</span></div>',
     '<div class="specline"><span class="k">Cold pipe</span><span class="v"><b>3.0 in mandrel alloy, '
     'whole run</b><br>straight into the bought 3 in hose adapter &mdash; no taper needed<br>'
     'BOV mounted close to the throttle</span></div>',
     "final spec cold pipe")
swap('<div class="kpi"><div class="lab">Predicted outlet IAT</div><div class="val g">55 &deg;C</div>'
     '<div class="note">130 &deg;F at 25 psi / 32 &deg;C ambient</div></div>',
     '<div class="kpi"><div class="lab">Predicted outlet IAT</div><div class="val g">70 &deg;C</div>'
     '<div class="note">157 &deg;F at 30 psi / 32 &deg;C ambient, 102 mm core</div></div>',
     "final spec kpi iat")
swap('<div class="kpi"><div class="lab">Predicted total &Delta;P</div><div class="val">1.4</div>'
     '<div class="note">psi &mdash; 5.6% of boost</div></div>',
     '<div class="kpi"><div class="lab">Predicted total &Delta;P</div><div class="val">1.41</div>'
     '<div class="note">psi &mdash; 4.7% of 30 psi boost</div></div>',
     "final spec kpi dp")
swap('<li><b>Measure M1&ndash;M4 from &sect;13</b> with the CS bumper and crash bar in place. Do not order\n'
     'until you have real numbers. If M1 &lt; 640 mm, order the 8047 instead.</li>',
     '<li><b>Measure M1 from &sect;13</b> &mdash; the aperture width &mdash; with the CS bumper and '
     'crash bar in place. M2 and M3 are answered by &sect;28; M1 is the only one still blocking. '
     'If M1 &lt; 640 mm, drop to a narrower core.</li>',
     "final spec build order")

# --------------------------------------------------------------- 8. section 22
old22 = cut('<section id="manifold">', '<!-- ============ 16 SOURCES ============ -->')
swap(old22, RW.MAN_NEW + "\n\n" + S.S23 + S.S24 + S.S25 + S.S26 + S.S27 + S.S28 + S.S29 + "\n\n",
     "section 22 + new sections 23-29")

# --------------------------------------------------------------- 9. renumber tail
swap('<h2><span class="num">23</span>Sources</h2>',
     '<h2><span class="num">30</span>Sources</h2>', "renumber sources")
swap('<h2><span class="num">24</span>Open questions and pending decisions</h2>',
     '<h2><span class="num">31</span>Open questions and pending decisions</h2>',
     "renumber open questions")

# --------------------------------------------------------------- 10. §21 patches
swap('<h3 id="r2110">21.10 &nbsp;Item 10 &mdash; exhaust manifold pairing</h3>\n'
     '<p class="note">This is large enough to have its own section. <b>The prior research is correct and the\n'
     'finding is verified independently.</b> See <a href="#manifold">&sect;22</a>.</p>',
     '<h3 id="r2110">21.10 &nbsp;Item 10 &mdash; exhaust manifold pairing</h3>\n'
     '<div class="callout c-good"><b>Resolved in round four, and the resolution is the opposite of '
     'what round three concluded.</b> The prior research described the manifold as 1+2 / 3+4 and '
     'round three verified that <i>that pairing</i> would be wrong. It would be. But the manifold '
     'on the car is <b>1+4 / 2+3</b> &mdash; the diagrams were corrected after they were drawn, and '
     'the attachment did not show it. <b>Nothing is wrong and nothing needs re-making.</b> The '
     'pulse-timing arithmetic is kept in <a href="#manifold">&sect;22</a> as the check that '
     'confirms 1+4 / 2+3 is correct.</div>',
     "21.10 manifold")

swap('<li><b>Whether the intake plenum is a limit.</b> The head-flow reference notes the stock Gen 2 plenum\n'
     'is documented to "struggle with flow above 350 whp." No plenum appears in the 64 invoices. At 404 whp\n'
     'this is a live question and it is not addressed anywhere in either body of work.</li>',
     '<li><b><s>Whether the intake plenum is a limit.</s> CLOSED in round four.</b> Dan is running a '
     '<b>Soara Performance custom dual plenum</b> with a 3 inch throttle flange, and a 74.5 mm Bosch '
     'throttle body. Those are exactly the two parts the head-flow reference said to change above '
     '450&ndash;500 whp. The model in this report assumes no plenum restriction; that assumption is '
     'now justified rather than hopeful. Worth noting that the "350 whp" figure in the head-flow '
     'reference is quoted from elsewhere and has no test data behind it in the supplied material.</li>',
     "21.12 plenum")

swap('<li><b>Drivetrain loss.</b> 20% is a considered choice from AWD data generally, not a measurement of\n'
     'this car. The one ST185-specific dyno figure found implies about 15%, but it is not a usable data\n'
     'point. A coast-down on a chassis dyno would settle it, and the answer moves the headline power by\n'
     '&plusmn;20 whp.</li>',
     '<li><b>Drivetrain loss.</b> Still the largest unverified constant. Round four reassessed it '
     'against the rebuilt gearbox, one-piece carbon driveshaft, LSD and lightweight wheels and '
     'concluded the steady-state factor <b>does not meaningfully change</b> &mdash; band 0.78 to '
     '0.83, midpoint still 0.80. See <a href="#driveline">&sect;27</a>. The band is worth '
     '&plusmn;13 whp. A coast-down settles it.</li>',
     "21.12 drivetrain")

swap('<div class="callout c-info"><b>Reproducing this.</b> <code>reconcile.py</code> performs the forensic',
     '<div class="callout c-info"><b>Round four adds:</b> <code>unified_model_r4.py</code> is the '
     'round-four model, <code>make_r4_chartdata.py</code> emits <code>data/chartdata_r4.js</code>, '
     'and <code>data/r4_console.txt</code> is the full numerical output with every intermediate '
     'value. <code>build_r4.py</code> applies round four to this page.<br><br>'
     '<b>Reproducing round three.</b> <code>reconcile.py</code> performs the forensic',
     "21.13 repro note")

# --------------------------------------------------------------- 11. inject R4 data + charts
r4data = io.open(os.path.join(HERE, "data", "chartdata_r4.js"), encoding="utf-8").read()
r4js = io.open(os.path.join(HERE, "r4_charts.js"), encoding="utf-8").read()
tail = "\ntry{initRound2();}catch(e){if(window.console)console.error(e);}\n"
assert tail in h
h = h.replace(tail, tail + "\n\n" + r4data + "\n" + r4js + "\n", 1)
changes.append("R4 data + charts")

# --------------------------------------------------------------- 12. footer
swap('<br><br>Prepared for Dan &middot; 30 August 2026 &middot; 5S-GTE ST185 project',
     '<br><br><b>All power figures in this report are estimates from a volumetric-efficiency model. '
     'This engine has never been run on a dynamometer.</b> The model is cross-checked against '
     'published third-party dyno results in &sect;26. Compressor efficiency for the EFR 7163 is read '
     'from the official BorgWarner product sheet (&sect;25); the surge and choke coordinates on that '
     'map are digitised from the printed plot and carry about &plusmn;1.5 lb/min of uncertainty. '
     'Cross-checked in Python (<code>unified_model_r4.py</code>).'
     '<br><br>Prepared for Dan &middot; round four, 31 August 2026 &middot; 5S-GTE ST185 project',
     "footer")

io.open(SRC, "w", encoding="utf-8").write(h)
print("applied %d edits" % len(changes))
for c in changes:
    print("  -", c)
print("size %d -> %d bytes" % (n_before, len(h)))
