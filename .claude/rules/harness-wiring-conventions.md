---
paths:
  - XTREMEX-IO-TABLE.html
  - SCHEMATIC-WIRING.html
  - apps/harness-schematic/**
  - docs/harness/*.harness
  - docs/HARNESS-*.md
  - docs/ECU-IO-AUDIT-*.md
  - docs/XTREMEX-IO-VERIFY-*.md
---

# Harness Wiring Conventions

- OEM body/engine-bay connections (relays, clutch, cruise stalk, brake, reverse, start, ignition switch, AC amplifier) are generic **blocks** — draw only the wires this harness lands; do not invent OEM internal pinouts. Bulkheads are the exception: see below.
- Give real pinouts only to parts this build controls: Link Superseal A/B/comms, aftermarket sensors we specify, and the Subaru BRZ e-throttle pedal (6-pin Sumitomo TS 025 — not a 4-pin APS/MP150).
- BRZ pedal: pins 1/2/4/5 (VC1/VC2/GND1/GND2) are power, live in `ST185-Power.harness`; pins 3/6 (VPA2/VPA1) are signal, live in `ST185-Signal.harness` at An Volt 5 (B33) / An Volt 4 (A14).
- Ignition Switch is a dummy OEM block feeding **DI 9 (B28)** for ECU Hold Power (PCLink Ignition Switch function, paired with the Aux 6 relay hold).
- Bulkheads are **real connectors**, not OEM blocks (Daniel, 2026-09-12): one circular MIL connector per Superseal loom, wired straight through. Loom A = Souriau `8STA0-14-35SN` firewall receptacle to `8STA6-14-35PN` engine plug; Loom B = `8STA0-14-35SA` to `8STA6-14-35PA`. Shell 14 arrangement 35 = 37 contacts #22D; keyway N on A and A on B so the two looms cannot be cross-mated. Cavities are numbered straight through in wire order — no signal grouping — and unused cavities are marked `spare`.
- Every wire crossing the firewall terminates in a bulkhead cavity: it is two wires (`<id>_c` cabin side, `<id>_e` engine side), not one wire passing through.
- `XTREMEX-IO-TABLE.html` is the living pin source of truth. `docs/XTREMEX-IO-VERIFY-2026-09-11.md`, `docs/ECU-IO-AUDIT-2026-09-12.md`, and `docs/HARNESS-FACES-2026-09-11.md` are frozen dated records — add new pin facts to the table first, then propagate to the schematic app and `.harness` files.
- See `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` for the full consolidation/layout plan and column-order convention.
