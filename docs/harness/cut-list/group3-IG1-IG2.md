# Group 3 - IG1 / IG2 (Engine Wire <-> Cowl Wire, under the ECU)

Decided with Dan 2026-10-21 (row 164). A decision record: the master `../MASTER-wirelist.csv` wins, and these become
master rows after cut-list groups 4-8. Every wire is dead and comes out back to its last live point, except IG2-15 B-R
(6 in pigtail: kill switch, then alternator IG), IG2-16 Y (charge lamp, stays) and IG1-11 (branch only; splice I2 and
ground IE stay).

| Joint | Pin | Wire colour | Signal | Cabin end (connector, pin) | Engine end (connector, pin) - removed with Engine Wire | EWD page | Action |
|---|---|---|---|---|---|---|---|
| IG1 | 2 | P | IDL to cruise ECU | Cruise ECU plug B pin 9 IDL (removed, earlier plan) | ECU plug C pin 12 IDL / Engine Wire splice I7 -> TPS T1-2 | [90/92] 1990 p.119, 1992 p.181; 1993 p.80 shows "to cruise ECU" | remove (dead) back to last live point |
| IG1 | 3 | L | Cruise vehicle-speed sensor signal | Cruise ECU plug A pin 7 SPD (M/T) | Speed sensor for cruise (1993 V2, on transaxle) pin 2 | [90/92] 1990 p.118; Mitchell Fig.12 "BLU" | remove (dead) back to last live point |
| IG1 | 4 | B-W | A/C clutch "on" to ECU AC | OEM ECU plug A (E9) pin 10 AC | Engine Wire E5 -> compressor A4-4, J/B2 2C-6 | 1993 p.79, 210 | remove (dead) back to last live point |
| IG1 | 6 | GR-B | Cruise actuator VR3 | Cruise ECU A10 | Cruise actuator (motor type) pin 3 | [90/92] 1990 p.119; Mitchell Fig.12 | remove (dead) back to last live point |
| IG1 | 7 | GR | Cruise actuator VR1 | Cruise ECU A12 | Actuator pin 1 | [90/92] | remove (dead) back to last live point |
| IG1 | 8 | R-G | Cruise actuator MC | Cruise ECU B10 | Actuator pin 7 | [90/92] | remove (dead) back to last live point |
| IG1 | 11 | BR | Cruise speed-sensor ground | Cowl splice I2 (USA) -> ground IE. Shared with cruise stalk C14-17 BR and cruise ECU GND A9. | Speed sensor pin 3 | [90/92] 1990 p.118, 1992 p.180 | remove IG1 branch back to splice I2 (I2/IE stays) |
| IG1 | 12 | Y-B | Oil-pressure warning | Comb meter C14 (C) pin 6 (removed) | Engine Wire -> ES2-3 -> ER No.2 -> oil pressure SW O2-1 | 1993 p.207 | remove (dead) back to last live point |
| IG1 | 13 | Y-G | Water-temp gauge | Comb meter C12 (A) pin 6 | Water temp sender W2-1 | 1993 p.207 | remove (dead) back to last live point |
| IG1 | 14 | B | Tach (igniter TAC) | Comb meter C14 (C) tacho; pin number not printed (*4) | Igniter I2-4 TAC (also feeds IH1-6 -> A15-18) | 1993 p.206 | remove (dead) back to last live point |
| IG1 | 15 | L-R (cowl) / R-W (engine) | Turbo (boost) meter | Comb meter C13 (B) pin 4 | Turbo pressure sensor T2-2 PIM | 1993 p.207, p.80 | remove (dead) back to last live point |
| IG1 | 16 | R-Y | Cruise actuator L (magnetic clutch) through the cruise-cancel contact | Stop-light SW (with cruise), cruise contact R-Y (1992 "S10 pin 4"; Mitchell Fig.12 RED-YEL) -> cruise ECU B3 | Actuator pin 5 | [90/92]; Mitchell Fig.12 | remove (dead) back to last live point |
| IG1 | 17 | GR-R | Cruise actuator VR2 | Cruise ECU A11 | Actuator pin 2 | [90/92] | remove (dead) back to last live point |
| IG1 | 18 | P-B | Cruise actuator MO | Cruise ECU B4 | Actuator pin 6 | [90/92] | remove (dead) back to last live point |
| IG2 | 1 | L-Y (cowl) / Y (engine, p.79) or L-Y (engine, p.210) | ECU ATS <-> A/C amp A15-2 | OEM ECU plug A pin 7 ATS | Engine Wire -> IH1-1 -> A15-2 | 1993 p.79, 210 | remove (dead) back to last live point |
| IG2 | 2 | P | MIL (ECU W) to DLC1 "W" | Cowl splice I6 -> comb meter C12 (A) pin 3 + ECU plug A pin 5 W | DLC1 (check connector) pin 2 W | 1993 p.81, 79 | remove (dead) back to last live point |
| IG2 | 3 | W-L | SRS TC to DLC1 | Centre airbag sensor assy pin 12 TC (removed) | DLC1 TC (15) | [90/92] 1992 p.200; Mitchell Fig.12 "check conn" | remove (dead) back to last live point |
| IG2 | 4 | R-L | Back-up SW feed (GAUGE 15A) | J/B3 3B-9 (GAUGE via 1E-5) | Back-up light SW B1 pin 2 (M/T) | [90/92] 1990 p.82, 1992 p.132 | remove (dead) back to last live point |
| IG2 | 5 | G | FC (fuel-pump control) | Circuit opening relay C9-4 (cowl, removed) | ECU A14 FC (drawn crossing here) | 1993 p.78, 79 | remove (dead) back to last live point |
| IG2 | 6 | W-L | TC diagnostic (cruise + ABS) | Cruise ECU B7 TC; IF1-3 -> ABS ECU TC | DLC1 TC (15) | [90/92] 1990 p.118/124, 1992 p.180/192 | remove (dead) back to last live point |
| IG2 | 7 | P | BATT (EFI 15A) | OEM ECU plug A pin 1 BATT | J/B2 2C-4 (15A EFI) | 1993 p.79 | remove (dead) back to last live point |
| IG2 | 12 | BR | SRS warning (LA) to DLC1 AB | Cowl splice I4 -> comb meter C12 (A) pin 8 + centre airbag sensor pin 9 LA | DLC1 AB (12) | 1993 p.207; 1992 p.200 | remove (dead) back to last live point |
| IG2 | 13 | R-B | Back-up lamp output | IF1-7 -> Floor -> BP1-8 -> rear back-up lamps | Back-up SW B1 pin 1 | [90/92] 1992 p.132 | remove (dead) back to last live point |
| IG2 | 14 | BR | Water-temp gauge ground | Comb meter C12 (A) pin 5 | Ground EC (intake manifold) | 1993 p.207 | remove (dead) back to last live point |
| IG2 | 15 | B-R | ECU-IG 15A | J3 junction conn <- J/B1 1B-8 (15A ECU-IG) | Alternator IG (G2 A-2); cruise speed sensor pin 1 [90/92] | 1993 p.74; 1992 p.180 | KEEP 6 in pigtail, splice (alt IG feed per master) |
| IG2 | 16 | Y | Charge lamp (alternator L) | Cowl splice I5 -> comb meter C14 (C) pin 8 (+ Canada retract relay) | Alternator L (G2 A-1) | 1993 p.74 | ?? charge lamp: decide |
| IG2 | 17 | W-R | ABS TS | IF1-16 -> ABS ECU TS | DLC1 TS (16) | [90/92] 1992 p.192 | remove (dead) back to last live point |
| IG2 | 18 | B-Y | +B from EFI main relay | Cowl splice I6 -> ECU plug A pins 12 (+B) and 13 (+B1), circuit opening relay C9-2 | J/B2 2C-10 / Engine Wire splice I7 (VSVs) | 1993 p.80, 78 | remove (dead) back to last live point |
| IG2 | 19 | L-B | Fuel-pump + (FP check) | Cowl splice I1 -> IE2-19 (R/B5 FP relay/resistor) and IF1-15 -> BP1-12 -> fuel pump | DLC1 FP | 1993 p.79, 78 | remove (dead) back to last live point |
| IG2 | 20 | B | STA (cranking) | Cowl splice I6 -> ECU plug A pin 11 STA, C9-3, comb meter C13 (B) pin 10 | Engine Wire <- EB1-2 (starter relay out) | 1993 p.78, 206 | remove (dead) back to last live point |
