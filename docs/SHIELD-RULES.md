# ST185 shield rules — settled, do not re-ask

The shield rules themselves are **B14** in `docs/harness/redesign/DECISIONS.md` "Binding
rules B1-B30" (the one rules home; it wins over this file). This file is the build detail
that applies them (the shield pins and cavities are in `docs/harness/MASTER-wirelist.csv`).

**B14 detail.** Cable: TE Raychem Spec 55. Shielded: crank, cam, knock, wheel speed, VRC outputs, turbo speed, flex
fuel, gearbox VSS, ETB, APS pedal, the CAN-Lambda run and every CAN pair; injectors and coils get none. A drain is its own
`M22759/16-20-06` wire, found by its part, never its colour; no connector shell, and no sleeve just to end one screen. A cabin device that
joins a loom part-way splices its drain where its signal wires join; a bulkhead device keeps its own drain and bulkhead
pin up to the splice at the ECU plug. Each VRC box has one 5-pin CNLINKO LP-16 IN plug (pin 3 = both screens) and one
OUT plug; its board is isolated from the case.

**`docs/harness/tools/check_wiring.py` S1-S3 enforces the drain and floating-screen rules (R207) mechanically, and
`tools/check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

Device pin, pin name, and whether that device gets a shield:
`docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`. Which ECU pin a device wire
lands on is owned by the ECU (`sot/channels.csv`, Link documentation, XtremeX
quick install manual).

## No connector shells (R33)

Every drain lands on a regular pin; no shell, backshell or shielding plate ever carries a
screen (the VRC LP-16 plugs included); the master has no shell pins, so a screen can only land on a numbered pin.

## Shared drain pin: one splice (R29, R30, R32)

Every shielded cable is drawn as if it had a drain wire, straight to its pin; no sleeve, no
splice just to end one screen. Two or more screens on one pin share ONE `GENERIC SOLDER
SPLICE` (no covering), placed on the pin's connector through its `locationId`
(https://docs.harness.design/component/splice), with one drain wire (no wire part number, R32) to the
pin. The T-splice is how it is built, not drawn (R30). Every CAN node branch shield goes into
its own named branch splice on the trunk drain (`SP-CAN-SH-*`, R207; the one exception to "one splice").
**CAN branch splices (Dan 2026-10-25):** where each CAN node branches off the trunk for power and CAN signal, that
node's shield splices onto the main trunk shield at that same point, one splice per branch point, never all in one lump.
Each branch splice is a solder sleeve that takes a drain lead (Raychem / TE type); part number TBD (row 166).

| Pin | Screens into the one splice | Splice |
|---|---|---|
| ECU-A A7 | crank, cam, turbo, flex, ETB sensor, APS, front WS spur, front WS FR spur | `SP-SHIELD-A` at `ECU-A`; the crank drain is the one crimped into A7, the others are soldered onto it (R30) |
| ECU-B B17 | knock, ETB motor, VSS, rear WS spur | `SP-SHIELD-B` at `ECU-B` |
| ECU-COMMS C1 (R207) | CAN trunk drain `w_shd_can_trunk` (one wire); CSB3, cluster, RealDash, ECU cable and bulkhead / Lambda branch drains | one named splice per branch, `sp_can_sh_clu` / `_csb` / `_rd` / `_bh`, at that branch point |
| VRC front IN pin 3 | FL and FR sensor cables | `sp_vrc_f_in_sh` at `lp16_vrc_f_in` |
| VRC rear IN pin 3 | RL and RR sensor cables | `sp_vrc_r_in_sh` at `lp16_vrc_r_in` |

Every bulkhead drain has its own cavity, so no bulkhead cavity needs a shared splice.
Both sensor screens of a VRC share its input plug pin 3 (Dan's design); `check_wiring.py` S2 / S3 for the rest.

## Vocabulary (Daniel)

**Screen means shield.** A **drain** is the wire that connects the shield to the pin
(no wire part number, R32). Shields exist only on cables; a device or sensor gets one shield
flag (never per pin or per wire), in `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`.

## The absolute rules (R27, R28, R33)

A shield floats at the sensor, runs unbroken as a multi-conductor Raychem cable, and
terminates at an ECU shield pin (A7 / B17); the only device-end landing is the wheel-speed
sensor shields on VRC IN pin 3 (R31). A shield that crosses the firewall does so on its own
bulkhead pin, wired on both halves, never on a shell. Do not invent break points. The ABS
wheel-speed sensors have **two wires**: no third conductor, no shield connection at the
sensor.

## Bulkhead pass-through (Daniel, 2026-10-01)

Only a signal that already passes through both firewall bulkhead halves must carry its shield
through both halves on matching pins. That shield floats at the sensor, must not stop on either
half, and terminates at the ECU shield pin. Every such shield gets its own bulkhead cavity (the
pin list is the master wire list). Once the bulkhead connectors are installed
they are straight-through, so a shield is not required to float at the bulkhead.

Loom A screens land on A7 through `SP-SHIELD-A`, loom B screens on B17 through `SP-SHIELD-B`,
the CAN screens on C1 through the trunk drain. No screen crosses between loom A and loom B
(R207, `check_wiring.py` S3). Nothing but a drain lands on A7, B17 or C1.

## VR conditioner boxes (R31, R34)

The VRC device gets one shield flag. The sensor cables' screens and the output cable's screen
are one continuous path: sensor (floats) -> IN plug pin 3 (one splice, R29) -> wire inside the
box -> OUT plug pin 3 -> output cable screen -> the `IX-WS-*` pair -> the shield splice -> **A7** (front) / **B17**
(rear). The plugs are `VRC-F-IN` / `VRC-F-OUT` and `VRC-R-IN` / `VRC-R-OUT`: input 1 left +, 2 left -, 3 both screens,
4 right +, 5 right -; output 1 +5 V, 2 Gnd Out, 3 screen, 4 left out, 5 right out. `check_wiring.py` treats IN 3 to OUT 3
as one path through the box.

The VRC and its panel sockets are not drawn. Each VRC harness is two separate pieces ending in
two non-shielded 5-pin CNLINKO LP-16 plugs (`LP-16-J05PE-02-001`, S8 / R34 / S16). Nothing bonds to the case
and no shell carries the screen (R33): the box is not part of the shield path, the PCB sits
in a printed holder (S26) and grounds through the output cable only, and the box mounts on nylon
hardware. There is no bare-metal landing to mask before powder coat.

## ABS routing

| Pair | Runs with |
|---|---|
| Front (FL, FR) | through the fenders, with loom C |
| Rear (RL, RR) | with the fuel pump and level sender |

Neither pair gets its own firewall crossing, and the wheel-speed loom uses **no
bulkhead connector** — it crosses on a grommet so each screen stays unbroken.
