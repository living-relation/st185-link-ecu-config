# ST185 Harness Redesign - Decision Record

**Repo:** `st185-link-ecu-config`  
**Status:** The one rules and decisions file (`AGENTS.md` points here). Open work is in `docs/OPEN-ITEMS.md`.

## Binding rules B1-B30 (R226)

**In force: Dan approved this page on 2026-10-20 (#377).** It replaced the old rule section (R1-R226, the S-rows and
the 2026-09-28 audit table), which was deleted on 2026-10-20 (OPEN-ITEMS row 151); git history keeps their full text.
The retire map under the rules stays for good so every old citation still resolves.
Each rule is 2 lines or less (Dan 2026-10-20): detail lives in the named sections of this file; older wording is in git history.
At most 30 rules: adding one means merging or removing one (R226). Newest ruling won wherever two old rows disagreed.
Surgical rewire (Dan 2026-10-20): forward of the firewall every wire is new; keep the OEM cabin / body wiring (B1, B5, B7, B9, B11).
A/C: both factory A/C amps stay (Dan 2026-10-20). D16 (Dan 2026-10-25): A15 drives `k_acc` (pin 8 to coil 85); the Link only sends the ACT kill (Aux 4); pin 2 hard-grounded; Ign 8 is tacho to pin 18; no clutch-on to the Link. Lock sensor (Dan 2026-10-26): same tacho through 4.7 kΩ to A15 pin 9 (OPEN-ITEMS History 2026-10-21 N61). Sensor common: keep cabin splice `SP-AC-SG` (replaces E10). The A/C pressure switch is the factory trinary switch, wired to the factory A/C amp; factory yellow-red is that switch output (A5 pin 4 through joiner E10 to A18 pin 13), not the sensor ground; sensor common is yellow (1990 ST185 EWD p.150 / p.152; 1992 EWD132U p.219). Clutch (Dan 2026-10-26): one ECU clutch input only — cruise clutch switch C17 to CSB3 pin 20 (VDI6) for flat-shift; clutch start switch C11 completes the starter circuit in hardware and is not an ECU input. Oil warning LED on CSB3 L4 (cavity 26, 0x643 byte 3). Brake fluid level switch is a factory safety item, not needed, not connected.

### Scope and records

- **B1 Scope.** Forward of the firewall every wire is new, on a named route (B9); keep the OEM cabin / body wiring.
  New wire also for fuel pump, dash feed, CAN, alarm and taps. Goals G1-G4; rows for blockers.
- **B2 Record at once** (Dan 2026-11-02, G1 b; replaces the freeze, which ended 2026-11-02, Dan B10 a). A rule or design decision
  Dan makes is written into this file (or the README it belongs in) and merged in the same session, never left only in memory or a handoff.
- **B3 One home per fact.** A new doc or SoT replaces older ones in the same PR; no archives (git history is one).
  Every ST185 file lives in this repo, except CAD models (B26); scratch is disposable only. Detail: "Where data lives (B3)" below.
- **B4 Ask only real choices.** Never ask what a rule, the SoT or a maker document answers, and never ask Dan to test or
  measure at the car (it is apart; Dan 2026-11-02): look it up (EWD, FSM, maker docs) or work it out. Real questions: OPEN-ITEMS "Needs Dan", lettered, one recommended.

### Wiring and harness

- **B5 ONE wire list.** `docs/harness/MASTER-wirelist.csv` holds every new wire, cut, reuse and tap with its EWD page; no
  row, no cut. Reuse an OEM wire only if its gauge fits and both ends are known. `sot/channels.csv` = ECU settings.
- **B6 Built in harness.design.** Every harness is built in harness.design from the master (Dan 2026-11-01), one at a
  time; our layout / schematic PDFs are retired. Detail: "harness.design files (B6)" below.
- **B7 ECU harness and bulkhead.** Loom A + B = ONE harness, `AB-cabin` + `AB-engine`; ECU pins never move. Firewall:
  one DRB102 (Dan B5 a, 2026-11-02; replaces the on-hand smaller-bulkhead option), cavities per Rule 3 below.
- **B8 Routes and views.** A route (route file or saved placement) changes only from Dan's markup or placement; lengths
  follow it, the formboard view does not (README). Detail: "Harness ownership (B8 list)" and "Placement and lengths" below.
- **B9 Boundary.** Forward of the firewall every wire is new, on a named route; OEM wire stays only as 6 in pigtails at
  lamps, pop-ups, ambient sensor and wiper. Kept: cabin wires, J/B1 / J/B3, R/B2 / R/B4. Removed: README. Pins: 1993 EWD.

### Power and grounds

- **B10 Grounds.** ECU power grounds splice to one wire to the POWER box battery-negative bar; Gnd Out takes only the
  return of a sensor the ECU powers, 12 V devices ground on the battery-negative bus. Detail: "Grounds (B10)" below.
- **B11 Power.** New circuits: glove-box POWER / LOGIC boxes (+ trunk `k_fp`, 40 A). Kept OEM circuits stay on their J/B
  fuses; one that lost its feed gets a glove-box feed or a listed J/B tap. Alternator MEGA 175 A; stop: kill or ACC.
- **B12 Wire gauge (Dan 2026-10-30).** The device and its wire set the circuit: size for the realistic peak load, drop to what
  the device's own contacts take; every contact end to end takes that wire and the fuse protects it. Steps and cases: "Gauge cases" below.
- **B13 Splices, seals, covering.** Bussed DT plugs only where the master has them; other splices soldered. Seals only
  forward of the firewall and on rear lamp / wheel-speed plugs. DR-25 on 2+ wire runs, System 25 boots at branches.
- **B14 Shields and drains.** Shielded cable as listed under Shields below; a shield runs unbroken, floats at
  the device and ends only at A7 (loom A), B17 (loom B) or C1 (CAN) through its own drain wire. Detail: Shields below.

### Relays

- **B15 Relays.** An ECU or CSB3 output drives a relay low-side (Aux 1-4 are low-side only, Aux 5-8 set Low): pin ->
  coil 85, 86 -> fused +12 V; no flyback diodes. Relay pins per maker drawing; boxes per `cad/fusebox/`. Detail: "Relays (B15)" below.

### CAN

- **B16 CAN frames.** Any CAN change reconciles across ECU, cluster, RealDash, CSB3 (Rule 2 below); frozen cluster wins. CSB3
  0x640-0x642 -> ECU; cluster reads 0x3E8-0x3EB, 0x3EE, sends 0x3EC/0x3ED; RealDash 0x3EB gear, 0x3EF-0x3F1.
- **B17 CAN wiring.** One bus (CAN 1, bus 2 unused), the CAN-Lambda on it, shielded the whole run. Every CAN node takes
  +12 V (fuse box) and ground (battery-negative bar) with the trunk at its branch, never ECU ground or chassis.
  Power (Dan 2026-11-04, X1): the ECU per Link's hold-power wiring (ignition wake, the ECU holds main relay K-EFI for
  the ETB); centre cluster and CSB3 on LOGIC Bus 2 (live with the ECU); CAN-Lambda on its own ON-only relay K-ON, no hold
  ("Relays (B15)"); RealDash Pi on the factory radio circuit (J/B No.1 CIG & RADIO 15 A, ACC), shared with the future radio; Dan adds a
  switch at the display (Dan 2026-11-04, N6). Reserved: radio on that circuit, amplifier one POWER positive-bar lug (README).
- **B18 CAN config now.** The ECU CAN config is written in the repo now (`link_g4x_can_setup.json` / `.lcs`,
  `switchboard_frames.json`, `check_parity.py` green); only work that needs the ECU connected waits for setup.

### ECU pins

- **B19 ECU pins.** Check every ECU-pin circuit against the G4X Quick Start Guide and plug-in guides (plug-in wins;
  never G4 / G4+ pages); a mismatch is a stop. Resistors only where needed; 12 V switch into a ground input via opto.
  An assigned ECU pin moves only to a pin the G4X Quick Start Guide shows can do the same job, checked and cited first (Dan 2026-11-04).
  For this ECU's own pinout the XtremeX Quick Start Guide wins over the plug-in spec sheet (Dan 2026-11-04, W2 a).

### Wire and parts

- **B20 Wire and colours.** SAE J1128 TXL in the cabin, trunk and harness C; `M22759/16` Tefzel for the engine harness
  and hot or high-current spots; solid colours by function, no ident bands. Detail: "Wire and colours (B20)" below.
- **B21 Picking parts.** Order and validation per `docs/sourcing/README.md` (on hand, TE, Dan's suppliers, else a stated
  reason). Never guess a PN: unverified = `TBD` + reason; every part real and buyable; parts made at work cost $0.

### Drawings and CAD

- **B22 End labels, clean sheets.** Each wire end says where that end lands, never a generic word or internal id; every
  part has a plain name, any code in parentheses. Only asked-for parts. Detail: "End labels and names (B22)" below.
- **B23 Models drive drawings.** The CAD model is the master: a physical change goes in the model first, then the drawing is regenerated, never hand-edited. Revs: Drawing rules below.
  Gate `check_drawings_current.py` checks the register, rev letters, issued PDFs and tracked fingerprints; it skips the STEP model files (in Dan's models folder, B26; Dan G2 a).
- **B24 Initials and revision marks.** DRAWN and every rev-log BY are a person, always `DG` (`.drawing-initials`), never
  an agent; no file = stop and ask. Full-letter revs from 2026-10-19 get rev triangles (Drawing rules below).
- **B25 What a drawing shows.** As the Drawing rules below list: no hidden lines or mesh facets, tangent edges in
  trimetrics, makers' own models, balloons only on visible parts, shop-only NOTES. Gate `check_drawing_rules.py`.
- **B26 CAD work.** CAD stays frozen unless Dan asks (model and drawing detail: Drawing rules below). Models live only in
  Dan's models folder (OneDrive `Desktop\models`, `publish-to-models`): latest rev + 2 previous, bought parts as maker models there; drawings / BOMs are copied here for the checks.
- **B27 Fuse boxes follow the harnesses.** Boxes are configured to match the harnesses (Dan 2026-10-26; build rules: Drawing rules below); until the revisit (row 107) the box CAD may lag and `sot/fuse-relay-map.csv` wins.
  Spare fuse and relay seats in the boxes are allowed and kept as spares: no cleanup of unused seats (Dan 2026-11-04, Y7).

### Shipping

- **B28 Shipping a change.** From `origin/main`; `check_all.py`, `check_parity.py` green; touched rows updated; PR with `Rows:`;
  pr-closeout, then squash-merge when Repo checks pass. Detail: "Shipping (B28)" below.
- **B29 Tracker, generated files.** `docs/OPEN-ITEMS.md` is the one tracker (open rows, Needs Dan, history), kept
  short. The drawings and BOM are generated, never hand-edited.
- **B30 Past decisions.** Old R1-R226, S1-S40 and audit rows resolve through the retire map below (full text in git
  history); what they decided lives in the files they changed. Reversing an applied decision is Dan's call.

### Retire map (permanent)

Every old rule ID and where it went. "dropped" = no longer binding, with the reason; "A/C" = the A/C facts (D16,
2026-10-25). Read an old citation (e.g. "DECISIONS R154") through this table.

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
| R13 | B9 | its A/C amp part: A/C, D16 2026-10-25 |
| R14 | B9 | |
| R15 | B11 | |
| R16 | B9 | |
| R17 | B30 | alternator plug: applied; the facts live in the file it changed |
| R18 | - | removed before R226 (git history) |
| R19 | B11 | |
| R20 | B11 | |
| R21 | B30 | ECU starts the engine, no clutch interlock: applied; the facts live in the file it changed |
| R22 | B30 | EPS pump wiring: applied; the facts live in the file it changed. Enable: one fuse, LOGIC EPSEN 5 A -> `K-EPS-EN` (Ign 6 active-low) -> 87 straight to the pump (E3 a, Dan 2026-11-02) |
| R23 | A/C | A/C - D16 2026-10-25 (amp drives k_acc; Link kill only) |
| R24 | B17 | |
| R25 | B15 | |
| R26 | B19 | |
| R27 | B14 | |
| R28 | B14 | |
| R29 | B14 | |
| R30 | B14 | build method: Shields below |
| R31 | B14 | |
| R32 | B14 | |
| R33 | B14 | |
| R34 | B14 | |
| R35 | B20 | |
| R36 | B12 | |
| R37 | B12 | |
| R38 | B21 | |
| R39 | dropped | dropped - the old library went with `rebuild/`; the part library rules are in the README (B6) |
| R40 | B4 | also B21 |
| R41 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| R42 | B8 | |
| R43 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| R44 | B22 | coverings: B13 |
| R45 | B5 | also B6 |
| R46 | B3 | |
| R47 | B8 | |
| R48 | B21 | |
| R49 | B22 | |
| R50 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
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
| R88 | dropped | no PDF export (R103), dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| R89 | dropped | circuit tracer deferred; OPEN-ITEMS row 117 keeps it |
| R90 | B30 | approval of the harness.design drawings superseded by R224 / R225 |
| R91 | B11 | |
| R92 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
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
| R103 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| R104 | - | removed before R226 (git history); replaced by R217 |
| R105 | B30 | RealDash 200 kPa tile, ruleset: applied; the facts live in the file it changed |
| R106 | B26 | |
| R107 | B8 | |
| R108 | - | removed before R226 (git history) |
| R109 | B1 | |
| R110 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| R111 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| R112 | B26 | |
| R113 | B4 | Dispatch detail: Dispatch below |
| R114 | B29 | |
| R115 | B4 | |
| R116 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
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
| R205 | A/C | A/C - D16 2026-10-25 (amp drives k_acc; Link kill only) |
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
| R223 | B10 | reversed 2026-11-01: VSS on ECU +8 V, Gnd Out, DI 8 pull-up off (B10) |
| R224 | dropped | the freeze ended 2026-11-02 (Dan B10 a, G1 b); the ONE drawing set retired 2026-11-01 (B6: harness.design) |
| R225 | B6 | amended by Dan 2026-10-20 (harness.design only a consumer); reversed 2026-11-01: harnesses are built in harness.design, our drawing PDFs retired |
| R226 | - | this page (the B1-B30 header) |
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
| S28 | A/C | A/C - D16 2026-10-25 (button and evap to the Link removed) |
| S29 | B30 | applied; the facts live in the file it changed |
| S30 | B30 | VRC IN / OUT labels: applied; the facts live in the file it changed |
| S31 | dropped | dropped - written for the deleted `rebuild/` files (R225); harness.design is back under B6 with its own README rules |
| S32 | B30 | machined enclosures: applied; the facts live in the file it changed |
| S33 | B30 | applied; the facts live in the file it changed |
| S34 | B15 |  |
| S35 | A/C | A/C - D16 2026-10-25 (amp sensor common; E10 cabin splice) |
| S36 | B30 | applied; the facts live in the file it changed |
| S37 | dropped | `validate_sot.py` replaced by `check_wiring.py` (R221) |
| S38 | B30 | applied; the facts live in the file it changed |
| S39 | - | removed before R226 (git history) |
| S40 | B11 |  |
| Audit row 1 (2026-09-28 table) | B17 | CAN-Lambda bulkhead pins: B30 |
| Audit row 2 (2026-09-28 table) | B7 | DRB102 accepted on its ratings |


## Rule 1 — Wiring: reconcile every wiring surface

**Trigger:** any change to any wiring document, diagram, pinout or BOM.

**Requirement:** before the change is final, every wiring surface below agrees. A change that leaves two documents disagreeing is not done.

Source-of-truth chain:

```
docs/harness/MASTER-wirelist.csv   the ONE wiring SoT (R221)
      |
      +-- sot/channels.csv             ECU channel settings; check_wiring.py compares live pins both ways
      +-- docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md   device pin, pin name, shield flag per device
      +-- XTREMEX-IO-TABLE.html        visual face of channels.csv (generated pin map)
      +-- docs/harness/drawings/       generated pin chart (build_pin_chart.py) and DRB102 map (build_drawings.py)
      +-- docs/harness/wirelists/      generated per-harness wire lists, xlsx + CSV (build_drawings.py --check reads them back)
      +-- harness.design files         ST185-<harness> Rev X, built from the master by gen_*.py (B6); never a source
      +-- sot/fuse-relay-map.csv       box seat -> circuit; wins over the parked fuse-box CAD (row 107)
      +-- docs/harness/routes/ + placement editors   device spots and lengths (B8)
      +-- docs/sourcing/PROJECT-BOM.*  generated shopping list
```

New wiring facts go into the master row first; `channels.csv`, the IO table, the drawings and the BOM follow. Device pin, pin name and whether that device gets a shield go into `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` (one shield flag per device). Which ECU pin a device wire lands on is owned by the ECU; ECU pins never move. If anything disagrees with the master on a pin, the other thing is wrong. No script writes the master or `channels.csv`. `python tools/check_all.py` must pass before every commit.

A wire on an ECU pin is also checked against the Link G4X Quick Start Guide and the G4X plug-in guides (plug-in wins): pin function and mode, what the pin may connect to, current limits, wire gauge. `check_wiring.py` fails on any far end the pin's class does not allow (R212), any ground that breaks the ground classes (R213, R216), any relay driven the wrong way (R219).

| Surface | Role |
|---|---|
| `docs/harness/MASTER-wirelist.csv` | The ONE wiring SoT (R221) |
| `sot/channels.csv` | ECU channel settings; pins checked against the master |
| `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` | Device pin, pin name, shield flag per device |
| `XTREMEX-IO-TABLE.html` | Visual face of `channels.csv` |
| `docs/harness/drawings/` | Generated: pin chart (`build_pin_chart.py`) and DRB102 map (`build_drawings.py`) |
| `docs/harness/wirelists/` | Generated per-harness wire lists (xlsx + CSV); `build_drawings.py --check` reads them back |
| harness.design files (`ST185-<harness> Rev X`) | Built from the master by `gen_*.py` (B6); never a source |
| `sot/fuse-relay-map.csv` | Box seat -> circuit; wins over the parked fuse-box CAD (row 107) |
| `docs/harness/routes/` + placement editors | Device spots and lengths (B8) |
| `docs/sourcing/PROJECT-BOM.csv` | Generated — re-run `build_project_bom.py` |
| This file | Binding rules B1-B30 and the procedure on this page |
| `docs/sourcing/te-on-hand-bom.csv` | Parts already owned — check before speccing anything new |

Generated files are never hand-edited. B9 applied: forward of the firewall a device end is new wire to the device's own plug or its 6 in pigtail (B9); a bay harness's cabin end may splice into a kept factory lead (J/B No.1, IE1, IG2, R/B No.4).

## Rule 2 — CAN: any change on any device reconciles across all devices

**Trigger:** any change to CAN configuration on any device, in any repo.

**Requirement:** reconcile against every other CAN participant before the change is final.

| Device | Where its config lives |
|---|---|
| Link G4X XtremeX ECU | `link_g4x_can_setup.json`, `link_g4x_can_setup.lcs` |
| Center cluster (ESP32-P4) | `center-cluster-esp32-p4` repo — `main/canbus.c` |
| RealDash | `link_g4x_realdash.xml`, `st185_dash.rd`, `REALDASH-LAYOUT.md`, `rd-build/` |
| ECUMaster CAN Switchboard (CSB3) | `ECUMASTER_SWITCHBOARD_SETUP.md` |
| Link CAN-Lambda | On the same bus |

Shared contract documents: `CAN-BUS-ID-ALLOCATION-TABLE.md` (wire format; parity gate), `CAN-BUS-MASTER-DESIGN.md` (architecture and PCLink apply), `BENCH-TEST.md`, `bench/frames.py`. The cluster's `CANBUS-ENCODE-DECODE-REFERENCE.html` lives only in the cluster repo — linked, never copied.

Bus facts: Link CAN-Lambda is on CAN bus 1 with everything else. CAN bus 2 is unused (those ECU pins are free). Single bus, 1 Mbit/s.

Authority when two configs disagree: (1) center cluster firmware as flashed — frozen, highest; (2) PCLink CAN configuration on the ECU; (3) everything else. On conflict the other device changes. Reflashing the cluster needs Daniel's explicit approval.

For every frame the change touches, confirm across all participants: frame ID, byte offsets and field widths, endianness (BigEndian unless a canonical doc says otherwise), scaling and offset, units, who transmits and who receives. A mismatch not fixed in the same pass goes into OPEN-ITEMS.

These rules cross repository boundaries. The cluster repo is `C:\projects\active\center-cluster-esp32-p4`. A CAN change here that affects the cluster is not complete until that side is checked. The only center-cluster portion in this repo is the CAN node plus power and ground. Interior cluster wiring lives only in the cluster repo.

## Rule 3 — the ECU harness: one harness, cabin side and engine side

Daniel, 2026-10-19 (R220): loom A and loom B are one harness, named `AB` — they both come from the same bulkhead.

- Two sides in the master: `AB-cabin` (ECU plugs A, B and C to the cabin half of the DRB102, plus every cabin branch) and `AB-engine` (the engine half of the bulkhead to every engine device the ECU drives or reads, throttle body included). Letters A / B / C are the ECU's own plug names and stay on the pins; ECU pin assignments never move.
- One bulkhead connector per side: `DRB102-CABIN` and `DRB102-ENGINE` (TE DRB12-102PXE-L018), cavities assigned by device (R208); the map is `docs/harness/drawings/DRB102-bulkhead-map.png`. The DRB102 (B7) is one 102-position bulkhead: cavities grouped by device in route order, a circuit uses the same cavity number on both sides, one cavity carries one net, and the contact size must take the wire's gauge and current.
- The ECU splice point: every cabin power, ground and rail splice sits at one place by the ECU plugs. +5 V (A32) is two bussed DT plugs `BUS-5V` (12-way) and `BUS-5V-2` (8-way, linked); Gnd Out A24 and B22 are their own 12-way bussed DT plugs `BUS-GNDOUT-A` / `BUS-GNDOUT-B` (no A24-B22 tie); +8 V, switched 12 V, the ECU A5 feed and the ECU power ground are soldered splices there (R169 parts: `DT06-12SA` / `DT04-12PA-P021`, `DT06-08SA` / `DT04-08PA-P021`, 13 A per pin). The ECU power ground splice joins A25, A34, B25, B34 only and runs one wire to the POWER box battery-negative bar (R216).
- Splice sizing (B12): by the combined gauge it joins; not for drains. Bulkhead substitution (B7): only a complete matching set from the maker's datasheet.
- A wire belongs to the one harness that carries it (`harness` column); `passes_through` names any harness it runs through. Mating halves (DRB102, the inline `IX-` pairs) are checked cavity for cavity by `check_wiring.py` M1.
- Every other harness keeps its own name: `CabinPower`, `HeavyDC`, `EngineRoom-C`, `Dash` (was `CAN`, `CSB3`, `ClusterLED`; Dan B8 = a, 2026-11-02), `AntiTheft`, `RearFuel`, `WheelSpeed-Front` / `-Rear`. Rear lights stay on the factory harness (no RearLights harness).

## Dispatch

Read this file and `AGENTS.md` first; they win. Dispatch only relays messages, picks the session and model, checks sessions, and takes no actions of its own.

- Relay Dan's words to a session. Relay a session's status back. Do not plan, edit, or decide.
- Session vs model is the only choice Dispatch makes. Look-ups go to a small model; wiring and CAD stay on a larger one.
- Before a question reaches Dan, a session answers it from the repo, the SoT, or a maker document. If that fails, ask Dan in `docs/OPEN-ITEMS.md` Needs Dan.
- Code sessions follow `AGENTS.md`. This section is for Dispatch only.

## Where data lives (B3)

Binding as part of B3.

- Scratch folders hold disposable work only; anything vital goes to its home by type: rules -> DECISIONS / README, agent instructions -> AGENTS.md, state and tracking -> OPEN-ITEMS, cross-session notes -> working memory; tools and scripts -> the repo (Dan 2026-11-03). Scratch inside the repo is `_scratch/` (gitignored); nothing vital ever goes there.
- Retiring files: `AGENTS.md` (R46).
- Before a file is folded away or deleted, every fact open work still needs is already in its home (lesson: #363 and #399 folded away the power-injection plan and cut-list groups 4-8; recovery phase 1 put them back, row 183).
- A session cleans a scratch or handoff folder only by deleting, by name, the files it made itself, never with a wildcard (lesson: 2026-11-03, a scratch cleanup deleted the planning research files).

## harness.design files (B6)

Moved here from rule B6 on 2026-11-02 (Dan L3 = a); binding as part of B6.

- File names carry a rev letter from Rev A (`ST185-<harness> Rev A`; a physical change = a new file at the next letter, Dan deletes the old; a view-only change keeps the file and letter; Dan 2026-11-02).
- Layout view = formboard (README).
- `build_drawings.py --check` keeps the layout tree, master lengths, the Option A wire lists ("Wire lists" below) and the DRB102 map current; the pin chart is the one pinout.
- The OEM splice reference is rebuilt from the master and checked (row 175).

## Grounds (B10)

Moved here from rule B10 on 2026-11-02 (Dan L3 = a); binding as part of B10.

- ECU power grounds (A25, A34, B25, B34) splice together, one wire to the POWER box battery-negative bar.
- Gnd Out takes only the return of a sensor the ECU powers (+5 V / +8 V); anything fed from a fuse box or the SW12 bus grounds on the battery-negative bus with the other 12 V devices, never on the ECU (Dan 2026-10-31; row 170).
- Shield drain only to the ECU shield pin; heavy loads may use chassis.
- The ignition coil ground goes to the POWER box NEG bar through bulkhead cavity 4, not the engine block (Dan 2026-10-29).
- ECU +8V Out feeds the cam sensor and the gearbox speed sensor only; the VSS returns on Gnd Out, DI 8 pull-up off (Dan 2026-11-01).

## Relays (B15)

Moved here from rule B15 on 2026-11-02 (Dan L3 = a); binding as part of B15.

- Link Aux outputs: Aux 1-4 low side only, Aux 5-8 high or low side (XtremeX QSG p.3); their current is `TBD` in
  `sot/channels.csv` (W3 a, 2026-11-04: no G4X document on hand gives it; Link forum 15847, a G4+ thread, says under 2 A low
  side and under 0.5 A high side). Aux 1-10 carry a 1.5 kOhm pull-up to regulated 12 V (forum 17727, Adamw, G4X). So a relay coil is driven low side (B15).
- Coil check (Dan 2026-11-01): whenever a fuse / relay box is touched or reviewed, check every relay coil against its driver; Link Aux outputs have their own flywheel diode, Ign / Inj outputs do not, so a relay on those gets a diode-coil part.
- ON-only relay K-ON (Dan 2026-11-04, N5 a; B17): LOGIC M7 (was K-REV), TE 6-1419137-4 (1 form C, diode). Coil 86 from
  J/B No.1 1H-7 B-O (IGN 7.5 A out, live at ON and ST; 1993 EWD p.62-63), coil 85 to the POWER box NEG bar. Contact:
  BUS1-6 LAM 10 A (Bus 1; Link CAN-Lambda QSG: 10 A fuse through an ignition relay; LAM 7.5 -> 10 A, Dan) -> 30; 87 ->
  the CAN-Lambda only (DRB102 cavity 95; Dan N6: its own relay and its own fuse). The RealDash Pi is off the LOGIC box
  (B17); the cluster stays alone on DEV 15 A (Bus 2); BUS2-1 and BUS2-12 are spare. No fuse-box design change.
  Coil check of the LOGIC box with it: K-ETB on Aux 2 (flywheeled), K-EPS-EN on Ign 6 and K-ACC on the A/C amp are diode
  parts, K-HL / K-HR / K-HORN switch-driven, K-ON key-driven with its own diode: all fit.

## Shields

`check_wiring.py` S1-S3 enforces the drain and floating-screen rules (R207). Device pin, pin name, and whether that device gets a shield: `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`.

**B14 detail.** Same cable and colours on both sides of the firewall (Dan 2026-10-31; row 171; moved here from rule B14 on 2026-11-02, Dan L3 = a). Cable: TE Raychem Spec 55. Shielded: crank, cam, knock, wheel speed, VRC outputs, turbo speed, flex fuel, ETB, APS pedal, the CAN-Lambda run and every CAN pair (one exception: the spur to the CAN-Lambda end terminator plug `CAN-TERM-END` is 2 plain wires, CAN-H and CAN-L, no shield, Dan 2026-11-03); injectors, coils and the gearbox VSS (plain wires, Dan 2026-11-01) get none. A drain is its own `M22759/16-20-06` wire, found by its part, never its colour; no connector shell, and no sleeve just to end one screen. A cabin device that joins a loom part-way splices its drain where its signal wires join; a bulkhead device keeps its own drain and bulkhead pin up to the splice at the ECU plug. Each VRC box has one 5-pin CNLINKO LP-16 IN plug (pin 3 = both screens) and one OUT plug; its board is isolated from the case.

**No connector shells (R33).** Every drain lands on a regular pin; no shell, backshell or shielding plate ever carries a screen (the VRC LP-16 plugs included).

**Shared drain pin: one splice (R29, R30, R32).** Every shielded cable is drawn as if it had a drain wire, straight to its pin. Two or more screens on one pin share ONE `GENERIC SOLDER SPLICE` (no covering), with one drain wire (no wire part number, R32) to the pin. The T-splice is how it is built, not drawn (R30). Every CAN node branch shield goes into its own named branch splice on the trunk drain (`SP-CAN-SH-*`, R207; the one exception to "one splice"). **CAN branch splices (Dan 2026-10-25):** where each CAN node branches off the trunk for power and CAN signal, that node's shield splices onto the main trunk shield at that same point, one splice per branch point, never all in one lump. Each branch splice is a solder sleeve that takes a drain lead (Raychem / TE type); part number TBD (row 166).

| Pin | Screens into the one splice | Splice |
|---|---|---|
| ECU-A A7 | crank, cam, turbo, flex, ETB sensor, APS, front WS spur, front WS FR spur | `SP-SHIELD-A`, 6 in (152 mm) behind `ECU-A` (N83 = A, Dan 2026-10-31); the crank drain is the one crimped into A7, the others are soldered onto it (R30) |
| ECU-B B17 | knock, ETB motor, rear WS spur | `SP-SHIELD-B`, 6 in (152 mm) behind `ECU-B` (N83 = A) |
| ECU-COMMS C1 (R207) | CAN trunk drain `w_shd_can_trunk` (one wire); CSB3, cluster, RealDash, ECU cable and bulkhead / Lambda branch drains | one named splice per branch, `sp_can_sh_clu` / `_csb` / `_rd` / `_bh`, at that branch point |
| VRC front IN pin 3 | FL and FR sensor cables | `sp_vrc_f_in_sh` at `lp16_vrc_f_in` |
| VRC rear IN pin 3 | RL and RR sensor cables | `sp_vrc_r_in_sh` at `lp16_vrc_r_in` |

Every bulkhead drain has its own cavity. Both sensor screens of a VRC share its input plug pin 3.

**Vocabulary.** Screen means shield. A drain is the wire that connects the shield to the pin (no wire part number, R32). Shields exist only on cables; a device or sensor gets one shield flag (never per pin or per wire).

**Absolute rules (R27, R28, R33).** A shield floats at the sensor, runs unbroken as a multi-conductor Raychem cable, and terminates at an ECU shield pin (A7 / B17); the only device-end landing is the wheel-speed sensor shields on VRC IN pin 3 (R31). A shield that crosses the firewall does so on its own bulkhead pin, wired on both halves, never on a shell. Do not invent break points. The ABS wheel-speed sensors have two wires: no third conductor, no shield connection at the sensor.

**Bulkhead pass-through.** Only a signal that already passes through both firewall bulkhead halves must carry its shield through both halves on matching pins. That shield floats at the sensor, must not stop on either half, and terminates at the ECU shield pin. Once the bulkhead connectors are installed they are straight-through, so a shield is not required to float at the bulkhead. Loom A screens land on A7 through `SP-SHIELD-A`, loom B screens on B17 through `SP-SHIELD-B`, the CAN screens on C1 through the trunk drain. No screen crosses between loom A and loom B (R207, `check_wiring.py` S3). Nothing but a drain lands on A7, B17 or C1.

**VR conditioner boxes (R31, R34).** The VRC device gets one shield flag. The sensor cables' screens and the output cable's screen are one continuous path: sensor (floats) -> IN plug pin 3 (one splice, R29) -> wire inside the box -> OUT plug pin 3 -> output cable screen -> the `IX-WS-*` pair -> the shield splice -> **A7** (front) / **B17** (rear). The plugs are `VRC-F-IN` / `VRC-F-OUT` and `VRC-R-IN` / `VRC-R-OUT`: input 1 left +, 2 left -, 3 both screens, 4 right +, 5 right -; output 1 +5 V, 2 Gnd Out, 3 screen, 4 left out, 5 right out. `check_wiring.py` treats IN 3 to OUT 3 as one path through the box.

The VRC and its panel sockets are not drawn. Each VRC harness is two separate pieces ending in two non-shielded 5-pin CNLINKO LP-16 plugs (`LP-16-J05PE-02-001`, S8 / R34 / S16). Nothing bonds to the case and no shell carries the screen (R33): the box is not part of the shield path, the PCB sits in a printed holder (S26) and grounds through the output cable only, and the box mounts on nylon hardware.

**ABS routing.** Front (FL, FR) runs through the fenders with loom C. Rear (RL, RR) runs with the fuel pump and level sender. Neither pair gets its own firewall crossing; the wheel-speed loom uses no bulkhead connector — it crosses on a grommet so each screen stays unbroken.

## Wire and colours (B20)

Moved here from rule B20 on 2026-11-02 (Dan L3 = a); binding as part of B20.

- Wire type (Dan 2026-10-31, N82 A): SAE J1128 TXL (XLPE, 125 C, `J1128-TXL-<awg>-<colour>`) in the cabin and trunk and for front-of-car (harness C) signal / low-current wires; `M22759/16` Tefzel (150 C) for the engine harness (AB-engine), anything within 150 mm of the exhaust, turbo or downpipe, the Spec 55 shielded cables, and any circuit where TXL's derated rating (about 0.8x Tefzel at 80 C cabin, 0.7x at 100 C engine bay) falls below its fuse (B12).
- Battery cables `BC-*`.
- Solid colours: Red +12 V, Black ground / drain, Orange sensor supply, Blue sensor return, White signal, Green CAN, Yellow switch in.
- No ident bands (Dan 2026-10-31): a printed wire-ID label at each end (B22) tells same-colour wires apart.

## End labels and names (B22)

Moved here from rule B22 on 2026-11-02 (Dan L3 = a); binding as part of B22.

- Each wire end says where that end lands (device, connector, pin, signal; OEM end + EWD ID; splice: what it joins), never a generic word or internal id; unknown = `TBD - <what>`.
- Only asked-for parts.
- Every connector, splice, bus, relay and box has a plain name; any code follows in parentheses (Dan 2026-10-31; row 172).

## Wire lists (Option A, Dan 2026-10-26)

The per-harness From / To wire lists (`docs/harness/wirelists/`, generated by `build_drawings.py` from the master) follow
these rules. Worked examples (splices at both ends, a wire crossing harness files, a one-end shield drain, a CAN trunk with
node branches): `docs/harness/wirelists/option-a-examples.html`.

1. One row per physical wire, or per core of a cable.
2. From and To only ever name a connector or device and its pin, never a splice. No blank pins: a lug on a stud reads `Lug`.
3. `Splice` names the splice(s) the wire lands in (`SP-1 > SP-2` through a link); `Branch` says what the wire is: wire,
   core, leg, trunk, link or drain.
4. Each splice has one trunk: the heaviest wire if one is heavier than the rest, else the one wire to an ECU pin, else the
   one wire to the bulkhead, else the one link to another splice, else the one wire to a power or ground source (fuse /
   relay box, J/B, bus, ground point), else the one factory tap, else the longest, else the first by wire ID.
5. A leg's To is the end its trunk lands on, followed through link splices. A trunk or link end inside a splice reads
   `legs of SP-x`.
6. A wire that leaves the file stops at the shared connector pin (the bulkhead); `Continues` names the other harness, its
   wire and where that wire goes, and any splice the wire shares with another harness.
7. A shield drain left unconnected reads `NC, floats` (pin `NC`): cut back and sealed under heat-shrink.
8. `build_drawings.py --check` reads each committed list (xlsx and its CSV) back against the master (rules 1-4, 7, ends,
   gauge, colour). harness.design files are built from the master by `gen_*.py`, not from these lists; the lists are the
   build / review copy. Removal rows are not wires and are left out (`is_removal`).

## Harness ownership (B8 list)

Moved here from rule B8 on 2026-11-02 (phase 3, O6); binding as part of B8. Harness ownership (Dan 2026-11-01): one harness file is one physical harness; each plug belongs to the harness that physically carries it and every wire landing on that plug is in that harness (`passes_through` names any other bundle it rides in); fuse / relay boxes, buses, studs and factory taps are hubs that several harnesses land on. A cable listed in a harness it cannot physically ride in (size, route, cavity limits) is flagged to Dan; the pin chart's first page lists every device by harness.
Locked device list (Dan B1 = a, 2026-11-02): this list is the target owner of every device; the master is brought to it (OPEN-ITEMS row 183 phase 2) and a device changes harness only with Dan's OK.

Locked by Dan 2026-11-02 (B1 = a; OPEN-ITEMS row 183). This is the **target** owner of every device after Dan's
2026-11-02 answers, not a copy of today's master: B7 = a (MR-S plugs B / C fully AB-engine, spare rows included), B8 = a
(`CAN` + `CSB3` + `ClusterLED` become one `Dash` harness), B9 = a (AB-cabin owns the cabin-to-trunk sill run), B6 = b
(the HeavyDC devices in Route 16 belong to HeavyDC's own map, Route 1). Base: the R90 lock (#203, files at `2c4aee6`)
and the master at `b2217ab` (#477), compared device by device on 2026-11-02; fixes for its double owners and cabin-only feeds
are below. Phase 2 (2026-11-02) applied this list to `MASTER-wirelist.csv`, with Dan B17 b, B18 a, B19 and B20 a.

**Hubs (B8: several harnesses land on them, no owner):** POWER box (B1) and its bus studs and NEG bar, LOGIC box (B2),
SW12 bus plug, every box relay (K-EFI, K-FAN, K-FAN2, K-HL, K-HR, K-HORN, K-ETB, K-ACC, K-EPS-EN, K-EPS, K-FP), trunk relay
block (B3), kill switch, ground points ID / IG / EA / EB and the engine block stud, and the factory taps on J/B No.1, IE1,
IG2, R/B No.2 and R/B No.4 (R/B No.3 and the fog switch F12 are no longer hubs: the fog circuit is removed, Dan 2026-11-02). Bussed plugs (`BUS-5V`, `BUS-5V-2`, `BUS-GNDOUT-A`, `BUS-GNDOUT-B`)
are splices (B8 editor devices) and sit in AB-cabin.

| Harness (target) | Devices it owns |
|---|---|
| AB-cabin | ECU plugs A, B and C (`ECU-A`, `ECU-B`, `ECU-C`; C moved in from Dash, Dan 2026-11-04 V2 a, with the ECU CAN cable to the CAN joins); bulkhead, cabin half (`DRB102-CABIN`); the ECU splice point; accelerator pedal (`APS-PEDAL`); IG2 wake diode (`D-IG2-WAKE`); cam pull-up, fuel-level pull-up and lock-sensor resistors (`R-CAM-PULLUP`, `R-FUELLVL`, `R-LOCK`); A/C amp taps (`A18` = 1993 A15, `A32`); ambient air sensor (`A1`, front, its two wires ride harness C to a "To front" hand-off); wheel-speed inline plugs, ECU side (`IX-WS-F-S`, `IX-WS-R-S`); fuel level inline plug, trunk end (`IX-FUEL-P`); the cabin-to-trunk sill run (B9: fuel pump relay coil wire `w_fp85`, fuel level pair, kill-switch IG leg; the fuel pump relay coil+ feed `w_k_fp_86_cp` (RearFuel) and the trunk pin lead (AntiTheft) ride it) |
| AB-engine | Bulkhead, engine half (`DRB102-ENGINE`); injectors 1-4, coils 1-4, throttle body (`ETB`), boost solenoid, crank, cam, knock, MAP, IAT, charge IAT, coolant temp (`ECT`), coolant / oil / fuel pressure, oil temp, flex fuel, turbo speed, gearbox speed (`VSS`), reverse switch (`REV-SW`); CAN-Lambda and the far-end CAN terminator plug (`CAN-LAMBDA`, `CAN-TERM-END`; Dan 2026-11-03); MR-S pump plugs B and C (`MRS-B`, `MRS-C`), spare cavities included (B7 = a); starter solenoid S plug (`STARTER-TRIGGER`; own short branch from DRB102 cavity 3, B20 a) |
| CabinPower | Only hubs (the boxes and relays above) plus the cabin feed wires between them and the factory taps: dome feed (`w_pmu_dome`, moves in from EngineRoom-C), hazard feed (`w_haz_cp`), R/B No.2 W-L feed (`w_rb2_wl`) dropped (Dan B17 b, phase 2); fog: no device (the cut-and-cap leads `FOG-CAP-1`, `-4`, `-6` are gone; the fog wires are removal rows `w_fog_*`, Dan 2026-11-02) |
| HeavyDC | Trunk battery posts (`BATT-POS`, `T-TRUNK-NEG`); RADLOK pair, both sides (`RADLOK-POS-CAB`, `-POS-ENG`, `-NEG-CAB`, `-NEG-ENG`); starter B+ stud lugs 1-3 (`T-STARTER-B`, `-2`, `-3`); alternator B+ stud (`T-ALT-B`); engine block stud lug 1 (`T-ENG-BLOCK`); jump post (`JUMP-POST`); kill switch and trunk relay block (hubs). Map: Route 1, with Route 16 devices H1, H2, H4, 18 and line 9 "Alt and starter" moved there (B6 = b, later phase), shown greyed in the AB-engine editor |
| EngineRoom-C | Headlamps (`H1`, `H2`); pop-up motors (`R2`, `R3`); front turn / clearance and side marker lamps (`F5`-`F8`); wiper motor (`F9`); washer pump (`W1`); horns (`HORN-LH`, `HORN-RH`); radiator and condenser fans with their grounds (`FAN-RAD`, `FAN-COND`, `-GND`); MR-S pump plug A (`MRS-A`); A/C compressor clutch (`A4`); A/C pressure switch (`A5`, both its wires; was also AB-cabin); alternator plug (`ALT-PLUG`); ground studs EA, EB and the EB strap lug (`GND-EA`, `GND-EB`, `GND-EB-2`); engine block stud lug 2 (`T-ENG-BLOCK-2`; lug 3 dropped: the EHPS pump ground `w_eps_gnd` lands on EA, Dan L4 a 2026-11-02) |
| Dash (was `CAN` + `CSB3` + `ClusterLED`) | the ECU-end CAN terminator (`R-TERM-ECU`) and the CAN joins (ECU plug C moved to AB-cabin, Dan 2026-11-04 V2 a); centre cluster and RealDash Pi CAN, power, ground and headlight-sense ends (`T-CLUSTER-*`, `T-REALDASH-*`); CSB3 plug (`CSB3`); 8-channel opto board (`OPTO-8`, was also AB-cabin); cruise ladder resistor (`R-CRUISE`, was also AB-cabin); cruise stalk, cruise clutch switch, stop switch and dimmer taps (`Cruise` = C14, `C17`, `S9`, `R10`); warning LEDs turn L / R, high beam, charge, park brake, oil (`D-TL`, `D-TR`, `D-HB`, `D-CHG`, `D-PK`, `D-OIL`, was CSB3 + ClusterLED); cluster plug taps (`C11`, `C12`) |
| AntiTheft | Alarm module (`ALARM`, was also AB-cabin; B18 a); siren (`SIREN`); shock sensor; status LED; valet switch; door, hood, trunk and park-lamp leads (`T-AT-DOOR`, `T-AT-HOOD`, `T-AT-TRUNK`, `T-AT-PARK`); its ground lugs (`T-AT-GND`, `-B`, `-C`) |
| RearFuel | Fuel pump (`FUEL-PUMP`); fuel level sender (`FUEL-LEVEL`) and its inline plug, sender end (`IX-FUEL-S`); trunk pump ground (`T-TRUNK-FP-GND`); the fuel pump relay coil+ feed `w_k_fp_86_cp` (SW12 bus plug by the LOGIC box to K-FP coil 86 in the trunk relay block), riding the AB-cabin sill run (Dan 2026-11-04: the boxes are far apart, so the wire belongs to the harness that holds the device it serves) |
| WheelSpeed-Front / -Rear | Wheel speed sensors (`WSS-FL`, `WSS-FR` / `WSS-RL`, `WSS-RR`); VR conditioner IN / OUT plugs (`VRC-F-*` / `VRC-R-*`); inline plugs, sensor side (`IX-WS-F-P` / `IX-WS-R-P`) |

**Changes from the old master (applied in phase 2, 2026-11-02):**

| Device or wire | Today | Target | Why |
|---|---|---|---|
| MR-S plugs B / C spare cavities (9 rows) | EngineRoom-C | AB-engine | B7 = a: one owner per plug |
| Alarm module immobiliser lead (`w_at_immob2`, ECU-B pin 27 to alarm pin 9) | AB-cabin | AntiTheft, riding AB-cabin (Dan B18 a) | it joins two non-hub plugs of two harnesses, so one plug gets a foreign wire either way |
| Opto board input 2 (`w_sw7_c`) and cruise ladder 5 V (`w_cru_5v_ac`) | AB-cabin | Dash | they land on the opto board / cruise resistor; the other end is a splice or a bussed plug |
| Oil warning LED (`w_oil_a` / `w_oil_k`) | ClusterLED + CSB3 | Dash | B8 = a merges both owners |
| A/C pressure switch signal (`w_ac_psw_in`, A5 pin 4) | AB-cabin | EngineRoom-C | A5 is harness C's plug in the bay; it ends at the cabin splice `SP-AC-PSW` |
| Dome feed (`w_pmu_dome`) | EngineRoom-C | CabinPower | both ends in the cabin (glove box to J/B No.1 1H-2), fault C4 |
| R/B No.2 W-L feed (`w_rb2_wl`) | EngineRoom-C | dropped, with `w_rb2_feed` | fault C1 / C4; Dan B17 b: AM1 feeds R/B No.2 through I2, as stock |
| Hazard feed (`w_haz_cp`) `passes_through` | EngineRoom-C | blank | glove box to IE1 at the LH kick, never in harness C |
| Horn relay output (`w_pmu_horn_cp`, K-HORN 87 to `SP-HORN` at the front) | CabinPower, `passes_through` EngineRoom-C | EngineRoom-C | it runs glove box to the horns inside harness C |
| Fuel pump relay coil wires (`w_fp85`, `w_k_fp_86_cp`) | AB-cabin / CabinPower, `passes_through` HeavyDC | `w_fp85` AB-cabin (sill run); `w_k_fp_86_cp` RearFuel, riding the AB-cabin sill run (Dan 2026-11-04) | B9 = a; signal wire is not taped to the 1/0 cable |
| Fuel level pair (`w_fl_sig`, `w45`) | AB-cabin, no carrier named | AB-cabin (sill run) | B9 = a |
| Kill switch IG legs (`w_ig_ks_in` IG2-15 to kill switch; `w_ig_ks_out` kill switch to alternator plug) | HeavyDC `passes_through` EngineRoom-C; EngineRoom-C `passes_through` HeavyDC | `w_ig_ks_in` AB-cabin (sill run); `w_ig_ks_out` EngineRoom-C `passes_through` AB-cabin | B9 = a; the alternator plug is harness C's |
| Trunk pin lead (`w_at_trunk_tie`) | AntiTheft, no carrier | AntiTheft `passes_through` AB-cabin | B9 = a |
| Siren and hood pin leads (`w_at_siren`, `w_at_gnd_a2`, `w_at_hood_tie`) | AntiTheft, no carrier | AntiTheft `passes_through` EngineRoom-C | they cross with harness C; the siren uses the driver-side (LH) fender / kick pass-through (Dan B19) |
| Starter S (`w_strl_c` / `w_strl_e`) | AB-cabin / AB-engine on Route 16 line 9 | `w_strl_e` AB-engine on its own short branch, DRB102 cavity 3 (Dan B20 a); `w_strl_c` stays AB-cabin (R/B No.4 to the cabin half of DRB102: one plug, one harness; Dan to confirm) | line 9 moves to HeavyDC's map (B6 = b) |
| HeavyDC devices H1, H2, H4, 18 and line 9 | Route 16 | Route 1 (HeavyDC map), greyed in the AB-engine editor | B6 = b; also removes the row 179 loops |

## Placement and lengths (B8)

Moved here from rule B8 on 2026-11-02 (phase 3, O6); binding as part of B8.

- Placement editor rule (Dan 2026-11-01): every harness gets a placement-editor pass (Dan places each device and draws its branch lines on the map) before its layout is built or it goes into harness.design; the saved placement becomes that harness's route and replaces its old route files and images in the repo (deleted, git history is the archive).
- Top views: front RIGHT, driver side up. No doubling back, overlap, hidden or empty leg; parallel runs spaced.
- Dan's saves are his (Dan 2026-11-02): no agent overwrites a saved placement, editor save or route without showing Dan the change and getting his OK first; the old save is kept as a backup either way.
- Editor devices (Dan 2026-11-02): one number per fuse / relay box (its relays in its note) and one for the ECU; bussed plugs are splices (no number, anywhere between ECU and bulkhead); a device outside the map's area is a hand-off point where its wires leave the bundle ("To trunk", "To front"), its far length from the other harness's map.
- Device spots (Dan 2026-10-28): the `devices` and `runs` in a route file's route data (Route 16 engine bay, Route 17 front) are the one definition of where each device sits and which line or branch it hangs on; a device has one spot in one file (a moved one is marked REMOVED in the other).
- Lengths from a route map: map length x 5.3 mm per EWD point (the 96 mm cylinder spacing) + 300 mm drop for a low-mounted part (`low: true` in the route data), an estimate until measured at the car.
- End allowance (Dan 2026-11-03, N3 = a): every tree length adds 100 mm at each wire end (2 x 100 mm per wire; `end_allowance_mm` in the layout file) for termination and service loop.
- AB-cabin (Dan 2026-11-02, A2-A4 = a): placed on the body manual under-body plan (DI-7), front right, driver up, in real mm (8.49 mm per PDF point from the 2525 mm wheelbase), plus an optional drop in mm per device; EWD p.44 (faded) is a look-only tab, since a 3-D view gives no lengths.
- The ECU engine harness tree and its master lengths are built from Route 16, harness C's from Route 17 (`route_trees` in the layout file); a splice sits where its legs part.
- Master lengths step (Dan L2 = a, 2026-11-02): a harness's master lengths are written from the layout tree at phase 4's lengths step, one harness at a time, with a before -> after list for Dan (OPEN-ITEMS row 183).
- A connector part-way along a line or run breaks out at least 6 in (152 mm) off it; the last connector at the end of a line or run may end it (Dan 2026-10-29).
- The engine bulkhead sits 16 in (406 mm) from where the trunk meets the firewall (`root_drop_mm`; Dan 2026-11-02 (J1); was 8 in / 203 mm, Dan 2026-10-29). The 6 in breakout rule above is unchanged.

## Gauge cases (B12)

Moved here from rule B12 on 2026-11-02 (phase 3, O6); binding as part of B12.

The device and its wire set the circuit.

- (1) Size the wire for the realistic highest load (peaks count, but they are not full time).
- (2) If the device's own connector has no contact for that size, drop to the next size its contacts take; that is the wire for the whole circuit.
- (3) Every other contact in the circuit (bulkhead, ECU, relay, splice) must take that wire; check each one, end to end.
- (4) The fuse protects that wire.
- (5) Last resort, only when there is no other way: split the circuit over two bulkhead pins and rejoin it.
- Ratings used for sizing (M22759/16, HP Academy), cabin 80 C / engine bay 100 C: 20 AWG 8 / 6 A, 18 AWG 11 / 9 A,
  16 AWG 15 / 12 A, 14 AWG 22 / 18 A.
- Any source (ECU output, fuse, relay, contact) rated below its load is flagged; a pass is a number, and a fail is asked of
  Dan before any part changes (Dan 2026-10-24).
- A step-down is the exception, not the plan: then a sealed Raychem (or generic) solder sleeve whose AWG range fits both wires, else a hand solder splice under adhesive heat shrink.
- Cases (Dan 2026-10-30, N72-N77): shared feeds (coils, injectors) are sized for all their loads and split into per-device branches; horns one size the whole run. Coils 14 AWG trunk + 16 AWG branches and grounds, COP 10 A; injectors 14 AWG trunk + 16 AWG branches, INJ 7.5 A; horns (PIAA Slim) 14 AWG throughout; ETB motor 18 AWG with TE 5-965906-1 + seal 1-967067-1 at the ETB (on TE drawing C-967616 for the Bosch MQS housing 1-967616-1; Dan 2026-10-31), ETB 7.5 A; fuel pump 10 AWG feed and ground to the pump's own short lead, FP fuse 40 A (N79); EPS 8 AWG + 50 A, solder splice onto the Toyota repair-wire lead 82998-12500 (8 mm2, so size-for-size; RM06H0E).
- CAN node feeds (Dan 2026-11-04, N5 a / N6, "check AWG amp rating of wires"): CAN-Lambda on the 10 A LAM fuse and K-ON:
  14 AWG TXL in the cabin (about 17.6 A), DRB102 cavity 95 size 12, 12 AWG then 16 AWG Tefzel in the bay (12 A); the
  RealDash Pi on the factory CIG & RADIO 15 A, so its tap is 16 AWG Tefzel (15 A; TXL 16 is about 12 A); the K-ON coil
  feed from the IGN 7.5 A fuse 18 AWG TXL, and the two older 1H-7 taps (`w_ig2_in`, `w_ign`) 20 -> 18 AWG TXL for the same
  fuse (Dan 2026-11-04; ECU-B pin 28 takes contact 3-1447221-3, 18-16 AWG). Known exception (Dan 2026-11-04, accepted):
  the CAN-Lambda's DTM size 20 contacts are rated 7.5 A (Link's own plug takes no larger contact) against its 8.1 A peak
  (manual p.5), a peak only during heater warm-up.
- Fans (N78, Dan 2026-10-31: 12 in, not bought yet): sized for an 18 A 12 in fan (SPAL high-performance range 14.5-18 A): 10 AWG, size-8 DTHD sockets (8-10 AWG), relay FASTON 280756-4 (12-10 AWG, insulation 3.4-5.1 mm; 280755-4 grips 5.0 mm and up, too big for 10 AWG Tefzel), TE 36161 ring (12-10 AWG) at the AMI studs, AMI FAN and FAN2 30 A. Re-check against the fan's data sheet once bought. Each uprated fan has two single-pin leads, so two DTHD06-1-8S plugs per fan (`FAN-RAD` / `FAN-RAD-GND`, `FAN-COND` / `FAN-COND-GND`) are right (Dan 2026-11-04, Y1 b).

## Drawing rules

Shop-drawing rules. Rev letters live in `cad/DRAWING-REVS.md`. Gates: `cad/check_drawings_current.py` (R183, R196) and `cad/check_drawing_rules.py` (R184–R196 and the R200 initials check K4).

| Rule | Source |
|---|---|
| Never show hidden lines in any view. Center marks and center lines for holes and radii are kept (and added where useful). | R150 (Dan 2026-10-17) |
| The model drives the rev letter; drawing and model letters always match. Letters run A-Z skipping I, L, O, Q, then AA, AB, ... (R152); Rev A only for a brand-new model. Drawing-only (clerical) changes to a released drawing add .01, .02 ...; a model change bumps the letter. | R147 |
| Redlines go on the drawing first, then the model is fixed, then the drawing is regenerated from the model. | R147 |
| The model is the master: every model change regenerates its drawing (same PR); a wrong drawing is fixed in the model or its source script, never by hand-editing the drawing. Drawing rev = model letter, or model letter + .NN for a clerical drawing-only change; models never get decimals. Gate `cad/check_drawings_current.py`; after regenerating a drawing run `python cad/check_drawings_current.py --update <part no>`. | R183 |
| No rev in file names; the letter lives in the title block and the register. | R148 |
| Rev log table, top right of sheet 1: Rev / Description / By / Date (dd/mm/yy), from the model's `<part no>.REVLOG.md` beside its STEP (plain `REVLOG.md` only when the folder holds one STEP). One row per PR / release, no clerical rows, Rev A = "Initial", newest 6 rows shown, full history kept in the file; title-block letter = newest row. | R152 |
| No visible mesh triangles, facet or seam lines in any drawing or render; parts look like smooth machined bodies. | R152 |
| Minimum wall thickness applies to structural / critical features only; anything questionable is flagged for Dan. | R151 |
| Model files are STEP only; STL only as a print-job file for a printed part. | R152 |
| Every model says what made it (`MADE-WITH.md` + register column). | R149 |
| Every fabricated assembly has its model and an assembly drawing, reissued with its parts. | R182 (B23) |
| No notes about things that are not in the model: no edge-break notes (also out of the tolerance block), nothing "not modelled". Replaces R138's drawing note. | R191 |
| Bought parts come from the real maker STEP (the models folder, B26), never an envelope model; no note says "envelope". | R184 |
| No pin / socket gender notes: gender belongs to the connector shell installed. | R185 |
| A balloon only where its part is clearly visible, its leader on that part; hidden parts are ballooned in an exploded or alternate view. | R186 |
| Tangent edges show in every trimetric view. | R187 |
| Balloons never overlap or crowd. | R188 |
| Fuse boxes: every fuse and relay has a note label beside its balloon naming its circuit or device (from the SoT). | R189 |
| Every harness wire landing on a fuse box carries its harness-drawing wire-end label (R156). | R190 |
| Change notes (what was fixed, markup dates, R / PR numbers) go in the rev log, never in NOTES. | R192 |
| Assembled views balloon only the primary parts (enclosure, lid). | R193 |
| Never label a screw that is not in the model; hidden screws go in an exploded view with dotted lines. | R194 |
| Notes are for a shop machinist: ELI5, short, plain steps. | R195 |
| Anything physical (a BOM line added / removed / swapped, a dimension, a part moved, a feature) is a model change: model letter bumped and merged first, drawing regenerated after. Only clerical drawing-only changes take .01. | R197 |
| Models first, drawings last: model-only PRs, then every drawing regenerated in one pass (`regen_pending` in `drawing-models.json` meanwhile). | R196 |
| DRAWN (title block) = the initials on Rev A of that drawing, never changed. Rev-log BY = the initials of the person who requested that change, never an agent or tool name. Always DG for this project. One per-computer file `%USERPROFILE%\.drawing-initials` (env `DRAWING_INITIALS`); missing = a person is asked once, an agent stops. | R200 (Dan N41 = B, 2026-10-19) |
| .01 clerical revs never appear in the REVISIONS table (full letters only; .01 is tracked in git); the title-block REV still shows e.g. D.01. | R200 (Dan via Dispatch 2026-10-19) |
| Every full-letter rev made from 2026-10-19 on puts its letter in a triangle next to each changed item (and the BOM row of a changed part number); old triangles stay on later revs (N42 = B). Declared in `spec['rev_marks']` or `<pn>.REVMARKS.json` beside the rev log; gate K5; revs before that date exempt (`cad/rev-marks.json`). | R200 (Dan N42 = B) |
| Every model has a `cad/README.md` row and a trimetric PNG; reuse Fusion documents (10 max). Every fabricated part and assembly has a drawing with a BOM (also as an Excel copy, in sync); each part / body its own model file; OTS parts need a model only, a modified OTS part a drawing + model. | B26 (moved out of the rule 2026-11-02) |
| Fuse boxes: small, PA12 MJF, no printed threads, live parts >= 3 mm apart, copper to copper (`cad/fusebox/src/spec.py`). | B27 (moved out of the rule 2026-11-02) |

## Shipping (B28)

Moved here from rule B28 on 2026-11-02 (Dan L3 = a); binding as part of B28.

- Never merge `main` into a conflicting PR: stop, tell Dan on its own line ("PR #n now conflicts with main on <file>"); only after
  his answer, cut a new branch from `origin/main`, carry the files over, close the old PR; no rebase, no force-push (Dan 2026-11-01).
- Never remove your own worktree.
- `git pull --ff-only` at session start and after every merge, then session-start unless work stops (Dan 2026-10-31 / 11-01).
