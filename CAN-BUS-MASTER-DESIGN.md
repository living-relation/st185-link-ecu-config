# CAN Bus Master Design — Celica Project

**Companion document:** `CAN-BUS-ID-ALLOCATION-TABLE.md` contains the byte-level layout for every ID referenced here. Read the two together — this document covers *architecture and configuration*; the allocation table covers *wire format*.

This document supersedes the bus-topology, ingestion, and fault-handling assumptions in **"CAN Bus Configuration for Link ECU.docx"** (see §8, Corrections).

---

## 1. Overview & Scope

A single shared CAN bus at **1 Mbit/s** connects:

| Node | Role | CAN participation |
|---|---|---|
| Link G4X FuryX ECU | Powertrain controller | Bidirectional. Also internally consumes its CAN-Lambda module (0x3B6) |
| center-cluster-esp32-p4 | Dash / instrument cluster | Bidirectional (TWAI_MODE_NORMAL) — the **only** dash board on CAN |
| ECUMaster CAN Switch Board V3 | Accessory I/O (analog inputs, switches, low-side outputs) | Bidirectional (0x640-0x642 out, 0x643 in) |
| Pi4+/Pi5 + USB-CAN adapter (CANable or PCAN USB) running RealDash | Secondary display (840×480, 7") | Passive listener only — receive 0x3EF/0x3F0/0x3F1 |

**Out of scope:** the left and right side displays (`left-side-cluster-esp32s3`, `right-side-cluster-esp32s3`) are **not CAN nodes**. Per `CANBUS-LINK-G4X-CONFIG.md`, they receive data from the center cluster over UART (center GPIO20→left GPIO44, center GPIO21→right GPIO44). They are unaffected by anything in this document.

---

## 2. Physical Layer

- **Topology:** single linear bus segment, 1 Mbit/s, ISO 11898-2, 120Ω termination at both physical ends of the bus.
- **Transceivers:**
  - ECU: Link G4X FuryX CANH/CANL (internal, includes CAN-Lambda module on the same internal bus).
  - center-cluster-esp32-p4: SN65HVD230 (3.3V), TWAI GPIO5=TX / GPIO4=RX (per `sdkconfig`/`Kconfig.projbuild`).
  - ECUMaster CAN Switch Board V3: built-in CAN transceiver, CANH/CANL screw terminals.
  - Pi USB-CAN adapter (CANable or PCAN USB): plugs into a USB port on the Pi; the adapter's CANH/CANL terminals wire to the shared bus. The Waveshare dual-MCP2515 hat physically present on the Pi is **NOT a CAN node** — it is retained for its cooling fan only. Do not wire its CANH/CANL to the bus.
- **Wiring rule:** all four nodes' CANH/CANL pairs are daisy-chained onto the same two-wire bus; termination resistors live at the two physical ends of the harness (commonly: ECU end and Pi end). Do not add a third termination point.

---

## 3. Bus Speed Reconciliation

| Device | Default speed | Required speed on this bus | Action |
|---|---|---|---|
| Link G4X FuryX (ECU CAN port + CAN-Lambda) | n/a (configured) | **1 Mbit/s** | Already set — `link_g4x_can_setup.lcs`, CANModule Index="1" (CAN1), BitRate=1000000. No change. |
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
- **Input frame** (Base+3 = 0x643): low-side output control (L1-L4), source TBD — see §9.

### SW_MASK assignment (0x642 byte4)

| Bit | Switch | Function |
|---|---|---|
| 0 | Switch 1 | Evaporator Core State |
| 1 | Switch 2 | AC Request |
| 2 | Switch 3 | Cruise Control Active |
| 3 | Switch 4 | Cruise Set / Accelerate |
| 4 | Switch 5 | Cruise Resume / Decelerate |
| 5-7 | Switch 6-8 | Unassigned — available for future accessory inputs |

### Heartbeat (0x642 byte7)
Increments on every transmitted 0x642 frame (0-255, wraps). Nominal cycle: switchboard default 20 Hz (50 ms). Used in the fault-tolerance design (§6).

---

## 5. PCLink Ingestion — User Streams & VDI Mapping

The Link G4X consumes two switchboard frames via PCLink "User Stream" inputs, converting raw CAN bytes into ECU-usable channels:

### User Stream 1 — Cabin/Ambient Temperature
- **Source:** 0x640, bytes 0-1 (Analog Input 1, raw 0-5000 mV from a thermistor wired to the switchboard's AIN1).
- **PCLink target:** **GP Temp1**, using a PCLink thermistor calibration table to convert the raw millivolt reading to °C.
- **Downstream use:** GP Temp1 is available to ECU logic (e.g., AC/evap control) and is optionally mirrored to RealDash on 0x3F0 byte5 ("Cabin Temp Mirror") so the dash doesn't need its own thermistor curve.

### User Stream 2 — Accessory Switch States (VDI1-5)
- **Source:** 0x642, byte 4 (SW_MASK), bits 0-4.
- **PCLink target:** Virtual Digital Inputs (VDI1-5), one bit per VDI:

| SW_MASK bit | VDI | Meaning |
|---|---|---|
| 0 | VDI1 | Evaporator Core State |
| 1 | VDI2 | AC Request |
| 2 | VDI3 | Cruise Control Active |
| 3 | VDI4 | Cruise Set / Accelerate |
| 4 | VDI5 | Cruise Resume / Decelerate |

- **Downstream use:** these VDIs feed the ECU's existing cruise-control and AC/evaporator logic (PCLink condition tables / virtual aux outputs) — e.g., VDI3=1 arms cruise, VDI4/VDI5 adjust the set speed, VDI2=1 requests the AC compressor clutch output, VDI1 controls the evaporator core relay logic.

Both User Streams require the ECU to be on the same physical bus as the switchboard (§3).

---

## 6. Fault Tolerance — Heartbeat-Based Failsafe

Two independent layers protect against switchboard communication loss:

### Layer 1 — PCLink CAN receive timeout (primary, ECU-side)
- Configure a receive timeout on each switchboard frame (0x640, 0x641, 0x642) in PCLink's CAN setup. If a configured frame isn't received within its expected window, PCLink applies a configured default/hold value to the associated channels.
- **Recommended timeout:** 200 ms (4× the switchboard's nominal 50 ms / 20 Hz cycle) — tolerates occasional dropped frames without false trips.
- **Recommended defaults on timeout:**
  - VDI1-5 → 0 (Evap Core off, AC not requested, Cruise inactive/no set-resume) — this is the fail-safe state: cruise disengaged, AC compressor off, evaporator relaxed.
  - GP Temp1 → hold last value (avoids a gauge jump from a transient dropout; a stale cabin temp reading is low-risk).
- This is the **primary safety net** and requires **no firmware changes** — pure PCLink configuration (Task #9).

### Layer 2 — heartbeat staleness check (secondary, ECU-side diagnostic)
- 0x642 byte7 increments on every transmitted frame. **Switchboard frames (0x640/0x641/0x642) are received only by the ECU** — neither RealDash nor the cluster sees them. The ECU can track the heartbeat across frames: if 0x642 keeps arriving but the heartbeat byte stops changing for several consecutive cycles, the switchboard's firmware is hung even though its CAN controller is still transmitting — a failure mode Layer 1 (frame-arrival timeout) cannot detect.
- **The ECU is the only node that sees the switchboard, so the ECU detects the fault and relays it to RealDash.** On a Layer-1 receive-timeout (or a detected heartbeat stall), the ECU sets **bit 5 of the Extended Warnings bitmask (0x3F1 byte6)** — "Switchboard/Accessory Bus Comm Fault" — in its own ECU→RealDash stream, which RealDash displays. This is single-transmitter-valid (the ECU owns 0x3F1). The cluster is not involved: it never sees switchboard frames and its displays are unchanged.
- This layer is **advisory only**. It does not itself force cruise/AC states — that remains Layer 1's job on the ECU.

### Resulting failsafe behavior on total switchboard loss
| Function | Failsafe state | Mechanism |
|---|---|---|
| Cruise Control | Disengaged (VDI3→0) | Layer 1 PCLink timeout |
| AC compressor | De-energized (VDI2→0) | Layer 1 PCLink timeout |
| Evaporator core / blower | Relaxed/off (VDI1→0) | Layer 1 PCLink timeout |
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
  | 0x3F0 | 1008 | Extended Sensors (fuel temp, engine load, coolant pressure, ethanol %, IAT, cabin temp, turbo speed, trigger errors) |
  | 0x3F1 | 1009 | IMU & Extended Warnings (accel X/Y/Z, ext warn bits incl. switchboard comm fault) |

  **Excluded from RealDash XML:**
  - 0x3E8–0x3EE — cluster frames; cluster already shows these. RealDash does not duplicate them.
  - 0x640–0x642 — switchboard frames; the ECU is the only node that needs to read them. Switchboard active states relevant to display are echoed by the ECU into 0x3EF/0x3F1.

  The RealDash channel-description XML is fully defined in `link_g4x_realdash.xml` (valid RealDash
  CAN v2, BigEndian, with the 0x3F1 warning bitmask decoded per-bit). The visual dashboard that
  consumes these inputs is specified in `REALDASH-LAYOUT.md`.

---

## 8. Corrections to "CAN Bus Configuration for Link ECU.docx"

These were identified during reconciliation and are documented in full (with byte-level resolution) in `CAN-BUS-ID-ALLOCATION-TABLE.md` §7. Summary:

### Conflict A — ID collision
The docx's proposed 0x3E8 (multiplexed Generic Dash) and 0x3E9-0x3EC ("Custom Stream 1-4", little-endian) collide with the immutable, coded-complete firmware streams on those same IDs (BigEndian, non-multiplexed Custom; 0x3EE absent from the docx entirely). **Resolution:** the docx's useful payloads are re-homed to new IDs **0x3EF-0x3F1**, using the existing BigEndian/Custom convention.

### Conflict B — Bidirectional vs. listen-only
The docx assumes the cluster is a passive/listen-only CAN node. The coded firmware (`canbus.h`) configures `TWAI_MODE_NORMAL` (bidirectional) and actively transmits 0x3EC/0x3ED on confirmed button press. **Resolution:** the cluster is a full bus participant — it transmits 0x3EC/0x3ED to the ECU. But a CAN ID has a single transmitter, so the cluster does not inject into the ECU-owned 0x3EF, and RealDash shares no CAN traffic with the cluster directly. The ECU receives 0x3EC/0x3ED and echoes the selected boost map / TC setting to RealDash in 0x3EF bytes 5 / 3.

### Conflict C — "Generic Dash" format assumption
The docx assumes Link's standard multiplexed "Generic Dash" stream type on 0x3E8. The coded firmware uses Link's **"Custom" stream type** with bespoke BigEndian layouts (per `CANBUS-LINK-G4X-CONFIG.md`, Global CAN Settings: Stream type = Custom, Byte order = Big endian). **Resolution:** all new streams (0x3EF-0x3F1) follow the same Custom/BigEndian convention.

### Additional correction — single shared bus requirement (not in docx)
The docx does not address the ECUMaster switchboard's bus segment or speed at all. This design requires the switchboard to share the ECU/cluster's 1 Mbit/s bus (reconfigured from its 500 kbps default) so that PCLink's User Stream ingestion (§5) can function. This is a net-new requirement introduced by this design, not a correction of an existing docx claim.

---

## 9. Decision — 0x643 Control Source = ECU (RESOLVED 2026-06-14)

0x643 (switchboard low-side output control, INPUT) needs a transmitter. Two candidates:

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — ECU (PCLink aux output → CAN TX)** | Link G4X PCLink aux/output table drives a CAN TX frame on 0x643 | ECU already has rich conditional logic (RPM, temp, speed-based conditions) available via Virtual Aux tables; no firmware changes | Couples body/accessory output control to the tune file rather than firmware — harder to version-control alongside cluster code; need to confirm PCLink's Custom-stream CAN TX supports per-bit aux-output mapping for L1-L4 |
| **B — Cluster (center-cluster-esp32-p4 via `canbus_inject_frame`)** | Cluster firmware periodically transmits 0x643 based on its own switch/UI state | Keeps accessory/body output ownership in the cluster, consistent with the cluster already owning UI inputs and transmitting 0x3EC/0x3ED on confirmed actions; `canbus_inject_frame()` already exists in `canbus.h` (currently scoped as a USB bench-tooling injector — would need to be promoted to a general "construct + send" helper, a small addition) | Requires new cluster firmware logic; adds a new periodic/event TX role to the cluster |

**Decision (2026-06-14): Option A — 0x643 is transmitted by the ECU** (Link G4X PCLink aux output → CAN TX). The switchboard low-side outputs are **not used for anything yet**; if/when they are used, the ECU owns that logic and they will most likely just drive **LEDs**. This is therefore **low priority** — no cluster firmware TX role for 0x643 is added, and `canbus_inject_frame()` stays scoped as USB bench tooling. (Option B, cluster-owned TX, was considered but not chosen.)

---

## 10. Summary — Action Items for Task #9

| # | Action | Owner |
|---|---|---|
| 1 | Reconfigure ECUMaster CAN Switch Board V3: bit rate 500 kbps → 1000 kbps | Hardware/config |
| 2 | Add 0x3EF (50ms), 0x3F0 (100ms), 0x3F1 (50ms) Custom/BigEndian streams to `link_g4x_can_setup.lcs`/`.json` | PCLink config |
| 3 | Configure PCLink User Stream 1 (0x640 bytes0-1 → GP Temp1, thermistor table) and User Stream 2 (0x642 byte4 bits0-4 → VDI1-5) | PCLink config |
| 4 | Configure PCLink receive timeouts (200ms) on 0x640/0x641/0x642 with fail-safe defaults (VDI1-5→0, GP Temp1→hold) | PCLink config |
| 5 | Cluster firmware: **no changes.** Cluster displays are unchanged — it keeps decoding 0x3E8–0x3EE and transmitting 0x3EC/0x3ED. The new 0x3EF/0x3F0/0x3F1 streams are ECU→RealDash only; switchboard comm-fault (§6) is ECU-detected and surfaced to RealDash via 0x3F1 byte6 bit5. | — (none) |
| 6 | **0x643 source = ECU** (PCLink aux→CAN TX) per §9 — outputs unused/LED-only, low priority | PCLink config (deferred) |
| 7 | RealDash XML frame/value definitions for 0x3EF-0x3F1 — **done** (`link_g4x_realdash.xml`). Build the dashboard per `REALDASH-LAYOUT.md`. 0x640-0x642 deliberately excluded (ECU echoes display-relevant values) | RealDash config |
| 8 | Verify bus termination (120Ω × 2): ECU end + Pi end (USB-CAN adapter side). Waveshare hat is not on the bus. | Hardware |
