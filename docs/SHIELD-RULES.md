# ST185 shield rules — settled, do not re-ask

Long form: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.27, §6.30, §6.31, §6.32.
This is the short version so it stops getting re-litigated.

**`docs/harness/audit_shields.py` enforces R1, R2, R3, R5 and R6 mechanically, and
`check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

R1 and R6 are the **single-device shield check**: a passive sensor screen floats
at the device, and a both-ended screen that is not a listed sensor continuation
fails. What that check covers, and what it excludes, is this file.

## The five absolute rules

1. **A shield is never connected at the device end.** It floats there. Always.
   *Single-device check. VRC and CSB3 enclosure screens are excluded — see
   Daniel, 2026-10-01 below.*
2. **It terminates at the ECU end only.** That is its single ground reference.
   *Single-device check. Same exclusion.*
3. **No connector in this build has a shell for a shield.** Do not model one, do
   not spec a connector that needs one, do not wire a drain to a connector body.
   *Exception: see the inline-active wording below.*
4. **A shield is cable only until it terminates at the ECU** — a core inside the
   cable, not a wire in its own right, right up to the ECU end.
5. **Shields pass THROUGH the bulkhead on their own pin, not on the bulkhead
   shell,** and that pin is wired on **both halves**.

## Inline active devices — exception (Daniel, 2026-10-01)

**This is the governing wording.** VRC screens and CSB3 enclosure screens are an
exception to the single-device shield rule. They are not one sensor line. Those
circuits include inline active parts. Their screens must be terminated at the
enclosure and at the ECU.

`audit_shields.py` therefore **excludes** VRC screens and CSB3 enclosure screens
from the single-device check (R1 float-at-device, and R6 fail a both-ended
screen that is not a listed sensor continuation). Crank, cam and knock stay on
that check and still end on `sp_shield_a` / `sp_shield_b`. The listed sensor
continuations the audit reads are `shieldBothEndsOk` in
`docs/harness/interfaces.json`: `cab_crank_c_sh`, `cab_cam_c_sh`,
`cab_knock_c_sh`.

CSB3 gets the same exception as the VRC. No CSB3 screen is drawn today; the
rule and the audit exclusion are in place so one can be added later. Do not
invent a CSB3 shield, connector or pin until one is actually drawn.

`cab_fout_fr_sh` (and its cabin continuations) is excluded from the
single-device check with the other VRC screens. It still lands on the existing
B17 path. **Do not add it, or its continuations, to the `VRC_FRONT` enclosure
screen list, and do not land it on the front case.** The front VRC case already
joins the IN screens and the OUT screen, and that OUT screen goes to A7.
Landing the FR screen on the front case would tie A7 to B17. `audit_mating.py`
M4 is unchanged and still fails that join. Do not invent a new enclosure
terminal for the FR screen.

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
| wss FL, FR (raw) | continuous through the **front** VRC enclosure, fender route, no bulkhead; FL/supply output screen → `IX_WS_FRONT` pin 5 → `sp_shield_a` → A7 | none — fender; inline pin 5 |
| wss FR (conditioned) | own 1-core screened cable, VRC OUT → `IX_WS_FRONT` pin 4 → ECU-B B21; screen → pin 6 → `sp_shield_b` → **B17**. Excluded from the single-device check with the other VRC screens (Daniel, 2026-10-01). Must **not** land on the front case or join `VRC_FRONT` enclosure screens — that would tie A7 to B17 | none; inline pin 6 |
| wss RL, RR | continuous through the **rear** VRC enclosure, no bulkhead; output screen → `IX_WS_REAR` pin 5 → `sp_shield_b` → B17 | none — grommet; inline pin 5 |

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
- **FR screen (Daniel, 2026-10-01).** The front box's FR conditioned output goes
  to ECU-B B21, so its screen belongs to B17. It rides its own 1-core screened cable
  whose screen stays on the existing B17 path (`IX_WS_FRONT` pin 6 → `sp_shield_b`).
  It is excluded from the single-device check with the other VRC screens. It
  **cannot land on the front case** and must not be added to the `VRC_FRONT`
  enclosure screen list: the case already joins the IN screens and the OUT screen
  to A7, so a B17 screen on that case would tie A7 to B17. Do not invent a new
  enclosure terminal for it. `audit_mating.py` M4 still fails that join.
- The VRC and its M8 connectors are not drawn (harness redesign, 2026-09-27). Each lead
  ends at a registered VRC endpoint; `interfaces.json` "enclosures" names the IN and OUT
  screen leads each case joins. `audit_shields.py` and `audit_mating.py` M4 trace on that
  one graph, through the inline interfaces, and M4 fails the build if A7 can reach B17
  through any box.

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
