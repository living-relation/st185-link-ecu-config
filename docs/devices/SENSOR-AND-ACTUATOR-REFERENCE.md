# Sensor and actuator reference

This file is the source of truth for the devices and sensors Daniel owns. For each
device it owns only that device's own pins: the pin, the pin's name, and whether
that device gets a shield. Those device pin names are fixed because they belong
to the device, and they are what the ECU end has to mate to. Which ECU pin a
device wire lands on is owned by the ECU, from the Link ECU documentation and the
XtremeX quick install manual (`sot/channels.csv`).

Unknown device pins are left blank. Do not invent a pinout or a part number.
A new device is Shield: no unless Daniel has already said that device has a
shield. Do not set a new device to yes or blank. Do not change a shield flag
he already set.

The only center-cluster portion in this repo is the CAN node, plus power and
ground to the cluster. Interior cluster wiring lives only in the center
cluster repo. Do not add interior cluster circuits here.

A device or sensor gets one shield flag. Do not mark a shield on a pin or a
wire.

Anything in the source of truth that has a shield must not use individual
wires. It must use a multi-conductor Tefzel Raychem cable.

Confirmed part numbers, calibrations and supply requirements stay here as
reference, each traced to a receipt, product page, factory manual or hands-on
source.

---

## E-throttle / DBW

**Throttle body — Bosch, 74.5mm.** Anything in the repo saying 74mm or 3S-GTE is wrong.

6-pin TB connector. The two TPS tracks run in opposite directions and sum to ≈5V — that
sum is the redundancy check.

Shield: yes

| Pin | Name |
|---|---|
| 1 | Motor (−) |
| 2 | TPS (−) |
| 3 | TPS (5V+) |
| 4 | Motor (+) |
| 5 | TPS 2 (out) |
| 6 | TPS 1 (out) |

**BRZ pedal — Subaru 36010CA110, 6-pin Sumitomo TS025.** Each track has its **own** 5V and
ground, the opposite of the throttle body, which shares. Looking into the 6-way with the
locking tab up:

Shield: yes

| Pin | Name |
|---|---|
| 1 | VC2 +5V (sub) |
| 2 | GND2 |
| 3 | VPA2 APS-S |
| 4 | VC1 +5V (main) |
| 5 | GND1 |
| 6 | VPA1 APS-M |

All six pins are one connector on `AB-cabin`, supplies included (`docs/harness/MASTER-wirelist.csv`).

Pin 6 is the full-range track. If the sub track saturates before full pedal travel, that
percentage must go into PCLink's `APS (Sub) 100%` — otherwise the ECU throws a permanent
fault and limits the engine to roughly 1800 rpm. Establish the figure by probing both
tracks across full travel before final wiring.

**V-Ethrottle relay:**

The V-throttle relay is allowed in the device source of truth. It feeds
power into the ECU to power the e-throttle body circuit.

Shield: no

| Pin | Name |
|---|---|
| 30 | fused battery |
| 85 | ECU active low |
| 86 | ignition-switched 12V |
| 87 | load output |

Matches Link's own published diagram (Adamw, Link forum moderator).

Note the throttle body itself has **no power input** — six pins, listed above. The relay
feeds the ECU's V-Ethrottle pin; the ECU's internal H-bridge drives the motor via Aux 9/10.

---

## Sensors — part numbers, calibration, and device pins

| Device | Part | Calibration / notes |
|---|---|---|
| MAP | Lowdoller 899005, 5-bar | 0.5V = −14.5 psi, 4.5V = 58 psi |
| Fuel + oil pressure | Lowdoller 7990150 ×2 | 0-150 psi, 0.5V = 0, 4.5V = 150 |
| Coolant pressure | Ronybuy 150 psi | Same linear scaling, tolerates 5-16 VDC |
| Fluid / oil temp | Lowdoller 153299 (Racepak 810-TR-300 equivalent) | 32°F = 1630Ω … 302°F = 4476Ω; PCLink likely has a matching preset |
| Fuel level | OEM ST185 resistive float | 3Ω full / 31.6Ω half / 110Ω empty (FSM; the half point is from the ST205 supplement, measure the real sender) — **needs an external pull-up** (470Ω to +5V gives 0.032 / 0.315 / 0.948 V), on an An Volt channel, not a Temp channel; PCLink 3-point table in DECISIONS S23 |
| Turbo speed | BorgWarner 179430 | See pin table |
| Crank | DNA Motoring OEM-SS-112 | The actual Toyota crank reluctor, 2-wire passive |
| Wheel speed ×4 | Camry / RAV4 / Highlander-family reluctors | 2-wire, therefore passive — an active Hall needs three |
| Flex fuel | Continental generic 3-pin | Ethanol % and fuel temp on one signal; there is no separate fuel temp sensor. Mounted on the fuel **return** line |
| ECT | Single sensor, water neck outlet | Part number not confirmed |
| Manifold IAT + charge-pipe IAT2 | Same GM-style NTC, bought as a pair | Both stay in the engine harness |
| Bosch 0261230340 | Combo pressure + temp | **Spare only.** If used, its temp side goes on Temp 1 or 2, never Temp 3/4 — a real installer confirmed it misreads on the fixed 1k pull-up |

**Turbo speed — BorgWarner 179430**

Connector face, left to right. Pin numbers are not on the photo.

Shield: yes

| Pin | Name |
|---|---|
|  | 0-5V Signal |
|  | Ground |
|  | +5V Supply |

**Crank — DNA Motoring OEM-SS-112**

Two-wire passive reluctor. Pin numbers are not in this repo.

Shield: yes

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

**Wheel speed ×4**

Four ABS reluctors. Each is signal and ground. Each sensor gets one
shield. That shield terminates on the VRC connector. Pin numbers are not
in this repo.

Shield: yes

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

**Flex fuel — Continental generic 3-pin**

Syltech pinout.

Shield: yes

| Pin | Name |
|---|---|
| A | VCC 12VDC |
| B | GND signal ground |
| C | Vout sensor output |

**Gearbox VSS — Toyota 83181-20040** (1991-97 Land Cruiser FZJ80 / Previa speedometer
sensor, 3 blade pins). Mate = Toyota 90980-11143 oval 3-pin socket plug, Sumitomo TS 090
sockets.

Shield: yes

| Pin | Name |
|---|---|
| 1 | IG +12V switched |
| 2 | ground |
| 3 | SP1 speed output |

**MAP — Lowdoller 899005**

Shield: no

| Pin | Name |
|---|---|
| 1 | low reference/ground |
| 2 | 5V |
| 3 | signal |

**Fuel pressure — Lowdoller 7990150**

Same pinout as MAP.

Shield: no

| Pin | Name |
|---|---|
| 1 | low reference/ground |
| 2 | 5V |
| 3 | signal |

**Oil pressure — Lowdoller 7990150**

Same pinout as MAP and fuel pressure.

Shield: no

| Pin | Name |
|---|---|
| 1 | low reference/ground |
| 2 | 5V |
| 3 | signal |

**Coolant pressure — Ronybuy 150 psi**

Shield: no

Comes with its own pigtail (Dan owns it): a 3-way plug on the sensor, bare leads on the other end; the harness
solder-splices to the leads. Plug pin numbers and colours from the seller's connection guide (Dan 2026-10-30).

| Pin | Plug pin | Name | Pigtail lead |
|---|---|---|---|
| A | 1 | GND | black |
| B | 2 | Supply + | red |
| C | 3 | Output | green |

**Oil temp — Lowdoller 153299**

Two pins. Pin numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

**Fuel level — OEM ST185**

Two pins. Pin numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

**ECT**

Two pins. Pin numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

**Manifold IAT**

Two pins. Pin numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

**Charge-pipe IAT2**

Two pins. Pin numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | signal |
|  | ground |

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
- Connector (Dan 2026-10-29): the sensor's bare leads get a DT04-3P + W3P + 0460-202-16141 pins; the harness
  side is DT06-3S-CE05 + W3S + 0462-201-16141. The pins take 16-20 AWG; the GS100701 leads are 20 AWG x 1 m (ZF datasheet
  GS1005-GS1007, 2024-09-11, in Dan's Drive), so they fit.

Pins are the DT cavity numbers (moulded on the housing); lead colours from Dan's sensor sheet.

Shield: yes

| Pin | Name | Sensor lead |
|---|---|---|
| 1 | +8V | brown |
| 2 | signal | black |
| 3 | ground | blue |

**Knock**

Two pins. Pin numbers are not in this repo.

Shield: yes

| Pin | Name |
|---|---|
|  | SIG+ |
|  | SIG- |

## MR-S (ZZW30) EHPS power steering pump - settled 2026-09-17

Confirmed from Daniel's photos of the actual pump. The EPS control module is **bolted to
the pump itself**, so everything below lives in the engine bay.

### Three connectors

| Ours | On the pump | Cavities | Part number | Used |
|---|---|---:|---|---|
| `mrs_pwr` | **A** - main power | 2 | `90980-12068` | 1 = +12 V from `k_eps`, 2 = GND to block |
| `mrs_ctrl` | **B** - signal | **6** | *not yet identified* | 2 = speed pulse in; 5 = switches `k_eps` coil- (R22); the rest unused |
| `mrs_en` | **C** - ignition | 2 | `90980-10942` | 1 = switched 12 V (7.5 A ign fuse), 2 unused |

No shields on the MRS.

**`mrs_ctrl` is a 6-way, not a 3-way.** The diagrams draw only the wired pins. Draw all six
and mark the spares unused - that is what the "3 vs 6 cavities" note was about. Its part
number is still unidentified; `90980-*` family, to confirm.

### Relay placement

**Changed 2026-09-28 (Daniel): every relay is in the cabin.** `k_eps` (HCR 150) now sits
in the glove box beside the POWER box (DECISIONS R75; was HCFB, then the LMI), drawn on `ST185-CabinPower`. The coil wires and the POWER AMI OUT-6 EPS feed (was LMI L7, HCFB H4) are cabin wires; the pump feed from
contact 87 runs point-to-point on loom C through the firewall (no bulkhead), like the fan
feeds. This replaces the 2026-09-17 "engine bay, next to the pump" placement.

**Sized 2026-09-28:** Bussmann AMI-60 (60 A) at POWER AMI OUT-6 (was LMI L7, HCFB H4) and 8 AWG feed. Pump draw: about 4 A idle and under 40 A at full load on a stock pump (honda-tech 'EHPS Redone' write-up; diyelectriccar MR2 EHPS wiki), 70-80 A at maximum load on raised-pressure pumps (Alaria Tech FAQ); factory MR-S EHPS fuse 50 A (2002 MR2 EWD element list). Bussmann AMI time-current (Cooper Bussmann AMI series data sheet): 100% >= 100 h, 110% >= 4 h, 150% 90-3600 s, 200% 5-100 s - an 80 A peak is 133% of 60 A, so it holds well over 90 s, longer than any full-lock burst. Wire: 8 AWG 150 C single wire in free air 76 A (Thermal Wire and Cable ampacity table, AS50881 method) >= 60 A, so the fuse protects the wire; 10 AWG (55 A) would not. The HCR 150's own rating:  130 A at 85 C
with a 25 mm2 load cable (TE datasheet V23132-X0000-A001). The longer heavy run from the
glove box to the pump also makes voltage drop a sizing input once the current is known.

**Two relays (DECISIONS R22, Daniel 2026-10-04; drawn 2026-10-12).** `k_eps` (HCR 150) carries
the pump feed: coil+ = 12 V ignition (`sp_sw12`), coil- switched to ground by the pump's own pin
B5 (net `MRS_RLY`, glove box -> `ST185-ECU-cabin` -> bulkhead -> `ST185-ECU-engine` ->
`ST185-EngineRoom-C`). `k_eps_en` (TE `6-1419137-4` micro relay in LOGIC box M21, fed by
LOGIC EPSEN 7.5 A) is the ECU's enable: Link Ign 6 (B12) sinks its coil-, its 87 feeds the LOGIC
MRS 7.5 A fuse -> pump C1. So the ECU switches the pump on, and the pump switches its own main
relay. Ign 6 runs on above ~400 rpm with a 1-2 s off-delay (setup time, R52). Older text named
connector B pin 6 "relay request out"; R22 names B5 - see `docs/OPEN-ITEMS.md`.

### Speed signal - it is an ECU output

`Aux 7 / A27` generates the SPD pulse train **to** the pump (~4 pulses/rev, 0-5 V). It is
not an input and carries no load information. Aux 5-8 already have an internal ~1.5 kOhm
pull-up, so **no external pull-up goes on this line until the high level has been scoped**
(see `XTREMEX-IO-TABLE.html`). Remove any pull-up drawn on it in the meantime.

### Idle-up for pump current draw - settled 2026-09-17

Pump current follows **steering effort, not road speed**: stopped-and-straight is a light
load, stopped-and-turning is the 60-80 A case. Plain inverse-VSS therefore raises idle at
every traffic light for nothing and does nothing during a fast corner. The strategy is:

1. **Measure the current.** Hall-effect sensor (ACS758 class, 0-5 V ratiometric) on the
   pump's 12 V feed into a spare **An Volt** input - `B31` or `B32` are free. Feed idle-up
   forward from measured amps. Also gives pump diagnostics and a CAN log channel.
2. **System-voltage droop idle-up** as the backstop. No hardware; catches every large load,
   not just the pump.
3. **Inverse-VSS is demoted to a gate**, not a trigger: idle-up only when speed is below
   roughly 5 km/h **and** (1) or (2) says the pump is actually pulling.

**Test before fitting the sensor.** The build is drive-by-wire and Link closed-loop idle on
an e-throttle absorbs load well. Once the car runs: idle it, log RPM, turn lock to lock.
Under roughly 100 rpm dip, fit nothing. Large dip or hunting, fit the current sensor.

Confirm the exact PCLink setting names against the **G4X Help built into PCLink** (F1) -
Link's online help was not reachable when this was written, and Link documentation
outranks this note.

If one of `mrs_ctrl`'s four unused pins turns out to be a load or fault output, that
replaces the current sensor for the price of one wire. Worth metering before buying.

## Cam sensor resistor - drawn wrong, fix before building

The component the diagrams call `r_cam` is a **1.8 kOhm resistor** for the cam position
sensor, currently placed at the sensor in the engine bay. Rename it to `cam_pullup`,
label "Cam sensor pull-up 1.8k".

**What it is for.** The cam sensor is a Hall-effect type running on 8 V. Its output does
not drive the line high - it only pulls the line down to ground. Left alone the line floats
between pulses and the ECU sees noise. A pull-up resistor ties the signal line to the 8 V
rail so it rests high, and every time the sensor switches it yanks the line low. That gives
the clean square edge the trigger input needs.

**The fault.** It is drawn in **series** with the signal, not pulling it up:

```
   drawn now:   cam.c2 --[1.8k]-- bh_eng.c32 == bh_fw.c32 -- ecu_a.a9 (Trig 2)
```

A9 is Trigger 2. So the resistor sits directly in the cam trigger path, where it attenuates
and slows the edge instead of conditioning it. That is the opposite of the intent.

**Correct arrangement** - the resistor bridges the 8 V rail to the signal line, and the
signal runs straight through:

```
   ECU 8V Out (A6) --[1.8k]--+
                             |
   cam signal ---------------+------------- ECU Trig 2 (A9)
   (sensor sinks this to ground)
```

**Put it on the ECU side**, in the cabin. Three reasons: it is out of engine-bay heat and
vibration; the value is easy to change on the bench while setting the trigger up; and it
needs no bulkhead pins of its own - 8 V already crosses on bulkhead A pin 4 for the
sensor's supply, and the cam signal already crosses on pin 32. Nothing new is added.

`r_fuellvl` (470 Ohm) and `r_cruise` (1k, DECISIONS S23; drawn 2026-10-14) are wired correctly as pull-ups to A32 and do
not need this change - only the cam one is wrong.

## VR conditioner (NCV1124 dual boards)

Write-up: `docs/devices/VR-WHEEL-SPEED-CONDITIONER.md`. Pins below are the
conditioner's own cavities from `sot/channels.csv` and `docs/harness/redesign/DECISIONS.md`.

Shield: yes

The VRC output cable is shielded, the same as the input. This is not a
shell-only shield. The drain is connected on both the VRC input and the
VRC output. The ABS input drains splice together and terminate on a
single pin. Each ABS sensor shield terminates on the VRC connector.

**Each IN connector (Front L, Front R, Rear L, Rear R)**

| Pin | Name |
|---|---|
| + | sensor + |
| − | sensor − |
| 3 | screen |

**Front OUT**

| Pin | Name |
|---|---|
| +5V | conditioner supply |
| Gnd | conditioner ground |
| FL | conditioned FL |
| FR | conditioned FR |

**Rear OUT**

| Pin | Name |
|---|---|
| +5V | conditioner supply |
| Gnd | conditioner ground |
| RL | conditioned RL |
| RR | conditioned RR |

## Wheel-speed sensors - their own loom, settled 2026-09-17

All four VR wheel-speed sensors and both dual-channel conditioner boards come out of looms
A and B into `ST185-WheelSpeed-Front.harness`. **No bulkhead connector** - this loom does not
cross bulkhead A or B, so the front sensors stop being firewall crossings with nowhere to
cross. Its only ties to the rest of the car are the conditioner outputs to the ECU and the
conditioner power and ground, which follow the shared-part rule in plan doc 6.15.

---

## Engine actuators on the ECU

Engine devices whose wires go directly to the ECU. Pin numbers are omitted
where this repo has no confirmed device pinout. ECU landings stay in
`sot/channels.csv`.

**Boost solenoid**

Two pins. Pin numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | battery plus |
|  | ECU active low |

**Link CAN-Lambda**

External wideband controller for a Bosch LSU 4.9. On CAN bus 1. Link pinout
for the CAN pair is recorded in `docs/harness/redesign/DECISIONS.md` B1. The
other two wires are +12V and ground; those pin numbers are not confirmed here.
The controller stays in the engine bay; its CAN and power run through bulkhead B,
shielded the whole run (Daniel, 2026-10-03).

Shield: yes

| Pin | Name |
|---|---|
|  | +12V |
|  | ground |
| 3 | CAN L |
| 4 | CAN H |

**Injectors ×4**

1400 cc high-Z sequential. Each injector is two pins. Pin numbers are not
in this repo. No part number recorded.

Shield: no

| Pin | Name |
|---|---|
|  | 12V |
|  | ECU active low |

**1ZZ COP ×4**

Smart coil-on-plug. The ECU drives the logic-level IGT input only. Pin
numbers are not in this repo.

Shield: no

| Pin | Name |
|---|---|
|  | +B |
|  | IGT |
|  | ground |

**CAN bus - every run between nodes**

The CAN H / CAN L pair between every node on CAN bus 1 (ECU, center cluster,
CSB3, Pi / RealDash adapter, CAN-Lambda) is shielded on every run (Daniel,
2026-10-03). The pair is drawn once, in `ST185-CAN.harness`.

Shield: yes

| Pin | Name |
|---|---|
|  | CAN H |
|  | CAN L |
