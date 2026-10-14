"""Build cad/fusebox/ST185-fusebox-summary.html: one page for Dan - his rev 3 review answered point by point, renders
(closed, loaded, EMPTY, underneath), the bend-radius table, pieces and build order, slot map, printed parts, parts list,
the copper stock picks and cut / drill drawings. Reads spec.py and the build's fusebox_report.json.
Images stay as separate PNGs beside the page. Claude Code, 2026-10-14 (rev 4: base + snap cover, open underneath,
bend radius, etched labels, Blue Sea-style battery block; rev 3 R75; rev 3.1 R76).
    python cad/fusebox/src/summary_html.py <dir with fusebox_report.json + renders> <out html>
"""
import os, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec as S

src_dir, out = sys.argv[1], sys.argv[2]
rep = json.load(open(os.path.join(src_dir, 'fusebox_report.json')))
E = lambda s: html.escape(str(s))

REV3_H = 85.0
REV3 = {'LOGIC': (79.0, 181.0, 85.0), 'POWER': (185.5, 181.0, 85.0), 'BATTRELAY': (150.0, 110.0, 53.5)}
boxes = rep.get('boxes_mm', {})
live = rep.get('live_clearance', {})
printed = rep.get('printed_parts', {})
mass = rep.get('mass_g', {})
cu_g = sum(mass.values())

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
n_pos = S.AMI_SLOTS['IN'] + S.AMI_SLOTS['OUT']
n_used = sum(1 for row in ('IN', 'OUT') for nm, a in S.AMI_ROWS[row][:S.AMI_SLOTS[row]] if a)
n_12awg = sum(1 for nm, g in S.AMI_AWG.items() if g == 12)

PRINTED_NOTE = {
    'Power_Base': 'The deck on four corner legs: 6 mm top plate, 3 mm skirt, cavity towers, standoff and bolt-head bosses, ribs; open underneath. '
                  'Six printed saddles (R16) and an outboard comb hang under it. Ears point front / rear, brass limiter in each.',
    'Logic_Base': 'Same idea: deck on four legs, strip pockets open underneath, mini-fuse and micro-relay cavities through.',
    'BattRelay_Base': 'Low floor plate, rim on the long sides only (both ends open), relay platform with 2 captured M6 nuts + limiters, '
                      'pedestal under the bar and pad, 2 tabs (one each long side).',
    'Cover': 'Rounded shell, 2.5 mm wall, R13 plan corners, R5 top edges; 4 snap tongues; labels etched 0.6 deep into the top.',
}

# OWN / BUY  (st185-pick-parts: on-hand CSV first, TE, approved suppliers, then others with a reason)
PARTS = [
    ('Relay F7 Mini ISO, 680 ohm', '1-1414147-0 (V23134-J0052-X429)', 'OWN 3', 'k_efi, k_str, k_fan. te-on-hand-bom.csv qty_ordered 3 - confirm on the shelf.'),
    ('Relay F7 Mini ISO, bracket, 560 ohm', '1-1393304-0 (V23134-J1052-X281)', 'OWN 2', 'k_fan2, power. Bracket not used (cut off or fold flat).'),
    ('Relay Power Relay B, 1 form C, 680 ohm', '1-1904020-2 (V23234-A0001-X032)', 'BUY 1', 'heater (87a to ground, row 106). TE (step 2). NO 35 A at 85 C.'),
    ('Micro relay A, NO, diode', '5-1393292-8', 'OWN 2', 'HEAD LH / RH (LOGIC box)'),
    ('Micro relay A, NO', '4-1904124-3', 'OWN 1', 'horn'),
    ('Micro relay A, NO, resistor', '4-1904124-2', 'OWN 1', 'k_etb'),
    ('Micro relay A, CO, diode', '6-1419137-4', 'OWN 2 + BUY 1', 'k_acc, k_eps_en (own); k_rev (buy)'),
    ('HCR150 relay, 130 A, IP67', '1416010-1 (V23132-A2001-B200)', 'OWN 2', 'k_eps beside the POWER box; k_fp in the battery block.'),
    ('HCR150 coil plug: Superseal 1.5 2-pole housing', '282080-1', 'BUY 1', 'TE, from the HCR150 data sheet (k_fp).'),
    ('Superseal 1.5 contact / seal', '282110-1 / 281934-2', 'OWN 2 / BUY 2', '282110-1 is on hand (qty_ordered 10).'),
    ('AMI bolt-in fuse', 'Bussmann AMI-30 / -40 / -50 / -60', 'BUY %d / %d / %d / %d' % (ami[30], ami[40], ami[50], ami[60]),
     'incl. the battery block AMI-40. Other maker (R38 step 4): TE makes no bolt-in fuse.'),
    ('Mini blade fuse (ATM)', 'Bussmann ATM-2 / 5 / 7.5 / 10 / 15 / 20', 'BUY ' + ' / '.join('%s' % mini[k] for k in sorted(mini)),
     'ratings ' + ', '.join('%sA x%d' % (k, mini[k]) for k in sorted(mini)) + '. Other maker: TE makes no blade fuse.'),
    ('FASTON 9.5 receptacle, 12-10 AWG', '280756-4', 'BUY 12', 'Mini ISO 30 / 87 (6 relays). TE. Fans / heater 87 are 8 AWG: receptacle for 8 AWG TBD (check the TE range).'),
    ('FASTON 6.35 receptacle, 18-14 AWG', '42281-1', 'OWN 20 + BUY ~7', 'Mini ISO 85 / 86 (12) + heater 87a (1) + micro 6.3 load blades (~14). qty_ordered 20.'),
    ('4.8 mm receptacle (micro coil blades)', 'TBD', '-', 'TBD: TE 4.8 x 0.8 receptacle for 18-20 AWG - pick in detail work.'),
    ('2.8 mm receptacle (mini fuse)', 'TBD', '-', 'TBD: 880398-2 is a candidate (plan S12), fit on an ATM blade not confirmed.'),
    ('Tubular lug 10 mm2 M5 (8-10 AWG)', 'Klauke 2R5', 'BUY %d' % (n_used - 1 - n_12awg + 2 + 1),
     'AMI outputs and relay feeds on 8-10 AWG, the 2 LOGIC feeds, the battery block AMI out. All sit under the deck on a standoff.'),
    ('Ring lug M5 for 12 AWG (EFI, STR relay feeds)', 'TBD', 'BUY %d' % n_12awg,
     'TBD: a TE PIDG / Solistrand ring tongue for 12-10 AWG with an M5 hole - not checked against the TE catalog yet. Klauke 2R5 is for 10 mm2 and too big for 12 AWG.'),
    ('Tubular lug 16 mm2 M5 (J/B1 HOT, 6 AWG)', 'Klauke 3R5', 'BUY 1', 'b 13, l 26, d4 8.5, hole 5.5 (Klauke table, Kempston Controls 3R10.pdf).'),
    ('Tubular lug 50 mm2 M8 (1/0 input)', 'Klauke 6R8', 'BUY 1', 'b 20, l 47, hole 8.4 (RS 398-3015 listing).'),
    ('Ring lug M6, 10 AWG (battery block: feed in, relay 3, relay 5)', 'TBD', 'BUY 3', 'TBD: Klauke R series M6 for 6 mm2 - not checked against the Klauke sheet yet.'),
    ('Brass hex standoff M5 female-female, 8 AF, 40 long', 'TBD', 'BUY %d' % n_pos,
     'NEW in rev 4: carries each AMI output (and relay feed) from the pad down to its lug under the deck; its hex sits in a printed hex hole so it cannot turn. '
     'TBD: not a TE line and none of the approved suppliers lists standoffs (R38 step 4) - pick a brass one from a maker sheet (e.g. Keystone / Wurth) in detail work. '
     'Current: brass C360 hex, ~36 mm2 after the thread, 40 mm long = about 0.07 mOhm, 0.25 W at 60 A.'),
    ('Brass hex standoff M5 female-female, 8 AF, 25 long', 'TBD', 'BUY 2', 'LOGIC strip feeds (Bus 1 / Bus 2), same pick as above.'),
    ('Set screw M5 x 12 A2 (stud on top of each standoff)', 'ISO 4026 M5x12', 'BUY %d' % n_pos, 'Screws into the standoff top through the pad; AMI ear + Keps nut on it, 4 Nm max (AMI sheet).'),
    ('Hex bolt M5 x 10 A2 (lug under each standoff)', 'ISO 4017 M5x10', 'BUY %d' % (n_used + 2), 'One per used AMI output + the 2 LOGIC feeds.'),
    ('Hex bolt M5 x 16 A2 + Keps nut', 'ISO 4017 M5x16 + DIN 6923 M5', 'BUY %d' % (n_pos + 2 + 2),
     'AMI input studs on the bars (POWER %d, battery 2) + the 2 LOGIC strip bolts (head on top). Head captured in a printed hex pocket.' % n_pos),
    ('Keps nut M5 A2', 'DIN 6923 M5', 'BUY %d' % (n_pos + 1), 'AMI output nuts.'),
    ('Hex bolt M8 x 20 / M6 x 16 A2 + nut + washer', 'ISO 4017 + ISO 4032 + ISO 7089', 'BUY 1 + 3', 'POWER 1/0 input (M8); battery feed stud + the 2 HCR150 flange bolts (M6, nut captured under the floor).'),
    ('Brass compression limiter, M5 / M6', 'TBD (OD 8, ID 5.3, L 6 / OD 10, ID 6.5, L 4.6)', 'BUY 10 / 2', '8 glove-box ears + 2 battery tabs / the 2 HCR150 flange bolts.'),
    ('Power bars, output pads, logic strips', 'tinned copper flat bar - see "Copper"', 'BUY 3 stock bars', 'Off the shelf; cut and drill only (R76).'),
    ('Bases and covers', 'PA12, powder-bed (MJF / SLS)', 'print 6 parts', 'See "Printed parts". No screws, no heat-set inserts: the covers snap on.'),
]

imgs = {f: c for f, c in [
    ('fusebox_render_iso_closed.png', 'Closed: rounded snap-on covers with every relay and fuse name etched in the top. LOGIC (left) and POWER on their corner legs; the 1/0 enters the POWER box end through an open notch.'),
    ('fusebox_render_iso_open.png', 'Covers off, loaded. POWER: six Mini ISO relays inboard, the AMI bar outboard. LOGIC: mini fuses and micro relays.'),
    ('fusebox_render_iso_empty.png', 'EMPTY - no relays or fuses, so you can see every terminal slot. Copper bar and pads are left in to show where they sit.'),
    ('fusebox_render_top_empty.png', 'EMPTY, top view: the relay, mini-fuse and micro-relay cavities.'),
    ('fusebox_render_under.png', 'Underneath (the open bottom): every AMI output lug on a brass standoff under the deck, cables leaving straight; '
                                 'the relay feeds turning up round their printed saddles; LOGIC feeds leaving straight out the rear.'),
    ('fusebox_render_power_bends.png', 'POWER box from below, relay feeds: each one runs straight off its lug, then one 90 deg bend round a printed R16 saddle into its relay terminal 30.'),
    ('fusebox_render_iso_open_rear.png', 'From the rear / outboard corner.'),
    ('battrelay_render_iso_closed.png', 'Battery relay block closed: Blue Sea 7720-style low cover, labels, two tabs (one each long side), cables only at the open ends.'),
    ('battrelay_render_iso_open.png', 'Battery block, cover off: feed in at the -x end -> M6 stud -> AMI 40 -> one straight jumper -> HCR150 terminal 3; terminal 5 straight out to the pump; coil lead along the front.'),
    ('battrelay_render_iso_empty.png', 'Battery block base EMPTY (no relay, no fuse): relay platform with the two flange-bolt bosses, pedestal under the bar and pad, open ends.'),
] if os.path.exists(os.path.join(src_dir, f))}

CSS = """
:root{--bg:#fafaf8;--fg:#1d1d1b;--mut:#666;--line:#ddd;--acc:#b35c00;--card:#fff;--ok:#2e7d32;--bad:#c62828}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#1b1b1a;--fg:#ecece8;--mut:#a0a09a;--line:#3a3a38;--acc:#f0a050;--card:#242423;--ok:#81c784;--bad:#ef9a9a}}
:root[data-theme=dark]{--bg:#1b1b1a;--fg:#ecece8;--mut:#a0a09a;--line:#3a3a38;--acc:#f0a050;--card:#242423;--ok:#81c784;--bad:#ef9a9a}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif;margin:0}
main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:24px;margin:8px 0 2px}h2{font-size:18px;margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
.mut{color:var(--mut)}table{border-collapse:collapse;width:100%;font-size:13.5px}
td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
.wrap{overflow-x:auto}figure{margin:12px 0}img{max-width:100%;border:1px solid var(--line);border-radius:6px;background:#888}
figcaption{color:var(--mut);font-size:13px}.kpi{display:flex;flex-wrap:wrap;gap:10px}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:150px}
.kpi b{display:block;font-size:20px}ol li,ul li{margin-bottom:6px}h3{font-size:15px;margin:18px 0 6px}a{color:var(--acc)}
.ok{color:var(--ok);font-weight:600}.bad{color:var(--bad);font-weight:600}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
"""


def fig(f):
    if f in imgs:
        h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (E(f), E(imgs[f]), E(imgs[f])))


def size(k):
    b = boxes.get(k, {})
    return '%.0f x %.0f x %.1f' % (b.get('L', 0), b.get('D', 0), b.get('H', 0))


PW, LG = boxes.get('POWER', {}), boxes.get('LOGIC', {})
h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
     '<title>ST185 Fuse Box CAD</title><style>%s</style></head><body><main>' % CSS,
     '<h1>ST185 fuse + relay boxes - CAD rev 4</h1>',
     '<p class="mut">Claude Code, 2026-10-14. Rev 4 is your review of rev 3 (8 points, all binding), answered below. Same rules as before: PA12 '
     'powder-bed print (R73), two glove-box boxes + a trunk relay block (R75), tinned copper stock cut and drilled only (R76). Fusion: the same document, '
     'renamed <code>ST185_fusebox_rev4</code> (was rev 3; no new document, R74). Model files (STEP / STL / f3d) are local, untracked, in '
     '<code>cad/fusebox/</code> of the main checkout. Build: <code>cad/fusebox/src/</code>.</p>',
     '<div class="kpi">',
     '<div>LOGIC box<b>%s</b><span class="mut">mm L x D x H (was 79 x 181 x 85)</span></div>' % size('LOGIC'),
     '<div>POWER box<b>%s</b><span class="mut">mm L x D x H (was 185.5 x 181 x 85)</span></div>' % size('POWER'),
     '<div>Battery block<b>%s</b><span class="mut">mm (was 150 x 110 x 53.5)</span></div>' % size('BATTRELAY'),
     '<div>Printed pieces<b>2 + 2 + 2</b><span class="mut">base + cover per box (rev 3: 3 + 3 + 2)</span></div>',
     '</div>']
fig('fusebox_render_iso_closed.png')
fig('fusebox_render_iso_open.png')

# ------------------------------------------------------------------ the review, point by point
bends = rep.get('bends', [])
h.append('<h2>Your review, point by point</h2><ol>')
h.append('<li><b>Too tall - bottoms left open.</b> No tray floor and no side slot any more. Each box is now a <b>base</b> (the deck, standing on four corner legs) '
         'and a <b>cover</b>. Mount face to cover top: POWER %.1f mm (was 85), LOGIC %.1f mm (was 85). Under the POWER deck is %.0f mm of open space and under '
         'the LOGIC deck %.0f mm: that is the room the wires need to bend at your radius (point 4) - the 8 AWG relay feeds set the POWER number. '
         'The printed cover itself is only about 42 mm tall.</li>' % (PW.get('H', 0), LG.get('H', 0), PW.get('z_d', 0), LG.get('z_d', 0)))
h.append('<li><b>Rounded, modern.</b> Covers have R13 corners and R5 rounded top edges all round (no sharp edge anywhere on top), bases R10 corners, round legs; '
         'the powder-bed freedom is used for the printed cable saddles and the outboard comb under the POWER deck, which also set the bend radius.</li>')
h.append('<li><b>Snap-on covers.</b> Four cantilever tongues per cover (slotted into the skirt), each with a half-round catch that drops into a pocket in the base. '
         'Off: push a small screwdriver into the slot beside a tongue. The battery block snaps the same way (a screw-down was allowed there; not needed).</li>')
h.append('<li><b>Bend radius on every cable.</b> Every heavy cable now leaves its lug dead straight along the lug axis - the AMI output lugs moved under the deck '
         'onto brass standoffs, so no cable is bent off a lug inside a box. The only in-box bends are the six relay feeds (AMI to relay terminal 30): one 90 deg bend each, '
         'wrapped round a printed R16 saddle. Table below.</li>')
h.append('<li><b>Empty renders.</b> Added: both glove-box boxes and the battery block with no relays or fuses, iso and top, plus an underside view.</li>')
h.append('<li><b>Etched labels.</b> Every relay, fuse and spare position has its name etched 0.6 mm into the cover top, right above it '
         '(%d labels on POWER, %d on LOGIC, %d on the battery block). List under "Labels".</li>'
         % tuple(len(rep.get('labels', {}).get(k, [])) for k in ('Power_Cover_PA12_printed', 'Logic_Cover_PA12_printed', 'BattRelay_Cover_PA12_printed')))
h.append('<li><b>Battery block.</b> Modeled after the <b>%s</b>. Why: %s Open design: a low base with rims on the long sides only and both ends open; no cable holes - '
         'cables come in under open notches in the cover ends. <b>Two tabs</b>, one on each long side at mid-length; every cable leaves an end, so nothing crosses a tab. '
         'Re-laid on one straight line so its jumper has no bend at all (point 4).</li>' % (E(S.REFERENCE_BRAND[0]), E(S.REFERENCE_BRAND[1])))
h.append('<li><b>Pieces and wiring.</b> Each box is 2 printed pieces (base, cover); the battery block too. You wire from below: the base is open underneath, so every '
         'terminal cavity, standoff and lug is reachable from the wire side. Crimp, push the terminal up into its cavity until it clicks, bolt the lugs under the deck, '
         'then mount the base, then plug the relays and fuses in from the top and snap the cover on. Full order under "How you build it".</li></ol>')

h.append('<h2>Bend radius check (every cable at every lug, stud and terminal)</h2>'
         '<p>Rule: FAA AC 43.13-1B CHG 1, par. 11-96 aa (p. 11-44/45) - a bundle no tighter than <b>10 x the OD</b> of its largest wire; where a wire breaks out at a terminal '
         'and is <b>suitably supported</b>, <b>3 x OD</b>. No cable maker publishes a bend radius for M22759/16 Tefzel or for SGX battery cable (checked: Thermax / ProWire '
         'M22759/16 sheet, Southwire SPEC 50050, AWC, Prestolite), so this installation rule is used. OD = maximum from the Thermax M22759/16 sheet; 1/0 SGX 13.6 mm. '
         'Gauges from the slot map (ENGINE-ROOM-POWER-REDISTRIBUTION 8.1). "Inside R" is from the model; on the two "bend under the deck" rows it is the most room there is.</p><div class="wrap"><table>'
         '<tr><th>Cable</th><th>AWG</th><th>OD mm</th><th>Path in the box</th><th>Inside R mm</th><th>Needed</th><th></th><th>Note</th></tr>')
for b in bends:
    rr = 'no bend' if b['r_inside'] is None else '%.1f' % b['r_inside']
    need = '%.1f (%s)' % (b['need'], b['rule']) if b['r_inside'] is not None else '-'
    h.append('<tr><td>%s</td><td>%s</td><td>%.2f</td><td>%s</td><td>%s</td><td>%s</td><td class="%s">%s</td><td>%s</td></tr>'
             % (E(b['where']), E(b['awg']), b['od'], E(b['path']), rr, E(need), 'ok' if b['ok'] else 'bad', 'OK' if b['ok'] else 'FAIL', E(b['note'])))
h.append('</table></div><p class="mut">Every cable stub was also checked against every printed part in Fusion: %s. The first bend outside a box is in the harness route: '
         'keep it to the "Note" figure - 3 x OD with a P-clamp or tie each side of the bend, otherwise 10 x OD.</p>'
         % ('no contact' if not rep.get('wire_to_printed_contact') else E(rep['wire_to_printed_contact'])))
fig('fusebox_render_power_bends.png')
fig('fusebox_render_under.png')

h.append('<h2>Empty boxes (terminal slots)</h2>')
fig('fusebox_render_iso_empty.png')
fig('fusebox_render_top_empty.png')

h.append('<h2>How you build it</h2><div class="grid"><div><h3>POWER box (2 printed pieces)</h3><ol>'
         '<li>Press a brass limiter into each of the 4 ears.</li>'
         '<li>Bench, base right way up: lay the bar in its pocket and the 14 pads in theirs. From below, push the M5 x 16 bolts (and the M8 x 20 for the 1/0) up through '
         'the hex head pockets and the bar holes.</li>'
         '<li>From below, slide a brass standoff up each hex hole until it meets its pad; from the top, screw an M5 set screw through the pad into it.</li>'
         '<li>Turn the base over (wire side up). Crimp the relay terminals, push each one up into its cavity until it clicks. Crimp the AMI output cables and '
         'bolt each lug to the bottom of its standoff (M5 x 10; the hex hole holds the standoff). The six relay feeds go lug -> straight -> round their saddle -> into '
         'terminal 30; tie each to its saddle.</li>'
         '<li>Right way up: AMI fuses on the studs, Keps nuts 4 Nm max; 1/0 lug on the M8.</li>'
         '<li>Mount the base in the glove box by its 4 ears (M5 through the limiters); the cables leave underneath between the legs.</li>'
         '<li>Plug the relays and the ACPS fuse in from the top, snap the cover on.</li></ol></div>'
         '<div><h3>LOGIC box (2 printed pieces)</h3><ol>'
         '<li>Limiters in the ears. From below, slide the two strips up into their pockets.</li>'
         '<li>Standoff under each strip end; M5 bolt down from the top (head in its hex pocket) into the standoff; feed lug under the standoff (M5 x 10).</li>'
         '<li>Wire side up: crimp and push in the mini-fuse and micro-relay terminals from below.</li>'
         '<li>Mount by the 4 ears (the two rear legs sit at x 45 / 70 so the Bus 1 / Bus 2 feeds leave the rear straight).</li>'
         '<li>Fuses and micro relays in from the top, snap the cover on.</li></ol></div>'
         '<div><h3>Battery block (2 printed pieces)</h3><ol>'
         '<li>From below, an M6 nut into each of the 2 hex pockets under the relay platform; limiters in the tabs and the 2 flange bosses.</li>'
         '<li>Drop the 3 bolt heads into the pedestal pockets (top), lay the bar and the pad on.</li>'
         '<li>HCR150 on its platform, 2 M6 bolts down through the flange into the captured nuts.</li>'
         '<li>AMI 40 on, jumper (two lugs, one straight 18 mm cable) from the AMI out to terminal 3, pump cable on terminal 5, coil plug on.</li>'
         '<li>Mount by the 2 tabs (passenger side of the trunk, between the rear wall and the battery - Z4), snap the cover on.</li></ol></div></div>'
         '<p class="mut">To service a relay terminal later: unbolt the base\'s ears and lift it - the bottom is open, nothing else holds it.</p>')

h.append('<h2>Battery relay block</h2>')
fig('battrelay_render_iso_closed.png')
fig('battrelay_render_iso_open.png')
fig('battrelay_render_iso_empty.png')

h.append('<h2>Labels (etched in the covers)</h2>')
for k, v in rep.get('labels', {}).items():
    h.append('<p><b>%s:</b> %s</p>' % (E(k.split('_')[0]), E(', '.join(v))))

h.append('<h2>Slot map</h2><div class="wrap"><table><tr><th>Unit</th><th>Position</th><th>Fuse / relay</th><th>Part</th><th>Wire</th></tr>')
for row in ('IN', 'OUT'):
    for i, (nm, a) in enumerate(S.AMI_ROWS[row][:S.AMI_SLOTS[row]]):
        h.append('<tr><td>POWER</td><td>AMI %s-%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (row, i + 1, E(nm if a else 'spare'), 'AMI-%d' % a if a else '-', ('%d AWG' % S.AMI_AWG[nm]) if a else '-'))
for i, nm in enumerate(S.IN_RELAY):
    pn, own = S.RELAY_PN[nm]
    h.append('<tr><td>POWER</td><td>R%d (column %s)</td><td>%s (fed by AMI IN-%d)</td><td>%s</td><td></td></tr>'
             % (i + 1, 'A' if i % 2 == 0 else 'B', E(nm), i + 1, E('%s (%s)' % (pn, own) if pn else '-')))
h.append('<tr><td>POWER</td><td>front of column B</td><td>ACPS mini fuse (heater 87)</td><td>ATM-10</td><td></td></tr>')
for col, (cx, fuses) in S.MINI_COLS.items():
    h.append('<tr><td>LOGIC</td><td>%s (%d)</td><td>%s</td><td>ATM</td><td>feed %d AWG</td></tr>'
             % (col, len(fuses), E(', '.join('%s %s' % (nm, a) if a else 'spare' for nm, a in fuses)), S.FEEDS[col][1]))
k = 0
for c, cx in enumerate(S.MICRO_COLS):
    for r, cy in enumerate(S.MICRO_Y):
        nm, pn, own = S.MICRO_POS[k]
        k += 1
        h.append('<tr><td>LOGIC</td><td>M%d%d</td><td>%s</td><td>%s</td><td></td></tr>' % (c + 1, r + 1, E(nm if pn else 'spare'), E('%s (%s)' % (pn, own) if pn else '-')))
h.append('<tr><td>BATTERY</td><td>F1</td><td>FP fuse 40 A</td><td>AMI-40</td><td>10 AWG</td></tr>'
         '<tr><td>BATTERY</td><td>K1</td><td>k_fp fuel pump relay</td><td>1416010-1 HCR150 (OWN)</td><td>10 AWG</td></tr></table></div>')

h.append('<h2>Printed parts (PA12, powder-bed)</h2><div class="wrap"><table><tr><th>Part</th><th>File (STL + STEP)</th><th>Size mm (x y z, incl. ears / tabs)</th><th>Volume / mass</th><th>What it is</th></tr>')
for n, pr in printed.items():
    sz = ' x '.join('%.1f' % v for v in pr.get('size_mm', [])) or '-'
    unit, rest = n.split('_', 1)
    kind = rest.split('_')[0]
    note = PRINTED_NOTE.get('%s_%s' % (unit, kind), PRINTED_NOTE.get(kind, ''))
    h.append('<tr><td>%s %s</td><td><code>%s.stl</code><br><code>%s.step</code></td><td>%s</td><td>%s cm&sup3; / ~%s g</td><td>%s</td></tr>'
             % (E(unit), E(kind), E(n), E(n), E(sz), E(pr.get('volume_cm3', '-')), E(int(pr.get('mass_g_pa12', 0))), E(note)))
h.append('</table></div><p class="mut">Mass at the HP PA12 density 1.01 g/cm&sup3;. Metal parts are STEP only, plus the whole assembly '
         '(<code>ST185_fusebox_rev4_assembly.step</code>).</p>')

h.append('<h2>Designed for powder-bed printing</h2><ul>'
         '<li><b>Walls:</b> 3 mm base skirt, 6 mm deck plate, 2.5 mm towers, ribs, gussets and cover walls. Nothing under 2.0 mm.</li>'
         '<li><b>No trapped powder:</b> bases are open underneath, covers are open shells; no closed cavity anywhere.</li>'
         '<li><b>Fits:</b> %.2f mm per side printed to printed (cover over base); %.1f mm per side metal in a printed pocket.</li>'
         '<li><b>Snaps:</b> tongue 12 wide, 11 long between two 1.2 slots, half-round catch 2.4, about 0.75 mm of engagement - within what PA12 takes repeatedly.</li>'
         '<li><b>Threads:</b> none printed, and no heat-set inserts now (the covers snap). Every bolt goes into metal: standoffs, nuts, captured heads.</li>'
         '<li><b>Torque into metal:</b> pad, standoff and lug are clamped metal to metal; the hex holes only stop the standoffs and bolt heads turning. '
         'The HCR150 flange clamps onto brass limiters over captured nuts.</li>'
         '<li><b>Heat:</b> PA12 HDT 95 &deg;C at 1.82 MPa. The 1" x 1/4" copper bar is three times the 1/0 copper; bench check at full load with a thermocouple anyway.</li>'
         '<li><b>Live-part spacing (measured in Fusion):</b> AMI pads %.1f mm apart (printed rib between), bar to any output %.1f, 1/0 lug to nearest output %.1f, '
         'output lugs under the deck %.1f, standoffs %.1f; Bus 1 / Bus 2 strips %.1f, their feed lugs %.1f; battery bar to pad %.1f, HCR150 lugs %.1f.</li>'
         '</ul>' % (S.PCLR, S.CLR, live.get('pad_to_pad_min_mm', 0), live.get('bar_to_pad_min_mm', 0), live.get('input_lug_to_pad_min_mm', 0),
                    live.get('under_deck_lug_to_lug_min_mm', 0), live.get('standoff_to_standoff_min_mm', 0), live.get('logic_strip_to_strip_mm', 0),
                    live.get('logic_feed_lug_to_lug_mm', 0), live.get('battrelay_bar_to_pad_mm', 0), live.get('battrelay_relay_lug_to_lug_mm', 0)))
if 'interference' in rep:
    h.append('<p><b>Interference check (all three units, every printed, copper and bought part):</b> %s.</p>'
             % ('none' if not rep['interference'] else E(rep['interference'])))

h.append('<h2>Parts list (OWN / BUY)</h2><p class="mut">Order: on-hand TE list, then TE, then approved suppliers, then others with a reason (R38). '
         '"OWN" counts are qty_ordered from te-on-hand-bom.csv - confirm on the shelf. TBD = not checked against a maker sheet yet. Rev 4 drops the M3 heat-set inserts and lid / deck screws.</p>'
         '<div class="wrap"><table><tr><th>Part</th><th>Part number</th><th>Qty</th><th>Note</th></tr>')
for r in PARTS:
    h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in r))
h.append('</table></div>')

h.append('<h2>Copper - tinned, off the shelf, cut and drilled only (R76)</h2><p>Copper in the model: %d g.</p>' % round(cu_g))
for key in ('bar', 'pad', 'strip'):
    title, opts = S.STOCK[key]
    h.append('<h3>%s</h3><div class="wrap"><table><tr><th></th><th>Part</th><th>Seller / part number</th><th>Size mm (W x T x L)</th><th>Price</th><th>Note</th></tr>' % E(title))
    for (tag, what, pn, size_, price, url, note) in opts:
        h.append('<tr><td>%s</td><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % ('<b>PICK</b>' if tag == 'PICK' else 'runner-up', E(url), E(what), E(pn), E(size_), E(price), E(note)))
    h.append('</table></div>')
h.append('<p class="mut">Ready-made option checked: %s - %s Prices seen 2026-10-14, they move. None is a TE part: TE sells no bar stock (R38 step 4).</p>'
         % (E(S.READY_MADE[0]), E(S.READY_MADE[1])))


def drawing(name, qty, L, Wd, T, holes, stock, note=''):
    """Top-view cut / drill drawing: L along x, Wd across; holes = [(from_end, from_centre_line, dia)]."""
    sc = min(4.0, 640.0 / L)
    pw, ph = L * sc, Wd * sc
    ox, oy = 20, 34
    svg = ['<svg viewBox="0 0 %d %d" width="100%%" style="max-width:%dpx" xmlns="http://www.w3.org/2000/svg" font-family="system-ui" font-size="11">'
           % (pw + 60, ph + 80, pw + 60),
           '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#c9a26b" stroke="currentColor"/>' % (ox, oy, pw, ph)]
    for (a, c, d) in holes:
        svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="var(--bg)" stroke="currentColor"/>' % (ox + a * sc, oy + ph / 2 - c * sc, d * sc / 2))
    svg.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="currentColor"/>' % (ox, oy + ph + 14, ox + pw, oy + ph + 14))
    svg.append('<text x="%.1f" y="%.1f" text-anchor="middle" fill="currentColor">%.1f</text>' % (ox + pw / 2, oy + ph + 28, L))
    svg.append('<text x="%.1f" y="%.1f" fill="currentColor">%.2f wide x %.2f thick</text>' % (ox, 20, Wd, T))
    svg.append('<text x="%.1f" y="%.1f" fill="currentColor">end A</text>' % (ox - 14, oy + ph + 46))
    svg.append('</svg>')
    rows = ''.join('<tr><td>%d</td><td>%.1f</td><td>%s</td><td>%.1f</td></tr>' % (i + 1, a, ('%+.2f' % c) if c else 'on centre', d) for i, (a, c, d) in enumerate(holes))
    h.append('<h3>%s - make %d</h3><p class="mut">From: %s. %s</p>%s<div class="wrap"><table><tr><th>Hole</th><th>mm from end A</th>'
             '<th>mm from the centre line</th><th>Drill dia</th></tr>%s</table></div>'
             % (E(name), qty, E(stock), E(note), '\n'.join(svg), rows))


h.append('<h2>Cut and drill drawings</h2><p class="mut">All holes are plain through holes, deburred, no tapping. Cut square, break the edges. '
         'Re-tin cut ends and holes if you like (optional at 12 V under a cover). End A is the forward (firewall) end in the glove-box boxes, the battery-feed end in the trunk block.</p>')
B = S.BAR
y_off = B['y0']
ins = [(S.AMI_Y0 + i * S.AMI_PITCH - y_off, -S.AMI_IN_OFF, 5.5) for i in range(S.AMI_SLOTS['IN'])]
outs = [(S.AMI_Y0 + i * S.AMI_PITCH - y_off, +S.AMI_IN_OFF, 5.5) for i in range(S.AMI_SLOTS['OUT'])]
drawing('POWER box bar', 1, B['y1'] - B['y0'], B['w'], S.BAR_T, [(S.IN_STUD_Y - y_off, 0.0, 8.5)] + sorted(ins + outs),
        S.STOCK['bar'][1][0][1], 'Hole 1 = 1/0 input (M8 bolt); the rest = AMI input studs (M5 bolts), inboard row at -6.25, outboard row at +6.25.')
drawing('Output pad', n_pos + 1, S.PAD['inner'] + S.PAD['outer'], S.PAD['w'], S.PAD['t'],
        [(S.PAD['inner'], 0.0, 5.5)], S.STOCK['pad'][1][0][1], '14 for the POWER box (2 are spares) + 1 for the battery block. End A faces the bar.')
Rb = S.RB['bar']
drawing('Battery block bar', 1, Rb['x1'] - Rb['x0'], Rb['w'], Rb['t'],
        [(S.RB['x_stud'] - Rb['x0'], 0.0, 6.5), (S.RB['x_ami_in'] - Rb['x0'], 0.0, 5.5)], S.STOCK['bar'][1][0][1],
        'Same stock as the POWER bar. Hole 1 = battery feed (M6), hole 2 = AMI 40 input (M5).')
SF = S.STRIP_FEED
for col, (cx, fuses) in S.MINI_COLS.items():
    Ls = (len(fuses) - 1) * S.MINI['pitch'] + 12 + SF['ext'][col]
    drawing('LOGIC strip %s (%d fuses)' % (col, len(fuses)), 1, Ls, S.STRIP['w'], S.STRIP['t'], [(Ls - SF['hole_from_end'], 0.0, 5.5)],
            S.STOCK['strip'][1][0][1], 'Hole = feed (M5 bolt, head on top, into the standoff below). The fuse-feed connections along the strip are detail work.')

h.append('<h2>Not done yet (detail work, after your OK)</h2><ul>'
         '<li>Terminal cavity shapes, locks / TPA from the TE terminal drawings (cavities are placeholders at the right pin pattern); how each mini fuse picks up its strip.</li>'
         '<li>Part numbers still TBD: brass standoffs, compression limiters, the 12 AWG M5 ring lug, the battery block M6 lugs, an 8 AWG 9.5 receptacle.</li>'
         '<li>Mount face under the glove-box boxes: the legs need a flat face; tell me the panel and I will add the bolt pattern to the route drawing.</li>'
         '<li>The 40 A AMI HTR fuse vs the heater relay\'s 35 A (keep or 30 A) - still your call.</li>'
         '<li>Then drawings, and the harness redraws in OPEN-ITEMS row 108.</li></ul>')
fig('fusebox_render_iso_open_rear.png')
h.append('</main></body></html>')
open(out, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', out)
