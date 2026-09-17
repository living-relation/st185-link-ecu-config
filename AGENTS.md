# AGENTS.md

> ## Before any wiring or CAN change — binding on every agent
>
> Read **`docs/RECONCILIATION-RULES.md`**. Two rules, both non-optional:
>
> 1. **Wiring** — a change to one wiring document is not done until it is checked against
>    the source-of-truth chain and **every other wiring surface**, including ones you did
>    not edit. `XTREMEX-IO-TABLE.html` is the pin source of truth; everything else is a
>    face of it.
> 2. **CAN** — a change on any device must be reconciled against **all** of them: Link ECU,
>    center cluster, RealDash, ECUMaster CSB3. This crosses repo boundaries. The cluster
>    firmware is frozen and outranks everything; on conflict, the other device changes.
>
> Link CAN-Lambda is on CAN bus 1. CAN bus 2 is unused and its ECU pins are free.

## Scope
- This repo is CAN configuration + bench/tooling for ST185 TrackCluster.
- Primary code paths are `bench/`, `apps/trackcluster-can-sender/`, and `rd-build/tools/`.
- Primary contracts are `link_g4x_can_setup.json` and `link_g4x_realdash.xml`.

## Source Of Truth
- CAN IDs, offsets, scaling: `link_g4x_can_setup.json`.
- Architecture and allocation: `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`.
- Bench behavior: `bench/frames.py`, `bench/can_bench.py`, `BENCH-TEST.md`.
- RealDash channel definitions: `link_g4x_realdash.xml`.
- ECU Superseal I/O (pins, pull-ups, drive types): `XTREMEX-IO-TABLE.html` — pin numbers confirmed 2026-09-11 vs official XtremeX Quick Start Guide (`docs/XTREMEX-IO-VERIFY-2026-09-11.md`).

## Board / progress snapshot
- Claude progress board is a **stale artifact** (last updated 2026-09-01). Do not treat it as SoT.
- Conflict sheet (board vs git vs husk session memory): `docs/BOARD-VERIFY-2026-09-11.md`.
- Harness faces status (schematic vs `.harness` SoT sync): `docs/HARNESS-FACES-2026-09-11.md`.
- Harness consolidation + Power/Signal layout proposal: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md`.
- ECU I/O and pinout audit (all pin claims cross-checked, `.harness` defects found and fixed): `docs/ECU-IO-AUDIT-2026-09-12.md`.
- Paste **CONFLICT rows only** into the ACTIVE `shipping\` trance; park husk-keyed chats.
## Related Repos (mandatory for CAN bus / wiring work)
This repo defines only one side of the CAN bus (ECU, RealDash, switchboard). The
other node — the gauge cluster — lives in a separate repo:
**[center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4)**.
Cluster firmware is frozen; everything here must stay compatible with it **as-is**.

Any time you are working with CAN bus IDs/frames/byte layouts, or with wiring
(harness, transceivers, pinout), you MUST reference `center-cluster-esp32-p4`
before making changes:
- Its `CANBUS-ENCODE-DECODE-REFERENCE.html` (derived from `main/canbus.c`) is the
  **single source of truth** for CAN IDs, byte layouts, scales, and offsets — see
  `CAN-CONFIG-STATUS.md` in this repo.
- Its `main/protocols/link_g4x.json` and `sdkconfig`/`Kconfig.projbuild` define the
  cluster's TWAI GPIO pinout and transceiver wiring — see `WIRING.md` and
  `CAN-BUS-MASTER-DESIGN.md` in this repo for how it fits the 5-node topology.
- Do not introduce a CAN ID, frame layout, or wiring change here that the cluster
  firmware doesn't already decode/expect — the cluster is not being modified as
  part of work in this repo.

If a local checkout of `center-cluster-esp32-p4` exists (commonly
`C:\projects\shipping\center-cluster-esp32-p4`), prefer reading its source files directly;
otherwise consult the GitHub repo linked above.

## Current Runnable Paths
- `bench/can_bench.py` for monitor/simulate/test workflows.
- `apps/trackcluster-can-sender/app.py` for desktop CAN sender UI.
- `rd-build/tools/automation_helper.py` for local RealDash editor automation.

## Commands
### Install deps
```bash
python -m pip install -r bench/requirements.txt
python -m pip install -r apps/trackcluster-can-sender/requirements.txt
python -m pip install -r rd-build/tools/requirements.txt
```

### Run bench flows
```bash
python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only
python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-cluster
python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash
```

### Run sender app
```bash
python apps/trackcluster-can-sender/app.py
set TC_DEVICE=cluster && python apps/trackcluster-can-sender/app.py
set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py
```

### Quick checks
```bash
python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py
python rd-build/tools/automation_helper.py size
```

## Working Rules
- Keep CAN changes synchronized across `bench/frames.py`, `link_g4x_can_setup.json`, and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Keep `ST185:` names in `link_g4x_realdash.xml` unchanged unless migration is explicitly requested.
- Keep warning-bit mapping parity between XML and `bench/frames.py` bit constants.
- Prefer minimal targeted edits; avoid broad rewrites of stable docs.
- Root `link_g4x_realdash.xml` is the single copy; do not reintroduce a duplicate under `rd-build/`.
- Before any CAN ID/frame or wiring change, check compatibility against `center-cluster-esp32-p4` (see **Related Repos** above).

## MCP / Integration Notes
- Optional MCP example exists at `rd-build/tools/mcp.example.json` for desktop control experiments.

## Cursor Cloud specific instructions
- The Cloud Agent environment is defined by `.cursor/environment.json`, which runs `.cursor/install.sh` (installs the WebKit2 GTK backend for the `pywebview` sender app plus the Python deps from the three `requirements.txt` files).
- No USB-CAN hardware is attached in Cloud Agents, and `vcan`/SocketCAN is unavailable (no `ip`/`modprobe` kernel-module tooling). Validate `bench/can_bench.py` flows against the `python-can` `virtual` interface by default, e.g.:
  ```bash
  python bench/can_bench.py --interface virtual --channel bench --bitrate 1000000 -v simulate-ecu --duration 1.5
  ```
  Reserve the `socketcan`/`pcan`/`slcan` commands elsewhere in this doc for real hardware.
- The `-v/--verbose` flag is global and must come before the subcommand.
- The desktop sender app (`apps/trackcluster-can-sender/app.py`) renders via `pywebview` on the VM display; use GUI/computer-use testing to verify it.

## Model

Pin the model and effort level explicitly rather than relying on the upstream default
(`/model` in Claude Code, the model picker in Cursor), so a vendor default change does not
silently alter how this project is worked on.

## Handoffs are never committed

Work orders, handoffs and session summaries do not belong in this repo. A committed handoff
reads as outstanding work long after it is done, and the next agent redoes it or reports it
as incomplete. Deliver a handoff in chat so it can be copied to whoever needs it.

What does belong in the repo: durable rules, decisions and reference material. If a handoff
contains an open item worth keeping, record the item itself in the relevant doc - not the
work order around it.
