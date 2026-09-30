# ST185 Harness Redesign — Unified Handoff

**Date:** 2026-09-27  
**Repo:** `st185-link-ecu-config`  
**Status:** Design decisions and checker audit complete; implementation not yet started.

## Objective

Rework the harness drawings so every file represents a physical harness that will actually be built. Electrical nets may cross harness boundaries, but each physical wire section, connector, cable, enclosure interface, and BOM item has one owner and is built once.

The drawings must remain useful for assembly: show real new connectors, exact OEM splice locations, EWD references, cable cores, shields, and harness boundaries without modeling factory connectors or devices that will not be installed as part of the new harness.

## Settled design rules

1. The far-end device defines the circuit. The ECU terminal is selected only after confirming that the ECU signal group can process that device.
2. ECU pins own ECU signals for assignment and source-of-truth purposes. After device-to-ECU assignments are settled, physical wiring is drawn.
3. Every crossover between separate new harnesses ends at a real inline connector. The mating half belongs to the receiving harness.
4. A shared physical route is not shared ownership. Every physical cable section is drawn and built once.
5. Shields float at device ends and terminate only at the ECU end.
6. The only shield exception is an inline electrical device with an enclosure; its enclosure may be part of the shield path. This applies to VRC boxes.
7. Do not raise the CAN termination issue again. It is settled and is not an open repair item.
8. OEM factory connectors and junction blocks are not new harness connectors unless the new harness physically plugs into them.
9. Connections to existing OEM wires or connector points are flying leads. Each flying lead must include the EWD connector ID, pin, page, wire color/function, and splice or attachment method.
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

## Current state

This handoff and the previous separate plan/audit files are design artifacts in the workspace output directory. No harness drawings or checker scripts have been modified or deleted yet. Deleting legacy checker scripts requires replacement validation first.
