# AGENTS.md

## Read first, before starting work or asking
Read in order: (1) this file; (2) `docs/harness/redesign/DECISIONS.md` "Binding rules B1-B30" (old R-numbers resolve
through its retire map), then `docs/RECONCILIATION-RULES.md`; (3) the working memory
`%USERPROFILE%\.claude\working-memory\st185-link-ecu-config\INDEX.md` (WSL: `/mnt/c/Users/<user>/.claude/...`);
(4) `docs/OPEN-ITEMS.md` "Status" (the current state; a new chat starts there). If a rule or note already answers a
question, act on it and cite it - never ask Dan something the rules already answer.

> **Project focus (R102, Dan 2026-10-15) - the ONLY scope, in order:** (1) wiring sorted so Dan can build the
> harnesses; (2) ECU base maps; (3) ECU CAN config written and checked; (4) CSB3 config finished. Open a
> `docs/OPEN-ITEMS.md` row only for a blocker of one of them; new ideas are shelved, not started.

> **Current work: the surgical rewire, `docs/OPEN-ITEMS.md` row 164.** Forward of the firewall every wire is new, on a
> named route (B9; `docs/harness/routes/` Routes 16 and 17); the OEM cabin wiring stays with J/B No.1 / No.3 and R/B
> No.2 / No.4. Lists and decided circuits: `docs/harness/README.md` "What stays and what goes"; work files and the next
> group: `docs/harness/cut-list/README.md`. Walk it with Dan one step at a time, 1993 EWD in hand. Parked: the fuse
> box (row 107 and rows 113 / 123 / 148). The drawing set (rows 153 / 155) is stale until row 164 writes the master.
> Wire lengths wait for a tape-measure pass (row 165). No bench tests: car checks use `docs/procedures/`.

> **Freeze (R224, Dan 2026-10-20):** no new rule, script, gate, drawing format or feature until the bloat cut is done
> (`docs/OPEN-ITEMS.md` rows 153, 155). Work only the cut and Goal 1 blockers.

## Before any wiring or CAN change - binding on every agent
1. **Wiring:** ONE source of truth, `docs/harness/MASTER-wirelist.csv` (R221). `sot/channels.csv` keeps only the ECU
   channel settings and is checked against it; `XTREMEX-IO-TABLE.html` is its visual face. Drawings and the BOM are
   generated from the master; no script writes the master. A change is done only when every wiring surface agrees
   (`docs/RECONCILIATION-RULES.md` Rule 1). Change it with the `st185-change-sot` skill.
2. **CAN:** a change on any device is reconciled against all of them - Link ECU, center cluster, RealDash, ECUMaster
   CSB3 (Rule 2). The cluster firmware is frozen and outranks everything; on conflict the other device changes. CAN
   config is never parked for setup time (R80): change the repo CAN files now with `bench/check_parity.py` green.
3. **ECU harness (R220):** loom A and B are ONE harness, `AB` (`AB-cabin`, `AB-engine`); ECU pins never move. Drawn by
   `docs/harness/tools/build_drawings.py` as ONE set, `ST185-harness` (R225): never hand-edited; no harness.design.
4. **ECU pins (R212):** every ECU-pin circuit is checked against the Link G4X Quick Start Guide and plug-in guides
   (G4X only; local copies in gitignored `docs/vendor/`; tracked extract `sot/channels.csv`). A mismatch is a stop.
5. **Grounds and relays (R213 / R216 / R217 / R219):** ECU power ground -> POWER box battery-negative bar only; PCBs, CAN
   nodes, LEDs -> battery-negative bus, never chassis; sensors -> Gnd Out only; shields -> drains only. An ECU output
   driving a relay is low-side: ECU pin -> coil 85, coil 86 -> fused +12 V. Gated by `check_wiring.py`.

Link CAN-Lambda is on CAN bus 1; CAN bus 2 is unused.

## Project map
- **CAN contracts:** `link_g4x_can_setup.json` (ECU frames, encode form; canonical for IDs, scaling, offsets),
  `link_g4x_can_setup.lcs` (decode form, ECU receive channels 0x3EC/0x3ED and CSB3 0x640/0x642),
  `switchboard_frames.json` (CSB3 0x640-0x643), `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`,
  `CANBUS-LINK-G4X-CONFIG.md`, `ECUMASTER_SWITCHBOARD_SETUP.md`, `CANBUS-ENCODE-DECODE-REFERENCE.html` (a pointer to the
  cluster repo's file; nothing from the cluster is copied here). Parity gate: `bench/check_parity.py`.
- **RealDash:** `link_g4x_realdash.xml` (the single copy), `REALDASH-LAYOUT.md`, `realdash-simulation.html`, `rd-build/`.
- **Bench and sender app:** `bench/can_bench.py`, `bench/frames.py`, `BENCH-TEST.md`, `apps/trackcluster-can-sender/`.
- **Wiring:** `docs/harness/` (folder map in its `README.md`): the master, `drawings/` (generated), `routes/` (Dan's
  approved routes), `cut-list/` (rewire work files), `redesign/DECISIONS.md` (every rule). Part data:
  `docs/sourcing/harness-parts.csv`. Shields: `docs/SHIELD-RULES.md`.
- **Tune:** `tune/` (PCLink seeds only; `tune/scripts/validate_tune.py`). Fuel hardware: `FUEL-SYSTEM.md`.
- **CAD:** the one `cad/` tree by part; `cad/README.md` is the ONE model list (its `Selected for build` column is the
  only build choice; a new model gets a row and a trimetric in the same PR). Heavy CAD files are gitignored in the main
  checkout `C:\projects\active\st185-link-ecu-config`. Fusion allows 10 editable documents: reuse, never throw away.
- **BOM:** `docs/sourcing/PROJECT-BOM.xlsx` / `.csv`, generated by `docs/sourcing/build_project_bom.py`; never hand-edit.
- **Tracker:** `docs/OPEN-ITEMS.md` - THE one tracker (open rows, Needs Dan, Status, History). No other plan or list.
- **Other docs:** `README.md`, `docs/devices/`, `docs/enclosures/`, `docs/sourcing/`, `docs/procedures/`,
  `docs/research/`, `docs/5sgte-project-data/`, `docs/intercooler-turbo-study/`. Dispatch-only: `docs/dispatch/`.
- **Agent files:** `.claude/skills/` (4 CAN / bench skills), `.claude/rules/` and `.cursor/rules/` (pointers only),
  `.githooks/` (pre-commit refuses `docs/research-hub.html`).

## Skills
Five ST185 skills live in Dan's claude.ai account (their one home): `st185-apply-route-markup`,
`st185-build-harness-from-sot`, `st185-change-sot`, `st185-pick-parts`, `st185-ship-change`. Pointer only.

## Related repo: the cluster (mandatory for CAN or wiring work)
`center-cluster-esp32-p4` (local `C:\projects\active\center-cluster-esp32-p4`, else GitHub
living-relation/center-cluster-esp32-p4). Its `main/canbus.c` is the decode truth (reads 0x3E8-0x3EB and 0x3EE, sends
0x3EC/0x3ED); its `sdkconfig` / `main/Kconfig.projbuild` define its CAN pins. Never add a frame or wiring change here
that the frozen cluster does not already expect. The sibling `st185-furyx-base-map` repo is FuryX-era: never copy from it.

## Commands
One-time per clone: `powershell -File .githooks/setup.ps1` (hooks + `merge.ours`). Python 3.14; requirements are pinned
in `bench/`, `apps/trackcluster-can-sender/`, `rd-build/tools/`.
```bash
python tools/check_all.py                  # every repo gate (never writes); must pass before every commit
python docs/harness/tools/check_wiring.py  # the ONE wiring check; --tbd lists unconfirmed parts
python bench/check_parity.py               # CAN contract parity
python docs/build-research-hub.py --strict # tracker counts; never commit docs/research-hub.html
python .github/scripts/test_docs_gates.py  # docs gate self-tests
python bench/can_bench.py --interface virtual --channel bench --bitrate 1000000 -v simulate-ecu --duration 1.5
```
Real hardware: `--interface pcan --channel PCAN_USBBUS1` with `monitor --known-only`, `full-cluster`, `full-realdash`.

## Working rules
- CAN changes stay in sync across `bench/frames.py`, the JSON, `.lcs`, `switchboard_frames.json`, the RealDash XML, the
  sender UI and `CAN-BUS-ID-ALLOCATION-TABLE.md`. Multibyte fields BigEndian. `0x3F1` byte 6 warning bits match the
  `bench/frames.py` constants. Keep `ST185:` names in the XML (renames break gauges). RealDash reads 0x3EF-0x3F1 plus
  the 0x3EB gear byte only. Frame routing: DECISIONS B16.
- **No stale documents (R211):** a new doc or SoT consolidates or deletes every older doc on the same thing in the same
  PR; nothing is bannered "superseded" or kept "for reference" (git history is the archive). Gate:
  `tools/check_doc_claims.py`. No wiring CSV under `docs/harness/` but the master (gate F1).
- Retiring files (R46): replaced versions, generated files, duplicates, scratch, finished handoffs need no OK (list them
  in the PR under "Retired"); Dan's only-copies, the SoT and DECISIONS rows need his OK.
- `main` is protected: PRs only, "Repo checks" and "Protect research hub" green, squash-merge. Every PR body has a
  `Rows: <n>, <n>` or `Rows: none` line (numbers only). Pulls fast-forward only; never force-push.
- Generated files: `docs/research-hub.html` is committed only by the "Regenerate research hub" Action (preview locally,
  then `git checkout -- docs/research-hub.html`); `PROJECT-BOM.*` and `docs/harness/drawings/*` come from their
  generators. On a conflict in one, take either side and re-run the generator.
- Drawing initials (R200): DRAWN and every rev BY are the requester, always `DG` here, read from
  `%USERPROFILE%\.drawing-initials`; an agent with no file stops and asks. Gate: `cad/check_drawing_rules.py`.
- Layout views: front of the car on the RIGHT, driver side up (R140, R153). Every wire carries its circuit's ident bands
  (R87).
- `tools/hygiene.ps1` (`-WhatIf` = dry run) removes merged worktrees and branches; sessions never remove their own.
- Dispatch-launched sessions: no clickable pickers, ask in plain text. Prefer minimal targeted edits.
- Do not edit `.claude/settings*.json` or `mcpServers` configs in normal work. Pin the model and effort explicitly.

## Dashboard
The research hub `docs/research-hub.html` (online: https://living-relation.github.io/st185-link-ecu-config/research-hub.html)
is generated from `docs/OPEN-ITEMS.md` (keep the table format: ID first, owner column 4, status column 6; closed
goal-tagged rows stay as one line for the goal bars), the route status boxes, `cad/README.md`, `docs/status/hub.json`,
`docs/status/grok-jobs.json` and `git log`. Moving any of these needs `docs/build-research-hub.py` checked.

## Cloud agents
Cursor Cloud uses `.cursor/environment.json` + `.cursor/install.sh`. No USB-CAN and no SocketCAN: test with the
`python-can` `virtual` interface; `-v` goes before the subcommand. RealDash editor automation (`rd-build/tools/`) needs a
GPU desktop session (headless is unsupported, `rd-build/FINDINGS.md`).
