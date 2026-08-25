---
name: run-can-bench-scenarios
description: Run and interpret CAN bench validation scenarios for this repo’s Link G4X/RealDash contract. Use when user says 'bench test CAN', 'verify frames', 'simulate ECU', 'run cluster scenario', or 'run realdash scenario'. Capabilities: preflight dependency checks, monitor mode (`--known-only`), `full-cluster`, `full-realdash`, sender-app simulation tie-in, and contract consistency checks across `bench/frames.py`, `link_g4x_can_setup.json`, and `link_g4x_realdash.xml`. Do NOT use for hardware wiring rewrites, ECU pinout changes, or physical bus troubleshooting beyond software-level command validation.
paths:
  - bench/**
  - apps/trackcluster-can-sender/**
  - link_g4x_can_setup.json
  - link_g4x_realdash.xml
  - CAN-BUS-*.md
  - CANBUS-*.md
  - REALDASH-LAYOUT.md
  - realdash-simulation.html
  - BENCH-TEST.md
---
# run-can-bench-scenarios

## Critical
- Treat `link_g4x_can_setup.json` as the canonical CAN contract before interpreting any bench output.
- Keep `0x3E8` to `0x3F1` behavior aligned across `bench/frames.py`, `link_g4x_can_setup.json`, and CAN docs; do not accept a "pass" if these drift.
- Do not rename `ST185:` input names in `link_g4x_realdash.xml` during validation work; RealDash bindings depend on exact names.
- Keep multibyte fields BigEndian unless a source file explicitly documents an exception.
- This skill validates software behavior only. Do not propose wiring rewrites, harness changes, or hardware rework.

## Instructions
1. **Run preflight dependency + syntax checks**
   - From project root, run:
     - `python -m pip install -r bench/requirements.txt`
     - `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
   - Confirm these files exist and are the ones used for bench validation:
     - `bench/can_bench.py`
     - `bench/frames.py`
     - `link_g4x_can_setup.json`
     - `link_g4x_realdash.xml`
   - **Verify** installs and compile checks complete with no Python errors before proceeding to the next step.
   - **Dependency:** This step has no dependency.

2. **Establish the exact runtime target (interface/channel/bitrate)**
   - Use the project’s standard invocation pattern from `CLAUDE.md`:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 <scenario>`
   - Keep `--interface pcan --channel PCAN_USBBUS1 --bitrate 1000000` unless the user explicitly supplies a different target.
   - **Verify** the chosen values are confirmed by the user/session context before proceeding to the next step.
   - **Dependency:** This step uses the environment prepared in Step 1.

3. **Run monitor baseline with known-frame filtering**
   - Execute:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`
   - Interpretation rule:
     - Pass baseline if output shows only known/expected frame IDs and no unknown-frame warnings.
     - Flag failure if unknown IDs appear or expected IDs in the `0x3E8` to `0x3F1` range are missing when traffic should be active.
   - **Verify** monitor output is captured and classified as pass/fail before proceeding to the next step.
   - **Dependency:** This step uses target settings from Step 2.

4. **Run full cluster scenario**
   - Execute:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-cluster`
   - Compare observed behavior against definitions in:
     - `bench/frames.py`
     - `CAN-BUS-ID-ALLOCATION-TABLE.md`
     - `CAN-BUS-MASTER-DESIGN.md`
   - Interpretation rule:
     - Pass if scenario runs to completion with no runtime exceptions and frame semantics match the documented cluster contract.
   - **Verify** completion status and semantic match are both true before proceeding to the next step.
   - **Dependency:** This step uses baseline confidence from Step 3.

5. **Run full RealDash scenario**
   - Execute:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash`
   - Validate RealDash contract consistency using:
     - `link_g4x_realdash.xml`
     - `REALDASH-LAYOUT.md`
     - `realdash-simulation.html`
   - Interpretation rule:
     - Pass if emitted channels map cleanly to expected `ST185:` inputs and scenario completes without decode/runtime failures.
   - **Verify** ST185 channel compatibility and successful completion before proceeding to the next step.
   - **Dependency:** This step uses interface + semantic assumptions confirmed in Steps 2 and 4.

6. **(When user asks to simulate ECU traffic) run sender app and re-check monitor**
   - Start sender app:
     - `python apps/trackcluster-can-sender/app.py`
   - Optional explicit device modes:
     - `set TC_DEVICE=cluster && python apps/trackcluster-can-sender/app.py`
     - `set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py`
   - While sender is active, re-run monitor command from Step 3 to confirm expected IDs/fields.
   - **Verify** injected traffic appears as expected and remains within known-frame contract before proceeding to the next step.
   - **Dependency:** This step uses scenario expectations from Steps 3-5.

7. **Report pass/fail with contract-focused evidence**
   - Produce a concise result block with:
     - Commands run
     - Scenario outcomes (`monitor`, `full-cluster`, `full-realdash`)
     - Any ID/field mismatches tied to exact files (`bench/frames.py`, `link_g4x_can_setup.json`, `link_g4x_realdash.xml`)
   - If mismatches exist, prescribe the smallest synchronized fix and list all files requiring aligned edits.
   - **Verify** every failure includes a reproducible command and a concrete file-level cause before ending.
   - **Dependency:** This step uses outputs from Steps 3-6.

## Examples
### Example 1: Bench validation request
- **User says:** "Bench test CAN and verify frames for cluster and RealDash."
- **Actions taken:**
  1. Run preflight install + compile checks.
  2. Run `monitor --known-only` with `pcan / PCAN_USBBUS1 / 1000000`.
  3. Run `full-cluster`.
  4. Run `full-realdash`.
  5. Cross-check any mismatch against `bench/frames.py` and `link_g4x_can_setup.json`.
- **Result:**
  - Returns a pass/fail table per scenario.
  - If failure appears (for example unknown ID in monitor), report exact failing command and specify which contract file must be updated to restore `0x3E8`-`0x3F1` alignment.

## Common Issues
1. **Error:** `ModuleNotFoundError: No module named 'can'`
   - **Fix:**
     1. Run `python -m pip install -r bench/requirements.txt`
     2. Re-run `python -m py_compile bench/frames.py bench/can_bench.py`
     3. Retry the bench command.

2. **Error:** `error: argument scenario: invalid choice: 'full_cluster'`
   - **Cause:** Wrong scenario name format.
   - **Fix:** Use exact CLI names from this project:
     - `monitor`
     - `full-cluster`
     - `full-realdash`

3. **Error:** `python: can't open file 'bench/can_bench.py': [Errno 2] No such file or directory`
   - **Fix:**
     1. Change to repository root (directory containing `bench/`).
     2. Verify file exists at `bench/can_bench.py`.
     3. Re-run command from project root.

4. **Error:** PCAN initialization/open failure (for example `PCAN_ERROR_*` or channel open failure)
   - **Fix:**
     1. Verify interface/channel values exactly match project defaults: `--interface pcan --channel PCAN_USBBUS1 --bitrate 1000000`.
     2. Ensure no other process is locking the same channel.
     3. Re-run monitor first (`monitor --known-only`) before full scenarios.

5. **Error:** Monitor shows unknown-frame messages while `--known-only` is enabled
   - **Fix:**
     1. Capture the unknown CAN ID(s) from output.
     2. Compare against `bench/frames.py` and `link_g4x_can_setup.json`.
     3. If new IDs are intentional, update both files (and related docs) in the same change so contract stays synchronized.

6. **Error:** RealDash scenario runs but channels do not bind as expected
   - **Fix:**
     1. Verify `ST185:` input names in `link_g4x_realdash.xml` were not changed.
     2. Cross-check mapping with `REALDASH-LAYOUT.md` and `realdash-simulation.html`.
     3. Re-run `full-realdash` after restoring exact input names.