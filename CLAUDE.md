# CLAUDE.md

## Mission
- Keep `Link G4X XtremeX` CAN configuration, `RealDash` channels, and bench tooling synchronized.
- Treat `link_g4x_can_setup.json` as the canonical config contract for IDs, scaling, and offsets.
- Preserve compatibility with frozen cluster firmware assumptions documented in `README.md` and `CANBUS-ENCODE-DECODE-REFERENCE.html`.

## Project Map
- **Core CAN contracts**: `link_g4x_can_setup.json` (ECU frames, PCLink encode form), `link_g4x_can_setup.lcs` (decode form), `switchboard_frames.json` (CSB3 0x640-0x643), `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`, `CAN-CONFIG-STATUS.md` (status note), `ECUMASTER_SWITCHBOARD_SETUP.md`, `CANBUS-ENCODE-DECODE-REFERENCE.html` (mirror of the cluster repo's copy - the cluster copy wins).
- **CAN parity gate**: `bench/check_parity.py` - JSON, `.lcs`, ID table, `bench/frames.py`, RealDash XML, sender UI and `switchboard_frames.json` must agree. Runs in CI (`.github/workflows/checks.yml`).
- **RealDash contract**: `link_g4x_realdash.xml`, `REALDASH-LAYOUT.md`, `realdash-simulation.html`.
- **Bench tooling**: `bench/can_bench.py`, `bench/frames.py`, `bench/requirements.txt`, `BENCH-TEST.md`.
- **Desktop sender app**: `apps/trackcluster-can-sender/app.py`, `apps/trackcluster-can-sender/ui/index.html`, `apps/trackcluster-can-sender/BUILD.md`, `apps/trackcluster-can-sender/requirements.txt`.
- **Automation assets**: `rd-build/tools/automation_helper.py`, `rd-build/tools/SETUP.md`, `rd-build/PLAN.md`, `rd-build/FINDINGS.md`.
- **Wiring SoT**: `sot/channels.csv` (every ECU pin and channel). `XTREMEX-IO-TABLE.html` is its visual face. `WIRING.md` covers the cluster boards and the 5-node CAN topology.
- **Harness / electrical**: `docs/harness/rebuild/*.harness` (one physical harness per file, ownership in `docs/harness/interfaces.json`; see `docs/harness/README.md`), gate `python docs/harness/check_all.py`. ECU looms follow the ECU connector letter (`ST185-A-cabin` / `-B-cabin` / `-A-engine` / `-B-engine`) - canonical rule `docs/RECONCILIATION-RULES.md` Rule 3, gate `validate_bulkhead_letter.py`; `docs/SHIELD-RULES.md`, `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`.
- **Engine calibration**: `tune/engine_constants.yaml`, `tune/limits.yaml`, `tune/tables/*.csv`, `tune/docs/`, `tune/scripts/` (incl. `validate_tune.py`), `tune/README.md` — PCLink seeds only; not an I/O or CAN source. `FUEL-SYSTEM.md` is fuel hardware reference, not CAN.
- **Other docs/**: `docs/devices/`, `docs/enclosures/`, `docs/sourcing/`, `docs/procedures/`, `docs/intercooler-turbo-study/`, `docs/5sgte-project-data/` (research), `docs/research-hub.html` (generated, see below).
- **Open items**: `docs/OPEN-ITEMS.md` - the one table of everything unresolved (owner, file:line, what unblocks it).
- **Handoffs**: `output/` (tracked) - session handoff notes. Not authoritative; the files they describe win.
- **Archive**: `archive/` holds retired harness drawings only. **Do not read or search it during normal work**; it is excluded from agent context and nothing in it is authoritative. Consult it only when explicitly asked why a past decision was made, and if it disagrees with a current doc, the current doc wins.
- **Agent ecosystem**: `.claude/skills/` (4 skills), `.claude/rules/` + `.cursor/rules/` (same rules, two tools), `.claude/settings.json` (permission allow-list), `.cursor/environment.json` + `.cursor/install.sh` (Cursor Cloud bootstrap), `.claudeignore` (keeps `archive/` out of context), `.githooks/` (pre-commit refuses `docs/research-hub.html`). No agent hooks are configured.

## Related Repos (mandatory for CAN bus / wiring work)
This repo defines only one side of the CAN bus (ECU, RealDash, switchboard). The
other node — the gauge cluster — lives in a separate repo:
**[center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4)**.
Cluster firmware is frozen; everything here must stay compatible with it **as-is**.

Any time you are working with CAN bus IDs/frames/byte layouts, or with wiring
(harness, transceivers, pinout), you MUST reference `center-cluster-esp32-p4`
before making changes:
- Its `main/canbus.c` is the **decode truth** (it reads 0x3E8-0x3EB and 0x3EE, sends
  0x3EC/0x3ED); its `CANBUS-ENCODE-DECODE-REFERENCE.html` is the readable reference derived
  from it — see `CAN-CONFIG-STATUS.md` in this repo.
- Its `sdkconfig` and `main/Kconfig.projbuild` define the
  cluster's TWAI GPIO pinout and transceiver wiring — see `WIRING.md` and
  `CAN-BUS-MASTER-DESIGN.md` in this repo for how it fits the 5-node topology.
- Do not introduce a CAN ID, frame layout, or wiring change here that the cluster
  firmware doesn't already decode/expect — the cluster is not being modified as
  part of work in this repo.

If a local checkout of `center-cluster-esp32-p4` exists (on dansPC:
`C:\projects\shipping\center-cluster-esp32-p4`), prefer reading its source files directly
(`bench/check_parity.py` also checks its decoded frame set when it sits next to this repo);
otherwise consult the GitHub repo linked above.

## Canonical References
- Include long-form docs instead of re-summarizing:
  - `@./README.md`
  - `@./CAN-BUS-ID-ALLOCATION-TABLE.md`
  - `@./CAN-BUS-MASTER-DESIGN.md`
  - `@./CANBUS-LINK-G4X-CONFIG.md`
  - `XTREMEX-IO-TABLE.html` — not auto-included (large); open it only when you need the pin map. `sot/channels.csv` is the source.
  - `@./docs/RECONCILIATION-RULES.md`
  - `@./BENCH-TEST.md`

## Fast Commands
### Environment + dependencies
Python 3.14 (same as CI). Requirements are pinned. One-time per clone (PowerShell, repo root):
`powershell -File .githooks/setup.ps1` — sets `core.hooksPath` and `merge.ours.driver`.
```bash
python -m pip install -r bench/requirements.txt
python -m pip install -r apps/trackcluster-can-sender/requirements.txt
python -m pip install -r rd-build/tools/requirements.txt
```

### Bench validation
```bash
python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only
python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-cluster
python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash
```

### Sender app dev run (PowerShell)
```powershell
python apps/trackcluster-can-sender/app.py
$env:TC_DEVICE='cluster'; python apps/trackcluster-can-sender/app.py
$env:TC_DEVICE='realdash'; python apps/trackcluster-can-sender/app.py
```

### Sanity checks
```bash
python docs/harness/check_all.py          # harness gates; --check mode, never writes
python bench/check_parity.py              # CAN contract parity
python tune/scripts/validate_tune.py      # tune seed tables (needs PyYAML)
python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py
python rd-build/tools/automation_helper.py size
python rd-build/tools/automation_helper.py screenshot rd-build/rd_screen.png
```

## Required Conventions
- Keep `0x3E8`-`0x3F1` semantics aligned across `bench/frames.py`, `link_g4x_can_setup.json`, and docs.
- Keep `ST185:` input names in `link_g4x_realdash.xml` stable; dashboard bindings depend on exact names.
- Keep all multibyte CAN fields BigEndian unless a source file explicitly documents otherwise.
- For warnings in `0x3F1` byte 6, keep bit mapping consistent with `bench/frames.py` constants and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Prefer focused edits; do not rewrite large docs if a small section update is enough.
- Before any CAN ID/frame or wiring change, check compatibility against `center-cluster-esp32-p4` (see **Related Repos** above).

## Known Gotchas
- `AGENTS.md` previously referenced removed paths like `apps/canbus-live-sender/`; use `apps/trackcluster-can-sender/`.
- Root `link_g4x_realdash.xml` is the single copy (the `rd-build/` duplicate was removed 2026-09-04 after drifting); do not reintroduce one.
- The sibling repo `st185-furyx-base-map` holds an older **FuryX-era** copy of `link_g4x_can_setup.json`/`.lcs` and `CANBUS-LINK-G4X-CONFIG.md`. This repo's versions are newer (frames `0x3EF`/`0x3F0`/`0x3F1`, 2-byte oil/fuel pressure, `MAP` not `MGP`) — never copy CAN files from it. Its `io_assignments.yaml` is FuryX-only and contradicts `XTREMEX-IO-TABLE.html`.
- `rd-build/tools/automation_helper.py` depends on desktop permissions and local GUI session; headless runs are unsupported per `rd-build/FINDINGS.md`.

## Change Workflow
1. Identify scope: CAN contract, XML mapping, bench code, app behavior, or docs.
2. Update the smallest authoritative source first (`link_g4x_can_setup.json` for wire contract, `link_g4x_realdash.xml` for RealDash input contract, `bench/frames.py` for encode/decode behavior).
3. Propagate to dependents (`CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-CONFIG-STATUS.md`, `BENCH-TEST.md`, `REALDASH-LAYOUT.md`) only where drift appears.
4. Run targeted command checks from **Fast Commands**.
5. Report what changed and where parity was revalidated.

## MCP + Tooling Note
- Optional desktop-control MCP example exists at `rd-build/tools/mcp.example.json`.
- `.claude/settings.json` exists (allow-list for git/python/pip/pytest). Do not edit it, `.claude/settings.local.json`, or `mcpServers` configs as part of normal work.

## Local environment

- Local checkout of this repo on dansPC is `C:\projects\shipping\st185-link-ecu-config` (moved from `C:\projects\st185-link-ecu-config`).

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
| `docs/harness/min/*.harness` | `docs/harness/make_min.py` | Same. `check_all.py` runs all three generators with `--check` and fails if a committed copy is stale. |

`.gitattributes` marks them `linguist-generated` and gives `research-hub.html`
`merge=ours`. Enable the driver (and the pre-commit hook) once per clone:

```
powershell -File .githooks/setup.ps1
```

If you still land in a conflict on one of these, do not resolve it by hand. Take either
side, re-run the generator, and stage the result.
