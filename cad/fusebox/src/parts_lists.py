"""Per-box parts lists for the custom fuse + relay boxes (cad/fusebox).

Writes three CSVs next to the summary page and returns the rows for summary_html.py:
    cad/fusebox/fusebox-parts-power.csv     POWER box (glove box)
    cad/fusebox/fusebox-parts-logic.csv     LOGIC box (glove box)
    cad/fusebox/fusebox-parts-battrelay.csv battery relay block (trunk)
docs/harness/buylist.py reads the BUY lines of these three files (the repo buy list, docs/harness/NEED-TO-BUY.md).

Counts come from spec.py (fuse slots, relay positions, wire gauges) and fusebox_report.json (printed volumes), so a
change to the boxes changes the lists. Every part number is checked against a maker sheet; the 'checked' column says
which. A part with no verified number is TBD and says why. Order (R38): on-hand TE list -> TE -> approved suppliers ->
others with a reason. On-hand quantities are qty_ordered from docs/sourcing/te-on-hand-bom.csv, handed out box by box
(POWER, LOGIC, BATTRELAY) so one shelf quantity is never counted twice. Prices: 'seen' = read on a listing 2026-10-14,
'est' = typical distributor price, not checked (they move).

    python cad/fusebox/src/parts_lists.py
Claude Code, 2026-10-14.
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S

FB = os.path.dirname(HERE)                                   # cad/fusebox
REPO = os.path.dirname(os.path.dirname(FB))
ONHAND_CSV = os.path.join(REPO, 'docs', 'sourcing', 'te-on-hand-bom.csv')
FILES = {'POWER': 'fusebox-parts-power.csv', 'LOGIC': 'fusebox-parts-logic.csv', 'BATTRELAY': 'fusebox-parts-battrelay.csv'}
BOX_NAME = {'POWER': 'POWER box (glove box)', 'LOGIC': 'LOGIC box (glove box)', 'BATTRELAY': 'Battery relay block (trunk)'}
COLS = ['box', 'group', 'item', 'part_number', 'maker', 'description', 'qty_need', 'qty_spare', 'own', 'buy',
        'unit_usd', 'line_usd', 'price_basis', 'source_url', 'checked_against', 'note']

TE = lambda pn: 'https://www.te.com/en/product-%s.html' % pn
DS_V23136 = 'TE data sheet V23136X0000A004 (Power Relay F4 A, 2023-09)'
DS_VCF = 'TE data sheet VCF7-X0000-A001 (Connectors for Mini / Maxi ISO relays)'

try:
    rep = json.load(open(os.path.join(FB, 'fusebox_report.json')))
except OSError:
    rep = {}
PRINT = rep.get('printed_parts', {})
mass = lambda k: PRINT.get(k, {}).get('volume_cm3', 0.0)


def on_hand():
    out = {}
    with open(ONHAND_CSV, encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            out[r['pn']] = int(r['qty_ordered'])
    return out


# ---------------------------------------------------------------- counts from spec.py
IN_USED = [(nm, a) for nm, a in S.AMI_ROWS['IN'][:S.AMI_SLOTS['IN']] if a]
OUT_USED = [(nm, a) for nm, a in S.AMI_ROWS['OUT'][:S.AMI_SLOTS['OUT']] if a]
N_IN, N_OUT = S.AMI_SLOTS['IN'], S.AMI_SLOTS['OUT']
N_POS = N_IN + N_OUT                                        # built positions (14)
mini_by_rating = {}
for col, (x, fuses) in S.MINI_COLS.items():
    for nm, a in fuses:
        if a:
            mini_by_rating[a] = mini_by_rating.get(a, 0) + 1
assert S.ACPS[1] == 10
MICRO_USED = [p for p in S.MICRO_POS if p[1]]
F7_USED = [p for p in S.F7_POS if p[1] and p[0] != 'heater']
n_micro_coil = 2 * len(MICRO_USED)
# micro relay load terminals: 2 on a form A, 3 on a form C (te-on-hand-bom.csv notes: 1 form A NO / 1 form C CO)
MICRO_FORM_C = {'6-1419137-4'}
n_micro_load = sum(3 if p[1] in MICRO_FORM_C else 2 for p in MICRO_USED)


def lug_for(awg):
    """Klauke tubular M5 lug by wire, TE PIDG for 12 AWG (a 10 mm2 barrel is too big for 12 AWG)."""
    return {12: '36161', 10: '2R5', 8: '2R5', 6: '3R5'}[awg]


class Lists:
    def __init__(self):
        self.avail = on_hand()
        self.rows = {b: [] for b in FILES}

    def add(self, box, group, item, pn, maker, desc, need, spare=0, unit=None, basis='est', url='', checked='', note='',
            own_pn=None):
        total = need + spare
        key = own_pn or pn
        own = min(self.avail.get(key, 0), total)
        self.avail[key] = self.avail.get(key, 0) - own
        buy = total - own
        line = round(unit * buy, 2) if unit is not None else ''
        self.rows[box].append(dict(box=box, group=group, item=item, part_number=pn, maker=maker, description=desc,
                                   qty_need=need, qty_spare=spare, own=own, buy=buy,
                                   unit_usd='' if unit is None else '%.2f' % unit, line_usd=line if line == '' else '%.2f' % line,
                                   price_basis=basis if unit is not None else '', source_url=url, checked_against=checked, note=note))


def spare(n, pct=0.1, lo=2):
    return max(lo, int(math.ceil(n * pct)))


def build():
    L = Lists()
    P, G, B = 'POWER', 'LOGIC', 'BATTRELAY'

    # ================================================================ POWER box
    L.add(P, 'Printed', 'Power Base (PA12 MJF)', 'Power_Base_PA12_printed', 'print service', 'Deck on four angular legs, open underneath', 1,
          unit=round(mass('Power_Base_PA12_printed') * 0.10, 2), basis='est', checked='cad/fusebox report volume %.1f cm3 at est. $0.10/cm3' % mass('Power_Base_PA12_printed'))
    L.add(P, 'Printed', 'Power Pan (belly pan, PA12 MJF)', 'Power_Pan_PA12_printed', 'print service', 'Snap-on belly pan, 4 integral tongues (no separate clips)', 1,
          unit=round(mass('Power_Pan_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('Power_Pan_PA12_printed'))
    L.add(P, 'Printed', 'Power Cover (PA12 MJF)', 'Power_Cover_PA12_printed', 'print service', 'Snap-on cover, etched labels, vent slots', 1,
          unit=round(mass('Power_Cover_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('Power_Cover_PA12_printed'))
    L.add(P, 'Copper', 'Power bar 25.4 x 6.35 x 148 mm, tinned', 'MECCANIXITY 12 in x 1 in x 1/4 in tinned flat bar (Amazon B0CGJBRNJX)', 'MECCANIXITY',
          'ONE 305 mm bar: the POWER bar (148 mm) and the battery block bar (36.5 mm) both come from it', 1, unit=26.19, basis='seen',
          url='https://www.amazon.com/dp/B0CGJBRNJX', checked='summary "Copper" section; seller page 2026-10-14',
          note='Cut + drill only (R76): 15 holes, drawing on the summary page. Stock bought here covers BATTRELAY too.')
    L.add(P, 'Copper', 'Output pads 15 x 3 x 17.5 mm, tinned (14 here + 1 in BATTRELAY)', 'Tinned copper bus bar 3 x 15 x 1000 mm C110 (Amazon B09Z7NBLDK)', 'Bopaodao (Amazon)',
          'ONE 1000 mm bar makes all 15 pads (290 mm with kerf)', 1, unit=51.99, basis='seen', url='https://www.amazon.com/dp/B09Z7NBLDK',
          checked='summary "Copper" section; seller page 2026-10-14', note='One drilled hole each (5.5 mm). Stock covers BATTRELAY pad too.')
    # fuses
    r30 = sum(1 for _, a in IN_USED + OUT_USED if a == 30)
    r40 = sum(1 for _, a in IN_USED + OUT_USED if a == 40)
    r50 = sum(1 for _, a in IN_USED + OUT_USED if a == 50)
    r60 = sum(1 for _, a in IN_USED + OUT_USED if a == 60)
    for rating, n in ((30, r30), (40, r40), (50, r50), (60, r60)):
        pn = 'AMI-%d' % rating
        L.add(P, 'Fuses', 'AMI bolt-down fuse %d A' % rating, pn, 'Eaton Bussmann', 'AMI series, 32 VDC, M5 stud ears 9.5 x 0.8 mm', n,
              unit=5.30, basis='seen (AMI-40 / -60 at 5+ on Waytek; -30 / -50 est.)',
              url='https://www.waytekwire.com/product/eaton-s-bussmann-series-ami-40-bolt-down-fuse',
              checked='Waytek AMI-40 / AMI-60 listings; Bussmann AMI sheet (spec.py AMI dims)',
              note='Other maker (R38 step 4): TE sells no bolt-down fuse. ' + ('Slots: ' + ', '.join(nm for nm, a in IN_USED + OUT_USED if a == rating)))
    L.add(P, 'Fuses', 'ACPS mini blade fuse 10 A', 'ATM-10', 'Eaton Bussmann', 'ATM mini blade fuse, blade 2.8 x 0.8 mm', 1, spare=0, unit=0.55, basis='est',
          checked='Littelfuse / Bussmann ATM blade 2.8 x 0.8 mm (ISO 8820-3 mini)', note='Front of relay column B, fed from heater 87.')
    # relays
    L.add(P, 'Relays', 'Heater relay k_htr, 1 form C, 12 V, 680 ohm', '1-1414687-0', 'TE Connectivity',
          'Power Relay F4 A (V23136-A0004-X059), Mini ISO, NO 40 A / NC 30 A at 85 C, silver alloy, coil 90 ohm + 680 ohm resistor', 1, unit=9.0, basis='est',
          url=TE('1-1414687-0'), checked=DS_V23136 + ' p.1: 1 form C limiting continuous current 40/30 A at 85 C; TE page: Active',
          note='REPLACES 1-1904020-2 (Power Relay B V23234-A0001-X032): TE lists it and every V23234 1 form C variant as Superseded. 40 A NO = the 40 A AMI HTR fuse, so the 40 A fuse vs 35 A relay mismatch (row 107) is closed without changing the fuse. Mini ISO pin pattern, 6.3 x 0.8 tabs; check the 28.5 mm pocket against the F4 A drawing.')
    n_14147 = sum(1 for p in F7_USED if p[1] == '1-1414147-0')
    n_13304 = sum(1 for p in F7_USED if p[1] == '1-1393304-0')
    L.add(P, 'Relays', 'Relay k_efi / k_str / k_fan (Maxi ISO F7, 1 form A, 680 ohm)', '1-1414147-0', 'TE Connectivity',
          'Power Relay F7 (V23134-J0052-X429), Maxi ISO, 50 A, 30/87 blades 9.5 x 1.2, 85/86 blades 6.3 x 0.8', n_14147, url=TE('1-1414147-0'),
          checked='TE page + data sheet V23134X0000A002 (F7 Maxi ISO, QC terminals); te-on-hand-bom.csv qty_ordered 3',
          note='On the shelf (R38 step 1). Earlier pages called the F7 "Mini ISO": the data sheet title is "Maxi ISO".')
    L.add(P, 'Relays', 'Relay k_fan2 / power (Maxi ISO F7, bracket, 560 ohm)', '1-1393304-0', 'TE Connectivity',
          'Power Relay F7 (V23134-J1052-X281), Maxi ISO, bracket (cut off or fold flat)', n_13304, url=TE('1-1393304-0'),
          checked='te-on-hand-bom.csv qty_ordered 2; same F7 data sheet')
    # relay terminals
    awg_87 = {'k_efi': S.AMI_AWG['EFI'], 'k_str': S.AMI_AWG['STR'], 'k_fan': S.AMI_AWG['FAN'], 'k_fan2': S.AMI_AWG['FAN2'], 'power': S.AMI_AWG['PWR']}
    n95_12_10 = sum(2 for p in F7_USED if awg_87[p[0]] in (12, 10))
    n95_8 = sum(2 for p in F7_USED if awg_87[p[0]] == 8)
    L.add(P, 'Terminals', 'Maxi relay load receptacle 9.5 x 1.2, 12-10 AWG', '280756-4', 'TE Connectivity',
          'FASTON .375 receptacle, uninsulated, 12-10 AWG (3.31-5.26 mm2), phosphor bronze, tin', n95_12_10, spare(n95_12_10), unit=0.40, basis='est',
          url=TE('280756-4'), checked='TE page (tab 9.53 x 1.22, 12-10 AWG) + ' + DS_VCF + ' (load 3.3-5.3 mm2)', note='30 / 87 of k_efi, k_str, power (12 / 12 / 10 AWG).')
    L.add(P, 'Terminals', 'Maxi relay load receptacle 9.5 x 1.2, 10-7 AWG', '280755-4', 'TE Connectivity',
          'FASTON .375 receptacle, uninsulated, 10-7 AWG (6-10 mm2), tin', n95_8, spare(n95_8), unit=0.50, basis='est', url=TE('280755-4'),
          checked='TE page (tab 9.53 x 1.22, 10-7 AWG) + ' + DS_VCF + ' (load 5.3-13.3 mm2)',
          note='CLOSES the TBD "8 AWG 9.5 receptacle": 30 / 87 of k_fan, k_fan2 (8 AWG).')
    n_f7_coil = 2 * len(F7_USED)
    L.add(P, 'Terminals', 'Relay coil receptacle 6.3 x 0.8, 20-18 AWG (F7 85/86 + heater 85/86)', '1-1393310-8', 'TE Connectivity',
          'Crimp terminal QC .250 (26A1348A) for 0.5-0.8 mm2, brass tin', n_f7_coil + 2, spare(n_f7_coil + 2), unit=0.12, basis='est', url=TE('1-1393310-8'),
          checked=DS_VCF + ' "Selection of fitting crimp terminals": 6.3 x 0.8, 0.5-0.8 mm2 (20-18), coil; TE page: Active',
          note='Coil wires are 20 AWG in spec.py (COIL_AWG). On-hand 42281-1 (18-14 AWG) is too big for 20 AWG, so it is not used here (it goes to the micro relay loads).')
    L.add(P, 'Terminals', 'Heater relay load receptacle 6.3 x 0.8, 10-8 AWG (30, 87, 87a)', '62998-2', 'TE Connectivity',
          'FASTON .250 receptacle, uninsulated, 10-8 AWG (5-8 mm2), brass tin', 3, spare(3), unit=0.30, basis='est', url=TE('62998-2'),
          checked='TE page (tab 6.35 x 0.81, 10-8 AWG); relay drawing V23234-A0001-X040: DIN 46244 A6.3-0.8 blades on all 5 terminals; F4 A sheet: Mini ISO pattern',
          note='Heater 30 / 87 are 8 AWG, 87a is 10 AWG (sot/channels.csv k_htr c5). 6.3 tab: a Mini ISO relay has no 9.5 blade.')
    L.add(P, 'Terminals', 'Mini fuse receptacle 2.8 x 0.8, 17-13 AWG (ACPS)', '880398-2', 'TE Connectivity',
          'Receptacle tab 2.8 x 0.8 mm, 1-2.5 mm2, tin, unsealed', 1, spare(1), unit=0.15, basis='est', url=TE('880398-2'),
          checked='TE page (tab 2.8 x 0.8, 1-2.5 mm2, 17-13 AWG)', note='ACPS output, 14 AWG. One per fuse: the other blade lands on the heater-87 jumper.')
    # lugs (AMI outputs and feeds)
    all_lugs = [(nm, S.AMI_AWG[nm]) for nm, a in IN_USED + OUT_USED]
    n2r5 = sum(1 for nm, g in all_lugs if lug_for(g) == '2R5')
    n3r5 = sum(1 for nm, g in all_lugs if lug_for(g) == '3R5')
    n36161 = sum(1 for nm, g in all_lugs if lug_for(g) == '36161')
    L.add(P, 'Lugs', 'Tubular lug 10 mm2, M5 hole (8-10 AWG)', 'Klauke 2R5', 'Klauke', 'Tinned copper tubular ring lug, 10 mm2, M5; b 12, l 22', n2r5, spare(n2r5), unit=0.70, basis='est',
          checked='Klauke R-series table (b 12, l 22, hole M5): summary Lugs line; same series as the verified 2R6 / 1R6 listings',
          note='AMI outputs and relay feeds on 8-10 AWG: ' + ', '.join(nm for nm, g in all_lugs if lug_for(g) == '2R5') + '.')
    L.add(P, 'Lugs', 'Tubular lug 16 mm2, M5 hole (6 AWG)', 'Klauke 3R5', 'Klauke', 'Tinned copper tubular ring lug, 16 mm2, M5; b 13, l 26', n3r5, 1, unit=1.10, basis='est',
          checked='Klauke table (Kempston Controls 3R10.pdf): b 13, l 26, hole 5.5', note='JB1 60 A output, 6 AWG.')
    L.add(P, 'Lugs', 'Ring lug 12-10 AWG, M5 / #10 hole', '36161', 'TE Connectivity', 'PIDG closed ring tongue, 12-10 AWG, #10 (5 mm) stud, tin, partially insulated', n36161, spare(n36161), unit=0.25, basis='est',
          url=TE('36161'), checked='TE page (12-10 AWG, #10 / 5 mm stud, PIDG, Active); RS listings call the same family "M5 stud size"',
          note='CLOSES the TBD "M5 ring lug for 12 AWG": EFI and STR feeds (12 AWG). Hole 5.1 mm over the 5 mm M5 bolt - snug, check a sample.')
    L.add(P, 'Lugs', 'Tubular lug 50 mm2, M8 hole (1/0 input)', 'Klauke 6R8', 'Klauke', 'Tinned copper tubular ring lug, 50 mm2, M8; b 20, l 47', 1, 0, unit=2.60, basis='est',
          checked='Klauke table: b 20, l 47, hole 8.4 (RS 398-3015 listing)')
    # standoffs
    n_so = N_IN + N_OUT + 2
    L.add(P, 'Standoffs', 'Brass hex standoff M5 female-female, 8 AF, 40 mm (ONE part number for all %d)' % n_so, 'Essentra 301540040050', 'Essentra Components',
          'Hex standoff, female-female M5, 8.0 AF, 40.0 mm, nickel-plated brass; sold in 50s', N_IN + N_OUT, 0, unit=0.60, basis='est',
          url='https://www.essentracomponents.com/en-gb/p/standoffs/301540040050',
          checked='Essentra listing (female-female, M5, 8.0 AF, 40.0 mm, nickel-plated brass); no TE part and none of the R38 approved suppliers lists standoffs (step 4)',
          note='Dan: one 40 mm part number for every standoff. Positions: %d IN row + %d OUT row here, 2 in LOGIC = %d; order one 50-pack. CAD still draws the OUT row and the 2 LOGIC feeds 12 mm (rev 5) - see the open question.' % (N_IN, N_OUT, n_so))
    # fasteners
    L.add(P, 'Fasteners', 'Set screw M5 x 12 A2 (stud on each pad standoff)', 'ISO 4026 M5 x 12 A2', 'stock hardware', 'Hex socket set screw, flat point, stainless A2', N_POS, spare(N_POS), unit=0.12, basis='est',
          checked='ISO 4026; 5 mm of thread into the standoff (summary)', note='Any hardware supplier; not a maker-PN part.')
    L.add(P, 'Fasteners', 'Hex bolt M5 x 10 A2 (IN-row lugs under the 40 mm standoffs)', 'ISO 4017 M5 x 10 A2', 'stock hardware', 'Hex head bolt, stainless A2', N_IN, spare(N_IN), unit=0.10, basis='est', checked='ISO 4017')
    L.add(P, 'Fasteners', 'Hex bolt M5 x 8 A2 (OUT-row lugs)', 'ISO 4017 M5 x 8 A2', 'stock hardware', 'Hex head bolt, stainless A2', N_OUT, spare(N_OUT), unit=0.10, basis='est', checked='ISO 4017',
          note='With one 40 mm standoff for every position (Dan) these become M5 x 10 like the IN row; one length, one line.')
    L.add(P, 'Fasteners', 'Hex bolt M5 x 16 A2 (AMI input stud on the bar, head captured)', 'ISO 4017 M5 x 16 A2', 'stock hardware', 'Hex head bolt, stainless A2', N_POS, spare(N_POS), unit=0.12, basis='est', checked='ISO 4017')
    L.add(P, 'Fasteners', 'Keps nut M5 A2 (AMI input + output ears, 2 per position)', 'DIN 6923 M5 A2 (or ISO 7093 washer + nut)', 'stock hardware', 'Flanged hex nut, stainless A2; 4 Nm max (AMI sheet)', 2 * N_POS, spare(2 * N_POS), unit=0.07, basis='est', checked='DIN 6923')
    L.add(P, 'Fasteners', 'Hex bolt M8 x 20 A2 + nut + washer (1/0 input stud)', 'ISO 4017 M8 x 20 + ISO 4032 + ISO 7089 A2', 'stock hardware', 'Bolt, nut, washer, stainless A2', 1, 1, unit=0.60, basis='est', checked='ISO 4017 / 4032 / 7089')
    # limiters + mount
    L.add(P, 'Mounting', 'Compression limiter, feet (4)', 'EFC 10S00056', 'EFC International',
          'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 6 mm, zinc steel', 4, 1, unit=0.30, basis='est', url='https://efc-intl.com/compare/metal-compression-limiters/standard-solid-knurled-compression-limiters',
          checked='EFC comparison table 2026-10-14. EFC lists no M5 limiter and no brass limiter at 8 x 6 mm; the CAD pocket (OD 8, ID 5.3, L 6) has NO stocked match',
          note='OPEN question: M6 limiter = feet pocket OD 8 -> 9.8 and mount bolt M5 -> M6 (CAD rev 6). Not a guess: the only checked part. Not live parts, so steel is fine.')
    L.add(P, 'Mounting', 'Mount screw, feet (4)', 'TBD length - M6 hex bolt A2', 'stock hardware', 'M6 bolt + washer through each foot', 4, 0, checked='length depends on the glove-box mount face, which is still an open item (summary "Not done yet")',
          note='TBD: panel thickness / construction not known; ISO 4017 M6 x L A2 once the panel is told.')
    L.add(P, 'Mounting', 'Printed snap clips / belly pan clips / heat-set inserts', 'none', '-', 'Not used: the 4 snap tongues are printed into every cover and pan; no inserts (every bolt goes into metal, R73)', 0, 0, checked='summary "Designed for powder-bed printing"')

    # ================================================================ LOGIC box
    L.add(G, 'Printed', 'Logic Base (PA12 MJF)', 'Logic_Base_PA12_printed', 'print service', 'Deck on four angular legs, strip pockets open underneath', 1,
          unit=round(mass('Logic_Base_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('Logic_Base_PA12_printed'))
    L.add(G, 'Printed', 'Logic Pan (belly pan, PA12 MJF)', 'Logic_Pan_PA12_printed', 'print service', 'Snap-on belly pan', 1,
          unit=round(mass('Logic_Pan_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('Logic_Pan_PA12_printed'))
    L.add(G, 'Printed', 'Logic Cover (PA12 MJF)', 'Logic_Cover_PA12_printed', 'print service', 'Snap-on cover, etched labels, vent slots', 1,
          unit=round(mass('Logic_Cover_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('Logic_Cover_PA12_printed'))
    ls = {c: (len(f) - 1) * S.MINI['pitch'] + 12 + S.STRIP_FEED['ext'][c] for c, (x, f) in S.MINI_COLS.items()}
    L.add(G, 'Copper', 'Logic strips 10 x 3 mm, tinned: BUS1 %.0f mm + BUS2 %.0f mm' % (ls['BUS1'], ls['BUS2']), 'Tin-plated copper bus bar 716426, 1000 x 10 x 3 mm', 'Nassau National Cable',
          'ONE 1000 mm bar makes both strips', 1, unit=60.09, basis='seen', url='https://nassaunationalcable.com/products/tin-plated-copper-bus-bar-716426-pack-of-3',
          checked='summary "Copper" section; seller page 2026-10-14', note='Cut + drill (one 5.5 mm feed hole each); drawings on the summary page. Listing title says "pack of 3": confirm the unit before ordering.')
    for rating in sorted(mini_by_rating):
        n = mini_by_rating[rating]                                   # the ACPS 10 A is a POWER-list line (not in MINI_COLS)
        if n:
            L.add(G, 'Fuses', 'Mini blade fuse %s A (ATM)' % rating, 'ATM-%s' % (('%g' % rating)), 'Eaton Bussmann', 'ATM mini blade fuse, blade 2.8 x 0.8 mm', n, unit=0.55, basis='est',
                  checked='Littelfuse / Bussmann ATM, 2.8 x 0.8 mm blade (ISO 8820-3 mini)',
                  note='Other maker: TE makes no blade fuse. ' + ', '.join(nm for c, (x, f) in S.MINI_COLS.items() for nm, a in f if a == rating and nm != 'ACPS'))
    for p in sorted(set(p[1] for p in MICRO_USED)):
        n = sum(1 for q in MICRO_USED if q[1] == p)
        who = ', '.join(q[0] for q in MICRO_USED if q[1] == p)
        desc = {'5-1393292-8': 'Micro Relay A (V23074-A2001-A402) 1 form A, 12 V, diode', '4-1904124-3': 'Micro Relay A (V23074-A1001-A403) 1 form A, 12 V',
                '4-1904124-2': 'Micro Relay A (V23074-A1001-A402) 1 form A, 12 V, resistor', '6-1419137-4': 'Micro Relay A (V23074-A2001-A403) 1 form C, 25 A, 12 V, diode'}[p]
        L.add(G, 'Relays', 'Micro relay: ' + who, p, 'TE Connectivity', desc, n, url=TE(p),
              checked='TE page; customer drawing V23074-A2001-A402-CD: terminals 1, 2 coil 4.8 x 0.8, 3, 5 load 6.3 x 0.8' if p == '5-1393292-8' else 'TE page; te-on-hand-bom.csv',
              note='On the shelf first (R38 step 1); the third 1 form C (k_rev) is the only buy.' if p == '6-1419137-4' else '')
    L.add(G, 'Terminals', 'Micro relay coil receptacle 4.8 x 0.8, 20-15 AWG', '2293255-1', 'TE Connectivity', 'FASTON .187 receptacle, uninsulated, 20-15 AWG (0.51-1.65 mm2), brass tin',
          n_micro_coil, spare(n_micro_coil), unit=0.10, basis='est', url=TE('2293255-1'), checked='TE page (4.75 mm tab, 20-15 AWG); relay drawing coil blades 4.8 x 0.8',
          note='CLOSES the TBD "4.8 mm receptacle (micro coil blades)". 2 per micro relay x %d relays; coil wire 20 AWG.' % len(MICRO_USED))
    L.add(G, 'Terminals', 'Micro relay load receptacle 6.3 x 0.8, 18-14 AWG', '42281-1', 'TE Connectivity', 'FASTON .250 receptacle, uninsulated, 18-14 AWG, brass', n_micro_load, spare(n_micro_load), unit=0.10, basis='est',
          url=TE('42281-1'), checked='TE page (6.35 x 0.81, 18-14 AWG); relay drawing load blades 6.3 x 0.8; te-on-hand-bom.csv qty_ordered 20', note='16 AWG loads (MICRO_LOAD_AWG). 2 on a form A, 3 on a form C.')
    n_small = sum(mini_by_rating.get(r, 0) for r in (2, 5, 7.5)) + mini_by_rating.get(10, 0)
    n_big = mini_by_rating.get(15, 0) + mini_by_rating.get(20, 0)
    L.add(G, 'Terminals', 'Mini fuse receptacle 2.8, 20-18 AWG (2 / 5 / 7.5 / 10 A)', '1241388-2', 'TE Connectivity', 'AMP MCP 2.8K receptacle, gold, 0.5-1 mm2, tab 2.8 (0.6 / 0.8 thick)',
          n_small, spare(n_small), unit=0.35, basis='est', url=TE('1241388-2'), checked='TE page (2.8 mm tab, 0.6 / 0.8 thick, 0.5-1 mm2); te-on-hand-bom.csv qty_ordered 10',
          note='CLOSES the TBD "2.8 mm receptacle" for the small fuses. One per fuse (the output blade).')
    L.add(G, 'Terminals', 'Mini fuse receptacle 2.8, 17-13 AWG (15 / 20 A)', '880398-2', 'TE Connectivity', 'Receptacle tab 2.8 x 0.8 mm, 1-2.5 mm2, tin, unsealed', n_big, spare(n_big), unit=0.15, basis='est',
          url=TE('880398-2'), checked='TE page (2.8 x 0.8, 1-2.5 mm2, 17-13 AWG)',
          note='DM 20 A: spec.py assumes 12 AWG, which is BIGGER than this receptacle takes (13 AWG max): the DM wire must be 14 AWG here (20 A in 14 AWG is fine for a chassis wire) - in OPEN-ITEMS row 108. The ACPS fuse receptacle is in the POWER list.')
    L.add(G, 'Terminals', 'Strip-side pickup of each mini fuse', 'not designed yet', '-', 'How each mini fuse blade meets its copper strip', 0, 0,
          note='OPEN (design, not a part number): the summary page lists it as detail work. Needs a decision before the strip is cut.')
    L.add(G, 'Lugs', 'Tubular lug 10 mm2, M5 hole (BUS1 8 AWG, BUS2 10 AWG feeds)', 'Klauke 2R5', 'Klauke', 'Tinned copper tubular ring lug, 10 mm2, M5', 2, 1, unit=0.70, basis='est', checked='Klauke R-series table')
    L.add(G, 'Standoffs', 'Brass hex standoff M5 f-f 8 AF 40 mm (strip feeds)', 'Essentra 301540040050', 'Essentra Components', 'Same part number as POWER (Dan: one standoff, all 40 mm)', 2, 0, unit=0.60, basis='est',
          url='https://www.essentracomponents.com/en-gb/p/standoffs/301540040050', checked='see POWER list', note='Same part number as the POWER standoffs: 14 + 2 = 16 pieces, one order (a 50-pack). Rev 5 CAD draws these two at 12 mm.')
    L.add(G, 'Fasteners', 'Hex bolt M5 x 8 A2 (strip bolts 2 + feed lugs 2)', 'ISO 4017 M5 x 8 A2', 'stock hardware', 'Hex head bolt, stainless A2', 4, spare(4), unit=0.10, basis='est', checked='ISO 4017')
    L.add(G, 'Mounting', 'Compression limiter, feet (4)', 'EFC 10S00056', 'EFC International', 'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 6 mm, zinc steel', 4, 1, unit=0.30, basis='est',
          url='https://efc-intl.com/compare/metal-compression-limiters/standard-solid-knurled-compression-limiters', checked='see POWER list (same open question)')
    L.add(G, 'Mounting', 'Mount screw, feet (4)', 'TBD length - M6 hex bolt A2', 'stock hardware', 'M6 bolt + washer through each foot', 4, 0, checked='length depends on the glove-box mount face (open item)')
    L.add(G, 'Mounting', 'Printed snap clips / belly pan clips / heat-set inserts', 'none', '-', 'Not used: snap tongues are printed in; no inserts (R73)', 0, 0, checked='summary')

    # ================================================================ BATTERY relay block
    L.add(B, 'Printed', 'BattRelay Base (PA12 MJF)', 'BattRelay_Base_PA12_printed', 'print service', 'Floor plate, relay platform, fuse pedestal, 2 end tabs', 1,
          unit=round(mass('BattRelay_Base_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('BattRelay_Base_PA12_printed'))
    L.add(B, 'Printed', 'BattRelay Cover (PA12 MJF)', 'BattRelay_Cover_PA12_printed', 'print service', 'Snap-on cover, side vents', 1,
          unit=round(mass('BattRelay_Cover_PA12_printed') * 0.10, 2), basis='est', checked='report volume %.1f cm3' % mass('BattRelay_Cover_PA12_printed'))
    L.add(B, 'Copper', 'Bar 25.4 x 6.35 x 36.5 mm, tinned', 'cut from the POWER bar stock (B0CGJBRNJX)', 'MECCANIXITY', 'From the same 305 mm bar as the POWER bar (no extra stock to buy)', 0, 0, checked='stock bought in the POWER list', note='Holes: M6 feed 6.5, AMI 40 input 5.5.')
    L.add(B, 'Copper', 'Pad 15 x 3 x 17.5 mm, tinned', 'cut from the pad stock (B09Z7NBLDK)', 'Bopaodao (Amazon)', 'From the same 1000 mm bar as the POWER pads (no extra stock to buy)', 0, 0, checked='stock bought in the POWER list')
    L.add(B, 'Relay', 'Fuel pump relay k_fp, HCR150, 12 V, 130 A, IP67', '1416010-1', 'TE Connectivity', 'High Current Relay 150 (V23132-A2001-B200), M6 screw load terminals, Superseal 1.5 coil plug', 1, url=TE('1416010-1'),
          checked='TE page + data sheet V23132-X0000-A001 (130 A contact, 150 A limiting, 3.9 W coil, M6 5 Nm, lug up to 25 mm2); te-on-hand-bom.csv qty_ordered 2',
          note='On the shelf. The second HCR150 is the k_eps relay (not in a box list).')
    L.add(B, 'Relay', 'Coil plug housing, Superseal 1.5, 2 pole', '282080-1', 'TE Connectivity', 'AMP Superseal 1.5 receptacle housing', 1, url=TE('282080-1'),
          checked='HCR150 data sheet "Connector Information": coil side housing 282080-1, wire seal 281934-2, contact 282110-1; te-on-hand-bom.csv qty_ordered 2',
          note='Earlier summary said BUY 1: it is on the shelf (OWN).')
    L.add(B, 'Relay', 'Coil plug contact', '282110-1', 'TE Connectivity', 'Superseal 1.5 receptacle contact (per HCR150 sheet)', 2, 1, url=TE('282110-1'), checked='HCR150 data sheet; te-on-hand-bom.csv qty_ordered 10',
          note='Earlier summary said BUY 2 for seal / contact: both on the shelf.')
    L.add(B, 'Relay', 'Coil plug wire seal', '281934-2', 'TE Connectivity', 'Superseal 1.5 single wire seal', 2, 1, url=TE('281934-2'), checked='HCR150 data sheet; te-on-hand-bom.csv qty_ordered 10')
    L.add(B, 'Fuses', 'AMI bolt-down fuse 40 A (FP)', 'AMI-40', 'Eaton Bussmann', 'AMI series 32 VDC, M5 ears', 1, unit=5.30, basis='seen', url='https://www.waytekwire.com/product/eaton-s-bussmann-series-ami-40-bolt-down-fuse',
          checked='Waytek AMI-40 listing', note='Same part as the POWER AMI-40s: order them together.')
    L.add(B, 'Lugs', 'Ring lug 6 mm2, M6 hole (feed in, relay terminal 3, relay terminal 5; 10 AWG)', 'Klauke 1R6', 'Klauke', 'Tinned copper tubular ring lug, 6 mm2, M6 stud, hole 6.5', 3, 1, unit=0.55, basis='est',
          url='https://www.voltus.com/en/klauke-1r6-tube-cable-lug-m6-without-viewing-hole-6-mm.html',
          checked='Voltus / Galaxus / RS listings: Klauke 1R6, 6 mm2, M6, tinned copper, 6.5 hole, 27.5 long; HCR150 sheet: M6 load screws, lug up to 25 mm2',
          note='CLOSES the TBD "M6 ring lug, 10 AWG". 10 AWG = 5.3 mm2, inside the 6 mm2 barrel.')
    L.add(B, 'Lugs', 'Tubular lug 10 mm2, M5 hole (AMI out end of the jumper)', 'Klauke 2R5', 'Klauke', 'Tinned copper tubular ring lug, 10 mm2, M5', 1, 1, unit=0.70, basis='est', checked='Klauke R-series table')
    L.add(B, 'Fasteners', 'Hex bolt M6 x 16 A2 + nut + washer (feed stud, 2 flange bolts)', 'ISO 4017 M6 x 16 + ISO 4032 + ISO 7089 A2', 'stock hardware', 'Bolt, nut, washer, stainless A2; flange nuts captured under the floor', 3, 1, unit=0.20, basis='est', checked='ISO 4017 / 4032 / 7089')
    L.add(B, 'Fasteners', 'Hex bolt M5 x 16 A2 (AMI input stud on the bar)', 'ISO 4017 M5 x 16 A2', 'stock hardware', 'Hex head bolt, stainless A2', 1, 1, unit=0.12, basis='est', checked='ISO 4017')
    L.add(B, 'Fasteners', 'Keps nut M5 A2 (AMI input + output ears)', 'DIN 6923 M5 A2', 'stock hardware', 'Flanged hex nut, stainless A2; 4 Nm max', 2, 1, unit=0.07, basis='est', checked='DIN 6923')
    L.add(B, 'Fasteners', 'Set screw M5 x 12 A2 (AMI output stud on the pad)', 'ISO 4026 M5 x 12 A2', 'stock hardware', 'Hex socket set screw, A2', 1, 1, unit=0.12, basis='est', checked='ISO 4026',
          note='No standoff in this box: the pad sits on the printed pedestal.')
    L.add(B, 'Mounting', 'Compression limiter, end tabs (2) and HCR150 flange bosses (2)', 'EFC 10S00052', 'EFC International',
          'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 4 mm, zinc steel', 4, 1, unit=0.25, basis='est', url='https://efc-intl.com/compare/metal-compression-limiters/standard-solid-knurled-compression-limiters',
          checked='EFC comparison table: the M6 flange pocket in the CAD is OD 10, ID 6.5, L 4.6 - this part is OD 9.8, ID 6.8, L 4 (CAD to follow)',
          note='End tabs follow the glove-box feet decision (M6 limiters, same open question).')
    L.add(B, 'Mounting', 'Mount screw, end tabs (2)', 'TBD length - M6 hex bolt A2', 'stock hardware', 'M6 bolt + washer through each tab', 2, 0, checked='length depends on the trunk mount face (Z4 location, no panel drawn)')
    L.add(B, 'Mounting', 'Printed snap clips / inserts', 'none', '-', 'Not used (snap tongues printed in; the base has a closed floor, no belly pan)', 0, 0, checked='summary')
    return L.rows


def totals(rows):
    out = {}
    for b, rs in rows.items():
        s = 0.0
        for r in rs:
            if r['line_usd'] != '':
                s += float(r['line_usd'])
        out[b] = round(s, 2)
    return out


def write(rows):
    for b, fn in FILES.items():
        with open(os.path.join(FB, fn), 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, lineterminator='\n')
            w.writeheader()
            w.writerows(rows[b])


if __name__ == '__main__':
    R = build()
    write(R)
    T = totals(R)
    for b in FILES:
        buy = sum(1 for r in R[b] if r['buy'] > 0)
        print('%-10s %2d lines, %2d with a BUY, est. $%.2f' % (b, len(R[b]), buy, T[b]))
