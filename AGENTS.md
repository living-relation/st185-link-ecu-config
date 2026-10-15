# AGENTS.md

> **Project focus (DECISIONS R102, Dan 2026-10-15) - the ONLY scope, in order:** (1) wiring sorted
> so Dan can build the harnesses; (2) ECU base maps; (3) ECU CAN config written and checked;
> (4) CSB3 config finished. Do not add to-dos outside these four; open a new `docs/OPEN-ITEMS.md`
> row only for a blocker of one of them.

> ## Before any wiring or CAN change — binding on every agent
>
> **First read `docs/harness/redesign/DECISIONS.md`, section "Binding rules from Daniel"
> (R1-R116).** It is the ONE home for every rule Daniel has set (harness split, OEM wiring,
> shields, wire and parts, drawing conventions, CAN routing, setup time); nothing else in
> this repo restates them. Then read **`docs/RECONCILIATION-RULES.md`** for the procedure.
> Three rules, all non-optional:
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
>
> **CAN config is never parked for setup time (DECISIONS R80):** an ECU CAN change (e.g. a CSB3
> bit) is made now in the repo CAN files (`link_g4x_can_setup.json` / `.lcs`, `switchboard_frames.json`,
> CAN docs) with `bench/check_parity.py` green; Daniel uploads the `.lcs` later. Only the import and
> live tests wait for the ECU.

## Mission
- Keep `Link G4X XtremeX` CAN configuration, `RealDash` channels, and bench tooling synchronized.
- Treat `link_g4x_can_setup.json` as the canonical config contract for IDs, scaling, and offsets.
- Preserve compatibility with frozen cluster firmware assumptions documented in `README.md` and the cluster repo's `CANBUS-ENCODE-DECODE-REFERENCE.html` (pointer only, never copied here).

## Project Map
- **Core CAN contracts**: `link_g4x_can_setup.json` (ECU frames, PCLink encode form), `link_g4x_can_setup.lcs` (decode form; also the ECU receive channels 0x3EC/0x3ED and CSB3 0x640/0x642), `switchboard_frames.json` (CSB3 0x640-0x643 plus its `ecu_receive` map), `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`, `ECUMASTER_SWITCHBOARD_SETUP.md`, `CANBUS-ENCODE-DECODE-REFERENCE.html` (a POINTER page to the cluster repo's file - no cluster file is copied into this repo; CI reads the cluster repo read-only at run time).
- **CAN parity gate**: `bench/check_parity.py` - JSON, `.lcs`, ID table, `bench/frames.py`, RealDash XML, sender UI and `switchboard_frames.json` must agree. Runs in CI (`.github/workflows/checks.yml`).
- **Doc hygiene (warn-only, CI)**: `.github/scripts/check_doc_duplicates.py` - one owner per fact: lists any passage of 6+ identical lines copied between tracked `.md` files. Keep the passage in one file and link to it from the others.
- **Doc size guard (warn-only, CI)**: `.github/scripts/check_doc_size.py` - warns when a tracked `.md` passes 1,500 lines, and when a top-level `.md` is not named in this file's project map (so add every new top-level doc here). No auto-archiving or age sweeps.
- **RealDash contract**: `link_g4x_realdash.xml`, `REALDASH-LAYOUT.md`, `realdash-simulation.html`.
- **Bench tooling**: `bench/can_bench.py`, `bench/frames.py`, `bench/requirements.txt`, `BENCH-TEST.md`.
- **Desktop sender app**: `apps/trackcluster-can-sender/app.py`, `apps/trackcluster-can-sender/ui/index.html`, `apps/trackcluster-can-sender/BUILD.md`, `apps/trackcluster-can-sender/requirements.txt`.
- **Automation assets**: `rd-build/tools/automation_helper.py`, `rd-build/tools/SETUP.md`, `rd-build/PLAN.md`, `rd-build/FINDINGS.md`.
- **Wiring SoT**: `sot/channels.csv` (every ECU pin and channel). `XTREMEX-IO-TABLE.html` is its visual face. `WIRING.md` covers the cluster boards and the 5-node CAN topology.
- **Harness / electrical**: `docs/harness/rebuild/*.harness` - drawings, **not a source of truth** (Daniel, 2026-10-04: they follow `sot/channels.csv`; never generate truth docs from them) (one physical harness per file, ownership in `docs/harness/interfaces.json`; see `docs/harness/README.md`), gate `python docs/harness/check_all.py`. ECU looms follow the ECU connector letter (`ST185-A-cabin` / `-B-cabin` / `-A-engine` / `-B-engine`) - canonical rule `docs/RECONCILIATION-RULES.md` Rule 3, gate `validate_bulkhead_letter.py`; `docs/SHIELD-RULES.md`, `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`. Drawing notes too long for the frame: `docs/harness/HARNESS-NOTES.md` (DECISIONS R92). Circuit tracer (end-to-end trace of every circuit with simulated ECU / CSB3 / CAN logic, both states): approved plan `docs/harness/CIRCUIT-TRACE-PLAN.md`, DECISIONS R89, built only when all 15 drawings are final (OPEN-ITEMS row 117).
- **Engine calibration**: `tune/engine_constants.yaml`, `tune/limits.yaml`, `tune/tables/*.csv`, `tune/docs/`, `tune/scripts/` (incl. `validate_tune.py`), `tune/README.md` — PCLink seeds only; not an I/O or CAN source. `FUEL-SYSTEM.md` is fuel hardware reference, not CAN.
- **Project files stay in this repo** (DECISIONS R67): nothing for ST185 goes in the `C:\projects` root, `_scratch`, `_tools`, `C:\projects\cad` or `inbox`. CAD: the one `cad/` tree, by part - `cad/busbar/` (five designs + `src/`), `cad/fusebox/`, `cad/enclosures/` (VRC, CSB3), `cad/drb102-plate/`; newest version of each model only. Research / pick pages: `docs/research/` (latest per topic). Status page: the hub's "Project status" section (see **Dashboard** below). An in-flight handoff: `output/` (deleted when done). Heavy CAD (every STEP, STL and Fusion `.f3d`, plus the busbar drawing PDFs) is gitignored and kept in the same `cad/` folder of the main checkout. Fusion allows only 10 editable documents (DECISIONS R74): reuse the part's existing document, never make throwaway ones, and list finished documents for Dan to set read-only. Local-only working files and vendor downloads: `_research/` (untracked).
- **Other docs/**: `docs/devices/`, `docs/enclosures/`, `docs/sourcing/`, `docs/procedures/`, `docs/intercooler-turbo-study/`, `docs/5sgte-project-data/` (research), `docs/research-hub.html` (generated, see below).
- **CAD index**: `cad/README.md` - the ONE list of every CAD model (summary page, local STEP/STL/f3d paths, Fusion link, external fuel hanger); a new model gets a row in the same PR (DECISIONS R77). Its `Selected for build` column (yes on the one version of each item being built, no on the rest) is the ONLY place the build choice lives; the hub shows the selected set first and folds the rest into "Superseded / alternatives - not used"; flip the flags in the same PR that picks a new rev.
- **CAD trimetrics + power package** (DECISIONS R83 / R84): every CAD model has a tracked trimetric PNG beside it (`cad/<model>/trimetric*.png`; fuel hanger in the reference-only `cad/fuel-hanger/`), rendered headless from its STEP by `cad/render_trimetric.py` (sources and dates in `cad/trimetrics.json`). A new or changed model re-renders its trimetric in the same PR. The power distribution package (POWER + LOGIC boxes, battery relay block, bus bar B rev3, VRC + CSB3 enclosures) is always shown as one package: `cad/README.md` "Power distribution package" table. Render (WSL, repo root): `~/projects/handbuilt-models/.venv/bin/python cad/render_trimetric.py --src /mnt/c/projects/active/st185-link-ecu-config [--only <id>]`.
- **Project tracker**: `docs/OPEN-ITEMS.md` - THE one tracker: every unresolved item (owner, source, what unblocks it) plus the dated project history. Decisions and every binding rule live in `docs/harness/redesign/DECISIONS.md` ("Binding rules from Daniel" is the rules home).
- **Route drawings**: `docs/harness/routes/` - Dan's approved route for each harness (one HTML per route, current version only); lint `docs/harness/check_route_drawings.py`.
- **Handoffs**: none kept. A finished handoff is deleted; open work goes into `docs/OPEN-ITEMS.md` (`output/` is for a handoff in flight only).
- **Agent ecosystem**: `.claude/skills/` (4 repo skills: `run-can-bench-scenarios`, `update-can-frame-contract`, `maintain-realdash-xml-mapping`, `extend-trackcluster-can-sender` - CAN/bench; see **Skills** below for the 5 global ST185 skills), `.claude/rules/` + `.cursor/rules/` (thin pointers to the rule owners - `DECISIONS.md`, `RECONCILIATION-RULES.md`, this file's Working Rules - never copies), `.claude/settings.json` (permission allow-list), `.cursor/environment.json` + `.cursor/install.sh` (Cursor Cloud bootstrap), `.githooks/` (pre-commit refuses `docs/research-hub.html`). No agent hooks are configured.

## Skills
Five skills for this project are saved **globally** (user-level, not in this repo) at
`C:\Users\danie\.claude\skills\st185-*\SKILL.md` - prefixed `st185-` so they don't collide
with other projects, and scoped by their own description to this repo. Their bodies are
not copied here; this is a pointer only.

- [`st185-apply-route-markup`](C:\Users\danie\.claude\skills\st185-apply-route-markup\SKILL.md) - redraw a route drawing in `docs/harness/routes/` from Dan's markup and add its top view (drawing-only).
- [`st185-build-harness-from-sot`](C:\Users\danie\.claude\skills\st185-build-harness-from-sot\SKILL.md) - build/check one `docs/harness/rebuild/*.harness` file against the SoT, never the reverse.
- [`st185-change-sot`](C:\Users\danie\.claude\skills\st185-change-sot\SKILL.md) - edit `sot/channels.csv` / `docs/harness/interfaces.json` and run the required check sequence, then list downstream harness files to redraw.
- [`st185-pick-parts`](C:\Users\danie\.claude\skills\st185-pick-parts\SKILL.md) - pick real part numbers in the on-hand-then-TE sourcing order; never guess a part number.
- [`st185-ship-change`](C:\Users\danie\.claude\skills\st185-ship-change\SKILL.md) - PR a finished change to protected `main`, squash-merge, clean up the worktree/branch.

The route-drawing lint they call, `docs/harness/check_route_drawings.py`, lives in this repo
and runs as a HARD gate in `check_all.py`, since it's a test, not a skill.

## Scope
- This repo is CAN configuration + bench/tooling for ST185 TrackCluster.
- Primary code paths are `bench/`, `apps/trackcluster-can-sender/`, and `rd-build/tools/`.
- Primary contracts are `link_g4x_can_setup.json` and `link_g4x_realdash.xml`.

## Source Of Truth
- CAN IDs, offsets, scaling: `link_g4x_can_setup.json` (ECU frames, PCLink encode form) and `switchboard_frames.json` (0x640-0x643). Parity gate: `python bench/check_parity.py`.
- Architecture and allocation: `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`.
- Bench behavior: `bench/frames.py`, `bench/can_bench.py`, `BENCH-TEST.md`.
- RealDash channel definitions: `link_g4x_realdash.xml`.
- Engine-room power splice table (where every ex-J/B2 / R/B load lands, §5.4; the OEM engine-bay boxes are removed, R12): `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`.
- Wiring SoT (every ECU pin and channel): `sot/channels.csv`. Visual face: `XTREMEX-IO-TABLE.html` (gated by `docs/harness/sync_io_table.py --check`).
- The harness drawings - **not a source of truth** (Daniel, 2026-10-04: they follow `sot/channels.csv`; never generate truth docs from them): `docs/harness/rebuild/*.harness` (15 files, one physical harness per file; wires between files are drawn broken off in both; the four ECU looms split by connector letter 2026-09-28; `docs/harness/README.md`). Ownership/interfaces: `docs/harness/interfaces.json`, `docs/harness/redesign/`. Gate: `python docs/harness/check_all.py`.
- Every binding wiring / parts / drawing rule: `docs/harness/redesign/DECISIONS.md` "Binding rules from Daniel". Reconcile procedure: `docs/RECONCILIATION-RULES.md` Rule 1; ECU loom letter detail: Rule 3.

## Board / progress snapshot
- Claude progress board is a **stale artifact** (last updated 2026-09-01). Do not treat it as SoT.
- `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` is the dated decision history (its §6 was
  the build-rule log until 2026-10-12). It is **not a rules home any more**: the binding rules
  are `docs/harness/redesign/DECISIONS.md` "Binding rules from Daniel", and where §6 disagrees
  with them the plan doc is history.

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
  link to it, never copy cluster files here; the pointer page in this repo is `CANBUS-ENCODE-DECODE-REFERENCE.html`.
- Its `sdkconfig` and `main/Kconfig.projbuild` define the
  cluster's TWAI GPIO pinout and transceiver wiring — see `WIRING.md` and
  `CAN-BUS-MASTER-DESIGN.md` in this repo for how it fits the 5-node topology.
- Do not introduce a CAN ID, frame layout, or wiring change here that the cluster
  firmware doesn't already decode/expect — the cluster is not being modified as
  part of work in this repo.

If a local checkout of `center-cluster-esp32-p4` exists (commonly
`C:\projects\active\center-cluster-esp32-p4`), prefer reading its source files directly
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

## Current Runnable Paths
- `bench/can_bench.py` for monitor/simulate/test workflows.
- `apps/trackcluster-can-sender/app.py` for desktop CAN sender UI.
- `rd-build/tools/automation_helper.py` for local RealDash editor automation.

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

### Run sender app (PowerShell)
```powershell
python apps/trackcluster-can-sender/app.py
$env:TC_DEVICE='cluster'; python apps/trackcluster-can-sender/app.py
$env:TC_DEVICE='realdash'; python apps/trackcluster-can-sender/app.py
```

### Quick checks
```bash
python docs/harness/check_all.py          # harness gates; --check mode, never writes
python docs/harness/audit_wire_spacing.py # wire overlap / spacing: schematic W1 (R86), layout W2 (R107)
python docs/harness/audit_layout.py      # layout view: overlaps / hidden bundles (R107); re-place: layout_tree.py
python bench/check_parity.py              # CAN contract parity
python tune/scripts/validate_tune.py      # tune seed tables (needs PyYAML)
python .github/scripts/check_doc_duplicates.py   # copied .md passages (warn-only)
python .github/scripts/check_doc_size.py         # >1,500-line / unlisted top-level .md (warn-only)
python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py
python rd-build/tools/automation_helper.py size
python rd-build/tools/automation_helper.py screenshot rd-build/rd_screen.png
```

### Route-drawing lint
The approved route drawings are `docs/harness/routes/` (current version only; git history is
the revision record). `check_all.py` runs the lint as a HARD gate; by hand:
```bash
python docs/harness/check_route_drawings.py                      # all routes
python docs/harness/check_route_drawings.py docs/harness/routes/ROUTE-5-A-CABIN.html
```

## Working Rules
- Keep CAN changes synchronized across `bench/frames.py`, `link_g4x_can_setup.json`, `switchboard_frames.json`, the `.lcs`, the RealDash XML, the sender UI and `CAN-BUS-ID-ALLOCATION-TABLE.md` — `python bench/check_parity.py` must pass.
- Open items live in one table: `docs/OPEN-ITEMS.md`.
- `docs/dispatch/DISPATCH-RULES.md` is for Claude Dispatch only; other agents ignore it.
- harness.design format / how-to: read its docs, never guess, and cite the page in the PR when it drives a format choice - https://docs.harness.design/feature/local-files/json-format (v1.2 `.harness` / `.harnesslib` - the files follow the desktop app's current schema, DECISIONS R111), https://docs.harness.design/feature/part-libraries, https://docs.harness.design/feature/desktop, https://docs.harness.design/feature/pinouts, https://docs.harness.design/files/harness/editing-guide.md.
- Dan edits the looms in the harness.design desktop app on the files in `docs/harness/rebuild/` (live files, no upload step; `docs/harness/README.md` "Open in the desktop app"); agents pause while he edits, the saved file wins. Drawing conventions: global skill `harness-design`; harness.design docs win.
- Schematic wires never overlap and parallel runs keep a 3-line-width gap (DECISIONS R86, Daniel 2026-10-14; the drawings keep the real insulation colours). After moving nodes or adding wires, re-route: `python docs/harness/route_wires.py rebuild/<file>.harness` (writes each wire's `layoutPoints`; `--check` = dry run), gate `docs/harness/audit_wire_spacing.py` (in `check_all.py`). Path model of the app's routing: `docs/harness/wire_paths.py`. Snapshots: the app's Export > PDF; agents' fallback PNG `docs/harness/render_schematic.py`.
- Every wire carries its circuit's ident bands (`identColors`, Blue / Yellow / White) and bundles ending at a connector carry a printed end label (DECISIONS R87; circuits in `docs/harness/interfaces.json` "identBands"; gate `docs/harness/audit_ident_bands.py`, in `check_all.py`). The band code goes at every end of the circuit.
- The deliverable for each harness is its `.harness` file in `docs/harness/rebuild/` (DECISIONS R88, amended 2026-10-15, K5): ident bands, end labels, title block and notes stay; there is no PDF export step and no gate for it (`pdfExportSettings` stays in the files, unchecked).
- The part library is the master (Daniel, 2026-10-12): change a part in `docs/harness/rebuild/ST185.harnesslib` FIRST, then copy it into the drawings, in the same PR; any difference between a drawing's part and the library fails, no exceptions (gate `docs/harness/check_harnesslib.py`, in `check_all.py`; `--add-missing` copies new parts).
- Keep `ST185:` names in `link_g4x_realdash.xml` unchanged unless migration is explicitly requested (renames break `.rd` gauge bindings).
- RealDash frame scope is the documented ECU streams `0x3EF`-`0x3F1` plus one approved exception (2026-09-04): the gear byte of `0x3EB` (`ST185: Gear`) for the reverse-camera auto-switch - see the CAN scope note in `REALDASH-LAYOUT.md` and the SCOPE note in the XML. Do not widen it to other `0x3E8`-`0x3EE` bytes without updating both.
- Keep conversion parity between the XML formulas and `bench/frames.py` scaling, and warning-bit mapping parity (`startbit`) between XML and the `bench/frames.py` bit constants.
- Prefer minimal targeted edits; avoid broad rewrites of stable docs.
- main is protected (ruleset "Protect main"); all changes go through PRs with "Repo checks" and "Protect research hub" green; only the research-hub bot (deploy key `RESEARCH_HUB_DEPLOY_KEY`) bypasses.
- Root `link_g4x_realdash.xml` is the single copy; do not reintroduce a duplicate under `rd-build/`.
- Before any CAN ID/frame or wiring change, check compatibility against `center-cluster-esp32-p4` (see **Related Repos** above).
- Keep all multibyte CAN fields BigEndian unless a source file explicitly documents otherwise.
- For warnings in `0x3F1` byte 6, keep bit mapping consistent with `bench/frames.py` constants and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Frame routing (who reads which frame, cluster frozen and first): `docs/harness/redesign/DECISIONS.md` R51; procedure `docs/RECONCILIATION-RULES.md` Rule 2.

### Python tooling
- Follow the existing adapter handling style in `apps/trackcluster-can-sender/app.py` (`gs_usb`, `slcan`, `seeedstudio`, vendor interfaces).
- Keep CAN payload validation strict (`11-bit ID`, `8-byte payload`) before transmit.
- Keep CLI scripts small, explicit and usage-driven, like `rd-build/tools/*.py`.
- Keep dependency docs aligned with the nearest `requirements.txt` (`bench/`, `apps/trackcluster-can-sender/`, `rd-build/tools/`).
- GUI automation scripts keep the desktop-only constraints documented in `rd-build/FINDINGS.md` and `rd-build/tools/SETUP.md`.

## Known Gotchas
- Older docs referenced removed paths like `apps/canbus-live-sender/`; use `apps/trackcluster-can-sender/`.
- The sibling repo `st185-furyx-base-map` holds an older **FuryX-era** copy of `link_g4x_can_setup.json`/`.lcs` and `CANBUS-LINK-G4X-CONFIG.md`. This repo's versions are newer (frames `0x3EF`/`0x3F0`/`0x3F1`, 2-byte oil/fuel pressure, `MAP` not `MGP`) — never copy CAN files from it. Its `io_assignments.yaml` is FuryX-only and contradicts `XTREMEX-IO-TABLE.html`.
- `rd-build/tools/automation_helper.py` depends on desktop permissions and local GUI session; headless runs are unsupported per `rd-build/FINDINGS.md`.

## Change Workflow
1. Identify scope: CAN contract, XML mapping, bench code, app behavior, or docs.
2. Update the smallest authoritative source first (`link_g4x_can_setup.json` for wire contract, `link_g4x_realdash.xml` for RealDash input contract, `bench/frames.py` for encode/decode behavior).
3. Propagate to dependents (`CAN-BUS-ID-ALLOCATION-TABLE.md`, `BENCH-TEST.md`, `REALDASH-LAYOUT.md`) only where drift appears.
4. Run targeted command checks from **Fast Commands**.
5. Report what changed and where parity was revalidated.

## MCP / Integration Notes
- Optional MCP example exists at `rd-build/tools/mcp.example.json` for desktop control experiments.
- `.claude/settings.json` exists (allow-list for git/python/pip/pytest). Do not edit it, `.claude/settings.local.json`, or `mcpServers` configs as part of normal work.

## Local environment

- Local checkout of this repo on dansPC is `C:\projects\active\st185-link-ecu-config`.

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

## Dashboard
One dashboard: the **research hub**, `docs/research-hub.html`, generated by `docs/build-research-hub.py` and committed only by the "Regenerate research hub" Action (see **Generated files** below). **Online (GitHub Pages, serves `/docs` from `main`): https://living-relation.github.io/st185-link-ecu-config/research-hub.html** Its top section, **Project status**, is for Dan on his phone or PC: open questions, his open items, route and CAD approval status, the CAD models gallery (trimetric + true local file paths, R83), the power distribution package (R84), recent merged PRs, build time. The old claude.ai live dashboard (`tools/dashboard/`) was deleted 2026-10-14 (DECISIONS R78, retired).

- Open questions for Dan: `docs/status/questions.json`, the only hand-kept input (tracked; Dispatch edits it by PR). Schema: `{"updated": "YYYY-MM-DD", "questions": [{"id":"M1","topic":"...","text":"...","options":[{"value":"A","label":"...","recommended":true}]}]}`. Remove a question once it is settled. Dan answers in the Dispatch chat with the ID and letter. IDs run A1..A9, B1..B9 ... Z9, then wrap to A1 (DECISIONS R115).
- Board at the top of the hub (2026-10-15): needs-Dan box, four goal bars (done / tagged rows in `docs/OPEN-ITEMS.md`, tags `[G1]`-`[G4]`; closed tagged rows stay in the tracker so the bars keep their "done" count), 15 loom tiles, and a "Now" strip. Hand-kept input: `docs/status/hub.json` (loom approval date + `needs_reapproval` list, running sessions; Dispatch edits it by PR). Loom thumbnails are `docs/harness/thumbs/*.png`, made by `render_layout.py` (fallback renderer, not an app export) at `--scale 0.25` then shrunk to 360 px; re-render one when its loom changes.
- Grok CAD jobs (DECISIONS R106): `docs/status/grok-jobs.json`, hand-kept by PR like the questions; fairsolid CAD jobs go to the Grok bot as a handoff zip and get an entry there (id, title, goal, status queued / sent / returned / accepted, zip, date, notes). The hub's "Grok CAD jobs" section renders it.
- Everything else is read at build time: `docs/OPEN-ITEMS.md` (keep its table format: leading ID cell, owner in column 4, status in column 6), the status box on each `docs/harness/routes/ROUTE-*.html`, the table in `cad/README.md`, and `git log`. A change that moves or renames any of these also needs `docs/build-research-hub.py` checked.
- CAD file locations: the page's CAD table comes from `cad/README.md` plus `cad/model-files.json` (the list of STEP/STL/f3d files, refreshed whenever `python docs/build-research-hub.py` runs on a PC that has the heavy files - commit it with the change; also lists the newest `revN` of the Fairsolid fuel hanger). A model file with no README row, an unnamed `.f3d`, or a stale hanger rev shows a warning on the page and on stderr.
- Open it: after a merge the bot regenerates the file; open https://living-relation.github.io/st185-link-ecu-config/research-hub.html (Pages, a minute or two after the bot's commit), or run **Pull All Repos** and open `C:/projects/active/st185-link-ecu-config/docs/research-hub.html`. Pages serves only `docs/`: links and images that point outside it (`../cad/...`) are switched to their GitHub copies by the page's own script when it runs on `github.io`.

## Generated files - who owns them

| File | Owner | Rule |
|---|---|---|
| `docs/research-hub.html` | **The "Regenerate research hub" Action** | **Never commit it.** (Its "Project status" section is described under **Dashboard** above.) Run `docs/build-research-hub.py` locally to preview, then `git checkout -- docs/research-hub.html` before you commit. PRs that touch `docs/**` (or the workflow) run the generator as a check and attach the HTML artifact. The bot commits the file to `main` only, after those changes merge. Committing it locally is what causes the rebase conflicts. |
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
- `python docs/harness/check_all.py` is the wiring audit. The 2026-09-18 conflict sheet is retired (git history); its bh_c questions are settled (bulkhead C deleted).
