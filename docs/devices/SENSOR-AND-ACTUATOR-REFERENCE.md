# Sensor and actuator reference

Confirmed device facts for this build — part numbers, calibrations, pinouts and supply
requirements, each traced to a real receipt, product page, factory manual or hands-on
source. Reference material, not a work order.

Channel and pin assignments are **not** here: `XTREMEX-IO-TABLE.html` is the source of
truth for those. This file covers what each device *is* and what it needs.

---

## E-throttle / DBW

**Throttle body — Bosch, 74.5mm.** Anything in the repo saying 74mm or 3S-GTE is wrong.

6-pin TB connector: Motor−, Pot− (shared ground), Pot+ (shared 5V), Motor+, Pot2 signal,
Pot1 signal. The two TPS tracks run in opposite directions and sum to ≈5V — that sum is
the redundancy check.

**BRZ pedal — Subaru 36010CA110, 6-pin Sumitomo TS025.** Each track has its **own** 5V and
ground, the opposite of the throttle body, which shares. Looking into the 6-way with the
locking tab up:

| Pin | Name | Channel |
|---|---|---|
| 1 | VC2 +5V (sub) | — |
| 2 | GND2 | — |
| 3 | VPA2 APS-S | An Volt 5 **B33** |
| 4 | VC1 +5V (main) | — |
| 5 | GND1 | — |
| 6 | VPA1 APS-M | An Volt 4 **A14** |

All six pins live in the **Signal** file, supplies included, per
`docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.11. (An earlier revision put pins
1/2/4/5 in Power; that was reversed.)

Pin 6 is the full-range track. If the sub track saturates before full pedal travel, that
percentage must go into PCLink's `APS (Sub) 100%` — otherwise the ECU throws a permanent
fault and limits the engine to roughly 1800 rpm. Establish the figure by probing both
tracks across full travel before final wiring.

**V-Ethrottle relay:** pin 30 = fused battery, pin 85 = Aux 2 (the ECU grounds it to close
the relay), pin 86 = ignition-switched 12V, pin 87 → the ECU's V-Ethrottle pin. Matches
Link's own published diagram (Adamw, Link forum moderator).

Note the throttle body itself has **no power input** — six pins, listed above. The relay
feeds the ECU's V-Ethrottle pin; the ECU's internal H-bridge drives the motor via Aux 9/10.

---

## A/C circuit

- The ECU does **not** need an "AC on" status input to kill the compressor. A status input
  only enables proactive idle-up, which this build accepts going without.
- The kill signal goes to the amplifier's **ACT** terminal. **Ground = kill, floating = AC
  runs normally** (~9-14V passive pull-up). Confirmed by two independent hands-on 3S-GTE
  installers and cross-checked against a same-generation Toyota factory voltage table.
- **AC1 is a separate, input-only terminal** — it reads clutch operating voltage for
  idle-up, 8-14V when engaged, and cannot be used to kill. Confirmed against the 1990 ST185
  factory wiring manual. Deliberately excluded from this build; do not reintroduce it.

---

## Sensors — part numbers and calibration

| Device | Part | Calibration / notes |
|---|---|---|
| MAP | Lowdoller 899005, 5-bar | 0.5V = −14.5 psi, 4.5V = 58 psi |
| Fuel + oil pressure | Lowdoller 7990150 ×2 | 0-150 psi, 0.5V = 0, 4.5V = 150 |
| Coolant pressure | Ronybuy 150 psi | Same linear scaling, tolerates 5-16 VDC |
| Fluid / oil temp | Lowdoller 153299 (Racepak 810-TR-300 equivalent) | 32°F = 1630Ω … 302°F = 4476Ω; PCLink likely has a matching preset |
| Fuel level | OEM ST185 resistive float | 3Ω full / 110Ω empty — **needs an external pull-up**, on an An Volt channel, not a Temp channel |
| Turbo speed | BorgWarner 179430 | Pin 1 = signal 0-5V, pin 2 = ground, pin 3 = +5V |
| Crank | DNA Motoring OEM-SS-112 | The actual Toyota crank reluctor, 2-wire passive |
| Wheel speed ×4 | Camry / RAV4 / Highlander-family reluctors | 2-wire, therefore passive — an active Hall needs three |
| Flex fuel | Continental generic 3-pin | Ethanol % and fuel temp on one signal; there is no separate fuel temp sensor. Mounted on the fuel **return** line |
| ECT | Single sensor, water neck outlet | Part number not confirmed |
| Manifold IAT + charge-pipe IAT2 | Same GM-style NTC, bought as a pair | Both stay in the engine harness |
| Bosch 0261230340 | Combo pressure + temp | **Spare only.** If used, its temp side goes on Temp 1 or 2, never Temp 3/4 — a real installer confirmed it misreads on the fixed 1k pull-up |
| Headlight dim trigger | AGmi, to cluster GPIO | `CONFIG_TC_HEADLIGHT_GPIO`, direct wire — not CAN, not an ECU pin. Needs a relay or optocoupler; do **not** feed +12V straight to that pin |

**Remote sensor block.** MAP, fuel pressure and oil pressure sensor bodies all mount on a
block on the **driver side** of the firewall. Pressure taps stay at the actual source —
manifold, FPR, OEM head port — with short lines running to the block. Bulkheads A and B are
on the passenger side, so these four runs cross the bay; route them as one group.

**Temp channel hardware.** Temp 1 and 2 have a selectable pull-up, or none, set in software
in PCLink. Temp 3 and 4 carry a **fixed 1 kΩ** pull-up that cannot be adjusted. Confirmed in
the XtremeX-specific quickstart guide, not the StormX one.

---

## Cam sensor — settled

Racer X kit, Cherry/ZF GS1007 Hall, single tooth.

- **Supply: the ECU's +8V Out.** Not switched 12V.
- **Pull-up: 1.8 kΩ**, bought separately. The ZF datasheet maps resistor to supply
  (1k @ 5V, 1.8k @ 9V, 2.4k @ 12V); 8V interpolates to about 1.6k, and 1.8k is the
  nearest standard value. The 2.4 kΩ the kit ships is sized for 12V and is not used.
- Wiring: Brown = VCC (+8V), Black = signal to Trigger 2, Blue = ground (Gnd Out, not
  chassis). Shielded, terminated at the ECU end only.
- Needs a connector — the kit pigtail is a placeholder. Still to be chosen.

## Fuel pump and radiator fan — governed by the power rule

Not an open fork. Section 6.2 of `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` decides
it: a load is fed **either** from a PDM output **or** from a relay and fuse, never both.
Any load above the PDM's per-output capacity takes a relay and fuse instead, and where the
PDM is still the right source for a large load, outputs are combined — the fuel pump being
the likely case.

The lookup is done. ECUMaster **PMU-16**: 10 × 25 A and 6 × 15 A high-side, 150 A total;
same-rating outputs may be paralleled (max three → 75 A). Connector terminals are the
real limit. Applied in `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`:

- Fuel pump stays on cabin relay `k_fp` (Power file).
- Both uprated fans stay on `k_fan` / `k_fan2` (peak current above one 25 A pin).
- EPS stays on `k_eps` HCR 150 / F7 60 A.
- PMU-16 takes HEAD LH/RH, HAZ-HORN, DOME and RTR at the vacated J/B No.2 cavities, plus
  the rest of body / lighting and the small engine accessories (ECU main, O2 heater,
  boost solenoid, purge). Scope settled 2026-09-17 — see
  `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.2.1 for the full split and the
  verified PMU-16 spec.

When the PMU is fitted it is a CAN 1 node at 1 Mbit/s — add it to `WIRING.md` and
`CAN-BUS-MASTER-DESIGN.md` in the same change that lands it on the car, and do
**not** add a third 120 Ω terminator.
