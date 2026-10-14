"""Build cad/fusebox/ST185-fusebox-summary.html: one page for Dan - render, dimensions, parts list, open choices.
Reads spec.py and the build's fusebox_report.json (main checkout cad/fusebox/, untracked). Images stay as separate
PNGs beside the page. Claude Code, 2026-10-14.
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
    ('M5 A2 stud + Keps nut', 'TBD (ISO 4026 set screw M5x12 + DIN 6923 nut)', 'BUY 30 + 30', '2 per AMI position; 4 Nm max (AMI sheet).'),
    ('M8 A2 stud + nut + washer', 'TBD (ISO 4026 M8x20 + ISO 4032 + ISO 7089)', 'BUY 1', '1/0 input'),
    ('Lid screw', 'ISO 7380 M3x10 A2', 'BUY 4', ''),
    ('Nylon shoulder washer, M5', 'TBD', 'BUY 8', '2 per ear (above + below): box isolated from the body, floats 1.5 mm.'),
    ('Tray + lid', '6061-T6, machined', 'make', 'walls 3, floor 3, lid 3'),
    ('Power bar, output pads, logic strips', '6061-T6 25 x 6 bar, 15 pads, 2 x 8 x 4 strips', 'make', 'ring-lug insets machined in the Al (bus bar style)'),
    ('Deck', 'PA6-GF, printed', 'make', 'terminal cavities + TPA comb; holds every conductor off the tray'),
]

iso = rep.get('isolation', {})
mass = rep.get('mass_g', {})
imgs = [(f, c) for f, c in [
    ('fusebox_render_iso_open.png', 'Lid off, from the forward / inboard corner. Forward wall: wire exit strip. Outboard end: 1/0 grommet.'),
    ('fusebox_render_top_open.png', 'Top view, forward edge at the bottom. Left to right: logic zone (mini fuses, micro relays), F7 relays, AMI power zone.'),
    ('fusebox_render_iso_closed.png', 'Closed, 4 isolated mounting ears.'),
    ('fusebox_render_iso_open_rear.png', 'From the rear / outboard corner.'),
    ('fusebox_section_power.png', 'Section through the AMI rows: bar, pads, lug insets, deck, cable bay.'),
    ('fusebox_section_logic.png', 'Section through the logic zone and the F7 relays.'),
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
     '<h1>ST185 glove-box fuse + relay box - CAD rev 1</h1>',
     '<p class="mut">Claude Code, 2026-10-14. One custom box (plan rev 2), modeled in Fusion from maker drawings. '
     'Dan\'s answers applied: L1 AMI studs (R71), L4 smallest sensible footprint (R72), L5 custom box (R70). '
     'Fusion: <code>ST185_fusebox_rev1</code> (Default Project). Model files (STEP / STL / f3d) are local, untracked, in '
     '<code>cad/fusebox/</code> of the main checkout. Build: <code>cad/fusebox/src/</code>.</p>',
     '<div class="kpi">',
     '<div>Outer size<b>%.1f x %.1f x %.1f</b><span class="mut">mm, L x D x H closed</span></div>' % (S.L, S.D, S.H),
     '<div>With ears<b>%.1f mm</b><span class="mut">long</span></div>' % (S.L + 2 * S.EAR['len']),
     '<div>Footprint<b>%s mm&sup2;</b><span class="mut">%d %% less than plan rev 2 (370 x 148)</span></div>' % (format(int(area), ','), round(100 * (1 - area / PLAN_AREA))),
     '<div>Positions<b>15 AMI / 26 mini</b><span class="mut">7 F7 / 10 micro</span></div>',
     '</div>']
for f, c in imgs[:2]:
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(c), E(c)))

h.append('<h2>How it is built</h2><ul>'
         '<li><b>Tray + lid:</b> machined 6061, same style as the VRC / CSB3 enclosures. A 22 mm cable bay under the deck; every wire leaves through one '
         'grommet strip in the forward (firewall) wall. The 1/0 feed enters through its own grommet in the outboard end wall.</li>'
         '<li><b>Isolation:</b> no conductor touches the aluminium. The printed PA6-GF deck carries every terminal, the bar and the pads; '
         'the box itself is isolated from the body by nylon shoulder washers on the 4 ears.</li>'
         '<li><b>Power zone (outboard):</b> one 25 x 6 aluminium bar along the depth, M8 1/0 input at its forward end, AMI fuses on both sides. '
         'Inboard row feeds the F7 relays (short internal leads); outboard row is the direct outputs. Each output stud sits on an aluminium pad with '
         'a ring-lug inset machined in (bus bar design B style): the lug drops into the pocket, the fuse ear clamps it, the barrel exits straight '
         'into a wire hole through the deck.</li>'
         '<li><b>F7 relays (middle):</b> 2 x 4 grid; the 8th spot is the ACPS mini fuse, beside the heater relay (L3B).</li>'
         '<li><b>Logic zone (inboard):</b> Bus 1 and Bus 2 mini-fuse columns (8.1 mm pitch) on 8 x 4 aluminium strips inside the deck, then 10 micro relay positions.</li></ul>')

h.append('<h2>Dimensions</h2><div class="wrap"><table><tr><th>Item</th><th>mm</th><th>Source</th></tr>')
for r in [
    ('Box, closed (L x D x H)', '%.1f x %.1f x %.1f' % (S.L, S.D, S.H), 'model'),
    ('Cable bay / deck / parts above deck', '22 / 26 / to %.1f' % S.LID_Z, 'plan rev 2 allowance; terminal depths to set from TE drawings'),
    ('AMI fuse', '41 long, 30 stud centres, body 16 x 12 x 6, hole 5.5, 4 Nm', 'Bussmann AMI sheet'),
    ('AMI pitch', '%.0f (lug pocket 12.6 + 3.4 wall, gap >= 3)' % S.AMI_PITCH, 'Klauke 2R5 b 12'),
    ('F7 relay', '25.9 sq x 24.9, pitch 30 x 36', 'TE F7 data sheet 2023-03'),
    ('Micro relay', '15.5 x 23 x 24.1, pitch 19 x 30', 'TE Micro Relay A 1308028'),
    ('Mini fuse', '10.92 x 3.81, pitch 8.1', 'Bussmann ATM / Eaton 15400'),
    ('Ears', '4 x %0.f x %0.f x %0.f, hole %0.f' % (S.EAR['len'], S.EAR['w'], S.EAR['t'], S.EAR['hole']), 'model'),
]:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div>')
if iso:
    h.append('<p><b>Isolation check (Fusion, measured):</b> closest conductor to the aluminium tray %.1f mm, to the lid %.1f mm; tray to the mounting face %.1f mm.</p>'
             % (iso.get('min_conductor_to_tray_mm', 0), iso.get('min_conductor_to_lid_mm', 0), iso.get('tray_to_mount_face_mm', 0)))
if 'interference' in rep:
    h.append('<p><b>Interference check:</b> %s.</p>' % ('none between parts' if not rep['interference'] else E(rep['interference'])))
if mass:
    h.append('<p class="mut">Masses (g): %s.</p>' % E(', '.join('%s %s' % (k, v) for k, v in mass.items())))

h.append('<h2>Parts list (OWN / BUY)</h2><p class="mut">Order: on-hand TE list, then TE, then approved suppliers, then others with a reason (R38). '
         '"OWN" counts are qty_ordered from te-on-hand-bom.csv - confirm on the shelf.</p><div class="wrap"><table>'
         '<tr><th>Part</th><th>Part number</th><th>Qty</th><th>Note</th></tr>')
for r in PARTS:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div>')

h.append('<h2>Open choices for Dan</h2><ol>'
         '<li><b>One box or two?</b> The task card says "the 2 custom boxes"; plan rev 2 (your 10-13 answer, fewer boxes) is ONE box. Modeled as one. '
         'Splitting it at the F7 column gives a %0.f mm power box and a %0.f mm logic box, same depth.</li>'
         '<li><b>Power bar metal:</b> aluminium 6061 here (matches the bus bar). Plan rev 2 said copper C110 25 x 3. Copper carries more current for its size; aluminium is lighter and the same metal as the bus bar. 25 x 6 Al (150 mm2) carries more than the 1/0 copper (53 mm2) that feeds it.</li>'
         '</ol>' % (S.L - 72, 72 + 2 * S.WALL))
h.append('<h2>Not done yet (detail work, after your OK)</h2><ul>'
         '<li>Terminal cavity shapes, TPA comb and front stops from the TE terminal drawings (cavities are placeholders at the right pin pattern).</li>'
         '<li>Deck and bar hold-down screws, lid gasket, molded labels; internal leads (relay-feed AMI to F7 pin 30, Bus 1 / Bus 2 links).</li>'
         '<li>Section renders (the section step ran Fusion out of memory and was dropped for rev 1), drawings (PDF), and the CabinPower redraw (R70).</li></ul>')
for f, c in imgs[2:]:
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(c), E(c)))
h.append('</main></body></html>')
open(out, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', out)
