# Gropus continuation plan — harness wiring (orientation pass)

**Read-only handoff, 2026-10-22.** This note does NOT change any wiring data. It records where the
surgical-rewire work stands, what Daniel's two latest chat answers change, the stale/conflicting
items found, the ordered next steps, and the open questions. The real owners of every fact are
`docs/OPEN-ITEMS.md` (tracker, row 164) and `docs/harness/redesign/DECISIONS.md` (rules B1-B30). When
Daniel confirms the two answers below, fold them into those files and delete this note (B3: one home
per fact; git history is the archive).

---

## 1. Where things stand

**Project focus (B1):** G1 wiring → G2 base maps → G3 CAN config → G4 CSB3. Only G1 (wiring) is the
active front. A freeze (B2) blocks new rules/scripts/docs/features until the bloat cut finishes.

**The plan = a surgical rewire (B1, B5, B7, B9, B11; Dan 2026-10-20/21):**
- **Keep** the OEM cabin/body wiring, cabin J/B No.1 and No.3, and the outer engine-room loop as
  6-inch pigtails only. Both A/C amps stay.
- **Replace** everything forward of the firewall with new wire on named routes (Route 16 engine lines
  1-9, Route 17 front lines 10-13).
- **Remove** every other OEM relay/fuse box (J/B No.2, R/B No.2-5, ABS relay box), the Engine Wire,
  the OEM ECU/igniter, SRS and ABS computers. Dead OEM wire comes out back to its last live point
  (not cut-and-capped).
- Custom glove-box POWER/LOGIC fuse boxes fill the gaps only.

**Done so far (merged to main):**
- Bloat cut: rules on one page B1-B30 (#377, #384); each rule trimmed to 2 lines (#385); dead scripts
  deleted (#380, partly restored #381); `rebuild/` deleted, ONE drawing set `ST185-harness` with a
  wire-by-wire read-back check in `build_drawings.py --check` (#372 + bloat steps 2-3).
- Surgical-rewire rules written (#385) and the kept/removed list in `docs/harness/README.md`.
- Route 16 (engine main, 9 lines) and Route 17 (front, 23 devices) drawn (#389, #392); B9 rewritten
  to "forward of the firewall every wire is new" (#392).
- Firewall cut list: **groups 1 (EB1) and 2 (ET1) decided** in row 164. Group 3 (IG1/IG2) is marked
  "next" — the detailed cut-list groups and the 21-circuit plan live in Daniel's chat, not the repo.

**Freeze/blockers right now:** fuse box rev 7 approval (row 107); Dan's review of the ONE drawing set
(row 153); A/C wiring N61. Nothing else in harness wiring moves until those clear.

**Note on PRs:** #385 is **merged** (rules). #387 ("A/C: Link runs the A/C, A15 removed") is **closed,
unmerged, draft** — it was built on the *voided* A/C design (Dan reversed "A15 removed" on 2026-10-20).
Its branch `dan_/ac-link-csb3` is dead; do not revive it. Current A/C direction = both amps stay, N61 open.

---

## 2. What Daniel's two chat answers change

These two answers are from the "Harness wiring diagram project" chat and are **not yet recorded** in
OPEN-ITEMS, DECISIONS, Needs Dan, or the master. They should be confirmed, then written in.

### Answer 1 — starter / clutch (Daniel chose option A)
- **C17 (cruise clutch switch) → the CSB3** for clutch state.
- **C11 → the starter only.**
- **Keep the factory R/B No.4 starter relay**, with the **Link switching its ground** (low-side,
  B15-compatible).

**What this reverses in the repo today:**
- The master currently runs the starter through a **glove-box LOGIC-box relay `k_str`**
  (`CabinPower` rows `w_k_str_86_cp`, `w_fb_k_str_87_cp`, `w_start_in_cp` from the R/B No.4 socket).
  README/History say "R/B No.4 removed; its jobs are in the glove-box boxes as k_str, k_htr, A/C fuse."
- Option A keeps the **physical factory R/B No.4 starter relay instead of `k_str`**. So `k_str` comes
  out of the LOGIC box, and the Link drives the factory relay coil's ground.
- This is the latest step in a flip-flop: 2026-10-20 "R/B No.2-4 stay (kick panels)" → 2026-10-21
  "all R/B boxes go except J/B1/J/B3" → now "keep R/B No.4 for the starter." **R/B No.4 must stop
  being on the removed list** for the starter relay; its other jobs (k_htr, A/C fuse) stay in the boxes.
- The README already hints at this ("the R/B No.4 socket keeps two live leads as pigtails: the key
  START wire and the clutch switch wire"), but the master still wires `k_str` as the starter relay.
  **README and master disagree — Answer 1 is the tie-breaker.**

### Answer 2 — rear lights (Daniel chose option B)
- **Reuse the OEM rear lighting wiring in the car** instead of building a new `RearLights` harness.

**What this changes in the repo today:**
- The master has a **19-row `RearLights` harness** (tail / stop / turn / reverse / ground to R11, R12,
  L1, H6, S9, ground point BL). Answer B means that harness is **dropped** — the rear lamps stay on
  their OEM wiring, fed from the kept cabin side (J/B No.1), same as other kept OEM circuits (B11).
- README already lists "the rear lights" under **Kept OEM**, so the master's new `RearLights` harness
  is the stale side. The only new wire the rear should need is whatever a removed box used to feed
  (e.g. reverse lamp feed if it came through a removed relay) — check each of the 19 rows against the
  1993 EWD and keep only genuine re-feeds.
- `docs/harness/routes/ROUTE-15-REARLIGHTS.html` becomes stale and should retire in the sweep.

---

## 3. Stale files, contradictions, and cleanup flags

1. **R/B No.4 removed vs kept** — README/History (removed, `k_str`) vs Answer 1 (keep factory relay).
   Resolve per Answer 1; update `docs/harness/README.md` kept/removed list, row 164, and the master.
2. **RearLights harness vs "rear lights kept OEM"** — 19 master rows + Route 15 contradict README and
   Answer 2. Resolve per Answer 2.
3. **PR #387 branch `dan_/ac-link-csb3`** — abandoned, built on the voided "A15 removed" A/C design.
   Dead end; don't reuse. A/C is N61 (both amps stay).
4. **Stale routes to retire in the sweep** (row 164): Routes 1-4 (engine-bay paths superseded by
   Route 16), Routes 10-13 (superseded by Route 17), and now Route 15 (per Answer 2).
5. **`cad/fusebox/frozen-inputs/`** (13 `.harness` copies + `full_text.json`, restored #381) may lag
   the master; `wiring_sim.py` / `fb_labels.py` read them. Reconcile at the next fuse-box CAD job.
6. **`w_fp85` route/length wrong** (row 157): routed "glove-box branch" 390 mm, but K-FP is in the
   trunk relay block (~3 m). Fix in the master.
7. **Unused wire parts** (row 167): ~striped/old-colour `M22759/16-*` rows in
   `docs/sourcing/harness-parts.csv` are unused after the 7-colour recode. Delete (R211).
8. **212 of 461 wire rows have no `est_length_mm`** (row 165): BOM undercounts wire length.
9. **Six `sot/channels.csv` rows parse with an extra field** (row 142): quote the notes.
10. **TBD cells in the master** (row 150): 5 housings, 7 cables, 109 pins, 80 terminals still TBD —
    blocked on maker drawings the agent network can't reach (403/404). Needs Dan's picks or PDFs.

---

## 4. Ordered plan to keep going (G1, surgical rewire — row 164)

Everything here is **step-by-step with Dan, 1993 EWD in hand** (B2 freeze still applies; this is G1
work, which the freeze allows).

1. **Confirm the two answers** (section 2) and the 21-circuit plan with Dan; then write them in:
   - Answer 1: edit the master (remove `k_str` as starter, wire the factory R/B No.4 relay coil ground
     from the Link, C11 → starter, C17 → CSB3), update README kept/removed list and row 164. A B15/
     B11 reconcile is needed (low-side drive of a factory relay; the relay's +12 V source).
   - Answer 2: remove the `RearLights` harness rows that are new wire, keep only true re-feeds, retire
     Route 15.
2. **Finish the firewall cut list** — group 3 (IG1/IG2), then the remaining groups up to 8 total. One
   master row per wire crossing from a removed part into a kept harness: re-feed from the cabin side,
   or remove back to its last live point, each with its 1993 EWD page.
3. **Settle A15 / N61** (A/C compressor-speed signal) before Dan reviews the drawing set — recommend
   option A (Link tacho → A15 RPM input, lock emulated); bench test planned.
4. **Write the cuts / re-feeds / reuses into the master** with pins at both ends (st185-change-sot),
   then `python docs/harness/tools/check_wiring.py` and `python tools/check_all.py`.
5. **Draw the new routes over the OEM pages** (old-vs-new overlays for every new harness route), then
   the B1-B30 walk-through, then the Step 5 add list (new wires only).
6. **Sweep stale material** — retire Routes 1-4, 10-13, 15; delete unused wire parts (row 167); fix
   `w_fp85` (row 157); fill `est_length_mm` (row 165); quote the six `sot/channels.csv` notes (row 142).
7. **Firewall bulkhead** sized from the new-wire count, from Dan's on-hand parts first (HDP24/26
   47-pin and 21-pin pairs, HD34/36 21-pin; `docs/sourcing/te-on-hand-bom.csv`).
8. **Per-harness wiring tables** generated from the master (row 158), after the bloat cut clears.

---

## 5. Open questions for Daniel

1. **Confirm Answer 1 (starter/clutch, option A):** keep the factory R/B No.4 starter relay with the
   Link switching its ground; C11 → starter only; C17 → CSB3. This reverses the glove-box `k_str`
   starter relay now in the master. OK to write in?
2. **Confirm Answer 2 (rear lights, option B):** reuse the OEM rear lighting wiring and drop the new
   `RearLights` harness (19 master rows + Route 15). OK to write in?
3. **Confirm the 21-circuit plan** from the chat (it is not in the repo — paste or confirm the list so
   it can be tracked in row 164).
4. **N61 (A/C / A15 compressor-speed signal):** confirm option A (Link tacho → A15 RPM input, lock
   signal emulated) so the drawing-set review isn't blocked.
5. **R/B No.4 jobs besides the starter:** k_htr and the A/C fuse were moved to the glove-box boxes.
   With R/B No.4 kept for the starter relay, do those stay in the boxes (recommended) or move back?
