# ST185 shield rules — settled, do not re-ask

The shield rules themselves are **R27-R34** in `docs/harness/redesign/DECISIONS.md` "Binding
rules from Daniel" (the one rules home; it wins over this file). This file is the inventory
and the build detail that apply them. The plan doc §6.27 / §6.30-6.32 is history.

**`docs/harness/audit_shields.py` enforces R1, R2, R3, R5 and R6 mechanically, and
`check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

Device pin, pin name, and whether that device gets a shield:
`docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`. Which ECU pin a device wire
lands on is owned by the ECU (`sot/channels.csv`, Link documentation, XtremeX
quick install manual).

## No connector shells (R33)

Every drain lands on a regular pin; no shell, backshell or shielding plate ever carries a
screen (the VRC LP-16 plugs included). `lint_v09.py` rejects any connector `shell`;
`audit_shields.py` R3 rejects any screen on a shell.

## Shared drain pin: one splice (R29, R30, R32)

Every shielded cable is drawn as if it had a drain wire, straight to its pin; no sleeve, no
splice just to end one screen. Two or more screens on one pin share ONE `GENERIC SOLDER
SPLICE` (no covering), placed on the pin's connector through its `locationId`
(https://docs.harness.design/component/splice), with one `M22759/16-20-06` drain wire to the
pin. The T-splice is how it is built, not drawn (R30). Every CAN node branch shield goes into
the one trunk screen splice (`sp_shield_can`).

| Pin | Screens into the one splice | Splice |
|---|---|---|
| ECU-A A7 | crank, cam, turbo, flex, ETB sensor, APS, front WS spur | `sp_shield_a` at `ecu_a`; the crank drain is the one crimped into A7, the others are soldered onto it (R30) |
| ECU-B B17 | knock, ETB motor, VSS, CAN trunk, rear WS spur, front WS FR spur | `sp_shield_b` at `ecu_b` |
| CAN trunk drain `w_shd_can` | CAN trunk, ECU port, CSB3, cluster, RealDash, bulkhead / Lambda branches | `sp_shield_can` at the branch point |
| VRC front IN pin 3 | FL and FR sensor cables | `sp_vrc_f_in_sh` at `lp16_vrc_f_in` |
| VRC rear IN pin 3 | RL and RR sensor cables | `sp_vrc_r_in_sh` at `lp16_vrc_r_in` |

Every bulkhead drain has its own cavity, so no bulkhead cavity needs a shared splice.
Gate: `validate_wheel_speed.py` W3 (each VRC harness has exactly one splice, which both sensor
screens share); `audit_shields.py` for the rest.

## Vocabulary (Daniel)

**Screen means shield.** A **drain** is the wire that connects the shield to the pin
(`M22759/16-20-06`, R32). Shields exist only on cables; a device or sensor gets one shield
flag (never per pin or per wire), in `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`.

## The absolute rules (R27, R28, R33)

A shield floats at the sensor, runs unbroken as a multi-conductor Raychem cable, and
terminates at an ECU shield pin (A7 / B17); the only device-end landing is the wheel-speed
sensor shields on VRC IN pin 3 (R31). A shield that crosses the firewall does so on its own
bulkhead pin, wired on both halves, never on a shell. Do not invent break points. The ABS
wheel-speed sensors have **two wires**: no third conductor, no shield connection at the
sensor.

## Bulkhead pass-through (Daniel, 2026-10-01, narrowed)

**This is the governing wording for firewall screens.** It limits the older
§6.32 "every shield gets its own bulkhead passthrough pin" wording: that
allocation applies only where this rule requires a bulkhead pin.

Only a signal that already passes through both firewall bulkhead halves must
carry its shield through both halves on matching pins. That shield floats at
the sensor, must not stop on either half, and terminates at the ECU or at the
destination device. Once the bulkhead connectors are installed they are
straight-through, so a shield is not required to float at the bulkhead.

## §6.32 — bulkhead pin allocation, in priority order

**Limited by "Bulkhead pass-through (Daniel, 2026-10-01, narrowed)" above —
that is the governing wording.**

**First choice: every shield gets its own bulkhead passthrough pin.** Allocate
that way whenever the pins exist. There are 16 free pairs on bulkhead A and 11 on
B, so first choice applies for through-bulkhead screens required by the
narrowing.

Fallback, if that ever stops being true:

1. Critical sensors keep a dedicated shield pin — crank and cam first, then knock.
2. Everything else shares one passthrough, then splits back out on the far side.
   Shields may be spliced together when the bulkhead runs out of pins.
3. All terminate together at the ECU shield grounds, however they crossed.

## Shield inventory

| Shield | Route | Bulkhead pin |
|---|---|---|
| crank | cable floats at the sensor → `bh_a_eng` c33 → `bh_a_fw` c33 → `sp_shield_a` → **ECU-A A7** | own pin, bulkhead A |
| cam | same, c34 → `sp_shield_a` → **A7** | own pin, bulkhead A |
| knock 1 | cable floats at the sensor → `bh_b_eng` c18 → `bh_b_fw` c18 → `sp_shield_b` → **ECU-B B17** (knock is pin B9, loom B) | own pin, bulkhead B |
| wss FL | drain connected on both the VRC input and the VRC output; ABS input drains splice together and terminate on a single pin (one shared splice, S9); fender route, no bulkhead; combined 4-core output screen → `IX_WS_FRONT` c5 → `sp_shield_a` → A7 | none — fender; inline pin 5 |
| wss FR | same VRC-side cable as FL (one shared VRC output screen to A7); FR's own core leaves the shield at `IX_WS_FRONT` (c6 now spare, not a drain) and continues cabin-side as its own short shielded B-cabin spur, floating at the inline end, draining only at **B17** (Route 9 rev 3, 2026-10-10 - supersedes the earlier two-separate-output-cables design) | none — fender for the VRC leg; the B-cabin spur has no bulkhead either |
| wss RL, RR | drain connected on both the VRC input and the VRC output; ABS input drains splice together and terminate on a single pin (one shared splice, S9); no bulkhead; output screen → `IX_WS_REAR` pin 5 → `sp_shield_b` → B17 | none — grommet; inline pin 5 |
| turbo speed, flex fuel, ETB sensor group (A22/A33) | 3- or 4-core cable (`cab_turbo`, `cab_flex`, `cab_etbs`) floats at the sensor → `bh_a_eng` c6 / c10 / c11 → `bh_a_fw` same → `sp_shield_a` → **A7** | own pin each, bulkhead A c6 / c10 / c11 (DRB 19 / 22 / 27, `docs/harness/DRB102-CAVITY-MAP.md`) |
| ETB motor group (B18/B26), gearbox VSS, CAN-Lambda pair | ETB motor: 2-core 18 AWG cable floats at the ETB (A-engine spur `cab_etbm_ae`), broken off to B-engine `cab_etbm_be` → `bh_b_eng` c22 → `bh_b_fw` c22 → `sp_shield_b` → **B17**. VSS: `cab_vss` floats at the VSS → c23 → `sp_shield_b` → B17. CAN-Lambda: `cab_can_lam` floats at the Lambda → `cab_lamcan_be` → c24 → B-cabin `cab_canbh_bc` → the CAN screen splice `sp_shield_can` → B17 (see CAN row). Each drain has its own cavity; the old shared B c1 pigtail plan is dropped | own pin each, bulkhead B c22 / c23 / c24 (DRB 88 / 91 / 94) |
| CAN trunk + drops (ECU/CSB3/cluster/RealDash) | CAN pair only (H/L); +12V/ground stay plain. Every segment is a 2-core shielded twisted pair (`cab_can_*` in ST185-CAN, `cab_can_csb_csb` in ST185-CSB3); the screens join at `sp_shield_can` and float at every node (ECU port, CSB3, cluster, RealDash, Lambda). One drain `w_shd_can` breaks off to B-cabin `sp_shield_b` → **B17** | none for the cabin drops; the Lambda leg uses bulkhead B c24 (row above) |
| APS pedal (VC1/GND1/VPA1, VC2/GND2/VPA2) | one 6-core shielded cable `cab_aps` on A-cabin, pedal to the ECU (2026-10-11, "pedal is one cable in A-cabin"); the screen floats at the pedal and drains at `sp_shield_a` → **A7**. The VPA2 core breaks off near the ECU to B-cabin (`w_aps_vpa2` → `br_w39` → B33, crossover (c)) | none — the pedal and the ECU are both in the cabin |

Loom A screens land on A7 through `sp_shield_a`, loom B screens on B17 through
`sp_shield_b`. Nothing but a drain lands on A7 or B17. The harness-reconcile pass's redraw list is
done: turbo speed, flex fuel, ETB, gearbox VSS and CAN were redrawn as shielded cables
2026-10-11 (plan §7.3), and the APS pedal as one shielded cable the same day. `docs/harness/audit_shields.py`
only enforces what IS drawn; it does not
yet flag these as failing because the device-level "Shield: yes" flags in
`docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` aren't cross-checked against the
drawings (`docs/OPEN-ITEMS.md` row 31).

`bh_a_fw` c1 / `bh_a_eng` c1 used to be a single shared drain. **Retired
2026-09-22** when §6.32 first choice was finally applied. Both are spare.

## VR conditioner boxes (R31, R34)

The VRC device gets one shield flag. The sensor cables' screens and the output cable's screen
are one continuous path: sensor (floats) -> IN plug pin 3 (one splice, R29) -> wire inside the
box -> OUT plug pin 5 -> output cable screen -> `IX_WS_*` c5 -> `sp_shield_a` / `sp_shield_b`
-> **A7** (front) / **B17** (rear). `audit_shields.py` R6 reads the both-end VRC screens from
`shieldBothEndsOk` in `docs/harness/interfaces.json`; `interfaces.json` "enclosures" names
the two drain pins each box joins (`<plug>.<pin>`).

The VRC and its panel sockets are not drawn. Each VRC harness is two separate pieces ending in
two non-shielded 5-pin CNLINKO LP-16 plugs (`LP-16-J05PE-02-001`, S8 / R34 / S16). Nothing bonds to the case
and no shell carries the screen (R33): the box is not part of the shield path, the PCB sits
on nylon standoffs and grounds through the output cable only, and the box mounts on nylon
hardware. There is no bare-metal landing to mask before powder coat. (The 2026-09-20 plan
§6.30 "enclosure is part of the screen" design is superseded; `docs/enclosures/` still
describes it - OPEN-ITEMS row 75.)

## §6.31 — ABS routing

| Pair | Runs with |
|---|---|
| Front (FL, FR) | through the fenders, with loom C |
| Rear (RL, RR) | with the fuel pump and level sender |

Neither pair gets its own firewall crossing, and the wheel-speed loom uses **no
bulkhead connector** — it crosses on a grommet so each screen stays unbroken.
