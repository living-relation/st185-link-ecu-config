"""Per-box parts lists for the custom fuse + relay boxes (cad/fusebox).

Writes three CSVs next to the summary page and returns the rows for summary_html.py:
    cad/fusebox/fusebox-parts-power.csv     POWER box (glove box)
    cad/fusebox/fusebox-parts-logic.csv     LOGIC box (glove box)
    cad/fusebox/fusebox-parts-battrelay.csv battery relay block (trunk)
docs/harness/buylist.py reads the BUY lines of these three files (the repo buy list, docs/harness/NEED-TO-BUY.md).

Counts come from spec.py (fuse slots, relay positions, wire gauges) and fusebox_report.json (printed volumes), so a
change to the boxes changes the lists. Every part number is checked against a maker sheet; the 'checked' column says
which. DECISIONS R82 (Dan 2026-10-14): every line is a real part you can buy, with a live source link - no TBD, no "or equivalent",
no generic placeholder; the 3D-printed box parts are the one exception (STL/STEP file + PA12, no link). Order (R38): on-hand TE list -> TE -> approved suppliers ->
others with a reason. On-hand quantities are qty_ordered from docs/sourcing/te-on-hand-bom.csv, handed out box by box
(POWER, LOGIC, BATTRELAY) so one shelf quantity is never counted twice. Prices: 'seen' = read on a listing 2026-10-14,
'est' = typical distributor price, not checked (they move).

    python cad/fusebox/src/parts_lists.py            (rev 6, the selected build)
    python cad/fusebox/src/parts_lists.py --rev 7    (rev 7 option: cad/fusebox/rev7/fusebox-parts-power.csv only - its LOGIC box
                                                       and battery block are rev 6 unchanged; --check checks both revs)
Claude Code, 2026-10-14. Rev 6 (DECISIONS R85): M6 limiters everywhere (C1), no mount bolts / nuts (C3: out of scope - the box
lists hold the boxes only), mini fuse input jumpers (C4), one 40 mm standoff (B5).
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

RS = {   # RS PRO stock numbers and the listing each was read on
    'M5x10': ('RS 287-3921', 'https://th.rs-online.com/web/p/hex-bolts/2873921', 'RS PRO A2/304 stainless hex bolt M5 x 10, DIN 933'),
    'M5x16': ('RS 263-2205', 'https://ph.rs-online.com/web/p/hex-bolts/2632205', 'RS PRO stainless hex bolt M5 x 16, DIN 933 (grade not stated on the listing)'),
    'M5set': ('RS 137-809', 'https://uk.rs-online.com/web/p/grub-screws-set-screws/0137809', 'RS PRO A2/304 stainless hex socket set screw M5 x 12, DIN 916'),
    'M5nut': ('RS 264-6432', 'https://se.rs-online.com/web/p/products/2646432', 'RS PRO A2/304 stainless serrated flange hex nut M5, DIN 6923'),
    'M8bolt': ('RS 190-276', 'https://ph.rs-online.com/web/p/hex-bolts/0190276', 'RS PRO stainless hex bolt M8 x 25, DIN 933 (grade not stated on the listing)'),
    'M8nut': ('RS 530-769', 'https://hkcn.rs-online.com/web/p/products/530769', 'RS PRO A2/304 stainless hex nut M8, DIN 934'),
    'M8wash': ('RS 797-6068', 'https://th.rs-online.com/web/p/washers/7976068', 'RS PRO stainless plain washer M8, DIN 125A'),
    'M6bolt16': ('RS 190-169', 'https://ie.rs-online.com/web/p/hex-bolts/0190169', 'RS PRO stainless (A4 / 316) hex bolt M6 x 16, DIN 933'),
    'M6bolt25': ('RS 264-6468', 'https://au.rs-online.com/web/p/hex-bolts/2646468', 'RS PRO stainless (A4 / 316) hex bolt M6 x 25, DIN 933'),
    'M6nut': ('RS 527-274', 'https://nl.rs-online.com/web/p/hex-nuts/0527274', 'RS PRO A2/304 stainless hex nut M6, DIN 934'),
    'M6wash': ('RS 287-3962', 'https://se.rs-online.com/web/p/washers/2873962', 'RS PRO A2/304 stainless plain washer M6, BS 4320C'),
    'M4x8': ('RS 287-3915', 'https://uk.rs-online.com/web/p/hex-bolts/2873915', 'RS PRO A2/304 stainless hex bolt M4 x 8, DIN 933'),
    'M4spring': ('RS 231-0691', 'https://se.rs-online.com/web/p/washers/2310691', 'RS PRO AISI 301 stainless spring washer M4, DIN 127B, 0.9 thick'),
}
EFC_URL = 'https://efc-intl.com/compare/metal-compression-limiters/standard-solid-knurled-compression-limiters'
FUTURE_53941 = 'https://www.futureelectronics.com/p/interconnect--pin-and-socket-connectors--crimp-terminals/53941-1-te-connectivity-5139464'
AWC_M22759_16_14 = 'https://www.awcwire.com/product/m22759_16-14'
ATM_URL = {2: 'https://www.standardelectricsupply.com/Bussmann-ATM-2-Automotive-Fuse', 5: 'https://www.stanion.com/Product/atm5bus',
           7.5: 'https://www.stanion.com/Product/atm71-2bus', 10: 'https://stanion.com/Product/atm10bus',
           15: 'https://www.vanmeterinc.com/catalog/electrical/fuses/automotive-fuses/eaton-atm-15', 20: 'https://www.stanion.com/Product/atm20bus'}
AMI_URL = {30: 'https://www.waytekwire.com/product/eaton-s-bussmann-series-ami-30-bolt-down-fuse',
           40: 'https://www.waytekwire.com/product/eaton-s-bussmann-series-ami-40-bolt-down-fuse',
           50: 'https://waytekwire.com/product/eaton-s-bussmann-series-ami-50-bolt-down-fuse',
           60: 'https://www.waytekwire.com/product/eaton-s-bussmann-series-ami-60-bolt-down-fuse'}
KLAUKE = {'2R5': ('Klauke 2R5', 'https://www.buerklin.com/en/p/klauke/cable-lugs/2r5/07F2065/'),
          '3R5': ('Klauke 3R5MS', 'https://buerklin.com/en/p/klauke/cable-lugs/3r5ms/07F9752'),
          '6R8': ('Klauke 6R8', 'https://www.buerklin.com/en/p/klauke/cable-lugs/6r8/07F2081/'),
          '1R6': ('Klauke 1R6', 'https://www.voltus.com/en/klauke-1r6-tube-cable-lug-m6-without-viewing-hole-6-mm.html')}
TE =  lambda pn: 'https://www.te.com/en/product-%s.html' % pn
DS_V23136 = 'TE data sheet V23136X0000A004 (Power Relay F4 A, 2023-09)'
DS_VCF = 'TE data sheet VCF7-X0000-A001 (Connectors for Mini / Maxi ISO relays)'

REV7_DIR = os.path.join(FB, 'rev7')
FILES7 = {'POWER': 'fusebox-parts-power.csv'}   # rev 7: only the POWER box (with the bus bar in it) changes


def load_print(rev):
    try:
        return json.load(open(os.path.join(REV7_DIR if rev == 7 else FB, 'fusebox_report.json'))).get('printed_parts', {})
    except OSError:
        return {}


PRINT = load_print(6)
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


def hw(L, box, group, key, item, need, spare, unit, note='', checked=None):
    pn, url, desc = RS[key]
    L.add(box, group, item, pn, 'RS PRO', desc, need, spare, unit=unit, basis='est', url=url,
          checked=checked or 'RS listing (stock number, size, standard) read 2026-10-14', note=note)


def lug(L, box, key, item, need, spare, unit, desc, note='', checked=''):
    pn, url = KLAUKE[key]
    L.add(box, 'Lugs', item, pn, 'Klauke', desc, need, spare, unit=unit, basis='est', url=url, checked=checked or 'Buerklin / Voltus listing 2026-10-14', note=note)


def build(rev=6):
    global PRINT
    PRINT = load_print(rev)
    R7 = rev == 7
    L = Lists()
    P, G, B = 'POWER', 'LOGIC', 'BATTRELAY'
    pr = lambda k: mass(k + '_PA12_printed')
    PRINT_NOTE = 'est. $0.10/cm3 on the printer\'s material cost; file is the STL/STEP in cad/fusebox%s (rule R82: printed parts need no buy link)' % ('/rev7' if R7 else '')

    def printed(box, key, item, desc):
        L.add(box, 'Printed', item, key + '_PA12_printed.stl + .step (PA12)', 'print (your PA12 powder-bed printer)', desc, 1,
              unit=round(pr(key) * 0.10, 2), basis='est', checked='report volume %.1f cm3; %s' % (pr(key), PRINT_NOTE))

    # ================================================================ POWER box
    if not R7:
        printed(P, 'Power_Base', 'Power Base', 'Deck on four angular legs, open underneath; PA12')
        printed(P, 'Power_Pan', 'Power Pan (belly pan)', 'Snap-on belly pan, 4 integral tongues (no separate clips); PA12')
        printed(P, 'Power_Cover', 'Power Cover', 'Snap-on cover, etched labels, vent slots; PA12')
        L.add(P, 'Copper', 'Power bar 25.4 x 6.35 x 148 mm, tinned', 'MECCANIXITY B0CGJBRNJX', 'MECCANIXITY (Amazon)',
              '12 in x 1 in x 1/4 in tinned copper flat bar: ONE bar makes the POWER bar (148 mm) and the battery block bar (36.5 mm)', 1, unit=26.19, basis='seen',
              url='https://www.amazon.com/dp/B0CGJBRNJX', checked='summary "Copper" section; seller page 2026-10-14',
              note='Cut + drill only (R76): 15 holes, drawing on the summary page. Stock bought here covers BATTRELAY too.')
    else:            # rev 7 (E2 = A): the bus bar lives in this box - its POS bar is the AMI bar, its NEG bar sits beside it
        printed(P, 'Power_Base', 'Power Base (with the bus zone)', 'Deck on four angular legs, open underneath, 62 mm bus zone at the rear, printed barrier wall NEG / POS; PA12')
        printed(P, 'Power_Pan', 'Power Pan (belly pan)', 'Snap-on belly pan, 4 integral tongues (no separate clips); PA12')
        printed(P, 'Power_Cover', 'Power Cover', 'Snap-on cover, etched labels (AMI, relays, bus terminals), vent slots; PA12')
        L.add(P, 'Copper', 'POS bus bar 25.4 x 6.35 x 226 mm + NEG bus bar 25.4 x 6.35 x 105 mm, tinned', 'MECCANIXITY B0CGJBRNJX', 'MECCANIXITY (Amazon)',
              '12 in x 1 in x 1/4 in tinned copper flat bar: bar 1 = POS bar (226 mm) + battery block bar (36.5 mm); bar 2 = NEG bar (105 mm), 195 mm spare',
              S.REV7_STOCK_BARS, unit=26.19, basis='seen', url='https://www.amazon.com/dp/B0CGJBRNJX', checked='summary "Copper" section; seller page 2026-10-14',
              note='Cut + drill only (R76): POS bar 14 x 5.5 (AMI inputs) + 3 x 8.5 (BAT+ IN, RADLOK+, spare); NEG bar 5 x 8.5. 161 mm2 of copper each - '
                   'three times the 1/0 cable (53 mm2). Replaces the B rev3 bus bar machined Al bars and set-screw port blocks (R76: no milling).')
    L.add(P, 'Copper', 'Output pads 15 x 3 x 17.5 mm, tinned (14 here + 1 in BATTRELAY)', 'Bopaodao B09Z7NBLDK', 'Bopaodao (Amazon)',
          'Tinned copper bus bar 3 x 15 x 1000 mm C110: ONE bar makes all 15 pads (290 mm with kerf)', 1, unit=51.99, basis='seen',
          url='https://www.amazon.com/dp/B09Z7NBLDK', checked='summary "Copper" section; seller page 2026-10-14', note='One drilled hole each (5.5 mm).')
    n = {a: sum(1 for _, x in IN_USED + OUT_USED if x == a) for a in (30, 40, 50, 60)}
    for rating in (30, 40, 50, 60):
        L.add(P, 'Fuses', 'AMI bolt-down fuse %d A' % rating, 'AMI-%d' % rating, 'Eaton Bussmann', 'AMI series, 32 VDC, M5 stud ears 9.5 x 0.8 mm', n[rating],
              unit=5.30, basis='seen (Waytek AMI-30 / -40 / -50 / -60 at 5+: $5.28 / $5.28 / $4.56 / $5.30)', url=AMI_URL[rating],
              checked='Waytek listing; Bussmann AMI sheet (spec.py AMI dims)',
              note='Other maker (R38 step 4): TE sells no bolt-down fuse. Slots: ' + ', '.join(nm for nm, a in IN_USED + OUT_USED if a == rating))
    L.add(P, 'Fuses', 'ACPS mini blade fuse 10 A', 'ATM-10', 'Eaton Bussmann', 'ATM mini blade fuse, blade 2.8 x 0.8 mm', 1, unit=0.55, basis='est', url=ATM_URL[10],
          checked='Stanion listing; Littelfuse / Bussmann ATM blade 2.8 x 0.8 mm (ISO 8820-3 mini)', note='Front of relay column B, fed from heater 87.')
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
          checked='TE page (tab 9.53 x 1.22, 10-7 AWG) + ' + DS_VCF + ' (load 5.3-13.3 mm2)', note='30 / 87 of k_fan, k_fan2 (8 AWG).')
    n_f7_coil = 2 * len(F7_USED)
    L.add(P, 'Terminals', 'Relay coil receptacle 6.3 x 0.8, 20-18 AWG (F7 85/86 + heater 85/86)', '1-1393310-8', 'TE Connectivity',
          'Crimp terminal QC .250 (26A1348A) for 0.5-0.8 mm2, brass tin', n_f7_coil + 2, spare(n_f7_coil + 2), unit=0.12, basis='est', url=TE('1-1393310-8'),
          checked=DS_VCF + ' "Selection of fitting crimp terminals": 6.3 x 0.8, 0.5-0.8 mm2 (20-18), coil; TE page: Active',
          note='Coil wires are 20 AWG in spec.py (COIL_AWG). On-hand 42281-1 (18-14 AWG) is too big for 20 AWG, so it goes to the micro relay loads instead.')
    L.add(P, 'Terminals', 'Heater relay load receptacle 6.3 x 0.8, 10-8 AWG (30, 87)', '62998-2', 'TE Connectivity',
          'FASTON .250 receptacle, uninsulated, 10-8 AWG (5-8 mm2), brass tin', 2, spare(2), unit=0.30, basis='est', url=TE('62998-2'),
          checked='TE page (tab 6.35 x 0.81, 10-8 AWG); relay drawing V23234-A0001-X040: DIN 46244 A6.3-0.8 blades on all 5 terminals; F4 A sheet: Mini ISO pattern',
          note='Heater 30 / 87 are 8 AWG (ST185-CabinPower k_htr). 87a is 14 AWG: a 42281-1 (next line). A Mini ISO relay has no 9.5 blade.')
    L.add(P, 'Terminals', 'Heater relay 87a receptacle 6.3 x 0.8, 18-14 AWG', '42281-1', 'TE Connectivity', 'FASTON .250 receptacle, uninsulated, 18-14 AWG, brass', 1, 1,
          unit=0.10, basis='est', url=TE('42281-1'), checked='TE page (6.35 x 0.81, 18-14 AWG); te-on-hand-bom.csv qty_ordered 20; ST185-CabinPower k_htr 87a 14 AWG',
          note='OPEN-ITEMS row 110 (c).')
    L.add(P, 'Terminals', 'Mini fuse receptacle 2.8 x 0.8, 17-13 AWG (ACPS input, 14 AWG)', '880398-2', 'TE Connectivity',
          'Receptacle tab 2.8 x 0.8 mm, 1-2.5 mm2, tin, unsealed', 1, 1, unit=0.15, basis='est', url=TE('880398-2'),
          checked='TE page (tab 2.8 x 0.8, 1-2.5 mm2, 17-13 AWG); ST185-CabinPower ACPS in 14 AWG', note='ACPS input from heater 87 (row 110 (c)).')
    L.add(P, 'Terminals', 'Mini fuse receptacle 2.8, 20-18 AWG (ACPS output, 18 AWG)', '1241388-2', 'TE Connectivity', 'AMP MCP 2.8K receptacle, gold, 0.5-1 mm2, tab 2.8 (0.6 / 0.8 thick)',
          1, 1, unit=0.35, basis='est', url=TE('1241388-2'), checked='TE page (2.8 mm tab, 0.6 / 0.8 thick, 0.5-1 mm2); te-on-hand-bom.csv qty_ordered 10; ST185-CabinPower ACPS out 18 AWG',
          note='Row 110 (c).')
    # lugs
    all_lugs = [(nm, S.AMI_AWG[nm]) for nm, a in IN_USED + OUT_USED]
    n2r5 = sum(1 for nm, g in all_lugs if lug_for(g) == '2R5')
    n3r5 = sum(1 for nm, g in all_lugs if lug_for(g) == '3R5')
    n36161 = sum(1 for nm, g in all_lugs if lug_for(g) == '36161')
    lug(L, P, '2R5', 'Tubular lug 10 mm2, M5 hole (8-10 AWG)', n2r5, spare(n2r5), 0.70, 'Tinned copper tubular ring lug, 10 mm2, M5, hole 5.3; b 12, l 22',
        note='AMI outputs and relay feeds on 8-10 AWG: ' + ', '.join(nm for nm, g in all_lugs if lug_for(g) == '2R5') + '.', checked='Buerklin listing 07F2065 (hole 5.3, M5) + Klauke table b 12 l 22')
    lug(L, P, '3R5', 'Tubular lug 16 mm2, M5 hole (6 AWG)', n3r5, 1, 1.10, 'Tinned copper tubular ring lug with inspection hole, 16 mm2, M5, hole 5.5; b 13, l 26',
        note='JB1 60 A output, 6 AWG. The 3R5MS is the 3R5 with an inspection hole: same barrel.', checked='Buerklin listing 07F9752 (16 mm2, M5, hole 5.5)')
    L.add(P, 'Lugs', 'Ring lug 12-10 AWG, M5 / #10 hole', '36161', 'TE Connectivity', 'PIDG closed ring tongue, 12-10 AWG, #10 (5 mm) stud, tin, partially insulated', n36161, spare(n36161), unit=0.25, basis='est',
          url=TE('36161'), checked='TE page (12-10 AWG, #10 / 5 mm stud, PIDG, Active); RS listings call the same family "M5 stud size"',
          note='EFI and STR feeds (12 AWG). Hole 5.1 mm over the 5 mm M5 bolt - snug, check a sample.')
    if not R7:
        lug(L, P, '6R8', 'Tubular lug 50 mm2, M8 hole (1/0 input)', 1, 0, 2.60, 'Tinned copper tubular ring lug, 50 mm2, M8, hole 8.4; b 20, l 47', checked='Buerklin listing 07F2081 (hole 8.4, M8)')
    else:
        n10 = sum(1 for p_ in S.REV7['pos_studs'] if p_[1] != 'SPARE') + sum(1 for n_ in S.REV7['neg_studs'] if n_[3] == '1/0')
        lug(L, P, '6R8', 'Tubular lug 50 mm2, M8 hole (the %d 1/0 bus cables)' % n10, n10, 1, 2.60, 'Tinned copper tubular ring lug, 50 mm2, M8, hole 8.4; b 20, l 47',
            checked='Buerklin listing 07F2081 (hole 8.4, M8)',
            note='BAT+ IN (H1), RADLOK+ (H3), BAT- (H2), RADLOK- (H6a), GND ID, GND IG (H7): the B rev3 set-screw ports become lugs. The small relay grounds keep their own M8 rings (harness parts).')
    # standoffs
    n_so = N_IN + N_OUT
    L.add(P, 'Standoffs', 'Brass hex standoff M5 female-female, 8 AF, 40 mm (ONE part number for all %d)' % n_so, 'Essentra 301540040050', 'Essentra Components',
          'Hex standoff, female-female M5, 8.0 AF, 40.0 mm, nickel-plated brass; sold in 50s', N_IN + N_OUT, 0, unit=0.60, basis='est',
          url='https://www.essentracomponents.com/en-gb/p/standoffs/301540040050',
          checked='Essentra listing (female-female, M5, 8.0 AF, 40.0 mm, nickel-plated brass); no TE part and none of the R38 approved suppliers lists standoffs (step 4)',
          note='B5 (Dan): one 40 mm part number for every standoff: %d IN row + %d OUT row = %d, all drawn 40 mm in CAD rev 6; the LOGIC box has none any more (its feed lugs bolt onto the strips). Sold in 50s.' % (N_IN, N_OUT, n_so))
    # fasteners
    hw(L, P, 'Fasteners', 'M5set', 'Set screw M5 x 12 (stud on each pad standoff)', N_POS, spare(N_POS), 0.12, note='Through the pad into the standoff (5 mm of thread); DIN 916 is a cup point - irrelevant for a stud.')
    hw(L, P, 'Fasteners', 'M5x10', 'Hex bolt M5 x 10 (lug under each standoff, IN and OUT rows)', N_IN + N_OUT, spare(N_IN + N_OUT), 0.10, note='One length for both rows now that every standoff is 40 mm.')
    hw(L, P, 'Fasteners', 'M5x16', 'Hex bolt M5 x 16 (AMI input stud on the bar, head captured)', N_POS, spare(N_POS), 0.12)
    hw(L, P, 'Fasteners', 'M5nut', 'Keps nut M5 (AMI input + output ears, 2 per position)', 2 * N_POS, spare(2 * N_POS), 0.07, note='4 Nm max (AMI sheet).')
    if not R7:
        hw(L, P, 'Fasteners', 'M8bolt', 'Hex bolt M8 x 25 (1/0 input stud)', 1, 1, 0.30, note='Rev 5 CAD draws M8 x 20; the nearest stocked stainless length is 25 (RS lists no M8 x 20).')
        hw(L, P, 'Fasteners', 'M8nut', 'Hex nut M8 (1/0 input stud)', 1, 1, 0.08)
        hw(L, P, 'Fasteners', 'M8wash', 'Plain washer M8 (1/0 input stud)', 1, 1, 0.05)
    else:
        n8 = len(S.REV7['pos_studs']) + len(S.REV7['neg_studs'])
        hw(L, P, 'Fasteners', 'M8bolt', 'Hex bolt M8 x 25 (bus studs: 3 POS + 5 NEG, head captured)', n8, 1, 0.30,
           note='Up through the deck into the bar, head in a printed hex pocket (R76: plain holes, no tapping). The spare POS stud gets its bolt now.')
        hw(L, P, 'Fasteners', 'M8nut', 'Hex nut M8 (bus studs)', n8, 1, 0.08)
        hw(L, P, 'Fasteners', 'M8wash', 'Plain washer M8 (bus studs)', n8, 1, 0.05)
    # limiters + mount
    L.add(P, 'Mounting', 'Compression limiter, feet (4)', 'EFC 10S00056', 'EFC International',
          'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 6 mm, zinc-plated steel', 4, 1, unit=0.30, basis='est', url=EFC_URL,
          checked='EFC comparison table 2026-10-14 (EFC lists no M5 limiter); CAD rev 6 foot: 10.2 press-fit pocket, 6 mm ear',
          note='C1 (Dan): M6 limiters in all 10 mount points. Mount bolts / nuts are not part of the box (C3).')

    if R7:
        return {P: L.rows[P]}

    # ================================================================ LOGIC box
    printed(G, 'Logic_Base', 'Logic Base', 'Deck on four angular legs, cavity towers, printed spine between the bus strips (lips under them); PA12')
    printed(G, 'Logic_Pan', 'Logic Pan (belly pan)', 'Snap-on belly pan; PA12')
    printed(G, 'Logic_Cover', 'Logic Cover', 'Snap-on cover, etched labels, vent slots; PA12')
    ls = {c: S.STRIP_Y[c][1] - S.STRIP_Y[c][0] for c in S.MINI_COLS}
    L.add(G, 'Copper', 'Logic strips 25.4 x 3.2 mm on edge, tinned: BUS1 %.0f mm + BUS2 %.0f mm' % (ls['BUS1'], ls['BUS2']), 'MECCANIXITY B0CGJC2S1L', 'MECCANIXITY (Amazon)',
          '2 pcs 12 in x 1 in x 1/8 in tinned copper flat bar: ONE bar makes both strips', 1, unit=27.19, basis='seen',
          url='https://www.amazon.com/dp/B0CGJC2S1L', checked='spec.py STOCK runner-up list 2026-10-14 (25.4 x 3.2 x 305, 2 pcs, $27.19)',
          note='Rev 6 (C4): replaces the 10 x 3 Nassau bar. Cut, drill and tap (R76): M4 at each lug stud, M5 at the feed - drawing on the summary page.')
    for rating in sorted(mini_by_rating):
        k = mini_by_rating[rating]
        L.add(G, 'Fuses', 'Mini blade fuse %s A (ATM)' % rating, 'ATM-%s' % ('7-1/2' if rating == 7.5 else '%g' % rating), 'Eaton Bussmann', 'ATM mini blade fuse, blade 2.8 x 0.8 mm', k, unit=0.55, basis='est', url=ATM_URL[rating],
              checked='distributor listing; Littelfuse / Bussmann ATM, 2.8 x 0.8 mm blade (ISO 8820-3 mini)',
              note='Other maker: TE makes no blade fuse. ' + ', '.join(nm for c, (x, f) in S.MINI_COLS.items() for nm, a in f if a == rating))
    for p in sorted(set(p[1] for p in MICRO_USED)):
        k = sum(1 for q in MICRO_USED if q[1] == p)
        who = ', '.join(q[0] for q in MICRO_USED if q[1] == p)
        desc = {'5-1393292-8': 'Micro Relay A (V23074-A2001-A402) 1 form A, 12 V, diode', '4-1904124-3': 'Micro Relay A (V23074-A1001-A403) 1 form A, 12 V',
                '4-1904124-2': 'Micro Relay A (V23074-A1001-A402) 1 form A, 12 V, resistor', '6-1419137-4': 'Micro Relay A (V23074-A2001-A403) 1 form C, 25 A, 12 V, diode'}[p]
        L.add(G, 'Relays', 'Micro relay: ' + who, p, 'TE Connectivity', desc, k, url=TE(p),
              checked='TE page; customer drawing V23074-A2001-A402-CD: terminals 1, 2 coil 4.8 x 0.8, 3, 5 load 6.3 x 0.8' if p == '5-1393292-8' else 'TE page; te-on-hand-bom.csv',
              note='On the shelf first (R38 step 1); the third 1 form C (k_rev) is the only buy.' if p == '6-1419137-4' else '')
    L.add(G, 'Terminals', 'Micro relay coil receptacle 4.8 x 0.8, 20-15 AWG', '2293255-1', 'TE Connectivity', 'FASTON .187 receptacle, uninsulated, 20-15 AWG (0.51-1.65 mm2), brass tin',
          n_micro_coil, spare(n_micro_coil), unit=0.10, basis='est', url=TE('2293255-1'), checked='TE page (4.75 mm tab, 20-15 AWG); relay drawing coil blades 4.8 x 0.8',
          note='2 per micro relay x %d relays; coil wire 20 AWG.' % len(MICRO_USED))
    L.add(G, 'Terminals', 'Micro relay load receptacle 6.3 x 0.8, 18-14 AWG', '42281-1', 'TE Connectivity', 'FASTON .250 receptacle, uninsulated, 18-14 AWG, brass', n_micro_load, spare(n_micro_load), unit=0.10, basis='est',
          url=TE('42281-1'), checked='TE page (6.35 x 0.81, 18-14 AWG); relay drawing load blades 6.3 x 0.8; te-on-hand-bom.csv qty_ordered 20', note='16 AWG loads (MICRO_LOAD_AWG). 2 on a form A, 3 on a form C.')
    outs = [(nm, a) for c, (x, f) in S.MINI_COLS.items() for nm, a in f if a]
    own_in = [nm for c, (x, f) in S.MINI_COLS.items() for i, (nm, a) in enumerate(f) if a and i >= S.STUDS[c] + (1 if c == 'BUS2' else 0)]
    jumpers = [nm for c, (x, f) in S.MINI_COLS.items() for i, (nm, a) in enumerate(f) if a and i < S.STUDS[c]]
    n_small = sum(1 for nm, a in outs if nm in S.OUT_SMALL) + len(own_in)
    n_big = sum(1 for nm, a in outs if nm not in S.OUT_SMALL)
    L.add(G, 'Terminals', 'Mini fuse receptacle 2.8, 20-18 AWG (outputs + MRS / B30 inputs)', '1241388-2', 'TE Connectivity', 'AMP MCP 2.8K receptacle, gold, 0.5-1 mm2, tab 2.8 (0.6 / 0.8 thick)',
          n_small, spare(n_small), unit=0.35, basis='est', url=TE('1241388-2'), checked='TE page (2.8 mm tab, 0.6 / 0.8 thick, 0.5-1 mm2); te-on-hand-bom.csv qty_ordered 10; ST185-CabinPower fb_logic contacts',
          note='By wire gauge (row 110 (c)): outputs %s + inputs %s.' % (', '.join(sorted(n for n, a in outs if n in S.OUT_SMALL)), ', '.join(own_in)))
    L.add(G, 'Terminals', 'Mini fuse receptacle 2.8, 17-13 AWG (16-14 AWG outputs + the %d input jumpers)' % len(jumpers), '880398-2', 'TE Connectivity', 'Receptacle tab 2.8 x 0.8 mm, 1-2.5 mm2, tin, unsealed',
          n_big + len(jumpers), spare(n_big + len(jumpers)), unit=0.15, basis='est', url=TE('880398-2'), checked='TE page (2.8 x 0.8, 1-2.5 mm2, 17-13 AWG); ST185-CabinPower fb_logic contacts',
          note='Outputs %s (%d) + one per input jumper (%d, 14 AWG, C4). DM is 14 AWG (13 AWG max here).' % (', '.join(n for n, a in outs if n not in S.OUT_SMALL), n_big, len(jumpers)))
    L.add(G, 'Jumpers', 'Input jumper ring lug, 16-14 AWG, #8 / M4 (one per fuse input)', '53941-1', 'TE Connectivity',
          'PIDG closed ring tongue terminal, 16-14 AWG, #8 / M4 stud, blue, tin', len(jumpers), spare(len(jumpers)), unit=0.37, basis='seen',
          url=FUTURE_53941, checked='TE page 53941-1 2026-10-14 (PIDG, #8 / M4, 16-14, overall 20.65, tongue 0.78, Active); Future Electronics listing $0.37 at 50, 22,000 in stock',
          note='C4 (Dan, option C). R38 step 2 (TE). TE sells it through distributors only ("not currently available" direct): Future link. Ring / sleeve size from the PIDG family - read off the first sample.')
    L.add(G, 'Jumpers', 'Input jumper wire 14 AWG, ~60 mm each (%d), per foot' % len(jumpers), 'M22759/16-14-2', 'M22759 (Tefzel, red)', 'Wire, 14 AWG, ETFE, tin plated copper, 150 C, 600 V (the harness wire, ST185.harnesslib m16_14_2)',
          5, 2, unit=1.00, basis='est', url=AWC_M22759_16_14, checked='ST185.harnesslib wire part m16_14_2; AWC M22759/16-14 listing (19 strands tinned copper, ETFE, 600 V, 150 C)',
          note='%d x ~60 mm = %.1f m (5 ft) + spare. R38 step 4: no ProWire USA listing for M22759/16-14 confirmed; AWC sells it by the foot. The same reel as the harness 14 AWG if one is bought.' % (len(jumpers), len(jumpers) * 0.06))
    hw(L, G, 'Jumpers', 'M4x8', 'Hex bolt M4 x 8, into the tapped strip (one per jumper lug)', len(jumpers), spare(len(jumpers)), 0.08,
       note='Head on the lug side; 3.1 mm of thread past the strip, 0.68 mm short of the other strip (Fusion). Spare studs stay as tapped holes.')
    hw(L, G, 'Jumpers', 'M4spring', 'Spring washer M4 under each jumper bolt head', len(jumpers), spare(len(jumpers)), 0.05)
    lug(L, G, '2R5', 'Tubular lug 10 mm2, M5 hole (BUS1 8 AWG, BUS2 10 AWG feeds)', 2, 1, 0.70, 'Tinned copper tubular ring lug, 10 mm2, M5, hole 5.3', checked='Buerklin listing 07F2065')
    hw(L, G, 'Fasteners', 'M5x10', 'Hex bolt M5 x 10, feed lug into the tapped strip (2)', 2, spare(2), 0.10, note='Rev 6: no standoffs in the LOGIC box; the feed lug bolts straight onto the strip face.')
    L.add(G, 'Mounting', 'Compression limiter, feet (4)', 'EFC 10S00056', 'EFC International', 'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 6 mm, zinc-plated steel', 4, 1, unit=0.30, basis='est',
          url=EFC_URL, checked='see POWER list', note='C1. Mount bolts / nuts are not part of the box (C3).')

    # ================================================================ BATTERY relay block
    printed(B, 'BattRelay_Base', 'BattRelay Base', 'Floor plate, relay platform, fuse pedestal, 2 end tabs; PA12')
    printed(B, 'BattRelay_Cover', 'BattRelay Cover', 'Snap-on cover, side vents; PA12')
    L.add(B, 'Copper', 'Bar 25.4 x 6.35 x 36.5 mm, tinned (cut from the POWER bar stock)', 'MECCANIXITY B0CGJBRNJX', 'MECCANIXITY (Amazon)', 'Same 305 mm bar as the POWER bar: no extra stock to buy', 0,
          url='https://www.amazon.com/dp/B0CGJBRNJX', checked='stock bought in the POWER list', note='Holes: M6 feed 6.5, AMI 40 input 5.5.')
    L.add(B, 'Copper', 'Pad 15 x 3 x 17.5 mm, tinned (cut from the pad stock)', 'Bopaodao B09Z7NBLDK', 'Bopaodao (Amazon)', 'Same 1000 mm bar as the POWER pads: no extra stock to buy', 0,
          url='https://www.amazon.com/dp/B09Z7NBLDK', checked='stock bought in the POWER list')
    L.add(B, 'Relay', 'Fuel pump relay k_fp, HCR150, 12 V, 130 A, IP67', '1416010-1', 'TE Connectivity', 'High Current Relay 150 (V23132-A2001-B200), M6 screw load terminals, Superseal 1.5 coil plug', 1, url=TE('1416010-1'),
          checked='TE page + data sheet V23132-X0000-A001 (130 A contact, 150 A limiting, 3.9 W coil, M6 5 Nm, lug up to 25 mm2); te-on-hand-bom.csv qty_ordered 2',
          note='On the shelf. The second HCR150 is the k_eps relay (not in a box list).')
    L.add(B, 'Relay', 'Coil plug housing, Superseal 1.5, 2 pole', '282080-1', 'TE Connectivity', 'AMP Superseal 1.5 receptacle housing', 1, url=TE('282080-1'),
          checked='HCR150 data sheet "Connector Information": coil side housing 282080-1, wire seal 281934-2, contact 282110-1; te-on-hand-bom.csv qty_ordered 2',
          note='Earlier summary said BUY 1: it is on the shelf (OWN).')
    L.add(B, 'Relay', 'Coil plug contact', '282110-1', 'TE Connectivity', 'Superseal 1.5 receptacle contact (per HCR150 sheet)', 2, 1, url=TE('282110-1'), checked='HCR150 data sheet; te-on-hand-bom.csv qty_ordered 10',
          note='Earlier summary said BUY 2 for seal / contact: both on the shelf.')
    L.add(B, 'Relay', 'Coil plug wire seal', '281934-2', 'TE Connectivity', 'Superseal 1.5 single wire seal', 2, 1, url=TE('281934-2'), checked='HCR150 data sheet; te-on-hand-bom.csv qty_ordered 10')
    L.add(B, 'Fuses', 'AMI bolt-down fuse 40 A (FP)', 'AMI-40', 'Eaton Bussmann', 'AMI series 32 VDC, M5 ears', 1, unit=5.30, basis='seen', url=AMI_URL[40],
          checked='Waytek AMI-40 listing', note='Same part as the POWER AMI-40s: order them together.')
    lug(L, B, '1R6', 'Ring lug 6 mm2, M6 hole (feed in, relay terminal 3, relay terminal 5; 10 AWG)', 3, 1, 0.55, 'Tinned copper tubular ring lug, 6 mm2, M6 stud, hole 6.5, 27.5 long',
        note='10 AWG = 5.3 mm2, inside the 6 mm2 barrel.', checked='Voltus / Galaxus / RS listings; HCR150 sheet: M6 load screws, lug up to 25 mm2')
    lug(L, B, '2R5', 'Tubular lug 10 mm2, M5 hole (AMI out end of the jumper)', 1, 1, 0.70, 'Tinned copper tubular ring lug, 10 mm2, M5, hole 5.3', checked='Buerklin listing 07F2065')
    hw(L, B, 'Fasteners', 'M6bolt16', 'Hex bolt M6 x 16 (feed stud, 2 flange bolts)', 3, 1, 0.30)
    hw(L, B, 'Fasteners', 'M6nut', 'Hex nut M6 (feed stud, 2 flange nuts captured under the floor)', 3, 1, 0.06)
    hw(L, B, 'Fasteners', 'M6wash', 'Plain washer M6 (feed stud, 2 flange bolts)', 3, 1, 0.05)
    hw(L, B, 'Fasteners', 'M5x16', 'Hex bolt M5 x 16 (AMI input stud on the bar)', 1, 1, 0.12)
    hw(L, B, 'Fasteners', 'M5nut', 'Keps nut M5 (AMI input + output ears)', 2, 1, 0.07)
    hw(L, B, 'Fasteners', 'M5set', 'Set screw M5 x 12 (AMI output stud on the pad)', 1, 1, 0.12, note='No standoff in this box: the pad sits on the printed pedestal.')
    L.add(B, 'Mounting', 'Compression limiter, end tabs (2)', 'EFC 10S00056', 'EFC International',
          'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 6 mm, zinc-plated steel', 2, 1, unit=0.30, basis='est', url=EFC_URL,
          checked='EFC comparison table 2026-10-14; the end tab is 6 mm thick, so the L 6 part (rev 5 listed the L 4 one here)',
          note='C1. Mount bolts / nuts are not part of the box (C3).')
    L.add(B, 'Mounting', 'Compression limiter, HCR150 flange bosses (2)', 'EFC 10S00052', 'EFC International',
          'Knurled solid compression limiter, M6, ID 6.80, OD 9.8, L 4 mm, zinc-plated steel', 2, 1, unit=0.25, basis='est', url=EFC_URL,
          checked='EFC comparison table 2026-10-14; CAD rev 6 flange pocket OD 9.8 + 0.8, L 4', note='Under the relay flange, over the captured M6 nut.')
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


def write(rows, rev=6):
    for b, fn in (FILES7 if rev == 7 else FILES).items():
        with open(os.path.join(REV7_DIR if rev == 7 else FB, fn), 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, lineterminator='\n')
            w.writeheader()
            w.writerows(rows[b])


def lint(rows):
    """DECISIONS R82: every line is a real part with a live source link (the printed parts: file + PA12, no link)."""
    bad = []
    for b, rs in rows.items():
        for r in rs:
            who = '%s: %s' % (b, r['part_number'])
            printed = '.stl + .step (PA12)' in r['part_number']
            if not printed and not r['source_url'].startswith('http'):
                bad.append(who + ' has no source link')
            text = (r['part_number'] + ' ' + r['item']).upper()
            for w in ('TBD', 'EQUIVALENT', 'GENERIC', 'STOCK HARDWARE', 'OR EQUIV'):
                if w in text:
                    bad.append(who + ' contains "%s"' % w)
            if r['qty_need'] > 0 and not r['checked_against']:
                bad.append(who + ' has no "checked against"')
    return bad


NL, CRLF = chr(10), chr(13) + chr(10)


def render(rows, b):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator=NL)
    w.writeheader()
    w.writerows(rows[b])
    return buf.getvalue()


if __name__ == '__main__':
    REVN = 7 if '--rev' in sys.argv[1:] and sys.argv[sys.argv.index('--rev') + 1] == '7' else 6
    R = build(REVN)
    bad = lint(R)
    if '--check' in sys.argv[1:]:
        R7 = build(7)
        bad += ['rev 7 ' + m for m in lint(R7)]
        for (rows, files, d, cmd) in ((build(6), FILES, FB, ''), (R7, FILES7, REV7_DIR, ' --rev 7')):
            for b, fn in files.items():
                fp = os.path.join(d, fn)
                old = open(fp, encoding='utf-8', newline='').read().replace(CRLF, NL) if os.path.exists(fp) else ''
                if old != render(rows, b):
                    bad.append('%s%s is stale: run python cad/fusebox/src/parts_lists.py%s and commit it' % ('rev7/' if cmd else '', fn, cmd))
        for m in bad:
            print('PARTS LIST:', m)
        print('fuse box parts lists: %d problem(s)' % len(bad))
        sys.exit(1 if bad else 0)
    if bad:
        for m in bad:
            print('PARTS LIST (R82):', m)
        sys.exit(1)
    write(R, REVN)
    T = totals(R)
    for b in R:
        buy = sum(1 for r in R[b] if r['buy'] > 0)
        print('%-10s %2d lines, %2d with a BUY, est. $%.2f' % (b, len(R[b]), buy, T[b]))
