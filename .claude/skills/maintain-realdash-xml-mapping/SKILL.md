---
name: maintain-realdash-xml-mapping
description: Maintains `link_g4x_realdash.xml` ST185 input mappings, conversions, enum/bit decoding, and CAN frame alignment with bench contracts. Use when requests include 'add RealDash input', 'fix ST185 channel', 'update warning bit', 'adjust scaling', or 'map a new CAN signal'. Key capabilities: frame-scope checks against `bench/frames.py` and `link_g4x_can_setup.json`, conversion consistency validation, and bench command verification. Do NOT use for `.rd` visual layout edits, screen design changes, or non-RealDash UI styling.
paths:
  - link_g4x_realdash.xml
  - bench/frames.py
  - link_g4x_can_setup.json
  - CAN-BUS-ID-ALLOCATION-TABLE.md
  - CANBUS-LINK-G4X-CONFIG.md
  - apps/trackcluster-can-sender/app.py
  - bench/can_bench.py
---
# maintain-realdash-xml-mapping

## Critical
- Treat `link_g4x_can_setup.json` as the canonical contract for CAN IDs, scaling, and offsets before touching `link_g4x_realdash.xml`.
- Keep `ST185:` input names in `link_g4x_realdash.xml` exactly stable unless the user explicitly asks for a rename; dashboard bindings depend on exact names.
- Keep `0x3E8` through `0x3F1` semantics synchronized across:
  - `bench/frames.py`
  - `link_g4x_can_setup.json`
  - `link_g4x_realdash.xml`
  - `CAN-BUS-ID-ALLOCATION-TABLE.md`
- For warning mappings in `0x3F1` byte 6, keep bit positions aligned with `bench/frames.py` constants and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Keep multibyte fields BigEndian unless a source file explicitly documents an exception.
- Do not edit `st185_dash.rd` for this workflow. This skill only covers XML channel mapping and conversion behavior.

## Instructions
1. Confirm scope and target signal before editing files.
   - Read these files first in this order:
     1. `link_g4x_realdash.xml`
     2. `link_g4x_can_setup.json`
     3. `bench/frames.py`
     4. `CAN-BUS-ID-ALLOCATION-TABLE.md`
   - Identify the exact frame ID, byte/bit location, scaling, offset, and whether the signal is numeric, enum, or warning-bit.
   - This step uses no prior step output.
   - Verify the requested signal is in the `0x3E8`-`0x3F1` contract (or explicitly approved outside it) before proceeding to the next step.

2. Lock the source-of-truth math and naming from existing contract files.
   - Pull conversion details from `link_g4x_can_setup.json` and the matching encoder/decoder logic in `bench/frames.py`.
   - Confirm the canonical signal label in docs and existing ST185 naming style in `link_g4x_realdash.xml`.
   - If the user requested a new signal that does not exist in JSON/frames contracts, update those contracts first, then return to XML.
   - This step uses output from Step 1.
   - Verify scale, offset, units, and bit-width match between JSON and `bench/frames.py` before proceeding to the next step.

3. Apply the XML mapping by cloning an adjacent existing ST185 input pattern.
   - In `link_g4x_realdash.xml`, locate an existing `ST185:` input in the same frame family and duplicate its structure and attribute ordering.
   - Keep the `ST185:` prefix and naming pattern consistent with existing entries. Only change the signal-specific suffix and conversion values required by Step 2.
   - Preserve existing XML style conventions in-file (attribute order, indentation, and spacing) so diffs stay minimal.
   - This step uses output from Step 2.
   - Verify the new or updated node keeps the same structural pattern as neighboring `ST185:` nodes before proceeding to the next step.

4. Apply enum or warning-bit mapping rules when relevant.
   - For enum-like values, mirror the enum mapping style already present in `link_g4x_realdash.xml` for similar channels.
   - For warning bits, map to the exact bit index documented for `0x3F1` byte 6 in `bench/frames.py` and `CAN-BUS-ID-ALLOCATION-TABLE.md`.
   - Do not reinterpret inverted logic unless that inversion already exists for the same warning family.
   - This step uses output from Step 3.
   - Verify each enum value or bit position resolves to the same meaning in XML, Python frame constants, and allocation docs before proceeding to the next step.

5. Run syntax and bench validation commands.
   - Run:
     - `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
     - `python -c "import xml.etree.ElementTree as ET; ET.parse('link_g4x_realdash.xml')"`
   - Run at least one RealDash-facing bench check:
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`
     - `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash`
   - This step uses output from Step 4.
   - Verify Python compile succeeds, XML parses cleanly, and monitor output shows no unexpected unknown frames before proceeding to the next step.

6. Perform contract sync pass across docs and mapping artifacts.
   - If signal semantics changed, update only the minimal needed sections in:
     - `CAN-BUS-ID-ALLOCATION-TABLE.md`
     - `CANBUS-LINK-G4X-CONFIG.md`
   - Confirm no drift between docs and implementation contracts (`bench/frames.py`, JSON, XML).
   - Keep edits focused; do not rewrite large documents for small mapping changes.
   - This step uses output from Step 5.
   - Verify the same frame ID, byte/bit location, and conversion math appears consistently in all touched files before proceeding to the next step.

7. Final regression check for sender app compatibility.
   - Run:
     - `python apps/trackcluster-can-sender/app.py`
     - `set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py`
   - Confirm no startup exceptions and that channel generation paths still run.
   - This step uses output from Step 6.
   - Verify app startup is clean and RealDash channel behavior matches expected mapping before marking complete.

## Examples
### Example 1: Add a new RealDash input mapped to existing CAN contract
- User says: "Add RealDash input for oil pressure and keep ST185 naming style."
- Actions taken:
  1. Read `link_g4x_can_setup.json` and `bench/frames.py` to locate oil pressure frame ID, byte offsets, scaling, and units.
  2. In `link_g4x_realdash.xml`, duplicate a nearby pressure-style `ST185:` input and adjust only the name suffix and conversion values to match the contract.
  3. Validate XML parse with `python -c "import xml.etree.ElementTree as ET; ET.parse('link_g4x_realdash.xml')"`.
  4. Run `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 full-realdash`.
  5. If needed, minimally update `CAN-BUS-ID-ALLOCATION-TABLE.md` to keep docs aligned.
- Result:
  - New `ST185:` input appears in `link_g4x_realdash.xml` using existing style.
  - Conversion math matches `link_g4x_can_setup.json` and `bench/frames.py`.
  - Bench RealDash simulation path passes without new unknown-frame drift.

### Example 2: Fix warning bit mapping mismatch
- User says: "Fix ST185 warning channel for traction warning bit."
- Actions taken:
  1. Read `bench/frames.py` constants for `0x3F1` byte 6 bit assignments.
  2. Compare with existing warning input in `link_g4x_realdash.xml` and update the bit mapping to match Python/doc contracts.
  3. Re-check `CAN-BUS-ID-ALLOCATION-TABLE.md` warning table for identical bit semantics.
  4. Run `monitor --known-only` and `full-realdash` bench commands.
- Result:
  - Warning channel now triggers on the correct bit position.
  - XML, Python constants, and docs stay aligned for `0x3F1` byte 6.

## Common Issues
- `xml.etree.ElementTree.ParseError: mismatched tag` in `link_g4x_realdash.xml`
  1. Validate XML syntax immediately: `python -c "import xml.etree.ElementTree as ET; ET.parse('link_g4x_realdash.xml')"`
  2. Compare edited node against the nearest working `ST185:` sibling and restore missing closing tags or quote pairs.
  3. Re-run parse command before any bench test.

- `xml.etree.ElementTree.ParseError: not well-formed (invalid token)`
  1. Check for invalid characters in copied enum labels or unit strings.
  2. Replace raw `&` with `&amp;` and ensure attribute quotes are balanced.
  3. Re-run `python -c "import xml.etree.ElementTree as ET; ET.parse('link_g4x_realdash.xml')"`.

- Bench monitor shows unknown/unstable mapping behavior for expected IDs
  1. Run `python bench/can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 monitor --known-only`.
  2. Confirm target signal frame is within `0x3E8`-`0x3F1` and documented in `CAN-BUS-ID-ALLOCATION-TABLE.md`.
  3. Cross-check scaling/offset and byte/bit location in both `link_g4x_can_setup.json` and `bench/frames.py`.
  4. Re-apply XML conversion values to match canonical contract.

- Warning channel flips the wrong indicator (common with `0x3F1` byte 6)
  1. Verify bit index in `bench/frames.py` warning constants.
  2. Verify same bit meaning in `CAN-BUS-ID-ALLOCATION-TABLE.md`.
  3. Update only the corresponding warning mapping in `link_g4x_realdash.xml`.
  4. Re-run `full-realdash` bench flow.

- Python compile check fails after mapping-related edits
  - Error: `SyntaxError` during `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
  1. Open the file named in the traceback and fix the exact syntax line first.
  2. Re-run the same `py_compile` command until clean.
  3. Then rerun XML parse and bench checks to ensure full pipeline integrity.

- Runtime sender test does not reflect RealDash channel updates
  1. Run `set TC_DEVICE=realdash && python apps/trackcluster-can-sender/app.py`.
  2. Verify the XML input name still starts with `ST185:` and matches expected binding name exactly.
  3. Confirm no accidental rename of existing channel keys.
  4. Re-test with `full-realdash` bench command to validate end-to-end mapping.