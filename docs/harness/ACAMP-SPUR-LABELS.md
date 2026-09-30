# A/C amplifier spur labels (2026-09-30)

Three circuits land on `ST185-ACAmp-Spur` as labeled flying leads. No OEM A/C
housings are in the loom. Solar sensor is not drawn. Ambient (TAM / TAM_RTN) is
not this pass.

Daniel (2026-09-30): 1990–1993 A/C amplifier and auto A/C amplifier pinouts are
interchangeable for these circuits. 1990 ST185 book locator for the compressor
amplifier is **A18**; 1992 Celica EWD132U locator is **A17**. Pin numbers below
are the same on both except where an assumption is called out.

## Labels

| Terminal | Land on | Factory colour | Function | Source |
|---|---|---|---|---|
| `fl_acamp_act` | A/C AMPLIFIER **A18 pin 11** | G-Y | ACT compressor cancel from ECU Aux 4 (ground = kill) | **1992** Celica EWD132U p.93 (ENGINE AND ECT ECU ACT → A17-11) and p.218 (A17 pin 11). Crops in this repo: `docs/electrical/ewd-snips/1992-celica-ewd132u-a17-act-p093.png`, `1992-celica-ewd132u-a17-clutch-p218.png`. Primary PDF: https://www.gtfour.ch/images/buecher/st18_stromlaufplan.pdf |
| `fl_acamp_mg` | A/C AMPLIFIER **A18 pin 9** | W-L | MG magnetic clutch lock sensor | **1990** ST185 EWD p.152. Repo snip: `docs/electrical/ewd-snips/1990-st185-autoac-pressure-clutch-p152.png`. 1992 EWD132U p.218 A17-9 matches (`1992-celica-ewd132u-a17-clutch-p218.png`) |
| `fl_a4_2` | **A4 pin 2** (A/C magnetic clutch and compressor sensor) | W-L | Other end of the MG wire | **1990** p.152 (device pin 2 on the clutch/sensor block). **1992** EWD132U p.28 locator list: “A 4 A/C Magnetic Clutch and Compressor Sensor” |
| `fl_acamp_psw` | A/C AMPLIFIER **A18 pin 13** | Y-R | A/C pressure switch in | **1990** ST185 EWD p.152 (`1990-st185-autoac-pressure-clutch-p152.png`). 1992 EWD132U p.219 A17-13 matches (`1992-celica-ewd132u-a17-pressure-p219.png`) |
| `fl_a5_4` | **A5 pin 4** (A/C pressure switch) | Y-R | Other end of the pressure-switch signal | **1990** p.152 (A5 pin 4 Y-R). EngineRoom-C still feeds **A5 pin 1** +12V (V-R) only |

Existing coolant-switch leads (not this pass, already on the spur):

| Terminal | Land on | Factory colour | Function | Source |
|---|---|---|---|---|
| `fl_acamp_tw` | AUTO A/C AMPLIFIER **A34 pin 20** | R-G | TW | 1990 p.150 (`1990-st185-autoac-amplifier-p150.png`) |
| `fl_acamp_sg` | A34 return **TBD** | TBD | Coolant-switch return | 1990 p.150 does not show the return pin — do not invent |

Kill copper: ECU-A A18 Aux 4 (Pink, this harness) on `ST185-A-cabin` → broken-off `br_w_ac_kill` → `fl_acamp_act` on this spur. Factory ACT colour is G-Y; splice the Pink lead into that G-Y at A18-11.

## Assumptions

1. **A18-11 = A17-11.** Pin 11 is not drawn on 1990 p.150 or p.152 (that is why SoT left ACT as TBD). 1992 p.93/p.218 show A17 pin 11 G-Y = ACT. Applied to the 1990 locator A18 because Daniel said 1990–1993 amplifier pinouts are interchangeable, and pins 9 (clutch) and 13 (pressure) already match across those years.
2. No Toyota housing part number is cited for A18, A4, or A5 — none is in the diagrams used here, and none is invented.

## Out of scope

- Dashboard solar sensor — not drawn.
- Ambient air temperature sensor (TAM / TAM_RTN, A34-6 / return TBD) — not added.
