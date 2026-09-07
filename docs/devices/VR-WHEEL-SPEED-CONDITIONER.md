# VR wheel-speed conditioner — 4 channels, two dual boards

Four ABS reluctor sensors feed DI 3–6 on the Link G4X XtremeX. A bare reluctor
sensor produces a sine wave whose amplitude falls with wheel speed, and the
ECU's digital inputs arm at a fixed hardware threshold of roughly 1.5–1.8 V.
Below about 20–24 km/h the sensors go dead, which is exactly the speed range
traction control needs most. A conditioner turns each sine wave into a clean
5 V square wave that stays valid down to walking pace.

Two dual-channel boards cover all four wheels.

---

## Purchased — settled 2026-09-06

**2 × Dual VR Conditioner (NCV1124), Speeduino compatible** — $24.99 each, order #11139.
Four channels total, one board per axle. No build required; this section is kept only
so the choice is traceable.

### Why the NCV1124 is the better chip here

The board uses an **ON Semiconductor NCV1124**, not the MAX9926 originally specced.
That swap is an improvement for this application:

| | NCV1124 | MAX9926 |
|---|---|---|
| Input threshold | **±160 mV typical** (135–185 mV), fixed, set by an internal reference | Adaptive peak threshold |
| Channels | 2 | 2 |
| Supply | 5 V (4.5–5.5 V) | 5 V |
| Input clamps | ±250 V on the sensor side with 22 kΩ series resistors | lower |
| Max frequency | 1.8 MHz, 680 kHz with clamps active | lower |

The number that matters is the threshold. The ECU's digital input arms somewhere
around **1.5–1.8 V**; the NCV1124 arms at **0.16 V**. That is roughly a tenfold
improvement in sensitivity, which is precisely the low-speed dropout being solved.

Adaptive thresholding is the MAX9926's advantage, and it matters most on crank and
cam signals where amplitude swings hugely between cranking and redline. For wheel
speed a fixed low threshold is the simpler and more predictable answer.

### Setup notes for these boards

- **Supply 5 V**, from the external supply, not the ECU's A32.
- **Ground the board to ECU sensor ground (Gnd Out, A24 or B22)**, not chassis.
  A chassis ground reintroduces the offset the differential input exists to reject.
- **Series input resistors are 22 kΩ** on the NCV1124 reference design, which is what
  gives the ±250 V clamp headroom. The Speeduino boards ship with these fitted.
- **Hold the `DIAG` pin low** for normal running. Pulling it high moves the negative
  threshold positive — that is the open-sensor diagnostic mode, not a run mode.
- Sensor pairs run as **shielded twisted pair**, shield terminated at the ECU end only.

## Wiring into the car

| Conditioner | Goes to | ECU pin |
|---|---|---|
| Channel 1 out | Wheel speed FL | DI 3 · A23 |
| Channel 2 out | Wheel speed FR | DI 4 · B21 |
| Channel 3 out | Wheel speed RL | DI 5 · B20 |
| Channel 4 out | Wheel speed RR | DI 6 · B19 |
| 5 V in | External 5 V supply | not the ECU's A32 |
| Ground | ECU sensor ground | Gnd Out · A24 or B22 |

Grounding the conditioner to **sensor ground rather than chassis** keeps the
reference identical to the ECU's own input reference. A chassis ground here
reintroduces exactly the offset the differential input exists to reject.

In PCLink, each DI becomes a frequency input. The conditioner output is a
clean square wave, so the arming threshold problem disappears — set the input
to digital/frequency and calibrate pulses per revolution from the tone ring
tooth count.
