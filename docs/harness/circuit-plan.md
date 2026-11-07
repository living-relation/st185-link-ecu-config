# Circuit plan - decided by complete circuit

Dan reviews the rewire by whole circuits, not single wires (2026-10-21). The 21-circuit table was approved with
changes to #2, #9, #11 and #18, then written into `docs/harness/MASTER-wirelist.csv` on 2026-10-25 (row 164). Pins are
1993 EWD; ECU pins are Link G4X XtremeX. This is a plan file, not a wiring source: the master owns every wire, and each
action below names the master wire id that carries it. If this file and the master disagree, the master wins and the
difference goes into `docs/OPEN-ITEMS.md`. Factory keep / gone list: `README.md` "What stays and what goes"; new box
seat to OEM landing: `README.md` "Power injection". Routes change only per DECISIONS B8.

| # | Circuit | Plan (in the master) |
|---|---|---|
| 1 | Engine management (factory ECU, igniter, EFI relays) | Gone. The Link plus the new engine harness replace it. |
| 2 | Starting | OEM starter relay in R/B No.4 stays. Coil + from key START; coil - through the clutch start switch C11. C11 completes the starter circuit in hardware; it is not an ECU input. No `k_str`. Aux 8 is spare. |
| 3 | Charging | IG2-15 B-R keeps a 6 in pigtail: kill switch, then alternator IG. IG2-16 Y stays and drives the 12 V charge LED in the Dash harness (sinks to OEM cluster plug C14 (C) pin 8). Alternator B+ on the heavy-cable harness. |
| 4 | Cruise | The OEM cruise ECU and actuator are gone; the stalk stays as CSB3 buttons. Cruise control clutch switch C17 pin 2 to CSB3 pin 20 (`w_sw5`) is the one ECU clutch input (flat-shift, via VDI6). C11 completes the starter circuit in hardware; it is not an ECU input. |
| 5 | SRS | Gone. |
| 6 | ABS | Gone. The wheel speed sensors get their own mini harnesses to the VRC enclosure. |
| 7 | Gauges + warning lamps | Gone; replaced by the CAN cluster. LEDs take turn, high beam, charge and park brake from the OEM cluster plugs, oil pressure from CSB3 L4 (cavity 26, 0x643 byte 3). OEM dimmer R10 stays for the rest of the dash lighting. Headlight-sense: tap R10 pin 1 green TAIL through EL814 IN3 to centre-cluster GPIO28 (Dan 2026-10-26: no change; encoder not used). |
| 8 | Main power (AM1, AM2, J/B1, dome, hazard, retract) | Trunk battery -> glove-box boxes -> cabin landings. `w_pdb_jb1` is behind the dash to J/B No.1 1I, 6 AWG for our 60 A JB1 fuse (`cad/fusebox/src/spec.py` AMI_AWG). |
| 9 | Blower | R/B No.4 stays with its heater relay, 40 A HEATER and 10 A A/C fuses; one new feed from B1 AMI IN-1. No `k_htr`. |
| 10 | A/C | Both amps stay. D16: A15 pin 8 drives `k_acc` coil 85; coil 86 from B2-BUS2-8; Link Aux 4 is the ACT kill only; pin 2 hard-grounded; Ign 8 is tacho to pin 18 and, through 4.7 kΩ, to pin 9 (lock-sensor workaround, N61 2026-10-21 / Dan 2026-10-26). A/C button and evap wires to the Link removed. Cabin sensor-common splice `SP-AC-SG` stays (replaces E10). A/C pressure switch and its yellow-red wire: DECISIONS, the A/C paragraph above B1. |
| 11 | Reverse + back-up lamps | No K-REV. OEM back-up switch drives the lamps; output tapped through opto IN2. New switch wires splice to the IG2-4 / IG2-13 pigtails. Factory rear lighting stays (no RearLights harness). |
| 12 | Fuel pump | `k_fp` in the trunk, rear-fuel harness (B3-K1). |
| 13 | Front lights + pop-ups | Front run (Route 17 line 10), spliced to the 6 in pigtails. |
| 14 | Horn | Front run, relay in the glove box (B2-M3). |
| 15 | Radiator + condenser fans | Link-controlled relays, front run. |
| 16 | Wiper + washer | Wiper on the driver fender run, washer pump on the front run. |
| 17 | Fog | Removed (Dan 2026-11-02): no fog lamps, relay or wiring. Every fog wire (switch F12, relay R/B No.3, 20 A FR FOG fuse) comes out back to its last live point; the relay and the fuse come out, the R/B No.4 seat stays empty. No spare circuit to the old fog-lamp spots. |
| 18 | Windows, locks, sunroof, seat | R/B No.2 stays; its 30 A POWER fuse is fed by AM1 (B1 AMI OUT-3, `w_pdb_am1`) through cowl splice I2, as stock (Dan B17 b, 1993 p.62 / p.137-142, US = Canada). No `k_pwr`. |
| 19 | Diagnostic plug (DLC1) | Gone. |
| 20 | Alarm hood pin + siren | Front run and driver fender run. |
| 21 | Engine-bay ground studs (EA, EB, EC) | The studs stay as ground points; every ground wire on them is new. |

ETB hold power is all cabin and J/B No.1 stays: Aux 6 (A28) holds K-EFI; DI 9 (B28) senses IG2; the IG2 wake diode feeds A5 from J/B1 1H-7; K-ETB on Aux 2 (A20) feeds B5.

CAN node power: DECISIONS B17, "CAN wiring (B17)" and "Relays (B15)" (Dan 2026-11-04 / 2026-11-07: each node's own fused feed and ground join the CAN trunk start at ECU plug C and ride its 4-core branch cable; wires in the master; factory feed path and the stereo reservation: README "Power injection").

Fuse box: parked. Seat-to-circuit assignment is `sot/fuse-relay-map.csv` (B1 POWER, B2 LOGIC, B3 trunk block, B4 EPS).

## Cut-list groups (row 164)

| Group | Joint | Status |
|---|---|---|
| 1 | EB1 Engine <-> Cowl (rear of RH fender) | Decided 2026-10-20 / 2026-10-26: dead. If the ignition-switch black-orange wire is at the engine plug (EB1-1), remove it. J/B No.1 fed from POWER JB1 60 A, 6 AWG for our 60 A load, spliced to a 6 in stub of the old 1I lead |
| 2 | ET1 ER Main <-> Engine (near J/B2) | Decided 2026-10-20 |
| 3 | IG1 / IG2 Engine <-> Cowl (under the ECU) | Decided 2026-10-21: table below |
| Boxes | the 7 OEM boxes + ABS relay box | Decided 2026-10-21: J/B1, J/B3, R/B2, R/B4 stay; J/B2, R/B3, R/B5, ABS relay box go |
| 4 | IH1 Engine <-> A/C No.1 | Decided 2026-10-25 / 2026-10-26: A15 pin 8 drives `k_acc`; Ign 8 tacho to pin 18; same tacho through 4.7 kΩ to pin 9 (N61); pin 2 hard-grounded; IH1-4/5 engine lock-sensor wires unused. Table below |
| 5 | EB2 / ES2 | Decided 2026-10-25: A5 pin 1 from R/B No.4 10 A A/C; pressure switch already on the master; ER No.2 gone. Table below |
| 6 | Box plugs (J/B2, R/B2-5) | Decided 2026-10-25: R/B2 and R/B4 re-fed; fog removed (Dan 2026-11-02, was cut and cap); starter / heater / A/C fuse stay on R/B4. Table below (R/B2 rows pending Dan's B4 check) |
| 7 | Removed parts on kept harnesses | Decided 2026-10-25: OEM ECU / C9 / SRS / ABS / cruise ECU / meter extras are dead; the Dash taps (was ClusterLED and CSB3) stay. Table below |
| 8 | ER Main branches | Decided 2026-10-25: the whole ER Main goes (B9); re-feeds are new wire on the master. Table below |

**Joint-code corrections (1993 p.37 / p.43 / p.63 / p.83 / p.219).** IF2 / IG1 in the brief is IG1 + IG2 (Engine <-> Cowl under the ECU); IF1/IF2 = Floor <-> Cowl (left kick). IG2 / IH1 in the brief is IH1 only (Engine <-> A/C No.1). EB2 is Engine <-> Cowl (same spot as EB1); ES2 is Engine <-> ER No.2 (near the distributor); ES1 is 4A-FE only. EA1 / EB1 / ET1 confirmed. IJ1 = Cowl <-> A/C No.1; IK1/IK2 = front door RH.

**Two system facts.** All main power entered through the Engine Wire (F11 is part of J/B2; AM1, AM2, J/B1 feed, R/B4 feed and the J/B2 relay/fuse bus are fed through it). The OEM ECU straddles two harnesses: plug A (E9) is on the Cowl Wire; plugs B (E7) and C (E8) are on the Engine Wire.

## IG1 / IG2 (Engine Wire <-> Cowl Wire, under the ECU)

Decided 2026-10-21. Every wire is dead and comes out back to its last live point, except IG2-15 B-R (6 in pigtail: kill switch, then alternator IG), IG2-16 Y (charge lamp, stays) and IG1-11 (branch only; splice I2 and ground IE stay).

| Joint | Pin | Wire colour | Signal | Cabin end | Engine end (removed with Engine Wire) | EWD page | Action |
|---|---|---|---|---|---|---|---|
| IG1 | 1 | - | not used (vacuum-type cruise only) | - | - | 1992 p.186 | none |
| IG1 | 2 | P | IDL to cruise ECU | Cruise ECU plug B pin 9 IDL | ECU plug C pin 12 IDL / splice I7 -> TPS T1-2 | [90/92] 1990 p.119, 1992 p.181; 1993 p.80 | remove (dead) |
| IG1 | 3 | L | Cruise vehicle-speed sensor signal | Cruise ECU plug A pin 7 SPD (M/T) | Speed sensor for cruise (1993 V2) pin 2 | [90/92] 1990 p.118 | remove (dead) |
| IG1 | 4 | B-W | A/C clutch "on" to ECU AC | OEM ECU plug A (E9) pin 10 AC | Engine Wire E5 -> compressor A4-4, J/B2 2C-6 | 1993 p.79, 210 | remove (dead) |
| IG1 | 5 | - | ECT only (A/T) | - | - | 1992 p.171 | none |
| IG1 | 6 | GR-B | Cruise actuator VR3 | Cruise ECU A10 | Cruise actuator pin 3 | [90/92] 1990 p.119 | remove (dead) |
| IG1 | 7 | GR | Cruise actuator VR1 | Cruise ECU A12 | Actuator pin 1 | [90/92] | remove (dead) |
| IG1 | 8 | R-G | Cruise actuator MC | Cruise ECU B10 | Actuator pin 7 | [90/92] | remove (dead) |
| IG1 | 11 | BR | Cruise speed-sensor ground | Cowl splice I2 (USA) -> ground IE. Shared with the cruise control switch BR ground (combination switch plug C16 (B) pin 17, 1993 EWD grid 59; 1993 TIS Ground Points p.3) and cruise ECU GND A9. | Speed sensor pin 3 | [90/92] 1990 p.118, 1992 p.180 | remove IG1 branch back to splice I2 (I2/IE stays) |
| IG1 | 12 | Y-B | Oil-pressure warning | Comb meter C14 (C) pin 6 (removed) | ES2-3 -> ER No.2 -> oil pressure SW O2-1 | 1993 p.207 | remove (dead) |
| IG1 | 13 | Y-G | Water-temp gauge | Comb meter C12 (A) pin 6 | Water temp sender W2-1 | 1993 p.207 | remove (dead) |
| IG1 | 14 | B | Tach (igniter TAC) | Comb meter C14 (C) tacho; pin number not printed (*4) | Igniter I2-4 TAC (also feeds IH1-6 -> A15-18) | 1993 p.206 | remove (dead) |
| IG1 | 15 | L-R (cowl) / R-W (engine) | Turbo (boost) meter | Comb meter C13 (B) pin 4 | Turbo pressure sensor T2-2 PIM | 1993 p.207, p.80 | remove (dead) |
| IG1 | 16 | R-Y | Cruise actuator L through the cruise-cancel contact | Stop-light SW cruise contact -> cruise ECU B3 | Actuator pin 5 | [90/92] | remove (dead) |
| IG1 | 17 | GR-R | Cruise actuator VR2 | Cruise ECU A11 | Actuator pin 2 | [90/92] | remove (dead) |
| IG1 | 18 | P-B | Cruise actuator MO | Cruise ECU B4 | Actuator pin 6 | [90/92] | remove (dead) |
| IG2 | 1 | L-Y (cowl) / Y or L-Y (engine) | ECU ATS <-> A/C amp A15-2 | OEM ECU plug A pin 7 ATS | IH1-1 -> A15-2 | 1993 p.79, 210 | remove (dead) |
| IG2 | 2 | P | MIL (ECU W) to DLC1 "W" | Cowl splice I6 -> comb meter C12 (A) pin 3 + ECU plug A pin 5 W | DLC1 pin 2 W | 1993 p.81, 79 | remove (dead) |
| IG2 | 3 | W-L | SRS TC to DLC1 | Centre airbag sensor assy pin 12 TC (removed) | DLC1 TC (15) | [90/92] 1992 p.200 | remove (dead) |
| IG2 | 4 | R-L | Back-up SW feed (GAUGE 15A) | J/B3 3B-9 (GAUGE via 1E-5) | Back-up light SW B1 pin 2 (M/T) | [90/92] 1990 p.82, 1992 p.132 | remove (dead); new switch feed splices to the IG2-4 pigtail |
| IG2 | 5 | G | FC (fuel-pump control) | Circuit opening relay C9-4 (removed) | ECU A14 FC | 1993 p.78, 79 | remove (dead) |
| IG2 | 6 | W-L | TC diagnostic (cruise + ABS) | Cruise ECU B7 TC; IF1-3 -> ABS ECU TC | DLC1 TC (15) | [90/92] 1990 p.118/124 | remove (dead) |
| IG2 | 7 | P | BATT (EFI 15A) | OEM ECU plug A pin 1 BATT | J/B2 2C-4 (15A EFI) | 1993 p.79 | remove (dead) |
| IG2 | 12 | BR | SRS warning (LA) to DLC1 AB | Cowl splice I4 -> comb meter C12 (A) pin 8 + centre airbag sensor pin 9 LA | DLC1 AB (12) | 1993 p.207; 1992 p.200 | remove (dead) |
| IG2 | 13 | R-B | Back-up lamp output | IF1-7 -> Floor -> BP1-8 -> rear back-up lamps | Back-up SW B1 pin 1 | [90/92] 1992 p.132 | remove (dead); new switch output splices to the IG2-13 pigtail |
| IG2 | 14 | BR | Water-temp gauge ground | Comb meter C12 (A) pin 5 | Ground EC (intake manifold) | 1993 p.207 | remove (dead) |
| IG2 | 15 | B-R | ECU-IG 15A | J3 <- J/B1 1B-8 (15A ECU-IG) | Alternator IG (round plug G2 (B) pin 3) | 1993 p.74; 1992 p.180 | KEEP 6 in pigtail, splice (alt IG feed per master) |
| IG2 | 16 | Y | Charge lamp (alternator L) | Cowl splice I5 -> comb meter C14 (C) pin 8 | Alternator L (round plug G2 (B) pin 2) | 1993 p.74 | KEEP; Dash charge LED sinks to C14-8 |
| IG2 | 17 | W-R | ABS TS | IF1-16 -> ABS ECU TS | DLC1 TS (16) | [90/92] 1992 p.192 | remove (dead) |
| IG2 | 18 | B-Y | +B from EFI main relay | Cowl splice I6 -> ECU A12 / A13, C9-2 | J/B2 2C-10 / splice I7 (VSVs) | 1993 p.80, 78 | remove (dead) |
| IG2 | 19 | L-B | Fuel-pump + (FP check) | Cowl splice I1 -> IE2-19 and IF1-15 -> BP1-12 -> fuel pump | DLC1 FP | 1993 p.79, 78 | remove (dead) |
| IG2 | 20 | B | STA (cranking) | Cowl splice I6 -> ECU A11, C9-3, comb meter C13 (B) pin 10 | Engine Wire <- EB1-2 (starter relay out) | 1993 p.78, 206 | remove (dead) |

Rows tagged **[90/92]** are not 1993-verified (row 156).

## Groups 4-8 wire by wire (restored 2026-11-02, row 183)

Restored from the cut-list draft `cut-list-draft-2026-10-20.md` groups 4-8 (deleted in #399; read it with `git show`
at `7a53512^`, folder `harness/cut-list/`),
re-read against the 21 circuits above and DECISIONS B9. Pins and pages are the draft's (1993 EWD printed pages unless
tagged **[90/92]**). "Action" is the current plan: **remove** (dead; comes out back to its last live point), **keep**
(OEM wire stays and works as before), or **re-fed by** `<master wire id>` (new wire in `MASTER-wirelist.csv` does the
job). The draft was written under an older plan; where it disagrees, the current plan is followed and the "Draft said"
column shows the difference:

- R/B No.2 and No.4 stay (the draft removed them); R/B No.3 goes (fog, circuit 17).
- Starter stays on the OEM R/B No.4 relay through C11 (circuit 2): no `k_str`, C11 is not a Link input, Aux 8 is spare.
- No `k_htr` / `k_pwr` / `k_rev` twins (circuits 9, 11, 18): the OEM relays keep their own coil and contact wiring.
- The whole Engine Room Main Wire goes, outer loop included (B9; the draft kept the outer loop and reused its leads):
  every bay load is new wire to its device plug or 6 in pigtail.

### Group 4 - IH1 (Engine Wire <-> A/C No.1, behind the glove box)

| Pin | Colour | Signal | Kept-side end | EWD | Draft said | Action |
|---|---|---|---|---|---|---|
| 1 | L-Y | A15 -> OEM ECU ATS | A/C amp A15 pin 2 | 1993 p.79, 210 | maybe a new wire to a Link input | remove the IH1 leg; A15 pin 2 hard-grounded by `w_ac_cool_gnd` (D16) |
| 3 | Y-B | Compressor sensor coil | A15 pin 5 | 1993 p.210 | new wire IH1-3 -> A4-3 | remove; no master row: D16 uses no compressor sensor coil (the lock check is fed from the tacho, pin 9) |
| 4 | W-R | Compressor lock sensor | A15 pin 14 via cowl splice I12 (I12 also feeds the A24 thermistor pin 1) | 1993 p.210-211 | new wire IH1-4 -> A4-2 | remove the IH1 leg back to I12; I12 and A24 keep |
| 5 | W-L | Compressor lock sensor | A15 pin 9 | 1993 p.210 | new wire IH1-5 -> A4-1 | remove the IH1 leg; pin 9 re-fed by `w_lock_9` (tacho through `R-LOCK` 4.7 kΩ, N61) |
| 6 | B | Engine speed for lock detection | A15 pin 18 | 1993 p.211 | re-feed from a Link output (open) | re-fed by `w_tach_18` (Ign 8 tacho via `SP-TACH`) |

### Group 5 - EB2 (Engine <-> Cowl, A/C pressure switch) and ES2 (Engine <-> ER No.2)

| Joint | Pin | Colour | Signal | Kept-side end | EWD | Draft said | Action |
|---|---|---|---|---|---|---|---|
| EB2 | 1 | V-R | R/B4 10 A A/C fuse out to pressure switch A5 pin 1 | cowl I9 -> R/B4 10 A A/C fuse pin 2 (also the V-R bus to the A/C amps) | 1993 p.211 | cut + cap; R/B4 gone so the V-R bus needs a re-feed | remove the EB2 leg; A5 pin 1 re-fed by `w_acp_1` from the kept R/B4 A/C fuse; the cabin V-R bus keeps |
| EB2 | 2 | Y-R | Pressure switch output to the A/C amp | E10 -> IJ1-11 -> A15 pin 13 (and A3 idle-up VSV pin 2) | 1993 p.211 | reuse the cowl side | re-fed by `w_ac_psw_in` (A5 pin 4) + `w_ac_psw_sw` (A15 pin 13) at cabin splice `SP-AC-PSW` (D16) |
| EB2 | 3, 4 | - | no cavity | - | p.37 | none | none |
| ES2 | 1-5 | B, BR, Y-B, G, R | STA, ECT ground, oil pressure SW, STJ, THW | none (ER No.2 removed) | 1993 p.66, 80, 207 | remove | remove with the harness; oil pressure is the Link sensor `OIL-P` (AB-engine) and the oil LED on CSB3 L4 (`w_oil_k`) |

Open from the draft: whether the car has an A3 idle-up VSV (p.219 lists it, p.28 does not); check at the car.

### Group 6 - J/B No.2 (with F11) and R/B No.2-5

J/B No.2, F11 and R/B No.5 sit in the engine bay on the ER Main: every lead goes with it (B9). R/B No.2 and No.4 are
cabin boxes and stay (circuits 2, 9, 18). R/B No.3 goes (circuit 17).

**J/B No.2 and F11 (LH front, 1993 p.23-24)**

| Plug | Pin | Colour | Signal | Old load | EWD | Draft said | Action |
|---|---|---|---|---|---|---|---|
| 2A | 2 | L-R | 30 A CDS FAN out | condenser fan A2 pin 2 | p.210 | re-feed POWER FAN2 | remove; re-fed by `w_fan2_pwr` (K-FAN2, new wire to the uprated fan) |
| 2A | 3 | R | 15 A HEAD LH out | headlamp H1 pin 3 | p.116 | splice LOGIC HL onto the old R lead | remove; re-fed by `w_pmu_hl` (K-HL, new wire to H1's 6 in pigtail) |
| 2A | 4 | B-R | Radiator fan + | radiator fan R1 pin 2 | p.210 | re-feed POWER FAN | remove; re-fed by `w_fan_pwr` (K-FAN); fan ground `w_fan_gnd` to EA |
| 2A | 5 | W-B | Relay / coil ground node | ground EB | p.62, 67, 210 | cut + cap | remove (EB stays as a ground point, new wires only) |
| 2A | 6 | R-Y | 15 A HEAD RH out | headlamp H2 pin 3 | p.116 | splice LOGIC HR onto the old lead | remove; re-fed by `w_pmu_hr` (K-HR) |
| 2B | 2, 3, 4, 5 | W, B-R, W, W | AM1 in, AM2 in, J/B2 B+ bus, alternator S | F11 / battery / alternator | p.62, 74, 116 | gone with the Engine Wire | remove; AM1 / AM2 re-fed by `w_pdb_am1` / `w_pdb_am2` at IE1; alternator S by `w_alt_s_c` |
| 2C | 1, 3, 4, 5, 6, 10 | LG-B, W, P, W-B, B-W, B-Y | fan coil, ALT -> engine main relay, EFI BATT, ground, A/C clutch, EFI +B | engine | p.62, 79, 210 | gone | remove (Link owns EFI: `k_efi`) |
| 2D | 1 | B-W | A/C clutch power hop | R/B5 clutch relay pin 3 | p.210 | cut + cap | remove; clutch is `w_acc_clutch` (K-ACC to A4 pin 4) |
| 2D | 2, 3, 5, 6 | B-R, W, LG-B, W | rad-fan +, headlight relay loop, fan coil, HEAD bus in | R/B5 / loop | p.62, 116, 210 | cut | remove |
| 2E | 2 | W | 30 A RTR out | IE1-3 -> retract relay R8 pin 3 | p.116 | re-feed POWER RTR | remove; re-fed by `w_pmu_rtr` at IE1-3 (cowl side) |
| 2E | 3 | W | 15 A HAZ-HORN out | R/B5 horn relay pin 3; IE1-12 -> hazard SW H5-8 | p.130, 185 | re-feed LOGIC HZ + horn relay | remove; hazard re-fed by `w_haz_cp` (LOGIC HZ via `SP-HZ`); horn relay feed `w_horn_30_cp` / `w_horn_86_cp` |
| 2E | 4 | L-Y | 20 A DOME out | J/B1 1H-2 | p.132, 200, 207 | re-feed LOGIC DM | remove; re-fed by `w_pmu_dome` at 1H-2 (owner fix: DECISIONS B8 list) |
| 2E | 5 | W | AM1 out | IE1-10 -> cowl I2 -> ignition SW I13-4 and R/B2 30 A POWER fuse pin 1 | p.62, 66 | re-feed POWER AM1 | remove; re-fed by `w_pdb_am1` at IE1-10. I2 also feeds R/B2, as stock (Dan B17 b) |
| 2E | 6 | B-R | AM2 out | IE1-17 -> I13-10 | p.62, 66 | re-feed POWER AM2 | remove; re-fed by `w_pdb_am2` at IE1-17 |
| 2E | 7 | R-Y | Headlight relay coil | IE1-2 -> I2 -> light control SW C15, retract relay R8-8 | p.116 | re-feed LOGIC head relay coils | remove; re-fed by `w_head_coil_cp` (K-HL / K-HR coil 85 via `SP-HEAD-COIL`) |
| 2E | 8 | B-O | IGN 7.5 A to J/B2 relay coils | ER Main splice E13 / E4 <- J/B1 1H-7 | p.210, 79 | cut + cap at J/B2 and R/B5 | remove; 1H-7 itself keeps (tapped by `w_ig2_in`, `w_ign`, `w_k_on_86_cp`) |
| F11-A | 2, 3, 4, 7 | W, W, B, B-R | AM1, 100 A ALT, FL MAIN in, AM2 | battery, alternator | p.62, 64 | gone | remove (trunk battery and HeavyDC, B11) |
| F11-C | 1 | W-L | 60 A ABS out | ABS relays (ER Main E12) | p.62; 1992 p.192 | cut + cap | remove (ABS gone, circuit 6) |

**R/B No.2 (LH kick, cowl) - stays (circuit 18)**

| Terminal | Pin | Colour | Signal | Kept-side end | EWD | Draft said | Action |
|---|---|---|---|---|---|---|---|
| 30 A POWER fuse | 1 | W | AM1 branch in | cowl I2 <- IE1-10 | p.62 | keep | fed by AM1 through the factory I2 branch (`w_pdb_am1` at IE1-10), as stock; `w_rb2_feed` dropped (Dan B17 b) |
| 30 A POWER fuse | 2 | W-L | 30 A POWER out | I1 / I4 -> power main relay 4, door lock ECU, sunroof, seat | p.137 | keep | keep (fed through the kept POWER fuse); `w_rb2_wl` dropped (Dan B17 b) |
| Power main relay | 1 | W-G | window / accessory power out | I1 -> IC1-3, IK1-3 | p.137 | re-feed POWER PWR + `k_pwr` | keep (no `k_pwr`) |
| Power main relay | 2 | L-Y | coil + (GAUGE via key-off diode D6) | I1 / D6 | p.136-137 | reuse as `k_pwr` 86 | keep |
| Power main relay | 3 | W-B | coil ground | ground | p.137 | cut + cap | keep |
| Power main relay | 4 | W-L | contact in | I1 / I4 (POWER fuse out) | p.137 | cut + cap | keep |

R/B No.2 check (2026-11-02, Dan B4 / B17 b): the only feed is the factory W from cowl splice I2 (AM1, IE1-10) into the
30 A POWER fuse pin 1; W-L is that fuse's output, so nothing else may land on it (1993 p.26, p.62, p.136-145; 1990 p.46
and 1992 p.66 agree; US = Canada). Splice codes are per diagram: the "I2" on the 1990 / 1992 cruise pages (IG1-11 BR
ground, group 3) and the fog relay's low-beam "I2" (1992 p.128) may not be the AM1 splice; tell them apart by wire colour
(W = AM1) before removing a leg.

**R/B No.3 (RH kick, fog relay) [90/92] - goes (circuit 17)**

No 1993 TIS fog page: relay and switch pins from 1992 p.128 and Mitchell 1993 Fig. 1 (grid C2-3); the fuse, switch
illumination and ground ends from 1993 p.62 / p.109 / p.231. USA wiring (Canada differs: 1992 p.122). 1993 p.26 numbers
the relay cavities 1, 2, 3, 5 (pin 4 below may be cavity 5 on the box). Every wire is removed back to its last live
point, never capped (Dan 2026-11-02); each has a master row.

| Terminal | Pin | Colour | Signal | Kept-side end | EWD | Draft said | Action |
|---|---|---|---|---|---|---|---|
| Fog relay | 1 | R-W | fog lamp feed | cowl -> EA1-6 -> ER Main -> fog lamps | 1992 p.128 | open | remove whole (no live end; the bay leg goes with B9), `w_fog_rb3_1` |
| Fog relay | 4 | G-R | contact in (20 A FR FOG) | R/B4 FOG fuse pin 2 | 1992 p.128; p.62 | open | remove whole (the fuse and the relay both come out), `w_fog_rb3_4` |
| Fog relay | 3 | G-B | coil - (fog switch) | fog switch F12 pin 6 | 1992 p.128 | open | remove whole (switch and relay both come out), `w_fog_sw` |
| Fog relay | 2 | R-W | coil + (low-beam line, I2 / IE1-18) | cowl I2 low-beam lead (IE1-18 / C15-12) | 1992 p.128; p.116 | open | remove back to splice I2 (I2 keeps its 2 low-beam legs), `w_fog_rb3_2` |
| Fog switch F12 | 3 | W-B | ground | J/B No.3 3A-1 (ground bus) | p.231; Mitchell 1993 | - | remove back to J/B No.3 3A-1 (the bus stays for the other switches), `w_fog_sw_gnd` |
| Fog switch F12 | 1 | G | illumination + | J/B No.3 3C-14 (TAIL illumination bus) | p.109 | - | remove back to J/B No.3 3C-14, `w_fog_sw_ill` |
| Fog switch F12 | 2 | W-G | illumination - | J/B No.3 3A-10 (ILL- bus to rheostat R10) | p.109 | - | remove back to J/B No.3 3A-10, `w_fog_sw_ill_rtn` |
| Fog switch F12 | 4, 5 | - | not used; no fog indicator in the switch or the meter | - | Mitchell 1993; p.206-207 | - | none |

**R/B No.4 (RH kick, cowl) - stays (circuits 2, 9, 10)**

| Terminal | Pin | Colour | Signal | Kept-side end | EWD | Draft said | Action |
|---|---|---|---|---|---|---|---|
| Starter relay | 1 | B-W | coil + (ST1) | I8 / I9 <- ignition SW I13-7 | p.66, 78 | reuse as the crank signal | keep; tapped by `w_start_in_cp` (start request, LOGIC BUS2-13 -> `w_start` to Link DI 7), pin id `ST-1` (fault C3 fixed in phase 2) |
| Starter relay | 2 | B-W | contact in (ST1) | I8 / I9 <- I13-7 | p.66 | cut + cap | keep |
| Starter relay | 3 | B | coil - through clutch start SW C11 pin 1 | C11 | p.66 | C11 -> Link Aux 8 | keep: C11 completes the starter circuit in hardware, not a Link input (circuit 2) |
| Starter relay | 4 | B | starter out | cowl -> EB1-2 (Engine Wire) | p.66, 78 | cut + cap; `k_str` instead | re-fed by `w_strl_c` (R/B4 pin 4 -> DRB102 cavity 3) and `w_strl_e` (-> starter S) |
| Heater relay | 1 | L-W | coil - from A/C amp HR | IQ2-9 -> A31 / A32 HR | p.215 | `k_htr` 85 | keep (no `k_htr`) |
| Heater relay | 3 | R-L | coil + (GAUGE via J4) | cowl J4 | p.215 | `k_htr` 86 | keep |
| Heater relay | 4 | B | blower + out | J5 -> blower B4 pin 2, -> 10 A A/C fuse pin 1 | p.211, 215 | re-feed from `k_htr` 87 | keep |
| Heater relay | 5 | L | contact in | 40 A HEATER fuse pin 2 | p.215 | cut + cap | keep |
| Heater relay | 2 | W-B | 87a = ground | R/B4 plug A pin 4 -> ground IG | p.215 | cut + cap | keep |
| 40 A HEATER fuse | 1 | W | feed in (EB1-3 via I9) | cowl I9 | p.62, 215 | cut + cap | re-fed by `w_rb4_feed` (AMI IN-1), pin id `HTR-1` (fault C3 fixed in phase 2); the EB1-3 leg comes out (group 1), leaving splice I9 with one live leg (open, row 183) |
| 40 A HEATER fuse | 2 | L | out to heater relay | heater relay pin 5 | p.215 | cut + cap | keep |
| 20 A FR FOG fuse | 1 / 2 | W / G-R | feed in (I9) / out to R/B3 pin 4 | I9; R/B3 | p.62; 1992 p.128 | fog removed | the fuse comes out, its seat stays empty; pin 1 lead removed back to splice I9 (`w_fog_fuse_in`; I9 keeps the HEATER and old EB1-3 legs), pin 2 lead removed whole (`w_fog_rb3_4`) |
| 10 A A/C fuse | 1 | B | in from heater relay 4 (J5) | J5 bus | p.211, 215 | cut + cap | keep |
| 10 A A/C fuse | 2 | V-R | A/C IG out | I9 -> EB2-1 (A5) and the V-R bus to the A/C amps | p.211-212 | re-feed, slot open | keep; A5 pin 1 tapped by `w_acp_1` (group 5) |

**R/B No.5 (RH front, ER Main) - goes**

| Relay | Pin | Colour | Signal | Old load | EWD | Draft said | Action |
|---|---|---|---|---|---|---|---|
| Horn relay | 3 | W | HAZ-HORN feed | J/B2 2E-3 | p.185 | cut + cap | remove; K-HORN (LOGIC M3) fed by `w_horn_30_cp` / `w_horn_86_cp` |
| Horn relay | 2 | G | coil - to horn SW | IE1-19 -> horn SW C15-10 | p.185 | reuse | remove the ER Main leg; re-fed by `w_horn_85_cp` (K-HORN 85 at IE1-19, cowl side) |
| Horn relay | 1 | G-R | horn + | horns H3-1, H4-1 | p.185 | splice the LOGIC horn relay onto the G-R lead | remove; re-fed by `w_pmu_horn_cp` -> `SP-HORN` -> `w_horn_lh` / `w_horn_rh` (new wire to each horn) |
| A/C mag clutch relay | 1, 5 | R-L | coil + / contact in (GAUGE) | J/B1 1H-1 | p.210 | cut + cap | remove |
| A/C mag clutch relay | 2 | L-Y | coil - (A/C amp MGC) | EA1-3 -> IJ1-1 -> A15 pin 8 | p.210-211 | maybe reuse into `k_acc` | remove the ER Main leg; A15 pin 8 re-fed by `w_acc_trig` (to K-ACC 85, D16) |
| A/C mag clutch relay | 3 | B-W | clutch power out | E2 -> 2D-1 | p.210 | cut + cap | remove; clutch is `w_acc_clutch` |
| Condenser fan relay No.2 | 1-5 | B-O, LG-B, B, W-B, B-R | coil IGN, coil -, series link, NC ground, rad fan + | ER Main | p.210 | cut + cap | remove; fans are K-FAN / K-FAN2 on Link outputs (`w_fan85`, `w_fan285`) |
| Condenser fan relay No.3 | 5 | B-W | condenser fan motor (-) | A2 pin 1 | p.210 | re-ground A2-1 to EA | remove; new fan grounded by `w_fan2_gnd` to EA |
| Condenser fan relay No.3 | 1, 2, 3 | B-W, W-B, B | coil +, coil -, series link | ER Main | p.210 | cut + cap | remove |
| Fuel pump relay | 1-4 | L-O, L-W, G-R, L-B | contact common, low / high speed out, coil (ECU FPR) | C9, F10, IE2-18 / 19 / 20 | p.78-79 | cut + cap | remove; fuel pump is K-FP in the trunk (`w_fpump_r`, coil `w_fp85`) |

Open from the draft: R/B No.2 / No.4 also carry multi-pin plugs (1993 p.26-27) whose cavity pinout is not in the 1993
pulls; the terminals above are what the system pages show. Check at the car with the boxes in hand.

### Group 7 - removed parts that sit on kept harnesses

Every lead below is dead and comes out back to its last live point (splice, plug or box), unless the action names a
master wire. Meter plug codes are the 1993 codes C12 (A) / C13 (B) / C14 (C), in the master too (N14 a, 2026-11-05).

| Part / plug | Pins | Kept-side ends | EWD | Draft said | Action |
|---|---|---|---|---|---|
| OEM ECU plug A (E9, Cowl Wire) | 1 BATT, 2 ELS, 5 W, 6 FPR, 9 SPD, 10 AC, 11 STA, 12 / 13 +B, 14 FC | IG2-7, J/B1 1D-6, I6 / meter C12-3, IE2-20, J2 (meter C13-6), IG1-4, I6, I6, IG2-5 / C9-4 | 1993 p.79-81 | cut + cap | remove |
| OEM ECU plug A (E9) | 4 STP (G-W) | J2 <- stop light SW S9 | 1993 p.79 | cut + cap | remove the E9 leg; S9 pin 1 keeps, tapped by `w_sw6` (CSB3 opto IN1) |
| OEM ECU plug A (E9) | 7 ATS (L-Y) | IG2-1 -> IH1-1 -> A15-2 | 1993 p.79 | open (see IH1-1) | remove; A15 pin 2 grounded by `w_ac_cool_gnd` (group 4) |
| OEM ECU plug A (E9) | 21 ACT (LG-B) | IJ1-3 (G-Y) -> A15 pin 11 | 1993 p.79 | maybe carry ACT to the Link | remove the E9 leg; A15 pin 11 re-fed by `w_ac_kill` (Link ACT kill, D16) |
| Circuit opening relay C9 (cowl) | 1, 2, 3, 4, 6 | IE2-18, I6, I6, IG2-5, J/B3 3B-2 -> ground ID | 1993 p.78 | cut + cap | remove (J/B3 and ID keep) |
| SRS centre airbag sensor | 1, 6, 7, 8, 9, 12, 13, 14 | J/B1 1C-3 / 1C-1 / 1C-4 / 1C-2, I4 (meter C12-7 / -8), ground IE / IG, IG2-3, IG2-12 | Mitchell 1993 Fig.12; 1992 p.200 | cut + cap | remove (circuit 5) |
| SRS front sensors F3 / F4, squib leads | 2-5, 10-11 | cowl runs along each fender; spiral cable | Fig.12; 1993 p.28 | remove back to the cowl trunk | remove |
| ABS ECU (26-pin and 16-pin), actuator A7 / A8, relays A11 / A12, check conn A9 / A10 | all | ID1, IF1, J/B1 1F-8 / 1F-11 / 1F-13, J2, decel sensor, IF1-16 -> IG2-17 | Mitchell 1993 Fig.13; 1992 p.192 | cut + cap; remove the ID1 leads | remove (circuit 6); J/B1 1F-8 park brake keeps its other loads |
| Wheel speed sensors (A13, A14, rears) | 1 / 2 | ER Main / Cowl / Floor leads | 1992 p.192 | cut at the sensor plugs | sensors keep; OEM leads removed; re-fed by WheelSpeed-Front / -Rear (`WSS-FL`, `WSS-FR`, `WSS-RL`, `WSS-RR`) |
| Cruise ECU plug A / B (motor type) | all but the stalk leads | J3, stop SW, J2, C17, park brake SW, IG1-6 / 7 / 17 / 18 / 2 / 8, meter C12-2, IG2-6 | Mitchell 1993 Fig.12; [90/92] 1990 p.118-119 | cut + cap, keep the stalk leads | remove (circuit 4) |
| Cruise control switch in the combination switch, plug C16 (B) | its 3 pins (master; Always 1993, README) | stalk switch | 1993 EWD grid 59 (Mitchell Fig. 15); 1993 TIS p.HdlitUSA (C16 = combination SW (B)); 1990 p.116 / 1992 p.180 same | keep for the CSB3 | keep; tapped by `w_an2`, `w_sw2`, `w_cru_gnd` (Dash) |
| Cruise clutch switch C17 | 2 (B) | was cruise ECU N&C | Mitchell 1993 Fig.12; 1993 p.32 | not in the draft | keep; tapped by `w_sw5` (CSB3 pin 20, the one clutch input) |
| Meter C12 (A) (1993) | 1, 2, 3, 5, 6, 7, 8, 9, 10 | rheostat, cruise PI, I6, IG2-14, IG1-13, I4, I4, IF1-9, IF1-12 | 1993 p.206-207 | cut + cap | remove (old meter gone, circuit 7) |
| Meter C13 (B) | 2 G-B turn LH, 11 G-Y turn RH, 12 R-L high beam | J3 / IE1-11 | 1993 p.206 | reuse per Dash | keep; tapped by `w_tl_a`, `w_tr_a`, `w_hb_a` (Dash) |
| Meter C13 (B) (1993) | 1, 3, 4, 5, 6, 7, 10 | J/B3 3B-6, IF1-14, IG1-15, J6, J2, 3B-9, IG2-20 | 1993 p.206 | cut + cap | remove |
| Meter C14 (C) | 9 B-O IGN, 8 Y charge, 1 R-G brake / park brake | 1D-5, I5 / IG2-16, J6 | 1993 p.206-207 | reuse per Dash | keep; tapped by `w_ig_tap`, `w_chg_k`, `w_pk_k` (Dash) |
| Meter C14 (C) (1993) | 3, 4, 5, 6 oil (Y-B), 10, tacho | 3B-10, J1, integration relay, IG1-12, 3B-16, IG1-14 | 1993 p.206-207 | cut + cap | remove; oil warning is the LED on CSB3 L4 (`w_oil_a` / `w_oil_k`) |
| Rear wiper motor and relay, rear washer outlet W1 pin 3 [90/92] | 1-3; W1-3 | back door wire -> J/B1 1F-10, rear wiper switch (1993 code TBD) | 1992 p.150 | cut + cap | remove (R54); front washer W1 pins 1 / 2 re-fed by `w_wash_neg` / `w_wash_pos`. Check at the car whether the pump has a pin 3 |
| Igniter, ECU plugs B / C, DLC1, cruise actuator, compressor clutch lead, back-up SW lead | all | only through IG1 / IG2 / IH1 / EB1 / EB2 | - | leave with the Engine Wire | remove; back-up SW wires re-fed by `w_rev_feed_c` / `w_rev_lamps` at the IG2-4 / IG2-13 pigtails (circuit 11) |

Open from the draft: the ABS ECU ground pin labels in Mitchell Fig.13 are partly illegible, and the front airbag sensor
leads are taken to be Cowl Wire (no joint drawn). Confirm at the car.

### Group 8 - Engine Room Main Wire branches

The draft chopped only the branches into the engine area and kept the outer loop. Under B9 the whole ER Main goes.
Every row is **remove**; the new wire that takes over each load is listed.

| Branch | Colour | Old job | EWD | Draft said | Action |
|---|---|---|---|---|---|
| ER Main -> ET1 lead (J/B1 1I-1) | B | J/B1 main B+ | p.62 | chop at ET1, re-feed | remove, keeping a 6 in 1I-1 stub at J/B1; re-fed by `w_pdb_jb1` (JB1 60 A, 6 AWG) |
| ER Main -> J/B2 (2A / 2D / 2E) | various | headlamps, fans, RTR, HAZ-HORN, DOME, AM1 / AM2, IGN, ground | p.23, 62, 116, 210 | chop at J/B2, splice new feeds onto the kept leads | remove; re-feeds as group 6 |
| ER Main -> F11-C | W-L | 60 A ABS | p.62 | chop | remove |
| ER Main -> R/B5 (RH front) | various | fan relays, clutch relay, horn relay, FP relay | p.27, 78, 185, 210 | chop at R/B5, re-feed horns, re-ground A2-1 | remove; re-feeds as group 6 (R/B No.5) |
| ER Main -> fuel pump resistor F10 + splice E3 | L-B / L-W | FP low / high speed | p.78 | chop, remove F10 | remove |
| ER Main -> ABS actuator / relays / check conn | various | ABS | 1992 p.192 | chop | remove |
| ER Main splice E13 / E4 IGN branch | B-O | IGN to J/B2 2E-8 and R/B5 relay No.2 | p.210 | chop both ends | remove; J/B1 1H-7 keeps |
| ER Main ground lead 2A-5 -> EB | W-B | relay / coil ground | p.62 | remove or cap | remove |
| ER Main outer loop: headlamps H1 / H2 | R, R-Y, R-L, R-W | lamp feed and returns | p.116 | kept (outer loop) | remove to the 6 in pigtails; re-fed by `w_pmu_hl`, `w_pmu_hr`, `w_hl_high` (IE1-11), `w_hl_low` (IE1-18) |
| ER Main outer loop: front turn / clearance / markers F5-F8 | G-B, G-Y, G | turn and TAIL | p.112, 130 | kept | remove to the pigtails; re-fed by `w_turn_f7` (1H-4), `w_turn_f8` (1H-8), `w_clr` (1H-6) via `SP-CLR` |
| ER Main outer loop: pop-up motors R2 / R3 | G, G-O, G-Y, G-B, G-W | retract feed and limits | p.117 | kept | remove to the pigtails; re-fed by the `w_rtr_*` wires from IE1-7 / 8 / 9 / 14 / 15 / 16 |
| ER Main / cowl: wiper F9 and washer W1 | L, L-B, L-O, L-R | wiper +B, LO, HI, park; washer | p.148 | kept | remove to the pigtails; re-fed by `w_wip_b` (1H-5), `w_wip_lo` (IE1-13), `w_wip_hi` (IE1-20), `w_wip_park` (IE1-6), `w_wash_neg` / `w_wash_pos` |
| ER Main fog branch (EA1-6 -> splice E1 -> fog lamps F1 / F2 -> E2 -> EA) | R-W, W-B | fog lamps | 1992 p.128 | kept / open | remove with the ER Main (circuit 17); its cabin leg R/B3-1 -> EA1-6 is `w_fog_rb3_1` |

The cabin-side stubs these land on stay: J/B1 1H-2 / 4 / 5 / 6 / 7 / 8 and 1I-1, IE1 (cowl side). They are ER Main
plugs at J/B1 (1993 p.63), so they are 6 in stubs of a removed wire; they are not yet on B9's kept-pigtail list (fault C6,
carried in OPEN-ITEMS row 183: this list is the one to add). Open from the draft: walk the car for anything else taped into the ER Main trunk near J/B2.
