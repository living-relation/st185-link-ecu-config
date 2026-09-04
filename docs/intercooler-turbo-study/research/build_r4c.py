# -*- coding: utf-8 -*-
"""Round four, part three: revised charge-pipe recommendation.

Dan clarified after part one:
  - no charge piping has been bought
  - 3.0 in throughout is too large to route around the engine and frame rails
  - the 3 in figure applies ONLY to the HD clamp adapter at the throttle body
  - he is not concerned about small transition losses
  - construction is fully welded, with HD clamps at three places only
  - 2.5 in is the working assumption unless the numbers clearly say otherwise
"""
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


# ============================================================ 10.1 intro
swap("""<div class="callout c-bad"><b>Rewritten in round four. This is no longer a decision.</b>
Round three recommended 2.5&nbsp;in both sides with a taper to 2.9&nbsp;in at the throttle.
That was written without knowing what had been bought. Outsider Garage order <b>#7870</b>,
5 January 2026, contains a <b>Bosch 74&nbsp;mm Throttle Body Hose and HD Clamp Adapter</b>
in the "<b>3 inch HD Clamp</b>" variant. The cold pipe therefore terminates at a
<b>3.0&nbsp;in (76.2&nbsp;mm) hose joint on a part that is already on the shelf.</b> The
question is not what diameter to run. It is where, if anywhere, to step down from it.</div>""",
     """<div class="callout c-bad"><b>Rewritten in round four.</b> Round three recommended
2.5&nbsp;in both sides with a taper to 2.9&nbsp;in at the throttle body, and did so without
knowing the real throttle bore or what had been bought.<br><br>
<b>What is bought:</b> Outsider Garage order <b>#7870</b>, 5 January 2026, includes a
<b>Bosch 74&nbsp;mm Throttle Body Hose and HD Clamp Adapter</b> in the
"<b>3 inch HD Clamp</b>" variant. <b>That 3 inch figure applies to the adapter, and to
nothing else.</b> No charge piping has been purchased.<br><br>
<b>What is not bought, and is therefore still a decision:</b> the pipe runs themselves, and
the intercooler's own port size &mdash; because &sect;08 and &sect;14 specify
<b>fabricated</b> end tanks, so the port is whatever gets welded on.<br><br>
<b>The answer is 2.5&nbsp;inch both sides</b>, with one welded cone up to 3.0&nbsp;inch over
the last 150&nbsp;mm to meet the adapter. The working below shows why, and what the choice
costs.</div>""",
     "10 intro")

swap("""<div class="eq">cold charge pipe
  &rarr; <b>3.00 in (76.2 mm) hose and HD clamp adapter</b>   <span class="cm">Outsider Garage #7870 line 2, $100</span>""",
     """<div class="eq">intercooler outlet tank        <span class="cm">port size is YOUR choice - the tanks are fabricated. Weld 2.50 in.</span>
  &rarr; cold charge pipe, 2.50 in   <span class="cm">welded throughout; one HD clamp for alignment</span>
  &rarr; welded cone 2.50 &rarr; 3.00 in over the last 150 mm
  &rarr; <b>3.00 in (76.2 mm) hose and HD clamp adapter</b>   <span class="cm">Outsider Garage #7870 line 2, $100. BOUGHT.</span>""",
     "10.1 chain")

# ============================================================ 10.4 rewrite
old104 = cut("<h3>10.4 &nbsp;Cold side &mdash; run 3.0 in, or step down and back up?</h3>",
             "<h3>10.5 &nbsp;Hot side &mdash; chosen independently</h3>")
new104 = r"""<h3>10.4 &nbsp;How the pipe is built, and why that changes the answer</h3>
<div class="callout c-info"><b>Construction, as Dan intends to build it.</b> Fully welded
tube, with heavy-duty clamped joints at <b>three places only</b>:
<ol class="q" style="margin-top:6px">
<li>the <b>intercooler</b>, so the core can come out;</li>
<li>the <b>throttle body</b>, at the bought 3&nbsp;inch HD clamp adapter;</li>
<li>one <b>alignment joint</b> in the run, so the pipe can be fitted without fighting
tolerance stack-up.</li>
</ol>
<b>This matters more than it sounds.</b> Round three's argument against a 2.5&nbsp;in cold
side was that it would need two extra <i>joints</i> &mdash; a step down at the intercooler
and a step back up at the throttle. <b>On a welded pipe a diameter change is not a joint. It
is a cone, and it costs one extra weld.</b> The joint-count objection disappears, and with it
the reason round four's first pass recommended 3.0&nbsp;inch.</div>

<h3>10.5 &nbsp;Velocity and pressure drop at real inside diameters</h3>
<p class="note">Design point 51.4&nbsp;lb/min (0.389&nbsp;kg/s) at 7,500 rpm and 30 psi. Hot
side at 311&nbsp;kPa and 214&nbsp;&deg;C, so &rho;&nbsp;=&nbsp;2.22&nbsp;kg/m&sup3;. Cold side
at 303&nbsp;kPa and 70&nbsp;&deg;C, so &rho;&nbsp;=&nbsp;3.05&nbsp;kg/m&sup3;. The hot side
carries the same mass through a gas 27% less dense, which is why it always runs faster and
drops more pressure through the same pipe.</p>
<div class="callout c-warn"><b>Every diameter below is a real inside diameter</b>, computed
as outside diameter minus twice a <b>0.065&nbsp;inch (1.651&nbsp;mm)</b> wall, which is the
standard aluminium charge-pipe wall thickness. Quoting velocities against nominal outside
diameter, which is common, understates them by 8&ndash;12%.</p>
<div class="scroll"><table id="t-r4pipes">
<thead><tr><th class="num">Pipe OD</th><th class="num">Real ID<br>at 0.065 in wall</th>
<th class="num">Hot side</th><th class="num">Hot &Delta;P<br>1.1 m, 3 bends</th>
<th class="num">Cold side</th><th class="num">Cold &Delta;P<br>1.5 m, 4 bends</th>
<th class="num">Volume<br>per metre</th></tr></thead>
<tbody></tbody></table></div>

<h3>10.6 &nbsp;Routing clearance, treated as a real constraint</h3>
<p class="note">Dan's objection to 3&nbsp;inch is that it will not route around the engine and
the frame rails. That is a physical constraint and it deserves a number rather than a
shrug.</p>
<div class="eq">what actually sets the space a pipe needs:

  bare welded tube        = outside diameter
  at a clamped joint      = OD + about 18 mm   <span class="cm">6 mm of silicone wall each side, 3 mm of T-bolt band each side</span>
  a 90&deg; mandrel bend at R/D 1.5 occupies a square corner of side
                          = centreline radius + OD/2</div>
<div class="scroll"><table id="t-r4route">
<thead><tr><th class="num">Pipe OD</th><th class="num">Real ID</th>
<th class="num">Bare tube<br>envelope</th><th class="num">At a clamped<br>joint</th>
<th class="num">Bend centreline<br>radius, R/D 1.5</th>
<th class="num">90&deg; bend<br>corner box</th></tr></thead>
<tbody></tbody></table></div>

<div class="callout c-bad"><b>A 3.0&nbsp;inch 90&deg; bend needs 25&nbsp;mm more corner room
than a 2.5&nbsp;inch one, in both directions, at every bend.</b> On a cold side with four
bends that is four corners each needing a 152&nbsp;mm square instead of a 127&nbsp;mm square.
Between a frame rail and a cam cover that is frequently the difference between a pipe that
goes in and a pipe that has to be re-made. <b>Dan's objection is correct and it is the
binding constraint here</b>, because as the next section shows, the thing it is traded
against is worth a tenth of a horsepower.</div>

<h3>10.7 &nbsp;What 2.5 inch actually costs, against 3.0 inch</h3>
<div class="scroll"><table id="t-r4cold">
<thead><tr><th>Cold-side layout</th><th class="num">Peak velocity</th>
<th class="num">Pressure drop</th><th class="num">Pipe volume</th>
<th class="num">Total charge<br>system volume</th><th class="num">&times; displacement</th>
<th class="num">Boost fill time</th><th class="num">90&deg; bend<br>corner box</th></tr></thead>
<tbody></tbody></table></div>

<p class="note">Every row ends at the same bought 3.0&nbsp;inch adapter. The hot side is held
at 2.5&nbsp;in in every row so the comparison is clean. "Welded cone" means a gradual
diffuser at 7&deg; per wall, not a sudden step &mdash; on a welded pipe that costs one extra
weld and nothing else.</p>

<div class="callout c-good"><b>The trade, stated in full.</b> Going from a 3.0&nbsp;inch cold
side to a 2.5&nbsp;inch one:
<div class="scroll" style="margin-top:8px"><table>
<thead><tr><th>What changes</th><th class="num">Direction and size</th><th>What it is worth</th></tr></thead>
<tbody>
<tr style="background:rgba(255,107,107,.07)"><td>Cold-side pressure drop</td>
<td class="num" style="color:#ff8f8f">worse by 0.34 psi</td>
<td>Raises the required pressure ratio from 3.410 to 3.436, which raises the compressor
outlet by <b>1.3&nbsp;&deg;C</b>. After a core with &epsilon;&nbsp;0.793 that is
<b>0.28&nbsp;&deg;C</b> at the intake valve, or about <b>0.1&nbsp;whp</b>.</td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Charge system volume</td>
<td class="num" style="color:#4fe0aa">better by 1.79 L</td>
<td>14.0&nbsp;L instead of 15.8&nbsp;L. 6.4&times; displacement instead of 7.2&times;.</td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Boost fill time</td>
<td class="num" style="color:#4fe0aa">better by 25 ms</td>
<td>191&nbsp;ms instead of 216&nbsp;ms at a 0.15&nbsp;kg/s ramp. Right at the edge of what a
driver can detect, and in the direction you want.</td></tr>
<tr style="background:rgba(56,211,159,.07)"><td>Corner room at every bend</td>
<td class="num" style="color:#4fe0aa">better by 25 mm</td>
<td>A 127&nbsp;mm bend box instead of 152&nbsp;mm. This is the one that decides whether the
pipe fits.</td></tr>
<tr><td>Extra welds</td><td class="num">one</td>
<td>The 2.5&nbsp;&rarr;&nbsp;3.0&nbsp;in cone at the throttle adapter. No extra clamped
joint.</td></tr>
</tbody></table></div>
<b>You are paying 0.1 whp for 25 mm of clearance at every corner and 25 ms of throttle
response. Take it.</b></div>

<div class="rec"><h3>Cold side: 2.5 in, with a welded cone to 3.0 in at the throttle</h3>
<div class="specline"><span class="k">Diameter</span><span class="v"><b>2.5 in OD mandrel alloy, 0.065 in wall &mdash; 60.2 mm real bore</b>, for 1.35 m of the 1.5 m run</span></div>
<div class="specline"><span class="k">Last 150 mm</span><span class="v">Welded cone 2.5 &rarr; 3.0 in at &le;7&deg; per wall, then 150 mm of 3.0 in tube into the bought HD clamp adapter</span></div>
<div class="specline"><span class="k">Taper length needed</span><span class="v">52 mm minimum at 7&deg; per wall. You have 150 mm, so make it gradual.</span></div>
<div class="specline"><span class="k">Velocity there</span><span class="v">145 ft/s (44 m/s), Mach 0.119 &mdash; well under any loss knee</span></div>
<div class="specline"><span class="k">Pressure drop</span><span class="v">0.591 psi including the cone</span></div>
<div class="specline"><span class="k">Intercooler port</span><span class="v"><b>Weld 2.5 in ports on the fabricated tanks.</b> See &sect;10.8 &mdash; this is a free choice and it removes the only other 3 in constraint.</span></div>
<div class="specline"><span class="k">Clamped joints</span><span class="v">Two on this side: the intercooler and the throttle adapter. Everything between is welded.</span></div>
</div>

<h3>10.8 &nbsp;The intercooler's own ports &mdash; checked, because they could have forced 3 inch</h3>
<p class="note">If the intercooler shipped with 3&nbsp;inch ports, the cold side would have
3&nbsp;inch hardware at <i>both</i> ends and the case for a 2.5&nbsp;inch run would weaken.
Every assembled unit surveyed in &sect;19.1 was checked.</p>
<div class="scroll"><table>
<thead><tr><th>Option</th><th class="num">Core size</th><th class="num">Ports</th><th>Consequence</th></tr></thead>
<tbody>
<tr><td>SpeedFactory SS-850, SKU SF-06-089</td><td class="num">24 &times; 12 &times; 3.0 in</td>
<td class="num">3.0 / 3.0 in</td>
<td>3 in only. Confirmed on the vendor listing &mdash; there is no 2.5 in variant of this
core.</td></tr>
<tr><td>SpeedFactory HPX</td><td class="num">24 &times; 12 &times; 4.5 in</td>
<td class="num">3.0 / 3.5 in</td><td>Mismatched, and 3 in minimum.</td></tr>
<tr><td>Treadstone TR1245</td><td class="num">22 &times; 12.5 &times; 4.5 in</td>
<td class="num">3.0 / 3.0 in</td><td>3 in only.</td></tr>
<tr><td>SpeedFactory "Street", SKU SF-06-082</td><td class="num">22 &times; 9 &times; 3.0 in</td>
<td class="num">2.5 / 2.5 in</td>
<td><span class="pill p-bad">Too small.</span> It is a 2.5 in unit, but the core is
9&nbsp;in tall and rated 300&ndash;500 hp. It does not solve the problem.</td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>Bare core plus fabricated tanks</b>
<span class="pill p-ok">what &sect;08 and &sect;14 already specify</span></td>
<td class="num">610 &times; 305 &times; 102 mm</td>
<td class="num"><b>whatever you weld on</b></td>
<td><b>The port is a free choice.</b> Weld 2.5 in and the cold side is a single diameter from
the intercooler to the cone at the throttle.</td></tr>
</tbody></table></div>

<div class="callout c-warn"><b>The one case where this flips.</b> If the aperture measurement
in &sect;13 forces you into a buying an assembled unit rather than fabricating tanks, you get
3&nbsp;inch ports whether you want them or not. In that case run <b>3.0&nbsp;inch cold</b>
&mdash; not because 3 inch is better, but because a 3&nbsp;&rarr;&nbsp;2.5&nbsp;&rarr;&nbsp;3
sandwich buys nothing and the routing problem is then yours to solve with bend placement
instead of diameter. <b>The recommendation is conditional on fabricating your own tanks, and
that is the plan of record.</b></div>

"""
swap(old104, new104, "10.4-10.8 rewrite")

# ============================================================ 10.5 old -> 10.9
swap("<h3>10.5 &nbsp;Hot side &mdash; chosen independently</h3>",
     "<h3>10.9 &nbsp;Hot side &mdash; chosen independently</h3>", "renumber 10.5")
swap("""<div class="rec"><h3>Hot side: 2.5 in</h3>""",
     """<div class="rec"><h3>Hot side: 2.5 in &mdash; and now it matches the cold side</h3>""",
     "hot side heading")
swap("""<div class="specline"><span class="k">Parts commonality</span><span class="v">2.5 in is also the EFR's compressor <i>inlet</i> size, so couplers, clamps and spares are shared with the intake side</span></div>""",
     """<div class="specline"><span class="k">Parts commonality</span><span class="v">2.5 in is also the EFR's compressor <i>inlet</i> size and now the cold side too, so tube stock, bends, couplers and clamps are shared across the whole car</span></div>""",
     "hot side commonality")

# ============================================================ 10.6 old -> 10.10
swap("<h3>10.6 &nbsp;So you are mixing diameters. Round three said not to.</h3>",
     "<h3>10.10 &nbsp;Mixing diameters &mdash; where this ended up</h3>", "renumber 10.6")
old_mix = cut('<div class="callout c-warn"><b>Round three said "2.5 inch both sides. Do not mix." That',
              "<h3>10.7 &nbsp;System volume and throttle response</h3>")
new_mix = r"""<div class="callout c-good"><b>Round three said "2.5 inch both sides. Do not mix."
Round four's first pass overturned that. This pass puts it back &mdash; and the round trip is
worth showing, because it is a good example of a recommendation being driven by an assumption
rather than by physics.</b>
<div class="scroll" style="margin-top:8px"><table>
<thead><tr><th>Claim</th><th>Status</th><th>Why</th></tr></thead>
<tbody>
<tr><td>"Run a bigger cold side because cold air is denser and flows better"</td>
<td><span class="pill p-bad">Wrong</span></td>
<td>The mass flow is identical on both sides. Denser air moves <i>slower</i> through the same
pipe, so if anything the cold side needs <i>less</i> area, not more. At 2.5&nbsp;in the hot
side runs 201&nbsp;ft/s and the cold side 145.</td></tr>
<tr><td>"Run a smaller hot side to keep velocity up for spool"</td>
<td><span class="pill p-bad">Wrong</span></td>
<td>Velocity in the charge pipe does nothing for spool. Pressure drop upstream of the
intercooler <i>hurts</i> spool, because the compressor has to make it up.</td></tr>
<tr><td>"The bought 3 inch adapter forces a 3 inch cold side"</td>
<td><span class="pill p-bad">Wrong, and it was mine</span></td>
<td>The first pass of round four concluded this. It rested on two assumptions that turned out
to be false: that a diameter change costs a clamped joint (it does not, on a welded pipe), and
that the intercooler port would also be 3&nbsp;inch (it is whatever you weld on). <b>The
adapter fixes 150&nbsp;mm of pipe, not 1,500&nbsp;mm.</b></td></tr>
<tr style="background:rgba(56,211,159,.10)"><td><b>"Size each side for its own duty, then let
the hardware set the last 150 mm"</b></td><td><span class="pill p-ok">This is the answer</span></td>
<td>Hot side 2.5&nbsp;in because 201&nbsp;ft/s is inside Garrett's band and it routes past the
turbine housing. Cold side 2.5&nbsp;in because the &Delta;P penalty is 0.1&nbsp;whp and the
routing gain is 25&nbsp;mm at every corner. They land on the same number for different
reasons, which is convenient rather than meaningful.</td></tr>
</tbody></table></div>
<b>So: a single 2.5 inch diameter for the whole system, with one welded cone in the last
150 mm.</b> That is what round three said, arrived at through a different argument, and with
the throttle-body transition now sized against a real 74.5&nbsp;mm bore instead of a guessed
74&nbsp;mm one.</div>

"""
swap(old_mix, new_mix, "10.10 mixing")

# ============================================================ 10.7 old -> 10.11
swap("<h3>10.7 &nbsp;System volume and throttle response</h3>",
     "<h3>10.11 &nbsp;System volume and throttle response</h3>", "renumber 10.7")
swap(r"""<div class="eq">System volume, the recommended 2.5 in hot / 3.0 in cold build:
  hot pipe   1.1 m &times; 2.85 L/m  =   3.13 L    <span class="cm">2.5 in OD, 60.2 mm bore</span>
  cold pipe  1.5 m &times; 4.17 L/m  =   6.26 L    <span class="cm">3.0 in OD, 72.9 mm bore</span>
  core internal, 19.0 L envelope at ~28% void  =   5.32 L
  end tanks  2 &times; 0.55 L        =   1.10 L
  <span class="cm">-----------------------------------------------</span>
  TOTAL                          =  <b>15.81 L</b>   <span class="cm">= 7.22 x engine displacement</span>
                                                <span class="cm">round three reported 9.05 L, which was wrong</span>

Fill time to 30 psi, at a 0.15 kg/s spool-up flow, section by section
at that section's own density:      <b>216 ms</b>
  same build with a 2.5 in cold side:  194 ms      <span class="cm">22 ms quicker, 0.44 psi worse</span></div>""",
     r"""<div class="eq">System volume, the recommended 2.5 in hot / 2.5 in cold build:
  hot pipe   1.10 m &times; 2.85 L/m  =   3.13 L    <span class="cm">2.5 in OD, 60.2 mm real bore</span>
  cold pipe  1.35 m &times; 2.85 L/m  =   3.85 L    <span class="cm">2.5 in OD, 60.2 mm real bore</span>
  cold tail  0.15 m &times; 4.17 L/m  =   0.63 L    <span class="cm">3.0 in OD into the bought adapter</span>
  core internal, 19.0 L envelope at ~28% void  =   5.32 L
  end tanks  2 &times; 0.55 L         =   1.10 L
  <span class="cm">-----------------------------------------------</span>
  TOTAL                           =  <b>14.01 L</b>   <span class="cm">= 6.40 x engine displacement</span>
                                                 <span class="cm">round three reported 9.05 L, which was wrong by half</span>

Fill time to 30 psi, at a 0.15 kg/s spool-up flow, section by section
at that section's own density:       <b>191 ms</b>
  the same build with a 3.0 in cold side: 216 ms   <span class="cm">25 ms slower, 0.34 psi better</span>
  a 2.25 in cold side:                    180 ms   <span class="cm">11 ms quicker, but 181 ft/s and 0.97 psi</span></div>""",
     "10.11 volume eq")
swap("""<p class="note">7.2&times; displacement is above the 3&ndash;5&times; figure usually quoted
as comfortable for a front-mount, and above the 6&times; figure usually quoted as the point
where lag becomes noticeable.""",
     """<p class="note">6.4&times; displacement is above the 3&ndash;5&times; figure usually
quoted as comfortable for a front-mount, and just above the 6&times; figure usually quoted as
the point where lag becomes noticeable.""",
     "10.11 volume note")

# ============================================================ 10.8 old -> 10.12
swap("<h3>10.8 &nbsp;Bends and routing</h3>", "<h3>10.12 &nbsp;Bends and routing</h3>",
     "renumber 10.8")
swap("""<li><b>Bend radius R/D &ge; 1.5.</b> For 3.0 in cold pipe that is a 114 mm centreline radius
minimum; for 2.5 in hot pipe, 95 mm.</li>""",
     """<li><b>Bend radius R/D &ge; 1.5.</b> For 2.5 in pipe that is a <b>95 mm centreline
radius</b> minimum, and the bend then occupies a <b>127 mm corner box</b>. Mock the tight
corners up in cardboard tube at that size before you order bends.</li>
<li><b>Three clamped joints, no more.</b> Intercooler, throttle body, and one alignment joint.
Every other transition is welded. Each clamped joint you delete removes about 18 mm from the
pipe's envelope at that point and one potential boost leak.</li>
<li><b>Put the alignment joint where you can reach it</b> &mdash; not behind the engine, and
not where the core has to come out past it.</li>""",
     "10.12 bends")
swap("""<li><b>Blow-off valve on the cold side</b>, as close to the throttle as practical, so it
vents the whole 15.8&nbsp;L on lift. With a system this large that placement matters more
than it would on a smaller one.</li>""",
     """<li><b>Blow-off valve on the cold side</b>, as close to the throttle as practical, so
it vents the whole 14.0&nbsp;L on lift. That is a weld-on bung, not a clamped joint.</li>""",
     "10.12 bov")

io.open(SRC, "w", encoding="utf-8").write(h)
print("applied %d edits" % len(done))
for d in done:
    print("  -", d)
print("size %d -> %d" % (n0, len(h)))
