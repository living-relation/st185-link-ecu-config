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

## Unresolved device specs

Two device-level questions are genuinely open. They are recorded here because they are
facts about hardware, not tasks.

**Cam sensor supply — conflicting sources.** The Racer X kit (Cherry/ZF GS1007 Hall, single
tooth) ships a 2.4 kΩ pull-up and its instructions call that required. The ZF datasheet ties
resistor value to supply voltage: 1k @ 5V, 1.8k @ 9V, 2.4k @ 12V. So the shipped resistor
implies a 12V supply. Two viable routes:

- switched 12V with the 2.4 kΩ the kit supplies, or
- the ECU's **+8V Out** with a **1.8 kΩ** pull-up bought separately (~1.6k interpolated,
  1.8k being the nearest standard value).

Wiring is the same either way: Brown = VCC, Black = signal to Trigger 2, Blue = ground
(Gnd Out, not chassis). Shielded, terminated at the ECU end only. Decide before ordering.

**Fuel pump and radiator fan — PDM or direct Aux.** `XTREMEX-IO-TABLE.html` currently has
Aux 3 = fuel pump relay and Aux 5 = rad fan relay, wired direct. The PDM option discussed
earlier never made it into the design. Moving both to the PDM would free two Aux channels.
This is a design decision, not a lookup — and if it lands as yes, the PDM must also be added
as a node in `WIRING.md` and `CAN-BUS-MASTER-DESIGN.md`.
