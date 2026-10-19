# Drawing / model revision register

Rules (Dan, 2026-10-17): the model drives the rev letter; a drawing always carries its model's letter. Letters start at A and skip I, L, O, Q.
Drawing-only clerical changes (notes, added views or sheets, no change to fit / form / function) add .01, .02, ... (e.g. H.01); a model change takes the next letter and resets the decimal.
Redlines go on the drawing first, then the model is fixed, then the drawing is regenerated from the model. Filenames carry no rev.


Fuel hanger evidence: the fairsolid run `C:\projects\_archive\2026-10-17-fairsolid\fairsolid\runs\fuel_hanger_billet_1014\` (moved from `C:\projects\active\fairsolid` on 2026-10-17, when Fairsolid moved into handbuilt-cad `pipelines/fairsolid/`) - `rev1` = the run root folder, then `rev2`..`rev8`; each folder is one release. `runs/` is gitignored in fairsolid, so there is no git history for it; a part counts as released in a folder when its model changed there (volume / bounding box in that folder's `hanger_report.json`).
| Item | Part no. | Model | Rev | Date | Change | Evidence (counted releases) | Files |
|---|---|---|---|---|---|---|---|
| CSB3 enclosure - body | ST185-CSB3-101 | `cad/enclosures/csb3/CSB3_part_CSB3-Body.step` (Fusion 360) | C.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/enclosures/csb3/ST185-CSB3-101.pdf` |
| CSB3 enclosure - lid | ST185-CSB3-102 | `cad/enclosures/csb3/CSB3_part_CSB3-Lid.step` (Fusion 360) | C.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/enclosures/csb3/ST185-CSB3-102.pdf` |
| VRC enclosure - body | ST185-VRC-101 | `cad/enclosures/vrc/VRC_part_VRC-Body.step` (Fusion 360) | D | 2026-10-17 | First engine drawing from the model; replaces the Fusion body view of `ST185-VRC-enclosure-drawing.pdf` (rev letter: see "How the letters were found") | see "How the letters were found" | `cad/enclosures/vrc/ST185-VRC-101.pdf` |
| VRC enclosure - lid | ST185-VRC-102 | `cad/enclosures/vrc/VRC_part_VRC-Lid.step` (Fusion 360) | A | 2026-10-17 | First engine drawing from the model; replaces the Fusion lid view of `ST185-VRC-enclosure-drawing.pdf` (rev letter: see "How the letters were found") | see "How the letters were found" | `cad/enclosures/vrc/ST185-VRC-102.pdf` |
| VRC board holder | ST185-VRC-103 | `cad/enclosures/vrc/print/ST185_VRC_board_holder_PA12.step` (Fusion 360) | D | 2026-10-17 | First issue from the model (rev letter: see "How the letters were found") | see "How the letters were found" | `cad/enclosures/vrc/ST185-VRC-103.pdf` |
| DRB102 firewall plate | ST185-DRB-101 | `cad/drb102-plate/DRB102-firewall-plate.step` (CadQuery) | C | 2026-10-17 | First issue from the model (rev letter: see "How the letters were found") | see "How the letters were found" | `cad/drb102-plate/ST185-DRB-101.pdf` |
| Fuse box rev 7 - POWER box - base | ST185-FB-101 | `cad/fusebox/rev7/Power_Base_PA12_printed.step` (Fusion 360) | V.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-101.pdf` |
| Fuse box rev 7 - POWER box - belly pan | ST185-FB-102 | `cad/fusebox/rev7/Power_Pan_PA12_printed.step` (Fusion 360) | G.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-102.pdf` |
| Fuse box rev 7 - POWER box - cover | ST185-FB-103 | `cad/fusebox/rev7/Power_Cover_PA12_printed.step` (Fusion 360) | G.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-103.pdf` |
| Fuse box rev 7 - R1 retainer clip | ST185-FB-104 | `cad/fusebox/rev7/Power_Retainer_R1_PA12_printed.step` (Fusion 360) | E.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-104.pdf` |
| Fuse box rev 7 - LOGIC box - base | ST185-FB-105 | `cad/fusebox/rev7/Logic_Base_PA12_printed.step` (Fusion 360) | T | 2026-10-18 | Model T (#324: LOGIC strips held on every side); drawing markup 18/10/26 (R184-R197): plain notes, no edge-break line | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-105.pdf` |
| Fuse box rev 7 - LOGIC box - belly pan | ST185-FB-106 | `cad/fusebox/rev7/Logic_Pan_PA12_printed.step` (Fusion 360) | H.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-106.pdf` |
| Fuse box rev 7 - LOGIC box - cover | ST185-FB-107 | `cad/fusebox/rev7/Logic_Cover_PA12_printed.step` (Fusion 360) | K.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-107.pdf` |
| Fuse box rev 7 - Battery relay box - base | ST185-FB-108 | `cad/fusebox/rev7/BattRelay_Base_PA12_printed.step` (Fusion 360) | J.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-108.pdf` |
| Fuse box rev 7 - Battery relay box - cover | ST185-FB-109 | `cad/fusebox/rev7/BattRelay_Cover_PA12_printed.step` (Fusion 360) | G.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-109.pdf` |
| Fuse box rev 7 - Battery relay bar | ST185-FB-111 | `cad/fusebox/rev7/BattRelay_Bar_Power_CuC110_25x6p35.step` (Fusion 360) | C.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-111.pdf` |
| Fuse box rev 7 - Battery block pad | ST185-FB-112 | `cad/fusebox/rev7/BattRelay_Pad_Out_CuC110_25p4x3p2.step` (Fusion 360) | C.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-112.pdf` |
| Fuse box rev 7 - POWER NEG bar | ST185-FB-113 | `cad/fusebox/rev7/Power_BarNeg_CuC110_25x6p35_L105.step` (Fusion 360) | C.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-113.pdf` |
| Fuse box rev 7 - POWER POS bus bar | ST185-FB-114 | `cad/fusebox/rev7/Power_Bar_Power_CuC110_25x6p35_POS_bus_L226.step` (Fusion 360) | B.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-114.pdf` |
| Fuse box rev 7 - LOGIC bus strip 1 | ST185-FB-115 | `cad/fusebox/rev7/Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step` (Fusion 360) | E.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-115.pdf` |
| Fuse box rev 7 - LOGIC bus strip 2 | ST185-FB-116 | `cad/fusebox/rev7/Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step` (Fusion 360) | E.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-116.pdf` |
| Fuse box rev 7 - POWER output C-strap | ST185-FB-117 | `cad/fusebox/rev7/Power_Strap_Out_CuC110_15x3_C.step` (Fusion 360; 14 identical straps) + `ST185-FB-117_model.step` (build123d: one strap + its flat blank) | A.01 | 2026-10-17 | Clerical (N15): note 5 = first-article proof test, each PEM nut to 6 N.m on a sample strap (model unchanged; A = new model R155) | new model = A (R147) | `cad/fusebox/rev7/drawings/ST185-FB-117.pdf` |
| Fuse box rev 7 - POWER box - assembly | ST185-FB-100P | `cad/fusebox/rev7/ST185_fusebox_rev7_assembly.step` (Fusion 360) | W | 2026-10-18 | First assembly drawing (buildability review, R181): BOM from `rev7/fusebox-parts-power.csv`, 5 install steps, the TE terminal insertion / harness-tie notes | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-100P.pdf` |
| Fuse box rev 7 - LOGIC box - assembly | ST185-FB-100L | `cad/fusebox/rev7/ST185_fusebox_rev7_assembly.step` (Fusion 360) | V | 2026-10-18 | Base T (#324); drawing markup 18/10/26 (R184-R197): primary-only balloons, fuse / relay label sheet, harness wire label sheets, 7 install steps incl. PEM nuts | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-100L.pdf` |
| Fuse box rev 7 - Battery relay box - assembly | ST185-FB-100B | `cad/fusebox/rev7/ST185_fusebox_rev7_assembly.step` (Fusion 360) | N.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): primary-only balloons, fuse / relay / wire label sheet, plain notes | see "How the letters were found" | `cad/fusebox/rev7/drawings/ST185-FB-100B.pdf` |
| VRC enclosure - assembly | ST185-VRC-100 | `cad/enclosures/vrc/VRC_assembly.step` (Fusion 360) | E | 2026-10-18 | First assembly drawing (buildability review, R181); holder screws M6 x 14 Lemu 2990806014 at the v2 bosses (R126 / R131) | see "How the letters were found" | `cad/enclosures/vrc/ST185-VRC-100.pdf` |
| CSB3 enclosure - assembly | ST185-CSB3-100 | `cad/enclosures/csb3/CSB3_assembly.step` (Fusion 360) | D | 2026-10-18 | First assembly drawing (buildability review, R181); Cat. 8847 lock-in supports + M8 x 6 seal set screws (R133) | see "How the letters were found" | `cad/enclosures/csb3/ST185-CSB3-100.pdf` |
| DRB102 firewall plate - assembly | ST185-DRB-100 | `cad/drb102-plate/DRB102-firewall-plate-assembly.step` (CadQuery) | C | 2026-10-18 | First assembly drawing (buildability review, R181) | see "How the letters were found" | `cad/drb102-plate/ST185-DRB-100.pdf` |
| Fuel hanger - flange (integral lug) | ST185-FH-101 | `cad/fuel-hanger/fuel_hanger.py` | G.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | top plate changed in fairsolid rev1 (97.18 cm3, lug integral) = A, rev2 (73.31) = B, rev3 (87.60; rev4/5 identical) = C, rev6 (82.66) = D, rev7 (76.01, bolt-on lug) = E, rev8 (75.96, M5 thru, rejected) = F; this release (89.94) = G | `cad/fuel-hanger/drawings/ST185-FH-101.pdf` / `.dxf` |
| Fuel hanger - lug block | ST185-FH-102 | - | A (obsolete) | 2026-10-17 | Merged into FH-101 rev G | only in rev7 (12.77 cm3) = A; rev8 identical | - |
| Fuel hanger - strut | ST185-FH-103 | `cad/fuel-hanger/build_holder.py` | F.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | rev1 (71.77; rev2 identical) = A, rev3 (71.88) = B, rev4 (71.40; rev5 identical) = C, rev6 (60.28) = D, rev7 (64.66; rev8 identical) = E; this PR (option B holder) = F | `cad/fuel-hanger/drawings/ST185-FH-103.pdf` / `.dxf` |
| Fuel hanger - foot | ST185-FH-104 | `cad/fuel-hanger/build_holder.py` | E.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | rev1 (24.20; rev2/3 identical) = A, rev4 (24.88; rev5 identical) = B, rev6 (19.21) = C, rev7 (20.00; rev8 identical) = D; this PR (option B holder) = E | `cad/fuel-hanger/drawings/ST185-FH-104.pdf` / `.dxf` |
| Fuel hanger - pump saddle | ST185-FH-105 | `cad/fuel-hanger/build_holder.py` | D.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): plain machinist notes, change notes and the edge-break line removed, tangent edges in the trimetric | rev1 (24.15; rev2/3 identical) = A, rev4 (24.18) = B, rev5 (15.95, band-clamp saddle; rev6-8 identical) = C; this PR (option B holder) = D | `cad/fuel-hanger/drawings/ST185-FH-105.pdf` / `.dxf` |
| Fuel hanger - assembly | ST185-FH-100 | `cad/fuel-hanger/build_holder.py` | K.01 | 2026-10-18 | Clerical, drawing markup 18/10/26 (R184-R197): primary-only balloons, exploded view with the hidden screws, plain notes | every fairsolid rev changed a part = A-H, #279 (flange G) = J, this release (option B holder) = K | `cad/fuel-hanger/drawings/ST185-FH-100.pdf` |

## How the letters were found (2026-10-17, DECISIONS R147)

Rev A is only for a brand-new model. An existing model: count its past releases in the repo history - the PRs / commits that released or changed it, first release = A (Dan 2026-10-17: this overrides converting rev numbers, so rev 7 is not automatically G); no history -> count its saved versions.

| Part no. | Rev | Evidence |
|---|---|---|
| ST185-CSB3-101 | C | No rev number. PRs that changed the body: #139 first release (A), #272 SteveCAD audit v3 tab slots F01, standoff M3 F08, tab corners F11 (B), #274 R133 lock-in supports + M8 seal holes (C). Not counted: #143 / #146 (moves), #189 (trimetric only), #273 (lid only, "body unchanged"). Cross-check: Fusion document `ST185-CSB3-Enclosure` v4 (v3 = lid loft). |
| ST185-CSB3-102 | C | No rev number. PRs that changed the lid: #139 first release (A), #272 F09 D-hole corners R3 (B), #273 R132 lid loft D62 x 6 (C). Not counted: #274 (`csb3_lockin.py` edits the body only). |
| ST185-VRC-101 | D | No rev number. PRs that changed the body: #139 first release (A), #267 holder v2 floor bosses - the 4 M3 bosses out, 2 x D11 bosses in (B), #272 SteveCAD audit v3 F01 tab slots 6.6, F02 bosses +1, spotface, F11 tab corners R3, IN / OUT upright (C), #273 N4 bosses to z 12.5, drill 5.0 x 11.5 (R131) (D). Not counted: #143 / #146 (moves), #189 (trimetric only), #195 ("counterbores stay as modelled"), #198 (drawing notes, BOMs), #239 (holder modelled on the existing M3 bosses, body unchanged). Geometry checked against the STEP 2026-10-17. |
| ST185-VRC-102 | A | No rev number. Only release of the lid: #139 (A). No later PR edits the lid (`enclosure_fixes_v3.py` F08 checks the lid screw holes, which are in the body; no change). |
| ST185-VRC-103 | D | No rev number on the file ("v2" in #267 names a design pass, not the current rev). PRs that changed the holder: #239 first model (A), #267 holder v2 (B), #272 recess height follows the F02 boss (C), #273 N4 +2.5 mm, lead reliefs, M6 x 14 (D). Not counted: #266 (print-file export), #275 (comment only). |
| ST185-DRB-101 | C | No rev number. PRs that changed the plate (`build_DRB102_plate.py`): #143 first in the repo (A), #272 D1 / F08 / OPEN-10 groove (B), #275 M5 tapped through (C). Not counted: #189 (trimetric only). |
| ST185-FB-101 | V | 18 releases of `Power_Base_PA12_printed` in the repo history: #160 (A), #171 (B), #190 (C), #200 (D), #217 (E), #229 (F), #265 (G), #268 (H), #270 (J), #271 (K), #272 (M), #273 (N), #275 (P), #277 (R), #291 (S, R155 N14 = B: base volume 840.3 -> 799.9 cm3), PR #297 (T, markup 2026-10-17: base volume 799.9 -> 848.2 cm3), PR #303 (U, fit audit / N21 2026-10-18: volume 848.2 -> 846.0 cm3), this PR (V, buildability review R181: strap hook lead-in + strap seat pocket, volume 846.0 -> 845.5 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-102 | G | 7 releases of `Power_Pan_PA12_printed` in the repo history: #171 (A), #190 (B), #200 (C), #265 (D), #270 (E), PR #291 (F, R155: pan volume 157.1 -> 156.9 cm3, the OUT exits follow the strap lugs), this PR (G, fit audit / N21 2026-10-18: volume 157.0 -> 156.7 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-103 | G | 7 releases of `Power_Cover_PA12_printed` in the repo history: #160 (A), #171 (B), #190 (C), #200 (D), #265 (E), #271 (F), this PR (G, markup 2026-10-17: cover volume 199.4 -> 199.0 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-104 | E | 5 releases of `Power_Retainer_R1_PA12_printed` in the repo history: #265 (A), #266 (B), #271 (C), PR #297 (D, markup 2026-10-17: clip volume 1.7 -> 1.3 cm3), this PR (E, fit audit / N21 2026-10-18: volume 1.3 -> 1.3 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-105 | S | 15 releases of `Logic_Base_PA12_printed` in the repo history: #160 (A), #171 (B), #190 (C), #215 (D), #217 (E), #229 (F), #237 (G), #265 (H), #270 (J), #271 (K), #273 (M), #275 (N), PR #297 (P, markup 2026-10-17: base volume 350.0 -> 357.7 cm3), PR #303 (R, fit audit / N21 2026-10-18: volume 357.7 -> 396.3 cm3), PR #308 (S, R170 HEAD relay 87a slots: volume 396.3 -> 395.9 cm3; the drawing was reissued in the buildability review, 2026-10-18). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. #275 from the source diff (LOGIC Bus 2 x 48.1 corner joint stays solid; size/volume unchanged at report resolution). Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-106 | H | 8 releases of `Logic_Pan_PA12_printed` in the repo history: #171 (A), #190 (B), #215 (C), #217 (D), #265 (E), #273 (F), PR #297 (G, markup 2026-10-17: pan volume 77.6 -> 83.5 cm3), this PR (H, fit audit / N21 2026-10-18: volume 83.5 -> 85.3 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-107 | K | 10 releases of `Logic_Cover_PA12_printed` in the repo history: #160 (A), #171 (B), #172 (C), #215 (D), #265 (E), #270 (F), #271 (G), #273 (H), PR #297 (J, markup 2026-10-17: cover volume 100.9 -> 101.0 cm3), this PR (K, fit audit / N21 2026-10-18: volume 101.0 -> 103.1 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-108 | J | 9 releases of `BattRelay_Base_PA12_printed` in the repo history: #160 (A), #171 (B), #190 (C), #265 (D), #270 (E), #271 (F), #277 (G), PR #297 (H, markup 2026-10-17: base volume 173.4 -> 191.8 cm3), this PR (J, fit audit / N21 2026-10-18: volume 191.8 -> 190.4 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-109 | G | 7 releases of `BattRelay_Cover_PA12_printed` in the repo history: #160 (A), #171 (B), #172 (C), #265 (D), #270 (E), #271 (F), this PR (G, fit audit / N21 2026-10-18: volume 107.5 -> 107.4 cm3). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-111 | C | 3 releases of `BattRelay_Bar_Power_CuC110_25x6p35` in the repo history: #153 (A), #160 (B), #272 (C). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-112 | C | 3 releases of `Power_Pad_Out_CuC110_15x3` in the repo history: #153 (A), #272 (B), this PR (C, markup 2026-10-17: new model `BattRelay_Pad_Out_CuC110_25p4x3p2` (mass 10.5 g)). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). | R155 (this PR): the POWER pads are gone; the drawing is the battery block pad `BattRelay_Pad_Out_CuC110_15x3` (same 17.5 x 15 x 3 geometry), so only the title and quantity change = clerical .01.
| ST185-FB-113 | C | 3 releases of `Power_BarNeg_CuC110_25x6p35_L105` in the repo history: #200 (A), #272 (B), #273 (C). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. #273 from the source diff (N3: bar x 4-109 -> 5-110, GND stud 102.0; mass unchanged). Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-114 | B | 2 releases of `Power_Bar_Power_CuC110_25x6p35_POS_bus_L226` in the repo history: #200 (A), #272 (B). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-115 | E | 5 releases of `Logic_Strip_Logic_CuC110_25p4x3p2_on_edge` in the repo history: #190 (A), #217 (B), #272 (C), #273 (D), this PR (E, markup 2026-10-17: strip mass 151.1 -> 153.1 g). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-116 | E | 5 releases of `Logic_Strip_Logic_CuC110_25p4x3p2_on_edge` in the repo history: #190 (A), #217 (B), #272 (C), #273 (D), this PR (E, markup 2026-10-17: strip mass 151.1 -> 153.1 g). First release = A. Counted = PRs where the part's size / volume (printed) or mass (copper) in `cad/fusebox/fusebox_report.json` (rev 4-6) / `cad/fusebox/rev7/fusebox_report.json` (rev 7) changed on main. Same model as FB-115 (Bus 2 strip), same letter. Rev number 7 not converted (Dan 2026-10-17). Not counted: PRs before the part had this name (#149-#153 rev 1-3 bodies), source-only PRs released by a later rebuild (#259-#263 -> #265), #278 (default-off variant). |
| ST185-FB-100P | W | Assembly: a release = a PR that released any of its fabricated parts (the ST185-FH-100 rule). Union of the FB-101 / -102 / -103 / -104 / -113 / -114 / -117 release lists above: #160, #171, #190, #200, #217, #229, #265, #266, #268, #270, #271, #272, #273, #275, #277, #291, #297, #303, this PR = 19 = W. Part letters per PR in `cad/fusebox/rev7/ST185-FB-100P.REVLOG.md`. First assembly drawing at W. |
| ST185-FB-100L | U | Assembly (FH-100 rule). Union of FB-105 / -106 / -107 / -115 / -116: #160, #171, #172, #190, #215, #217, #229, #237, #265, #270, #271, #272, #273, #275, #297, #303, #308 = 17 = U. First assembly drawing at U. |
| ST185-FB-100B | N | Assembly (FH-100 rule). Union of FB-108 / -109 / -111 / -112: #153, #160, #171, #172, #190, #265, #270, #271, #272, #277, #297, #303 = 12 = N. First assembly drawing at N. |
| ST185-VRC-100 | E | Assembly (FH-100 rule). Union of VRC-101 / -102 / -103: #139, #239, #267, #272, #273 = 5 = E. |
| ST185-CSB3-100 | D | Assembly (FH-100 rule). Union of CSB3-101 / -102: #139, #272, #273, #274 = 4 = D. |
| ST185-DRB-100 | C | Assembly (FH-100 rule). DRB-101 releases #143, #272, #275 = 3 = C (the connector, flange and O-ring are bought). |
| ST185-FB-117 | A.01 | New model in this PR (R155, N14 = B): Rev A only for a brand-new model (R147). | N15 (this PR): proof-test note only = clerical .01.

The older Fusion drawings `cad/enclosures/csb3/ST185-CSB3-enclosure-drawing.pdf` and `cad/enclosures/vrc/ST185-VRC-enclosure-drawing.pdf` and their 2026-10-17 markups are kept as they are (no rev letter assigned). The VRC body and lid now have engine drawings (ST185-VRC-101 D, -102 A, 2026-10-17); the old Fusion VRC drawing shows hidden lines (R150) and stays for reference only.

## Made with - every model file in `cad/` (DECISIONS R149)

From the STEP / STL headers (`FILE_NAME` originating system), the build scripts and the git history; "unconfirmed" = not proven, never guessed. Each model folder has the same facts in its own `MADE-WITH.md`. The fuel hanger has its own `cad/fuel-hanger/MADE-WITH.md`.

| Model file (under `cad/`) | Made with | Note |
|---|---|---|
| busbar/design-A-rev3/A_rev3_ASSEMBLY.step | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_BarScrew_ISO7380_M4x10_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/A_rev3_Bar_NEG_Al6061.step | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_Bar_POS_Al6061.step | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_Body_printed_ASA.step | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_Body_printed_ASA.stl | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_Bolt_ISO4017_M10x30_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/A_rev3_Bolt_ISO4017_M10x35_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/A_rev3_Bolt_ISO4017_M8x25_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/A_rev3_Bolt_ISO4017_M8x35_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/A_rev3_Cover_printed_ASA.step | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_Cover_printed_ASA.stl | Fusion 360 |  |
| busbar/design-A-rev3/A_rev3_HeatSetInsert_M4x8.1_brass.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/A_rev3_REF_MountScrew_ISO7380_M6x16_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A-rev3/ST185_busbar_A_rev3.f3d | Fusion 360 |  |
| busbar/design-A/A_ASSEMBLY.step | Fusion 360 |  |
| busbar/design-A/A_BarScrew_ISO7380_M4x10_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/A_Bar_NEG_Al6061.step | Fusion 360 |  |
| busbar/design-A/A_Bar_POS_Al6061.step | Fusion 360 |  |
| busbar/design-A/A_Body_printed_ASA.step | Fusion 360 |  |
| busbar/design-A/A_Body_printed_ASA.stl | Fusion 360 |  |
| busbar/design-A/A_Bolt_ISO4017_M10x30_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/A_Bolt_ISO4017_M10x35_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/A_Bolt_ISO4017_M8x25_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/A_Bolt_ISO4017_M8x35_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/A_Cover_printed_ASA.step | Fusion 360 |  |
| busbar/design-A/A_Cover_printed_ASA.stl | Fusion 360 |  |
| busbar/design-A/A_HeatSetInsert_M4x8.1_brass.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/A_REF_MountScrew_ISO7380_M6x16_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-A/ST185_busbar_A.f3d | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_ASSEMBLY.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_BarScrew_ISO7380_M4x10_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev2/B_rev2_Bar_NEG_Al6061.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_Bar_POS_Al6061.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_Bar_UNI_Al6061.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_Body_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_Body_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_Bolt_ISO4017_M8x25_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev2/B_rev2_Bolt_ISO4017_M8x30_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev2/B_rev2_Cover_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_Cover_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_HeatSetInsert_M4x8.1_brass.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev2/B_rev2_LinkStrap_6061_6x20_P50.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_NotchPlug_N_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_NotchPlug_N_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_NotchPlug_P_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_NotchPlug_P_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev2/B_rev2_REF_MountScrew_ISO7380_M6x16_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev2/B_rev2_SetScrew_ISO4029_M8x12_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev2/ST185_busbar_B_rev2.f3d | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_ASSEMBLY.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_BarScrew_ISO7380_M4x10_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev3/B_rev3_Bar_NEG_Al6061.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_Bar_POS_Al6061.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_Bar_UNI_Al6061.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_Body_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_Body_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_Bolt_ISO4017_M8x25_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev3/B_rev3_Bolt_ISO4017_M8x30_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev3/B_rev3_Cover_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_Cover_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_HeatSetInsert_M4x8.1_brass.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev3/B_rev3_LinkStrap_6061_6x20_P50.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_NotchPlug_N_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_NotchPlug_N_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_NotchPlug_P_printed_ASA.step | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_NotchPlug_P_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B-rev3/B_rev3_REF_MountScrew_ISO7380_M6x16_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev3/B_rev3_SetScrew_ISO4029_M8x12_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B-rev3/ST185_busbar_B_rev3.f3d | Fusion 360 |  |
| busbar/design-B/B_ASSEMBLY.step | Fusion 360 |  |
| busbar/design-B/B_Bar_NEG_Al6061.step | Fusion 360 |  |
| busbar/design-B/B_Bar_POS_Al6061.step | Fusion 360 |  |
| busbar/design-B/B_Body_printed_ASA.step | Fusion 360 |  |
| busbar/design-B/B_Body_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B/B_Bolt_ISO4017_M8x25_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B/B_ClampScrew_ISO7380_M4x10_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B/B_Cover_printed_ASA.step | Fusion 360 |  |
| busbar/design-B/B_Cover_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B/B_HeatSetInsert_M4x8.1_brass.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B/B_Locator_NEG_printed_ASA.step | Fusion 360 |  |
| busbar/design-B/B_Locator_NEG_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B/B_Locator_POS_printed_ASA.step | Fusion 360 |  |
| busbar/design-B/B_Locator_POS_printed_ASA.stl | Fusion 360 |  |
| busbar/design-B/B_REF_MountScrew_ISO7380_M6x16_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B/B_SetScrew_ISO4029_M8x12_A2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| busbar/design-B/ST185_busbar_B.f3d | Fusion 360 |  |
| drb102-plate/DRB102-firewall-plate-assembly.step | CadQuery |  |
| drb102-plate/DRB102-firewall-plate.step | CadQuery |  |
| enclosures/csb3/CSB3_assembly.step | Fusion 360 |  |
| enclosures/csb3/CSB3_part_CSB3-Body.step | Fusion 360 |  |
| enclosures/csb3/CSB3_part_CSB3-Lid.step | Fusion 360 |  |
| enclosures/csb3/CSB3_part_ECUMaster_CSB3_manual_v2.1_p.4.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/csb3/CSB3_part_HD34-24-33PE_envelope_from_TE_CVM_model.step | Fusion 360 | Purchased / reference part. Envelope from the TE CVM model (file name); original geometry source unconfirmed. |
| enclosures/csb3/CSB3_part_Lock-in_supports_Cat_8847_L10_x2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/csb3/CSB3_part_ORING-AS568-039.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/csb3/CSB3_part_Set_screws_M8x1.25x6_ISO_4026_x2.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/csb3/ST185-CSB3-Enclosure.f3d | Fusion 360 |  |
| enclosures/vrc/ST185-VRC-Enclosure.f3d | Fusion 360 |  |
| enclosures/vrc/VRC_assembly.step | Fusion 360 |  |
| enclosures/vrc/VRC_part_LP16-IN_LP-16-C05SX-02-101_envelope.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/vrc/VRC_part_LP16-OUT_LP-16-C05SX-02-101_envelope.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/vrc/VRC_part_ORING-AS568-039.step | Fusion 360 | Purchased / reference part. Original geometry source unconfirmed. |
| enclosures/vrc/VRC_part_OpenLogicEFI_NCV1124_VR_module_RevB3.step | Fusion 360 | Purchased / reference part. Board shape from the OpenLogicEFI KiCad file (`cad/enclosures/PLAN-notes.md`); how it got into Fusion is unconfirmed. |
| enclosures/vrc/VRC_part_VRC-Board-Holder.step | Fusion 360 |  |
| enclosures/vrc/VRC_part_VRC-Board-Holder.stl | Fusion 360 |  |
| enclosures/vrc/VRC_part_VRC-Body.step | Fusion 360 |  |
| enclosures/vrc/VRC_part_VRC-Lid.step | Fusion 360 |  |
| enclosures/vrc/print/ST185_VRC_board_holder_PA12.3mf | Fusion 360 |  |
| enclosures/vrc/print/ST185_VRC_board_holder_PA12.step | Fusion 360 |  |
| enclosures/vrc/print/ST185_VRC_board_holder_PA12.stl | Fusion 360 |  |
| fusebox/BattRelay_Bar_Power_CuC110_25x6p35.step | Fusion 360 |  |
| fusebox/BattRelay_Base_PA12_printed.step | Fusion 360 |  |
| fusebox/BattRelay_Base_PA12_printed.stl | Fusion 360 |  |
| fusebox/BattRelay_Cover_PA12_printed.step | Fusion 360 |  |
| fusebox/BattRelay_Cover_PA12_printed.stl | Fusion 360 |  |
| fusebox/BattRelay_Pad_Out_CuC110_15x3.step | Fusion 360 |  |
| fusebox/Logic_Base_PA12_printed.step | Fusion 360 |  |
| fusebox/Logic_Base_PA12_printed.stl | Fusion 360 |  |
| fusebox/Logic_Cover_PA12_printed.step | Fusion 360 |  |
| fusebox/Logic_Cover_PA12_printed.stl | Fusion 360 |  |
| fusebox/Logic_Pan_PA12_printed.step | Fusion 360 |  |
| fusebox/Logic_Pan_PA12_printed.stl | Fusion 360 |  |
| fusebox/Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step | Fusion 360 |  |
| fusebox/Power_Bar_Power_CuC110_25x6p35.step | Fusion 360 |  |
| fusebox/Power_Base_PA12_printed.step | Fusion 360 |  |
| fusebox/Power_Base_PA12_printed.stl | Fusion 360 |  |
| fusebox/Power_Cover_PA12_printed.step | Fusion 360 |  |
| fusebox/Power_Cover_PA12_printed.stl | Fusion 360 |  |
| fusebox/Power_Pad_Out_CuC110_15x3.step | Fusion 360 |  |
| fusebox/Power_Pan_PA12_printed.step | Fusion 360 |  |
| fusebox/Power_Pan_PA12_printed.stl | Fusion 360 |  |
| fusebox/ST185_fusebox_rev6.f3d | Fusion 360 |  |
| fusebox/ST185_fusebox_rev6_assembly.step | Fusion 360 |  |
| fusebox/rev7/BattRelay_Bar_Power_CuC110_25x6p35.step | Fusion 360 |  |
| fusebox/rev7/BattRelay_Base_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/BattRelay_Base_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/BattRelay_Cover_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/BattRelay_Cover_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/BattRelay_Pad_Out_CuC110_15x3.step | Fusion 360 |  |
| fusebox/rev7/Logic_Base_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Logic_Base_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Logic_Cover_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Logic_Cover_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Logic_Pan_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Logic_Pan_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step | Fusion 360 |  |
| fusebox/rev7/Power_BarNeg_CuC110_25x6p35_L105.step | Fusion 360 |  |
| fusebox/rev7/Power_Bar_Power_CuC110_25x6p35_POS_bus_L226.step | Fusion 360 |  |
| fusebox/rev7/Power_Base_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Power_Base_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Power_Cover_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Power_Cover_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Power_Pad_Out_CuC110_15x3.step | Fusion 360 | no longer built since R155 (the POWER pads became the C-straps); the file in the main checkout is the last export |
| fusebox/rev7/Power_Pan_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Power_Pan_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Power_Retainer_R1_PA12_printed.step | Fusion 360 |  |
| fusebox/rev7/Power_Retainer_R1_PA12_printed.stl | Fusion 360 |  |
| fusebox/rev7/Power_Strap_Out_CuC110_15x3_C.step | Fusion 360 | R155: 14 copper C-straps (`cad/fusebox/src/build_fusion.py`) |
| fusebox/rev7/ST185-FB-117_model.step | build123d | drawing model: one Fusion strap + the flat blank from `spec.strap_blank()` (`cad/drawings/run_fb117.py`) |
| fusebox/rev7/ST185_fusebox_rev7.f3d | Fusion 360 |  |
| fusebox/rev7/ST185_fusebox_rev7_assembly.step | Fusion 360 |  |
| fusebox/rev7/print/ST185_R1_retainer_clip_PA12.3mf | Fusion 360 |  |
| fusebox/rev7/print/ST185_R1_retainer_clip_PA12.step | Fusion 360 |  |
| fusebox/rev7/print/ST185_R1_retainer_clip_PA12.stl | Fusion 360 |  |

Totals (fuel hanger not included): 163 model files - Fusion 360 161, CadQuery 2.
