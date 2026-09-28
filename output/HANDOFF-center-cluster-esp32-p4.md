# Handoff — center-cluster-esp32-p4

**Date:** 2026-09-27
**Repo:** github.com/living-relation/center-cluster-esp32-p4
**State:** Clean working tree, `main` at `8253282`, up to date with `origin/main`. No local changes.

---

## Context from this session

A technical debt analysis was completed on the sibling repo `st185-link-ecu-config`. One finding crosses the boundary into this repo.

---

## Cross-repo open item

**CAN termination mismatch:** The 5-node ST185 CAN bus (1 Mbit/s) has a documented disagreement about where the bus terminates:

- `st185-link-ecu-config` physical wiring (`WIRING.md` §7.3 and `CAN-BUS-MASTER-DESIGN.md`) puts **END B** at the Raspberry Pi (RealDash listener).
- The actual termination per commit `2adefae` is at the **ECU** and the **CAN-Lambda** module — not the Pi.

This is a physical-layer issue, not a firmware framing issue. Resolving it may require:

1. **Checking `main/canbus.c`** — verify the TWAI termination resistor configuration matches the physical termination placement decided for the 5-node bus.
2. **Updating `CANBUS-ENCODE-DECODE-REFERENCE.html`** — unlikely to need changes for a termination-only fix, but flag it if any framing documentation references termination placement.

The cluster firmware is **frozen** — no code changes are expected or needed for any of the tech debt cleanup items on the ECU config side. All cleanup is confined to `st185-link-ecu-config`.

---

## No action required now

This handoff is informational so the next agent working on the cluster repo knows the context. The termination item is documented but not urgent — the bus works with the current configuration; it's a documentation/wiring-convention mismatch, not a functional failure.
