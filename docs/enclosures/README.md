# Enclosure BOMs

CSV sources of truth for the two enclosure families sealed in
`docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` (6.30 / 6.35 / 6.37 pins / 6.40 connector).

| Box | Plan | CSV |
|---|---|---|
| VR conditioner (x2 identical) | 6.30 / 6.35 | [vr-conditioner-bom.csv](vr-conditioner-bom.csv) |
| CSB3 | 6.37 pin map + 6.40 HD30 | [csb3-bom.csv](csb3-bom.csv) |

Both boxes are **custom machined 6061-T6** (adopted by Dispatch 2026-10-14, DECISIONS S32; replaces the Hammond 1590WYFL / 1590WUFL): body + lid with an AS568-039 NBR O-ring face seal, 4x ISO 10642 M3 x 12 countersunk lid screws, slotted tabs for M6 nylon screws. VRC box 90 x 50 x 45 mm (74 across the tabs), CSB3 box 70 x 70 x 56 mm (94 across the tabs). Drawings and summary: [`cad/enclosures/`](../../cad/enclosures/) (`ST185-enclosures.html`, `vrc/` and `csb3/` drawing PDFs). Still open: inside vs outside face for the VRC D30 counterbores (OPEN-ITEMS row 114), the LP-16 rear nut size (row 98), the M6 tab screw and the printed board holder model (row 97). [hammond-1590WYFL.pdf](hammond-1590WYFL.pdf) is kept as the size comparison only.

## Rules

- Edit the CSV only. Pretty tables are regenerated from it.
- Prefer DigiKey / Mouser stock links with the current listing URL (not a stale product-ID suffix); put manufacturer STEP ZIPs in `cad_url` when published, otherwise leave empty or `N/A`. Record live-check notes in `stock_note` — do not freeze snapshot quantities.
- Wire and cable stay generic per plan 6.24 — not listed here.
- Do not undo loom / rebuild work on other paths; this folder is enclosure buy lists only.

## Build notes (carry into the CSV `notes` column when they change)

- VR: two CNLINKO LP-16 rear-nut panel sockets (IN + OUT, `LP-16-C05SX-02-101`, DECISIONS S16), D cutout 18.5 mm / 16.5 mm across the flat. Nothing bonds to the case (DECISIONS R31 / R33), so there is no landing to mask.
- VR: the module sits in a 3D-printed holder on the box floor (DECISIONS S26 E1: no carrier board, no standoffs); screens go by pin and join inside the box by wire, nothing bonds to the case (6.30, R31 / R33).
- VR: IN / OUT are engraved on the box ends; the leads carry printed VRC-IN / VRC-OUT heat-shrink labels and a blue (IN) / yellow (OUT) band (DECISIONS S30).
- Both: the box mounts on nylon (M6 nylon tab screws), clear anodize is fine, keep the O-ring groove and seal faces uncoated or anodize-only.
- CSB3: on-board 120 ohm terminator jumper stays OPEN.
- CSB3: signal wire to this box is 20 AWG minimum (HD30 size-20 contacts).

## Shelf
- Map: `C:\projects\docs\project-structure.md` (Enclosure BOMs 2026-09-21).
- Branch `docs/enclosure-bom-vr-csb3` merged to main via PR #23 (25c25b6); CSVs live here: [vr-conditioner-bom.csv](vr-conditioner-bom.csv), [csb3-bom.csv](csb3-bom.csv). Do not hand-edit two HTML faces — regenerate from these CSVs.

## CAD

Custom VRC and CSB3 enclosure CAD (drawings, renders, plan notes) is in the repo CAD tree: [`cad/enclosures/`](../../cad/enclosures/). The model files (Fusion `.f3d`, every STEP) are gitignored and kept only in the main checkout, in the same folder (DECISIONS R67).
