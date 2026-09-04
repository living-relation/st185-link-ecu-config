# AGENTS.md

## Scope
- This repo is CAN configuration + bench/tooling for ST185 TrackCluster.
- Primary code paths are `bench/`, `apps/trackcluster-can-sender/`, and `rd-build/tools/`.
- Primary contracts are `link_g4x_can_setup.json` and `link_g4x_realdash.xml`.

## Source Of Truth
- CAN IDs, offsets, scaling: `link_g4x_can_setup.json`.
- Architecture and allocation: `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`.
- Bench behavior: `bench/frames.py`, `bench/can_bench.py`, `BENCH-TEST.md`.
- RealDash channel definitions: `link_g4x_realdash.xml`.

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
  `CAN-BUS-MASTER-DESIGN.md` in this repo for how it fits the 4-node topology.
- Do not introduce a CAN ID, frame layout, or wiring change here that the cluster
  firmware doesn't already decode/expect — the cluster is not being modified as
  part of work in this repo.

If a local checkout of `center-cluster-esp32-p4` exists (commonly
`C:\projects\center-cluster-esp32-p4`), prefer reading its source files directly;
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
- If editing `rd-build/link_g4x_realdash.xml`, compare against root `link_g4x_realdash.xml` to prevent drift.
- Before any CAN ID/frame or wiring change, check compatibility against `center-cluster-esp32-p4` (see **Related Repos** above).

## MCP / Integration Notes
- Optional MCP example exists at `rd-build/tools/mcp.example.json` for desktop control experiments.
- Caliber hooks exist in `.claude/hooks/` and `.cursor/hooks.json`; keep config guidance compatible with them.

<!-- caliber:managed:pre-commit -->
## Before Committing

**IMPORTANT:** Before every git commit, you MUST ensure Caliber syncs agent configs with the latest code changes.

First, check if the pre-commit hook is already installed:
```bash
grep -q "caliber" .git/hooks/pre-commit 2>/dev/null && echo "hook-active" || echo "no-hook"
```

- If **hook-active**: the hook handles sync automatically — just commit normally. Tell the user: "Caliber will sync your agent configs automatically via the pre-commit hook."
- If **no-hook**: run Caliber manually before committing:
  1. Tell the user: "Caliber: Syncing agent configs with your latest changes..."
  2. Run: `caliber refresh && git add CLAUDE.md .claude/ .cursor/ .cursorrules .github/copilot-instructions.md .github/instructions/ AGENTS.md CALIBER_LEARNINGS.md .agents/ .opencode/ 2>/dev/null`
  3. After it completes, briefly tell the user what Caliber updated. Then proceed with the commit.

**Valid `caliber refresh` options:** `--quiet` (suppress output) and `--dry-run` (preview without writing). Do not pass any other flags — options like `--auto-approve`, `--debug`, or `--force` do not exist and will cause errors.

**`caliber config`** takes no flags — it runs an interactive provider setup. Do not pass `--provider`, `--api-key`, or `--endpoint`.

If `caliber` is not found, read `.agents/skills/setup-caliber/SKILL.md` and follow its instructions to install Caliber.
<!-- /caliber:managed:pre-commit -->

<!-- caliber:managed:learnings -->
## Session Learnings

Read `CALIBER_LEARNINGS.md` for patterns and anti-patterns learned from previous sessions.
These are auto-extracted from real tool usage — treat them as project-specific rules.
<!-- /caliber:managed:learnings -->

<!-- caliber:managed:model-config -->
## Model Configuration

Recommended default: `claude-sonnet-4-6` with high effort (stronger reasoning; higher cost and latency than smaller models).
Smaller/faster models trade quality for speed and cost — pick what fits the task.
Pin your choice (`/model` in Claude Code, or `CALIBER_MODEL` when using Caliber with an API provider) so upstream default changes do not silently change behavior.

<!-- /caliber:managed:model-config -->

<!-- caliber:managed:sync -->
## Context Sync

This project uses [Caliber](https://github.com/caliber-ai-org/ai-setup) to keep AI agent configs in sync across Claude Code, Cursor, Copilot, and Codex.
Configs update automatically before each commit via `caliber refresh`.
If the pre-commit hook is not set up, read `.agents/skills/setup-caliber/SKILL.md` and follow the setup instructions.
<!-- /caliber:managed:sync -->
