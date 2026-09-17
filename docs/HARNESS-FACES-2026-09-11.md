# Harness faces - 2026-09-11 (updated 2026-09-12)

One harness, two faces. Do not crown one and burn the other.

## Faces
| Face | Where | Job | Score today |
|------|-------|-----|-------------|
| Loom / read | Claude artifact + `apps\harness-schematic\` | Trace nets, layers, pin story | Readable; as cut/crimp sheet **4/10** (no AWG/length/terminate-at/checkbox) |
| SoT / BOM | `docs\harness\ST185-Power.harness` + `ST185-Signal.harness` | Connector PNs, cavities, splices | Structure OK; as finished build pack **5/10** (half unwired; 0 cavity crimps; bulkheads carry no wires) |

## Rules
- Crown **shipping** copies as ACTIVE (Desktop HTML hashes differ).
- Colour SoT: `XTREMEX-IO-TABLE.html` + XtremeX Quickstart (not stale Desktop diagram).
- OEM body connections (relays, bulkheads, clutch, cruise stalk, brake, reverse, start, ignition switch) are generic **blocks** — do not invent OEM pinouts. Exception: Subaru BRZ APS is a real 6-pin TS 025.
- Band 3 / CSB3 stays dashed until real I/O connector exists.
- Next spell: generate `HARNESS-BUILD-LIST` from schematic graph (From/To/colour/AWG/terminate-at/splice/done).
- Layout/consolidation proposal: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md`.

## 2026-09-12 — the `.harness` pair now lives in this repo
The desktop `.harness` files were split into a power half and a signal half and
were only in `Downloads`. Both are now tracked here:

- `docs/harness/ST185-Power.harness`
- `docs/harness/ST185-Signal.harness`

They were audited, corrected and both views rebuilt — see
`docs/ECU-IO-AUDIT-2026-09-12.md` for what changed. Headline: 15 cavities on the
power file carried the relay term `30 (+12V)` while wired to Gnd Out or 5 V, the
flex sensor was on the +8 V rail instead of 12 V, and both layout views had the
34- and 37-way connectors stacked on top of each other on a 90 px pitch.

Edit these in place from now on. Open at app.harness.design, and save back over
the repo copy rather than into `Downloads`, so the tracked file stays the SoT.

## Sources
- Grimoire compare (Grim Council 2026-09-11)
- Claude app: https://claude.ai/public/artifacts/62e39e19-dcdd-41cf-bf4c-9bbc91bb8c1d
- Original desktop copy: `Documents\Wire Harnesses\ST185 Link G4X XtremeX - ECU Harness.harness`
