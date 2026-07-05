# CAN Bus ID Allocation Table — Celica Project

**Bus:** Single CAN bus, **1 Mbit/s**, ISO 11898-2, 120Ω terminated.
**Members:** Link G4X XtremeX ECU, center-cluster-esp32-p4 (TWAI, NORMAL/bidirectional), ECUMaster CAN Switch Board V3, and Raspberry Pi 5 running RealDash via a **USB-CAN adapter** (CANable/PCAN). (The Waveshare dual-MCP2515 hat on the Pi is retained for its fan only — it is **not** on the CAN bus.)

> **Configuration requirement:** the ECUMaster CAN Switch Board V3 ships with a **default speed of 500 kbps**. It must be set to **1 Mbit/s** to share this bus (matches `link_g4x_can_setup.lcs` CANModule Index=1 / CAN1, BitRate=1000000). 1000 kbps is a supported speed per the switchboard manual — this is a config change, not a hardware conflict.

---

## 1. Master Table

| CAN ID (hex) | CAN ID (dec) | Name | Direction | Cycle | Status |
|---|---|---|---|---|---|
| 0x3B6 | 950 | Link CAN-Lambda broadcast | CAN-Lambda module → ECU | ~10-20 Hz (module-controlled) | **Reserved — do not reuse.** On-bus, ECU-internal consumption (Bosch LSU 4.9). |
| 0x3E8 | 1000 | Engine Fast | ECU → Cluster | 10 ms | Immutable — coded-complete |
| 0x3E9 | 1001 | Speed / Press / Ign | ECU → Cluster | 10 ms | Immutable — coded-complete |
| 0x3EA | 1002 | Lambda | ECU → Cluster | 10 ms | Immutable — coded-complete |
| 0x3EB | 1003 | Gear / Fuel | ECU → Cluster | 50 ms | Immutable — coded-complete |
| 0x3EC | 1004 | Boost map selection | Cluster → ECU | event (on confirmed button press) | Immutable — coded-complete |
| 0x3ED | 1005 | TC slip-angle/setting selection | Cluster → ECU | event (on confirmed button press) | Immutable — coded-complete |
| 0x3EE | 1006 | Engine Protect | ECU → Cluster | 50 ms | Immutable — coded-complete |
| **0x3EF** | **1007** | **Drive Assist & Status (NEW)** | ECU → RealDash | 50 ms | New — this allocation |
| **0x3F0** | **1008** | **Extended Sensors (NEW)** | ECU → RealDash | 100 ms | New — this allocation |
| **0x3F1** | **1009** | **IMU & Extended Warnings (NEW)** | ECU → RealDash | 50 ms | New — this allocation |
| 0x3F2–0x63F | 1010–1599 | — | — | — | Reserved / available for future expansion |
| 0x640 | 1600 | Switchboard Analog 1–4 (Base+0) | Switchboard → ECU | 20 Hz (default) | Existing device, fully mapped below. ECU-only; RealDash does not read it — display-relevant values are echoed into 0x3EF/0x3F1. |
| 0x641 | 1601 | Switchboard Analog 5–8 (Base+1) | Switchboard → ECU | 20 Hz (default) | Existing device, fully mapped below. ECU-only (not read by RealDash). |
| 0x642 | 1602 | Switchboard Rotary/Switch/Heartbeat (Base+2) | Switchboard → ECU | 20 Hz (default) | Existing device, fully mapped below. ECU-only (not read by RealDash). |
| 0x643 | 1603 | Switchboard Low-Side Output Control (Base+3) | **ECU** → Switchboard | event | INPUT — source = **ECU** (PCLink aux→CAN TX); outputs unused/LED-only — master-design §9 |
| 0x644+ | 1604+ | — | — | — | Available if a second switchboard is added (Base ID configurable) |

---

## 2. Section A — ECU → Cluster TX (Immutable, coded-complete)

Source: `link_g4x_can_setup.lcs`, `CANBUS-LINK-G4X-CONFIG.md`. All streams are **Custom type, BigEndian, non-multiplexed**, on the 1 Mbit/s `CANModule Index="1"` (CAN1).

### 0x3E8 — Engine Fast (CycleTime 10ms)
| Bytes | Field | Type | Scale | Offset | Notes |
|---|---|---|---|---|---|
| 0–1 | Engine Speed (RPM) | uint16 BE | 1 | 0 | |
| 2–3 | MAP (absolute) | uint16 BE | 1 | 0 | Use **MAP**, not MGP. ~100 at idle, never negative. Firmware subtracts 100 → gauge boost. |
| 4 | ECT (Coolant Temp) | uint8 | 1 | -50 | °C |
| 5 | IAT (Manifold) | uint8 | 1 | -50 | °C |
| 6 | Oil Temp | uint8 | 1 | -50 | °C |
| 7 | — | — | — | — | **Free (1 byte)** |

### 0x3E9 — Speed / Press / Ign (CycleTime 10ms)
| Bytes | Field | Type | Scale | Offset | Notes |
|---|---|---|---|---|---|
| 0–1 | Ignition Angle | uint16 BE | 0.1 | -100 | degrees |
| 2 | Vehicle Speed | uint8 | 1 | 0 | |
| 3–4 | Oil Pressure | uint16 BE | 1 | 0 | kPa — widened from 1 byte (1 byte capped at 37 PSI) |
| 5–6 | Fuel Pressure | uint16 BE | 1 | 0 | kPa — widened from 1 byte |
| 7 | — | — | — | — | **Free (1 byte)** |

### 0x3EA — Lambda (CycleTime 10ms)
| Bytes | Field | Type | Scale | Offset | Notes |
|---|---|---|---|---|---|
| 0–1 | Lambda 1 | uint16 BE | 0.001 | 0 | derived from CAN-Lambda (0x3B6) internally by ECU |
| 2–7 | — | — | — | — | **Free (6 bytes)** |

### 0x3EB — Gear / Fuel (CycleTime 50ms)
| Bytes | Field | Type | Scale | Offset | Notes |
|---|---|---|---|---|---|
| 0 | Gear Position | uint8 | 1 | 0 | 0=N, 1-6, 7=R (firmware maps 7→-1) |
| 1 | Fuel Level | uint8 | 1 | 0 | % |
| 2–7 | — | — | — | — | **Free (6 bytes)** |

### 0x3EE — Engine Protect (CycleTime 50ms)
Drives the full-screen warning overlay (max 3 shown, priority-ordered). 0 = OK, nonzero = active.

| Bytes | Field | Type | Notes |
|---|---|---|---|
| 0 | Knock | uint8 | |
| 1 | Ignition Cut | uint8 | |
| 2 | Fuel Cut | uint8 | |
| 3 | Boost Cut | uint8 | |
| 4 | Sensor Error | uint8 | |
| 5 | Throttle Error | uint8 | |
| 6–7 | — | — | **Free (2 bytes)** |

> **Free-byte note:** the 18 free bytes above (0x3E8 byte7, 0x3E9 bytes5-7, 0x3EA bytes2-7, 0x3EB bytes2-7, 0x3EE bytes6-7) are **not assigned in this allocation**. Using them requires the firmware "Adding a channel later" procedure (dash_data.h → canbus.c/dash_data.c/ui_*.c → .lcs/.json) across all three cluster boards — out of scope for the current pass. They remain available for a future firmware revision.

---

## 3. Section B — Cluster → ECU TX (Immutable, coded-complete)

Source: `canbus.h` (`canbus_tx_selection(uint32_t id, uint8_t index)` — called only from `inputs.c` on confirmed button press, never from a timer).

| CAN ID | Name | DLC | Payload |
|---|---|---|---|
| 0x3EC | Boost map selection | 1 | Byte0 = selected boost-map index (0-based) |
| 0x3ED | TC slip-angle/setting selection | 1 | Byte0 = selected TC setting index (0-based) |

Both are **event-driven** (sent once on selection change), not periodic.

---

## 4. Section C — Link CAN-Lambda (Reserved)

| CAN ID | Name | Notes |
|---|---|---|
| 0x3B6 (950) | CAN-Lambda built-in broadcast | Native PCLink receive mode, tuned for Bosch LSU 4.9. Consumed internally by the ECU to compute Lambda 1 (re-broadcast on 0x3EA byte0-1). Present on the physical bus — **reserve this ID, do not reassign**. |

---

## 5. Section D — ECUMaster CAN Switch Board V3 (Base ID = 0x640)

Source: switchboard manual v2.1 (FW 3.0+). "CAN Switch Board uses Base ID + 0 to Base ID + 2 as output IDs and Base ID + 3 as an input ID." Default transmission rate 20 Hz.

### 0x640 (Base+0) — Analog Inputs 1–4 (OUTPUT)
| Bytes | Field | Type | Range | Notes |
|---|---|---|---|---|
| 0–1 | Analog Input 1 | uint16 BE | 0–5000 mV | |
| 2–3 | Analog Input 2 | uint16 BE | 0–5000 mV | |
| 4–5 | Analog Input 3 | uint16 BE | 0–5000 mV | |
| 6–7 | Analog Input 4 | uint16 BE | 0–5000 mV | |

### 0x641 (Base+1) — Analog Inputs 5–8 (OUTPUT)
| Bytes | Field | Type | Range | Notes |
|---|---|---|---|---|
| 0–1 | Analog Input 5 | uint16 BE | 0–5000 mV | |
| 2–3 | Analog Input 6 | uint16 BE | 0–5000 mV | |
| 4–5 | Analog Input 7 | uint16 BE | 0–5000 mV | |
| 6–7 | Analog Input 8 | uint16 BE | 0–5000 mV | |

### 0x642 (Base+2) — Rotary / Switch / Analog-State / Low-Side / Heartbeat (OUTPUT)
| Byte | Field | Notes |
|---|---|---|
| 0 | Rotary 1 (bits 4-7) / Rotary 2 (bits 0-3) | nibble-packed |
| 1 | Rotary 3 (bits 4-7) / Rotary 4 (bits 0-3) | nibble-packed |
| 2 | Rotary 5 (bits 4-7) / Rotary 6 (bits 0-3) | nibble-packed |
| 3 | Rotary 7 (bits 4-7) / Rotary 8 (bits 0-3) | nibble-packed |
| 4 | SW_MASK | bit0=Switch1 ... bit7=Switch8 |
| 5 | AS_MASK | bit0=AnalogState1 ... bit7=AnalogState8 (<2V→0, >3V→1) |
| 6 | LS_MASK | bit0=LowSide1 ... bit3=LowSide4 |
| 7 | Heartbeat | uint8, increments every sent message (0-255, wraps) |

**SW_MASK assignment (from project docx, consistent with manual's bit ordering):**

| Bit | Switch | Function |
|---|---|---|
| 0 | Switch 1 | Evaporator Core State |
| 1 | Switch 2 | AC Request |
| 2 | Switch 3 | Cruise Control Active |
| 3 | Switch 4 | Cruise Set / Accelerate |
| 4 | Switch 5 | Cruise Resume / Decelerate |
| 5-7 | Switch 6-8 | **Unassigned — available** |

### 0x643 (Base+3) — Low-Side Output Control (INPUT, host → switchboard)

> **Source = ECU** (Link G4X PCLink aux output → CAN TX), decided 2026-06-14. Switchboard outputs are currently unused (likely LED-only when used); the cluster does **not** transmit 0x643. See master-design §9.
| Byte | Field | Notes |
|---|---|---|
| 0 | L1 control | DLC ≥ 4 required |
| 1 | L2 control | |
| 2 | L3 control | |
| 3 | L4 control | |
| 4-7 | 0 | reserved |

---

## 6. Section E — New RealDash-Only TX Streams (0x3EF–0x3F1)

All new streams follow the existing convention: **Custom type, BigEndian, non-multiplexed**, broadcast on the shared 1 Mbit/s bus. These require new PCLink "Custom Stream" outputs configured on the Link G4X — see Task #9.

### 0x3EF — Drive Assist & Status (CycleTime 50ms)
| Bytes | Field | Type | Scale | Offset | Source |
|---|---|---|---|---|---|
| 0–1 | Target Lambda | uint16 BE | 0.001 | 0 | ECU (new PCLink broadcast — target AFR table value) |
| 2 | Throttle % | uint8 | 1 | 0 | ECU (TPS, new PCLink broadcast) |
| 3 | TC Setting | uint8 | 1 | 0 | **ECU echo** — the ECU receives the cluster's TC selection on 0x3ED and re-broadcasts it here (no cluster↔RealDash crossover) |
| 4 | TC Intervention % | uint8 | 1 | 0 | ECU (new PCLink broadcast — torque/ignition cut %) |
| 5 | Boost Map Index | uint8 | 1 | 0 | **ECU echo** — the ECU receives the cluster's boost-map selection on 0x3EC and re-broadcasts it here |
| 6 | Cruise Control State | uint8 (enum) | 1 | 0 | ECU (new PCLink broadcast). 0=Off, 1=Standby, 2=Set/Active, 3=Resume, 4=Override |
| 7 | AC Status | uint8 (enum) | 1 | 0 | ECU (new PCLink broadcast, post-VDI). 0=Off, 1=Requested, 2=Compressor Engaged, 3=Fault |

> **Bytes 3 & 5 are ECU echoes.** RealDash and the cluster share no CAN traffic directly — everything RealDash sees comes from the ECU. The cluster transmits its boost-map and TC selections to the ECU on **0x3EC** (map index) and **0x3ED** (TC index); the ECU receives those into channels and re-broadcasts them to RealDash in 0x3EF bytes 5 and 3. PCLink config required: receive 0x3EC/0x3ED into channels, then place those channels in 0x3EF (Task #9).

### 0x3F0 — Extended Sensors (CycleTime 100ms)
| Byte | Field | Type | Scale | Offset | Notes |
|---|---|---|---|---|---|
| 0 | Fuel Temp | uint8 | 1 | -50 | °C, matches ECT/IAT/OilTemp convention |
| 1 | Engine Load % | uint8 | 1 | 0 | |
| 2–3 | Coolant Pressure | uint16 BE | 1 | 0 | kPa — widened to 2 bytes for headroom (1 byte capped 255 kPa) |
| 4 | Ethanol % | uint8 | 1 | 0 | flex-fuel sensor |
| 5 | Charge-Pipe IAT | uint8 | 1 | -50 | °C, post-intercooler (distinct from 0x3E8 manifold IAT) |
| 6 | Turbo Speed ÷1000 | uint8 | 1000 | 0 | RPM, 1k resolution (u8 -> 0-255,000), e.g. 150 = 150,000 RPM |
| 7 | Trigger Error Count | uint8 | 1 | 0 | rolling/cumulative sync-error count |

> **Cabin Temp removed (2026-06-28):** dropped to fit 2-byte Coolant Pressure (frame was full at 8 bytes). Cabin temp is **no longer available via the ST185 RealDash inputs** — RealDash does not read the switchboard 0x640 frame directly. To restore cabin temp, add a new frame 0x3F2 (with a matching RealDash frame/value) rather than reading 0x640.

### 0x3F1 — IMU & Extended Warnings (CycleTime 50ms)
| Bytes | Field | Type | Scale | Offset | Notes |
|---|---|---|---|---|---|
| 0–1 | Accel X ×10 | int16 BE (signed) | 0.1 | 0 | g-force |
| 2–3 | Accel Y ×10 | int16 BE (signed) | 0.1 | 0 | g-force |
| 4–5 | Accel Z ×10 | int16 BE (signed) | 0.1 | 0 | g-force |
| 6 | Extended Warnings Bitmask | uint8 | — | — | bit0=Flat Shift Active, bit1=Radiator Fan On, bit2=Low Fuel Warning, bit3=High Coolant Pressure, bit4=Low Oil Pressure (secondary threshold), **bit5=Switchboard Comm Fault (ECU-set; see master §6)**, bits6-7=spare |
| 7 | — | — | — | — | reserved (0x00) |

> **Note on docx's "AC/cruise/flat-shift/radiator-fan status bitmask":** AC and cruise status are now given full enum bytes (0x3EF bytes 6-7) for richer state than a single bit. Flat-shift and radiator-fan status move into the Extended Warnings bitmask above (0x3F1 byte6, bits 0-1). This supersedes the docx's single packed-bitmask proposal.

---

## 7. Conflicts A/B/C — Documentation & Resolution

### Conflict A — CAN ID collision (docx vs. coded firmware)
**Docx proposal:** 0x3E8 as a multiplexed "Link Generic Dash" stream, plus 0x3E9–0x3EC as "Custom Stream 1-4" (little-endian).

**Actual coded firmware:** 0x3E8/0x3E9/0x3EA/0x3EB are non-multiplexed **Custom/BigEndian** streams (Engine Fast / Speed-Press-Ign / Lambda / Gear-Fuel) per `link_g4x_can_setup.lcs`; 0x3EC is the cluster's boost-map-selection TX (cluster→ECU); 0x3EE (Engine Protect) is entirely absent from the docx's table.

**Resolution:** The docx's 0x3E8–0x3EC architecture **cannot be implemented as written** — it collides with immutable, coded-complete firmware. Its useful payloads (fuel temp, engine load%, TC intervention%, coolant pressure, ethanol%, charge-pipe IAT, cabin temp, turbo speed, accel XYZ, trigger error count, AC/cruise/flat-shift/radiator-fan status) are **re-homed to 0x3EF–0x3F1** (Section E above), all BigEndian/Custom to match the existing convention.

### Conflict B — Bidirectional vs. listen-only
**Docx assumption:** the ESP32 cluster is "completely passive" / listen-only on the CAN bus.

**Actual coded firmware:** `canbus.h` configures `TWAI_MODE_NORMAL` (bidirectional) and exposes `canbus_tx_selection()`, actively used for 0x3EC and 0x3ED.

**Resolution:** The cluster is a full bus participant — it transmits 0x3EC/0x3ED to the ECU. But a CAN ID has exactly one transmitter, so the cluster does **not** inject into the ECU-owned 0x3EF, and RealDash never reads cluster frames directly (no cluster↔RealDash crossover). The ECU receives 0x3EC/0x3ED and **echoes** the selected boost map / TC setting to RealDash in 0x3EF bytes 5 / 3.

### Conflict C — "Generic Dash" format assumption
**Docx assumption:** the ESP32 expects Link's standard multiplexed "Generic Dash" format on 0x3E8.

**Actual coded firmware:** uses Link's **"Custom" stream type** with bespoke BigEndian byte layouts (see Section A), not the generic multiplexed dash format.

**Resolution:** All new streams (0x3EF–0x3F1) follow the **Custom/BigEndian** convention already established, for consistency with the existing decoder in `canbus.c`.

---

## 8. Summary of New Allocations (for Task #9)

| Action | Detail |
|---|---|
| Add 3 new Custom/BigEndian streams to `link_g4x_can_setup.lcs` / `.json` | 0x3EF (50ms), 0x3F0 (100ms), 0x3F1 (50ms) — see Section E for field layouts |
| Configure ECUMaster Switch Board V3 | Set CAN speed to 1000 kbps (non-default); confirm Base ID = 0x640; verify SW_MASK assignments match Section 5 |
| Cluster firmware (`canbus.c`/`dash_data.c`) | **No changes** — cluster displays are unchanged; it keeps decoding 0x3E8–0x3EE and sending 0x3EC/0x3ED. 0x3EF/0x3F0/0x3F1 are ECU→RealDash only |
| RealDash XML | **Done** — `link_g4x_realdash.xml` defines `<frame id="1007/1008/1009">` (0x3EF–0x3F1) as valid RealDash CAN v2 (BigEndian, per-bit warning decode). 0x640–0x642 excluded (ECU echoes display-relevant values). Dashboard layout: `REALDASH-LAYOUT.md` |
| 0x643 source = **ECU** | L1–L4 control transmitted by ECU (PCLink aux output → CAN TX); switchboard outputs unused for now (likely LED-only). Cluster has no 0x643 TX role — master-design §9 |
