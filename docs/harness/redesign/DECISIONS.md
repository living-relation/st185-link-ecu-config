# ST185 Harness Redesign — Decision Record

**Date:** 2026-09-27  
**Repo:** `st185-link-ecu-config`  
**Status:** Frozen decision record. Merges `HARNESS-REDESIGN-PLAN.md` and `HARNESS-CHECKER-AUDIT.md`.
The phased work, and the conflicts with current rules that must be settled first, are in
[`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

## Objective

Rework the harness drawings so every file represents a physical harness that will actually be built. Electrical nets may cross harness boundaries, but each physical wire section, connector, cable, enclosure interface, and BOM item has one owner and is built once.

The drawings must remain useful for assembly: show real new connectors, exact OEM splice locations, EWD references, cable cores, shields, and harness boundaries without modeling factory connectors or devices that will not be installed as part of the new harness.

## Settled design rules

1. The far-end device defines the circuit. The ECU terminal is selected only after confirming that the ECU signal group can process that device.
2. ECU pins own ECU signals for assignment and source-of-truth purposes. After device-to-ECU assignments are settled, physical wiring is drawn.
3. Every crossover between separate new harnesses ends at a real inline connector. The mating half belongs to the receiving harness.
4. A shared physical route is not shared ownership. Every physical cable section is drawn and built once.
5. Shields float at the sensor and terminate at the ECU or at the destination device.
6. The only shield exception is an inline electrical device with an enclosure; its enclosure may be part of the shield path. This applies to VRC boxes.
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

The enclosure BOM defines Hammond 1590Y with TE Deutsch `HD34-24-33PE` as the enclosure receptacle. The harness shows the compatible mating plug `HD36-24-33SE` with size-20 socket contacts `0462-201-2031`, then stops. Do not draw CSB3 or the Hammond enclosure.

### VRC

Do not show VRC devices, enclosures, or M8 panel connectors. Use labeled endpoints such as `VRC_REAR_IN_L`, `VRC_REAR_IN_R`, `VRC_REAR_OUT`, and their front equivalents. Output semantics are +5V, Gnd Out, left output, right output, and shield/drain.

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
- Shield drains float at device ends and reach the correct ECU shield ground, except for VRC enclosure paths.
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

J/B2 2A / 2D / 2E stay real connectors: the build crimps a dummy header that plugs into
them (rule 8 exception). J/B1, IE1, R/B2, R/B4, the OEM switches and both A/C amplifiers
become flying leads.

## Open questions

| | Question | Options | State |
|---|---|---|---|
| Q-RAIL | The injector rail (F11 15 A) and COP rail (F10 20 A) feed A devices but cross on bulkhead B c1/c2, on size-12 contacts (`0460-220-1231` / `0462-210-1231`, 25 A). Rule 3 wants them on bulkhead A, which (`HDP24-24-47`) has 5 size-16 and 42 size-20 cavities, no size-12; the size-16 contacts are 13 A and only c1 is spare. | (1) keep on B as a recorded exception; (2) run both rails through loom C point-to-point like the starter and fan feeds; (3) replace bulkhead A with an insert that has size-12 positions; (4) split each rail over two size-16 contacts on A | ~~Resolved 2026-09-28 (Daniel): option (1) as a spur~~ **Final 2026-09-28 (Daniel): A side, through the DTP 4-way pass-through `IX_RAIL_A`** - see "Audit closed" below. Crossover (d) retired. |

## Binding decisions (Daniel, 2026-09-28 audit) - final, do not re-ask

| | Decision | Where it lives |
|---|---|---|
| B1 | **Link CAN-Lambda** runs its four wires through **bulkhead B**: c13 CAN H, c14 CAN L (size 16, 20 AWG), c3 +12V, c4 GND (size 12, 14 AWG, stepped to 20 AWG at `sp_lam12_b` / `sp_lamg_b` after the firewall for the DTM plug). +12V from cabin fuse **F5 10 A** (`ST185-CabinPower`); GND to the cabin chassis ground `sp_chassis`. Link pinout: pin 3 CAN L, pin 4 CAN H. Broken off CAN <-> B-cabin / B-engine. This uses bulkhead B's last four spares. | `ST185-CAN`, `-B-cabin`, `-B-engine`, `-CabinPower`, `-A-cabin`, `interfaces.json` |
| B2 | **VSS (E154F)**: drawn as-is on the best reading - Toyota 83181-20040, plug **90980-11143**, pin 1 IG +12V, 2 ground, 3 SP1 out. No TBD. | `ST185-B-engine`, `sot/channels.csv` B29 |
| B3 | **Charge-lamp resistor**: reference note on ClusterLED only, never a drawn part. | `ST185-ClusterLED` `n_chg_test` |
| B4 | `sp_5v` is split into `sp_5v` + `sp_5v_2`; `sp_gndout_eng` is a `GENERIC CRIMP SPLICE 14-10`: four 20 AWG = one 14 AWG combined (Wire Barn Combined Wire Gauge Calculator). Closed by Daniel 2026-09-28 under the combined-gauge splice rule below. | `ST185-A-cabin`, `-A-engine` |
| B5 | **Alternator output protection**: fusible link or inline fuse / breaker on the positive cable at the trunk battery or near the cabin fuse box - never at the starter. | `ST185-EngineRoom-C` `n_alt_prot`, plan 6.20 |
| B6 | Battery is **AGM**. Main power parts: Eaton RFRM box plus a small GEP set, a **Longacre 4-terminal kill switch** in the trunk (second pair cuts the alternator IG), and the G4X Stop Switch input. Drawn only where a place already exists; the power layout is not redesigned. | AGM and kill switch: `n_alt_prot`, `buylist.py`. RFRM, GEP and the Stop Switch input have no place in the drawings yet, so they are recorded here only |
| B7 | **RealDash Pi**: switched ignition feed only, on and off with the car. No Pi-hold relay or power-hold circuit anywhere. | EngineRoom-C `gbx_body` DEV, CSB3 L1 spare, plan 6.38 / 6.47 |
| B8 | **k_eps** sized: HCFB H4 Bussmann **AMI-60**, **8 AWG** feed. Sources in `sot/channels.csv` k_eps c1. | `ST185-CabinPower`, `-B-cabin`, `-EngineRoom-C` |

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
  not chase it. Owner text: `docs/RECONCILIATION-RULES.md` Rule 3.
- **Connector substitution - standing rule (Daniel, 2026-09-28):** if bulkhead A or B runs out
  of pins or needs higher-capacity contacts, spec a different connector or add a second one,
  with a complete compatible matching set for both sides (housings, inserts, contacts per wire
  gauge, seals / cavity plugs, wedgelocks, gasket or backshell), every part number from the
  maker's datasheet. Owner text: `docs/RECONCILIATION-RULES.md` Rule 3.
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
Full options and ratings are in `C:\projects\inbox\st185-research\BULKHEAD-OPTIONS-2026-09-29.html`
and `DRB102-RATINGS.html`.

Ratings: 6 of 9 checked items pass with margin against a firewall location (-55 to
125°C operating range, IP68 | IP6K9K mated sealing, vibration, mechanical shock,
thermal cycling, and per-size contact current) plus SAE J2030 automotive-connector
compliance. Three items (unmated sealing, an itemized fluid-resistance list, and salt-
spray duration) were not found on TE's reachable consumer pages; chasing the actual TE
spec/qualification PDFs for those is open item #40. Daniel, 2026-09-29: "PROCEED with
step 3 (implement), taking SAE J2030 compliance plus the strong pass on everything else
as good enough" — implementation went ahead on that basis; if a qualification PDF later
surfaces a real failure for a firewall spot, this decision is reopened.

The physical DRB102 is drawn as two logical halves so the A/B ECU-letter gate (Rule 3)
still applies to each side's own signals — `bh_a_fw` / `bh_a_eng` (49 cavities: the
former bulkhead A's 37 real circuits, unchanged size-16/size-20 upsized to size-16, plus
the two `IX_RAIL_A` power feeds folded in on size-12) and `bh_b_fw` / `bh_b_eng` (21
cavities: bulkhead B's existing 19 real circuits, already size-12/size-16, unchanged).
Every existing contact part number is reused unchanged (`0460/0462-202/201-1631` size-16
gold 13 A, `0460/0462-220/210-1231` size-12 gold 25 A already in the owned-stock and
contact library) — the DRB102 needed zero new contact parts, only new housings.

Each half's `.harness` file carries its own local `connectorParts` copy of the DRB102
housing (`cp_drb_recept` / `cp_drb_plug`), with `numberOfCavities` set to that file's own
cavity count (49 or 21) so `lint_v09.py`'s per-file cavity-count check still holds —
this is a per-file documentation choice, not a claim that the physical housing itself
has only 49 or 21 positions. The two halves are tied together with a new
`"physicalPartGroup"` field (`"drb102_recept"` on `bh_a_fw`/`bh_b_fw`,
`"drb102_plug"` on `bh_a_eng`/`bh_b_eng`) so `buylist.py` counts the housing and its
flange once, not once per half — see the "shared physical part" gap this closes,
below. The flange is wired through `cp_drb_recept`'s `mountPartId` (owned by the
alphabetically-first half, `bh_a_fw`) so it is bought exactly once. The DRB102 needs
**two** wedgelocks per shell (left + right, different part numbers:
`WB-51PAL`/`WB-51PAR` receptacle side, `WB-51SAL`/`WB-51SAR` plug side) and the
`.harness` schema only holds one `lockPartId` per connector configuration, so all four
are tracked as `buylist.py` `EXTRA` line items instead (documented in each half's
`lockParts` library for reference) rather than forced into that single field.

`buylist.py` gained the `physicalPartGroup` mechanism described above: distinct
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

## Current state

Execution is in progress; see the adopted decisions above and the phase status in
`IMPLEMENTATION-PLAN.md`. Deleting legacy checker scripts requires replacement validation first.
