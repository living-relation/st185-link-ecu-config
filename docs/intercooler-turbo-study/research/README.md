# 5S-GTE ST185 — Intercooler and Turbo Selection Study

Research + engineering study for the 1991 Celica GT-Four ST185 with the 5S-GTE hybrid.
Round one picked the intercooler. Round two picked the turbo and the redline. Round three
(30 August 2026) reconciled this study against a body of earlier turbo research supplied
afterwards, and changed five conclusions. Rounds four and five applied Dan's corrections
to the hardware list and rebuilt the model around them. **Round six (1 September 2026)
restored two items from the original brief that were dropped during the round three–five
rewrites.**

## Round six — the two restored items

| Item | Finding | Section |
|---|---|---|
| **Oil cooler placement** | Front corner or fender well, outside the intercooler footprint. Behind the core costs the radiator **21% of its driving temperature difference**; in front of the core costs **5.0 °C of IAT**. If a corner feed is impossible, take *behind* over *in front* — never put a heat source in the charge cooler's inlet air. | §13 |
| **CS crash bar** | Do not remove it. Start the duct lip 40–60 mm behind it so its wake re-attaches, or fair it. Bare it costs **4.6 °C**; radiused, 2.5 °C; with a teardrop fairing, **0.9 °C**. The 25.4 mm bar is only 11% geometric blockage but ~28% *effective* blockage, because a square section sheds a wake 2.5× its height. | §12 |

Working: `oilcooler_crashbar.py` → `data/r6_data.json`.

## Open this

**`intercooler-report.html`** — the deliverable. Double-click it. Self-contained: all CSS,
JavaScript and charts are inline, no internet needed. 24 sections, 27 charts, 2 calculators.

---

## Round three — what changed, and why

| # | Was | Now | Why |
|---|---|---|---|
| 1 | 420–480 whp street/track, ~540 race (this report) and 466–517 whp (prior research) | **404 whp** at 7,500 rpm / 30 psi. Band 384–424. | Charge temperature is now solved simultaneously with airflow, and the conversion constants are corrected. §21.1 |
| 2 | Buy a Garrett G25-770, ~$1,850 | **Keep the EFR 7163 you own** | The G25-770 is not in Garrett's catalogue, and at 30 psi every candidate makes 401–406 whp anyway. §21.7 |
| 3 | Core 610 × 305 × **76** mm | Core 610 × 305 × **102** mm | Worth 9.2 °C and 7 whp, and you have the clearance. Reject the prior research's 711 mm *width* — the radiator behind it is only 712 mm. §21.8 |
| 4 | Manifold not examined | **Twin-scroll manifold is paired wrong** (1+2 / 3+4, should be 1+4 / 2+3) | Independently verified. Costs ~7 whp and 300–500 rpm of spool. §22 |
| 5 | Boost control not covered | **Feed the wastegate solenoid pre-throttle**, not from the manifold distribution block | Otherwise boost spikes on re-application after a lift or shift. §21.11 |

### The single error behind most of the gap

`06_turbo_model.py` computes `lb/min = K × RPM × VE × PR` where `K` is built from
`2164 cc ÷ 2 × 0.0765 lb/ft³`. That density is dry air at **15 °C at sea level**. Multiplying it
by pressure ratio and nothing else means the model assumes the air at the intake valve is at
15 °C, at every boost level. The real figure at this car's design point is about **79 °C**, and
79 °C air is 18% less dense. The same model uses 14.7 psi as ambient; Weaverville is 93.87 kPa.

At 7,500 rpm and 30 psi the three models give **542 / 441 / 404 whp**.

### The conversion constants, resolved

| Constant | Prior research | This report, r2 | **Round three** | Basis |
|---|---|---|---|---|
| Crank hp per lb/min, E85 | 11.0 | 10.0 | **10.0** | Garrett `60 ÷ (AFR × BSFC)`. AFR 7.8, BSFC 0.77 → 10.0. 11.0 needs BSFC 0.70, better than published E85 turbo figures. |
| Drivetrain factor, AWD | 0.85 | 0.82 | **0.80** | Measured Evo 6 engine-vs-chassis: 23%. Subaru consensus 20–25%. ST185's transverse transaxle is slightly kinder. Band 18–22%. |
| Displacement | 2,164 cc | 2,188.8 cc | **2,188.8 cc** | 87.5 mm bore. The prior research had both figures in different files. |
| whp per lb/min | 9.35 | 8.20 | **8.00** | |

**That one row spans 374 to 472 whp on identical airflow.** It is the largest single source of
disagreement between the two bodies of work — larger than the VE argument, which turned out to
be nearly a non-issue (the r2 and r3 VE curves agree to 0.006 everywhere).

---

## Round three recommendation, in one box

| | |
|---|---|
| Turbo | **Keep the BorgWarner EFR 7163.** 84% of choke and PR 3.42 of 3.6 at the design point — it is not used up. |
| Boost | 30 psi on E85 (its ceiling is 32.6 psi / ~419 whp) |
| Redline | **7,200 rpm**, 7,500 outer limit. 7,200→7,500 is worth +6 whp. Above 7,500 the gains are 1–3 whp. |
| Power | **404 whp / 505 crank** at 7,500 rpm |
| Core | **610 × 305 × 102 mm** bar & plate, single pass. Needs 137 mm clear front-to-back. |
| Predicted IAT | 70 °C (157 °F) at 30 psi, 32 °C ambient, 100 km/h ducted |
| Manifold | **Re-pair to 1+4 / 2+3 before any dyno tuning** |
| Boost control | Solenoid supply from a 1/8 NPT bung in the **cold-side charge pipe** |
| Machine billet end tanks? | Still a no-go. §18 unchanged. |

**What binds the redline** is the bottom end — rod ratio 1.516, 22.8 m/s mean piston speed at
7,500 rpm — not the head and not the VE. The Taylor Mach index stays under 0.55 to 8,000 rpm and
per-cylinder port demand peaks at 69 CFM against a ~245 CFM port. The head has margin; there is
simply nothing left to gain by the time the bottom end starts to complain.

---

## Earlier rounds, kept for the record

### Round two
Picked the (now withdrawn) G25-770, moved the design point from 25 to 30 psi, and killed the
billet end tank idea. Corrected round one's claim that raising the rev limit does not help — that
came from an assumed VE curve with no source, which round three confirms was the genuine outlier.

### Round one
Picked bar-and-plate over tube-and-fin (three public datasets disagree; the use case favours
bar-and-plate), 2.5 in piping both sides with a single taper at the 74 mm throttle body, and
established that **the ducting matters more than the core** — unducted to sealed-and-ducted is
worth ~37 °C, where the largest difference between core types is ~10 °C.

### Two corrections to the original brief
1. **Location.** The brief assumed Miami. "Toyota N Miami" is an online parts vendor; every
   ship-to is **Weaverville, NC 28787** (~2,100 ft). All math uses 32 °C / 93.87 kPa.
2. **Tube-and-fin is not generally better.** The tube-fin vendor found tube-fin better, the
   bar-plate vendor found bar-plate better, the independent tester found no difference.

---

## What's in this folder

| File | What it is |
|---|---|
| `intercooler-report.html` | **The report — open this** |
| `intercooler-report.round2.bak.html` | Before round three |
| `intercooler-report.round1.bak.html` | Before the turbo work |
| **`data/prior-turbo-research/`** | **The supplied earlier turbo research, preserved verbatim** — the shared model, 4 CSVs, the head-flow reference, and 15 charts |
| **`reconcile.py`** | Round three — forensic diff of the prior research (stage 1), then the unified model (stage 2) |
| **`unified_model.py`** | Round three — the model itself. One consistent set of constants, charge temperature coupled to airflow. |
| **`make_r3_chartdata.py`** | Emits `data/chartdata_r3.js`, the data block the round-three charts read |
| **`build_r3.py` / `build_r3_js.py` / `build_r3_open.py`** | One-shot scripts that spliced round three into the report. Kept for audit. |
| **`verify_r3.js`** | Verification harness. Checks all 27 charts mount, both calculators compute, defaults match the model, zero console errors, no external resources. |
| **`dump_r3_svg.js`** | Dumps the round-three charts to standalone SVG for visual inspection |
| `rpm_sensitivity.py`, `rpm_sens2.py` | Round two — VE models, redline sweep, head-to-head |
| `thermal.py` … `thermal4.py` | Rounds one and two — ε-NTU, heat soak, core size study |
| `endtank.py` | Round two — billet cost and machining time |
| `make_chartdata.py`, `verify.js`, `dumpsvg2.js` | Round two equivalents of the above |
| `build-inputs.csv` | Extracted build spec with source and confidence for each row |
| `data/r3png/`, `data/r3svg/` | Rendered round-three charts, for checking them outside the report |

### Re-running round three

```
python reconcile.py
python unified_model.py
python make_r3_chartdata.py
node verify_r3.js
```

`reconcile.py` prints the forensic diff — what the prior model's constant `K` actually contains,
the implied VE inside each supplied CSV, and the itemised walk from 511 whp to 466 whp.

---

## How the numbers were produced

- **Build inputs** — 64 parts invoices OCR'd (Tesseract 5.4), the `st185-link-ecu-config` repo
  read directly, and 145 prior Claude session transcripts keyword-scanned.
- **Airflow** — displacement × rpm × VE × manifold density, with **manifold density evaluated at
  the solved charge temperature**, iterated to convergence against the ε-NTU intercooler model.
  This is the step neither prior model performed.
- **VE** — a broad cam/plenum term × the Taylor inlet Mach index rolloff × a residual-gas penalty
  for exhaust backpressure. Anchored on the supplied cylinder-head flow reference.
- **Compressor efficiency** — for the four EFR turbos, from the prior research's digitization of
  the official BorgWarner maps (RMS 0.010–0.048 efficiency points). **The Garrett figures are
  modelled and are flagged as such in §21.6** — no official Garrett map was digitized anywhere.
- **Manifold pairing** — reconstructed from firing order (1-3-4-2) and cam duration (264°) alone,
  independently of the prior research, which it confirms exactly.
- **Verification** — the report's JavaScript run headless and cross-checked against the Python
  model. 27/27 charts render, both calculators compute, zero console errors, no external
  resources. Two deliberate model differences are documented in §21.13 rather than hidden.

## Error bands

Predicted temperatures ±5 °C. ΔP ±30%. **Power ±20 whp on the drivetrain factor alone.** The
manifold pairing *geometry* is exact; its *consequences* are worth ±50%. Bumper aperture
dimensions are estimated from adjacent known parts — **measure M1–M5 in §13 and §24 before
ordering anything.**

## Open questions

Sixteen, listed in §24 of the report. The three that block everything else:

1. **Measure the bumper aperture — now including 137 mm of depth** for the thicker core.
2. **Confirm the manifold pairing on the physical part.** §22's arithmetic is verified, but the
   claim that your manifold is 1+2 / 3+4 comes from the prior research and has not been checked
   by looking at it. Trace which two runners enter each scroll at the turbine flange.
3. **Re-make the manifold, fit an undivided housing, or leave it?** It should happen before any
   dyno tuning, and before judging the turbo.

**The cheapest way to check most of this report at once** is still one logged 3rd-gear pull with
MAP, rpm, charge IAT (An Volt 6 — planned, not yet wired) and ethanol content. Back-calculating
VE from it would settle the largest remaining modelling argument, since the prior research
contains three different VE curves and this report contains two more.
