# Toyota 3S-GTE Hybrid Build — Two-Topic Technical Research Report
*(5S-FE block + 3S-GTE head hybrid, 87.5mm × 91.0mm, 2188.8cc, HKS 264 cams, 7500 rpm, E85, EFR 7163-G, ~465–467 whp target — 1991 Celica ST185)*

## TL;DR
- **Topic 1 (head airflow):** The "250–292 CFM stock" note conflates two different heads and two test pressures — the ~292 traces to a *ported 3S-GE BEAMS intake at 25″ H₂O*, while the ~250 is a *stock Gen 2 3S-GTE intake at ~0.5″ lift at an undocumented depression*. A realistic stock Gen 2 3S-GTE intake peaks around **240–268 CFM** (best assessed as referenced to 25–28″ H₂O, **not** 10″); exhaust ~175 CFM. At the target power the head is **adequate but the tightest-margin component**, not a hard wall — porting to ~300 CFM lets you hit 465 whp at meaningfully lower boost.
- **Topic 2 (coolant plumbing):** OEM 3S-GTE turbo coolant connections are **banjo-style, most commonly cited as M14×1.5** (verify with calipers — one builder measured ~16mm/M16×1.5). The **EFR 7163 bearing-housing water ports are confirmed M14×1.5**, and only two of the four are used. The cleanest build path is banjo-to-6AN adapters at both ends, or a welded -6AN bung / Swagelok tube-to-AN on the cut OEM hard line.
- **Compatibility:** The EFR *requires* diagonal flow — coolant in at a bottom port, out the opposite top port — for air purging and post-shutdown thermosiphon. The OEM MR2/Celica circuit does **not** automatically deliver that geometry, so you must deliberately route feed→lower port and return→opposite-upper port with the return rising back toward the engine.

---

# TOPIC 1 — 3S-GTE Cylinder Head Airflow

## Key Findings
1. The "250–292 CFM stock" claim is **not a coherent single-source stock figure** — it mixes a ported BEAMS number with an unpressurized stock 3S-GTE number.
2. Realistic **stock Gen 2 3S-GTE intake is ~240–268 CFM peak; exhaust ~175 CFM peak**; test depression is poorly documented in every public source.
3. The head is **adequate for ~465 whp on E85 at 7500 rpm but works near its comfortable ceiling** in stock form. It is not a hard flow limiter at this power, but it has the least headroom of the major components.

## Details

### 1.1 Origin and likely test pressure of the "250–292 CFM" figure
- **The "~292" originates from a ported 3S-GE BEAMS (NA) head, not a stock 3S-GTE turbo head.** A Toymods flow test of an Altezza 3S-GE BEAMS head (ports worked by HSD; 35mm intake / 30mm exhaust valves) at **25 inches of water** produced intake CFM of 79.79 / 157.8 / 218.3 / 263.1 / 276.5 / 285.1 / 291.9 at 0.100″/0.200″/0.300″/0.400″/0.450″/0.500″/0.550″ lift. The 291.9 CFM @ 0.550″/25″ is the "292."
- **The "~250" is a stock Gen 2 3S-GTE intake datapoint** posted on MR2 Owners Club ("just under 250 CFM at just under 0.5″ lift"), but the poster and repliers explicitly did not know the test depression.
- **Disregard generic web hits:** Many "230/250/292 CFM" results actually refer to the **Chevrolet 250/292 inline-six** and #292 castings, not Toyota — a search-engine false match.
- **Best assessment:** The 3S figures are most consistent with **25″ H₂O** (the BEAMS number) and **28″ H₂O** (Chris K.'s Superflow 600 work). There is no evidence any 3S number was taken at 10″. Treat "250–292 stock" as **not verified as stock and not at a single stated pressure.**

### 1.2 Measured 3S-GTE flow datapoints (with sourcing caveats)
No fully itemized 0.100″→0.550″ intake-AND-exhaust curve for the 3S-GTE *turbo* head at a stated depression exists in any openly accessible source; the one known Gen 2 chart is behind the MR2OC paywall (HTTP 402). Recovered datapoints:

| Gen | Port | Lift | CFM | Depression | Source |
|-----|------|------|-----|-----------|--------|
| Gen 1 (ST165) | Intake | 0.350″ | ~200 stock / ~240 ported | not stated | MR2OC user (flowed an ST165 head) |
| Gen 2 (ST185) | Intake | peak | ~240 stock | Superflow 600 (not stated in text) | Chris K. (EngineLogics) |
| Gen 2 (ST185) | Exhaust | peak | ~175 stock | Superflow 600 (not stated) | Chris K. |
| Gen 2 (ST185) | Intake | peak | 268 stock / ~300 ported | not stated (phone quote) | Chris K. via All-Trac |
| Gen 2 (ST185) | Intake | ~0.5″ | ~250 stock | not stated | MR2OC "stock 3sgte head flow cfm" |
| Gen 2 (ST185) ported | Intake | peak | ~310 | not stated | MR2OC comparison thread |

**Reference curve (3S-GE BEAMS, ported, 25″ H₂O — NOT the turbo head, but the only complete stated-depression 3S curve found):** intake 79.8→291.9 CFM (0.100″→0.550″); exhaust 69.0 / 133.1 / 171.8 / 190.1 / 195.9 / 201.3 (0.100″→0.500″).

### 1.3 Valve sizes, chamber and port volumes by generation
- **Valve head diameters (all 3S-GTE generations, essentially unchanged):** intake **33.5 mm**, exhaust **29.0 mm**. Confirmed by the Brian Crower catalog — "BC3352 – Toyota 3SGTE Intake Valves (33.5mm / STD)" and "BC3353 – Toyota 3SGTE Exhaust Valves (29mm / STD)," 6mm stem — and by Ferrea and GSC listings. +1mm oversizes (34.5 / 30 mm) are offered.
- **Cam lift (context for useful flow range):** Gen 1 7.15 mm (~0.281″); Gen 2 8.2/8.2 mm (~0.323″); Gen 3 8.7/ [Toymods](https://www.toymods.org.au/forums/threads/4007-FAQ-GEN-3-3sgte-Differences-mods-please-post-in-FAQ) 8.2 mm intake/exhaust. Practical valvetrain ceiling is around 0.400″ lift, so flow quoted at 0.500–0.600″ is largely academic for this head — your HKS 264 cams (higher lift than stock) push the useful range up but the port shape still governs.
- **Combustion chamber volume:** measured/quoted at **~49–51 cc** for Gen 2 (CP uses 49 cc; one measured chamber 51.3 cc; another 49.5 cc). Gen 3 is sometimes *calculated* higher (~62 cc in one spreadsheet) but this is disputed; most builders use ~49–50 cc.
- **Compression ratios:** Gen 1 8.5:1, Gen 2 8.8:1, [Motor Reviewer](https://www.motorreviewer.com/engine.php?engine_id=152) Gen 3 8.5:1, Gen 4/5 9.0:1 (confirmed by the 8020 Automotive 3S-GTE guide).
- **Port volumes:** No reliable published cc figures for 3S-GTE intake/exhaust port volumes were found — **data gap.** Gen 2 is widely reported to have larger, more tapered intake ports (higher bench peak) than the smaller/oval Gen 3 ports (better velocity).

### 1.4 Ported vs stock bounding
Consistent across sources: stock Gen 2 intake ~240–268 CFM peak; ported ~300–310 CFM peak — roughly a **+15–25% intake gain from porting.** So the upper end of "250–292" reflects *ported/BEAMS* work, and a genuine *stock* Gen 2 3S-GTE intake is realistically in the **~240–268 CFM** band.

### 1.5 Flow-depression correction methodology
Flow scales with the square root of the pressure ratio:

**CFM₂ = CFM₁ × √(P₂ / P₁)** (P = test depression, inches of water)

Useful multipliers:
- 25″ → 28″: × √(28/25) = **×1.0583**
- 10″ → 28″: × √(28/10) = **×1.673**
- 28″ → 25″: × √(25/28) = **×0.945**
- 25″ → 10″: × √(10/25) = ×0.632

Example: the BEAMS 291.9 CFM @ 25″ ≈ **308.9 CFM corrected to 28″.** Caveat from flow-bench practitioners: this is a first-order approximation — ports can go turbulent at higher depressions and under-scale, so cross-bench comparisons remain approximate.

### 1.6 Airflow-requirement sanity check (is the head a limiter at ~465 whp / E85 / 7500 rpm?)
**Actual volumetric demand:** displacement 2188.8 cc; per-cylinder swept 547.2 cc. At 7500 rpm each cylinder inducts 3750 times/min. At 100% VE the actual throughput is ~2.05 m³/min per cylinder ≈ **~72–73 CFM per cylinder of real air movement** (at operating density — *not* a 28″ bench number).

**NA HP-per-CFM rule of thumb:** HP per cylinder ≈ 0.26 × (peak intake CFM at 28″); for a 4-cylinder, NA crank HP ≈ 1.04 × CFM. (Equivalent forms: 0.43×CFM@10″ or 0.275×CFM@25″ per cylinder.)
- Stock head at ~245 CFM (28″) → NA potential ≈ 0.26 × 245 × 4 ≈ **~255 crank hp NA** — consistent with the real NA 3S-GE making ~200–215 hp on ~200 CFM ports, so the rule checks out here.

**How the rule changes boosted:** For the same VE, air *mass* through a fixed port scales with absolute manifold pressure, so a head worth X NA hp supports roughly **X × (manifold absolute ÷ atmospheric)** boosted hp. Target ~465 whp AWD ≈ ~545–565 crank hp (15–18% AWD driveline loss). That implies pressure ratio ≈ 545/255 ≈ **~2.1 — about 1.1 bar / ~16 psi boost.**

**Mass-flow cross-check:** ~50 lb/min air ≈ ~500 crank hp at ~10 hp per lb/min — consistent with the target and with the EFR 7163's ~60 lb/min capability.

**Verdict:** At ~16–17 psi on the EFR 7163, a **stock-flowing 3S-GTE head can support ~465 whp on E85 — adequate, but working near the top of its comfortable range.** It is not a hard wall at this power, but it is the least-headroom component. **Porting the intake to ~300 CFM would achieve the same power at lower boost (~2.1 → ~1.7 PR), improving spool, EGTs and reliability.** The exhaust port (~175 CFM stock) is proportionally the weaker side and gains most from a quality 3-angle valve job.

**On the VE ≈ 1.005 @ 5500 rpm assumption:** A trapped VE marginally above 1.0 for a well-tuned, intake-tuned, boosted engine is a reasonable modeling input, but it is an **estimate, not measured data** — validate against a dyno/MAF log before treating it as fact.

---

# TOPIC 2 — OEM 3S-GTE Turbo Coolant Line → AN Adapter Sourcing

## Key Findings
1. OEM 3S-GTE turbo coolant connections are **banjo-style**, thread most commonly cited **M14×1.5** (some builders measure ~M16×1.5 — verify).
2. The **EFR 7163 bearing-housing water ports are M14×1.5** (confirmed), and only two of the four are used; Turbosource sells a purpose-made pair of **-6AN adapters with 16mm crush washers**.
3. The **EFR diagonal-flow requirement is real and OEM MR2/Celica routing is not automatically compatible** — you must deliberately achieve in-low / out-opposite-high geometry.

## Details

### 2.1 OEM 3S-GTE turbo coolant line configuration (Gen 2 ST185 / MR2 SW20)
- **Connection type:** Banjo fittings/bolts at the turbo, fed by brazed steel hard lines. Toyota's EPC/BGB names them "Water By-Pass Pipe No. 1" (a two-pipe brazed assembly) plus a "No. 2" bypass pipe at the oil cooler; the No. 1 pipe seals to the water pump with an O-ring + flange gasket.
- **Banjo bolt thread:** **M14×1.5** is the most commonly cited spec for Toyota CT-series turbo coolant banjo bolts and matches the mainstream aftermarket "M14×1.5 turbo coolant banjo" ecosystem (Garrett GT25/28/30/35 coolant ports are also M14×1.5). **However, at least one builder measured the Toyota water banjo at ~16mm OD (suggesting M16×1.5).** **Measure your specific bolt before ordering.** For reference, the OEM *oil* feed adapter on the block is M18×1.5 (per the turbomr2 rebuild writeup) — do not confuse the two.
- **Toyota part numbers:** Toyota's catalog names the coolant hard lines but does not surface clean public part numbers for the turbo coolant *banjo bolts* specifically; the community references OEM CT26 water pipes/banjos as dealer-available. Note: M14×1.5×25mm banjo-bolt and crush-washer part numbers circulating in forums (e.g. MD314117 / MF660065) are **Mitsubishi/DSM** numbers and should not be assumed identical to Toyota. **Partial data gap on exact Toyota banjo-bolt PNs — verify at a Toyota parts counter.**
- **Gen 3 (ST205/SW20) difference:** The CT20b relocates the coolant ports vs. the CT26, so hard-line routing differs; the connection style is the same family but the pipes are **not interchangeable** between CT26 (ST185) and CT20b (Gen 3).

### 2.2 OEM hard-line tube OD
No manufacturer-sourced exact OD was found. **Reasoned estimate:** based on builders replacing the section with 3/8″ (≈9.5mm) OD stainless and typical Toyota metric coolant hard-line sizing, the OEM turbo coolant hard line is most likely **~8mm OD (possibly up to ~10mm / 3/8″)**. **This is an estimate — measure the actual pipe at the intended cut point before selecting a compression or weld-on fitting.**

### 2.3 Adapter options to reach -6AN (vendors / part numbers)

**A. Banjo-bolt-to-AN adapters (simplest; recommended at the turbo):**
- **EFR turbo side — purpose-made:** **Turbosource "BorgWarner EFR 6AN coolant adapter fittings"** — a pair of -6AN adapters with 16mm crush washers; product text: *"One pair of Borgwarner EFR 6AN coolant adapter fittings with 16mm crush washers. These fit all b1 and b2 EFRs with either steel or aluminum CHRA. Coolant must flow diagonally through CHRA."* Alternatives: **AGP Turbo "EFR and GT Ball Bearing Water Line Banjo Set"** (2× M14 banjo bolts, 2× M14 banjo fittings with 3/8″ hose barb, 4× copper crush washers); **Gryphontek "BorgWarner EFR Turbo Water Fitting Kit"** (4AN/6AN, banjo bolt, copper washers).
- **OEM Toyota side — M14×1.5 banjo to -6AN:** **Kinugawa "Turbo Coolant Banjo Bolt kit M14×1.5 to -6AN"** (Garrett GT28/30/35 pattern; Amazon/Walmart; -4AN versions also exist). **Vibrant Performance Single Banjo Adapter Assembly** (male AN flare with metric bolt, catalog V1198). If yours measures **M12×1.25**: Vibrant single male banjo -6AN/M12×1.25, or **Radium AN ORB swivel banjo (12mm)** via Summit, or Russell M12×1.25 banjo adapters (AutoZone).

**B. Metric hard-line flare-to-AN:** Few off-the-shelf options match the exact OEM flare; most builders abandon the OEM flare for banjo adapters or cut-and-adapt.

**C. Compression-fitting-to-AN (if reusing cut hard line):** Swagelok/Parker tube-to-AN (e.g. 3/8″ tube × 3/8″ NPT, then NPT→-6AN) is proven — one builder used *"3/8 tube × 3/8 npt stainless Swagelok fittings at the turbo and .375 OD × .319 ID stainless tubing plumbed to the stock coolant pipes."* Size the fitting to the measured tube OD (likely 8mm or 3/8″).

**D. Weld-on / braze-on AN bungs (recommended if retaining OEM hard-line routing):** Cut the OEM steel hard line and TIG a steel -6AN weld bung — clean, permanent, flow-unrestricted (Vibrant, ATP, generic).

**E. Purpose-made 3S-GTE coolant kits:** Kinugawa and MAMBA sell 3S-GTE/CT26 turbo *water line kits*, but they are built for CT-series journal-bearing turbos, not the EFR banjo geometry — usable as a parts source (banjo pipes, barbs) rather than a drop-in EFR solution.

### 2.4 Practical guidance, flow adequacy, and pitfalls
- **OEM bypass-pipe flow adequacy:** The OEM circuit was sized to cool a journal-bearing CT26; it is generally regarded as **adequate for an EFR bearing housing** provided it isn't necked down. The EFR ball-bearing cartridge needs steady coolant for post-shutdown heat-soak protection, not high volume. Use **-6AN throughout** for margin.
- **No restrictors:** BorgWarner/Full-Race explicitly warn *"Do not use an external oil supply restrictor! All oil flow restriction that is required for the ball bearing and sealing system is accomplished internally within the bearing housing."* Keep the **coolant circuit unrestricted** as well.
- **Common pitfalls:** aluminum AN fittings can develop pinhole leaks at tight elbows (use stainless at the turbo); OEM 3S banjo-bolt access is notoriously tight (27mm socket; remove the coolant pipe for access); confirm crush-washer sizes (14mm/16mm) and re-torque after heat cycles.

### 2.5 EFR diagonal-flow compatibility with OEM routing
- **BorgWarner/Full-Race requirement (confirmed, verbatim):** *"Water flow needs to enter the bearing housing through a bottom port on one side, and exit the top port on the opposite side. Water cooling is particularly critical on EFR turbos equipped with aluminum bearing housings!"* Full-Race further notes the **water ports are M14×1.5 and only two of the four are needed** (plug the other two). Purpose: air purging and post-shutdown thermosiphon.
- **OEM MR2/Celica compatibility:** The factory circuit was **not** designed around the EFR's diagonal in-low/out-high-opposite geometry (the ST165 uses opposite-side feed/return with the return climbing to the radiator top tank; the MR2/ST185 layout differs). **Plan your AN routing to satisfy the EFR rule regardless of OEM habit:** take the OEM feed to a *lower* EFR coolant port on one side, and run the *opposite-side upper* port as the return, routed so the return line rises back toward the engine/coolant system to enable thermosiphon. Confirm the OEM feed tap is at/below turbo centerline and the return climbs — if the OEM return would trap coolant or run downhill, re-route it. **This is a design step, not a bolt-on.**

---

## Recommendations

**Topic 1 (head):**
1. **Treat the head as adequate but the tightest-margin component.** Proceed with the EFR 7163; expect ~16–17 psi to reach 465 whp on a stock-flowing head.
2. **Port the intake to ~300 CFM and do a quality 3-angle exhaust valve job** to hit the target at lower boost (~1.7 PR), with better spool and cooler EGTs. Prioritize the exhaust side (~175 CFM stock is the weak link).
3. **Flow-test your actual head at 28″ H₂O** across 0.100–0.400″ lift (intake and exhaust) before finalizing the model — this replaces the unreliable "250–292" note.
4. **Validate VE ≈ 1.005 on the dyno**; do not treat it as measured until confirmed.
   - *Threshold that changes the plan:* if measured stock intake flow is below ~230 CFM @ 28″, porting becomes effectively mandatory for the target; above ~270 CFM, mild work suffices.

**Topic 2 (coolant plumbing):**
1. **Measure first** — OEM banjo-bolt thread (M14×1.5 vs M16×1.5) and hard-line OD (8mm vs 10mm/3/8″) with calipers.
2. **At the EFR:** buy the Turbosource EFR -6AN coolant adapter pair (16mm crush washers) or the AGP EFR banjo set; the EFR ports are M14×1.5 and you use only two of four (plug the rest).
3. **At the OEM side:** if reusing the OEM banjo, use an M14×1.5 (or measured size) banjo-to-6AN adapter (Kinugawa/Vibrant). If cutting the OEM hard line, **weld a -6AN bung** or use a Swagelok tube-to-AN + NPT-to-AN adapter sized to the measured OD.
4. **Enforce the EFR diagonal geometry** (in low, out opposite/high, return rising) even if it means re-routing OEM lines. Use -6AN throughout, no restrictors, stainless fittings at the turbo.

## Caveats
- No openly accessible source provides a complete, itemized 3S-GTE *turbo* head flow curve at a stated depression; the best full 3S curve found is a *3S-GE BEAMS* head at 25″. Every 3S-GTE flow number found **lacks a documented test pressure.** Treat all cited CFM as approximate and bench-dependent.
- The "250–292 CFM stock" build-note figure is **not verified as stock** and mixes a BEAMS ported number with an unpressurized 3S-GTE stock number.
- Exact Toyota part numbers for the turbo coolant banjo bolts and the hard-line OD could not be confirmed from primary Toyota documentation and are flagged as estimates/verify-in-person; forum-quoted MD/MF part numbers are Mitsubishi, not Toyota.
- Crank-hp and drivetrain-loss figures are estimates; AWD losses vary ~15–20%. The pressure-ratio/boost estimates follow directly from those assumptions and should be treated as planning figures, not guarantees.
