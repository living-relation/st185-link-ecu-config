"""ST185 glove-box fuse + relay boxes (rev 5: base + snap-on cover + snap-on belly pan; TWO boxes + a battery relay block):
layout spec shared by the Fusion build and the summary page.

Rev 5 (Dan's review of rev 4, 2026-10-14, 11 points, task card fusebox rev 5): vent slots in every cover; the battery block's
cover shown from every side (it was only in the closed view) and its tabs moved to the short ends; exploded and step-by-step
install views; every cable drawn to the box edge (harness wires drop out of each terminal, bend at 3 x OD and run in bundles
to one exit edge); rugged look (bumper band + ribs on the covers, angular legs); short standoffs where a lug needs no bend
(OUT row and LOGIC feeds: lug right under the deck, 12 mm); a snap-on belly pan under each glove-box box covers every live
part underneath; lid labels stay the rev 4 etched names (Dan: "the lid labels were fine as they were"). POWER relays turned 90 deg (30 / 87 along x) so
the harness wires leave in straight bundles that never cross a feed wire; the bar moved 8.5 mm outboard for it.

Rev 4 (Dan's review of rev 3, 2026-10-14, task card fusebox rev 4): bottoms left open (no tray floor, no side wire slot) -
each glove-box box is a printed BASE (the deck, on four corner legs with ears) and a snap-on printed COVER (rounded shell,
etched labels for every relay and fuse). Terminals are crimped, then pushed into the deck from the wire side (below).
Every heavy cable leaves its lug dead straight: the AMI output lugs sit UNDER the deck on brass hex standoffs; the relay
feeds make one 90 deg bend each, round a printed saddle (R_SADDLE) that sets and supports the radius. Bend rule: FAA AC
43.13-1B CHG 1 par 11-96 aa (p.11-44/45): bundles >= 10 x OD of the largest wire; at a terminal breakout, where the
wire is suitably supported, >= 3 x OD. No cable maker publishes a bend radius for M22759/16 or SGX (checked:
Thermax / ProWire M22759/16 sheet, Southwire SPEC 50050, AWC, Prestolite). Battery block: Blue Sea Systems 7720
Safety Fuse Block style (low base, snap cover, cables in at the open ends, no holes), 2 side tabs, nothing over a tab.

Rev 3 (R75): two boxes (POWER outboard, LOGIC inboard) + battery relay block. Rev 3.1 (R76): tinned copper stock, cut +
drilled only. Rev 2 (R73): PA12 powder-bed printed housings - walls >= 2.0 (>= 3 where loaded), ribs not solid blocks,
no closed cavities, 0.4-0.5 mm between printed parts, no printed threads, every bolted joint clamps metal to metal.

All dimensions in mm. Each box has its own local frame: x along the box (inboard -> outboard), y depth (forward /
firewall = 0 -> rearward), z up, 0 = the mount face (underside of the legs). The build moves each box to its place.
Claude Code, 2026-10-14.

Maker drawings (no guessed dims; copies in the main checkout's untracked _research/fusebox-ds/):
  AMI    - Bussmann AMI series sheet (Cooper Bussmann TP p.34): 41.0 long, 30.0 stud centres, body 16.0 x 12.0 x 6.0,
           ear 9.5 wide x 0.8 thick, hole 5.5, 4 Nm max.
  F7     - TE Power Relay F7 (V23134) data sheet 2023-03: body 25.9 +/-0.3 square x 24.9; 30/87 blades 9.5 x 1.2.
  Micro  - TE Micro Relay A (V23074) catalog 1308028: 23 max x 15.5 max x 25.4 max.
  Mini   - Bussmann ATM: 10.92 x 3.81 x 16.3; 8.1 mm fuse centre lines (Eaton 15400 RFRM sheet).
  Lugs   - Klauke 6R8 (50 mm2, M8): b 20, l 47. Klauke 2R5 (10 mm2, M5): b 12, l 22. Klauke 3R5 (16 mm2, M5): b 13, l 26.
  Wire   - M22759/16 max OD (Thermax sheet via ProWire USA, p.41): 12 AWG 2.97, 10 AWG 3.61, 8 AWG 5.13, 6 AWG 6.43,
           18 AWG 1.85, 20 AWG 1.57. 1/0 SGX battery cable OD 13.3 nominal (Southwire SPEC 50050, 0.523 in); 13.6 used
           (Prestolite SGX up to 0.537 in).
"""

CLR = 0.4            # metal part in a printed pocket, per side (MJF)
PCLR = 0.45          # printed part to printed part, per side
RIB = 2.5            # rib / gusset thickness
SKIRT = 3.0          # deck perimeter skirt (the base's side wall)
PLATE = 6.0          # deck top plate
TOWER = 2.5          # wall round each terminal-cavity group
GAP = 3.0            # min gap between installed lugs (Dan's rule, bus bar)
D = 181.0            # base depth (y), both glove-box boxes
BASE_R = 10.0        # base plan corner radius
COVER = dict(t=2.5, R=BASE_R + 0.45 + 2.5, r=5.0, over=13.0, clear=1.5)   # wall, plan corner R, top edge round, skirt overlap below the deck top, over the tallest part
SNAP = dict(w=12.0, slot=1.2, len=11.0, bump=2.4, z_from_top=10.0)         # cantilever tongue in the cover skirt, half-round bump into a pocket in the base skirt
LABEL = dict(depth=0.6, h_relay=3.6, h_ami=3.0, h_mini=2.4, h_micro=2.8)  # etched into the cover top (HP MJF: engraved text >= 0.5 deep); rev 4 names kept (Dan)
VENT = dict(w=2.6, l=14.0, pitch=18.0)   # vent slot through the cover: 2.6 wide keeps fingers and tools out (IP2X finger probe is 12.5)
RUG = dict(band_h=6.0, band_out=1.5, rib_w=3.0, rib_out=1.5, rib_pitch=30.0)   # cover bumper band + side ribs (rugged look)
LEG = dict(w_bot=24.0, w_top=16.0, out_top=4.0, out_slope=18.0, foot_out=22.0, foot_w=20.0, ear_t=6.0, hole=8.4, wall=3.0,
           ear_len=16.0, ear_w=20.0)
# rev 5 angular leg (Dan: "angular legs, less dumb looking"): a hollow buttress on a skirt face, 24 wide at the foot tapering
# to 16 at the top, outer face sloping from 4 proud of the skirt (top) to 18 out (foot); a flat foot with the M5 hole 22 out
# (brass limiter); open underneath (no closed cavity, R73). ear_len / ear_w: the battery block's flat end tabs.
PAN = dict(t=2.5, z0=1.5, over=4.0, gap=2.0)   # belly pan: floor underside 1.5 above the mount face, wall slides 4 up inside the skirt
LIMITER_M5 = dict(od=8.0, id=5.3, l=6.0)
HEAD = {5: dict(af=8.0, k=3.5), 6: dict(af=10.0, k=4.0), 8: dict(af=13.0, k=5.3)}   # ISO 4017 hex bolt heads
INSERT_M3 = dict(hole=4.0, depth=6.0)

# ---------- heights (z, from the mount face). Rev 5: belly pan floor 1.5-4.0, 2 mm air, IN-row lug bolt head 6-9.5, palm 9.5.
LUG_Z = PAN['z0'] + PAN['t'] + PAN['gap'] + 3.5   # palm underside of every IN-row (relay feed) lug = 9.5
LUG_C = LUG_Z + 3.5              # barrel centre (Klauke d4 7)
R_SADDLE = 16.0                  # printed saddle radius = inside bend radius of every relay feed (8 AWG needs 3 x 5.13 = 15.4)
STANDOFF = dict(af=8.0, long=40.0, short=12.0, thread=5)    # brass hex standoff M5 female-female (Essentra 301540040050, 40 mm): long = IN row (feeds that bend); short = OUT row + LOGIC feeds (straight, 12 mm in this CAD rev - Dan wants one 40 mm part number, see parts_lists.py)
TOWER_H = {'POWER': 20.5, 'LOGIC': 22.0}                     # deck top to deck underside (terminal cavity length)

# ---------- logic zone (inboard): mini fuses + micro relays
MINI = dict(l=10.92, w=3.81, h_above=9.0, pitch=8.1)
MINI_COLS = {   # x centre, fuses forward -> rear: (label, amps or None for a spare position)
    'BUS1': (12.5, [('EFI86', 5), ('HL', 15), ('HR', 15), ('HZ', 15), ('DM', 20), ('WL', 15), ('ALM', 5),
                    ('ALMS', 2), ('ALTS', 2), ('ETB', 10), ('SP', None), ('SP', None)]),
    'BUS2': (27.0, [('LAM', 7.5), ('SW12', 7.5), ('COP', 15), ('INJ', 15), ('CSB', 5), ('DEV', 15), ('EPSEN', 7.5),
                    ('ACC', 10), ('ALMIG', 2), ('SP', None), ('SP', None), ('MRS', 7.5), ('B30', 2)]),
}
MINI_Y0 = 28.0       # first fuse centre
MICRO = dict(x=15.5, y=23.0, h=24.1)
MICRO_COLS = (44.0, 63.0)
MICRO_Y = (21.0, 51.0, 81.0, 111.0, 141.0)
MICRO_POS = [('HEAD LH', '5-1393292-8', 'OWN'), ('HEAD RH', '5-1393292-8', 'OWN'), ('horn', '4-1904124-3', 'OWN'),
             ('k_etb', '4-1904124-2', 'OWN'), ('k_acc', '6-1419137-4', 'OWN'), ('k_eps_en', '6-1419137-4', 'OWN'),
             ('k_rev', '6-1419137-4', 'BUY'), ('SPARE', None, None), ('SPARE', None, None), ('SPARE', None, None)]

# ---------- F7 relays (middle): 2 columns x 4 rows; 8th spot holds the ACPS mini fuse next to the heater relay
F7 = dict(body=25.9, h=24.9)
F7_COLS = (87.0, 117.0)
F7_ROWS = (26.0, 62.0, 98.0, 134.0)
F7_POS = [('k_efi', '1-1414147-0', 'OWN'), ('k_str', '1-1414147-0', 'OWN'), ('k_fan', '1-1414147-0', 'OWN'),
          ('k_fan2', '1-1393304-0', 'OWN'), ('power', '1-1393304-0', 'OWN'), ('SPARE', None, None),
          ('heater', '1-1414687-0', 'BUY'), ('ACPS', None, None)]   # col 0 rows 0-3, col 1 rows 0-3; ACPS beside heater (L3B)
ACPS = ('ACPS', 10)
# heater relay = TE Power Relay F4 A, 1 form C, 680 ohm resistor (V23136-A0004-X059 = 1-1414687-0), data sheet V23136X0000A004 2023-09:
# Mini ISO, 1 form C NO 40 A / NC 30 A limiting continuous at 85 C (= the 40 A AMI HTR fuse). It REPLACES the Power Relay B 1-1904020-2
# (V23234-A0001-X032): TE lists every V23234 1 form C as Superseded. The pocket below is still the Power Relay B drawing (body 28.5
# (-1) square x 25.3 (-0.6); 85-86 16.8, 87 7.9 from the 85/86 line, 87a 8.35 from 87, 30-87 17.9): same ISO 7588 Mini pattern, check the
# F4 A drawing (V23136-A0004-X059-CD) against it at the next Fusion rebuild.
RELAY_B = dict(body=28.5, h=25.3, pos='heater', v87a=7.65 - 8.35)
# ---------- power zone (outboard): one Al bar along y, AMI both sides, M8 1/0 input at the forward end
BAR_METAL = 'CuC110'   # Y2 decided (Dan, 2026-10-14, R76): tinned copper, off-the-shelf flat bar, cut + drilled only
METAL = {'Al6061': dict(name='Al6061', density=2.70, iacs=43), 'CuC110': dict(name='CuC110', density=8.89, iacs=100)}
AMI = dict(L=41.0, c=30.0, body_l=16.0, body_w=12.0, body_h=6.0, ear_w=9.5, ear_t=0.8, hole=5.5)
AMI_IN_OFF = 6.25    # input stud offset from the bar centre line (both rows on one 25 mm bar)
AMI_PITCH = 18.0     # pad 15 (3 x 15 tinned stock) + 3.0 gap (printed rib 2.2 between neighbouring outputs)
AMI_Y0 = 43.0        # first fuse position centre
AMI_ROWS = {         # forward -> rear; amps None = spare position
    'IN':  [('HTR', 40), ('EFI', 30), ('STR', 30), ('FAN', 40), ('FAN2', 30), ('PWR', 30), ('SP', None), ('SP', None)],
    'OUT': [('BUS1', 50), ('RTR', 30), ('AM1', 40), ('AM2', 30), ('JB1', 60), ('EPS', 60), ('SP', None), ('SP', None)],
}
# 15 positions built (plan rev 2): the inboard row's 8th slot is left blank
AMI_SLOTS = {'IN': 7, 'OUT': 7}   # rev 3.1: 14 positions (2 spare) - the 18 mm pitch leaves no room for an 8th
AMI_COLOUR = {30: 'orange', 40: 'ltgreen', 50: 'red', 60: 'yellow'}
PAD = dict(inner=6.5, outer=11.0, w=15.0, t=3.0)   # output pad: 17.5 cut from 3 x 15 tinned bar; stud = M5 bolt from below
LUG_M5 = dict(b=12.0, l=22.0, tip=6.0, t=2.0, d4=7.0)
LUG_M8 = dict(b=20.0, l=47.0, tip=10.0, t=3.0, d4=14.0)
IN_STUD_Y = 22.0     # 1/0 input stud on the POWER bar
M5_NUT = dict(af=8.0, h=4.0)
M8_NUT = dict(af=13.0, h=6.5)

# ---------- POWER box (local frame). Relays on the inboard half, AMI bar outboard. Each relay sits where its feed lands:
# the AMI IN-row output lug points inboard, the wire runs straight under the deck and turns up round a saddle into the
# relay's terminal 30 (30 is 10.25 off the relay centre, so the relay centre is the fuse line + 10.25).
POWER = dict(L=180.5, x_bar=128.5)                   # rev 5: bar 8.5 outboard (relays turned 90 deg: the column A feed needs the room)
POWER['z_d'] = 32.0                                   # deck underside >= LUG_C + R_SADDLE + 8 AWG OD / 2 = 31.6
POWER['z_t'] = POWER['z_d'] + TOWER_H['POWER']        # deck top
POWER['bar_top'] = POWER['z_t'] + 2.0                 # bar and pads 2 mm proud of the deck
POWER['out_lug_z'] = POWER['bar_top'] - 3.0 - STANDOFF['short'] - 2.0   # OUT-row lug palm, right under the deck plate (6 AWG barrel top 0.5 under it)
assert abs(POWER['bar_top'] - 3.0 - 2.0 - LUG_Z - STANDOFF['long']) < 0.01, 'IN-row standoff length'
# Relays turned 90 deg in rev 5: terminal 30 on the +x side on its fuse line, 87 7.65 inboard of the centre, 85 / 86 at +-8.45 in y.
# Then every harness wire (87, 87a, 85, 86, ACPS) drops, bends at 3 x OD toward -x and runs in a bundle along a line no feed wire
# uses (87 on the fuse line inboard of the feed's bend; coils half way between fuse lines) out of the inboard end.
BAR_T = 6.35                                          # power bar: 1" x 1/4" tinned copper flat bar (R76), in a deck pocket
BAR = dict(w=25.4, y0=10.0, y1=158.0)                 # cut from 1" x 1/4" x 12" tinned bar (R76)
F7_X = (16.5, 45.5)                                   # relay columns: B (odd fuse lines) inboard, A (even)
ACPS_Y = 35.0                                         # ACPS mini fuse at the front of column B (fed from heater 87)
# AMI IN-row fuse i feeds relay i; even i -> column A, odd -> column B
IN_RELAY = ['heater', 'k_efi', 'k_str', 'k_fan', 'k_fan2', 'power', 'SPARE']
RELAY_PN = {'heater': ('1-1414687-0', 'BUY'), 'k_efi': ('1-1414147-0', 'OWN'), 'k_str': ('1-1414147-0', 'OWN'),
            'k_fan': ('1-1414147-0', 'OWN'), 'k_fan2': ('1-1393304-0', 'OWN'), 'power': ('1-1393304-0', 'OWN'), 'SPARE': (None, None)}
LUG_6AWG = dict(b=13.0, l=26.0, tip=6.0, t=2.0, d4=8.5)   # Klauke 3R5 (JB1 HOT 60 A)

# ---------- LOGIC box (local frame): rev 3 zone positions kept; strip feeds on standoffs under the deck, lug to the rear
STRIP = dict(w=10.0, t=3.0)                           # logic strips: 10 x 3 tinned bar
LOGIC = dict(L=79.0, z_d=20.0)                        # rev 5: z_d set by the harness bundles under the deck (checked in the build)
LOGIC['z_t'] = LOGIC['z_d'] + TOWER_H['LOGIC']
LOGIC['strip_top'] = LOGIC['z_t'] - 4.0               # strip 4 below the deck top (fuse receptacles above it)
LOGIC['feed_lug_z'] = LOGIC['strip_top'] - 3.0 - STANDOFF['short'] - 2.0

STRIP_FEED = dict(ext={'BUS1': 16.5, 'BUS2': 23.5}, hole_from_end=7.0)  # strip runs on past its cavity tower; feed lugs > 3 apart
FEEDS = {'BUS1': ('AMI BUS1 50 A output', 8), 'BUS2': ('k_efi 87', 10)}   # (from, AWG) - wires run box to box

PLACE = {'LOGIC': (0.0, 0.0), 'POWER': (160.0, 0.0), 'BATTRELAY': (0.0, -175.0)}   # world (x, y) of each box's local origin (renders only)

# ---------- wires at every lug / stud / terminal
OD = {'1/0': 13.6, 6: 6.43, 8: 5.13, 10: 3.61, 12: 2.97, 14: 2.41, 16: 2.06, 18: 1.85, 20: 1.57}
# AWG per AMI position (ENGINE-ROOM-POWER-REDISTRIBUTION 8.1 slot map; a fuse-to-relay jumper takes the relay-in gauge)
AMI_AWG = {'HTR': 8, 'EFI': 12, 'STR': 12, 'FAN': 8, 'FAN2': 8, 'PWR': 10,
           'BUS1': 8, 'RTR': 10, 'AM1': 8, 'AM2': 10, 'JB1': 6, 'EPS': 8}
RELAY_OUT_AWG = 8      # largest wire on any Mini ISO terminal (fan 87, heater 87): bends below the deck
LOGIC_MAX_AWG = 12     # largest wire on a mini fuse / micro relay receptacle (DOME 12 AWG)
# rev 5 harness tails (drawn to the box edge). Gauge per fuse rating in the usual ampacity steps - the harness files set the
# real gauge. Relay 87 = the gauge of its AMI feed; coils 20 AWG; micro relay loads 16 AWG.
MINI_AWG = {2: 20, 5: 20, 7.5: 18, 10: 18, 15: 16, 20: 12}
COIL_AWG, MICRO_LOAD_AWG, ACPS_AWG, H87A_AWG = 20, 16, 14, 18

# ---------- battery relay block (trunk, passenger side between rear wall and battery, Z4): HCR150 + AMI 40
# One straight line along x: battery feed (-x end) -> M6 stud -> AMI 40 -> straight jumper -> HCR150 terminal 3;
# terminal 5 -> pump cable straight out the +x end. The AMI sits on a printed pedestal so its lug is at the HCR150
# terminal height: the jumper has no bend. Rev 5: two tabs, one on each SHORT end (Dan), at y 67, clear of the cables; every cable leaves an end.

# ---------- battery relay block (trunk, near the battery): fuel pump relay + its fuse (R75; R15 exception)
# Relay: TE HCR150 V23132-A2001-B200 = 1416010-1 (on hand, 2 ordered; the second was the dropped battery-kill relay).
# TE data sheet V23132 03-2014: body 63 x 45, 40 deep off the flange face; flange holes 84 apart (6.5 dia + 7.5 x 6.5
# slot), 13.5 above the body's terminal edge; M6 screw load terminals 17 apart, 65.2 to their ends; 2-pole Superseal
# 1.5 coil plug to 71; 130 A at 85 C (16 mm2 cable 120 A), 3.9 W coil (0.33 A - Link Aux 3 is a 2 A low side).
HCR = dict(body_x=63.0, body_y=45.0, depth=40.0, holes=84.0, hole_d=6.5, hole_z=13.5, term_pitch=17.0,
           term_to=65.2 - 45.0, plug_to=71.0 - 45.0, term_w=14.0, flange_t=3.0)
RB = dict(L=184.0, D=92.0, floor=4.0, rim=12.0,     # base outer; relay on its flange face (40 deep), flange raised 6 on bosses
          y_b=40.0,                                  # relay body terminal edge (body y_b .. y_b + 45)
          x_stud=20.0, x_ami_in=38.0, x_t3=118.0,    # M6 battery stud, AMI in (out = +30), HCR150 terminal 3 (5 = +17): 18 mm jumper
          bar=dict(x0=8.0, x1=44.5, w=25.4, t=6.35),       # ends 0.5 short of the AMI body
          term_z=(14.0, 34.0),                       # terminal blocks set back 10 from the flange face (TE side view)
          lim_m6=dict(od=10.0, id=6.5, l=4.6), tab_y=67.0,   # rev 5: one tab on each SHORT end at y 67, clear of the cables (y 13-30)
          cover_h=50.0, fuse=('FP', 40), awg_feed=10, awg_pump=10, awg_coil=20)
REFERENCE_BRAND = ('Blue Sea Systems 7720 Safety Fuse Block (AMI / MIDI)',
                   'Chosen by Claude (Dan, Z9 2026-10-14: "your pick"; DECISIONS S27). It fits all four asks: open frame (a low base and a '
                   'cover - no closed tub); lid on, no screws (the cover is a separate part that comes off by hand); no cable holes (its cover '
                   'breakouts give wire access from three directions, so cables come in under the cover, not through the base); and it takes '
                   'the same AMI fuse we use, built for wet, vibrating places (marine). 125 x 38 mm for one fuse (Blue Bottle Marine listing '
                   'BS-7720). The one change: its 2 fixings become 2 end tabs (rev 5: Dan wants the mounts on the short ends), set beside the cables so none leaves over a tab. Not chosen: Bussmann RTMR (a '
                   'Mini ISO / mini-fuse module - no room for the HCR150 and an AMI); MTA / Littelfuse sealed power-distribution boxes (closed '
                   'tubs with cable seals, i.e. holes, the opposite of open); Blue Sea MRBF terminal blocks (they sit on the battery post).')

# ---------- R76: off-the-shelf tinned copper stock (Dan: no machined bars; cut, drill and tap are OK). Picks first.
# Prices seen on amazon.com / the seller page 2026-10-14 (they move); none of these is a TE part - TE sells no bar stock (R38 step 4).
STOCK = {
    'bar': ('Power bars (POWER box 148 mm + battery block 36.5 mm)', [
        ('PICK', 'MECCANIXITY 12" x 1" copper flat bar, 1/4" thick, tinned', 'Amazon B0CGJBRNJX', '25.4 x 6.35 x 305', '$26.19',
         'https://www.amazon.com/dp/B0CGJBRNJX', 'One bar makes both power bars with 120 mm left over.'),
        ('alt', 'Tinned copper flat bus bar 3 x 25 x 200 mm, C110 (Bopaodao listing)', 'Amazon B09Z7KJV65', '25 x 3 x 200', '$27.79',
         'https://www.amazon.com/dp/B09Z7KJV65', 'Thinner: still 75 mm2 of copper (> the 53 mm2 1/0 feed); 200 mm covers the POWER bar only.'),
        ('alt', 'TEN-HIGH tinned copper flat bar 5 x 30 x 1000 mm', 'Amazon B08NT3YSXT', '30 x 5 x 1000', '$109.49',
         'https://www.amazon.com/dp/B08NT3YSXT', 'Plenty of stock; 30 wide needs a 5 mm wider bar pocket.'),
    ]),
    'pad': ('Output pads (14 POWER + 1 battery block, 17.5 long each)', [
        ('PICK', 'Tinned copper flat bus bar 3 x 15 x 1000 mm, C110 (Bopaodao listing)', 'Amazon B09Z7NBLDK', '15 x 3 x 1000', '$51.99',
         'https://www.amazon.com/dp/B09Z7NBLDK', '15 pads use 290 mm with saw kerf; the rest is spare.'),
        ('alt', 'Same stock, 3 x 15 x 200 mm', 'Amazon B09Z7N2CP6', '15 x 3 x 200', '$24.99 each (buy 2)',
         'https://www.amazon.com/dp/B09Z7N2CP6', '10 pads per piece.'),
        ('alt', 'MECCANIXITY 2 pcs 12" x 1" x 1/8" tinned', 'Amazon B0CGJC2S1L', '25.4 x 3.2 x 305 (2)', '$27.19',
         'https://www.amazon.com/dp/B0CGJC2S1L', 'Pads would be 25.4 long, not 17.5 - the box grows about 8 mm; only if the 15 mm stock is gone.'),
    ]),
    'strip': ('Logic strips (Bus 1 118 mm, Bus 2 133 mm)', [
        ('PICK', 'Tin-plated copper bus bar 716426, 1000 x 10 x 3 mm', 'Nassau National Cable 716426', '10 x 3 x 1000', '$60.09',
         'https://nassaunationalcable.com/products/tin-plated-copper-bus-bar-716426-pack-of-3', 'Both strips from one length.'),
        ('alt', 'Tinned C110 copper bus bar 3 x 10 x 1000 mm', 'Amazon B0GWHX98C1', '10 x 3 x 1000', '$166.91',
         'https://www.amazon.com/dp/B0GWHX98C1', 'Same size, much dearer.'),
        ('alt', 'Nickel-plated copper flat bus bar 3 x 10 x 1000 mm (Bopaodao listing)', 'Amazon B0B1VKYJS1', '10 x 3 x 1000', '$56.99',
         'https://www.amazon.com/dp/B0B1VKYJS1', 'Nickel, not tin - fine against tinned terminals, but not what R76 asks for.'),
    ]),
}
READY_MADE = ('Bussmann LMI (AMI modules on a common bus bar, B109-7046-x)', 'The only ready-made AMI bus found. It is R18 Option B, which R70 replaced: '
              '25 mm per position (vs 18 here) and its own housings, so it does not fit the printed boxes.')
