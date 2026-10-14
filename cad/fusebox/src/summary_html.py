"""Build cad/fusebox/ST185-fusebox-summary.html: one page for Dan - render, dimensions, printed parts, parts list, open choices.
Reads spec.py and the build's fusebox_report.json (main checkout cad/fusebox/, untracked). Images stay as separate
PNGs beside the page. Claude Code, 2026-10-14 (rev 2: powder-bed printed PA12 housings, R73).
    python cad/fusebox/src/summary_html.py <dir with fusebox_report.json + renders> <out html>
"""
import os, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec as S

src_dir, out = sys.argv[1], sys.argv[2]
rep = json.load(open(os.path.join(src_dir, 'fusebox_report.json')))
E = lambda s: html.escape(str(s))

PLAN_AREA = 370 * 148
area = S.L * S.D

ami = {30: 0, 40: 0, 50: 0, 60: 0}
for row in ('IN', 'OUT'):
    for nm, a in S.AMI_ROWS[row][:S.AMI_SLOTS[row]]:
        if a:
            ami[a] += 1
mini = {}
for col, (x, fuses) in S.MINI_COLS.items():
    for nm, a in fuses:
        if a:
            mini[a] = mini.get(a, 0) + 1
mini[S.ACPS[1]] = mini.get(S.ACPS[1], 0) + 1
n_hold = len(S.BAR_SCREW_Y) + S.AMI_SLOTS['IN'] + S.AMI_SLOTS['OUT']

PRINTED_NOTE = {
    'Tray_PA12_printed': 'Open-top tub, 3 mm walls and floor, 4 gusseted mounting ears (brass limiter in each), 4 deck posts and 4 corner bosses with M3 heat-set inserts. Forward wire-exit slot, 1/0 grommet hole in the outboard end.',
    'Deck_PA12_printed': '8 mm top plate on a 3 mm skirt; terminal-cavity towers under every relay / fuse group; 4 ribs under the power zone run front-to-back (with the wires). Open underneath: no closed cavity, no trapped powder.',
    'Lid_PA12_printed': '2.5 mm plate with a 2 x 3 mm rib grid on top (stops a flat PA12 plate warping); 4 M3 screws into the tray inserts.',
}

# OWN / BUY  (st185-pick-parts: on-hand CSV first, TE, approved suppliers, then others with a reason)
PARTS = [
    ('Relay F7 Maxi ISO, 680 ohm', '1-1414147-0 (V23134-J0052-X429)', 'OWN 3 + BUY 1', 'heater, k_efi, k_fan (own); k_str (buy). te-on-hand-bom.csv: qty_ordered 3 - confirm on the shelf.'),
    ('Relay F7 Maxi ISO, bracket, 560 ohm', '1-1393304-0 (V23134-J1052-X281)', 'OWN 2', 'k_fan2, power. Bracket not used in the box (cut off or fold flat).'),
    ('Micro relay A, NO, diode', '5-1393292-8', 'OWN 2', 'HEAD LH / RH'),
    ('Micro relay A, NO', '4-1904124-3', 'OWN 1', 'horn'),
    ('Micro relay A, NO, resistor', '4-1904124-2', 'OWN 1', 'k_etb'),
    ('Micro relay A, CO, diode', '6-1419137-4', 'OWN 2 + BUY 1', 'k_acc, k_eps_en (own); k_rev (buy)'),
    ('HCR150 relay', '1416010-1', 'OWN 1', 'k_eps, mounted beside the box (not in it)'),
    ('AMI bolt-in fuse', 'Bussmann AMI-30 / -40 / -50 / -60', 'BUY %d / %d / %d / %d' % (ami[30], ami[40], ami[50], ami[60]),
     'Other maker (R38 step 4): TE makes no bolt-in fuse. Part numbers from the Bussmann AMI sheet / Mouser list.'),
    ('Mini blade fuse (ATM)', 'Bussmann ATM-2 / 5 / 7.5 / 10 / 15 / 20', 'BUY ' + ' / '.join('%s' % mini[k] for k in sorted(mini)),
     'ratings ' + ', '.join('%sA x%d' % (k, mini[k]) for k in sorted(mini)) + '. Other maker: TE makes no blade fuse.'),
    ('FASTON 9.5 receptacle, 12-10 AWG', '280756-4', 'BUY 12', 'F7 30 / 87 (6 relays). TE.'),
    ('FASTON 6.35 receptacle, 18-14 AWG', '42281-1', 'OWN 20 + BUY ~6', 'F7 85 / 86 (12) + micro 6.3 load blades (~14). qty_ordered 20.'),
    ('4.8 mm receptacle (micro coil blades)', 'TBD', '-', 'TBD: TE 4.8 x 0.8 receptacle for 18-20 AWG - pick in detail work.'),
    ('2.8 mm receptacle (mini fuse)', 'TBD', '-', 'TBD: 880398-2 is a candidate (plan S12), fit on an ATM blade not confirmed.'),
    ('Tubular lug 10 mm2 M5 (AMI outputs, 8-10 AWG)', 'Klauke 2R5', 'BUY 11', 'Same lug family as the bus bar (Klauke R); TE SOLISTRAND alternative not checked yet.'),
    ('Tubular lug 16 mm2 M5 (J/B1 HOT, 6 AWG)', 'Klauke 3R5', 'BUY 1', 'Hole 5.5 confirmed; tongue width NOT confirmed - pocket drawn for 12 mm.'),
    ('Tubular lug 50 mm2 M8 (1/0 input)', 'Klauke 6R8', 'BUY 1', 'b 20, l 47, hole 8.4 (RS 398-3015 listing).'),
    ('M5 A2 stud + Keps nut', 'TBD (ISO 4026 set screw M5x12 + DIN 6923 nut)', 'BUY 30 + 30', '2 per AMI position, threaded into the Al bar / pads; 4 Nm max (AMI sheet).'),
    ('M8 A2 stud + nut + washer', 'TBD (ISO 4026 M8x20 + ISO 4032 + ISO 7089)', 'BUY 1', '1/0 input, threaded into the Al bar'),
    ('Hold-down screw M4x10 A2', 'ISO 7380', 'BUY %d' % n_hold, 'From below, into tapped Al bar (5) and pads (15).'),
    ('Brass compression limiter, M4', 'TBD (OD 7, ID 4.3, L 4)', 'BUY %d' % n_hold, 'Under every hold-down: the clamp goes screw -> brass -> Al, never into bare nylon.'),
    ('Brass compression limiter, M5', 'TBD (OD 8, ID 5.3, L 6)', 'BUY 4', 'One per mounting ear.'),
    ('Brass heat-set insert, M3', 'TBD (hole 4.0 x 6 deep as drawn - set to the insert maker)', 'BUY 8', '4 lid corners + 4 deck posts. No printed threads.'),
    ('Lid / deck screw', 'ISO 7380 M3x8 A2 (lid), M3x10 (deck)', 'BUY 4 + 4', ''),
    ('Power bar, output pads, logic strips', '6061-T6: 25 x 6 bar, 15 pads, 2 strips 8 x 4', 'make', 'Ring-lug insets machined in the Al pads (bus bar style). The only metal besides studs, lugs and hardware.'),
    ('Tray, deck, lid', 'PA12, powder-bed (MJF / SLS)', 'print', 'See "Printed parts" above.'),
]

live = rep.get('live_clearance', {})
printed = rep.get('printed_parts', {})
imgs = [(f, c) for f, c in [
    ('fusebox_render_iso_open.png', 'Lid off, from the forward / inboard corner. Forward wall: wire exit strip. Outboard end: 1/0 grommet.'),
    ('fusebox_render_top_open.png', 'Top view, forward edge at the bottom. Left to right: logic zone (mini fuses, micro relays), F7 relays, AMI power zone.'),
    ('fusebox_render_iso_closed.png', 'Closed: ribbed PA12 lid, 4 gusseted ears with brass limiters.'),
    ('fusebox_render_iso_open_rear.png', 'From the rear / outboard corner.'),
] if os.path.exists(os.path.join(src_dir, f))]

CSS = """
:root{--bg:#fafaf8;--fg:#1d1d1b;--mut:#666;--line:#ddd;--acc:#b35c00;--card:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#1b1b1a;--fg:#ecece8;--mut:#a0a09a;--line:#3a3a38;--acc:#f0a050;--card:#242423}}
:root[data-theme=dark]{--bg:#1b1b1a;--fg:#ecece8;--mut:#a0a09a;--line:#3a3a38;--acc:#f0a050;--card:#242423}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif;margin:0}
main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:24px;margin:8px 0 2px}h2{font-size:18px;margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
.mut{color:var(--mut)}table{border-collapse:collapse;width:100%;font-size:13.5px}
td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
.wrap{overflow-x:auto}figure{margin:12px 0}img{max-width:100%;border:1px solid var(--line);border-radius:6px;background:#888}
figcaption{color:var(--mut);font-size:13px}.kpi{display:flex;flex-wrap:wrap;gap:10px}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:150px}
.kpi b{display:block;font-size:20px}ol li{margin-bottom:6px}
"""

h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
     '<title>ST185 Fuse Box CAD</title><style>%s</style></head><body><main>' % CSS,
     '<h1>ST185 glove-box fuse + relay box - CAD rev 2 (printed)</h1>',
     '<p class="mut">Claude Code, 2026-10-14. One custom box (plan rev 2). Rev 2: tray, deck and lid are PA12 printed by powder-bed fusion '
     '(Dan\'s HP printer, R73); only the current-carrying parts are metal. Dan\'s answers: L1 AMI studs (R71), L4 smallest sensible '
     'footprint (R72), L5 custom box (R70). Fusion: <code>ST185_fusebox_rev2</code> (Default Project; rev 1 aluminium version kept there as history). '
     'Model files (STEP / STL / f3d) are local, untracked, in <code>cad/fusebox/</code> of the main checkout. Build: <code>cad/fusebox/src/</code>.</p>',
     '<div class="kpi">',
     '<div>Outer size<b>%.1f x %.1f x %.1f</b><span class="mut">mm, L x D x H closed</span></div>' % (S.L, S.D, S.H),
     '<div>With ears<b>%.1f mm</b><span class="mut">long</span></div>' % (S.L + 2 * S.EAR['len']),
     '<div>Footprint<b>%s mm&sup2;</b><span class="mut">%d %% less than plan rev 2 (370 x 148)</span></div>' % (format(int(area), ','), round(100 * (1 - area / PLAN_AREA))),
     '<div>Positions<b>15 AMI / 26 mini</b><span class="mut">7 F7 / 10 micro</span></div>',
     '</div>']
for f, c in imgs[:2]:
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(c), E(c)))

h.append('<h2>Printed parts (PA12, powder-bed)</h2><div class="wrap"><table><tr><th>Part</th><th>File (STL + STEP)</th><th>Size mm (L x D x H)</th><th>Volume / mass</th><th>What it is</th></tr>')
for n in ('Tray_PA12_printed', 'Deck_PA12_printed', 'Lid_PA12_printed'):
    pr = printed.get(n, {})
    sz = ' x '.join('%.1f' % v for v in pr.get('size_mm', [])) or '-'
    h.append('<tr><td>%s</td><td><code>%s.stl</code><br><code>%s.step</code></td><td>%s</td><td>%s cm&sup3; / ~%s g</td><td>%s</td></tr>'
             % (E(n.split('_')[0]), E(n), E(n), E(sz), E(pr.get('volume_cm3', '-')), E(int(pr.get('mass_g_pa12', 0))), E(PRINTED_NOTE[n])))
h.append('</table></div><p class="mut">Mass at the HP PA12 part density 1.01 g/cm&sup3;. Metal parts are exported as STEP only '
         '(<code>Bar_Power_Al6061_25x6</code>, <code>Pad_Out_Al6061</code>, <code>Strip_Logic_Al6061_8x4</code>) plus the whole assembly '
         '(<code>ST185_fusebox_rev2_assembly.step</code>).</p>')

h.append('<h2>Designed for powder-bed printing</h2><ul>'
         '<li><b>Walls:</b> 3 mm tray walls and floor (loaded), 2.5 mm ribs and gussets, 8 mm deck plate (4 mm under the metal pockets), 2.5 mm lid plus ribs. Nothing under 2.0 mm.</li>'
         '<li><b>No solid blocks:</b> the deck is a ribbed shell with towers only where the terminal cavities are; the lid is ribbed instead of thick.</li>'
         '<li><b>No trapped powder:</b> every printed part is open on one side (tray top, deck underside, lid is a plate); no closed cavity, so no escape holes are needed.</li>'
         '<li><b>Fits:</b> %.2f mm per side between printed parts (deck in tray, around posts and bosses); %.1f mm per side for metal in a printed pocket.</li>'
         '<li><b>Threads:</b> none printed. M3 brass heat-set inserts in the tray (lid corners, deck posts); all power studs thread into the aluminium bar and pads.</li>'
         '<li><b>Torque goes into metal:</b> the AMI nuts (4 Nm) bear on the fuse ear, lug and Al pad / bar; the stud is threaded into the Al. The bar (5 screws) and every pad (1 screw) '
         'are held down from below by M4 screws through brass compression limiters, so the clamp is screw -> brass -> Al and never crushes nylon. The mounting ears have brass limiters too.</li>'
         '<li><b>Heat:</b> PA12 (HP 3D HR PA 12) deflects at 95 &deg;C under 1.82 MPa and 175 &deg;C under 0.45 MPa. The 25 x 6 Al bar (150 mm&sup2;) carries more than '
         'the 1/0 copper (53 mm&sup2;) that feeds it, so the bar runs cooler than the feed cable. Keep it below 95 &deg;C: check with a thermocouple on the bench at full load before the box goes in.</li>'
         '<li><b>Live-part spacing (measured in Fusion):</b> neighbouring AMI outputs %.1f mm apart with a printed rib between, input bar to any output %.1f mm, 1/0 lug to the nearest output %.1f mm, '
         'output lugs %.1f mm apart. At 12-14 V these gaps are about keeping debris and a dropped tool from bridging, not about voltage.</li>'
         '</ul>' % (S.PCLR, S.CLR, live.get('pad_to_pad_min_mm', 0), live.get('bar_to_pad_min_mm', 0), live.get('input_lug_to_pad_min_mm', 0), live.get('output_lug_to_lug_min_mm', 0)))

h.append('<h2>How it is laid out</h2><ul>'
         '<li><b>Power zone (outboard):</b> one 25 x 6 aluminium bar along the depth, M8 1/0 input at its forward end, AMI fuses on both sides. '
         'Inboard row feeds the F7 relays (short internal leads); outboard row is the direct outputs. Each output stud sits on an aluminium pad with '
         'a ring-lug inset machined in (bus bar design B style).</li>'
         '<li><b>F7 relays (middle):</b> 2 x 4 grid; the 8th spot is the ACPS mini fuse, beside the heater relay (L3B).</li>'
         '<li><b>Logic zone (inboard):</b> Bus 1 and Bus 2 mini-fuse columns (8.1 mm pitch) on 8 x 4 aluminium strips that slide into the deck from below, then 10 micro relay positions.</li>'
         '<li><b>Wiring:</b> every wire drops through the deck into the 22 mm cable bay and leaves through one grommet strip in the forward (firewall) wall.</li></ul>')

h.append('<h2>Dimensions</h2><div class="wrap"><table><tr><th>Item</th><th>mm</th><th>Source</th></tr>')
for r in [
    ('Box, closed (L x D x H)', '%.1f x %.1f x %.1f' % (S.L, S.D, S.H), 'model'),
    ('Cable bay / deck / parts above deck', '22 / 26 / to %.1f' % S.LID_Z, 'plan rev 2 allowance; terminal depths to set from TE drawings'),
    ('AMI fuse', '41 long, 30 stud centres, body 16 x 12 x 6, hole 5.5, 4 Nm', 'Bussmann AMI sheet'),
    ('AMI pitch', '%.1f (pad 14.5 + 3.0 gap)' % S.AMI_PITCH, 'Klauke 2R5 b 12 -> pocket 12.8'),
    ('F7 relay', '25.9 sq x 24.9, pitch 30 x 36', 'TE F7 data sheet 2023-03'),
    ('Micro relay', '15.5 x 23 x 24.1, pitch 19 x 30', 'TE Micro Relay A 1308028'),
    ('Mini fuse', '10.92 x 3.81, pitch 8.1', 'Bussmann ATM / Eaton 15400'),
    ('Ears', '4 x %0.f x %0.f x %0.f, 2 gussets each, hole %.1f for the M5 limiter' % (S.EAR['len'], S.EAR['w'], S.EAR['t'], S.EAR['hole']), 'model'),
]:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div>')
if 'interference' in rep:
    h.append('<p><b>Interference check:</b> %s.</p>' % ('none between parts' if not rep['interference'] else E(rep['interference'])))

h.append('<h2>Parts list (OWN / BUY)</h2><p class="mut">Order: on-hand TE list, then TE, then approved suppliers, then others with a reason (R38). '
         '"OWN" counts are qty_ordered from te-on-hand-bom.csv - confirm on the shelf. TBD = not checked against a maker sheet yet.</p><div class="wrap"><table>'
         '<tr><th>Part</th><th>Part number</th><th>Qty</th><th>Note</th></tr>')
for r in PARTS:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div>')

h.append('<h2>Open choices for Dan</h2><ol>'
         '<li><b>One box or two?</b> The task card says "the 2 custom boxes"; plan rev 2 (your 10-13 answer, fewer boxes) is ONE box. Modeled as one. '
         'Splitting it at the F7 column gives an about %0.f mm power box and an about %0.f mm logic box, same depth - and two smaller prints.</li>'
         '<li><b>Power bar metal:</b> aluminium 6061 here (matches the bus bar). Plan rev 2 said copper C110. Copper carries more current for its size; '
         'aluminium is lighter and the same metal as the bus bar.</li>'
         '<li><b>PA12 or a glass-filled grade?</b> Plain PA12 assumed. HP\'s PA12 GB (glass beads) is stiffer but more brittle - say if your shop prefers it near the bar.</li>'
         '</ol>' % (S.L - 72, 72 + 2 * S.WALL))
h.append('<h2>Not done yet (detail work, after your OK)</h2><ul>'
         '<li>Terminal cavity shapes, TPA comb and front stops from the TE terminal drawings (cavities are placeholders at the right pin pattern).</li>'
         '<li>Exact heat-set insert and compression-limiter part numbers (hole sizes drawn as placeholders); lid seal; molded labels; internal leads (relay-feed AMI to F7 pin 30, Bus 1 / Bus 2 links).</li>'
         '<li>Section renders (that Fusion step ran out of memory in rev 1 and stays off), drawings, and the CabinPower redraw (R70).</li></ul>')
for f, c in imgs[2:]:
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(c), E(c)))
h.append('</main></body></html>')
open(out, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', out)
