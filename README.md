# st185-link-ecu-config

Link G4X XtremeX ECU, RealDash, and ECUMaster CAN Switch Board V3 configuration for the 1993 Toyota Celica GT-Four ST185 (3S-GTE) TrackCluster build.

## Scope

This repo contains everything on the **CAN bus side** — ECU config, RealDash XML, and switchboard setup. It is intentionally separate from the ESP32 cluster firmware repos because nothing here requires changing cluster code.

Cluster firmware is frozen. All files in this repo must be compatible with the cluster **as-is**.

## 4-Node CAN Bus (1 Mbit/s, BigEndian)

| Node | ID Range | Role |
|---|---|---|
| Link G4X XtremeX ECU | 0x3E8–0x3F1 TX, 0x3EC/0x3ED RX | Engine management — bus master |
| center-cluster-esp32-p4 | 0x3EC/0x3ED TX, all others RX | Gauge cluster — listens + sends driver selections |
| ECUMaster CAN Switch Board V3 | 0x640–0x642 TX, 0x643 RX | Analog/digital inputs, low-side outputs |
| Raspberry Pi 5 (RealDash) | passive listener (ch1) | Dashboard display — listen-only |

## Files

| File | Purpose |
|---|---|
| `link_g4x_can_setup.lcs` | PCLink-importable CAN TX stream config. v1.1 has 2 scale bug-fixes. |
| `link_g4x_can_setup.json` | Canonical CAN config twin — authoritative source of truth for all IDs, offsets, scales, and notes. |
| `link_g4x_realdash.xml` | RealDash CAN **channel-description** XML v2 — the 3 ECU→RealDash frames (0x3EF–0x3F1), valid/importable, BigEndian, with bit-decoded warnings and named `ST185:` inputs. |
| `REALDASH-LAYOUT.md` | RealDash **dashboard layout design** — buildable spec for a 2-page dash (single 800×480 engineering page with 3D tiles, LED warnings + strobing alarms + cruise-mode readout, and a media-player page), plus simple install steps. Binds to the inputs in `link_g4x_realdash.xml`. |
| `realdash-demo.html` | **Browser preview** of the layout above (not a `.rd` file) — open in any browser to see both pages, the 3D tiles, glowing/strobing LED warnings, and simulated live values. Buttons toggle DASH/MEDIA and the warning strobe. |
| `ECUMASTER_SWITCHBOARD_SETUP.md` | Step-by-step ECUMaster CAN Switch Board V3 configuration guide. |
| `CAN-BUS-MASTER-DESIGN.md` | Architecture, PCLink User Streams, fault tolerance, 4-node topology. |
| `CAN-BUS-ID-ALLOCATION-TABLE.md` | Master ID allocation table — all byte layouts, sections A–E. |
| `CANBUS-LINK-G4X-CONFIG.md` | PCLink setup guide: module settings, stream import, User Stream wiring. |
| `WIRING.md` | Physical wiring reference — cluster boards + 4-node CAN bus topology. |

## Import Checklist (PCLink, when ECU is available)

1. Set CAN Module 2 → **1 000 000 bps**, Custom stream type, BigEndian.
2. File → Open → `link_g4x_can_setup.lcs` — verify all 8 TX channels appear.
3. Add User Streams: 0x640 bytes0-1 → GP Temp1; 0x642 byte4 bits0-4 → VDI1-5.
4. Set CAN Receive Timeout: 200 ms on frames 0x640 / 0x641 / 0x642.
5. Confirm ECU echoes TC Setting (0x3EF byte3) and Boost Map Index (0x3EF byte5) back to 0x3ED / 0x3EC.

## Known Fixes vs. Previous Version

| Frame | Parameter | Old Scale | Correct Scale | Effect of Bug |
|---|---|---|---|---|
| 0x3EF | Lambda Target | 1000 | **0.001** | Transmitted value was always 0 (truncated) |
| 0x3F1 | Accel X/Y/Z | 10 | **0.1** | Transmitted value was always 0 (truncated) |

See `link_g4x_can_setup.json` for the definitive scale derivations.
