# CLAUDE.md

## Mission
- Keep `Link G4X XtremeX` CAN configuration, `RealDash` channels, and bench tooling synchronized.
- Treat `link_g4x_can_setup.json` as the canonical config contract for IDs, scaling, and offsets.
- Preserve compatibility with frozen cluster firmware assumptions documented in `README.md` and `CANBUS-ENCODE-DECODE-REFERENCE.html`.

## Project Map
- **Core CAN contracts**: `link_g4x_can_setup.json`, `link_g4x_can_setup.lcs`, `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`.
- **RealDash contract**: `link_g4x_realdash.xml`, `REALDASH-LAYOUT.md`, `realdash-simulation.html`.
- **Bench tooling**: `bench/can_bench.py`, `bench/frames.py`, `bench/requirements.txt`, `BENCH-TEST.md`.
- **Desktop sender app**: `apps/trackcluster-can-sender/app.py`, `apps/trackcluster-can-sender/ui/index.html`, `apps/trackcluster-can-sender/BUILD.md`, `apps/trackcluster-can-sender/requirements.txt`.
- **Automation assets**: `rd-build/tools/automation_helper.py`, `rd-build/tools/SETUP.md`, `rd-build/PLAN.md`, `rd-build/FINDINGS.md`.
- **Agent ecosystem**: `.claude/skills/`, `.cursor/skills/`, `.agents/skills/`, `.cursor/hooks.json`, `.claude/hooks/`.

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

## Canonical References
- Include long-form docs instead of re-summarizing:
  - `@./README.md`
  - `@./CAN-BUS-ID-ALLOCATION-TABLE.md`
  - `@./CAN-BUS-MASTER-DESIGN.md`
  - `@./CANBUS-LINK-G4X-CONFIG.md`
  - `@./BENCH-TEST.md`

## Fast Commands
### Environment + dependencies
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

### Sender app dev run
```bash
python apps/trackcluster-can-sender/app.py
set TC_DEVICE=cluster && python apps/trackcluster-can-sender/app.py
set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py
```

### Sanity checks
```bash
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
- `rd-build/link_g4x_realdash.xml` can drift from `link_g4x_realdash.xml`; verify conversion parity when touching either.
- `rd-build/tools/automation_helper.py` depends on desktop permissions and local GUI session; headless runs are unsupported per `rd-build/FINDINGS.md`.

## Change Workflow
1. Identify scope: CAN contract, XML mapping, bench code, app behavior, or docs.
2. Update the smallest authoritative source first (`link_g4x_can_setup.json` for wire contract, `link_g4x_realdash.xml` for RealDash input contract, `bench/frames.py` for encode/decode behavior).
3. Propagate to dependents (`CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-CONFIG-STATUS.md`, `BENCH-TEST.md`, `REALDASH-LAYOUT.md`) only where drift appears.
4. Run targeted command checks from **Fast Commands**.
5. Report what changed and where parity was revalidated.

## MCP + Tooling Note
- Optional desktop-control MCP example exists at `rd-build/tools/mcp.example.json`.
- Do not create or edit `.claude/settings.json`, `.claude/settings.local.json`, or `mcpServers` configs from this file.

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
  2. Run: `caliber refresh && git add CALIBER_LEARNINGS.md CLAUDE.md .claude/ .cursor/ .cursorrules AGENTS.md .agents/ 2>/dev/null`
  3. After it completes, briefly tell the user what Caliber updated. Then proceed with the commit.

**Valid `caliber refresh` options:** `--quiet` (suppress output) and `--dry-run` (preview without writing). Do not pass any other flags — options like `--auto-approve`, `--debug`, or `--force` do not exist and will cause errors.

**`caliber config`** takes no flags — it runs an interactive provider setup. Do not pass `--provider`, `--api-key`, or `--endpoint`.

If `caliber` is not found, tell the user: "This project uses Caliber for agent config sync. Run /setup-caliber to get set up."
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
If the pre-commit hook is not set up, run `/setup-caliber` to configure everything automatically.
<!-- /caliber:managed:sync -->
