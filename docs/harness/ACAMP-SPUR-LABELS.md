# A/C amplifier leads: pins, colours and sources

The amplifier-side leads (`fl_acamp_tw`, `fl_acamp_sg`, `fl_acamp_act`, `fl_acamp_psw`) are drawn on
`ST185-ECU-cabin`; the pressure-switch device lead (`fl_a5_4`) is on `ST185-EngineRoom-C`, crossing between the two
files as the broken-off pair `BR_AC_PSW` (`docs/harness/interfaces.json`). The compressor has no VC coil (Dan,
DECISIONS R205): the clutch is one wire, `k_acc` (LOGIC M5) pin 87 to A4 pin 4, grounded through the engine. No OEM A/C
housings are in either file. Solar sensor is not drawn. Ambient (TAM; return on the TW_RTN common) is not drawn.

Daniel (2026-09-30): 1990–1993 A/C amplifier and auto A/C amplifier pinouts are
interchangeable for these circuits. 1990 ST185 book locator for the compressor
amplifier is **A18**; 1992 Celica EWD132U locator is **A17**. Pin numbers below
are the same on both except where an assumption is called out.

## Labels

| Terminal | Land on | Factory colour | Function | Source |
|---|---|---|---|---|
| `fl_acamp_act` | A/C AMPLIFIER **A18 pin 11** | G-Y | ACT compressor cancel from ECU Aux 4 (ground = kill) | **1992** Celica EWD132U p.93 (ENGINE AND ECT ECU ACT → A17-11) and p.218 (A17 pin 11). Crops in this repo: `docs/electrical/ewd-snips/1992-celica-ewd132u-a17-act-p093.png`, `1992-celica-ewd132u-a17-clutch-p218.png`. Primary PDF: https://www.gtfour.ch/images/buecher/st18_stromlaufplan.pdf |
| `fl_acamp_psw` | A/C AMPLIFIER **A18 pin 13** | Y-R | A/C pressure switch in | **1990** ST185 EWD p.152 (`1990-st185-autoac-pressure-clutch-p152.png`). 1992 EWD132U p.219 A17-13 matches (`1992-celica-ewd132u-a17-pressure-p219.png`) |
| `fl_a5_4` | **A5 pin 4** (A/C pressure switch) | Y-R | Other end of the pressure-switch signal | **1990** p.152 (A5 pin 4 Y-R). **A5 pin 1** +12V comes from `ST185-CabinPower` (MTA-3 ACPS 10 A, `w_acp_1`, broken off through EngineRoom-C) |

Heater-core thermistor (TW) leads:

| Terminal | Land on | Factory colour | Function | Source |
|---|---|---|---|---|
| `fl_acamp_tw` | AUTO A/C AMPLIFIER **A34 pin 20** | R-G | TW - heater-core water temp thermistor (dash, on the heater housing), not an engine coolant switch | 1990 p.150 (`1990-st185-autoac-amplifier-p150.png`); **corrected 2026-10-04** per 1993 TIS EWD p.211 and Mitchell component locations |
| `fl_acamp_sg` | A34 return **TBD** | TBD | TW return (thermistor, not a switch) | 1990 p.150 does not show the return pin — do not invent |

Kill copper: ECU-A A18 Aux 4 (Gray 20 AWG) wires straight to `fl_acamp_act`, both on `ST185-ECU-cabin` now (no break needed since the kill switch output and the amplifier lead are in the same file). Factory ACT colour is G-Y; splice the Gray lead into that G-Y at A18-11.

`fl_a5_4` is a new-wire run terminated at the pressure switch's own mating plug, not solder-sleeved into factory
wire (no factory engine-bay wire reused, R11); the plug part number is not yet chosen.

## Assumptions

1. **A18-11 = A17-11.** Pin 11 is not on 1990 p.150 or p.152 (that is why ACT was left TBD). 1992 p.93/p.218 show A17 pin 11 G-Y = ACT. Applied to the 1990 locator A18 because Daniel said 1990–1993 amplifier pinouts are interchangeable, and pins 5 (clutch Y-B) and 13 (pressure Y-R) already match across those years.
2. No Toyota housing part number is cited for A18, A4, or A5 — none is in the diagrams used here, and none is invented.

The flying-lead insulation on the pressure lead follows the factory colour (Y-R). That is a splice colour, not the ECU harness palette. Kill stays Gray 20 AWG.

## Out of scope

- Dashboard solar sensor — not drawn.
- Ambient air temperature sensor (TAM, A34-6 / return A34-15 SG, the sensor common shared with TW - `sot/channels.csv` TW_RTN) — not added.
