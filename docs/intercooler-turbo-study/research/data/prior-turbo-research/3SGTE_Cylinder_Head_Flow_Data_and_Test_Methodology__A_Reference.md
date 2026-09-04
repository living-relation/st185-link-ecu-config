# 3S-GTE Cylinder Head Flow Data & Test Methodology — A Reference for VE Modeling on a 2.2L Hybrid Build

## TL;DR
- **28 inches of water (inH₂O) is the dominant US aftermarket flow-bench standard** — traced to Smokey Yunick, who (per his book *Power Secrets* and as recounted by David Vizard) started from an earlier 10" norm, tested in ~2" increments up to ~34", and found improvements only reliably showed on the dyno at 26–28". 25" is common on Superflow benches and much European/Japanese/Australian data. Convert between them with the square-root-of-pressure-ratio rule: CFM₂₈ = CFM₂₅ × √(28/25) = CFM₂₅ × 1.0583. [Speed-Talk](https://www.speed-talk.com/forum/viewtopic.php?p=122973)
- **The "250–292 CFM" range for a stock 3S-GTE head is misleading as a "stock" figure.** A genuinely stock 3S-GTE intake port flows roughly 240–250 CFM peak at 28" and only at ~0.45–0.50" lift — well beyond the ~0.32–0.35" the stock cam ever reaches. The ~292 number is actually a naturally-aspirated 3S-GE (Altezza) head measured at 25", not a turbo GTE head. Realistic per-port peak intake for a stock GTE head is **~240–250 CFM @ 28"**.
- **A VE curve peaking near 1.005 (≈100.5%) at 5500 rpm is plausible ONLY if it is a naturally-aspirated-basis VE.** On a turbo engine "raw" VE (mass referenced to atmosphere) routinely runs 150–200%+ and is set mostly by boost/pressure ratio, not head flow. If 1.005 is meant as the boosted number it is far too low; if it is the geometric/NA-basis filling it is realistic and slightly optimistic for HKS 264 cams at only 5500 rpm.

## Key Findings

1. **Test depression conventions.** 28" H₂O (≈1 psi; each inch ≈ 0.036 psi) is the de-facto US comparison standard; 25" is the traditional Superflow calibration point (with a ~0.586 discharge coefficient) and is common outside the US; 10" appears on small/older benches and kart/motorcycle work. Small-bore 4-cylinder heads are sometimes flowed at lower depressions purely because smaller benches lack the vacuum capacity to pull 28" through the port — this does not bias the port itself, but it makes the raw CFM read lower and non-comparable unless corrected.

2. **Correction math.** Flow scales with the square root of the pressure ratio: CFM_target = CFM_known × √(P_target / P_known). Exact for the bench orifice (flow ∝ √ΔP) but only approximate across large ratios, because a poppet valve's discharge coefficient shifts with pressure differential.

3. **Standard lift points.** US data is reported in 0.050"–0.100" increments (0.050 … 0.600"); metric data in 1mm steps. Because the stock 3S-GTE cam lifts only ~8.2–8.7mm (0.32–0.34"), flow numbers quoted at 0.500–0.600" are irrelevant to a stock-cammed engine and only partially relevant even with the HKS 264s (~9mm / 0.354").

4. **Stock valve/cam specs are well documented; port volumes in cc are NOT publicly documented for the 3S-GTE** — a genuine data gap requiring direct measurement.

5. **HP-from-CFM rules** (Vizard / SuperFlow: HP ≈ 0.257 × peak intake CFM@28" × cylinders) are naturally-aspirated tools; they set the *airflow ceiling of the head*, not boosted engine power, and understate forced-induction output.

## Details

### 1. Test pressure / depression conventions

**Dominant conventions and origin.** The 28" H₂O standard is attributed to Smokey Yunick. As David Vizard recounts (Muscle Car DIY, *Understanding Cylinder Head Flow Testing Procedures, Part 2*), Yunick "ran the gamut on this and declared that tests had to be done at a minimum of 28 inches of water (H2O) depression for a flow bench improvement to consistently show up as a power improvement on the dyno," and because he was so widely respected "this 28-inch measurement became an accepted standard for the performance-engine building community." [Muscle Car DIY](https://www.musclecardiy.com/cylinder-heads/understanding-cylinder-head-flow-testing-procedures-part-2/) His book *Power Secrets* (Yunick with Larry Schreib, 1983) describes moving up from the earlier 10" norm and testing in ~2" increments, finding best accuracy in the 26–28" band. One inch of water ≈ 0.036 psi, so 28" ≈ 1.0 psi. [CamaroZ28](https://www.camaroz28.com/forums/advanced-tech-38/where-did-28-inches-water-come-340787/) Superflow's benches historically calibrated at 25" H₂O with a ~0.586 discharge coefficient, which is why much data — and most European/Japanese/Australian data — is reported at 25". Lower depressions (10", 15") appear on older/lower-powered benches.

**Why some small 4-cyl heads get tested low.** It is bench capacity, not head design: "some benches use 25"… Because they're not powerful enough to draw 28" from a big port." At 400 CFM/28" a Superflow draws ~30 A at 230 V; doubling depression to 56" raises flow only ~42% but nearly triples power draw. [For A Bodies Only](https://www.forabodiesonly.com/mopar/threads/what-is-the-best-pressure-to-use-for-flow-bench-testing.586228/)

**Does low-depression testing bias published numbers?** The port's behavior is largely depression-independent for well-behaved ports ("Ports that behave don't change at all — cfm stays about same whether there is 35" or 5" depression"), [Speed-Talk](https://www.speed-talk.com/forum/viewtopic.php?t=12038) but some ports are genuinely depression-sensitive. The real bias is *comparability*: a number taken at 10" or 25" reads lower than the same port at 28", so any figure quoted without its test depression is nearly meaningless. As Harold Bettes put it: "if someone attempts to impress you with an airflow number always ask at what test pressure the number was collected." [Wordpress](https://performancespecialties.wordpress.com/2013/06/09/flow-bench-analysis/)

**The correction formula (worked examples).** CFM₂ = CFM₁ × √(P₂/P₁).
- **25" → 28":** multiplier = √(28/25) = √1.12 = **1.0583**. Example: 250 CFM @ 25" → 250 × 1.0583 = **264.6 CFM @ 28"**.
- **28" → 25":** multiplier = √(25/28) = **0.945**. Example: 264.6 × 0.945 = 250 CFM (round-trip check).
- **10" → 28":** √(28/10) = 1.673. A 150 CFM @ 10" port → **250.9 CFM @ 28"**.
- **Bettes' published example:** √(28/60) = 0.683, so 450 CFM @ 60" = 307.4 CFM @ 28"; the reciprocal 1/0.683 = 1.464 converts 28"→60". [Wordpress](https://performancespecialties.wordpress.com/2013/06/09/flow-bench-analysis/)
Caveat from multiple bench operators: the rule is exact for the orifice/manometer physics but only approximate across a head because "the efficiency of a poppet valve is dependent of the pressure differential. So 25 to 28 probably no problem, 10 to 150 probably not so good." [Mini Engine Stuff](https://aseriesmodifications.wordpress.com/category/flow-testing/)

**Why real engines don't see 28".** A running engine's instantaneous port depression is high at low lift (200"+ H₂O) and low at high lift (~50" falling to ~15–20" on a well-developed head at the power peak). 28" was chosen (per Ken Sperry/Pat Baer seminar notes) because it "mimics the average pressure drop through the intake cycle when an engine is peaking its power curve." A very good unrestricted intake shows only ~1" Hg (~0.5 psi ≈ 14" H₂O) of manifold depression at the power peak.

### 2. Standard lift points & stock 3S-GTE valvetrain specs

**Lift increments.** Conventionally 0.050", 0.100", 0.150", 0.200", 0.250", 0.300", 0.350", 0.400", 0.450", 0.500", 0.550", 0.600" (imperial) or 1mm steps (metric).

**Maximum useful lift.** For the 3S family, flow-relevant gains fall off sharply beyond ~0.400" (≈10mm): a knowledgeable porter on the related platform noted "the gains are sharply reduced at .400 lift." Above that the port stalls (flow plateaus and can reverse/turbulate) — de-shrouding a bigger valve on the architecturally-similar Mini A-series head showed "the flow numbers in the high lift area are not much better even though the valve is significantly larger… the port gets quite noisy after about 5mm lift."

**Stock valve lift and duration by generation** (Toyota factory / widely corroborated references):

| Generation | Chassis | Duration (in/ex) | Valve lift (in/ex) |
|---|---|---|---|
| Gen 1 3S-GTE | ST165 | 232°/232° | 7.15 mm / 7.15 mm (0.281") |
| Gen 2 3S-GTE | ST185 / SW20 Rev1–2 | 236°/236° | 8.2 mm / 8.2 mm (≈0.323–0.335") |
| Gen 3 3S-GTE | ST205 / SW20 Rev3 | 240°/236° | 8.7 mm / 8.2 mm (0.343"/0.323") |
| Gen 4 3S-GTE | Caldina ST215 | 248°/246° | 8.75 mm / 8.2 mm |

(MR2OC's measured cam-spec sheet lists the Gen 2 stock cam at "Advertised duration 236 degrees… Max Lift: 8.52mm (0.335")" and the Gen 3 intake as 240° with ~0.5mm more lift — consistent with the table above.)

**HKS 264 cams vs stock.** The common 3S-GTE HKS 264 profile (exhaust cam PN 2202-RT064, marketed as "Step 2 264°/9mm" by Real Street Performance and RZCrew Garage) is **264° advertised duration with ~9.0 mm intake / 8.95 mm exhaust lift**; HKS's "duration @ 1mm lift" figure is **224°**, and forum cam cards list max lift ~9.2mm. Versus a Gen 2 stock cam (236°/8.2mm) that is roughly **+28° duration and +0.8mm lift**; versus Gen 3 (240°/8.7mm) it is **+24° duration and only ~+0.3mm lift**. So even with HKS 264s peak valve lift is only ~9mm (0.354"), meaning flow-bench data above ~0.400" lift remains beyond what your cams reach.

**Stock valve diameters and stem** (all GTE generations share these): intake head **33.5 mm**, exhaust head **29.0 mm**, both on **6 mm stems** — confirmed across Ferrea (intake F1863P 33.5mm / exhaust F1865P 29mm STD), Brian Crower (BC3352/BC3353), and GSC Power-Division standard-size valve spec tables. (The NA 3S-GE BEAMS uses larger ~35.0–35.5mm intake / 30.0–30.1mm exhaust valves on ~5.5mm stems — relevant when comparing flow.)

**Port volumes.** Publicly documented cc port volumes for the 3S-GTE could not be found in the forum/porter record — a genuine data gap. What *is* documented is port *shape*: Gen2/ST185 intake ports are large rectangular TVIS ports (~48×35mm) that "taper quite dramatically"; Gen3/ST205 ports are ~10mm longer, lower and more oval (~56×33mm), no TVIS. The Gen2 intake has larger cross-section (higher flow, lower velocity); the Gen3 intake is smaller (higher velocity, better midrange), and the Gen3 exhaust flows slightly better.

### 3. Published flow numbers (organized by lift, with test depression labeled)

**⚠️ Source-quality note:** No complete, fully-tabulated stock 3S-GTE intake+exhaust flow sheet with all conditions stated exists in the public record. The best available are the Gen 1 table below (stated 28") and the stock-Gen2 peak figures. Where depression is unstated, it is flagged.

**Stock Gen 1 (ST165) 3S-GTE — stated "at 28 inches of water," stock-size valves** (forum-measured, MR2OC):

| Lift (in) | Intake CFM @28" | Exhaust CFM @28" |
|---|---|---|
| 0.100 | 80.7 | 70.3 |
| 0.200 | 160.3 | 142.1 |
| 0.300 | 216.9 | 185.3 |
| 0.350 | 228.7 | 186.8 |
| 0.400 | 238.3 | 188.2 |

**Mildly ported Gen 1 (stock valves), same source, 28":** intake rises to 235.3 @0.350" and 247.1 @0.400"; exhaust ~200–201 @0.350–0.400".

**Stock Gen 2 (ST185/SW20) 3S-GTE — peak figures:**
- Professional Superflow-600 operator, **28"**: "a stock Gen 2 head flows in the 240 range on the intake ports and 175 on the exhaust" (peak/near-peak).
- Member scanned flow test: "just under 250 CFM at just under 0.5" lift" (stock Gen 2; depression on original chart, not restated in surviving text).

**Vendor claims (depression NOT stated — treat with caution):** One porter quoted ST185 stock intake at 268 CFM and ~300 CFM ported; another claimed 305 (Gen1) / ~320 (Gen2) ported. None state test depression or lift, so they are not directly comparable and should be excluded from VE calibration.

**Reference — NA 3S-GE Altezza head (NOT a GTE head), stated "25 inches of water," tested by HSD, ~35mm intake / ~30mm exhaust valves, ported:**

| Lift (in) | Intake CFM @25" | (→ @28", ×1.0583) |
|---|---|---|
| 0.100 | 79.79 | 84.4 |
| 0.200 | 157.8 | 167.0 |
| 0.300 | 218.3 | 231.0 |
| 0.400 | 263.1 | 278.4 |
| 0.450 | 276.5 | 292.6 |
| 0.500 | 285.1 | 301.7 |
| 0.550 | 291.9 | 308.9 |

Exhaust for this head @25": 69.0 / 133.1 / 171.8 / 190.1 / 195.9 / 201.3 CFM at 0.100–0.500".

**Is 250–292 CFM plausible for a stock GTE head?** Partly. The ~240–250 low end is a credible measured *peak intake* at 28" for a stock Gen2 head, but it occurs at ~0.45–0.50" lift — far above the stock cam's 0.32". The ~292 high end is the NA 3S-GE head at 25" (≈309 @28"), a different head with bigger valves and porting; quoting it as "stock 3S-GTE" is wrong. **Realistic stock GTE per-port peak intake ≈ 240–250 CFM @28"; at the stock cam's actual ~0.32" lift the port is only flowing ~215–225 CFM.** For a 2.0L 4-valve turbo head those numbers are sensible — a ~250 CFM peak intake port feeding a 500cc cylinder is generously sized, which is precisely why the Gen2 is criticized for low port velocity once TVIS is removed.

**3S-GE comparison (better documented, shared architecture).** The NA BEAMS/Altezza head is the flow benchmark: stock port ~213 CFM, mild porting ~251 CFM @0.500"; [toymods](https://www.toymods.org.au/forums/threads/27689-port-flows-of-3sge-BEAMS) the HSD-ported example reached ~292 CFM @25" (~309 @28"). BEAMS/3S-GE heads have steeper, straighter ports and larger valves and are widely considered a better-breathing casting than any GTE head, which is why some high-rpm builders start there. GTE and GE heads share bore spacing, valve angle, and combustion-chamber architecture but differ in port size/shape and valvetrain (GTE Gen2 = over-bucket shims, Gen3 = under-bucket).

### 4. Using flow data for VE estimation

**CFM→HP rules and their assumptions.** The canonical rule (David Vizard / SuperFlow) is **HP = 0.257 × peak intake CFM@28" × number of cylinders** (≈2.06 hp per peak CFM on a V8). SuperFlow's SF-110 manual expressed it as *Flow@10" × 0.43 × cylinders*; the 0.257 factor is the 28" equivalent, and TorqStorm gives the inverse form "Horsepower ÷ # of cylinders ÷ 0.257 = Airflow @ 28 inches H2O." TorqStorm rates it "exceptionally accurate on naturally aspirated engines to around 700 horsepower and 7,000 rpm… Once above those values, the rate it skews increases. The airflow value used must be achieved at 28 inches of H2O." Applied to a stock GTE head: 0.257 × 245 × 4 ≈ **252 hp NA ceiling**. **These are NA rules** — they estimate the head's airflow ceiling at atmospheric pressure and do not account for boost. On your turbo build the head is fed compressed air, so actual power far exceeds the NA-rule figure; the rule instead confirms the head can support far more than a stock NA engine needs and is unlikely to be your limiter until high boost/rpm.

**Engine airflow demand vs bench flow.** Engine demand (four-stroke): CFM = (CID × RPM × VE) / 3456. For your 2188.8cc (133.6 CID) engine at 7500 rpm and VE≈1.0 NA-basis, demand ≈ (133.6 × 7500 × 1.0)/3456 ≈ **290 CFM total ≈ 72 CFM/cyl of actual throughput** — but that is volumetric throughput, not directly the same quantity as a 28" bench number (a steady-state potential at a fixed ~1 psi drop). Under boost the *mass* demand multiplies by the pressure ratio: at ~2.4 bar absolute (PR≈2.4) the engine ingests ~2.4× the mass, so "raw" VE (mass basis referenced to atmosphere) runs 150–200%+. A running engine's port sees a *lower* average depression (~15–20" at the power peak on a good head) than the 28" bench; healthy port air speed is ~200–400 ft/s and should stay below Mach ~0.5 at the choke point to avoid a VE nosedive.

**Sanity-checking a VE peak of 1.005 @5500 rpm.** Interpretation is everything:
- **If NA-basis** (charge relative to atmospheric density — the geometric filling before boost is multiplied in): **1.005 (100.5%) at 5500 rpm is realistic and slightly optimistic** for HKS 264 cams on this head. Good mild-cam 4-valve turbo heads commonly peak ~95–105% NA-basis, and 5500 rpm is a reasonable peak location given 264° cams and the long 91mm stroke (which favors mid-rpm filling). It should then fall off toward 7500 rpm as the ~250 CFM ports and 9mm lift become limiting.
- **If boosted/raw-basis:** 1.005 is far too low — raw VE under boost must exceed 100% roughly in proportion to the pressure ratio (e.g. ~180–200% at PR≈1.9–2.0). A 1.005 peak would imply essentially no boost.

Cross-check via the airflow identity: at 5500 rpm, VE=1.005, 133.6 CID → NA-basis demand ≈ (133.6×5500×1.005)/3456 ≈ **214 CFM total ≈ 53 CFM/cyl**, comfortably within the port's ~245 CFM@28" capacity. This confirms the head is not the bottleneck at 5500 rpm, and the peak location is physically sensible. E85's evaporative charge-cooling raises effective VE modestly (denser charge), consistent with a peak at or just above 1.00.

## Recommendations

1. **Label every flow figure with its test depression before using it.** Convert all to one basis (28" recommended) via CFM₂₈ = CFM₂₅ × 1.0583. Discard any figure lacking a stated depression AND lift — this removes the "268/300/320" vendor claims from your VE work.
2. **Anchor the head at ~245 CFM intake / ~180 CFM exhaust peak @28" (stock Gen2), and ~215–225 CFM at the stock 0.32" lift.** With HKS 264s reaching ~9mm (0.354"), use the **0.300–0.400" rows** (216–238 CFM intake @28" from the Gen1/Gen2 data) as your realistic in-service port-flow band — NOT the 0.500"+ numbers, which your cam never reaches.
3. **Treat the 1.005 @5500 peak as an NA-basis figure and validate against logged MAP/IAT/injector data.** Back-calculate VE from measured airflow: "raw" VE should land ~150–200% at full boost; "adjusted" VE (boost pressure entered as the reference pressure) should sit ~90–105%. If your model's 1.005 is already the boosted number, it is wrong by the pressure ratio and needs rescaling.
4. **Expect the port — not the cam — to limit near 7000–7500 rpm.** Model VE rolling off above ~6000 rpm as the ~250 CFM ports and 9mm lift cap out. If dyno/log data shows VE holding flat to 7500, suspect the model; if it droops, that is physically expected and your ~7500 ceiling is appropriate.
5. **For the current combo, prioritize cam timing/centerline and boost/exhaust tuning over chasing bench CFM** — the stock GTE ports already exceed mid-range demand. Save head porting/valve work for when you raise the power or rpm target.

**Thresholds that change the recommendation:** if peak power target rises above ~450–500 whp — where the stock Gen2 intake's ~245 CFM/port and small plenum start to choke (the stock Gen2 plenum is documented to "struggle with flow… above 350whp") — move to a ported head + larger plenum/throttle body. If you raise the rev ceiling above ~8000 rpm, the 9mm HKS lift and ~250 CFM ports become the hard limit, requiring higher-lift cams (e.g. Kelford/GSC ~10.5–11mm) plus porting.

## Caveats
- **The single biggest data-quality issue: almost no stock 3S-GTE flow sheet online states all of its conditions.** The Gen1 table (28", stated) and the stock-Gen2 peak figures are the most trustworthy; everything else is either unstated-condition vendor claims or the NA 3S-GE head being conflated with the turbo head.
- **Port volumes in cc are undocumented** for the 3S-GTE in the public record. If you need them for a 1-D engine simulation, they must be cc'd directly on your head.
- Forum flow numbers come from different benches, operators, and calibration standards; absolute CFM can vary ±5–10% bench-to-bench. Use them for *shape/trends* and relative comparison, not absolute VE calibration.
- The square-root depression correction is approximate across large pressure ratios and for depression-sensitive ports; treat 25"↔28" conversions as solid but anything spanning 10"↔28"+ as rough.
- CFM→HP rules are naturally-aspirated tools; do not use them to predict boosted output — only to confirm the head is not the airflow bottleneck.
- Whether 1.005 is NA-basis or boosted-basis VE fundamentally changes its interpretation; confirm which convention your model uses before trusting the peak. Note that your stated peak location (5500 rpm) is well below your 7500 rpm ceiling, which is consistent with a torque-biased mid-range build on a long-stroke engine but means the top-end VE (and therefore top-end power) hinges on how gracefully the ~250 CFM ports and 9mm lift let the curve taper.