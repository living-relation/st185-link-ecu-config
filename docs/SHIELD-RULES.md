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
   He has not named one in this request, so do not invent break points. The VR
   conditioner case (Daniel, 2026-09-25, §6.30) is the named break already in
   this file.
3. **No connector in this build has a shell for a shield.** Do not model one, do
   not spec a connector that needs one, do not wire a drain to a connector body.
   *Exception: see "Powered device inline" below.*
4. **A shield exists only on a cable** — a core inside the cable, not a wire in
   its own right, until a drain takes it to a pin.
5. **Only a signal that already passes through both firewall bulkhead halves
   must carry its shield through both halves,** on matching pins, not on the
   bulkhead shell. That shield floats at the sensor, must not stop on either
   half, and terminates at the ECU or at the destination device.

## Powered device inline — the one named break (Daniel, 2026-09-25)

Rules 1–3 describe a passive run, sensor to ECU. **When a powered device sits in
the middle of a cable, that cable's shielding is decided case by case and written
in this file.** Nothing is an exception unless it is listed here. R6 in the audit
fails any screen bonded at both ends that is not listed.

Listed today: the two VR conditioner boxes (§6.30 below). Both-end-bonded
screens allowed: `cab_fout_sh`, `cab_rout_sh` (VRC case to inline pin 5) and their
continuations through the inline interfaces, `cab_fspur_sh`, `cab_rspur_sh`,
`cab_fspur_fr_sh`. The list the audit reads is `shieldBothEndsOk` in
`docs/harness/interfaces.json`.

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
| wss FL, FR (raw) | continuous through the **front** VRC enclosure, fender route, no bulkhead; FL/supply output screen → `IX_WS_FRONT` pin 5 → `sp_shield_a` → A7 | none — fender; inline pin 5 |
| wss FR (conditioned) | own 1-core screened cable, VRC OUT → `IX_WS_FRONT` pin 4 → ECU-B B21; screen → pin 6 → `sp_shield_b` → **B17**, floats at the VRC so it never touches the enclosure (Daniel, 2026-09-25) | none; inline pin 6 |
| wss RL, RR | continuous through the **rear** VRC enclosure, no bulkhead; output screen → `IX_WS_REAR` pin 5 → `sp_shield_b` → B17 | none — grommet; inline pin 5 |

Loom A screens land on A7 through `sp_shield_a`, loom B screens on B17 through
`sp_shield_b`. Nothing but a drain lands on A7 or B17.

`bh_a_fw` c1 / `bh_a_eng` c1 used to be a single shared drain. **Retired
2026-09-22** when §6.32 first choice was finally applied. Both are spare.

## §6.30 — VR conditioner enclosures (the rule 3 exception, powered-device form)

The conditioner is a powered device, so its case is the screen junction. Two
segments meet there. The sensor drop floats at the sensor and lands on the case;
the output screen is bonded at **both** ends — case and ECU. The case is isolated
from chassis, so both-end bonding makes no ground loop. Bond the case to chassis
and it becomes one. Plan §6.42
(wheel speed shielding, segmented) describes the same arrangement; this section
is the governing wording (the §6.42 table was corrected to match on 2026-09-25):

```
  ABS sensor           VR conditioner enclosure (case)               ECU
  (FLOAT) ═══ IN pin 3 ── wire inside box ── ring terminal on case
                                              case ── OUT shielding plate ═══ shield splice ── A7 or B17
                     PCB isolated from the case; case isolated from chassis
```

- **Sensor drop (raw VR pair):** floats at the sensor, crosses the IN connector on
  **pin 3** (not the shell), and a short wire inside the box takes it to a ring
  terminal on the case.
- **VRC output cable:** screen bonded to the case at the OUT connector's shielding
  plate **and** to the ECU shield splice. Front box → `sp_shield_a` → **A7**; rear
  box → `sp_shield_b` → **B17**.
- **FR output (Daniel, 2026-09-25).** The front box's FR conditioned output goes
  to ECU-B B21. It rides its own 1-core screened cable whose screen lands on
  `sp_shield_b` and **floats at the VRC** — it never touches the front case. Do
  not invent a new enclosure terminal for the FR screen.
- The VRC and its M8 connectors are not drawn (harness redesign, 2026-09-27). Each lead
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
