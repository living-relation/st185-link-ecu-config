# ST185 shield rules — settled, do not re-ask

Long form: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.27, §6.30, §6.31, §6.32.
This is the short version so it stops getting re-litigated.

**`docs/harness/audit_shields.py` enforces R1, R2, R3, R5 and R6 mechanically, and
`check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

Device pin, pin name, and whether that device gets a shield:
`docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`. Which ECU pin a device wire
lands on is owned by the ECU (`sot/channels.csv`, Link documentation, XtremeX
quick install manual).

## No connector shells (Daniel, 2026-10-12, binding, project-wide)

**Never rely on a connector shell for a screen.** Every cable drain / screen lands on a
regular pin in the connector, the same way as any other conductor. No connector on this car
is chosen for a shieldable shell, and no screen continuity runs through a connector body,
backshell or shielding plate. This includes the VRC M8 plugs (DECISIONS S8): they are
non-shielded, and their drains have their own pins. It supersedes the metal-shell reasoning
in `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` 6.30 "Why M8 and not DT/DTM".
`lint_v09.py` rejects any connector `shell`; `audit_shields.py` R3 rejects any screen on a shell.

## Drain T-splice (Daniel, 2026-10-12, binding)

Raychem shielded cable has no drain wire. Each screen gets a Raychem SolderSleeve whose short
insulated lead is that cable's drain - a drain is a normal insulated wire.

- **Two or more drains on one pin: T-splice.** One drain is the one crimped (or soldered)
  into the pin. Each other drain is soldered onto it about **6 mm (0.25 in) behind the rear
  of the connector**: cut away about 6 mm of insulation at that one spot on the crimped drain
  and solder the other drain to it, then cover it. No combined-gauge pigtail, never two wires
  in one contact.
- **Drain gauge does not scale with the number of screens.** Drains carry only noise current,
  so the normal drain lead gauge stays (20 / 22 AWG). The combined-gauge splice rule
  (`docs/RECONCILIATION-RULES.md` Rule 3) is for power and signal splices only, never drains.
- **CAN:** every node branch drain T-splices onto the bus trunk drain (`sp_shield_can`, at the
  branch point), and the trunk drain T-splices onto the B17 drain behind ECU-B.
- Drawn as: each screen ends at its SolderSleeve splice (covering `S200-2-W1-22-9`) or, where
  the cable already arrives as a drain, at the T-splice; the T-splice is a
  `GENERIC SOLDER SPLICE` placed on the pin's connector (`locationId`, harness.design
  "drag its location handle onto a connector", https://docs.harness.design/component/splice).
  The wire from the T-splice to the pin is the last few mm of the crimped drain.

| Pin | Crimped drain | T-spliced onto it | T-splice |
|---|---|---|---|
| ECU-A A7 | crank (`w_drain_ecu_a` is its end) | cam, turbo, flex, ETB sensor, APS, front WS spur | `sp_shield_a` at `ecu_a` |
| ECU-B B17 | knock (`w_drain_ecu_b` is its end) | ETB motor, VSS, CAN trunk, rear WS spur, front WS FR spur | `sp_shield_b` at `ecu_b` |
| CAN trunk drain `w_shd_can` | CAN trunk | ECU port, CSB3, cluster, RealDash, bulkhead / Lambda branches | `sp_shield_can` at the branch point |
| VRC front IN pin 3 | FL sensor cable | FR sensor cable | `sp_vrc_f_in_t` at `m9_vrc_f_in` |
| VRC rear IN pin 3 | RL sensor cable | RR sensor cable | `sp_vrc_r_in_t` at `m9_vrc_r_in` |

Every bulkhead drain has its own cavity, so no bulkhead cavity needs a T-splice.

## Vocabulary (Daniel)

**Screen means shield.** A **drain** is the wire that connects the shield to the
pin. Shields exist only on cables. Some cables have a shield and some do not.
Not every shielded cable has a drain wire. When a shielded cable has no drain
wire and the shield has to land on a connector pin, the termination is a
Raychem solder sleeve with a wire lead, and that lead is the drain. Do not
put a solder sleeve on a plain wire, a flying lead, or an unshielded part (joining two drains
is a T-splice, above). A solder
sleeve is not for the sensor end when the sensor already has its own connector.

## The five absolute rules

1. **A shield is never connected at the sensor end.** It floats there. Always.
2. **If a shield exists on a cable, or the device source of truth says that
   device has a shield, the shield terminates at the ECU or at the destination
   device.** Shields stay continuous unless Daniel has named a specific break.
   He has not named one in this request, so do not invent break points.
3. **No connector in this build has a shell for a shield.** Do not model one, do
   not spec a connector that needs one, do not wire a drain to a connector body.
4. **A shield exists only on a cable** — a core inside the cable, not a wire in
   its own right, until a drain takes it to a pin.
5. **Only a signal that already passes through both firewall bulkhead halves
   must carry its shield through both halves,** on matching pins, not on the
   bulkhead shell. That shield floats at the sensor, must not stop on either
   half, and terminates at the ECU or at the destination device.

A device or sensor gets one shield. Do not mark a shield on a pin or a wire.

Anything in the source of truth that has a shield must not use individual
wires. It must use a multi-conductor Tefzel Raychem cable.

Also settled: the ABS wheel-speed sensors have **two wires**. No third conductor,
no shield connection at the sensor.

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
| wss FL | drain connected on both the VRC input and the VRC output; ABS input drains splice together and terminate on a single pin (T-splice, S9); fender route, no bulkhead; combined 4-core output screen → `IX_WS_FRONT` c5 → `sp_shield_a` → A7 | none — fender; inline pin 5 |
| wss FR | same VRC-side cable as FL (one shared VRC output screen to A7); FR's own core leaves the shield at `IX_WS_FRONT` (c6 now spare, not a drain) and continues cabin-side as its own short shielded B-cabin spur, floating at the inline end, draining only at **B17** (Route 9 rev 3, 2026-10-10 - supersedes the earlier two-separate-output-cables design) | none — fender for the VRC leg; the B-cabin spur has no bulkhead either |
| wss RL, RR | drain connected on both the VRC input and the VRC output; ABS input drains splice together and terminate on a single pin (T-splice, S9); no bulkhead; output screen → `IX_WS_REAR` pin 5 → `sp_shield_b` → B17 | none — grommet; inline pin 5 |
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

## §6.30 — VR conditioner enclosures

The VRC device gets one shield. Do not mark a shield on each wire. Do not
record a separate shell flag.

The VRC output cable is shielded, the same as the input. This is not a
shell-only shield. The drain is connected on both the VRC input and the VRC
output. The ABS input drains splice together and terminate on a single pin.
Each ABS sensor shield terminates on the VRC connector.

```
  ABS sensor           VR conditioner                               ECU
  (FLOAT) ═══ IN ── ABS input drains splice ── OUT ═══ shield splice ── A7 or B17
                     drain on the VRC input and on the VRC output
```

Front box → `sp_shield_a` → **A7**; rear box → `sp_shield_b` → **B17**.
`audit_shields.py` R6 reads the both-end VRC screens from `shieldBothEndsOk` in
`docs/harness/interfaces.json`.

The VRC and its panel sockets are not drawn. Each VRC harness is two separate pieces ending in
two non-shielded 5-pin M9 plugs (binder `99 0414 00 05`; DECISIONS S8, Daniel's example
2026-10-12): each sensor cable screen has its own Raychem `S200-2-W1-22-9` SolderSleeve with a
22 AWG drain lead; the left drain is the one soldered into IN pin 3 and the right drain is
T-spliced onto it about 6 mm behind the plug (DECISIONS S9 - this is how the "splice together
and terminate on a single pin" rule above is built); the output cable drain is OUT pin 5.
Inside the box the build wires IN pin 3 to OUT pin 5 - drain continuity is by pin, never by a
connector shell, and nothing bonds to the case. `interfaces.json` "enclosures" names the two
drain pins each box joins (`<plug>.<pin>`). `audit_shields.py` traces on that one graph through
the inline interfaces.

Two isolation rules, both of which fail silently and read as a flaky sensor:

- The **enclosure must not touch chassis**. It is part of the screen, not a ground.
  Nylon mounting hardware.
- The **PCB must not touch the enclosure**. Nylon standoffs. The board grounds
  through the output cable only.

Mask the three connector landings **and the case ring-terminal spot** before powder
coat — a coated landing breaks the screen.

## §6.31 — ABS routing

| Pair | Runs with |
|---|---|
| Front (FL, FR) | through the fenders, with loom C |
| Rear (RL, RR) | with the fuel pump and level sender |

Neither pair gets its own firewall crossing, and the wheel-speed loom uses **no
bulkhead connector** — it crosses on a grommet so each screen stays unbroken.
