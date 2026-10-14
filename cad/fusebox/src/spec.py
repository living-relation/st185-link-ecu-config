"""ST185 glove-box fuse + relay box (one box, plan rev 2): layout spec shared by the Fusion build and the summary page.

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

WALL = 3.0           # 6061 tray wall
FLOOR = 3.0          # 6061 tray floor
DECK_Z0 = 25.0       # underside of the printed PA6-GF deck (22 mm cable bay below it, plan rev 2)
DECK_Z1 = 51.0       # deck top: terminal cavities + TPA comb live in these 26 mm
BAR_T = 6.0          # Al power bar / output pads thickness, sit in deck pockets
BAR_TOP = 53.0       # top of bar and pads (2 mm proud of the deck)
LID_Z = 79.5         # lid underside (tallest part: micro relay 51 + 25.4 = 76.4)
LID_T = 3.0
GAP = 3.0            # min gap between installed lugs (Dan's rule, bus bar)
CLR = 0.3            # pocket clearance per side (bus bar POCKET clr)

L = 254.5            # outer length (x)
D = 163.0            # outer depth (y)
H = LID_Z + LID_T    # 82.5 closed

# ---------- logic zone (inboard): mini fuses + micro relays
MINI = dict(l=10.92, w=3.81, h_above=9.0, pitch=8.1)
MINI_COLS = {   # x centre, fuses forward -> rear: (label, amps or None for a spare position)
    'BUS1': (11.5, [('EFI86', 5), ('HL', 15), ('HR', 15), ('HZ', 15), ('DM', 20), ('WL', 15), ('ALM', 5),
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
F7_POS = [('heater', '1-1414147-0', 'OWN'), ('k_efi', '1-1414147-0', 'OWN'), ('k_str', '1-1414147-0', 'BUY'),
          ('k_fan', '1-1414147-0', 'OWN'), ('k_fan2', '1-1393304-0', 'OWN'), ('power', '1-1393304-0', 'OWN'),
          ('SPARE', None, None), ('ACPS', None, None)]   # order: col 0 rows 0-3, col 1 rows 0-3
ACPS = ('ACPS', 10)

# ---------- power zone (outboard): one Al bar along y, AMI both sides, M8 1/0 input at the forward end
BAR = dict(x=190.0, w=25.0, y0=5.0, y1=158.0)
AMI = dict(L=41.0, c=30.0, body_l=16.0, body_w=12.0, body_h=6.0, ear_w=9.5, ear_t=0.8, hole=5.5)
AMI_IN_OFF = 6.25    # input stud offset from the bar centre line (both rows on one 25 mm bar)
AMI_PITCH = 16.0     # 2R5 pocket 12.6 + 3.4 wall >= GAP
AMI_Y0 = 40.0        # first fuse position centre
AMI_ROWS = {         # forward -> rear; amps None = spare position
    'IN':  [('HTR', 40), ('EFI', 30), ('STR', 30), ('FAN', 40), ('FAN2', 30), ('PWR', 30), ('SP', None), ('SP', None)],
    'OUT': [('BUS1', 50), ('RTR', 30), ('AM1', 40), ('AM2', 30), ('JB1', 60), ('EPS', 60), ('SP', None), ('SP', None)],
}
# 15 positions built (plan rev 2): the inboard row's 8th slot is left blank
AMI_SLOTS = {'IN': 7, 'OUT': 8}
AMI_COLOUR = {30: 'orange', 40: 'ltgreen', 50: 'red', 60: 'yellow'}
PAD = dict(inner=6.5, outer=11.0, w=14.5)   # output pad extent from its stud (toward bar / away from bar), width
LUG_M5 = dict(b=12.0, l=22.0, tip=6.0, t=2.0, d4=7.0)
LUG_M8 = dict(b=20.0, l=47.0, tip=10.0, t=3.0, d4=14.0)
IN_STUD_Y = 19.0
M5_NUT = dict(af=8.0, h=4.0)
M8_NUT = dict(af=13.0, h=6.5)

# ---------- mounting: 4 Al ears, nylon shoulder washers above and below (box floats 1.5 mm off the mount face)
EAR = dict(len=14.0, w=20.0, t=4.0, hole=10.0, ys=(30.0, 130.0))
ISO = dict(od=16.0, id=5.5, t=1.5, sleeve_od=9.5)
LID_SCREWS = [(WALL + 3.2, WALL + 3.2), (L - WALL - 3.2, WALL + 3.2), (WALL + 3.2, D - WALL - 3.2), (L - WALL - 3.2, D - WALL - 3.2)]  # M3, in r7 corner bosses
WIRE_EXIT = dict(x0=10.0, x1=L - 10.0, z0=6.0, z1=22.0)     # forward wall, under the deck
IN_GROMMET = dict(d=22.0)                                     # outboard end wall, 1/0 entry
