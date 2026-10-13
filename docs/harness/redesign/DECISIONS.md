# ST185 Harness Redesign — Decision Record

**Date:** 2026-09-27  
**Repo:** `st185-link-ecu-config`  
**Status:** Frozen decision record. Merges the now-removed `output/HARNESS-REDESIGN-PLAN.md` and
`output/HARNESS-CHECKER-AUDIT.md` (superseded and deleted 2026-10-10).
The 2026-09-27 phased implementation plan is complete (deleted 2026-10-11); open work is in
`docs/OPEN-ITEMS.md`.

## Binding rules from Daniel

**This section is the one home for every rule Daniel has set** (consolidated 2026-10-12 from his
Dispatch notes; most of these were never written into the repo before, which is how stale docs
survived). One dated line per rule, newest ruling wins. `AGENTS.md`, the per-tool rule files
(`.claude/rules/`, `.cursor/rules/`), `docs/harness/README.md`, `sot/README.md` and the global
`st185-*` / `harness-design` skills point here and do not restate these. The procedures that apply
them live in `docs/RECONCILIATION-RULES.md` (how to reconcile, the surface table, Rule 3 detail)
and `docs/SHIELD-RULES.md` (shield inventory and build detail); where either disagrees with a line
here, this section wins. The `Sn` rows further down are the dated decision record behind many
of these lines. Gates in brackets are the scripts in `docs/harness/` that check the rule.

### Harness file split

- **R1** (2026-09-27/28) The ECU connector letter decides loom and bulkhead: connector A -> `ST185-A-cabin` -> bulkhead A -> `ST185-A-engine`; B the same. Exactly four ECU files. A pin's letter is its `conn` column in `sot/channels.csv`. [`validate_bulkhead_letter.py`; detail: `docs/RECONCILIATION-RULES.md` Rule 3]
- **R2** (2026-09-28) Non-ECU wires (fused 12V, relay outputs, grounds) follow the bulkhead of the ECU signal of the device they serve. Harness files are never merged or duplicated. [`validate_bulkhead_letter.py`]
- **R3** (2026-09-28) A wire that runs between two harness files is drawn broken off in BOTH files, each end a noted `Loose` terminal naming the other file; where that cannot resolve, an inline connector pair where the wire leaves one file and enters the other, noted in both. Registered in `docs/harness/interfaces.json` "breaks" / "interfaces". [`validate_bulkhead_letter.py` L6/L7, `validate_interfaces.py`]
- **R4** (2026-09-28, final wording) +5V (A32) is spliced at ECU A in the cabin and feeds both letters; its B leg leaves A-cabin broken off ("see other diagram"). Sensor ground is NOT shared across letters: loom A returns to A24, loom B to B22, no A24-B22 tie. *Conflict note: the 09-27 split note said "5V + sensor ground splice at ECU A"; the 09-28 ruling (ground back onto B22, `IX_B_RAIL` +5V only) is later and wins.* [crossover (a)]
- **R5** (2026-09-28) ETB: the B18/B26 motor wires leave `ST185-B-engine` as a broken-off spur right after bulkhead B; `ST185-A-engine` shows them coming in and joining the A trunk under sheathing after bulkhead A, to the throttle body drawn there. All e-throttle BODY wires are engine-bay wiring. [crossover (b)]
- **R6** (2026-09-28, pedal form superseded 2026-10-11) APS pedal: channel 1 on A14, channel 2 on B33. All e-throttle PEDAL wires stay in the cabin. *Conflict note: 09-28 said the pedal joins broken-off A and B spurs at one Deutsch pair (`IX_APS`); 2026-10-11 "pedal is one cable in A-cabin" wins - the BRZ pedal connector is drawn on `ST185-A-cabin`, only the B33 leg breaks off to `ST185-B-cabin`.* [crossover (c)]
- **R7** (2026-09-28) No center-cluster harness is drawn in this repo (the cluster repo owns its interior wiring); the cluster appears only as a CAN node with power and ground. `ST185-ClusterLED` and `ST185-AntiTheft` stay here. `CabinAccessory` was dropped.
- **R8** (2026-09-29) If bulkhead A or B runs out of pins or needs bigger contacts, a different connector may replace it or a second one may sit beside it, only as a complete compatible matching set for both sides (housings, inserts, contacts per gauge, seals, plugs, wedgelocks, gasket/backshell), every part number from the maker's datasheet.
- **R9** (2026-10-03) A bulkhead pin is shared only by the same signal class and net: same rail, same ground, shield drain, CAN L, CAN H. If the combined AWG will not fit the contact, one short pigtail on the pin with a splice behind it. Never two different circuits on one cavity. [`audit_bh_collisions.py`, `audit_cavity_parts.py` K3]
- **R10** (2026-10-12, S10/S11) A connector shared by more than one file is drawn WHOLE in every file: real part, real cavity count, same designations; the other file's cavities N/C with a note "see ST185-<other>". The DRB102 is ONE 102-position connector; A and B are only our names for its sections. [`audit_shared_connectors.py`, `audit_mating.py` M8]

### OEM vehicle wiring

- **R11** (2026-10-10, repeated 2026-10-12, S15) NO OEM engine-bay wire or connector is reused. Every engine-bay run (horn, lights, fans, fender leads included) is new wire in project colours; device-end connectors stay as recorded (OEM device plugs where chosen, DT where Daniel said DT). Cabin J/B and dash wiring reuse is unchanged - flying leads spliced into factory cabin leads stay normal. [`audit_dan_rules.py` D1]
- **R12** (2026-09-29, 2026-10-12, S15) OEM boxes kept: only the cabin J/Bs (J/B No.1, No.3) and under-dash wiring. ALL OEM relay blocks (R/B No.2-5) and EVERY engine-bay box (J/B No.2, R/B No.5, F11 fusible-link box) are removed; nothing lands on them, no dummy headers. [`validate_oem_endpoints.py` E4]
- **R13** (2026-09-29) Deleted OEM parts, never a source for a circuit: circuit opening relay, injector resistor pack, fuel pump resistor and relay, A15 A/C amplifier, J/B No.2, R/B No.5, F11, combination meter. Owner of the deleted list: `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §5.6.
- **R14** (2026-09-29) No airbag/SRS, no ABS ECU, no cruise ECU. The combination meter and all its plugs and wires are gone; the charge lamp moves to `ST185-ClusterLED`. *Confirm note: `ST185-ClusterLED` taps the dash-harness side of C11/C12 at the meter as cabin flying leads - read here as the harness-side leads, not the meter's own plugs.*
- **R15** (2026-09-29) All fuses and relays live in the cabin (the trunk battery area is fine for the main battery fuse). The alternator output is protected by a fusible link, inline fuse or breaker at the battery / on the + cable near the fuse box - never at the starter. [B5]
- **R16** (2026-10-04) Use the 1993 model year wherever EWD years conflict; the updated ST185 repair manual (`C:\projects\active\st185-celica-repair-manual`) is the primary reference. Older EWD page citations (1990 book, 1992 EWD132U) are a reading aid only.
- **R17** (2026-10-04) Alternator B+ and the OEM 1993 round 3-pin alternator plug run in `ST185-HeavyDC`. *Applied 2026-10-12 as Daniel's decision: the bulkhead-B IG/L/S route (old §10/36, OPEN-ITEMS row 54 step 6) is dropped. The B+ is drawn (`t_alt_b`, 2 AWG to the starter B+). The 3-pin plug is not drawn yet: its part number, how its three wires cross the firewall and where IG and S are fed are questions for Daniel (OPEN-ITEMS G1-1 to G1-3).*
- **R18** (2026-10-11) Cabin fuse box = Option B: Eaton RFRM `15401-1-2-1-0A` + 3x MTA modules + Eaton Bussmann LMI (loose LMI1 modules in two stacks, S14). The MTA module part number is under review (`0301491` not found). No battery box in the plan. Slot map: `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §8.1.
- **R19** (2026-09-28) Battery is AGM. Kill: Longacre 4-terminal switch in the trunk plus the G4X Stop Switch input. [B6]
- **R20** (2026-09-28) Raspberry Pi: on with the car, off when the car is off. NO hold relay or power-hold circuit. [B7]
- **R21** (2026-10-04, §26.1) The ECU controls start (`k_str`, Aux 8 A26); no clutch-start interlock; the clutch switch is a CSB3 input.
- **R22** (2026-10-04, §18) MR-S EHPS pump: A1 = battery 12V via a 40-50 A continuous-duty relay in the cabin plus fuse; A2 = ground; that relay's coil+ = 12V ignition, coil- switched by pump pin B5; C1 = 12V ignition via 7.5 A; B2 = road-speed pulse (Link Aux 7, A27). `k_eps_en` micro relay on Link Ign 6 (B12), on above ~400 rpm with a 1-2 s off-delay. *Applied 2026-10-12: `sot/channels.csv` (b12, `k_eps` c2 / c3, new `k_eps_en` c1-c4, `mrs_eps` b5) and the drawings follow this rule; the B5 wire crosses bulkhead A c27 (R2: the pump's ECU signal A27 is on A); `k_eps_en` sits in an RFRM micro position on EPSEN 7.5 A, its 87 feeding the MTA-2 MRS 7.5 A fuse.*
- **R23** (2026-10-04, §3) A/C: keep the auto amplifier; A15 removed; the Link drives the clutch relay `k_acc` on Ign 8 (B10) with the dual pressure switch in series; A/C button V-G -> An Volt 10 (B31); evaporator thermistor (1.5 kOhm at 25 C) -> An Volt 11 (B32). Heater water sensor A25 stays.
- **R24** (2026-09-28, B1) The Link CAN-Lambda stays in the bay; its CAN H/L, 12V and GND cross on bulkhead B, shielded the whole run.
- **R25** (2026-09-26) Relays are active-low: the ECU sinks coil- (85); coil+ on 86. No external flyback diodes - the G4X outputs are internally suppressed and the 1ZZ coils have theirs built in. *Citation still to add: the exact PCLink G4X Help page (`sot/channels.csv` b12 cites "PCLink G4X Help 'Auxiliary Output Wiring'").*
- **R26** (2026-10-04) Link G4X documentation only for pins and wiring - never G4 or G4+ pages; plug-in ECU manuals only for theory and features.

### Shields and drains

- **R27** (2026-10-03) A shielded device uses Raychem shielded cable, never loose hookup wire. The shield runs unbroken from the ECU to the device and terminates at an ECU shield-ground pin (A7 / B17), NOT at the device end; it floats at the sensor. *Wording note: the older "or at the destination device" (settled rule 5, SHIELD-RULES absolute rule 2) covers only R31's VRC IN pin.* [`audit_shields.py`, `audit_pin_names.py`]
- **R28** (2026-10-03) Shield list: crank, cam, knock, wheel speed x4 (sensor -> VRC), VRC outputs, turbo speed, flex fuel, gearbox VSS, ETB, APS pedal, the CAN-Lambda run, ALL CAN bus runs (the CAN pair; +12V and ground stay plain). Injectors and coils: NO shields. Owner of the per-device flag: `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`.
- **R29** (2026-10-12, S12/S9) No solder sleeves are drawn. Every shielded cable is drawn as if it had a drain wire: the shield goes straight to its pin. Only where 2+ shields share one pin: ONE splice (`GENERIC SOLDER SPLICE`, located on the pin's connector) and one drain wire to the pin. Never an extra splice, never a splice per cable, never a chain. [`validate_wheel_speed.py` W3, `audit_dan_rules.py` D2]
- **R30** (2026-10-12, S9) Drain T-splice is the BUILD method, not drawn: one drain crimped into the pin, the other soldered onto it about 0.25 in (6 mm) behind the connector rear (about 0.25 in of insulation cut away). Drain gauge never scales with the shield count. The same for every CAN node drain onto the trunk drain.
- **R31** (2026-10-03, 2026-10-12, S8) VRC: the L and R input shields terminate at the VRC IN connector pin 3 (one splice, R29); the VRC output cable is shielded and terminates at the VRC OUT connector pin 5 AND reaches an ECU shield pin. The VRC PCB is isolated from the enclosure and nothing bonds to the case; drain continuity inside the box is by wire, pin to pin. *Supersedes settled rule 6 ("enclosure may be part of the shield path").*
- **R32** (2026-10-12, #110) Drain wire = `M22759/16-20-06`, 20 AWG black/blue Tefzel, unique to drains; gates find a drain by its part, never by colour. [`lint_v09.py`]
- **R33** (2026-10-04, 2026-10-12, S8d) No connector is chosen for "shieldability"; never rely on a connector shell for screen continuity; every drain lands on a normal pin. [`lint_v09.py`, `audit_shields.py` R3]
- **R34** (2026-10-12, S8) VRC drawing: exactly two plugs per VRC harness, both CNLINKO `LP-16-J05PE-02-001` (5-pin, unshielded, solder, 22-20 AWG; S16): one shared IN plug (the L and R legs run separately and meet only at it) and one OUT plug; IN and OUT drawn as separate pieces with no link; the VRC box is not drawn. The box takes the `LP-16-C05SX-02-101` rear-nut panel socket (S16). [`validate_wheel_speed.py` W8/W9]

### Wire and parts

- **R35** (2026-10-12, #108) Wire = `M22759/16-<AWG>-<MIL colour code>` Tefzel; no generic `EW-1C*` wire parts. Battery cable `BC-*` stays. *Supersedes plan §6.24 "wire and cable are generic in every BOM".* [`audit_dan_rules.py` D3, `part_desc.py`]
- **R36** (2026-09-28) Power and signal splices are sized by the combined gauge of the wires they join (Wire Barn Combined Wire Gauge Calculator: 4 x 20 AWG = 14 AWG). Not for drains (R30). The harness.design per-wire splice warning is a known false alarm. [`audit_cavity_parts.py` K3]
- **R37** (2026-10-11, S6) Heavy cable sizes are calculated from amps, run length and temperature; never asked.
- **R38** (2026-10-10, suppliers added 2026-10-12) Parts order: Daniel's on-hand TE list first (`docs/sourcing/te-on-hand-bom.csv`; never ask for counts) -> TE (prefer free samples) -> Daniel's approved suppliers (`docs/sourcing/README.md` "Approved suppliers": ProWire USA, Find Pigtails, KSV Looms, Connector Experts, Plimpton Innovations, PT Motorsport, CrimpZone, B Motorsports, Corsa Technic) -> others only with a stated reason. Never guess a part number: an unverified part is `TBD` plus the reason; cite the datasheet. Procedure: `docs/sourcing/README.md`, skill `st185-pick-parts`.
- **R39** (2026-10-12, #111) The part library `docs/harness/rebuild/ST185.harnesslib` is the master: change the library FIRST, then the drawings, in the same PR; any difference between a drawing's part and the library fails. Cloud 5LO8 and Daniel's app library are synced from it. [`check_harnesslib.py`]
- **R40** (2026-10-12) Look up maker drawings yourself for dimensions; do not ask Daniel.

### Drawing conventions

- **R41** (2026-10-12) The harness.design docs and tutorials (https://docs.harness.design) are the authority for drawing conventions; if one of Daniel's rules conflicts with them, flag it in `docs/OPEN-ITEMS.md` with both sides and the doc link and ask - never pick silently.
- **R42** (2026-10-12) Schematic: any direction that reads best (often centre-out). Layout: MUST read left to right along the physical route. [`audit_drawing_rules.py` L1]
- **R43** (2026-10-12) Signals auto-propagate across a net; where a name changes across a device or plug, set each side explicitly with `propagate: false`. One propagating signal per net; terminals never propagate. [`audit_drawing_rules.py` S1-S3]
- **R44** (2026-10-12, S13) CLEAN drawings: only parts Daniel asked for; no added coverings, boots, sleeves, seals, backshells or accessories; nothing labelled "not used"; no extra splices; unreferenced part definitions removed. The model is Daniel's own `ST185-WheelSpeed-Rear.harness`. Daniel's saved file wins over an agent's version: change the gate, not his drawing. [`audit_parts_layout.py` P1, `audit_dan_rules.py` D4]
- **R45** (2026-10-04) `.harness` files are never a source of truth; they are built and checked against the SoT chain (`sot/channels.csv` -> `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` -> `XTREMEX-IO-TABLE.html` -> the drawings). New pin facts go into `sot/channels.csv` first (2026-09-25). [`validate_sot.py`, `sync_io_table.py --check`]
- **R46** (2026-10-04) Never auto-archive a document. Moving anything into `archive/` (or `C:\projects\_archive\`) needs Daniel's OK; settled project content is never deleted outright.
- **R47** (2026-10-10) The approved routes in `docs/harness/routes/` are Daniel's; agents do not change a route without his markup (blue line = route, blue arrow + black label = part spot, black box = instruction; every isometric figure gets a top view, §34). Skill: `st185-apply-route-markup`. [`check_route_drawings.py`, SOFT]
- **R48** (2026-09-28) Part descriptions describe the part, never its use: `TYPE, SUBTYPE, key ratings`, uppercase, no nets, circuits, devices, groups, layers, sensors, signals, stock counts, dates or plan references; wire and cable text is generated from gauge and colour. [`part_desc.py`]
- **R49** (2026-10-12) No unused part in any parts list; never join separate harnesses in one layout. [`audit_parts_layout.py` P1/P2]
- **R50** (2026-10-12) Daniel edits the drawings in the harness.design desktop app on the live files in `docs/harness/rebuild/`; agents pause while he edits and the file saved to disk wins. Workflow: `docs/harness/README.md` "Open in the desktop app", global skill `harness-design`.

### Body wiring (added 2026-10-12, second card)

- **R53** (2026-10-12) Front windshield wipers and washer stay. They are new engine-bay wiring on `ST185-EngineRoom-C` (R11) and must be drawn: wiper motor, washer pump, park circuit. Not drawn yet (OPEN-ITEMS row 54 step 5).
- **R54** (2026-10-12) The rear windshield wiper and washer are DELETED. Nothing is drawn for them; any doc or drawing that still carries a rear wiper / washer circuit, fuse or relay is stale. Owner of the deleted list: `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §5.6.
- **R55** (2026-10-12) Rear lighting is a NEW harness (the original rear wires are missing): full third brake light, reverse lights, tail lights and brake lights, all new wire. No doc or drawing may assume the OEM rear lighting wiring is reused. The harness file, its `interfaces.json` entry, route and feed point are still to be made (OPEN-ITEMS row 86).
- **R56** (2026-10-12, corrected the same day) Brake switch -> CSB3 input S7 (`interfaces.json` FL_BRAKE_SW_C1); the ECU gets brake over CAN from the CSB3. Any 12 V-active switch feeding an input that needs ground-active goes through an optoisolator.
- **R57** (2026-10-12) Glove-box power block = ONE combined power + ground bus bar; the part is being picked (Victron / Egis single-polarity options rejected). The Blue Sea 2127 / 2719 PowerBar lines in `buylist.py` EXTRA and the `PDB-M8x8` placeholder stand only until that part is picked (OPEN-ITEMS row 88).
- **R58** (2026-10-12) The door lock / tilt-away always-hot feed (the ex-R/B2 W-L net) = a new 15 A fuse on the RFRM. Closes the question in OPEN-ITEMS row 82; drawing it on `ST185-CabinPower` is pending.
- **R59** (2026-10-12) The EA engine-bay ground stud (right front fender) is M8: every ring lug landing on EA is an M8 ring sized to its wire.
- **R60** (2026-10-12) VRC enclosure panel connector = a solder, jam-nut style connector that fits the enclosure wall; picked 2026-10-12: CNLINKO LP-16 (S16). This replaces the binder M9 panel mate and its AWG 24 solder-cup limit (OPEN-ITEMS rows 76 / 77). *Partly supersedes R34 / S8: the two-plugs-per-harness form, pin map and one-splice drain stay; the drawings now carry the LP-16 cable plug `LP-16-J05PE-02-001` (S16).*

### CAN data routing

- **R51** (2026-06-16, 2026-10-03) Switchboard (CSB3) 0x640 / 0x641 / 0x642 go to the ECU only; the ECU echoes what it needs into its own TX frames. The cluster reads 0x3E8-0x3EB and 0x3EE; RealDash reads 0x3EB (gear byte only) and 0x3EF-0x3F1. The cluster sends 0x3EC / 0x3ED to the ECU (in the `.lcs` receive list). Cluster firmware as flashed is frozen and outranks every other device. Procedure: `docs/RECONCILIATION-RULES.md` Rule 2; contract details: `AGENTS.md` Working Rules. [`bench/check_parity.py`]

### Setup time

- **R52** (2026-10-11, S2/S7) All ECU settings (PCLink names, output configuration, tuning) happen at SETUP TIME, once the ECU is on the bench; outputs are named by connector + pin and/or the Quick Start Guide label ("B12 / Ign 6"). No configs are pending now: RealDash and the cluster are configured, the CSB3 is not bought. EPS speed signal: start from the MR-S VSS pulse rate and keep the ECU output adjustable (S1). Tracker: `docs/OPEN-ITEMS.md` setup-time table.

### Rule conflicts found in the 2026-10-12 consolidation

| Rules | What disagreed | Resolution |
|---|---|---|
| R4 | "5V + sensor ground splice at ECU A, B leg broken off" (09-27) vs "sensor ground never tied across letters" (09-28) | Newer wins: +5V only crosses; ground per letter. |
| R6 | Pedal at one Deutsch pair `IX_APS` (09-28) vs "pedal is one cable in A-cabin" (10-11) | Newer wins; `IX_APS` retired. |
| R27 / R31 | "terminates at the ECU or at the destination device" (09-19, 09-27) vs "at an ECU shield pin, NOT the device end" (10-03) and the VRC IN pin 3 landing (10-03, 10-12) | Read as: ECU pin always; the only device-end landing is the wheel-speed sensor shields at VRC IN pin 3. **Daniel to confirm the wording.** |
| R31 vs settled rule 6 / plan §6.30 | "enclosure may be part of the shield path" (09-27) vs "nothing bonds to the case, no shell" (10-12) | Newer wins; rule 6 marked superseded, `docs/SHIELD-RULES.md` §6.30 rewritten, OPEN-ITEMS row 75 still covers `docs/enclosures/`. |
| R17 | Alternator 3-pin plug "in ST185-HeavyDC" vs alternator IG/L/S "on bulkhead B spares" (OPEN-ITEMS row 54 step 6, DECISIONS §10/36) | R17 wins (2026-10-12): bulkhead-B route dropped; the plug's part, firewall crossing and IG / S feeds are OPEN-ITEMS G1-1 to G1-3. |
| R22 | Two-relay EPS (k_eps coil- by pump B5, k_eps_en on B12) vs `sot/channels.csv` single stage (B12 straight to k_eps 85) | DAN-RULES is newer; applied 2026-10-12 (SoT + B-cabin / CabinPower / A-cabin / A-engine / EngineRoom-C). |
| R35 vs plan §6.24 | "wire and cable are generic in every BOM" (09-17) vs M22759/16 part numbers (10-12) | Newer wins; §6.24 is history. |
| R34 vs DECISIONS §20/23/32 row | VRC box "one DTM 8-way IN + one OUT" (10-05) vs two VRC plugs (10-12, S8; CNLINKO LP-16 since S16) | Newer wins; the enclosure BOM / Routes 9-10 text lag (OPEN-ITEMS rows 64, 70, 71). |
| R29 / R30 vs OPEN-ITEMS row 73 | Row 73 still says "each cable has its own SolderSleeve ... T-spliced ... inside the transition boot" | Row 73 drain text corrected to S9/S12 (one splice drawn; T-splice is build method). |
| R14 | "combo meter and all its plugs/wires gone" vs `ST185-ClusterLED` flying leads at C11/C12 "at the combination meter" | Read as the dash-harness side of those connectors (cabin reuse allowed). **Daniel to confirm.** |
| R42 vs plan §6.33 | Fixed left-to-right schematic geometry (09-20) vs "schematic: any direction; layout: left to right" (10-12) | Newer wins; §6.33 is history. |
| R60 vs R34 / S8 | Binder M9 `99 0414 00 05` plugs (10-12, morning) vs solder jam-nut panel connector (10-12, later) | Newer wins; answered by S16 (CNLINKO LP-16, drawings updated). |
| R57 vs `buylist.py` EXTRA | Blue Sea 2127 PowerBar + 2719 cover (single polarity, 09-17) vs one combined power + ground bus bar (10-12) | Newer wins; the EXTRA lines and the `PDB-M8x8` placeholder are replaced when the part is picked. |
| R58 vs OPEN-ITEMS row 82 | "pick the fuse for W-L" vs new 15 A RFRM fuse | Answered by R58; the drawing is still to do. |
| R55 vs ENGINE-ROOM-POWER-REDISTRIBUTION §3.1 / §5.2 | J/B No.1 STOP / TAIL fuses assumed to feed the OEM rear lighting | The OEM rear wires are missing; the new rear harness needs its own feed point - **Daniel decides** (row 86). |

## Objective

Rework the harness drawings so every file represents a physical harness that will actually be built. Electrical nets may cross harness boundaries, but each physical wire section, connector, cable, enclosure interface, and BOM item has one owner and is built once.

The drawings must remain useful for assembly: show real new connectors, exact OEM splice locations, EWD references, cable cores, shields, and harness boundaries without modeling factory connectors or devices that will not be installed as part of the new harness.

## Settled design rules

1. The far-end device defines the circuit. The ECU terminal is selected only after confirming that the ECU signal group can process that device.
2. ECU pins own ECU signals for assignment and source-of-truth purposes. After device-to-ECU assignments are settled, physical wiring is drawn.
3. Every crossover between separate new harnesses ends at a real inline connector. The mating half belongs to the receiving harness.
4. A shared physical route is not shared ownership. Every physical cable section is drawn and built once.
5. Shields float at the sensor and terminate at the ECU or at the destination device.
6. ~~The only shield exception is an inline electrical device with an enclosure; its enclosure may be part of the shield path. This applies to VRC boxes.~~ **Superseded 2026-10-12 (R31, R33):** nothing bonds to a case and no shell carries a screen; VRC drain continuity is pin to pin by wire inside the box.
7. Do not raise the CAN termination issue again. It is settled and is not an open repair item.
8. OEM factory connectors and junction blocks are not new harness connectors unless the new harness physically plugs into them.
9. Connections to existing OEM wires or connector points are flying leads. Each flying lead must include the EWD connector ID, pin, page, function, and splice or attachment method.
10. `cp_xref` is not sufficient as the long-term ownership model. New references need owner harness, interface ID, build-once status, and BOM ownership.

## Physical harness architecture

### ECU-to-firewall cabin harness

Contains ECU-A, ECU-B, cabin-side firewall A, and cabin-side firewall B. Its only intentional A/B crossover is shared ECU power/ground distribution from A-side sources to B-side ECU pins. Other circuits remain with their assigned ECU connector and firewall bulkhead.

### Engine-A harness

Runs from engine-side Bulkhead A to A-assigned engine sensors and devices. It must not cross over to Engine-B circuits on the engine side.

It includes the dedicated A/C coolant-temperature switch circuit from the new sensor to engine-side Bulkhead A. This circuit does not route to the ECU.

### Engine-B harness

Runs from engine-side Bulkhead B to B-assigned engine sensors and components. It must not cross over to Engine-A circuits on the engine side.

### Loom C — engine-room/high-current harness

Carries high-current power from the cabin battery/fuse/relay area through the front fenders and engine-room perimeter. It feeds factory junction blocks, dashboard/cowl/HVAC/front-perimeter loads, starter and alternator power, fans, and jumper lugs. Heavy firewall crossings use RADLOK connectors.

OEM junction-block and OEM-device connections are flying leads with EWD locator labels, not modeled OEM plug housings.

### Rear wheel-speed harness

One Y harness:

- Rear-left ABS connector to the rear VRC IN-L endpoint.
- Rear-right ABS connector to the rear VRC IN-R endpoint.
- One shielded VRC output cable with four insulated conductors plus shield/drain.
- Output terminates at one 5-pin Deutsch inline connector near the ECU.
- Pin 5 carries the shield/drain toward the ECU shield ground.

The VRC enclosure and its M8 input/output connectors are not drawn.

### Front wheel-speed harness

Mirrors the rear arrangement:

- Front-left ABS connector to front VRC IN-L endpoint.
- Front-right ABS connector to front VRC IN-R endpoint.
- One shielded output cable with four insulated conductors plus shield/drain.
- Output terminates at one 5-pin Deutsch inline connector near the ECU.
- Pin 5 carries the shield/drain toward the ECU shield ground.

The VRC enclosure and its M8 connectors are not drawn.

### ECU-side wheel-speed spurs

The ECU-side harness owns exactly two short spurs:

- Front spur to the mating half of the front 5-pin Deutsch connector.
- Rear spur to the mating half of the rear 5-pin Deutsch connector.

Each carries +5V, Gnd Out, two conditioned outputs, and the shield/drain. No ABS sensor wiring or VRC input wiring is owned by the ECU harness.

## Device and OEM interface rules

### CSB3

The enclosure BOM defines Hammond 1590WYFL (liquid resistant, flanged) with TE Deutsch `HD34-24-33PE` as the enclosure receptacle. The harness shows the compatible mating plug `HD36-24-33SE` with size-20 socket contacts `0462-201-2031`, then stops. Do not draw CSB3 or the Hammond enclosure.

### VRC

Do not show VRC devices, enclosures, or their panel connectors. Exception (Daniel 2026-10-12, S8): each VRC harness draws its two M8 *cable plugs* (one shared IN, one OUT, as two separate pieces) on `ST185-WheelSpeed-Front` / `ST185-WheelSpeed-Rear`. Otherwise use labeled endpoints such as `VRC_REAR_IN_L`, `VRC_REAR_IN_R`, `VRC_REAR_OUT`, and their front equivalents. Output semantics are +5V, Gnd Out, left output, right output, and shield/drain.

### OEM flying leads

Use loose wire endpoints for OEM A/C amplifiers, factory junction blocks, OEM switches, and other factory wiring that will be spliced rather than unplugged. The endpoint label is the physical locator, not a new connector part.

### OEM A/C system

The OEM A/C amplifier owns ambient temperature, evaporator/water-temperature, and A/C request/control functions. These are not CSB3 inputs. The A/C pressure switch and ambient wiring remain OEM-side circuits based on the EWD.

The A/C amplifier also receives its own dedicated coolant-temperature switch. The path is: new engine sensor → Engine-A → Bulkhead A → short cabin-side branch → inline connector → A/C amplifier flying lead. The ECU ECT sensor remains separate; a second coolant sensor/switch is required.

### Obsolete CSB3 assumptions

Remove from the active harness model and CSB3 documentation:

- CSB3 cabin-temperature input.
- CSB3 evaporator-core input.
- CSB3 A/C-request input.

These are removed design assumptions, not unresolved wiring gaps.

## Endpoint types to implement

- `real_connector` — a new connector physically installed in the harness.
- `inline_interface` — a real connector pair ending one harness and starting another; counted once in the BOM.
- `oem_flying_lead` — loose wire to an existing factory wire/point; no OEM connector BOM part.
- `device_endpoint` — labeled VRC/device boundary with no device connector shown.
- `reference_only` — context only; no wire or BOM claim.

Every physical conductor should identify `physicalOwner`, `interfaceId` when applicable, `buildOnce: true`, and BOM owner. References must not look like physical work still to be built.

## Required implementation sequence

1. Freeze this handoff as the design decision record.
2. Confirm the exact 5-pin Deutsch family, contacts, seals, and backshells for front/rear wheel-speed interfaces.
3. Define the physical harness inventory: ECU/cabin, Engine-A, Engine-B, Loom C, Front WheelSpeed, Rear WheelSpeed, Rear Fuel, and the A/C amplifier spur as needed.
4. Remove obsolete CSB3 A/C assumptions and convert OEM device/J/B endpoints to flying leads with EWD locators.
5. Correct Bulkhead A c32 to `spare` everywhere it appears in active drawings.
6. Add the A/C coolant switch to Engine-A and the cabin-side inline interface.
7. Rebuild the rear wheel-speed Y harness, shielded five-pin output interface, and ECU-side rear spur.
8. Mirror the completed design for the front wheel-speed harness and ECU-side front spur.
9. Apply the endpoint convention to CSB3, OEM A/C, OEM junction-block, and remaining harness interfaces.
10. Replace ownership/BOM generation and regenerate min files and generated outputs.
11. Run the revised checker suite and inspect every cross-harness interface.

## Acceptance criteria

- No VRC enclosure or M8 connector appears in wheel-speed harness files.
- Front and rear wheel-speed sensor drops each form one Y harness.
- Each VRC output is one shielded five-conductor interface ending at one real 5-pin Deutsch connector.
- ECU-side harness has exactly one front spur and one rear spur.
- CSB3 harness ends at `HD36-24-33SE` and does not draw CSB3 itself.
- OEM endpoints are flying leads with EWD connector/pin labels and no OEM BOM connector housing.
- Every physical section has one owner and is counted once.
- Bulkhead A/B mating and shield rules pass.
- Shield drains float at device ends and reach the correct ECU shield ground (the wheel-speed sensor shields land on the VRC IN pin, R31).
- No unexplained direct cross-loom conductor remains.

## Harness checker and generator audit

The current suite encodes the old model: nine broad looms, direct device connectors, `cp_xref` dummies, VRC boxes/M8 connectors, direct wheel-speed-to-ECU paths, connector-ID BOM deduplication, and a frozen legacy-prebuild comparison.

### Keep, with changes

- `lint_v09.py` — keep for schema validity; accept endpoint/interface metadata.
- `audit_cavity_parts.py` — keep the one-cavity rule; ignore non-physical endpoints.
- `audit_bh_collisions.py` — keep; bulkhead one-circuit-per-cavity remains valid.
- `audit_bulkhead_pairs.py` — keep but distinguish bulkheads from inline/device endpoints.
- `audit_pin_names.py` — keep shield-ground and bulkhead-name rules; remove VRC connector assumptions.
- `validate_sot.py` — keep ECU pin ownership checks; allow non-ECU device circuits without fake ECU rows.
- `sync_io_table.py` — keep limited to ECU SoT and IO table.
- `make_min.py` — keep for upload copies.

### Rewrite substantially

- `audit_shields.py` — trace abstract VRC enclosure exceptions and the fifth output drain pin without requiring modeled VRC shells.
- `audit_mating.py` — retain bulkhead checks, replace old device-connector M7 with interface ownership checks.
- `check_all.py` — run the revised structural, ownership, interface, shield, BOM, build-list, and min-file gates.
- `run_pipeline.bat` — replace the mutating legacy order with the explicit validation pipeline.

### Replace

- `buildlist.py` — it hardcodes nine filenames, treats references as build endpoints, reports deliberate cross-harness handoffs as `no route found`, and has no physical-owner/interface model.
- `buylist.py` — connector-ID deduplication and `cp_xref` cannot represent inline pairs, flying leads, device endpoints, or fifth-pin drains.

Replacement build-list output must include physical owner, interface ID, endpoint type, EWD locator, connector/mating-half details, build-once identity, cable core/drain mapping, and explicit handoff records.

Replacement BOM logic must count inline connector pairs once, count CSB3 `HD36-24-33SE` as a real harness part, count no OEM connector housing for flying leads, count no VRC connector, and count cable/splice materials by physical owner.

### Retirement candidates — do not delete yet

- `verify_rebuild.py` — compares against the old `legacy-prebuild/` graph and will treat intentional physical decomposition as false failures. Replace it with ownership/connectivity validation first.
- `fix_cable_parts.py` in its current mutating form — hardcodes 1/2/4-core cable classes and rewrites all files. The new VRC output needs four cores plus a drain pin. Convert to a validator or replace it.
- `layout_633.py` in its current hardcoded nine-loom form — contains VRC IDs and old zones and mutates files. Replace with per-harness layout generation.

Retire these only after replacement gates pass. Existing `cp_xref` objects may remain temporarily during migration, but new work must not use them to represent inline connectors, OEM flying leads, or VRC endpoints.

## Proposed replacement gates

1. `validate_interfaces.py` — unique interface IDs, exactly two mating halves, declared harness ownership, complete endpoint references.
2. `validate_ownership.py` — one owner per physical conductor, one BOM owner per build-once item, no BOM claim from references.
3. `validate_oem_endpoints.py` — every flying lead has EWD page, connector, pin, and connection method; no OEM connector housing is counted.
4. `validate_wheel_speed.py` — two sensor branches per front/rear, one VRC endpoint per side, one shielded four-core-plus-drain output, one five-pin connector, one ECU spur per interface.
5. Revised `audit_shields.py` — abstract-endpoint-aware shield tracing.
6. Replacement `buildlist.py` — owner-aware physical build list.
7. Replacement `buylist.py` — interface-aware one-count BOM.

## First implementation slice

Before restructuring every loom, complete one vertical slice:

1. Rear wheel-speed Y harness.
2. Rear five-pin shielded output connector.
3. ECU-side rear spur.
4. Ownership-aware build-list and BOM records.
5. Revised shield/interface checks.

Then mirror it for the front wheel-speed harness, and apply the same conventions to CSB3, OEM A/C, OEM junction blocks, and remaining harnesses.

## Adopted for execution (2026-09-27)

The implementation plan listed six open points (D1-D6). Execution went ahead on the
recommended option for each. Every one can be reversed; the drawings and the registry
(`docs/harness/interfaces.json`) are the only places that carry them.

| | Decision | Consequence |
|---|---|---|
| D1 | **Front interface is 6-way with two drains.** Pin 5 = drain of the front output cable (5V / Gnd / FL, screen → SHIELD_A, A7). Pin 6 = drain of FR's own 1-core screened cable (→ SHIELD_B, B17). | The 6-way drawing is unchanged. |
| D2 | **Deutsch DT 6-way:** `DT04-6P` receptacle + `W6P` on the wheel-speed harness side, `DT06-6S` plug + `W6S` on the ECU spur (the receiving harness; it supplies +5V, so it gets the sockets). Contacts `0460-202-1631` / `0462-201-1631` (size 16, owned). Rear pin 6 is plugged (`114017`). | Two new connector pairs to buy. The owned `DT04-12PA` / `DT06-12SA` sets stay available. |
| D3 | ~~`ST185-CAN`, `ST185-AntiTheft`, `ST185-ClusterLED` stay as they are. The ECU/cabin merge and the engine re-split by bulkhead letter are Phase 7.~~ **Superseded 2026-09-28** by `docs/RECONCILIATION-RULES.md` Rule 3 (Daniel): four ECU looms by connector letter, `ST185-A-cabin` / `-B-cabin` / `-A-engine` / `-B-engine`; the merged ECU/cabin drawing is retired. CAN, AntiTheft and ClusterLED still stay as they are. | — |
| D4 | **Rear Fuel is its own harness** with a `DT04-2P` / `DT06-2S` inline pair for fuel level (signal + ground). The pump keeps its own connector per 6.41. | — |
| D5 | **A/C coolant switch** crosses on **bulkhead A c37 (signal) / c38 (return)**, then a `DT04-2P` / `DT06-2S` inline to a short A/C amplifier spur. Amplifier end: flying lead to TW, conn C (A34) pin 20, EWD p.150. Return pin and the switch part number are `TBD` (never invent a part number). | — |
| D6 | **CSB3 0x640/0x642 A/C bits are unassigned in the docs only.** No frame, `frames.py` or RealDash change. | — |

~~J/B2 2A / 2D / 2E stay real connectors: the build crimps a dummy header that plugs into
them (rule 8 exception). J/B1, IE1, R/B2, R/B4, the OEM switches and both A/C amplifiers
become flying leads.~~ **Superseded 2026-10-12 (S15):** J/B2 is removed; no dummy header.

## Open questions

| | Question | Options | State |
|---|---|---|---|
| Q-RAIL | The injector rail (F11 15 A) and COP rail (F10 20 A) feed A devices but cross on bulkhead B c1/c2, on size-12 contacts (`0460-220-1231` / `0462-210-1231`, 25 A). Rule 3 wants them on bulkhead A, which (`HDP24-24-47`) has 5 size-16 and 42 size-20 cavities, no size-12; the size-16 contacts are 13 A and only c1 is spare. | (1) keep on B as a recorded exception; (2) run both rails through loom C point-to-point like the starter and fan feeds; (3) replace bulkhead A with an insert that has size-12 positions; (4) split each rail over two size-16 contacts on A | ~~Resolved 2026-09-28 (Daniel): option (1) as a spur~~ **Final 2026-09-28 (Daniel): A side, through the DTP 4-way pass-through `IX_RAIL_A`** - see "Audit closed" below. Crossover (d) retired. **Closed.** `IX_RAIL_A` itself was retired 2026-09-29: the rails cross on bulkhead A c48 / c49 of the shared DRB102 (see below). Fuses are now RFRM INJ 15 A / RFRM COP 20 A (Option B, 2026-10-11). |

## Binding decisions (Daniel, 2026-09-28 audit) - final, do not re-ask

| | Decision | Where it lives |
|---|---|---|
| B1 | **Link CAN-Lambda** runs its four wires through **bulkhead B**: c13 CAN H, c14 CAN L (size 16, 20 AWG), c3 +12V, c4 GND (size 12, 14 AWG, stepped to 20 AWG at `sp_lam12_b` / `sp_lamg_b` after the firewall for the DTM plug). +12V from cabin fuse **F5 10 A** (`ST185-CabinPower`; since Option B 2026-10-11 the fuse is **RFRM LAM 10 A**, RFRM Bus 2); GND to the cabin chassis ground `sp_chassis`. Link pinout: pin 3 CAN L, pin 4 CAN H. Broken off CAN <-> B-cabin / B-engine. This uses bulkhead B's last four spares. | `ST185-CAN`, `-B-cabin`, `-B-engine`, `-CabinPower`, `-A-cabin`, `interfaces.json` |
| B2 | **VSS (E154F)**: drawn as-is on the best reading - Toyota 83181-20040, plug **90980-11143**, pin 1 IG +12V, 2 ground, 3 SP1 out. No TBD. | `ST185-B-engine`, `sot/channels.csv` B29 |
| B3 | **Charge-lamp resistor**: reference note on ClusterLED only, never a drawn part. | `ST185-ClusterLED` `n_chg_test` |
| B4 | `sp_5v` is split into `sp_5v` + `sp_5v_2`; `sp_gndout_eng` is a `GENERIC CRIMP SPLICE 14-10`: four 20 AWG = one 14 AWG combined (Wire Barn Combined Wire Gauge Calculator). Closed by Daniel 2026-09-28 under the combined-gauge splice rule below. | `ST185-A-cabin`, `-A-engine` |
| B5 | **Alternator output protection**: fusible link or inline fuse / breaker on the positive cable at the trunk battery or near the cabin fuse box - never at the starter. | `ST185-EngineRoom-C` `n_alt_prot`, plan 6.20 |
| B6 | Battery is **AGM**. Main power parts: Eaton RFRM box plus a small GEP set, a **Longacre 4-terminal kill switch** in the trunk (second pair cuts the alternator IG), and the G4X Stop Switch input. Drawn only where a place already exists; the power layout is not redesigned. | AGM and kill switch: `n_alt_prot`, `buylist.py`. RFRM is drawn in `ST185-CabinPower` since fuse box Option B (2026-10-11, PR #83); GEP and the Stop Switch input have no place in the drawings yet, so they are recorded here only |
| B7 | **RealDash Pi**: switched ignition feed only, on and off with the car. No Pi-hold relay or power-hold circuit anywhere. | `ST185-CabinPower` RFRM DEV (was EngineRoom-C `gbx_body` DEV before Option B, 2026-10-11), CSB3 L1 spare, plan 6.38 / 6.47 |
| B8 | **k_eps** sized: HCFB H4 Bussmann **AMI-60** (now **LMI L7**, AMI-60, since Option B 2026-10-11), **8 AWG** feed. Sources in `sot/channels.csv` k_eps c1. | `ST185-CabinPower`, `-B-cabin`, `-EngineRoom-C` |

**Audit closed (Daniel, 2026-09-28, final):**

- **Q-RAIL - resolved, B spur kept.** Daniel: "move the injector (F10) and COP (F11) power feeds
  to bulkhead A (A-cabin -> bulkhead A -> A-engine), per Rule: non-ECU power follows its
  device's ECU signal bulkhead. Remove the B spur and crossover (d). If bulkhead A's spare
  cavities can't take the size-12 contacts, keep the current B spur instead and tell me exactly
  why." They can't: bulkhead A (`HDP24-24-47PE-L017` / `HDP26-24-47SE-L015`) has 42 size-20 and
  5 size-16 cavities and no size-12 position, so a size-12 contact (`0460-220-1231` /
  `0462-210-1231`, 12-14 AWG, 25 A) has nowhere to go. The fallback does not fit either: the
  rails are 14 AWG on 15 A (F11) and 20 A (F10) fuses, a size-16 contact is 13 A and takes 16-20
  AWG, a size-20 is 7.5 A, and only one size-16 cavity (c1) is spare - splitting each rail over
  two size-16 contacts would need four. *(Superseded the same day - see Q-RAIL final below.)*
- **Splice sizing - standing rule (Daniel, 2026-09-28):** size a splice by the **combined** gauge
  of the wires it joins, using the Wire Barn Combined Wire Gauge Calculator
  (https://www.wirebarn.com/Combined-Wire-Gauge-Calculator_ep_42.html); the splice's range must
  cover that combined gauge (example: 4 x 20 AWG = 1 x 14 AWG, fits a 14-10 splice).
  harness.design's per-wire "wires are too thin" warning on splices is a known false alarm - do
  not chase it. Owner: R36 above (shield drains excepted, R30); detail in `docs/RECONCILIATION-RULES.md` Rule 3.
- **Connector substitution - standing rule (Daniel, 2026-09-28):** if bulkhead A or B runs out
  of pins or needs higher-capacity contacts, spec a different connector or add a second one,
  with a complete compatible matching set for both sides (housings, inserts, contacts per wire
  gauge, seals / cavity plugs, wedgelocks, gasket or backshell), every part number from the
  maker's datasheet. Owner: R8 above.
- **Q-RAIL - final (Daniel, 2026-09-28): the rails cross on the A side.** Daniel: "Apply it now
  to Q-RAIL: the injector (F11, 15A) and COP (F10, 20A) feeds belong on the A side per the
  ECU-letter rule. Find the simplest complete matching set that carries both 14 AWG feeds
  across the firewall on the A side." Chosen: a Deutsch DTP 4-way flange pass-through beside
  bulkhead A, `IX_RAIL_A` - it changes nothing on bulkhead A. A new HDP20 insert was ruled
  out: every shell-24 arrangement with size-12 positions has at most 6 size-20 cavities
  (24-29: 4 x 12, 19 x 16, 6 x 20), and bulkhead A uses 33 size-20 and 4 size-16 today (TE
  HDP20 configuration sheet). DTP is the only Deutsch size-12 family with a flange-mount
  receptacle in TE's catalog, and only in 4-way (`DTP04-4P-L012`). c1 injector, c2 COP, c3 /
  c4 plugged. The B spur and crossover (d) are removed; bulkhead B c1 / c2 are spare.

  | Side | Part | PN (TE Deutsch) |
  |---|---|---|
  | Cabin (`ST185-A-cabin`, firewall) | Flange receptacle, 4 pos, pins | `DTP04-4P-L012` |
  | | Mounting gasket | `DTP4P-L012-GKT` |
  | | Wedgelock | `WP-4P` |
  | | Pin contact, size 12, solid, gold, 12-14 AWG, 25 A (x2, owned) | `0460-220-1231` |
  | | Cavity sealing plug (x2) | `114017` |
  | Engine (`ST185-A-engine`) | Plug, 4 pos, sockets | `DTP06-4S` |
  | | Wedgelock | `WP-4S` |
  | | Socket contact, size 12, solid, gold, 12-14 AWG, 25 A (x2, owned) | `0462-210-1231` |

  TE's DTP standard contacts are the nickel `0460-204-12141` / `0462-203-12141`; the catalog
  also lists gold size-12 solid contacts for DTP (kits DTP2-4 / DTP4-4), and Deutsch solid
  contacts are intermateable across the DT / DTP / HD / HDP families, so the owned gold
  `0460-220-1231` / `0462-210-1231` are used.
  | | Cavity sealing plug (x2) | `114017` |
- **`IX_B_RAIL` - resolved as-is:** +5V only, from Daniel's own words ("use the extra A connector
  pins to carry power and ground over to the B engine harness, as a short spur with inline
  connector"; ground later ruled back onto B22).
- **Bulkhead B shield spare:** none kept; the CAN-Lambda stays as drawn (B1).
- **Charge-lamp resistor:** the removal (`fe99eea`) is correct; only the ClusterLED reference
  note remains (B3).

## Bulkhead A/B + DTP replaced by a shared DRB102 (Daniel, 2026-09-29)

**Decision:** Bulkhead A (`HDP24-24-47PE-L017` / `HDP26-24-47SE-L015`), bulkhead B
(`HDP24-24-21PN` / `HDP26-24-21SN`), and the `IX_RAIL_A` DTP 4-way pass-through (Q-RAIL
final, above) are retired and replaced by **one** Deutsch DRB 102-way bulkhead —
`DRB12-102PAE-L018` (firewall receptacle) + `DRB16-102SAE-L018` (engine plug) +
`DRBF-1A` (mounting flange for the mated pair), one firewall hole in place of three.
Full options and ratings are in `_research\BULKHEAD-OPTIONS-2026-09-29.html`
and `_research\DRB102-RATINGS.html` (local-only, untracked; moved from the retired `C:\projects\inbox\st185-research\`).

Ratings: 6 of 9 checked items pass with margin against a firewall location (-55 to
125°C operating range, IP68 | IP6K9K mated sealing, vibration, mechanical shock,
thermal cycling, and per-size contact current) plus SAE J2030 automotive-connector
compliance. Three items (unmated sealing, an itemized fluid-resistance list, and salt-
spray duration) were not found on TE's reachable consumer pages; chasing the actual TE
spec/qualification PDFs for those is open item #40. Daniel, 2026-09-29: "PROCEED with
step 3 (implement), taking SAE J2030 compliance plus the strong pass on everything else
as good enough" — implementation went ahead on that basis; if a qualification PDF later
surfaces a real failure for a firewall spot, this decision is reopened.

*(Drawing form superseded 2026-10-12 by S10: every drawing shows the whole 102-cavity connector, the other section N/C. The paragraph below is history.)*
The physical DRB102 is drawn as two logical halves so the A/B ECU-letter gate (Rule 3)
still applies to each side's own signals — `bh_a_fw` / `bh_a_eng` (49 cavities: the
former bulkhead A's 37 real circuits, unchanged size-16/size-20 upsized to size-16, plus
the two `IX_RAIL_A` power feeds folded in on size-12) and `bh_b_fw` / `bh_b_eng` (21
cavities: bulkhead B's existing 19 real circuits, already size-12/size-16, unchanged).
Every existing contact part number is reused unchanged (`0460/0462-202/201-1631` size-16
gold 13 A, `0460/0462-220/210-1231` size-12 gold 25 A already in the owned-stock and
contact library) — the DRB102 needed zero new contact parts, only new housings.

**Cavity map settled (2026-10-11, from TE's drawing DRB12-102PXE-L018 rev C3):**
`docs/harness/DRB102-CAVITY-MAP.md`. Each drawn cavity's `designation` is now its real
DRB cavity number; cavity ids (`cN`) are unchanged, so no wire moved. A keeps its 49
cavities (37 live circuits and 3 reserved drains fill the right wedgelock half's 40
size-16 positions, its 7 spares in 52-61, injector/COP on size-12 1 and 2). B grows from 21 to 53
so that all 102 physical cavities are drawn exactly once, each with a contact or a sealing
plug: 3 reserved shield-drain cavities (c22-c24) plus every remaining spare (size 16, 12, 8
and 4). Each shield drain gets its own cavity, which retires the §7.3 plan to share B c1
through a 14 AWG pigtail. Gate: `audit_mating.py` M8.

Each half's `.harness` file carries its own local `connectorParts` copy of the DRB102
housing (`cp_drb_recept` / `cp_drb_plug`), with `numberOfCavities` set to that file's own
cavity count (49 or 21) so `lint_v09.py`'s per-file cavity-count check still holds —
this is a per-file documentation choice, not a claim that the physical housing itself
has only 49 or 21 positions. The two halves are tied together with a new
physical part group (`drb102_recept` = `bh_a_fw`/`bh_b_fw`,
`drb102_plug` = `bh_a_eng`/`bh_b_eng`; since 2026-10-12 kept in `docs/harness/interfaces.json`
`physicalPartGroups`, because harness.design rejects an unknown connector key) so `buylist.py` counts the housing and its
flange once, not once per half — see the "shared physical part" gap this closes,
below. The flange is wired through `cp_drb_recept`'s `mountPartId` (owned by the
alphabetically-first half, `bh_a_fw`) so it is bought exactly once. The DRB102 needs
**two** wedgelocks per shell (left + right, different part numbers:
`WB-51PAL`/`WB-51PAR` receptacle side, `WB-51SAL`/`WB-51SAR` plug side) and the
`.harness` schema only holds one `lockPartId` per connector configuration, so all four
are tracked as `buylist.py` `EXTRA` line items instead rather than forced into that single field
(the reference copies in each half's `lockParts` list were removed 2026-10-12: no unused
parts in a parts list, `audit_parts_layout.py` P1).

`buylist.py` gained the physical-part-group mechanism described above: distinct
connector ids that are documentation halves of one physical part (not copies of the
same id in different looms — that's the pre-existing `SHARED` handling) now dedupe the
housing part number and its configuration hardware (lock/boot/backshell/mount/
dustCover) to the alphabetically-first half, while every cavity's own contacts and
plugs still count on both halves since those are real and separate. This closes the
exact gap flagged in `BULKHEAD-OPTIONS-2026-09-29.html`: "buylist.py / NEED-TO-BUY.md —
needs a 'shared physical part' flag... today's 'counted once' handling only dedupes the
same id across files." The old HDP24-specific backshell/gasket/panel-nut `EXTRA`
entries (`2428-011-2405`, `M902-2243`, `16-04477`, `2411-001-2405`) are removed — there
is no more shell-24 HDP housing to backshell, gasket, or panel-nut.

**Files touched:** `ST185-A-cabin.harness`, `ST185-A-engine.harness`,
`ST185-B-cabin.harness`, `ST185-B-engine.harness`, `docs/harness/interfaces.json`
(`IX_RAIL_A` inline_interface removed, its broken-off `"what"` text repointed to
`bh_a_fw` c48/c49), `docs/harness/buylist.py`. No `sot/channels.csv` change was needed —
it tracks ECU signal channels, and the injector/COP power feeds were never recorded
there as rows.

## Settled 2026-10-11 (Daniel) - final, do not re-ask

| # | Decision | Recorded detail |
|---|---|---|
| S1 | **MR-S EPS speed signal** (Link Aux 7, A27 -> pump B pin 2): start from the OEM vehicle-speed pulse rate the MR-S pump expects for its model years, and keep the ECU output's pulse range adjustable so the assist level can be tuned. | Exact rate and output setup are set at ECU setup time (`docs/OPEN-ITEMS.md` setup-time table). |
| S2 | **All ECU settings happen at setup time** (no ECU on hand now): PCLink setting names, output config, tuning. They are a setup-time group in the tracker, not open questions. Outputs are named by ECU connector + pin and/or the Link XtremeX Quick Start Guide pin label (e.g. "B12 / Ign 6"). | `docs/OPEN-ITEMS.md` setup-time table. |
| S3 | **Front wheel-speed sensor plug: designer's choice.** Chosen: keep what is drawn - a sealed Deutsch DT 2-way at each front sensor (`DT06-2S` on `ST185-WheelSpeed-Front`, `wss_fl` / `wss_fr`; owned size-16 contacts), the same family as the rear and the fuel-level sender. | Note: the drawing does not use the OEM ABS 2-pin housing; if the sensor keeps its OEM pigtail, a `DT04-2P` goes on that pigtail. |
| S4 | **+5V (A32) load is an engineering estimate, not a question.** Consumers on `sp_5v`: MAP, fuel and oil pressure (Lowdoller 899005 / 7990150 x2), coolant pressure (Ronybuy), ETB TPS (2 tracks), APS pedal (2 tracks), turbo speed (BorgWarner 179430), 2 VRC boards (NCV1124). Upper bound from the usual supply current of each sensor class (ratiometric pressure sensor <= 10 mA, Hall/pot track <= 10 mA, Hall speed sensor <= 20 mA, NCV1124 board <= 10 mA): 4 x 10 + 4 x 10 + 20 + 2 x 10 = **about 120 mA worst case, about 60 mA typical**. | Not datasheet-confirmed per part; the Link +5V Out current limit is not in the local Link PDFs, so compare at setup time (PCLink help) - setup-time table. |
| S5 | **DTM seals: closed.** Every DTM connector uses its built-in seals; no separate core-OD rule is added. | - |
| S6 | **Heavy cable sizes are calculated** (amps, run length, temperature - the 2026-09-17 gauge rule in `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md`), never asked. H5 alternator B+ (`w_alt`): 160 A peak; 2 AWG copper is about 0.51 mOhm/m at 20 C, about 0.68 mOhm/m at 105 C, so a ~1.5 m bay run drops about 0.16 V (1.4 %) at 160 A. 4 AWG (about 1.1 mOhm/m hot) would drop about 0.26 V (2.2 %) and run hotter, with less margin for the peak-current-plus-margin rule. **H5 stays 2 AWG**, as drawn. | Run length is an estimate from Route 1 (not drawn as a length); re-check if the route grows past ~3 m. |
| S7 | **No configs are pending:** RealDash and the center cluster are already configured; the CSB3 is not bought yet, so its CAN/input assignments wait for setup (its harness stays drawn). | `docs/OPEN-ITEMS.md` setup-time table. |

## Settled 2026-10-12 (Daniel) - binding

| # | Decision | Recorded detail |
|---|---|---|
| S8 | **Front and rear wheel speed, `ST185-WheelSpeed-Front` and `ST185-WheelSpeed-Rear`** (Daniel 2026-10-12; final = Daniel's own example drawing of the front, harness.design ZZxQ, export `_research/WS-FRONT-DAN-EXAMPLE-2026-10-12.json`, mirrored on the rear): (a) **two separate pieces, no drawn link** - IN: the L and R sensor cables run to a point by the IN plug (`bp_*_y`) and land in it; OUT: the OUT plug -> 4-core screened cable (1100 / 1880 mm + 300 mm) -> the inline DT04-6P c1-c5 (c6 spare). Layout note "VRC FRONT" / "VRC REAR" between the plugs. No bundle, branch point, wire or cable joins the IN plug to the OUT plug. (b) **two plugs, same part**: CNLINKO `LP-16-J05PE-02-001` female cable plug, 5 contacts, unshielded, solder (S16; was binder M9 `99 0414 00 05` until 2026-10-12). IN (`lp16_vrc_f_in` / `lp16_vrc_r_in`): 1 ABS+ L, 2 ABS- L, 3 shield drain, 4 ABS+ R, 5 ABS- R. OUT (`lp16_vrc_f_out` / `lp16_vrc_r_out`): 1 +5V, 2 Gnd, 3 L out, 4 R out, 5 screen drain. (c) **screens**: both sensor cable screens go into ONE splice at the IN plug and one drain wire runs to IN pin 3 - no SolderSleeve (S12 final). (d) **no connector shells, project-wide** - every drain lands on a pin (`docs/SHIELD-RULES.md`). | Parts recorded in `docs/sourcing/README.md` "Picked parts not on hand". Plug gauge: S16 (OPEN-ITEMS row 76 closed). Gates: `validate_wheel_speed.py` W1, W3 (both screens into one splice, one drain wire to the screen pin; legs meet only at a point by the IN plug), W8 (one shared IN + one OUT plug, same part), W9 (IN and OUT never joined); `lint_v09.py` / `audit_shields.py` R3 reject shells. Reverses the 2026-10-05 "one DTM 8-way IN + one OUT" entry below (row 20/23/32) and the IN text of Routes 9 / 10 - OPEN-ITEMS rows 70, 71, 73. |
| S9 | **Shared drain pin = one splice** (Daniel 2026-10-12, binding; supersedes the earlier "drain T-splice" wording): where two or more screens land on one pin, all of them go into ONE splice node and one drain wire runs from it to the pin - no chain, no per-cable splice, no combined-gauge pigtail, no two wires in one contact. Drain gauge does not scale with the number of screens (noise current only). Every CAN node branch shield goes into the one trunk splice. Applied to A7, B17, the CAN screen splice and both VRC IN pin 3s. | Owner: R29 / R30 above; inventory in `docs/SHIELD-RULES.md` "Shared drain pin". Drawn as a `GENERIC SOLDER SPLICE` on the pin's connector (`locationId`). OPEN-ITEMS rows 73 / 76 noted (drain side only). |
| S12 | **No SolderSleeves; every shielded cable is drawn as if it had a drain wire** (Daniel 2026-10-12, binding; the sleeve-per-screen idea of #103 / #104 is dropped): our Raychem cable has no drain wire, but the drawings do not show that. A cable's shield connects directly to its connector drain pin; no splice node exists just to terminate a shield and no sleeve is a covering anywhere. Only where 2+ shields share ONE pin: one splice, one wire to the pin (S9). Removed: `audit_solder_sleeves.py`, `cable_dimensions.json`, the sleeve splices on all looms, the `S200` sleeve and 22 AWG sleeve-lead parts from `ST185.harnesslib`. | `docs/SHIELD-RULES.md`; gate `validate_wheel_speed.py` W3. Cable OD / sleeve sizing work (OPEN-ITEMS row 81) closed as dropped. |
| S13 | **Drawings stay clean** (Daniel 2026-10-12, binding; his own `ST185-WheelSpeed-Rear.harness` is the model): only parts Daniel asked for; no entry or cavity signal that says "not used" or is a placeholder; no coverings, boots, sleeves, seals or backshells added unasked; no splice unless 2+ wires or shields truly join; part definitions the drawing does not reference are removed (`ST185.harnesslib` holds only what the drawings use). Real spare cavities on real connectors stay, other files' cavities stay N/C, and spares get no extra parts. Gates relaxed to match: `audit_drawing_rules.py` G2 lists a bundle without a length instead of failing; `audit_cavity_parts.py` no longer requires a sealing plug on an unused bulkhead cavity. | Skills `harness-design` and `st185-build-harness-from-sot`; `docs/OPEN-ITEMS.md` history. |
| S14 | **LMI fuse block = loose Eaton modules in two stacks** (Daniel 2026-10-12; closes OPEN-ITEMS row 78 item 2): Eaton Series LMI allows "maximum of seven modules per assembly" including the input module, so 7 fuses cannot share one input; assembled LMI units have a minimum order of 100, so the box is built from parts sold singly. Stack A: `LMI1-M-1-1` input + 4 x `LMI1-M-1-0` (L1 50, L4 40, L6 60, L7 60 A) on bus bar `B109-7046-5`; stack B: `LMI1-M-1-1` input + 3 x `LMI1-M-1-0` (L2 / L3 / L5, 30 A) on `B109-7046-4`; each input has its own 4 AWG feed from the PDB bus. Each module is its own drawn connector (`lmi_a_*`, `lmi_b_*`): input module 1 stud (M8), fuse module 2 studs (M5, BUS + OUT). Covers come with every module; bus bars are bought, not drawn. Source: Eaton Series LMI catalog page and spec sheet (https://www.eaton.com/us/en-us/catalog/emobility/series-lmi.html). | `ST185-CabinPower` |
| S10 | **DRB102 bulkhead = one 102-position connector** (Daniel 2026-10-12, option A; closes OPEN-ITEMS row 78 item 1): A and B are only our names for sections of ONE connector. Library parts `DRB12-102PAE-L018` / `DRB16-102SAE-L018` have `numberOfCavities` 102; `bh_a_fw` / `bh_b_fw` / `bh_a_eng` / `bh_b_eng` each show all 102 cavities with TE's numbers, the other section's cavities N/C (no signal, contact or plug) with a note "see ST185-<other>". The loom split by ECU letter (Rule 3) stays. | N/C cavities are not conductors, so they do not count toward the Free-plan 100-connection limit (https://docs.harness.design/plan: a connection is a conductor between two components; https://docs.harness.design/component/connector: an N/C cavity is treated as unwired everywhere). Gates: `audit_mating.py` M8 (live cavities), `audit_shared_connectors.py`. |
| S11 | **Shared connectors are drawn whole** (Daniel 2026-10-12, binding for all harnesses, all projects): a physical connector shared by more than one harness file is drawn as the WHOLE connector in every file - real part, real cavity count, same designations; cavities owned by another file are N/C with a "see <other file>" note. Never a partial connector or an invented split part. | Registry: `interfaces.json` "physicalPartGroups" (today only the DRB102). Gate `audit_shared_connectors.py` SC1-SC5 in `check_all.py`. Rule text also in `docs/harness/README.md` and the `harness-design` / `st185-build-harness-from-sot` skills. |
| S15 | **No OEM engine-bay fuse / relay box, plug or wire** (Dan, 2026-10-10 rule, applied 2026-10-12): J/B No.2, R/B No.2-5, F11, the engine-room main wire and every factory plug and wire that ran to them are removed. Every ex-J/B2 / R/B load gets its own new wire from the glove-box box: bay loads to the device plug (HEAD LH / RH -> H1 / H2 pin 3; horns -> DT 2-way each, ground to EA), cabin loads to the factory cabin lead (hazard IE1-12, dome J/B1 1H-2, RTR IE1-3 -> R8, AM1 / AM2 IE1-10 / -17, always-hot J/B1 1I-1, blower B4 pin 2, power windows W-G). The J/B2 dummy header and the `(OEM block)` part are deleted; the 2026-09-27 "J/B2 2A / 2D / 2E stay real connectors" note above is superseded. Pins: 1993 TIS EWD p.62, 116, 130, 132, 137, 185, 215-216. | `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §5.4 (owner), `ST185-EngineRoom-C`, `ST185-CabinPower`; open: OPEN-ITEMS rows 46, 54, 82. |
| S16 | **VRC enclosure connectors = CNLINKO LP-16, rear nut** (Daniel 2026-10-12; the pick for R60, replacing the binder M9 of S8 / R34, whose solder cups take AWG 24 max): cable plug `LP-16-J05PE-02-001` (female, 5 pin, plastic, solder cups 0.34-0.5 mm2 / 22-20 AWG, IP68 mated, latch, 5 A 250 V) on both IN and OUT of both VRC harnesses; panel socket `LP-16-C05SX-02-101` (male, single-hole rear nut M18 x 1.5) x2 per box. Female on the cable so the OUT lead (ECU +5V) has recessed sockets when unplugged. Pin map unchanged (S8 b). Fit on Hammond 1590WYFL: D cutout 18.5 mm / 16.5 mm across the flat, max panel 4.5 mm vs a wall of about 3.4 mm at the rim, face 25.5 mm round x 27.8 mm on a 38 mm body wall, 27.0 mm or less behind the panel vs 85.17 mm inside. LP-12 (Daniel's example) was checked first: its rear-nut socket has no published max panel thickness, so it was not used. | CNLINKO drawings LP-16-xxxPE-02-0xxx and LP-16-xxxSX-02-1xxx (CNLINKO download center, LP series); `docs/harness/rebuild/ST185.harnesslib`, `docs/enclosures/vr-conditioner-bom.csv`, `docs/sourcing/README.md`. OPEN-ITEMS rows 76 / 77 closed; two-cable entry at the IN plug is row 73. |

## Harness reconcile plan (2026-09-29 to 2026-10-11) - retired 2026-10-11

The harness reconcile plan (`HARNESS-RECONCILE-PLAN.html`, local-only, never committed) was
the planning document for the routes and the harness update pass. It was retired in the
2026-10-11 repo cleanup: its decisions are applied in the files named below, its open
questions are rows in `docs/OPEN-ITEMS.md`, and the approved route drawings are tracked in
`docs/harness/routes/`. Repo text that cites "plan §N" or "Section N" (2026-10 dates) means
this plan; the index below says what each section settled and where it lives now.

| § | Settled (Daniel unless noted) | Lives now in |
|---|---|---|
| 1-2 | J/B and R/B map; factory harness list | `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` |
| 3, 9.5, 15 | A/C: keep the auto amp, delete A15; Link drives the clutch relay `k_acc` on Ign 8 (B10); A/C button on An Volt 10 (B31), evaporator thermistor on An Volt 11 (B32); dual pressure switch A5 in series with the relay coil | `sot/channels.csv` b10/b31/b32, `docs/harness/ACAMP-SPUR-LABELS.md` |
| 7 | Shield rules S1-S7, V1-V3, B1; redraw list 7.3 (done, PR #82) | `docs/SHIELD-RULES.md`, `docs/RECONCILIATION-RULES.md` |
| 8 | Endpoint pin list authored from the SoT, drawings checked against it (not generated from drawings) - not yet approved or built | `docs/OPEN-ITEMS.md` |
| 9.1 | No fuse or relay in the engine bay; F11, R/B No.5 and J/B No.2 deleted | `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` |
| 10, 36 | `ST185-HeavyDC` split out of harness C (PR #75); alternator IG/L/S through bulkhead B size-16 spares (superseded by R17, 2026-10-12) | `docs/harness/rebuild/ST185-HeavyDC.harness`, `docs/harness/DRB102-CAVITY-MAP.md` |
| 11 | VRC +5V from ECU A32 | `docs/devices/VR-WHEEL-SPEED-CONDITIONER.md` |
| 13.1 | ETB and APS: one shielded cable per device | `docs/SHIELD-RULES.md` |
| 18, 18.1 | MR-S EHPS pump: `k_eps` coil - switched by pump B5; `k_eps_en` (Ign 6, B12) enables it above ~400 rpm | `sot/channels.csv` b12, `k_eps` rows; `docs/OPEN-ITEMS.md` row 40 |
| 19 | Deleted: circuit opening relay, injector resistor pack, fuel pump resistor, fog lights | `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §5.6 |
| 20, 23, 32 | VRC boxes: Hammond 1590WUFL; ~~one DTM 8-way IN (key A) + one OUT (key B)~~ (superseded by S8 / R34 / S16: two CNLINKO LP-16 plugs); both VRCs mid-dash above the ECU; ECU at the factory ECM spot | VRC location: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md`; the 1590WUFL/DTM enclosure change is not yet in `docs/enclosures/` (`docs/OPEN-ITEMS.md`) |
| 25.1 | Doc policy: open questions may live in repo docs only if kept current; completed handoffs are removed; one project tracker | `docs/OPEN-ITEMS.md` |
| 26.1 | Start is ECU-controlled (`k_str`, Aux 8 A26); no clutch-start interlock; clutch switch stays a CSB3 input | `sot/channels.csv`, `docs/harness/rebuild/ST185-CSB3.harness` |
| 26.2 | OEM R/B No.2, No.3, No.4 removed; power windows/locks and blower get fuse + relay in the glove-box box; A/C fuse fed from the heater relay output | `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §8 |
| 26.3, 27 | Relays not driven directly by the Link: `k_acc` (pressure switch in series), `k_eps` (pump B5), heater (auto amp), headlight (IE1-2), horn (IE1-19), power (key IG), OEM R8 retract relay; everything else Link-direct. B28 senses IG2 at J/B1 1H-7 | `sot/channels.csv` b28 |
| 34 | Route drawings: every isometric route figure has a top view (RM305U1 p.IN-24 outline); markup code - blue line = route, blue arrow + black label = part spot, black box = instruction | `docs/harness/routes/`, lint `docs/harness/check_route_drawings.py`, skill `st185-apply-route-markup` |
| 35 | AntiTheft: status LED centre console, siren bay centre by the firewall, valet switch driver side, shock sensor beside the alarm module; siren/hood-pin leads through harness C's RH grommet | `docs/harness/rebuild/ST185-AntiTheft.harness` |
| 36.5 | Process: one ordered question queue; nothing answerable from the EWD, datasheets or SoT is asked | `docs/OPEN-ITEMS.md` |
| 38 | RTR fuse only (OEM R8 relay stays); tilt-away column on 30 A POWER; ECU wake IG2 -> diode, B28 before the diode, Aux 6 holds `k_efi`; B30 start request from ST1 through a 2 A box fuse | `sot/channels.csv` b28/b30, `ENGINE-ROOM-POWER-REDISTRIBUTION.md` §8.1 |
| 39 | No factory engine-bay wire reused | R11 above |
| 40 | All 14 routes approved 2026-10-10; harness update pass checklist (steps 1-4, 8, 9, 11 and the shield redraw done in PRs #73-#83) | remaining steps: `docs/OPEN-ITEMS.md` |
| 33, 36.4 | GEP PDM-R stack - superseded by fuse box Option B (2026-10-11) | `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §8.1 |

## Current state

The 2026-09-27 phased implementation plan is complete and was deleted 2026-10-11. Open work and
project history are tracked in `docs/OPEN-ITEMS.md`.
