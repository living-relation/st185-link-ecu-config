# Harness and wiring - what is in this folder

**The ONE wiring source of truth is `MASTER-wirelist.csv`** (DECISIONS R221): one row per wire, FROM end to TO end, for
every harness. `sot/channels.csv` keeps only the ECU channel settings and is checked against it. Every rule Daniel has set
is in `redesign/DECISIONS.md` "Binding rules B1-B30"; this page restates none of them (it holds the factory-wiring detail
that B9 points to).

| Path | What it is | Edit it? |
|---|---|---|
| `MASTER-wirelist.csv` | every wire, cavity, splice, mate and spare of every harness | **Yes - the only wiring file you edit** |
| `sot/fuse-relay-map.csv` | B1 / B2 / B3 / B4 seat to circuit (not a wire list) | Yes, when a seat changes |
| `drawings/` | generated: each drawing set as three PDFs (`<set>-schematic.pdf`, `<set>-layout.pdf`, `<set>-pinout.pdf`). Each grouped section is its own page (a section continues when it does not fit). A schematic page holds six wires, each in its own line colour so it can be followed; the label keeps the wire colour. Layout pages are the approved drawings in `routes/`, including Routes 16 and 17 on 1993 EWD p.36. Routes 2-7 were wrong and are removed (Dan 2026-10-26); AB-cabin and CabinPower have no route file, so they fall back to the physical tree. Each page has its own title block and rev log. Plus the DRB102 insert-face map | No - re-run the generator |
| `wirelists/` | generated: one From / To wire list per harness (`ST185-<harness>-wirelist.xlsx`: Wires, Connectors, Splices, Spare Cavities, Key), in the Option A splice-column format (DECISIONS "Wire lists"; examples `option-a-examples.html`); so far AB-cabin and AB-engine (`"wirelists"` in the layout file) | No - re-run the generator |
| `tools/build_drawings.py` | the drawing generator; a drawing set is `tools/<set>.layout.json` (physical tree, harnesses in the set; the AB-engine part of the tree is built from Route 16's device spots and lines by `route_trees`, DECISIONS B8) + `tools/<set>.revs.json` (title block, rev log) | The layout and rev files, yes |
| `tools/check_wiring.py` | the ONE wiring check (also writes the IO table pin map with `--write-io-table`) | Only to add a rule |
| `routes/` | Dan's approved route drawing per harness (one HTML each, current version only) | Only from Dan's markup |
| `circuit-plan.md` | the 21 circuits, cut-list groups and the IG1 / IG2 table | Yes, when a circuit decision changes |
| `redesign/DECISIONS.md` | the one rules and decisions file (B1-B30, retire map, reconcile / shield / drawing / dispatch) | Only for a new Dan rule |

Generated views that are not committed (R221): the pinout `.xlsx` and thumbnails land in `out/` (gitignored).

## Change the wiring

1. Edit the rows in `MASTER-wirelist.csv` (pins exactly as the maker numbers them; a part number not confirmed by a maker
   document is `TBD`, never guessed).
2. `python docs/harness/tools/check_wiring.py` (add `--tbd` to list every TBD cell).
3. `python docs/harness/tools/build_drawings.py <set>` for a drawing set that holds the harness, and
   `python docs/sourcing/build_project_bom.py` for the shopping list.
4. `python tools/check_all.py` before the commit (CI runs it, plus `check_wiring.py --self-test`).

## harness.design copy (optional, never a source)

A harness.design document is only a viewer of the master (DECISIONS B6); nothing in it is edited back. AB-engine:
https://app.harness.design/lDDj (Rev K). How these are built and kept right (repo notes; the global `harness-design`
skill is not changed for this project):
- Built from the master + the `route_trees` layout tree by a throwaway script (freeze: none is committed). New or
  regenerated document: one `set_document_json`; every later change: `edit_document` ops with only what changes.
- Check after every upload: `validate_harness`, `get_wire_lengths` against the master, and the rendered view.
- Layout: keep each device and junction at its Route 16 spot; bundles follow the route corners, lightly smoothed (slants
  fine, no staircases or rapid turns). Change it in small steps; never swap in a different layout method (Dan 2026-10-29).
- Schematic: bulkhead left, splices middle, devices right; each wire horizontal, one 90 degree jog in its own lane,
  horizontal into its pin; no two signals on one line.
- Format facts (v1.3): bundle and branch-point points are `layoutPosition`; wire and cable-core points are
  `schematicPosition`, drawn at (x+15, y+15); a cable core's points run from the cable outward on both sides.
- The Pro plan (revisions work) has no connection limit, so AB-cabin can be one document.
- Parts view sync (Dan 2026-10-29): fix it whenever it shows up. Every part in the document must be in sync with the
  library (`compare_parts`). Out of sync: the library wins (pull), unless `docs/sourcing/harness-parts.csv` says
  otherwise. Not in the library: give the part its full maker, description and jacket colour from
  `harness-parts.csv`, then add it to the library with its accessories pointing at the library's own lock / contact
  ids. A `TBD` part is never added.

## Harnesses in the master

`AB-cabin` and `AB-engine` (the ECU harness, loom A and B merged, R220), `CabinPower`, `HeavyDC`, `EngineRoom-C`, `CAN`,
`CSB3`, `ClusterLED`, `AntiTheft`, `RearFuel`, `WheelSpeed-Front`, `WheelSpeed-Rear`. All 12 are drawn by
the generator as ONE drawing set, `ST185-harness` (`drawings/ST185-harness-schematic.pdf`, `-layout.pdf`, `-pinout.pdf`;
layout tree `tools/ST185-harness.layout.json`). Rear lights stay on the factory harness. AB-cabin has no route (Dan 2026-10-26): it runs from the bulkhead to the centre of
the dash near the floor, where every other harness to the ECU joins it; it is drawn left to right, and where each other
harness's branch joins is set in the layout tree. Part makers and descriptions
(AWG ranges) the BOM and the check read: `docs/sourcing/harness-parts.csv`. Fuse and relay seats: `sot/fuse-relay-map.csv`.

## Factory wiring facts (OEM ends)

- What stays and what goes (DECISIONS B1 / B9, surgical rewire, Dan 2026-10-20):
  - **Kept OEM:** every cabin wire (cowl, instrument panel, floor, door, seat, console and luggage room wires); cabin
    J/B No.1 and No.3 (what a kept J/B feeds stays fed from it: fuse, relay, pin); cabin R/B No.2 (windows, locks,
    sunroof, seat; its 30 A POWER fuse is re-fed by one new wire from the glove-box boxes) and R/B No.4 (one short new
    feed wire from the glove-box boxes; its heater relay, 40 A HEATER and 10 A A/C fuses and its starter relay stay)
    (Dan 2026-10-21: keep the complex OEM cabin wiring to cut wiring cost); the rear lights and their OEM wiring, reused
    as they are (no new RearLights harness; this replaces R55, Dan 2026-10-25); both A/C amps (A15 and the auto A/C amp
    A31 / A32, A23); the four wheel speed sensors (they feed the Link). Forward of the firewall only 6 in OEM pigtails
    stay, spliced to new wire at the headlights, turn / hazard and clearance / corner lamps, pop-up motors, ambient air
    temp sensor and wiper motor (B9).
  - **Removed (never a circuit source):** the Engine Wire; the Engine Room Main Wire (outer loop) and every Cowl Wire
    leg forward of the firewall, except those pigtails; every OEM relay and fuse box except J/B No.1 / No.3 and R/B No.2
    / No.4: J/B No.2, R/B No.3 (fog relay) and No.5, the ABS relay box (Dan 2026-10-21; their jobs
    are in the glove-box POWER / LOGIC boxes); the OEM engine ECU and igniter; every SRS crash sensor and SRS computer;
    the ABS computer and actuator; the brake fluid level switch (factory safety item, not needed, will not be connected); the whole fog circuit: the lamps (removed long ago), the fog light switch F12 on the dash and every fog wire, cut and capped (Dan 2026-10-25; fog only, the rest of B5 still removes to the last live point); the 20 A FR FOG fuse in R/B No.4 is left as a spare position. Each live wire that crossed from a
    removed part into a kept harness gets one row in the master: re-feed from the cabin side, or remove. A dead OEM wire
    comes out of its harness back to its last live point (splice, plug or box), except the fog leads above.
  - **Circuits decided (Dan 2026-10-21 to 2026-10-25; written into the master, row 164):** starter: the OEM starter relay
    in R/B No.4 stays, coil + from key START, coil - through the clutch start switch C11 (C11 completes the starter
    circuit in hardware; it is not an ECU input; no `k_str`; Aux 8 spare). Clutch: the cruise control clutch switch C17 (pin 2, B wire; pin 1 W-B stays on its ground) is the one ECU clutch input (flat-shift, via CSB3 VDI6);
    C11 is hardware starter only. Reverse: no K-REV; the back-up switch drives the lamps as OEM, its output is
    tapped through opto IN2 to the CSB3; the new switch wires (engine harness, bulkhead A) splice to the IG2-4 / IG2-13
    pigtails. Charge lamp: IG2-16 Y stays, the ClusterLED charge LED sinks to OEM cluster plug C12-8. IG2-15 B-R
    (ECU-IG) keeps a 6 in pigtail to the kill switch, then the alternator IG. ETB hold power is all cabin and J/B No.1
    stays: Aux 6 (A28) -> K-EFI, DI 9 (B28) IG sense, IG2 wake diode from J/B1 1H-7 -> A5, K-ETB on Aux 2 (A20) -> B5.
    A/C (D16): A15 drives `k_acc` (pin 8 to coil 85); Link Aux 4 is the ACT kill only; pin 2 hard-grounded; Ign 8 is tacho
    to pin 18 and through 4.7 kΩ to pin 9 (lock-sensor workaround, N61); A/C button and evap thermistor wires to the Link
    removed.     Cabin splice `SP-AC-SG` stays (sensor common). The A/C pressure switch is the factory trinary switch, wired to the factory A/C amp; factory yellow-red is that switch output, not the
    sensor ground (1990 ST185 EWD p.150 / p.152). Headlight-sense: R10 pin 1 through EL814 IN3 (OEM dimmer stays; Dan 2026-10-26).
    `w_pdb_jb1` lands behind the dash on J/B No.1 1I, 6 AWG for our 60 A JB1 fuse. Fuse box design is parked: seats live in `sot/fuse-relay-map.csv`
    (B1 POWER, B2 LOGIC, B3 trunk block, B4 EPS). Circuit plan: `circuit-plan.md`.
  - **New wire** (routes: `routes/ROUTE-16-ENGINE-MAIN.html` lines 1-9, `routes/ROUTE-17-FRONT.html` lines 10-13): the
    engine harness (Link to every engine sensor and actuator; through bulkhead A); power from the trunk battery up the
    passenger side to the glove-box boxes, then out through the RH fender grommet for engine-bay loads; the front run
    (inside the RH fender, then along the underside of the radiator support) to every front device; the driver fender
    run (driver kick pass-through) to the wiper motor and the alarm siren; one mini harness per front wheel speed sensor
    to the VRC enclosure by the ECU; the fuel pump circuit; one dash feed for the cluster, LEDs and RealDash Pi; CAN;
    the alarm add-on; power taps. No spare circuit to the old fog-lamp spots: aux circuits come later and are separate (Dan 2026-10-25).
    Engine-bay jump studs at the old battery spot are optional (owning harness open).
  - **Connectors:** the new wire mates only with each device's own connector (Dan has the mating plugs); no new inline
    connector anywhere on a run, and none added at the device, unless one later helps install or maintenance (fewer
    connectors, fewer failure points; Dan 2026-10-21).
  - Kept OEM ground points (where a high-current load may ground, B10): EA (M8 studs), EB, EC, ID, IE / IF, IG.
- Pin authority for OEM ends: the 1993 ST185 EWD (Dan 2026-10-20, DECISIONS R16): the 1993 TIS EWD pages in the
  `st185-celica-repair-manual` repo. The 1990 ST185 All-Trac book and the 1992 Celica EWD132U are reading aids only; an
  end still sourced from them is re-checked against 1993 (`docs/OPEN-ITEMS.md` row 156). The public PDF labelled EWD160U
  is the FWD AT180 / ST184 book: never use its pin numbers. Factory snips: `docs/electrical/ewd-snips/`.
- Before first power-up, with the battery isolated: ohmmeter from each cabin landing (J/B1, IE1, the old R/B2 / R/B4
  leads, blower, ignition switch) to its named load.
