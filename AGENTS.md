# AGENTS.md

> ## Before any wiring or CAN change — binding on every agent
>
> Read **`docs/RECONCILIATION-RULES.md`**. Three rules, all non-optional:
>
> 1. **Wiring** — a change to one wiring document is not done until it is checked against
>    the source-of-truth chain and **every other wiring surface**, including ones you did
>    not edit. `sot/channels.csv` is the pin source of truth; `XTREMEX-IO-TABLE.html` is its
>    visual face. The `.harness` looms are drawings, not a source of truth.
> 2. **CAN** — a change on any device must be reconciled against **all** of them: Link ECU,
>    center cluster, RealDash, ECUMaster CSB3. This crosses repo boundaries. The cluster
>    firmware is frozen and outranks everything; on conflict, the other device changes.
> 3. **ECU looms** — follow the ECU connector letter: A pins → `ST185-A-cabin` → bulkhead A
>    → `ST185-A-engine`, B the same. Crossovers (a) +5V / Gnd Out, (b) ETB A20 / B5,
>    (c) APS A14 / B33 only. Gate: `docs/harness/validate_bulkhead_letter.py`.
>
> Link CAN-Lambda is on CAN bus 1. CAN bus 2 is unused and its ECU pins are free.

## Scope
- This repo is CAN configuration + bench/tooling for ST185 TrackCluster.
- Primary code paths are `bench/`, `apps/trackcluster-can-sender/`, and `rd-build/tools/`.
- Primary contracts are `link_g4x_can_setup.json` and `link_g4x_realdash.xml`.

## Source Of Truth
- CAN IDs, offsets, scaling: `link_g4x_can_setup.json` (ECU frames, PCLink encode form) and `switchboard_frames.json` (0x640-0x643). Parity gate: `python bench/check_parity.py`.
- Architecture and allocation: `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`.
- Bench behavior: `bench/frames.py`, `bench/can_bench.py`, `BENCH-TEST.md`.
- RealDash channel definitions: `link_g4x_realdash.xml`.
- Engine-room power splice table (kick-panel J/Bs, vacated J/B2): `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`.
- Wiring SoT (every ECU pin and channel): `sot/channels.csv`. Visual face: `XTREMEX-IO-TABLE.html` (gated by `docs/harness/sync_io_table.py --check`).
- The harness drawings - **not a source of truth** (Daniel, 2026-10-04: they follow `sot/channels.csv`; never generate truth docs from them): `docs/harness/rebuild/*.harness` (15 files, one physical harness per file; wires between files are drawn broken off in both; the four ECU looms split by connector letter 2026-09-28; `docs/harness/README.md`). Ownership/interfaces: `docs/harness/interfaces.json`, `docs/harness/redesign/`. Gate: `python docs/harness/check_all.py`.
- Wiring reconciliation rules: `docs/RECONCILIATION-RULES.md` Rule 1; ECU loom letter rule: Rule 3.

## Board / progress snapshot
- Claude progress board is a **stale artifact** (last updated 2026-09-01). Do not treat it as SoT.
- Harness build rules: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6. The 2026-09-27
  redesign (physical-harness-per-file, ownership/interface model) supersedes the file
  inventory in §6.41; current decisions are `docs/harness/redesign/DECISIONS.md`.
- `archive/` holds retired harness drawings only. They are not authoritative.
- Paste **CONFLICT rows only** into the ACTIVE `shipping\` trance; park husk-keyed chats.
## Related Repos (mandatory for CAN bus / wiring work)
This repo defines only one side of the CAN bus (ECU, RealDash, switchboard). The
other node — the gauge cluster — lives in a separate repo:
**[center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4)**.
Cluster firmware is frozen; everything here must stay compatible with it **as-is**.

Any time you are working with CAN bus IDs/frames/byte layouts, or with wiring
(harness, transceivers, pinout), you MUST reference `center-cluster-esp32-p4`
before making changes:
- Its `main/canbus.c` is the **decode truth** (reads 0x3E8-0x3EB and 0x3EE, sends 0x3EC/0x3ED);
  its `CANBUS-ENCODE-DECODE-REFERENCE.html` (https://github.com/living-relation/center-cluster-esp32-p4/blob/main/CANBUS-ENCODE-DECODE-REFERENCE.html) is the readable reference derived from it —
  link to it, never copy cluster files here; see `CAN-CONFIG-STATUS.md` in this repo.
- Its `sdkconfig` and `main/Kconfig.projbuild` define the
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

### Run sender app (PowerShell)
```powershell
python apps/trackcluster-can-sender/app.py
$env:TC_DEVICE='cluster'; python apps/trackcluster-can-sender/app.py
$env:TC_DEVICE='realdash'; python apps/trackcluster-can-sender/app.py
```

### Quick checks
```bash
python docs/harness/check_all.py
python bench/check_parity.py
python tune/scripts/validate_tune.py
python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py
python rd-build/tools/automation_helper.py size
```

## Working Rules
- Keep CAN changes synchronized across `bench/frames.py`, `link_g4x_can_setup.json`, `switchboard_frames.json`, the `.lcs`, the RealDash XML, the sender UI and `CAN-BUS-ID-ALLOCATION-TABLE.md` — `python bench/check_parity.py` must pass.
- Open items live in one table: `docs/OPEN-ITEMS.md`.
- Keep `ST185:` names in `link_g4x_realdash.xml` unchanged unless migration is explicitly requested.
- Keep warning-bit mapping parity between XML and `bench/frames.py` bit constants.
- Prefer minimal targeted edits; avoid broad rewrites of stable docs.
- main is protected (ruleset "Protect main"); all changes go through PRs with "Repo checks" and "Protect research hub" green; only the research-hub bot (deploy key) bypasses.
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

## Generated files - who owns them

| File | Owner | Rule |
|---|---|---|
| `docs/research-hub.html` | **The "Regenerate research hub" Action** | **Never commit it.** Run `docs/build-research-hub.py` locally to preview, then `git checkout -- docs/research-hub.html` before you commit. PRs that touch `docs/**` (or the workflow) run the generator as a check and attach the HTML artifact. The bot commits the file to `main` only, after those changes merge. Committing it locally is what causes the rebase conflicts. |
| `docs/harness/HARNESS-BUILD-LIST.csv` | `docs/harness/buildlist.py` | Commit it, but always regenerate - never hand-edit, never hand-merge. |
| `docs/harness/NEED-TO-BUY.md` | `docs/harness/buylist.py` | Same. |

`.gitattributes` marks them `linguist-generated` and gives `research-hub.html`
`merge=ours`. Enable the driver and the pre-commit hook once per clone:

```
powershell -File .githooks/setup.ps1
```

If you still land in a conflict on one of these, do not resolve it by hand. Take either
side, re-run the generator, and stage the result.

## Wiring audit
- `python docs/harness/check_all.py` is the wiring audit. The 2026-09-18 conflict sheet is archived; its bh_c questions are settled (bulkhead C deleted).
