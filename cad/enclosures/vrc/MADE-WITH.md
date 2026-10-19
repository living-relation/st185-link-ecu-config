# Made with - `cad/enclosures/vrc/`

What made each model file in this folder (Dan 2026-10-17, DECISIONS R149). The model files are gitignored and live in the main checkout (R67); this note is tracked.
Source: the STEP / STL header, the build scripts and the git history. "unconfirmed" = not proven, never guessed. Register for all of `cad/`: [`cad/DRAWING-REVS.md`](../../DRAWING-REVS.md).

| File | Made with | Evidence | Note |
|---|---|---|---|
| `ST185-VRC-Enclosure.f3d` | Fusion 360 | native Fusion archive (.f3d); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py`, `vrc_lp16_cutout.py`, `fusion_real_connectors.py` (Fusion API) |  |
| `VRC_assembly.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py`, `vrc_lp16_cutout.py`, `fusion_real_connectors.py` (Fusion API) | The LP-16 bodies are the maker's model (rows below). |
| `VRC_part_LP16-IN_LP-16-C05SX-02-101.step` | build123d | STEP header: Open CASCADE (build123d export); `cad/enclosures/src/real_connectors.py place` | Purchased part: the CNLINKO model `cad/vendor/cnlinko/LP-16-C05SX-02-101/LP-16-C05SX-02-101.step` (Dan's Fusion copy, `cad/vendor/INDEX.md`) placed in the +x wall; its fused jam nut cut out and set on the 3.5 wall's inside face, the core inside the wall trimmed to the panel-hole flats (16.4). Imported into the Fusion document. Replaces the envelope (R184). |
| `VRC_part_LP16-OUT_LP-16-C05SX-02-101.step` | build123d | STEP header: Open CASCADE (build123d export); `cad/enclosures/src/real_connectors.py place` | Same as LP16-IN, in the -x wall. |
| `VRC_part_ORING-AS568-039.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py` (Fusion API) | Purchased / reference part. Original geometry source unconfirmed. |
| `VRC_part_OpenLogicEFI_NCV1124_VR_module_RevB3.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py` (Fusion API) | Purchased / reference part. Board shape from the OpenLogicEFI KiCad file (`cad/enclosures/PLAN-notes.md`); how it got into Fusion is unconfirmed. |
| `VRC_part_VRC-Board-Holder.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py` (Fusion API) |  |
| `VRC_part_VRC-Board-Holder.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py` (Fusion API) |  |
| `VRC_part_VRC-Body.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py`, `vrc_lp16_cutout.py` (Fusion API) |  |
| `VRC_part_VRC-Lid.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-VRC-Enclosure`; `cad/enclosures/src/build_vrc_holder.py`, `enclosure_fixes_v3.py` (Fusion API) |  |
| `print/ST185_VRC_board_holder_PA12.3mf` | Fusion 360 | 3MF has no tool metadata; written by `export_print_files.py` (Fusion C3MF export); `cad/export_print_files.py` (Fusion API STEP / STL / 3MF export, PR #266) |  |
| `print/ST185_VRC_board_holder_PA12.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/export_print_files.py` (Fusion API STEP / STL / 3MF export, PR #266) |  |
| `print/ST185_VRC_board_holder_PA12.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/export_print_files.py` (Fusion API STEP / STL / 3MF export, PR #266) |  |
