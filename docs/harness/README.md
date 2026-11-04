# Harness and wiring - what is in this folder

**The ONE wiring source of truth is `MASTER-wirelist.csv`** (DECISIONS R221): one row per wire, FROM end to TO end, for
every harness. `sot/channels.csv` keeps only the ECU channel settings and is checked against it. Every rule Daniel has set
is in `redesign/DECISIONS.md` "Binding rules B1-B30"; this page restates none of them (it holds the factory-wiring detail
that B9 points to).

| Path | What it is | Edit it? |
|---|---|---|
| `MASTER-wirelist.csv` | every wire, cavity, splice, mate and spare of every harness | **Yes - the only wiring file you edit** |
| `sot/fuse-relay-map.csv` | B1 / B2 / B3 / B4 seat to circuit (not a wire list) | Yes, when a seat changes |
| `drawings/` | generated: the pin chart `ST185-pin-chart.pdf` (the one pinout, a bench printout) and the DRB102 insert-face map `DRB102-bulkhead-map.png`. No layout / schematic PDFs: harnesses are built in harness.design (Dan 2026-11-01) | No - re-run the generator |
| `wirelists/` | generated: one From / To wire list per harness, `ST185-<harness>-wirelist.xlsx` (Wires, Connectors, Splices, Spare Cavities, Key) and `ST185-<harness>-wirelist.csv` (the Wires sheet; the only wiring CSV besides the master, F1), in the Option A splice-column format (DECISIONS "Wire lists"; examples `option-a-examples.html`); so far AB-cabin and AB-engine (`"wirelists"` in the layout file) | No - re-run the generator |
| `tools/build_drawings.py` | makes no drawings (Dan 2026-11-01): the layout tree, wire routing and master lengths (tree path + 100 mm at each wire end, `end_allowance_mm`, DECISIONS B8), the wire lists (xlsx + CSV, removal rows skipped) and the DRB102 map; a drawing set is `tools/<set>.layout.json` (physical tree, harnesses in the set; the AB-engine part of the tree is built from Route 16's device spots and lines, and the harness C (EngineRoom-C) part from Route 17's (runs 10 / 11, the RH fender grommet run, and Route 16 lines for the A/C, alternator plug, EPS pump and block ground), by `route_trees`, DECISIONS B8) | The layout file, yes |
| `tools/build_pin_chart.py` | builds `drawings/ST185-pin-chart.pdf` from the master; connector faces in `tools/pin_chart/` (sourced layouts; a connector without one is a numbered list, flagged) | The face files, yes |
| `tools/check_wiring.py` | the ONE wiring check (also writes the IO table pin map with `--write-io-table`) | Only to add a rule |
| `tools/gen_cabin.py` | builds the two harness.design AB-cabin documents from the master, split by device (Dan 2026-11-04, V1 a): `ST185-AB-cabin 1 - sensor rails and screens Rev B` (every wire joined through devices, splices and shielded cables to the sensor rails and screens: bus plugs `BUS-5V`, `BUS-5V-2`, `BUS-GNDOUT-A` / `-B`, splices `SP-8V`, `SP-SHIELD-A` / `-B`; so the pedal, the wheel-speed and fuel-level inlines and their cables) and `ST185-AB-cabin 2 - straight runs, power, taps and CAN Rev B` (the rest: plain ECU-to-bulkhead wires, ECU power and grounds, relays and new fuse boxes, factory taps, CAN); the ECU plugs A, B, C and `DRB102-CABIN` are drawn whole in both (cavities wired in the other one N/C with a note), every other device sits whole in one; `python gen_cabin.py <repo> <out> <1\|2>`, needs `<out>/lib.json` (part library 5LO8 dump); writes `abcab<1\|2>.json`, `abcab<1\|2>_lib_ops.json` and `abcab<1\|2>_expect.json`, then route with `genroute.py`. Built from the `ST185-harness.layout.json` tree (AB-cabin's placement-editor layout and the glove-box breakout `GB_T`); stops if a routed length differs from the master or a document passes 100 connections. Shielded cables are drawn as cables; labels per "Pin text" below. Layout = formboard; schematic = bulkhead and far ends left, cables beside them, splices middle, ECU side right, narrowest lane field that routes cleanly | Never by hand-editing its output |
| `tools/gen_engc.py` | builds the harness.design EngineRoom-C document (`ST185-EngineRoom-C Rev B`) from the master; `python gen_engc.py <repo> <out>`, needs `<out>/lib_engc.json` (part library 5LO8 dump); writes `ld37.json` and `ld37_lib_ops.json`, then route with `genroute.py`. Built from the Route 17 tree; stops if a routed length differs from the master. Layout = formboard (orthogonal, front right, driver up; a separate piece such as the EB block strap sits below); schematic = narrowest lane field that routes cleanly | Never by hand-editing its output |
| `tools/gen_abeng.py` | builds the harness.design AB-engine document (`ST185-AB-engine Rev C`) from the master; `python gen_abeng.py <repo> <out>`, needs `<out>/lib.json` (part library 5LO8 dump); writes `abeng.json` and `abeng_lib_ops.json`, then route with `genroute.py`. Built from the Route 16 tree alone (the HeavyDC segments that loop through it are left out, row 179); stops if a routed length differs from the master or the document passes 100 connections. Shielded cables are drawn as cables; a plug the master names as a connector's mate (the CAN-Lambda terminator) is drawn mated to it. Layout = formboard; schematic = bulkhead in the centre third, splices beside it, devices right, narrowest lane field that routes cleanly | Never by hand-editing its output |
| `tools/genroute.py` | orthogonal schematic routing for a harness.design document JSON (Dan's format rules); keeps node positions, rewrites wire / core / shield points; `python genroute.py <doc.json> <out.json>` | Only with the format rules |
| `tools/router.py` | the lane router `genroute.py` uses (box collision, a line along a box edge counts as a hit, shared lanes per splice or ground-stud net, crossing order) | Only with `genroute.py` |
| `routes/` | Dan's approved route drawing per harness (one HTML each, current version only); each is replaced by that harness's saved placement-editor layout when its pass is done (DECISIONS B8) | Only from Dan's markup or placement |
| `PLAN-2026-10-31-audit.md` | temporary hand-off plan for OPEN-ITEMS rows 170, 172, 173 and 175 (Dan 2026-10-31); deleted when they close | No - closed to additions |
| `circuit-plan.md` | the 21 circuits and the cut-list groups 1-8 wire by wire (remove / keep / re-fed by a master wire) | Yes, when a circuit decision changes |
| `redesign/DECISIONS.md` | the one rules and decisions file (B1-B30, retire map, reconcile / shield / drawing / dispatch) | Only for a new Dan rule |

## Change the wiring

1. ECU-pin circuits first: `AGENTS.md` "Before any wiring or CAN change" item 4 (a mismatch is a stop: ask Dan). Then
   edit the rows by hand in `MASTER-wirelist.csv` and, for ECU settings, `sot/channels.csv`, in the existing style; quote
   any field that contains a comma (pins exactly as the maker numbers them; a part number not confirmed by a maker
   document is `TBD`, never guessed).
2. `python docs/harness/tools/check_wiring.py` (add `--tbd` to list every TBD cell). After editing `sot/channels.csv`,
   also `python docs/harness/tools/check_wiring.py --write-io-table` (regenerates the `XTREMEX-IO-TABLE.html` pin map).
3. `python docs/harness/tools/build_drawings.py` (wire lists as xlsx + CSV, DRB102 map, length check; `--check` reads the
   lists back), `python docs/harness/tools/build_pin_chart.py` for the pin chart (it prints with Playwright's bundled
   Chromium, else the installed Edge, else Chrome; on Dan's PC: `uv run --no-project --with playwright --with pypdf
   python docs/harness/tools/build_pin_chart.py`), and `python docs/sourcing/build_project_bom.py` for the shopping list.
4. Before the commit, together: `python tools/check_all.py`, `python bench/check_parity.py` and
   `python tune/scripts/validate_tune.py` (CI runs `check_all.py`, plus `check_wiring.py --self-test`).
5. Ship it per `AGENTS.md` "Working rules" and DECISIONS B28 (PR with a `Rows:` line, then pr-closeout). Part numbers
   are picked per `docs/sourcing/README.md` (B21).

A removal row (a factory wire taken out of the car, back to its last live point; B5 "no row, no cut") is written as: `oem_method` starting "remove" ("remove whole: ..." or "remove back to <splice, plug or box>"), `wire_pn` `none (removed)`, gauge, colour and length blank. `check_wiring.py` audits it like any row; `build_drawings.py`, the BOM, the pin chart and the harness.design generators skip it (`build_drawings.is_removal`).

## harness.design - where the harnesses are built

Don't ask, build (Dan 2026-11-03): once a harness has its wire list, factory taps, route and lengths, the agent builds its
harness.design file straight away and sends the link; never stop to ask "now or later".
Every harness is built in harness.design from the master (Dan 2026-11-01, DECISIONS B6): it forces a wire list and a
planned layout first. The master stays the only wiring source; nothing in a document is edited back into it.
File names carry a revision letter (Dan 2026-11-02): `ST185-<harness> Rev A`. Only a physical change (wires, parts, pins,
lengths) makes a new file at the next letter (`Rev B`; agents cannot rename; Dan deletes the old file). A view-only
change (layout, schematic tidy, labels, colours) edits the same file and keeps its letter (Dan 2026-11-02). Current files
and their links: `docs/OPEN-ITEMS.md` "Current state" (the harness.design bullet). AB-cabin (two documents, 100-connection plan limit) is rebuilt
after its placement pass as new files (Rev A 2026-11-03; Rev B 2026-11-04, ECU plug C joined, split by device: `gen_cabin.py`) (the old
8OJ2 / kD3r and the unfinished CabinPower VlEB were deleted by Dan 2026-11-02). How these are built and kept right (repo notes; the global `harness-design`
skill is not changed for this project):
- Built from the master + the `route_trees` layout tree by the generators in `tools/` (`gen_abeng.py`, `gen_engc.py`, `gen_cabin.py`). New or
  regenerated document: one `set_document_json`; every later change: `edit_document` ops with only what changes.
- One device, one file (Dan 2026-11-04): a harness split over two files (100-connection limit) is split between
  devices, never through one: every wire a device has in that harness is in the same file. The one exception, AB-cabin:
  the ECU plugs and the bulkhead DRB102 are drawn whole in both its files (Dan 2026-11-04, V1 a). A device with wires
  in several harnesses (the ECU, the fuse / relay boxes) is drawn in each harness's file with that harness's wires.
  Wires between the fuse / relay boxes are their own harness (CabinPower, built later), never AB-cabin (Dan 2026-11-04).
- Check after every upload: `validate_harness`, `get_wire_lengths` against the master, and the rendered view.
- Review a harness by reading 10 random rows: each says what the wire does and its far end matches; never accept a
  harness on counts alone (practice per SAE AS50881 / IPC/WHMA-A-620).
- Layout view = a FORMBOARD (Dan 2026-11-02; replaces the 2026-10-29 "Route 16 spots, smoothed" rule): the harness
  drawn laid flat on a build table, organised for building it, not a copy of the car. The placement editor / route map
  is where install spots and lengths come from; the formboard only re-arranges them.
  - Straight trunk, branches off it at 90 degrees, on the grid; orthogonal lines only, no slants or curves.
  - Parallel runs bundled into one line; breakouts that sit close together merged into one branch.
  - Wire lengths stay exactly the master's (drawn length is not to scale; the numbers are).
  - Orientation: front of car RIGHT, rear / trunk LEFT, driver side on top. Each harness sits where it lies along the
    car, so harnesses that run the full length (cabin to trunk) fit; engine-bay harnesses have the bulkhead near the
    center third of the page (Dan 2026-11-02 (J1)). Never put the bulkhead on the left as a blanket rule.
  - A connector part-way along a line breaks out at least 6 in off it; the last one may end the run (B8). Coil and
    injector breakouts run parallel (Dan 2026-11-02 (J1)).
- Schematic: compact (fits one screen zoomed out); both columns start level at the top; connectors may be reordered
  for readability, pin order never changes (Dan 2026-11-02). The one exception: device rows may sit half a grid square
  (15 px) below the cabin-side rows so wires don't overlap (Dan 2026-11-03, N1 = a). Other harnesses: bulkhead left, splices middle, devices right; each wire horizontal, one 90 degree jog in its own lane,
  horizontal into its pin; no two signals on one line.
  - Engine harness schematic (Dan 2026-11-02 (J1)): bulkhead near the center third of the page; splices near the bulkhead,
    preferably on the cabin harness before the bulkhead, never in the middle of a run (injectors and ignition coils are the
    exception); devices to the right of the bulkhead; straight orthogonal runs with one 90 degree jog per lane.
  - 45 degree jogs may be placed close to devices, near splices and before connectors (Dan 2026-11-02 (J1)).
  - Parallel wires must not conceal or overlap other wires (schematic view only; overlap is unavoidable in the layout
    view); parallel runs in schematic views keep at least half a grid square between them (Dan 2026-11-02 (J1)).
- Schematic format (Dan 2026-11-01): every connector 8 grid units wide (`width` 240, document `schematic.connectorWidth`
  240). Lines orthogonal (plus the 45 degree jogs above, Dan 2026-11-02 (J1)); wires of one cable or one run share a path, side by side, like the real cable; no wire folds
  back over itself; no layout points next to a device or connector other than those 45 degree jogs (let the app route the last stretch; "Make
  orthogonal" in the app fixes a bad route). A part in parallel with two lines (e.g. the CAN 120 ohm resistor) sits
  between them with short equal legs. A ground stud is drawn on the side of the car its wires go to (LH pop-up and
  lamps at EB, RH ones at EA; Dan 2026-11-01), so LH and RH grounds can't be mixed up.
- Pin text (Dan 2026-11-01): a device pin says only what that pin does ("+8 V", "Gnd", "Signal", "Motor +", "Switched
  +12 V (NO)"); the device name is already on the connector. Bulkhead, ECU and splice ends name the device ("Gearbox
  speed signal"). Never "in" / "out" (direction is relative): "+12 V to reverse switch", "Switched +12 V from reverse
  switch". One name per device, the master's (reverse switch, not back-up switch). The text comes from the master's
  end descriptions; AB-engine done, every other harness when its document is next built. A device's factory lead (a
  terminal, so no connector name) carries the device name in its label, the master's, code in parentheses: "LH
  headlamp (H1) pin 3 (factory lead)" (Dan 2026-11-03).
  A splice end whose other legs are in another file or harness says where they go: "to AB-cabin 2, <device name>", and
  only a wire that ends there because it continues in another file carries a label naming its signal (Dan 2026-11-04).
  A factory tap names the device first, then its code, pin and the factory wire it splices onto: "A/C amplifier (A32)
  pin 15, spliced onto <wire>" (Dan 2026-11-04). A wire end at a new fuse / relay box names
  the box first, then the relay or fuse: "New LOGIC fuse box, K-EPS-EN", "New POWER fuse box, F12"; a wire between two
  boxes names both ends that way (Dan 2026-11-04).
- Format facts (v1.3): bundle and branch-point points are `layoutPosition`; wire and cable-core points are
  `schematicPosition`, drawn at (x+15, y+15); a cable core's points run from the cable outward on both sides.
- Connection limit: 100 connections per document (plan limit, 2026-11-01); a bigger harness is split by whole circuits into numbered documents (AB-cabin: 1 sensor rails and screens, 2 straight runs, power, taps and CAN; split by device, `gen_cabin.py`).
- Display stripes (Dan 2026-11-01): in each harness.design document every +12 V (red) wire gets a stripe colour per circuit, the same for every wire of that circuit, so crossing power wires can be followed; a note in the document lists them. Tracing only: the wire part, master colour and BOM stay plain red.
- Parts (Dan 2026-11-02 (J1)): parts come from library 5LO8 first; unconfirmed part numbers stay `TBD`; out-of-sync
  parts are synced and missing parts are added, as below. Parts view sync (Dan 2026-10-29): fix it whenever it shows up. Every part in the document must be in sync with the
  library (`compare_parts`). Out of sync: the library wins (pull), unless `docs/sourcing/harness-parts.csv` says
  otherwise. Not in the library: give the part its full maker, description and jacket colour from
  `harness-parts.csv`, then add it to library 5LO8 with its accessories pointing at the library's own lock / contact
  ids. A `TBD` part is never added.

## Harnesses in the master

Ten harnesses today. Purpose restored from `git show e2ec9d7^:docs/harness/README.md` "The 13 harnesses" (deleted in
#363) and re-read against today's master; which device belongs to which harness is the locked list in
`redesign/DECISIONS.md` "Harness ownership (B8 list)". Dan B8 = a (2026-11-02): `CAN`, `CSB3` and `ClusterLED` are one
`Dash` harness (master changed in phase 2, OPEN-ITEMS row 183).

| Harness | Purpose / scope | Route |
|---|---|---|
| `AB-cabin` | ECU harness, cabin side (loom A + B, R220): Link plugs A, B and C (C, the CAN / comms port, joined 2026-11-04, Dan V2 a), the cabin half of the DRB102, the ECU splice point (bussed plugs `BUS-5V`, `BUS-5V-2`, `BUS-GNDOUT-A`, `BUS-GNDOUT-B`; +8 V, switched 12 V, A5 feed and ECU power-ground splices), the ECU relay coil wires (relays sit in the boxes), APS pedal, A/C amp taps (A15 / A32 / A1), IG / reverse / start taps, both wheel-speed inline plugs, fuel level, and the cabin-to-trunk sill run (Dan B9 = a) | none (bulkhead to centre dash; placement editor, row 180) |
| `AB-engine` | ECU harness, engine side: the engine half of the DRB102 to every engine sensor and actuator, throttle body included, plus the CAN-Lambda, MR-S plugs B / C (Dan B7 = a) and the starter S wire (DRB102 cavity 3) | Route 16 (lines 1-9 today; line 9 "Alt and starter" moves to Route 1, Dan B6 = b) |
| `CabinPower` | Glove-box POWER (B1) and LOGIC (B2) boxes with their relays and every cabin power injection ("Power injection" below): J/B No.1, IE1, R/B No.4 re-feed, SW12 bus; the fog removal rows (`w_fog_*`, Dan 2026-11-02) | none (glove box to the kick panels) |
| `HeavyDC` | Trunk battery, kill switch, 1/0 cables to the POWER box and through the RADLOK pair, starter and alternator B+, engine block ground, jump post, trunk relay block (B3, `k_fp`), POWER NEG to grounds ID / IG | Route 1 (its engine-bay devices move there from Route 16, Dan B6 = b) |
| `EngineRoom-C` | "Harness C": every new front-of-firewall wire that is not ECU or heavy cable: headlamps, pop-ups, front lamps, wiper / washer, horns, fans, EPS pump plug A, A/C compressor clutch and pressure switch, alternator plug, ground studs EA / EB; its cabin ends are splices into the J/B No.1 / IE1 / IG2 / R/B No.4 factory leads | Route 17 lines 10-13 (+ RH fender grommet run) |
| `Dash` | Was `CAN` + `CSB3` + `ClusterLED` (Dan B8 = a). CAN 1 backbone (the only CAN H / L): the CAN joins at the ECU (ECU plug C itself is AB-cabin's, Dan 2026-11-04 V2 a), cluster and RealDash nodes, ECU-end terminator, dash 12 V split; ECUMaster CSB3 plug, cruise stalk buttons, C17 clutch, S9 brake, R10 headlight sense, the 8-channel opto board at the plug; warning LEDs (turn, high beam, charge, park brake, oil) fed from the OEM cluster plug taps | Routes 8 / 12 / 13 (old pages) |
| `AntiTheft` | Alarm module, siren, shock sensor, status LED, valet switch, door / hood / trunk pin and park-lamp leads | Route 14 |
| `RearFuel` | Fuel pump (from `k_fp` in the trunk relay block) and fuel level sender behind `IX-FUEL` | Route 11 |
| `WheelSpeed-Front` / `-Rear` | Wheel speed sensor -> VR conditioner -> inline DT to AB-cabin (`IX-WS-F` / `IX-WS-R`) | Routes 9 / 10 |

Alternator (Dan 2026-11-02): all 3 wires of the round 3-pin plug G2 (B) (1 S battery sense, 2 L charge lamp, 3 IG excite; ground through the case; 1993 EWD p.74-75) stay in one harness, EngineRoom-C (harness C, RH fender grommet to Route 16 line 9, no bulkhead pins); the heavy B+ cable stays in HeavyDC. Plug confirmed at the car (Dan 2026-11-02): the fitted 160 A alternator has the round G2 (B) plug, so the pinout above stands (the All-Trac grey G2 (A) plug, 1 L, 2 IG, 3 S, is not used).

Routes 1 and 8-14 are the old route pages; no tool reads them since #456, and each is replaced by that harness's
placement-editor layout at its pass (B8). Only Routes 16 / 17 carry device spots today. Deleted routes, for a harness's
starting map at its pass (all hand-drawn pictures, no route data, so their lines are traced into the editor): Routes 2-7
from `801c1f3^` (#402: 2 old harness C rev 12, 3 / 4 A- / B-engine, 5 / 6 A- / B-cabin = AB-cabin, 7 CabinPower, its
redraw approved in `5e5f21b`), read with `git show 801c1f3^:docs/harness/routes/<file>` (e.g. `ROUTE-7-CABINPOWER.html`); Route 15 rear lights
from `960e25e^` (#466; not needed, rear lights stay factory). Route 2 was the only drawing of harness C's cabin leg (glove
box under the dash to the RH fender grommet).

Each is built in harness.design (one at a time); the layout tree for all of them is `tools/ST185-harness.layout.json`;
pinout: `drawings/ST185-pin-chart.pdf`. Rear lights stay on the factory harness (no RearLights harness, #399). AB-cabin's route is its placement-editor layout (row 180): it runs from the bulkhead to the centre of
the dash near the floor, where every other harness to the ECU joins it; it is drawn left to right, and where each other
harness's branch joins is set in the layout tree. Part makers and descriptions
(AWG ranges) the BOM and the check read: `docs/sourcing/harness-parts.csv`. Fuse and relay seats: `sot/fuse-relay-map.csv`.

## Power injection (new box seat -> OEM landing or new harness)

Where each new box seat puts power into the car. Restored from the old power plan `ENGINE-ROOM-POWER-REDISTRIBUTION.md`
(sections 3.1, 5.2, 5.4; deleted in #363; read it with `git show` at `e2ec9d7^`, folder `electrical/`), re-checked against today's master and `sot/fuse-relay-map.csv`. The master
wire id is the source; this table only points at it. EWD = 1993 printed page. Kept rules from that plan: one source per
load; inject only where the factory feed came through the Engine Wire (J/B1 1I-1, IE1-10, IE1-17, plus the kept R/B No.2 /
No.4 fuses); J/B1 1H-7 (IGN) comes alive from AM2 through the ignition switch, so it is tapped, never fed; never land a
new feed on J/B1 1A-1G. Superseded from that plan: R/B No.2 / No.4 removed, `k_str` / `k_htr` / `k_pwr` / `k_rev`, the
1990 / 1992 pin pages, the kept ER Main (see `circuit-plan.md` groups 6-8).

**B1 POWER box (glove box, outboard)**

| Seat | Fuse / relay | Master wire (AWG) | Lands on | Powers | EWD | Status |
|---|---|---|---|---|---|---|
| AMI IN-1 (relay seat R1 vacant) | R/B No.4 feed | `w_rb4_feed` (8) | R/B No.4 40 A HEATER fuse pin 1, W (RH kick) | heater relay -> blower B4; 10 A A/C fuse (A/C amps, A5); the 20 A FR FOG fuse comes out, seat empty (`w_fog_fuse_in` removed back to I9) | p.62, p.215 | current; own pin id `HTR-1` (fault C3 fixed in phase 2) |
| AMI IN-2 | EFI 30 A, relay R2 K-EFI | `w_fb_k_efi_87_cp` (12), `w77_cp` (10) | K-EFI 30 -> LOGIC Bus 2 (switched bus) | everything on Bus 2 | - | current |
| AMI IN-3 | (vacant, was start 30 A) | - | - | - | - | vacant (starter on OEM R/B No.4) |
| AMI IN-4 | radiator fan, relay R4 K-FAN | `w_fb_k_fan_87_cp` (10) -> `w_fan_pwr` (10) | new wire to the radiator fan (EngineRoom-C) | radiator fan | - | current |
| AMI IN-5 | condenser fan, relay R5 K-FAN2 | `w_fb_k_fan2_87_ac` (10) -> `w_fan2_pwr` (10) | new wire to the condenser fan (EngineRoom-C) | condenser fan | - | current |
| AMI IN-6 (relay seat R6 vacant) | (vacant, was R/B No.2 feed) | - | - | R/B No.2 is fed by AM1 through cowl splice I2, as stock (AMI OUT-3) | p.62, p.137 | vacant (Dan B17 b: `w_rb2_feed` dropped, phase 2) |
| AMI OUT-1 | LOGIC feed | `w_hc_fb` (8) | LOGIC Bus 1 (permanent bus) | everything on Bus 1 | - | current |
| AMI OUT-2 | RTR 30 A | `w_pmu_rtr` (10) | IE1 pin 3, W (cowl side) | retract control relay R8 pin 3 | p.116 | current |
| AMI OUT-3 | AM1 40 A | `w_pdb_am1` (8) | IE1 pin 10, W (cowl side) | ignition switch I13-4 AM1 (ACC / IG1 / ST1) via cowl splice I2; I2 also feeds the R/B No.2 30 A POWER fuse, as stock | p.62, p.66 | current (Dan B17 b, 1993 p.62 / p.137-142, US = Canada; master cites 1993 p.62 since phase 2) |
| AMI OUT-4 | AM2 30 A | `w_pdb_am2` (10) | IE1 pin 17, B-R (cowl side) | ignition switch I13-10 AM2 (IG2) | p.62, p.66 | current (master cites 1993 p.62 since phase 2) |
| AMI OUT-5 | J/B No.1 60 A | `w_pdb_jb1` (6) | J/B No.1 1I pin 1, B (6 in stub, behind the dash) | taillight relay, STOP, ECU-B, DEFOGGER, tail bus | p.62 | current (pin id `1I-1`; master cites 1993 p.62 since phase 2) |
| AMI OUT-6 | EPS 50 A -> B4 relay K-EPS | `w_fb_k_eps_30_ac` (8) -> `w_eps_pwr_bc` (8) | new wire to MR-S pump plug A pin 1 (EngineRoom-C) | EPS pump | - | current |
| ACPS | (vacant) | - | - | A5 pin 1 now from the kept R/B No.4 10 A A/C fuse (`w_acp_1`, p.211-212) | - | vacant |
| NEG studs | battery negative | `w_gnd_id`, `w_gnd_ig` (1/0) | ground ID (LH kick) and IG (R/B No.4 set bolt, RH kick) | cabin body grounds | p.229 | current (HeavyDC) |
| BAT / ALT / NEG studs | trunk battery in, out to the bay | `w_ks_h1`, `w_h3_radlok_pos`, `w_h6a_radlok_neg` (1/0) | kill switch; RADLOK + / - to the starter B+ and block | HeavyDC | - | current |

**B2 LOGIC box (glove box, inboard).** Bus 1 is permanent (from AMI OUT-1); Bus 2 is switched (K-EFI 30).

| Seat | Fuse / relay | Master wire | Lands on | Powers | EWD | Status |
|---|---|---|---|---|---|---|
| BUS1-1 | EFI86 5 A | `w_k_efi_86_cp` | K-EFI coil 86 | EFI main relay hold | - | current |
| BUS1-2 / BUS1-3 | HL / HR 15 A, relays M1 / M2 K-HL / K-HR | `w_hl_cp` / `w_hr_cp` -> `w_pmu_hl` / `w_pmu_hr`; coil 85 `w_head_coil_cp` | new wire to headlamp H1 / H2 pin 3 (EngineRoom-C); coils to IE1 pin 2, R-Y | headlamps (light switch C15 / retract relay R8 sink the coils) | p.116 | current; seats in `sot/fuse-relay-map.csv` (phase 2) |
| BUS1-4 | HZ 15 A via `SP-HZ`, relay M3 K-HORN | `w_hz_cp` -> `w_haz_cp`; `w_horn_30_cp`, `w_horn_86_cp` -> `w_pmu_horn_cp`; coil 85 `w_horn_85_cp` | IE1 pin 12, W (hazard); horns via `SP-HORN` (EngineRoom-C); coil to IE1 pin 19, G | hazard switch H5-8 / flasher; horns (horn switch sinks the coil) | p.130, p.185 | current; seat in the map (phase 2) |
| BUS1-5 | DOME 20 A | `w_pmu_dome` (14) | J/B No.1 1H pin 2, L-Y | dome, interior, clock | p.132 | current; owned by CabinPower, pin id `1H-2` (fault C4 fixed in phase 2) |
| BUS1-6 | (vacant, was WL 15 A) | - | - | door lock ECU, tilt-away stay fed from the R/B No.2 30 A POWER fuse output (AM1 via I2, as stock) | p.137 | vacant (Dan B17 b: `w_rb2_wl` dropped, phase 2) |
| BUS1-7 / BUS1-8 | ALM 5 A / ALMS 2 A | `w_at_12v_tie_cp` / `w_at_12v_shk_tie_cp` | alarm pin 1 / shock sensor A (AntiTheft) | alarm | - | current; seats in the map (phase 2) |
| BUS1-9 | alternator S | `w_alt_s_c` | alternator plug pin 1 (EngineRoom-C) | alternator sense | p.74 | current; seat in the map (ALTS 2 A, phase 2); `passes_through` cleared (was "CabinPower / HeavyDC") |
| BUS1-10 | ETB 7.5 A, relay M4 K-ETB | `w_fb_k_etb_30_cp` -> `w82_ac` | ECU plug B pin 5 (AB-cabin) | throttle motor power | - | current |
| BUS2-1 | CAN-Lambda 12 V | `w_lam12_cp` | DRB102 cavity 95 (AB-cabin -> AB-engine) | CAN-Lambda | - | current; seat in the map (phase 2) |
| BUS2-2 | SW12 bus | `w_cp_sw12_in` -> `BUS-SW12` | relay coil 86 of K-FP, K-FAN, K-ETB, K-FAN2, K-EPS, K-EPS-EN; `w_fb_sw12` -> AB-cabin switched 12 V (ECU A5 feed, DRB102 cavity 30) | relay coils, ECU switched 12 V | - | current; seat in the map (phase 2) |
| BUS2-3 / BUS2-4 | coils / injectors | `w_cop_pwr_ac` / `w_inj_pwr_ac` | DRB102 cavity 1 / 2 (AB-engine) | COP coils, injectors | - | current; seats in the map (phase 2) |
| BUS2-5 | CSB3 12 V | `w_csb12` | CSB3 pin 1 | CSB3 (Dash) | - | current; seat in the map (phase 2) |
| BUS2-6 | dash 12 V | `w_dev_cp` -> `SP-DEV` | cluster and RealDash Pi supplies (Dash) | centre cluster, RealDash | - | current; seat in the map (phase 2) |
| BUS2-7 | EPSEN 5 A, relay M6 K-EPS-EN (87 straight out, no second fuse; E3 a) | `w_fb_k_eps_en_30_cp` -> K-EPS-EN 87 -> `w_fb_mrs_en` | DRB102 cavity 83 -> MR-S plug C pin 1 (AB-engine) | EPS enable | - | current |
| BUS2-8 | ACC 10 A via `SP-ACC12`, relay M5 K-ACC | `w_acc_fuse` -> `w_fb_k_acc_30_cp`, `w_acc86` -> `w_acc_clutch` | new wire to compressor A4 pin 4 (EngineRoom-C); coil 85 from A15 pin 8 (`w_acc_trig`) | A/C clutch (D16) | p.210-211 | current |
| BUS2-9 | ALMIG 2 A | `w_at_ig_tie_cp` | alarm pin 3 (AntiTheft) | alarm ignition sense | - | current; seat in the map (phase 2) |
| BUS2-13 | start request | in `w_start_in_cp`, out `w_start` | tap on R/B No.4 starter relay pin 1, B-W (ST1) -> Link DI 7 (ECU plug B pin 30) | start sense | p.66 | current; own pin id `ST-1` (fault C3 fixed in phase 2) |

**B3 trunk relay block and B4 EPS relay**

| Seat | Fuse / relay | Master wire | Lands on | Powers | Status |
|---|---|---|---|---|---|
| B3 BATT / FP | 40 A (B11), relay K1 K-FP | `w_fp_feed` (kill switch MAIN2), `w_fp_30` -> `w_fpump_r` (10) | fuel pump pin 1 (RearFuel); coil 86 `w_k_fp_86_cp` from `BUS-SW12`, coil 85 `w_fp85` to ECU plug A pin 19 | fuel pump | current; the two coil wires ride the AB-cabin sill run (Dan B9 = a, phase 2) |
| B4 EPS | HCR 150 K-EPS | AMI OUT-6 above | MR-S plug A | EPS pump | current |

No new box feeds J/B No.3: what it feeds stays fed through J/B No.1 (B9). Before first power-up, with the battery isolated:
ohmmeter from each landing above to its named load.

## Factory wiring facts (OEM ends)

- What stays and what goes (DECISIONS B1 / B9, surgical rewire, Dan 2026-10-20):
  - **Kept OEM:** every cabin wire (cowl, instrument panel, floor, door, seat, console and luggage room wires); cabin
    J/B No.1 and No.3 (what a kept J/B feeds stays fed from it: fuse, relay, pin); cabin R/B No.2 (windows, locks,
    sunroof, seat; its 30 A POWER fuse is fed by AM1 through cowl splice I2, as stock: Dan B17 b) and R/B No.4 (one short new
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
    the ABS computer and actuator; the brake fluid level switch (factory safety item, not needed, will not be connected); the whole fog circuit (Dan 2026-11-02, replaces the 2026-10-25 cut-and-cap): no fog lamps, no fog relay, no fog wiring; every fog wire (to and from the fog switch F12, the fog relay R/B No.3 and the 20 A FR FOG fuse) is removed back to its last live point like any dead wire; the R/B No.3 relay and the FR FOG fuse come out (its R/B No.4 seat stays empty). Each live wire that crossed from a
    removed part into a kept harness gets one row in the master: re-feed from the cabin side, or remove. A dead OEM wire
    comes out of its harness back to its last live point (splice, plug or box).
  - **Circuits decided (Dan 2026-10-21 to 2026-10-25; written into the master, row 164):** starter: the OEM starter relay
    in R/B No.4 stays, coil + from key START, coil - through the clutch start switch C11 (C11 completes the starter
    circuit in hardware; it is not an ECU input; no `k_str`; Aux 8 spare). Clutch: the cruise control clutch switch C17 (pin 2, B wire; pin 1 W-B stays on its ground) is the one ECU clutch input (flat-shift, via CSB3 VDI6);
    C11 is hardware starter only. Reverse: no K-REV; the back-up switch drives the lamps as OEM, its output is
    tapped through opto IN2 to the CSB3; the new switch wires (engine harness, bulkhead A) splice to the IG2-4 / IG2-13
    pigtails. Charge lamp: IG2-16 Y stays, the Dash charge LED sinks to OEM cluster plug C12-8. IG2-15 B-R
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
    The engine-bay jump post at the old battery spot is HeavyDC's (`JUMP-POST`, DECISIONS "Harness ownership (B8 list)").
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
