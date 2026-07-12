# ST185 TrackCluster .rd — Build Notes (2026-07-06)

Built with RealDash 2.6.7 (Windows, Microsoft Store) via editor automation on DansPC.

## Deliverables
- `st185_dash.rd` (repo root + `rd-build/realdash-root/st185_dash.rd`) — 39,248 bytes
- No `_anim.xml` sidecar (no animations created — see deviations)
- CAN channel file: `rd-build/link_g4x_realdash.xml` (imported into a RealDash CAN / WIFI-LAN connection)

## What was built (per PLAN.md §4)
- Editor canvas 1920×1080; all spec coords scaled ×2.4 (X/W) and ×2.25 (Y/H).
  RealDash normalizes to display, so on the Pi's 800×480 everything lands at spec positions.
- Top strip (0,0,1920,122, #26384c) with title "ST185 / DASH".
- 6 status pills, each bound to its ST185 bit channel, dim (#243243) with dynamic
  background to lit color at value 1: FLAT & FAN → blue #34a8ff; LOFUEL & SBFLT → amber
  #ffc233; COOLANT P & OIL P 2 → red #ff4d57.
- 13 tiles (4×4 grid, 3 span-2): background panels #2c3c50/#243243, dim labels #9fb1c6,
  large white value texts #f3f8ff bound to `ST185:` channels (rebound with "185:" prefix
  after discovering plain-name searches matched RealDash core channels first).
- Alarm tiles (Charge IAT 50/60, Coolant P 150/250, Turbo 180k/190k, Fuel Temp 55/70,
  Trigger Err 1/5): warning/critical set + dynamic text color white→red.

## Deviations from spec (documented per plan)
1. No mini-bars in tiles (Throttle, TC intervention, etc.) — RealDash bar gauges not
   built; numeric values + dynamic alarm colors carry the function.
2. No strobe fade animations on the two red pills / alarm states (§4.4) — pills still
   turn solid red via dynamic color. Can be added manually in the editor later
   (select pill → animations → fade 0.35s ping-pong).
3. Caution band renders as a white→red blend (RealDash dynamic color has 2 stops),
   not a discrete amber step. Amber is used as the lit color of LOFUEL/SBFLT pills.
4. Chrome-gradient title text → solid #f4f7fb; radial background → flat dark canvas.
5. Labels carry units in ASCII: "TARGET LAMBDA", "CHARGE IAT (C)", "COOLANT P (kPa)",
   "TURBO (RPM)" (λ/° glyphs not typeable via automation).
6. Boost Map / Cruise / A/C show numeric values; enum text (OFF/STBY/…) depends on
   RealDash's enum rendering with live CAN data — verify on bench.
7. Small "-" placeholder visible in empty tile-background text gauges until CAN data
   arrives; hidden behind live values in practice.

## Connection created
Garage → My Supercar → Connections: "RealDash CAN — WIFI/LAN 192.168.0.10:35000" with
custom channel description `link_g4x_realdash.xml`. On the Pi, change the connection
type/target to the real source; keep the same channel description file.

## Validation status
- Live sanity checks: all 13 values render and update from the bound channels
  (Target Lambda shows 0.6 = channel rangeMin; alarm tiles white below warning).
- NOT yet validated against real CAN frames — last-mile step on the bench/Pi with
  `apps/canbus-bench-test.html` / `canbus-live-sender` per PLAN.md §6.

## Account note
Login used the My RealDash account from CREDENTIALS.md. Consider rotating that
password now that the build is done (it was shared in plaintext).
