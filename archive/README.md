# archive/

Retired material. **Nothing here is authoritative.** Each entry is kept only so a
past decision can be re-read if the question comes up again, with a one-line note
saying why it was retired — the convention set out in `DOCS-CLEANUP-PLAN.md` §7.

Rule: if a file here disagrees with a current document, the current document wins.
Files are retired here rather than deleted; deletion is reserved for material that
is both wrong and duplicated elsewhere.

## Contents

| File | Retired | Why |
|---|---|---|
| `ALARM_MAPPING_POLICY.md` | 2026-09-05 | Temporary `0x3EE` alarm-mapping rule used while designing the cluster layouts ("never duplicate gauge-shown conditions as alarm bytes"). No ECU meaning. Byte layout lives in `CAN-BUS-ID-ALLOCATION-TABLE.md`. |

## Lost, not archived

Recorded so a future search does not waste time looking. These came from the
sibling repo `st185-furyx-base-map`, which had **no git remote** and was deleted
2026-09-05 after its engine data was imported into `tune/`. They were never
committed to this repo, so they are **not** recoverable from this history:

| File | What it was | Why it was dropped |
|---|---|---|
| `config/io_assignments.yaml` | Full FuryX channel map | Contradicted `XTREMEX-IO-TABLE.html` on ~10 channels; declared an onboard LSU 4.9 the XtremeX does not have (conflicts C19, C26) |
| `docs/references/FuryXQuickstartGuide.pdf` | Link FuryX quickstart | Wrong ECU (conflict C2) |
| `docs/references/linkecu-furyx-dealer.html` | Dealer page scrape | Wrong ECU |
| `docs/references/FURYX_QUICKSTART_NOTES.md` | FuryX pinout notes | Same wrong An Volt / ETB / onboard-wideband map as `io_assignments.yaml` |
| `docs/SENSOR_WIRING.md`, `docs/IO_BUDGET.md`, `docs/PWM_OUTPUTS.md` | FuryX I/O allocation docs | I/O domain — superseded by `XTREMEX-IO-TABLE.html` |
| `docs/AGENT_GUIDE.md`, `docs/AGENT_SESSION_CONTEXT.md`, `docs/ECU_SESSION_CHECKPOINT.md`, `docs/ECU_PACKAGE_README.md` | Handoff notes for the old repo's own workflow | Repo-meta, not engine data |
| `scripts/package_ecu.ps1` | Zip packager for the standalone FuryX bundle | Redundant once the content lived in a repo with a remote |

Everything engine-side from that repo **was** imported and is live under `tune/`.

## Recovering something retired here

Files in this folder are readable as-is. For anything removed from the repo in a
past commit, git still has it:

```bash
git log --oneline --all -- <path>      # find the commit that last had it
git show <commit>:<path>               # print it
```
