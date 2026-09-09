# BorgWarner MatchBot procedure (official field help)

Source: live tool at https://www.borgwarner.com/matchbot/ — every range below
is copied from the page's `?` pop-ups (`ddrivetip` in `index.html`) or from
`bot.js` v1.4. Do not invent values. A previous pass that ignored these
dependencies produced `Turbine Match Not Possible`, negative wastegate area,
and `NaN` port diameters.

## Why the first pass was invalid

MatchBot is not "enter boost + pick a compressor." Several fields are
**defaults you must leave alone until the points plot**, and TER is an
**iterated control**, not a guessed constant.

`bot.js` marks a point impossible when computed wastegate fraction `fPW < 0`
(turbine shaft power cannot meet compressor power at that TER). The pink
banner then says: raise Turbine Expansion Ratio, or lower that point's boost.

Selecting **E85/E100** in the fuel dropdown **overwrites VE, EGT, BSFC, and
AFR** (`fuelType()` in `bot.js`) — including VE up to 110% at point 6. The
BSFC tooltip explicitly says **do not do that** for alcohol: keep gasoline
AFR/BSFC so the airflow/power math stays correct (fuel-flow lb/hr will be
wrong; compute E85 fuel separately).

## Official suggested ranges

| Field | Official help |
| --- | --- |
| VE (gasoline) | 90–95% at low speed; 95–110% between peak torque and max power, depending on breathing (cams, manifolds, VVT) |
| Boost | Target per speed. If the turbine is too large to make the target, the tool notifies you |
| Intercooler effectiveness | 90–95% low speed typical IC; 85–90% high speed typical IC; 100% air-to-water; 0% no IC |
| Intercooler pressure drop | 1–2 psi at peak power; scales as **(flow ratio)²** at lower points |
| Air-filter restriction | ≤ 1 psi at peak, ~0.5 psi for a low-restriction system; same square-law scale |
| Muffler / exhaust backpressure | Stock cat+muffler 6–7 psi at peak; race / dump pipe almost nothing. **Significant effect on turbine match.** Square-law scale |
| Compressor efficiency | **Leave defaults, plot points, then refine from the compressor map** |
| Turbine efficiency | **Leave defaults** unless a map value is known. Twin-scroll + divided manifold: raise low-speed TE by **10–15%** |
| EGT | Gasoline 11:1 → 1650 °F; 12.5:1 → 1750 °F; 14:1 → 1850 °F. E85/E100 ~50–100 °F cooler than gasoline |
| Turbine expansion ratio | Move +/− until **all six points land on a single Phi curve** on the Turbine Map. Collapse Calculated Outputs, expand Turbine Map, watch the dots. `All +` / `All −` scale the six TERs together |
| BSFC (gasoline) | Low rpm 0.42–0.47; mid 0.45–0.50; peak power 0.50–0.60; 7500–9000 rpm 0.60–0.70 |
| AFR | Gasoline on boost 11.0–12.5; before boost ~13:1. **Alcohol: use gasoline AFR + gasoline BSFC** (see BSFC tip) |
| Fuel dropdown | Pump Gas for this study. E85 power is computed outside MatchBot from airflow × 11 hp/lb-min |

EFR housings span **PHI 0.020–0.048** (EFR Technical Training Guide). Internal
wastegate ports: 31 mm (small housings) / 36 mm (B/C housings). Design intent
is up to ~40% wastegate fraction.

## Defaults we leave until the map plots (`index.html` values)

| Point | RPM (demo) | CE % | TE % | TER |
| --- | --- | --- | --- | --- |
| 1 | 2000 | 66 | 75 | 1.21 |
| 2 | 3000 | 70 | 73 | 1.38 |
| 3 | 4000 | 74 | 72 | 1.61 |
| 4 | 5000 | 76 | 71 | 1.81 |
| 5 | 6000 | 72 | 70 | 1.98 |
| 6 | 7000 | 66 | 70 | 2.18 |

Compressor codes: `70s75` = EFR 7064, `71x80` = EFR 7163, `76s75` = EFR 7670.

Official map images (MatchBot + catalog PDFs):

- https://www.borgwarner.com/matchbot/images/new/EFR/BorgWarner%20EFR%207064%20Compressor%20Map.jpg
- https://www.borgwarner.com/matchbot/images/new/EFR/BorgWarner%20EFR%207163%20Compressor%20Map.jpg
- https://www.borgwarner.com/matchbot/images/new/EFR/BorgWarner%20EFR%207670%20Compressor%20Map.jpg
- https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7064-b.pdf
- https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7163-f.pdf
- https://www.borgwarner.com/docs/default-source/iam/boosting-technologies/efr-7670-b.pdf

## This engine's MatchBot case (ST185 5S-GTE 2.189 L)

See `matchbot_case.yaml`. VE entered here is **breathing VE** (head + cams),
not the backpressure-eroded curve in `inputs.yaml`. MatchBot's EMP / dP then
shows whether the turbine can hold the boost target.

## Run order

1. Reset MatchBot.
2. Single turbo, 2.189 L, 75 °F, 0 ft, Pump Gas.
3. Fill the six operating points from `matchbot_case.yaml`.
4. Leave CE at defaults. Set TE to defaults + twin-scroll low-speed bonus.
5. Start TER at defaults. Click `All +` until no point shows N/A wastegate.
6. Expand Turbine Map. Nudge TER so PHI stays inside 0.020–0.048 and wastegate
   fraction rises with rpm (catalog example: ~1 / 14 / 24 / 34 / 37 / 38 %).
7. Select compressor (`70s75` / `71x80` / `76s75`). Read CE from the island
   under each dot and write those CE values back; recalculate once.
8. Capture the full input/output table + compressor map + turbine map.
9. Repeat for the other two compressors (same engine case; TER may need a
   small re-trim because CE feedback changes shaft power).
