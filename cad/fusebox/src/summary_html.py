"""Build cad/fusebox/ST185-fusebox-summary.html: one page for Dan - renders, sizes, slot map, printed parts, parts list,
the Y2 bar-metal choice. Reads spec.py and the build's fusebox_report.json (main checkout cad/fusebox/, untracked).
Images stay as separate PNGs beside the page. Claude Code, 2026-10-14 (rev 3: two boxes + battery relay block, R75).
    python cad/fusebox/src/summary_html.py <dir with fusebox_report.json + renders> <out html>
"""
import os, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec as S

src_dir, out = sys.argv[1], sys.argv[2]
rep = json.load(open(os.path.join(src_dir, 'fusebox_report.json')))
E = lambda s: html.escape(str(s))

PLAN_AREA = 370 * 148
REV2_AREA = 254.5 * 181.0
boxes = rep.get('boxes_mm', {})
fp = rep.get('footprint_mm2', {})
cabin_area = fp.get('LOGIC', 0) + fp.get('POWER', 0)

ami = {30: 0, 40: 0, 50: 0, 60: 0}
for row in ('IN', 'OUT'):
    for nm, a in S.AMI_ROWS[row][:S.AMI_SLOTS[row]]:
        if a:
            ami[a] += 1
ami[S.RB['fuse'][1]] += 1                      # battery relay block AMI 40
mini = {}
for col, (x, fuses) in S.MINI_COLS.items():
    for nm, a in fuses:
        if a:
            mini[a] = mini.get(a, 0) + 1
mini[S.ACPS[1]] = mini.get(S.ACPS[1], 0) + 1
n_hold_box = len(S.BAR_SCREW_Y) + S.AMI_SLOTS['IN'] + S.AMI_SLOTS['OUT']
n_hold = n_hold_box + 3
n_posts = sum(len(b['posts']) for b in S.BOXES.values())
n_lim5 = 4 * len(S.BOXES) + 2
cu = S.METAL['CuC110']['density'] / S.METAL['Al6061']['density']
mass = rep.get('mass_g', {})
al_g = sum(mass.values())

PRINTED_NOTE = {
    'Tray': 'Open-top tub, 3 mm walls and floor, 4 gusseted ears (brass limiter in each), deck posts and 4 corner bosses with M3 heat-set inserts, forward wire-exit slot.',
    'Deck': '8 mm top plate on a 3 mm skirt; terminal-cavity towers under every relay / fuse group; open underneath (no closed cavity, no trapped powder).',
    'Lid': '2.5 mm plate with a 2 x 3 mm rib grid on top (stops a flat PA12 plate warping); 4 M3 screws into the tray inserts.',
    'BattRelay_Tray': 'Open-top tub, 4 mm floor: HCR150 bolted through its flange + 2 brass M6 limiters (the same 2 bolts hold the block down), ribs under the bar and pad, 2 ears at the fuse end, grommet holes: battery feed (end), pump feed + coil lead (front).',
    'BattRelay_Lid': '2.5 mm ribbed plate, 4 M3 screws into inserts.',
}

# OWN / BUY  (st185-pick-parts: on-hand CSV first, TE, approved suppliers, then others with a reason)
PARTS = [
    ('Relay F7 Mini ISO, 680 ohm', '1-1414147-0 (V23134-J0052-X429)', 'OWN 3', 'k_efi, k_str, k_fan. te-on-hand-bom.csv qty_ordered 3 - confirm on the shelf.'),
    ('Relay F7 Mini ISO, bracket, 560 ohm', '1-1393304-0 (V23134-J1052-X281)', 'OWN 2', 'k_fan2, power. Bracket not used in the box (cut off or fold flat).'),
    ('Relay Power Relay B, 1 form C, 680 ohm', '1-1904020-2 (V23234-A0001-X032)', 'BUY 1', 'heater k_htr (changeover, 87a to ground - row 106). TE (step 2): same Mini ISO pattern as the F7 plus 87a; 28.5 sq x 25.3; NO 35 A at 85 C (50 A at 23 C) against the 40 A AMI HTR fuse - fine for the blower, see note under the table.'),
    ('Micro relay A, NO, diode', '5-1393292-8', 'OWN 2', 'HEAD LH / RH (LOGIC box)'),
    ('Micro relay A, NO', '4-1904124-3', 'OWN 1', 'horn'),
    ('Micro relay A, NO, resistor', '4-1904124-2', 'OWN 1', 'k_etb'),
    ('Micro relay A, CO, diode', '6-1419137-4', 'OWN 2 + BUY 1', 'k_acc, k_eps_en (own); k_rev (buy)'),
    ('HCR150 relay, 130 A, IP67', '1416010-1 (V23132-A2001-B200)', 'OWN 2', 'k_eps beside the POWER box; k_fp in the battery relay block (the second one was the dropped battery-kill relay). Coil 3.9 W = 0.33 A on Link Aux 3 (2 A low side).'),
    ('HCR150 coil plug: Superseal 1.5 2-pole housing', '282080-1', 'BUY 1', 'TE, from the HCR150 data sheet (k_fp).'),
    ('Superseal 1.5 contact / seal', '282110-1 / 281934-2', 'OWN 2 / BUY 2', '282110-1 is on hand (qty_ordered 10).'),
    ('AMI bolt-in fuse', 'Bussmann AMI-30 / -40 / -50 / -60', 'BUY %d / %d / %d / %d' % (ami[30], ami[40], ami[50], ami[60]),
     'incl. the battery block AMI-40. Other maker (R38 step 4): TE makes no bolt-in fuse.'),
    ('Mini blade fuse (ATM)', 'Bussmann ATM-2 / 5 / 7.5 / 10 / 15 / 20', 'BUY ' + ' / '.join('%s' % mini[k] for k in sorted(mini)),
     'ratings ' + ', '.join('%sA x%d' % (k, mini[k]) for k in sorted(mini)) + '. Other maker: TE makes no blade fuse.'),
    ('FASTON 9.5 receptacle, 12-10 AWG', '280756-4', 'BUY 12', 'Mini ISO 30 / 87 (6 relays). TE. Power Relay B blade widths to confirm on its drawing in detail work.'),
    ('FASTON 6.35 receptacle, 18-14 AWG', '42281-1', 'OWN 20 + BUY ~7', 'Mini ISO 85 / 86 (12) + heater 87a (1) + micro 6.3 load blades (~14). qty_ordered 20.'),
    ('4.8 mm receptacle (micro coil blades)', 'TBD', '-', 'TBD: TE 4.8 x 0.8 receptacle for 18-20 AWG - pick in detail work.'),
    ('2.8 mm receptacle (mini fuse)', 'TBD', '-', 'TBD: 880398-2 is a candidate (plan S12), fit on an ATM blade not confirmed.'),
    ('Tubular lug 10 mm2 M5 (8-10 AWG)', 'Klauke 2R5', 'BUY 14', '11 AMI outputs + 2 LOGIC strip feeds + 1 battery block AMI out. b 12, l 22 (Klauke sheet via Rapid).'),
    ('Tubular lug 16 mm2 M5 (J/B1 HOT, 6 AWG)', 'Klauke 3R5', 'BUY 1', 'b 12 confirmed (Klauke table, Kempston Controls 3R10.pdf): a 13, l 26, d4 8.5, hole 5.5 - fits the 12.8 pocket.'),
    ('Tubular lug 50 mm2 M8 (1/0 input)', 'Klauke 6R8', 'BUY 1', 'b 20, l 47, hole 8.4 (RS 398-3015 listing).'),
    ('Ring lug M6, 10 AWG (battery block: feed in, relay 3, relay 5)', 'TBD', 'BUY 3', 'TBD: Klauke R series M6 for 6 mm2 - not checked against the Klauke sheet yet. HCR150 terminals take an M6 lug up to 25 mm2 (TE sheet).'),
    ('M5 A2 stud + Keps nut', 'TBD (ISO 4026 set screw M5x12 + DIN 6923 nut)', 'BUY 32 + 32', '2 per AMI position (15 + 1), threaded into the bar / pads; 4 Nm max (AMI sheet).'),
    ('M8 / M6 A2 stud + nut + washer', 'TBD (ISO 4026 + ISO 4032 + ISO 7089)', 'BUY 1 + 1', 'POWER box 1/0 input (M8); battery block feed (M6).'),
    ('Hold-down screw M4x10 A2', 'ISO 7380', 'BUY %d' % n_hold, 'From below into the tapped bar and pads: POWER %d, battery block 3.' % n_hold_box),
    ('Strip feed screw M5x8 A2', 'ISO 7380', 'BUY 2', 'LOGIC: feed lug under each strip end.'),
    ('Brass compression limiter, M4', 'TBD (OD 7, ID 4.3, L 4)', 'BUY %d' % n_hold, 'Under every hold-down. TBD: no maker sheet checked yet (McMaster round brass spacers are the likely source).'),
    ('Brass compression limiter, M5 / M6', 'TBD (OD 8, ID 5.3, L 6 / OD 10, ID 6.5, L 4)', 'BUY %d / 2' % n_lim5, 'Mounting ears / the HCR150 flange bolts.'),
    ('Brass heat-set insert, M3', 'McMaster 94459A130 (candidate)', 'BUY %d' % (12 + n_posts),
     'M3 x 0.5, 4.3 long, 4.0 hole per the Aboveboard Electronics cross-reference - confirm on the McMaster page before ordering. Other maker (R38 step 4): TE and the approved suppliers sell no heat-set inserts. Hole drawn 4.0 x 6 deep.'),
    ('Lid / deck screw', 'ISO 7380 M3x8 A2 (lid), M3x10 (deck)', 'BUY 12 + %d' % n_posts, ''),
    ('Power bars, output pads, logic strips', '%s: 2 bars 25 x 6, 16 pads, 2 strips 8 x 4' % S.BAR_METAL, 'make', 'Metal is Y2 (below). Ring-lug insets machined in the POWER pads.'),
    ('Trays, decks, lids', 'PA12, powder-bed (MJF / SLS)', 'print 8 parts', 'See "Printed parts".'),
]

live = rep.get('live_clearance', {})
printed = rep.get('printed_parts', {})
imgs = [(f, c) for f, c in [
    ('fusebox_render_iso_open.png', 'Lids off. Back left: LOGIC box (mini fuses + micro relays). Back right: POWER box (Mini ISO relays + AMI bar, 1/0 in at the outboard end). Front: battery relay block (shown next to them; it goes in the trunk).'),
    ('fusebox_render_top_open.png', 'Top view, forward (wire-exit) edge at the bottom.'),
    ('battrelay_render_iso_open.png', 'Battery relay block, lid off: battery feed in on the M6 stud, AMI 40, lead to HCR150 terminal 3; terminal 5 out to the pump through the front wall; coil lead out beside it.'),
    ('fusebox_render_iso_closed.png', 'Closed: ribbed PA12 lids, gusseted ears with brass limiters.'),
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
.kpi b{display:block;font-size:20px}ol li,ul li{margin-bottom:6px}
"""


def size(k):
    b = boxes.get(k, {})
    return '%.1f x %.1f x %.1f' % (b.get('L', 0), b.get('D', 0), b.get('H', 0))


h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
     '<title>ST185 Fuse Box CAD</title><style>%s</style></head><body><main>' % CSS,
     '<h1>ST185 fuse + relay boxes - CAD rev 3 (two boxes + battery relay block)</h1>',
     '<p class="mut">Claude Code, 2026-10-14. Rev 3 follows Dan\'s Y1 answer (DECISIONS R75): the rev 2 box is split into a LOGIC box and a POWER box in '
     'the glove box, plus a small relay block at the battery (trunk) for the fuel pump relay. Same print rules as rev 2 (PA12 powder-bed, R73); only '
     'current-carrying parts are metal. Earlier answers: L1 AMI studs (R71), L4 smallest sensible footprint (R72), L5 custom boxes (R70). '
     'Fusion: <code>ST185_fusebox_rev3</code> (the rev 2 document, renamed and rebuilt - no new document, R74). Model files (STEP / STL / f3d) are local, '
     'untracked, in <code>cad/fusebox/</code> of the main checkout. Build: <code>cad/fusebox/src/</code>.</p>',
     '<div class="kpi">',
     '<div>LOGIC box<b>%s</b><span class="mut">mm, L x D x H closed</span></div>' % size('LOGIC'),
     '<div>POWER box<b>%s</b><span class="mut">mm, L x D x H closed</span></div>' % size('POWER'),
     '<div>Battery relay block<b>%s</b><span class="mut">mm, trunk</span></div>' % size('BATTRELAY'),
     '<div>Glove-box footprint<b>%s mm&sup2;</b><span class="mut">two boxes, %d %% less than plan rev 2; rev 2 one box: %s</span></div>'
     % (format(int(cabin_area), ','), round(100 * (1 - cabin_area / PLAN_AREA)), format(int(REV2_AREA), ',')),
     '</div>']
for f, c in imgs[:3]:
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(c), E(c)))

h.append('<h2>How it is split</h2><ul>'
         '<li><b>POWER box (outboard, nearest the 1/0 from the RH sill):</b> the bar with all %d AMI fuses (inboard row feeds the relays, outboard row are the '
         'direct outputs), the six Mini ISO relays (k_efi, k_str, k_fan, k_fan2, power - TE F7; heater k_htr - TE Power Relay B changeover, its cavity has the '
         '5th terminal, 87a), the ACPS mini fuse beside the heater relay, one spare relay position. The HCR150 EPS relay stays beside it.</li>'
         '<li><b>LOGIC box (inboard, toward the ECU):</b> Bus 1 and Bus 2 mini-fuse columns on two metal strips, ten micro relay positions (three spare). '
         'Each strip has its own feed lug, screwed to the strip underside at its rear end: <b>Bus 1</b> from the POWER box AMI BUS1 50 A output (8 AWG), '
         '<b>Bus 2</b> from k_efi 87 (10 AWG). These two wires are the only box-to-box links.</li>'
         '<li><b>Cut line:</b> the gap between the micro relays and the first Mini ISO column - every zone keeps its rev 2 position, so the layout, '
         'pitches and clearances are unchanged.</li>'
         '<li><b>Battery relay block (trunk, near the battery):</b> the fuel pump relay k_fp = the spare on-hand TE HCR150 (130 A at 85 C against a 19-25 A pump), '
         'its AMI 40 fuse on a short bar, M6 battery feed stud. Feed from the kill switch LOAD side, so the trunk switch also stops the pump. Coil- from Link Aux 3 (A19). '
         'The pump feed no longer runs from the glove box to the trunk.</li>'
         '<li><b>Wiring:</b> in both glove-box boxes every wire drops through the deck into the 22 mm cable bay and leaves through the forward (firewall) wall.</li></ul>'
         % (sum(ami.values()) - 1))

h.append('<h2>Slot map</h2><div class="wrap"><table><tr><th>Unit</th><th>Position</th><th>Fuse / relay</th><th>Part</th></tr>')
for row in ('IN', 'OUT'):
    for i, (nm, a) in enumerate(S.AMI_ROWS[row][:S.AMI_SLOTS[row]]):
        h.append('<tr><td>POWER</td><td>AMI %s-%d</td><td>%s</td><td>%s</td></tr>' % (row, i + 1, E(nm if a else 'spare'), 'AMI-%d' % a if a else '-'))
k = 0
for c, cx in enumerate(S.F7_COLS):
    for r, cy in enumerate(S.F7_ROWS):
        nm, pn, own = S.F7_POS[k]
        k += 1
        if nm == 'ACPS':
            h.append('<tr><td>POWER</td><td>R%d%d</td><td>ACPS mini fuse (heater 87)</td><td>ATM-10</td></tr>' % (c + 1, r + 1))
        else:
            h.append('<tr><td>POWER</td><td>R%d%d</td><td>%s</td><td>%s</td></tr>' % (c + 1, r + 1, E(nm), E('%s (%s)' % (pn, own) if pn else '-')))
for col, (cx, fuses) in S.MINI_COLS.items():
    h.append('<tr><td>LOGIC</td><td>%s (%d)</td><td>%s</td><td>ATM</td></tr>' % (col, len(fuses), E(', '.join('%s %s' % (nm, a) if a else 'spare' for nm, a in fuses))))
k = 0
for c, cx in enumerate(S.MICRO_COLS):
    for r, cy in enumerate(S.MICRO_Y):
        nm, pn, own = S.MICRO_POS[k]
        k += 1
        h.append('<tr><td>LOGIC</td><td>M%d%d</td><td>%s</td><td>%s</td></tr>' % (c + 1, r + 1, E(nm if pn else 'spare'), E('%s (%s)' % (pn, own) if pn else '-')))
h.append('<tr><td>BATTERY</td><td>F1</td><td>FP fuse 40 A</td><td>AMI-40</td></tr>'
         '<tr><td>BATTERY</td><td>K1</td><td>k_fp fuel pump relay</td><td>1416010-1 HCR150 (OWN)</td></tr></table></div>')

h.append('<h2>Printed parts (PA12, powder-bed)</h2><div class="wrap"><table><tr><th>Part</th><th>File (STL + STEP)</th><th>Size mm (L x D x H)</th><th>Volume / mass</th><th>What it is</th></tr>')
for n, pr in printed.items():
    sz = ' x '.join('%.1f' % v for v in pr.get('size_mm', [])) or '-'
    unit, rest = n.split('_', 1)
    kind = rest.split('_')[0]
    note = PRINTED_NOTE.get('%s_%s' % (unit, kind), PRINTED_NOTE.get(kind, ''))
    h.append('<tr><td>%s %s</td><td><code>%s.stl</code><br><code>%s.step</code></td><td>%s</td><td>%s cm&sup3; / ~%s g</td><td>%s</td></tr>'
             % (E(unit), E(kind), E(n), E(n), E(sz), E(pr.get('volume_cm3', '-')), E(int(pr.get('mass_g_pa12', 0))), E(note)))
h.append('</table></div><p class="mut">Mass at the HP PA12 part density 1.01 g/cm&sup3;. Metal parts are exported as STEP only, plus the whole assembly '
         '(<code>ST185_fusebox_rev3_assembly.step</code>).</p>')

h.append('<h2>Designed for powder-bed printing (same rules as rev 2)</h2><ul>'
         '<li><b>Walls:</b> 3 mm tray walls and floor (4 mm battery block floor), 2.5 mm ribs and gussets, 8 mm deck plate, 2.5 mm lids plus ribs. Nothing under 2.0 mm.</li>'
         '<li><b>No solid blocks, no trapped powder:</b> ribbed decks open underneath, open-top trays, ribbed lids; no closed cavity.</li>'
         '<li><b>Fits:</b> %.2f mm per side printed to printed; %.1f mm per side metal in a printed pocket.</li>'
         '<li><b>Threads:</b> none printed. M3 brass heat-set inserts for lids and deck posts; power studs thread into the metal.</li>'
         '<li><b>Torque goes into metal:</b> AMI nuts on fuse ear / lug / metal; every bar, pad and strip held from below through brass limiters (strip feed screws clamp the lug straight to the strip); '
         'the HCR150 bolts clamp its flange through brass limiters to the trunk floor.</li>'
         '<li><b>Heat:</b> PA12 HDT 95 &deg;C at 1.82 MPa. Bench check the bar at full load with a thermocouple before the box goes in.</li>'
         '<li><b>Live-part spacing (measured in Fusion):</b> AMI outputs %.1f mm apart with a printed rib between, bar to any output %.1f mm, 1/0 lug to nearest output %.1f mm, '
         'output lugs %.1f mm; Bus 1 to Bus 2 strip %.1f mm; battery block bar to pad %.1f mm, HCR150 lugs %.1f mm (set by the relay\'s 17 mm terminal pitch).</li>'
         '</ul>' % (S.PCLR, S.CLR, live.get('pad_to_pad_min_mm', 0), live.get('bar_to_pad_min_mm', 0), live.get('input_lug_to_pad_min_mm', 0),
                    live.get('output_lug_to_lug_min_mm', 0), live.get('logic_strip_to_strip_mm', 0), live.get('battrelay_bar_to_pad_mm', 0),
                    live.get('battrelay_relay_lug_to_lug_mm', 0)))
if 'interference' in rep:
    h.append('<p><b>Interference check (all three units):</b> %s.</p>' % ('none between parts' if not rep['interference'] else E(rep['interference'])))

h.append('<h2>Dimensions and sources</h2><div class="wrap"><table><tr><th>Item</th><th>mm</th><th>Source</th></tr>')
for r in [
    ('LOGIC / POWER / battery block, closed', '%s / %s / %s' % (size('LOGIC'), size('POWER'), size('BATTRELAY')), 'model'),
    ('AMI fuse', '41 long, 30 stud centres, body 16 x 12 x 6, hole 5.5, 4 Nm', 'Bussmann AMI sheet'),
    ('F7 relay', '25.9 sq x 24.9, pitch 30 x 36', 'TE F7 data sheet 2023-03'),
    ('Power Relay B (heater)', '28.5 sq x 25.3; 85-86 16.8, 87 7.9 off the 85/86 line, 87a 8.35 from 87, 30-87 17.9', 'TE V23234 data sheet 11-2018'),
    ('HCR150', 'body 63 x 45, 40 deep; flange holes 84 apart, 6.5; M6 terminals 17 apart; 71 to the coil plug', 'TE V23132 data sheet 03-2014'),
    ('Micro relay', '15.5 x 23 x 24.1, pitch 19 x 30', 'TE Micro Relay A 1308028'),
    ('Mini fuse', '10.92 x 3.81, pitch 8.1', 'Bussmann ATM / Eaton 15400'),
]:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div>')

h.append('<h2>Parts list (OWN / BUY)</h2><p class="mut">Order: on-hand TE list, then TE, then approved suppliers, then others with a reason (R38). '
         '"OWN" counts are qty_ordered from te-on-hand-bom.csv - confirm on the shelf. TBD = not checked against a maker sheet yet.</p><div class="wrap"><table>'
         '<tr><th>Part</th><th>Part number</th><th>Qty</th><th>Note</th></tr>')
for r in PARTS:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div><p class="mut">Heater relay vs fuse: the AMI HTR fuse is 40 A and Power Relay B carries 35 A continuous at 85 &deg;C on its NO contact '
         '(ISO 8820-3 overload 1.35 x 35 A for 30 min, so a 40 A fuse still protects it). The blower draws well under that; if the 40 A fuse is only there for '
         'wire size, a 30 A AMI would match the relay exactly - your call.</p>')

h.append('<h2>Y2 - power bar: aluminium or copper?</h2><div class="wrap"><table><tr><th></th><th>Aluminium 6061 (modeled)</th><th>Tinned copper C110 (Dispatch pick)</th></tr>'
         '<tr><td>Conductivity</td><td>about 43 %% IACS: needs the 25 x 6 section</td><td>100 %% IACS: 25 x 3 would do the same job; 25 x 6 runs much cooler</td></tr>'
         '<tr><td>Joints</td><td>Tinned copper lugs on bare Al = galvanic pair; needs plating or contact grease; Al creeps under bolt clamp, so nuts lose preload over heat cycles</td>'
         '<td>Tin to tin with the Klauke lugs - no galvanic pair, no creep worth worrying about</td></tr>'
         '<tr><td>Stud threads (4 Nm AMI)</td><td>M5 in 6061 is fine at 4 Nm but strips sooner if over-torqued</td><td>Copper threads hold the same; C110 is gummy to tap - use C101 / C145 or a good tap</td></tr>'
         '<tr><td>Weight (bars, pads, strips)</td><td>%d g</td><td>about %d g at the same sizes</td></tr>'
         '<tr><td>Making it</td><td>Easy to machine, cheap, same metal as the bus bar</td><td>Costs more, harder to machine; tin plate after machining</td></tr>'
         '<tr><td>Heat into the PA12</td><td>Runs warmer for the same section</td><td>Runs cooler - more margin to the 95 &deg;C PA12 limit</td></tr></table></div>'
         '<p>Recommendation: tinned copper, mainly for the joints (no Al-to-tin pair, no creep). Weight is the only real cost. Switching is one line '
         '(<code>BAR_METAL</code> in <code>spec.py</code>); the model is unchanged either way.</p>' % (round(al_g), round(al_g * cu)))

h.append('<h2>Not done yet (detail work, after your OK)</h2><ul>'
         '<li>Terminal cavity shapes, TPA comb and front stops from the TE terminal drawings (cavities are placeholders at the right pin pattern).</li>'
         '<li>Compression-limiter part numbers, M6 lugs for the battery block, the heat-set insert confirmed on the McMaster page; lid seals; molded labels; internal leads.</li>'
         '<li>Trunk mounting spot for the battery block (Route 1 area, near the kill switch) and a drip / splash check - the HCR150 is IP67, the block lid is not sealed.</li>'
         '<li>Drawings, and the harness redraws listed in OPEN-ITEMS row 107.</li></ul>')
for f, c in imgs[3:]:
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(c), E(c)))
h.append('</main></body></html>')
open(out, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', out)
