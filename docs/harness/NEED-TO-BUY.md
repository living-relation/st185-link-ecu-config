# Harness — need to buy

Quantities came from the live harness.design looms exported 2026-09-30T09:48:41-04:00 (2026-09-30 9:48 AM America/New_York), not from the `.harness` files in `docs/harness/rebuild/` (main is behind those drawings). Drawing / loom JSON is not in this repo.
Looms in this export (id and name): `wkGz` ST185-WheelSpeed-Front, `rYzW` ST185-WheelSpeed-Rear, `mED3` ST185-B-cabin, `7AgB` ST185-A-cabin, `nzvp` ST185-B-engine, `lpq1` ST185-A-engine, `kopv` ST185-AntiTheft, `oOwL` ST185-EngineRoom-C, `jno4` ST185-CAN, `gklj` ST185-ClusterLED, `39zp` ST185-CabinPower, `lpB1` ST185-CSB3, `q2yk` ST185-RearFuel, `pzxm` ST185-ACAmp-Spur, `jnz4` ST185-APS-Pedal, `lpqV` Center Cluster.
On-hand piece counts come from `TE_BOM_with_screenshots.xlsx` plus the three TE invoices in Drive (`docs/harness/buylist.py` `ONHAND`). Lengths are not on that stock list.
Regenerate with `python docs/harness/from_live_boms.py --from-export <boms.json>`. Do not hand-edit. `buylist.py` no longer writes this file from `rebuild/`.
ClusterLED (`gklj`) exported a few M22759 runs in metres; those lengths are added as millimetres in the totals below.

## Short — order these (ST185 looms)

| Part number | Mfr | Description | Unit | Need | Have | **Buy** |
|---|---|---|---|---:|---:|---:|
| `GENERIC SOLDER SPLICE` |  | SPLICE, SOLDERED, ADHESIVE HEATSHRINK OVER | ea | 40 | 0 | **40** |
| `0462-201-2031` | TE DEUTSCH | CONTACT, SOCKET, SOLID, SIZE 20, GOLD, 20 AWG, 7.5 A | ea | 32 | 0 | **32** |
| `114017` | TE DEUTSCH | PLUG, SEALING, CAVITY, SIZE 16, WHITE | ea | 28 | 0 | **28** |
| `GENERIC FLYING LEAD` |  | TERMINAL, FLYING LEAD | ea | 28 | 0 | **28** |
| `8100-0461` | Sumitomo | CONTACT, SOCKET, CRIMP, SUMITOMO TS 090 (2.3 MM), TIN, 0.5-1.25 MM2 (20-16 AWG) | ea | 23 | 0 | **23** |
| `0413-204-2005` | TE DEUTSCH | PLUG, SEALING, CAVITY, SIZE 20, RED | ea | 11 | 0 | **11** |
| `S200-3-WI-22-9` | TE Connectivity | SLEEVE, SOLDERSLEEVE SHIELD DRAIN 22AWG | ea | 11 | 0 | **11** |
| `12084200` | Aptiv | CONTACT, SOCKET, CRIMP, METRI-PACK 150.2, TIN, CABLE-SEALED, 0.35-0.5 MM2 (22-20 AWG) | ea | 16 | 6 | **10** |
| `W2S` | TE DEUTSCH | WEDGELOCK, DT, 2-WAY PLUG | ea | 10 | 0 | **10** |
| `S200-2-WI-22-9` | TE Connectivity | SLEEVE, SOLDERSLEEVE SHIELD DRAIN 22AWG | ea | 9 | 0 | **9** |
| `DT06-2S` | TE DEUTSCH | CONNECTOR, PLUG, DT, 2 POS, SOCKET CONTACTS, N SEAL, GRAY | ea | 10 | 2 | **8** |
| `1-1355877-1` | TE Connectivity | CONTACT, FUSE, SINGLE, CUNISI PRE-TINNED, 1.0-2.5 MM2 (18-14 AWG) | ea | 6 | 0 | **6** |
| `280756-4` | TE Connectivity | CONTACT, RECEPTACLE, FASTIN-FASTON 375 (9.5 MM), UNINSULATED, TIN, 3.3-5.3 MM2 (12-10 AWG) | ea | 6 | 0 | **6** |
| `GENERIC LUG M10 50MM2` |  | TERMINAL, LUG, RING, COPPER, TINNED, 50 MM2 (1/0) BARREL, M10 STUD, ADHESIVE HEATSHRINK | ea | 6 | 0 | **6** |
| `0462-201-16141` | TE DEUTSCH | CONTACT, SOCKET, SOLID, SIZE 16, NICKEL, 16-20 AWG, 13 A | ea | 17 | 12 | **5** |
| `15326426` | Aptiv | CONTACT, SOCKET, CRIMP, GT 150, GOLD, SEALED, 0.35-0.50 MM2 (22-20 AWG), CABLE OD 1.20-1.85 MM | ea | 5 | 0 | **5** |
| `GENERIC HEAVY FLYING LEAD 10-6` |  | TERMINAL, FLYING LEAD, HEAVY | ea | 5 | 0 | **5** |
| `12110293` | Aptiv | CONNECTOR, PLUG, METRI-PACK 150.2, 3 POS, SEALED, SOCKET CONTACTS | ea | 4 | 0 | **4** |
| `1393310-4` | TE Connectivity | SOCKET, RELAY, MAXI ISO (VCF7-1000), 4 POS | ea | 5 | 1 | **4** |
| `15419715` | Aptiv | CONNECTOR, PLUG, GT 150, 2 POS, SEALED, GRAY, USCAR / EV6 | ea | 4 | 0 | **4** |
| `280755-4` | TE Connectivity | CONTACT, RECEPTACLE, FASTIN-FASTON 375 (9.5 MM), UNINSULATED, TIN, 6-10 MM2 (10-8 AWG) | ea | 4 | 0 | **4** |
| `90980-11062` | Toyota | CONNECTOR, PLUG, TOYOTA, 2 POS, SOCKET CONTACTS | ea | 4 | 0 | **4** |
| `90980-11885` | Toyota | CONNECTOR, PLUG, TOYOTA, 4 POS, SOCKET CONTACTS | ea | 4 | 0 | **4** |
| `DT04-6P` | TE DEUTSCH | CONNECTOR, RECEPTACLE, DT, 6 POS, PIN CONTACTS, N SEAL, GRAY | ea | 4 | 0 | **4** |
| `DT06-6S` | TE DEUTSCH | CONNECTOR, PLUG, DT, 6 POS, SOCKET CONTACTS, N SEAL, GRAY | ea | 4 | 0 | **4** |
| `DTHD06-1-8S` | TE DEUTSCH | CONNECTOR, PLUG, DTHD, 1 POS, SIZE 8 SOCKET CONTACT, 8-10 AWG, 60 A | ea | 4 | 0 | **4** |
| `GENERIC RING M5 10-8` |  | TERMINAL, LUG, RING, COPPER, TINNED, 10-8 AWG, M5 STUD, ADHESIVE HEATSHRINK | ea | 4 | 0 | **4** |
| `GENERIC RING M6 22-16` |  | TERMINAL, RING, INSULATED, NYLON, M6 STUD, 22-16 AWG | ea | 4 | 0 | **4** |
| `S200-4-WI-22-9` | TE Connectivity | SLEEVE, SOLDERSLEEVE SHIELD DRAIN 22AWG | ea | 4 | 0 | **4** |
| `W6P` | TE DEUTSCH | WEDGELOCK, DT, 6-WAY RECEPTACLE | ea | 4 | 0 | **4** |
| `W6S` | TE DEUTSCH | WEDGELOCK, DT, 6-WAY PLUG | ea | 4 | 0 | **4** |
| `1-1355880-1` | TE Connectivity | CONTACT, FUSE, SINGLE, CUNISI PRE-TINNED, 2.5-4 MM2 (14-12 AWG) | ea | 3 | 0 | **3** |
| `GENERIC LUG M8 4AWG` |  | TERMINAL, LUG, RING, COPPER, TINNED, 4 AWG, M8 STUD, ADHESIVE HEATSHRINK | ea | 3 | 0 | **3** |
| `GENERIC RING M6 12-10` |  | TERMINAL, RING, INSULATED, NYLON, M6 STUD, 12-10 AWG | ea | 3 | 0 | **3** |
| `1-1355833-1` | TE Connectivity | CONTACT, FUSE, SINGLE, CUNISI PRE-TINNED, 0.5-1.0 MM2 (20-18 AWG) | ea | 2 | 0 | **2** |
| `1-1355844-1` | TE Connectivity | CONTACT, BUSBAR, CUNISI PRE-TINNED, 4.0-6.0 MM2 (10 AWG) | ea | 2 | 0 | **2** |
| `120R 1/4W` |  | RESISTOR, FIXED, METAL FILM, 120 OHM, 1 PCT, 1/4 W | ea | 2 | 0 | **2** |
| `160927-4` | TE Connectivity | CONTACT, RECEPTACLE, 6.3 X 0.8, TIN, 1.0-2.5 MM2 (18-14 AWG) | ea | 2 | 0 | **2** |
| `280919-4` | TE Connectivity | CONTACT, RECEPTACLE, 4.8 X 0.8, TIN, 0.5-1.5 MM2 (20-16 AWG) | ea | 2 | 0 | **2** |
| `BDK 2.8` | Bosch | CONTACT, SOCKET, CRIMP, BOSCH BDK 2.8, 0.5-1.0 MM2 (20-18 AWG) | ea | 2 | 0 | **2** |
| `DT04-2P` | TE DEUTSCH | CONNECTOR, RECEPTACLE, DT, 2 POS, PIN CONTACTS, N SEAL, GRAY | ea | 2 | 0 | **2** |
| `GENERIC BUTT SPLICE 22-16` |  | SPLICE, BUTT, INSULATED, 22-16 AWG | ea | 2 | 0 | **2** |
| `GENERIC LUG M10 2AWG` |  | TERMINAL, LUG, RING, COPPER, TINNED, 2 AWG, M10 STUD, ADHESIVE HEATSHRINK | ea | 2 | 0 | **2** |
| `GENERIC LUG M8 8AWG` |  | TERMINAL, LUG, RING, COPPER, TINNED, 8 AWG, M8 STUD, ADHESIVE HEATSHRINK | ea | 2 | 0 | **2** |
| `RL00801-50BK` | Amphenol | CONNECTOR, CABLE, RADLOK 8.0, FEMALE, 200 A, 50 MM2 (1/0), BLACK | ea | 2 | 0 | **2** |
| `RL00801-50RE` | Amphenol | CONNECTOR, CABLE, RADLOK 8.0, FEMALE, 200 A, 50 MM2 (1/0), RED | ea | 2 | 0 | **2** |
| `W2P` | TE DEUTSCH | WEDGELOCK, DT, 2-WAY RECEPTACLE | ea | 2 | 0 | **2** |
| `W3S` | TE DEUTSCH | WEDGELOCK, DT, 3-WAY PLUG | ea | 2 | 0 | **2** |
| `1-1904045-6` | TE Connectivity | SOCKET, RELAY, MICRO ISO, 5 POS, WITH MOUNTING FLAP (V23333-Z0001-B046) | ea | 1 | 0 | **1** |
| `1.8k 1/4W` |  | RESISTOR, FIXED, METAL FILM, 1.8 KOHM, 5 PCT, 1/4 W | ea | 1 | 0 | **1** |
| `10k 1/4W` |  | RESISTOR, FIXED, METAL FILM, 10 KOHM, 5 PCT, 1/4 W | ea | 1 | 0 | **1** |
| `12052641` | Aptiv | CONNECTOR, PLUG, METRI-PACK 150.2, 2 POS, SEALED, SOCKET CONTACTS | ea | 2 | 1 | **1** |
| `15326427` | Aptiv | CONTACT, SOCKET, CRIMP, GT 150, GOLD, 0.75-1.0 MM2 (18-16 AWG) | ea | 6 | 5 | **1** |
| `470R 1/4W` |  | RESISTOR, FIXED, METAL FILM, 470 OHM, 5 PCT, 1/4 W | ea | 1 | 0 | **1** |
| `7-1904094-9` | TE Connectivity | RELAY, PLUG-IN, MAXI ISO F7, TE V23134-J0052-X439, 1 FORM A, 70 A AT 23 C / 50 A AT 85 C, 12 VDC COIL 91 OHM, DIODE SUPPRESSED, CATHODE ON 86 | ea | 1 | 0 | **1** |
| `90980-11143` | Toyota | CONNECTOR, PLUG, TOYOTA OVAL, 3 POS, SOCKET CONTACTS | ea | 1 | 0 | **1** |
| `DRB12-102PAE-L018` | TE DEUTSCH | CONNECTOR, RECEPTACLE, DRB, 102 POS, PIN CONTACTS, E SEAL, A KEY, WIRE ROUTER, FLANGE MOUNT | ea | 1 | 0 | **1** |
| `DRB16-102SAE-L018` | TE DEUTSCH | CONNECTOR, PLUG, DRB, 102 POS, SOCKET CONTACTS, E SEAL, A KEY, WIRE ROUTER | ea | 1 | 0 | **1** |
| `DRBF-1A` | TE DEUTSCH | FLANGE, MOUNTING, DRB 102/128 SERIES | ea | 1 | 0 | **1** |
| `GENERIC CRIMP SPLICE 14-10` |  | SPLICE, CRIMP, UNINSULATED, COPPER, TINNED, COMBINED 14-10 AWG, ADHESIVE HEATSHRINK OVER | ea | 1 | 0 | **1** |
| `GENERIC LUG M10 4AWG` |  | TERMINAL, LUG, RING, COPPER, TINNED, 4 AWG, M10 STUD, ADHESIVE HEATSHRINK | ea | 1 | 0 | **1** |
| `GENERIC LUG M10 8AWG` |  | TERMINAL, LUG, RING, COPPER, TINNED, 8 AWG, M10 STUD, ADHESIVE HEATSHRINK | ea | 1 | 0 | **1** |
| `GENERIC LUG M8 2AWG` |  | TERMINAL, LUG, RING, COPPER, TINNED, 2 AWG, M8 STUD, ADHESIVE HEATSHRINK | ea | 1 | 0 | **1** |
| `GENERIC SPADE RECEPTACLE 12-10` |  | TERMINAL, QUICK CONNECT, RECEPTACLE, INSULATED, 6.3 MM (250) TAB, 12-10 AWG | ea | 1 | 0 | **1** |
| `HD36-24-33SE` | TE DEUTSCH | CONNECTOR, PLUG, HD30, SHELL 24, 33 POS, SOCKET CONTACTS, E SEAL | ea | 1 | 0 | **1** |
| `LMI5-M-2-CB1AD` | Eaton Bussmann | FUSE BLOCK, MODULAR, LMI, METRIC, 1 INPUT MODULE (M8 STUD) + 4 AMI FUSE MODULES (M5 STUDS), 400 A MAX COMBINED | ea | 1 | 0 | **1** |
| `MR-S ZZW30 EHPS pump - A 90980-12068 / B 90980-10897 / C 90980-10942` |  | CONNECTOR SET, TOYOTA, 3 HOUSINGS: 90980-12068 2 POS, 90980-10897 6 POS, 90980-10942 2 POS | ea | 1 | 0 | **1** |
| `PDB-M8x8` |  | BLOCK, POWER DISTRIBUTION, 8 STUD M8, 150-250 A BUS | ea | 1 | 0 | **1** |
| `Sumitomo TS 025 6-way` |  | CONNECTOR, PLUG, SUMITOMO TS 025, 6 POS, SOCKET CONTACTS | ea | 1 | 0 | **1** |
| `V23132-A2001-B200` | TE Connectivity | RELAY, HIGH CURRENT, TE HCR 150, IP67, 1 FORM A, 130 A AT 85 C, 12 VDC COIL 37 OHM 3.9 W, PARALLEL RESISTOR, STUD LOAD TERMINALS | ea | 1 | 0 | **1** |
| `WM-4S` | TE DEUTSCH | WEDGELOCK, DTM, 4-WAY PLUG | ea | 1 | 0 | **1** |
| `WM-6S` | TE DEUTSCH | WEDGELOCK, DTM, 6-WAY PLUG | ea | 1 | 0 | **1** |
| `jump-post-M8` |  | POST, JUMP START, M8, INSULATED | ea | 1 | 0 | **1** |

## Wire and cable — cut lengths (ST185 looms)

| Part number | Mfr | Description | Unit | Need | Have | **Buy** |
|---|---|---|---|---:|---:|---:|
| `M22759/16-20-9` |  | WIRE, M22759/16, 20 AWG WHITE | mm | 19060 | 0 | **19060** |
| `M22759/16-20-5` |  | WIRE, M22759/16, 20 AWG GREEN | mm | 19010 | 0 | **19010** |
| `M22759/16-14-2` |  | WIRE, M22759/16, 14 AWG RED | mm | 16110 | 0 | **16110** |
| `M22759/16-20-09` |  | WIRE, M22759/16, 20 AWG BLACK/WHITE | mm | 15520 | 0 | **15520** |
| `M22759/16-20-3` |  | WIRE, M22759/16, 20 AWG ORANGE | mm | 10050 | 0 | **10050** |
| `BC-1/0-BLK` |  | CABLE, BATTERY, 1/0 AWG, BLACK, FINE-STRAND COPPER, SAE J1127 SGX 125 C OR EQUIV | mm | 9920 | 0 | **9920** |
| `M22759/16-8-2` |  | WIRE, M22759/16, 8 AWG RED | mm | 9640 | 0 | **9640** |
| `M22759/16-18-2` |  | WIRE, M22759/16, 18 AWG RED | mm | 9510 | 0 | **9510** |
| `M22759/16-20-2` |  | WIRE, M22759/16, 20 AWG RED | mm | 9490 | 0 | **9490** |
| `M22759/16-20-4` |  | WIRE, M22759/16, 20 AWG YELLOW | mm | 8970 | 0 | **8970** |
| `M22759/16-20-1` |  | WIRE, M22759/16, 20 AWG BROWN | mm | 8930 | 0 | **8930** |
| `M22759/16-12-2` |  | WIRE, M22759/16, 12 AWG RED | mm | 7910 | 0 | **7910** |
| `BC-1/0-RED` |  | CABLE, BATTERY, 1/0 AWG, RED, FINE-STRAND COPPER, SAE J1127 SGX 125 C OR EQUIV | mm | 7610 | 0 | **7610** |
| `EW-1C20-GRN` |  | WIRE, ELECTRICAL, 20 AWG, GREEN, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 6630 | 0 | **6630** |
| `55PC1122-20-2/6-9` |  | CABLE, SHIELDED TWISTED PAIR 20AWG | mm | 6580 | 0 | **6580** |
| `M22759/16-10-2` |  | WIRE, M22759/16, 10 AWG RED | mm | 5740 | 0 | **5740** |
| `M22759/16-20-8` |  | WIRE, M22759/16, 20 AWG GRAY | mm | 5640 | 0 | **5640** |
| `M22759/16-20-7` |  | WIRE, M22759/16, 20 AWG VIOLET | mm | 5590 | 0 | **5590** |
| `55PC1213-20-9-9` |  | CABLE, SHIELDED SINGLE CONDUCTOR 20AWG | mm | 5580 | 0 | **5580** |
| `M22759/16-20-0` |  | WIRE, M22759/16, 20 AWG BLACK | mm | 5320 | 0 | **5320** |
| `BC-2-RED` |  | CABLE, BATTERY, 2 AWG, RED, FINE-STRAND COPPER, SAE J1127 SGX 125 C OR EQUIV | mm | 5050 | 0 | **5050** |
| `M22759/16-18-0` |  | WIRE, M22759/16, 18 AWG BLACK | mm | 4860 | 0 | **4860** |
| `M22759/16-18-9` |  | WIRE, M22759/16, 18 AWG WHITE | mm | 4450 | 0 | **4450** |
| `M22759/16-18-7` |  | WIRE, M22759/16, 18 AWG VIOLET | mm | 4310 | 0 | **4310** |
| `BC-4-BLK` |  | CABLE, BATTERY, 4 AWG, BLACK, FINE-STRAND COPPER, SAE J1127 SGX 125 C OR EQUIV | mm | 3770 | 0 | **3770** |
| `EW-1C12-RED` |  | WIRE, ELECTRICAL, 12 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 3350 | 0 | **3350** |
| `M22759/16-8-0` |  | WIRE, M22759/16, 8 AWG BLACK | mm | 3250 | 0 | **3250** |
| `55PC1243-20-2/6/4/5-9` |  | CABLE, SHIELDED TWISTED QUAD 20AWG | mm | 2720 | 0 | **2720** |
| `M22759/16-10-0` |  | WIRE, M22759/16, 10 AWG BLACK | mm | 2710 | 0 | **2710** |
| `M22759/16-20-39` |  | WIRE, M22759/16, 20 AWG ORANGE/WHITE | mm | 2560 | 0 | **2560** |
| `M22759/16-10-1` |  | WIRE, M22759/16, 10 AWG BROWN | mm | 2240 | 0 | **2240** |
| `M22759/16-8-9` |  | WIRE, M22759/16, 8 AWG WHITE | mm | 2240 | 0 | **2240** |
| `55PC1133-20-2/6/4-9` |  | CABLE, SHIELDED TWISTED TRIPLE 20AWG | mm | 2230 | 0 | **2230** |
| `EW-1C20-WHT` |  | WIRE, ELECTRICAL, 20 AWG, WHITE, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 2200 | 0 | **2200** |
| `M22759/16-6-9` |  | WIRE, M22759/16, 6 AWG WHITE | mm | 2190 | 0 | **2190** |
| `M22759/16-18-09` |  | WIRE, M22759/16, 18 AWG BLACK/WHITE | mm | 1610 | 0 | **1610** |
| `M22759/16-18-29` |  | WIRE, M22759/16, 18 AWG RED/WHITE | mm | 1600 | 0 | **1600** |
| `M22759/16-20-6` |  | WIRE, M22759/16, 20 AWG BLUE | mm | 1520 | 0 | **1520** |
| `BC-4-RED` |  | CABLE, BATTERY, 4 AWG, RED, FINE-STRAND COPPER, SAE J1127 SGX 125 C OR EQUIV | mm | 1230 | 0 | **1230** |
| `EW-1C20-ORG` |  | WIRE, ELECTRICAL, 20 AWG, ORANGE, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 1210 | 0 | **1210** |
| `EW-1C8-RED` |  | WIRE, ELECTRICAL, 8 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 900 | 0 | **900** |
| `M22759/16-20-54` |  | WIRE, M22759/16, 20 AWG GREEN/YELLOW | mm | 890 | 0 | **890** |
| `M22759/16-18-3` |  | WIRE, M22759/16, 18 AWG ORANGE | mm | 820 | 0 | **820** |
| `EW-1C12-BLK` |  | WIRE, ELECTRICAL, 12 AWG, BLACK, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 770 | 0 | **770** |
| `EW-1C14-RED` |  | WIRE, ELECTRICAL, 14 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 750 | 0 | **750** |
| `EW-1C18-RED` |  | WIRE, ELECTRICAL, 18 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 750 | 0 | **750** |
| `EW-1C10-RED` |  | WIRE, ELECTRICAL, 10 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 730 | 0 | **730** |
| `EW-1C20-BLK-WHT` |  | WIRE, ELECTRICAL, 20 AWG, BLACK/WHITE, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 700 | 0 | **700** |
| `EW-1C20-RED` |  | WIRE, ELECTRICAL, 20 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 620 | 0 | **620** |
| `EW-1C20-BLK` |  | WIRE, ELECTRICAL, 20 AWG, BLACK, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 570 | 0 | **570** |
| `M22759/16-16-2` |  | WIRE, M22759/16, 16 AWG RED | mm | 430 | 0 | **430** |
| `M22759/16-14-0` |  | WIRE, M22759/16, 14 AWG BLACK | mm | 360 | 0 | **360** |
| `EW-1C20-BRN` |  | WIRE, ELECTRICAL, 20 AWG, BROWN, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 300 | 0 | **300** |
| `EW-1C20-YEL` |  | WIRE, ELECTRICAL, 20 AWG, YELLOW, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 300 | 0 | **300** |
| `EW-1C16-RED` |  | WIRE, ELECTRICAL, 16 AWG, RED, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV | mm | 250 | 0 | **250** |
| `M22759/16-20-03` |  | WIRE, M22759/16, 20 AWG BLACK/ORANGE | mm | 160 | 0 | **160** |
| `M22759/16-20-25` |  | WIRE, M22759/16, 20 AWG RED/GREEN | mm | 140 | 0 | **140** |

## Shop once — one housing on two letter-halves

The live BOM lists each DRB102 shell on both ECU-letter halves. That is one
physical connector, not two. Per-loom parts lists keep the export quantity
on each half; the Need / Buy columns above use one housing.

| Part number | Halves in this export | Qty on each half | Shop |
|---|---|---|---:|
| `DRB12-102PAE-L018` | `7AgB` ST185-A-cabin, `mED3` ST185-B-cabin | 1 on `7AgB`, 1 on `mED3` | 1 |
| `DRB16-102SAE-L018` | `lpq1` ST185-A-engine, `nzvp` ST185-B-engine | 1 on `lpq1`, 1 on `nzvp` | 1 |

## Covered by stock (ST185 looms)

| Part number | Description | Unit | Need | Have |
|---|---|---|---:|---:|
| `0413-214-1205` | PLUG, SEALING, CAVITY, SIZE 12, YELLOW | ea | 4 | 10 |
| `0460-202-1631` | CONTACT, PIN, SOLID, SIZE 16, GOLD, 16-20 AWG, 13 A | ea | 78 | 130 |
| `0460-220-1231` | CONTACT, PIN, SOLID, SIZE 12, GOLD, 12-14 AWG, 25 A | ea | 4 | 20 |
| `0462-201-1631` | CONTACT, SOCKET, SOLID, SIZE 16, GOLD, 16-20 AWG, 13 A | ea | 95 | 118 |
| `0462-203-08141` | CONTACT, SOCKET, SOLID, SIZE 8, NICKEL, 8-10 AWG, 60 A | ea | 4 | 9 |
| `0462-210-1231` | CONTACT, SOCKET, SOLID, SIZE 12, GOLD, 12-14 AWG, 25 A | ea | 4 | 20 |
| `1 928 403 874` | CONNECTOR, PLUG, BOSCH COMPACT 1.1A, 2 POS, SOCKET CONTACTS | ea | 1 | 1 |
| `1-1393304-0` | RELAY, PLUG-IN, MAXI ISO F7, TE V23134-J1052-X281, 1 FORM A, 70 A AT 23 C / 50 A AT 85 C, 12 VDC COIL 90 OHM, 560 OHM PARALLEL RESISTOR, MOUNTING BRACKET | ea | 2 | 2 |
| `1-1414147-0` | RELAY, PLUG-IN, MAXI ISO F7, TE V23134-J0052-X429, 1 FORM A, 70 A AT 23 C / 50 A AT 85 C, 12 VDC COIL 90 OHM, 680 OHM PARALLEL RESISTOR | ea | 2 | 3 |
| `13519047` | CONNECTOR, PLUG, GT 150, 3 POS, SEALED, SOCKET CONTACTS | ea | 1 | 1 |
| `2141029-1` | FUSE HOLDER, MODULE, MFINITY, 16 POS MINI FUSE, HARD WIRED | ea | 1 | 1 |
| `282110-1` | CONTACT, SOCKET, CRIMP, SUPERSEAL 1.5, TIN, 0.75-1.5 MM2 (18-16 AWG), SEAL 281934-2 | ea | 2 | 10 |
| `3-1447221-3` | CONTACT, SOCKET, CRIMP, SUPERSEAL 1.0, GOLD, 0.75-0.85 MM2 (18 AWG) | ea | 17 | 68 |
| `3-1447221-4` | CONTACT, SOCKET, CRIMP, SUPERSEAL 1.0, GOLD, 0.5 MM2 (20 AWG), INSUL 1.6-2.2 MM | ea | 41 | 68 |
| `4-1437290-0` | CONNECTOR, RECEPTACLE, SUPERSEAL 1.0, 34 POS, CODE 1, SOCKET CONTACTS, BLUE | ea | 1 | 2 |
| `4-1437290-1` | CONNECTOR, RECEPTACLE, SUPERSEAL 1.0, 34 POS, CODE 2, SOCKET CONTACTS, BLUE | ea | 1 | 2 |
| `4-1904124-2` | RELAY, PLUG-IN, MICRO ISO, TE V23074-A1001-A402, 1 FORM A, 25 A, 12 VDC COIL 119 OHM, 680 OHM PARALLEL RESISTOR | ea | 1 | 2 |
| `42281-1` | CONTACT, RECEPTACLE, FASTIN-FASTON 250 (6.3 MM), TIN, 0.8-2.0 MM2 (18-14 AWG) | ea | 10 | 20 |
| `D 261 205 358-01` | CONNECTOR, PLUG, BOSCH MOTORSPORT KIT, 6 POS, SOCKET CONTACTS | ea | 1 | 1 |
| `DT06-12SA` | CONNECTOR, PLUG, DT, 12 POS, SOCKET CONTACTS, N SEAL, KEY A, GRAY | ea | 1 | 2 |
| `DT06-3S` | CONNECTOR, PLUG, DT, 3 POS, SOCKET CONTACTS, N SEAL, GRAY | ea | 2 | 2 |
| `DTM06-4S` | CONNECTOR, PLUG, DTM, 4 POS, SOCKET CONTACTS, GRAY | ea | 1 | 1 |
| `DTM06-6S` | CONNECTOR, PLUG, DTM, 6 POS, SOCKET CONTACTS, GRAY | ea | 1 | 1 |
| `W12S` | WEDGELOCK, DT, 12-WAY PLUG | ea | 1 | 2 |

## Not purchased — already on the car, or supplied with the device (ST185 looms)

| Modelled as | What it really is | Unit | Qty |
|---|---|---|---:|
| `(LED board indicator - 12 V, resistor on board)` | DIODE, LIGHT EMITTING, INDICATOR, 12 V | ea | 6 |
| `(OEM block)` | CONNECTOR, OEM, JUNCTION OR RELAY BLOCK | ea | 3 |
| `(Toyota TS terminals, supplied with owned housings)` | CONTACT, SOCKET, CRIMP, TOYOTA | ea | 4 |
| `(generic)` | CONTACT, SOCKET, CRIMP, GENERIC | ea | 18 |
| `(glove-box body block - 2nd fuse block + relays)` | ASSEMBLY, FUSE AND RELAY BLOCK, 12-16 WAY, GLOVE BOX | ea | 1 |
| `(integral - RL00801-50)` | CONTACT, RADSOK 8.0, INTEGRAL TO RL00801-50 CABLE CONNECTOR, 50 MM2 (1/0) CRIMP BARREL | ea | 4 |
| `(kit socket, D 261 205 358-01)` | CONTACT, SOCKET, CRIMP, GOLD | ea | 6 |
| `(kit-supplied pigtail)` | CONNECTOR, PIGTAIL, 3 POS | ea | 1 |
| `(pump pigtail - Walbro F90000295)` | CONNECTOR, PIGTAIL, 2 POS | ea | 1 |
| `(ring lug, 8 AWG, M6)` | TERMINAL, LUG, RING, COPPER, TINNED, 8 AWG, M6 STUD, ADHESIVE HEATSHRINK | ea | 2 |
| `(ring lug, sized to cable)` | TERMINAL, LUG, RING, COPPER, TINNED, SIZED TO CABLE, ADHESIVE HEATSHRINK | ea | 17 |
| `TBD - A/C coolant temperature switch connector` | CONNECTOR, 2 POS, TYPE TBD | ea | 1 |

## Quantity 0 in the live BOM (ST185 looms)

Present on a live loom's parts list at quantity 0. Not ordered from this export.

| Part number | Description | Unit | Qty in export |
|---|---|---|---:|
| `0460-202-2031` | CONTACT, PIN, SOLID, SIZE 20, GOLD, 20 AWG, 7.5 A | ea | 0 |
| `DTP04-4P-L012` | CONNECTOR, RECEPTACLE, DTP, 4 POS, PIN CONTACTS, FLANGE MOUNT | ea | 0 |
| `DTP06-4S` | CONNECTOR, PLUG, DTP, 4 POS, SOCKET CONTACTS | ea | 0 |
| `DTP4P-L012-GKT` | GASKET, MOUNTING, DTP 4 POS FLANGE RECEPTACLE L012 | ea | 0 |
| `HDP24-24-21PN` | CONNECTOR, RECEPTACLE, HDP20, SHELL 24, 21 POS, PIN CONTACTS, N SEAL | ea | 0 |
| `HDP24-24-47PE-L017` | CONNECTOR, RECEPTACLE, HDP20, SHELL 24, 47 POS, PIN CONTACTS, E SEAL, REVERSE RING FLANGE | ea | 0 |
| `HDP26-24-21SN` | CONNECTOR, PLUG, HDP20, SHELL 24, 21 POS, SOCKET CONTACTS, N SEAL | ea | 0 |
| `HDP26-24-47SE-L015` | CONNECTOR, PLUG, HDP20, SHELL 24, 47 POS, SOCKET CONTACTS, E SEAL, THREADED COUPLING | ea | 0 |
| `WB-51PAL` | WEDGELOCK, DRB 102/128, RECEPTACLE, LEFT | ea | 0 |
| `WB-51PAR` | WEDGELOCK, DRB 102/128, RECEPTACLE, RIGHT | ea | 0 |
| `WB-51SAL` | WEDGELOCK, DRB 102/128, PLUG, LEFT | ea | 0 |
| `WB-51SAR` | WEDGELOCK, DRB 102/128, PLUG, RIGHT | ea | 0 |
| `WP-4P` | WEDGELOCK, DTP, 4 POS, RECEPTACLE | ea | 0 |
| `WP-4S` | WEDGELOCK, DTP, 4 POS, PLUG | ea | 0 |

## Center Cluster (`lpqV`) — order these

From the same live export (`lpqV` Center Cluster). Not an ST185 rebuild file.

| Part number | Mfr | Description | Unit | Need | Have | **Buy** |
|---|---|---|---|---:|---:|---:|
| `GENERIC 2.54 CRIMP SOCKET 22-28` |  | CONTACT, SOCKET, 2.54mm (Dupont-style) CRIMP, 22-28 AWG — generic | ea | 49 | 0 | **49** |
| `GENERIC SCREW TERMINAL CONTACT` |  | Screw clamp contact - generic | ea | 11 | 0 | **11** |
| `GENERIC EC11 ROTARY ENCODER W/ SWITCH` |  | Rotary encoder, A / C / B + 2 push-switch pins - generic | ea | 3 | 0 | **3** |
| `EW-RING` |  | TERMINAL, RING, INSULATED, M6 STUD, 22-16 AWG | ea | 2 | 0 | **2** |
| `GENERIC 2.54 1x2 HOUSING` |  | HOUSING, 2.54mm, 1x2, FEMALE — generic dummy | ea | 2 | 0 | **2** |
| `GENERIC 2.54 1x4 HOUSING` |  | HOUSING, 2.54mm, 1x4, FEMALE — generic dummy | ea | 2 | 0 | **2** |
| `GENERIC FLYING LEAD` |  | Flying lead, joined to vehicle circuit at install (butt splice / solder sleeve) | ea | 2 | 0 | **2** |
| `PHOENIX-STYLE SCREW TERMINAL 1x4` |  | Screw terminal block, 4-pole, Phoenix style - generic | ea | 2 | 0 | **2** |
| `1.5k 1/4W` |  | 1.5k ohm series resistor, headlight-sense PC817 LED from illumination +12V | ea | 1 | 0 | **1** |
| `GENERIC 2.54 2x20 HOUSING` |  | HOUSING, 2.54mm, 2x20 (40-way), FEMALE — generic dummy for Waveshare P4-XC J8 | ea | 1 | 0 | **1** |
| `GENERIC MOMENTARY PUSHBUTTON NO` |  | Momentary normally-open pushbutton, 2 pins - generic | ea | 1 | 0 | **1** |
| `PHOENIX-STYLE SCREW TERMINAL 1x3` |  | Screw terminal block, 3-pole, Phoenix style - generic | ea | 1 | 0 | **1** |

## Center Cluster (`lpqV`) — quantity 0 in the live BOM

| Part number | Description | Unit | Qty in export |
|---|---|---|---:|
| `EW-1C22-BLK` | WIRE, 22 AWG, BLACK — ground | mm | 0 |
| `EW-1C22-BLU` | Trigger / CAN H | mm | 0 |
| `EW-1C22-GRN` | Digital / CAN L | mm | 0 |
| `EW-1C22-ORG` | +5V Out | mm | 0 |
| `EW-1C22-ORG-WHT` | WIRE, 22 AWG, ORANGE/WHITE — 3V3 | mm | 0 |
| `EW-1C22-PNK` | Aux out | mm | 0 |
| `EW-1C22-RED` | WIRE, 22 AWG, RED — switched 12V (low current) | mm | 0 |
| `EW-1C22-RED-WHT` | WIRE, 22 AWG, RED/WHITE — illumination +12V | mm | 0 |
| `EW-1C22-VIO` | Ignition | mm | 0 |
| `EW-1C22-VIO-WHT` | WIRE, 22 AWG, VIOLET/WHITE | mm | 0 |
| `EW-1C22-WHT` | Analog in | mm | 0 |
| `EW-1C22-YEL` | Temp | mm | 0 |
