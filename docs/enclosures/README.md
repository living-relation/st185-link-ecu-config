# Enclosure BOMs

CSV sources of truth for the two enclosure families sealed in
`docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` (6.30 / 6.35 / 6.37 pins / 6.40 connector).

| Box | Plan | CSV |
|---|---|---|
| VR conditioner (x2 identical) | 6.30 / 6.35 | [vr-conditioner-bom.csv](vr-conditioner-bom.csv) |
| CSB3 | 6.37 pin map + 6.40 HD30 | [csb3-bom.csv](csb3-bom.csv) |

## Rules

- Edit the CSV only. Pretty tables are regenerated from it.
- Prefer DigiKey / Mouser stock links; free STEP when the manufacturer or DigiKey publishes one; otherwise leave `cad_url` empty or `N/A`.
- Wire and cable stay generic per plan 6.24 — not listed here.
- Do not undo loom / rebuild work on other paths; this folder is enclosure buy lists only.

## Build notes (carry into the CSV `notes` column when they change)

- VR: mask the three M8 landings before any powder coat — coating breaks the shield path.
- VR: PCB on nylon standoffs; shell carries the screen (6.30).
- CSB3: on-board 120 ohm terminator jumper stays OPEN.
- CSB3: signal wire to this box is 20 AWG minimum (HD30 size-20 contacts).
