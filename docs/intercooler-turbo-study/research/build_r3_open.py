# -*- coding: utf-8 -*-
"""Replace the open-questions section with the round-three list, and add the
explicit model-divergence note required by the cross-check."""
import io, os

HERE = "/sessions/amazing-blissful-bell/mnt/projects/5sgte-intercooler-research"
REPORT = os.path.join(HERE, "intercooler-report.html")
lines = io.open(REPORT, encoding="utf-8").read().split("\n")

# section id="open" starts at index of the line containing it
start = next(i for i, l in enumerate(lines) if 'id="open"' in l)
end = next(i for i in range(start, len(lines)) if "</section>" in lines[i])
assert lines[start].strip() == '<section id="open">', lines[start]

NEW = '''<section id="open">
<h2><span class="num">24</span>Open questions and pending decisions</h2>
<p class="lede">Rewritten for round three. Items closed by the reconciliation in &sect;21 have been
removed. The list is ordered by how much it blocks other work.</p>

<h3>Blocking &mdash; nothing else can be finalised until these are answered</h3>
<ol class="q">
<li><b>Measure M1&ndash;M4 in &sect;13, and add a fifth.</b> Still the largest unknown in this report.
&sect;21.8 now recommends a <b>102 mm deep</b> core rather than 76 mm, so the depth measurement matters
more than it did: you need <b>137 mm</b> clear from the back of the bumper skin to the front of the A/C
condenser (102 core + 25 duct + 10 mounting). The width requirement is unchanged at
&ge;&nbsp;640&nbsp;mm. <b>M5, new:</b> confirm the aperture is not wide enough to tempt you toward the
711 mm core &mdash; the radiator behind it is only 712 mm overall, so anything wider than about 650 mm
of core is shadowing rather than cooling.</li>

<li><b>Confirm the manifold pairing on the physical part.</b> &sect;22 is built on the prior research's
statement that the manifold is paired 1+2&nbsp;/&nbsp;3+4. The <i>consequences</i> of that pairing are
verified arithmetic, but <b>the pairing itself has not been confirmed by looking at the manifold.</b>
Trace which two runners enter each scroll at the turbine flange and confirm before spending anything.
If it is already 1+4&nbsp;/&nbsp;2+3, &sect;22 does not apply and you have found 7 whp and 400 rpm of
spool that you already own.</li>

<li><b>Re-make the manifold, fit an undivided housing, or leave it?</b> &sect;22 recommends re-making it.
This forks the build because it should happen <i>before</i> any dyno tuning, and because judging the
turbo on a mis-paired manifold will push you toward buying a turbo you do not need.</li>
</ol>

<h3>Needs a decision, but not blocking</h3>
<ol class="q" start="4">
<li><b>Accept 404 whp as the target?</b> &sect;21.1 resolves the honest number at <b>404 whp</b>
(505 crank) at 7,500 rpm and 30 psi. The earlier figures &mdash; this report's 420&ndash;480 and the
prior research's 466&ndash;517 &mdash; are both superseded. If 404 whp is not enough, the conversation
changes from intercoolers to displacement, and that is a different project.</li>

<li><b>Redline: 7,200 or 7,500?</b> &sect;21.5 recommends 7,200 with 7,500 as an outer limit.
7,200&nbsp;&rarr;&nbsp;7,500 is worth <b>+6 whp</b> and costs a set of valve springs and some service
life. It is a small, cheap decision either way, and it is genuinely yours.</li>

<li><b>Does the intake plenum need replacing?</b> Raised by the supplied head-flow reference, which
notes the stock Gen&nbsp;2 plenum is documented to "struggle with flow above 350 whp." <b>No plenum
appears in the 64 invoices.</b> At 404 whp this is a live question and it is addressed nowhere in
either body of work. It could be worth more than the core depth change.</li>

<li><b>3.0 in intercooler ports against 2.5 in piping.</b> Carried over unresolved. Every assembled
core in &sect;19.1 ships with 3.0 in ports; &sect;10 specifies 2.5 in pipe. Step at the tank with a
short reducer, or move the whole charge system to 3.0 in. Do not run a sharp step.</li>

<li><b>Plumb the boost-control solenoid pre-throttle.</b> &sect;21.11 makes this a build note rather
than an open question, but it is not done yet: it needs a 1/8 NPT bung in the cold-side charge pipe.
Decide where before the pipes are fabricated, because adding it afterwards means cutting a finished
pipe.</li>
</ol>

<h3>Measurements that would replace a model with a fact</h3>
<ol class="q" start="9">
<li><b>Back-calculate VE from a log.</b> &sect;21.2 found <b>three different VE curves inside the prior
research and two more in this report</b>. Logging MAP, IAT and injector duty on one pull and
back-calculating VE would settle the largest remaining modelling argument in an afternoon. Adjusted VE
should land at 90&ndash;105%; if it does not, the model in &sect;21 is wrong and should be rebuilt around
the measurement.</li>

<li><b>Wire the An&nbsp;Volt&nbsp;6 charge IAT input.</b> It is already planned in the ECU pinout and
not yet connected. It makes the whole of &sect;19.4 and &sect;21.9 checkable, and charge temperature is
the single quantity that most separates the three models.</li>

<li><b>Measure drivetrain loss with a coast-down.</b> &sect;21.3 uses 20% from general AWD data, not
from this car. The band 18&ndash;22% moves the headline power by about &plusmn;20 whp, and it is the
largest single unverified constant in the report.</li>

<li><b>Measure exhaust backpressure.</b> One gauge before and after the manifold change turns the whole
of &sect;22.2 from an estimate into a measurement. You already have the 5-bar MAP sensor and the turbo
speed sensor for the other half of the picture.</li>
</ol>

<h3>Model uncertainty &mdash; stated, not resolved</h3>
<ol class="q" start="13">
<li><b>The EFR 7163's compressor efficiency.</b> The digitized official map fit has RMS 0.048 efficiency
points on this turbo, the worst of the four EFRs, and it is the turbo the headline number depends on.
A true 66% rather than 70.6% puts the charge about 5&nbsp;&deg;C hotter than modelled here.</li>

<li><b>The two Garrett candidates have no official map data at all.</b> &sect;21.6. Their efficiency
figures are modelled and are used only to show that the turbo choice does not matter at 30 psi. Do not
use them to rank one Garrett against another.</li>

<li><b>The 1.6&nbsp;&rarr;&nbsp;2.0 backpressure shift in &sect;22.2 is an informed estimate.</b> So is
the 300&ndash;500 rpm spool figure, which comes from published twin-versus-single-scroll tests on other
engines. The direction is certain; the magnitudes are worth &plusmn;50%.</li>

<li><b>Two small, deliberate differences between the report's calculator and the &sect;21 model.</b>
See the note in &sect;21.13. Neither changes a recommendation.</li>
</ol>

<h3>Closed by round three</h3>
<ul class="tight">
<li><s>Which turbo?</s> &mdash; keep the EFR 7163. &sect;21.7</li>
<li><s>Is the 7163 used up?</s> &mdash; no. 84% of choke, PR 3.42 of 3.6. &sect;21.1</li>
<li><s>Displacement, 2.2 or 2.3 L?</s> &mdash; 2,188.8 cc. 87.5 mm bore. &sect;21.4</li>
<li><s>Which VE curve, and does it collapse?</s> &mdash; it tapers, it does not collapse; the bottom
end binds first. &sect;21.5</li>
<li><s>What charge temperature should the build assume?</s> &mdash; 70 &deg;C on the recommended core.
&sect;21.9</li>
<li><s>Core depth, 76 or 102 mm?</s> &mdash; 102 mm. &sect;21.8</li>
<li><s>Where does the wastegate solenoid get its pressure?</s> &mdash; pre-throttle. &sect;21.11</li>
</ul>
</section>'''

lines[start:end+1] = NEW.split("\n")
html = "\n".join(lines)

# ---- divergence note, appended to section 21 ----
DIV = '''
<h3 id="r2113">21.13 &nbsp;Where the report's calculator and the &sect;21 model still differ</h3>
<p class="note">The interactive calculator in &sect;05 and the Python model behind &sect;21 were run
against each other at the same design point. They agree on the two things that matter and differ on two
things that do not. Both differences are deliberate and are recorded here rather than hidden.</p>
<div class="scroll"><table>
<thead><tr><th>Quantity</th><th class="num">&sect;05 calculator</th><th class="num">&sect;21 model</th>
<th class="num">Difference</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Intercooler outlet temperature</td><td class="num">69.2 &deg;C</td><td class="num">69.6 &deg;C</td>
<td class="num">0.4 &deg;C</td><td><span class="pill p-ok">Agree.</span> Same &epsilon;-NTU code, same core.</td></tr>
<tr><td>Core effectiveness &epsilon;</td><td class="num">0.787</td><td class="num">0.793</td>
<td class="num">0.006</td><td><span class="pill p-ok">Agree.</span></td></tr>
<tr><td>Wheel horsepower</td><td class="num">417</td><td class="num">411</td><td class="num">6 whp</td>
<td><span class="pill p-ok">Agree within the rounding of the VE slider.</span></td></tr>
<tr><td><b>Pressure ratio</b></td><td class="num">3.30</td><td class="num">3.42</td><td class="num">0.12</td>
<td><b>Deliberate.</b> The &sect;04 formula is <code>PR = P_MAP / (P_amb &times; 0.97)</code> and stops
at the manifold. The &sect;21 model adds the 1.5 psi the compressor must also make up across the core
and pipework, because that pressure has to come from somewhere. The &sect;21 figure is the more correct
one; the &sect;05 one is kept because &sect;04 documents that exact equation and the &sect;05
pressure-drop tab handles &Delta;P separately.</td></tr>
<tr><td><b>Compressor outlet temperature</b></td><td class="num">207 &deg;C</td><td class="num">214 &deg;C</td>
<td class="num">7 &deg;C</td><td><b>Follows from the row above.</b> A higher pressure ratio means more
compression work and a hotter outlet. It washes out almost entirely after the intercooler, which is why
the outlet temperatures still agree to 0.4 &deg;C.</td></tr>
<tr><td><b>Volumetric efficiency</b></td><td class="num">0.94, fixed by the slider</td>
<td class="num">0.938, recomputed</td><td class="num">&mdash;</td>
<td><b>Deliberate.</b> The calculator takes VE as an input so you can test your own assumption. The
&sect;21 model recomputes it from the Taylor Mach index at the solved charge temperature. The slider
default of 0.94 is set to the &sect;21 value at the design point, so they start in agreement and diverge
only if you move the rpm slider without moving the VE slider.</td></tr>
</tbody></table></div>
<div class="callout c-info"><b>Reproducing this.</b> <code>reconcile.py</code> performs the forensic
diff of the prior research (stage 1) and builds the unified model (stage 2).
<code>unified_model.py</code> is the model itself. <code>make_r3_chartdata.py</code> emits
<code>data/chartdata_r3.js</code>, which is the data block embedded in this page.
<code>verify_r3.js</code> loads this file in a headless DOM and checks that all 27 charts mount, both
calculators compute, there are no console errors, and the page loads no external resources. All four
are in the project folder alongside this report.</div>
</section>'''

marker = '''<b>Whether the intake plenum is a limit.</b> The head-flow reference notes the stock Gen 2 plenum
is documented to "struggle with flow above 350 whp." No plenum appears in the 64 invoices. At 404 whp
this is a live question and it is not addressed anywhere in either body of work.</li>
</ul></div>
</section>'''
assert html.count(marker) == 1, html.count(marker)
html = html.replace(marker, marker.replace("</section>", "") + DIV)

io.open(REPORT, "w", encoding="utf-8").write(html)
print("open questions + divergence note written, %d bytes" % len(html))
