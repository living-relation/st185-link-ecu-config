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

## Vocabulary (Daniel)

**Screen means shield.** A **drain** is the wire that connects the shield to the
pin. Shields exist only on cables. Some cables have a shield and some do not.
Not every shielded cable has a drain wire. When a shielded cable has no drain
wire and the shield has to land on a connector pin, the termination is a
Raychem solder sleeve with a wire lead, and that lead is the drain. Do not
solder a plain wire, a splice, a flying lead, or an unshielded part. A solder
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
| wss FL | drain connected on both the VRC input and the VRC output; ABS input drains splice together and terminate on a single pin; fender route, no bulkhead; combined 4-core output screen → `IX_WS_FRONT` c5 → `sp_shield_a` → A7 | none — fender; inline pin 5 |
| wss FR | same VRC-side cable as FL (one shared VRC output screen to A7); FR's own core leaves the shield at `IX_WS_FRONT` (c6 now spare, not a drain) and continues cabin-side as its own short shielded B-cabin spur, floating at the inline end, draining only at **B17** (Route 9 rev 3, 2026-10-10 - supersedes the earlier two-separate-output-cables design) | none — fender for the VRC leg; the B-cabin spur has no bulkhead either |
| wss RL, RR | drain connected on both the VRC input and the VRC output; ABS input drains splice together and terminate on a single pin; no bulkhead; output screen → `IX_WS_REAR` pin 5 → `sp_shield_b` → B17 | none — grommet; inline pin 5 |
| turbo speed, flex fuel, ETB sensor group (A22/A33) | **planned, not yet drawn** - redraw list below | new size-16 pin each, bulkhead A |
| ETB motor group (B18/B26), gearbox VSS, CAN-Lambda pair | **planned, not yet drawn** - redraw list below; these three plus knock 1 share bulkhead B's one spare drain pin (c1) via a 14 AWG pigtail splice, since bulkhead B has no other size-16/20 spare (`docs/RECONCILIATION-RULES.md`, DRB102 caveat) | shared pin, bulkhead B |
| CAN trunk + drops (ECU/CSB3/cluster/RealDash) | **planned, not yet drawn** - CAN pair only (H/L); +12V/ground stay plain. Joins the same bulkhead-B shared drain above | shared pin, bulkhead B |
| APS pedal — A group (VC2/GND2/VC1/GND1/VPA1) | **planned, not yet drawn** - folds into `IX_APS` growing a drain pin (`ST185-APS-Pedal` harness being folded into A-cabin, see `docs/OPEN-ITEMS.md`) | new pin, bulkhead A side of `IX_APS` |
| APS pedal — B group (VPA2) | **planned, not yet drawn** - same fold-in, B side of `IX_APS` | new pin, bulkhead B side of `IX_APS` |

Loom A screens land on A7 through `sp_shield_a`, loom B screens on B17 through
`sp_shield_b`. Nothing but a drain lands on A7 or B17. The "planned, not yet drawn"
rows above are the harness-reconcile pass's redraw list (currently crank/cam/knock
pass S1-S5; turbo speed, flex fuel, ETB, gearbox VSS, CAN and APS pedal still draw
loose, unshielded wires and fail S1-S5 until their harness files are redrawn - the
A-engine/B-engine/CAN/CSB3/APS-Pedal steps of the harness-reconcile pass, not yet
done). `docs/harness/audit_shields.py` only enforces what IS drawn; it does not
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

The VRC and its M8 connectors are not drawn (harness redesign, 2026-09-27). Each lead
ends at a registered VRC endpoint; `interfaces.json` "enclosures" names the IN and OUT
screen leads each case joins. `audit_shields.py` traces on that one graph through
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
