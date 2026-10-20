# ST185 Harness Redesign - Decision Record

**Repo:** `st185-link-ecu-config`  
**Status:** The decision record. Open work and project history are in `docs/OPEN-ITEMS.md`.

## Binding rules B1-B30 (R226)

**In force: Dan approved this page on 2026-10-20 (#377).** It replaced the old rule section (R1-R226, the S-rows and
the 2026-09-28 audit table), which was deleted on 2026-10-20 (OPEN-ITEMS row 151); git history keeps their full text.
The retire map under the rules stays for good so every old citation still resolves.
Each rule gets trimmed to 2 lines or less in a later PR (Dan 2026-10-20); the substance stays.
At most 30 rules: adding one means merging or removing one (R226). Newest ruling won wherever two old rows disagreed.
A/C is left off this page on purpose (Dan: "ignore this"). **A/C, decided 2026-10-20 (Dan; closes Needs Dan N61):** the
compressor A/C amplifier A15 is removed and the Link G4X is the A/C controller. It drives the clutch relay `k_acc`
(B10 / Ign 8) and the condenser fan relay `k_fan2` (B13 / Ign 5). The A/C request (dash A/C switch V-G) goes opto board
IN3 -> CSB3 S2 -> 0x642 -> VDI2, and the evaporator thermistor A24 (pins 1-2) goes to CSB3 A1 with a 3.9 kOhm pull-up
to the CSB3 +5V -> 0x640; neither touches an ECU plug, and ECU A18, B31, B32 are spare. The 2-pin dual pressure switch
A5 stays in series with the `k_acc` coil feed from the POWER box ACPS 10 A, which also feeds the A/C switch; the switch
lamp sinks on the `k_acc` 85 / B10 net; the ambient sensor A1 gets new EngineRoom-C wires to its cowl leads. The auto A/C
amplifier (A31 / A32) and A23 keep the blower, air mix, mode and their sensors on factory wiring. The wires live in the
master, the CSB3 bits in the CAN files; the Link A/C logic is set at tune time.

### Scope and freeze

- **B1 Scope.** The project has four goals, in this order: (1) wiring sorted so Dan can build the harnesses; (2) ECU
  base maps; (3) ECU CAN config written and checked; (4) CSB3 config finished. A new `docs/OPEN-ITEMS.md` row is opened
  only for a blocker of one of them and starts with its tag `[G1]`-`[G4]`; anything else is mentioned to Dan, not added.
  Whether a part or box fits in the car is Dan's call at the build, never an agent item.
- **B2 Freeze.** Until the bloat cut is done (OPEN-ITEMS rows 151-155): no new rule, script, gate, doc, drawing format
  or feature; only the cut and Goal 1 blockers. A passing gate only proves the files agree with the scripts, not that
  the wiring is right; Dan's spot-check at the car is the proof (row 155).
- **B3 One home per fact.** A new document or source of truth replaces the older ones in the same PR: move what is
  still valid, delete the rest, fix every link. Nothing is archived or bannered "superseded"; git history is the
  archive. Retiring old versions, generated files, duplicates, scratch and empty files needs no OK - list them under
  "Retired" in the PR body (`git rm`; untracked files to the Recycle Bin). Dan's only copies, the SoT, these rules and
  anything outside this repo need his OK. Every ST185 file lives in this repo (working files in untracked `_research/`;
  CAD work in progress may sit in `C:\projects\_scratch`, but the final lands in `cad/`).
- **B4 Ask only real choices.** Read these rules and the docs first; never ask what a rule, the SoT or a maker document
  answers (look up maker drawings yourself, calculate cable sizes yourself, decide the obvious). A real question goes
  only in the "Needs Dan" table of `docs/OPEN-ITEMS.md`: running ID (A1..Z9, then wrap), multiple choice with one
  recommended letter; the row is deleted once answered and the answer lands here or in the SoT. Dispatch only relays and
  tracks; sessions do the thinking and the work (`docs/dispatch/DISPATCH-RULES.md`).

### Wiring and harness

- **B5 ONE wiring source of truth.** `docs/harness/MASTER-wirelist.csv`: one row per physical wire FROM end TO end (or
  per spare cavity), every harness. Each connector end has a meaningful ID, the real maker housing PN, the pin exactly
  as the maker numbers it and the terminal PN; a wire carries a net name only where it ends at a splice or bussed plug;
  every splice has a plain name; a power end is labelled by its real source, relay then fuse. Anything a maker document
  does not confirm is `TBD` plus the reason, never guessed. `sot/channels.csv` holds only the ECU channel settings and
  is checked against the master both ways. No script writes the master or `channels.csv`. When anything disagrees with
  the master, the other thing is wrong. Gate: `docs/harness/tools/check_wiring.py`.
- **B6 ONE drawing set, read back.** Every harness is drawn in ONE drawing set, `ST185-harness`, by our own generator
  `docs/harness/tools/build_drawings.py`: schematic, layout and pinout sheets from the master, never edited by hand,
  never a source. A change goes into the master first, then the set is regenerated. The read-back check compares every
  wire on the sheets with the master (both ends, connector, pin, gauge, colour, ident bands); any difference fails.
  harness.design is allowed only as an optional consumer: one wiring table per harness (13), generated from the master as
  a committed CSV (never hand-edited, checked by its generator's `--check`), with the .xlsx made on demand for
  harness.design import - built right after the bloat cut (OPEN-ITEMS row 158); the master stays the only source of
  truth. Wire list and pinout come first; the schematic layout does not chase perfection.
- **B7 The ECU harness and the bulkhead.** Loom A and loom B are ONE ECU harness: `AB-cabin` (ECU plugs A, B, C to the
  cabin half of the DRB102) and `AB-engine` (the engine half to every engine device). A, B and C are the ECU's plug names
  and ECU pins never move. The DRB102 is one 102-position bulkhead, accepted on its ratings; its cavities are grouped by
  device in route order, a circuit uses the same cavity number on both sides, the contact size must take the wire's
  gauge and current, and one cavity carries one net. A replacement bulkhead is only a complete matching set from the
  maker's datasheet. The cabin power splices sit at one ECU splice point by the plugs; Gnd Out A24 and B22 never tie.
- **B8 Routes and layout views.** The approved routes in `docs/harness/routes/` are Dan's: change one only from his
  markup (blue line = route, blue arrow + black label = part spot, black box = instruction; every isometric figure gets
  a top view). A harness follows its route: trunk, branch take-offs, which wires run together. Every layout and route
  top view is a true top view: front of the car on the RIGHT, driver (LH) side up, passenger side down. No branch doubles
  back, nothing overlaps or hides, parallel runs keep space unless they end at the same part, no bundle leg without a
  wire.
- **B9 Factory wiring.** No factory engine-bay wire, connector or box is reused: every engine-bay run is new wire.
  Kept: cabin J/B No.1 and No.3 and the under-dash wiring; what a kept J/B already feeds stays fed from it (its fuse,
  relay and pin). Gone and never a circuit source: every OEM relay block and engine-bay box (J/B No.2, R/B No.2-5, F11),
  the OEM ECU, EFI / circuit-opening / fuel pump relays and resistors, ABS, SRS, the cruise ECU, the combination meter,
  the OEM fan relays, the rear wiper and washer; front wipers and washer stay; no side marker lights. Kept OEM ground
  points: EA (M8 studs), EB, EC, ID, IE / IF, IG. Factory pin numbers come from the 1993 ST185 EWD (the 1990 / 1992 books
  are reading aids only). Every OEM cruise stalk function is kept. The rear lighting is a new harness; rear lamp ends
  are flying leads soldered to the factory bulb-socket pigtails; the turn flasher is a load-independent LED flasher in
  the stock socket. No center-cluster harness is drawn here.

### Power and grounds

- **B10 Grounds.** The ECU power grounds (A25, A34, B25, B34) join only each other at the ECU ground splice; ONE wire
  runs from it to the battery-negative bar in the POWER box. PCBs, CAN nodes, LEDs and other low-voltage electronics go
  to the battery-negative bus, never chassis. Sensors return to ECU Gnd Out only (A24 / B22). Shields go to drains only.
  High-current loads (motors, fans, pumps, lamps, horn, heater, coils) may use chassis ground at a kept OEM ground point.
- **B11 Fuses, power and stopping the engine.** Every fuse and relay is in the cabin: the glove-box POWER box (AMI bolt-in
  fuses for 30 A and up, Mini ISO relays, the battery-negative bus) and LOGIC box (mini blade fuses, micro relays). The
  one exception is the battery relay block for the fuel pump (`k_fp` and its 40 A fuse) in the trunk, passenger side,
  fed from the kill switch's load side. The alternator (170 A max) is fused at the POWER box (MEGA 175 A), never at the
  starter, and its path is sized by the load, not a sustained 170 A. The engine stops by the trunk kill switch
  (Longacre 52-45780: main pole battery +, second pole the alternator IG, alternator B+ on the load side) or by the key
  turned ON -> ACC (ECU ignition switch input); no separate stop input. The Raspberry Pi is on with the car and off with
  it, no hold relay. The cluster and the RealDash Pi get four wires at their connector: +12 V, ground, CAN H, CAN L.
- **B12 Wire gauge and splices.** Size every wire from the peak current of the high-performance device plus margin for
  heat, voltage drop and run length (more in the engine bay and on long runs); when two sizes are defensible take the
  larger; heavy cables are calculated, never asked. A wire behind a fuse is sized for that fuse (a relay coil feed behind
  a 15 A fuse is 16 AWG). The wire is chosen first, then a contact that takes it - never a thinner wire to suit a
  contact. A load fused above what its plug's terminals take runs fuse-sized wire to a splice and one pigtail of 150 mm
  or less, return included. A splice is sized by the combined gauge it joins (drains excepted); heat shrink over a joint
  is sized per end: the wires entering each end lie between the sleeve's recovered and supplied ID.
- **B13 Splices, seals and coverings.** Bussed DEUTSCH DT plugs only where the master has them (cabin SW12, the ECU +5 V
  rail, Gnd Out A and Gnd Out B); every other splice is soldered, and every engine-bay splice is soldered and wrapped in
  the loom covering. Wire seals only forward of the firewall (engine side of the DRB102), on every rear lamp connection
  and on every wheel-speed sensor connector (E-seal housings where the wire is thin); cabin connectors, the ECU plugs and
  the in-cabin fuel pump plug need none; DTM plugs use their built-in seals. Every bundle segment of 2+ conductors is
  covered in Raychem DR-25 and every 3- or 4-leg branch point gets a TE System 25 boot; nothing else is added unasked.
- **B14 Shields and drains.** Shielded (TE Raychem Spec 55 cable): crank, cam, knock, wheel speed, VRC outputs, turbo
  speed, flex fuel, gearbox VSS, ETB, APS pedal, the CAN-Lambda run and every CAN pair; injectors and coils none. A shield
  runs unbroken and ends only at the ECU, floating at the device: loom A drains to A7, loom B to B17, the CAN screens only
  to C1 through ONE trunk drain with each node's drain spliced on at its own branch; A and B shields never cross. A drain
  is its own `M22759/16-20-06` wire (found by its part, never its colour); no connector shell, no solder sleeve; 2+
  shields on one pin = one named splice and one drain wire. A cabin device that joins a loom part-way splices its drain
  where its signal wires join; a bulkhead device keeps its own drain and bulkhead pin up to the splice at the ECU plug.
  Each VRC box has one 5-pin CNLINKO LP-16 IN plug (pin 3 = both screens) and one OUT plug; its board is isolated from
  the case. Detail: `docs/SHIELD-RULES.md`.

### Relays

- **B15 Relays.** An ECU output that drives a relay is low-side: ECU pin -> coil 85, coil 86 -> fused +12 V (Aux 1-4
  are low-side only; Aux 5-8 set Low in PCLink); a CSB3 output sinks the same way. No external flyback diodes. Relay
  pins follow the maker drawing of the real blades: the POWER box Mini ISO relays and the heater relay take the feed on
  87 and switch out on 30 (heater 87a = ground, as the factory car). The latest fuse-box design (`cad/fusebox/src/spec.py`,
  `cad/fusebox/rev7/wiring_plan.json`) decides every harness connection to the boxes, slot names included.

### CAN

- **B16 CAN frames.** A CAN change on any device is reconciled against all four: Link ECU, center cluster, RealDash,
  ECUMaster CSB3 (`docs/RECONCILIATION-RULES.md` Rule 2, gate `bench/check_parity.py`). The cluster firmware as flashed
  is frozen and wins every conflict. CSB3 0x640-0x642 go to the ECU only; the cluster reads 0x3E8-0x3EB and 0x3EE and
  sends 0x3EC / 0x3ED; RealDash reads 0x3EB (gear byte only) and 0x3EF-0x3F1. The knock frame 0x3EE goes out every
  10 ms with no delay anywhere. RealDash units differ from the clusters on purpose, and the clusters' colour thresholds
  are display behaviour - neither is "fixed".
- **B17 CAN wiring.** The Link CAN-Lambda sits in the engine bay on CAN bus 1, shielded the whole run; CAN bus 2 is
  unused. Every CAN node (cluster, CSB3 + opto board, RealDash Pi, CAN-Lambda) takes its +12 V and ground WITH the CAN
  trunk, at its own branch point, together with its CAN H / L and its drain splice: trunk +12 V from the fuse box, trunk
  ground to the battery-negative bar, never the ECU ground or chassis.
- **B18 CAN config now, ECU settings at setup.** The ECU CAN configuration (receive and transmit channels, the CSB3
  switch bits) is written in the repo now - `link_g4x_can_setup.json` / `.lcs`, `switchboard_frames.json`, the CAN docs -
  with `bench/check_parity.py` green; Dan uploads the `.lcs` later. Only work that needs the ECU connected (PCLink help,
  the import, live tests, tuning, adjustable outputs like the EPS speed pulse) waits for setup time; outputs are named by
  connector + pin and / or the QSG label ("B12 / Ign 6").

### ECU pins

- **B19 ECU pins.** Every circuit with a wire on an ECU pin (Link G4X plugs A / B / C) is checked against the Link G4X
  Quick Start Guide and the G4X plug-in guides (the plug-in guide wins for special circuits and pin modes): function and
  mode, what it may connect to, current limit, wire gauge. A mismatch is a stop: do not draw it, ask. Only G4X documents
  for pins and wiring (never G4 / G4+ pages). Resistors only where physically needed, never where the ECU already pulls
  up or down, drawn with a full path and on the BOM. A 12 V-active switch into a ground-active input goes through an
  optoisolator.

### Wire and parts

- **B20 Wire, colours and ident bands.** Wire is `M22759/16-<AWG>-<colour code>` Tefzel; battery cable stays `BC-*`.
  Seven solid colours by function, no stripes: Red +12 V power; Black power / chassis ground and drains; Orange sensor
  supply (+5 V, +8 V); Blue sensor ground and signal returns; White every signal and ECU output; Green CAN H and CAN L;
  Yellow switch inputs. Every wire carries its circuit's ident bands (Blue / Yellow / White, 1-4 bands, `ident_bands`
  in the master) at every end of the circuit; a code is unique within a drawing, the shortest codes go to the circuits
  with the most wires; 6 AWG and heavier carry none.
- **B21 Picking parts.** Order: Dan's on-hand TE list (`docs/sourcing/te-on-hand-bom.csv`, never ask for counts) -> TE
  (free samples first) -> Dan's approved suppliers (`docs/sourcing/README.md`) -> others only with a stated reason. Never
  guess a part number: unverified = `TBD` + the reason. A spec read off a non-maker listing is checked against the
  maker's sheet, else a source on `docs/sourcing/TRUSTED-SOURCES.md`, else two more independent sources; once validated,
  also check Amazon / AliExpress / eBay for price. A number with no maker sheet, official model or measurement behind it
  is marked UNVERIFIED. Every part must be real and buyable; a part description describes the part, never its use. BOM:
  parts made at work cost $0; labels and ident bands are not priced.

### Drawings and CAD

- **B22 Wire-end labels, clean sheets.** Every wire end says where THAT end lands in the car: a device pin as device +
  connector + pin + signal; another harness or the bulkhead as connector + pin + what and where; an OEM end as location,
  connector, pin, EWD description and page; a stud or lug as what it is, where, and its EWD ID; a splice says what it
  joins. Never a generic word ("broken off", "loose", "see other", bare "GND" / "Signal" / "Power"), a bare pin code or
  an internal id; unknown = `TBD - <what to check>`. A sheet carries only what Dan asked for: no unused part, no "not
  used" entry, no extra splice.
- **B23 Models drive drawings.** For CAD the model is the master: every physical change (a dimension, a feature, a part
  added, removed, moved or swapped) is made in the model and merged first; the drawing is then regenerated from it,
  never hand-edited. Rev letters: A only for a new model, then B, C ... skipping I, L, O, Q, after Z AA, AB ...; a
  drawing-only clerical change adds .01, .02, is not listed in the rev log and needs no model change; no rev in any file
  name. Each model keeps `<pn>.REVLOG.md` (one row per release, Rev A "Initial") and `MADE-WITH.md`; every fabricated
  assembly has an assembly drawing, reissued with its parts. Gate: `cad/check_drawings_current.py`.
- **B24 Initials and revision marks.** DRAWN is the person on Rev A and never changes; every rev-log BY is the person
  who asked for the change - for this project always `DG`, read from `%USERPROFILE%\.drawing-initials` (env
  `DRAWING_INITIALS` overrides). Never an agent or tool name; an agent with no file STOPS and asks. Every full-letter
  rev from 2026-10-19 on puts its letter in a triangle next to each changed item and BOM row; old triangles stay. Gate:
  `cad/check_drawing_rules.py` K4 / K5.
- **B25 What a drawing shows.** No hidden lines (center marks and center lines are fine); tangent edges in trimetric
  views; no mesh facets - parts look like smooth machined bodies. Every bought part is the maker's own model, never an
  envelope. A balloon only where its part is clearly visible, its leader on that part, balloons never overlapping;
  mostly assembled views balloon only the primary parts. Fuse box sheets label each fuse and relay with its circuit and
  each wire landing with its harness end label, from the SoT. NOTES say only how to make, fit or check the part, in
  plain shop words; change history goes in the rev log; no note about anything not in the model (no pin / socket gender
  note, no unmodelled edge break, no screw that is not modelled). Gate: `cad/check_drawing_rules.py`.
- **B26 CAD work.** CAD scripts and models stay frozen unless Dan asks for CAD work. Every model has a row in
  `cad/README.md` (its `Selected for build` flag is the only place the build choice lives) and a trimetric PNG rendered
  from its STEP; re-render only the views that changed. Fusion allows 10 editable documents: reuse the part's document,
  never make throwaway ones, list finished ones for Dan to set read-only. Heavy CAD (STEP, STL, `.f3d`) stays gitignored
  in the main checkout's `cad/`. Bought-part models come from the maker by shell download into `cad/vendor/` (never a
  browser download; login-only files go on its "Dan to download" list). Fairsolid CAD jobs go to the Grok bot as a
  handoff zip, listed in `docs/status/grok-jobs.json`. Wiring and CAD work runs on Opus.
- **B27 Fuse boxes and printed parts.** As small as sensible. Printed parts are PA12 on Dan's HP MJF printer: no printed
  threads (heat-set inserts or captured nuts), >= 0.5 mm between faces, nothing floats, free-standing walls get a root
  fillet, snap hooks stay inside the HP strain limit. The 2.0 mm wall minimum applies to structural, sealing, retention
  and circuit-separating walls only; any other thin spot is flagged for Dan, never passed silently. Live parts at
  different potential keep >= 3 mm apart (one ground node: 1.5 mm between lugs); clearance rules never apply to
  plastic. Current runs copper to copper on clamped faces, never through threads; bars are tinned stock copper, cut and
  drilled. Terminals lock themselves in cavities sized by everything that passes through; relays and fuses are held by
  blade friction; every ring lug sits in a pocket. The design detail is in `cad/fusebox/src/spec.py`; gates in
  `tools/check_all.py`.

### Shipping

- **B28 Shipping a change.** Work on a branch cut from `origin/main`; `python tools/check_all.py` and
  `python bench/check_parity.py` green before the commit. `main` is protected: every change is a PR whose body has a
  `Rows: <n>, <n>` or `Rows: none` line, squash-merged once "Repo checks" and "Protect research hub" are green. Before
  the PR, update what the work touched (OPEN-ITEMS rows, a new Dan rule here). A session never removes its own
  worktree or branch; `tools/hygiene.ps1` cleans up afterwards.
- **B29 Tracker, hub and generated files.** `docs/OPEN-ITEMS.md` is the one tracker: open rows, the "Needs Dan" table and
  the dated history. The research hub (`docs/research-hub.html`) is generated and committed only by its bot; keep it and
  the tracker fresh, short and visual. Generated files (the hub, `docs/harness/drawings/`, the project BOM) are never
  hand-edited - re-run their generator.
- **B30 Past decisions.** The dated rows that stood here before (R1-R226, S1-S40, the 2026-09-28 audit rows 1-2) are
  retired into the map below; git history of this file keeps their full text. What they decided lives in the file they
  changed: wiring in the master, ECU settings in `sot/channels.csv`, CAN in the CAN files, CAD in the `cad/` specs and
  rev logs. Reversing an applied decision is a question for Dan, never a silent edit.

### Retire map (permanent)

Every old rule ID and where it went. "dropped" = no longer binding, with the reason; "A/C" = left off this page,
decided 2026-10-20 in the A/C line above (N61 closed). Read an old citation (e.g. "DECISIONS R154") through this table.

| Old | Now | Note |
|---|---|---|
| R1 | B7 | ECU letter split, amended by R220 |
| R2 | B7 | |
| R3 | dropped | cross-file broken-off ends; one drawing set (R225), `passes_through` in the master |
| R4 | B7 | |
| R5 | B7 | |
| R6 | B7 | APS pins fixed |
| R7 | B9 | |
| R8 | B7 | |
| R9 | B7 | |
| R10 | B7 | |
| R11 | B9 | |
| R12 | B9 | OEM ground points in B9 |
| R13 | B9 | its A/C amp part: A/C (decided 2026-10-20, A/C line at the top) |
| R14 | B9 | |
| R15 | B11 | |
| R16 | B9 | |
| R17 | B30 | alternator plug: applied; the facts live in the file it changed |
| R18 | - | removed before R226 (git history) |
| R19 | B11 | |
| R20 | B11 | |
| R21 | B30 | ECU starts the engine, no clutch interlock: applied; the facts live in the file it changed |
| R22 | B30 | EPS pump wiring: applied; the facts live in the file it changed |
| R23 | A/C | A/C - left off the page; decided 2026-10-20 (A/C line at the top) |
| R24 | B17 | |
| R25 | B15 | |
| R26 | B19 | |
| R27 | B14 | |
| R28 | B14 | |
| R29 | B14 | |
| R30 | B14 | build method: `docs/SHIELD-RULES.md` |
| R31 | B14 | |
| R32 | B14 | |
| R33 | B14 | |
| R34 | B14 | |
| R35 | B20 | |
| R36 | B12 | |
| R37 | B12 | |
| R38 | B21 | |
| R39 | dropped | the harness.design part library goes with `rebuild/` (R225) |
| R40 | B4 | also B21 |
| R41 | dropped | dropped - harness.design is gone (R225) |
| R42 | B8 | |
| R43 | dropped | dropped - harness.design is gone (R225) |
| R44 | B22 | coverings: B13 |
| R45 | B5 | also B6 |
| R46 | B3 | |
| R47 | B8 | |
| R48 | B21 | |
| R49 | B22 | |
| R50 | dropped | dropped - harness.design is gone (R225) |
| R51 | B16 | |
| R52 | B18 | |
| R53 | B9 | |
| R54 | B9 | |
| R55 | B9 | |
| R56 | B19 | brake via the CSB3: B30 |
| R57 | B11 | |
| R58 | B30 | door lock / tilt-away feed: applied; the facts live in the file it changed |
| R59 | B9 | EA = M8 |
| R60 | B14 | VRC LP-16 plugs |
| R61 | B9 | |
| R62 | B9 | |
| R63 | B12 | |
| R64 | B11 | |
| R65 | B16 | |
| R66 | B9 | |
| R67 | B3 | also B26 |
| R68 | B16 | |
| R69 | dropped | harness.design 100-connection split (R220, R225) |
| R70 | - | removed before R226 (git history) |
| R71 | B11 | |
| R72 | B27 | |
| R73 | B27 | |
| R74 | B26 | |
| R75 | B11 | |
| R76 | B27 | |
| R77 | B26 | |
| R78 | - | removed before R226 (git history) |
| R79 | B27 | fuse box rev 4 review: applied; the facts live in the file it changed |
| R80 | B18 | |
| R81 | B27 | fuse box rev 5 review: applied; the facts live in the file it changed |
| R82 | B21 | |
| R83 | B26 | |
| R84 | B30 | power package view: the `cad/README.md` table |
| R85 | B30 | fuse box rev 6 parts: applied; the facts live in the file it changed |
| R86 | - | removed before R226 (git history) |
| R87 | B20 | its harness.design label part dropped (R225) |
| R88 | dropped | no PDF export (R103), dropped - harness.design is gone (R225) |
| R89 | dropped | circuit tracer deferred; OPEN-ITEMS row 117 keeps it |
| R90 | B30 | approval of the harness.design drawings superseded by R224 / R225 |
| R91 | B11 | |
| R92 | dropped | dropped - harness.design is gone (R225) |
| R93 | B27 | |
| R94 | B27 | |
| R95 | B8 | |
| R96 | B12 | |
| R97 | B11 | |
| R98 | B16 | |
| R99 | dropped | circuit tracer deferred; OPEN-ITEMS row 117 |
| R100 | B16 | cluster fix flashed = frozen baseline |
| R101 | B27 | |
| R102 | B1 | |
| R103 | dropped | dropped - harness.design is gone (R225) |
| R104 | - | removed before R226 (git history); replaced by R217 |
| R105 | B30 | RealDash 200 kPa tile, ruleset: applied; the facts live in the file it changed |
| R106 | B26 | |
| R107 | B8 | |
| R108 | - | removed before R226 (git history) |
| R109 | B1 | |
| R110 | dropped | dropped - harness.design is gone (R225) |
| R111 | dropped | dropped - harness.design is gone (R225) |
| R112 | B26 | |
| R113 | B4 | Dispatch detail: `docs/dispatch/DISPATCH-RULES.md` |
| R114 | B29 | |
| R115 | B4 | |
| R116 | dropped | dropped - harness.design is gone (R225) |
| R117 | B9 | back-up switch plug: B30 |
| R118 | B28 | |
| R119 | B4 | also B29 |
| R120 | B27 | |
| R121 | B27 | |
| R122 | B30 | cover backup screws: applied; the facts live in the file it changed |
| R123 | B27 | |
| R124 | B22 | |
| R125 | B22 | |
| R126 | B30 | VRC board holder: applied; the facts live in the file it changed |
| R127 | B27 | |
| R128 | B27 | |
| R129 | B27 | PEM nuts: applied; the facts live in the file it changed |
| R130 | B27 | |
| R131 | B30 | VRC holder height: applied; the facts live in the file it changed |
| R132 | B30 | CSB3 lid loft: applied; the facts live in the file it changed |
| R133 | B30 | CSB3 board supports: applied; the facts live in the file it changed |
| R134 | B30 | applied; the facts live in the file it changed |
| R135 | B27 | |
| R136 | B30 | applied; the facts live in the file it changed |
| R137 | B30 | applied; the facts live in the file it changed |
| R138 | B25 | R191 wins on the note half |
| R139 | B3 | |
| R140 | B8 | |
| R141 | - | removed before R226 (git history) |
| R142 | B30 | RADLOK pass-through: applied; the facts live in the file it changed |
| R143 | B28 | |
| R144 | - | removed before R226 (git history) |
| R145 | B27 | |
| R146 | - | removed before R226 (git history) |
| R147 | B23 | |
| R148 | B23 | |
| R149 | B23 | |
| R150 | B25 | |
| R151 | B27 | |
| R152 | B23 | smooth bodies: B25 |
| R153 | B8 | |
| R154 | B8 | endpoints: B5 |
| R155 | B27 | C-strap: applied; the facts live in the file it changed |
| R156 | B22 | |
| R157 | B27 | |
| R158 | B30 | cover catches: applied; the facts live in the file it changed |
| R159 | B27 | |
| R160 | B27 | |
| R161 | B11 | |
| R162 | B11 | |
| R163 | B21 | also B25, B26 |
| R164 | B15 | |
| R165 | B15 | |
| R166 | B30 | MCP 2.8 receptacles: applied; the facts live in the file it changed |
| R167 | B21 | |
| R168 | B15 | |
| R169 | B13 | |
| R170 | B15 | HEAD relay 5th blade: applied; the facts live in the file it changed |
| R171 | B13 | |
| R172 | dropped | harness.design fan limit; accepted as drawn |
| R173 | B13 | |
| R174 | B14 | |
| R175 | B13 | |
| R176 | B30 | 12 AWG bulkhead feeds: applied; the facts live in the file it changed |
| R177 | B12 | |
| R178 | B9 | |
| R179 | B8 | |
| R180 | dropped | retired by R221 before R226 |
| R181 | B27 | |
| R182 | B23 | |
| R183 | B23 | |
| R184 | B25 | |
| R185 | B25 | |
| R186 | B25 | |
| R187 | B25 | |
| R188 | B25 | |
| R189 | B25 | |
| R190 | B25 | |
| R191 | B25 | |
| R192 | B25 | |
| R193 | B25 | |
| R194 | B25 | |
| R195 | B25 | |
| R196 | B23 | |
| R197 | B23 | |
| R198 | B27 | C-strap PEM edge: applied; the facts live in the file it changed |
| R199 | B30 | C-strap studs / nut holder: applied; the facts live in the file it changed |
| R200 | B24 | |
| R201 | B5 | |
| R202 | B6 | |
| R203 | B5 | |
| R204 | B15 | |
| R205 | A/C | A/C - left off the page; decided 2026-10-20 (A/C line at the top) |
| R206 | B5 | |
| R207 | B14 | |
| R208 | B7 | |
| R209 | B20 | |
| R210 | B21 | |
| R211 | B3 | |
| R212 | B19 | |
| R213 | B10 | |
| R214 | B12 | resistors: B19 |
| R215 | B11 | |
| R216 | B10 | |
| R217 | B17 | also B10 |
| R218 | - | removed before R226 (git history); loom A-B crossing gate, 2026-10-19 |
| R219 | B15 | |
| R220 | B7 | |
| R221 | B5 | |
| R222 | B4 | |
| R223 | B30 | gearbox VSS on switched 12 V, DI 8 pull-up ON: applied; the facts live in the file it changed; Link check open in OPEN-ITEMS |
| R224 | B2 | the ONE drawing set and read-back: B6 |
| R225 | B6 | amended by Dan 2026-10-20: harness.design only as an optional consumer of generated per-harness tables |
| R226 | B2 | this page |
| S1 | B18 |  |
| S2 | B18 |  |
| S3 | B30 | front WSS plug: applied; the facts live in the file it changed |
| S4 | B30 | +5 V load estimate; setup-time check in OPEN-ITEMS |
| S5 | B13 |  |
| S6 | B12 |  |
| S7 | - | removed before R226 (git history) |
| S8 | B14 | VRC harness pieces: B30 |
| S9 | B14 |  |
| S10 | B7 |  |
| S11 | dropped | shared connector drawn whole in every file; one drawing set (R225) |
| S12 | B14 |  |
| S13 | B22 |  |
| S14 | dropped | LMI fuse block replaced by the POWER box (R91) |
| S15 | B9 |  |
| S16 | B14 | LP-16 part picks: B30 |
| S17 | B9 | Route 15 answers: B30 |
| S18 | B30 | alternator plug and wires: applied; the facts live in the file it changed |
| S19 | B30 | wiper / washer spots: applied; the facts live in the file it changed |
| S20 | B12 |  |
| S21 | B11 |  |
| S22 | B16 |  |
| S23 | B9 | cruise ladder and fuel level values: B30 |
| S24 | B30 | B30 / B28 inputs: applied; the facts live in the file it changed |
| S25 | B19 | opto board: B30 |
| S26 | B30 | enclosure answers: applied; the facts live in the file it changed |
| S27 | B30 | applied; the facts live in the file it changed |
| S28 | A/C | A/C - left off the page; decided 2026-10-20 (A/C line at the top) |
| S29 | B30 | applied; the facts live in the file it changed |
| S30 | B30 | VRC IN / OUT labels: applied; the facts live in the file it changed |
| S31 | dropped | dropped - harness.design is gone (R225) |
| S32 | B30 | machined enclosures: applied; the facts live in the file it changed |
| S33 | B30 | applied; the facts live in the file it changed |
| S34 | B15 |  |
| S35 | A/C | A/C - left off the page; decided 2026-10-20 (A/C line at the top) |
| S36 | B30 | applied; the facts live in the file it changed |
| S37 | dropped | `validate_sot.py` replaced by `check_wiring.py` (R221) |
| S38 | B30 | applied; the facts live in the file it changed |
| S39 | - | removed before R226 (git history) |
| S40 | B11 |  |
| Audit row 1 (2026-09-28 table) | B17 | CAN-Lambda bulkhead pins: B30 |
| Audit row 2 (2026-09-28 table) | B7 | DRB102 accepted on its ratings |
