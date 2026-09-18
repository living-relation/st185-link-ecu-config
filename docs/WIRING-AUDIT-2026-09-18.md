# ST185 wiring audit — 2026-09-18

## Purpose
Read-only pass: living ECU IO vs harness.design vs HTML/MD faces. **Pass A mechanical applied** on feature branch (see below).

Vehicle: **1991** ST185 / 5S-GTE / Link G4X XtremeX.

## Trust order (Seeker's lamps)
1. Latest Claude/Cursor wiring decisions
2. `harness.design` — mechanical loom SoT
3. `XTREMEX-IO-TABLE.html` — ECU IO / colour SoT

Do not circular-reconcile HTML↔MD.

## Bottom line
Living ECU IO channel IDs match pin-for-pin across `XTREMEX-IO-TABLE.html` + repo `docs/harness/*.harness`. No material channel mismatches.

**Pass A COMPLETE** (2026-09-18, branch `pass-a-bh-c-delete-locks`; Pass A @ `37af8f6`, VSS Path B @ `784c712`, power/comms arch @ `d0bd909` pushed):
- Commits: `37dab05` residue · `4aa016f` bh_c delete · `0c868d4` B29/fuel/AC IO · `37af8f6` audit + BOM + pin-graph crown
- `bh_c_*` deleted from ACTIVE Signal + Power (empty shells + leftover HV). Fan/EPS HV already live in `ST185-EngineRoom-C.harness` (direct, no HDP20). ETB 12 V via bh_c removed as leftover — V-Ethrottle remains `k_etb` → B5 (`w82`); do not invent A/B cavities.
- A7 shield bulkhead run `w12_c` / `w12_e`: **Gray → Green/Yellow**
- Gnd Out harness colours: **Black → Black/White** (Power `sp_gndout*` rails)
- B29 / DI8: **SEALED car-side** — gearbox **3-wire 12V Toyota VSS** (not 4-wire); mate = **generic oval 3-pin plug with socket contacts**, **PN TBD**; signal → B29 / DI 8; oval cavity map TBD (do not invent); **not** OEM SPD tap (path A). Stub `vss_gbx` in Signal (no wire yet).
- Fuel level: OEM sender + divider; pull-up **`r_fuellvl` = 470 Ω** (living SoT — SENSOR-AND-ACTUATOR-REFERENCE / NEED-TO-BUY / harness; cal may refine later)
- AC kill: intentional OEM amp; **ground = kill, float = run**
- BUILD-LIST / NEED-TO-BUY regenerated from harness crown

## Conflict table

| Priority | Item | Note |
|----------|------|------|
| DONE | `bh_c` | **Deleted** from Signal + Power ACTIVE. EngineRoom-C / RADLOK remain SoT for HV fans/EPS / heavy DC |
| MED | B27/B28 | Frozen VERIFY says Spare; living SoT is B28 = DI9 Ign Switch — leave VERIFY frozen |
| DONE | A7 shield | **Green/Yellow** on Signal `w12_c`/`w12_e` (matches XTREMEX-IO-TABLE) |
| DONE | Gnd Out colour | Power rails **Black/White** |
| INFO | BOARD-VERIFY | "pins unverified" is a stale snapshot |
| LOCKED | B29 harness wire | **Path B** @ `784c712`: gearbox **3-wire 12V Toyota VSS** → generic **oval 3-pin sockets**, P/N TBD. Faces **IGN / GND / SP1** (not pin #s). **SP1 → B29/DI8** only into ECU loom; IGN+GND bay-local. Path A jarred. Cavity order still open. |
| LOCKED | Fuel pull-up Ω | **`r_fuellvl` = 470 Ω** to +5V (A32) for An Volt 9 / B24 — living SoT (SENSOR-AND-ACTUATOR-REFERENCE + NEED-TO-BUY + harness). Float ~3/110 Ω. Level only (no low-fuel LED). V→% cal on-car. |

## Pin-graph (crowned on Pass A)
`docs/harness/ecu_pin_graph.csv` (crowned @ `37af8f6`).

## Update plan (after Daniel okays)
1. Crown pin-graph CSV under `docs/harness/` (optional / next)
2. ~~Pass A — migrate/delete `bh_c`~~ **DONE**
3. ~~Colour hygiene A7 / Gnd Out~~ **DONE**
4. ~~Regenerate BUILD-LIST / NEED-TO-BUY~~ **DONE** (this pass)
5. Leave VERIFY / AUDIT / BOARD frozen (BOARD/VERIFY still frozen; this audit is the living Pass A record)
6. Stop editing OneDrive monolith
7. Draw B29→`vss_gbx` signal wire once oval cavity map (which cavity = SIG) is known; Fuel pull-up locked `r_fuellvl` = 470 Ω; V→% cal on-car. PN for oval 3-pin still TBD.

## Consolidation
Option A: pin-graph as IO index + four `.harness` as manufacturing SoT; HTML/MD generated or thin pointers. Keep harness.design first-class.

## Locked decisions (Daniel via Grimoire 2026-09-18) — ALL sealed; Pass A applied
Living SoT + Link primary + Daniel locks:
- **CAN 2 unused** — DI9/DI10 free as ordinary DIs; all buses on **CAN 1**
- **Hold Power required** for ETB key-off — Aux 6 (A28) + DI 9 (B28)
- **V-Ethrottle (B5)** = **12V power IN** via Aux 2 (A20) relay — not ECU out
- **+8V cam Hall:** A6 +8V Out + **1.8k** pull-up (not kit 2.4k/12V)
- **AC-kill-only / no Request DI** — intentional OEM amp; polarity **ground = kill, float = run**
- **Pin-graph CSV** — crowned on Pass A @ 37af8f6
- **Loom C / bh_c** — **deleted** `bh_c_*` from ACTIVE; no bulkhead; EngineRoom-C / RADLOK pass-thru
- **A7 colours** — **Green/Yellow** (applied on Signal shield bulkhead run)
- **B29** — **SEALED**: gearbox **3-wire 12V Toyota VSS** (not 4-wire); generic oval 3-pin socket plug **PN TBD**; signal → B29 / DI 8; cavity map TBD; **not** OEM SPD tap (path A)
- **Fuel level** — OEM sender + **`r_fuellvl` 470 Ω** pull-up (living SoT)
- **Git** — **feature branch only**; no main until verified

## Open locks (Daniel)
Policy locks (Daniel 2026-09-18): VSS wire to labeled 12V/GND/Signal (cavity order later, no invent); fuel pull-up **`r_fuellvl` = 470 Ω** (living SoT: SENSOR-AND-ACTUATOR-REFERENCE + NEED-TO-BUY + harness); KEEP RTR+horn on Loom C; residual LED harness face **YES**; RADLOK must exceed **160 A continuous**; UVC cam TBD; car year **1991**; push of `pass-a-bh-c-delete-locks` approved (Grimoire fires from 1:1). Batt LED: C12(C)8 Y = alt L, C12(C)9 B–O = IG — residual; no CSB. **Repo rule:** never put ask-lists / open-question docs in-repo.



## Power + CAN1 face (Daniel 2026-09-18)
See `docs/POWER-AND-COMMS-ARCHITECTURE.md` (@ `d0bd909`). Summary:
- Trunk batt → kill + fusible link → RADLOKs to engine (starter/alt); jump lugs near firewall; fuse/relay box + PDU glovebox side
- **CAN 1 only:** 3-cluster + RealDash Pi 7" + CAN-Lambda + ECUMaster CSB + PDU; CAN1 comms cable carries **12V+GND out** for displays/CSB
- Reverse: OEM reverse switch → ECU gear=7 on CAN → cluster **R** + RealDash USB camera


## Fuel sender measurement (2026-09-18)
- OEM float is **resistive** (~3 Ω full / ~110 Ω empty), not a native 5 V sender.
- Factory gauge is on the **12 V body** side; Link An Volt is **0–5 V** only → **+5 V pull-up/divider** on An Volt 9 / B24 (do not feed 12 V gauge circuit into B24).
- Low-fuel **silver single-wire** cylinder = thermistor (not float). See **Low-fuel thermistor** below.
- **EWD cite:** ST185 Combination Meter pp.145–146; F18 float 3–4 ≈ 3 Ω full / 110 Ω empty; gauge on **15A GAUGE 12 V**.
- Harness colors (sheet + community): **Y–R** level, **Y–L** empty-lamp candidate, **BR** float ground (Y–L = thermistor candidate until F18 pin page locks).


## CAN gear / reverse (SoT check 2026-09-18)
- Bus (`0x3EB` byte 0): `0=N, 1–6=fwd, 7=R` — frozen in center-cluster `canbus.c` + `CANBUS-ENCODE-DECODE-REFERENCE.html`
- Center UI: `7 → −1` then glyph **R**
- RealDash: not set up yet — reflash + listen-frame; map wire `7` → R/−1 or Reverse Lights
- Reverse path: OEM reverse switch → ECU → CAN gear=7 → cluster R; RealDash USB camera after reflash

## RealDash reverse camera status (2026-09-18)
- **Pi Linux caveat (2026-09-18):** USB camera as RealDash **Video Gauge** is **Android-proven only** — Pi/Linux in-gauge cam path **unverified**. Gate any Pi reflash on a **Pi in-gauge cam smoke test**. **Jump-to-Page** (gear/R page) can ship separately without waiting on video gauge.
Do **not** reflash Pi until camera page + triggers exist.

| Piece | Status |
|-------|--------|
| Path: OEM reverse → ECUMaster CSB → CAN → ECU Trigger → Gear=7 on `0x3EB` | Sealed |
| `link_g4x_realdash.xml` Gear carve-out (`ST185: Gear`, frame 1003) | Written (bind when building) |
| Camera page + triggers in `.rd` | **Not built** — deferred 2026-09-04; flash **`.rd`+XML together** when ready |
| Layout plan | Still single-page; no page swipe / media player yet |

Verified capability: Jump to Page / Video Gauge Play from trigger (in-app; no Linux app-switch). **Trigger:** existing Link **Gear on `0x3EB`** (map 7→R page only; **not** Reverse Lights; **do not display gear** on RealDash). Camera page still **unbuilt**; when ready, flash **`.rd` + XML together**. Do not reflash Pi on XML alone.

## Low-fuel LED algorithm (Daniel + Grimoire 2026-09-18)
> **SCRAPPED 2026-09-18 afternoon** — float An Volt is fuel level only; no LED/thermistor lamp path.

Thermistor **dropped**. Drive **12V low-fuel LED** from float An Volt (B24).

**Two stages** (Grimoire 2026-09-18):
- **Gauge path:** short upstream filter **4–8 s** (smooth needle / An Volt display)
- **Lamp path:** separate **~45 s** confirm + hysteresis (not the same filter as the gauge)

Prefer **hysteresis + confirm timers** (not raw MA alone):
- **On:** smoothed level below threshold for **45 s continuous**
- **Off:** smoothed level above threshold + ~**5–8%** hysteresis for **15–20 s**
- Smooth: exponential MA, τ ≈ **20–30 s** (or 40–60 samples @ 1 Hz)
OEM thermistor ~40 s dry→lamp was thermal lag; this recreates that calm in software.

## Daniel correction (2026-09-18 afternoon) — SCRAP low-fuel LED parchment
**SCRAP** all low-fuel LED / thermistor / cluster lamp drive plans. Float An Volt + divider is for **FUEL LEVEL display only** (not a lamp driver).

### RealDash reverse (corrected)
- **MUST** use existing Link **Gear on `0x3EB`** (already in ECU CAN + center cluster). **NOT** Reverse Lights.
- **No new ECU I/O.** Do **not** display gear on RealDash.
- Prefer **return-to-main** after out-of-R for **10 s** (or **10 mph** if speed listen is added later).
- Cam page still unbuilt; Pi USB Video Gauge unverified; Jump-to-Page can ship separately; flash `.rd`+XML together when ready.

### Warning LEDs present (no low-fuel LED)
- **Hi beam, L+R turn, park brake** — body electronics / residual dash harness taps behind removed cluster
- **Batt charge** — residual dash stub: **C12(C)9 B–O** = IG, **C12(C)8 Y** = alt **L** (EWD ~p.144; regulator grounds L to light lamp). **No CSB bit.** Oil pressure LED still Link → CSB (active-low verify).
- **Ignore OEM meter pin faces** (C10/C11/C12 fuel/lamp faces) — residual dash harness only, not a full meter rebuild

F18 2–1 thermistor map remains archival OEM only; not used.

## RealDash / CSB LED bits (Grimoire 2026-09-18)
- Reverse cam: `ST185: Gear` on `0x3EB` already carved in `link_g4x_realdash.xml` — cam only; **no** Reverse Lights; **no** gear gauge on RealDash.
- **Return-to-main:** Dummy Timer — Gear≠7 resets; timer ≥ **10 s** → Jump to main (no MPH listen required).
- RealDash Gear carve-out already in `link_g4x_realdash.xml` (`ST185: Gear` / `0x3EB`) — cam-only, no gear gauge.
- Oil: `0x3F1` bit4 = Low Oil Press 2 already allocated; cluster has oil kPa on `0x3E9`.
- CSB `0x643` confirmed ECU→CSB **low-side** (GND switch); **LS4+** currently spare after fan/AC.
- **Batt charge:** alt **L** path sealed — **no CAN/CSB bit**. Oil pressure stays Link→CSB.
- UVC cam candidates + Pi smoke-test gate: see POWER-AND-COMMS / council notes.

## Daniel seals (2026-09-18) — SUPERSEDED where conflicted by afternoon correction — living-relation + Claude SoT
Defer to **Claude 5sgte/cowork** + **living-relation/`st185-link-ecu-config`** as primary; **rd-st185** Cursor work is secondary.

1. **Global SoT** — Claude + living-relation primary; rd-st185 secondary.
2. **Low fuel** — **drop** in-tank low-fuel thermistor. Drive cluster **12V low-fuel LED** from float **An Volt** (B24) + **smoothing** (target ~40–60 s), not thermistor self-heat.
3. **Loom C purpose** — OEM loom-C mods + **12V/GND injection** for trunk battery / fuse relocate; keep **kick-panel junctions** + most inner OEM harness. Many loom-C diagrams are **intentional** (purpose docs), even where Pass A removed `bh_c_*` ACTIVE bulkhead shells.
4. **Cluster 12V LEDs** — low fuel, low oil pressure, alt/charge, park brake, high beam, L/R turn. Prefer **OEM cluster circuit taps** after gauge remove; do **not** rework dash loom beyond cluster removal. Fuel taps inked (F18 / C10–C11); other warning LEDs (oil/alt/park/beam/turn) still need EWD face.
5. **Reverse** — already in SoT: OEM reverse → **ECUMaster CSB** → CAN → ECU Trigger **Gear=7** on `0x3EB`. RealDash USB camera page **DEFERRED** as of 2026-09-04 (not a wiring blocker).

No main merge until Daniel verifies.

## Cluster / F18 EWD pin-map (Seeker 2026-09-18) — archival; ignore meter faces for build
Cite: ST185 EWD p.145 circuit + p.146 hints. Meter codes **C10(A) / C11(B) / C12(C)** (ignore C13–C15 header mismatch).

### F18 fuel sender
| Pins | Function | Colors | Notes |
|------|----------|--------|-------|
| **3–4** | Float | **Y–R** / **BR** | ≈ 3 Ω full / ≈ 110 Ω empty — living An Volt path |
| **2–1** | Low-fuel thermistor | **Y–L** / **W–B** | Lamp side → case GND; path F18 → BP1 → IF1 → meter. **Cavity locked** but thermistor **still DROPPED** for An Volt % → 12V LED |

### Cluster fuel taps (OEM after gauge remove)
- Fuel gauge: **C11(B) pin 3** ← Y–R ← F18-3
- Low-fuel lamp: **C10(A) pin 10** ← Y–L ← F18-2
- Gauge power: **C11(B) pin 7** ← R–L from 15A GAUGE

Full C10–C12 cavity art not in this EWD (location only). No pin rewrite if float stays on An Volt.

## Residual dash-harness taps (Seeker 2026-09-18)
OEM meter **gone** — splice **harness stubs** at C10/C11/C12 (**not** meter PCB). Cite EWD p.144 / p.72 / p.82.

| LED | Stub cavity | Color | Body source (upstream) |
|-----|-------------|-------|------------------------|
| Hi beam | **C11(B)12** | **R–L** | High-beam feed (dimmer HIGH / same as RH high) |
| Turn L | **C11(B)2** | **G–B** | Turn/hazard flasher LH |
| Turn R | **C11(B)11** | **G–Y** | Turn/hazard flasher RH |
| Charge / alt L | **C12(C)8** | **Y** | Alt regulator **L** (grounds to light) — keep L to alt; splice residual |
| Charge / IG feed | **C12(C)9** | **B–O** | IG feed for charge lamp — residual |
| Park brake | **C12(C)1** | **R–G** | Grounds via **P1** (and/or B2 fluid) — sense ground-side |

Oil + batt = Link/CSB (`0x3F1` / `0x643`), not body loom. Dummy Timer ≈10s exit-R (no native Delay). **No** load-bearing STEP ST185+3S-GTE (mesh/scan only; ignore Fujimi kit STLs as loom CAD).

### Pi5 UVC cam candidates (still smoke-test gate)
1. ELP-USBFHD06H-BH36 — waterproof FHD UVC
2. Kayeton KYT-U200-CA01
3. Goobuy UC-531 IP67
Ignore AHD / LCD backup kits. RealDash Linux USB Video Gauge still unproven.


## Loom C ↔ EWD flag pass (Roger Roger 2026-09-18) — read-only
Inventory: SoT `docs/harness/ST185-EngineRoom-C.harness` + 3 cursor splits (schematic only). EWD = 1990 All-Trac PDF in inbox.

**MATCH:** OEM-stay + trunk 12V/GND inject; no bh_c; EA1/IE1/ID1; AM1/AM2 at IE1-10/17; HEAD 2A-3/6; DOME 2E-4; grounds; residual stubs C11/C12 colors; ABS/SRS deleted.

**FLAG (top)**
1. Layout missing on all EngineRoom-C `.harness` (schematic-only)
2. 2E-2 / 2E-3 still wired despite PROBE — ohmmeter before crimp
3. Probe note overclaims EWD p.48 (AM1/AM2 vs RTR/HAZ)
4. `w_pdb_am2` color Brown vs EWD **B–R**
5. Inject colors generic Red vs Toyota stripes
6. Stale consolidation docs still mention bh_c leftovers
7. Meter hint codes C13–C15 ≠ circuit C10–C12 — ignore hints
8. Residuals MD-only, not in any `.harness`
9. RADLOK must **exceed 160 A continuous** (alt 160 A upgraded) — size TBD to meet that
10. Book year 1990 vs car 1991 — spot-check on car


No edits/push from this pass. Full detail in Roger 1:1 if needed.


## Daniel locks (2026-09-18 evening)
- **Repo rule:** never put ask lists / open questions / handoff TODOs in the repo — living asks stay in chat/memory only.
- **VSS:** wire to labeled 12V / GND / Signal; cavity order later (no invent).
- **Fuel pull-up:** **`r_fuellvl` = 470 Ω** (found in SENSOR-AND-ACTUATOR-REFERENCE + NEED-TO-BUY + harness) — level only.
- **KEEP** RTR + horn on Loom C.
- Residual LED harness face: **YES**.
- Batt/charge LED: **C12(C)8 Y** = alt **L**, **C12(C)9 B–O** = IG — residual splice; **no CSB**.
- **RADLOK** must exceed **160 A continuous** (alt is 160 A upgraded).
- UVC cam: TBD (prior candidates rejected).
- Push of `pass-a-bh-c-delete-locks` **approved** — Grimoire pushes from 1:1.
- Vehicle year: **1991** (not 1993). EWD family same.

## Related shelves
- `docs/BOARD-VERIFY-2026-09-11.md`
- `docs/HARNESS-FACES-2026-09-11.md`
- `XTREMEX-IO-TABLE.html`
- `docs/POWER-AND-COMMS-ARCHITECTURE.md` — race power + CAN1/comms (Daniel 2026-09-18)

## Sixth crown (2026-09-18)
Link G4X XtremeX QSG + Link admin posts (ST185/MR2) + HP Academy / official manuals — verify living IO before Pass A. 3SGTE AC threads = pattern evidence only, not ST185 pin fact.

Pass A **applied** (2026-09-18). Checklist: delete bh_c ✅, A7 to Green/Yellow ✅, B29 VSS (IO) ✅, fuel divider note ✅, AC kill polarity ✅, Gnd Out BW ✅, regenerate build-list faces ✅. Feature branch only.

## Link-canon match table (2026-09-18)

Primary: XtremeX QSG 2023 (not 2016 G4+), TST185X OEM meanings only, Adamw staff posts. 3SGTE/HPA = AC pattern only.

| Claim | Living SoT | Link primary | Verdict |
|-------|------------|--------------|---------|
| B28 = DI9 Ign Switch | XTREMEX-IO-TABLE: DI9 Ign Switch (Hold Power); CAN 2 unused; Aux 6 EFI hold | QSG: DI9 switch or CAN2; Adamw: Ign DI needed when post-key-off hold | **MATCH cavity** — B28 as DI9 allowed by QSG; Hold Power is **project choice** (Adamw: often skip on DBW). Ink as allowed + intentional, not Link-required. PCB-rev for DI9/CAN2 mux still unproven |
| B27 = DI10 Available | CAN 2 unused | QSG PCB >=1.4 DI9/10 vs CAN2 | **MATCH** if board not using CAN2 — confirm PCB rev once |
| Aux AC / FP / fan | Project Aux + DI | Staff pattern Aux+DI+Basic; TST185X OEM pins are plug-in only | **MATCH pattern** — do not copy TST185X pin numbers onto wire-in |
| Ign colours Violet / shield GY | This harness column | QSG defers to PCLink; no admin override | **KEEP** XTREMEX-IO-TABLE |
| bh_c delete | Consolidation plan | No Link post | **Project decision** — applied Pass A |
| Frozen VERIFY B28 Spare | Dated record | Living + QSG allow DI9 switch | **Leave frozen** — not a living conflict |

**Bottom line:** Link-canon does not force a pin rewrite. B28 DI9 Ign Switch = allowed + intentional (Hold Power project choice, not Link-required). PCB-rev for DI9/CAN2 mux unproven. Pass A **complete** on feature branch. Feature branch only — no main until verified.

## Forum dive topics (Daniel 2026-09-18)
Also check Link forum discussions on:
- Electronic throttle body
- Electric throttle pedal
- AC control via OEM AC amplifier (Link only sends AC kill to the amplifier)
- ECU power hold wiring
## Forum dive staff brief (2026-09-18)
- **ETB + pedal:** Adamw — Aux9/10 motor; TPS/APS dual AN Volts; +5V + sensor gnd. Matches living Aux9/10 + B5. No pin rewrite.
- **Power hold:** Ign Switch DI mainly stepper keep-alive; for DBW key often cuts ECU power. Aux6+DI9 Hold Power = **allowed intentional**, not QSG-required.
- **OEM AC amp kill-only:** Staff Basic wants DI Request + Aux Clutch. Living kill-only to OEM amp = **intentional override** — polarity confirmed ground=kill float=run; do not invent Request DI to match Link.
- **Ignore:** TST185X pin numbers; non-staff pinouts; Hold Power as Link-mandated for DBW.

## VSS car-side seal (Daniel 2026-09-18)
- **Sensor:** gearbox **3-wire 12V Toyota VSS** (not 4-wire).
- **Connector:** generic **oval 3-pin plug with socket contacts**; **part number TBD**.
- **ECU landing:** signal → **B29 / DI 8** for mph.
- **Pin map:** oval cavities PWR / SIG / GND = **TBD** — do not invent.
- **Not chosen:** OEM SPD tap (path A).
- **Fuel pull-up:** **`r_fuellvl` = 470 Ω** (living SoT; not an open ask).
- Harness: stub connector `vss_gbx` + part `cp_vss_oval3` in `ST185-Signal.harness`; B29 still `notConnected` until SIG cavity known.

## Low-fuel thermistor — **DROPPED** (Daniel 2026-09-18; was Seeker FSM lantern)
> **SCRAPPED 2026-09-18 afternoon** — float An Volt is fuel level only; no LED/thermistor lamp path.

- **DROPPED:** do not wire in-tank thermistor. Cluster low-fuel **12V LED** from float An Volt + smoothing (~40–60 s).
- Single-wire silver cylinder is the **low-fuel thermistor**, not the float (float = F18 pins 3–4 ohms).
- Toyota instrument FSM bench (Celica-family): battery on sensor terminal; test lamp body to ground — **dry → lamp on within ~40 s**; **immersed → lamp stays off**.
- OEM intent: **IG → lamp → single wire → case ground** when hot/dry. Bare LED alone is the wrong load (needs ~incandescent ballast / self-heat current).
- **LED options for Daniel (no pin invent):**
  1. **SEALED:** float An Volt 9 / B24 → cluster **12V low-fuel LED** + smoothing ~40–60 s (thermistor dropped)
  2. Keep thermistor: **IG → ballast/lamp → wire → case GND**, sense node with transistor/optocoupler → LED
  3. Tap lamp voltage into an An Volt and threshold
- Thermistor F18 cavity **locked: pins 2–1** (Y–L / W–B) — path still **DROPPED**; do not wire for cluster LED. Local EWD PDF: `inbox/.../Toyota - ST185 - Electrical Wiring Diagram.pdf` COMBINATION METER pp.145–146.

