"""ST185 glove-box fuse + relay boxes (rev 6: base + snap-on cover + snap-on belly pan; TWO boxes + a battery relay block):
layout spec shared by the Fusion build and the summary page.

Rev 6 (Dan's answers to the rev 5 parts questions, 2026-10-14, DECISIONS R85): C1 - M6 compression limiters (EFC 10S00056,
L 6) in all 10 mount points (POWER / LOGIC feet, battery block end tabs); the HCR150 flange bosses take EFC 10S00052 (L 4).
C4 (= option C, replaces "stud fuses") - the LOGIC mini blade fuses stay; each fuse input is a short 14 AWG jumper: TE
880398-2 receptacle in the input cavity, TE PIDG 53941-1 ring lug (#8 / M4) bolted to its bus strip. The strips stand on edge
(25.4 x 3.2 tinned), back to back either side of a printed spine, straight under each column's input blades, so every jumper
drops straight down into its lug (no bend); lugs alternate between two rows (3 mm between lugs, Dan's rule). BUS1 inputs
face +x, BUS2 inputs face -x, so the two strips sit between the fuse columns; the micro relay columns move 4 mm outboard.
LOGIC deck 18.5 mm higher (room for the jumpers above the harness bundles). C3 - mount bolts / nuts are not part of the
boxes (parts lists). B5 - every standoff is the one 40 mm part (POWER OUT row now 40 mm too; LOGIC has none any more: its feed
lugs bolt straight onto the strips).

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
import math


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

# R127 amendment (Dan 2026-10-16: "this outer wall is still too thin for my liking" ... "you can't thicken inward because of the terminals.
# you have to just thicken out a tiny bit"): every outer wall of a base keeps >= OUTER_MIN behind its deepest pocket (the catch pockets,
# (bump + 0.2) / 2 deep), so the skirt / rim grows OUTWARD only by what that needs; the cover grows with it, same clearances.
OUTER_MIN = 3.0
SKIRT_OUT = round(max(0.0, OUTER_MIN - (SKIRT - (SNAP['bump'] + 0.2) / 2)), 2)   # POWER / LOGIC skirt 3.0 -> 4.3
RIM_OUT = round(max(0.0, OUTER_MIN - (4.0 - (SNAP['bump'] + 0.2) / 2)), 2)       # battery block rim 4.0 (R128) -> 4.3
LABEL = dict(depth=0.6, depth7=0.5, h_relay=3.6, h_ami=3.0, h_mini=2.4, h_micro=2.8)  # etched into the cover top (HP MJF: engraved text >= 0.5 deep); rev 4 names kept (Dan)
VENT = dict(w=2.6, l=14.0, pitch=18.0)   # vent slot through the cover: 2.6 wide keeps fingers and tools out (IP2X finger probe is 12.5)
RUG = dict(band_h=6.0, band_out=1.5, rib_w=3.0, rib_out=1.5, rib_pitch=30.0)   # cover bumper band + side ribs (rugged look)
LEG = dict(w_bot=24.0, w_top=16.0, out_top=4.0, out_slope=18.0, foot_out=22.0, foot_w=20.0, ear_t=6.0, hole=10.2, socket=17.0, wall=3.0,
           ear_len=16.0, ear_w=20.0)
# rev 5 angular leg (Dan: "angular legs, less dumb looking"): a hollow buttress on a skirt face, 24 wide at the foot tapering
# to 16 at the top, outer face sloping from 4 proud of the skirt (top) to 18 out (foot); a flat foot with the M6 hole 22 out
# (rev 6: steel M6 limiter, press fit 10.2 over its 9.8 knurl; socket clearance 17 for an M6 head); open underneath (no closed cavity, R73). ear_len / ear_w: the battery block's flat end tabs.
PAN = dict(t=2.5, z0=1.5, over=4.0, gap=2.0)   # belly pan: floor underside 1.5 above the mount face, wall slides 4 up inside the skirt
LIMITER_M6 = dict(od=9.8, id=6.8, l=6.0)         # EFC 10S00056: knurled solid, M6, OD 9.8, ID 6.8, L 6 (feet and end tabs, ear 6 thick)
LIMITER_M6_SHORT = dict(od=9.8, id=6.8, l=4.0)   # EFC 10S00052: L 4 (HCR150 flange bosses)
HEAD = {4: dict(af=7.0, k=2.8), 5: dict(af=8.0, k=3.5), 6: dict(af=10.0, k=4.0), 8: dict(af=13.0, k=5.3)}   # ISO 4017 hex bolt heads
INSERT_M3 = dict(hole=4.0, depth=6.0)

# ---------- heights (z, from the mount face). Rev 5: belly pan floor 1.5-4.0, 2 mm air, IN-row lug bolt head 6-9.5, palm 9.5.
LUG_Z = PAN['z0'] + PAN['t'] + PAN['gap'] + 3.5   # palm underside of every IN-row (relay feed) lug = 9.5
LUG_C = LUG_Z + 3.5              # barrel centre (Klauke d4 7)
R_SADDLE = 16.0                  # printed saddle radius = inside bend radius of every relay feed (8 AWG needs 3 x 5.13 = 15.4)
STANDOFF = dict(af=8.0, long=40.0, thread=5, depth=10.0)    # brass hex standoff M5 female-female, 40 mm: rev 6 = the ONE standoff, IN and OUT rows (B5);
# OPEN-5 (SteveCAD v3 F06, Claude 2026-10-16): Accu HHTPS-M5-8-40-BR-NI - same 8 AF x 40 envelope as the Essentra 301540040050 it replaces,
# but its listing states the thread depth (10 mm each end); Essentra's page could not be read, so its depth stayed unknown
# Pad stud (OPEN-5): M5 x 20 DIN 916 A2 set screw, 9.5 into the standoff (1.9 x D, 0.5 short of its 10 mm thread), then pad 3.0 + AMI ear 0.8
# + DIN 6923 nut 5.0, 1.7 past the nut (2 threads)
SETSCREW = dict(l=20.0, in_so=9.5)
# HP 3D High Reusability PA 12 data sheet 4AA6-4895ENE (2017): E 1700 MPa XY, tensile 48 MPa, elongation 20 % XY / 15 % Z, HDT 95 C XY at
# 1.82 MPa. Used by the snap-tab checks below.
PA12 = dict(E=1700.0, sy=48.0, nu=0.39)

# ---------- POWER outputs: copper C-strap per AMI position (N14 = B, Dan 2026-10-17: "do B"; DECISIONS R155 supersedes R146 / R144)
# Every POWER position - the 6 outputs, the 6 relay feeds (IN row, Dispatch 2026-10-17: "C-strap on all 12") and the 2 spares - is ONE bent
# copper strap instead of pad + 40 mm brass standoff + set screw: top leg under the AMI ear, web down through a well in the deck, bottom
# leg under the deck with the lug bolted palm-UP against its underside. Current runs ear -> copper -> lug on clamped flat copper faces only:
# no brass, no thread in the path (Dan's current rule: copper over brass over aluminium, never through threads).
# Hold (positive, no friction / glue): two side lips (the top leg's wings carried `lip` past the web, either side of a `neck` wide web
# top) rest on a printed ledge = DOWN stop; a printed snap hook reaches `over` across the lip ends = UP stop. Mirror image on the IN row
# (web inboard of the output stud, lug pointing -x to its relay saddle). Concept: _research/snapshots/2026-10-17-N14/B (concept B), with
# the edge distances below fixed for the real nuts.
#   stock: 3 x 15 tinned C110 (STOCK['pad'], Bopaodao B09Z7NBLDK, the old pad stock); ri inside bend radius (annealed C110 <= 1 t)
#   x offsets from the output stud x_out, + = the web side: web 5.25 .. 8.25, lug bolt 0.5 (bottom PEM 7.1 from the bottom leg end; its
#   head clears the web by 0.43); ledge: the printed ledge runs on this far past the lip ends to the hook slot (the ledge band is then
#   3.6 thick: R127 >= 3 for the DOWN stop, which on the OUT row stands over the belly-pan groove)
#   z: top leg = bar_top - t .. bar_top (the old pad), bottom leg z_bl .. z_bl + t, lug palm top = z_bl
STRAP = dict(t=3.0, w=15.0, w_low=14.2, ri=1.0, top_in=6.5, web=(5.25, 8.25), lip=2.0, ledge=1.9, neck=7.0, slit=6.0, z_bl=14.0, lug=0.5,
             clr=0.3, trim=0.6, kerf=0.5, k=0.33)
# w_low: below the top leg (web and bottom leg) the strap is milled / filed to 14.2 (= 2 x the PEM edge 7.1), so the PA12 wall between two
# neighbouring wells is 18 - 14.2 - 2 x 0.3 = 3.2 (R127 >= 3; at 15 wide it was 2.4); the top leg, the lips and the AMI ear face stay 15.
# trim: the top leg is cut 0.6 long, its top PEM pressed, then trimmed (see STRAP_PEM 'top_edge'). kerf: the saw cut either side of the
# neck tongue, so the tongue bends down while the lips beside it stay flat (lips 3.5 wide each). k: bend K-factor for the flat blank
# (annealed C110, ri / t = 0.33: K 0.33), bend allowance pi / 2 (ri + k t) per 90 deg bend - the shop checks the first blank (drawing note).
# PEM nuts in the strap (Dan's card: stainless; PennEngineering bulletin CL / pemnet.com product page CLSS-M5-2, read 2026-10-17): 300-series
# stainless self-clinching nut M5, shank code 2, mounting hole 6.35 +0.08, head E 8.64 x T 2.0, C max 6.33, min hole centre to edge 7.1,
# sheet HRB 70 / HB 125 or less (C110 copper is far softer). PEM's "Performance data for PEM fasteners installed into copper" (Rev. 5/22/20)
# lists only the steel type S: SS-M5-2 in 1.5 mm Cu-ETP torque-out 5.3 N.m, pushout 1080 N (SS-M5-2ZI = heat-treated steel, zinc - PEM
# Table II "S, SS and H: steel", so it is NOT the stainless part). CLSS has the same envelope; its copper figure is not published.
# top_edge: the AMI fuse body sits 7.0 from the ear stud (AMI c 30, body 16), so the top leg can only reach 6.5 from the top nut - under the
# 7.1 rule. The rule is about bulging the edge while the nut is pressed in: the blank is cut `trim` long (7.1), the nut pressed, THEN the end
# trimmed to 6.5 (drawing note); the ligament left round the knurl is 85 % of a 7.1 one. First article: torque check (drawing note).
STRAP_PEM = dict(pn='CLSS-M5-2', maker='PennEngineering (PEM)', hole=6.35, E=8.64, T=2.0, A=1.38, edge=7.1, top_edge=6.5,
                 url='https://www.pemnet.com/products/product-finder/clss-m5-2/', copper_torque_out_Nm=5.3, copper_pushout_N=1080)
# Bolt torque: AMI sheet 4 N.m max on the ear; the lug bolt the same. A nut only reacts the THREAD share of the bolt torque (the head share
# goes into the ear / palm): K = 0.2, mu 0.15 (thread and head), M5 d2 4.48, head bearing radius 3.3 -> preload F = T / (K d) and
# T_thread = F d2 / 2 (p / (pi d2) + 1.155 mu). See strap_numbers().
BOLT_T = dict(T=4.0, K=0.2, mu=0.15, d=5.0, d2=4.48, p=0.8, r_head=3.3)
# Snap hooks (UP stop). OUT row: the hook is on the base skirt - the skirt is the arm (freed by two side slots + an inner slot from `root`
# up), and the cover skirt overlaps it from outside, so with the cover on the hook cannot open. IN row: an arm cut free in the deck block by
# a slot ring (deck_tab style), inboard of the lips. w across the strap width (covers both lips), over = hook past the lip end (lip 2.0),
# t arm thickness, root = arm root z, hook_t hook thickness, slot 1.0 (> 0.5 MJF, S6). FEA: cad/fusebox/src/strap_fea.py.
STRAP_TAB = {'OUT': dict(w=12.0, over=1.5, t=None, root=35.0, hook_t=3.2, slot=1.0, lead=40.0, lead_z=0.3),
             'IN': dict(w=12.0, over=1.5, t=4.3, root=35.0, hook_t=3.2, slot=1.0, lead=40.0, lead_z=0.3)}
# lead / lead_z (buildability review 2026-10-18, DECISIONS R181): the hook's lead-in face, `lead` deg from the vertical, from `lead_z` above the
# hook underside - the bar-tab rule (BAR_TAB lead, R157), so it reaches 2.43 past the tip, beyond the lip end (over 1.5 + strap clr 0.3). The
# old 0.9 x 45 chamfer covered only 0.9 of the 1.5 catch: dropped straight down, the lip landed flat on the 0.6 of hook top past the chamfer
# (contact ~88 deg to the push, self-locking) and the strap could not go in without pushing the hook back by hand. Insertion sweep:
# _research/cad-buildability-final-2026-10-18.html (real STEP solids, 0.25 mm steps, all 14 stations).
# w 12 / slot 1.0: the PA12 left between two neighbouring arms' slots is 4.0 (R127 >= 3); the hook still covers 2.0 of each lip.
# Markup 2026-10-17 (Dan 23-15 / 23-17, DECISIONS R157): every hold-down hook bears on what it holds - its underside is level with the copper
# top (0 gap, was 0.1 over it) - and its arm stays inside the HP snap-fit strain limit. HP MJF Handbook, "Snap-fits" chapter: allowable strain
# < 1/3 x elongation at yield (eq. 7), base radius >= h / 2, assembly angle 35-40 deg; HP Jet Fusion 5200 PA 12 TDS: elongation at yield 10 % XY,
# 8 % Z. The arms stand up in Z, so SNAP_EPS = 8 / 3 = 2.67 %, 2.6 used. Strain 1.5 h y / L^2 (HP: y = 0.67 eps L^2 / h, rectangular beam).
# Strap arms: root 36.5 -> 35.0 (3.0 of skirt / block left under the slots) so the 4.3 arm stays under the limit with the hook on the lip
# (L 18.0 -> 19.5: 2.95 % -> 2.55 %); the strap lip is only 2.0 long, so the catch stays 1.5 (Dispatch card: >= 1.5 - 2); slots 0.6 -> 1.0.
SNAP_EPS = 2.6
HOOK_GAP = 0.0       # hook underside to the copper top (Dan 23-15: "a tab that doesn't touch holds nothing"); MJF +-0.25 gives 0 - 0.1 preload


def strap_blank():
    """Flat blank of the C-strap (shop drawing ST185-FB-117), measured along the strip from the TOP-leg end (after the trim; the cut
    blank is `trim` longer at that end). Bend allowance per 90 deg bend = pi / 2 (ri + k t); straights between the bend tangents."""
    st = STRAP
    ro = st['ri'] + st['t']
    ba = math.pi / 2 * (st['ri'] + st['k'] * st['t'])
    top = (st['web'][1] - ro) + st['top_in']                       # top-leg end -> first bend tangent
    web = (POWER['bar_top'] - ro) - (st['z_bl'] + ro)               # web between the bend tangents
    bot = (st['web'][1] - ro) - (st['lug'] - STRAP_PEM['edge'])     # second bend tangent -> bottom-leg end
    L = top + ba + web + ba + bot
    lip_end = top + (st['web'][1] + st['lip'] - (st['web'][1] - ro))           # the lips carry on flat past the first bend start
    neck_end = top + ba + (st['slit'] - (ro - st['t']))                          # the tongue is neck wide this far (model: slit under the leg)
    return dict(w=st['w'], w_low=st['w_low'], low_from=round(neck_end, 2), t=st['t'], length=round(L, 2), cut_length=round(L + st['trim'], 2), bend_allowance=round(ba, 3), ri=st['ri'], k=st['k'],
                straights=(round(top, 2), round(web, 2), round(bot, 2)), bend_centres=(round(top + ba / 2, 2), round(top + ba + web + ba / 2, 2)),
                pem_top=st['top_in'], pem_bottom=round(L - STRAP_PEM['edge'], 2), pem_hole=STRAP_PEM['hole'],
                kerf=dict(y=(st['neck'] / 2, st['neck'] / 2 + st['kerf']), x=(round(top, 2), round(lip_end, 2))),
                notch=dict(y=(st['neck'] / 2, st['w'] / 2), x=(round(lip_end, 2), round(neck_end, 2))))


def strap_numbers(amps_awg, t_hot=85.0):
    """Ampacity / temperature rise of the copper strap (Dan's rule: calculate it for anything non-standard), per position, and the bolt
    torque the PEM nut has to react. Method as concept B (_research/snapshots/2026-10-17-N14/B/B_numbers.json): C110 100 % IACS
    rho 1.72e-8 ohm.m, alpha 0.00393 /K; box ambient t_hot (cabin, -40 .. +85 C) + 10 K for the
    strap's own resistance; heat out by still air only (h 6 W/m2K on the perimeter, no heat out the ends = upper bound).
    The old part: pad 8 mm + 40 mm brass hex 8 AF (C36000, 26 % IACS; 20 mm of it tapped 10 deep each end).
    Path: the strap's own centre line (concept B summed 7 + 6 + 37 + 6.5 and counted the neck twice); the rise uses the narrowest long
    section (web / bottom leg, w_low x t) - the 7 mm neck is 11 mm long and clamped next to the ear, so it is listed (neck_W_per_m), not
    used for the rise."""
    rho, a = 1.72e-8, 0.00393
    t_, w_, n_ = STRAP['t'], STRAP['w'], STRAP['neck']
    A, An, Al = w_ * t_, n_ * t_, STRAP['w_low'] * t_
    ro = STRAP['ri'] + t_
    arc = math.pi / 2 * (STRAP['ri'] + t_ / 2)                       # bend centre line
    top = STRAP['web'][1] - ro                                       # ear centre -> first bend (full 15 x 3)
    neck = arc + (STRAP['slit'] - (ro - t_))                         # first bend + the slit under the leg, neck wide
    web = (POWER['bar_top'] - ro) - (STRAP['z_bl'] + ro) - (STRAP['slit'] - (ro - t_))   # rest of the web (14.2 x 3)
    bot = arc + (STRAP['web'][1] - ro - STRAP['lug'])                # second bend + bottom leg to the lug bolt (14.2 x 3)
    seg = [(top, A), (neck, An), (web, Al), (bot, Al)]
    R = lambda T: sum(rho * (l / 1000) / (s * 1e-6) for l, s in seg) * (1 + a * (T - 20))
    A_hex = math.sqrt(3) / 2 * 8.0 ** 2
    R_old = rho * (8.0 / 1000) / (A * 1e-6) + (rho / 0.26) * sum((l / 1000) / (s * 1e-6) for l, s in ((20.0, A_hex), (20.0, A_hex - math.pi * 2.1 ** 2)))
    h, perim = 6.0, 2 * (w_ + t_) / 1000
    rows = {}
    for name, (amps, awg) in amps_awg.items():
        qp = amps ** 2 * rho * (1 + a * (t_hot + 10 - 20)) / (Al * 1e-6)     # W/m along the web / bottom leg (14.2 x 3)
        qn = amps ** 2 * rho * (1 + a * (t_hot + 10 - 20)) / (An * 1e-6)     # W/m in the neck
        rise = qp / (h * 2 * (STRAP['w_low'] + t_) / 1000)
        rows[name] = dict(amps=amps, awg=awg, strap_W=round(amps ** 2 * R(t_hot + 10), 3), old_conductor_W=round(amps ** 2 * R_old * 1.15, 3),
                          strap_W_per_m=round(qp, 2), neck_W_per_m=round(qn, 2), rise_K_no_end_cooling=round(rise, 1), worst_strap_C=round(t_hot + rise, 1))
    B = BOLT_T
    F = B['T'] / (B['K'] * B['d'] / 1000)
    t_thread = F * (B['d2'] / 2000) * (B['p'] / (math.pi * B['d2']) + 1.155 * B['mu'])
    t_head = F * B['mu'] * B['r_head'] / 1000
    return dict(R_strap_uohm_20C=round(R(20.0) * 1e6, 1), R_strap_uohm_95C=round(R(t_hot + 10) * 1e6, 1), R_old_conductor_uohm_20C=round(R_old * 1e6, 1),
                joints=dict(strap='ear -> strap, strap -> lug: two clamped copper faces, no thread in the path',
                            old='ear -> pad, pad -> brass, brass -> lug (3) + the set-screw thread in parallel'),
                per_position=rows,
                bolt=dict(T_Nm=B['T'], preload_N=round(F), thread_share_Nm=round(t_thread, 2), head_share_Nm=round(t_head, 2),
                          nut_reaction_Nm=round(t_thread, 2), pem_torque_out_Nm=STRAP_PEM['copper_torque_out_Nm'],
                          margin=round(STRAP_PEM['copper_torque_out_Nm'] / t_thread, 1),
                          margin_trimmed_top=round(0.85 * STRAP_PEM['copper_torque_out_Nm'] / t_thread, 1),
                          note='torque-out = PEM copper data for the steel S type (SS-M5-2, same M5 / code 2 envelope); the CLSS copper figure is not '
                               'published - first-article check on the drawing'))
# Bar hold-down tabs (Dan N5: "add printed tabs that hold the bars down"): a snap arm cut free of the deck by a slot all round (`slot`), `t` thick,
# `w` wide, rooted `root` under the deck top; its hook reaches `over` past the bar edge (inside the 0.3 edge break) with a 45 deg lead-in, the
# underside square. The bar pushes the arm out by over + CLR on the way in. Battery block: the bar sits on its pedestal, so the arm stands
# on the floor beside the pedestal, `gap` off it. Arm strain 1.5 t d / L^2 and push force 3 E I d / L^3 are in the build report.
BAR_TAB = dict(t=2.2, w=6.0, root=16.0, slot=1.0, over=2.0, hook_t=2.5, gap=0.7, t_stand=4.0, w_stand=12.0, lead=40.0)
# t_stand / w_stand: the free arms on the battery block floor (35 long). Markup 2026-10-17 (R157): catch 1.0 -> 2.0, hook 1.6 -> 2.5 thick,
# root 12 -> 16 under the deck top (arm 14 -> 18 long: strain 1.5 x 2.2 x (2.0 + 0.4 CLR) / 18^2 = 2.44 % < SNAP_EPS), lead-in 40 deg
# (HP 35 - 40); battery block arms 6 x 3.5 -> 12 x 4.0 (Dan 23-06: "make these 2 tabs bigger").
TOWER_H = {'POWER': 20.5, 'LOGIC': 22.0}                     # deck top to deck underside (terminal cavity length)

# ---------- logic zone (inboard): mini fuses + micro relays
MINI = dict(l=10.92, w=3.81, h_above=9.0, pitch=8.1)
# rev 7 LOGIC clearance fix (Dan, 2026-10-14: 3 mm rule): everything outboard of the spine (Bus 2 column, both micro relay columns) sits
# 2.5 mm further outboard and the box is 2.5 mm wider (79 -> 81.5), so the Bus 1 / Bus 2 strips are 6.3 apart (rev 6: 3.8) and an M4 x 8
# jumper bolt tip (3.1 past its own strip) stays >= 3 mm from the other strip. Bus 1 cannot move inboard (its tail bundle meets the
# belly pan wall) and Bus 2 cannot move alone (its fuses would hit the micro relays), so the box grows instead. Same parts.
# N2 (PEM nuts): the M4 x 8 jumper bolt is the shortest that passes the nut (tip 3.12 past the strip, 1.12 past the nut head), and the
# upper row is now only 5.0 over the lower, so the Bus 1 and Bus 2 bolt tips at one y are 1.0 apart in z: the gap between the strips grows
# 6.3 -> 9.2 to keep Dan's 3 mm between Bus 1 and Bus 2 (tip to tip 3.1, tip to the other strip's nut head 4.1): again everything outboard
# of the spine moves out, by PEM_GROW, and the box is that much wider
PEM_GROW = 2.9
# N21 (Dan 2026-10-18: MCP 2.8 receptacles) + the fit audit: a mini fuse's blades are 8.1 apart (Littelfuse MINI 297 data sheet rev 09/27/2024 p.2:
# 10.9 over both blades, blades 2.8 wide), not the 6.0 the boxes had. MINI_BLADE_X = half the blade pitch. Each fuse column's sockets spread 1.05
# a side: Bus 1 stays (its tail bundle meets the pan wall), Bus 2 moves out 2 x 1.05 so the strips (on the input blades) keep their 9.2 gap, and
# everything outboard of Bus 2 (micro relay columns, box width) moves out 3 x 1.05 so Bus 2's outputs keep their clearance to the relays.
MINI_BLADE_X = (10.9 - 2.8) / 2
MINI_SLOT = (2.8 + 0.4, 0.8 + 0.8)    # blade slot above the seat: blade 2.8 x 0.8 (Littelfuse p.2) + 0.2 / 0.4 a side; the MCP box (3.10 x 4.40) stops on the 1.6 side
FUSE_GROW = MINI_BLADE_X - 3.0
MINI_COLS = {   # x centre, fuses forward -> rear: (label, amps or None for a spare position)
    'BUS1': (13.5, [('EFI86', 5), ('HL', 15), ('HR', 15), ('HZ', 15), ('DM', 20), ('WL', 15), ('ALM', 5),
                    ('ALMS', 2), ('ALTS', 2), ('ETB', 10), ('SP', None), ('SP', None)]),
    'BUS2': (37.5 + PEM_GROW + 2 * FUSE_GROW, [('LAM', 7.5), ('SW12', 7.5), ('COP', 15), ('INJ', 15), ('CSB', 5), ('DEV', 15), ('EPSEN', 7.5),
                    ('ACC', 10), ('ALMIG', 2), ('SP', None), ('SP', None), ('MRS', 7.5), ('B30', 2)]),
}
MINI_Y0 = 28.0       # first fuse centre (rev 6 / 7 up to 2026-10-17)
# Markup 2026-10-17 (Dan 23-21: "some are too close ... There is room to spread them out while keeping the bar the same size. don't need the
# extra positions"): the 4 spare fuse positions (BUS1 11 / 12, BUS2 10 / 11, no stud feed in use) are deleted and the rest spread out on ONE
# grid for both columns, so every Bus 1 stud still has its Bus 2 neighbour at the same y in the other row (the 3 mm Bus 1 / Bus 2 gate):
# pitch 8.1 -> 9.35 from y 31.7. 31.7 = the first Bus 1 stud's bolt head 3.0 clear of the Bus 1 feed lug (Dan's "overlap!!": at y 28 the head
# corner sat 0.6 inside the feed lug ring); 9.35 = the most that keeps the last Bus 1 stud at its PEM edge distance (strip end 124 - 6.9) and
# B30 (BUS2-13) in front of the Bus 2 feed lug ring. The cavity numbers keep their old numbers (BUS2-12 / -13 are in ST185-CabinPower).
MINI_GRID = dict(y0=31.7, pitch=9.35)
MINI_DROP = {'BUS1': (10, 11), 'BUS2': (9, 10)}     # spare positions deleted (index into MINI_COLS)
MINI_OWN_IN = {'BUS2': (11, 12)}                    # MRS / B30: own harness input, no stud


def mini_kept(col, i):
    return i not in MINI_DROP.get(col, ())


def mini_y(col, i):
    """y of fuse i (index into MINI_COLS[col]) on the shared grid: the kept positions in order."""
    k = [j for j in range(len(MINI_COLS[col][1])) if mini_kept(col, j)].index(i)
    return round(MINI_GRID['y0'] + k * MINI_GRID['pitch'], 3)


def mini_stud(col, i):
    """True where fuse i is fed by a jumper from a stud on its bus strip."""
    return mini_kept(col, i) and i not in MINI_OWN_IN.get(col, ())


def mini_list():
    """[(col, i, name, amps, x centre, y)] of every kept fuse position."""
    return [(col, i, nm, amps, cx, mini_y(col, i)) for col, (cx, fuses) in MINI_COLS.items() for i, (nm, amps) in enumerate(fuses) if mini_kept(col, i)]
MICRO = dict(x=15.5, y=23.0, h=24.1)
MICRO_COLS = (53.5 + PEM_GROW + 3 * FUSE_GROW, 72.0 + PEM_GROW + 3 * FUSE_GROW)    # rev 6: 5 / 4.5 mm outboard (the bus strips sit between the fuse columns); rev 7: + 2.5 (clearance fix);
                             # R123: + 2.0 so the Bus 2 output terminals (880398-2) keep their lance ledges next to the micro relay 85 (R73 2.0 wall)
MICRO_Y = (21.0, 51.0, 81.0, 111.0, 141.0)
# R127 sweep (Dan 2026-10-16: "fix the ones you found as long as they don't alter the function and installability of the parts"): the
# spots that stay under 2.0 mm / 3 mm because the part needs them that way. build_fusion.py records a box round each one in
# fusebox_report.json "wall_exempt"; cad/check_printed_walls.py leaves out what lies inside and lists it under these names.
WALL_EXEMPT = {
    'seat lip': 'R121: the deck top over each receptacle is the stop the terminal seats against; HOLE top_gap = 1.0 sets how far the '
                'relay / fuse blade goes into the receptacle (thicker = less blade engagement); webs between neighbouring blade slots follow the pin spacing',
    '87a slot': 'micro relay pin spacing (TE 1308028): the 87a blade slot sits 1.9 from the 85 / 86 cavities on the change-over and spare '
                'positions (the normally-open relays have no 87a slot any more)',
    'cover catch pocket': 'snap: the cover tongue bump sits in this pocket in the outer face of the 4.3 skirt / rim (3.0 left behind it); the bump size is the catch',
    'cover screw insert': 'R122: the M3 heat-set insert hole in its boss beside the catch',
    'pan catch pocket': 'snap: the belly-pan tongue bump sits in this pocket just above the skirt bottom edge - the lip under it is the catch (the pocket height is set by the pan bump)',
    'pan snap tongue': 'snap: the pan tongue between its two slots has to flex; its bump is the catch',
    'cover snap tongue': 'snap: the cover tongue between its two slots has to flex; its bump is the catch',
    'cover screw hole': 'R122: the 3.4 screw hole lines up with the insert 9.5 under the deck top - the 2.5 cover band keeps 1.8 under it',
    'label': 'rev 4 etched names (Dan: "the lid labels were fine as they were"): the PA12 between letter strokes, 0.5 deep; the cover top under the text is 2.0',
    'notch at corner': 'a cable exit notch (its size and place set by its cable) runs into a rounded corner of the cover / pan: the notch side '
                       'meets the curved wall at a slant; widening it opens the corner, moving it moves the cable',
    'relay cavity web': 'attachment only: the PA12 between the cavities of a micro relay (and between the 87a and 85 / 86 cavities of the POWER '
                        'heater relay, Power Relay B pattern) - its size follows the TE pin spacing and the R120 hole sizes, and it joins the box '
                        'at its corners between the cavities (2.0-2.9); the walls themselves pass W',
    'saddle lip': 'attachment only: the 2.0 lips each side of a POWER bend saddle (R127 amendment: whole curve, both lips kept) meet the saddle '
                  'core along the full curve; listed since the 2026-10-17 sweep filled the R2 - R7 slits, which split the thin network the '
                  'checker had joined them to (geometry unchanged)',
    'groove strip': 'attachment only: a 2.0 - 3.0 strip of PA12 between a terminal cavity and the groove the belly-pan wall slides up in, '
                    'hanging from the deck block (R128 cuts such strips only under 2.0); the cavity and the pan set it (geometry unchanged, '
                    'listed since the 2026-10-17 sweep)',
    'strip lip': 'LOGIC spine lips the bus strips slide in on (from the rear): 0.9 thick (spec.SPINE lip_t, z 4.6 - 5.5), 0.4 under the strip '
                 'and 0.6 over the belly-pan floor (z 4.0); thicker raises the strips (every stud row and PEM edge distance moves) or closes '
                 'the pan gap. Re-measured 2026-10-17 (SteveCAD sweep C7): the lips are this feature - the solid PA12 over the strips is not it',
    'bar snap tab': 'R146 / R155 (Dan N5: printed tabs that hold the bars down): the snap arm (2.2 thick) has to flex to let the bar in, and its hook '
                    '(1.6) carries no load but the bar\'s own lift; walls, slots and the arm are sized for MJF (slots 1.0 > 0.5 S6)',
    'lug pocket wall': 'markup 2026-10-17 (Dan 23-18 / 23-27 pockets, R160): attachment only - the PA12 wall between two NEG bus lug tongues is 2.2 '
                       '(3.0 between the tongues, Dan\'s lug rule, less 0.4 clearance each side); it only stops a lug turning while its nut is '
                       'torqued and stands on the raised pocket floor along its whole 26 mm length. One ground node (R135).',
    'strip snap hook': 'markup 2026-10-18 (Dan: the LOGIC strips must be held by printed tabs, R157 style): the arm over each strip\'s rear '
                       'end has to flex up 2.4 to let the strip slide in (STRIP_HOLD, 2.25 % < SNAP_EPS); its tooth is a 40 deg wedge '
                       '(R181 lead-in) with a 0.3 land, and the arm hangs free under the deck between its post and the tooth',
    'strap snap tab':'R155 (N14 = B): the snap arm over each copper strap\'s lips has to flex 1.5 to let the strap in (STRAP_TAB, FEA in '
                      'strap_fea.py); its slots are 1.0 (> 0.5 S6) and the ledge the lips rest on is between the well and the slot',
}
GAP_OPEN = 0.65      # SteveCAD sweep C1 (S6): least opening of a cavity-join bridge - HP MJF needs >= 0.5 between faces (check_printed_solid S6)
MICRO_NO = ('4-1904124-2',)     # normally-open micro relays: no 87a contact (no 87a blade)
# Fit audit 2026-10-18: 4-1904124-3 (horn) is V23074-A1001-A403 = 1 form C, resistor (TE Micro Relay A data sheet rev 1119 p.4 part table, te.com
# page, TE STEP: 5 blades) - it has an 87a blade, so it gets the 87a slot. 5-1393292-8 (V23074-A2001-A402-EV-CBOX, HEAD LH / RH): R170 (N26,
# Dan 2026-10-18) - TE customer drawing V23074-A2001-CD sheet 1 rev A (Dan's screenshot) shows 5 blades, 1 / 2 coil 4.8 x 0.8, 3 / 5 load
# 6.3 x 0.8, terminal 4 present, change-over circuit (3 = 30 common, 5 = 87 NO, 4 = 87a NC), as TE's 3D model c-5-1393292-8-o-3d.stp - so it
# gets the 87a slot like the horn (a plain blade slot: 87a has no harness wire).
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
RELAY_B = dict(body=28.5, h=25.3, pos='heater', v87a=-10.25 + 8.35)   # fit audit 2026-10-18: 87a is 8.35 from 87 (the far blade), was from 30
# ---------- relay pin patterns (fit audit 2026-10-18, Dispatch: "the maker drawings decide the pattern"). Each from the maker drawing, checked on
# TE's own STEP (cad/vendor/te/<pn>/, cad/vendor/INDEX.md). Until 2026-10-18 the micro pattern was an estimate ("set exactly in detail work") and
# the Mini ISO pattern had the coil line 1.6 off, the 30 blade turned the wrong way and the 30 / 87 names on the wrong blades.
# Micro Relay A (TE data sheet V23074 rev 1119 p.3, bottom view; STEPs 4-1904124-2/-3, 5-1393292-8, 6-1419137-4): 30 (terminal 3) 8 from 87
# (terminal 5), 87 6 from the coil row 85 / 87a / 86 (terminals 2 / 4 / 1, 4.5 apart), all on the relay's long axis; 87 is 11.4 from the body end
# = the body centre. Coil + is terminal 1 (the NOD / COD diode's cathode side) = 86, at +x; 85 (terminal 2, coil -) at -x. Box (dx, dy) from the
# relay centre (cx, cy); load blades 6.3 wide across the axis, 85 / 86 / 87a 4.8 wide along it.
MICRO_PINS = {'30': (0.0, -8.0), '87': (0.0, 0.0), '87a': (0.0, 6.0), '85': (-4.5, 6.0), '86': (4.5, 6.0)}
# Power Relay F7, Maxi ISO (TE data sheet V23134 rev 2607 p.3, bottom view; STEPs 1-1414147-0, 1-1393304-0): 85 - 86 16.9; 87 8.4 from the coil
# line, blade along it; 30 9.5 the other side (30 - 87 17.9), blade turned 90 deg; 87 2.7 from the 25.9 body edge. (u, v) in the build's F7 frame:
# box x = cx - v, y = cy + u. The heater relay (Power Relay F4 A 1-1414687-0, STEP; Power Relay B pattern): 87 7.9 from the coil line (85 - 86
# 16.8), 87a 8.35 from 87, 30 - 87 17.9.
F7_PINS = {'30': (0.0, 7.65), '87': (0.0, -10.25), '85': (-8.45, -1.85), '86': (8.45, -1.85)}
RELAY_B_PINS = {'30': (0.0, 7.65), '87': (0.0, -10.25), '87a': (0.0, RELAY_B['v87a']), '85': (-8.4, -2.35), '86': (8.4, -2.35)}
# Which harness pin (sot/channels.csv c1 = 30, c4 = 87) lands on which real blade. The box brings every AMI feed up round its saddle into the FAR
# blade (v -10.25) = the real 87, and takes the harness out of the NEAR blade = the real 30. The F7s are 1 form A (30 - 87 is one switch, either way
# round): DECISIONS R168 (N22 = A) puts the feed on 87; the heater (1 form C, DECISIONS R164): 87 = the 40 A feed, 30 = the blower, as on the car
# (1993 EWD p.215). ST185-CabinPower draws every POWER relay that way (OPEN-ITEMS rows 132 / 137), so harness pin = real blade for all six.
POWER_ROLE_POS = {'30': 'near', '87': 'far'}
# ---------- power zone (outboard): one Al bar along y, AMI both sides, M8 1/0 input at the forward end
BAR_METAL = 'CuC110'   # Y2 decided (Dan, 2026-10-14, R76): tinned copper flat bar stock; machined parts since D6 (Dan 2026-10-16, R76 amended)
# SteveCAD audit v3 (2026-10-16, Dan's D3 / D6): clearance holes ISO 273 medium, tapped holes modelled at the ISO coarse tap drill,
# every copper part is a machined part with a 0.3 x 45 deg edge break on every edge (hole rims included, F10).
CLEAR = {5: 5.5, 6: 6.6, 8: 9.0}     # ISO 273 medium clearance (F19: M8 8.5 -> 9.0, battery block M6 6.5 -> 6.6)
TAP_DRILL = {3: 2.5, 4: 3.3, 5: 4.2, 6: 5.0}   # ISO coarse tap drill (F07: LOGIC strip M4 4.0 -> 3.3, M5 5.0 -> 4.2)
CU_BREAK = 0.3                       # copper edge break, 0.3 x 45 deg on every edge (F10 / D6)
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
M5_NUT = dict(af=8.0, h=5.0)    # DIN 6923 M5 flange nut, m = 5.0 (F06: was drawn 4.0)
BOLT_L = {5: 16.0, 8: 25.0}     # bar bolts up through the bar from their printed hex pocket: M5 x 16, M8 x 25 (parts lists)
M8_NUT = dict(af=13.0, h=6.5)

# ---------- POWER box (local frame). Relays on the inboard half, AMI bar outboard. Each relay sits where its feed lands:
# the AMI IN-row output lug points inboard, the wire runs straight under the deck and turns up round a saddle into the
# relay's terminal 30 (30 is 10.25 off the relay centre, so the relay centre is the fuse line + 10.25).
POWER = dict(L=180.5, x_bar=128.5)                   # rev 5: bar 8.5 outboard (relays turned 90 deg: the column A feed needs the room)
POWER['z_d'] = 32.0                                   # deck underside >= LUG_C + R_SADDLE + 8 AWG OD / 2 = 31.6
POWER['z_t'] = POWER['z_d'] + TOWER_H['POWER']        # deck top
POWER['bar_top'] = POWER['z_t'] + 2.0                 # bar and pads 2 mm proud of the deck
POWER['out_lug_z'] = POWER['bar_top'] - 3.0 - STANDOFF['long'] - 2.0    # rev 6: OUT-row lug palm on the 40 mm standoff = the IN-row height (LUG_Z)
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

# ---------- LOGIC box (local frame). Rev 6 (C4): bus strips on edge between the fuse columns, one jumper per fuse input.
# BUS1 inputs on the +x blade (output -x), BUS2 inputs on the -x blade (output +x): both input lines face the strips.
MINI_IN = {'BUS1': +1, 'BUS2': -1}                    # side of the input blade (blades at cx +- MINI_BLADE_X)
STRIP = dict(h=25.4, t=3.2)                           # 1" x 1/8" tinned copper flat bar on edge (MECCANIXITY B0CGJC2S1L), PEM self-clinching nuts (N2)
# N2 (Dan 2026-10-16, OPEN-3 = A): the strip threads are PEM self-clinching nuts pressed into the copper, not tapped copper (3.2 mm gave M4
# 0.8 x D). PEM bulletin CL (S / SS / CLS / CLSS metric table) + pemnet.com product pages; PEM "Performance data for PEM fasteners installed
# into copper" tests type S in Cu-ETP (= C110): S-M4-1 in 1 mm 2.7 N.m torque-out, SS-M5-2 in 1.5 mm 5.3 N.m. Sheet: >= the shank code's
# min thickness (code 2: 1.4; the strip is 3.2, so the nut sits flush on the shank side, sub-flush 1.82 inside the hole) and softer than
# HRB 80 / HB 150 (copper C110 is far softer). The head (E x T) stands on the strip face AWAY from the lug, in the gap between the strips,
# so the lug palm sits on bare copper round the hole. hole = mounting hole (+0.08), edge = least hole centre to strip edge.
PEM = {4: dict(pn='S-M4-2ZI', hole=5.41, E=7.87, T=2.0, A=1.38, edge=6.9, url='https://www.pemnet.com/products/product-finder/s-m4-2zi/'),
       5: dict(pn='SS-M5-2ZI', hole=6.35, E=8.64, T=2.0, A=1.38, edge=7.1, url='https://www.pemnet.com/products/product-finder/ss-m5-2zi/')}
JLUG = dict(ring=8.0, t=0.78, L=20.65, neck=2.0, sleeve=5.3, hole=4.34, ax=2.26)
# TE PIDG 53941-1 (TE page 2026-10-14: #8 / M4 stud, 16-14 AWG, overall 20.65, tongue 0.78; blue sleeve). Ring 8.0 and sleeve 5.3
# are PIDG #8 family sizes, not on the TE page: read them off the first sample. ax = barrel axis off the palm mid-plane.
JBOLT = dict(m=4, l=8.0, washer_t=0.9, washer_od=7.6)  # RS 287-3915 M4 x 8 A2 + RS 231-0691 DIN 127B spring washer, into the PEM nut in the strip (R129)
JROW = dict(z_lo=12.8, dz=5.0)                        # palm centres: N2: lower row 5.9 + 6.9 PEM edge (was 10.0); upper row +5.0 (was 7.5), so the upper
                                                      # lug barrel still ends 4 under the deck (34.45 + 4 <= 38.5); one strip = one circuit (J1 = A)
JUMPER_AWG = 14      # the largest jumper (20 A DM); rev 6 / 7 used it on every input
# Markup 2026-10-17 (Dan 23-21: "does the wire and terminal have to be so large for these fuses?"): no - each jumper is sized by its own fuse,
# the same gauge the fuse's output wire takes (MINI_AWG: 2 / 5 A 20 AWG, 7.5 / 10 A 18, 15 A 16, 20 A 14). The jumper sits upstream of its mini
# fuse, so only the bus feed fuse is in front of it - the same short-tap basis as the 14 AWG jumper it replaces (14 AWG is not covered by the
# 50 A Bus 1 fuse either): one ~10 mm run inside the closed box, its load current capped by its own mini fuse. Terminals by gauge (TE pages,
# read 2026-10-17): 20 - 18 AWG -> receptacle 1241388-2 (MCP 2.8K, 0.5 - 1 mm2, already the small LOGIC output part) + ring TE 320554 (PIDG
# #8 / M4, 22 - 16 AWG, tongue 0.79, length 20.24, insulation 2.03 - 3.18: thin-wall 18 / 20 AWG gets the R120 RNF-100 build-up); 16 - 14 AWG
# -> 880398-2 + 53941-1 as before.
JLUG_SMALL = dict(JLUG, pn='320554', t=0.79, L=20.24, sleeve=4.6, ins=(2.03, 3.18))   # sleeve 4.6 est. (PIDG red family, not on the TE page)


def jumper(amps):
    """(awg, receptacle, ring lug pn, lug dims) of the input jumper of a mini fuse of this rating."""
    awg = MINI_AWG[amps]
    if awg >= 18:           # N21: TE MCP 2.8 receptacle by gauge (114-18148 Table 7)
        return awg, '1-968849-1', '320554', JLUG_SMALL
    return awg, '1-968851-1', '53941-1', JLUG
LOGIC = dict(L=83.5 + PEM_GROW + 3 * FUSE_GROW, z_d=38.5)                        # R123: 2.0 wider (micro relay columns out, self-locking ledges); rev 7: 2.5 wider (clearance fix; rev 6: 79.0); rev 6: deck 18.5 higher - upper lug barrel end 34.15 + 4 of jumper below the cavity
LOGIC['z_t'] = LOGIC['z_d'] + TOWER_H['LOGIC']
STRIP_Z0 = 5.9                                        # strip bottom edge, on the spine lips (pan floor top 4.0)
SPINE = dict(t=3.0, lip=3.2, lip_t=0.9)               # printed wall between the strips, lips under both strips (strips slide in from the rear)
# fit audit 2026-10-18: t 2.2 -> 3.0 - the strip rail (card item 13, 22-59) hangs on the spine, and R127 wants >= 3 mm under a held piece; the
# strips are 9.2 apart (PEM_GROW), so 3.1 of air stays each side; the M4 bolt-tip passes are cut through the spine as before
# Dan's drawing markup 2026-10-18 ("LOGIC box bars are still not secured ... must not rely on wires or one end stud, and must not float
# away from the wall"): each strip is held by the printed base on every side (R157 style), the copper is unchanged.
#   IN  (seated against the wall): the spine fills the gap to each strip, 0 gap, in a band under the PEM heads and a band over them
#        (pad_clr round the heads); the heads, bolt tips and feed nut keep the 3.0 spine and its passes between the bands.
#   OUT: a kerb on the lug face at the bottom edge (kerb_t thick, `catch` up the face, clear of the feed lug) and top lips (lip_t x >= lip_w:
#        R127 attachment >= 3) between the
#        jumper sleeves (lip_w wide, sleeve + lip_clr clear), both `gap` off the face (the kerb stops own_clr short of an own-input
#        wire - MRS / B30 drop down the jumper line and turn along the pan floor); the strips still slide in along the lips from the rear.
#   DOWN / UP: the lips and the rail (card item 13). FRONT: a stop pad on the J4 channel floor at the strip's front end.
#   REAR: a snap hook (arm along y, flexes up into the free space under the deck): its tooth drops `catch` behind the strip's rear end once
#        it has slid in; lead-in `lead` deg from the push direction from lead_z off the catch face (R181), arm t x arm_L for SNAP_EPS.
#        end_clr: the tooth sits that far behind the nominal strip end (the strip's +-0.5 length); defl_clr: arm underside over the strip top.
STRIP_HOLD = dict(gap=0.2, kerb_t=2.0, catch=2.0, lip_t=3.0, lip_w=3.0, lip_clr=0.5, sleeve=JLUG['sleeve'], feed_clr=6.5, own_clr=7.5, pad_clr=0.4,
                  arm_L=20.0, arm_t=2.5, arm_side=0.5, post=4.0, tooth=3.0, end_clr=0.5, defl_clr=0.4, lead=40.0, lead_z=0.3, slot=1.0)
# strip y extents and feeds: BUS1 feed at its front end (lug face, wire out the front), BUS2 feed at its rear end (wire out the rear)
# J4 = B (Dan, 2026-10-14, DECISIONS R94): the Bus 1 strip starts 3.5 later (8 -> 11.5) and its feed lug sits lower and 3 mm rearward
# (y 15 / z 22 -> y 18 / z 13), so a band opens in front of the spine where the HL / HR / ETB wires cross under the deck (CHANNEL below).
STRIP_Y = {'BUS1': (11.5, 124.0), 'BUS2': (21.1, 140.1)}     # N2: PEM edge distance at both ends (6.9 M4 / 7.1 M5): Bus 1 + 1.0 at the rear,
# Bus 2 starts 2.4 earlier (was 23.5: the Bus 1 feed bolt tip now keeps 3.4 in x from it across the wider gap) and ends 0.1 later
FEED = {'BUS1': dict(y=18.6, z=13.0, dir=-1), 'BUS2': dict(y=133.0, z=13.0, dir=+1)}   # N2: Bus 1 feed 0.6 rearward (PEM M5 edge 7.1)
STUDS = {'BUS1': 10, 'BUS2': 9}                       # stud positions per strip (markup 2026-10-17: spares deleted - see MINI_DROP / mini_stud)
FEEDS = {'BUS1': ('AMI BUS1 50 A output', 8), 'BUS2': ('k_efi 30', 10)}   # (from, AWG) - wires run box to box
# harness gauge per LOGIC output (ST185-CabinPower fb_logic contacts: 1241388-2 = 20-18 AWG, 880398-2 = 16-14 AWG)
OUT_SMALL = {'EFI86', 'ALM', 'ALMS', 'ALTS', 'CSB', 'EPSEN', 'ALMIG', 'MRS', 'B30'}

PLACE = {'LOGIC': (0.0, 0.0), 'POWER': (160.0, 0.0), 'BATTRELAY': (0.0, -175.0)}   # world (x, y) of each box's local origin (renders only)

# ---------- wires at every lug / stud / terminal
OD = {'1/0': 13.6, 6: 6.43, 8: 5.13, 10: 3.61, 12: 2.97, 14: 2.41, 16: 2.06, 18: 1.85, 20: 1.57}
# AWG per AMI position (ENGINE-ROOM-POWER-REDISTRIBUTION 8.1 slot map; a fuse-to-relay jumper takes the relay-in gauge)
AMI_AWG = {'HTR': 8, 'EFI': 12, 'STR': 12, 'FAN': 8, 'FAN2': 8, 'PWR': 10,
           'BUS1': 8, 'RTR': 10, 'AM1': 8, 'AM2': 10, 'JB1': 6, 'EPS': 8}
RELAY_OUT_AWG = 8      # largest wire on any Mini ISO terminal (fan 87, heater 87): bends below the deck
LOGIC_MAX_AWG = 14     # largest wire on a mini fuse / micro relay receptacle (rev 6: DM and the input jumpers, 14 AWG)
# rev 5 harness tails (drawn to the box edge). Gauge per fuse rating in the usual ampacity steps - the harness files set the
# real gauge. Relay 87 = the gauge of its AMI feed; coils 20 AWG; micro relay loads 16 AWG.
MINI_AWG = {2: 20, 5: 20, 7.5: 18, 10: 18, 15: 16, 20: 14}   # DM 20 A = 14 AWG (TE 880398-2 takes 13 AWG max; row 107)
COIL_AWG, MICRO_LOAD_AWG, ACPS_AWG, H87A_AWG = 20, 16, 14, 18
RELAY87_AWG = {'k_efi': 10}   # 87 tails whose harness gauge differs from the AMI feed (ST185-CabinPower w77_cp 10 AWG; OPEN-ITEMS 119 (a))

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
           term_to=65.2 - 45.0, plug_to=71.0 - 45.0, term_w=19.1, flange_t=3.0,   # term_w 14 -> 19.1: TE STEP terminal blocks reach 9.55 either side of a stud (fit audit 2026-10-18)
          
           term_x0=1.95, term_y=9.0)   # fit audit 2026-10-18: the M6 terminals are NOT centred between the flange holes - TE STEP c-1416010-1-a-3d.stp puts
                           # them at +1.95 / +18.95 from the hole midpoint (coil connector at -30.5 .. -11.3), as TE data sheet V23132 rev 0314 p.2
                           # front view shows (terminals right of centre, connector left); the box had them centred (10.45 off). term_y: the stud
                           # axes are 9.0 off the body's terminal edge (TE STEP; the box used term_to / 2 = 10.1)
RB = dict(L=184.0, D=92.0, floor=4.0, rim=12.0,     # base outer; relay on its flange face (40 deep), flange raised 6 on bosses
          y_b=40.0,                                  # relay body terminal edge (body y_b .. y_b + 45)
          x_stud=20.0, x_ami_in=38.0, x_t3=128.45,   # M6 battery stud, AMI in (out = +30), HCR150 terminal 3 (5 = +17); fit audit 2026-10-18:
                                                     # 118 -> 128.45 = the real stud (HCR term_x0), the relay body / holes stay at x 126.5
          bar=dict(x0=8.0, x1=44.5, w=25.4, t=6.35),       # ends 0.5 short of the AMI body
          term_z=(14.0, 34.0),                       # terminal blocks set back 10 from the flange face (TE side view)
          lim_m6=LIMITER_M6_SHORT, tab_y=67.0,   # rev 5: one tab on each SHORT end at y 67, clear of the cables (y 13-30)
          cover_h=50.0, fuse=('FP', 40), awg_feed=10, awg_pump=10, awg_coil=18, n_coil=2)   # coil plug: two 18 AWG leads (ST185-HeavyDC w_fp85_h / w_fp86_h; 119 (b))
REFERENCE_BRAND = ('Blue Sea Systems 7720 Safety Fuse Block (AMI / MIDI)',
                   'Chosen by Claude (Dan, Z9 2026-10-14: "your pick"; DECISIONS S27). It fits all four asks: open frame (a low base and a '
                   'cover - no closed tub); lid on, no screws (the cover is a separate part that comes off by hand); no cable holes (its cover '
                   'breakouts give wire access from three directions, so cables come in under the cover, not through the base); and it takes '
                   'the same AMI fuse we use, built for wet, vibrating places (marine). 125 x 38 mm for one fuse (Blue Bottle Marine listing '
                   'BS-7720). The one change: its 2 fixings become 2 end tabs (rev 5: Dan wants the mounts on the short ends), set beside the cables so none leaves over a tab. Not chosen: Bussmann RTMR (a '
                   'Mini ISO / mini-fuse module - no room for the HCR150 and an AMI); MTA / Littelfuse sealed power-distribution boxes (closed '
                   'tubs with cable seals, i.e. holes, the opposite of open); Blue Sea MRBF terminal blocks (they sit on the battery post).')

# ---------- R76: tinned copper flat bar stock (picks first). Amended 2026-10-16 (D6): the bars, pads and strips are machined from it
# (holes to the drawing, 0.3 x 45 edge break everywhere) - no longer cut + drill only.
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
    # SteveCAD sweep C6 (2026-10-17): lengths = STRIP_Y (N2 / R129 moved the ends for the PEM edge distance); holes = the PEM mounting
    # holes (S-M4-2ZI 5.41, SS-M5-2ZI 6.35, +0.08 / -0), never tapped (R129); a STEP reads 6.01 / 6.95 at the rims = the 0.3 x 45 edge break
    'strip': ('Logic strips on edge (Bus 1 %.1f mm, Bus 2 %.1f mm, 25.4 x 3.2)' % (STRIP_Y['BUS1'][1] - STRIP_Y['BUS1'][0], STRIP_Y['BUS2'][1] - STRIP_Y['BUS2'][0]), [
        ('PICK', 'MECCANIXITY 2 pcs 12" x 1" x 1/8" tinned copper flat bar', 'Amazon B0CGJC2S1L', '25.4 x 3.2 x 305 (2)', '$27.19',
         'https://www.amazon.com/dp/B0CGJC2S1L', 'Both strips from one bar (235 mm with kerf); the second bar is spare. Drill the PEM mounting holes '
         '(5.41 +0.08 at each M4 stud, 6.35 +0.08 at the M5 feed) and press in the PEM nuts (R129) - no tapping.'),
        ('alt', 'Tinned copper flat bus bar 3 x 25 x 200 mm, C110 (Bopaodao listing)', 'Amazon B09Z7KJV65', '25 x 3 x 200', '$27.79 each (buy 2)',
         'https://www.amazon.com/dp/B09Z7KJV65', 'One strip per piece; 3.0 thick (0.2 thinner - the lugs sit 0.2 further from their jumpers, fine).'),
    ]),
}
READY_MADE = ('Bussmann LMI (AMI modules on a common bus bar, B109-7046-x)', 'The only ready-made AMI bus found. It is R18 Option B, which R70 replaced: '
              '25 mm per position (vs 18 here) and its own housings, so it does not fit the printed boxes.')

# ---------- rev 7 (Dan's E2 = A, 2026-10-14, "make a separate new version so I can see it"): NO separate glove-box bus bar and NO
# copper bar of its own in the POWER box. The bus bar's POS bar (bus bar B rev3, Dan's E1 pick, re-made in tinned copper stock -
# R76, cut + drilled only) IS the AMI bar: the AMI fuses bolt straight onto it, and the POWER box is the holder + cover round it.
# The bar simply runs on past the last AMI position into a 62 mm "bus zone" at the rear of the box, where the B rev3 terminals
# land: on the POS bar BAT+ IN (H1), RADLOK+ (H3) and a spare M8; on a NEG bar (same stock, on flat, inboard of the POS bar)
# BAT- (H2), RADLOK- (H6a), GND ID / GND IG (H7) and one M8 for the small relay grounds (k_htr 87a, k_pwr 85, k_rev 85 - M8 rings
# in ST185-CabinPower). Every B rev3 1/0 set-screw port becomes a Klauke 6R8 lug on an M8 bolt (the milled port blocks broke R76).
# The B rev3 universal bar U + link strap / AMG fuse is dropped (the 2 spare AMI positions + the spare M8 stud take its place).
# Removed against rev 6: the 1/0 cable bus bar -> POWER box (ST185-CabinPower w_fb_in) and its two 1/0 lugs, the POWER box's own
# 148 mm copper bar, and the whole separate bus bar housing. LOGIC box and battery relay block: unchanged (their feeds do not move).
# A printed barrier wall stands between the NEG terminals and the POS bar. Box frame as rev 6: x inboard -> outboard, y front -> rear.
REV7 = dict(
    D=243.0,                                   # POWER box depth: rev 6 181 + 62 bus zone at the rear (y > 181)
    bar_y1=236.0,                              # POS bar: y 10 -> 236 (226 long), cut from 1" x 1/4" tinned (R76)
    pos_studs=[(178.0, 'BAT+ IN', 'H1'), (202.0, 'RADLOK+', 'H3'), (226.0, 'SPARE', None)],   # M8 on the POS bar, 1/0 lugs out +x
    neg_bar=dict(x0=5.0, x1=110.0, yc=205.0),  # NEG bar on flat along x (105 long, same stock), lugs out +y (rear end); N3: 1 mm outboard (was 4 - 109)
    neg_studs=[(15.0, 'BAT-', 'H2', '1/0'), (38.0, 'RADLOK-', 'H6a', '1/0'), (61.0, 'GND ID', 'H7', '1/0'), (84.0, 'GND IG', 'H7', '1/0'),
               (102.0, 'GND', 'relays', 'small')],   # 23 pitch = 20 lug + 3 gap (Dan's rule); GND: up to 3 small M8 rings
    # F05 (SteveCAD v3, 2026-10-16): GND stud off the bar end (103.5 -> 100.5). N3 (Dan 2026-10-16, OPEN-2: "I can get a tool in there", the
    # pitch is accepted if the air gap between the two NEG lugs / nuts meets spec): both lugs are the one ground node, so the spec is practical -
    # neg_lug_gap between ring edges (lugs turning under torque never touch) - and at 100.5 the 6R8 ring (b 20, Klauke) and the GND ring (b 13)
    # touched; the stud nudged to 102.0 (18.0 pitch) and the bar 1 mm outboard: hole centre 8.0 from the bar end, nut corner 1.0 from the barrier
    neg_lug_gap=1.5,                           # N3: least gap between NEG lug ring edges (one ground node: practical, not an electrical clearance)
    small_ring_b=13.0,                         # widest small M8 ring tongue (TE PIDG, 22-16 / 16-14 AWG M8 rings, ST185-CabinPower)
    small_awg=(14, 18, 20),                    # k_htr 87a 14, k_pwr 85 18, k_rev 85 20 (CabinPower t_pdb_gnd_*)
    barrier=(110.5, 113.5),                    # printed wall x between the NEG terminals and the POS bar pocket (115.4); 3.0 thick (R127 sweep, was 2.5)
    barrier_h=20.0,                            # wall above the deck top (lug barrels top out 13.9 above the bar)
    cover_snaps_rear=(124.0, 160.0),           # rear-face cover catches moved clear of the NEG cable notches
)

# ---------- Dan's markup 2026-10-17 (task card _research/TASK-fusebox-markup-1017.md, DECISIONS R157 - R160)
# Lug pockets (23-18 / 23-27: "WHERE ARE MY MACHINED 'POCKETS' FOR EACH RING TERMINAL TO SIT IN?"), the bus bar idea (cad/busbar spec.POCKET,
# Dan 2026-10-13) moved into the printed base: the lug palm keeps sitting on bare copper (copper to copper, nothing printed under the clamp);
# where its tongue / barrel leaves the copper it runs between printed walls (palm b + 2 x clr, barrel d4 + 2 x trough) over a printed floor
# `under` below the palm underside, so it cannot turn when its nut is torqued. Sizes from the lug drawings already in this file (LUG_M8 Klauke
# 6R8 b 20 / d4 14, LUG_M5 2R5 b 12 / d4 7, LUG_6AWG 3R5 b 13, the battery block 2R5 / 1R6 lugs).
POCKET = dict(clr=0.4, trough=0.5, under=0.3, wall=3.2, wall_neg=2.2, h_over_palm=2.0, wall_min=2.0)
# POS bus lugs (BAT+ IN, RADLOK+): walls along x from the bar edge to the box edge, z_t + POS_WALL_H high - the wall between the two is Dan's
# 23-31 "separating wall here"; the one in front of BAT+ starts behind the bar tab at y 164 (that tab's arm is the palm's front wall there).
POS_WALL_H = 20.0
# NEG front wall (23-31 "add more wall here", the orange lines): in front of the NEG terminals, from the skirt to the R7 barrier, as high and
# thick as the barrier.
NEG_FRONT_WALL = dict(y=(177.5, 180.5), x0=SKIRT - 0.01)
# Under-deck isolation ribs (23-27 T walls inside the skirt segments, 23-33 "tall features from the base that extend between each bar"): one rib
# between every two strap stations and one past each end, both rows, hanging from the deck block down to RIB_Z0 - the 3.2 PA12 wall between two
# strap wells carried on down past the straps' webs, bottom legs and lugs. At the lug palm height (z PALM_Z) the rib widens to the lug: walls
# b + 2 x clr apart = the pocket of every palm-up output lug (bolted from below, the socket fits the 12.8 slot).
FIN = dict(t=3.2, z0=6.0, palm_z=(10.0, 13.7), pan_gap=0.65)
# Wall root fillets (23-31: "add strengthening features to ALL walls, like small fillets at bottom edge, or ribs, so it can't snap off"):
# a concave fillet of radius FILLET_R along both bottom edges of every free-standing printed wall (HP snap-fit chapter: root radius >= h / 2).
FILLET_R = 2.0
# Cover catches (23-30: "the larger the base, the more holding tabs it needs"): R122-style rule - every face of a cover gets catches, no two
# more than CATCH_MAX apart and none more than CATCH_END from a corner, on the free spans between cable notches, legs and strap arms.
CATCH_MAX = 100.0
POWER_CATCHES = {'-y': (45.125, 90.25, 135.375), '+y': (124.0, 160.0), '-x': (52.0, 124.0), '+x': (20.0, 226.0)}
# -x catches sit between the cover's side ribs (y 34 / 70 / 106 / 142) with their R122 screws 13 toward the middle; the two +x catches get no
# backup screw: at y 20 the screw would land in the rounded corner or the first strap arm's slot, at y 226 on the cover rib at y 214 (listed).
# LOGIC wire-group walls (23-12 orange slots / 23-33 "short walls in the base to help align and separate wire groups"): ribs on the belly-pan
# floor between the harness bundles - between the two micro relay columns and between micro column 1 and the Bus 2 outputs. They start at the
# pan's front wall (joined to it) and run back past the last relay.
LOGIC_GROUP_WALLS = dict(t=2.0, x=None, y1=152.0, z_top=13.3)   # top: over the bundles (packed U top 12.8 - 13.2), 0.5 under the direct relay jumpers (wiring_sim JUMP_Z 15, 14 AWG bottom 13.8)
# Battery relay block (23-06): the AMI out pad grows to the bar width (25.4, MECCANIXITY B0CGJC2S1L 1" x 1/8" stock, the second bar of the LOGIC
# strip pair, spare until now) and gets two snap tabs of its own; 22-59: the FP 40A out stud was an M5 x 16 whose end pushed into the cover
# (top 52.2 vs cover inside 51.5) - M5 x 12 (1.0 past the nut, 3.5 under the cover).
RB_PAD = dict(w=25.4, t=3.2, x0=-6.5, x1=9.0, tab_x=1.0, stock='MECCANIXITY B0CGJC2S1L', bolt_out=12.0)
REV7_STOCK_BARS = 2   # POS bar 226 + battery block bar 36.5 from bar 1; NEG bar 105 from bar 2 (MECCANIXITY B0CGJBRNJX, 305 long)


# ---------- J answers (Dan, 2026-10-14, DECISIONS R94). J1 = A: lugs on one strip are one circuit (the 3 mm rule is between circuits).
# J2 = B: rub protection, guide walls under the decks, crimp-sized terminal holes. J3 = A: one wire per terminal (HL / HR fuse out ->
# splice -> relay 30 + 86; k_horn 86 from sp_hz). J4 = B: a printed channel across the front of the strips, so no wire leaves the LOGIC box
# to come back in.
# Terminal data from the TE product pages, read 2026-10-14 (te.com/en/product-<pn>.html, "Features"): compatible insulation diameter
# range (mm), terminal material thickness t (mm), product length L (mm). None = not on the TE page: T_EST / L_EST are used and marked est.
TERM = {   # L: R163 - from the TE STEP where we have one (42281-1 19.05 -> 20.18, 280755 / 6 29 -> 28.2, 1241388-2 18.45)
    '880398-2': dict(ins=(2.3, 3.5), t=None, L=26.5, head=(5.6, 4.1), what='2.8 receptacle 1-2.5 mm2 (17-13 AWG), typical 33 A'),
    '1241388-2': dict(ins=(1.4, 2.1), t=None, L=18.45, head=(4.4, 4.4), what='MCP 2.8K receptacle 0.5-1 mm2, typical 15 A'),
    '1241390-1': dict(ins=(2.2, 3.0), t=None, L=18.45, head=(3.1, 4.4), what='MCP 2.8K receptacle 1.5-2.5 mm2, unsealed, tin, typical 22 A'),
    # N21 (Dan 2026-10-18): TE AMP MCP 2.8 receptacles, unsealed, pre-tin, locking lance, tab 2.8 x 0.8. Wire / insulation from TE application spec
    # 114-18148 Rev D1 (07 Feb 2023) Table 7 (AWG wires) + product group drawing 1355036: 1-968851-1 16 / 14 AWG (1.3 / 2.0 mm2; DIN 1.0 - 2.5),
    # insulation 2.2 - 3.0; 1-968849-1 20 / 18 AWG (0.5 / 0.8 mm2; DIN 0.5 - 1.0), insulation 1.4 - 2.1 (te.com pages say 1.9 - 3.0 / 1.3 - 2.1: the
    # spec and drawing are tighter and win). L / head from TE's STEPs (c-1-968851-1-e-3d.stp, c-1-968849-1-j3-3d.stp).
    '1-968851-1': dict(ins=(2.2, 3.0), t=None, L=21.2, head=(3.1, 4.4), what='MCP 2.8 receptacle 16 / 14 AWG (1.0 - 2.5 mm2), unsealed, pre-tin, typical 22 A'),
    '1-968849-1': dict(ins=(1.4, 2.1), t=None, L=20.2, head=(3.1, 4.4), what='MCP 2.8 receptacle 20 / 18 AWG (0.5 - 1.0 mm2), unsealed, pre-tin, typical 15 A'),
    '42281-1': dict(ins=(2.79, 4.32), t=0.41, L=20.18, head=(7.49, 3.45), what='FASTON .250 receptacle 18-14 AWG'),
    '2293255-1': dict(ins=(2.3, 3.3), t=0.33, L=None, head=(5.6, 3.0), what='FASTON .187 receptacle 20-15 AWG'),
    '280919-2': dict(ins=(2.31, 3.3), t=0.25, L=16.0, head=(5.6, 2.3), what='FASTIN-FASTON .187 receptacle 20-15 AWG, locking lance'),
    '280755-4': dict(ins=(5.0, 7.0), t=0.51, L=28.18, head=(11.10, 3.80), what='FASTON .375 receptacle 10-7 AWG'),
    '280756-4': dict(ins=(3.4, 5.1), t=0.51, L=28.17, head=(11.10, 3.80), what='FASTON .375 receptacle 12-10 AWG'),
    '62998-2': dict(ins=(5.84, 7.11), t=0.43, L=19.69, head=(7.62, 3.2), what='FASTON .250 receptacle 10-8 AWG'),
}
# R120 (Dan 2026-10-15, M6): head = the receptacle's widest section (W across the tab, H through it, lance included), max of tolerance,
# from the TE customer drawings (te.com DocumentDelivery "Customer Drawing", read 2026-10-15): 880398 box 5.4+-0.2 x 3.9+-0.2 (the two
# retention lances spread 8.21 and fold in as it goes through); 1241437 (MCP 2.8K group drawing that 1241388 refers to) 4.2+-0.2 x 4.4;
# 42281 rev AN section A-A 7.49, side 4.70 max incl. lance; 2293255 rev A3 section Q-Q 5.6; 280755 / 280756 section A-A 11.10, side
# 3.80 + 1.25+-0.2 lance; 62998 rev G section A-A 7.62. HEAD_EST: H not dimensioned on the drawing, scaled off it (est.).
HEAD_EST = {'2293255-1', '62998-2', '42281-1', '280919-2'}
# R121 (2026-10-15): head = the RIGID contact box, the locking lance folded flat (it springs in as it goes through): 42281-1 4.70 over the
# lance - 1.25 lance (est: the 280755 / 280756 lance height on their TE pages) = 3.45 est; 280755 / 280756 3.80 (the 1.25 lance is LOCK).
T_EST, L_EST = 0.40, 20.0        # est: metal thickness / length where the TE page gives none
HOLE = dict(clr=CLR, min_wall=2.0, lead_in=2.0, top_gap=1.0)
# Fit audit 2026-10-18 (Dispatch rule 3, "each blade lands in its terminal's contact zone"): the receptacle's contact end sits SEAT_GAP under the
# deck top. With top_gap 1.0 the TE micro relay's 4.8 blades (11.17 long below the relay's feet, TE STEPs 4-1904124-2/-3, 5-1393292-8,
# 6-1419137-4; data sheet 11.2 +-0.3) went 10.17 into the 280919-2 receptacle, whose contact box is 8.25 long before its wire barrel (TE STEP
# c-280919-2-m-3d.stp) - the tip ran into the crimp. Every receptacle of a micro relay now sits 3.2 down (one seat plane, so no PA12 sliver is left
# between a shallow and a deep cavity): the blades go 7.97 into 280919-2 (box 8.25) and 42281-1 (box 10.25). Every other pairing lands inside its
# box at 1.0 (fit_audit.json). Worst-case blade tolerance against TE's application specs: UNVERIFIED (114-series specs on Dan's download list).
SEAT_GAP = {'micro': 3.2}       # by cavity kind prefix


def seat_gap(part, kind=''):
    return SEAT_GAP.get(kind.split(' ')[0], HOLE['top_gap'])   # terminal hole (R120): slot = terminal envelope + 0.4 per side; walls >= 2.0
                                                                # (R73) or the two holes join into one slot (Dan); >= 2 mm deep at the mouth;
                                                                # receptacle top 1 below the deck top
# Default terminal of a cavity with no harness wire yet (a spare): the largest wire it takes, so a later wire still fits.
TERM_DEFAULT = {'fuse in': ('1-968851-1', 14), 'fuse out': ('1-968851-1', 14), 'acps in': ('1-968851-1', 14), 'acps out': ('1-968851-1', 14),
                'micro 30': ('42281-1', 14), 'micro 87': ('42281-1', 14), 'micro 87a': ('280919-2', 18), 'micro 85': ('280919-2', 18),
                'micro 86': ('280919-2', 18), 'F7 30': ('280755-4', 8), 'F7 87': ('280755-4', 8), 'F7 87a': ('42281-1', 14),
                'F7 85': ('42281-1', 18), 'F7 86': ('42281-1', 18)}
FLOAT_BACKING = 0.5   # R101: a hanging feature with less of its top face on solid material than this is floating (Dan's marks: 5-15 %; the rest >= 76 %)
GUIDE = dict(t=2.0, h=3.5, reach=12.0)     # J2: short guide walls under the deck between neighbouring holes (centres closer than reach)


# R120 / OPEN-ITEMS row 121 (Dan M6 = A, 2026-10-15): insulation build-up sleeve under the insulation crimp of a thin-wall wire below its
# terminal's insulation range.
# TE Raychem RNF-100 2:1 polyolefin (TE / distributor data sheets, read 2026-10-15): expanded ID min, recovered ID max, recovered wall nom.
SLEEVE = {'RNF-100-3/32': (2.4, 1.2, 0.50), 'RNF-100-1/8': (3.2, 1.6, 0.50), 'RNF-100-1/4': (6.4, 3.2, 0.65)}


def sleeved_od(wire_od, size):
    """OD of one sleeve shrunk onto a wire (est.: the wall keeps its cross-section area when it stops short of full recovery)."""
    _, rid, w = SLEEVE[size]
    return math.sqrt(wire_od ** 2 + (rid + 2 * w) ** 2 - rid ** 2)


def build_up(part, wire_od):
    """Fewest RNF-100 layers that bring wire_od into the terminal's insulation range: ([sizes], OD), or (None, wire_od).
    A layer must slide on (expanded ID >= OD) and grip (recovered ID <= OD)."""
    lo, hi = TERM[part]['ins']
    for seq in [[s] for s in SLEEVE] + [['RNF-100-3/32', 'RNF-100-1/8']]:
        d = wire_od
        for s in seq:
            if not SLEEVE[s][1] <= d <= SLEEVE[s][0]:
                break
            d = sleeved_od(d, s)
        else:
            if lo <= d <= hi:
                return seq, d
    return None, wire_od


def crimp_od(part, wire_od):
    """OD the insulation barrel closes on (R120 / M6 = A): the wire, or the wire with its RNF-100 build-up when it is below the range."""
    seq, d = build_up(part, wire_od) if wire_od < TERM[part]['ins'][0] else (None, wire_od)
    return d


def barrel_od(part, wire_od):
    """Crimped barrel envelope (mm): the insulation barrel closes on the (sleeved) wire insulation, never below the smallest insulation
    it is made for, plus the metal on both sides."""
    t_ = TERM[part]
    return max(crimp_od(part, wire_od), t_['ins'][0]) + 2 * (t_['t'] if t_['t'] is not None else T_EST)


# R120 (Dan 2026-10-15: "the holes ... should be made based on the widest part being inserted which would be the contact terminal itself.
# all wire OD would always be smaller in diameter than the contact."): the crimped terminal goes up through its hole from under the deck,
# so the hole is a slot sized from the terminal's widest section - max(head, crimped barrel) each way - + HOLE['clr'] per side, the long
# side along the blade width. The wire (or sleeved wire) only has to be smaller, which it always is. BLADE_AXIS: the box axis the blade
# width (head W) runs along, from the cavity pockets in build_fusion.py (fuse / ACPS blades in the fuse plane; micro 30 / 87 across the
# relay, 85 / 86 / 87a along it; F7 cavities turned 90 deg).
BLADE_AXIS = {'fuse in': 'x', 'fuse out': 'x', 'acps in': 'x', 'acps out': 'x', 'micro 30': 'x', 'micro 87': 'x', 'micro 85': 'y',
              'micro 86': 'y', 'micro 87a': 'y', 'F7 30': 'x', 'F7 87': 'y', 'F7 87a': 'y', 'F7 85': 'x', 'F7 86': 'x'}   # F7 30 turned 90 deg to 87 (fit audit 2026-10-18)


# R120 as Dan confirmed it (2026-10-15): "Hole size = the largest cross-section, seen along the wire's insertion axis, of everything that
# passes through: the terminal's contact box, its crimped wire + insulation barrels, and the wire behind them - plus 0.4 mm per side (CLR).
# For the wire, use the THICKEST insulation that terminal accepts (top of its insulation range ...), not today's thin-wall wire, so GXL or
# thicker wire always fits. If the terminal's own outline is larger than any wire it accepts, the terminal sets the size. Holes need not be
# round - use the combined outline."
# R121 (Dan 2026-10-15: "for install, terminals have to be self locking"): the terminal goes up from under the deck, contact box first, and
# snaps in. LOCK, per terminal, from its TE customer drawing / product page (read 2026-10-15), measured from the contact end (the seat):
#   neck     contact end to the top of the insulation barrel (or the 880398-2 stop flange): the big parts of the terminal (insulation
#            barrel on the thickest insulation, flange) never get higher than this when it is seated, so above it only the contact box and
#            the small wire barrel pass and the cavity steps in to the box - that box-sized stretch is the lance's ledge (R120 still holds:
#            each height is sized by everything that passes it). neck = TE length - insulation barrel length (est where scaled)
#   tip      contact end to the lance tip; out = how far the lance springs out past the box (each side on its axis); 'W' = across the blade
#            width (880398-2: two side lances), 'H' = through it (FASTON / MCP: one lance, the window is cut both sides so the terminal
#            goes in either way round)
#   shoulder 880398-2 only: lance tip to its stop flange (3.8, dimensioned) - the printed shoulder between them; flange = flange width
#   kind 'dimple': no lance (TE "Mating Retention Type: Dimple") - not used in the boxes (R123 swaps it, TERM_SWAP);
#   kind 'clip': no lance terminal exists for that blade + wire - held by the R123 retainer clip (RETAIN)
# Sources: 880398 (lance spread 8.21+-0.38 on a 5.4 box, 5.9 to the lance root, 3.8 tip to flange; tip 9.7 and flange 8.6 scaled, est);
# 1241437 MCP 2.8K (contact zone 6.3, box 6.3 + 4.2; the steel overspring lance: tip / out est, check on the on-hand sample); 42281 rev AN
# (19.05 long, 7.37 max contact end to lance tip; lance 1.25 est; insulation barrel ~4 scaled); 280755 / 280756 (TE page "Locking Lance
# Height 1.25 mm", 10.65 to the tip, 29 long, insulation barrel ~5.5 scaled); 2293255 rev A3 (15 long), 62998 rev G (19.69 long). Release: press the lance flat from the top through the blade
# slot (MCP: TE extraction tool 5-1579008-7, AMP MCP 2.8 contact-to-wire; the others: TE tool per terminal TBD at the sample check).
LOCK = {
    '880398-2': dict(kind='lance', axis='W', out=1.6, tip=9.7, shoulder=3.8, flange=8.6, neck=13.5, est=True),
    '1241388-2': dict(kind='lance', axis='H', out=0.8, tip=6.3, neck=15.0, est=True),
    '1241390-1': dict(kind='lance', axis='W', out=0.54, tip=5.5, neck=16.0, est=False),
    '1-968851-1': dict(kind='lance', axis='W', out=0.47, tip=6.8, neck=18.25, est=False),
    '1-968849-1': dict(kind='lance', axis='W', out=0.47, tip=6.9, neck=18.35, est=False),
    '42281-1': dict(kind='lance', axis='H', out=1.25, tip=7.37, neck=15.0, est=True),
    '280755-4': dict(kind='lance', axis='H', out=1.45, tip=10.65, neck=23.5, est=True),
    '280756-4': dict(kind='lance', axis='H', out=1.45, tip=10.65, neck=23.5, est=True),
    '2293255-1': dict(kind='dimple', neck=11.8, est=True),
    '280919-2': dict(kind='lance', axis='H', out=1.2, tip=5.0, neck=12.5, est=True),
    '62998-2': dict(kind='clip', neck=15.3, est=True),     # R123 B: no lance terminal exists for 8 AWG on a 6.3 blade - retainer clip
}


def barrel_max(part):
    """Crimped insulation barrel on the THICKEST insulation the terminal accepts (R120): top of its range + the metal both sides."""
    t_ = TERM[part]
    return t_['ins'][1] + 2 * (t_['t'] if t_['t'] is not None else T_EST)


def _xy(w, h, kind):
    return (w, h) if BLADE_AXIS[kind] == 'x' else (h, w)


def hole(part, kind):
    """(size x, size y) of the hole (R120): the combined outline of the box, the barrels on the thickest insulation and (880398-2) the
    stop flange, + clr per side, the long side along BLADE_AXIS[kind]. Never from today's wire: that only has to be smaller."""
    if part in REAL:             # the real terminal: the size of the hole zone (it may sit off the blade line - zones() places it)
        z_ = real_zones(part, kind)[0]
        return (z_[3] - z_[2], z_[5] - z_[4])
    (w, h), b, c = TERM[part]['head'], barrel_max(part), 2 * HOLE['clr']
    w = max(w, b, LOCK[part].get('flange', 0.0))
    return _xy(w + c, max(h, b) + c, kind)


def lance_side(c, cavities):
    """+1 / -1: the side of the H axis the lance window opens to - the side with the most room to the neighbouring cavities (their
    R120 hole / box outlines within NEAR mm in the same box; an 87a with no harness wire is a plain blade slot and does not count).
    c / cavities: dicts with box, x, y, kind (+ part, source when known)."""
    part = c.get('part')
    if part not in LOCK or LOCK[part]['kind'] != 'lance' or LOCK[part]['axis'] != 'H':
        return 1
    nb = [d for d in cavities if d is not c and d['box'] == c['box'] and 0 < math.hypot(d['x'] - c['x'], d['y'] - c['y']) < NEAR
          and d.get('part') in TERM and not (d['kind'].endswith('87a') and d.get('source') != 'harness')]
    best, side = None, 1
    for sd in (1, -1):
        w = zones(part, c['kind'], sd)[-1]
        r = (c['x'] + w[2], c['x'] + w[3], c['y'] + w[4], c['y'] + w[5])
        room = 1e9
        for d in nb:
            hx, hy = hole(d['part'], d['kind'])
            (bw, bh), cl = TERM[d['part']]['head'], 2 * HOLE['clr']
            bx, by = _xy(bw + cl, bh + cl, d['kind'])
            for (sx, sy) in ((bx, by),) if LOCK[d['part']]['neck'] > LOCK[part]['neck'] else ((bx, by), (hx, hy)):
                q = (d['x'] - sx / 2, d['x'] + sx / 2, d['y'] - sy / 2, d['y'] + sy / 2)
                gx, gy = max(r[0] - q[1], q[0] - r[1]), max(r[2] - q[3], q[2] - r[3])
                room = min(room, math.hypot(gx, gy) if gx > 0 and gy > 0 else max(gx, gy))
        if best is None or room > best + 1e-6:
            best, side = room, sd
    return side


NEAR = 15.0


def zones(part, kind, side=1):
    """The cavity from the mouth up to the seat, as [(dz_lo, dz_hi, x0, x1, y0, y1)]: dz from the seat (the contact end), bottom up, dz_lo
    None = from the mouth; x / y offsets from the cavity centre. R120 hole below the neck; above it the box (+ clr) - the lance's ledge -
    and the R121 lance window from the tip up to the seat: both sides of the blade width for a 'W' lance (880398-2), the `side` of the H
    axis for an 'H' lance (lance_side: the side with the most room, the terminal goes in lance that way). The deck's blade slot above the
    seat, narrower than the box, is the stop the other way."""
    if part in REAL:
        return real_zones(part, kind, side)
    L_, (w, h), c = LOCK[part], TERM[part]['head'], 2 * HOLE['clr']

    def r(a, b, ea=0.0, eb=0.0):        # a x b (W x H frame) with the H side extended by ea (-) / eb (+), into box x / y
        if BLADE_AXIS[kind] == 'x':
            return (-a / 2, a / 2, -b / 2 - ea, b / 2 + eb)
        return (-b / 2 - ea, b / 2 + eb, -a / 2, a / 2)
    hx, hy = hole(part, kind)
    out = [(None, -L_['neck'], -hx / 2, hx / 2, -hy / 2, hy / 2)]
    box = r(w + c, h + c)
    if L_['kind'] != 'lance':
        return out + [(-L_['neck'], 0.0) + box]
    o = L_['out']
    if L_['axis'] == 'W':
        win = r(w + c + 2 * o, h + c)
    else:
        win = r(w + c, h + c, o if side < 0 else 0.0, o if side > 0 else 0.0)
    return out + [(-L_['neck'], -L_['tip']) + box, (-L_['tip'], 0.0) + win]


def outline(part, kind, side=1):
    """(x0, x1, y0, y1) that bounds every zone - for the collar round the cavity."""
    zs = zones(part, kind, side)
    return min(z[2] for z in zs), max(z[3] for z in zs), min(z[4] for z in zs), max(z[5] for z in zs)


# R122 (Dan 2026-10-15: "add one small screw hole on each lid and base tab for extra support if needed"): beside every cover catch (all
# three boxes) ONE optional M3 screw backs up the snap - an M3 brass heat-set insert (McMaster 94459A140: 5.7 installed, hole 4.0, 6.5 min
# material; R73: threads in metal, never printed) pressed into a boss behind the base skirt, and an M3 x 10 cap screw through a clearance
# hole in the cover wall + bumper band. The boss hangs from the deck plate (LOGIC / POWER) or stands on the floor (battery block), so it is
# never floating (R101); walls round the insert >= 2.0 (R73). It sits `off` along the wall from the catch centre, clear of the tongue and
# its two slots (half width 6 + 1.2 + the head), at the catch height. The belly-pan catches are tongues in the pan wall with no tab, so
# they get no screw (Dan: "if they have tabs").
def SCREW_SKIP_RB(L, D):
    """Battery block cover catches with no backup screw: the rear one at 0.75 L - the HCR150 flange (x 76.5-176.5, from z 10) covers the
    rear rim there and the cover skirt ends at z 6.5, so no insert boss fits (3 screws on that box)."""
    return [(L * 0.75, D)]


SCREW = dict(off=13.0, d_ins=4.0, ins_depth=6.0, boss_w=8.6, boss_depth=5.0, boss_h=8.0, d_clear=3.4, head_d=5.5, z_from_top=9.5)
# ins_depth: insert hole from the skirt's outer face (5.7 insert + 0.3); skirt 3.0 + boss 5.0 = 8.0, so 2.0 of wall stays behind it (R73)


# R123 (Dan 2026-10-15, M8: "A. individually use B if a doesn't work. they do not have to be TE contacts"): every box terminal self-locks.
# (A) a terminal with no lance is swapped, box side, for one with a locking lance on the same tab and wire range: TERM_SWAP maps the part the
# harness drawing names to the one the box is built and bought with (the .harness files change later - Dan's review; follow-up list).
# 2293255-1 (dimple) -> TE 280919-2 (FASTIN-FASTON .187, 4.75 x 0.81 tab, 20-15 AWG, ins 2.31-3.3, lance 1.2, 16 long; TE page + drawing
# 280919 rev M2: box 5.6 wide, 6.4 long, 3.5 over the lance, lance tip 5 from the contact end; box height and neck est.).
# (B) where no lance terminal exists - 62998-2 (8 AWG on the heater relay's 6.3 blades: TE FASTON / FASTIN-FASTON and Aptiv Metri-Pack 630
# stop at 10 AWG with a lance) - and where a cavity cannot keep a ledge (the heater relay 87a, in the middle of its pin pattern): a printed
# RETAINER clip under that relay. It is threaded onto the relay's wires before they are crimped, then pushed up under the deck after the
# terminals are in; two barbed legs snap into pockets in the cavity collar; its plate stops every terminal on that relay from backing out.
# Wire holes = the wire there + clr per side (smaller than the crimped insulation barrel it stops; a thicker-wire harness reprints the clip).
TERM_SWAP = {'2293255-1': '280919-2', '880398-2': '1-968851-1', '1241388-2': '1-968849-1'}
# N21 (Dan 2026-10-18, "MCP 2.8 female receptacles"; DECISIONS R166): every mini fuse / ACPS socket takes a TE AMP MCP 2.8 receptacle by wire
# gauge - 1-968849-1 for 20 / 18 AWG, 1-968851-1 for 16 / 14 AWG (the 15 A circuits stay 16 AWG). Box-side swap like R123: ST185-CabinPower and
# ST185.harnesslib still name 880398-2 / 1241388-2 (OPEN-ITEMS follow-up). Dan's lead was Ballenger Motorsports CONN-100329 ("1.25 - 2.5 mm2"):
# Ballenger names no TE part number; 1-968851-1 is the TE part with that tab, plating and the 16 / 14 AWG crimp data (114-18148 Table 7).
PLACE_HOLD = {}
RETAIN = {'POWER': ['R1']}      # relay positions whose terminals are held by a retainer clip (the heater relay k_htr)
RETAINER = dict(t=2.0, play=0.2, leg=(2.5, 4.0), leg_h=6.0, barb=0.6, barb_h=1.5, clr=CLR, boss=2.0, bear=0.3,
                leg_shift={'R1': (0.0, 10.5)})   # along the short side, per leg: R1's +x leg clears the heater feed-cable bend saddle (y 38.4-47.6)
# t plate (R73 wall), play under the lowest terminal end, leg cross-section / height into its collar pocket, barb out / height at the leg
# top (snaps over the pocket's undercut), boss = collar wall round each leg pocket, bear = least the crimped insulation barrel rests on
# the plate each side. On a retained end the RNF-100 build-up is cut to the insulation barrel length, so only the bare wire goes through.


def retainer_hole(part, wire_od):
    """(hole d, crimped barrel d) at a retainer clip: the bare wire + clr per side, and the insulation barrel it stops."""
    return wire_od + 2 * RETAINER['clr'], barrel_od(part, wire_od)


# J4 = B: LOGIC front channel. Fuse-side wires come forward along x 7.4 (between the belly pan wall and the Bus 1 output risers), turn
# along the front in front of the spine (y 7.25), each on its own level, over a printed floor (the Bus 1 feed lug is under it); the
# HL / HR splices lie stacked in the channel past the spine; every branch then runs to its relay on its own level. Levels: centre z.
CHANNEL = dict(x_fwd=7.4, y=7.25, y_sp=8.5, floor=(16.95, 18.95), floor_x=(8.5, 44.0 + PEM_GROW + 3 * FUSE_GROW), floor_y=(6.45, 10.6), wide_y=20.5, wide_x0=27.05 + PEM_GROW / 2 + FUSE_GROW,
               splice=dict(x0=27.5 + PEM_GROW / 2 + FUSE_GROW, x1=40.0 + PEM_GROW / 2 + FUSE_GROW, od=4.5, L=12.5),   # est: solder splice + adhesive heat shrink over 14 + 14 + 16 AWG (L1; combined 10 AWG)
               z=dict(ETB=20.18, HR=24.16, HL=28.86, HR30=23.1, HR86=25.45, HL30=27.8, HL86=29.95),
               x_etb=44.0 + PEM_GROW + 3 * FUSE_GROW, x_hr=62.8 + PEM_GROW + 3 * FUSE_GROW)    # x_hr between the micro relay columns (R123: + 2.0 with them)
CHANNEL_SPLICES = ('sp_hl', 'sp_hr')
# J2 = B rub protection. LOGIC: a rib on the belly pan between the Bus 1 output wires (kept at x <= lane_x_max) and the Bus 1 strip bolt
# heads (x 14.67 up) - PAN_RIB; a relief (the pan wall thinned) at the outboard micro relay column, where the 86 wires drop 1 mm from the wall
# and ease forward (the relief runs 11 mm ahead of each relay centre, 5 behind).
PAN_RIB = dict(x=(12.0, 14.0), y=(23.5, 125.0), z_top=15.5)   # starts behind the Bus 1 feed bolt head (y 13.4 - 22.6 at z 13)
LANE_X = {('LOGIC', round(13.5 - MINI_BLADE_X, 2)): (6.9, 11.5)}   # Bus 1 output lane: wire edges between the pan's rounded front corner and the rib
PAN_RELIEF = dict(depth=0.5, fwd=11.0, back=5.0)   # inner face cut back 0.5 (wall 2.5 -> 2.0, the R73 minimum): the base legs sit right outside it at y 21 / 141
PAN_SNAPS_X = (63.0, 123.0)       # LOGIC belly pan catches on the end walls, clear of the reliefs (rev 7: 0.3 / 0.7 of the depth)
CHANNEL_CAD_SKIP = {'HL', 'HR', 'ETB', 'HEAD LH 30', 'HEAD LH 86', 'HEAD RH 30', 'HEAD RH 86', 'k_etb 30'}   # CAD tails that are channel wires now


# ---------- vendor CAD models (Dan 2026-10-18, DECISIONS R163: "you should use actual official cad models from manufacturer websites or other
# community shared sites when possible"). The files live in the main checkout's cad/vendor/<maker>/<pn>/ (gitignored, R67); cad/vendor/INDEX.md
# (committed) lists PN, source URL and file. TE customer view models (te.com "3D STEP" link on each product page, read 2026-10-18): frame =
# contact (mating) end at Z 0, the wire running down -Z, blade width along X, the locking lance on the -Y side; y_box = the contact box's Y centre
# (measured on the STEP over its top 4 mm) - the blade line, put on the cavity centre.
VENDOR_DIR_MAIN = r'C:\projects\active\st185-link-ecu-config\cad\vendor'
TE_DOC = 'https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=%s&DocType=Customer%%20View%%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=%s'
VENDOR_TERM = {   # pn: (maker dir, file, y_box, TE DocNm)
    '880398-2': ('te', 'c-880398-2-t-3d.stp', 2.24, 'CVM_880398-2'),
    '1241388-2': ('te', 'c-1241388-2-c6-3d.stp', 2.20, '1241388-2'),
    '1241390-1': ('te', 'c-1241390-1-c6-3d.stp', 2.20, '1241390-1'),
    '1-968851-1': ('te', 'c-1-968851-1-e-3d.stp', 2.20, 'CVM_1-968851-1'),
    '1-968849-1': ('te', 'c-1-968849-1-j3-3d.stp', 2.20, '1-968849-1'),
    '42281-1': ('te', 'c-42281-1-dj-3d.stp', 1.65, 'CVM_42281-1'),
    '280919-2': ('te', 'c-280919-2-m-3d.stp', 0.85, 'CVM_280919-2'),
    '280755-4': ('te', 'c-280755-4-l-3d.stp', 1.99, 'CVM_280755-4'),
    '280756-4': ('te', 'c-280756-4-p-3d.stp', 1.99, 'CVM_280756-4'),
    '62998-2': ('te', 'c-62998-2-w-3d.stp', 1.43, 'CVM_62998-2'),
}


# R163 (card item 13, 2026-10-18): the terminal cavities are sized from the REAL terminal - TE's own STEP (spec.VENDOR_TERM) - not from
# estimates. Measured on each model (sections every 0.5 mm, model frame: contact end Z 0, wire down -Z, blade width X, lance on -Y, box floor
# Y 0): box W x H (Y 0..H, the blade line at H / 2), lock (W = side lances +-X / H = one lance on -Y: spring-out past the box, tip depth =
# the deepest section the lance reaches, + 0.1 - checked by interference in the assembly), neck
# (contact end to the insulation barrel = where the big hole starts, R120), L. The models show the barrels OPEN (uncrimped wings); crimped
# (R120: the thickest wire / insulation the terminal accepts): wire barrel Y 0 .. d_max + 2 t, insulation barrel Y y_ins .. y_ins + ins_max + 2 t,
# width = TE application spec crimp width where TE gives one (114-20021 .375 series: wire 4.06 - 4.57, insulation 6.35), else the same as the
# height. d_max = the stranded conductor diameter at the top of the TE wire range (est: not on the TE pages); t = the metal (TE page, else
# T_EST). Cross-check 280756-4: 2.95 + 2 x 0.51 = 3.97 high vs TE 114-20021's 3.20 for 6 mm2 - conservative.
REAL = {   # pn: box (W, H), lock (axis, out, tip) or None, neck, L, wire barrel z (from, to), insulation barrel (z from, y_lo), d_max, spec widths
    '1241388-2': dict(box=(3.10, 4.40), lock=('W', 0.54, 6.4), neck=16.0, L=18.45, wz=(9.75, 15.75), iz=(16.25, 0.75), d=1.30, ww=None, iw=None, lclr=0.2),
    '1241390-1': dict(box=(3.10, 4.40), lock=('W', 0.54, 6.4), neck=16.0, L=18.45, wz=(9.75, 15.75), iz=(16.25, 0.55), d=2.00, ww=None, iw=None, lclr=0.2),
    # N21: measured on TE's STEPs (sections every 0.5), from the spring tips (the seat; they stand 0.6 / 0.7 above the model's Z 0): box 3.10 x 4.40,
    # side lances to +-2.02 (0.47 out) down to 6.8 / 6.9; wire barrel 13.2 / 13.8 (its earliest section) - 17.0 / 17.1, insulation barrel from 18.5 / 18.6 (y from 0.6 / 0.7).
    # Lance ledge clearance 0.15 (0.47 - 0.15 = 0.32 >= LOCK_MIN 0.3).
    '1-968851-1': dict(box=(3.10, 4.40), lock=('W', 0.47, 6.8), neck=18.25, L=21.2, wz=(13.2, 17.0), iz=(18.5, 0.6), d=2.00, ww=None, iw=None, lclr=0.15),
    '1-968849-1': dict(box=(3.10, 4.40), lock=('W', 0.47, 6.9), neck=18.35, L=20.2, wz=(13.8, 17.1), iz=(18.6, 0.7), d=1.30, ww=None, iw=None, lclr=0.15),
    '42281-1': dict(box=(7.44, 3.30), lock=('H', 1.04, 7.1), neck=16.0, L=20.18, wz=(10.25, 15.75), iz=(16.25, -0.38), d=1.85, ww=None, iw=None),
    '280919-2': dict(box=(5.60, 2.40), lock=('H', 1.00, 5.1), neck=12.5, L=16.0, wz=(8.25, 12.25), iz=(12.5, -0.40), d=1.60, ww=None, iw=None),
    '280755-4': dict(box=(11.13, 3.97), lock=('H', 1.26, 10.8), neck=24.5, L=28.18, wz=(16.5, 22.5), iz=(24.5, -0.64), d=4.10, ww=4.57, iw=6.35),
    '280756-4': dict(box=(11.13, 3.97), lock=('H', 1.26, 10.8), neck=24.5, L=28.17, wz=(16.5, 22.5), iz=(24.5, -0.64), d=2.95, ww=4.06, iw=6.35),
    '62998-2': dict(box=(7.54, 2.85), lock=None, neck=16.0, L=19.68, wz=(10.5, 14.5), iz=(16.25, -0.51), d=3.70, ww=None, iw=None),
}


# lclr: clearance at the lance's ledge (the box-sized stretch under the window). TE's MCP 2.8K lances spring only 0.54 past the box, so with the
# R120 0.4 the catch would be 0.14 - under check_terminal_holes LOCK_MIN 0.3; 0.2 there gives 0.34 (the rest of the cavity keeps 0.4).
LEDGE_CLR = {pn: v['lclr'] for pn, v in REAL.items() if 'lclr' in v}
for _pn, _r in REAL.items():          # the lock data the gates read = the real terminal's
    if _r['lock']:
        LOCK[_pn].update(axis=_r['lock'][0], out=_r['lock'][1], tip=_r['lock'][2], neck=_r['neck'], est=False)
        LOCK[_pn].pop('shoulder', None)
    else:
        LOCK[_pn].update(neck=_r['neck'], est=False)


def real_env(pn):
    """Crimped envelope of the real terminal in the model frame: dict(box, wire, ins) of (half width, y_lo, y_hi) + the blade line yb."""
    R_, T_ = REAL[pn], TERM[pn]
    t = T_['t'] if T_['t'] is not None else T_EST
    W_, H_ = R_['box']
    hw = H_ if False else None
    wh = R_['d'] + 2 * t                                    # crimped wire barrel height (from the floor, Y 0)
    ih = T_['ins'][1] + 2 * t                               # crimped insulation barrel height (from its floor)
    y_i = R_['iz'][1]
    return dict(yb=H_ / 2, box=(W_ / 2, 0.0, H_), wire=(max(R_['ww'] or 0.0, wh) / 2, 0.0, wh),
                ins=(max(R_['iw'] or 0.0, ih) / 2, y_i, y_i + ih))


def real_zones(part, kind, side=1):
    """zones() from the real terminal (R120 / R121 as before, real numbers): from the mouth to the neck everything that passes (box, crimped
    barrels, the wire behind), the neck to the lance tip the box and the crimped wire barrel (the lance folds flat as it passes, so its ledge
    stays), the tip to the seat the box + the sprung lance (W: both sides of the blade width; H: the -Y side). Coordinates relative to the cavity
    centre = the blade line; model +Y -> box H axis * -side (the placement in build_fusion.place_terminals uses the same mapping)."""
    E, R_, c = real_env(part), REAL[part], HOLE['clr']
    yb = E['yb']

    def to_box(u0, u1, v0, v1):          # (W range, model-Y range rel. to the blade line) -> (x0, x1, y0, y1)
        h0, h1 = sorted((-side * v0, -side * v1))
        if BLADE_AXIS[kind] == 'x':
            return (u0, u1, h0, h1)
        return (h0, h1, u0, u1)
    bw, bl, bh = E['box']
    ww, wl, wh = E['wire']
    iw, il, ih = E['ins']
    u_all = max(bw, ww, iw) + c
    hole = to_box(-u_all, u_all, min(bl, wl, il) - yb - c, max(bh, wh, ih) - yb + c)
    cl = R_.get('lclr', c)
    ax = R_['lock'][0] if R_['lock'] else None
    u_bx = max(bw + (cl if ax == 'W' else c), ww + c)
    box_ = to_box(-u_bx, u_bx, bl - yb - (cl if ax == 'H' else c), max(bh, wh) - yb + c)
    out = [(None, -R_['neck']) + hole]
    if R_['lock'] is None:
        return out + [(-R_['neck'], 0.0) + box_]
    ax, o, tip = R_['lock']
    if ax == 'W':
        u_w = max(bw + o + c, ww + c)
        win = to_box(-u_w, u_w, bl - yb - c, max(bh, wh) - yb + c)
    else:
        win = to_box(-u_bx, u_bx, bl - yb - c - o, max(bh, wh) - yb + c)
    return out + [(-R_['neck'], -tip) + box_, (-tip, 0.0) + win]

