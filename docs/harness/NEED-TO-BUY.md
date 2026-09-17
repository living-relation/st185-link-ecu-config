# Harness — need to buy

Generated from `ST185-Signal.harness`, `ST185-Power.harness`, `ST185-CAN.harness` and `ST185-EngineRoom-C.harness` on 2026-09-17.
On-hand comes from `TE_BOM_with_screenshots.xlsx` plus the three TE invoices in Drive.
Regenerate with `docs/harness/buylist.py` after any harness change — do not hand-edit.

## Short — order these

| Part number | Mfr | Description | Need | Have | **Buy** |
|---|---|---|---:|---:|---:|
| `0460-202-2031` | TE DEUTSCH | Size 20 solid PIN, 20 AWG, 7.5 A - TO BUY | 42 | 0 | **42** |
| `0462-201-2031` | TE DEUTSCH | Size 20 solid SOCKET, 20 AWG, 7.5 A - TO BUY | 42 | 0 | **42** |
| `0413-204-2005` | TE DEUTSCH | Sealing plug, size 20, red | 30 | 0 | **30** |
| `114017` | TE DEUTSCH | Sealing plug, size 16, white | 16 | 0 | **16** |
| `Jump lugs 2 AWG / 1/0` | generic | Trunk +, trunk −, PDB, starter B+, engine block, engine-bay jump post | 8 | 0 | **8** |
| `1-1904045-6` | TE Connectivity | Micro ISO relay connector kit (harness-side socket for the V23074 relays) | 6 | 0 | **6** |
| `12110293` | Aptiv | MP150.2 3-way sealed sensor | 4 | 0 | **4** |
| `15419715` | Aptiv | GT150 2-way gray USCAR/EV6 injector | 4 | 0 | **4** |
| `90980-11062` | Toyota | 2-pin sensor pigtail | 4 | 0 | **4** |
| `90980-11885` | Toyota | 4-way 1ZZ COP connector | 4 | 0 | **4** |
| `280756-4` | TE Connectivity | 250-series terminal 12-10 AWG, for VCF7 power legs | 4 | 0 | **4** |
| `DT06-2S` | Deutsch | DT 2-way socket plug | 5 | 2 | **3** |
| `120R 1/4W` | Generic | 120 ohm CAN bus termination | 2 | 0 | **2** |
| `RL00571-35 black shell` | Amphenol | RADLOK 5.7mm RADSOK bulkhead pair, black, 2 AWG / 25 mm2 - bat | 2 | 0 | **2** |
| `RL00571-35 red shell` | Amphenol | RADLOK 5.7mm RADSOK bulkhead pair, red, 2 AWG / 25 mm2 - batte | 2 | 0 | **2** |
| `16-04477` | TE DEUTSCH | Gasket 24SZ | 6 | 4 | **2** |
| `1.8k 1/4W` | Generic | 1.8k ohm pull-up, cam Hall sensor signal to +8V Out | 1 | 0 | **1** |
| `10k 1/4W` | Generic | 10k pull-up for OEM cruise stalk resistor ladder into CSB3 Ana | 1 | 0 | **1** |
| `12052641` | Aptiv (Delphi) Metri-Pack 150 | 2-way sealed connector — fuel level sender / 2nd (condenser) f | 2 | 1 | **1** |
| `470R 1/4W` | Generic | 470 ohm pull-up, fuel level sender (An Volt 9) to +5V | 1 | 0 | **1** |
| `PDB-M8x8` | TBD | 8-stud power distribution block at glove box, M8, 150-250 A bu | 1 | 0 | **1** |
| `PMU-16` | ECUMaster | 10x25A + 6x15A high-side, 150A total, M6 stud + 39-way. On CAN | 1 | 0 | **1** |
| `Sumitomo TS 025 6-way` | Sumitomo / Subaru | Subaru BRZ / Toyota-family e-throttle pedal. Looking into conn | 1 | 0 | **1** |
| `jump-post-M8` | TBD | Engine-bay jump / accessory post on starter B+ net. | 1 | 0 | **1** |
| `HCR 150 mating hardware` | TE Connectivity | Receptacle / terminals for V23132-A2001-B200 - CONFIRM with supplier | 1 | 0 | **1** |
| `2 AWG welding cable red/black` | generic | Trunk battery +/−, RADLOK charge/start, jump post. Length TBD on the car. | 1 | 0 | **1** |
| `8 AWG TXL red/black` | generic | EPS pump 12V/GND (passenger ABS trough) and uprated fan 12V/GND (core support) | 1 | 0 | **1** |
| `ANL 150A + holder` | generic | PMU-16 M6 input fuse at the glove-box PDB (or PMU's own input fuse) | 1 | 0 | **1** |
| `2127` | Blue Sea Systems | PDB1 glove-box distribution block, 250A, four 5/16"-18 studs. Starter is fed direct from the main cable per OEM (plan 6.20), so PDB1 carries accessories only. | 1 | 0 | **1** |
| `2719` | Blue Sea Systems | MaxiBus insulating cover for PDB1 / 2127. Not optional - PDB1 is inside the cabin. | 1 | 0 | **1** |
| `ANL/MEGA 300A + holder` | generic | MAIN battery fuse, within ~18in of the trunk battery positive. Protects the whole cabin run - OEM leaves the starter lead unfused but its battery is 2ft away, ours is 12ft. See plan 6.20. | 1 | 0 | **1** |
| `ANL 175A + holder` | generic | Alternator B+ protection. OEM uses 100A FL ALT for the stock alternator; scaled for the 160A unit. See plan 6.20. | 1 | 0 | **1** |
| `Battery master cutoff` | generic | Trunk, alongside the main fuse. Motorsport requirement and the sane place for it. | 1 | 0 | **1** |
| `55A1131-20 or M27500-20SB1T23` | TE / Raychem | Single-conductor shielded, 20 AWG, crosslinked ETFE. EPS speed pulse (Aux 7 -> pump conn B) and any other screened single signal. Shield grounded at the ECU end only. CONFIRM which of the two is the stock on hand - see plan 6.24. | 1 | 0 | **1** |

## Covered by stock

| Part number | Description | Need | Have |
|---|---|---:|---:|
| `0413-214-1205` | Sealing plug, size 12, yellow | 10 | 10 |
| `0460-202-1631` | Size 16 solid PIN, 16-20 AWG, 13 A | 22 | 130 |
| `0460-204-0490` | Size 4 solid PIN, 6 AWG, 100 A | 1 | 5 |
| `0460-204-08141` | Size 8 solid PIN, 8-10 AWG, 60 A | 2 | 5 |
| `0460-220-1231` | Size 12 solid PIN, 12-14 AWG, 25 A | 10 | 20 |
| `0462-201-1631` | Size 16 solid SOCKET, 16-20 AWG, 13 A | 22 | 118 |
| `0462-203-04141` | Size 4 solid SOCKET, 6 AWG, 100 A | 1 | 9 |
| `0462-203-08141` | Size 8 solid SOCKET, 8-10 AWG, 60 A | 2 | 9 |
| `0462-210-1231` | Size 12 solid SOCKET, 12-14 AWG, 25 A | 10 | 20 |
| `1 928 403 874` | 2-way knock sensor connector | 1 | 1 |
| `114018-ZZ` | Sealing plug, size 8, white | 2 | 10 |
| `114019-ZZ` | Sealing plug, size 4, white | 2 | 10 |
| `13519047` | GT150 3-way flex-fuel sensor | 1 | 1 |
| `2141029-1` | Fuse box assembly, hard wired | 1 | 1 |
| `2411-001-2405` | Panel nut size 24 | 3 | 4 |
| `2428-011-2405` | Backshell 24SZ right-angle L017 | 1 | 1 |
| `4-1437290-0` | SUPERSEAL 1.0 34-way receptacle COD 1 — Link XtremeX loom B | 1 | 2 |
| `4-1437290-1` | SUPERSEAL 1.0 34-way receptacle COD 2 — Link XtremeX loom A | 1 | 2 |
| `90980-10897` | MR-S EHPS pump — control connector housing (pigtail 82998-1244 | 1 | 1 |
| `90980-10942` | MR-S EHPS pump — small ignition-enable connector housing (pigt | 1 | 1 |
| `90980-12068` | MR-S EHPS pump — main power connector housing (pigtail 82998-1 | 1 | 1 |
| `D 261 205 358-01` | 6-pin Bosch Motorsport ETB mate | 1 | 1 |
| `DT06-3S` | DT 3-way socket plug | 1 | 2 |
| `DTM06-4S` | DTM 4-way socket — CAN-Lambda harness side | 1 | 1 |
| `DTM06-6S` | DTM 6-way socket — ECU comms harness side | 1 | 1 |
| `HDP24-24-21PN` | HDP20 sz24 21-way receptacle, PIN, N seal - bulkhead B, firewa | 1 | 1 |
| `HDP24-24-47PE-L017` | HDP20 sz24 47-way receptacle, PIN, E seal, reverse ring flange | 1 | 1 |
| `HDP24-24-9PE` | HDP20 sz24 9-way receptacle, PIN, E seal - bulkhead C, high cu | 1 | 2 |
| `HDP26-24-21SN` | HDP20 sz24 21-way plug, SOCKET, N seal - bulkhead B, engine si | 1 | 1 |
| `HDP26-24-47SE-L015` | HDP20 sz24 47-way plug, SOCKET, E seal, threaded - bulkhead A, | 1 | 1 |
| `HDP26-24-9SE` | HDP20 sz24 9-way plug, SOCKET, E seal - bulkhead C, high curre | 1 | 2 |
| `M902-2243` | Backshell 24SZ straight L015 | 1 | 1 |
| `VCF7-1000 / 1393310-4` | Maxi relay mounting block | 1 | 1 |

## Not purchased — already on the car, or supplied with the device

| Modelled as | What it really is | Qty |
|---|---|---:|
| `(OEM block)` | Generic OEM block - only the pins this harness lands. No inven | 8 |
| `(OEM block, 2-way)` | Generic OEM block — 2 cavities. No invented OEM pinout. | 5 |
| `(OEM block, 5-way)` | Generic OEM block — 5 cavities (relay / cruise stalk). | 8 |
| `(kit-supplied pigtail)` | 3-pin pigtail supplied with the RacerX MR2 Cherry Hall cam-pos | 1 |
| `(none — PCB screw terminals)` | CAN Switch Board V3 screw-terminal I/O. No harness-side connec | 1 |
| `(unspecified — OEM ST185 AC amplifier)` | AC amplifier control connector. Pin count/layout inferred from | 1 |
| `TBD - moulded breakout boot` | Adhesive-lined moulded transition boot at each loom breakout.  | 24 |

## Still unspecified

- **Moulded breakout boots** for the branch points — `boot_breakout` is a placeholder. Needs a real dash number per branch OD once the trunk diameters are known.
- **HCR 150 mating hardware** — confirm the receptacle and terminal part numbers for `V23132-A2001-B200` with the supplier before ordering.
