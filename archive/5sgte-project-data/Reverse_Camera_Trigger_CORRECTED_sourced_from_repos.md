<!-- RETIRED 2026-09-06. Describes the superseded "reverse switch -> ECU DI4 direct" decision.
     Current: reverse is on the ECUMaster switchboard over CAN; DI 3-6 are ABS wheel speed.
     Authoritative for ECU I/O: XTREMEX-IO-TABLE.html -->

# Reverse-Camera Trigger — CORRECTED, Sourced from Dan's Actual Repos

**Supersedes the earlier "Reverse-Camera Trigger for ST185 5S-GTE Build" artifact**, which was built from generic Link documentation because the GitHub repos weren't reachable at the time. This version is sourced directly from `living-relation/st185-link-ecu-config`, `living-relation/center-cluster-esp32-p4`, and Google Drive.

## TL;DR

- **ECU = Link G4X XtremeX.** Confirmed across all three repos. The Google Drive "FuryX" PDFs (`Link G4X FuryX Trigger & Ignit 1.pdf`, `FuryX Engine Harness Netlist, 1.pdf`) are unrelated/stray documents — not this build.
- **No reverse switch on the IO table.** DI4–DI10 (7 channels) are marked spare/unassigned in `XTREMEX-IO-TABLE.md`. Plenty of room.
- **A native CAN "Gear Position" channel already exists** (0x3EB byte 0: 0=N, 1–6, 7=R → firmware remaps to −1) and is already decoded by the center cluster. It's just not fed by anything yet — no reverse switch is wired.
- **Both displays sit on one shared CAN bus** (ECU + center cluster + ECUMaster switchboard + Pi5/RealDash, all daisy-chained, 1 Mbit/s). RealDash is a passive listener already on this bus, but its current channel-description XML only maps frames 0x3EF–0x3F1 — gear isn't in there.
- **Recommendation:** wire the physical reverse-light switch to a spare DI (DI4 is a clean pick — currently labeled "Launch/spare"), have PCLink set Gear Position = 7 when it's active, then add camera-trigger logic in software on each display. No other new hardware needed.

## Sources (all fetched directly, dated/versioned)

| Source | What it establishes |
|---|---|
| `github.com/living-relation/st185-link-ecu-config` (41 commits, public) | Authoritative CAN + IO config repo. README: *"This repo contains everything on the CAN bus side... Cluster firmware is frozen."* |
| -> `XTREMEX-IO-TABLE.md` | Full DI/AnVolt/Trigger/Aux assignment table for the XtremeX |
| -> `CAN-BUS-ID-ALLOCATION-TABLE.md` | Byte-level layout for every CAN frame, "Immutable — coded-complete" status per frame |
| -> `WIRING.md` | Physical topology: 4-node shared CAN bus, Pi5 wiring via USB-CAN adapter |
| `github.com/living-relation/center-cluster-esp32-p4` (50 commits, public) | Confirms XtremeX again; center cluster firmware decodes 0x3E8–0x3EE |
| `github.com/research655/RD-st185-link-ecu-config` | Fork of the same `st185-link-ecu-config` repo — identical content, no new information |
| Google Drive: `center-*.md`, `board_config.h`, `TrackCluster ECU Dashboard.html`, etc. (TrackCluster project folder) | Corroborates the same 4-node topology and gear-channel decode; **also contains stray FuryX docs unrelated to this build** |

## Findings

### 1. ECU model — resolved
Your Drive has a "Link G4X FuryX" engine harness spec (`Link G4X FuryX Trigger & Ignit 1.pdf`, dated modified 2026-01-23) that describes a different vehicle framing ("Weekend autocross/track + street," "top-mount turbo"). This does **not** match your actual, current, actively-committed repos, which say XtremeX consistently and specifically for the ST185 3S-GTE TrackCluster build. Treat the FuryX PDFs as stale/unrelated — possibly an earlier alternate-ECU exploration that never became the real build.

### 2. XtremeX I/O table — current state (`XTREMEX-IO-TABLE.md`)

**Digital Inputs:**

| DI | Assignment | Status |
|---|---|---|
| DI 1 | Flex-fuel sensor (frequency) | confirm (proposed) |
| DI 2 | Clutch switch | confirm (proposed) |
| DI 3 | Brake switch | confirm (proposed) |
| DI 4 | Launch / **spare** | TBD |
| DI 5 | **spare** | TBD |
| DI 6 | **spare** | TBD |
| DI 7 | **spare** | TBD |
| DI 8 | **spare** | TBD |
| DI 9 / CAN2-L | **spare DI** (CAN2 deliberately unused) | TBD |
| DI 10 / CAN2-H | **spare DI** (CAN2 deliberately unused) | TBD |

No reverse switch anywhere in this table. **Caveat:** this table is explicitly an unlocked draft — its own closing note says *"I'll fill each row as you confirm it, then lock the table."* Rows marked "confirm" or "TBD" aren't final. Treat "DI4–DI10 spare" as the best current answer, not a locked spec.

**Discrepancy to flag:** stored memory has DI 5 (B loom, Grey/White) assigned to the BorgWarner turbo speed sensor. The current table shows DI5 as spare, and turbo speed instead appears as a CAN value (`0x3F0` byte 6, "Turbo Speed / 1000"). Worth a quick check on your end — either the memory is outdated, or turbo speed moved to an analog/frequency path that gets echoed into that CAN frame some other way (possibly via the ECUMaster switchboard, which also handles analog/digital inputs). Memory hasn't been changed pending your confirmation.

### 3. CAN bus architecture — 4 nodes, one shared bus

From `WIRING.md` section 7 and `CAN-BUS-ID-ALLOCATION-TABLE.md` section 1:

```
Link G4X XtremeX ECU  --CANH/CANL--  center-cluster-esp32-p4  --  ECUMaster CAN Switch Board V3  --  Pi5 (RealDash)
   (120ohm term, END A)                (SN65HVD230 transceiver)         (Base ID 0x640)              (USB-CAN adapter,
                                                                                                        120ohm term, END B)
```

- Single bus, 1 Mbit/s, ISO 11898-2, BigEndian custom streams.
- **The Pi (RealDash) is a passive listener on this exact bus** via a USB-CAN adapter (CANable or PCAN), not a separate network. It physically receives every frame the ECU and cluster send, including 0x3EB (Gear).
- Frame ownership:
  - `0x3E8`–`0x3EB`, `0x3EE`: ECU -> Cluster (Engine Fast, Speed/Press/Ign, Lambda, **Gear/Fuel**, Engine Protect)
  - `0x3EC`/`0x3ED`: Cluster -> ECU (driver selections)
  - `0x3EF`–`0x3F1`: ECU -> RealDash only (Drive Assist & Status, Extended Sensors, IMU & Warnings) — **added specifically because RealDash and the cluster don't share CAN traffic directly**
  - `0x640`–`0x643`: ECUMaster switchboard <-> ECU

### 4. The Gear Position CAN channel (0x3EB byte 0)

```
Bytes  Field           Type    Scale  Offset  Notes
0      Gear Position   uint8   1      0       0=N, 1-6, 7=R (firmware maps 7 -> -1)
1      Fuel Level      uint8   1      0       %
2-7    --              --      --     --      Free (6 bytes)
```

Status: **"Immutable — coded-complete."** This is a real, working channel — the center cluster's firmware already decodes it into its `dash_data_t.gear` field. What's missing is the *input side*: nothing currently sets Gear Position to 7, because no reverse switch exists yet in the wiring or PCLink config.

### 5. Per-display status

**Center cluster (ESP32-P4):**
- Already decodes 0x3EB (Gear) — no new CAN work needed once the switch/PCLink side is done.
- `REALDASH-LAYOUT.md`/TrackCluster docs describe the current UI (tach, shift-lights, gear glyph, odometer) with **no camera page** — this is new UI work, not a config change.
- Adding a reverse-camera view would mean: a new LVGL screen/page bound to a USB camera feed, shown when `dash.gear == -1`.

**RealDash (Pi):**
- Physically on the bus already, but `link_g4x_realdash.xml` only defines channels for frames 0x3EF/0x3F0/0x3F1. **Gear (0x3EB) is not currently in RealDash's channel list.**
- Fix is config-only: add a channel definition for 0x3EB byte 0 to the XML (BigEndian, matching the existing convention), reimport into RealDash, then map it to *Body Electronics -> Gear* per RealDash's documented input-mapping feature.
- Then add a RealDash trigger: gear = R (-1) -> switch to camera page — this is a standard, documented RealDash capability.
- `REALDASH-LAYOUT.md` currently describes a single-page 800x480 engineering dash with "no media page" — so the camera page doesn't exist yet there either; it's new layout work, not just a channel add.

### 6. Recommended implementation path

1. **Wire the reverse-light switch to a spare DI.** DI4 (currently "Launch/spare") is a reasonable pick, or any of DI5–DI10. Confirm in PCLink whether CAN2 is still intentionally disabled before touching DI9/DI10.
2. **In PCLink, drive Gear Position to 7 when that DI is active.** Exact mechanism (direct GP runtime override vs. configuring Link's native RPM/Speed gear detection with a reverse ratio) isn't documented in your repos — this needs to be worked out in PCLink itself, not assumed.
3. **Center cluster:** add a camera-trigger UI state (new LVGL page) bound to `dash.gear == -1`. Pure firmware change, no new CAN.
4. **RealDash:** add a 0x3EB-byte-0 channel to `link_g4x_realdash.xml`, map it to *Body Electronics -> Gear*, add a trigger rule (gear = R -> camera page). Pure config change, no new wiring — the Pi already sees the frame.
5. **Update `XTREMEX-IO-TABLE.md`** once the switch DI is chosen and confirmed, since the table is explicitly unlocked/in-progress.

## Open questions (unresolved — need your input, not assumptions)

1. Which DI do you want for the reverse switch — DI4, or another spare?
2. Confirm/resolve the turbo-speed-sensor DI5 discrepancy against current PCLink config.
3. Confirm the PCLink mechanism for setting Gear Position = 7 from a DI (direct write vs. reverse-ratio gear detection) — this determines exactly how "wire switch -> CAN gear=7" gets implemented in PCLink.
4. Do you want the reverse-camera page added to the center cluster, RealDash, or both? (Docs suggest neither currently has a camera page built.)
