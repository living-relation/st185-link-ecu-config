# Made with - `cad/fusebox/rev7/`

What made each model file in this folder (Dan 2026-10-17, DECISIONS R149). The model files are gitignored and live in the main checkout (R67); this note is tracked.
Source: the STEP / STL header, the build scripts and the git history. "unconfirmed" = not proven, never guessed. Register for all of `cad/`: [`cad/DRAWING-REVS.md`](../../DRAWING-REVS.md).

| File | Made with | Evidence | Note |
|---|---|---|---|
| `BattRelay_Bar_Power_CuC110_25x6p35.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `BattRelay_Base_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `BattRelay_Base_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `BattRelay_Cover_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `BattRelay_Cover_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `BattRelay_Pad_Out_CuC110_15x3.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Base_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Base_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Cover_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Cover_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Pan_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Pan_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_BarNeg_CuC110_25x6p35_L105.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Bar_Power_CuC110_25x6p35_POS_bus_L226.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Base_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Base_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Cover_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Cover_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Pad_Out_CuC110_15x3.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) | no longer built since R155 (the POWER pads became the C-straps) |
| `Power_Pan_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Pan_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Retainer_R1_PA12_printed.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Retainer_R1_PA12_printed.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `Power_Strap_Out_CuC110_15x3_C.step` | Fusion 360 | `cad/fusebox/src/build_fusion.py` (Fusion API), R155 | 14 copper C-straps (ST185-FB-117) |
| `ST185-FB-117_model.step` | build123d | `cad/drawings/run_fb117.py`: one Fusion strap + the flat blank from `spec.strap_blank()`, each with its 2 PEM CLSS-M5-2 nuts built from PEM Bulletin CL p. CL-5 (`spec.STRAP_PEM`; PEM's STEP needs a sign-up, R163) | drawing model for ST185-FB-117 |
| `ST185-FB-117_stages.step` | build123d | `cad/drawings/run_fb117.py` (`FB117_MODEL_ONLY=1`): the nut install steps as named solids - nuts beside their holes, both pressed with the 0.6 TRIM_OFFCUT, trimmed | stage model for ST185-FB-117 (markup 2026-10-18) |
| `ST185_fusebox_rev7.f3d` | Fusion 360 | native Fusion archive (.f3d); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `ST185_fusebox_rev7_assembly.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/fusebox/src/build_fusion.py` (Fusion API) |  |
| `print/ST185_R1_retainer_clip_PA12.3mf` | Fusion 360 | 3MF has no tool metadata; written by `export_print_files.py` (Fusion C3MF export); `cad/export_print_files.py` (Fusion API STEP / STL / 3MF export, PR #266) |  |
| `print/ST185_R1_retainer_clip_PA12.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); `cad/export_print_files.py` (Fusion API STEP / STL / 3MF export, PR #266) |  |
| `print/ST185_R1_retainer_clip_PA12.stl` | Fusion 360 | STL header: ATF (Autodesk Translation Framework); `cad/export_print_files.py` (Fusion API STEP / STL / 3MF export, PR #266) |  |
