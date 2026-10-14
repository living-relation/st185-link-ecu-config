"""Build cad/fusebox/ST185-fusebox-summary.html: one page for Dan - his rev 4 review answered point by point, renders
(closed, open, EMPTY, underneath with and without the belly pans, every cable to the box edge, exploded and step-by-step
install views with numbered callouts), the lid labels, the bend-radius table, the stud lengths, pieces and build order,
slot map, printed parts, parts list, the copper stock picks and cut / drill drawings. Reads spec.py and the build's
fusebox_report.json. Images stay as separate PNGs beside the page.
Claude Code, 2026-10-14 (rev 5: Dan's review of rev 4, lid labels kept as rev 4; rev 4 R79; rev 3 R75; rev 3.1 R76).
    python cad/fusebox/src/summary_html.py <dir with fusebox_report.json + renders> <out html>
"""
import os, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec as S

src_dir, out = sys.argv[1], sys.argv[2]
rep = json.load(open(os.path.join(src_dir, 'fusebox_report.json')))
E = lambda s: html.escape(str(s))

REV4 = {'LOGIC': (79.0, 181.0, 68.9), 'POWER': (172.0, 181.0, 77.8), 'BATTRELAY': (184.0, 92.0, 54.0)}
boxes = rep.get('boxes_mm', {})
live = rep.get('live_clearance', {})
printed = rep.get('printed_parts', {})
mass = {k: v for k, v in rep.get('mass_g', {}).items() if S.BAR_METAL in k}
cu_g = sum(mass.values())
callouts = rep.get('callouts', {})
so = rep.get('standoffs', {})

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
n_in_used = sum(1 for nm, a in S.AMI_ROWS['IN'][:S.AMI_SLOTS['IN']] if a)
n_out_used = sum(1 for nm, a in S.AMI_ROWS['OUT'][:S.AMI_SLOTS['OUT']] if a)
n_used = n_in_used + n_out_used
n_12awg = sum(1 for nm, g in S.AMI_AWG.items() if g == 12)

PRINTED_NOTE = {
    'Power_Base': 'The deck on four angular legs (front and rear faces): 6 mm top plate, 3 mm skirt, cavity towers, standoff and bolt-head bosses, ribs, '
                  'six printed R16 saddles under it; open underneath. Brass limiter in each foot.',
    'Logic_Base': 'Same idea: deck on four angular legs (on the two long sides), strip pockets open underneath, mini-fuse and micro-relay cavities through.',
    'BattRelay_Base': 'Floor plate, rim on the long sides only (both ends open), relay platform with 2 captured M6 nuts + limiters, one ribbed fuse pedestal '
                      'under the bar and pad, a tab on each short end.',
    'Cover': 'Rounded shell, 2.5 mm wall, R13 plan corners, R5 top edges, a bumper band round the bottom and ribs up the walls; 4 snap tongues; '
             'vent slots; every relay and fuse name etched 0.6 deep (the rev 4 labels, unchanged).',
    'Pan': 'NEW: a shallow tray under the open bottom (2.5 mm floor and wall). Its wall slides 4 mm up inside the skirt; 4 tongues catch in pockets '
           'in the skirt. Notches in its wall let the bundles out.',
}

import parts_lists as PL
PARTS_BY_BOX = PL.build()          # per-box parts lists; PL.write() also writes the three CSVs
PL.write(PARTS_BY_BOX)
PART_TOTALS = PL.totals(PARTS_BY_BOX)

CAP = {
    'fusebox_render_iso_closed.png': 'Closed: vent slots in both lids, bumper band and ribs, angular legs; the etched names are the rev 4 labels, unchanged. Yellow = the harness '
                                     'bundles leaving the LOGIC front edge and the POWER inboard end; red = the heavy cables.',
    'fusebox_render_iso_closed_rear.png': 'From the rear / outboard corner: OUT-row cables leave the POWER end in a row right under the lid; Bus 1 / Bus 2 feeds leave the LOGIC rear.',
    'fusebox_render_iso_open.png': 'Covers off, loaded. POWER relays are turned 90 deg from rev 4 (see point 5).',
    'fusebox_render_iso_empty.png': 'EMPTY - no relays or fuses, every terminal slot visible. Copper and standoffs left in to show where they sit.',
    'fusebox_render_top_empty.png': 'EMPTY, top view.',
    'fusebox_render_under_pan.png': 'Underneath with the snap-on belly pans: nothing live can be touched. The bundles leave through notches in the pan wall.',
    'fusebox_render_under_open.png': 'Underneath, pans off: every cable from every terminal, lug and stud, all the way to the box edge.',
    'fusebox_render_power_bends.png': 'POWER from below, relay feeds only: each runs straight off its lug, then one 90 deg bend round a printed R16 saddle into terminal 30.',
    'battrelay_render_iso_closed.png': 'Battery block with its lid (the snap-on cover - it was in rev 4 too, only in the closed view): rev 4 labels, side vents, a tab on each short end.',
    'battrelay_render_iso_closed_rear.png': 'The other side and the +x end: pump cable and coil lead leave the end; the tab sits beside them, not under them.',
    'battrelay_render_iso_open.png': 'Cover off: battery feed -> M6 stud on the bar -> AMI 40 -> straight jumper -> HCR150 terminal 3; terminal 5 straight out to the pump.',
    'battrelay_render_iso_empty.png': 'Base EMPTY: relay platform, the one fuse pedestal, open ends, end tabs.',
    'battrelay_render_under.png': 'Underneath: closed floor (nothing live), the two captured M6 flange nuts (not live), the end tabs.',
    'fusebox_render_top_lid_power.png': 'POWER lid, top view (rev 4 etched names).',
    'fusebox_render_top_lid_logic.png': 'LOGIC lid, top view (rev 4 etched names).',
}
imgs = {f for f in os.listdir(src_dir) if f.endswith('.png')}

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
ol.co{columns:2;column-gap:28px;font-size:13.5px;padding-left:22px}@media (max-width:640px){ol.co{columns:1}}
.num{display:inline-block;min-width:22px;text-align:center;background:#ffd200;color:#141414;border-radius:11px;font-weight:700;font-size:12.5px;padding:0 4px}
"""

h = []


def fig(f, cap=None):
    if f not in imgs:
        return
    cap = cap or CAP.get(f, '')
    h.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption>' % (E(f), E(cap), E(cap)))
    if f in callouts:
        h.append('<ol class="co">%s</ol>' % ''.join('<li value="%d">%s</li>' % (n, E(t)) for (n, x, y, t) in sorted(callouts[f])))
    h.append('</figure>')


def size(k):
    b = boxes.get(k, {})
    return '%.0f x %.0f x %.1f' % (b.get('L', 0), b.get('D', 0), b.get('H', 0))


PW, LGc, BR = boxes.get('POWER', {}), boxes.get('LOGIC', {}), boxes.get('BATTRELAY', {})
SP, SL = so.get('POWER', {}), so.get('LOGIC', {})
h += ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
      '<title>ST185 Fuse Box CAD</title><style>%s</style></head><body><main>' % CSS,
      '<h1>ST185 fuse + relay boxes - CAD rev 5</h1>',
      '<p class="mut">Claude Code, 2026-10-14. Rev 5 is your review of rev 4 (11 points; point 11 dropped - your correction: the lid labels stay as they were), answered below. Everything else from rev 4 is kept: '
      'open bottoms, snap-on covers, bend radius on every cable, the Blue Sea 7720 look for the battery block, AMI studs, tinned copper stock cut and drilled only '
      '(R73, R75, R76, R79, S27). Fusion: the same document, renamed <code>ST185_fusebox_rev5</code> (no new document, R74). Model files (STEP / STL / f3d) are local, '
      'untracked, in <code>cad/fusebox/</code> of the main checkout. Build: <code>cad/fusebox/src/</code>.</p>',
      '<div class="kpi">',
      '<div>LOGIC box<b>%s</b><span class="mut">mm L x D x H (rev 4: 79 x 181 x 68.9)</span></div>' % size('LOGIC'),
      '<div>POWER box<b>%s</b><span class="mut">mm L x D x H (rev 4: 172 x 181 x 77.8)</span></div>' % size('POWER'),
      '<div>Battery block<b>%s</b><span class="mut">mm, %.0f long with the end tabs (rev 4: 184 x 92 x 54)</span></div>' % (size('BATTRELAY'), BR.get('L_with_tabs', 0)),
      '<div>Printed pieces<b>3 + 3 + 2</b><span class="mut">base + cover + belly pan per glove-box box; base + cover in the trunk</span></div>',
      '</div>']
fig('fusebox_render_iso_closed.png')
fig('battrelay_render_iso_closed.png')

# ------------------------------------------------------------------ the review, point by point
h.append('<h2>Your review, point by point</h2><ol>')
h.append('<li><b>Vent slots on the lids.</b> Rows of 2.6 x 14 mm slots through every glove-box lid, placed clear of the etched names (over the gaps between relay '
         'columns and along the outboard edge). 2.6 mm keeps fingers and tools out. The battery block in the trunk gets its slots in the long side walls instead of the '
         'top, so a spill on the lid does not run in.</li>')
h.append('<li><b>Where is the lid for the little one?</b> It was there in rev 4, but only in the one closed picture - the one you looked at was the open view. Rev 5 shows '
         'it closed from both sides, from underneath, and lifted off in the exploded view (Battery relay block, below).</li>')
h.append('<li><b>Little one: mounts on the short ends.</b> Done - one tab on each short end (M5, brass limiter), set at the rear half of the end so no cable '
         'leaves over a tab (the cables leave the ends at the front half). The tabs on the long sides are gone.</li>')
h.append('<li><b>How the bus bars, terminals and fuses go in.</b> New: an exploded view of each box with numbered parts, and four step pictures for the POWER box '
         '(copper in; turn over, terminals and lugs from below; fuses and relays from the top; pan and cover on). See "How it goes together".</li>')
h.append('<li><b>The rest of the cable routing.</b> Every wire is now drawn from its terminal to the box edge. Each harness wire drops straight out of its cavity, '
         'bends once (3 x OD, tied into its bundle) and runs in a bundle to one exit: the LOGIC front edge (4 bundles) and the POWER inboard end (13 small bundles). '
         'To make that work in the POWER box the relays are turned 90 deg: now no harness wire ever has to cross a relay feed. The bar moved 8.5 mm outboard for it. '
         'Heavy cables: OUT row and the 1/0 out the outboard end, Bus feeds out the LOGIC rear. Table and pictures under "Cable routing".</li>')
h.append('<li><b>More rugged.</b> Bumper band round the bottom of every lid, vertical ribs up the walls, angular legs (point 9), chamfered tabs, the battery block\'s two '
         'risers joined into one ribbed fuse pedestal.</li>')
h.append('<li><b>Why were the studs underneath so long?</b> They are brass standoffs that carry each AMI fuse output down to a cable lug under the deck, so the cable '
         'can leave its lug dead straight (your bend-radius rule). In rev 4 every lug sat at the bottom, so every standoff was 40 mm (25 in LOGIC). Rev 5 makes each one only '
         'as long as its cable needs:<ul>'
         '<li><b>OUT row (%d) and the 2 LOGIC feeds: 12 mm.</b> Those cables run straight out of the box, so the lug now sits right under the deck '
         '(lug at %.1f mm, just under the deck plate at %.1f).</li>'
         '<li><b>IN row (%d, the relay feeds): still %.0f mm - that is what the stack needs.</b> Each feed has to turn up into its relay\'s terminal 30 from below. '
         'Bottom up: lug at %.1f mm (just above the new belly pan), the R16 bend round its saddle (8 AWG needs 3 x 5.13 = 15.4) up to the deck underside at %.0f, '
         'then the terminal cavity, %.1f mm, to the pad at %.1f. %.1f - %.1f - 2 mm of lug = %.0f mm. Shorter only if the 8 AWG feeds bend tighter than your rule.</li></ul></li>'
         % (S.AMI_SLOTS['OUT'], SP.get('out_lug_z', 0), SP.get('plate_bottom', 0), S.AMI_SLOTS['IN'], SP.get('IN', 0), SP.get('in_lug_z', 0),
            SP.get('z_d', 0), SP.get('pad_bottom', 0) - SP.get('z_d', 0), SP.get('pad_bottom', 0), SP.get('pad_bottom', 0), SP.get('in_lug_z', 0), SP.get('IN', 0)))
h.append('<li><b>What are the other 2 parts on the smallest box?</b> The two grey blocks are <b>printed risers (pedestals)</b>, part of the base. The first carries the '
         '<b>copper bar</b> with the battery stud (M6, battery feed in) and the fuse\'s input stud; the second carries the <b>copper pad</b> with the fuse\'s output stud. They lift '
         'the AMI fuse so its output lug sits level with the relay\'s terminal 3, so the jumper is one straight piece of cable. In rev 5 they are one ribbed block (the fuse '
         'pedestal) and they are numbered in the exploded view: 5 bar, 6 pad, 7 pedestal.</li>')
h.append('<li><b>No more feet - angular legs.</b> Each leg is now a hollow tapered buttress on a skirt face (24 wide at the foot, 16 at the top, outer face sloping '
         'out to the foot), with a flat foot and the M5 hole outside it. POWER: on the front and rear faces; LOGIC: on its two long sides, so the front edge and rear '
         'stay clear for cables. Open underneath (no trapped powder).</li>')
h.append('<li><b>Snap-on covers for everything live underneath.</b> New belly pan under each glove-box box: a 2.5 mm PA12 tray whose wall slides 4 mm up inside '
         'the skirt and catches with 4 tongues. It covers every lug, standoff, bolt head and terminal crimp; nearest live part to the pan: %.1f mm. Cables leave '
         'through notches in its wall. To make room under the IN-row bolt heads the boxes grew %.1f (POWER) and %.1f mm (LOGIC) in height. The battery block already '
         'had a closed floor (nothing live underneath).</li>' % (live.get('pan_to_nearest_live_power_mm', 0), PW.get('H', 0) - REV4['POWER'][2], LGc.get('H', 0) - REV4['LOGIC'][2]))
h.append('<li><b>Lid labels:</b> unchanged - the rev 4 etched names (your correction: they were fine; the numbers / legend comment was about a route drawing).</li></ol>')

h.append('<h2>Lids, top view</h2>')
fig('fusebox_render_top_lid_power.png')
fig('fusebox_render_top_lid_logic.png')
h.append('<h3>Labels (etched in the covers)</h3>')
for k, v in rep.get('labels', {}).items():
    h.append('<p><b>%s:</b> %s</p>' % (E(k.split('_')[0]), E(', '.join(v))))

# ------------------------------------------------------------------ cable routing
h.append('<h2>Cable routing (point 5)</h2><p>Yellow = harness wires (each terminal\'s own wire), red = heavy cables. Gauges here follow the fuse rating '
         '(2-5 A 20 AWG, 7.5-10 A 18, 15 A 16, 20 A 12; relay 87 = its feed; coils 20) - the harness drawings set the real gauge. Every bundle runs where no other cable '
         'runs and leaves at one edge. Bundle size = 1.2 x the root of the summed squared ODs.</p>')
fig('fusebox_render_under_open.png')
fig('fusebox_render_routing_power.png', 'POWER box, wiring only, from below.')
fig('fusebox_render_routing_logic.png', 'LOGIC box, wiring only, from below.')
fig('fusebox_render_under_pan.png')
for bx, edge in (('POWER', 'inboard end, at y'), ('LOGIC', 'front edge, at x')):
    h.append('<h3>%s bundles (leave the %s)</h3><div class="wrap"><table><tr><th>At</th><th>Wires</th><th>Bundle mm</th><th>Spare room under the deck mm</th><th>Which</th></tr>' % (bx, edge))
    for ln in rep.get('lanes', {}).get(bx, []):
        h.append('<tr><td>%.0f</td><td>%d</td><td>%.1f</td><td>%.1f</td><td>%s</td></tr>' % (ln['at'], ln['wires'], ln['d'], ln['room'], E(', '.join(ln['what']))))
    h.append('</table></div>')

# ------------------------------------------------------------------ assembly
h.append('<h2>How it goes together (point 4)</h2>')
fig('fusebox_power_explode.png', 'POWER box, exploded.')
fig('fusebox_power_step1.png', 'Step 1 - base right way up: copper and standoffs in.')
fig('fusebox_power_step2.png', 'Step 2 - turned over (wire side up): terminals, lugs and bundles.')
fig('fusebox_power_step3.png', 'Step 3 - right way up: fuses, relays, the 1/0.')
fig('fusebox_power_step4.png', 'Step 4 - mount it, then pan and cover snap on.')
fig('fusebox_logic_explode.png', 'LOGIC box, exploded.')
h.append('<div class="grid"><div><h3>POWER box (3 printed pieces)</h3><ol>'
         '<li>Press a brass limiter into each of the 4 feet.</li>'
         '<li>Base right way up: lay the bar and the 14 pads in their pockets. From below, push the M5 x 16 bolts (and the M8 x 20 for the 1/0) up through the hex head '
         'pockets and the bar holes. Slide a standoff up each hex hole (40 mm in the IN row, 12 mm in the OUT row) and screw a set screw down through each pad into it.</li>'
         '<li>Turn the base over. Crimp the relay terminals, push each one up into its cavity until it clicks, and tie the wires into their bundles (they leave the inboard '
         'end). Bolt the AMI output lugs under their standoffs (M5 x 10 IN row, M5 x 8 OUT row); each relay feed goes lug -> straight -> round its saddle -> terminal 30.</li>'
         '<li>Right way up: AMI fuses on the studs, Keps nuts 4 Nm max; 1/0 lug on the M8.</li>'
         '<li>Mount the base by its 4 feet, snap the belly pan up into the skirt, plug the relays and the ACPS fuse in, snap the cover on.</li></ol></div>'
         '<div><h3>LOGIC box (3 printed pieces)</h3><ol>'
         '<li>Limiters in the feet. From below, slide the two strips up into their pockets.</li>'
         '<li>12 mm standoff under each strip end; M5 x 8 strip bolt down from the top (head in its pocket) into the standoff; feed lug under it (M5 x 8).</li>'
         '<li>Wire side up: crimp and push in the mini-fuse and micro-relay terminals; tie each column\'s wires into its bundle (front edge).</li>'
         '<li>Mount by the 4 feet (long sides), snap the pan on, fuses and micro relays in, snap the cover on.</li></ol></div>'
         '<div><h3>Battery block (2 printed pieces)</h3><ol>'
         '<li>From below, an M6 nut into each of the 2 hex pockets under the relay platform; limiters in the end tabs and the 2 flange bosses.</li>'
         '<li>Drop the 3 bolt heads into the fuse pedestal pockets (top), lay the bar and the pad on.</li>'
         '<li>HCR150 on its platform, 2 M6 bolts down through the flange into the captured nuts.</li>'
         '<li>AMI 40 on, jumper (two lugs, one straight 18 mm cable) from the AMI out to terminal 3, pump cable on terminal 5, coil plug on.</li>'
         '<li>Mount by the 2 end tabs (passenger side of the trunk, between the rear wall and the battery - Z4), snap the cover on.</li></ol></div></div>'
         '<p class="mut">To service a terminal later: unsnap the pan - every cavity is right there.</p>')

# ------------------------------------------------------------------ bends
bends = rep.get('bends', [])
h.append('<h2>Bend radius check (every cable at every lug, stud and terminal)</h2>'
         '<p>Rule: FAA AC 43.13-1B CHG 1, par. 11-96 aa (p. 11-44/45) - a bundle no tighter than <b>10 x the OD</b> of its largest wire; where a wire breaks out at a terminal '
         'and is <b>suitably supported</b>, <b>3 x OD</b>. No cable maker publishes a bend radius for M22759/16 Tefzel or for SGX battery cable (checked: Thermax / ProWire '
         'M22759/16 sheet, Southwire SPEC 50050, AWC, Prestolite), so this installation rule is used. OD = maximum from the Thermax M22759/16 sheet; 1/0 SGX 13.6 mm.</p><div class="wrap"><table>'
         '<tr><th>Cable</th><th>AWG</th><th>OD mm</th><th>Path in the box</th><th>Inside R mm</th><th>Needed</th><th></th><th>Note</th></tr>')
for b in bends:
    rr = 'no bend' if b['r_inside'] is None else '%.1f' % b['r_inside']
    need = '%.1f (%s)' % (b['need'], b['rule']) if b['r_inside'] is not None else '-'
    h.append('<tr><td>%s</td><td>%s</td><td>%.2f</td><td>%s</td><td>%s</td><td>%s</td><td class="%s">%s</td><td>%s</td></tr>'
             % (E(b['where']), E(b['awg']), b['od'], E(b['path']), rr, E(need), 'ok' if b['ok'] else 'bad', 'OK' if b['ok'] else 'FAIL', E(b['note'])))
h.append('</table></div><p class="mut">Every cable (heavy and harness) was also checked against every printed part in Fusion: %s. The first bend outside a box is in the harness route: '
         'keep it to the "Note" figure - 3 x OD with a P-clamp or tie each side of the bend, otherwise 10 x OD.</p>'
         % ('no contact' if not rep.get('wire_to_printed_contact') else E(rep['wire_to_printed_contact'])))
fig('fusebox_render_power_bends.png')

h.append('<h2>Empty boxes (terminal slots)</h2>')
fig('fusebox_render_iso_empty.png')
fig('fusebox_render_top_empty.png')
fig('fusebox_render_iso_open.png')
fig('fusebox_render_iso_closed_rear.png')

# ------------------------------------------------------------------ battery block
h.append('<h2>Battery relay block</h2>')
fig('battrelay_explode.png', 'Battery block, exploded: the lid (1) and every part, numbered.')
fig('battrelay_render_iso_closed_rear.png')
fig('battrelay_render_under.png')
fig('battrelay_render_iso_open.png')
fig('battrelay_render_iso_empty.png')
h.append('<h3>Style (Z9: your pick, S27) - %s</h3><p>%s</p><div class="wrap"><table><tr><th>You asked for</th><th>How the block meets it</th></tr>'
         '<tr><td>Open frame</td><td>Floor plate, rims on the two long sides only, both ends open - the cover is the only enclosure.</td></tr>'
         '<tr><td>Snap or screw lid</td><td>Snap: 4 cantilever tongues into pockets in the side rims (no screws, no inserts).</td></tr>'
         '<tr><td>2 tabs, on the short ends (rev 5)</td><td>One tab on each end at y %.0f (rear half), M5 through a brass limiter.</td></tr>'
         '<tr><td>No cable over a tab</td><td>Battery feed in at the -x end, pump cable and coil lead out at the +x end, all at the front half; the tabs sit at the rear half.</td></tr>'
         '<tr><td>No cable holes</td><td>Cables pass under open notches in the cover ends (the 7720 breakout idea); the base has no holes for cables.</td></tr></table></div>'
         % (E(S.REFERENCE_BRAND[0]), E(S.REFERENCE_BRAND[1]), S.RB['tab_y']))

# ------------------------------------------------------------------ slot map
h.append('<h2>Slot map</h2><div class="wrap"><table><tr><th>Unit</th><th>Position</th><th>Fuse / relay</th><th>Part</th><th>Wire</th></tr>')
for row in ('IN', 'OUT'):
    for i, (nm, a) in enumerate(S.AMI_ROWS[row][:S.AMI_SLOTS[row]]):
        h.append('<tr><td>POWER</td><td>AMI %s-%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (row, i + 1, E(nm if a else 'spare'), 'AMI-%d' % a if a else '-', ('%d AWG' % S.AMI_AWG[nm]) if a else '-'))
for i, nm in enumerate(S.IN_RELAY):
    pn, own = S.RELAY_PN[nm]
    h.append('<tr><td>POWER</td><td>R%d (column %s)</td><td>%s (fed by AMI IN-%d)</td><td>%s</td><td></td></tr>'
             % (i + 1, 'A' if i % 2 == 0 else 'B', E(nm), i + 1, E('%s (%s)' % (pn, own) if pn else '-')))
h.append('<tr><td>POWER</td><td>front of column B</td><td>ACPS mini fuse (heater 87)</td><td>ATM-10</td><td>%d AWG</td></tr>' % S.ACPS_AWG)
n = 0
for col, (cx, fuses) in S.MINI_COLS.items():
    for nm, a in fuses:
        n += 1
        h.append('<tr><td>LOGIC</td><td>%s-%d</td><td>%s (%s)</td><td>%s</td><td>%s</td></tr>'
                 % (col, n if col == 'BUS1' else n - len(S.MINI_COLS['BUS1'][1]), E(nm if a else 'spare'), 'Bus 1' if col == 'BUS1' else 'Bus 2', ('ATM-%g' % a) if a else '-', ('%d AWG' % S.MINI_AWG[a]) if a else '-'))
k = 0
for c, cx in enumerate(S.MICRO_COLS):
    for r, cy in enumerate(S.MICRO_Y):
        nm, pn, own = S.MICRO_POS[k]
        k += 1
        h.append('<tr><td>LOGIC</td><td>M%d%d</td><td>%s</td><td>%s</td><td></td></tr>' % (c + 1, r + 1, E(nm if pn else 'spare'), E('%s (%s)' % (pn, own) if pn else '-')))
h.append('<tr><td>BATTERY</td><td>F1</td><td>FP fuse 40 A</td><td>AMI-40</td><td>10 AWG</td></tr>'
         '<tr><td>BATTERY</td><td>K1</td><td>k_fp fuel pump relay</td><td>1416010-1 HCR150 (OWN)</td><td>10 AWG</td></tr></table></div>')

# ------------------------------------------------------------------ printed parts
h.append('<h2>Printed parts (PA12, powder-bed)</h2><div class="wrap"><table><tr><th>Part</th><th>File (STL + STEP)</th><th>Size mm (x y z, incl. legs / tabs)</th><th>Volume / mass</th><th>What it is</th></tr>')
for nme, pr in printed.items():
    sz = ' x '.join('%.1f' % v for v in pr.get('size_mm', [])) or '-'
    unit, rest = nme.split('_', 1)
    kind = rest.split('_')[0]
    note = PRINTED_NOTE.get('%s_%s' % (unit, kind), PRINTED_NOTE.get(kind, ''))
    h.append('<tr><td>%s %s</td><td><code>%s.stl</code><br><code>%s.step</code></td><td>%s</td><td>%s cm&sup3; / ~%s g</td><td>%s</td></tr>'
             % (E(unit), E(kind), E(nme), E(nme), E(sz), E(pr.get('volume_cm3', '-')), E(int(pr.get('mass_g_pa12', 0))), E(note)))
h.append('</table></div><p class="mut">Mass at the HP PA12 density 1.01 g/cm&sup3;. Metal parts are STEP only, plus the whole assembly '
         '(<code>ST185_fusebox_rev5_assembly.step</code>).</p>')

h.append('<h2>Designed for powder-bed printing</h2><ul>'
         '<li><b>Walls:</b> 3 mm base skirt, 6 mm deck plate, 2.5 mm towers, ribs, cover and pan walls, 3 mm leg walls. Nothing under 2.0 mm.</li>'
         '<li><b>No trapped powder:</b> bases, legs and pans are open, covers are open shells; no closed cavity anywhere.</li>'
         '<li><b>Fits:</b> %.2f mm per side printed to printed (cover over base, pan inside the skirt); %.1f mm per side metal in a printed pocket.</li>'
         '<li><b>Snaps:</b> tongue 12 wide, 11 long between two 1.2 slots, half-round catch 2.4 - covers and pans alike.</li>'
         '<li><b>Threads:</b> none printed, no heat-set inserts. Every bolt goes into metal: standoffs, nuts, captured heads.</li>'
         '<li><b>Heat:</b> PA12 HDT 95 &deg;C at 1.82 MPa. The 1" x 1/4" copper bar is three times the 1/0 copper; bench check at full load with a thermocouple anyway. '
         'The vent slots let the relay coil heat out.</li>'
         '<li><b>Live-part spacing (measured in Fusion):</b> AMI pads %.1f mm apart, bar to any output %.1f, 1/0 lug to nearest output %.1f, '
         'output lugs %.1f, standoffs %.1f; Bus 1 / Bus 2 strips %.1f, their feed lugs %.1f; battery bar to pad %.1f, HCR150 lugs %.1f; belly pan to nearest live part %.1f.</li>'
         '</ul>' % (S.PCLR, S.CLR, live.get('pad_to_pad_min_mm', 0), live.get('bar_to_pad_min_mm', 0), live.get('input_lug_to_pad_min_mm', 0),
                    live.get('under_deck_lug_to_lug_min_mm', 0), live.get('standoff_to_standoff_min_mm', 0), live.get('logic_strip_to_strip_mm', 0),
                    live.get('logic_feed_lug_to_lug_mm', 0), live.get('battrelay_bar_to_pad_mm', 0), live.get('battrelay_relay_lug_to_lug_mm', 0),
                    live.get('pan_to_nearest_live_power_mm', 0)))
if 'interference' in rep:
    h.append('<p><b>Interference check (all three units, every printed, copper and bought part):</b> %s.</p>'
             % ('none' if not rep['interference'] else E(rep['interference'])))

h.append('<h2>Parts lists (one per box, OWN / BUY)</h2><p class="mut">Order (R38): on-hand TE list, then TE, then the approved suppliers, then others with a reason. '
         'Every part number below was checked against a maker sheet or listing (the "Checked against" column says which); TBD says why. "OWN" = on the shelf, '
         'qty_ordered from te-on-hand-bom.csv, handed out box by box (confirm on the shelf). Prices: seen = read on a listing 2026-10-14, est = typical price, '
         'not checked; both move. Spares are included in the quantity (10 %, at least 2, on small parts). The same lines are in the CSVs beside this page and the '
         'BUY lines are in the repo buy list (docs/harness/NEED-TO-BUY.md).</p>')
for box, fn in PL.FILES.items():
    rows_ = PARTS_BY_BOX[box]
    h.append('<h3>%s - <a href="%s">%s</a> - est. $%.2f to buy</h3><div class="wrap"><table><tr><th>Group</th><th>Item</th><th>Part number</th><th>Maker</th>'
             '<th>Need + spare</th><th>OWN</th><th>BUY</th><th>Unit $</th><th>Checked against / note</th></tr>' % (E(PL.BOX_NAME[box]), E(fn), E(fn), PART_TOTALS[box]))
    for r in rows_:
        pn = '<a href="%s">%s</a>' % (E(r['source_url']), E(r['part_number'])) if r['source_url'] else E(r['part_number'])
        unit = ('%s <span class="mut">%s</span>' % (E(r['unit_usd']), E(r['price_basis'].split(' ')[0]))) if r['unit_usd'] else ''
        h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s + %s</td><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s%s</td></tr>' % (
            E(r['group']), E(r['item']), pn, E(r['maker']), E(r['qty_need']), E(r['qty_spare']), E(r['own']), E(r['buy']), unit,
            E(r['checked_against']), ('<br><span class="mut">%s</span>' % E(r['note'])) if r['note'] else ''))
    h.append('</table></div>')
h.append('<p class="mut">Total to buy, all three boxes, est. $%.2f (copper stock $%.2f of it). Not in these lists: the harness wires, 1/0 and the battery cables, '
         'and the k_eps HCR150 beside the POWER box (it is on a loom list).</p>' % (sum(PART_TOTALS.values()), 26.19 + 51.99 + 60.09))

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
            S.STOCK['strip'][1][0][1], 'Hole = feed (M5 bolt, head on top, into the standoff below). Rev 5: longer, so the feed lug sits past the cavity tower. '
            'The fuse-feed connections along the strip are detail work.')

h.append('<h2>Not done yet (detail work, after your OK)</h2><ul>'
         '<li>Terminal cavity shapes, locks / TPA from the TE terminal drawings (cavities are placeholders at the right pin pattern); how each mini fuse picks up its strip.</li>'
         '<li>Part numbers: every TBD is now a checked number (parts lists above). Still open: the M5 / M6 limiter + mount-bolt size (no stocked M5 limiter exists - see the limiter lines), '
         'whether the 12 mm standoffs become 40 mm (Dan: one 40 mm part number), the mount-screw lengths (panel unknown) and how each mini fuse picks up its strip.</li>'
         '<li>Mount face under the glove-box boxes: tell me the panel and I will add the bolt pattern to the route drawing.</li>'
         '<li>Heater fuse vs relay: fixed. The 35 A Power Relay B 1-1904020-2 is superseded at TE; its successor TE Power Relay F4 A 1-1414687-0 carries 40 A NO at 85 C, so the 40 A AMI HTR fuse stays. The CAD pocket still has the Power Relay B outline: check it against the F4 A drawing at the next Fusion rebuild.</li>'
         '<li>Then drawings, and the harness redraws in OPEN-ITEMS row 108 (the harness gauges here are placeholders by fuse rating).</li></ul>')
h.append('</main></body></html>')
open(out, 'w', encoding='utf-8').write('\n'.join(h))
print('wrote', out)
