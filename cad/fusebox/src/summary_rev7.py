"""Build cad/fusebox/rev7/ST185-fusebox-rev7-summary.html: Dan's E2 = A option side by side with rev 6 - what moved, the
wire-count change, the whole power distribution package (R84) for both revs, the rev 7 renders, the bus zone terminals,
the checks, the cut / drill list for the two copper bus bars and the rev 7 POWER parts list. Reads spec.py REV7, the rev 7
build's fusebox_report.json and the parts lists. Rev 7 is selected for build (Dan's P7 = A, U1 = A, DECISIONS R91).
The "More views" section shows the side views and the typical arrangement (render-only, cad/fusebox/rev7/*side* / *arrangement*).
    python cad/fusebox/src/summary_rev7.py
Claude Code, 2026-10-14.
"""
import os, sys, json, html
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S
import parts_lists as PL

FB = os.path.dirname(HERE)
D7 = os.path.join(FB, 'rev7')
OUT = os.path.join(D7, 'ST185-fusebox-rev7-summary.html')
rep = json.load(open(os.path.join(D7, 'fusebox_report.json')))
plan = json.load(open(os.path.join(D7, 'wiring_plan.json')))
wrep = json.load(open(os.path.join(D7, 'wiring_report.json')))
# the rev 7 build before Dan's 3 mm fix (PR #214, cad/fusebox/rev7/fusebox_report.json at that commit)
BEFORE = {'logic_strip_to_strip_mm': 3.8, 'logic_bolt_to_other_strip_min_mm': 0.68, 'logic_jumper_lug_to_lug_min_mm': 1.86,
          'logic_strip_to_printed_min_mm': 0.4, 'logic_jumper_parts_to_printed_min_mm': 0.6, 'logic_jumper_parts_to_harness_min_mm': 0.56,
          'pan_to_nearest_live_power_mm': 0.59}
rep6 = json.load(open(os.path.join(FB, 'fusebox_report.json')))
E = lambda s: html.escape(str(s))
R7 = S.REV7
MAIN = r'C:\projects\active\st185-link-ecu-config\cad'

rows6, rows7 = PL.build(6), PL.build(7)
tot6, tot7 = PL.totals(rows6), PL.totals(rows7)
pcs = lambda rs: sum(int(r['qty_need']) for r in rs)
b6, b7 = rep6['boxes_mm']['POWER'], rep['boxes_mm']['POWER']
live = rep['live_clearance']
callouts = rep.get('callouts', {})
pp6, pp7 = rep6['printed_parts'], rep['printed_parts']
n_pos = sum(1 for p in R7['pos_studs'] if p[1] != 'SPARE')
n_neg10 = sum(1 for n in R7['neg_studs'] if n[3] == '1/0')

CSS = """:root{--bg:#fafaf8;--fg:#1d1d1b;--mut:#666;--line:#ddd;--acc:#b35c00;--card:#fff;--ok:#2e7d32;--bad:#c62828}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#1b1b1a;--fg:#ecece8;--mut:#a0a09a;--line:#3a3a38;--acc:#f0a050;--card:#242423;--ok:#81c784;--bad:#ef9a9a}}
:root[data-theme=dark]{--bg:#1b1b1a;--fg:#ecece8;--mut:#a0a09a;--line:#3a3a38;--acc:#f0a050;--card:#242423;--ok:#81c784;--bad:#ef9a9a}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif;margin:0}
main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:24px;margin:8px 0 2px}h2{font-size:18px;margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
.mut{color:var(--mut)}table{border-collapse:collapse;width:100%;font-size:13.5px}
td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
.wrap{overflow-x:auto}figure{margin:12px 0}img{max-width:100%;border:1px solid var(--line);border-radius:6px;background:#888}
img.w{background:#fff}figcaption{color:var(--mut);font-size:13px}.kpi{display:flex;flex-wrap:wrap;gap:10px}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:150px}
.kpi b{display:block;font-size:20px}ol li,ul li{margin-bottom:6px}h3{font-size:15px;margin:18px 0 6px}a{color:var(--acc)}
.ok{color:var(--ok);font-weight:600}.bad{color:var(--bad);font-weight:600}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
ol.co{columns:2;column-gap:28px;font-size:13.5px;padding-left:22px}@media (max-width:640px){ol.co{columns:1}}
.note{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:6px;padding:8px 12px}
td.d{font-weight:700}"""

h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
     '<title>ST185 Fuse Box Rev 7</title><style>%s</style></head><body><main>' % CSS]
A = h.append


def fig(f, cap, cls=''):
    if not os.path.exists(os.path.join(D7, f)) and not os.path.exists(os.path.join(FB, f.replace('../', ''))):
        return
    A('<figure><img%s src="%s" alt="%s"><figcaption>%s</figcaption>' % (' class="%s"' % cls if cls else '', E(f), E(cap), E(cap)))
    if f in callouts:
        A('<ol class="co">%s</ol>' % ''.join('<li value="%d">%s</li>' % (n, E(t)) for (n, x, y, t) in sorted(callouts[f])))
    A('</figure>')


A('<h1>ST185 fuse boxes - rev 7 (selected for build)</h1>')
A('<p class="mut">Claude Code, 2026-10-14. Your E2 answer: "make a separate new version so I can see it". Rev 7 is that version, and you picked it: '
  '<b>P7 = A, U1 = A (DECISIONS R91)</b>. The POWER box below is selected for build. The LOGIC box is rebuilt here for your 3 mm rule '
  '(<a href="#clearance">3 mm fix</a>, R93); the battery relay block stays rev 6 (<a href="../ST185-fusebox-summary.html">rev 6 page</a>). '
  '<a href="#views">Every wire simulated: sides, exploded, underneath, routing, the boxes cabled together</a>. Open questions: J1-J4.</p>')
A('<div class="note"><b>The idea in one line:</b> the glove-box bus bar and the POWER box become one thing. The bus bar\'s + bar runs right '
  'through the POWER box and the AMI fuses bolt straight onto it. No second copper bar, no separate bus bar box, no thick cable between them.</div>')
A('<div class="kpi">')
A('<div>POWER box + bus bar<b>%.0f x %.0f x %.1f</b><span class="mut">mm L x D x H (rev 6 POWER: %.0f x %.0f x %.1f, plus the B rev3 bus bar 345 x 120 x 55)</span></div>'
  % (b7['L'], b7['D'], b7['H'], b6['L'], b6['D'], b6['H']))
A('<div>1/0 cables at the glove box<b>%d (rev 6: %d)</b><span class="mut">one fewer: the bus bar to POWER box link is gone</span></div>' % (n_pos + n_neg10, n_pos + n_neg10 + 1))
A('<div>Boxes in the glove box<b>2 (rev 6: 3)</b><span class="mut">POWER (with the bus) + LOGIC</span></div>')
A('<div>POWER parts<b>%d pcs, $%.0f</b><span class="mut">rev 6 POWER alone: %d pcs, $%.0f (B rev3 bus bar had no parts list)</span></div>'
  % (pcs(rows7['POWER']), tot7['POWER'], pcs(rows6['POWER']), tot6['POWER']))
A('</div>')

A('<h2>The whole power distribution package, rev 7 next to rev 6</h2>')
A('<p class="mut">Same camera, same scale idea, every member together (R84): POWER (+ bus), LOGIC, battery relay block, 2 x VRC, CSB3. '
  'Rev 6 has the separate B rev3 bus bar (the long box at the back).</p><div class="grid">')
fig('package-rev7.png', 'Rev 7: POWER box with the bus bar inside it, LOGIC box, battery relay block, 2 x VRC, CSB3.', 'w')
fig('../package-rev6.png', 'Rev 6 (superseded): the same plus the separate B rev3 bus bar and the 1/0 link cable to the POWER box.', 'w')
A('</div>')

A('<h2>Wire count against rev 6</h2><div class="wrap"><table><tr><th>Wire / cable</th><th>Rev 6</th><th>Rev 7</th><th>Change</th><th>Why</th></tr>')
WC = [
    ('1/0 cables landing at the glove box (H1 BAT+, H2 BAT-, H3 RADLOK+, H6a RADLOK-, H7 GND ID / IG)', 6, 6, 'same cables, now on M8 lugs in the POWER box bus zone'),
    ('1/0 link bus bar -> POWER box bar (ST185-CabinPower w_fb_in)', 1, 0, 'the + bar is the AMI bar now'),
    ('1/0 lug ends in the glove box', 8, 6, 'the link cable had a lug at each end'),
    ('Relay feeds, AMI IN row -> relay terminal 30', 6, 6, 'unchanged (they already bolt onto the bar)'),
    ('AMI OUT row harness cables', 6, 6, 'unchanged'),
    ('LOGIC feeds (BUS1 50 A, BUS2 k_efi 87)', 2, 2, 'unchanged'),
    ('Small relay grounds to the NEG bar (k_htr 87a, k_pwr 85, k_rev 85)', 3, 3, 'same 3 wires; the two POWER-box ones now end in the same box (shorter)'),
]
t6 = t7 = 0
for (what, a, b, why) in WC[:2] + WC[3:]:
    t6 += a
    t7 += b
for (what, a, b, why) in WC:
    d = b - a
    A('<tr><td>%s</td><td>%d</td><td>%d</td><td class="d">%s</td><td>%s</td></tr>' % (E(what), a, b, ('%+d' % d) if d else '0', E(why)))
A('<tr><td><b>Cables in total</b> (lug ends row not counted)</td><td><b>%d</b></td><td><b>%d</b></td><td class="d">%+d</td><td>one heavy 1/0 cable and its 2 lugs fewer</td></tr>'
  % (t6, t7, t7 - t6))
A('</table></div>')

A('<h2>What changed from rev 6</h2><ol>')
A('<li><b>No copper bar of its own in the POWER box.</b> The bus bar\'s + bar (POS) runs the whole length: 1" x 1/4" tinned copper, %d mm long (rev 6 POWER bar: %d). '
  'The 14 AMI positions bolt onto it exactly as in rev 6 (same pads, standoffs, relays, saddles, harness bundles).</li>' % (R7['bar_y1'] - S.BAR['y0'], S.BAR['y1'] - S.BAR['y0']))
A('<li><b>A bus zone at the back of the box</b> (+%d mm deep). On the + bar: BAT+ IN, RADLOK+ and a spare M8 - those cables leave straight out of the outboard end. '
  'Beside it a NEG bar (same stock, %d mm): BAT-, RADLOK-, GND ID, GND IG and one M8 for the small relay grounds - those leave straight out the back.</li>'
  % (R7['D'] - S.D, R7['neg_bar']['x1'] - R7['neg_bar']['x0']))
A('<li><b>A printed wall between NEG and POS</b> (2.5 mm, 20 mm above the deck). Closest NEG part to a POS part: <b>%.1f mm</b>, with the wall in between.</li>' % live['bus_neg_to_pos_min_mm'])
A('<li><b>B rev3 adapted to R76 (cut + drill only):</b> its machined aluminium bars and 1/0 set-screw port blocks become plain tinned copper bars with M8 '
  'bolts (head captured in the deck, like every other bolt) and Klauke 6R8 lugs. Its universal bar U and the link strap / AMG fuse option are dropped (question U1 below).</li>')
A('<li><b>Feet:</b> still four with M6 limiters; the rear-inboard foot moved round to the inboard end so no cable runs over a mounting bolt.</li>')
A('<li><b>Unchanged:</b> LOGIC box and battery relay block (their feeds do not move); bend radius rule, belly pan, PA12 print rules, M6 limiters, 40 mm standoffs.</li></ol>')

A('<h2>Rev 7 renders</h2>')
for f, cap in (('fusebox_render_iso_closed.png', 'Closed. The POWER box is 62 mm deeper; the bus terminals are etched on the lid.'),
               ('fusebox_render_iso_closed_rear.png', 'From the back: the four NEG cables + the small ground bundle leave the rear, BAT+ IN and RADLOK+ the outboard end.'),
               ('fusebox_render_iso_open.png', 'Covers off: the + bar runs from the AMI fuses into the bus zone; NEG bar on the left of the barrier wall.'),
               ('fusebox_render_top_lid_power.png', 'POWER lid, top view: rev 6 names + the bus terminals.'),
               ('fusebox_render_iso_empty.png', 'Empty: bars, pads, standoffs and the printed barrier.'),
               ('fusebox_render_top_empty.png', 'Empty, top view.'),
               ('fusebox_render_under_pan.png', 'Underneath with the belly pans.'),
               ('fusebox_render_under_open.png', 'Underneath, pans off.'),
               ('fusebox_render_routing_power.png', 'POWER box cables (numbered).'),
               ('fusebox_render_power_bends.png', 'Relay feed bends round their saddles (unchanged).'),
               ('fusebox_power_explode.png', 'Exploded: how it goes together.'),
               ('fusebox_power_step1.png', 'Step 1: bars, pads, bolts, standoffs.'),
               ('fusebox_power_step2.png', 'Step 2: harness terminals and the lugs under the deck.'),
               ('fusebox_power_step3.png', 'Step 3: fuses, relays, the 1/0 bus lugs on top.'),
               ('fusebox_power_step4.png', 'Step 4: belly pan and cover.')):
    fig(f, cap)
A('<div class="grid">')
fig('trimetric-power.png', 'Trimetric, POWER box rev 7 (R83).', 'w')
fig('trimetric-logic.png', 'Trimetric, LOGIC box rev 7 (3 mm fix: 81.5 wide).', 'w')
fig('../trimetric-battrelay.png', 'Trimetric, battery relay block (rev 6, unchanged in rev 7).', 'w')
A('</div>')

A('<h2 id="clearance">LOGIC: the 3 mm fix (Dan\'s rule)</h2>')
A('<p>Your question: do the bars under the LOGIC box touch? <b>No</b> - the Bus 1 and Bus 2 strips were 3.8 mm apart. But an M4 x 8 jumper bolt '
  'sticks 3.1 mm out of its own strip, so its tip was <b>0.68 mm</b> from the other strip. Fix, same parts: the Bus 2 fuse column and both micro relay '
  'columns sit 2.5 mm further outboard and the box is 2.5 mm wider (79 -&gt; 81.5). Bus 1 could not move inboard (its wire bundle meets the belly pan '
  'wall) and Bus 2 could not move alone (its fuses would hit the micro relays). A gate now fails any live-to-live gap under 3 mm '
  '(<code>cad/fusebox/src/check_clearance.py</code>, in <code>check_all.py</code>).</p>')
A('<div class="wrap"><table><tr><th>Gap</th><th>Before</th><th>Now</th><th>Kind</th></tr>')
for k, lbl, kind in (('logic_bolt_to_other_strip_min_mm', 'strip bolt tip to the OTHER strip', 'live to live (Bus 1 / Bus 2)'),
                     ('logic_bus1_to_bus2_min_mm', 'any Bus 1 part to any Bus 2 part', 'live to live'),
                     ('logic_strip_to_strip_mm', 'Bus 1 strip to Bus 2 strip', 'live to live'),
                     ('logic_jumper_lug_to_lug_min_mm', 'jumper lug to the next lug, same strip', 'live to live, one circuit - question J1'),
                     ('logic_strip_to_printed_min_mm', 'strip to its printed lips', 'live to plastic - question J2'),
                     ('logic_jumper_parts_to_printed_min_mm', 'jumper parts to the deck', 'live to plastic - J2'),
                     ('logic_jumper_parts_to_harness_min_mm', 'jumper parts to the CAD tail bundles', 'live to insulation - J2'),
                     ('pan_to_nearest_live_power_mm', 'POWER belly pan to the nearest live part', 'live to plastic - J2')):
    b_, n_ = BEFORE.get(k), live.get(k)
    ok = n_ is not None and n_ >= 3.0
    A('<tr><td>%s</td><td>%s</td><td class="%s">%s</td><td>%s</td></tr>' % (E(lbl), ('%.2f mm' % b_) if b_ is not None else 'not measured',
      'ok' if ok else ('mut' if 'J' in kind else 'bad'), ('%.2f mm' % n_) if n_ is not None else '-', E(kind)))
A('</table></div>')

A('<h2 id="views">Every wire in place (simulation)</h2>')
pb = plan['per_box_wire_ends']
A('<div class="note">Your question: "aren\'t there going to be more wires in these? can you simulate that?" Every harness wire that lands in a box '
  '(<code>ST185-CabinPower</code>, <code>-HeavyDC</code>, <code>-EngineRoom-C</code>), at its real cavity, with its real gauge (outside diameter), '
  'insulation colour, ident bands and terminal part, bundled into the exit it leaves by (the CAD lanes) with the bend rule: 3 x OD where it is '
  'tied into its bundle, 10 x OD free outside. <code>cad/fusebox/src/wiring_sim.py</code> plans it, <code>render_wired_rev7.py</code> draws and '
  'checks it in Fusion (not saved). Nothing in the design was changed for it.</div>')
A('<div class="kpi"><div>POWER<b>%d wire ends</b><span class="mut">%d drawn here + the CAD feeds, OUT row and 1/0</span></div>'
  '<div>LOGIC<b>%d wire ends</b><span class="mut">%d drawn here + the 2 feeds and 19 jumpers</span></div>'
  '<div>Battery relay block<b>%d wire ends</b><span class="mut">feed, jumper, pump + 2 coil wires</span></div></div>'
  % (pb['POWER'], wrep['wires_drawn']['POWER'], pb['LOGIC'], wrep['wires_drawn']['LOGIC'], pb['BATT']))
A('<h3>What the simulation found</h3><div class="wrap"><table><tr><th>Check</th><th>Result</th></tr>')
fits = all(x['fits'] for x in plan['exits'])
tight = min(plan['exits'], key=lambda x: (x['margin'] if x['margin'] is not None else 99))
A('<tr><td>Do all wires fit through the exits / notches?</td><td class="%s">%s</td></tr>' % ('ok' if fits else 'bad',
  ('yes - every exit. Tightest: %s exit at %.1f, %d wires, round bundle %.1f mm in a %.1f mm notch' % (tight['box'], tight['lane'], tight['wires'], tight['d'], tight['opening']))
  if fits else 'no - see the exit table'))
A('<tr><td>Does any wire block a fuse or relay from being pulled?</td><td class="%s">%s</td></tr>' % ('ok', 'no. (The only hits are the battery block HCR150 and '
  'its own cables: a screw-terminal relay, its terminal nuts come off before it lifts out.)' if all('HCR150' in x[0] for x in wrep['pull']) else E(wrep['pull'])))
A('<tr><td>Do the covers still close?</td><td class="%s">%s</td></tr>' % ('ok' if not wrep['cover'] else 'bad', 'yes - no wire touches a cover' if not wrep['cover'] else E(wrep['cover'])))
A('<tr><td>Wire through printed plastic</td><td class="%s">%s</td></tr>' % ('ok' if not wrep['through_printed'] else 'bad',
  'none' if not wrep['through_printed'] else '%d wires rub the LOGIC belly pan wall (the outboard relay column\'s 86 pins are 1 mm from it, as rev 6): %s - question J2'
  % (len(wrep['through_printed']), E(', '.join(sorted(set(x[0] for x in wrep['through_printed'])))))))
A('<tr><td>Wire insulation against bare live metal</td><td class="%s">%s</td></tr>' % ('ok' if not wrep['bare_metal_touch'] else 'bad',
  'none' if not wrep['bare_metal_touch'] else '%s pass %.2f mm from the Bus 1 strip bolt heads - question J2' % (E(', '.join(sorted(set(x[0] for x in wrep['bare_metal_touch'])))),
  min(x[2] for x in wrep['bare_metal_touch']))))
A('<tr><td>Live to live (3 mm rule)</td><td class="ok">no new bare metal in the simulation; the gate result above stands (only J1 open)</td></tr>')
A('<tr><td>Wire to wire</td><td>%d places where two modelled wires share space (they cross in the crowded LOGIC lanes and under the deck); '
  'insulated wires crossing is normal, so the 3 mm rule does not apply. Closest: %.2f mm</td></tr>' % (len(wrep['wire_wire']['overlaps']), wrep['wire_wire']['min_mm'] or 0.0))
A('<tr><td>Two wires crimped in one terminal</td><td class="bad">%s - question J3</td></tr>' % E('; '.join(
  '%s: %s mm2 in %s (max %s)' % (d['cavity'], d['mm2'], d['part'], d['range'][1]) for d in plan['doubles'] if d['over'])))
A('<tr><td>LOGIC wires that leave and come back in</td><td>%d (%s): Bus 1 fuse to a relay in the same box, the strips are in the way under the deck - question J4</td></tr>'
  % (len(plan['loops']), E(', '.join(plan['loops']))))
A('</table></div>')
A('<h3>Exits</h3><div class="wrap"><table><tr><th>Box</th><th>Exit (lane)</th><th>Wires (CAD drew)</th><th>Round bundle</th><th>Notch</th><th>Packed in the notch: top</th><th>Fits</th></tr>')
for x in plan['exits']:
    A('<tr><td>%s</td><td>%.1f</td><td>%d (%d)</td><td>%.1f mm</td><td>%.1f mm</td><td>z %.1f (deck %.1f)</td><td class="%s">%s</td></tr>' % (
      x['box'], x['lane'], x['wires'], x['cad_wires'], x['d'], x['opening'], x['stack_top'], x['deck'], 'ok' if x['fits'] else 'bad', 'yes' if x['fits'] else 'no'))
A('</table></div>')
A('<h3>Each box, wired</h3>')
for key, nm in (('power', 'POWER (rev 7)'), ('logic', 'LOGIC (rev 7)')):
    A('<div class="grid">')
    for f, cap in (('fusebox_%s_wired_side_long.png' % key, '%s, long side.' % nm), ('fusebox_%s_wired_side_end.png' % key, '%s, short end.' % nm),
                   ('fusebox_%s_wired_explode.png' % key, '%s, exploded (the wires stay with the base).' % nm), ('fusebox_%s_wired_under.png' % key, '%s, underneath, pan off.' % nm),
                   ('fusebox_%s_wired_routing.png' % key, '%s, wire routing seen from below.' % nm)):
        fig(f, cap)
    A('</div>')
A('<div class="grid">')
for f, cap in (('battrelay_wired_side_long.png', 'Battery relay block, long side.'), ('battrelay_wired_side_end.png', 'Battery relay block, short end.'),
               ('battrelay_wired_explode.png', 'Battery relay block, exploded.'), ('battrelay_wired_under.png', 'Battery relay block, underneath.'),
               ('battrelay_wired_routing.png', 'Battery relay block, wiring from below.')):
    fig(f, cap)
A('</div><h3>Typical arrangement, cabled together</h3>')
A('<p class="mut">The real mount spot in the glove box is still to be measured (Route 1), so the shelf and the trunk floor are stand-ins and the LOGIC box '
  'sits 55 mm inboard of its render spot (bend room for the POWER box tails). Cable directions follow the routes: H1 / H2 back along the RH sill, '
  'RADLOK + / - forward to the RH firewall, GND ID to the left kick, GND IG to the right kick; Bus 1 / Bus 2 and k_efi 86 box to box; the relay '
  'grounds (k_htr 87a, k_pwr 85, k_rev 85) round to the NEG bar ring; the rest of the tails forward in grey looms (CabinPower). 1/0 bends at 3 x OD with a '
  'P-clamp each side. Lugs: Klauke 6R8 (bus zone), 2R5 / 3R5MS (OUT row), 2R5 (LOGIC feeds), 1R6 (battery block) - the parts-list parts.</p>')
for f, cap in (('fusebox_arrangement_wired_glovebox.png', 'Glove box: POWER (rev 7) + LOGIC cabled together.'),
               ('fusebox_arrangement_wired_glovebox_rear.png', 'From the rear: the 1/0 cables and the relay grounds to the NEG bar.'),
               ('fusebox_arrangement_wired_glovebox_open.png', 'Covers off: the box-to-box wires.'),
               ('fusebox_arrangement_wired_glovebox_top.png', 'Top view (front of the car at the bottom, RH door on the right).'),
               ('fusebox_arrangement_wired_trunk.png', 'Trunk: the battery relay block and its cables.')):
    fig(f, cap)
A('<h3>LOGIC rev 7 build renders</h3><div class="grid">')
for f, cap in (('fusebox_logic_explode.png', 'LOGIC rev 7, exploded (numbered).'), ('fusebox_render_routing_logic.png', 'LOGIC rev 7 cables (CAD tails).'),
               ('fusebox_render_top_lid_logic.png', 'LOGIC rev 7 lid.'), ('../battrelay_explode.png', 'Battery relay block, exploded (rev 6, unchanged).'),
               ('../battrelay_render_under.png', 'Battery relay block underneath (rev 6, unchanged).')):
    fig(f, cap)
A('</div>')

A('<h2>Bus zone terminals</h2><div class="wrap"><table><tr><th>Bar</th><th>Terminal</th><th>Cable</th><th>Lug</th><th>Leaves</th></tr>')
for (y, nm, hh) in R7['pos_studs']:
    A('<tr><td>POS +</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (E(nm), E(hh + ', 1/0' if hh else 'none yet'),
      'Klauke 6R8 (M8)' if hh else 'bolt + nut fitted', 'outboard end, straight' if hh else '-'))
for (x, nm, hh, g) in R7['neg_studs']:
    A('<tr><td>NEG -</td><td>%s</td><td>%s</td><td>%s</td><td>rear, straight</td></tr>' % (E(nm), E(hh + ', 1/0' if g == '1/0' else 'k_htr 87a 14 AWG, k_pwr 85 18 AWG, k_rev 85 20 AWG'),
      'Klauke 6R8 (M8)' if g == '1/0' else 'their own M8 rings, stacked (harness parts)'))
A('</table></div>')

A('<h2>Checks (Fusion, rev 7 build)</h2><div class="wrap"><table><tr><th>Check</th><th>Result</th></tr>')
for k, lbl in (('logic_bus1_to_bus2_min_mm', 'LOGIC any Bus 1 part to any Bus 2 part (3 mm)'), ('logic_bolt_to_other_strip_min_mm', 'LOGIC strip bolt tip to the other strip (3 mm)'),
               ('bus_pos_lug_to_lug_min_mm', 'POS 1/0 lug to lug (Dan\'s rule: 3 mm)'), ('bus_neg_lug_to_lug_min_mm', 'NEG lug to lug (3 mm)'),
               ('bus_neg_to_pos_min_mm', 'nearest NEG part to POS part (wall between)'), ('bus_pos_lug_to_out_pad_min_mm', 'POS bus lug to nearest AMI output pad'),
               ('pad_to_pad_min_mm', 'AMI output pad to pad'), ('under_deck_lug_to_lug_min_mm', 'lugs under the deck'),
               ('pan_to_nearest_live_power_mm', 'belly pan to nearest live part')):
    A('<tr><td>%s</td><td>%.2f mm</td></tr>' % (E(lbl), live[k]))
bad = [b for b in rep['bends'] if not b['ok']]
A('<tr><td>Cable bends (3 x OD supported / 10 x OD free, FAA AC 43.13-1B)</td><td class="%s">%d checked, %d fail</td></tr>' % ('ok' if not bad else 'bad', len(rep['bends']), len(bad)))
A('<tr><td>Interference between solid parts</td><td class="%s">%s</td></tr>' % ('ok' if not rep['interference'] else 'bad', 'none' if not rep['interference'] else E(rep['interference'])))
A('<tr><td>Cable through printed plastic</td><td class="%s">%s</td></tr>' % ('ok' if not rep['wire_to_printed_contact'] else 'bad', 'none' if not rep['wire_to_printed_contact'] else E(rep['wire_to_printed_contact'])))
A('</table></div>')

A('<h2>Cut + drill (R76: no milling)</h2><div class="wrap"><table><tr><th>Piece</th><th>Stock</th><th>Length</th><th>Holes (from the front / inboard end, on the bar)</th></tr>')
y0 = S.BAR['y0']
ami_y = [S.AMI_Y0 + i * S.AMI_PITCH - y0 for i in range(S.AMI_SLOTS['IN'])]
A('<tr><td>POS bar (bus + AMI inputs)</td><td>1" x 1/4" tinned (MECCANIXITY B0CGJBRNJX), bar 1</td><td>%.0f mm</td><td>14 x 5.5 mm: pairs %.2f mm either side of the centre line at %s; '
  '3 x 8.5 mm on the centre line at %s</td></tr>' % (R7['bar_y1'] - y0, S.AMI_IN_OFF, ', '.join('%.0f' % v for v in ami_y),
                                                     ', '.join('%.0f' % (p[0] - y0) for p in R7['pos_studs'])))
nb = R7['neg_bar']
A('<tr><td>NEG bar</td><td>same stock, bar 2</td><td>%.0f mm</td><td>5 x 8.5 mm on the centre line at %s</td></tr>' % (nb['x1'] - nb['x0'], ', '.join('%.1f' % (n[0] - nb['x0']) for n in R7['neg_studs'])))
A('<tr><td>Battery block bar</td><td>bar 1 (after the POS bar)</td><td>36.5 mm</td><td>as rev 6</td></tr>')
A('<tr><td>Output pads (14 + 1)</td><td>3 x 15 tinned (Bopaodao B09Z7NBLDK)</td><td>17.5 mm each</td><td>as rev 6</td></tr>')
A('</table></div>')

A('<h2>POWER box parts list, rev 7 (with the bus bar in it)</h2>')
A('<p class="mut">Every line a real part with a link (R82; <code>parts_lists.py --check</code>). CSV: <code>cad/fusebox/rev7/fusebox-parts-power.csv</code>. '
  'LOGIC and battery block: the rev 6 lists, unchanged (<code>cad/fusebox/fusebox-parts-logic.csv</code>, <code>-battrelay.csv</code>).</p>')
A('<div class="wrap"><table><tr><th>Group</th><th>Item</th><th>Part</th><th>Need</th><th>Own</th><th>Buy</th><th>$ line</th></tr>')
for r in rows7['POWER']:
    pn = E(r['part_number'])
    if r['source_url']:
        pn = '<a href="%s">%s</a>' % (E(r['source_url']), pn)
    A('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (E(r['group']), E(r['item']), pn, r['qty_need'], r['own'], r['buy'], E(r['line_usd'])))
A('<tr><td></td><td><b>Total (est.)</b></td><td></td><td><b>%d</b></td><td></td><td></td><td><b>$%.2f</b></td></tr></table></div>' % (pcs(rows7['POWER']), tot7['POWER']))

A('<h2>Printed parts</h2><div class="wrap"><table><tr><th>Part</th><th>Rev 7 size (mm)</th><th>Rev 7 volume</th><th>Rev 6 volume</th></tr>')
for k in ('Power_Base_PA12_printed', 'Power_Pan_PA12_printed', 'Power_Cover_PA12_printed'):
    a, b = pp7[k], pp6.get(k, {})
    A('<tr><td>%s</td><td>%s</td><td>%.1f cm3</td><td>%s</td></tr>' % (E(k), ' x '.join('%.0f' % v for v in a['size_mm']), a['volume_cm3'],
      ('%.1f cm3' % b['volume_cm3']) if b else '-'))
A('</table></div><p class="mut">The base is 307 mm long over the feet: check it against the printer bed.</p>')

A('<h2>Files</h2><ul>')
A('<li>Fusion: <code>ST185_fusebox_rev7</code> (Default Project) - its own document, saved-as from rev 6; <code>ST185_fusebox_rev6</code> is untouched.</li>')
A('<li>Local model files: <code>%s\\fusebox\\rev7\\</code> (<code>ST185_fusebox_rev7.f3d</code>, <code>ST185_fusebox_rev7_assembly.step</code>, '
  '<code>Power_*</code> STEP / STL, the two bars as STEP). LOGIC / battery block files: rev 6, <code>%s\\fusebox\\</code>.</li>' % (MAIN, MAIN))
A('<li>Build: <code>cad/fusebox/src/build_fusion.py</code> <code>build(out_dir, rev=7)</code>; spec: <code>spec.py</code> <code>REV7</code>.</li></ul>')

A('<h2>Open questions (batch J)</h2><ul>')
for q in json.load(open(os.path.join(os.path.dirname(os.path.dirname(FB)), 'docs', 'status', 'questions.json')))['questions']:
    if q['id'].startswith('J'):
        A('<li><b>%s - %s:</b> %s<br>%s</li>' % (E(q['id']), E(q['topic']), E(q['text']), ' / '.join('%s) %s%s' % (o['value'], E(o['label']), ' <i>(recommended)</i>' if o.get('recommended') else '') for o in q['options'])))
A('</ul>')
A('<h2>Answered</h2><p><b>P7 = A</b> (rev 7 selected) and <b>U1 = A</b> (the B rev3 universal bar U stays out: the 2 spare AMI positions and the '
  'spare M8 on the + bar cover a new feed), Dan 2026-10-14, DECISIONS R91. The harness redraws that follow are OPEN-ITEMS row 118.</p>')
A('</main></body></html>')
open(OUT, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', os.path.relpath(OUT, os.path.dirname(os.path.dirname(FB))))
