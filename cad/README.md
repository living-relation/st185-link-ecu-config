# ST185 CAD index

The ONE list of every custom-part CAD model (DECISIONS R77). **A new CAD model gets a row here in the same PR that adds it.**

- **Summary page** = tracked HTML in git (renders, drawings). Open it from the repo or the research hub.
- **Model files** (STEP, STL, Fusion `.f3d`, busbar drawing PDFs) are **gitignored and local only**. They sit in the same `cad/` folder of the main checkout, `C:\projects\active\st185-link-ecu-config\cad\...` (a worktree has only the tracked files).
- **Trimetric** (DECISIONS R83) = one PNG per model, same camera and style for all, rendered headless from the model's STEP by `cad/render_trimetric.py` (never a Fusion document, R74) and tracked beside the model (`cad/<model>/trimetric*.png`; the fuel hanger's sits in the reference-only `cad/fuel-hanger/`). `cad/trimetrics.json` records which STEP files each picture came from and their dates; the research hub warns when a STEP is newer than its picture or a row has no picture. **A new or changed CAD model re-renders its trimetric in the same PR.**
- **Fusion cloud link**: none recorded for any model. Fusion links were not available when this index was made (no Fusion read access in that session); add the link to a row when it is known. Fusion allows 10 editable documents (R74): reuse a part's existing document, never make throwaway ones.

| Model | What it is | Status / rev | Summary page | Local model files | Fusion cloud | Trimetric |
|---|---|---|---|---|---|---|
| Bus bar, design A | Printed ASA body + Al 6061 bars, first design | Superseded by A rev3 (kept for comparison) | [ST185-busbar-designs.html](busbar/ST185-busbar-designs.html) | `cad/busbar/design-A/` (`ST185_busbar_A.f3d`, `A_ASSEMBLY.step`, parts `.step`/`.stl`, `A_drawing.pdf`) | none recorded | <img src="busbar/design-A/trimetric.png" alt="Bus bar A" width="160"> |
| Bus bar, design A rev3 | Design A, third revision | Saved design | same page | `cad/busbar/design-A-rev3/` (`ST185_busbar_A_rev3.f3d`, `A_rev3_ASSEMBLY.step`, ...) | none recorded | <img src="busbar/design-A-rev3/trimetric.png" alt="Bus bar A rev3" width="160"> |
| Bus bar, design B | Printed body, locators, Al bars, first B design | Superseded by B rev2/rev3 | same page | `cad/busbar/design-B/` (`ST185_busbar_B.f3d`, `B_ASSEMBLY.step`, ...) | none recorded | <img src="busbar/design-B/trimetric.png" alt="Bus bar B" width="160"> |
| Bus bar, design B rev2 | Design B, second revision (adds link strap, notch plugs) | Saved design | same page | `cad/busbar/design-B-rev2/` (`ST185_busbar_B_rev2.f3d`, `B_rev2_ASSEMBLY.step`, ...) | none recorded | <img src="busbar/design-B-rev2/trimetric.png" alt="Bus bar B rev2" width="160"> |
| Bus bar, design B rev3 | Design B, third revision | **Dan's pick (E1)** - newest B; the bus bar in the power distribution package | same page | `cad/busbar/design-B-rev3/` (`ST185_busbar_B_rev3.f3d`, `B_rev3_ASSEMBLY.step`, ...) | none recorded | <img src="busbar/design-B-rev3/trimetric.png" alt="Bus bar B rev3" width="160"> |
| VRC enclosure | VR-conditioner box (body, lid, O-ring, LP16 connectors) | Model + drawing done | [ST185-enclosures.html](enclosures/ST185-enclosures.html) | `cad/enclosures/vrc/` (`ST185-VRC-Enclosure.f3d`, `VRC_assembly.step`, `VRC_part_*.step`, drawing PDF) | none recorded | <img src="enclosures/vrc/trimetric.png" alt="VRC enclosure" width="160"> |
| CSB3 enclosure | ECUMaster CSB3 switchboard box (body, lid, HD34 connector) | Model + drawing done | same page | `cad/enclosures/csb3/` (`ST185-CSB3-Enclosure.f3d`, `CSB3_assembly.step`, `CSB3_part_*.step`, drawing PDF) | none recorded | <img src="enclosures/csb3/trimetric.png" alt="CSB3 enclosure" width="160"> |
| DRB102 firewall plate | Firewall mounting plate for the DRB102 | Model done | [DRB102-FIREWALL-PLATE.html](drb102-plate/DRB102-FIREWALL-PLATE.html) (build script `build_DRB102_plate.py` beside it) | `cad/drb102-plate/` (`DRB102-firewall-plate.step`, `DRB102-firewall-plate-assembly.step`; no `.f3d`) | none recorded | <img src="drb102-plate/trimetric.png" alt="DRB102 firewall plate" width="160"> |
| Fuse boxes, rev 2 | ONE glove-box fuse + relay box (R70) | **Superseded by rev 3** (R75); plan page kept | [ST185-fusebox-cad-PLAN.html](fusebox/ST185-fusebox-cad-PLAN.html) | none kept (replaced by rev 3) | none recorded | none (no model kept) |
| Fuse boxes, rev 5 | TWO printed PA12 boxes (power, logic) + battery relay block; each a base (deck on angular legs, open underneath) + snap-on cover (vents, rev 4 etched names) + snap-on belly pan over the live parts underneath; short standoffs where the cable leaves straight; every cable drawn to the box edge; battery block tabs on the short ends (R73, R75, R76, R79, R81) | Current (rev 5; rev 3 / 3.1 / 4 superseded, in the Fusion version history) | [ST185-fusebox-summary.html](fusebox/ST185-fusebox-summary.html) | `cad/fusebox/` (parts lists `fusebox-parts-power.csv` / `-logic.csv` / `-battrelay.csv`, tracked; `ST185_fusebox_rev5.f3d`, `ST185_fusebox_rev5_assembly.step`, `Power_*`, `Logic_*`, `BattRelay_*` `Base` / `Cover` / `Pan` `.step`/`.stl`, copper `.step`) | none recorded (Fusion document `ST185_fusebox_rev5`, Default Project) | <img src="fusebox/trimetric-power.png" alt="POWER box" width="160"> <img src="fusebox/trimetric-logic.png" alt="LOGIC box" width="160"> <img src="fusebox/trimetric-battrelay.png" alt="Battery relay block" width="160"> |
| Billet fuel hanger | In-tank pump hanger in billet 6061, Walbro F90000295; **outside this repo** (Fairsolid run) | **Rev 7 is the newest** (2026-10-14: blind pockets only, bolted-on mounting block); `rev2/` to `rev6/` are earlier passes; no Fusion used (build123d script) | `C:\projects\active\fairsolid\runs\fuel_hanger_billet_1014\rev7\SUMMARY.md` (each rev folder has its own `SUMMARY.md`) | `C:\projects\active\fairsolid\runs\fuel_hanger_billet_1014\rev7\` (`hanger_billet_assembly.step`/`.stl`, per-part files, `hanger_billet.py`) | none (no Fusion document) | <img src="fuel-hanger/trimetric.png" alt="Billet fuel hanger" width="160"> |

## Power distribution package

Always shown together, as one package (DECISIONS R84): the research hub's "Power distribution package" section reads this table and adds up the parts. A member's parts come from its parts list CSV (pieces = `qty_need`) or, with no BOM yet, from the solids in its assembly STEP (`model:<id>` = the entry in `cad/trimetrics.json`), times the number per car.

| Member | Trimetric | Per car | Parts from |
|---|---|---|---|
| POWER fuse + relay box (rev 5) | `fusebox/trimetric-power.png` | 1 | `fusebox/fusebox-parts-power.csv` |
| LOGIC fuse + relay box (rev 5) | `fusebox/trimetric-logic.png` | 1 | `fusebox/fusebox-parts-logic.csv` |
| Battery relay block (rev 5) | `fusebox/trimetric-battrelay.png` | 1 | `fusebox/fusebox-parts-battrelay.csv` |
| Bus bar, design B rev3 (Dan's pick, E1) | `busbar/design-B-rev3/trimetric.png` | 1 | `model:busbar-B-rev3` |
| VRC enclosure | `enclosures/vrc/trimetric.png` | 2 | `model:enclosure-vrc` |
| CSB3 enclosure | `enclosures/csb3/trimetric.png` | 1 | `model:enclosure-csb3` |

**File lists on the research hub's Project status page** come from `cad/model-files.json`, which `python docs/build-research-hub.py` rewrites whenever it is run on a PC that has the model files (commit the refreshed file with the change). The builder warns on the page and on stderr if a model file sits in a folder with no row here, an `.f3d` is not named here, or the hanger row is not the newest `revN` folder.

External rows point at a local path only; that run folder is not in this repo and not in git here.
