# ST185 shield rules — settled, do not re-ask

Long form: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.27, §6.30, §6.31, §6.32.
This is the short version so it stops getting re-litigated.

**`docs/harness/audit_shields.py` enforces R1, R2, R3, R5 and R6 mechanically, and
`check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

## The five absolute rules

1. **A shield is never connected at the device end.** It floats there. Always.
2. **It terminates at the ECU end only.** That is its single ground reference.
3. **No connector in this build has a shell for a shield.** Do not model one, do
   not spec a connector that needs one, do not wire a drain to a connector body.
   *Exception: see "Powered device inline" below.*
4. **A shield is cable only until it terminates at the ECU** — a core inside the
   cable, not a wire in its own right, right up to the ECU end.
5. **Shields pass THROUGH the bulkhead on their own pin, not on the bulkhead
   shell,** and that pin is wired on **both halves**.

## Powered device inline — the one exception (Daniel, 2026-09-25)

Rules 1–3 describe a passive run, sensor to ECU. **When a powered device sits in
the middle of a cable, that cable's shielding is decided case by case and written
in this file.** Nothing is an exception unless it is listed here. R6 in the audit
fails any screen bonded at both ends that is not listed.

Listed today: the two VR conditioner boxes (§6.30 below). Both-end-bonded
screens allowed: `cab_fout_sh`, `cab_rout_sh`.

Also settled: the ABS wheel-speed sensors have **two wires**. No third conductor,
no shield connection at the sensor.

## §6.32 — bulkhead pin allocation, in priority order

**First choice: every shield gets its own bulkhead passthrough pin.** Allocate
that way whenever the pins exist. There are 16 free pairs on bulkhead A and 11 on
B, so first choice applies — **there is no sharing in this build.**

Fallback, if that ever stops being true:

1. Critical sensors keep a dedicated shield pin — crank and cam first, then knock.
2. Everything else shares one passthrough, then splits back out on the far side.
3. All terminate together at the ECU shield grounds, however they crossed.

## Shield inventory

| Shield | Route | Bulkhead pin |
|---|---|---|
| crank | cable floats at the sensor → `bh_a_eng` c33 → `bh_a_fw` c33 → `sp_shield_a` → **ECU-A A7** | own pin, bulkhead A |
| cam | same, c34 → `sp_shield_a` → **A7** | own pin, bulkhead A |
| knock 1 | cable floats at the sensor → `bh_b_eng` c18 → `bh_b_fw` c18 → `sp_shield_b` → **ECU-B B17** (knock is pin B9, loom B) | own pin, bulkhead B |
| wss FL, FR (raw) | continuous through the **front** VRC enclosure, loom C fender sub-loom, no bulkhead; FL output cable screen → `sp_shield_a` → A7 | none — fender |
| wss FR (conditioned) | own 1-core screened cable, VRC OUT c4 → ECU-B B21; screen → `sp_shield_b` → **B17**, floats at the VRC so it never touches the enclosure (Daniel, 2026-09-25) | none |
| wss RL, RR | continuous through the **rear** VRC enclosure, no bulkhead; output screen → `sp_shield_b` → B17 | none — grommet |

**The two shield grounds are never joined.** Loom A screens land on A7 through
`sp_shield_a`, loom B screens on B17 through `sp_shield_b`. The old shared
`sp_shield_cab` that tied A7 to B17 was split on 2026-09-22. `audit_mating.py`
(M3, M4) fails the build if a bulkhead-A screen reaches B17, a bulkhead-B screen
reaches A7, or the two pins are ever connected.

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
- **FR exception (Daniel, 2026-09-25).** The front box's FR conditioned output goes
  to ECU-B B21, so its screen belongs to B17. It rides its own 1-core screened cable
  whose screen lands on `sp_shield_b` only and **floats at the VRC** — it never
  touches the front case, which is on A7. That keeps A7 and B17 apart.
- `audit_shields.py` treats each box's IN pin 3 landings and OUT shell as one case
  node; `audit_mating.py` M4 fails the build if A7 can reach B17 through any box.

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
