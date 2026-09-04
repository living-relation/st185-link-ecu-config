# -*- coding: utf-8 -*-
"""Round four, part four: JS table builders for the revised charge-pipe section,
plus the remaining prose that quoted the withdrawn 3.0 in cold-side figures.
Patches r4_charts.js and the copy embedded in intercooler-report.html identically."""
import os, io

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "intercooler-report.html")
JS = os.path.join(HERE, "r4_charts.js")

# ---------------------------------------------------------------- JS edits
OLD_COLD = '''/* ---------- table: cold layouts ---------- */
function fillR4Cold(){
  var b=r4Body("t-r4cold"); if(!b) return;
  b.innerHTML = R4.coldLayouts.map(function(r){
    var rec = r.lab.indexOf("3.00 in the whole")===0;
    return '<tr'+(rec?' style="background:rgba(56,211,159,.10)"':'')+'>'
      +'<td>'+(rec?'<b>'+r.lab+'</b> <span class="pill p-ok">recommended</span>':r.lab)+'</td>'
      +'<td class="num">'+r.vmax+' ft/s</td>'
      +'<td class="num">'+r4Num(r.dp,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.vol,2)+' L</td>'
      +'<td class="num">'+r4Num(r.sysL,2)+' L</td>'
      +'<td class="num">'+r4Num(r.sysX,2)+'&times;</td>'
      +'<td class="num">'+r.fill_ms+' ms</td></tr>';
  }).join("");
}'''

NEW_COLD = '''/* ---------- table: cold layouts ---------- */
function fillR4Cold(){
  var b=r4Body("t-r4cold"); if(!b) return;
  var rows=R4.coldLayouts.slice().sort(function(a,c){return a.box-c.box;});
  b.innerHTML = rows.map(function(r){
    var rec = r.lab.indexOf("2.50 in run")===0;
    var tight = r.lab.indexOf("2.25 in run")===0;
    var big = r.lab.indexOf("3.00 in the whole")===0;
    var bg = rec ? ' style="background:rgba(56,211,159,.10)"'
           : (big ? ' style="background:rgba(255,179,71,.07)"' : '');
    var tag = rec ? ' <span class="pill p-ok">recommended</span>'
            : (big ? ' <span class="pill p-warn">will not route</span>'
            : (tight ? ' <span class="pill p-warn">181 ft/s, 0.97 psi</span>' : ''));
    return '<tr'+bg+'><td>'+(rec?'<b>'+r.lab+'</b>':r.lab)+tag+'</td>'
      +'<td class="num">'+r.vmax+' ft/s</td>'
      +'<td class="num">'+r4Num(r.dp,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.vol,2)+' L</td>'
      +'<td class="num">'+r4Num(r.sysL,2)+' L</td>'
      +'<td class="num">'+r4Num(r.sysX,2)+'&times;</td>'
      +'<td class="num">'+r.fill_ms+' ms</td>'
      +'<td class="num">'+r.box+' mm</td></tr>';
  }).join("");
}

/* ---------- table: velocity and dP at real inside diameters ---------- */
function fillR4Pipes(){
  var b=r4Body("t-r4pipes"); if(!b) return;
  b.innerHTML = R4.pipes.map(function(r){
    var rec = (r.od===2.50);
    var note = "";
    if(r.od===2.00) note=" <span class=\\"note\\">too small &mdash; 1.67 psi on the hot side alone</span>";
    if(r.od===3.00) note=" <span class=\\"note\\">lowest loss, largest to route</span>";
    return '<tr'+(rec?' style="background:rgba(56,211,159,.10)"':'')+'>'
      +'<td class="num">'+(rec?'<b>'+r.od.toFixed(2)+' in</b>':r.od.toFixed(2)+' in')+note+'</td>'
      +'<td class="num"><b>'+r4Num(r.id_mm,1)+' mm</b></td>'
      +'<td class="num">'+r.hot_fts+' ft/s <span class="note">M '+r4Num(r.hot_mach,3)+'</span></td>'
      +'<td class="num">'+r4Num(r.hot_dp,3)+' psi</td>'
      +'<td class="num">'+r.cold_fts+' ft/s <span class="note">M '+r4Num(r.cold_mach,3)+'</span></td>'
      +'<td class="num">'+r4Num(r.cold_dp,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.vol_per_m,2)+' L/m</td></tr>';
  }).join("");
}

/* ---------- table: routing envelope ---------- */
function fillR4Route(){
  var b=r4Body("t-r4route"); if(!b) return;
  b.innerHTML = R4.routing.map(function(r){
    var rec = (r.od===2.50);
    return '<tr'+(rec?' style="background:rgba(56,211,159,.10)"':'')+'>'
      +'<td class="num">'+(rec?'<b>'+r.od.toFixed(2)+' in</b>':r.od.toFixed(2)+' in')+'</td>'
      +'<td class="num">'+r4Num(r.id_mm,1)+' mm</td>'
      +'<td class="num">'+r4Num(r.bare,1)+' mm</td>'
      +'<td class="num">'+r4Num(r.clamped,1)+' mm</td>'
      +'<td class="num">'+r.clr+' mm</td>'
      +'<td class="num"><b>'+r.box+' mm</b></td></tr>';
  }).join("");
}'''

OLD_JOBS = ('["fillR4Tb",fillR4Tb],["fillR4Cold",fillR4Cold],["fillR4Hot",fillR4Hot],')
NEW_JOBS = ('["fillR4Tb",fillR4Tb],["fillR4Cold",fillR4Cold],["fillR4Hot",fillR4Hot],\n'
            '            ["fillR4Pipes",fillR4Pipes],["fillR4Route",fillR4Route],')

# hot-side note table: 2.50 is now the same as the cold side
OLD_HOTNOTE = ('2.50:"Recommended. Bottom of the band, and it matches the compressor '
               'inlet size.",')
NEW_HOTNOTE = ('2.50:"Recommended. Bottom of the band, matches the compressor inlet AND '
               'the cold side, so one tube stock for the whole car.",')

for path in (JS, SRC):
    s = io.open(path, encoding="utf-8").read()
    n0 = len(s)
    for old, new, lab in ((OLD_COLD, NEW_COLD, "cold+pipes+route builders"),
                          (OLD_JOBS, NEW_JOBS, "job list")):
        assert old in s, "MISSING in %s: %s" % (os.path.basename(path), lab)
        s = s.replace(old, new, 1)
    # the hot-side note exists in two forms depending on whether the 2.25 in-band
    # fix has already been applied to that copy
    hot_variants = [OLD_HOTNOTE,
                    '2.50:"Recommended. In the band, and it matches the compressor '
                    'inlet size.",']
    if not any(v in s for v in hot_variants):
        raise AssertionError("MISSING in %s: hot note" % os.path.basename(path))
    for v in hot_variants:
        if v in s:
            s = s.replace(v, NEW_HOTNOTE, 1)
            break
    io.open(path, "w", encoding="utf-8").write(s)
    print("patched %-26s %d -> %d" % (os.path.basename(path), n0, len(s)))

# ---------------------------------------------------------------- prose edits
h = io.open(SRC, encoding="utf-8").read()
n0 = len(h)
done = []


def swap(old, new, label):
    global h
    assert old in h, "MISSING ANCHOR: " + label
    h = h.replace(old, new, 1)
    done.append(label)


# ---- exec summary
swap('<b>(5)</b> The <b>charge pipe is no longer a decision</b>. The bought throttle adapter is\n'
     '3.0&nbsp;inch, so the cold side is 3.0&nbsp;in and the hot side is 2.5&nbsp;in.\n'
     '<a href="#pipes">&sect;10</a></div>',
     '<b>(5)</b> The <b>charge pipe is 2.5&nbsp;inch on both sides</b>, with one welded cone up '
     'to 3.0&nbsp;inch over the last 150&nbsp;mm to meet the throttle adapter Dan already owns. '
     'Routing clearance decides this, not pressure drop: 3.0&nbsp;inch needs 25&nbsp;mm more '
     'corner room at every bend, and the pressure-drop penalty for 2.5&nbsp;inch is worth '
     '<b>0.1&nbsp;whp</b>. <a href="#pipes">&sect;10</a></div>',
     "exec item 5")

swap('run\n<b>2.5&nbsp;inch hot-side and 3.0&nbsp;inch cold-side piping</b> into the 3&nbsp;inch throttle\n'
     'adapter you already own,',
     'run\n<b>2.5&nbsp;inch piping on both sides</b> with a welded cone into the 3&nbsp;inch '
     'throttle adapter you already own,',
     "exec lede pipes")

swap('<div class="specline"><span class="k">Cold-side pipe</span><span class="v"><b>3.0&nbsp;in OD '
     'the whole run</b> <span class="note">&mdash; fixed by the bought 3 in throttle adapter. '
     '&sect;10</span></span></div>',
     '<div class="specline"><span class="k">Cold-side pipe</span><span class="v"><b>2.5&nbsp;in OD '
     '(60.2&nbsp;mm real bore)</b>, welded cone to 3.0&nbsp;in over the last 150&nbsp;mm '
     '<span class="note">&mdash; 145 ft/s. &sect;10</span></span></div>\n'
     '<div class="specline"><span class="k">Intercooler ports</span><span class="v">'
     '<b>Weld 2.5&nbsp;in ports</b> on the fabricated tanks <span class="note">&mdash; a free '
     'choice, and it keeps one diameter end to end. &sect;10.8</span></span></div>',
     "spec cold pipe")

swap('<div class="specline"><span class="k">Predicted total &Delta;P</span><span class="v">'
     '<b>1.41&nbsp;psi</b> (4.7% of 30&nbsp;psi boost) <span class="note">&mdash; itemised in '
     '&sect;10.7</span></span></div>\n'
     '<div class="specline"><span class="k">Charge system volume</span><span class="v">15.8&nbsp;L, '
     '7.2&times; displacement, 216&nbsp;ms fill <span class="note">&mdash; round three said 9.1 L '
     'and was wrong</span></span></div>',
     '<div class="specline"><span class="k">Predicted total &Delta;P</span><span class="v">'
     '<b>1.76&nbsp;psi</b> (5.9% of 30&nbsp;psi boost) <span class="note">&mdash; itemised in '
     '&sect;11</span></span></div>\n'
     '<div class="specline"><span class="k">Charge system volume</span><span class="v">14.0&nbsp;L, '
     '6.4&times; displacement, 191&nbsp;ms fill <span class="note">&mdash; round three said 9.1 L '
     'and was wrong by half</span></span></div>',
     "spec dP and volume")

swap('<div class="kpi"><div class="lab">Total pressure drop</div><div class="val g">1.41</div>\n'
     '<div class="note">psi &mdash; 4.7% of boost. Throttle body contributes 0.047. &sect;10.7</div></div>',
     '<div class="kpi"><div class="lab">Total pressure drop</div><div class="val g">1.76</div>\n'
     '<div class="note">psi &mdash; 5.9% of boost. Throttle body contributes 0.047. &sect;11</div></div>',
     "kpi dP")

swap('<tr><td>Pipe diameter, mix or not</td><td><b>2.5&nbsp;in hot, 3.0&nbsp;in cold</b>'
     '<br><span class="note">changed in round four &mdash; the hardware decides it</span></td>',
     '<tr><td>Pipe diameter, mix or not</td><td><b>2.5&nbsp;in both sides</b>'
     '<br><span class="note">round three\'s answer, reached by a better route. &sect;10.10</span></td>',
     "decision table pipes")

# ---- section 11
swap('<p class="lede">Target: <b>&le; 1.5 psi total at peak flow</b>. The round-four build &mdash; '
     '2.5&nbsp;in hot, 3.0&nbsp;in cold, 610&times;305&times;102 core, 74.5&nbsp;mm throttle '
     '&mdash; comes to <b>1.41 psi</b>, which is 4.7% of 30 psi boost. Itemised in '
     '<a href="#pipes">&sect;10.7</a>.</p>\n'
     '<div class="callout c-info"><b>Round-four itemisation, replacing the four tiles below.</b> '
     'Hot pipe 2.5 in <b>0.586</b> &middot; core <b>0.180</b> &middot; end tanks <b>0.350</b> '
     '&middot; cold pipe 3.0 in <b>0.247</b> &middot; throttle body <b>0.047</b> &middot; the two '
     '1.7 mm steps <b>0.004</b> &nbsp;=&nbsp; <b>1.413 psi</b>. The hot side is now the largest '
     'single term, at 41% of the total, because it carries the least dense air.</div>',
     '<p class="lede">The round-four build &mdash; 2.5&nbsp;in hot, 2.5&nbsp;in cold with a welded '
     'cone to 3.0&nbsp;in at the throttle, 610&times;305&times;102 core, 74.5&nbsp;mm throttle '
     '&mdash; comes to <b>1.76 psi</b>, which is 5.9% of 30 psi boost.</p>\n'
     '<div class="callout c-info"><b>Round-four itemisation, replacing the four tiles below.</b>\n'
     'Hot pipe 2.5 in <b>0.586</b> &middot; core <b>0.180</b> &middot; end tanks <b>0.350</b> '
     '&middot; cold pipe 2.5 in <b>0.547</b> &middot; the welded cone and 3.0 in tail '
     '<b>0.044</b> &middot; throttle body <b>0.047</b> &middot; the two 1.7 mm steps at the '
     'throttle <b>0.004</b> &nbsp;=&nbsp; <b>1.757 psi</b>.<br><br>'
     '<b>The 1.5 psi "target" was always a rule of thumb, not a limit, and it is worth saying '
     'what exceeding it actually costs.</b> Going from 1.41 psi to 1.76 psi raises the required '
     'pressure ratio from 3.410 to 3.436, the compressor outlet by <b>1.3&nbsp;&deg;C</b>, the '
     'charge at the intake valve by <b>0.28&nbsp;&deg;C</b>, and the power by about '
     '<b>0.1&nbsp;whp</b>. The two pipes are 64% of the total because they carry the whole flow '
     'over the longest distance &mdash; not because either is undersized.</div>',
     "section 11 lede")

swap('<div class="kpi"><div class="lab">Cold pipe, 3.0 in</div><div class="val g">0.25</div>'
     '<div class="note">psi &mdash; 1.5 m, 4 bends. Round four.</div></div>',
     '<div class="kpi"><div class="lab">Cold pipe, 2.5 in</div><div class="val">0.55</div>'
     '<div class="note">psi &mdash; 1.35 m, 4 bends, plus 0.044 for the cone and tail</div></div>',
     "section 11 kpi cold")

swap('<b>core is nearly the smallest contributor</b> &mdash; about 13% of total loss. The piping and '
     'end tanks together account for ~84%, and the throttle body is 3%.',
     '<b>core is nearly the smallest contributor</b> &mdash; about 10% of total loss. The piping '
     'and end tanks together account for ~87%, and the throttle body is under 3%.',
     "section 11 callout")

# ---- section 14
swap('<div class="specline"><span class="k">Cold pipe</span><span class="v"><b>3.0 in mandrel alloy, '
     'whole run</b><br>straight into the bought 3 in hose adapter &mdash; no taper needed<br>'
     'BOV mounted close to the throttle</span></div>',
     '<div class="specline"><span class="k">Cold pipe</span><span class="v"><b>2.5 in mandrel alloy, '
     '0.065 in wall</b><br>welded cone 2.5 &rarr; 3.0 in over the last 150 mm into the bought '
     'hose adapter<br>BOV bung welded close to the throttle</span></div>\n'
     '<div class="specline"><span class="k">Joints</span><span class="v">Fully welded. HD clamps at '
     'three places only:<br>intercooler, throttle body, one alignment joint</span></div>',
     "final spec cold pipe")
swap('<div class="specline"><span class="k">Port placement</span><span class="v">Inlet bottom-left corner<br>'
     'Outlet top-right corner (diagonal)</span></div>',
     '<div class="specline"><span class="k">Port placement</span><span class="v">Inlet bottom-left corner<br>'
     'Outlet top-right corner (diagonal)<br><b>2.5 in ports, both</b> &mdash; &sect;10.8</span></div>',
     "final spec ports")
swap('<div class="kpi"><div class="lab">Predicted total &Delta;P</div><div class="val">1.41</div>'
     '<div class="note">psi &mdash; 4.7% of 30 psi boost</div></div>',
     '<div class="kpi"><div class="lab">Predicted total &Delta;P</div><div class="val">1.76</div>'
     '<div class="note">psi &mdash; 5.9% of 30 psi boost</div></div>',
     "final spec kpi dp")

# ---- section 23 change table
swap('<td>Closes the open question about the stock Gen 2 plenum. Charge-pipe recommendation\n'
     're-run against the real hardware. &sect;10 rewritten. The pipe diameter at the throttle is\n'
     'no longer a choice.</td>\n'
     '<td class="num"><b>0 whp</b><br><span class="note">it removes a risk, it does not add\n'
     'power. Cold pipe changes from 2.5 in to 3.0 in.</span></td></tr>',
     '<td>Closes the open question about the stock Gen 2 plenum. Charge-pipe recommendation '
     're-run against the real hardware and against routing clearance. &sect;10 rewritten. The '
     'throttle bore is 74.5&nbsp;mm, not 74; the bought adapter fixes the last 150&nbsp;mm at '
     '3.0&nbsp;in; the runs stay at 2.5&nbsp;in.</td>\n'
     '<td class="num"><b>0 whp</b><br><span class="note">it removes a risk, it does not add '
     'power. The pipe recommendation ends up where round three had it, for better reasons. '
     '&sect;10.10</span></td></tr>',
     "S23 item 2")

# ---- section 31 closed items
swap('<li><s>What pipe diameter into the throttle body?</s> &mdash; 3.0 in. The bought adapter decides\n'
     'it. &sect;10.4</li>',
     '<li><s>What pipe diameter for the charge pipes?</s> &mdash; <b>2.5 in both sides</b>, with a '
     'welded cone to 3.0 in over the last 150 mm into the bought adapter. Routing clearance '
     'decides it; the pressure-drop penalty is 0.1 whp. &sect;10.7</li>\n'
     '<li><s>Do the intercooler ports force a 3 in cold side?</s> &mdash; no. The tanks are '
     'fabricated, so the port is whatever you weld on. Weld 2.5 in. &sect;10.8</li>',
     "S31 closed pipe")

io.open(SRC, "w", encoding="utf-8").write(h)
print("applied %d prose edits" % len(done))
for d in done:
    print("  -", d)
print("size %d -> %d" % (n0, len(h)))
