# ST185 RealDash `.rd` build package (local Cursor agent edition)

Self-contained handoff for building a real RealDash `.rd` dashboard for the 1993 Toyota Celica
GT-Four ST185 (3S-GTE) "TrackCluster". Hand this whole folder to a **Cursor agent running locally on
a PC that has RealDash installed and a real GPU-backed desktop**. Everything the agent needs is here.

## Quick start (for the local agent)

1. Read `PLAN.md` top to bottom. Start with the Context note and section 0 (prerequisites).
2. Read `FINDINGS.md` — a prior cloud attempt failed *only* because that VM had no GPU; make sure
   this PC uses hardware OpenGL (RealDash must reach the **Garage** screen after login, not a stuck
   spinner).
3. Install tooling per `tools/SETUP.md` (`pip install -r tools/requirements.txt`).
4. Launch RealDash, log in with `CREDENTIALS.md`, import `link_g4x_realdash.xml` (PLAN.md section 3).
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
- `link_g4x_realdash.xml` - RealDash CAN v2 channel-description file. Import it so the `ST185:`-prefixed
  inputs exist for gauges to bind to (also embedded inline in PLAN.md section 3).
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
