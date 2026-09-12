# ECU I/O and pinout audit — 2026-09-12

Full cross-check of every document in this repo that claims an ECU pin, plus the
two harness.design `.harness` files. Method: machine-extract every `A1..A34` /
`B1..B34` claim from each source and diff them against each other.

## Verdict

**The repo documents already agree.** All four live sources match pin-for-pin on
all 68 Superseal cavities. No corrections were needed in the docs. Every defect
found was in the two `.harness` files, and those are fixed — see below.

## Sources compared

| Source | Role | Pins claimed | Agreement |
|---|---|---|---|
| `XTREMEX-IO-TABLE.html` | **Authority** — channel + pin + wire + function | 65 | — (baseline) |
| `apps/harness-schematic/index.html` | Interactive loom/schematic viewer | 68 | Exact match |
| `docs/harness/ST185-Signal.harness` | harness.design SoT / BOM | 68 | Exact match |
| `docs/XTREMEX-IO-VERIFY-2026-09-11.md` | Verification record vs official QSG | 55 | Exact match (subset) |
| `SCHEMATIC-WIRING.html` | One-page SVG schematic | 51 | Exact match (subset) |
| `WIRING.md` | Cluster GPIO + CAN only | 0 | Correctly defers to the IO table |
| `docs/harness/HARNESS_WIRING_DIAGRAM.html` | Redirect stub → `apps/harness-schematic/` | 0 | Fine as-is |
| `archive/…/ECU_WIRING_MASTER_SOURCE_OF_TRUTH.md` | Retired staging draft | 0 tables | Already banner-marked "NOT A SOURCE OF TRUTH" |

Two apparent conflicts were checked and dismissed as false positives:

- `apps/harness-schematic/index.html` passes strings like `"A9"` and `"S1"` as the
  third argument to `comp()`. That parameter is `ident` — a reference designator
  (**A**ctuator 9, **S**ensor 1), not an ECU pin. Real pin data in that file lives
  in the `loomPins("A", …)` / `loomPins("B", …)` tables, and those match.
- `B2`, `B3` and `B14` appear in the `.harness` file but not in the IO table.
  `B2`/`B3` are inside the table's `B4–B1` range notation; `B14` is the one empty
  cavity with no terminal. Both correct.

## Source-of-truth hierarchy (unchanged)

1. Flashed CAN configs → 2. PCLink configs → 3. **`XTREMEX-IO-TABLE.html`** →
4. loom-building aids (`SCHEMATIC-WIRING.html`, `apps/harness-schematic/`,
   `docs/harness/*.harness`).

Physical pin numbers, drive types and wire colours come from Link's official
XtremeX Quick Start Guide, never from a project doc alone.

## Defects found and fixed — POWER harness

All in `ST185 Link G4X XtremeX – Power Harness.harness`, now
`docs/harness/ST185-Power.harness`.

### 1. Relay terminal name copy-pasted onto 15 non-relay cavities

Cavity `c3` on fifteen parts was labelled `30 (+12V)` — relay-socket terminal
nomenclature that has no meaning on a sensor, coil or throttle body. Nine of them
were actually carrying sensor ground or a 5 V supply, so the label said `+12V`
on a wire that is Gnd Out.

| Part | `c3` was | `c3` now | What the wire actually carries |
|---|---|---|---|
| `cam` Cam Hall | `30 (+12V)` | `Gnd Out` | Black/White → `sp_gndout` |
| `map` MAP | `30 (+12V)` | `Gnd Out` | Black/White → `sp_gndout` |
| `oilp` Oil pressure | `30 (+12V)` | `Gnd Out` | Black/White → `sp_gndout` |
| `fuelp` Fuel pressure | `30 (+12V)` | `Gnd Out` | Black/White → `sp_gndout` |
| `clntp` Coolant pressure | `30 (+12V)` | `Gnd Out` | Black/White → `sp_gndout` |
| `turbospd` Turbo speed | `30 (+12V)` | `Gnd Out` | Black/White → `sp_gndout` |
| `etb` Bosch 74.5 mm ETB | `30 (+12V)` | `+5V (TPS supply)` | Orange → `sp_5v` |
| `buck` 12 V→5 V converter | `30 (+12V)` | `5V OUT` | Orange → `sp_5vbuck` |
| `cop1`–`cop4` | `30 (+12V)` | `IGF (to signal file)` | unwired here |
| `aps` Accel pedal | `30 (+12V)` | `APS-2 5V` | unwired here |
| `flex` Flex fuel | `30 (+12V)` | `Signal (to signal file)` | unwired here |
| `lambda` CAN-Lambda | `30 (+12V)` | `CAN H (signal file)` | unwired here |

The ETB one mattered most: a 6-pin Bosch DBW body has no +12 V pin at all. Motor
power arrives on the H-bridge (B18/B26); `c3` is the 5 V TPS supply.

### 2. Cam Hall ground return was the wrong colour

`w24` (Cam Hall `c3` → `sp_gndout`) was **Blue**. Every other Gnd Out wire in the
file is Black/White, and `XTREMEX-IO-TABLE.html` specifies Black/White for Gnd
Out. Corrected to Black/White.

### 3. Flex-fuel sensor was fed from the ECU +8 V rail — **build change**

`w217` ran the flex sensor supply to `sp_8v`, and the cavity was hedged as
`12V/8V`. `XTREMEX-IO-TABLE.html` specifies **12 V / Gnd Out / signal** for the
Continental 3-pin sensor, and the Link `+8V Out` (A6) is a low-current supply
intended for the cam Hall on Trigger 2.

Moved to `sp_sw12` (EFI-main-relay switched 12 V, same rail as the injectors,
COPs, turbo speed sensor and boost solenoid) and the cavity relabelled `12V`.
`sp_8v` now feeds the cam Hall only, which is what the IO table calls for.

**Verify this against the sensor you actually have before crimping.**

## Defects found and fixed — both harness files

### 4. Wheel-speed wires could not route

The VR conditioner flying leads (`vr1_*`, `vr2_*`) were never attached to the
bundle graph, so all eight wheel-speed wires had no path through the loom and
six real bundles (`bn_drv_vr1`, `bn_rear_vr2`, `bn_wssfl`, `bn_wssfr`,
`bn_wssrl`, `bn_wssrr`) read as empty. Added 12 lead bundles from `bp_vr1` /
`bp_vr2` to the conditioner terminals.

### 5. Dash controls had no loom run

The ODO/trip button and both encoders wired straight to the cluster header with
no bundle. Added 7 bundles from `bp_dash`.

### 6. POWER bundle tree was a 13-bundle stub

Only 14 of 46 parts were on the bundle graph, and none of the splices were, so
almost no power wire could route in layout view. Added 43 bundles: each splice to
its zone branch point, and each load/sensor to `bp_eng` or `bp_cabin`.

*Assumption:* splice homes were inferred from where they already sat in the
layout view — `sp_12v`/`sp_sw12`/`sp_5v`/`sp_8v` → `bp_a_out`, `sp_gndout` →
`bp_eng`, `sp_chassis` → `bp_b_out`, `sp_5vbuck` → `bp_cabin`. Adjust if the
physical splice locations differ.

### 7. Dead-end bundles removed

Seven bundles in the SIGNAL file ran to parts that carry no wire there because
they belong to the POWER file: `bn_batt`, `bn_chgnd`, `bn_rad`, `bn_fan2`,
`bn_mrs_p`, `bn_buck`, `bn_fpump`. Removed.

Note the test used: a bundle is dead only when one end is a **leaf** carrying
zero wires. A shortest-path occupancy test is unsafe here — where two equal
routes exist the loser reads as empty, and that would have deleted the three
real CAN runs (`bn_can_hub`, `bn_can_csb`, `bn_can_eng`).

## Both views rebuilt

Both files had every part on a flat 90 px pitch regardless of size. A 34-cavity
ECU connector is ~1080 px tall and a 37-cavity bulkhead ~1170 px, so ECU-A,
ECU-B, ECU-Comms and all four bulkheads were stacked on top of each other.

Rebuilt both views as labelled, colour-coded zone columns on the 30 px grid,
sized from real footprints (`60 + 30 × cavities`), with 180 px between columns
and 60 px between parts. Columns taller than 2400 px wrap into sub-columns so
the drawing reads wide rather than as one long ribbon.

| File | View | Canvas | Overlaps |
|---|---|---|---|
| POWER | layout | 4290 × 2730 | 0 |
| POWER | schematic | 2580 × 2790 | 0 |
| SIGNAL | layout | 8640 × 2820 | 0 |
| SIGNAL | schematic | 5490 × 2820 | 0 |

## Checks run on the output

- Validated against the official `https://docs.harness.design/files/harness/schema/v0.9.json` — **0 errors** in both files.
- Unique ids across the whole document — no duplicates.
- Every wire / bundle / mate reference resolves — no dangling ids.
- Every positioned part is a multiple of 30 (the harness.design grid).
- Rectangle-intersection test on real footprints — **0 overlaps** in all four views.
- Dead-end stubs — **0** remaining in both files.

## Follow-up pass — 2026-09-12, after Daniel's answers

### Flex-fuel supply confirmed at 12 V — item 3 closed

AEM's datasheet for the same Continental sensor (kit 30-2200 / 30-2201) gives
**Battery Voltage 9 to 18 V** and the pinout **1 = Vcc Battery 12 V, 2 = GND,
3 = Vout**. Output is 50 Hz = 0 % ethanol to 150 Hz = 100 %, with the negative
pulse width carrying fuel temperature. It wants a 12 V-tolerant frequency input
with an internal pull-up, which is exactly what DI 2 with the pull-up on
provides. The +8 V rail was below the sensor's 9 V minimum, so the move to
switched 12 V was required, not merely tidier.

Watch out for one error in that datasheet: the pull-up paragraph names "pins 1
(Vout) and 3 (Vcc)", which contradicts its own pinout table on the next page.
The table is right.

Source: <https://documents.aemelectronics.com/techlibrary_30-2201_flex_fuel_content_sensor_kit.pdf>

### Bulkheads are now real connectors — item 2 closed

Per Daniel: one circular MIL connector per Superseal loom, assigned straight
through. This supersedes the "bulkheads stay 2-cavity TBD blocks" line in
`.claude/rules/harness-wiring-conventions.md`, which has been updated.

| Loom | Firewall receptacle | Engine plug | Contacts | Used | Spare |
|---|---|---|---|---|---|
| A | `8STA0-14-35SN` | `8STA6-14-35PN` | 37 | 26 | 11 |
| B | `8STA0-14-35SA` | `8STA6-14-35PA` | 37 | 9 | 28 |

Souriau 8STA, shell 14 arrangement 35 = **37 contacts, size #22D**. Contact
count cross-checked against the MIL-DTL-38999 insert-arrangement table, where
the equivalent shell-15 arrangement 35 is also 37 contacts — the arrangement
number is not the contact count, so it has to be looked up. Keyway **N** on
loom A and **A** on loom B, so the two bulkheads physically cannot be
cross-mated. Both are stocked by XTRA Motorsport, the same supplier as the
`202K142-25-0` shell-14 boot already in the BOM.

Every wire crossing the firewall is now two wires terminating in a cavity —
`<id>_c` on the cabin side, `<id>_e` on the engine side — so the file yields a
real bulkhead pin schedule. 35 wires were split (86 → 121).

Cavities are numbered straight through in wire order, as asked. Note that the
A/B split follows **physical routing**, not the loom letter: `w205` (ECU-B B9,
knock sensor) and `w54` (ECU-B B21, front-right wheel speed) cross through
bulkhead **A**, because those devices sit on the A-side of the engine bay.

### Duplicate parts removed

Five power-only connectors (`rad_fan`, `fan2`, `buck`, `fuelpump`, `mrs_pwr`)
were deleted from the signal file, and the signal-only `ign_sw` block was
deleted from the power file — the same duplication in the other direction. All
six were verified to carry zero wires in the file they were removed from.

### `DOCS-CLEANUP-PLAN.html` archived

Moved to `archive/`. It was a 76 KB clone of the markdown that had drifted: it
never gained §0 "Terms defined on first use" or §13 "Reconciliation log". Eight
files across the repo cite the markdown; nothing cited the HTML.

## Still open

1. **Bulkhead contact and backshell part numbers are not yet in the BOM.** The
   shells are specified; the size 22D crimp pins and sockets are placeholder
   entries (`ct_8sta22p` / `ct_8sta22s`) and the shell-14 boot is already there
   as `202K142-25-0`. Confirm the exact contact and backshell numbers with the
   supplier before ordering.
2. **Wire gauge, length and terminate-at are still absent everywhere.** That is
   the remaining gap between this file and a cut-and-crimp sheet — see the
   `HARNESS-BUILD-LIST` note in `docs/HARNESS-FACES-2026-09-11.md`.
3. **Three resistor wires do not route through bundles** (`r_cam`, `r_fuellvl`,
   `r_cruise`). Each resistor has a `locationId`, which is how harness.design
   places an inline part, so this is expected — flagged only so it is not
   re-diagnosed later.

## 2026-09-12 follow-up (OEM blocks + BRZ pedal)

Later the same day the APS connector became a Subaru BRZ 6-pin Sumitomo TS 025
(not MP150 4-way), OEM connections were redrawn as generic blocks, and
bulkheads were collapsed from empty 37-way parts to 2-cavity TBD blocks.
Hold Power Ignition Switch is DI 9 (B28). See
`docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md`.

**Superseded in part.** The bulkhead-as-TBD-block decision was reversed by
Daniel the same day — bulkheads are real 8STA connectors with wires landing in
cavities, as recorded in the follow-up section above. The OEM-block treatment
still stands for relays, switches, the cruise stalk, the AC amplifier and the
ignition switch.
