# ST185 Harness Redesign Plan

**Date:** 2026-09-27
**Status:** Design plan and checker audit; implementation not yet started

## Purpose

Rework the harness drawings so each file represents a physical harness that will
actually be built. Shared electrical nets may cross harness boundaries, but a
physical wire section, connector, enclosure, or BOM item must have one owner.

The drawings must show enough information to build and splice the harnesses
without modeling OEM connector housings that will not be replaced or mated.

## Non-negotiable design decisions

1. The far-end device defines the circuit. The ECU terminal is selected only
   after checking that the ECU input/output group can process that device signal.
2. ECU pins own ECU signals for assignment and source-of-truth purposes. Once
   device-to-ECU assignments are settled, physical wiring is drawn from those
   assignments.
3. All shields float at the device end and terminate only at the ECU end.
4. The only shield exception is an inline electrical device with an enclosure;
   its enclosure may be part of the shield path. This applies to the VRC boxes.
5. Do not raise the CAN termination issue again. It is settled and is not an
   open repair item.
6. Every crossover between separate new harnesses ends at a real inline
   connector. The mating half belongs to the receiving harness.
7. A shared route is not shared harness ownership. Each physical section is
   drawn and built once by its owner.
8. OEM factory connectors and junction blocks are not new harness connectors
   unless the build physically plugs into them.
9. Wires attached to existing OEM wires or connector points are drawn as flying
   leads. Each flying lead carries an EWD locator: factory connector ID, pin,
   wire color/function, page, and splice/attachment method.
10. CSB3 is a new device in an enclosure. The harness shows its compatible
    mating connector and stops there; it does not draw the CSB3 device.
11. VRC devices and their enclosure connectors are not drawn in the wheel-speed
    harnesses. Use labeled VRC input/output endpoints instead.
12. `cp_xref` is not sufficient as the long-term ownership model. References
    must identify owner harness, interface ID, and whether anything is built or
    purchased at that point.

## Physical harness set

### ECU-to-firewall cabin harness

Contains ECU-A, ECU-B, cabin-side firewall A, and cabin-side firewall B.
The only intentional A/B crossover is shared ECU power/ground distribution from
A-side sources to B-side ECU pins. Other circuits stay with their assigned ECU
connector and firewall bulkhead.

### Engine-A harness

Runs from engine-side Bulkhead A to A-assigned engine sensors and devices.
It must not cross over to Engine-B circuits on the engine side.

Includes the new dedicated A/C coolant-temperature switch circuit: sensor to
engine-side Bulkhead A. The circuit is not routed to the ECU.

### Engine-B harness

Runs from engine-side Bulkhead B to B-assigned engine sensors and components.
It must not cross over to Engine-A circuits on the engine side.

### Loom C — engine-room/high-current harness

Carries high-current power from the cabin battery/fuse/relay area through the
front fenders and engine-room perimeter. It feeds factory junction blocks,
dashboard/cowl/HVAC/front-perimeter loads, starter and alternator power, fans,
and jumper lugs. Heavy firewall crossings use RADLOK connectors.

OEM junction-block and OEM-device connections are flying leads with EWD
locator labels, not modeled OEM plug housings.

### Rear wheel-speed harness

One Y harness:

- Rear-left ABS connector to the rear VRC IN-L endpoint.
- Rear-right ABS connector to the rear VRC IN-R endpoint.
- One shielded VRC output cable: four conductors plus shield/drain.
- Output ends at a 5-pin Deutsch inline connector near the ECU.
- The fifth pin carries the shield/drain toward the ECU shield ground.

The VRC enclosure and M8 connectors are not shown.

### Front wheel-speed harness

Mirrors the rear wheel-speed harness:

- Front-left ABS connector to front VRC IN-L endpoint.
- Front-right ABS connector to front VRC IN-R endpoint.
- One shielded output cable: four conductors plus shield/drain.
- Output ends at a 5-pin Deutsch inline connector near the ECU.
- VRC enclosure and M8 connectors are not shown.

### ECU-side wheel-speed spurs

The ECU-side harness owns two small spurs only:

- Front wheel-speed spur to the mating half of the front 5-pin connector.
- Rear wheel-speed spur to the mating half of the rear 5-pin connector.

These carry ECU +5V, Gnd Out, two conditioned signals, and the shield/drain.
No ABS sensor wiring or VRC input wiring is owned by the ECU harness.

## Device/interface rules

### CSB3

The enclosure BOM defines Hammond 1590Y with TE Deutsch HD34-24-33PE as the
box receptacle. The harness shows the mating TE Deutsch HD36-24-33SE plug with
size-20 socket contacts 0462-201-2031, then stops. Do not draw CSB3 or its
Hammond enclosure in the harness file.

### VRC

Do not show the VRC enclosure or M8 panel connectors. Use endpoint labels such
as `VRC_REAR_IN_L`, `VRC_REAR_IN_R`, and `VRC_REAR_OUT`. The output endpoint
has +5V, Gnd Out, left output, right output, and screen/drain semantics.

### OEM A/C system

The OEM A/C amplifier owns the ambient, evaporator/water-temperature, and A/C
request/control functions. These are not CSB3 inputs. The A/C pressure switch
and ambient wiring are represented as OEM-side circuits/flying leads based on
the EWD. The A/C amplifier also receives its own dedicated coolant-temperature
switch from Engine-A through Bulkhead A, then a short cabin-side branch and
inline connector to the amplifier flying lead.

The ECU ECT sensor remains a separate ECU-owned circuit. A second coolant
sensor/switch is required for the A/C amplifier.

### Obsolete CSB3 A/C assumptions

Remove from the active model and setup documentation:

- CSB3 cabin temperature input.
- CSB3 evaporator-core input.
- CSB3 A/C-request input.

These are not unresolved CSB3 wiring gaps.

## Data-model changes

Add explicit endpoint/interface metadata rather than using generic dummies:

- `real_connector` — new connector physically installed in the harness.
- `inline_interface` — real connector pair ending one harness and starting the
  next; BOM counted once.
- `oem_flying_lead` — loose wire to an existing factory wire/point; no OEM
  connector part in the BOM.
- `device_endpoint` — labeled VRC/device boundary with no device connector
  shown in the harness.
- `reference_only` — context only; no wire, connector, or BOM claim.

Every physical conductor should identify `physicalOwner`, `interfaceId` when
applicable, `buildOnce: true`, and the receiving/owning harness.

## Implementation order

1. Freeze this decision record and create a machine-readable interface/ownership
   convention in the harness documentation.
2. Confirm the 5-pin Deutsch family and exact part numbers for the front/rear
   wheel-speed inline connector pair, contacts, seals, and backshells.
3. Define the new harness files or replacement names for ECU/cabin, Engine-A,
   Engine-B, Loom C, Front WheelSpeed, Rear WheelSpeed, Rear Fuel, and the A/C
   amplifier spur.
4. Remove obsolete CSB3 A/C circuits and convert OEM device/J/B endpoints to
   flying-lead records with EWD locators.
5. Correct Bulkhead A c32 to `spare` on every active drawing that shows it.
6. Add the A/C coolant switch to Engine-A and the cabin-side inline interface.
7. Rebuild front/rear wheel-speed drawings using the Y-harness and five-pin
   output interface model.
8. Add ECU-side front/rear wheel-speed spurs.
9. Replace ownership/BOM generation with interface-aware buildlist and buylist
   generation.
10. Replace or retire the old frozen-baseline verifier after the new physical
    graph has its own connectivity checks.
11. Regenerate min files and generated BOM/build-list outputs.
12. Run the revised checker suite and inspect every cross-harness interface.

## Acceptance criteria

- No VRC enclosure or M8 panel connector appears in wheel-speed harness files.
- Front and rear wheel-speed sensor drops each form one Y harness.
- Each VRC output is one shielded five-conductor interface ending at one real
  5-pin Deutsch connector.
- ECU-side harness has exactly one front spur and one rear spur.
- CSB3 harness ends at HD36-24-33SE and does not draw CSB3 itself.
- OEM endpoints are flying leads with EWD connector/pin labels and no OEM BOM
  connector parts.
- Every physical section has one owner and is counted once in the BOM.
- Bulkhead A/B mating and shield rules still pass.
- Shield drains remain floating at device ends and terminate at the correct ECU
  shield ground, except VRC enclosure paths.
- The checker suite reports no unexplained direct cross-loom conductors.
