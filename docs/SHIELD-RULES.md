# ST185 shield rules — settled, do not re-ask

Long form: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.27, §6.30, §6.31, §6.32.
This is the short version so it stops getting re-litigated.

**`docs/harness/audit_shields.py` enforces R1, R2, R3, R5 and R7 mechanically, and
`check_all.py` runs it.** If a change breaks one of these rules the build fails.
That is deliberate: these were settled once and kept getting re-opened because
nothing checked them.

R1 is the **single-device shield check** for a passive sensor screen: it floats
at the device. The old exclusive R6 (only listed screens may be both-ended, and
only crank, cam and knock may pass the firewall) is **withdrawn**. What the
checks cover, and what they exclude, is this file.

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
5. **Only a signal that already passes through both firewall bulkhead halves
   must carry its shield through both halves,** on matching pins, not on the
   bulkhead shell. A sensor screen floats at the sensor, must not stop on
   either half, and terminates at A7 or B17. A CAN-connector screen (cluster,
   RealDash, CSB3 CANbus drop, trunk) must also pass through if its signal does,
   then joins `sp_shield_a` and ends at **A7**. It must not land on B17,
   `ecu_com`, or `sp_shield_b`. The Link lambda 4-core screen is a loom-B
   through-screen:
   it floats at the controller, passes bulkhead B c2, and lands on B17.
   A screen that runs only in the
   cabin does not terminate at the bulkhead. A screened cable that is not
   broken by an inline connector and does not pass its signal through the
   bulkhead also does not terminate at the bulkhead.

## Inline active devices — exception (Daniel, 2026-10-01)

**This is the governing wording.** VRC screens and CSB3 enclosure screens are an
exception to the single-device shield rule. They are not one sensor line. Those
circuits include inline active parts. Their screens must be terminated at the
enclosure and at the ECU.

`audit_shields.py` therefore **excludes** VRC screens and CSB3 enclosure screens
from the single-device check (R1 float-at-device). They are not folded into the
bulkhead pass-through check. Crank, cam and knock stay on R1 and still end on
`sp_shield_a` / `sp_shield_b`. `interfaces.json` `shieldBothEndsOk` names the
cabin continuations of those three (`cab_crank_c_sh`, `cab_cam_c_sh`,
`cab_knock_c_sh`) as documentation, not as an exclusive permit.

CSB3 gets the same exception as the VRC. Two CSB3 shields, not collapsed
(Daniel, 2026-10-01):

- The **enclosure** screen (`cab_can_csb3_sh` on `ST185-CSB3`) is grounded at
  the CSB3 box on Loose `ep_csb3_sh`, the same case-ground pattern the VRC
  drawings already use. No connector, cavity, or part number.
- The **CANbus** drop screen (`cab_can_csb_sh` on `ST185-CAN`) splices onto
  the CAN trunk at `sp_can_sh`. It does not land on the CSB3 box.

`cab_fout_fr_sh` (and its cabin continuations) is excluded from the
single-device check with the other VRC screens. It **is** grounded at the
front VRC case, on the existing shared OUT case pin (`ep_vrc_f_out_sh`).
It stays on `IX_WS_FRONT` pin 6. `cab_fspur_fr_sh_ac` stays on that cavity
and stops at the break. `cab_fspur_fr_sh` continues onto `sp_shield_a` (A7),
not `sp_shield_b` / B17. The front case already goes to A7 through pin 5
and `sp_shield_a`; sending the FR continuation to B17 would join A7 to B17.
`audit_mating.py` M4 is unchanged and still fails that join. Do not invent
a new enclosure terminal for the FR screen. The rear box stays on B17.

Also settled: the ABS wheel-speed sensors have **two wires**. No third conductor,
no shield connection at the sensor.

## Bulkhead pass-through (Daniel, 2026-10-01, narrowed)

**This is the governing wording for firewall screens.** It is not the VRC / CSB3
enclosure exception, and it is not the CAN-node exception.

Only a signal that already passes through both firewall bulkhead halves must
carry its shield through both halves on matching pins. A **sensor** screen
floats at the sensor, must not stop on either half, and terminates at A7 or
B17. Once the bulkhead connectors are installed they are straight-through, so
a shield is not required to float at the bulkhead.

A screen that runs only in the cabin does not terminate at the bulkhead. A
screened cable that is not broken by an inline connector and does not pass
its signal through the bulkhead also does not terminate at the bulkhead.

`audit_shields.py` R5 / R7 fail the build if a shield lands on one half and
does not continue as a screen on the matching pin of the other half, or if a
through-bulkhead **sensor** screen stops on the bulkhead instead of reaching
A7 or B17. Where both halves already have the matching shield pin, the screen
continues through. Where a matching shield pin is not already drawn, leave
the drawing and report the miss. Do not invent a pin, cavity, connector or
part number.

Crank, cam and knock already pass through (A c33, A c34, B c18) and still
end on `sp_shield_a` / `sp_shield_b`. The older exclusive rule that only those
three may pass the firewall is withdrawn.

The Link lambda power, ground and CAN H/L pair all pass through bulkhead B
(c3 / c4 / c13 / c14). That screen is a **loom-B through-screen**: it
floats at the controller, passes both halves on **c2** (the unused size-12
cavity next to c3 / c4; contact stays size 12). A 14 AWG stub already in
the document (`M22759/16-14-0`) is what enters that contact; the 20 AWG
drain solders to it at `sp_lam_stub_e` / `sp_lam_stub_c`. The cabin drain
then lands on **B17** on its own conductor (`cab_lam_can_c_sh`). It does
not join `sp_shield_b`, the CAN ring, or A7.

## CAN screens — A7 via sp_shield_a, not ecu_com (Daniel, 2026-10-01)

**This is the governing wording for CAN-connector screens.** It is not the
VRC / CSB3 enclosure exception. It is not an A7 / B17 sensor screen.

Every CAN node run (CSB3, cluster `t_cluster_can`, RealDash
`t_realdash_can`, and the trunk toward the ECU) uses the
same 4-core shielded Tefzel already in the harness `*Parts` arrays:
`55PC1243-20-2/6/4/5-9` / `cab_sh_4c`. One common braid around all four
wires. Daniel 2026-10-01: the single-shield cable is fine. Do not hunt for
or invent a two-pair individually shielded cable. One pair of cores is CAN
H/L, one pair is +12V and ground. Where a drop branches off the trunk,
splice those drop screens to each other at the existing branch point
(`sp_can_sh`).

Power and ground splice into the trunk at the same location as the CAN
pairs (`sp_can12` / `sp_cang` with `sp_canh` / `sp_canl`). At the ECU they
splice from the switched supply that turns the ECU on (`sp_sw12`, F9,
`ecu_a` a5, `w78`) and the ECU ground (`sp_chassis`, a25 / a34, `w70` /
`w_a34`) into the **pin half** of the DTM-6, not onto the LTW.

The six inches from the Link CANLTW to the **socket** half of that DTM-6
(`dtm_can_s`, DTM06-6S) is `55PC1122-20-2/6-9` / `cab_sh_2c`: CAN H and
CAN L only. No power, no ground, no other conductors leave the LTW. The
stub braid is **not terminated** at either end — not on the LTW, not on
the DTM, not on pin 5, not on A7 / B17 / `ecu_com`, and not on the ground
symbol. Do not draw a shield pin for it. The CANLTW round plug itself is
**not drawn**. Do not invent it.

The **pin** half (`dtm_can_p`, DTM04-6P) is the start of the 4-core trunk.
House pinout: 1=+12V, 2=GND, 3=CAN L, 4=CAN H, 5=trunk shield, 6 unused.
The trunk braid passes pin 5, joins the node screens at `sp_can_sh`, and
continues broken off (`br_can_sh`) into `sp_shield_a` on `ST185-A-cabin`,
the splice that already drains into **A7**. It is not a second wire in the
A7 pin. It does not join `sp_shield_b`, and it does not land on `ecu_com`.
The partless ring `t_can_sh_gnd` is gone.

The Link lambda power, ground and CAN H/L cores still ride `cab_sh_4c`
through the bulkhead. That screen is **not** a CAN-connector screen. It
floats at the lambda controller, passes both halves of bulkhead B on c2,
and lands on B17 on its own conductor (`cab_lam_can_c_sh`). It does **not**
join `sp_shield_b`, and it does **not** go to A7, `ecu_com`, or the CAN
trunk. A Raychem solder sleeve with an integrated
drain (`S200-3-WI-22-9`, already in the covering parts) is used only where
a terminated CAN-node shield has no drain of its own, and only on the
terminated end (`sp_can_sh`). Device ends of the cluster and RealDash
CAN-node screens float. The CSB3 CANbus drop screen splices at `sp_can_sh`;
the CSB3 enclosure screen is on the box, not on that splice.

**Do not terminate that shield network on `ecu_com` or B17.** `ecu_com` on
`ST185-CAN` is the six-pin comms / tuning port (DTM06-6S). It is not the ECU
CAN connector. Do not land the CAN braid on any of its cavities. Pin 5 is
RS232 TX, even when this build marks it unused. Daniel's pin-5 shield
pass-through is on the **other** 6-pin DTM drawn on this harness:
`dtm_can_s` (DTM06-6S, socket, LTW stub) mated to `dtm_can_p` (DTM04-6P,
pin, trunk). Trunk shield lands on `dtm_can_p` pin 5 and continues into
`sp_shield_a` / **A7**. Do not add a 12V wire to `ecu_com`. Do not put any
shield braid in `ecu_com` c1. The LTW stub braid (`cab_ltw` / `55PC1122-20-2/6-9`)
stays open at both ends. Socket cavities 1, 2 and 5 stay plugged.

Lambda +12V and ground ride the same 4-core as CAN H/L. The screen uses
the existing unused bulkhead B cavity **c2** on both halves (size-12
contacts already on this connector: pin `0460-220-1231`, socket
`0462-210-1231`; 20 AWG drain in a 12–14 AWG contact, contact left as
drawn). It does not join the CAN-node screens.

`audit_shields.py` **requires** CAN-connector screens that have an end to
reach A7 through `sp_shield_a`, and it **fails** the build if one of them
reaches B17, any `ecu_com` cavity, or `sp_shield_b`.
`audit_mating.py` M4 is unchanged: screens must not join A7 to B17.
Center stays a CAN drop on `t_cluster_can`. Do not add a Center Cluster loom.

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
| CAN-Lambda 4-core | power / ground / CAN H/L through bulkhead B c3 / c4 / c13 / c14 on `55PC1243-20-2/6/4/5-9`. Screen floats at the controller → solder to 14 AWG stub `w_drain_lam12_e` → `bh_b_eng` c2 → `bh_b_fw` c2 via stub `w_drain_lam12_c` → `cab_lam_can_c_sh` → **ECU-B B17**. Not `sp_shield_b`, not A7, not the CAN trunk. Size-12 contact left as drawn (`0460-220-1231` / `0462-210-1231`) | own pin, bulkhead B c2 |
| CAN trunk / node screens | 4-core braid through `dtm_can_p` pin 5 → `sp_can_sh` → `br_can_sh` → `sp_shield_a` → **ECU-A A7**. CSB3 CANbus drop (`cab_can_csb_sh`) joins `sp_can_sh` and does not land on the CSB3 box. Cluster / RealDash device ends float. Not B17, not `ecu_com`. | none — DTM pin 5, then A7 |
| CSB3 enclosure | `cab_can_csb3_sh` on `ST185-CSB3` → Loose `ep_csb3_sh` at the box. Not the CANbus drop. | none |
| wss FL, FR (raw) | continuous through the **front** VRC enclosure, fender route, no bulkhead; FL/supply output screen → `IX_WS_FRONT` pin 5 → `sp_shield_a` → A7 | none — fender; inline pin 5 |
| wss FR (conditioned) | own 1-core screened cable, VRC OUT → `IX_WS_FRONT` pin 4 → ECU-B B21. Screen grounded at the front case on the shared OUT pin, stays on pin 6, `cab_fspur_fr_sh_ac` to the break, `cab_fspur_fr_sh` → `sp_shield_a` → **A7**. Not B17. | none; inline pin 6 |
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
  to ECU-B B21. Its screen is grounded at the front case on the existing shared
  OUT case pin, stays on `IX_WS_FRONT` pin 6, and continues onto `sp_shield_a`
  (**A7**), not B17. `cab_fspur_fr_sh_ac` stays on cavity 6. Moving that
  continuation onto B17 would join A7 to B17 through the case. The rear box
  stays on B17. Do not invent a new enclosure terminal. `audit_mating.py` M4
  still fails an A7–B17 join.
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
