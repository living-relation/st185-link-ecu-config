# CAN Bus Master Design — Celica Project

The byte-level layout for every ID is `CAN-BUS-ID-ALLOCATION-TABLE.md` (the one wire-format table; `bench/check_parity.py` reads it). This file is the one CAN architecture and PCLink-apply document.

---

## 1. Overview & Scope

A single shared CAN bus at **1 Mbit/s** connects **five nodes**:

| Node | Role | CAN participation |
|---|---|---|
| Link G4X XtremeX ECU | Powertrain controller | Bidirectional |
| Link CAN-Lambda | External wideband (Bosch LSU 4.9) | Transmit 0x3B6; receive 0x3BE. Physically on the bus — not an ECU-internal-only device |
| center-cluster-esp32-p4 | Dash / instrument cluster | Bidirectional (TWAI_MODE_NORMAL) — the **only** dash board on CAN |
| ECUMaster CAN Switch Board V3 | Accessory I/O (analog inputs, switches, low-side outputs) | Bidirectional (0x640-0x642 out, 0x643 in) |
| Pi4+/Pi5 + USB-CAN adapter (CANable or PCAN USB) running RealDash | Secondary display (840×480, 7") | Passive listener only — receive 0x3EF/0x3F0/0x3F1 |

**Out of scope:** the left and right side displays (`left-side-cluster-esp32s3`, `right-side-cluster-esp32s3`) are **not CAN nodes**. Per `CAN-BUS-MASTER-DESIGN.md`, they receive data from the center cluster over UART (center GPIO20→left GPIO44, center GPIO21→right GPIO44). They are unaffected by anything in this document.

---

## 2. Physical Layer

- **Topology:** single linear bus segment, 1 Mbit/s, ISO 11898-2, 120Ω termination at both physical ends of the bus. **Settled 2026-09-27 (harness redesign; not an open item): the two ends are the ECU and the Link CAN-Lambda**, matching `ST185-CAN.harness` as drawn (`r_term_ecu`, `r_term_end`). The center cluster, switchboard, and Pi are mid-bus stubs — none of them are terminated.
- **Transceivers:**
  - ECU: Link G4X XtremeX CANH/CANL.
  - Link CAN-Lambda: module CANH/CANL on the shared bus (0x3B6 / 0x3BE). This is the fifth node.
  - center-cluster-esp32-p4: SN65HVD230 (3.3V), TWAI GPIO5=TX / GPIO4=RX (per `sdkconfig`/`Kconfig.projbuild`).
  - ECUMaster CAN Switch Board V3: built-in CAN transceiver, CANH/CANL screw terminals.
  - Pi USB-CAN adapter (CANable or PCAN USB): plugs into a USB port on the Pi; the adapter's CANH/CANL terminals wire to the shared bus. The Waveshare dual-MCP2515 hat physically present on the Pi is **NOT a CAN node** — it is retained for its cooling fan only. Do not wire its CANH/CANL to the bus.
- **Wiring rule:** all five nodes' CANH/CANL pairs are daisy-chained onto the same two-wire bus; termination resistors live at the ECU end and the CAN-Lambda end only. Do not add a third termination point, and do not terminate at the center cluster, switchboard, or Pi.
- **Node hook-up (moved from the retired `WIRING.md`, 2026-10-19; the wires themselves are in `docs/harness/MASTER-wirelist.csv`):**
  - Center cluster: Waveshare [SN65HVD230 CAN Board](https://www.waveshare.com/sn65hvd230-can-board.htm), passive (no firmware). VCC -> the P4's **3V3** (never 5 V), GND -> GND, CTX -> GPIO5 (TWAI TX), CRX -> GPIO4 (TWAI RX), CANH / CANL -> the bus. Never short CANH to CANL. No resistor on this board (mid-bus stub). The cluster's J8 header pinout lives only in `center-cluster-esp32-p4` (`PINOUT.md`, `main/Kconfig.projbuild`).
  - Switchboard: CANH / CANL screw terminals; its onboard 120 ohm jumper stays **OFF**; bit rate set to 1000 kbps before it is connected (§3, `ECUMASTER_SWITCHBOARD_SETUP.md`).
  - Pi USB-CAN adapter: CANH -> CANH, CANL -> CANL, GND -> bus ground; a PCAN USB's termination switch stays **OFF**. The Pi runs on a switched ignition feed only, no hold relay (Daniel 2026-09-28).

---

## 3. Bus Speed Reconciliation

| Device | Default speed | Required speed on this bus | Action |
|---|---|---|---|
| Link G4X XtremeX (ECU CAN port) | n/a (configured) | **1 Mbit/s** | Already set — `link_g4x_can_setup.lcs`, CANModule Index="1" (CAN1), BitRate=1000000. No change. |
| Link CAN-Lambda (external module) | 1 Mbit/s native | **1 Mbit/s** | On-bus node. PCLink mode `Link CAN-Lambda`, ID 950 (0x3B6). |
| center-cluster-esp32-p4 (TWAI) | n/a (coded) | **1 Mbit/s** | Already coded-complete. No change. |
| ECUMaster CAN Switch Board V3 | **500 kbps** | **1 Mbit/s** | **Required reconfiguration** — 1000 kbps is a supported, non-default speed per the switchboard manual. Must be changed via the ECUMaster configuration tool before the switchboard is connected to this bus. |
| Pi USB-CAN adapter (CANable or PCAN USB) | configurable | **1 Mbit/s** | Set in RealDash's CAN adapter settings. The Waveshare hat is cooling only — not configured here. |

**Why one shared bus:** PCLink's "User Stream" feature (§5) lets the ECU ingest the switchboard's 0x640/0x642 frames directly — but only if the ECU and the switchboard are on the same physical bus segment. This is the architectural reason the switchboard's speed must be changed rather than left on its own 500 kbps segment.

---

## 4. ECUMaster CAN Switch Board V3 — Configuration

- **Base ID:** 0x640 (factory default — keep as-is).
- **Bit rate:** 1000 kbps (**non-default — see §3**).
- **Output frames** (Base+0 / Base+1 / Base+2 = 0x640/0x641/0x642): full byte layout in allocation table §5. Summary:
  - 0x640: Analog Inputs 1-4 (raw mV, 0-5000)
  - 0x641: Analog Inputs 5-8 (raw mV, 0-5000)
  - 0x642: Rotaries 1-8 (nibble-packed), SW_MASK (8 switches), AS_MASK (8 analog-states), LS_MASK (4 low-side outputs), heartbeat byte
- **Input frame** (Base+3 = 0x643): low-side output control (L1-L4), source = **ECU** (decided 2026-06-14, §8). Outputs unused / LED-only for now. Sent as a 50 ms periodic PCLink TX stream; bytes change only when an output changes.

### SW_MASK assignment (0x642 byte4)

| Bit | Switch | Function |
|---|---|---|
| 0 | Switch 1 | Unassigned (was Evaporator Core State; A/C is the OEM amplifier's, 2026-09-27) |
| 1 | Switch 2 | Unassigned (was AC Request; same) |
| 2 | Switch 3 | Cruise Control Active (MAIN, stalk pin 15) |
| 3 | Switch 4 | Unassigned (was Cruise Set; the OEM stalk has no SET wire, S23) |
| 4 | Switch 5 | Unassigned (was Cruise Resume; the OEM stalk has no RESUME wire, S23) |
| 5 | Switch 6 | Clutch pedal down (2026-10-14, R80) |
| 6 | Switch 7 | Brake pedal pressed (2026-10-14, R80) |
| 7 | Switch 8 | Reverse engaged (2026-10-14, R80) |

### Heartbeat (0x642 byte7)
Increments on every transmitted 0x642 frame (0-255, wraps). Nominal cycle: switchboard default 20 Hz (50 ms). Used in the fault-tolerance design (§6).

---

## 5. PCLink Ingestion — User Streams & VDI Mapping

The Link G4X consumes two switchboard frames via PCLink "User Stream" inputs, converting raw CAN bytes into ECU-usable channels:

### User Stream 1 — retired 2026-09-27
- Analog Input 1 (0x640 bytes 0-1) used to carry a cabin thermistor into **GP Temp1**. Cabin, evaporator and A/C request belong to the OEM A/C amplifier, so no CSB3 input is wired for them and Analog Input 1 is unassigned. The frame layout is unchanged.

### User Stream 2 — Accessory Switch States (VDI3, VDI6-8)
- **Source:** 0x642, byte 4 (SW_MASK), bits 2 and 5-7 (receive channel 0x642 in the `.lcs`; canonical map `switchboard_frames.json` "ecu_receive").
- **PCLink target:** Virtual Digital Inputs (VDI1-5), one bit per VDI:

| SW_MASK bit | VDI | Meaning |
|---|---|---|
| 0 | VDI1 | Unassigned (was Evaporator Core State) |
| 1 | VDI2 | Unassigned (was AC Request) |
| 2 | VDI3 | Cruise Control Active |
| 3 | VDI4 | Unassigned |
| 4 | VDI5 | Unassigned |
| 5 | VDI6 | Clutch Switch — cruise cancel; clutch input for flat shift / launch |
| 6 | VDI7 | Brake Switch — cruise cancel (the ECU's brake input) |
| 7 | VDI8 | Reverse Switch — sets Gear Position = 7 (R) in 0x3EB |

- **Downstream use:** these VDIs feed the ECU's cruise-control logic (PCLink condition tables / virtual aux outputs) — VDI3=1 arms cruise, VDI6 (clutch) and VDI7 (brake) cancel it; SET/COAST, RES/ACC and CANCEL come from the stalk ladder on CSB3 Analog 2 (0x640 bytes 2-3), decoded in PCLink (ECUMASTER_SWITCHBOARD_SETUP.md Step 4.1). VDI1, VDI2, VDI4 and VDI5 are unassigned; A/C request and evaporator control are the OEM A/C amplifier's.

Both User Streams require the ECU to be on the same physical bus as the switchboard (§3).

---

## 6. Fault Tolerance — Heartbeat-Based Failsafe

Two independent layers protect against switchboard communication loss:

### Layer 1 — PCLink CAN receive timeout (primary, ECU-side)
- Configure a receive timeout on each switchboard frame (0x640, 0x641, 0x642) in PCLink's CAN setup. If a configured frame isn't received within its expected window, PCLink applies a configured default/hold value to the associated channels.
- **Recommended timeout:** 200 ms (4× the switchboard's nominal 50 ms / 20 Hz cycle) — tolerates occasional dropped frames without false trips.
- **Recommended defaults on timeout:**
  - Every switchboard receive channel → 0 (VDI3 = cruise disarmed, VDI6-8 off, Cruise Stalk mV = 0) — the fail-safe state: cruise disengaged.
- This is the **primary safety net** and requires **no firmware changes** — pure PCLink configuration (Task #9).

### Layer 2 — heartbeat staleness check (secondary, ECU-side diagnostic)
- 0x642 byte7 increments on every transmitted frame. **Switchboard frames (0x640/0x641/0x642) are received only by the ECU** — neither RealDash nor the cluster sees them. The ECU can track the heartbeat across frames: if 0x642 keeps arriving but the heartbeat byte stops changing for several consecutive cycles, the switchboard's firmware is hung even though its CAN controller is still transmitting — a failure mode Layer 1 (frame-arrival timeout) cannot detect.
- **The ECU is the only node that sees the switchboard, so the ECU detects the fault and relays it to RealDash.** On a Layer-1 receive-timeout (or a detected heartbeat stall), the ECU sets **bit 5 of the Extended Warnings bitmask (0x3F1 byte6)** — "Switchboard/Accessory Bus Comm Fault" — in its own ECU→RealDash stream, which RealDash displays. This is single-transmitter-valid (the ECU owns 0x3F1). The cluster is not involved: it never sees switchboard frames and its displays are unchanged.
- This layer is **advisory only**. It does not itself force cruise/AC states — that remains Layer 1's job on the ECU.

### Resulting failsafe behavior on total switchboard loss
| Function | Failsafe state | Mechanism |
|---|---|---|
| Cruise Control | Disengaged (VDI3→0) | Layer 1 PCLink timeout |
| Throttle | Returns to driver pedal authority | Consequence of cruise disengage above — no separate action needed |
| Driver notification | "Switchboard/Accessory Bus Comm Fault" warning | ECU detects (only node seeing switchboard) → sets 0x3F1 byte6 bit5 → RealDash displays |

**Recovery:** once 0x640/0x641/0x642 resume arriving within the timeout window, PCLink's Layer-1 channels return to live values automatically (standard PCLink timeout-recovery behavior). The ECU clears the 0x3F1 comm-fault bit once the switchboard frames/heartbeat resume.

---

## 7. RealDash / Pi Physical Layer

- **Hardware:** Pi4+/Pi5 running RealDash on an 840×480 7" screen. CAN interface is a **USB-CAN adapter (CANable or PCAN USB)** connected to one of the Pi's USB ports. The Waveshare dual-MCP2515 hat physically present on the Pi is retained for its cooling fan only — it is **not** wired to the CAN bus and must not be configured in RealDash.
- **CAN connection:** USB-CAN adapter CANH/CANL → shared vehicle bus. Speed: **1 Mbit/s**. Configure as `bus="0"` (first CAN connection) in RealDash.
- **Role:** RealDash is a **passive listener** — it does not transmit. No arbitration or TX-conflict considerations.
- **RealDash XML scope (CRITICAL):** RealDash receives **only** the three new ECU TX frames that the cluster does not display:

  | Frame ID | Decimal | Content |
  |---|---|---|
  | 0x3EF | 1007 | Drive Assist & Status (TC state, boost map index, cruise state, AC status, lambda target, TPS) |
  | 0x3F0 | 1008 | Extended Sensors (fuel temp, engine load, coolant pressure [2 bytes], ethanol %, charge-pipe IAT, turbo speed, trigger errors) — cabin temp dropped 2026-06-28 to fit 2-byte coolant pressure |
  | 0x3F1 | 1009 | IMU & Extended Warnings (accel X/Y/Z, ext warn bits incl. switchboard comm fault) |

  **Excluded from RealDash XML:**
  - 0x3E8–0x3EE — cluster frames; cluster already shows these. RealDash does not duplicate them.
  - 0x640–0x642 — switchboard frames; the ECU is the only node that needs to read them. Switchboard active states relevant to display are echoed by the ECU into 0x3EF/0x3F1.

  The RealDash channel-description XML is fully defined in `link_g4x_realdash.xml` (valid RealDash
  CAN v2, BigEndian, with the 0x3F1 warning bitmask decoded per-bit). The visual dashboard that
  consumes these inputs is specified in `REALDASH-LAYOUT.md`.

---

## 8. Decision — 0x643 Control Source = ECU (RESOLVED 2026-06-14)

0x643 (switchboard low-side output control, INPUT) needs a transmitter. Two candidates:

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — ECU (PCLink aux output → CAN TX)** | Link G4X PCLink aux/output table drives a CAN TX frame on 0x643 | ECU already has rich conditional logic (RPM, temp, speed-based conditions) available via Virtual Aux tables; no firmware changes | Couples body/accessory output control to the tune file rather than firmware — harder to version-control alongside cluster code; need to confirm PCLink's Custom-stream CAN TX supports per-bit aux-output mapping for L1-L4 |
| **B — Cluster (center-cluster-esp32-p4 via `canbus_inject_frame`)** | Cluster firmware periodically transmits 0x643 based on its own switch/UI state | Keeps accessory/body output ownership in the cluster, consistent with the cluster already owning UI inputs and transmitting 0x3EC/0x3ED on confirmed actions; `canbus_inject_frame()` already exists in `canbus.h` (currently scoped as a USB bench-tooling injector — would need to be promoted to a general "construct + send" helper, a small addition) | Requires new cluster firmware logic; adds a new periodic/event TX role to the cluster |

**Decision (2026-06-14): Option A — 0x643 is transmitted by the ECU** (Link G4X PCLink aux output → CAN TX). The switchboard low-side outputs are **not used for anything yet**; if/when they are used, the ECU owns that logic and they will most likely just drive **LEDs**. This is therefore **low priority** — no cluster firmware TX role for 0x643 is added, and `canbus_inject_frame()` stays scoped as USB bench tooling. (Option B, cluster-owned TX, was considered but not chosen.)

---

## 9. Summary — Action Items for Task #9

| # | Action | Owner |
|---|---|---|
| 1 | Reconfigure ECUMaster CAN Switch Board V3: bit rate 500 kbps → 1000 kbps | Hardware/config |
| 2 | Add 0x3EF (50ms), 0x3F0 (100ms), 0x3F1 (50ms) Custom/BigEndian streams to `link_g4x_can_setup.lcs`/`.json` | PCLink config |
| 3 | User Stream 2 (0x642 byte4 bits 2, 5-7 → VDI3, VDI6-8) and the 0x640 Cruise Stalk mV channel — **written** in the `.lcs` receive channels (2026-10-14, R80); imported with the `.lcs`. User Stream 1 (cabin temp → GP Temp1) is retired, see §5 | PCLink config |
| 4 | PCLink receive timeouts (200ms) on 0x640/0x642 with fail-safe value 0 — **written** in the `.lcs` (`Timeout="200"`) | PCLink config |
| 5 | Cluster firmware: **no changes.** Cluster displays are unchanged — it keeps decoding 0x3E8–0x3EB and 0x3EE (`main/canbus.c`) and transmitting 0x3EC/0x3ED. The new 0x3EF/0x3F0/0x3F1 streams are ECU→RealDash only; switchboard comm-fault (§6) is ECU-detected and surfaced to RealDash via 0x3F1 byte6 bit5. | — (none) |
| 6 | **0x643 source = ECU** (PCLink aux→CAN TX) per §8 — outputs unused/LED-only, low priority | PCLink config (deferred) |
| 7 | RealDash XML frame/value definitions for 0x3EF-0x3F1 — **done** (`link_g4x_realdash.xml`). Build the dashboard per `REALDASH-LAYOUT.md`. 0x640-0x642 deliberately excluded (ECU echoes display-relevant values) | RealDash config |
| 8 | Verify bus termination (120Ω × 2): ECU end + CAN-Lambda end only. Center cluster, switchboard, and Pi (USB-CAN adapter) are mid-bus stubs — confirm none of them are terminated. Waveshare hat is not on the bus. | Hardware |


## 10. PCLink apply (ECU side)

Import `link_g4x_can_setup.lcs` in PCLink → CAN → Setup → File → Open. `link_g4x_can_setup.json` is the human-readable canonical copy of the same map (encode form). The cluster decoder (`main/canbus.c` in `center-cluster-esp32-p4`, frozen) must match; `bench/check_parity.py` checks this repo's copies. Assign only the channels in the ID table — extra channels waste bus bandwidth.

Left and right side displays are not CAN nodes. They receive data from the center cluster over UART (center GPIO20→left GPIO44, center GPIO21→right GPIO44).

| Setting | Value |
|---|---|
| CAN module | the module wired to the dashboard transceiver |
| Bit rate | **1 Mbit/s** |
| Stream type | **Custom** |
| Byte order | **Big endian** |
| Transmit | streams 0x3E8–0x3EB, 0x3EE and 0x3EF–0x3F1 (ID table) |
| Receive | 0x3EC / 0x3ED (center encoder selections; ECU echoes them in 0x3EF bytes 5 / 3); 0x640 / 0x642 (CSB3); Link CAN-Lambda 0x3B6 |

**External Link CAN Lambda.** There is no onboard wideband. ECU Controls → CAN Setup: Mode tab, CAN Configuration = User Defined, Bit Rate = 1 Mbit/s. Data box, free channel: Mode = Link CAN-Lambda, CAN ID = 950 (0x3B6), format Normal. CAN Devices → Find Devices → confirm Lambda 1. Factory defaults (device identifier 0, 1 Mbit/s). Reconfig commands go on 958 (0x3BE).

**Cluster selections (Daniel 2026-10-03).** The ECU receives 0x3EC (boost-map index 0–3) and 0x3ED (TC index 0–4). Receive channels are at the end of `link_g4x_can_setup.lcs`.

**CSB3 receive.** Channels at the end of the `.lcs`, map in `switchboard_frames.json` "ecu_receive". Timeout 200 ms on each, value 0 on timeout. Switchboard frames go to the ECU only (B16); what a display needs is echoed in ECU frames.

**Adding or removing a channel later.** Never broadcast a channel the firmware has no field for: (1) add the field to cluster `dash_data.h`; (2) decode it in `canbus.c` (frozen — needs Daniel's approval); (3) then assign the next free byte here and update `.lcs` / `.json`, the ID table and `bench/frames.py`; `python bench/check_parity.py` must pass.

**Validate (PCLink).** CAN → Monitor: 0x3E8–0x3EB and 0x3EE at their cycle times; cross-check against the live runtime page; dashboard gauges track within ~2 s and an engine-protection flag raises the right-cluster warning overlay.

**Validate (vehicle).** Transceiver wired only to the center board (GPIO5 TX, GPIO4 RX) and ECU CANH/CANL. Side displays have UART from center GPIO20/21 TX to each side GPIO44 RX, plus common GND. With ECU live, center updates from CAN and both side displays mirror over UART.
