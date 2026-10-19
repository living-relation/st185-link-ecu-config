# Made with - `cad/enclosures/csb3/`

What made each model file in this folder (Dan 2026-10-17, DECISIONS R149). The model files are gitignored and live in the main checkout (R67); this note is tracked.
Source: the STEP / STL header, the build scripts and the git history. "unconfirmed" = not proven, never guessed. Register for all of `cad/`: [`cad/DRAWING-REVS.md`](../../DRAWING-REVS.md).

| File | Made with | Evidence | Note |
|---|---|---|---|
| `CSB3_assembly.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py`, `fusion_real_connectors.py` (Fusion API) | The HD34 body is TE's own model (row below). |
| `CSB3_part_CSB3-Body.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py` (Fusion API) |  |
| `CSB3_part_CSB3-Lid.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py`, `fusion_real_connectors.py` (Fusion API) |  |
| `CSB3_part_ECUMaster_CSB3_manual_v2.1_p.4.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py` (Fusion API) | Purchased / reference part. Original geometry source unconfirmed. |
| `CSB3_part_HD34-24-33PE.step` | build123d | STEP header: Open CASCADE (build123d export); `cad/enclosures/src/real_connectors.py place` | Purchased part: TE's own model `cad/vendor/te/HD34-24-33PE/c-hd34-24-33pe-a-3d.stp` (`cad/vendor/INDEX.md`), only moved into the box frame (z + 84.16); imported into the Fusion document. Replaces the envelope (R184). |
| `CSB3_part_Lock-in_supports_Cat_8847_L10_x2.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py` (Fusion API) | Purchased / reference part. Original geometry source unconfirmed. |
| `CSB3_part_ORING-AS568-039.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py` (Fusion API) | Purchased / reference part. Original geometry source unconfirmed. |
| `CSB3_part_Set_screws_M8x1.25x6_ISO_4026_x2.step` | Fusion 360 | STEP header: Autodesk Translation Framework (Fusion export); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py` (Fusion API) | Purchased / reference part. Original geometry source unconfirmed. |
| `ST185-CSB3-Enclosure.f3d` | Fusion 360 | native Fusion archive (.f3d); Fusion document `ST185-CSB3-Enclosure`; `cad/enclosures/src/enclosure_fixes_v3.py`, `csb3_lockin.py`, `fusion_real_connectors.py` (Fusion API) |  |
