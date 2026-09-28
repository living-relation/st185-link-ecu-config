# Harness Checker and Generator Audit

**Date:** 2026-09-27
**Scope:** `docs/harness/*.py` and `run_pipeline.bat`

## Summary

The current suite is built around the previous model:

- nine broad loom files,
- direct device connectors represented in drawings,
- `cp_xref` dummy nodes,
- VRC boxes and M8 connectors represented as harness components,
- direct wheel-speed-to-ECU endpoints,
- shared-connector BOM deduplication by connector ID,
- and a frozen legacy-prebuild connection comparison.

The new model requires real interface boundaries, owner-aware build/BOM output,
OEM flying leads, device endpoints, and separate front/rear wheel-speed Y
harnesses. The current suite should be divided into structural gates, ownership
and interface gates, and obsolete migration tools.

## Script disposition

| Script | Disposition | Reason |
|---|---|---|
| `lint_v09.py` | Keep, modify | Still needed for harness.design schema validity, but must accept the new endpoint metadata and revised connector categories without treating valid endpoint records as malformed. |
| `audit_cavity_parts.py` | Keep, modify lightly | The one-cavity/one-contact-or-plug rule remains valid for real connectors. It must ignore endpoint records that are not physical connectors. |
| `audit_bh_collisions.py` | Keep | One bulkhead cavity must still carry one circuit on each half. It is independent of the new inline-boundary model. |
| `audit_bulkhead_pairs.py` | Keep, modify | Real bulkhead A/B pairs still need both halves, but endpoint/flying-lead boundaries must not be mistaken for bulkhead halves. |
| `audit_pin_names.py` | Keep, modify lightly | Shield-ground purity remains mandatory. Bulkhead name parity remains mandatory. It should not inspect removed VRC connector cavities. |
| `audit_shields.py` | Keep, rewrite sections | Shield behavior remains mandatory, but VRCs are no longer drawn as connectors. The checker must validate the 5-pin output cable's drain and the abstract VRC enclosure exception without requiring modeled M8 shells. |
| `audit_mating.py` | Keep, substantially rewrite | Existing M1-M6 bulkhead checks remain useful. M7 assumes a device connector drawn on multiple looms and must be replaced with interface ownership checks. Remove VRC device-node assumptions. |
| `validate_sot.py` | Keep, modify | ECU pin ownership and one-signal-per-ECU-pin remain foundational. Add validation for non-ECU device circuits and ensure flying leads do not require fake ECU rows. |
| `sync_io_table.py` | Keep | Still governs the ECU pin source-of-truth and visual IO table. It should not be expanded to own OEM/VRC/CSB3 physical interfaces. |
| `buildlist.py` | Replace | It currently assumes each conductor's endpoints are directly buildable, reports cross-owner routes as `no route found`, and has no physical-owner/interface semantics. |
| `buylist.py` | Replace | Connector-ID deduplication and `cp_xref` stamping cannot express owner harness, inline connector pair, flying lead, or device endpoint semantics reliably. |
| `fix_cable_parts.py` | Retire after migration, or rewrite as a narrow validator | It hardcodes current 1/2/4-core cable classes and rewrites all rebuild files. The new VRC output requires a shielded 4-core-plus-drain cable and should not be silently rewritten by a legacy repair script. |
| `layout_633.py` | Replace/rework | Its zones hardcode VRC connector IDs and the old nine-loom arrangement. It also mutates files. The new layouts need separate wheel-speed Y harnesses and explicit inline interfaces. |
| `verify_rebuild.py` | Retire after migration | It compares against the old four-file legacy baseline and has large historical exception tables. The new physical graph intentionally changes ownership and boundaries, so this verifier would create false failures. Replace with a new connectivity/ownership verifier. |
| `make_min.py` | Keep | Whitespace-minified upload copies remain useful after the new files are generated. |
| `check_all.py` | Keep, rewrite | It should run the revised structural, ownership, interface, shield, BOM, build-list, and min-file gates. Remove the old verifier once retired. |
| `run_pipeline.bat` | Rewrite | It currently runs mutating legacy scripts in an old order and omits several hard gates. It should call the new explicit validation pipeline. |

## Detailed conflicts found

### `buildlist.py`

Current problems:

- Hardcodes nine filenames, not the new physical harness inventory.
- Treats a connector endpoint as a build endpoint even when it is only a
  cross-reference dummy.
- Has no concept of `physicalOwner`, `interfaceId`, `buildOnce`, or
  `oem_flying_lead`.
- Counts a long route as missing when it crosses files by design.
- Cannot distinguish an OEM flying lead from a missing connector.
- Current `Route` field follows local bundle graphs only, so cross-harness
  handoffs appear as `no route found`.

Replacement output should include:

- physical harness owner,
- interface ID,
- from/to endpoint type,
- EWD locator for OEM flying leads,
- real connector and mating-half details,
- build-once identity,
- cable core/drain mapping,
- and an explicit `handoff` rather than `no route found`.

### `buylist.py`

Current problems:

- Deduplicates by repeated connector ID across drawings.
- Assumes `excludeFromBom` and `cp_xref` identify the owner.
- Cannot count a connector pair once while preserving which harness owns each
  half.
- Adds hardcoded `DEVICE_SIDE` parts instead of reading explicit interface data.
- Treats OEM modeled blocks as not-a-part rather than modeling flying leads.
- Has no rules for a five-pin wheel-speed interface with a dedicated drain pin.

Replacement logic should count:

- a real inline connector pair exactly once,
- one mating half per receiving/owning harness,
- CSB3 HD36 plug and contacts as real harness parts,
- no OEM connector housing for flying leads,
- device endpoints as zero connector BOM,
- cable and splice material by physical owner,
- and the fifth wheel-speed connector pin/drain explicitly.

### `audit_mating.py`

Keep its bulkhead checks, but replace the old device-connector M7 rule with:

- every `inline_interface` has exactly two mating halves,
- the two halves belong to different declared harnesses,
- each interface net/core has one owner section on each side,
- no conductor skips an interface boundary between independent harnesses,
- VRC endpoint references are valid but do not require VRC connector objects,
- CSB3 ends at its harness plug rather than at a CSB3 device node.

### `audit_shields.py`

The current script explicitly requires modeled VRC connector IDs and shell
landings. That is incompatible with the new rule that VRC connectors are not
drawn. Replace those checks with interface metadata:

- wheel-speed sensor shields terminate at the abstract VRC enclosure endpoint,
- VRC output shield/drain is carried as the fifth cable/connector circuit,
- drain reaches the correct ECU shield pin,
- no drain lands on the ABS sensor device end,
- only the VRC enclosure exception may bond both sides of a screen.

### `fix_cable_parts.py`

The hardcoded 4-core VRC cable is close to the new requirement but the output
connector now has an explicit fifth drain pin. The cable model must distinguish:

- four insulated cores,
- overall shield/drain,
- drain termination at connector pin 5,
- and shield ownership/termination metadata.

Do not let this script silently rewrite newly modeled cables. Convert it into a
validator or replace it with an explicit cable-part generator after the data
model is settled.

### `layout_633.py`

The current `ZONE` table includes VRC connector IDs, `vr1_*`/`vr2_*` nodes,
and the old wheel-speed layout. It will place or park new endpoint/interface
objects incorrectly unless replaced. Layout should be generated per physical
harness, with wheel-speed Y branches readable and the ECU-side spurs shown as
short separate branches.

### `verify_rebuild.py`

This is the most likely false-failure source. It compares the current files to
`legacy-prebuild/` and encodes historical changes such as direct wheel-speed
runs, VRC connector cores, and `cp_xref` resolution. The new architecture is an
intentional physical decomposition, not a connection-preserving split of the
old graph. Retire it after a replacement ownership/connectivity verifier exists.

## Proposed replacement gates

1. `validate_interfaces.py`
   - interface IDs unique,
   - exactly two mating halves for inline interfaces,
   - harness ownership declared,
   - no missing endpoint references.
2. `validate_ownership.py`
   - every physical wire/cable has one owner,
   - `buildOnce` items have one BOM owner,
   - reference-only objects claim no BOM.
3. `validate_oem_endpoints.py`
   - every flying lead has EWD page, connector, pin, and connection method,
   - no OEM connector housing is counted as a new part.
4. `validate_wheel_speed.py`
   - front/rear each have two sensor branches,
   - one VRC input endpoint per side,
   - one shielded four-core output cable plus drain,
   - one five-pin inline connector,
   - ECU side has one spur per front/rear interface.
5. `validate_shields.py` replacement or revised `audit_shields.py`
   - abstract-endpoint-aware shield tracing.
6. `buildlist.py` replacement
   - owner-aware physical build list.
7. `buylist.py` replacement
   - interface-aware BOM with one-count semantics.

## Scripts proposed for retirement

Do not delete until the replacement gates and generators pass:

- `verify_rebuild.py`
- `fix_cable_parts.py` in its current mutating form
- `layout_633.py` in its current hardcoded nine-loom form

`cp_xref` objects should also be retired from new work. Existing ones can remain
only during migration and must not be used to represent an inline connector,
OEM flying lead, or VRC endpoint.

## Immediate next implementation slice

Before changing every loom, build one complete vertical slice:

1. Rear wheel-speed Y harness.
2. Rear five-pin shielded output connector.
3. ECU-side rear spur.
4. Revised ownership-aware buildlist/buylist records.
5. Revised shield/interface checks.

Once that passes, mirror it for the front wheel-speed harness. Then apply the
same endpoint convention to CSB3, OEM A/C, OEM junction-block connections, and
remaining harnesses.
