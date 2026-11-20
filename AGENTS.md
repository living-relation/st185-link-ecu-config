# AGENTS.md

## Read first, before starting work or asking
Read in order: (1) this file; (2) `docs/harness/redesign/DECISIONS.md` — B1–B30 and Rules 1–3; use the retire map only to look up an old R-number; (3) the store `STATE.md` (a new chat starts there), this branch's `STATE-<slug>.md`, then `docs/NEEDS-DAN.md`; (4) the store `INDEX.md` (preference and fact notes). If a rule or note already answers a question, act on it — never ask Dan something the rules already answer.

Store unreachable (PC offline, cloud session): work from committed docs.

## Where things live (workstation-core template, profile Full; Dan A92 a / A93 a, 2026-11-19)
| Role | Location |
|---|---|
| Router | `AGENTS.md` |
| Decisions (why) | `docs/harness/redesign/DECISIONS.md` (append only) |
| Rules (how) | `.claude/rules/` (Cursor copies generated) |
| SPEC (done criteria) | `docs/harness/redesign/SPEC.md` |
| Data (values) | `docs/harness/MASTER-wirelist.csv`, `sot/channels.csv`, `sot/fuse-relay-map.csv`, `docs/harness/tools/ST185-harness.layout.json` + `placement_editor/seeds/`, `docs/harness/tools/corridors.json`, `cad/fusebox/src/spec.py`; registry `.claude/sot.json` |
| Open questions for Dan | `docs/NEEDS-DAN.md` (CI reads it; A96 a) |
| Live state | store `st185-link-ecu-config/STATE.md`, `STATE-<slug>.md` |
| Backlog | store `st185-link-ecu-config/BACKLOG.md` (open rows keep their old tracker IDs); history in the store `archives/` |
| Branch checklist | `TASK.md` at the worktree root, git-ignored |

The store is `<Projects>\_claude\Claude Projects\Working Memory\memory\st185-link-ecu-config\` (`python <workstation>/scripts/state/state_paths.py` prints it). Memory (workstation, global to every project): live progress lives in the store STATE / BACKLOG, never in the repo (A92 a; was workstation #32 "progress lives in the repo"); personal preferences stay in the store notes listed in its `INDEX.md`; Cursor edits Claude's notes directly; there is no sync step. Handoffs: the `state-closeout` skill (handoff mode) and the branch's STATE-<slug>; never a handoff file in the repo or `.claude/handoff/`. Run state-closeout at 80% context, on a pivot, a blocker, a milestone and a PR (`.claude/rules/00-state-protocol.md`). Scratch folders hold disposable work only (in the repo: `_scratch/`, gitignored, nothing vital ever there): anything vital goes to its home by type, tools and scripts into the repo; clean scratch only by deleting your own files by name (DECISIONS "Where data lives (B3)", Dan 2026-11-03).

> **Project focus (R102, Dan 2026-10-15) - the ONLY scope, in order:** (1) wiring sorted so Dan can build the harnesses; (2) ECU base maps; (3) ECU CAN config written and checked; (4) CSB3 config finished. Open a store BACKLOG row only for a blocker of one of them.

> **Current work:** the store `STATE.md` (Current Goal and Next Single Step).


## Before any wiring or CAN change
1. **Wiring:** ONE source of truth, `docs/harness/MASTER-wirelist.csv`. `sot/channels.csv` is ECU settings only; `XTREMEX-IO-TABLE.html` is its visual face. The wire lists, pin chart, DRB102 map and BOM are generated from the master; no script writes the master, except `build_drawings.py --write-lengths` for the lengths of placed harnesses (DECISIONS "Placement and lengths (B8)"). A change is done only when every wiring surface agrees (DECISIONS Rule 1).
2. **CAN:** reconcile across Link ECU, center cluster, RealDash, ECUMaster CSB3 (DECISIONS Rule 2). Frozen cluster wins. Write the repo CAN files now; `bench/check_parity.py` green.
3. **ECU harness:** loom A and B are ONE harness, `AB` (`AB-cabin`, `AB-engine`); ECU pins move only per DECISIONS B19. One layout tree, `ST185-harness.layout.json`; one harness.design file per harness (B6).
4. **ECU pins:** before any edit, check every ECU-pin circuit against the Link G4X Quick Start Guide and plug-in guides (G4X only; DECISIONS B19). A mismatch is a stop: ask Dan. G4 / G4+ sources are never used, not even as "closest available"; with no G4X source the answer is "TBD (no G4X source)" (repeated violation logged 2026-11-16, Dan).
5. **Grounds and relays:** DECISIONS B10 (grounds) and B15 (relays).

CAN bus: one bus, CAN 1 (DECISIONS B17).

## Project map
- **Rules / decisions:** `docs/harness/redesign/DECISIONS.md` (the one file); done criteria `docs/harness/redesign/SPEC.md`. Open work: the store `BACKLOG.md`; questions for Dan: `docs/NEEDS-DAN.md`.
- **Wiring:** `docs/harness/MASTER-wirelist.csv`, folder map `docs/harness/README.md` (with the current harness.design files and links), circuit plan `docs/harness/circuit-plan.md`, routes `docs/harness/routes/` (change only per DECISIONS B8), generated pin chart and DRB102 map `docs/harness/drawings/`, seats `sot/fuse-relay-map.csv`, parts `docs/sourcing/harness-parts.csv`.
- **CAN:** `link_g4x_can_setup.json` / `.lcs`, `switchboard_frames.json`, `CAN-BUS-ID-ALLOCATION-TABLE.md` (wire format), `CAN-BUS-MASTER-DESIGN.md` (architecture and PCLink apply), `ECUMASTER_SWITCHBOARD_SETUP.md`. Parity: `bench/check_parity.py`. Cluster decode: `center-cluster-esp32-p4` `main/canbus.c` (frozen).
- **RealDash / bench:** `link_g4x_realdash.xml`, `REALDASH-LAYOUT.md`, `BENCH-TEST.md`, `bench/`, `apps/trackcluster-can-sender/`.
- **Tune / fuel:** `tune/` (PCLink seeds; `tune/scripts/validate_tune.py`); `FUEL-SYSTEM.md`.
- **CAD / BOM:** model first, then drawing: never a drawing or parts-list change ahead of the Fusion model (DECISIONS "Drawing rules", Dan 2026-11-15). `cad/README.md` (the one model list); `docs/sourcing/PROJECT-BOM.xlsx` / `.csv` generated by `docs/sourcing/build_project_bom.py`.
- **Agent files:** `AGENTS.md` (this router; `CLAUDE.md` and `CLAUDE.local.md` were folded in here 2026-11-19), `CLAUDE.md` (one line, `@AGENTS.md`, so Claude Code loads this router; kept on purpose, Dan B2 a 2026-11-20: session-start, state-init and repo-cleanup leave it and never fold or delete it), `.claude/skills/` (pointers), `.claude/rules/` (the rules; `.cursor/rules/` is generated from them by `python <workstation>/scripts/state/rules_sync.py`, never hand-edited), `.claude/sot.json` (source-of-truth registry).

## Commands
Python 3.14. The gates, run before every commit:
```bash
python tools/check_all.py
python docs/harness/tools/check_wiring.py
python docs/harness/tools/build_drawings.py --check
python docs/harness/tools/check_corridors.py
python docs/harness/tools/trace_circuits.py --check
python bench/check_parity.py
python .github/scripts/test_docs_gates.py
python tune/scripts/validate_tune.py
python cad/check_drawings_current.py
python bench/can_bench.py --interface virtual --channel bench --bitrate 1000000 -v simulate-ecu --duration 1.5
```
Pin chart: `uv run --no-project --python 3.14 --with playwright --with openpyxl python docs/harness/tools/build_pin_chart.py`. State and registry: `python <workstation>/scripts/state/state_lint.py --repo .`, `sot_guard.py lint-registry`, `rules_sync.py --check` (same folder).

## Working rules
- CAN changes stay in sync across `bench/frames.py`, the JSON, `.lcs`, `switchboard_frames.json`, the RealDash XML, the sender UI and `CAN-BUS-ID-ALLOCATION-TABLE.md`. Multibyte fields BigEndian. RealDash reads 0x3EF-0x3F1 plus the 0x3EB gear byte only.
- No stale documents (R211): a new doc replaces older ones in the same PR; git history is the archive. Gate: `tools/check_doc_claims.py`. The master is the only hand-edited wiring CSV; the per-harness lists in `docs/harness/wirelists/` are generated by `build_drawings.py` and read back by its `--check` (F1, Dan B2 a).
- Keep local `main` in sync with `origin/main` (`git pull --ff-only` at session start and after every merge; DECISIONS B28, Dan 2026-10-31).
- `main` is protected: PRs only, the required check (Repo checks) green, squash-merge. Every PR body has a `Rows: <n>, <n>` line (store BACKLOG row IDs, kept from the old tracker) or `Rows: none` (A96 a), and a `State:` line (pr-closeout). Run the pr-closeout skill right after a PR opens (A96 a; B28). Never force-push.
- Always clean up after yourself: your own worktrees, branches and scratch files, deleted by name (Dan 2026-11-03; DECISIONS "Where data lives (B3)"); the worktree your session is running in stays for `tools/hygiene.ps1` (B28 "Never remove your own worktree").
- Standing yes (Dan Y2 a, Y3 a, 2026-11-09): delete leftovers Dan has already approved without asking again; start the next harness.design rebuild on the STATE / BACKLOG list without asking. harness.design files are changed or created without showing Dan first, and every report gives each changed or new file's https://app.harness.design/<documentId> link (Dan 2026-11-15; DECISIONS B6 "harness.design changes and links"), but only while the master and layout are unchanged: a master / SOT change (master, `sot/*`, layout tree or seeds, `corridors.json`, `spec.py`, DECISIONS rules) or any work outside harness files is asked first, and the report lists every master / SOT cell changed (Dan A48 a).
- Worktrees live inside the project folder at `.claude/worktrees/<name>` (git-excluded), never as sibling folders (Dan 2026-11-08).
- Bad data, stale files or drift found: fix it with the cleanup / consolidation / drift tools and skills (repo-cleanup, git-checker, session-sweep, the drift checks in `tools/check_all.py`) (Dan 2026-11-03).
- Sanitation sweep (Dan W1 2026-11-09): after every 3 merged PRs, the main session starts a read-only subagent that lists stale files, conflicts, broken pointers and STATE / BACKLOG drift against `origin/main` and reports to the main session; the main session fixes the findings in a normal PR (deletions still need Dan's yes).
- Generated: `PROJECT-BOM.*`, `docs/harness/drawings/*` and `docs/harness/wirelists/ST185-*-wirelist.*` come from their generators.
- harness.design conventions come from its own docs, not from memory (Dan 2026-11-09): before changing how a file is built or drawn (a generator, a new kind of end, splice, note, group or part), read the matching topic of the harness.design MCP editing guide (`read_editing_guide`: start at `editing-basics`, then `devices`, `splices`, `terminals`, `notes` ...) and search the user docs (`search_docs` / `read_doc`); re-read them every session that touches a file. What the docs say, and where this repo goes beyond them: `docs/harness/README.md` "harness.design".
- Drawing initials always `DG` (repo-root `.drawing-initials`, Dan X2 a). Layout: front RIGHT, driver side up. Dispatch: relay only. Ask Dan decisions with the question tool; a decision that depends on an image is asked in chat text (Dan 2026-11-01). Question IDs and where questions live: `.claude/rules/questions.md`.
- Agents never order parts: what Dan buys goes on the store BACKLOG (Dan; handoffs 2026-11-17).
- Do not edit `.claude/settings*.json` or `mcpServers` in normal work.

## Cloud agents
Cursor Cloud uses `.cursor/environment.json` + `.cursor/install.sh`. No USB-CAN / SocketCAN: test with `python-can` `virtual`; `-v` before the subcommand.
