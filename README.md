# st185-link-ecu-config

Link G4X XtremeX ECU, RealDash, and ECUMaster CAN Switch Board V3 configuration for the 1993 Toyota Celica GT-Four ST185 (5S-GTE) TrackCluster build.

## Scope

This repo contains everything on the **CAN bus side** — ECU config, RealDash XML, and switchboard setup. It is intentionally separate from the ESP32 cluster firmware repos because nothing here requires changing cluster code.

Cluster firmware is frozen. All files in this repo must be compatible with the cluster **as-is**.

## Related repos

- **[center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4)** — the gauge cluster firmware. Its `main/canbus.c` is the decode truth for the frames the cluster reads (0x3E8–0x3EB, 0x3EE); its [`CANBUS-ENCODE-DECODE-REFERENCE.html`](https://github.com/living-relation/center-cluster-esp32-p4/blob/main/CANBUS-ENCODE-DECODE-REFERENCE.html) is the readable reference derived from it (linked, not copied). Any change to CAN framing, IDs, or wiring in this repo must be checked against that repo for compatibility — see `CAN-BUS-MASTER-DESIGN.md`.

## 5-Node CAN Bus (1 Mbit/s, BigEndian)

| Node | ID Range | Role |
|---|---|---|
| Link G4X XtremeX ECU | 0x3E8–0x3EB, 0x3EE–0x3F1 TX, 0x643 TX (once an output is used); RX 0x3B6, 0x640–0x642, 0x3EC/0x3ED (cluster encoder selections) | Engine management — bus master |
| Link CAN-Lambda | 0x3B6 TX (0x3BE RX) | External wideband module — physically on the bus |
| [center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4) | 0x3EC/0x3ED TX, all others RX | Gauge cluster — listens + sends driver selections |
| ECUMaster CAN Switch Board V3 | 0x640–0x642 TX, 0x643 RX | Analog/digital inputs, low-side outputs |
| Raspberry Pi 5 (RealDash) | RX 0x3EB (gear byte only), 0x3EF–0x3F1 | Dashboard display — listen-only |

## Files

| File | Purpose |
|---|---|
| `link_g4x_can_setup.lcs` | PCLink-importable CAN TX stream config. v1.1 has 2 scale bug-fixes. |
| `link_g4x_can_setup.json` | Canonical ECU wire contract for 0x3E8–0x3F1 (IDs, offsets, scales, notes). Scales are PCLink **encode** form (raw = value × scale + offset); the `.lcs`, ID table and `bench/frames.py` use **decode** form. |
| `switchboard_frames.json` | ECUMaster CSB3 frames 0x640–0x643 (layout per the CSB3 manual v2.1). |
| `bench/check_parity.py` | Checks the JSON, `.lcs`, ID table, `frames.py`, RealDash XML, sender UI and `switchboard_frames.json` all agree. Runs in CI. |
| `link_g4x_realdash.xml` | RealDash CAN **channel-description** XML v2 — the 3 ECU→RealDash frames (0x3EF–0x3F1) plus the gear byte of 0x3EB (reverse-camera switch), valid/importable, BigEndian, with bit-decoded warnings and named `ST185:` inputs. |
| `CANBUS-ENCODE-DECODE-REFERENCE.html` | Pointer page only: links to the cluster repo's encode/decode reference and its `main/canbus.c`. No cluster file is copied into this repo; `bench/check_parity.py` reads the cluster source read-only in CI. |
| `REALDASH-LAYOUT.md` | RealDash **dashboard layout design** — buildable spec for the **single-page** blue/chrome 800x480 engineering dash (4x4 tile grid + strobing warning strip; no media page). Binds to `link_g4x_realdash.xml`. |
| `docs/harness/wirelist/*-wirelist.csv` | **Wiring source of truth** (DECISIONS R206) — every wire, pin, splice, end, mate and net. New wiring facts go here first. |
| `sot/channels.csv` | The ECU channel settings (type, pull-up, tune / CAN data) and ECU pin assignments, checked against the wire lists both ways. |
| `XTREMEX-IO-TABLE.html` | Visual face of `sot/channels.csv`: channel plan, pin budget, and a generated pin map of every ECU pin. `docs/harness/sync_io_table.py --check` fails if it disagrees with the CSV. Open in a browser. |
| `docs/harness/rebuild/*.harness` | **The physical harnesses, one per file** (harness.design v1.2, DECISIONS R111; ownership in docs/harness/interfaces.json) — what gets built. See `docs/harness/README.md`. |
| `docs/harness/check_all.py` | Runs every harness gate (SoT, IO table, lint, mating, shields, pin names, wire lists, buy list). Must pass before every commit. |
| `docs/harness/NEED-TO-BUY.md` | Generated buy list. Never hand-edit — regenerate with `docs/harness/buylist.py`; `check_all.py` fails if they are stale. |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | OEM landing facts with factory EWD snips: where every ex-J/B2 / R/B load lands now that the OEM engine-bay boxes are removed (R12, §5.4). The wire lists own the wiring. |
| `ECUMASTER_SWITCHBOARD_SETUP.md` | Step-by-step ECUMaster CAN Switch Board V3 configuration guide. |
| `CAN-BUS-MASTER-DESIGN.md` | Architecture, PCLink User Streams, fault tolerance, 5-node topology. |
| `CAN-BUS-ID-ALLOCATION-TABLE.md` | Master ID allocation table — all byte layouts, sections A–E. |
| `CANBUS-LINK-G4X-CONFIG.md` | PCLink setup guide: module settings, stream import, User Stream wiring. |
| `WIRING.md` | Physical wiring reference — cluster boards + 5-node CAN bus topology. |
| `tune/engine_constants.yaml` | Machine-readable engine constants (bore, cams, trigger, injectors, turbo, fuel, targets). Engine calibration only — not an I/O source. |
| `tune/tables/` | PCLink table seeds — VE (93 + E85), ignition base, injector dead time. Conservative placeholders, not dyno data. See `tune/README.md`. |
| `FUEL-SYSTEM.md` | Fuel system reference — AN hose sizing and pump capacity notes. Not part of the CAN bus contract. |
| `docs/harness/redesign/DECISIONS.md` | Decision record and **the one home for every binding rule Daniel has set** (section "Binding rules from Daniel"). |
| `docs/research-hub.html` | Index of everything under `docs/` plus interactive parts tables (on-hand BOM, harness buy list, enclosure BOMs). Open in any browser. The "Regenerate research hub" Action runs `python docs/build-research-hub.py` on PRs that touch `docs/**` and commits the HTML on `main` only — do not commit the HTML yourself. |

## Import Checklist (PCLink, when ECU is available)

1. Set CAN Module 1 (CAN1) → **1 000 000 bps**, Custom stream type, BigEndian.
2. File → Open → `link_g4x_can_setup.lcs` — verify all 8 TX channels appear.
3. Switchboard receive (already in the `.lcs`, 2026-10-14): 0x640 bytes 2-3 Cruise Stalk mV; 0x642 byte4
   bit 2 → VDI3 (cruise main), bit 5 → VDI6 (clutch), bit 6 → VDI7 (brake), bit 7 → VDI8 (reverse).
   Confirm they imported (or enter them by hand with the same values).
4. CAN Receive Timeout: 200 ms on 0x640 / 0x642, value 0 on timeout (in the `.lcs`).
5. Echo target: 0x3EF byte 3 (TC Setting) and byte 5 (Boost Map Index) are meant to carry the cluster's
   0x3ED / 0x3EC selections, re-broadcast by the ECU. The ECU **receives** 0x3EC/0x3ED (Daniel,
   2026-10-03) - set up the two receive channels at the end of the `.lcs` (DLC 1, byte 0 = index).

## Scale forms

Scales in the `.lcs` are **decode** form: value = raw × Scale + Offset.

`link_g4x_can_setup.json` holds the same fields in **encode** form (e.g. Lambda Target scale 1000 there
= 0.001 here). `bench/check_parity.py` checks the two agree.
