<!-- ══════════════════════════════════════════════════════════════════════
     RETIRED 2026-09-06 — NOT A SOURCE OF TRUTH, DESPITE THE FILENAME.
     This was an unlanded staging draft. Its DI4/DI5 proposals contradict the
     current design: reverse is on the ECUMaster switchboard over CAN, and
     DI 3-6 all four carry ABS wheel speed.
     Authoritative for ECU I/O: XTREMEX-IO-TABLE.html
     ══════════════════════════════════════════════════════════════════════ -->

# ECU Wiring — Master Source of Truth (v1)

**Vehicle:** 1993 Toyota Celica GT-Four ST185 AllTrac, "5S-GTE" hybrid (5S-FE block bored 87.5mm + 3S-GTE Gen 2 head)
**ECU:** Link G4X XtremeX (confirmed — see prior corrected artifact for the FuryX-doc mixup resolution)
**Status:** New consolidated document. Supersedes nothing yet on GitHub — this is the staging draft to reconcile into `XTREMEX-IO-TABLE.md` once you sign off.

> **2026-09-04 note (added when this file was copied into the repo):** The `ECU-wiring-design`
> branch's `DOCS-CLEANUP-PLAN.md` (2026-08-31, conflict C16) has since **reversed** the "Decided
> today" reverse-switch call below (§1, DI4) back to switchboard routing — see
> `REVERSE-CAMERA-TRIGGER-RESOLUTION.md` in this same folder for the current, authoritative
> answer. This file is kept as-is for history; do not treat the DI4 row below as current.

## harness.design — status

Tried `https://app.harness.design/Lgjw`. It's a client-rendered (Next.js) web app — a plain fetch returns only an empty page shell, no diagram data. I have no browser-automation or harness.design connector in this environment, so **I cannot view what's currently on that canvas, and I cannot write to it directly.** If harness.design supports exporting to CSV/JSON/image, send that export and I'll reconcile it against this document. Otherwise, treat this markdown table as the working source of truth, and you (or I, if you paste in harness.design's import format) can transcribe it in there by hand.

## How this document was built

Pulled from every source available, cross-referenced against each other:

- `living-relation/st185-link-ecu-config`: `XTREMEX-IO-TABLE.md`, `CAN-BUS-ID-ALLOCATION-TABLE.md`, `CAN-BUS-MASTER-DESIGN.md`, `CANBUS-LINK-G4X-CONFIG.md`, `ECUMASTER_SWITCHBOARD_SETUP.md`
- `living-relation/center-cluster-esp32-p4` (README, confirms XtremeX + external Link CAN-Lambda)
- Google Drive: "Daniel Grippin engine harness 1st draught" pinout image (an earlier hand-drafted device list — useful cross-check, not a current pin authority)
- Stored project memory (turbo, boost control, fuel system, cams, etc.)

**Status legend:**
- ✅ **Confirmed** — appears in the current GitHub repo, consistent across sources
- 🆕 **Decided today** — you asked me to decide; documented here, not yet written back to GitHub
- 🟡 **Proposed** — in the repo as a draft assignment, not yet locked
- ⬜ **Open** — genuinely unresolved, needs your input or field verification

---

## 1. Digital Inputs (DI 1–10)

| DI | Loom / wire | Function | Status | Notes |
|---|---|---|---|---|
| DI 1 | A / Red | Flex-fuel sensor (frequency → ethanol % + fuel temp) | 🟡 | Matches your fuel system (ATS 1400cc injectors, flex fuel sensor, fixed E85 tune) |
| DI 2 | A / Red-White | Clutch switch | 🟡 | |
| DI 3 | A / Red-Blue | Brake switch | 🟡 | |
| DI 4 | B / Grey-Purple | **Reverse switch → drives Gear Position = 7 in PCLink** | 🆕 **Decided today** | You confirmed: reverse switch sets Gear Pos=7 directly; forward gears are RPM/Speed math in the ECU. DI4 chosen because it was already labeled "Launch/spare" — a clean, unambiguous pick with no collision risk. **PCLink mechanism to implement:** a Virtual Aux / condition that forces the Gear Position runtime channel to 7 when this DI is active, overriding the RPM/Speed calculation. Exact PCLink screen/steps not yet verified — flag for your PCLink session. |
| DI 5 | B / Grey-White | **Turbo speed sensor (BorgWarner PN 179430)** | 🆕 **Decided today** | You confirmed the turbo speed sensor wires directly to the ECU and gets broadcast on CAN 0x3F0 byte 6. Restores DI5 to match your original build notes (which had turbo speed here) — the current GitHub table had drifted to "spare," this reconciles it. **Open flag:** 14-blade wheel × sensor pulse output vs. Link's documented DI frequency ceiling (~10 kHz) needs checking against your warn/hard-limit RPM (140k/145k) before this is final — see §6. |
| DI 6 | B / Grey | spare | ⬜ | |
| DI 7 | B / Grey-Yellow | spare | ⬜ | |
| DI 8 | B / Grey-Green | spare | ⬜ | |
| DI 9 / CAN2-L | A / White | spare DI (CAN2 intentionally unused) | ⬜ | |
| DI 10 / CAN2-H | B / White | spare DI (CAN2 intentionally unused) | ⬜ | |

**Cross-check:** your own earlier hand-drafted harness image ("Daniel Grippin engine harness 1st draught," Google Drive) already listed both a "Rev Switch" (white wire, switched feed, ECU body connector) and "Turbo Speed" (white signal wire + sensor ground + shield, ECU) as planned devices — this confirms both were always intended, just not yet carried into the current GitHub table before today.

## 2. Analog Volt Inputs (AnVolt 1–11)

| Channel | Loom / wire | Function | Status |
|---|---|---|---|
| An Volt 1 | A / Red | MAP sensor | ✅ |
| An Volt 2 | A | TPS (throttle position — cable throttle, ST185 is not DBW) | ✅ |
| An Volt 3 | A / Green | Oil pressure | ✅ |
| An Volt 4 | A | Fuel pressure | ✅ |
| An Volt 5 | B / Green | Coolant pressure | ✅ |
| An Volt 6 | B / Yellow-Green | Charge-pipe IAT (2nd, if analog) | ⬜ |
| An Volt 7 | B | Wideband (only if analog 0–5V type) | ⬜ — **N/A**, you use an external Link CAN-Lambda module (CAN-based, not analog) per `CANBUS-LINK-G4X-CONFIG.md`, so this row is likely unused |
| An Volt 8–11 | A/B | spare | ⬜ |

## 3. Temperature Inputs (Temp 1–4)

| Channel | Loom / wire | Function | Status |
|---|---|---|---|
| Temp 1 | A / Red-White | ECT (coolant temp) | ✅ |
| Temp 2 | A / Green | IAT (intake air temp) | ✅ |
| Temp 3 | B / Yellow-Green | Oil temp | ✅ |
| Temp 4 | A / Yellow-Orange | Fuel temp (or from flex sensor) | ⬜ |

## 4. Triggers & Knock

| Channel | Loom / wire | Function | Status |
|---|---|---|---|
| Trigger 1 | A / Yellow | Crank position (Ne) — BEAMS crank sprocket for coil-on-plug trigger compatibility | 🟡 confirm trigger type/pattern |
| Trigger 2 | A / Yellow-Brown | Cam / home (G) — feeds camshaft position; also relevant to HKS Step 2 264° cam degreeing work | 🟡 confirm |
| Knock 1 | B / Grey-ish | Knock sensor | ✅ |
| Knock 2 | B | 2nd knock (if fitted) | ⬜ |

## 5. Outputs

| Channel | Loom / wire | Function | Status |
|---|---|---|---|
| Injection 1–4 | A / Blue family | ATS Racing 1400cc injectors, cyl 1–4 (sequential) | ✅ |
| Injection 5–8 | B / Blue family | spare (usable as aux) | ⬜ |
| Ignition 1–4 | A / Orange family | Coils — coil-on-plug (COP), enabled by BEAMS crank sprocket | 🟡 confirm ignition type |
| Ignition 5–8 | B / Orange family | spare (usable as aux) | ⬜ |
| Aux 1 | A / Orange-Yellow | Boost control solenoid — MAC 46A-AA1-JDBA-1BA 4-port, driving the Turbosmart GenV IWG Twin Port actuator (TS-0620-4012, 14 psi spring) | 🟡 |
| Aux 2 | A / Orange-Green | Idle (ISC) — pin of a pair if 3-wire | 🟡 |
| Aux 3 | A / Orange-Blue | Idle (ISC) 2nd / spare | ⬜ |
| Aux 4 | A / Orange-Purple | Fuel pump relay | 🟡 |
| Aux 5 | A | Radiator fan | 🟡 |
| Aux 6 | A | AC clutch (or via switchboard low-side output instead — see §7) | ⬜ |
| Aux 7 | A / Brown-Orange | Tacho out / CEL | ⬜ |
| Aux 8 | A / Brown-Red | spare | ⬜ |
| Aux 9 (E-throttle +) | A / Purple | **Unused** — ST185 is cable throttle, not DBW | 🟡 confirm |
| Aux 10 (E-throttle −) | A / Purple-White | **Unused** (cable throttle) | 🟡 |

## 6. Turbo speed sensor frequency — RESOLVED (was an open flag, now checked against BorgWarner's own documentation)

**EFR 7163 max speed:** BorgWarner's official catalog page for the 7163 (applies to all variants including your 11639880002 Type-G) plots compressor speed islands up to **150,000 RPM** — the top labeled line on their compressor map. Your configured warn (140,000) / hard limit (145,000) sit just under that with sensible margin.

**Why "1.75 pulses/rev" is correct, not an error:** per BorgWarner's own speed sensor installation guide, all EFR compressor wheels (except 67mm variants) have **14 blades**, and the sensor's internal electronics divides the raw blade-pass frequency by 8 before outputting. 14 ÷ 8 = **1.75 pulses per shaft revolution** — an exact match to the PCLink scaling already configured. Not a mistake, confirmed correct.

**Output frequency at your limits** (RPM × 14 ÷ 480):

| RPM | Sensor output frequency |
|---|---|
| 140,000 (warn) | ~4,083 Hz |
| 145,000 (hard limit) | ~4,229 Hz |
| 150,000 (BorgWarner's max plotted speed) | ~4,375 Hz |
| 300,000 (sensor's own rated ceiling per BorgWarner PN 179430 spec) | ~8,750 Hz |

Even at the sensor's full rated max (300,000 RPM — far beyond anything the 7163 itself will ever see), output stays under 8.75 kHz, comfortably inside Link's ~10 kHz DI frequency ceiling. **DI5 is confirmed appropriate for this sensor across its entire usable range — no signal conditioner or special input required.** Output is a digital open-collector square wave (needs a pull-up, which Link DIs provide), matching Link's DI architecture directly.

**CAN resolution (already fixed in the repo):** `0x3F0` byte 6, unsigned 8-bit, 1000 RPM per count, 0–255,000 RPM range. At a 145k operating ceiling that's ~145 of 255 possible steps — 1000 RPM resolution is coarse but entirely adequate for a dash/logging value at this scale.

Sources: BorgWarner official EFR 7163 catalog page (compressor map, borgwarner.com); BorgWarner/Full-Race official speed sensor installation instructions (blade count, ÷8 divisor, worked frequency examples); BorgWarner PN 179430 product spec (0–300,000 RPM rated range, digital open-collector output).

## 7. ECUMaster CAN Switch Board V3 — accessory devices (not ECU-direct)

These don't wire to the ECU directly — they go through the switchboard (Base ID 0x640, reconfigured to 1 Mbit/s to share the ECU bus) and reach PCLink as CAN "User Stream" inputs:

| Switchboard input | Physical signal | Routed to |
|---|---|---|
| Analog 1 | Cabin temp NTC thermistor | PCLink GP Temp1 |
| Analog 2 | OEM cruise control stalk (resistor ladder, 1993 ST185 factory stalk — OEM cruise ECU bypassed, Link handles cruise natively) | PCLink AS_MASK or raw-mV decode → VDI1–3 (SET/RESUME/CANCEL) |
| Analog 3–8 | TBD | — |
| SW_MASK bit0 | Cruise MAIN switch (if discrete wire) | VDI1 |
| SW_MASK bit1 | AC request button | VDI2 |
| SW_MASK bit2 | Evap core over-temp switch | VDI3 |
| SW_MASK bit3–4 | spare | VDI4–5 |
| Low-side outputs (0x643, ECU → switchboard) | Fan relay 1, fan relay 2, AC compressor relay, spare | ECU-commanded, switchboard-driven |

## 8. CAN Bus — 4-node architecture (unchanged, for reference)

```
Link G4X XtremeX ECU  <-->  center-cluster-esp32-p4  <-->  ECUMaster CAN Switch Board V3  <-->  Pi5 (RealDash, listen-only)
```

1 Mbit/s, ISO 11898-2, BigEndian custom streams, 120Ω termination at the two physical bus ends (ECU end + Pi end). External Link CAN-Lambda module also shares this bus (ID 0x3B6, reserved). Full frame-by-frame byte layout already documented in `CAN-BUS-ID-ALLOCATION-TABLE.md` — unchanged by today's decisions except that CAN frame 0x3EB byte 0 (Gear Position) will now actually receive a value once DI4/PCLink logic is wired in.

## 9. Decisions made today (recap)

1. **Reverse switch → DI4.** PCLink sets Gear Position = 7 when active. Forward gears remain RPM/Speed math (unchanged, native Link feature).
2. **Turbo speed sensor → DI5**, restoring your original plan; frequency-range check flagged (§6) before calling it final.
3. **RealDash gets the camera** (not center cluster). Camera is a USB input into the Pi. Reverse trigger comes from the Gear Position CAN channel (0x3EB byte 0) once §1 above is wired — RealDash's channel XML still needs that channel added (from the earlier corrected artifact, this hasn't changed).
4. **RealDash reconfiguration + camera page build is deferred to an SSH session**, per your note — nothing further needed here until then.

## 10. Still open — needs you, not guesses

- Confirm the PCLink mechanism for forcing Gear Position = 7 from DI4 (exact PCLink screen/logic block).
- Resolve §6 (turbo speed sensor DI frequency ceiling) before wiring DI5.
- Everything marked 🟡/⬜ above was already open in the GitHub table before today — still open now, just consolidated here.
- Confirm whether you want this document's DI4/DI5 decisions written back into `XTREMEX-IO-TABLE.md` on GitHub (I can produce the exact diff/PR text — I can't push to GitHub myself, no write access to your repos).
