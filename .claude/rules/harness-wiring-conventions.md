# Harness Wiring Conventions - pointer only

**Every wiring rule Daniel has set lives in one place: `docs/harness/redesign/DECISIONS.md`,
section "Binding rules from Daniel" (R1-R122).** Read it before any wiring, harness, shield,
parts or drawing change. This file deliberately restates nothing, so it cannot drift.

- The reconcile procedure (source-of-truth chain, every wiring surface that must agree, Rule 3
  detail): `docs/RECONCILIATION-RULES.md` Rules 1 and 3.
- Shield inventory and build detail: `docs/SHIELD-RULES.md`.
- Which file is which harness, the desktop-app workflow and the gate pipeline:
  `docs/harness/README.md`.
- `python docs/harness/check_all.py` must pass before every commit.
