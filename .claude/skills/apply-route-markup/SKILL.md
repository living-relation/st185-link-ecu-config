---
name: apply-route-markup
description: Redraws a route HTML drawing in `_research/routes/` (main checkout only) from Dan's markup on the current isometric figure. Use when Dan hands back a route drawing with blue/black annotations, says "redraw route N", "apply my markup", or "add a top view". Covers reading his markup code, revisioning the old file, redrawing the isometric, adding/updating the matching top view, and running the route lint. Do NOT use to edit `.harness` files, `sot/channels.csv`, or `docs/harness/interfaces.json` — this skill is drawing-only.
paths:
  - _research/routes/**
  - scripts/check_route_drawings.py
---
# apply-route-markup

## Where to run
- The route files live in the main checkout, `C:\projects\active\st185-link-ecu-config\_research\routes\` — `_research/` is untracked and local-only, not present in other worktrees. The lint script lives in this repo at `scripts/check_route_drawings.py` and takes a file or directory path. Shell: PowerShell.

## Critical
- Dan's markup code: a **blue line with no text is a route**; a **blue arrow with a black label shows where a part sits**; a **black box is a plain-text instruction** — apply it literally, don't infer beyond it.
- Never overwrite a route file in place. Before redrawing, copy the current file to the next `-revN` (e.g. `ROUTE-5-A-CABIN-rev3.html` → `-rev4.html`). No rev is ever deleted (`HARNESS-RECONCILE-PLAN.html` §34, "Old versions / KEPT").
- Every isometric route figure needs a top view immediately after it (Dan, binding, `HARNESS-RECONCILE-PLAN.html` §34): same route, same colors; that figure's part bright, the rest faded; numbered markers matching the isometric figure's numbers (a new key if the isometric has none); blue B/R/L markers for the bulkhead and both fender pass-throughs; a FRONT arrow; passenger (RH) / driver (LH) sides labeled.
- Top-view base drawing: the car outline from the 1993 Celica repair manual RM305U1, Introduction, "Vehicle Lift and Support Locations", p. IN-24 (lightened, outline only — drawn from underneath, but the outline is the same from above). Reuse that one outline across every route; don't redraw it by hand each time.
- A route line is a `<polyline>`/`<path>` with `fill="none"` — a red shape without that fill renders as a filled blob, not a line.
- This is a planning/drawing skill only. Do not touch `.harness` files, `sot/channels.csv`, or `docs/harness/interfaces.json` — that is `build-harness-from-sot`'s job, and a parallel session may be mid-change there.

## Instructions
1. Read Dan's markup on the current rev and sort each mark into route / part-location / instruction using the code above.
2. Copy the current `ROUTE-N-*.html` to the next `-revN` before changing anything; keep every prior rev untouched.
3. In the new rev, redraw the isometric: add/update the red `fill="none"` route path(s) for each blue line, add a numbered circle+text marker for each blue-arrow part location, and update the key table below the figure with the new/changed marker numbers.
4. Apply any black-box instruction text as a caption or note at its location — verbatim scope, no invented facts.
5. Add or update the top view immediately after the isometric figure, following the binding rule above (same colors, bright/faded split, B/R/L + FRONT + side labels, RM305U1 p.IN-24 outline).
6. Run the route lint and report only the path it ran against:
   `python scripts/check_route_drawings.py "C:\projects\active\st185-link-ecu-config\_research\routes\ROUTE-N-....html"`
7. Stop here — hand the approved route off to `build-harness-from-sot` for the actual `.harness` edit.

## Verification
- The lint in step 6 exits 0, or every reported issue is one you intend to leave (for example, an older rev that predates the top-view rule, which you did not touch).
- `git status` in the main checkout shows only the new `-revN` file added — no prior rev deleted or modified, and nothing under `docs/harness/`, `sot/`, or `interfaces.json` touched.
