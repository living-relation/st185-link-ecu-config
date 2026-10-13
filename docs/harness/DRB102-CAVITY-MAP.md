# DRB102 bulkhead - physical cavity map

The one firewall bulkhead is a Deutsch DRB 102-way: `DRB12-102PAE-L018` receptacle (cabin,
pin contacts) + `DRB16-102SAE-L018` plug (engine, socket contacts) + `DRBF-1A` flange. It is ONE
102-position connector (Daniel, 2026-10-12, DECISIONS S10). Every drawing that uses it shows
the whole connector - all 102 cavities with TE's numbers: the receptacle `bh_a_fw` on
`ST185-A-cabin` and `bh_b_fw` on `ST185-B-cabin`, the plug `bh_a_eng` on `ST185-A-engine` and
`bh_b_eng` on `ST185-B-engine`. "A" and "B" are only our names for its two sections, set by
ECU connector letter (Rule 3); each drawing wires its own section and marks the other
section's cavities N/C ("see ST185-<other>"). This file says which section owns each cavity.

Resolved 2026-10-11 (Claude Code) from TE's own customer drawing, closing `OPEN-ITEMS` row 42.
Nothing here is provisional.

## Source

TE customer drawing **DRB12-102PXE-L018, rev C3** (19 Apr 2024), sheet 1, insert face view.
It is the drawing TE's `DRB12-102PAE-L018` part page links (`ENG_CD_DRB12-102PXE-L018_C3.pdf`).
Its own callouts: 80× size 16, 16× size 12, 4× size 8, 2× size 4 - the same counts as the TE
DRB catalog's 102-way insert arrangement. Secondary locks are `WB-51P*R` / `WB-51P*L` (one per
51-cavity half). Contact wire ranges from the same sheet: size 16 = 14-20 AWG, size 12 = 12-14
AWG, size 8 = 8-10 AWG, size 4 = 6 AWG.

## Layout (face as drawn by TE)

Twelve columns, left to right as TE draws the face. Each column reads top to bottom.

| Column | Cavities, top to bottom | Sizes |
|---|---|---|
| 1 | 102 - 95 | 12 |
| 2 | 94 - 83 | 16 |
| 3 | 82 - 71 | 16 |
| 4 | 70 - 67, gap, 66 - 63 | 16 |
| 5 | 62, 61, **60**, 59, 58 | 60 = size 4, rest 16 |
| 6 | 57, 56, **55, 54**, 53, 52 | 55, 54 = size 8, rest 16 |
| 7 | 51, 50, **49, 48**, 47, 46 | 49, 48 = size 8, rest 16 |
| 8 | 45, 44, **43**, 42, 41 | 43 = size 4, rest 16 |
| 9 | 40 - 37, gap, 36 - 33 | 16 |
| 10 | 32 - 21 | 16 |
| 11 | 20 - 9 | 16 |
| 12 | 8 - 1 | 12 |

Columns 1-6 (52-102) are the left wedgelock half, 7-12 (1-51) the right.

| Size | Cavities |
|---|---|
| 12 | 1-8, 95-102 |
| 8 | 48, 49, 54, 55 |
| 4 | 43, 60 |
| 16 | every other cavity (80) |

## Allocation rules used

- **A and B are sections of the one connector, not wedgelock halves.** A has 47 size-16 positions drawn and
  one wedgelock half has 40, so A's 37 live circuits and 3 shield drains fill the right
  half's size-16 cavities and A's 7 spares sit in the next column over (52-61). B takes everything else. Rule 3 is about
  which loom and which drawn half a pin is on; the physical shell is one part.
- **Each shielded run sits in one column, signal - return - drain in a row** (crank, cam,
  turbo speed, flex, ETB sensor group on A; knock, ETB motor, gearbox VSS, CAN-Lambda pair on
  B), so the drain is crimped next to the wires it screens.
- **Every shield drain has its own cavity.** The DRB102 has room, so the old plan (§7.3) of
  sharing bulkhead B c1 through a 14 AWG pigtail is no longer needed. Rule B1 (a pin is
  shared only by the same signal) is met trivially: nothing shares.
- **Every one of the 102 cavities is drawn exactly once** across the two halves, each with a
  contact or a sealing plug, so the buy list counts every plug the E-seal needs.
- The six drain cavities (A c6, c10, c11; B c22, c23, c24) were reserved by #81 and are wired
  by the shield redraw (plan §7.3, 2026-10-11).

Gate: `docs/harness/audit_mating.py` rule M8 (designation = real cavity number on both halves,
each cavity used once, contact/plug size matches this map).

## Spare capacity

| Size | A spare | B spare |
|---|---|---|
| 16 | 6 (52, 53, 57, 58, 59, 61) | 12 (63-70, 79-82) |
| 12 | 0 | 12 (3-8, 97-102) |
| 8 | - | 4 (48, 49, 54, 55) |
| 4 | - | 2 (43, 60) |

A cavity 56 (`c27`) carries the EPS relay coil- wire from the MR-S pump B5 since 2026-10-12 (DECISIONS R22).
B cavity 62 (`c25`) carries the back-up switch feed since 2026-10-13 (DECISIONS S17 C4); cavity 76 (`c12`) is the switch output.
The alternator IG/L/S do NOT cross here: DECISIONS R17 / S18 put the alternator plug in `ST185-HeavyDC`;
its three wires pass the firewall in harness C's own RH fender grommet (`ST185-EngineRoom-C`).

## Sealing plugs

Size 16 `114017` (to buy), size 12 `0413-214-1205`, size 8 `114018-ZZ`, size 4 `114019-ZZ`,
all Deutsch; the last three are owned (`docs/sourcing/te-on-hand-bom.csv`). TE lists the size-8 and size-4 plugs by
contact size for HD/HDP/DT; the DRB uses the same solid contact sizes, but TE's DRB page does
not list a plug by number - check one in the physical housing before buying more
(`docs/OPEN-ITEMS.md`).

## Full map

| DRB | Wedgelock | Size | Bulkhead | Cavity id | Use |
|---|---|---|---|---|---|
| 1 | right (1-51) | 12 | A | c48 | Switched 12V - INJECTOR power feed, fuse RFRM INJ 15A (14 AWG) - moved in from retired IX_RAIL_A (DTP 4-way) |
| 2 | right (1-51) | 12 | A | c49 | Switched 12V - COP / ignition coil power feed, fuse RFRM COP 20A (14 AWG) - moved in from retired IX_RAIL_A (DTP 4-way) |
| 3 | right (1-51) | 12 | B | c38 | spare (size 12) |
| 4 | right (1-51) | 12 | B | c39 | spare (size 12) |
| 5 | right (1-51) | 12 | B | c40 | spare (size 12) |
| 6 | right (1-51) | 12 | B | c41 | spare (size 12) |
| 7 | right (1-51) | 12 | B | c42 | spare (size 12) |
| 8 | right (1-51) | 12 | B | c43 | spare (size 12) |
| 9 | right (1-51) | 16 | A | c24 | ECU-A A8 |
| 10 | right (1-51) | 16 | A | c41 | Gnd Out to engine sensors (bulkhead splice sp_gnd_bha, 20 AWG) - crank |
| 11 | right (1-51) | 16 | A | c33 | Crank VR screen |
| 12 | right (1-51) | 16 | A | c4 | +8V Out to cam Hall |
| 13 | right (1-51) | 16 | A | c29 | ECU-A A9 |
| 14 | right (1-51) | 16 | A | c42 | Gnd Out to engine sensors (bulkhead splice sp_gnd_bha, 20 AWG) - cam |
| 15 | right (1-51) | 16 | A | c34 | Cam Hall screen |
| 16 | right (1-51) | 16 | A | c40 | +5V Out to engine sensors (bulkhead splice sp_5v_bha, 20 AWG) - turbo speed |
| 17 | right (1-51) | 16 | A | c7 | ECU-A A30 |
| 18 | right (1-51) | 16 | A | c43 | Gnd Out to engine sensors (bulkhead splice sp_gnd_bha, 20 AWG) - turbo speed |
| 19 | right (1-51) | 16 | A | c6 | Turbo speed screen (to A7) |
| 20 | right (1-51) | 16 | A | c5 | Switched 12V to engine sensors |
| 21 | right (1-51) | 16 | A | c9 | ECU-A A31 |
| 22 | right (1-51) | 16 | A | c10 | Flex fuel screen (to A7) |
| 23 | right (1-51) | 16 | A | c2 | +5V Out to engine sensors (bulkhead splice sp_5v_bha, 20 AWG) - ETB |
| 24 | right (1-51) | 16 | A | c21 | ECU-A A22 |
| 25 | right (1-51) | 16 | A | c22 | ECU-A A33 |
| 26 | right (1-51) | 16 | A | c3 | Gnd Out to engine sensors (bulkhead splice sp_gnd_bha, 20 AWG) - IAT / ETB / ECT branch |
| 27 | right (1-51) | 16 | A | c11 | ETB sensor group screen (to A7) |
| 28 | right (1-51) | 16 | A | c39 | +5V Out to engine sensors (bulkhead splice sp_5v_bha, 20 AWG) - MAP |
| 29 | right (1-51) | 16 | A | c44 | Gnd Out to engine sensors (bulkhead splice sp_gnd_bha, 20 AWG) - flex / MAP branch |
| 30 | right (1-51) | 16 | A | c8 | ECU-A A17 |
| 31 | right (1-51) | 16 | A | c13 | ECU-A A4 |
| 32 | right (1-51) | 16 | A | c14 | ECU-A A3 |
| 33 | right (1-51) | 16 | A | c15 | ECU-A A2 |
| 34 | right (1-51) | 16 | A | c16 | ECU-A A1 |
| 35 | right (1-51) | 16 | A | c17 | ECU-A A13 |
| 36 | right (1-51) | 16 | A | c18 | ECU-A A12 |
| 37 | right (1-51) | 16 | A | c19 | ECU-A A11 |
| 38 | right (1-51) | 16 | A | c20 | ECU-A A10 |
| 39 | right (1-51) | 16 | A | c23 | ECU-A A21 |
| 40 | right (1-51) | 16 | A | c25 | ECU-A A15 |
| 41 | right (1-51) | 16 | A | c26 | ECU-A A16 |
| 42 | right (1-51) | 16 | A | c35 | MRS EPS pump logic enable (fuse box MTA-2 MRS, 7.5A) * |
| 43 | right (1-51) | 4 | B | c52 | spare (size 4) |
| 44 | right (1-51) | 16 | A | c36 | Aux 7 MRS speed-out (ECU A27) |
| 45 | right (1-51) | 16 | A | c37 | A/C coolant switch signal -> A/C amplifier TW (not ECU) |
| 46 | right (1-51) | 16 | A | c38 | A/C coolant switch return -> A/C amplifier |
| 47 | right (1-51) | 16 | A | c45 | +5V Out to B engine sensors via IX_B_RAIL - oil pressure |
| 48 | right (1-51) | 8 | B | c48 | spare (size 8) |
| 49 | right (1-51) | 8 | B | c49 | spare (size 8) |
| 50 | right (1-51) | 16 | A | c46 | +5V Out to B engine sensors via IX_B_RAIL - fuel pressure |
| 51 | right (1-51) | 16 | A | c47 | +5V Out to B engine sensors via IX_B_RAIL - coolant pressure |
| 52 | left (52-102) | 16 | A | c1 | spare (size 16) |
| 53 | left (52-102) | 16 | A | c12 | spare (size 16) |
| 54 | left (52-102) | 8 | B | c50 | spare (size 8) |
| 55 | left (52-102) | 8 | B | c51 | spare (size 8) |
| 56 | left (52-102) | 16 | A | c27 | spare (size 16) |
| 57 | left (52-102) | 16 | A | c28 | spare (size 16) |
| 58 | left (52-102) | 16 | A | c30 | spare (size 16) |
| 59 | left (52-102) | 16 | A | c31 | spare (size 16) |
| 60 | left (52-102) | 4 | B | c53 | spare (size 4) |
| 61 | left (52-102) | 16 | A | c32 | spare (size 16) |
| 62 | left (52-102) | 16 | B | c25 | Back-up switch B1 pin 2 feed <- J/B No.1 GAUGE 15A (J/B3 3B-9 R-L) |
| 63 | left (52-102) | 16 | B | c26 | spare (size 16) |
| 64 | left (52-102) | 16 | B | c27 | spare (size 16) |
| 65 | left (52-102) | 16 | B | c28 | spare (size 16) |
| 66 | left (52-102) | 16 | B | c29 | spare (size 16) |
| 67 | left (52-102) | 16 | B | c30 | spare (size 16) |
| 68 | left (52-102) | 16 | B | c31 | spare (size 16) |
| 69 | left (52-102) | 16 | B | c32 | spare (size 16) |
| 70 | left (52-102) | 16 | B | c33 | spare (size 16) |
| 71 | left (52-102) | 16 | B | c7 | ECU-B B15 |
| 72 | left (52-102) | 16 | B | c8 | ECU-B B16 |
| 73 | left (52-102) | 16 | B | c9 | ECU-B B23 |
| 74 | left (52-102) | 16 | B | c10 | ECU-B B6 |
| 75 | left (52-102) | 16 | B | c11 | ECU-B B7 |
| 76 | left (52-102) | 16 | B | c12 | Back-up switch B1 pin 1 out (+12V in reverse) -> reverse relay k_rev 86 + opto IN2 (CSB3 S8) |
| 77 | left (52-102) | 16 | B | c19 | Gnd Out (ECU B22) to B engine sensors (bulkhead splice sp_gnd_bhb, 20 AWG) - oil temp / charge-pipe IAT / oil / coolant pressure branch |
| 78 | left (52-102) | 16 | B | c21 | Gnd Out (ECU B22) to B engine sensors (bulkhead splice sp_gnd_bhb, 20 AWG) - fuel pressure / VSS branch |
| 79 | left (52-102) | 16 | B | c34 | spare (size 16) |
| 80 | left (52-102) | 16 | B | c35 | spare (size 16) |
| 81 | left (52-102) | 16 | B | c36 | spare (size 16) |
| 82 | left (52-102) | 16 | B | c37 | spare (size 16) |
| 83 | left (52-102) | 16 | B | c16 | Knock 1 SIG+ (ECU B9) |
| 84 | left (52-102) | 16 | B | c17 | Knock 1 SIG- (to Gnd Out B22) |
| 85 | left (52-102) | 16 | B | c18 | Knock 1 screen |
| 86 | left (52-102) | 16 | B | c5 | ETB motor + (Aux 9, B18) |
| 87 | left (52-102) | 16 | B | c6 | ETB motor - (Aux 10, B26) |
| 88 | left (52-102) | 16 | B | c22 | ETB motor screen (to B17) |
| 89 | left (52-102) | 16 | B | c15 | Gearbox VSS signal (ECU B29, DI 8) |
| 90 | left (52-102) | 16 | B | c20 | Switched 12V to gearbox VSS (from sp_sw12) |
| 91 | left (52-102) | 16 | B | c23 | Gearbox VSS screen (to B17) |
| 92 | left (52-102) | 16 | B | c13 | CAN H to Link CAN-Lambda (ST185-CAN) |
| 93 | left (52-102) | 16 | B | c14 | CAN L to Link CAN-Lambda (ST185-CAN) |
| 94 | left (52-102) | 16 | B | c24 | CAN-Lambda CAN pair screen (to B17, via the CAN screen splice) |
| 95 | left (52-102) | 12 | B | c3 | CAN-Lambda +12V, cabin fuse F5 10A (14 AWG) |
| 96 | left (52-102) | 12 | B | c4 | CAN-Lambda ground to cabin chassis ground (14 AWG) |
| 97 | left (52-102) | 12 | B | c1 | spare (size 12) |
| 98 | left (52-102) | 12 | B | c2 | spare (size 12) |
| 99 | left (52-102) | 12 | B | c44 | spare (size 12) |
| 100 | left (52-102) | 12 | B | c45 | spare (size 12) |
| 101 | left (52-102) | 12 | B | c46 | spare (size 12) |
| 102 | left (52-102) | 12 | B | c47 | spare (size 12) |
