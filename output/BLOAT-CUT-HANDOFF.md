# Bloat-cut plan and handoff (R224 steps 4-6 + memory cleanup)

**Status (2026-10-20, updated as steps land):** plan approved by Dan. Step 0 merged (#376). Step 1: B1-B30 + retire map
approved by Dan and merged (#377); the old rule rows deleted and every pointer moved to "Binding rules B1-B30" (#PR1);
the trim of each rule to 2 lines or less is draft PR #PR2. Step 2 (read-back check, row 154): merged (#378).
Step 3 (`rebuild/` deleted, row 153): merged (#379). Step 4 (dead scripts, row 152): merged (#380; Dan had 11 RealDash helpers and the fuse-box CAD inputs restored in #383). Step 5: done (memory
pruned; the PC skill copies recycled after a diff against the claude.ai copies; AGENTS.md "Skills" points to the account).
Left: Dan's review of draft PR #PR2 (row 151).
Delete this file once every step, Dan's step-1 approval included, is done (open work goes into `docs/OPEN-ITEMS.md`).

## Context
Dan (R224, 2026-10-20): "Too many scripts and rules." The project has 216 R-rules, 116 `.py`
files, 112 `.md` files, a frozen `docs/harness/rebuild/` that four scripts still read, and 7
stale working-memory notes. Agents load all of it and drift. The goal is a small repo an agent
can read fast, with a one-page rule set, one read-back check, and no dead files.

## Decisions made this session (Dan, 2026-10-20)
- Approved: rules to one page (1A) with a cap (1B), read-back check + delete `rebuild/`, delete
  dead scripts, prune memory + keep skills in one place.
- Rule cap = **30**. Adding a rule means removing or merging one.
- Memory: **delete** the 7 STALE notes and the dead INDEX line.
- Order: **rules first**, then read-back, then `rebuild/`, then scripts.
- Skills home = **claude.ai account**. Delete the PC copies (`C:\Users\danie\.claude\skills\st185-*`).
- A/C (R13 vs R23, N61): **left off the rules page** (Dan: "ignore this").
- Rules approval: **one draft PR, Dan reviews** before anything is deleted.
- Shipping: each step commits, pushes, merges once green, then syncs the PC checkout.

## Steps (one PR each, branch `dan_/funny-maxwell-0hcb43`, then fresh from main)

### 0. Handoff into the repo (this plan)
- Copy this plan to `output/BLOAT-CUT-HANDOFF.md` (an in-flight handoff, allowed by AGENTS.md).
- Fix the stale range at `AGENTS.md:22` ("R1-R197" -> "R1-R226"): a clerical edit.
- PR `Rows: 151, 152, 153, 154`, merge when green, sync.

### 1. Rules on one page (row 151, R226), draft PR, Dan approves
- Read the old rule section of `docs/harness/redesign/DECISIONS.md` (216 R-lines) and the S-rows (done; now deleted, git history keeps them).
- Draft at most 30 short plain rules, grouped: scope/freeze, power+grounds, relays, CAN,
  ECU pins, wire+parts, drawings, shipping. Newest ruling wins. No A/C line.
- Write them as the new "Binding rules" section at the top of `DECISIONS.md`, plus a retire list
  (every old R-number -> the new rule number it merged into, or "dropped").
- The PR does not delete the old rules. It **waits for Dan's review** (not auto-merged).
- After Dan approves (done 2026-10-20, #PR1): delete the old R-lines and S-rows, and repoint
  `AGENTS.md` (its cut to about 80 lines is still open), `.claude/rules/*`, `.cursor/rules/*`,
  `docs/RECONCILIATION-RULES.md`, `docs/SHIELD-RULES.md`, `docs/dispatch/DISPATCH-RULES.md`.
  Then merge and sync.

### 2. Read-back check (row 154, R224 step 4)
- Extend `docs/harness/tools/build_drawings.py --check` (no new script, freeze-safe):
  extract the pinout/schematic PDF text and compare every wire with
  `docs/harness/MASTER-wirelist.csv` (both ends, connector, pin, gauge, colour, ident bands).
  Any difference fails.
- It is already wired into `tools/check_all.py`, so no new gate entry is needed.
- Verify: corrupt one master row in a scratch copy and confirm the check fails.

### 3. Delete `docs/harness/rebuild/` (row 153)
- Move the part data that readers still need (descriptions, AWG ranges) into one parts table
  next to the master. Repoint `docs/sourcing/build_project_bom.py`,
  `docs/harness/tools/check_wiring.py`, `cad/fusebox/src/wiring_sim.py`,
  `cad/drawings/fb_labels.py` and the `.cursor/rules/can-frame-contracts.mdc` glob.
- `git rm -r docs/harness/rebuild/`. The BOM output must be byte-identical before and after.
- Note: Dan's review of the `ST185-harness` sheets is still open on row 153 and does not block this.

### 4. Delete dead scripts (row 152)
- List every tracked `.py` file, and grep for callers (other scripts, `tools/check_all.py`,
  `.github/workflows/`, docs commands).
- No caller and not a live hand-run job = delete. Keep frozen CAD scripts that are still in use.
- PR body has a "Retired" list (R46).

### 5. Memory and skills (outside the repo, on DansPC via Desktop Commander)
- Delete the 7 STALE notes in `C:\Users\danie\.claude\working-memory\st185-link-ecu-config\`
  (harness-rules-2026-10, feedback_harness_parts_and_layout, reference_harness_app_view_facts,
  rules-home-decisions, project_glovebox_busbar_cad, project_custom_fusebox_plan,
  project_wire_routing_r86).
- Delete these 9 lines in `INDEX.md` (Dan's line numbers, 2026-10-20), **bottom up** so the numbers
  stay right: 28, 27, 26, 21, 20, 17, 16, 14, 13.
  - Stale notes: 28, 21, 20, 17, 16, 14, 13.
  - Dead links: 27 (`feedback_fusebox_approval_real_parts`), 26 (`feedback_harness_png_snapshots`).
  - Before deleting, re-read INDEX.md and confirm each line still holds the expected entry.
- Add one dated note line to INDEX.
- Skills: confirm that the claude.ai copies match, then delete `C:\Users\danie\.claude\skills\st185-*`
  and update the AGENTS.md "Skills" section to point to the claude.ai account.

## Shipping each step
1. `python tools/check_all.py` green, plus `python bench/check_parity.py`.
2. Commit, then `git push -u origin <branch>`.
3. Open a PR (body: `Rows: ...`, "Retired" list). Merge via GitHub (squash) once "Repo checks"
   and "Protect research hub" are green. Step 1's first PR waits for Dan.
4. Sync: on DansPC run `git -C C:\projects\active\st185-link-ecu-config pull --ff-only`
   (Desktop Commander), then `git fetch origin main && git checkout -B <branch> origin/main`
   here for the next step.

## Verification
- `python tools/check_all.py` passes after every step.
- Step 2: a deliberate one-cell mismatch makes the check fail.
- Step 3: `build_project_bom.py` output unchanged; `check_wiring.py` passes with no `rebuild/`.
- Step 4: `check_all.py`, CI workflows and every doc command still run.
- Rule count on the new page is 30 or fewer.

## Open items / blockers
- Desktop Commander must be online for step 5 and for the PC sync (it timed out once this session).
- Dan's rules review gates the deletion half of step 1.
- N61 (A/C) remains open in OPEN-ITEMS, untouched by this plan.
- Row 155 (car spot-check) is Dan's and follows step 3.
