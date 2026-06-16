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
| Analog 1 | 0x640 | bytes 0-1 | Cabin temp NTC thermistor | PCLink maps this to GP Temp1 via calibration table |
| Analog 2 | 0x640 | bytes 2-3 | OEM cruise control stalk (resistor ladder signal) | See Step 4.1 |
| Analog 3 | 0x640 | bytes 4-5 | TBD | |
| Analog 4 | 0x640 | bytes 6-7 | TBD | |
| Analog 5 | 0x641 | bytes 0-1 | TBD | |
| Analog 6–8 | 0x641 | bytes 2-7 | TBD | |

**In the configurator:** Set each active channel to:
- Input type: **Voltage (0–5V)**
- Output format: **Raw mV**, uint16, BigEndian
- Transmit rate: **20 Hz (50 ms)**

---

## Step 4.1 — OEM Cruise Control Stalk (Resistor Ladder)

### Background

The 1993 ST185 AllTrac cruise control stalk uses a **resistor ladder** — one signal wire that
outputs different voltages for each switch position (SET/ACCEL, COAST/DECEL, RESUME/ACCEL,
CANCEL). This is an analog signal, NOT a digital switch. It connects to a CSB3 **analog input**
(Analog 2), not a digital input.

The OEM cruise control ECU (C/C ECU) is bypassed entirely in this build. The Link G4X FuryX
handles cruise control natively via its own cruise control strategy once it receives the correct
switch inputs.

### What to look up in the ST185 electrical diagram

You need **two things** from the service manual (Electrical section, Cruise Control System):

1. **The signal wire** — which wire on the cruise stalk connector carries the resistor ladder
   voltage. Common colors in that era: blue/white, blue/yellow. Look for a wire that goes from
   the stalk to a "CRUISE CONTROL ECU" labeled connector, shown entering on an "STA" or similar
   signal terminal.

2. **The reference voltage and resistance values** — the table showing each switch state, its
   resistance (kΩ), and the resulting voltage. This is sometimes labeled "Cruise Switch Voltage"
   or "Multiswitch Resistance Table" in the electrical manual. Example format:
   ```
   Switch pressed    Resistance to GND    Voltage (5V ref)
   None              Open                 5.0 V
   CANCEL            3.3 kΩ              ~4.1 V
   RESUME/ACCEL      1.0 kΩ              ~3.0 V
   SET/COAST         0.27 kΩ             ~1.3 V
   ```
   **Do not assume the values above are correct for the ST185** — they are examples only.
   Look up the actual values and add them to this table once found.

### Wiring to CSB3 Analog 2

The OEM circuit uses a 5V reference from the cruise control ECU. Since you're bypassing that ECU,
you need to provide the 5V pull-up yourself. Options:

**Option A — CSB3 provides 5V reference (check CSB3 manual):**
Some CSB3 analog inputs have a configurable 5V pull-up. If available:
- Connect the cruise stalk signal wire directly to CSB3 Analog 2 input
- Enable the internal pull-up in the ECUMaster configurator
- The voltage divider is formed internally

**Option B — External pull-up resistor:**
If CSB3 has no internal pull-up:
- Add a 10 kΩ resistor from CSB3's 5V output to the Analog 2 input line
- Connect the cruise stalk signal wire to that same junction
- The stalk's ladder resistors then divide against this 10 kΩ to produce the voltage
- Verify the resulting voltage levels still fall within distinct thresholds for each switch

**If the OEM circuit is 12V-referenced** (verify in the diagram — look for a 12V supply to the
cruise stalk connector):
- Add a voltage divider to bring 12V max → 5V max before CSB3 Analog 2
- Standard divider: 10 kΩ upper, 6.2 kΩ lower (roughly 3:2 ratio for 12→5V scale)
- Recalculate all threshold voltages after the divider

### Decoding approach — two options

**Option A — CSB3 AS_MASK threshold decoding (preferred, if supported):**

The CSB3's AS_MASK field (0x642 byte3) suggests built-in support for analog switch decoding.
Check the ECUMaster CAN Switch Board V3 manual for "Analog Switch" or "AS" configuration.
If supported:
1. In the configurator, assign Analog 2 as an Analog Switch input
2. Enter the voltage thresholds for each switch state (from the ST185 diagram)
3. Assign each decoded state to an AS_MASK bit (bit0=SET, bit1=RESUME, bit2=CANCEL, etc.)
4. In PCLink, extend the 0x642 CAN User Stream to include byte3:
   - AS_MASK bit0 → VDI1 (cruise SET)
   - AS_MASK bit1 → VDI2 (cruise RESUME — this replaces the current AC assignment; shift AC
     to a different VDI if needed)
   - AS_MASK bit2 → VDI3 (cruise CANCEL)
5. In PCLink cruise control settings, map VDI1=SET, VDI2=RESUME, VDI3=CANCEL

**⚠️ NOTE:** If AS_MASK decodes the cruise stalk, reassign the SW_MASK bits (Step 5) so they
don't overlap with cruise functions. See Step 5 for the current VDI assignment table.

**Option B — Raw mV decode in PCLink:**

If CSB3 AS_MASK decoding is not available:
1. Analog 2 → CSB3 → 0x640 bytes 2-3 (raw mV, uint16, BigEndian)
2. In PCLink, receive 0x640 bytes 2-3 as a GP Voltage channel (e.g., "Cruise Stalk mV")
3. Use PCLink's Math Channels (or Auxiliary Channels) to decode voltage ranges:
   ```
   If Cruise Stalk mV > [CANCEL_LOW] AND < [CANCEL_HIGH] → virtual output: CANCEL = ON
   If Cruise Stalk mV > [RESUME_LOW] AND < [RESUME_HIGH] → virtual output: RESUME = ON
   If Cruise Stalk mV > [SET_LOW]    AND < [SET_HIGH]    → virtual output: SET = ON
   ```
4. Map each virtual output to a PCLink VDI or directly to the cruise control function inputs
5. Threshold values come from the ST185 electrical diagram (see table above)

### MAIN switch

The ST185 MAIN cruise on/off switch may be:
- A separate discrete wire on the stalk connector (goes fully open/close, not through the resistor
  ladder) → wire to a CSB3 digital input → SW_MASK bit per Step 5
- OR embedded in the resistor ladder as the "full voltage = off" state (no separate wire needed)

Verify in the ST185 electrical diagram which type the MAIN switch is.

---

## Step 5 — Digital Switch Assignments (SW_MASK → 0x642 byte4)

The CSB3 packs digital input states into byte4 of 0x642 as a bitmask (SW_MASK).
PCLink reads this via a CAN User Stream: **0x642 byte4 bits0-4 → VDI1–VDI5**.

| SW_MASK Bit | Physical Signal | PCLink VDI | Function |
|---|---|---|---|
| bit0 (LSB) | Cruise MAIN switch (if discrete wire — see Step 4.1) | VDI1 | Cruise master on/off |
| bit1 | AC request button | VDI2 | AC compressor request |
| bit2 | Evap core over-temp switch | VDI3 | Evap over-temp protect |
| bit3 | Spare | VDI4 | Assign as needed |
| bit4 | Spare | VDI5 | Assign as needed |
| bit5–7 | Unused | — | Not read by PCLink |

**Note:** If the cruise stalk AS_MASK decoding path is used (Step 4.1 Option A), the cruise
SET/RESUME/CANCEL functions arrive via AS_MASK bits, NOT SW_MASK bits. In that case bit0 here
only handles the MAIN on/off switch. Reassign VDI mapping in PCLink accordingly.

In the configurator, map physical wires to digital input channels and confirm the bit ordering matches the table above.

**PCLink VDI failsafe:** If CSB3 comm is lost (PCLink timeout 200 ms), VDI1–VDI5 default to **0** (all off). This is safe — cruise cancels, AC off.

---

## Step 6 — Rotary Encoder Assignments (0x642 bytes 0–2)

Rotary positions are nibble-packed (4 bits each, 0–15 positions per encoder):

| 0x642 Byte | Upper Nibble [7:4] | Lower Nibble [3:0] |
|---|---|---|
| byte0 | Rotary 1 | Rotary 2 |
| byte1 | Rotary 3 | Rotary 4 |
| byte2 | Rotary 5 | Mode switch position |

Assign physical encoders in the configurator:
- **Rotary 1** → Boost map selector (cluster decodes → sends 0x3EC to ECU)
- **Rotary 2** → TC map selector (cluster decodes → sends 0x3ED to ECU)
- **Rotary 3–5 / Mode** → TBD (leave unassigned until you have hardware)

**Note:** The cluster firmware decodes these rotary values directly from 0x642. The ECU receives the selection via 0x3EC/0x3ED from the cluster, then echoes it back in 0x3EF bytes 5 and 3 — so RealDash reads the selection from the ECU echo, not the cluster directly.

---

## Step 7 — Low-Side Outputs (0x643 — CSB3 is the receiver)

The ECU commands CSB3 low-side outputs via ID 0x643 at 50 ms. The cluster does NOT transmit 0x643. The ECU is the sole transmitter.

| 0x643 Byte | Bit | CSB3 Output | Suggested Use |
|---|---|---|---|
| byte0 | bit0 | LS Out 1 | Cooling fan relay 1 |
| byte0 | bit1 | LS Out 2 | Cooling fan relay 2 |
| byte0 | bit2 | LS Out 3 | AC compressor relay |
| byte0 | bit3 | LS Out 4 | Spare |
| byte1 | bit0–7 | LS Out 5–8 (if equipped) | Spare |

In PCLink, set up a **CAN Transmit** stream on ID 0x643 with a 50 ms cycle time. Use PCLink virtual outputs and bit-packing to map your fan/AC channels to the correct bits.

---

## Step 8 — Heartbeat (Automatic — No Config Needed)

0x642 byte7 is a rolling counter (0→255→0) that increments with every CSB3 transmission. The ECU monitors this automatically via the PCLink receive timeout setting.

- **PCLink timeout:** 200 ms on CAN User Streams 0x640 / 0x641 / 0x642
- **Fault action (automatic):** VDI1–5 reset to 0; GP Temp1 holds last value
- **Fault broadcast:** PCLink sets 0x3F1 byte6 bit5 ("Switchboard Comm Fault")

The CSB3 needs no configuration for the heartbeat. PCLink side: see `CANBUS-LINK-G4X-CONFIG.md` for the receive timeout setting.

---

## Step 9 — Termination (Critical)

Exactly two 120Ω termination resistors go on the bus — one at each physical end.

| Node | Position | Termination |
|---|---|---|
| Link G4X FuryX ECU | Bus end 1 | **ON** (120Ω — built-in or add inline) |
| center-cluster-esp32-p4 | Middle | **None** (SN65HVD230 has no termination) |
| ECUMaster CSB3 | Middle | **Jumper OFF** — do not close onboard termination |
| Pi4+/Pi5 + USB-CAN adapter | Bus end 2 | **ON** — via adapter termination switch (PCAN USB) or inline 120Ω (CANable) |

**NOTE:** The Waveshare hat on the Pi is for cooling fan only — it has no CAN connections.
The termination at the Pi end comes from the USB-CAN adapter or an inline resistor, not the hat.

Bus topology (daisy chain, shortest stub lengths):
```
[ECU end] ──── center cluster ──── CSB3 ──── Pi/USB-CAN [bus end]
   120Ω                                              120Ω
```

If you need to bench-test the CSB3 alone on a short cable with a USB-CAN adapter, you can close the CSB3 termination jumper temporarily. **Remove it again before connecting to the full bus.**

---

## Final Verification Checklist

Before first power-on with ECU on the bus:

- [ ] CSB3 CAN speed confirmed **1000 kbps** in configurator
- [ ] Base ID confirmed **0x640**
- [ ] CSB3 termination jumper confirmed **OPEN (OFF)**
- [ ] Analog 1 wired to cabin temp thermistor (or test with known resistor)
- [ ] SW_MASK bits 0–4 wired to correct switches/buttons
- [ ] With CSB3 powered and isolated, 0x640 / 0x641 / 0x642 frames visible in CAN monitor at 1 Mbit/s
- [ ] In PCLink — CAN User Stream 0x640 bytes 0-1 → GP Temp1 configured
- [ ] In PCLink — CAN User Stream 0x642 byte4 bits 0-4 → VDI1-5 configured
- [ ] In PCLink — receive timeout 200 ms set for 0x640 / 0x641 / 0x642
- [ ] In PCLink — 0x643 TX stream configured for low-side outputs (fan / AC)
