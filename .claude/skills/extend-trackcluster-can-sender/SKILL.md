---
name: extend-trackcluster-can-sender
description: Adds or adjusts `apps/trackcluster-can-sender` behavior safely. Use when user asks to update sender app logic, add adapter support, or tweak sender UI profiles (e.g., 'update sender app', 'new adapter support', 'UI profile tweak'). Provides adapter scan flow updates, CAN transmit guardrails, and profile integrity validation with project contract checks. Do NOT use for non-app documentation-only changes or for bench/realdash contract redesigns.
paths:
  - apps/trackcluster-can-sender/**
  - bench/frames.py
  - link_g4x_can_setup.json
  - CAN-BUS-ID-ALLOCATION-TABLE.md
---
# extend-trackcluster-can-sender

## Critical
- Treat `link_g4x_can_setup.json` as the CAN contract source of truth before changing sender behavior.
- Do not ship sender changes unless `apps/trackcluster-can-sender/app.py` still compiles and bench contract IDs `0x3E8`-`0x3F1` remain aligned with `bench/frames.py` and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Keep multibyte CAN fields BigEndian unless an existing project file explicitly documents an exception.
- If UI profile labels/inputs map to RealDash signals, keep `ST185:` naming stable to avoid downstream breakage.

## Instructions
1. **Collect baseline and scope the change**
   - Open and review these files first:
     - `apps/trackcluster-can-sender/app.py`
     - `apps/trackcluster-can-sender/ui/index.html`
     - `apps/trackcluster-can-sender/requirements.txt`
     - `link_g4x_can_setup.json`
     - `bench/frames.py`
   - Confirm whether the request is backend-only (adapter/tx), UI-only (profile controls), or both.
   - Record which CAN IDs/signals are affected, especially in `0x3E8`-`0x3F1` range.
   - **Validation gate:** Verify the requested behavior maps to existing sender app responsibilities before proceeding to the next step.
   - **Dependency:** This is the source step; later steps depend on this scoped change list.

2. **Extend adapter scan logic in `app.py` using existing app patterns**
   - Edit only `apps/trackcluster-can-sender/app.py` for runtime scan/detection behavior.
   - Keep existing import style and module layout in that file; add imports only if required by current code structure.
   - Add/adjust adapter probing in the same control path currently used for interface/device selection (do not create a parallel startup path).
   - Preserve current env-driven device selection behavior (`TC_DEVICE`) and ensure new adapter scan paths still honor it.
   - If a new Python dependency is required for adapter detection, append it in `apps/trackcluster-can-sender/requirements.txt`.
   - **Validation gate:** Verify adapter scan still returns at least one usable path for existing device modes before proceeding to the next step.
   - **Dependency:** This step uses output from Step 1.

3. **Add or tighten transmit guards in `app.py`**
   - Implement guards in the same transmit call chain currently used by sender frame publishing.
   - Enforce these checks before writing any CAN frame:
     - Interface/adapter is initialized and healthy.
     - Device/profile mode is resolved (`cluster` or `realdash` path as currently implemented).
     - Outgoing frame IDs and payload lengths match existing sender expectations.
   - Keep guard failures explicit and user-visible (same error/reporting style already used in `app.py`).
   - Do not silently coerce invalid frame IDs or malformed payloads.
   - **Validation gate:** Verify invalid transmission inputs fail fast without sending frames before proceeding to the next step.
   - **Dependency:** This step uses output from Step 2.

4. **Apply UI profile tweaks in `ui/index.html` without breaking binding contracts**
   - Edit `apps/trackcluster-can-sender/ui/index.html` only for sender UI/profile updates.
   - Reuse existing element naming conventions, classes, and event wiring patterns from this file.
   - If adding profile controls, keep values compatible with backend profile keys used in `app.py`.
   - Do not rename existing bound fields unless backend mapping is updated in the same change.
   - **Validation gate:** Verify each new/changed UI control has a matching backend key/handler path before proceeding to the next step.
   - **Dependency:** This step uses output from Step 1 and Step 3.

5. **Run profile integrity checks across app/backend/contracts**
   - Confirm profile options exposed in `ui/index.html` resolve to valid runtime behavior in `app.py`.
   - Confirm all outgoing signal transforms still align with canonical config in `link_g4x_can_setup.json`.
   - If warnings/flags in `0x3F1` byte 6 are touched, keep bit mapping consistent with `bench/frames.py` and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
   - Keep edits focused; do not rewrite unrelated docs.
   - **Validation gate:** Verify no profile path can select an unsupported adapter/device/frame mapping before proceeding to the next step.
   - **Dependency:** This step uses output from Step 3 and Step 4.

6. **Execute project sanity commands for this app change**
   - Run:
     - `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
   - If dependencies changed, run:
     - `python -m pip install -r apps/trackcluster-can-sender/requirements.txt`
   - Run sender app in default and explicit device modes:
     - `python apps/trackcluster-can-sender/app.py`
     - `set TC_DEVICE=cluster && python apps/trackcluster-can-sender/app.py`
     - `set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py`
   - **Validation gate:** Verify all three app runs start without import/runtime startup errors before proceeding to the next step.
   - **Dependency:** This step uses output from Step 5.

7. **(When CAN hardware is available) perform behavior validation**
   - Validate emitted frames with bench tooling:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-cluster`
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash`
   - Confirm no unexpected IDs, and verify known frame semantics remain stable for `0x3E8`-`0x3F1`.
   - **Validation gate:** Verify monitor output contains only expected IDs/scaling before marking the task complete.
   - **Dependency:** This step uses output from Step 6.

## Examples
### Example 1: Add adapter support with safe fallback
- **User says:** "Update sender app to support a new adapter and keep current cluster mode working."
- **Actions taken:**
  1. Review `apps/trackcluster-can-sender/app.py`, `apps/trackcluster-can-sender/requirements.txt`, `bench/frames.py`, and `link_g4x_can_setup.json`.
  2. Extend adapter detection in the existing startup/interface selection path in `app.py`.
  3. Add transmit pre-checks (adapter initialized, valid mode, valid frame shape) in the existing send pipeline.
  4. Run `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`.
  5. Run sender app in default/`cluster`/`realdash` modes.
- **Result:** New adapter path is selectable, existing modes still boot, and invalid tx attempts are blocked before send.

### Example 2: UI profile tweak without contract drift
- **User says:** "Tweak sender UI profile options for RealDash, no protocol changes."
- **Actions taken:**
  1. Update `apps/trackcluster-can-sender/ui/index.html` using existing control naming/event patterns.
  2. Ensure profile keys still map to current backend handling in `apps/trackcluster-can-sender/app.py`.
  3. Verify no changes to CAN contract files except where explicitly required.
  4. Run compile/startup checks from Step 6.
- **Result:** UI behavior changes are live, backend mapping remains intact, and CAN frame contract remains stable.

## Common Issues
- `ModuleNotFoundError: No module named 'can'`
  1. Install sender dependencies: `python -m pip install -r apps/trackcluster-can-sender/requirements.txt`
  2. Re-run: `python apps/trackcluster-can-sender/app.py`

- `SyntaxError` or `IndentationError` in `apps/trackcluster-can-sender/app.py`
  1. Run: `python -m py_compile apps/trackcluster-can-sender/app.py`
  2. Fix the exact failing line reported by `py_compile`
  3. Re-run full compile gate: `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`

- App starts but adapter list is empty / no usable CAN interface
  1. Verify new adapter scan code is in the same startup path used by existing interface selection in `app.py`
  2. Confirm required adapter dependency is present in `apps/trackcluster-can-sender/requirements.txt`
  3. Reinstall deps and restart app

- Sender runs but no frames are accepted by downstream tools
  1. Run monitor check: `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`
  2. Verify sent IDs remain in expected contract and payload sizing matches existing frame definitions
  3. Cross-check `link_g4x_can_setup.json` vs `bench/frames.py` for changed IDs/scaling/offsets

- Wrong behavior only in one mode after a profile tweak (`cluster` or `realdash`)
  1. Test both explicit modes:
     - `set TC_DEVICE=cluster && python apps/trackcluster-can-sender/app.py`
     - `set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py`
  2. Verify UI profile key names in `ui/index.html` exactly match backend profile handling in `app.py`
  3. Restore compatibility for any renamed profile field

- Warning/status bits regress after sender changes (especially `0x3F1` byte 6)
  1. Verify bit mapping against `bench/frames.py`
  2. Verify the same mapping in `CAN-BUS-ID-ALLOCATION-TABLE.md`
  3. Re-run `full-cluster` and `full-realdash` bench validations to confirm parity