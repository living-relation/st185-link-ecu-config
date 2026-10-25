# Surgical rewire - cut-list work files

Working files for `docs/OPEN-ITEMS.md` row 164 (B1, B5, B9). They record what Dan decided and how; they are **not** a
wiring source. The master `../MASTER-wirelist.csv` stays the only wiring truth, and each decision here becomes master
rows (st185-change-sot) after cut-list groups 4-8. Current lists: `../README.md` "What stays and what goes".

## Status (2026-10-25)

| Group | Joint | Status |
|---|---|---|
| 1 | EB1 Engine <-> Cowl (rear of RH fender) | Decided 2026-10-20: dead; J/B No.1 fed from POWER JB1 60 A spliced to a 6 in stub of the old 1I lead |
| 2 | ET1 ER Main <-> Engine (near J/B2) | Decided 2026-10-20 |
| 3 | IG1 / IG2 Engine <-> Cowl (under the ECU) | Decided 2026-10-21: `group3-IG1-IG2.md` |
| Boxes | the 7 OEM boxes + ABS relay box | Decided 2026-10-21: J/B1, J/B3, R/B2, R/B4 stay; J/B2, R/B3, R/B5, ABS relay box go |
| 4-8 | IH1, EB2 / ES2, box plugs, removed parts, ER Main branches | Next; start from `cut-list-draft-2026-10-20.md` |

## Files

| File | What it is |
|---|---|
| `circuit-plan.md` | the circuits decided by complete circuit (starter, clutch, reverse, charge lamp, hold power, rear lights, fuse box) |
| `group3-IG1-IG2.md` | every IG1 / IG2 wire: pin, colour, both ends, 1993 EWD page, action |
| `cut-list-draft-2026-10-20.md` | the first 8-group draft (working draft for groups 4-8; its read-first note lists what changed) |
| `dan_routes_p36.json`, `front_loads_p36.json`, `gb_boxes_p42.json` | route polylines and spots in FSM page points (p.36 engine bay, p.42 dash), for the route overlays; the low end of `gb_boxes_p42.json` is the old floor spot: the boxes now sit in the glove box area (Dan 2026-10-25) |

The route drawings Dan approved are in `../routes/` (Routes 16, 17); the cut-list page and chat images were deleted 2026-10-25 (git history).
