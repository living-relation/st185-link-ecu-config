# Retired by the 2026-09-27 harness redesign

Moved here, not deleted, after their replacements passed. Nothing here is authoritative.

| File | Why it was retired | Replaced by |
|---|---|---|
| `verify_rebuild.py` + `legacy-prebuild/` | Diffed every conductor against the frozen pre-split baseline, so the redesign's intentional ownership and boundary moves read as losses. | `docs/harness/verify_connectivity.py` (every SoT signal pin traced to a device across all boundaries) plus `validate_ownership.py` / `validate_interfaces.py`. |
| `fix_cable_parts.py` | Silently rewrote every loom's cable parts with hardcoded 1/2/4-core classes; the redesign models its cables explicitly. | Cable parts are set in the drawings; `lint_v09.py` checks core counts and screens. |
| `layout_633.py` | Mutated layout using a hardcoded nine-loom zone table with VRC connector ids that no longer exist. | Layout is edited per harness in harness.design. |

Decision record: `docs/harness/redesign/DECISIONS.md`.
