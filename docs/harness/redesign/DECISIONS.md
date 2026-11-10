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
A/C: both factory A/C amps stay (Dan 2026-10-20). D16 (Dan 2026-10-25): A15 drives `k_acc` (pin 8 to coil 85); the Link only sends the ACT kill (Aux 4); pin 2 hard-grounded; Ign 8 is tacho to pin 18; no clutch-on to the Link. Lock sensor (Dan 2026-10-26): same tacho through 4.7 kΩ to A15 pin 9 (OPEN-ITEMS History 2026-10-21 N61). Sensor common: keep cabin splice `SP-AC-SG` (replaces E10); it lands on auto A/C amp A32 pin 15, the Y wire that feeds one end of every A/C sensor (1993 TIS EWD p.211-212; the page prints TW over pin 15 and SG over pin 20, whose B wire goes to A25 alone; pin kept, Dan N19 a 2026-11-05). The A/C pressure switch is the factory trinary switch, wired to the factory A/C amp; factory yellow-red is that switch output (A5 pin 4 through joiner E10 to A15 pin 13; 1993 TIS EWD p.211), not the sensor ground; sensor common is yellow (1993 TIS EWD p.211-212 above; reading aids 1990 ST185 EWD p.150 / p.152, 1992 EWD132U p.219). Clutch (Dan 2026-10-26): one ECU clutch input only — cruise clutch switch C17 to CSB3 pin 20 (VDI6) for flat-shift; clutch start switch C11 completes the starter circuit in hardware and is not an ECU input. Oil warning LED on CSB3 L4 (cavity 26, 0x643 byte 3). Brake fluid level switch is a factory safety item, not needed, not connected.

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
  return of a sensor the ECU powers, 12 V devices ground on the battery-negative bus, except a factory load or a part that
  replaces one, which keeps that load's factory ground point (N83 a). Detail: "Grounds (B10)" below.
- **B11 Power.** No factory fuse / relay box is left in the engine bay; factory boxes used: cabin J/B No.1, J/B No.3, R/B No.2, R/B No.4 only.
  New feeds: glove-box POWER / LOGIC (+ trunk `k_fp`, 40 A); README "Factory boxes (B11)". Alternator fuse 175 A (MRBF, Gauge cases); stop: kill or ACC.
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
- **B17 CAN wiring.** One bus (CAN 1, bus 2 unused), the CAN-Lambda on it, shielded the whole run. The trunk starts at ECU
  plug C and runs past the switch board, cluster and Pi taps to the CAN-Lambda (Dan P1, 2026-11-09); each node's own fused +12 V and its ground, never ECU ground or chassis. Detail: "CAN wiring (B17)" below.
  Power (Dan 2026-11-04, X1): the ECU per Link's hold-power wiring (ignition wake, the ECU holds main relay K-EFI for
  the ETB); centre cluster and CSB3 on LOGIC Bus 2 (live with the ECU); CAN-Lambda on its own ON-only relay K-ON, no hold
  ("Relays (B15)"); RealDash Pi on the factory radio circuit (J/B No.1 CIG & RADIO 15 A, ACC), shared with the future radio, through its own 5 A inline fuse at the radio tap (Dan N58 a, 2026-11-07; N107 a, 2026-11-08); Dan adds a
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
  part has a plain name, no codes where Dan reads (fuse box and relay codes excepted). Only asked-for parts. Detail: "End labels and names (B22)" below.
- **B23 Models drive drawings.** The CAD model is the master: a physical change goes in the model first, then the drawing is regenerated, never hand-edited. Revs: Drawing rules below.
  Gate `check_drawings_current.py` checks the register, rev letters, issued PDFs and tracked fingerprints; it skips the STEP model files (in Dan's models folder, B26; Dan G2 a).
- **B24 Initials and revision marks.** DRAWN and every rev-log BY are a person, always `DG` (`.drawing-initials`), never
  an agent; no file = stop and ask. Full-letter revs from 2026-10-19 get rev triangles (Drawing rules below).
- **B25 What a drawing shows.** As the Drawing rules below list: no hidden lines or mesh facets, tangent edges in
  trimetrics, makers' own models, balloons only on visible parts, shop-only NOTES. Gate `check_drawing_rules.py`.
- **B26 CAD work.** CAD stays frozen unless Dan asks (model and drawing detail: Drawing rules below). Models live only in
  Dan's models folder (OneDrive `Desktop\models`, `publish-to-models`): latest rev + 2 previous, bought parts as maker models there; drawings / BOMs are copied here for the checks.
- **B27 Fuse boxes follow the harnesses.** Boxes are configured to match the harnesses (Dan 2026-10-26; build rules: Drawing rules below); until the revisit (row 107) the box CAD may lag and `sot/fuse-relay-map.csv` wins.
  Spare fuse and relay seats in the boxes are allowed and kept as spares: no cleanup of unused seats (Dan 2026-11-04, Y7); the box CAD is frozen, so a seat "removed" by a harness change stays in the model as a spare, never stale (Dan 2026-11-07). Ends at a box: "Bus bars and fuse box ends" below.

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
      +-- docs/harness/tools/ST185-harness.layout.json   the layout tree: owns every wire length (N69 a); --write-lengths copies them into the master
      +-- docs/harness/routes/ + placement editors   device spots (B8)
      +-- docs/sourcing/PROJECT-BOM.*  generated shopping list
```

New wiring facts go into the master row first; `channels.csv`, the IO table, the drawings and the BOM follow. Device pin, pin name and whether that device gets a shield go into `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` (one shield flag per device). Which ECU pin a device wire lands on is owned by the ECU; ECU pins never move. If anything disagrees with the master on a pin, the other thing is wrong. No script writes the master or `channels.csv`, except `build_drawings.py --write-lengths`, which writes the placed harnesses' `est_length_mm` from the layout tree ("Placement and lengths (B8)", Dan N69 a). `python tools/check_all.py` must pass before every commit.

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
| `docs/harness/tools/ST185-harness.layout.json` | The layout tree: owns every wire length (Dan N69 a); `build_drawings.py --write-lengths` writes them into the master for the placed harnesses, `--check` fails on a difference |
| `docs/harness/routes/` + placement editors | Device spots (B8) |
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
- The ECU splice point: every cabin power, ground and rail splice sits at one place by the ECU plugs. +5 V (A32) is two bussed DT plugs `BUS-5V` (12-way) and `BUS-5V-2` (8-way, linked); Gnd Out A24 and B22 are their own 12-way bussed DT plugs `BUS-GNDOUT-A` / `BUS-GNDOUT-B` (no A24-B22 tie); +8 V, switched 12 V, the ECU A5 feed and the ECU power ground are soldered splices there (R169 parts: `DT06-12SA` / `DT04-12PA-P021`, `DT06-08SA` / `DT04-08PA-P021`, 13 A per pin; each plug drawn mated to its bussed receptacle, every used pin one signal name, no bridges: "harness.design files (B6)" R6, which replaced N57 a's bridges 2026-11-08). The ECU power ground splice joins A25, A34, B25, B34 only and runs one wire to the POWER box battery-negative bar GND stud (R216).
- Splice sizing (B12): by the combined gauge it joins; not for drains. Bulkhead substitution (B7): only a complete matching set from the maker's datasheet.
- A wire belongs to the one harness that carries it (`harness` column); `passes_through` names any harness it runs through. Mating halves (DRB102) are checked cavity for cavity by `check_wiring.py` M1.
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

Labels and names (Dan 2026-11-08, standing; these win over any older text on this page, in "End labels and names (B22)", the README "Pin text" rules and N57 a; harness.design's own way: a component's label is its name and replaces its ID wherever it is named, the IDs (C1, W3) show only with "Show component IDs" on, docs.harness.design/feature/component-ids; a signal set on a cavity propagates along its net, same-named global signals are one net, docs.harness.design/feature/signals; a device is the connectors and terminals that plug into it, docs.harness.design/guides/device):
- R1 (2026-11-08): a connector's name says what it is or what it is for, in plain words ("Firewall bulkhead connector (cabin side)", "Sensor ground bus plug, ECU plug B"), never a code (DRB102-CABIN, BUS-5V-2: the part number already says which part it is). The master `<end>_name` is that name; ids stay as keys only. The connector header shows only the name: the app's ID (C1, C2) is hidden unless a viewer turns on "Show component IDs" (canvas `I`, PDF export "Component IDs"), a per-viewer setting the document cannot store. Replaces the B22 rule "any code follows in parentheses" for harness.design labels.
- R2 (2026-11-08): pin text is the basic signal on that pin ("+5 V", "Coil (-)"). A wire's label says what that wire is for ("+5 V cruise ladder"), never its wire id or part number: the master column `wire_label` (the generators put it on the wire's ident label).
- R3 (2026-11-08): a pin's signal names the signal type ("+5 V sensor supply", "Sensor ground A24 (ECU Gnd Out)", "Shield drain A7"), one name per net at its hub ends (ECU, bulkhead, inline, bus plug, splice, box and factory-tap ends), never a list of every device on the net; a device is named only at that device's own end and on the wire label. Replaces the README "Pin text" rule that bulkhead, ECU and splice ends name the device.
- R4 (2026-11-08): notes never repeat what the connector or terminal label already says. An OEM splice note stops at the factory wire and pin: "Splice to OEM wire Y - cluster plug C14 (C) pin 8" (replaces the N13 a / N16 a long form: function and location are on the label and pin text). Terminal labels are short ("Cluster plug C14 (C) pin 8").
- R5 (2026-11-08): no empty connector in a schematic (no wired cavity and no reason to be drawn): it is left out. Replaces V1 a's "drawn whole in both files" for a plug with no wire in that file (ECU plug C in AB-cabin 1).
- R6 (2026-11-08): a bussed connector is drawn as its real bussed part mated to its real mating housing, like any connector pair: the harness plug (TE DEUTSCH DT06-12SA + wedgelock W12S, sockets 0462-201-16141; DT06-08SA + W8S) mated to its bussed receptacle (DT04-12PA-P021 "one 12-pin buss" / DT04-08PA-P021 "one 8-pin buss", key A to match the plugs; the receptacle's wedgelock TBD by the TE drawing), every used pin with the identical signal name (one global signal, the bus), no pin-to-pin bridge links. Replaces N57 a's INTEGRAL bridges (the 33 `br_*` rows are gone; `check_wiring.py` B1 now checks one signal name per bussed plug). The INTEGRAL links of the jump bus bar and the MRBF fuse block (N55 a, N61 a) stay.
- Bussed receptacle = cap (Dan 2026-11-09, standing): the bussed receptacle has its pins tied together inside; wires land only on the plug half (DT06-12SA / DT06-08SA), never on the receptacle, which has no wires and no wire-end terminals (`check_wiring.py` B2). In layout views the receptacle is a plain mated cap drawn face to face with its plug. Bussed plugs are harness parts, never fuse box parts ("there's not any bussed plugs in the fuse boxes"): they sit outside any fuse box group outline (beside the box), stay on the harness BOM and are never excludeFromBom as box parts.
- R7 (2026-11-08): ring terminals are shown as ring terminals with their maker part where the master knows it (one part number on that stud): box studs and ground studs (EA, EB, ID, BL). A stud whose lugs carry different part numbers (EA: 52291, 70102, 70250) or TBD keeps a plain ring until each lug is its own terminal (needs the ground-stud audit).
- R8 (2026-11-08): no long descriptions: a name or pin text says what it is, where it goes, its purpose and where it sits, briefly ("Cowl plug II1 pin 3", "Radio ACC +12 V (CIG & RADIO 15 A)", "RealDash Pi inline fuse 5 A").
- R9 (2026-11-08): nothing labelled misleadingly: "LED IG +12 V" (reads like an ignition LED) is "Ignition +12 V for the cluster LEDs".
- R10 (Dan 2026-11-09 23:29, standing, every harness file): any wire that continues into another harness file carries a note at that end, built from these parts in this order, each only where it applies: "to <harness file name>" (the file's name without its rev letter, so the note does not go stale); the physical location in the car of the destination device, connector, bus or component; the FSM document title and page and / or diagram where it can be looked up; the component, fuse or relay and its terminal; the connector and pin number (just the pin when the component has one connector; or the ground stud or other landing); the wire colour when the wire is spliced onto another wire; or "flying lead" when it connects to nothing yet or is a spare. Why: the other end can be found and run exactly where it needs to go, and bundled with the right trunk and branch of the other harness. A part not confirmed from the manual or the master is written TBD, never guessed. A two-wire in-line "splice" that only marks where one wire crosses into another file or ends as a capped lead (the five AntiTheft alarm "splices": shock sensor +12 V, alarm +12 V, alarm ignition, door trigger, hood trigger) is not a splice: it is one whole wire, shown as "continues to ..." or "flying lead" (how the master models it: OPEN-ITEMS Needs Dan T3). Applied to each file when it is next built.
- T3 (Dan 2026-11-09 23:49: "I don't really care as long as it works every time and it appears in my harness design files the way I want it to"; the agent picks): the five AntiTheft alarm two-wire joins become one wire each, end to end, owned by AntiTheft (the harness of the part it serves, B8), with no splice; each ends at the alarm spot as a labelled, capped flying lead (`Loose` terminal). The other two-wire joins in the master stay (pop-up motor pigtail joins, jump bar studs, A/C sensor common, CAN-Lambda and switch board joins): they are real joins. Per the harness.design editing guide a splice has at least 2 wires, so no file ends a wire on a one-wire splice (README "harness.design"). Applied with the cabin redraw.
- How (2026-11-08): `build_drawings.relabel` applies R1-R9 to every generated document after placement (names from the master, `wire_label`, short notes, bussed receptacles mated, empty connectors dropped, ring parts), so positions stay as placed; a box member inside its device group (LOGIC box, box relays, box rings) cannot be relabelled by `edit_document`, so a live file's group members change in the app or at that file's next rev. (Box groups are gone since R1 a, Dan 2026-11-09, so every end can be relabelled in place.)

- File names carry a rev letter from Rev A (`ST185-<harness> Rev A`; a physical change = a new file at the next letter, Dan deletes the old; a view-only change keeps the file and letter; Dan 2026-11-02).
- Layout view = formboard (README).
- `build_drawings.py --check` keeps the layout tree, master lengths, the Option A wire lists ("Wire lists" below) and the DRB102 map current; the pin chart is the one pinout.
- The OEM splice notes come from the master via `build_drawings.oem_splice_note` (the OEM splice reference was retired, Dan N22 a, #534).
- N118 b (Dan 2026-11-08, for the 2026-11-08 label pass): where Dan's own live edits in a harness.design file (his labels, opto pin texts) clash with the label ops generated from the master, the generated ops win and overwrite them; files are built from the master. Dan 2026-11-08: his live edits were tests, so the generated files overwrite them and none of his deletions (AB-cabin 1 ECU plug C, bridges, the Dash CAN shield splice and its wires, his key-B plug and jumper wires) go into the master.

## Grounds (B10)

Moved here from rule B10 on 2026-11-02 (Dan L3 = a); binding as part of B10.

- ECU power grounds (A25, A34, B25, B34) splice together, one wire to the POWER box battery-negative bar GND stud ("Bus bars and fuse box ends" N60 a).
- Gnd Out takes only the return of a sensor the ECU powers (+5 V / +8 V); anything fed from a fuse box or the SW12 bus grounds on the battery-negative bus with the other 12 V devices, never on the ECU (Dan 2026-10-31; row 170); factory-load grounds: below (N83 a).
- Factory-load grounds (Dan N83 a, 2026-11-08; replaces the N82 a exception): a factory load kept on new wire, or a part that replaces a factory load like for like (LED for a bulb, new headlamps, uprated fan or pump), keeps that load's factory ground point (1993 EWD page cited in the master), or the front body point on the same side (EA RH, EB LH). Only where the path to that point is kept factory cabin wiring (e.g. dimmer -> J6 -> ID) or a new wire to a ground stud named in the master that exists in the new design. Every ground wire forward of the firewall is new (B9); only the ground points are factory. Never for electronics with CAN, ECU or sensor ties (they stay on the battery-negative bus). Add-ons that replace no factory load are not covered: the alarm stays a named exception (N43 b); heavy loads may still use chassis. In the master each such ground wire's note carries the tag `factory ground (N83 a)` with its 1993 EWD page; `check_wiring.py` E3 accepts a tagged wire on a body ground stud (`GND-*`) and still fails it for CAN, ECU or sensor ties; the alarm ground `w_at_gnd_a1` stays in its E3 known list as the one named exception.
- Shield drain only to the ECU shield pin; heavy loads may use chassis.
- The ignition coil ground goes to the POWER box NEG bar through bulkhead cavity 4 and the cabin ground splice `SP-CABIN-GND`, not the engine block (Dan 2026-10-29; N60 a 2026-11-07).
- ECU +8V Out feeds the cam sensor and the gearbox speed sensor only; the VSS returns on Gnd Out, DI 8 pull-up off (Dan 2026-11-01).
- Alarm grounds (Dan N43 b, 2026-11-06): ring terminal `T-AT-GND` at the alarm spot (the `AL-GND` lead and the siren ground pull-wire) to a chassis ground point Dan picks at install, a named exception to B10.
- Example of the factory-load rule, the Dash LED ground (Dan N82 a, 2026-11-08, replaces N74 a; under N83 a since 2026-11-08): `w_led_gnd_out`, from the LED ground splice `SP-LED-GND` (the - legs of the turn LH / RH and high beam cluster LEDs), keeps the factory ground point ID (LH kick): the LEDs replace the factory cluster indicator lamps, whose ground is C13 (B) pin 1, W-B, to ground point ID (1993 EWD Combmeter p.206-208, TSHWL p.130, HdlitUSA p.116; `st185-celica-repair-manual` `manuals-electrical/`). LED current only (mA); on the cabin ground splice `SP-CABIN-GND` it would push `w_cabin_gnd` over 8 AWG by the B12 fuse-sum rule.
- Dash LED polarity (1993 EWD check, 2026-11-08): LED + on C13 (B) pins 2 (turn LH), 11 (turn RH) and 12 (high beam), LED - to `SP-LED-GND`, is correct. Pin 12 hangs off the low-beam ground R-L at splice I2: ground on LOW, about +12 V through the low-beam filaments on HIGH / FLASH. So the high-beam LED's +12 V comes through the factory low-beam filaments: any headlamp change must recheck it. Rechecked 2026-11-08 (Dan N89 a): no lamp hangs on R-L any more, so the high-beam out feeds the R-L line through R-HB (220 ohm, 1 W) at IE1-11 and the LED lights at HIGH / FLASH only ("Headlamps, DRL and pop-ups" below).
- Grounds by kind (Dan 2026-11-08, standing): never join grounds just because a wire says "ground": pick the kind (device power ground, shield drain, sensor ground) and its place for each one; layout views show the real ring terminal where one is used.
- N106 a (Dan 2026-11-08; replaces the `w_led_gnd_out` wire of the N82 a example above; in the master 2026-11-08): the LED ground splice `SP-LED-GND` (turn LH / RH and high-beam LEDs only) splices onto the factory cluster ground C13 (B) pin 1 W-B (to ID, N83 a); `w_led_gnd_out` is dropped.
- N109 a (Dan 2026-11-08; in the master 2026-11-08): the opto board input common (COM1) gets its own wire to the cabin ground splice `SP-CABIN-GND`, labelled "Opto input return (brake / reverse / tail signals)", never "COM1".
- N103 (Dan 2026-11-08; in the master 2026-11-08): A/C amp A15 pin 2 ("coolant OK") goes to the nearest body ground by the amp, off `SP-CABIN-GND`; `w_cabin_gnd` then returns 40 A and drops to 10 AWG (B12), replacing the 8 AWG / 50 A sum in N60 a below (its ring is Panduit PV10-56R, as `w66`). F1 a (Dan 2026-11-08): that nearest body ground is IG (RH kick, the R/B No.4 set bolt), as in the master.
- N102 + N108 a (Dan 2026-11-08; in the master 2026-11-08): the cruise stalk return is "CSB3 reference ground" (CSB3 SGND); the cruise ladder pull-up comes from the CSB3's own +5 V, so `w_cru_5v_ac` is dropped; a cut row is added for the factory BR path to body ground IE (EWD page TBD).

## Bus bars and fuse box ends

Binding as part of B10, B12 and B27. Basis (Dan 2026-11-07): the harness.design device guide (docs.harness.design/guides/device): a fuse box is a device, the harness ends at its lugs, one terminal per post in a named Group with a Group Part; same-named global signals read as one net. (The Group / Group Part part is superseded by R1 a, Dan 2026-11-09: no box groups.)

- Fuse box guts out of scope for harness files (Dan 2026-11-09, "you're not drawing the fuse box guts. Out of scope"; same as his 2026-11-07 rule "draw each wire as a wire end coming to the box"): a wire with both ends inside the POWER / LOGIC box (box studs, box relays, the LOGIC fuse outputs, in-box splices) is the fuse box's own wiring. Dan R1 a (2026-11-09): "The box insides are modeled in the model only": box insides and their parts live only in the fuse box CAD model and its BOM (`cad/fusebox`, OPEN-ITEMS row 107); the master and the harness files stop at the box. The 19 box-internal rows were removed from the master 2026-11-09 (18 CabinPower: the LOGIC fuse outputs and AMI studs to the box relays, the Bus 1 / Bus 2 feeds, the K-ON coil ground ring; `w_acc86` AB-cabin), with the in-box splices SP-HR, SP-DRL12 and SP-ACC12 (no harness wire used them). Harness files show only harness wires ending at the box: a ring on a stud, or a terminal at a box seat labelled box, seat and terminal ("LOGIC box seat M8, terminal 86 - DRL relay (K-DRL)") or at a LOGIC fuse output (`build_drawings.box_seat_ends`); no relay bodies or box guts are drawn. Relays outside the boxes stay drawn devices: K-EPS (B4), RLY-DRL (beside the LOGIC box). The switched +12 V bus plug `BUS-SW12` is a harness part beside the LOGIC box, not a box part ("there's not any bussed plugs in the fuse boxes"), so its wires stay harness wires.
- S1 a (Dan 2026-11-09): the trunk battery relay block (B3) is a box like POWER / LOGIC: its insides live only in its model; K-FP is not drawn and its harness wires end at "Trunk relay block seat K1, terminal <n> - Fuel pump relay (K-FP)". Block-internal rows removed from the master: `w_fp_30` (block fuse FP -> K-FP 30) and the K-FP 87a spare row.
- S2 a (Dan 2026-11-09): POWER box fuse output AMI OUT-1 is real (model cover label "BUS1 50A"): it feeds LOGIC Bus 1 (8 AWG, a box-to-box cable owned by the box model); `sot/fuse-relay-map.csv` carries it.
- U1 a, Dan 2026-11-09: the 50 A fuse on POWER AMI OUT-1 -> LOGIC Bus 1 stays (the box model owns that cable).
- S3 (Dan 2026-11-09, standing): the box copper bars and the number of spots in each box model are frozen: spots may be renamed and reused, but adding spots needs a model redesign, so existing spots are used first (the boxes hold the most spots needed). The box cable entries / exits are planned for clean, organised cables; a major change to cables entering or leaving a box also needs light redesign. Every change that needs box remodelling is recorded in the "Box remodel list" (OPEN-ITEMS row 107) and done after all harnesses are made. Checked 2026-11-09: LOGIC BUS2-12 / BUS2-13 are existing own-input seats in the model (Bus 2 positions 12 / 13, MRS / B30), so no spot moves.

- N64 a (Dan 2026-11-07 10:08): inside the two frozen fuse boxes (POWER, LOGIC) each wire ends in its own ring terminal named by the stud it lands on (`T-PWR-*` / `T-LOG-*`, master name "<bar or fuse>, <stud> stud", e.g. "POWER box NEG bar, GND ID stud"); every stud on one bar shares one global signal ("POWER box NEG bar", "POWER box + bar", "LOGIC box Bus 1", "LOGIC box Bus 2"; an AMI fuse output stud is "POWER box AMI OUT-3 fuse"); each box is one Group with a Group Part (the generators emit the groups, N81 a; README "Fuse box ends" lists the members); no splices or jumpers inside a box; the LOGIC fuse outputs stay box slots (connector `LOGIC` pins); a wire landing on an AMI fuse stud or a bus-strip feed stud is a ring terminal named by that stud (replaces N63). The old `POWER-NEG-BAR` terminal and `POWER-STUDS` pin NEG are merged into per-stud rings; the old `POWER-STUDS` "ALT" pin was the + bar RADLOK+ stud. Stud names come from the box design (`cad/fusebox/src/spec.py` REV7 `neg_studs` / `pos_studs`, `AMI_ROWS`, `FEEDS`); `check_wiring.py` P1 checks them. 1/0 lugs: Klauke 6R8 (spec.py `LUG_M8`).
- N65 a (Dan 2026-11-07): one ring terminal per wire; the BOM counts every lug (a lug the frozen box parts list already buys is counted there once).
- N59 a (Dan 2026-11-07): the LOGIC box has no negative bar; its grounds land on the POWER box negative bar.
- N60 a (Dan 2026-11-07): the POWER box NEG bar small GND stud carries exactly 3 rings: the ECU power ground `w66` on its own, the K-ON coil 85 ground `w_k_on_85_cp` on its own (ring TE 320572, 22-16 AWG, M8, 11.91 mm wide), and `w_cabin_gnd` from the new cabin ground splice `SP-CABIN-GND` (glove box, beside the POWER box), which gathers every other small ground (CAN-Lambda `w_lamg_ac`, coils `w_cop_gnd_ac`, flex fuel `w_flex_ret_c`, A/C amp `w_ac_cool_gnd`, CAN nodes `w_can_gnd`, since T1 a `w_gnd_clu` / `w_gnd_csb` / `w_gnd_rd`). `w_cabin_gnd` (B12, the sum of the fuses it returns): LAM 10 + COP 10 + DEV 5 + CSB 5 + Pi 5 + SW12 5 (flex fuel) + R/B No.4 A/C 10 = 50 A: 8 AWG Tefzel (IEWC suggested ampacities, up to 3 conductors in a cable, 110 C: 8 AWG 60 A, 10 AWG 45 A), as the 8 AWG `w_hc_fb` on the 50 A AMI BUS1 fuse. The rings for `w66` and `w_cabin_gnd`: N68 a below. Their master names (2026-11-08) tell the 3 apart: "POWER box NEG bar, GND stud, ring 1 of 3" (`T-PWR-NEG-GND-1`, `w66`), "ring 2 of 3" (`-2`, `w_k_on_85_cp`), "ring 3 of 3" (`-3`, `w_cabin_gnd`); `check_wiring.py` P1 reads the stud before the ", ring" suffix. Since R1 a (2026-11-09) `w_k_on_85_cp` and `w_hc_fb` are box insides, kept only in the fuse box CAD model (the ring 2 seat stays on the stud). (`w_cabin_gnd` gauge superseded: 10 AWG since N103, Dan 2026-11-08.)
- N68 a (Dan 2026-11-07): the GND stud rings are Panduit PV10-56R for `w66` (12-10 AWG, 5/16 in / M8 stud, W 13.2 mm; Panduit drawing A41187) and (until N103, 2026-11-08: since then PV10-56R too, 10 AWG) Klauke 2R8 for `w_cabin_gnd` (nominal 10 mm2, M8, b 15 mm; Klauke tubular cable lug ordering table; Klauke gives no AWG range, so its fit on 8 AWG, 8.37 mm2, is TBD by the maker, as the box's 2R5 on the 8 AWG BUS1 feed). The rule for this stud is "ring eyes do not overlap": the GND IG 1/0 lug and every ring on the GND stud are one ground node, so touching is harmless. The frozen box CAD (models folder `st185_fusebox_1101` revB) gives 8.0 mm from the GND stud (x 102.0) to the GND IG 6R8 lug edge (x 94.0) and 8.5 mm to the printed barrier (x 110.5), so a ring eye up to 16 mm wide fits (2R8 15 mm: 0.5 mm to the 6R8, 1.0 mm to the barrier). This replaces the 13.0 mm limit, which came only from `cad/fusebox/src/spec.py` REV7 `neg_lug_gap` (1.5 mm, "practical, not an electrical clearance", N3) and `small_ring_b`; both stay as they are in `cad/`, because `small_ring_b` sets the printed lug-pocket walls and snap arms in `build_fusion.py` and `neg_lug_gap` feeds `check_clearance.py` (frozen box, no geometry change), so the rule lives here and in the master notes. Why: no maker 10 or 8 AWG M8 ring is 13.0 mm or narrower (TE 320576 13.49 mm, Panduit PV10-56R 13.21 mm, JST 5.5-S8 13.21 mm, Molex 19193-0120 13.72 mm, Klauke 2R8 15 mm).
- N81 a (Dan 2026-11-07): the fuse boxes are devices: each is a harness.design Group with a Group Part (`gp_fb_100p` "ST185-FB-100P", `gp_fb_100l` "ST185-FB-100L", in the document's parts), excludeFromBom on the group, because the box parts lists in `cad/fusebox` buy the box and its relays. The `LOGIC` connector's part is the whole box assembly ("ST185-FB-LOGIC rev 7") and each box relay connector's part is the relay itself, so both are excludeFromBom too (parts kept for identification; no double count); the ring terminals stay counted (N65 a). The generators emit the groups (`build_drawings.box_groups`, the format the app writes), with only the members each document has: POWER box = the `T-PWR-*` rings and K-EFI, K-FAN, K-FAN2; LOGIC box = the `LOGIC` connector, the `T-LOG-BUS1` / `-2` rings and K-HL, K-HR, K-HORN, K-ETB, K-ACC, K-EPS-EN, K-ON. K-EPS (B4) is in neither. **Superseded by R1 a (Dan 2026-11-09): no box groups; box seat ends are plain labelled terminals, box insides live only in the box CAD model.**
- N80 a (Dan 2026-11-07): in AB-cabin 2, K-ACC stays outside the LOGIC group until CabinPower is built: grouping it there pulls splice `SP-ACC12` into the group and breaks wire W36's route (`build_drawings.BOX_GROUP_OUTSIDE`); in EngineRoom-C K-ACC is in the group. It is excludeFromBom either way. **Superseded by R1 a (Dan 2026-11-09): no box groups.**
- Engine-bay jump bar (Dan 2026-11-07): the Blue Sea 2104 bar is one splice per stud, `SP-JUMP-1` .. `SP-JUMP-4`, each with its own lug, neighbours joined by INTEGRAL links in stud order (`w_jb_12`, `w_jb_23`, `w_jb_34`). The 1-4 numbering is the master's; its physical order along the bar is not recorded.
- N61 a (Dan 2026-11-07): the alternator fuse on bar stud 3 is the INTEGRAL link `w_alt_fuse` "MRBF fuse (Blue Sea 5191)" from `SP-JUMP-3` to `SP-ALT-FUSE`, the block's M8 output stud where `w_alt` lands. The old `ALT-FUSE` device and its harness.design mate to `JUMP-BAR` are gone.
- N55 a (Dan 2026-11-07): links (the jump bar copper, the MRBF fuse block; no bussed-plug bridges since R6) use wire part `INTEGRAL`: no length, no gauge, not bought, out of the BOM, cut list and length checks (like the RADLOK pass-through rows); `build_drawings.is_integral`, `check_wiring.py` I1.
- N56 a (Dan 2026-11-07): this model lives in the master wire list, so every drawing agrees.
- N57 a (Dan 2026-11-07; its bridges replaced by R6, Dan 2026-11-08, "harness.design files (B6)"): the bus plugs (`BUS-5V`, `BUS-5V-2`, `BUS-GNDOUT-A`, `BUS-GNDOUT-B`, `BUS-SW12`) stay real DT06 plugs with their bussed receptacles; since R6 each plug is drawn mated to its receptacle, every used pin carries the same signal name (`check_wiring.py` B1), and there are no pin-to-pin `br_*` rows. Each cap busses every cavity: DT04-12PA-P021 "One 12-Pin Buss", DT04-08PA-P021 "One 8-Pin Buss" (Del City DT bussed receptacle pages; Amphenol AT04-12PA-P021 drawing note 3 "12 pin busbar", rev A2 ref DT04-12PA-P021).
- N62 a (Dan 2026-11-07): the Blue Sea 2104 bar, MRBF block 5191 and fuse 5186 are fixed-quantity lines of `docs/sourcing/harness-parts.csv`; the ring terminals are counted from the master.
- Frozen fuse boxes (Dan 2026-11-07 10:05): the fuse box CAD is largely frozen; relay and fuse slots "removed" during harness changes stay in the model as spares and can be used any time; they are not stale and cleanup sweeps must not flag them (e.g. 100L item 16 K-REV seat, 100P item 16 POWER relay, item 21 heater 87a, `cad/fusebox/rev7/wiring_plan.json` `t_pdb_gnd_*`). Never edit `cad/` to delete them.
- N67 a (Dan 2026-11-07): the frozen LOGIC box parts list (`cad/fusebox/fusebox-parts-logic.csv` line 12) still counts the cluster DEV fuse as 15 A; it stays as is until the fuse box revisit (row 107); the fuse map (`sot/fuse-relay-map.csv`, DEV 5 A) wins (B27).

## Relays (B15)

Moved here from rule B15 on 2026-11-02 (Dan L3 = a); binding as part of B15.

- Link Aux outputs: Aux 1-4 low side only, Aux 5-8 high or low side (XtremeX QSG p.3); their current is `TBD` in
  `sot/channels.csv` (W3 a, 2026-11-04: no G4X document on hand gives it; Link forum 15847, a G4+ thread, says under 2 A low
  side and under 0.5 A high side). Aux 1-10 carry a 1.5 kOhm pull-up to regulated 12 V (forum 17727, Adamw, G4X). So a relay coil is driven low side (B15).
- Coil check (Dan 2026-11-01): whenever a fuse / relay box is touched or reviewed, check every relay coil against its driver; Link Aux outputs have their own flywheel diode, Ign / Inj outputs do not, so a relay on those gets a diode-coil part.
- ON-only relay K-ON (Dan 2026-11-04, N5 a; B17): LOGIC M7 (was K-REV), TE 6-1419137-4 (1 form C, diode). Coil 86 from
  J/B No.1 1H-7 B-O (IGN 7.5 A out, live at ON and ST; 1993 EWD p.62-63), coil 85 to the POWER box NEG bar GND stud (N60 a). Contact:
  BUS1-6 LAM 10 A (Bus 1; Link CAN-Lambda QSG: 10 A fuse through an ignition relay; LAM 7.5 -> 10 A, Dan) -> 30; 87 ->
  the CAN-Lambda only (DRB102 cavity 95; Dan N6: its own relay and its own fuse). The RealDash Pi is off the LOGIC box
  (B17); the cluster stays alone on DEV (Bus 2), 5 A since Dan N52 a 2026-11-07 (was 15 A); BUS2-1 and BUS2-12 are spare. No fuse-box design change.
  Coil check of the LOGIC box with it: K-ETB on Aux 2 (flywheeled), K-EPS-EN on Ign 6 and K-ACC on the A/C amp are diode
  parts, K-HL / K-HR / K-HORN switch-driven, K-ON key-driven with its own diode: all fit. K-DRL (M8, Dan N87 a) and K-POD (M10, Dan N93 a, 2026-11-08) are switch-driven, resistor or no suppression needed: fit; the DRL cut relay RLY-DRL (outside the box, N90 a) is switch-driven too.

## Headlamps, DRL and pop-ups (Dan 2026-11-08)

Binding as part of B10, B15 and B27. Circuit and truth table: `docs/harness/circuit-plan.md` "Headlamps, DRL and pop-ups".

- Source, Dan's stalk (2026-11-08): 0 = pods down, lamps off; 1 = pods stay; 2 = parking lamps, pods stay; 3 = low beams, pods up; pull back = high beams; flash = pods up and high beams while held, back on release. Factory wiring (1993 EWD p.116-117): light switch HEAD grounds R-Y (splice I2: head relay coil, R8 pin 8 UP), pos 1 / TAIL ground P (R8 pin 6, hold); dimmer LOW grounds R-L (lamp pin 1, low), HIGH grounds R-W (lamp pin 2, high), FLASH grounds R-Y and R-W; the high-beam LED, C13 (B) pin 12, sits on R-L.
- N84 a: no relay kit (RENMAII REN012 not used). Harness C feeds the HWSTAR H6054 LED lamps switched +12 V from the LOGIC box relays, the lamp common (pin 3) to ground on the same-side front point (EB LH, EA RH; N83 a); the factory dimmer and light switch only drive relay coils. Fit (Dan 2026-11-08): the lamps are OEM size and fit, on the factory plug; lead ends: the white DRL leads to `SP-DRL`, the yellow turn leads to the F7 / F8 pigtails (below).
- N89 a (Dan 2026-11-08; replaces the per-side layout asked under N84): per-beam relays in their own seats, existing fuses, no spare seat: K-HL (M1, HL 15 A) = low beams of both lamps, coil 85 on R-Y (IE1-2: HEAD or FLASH); K-HR (M2, HR 15 A) = high beams of both lamps, coil 86 from K-HL 87, coil 85 on R-W (IE1-18: HIGH or FLASH). The high beams light only with the head lamps on (R-W is grounded at HIGH even with the lights off), and the low beams stay on with the high beams. Per-side fusing is gone. Per-side changeover relays cannot be wired: the frozen LOGIC box has no 87a terminal cavity in any micro seat (`cad/fusebox/rev7/wiring_plan.json`: every 87a is "spare", a blade slot only; `cad/fusebox/src/check_terminal_holes.py` H1).
- Dash high-beam LED (N82 a recheck): with no lamp on R-L the LED would stay dark, so the high-beam out feeds the R-L line through `R-HB` (220 ohm, 1 W) at IE1-11: lit at HIGH / FLASH only (at LOW the dimmer grounds R-L and K-HR is off).
- N85 a: the DRLs go off when the low or high beams are on. N90 a (Dan 2026-11-08) builds it: one small relay outside the LOGIC box, beside it, `RLY-DRL` (Song Chuan 301-1C-C-R1-U01-12VDC, ISO 280 micro SPDT, in a Delphi Metri-Pack 280 socket 12110539; customconnectorkits.com), coil 86 from the HL fuse (`SP-HL`), coil 85 on R-Y (`SP-HEAD-COIL`, with K-HL), its NC 87a in the DRL feed (K-DRL 87 -> RLY-DRL 30 / 87a -> `SP-DRL`), so the DRLs go off whenever the head lamps are on (HEAD or FLASH). Feed and fuse stay BUS2-1 DRL 7.5 A.
- N91 a (Dan 2026-11-08): the low beams stay on with the high beams (as built under N89 a); `R-HB` stays.
- N87 a: a separate DRL switch raises the pods through 2 diodes at R8: the R-Y lead I2 -> R8 pin 8 is cut near R8 (kept cabin lead, solder, B9); D1 anode at R8 pin 8, cathode to the I2 side; D2 anode at R8 pin 8, cathode to the DRL switch, which grounds it and the K-DRL coil on R8's own ground lead (pin 12 W-B, to ID). So the stalk and the DRL switch each command UP, and the DRL never energises K-HL. DRL feed: LOGIC BUS2-1 DRL 7.5 A (Bus 2, live with K-EFI, so key on) -> K-DRL (spare seat M8, TE 4-1904124-2, on hand) 30 / 86; 87 -> both white DRL leads. Switch (Dan K1 a, 2026-11-08: small round panel rocker, on / off): Arcolectric (Bulgin) `R13112AAAA`, SPST on-off, black, I / O legend, 20.2 mm panel hole, 4.8 x 0.8 mm quick-connect tabs (maker sheet https://docs.rs-online.com/af05/0900766b808a97c8.pdf; colour / legend from RS 314-4995, the maker sheet does not decode the suffix); signal current only, so any SP rating covers it; receptacles TE `280919-2` (20-15 AWG) under heat shrink, crimp tool TBD (TE tool for 280919 not confirmed); spot left of the steering wheel (Dan 2026-11-08). Key on only (Dan N93 a, 2026-11-08; replaces N92 a): D2's cathode goes through the NO contact of the key-on relay `K-POD` (spare seat M10, TE 4-1904124-3, on hand; coil 86 from BUS2-1 DRL 7.5 A, coil 85 on the DRL switch), so with the key off D2 cannot be grounded and the pods follow the stalk alone, as stock; the head lamps and pods still work without the key through the stalk (3 then 1 = pods up, beams off, for maintenance). Key on + DRL switch on = pods up and DRLs lit, the DRLs off while the head lamps are on (N90 a). Diodes: DEUTSCH DT04-2P-RT01 (MUR460) from customconnectorkits.com (Dan 2026-11-08); which cavity is the anode is TBD by the TE drawing.
- Front turn (Dan 2026-11-08): each lamp's yellow lead joins its side's turn feed on the F7 / F8 pin 3 pigtail (G-B LH, G-Y RH; 1993 EWD p.130); the bumper lamps stay.
- N86 (Dan 2026-11-08): both horns share one ground: `SP-HORN-GND` at the horns, one 14 AWG wire to EA (RH fender apron, out of the bumper opening), tagged factory ground (N83 a), 1993 EWD p.185.
- N105 a (Dan 2026-11-08; in the master 2026-11-08): the DRL switch splice `SP-DRL-SW` moves to the glove box (by the LOGIC box), not at the switch.

## CAN wiring (B17)

Binding as part of B17. Dan's design, 2026-11-07 09:23, verbatim:

> "The cluster can, power, and ground should all be in the same shielded cable, so following the same path to the main can trunk. The main can trunk starts at the ECU comms connector C. All power and ground for can nodes joins the can trunk at that same starting location near ECU connector C. The can trunk branches off for each can node, then loops around to bring can H and can L out to the can lambda controller. The can lambda is the far node and gets 120 ohm resistor. The other end is the ECU comms connected, which should have a 120 ohm resistor built in? The cluster, csb3, and the pi each get can L/H and power and ground directly from the can trunk. Each device gets the same 4 core shielded cable for that."

- Shields (Dan 2026-11-07 09:24): "So yes the can shield splices onto the can trunk where it's branch comes off". Each node cable's screen splices onto the trunk screen at that node's branch point on the trunk (`SP-CAN-SH-CLU`, `-CSB`, `-RD`, `-BH`, all at the trunk start by ECU plug C, layout node `CANJ`), not at the device; superseded by P1 (2026-11-09, below): each branch splice sits at its node's tap and the trunk screen drains at ECU plug C pin 1 through `cab_can_ecu_sh` (`w_shd_can_trunk` dropped 2026-11-08, `SP-CAN-SH-BH` gone).
- (Superseded by P1 / T1 a: the drops are 2-core CAN cable.) Branch cable: cluster, CSB3 and RealDash Pi each get one TE Raychem Spec 55 4-core shielded cable `55A1841-20-2/4/5/6-9` (4 x 20 AWG, tinned-copper shield, ETFE; OD 0.173 in / 4.39 mm nominal, 0.202 in / 5.13 mm max, TE SCD 55A1841 rev E): CAN H, CAN L, +12 V, ground. Master cables `CAB-CAN-CLU`, `CAB-CAN-CSB`, `CAB-CAN-RD`. Core colours: CAN H yellow, CAN L green, +12 V red, ground blue (the cable's colour digits 2/4/5/6; the SCD cites MIL-STD-681 and shows 5 green, 6 blue, 9 white jacket; 2 red and 4 yellow are that code's, not shown on the SCD page).
- N49 b (Dan 2026-11-07 09:47): the extra ECU-end terminator `R-TERM-ECU` (master `wc_term1` / `wc_term2`, part `120R 1/4W`) is deleted; the ECU's built-in terminator is the ECU end of the bus. Source: Link forum moderator Adamw, 2022-01-11, "the ECU already has one built-in so you only need one at the far end of the bus" (https://forums.linkecu.com/topic/15390-can-network-wiring-twisted-pairs-adding-a-wideband-controller-obd2-port/); not confirmed in Link's own manuals. `CAN-TERM-END` at the CAN-Lambda stays. Bench check before first start: `BENCH-TEST.md` "CAN bus termination check" (about 60 ohm; about 120 ohm means no built-in terminator and `R-TERM-ECU` comes back).
- N50 b (Dan 2026-11-07 09:47; the fuses stand, the trunk-start joins and cores are superseded by P1 / T1 a): every node keeps its own fused feed (cluster LOGIC DEV, CSB3 LOGIC CSB on Bus 2, Pi the factory CIG & RADIO ACC lead at cowl plug II1 pin 3, CAN-Lambda K-ON). The feed wires and the node grounds come to the trunk start (`CANJ`); from there each node's +12 V and ground ride its own 4-core branch cable with CAN H / CAN L (`SP-CLU-12V` -> `wc_12v_clu`, `SP-CSB-12V` -> `wc_12v_csb`).
- N51 a (Dan 2026-11-07 09:47): CAN-Lambda power stays on its own 14 AWG wires (`w_lam12_cp` and on, DRB102 cavities 95 / 96, unchanged); only CAN H / L go out to it on the existing bulkhead leg.
- N52 a (Dan 2026-11-07 09:47): cluster fuse LOGIC DEV 15 A -> 5 A, so the 20 AWG core is protected (Gauge cases: 20 AWG 8 A cabin). The feed leg `w_dev_clu` stays 16 AWG Tefzel: the fuse-box design has 16 AWG at BUS2-6 (P1) and its contact 1-968851-1 takes 16-14 AWG; since T1 a it runs straight to the cluster (the 20 AWG core and `SP-CLU-12V` are gone).
- N53 a (Dan 2026-11-07 09:47; superseded by T1 a: each node grounds straight to `SP-CABIN-GND`, `SP-CAN-GND` and `w_can_gnd` are gone): each node's ground core joins `SP-CAN-GND` at the trunk start; ONE trunk ground wire `w_can_gnd` runs from there to the cabin ground splice `SP-CABIN-GND` by the POWER box, then on to the NEG bar (B10; N60 a 2026-11-07). Size (B12): it returns DEV 5 A + CSB 5 A + Pi 5 A = 15 A: 16 AWG Tefzel (15 A cabin). The CSB3 ground splice `SP-CSB-GND` (CSB3 cavity 1, power ground) reaches it by the CSB3 branch cable's ground core `w_gnd_csb` (replaces `w_csbg_ac`).
- N54 a (Dan 2026-11-07 09:47; superseded by P1): the CSB3 branch comes off the CAN joins like the cluster and the Pi (layout segment `CANJ`-`CSB3` 320 mm, was `ECU`-`CSB3` 370 mm, so the path ECU to CSB3 stays 370 mm), not straight from the ECU.
- N58 a (Dan 2026-11-07 09:54): the Pi stays on the factory CIG & RADIO ACC feed (II1 pin 3). A 5 A inline fuse `F-PI` (Littelfuse MINI FHM in-line holder `0FHM0003ZXJB`, 16 AWG leads, with an `ATM-5` MINI fuse) sits where the Pi feed joins the trunk start; after it the Pi +12 V rode the 20 AWG red core of its branch cable (`wc_12v_rd`; superseded: fuse spot N107 a, plain wire T1 a). The feed leg II1 pin 3 to the fuse (`w_pi12`) stays 16 AWG Tefzel for the factory 15 A fuse.
- N107 a (Dan 2026-11-08; replaces where N58 a puts the fuse; in the master 2026-11-08): the Pi fuse `F-PI` sits at the radio ACC tap (cowl plug II1 pin 3) with a short lead to the Pi, not at the trunk start; the Pi branch cable's +12 V core is a spare.
- **P1 (Dan 2026-11-09; replaces the "branches all off the trunk start (`CANJ`)" layout of the 2026-11-07 design above; in the master 2026-11-09):** one continuous shielded CAN trunk, ECU plug C (comms port, the ECU's built-in terminator) at one end and the CAN-Lambda (end terminator `CAN-TERM-END`) at the far end; the switch board, centre cluster and RealDash Pi drop off it along the way, in that order (Dan: "The order is up to you"; the taps sit on the existing dash branches, so every order gives the same trunk length, and this one is Dan's sketch). Dan's sketch: ECU comms C ======= CAN-Lambda, with the switch board, cluster and Pi each hanging off the trunk. Built as (drops and node power / ground per T1 a below):
  - Trunk = TE Raychem `55A1821-20-9/5-9` shielded twisted pair the whole way, in four segments: ECU plug C -> switch board tap (`CAB-CAN-ECU`, AB-cabin), switch board tap -> cluster tap (`CAB-CAN-T2`, Dash), cluster tap -> Pi tap (`CAB-CAN-T3`, Dash), Pi tap -> bulkhead cavities 79 / 80 / 81 (`CAB-CANBH-BC`, AB-cabin), then the existing engine run to the CAN-Lambda (`CAB-LAMCAN-BE`). At each tap the trunk segments' CAN H, CAN L and screens join in that tap's splices (`SP-CANH-<node>`, `SP-CANL-<node>`, `SP-CAN-SH-<node>`, layout nodes `TAP_CSB` / `TAP_CLU` / `TAP_PI`, 80 mm before each node on its dash branch).
  - Drops (Dan T1 a, 2026-11-09; replaces the 4-core drops): each node drops off its tap on a 2-core shielded CAN cable only, `55A1821-20-9/5-9` like the trunk (CAN H white, CAN L green + screen), tap -> node 280 mm cut length (80 mm + 2 x 100 mm end allowance), inside the ~300 mm stub limit for 1 Mbit/s (ISO 11898-2 practice). The far end's stubs at the CAN-Lambda splices (CAN-Lambda pins, terminator plug) are 200 mm.
  - Screens: one screen path, drained only at ECU plug C pin 1; each drop's screen splices onto the trunk screen at its tap and floats at its node; the trunk screen floats at the CAN-Lambda. The old chained shield splices and 200 mm jumpers at the trunk start (`w_shd_can_csb`, `w_shd_can_rd`, `w_shd_can_bh`, `SP-CAN-SH-BH`) and the CAN H / L joins `SP-CANH` / `SP-CANL` are gone.
  - Power and ground (Dan T1 a, 2026-11-09; replaces N50 b's and N53 a's cable cores and joins, the fuses stay): each node's +12 V is one plain wire straight from its fused feed (cluster: LOGIC DEV 5 A, `w_dev_clu`, 16 AWG Tefzel for the box contact; switch board: LOGIC CSB 5 A, `w_csb12`, 20 AWG, to its plug cavity 2; Pi: `F-PI` at the radio tap, `w_pi12_out`, N107 a) and its ground one plain 20 AWG black wire straight to the cabin ground splice `SP-CABIN-GND` by the POWER box (battery-negative bus, B10; 5 A fuses, B12 cabin 8 A): `w_gnd_clu`, `w_gnd_rd`, and `w_gnd_csb` from the switch board ground splice `SP-CSB-GND`. Gone: the +12 V joins `SP-CLU-12V` / `SP-CSB-12V`, the CAN node ground join `SP-CAN-GND` and its trunk ground `w_can_gnd` (one direct wire per node is fewer parts than a join plus a trunk wire), and the drop cores `wc_12v_clu` / `wc_12v_csb`. The cabin ground splice now takes 8 legs.
  - Termination: two 120 ohm ends only, the ECU (built in, N49 b; bench check in `BENCH-TEST.md`) and `CAN-TERM-END`; no terminator anywhere in the middle.

## Shields

`check_wiring.py` S1-S3 enforces the drain and floating-screen rules (R207). Device pin, pin name, and whether that device gets a shield: `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`.

**B14 detail.** Same cable and colours on both sides of the firewall (Dan 2026-10-31; row 171; moved here from rule B14 on 2026-11-02, Dan L3 = a). Cable: TE Raychem Spec 55. Shielded: crank, cam, knock, wheel speed, VRC outputs, turbo speed, ETB, APS pedal, the CAN-Lambda run and every CAN pair (one exception: the spur to the CAN-Lambda end terminator plug `CAN-TERM-END` is 2 plain wires, CAN-H and CAN-L, no shield, Dan 2026-11-03); injectors, coils, the gearbox VSS (plain wires, Dan 2026-11-01) and flex fuel (Dan N31 b, 2026-11-06) get none. Across the firewall a circuit keeps its colour and gauge on both halves; only the wire type changes (TXL in the cabin, Tefzel in the bay; Dan N30, 2026-11-06). A drain is the shielded cable's own drain wire, bought with the cable, so it has no wire part number (R32 stands; Dan N71, 2026-11-07); it is found by its master row, never its colour; no connector shell, and no sleeve just to end one screen. A cabin device that joins a loom part-way splices its drain where its signal wires join; a bulkhead device keeps its own drain and bulkhead pin up to the splice at the ECU plug. Each VRC box has one 5-pin CNLINKO LP-16 IN plug (pin 3 = both screens) and one OUT plug (pin 5 = screen, G2 a); its board is isolated from the case.

**No connector shells (R33).** Every drain lands on a regular pin; no shell, backshell or shielding plate ever carries a screen (the VRC LP-16 plugs included).

**Shared drain pin: one splice (R29, R30, R32).** Every shielded cable is drawn as if it had a drain wire, straight to its pin. Two or more screens on one pin share ONE `GENERIC SOLDER SPLICE` (no covering), with one drain wire (the cable's own, no wire part number, R32 / N71) to the pin. The T-splice is how it is built, not drawn (R30). Every CAN node branch shield goes into its own named branch splice on the trunk drain (`SP-CAN-SH-*`, R207; the one exception to "one splice"). **CAN branch splices (Dan 2026-10-25):** where each CAN node branches off the trunk for power and CAN signal, that node's shield splices onto the main trunk shield at that same point, one splice per branch point, never all in one lump. Each branch splice is a solder sleeve that takes a drain lead (Raychem / TE type); part number TBD (row 166).

| Pin | Screens into the one splice | Splice |
|---|---|---|
| ECU-A A7 | crank, cam, turbo, ETB sensor, pedal 1, pedal 2, front WS spur (one 4-core cable) | the shield drain bus plug `BUS-SHIELD-A` by ECU plug A (DT06-08SA + W8S, mated to the bussed receptacle DT04-08PA-P021, sockets 0462-201-16141; Dan N104 a, 2026-11-08): each screen on its own pin, one drain wire `w_drain_ecu_a` from pin 1 to A7 |
| ECU-B B17 | knock, ETB motor, rear WS spur (its screen straight to the splice, Dan 2026-11-08) | `SP-SHIELD-B`, 6 in (152 mm) behind `ECU-B` (N83 = A) |
| ECU-COMMS C1 (R207) | the ECU CAN cable's own screen `cab_can_ecu_sh` (ECU plug C pin 1 to the trunk start, Dan 2026-11-08); CSB3, cluster, RealDash and bulkhead / Lambda branch screens splice onto it | one named splice per branch, `SP-CAN-SH-CLU` / `-CSB` / `-RD` / `-BH`, at that branch point on the trunk, all at the trunk start by ECU plug C (Dan 2026-11-07, "CAN wiring (B17)") |
| VRC front IN pin 3 | FL and FR sensor cables | `sp_vrc_f_in_sh` at `lp16_vrc_f_in` |
| VRC rear IN pin 3 | RL and RR sensor cables | `sp_vrc_r_in_sh` at `lp16_vrc_r_in` |

Every bulkhead drain has its own cavity. Both sensor screens of a VRC share its input plug pin 3.

**Vocabulary.** Screen means shield. A drain is the shielded cable's own drain wire, bought with the cable, that connects the shield to the pin (no wire part number, R32 / N71). Shields exist only on cables; a device or sensor gets one shield flag (never per pin or per wire).

**Absolute rules (R27, R28, R33).** A shield floats at the sensor, runs unbroken as a multi-conductor Raychem cable, and terminates at an ECU shield pin (A7 / B17); the only device-end landing is the wheel-speed sensor shields on VRC IN pin 3 (R31). A shield that crosses the firewall does so on its own bulkhead pin, wired on both halves, never on a shell. Do not invent break points. The ABS wheel-speed sensors have two wires: no third conductor, no shield connection at the sensor.

**Bulkhead pass-through.** Only a signal that already passes through both firewall bulkhead halves must carry its shield through both halves on matching pins. That shield floats at the sensor, must not stop on either half, and terminates at the ECU shield pin. Once the bulkhead connectors are installed they are straight-through, so a shield is not required to float at the bulkhead. Loom A screens land on A7 through the shield drain bus plug `BUS-SHIELD-A`, loom B screens on B17 through `SP-SHIELD-B`, the CAN screens on C1 through the trunk drain. No screen crosses between loom A and loom B (R207, `check_wiring.py` S3). Nothing but a drain lands on A7, B17 or C1.

**VR conditioner boxes (R31, R34).** The VRC device gets one shield flag. The sensor cables' screens and the output cable's screen are one continuous path: sensor (floats) -> IN plug pin 3 (one splice, R29) -> wire inside the box -> OUT plug pin 5 -> the AB-cabin spur cable screen -> the shield drain bus plug (front, `BUS-SHIELD-A`) / shield splice (rear, `SP-SHIELD-B`) -> **A7** (front) / **B17** (rear). No inline pair (Dan J1 a, 2026-11-08: simpler, fewer failure points): the AB-cabin spur cable ends on the VRC OUT mating plug (CNLINKO LP-16-J05PE-02-001, solder cup, 22-20 AWG), and that plug is the disconnect between the ECU harness and the wheel speed harness, which is only the sensor cables into the VRC IN plug. The plugs are `VRC-F-IN` / `VRC-F-OUT` and `VRC-R-IN` / `VRC-R-OUT`: input 1 left +, 2 left -, 3 both screens, 4 right +, 5 right -; output 1 +5 V, 2 Gnd Out, 3 left out, 4 right out, 5 screen (the VRC enclosure CAD BOM `vr-conditioner-bom.csv`, Dan G2 a 2026-11-08; replaces 3 screen / 4 left / 5 right, Dan 2026-10-19). `check_wiring.py` treats IN 3 to OUT 5 as one path through the box.

The VRC and its panel sockets are not drawn. Each VRC harness is two separate pieces ending in two non-shielded 5-pin CNLINKO LP-16 plugs (`LP-16-J05PE-02-001`, S8 / R34 / S16). Nothing bonds to the case and no shell carries the screen (R33): the box is not part of the shield path, the PCB sits in a printed holder (S26) and grounds through the output cable only, and the box mounts on nylon hardware.

**ABS routing.** Front (FL, FR) runs through the fenders with loom C. Rear (RL, RR) runs with the fuel pump and level sender. Neither pair gets its own firewall crossing; the wheel-speed loom uses no bulkhead connector — it crosses on a grommet so each screen stays unbroken.

**Shield path (Dan 2026-11-08, standing, no exceptions).** A shield is part of its shielded cable and follows the exact path of the cable's other wires all the way to the destination connector (an ECU A device to `ECU-A`, an ECU B device to `ECU-B`); only there does it split off and splice onto that ECU shield pin's splice. Same-size shielded wires of one device ride in ONE multi-core shielded cable with the right core count, unless no such cable exists.

**2026-11-08 shield fixes (Dan; in the master 2026-11-08, the table above shows them):**
- N104 a: the A7 shield splice is a bussed DEUTSCH plug by ECU plug A (`BUS-SHIELD-A`).
- Pedal: its screens go straight to `BUS-SHIELD-A` (drop `w_shd_a_aps` and `SP-SHIELD-A-APS`); the pedal stays 2 cables.
- Front wheel speed spur: ONE 4-core `55A1841-20-2/4/5/6-9`, screen to `BUS-SHIELD-A` (drop `w_shd_a_wsf` and `SP-SHIELD-A-WSF`).
- Rear wheel speed screen to `SP-SHIELD-B` (drop `w_shd_b_wsr` and `SP-SHIELD-B-WSR`).
- The ECU CAN cable screen `cab_can_ecu_sh` ends on ECU plug C pin 1 (drop `w_shd_can_trunk`).
- Wheel speed sensor screens float at the sensors.

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
- Every connector, splice, bus, relay and box has a plain name, unique across the project (Dan 2026-10-31; row 172). No codes in anything Dan reads (Dan C1 b, 2026-11-08: he never uses them): wire lists, pin chart, DRB102 map, harness.design files, editors and chat show the plain name only. The code (`K-FP`, `SP-CABIN-GND`, ...) stays in the master and the scripts as the matching key. Exceptions (Dan 2026-11-08): fuse box and relay codes stay (fuse and relay seats, studs, bus pins, and the relay names themselves, e.g. "LOGIC box seat M8", "BUS2-1", "K-FAN"), shown after the plain name, since those are what he builds the boxes by. Also kept (Dan E1 a, E2 a, 2026-11-08): factory plug IDs from the 1993 EWD (e.g. "Cowl plug IE1 (LH kick)", "A/C amp A15"), so he can look them up in the manual, and the short names CSB3, VRC, ETB and IGT.
- Boards in enclosures (Dan 2026-11-08, standing): the switch board (CSB3) and the VR conditioners are boards inside their CAD enclosures; their board pins are internal. Harness ends land on the enclosure connector pins assigned in the CAD model (CSB3: TE HD34-24-33PE receptacle in the lid; VRC: two CNLINKO LP-16-C05SX-02-101 sockets, IN / OUT), using Dan's on-hand mating connector. G1 a (Dan 2026-11-08): the CSB3 board-signal -> HD34-24-33PE cavity map is `docs/enclosures/csb3-hd34-pinmap.csv` (Dan pre-approved 2026-11-08, manual v2.1 page 4). The master carries this map (PR #582). Unused cavities (6-9, 11-13, 18-19, 21-24, 26) get empty sockets with no wire, as the map says, ready for future wires; Dan accepts that those holes are not sealed (Dan L1 b, 2026-11-08). Cavities 27-33 get sealing plugs. G2 a: the VRC pins follow the CAD BOM (`vr-conditioner-bom.csv`; "VR conditioner boxes (R31, R34)" below). G3 a: the mating parts are chosen whether or not a record shows them on hand: CSB3 plug HD36-24-33SE, size 20 sockets 0462-201-2031 (crimp tool DEUTSCH HDT-48-00), size 20 sealing plugs 0413-204-2005; VRC plugs CNLINKO LP-16-J05PE-02-001 x4 (solder cups, 22-20 AWG, no crimp tool). None is in `te-on-hand-bom.csv` (2026-11-08 check); the CAD BOMs list them as buy.
- Where the row 172 name map (`docs/harness/PLAN-2026-10-31-audit.md`) and the master disagree, the master's current name wins; a new splice is named by the map's catch-all rule, "<what> splice: <what it joins>" (Dan N75 b, 2026-11-07).

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

**Hubs (B8: several harnesses land on them, no owner):** POWER box (B1) and its bar and fuse studs (one ring terminal per wire, `T-PWR-*`), LOGIC box (B2),
SW12 bus plug, every box relay (K-EFI, K-FAN, K-FAN2, K-HL, K-HR, K-HORN, K-ETB, K-ACC, K-EPS-EN, K-EPS, K-FP, the ON-only relay K-ON, the DRL relay K-DRL, the pop-up key-on relay K-POD), trunk relay
block (B3), kill switch, ground points ID / IG / EA / EB and the engine block stud, and the factory taps on J/B No.1, IE1,
IG2, R/B No.2 and R/B No.4 (R/B No.3 and the fog switch F12 are no longer hubs: the fog circuit is removed, Dan 2026-11-02). Bussed plugs (`BUS-5V`, `BUS-5V-2`, `BUS-GNDOUT-A`, `BUS-GNDOUT-B`; each mated to its bussed receptacle, R6)
are splices (B8 editor devices) and sit in AB-cabin.

| Harness (target) | Devices it owns |
|---|---|
| AB-cabin | ECU plugs A, B and C (`ECU-A`, `ECU-B`, `ECU-C`; C moved in from Dash, Dan 2026-11-04 V2 a, with the ECU CAN cable to the switch board tap, P1); bulkhead, cabin half (`DRB102-CABIN`); the ECU splice point; accelerator pedal (`APS-PEDAL`); IG2 wake diode (`D-IG2-WAKE`); cam pull-up, fuel-level pull-up and lock-sensor resistors (`R-CAM-PULLUP`, `R-FUELLVL`, `R-LOCK`); A/C amp taps (`A15`, `A32`); ambient air sensor (`A1`, front, its two wires ride harness C to a "To front" hand-off); the wheel-speed spurs to the VRC OUT mating plugs (`VRC-F-OUT`, `VRC-R-OUT` plug halves; no inline pair, Dan J1 a 2026-11-08); the fuel level sender (`FUEL-LEVEL`): the sill run's fuel level pair lands straight on its plug, no inline pair (Dan N1 a, 2026-11-08: simpler, fewer failure points, same reasoning as J1 a); the cabin-to-trunk sill run (B9: fuel pump relay coil wire `w_fp85`, fuel level pair, kill-switch IG leg; the fuel pump relay coil+ feed `w_k_fp_86_cp` (RearFuel) rides it; the AntiTheft trunk pin lead is gone, Dan N41 a) |
| AB-engine | Bulkhead, engine half (`DRB102-ENGINE`); injectors 1-4, coils 1-4, throttle body (`ETB`), boost solenoid, crank, cam, knock, MAP, IAT, charge IAT, coolant temp (`ECT`), coolant / oil / fuel pressure, oil temp, flex fuel, turbo speed, gearbox speed (`VSS`), reverse switch (`REV-SW`); CAN-Lambda and the far-end CAN terminator plug (`CAN-LAMBDA`, `CAN-TERM-END`; Dan 2026-11-03); MR-S pump plugs B and C (`MRS-B`, `MRS-C`), spare cavities included (B7 = a); starter solenoid S plug (`STARTER-TRIGGER`; DRB102 cavity 3, B20 a; on the turbo-speed branch N19, Y7 b) |
| CabinPower | Only hubs (the boxes and relays above) plus the cabin feed wires between them and the factory taps: dome feed (`w_pmu_dome`, moves in from EngineRoom-C), hazard feed (`w_haz_cp`), R/B No.2 W-L feed (`w_rb2_wl`) dropped (Dan B17 b, phase 2); fog: no device (the cut-and-cap leads `FOG-CAP-1`, `-4`, `-6` are gone; the fog wires are removal rows `w_fog_*`, Dan 2026-11-02); the headlamp / DRL cabin parts (Dan 2026-11-08): splices `SP-HL-ON`, `SP-HR-HI`, the dash high-beam LED resistor `R-HB`, the DRL cut relay `RLY-DRL` beside the LOGIC box (N90 a), the DRL switch `DRL-SW` (left of the steering wheel, Dan 2026-11-08; Arcolectric R13112AAAA, Dan K1 a) and `SP-DRL-SW`, the pop-up diodes `D-R8-1` / `D-R8-2` and `SP-R8-UP` at R8 |
| HeavyDC | Trunk battery posts (`BATT-POS`, `T-TRUNK-NEG`); RADLOK pair, both sides (`RADLOK-POS-CAB`, `-POS-ENG`, `-NEG-CAB`, `-NEG-ENG`); starter B+ stud, one lug (`T-STARTER-B`); alternator B+ stud (`T-ALT-B`); engine block stud lug 1 (`T-ENG-BLOCK`); jump bus bar (stud splices `SP-JUMP-1` .. `-4`) and jump post (`JUMP-POST`), side by side at the OEM battery spot (Dan N11 a 2026-11-05); the alternator fuse block on bar stud 3 (INTEGRAL link `w_alt_fuse` to `SP-ALT-FUSE`, Dan N61 a 2026-11-07); kill switch and trunk relay block (hubs). Map: Route 1, with Route 16 devices H1, H2, H4, 18 moved there (B6 = b; done 2026-11-04: marked `moved_to` in the Route 16 route data, HeavyDC on its own Route 1 tree; line 9 itself stays in Route 16 for AB-engine lines 3 / 4 / 6, the starter S branch and harness C), shown greyed in the AB-engine editor |
| EngineRoom-C | Headlamps (`H1`, `H2`); pop-up motors (`R2`, `R3`); front turn / clearance and side marker lamps (`F5`-`F8`); wiper motor (`F9`); washer pump (`W1`); horns (`HORN-LH`, `HORN-RH`); radiator and condenser fans with their grounds (`FAN-RAD`, `FAN-COND`, `-GND`); MR-S pump plug A (`MRS-A`); A/C compressor clutch (`A4`); A/C pressure switch (`A5`, both its wires; was also AB-cabin); alternator plug (`ALT-PLUG`); ground studs EA, EB and the EB strap lug (`GND-EA`, `GND-EB`, `GND-EB-2`); engine block stud lug 2 (`T-ENG-BLOCK-2`; lug 3 dropped: the EHPS pump ground `w_eps_gnd` lands on EA, Dan L4 a 2026-11-02); DRL split `SP-DRL` and horn ground join `SP-HORN-GND` (Dan 2026-11-08) |
| Dash (was `CAN` + `CSB3` + `ClusterLED`) | the CAN trunk segments between the switch board, cluster and Pi taps, the taps and their 2-core drops, each node's plain +12 V and ground wire, and the Pi inline fuse `F-PI` ("CAN wiring (B17)" P1 / T1 a; ECU plug C and the trunk ends are AB-cabin's, Dan 2026-11-04 V2 a; the ECU's built-in terminator is the ECU end, Dan N49 b 2026-11-07); centre cluster and RealDash Pi CAN, power, ground and headlight-sense ends (`T-CLUSTER-*`, `T-REALDASH-*`); CSB3 plug (`CSB3`); 8-channel opto board (`OPTO-8`, was also AB-cabin); cruise ladder resistor (`R-CRUISE`, was also AB-cabin); cruise switch, cruise clutch switch, stop switch and dimmer taps (`C16` = combination switch plug C16 (B), cruise switch pins 5 / 15 / 17, #535; `C17`, `S9`, `R10`); warning LEDs turn L / R, high beam, charge, park brake, oil (`D-TL`, `D-TR`, `D-HB`, `D-CHG`, `D-PK`, `D-OIL`, was CSB3 + ClusterLED); cluster plug taps (`C13`, `C14`) |
| AntiTheft | Alarm-ready tap points, Dan 2026-11-06 (no alarm picked: no alarm module, siren, shock sensor, status LED, valet switch or hood pin switch drawn): labelled nodes at the alarm spot, constant +12 V `AL-12V` (LOGIC ALM 5 A) and `AL-12V-SHK` (LOGIC ALMS 2 A), ignition `AL-IGN` (LOGIC ALMIG 2 A), door trigger `AL-DOOR` (from the factory tap `T-AT-DOOR`, J/B No.1 1B-11 R-W; trunk pin dropped, Dan N41 a), hood trigger `AL-HOOD`, immobiliser `AL-IMMOB` (ECU-B pin 27, B18 a), ground `AL-GND`, siren `AL-SIREN`, hazard flash `AL-HAZ` (reserved, no wire, Dan N47); pull-wire bay ends `AL-SIREN-BAY`, `AL-SIREN-GND-BAY` (LH pass-through, B19) and `AL-HOOD-BAY` (RH front); the ground ring terminal at the alarm (`T-AT-GND`; Dan N43 b) |
| RearFuel | Fuel pump (`FUEL-PUMP`); the pump feed runs straight from the fuel pump relay to the pump (Dan 2026-11-08); the fuel level sender moved to AB-cabin with its wires (Dan N1 a, 2026-11-08); pump ground ring on factory ground point BL, back panel centre (`GND-BL`, Dan N97 a); the fuel pump relay coil+ feed `w_k_fp_86_cp` (SW12 bus plug by the LOGIC box to K-FP coil 86 in the trunk relay block), riding the AB-cabin sill run (Dan 2026-11-04: the boxes are far apart, so the wire belongs to the harness that holds the device it serves) |
| WheelSpeed-Front / -Rear | Wheel speed sensors (`WSS-FL`, `WSS-FR` / `WSS-RL`, `WSS-RR`); VR conditioner boxes and their IN plugs (`VRC-F-IN` / `VRC-R-IN`); the OUT plug halves are AB-cabin's (Dan J1 a, 2026-11-08) |

**Changes from the old master (applied in phase 2, 2026-11-02):**

| Device or wire | Today | Target | Why |
|---|---|---|---|
| MR-S plugs B / C spare cavities (9 rows) | EngineRoom-C | AB-engine | B7 = a: one owner per plug |
| Alarm module immobiliser lead (`w_at_immob2`, ECU-B pin 27 to alarm pin 9; node `AL-IMMOB` since 2026-11-06) | AB-cabin | AntiTheft, riding AB-cabin (Dan B18 a) | it joins two non-hub plugs of two harnesses, so one plug gets a foreign wire either way |
| Opto board input 2 (`w_sw7_c`) and cruise ladder 5 V (`w_cru_5v`, from the switch board +5 V since N108 a, 2026-11-08) | AB-cabin | Dash | they land on the opto board / cruise resistor; the other end is a splice or a bussed plug |
| Oil warning LED (`w_oil_a` / `w_oil_k`) | ClusterLED + CSB3 | Dash | B8 = a merges both owners |
| A/C pressure switch signal (`w_ac_psw_in`, A5 pin 4) | AB-cabin | EngineRoom-C | A5 is harness C's plug in the bay; it ends at the cabin splice `SP-AC-PSW` |
| Dome feed (`w_pmu_dome`) | EngineRoom-C | CabinPower | both ends in the cabin (glove box to J/B No.1 1H-2), fault C4 |
| R/B No.2 W-L feed (`w_rb2_wl`) | EngineRoom-C | dropped, with `w_rb2_feed` | fault C1 / C4; Dan B17 b: AM1 feeds R/B No.2 through I2, as stock |
| Hazard feed (`w_haz_cp`) `passes_through` | EngineRoom-C | blank | glove box to IE1 at the LH kick, never in harness C |
| Horn relay output (`w_pmu_horn_cp`, K-HORN 87 to `SP-HORN` at the front) | CabinPower, `passes_through` EngineRoom-C | EngineRoom-C | it runs glove box to the horns inside harness C |
| Fuel pump relay coil wires (`w_fp85`, `w_k_fp_86_cp`) | AB-cabin / CabinPower, `passes_through` HeavyDC | `w_fp85` AB-cabin (sill run); `w_k_fp_86_cp` RearFuel, riding the AB-cabin sill run (Dan 2026-11-04) | B9 = a; signal wire is not taped to the 1/0 cable |
| Fuel level pair (`w_fl_sig`, `w45`) | AB-cabin, no carrier named | AB-cabin (sill run) | B9 = a |
| Kill switch IG legs (`w_ig_ks_in` IG2-15 to kill switch; `w_ig_ks_out` kill switch to alternator plug) | HeavyDC `passes_through` EngineRoom-C; EngineRoom-C `passes_through` HeavyDC | `w_ig_ks_in` AB-cabin (sill run); `w_ig_ks_out` EngineRoom-C `passes_through` AB-cabin | B9 = a; the alternator plug is harness C's |
| Trunk pin lead (`w_at_trunk_tie`) | AntiTheft, no carrier | AntiTheft `passes_through` AB-cabin | B9 = a; the lead was dropped 2026-11-06 (trunk pin dropped, Dan N41 a) |
| Siren and hood pin leads (`w_at_siren`, `w_at_gnd_a2`, `w_at_hood_tie`) | AntiTheft, no carrier | AntiTheft `passes_through` EngineRoom-C | they cross with harness C; the siren uses the driver-side (LH) fender / kick pass-through (Dan B19); since Z13 b (Dan 2026-11-09) the hood pin lead shares that LH pass-through and runs on down the LH side to the front centre |
| Starter S (`w_strl_c` / `w_strl_e`) | AB-cabin / AB-engine on Route 16 (N19 since Y7 b, 2026-11-09; was line 9) | `w_strl_e` AB-engine, DRB102 cavity 3 (Dan B20 a), on the turbo-speed branch N19 (Dan Y7 b, 2026-11-09); `w_strl_c` stays AB-cabin (R/B No.4 to the cabin half of DRB102: one plug, one harness; Dan to confirm) | line 9 moves to HeavyDC's map (B6 = b) |
| HeavyDC devices H1, H2, H4, 18 and line 9 | Route 16 | Route 1 (HeavyDC map), greyed in the AB-engine editor | B6 = b; also removes the row 179 loops |

## Placement and lengths (B8)

Moved here from rule B8 on 2026-11-02 (phase 3, O6); binding as part of B8.

- Lengths live in the layout tree only (Dan N69 a, 2026-11-07): `est_length_mm` in the master is written by the tool from the tree, never by hand, for every harness Dan has placed; `build_drawings.py --check` fails when a placed harness's master length differs from its tree length. A harness not placed yet keeps its estimate until placed. The placed list is `PLACED` in `build_drawings.py` (a harness joins at its lengths step, below); `--lengths` prints the before -> after list, `--write-lengths` writes it. Why: one length source, no drift (`w204_e` / `w10` drifted 1 mm after #522).
- Placement editor rule (Dan 2026-11-01; the "Dan draws its branch lines" part is superseded by N120 and Z10 b below: Dan only places devices): every harness gets a placement-editor pass (Dan places each device and draws its branch lines on the map) before its layout is built or it goes into harness.design; the saved placement becomes that harness's route and replaces its old route files and images in the repo (deleted, git history is the archive).
- Old route pages (Dan N72 b, 2026-11-07): a harness's old page in `docs/harness/routes/` is deleted at that harness's harness.design step, once every still-open fact on it is in its SoT: Route 1 (HeavyDC, built) now, Routes 8 / 12 / 13 at Dash's step, Route 14 at AntiTheft's; Routes 9 / 10 / 11 deleted 2026-11-09 (Dan X1 a: their routes are agent-drawn in the layout tree, N120). Its before / after screenshots in `_research/snapshots/2026-10-15-wp4-route-labels/` (Dan's PC only, not in git) are deleted with it (Dan N79 a, 2026-11-07).
- Route 1 page deleted (Dan N77 b, 2026-11-07): `ROUTE-1-HEAVYDC.html` is gone (git history keeps it). Its one fact with no other home, the rev 3 flag (2026-10-04) that the alternator sits right below the firewall plug with backshell / wire-exit clearance and heat to confirm, is closed by Dan's Route 1 approval (2026-10-15); its other facts already live elsewhere. HeavyDC's route is the layout tree (`ST185-harness.layout.json`); "Route 1 point N" in master ends and layout labels are names in that tree.
- No tape-measure pass (Dan N73 a, 2026-11-07): a placed harness's lengths are its tree lengths (N69 a); every other harness gets its lengths at its own lengths step (OPEN-ITEMS row 183).
- Top views: front RIGHT, driver side up. No doubling back, overlap, hidden or empty leg; parallel runs spaced.
- Dan's saves are his (Dan 2026-11-02): no agent overwrites a saved placement, editor save or route without showing Dan the change and getting his OK first; the old save is kept as a backup either way.
- Editor devices (Dan 2026-11-02): one number per fuse / relay box (its relays in its note) and one for the ECU; bussed plugs are splices (no number; where they sit: "Splice and bussed-plug spots" below); a device outside the map's area is a hand-off point where its wires leave the bundle ("To trunk", "To front"), its far length from the other harness's map.
- Device spots (Dan 2026-10-28): the `devices` and `runs` in a route file's route data (Route 16 engine bay, Route 17 front) are the one definition of where each device sits and which line or branch it hangs on; a device has one spot in one file (a moved one is marked REMOVED in the other).
- Lengths from a route map: map length x 5.3 mm per EWD point (the 96 mm cylinder spacing) + 300 mm drop for a low-mounted part (`low: true` in the route data), an estimate until that harness's lengths step (N73 a).
- End allowance (Dan 2026-11-03, N3 = a): every tree length adds 100 mm at each wire end (2 x 100 mm per wire; `end_allowance_mm` in the layout file) for termination and service loop.
- AB-cabin (Dan 2026-11-02, A2-A4 = a): placed on the body manual under-body plan (DI-7), front right, driver up, in real mm (8.49 mm per PDF point from the 2525 mm wheelbase), plus an optional drop in mm per device; EWD p.44 (faded) is a look-only tab, since a 3-D view gives no lengths.
- The ECU engine harness tree and its master lengths are built from Route 16, harness C's from Route 17 (`route_trees` in the layout file), HeavyDC's from its own Route 1 segments (a Route 16 device marked `moved_to` is skipped, B6 b); a splice sits where its legs part, unless the layout `place` pins it (the AB-engine bulkhead splices sit at the trunk junction below the bulkhead, as Dan approved, #499).
- Master lengths step (Dan L2 = a, 2026-11-02): a harness's master lengths are written from the layout tree at phase 4's lengths step, one harness at a time, with a before -> after list for Dan (OPEN-ITEMS row 183).
- A connector part-way along a line or run breaks out at least 6 in (152 mm) off it; the last connector at the end of a line or run may end it (Dan 2026-10-29).
- The engine bulkhead sits 16 in (406 mm) from where the trunk meets the firewall (`root_drop_mm`; Dan 2026-11-02 (J1); was 8 in / 203 mm, Dan 2026-10-29). The 6 in breakout rule above is unchanged.
- Splice and bussed-plug spots (Dan 2026-11-08, standing; replaces "anywhere between ECU and bulkhead", 2026-11-02): a splice sits near the ECU connector, the bulkhead, or the device / branch it serves, nowhere else; bussed plugs sit close to the ECU connector or close to the bulkhead, never mid-run where it can be helped; the ECU power, ground and shield bussed plugs sit as close to the ECU plugs as possible (fuse-box power / ground bussed plugs are exempt); ignition coils, CAN nodes and injectors are exceptions.
- Own parts only (Dan N112 a, 2026-11-08, standing): a placement editor shows only that harness's own parts; moves of other harnesses' parts in an editor save (the ECU, IG2 and A15 in the CabinPower save) are ignored.
- Shared trunk (Dan 2026-11-08, standing): wires bound for the same place (e.g. everything to the trunk) share the same trunk run, never split onto separate paths.
- **Editors refine, agents route (Dan N120, 2026-11-08, standing; overrides "Dan places, saves" as the way routes are made):** the agent draws every harness route itself, in the most efficient, optimal, logical, cleanest straight-line way, and seeds each placement editor with the devices already roughly in the right spots. The editor only refines device placement: Dan nudges where devices sit, he does not trace routes. An editor save never moves a device to another harness, never makes dramatic length or placement changes, and never adds complexity (e.g. running a wire through more than one fuse box for no reason). If a save would do any of these, the agent flags it to Dan instead of applying it.
- Y7 b (Dan 2026-11-09): starter solenoid (STARTER-TRIGGER) hangs off the turbo-speed branch N19, a little toward the firewall (Route 16 spot [335.8, 239], approximate; formboard x about 118); FSM Component_Location p.2, RM305U1 p.2; w_strl_e 1948 -> 1853 mm. Since the engine-bay redraw (2026-11-09, below) branch N19 is gone: the starter S end keeps Dan's spot and breaks straight out of line 2 (w_strl_e 1906 mm).
- Engine-bay redraw (Dan Z10 b, 2026-11-09; device spots unchanged on Route 16, Dan's 2026-11-01 spots restored on Route 17): AB-engine is 5 lines with no device branches (was 9 main lines + 19 branches): one straight trunk from the bulkhead to the throttle body, every head device a straight breakout; line 2 keeps the outboard path past the old J/B No.2 spot (turbo heat clearance), line 6 is the belt-end drop, line 4 the passenger front run, line 5 the fuel-pressure spur. EngineRoom-C is 7 lines (was 22 lines and stubs): one run from the RH fender exit along the radiator support to ground stud EB with straight breakouts, the EA ground leg with the MR-S plug A stub, the A/C pressure switch and alternator plug on square stubs off engine line 6, a straight wiper run from the LH pass-through, the block strap as one straight line; the pass-through start points are Dan's 2026-11-01 points. Feeding the LH corner lamps from the LH pass-through was tried and dropped: under 1 m saved, four splices moved, front harness split. Totals: AB-engine 114,139 -> 107,374 mm, EngineRoom-C 101,510 -> 97,828 mm; 141 lengths written (85 + 54 + the two AB-cabin ambient sensor wires 3290 -> 3185).
- Simpler is better (Dan 2026-11-08, standing): pick the simplest route and layout that works; fewer nodes, fewer branches, no detours.
- **Devices are Dan's, routes are the agent's (Dan Z10 b and his 21:02 message, 2026-11-09, standing, every harness):** Dan places components roughly; device spots are his, and a redraw never moves one. The agent draws every route: tidy, straight lines, as few branches as possible, shortest possible, minimal double-backs; beyond that the route layout is the agent's. Device spots used: the latest spot Dan placed by hand in an editor, else the seed spot he approved. Each redraw shows Dan a before -> after picture and length list in chat (L2 a stays as a report); since his 21:21 message (finish every harness without stopping; the agent checks each harness.design file by hand against the wire list) the lengths are written without waiting, and Dan refines device spots afterwards in the phone editor. Replaces "Route drawings stay as Dan marked them" (OPEN-ITEMS, surgical rewire) and "avoid redraws".
- Z13 b (Dan 2026-11-09), AntiTheft redraw: the alarm spot and the alarm ground ring sit on Dan's 2026-11-08 editor save; the alarm branch leaves the dash run 129 mm past the dash branch (`BP_AL`) and runs 223 mm straight back to the alarm spot; the ground ring is a 139 mm stub (`AT_GND`); the siren leads run 130 mm forward from the LH pass-through to the LH firewall corner (`BP_LFW`), then 650 mm along the firewall; the hood pin lead end is at the front centre (Dan's save) and the lead shares the LH pass-through with the siren leads (b: one hole through the firewall, about 240 mm longer than the RH side), 1052 mm forward to the LH front corner and 670 mm across. Lengths: `w_at_gnd_a1` 200 -> 339, `w_at_siren` 2484 -> 2244, `w_at_gnd_a2` 2484 -> 2383, `w_at_immob2` 380 -> 582, `w_at_door_tie` 1220 -> 1164, `w_at_hood_tie` 2260 -> 3316, and the three CabinPower alarm feeds 1012 -> 1214.
- Y8 a (Dan 2026-11-09): the "Route 16 Placement Editor" (https://claude.ai/artifact/CZpVoJkJeGmt79GpnvaBFQ) is AB-engine's editor; its saved db doc is gone, the repo's Route 16 route-data (Dan's 2026-10-28 placement, #413, plus Y7 b) is the record.
- Device spots for the cabin redraw (Dan 2026-11-09 23:49). Y9 b: the ECU sits on Dan's hand-placed spot, the OEM ECU location (about 135 mm toward the driver and further back than the dash-centre seed). Q2: the LH pass-through is behind the kick panel, under the dash; the wires go up through the quarter panel into the engine bay, as the FSM shows (look the path up in the manual before drawing it; one hole). R2: the trunk battery relay block is just to the right of the battery, passenger side rear, to the right of the spare tire well and about 8 in (203 mm) forward of the trunk's back wall. V3 a: no new engine-bay editor; Dan marks up the pictures and the agent redraws. Engine-bay grouping rule (Dan 23:39 / 23:41): on AB-engine the injectors share one branch, the coils share one branch, the bulkhead connector sits on a short stub of its own, and every other sensor sits on a shared, named branch close to Dan's original grouping; no sensor makes its own breakout from the main trunk (the 5-line version of #618 is replaced; drawing waiting on Dan, OPEN-ITEMS Needs Dan W4).
- W4 c (Dan 2026-11-10 00:08), engine bay harness only: Dan may move parts that are already in the AB-engine harness (no part is removed), then draws the overall routes himself in the AB-engine editor. He does not draw each sensor's spur or branch: the agent gives every sensor its own spur in harness.design, and a sensor is never wired 0 mm from the trunk or a branch. The other harnesses keep the standing rule (devices are Dan's, routes are the agent's). The `956c1c1` named-branch draft is only the editor's starting picture.
- AB-engine routes from Dan's W4 c save (2026-11-10 12:09Z, `layouts/route16`): Route 16 = his part spots and his overall lines, joined into the trunk L1 (bulkhead to the throttle body), the bulkhead stub, the belt-end drop L6 (with his CAN-Lambda leg) and its crank branch N15, the passenger front run L4 (with his oil temp leg), the injector branch L7, the coil branch L8, the turbo branch N19 with the driver-side drop L2 and the driver-side sensor branch N3, the gearbox speed branch N22 and the knock / coolant pressure branch N30. The agent added one branch, the intake sensor branch N5 (fuel pressure, IAT, MAP, flex fuel), so those four do not each break out of the trunk. Every device sits on a shared branch with its own spur (at least 152 mm when the branch goes on past it, and now also at the end of the trunk: the throttle body); a device at the end of its own branch ends that branch. Harness C follows: its RH fender run meets the new trunk start, its alternator stub starts on the new belt-end drop, and its engine block ground leg leaves the turbo branch N19 (was line 2). AB-engine total 104,410 -> 105,377 mm (85 wires); EngineRoom-C 4 wires +212 mm.
- X3 b (Dan 2026-11-10 00:08), Embed: try harness.design's Embed (linked sub-harness) only for pairs whose combined connection count stays under the plan's 100-connection limit; every other wire that continues into another file keeps the R10 note.
- U4 a (Dan 2026-11-10 00:58): the outside air temp sensor wires (`w_amb_sig`, `w_amb_rtn`; sensor A1 low in the front bumper to the auto A/C amplifier A32 behind the glove box) belong to EngineRoom-C, the front harness that already runs to the bumper; each stays one wire and passes through AB-cabin to the amplifier and the A/C sensor common splice, with an R10 note on its cabin end.
- Layout history check (2026-11-09, Dan: "a session messed them up"): AB-engine (Route 16) and HeavyDC match what Dan placed / approved. EngineRoom-C does not: since #496 (`02cc994`) 14 Route 17 device spots are the 2026-10-21 starting spots, written over Dan's 2026-11-01 hand placement (#467, `0e33138`; editor db backup `layouts/harnessC_route17_restore`) by the old editor's load-race save of 2026-11-02 10:39Z; the engine-bay redraw restores Dan's 11-01 spots (his 21:02 message: device locations are what matter; no lettered answer, so he can still object). AntiTheft's 2026-11-08 save was only half applied (siren only); Z13 b applies the rest.
- Top view only (Dan 2026-11-08, standing): an editor never has Dan place new devices on an isometric view. Placement happens on the top view only. An isometric view is allowed only once it shows exactly the same devices as the top view, already placed, with every route already drawn the optimal way.
- Reset (Dan N120, 2026-11-08): the CabinPower, WheelSpeed-Front / -Rear and RearFuel routes go back to before Dan's 2026-11-08 editor saves, and are redone under the rule above. The `cp4` tree work (N110 a box loop GB -> LOGIC -> POWER, N111 a RH kick line, N113 a fuel level tie-in, N114 a fan / EPS feeds by the kick line) is void, and its 135-change length list is not written (N115 a moot). A backup of the voided tree is kept in `_scratch/`.

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
  14 AWG TXL in the cabin (about 17.6 A), DRB102 cavity 95 size 12, 14 AWG then 16 AWG Tefzel in the bay (12 A); 14 AWG
  to match the cabin half (Dan N30 / N39 b, 2026-11-06): 14 AWG Tefzel about 18 A in the bay, above the 10 A LAM fuse;
  Link sets only a minimum, 0.85-1.00 mm2 (CAN-Lambda QSG p.2); the
  RealDash Pi on the factory CIG & RADIO 15 A, so its tap to the 5 A inline fuse `F-PI` is 16 AWG Tefzel (15 A; TXL 16 is about 12 A); the K-ON coil
  feed from the IGN 7.5 A fuse 18 AWG TXL, and the two older 1H-7 taps (`w_ig2_in`, `w_ign`) 20 -> 18 AWG TXL for the same
  fuse (Dan 2026-11-04; ECU-B pin 28 takes contact 3-1447221-3, 18-16 AWG). Known exception (Dan 2026-11-04, accepted):
  the CAN-Lambda's DTM size 20 contacts are rated 7.5 A (Link's own plug takes no larger contact) against its 8.1 A peak
  (manual p.5), a peak only during heater warm-up.
- CAN node feeds and grounds (plain wires since T1 a; their fuses and feed legs): "CAN wiring (B17)" P1 / T1 a, N52 a, N58 a.
- Fans (N78, Dan 2026-10-31: 12 in, not bought yet): sized for an 18 A 12 in fan (SPAL high-performance range 14.5-18 A): 10 AWG, size-8 DTHD sockets (8-10 AWG), relay FASTON 280756-4 (12-10 AWG, insulation 3.4-5.1 mm; 280755-4 grips 5.0 mm and up, too big for 10 AWG Tefzel), TE 36161 ring (12-10 AWG) at the AMI studs, AMI FAN and FAN2 30 A. Re-check against the fan's data sheet once bought. Each uprated fan has two single-pin leads, so two DTHD06-1-8S plugs per fan (`FAN-RAD` / `FAN-RAD-GND`, `FAN-COND` / `FAN-COND-GND`) are right (Dan 2026-11-04, Y1 b).
- Big cable lugs (Dan 2026-11-05): never stack large battery cables (2 AWG and up) on one stud; two 1/0 lugs cannot seat flat. Every big cable gets its own stud (a junction is a bus bar with one stud per cable, never the starter stud). HeavyDC (Dan N11 a, 2026-11-05): the engine-bay junction is a 4-stud bus bar at the OEM battery spot (battery now in the trunk), next to the jump post: Blue Sea PowerBar 600A `2104` (3/8-16 studs, 600 A DC; stud splices `SP-JUMP-1` .. `-4`, "Bus bars and fuse box ends"): stud 1 RADLOK + 1/0 in, stud 2 1/0 to the starter B+ (its one lug), stud 3 the alternator fuse block (no lug; below), stud 4 2 AWG to the jump post. Lengths from the Route 1 tree, Dan OK'd 2026-11-05. The alternator lead gets a fuse at the bus bar (Dan N12 a, 2026-11-05): Blue Sea MRBF 175 A `5186` on a Blue Sea MRBF terminal fuse block `5191` bolted to bar stud 3 (3/8 in stud, 300 A block, M8 output stud: the alternator 2 AWG lug, 5/16 in ring, is its one lug; fuse interrupt 10,000 A at 14 V; bluesea.com/products/5191 and /5186) (Dan N26 a, 2026-11-05). Size: 175 A per B11 (fitted alternator 160 A); 2 AWG 105 C in an engine space carries 178 A (Ancor / ABYC temp-rating sheet), so the fuse protects the lead if `BC-2-RED` is 105 C rated: it is SAE J1127 SGX, rated 125 C (`docs/sourcing/harness-parts.csv`; SGX sheet sycor.com "-40 C to 125 C", checked 2026-11-06). In the master the fuse block is the INTEGRAL link `w_alt_fuse` "MRBF fuse (Blue Sea 5191)" from bar stud 3 (`SP-JUMP-3`) to its M8 output stud `SP-ALT-FUSE`, where `w_alt` lands (Dan N61 a, 2026-11-07; replaces the N29 a device and its mate).

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
| DRAWN (title block) = the initials on Rev A of that drawing, never changed. Rev-log BY = the initials of the person who requested that change, never an agent or tool name. Always DG for this project. The repo-root file `.drawing-initials` (`DG`, tracked, Dan X2 a 2026-11-09) is the record; a tool that reads the per-computer `%USERPROFILE%\.drawing-initials` (env `DRAWING_INITIALS`) uses the same `DG`; missing = a person is asked once, an agent stops. | R200 (Dan N41 = B, 2026-10-19) |
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
