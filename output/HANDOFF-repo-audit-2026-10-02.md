# HANDOFF: st185-link-ecu-config repo audit and remediation (2026-10-02, corrected)

**Status (2026-10-03): DONE.** WS0-WS3, WS5-WS7 merged to `main` one at a time (squash). WS4 held.
Open items: `docs/OPEN-ITEMS.md`. Plain-language summary:
`C:\projects\inbox\st185-research\REPO-AUDIT-SUMMARY.html`.

| WS | What | PR | Result |
|---|---|---|---|
| WS0 | Gate + baseline | - | Waited for the other task's rebase/push; `check_all.py` passed (19/19). Worked in a separate worktree so the main checkout was never touched mid-flight. |
| WS1 | CI + generated-file gates | #42 | `--check` mode for buylist/buildlist/make_min, no date stamp, LF output, new `checks.yml` (check_all + compile + parity), pre-commit hook, pinned requirements, Python 3.14. |
| WS2 | CAN contract + code | #43 | `switchboard_frames.json`, `bench/check_parity.py`, JSON turbo scale bug fixed, SW bits 0/1 retired, `mgp`->`map_kpa`, RealDash UI profile sends 0x3EB. |
| WS3 | CAN + wiring prose | #44 | Termination text (ECU + CAN-Lambda), 0x643 per CSB3 manual, 0x3EC/0x3ED receive marked undecided, 0x3EB, encode/decode wording, cluster pointers. |
| WS4 | Harness docs | held | Per correction 5 - listed in `docs/OPEN-ITEMS.md`. |
| WS5 | Agent config + map | #45 | CLAUDE.md / AGENTS.md map and paths, `.claudeignore`, PowerShell commands, skill paths. |
| WS6 | Tune + rd-build | #46 | `tune/scripts/validate_tune.py`, rd-build embedded XML removed, current `.rd`/sim/XML declared. |
| WS7 | Open-items ledger | #47 | `docs/OPEN-ITEMS.md` (28 rows, every row cites a live file:line) + this file. |

## Corrections from Dispatch (binding; they override the original text below)

1. D7 CAN termination is SETTLED: resistors at the ECU and CAN-Lambda, as drawn. WS3/WS7 only remove leftover "terminate at the Pi" text. *(Done - ECUMASTER Step 9, WIRING.md.)*
2. WS7: "Plan 6.46 PDU buy decision OPEN" is CLOSED - no PMU/PDM. *(Not listed.)*
3. WS2: do NOT add 0x3EC/0x3ED receive entries to the .lcs. Record ECU receive of cluster frames as an open item only. *(Done - OPEN-ITEMS row 1.)*
4. Leave ALL A/C wording alone; code changes per D3 OK. *(Done - only `frames.py`/`can_bench.py` SW bits and labels changed.)*
5. HOLD WS4 entirely; list its items as open items. *(Done - rows 17-20.)*
6. Don't touch `docs/harness/rebuild/*.harness`, `interfaces.json`, `sot/channels.csv`, harness.design, or the A7/B17 shield wording. *(Not touched. Note: commit 4c13b22, part of the batch rebased onto main on 2026-10-03, had already deleted the A7/B17 join ban "per Daniel's shield rules" - OPEN-ITEMS row 15 asks Daniel to confirm.)*
7. Sequential WS0 -> WS1 -> WS2 -> WS3 -> WS5 -> WS6 -> WS7, one branch + PR each, squash-merged, main re-pulled and check_all passing before the next. Wait for Copilot review; if none in ~10 min, merge and note it. *(Done - no Copilot review arrived on any PR; each PR has a comment saying so.)*
8. D1 approved: separate `switchboard_frames.json`. Archive rule via `.claudeignore` only; don't edit `.claude/settings.json`. *(Done.)*
9. Standing rules: never guess; G4X docs only; never commit `docs/research-hub.html`; never read `archive/`; keep line endings; no external flyback diodes; reconcile CAN against the frozen `canbus.c`. *(Followed. Line endings checked per file with `git ls-files --eol`.)*
10. Report after each workstream. *(Reports are in the session and in each PR body.)*

## Things the original handoff got wrong (found while doing it)

| Handoff said | Actually |
|---|---|
| README.md:55 channel count - ".lcs has 9 entries, identify the 9th" | The `.lcs` has **8** channels; README's "8 TX channels" was already right. |
| Switch bits 0,1 "of 0x640" (D3) | SW_MASK is **0x642** byte 4. 0x640 is analog 1-4. |
| `outputs/` is gitignored | It is not ignored and does not exist; left out of the map. |
| JSON / .lcs / table agree on every scale | They agree on the **wire**, but the JSON had Turbo Speed `scale: 1000` (decode value) in an encode-form file. Fixed to 0.001 in WS2. |
| HCR 150 TBD at HARNESS plan :2371 | Now at :2365 (file moved). OPEN-ITEMS cites live lines. |

## Original handoff (as received)

```
HANDOFF: st185-link-ecu-config repo audit and remediation (2026-10-02)
Context: Read-only audit of ownership, pointers, SoT consistency and maintenance tooling (archive/ untouched). check_all.py was NOT run. Wire layouts for 0x3E8-0x3F1 agree across JSON, .lcs, frames.py, ID table, XML and sender UI. The drift is in surrounding text, missing parity checks, CI coverage, and stale pointers.

Ownership map: Pins SoT sot/channels.csv -> XTREMEX-IO-TABLE.html (gate: sync_io_table.py --check). Looms docs/harness/rebuild/*.harness (15) + interfaces.json -> min/, HARNESS-BUILD-LIST.csv, NEED-TO-BUY.md (19 gates in check_all.py). CAN wire contract link_g4x_can_setup.json -> .lcs, bench/frames.py, ID table, RealDash XML, sender UI (no gate). Cluster truth: cluster repo main/canbus.c -> local CANBUS-ENCODE-DECODE-REFERENCE.html (no gate). Tune: tune/engine_constants.yaml, tune/tables/*.csv -> tune/docs/* (no gate). Research hub: docs/build-research-hub.py -> docs/research-hub.html (Action only).

Rules for every workstream: edit ONLY the files in your "Owns" list; requests for other files go in the report. Never read archive/. Never commit docs/research-hub.html. Unless you're WS1, after running check_all do `git checkout -- docs/harness/NEED-TO-BUY.md docs/harness/HARNESS-BUILD-LIST.csv docs/harness/min` before committing. git pull before push. Anything found and not fixed goes in the report as an open item.

Shared decisions: D1 canonical JSON stays link_g4x_can_setup.json; switchboard 0x640-0x643 goes in a NEW switchboard_frames.json. D2 JSON uses PCLink encode (raw = value*scale + offset); .lcs/table/frames.py use decode. Both stay, and the convention gets stated. D3 switch bits 0,1 of 0x640 and analog 1 are UNASSIGNED. D4 0x643 L1-L4 source is the ECU; outputs unused/LED-only. D5 RealDash also reads 0x3EB. D6 cluster repo path is C:\projects\shipping\center-cluster-esp32-p4; decode truth is main/canbus.c (main/protocols/link_g4x.json does not exist). D7 (see correction 1).

Ownership matrix:
WS1 CI + generated-file gates: .github/workflows/**, .githooks/** (new), docs/harness/buylist.py, buildlist.py, make_min.py, check_all.py, NEED-TO-BUY.md, HARNESS-BUILD-LIST.csv, min/**, bench/requirements.txt, apps/trackcluster-can-sender/requirements.txt, rd-build/tools/requirements.txt, .gitattributes
WS2 CAN contract + code: link_g4x_can_setup.json, .lcs, switchboard_frames.json (new), bench/frames.py, bench/can_bench.py, bench/check_parity.py (new), apps/trackcluster-can-sender/app.py, ui/index.html, link_g4x_realdash.xml, .claude/rules/can-frame-contracts.md, .cursor/rules/*can*, .claude/skills/update-can-frame-contract/**, run-can-bench-scenarios/**, maintain-realdash-xml-mapping/**
WS3 CAN + wiring prose: CAN-BUS-ID-ALLOCATION-TABLE.md, CAN-BUS-MASTER-DESIGN.md, CANBUS-LINK-G4X-CONFIG.md, CAN-CONFIG-STATUS.md, ECUMASTER_SWITCHBOARD_SETUP.md, BENCH-TEST.md, REALDASH-LAYOUT.md, README.md, WIRING.md, CANBUS-ENCODE-DECODE-REFERENCE.html
WS4 (HELD): docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md, docs/enclosures/README.md, docs/harness/README.md, ACAMP-SPUR-LABELS.md, RECONCILIATION-RULES.md, SHIELD-RULES.md, docs/electrical/**, the stray research-hub.html.bak
WS5 Agent config + project map: CLAUDE.md, AGENTS.md, .claude/settings.json (read-only per correction 8), .claude/rules/harness-wiring-conventions.md (don't touch the shield wording), .claude/skills/extend-trackcluster-can-sender/**, .cursor/environment.json, .cursor/install.sh, .cursor/hooks.json, .claude/hooks/**, .claudeignore (new)
WS6 Tune + rd-build cleanup: tune/** (incl. new tune/scripts/validate_tune.py), docs/intercooler-turbo-study/model/inputs.yaml, rd-build/** except rd-build/tools/requirements.txt, realdash-simulation.html, st185_dash.rd
WS7 Open-items ledger: docs/OPEN-ITEMS.md (new); read-only everywhere else.
Coupling: WS1 adds a CI step `python bench/check_parity.py` guarded with `if: hashFiles('bench/check_parity.py') != ''`. WS5's CLAUDE.md map points to docs/OPEN-ITEMS.md and switchboard_frames.json.

WS1: make check_all.py + compile checks run on every relevant PR; stop generated files lying about staleness. buylist.py (~line 208) stamps the date -> remove it or derive it from content/git. Add --check mode (regenerate in memory, diff, exit 1) to buylist.py/buildlist.py/make_min.py; check_all calls --check, with --write kept for local use. New workflow: check_all + py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py + the conditional parity step; triggers sot/**, docs/harness/**, XTREMEX-IO-TABLE.html, bench/**, apps/**, the CAN files, and the workflow itself. .githooks/pre-commit refuses a staged docs/research-hub.html; a one-line setup script for core.hooksPath (+ merge.ours.driver). Report the CLAUDE.md line for WS5. Pin the 3 requirements files; align the Python version (CI 3.12 vs local 3.14) and state the choice. Verify: check_all twice -> git status clean after the 2nd run; CI green on a PR; a perturbed pin-table row makes CI fail.
WS2: create switchboard_frames.json (0x640-0x643) from the ID table + frames.py, with unified cycle wording. frames.py:285-289 retire SW_EVAP_CORE/SW_AC_REQUEST (D3); can_bench.py:638,653-657,777 fix labels and bit cycling; rename mgp->map (frames.py:80,83). JSON/.lcs: header comment stating encode vs decode (D2); fix the _comment pointing at the nonexistent link_g4x.json (D6). (0x3EC/0x3ED: see correction 3.) bench/check_parity.py (stdlib): JSON vs frames.py vs XML vs ui/index.html profiles for 0x3E8-0x3F1 + WARN bits; switchboard_frames.json vs frames.py; parse the ID table markdown; .lcs vs JSON; exit 0/1 with a per-field diff. ui/index.html: the RealDash profile includes 0x3EB; lines 211-212 stop pointing at the removed canbus-live-sender. Update can-frame-contracts.md (+ the .cursor mdc) and the update-can-frame-contract skill (to run check_parity.py); fix relative paths in the other 2 CAN skills. Verify: check_parity exits 0; a mutation exits 1; py_compile; reconcile against canbus.c.
WS3: CAN-BUS-MASTER-DESIGN.md:60 0x643 source "TBD" -> ECU (D4). ECUMASTER_SWITCHBOARD_SETUP.md:235,286 L1-L4 fan/AC -> unused/LED-only, with consistent 0x643 cycle wording (225). BENCH-TEST.md:235 drop cabin temp (A/C wording otherwise left alone per correction 4). README.md:55 channel count (verify against the .lcs: 9 entries, identify the 9th), README.md:59-63 echo target (0x3EF bytes 3/5) and the decode-vs-encode wording; README.md:28 and REALDASH-LAYOUT.md:12 add 0x3EB. CAN-CONFIG-STATUS.md refresh (2026-09-27 unassignments, switchboard JSON, parity script, 0x3EB, cluster path). CANBUS-LINK-G4X-CONFIG.md:1 pointer. CANBUS-ENCODE-DECODE-REFERENCE.html: header note that it mirrors the cluster copy and differs only at line 161. WIRING.md: non-termination fixes + remove any terminate-at-Pi leftovers. Verify: greps for the stale phrases come back empty.
WS5: CLAUDE.md: cluster path (D6); remove the mentions of the nonexistent .cursor/hooks.json and .claude/hooks/; correct "three skills dirs" (remove the empty .cursor/skills and .agents/skills locally); reconcile the settings.json sentence. Project Map adds WIRING.md, FUEL-SYSTEM.md, ECUMASTER_SWITCHBOARD_SETUP.md, CAN-CONFIG-STATUS.md, the reference HTML (mirror), switchboard_frames.json, bench/check_parity.py, docs/OPEN-ITEMS.md, output/, docs/ subtrees, tune/limits.yaml|docs|scripts, outputs/ (gitignored); replace the @./XTREMEX-IO-TABLE.html auto-include with a pointer line. AGENTS.md: "14 files" -> 15, cluster path, stale canbus-live-sender mentions. .claudeignore for archive/. The extend-trackcluster-can-sender skill gets full paths. Add WS1's setup line. Verify: a scripted existence check of every path in CLAUDE.md/AGENTS.md.
WS6: tune/scripts/validate_tune.py checks the 14 CSVs (axis monotonicity, shared MAP 20-200 / RPM 800-7000 axes, shape), ceilings (18/30 psi) vs engine_constants.yaml, and that referenced files exist. inputs.yaml reads from engine_constants.yaml or gets a diff check. rd-build/PLAN.md:116,132-172 remove the embedded XML copy and the "Corrected in" note; BUILD-NOTES.md:48 / PLAN.md:283 stop treating canbus-live-sender as live; PLAN.md:183, README.md:33 stale Cabin Temp wording. rd-build/README.md: declare the current realdash-root version (v2-v10), the current st185_dash.rd, and the canonical simulation HTML; delete nothing. Verify: validate_tune exits 0; a mutation exits 1; grep shows no live-sender references.
WS7: docs/OPEN-ITEMS.md, one table (item, owner, source file:line, status, what unblocks it). Seed: switchboard analog 3-8 / rotary 1-5 TBD (ECUMASTER_SWITCHBOARD_SETUP.md:61-64,211); A/C spur TBDs (ACAMP-SPUR-LABELS.md:27,41), noted as superseded by the reconcile plan; OEM flying-lead EWD locators TBD (interfaces.json:297-356; build list rows 239,277,303,339-349); placeholder connector parts, HCR 150 resistor value (HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md:2068,2371), ENGINE-ROOM ratings (ENGINE-ROOM-POWER-REDISTRIBUTION.md:116); RealDash headless automation blocked (rd-build/FINDINGS.md:21, PLAN.md:329); cluster decode coverage of 0x3EC/0x3ED/0x3EF-0x3F1 unconfirmed (canbus.c:179-183); 0x3EC/0x3ED ECU-receive undecided (correction 3); all held WS4 items; and every "request"/unfixed item from WS1-WS6. Every row cites a real file:line.
Acceptance after all merges: check_all, check_parity, validate_tune, py_compile all pass; git status clean; CI green.
```
