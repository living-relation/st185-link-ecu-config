# Circuit plan - decided by complete circuit

Dan reviews the rewire by whole circuits, not single wires (2026-10-21). The 21-circuit table was approved with
changes to #2, #9, #11 and #18, then written into `docs/harness/MASTER-wirelist.csv` on 2026-10-25 (row 164). Pins are
1993 EWD; ECU pins are Link G4X XtremeX. This file is not a wiring source. Factory keep / gone list: `README.md`
"What stays and what goes". Approved routes stay in `routes/` (do not delete or reroute).

| # | Circuit | Plan (in the master) |
|---|---|---|
| 1 | Engine management (factory ECU, igniter, EFI relays) | Gone. The Link plus the new engine harness replace it. |
| 2 | Starting | OEM starter relay in R/B No.4 stays. Coil + from key START; coil - through the clutch start switch C11. C11 completes the starter circuit in hardware; it is not an ECU input. No `k_str`. Aux 8 is spare. |
| 3 | Charging | IG2-15 B-R keeps a 6 in pigtail: kill switch, then alternator IG. IG2-16 Y stays and drives the 12 V charge LED in the ClusterLED harness (sinks to OEM cluster plug C12-8). Alternator B+ on the heavy-cable harness. |
| 4 | Cruise | The OEM cruise ECU and actuator are gone; the stalk stays as CSB3 buttons. Cruise control clutch switch C17 pin 2 to CSB3 pin 20 (`w_sw5`) is the one ECU clutch input (flat-shift, via VDI6). C11 completes the starter circuit in hardware; it is not an ECU input. |
| 5 | SRS | Gone. |
| 6 | ABS | Gone. The wheel speed sensors get their own mini harnesses to the VRC enclosure. |
| 7 | Gauges + warning lamps | Gone; replaced by the CAN cluster. LEDs take turn, high beam, charge and park brake from the OEM cluster plugs, oil pressure from CSB3 L4 (cavity 26, 0x643 byte 3). OEM dimmer R10 stays for the rest of the dash lighting. Headlight-sense: tap R10 pin 1 green TAIL through EL814 IN3 to centre-cluster GPIO28 (Dan 2026-10-26: no change; encoder not used). |
| 8 | Main power (AM1, AM2, J/B1, dome, hazard, retract) | Trunk battery -> glove-box boxes -> cabin landings. `w_pdb_jb1` is behind the dash to J/B No.1 1I, 6 AWG for our 60 A JB1 fuse (`cad/fusebox/src/spec.py` AMI_AWG). |
| 9 | Blower | R/B No.4 stays with its heater relay, 40 A HEATER and 10 A A/C fuses; one new feed from B1 AMI IN-1. No `k_htr`. |
| 10 | A/C | Both amps stay. D16: A15 pin 8 drives `k_acc` coil 85; coil 86 from B2-BUS2-8; Link Aux 4 is the ACT kill only; pin 2 hard-grounded; Ign 8 is tacho to pin 18 and, through 4.7 kΩ, to pin 9 (lock-sensor workaround, N61 2026-10-21 / Dan 2026-10-26). A/C button and evap wires to the Link removed. Cabin sensor-common splice `SP-AC-SG` stays (replaces E10). The A/C pressure switch is the factory trinary switch, wired to the factory A/C amp; factory yellow-red is that switch output, not the sensor ground (1990 ST185 EWD p.150 / p.152). |
| 11 | Reverse + back-up lamps | No K-REV. OEM back-up switch drives the lamps; output tapped through opto IN2. New switch wires splice to the IG2-4 / IG2-13 pigtails. Factory rear lighting stays (no RearLights harness). |
| 12 | Fuel pump | `k_fp` in the trunk, rear-fuel harness (B3-K1). |
| 13 | Front lights + pop-ups | Front run (Route 17 line 10), spliced to the 6 in pigtails. |
| 14 | Horn | Front run, relay in the glove box (B2-M3). |
| 15 | Radiator + condenser fans | Link-controlled relays, front run. |
| 16 | Wiper + washer | Wiper on the driver fender run, washer pump on the front run. |
| 17 | Fog | Removed: R/B No.3, switch F12 and every fog wire, cut and capped. 20 A FR FOG fuse in R/B No.4 is a spare. No spare circuit to the old fog-lamp spots. |
| 18 | Windows, locks, sunroof, seat | R/B No.2 stays; its 30 A POWER fuse gets one new feed from B1 AMI IN-6. No `k_pwr`. |
| 19 | Diagnostic plug (DLC1) | Gone. |
| 20 | Alarm hood pin + siren | Front run and driver fender run. |
| 21 | Engine-bay ground studs (EA, EB, EC) | The studs stay as ground points; every ground wire on them is new. |

ETB hold power is all cabin and J/B No.1 stays: Aux 6 (A28) holds K-EFI; DI 9 (B28) senses IG2; the IG2 wake diode feeds A5 from J/B1 1H-7; K-ETB on Aux 2 (A20) feeds B5.

Fuse box: parked. Seat-to-circuit assignment is `sot/fuse-relay-map.csv` (B1 POWER, B2 LOGIC, B3 trunk block, B4 EPS).

## Cut-list groups (row 164)

| Group | Joint | Status |
|---|---|---|
| 1 | EB1 Engine <-> Cowl (rear of RH fender) | Decided 2026-10-20 / 2026-10-26: dead. If the ignition-switch black-orange wire is at the engine plug (EB1-1), remove it. J/B No.1 fed from POWER JB1 60 A, 6 AWG for our 60 A load, spliced to a 6 in stub of the old 1I lead |
| 2 | ET1 ER Main <-> Engine (near J/B2) | Decided 2026-10-20 |
| 3 | IG1 / IG2 Engine <-> Cowl (under the ECU) | Decided 2026-10-21: table below |
| Boxes | the 7 OEM boxes + ABS relay box | Decided 2026-10-21: J/B1, J/B3, R/B2, R/B4 stay; J/B2, R/B3, R/B5, ABS relay box go |
| 4 | IH1 Engine <-> A/C No.1 | Decided 2026-10-25 / 2026-10-26: A15 pin 8 drives `k_acc`; Ign 8 tacho to pin 18; same tacho through 4.7 kΩ to pin 9 (N61); pin 2 hard-grounded; IH1-4/5 engine lock-sensor wires unused |
| 5 | EB2 / ES2 | Decided 2026-10-25: A5 pin 1 from R/B No.4 10 A A/C; pressure switch already on the master; ER No.2 gone |
| 6 | Box plugs (J/B2, R/B2-5) | Decided 2026-10-25: R/B2 and R/B4 re-fed; fog cut and cap; starter / heater / A/C fuse stay on R/B4 |
| 7 | Removed parts on kept harnesses | Decided 2026-10-25: OEM ECU / C9 / SRS / ABS / cruise ECU / meter extras are dead; ClusterLED and CSB3 taps stay |
| 8 | ER Main branches | Decided 2026-10-25: chop at J/B2 / R/B5 / ET1; re-feeds already on the master |

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
| IG1 | 11 | BR | Cruise speed-sensor ground | Cowl splice I2 (USA) -> ground IE. Shared with cruise stalk C14-17 BR and cruise ECU GND A9. | Speed sensor pin 3 | [90/92] 1990 p.118, 1992 p.180 | remove IG1 branch back to splice I2 (I2/IE stays) |
| IG1 | 12 | Y-B | Oil-pressure warning | Comb meter C14 (C) pin 6 (removed) | ES2-3 -> ER No.2 -> oil pressure SW O2-1 | 1993 p.207 | remove (dead) |
| IG1 | 13 | Y-G | Water-temp gauge | Comb meter C12 (A) pin 6 | Water temp sender W2-1 | 1993 p.207 | remove (dead) |
| IG1 | 14 | B | Tach (igniter TAC) | Comb meter C14 (C) tacho; pin number not printed (*4) | Igniter I2-4 TAC (also feeds IH1-6 -> A15-18) | 1993 p.206 | remove (dead) |
| IG1 | 15 | L-R (cowl) / R-W (engine) | Turbo (boost) meter | Comb meter C13 (B) pin 4 | Turbo pressure sensor T2-2 PIM | 1993 p.207, p.80 | remove (dead) |
| IG1 | 16 | R-Y | Cruise actuator L through the cruise-cancel contact | Stop-light SW cruise contact -> cruise ECU B3 | Actuator pin 5 | [90/92] | remove (dead) |
| IG1 | 17 | GR-R | Cruise actuator VR2 | Cruise ECU A11 | Actuator pin 2 | [90/92] | remove (dead) |
| IG1 | 18 | P-B | Cruise actuator MO | Cruise ECU B4 | Actuator pin 6 | [90/92] | remove (dead) |
| IG2 | 1 | L-Y (cowl) / Y or L-Y (engine) | ECU ATS <-> A/C amp A15-2 | OEM ECU plug A pin 7 ATS | IH1-1 -> A15-2 | 1993 p.79, 210 | remove (dead) |
| IG2 | 2 | P | MIL (ECU W) to DLC1 "W" | Cowl splice I6 -> comb meter C12 (B) pin 3 + ECU plug A pin 5 W | DLC1 pin 2 W | 1993 p.81, 79 | remove (dead) |
| IG2 | 3 | W-L | SRS TC to DLC1 | Centre airbag sensor assy pin 12 TC (removed) | DLC1 TC (15) | [90/92] 1992 p.200 | remove (dead) |
| IG2 | 4 | R-L | Back-up SW feed (GAUGE 15A) | J/B3 3B-9 (GAUGE via 1E-5) | Back-up light SW B1 pin 2 (M/T) | [90/92] 1990 p.82, 1992 p.132 | remove (dead); new switch feed splices to the IG2-4 pigtail |
| IG2 | 5 | G | FC (fuel-pump control) | Circuit opening relay C9-4 (removed) | ECU A14 FC | 1993 p.78, 79 | remove (dead) |
| IG2 | 6 | W-L | TC diagnostic (cruise + ABS) | Cruise ECU B7 TC; IF1-3 -> ABS ECU TC | DLC1 TC (15) | [90/92] 1990 p.118/124 | remove (dead) |
| IG2 | 7 | P | BATT (EFI 15A) | OEM ECU plug A pin 1 BATT | J/B2 2C-4 (15A EFI) | 1993 p.79 | remove (dead) |
| IG2 | 12 | BR | SRS warning (LA) to DLC1 AB | Cowl splice I4 -> comb meter C12 (A) pin 8 + centre airbag sensor pin 9 LA | DLC1 AB (12) | 1993 p.207; 1992 p.200 | remove (dead) |
| IG2 | 13 | R-B | Back-up lamp output | IF1-7 -> Floor -> BP1-8 -> rear back-up lamps | Back-up SW B1 pin 1 | [90/92] 1992 p.132 | remove (dead); new switch output splices to the IG2-13 pigtail |
| IG2 | 14 | BR | Water-temp gauge ground | Comb meter C12 (A) pin 5 | Ground EC (intake manifold) | 1993 p.207 | remove (dead) |
| IG2 | 15 | B-R | ECU-IG 15A | J3 <- J/B1 1B-8 (15A ECU-IG) | Alternator IG (G2 A-2) | 1993 p.74; 1992 p.180 | KEEP 6 in pigtail, splice (alt IG feed per master) |
| IG2 | 16 | Y | Charge lamp (alternator L) | Cowl splice I5 -> comb meter C14 (C) pin 8 | Alternator L (G2 A-1) | 1993 p.74 | KEEP; ClusterLED charge LED sinks to C12-8 |
| IG2 | 17 | W-R | ABS TS | IF1-16 -> ABS ECU TS | DLC1 TS (16) | [90/92] 1992 p.192 | remove (dead) |
| IG2 | 18 | B-Y | +B from EFI main relay | Cowl splice I6 -> ECU A12 / A13, C9-2 | J/B2 2C-10 / splice I7 (VSVs) | 1993 p.80, 78 | remove (dead) |
| IG2 | 19 | L-B | Fuel-pump + (FP check) | Cowl splice I1 -> IE2-19 and IF1-15 -> BP1-12 -> fuel pump | DLC1 FP | 1993 p.79, 78 | remove (dead) |
| IG2 | 20 | B | STA (cranking) | Cowl splice I6 -> ECU A11, C9-3, comb meter C13 (B) pin 10 | Engine Wire <- EB1-2 (starter relay out) | 1993 p.78, 206 | remove (dead) |

Rows tagged **[90/92]** are not 1993-verified (row 156).
