# Wiring audit fixes (OPEN-ITEMS rows 170-175) - hand-off plan

**Temporary plan (Dan 2026-10-31).** It holds the step-by-step for rows 170-175 so any agent can finish them without
asking Dan for context. Nothing may be added to this file after it is saved; progress goes in the OPEN-ITEMS rows.
**Delete this file in the PR that closes the last of rows 170-175** (and drop its line from `docs/harness/README.md`).

Every decision below is already Dan's (DECISIONS B2, B6, B10, B14, B20, B22, B28; N83 = A). Do not re-ask them.

## 0. Before you start

1. `git switch main && git pull --ff-only` (B28), then branch. Read `AGENTS.md`, DECISIONS B1-B30 and the "Shields" and
   "Wire lists" sections, OPEN-ITEMS rows 170-175.
2. Master edits follow the `st185-change-sot` skill; shipping follows `st185-ship-change` (B28). The master is
   `docs/harness/MASTER-wirelist.csv`; nothing else is hand-edited (drawings, wire lists, BOM regenerate).
3. Order and PRs: **PR 1** = rows 170 + 171 + 173 (master only, then regenerate); **PR 2** = row 172 (names);
   **PR 3** = row 174 (generator: per-device pages); **PR 4** = row 175 (OEM splice reference). Each PR: `python
   tools/check_all.py`, `python bench/check_parity.py`, `python .github/scripts/test_docs_gates.py` green; `Rows:` line;
   squash-merge when CI is green (Dan: merge your own PRs, don't wait); pull `main` after the merge.
4. Mil colour digits in the Spec 55 part numbers: 0 black, 2 red, 4 yellow, 5 green, 6 blue, 9 white.

## 1. Row 170 - 12 V sensor grounds off the ECU (B10; Dan B2 = one shared return)

Today: gearbox speed sensor (`VSS`, Toyota 83181-20040, fed from the LOGIC SW12 fuse) pin 2 -> `w_vss_gnd` (yellow core
of `CAB-VSS`) -> splice `SP-GNDOUT-B-ENG3` (with fuel pressure `FUEL-P` pin 1) -> `w_gnd_b_e_c21` -> bulkhead 15 ->
`w_gnd_b_c21` -> `BUS-GNDOUT-B` cavity 8 -> ECU B22. Flex fuel (`FLEX`, Continental, +12 V from `SP-SW12-ENG`) pin B ->
splice `SP-GNDOUT-ENG2` (with `MAP` pin 1) -> `w_gnd_a_e_c44` -> bulkhead 18 -> `w_gnd_a_c44` -> `BUS-GNDOUT-A` cavity 6
-> ECU A24.

Target:

| Step | Change |
|---|---|
| a | New engine splice `SP-12V-RET-ENG` "12 V sensor return splice: gearbox speed + flex fuel", placed where the VSS and flex legs part on the Route 16 tree (the generator places a splice where its legs part). |
| b | `w_vss_gnd` (VSS pin 2, yellow core, `CAB-VSS`) now ends on `SP-12V-RET-ENG`. Flex pin B leg (yellow core of `CAB-FLEX`) now ends on `SP-12V-RET-ENG`. |
| c | New trunk wire `SP-12V-RET-ENG` -> bulkhead **cavity 62** (spare size 20, sealing plug `114017` today), AB-engine, `M22759/16-20-0` black 20 AWG, engine contact as the other size-20 engine cavities (`0462-201-1631`). |
| d | Cabin half: bulkhead 62 -> `POWER-NEG-BAR` (the POWER box battery-negative bar, M8 stud, glove box), loose `J1128-TXL-20-BLACK` (B20 cabin wire; it is a plain return, not a shielded circuit), cabin contact `0460-202-1631`, ring lug as the other 20 AWG NEG-bar wires (`w_csbg_ac`, `w_ac_cool_gnd`); length as `w_lamg_ac` (bulkhead to the NEG bar). |
| e | Fuel pressure and MAP keep their ECU legs. `SP-GNDOUT-B-ENG3` and `SP-GNDOUT-ENG2` each have one device leg left: delete both splices; bulkhead 15 -> `FUEL-P` pin 1 and bulkhead 18 -> `MAP` pin 1 become direct wires (keep the existing wire ids and lengths to the old splice spot, plus the old leg length). |
| f | Text: bulkhead 15 and `BUS-GNDOUT-B` cavity 8 read "Gnd fuel pressure" (not "+ VSS"); bulkhead 18 / `BUS-GNDOUT-A` 6 read "Gnd MAP" (not "+ flex"). Bulkhead 62 reads "12 V sensor return (gearbox speed + flex fuel)". |
| g | Remove cavity 62 from the spare / sealing-plug rows (both halves). |

Check: `check_wiring.py` E3 passes (no chassis ground), nothing powered from SW12 ends on `BUS-GNDOUT-*` or
`SP-GNDOUT-*`. Grep the master after the change: no `VSS` or `FLEX` row touches a `GNDOUT` id.

## 2. Row 171 - same shielded cable both sides of the firewall (B14)

Each circuit below is Spec 55 shielded in AB-engine but loose TXL in AB-cabin. In AB-cabin, replace the loose wires
between the bulkhead and their cabin ends with **one cable of the same part number**, cores in the **same colours as
the engine half**, ident bands copied from the engine half. Cabin ends do not move (the cores fan out at the ECU
splice point to the same ECU pins, bus cavities and splices). The cabin drain wire (`w_shc_*`) becomes that cable's
screen drain, still to the same splice. Model the rows on the cabin cables that already exist (`CAB-APS1`,
`CAB-FSPUR-FR-AC`, `CAB-CANBH-BC`): `cable` + `cable_pn` set, `wire_pn` blank on cores, a `cable screen` row for the
screen. Cable length = the longest cabin core run it replaces. Tefzel / Spec 55 stays (B20 already lists Spec 55
cables); the TXL rule does not apply to these cables. A core with no cabin job is cut back and sealed under heat
shrink (pin `NC`, like Wire lists rule 7).

| Circuit | Cable (same PN both sides) | Bulkhead cavity -> cabin end (core colour) | Cabin wires replaced |
|---|---|---|---|
| Crank | `55A1821-20-6/9-9` | 74 sig -> ECU-A 8 (white); 75 gnd -> BUS-GNDOUT-A 3 (blue); 76 screen -> SP-SHIELD-A | `w200_c`, `w_gnd_a_c41`, `w_shc_crank` |
| Cam | `55A1831-20-2/4/6-9` | 63 +8 V -> SP-8V (red); 64 sig -> SP-CAM (blue); 65 gnd -> BUS-GNDOUT-A 4 (yellow); 66 screen -> SP-SHIELD-A | `w_rail_sp_8v_c`, `w_cam_sig_c`, `w_gnd_a_c42`, `w_shc_cam` |
| Knock | `55A1821-20-6/9-9` | 71 sig -> ECU-B 9 (blue); 72 (-) -> BUS-GNDOUT-B 6 (white); 73 screen -> SP-SHIELD-B | `w205_c`, `w12_c`, `w_shc_knock1` |
| Turbo speed | `55A1831-20-2/4/6-9` | 52 +5 V -> BUS-5V 4 (red); 53 sig -> ECU-A 30 (blue); 56 gnd -> BUS-GNDOUT-A 5 (yellow); 57 screen -> SP-SHIELD-A | `w_5v_a_c40`, `w16_c`, `w_gnd_a_c43`, `w_shc_turbo` |
| Gearbox speed (VSS) | `55A1831-20-2/4/6-9` | 67 +12 V -> SP-SW12 (red); 68 sig -> ECU-B 29 (blue); yellow `NC` sealed (the return crosses on cavity 62 as a loose wire, row 170); 69 screen -> SP-SHIELD-B | `w_rail_sw12_b_c_ac`, `w_vss_sig_c`, `w_shc_vss` |
| Flex fuel | `55A1831-20-2/4/6-9` | 31 sig -> ECU-A 31 (blue); red and yellow `NC` sealed (flex +12 V and its return do not cross here); 32 screen -> SP-SHIELD-A | `w48_c`, `w_shc_flex` |
| Throttle sensor | `55A1841-20-2/4/5/6-9` | 41 +5 V -> BUS-5V 2 (red); 42 TPS1 -> ECU-A 22 (green); 44 TPS2 -> ECU-A 33 (blue); yellow `NC` sealed (sensor ground returns through bulkhead 34); 47 screen -> SP-SHIELD-A | `w_rail_sp_5v_c`, `w128_c`, `w129_c`, `w_shc_etbs` |
| Throttle motor | `55A1821-18-2/0-9` | 45 motor + -> ECU-B 18 (red); 46 motor - -> ECU-B 26 (black); 50 screen -> SP-SHIELD-B | `w124_c`, `w215_c`, `w_shc_etbm` |

Check: the S1-S3 shield checks in `check_wiring.py` pass; every bulkhead cavity above has the same colour and bands on
both halves (re-run the pairing check in section 7).

## 3. Row 173 - wire-end text and the shield splice distance

1. About 120 master ends carry the fuse path as their description (`... -> LOGIC SW12 5 A fuse`, `AMI BUS1 50 A fuse
   -> ...`). For each: the end's `*_desc` becomes what the wire does (its `*_note` already says it in most rows, e.g.
   firewall 67 = "+12 V gearbox speed", `K-FP` 86 = "Fuel pump relay coil +"), and the fuse path moves into the
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
| `SP-12V-RET-ENG` (row 170) | 12 V sensor return splice: gearbox speed + flex fuel |
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

## 5. Row 174 - drawings, one page per device per harness (B2 / B6 exception)

Change `docs/harness/tools/build_drawings.py` schematic grouping; layout pages (routes) and the pinout set stay.

1. Per harness, one schematic page per **field device** (sensor, actuator, OEM device, relay, inline plug pair): the
   device's connector and every wire of that harness that serves it, followed through splices and the firewall plug to
   its far end in that harness (ECU pin, bus cavity, fuse box, ground bar). VSS: one page in AB-engine (sensor, its
   cable, `SP-12V-RET-ENG`, firewall 62 / 67 / 68 / 69) and one in AB-cabin (firewall 62 / 67 / 68 / 69 to ECU-B 29,
   `SP-SW12`, `POWER-NEG-BAR`, `SP-SHIELD-B`).
2. Shared trunks (bus feeds, `SP-SHIELD-*` trunks, ECU power ground, CAN trunk) go on one "Buses and splices" page per
   harness; a device page draws its own leg to the bus or splice and labels it "to <bus>, page N".
3. The ECU, fuse boxes and firewall plug never get a device page; they appear as far ends.
4. A device too big for one page (switch board, alarm) continues on the next page; title "part n of m" counts that
   device's pages only (fixes today's "part 5 of 4" and the duplicate / mismatched counters).
5. Keep: one line colour per wire, revision block, `DG` initials, title block, read-back (`--check`) of every wire end.
6. Update the `drawings/` line in `docs/harness/README.md` (it still describes the grouped-section pages).

Check: every master wire end appears on exactly one schematic page per harness (read-back); VSS appears on exactly two
schematic pages (AB-engine, AB-cabin); `build_drawings.py --check` green. Bump the revision letter with a rev-log line.

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
5. Working memory (Dan's PC): `%USERPROFILE%\.claude\working-memory\st185-link-ecu-config\project_oem_splice_reference.md`
   says the reference is "local, not committed" - it is committed; correct that note and its INDEX line.

Check: `python docs/harness/oem-splice-reference/build_xlsx.py --check` green; zero rows name a wire missing from the
master; every master factory-tap wire appears once.

## 7. Done when

- Rows 170-175 closed in OPEN-ITEMS (History line each), this file deleted with its README line, `main` pulled.
- Pairing check (run after PR 1): for every firewall cavity, both halves have the same circuit, colour and bands, and a
  shielded engine half has a shielded cabin half.
