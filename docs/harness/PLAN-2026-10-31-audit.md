# Wiring audit fixes (OPEN-ITEMS row 172) - hand-off plan

**Temporary plan (Dan 2026-10-31).** It holds the step-by-step for row 172 so any agent can finish it without asking
Dan for context. Nothing may be added to this file after it is saved; progress goes in the OPEN-ITEMS row. Rows 170,
171, 173, 174 and 175 are closed and their sections (1-3, 5 and 6) were removed (git history keeps them); section
numbers stay as the rows cite them.
**Delete this file in the PR that closes row 172** (and drop its line from `docs/harness/README.md`).

Every decision below is already Dan's (DECISIONS B2, B6, B22, B28). Do not re-ask them.

## 0. Before you start

1. `git switch main && git pull --ff-only` (B28), then branch. Read `AGENTS.md`, DECISIONS B1-B30 and the "End labels
   and names (B22)" and "Wire lists" sections, OPEN-ITEMS row 172.
2. Master edits follow `docs/harness/README.md` "Change the wiring"; shipping follows AGENTS.md and B28 (then pr-closeout). The master is
   `docs/harness/MASTER-wirelist.csv`; nothing else is hand-edited (drawings, wire lists, BOM regenerate).
3. One PR for row 172 (names): `python tools/check_all.py`, `python bench/check_parity.py`, `python
   .github/scripts/test_docs_gates.py` green; `Rows:` line; squash-merge when CI is green; pull `main` after the merge.

## 4. Row 172 - plain names (B22): the `*_name` columns

Rule: plain words first, any code in parentheses after. IDs (`wire_id`, `*_id`) stay as keys; drawings and wire lists
show the name. Apply this map to every row's `from_name` / `to_name` for the id; variants of one id become one name.

| id | plain name |
|---|---|
| `DRB102-CABIN` / `DRB102-ENGINE` | Firewall plug, cabin side (DRB102) / Firewall plug, engine side (DRB102) |
| any "BH-A pin N" / "BH-B pin N" text | firewall pin N |
| `BUS-5V` / `BUS-5V-2` | ECU +5 V sensor supply bus 1 / 2 (DT 12-way / 8-way) |
| `BUS-GNDOUT-A` / `-B` | ECU sensor ground bus A, ECU pin A24 / bus B, ECU pin B22 (DT 12-way) |
| `BUS-SW12` | Switched +12 V bus (glove box, DT 12-way) |
| `SP-SW12` / `SP-SW12-ENG` | Switched +12 V splice, at the ECU plugs / engine bay (boost solenoid + flex fuel) |
| `SP-8V` / `SP-CAM` | Cam sensor +8 V splice / Cam signal + pull-up splice |
| `SP-A5` / `SP-GND-ECU` | ECU main feed splice (SW12 + IG2 wake) / ECU power ground splice |
| `SP-GNDOUT-ENG` | Sensor ground splice: coolant temp + intake temp + throttle (engine bay) |
| `SP-GNDOUT-B-ENG` / `-ENG2` | Sensor ground splice: oil temp + charge temp / oil pressure + coolant pressure |
| `SP-SHIELD-A` / `-B` | Shield drain splice, 6 in behind ECU plug A / B |
| `SP-SHIELD-A-APS` / `-A-WSF` / `-B-WSR` | Shield drain splice at the pedal / front wheel-speed plug / rear wheel-speed plug |
| `SP-WS-F-SHIELD` / `SP-WS-R-SHIELD` | Front / rear wheel-speed sensor screen join |
| `SP-INJ-ENG` / `SP-COP-ENG` | Injector +12 V splice / Coil +12 V splice |
| `SP-CHASSIS-ENG` | Coil ground splice (to the POWER box ground bar) |
| `SP-LAM12-B` / `SP-LAMG-B` | Lambda +12 V splice / Lambda ground splice |
| `SP-CANH` / `SP-CANL` / `-LAM` | CAN high / low join, dash / at the Lambda |
| `SP-CAN-SH-BH` / `-CLU` / `-CSB` / `-RD` | CAN shield join: firewall / cluster / switch board / RealDash Pi |
| `SP-CSB-GND` | Switch board ground splice |
| `IX-WS-F-S` / `-P`, `IX-WS-R-S` / `-P` | Front / rear wheel-speed inline plug (socket half / pin half) |
| `IX-FUEL-S` / `IX-FUEL-P` | Fuel sender inline plug (socket half / pin half) |
| `K-FP` | Fuel pump relay (trunk relay block, K1) |
| `K-EFI` / `K-FAN` / `K-FAN2` | EFI main relay / Radiator fan relay / Condenser fan relay (power box R2 / R4 / R5) |
| `K-HL` / `K-HR` / `K-HORN` / `K-ETB` / `K-ACC` / `K-EPS-EN` | Headlight LH / Headlight RH / Horn / Throttle power / A/C clutch / Steering pump enable relay (logic box M1 / M2 / M3 / M4 / M5 / M6) |
| `K-EPS` | Steering pump relay (beside the power box) |
| `LOGIC` / `POWER` | Logic fuse box (glove box) / Power fuse box (glove box) |
| `POWER-STUDS` / `POWER-NEG-BAR` | Power box studs / Power box ground bar (M8) |
| `BATT-RELAY-BLOCK` | Trunk relay block |
| `REV-SW` | Reverse light switch (EWD B1) |
| `VSS` | Gearbox speed sensor (VSS, Toyota 83181-20040) |
| `ECU-C` | ECU tuning port |
| `OPTO-8` | Optocoupler board, 8 channel |
| `T-CLUSTER-PWR` / `T-REALDASH-PWR` | Cluster power input / RealDash Pi power input |
| `D-IG2-WAKE` | IG2 wake diode |
| `R-CRUISE` / `R-FUELLVL` / `R-CAM-PULLUP` / `R-LOCK` | Cruise switch resistor / Fuel level pull-up resistor / Cam pull-up resistor / Lock-sensor resistor |
| `ALT-PLUG` | Alternator plug (round 3-pin) |
| `RADLOK-POS-CAB` / `-NEG-CAB` / `-POS-ENG` / `-NEG-ENG` | Battery + / - firewall post, cabin side / engine side (RADLOK) |
| `MRS-A` / `MRS-B` / `MRS-C` | Steering pump plug A / B / C (MR-S EHPS) |
| `A32` / `A5` / `A4` / `A1` | Auto A/C amplifier (A32) / A/C pressure switch (A5) / A/C compressor (A4) / Outside air temp sensor (A1) |
| `IG2` / `IE1` | Cowl plug under the ECU (IG2) / Cowl plug, LH kick (IE1) |
| `JB1` / `JB1-1H` | Junction block 1, LH kick (J/B No.1) |
| `RB2` / `RB3` / `RB4` | Relay block 2, LH kick (R/B No.2) / Relay block 3 (R/B No.3) / Relay block 4, RH kick (R/B No.4) |
| `C11` / `C12` / `C17` / `C16` | Cluster plug C11 / Cluster plug C12 / Cruise clutch switch (C17) / Combination switch plug, cruise switch (C16 (B)) |
| `F7` / `F8` / `F9` / `F12` | LH / RH front turn lamp (F7 / F8) / Wiper motor (F9) / Fog switch (F12) |
| `R2` / `R3` / `R10` / `S9` / `W1` | LH / RH headlight lift motor (R2 / R3) / Dash dimmer (R10) / Brake light switch (S9) / Washer motor (W1) |
| `H1` / `H2` | LH / RH headlamp (H1 / H2) |
| `GND-ID` / `GND-IG` / `GND-EA` / `GND-EB` | Ground stud, LH kick (ID) / RH kick (IG) / RH fender (EA) / LH fender (EB) |
| all other `SP-*` (`SP-AC-PSW`, `SP-ACC12`, `SP-REV`, `SP-FUEL-LVL`, `SP-HL`, `SP-HR`, `SP-HZ`, `SP-AT-12V`, `SP-12V-SHK`, `SP-DEV`, `SP-IG`, `SP-HEAD-COIL`, `SP-HORN`, `SP-HL-HIGH`, `SP-HL-LOW`, `SP-RTR-*`, `SP-CLR`, `SP-LED-12V`, `SP-LED-GND`, `SP-PARK`, `SP-DOOR`, `SP-HOOD`, `SP-TRUNK`, `SP-CRUISE-LADDER`, `SP-TACH`, `SP-AC-SG`) | "<what> splice: <what it joins>", from the current name text with the id, fuse names and internal codes removed (e.g. `SP-ACC12` "B2-BUS2-8 ACC 10 A to k_acc 30 and 86" -> "A/C clutch relay feed splice: ACC fuse to relay pins 30 + 86") |
| cable screens `CAB-*` "cab_x screen (floats at the device end)" | "<circuit> cable screen (floats at the sensor)" |

Then: no name may contain a seat code (`B1-R4`, `B2-M5`, `B3-K1`, `B2-BUS2-8`), an internal id (`k_acc`, `w_*`) or a
bare part number as the whole name. Drawings and wire lists print the name; a wire label prints its end description
(row 173), with the wire id in small text only.

## 7. Done when

- Row 172 closed in OPEN-ITEMS (History line), this file deleted with its README line, `main` pulled.
