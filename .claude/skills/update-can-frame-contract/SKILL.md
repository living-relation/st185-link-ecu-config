---
name: update-can-frame-contract
description: Updates CAN frame definitions across `bench/frames.py` and `link_g4x_can_setup.json` so IDs, byte layout, scaling, and offsets stay synchronized. Use when requests mention "add CAN signal", "change byte layout", "new frame", "update frame 0x3E8-0x3F1", or "change warning bits". Handles BigEndian packing, cross-file parity checks, and required docs updates in CAN contract docs. Do NOT use for RealDash gauge styling/layout-only changes that do not change CAN payload contracts.
paths:
  - bench/frames.py
  - link_g4x_can_setup.json
  - CAN-BUS-ID-ALLOCATION-TABLE.md
  - CANBUS-LINK-G4X-CONFIG.md
  - bench/*.py
  - apps/trackcluster-can-sender/app.py
---
# update-can-frame-contract

## Critical
- Treat `link_g4x_can_setup.json` as the canonical CAN contract for IDs, scaling, offsets, and signal ranges. Do not change `bench/frames.py` first.
- Keep `0x3E8`-`0x3F1` semantics aligned across `bench/frames.py`, `link_g4x_can_setup.json`, and docs.
- Keep all multibyte CAN fields BigEndian unless an existing source file explicitly documents otherwise.
- For frame `0x3F1` byte 6 warnings, keep bit mapping consistent with `bench/frames.py` constants and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Do not rename existing `ST185:` input names in `link_g4x_realdash.xml` when doing CAN contract work; dashboard bindings depend on exact names.

## Instructions
1. **Collect the target contract change and lock frame scope**
   - Open `link_g4x_can_setup.json` and identify the exact frame ID (`0x3E8`-`0x3F1`), byte index, bit position/length, scale, offset, min, max, and unit to change.
   - If adding a new frame, reserve/confirm ID placement with `CAN-BUS-ID-ALLOCATION-TABLE.md` before editing code.
   - Write a one-line change note in your working notes: `FRAME_ID / SIGNAL / BYTE_LAYOUT / SCALE_OFFSET`.
   - **Dependency:** This is the base input for all following steps.
   - **Validation gate:** Verify the requested signal does not conflict with an existing signal at the same frame byte/bit before proceeding to Step 2.

2. **Update canonical contract in `link_g4x_can_setup.json` first**
   - Edit only the relevant message/signal block in `link_g4x_can_setup.json`.
   - Preserve existing key naming and numeric style already used in the file (do not refactor unrelated blocks).
   - For multibyte signals, keep BigEndian ordering unless the file already documents an exception for that specific signal.
   - If changing scale/offset, update both values together as one atomic contract change.
   - **Dependency:** Uses the frame/signal plan from Step 1.
   - **Validation gate:** Verify JSON is valid before proceeding: run `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py` and confirm no JSON-related parse/runtime failure appears in downstream tooling.

3. **Mirror payload packing/unpacking behavior in `bench/frames.py`**
   - Update constants, frame builders, and/or decode helpers in `bench/frames.py` so encoded bytes match the updated contract.
   - Keep existing packing style and helper usage already present in `bench/frames.py`; do not introduce a different endian/bitfield approach for one signal.
   - If the change touches frame `0x3F1` byte 6 warnings, update the warning bit constants and any composed warning byte logic together.
   - **Dependency:** Uses canonical field layout from Step 2.
   - **Validation gate:** Verify every changed signal has matching byte/bit placement in both `link_g4x_can_setup.json` and `bench/frames.py` before proceeding to Step 4.

4. **Run bench-level contract validation commands**
   - Use the project bench commands from `CLAUDE.md`:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-cluster`
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash`
   - If hardware is unavailable, still run compile-level validation:
     - `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
   - **Dependency:** Uses synchronized code from Steps 2 and 3.
   - **Validation gate:** Verify at least compile validation passes (required) and bench scenarios pass when hardware is available before proceeding to Step 5.

5. **Update contract documentation parity**
   - Update the exact frame/signal sections in:
     - `CAN-BUS-ID-ALLOCATION-TABLE.md`
     - `CANBUS-LINK-G4X-CONFIG.md`
   - Keep terminology and frame tables consistent with `README.md` and existing docs style.
   - If a new frame was added, document ID purpose, byte map, and scale/offset mapping in both docs.
   - **Dependency:** Uses validated frame behavior from Step 4.
   - **Validation gate:** Verify docs values (ID, byte index, bit length, scale, offset) exactly match `link_g4x_can_setup.json` before proceeding to Step 6.

6. **Run final parity and regression checks**
   - Re-run:
     - `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
     - `python rd-build/tools/automation_helper.py size`
   - If sender behavior is affected, run one app smoke start:
     - `python apps/trackcluster-can-sender/app.py`
   - Confirm no unintended changes to `link_g4x_realdash.xml` `ST185:` names.
   - **Dependency:** Uses finalized code/docs from Step 5.
   - **Validation gate:** Verify changed files are limited to CAN contract scope (`bench/frames.py`, `link_g4x_can_setup.json`, and related CAN docs) before completing.

## Examples
### Example 1: Add a CAN signal to an existing frame
**User says:** "Add oil temp signal to frame 0x3EA using bytes 4-5 with scale 0.1 and offset -40."

**Actions taken:**
1. Locate frame `0x3EA` and free bytes in `link_g4x_can_setup.json`.
2. Add signal definition in `link_g4x_can_setup.json` with BigEndian byte order, scale `0.1`, offset `-40`.
3. Update `bench/frames.py` encode/decode logic and constants for the same bytes.
4. Run `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`.
5. Update `CAN-BUS-ID-ALLOCATION-TABLE.md` and `CANBUS-LINK-G4X-CONFIG.md` with the new signal map.

**Result:**
- Frame payload layout is synchronized across contract JSON, bench tooling, and docs.
- Compile validation passes; bench scenarios are ready for hardware verification.

### Example 2: Change warning bit in 0x3F1 byte 6
**User says:** "Move low fuel warning to bit 2 in 0x3F1 byte 6."

**Actions taken:**
1. Update warning bit definition for `0x3F1` byte 6 in `link_g4x_can_setup.json`.
2. Update corresponding warning bit constant/packing logic in `bench/frames.py`.
3. Update warning mapping row in `CAN-BUS-ID-ALLOCATION-TABLE.md`.
4. Run compile validation and bench monitor command.

**Result:**
- Warning bit mapping remains consistent across code and documentation, avoiding cluster misinterpretation.

## Common Issues
- **Error:** `json.decoder.JSONDecodeError: Expecting ',' delimiter ... link_g4x_can_setup.json`
  1. Verify trailing commas or missing braces in `link_g4x_can_setup.json`.
  2. Re-open the edited message block and compare bracket depth with neighboring blocks.
  3. Re-run: `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`.

- **Error:** Bench output shows unknown or mismatched frame interpretation during `monitor --known-only`
  1. Verify frame ID and byte offsets are identical between `link_g4x_can_setup.json` and `bench/frames.py`.
  2. Check BigEndian ordering for multibyte fields (do not swap byte order unless explicitly documented).
  3. Re-run: `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`.

- **Error:** Warning indicators wrong after `0x3F1` change (wrong lamp/state)
  1. Verify `0x3F1` byte 6 bit mapping in `bench/frames.py` constants.
  2. Verify same bit positions in `CAN-BUS-ID-ALLOCATION-TABLE.md` and `link_g4x_can_setup.json`.
  3. Re-test with `full-cluster` bench mode.

- **Error:** `pcan` interface/open failure (for example, cannot open `PCAN_USBBUS1`)
  1. Confirm device/channel is connected and available.
  2. Retry with the exact command from `CLAUDE.md` including `--channel PCAN_USBBUS1 --bitrate 1000000`.
  3. If hardware is unavailable, complete compile validation first and mark bench hardware validation as pending.

- **Issue:** RealDash stops updating a channel after CAN changes
  1. Verify CAN payload contract still maps to existing `ST185:` input names in `link_g4x_realdash.xml`.
  2. Do not rename existing `ST185:` keys during CAN frame updates.
  3. Validate with `full-realdash` bench scenario.

- **Issue:** Contract changed but docs drifted
  1. Diff `link_g4x_can_setup.json` against `CAN-BUS-ID-ALLOCATION-TABLE.md` and `CANBUS-LINK-G4X-CONFIG.md` for frame ID, byte index, scale, and offset mismatches.
  2. Update docs immediately in the same change set.
  3. Re-run final compile checks to ensure no accidental code edits.