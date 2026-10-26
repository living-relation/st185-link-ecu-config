# Harness Wiring Conventions - pointer only

**Every wiring rule Daniel has set lives in one place: `docs/harness/redesign/DECISIONS.md`,
section "Binding rules B1-B30"; old R-numbers resolve through its retire map.** Read it before any wiring, harness, shield,
parts or drawing change. This file deliberately restates nothing, so it cannot drift.

- The reconcile procedure (source-of-truth chain, every wiring surface that must agree, Rule 3
  detail): `docs/harness/redesign/DECISIONS.md` Rules 1 and 3.
- Shield inventory and build detail: `docs/harness/redesign/DECISIONS.md`.
- What is in `docs/harness/` and how to change the wiring: `docs/harness/README.md`.
- The ONE wiring source of truth: `docs/harness/MASTER-wirelist.csv` (R221); `python tools/check_all.py` must pass before every commit.
