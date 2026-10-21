# ST185 Harness Redesign - Decision Record

**Repo:** `st185-link-ecu-config`  
**Status:** The decision record. Open work and project history are in `docs/OPEN-ITEMS.md`.

## Binding rules B1-B30 (R226)

**In force: Dan approved this page on 2026-10-20 (#377).** It replaced the old rule section (R1-R226, the S-rows and
the 2026-09-28 audit table), which was deleted on 2026-10-20 (OPEN-ITEMS row 151); git history keeps their full text.
The retire map under the rules stays for good so every old citation still resolves.
Each rule is 2 lines or less (Dan 2026-10-20): detail lives in the file the rule names, older wording in git history.
At most 30 rules: adding one means merging or removing one (R226). Newest ruling won wherever two old rows disagreed.
Surgical rewire (Dan 2026-10-20): keep the OEM body wiring, replace only the engine-bay wiring (B1, B5, B7, B9, B11).
A/C: both factory A/C amps stay (Dan 2026-10-20); how the Link feeds the compressor amp A15 is open (Needs Dan N61).

### Scope and freeze

- **B1 Scope.** Keep the OEM body wiring, replace only the engine-bay wiring; new wire only for the engine harness, fuel
  pump, dash feed (cluster, LEDs, Pi), CAN, alarm and taps. Goals G1 wiring, G2 maps, G3 CAN, G4 CSB3; rows for blockers.
- **B2 Freeze.** Until the bloat cut is done (OPEN-ITEMS rows 151-155): no new rule, script, gate, doc, drawing format
  or feature; only the cut and G1 blockers. A green gate is no proof; Dan's spot-check at the car is (row 155).
- **B3 One home per fact.** A new doc or SoT replaces older ones in the same PR; no archives (git history is one).
  Retiring files: `AGENTS.md` (R46). Every ST185 file lives in this repo (CAD work in progress may sit in `_scratch`).
- **B4 Ask only real choices.** Never ask what a rule, the SoT or a maker document answers: look it up or work it out. A
  real question goes in the OPEN-ITEMS "Needs Dan" table as lettered options with one recommended.

### Wiring and harness

- **B5 ONE wire list.** `docs/harness/MASTER-wirelist.csv` holds every new wire, cut, reuse and tap with its EWD page; no
  row, no cut. Reuse an OEM wire only if its gauge fits and both ends are known. `sot/channels.csv` = ECU settings.
- **B6 ONE drawing set, read back.** `ST185-harness` is generated from the master by `build_drawings.py`, never
  hand-edited; `--check` reads every wire back. Wire list and pinout first; harness.design only as a generated consumer.
- **B7 ECU harness and bulkhead.** Loom A + B = ONE harness, `AB-cabin` + `AB-engine`; ECU pins never move. Firewall:
  DRB102, or 1-2 smaller bulkheads from Dan's on-hand parts first, sized from the new-wire count (Rule 3).
- **B8 Routes and views.** A route (`docs/harness/routes/`) changes only from Dan's markup; the harness follows it. Top
  views: front RIGHT, driver side up. No doubling back, overlap, hidden or empty leg; parallel runs spaced.
- **B9 Boundary.** No OEM wire crosses into the engine bay; every engine-bay circuit is new wire on one main route. Only
  the Engine Room Main outer loop stays. Kept: cabin wires, J/B No.1/3, R/B No.2-4; list: README; pins: 1993 EWD.

### Power and grounds

- **B10 Grounds.** ECU power grounds (A25, A34, B25, B34) splice together, one wire to the POWER box battery-negative
  bar. Electronics to the battery-negative bus, sensors to Gnd Out, shields to drains; heavy loads may use chassis.
- **B11 Power.** New circuits: glove-box POWER / LOGIC boxes (+ trunk `k_fp`, 40 A). Kept OEM circuits stay on their J/B
  fuses; one that lost its feed gets a glove-box feed or a listed J/B tap. Alternator MEGA 175 A; stop: kill or ACC.
- **B12 Wire gauge.** Size a wire for the device's peak current plus margin (when in doubt, the larger) and at least for
  its fuse. Wire first, then a contact that takes it, else a fuse-sized splice + pigtail of 150 mm or less.
- **B13 Splices, seals, covering.** Bussed DT plugs only where the master has them; other splices soldered. Seals only
  forward of the firewall and on rear lamp / wheel-speed plugs. DR-25 on 2+ wire runs, System 25 boots at branches.
- **B14 Shields and drains.** Shielded cable where `docs/SHIELD-RULES.md` lists it; a shield runs unbroken, floats at
  the device and ends only at A7 (loom A), B17 (loom B) or C1 (CAN) through its own drain wire.

### Relays

- **B15 Relays.** An ECU or CSB3 output drives a relay low-side (Aux 1-4 are low-side only, Aux 5-8 set Low): pin ->
  coil 85, 86 -> fused +12 V; no flyback diodes. Relay pins per maker drawing; boxes per `cad/fusebox/`.

### CAN

- **B16 CAN frames.** Any CAN change reconciles across ECU, cluster, RealDash, CSB3 (Rule 2); frozen cluster wins. CSB3
  0x640-0x642 -> ECU; cluster reads 0x3E8-0x3EB, 0x3EE, sends 0x3EC/0x3ED; RealDash 0x3EB gear, 0x3EF-0x3F1.
- **B17 CAN wiring.** One bus (CAN 1, bus 2 unused), the CAN-Lambda on it, shielded the whole run. Every CAN node takes
  +12 V (fuse box) and ground (battery-negative bar) with the trunk at its branch, never ECU ground or chassis.
- **B18 CAN config now.** The ECU CAN config is written in the repo now (`link_g4x_can_setup.json` / `.lcs`,
  `switchboard_frames.json`, `check_parity.py` green); only work that needs the ECU connected waits for setup.

### ECU pins

- **B19 ECU pins.** Check every ECU-pin circuit against the G4X Quick Start Guide and plug-in guides (plug-in wins;
  never G4 / G4+ pages); a mismatch is a stop. Resistors only where needed; 12 V switch into a ground input via opto.

### Wire and parts

- **B20 Wire and colours.** `M22759/16` Tefzel (battery `BC-*`), solid colours: Red +12 V, Black ground / drain, Orange
  sensor supply, Blue sensor return, White signal, Green CAN, Yellow switch in. Ident bands at circuit ends, not 6 AWG+.
- **B21 Picking parts.** Order and validation per `docs/sourcing/README.md` (on hand, TE, Dan's suppliers, else a stated
  reason). Never guess a PN: unverified = `TBD` + reason; every part real and buyable; parts made at work cost $0.

### Drawings and CAD

- **B22 End labels, clean sheets.** Each wire end says where that end lands (device, connector, pin, signal; OEM end +
  EWD ID; splice: what it joins), never a generic word or internal id; unknown = `TBD - <what>`. Only asked-for parts.
- **B23 Models drive drawings.** The CAD model is the master: a physical change goes in the model first, then the
  drawing is regenerated, never hand-edited. Revs: `cad/DRAWING-RULES.md`; gate `check_drawings_current.py`.
- **B24 Initials and revision marks.** DRAWN and every rev-log BY are a person, always `DG` (`.drawing-initials`), never
  an agent; no file = stop and ask. Full-letter revs from 2026-10-19 get rev triangles (`cad/DRAWING-RULES.md`).
- **B25 What a drawing shows.** As `cad/DRAWING-RULES.md` lists: no hidden lines or mesh facets, tangent edges in
  trimetrics, makers' own models, balloons only on visible parts, shop-only NOTES. Gate `check_drawing_rules.py`.
- **B26 CAD work.** CAD stays frozen unless Dan asks. Every model has a `cad/README.md` row and a trimetric PNG; heavy
  files stay gitignored; bought parts are maker models in `cad/vendor/`; reuse Fusion documents (10 max).
- **B27 Fuse boxes and printed parts.** As small as sensible; PA12 on Dan's HP MJF, no printed threads; live parts >= 3
  mm apart; current copper to copper, never through threads. Detail: `cad/fusebox/src/spec.py` and its gates.

### Shipping

- **B28 Shipping a change.** Branch from `origin/main`; `check_all.py` and `check_parity.py` green; update touched
  OPEN-ITEMS rows; PR with a `Rows:` line, squash-merged when both required checks pass. Never remove your own worktree.
- **B29 Tracker, hub, generated files.** `docs/OPEN-ITEMS.md` is the one tracker (open rows, Needs Dan, history), kept
  short. The hub, drawings and BOM are generated, never hand-edited; only the bot commits the hub.
- **B30 Past decisions.** Old R1-R226, S1-S40 and audit rows resolve through the retire map below (full text in git
  history); what they decided lives in the files they changed. Reversing an applied decision is Dan's call.

### Retire map (permanent)

Every old rule ID and where it went. "dropped" = no longer binding, with the reason; "A/C" = left off this page,
open as Needs Dan N61. Read an old citation (e.g. "DECISIONS R154") through this table.

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
| R13 | B9 | its A/C amp part: A/C, Needs Dan N61 |
| R14 | B9 | |
| R15 | B11 | |
| R16 | B9 | |
| R17 | B30 | alternator plug: applied; the facts live in the file it changed |
| R18 | - | removed before R226 (git history) |
| R19 | B11 | |
| R20 | B11 | |
| R21 | B30 | ECU starts the engine, no clutch interlock: applied; the facts live in the file it changed |
| R22 | B30 | EPS pump wiring: applied; the facts live in the file it changed |
| R23 | A/C | A/C - left off the page (Needs Dan N61) |
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
| R205 | A/C | A/C - left off the page (Needs Dan N61) |
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
| S28 | A/C | A/C - left off the page (Needs Dan N61) |
| S29 | B30 | applied; the facts live in the file it changed |
| S30 | B30 | VRC IN / OUT labels: applied; the facts live in the file it changed |
| S31 | dropped | dropped - harness.design is gone (R225) |
| S32 | B30 | machined enclosures: applied; the facts live in the file it changed |
| S33 | B30 | applied; the facts live in the file it changed |
| S34 | B15 |  |
| S35 | A/C | A/C - left off the page (Needs Dan N61) |
| S36 | B30 | applied; the facts live in the file it changed |
| S37 | dropped | `validate_sot.py` replaced by `check_wiring.py` (R221) |
| S38 | B30 | applied; the facts live in the file it changed |
| S39 | - | removed before R226 (git history) |
| S40 | B11 |  |
| Audit row 1 (2026-09-28 table) | B17 | CAN-Lambda bulkhead pins: B30 |
| Audit row 2 (2026-09-28 table) | B7 | DRB102 accepted on its ratings |
