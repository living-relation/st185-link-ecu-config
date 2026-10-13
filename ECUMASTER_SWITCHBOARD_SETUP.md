# ECUMaster CAN Switch Board V3 — Configuration Guide
## ST185 TrackCluster Build

### Overview

The ECUMaster CAN Switch Board V3 (CSB3) connects analog sensors, rotary encoders, and digital switches to the CAN bus. The ECU also sends low-side (ground-switching) output commands back to the CSB3 via ID 0x643.

**Critical:** The CSB3 ships at **500 kbps**. Our bus runs at **1 Mbit/s**. A 500 kbps device on a 1 Mbit/s bus will corrupt every frame. Change the speed BEFORE connecting to any other node.

---

## Step 1 — Software & Hardware Required

- ECUMaster **CAN Switch Board Configurator** — download from ecumaster.com (free)
- Windows 10/11 x64
- USB cable to the CSB3 (the CSB3 V3 has a micro-USB config port — confirm on your specific unit)
- OR a USB-to-CAN adapter if your unit configures over CAN

Confirm you have the **V3** manual — V1/V2 used different software.

---

## Step 2 — Change CAN Bus Speed (Do This First, Before Connecting to Car)

1. Open ECUMaster CSB Configurator. Power the CSB3 via USB or 12V supply.
2. Connect USB. Let the configurator detect the device.
3. Go to **Device Settings** (or **CAN Settings**) tab.
4. Change **CAN Baud Rate** from `500 kbps` → `1000 kbps` (1 Mbit/s).
5. Click **Write to Device** / **Apply** / **Save**.
6. Power-cycle the CSB3 (unplug and replug power).
7. Reconnect in the configurator — verify it now shows **1000 kbps**.

**Bench verification (optional but recommended):**
Connect CSB3 to a USB-CAN adapter (also at 1 Mbit/s). Open a CAN monitor (SavvyCAN, PCAN-View, or similar). Confirm frames appear on IDs **0x640**, **0x641**, **0x642** at ~20 Hz.

---

## Step 3 — Confirm Base CAN ID = 0x640

Our allocation table uses Base ID **0x640**. The CSB3 generates:

| Frame ID | Description |
|---|---|
| 0x640 | Analog Inputs 1–4 (uint16 mV × 4) |
| 0x641 | Analog Inputs 5–8 (uint16 mV × 4) |
| 0x642 | Rotary encoders, switch states, heartbeat |
| 0x643 | ECU → CSB3 low-side commands (CSB3 receives this) |

In the configurator, check **Base CAN ID** under Device Settings. If not 0x640 (1600 decimal), change it. Write and power-cycle.

---

## Step 4 — Analog Input Assignments

Each analog channel outputs raw mV (0–5000), uint16, BigEndian, at ~20 Hz.

| CSB3 Analog Input | CAN Frame | Byte Offset | Connected Signal | Notes |
|---|---|---|---|---|
| Analog 1 | 0x640 | bytes 0-1 | Unassigned (brought out, spare) | Was cabin temp; A/C is the OEM amplifier's (2026-09-27) |
| Analog 2 | 0x640 | bytes 2-3 | OEM cruise control stalk (C14 pin 5 resistor ladder, 1 kohm pull-up to +5V) | See Step 4.1 |
| Analog 3 | 0x640 | bytes 4-5 | TBD | |
| Analog 4 | 0x640 | bytes 6-7 | TBD | |
| Analog 5 | 0x641 | bytes 0-1 | TBD | |
| Analog 6–8 | 0x641 | bytes 2-7 | TBD | |

**In the configurator:** Set each active channel to:
- Input type: **Voltage (0–5V)**
- Output format: **Raw mV**, uint16, BigEndian
- Transmit rate: **20 Hz (50 ms)**

---

## Step 4.1 — OEM Cruise Control Stalk (Resistor Ladder + MAIN)

Settled from the factory manual 2026-10-13 (`docs/harness/redesign/DECISIONS.md` R66, S23). All OEM stalk
functions are kept: MAIN on/off, SET/COAST, RES/ACC, CANCEL. (Earlier text called these SET/ACCEL and
RESUME/DECEL - backwards. Holding SET/COAST decelerates, holding RES/ACC accelerates.)

### What the stalk really is

The stalk is connector **C14** of the combination switch. It has three wires (1990 ST185 EWD p.116, book p.118;
1992 Celica EWD132U p.180 has the same pins):

| C14 pin | Colour | Function | Goes to |
|---|---|---|---|
| 5 | W (white) | Control ladder: a resistor to ground per position | CSB3 **A2** (`FL_CRUISE_STALK_C1`) |
| 15 | Y-B (yellow / black) | MAIN on/off: a contact to the pin 17 ground when ON | CSB3 **S3** (`FL_CRUISE_STALK_C3`) |
| 17 | BR (brown) | Switch ground (OEM: body ground IE) | CSB3 ground (a ground lead replaces the old C4 lead) |

Ladder resistance to ground (1993 Mitchell Electrical p.98-99, switch test): OFF open, **RES/ACC about 68 ohm,
SET/COAST about 198 ohm, CANCEL about 418 ohm**. There are no separate SET or RESUME wires, so CSB3 S4 / S5
are not used. A car with an SRS column uses the same three wires on a 6-pin slip ring as pins 4 W / 5 Y-B / 3 BR
(Mitchell); R14 says this car has no SRS, so use 5 / 15 / 17 and check the car's connector before soldering.

The OEM cruise ECU is bypassed. The Link G4X cruise strategy does the control; its brake and clutch cancels
come from CSB3 S7 / S6 and the speed from the ECU.

### Pull-up for A2

The OEM cruise ECU supplied the reference. Here a resistor from +5V (ECU A32, via `r_cruise` in `ST185-CSB3`)
to the A2 junction forms the divider with the ladder. **Use 1 kohm, not 10 kohm.** A 10 kohm pull-up gives only
34 / 98 / 400 mV, which a small ground offset between the stalk ground and the CSB3 ground would swamp.

| Position | Ladder (ohm) | A2 with 1 kohm (mV) | A2 with 10 kohm (mV) |
|---|---|---|---|
| none (open) | open | 5000 | 5000 |
| RES/ACC | 68 | 318 | 34 |
| SET/COAST | 198 | 827 | 98 |
| CANCEL | 418 | 1474 | 400 |

Current through the 1 kohm is at most 5 mA, so the A32 +5V budget (OPEN-ITEMS row 69) is untouched. These are
the Toyota nominal values ("approx."); measure the real stalk and tune the bands at setup. The CSB3 analog
input impedance is not in the repo - check it in the CSB3 manual, since it loads the divider.

### Decoding - raw mV in PCLink (Option B, chosen)

The CSB3 manual v2.1 says AS_MASK is one fixed 2 V / 3 V threshold per input, so it cannot split one ladder
into three states. Option A (AS_MASK) is therefore not used.

1. Analog 2 -> CSB3 -> 0x640 bytes 2-3 (raw mV, uint16, BigEndian).
2. In PCLink receive it as a voltage channel ("Cruise Stalk mV") and decode with math channels. Starting bands,
   from the 1 kohm table above (midpoints between positions), to be tuned on the car:

   | mV | State |
   |---|---|
   | under 150 | fault (shorted ladder) |
   | 150 - 570 | RES/ACC |
   | 570 - 1150 | SET/COAST |
   | 1150 - 3200 | CANCEL |
   | over 3200 | none |

3. Map the decoded states to the Link cruise function inputs (SET/COAST, RES/ACC, CANCEL). Hold behaviour
   (hold SET/COAST = slow down, hold RES/ACC = speed up) is a setting of the Link cruise strategy.
4. MAIN is the CSB3 S3 input -> SW_MASK bit 2 -> VDI3 (Step 5). It is a contact to ground, so the CSB3 switch
   input has to see ground as ON; confirm the input polarity and pull in the CSB3 manual (not recorded in the
   repo). The OEM ECU also drops MAIN after an auto cancel until the ignition is cycled; set the same
   re-arm in the Link cruise strategy if wanted.

---

## Step 5 — Digital Switch Assignments (SW_MASK → 0x642 byte4)

The CSB3 packs digital input states into byte4 of 0x642 as a bitmask (SW_MASK).
PCLink reads this via a CAN User Stream: **0x642 byte4 bits0-4 → VDI1–VDI5**.

| SW_MASK Bit | Physical Signal | PCLink VDI | Function |
|---|---|---|---|
| bit0 (LSB) | Switch 1 — unassigned (was evap core) | VDI1 | — |
| bit1 | Switch 2 — unassigned (was A/C request) | VDI2 | — |
| bit2 | Switch 3 — cruise MAIN on (CSB3 c17, stalk pin 15) | VDI3 | Cruise master on/off |
| bit3 | Switch 4 — unassigned (was cruise SET; the stalk has no such wire) | VDI4 | — |
| bit4 | Switch 5 — unassigned (was cruise RESUME; the stalk has no such wire) | VDI5 | — |
| bit5–7 | Unused | — | Not read by PCLink |

**Setup time (Dan, Route 15 C14, 2026-10-13 - no config now):** the brake switch is wired to CSB3 **S7 = SW_MASK bit 6** and
reverse to **S8 = bit 7**, both through the inline optoisolator (`ST185-CSB3`, DECISIONS S17 / R56). PCLink needs a
CAN user-stream mapping for bit 6 (brake pressed) - and bit 7 if the ECU wants reverse - when the ECU is on the bench;
confirm then that the set bit means pressed / engaged. The CAN contract (`switchboard_frames.json`) is not changed until
that mapping is made (`docs/OPEN-ITEMS.md` setup-time row 91).

**Note:** SET/COAST, RES/ACC and CANCEL do not arrive on SW_MASK or AS_MASK: they are decoded in PCLink from the A2 raw mV (Step 4.1). SW_MASK bit 2 carries only MAIN.

In the configurator, map physical wires to digital input channels and confirm the bit ordering matches the table above.

**PCLink VDI failsafe:** If CSB3 comm is lost (PCLink timeout 200 ms), VDI1–VDI5 default to **0** (all off). This is safe — cruise cancels.

---

## Step 6 — Rotary Encoder Assignments (0x642 bytes 0–3)

Rotary positions are nibble-packed (4 bits each, 0–15 positions per encoder):

| 0x642 Byte | Upper Nibble [7:4] | Lower Nibble [3:0] |
|---|---|---|
| byte0 | Rotary 1 | Rotary 2 |
| byte1 | Rotary 3 | Rotary 4 |
| byte2 | Rotary 5 | Rotary 6 |
| byte3 | Rotary 7 | Rotary 8 |

Assign physical encoders in the configurator:
- **Rotary 1–8** → TBD — assign functions once hardware and use-case are confirmed
  (manual v2.1: rotaries are read from the analog inputs; R# = position of a rotary switch on analog input #)

**Routing note:** CSB3 rotary values (0x642 bytes 0-3) go to the **ECU only**. The ECU decides
what to do with them. The cluster does NOT read switchboard frames.

The cluster's own boost-map and TC-map encoder inputs come from its physical GPIO encoders
(center P4 GPIO 30/31/32 and 49/50/51) — those are separate knobs wired directly to the
cluster board. The cluster sends 0x3EC/0x3ED to the ECU based on those GPIO encoders.
The CSB3 rotary channels are a separate set of inputs available to the ECU for other functions.

---

## Step 7 — Low-Side Outputs (0x643 — CSB3 is the receiver)

The ECU commands CSB3 low-side outputs via ID 0x643, sent as a 50 ms periodic PCLink CAN TX stream (the
bytes only change when an output changes; the manual sets no required rate). The cluster does NOT
transmit 0x643. The ECU is the sole transmitter (decided 2026-06-14, `CAN-BUS-MASTER-DESIGN.md` §9).

Layout per the CSB3 manual v2.1 §6 (DLC ≥ 4, one **byte** per output, not bits) — same as
`switchboard_frames.json` and `CAN-BUS-ID-ALLOCATION-TABLE.md` §5:

| 0x643 Byte | CSB3 Output | Use |
|---|---|---|
| byte0 | L1 ctrl | Unused (LED-only if ever used) |
| byte1 | L2 ctrl | Unused (LED-only if ever used) |
| byte2 | L3 ctrl | Unused (LED-only if ever used) |
| byte3 | L4 ctrl | Unused (LED-only if ever used) |
| byte4–7 | — | Send 0x00 |

Each output is rated 0.5 A (manual §2). Nothing is assigned yet, so the PCLink 0x643 stream can wait;
when an LED is added, map its PCLink virtual output to the matching byte.

---

## Step 8 — Heartbeat (Automatic — No Config Needed)

0x642 byte7 is a rolling counter (0→255→0) that increments with every CSB3 transmission. The ECU monitors this automatically via the PCLink receive timeout setting.

- **PCLink timeout:** 200 ms on CAN User Streams 0x640 / 0x641 / 0x642
- **Fault action (automatic):** VDI1–5 reset to 0
- **Fault broadcast:** PCLink sets 0x3F1 byte6 bit5 ("Switchboard Comm Fault")

The CSB3 needs no configuration for the heartbeat. PCLink side: see `CANBUS-LINK-G4X-CONFIG.md` for the receive timeout setting.

---

## Step 9 — Termination (Critical)

Exactly two 120Ω termination resistors go on the bus — one at each physical end. **Settled
(2026-09-27): the two ends are the ECU and the Link CAN-Lambda**, as drawn in
`docs/harness/rebuild/ST185-CAN.harness` (`r_term_ecu`, `r_term_end`). See the topology bullets in
`CAN-BUS-MASTER-DESIGN.md` and `WIRING.md` §7.

| Node | Position | Termination |
|---|---|---|
| Link G4X XtremeX ECU | Bus end 1 | **ON** — 120Ω in the CAN harness at the ECU end |
| Link CAN-Lambda | Bus end 2 | **ON** — 120Ω in the CAN harness at the CAN-Lambda end |
| center-cluster-esp32-p4 | Mid-bus stub | **None** (SN65HVD230 has no termination) |
| ECUMaster CSB3 | Mid-bus stub | **Jumper OFF** — do not close onboard termination |
| Pi4+/Pi5 + USB-CAN adapter | Mid-bus stub | **None** — PCAN USB termination switch OFF; no inline resistor on a CANable |

**NOTE:** The Waveshare hat on the Pi is for cooling fan only — it has no CAN connections.

Bus topology (daisy chain, shortest stub lengths; stub order as drawn in `ST185-CAN.harness`):
```
[ECU end] ──── mid-bus stubs: cluster, CSB3, Pi/USB-CAN ──── [CAN-Lambda end]
   120Ω                                                          120Ω
```

If you need to bench-test the CSB3 alone on a short cable with a USB-CAN adapter, you can close the CSB3 termination jumper temporarily. **Remove it again before connecting to the full bus.**

---

## Final Verification Checklist

Before first power-on with ECU on the bus:

- [ ] CSB3 CAN speed confirmed **1000 kbps** in configurator
- [ ] Base ID confirmed **0x640**
- [ ] CSB3 termination jumper confirmed **OPEN (OFF)**
- [ ] SW_MASK bit 2 wired to the cruise MAIN switch (bits 0–1 and 3–4 unassigned); stalk ladder on A2 with a 1 kohm pull-up
- [ ] With CSB3 powered and isolated, 0x640 / 0x641 / 0x642 frames visible in CAN monitor at 1 Mbit/s
- [ ] In PCLink — CAN User Stream 0x642 byte4 bits 0-4 → VDI1-5 configured
- [ ] In PCLink — receive timeout 200 ms set for 0x640 / 0x641 / 0x642
- [ ] In PCLink — 0x643 TX stream (50 ms) only once an output is assigned (L1-L4 unused / LED-only for now)
