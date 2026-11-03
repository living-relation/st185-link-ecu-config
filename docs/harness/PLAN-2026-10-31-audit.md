# Wiring audit fixes (OPEN-ITEMS rows 170, 172, 173, 175) - hand-off plan

**Temporary plan (Dan 2026-10-31).** It holds the step-by-step for rows 170, 172, 173 and 175 so any agent can finish
them without asking Dan for context. Nothing may be added to this file after it is saved; progress goes in the
OPEN-ITEMS rows. Rows 171 and 174 closed 2026-11-01; their sections (2 and 5) were removed in the 2026-11-03 cleanup
(git history keeps them); section numbers stay as the rows cite them.
**Delete this file in the PR that closes the last of rows 170, 172, 173 and 175** (and drop its line from `docs/harness/README.md`).

Every decision below is already Dan's (DECISIONS B2, B6, B10, B14, B20, B22, B28; N83 = A). Do not re-ask them.

## 0. Before you start

1. `git switch main && git pull --ff-only` (B28), then branch. Read `AGENTS.md`, DECISIONS B1-B30 and the "Shields" and
   "Wire lists" sections, OPEN-ITEMS rows 170, 172, 173, 175.
2. Master edits follow `docs/harness/README.md` "Change the wiring"; shipping follows AGENTS.md and B28 (then pr-closeout). The master is
   `docs/harness/MASTER-wirelist.csv`; nothing else is hand-edited (drawings, wire lists, BOM regenerate).
3. Order and PRs: **PR 1** = rows 170 + 173 (master only, then regenerate); **PR 2** = row 172 (names);
   **PR 4** = row 175 (OEM splice reference; PR 3, row 174, is gone with the drawing PDFs, B6). Each PR: `python
   tools/check_all.py`, `python bench/check_parity.py`, `python .github/scripts/test_docs_gates.py` green; `Rows:` line;
   squash-merge when CI is green (Dan: merge your own PRs, don't wait); pull `main` after the merge.
4. Mil colour digits in the Spec 55 part numbers: 0 black, 2 red, 4 yellow, 5 green, 6 blue, 9 white.

## 1. Row 170 - 12 V sensor grounds off the ECU (B10; Dan B2 = one shared return)

The gearbox speed sensor (`VSS`) left this row (Dan 2026-11-01, #460 / #461; row 170): it is fed from ECU +8 V Out, so
its return `w_vss_gnd` on `SP-GNDOUT-B-ENG3` (with fuel pressure) is right and nothing below touches it. Flex fuel is
the only 12 V sensor return left.

Today: flex fuel (`FLEX`, Continental, +12 V from `SP-SW12-ENG`) pin B ->
splice `SP-GNDOUT-ENG2` (with `MAP` pin 1) -> `w_gnd_a_e_c44` -> bulkhead 18 -> `w_gnd_a_c44` -> `BUS-GNDOUT-A` cavity 6
-> ECU A24.

Target:

| Step | Change |
|---|---|
| a | No new splice: with the VSS gone the return has one leg, and a one-leg splice becomes a direct wire (as step e). The `SP-12V-RET-ENG` splice of the first draft is dropped. |
| b | Flex pin B leg (yellow core of `CAB-FLEX`) now ends on bulkhead **cavity 62** (spare size 20, sealing plug `114017` today), AB-engine, engine contact as the other size-20 engine cavities (`0462-201-1631`). |
| d | Cabin half: bulkhead 62 -> `POWER-NEG-BAR` (the POWER box battery-negative bar, M8 stud, glove box), loose `J1128-TXL-20-BLACK` (B20 cabin wire; it is a plain return, not a shielded circuit), cabin contact `0460-202-1631`, ring lug as the other 20 AWG NEG-bar wires (`w_csbg_ac`, `w_ac_cool_gnd`); length as `w_lamg_ac` (bulkhead to the NEG bar). |
| e | MAP keeps its ECU leg. `SP-GNDOUT-ENG2` has one device leg left: delete it; bulkhead 18 -> `MAP` pin 1 becomes a direct wire (keep the existing wire id and length to the old splice spot, plus the old leg length). `SP-GNDOUT-B-ENG3` stays (fuel pressure + VSS). |
| f | Text: bulkhead 18 / `BUS-GNDOUT-A` 6 read "Gnd MAP" (not "+ flex"). Bulkhead 62 reads "12 V sensor return (flex fuel)". Bulkhead 15 / `BUS-GNDOUT-B` 8 keep "fuel pressure, gearbox speed". |
| g | Remove cavity 62 from the spare / sealing-plug rows (both halves). |

Check: `check_wiring.py` E3 passes (no chassis ground), nothing powered from SW12 ends on `BUS-GNDOUT-*` or
`SP-GNDOUT-*`. Grep the master after the change: no `FLEX` row touches a `GNDOUT` id.

## 3. Row 173 - wire-end text and the shield splice distance

1. About 120 master ends carry the fuse path as their description (`... -> LOGIC SW12 5 A fuse`, `AMI BUS1 50 A fuse
   -> ...`). For each: the end's `*_desc` becomes what the wire does (its `*_note` already says it in most rows, e.g.
   firewall 67 = "+8 V to gearbox speed sensor", `K-FP` 86 = "Fuel pump relay coil +"), and the fuse path moves into the
   `*_note` as "Fed by: <fuse path>". Where the note is a location note instead ("LOGIC box (glove box) fuse SW1"),
   write the function from the circuit (B22: device, pin, signal).
2. N83 = A (Dan 2026-10-31): `SP-SHIELD-A` and `SP-SHIELD-B` sit **6 in (152 mm) behind** their ECU plug; replace "6 mm".
3. `VSS` connector name becomes "Gearbox speed sensor (VSS, Toyota 83181-20040)"; the long text moves to the note.

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
| `A18` (also called A15) | A/C amplifier (EWD A15, 1993) - fix the A18 / A15 clash to the 1993 code |
| `A32` / `A5` / `A4` / `A1` | Auto A/C amplifier (A32) / A/C pressure switch (A5) / A/C compressor (A4) / Outside air temp sensor (A1) |
| `IG2` / `IE1` | Cowl plug under the ECU (IG2) / Cowl plug, LH kick (IE1) |
| `JB1` / `JB1-1H` | Junction block 1, LH kick (J/B No.1) |
| `RB2` / `RB3` / `RB4` | Relay block 2, LH kick (R/B No.2) / Relay block 3 (R/B No.3) / Relay block 4, RH kick (R/B No.4) |
| `C11` / `C12` / `C17` / `Cruise` | Cluster plug C11 / Cluster plug C12 / Cruise clutch switch (C17) / Cruise stalk switch (C14) |
| `F7` / `F8` / `F9` / `F12` | LH / RH front turn lamp (F7 / F8) / Wiper motor (F9) / Fog switch (F12) |
| `R2` / `R3` / `R10` / `S9` / `W1` | LH / RH headlight lift motor (R2 / R3) / Dash dimmer (R10) / Brake light switch (S9) / Washer motor (W1) |
| `H1` / `H2` | LH / RH headlamp (H1 / H2) |
| `GND-ID` / `GND-IG` / `GND-EA` / `GND-EB` | Ground stud, LH kick (ID) / RH kick (IG) / RH fender (EA) / LH fender (EB) |
| all other `SP-*` (`SP-AC-PSW`, `SP-ACC12`, `SP-REV`, `SP-FUEL-LVL`, `SP-HL`, `SP-HR`, `SP-HZ`, `SP-AT-12V`, `SP-12V-SHK`, `SP-DEV`, `SP-IG`, `SP-HEAD-COIL`, `SP-HORN`, `SP-HL-HIGH`, `SP-HL-LOW`, `SP-RTR-*`, `SP-CLR`, `SP-LED-12V`, `SP-LED-GND`, `SP-PARK`, `SP-DOOR`, `SP-HOOD`, `SP-TRUNK`, `SP-CRUISE-LADDER`, `SP-TACH`, `SP-AC-SG`) | "<what> splice: <what it joins>", from the current name text with the id, fuse names and internal codes removed (e.g. `SP-ACC12` "B2-BUS2-8 ACC 10 A to k_acc 30 and 86" -> "A/C clutch relay feed splice: ACC fuse to relay pins 30 + 86") |
| cable screens `CAB-*` "cab_x screen (floats at the device end)" | "<circuit> cable screen (floats at the sensor)" |

Then: no name may contain a seat code (`B1-R4`, `B2-M5`, `B3-K1`, `B2-BUS2-8`), an internal id (`k_acc`, `w_*`) or a
bare part number as the whole name. Drawings and wire lists print the name; a wire label prints its end description
(row 173), with the wire id in small text only.

## 6. Row 175 - OEM splice reference, rebuilt and checked

Today `docs/harness/oem-splice-reference/build_xlsx.py` hard-codes 151 wire ids (55 no longer exist) and misses 36 of
the 82 master wires that tap or reuse a factory point; nothing runs it.

1. `build_xlsx.py`: drop the hard-coded list. Rows = every master wire with `oem_location` or `oem_method` set, grouped
   one sheet per factory connector or junction block (the OEM end's id: `JB1`, `IE1`, `IG2`, `RB2`, `RB4`, `C11`,
   `C12`, `H1`/`H2`, `R2`/`R3`, `F7`/`F8`/`F9`, `W1`, `A18`/`A32`/`A5`, `S9`, `C17`, cruise stalk, starter, ...).
   Columns as today (connector, pin, OEM colour, gauge, new colour, description, method, EWD page, wire id, flag),
   using the plain names from row 172.
2. Images: keep `make_images.py` crops (they read `C:\projects\active\st185-celica-repair-manual`); add a crop for each
   new sheet's connector face. A sheet without a crop says "no crop yet" in its header row (not a failure).
3. Add `--check` to `build_xlsx.py` (rebuild the table in memory, compare cell values with the committed xlsx, fail on
   any difference) and call it from `tools/check_all.py` next to `build_drawings.py --check`.
4. List the folder in `docs/harness/README.md` as generated ("No - re-run the generator").

Check: `python docs/harness/oem-splice-reference/build_xlsx.py --check` green; zero rows name a wire missing from the
master; every master factory-tap wire appears once.

## 7. Done when

- Rows 170, 172, 173 and 175 closed in OPEN-ITEMS (History line each), this file deleted with its README line, `main` pulled.
- Pairing check (run after PR 1): for every firewall cavity, both halves have the same circuit and colour, and a
  shielded engine half has a shielded cabin half.
