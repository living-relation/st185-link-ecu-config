# 5sgte Project Data — copied from the claude.ai Project

This folder is a copy of the docs and files held in the claude.ai Project **"5sgte Project
Data"** (turbo selection, boost control, ECU tuning, E85 tuning research for this build), copied
into this repo on 2026-09-04 at Dan's request so the research lives alongside the ECU/CAN work
in one place. `docs/` mirrors the Project's "docs" list; `files/` mirrors its "files" list
(images and PDFs).

## Scope and honesty notes

- **This is a snapshot, not a live sync.** The claude.ai Project is still the place new research
  gets added day to day. If you update something there, it will drift from this copy until
  someone re-copies it. Nothing here auto-updates.
- **The three PDFs are text-only copies**, not the original PDF files. The tool used to pull
  Project files into this repo only returns extracted text for PDF/document uploads (not the
  original bytes), so `files/*.extracted-text.md` are text transcriptions — figures, QR codes,
  and the laminate card's visual layout from the originals are not reproduced. The real PDFs
  remain in the claude.ai Project's file uploads.
- **The 15 `.png` charts and the 14 CSVs/`.py` model came across as exact original bytes** — true
  copies, not transcriptions.
- **Some of these docs contain superseded conclusions, kept as-is for history.** In particular:
  - `ECU_WIRING_MASTER_SOURCE_OF_TRUTH.md`, `Reverse_Camera_Trigger_CORRECTED_sourced_from_repos.md`,
    and `ECU-mermaid-chart.md` all describe an earlier "reverse switch → ECU DI4 direct" decision
    (2026-08-19). That has since been reversed back to switchboard routing — see
    `REVERSE-CAMERA-TRIGGER-RESOLUTION.md` in this same folder, and the root-level
    `XTREMEX-IO-TABLE.html` / `CAN-CONFIG-STATUS.md`, which are current.
  - Several docs here still say "3S-GTE" or describe cable-throttle; per the
    `ECU-wiring-design` branch's `DOCS-CLEANUP-PLAN.md`, the engine is actually a 5S-GTE hybrid
    and the car is drive-by-wire (Bosch ETB + BRZ pedal), not cable throttle. That reconciliation
    is a separate, larger, not-yet-approved effort — this folder is not the place it gets fixed.
  - `06_turbo_model.py` and its downstream CSVs use `DISPLACEMENT_CC = 2164` / `CID = 132.06`,
    while other docs here cite `2188.8cc` for the same hybrid build (87.5mm bore × 91.0mm
    stroke). Both are in the source material as received — not reconciled here.
- **Do not treat every number in this folder as current or mutually consistent.** These are
  research artifacts from several different working sessions, not a single audited spec. Where
  this folder disagrees with the root-level, actively-maintained docs (`XTREMEX-IO-TABLE.html`,
  `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-CONFIG-STATUS.md`), the root-level docs win.

## Contents

`docs/` — research reports, decision logs, boost/duty/shakedown tables (CSV), and the turbo
comparison model (`06_turbo_model.py`) used to generate the project's charts.

`files/` — compressor maps, boost/power charts, tuning-plan images, and the three timing-belt/
cam-degreeing PDFs (as extracted text, see above).
