# ST185 RealDash `.rd` build package (local Cursor agent edition)

Self-contained handoff for building a real RealDash `.rd` dashboard for the 1993 Toyota Celica
GT-Four ST185 (5S-GTE) "TrackCluster". Hand this whole folder to a **Cursor agent running locally on
a PC that has RealDash installed and a real GPU-backed desktop**. Everything the agent needs is here.

## Quick start (for the local agent)

1. Read `PLAN.md` top to bottom. Start with the Context note and section 0 (prerequisites).
2. Read `FINDINGS.md` — a prior cloud attempt failed *only* because that VM had no GPU; make sure
   this PC uses hardware OpenGL (RealDash must reach the **Garage** screen after login, not a stuck
   spinner).
3. Install tooling per `tools/SETUP.md` (`pip install -r tools/requirements.txt`).
4. Launch RealDash, log in with `CREDENTIALS.md` (local only, gitignored), import the repo-root
   `link_g4x_realdash.xml` (PLAN.md section 3).
5. Build the single-page dashboard exactly per PLAN.md section 4, validate (section 6), export the
   `.rd` (+ `_anim.xml`) and hand it back (section 7).

## Contents

- `PLAN.md` - the full execution plan, updated for a local Cursor agent: prerequisites, PC setup,
  the screenshot->click automation loop, the CAN channel import, the exact tile-by-tile dashboard
  spec (positions, colors, bindings, thresholds), build procedure, validation, delivery, plus an
  appendix of findings. **Start here.** Sections 3 and 4 (the CAN contract and the dashboard spec)
  are the authoritative source of truth and are unchanged from the original package.
- `CREDENTIALS.md` - My RealDash account login (subscription active, 0/3 devices). Requested for
  this handoff; keep private.
- `FINDINGS.md` - why this must run on a GPU-backed PC (the software-OpenGL-ES deadlock diagnosis),
  and everything already ruled out (network, login, subscription, device limit).
- The CAN channel file is the **repo-root** `link_g4x_realdash.xml` (single copy — there is no
  `rd-build/link_g4x_realdash.xml` any more). Import it so the `ST185:`-prefixed inputs exist for
  gauges to bind to (PLAN.md section 3).
- `realdash-simulation-REFERENCE.html` - live HTML/JS preview of the dashboard's look & feel (open in
  any browser). **Visual/style reference only** — it still shows a leftover "CABIN" tile that is NOT
  in the final layout. The authoritative layout is PLAN.md section 4 (no Cabin tile; Trigger Errors
  spans the freed slot).
- `tools/` - desktop-automation tooling for the agent:
  - `automation_helper.py` - PyAutoGUI CLI: screenshot / click / type / key / pixel. This is the
    only tool the agent needs to drive the editor.
  - `requirements.txt` - `pip install -r tools/requirements.txt`.
  - `SETUP.md` - install + per-OS permissions (macOS Accessibility/Screen Recording, Linux
    scrot/tk), verification steps, and an optional remote (VNC) path.
  - `mcp.example.json` - OPTIONAL example only; no MCP server is required.

## Which file is current (declared 2026-10-03; nothing deleted)

| What | Current | Older copies (history only) |
|---|---|---|
| Dashboard `.rd` | repo-root `st185_dash.rd` — the delivered build per `BUILD-NOTES.md` (2026-07-06) | `rd-build/realdash-root/st185_dash.rd` and `st185_dash_v2.rd` … `st185_dash_v10.rd` (intermediate editor saves; v10 is the last numbered save) |
| Simulation / look-and-feel | repo-root `realdash-simulation.html` (no Cabin tile; linked from `REALDASH-LAYOUT.md`) | `rd-build/realdash-simulation-REFERENCE.html` (still shows a Cabin tile) |
| CAN channel file | repo-root `link_g4x_realdash.xml` | none |

**Open item:** `BUILD-NOTES.md` says the root file and `realdash-root/st185_dash.rd` are the same
39,248-byte build, but the committed files differ (root 39,548 bytes; `realdash-root/st185_dash.rd`
99,648 bytes). Confirm which `.rd` is actually on the Pi before building on either. Tracked in
`docs/OPEN-ITEMS.md`.

## Tools / MCP / connectors required

- **Tools:** RealDash (installed on the PC); Python 3 + PyAutoGUI (`tools/requirements.txt`); the
  shipped `tools/automation_helper.py`.
- **MCP servers:** none required.
- **Connectors / remote desktop:** none required (agent + RealDash on the same machine). A remote
  VNC option is documented in `tools/SETUP.md` only for the case where the agent runs on a different
  machine.

## Why this exists

RealDash's `.rd` format is an undocumented proprietary binary; the only way to produce a valid one is
to drive RealDash's own visual editor. This package lets a computer-use-capable Cursor agent do
exactly that on your PC: install/verify RealDash, import the CAN XML, build every tile per the spec,
save, and hand back the finished `.rd` (+ animation sidecar) to copy onto your Raspberry Pi.
