# Handoff — st185-link-ecu-config

**Date:** 2026-09-27
**Repo:** github.com/living-relation/st185-link-ecu-config
**State:** Clean working tree, `main` at `4e782d9`, up to date with `origin/main`.

---

## Done this session

1. Fetched GitHub changes — repo was already up to date (`b265f1d`), no pull needed.
2. Completed a full technical debt analysis. PDF saved at `output/TECHNICAL-DEBT-CLEANUP-PLAN.pdf`.
3. Removed the "Handoffs are never committed" section from both `CLAUDE.md` and `AGENTS.md` in a single commit (`4e782d9`). The generated-files ownership table that followed it is preserved. Pushed to `origin/main`.

---

## Open items from the tech debt plan (prioritized)

### Phase 1: Quick wins (~1 hr)
- `git rm -r --cached` the tracked `__pycache__` dirs in `bench/`, `apps/trackcluster-can-sender/`, and `docs/harness/`
- Delete 9 versioned `st185_dash_v*.rd` files from `rd-build/realdash-root/`
- Fix stale `canbus-live-sender` references in `.gitignore` and `rd-build/PLAN.md`
- Add `pyproject.toml` with ruff + mypy config
- Add `.github/dependabot.yml`

### Phase 2: CI & tests (~4–8 hrs)
- Add `.github/workflows/ci.yml` with ruff + `py_compile` on every push/PR
- Create `tests/test_frames.py` with round-trip encode/decode tests for `bench/frames.py`
- Create `tests/test_can_contract.py` validating `frames.py` ↔ `link_g4x_can_setup.json` parity
- Add `docs/harness/check_all.py` to CI

### Phase 3: Documentation cleanup (~2–4 hrs)
- Convert `CAN-CONFIG-STATUS.md` from handoff note to permanent reference, or delete and merge facts into canonical docs
- De-duplicate `CLAUDE.md`/`AGENTS.md` shared sections (~50% overlap remains after the handoffs rule removal)
- Review/archive `rd-build/tools/` one-off scripts
- Remove stale board reference from `AGENTS.md`

### Phase 4: Modernization (~4–8 hrs)
- Add `ruff format` to CI and format all Python files
- Fix type hint inconsistencies in `frames.py` and `can_bench.py`
- Generate pinned dependency lock files
- Reconcile Python version mismatch (CI 3.12 vs local 3.14)

---

## Cross-repo open item

**CAN termination mismatch:** ST185-CAN terminates at the ECU and the CAN-Lambda, but `WIRING.md` §7.3 and the master design put END B at the Pi. Recorded as an open item in commit `2adefae` but not yet resolved. This crosses into `center-cluster-esp32-p4` territory.

---

## Uncommitted local changes

- `.cursor/settings.json` — IDE settings file, not project content
- `output/` — this session's output directory (tech debt PDF + handoffs)
