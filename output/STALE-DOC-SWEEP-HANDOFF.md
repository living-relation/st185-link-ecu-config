# Stale-document sweep - handoff

Started 2026-10-11. Goal: walk the file tree one document at a time and find content that is
superseded or conflicts with newer decisions. Daniel says "ok" to move to the next document;
this file is updated at each step. Not authoritative - the files it describes win.

## Reference change driving the sweep

PR #83 (eda59b6, 2026-10-11), fuse box Option B: the glove-box fuse box is now Bussmann LMI
(L1-L7) + Eaton RFRM + 3x MTA 0301491, drawn only in `ST185-CabinPower`. Retired: TE
`2141029-1` F1-F13 block, the second fuse block, ANL 100 A, `gbx_body` in EngineRoom-C, the old
F-number / HCFB labels. Also: J/B No.2 is on the **driver** side (ENGINE-ROOM doc §2, 2026-09-29).

## Method

`Grep` for retired names (second fuse block, 2141029, ANL 100, gbx_body, HCFB, MFINITY), then
read the hits in context. Skip `archive/` and generated files (`research-hub.html`,
`docs/harness/min/`). Historical dated logs (the plan doc) are not "stale", they are history.

## Done

### 1. docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md - FIXED (uncommitted)

Not superseded by any newer doc (AGENTS.md, README.md, RECONCILIATION-RULES.md and the harness
plan all still name it the living splice table). Conflicts found and fixed:

- Fuse-box wording (§1, §3 diagram, §3.1, §4, §5.3, §5.4, §8, §9, §10 table, header line 7) said
  TE 2141029-1 / second fuse block / ANL 100 A / HCFB; now points at the Option B box in
  `ST185-CabinPower`. ACPS fuse row updated to 10 A from heater relay 87 (per the PR #83 slot map).
- J/B2 side: §5.4 heading and §9 step 6 still routed the dummy header along the passenger
  fender / ABS trough; now driver side, route deferred to `ST185-EngineRoom-C.harness`. §4 step 5
  open item reworded.
- §10 marked "Historic below" (PMU-16 arithmetic predates the no-PDU decision, plan 6.48).
- Not touched: OPEN-ITEMS rows 15 and 20 point at this file's line numbers (unchanged). Row 20 says
  the `docs/electrical/**` review is HELD, so Daniel may still need to sign off the content.
- Gate: `check_all.py` passes except `sync_io_table.py` (the known CRLF false positive per PR #83;
  not re-verified).

### 2. docs/harness/redesign/DECISIONS.md - FOUND, NOT YET FIXED

"Binding decisions (2026-09-28 audit)" table, marked "final, do not re-ask". Change locations and
names only, never the decisions.

- B1: CAN-Lambda +12V from "cabin fuse F5 10 A" - F-numbers relabeled by Option B; current name
  not checked.
- B6: says the RFRM "has no place in the drawings yet" - it is now drawn in `ST185-CabinPower`.
- B7: points at EngineRoom-C `gbx_body` - removed.
- B8: "HCFB H4 Bussmann AMI-60" - now LMI L7 (ENGINE-ROOM doc and SENSOR-AND-ACTUATOR-REFERENCE
  already say "LMI L7 (was HCFB H4)").

Related, same pass: `docs/harness/interfaces.json:7` still says "fuse block and HCFB on
ST185-CabinPower". `docs/harness/README.md:56` names `gbx_body` but only to say it moved - fine.
Awaiting Daniel's go-ahead to edit.

### 3. sot/channels.csv (and XTREMEX-IO-TABLE.html) - CSV CLEAN, HTML STALE (not yet fixed)

- `sot/channels.csv:106` (k_eps c1) already says LMI L7, "was HCFB H4 before the Option B fuse
  box". Nothing to fix.
- `XTREMEX-IO-TABLE.html:343` is hand-written prose (not inside the generated SOT block, no
  script writes it): "the glove-box body block is a second fuse block plus micro ISO relays".
  Stale - should say the Option B box (LMI + RFRM + 3x MTA, `ST185-CabinPower`). It is a prose
  edit, but `sync_io_table.py --check` gates this file, so re-run it after editing. Daniel's
  call whether the HTML is edited.

### 4. docs/RECONCILIATION-RULES.md - STALE in Rule 3 (not yet fixed)

Rest of the file (Rule 1 surface table, Rule 2 CAN, bus facts, crossovers a-c, fuse box line 225)
is current.

- Lines 193-197: says the injector rail "(F11 15 A)" and COP rail "(F10 20 A)" cross through
  `IX_RAIL_A`, a Deutsch DTP 4-way flange pass-through. Both wrong now: the fuses are RFRM INJ 15 A /
  RFRM COP 20 A, and IX_RAIL_A is **retired** - the rails moved onto bulkhead A c48 / c49 on the
  shared DRB102 (`docs/harness/DRB102-CAVITY-MAP.md:91-92`, `interfaces.json` BR_W_INJ_PWR_C /
  BR_W_COP_PWR_C, A-cabin / A-engine harness signals "moved in from retired IX_RAIL_A").
- Line 232: "crossover (c) below" - crossover (c) is above that line.
- Same stale fact elsewhere (not yet read as their own documents):
  - `docs/harness/validate_bulkhead_letter.py:42` docstring (IX_RAIL_A, DTP 4-way)
  - `docs/harness/check_all.py:66` comment
  - `docs/harness/redesign/DECISIONS.md` Q-RAIL row (line 235): F11/F10 and IX_RAIL_A
  - `docs/OPEN-ITEMS.md` row 28: says IX_RAIL_A is "not drawn or registered" and cites
    RECONCILIATION-RULES:180 - the item is moot now that the pass-through is retired
  - `ST185-A-cabin.harness` lines ~1290 / 1304: broken-off terminal text still says
    "to IX_RAIL_A c1 / c2" (drawing text, not a doc; flagged only)

### 5. docs/OPEN-ITEMS.md - STALE rows (not yet fixed)

Rows 45-53 (Option B) and 1-10, 22-27, 30-31, 33-39, 40-44 checked: current or correctly closed.
Stale:

- Row 28: IX_RAIL_A "not drawn or registered" - the pass-through is **retired** (rails moved to
  bulkhead A c48/c49, see item 4). Close it, and its source `RECONCILIATION-RULES.md:180` is gone.
- Row 12: "Superseded - pending reconcile plan" - ACAmp-Spur was folded into A-cabin / EngineRoom-C
  on 2026-10-11 (#77). Its source `docs/harness/ACAMP-SPUR-LABELS.md:27,:41` points at a blank
  line / a file for a retired loom. Close or re-point.
- Row 13 cites `HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md:2063` (now a shielded-cable-parts line, not
  the four TBD connector parts); row 14 cites `:2365` (blank line). Line numbers drifted; the
  items themselves may still be open - needs a text search in the plan doc, not a line number.
- Row 19: "for the shield wording see row 15" - the shield row is **16**; 15 is engine-room power.
- Row 32: report lives in `C:\projects\inbox\st185-research\` - `inbox\` no longer exists (root
  layout has only `active\ _archive\ _scratch\ ...`). Report may be lost; say so or re-point.
- Row 29 (closed, history) names `C:\projects\shipping\...` - folder is now `active\`. Harmless.
- Rows 18-20 "Held WS4" (this very review) say wait for the reconcile plan and Engine A change.
  Reconcile passes 1-3 have landed, so these may now be unblocked; Row 17 (Engine A layout) is
  still marked waiting on Daniel. His call whether to keep holding.
- Row 11: "14 of 28 flying leads" count and the FL_ACAMP_* names were not recounted after the
  ACAmp-Spur fold; unverified.

### 6. docs/harness/ACAMP-SPUR-LABELS.md - MOSTLY CURRENT, a few stale lines (not yet fixed)

Not superseded: #77 (2026-10-11) added a retirement banner and re-pointed terminals to A-cabin /
EngineRoom-C. Pins, colours and sources stand. Remaining problems:

- Heading "Existing coolant-thermistor leads (not this pass, already on the spur)" - there is no
  spur any more.
- Internal contradiction: the table says `fl_acamp_mg` / `fl_a4_3` are the **variable-displacement
  control coil, not fitted** (Y-B, A18-5 / A4-3; OPEN-ITEMS row 37 agrees), but the paragraph after
  Assumptions says "insulation on clutch and pressure follows the factory lead... The compressor has
  the clutch only", i.e. calls the same lead the clutch. One of them is wrong.
- "EngineRoom-C still feeds A5 pin 1 +12V (V-R) only" - the pressure-switch +12V now comes from
  CabinPower (RFRM ACPS 10 A, `w_acp_1`).
- Knock-on in item 1: `ENGINE-ROOM-POWER-REDISTRIBUTION.md` §5.7 row C10 and §9 step 7 call
  `fl_a4_3` the "A/C compressor clutch" / "clutch" lead - same contradiction with this file and
  OPEN-ITEMS row 37. (I introduced no new text there, but I left it in.)
- `sot/README.md` also cites this file - not yet read.

### 7. sot/README.md - ONE STALE PHRASE (not yet fixed)

Checked against `sot/channels.csv`: owner list (ECU/VRC/ACAMP/PWR/MRS), columns, classes, "two rows
are tbd" (TAM_RTN, TW_RTN), and the `validate_sot.py` / `check_all.py` claims are all correct.

- "Two rows are `tbd` (the A/C amp's ambient-sensor return and **coolant-switch return**)": the
  second TBD row is `TW_RTN`, a heater-core water-temp **thermistor** return, not a coolant switch
  (corrected 2026-10-04, channels.csv row 104; OPEN-ITEMS row 37). The README missed that
  correction. Fix: "ambient-sensor return and heater-core thermistor (TW) return".

### 8. docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md - STALE, several places (not yet fixed)

2,416 lines, grew by accretion. Its own banner says "6.x wins, highest numbered subsection wins".
That rule is now broken because **Option B (2026-10-11) is not in the plan at all** - the last
section is 6.55 (2026-09-26); Option B lives only in PR #83, the harness README and
`_research/FUSEBOX-B-SLOT-MAP.md` (untracked). Findings:

- No section records Option B, so these older sections read as current with no banner:
  - 6.54 (`:2287`, fusing/feeds) and 6.55 (`:2370`, FB1 `2141029-1`, "Glove-box body block is
    `gbx_body`" at `:2390`) - gbx_body and the TE block are gone.
  - 6.48-ish text at `:1799`, `:1908`, `:1950`, `:2029`: "second fuse block", "TE 2141029-1 is full
    at F1-F13", "pick the 12-way second fuse block" - retired design.
  - `:2310` / `:2354` MFINITY module `2141029-1`.
- Top banner table `:14-18`: "Now (6.41): 6 looms: A, B, C, CAN, cabin accessory, rear trunk" -
  there are now 14 looms (`docs/harness/rebuild/`). The banner defers to `harness/README.md` but the
  number is wrong.
- Section 1 table `:43-45`: `docs/harness/ST185-EngineRoom-C.harness` row says "Retired drawing".
  That path is retired but EngineRoom-C is **live** at `docs/harness/rebuild/`. Same old path at
  `:145` and `:175`.
- `:160`, `:166`, `:170`: "HDP20 A and B, passenger side", "PMU-16 ... in the glove box" - HDP20 was
  superseded by DRB102 (`:1259`, 2026-10-10) and there is no PMU (6.48). The 6.41 table was never
  updated.
- OPEN-ITEMS citations: row 14 (HCR 150 parallel-resistor TBD) is now at `:2379`, not `:2365`. Row
  13 ("four connector parts are placeholder TBD, 2 AWG will not fit 25 mm2") - could not find that
  text near `:2063` or by grep; the item may have been resolved by 6.51 (`:2180`, 1/0 + RADLOK 8.0).
- Not stale: sections 1-5 history and the 6.43-6.48 PDU/PMU chapters carry SUPERSEDED banners.

Suggested fix: add a short "6.56 Fuse box Option B (2026-10-11)" section that says what replaced
what, and add one-line "superseded by 6.56" banners to 6.54/6.55 and the 2nd-fuse-block passages.

### 9. docs/harness/README.md - MOSTLY CURRENT, 4 stale spots (not yet fixed)

Current: "14 harnesses" (matches `rebuild/`, 14 files), CabinPower row, fuse-box paragraph (lines
55-60), DRB102 bulkhead bullet, the gate pipeline list (matches `check_all.py` HARD list, 19 gates),
parts rules.

- Line 38: EngineRoom-C scope says "engine room, PDB, **fuse blocks + relays**, EPS..." - the fuse
  box moved to CabinPower (the README's own lines 55-58 say so). Contradiction inside the file.
- Line 46: "the one open deviation (Q-RAIL)" - Q-RAIL was ruled (rails cross on the A side) and is no
  longer open; Rule 3 says crossover (d) is retired. See also item 4 (rails now on bulkhead A c48/c49).
- Lines 66-68: "The four [inline interfaces] today: IX_WS_FRONT, IX_WS_REAR, IX_AC_CTS, IX_FUEL_LVL".
  `interfaces.json` lists four, but they are IX_WS_REAR, IX_WS_FRONT, IX_FUEL_LVL and **IX_B_RAIL**
  (which the README itself uses at lines 35-36). `IX_AC_CTS` is not registered anywhere any more (only
  prose mentions in `sot/channels.csv:103` and an EngineRoom-C note), so remove it and add IX_B_RAIL.
  Also `IX_AC_CTS` in channels.csv rows 103/104 notes is a dead reference (SoT file).
- Lines 136-137: "Current examples [of TBD parts]: the RADLOK pass-through, the A/C coolant switch" -
  RADLOK parts were picked (`RL9080-301-F1RE` etc., 6.51). Only the A/C coolant-switch connector is
  still `TBD` in `rebuild/*.harness`.

### 10. docs/harness/redesign/ (INTERFACES.md, IMPLEMENTATION-PLAN.md, DECISIONS.md)

Method switched to the scripted pass (see "Scripted check" at the end): path/line-ref check plus a
retired-term grep, then read the hits in context.

- `INTERFACES.md`: 0 hits. CURRENT.
- `IMPLEMENTATION-PLAN.md`: a dated 2026-09-27 status snapshot; all phases marked Done, Phase 7
  already says "Superseded 2026-09-28". Cites deleted scripts/files (`verify_rebuild.py`,
  `fix_cable_parts.py`, `layout_633.py`, `ST185-WheelSpeed.harness`, `docs/harness/interfaces.yaml`
  which became `interfaces.json`). All inside completed-phase text. HISTORICAL - acceptable; optional
  one-line "all paths below are as of 2026-09-27" note.
- `DECISIONS.md` (in addition to item 2's B1/B6/B7/B8):
  - Lines 5-6 cite `output/HARNESS-REDESIGN-PLAN.md` and `output/HARNESS-CHECKER-AUDIT.md`; the header
    already says they were deleted 2026-10-10. Fine.
  - "Open questions" table (`:231-235`) still lists **Q-RAIL as open**, while the same file resolves it
    at `:252` / `:273` and again retires IX_RAIL_A at `:376`. Mark the row resolved/retired.
  - `:314` points at `C:\projects\inbox\st185-research\BULKHEAD-OPTIONS-2026-09-29.html` - `inbox\`
    no longer exists; `:315`/`:368` cite `DRB102-RATINGS.html` / `BULKHEAD-OPTIONS-...html` that are
    not tracked. Sources unreachable.
  - HDP24/HDP26/IX_RAIL_A text at `:256-330` is the dated decision log (history), superseded by the
    "Bulkhead A/B + DTP replaced by a shared DRB102" section at `:307`.

### 11. Remaining prose docs (scripted pass, hits read in context)

Order walked: from item 10 forward (docs/intercooler, procedures, sourcing, link_*, rd-build,
realdash-simulation, sot, switchboard, tune), then wrapped to the top (.claude, .cursor, .github,
root *.md, apps, bench, docs/5sgte, devices, enclosures, harness) and back to the start file.

STALE (not yet fixed):
- `docs/RECONCILIATION-RULES.md:108` (Rule 2 participants table) lists the cluster config as
  `main/canbus.c`, `main/protocols/link_g4x.json`. That JSON **does not exist** in the cluster repo
  (`CAN-CONFIG-STATUS.md:14` and `.cursor/rules/can-frame-contracts.mdc` both say so). Drop it.
  (Item 4 said Rule 2 was current; this corrects it.)
- `AGENTS.md:69`: "`docs/harness/rebuild/*.harness` (15 files ...)" - there are 14.
- `docs/SHIELD-RULES.md:92-93`: pedal rows say "planned, not yet drawn" but also say the pedal is
  now drawn in A-cabin; wording is contradictory, otherwise accurate (APS-Pedal / IX_APS fold-in is
  documented). Low priority.
- `docs/sourcing/README.md:14,48-54,78-79`: "Bulkhead A is HDP24-24-47, Bulkhead B HDP24-24-21 ...
  fully covered by what is already here"; bulkheads are now one shared DRB102 (2026-10-10). The
  HDP stock notes are still true as inventory, the bulkhead statements are not. Dated 2026-09-21.
- `.cursor/rules/*.mdc` vs `.claude/rules/*.md`: AGENTS.md says "same rules, two tools". Only
  `harness-wiring-conventions` is identical. `realdash-xml-conventions.mdc` lacks the approved
  0x3EB Gear-byte exception that the .claude copy has (a Cursor agent would not know it);
  `can-frame-contracts` and `python-tooling-patterns` are reworded copies (facts agree).
- `tune/docs/FEATURES_AC_IDLE_CRUISE_TC.md:47` cites `AGENT_SESSION_CONTEXT.md` (not imported; tune/README
  says session docs were left behind). `tune/docs/RESEARCH.md:101` cites
  `docs/references/linkecu-furyx-dealer.html` (not in repo; `docs/vendor/` is gitignored).
- `docs/harness/check_all.py:66` comment and `validate_bulkhead_letter.py:42` docstring still describe
  IX_RAIL_A (code comments; see item 4).
- `.cursor/install.sh:13` says base image has Python 3.12; CI and dansPC use 3.14 (OPEN-ITEMS row 33
  already tracks this).

CURRENT (scripted check clean, or only intentional history/cross-repo refs):
`.claude/rules/*` (other than the .cursor drift above), `.claude/skills/*`, `.github/workflows/*`,
`BENCH-TEST.md`, `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CAN-CONFIG-STATUS.md`,
`CANBUS-LINK-G4X-CONFIG.md`, `ECUMASTER_SWITCHBOARD_SETUP.md`, `FUEL-SYSTEM.md`, `README.md`,
`REALDASH-LAYOUT.md`, `WIRING.md`, `apps/*`, `docs/devices/*`, `docs/enclosures/README.md`,
`docs/harness/DRB102-CAVITY-MAP.md`, `docs/intercooler-turbo-study/*`, `docs/procedures/*`,
`docs/5sgte-project-data/*`, `rd-build/*` (CREDENTIALS.md and `_anim.xml` are intentionally absent /
gitignored), `tune/README.md` and the other `tune/docs/*`. `python bench/check_parity.py` passes, so
`link_g4x_can_setup.json/.lcs`, `link_g4x_realdash.xml`, `switchboard_frames.json`, `bench/frames.py`,
the ID table and the sender UI agree with each other and with the cluster firmware. False positives
(cross-repo `main/canbus.c`, `@./` includes, bare script names) were filtered out.

NOT swept (out of scope for a staleness-of-prose pass): tune CSV tables, intercooler research data,
`.harness` drawings (SoT-driven, gated by `check_all.py`), `docs/harness/min/` and other generated
files, source code beyond its docstrings.

## Scripted check (reusable)

`refcheck.py` (scratchpad copy; full text lives in the `iterative-cleaning` skill): for each prose
doc, extract backtick paths and markdown links and report (a) paths that no longer exist, (b)
`file:line` citations that land on a blank / out-of-range line, (c) hits for a list of retired
terms. Then read each hit in context and classify: stale / history (dated log) / cross-repo / false
positive.

## Shipping

Handoff committed on a branch and pushed (see chat for the path and branch). The edits to
`docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` are NOT in that commit; they remain in the
working tree. `main` is protected; ship via PR (`st185-ship-change`) when Daniel says so.
