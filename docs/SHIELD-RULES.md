# ST185 shield rules — settled, do not re-ask

Long form: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.27, §6.30, §6.31, §6.32.
This is the short version so it stops getting re-litigated.

**`docs/harness/audit_shields.py` enforces R1, R2, R3 and R5 mechanically, and
`check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

## The five absolute rules

1. **A shield is never connected at the device end.** It floats there. Always.
2. **It terminates at the ECU end only.** That is its single ground reference.
3. **No connector in this build has a shell for a shield.** Do not model one, do
   not spec a connector that needs one, do not wire a drain to a connector body.
   *One documented exception: the VR conditioner enclosures (§6.30 / §6.35).*
4. **A shield is cable only until it terminates at the ECU** — a core inside the
   cable, not a wire in its own right, right up to the ECU end.
5. **Shields pass THROUGH the bulkhead on their own pin, not on the bulkhead
   shell,** and that pin is wired on **both halves**.

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
| wss FL, FR | continuous through the **front** VRC enclosure, loom C fender sub-loom, no bulkhead; output screen → `sp_shield_a` → A7 | none — fender |
| wss RL, RR | continuous through the **rear** VRC enclosure, no bulkhead; output screen → `sp_shield_b` → B17 | none — grommet |

**The two shield grounds are never joined.** Loom A screens land on A7 through
`sp_shield_a`, loom B screens on B17 through `sp_shield_b`. The old shared
`sp_shield_cab` that tied A7 to B17 was split on 2026-09-22. `audit_mating.py`
(M3, M4) fails the build if a bulkhead-A screen reaches B17, a bulkhead-B screen
reaches A7, or the two pins are ever connected.

`bh_a_fw` c1 / `bh_a_eng` c1 used to be a single shared drain. **Retired
2026-09-22** when §6.32 first choice was finally applied. Both are spare.

## §6.30 — VR conditioner enclosures (the rule 3 exception)

The screen runs **unbroken** sensor → enclosure → ECU:

```
  ABS sensor        VR conditioner enclosure shell        ECU
  (FLOAT) ══════════ shell ── shell ══════════════════════ (SINK: shield gnd)
                  one continuous shield, PCB isolated from the shell
```

Two isolation rules, both of which fail silently and read as a flaky sensor:

- The **enclosure must not touch chassis**. It is part of the screen, not a ground.
- The **PCB must not touch the enclosure**. Nylon standoffs. The board grounds
  through the output cable only.

Mask the connector landings before powder coat — a coated landing breaks the screen.

## §6.31 — ABS routing

| Pair | Runs with |
|---|---|
| Front (FL, FR) | through the fenders, with loom C |
| Rear (RL, RR) | with the fuel pump and level sender |

Neither pair gets its own firewall crossing, and the wheel-speed loom uses **no
bulkhead connector** — it crosses on a grommet so each screen stays unbroken.
