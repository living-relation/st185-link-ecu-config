# Charge pipe and throttle body plumbing specification
## 5S-GTE Celica ST185

Revision 2, 31 August 2026. Supersedes revision 1 of the same date, which
wrongly concluded that the throttle body clamp forced 3.00 inch pipe through the
whole system. It does not. The clamp is one fitting at one end of one run.

Companion document: `PATCH-NOTE-intercooler-report.md`.
Source files: `data/throttle-body-plumbing/`.

---

## 1. Recommendation

**Hot side: 2.50 inch outside diameter × 0.065 inch wall.**
**Cold side: 3.00 inch outside diameter × 0.065 inch wall.**

Different sizes on the two runs, for different reasons, and not because of any
folklore about hot air needing more room.

The hot side runs past the turbine housing in the tightest and hottest part of a
transverse engine bay. 2.50 inch is the smallest pipe there, it puts velocity
closest to where it should be, and it costs 0.44 psi over the run.

The cold side already has a **3.00 inch fitting at both ends** — the SpeedFactory
SS-850 outlet is 3 inch, and the Outsider Garage throttle adapter is 3 inch.
Running 3.00 inch between them means no transition pieces at either end, and it
saves 0.25 psi.

**The packaging argument actually favours 3.00 inch on the cold side, because
you are welding.** A welded 3.00 inch pipe is 76.2 mm across. A 2.50 inch pipe
joined with silicone couplers and T-bolt clamps is **80.5 mm** across at every
coupler. Your welded 3 inch run is slimmer at every point than a conventional
2.5 inch coupled run would be. Full numbers in §6.

If the 3.00 inch cold side genuinely will not route, §5 gives the 2.50 inch
fallback and what it costs. It is not a large penalty. Decide it with the car in
front of you, not on paper.

---

## 2. Velocity and pressure drop

Design point, unchanged from the intercooler report: **45.7 lb/min (0.3455 kg/s)**.
Hot side 274 kPa at 180 °C, air density 2.106 kg/m³. Cold side 266 kPa at 62 °C,
density 2.765 kg/m³. Hot run 1.1 m with 3 bends, cold run 1.5 m with 4 bends.
Colebrook friction factor, 0.0015 mm roughness, bend loss coefficient 0.20 each.

**All diameters below are inside diameters at 0.065 inch wall.** Sizing on
nominal outside diameter overstates the flow area by 9–11% and understates every
velocity by the same proportion.

| Pipe OD | Inside dia | Hot side velocity | Hot ΔP | Cold side velocity | Cold ΔP | Volume |
|---------|-----------|-------------------|--------|--------------------|---------|--------|
| 2.50 in | 60.20 mm | 189.1 ft/s | 0.442 psi | 144.0 ft/s | 0.446 psi | 2.85 L/m |
| 2.75 in | 66.55 mm | 154.7 ft/s | 0.288 psi | 117.9 ft/s | 0.291 psi | 3.48 L/m |
| 3.00 in | 72.90 mm | 128.9 ft/s | 0.196 psi | 98.2 ft/s | 0.198 psi | 4.17 L/m |

Reading it:

- **No option is undersized.** Garrett's 200–300 ft/s guidance is a "do not go
  below this" rule, and at 189 ft/s the 2.50 inch hot side is the closest of the
  three to it. Nothing here is a restriction.
- **2.50 inch is not a problem.** 0.888 psi for both runs is 3.6% of 25 psi
  boost. Your instinct was sound.
- **The gain from going bigger is real but modest.** 2.50 → 3.00 inch on both
  runs saves 0.49 psi. Roughly 2% of boost.
- **98 ft/s on a 3.00 inch cold side is low.** Below about 100 ft/s a pipe stops
  earning its volume. This is the honest argument against 3 inch cold side, and
  it is why the hot side should stay at 2.50 inch rather than following it.

### Against the report's 1.5 psi total budget

Adding the core (0.18 psi) and end tanks (0.35 psi):

| Build | Total system ΔP | Share of 25 psi |
|-------|-----------------|-----------------|
| 2.50 hot + 2.50 cold, with transitions | 1.44 psi | 5.7% |
| **2.50 hot + 3.00 cold** | **1.17 psi** | **4.7%** |
| 2.75 hot + 2.75 cold | 1.13 psi | 4.5% |
| 3.00 hot + 3.00 cold | 0.92 psi | 3.7% |

Every option meets the 1.5 psi target. This is not a pass-or-fail decision, it
is a preference. That matters, because it means packaging should win any
argument where the two conflict.

### Why 2.75 inch is not recommended

It sits neatly in the middle on flow, and only 6.3 mm fatter than 2.50 inch. But
2.75 inch aluminium mandrel bends are a specialty size — fewer suppliers, higher
price per bend, and it matches neither the 3 inch intercooler ports nor anything
else on the car. Given cost is your stated reason for welding, it is the wrong
place to spend.

---

## 3. The intercooler ports

**SpeedFactory SS-850: 3 inch inlet and 3 inch outlet**, bead-rolled tube ends,
on a 24 × 12 × 3 inch bar-and-plate core.

This is the fact that changes the cold side answer. The cold side now has a
3 inch fitting at the intercooler and a 3 inch fitting at the throttle. Running
2.50 inch between them means a contraction at one end and an expansion at the
other, purely to be narrower in the middle.

**Note the bead-rolled ends.** They are made for silicone couplers, not for HD
clamps. Fitting an HD clamp at the intercooler means cutting the bead off and
welding a ferrule to the tank spigot. See §4 — there is a better reason not to
put a rigid clamp there anyway.

---

## 4. Joints — a correction to the plan

You specified all welded, with HD clamps at the intercooler, at the throttle
body, and one for alignment. The clamp count is right. The **location of the
intercooler joint needs changing.**

**The engine moves and the intercooler does not.** The engine sits on rubber
mounts and rocks several millimetres under load and on gear changes. The
intercooler is bolted to the chassis. A pipe that is rigidly clamped at both
ends bridges that movement, and the stress goes into the welds and the tank
spigots. Aluminium has no fatigue limit — it does not matter how low the stress
is, enough cycles will crack it. This is the single most common way a welded
charge pipe fails.

Each run needs at least one flexible joint. The right place is the intercooler
end, because that is where the relative movement is.

Recommended joint plan:

| Run | Intercooler end | Middle | Engine end |
|-----|-----------------|--------|------------|
| Hot | 4-ply silicone coupler, 2.5 → 3.0 in reducer, T-bolt clamps. **Flexible** | welded | Silicone coupler at the turbo, 2.0 → 2.5 in reducer. **Flexible** |
| Cold | 4-ply silicone coupler, 3.0 in straight, T-bolt clamps. **Flexible** | one HD clamp for alignment | HD clamp to the throttle adapter. **Rigid, and fine** |

The HD clamp at the throttle is rigid, and that is correct — both sides of it
are mounted to the engine, so there is no relative movement across it.

This uses **two HD clamps, not three**, and it is cheaper as well as more
reliable. The silicone couplers at the intercooler are doing a job no clamp can
do.

If you want a hard joint at the intercooler for looks or for boost security, put
the flexible joint somewhere else in the same run instead. The requirement is
one flexible joint per run, not one at any particular place.

---

## 5. If the 3.00 inch cold side will not route

You cannot buy your way out of the 3 inch clamp. **Outsider Garage does not make
a 2.50 inch version of that adapter.** Confirmed from their product record: the
74 mm adapter is offered only as `3" Hose` or `3" HD Clamp`, in three colours,
all at $135. Their whole Bosch adapter range starts at 3 inch — the 68 mm
adapter is also 3 inch, the 82 mm is 3.5 inch. There is nothing smaller to swap
to, and the part you own is the correct one.

So a 2.50 inch cold side needs a transition you fabricate.

### The transition piece

Weld a 2.50 → 3.00 inch cone onto the plain end of a 3.000 inch HD clamp weld
ferrule. That single piece then clamps straight to the throttle adapter.

| Included cone angle | Length | Loss at peak flow |
|--------------------|--------|-------------------|
| 7° (textbook diffuser) | 104 mm (4.09 in) | 0.0055 psi |
| 10° | 73 mm (2.86 in) | 0.0078 psi |
| 14° | 52 mm (2.04 in) | 0.0117 psi |
| No cone, sudden step | 0 mm | 0.0391 psi |

*(Diffuser: an expanding duct. Expansions want a shallow angle because the air
slows as it spreads, and if it spreads too fast it separates off the wall and
tumbles instead of filling the pipe. 7° included is the classic limit.)*

**Use 10°.** 73 mm is far easier to package than 104 mm, and it costs 0.0023 psi
more. That is 0.0001% of boost.

You would also need a contraction at the intercooler outlet, 3.00 → 2.50 inch,
which a reducing silicone coupler handles at 0.012–0.023 psi.

### What the 2.50 inch cold side actually costs

| | 3.00 in cold | 2.50 in cold |
|---|---|---|
| Cold pipe ΔP | 0.198 psi | 0.446 psi |
| Transitions | none | 0.017 psi |
| **Total** | **0.198 psi** | **0.463 psi** |
| Difference | — | **+0.265 psi, about 1% of boost** |
| Extra parts | none | one fabricated cone, one reducing coupler |
| Charge volume | +2.0 L | baseline |

**This is a small penalty.** If 3.00 inch will not clear the frame rail without
ugly routing or extra bends, take the 2.50 inch and the cone. Every extra bend
you add trying to squeeze a 3 inch pipe through costs about 1% of pressure each,
so three added bends wipes out the entire advantage.

Do not spend effort on the 1–2 mm steps anywhere in the chain. The full junction
analysis is in §8 and every one of them is worth less than a thousandth of a psi.

---

## 6. Packaging — what actually has to clear

This is the number that matters for routing, and it is not the pipe diameter.

| Configuration | Outside diameter | |
|---------------|-----------------|---|
| Welded 2.50 in pipe | **63.5 mm** | 2.50 in |
| Welded 2.75 in pipe | **69.8 mm** | 2.75 in |
| Welded 3.00 in pipe | **76.2 mm** | 3.00 in |
| 2.50 in + 4-ply silicone coupler | 74.5 mm | 2.93 in |
| 3.00 in + 4-ply silicone coupler | 87.2 mm | 3.43 in |
| 2.50 in + coupler + T-bolt clamp band | **80.5 mm** | 3.17 in |
| 3.00 in + coupler + T-bolt clamp band | **93.2 mm** | 3.67 in |
| 3.00 in HD clamp assembly | **estimate 100–115 mm** | see note |

A T-bolt clamp's trunnion and bolt stick out a further 20–25 mm, but on one side
only — you can clock that away from the obstruction.

**The conclusion that matters:** welded 3.00 inch pipe at 76.2 mm is *narrower*
than 2.50 inch pipe with couplers at 80.5 mm. Because you are welding, going up
a pipe size costs you nothing in clearance along the run. It only costs you at
the three joints.

So route the run on 76.2 mm and check clearance carefully at just three places:
the intercooler coupler, the alignment clamp, and the throttle clamp.

**The HD clamp outside diameter is an estimate and needs confirming.** Vibrant do
not publish it and the retailer page timed out. The figure above is inferred from
the ferrule flange plus clamp body being roughly 1.3–1.5× the tube diameter.
Measure the clamp when it arrives, before you commit to a route that has it
passing close to the frame rail. This is the one packaging number in this
document that is not solid.

---

## 7. Bill of materials

Prices are indicative US retail as of August 2026 and need confirming at
purchase. They are here for relative comparison, not for budgeting.

### Pipe

| Item | Spec | Qty | Est. cost |
|------|------|-----|-----------|
| Hot side tube and bends | 2.50 in OD × 0.065 in wall, 6061-T6 aluminium, mandrel bent, R/D ≥ 1.5 (95 mm min centreline radius) | ~3 bends + straight, 1.1 m total | $70–110 |
| Cold side tube and bends | 3.00 in OD × 0.065 in wall, 6061-T6 aluminium, mandrel bent, R/D ≥ 1.5 (114 mm min centreline radius) | ~4 bends + straight, 1.5 m total | $90–140 |

**Wall thickness: 0.065 inch (1.65 mm).** It is the stock size for mandrel
intercooler tube from every supplier, HD clamp ferrules are bored to suit it, and
across the whole 0.049–0.083 range the flow difference is 0.04 psi. Choose it for
availability and weldability, not flow. Use 0.083 only for a section that carries
a sensor bung or that you expect to rework.

### Clamped joints

| Item | Spec | Qty | Est. cost |
|------|------|-----|-----------|
| HD clamp, throttle body | Vibrant 3.000 in HD clamp. You need the clamp band plus **one** weld ferrule — the Outsider Garage adapter is the other half of the joint | 1 | $60–100 |
| HD clamp, alignment joint | Vibrant 12516 full assembly, 3.00 in — clamp, **two** aluminium weld ferrules with O-rings, union sleeve, locking pin | 1 | $150–190 |

Buy both from Vibrant. Outsider Garage machined the adapter face to the Vibrant
pattern, and face profiles vary between makers. Mixing brands across one joint is
a leak risk.

**Check on arrival:** the Vibrant full assembly includes a union sleeve that sits
between the two ferrules. Confirm the Outsider Garage adapter's integral face
works with the sleeve, or whether that joint wants the ferrule direct. Test fit
before welding anything.

### Flexible joints

| Item | Spec | Qty | Est. cost |
|------|------|-----|-----------|
| Silicone coupler, turbo outlet | 4-ply aramid, 2.00 → 2.50 in reducer | 1 | $18–28 |
| Silicone coupler, intercooler inlet | 4-ply aramid, 2.50 → 3.00 in reducer | 1 | $18–28 |
| Silicone coupler, intercooler outlet | 4-ply aramid, 3.00 in straight | 1 | $15–25 |
| T-bolt clamps | 2 per coupler, sized to the coupler outside diameter. Do not use worm-drive clamps at 25 psi | 6 | $30–48 |

### Not needed

| Item | Why |
|------|-----|
| 2.50 → 2.90 in taper coupler | Was in the report's parts list for a taper into the throttle that does not exist in this build |
| 2.50 → 3.00 in transition cone | Only if you take the §5 fallback |
| Third HD clamp | §4 — the intercooler joint should be flexible, not clamped |

### Rough total

**$450–670** for the charge piping, depending on bend count and where you buy.
The two HD clamps are roughly 40% of it, which is why welding the rest is the
right call.

---

## 8. The diameter chain

Cold side, flow direction, recommended 3.00 inch build.

| # | Station | Inside diameter | Source |
|---|---------|-----------------|--------|
| 1 | SS-850 intercooler outlet | 3 in nominal, actual bore not published | Vendor listing |
| 2 | Silicone coupler, 3.00 in | ~76.2 mm relaxed | Standard |
| 3 | Cold charge pipe | **72.90 mm (2.870 in)** | 3.000 in OD − 2 × 0.065 in wall |
| 4 | HD clamp ferrule, alignment joint | ~72.9 mm | Bored to suit the tube. Not published |
| 5 | HD clamp ferrule, throttle end | ~72.9 mm | Same |
| 6 | Outsider Garage adapter, both ends | **not published** | Measure |
| 7 | Bosch 0 280 750 474 inlet | **not published** | Measure |
| 8 | **Throttle plate** | **74.50 mm (2.933 in)** | Plate stamped 745 |
| 9 | Bosch outlet | **not published** | Measure |
| 10 | Custom DBW manifold adapter, in and out | **not published** | On the Gmail drawings |
| 11 | Plenum flange bore | **not published** | Measure. The 109 mm and 105 mm figures are the flange plate outside, not the bore |

### Junctions

| Junction | Step | Direction | Cost | Action |
|----------|------|-----------|------|--------|
| Pipe 72.90 → plate 74.50 | +1.60 mm | Step up | 0.0003 psi | None. Leave it |
| All others | unknown, expected 0–3 mm | mixed | under 0.001 psi each | None |

Every step in this chain is worth less than a thousandth of a psi. **Do not blend
anything.** In particular, do not grind the throttle body's inlet casting — the
gain is unmeasurable and the risk is aluminium swarf in a $225 throttle body with
a sealed motor and dual position sensors.

Step up into the throttle is the good direction anyway: the air enters open space
and the lip faces downstream where it sits in the wake.

The manifold side, stations 10 and 11, was designed in CAD by Outsider Garage
from your own flange measurements with an STL sent for test fitting. It is
already matched. Listed for completeness only.

---

## 9. The throttle body adapter, for the record

**Bosch 74mm Throttle Body Hose & HD Clamp Adapters**, variant `3" HD Clamp /
Silver`, $100 on order #7870, 5 January 2026.

It is **not a weld-on flange**. It is a billet sleeve that slips over the
throttle body inlet, seals with an O-ring, and bolts on with four long cap
screws. Its outer end is machined as a flat radial clamp face — the throttle-side
half of an HD clamp joint. You weld nothing to it. You weld a matching ferrule to
your pipe and clamp the two together.

Vendor description: "billet adapters that slides over the Bosch DBW throttle body
to allow the use of a standard hose coupler or HD clamp. HD clamp compatibility
is for Vibrant style HD clamps and similar." Fitment listed as Bosch 0 280 750
474, which is exactly your throttle body. Supplied with the adapter, O-rings and
yellow zinc hardware — no clamp, no ferrule.

**"3 inch" means nominal tube size**, the same convention aluminium intercooler
piping uses. It refers to 3.00 inch (76.20 mm) outside diameter tube. Confirmed
by Vibrant selling their HD Clamp Weld Ferrules (SKU V1180) by "Matching Tube
Size" — 2.000, 2.500, 3.000, 3.500, 4.000, 5.000 inch — and by Outsider Garage's
own scratch-and-dent listing naming the identical variant "Bosch 74mm → 3\" HD
Clamp".

---

## 10. Sources

- Outsider Garage product record, `bosch-74mm-throttle-body-hose-and-hd-clamp-adapters`, retrieved 31 Aug 2026 — filed at `data/throttle-body-plumbing/`
- SpeedFactory SS-850, 3 in inlet / 3 in outlet, 24 × 12 × 3 in bar-and-plate core, 600–850 hp, bead-rolled tube ends
- Vibrant Performance HD Clamp Weld Ferrules, SKU V1180, sold by matching tube size
- Vibrant Performance 12516, HD clamp full assembly for 3.00 in OD tubing — clamp, two aluminium weld ferrules with O-rings, union sleeve, locking pin
- Gmail, Outsider Garage order #7870, 5 January 2026
- Calculations: `data/throttle-body-plumbing/charge-pipe-math.py` and `verify-dimension-chain.py`

---

## Open questions

1. **Will 3.00 inch route on the cold side?** The whole recommendation turns on
   this and it can only be answered with the car in front of you. Check at
   76.2 mm along the run, and at the three joints. Decision rule: if fitting
   3 inch costs you more than two extra bends, take the 2.50 inch fallback in §5
   instead.
2. **HD clamp outside diameter.** Not published by Vibrant. Estimated 100–115 mm
   in §6. Measure on arrival before committing to a route that passes the frame
   rail closely.
3. **Does the Vibrant union sleeve work with the Outsider Garage adapter face?**
   The full assembly includes one. Test fit before welding.
4. **Intercooler joint — clamp or coupler?** §4 recommends changing this to a
   silicone coupler for engine movement. Your call, but do not leave both ends of
   a run rigid.
5. **Hot side at 2.50 inch means a 2.50 → 3.00 inch reducer at the intercooler
   inlet.** Confirm that clears, since the SS-850 inlet is also 3 inch.
6. **Seven bores in the chain are unmeasured.** Both ends of the OG adapter, both
   Bosch ports, both manifold adapter ends, the plenum flange bore. None of them
   change the pipe sizing decision — they are for the record.
7. **The two manifold adapter PDF drawings are still not retrieved.** The Gmail
   connector in this session can see the attachments exist but has no tool to
   download them, and they are not on local disk. Save them out of Gmail by hand
   into `data/throttle-body-plumbing/`. Message IDs are in that folder's README.
8. **Charge volume recheck.** A 3.00 inch cold side adds about 2.0 L. The report's
   system total was 9.05 L, about 4.1× displacement. It becomes roughly 11 L,
   about 5×. Still inside the healthy 3–6× band, but the report's figure is now
   stale.
9. **The report's §10 velocity table is computed on outside diameter** while its
   §11 pressure drop budget is computed on inside diameter. They contradict each
   other. See the patch note.
