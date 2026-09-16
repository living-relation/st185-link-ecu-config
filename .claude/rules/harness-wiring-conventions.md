# Harness Wiring Conventions

**Canonical text: `docs/RECONCILIATION-RULES.md` Rule 1. Read it before finalizing any wiring
change.** This file is a pointer plus the facts most often got wrong — it is deliberately not
a second copy, so the two cannot drift apart.

## The rule

A change to one wiring document is not done until it is checked against the source-of-truth
chain **and every other wiring surface**, including the ones you did not edit. They must all
agree.

## Source of truth

`XTREMEX-IO-TABLE.html` → `SCHEMATIC-WIRING.html` + `apps/harness-schematic/` →
`docs/harness/*.harness` → harness.design app copy (mirror only).

New pin facts go into the table first. If a downstream face disagrees, the face is wrong.

## Facts that are commonly stale

- **Two bulkheads only**, A and B, HDP20 from owned stock: A is `HDP24-24-47PE-L017` /
  `HDP26-24-47SE-L015`, B is `HDP24-24-21PN` / `HDP26-24-21SN`. Bulkhead C is deleted. The
  Souriau 8STA 37-way design is superseded — do not reintroduce it.
- **Every ECU pin is Signal by default.** Exceptions to Power: the 12V ignition supply with
  its hold wiring, and all relay trigger outputs.
- **All pedal pins are Signal**, supplies included. This reverses the older rule that put
  pins 1/2/4/5 in Power.
- **All ETB pins are Signal**, motor pair included. **All 5V sensor power is Signal.**
- **Harness C is the Engine Room Harness** — no bulkhead, exits the driver fender around the
  front of the bay.
- **Shields** terminate at the ECU only. Model a shielded run as a cable whose `shield` core
  has a `source` and no `target`. Device-end connectors carry no shell.

Full build rules: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.
