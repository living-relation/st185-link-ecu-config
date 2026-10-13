# Enclosure BOMs

CSV sources of truth for the two enclosure families sealed in
`docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` (6.30 / 6.35 / 6.37 pins / 6.40 connector).

| Box | Plan | CSV |
|---|---|---|
| VR conditioner (x2 identical) | 6.30 / 6.35 | [vr-conditioner-bom.csv](vr-conditioner-bom.csv) |
| CSB3 | 6.37 pin map + 6.40 HD30 | [csb3-bom.csv](csb3-bom.csv) |

Both boxes are Hammond 1590WYFL (natural diecast Al, 92x92x42 mm, 122.2 mm outside mounting flange, liquid resistant with silicone gasket). Drawing: [hammond-1590WYFL.pdf](hammond-1590WYFL.pdf) (Hammond's single drawing covers both 1590YFL and the liquid-resistant 1590WYFL; same box and flange).

## Rules

- Edit the CSV only. Pretty tables are regenerated from it.
- Prefer DigiKey / Mouser stock links with the current listing URL (not a stale product-ID suffix); put manufacturer STEP ZIPs in `cad_url` when published, otherwise leave empty or `N/A`. Record live-check notes in `stock_note` — do not freeze snapshot quantities.
- Wire and cable stay generic per plan 6.24 — not listed here.
- Do not undo loom / rebuild work on other paths; this folder is enclosure buy lists only.

## Build notes (carry into the CSV `notes` column when they change)

- VR: two CNLINKO LP-16 rear-nut panel sockets (IN + OUT, `LP-16-C05SX-02-101`, DECISIONS S16), D cutout 18.5 mm / 16.5 mm across the flat. Nothing bonds to the case (DECISIONS R31 / R33), so there is no landing to mask.
- VR: PCB on nylon standoffs; screens go by pin and join inside the box by wire, nothing bonds to the case (6.30, R31 / R33).
- CSB3: on-board 120 ohm terminator jumper stays OPEN.
- CSB3: signal wire to this box is 20 AWG minimum (HD30 size-20 contacts).

## Shelf
- Map: `C:\projects\docs\project-structure.md` (Enclosure BOMs 2026-09-21).
- Branch `docs/enclosure-bom-vr-csb3` merged to main via PR #23 (25c25b6); CSVs live here: [vr-conditioner-bom.csv](vr-conditioner-bom.csv), [csb3-bom.csv](csb3-bom.csv). Do not hand-edit two HTML faces — regenerate from these CSVs.
