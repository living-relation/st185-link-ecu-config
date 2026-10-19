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
  '<a href="#views">Every wire simulated: sides, exploded, underneath, routing, the boxes cabled together</a>. '
  'Your J1-J4 answers are built in (DECISIONS R94): <a href="#janswers">J answers</a>. '
  'The floating ribs and saddles you marked are joined to the base (R101): <a href="#r95">ribs + saddles supported</a>.</p>')
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
    ('LOGIC feeds (BUS1 50 A, BUS2 k_efi 30)', 2, 2, 'unchanged'),
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
  'The 14 AMI positions bolt onto it as in rev 6 (relays, saddles, harness bundles); since R155 each output is a copper C-strap instead of a pad on a brass standoff.</li>' % (R7['bar_y1'] - S.BAR['y0'], S.BAR['y1'] - S.BAR['y0']))
A('<li><b>A bus zone at the back of the box</b> (+%d mm deep). On the + bar: BAT+ IN, RADLOK+ and a spare M8 - those cables leave straight out of the outboard end. '
  'Beside it a NEG bar (same stock, %d mm): BAT-, RADLOK-, GND ID, GND IG and one M8 for the small relay grounds - those leave straight out the back.</li>'
  % (R7['D'] - S.D, R7['neg_bar']['x1'] - R7['neg_bar']['x0']))
A('<li><b>A printed wall between NEG and POS</b> (2.5 mm, 20 mm above the deck). Closest NEG part to a POS part: <b>%.1f mm</b>, with the wall in between.</li>' % live['bus_neg_to_pos_min_mm'])
A('<li><b>B rev3 adapted to R76:</b> its machined aluminium bars and 1/0 set-screw port blocks become plain tinned copper bars with M8 '
  'bolts (head captured in the deck, like every other bolt) and Klauke 6R8 lugs. Its universal bar U and the link strap / AMG fuse option are dropped (question U1 below).</li>')
A('<li><b>Feet:</b> still four with M6 limiters; the rear-inboard foot moved round to the inboard end so no cable runs over a mounting bolt.</li>')
A('<li><b>Unchanged:</b> LOGIC box and battery relay block (their feeds do not move); bend radius rule, belly pan, PA12 print rules, M6 limiters.</li>')
SN = rep.get('straps', {}).get('numbers', {})
FEA = json.load(open(os.path.join(D7, 'strap_fea.json'))) if os.path.exists(os.path.join(D7, 'strap_fea.json')) else {}
if SN:
    A('<li><b>R155 (N14 = B, 2026-10-17): every AMI position is one copper C-strap</b> (ST185-FB-117, 3 x 15 tinned C110, web / bottom leg 14.2): top leg under '
      'the AMI ear, web down a well in the deck, bottom leg under the deck with the lug bolted palm-up to it; %s; M5 x 10 ear bolt and the lug nut at 4 N.m. '
      'Current: ear -> copper -> lug, no brass and no thread in the path (%.1f uohm, the old pad + standoff %.1f). Held both ways: the lips rest on a printed ledge '
      '(down), a snap hook reaches over them (up) - OUT row the freed skirt, IN row an arm in the deck; 100 N up on the hook: SF %.2f / %.2f (PA12). '
      'The brass standoffs, set screws, crush ribs and LOCTITE 406 (R155) are gone.</li>'
      % (S.STRAP_STUD['pn'] + ' stud (lug end) + DIN 934 nut in a printed holder (top end), N37', SN['R_strap_uohm_20C'], SN['R_old_conductor_uohm_20C'], FEA.get('OUT', {}).get('SF', 0), FEA.get('IN', {}).get('SF', 0)))
A('</ol>')
A('<h2>R155: the copper C-strap station</h2>')
for f, cap in (('renders/closeups/r155_strap_half_section_OUT_JB1.png', 'OUT row (JB1 60 A), half-section at the fuse line: ear on copper, web down the well, lug palm-up under the bottom leg; lips on the ledge, snap hook over them.'),
               ('renders/closeups/r155_strap_iso_OUT_JB1.png', 'The same station, printed base and pan see-through.'),
               ('renders/closeups/r155_strap_half_section_IN_HTR.png', 'IN row (HTR 40 A): the same strap turned 180 deg, its lug runs inboard under the web to the relay saddle.')):
    fig(f, cap)

A('<h2>R181: the C-straps drop straight in (buildability review, 2026-10-18)</h2>')
A('<p>Dan: "make sure the bent copper bars ... can actually be installed from either the top or the bottom". Insertion sweep on the real '
  'STEP solids (base + 14 straps + PEM nuts), 0.25 mm / 2 deg steps, the snap arm free to move within its %.1f %% strain limit '
  '(SNAP_EPS, 1.53 mm): straight down is the only path - from below, tilted (10 / 20 / 30 deg, either end first) or slid in, the strap '
  'hits the rigid deck (the well fits the web and bottom leg with %.1f mm a side). Straight down cleared everything rigid, but the '
  'lip landed flat on the 0.6 mm of hook top past the old 0.9 x 45 chamfer: contact ~88 deg to the push, self-locking - the strap '
  'only went in with the hook pushed back by hand. Fix (R181): the bar-tab lead-in on the strap hooks, %.0f deg from the vertical from '
  '%.1f above the underside, reaching past the lip end; the strap seat pocket starts at the bottom-leg end (0.2 -&gt; 0.3 passing '
  'clearance). Rebuilt model: all 14 stations clear, the hook flexes 1.50 of its 1.53 mm snap-strain limit, steepest contact 51 deg.</p>'
  % (S.SNAP_EPS, S.STRAP['clr'], S.STRAP_TAB['OUT']['lead'], S.STRAP_TAB['OUT']['lead_z']))
for f, cap in (('renders/closeups/r180_strap_insertion_OUT_JB1.png', 'OUT row (JB1), section through a lip: top row the #303 model (stops at 6.00 above the seat), bottom row the rebuilt model.'),
               ('renders/closeups/r180_strap_insertion_IN_HTR.png', 'IN row (HTR), the same.')):
    fig(f, cap)

A('<h2>R170: HEAD relay sockets (5 blades)</h2>')
fig('renders/closeups/head_relay_sockets.png', 'HEAD LH / RH (TE 5-1393292-8): TE drawing V23074-A2001-CD (N26, Dan 2026-10-18) shows a 5th blade at terminal 4 (87a, 4.8 x 0.8), so both sockets now have the 87a blade slot between 85 and 86, like the horn. 87a carries no wire, so it is a plain slot joined to the 87 cavity; fit audit: all 5 TE blades on their slots (offset 0.00), interference 0 (was 42.9 mm3 from the blade the box had no slot for).')

A('<h2>Rev 7 renders</h2>')
for f, cap in (('fusebox_render_iso_closed.png', 'Closed. The POWER box is 62 mm deeper; the bus terminals are etched on the lid.'),
               ('fusebox_render_iso_closed_rear.png', 'From the back: the four NEG cables + the small ground bundle leave the rear, BAT+ IN and RADLOK+ the outboard end.'),
               ('fusebox_render_iso_open.png', 'Covers off: the + bar runs from the AMI fuses into the bus zone; NEG bar on the left of the barrier wall.'),
               ('fusebox_render_top_lid_power.png', 'POWER lid, top view: rev 6 names + the bus terminals.'),
               ('fusebox_render_iso_empty.png', 'Empty: bars, the 14 copper C-straps and the printed barrier.'),
               ('fusebox_render_top_empty.png', 'Empty, top view.'),
               ('fusebox_render_under_pan.png', 'Underneath with the belly pans.'),
               ('fusebox_render_under_open.png', 'Underneath, pans off.'),
               ('fusebox_render_routing_power.png', 'POWER box cables (numbered).'),
               ('fusebox_render_power_bends.png', 'Relay feed bends round their saddles (unchanged).'),
               ('fusebox_power_explode.png', 'Exploded: how it goes together.'),
               ('fusebox_power_step1.png', 'Step 1: bars and bolts; the copper straps drop into their wells and snap under the hooks.'),
               ('fusebox_power_step2.png', 'Step 2: harness terminals and the lugs under the deck.'),
               ('fusebox_power_step3.png', 'Step 3: fuses, relays, the 1/0 bus lugs on top.'),
               ('fusebox_power_step4.png', 'Step 4: belly pan and cover.')):
    fig(f, cap)
A('<div class="grid">')
fig('trimetric-power.png', 'Trimetric, POWER box rev 7 (R83).', 'w')
fig('trimetric-logic.png', 'Trimetric, LOGIC box rev 7 (3 mm fix: 81.5 wide).', 'w')
fig('trimetric-battrelay.png', 'Trimetric, battery relay block rev 7 (R122 screws, R128 solid platform and pedestal).', 'w')
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
                     ('logic_jumper_lug_to_lug_min_mm', 'jumper lug to the next lug, same strip', 'live to live, one circuit - not gated (J1 = A)'),
                     ('logic_strip_to_printed_min_mm', 'strip to its printed lips', 'live to plastic - kept (J2 = B)'),
                     ('logic_jumper_parts_to_printed_min_mm', 'jumper parts to the deck', 'live to plastic - kept (J2 = B)'),
                     ('logic_jumper_parts_to_harness_min_mm', 'jumper parts to the CAD tail bundles', 'live to insulation - kept (J2 = B)'),
                     ('logic_pan_rib_to_live_min_mm', 'new pan rib to the nearest live part', 'live to plastic - J2 = B rib'),
                     ('logic_base_to_live_min_mm', 'base (channel floor, guide walls) to the nearest live part', 'live to plastic - J2 / J4'),
                     ('pan_to_nearest_live_power_mm', 'POWER belly pan to the nearest live part', 'live to plastic - kept (J2 = B)')):
    b_, n_ = BEFORE.get(k), live.get(k)
    ok = n_ is not None and n_ >= 3.0
    A('<tr><td>%s</td><td>%s</td><td class="%s">%s</td><td>%s</td></tr>' % (E(lbl), ('%.2f mm' % b_) if b_ is not None else 'not measured',
      'ok' if ok else ('mut' if 'J' in kind else 'bad'), ('%.2f mm' % n_) if n_ is not None else '-', E(kind)))
A('</table></div>')

A('<h2 id="janswers">Your J1-J4 answers (DECISIONS R94)</h2>')
TH = rep.get('terminal_holes', {})
slots = rep.get('terminal_slots', {})
gw = rep.get('guide_walls', {})
nh = sum(len(v) for v in TH.values())
walls = []
for b_, L_ in TH.items():
    for i_ in range(len(L_)):
        for j_ in range(i_ + 1, len(L_)):
            a_, c_ = L_[i_], L_[j_]
            if a_['group'] != c_['group'] and 'd' in a_ and 'd' in c_:
                walls.append(((a_['x'] - c_['x']) ** 2 + (a_['y'] - c_['y']) ** 2) ** 0.5 - (a_['d'] + c_['d']) / 2)
CH = S.CHANNEL
A('<div class="wrap"><table><tr><th>Question</th><th>Your answer</th><th>What changed</th></tr>')
A('<tr><td>J1 jumper lugs 1.86 mm apart on one strip</td><td>A</td><td>Kept. The 3 mm rule is between different circuits: the lugs on one strip are one '
  'circuit, so that gap is reported, not gated, from now on (<code>check_clearance.py</code> SAME_CIRCUIT). Bus 1 to Bus 2 stays gated: %.2f mm.</td></tr>'
  % live['logic_bus1_to_bus2_min_mm'])
A('<tr><td>J2 live parts against plastic / insulation</td><td>B + your markup</td><td>(1) A printed <b>rib on the LOGIC belly pan</b> (x %.0f-%.0f, %.1f high) '
  'between the Bus 1 output wires and the Bus 1 strip bolt heads; the Bus 1 wires now stack between the pan\'s rounded corner and the rib. '
  '(2) A <b>relief</b> in the pan wall at the outboard micro relay column (inner face cut back %.1f mm, to the 2.0 mm minimum - the base legs sit right outside it). '
  '(3) <b>%d terminal holes</b> sized for their crimp barrel (table below), <b>%d pairs joined into one slot</b> where the wall would have been under %.1f mm, '
  'thinnest wall left between separate holes %.2f mm. (4) <b>%d short guide walls</b> (%.1f x %.1f mm) under the decks between neighbouring holes. '
  'New gate: <code>check_terminal_holes.py</code>.</td></tr>' % (S.PAN_RIB['x'][0], S.PAN_RIB['x'][1], S.PAN_RIB['z_top'] - 4.0, S.PAN_RELIEF['depth'],
  nh, sum(len(v) for v in slots.values()), S.HOLE['min_wall'], min(walls) if walls else 0.0, sum(v['n'] for v in gw.values()), S.GUIDE['t'], S.GUIDE['h']))
A('<tr><td>J3 two wires in one terminal</td><td>A, only if rated for the combined current</td><td>Done in <code>ST185-CabinPower</code>: HL and HR fuse outputs '
  'carry ONE 14 AWG wire each (<code>w_hl_cp</code>, <code>w_hr_cp</code>) to a splice (<code>sp_hl</code>, <code>sp_hr</code>) in the LOGIC front channel that feeds '
  'relay 30 and 86; the horn relay 86 now comes from the existing <code>sp_hz</code> splice (it was a jumper off its own terminal 30). Rating, combined current '
  'through the single wire and terminal: the ATM-15 fuse caps it at 15 A; 14 AWG M22759/16 is about 22 A as a single wire in free air at 80 C '
  '(<a href="https://www.hpacademy.com/assets/Course-Content/Wiring-Fundamentals/1dbddd6411/WireGauge-CurrentRating_CheatSheet.pdf">HP Academy M22759/16 sheet</a>), '
  'x 0.7 in a bundle (R89) = 15.4 A, so it passes; the fuse receptacle is TE 1-968851-1 (MCP 2.8, R166): 1.0-2.5 mm2, 16 / 14 AWG crimp data (TE 114-18148 Rev D1 Table 7). No terminal holds two wires now.</td></tr>')
A('<tr><td>J4 wires that left the box and came back in</td><td>B</td><td>A printed <b>channel floor across the front</b> (z %.2f-%.2f, over the Bus 1 feed lug). '
  'To make room in front of the spine the Bus 1 strip starts at y %.1f (was 8), Bus 2 at y %.1f (was 21) and the Bus 1 feed lug sits at y %.0f / z %.0f '
  '(was 15 / 22). %d wires now cross there, each on its own level (%s), the two splices stacked in the channel past the spine; nothing leaves the box '
  'and comes back.</td></tr>' % (CH['floor'][0], CH['floor'][1], S.STRIP_Y['BUS1'][0], S.STRIP_Y['BUS2'][0], S.FEED['BUS1']['y'], S.FEED['BUS1']['z'],
  len(plan.get('channel', {})), E(', '.join('%s z %.1f' % (k, v) for k, v in sorted(CH['z'].items(), key=lambda kv: kv[1])))))
A('</table></div>')
A('<h3>Terminal holes as built: crimp barrel sizes (TE product pages, read 2026-10-14) - superseded by R120 below</h3>')
A('<p class="mut">Hole = the crimped barrel + %.1f mm a side. Barrel = the larger of the wire insulation and the smallest insulation the terminal is made for '
  '(an uninsulated terminal: the wire insulation still has to go in), plus the metal both sides. Round bore from under the deck up through the barrel zone '
  '(the lower %d %% of the terminal, est), at least %.0f mm deep. A spare cavity gets the hole of the largest wire it takes. Metal thickness or length not on '
  'the TE page: %.2f mm / %.0f mm, marked est.</p>' % (S.HOLE['clr'], 45, S.HOLE['lead_in'], S.T_EST, S.L_EST))
A('<div class="wrap"><table><tr><th>Terminal</th><th>Insulation range</th><th>Metal</th><th>Length</th><th>Holes (box: count x diameter)</th></tr>')
for pn, t_ in S.TERM.items():
    use = {}
    for b_, L_ in TH.items():
        for h_ in L_:
            if h_['part'] == pn and 'd' in h_:
                use.setdefault((b_, h_['d']), 0)
                use[(b_, h_['d'])] += 1
    A('<tr><td>%s<br><span class="mut">%s</span></td><td>%.2f-%.2f mm</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (pn, E(t_['what']), t_['ins'][0], t_['ins'][1],
      ('%.2f' % t_['t']) if t_['t'] else '%.2f est' % S.T_EST, ('%.1f' % t_['L']) if t_['L'] else '%.0f est' % S.L_EST,
      E('; '.join('%s %d x %.2f' % (b_, n_, d_) for (b_, d_), n_ in sorted(use.items()))) or '-'))
A('</table></div>')
A('<div class="grid">')
fig('fusebox_logic_base_holes.png', 'LOGIC base from below (R128): one solid block under the deck - the terminal cavities, joined slots, guide walls and the J4 channel floor.')
fig('fusebox_power_base_holes.png', 'POWER base from below (R127 / R128): one solid block under the deck - the terminal cavities, hex pockets and bend saddles.')
A('</div>')
A('<p>Joined slots (wall under %.1f mm): %s.</p>' % (S.HOLE['min_wall'], E('; '.join(' + '.join(g) for b_ in slots for g in slots[b_])) or 'none'))
grip = [(w_['wire'], e_['part'], w_['od']) for w_ in plan['wires'] for e_ in w_['ends'] if e_.get('at') and e_.get('box') in ('LOGIC', 'POWER')
        and e_.get('part') in S.TERM and w_['od'] < S.TERM[e_['part']]['ins'][0]]
A('<div class="note"><b>Thin-wall wire, OPEN-ITEMS row 121 - your M6 = A (DECISIONS R120):</b> %d wire ends use wire thinner than their terminal&#39;s '
  'insulation range (M22759/16 is thin-wall: 14 AWG is 2.41 mm, 18 AWG 1.85 mm), e.g. 18 AWG in a 42281-1 (made for 2.79-4.32 mm insulation). Each gets a '
  'TE Raychem RNF-100 build-up sleeve under the insulation crimp (table below; on the POWER / LOGIC parts lists).</div>' % len(grip))
A('<h3 id="r120">Terminal cavities: hole sized by everything that passes, self-locking terminals (DECISIONS R120, R121, Dan 2026-10-15)</h3>')
A('<p><b>Hole (R120):</b> the largest cross-section, along the insertion axis, of everything that goes through - the contact box, the crimped '
  'barrels on the <b>thickest</b> insulation the terminal accepts (so GXL or thicker wire always fits), the wire behind them, and any stop '
  'flange - + %.1f mm a side, a combined (rectangular) outline. <b>Lock (R121):</b> the terminal goes up from under the deck, contact box first, and '
  'snaps in: above its neck (where the insulation barrel stops when seated) the cavity steps in to the box - the ledge - and opens a window from the '
  'lance tip up to the seat, so the lance springs out over the ledge; the deck blade slot above (narrower than the box) stops it the other way. Relays '
  'and fuses are held by blade friction only; the cover stays as it is. Where the relay / fuse pin spacing leaves under 2.0 mm, neighbouring cavities '
  'share one opening (R73 kept) and each terminal locks on the side with room (lance that way). <b>M8 = A (R123):</b> the micro relay coil terminal is '
  'TE 280919-2 (locking lance) instead of 2293255-1, and the micro relay columns sit 2.0 mm further out (LOGIC 2.0 wider) so the Bus 2 outputs keep '
  'their ledges; <b>B</b> only where no lance terminal exists - the heater relay R1 (62998-2, 8 AWG on 6.3 blades): a printed retainer clip under it, '
  'threaded onto its wires before crimping, snaps into its collar. <b>Every cavity in the current STEP is from before R120 / R121: all %d are recut at the next rev 7 '
  'Fusion rebuild</b> (<code>check_terminal_holes.py --list</code>).</p>'
  % (S.HOLE['clr'], sum(1 for c_ in plan['cavities'] if c_.get('hole') and not (c_['kind'].endswith('87a') and c_['source'] != 'harness'))))
A('<div class="wrap"><table><tr><th>Terminal</th><th>Box W x H (TE drawing)</th><th>Insulation range</th><th>Lock</th><th>Holes (box: count x size x by y)</th></tr>')
for pn, t_ in S.TERM.items():
    use = {}
    for c_ in plan['cavities']:
        if c_['part'] == pn and c_.get('hole') and not (c_['kind'].endswith('87a') and c_['source'] != 'harness'):
            k_ = (c_['box'], tuple(c_['hole']))
            use[k_] = use.get(k_, 0) + 1
    L_ = S.LOCK[pn]
    lk = ('lance %s, springs out %.2f, tip %.2f below the contact end%s' % ('both sides of the blade width' if L_['axis'] == 'W' else 'through the blade',
          L_['out'], L_['tip'], ' (est.)' if L_.get('est') else '')) if L_['kind'] == 'lance' else ('retainer clip (R123 B)' if L_['kind'] == 'clip' else 'no lance - swapped (R123)')
    A('<tr><td>%s<br><span class="mut">%s</span></td><td>%.2f x %.2f%s</td><td>%.2f-%.2f mm</td><td>%s</td><td>%s</td></tr>' % (
      pn, E(t_['what']), t_['head'][0], t_['head'][1], ' (H est.)' if pn in S.HEAD_EST else '', t_['ins'][0], t_['ins'][1], E(lk),
      E('; '.join('%s %d x %.2f x %.2f' % (b_, n_, sl_[0], sl_[1]) for (b_, sl_), n_ in sorted(use.items()))) or '-'))
A('</table></div>')
A('<p><b>Optional cover screws (R122):</b> beside each of the 4 cover catches on every box, an M3 brass heat-set insert (McMaster 94459A140) in a boss '
  'behind the base skirt (hung from the deck plate; on the battery block it stands on the floor) and an M3 x 10 cap screw (Accu SSCF-M3-10-A4) through '
  'a 3.4 mm hole in the cover band, %.0f mm from the catch centre - clear of the tongue. The snaps stay the main hold. The belly pans have no tab, so no screw.</p>'
  % S.SCREW['off'])
sl = {}
for (w_, pn, od) in grip:
    seq, d2 = S.build_up(pn, od)
    k_ = (pn, od, ' + '.join(seq) if seq else 'none fits', round(d2, 2))
    sl[k_] = sl.get(k_, 0) + 1
A('<div class="wrap"><table><tr><th>Terminal</th><th>Wire OD</th><th>RNF-100 build-up (under the insulation crimp)</th><th>Built-up OD (est.)</th><th>Ends</th></tr>')
for (pn, od, sq, d2), n_ in sorted(sl.items()):
    A('<tr><td>%s</td><td>%.2f</td><td>%s</td><td>%.2f</td><td>%d</td></tr>' % (pn, od, E(sq), d2, n_))
A('</table></div>')
A('<p class="mut">The 87a cavities have no harness wire today, so they keep their plain blade slot: an 87a terminal next to 85 / 86 would leave only 0.4 mm '
  'of wall (the micro relay pin pattern), so a future 87a wire needs its own look.</p>')

FS = rep.get('feature_support', {})
A('<h2 id="r95">Ribs and saddles supported (DECISIONS R101)</h2>')
A('<p>Your markup 2026-10-15: "the little ribs and the wire radius runners are just floating. fill in the gaps between relay positions '
  'under the ribs and add material under the radius runners". They were joined to the base, but only by a sliver: a guide wall crossing the gap '
  'between two relay positions had cavity tower over its ends only, and each POWER bend saddle met the deck only where the relay tower was. '
  'Now:</p><ul>')
for bx, kind, what in (('LOGIC', 'guide wall', 'a web the size of the wall fills the gap between the towers, from the wall up into the deck plate'),
                       ('POWER', 'saddle', 'the back of the saddle runs on up into the deck plate (it used to stop at the tower bottom)')):
    L_ = [f for f in FS.get(bx, []) if f['kind'] == kind and f['web']]
    if L_:
        A('<li><b>%s, %d %ss</b> (top face %.0f-%.0f %% backed before): %s.</li>' % (bx, len(L_), kind, 100 * min(f['before'] for f in L_),
          100 * max(f['before'] for f in L_), E(what)))
A('<li>Nothing else changed (your call: "i like them as they are. just fix the floating pieces i mentioned"). Floating = under %.0f %% of the top face on solid '
  'material; every other hanging feature is above that and stays as it was (%s).</li>' % (100 * S.FLOAT_BACKING, ', '.join(
    '%s: %d of %d left alone' % (bx, sum(1 for f in L_ if not f['web']), len(L_)) for bx, L_ in sorted(FS.items()))))
A('<li>Every printed part of all three boxes (POWER, LOGIC, battery relay block: base, pan, cover) is one solid - one body, one lump, one shell '
  'in Fusion and one connected mesh in its STL. New HARD gate <code>cad/fusebox/src/check_printed_solid.py</code> (in <code>check_all.py</code>) '
  'checks all three things.</li>')
A('<li>The LOGIC front channel floor is a shelf carried by the spine. It is connected, but nothing can go under it: the Bus 1 feed lug sits there.</li></ul>')
A('<div class="grid">')
for f, cap in (('r95_logic_section_before.png', 'LOGIC, cut through a guide wall between the micro relay columns - before: a deep slot, the wall hangs at its end'),
               ('r95_logic_section_after.png', 'After: the slot under the wall is solid'),
               ('r95_power_saddles_before.png', 'POWER from below, bend saddles - before: each saddle meets the deck only at the relay tower'),
               ('r95_power_saddles_after.png', 'After: every saddle runs up into the deck plate')):
    fig(f, cap, 'w')
A('</div>')

WC = json.load(open(os.path.join(D7, 'wall_check.json')))['parts']
A('<h2 id="sweep">Wall sweep: every printed part (DECISIONS R128)</h2>')
A('<p>Your call 2026-10-16: "fix the ones you found as long as they don&#39;t alter the function and installability of the parts". The R127 gate '
  '(walls over 1.95 mm, every feature attached by 3 mm or more) found 411 thin-wall and 32 attachment spots on the nine printed parts (counted with '
  'the corrected checker). Fixed by rule in the build, nothing moved that a terminal, relay, fuse, cover, pan, screw, cable or mounting point uses:</p><ul>')
for li in ('LOGIC base: one solid block under the deck plate, as the POWER base (R127) - the towers, collars and slivers between them are inside it.',
           'Relay / fuse blade slots only above the receptacle seat (the R120 cavity is the hole below); an 87a with no terminal is as deep as the '
           'blade reaches; the normally-open micro relays (HEAD L / R, HORN, ETB) have no 87a slot at all.',
           'A strip under 2.0 mm left between two openings of a joined cavity group, or between a cavity / hex pocket and the belly-pan groove, is cut away '
           '(the R120 join rule carried through); no lock ledge is touched (checked on all 119 lance cavities).',
           'Slanted guide walls that crossed a straight one (left only triangular slivers) are left out; the straight walls stay.',
           'All 8 mounting legs solid (outside, foot, M6 hole and socket unchanged); battery block relay platform and fuse pedestal solid, rim 4.0 '
           '(was 3.0, grown inward); bus-zone barrier wall 3.0 (was 2.5, grown away from the NEG bar).',
           'Fuse-body recesses level with the pad seat (0.4 under the fuse body, was 0.6); two LOGIC spine bolt passes 1.9 apart joined into one slot; '
           'two pan exit notches closer than 2.0 joined; a pan floor under a notch thickened downward to 2.0; cover labels 0.5 deep (2.0 of top left).'):
    A('<li>%s</li>' % E(li))
A('</ul><p>What has to stay thin is a <b>named exemption</b> - the build records a box round each one and the gate lists it by name '
  '(<code>spec.WALL_EXEMPT</code>):</p><div class="wrap"><table><tr><th>Exemption</th><th>Why it stays</th></tr>')
for k, why in S.WALL_EXEMPT.items():
    A('<tr><td>%s</td><td>%s</td></tr>' % (E(k), E(why)))
A('</table></div><div class="wrap"><table><tr><th>Part</th><th>Thin-wall spots</th><th>Attachment spots</th><th>Volume</th></tr>')
for n, w in WC.items():
    A('<tr><td>%s</td><td>%d</td><td>%s</td><td>%.1f cm3</td></tr>' % (E(n), len(w['walls']), len(w['attach']) if w.get('attach_checked') else 'shell', w['volume_cm3']))
A('</table></div><div class="grid">')
A('<p><b>Amended 2026-10-16 (R127):</b> every outer wall of a base keeps 3.0 behind its deepest pocket, grown OUTWARD only (skirt 3.0 -> 4.3, battery '
  'rim 4.3; inner face, cavities, pans unchanged; covers grow with the outline, same clearances); the curved bend saddles are back, cut only near the top '
  'by a radial plane clear of the 30 cavity.</p>')
for f, cap in (('renders/closeups/sweep_saddle.png', 'Bend saddle, #270 / now.'), ('renders/closeups/sweep_outer_wall.png', 'Outer wall beside a relay cavity, #270 / now.'),
               ('renders/closeups/sweep_logic_under.png', 'LOGIC base from below, before / after.'),
               ('renders/closeups/sweep_logic_cavities.png', 'LOGIC cavities from below, before / after.'),
               ('renders/closeups/sweep_legs.png', 'Mounting leg, before / after.'),
               ('renders/closeups/sweep_battrelay.png', 'Battery relay block base, before / after.')):
    fig(f, cap, 'w')
A('</div>')
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
  'none (J2 = B: the pan wall relief at the outboard relay column)' if not wrep['through_printed'] else '%d wires touch printed plastic: %s'
  % (len(wrep['through_printed']), E(', '.join(sorted(set(x[0] for x in wrep['through_printed'])))))))
A('<tr><td>Wire insulation against bare live metal</td><td class="%s">%s</td></tr>' % ('ok' if not wrep['bare_metal_touch'] else 'bad',
  'none (J2 = B: the pan rib keeps the Bus 1 wires off the strip bolt heads)' if not wrep['bare_metal_touch'] else '%s pass %.2f mm from bare metal' % (E(', '.join(sorted(set(x[0] for x in wrep['bare_metal_touch'])))),
  min(x[2] for x in wrep['bare_metal_touch']))))
A('<tr><td>Live to live (3 mm rule)</td><td class="ok">no new bare metal in the simulation; the gate result above stands (J1 = A: same-strip gaps reported, not gated)</td></tr>')
A('<tr><td>Wire to wire</td><td>%d places where two modelled wires share space (they cross in the crowded LOGIC lanes and under the deck); '
  'insulated wires crossing is normal, so the 3 mm rule does not apply. Closest: %.2f mm</td></tr>' % (len(wrep['wire_wire']['overlaps']), wrep['wire_wire']['min_mm'] or 0.0))
over_ = [d for d in plan['doubles'] if d['over']]
A('<tr><td>Two wires crimped in one terminal</td><td class="%s">%s</td></tr>' % ('bad' if over_ else 'ok', E('; '.join(
  '%s: %s mm2 in %s (max %s)' % (d['cavity'], d['mm2'], d['part'], d['range'][1]) for d in over_)) if over_ else 'none (J3 = A: one wire per terminal, the HL / HR splices)'))
A('<tr><td>LOGIC wires that leave and come back in</td><td class="%s">%s</td></tr>' % ('bad' if plan['loops'] else 'ok',
  ('%d: %s' % (len(plan['loops']), E(', '.join(plan['loops'])))) if plan['loops'] else
  'none (J4 = B: %d wires cross in the front channel - %s)' % (len(plan.get('channel', {})), E(', '.join(sorted(plan.get('channel', {})))))))
A('</table></div>')
A('<h3>Exits</h3><div class="wrap"><table><tr><th>Box</th><th>Exit (lane)</th><th>Wires (CAD drew)</th><th>Round bundle</th><th>Notch</th><th>Packed in the notch: top</th><th>Fits</th></tr>')
for x in plan['exits']:
    if x['opening'] is None:     # R123: the micro relay lanes moved in the source; the CAD notch follows at the rev 7 rebuild
        A('<tr><td>%s</td><td>%.1f</td><td>%d (-)</td><td>%.1f mm</td><td>-</td><td>z %.1f (deck %.1f)</td><td class="mut">moved (R123): notch cut at the rev 7 rebuild</td></tr>' % (
          x['box'], x['lane'], x['wires'], x['d'], x['stack_top'], x['deck']))
        continue
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
               ('bus_neg_to_pos_min_mm', 'nearest NEG part to POS part (wall between)'), ('bus_pos_lug_to_out_strap_min_mm', 'POS bus lug to nearest AMI output strap'),
               ('strap_to_strap_min_mm', 'AMI copper strap to strap'), ('strap_station_to_station_min_mm', 'strap station to the next (strap, PEM nuts, bolts, lug)'),
               ('under_deck_lug_to_lug_min_mm', 'lugs under the deck'),
               ('pan_to_nearest_live_power_mm', 'belly pan to nearest live part')):
    A('<tr><td>%s</td><td>%.2f mm</td></tr>' % (E(lbl), live[k]))
bad = [b for b in rep['bends'] if not b['ok']]
A('<tr><td>Cable bends (3 x OD supported / 10 x OD free, FAA AC 43.13-1B)</td><td class="%s">%d checked, %d fail</td></tr>' % ('ok' if not bad else 'bad', len(rep['bends']), len(bad)))
A('<tr><td>Interference between solid parts</td><td class="%s">%s</td></tr>' % ('ok' if not rep['interference'] else 'bad', 'none' if not rep['interference'] else E(rep['interference'])))
pp_ = rep['printed_parts']
one = all(v.get('lumps') == 1 and v.get('shells') == 1 and v['bodies'] == 1 for v in pp_.values())
A('<tr><td>Every printed part one solid, every rib / saddle backed (R101)</td><td class="%s">%s</td></tr>' % (
    'ok' if one else 'bad', ('%d parts, 1 lump each' % len(pp_)) if one else 'FLOATING PIECE'))
A('<tr><td>Cable through printed plastic</td><td class="%s">%s</td></tr>' % ('ok' if not rep['wire_to_printed_contact'] else 'bad', 'none' if not rep['wire_to_printed_contact'] else E(rep['wire_to_printed_contact'])))
A('</table></div>')

A('<h2>Copper: machined parts (D6, R76 amended 2026-10-16)</h2><p class="mut">Every copper piece is a machined part to its drawing: '
  'holes as below (clearance ISO 273 medium; LOGIC strip holes at the tap drill), <b>0.3 x 45 deg edge break on every edge, hole rims included</b> (F10). '
  'SteveCAD audit v3 checks: NEG 14,878.1 / POS 33,050.9 mm3, the same as the checked reference files.</p>'
  '<div class="wrap"><table><tr><th>Piece</th><th>Stock</th><th>Length</th><th>Holes (from the front / inboard end, on the bar)</th></tr>')
y0 = S.BAR['y0']
ami_y = [S.AMI_Y0 + i * S.AMI_PITCH - y0 for i in range(S.AMI_SLOTS['IN'])]
A('<tr><td>POS bar (bus + AMI inputs)</td><td>1" x 1/4" tinned (MECCANIXITY B0CGJBRNJX), bar 1</td><td>%.0f mm</td><td>14 x 5.5 mm: pairs %.2f mm either side of the centre line at %s; '
  '3 x %.1f mm on the centre line at %s</td></tr>' % (R7['bar_y1'] - y0, S.AMI_IN_OFF, ', '.join('%.0f' % v for v in ami_y), S.CLEAR[8],
                                                     ', '.join('%.0f' % (p[0] - y0) for p in R7['pos_studs'])))
nb = R7['neg_bar']
A('<tr><td>NEG bar</td><td>same stock, bar 2</td><td>%.0f mm</td><td>5 x %.1f mm on the centre line at %s (the GND stud 8.0 from the end; 1.5 between the GND ring and the GND IG 6R8, N3)</td></tr>' % (nb['x1'] - nb['x0'], S.CLEAR[8], ', '.join('%.1f' % (n[0] - nb['x0']) for n in R7['neg_studs'])))
A('<tr><td>Battery block bar</td><td>bar 1 (after the POS bar)</td><td>36.5 mm</td><td>M6 feed %.1f, AMI 40 input 5.5</td></tr>' % S.CLEAR[6])
A('<tr><td>LOGIC strips (2)</td><td>1" x 1/8" tinned (MECCANIXITY B0CGJC2S1L)</td><td>%.1f / %.1f mm</td><td>PEM mounting holes %.2f +0.08 at each stud (rows z %.1f / %.1f) and %.2f '
  'at the feed, then PEM %s / %s self-clinching nuts pressed in, heads on the gap side (N2, R129); strips %.1f apart</td></tr>' % (
    S.STRIP_Y['BUS1'][1] - S.STRIP_Y['BUS1'][0], S.STRIP_Y['BUS2'][1] - S.STRIP_Y['BUS2'][0], S.PEM[4]['hole'], S.JROW['z_lo'], S.JROW['z_lo'] + S.JROW['dz'],
    S.PEM[5]['hole'], S.PEM[4]['pn'], S.PEM[5]['pn'], live.get('logic_strip_to_strip_mm', 0)))
BL = S.strap_blank()
A('<tr><td>Output C-straps (14, ST185-FB-117)</td><td>3 x 15 tinned (Bopaodao B09Z7NBLDK)</td><td>blank %.2f mm (%.2f finished, no trim)</td><td>top hole %.1f / lug hole %.1f +0.08 (PEM %s stud) at %.1f and %.2f from the top end; '
  'kerfs + notches beside the 7.0 tongue; edges milled to %.1f from %.2f; bends R%.1f at %.2f / %.2f (drawing)</td></tr>' % (
    BL['cut_length'], BL['length'], BL['hole_top'], BL['hole_lug'], S.STRAP_STUD['pn'], BL['pem_top'], BL['pem_bottom'], BL['w_low'], BL['low_from'], BL['ri'], BL['bend_centres'][0], BL['bend_centres'][1]))
A('<tr><td>Battery block pad (1, ST185-FB-112)</td><td>same 3 x 15 bar</td><td>17.5 mm</td><td>one 5.5</td></tr>')
A('</table></div>')

A('<h2>POWER box parts list, rev 7 (with the bus bar in it)</h2>')
A('<p class="mut">Every line a real part with a link (R82; <code>parts_lists.py --check</code>). CSV: <code>cad/fusebox/rev7/fusebox-parts-power.csv</code>. '
  'LOGIC and battery block: the lists in <code>cad/fusebox/fusebox-parts-logic.csv</code> / <code>-battrelay.csv</code>, printed parts priced from these rev 7 volumes.</p>')
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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(FB)), 'docs'))
from needs_dan import open_questions
for q in open_questions():
    if q['id'].startswith('J'):
        A('<li><b>%s - %s:</b> %s<br>%s</li>' % (E(q['id']), E(q['topic']), E(q['text']), ' / '.join('%s) %s%s' % (o['value'], E(o['label']), ' <i>(recommended)</i>' if o.get('recommended') else '') for o in q['options'])))
A('</ul>')
A('<h2>Answered</h2><p><b>P7 = A</b> (rev 7 selected) and <b>U1 = A</b> (the B rev3 universal bar U stays out: the 2 spare AMI positions and the '
  'spare M8 on the + bar cover a new feed), Dan 2026-10-14, DECISIONS R91. The harness redraws that follow are OPEN-ITEMS row 118.</p>')
A('</main></body></html>')
open(OUT, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', os.path.relpath(OUT, os.path.dirname(os.path.dirname(FB))))
