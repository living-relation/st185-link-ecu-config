# Reverse Camera Trigger — Resolution (updated 2026-09-04, Rev 3)

**This replaces the 2026-08-24 version of this doc.** That version adopted the 2026-08-19
DI4-direct decision from `ECU_WIRING_MASTER_SOURCE_OF_TRUTH.md`. This update reverses that,
per Dan's instruction to treat the `ECU-wiring-design` GitHub branch as authoritative for ECU I/O.

## Current answer (authoritative)

Reverse switch → **ECUMaster CAN switchboard** → CAN → ECU. Not an ECU digital input.
A PCLink **Trigger** (confirmed by Dan) sets Gear Position = 7 on CAN 0x3EB when active.
Source: `ECU-wiring-design` branch, `XTREMEX-IO-TABLE.html` + `DOCS-CLEANUP-PLAN.md`
(2026-08-31, conflict C16) — which explicitly reverses the 2026-08-19 DI4-direct decision.
Reasoning: on/off switches go to the switchboard so the ECU's digital inputs stay free for
frequency signals (turbo speed, 4x ABS wheel speed). Checked directly: DI 4 is committed to
an ABS wheel-speed sensor on that branch, not spare — DI4-direct would have collided with it.

## What changed since the last version of this doc

1. Found and read the `ECU-wiring-design` branch (Dan: "I've started building an interactive
   wiring diagram app... trying to keep [the repo] the central source of truth"). It contains
   `DOCS-CLEANUP-PLAN.md`, a 762-line reconciliation across 55 documents in 5 locations, with
   27 numbered conflicts (C1-C27) and Section 7 naming `XTREMEX-IO-TABLE.html` and
   `SCHEMATIC-WIRING.html` as the single sources of truth for ECU I/O and wiring.
2. Grepped that branch's `XTREMEX-IO-TABLE.html` directly (not summaries) to confirm: reverse
   switch is "SB → CAN → ECU" — same as GitHub main's original design, which the 2026-08-19
   project doc had overridden. Main and the branch agree with each other on this point.
3. Dan confirmed the PCLink mechanism is a **Trigger** (not Virtual Aux, not a generic
   "condition" — earlier drafts guessed wrong).
4. Dan confirmed the RealDash camera page/trigger build is deferred — this was a planning
   session only.

## The RealDash gap — fix drafted, not yet pushed

`link_g4x_realdash.xml`'s header deliberately excludes CAN frames 0x3E8-0x3EE (gear included)
because the center cluster already displays them. That's the one real gap for a RealDash-based
camera trigger. Fix: a new, minimal `<frame id="1003">` (0x3EB) exposing only the Gear byte as
`ST185: Gear` — Fuel Level left out to keep the carve-out to exactly what's needed.

This is **committed to a local clone of `main`** (commit `1c2261c`), along with matching updates
to `CAN-CONFIG-STATUS.md`, `.claude/rules/realdash-xml-conventions.md`, and a small wording
clarification in `XTREMEX-IO-TABLE.html` ("Trigger" instead of unspecified "tune function").
**Not pushed to GitHub** — this session has no GitHub write access (no connector installed for
this workspace; the sandbox's git-credential proxy reports the repo isn't in its authorized set).
A patch file and exact git commands were given to Dan directly in-chat to apply himself.

## Still open

- Push access: needs either a GitHub connector added to this workspace, or Dan applies the
  patch himself.
- Exact PCLink Trigger name/threshold — not yet screenshotted from PCLink itself.
- DI 1-2, 7-8 and the DI3-6 ABS-wheel-speed assignment are still marked "proposed" in the
  branch's cleanup plan (its own open-question #8) — unrelated to this fix, not resolved here.
- The much larger `DOCS-CLEANUP-PLAN.md` consolidation (55 docs, 27 conflicts, merging
  `ECU-wiring-design` into `main`, fixing 3S-GTE→5S-GTE and FuryX→XtremeX everywhere, etc.) is
  explicitly marked "PLAN ONLY — approve before any change" and is out of scope for this fix.

## Artifact

Interactive signal-path reference (Rev 3, corrected back to switchboard):
https://claude.ai/code/artifact/1eae0532-029e-4548-b38f-812fbdd14ba6
