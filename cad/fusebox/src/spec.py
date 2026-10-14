"""ST185 glove-box fuse + relay boxes (rev 3: TWO boxes + a battery relay block): layout spec shared by the Fusion build
and the summary page.

Rev 3 (Dan, 2026-10-14, Y1, DECISIONS R75): the rev 2 box is split in two along the gap between the logic zone and the
F7 relays - POWER box (AMI bar + Mini ISO relays + ACPS) outboard, LOGIC box (mini fuse strips + micro relays) inboard -
plus a small relay block at the battery (trunk) for the fuel pump relay (the spare on-hand TE HCR150). Every zone keeps
its rev 2 x position below; each box is a window [x0, x1] on that common x axis, and the build moves each box to its own
place. The logic strips get a feed lug each (BUS1 from the AMI BUS1 output, BUS2 from k_efi 87). The heater relay is
the TE Power Relay B 1 form C (Mini ISO, 87a), so its cavity has the 5th terminal. The power bar metal is a switch
(BAR_METAL) while Dan picks aluminium or copper (Y2).

Rev 2 (Dan, 2026-10-14, R73): every housing part is printed by powder-bed fusion (HP MJF / SLS, PA12): tray, deck, lid,
mounting ears. Only current-carrying parts are metal (bar, pads, strips, studs, lugs). PA12 (HP 3D HR PA 12 data sheet):
HDT 175 C at 0.45 MPa, 95 C at 1.82 MPa, tensile ~48 MPa. Design rules: walls >= 2.0 (>= 3 where loaded), ribs not
solid blocks, no closed cavities (no trapped powder), 0.4-0.5 mm between printed parts, threads only in brass heat-set
inserts, every bolted joint clamps metal-to-metal through brass compression limiters.

All dimensions in mm. x = along the box, inboard (ECU side) -> outboard (RH kick / bus bar); y = depth, forward
(firewall, wire exit) = 0 -> rearward; z = up, 0 = underside of the aluminium tray.
Claude Code, 2026-10-14. Dan's answers: L1 AMI studs, L4 smallest sensible footprint (glove box is not a limit),
L5 custom box (replaces R18 Option B).

Maker drawings (no guessed dims; copies in the main checkout's untracked _research/fusebox-ds/):
  AMI    - Bussmann AMI series sheet (Cooper Bussmann TP p.34): 41.0 long, 30.0 stud centres, body 16.0 x 12.0 x 6.0,
           ear 9.5 wide x 0.8 thick, hole 5.5, 4 Nm max.
  F7     - TE Power Relay F7 (V23134) data sheet 2023-03: body 25.9 +/-0.3 square (26.2 max) x 24.9 (25.2 max);
           QC terminals 17 long; 30/87 blades 9.5 x 1.2, 85/86 6.3 x 0.8; bottom view 85-86 16.9 apart,
           30-87 17.9 apart, 87 2.7 in from the edge.
  Micro  - TE Micro Relay A (V23074) catalog 1308028: 23 max x 15.5 max x 25.4 max (24.1 body); 4.8 / 6.3 blades.
  Mini   - Bussmann ATM: 10.92 x 3.81 x 16.3; 8.1 mm fuse centre lines (Eaton 15400 RFRM sheet).
  Lugs   - Klauke 6R8 (50 mm2, M8): b 20, l 47, hole 8.4 (RS 398-3015 / Express Electrical listing) -> 1/0 input.
           Klauke 2R5 (10 mm2, M5): b 12, l 22 (Klauke sheet via Rapid 04-6163) -> AMI outputs, 8-10 AWG.
           6 AWG (16 mm2) J/B1 HOT lug = Klauke 3R5, hole 5.5 (Buerklin); its b is NOT confirmed - pocket sized
           for b 12, check on the 3R5 drawing before machining.
"""

WALL = 3.0           # printed tray wall (loaded: >= 3)
FLOOR = 3.0          # printed tray floor
DECK_Z0 = 25.0       # underside of the printed PA6-GF deck (22 mm cable bay below it, plan rev 2)
DECK_Z1 = 51.0       # deck top: terminal cavities + TPA comb live in these 26 mm (towers, not a solid block)
PLATE_Z0 = 43.0      # deck top plate underside (8 mm plate; 4 mm left under the bar / pad pockets)
SKIRT = 3.0          # deck perimeter skirt
RIB = 2.5            # rib thickness (deck, ears, lid)
TOWER = 3.0          # wall around each terminal-cavity group, down to DECK_Z0
DECK_RIBS_X = (162.0, 172.0, 208.0, 218.0)   # ribs under the power-zone plate, along y (parallel to the wire run)
BAR_T = 6.35         # power bar: 1" x 1/4" tinned copper flat bar (R76), sits in a deck pocket
BAR_TOP = 53.0       # top of bar and pads (2 mm proud of the deck)
LID_Z = 79.5         # lid underside (tallest part: micro relay 51 + 25.4 = 76.4)
LID_T = 2.5
LID_RIB = dict(h=3.0, w=2.0, pitch=40.0)   # ribs on top of the lid (flat PA12 plates warp)
GAP = 3.0            # min gap between installed lugs (Dan's rule, bus bar)
CLR = 0.4            # metal part in a printed pocket, per side (MJF)
PCLR = 0.45          # printed part to printed part, per side

L = 254.5            # outer length (x)
D = 181.0            # outer depth (y)
H = LID_Z + LID_T + LID_RIB['h']   # 85.0 closed

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
          ('heater', '1-1904020-2', 'BUY'), ('ACPS', None, None)]   # col 0 rows 0-3, col 1 rows 0-3; ACPS beside heater (L3B)
ACPS = ('ACPS', 10)
# heater relay = TE Power Relay B, 1 form C (V23234-A0001-X032 = 1-1904020-2, 680 ohm resistor, no bracket), data sheet
# ENG_DS_V23234_X0000_A001 11-2018: body 28.5 (-1) square x 25.3 (-0.6); terminals 11.5 long; bottom view 85-86 16.8,
# 87 7.9 from the 85/86 line, 87a 8.35 from 87, 30-87 17.9. Same ISO 7588 pattern as the F7 plus 87a. NO 35 A at 85 C.
RELAY_B = dict(body=28.5, h=25.3, pos='heater', v87a=7.65 - 8.35)

# ---------- power zone (outboard): one Al bar along y, AMI both sides, M8 1/0 input at the forward end
BAR = dict(x=190.0, w=25.4, y0=10.0, y1=158.0)   # cut from 1" x 1/4" x 12" tinned bar
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
IN_STUD_Y = 22.0
M5_NUT = dict(af=8.0, h=4.0)
M8_NUT = dict(af=13.0, h=6.5)

# ---------- mounting: 4 Al ears, nylon shoulder washers above and below (box floats 1.5 mm off the mount face)
EAR = dict(len=18.0, w=22.0, t=6.0, hole=8.4, gusset_h=14.0, ys=(30.0, 150.0))   # printed, M5 through a brass limiter
LIMITER_M5 = dict(od=8.0, id=5.3, l=6.0)    # ears
HEAD = {5: dict(af=8.0, k=3.5), 6: dict(af=10.0, k=4.0), 8: dict(af=13.0, k=5.3)}   # ISO 4017 hex bolt heads, captured in printed hex pockets
STRIP = dict(w=10.0, t=3.0, z1=44.0)        # logic strips: 10 x 3 tinned bar, top at z1
INSERT_M3 = dict(hole=4.0, depth=6.0)       # brass heat-set insert, M3 (lid + deck screws); hole per insert maker - TBD part
POSTS = [(20.0, 13.0), (20.0, 165.0), (145.0, 14.0), (100.0, 167.0)]   # tray posts the deck screws into (M3 inserts)
POST_D = 10.0
LID_SCREWS = [(WALL + 3.2, WALL + 3.2), (L - WALL - 3.2, WALL + 3.2), (WALL + 3.2, D - WALL - 3.2), (L - WALL - 3.2, D - WALL - 3.2)]  # M3, in r7 corner bosses
WIRE_EXIT = dict(x0=10.0, x1=L - 10.0, z0=6.0, z1=22.0)     # forward wall, under the deck
IN_GROMMET = dict(d=22.0)                                     # outboard end wall, 1/0 entry

# ---------- rev 3: the two glove-box boxes are windows on the common x axis above (inner walls at x0 + WALL, x1 - WALL)
BOXES = {
    'LOGIC': dict(x0=0.0, x1=79.0, place=(0.0, 0.0),            # mini fuse strips + micro relays
                  posts=[(20.0, 13.0), (12.0, 168.0), (44.0, 167.0)], ears_y=(30.0, 150.0)),
    'POWER': dict(x0=69.0, x1=L, place=(140.0, 0.0),           # Mini ISO relays + ACPS + AMI bar (world x; LOGIC + ears end at 97)
                  posts=[(145.0, 14.0), (85.0, 165.0), (145.0, 167.0)], ears_y=(30.0, 150.0)),
}
STRIP_FEED = dict(ext=16.0, hole_from_end=7.0)   # logic strip extended at the rear; M5 bolt down through it, feed lug + nut underneath
FEEDS = {'BUS1': ('AMI BUS1 50 A output', 8), 'BUS2': ('k_efi 87', 10)}   # (from, AWG) - wires run box to box

# ---------- battery relay block (trunk, near the battery): fuel pump relay + its fuse (R75; R15 exception)
# Relay: TE HCR150 V23132-A2001-B200 = 1416010-1 (on hand, 2 ordered; the second was the dropped battery-kill relay).
# TE data sheet V23132 03-2014: body 63 x 45, 40 deep off the flange face; flange holes 84 apart (6.5 dia + 7.5 x 6.5
# slot), 13.5 above the body's terminal edge; M6 screw load terminals 17 apart, 65.2 to their ends; 2-pole Superseal
# 1.5 coil plug to 71; 130 A at 85 C (16 mm2 cable 120 A), 3.9 W coil (0.33 A - Link Aux 3 is a 2 A low side).
HCR = dict(body_x=63.0, body_y=45.0, depth=40.0, holes=84.0, hole_d=6.5, hole_z=13.5, term_pitch=17.0,
           term_to=65.2 - 45.0, plug_to=71.0 - 45.0, term_w=14.0, flange_t=3.0)
RB = dict(L=150.0, D=110.0, floor=4.0, wall=3.0, lid_z=48.0,  # tray outer; relay lies on its flange face (40 deep)
          relay_xy=(95.0, 62.0),                             # body centre; terminal edge toward -y (y 39.5)
          term_z=(14.0, 34.0),                               # terminal blocks set back 10 from the flange face (TE side view)
          bar=dict(x=24.5, w=25.4, y0=18.0, y1=56.0, z0=14.0, t=6.35),    # cut from the same 1" x 1/4" tinned bar
          in_stud_y=28.0, ami_in_y=50.0,                     # M6 battery input stud, then the AMI along +y
          lim_m6=dict(od=10.0, id=6.5), ami_y=None, pedestal_ribs=3, ears_y=(25.0, 85.0),
          fuse=('FP', 40), place=(0.0, -170.0))

# ---------- R76: off-the-shelf tinned copper stock (Dan: no machined bars; cut, drill and tap are OK). Picks first.
# Prices seen on amazon.com / the seller page 2026-10-14 (they move); none of these is a TE part - TE sells no bar stock (R38 step 4).
STOCK = {
    'bar': ('Power bars (POWER box 148 mm + battery block 38 mm)', [
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
    'strip': ('Logic strips (Bus 1 117 mm, Bus 2 125 mm)', [
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
