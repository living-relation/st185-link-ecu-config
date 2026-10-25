# ST185 surgical rewire - interface cut list (working draft, written 2026-10-20)

> **Read first (2026-10-25).** Groups 1-3 and every box are decided: `README.md` and `../README.md` "What stays and
> what goes" win over this draft. Where it says cut and cap, read remove back to the last live point; where it keeps
> R/B No.2-5 or a kept engine-bay loop, read B9 (forward of the firewall every wire is new; R/B No.2 / No.4 stay).
> Groups 4-8 below are the starting point for the next walk-through with Dan.

Scope: every wire that crosses from a removed part/harness into a kept harness, per Daniel's 2026-10-20 "surgical rewire" plan.
Read-only research; nothing in either repo was changed.

**Sources and authority**
- Pins and colours come from the 1993 TIS EWD system pages in `st185-celica-repair-manual/manuals-electrical/` ("1993 p.NN" = printed page number).
- The 1993 pulls do not include the back-up light, cruise, ABS, SRS, fog light or rear wiper systems. For those I used the
  Mitchell 1993 overall diagrams (Fig. 12 = cruise + SRS centre sensor, Fig. 13 = ABS). Mitchell does not show the harness
  joint connectors, so the joint pin numbers for those circuits come from the 1990 ST185 / 1992 EWD132U books. Those rows
  are tagged **[90/92]**: the 1990 and 1992 books agree on them, but they are not 1993-verified.
- "Kept side" = the end on a harness Daniel keeps (Cowl, ER Main outer loop, A/C No.1/No.2, Floor, etc.).
- Re-feed slot names are taken from `cad/fusebox/src/spec.py` (POWER AMI: HTR, EFI, STR, FAN, FAN2, PWR / BUS1, RTR, AM1, AM2, JB1, EPS;
  LOGIC BUS1: EFI86, HL, HR, HZ, DM, WL, ALM...; BUS2: ... ACC, ...; micro relays HEAD LH/RH, horn, k_acc, k_rev).

**Joint-code corrections to the brief (checked against 1993 p.37 / p.43 / p.63 / p.83 / p.219)**

| Brief said | 1993 EWD actually says |
|---|---|
| IF2 / IG1 = Engine <-> Cowl (under ECU) | **IG1 + IG2** = Engine <-> Cowl (under the ECU). IF1/IF2 = Floor <-> Cowl (left kick). |
| IG2 / IH1 = Engine <-> A/C No.1 (behind glove box) | **IH1 only** = Engine <-> A/C No.1. |
| EB2 / ES1 / ES2 = Engine <-> ER No.2 | **EB2** = Engine <-> Cowl (rear of RH front fender, same spot as EB1). **ES2** = Engine <-> ER No.2 (near the distributor). ES1 is 4A-FE only. |
| EA1 / EB1 / ET1 | Confirmed: EA1 = Cowl <-> ER Main (front of RH fender), EB1 = Engine <-> Cowl, ET1 = ER Main <-> Engine (near J/B2). |
| (p.45 table) | That table's row grouping is offset too: IJ1 = Cowl <-> A/C No.1 (p.83/p.219), IK1/IK2 = front door RH. |

**Two system facts that drive the list**
- **All main power entered through the Engine Wire.** The F11 fuse box is part of J/B2 and its plug A is on the Engine Wire.
  AM1, AM2, the J/B1 feed (ET1), the R/B4 feed (EB1-3) and the J/B2 relay/fuse bus (2B-4) are all fed from the battery
  through the Engine Wire (1993 p.62). Removing the Engine Wire therefore removes every one of those feeds.
- **The OEM ECU straddles two harnesses.** ECU plug A (E9) is on the **Cowl Wire**. Plugs B (E7) and C (E8) are on the
  Engine Wire. Evidence: the plug-A pins BATT, +B, AC and ATS reach engine items only through IG1/IG2, while every pin on
  plugs B and C goes straight to engine parts (1993 p.78-81). Plug A is therefore listed in group 7.

---

## 1. EB1 - Engine Wire <-> Cowl Wire (rear side of RH front fender), gray 4-cavity

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| EB1 | 1 | B-O | IG2 from the ignition switch, **unfused** | Ignition SW I13 pin 9 (IG2). Same B-O lead also feeds J/B1 1A-5 (7.5A IGN fuse in). | Engine Wire: splice E7 -> noise filter N3-1; E9 -> ignition coil I4-1 (+), igniter I2-3 (+B); SFI resistor S14-2 -> injectors | 1993 p.66, 67, 78 | cut + cap at EB1; leave the I13-9 -> 1A-5 lead alone | The new engine harness takes switched power from the LOGIC box, not from this unfused lead. |
| EB1 | 2 | B | Starter "ST/50" signal | R/B4 starter relay pin 4 (R/B4 removed, so this whole cowl lead is dead) | Engine Wire: E5 -> starter S2 terminal 50 (A-1), cold-start injector C3-2, ES2-1 (start-injector time SW STA), and back into the cabin through IG2-20 | 1993 p.66, 78, 206 | cut + cap (or pull the lead back to R/B4) | New solenoid feed = POWER STR / k_str in the new engine harness. |
| EB1 | 3 | W | 100A ALT link output, the **R/B4 feed** | Cowl splice I9 -> R/B4 40A HEATER fuse pin 1 + 20A FR FOG fuse pin 1 | Engine Wire splice E8 <- F11 A-3 (100A ALT) | 1993 p.62 | cut + cap | Heater is re-fed from POWER HTR 40 (master CabinPower). Fog has no slot: see group 6. |
| EB1 | 4 | - | not used on 3S-GTE (2WD only) | - | - | 1992 p.74/94 | none | |

Unclear (EB1)
- EB1-1: confirm at the car that the B-O lead is spliced to the 1A-5 feed inside the cowl wire and does not run as a separate wire from I13-9. The drawings show both legs leaving I13-9.

## 2. ET1 - Engine Room Main Wire <-> Engine Wire (near J/B2), gray 1-cavity

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| ET1 | 1 | W (engine side) / **B** (ER Main side) | J/B1 main B+ feed | ER Main B lead -> J/B1 plug 1I pin 1 (taillight relay, 15A STOP, 15A ECU-B, 30A DEFOGGER bus) | Engine Wire splice E8 <- F11 A-3 (100A ALT) | 1993 p.62, 108, 112 | re-feed J/B1 from POWER **JB1 60A** (AMI OUT-5; the master already splices it to the 1I-1 lead in the cabin); cut + cap the ET1 end | Heavy wire. With the outer loop kept, this lead runs from near J/B2 back to the left kick panel. Its ET1 end is dead after the re-feed. |

Unclear (ET1)
- Should the cabin-end re-feed stay as in the master (splice at 1I-1), or should the old ER Main B lead be pulled out entirely? Daniel's call at the car.

## 3. IG1 / IG2 - Engine Wire <-> Cowl Wire (under the ECU)

IG1 is 18 cavities (no 9 or 10). IG2 is dark gray, 20 cavities. 1993 face p.43 shows IG2 cavities 1, 2 and 10 as "X", but the 1992 face p.45 shows all 20.

### IG1

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| IG1 | 1 | - | not used (vacuum-type cruise only) | - | - | 1992 p.186 | none | |
| IG1 | 2 | P | IDL to cruise ECU | Cruise ECU plug B pin 9 IDL (removed, earlier plan) | ECU plug C pin 12 IDL / Engine Wire splice I7 -> TPS T1-2 | [90/92] 1990 p.119, 1992 p.181; 1993 p.80 shows "to cruise ECU" | cut + cap | Dead at both ends. |
| IG1 | 3 | L | Cruise vehicle-speed sensor signal | Cruise ECU plug A pin 7 SPD (M/T) | Speed sensor for cruise (1993 V2, on transaxle) pin 2 | [90/92] 1990 p.118; Mitchell Fig.12 "BLU" | cut + cap | |
| IG1 | 4 | B-W | A/C clutch "on" to ECU AC | OEM ECU plug A (E9) pin 10 AC | Engine Wire E5 -> compressor A4-4, J/B2 2C-6 | 1993 p.79, 210 | cut + cap | Link A/C clutch control is k_acc (master ACC rows). |
| IG1 | 5 | - | ECT only (A/T) | - | - | 1992 p.171 | none | |
| IG1 | 6 | GR-B | Cruise actuator VR3 | Cruise ECU A10 | Cruise actuator (motor type) pin 3 | [90/92] 1990 p.119; Mitchell Fig.12 | cut + cap | |
| IG1 | 7 | GR | Cruise actuator VR1 | Cruise ECU A12 | Actuator pin 1 | [90/92] | cut + cap | |
| IG1 | 8 | R-G | Cruise actuator MC | Cruise ECU B10 | Actuator pin 7 | [90/92] | cut + cap | |
| IG1 | 11 | BR | Cruise speed-sensor ground | Cowl splice I2 (USA) -> ground IE. Shared with cruise stalk C14-17 BR and cruise ECU GND A9. | Speed sensor pin 3 | [90/92] 1990 p.118, 1992 p.180 | cut + cap the IG1 branch only; **keep I2/IE** | The CSB3 stalk ground (master CSB SP-CSB-GND) lives on this splice. |
| IG1 | 12 | Y-B | Oil-pressure warning | Comb meter C14 (C) pin 6 (removed) | Engine Wire -> ES2-3 -> ER No.2 -> oil pressure SW O2-1 | 1993 p.207 | cut + cap | |
| IG1 | 13 | Y-G | Water-temp gauge | Comb meter C12 (A) pin 6 | Water temp sender W2-1 | 1993 p.207 | cut + cap | |
| IG1 | 14 | B | Tach (igniter TAC) | Comb meter C14 (C) tacho; pin number not printed (*4) | Igniter I2-4 TAC (also feeds IH1-6 -> A15-18) | 1993 p.206 | cut + cap | |
| IG1 | 15 | L-R (cowl) / R-W (engine) | Turbo (boost) meter | Comb meter C13 (B) pin 4 | Turbo pressure sensor T2-2 PIM | 1993 p.207, p.80 | cut + cap | Colour changes at the joint. |
| IG1 | 16 | R-Y | Cruise actuator L (magnetic clutch) through the cruise-cancel contact | Stop-light SW (with cruise), cruise contact R-Y (1992 "S10 pin 4"; Mitchell Fig.12 RED-YEL) -> cruise ECU B3 | Actuator pin 5 | [90/92]; Mitchell Fig.12 | cut + cap | Do not disturb the S9-1 G-W stop lead (CSB3 / RearLights tap). |
| IG1 | 17 | GR-R | Cruise actuator VR2 | Cruise ECU A11 | Actuator pin 2 | [90/92] | cut + cap | |
| IG1 | 18 | P-B | Cruise actuator MO | Cruise ECU B4 | Actuator pin 6 | [90/92] | cut + cap | |

### IG2

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| IG2 | 1 | L-Y (cowl) / Y (engine, p.79) or L-Y (engine, p.210) | ECU ATS <-> A/C amp A15-2 | OEM ECU plug A pin 7 ATS | Engine Wire -> IH1-1 -> A15-2 | 1993 p.79, 210 | **?** if the Link needs the A15 ATS/idle-up signal, run a new wire from IH1-1 (A/C No.1 side) to a Link input; otherwise cut + cap | 1993 face p.43 shows cavity 1 as X. |
| IG2 | 2 | P | MIL (ECU W) to DLC1 "W" | Cowl splice I6 -> comb meter C12 (A) pin 3 + ECU plug A pin 5 W | DLC1 (check connector) pin 2 W | 1993 p.81, 79 | cut + cap | 1993 face p.43 shows cavity 2 as X. |
| IG2 | 3 | W-L | SRS TC to DLC1 | Centre airbag sensor assy pin 12 TC (removed) | DLC1 TC (15) | [90/92] 1992 p.200; Mitchell Fig.12 "check conn" | cut + cap | |
| IG2 | 4 | R-L | Back-up SW feed (GAUGE 15A) | J/B3 3B-9 (GAUGE via 1E-5) | Back-up light SW B1 pin 2 (M/T) | [90/92] 1990 p.82, 1992 p.132 | **?** reuse as the feed for the new engine-harness back-up SW lead (the master REV row already taps 3B-9 R-L), or cut + cap | |
| IG2 | 5 | G | FC (fuel-pump control) | Circuit opening relay C9-4 (cowl, removed) | ECU A14 FC (drawn crossing here) | 1993 p.78, 79 | cut + cap | Drawing anomaly: C9 and ECU plug A both look like cowl parts. Dead either way. |
| IG2 | 6 | W-L | TC diagnostic (cruise + ABS) | Cruise ECU B7 TC; IF1-3 -> ABS ECU TC | DLC1 TC (15) | [90/92] 1990 p.118/124, 1992 p.180/192 | cut + cap | |
| IG2 | 7 | P | BATT (EFI 15A) | OEM ECU plug A pin 1 BATT | J/B2 2C-4 (15A EFI) | 1993 p.79 | cut + cap | |
| IG2 | 8, 9 | - | 4A-FE only | - | - | 1992 p.108 | none | |
| IG2 | 10, 11 | - | no wire found | - | - | - | none | |
| IG2 | 12 | BR | SRS warning (LA) to DLC1 AB | Cowl splice I4 -> comb meter C12 (A) pin 8 + centre airbag sensor pin 9 LA | DLC1 AB (12) | 1993 p.207; 1992 p.200 | cut + cap | |
| IG2 | 13 | R-B | Back-up lamp output | IF1-7 -> Floor -> BP1-8 -> rear back-up lamps | Back-up SW B1 pin 1 | [90/92] 1992 p.132 | cut + cap | Rear floor wire is missing (R55); RearLights harness is new. |
| IG2 | 14 | BR | Water-temp gauge ground | Comb meter C12 (A) pin 5 | Ground EC (intake manifold) | 1993 p.207 | cut + cap | |
| IG2 | 15 | B-R | ECU-IG 15A | J3 junction conn <- J/B1 1B-8 (15A ECU-IG) | Alternator IG (G2 A-2); cruise speed sensor pin 1 [90/92] | 1993 p.74; 1992 p.180 | reuse per the master (HeavyDC ALTIG: IG2-15 cowl side -> kill-switch ALT1) | |
| IG2 | 16 | Y | Charge lamp (alternator L) | Cowl splice I5 -> comb meter C14 (C) pin 8 (+ Canada retract relay) | Alternator L (G2 A-1) | 1993 p.74 | reuse per the master (EngineRoom-C ALTL: ALT-PLUG 2 -> IG2-16) | |
| IG2 | 17 | W-R | ABS TS | IF1-16 -> ABS ECU TS | DLC1 TS (16) | [90/92] 1992 p.192 | cut + cap | |
| IG2 | 18 | B-Y | +B from EFI main relay | Cowl splice I6 -> ECU plug A pins 12 (+B) and 13 (+B1), circuit opening relay C9-2 | J/B2 2C-10 / Engine Wire splice I7 (VSVs) | 1993 p.80, 78 | cut + cap | |
| IG2 | 19 | L-B | Fuel-pump + (FP check) | Cowl splice I1 -> IE2-19 (R/B5 FP relay/resistor) and IF1-15 -> BP1-12 -> fuel pump | DLC1 FP | 1993 p.79, 78 | cut + cap | The fuel pump is re-done by the RearFuel harness and k_fp. |
| IG2 | 20 | B | STA (cranking) | Cowl splice I6 -> ECU plug A pin 11 STA, C9-3, comb meter C13 (B) pin 10 | Engine Wire <- EB1-2 (starter relay out) | 1993 p.78, 206 | cut + cap | |

Unclear (IG1/IG2)
- **IG2 cavities 1 and 2**: the 1993 face drawing (p.43) shows "X", yet 1993 p.79/p.81/p.210 put the ATS and MIL wires on IG2-1 and IG2-2 (1992 face shows all 20). Check at the car.
- IG2-1 engine-side colour: p.79 says Y, p.210 says L-Y. Dead once the Engine Wire is gone, but it matters if the cavity is used to identify the wire.
- IG2-5 (FC): the drawing's route does not fit the harness tables (see note). Dead either way.
- All [90/92] pins (cruise, ABS, SRS, back-up) need a 1993 confirmation at the car: no 1993 TIS page exists for those systems here.
- Cruise actuator routing: 1992 p.181 labels IG1 as "2WD" and IE2 as "All-Trac". The All-Trac-only 1990 book (p.119) puts it on IG1, and so does the 1992 All-Trac ground note. I went with IG1.

## 4. IH1 - Engine Wire <-> A/C No.1 Wire (behind the glove box), 6 cavities (2 = none)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| IH1 | 1 | L-Y | A15 -> ECU ATS | A/C amplifier A15 pin 2 | Engine Wire -> IG2-1 -> OEM ECU plug A pin 7 | 1993 p.79, 210 | **?** new wire to a Link input if wanted; else cut + cap | Not a compressor wire. |
| IH1 | 3 | Y-B | Compressor sensor coil (*1 = ex. 5S-FE M/T, so it applies to 3S-GTE) | A15 pin 5 | Compressor A4 pin 3 | 1993 p.210 | **new wire**: IH1-3 A/C No.1 side -> A4-3 in the new engine harness | Not in the brief's list (2, 9, 14, 18). Added. |
| IH1 | 4 | W-R | Compressor lock sensor | A15 pin 14 through cowl/A-C splice I12 (I12 also feeds A24 A/C thermistor pin 1: keep it) | Compressor A4 pin 2 | 1993 p.210, 211 | **new wire**: IH1-4 -> A4-2 | |
| IH1 | 5 | W-L | Compressor lock sensor | A15 pin 9 | Compressor A4 pin 1 | 1993 p.210 | **new wire**: IH1-5 -> A4-1 | |
| IH1 | 6 | B | Engine-speed pulse for compressor lock detection | A15 pin 18 | Igniter I2-4 TAC ("from igniter") | 1993 p.211 | **re-feed**: new wire from a Link tacho output (Aux) to IH1-6 / A15-18 **?** | Without this, A15 may flag a locked compressor and kill the clutch. |

Unclear (IH1)
- A15-18 needs an rpm pulse. Which Link output and signal level does A15 accept (igniter TAC was 12 V open-collector)? This needs Daniel's decision.
- A15-2/ATS: is it needed with the Link at all? (OEM function: A/C-on/idle-up handshake between the amplifier and the ECU.)

## 5. EB2 (Engine <-> Cowl, A/C pressure SW) and ES2 (Engine <-> Engine Room No.2)

### EB2 - Engine Wire <-> Cowl Wire (rear of RH front fender), gray, 2 of 4 cavities used

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| EB2 | 1 | V-R | A/C 10A fuse out to the dual-pressure SW | Cowl splice I9 -> R/B4 10A A/C fuse pin 2 (the same V-R bus feeds the A/C amp/control side) | A/C dual-pressure SW A5 pin 1 | 1993 p.211 | cut + cap at EB2; the A5 feed is the master's new ACPS run | The R/B4 A/C fuse is removed, so the cowl V-R bus needs a re-feed (group 6, R/B4). |
| EB2 | 2 | Y-R | Pressure-SW output to the A/C amp | Cowl splice E10 -> IJ1-11 -> A15-13; and A3 A/C idle-up VSV pin 2 | A5 pin 4 | 1993 p.211 | **reuse**: the new engine-harness A5-4 lead lands on the EB2-2 cowl side (master ACC rows: A18-13 / SP-AC-PSW) | |
| EB2 | 3, 4 | - | no cavity | - | - | p.37 | none | |

### ES2 - Engine Wire <-> Engine Room No.2 Wire (near the distributor), gray 6-cavity (5 used)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| ES2 | 1 | B | STA to the start-injector time SW | none (ER No.2 removed) | Engine Wire E5 -> S1 pin 1 STA | 1993 p.66 | remove with the harness | |
| ES2 | 2 | BR | Sensor ground E2 | none | E5 <- ECT sensor E4 pin 1 | 1993 p.80 | remove | |
| ES2 | 3 | Y-B | Oil-pressure SW | none | IG1-12 -> oil pressure SW O2 pin 1 | 1993 p.207 | remove | The new cluster/Link needs its own oil-pressure input (new harness). |
| ES2 | 4 | G | STJ (cold-start injector / time SW) | none | Engine Wire E7: ECU B7 STJ + C3-1 -> S1 pin 2 | 1993 p.66, 79 | remove | |
| ES2 | 5 | R | THW (coolant temp) | none | ECU C4 THW -> E4 pin 2 | 1993 p.80 | remove | |
| ES1 | - | - | 4A-FE only (near the starter) | - | - | p.41 | n/a | |

**Decision - Engine Room No.2 Wire: REMOVE.** On the 3S-GTE its only joint is ES2 (all 1990/1992/1993 tables), and all 5 of its
circuits are engine-mounted: start-injector time SW S1, coolant temp sensor E4, oil pressure SW O2. It carries nothing to the
body, so no kept-harness interface exists.

Unclear (EB2/ES2)
- E10 (the Y-R splice) and A3 (A/C idle-up VSV): p.219 lists E10 as "Engine Wire", but the drawing only works if E10 is a cowl
  splice. A3 is listed on p.219 but is absent from the 3S-GTE engine-bay location page (p.28). Does the car have an A3 VSV, and on which harness?

## 6. J/B No.2 (with F11) and R/B No.2-5 - every plug, and which kept harness each wire continues into

### J/B No.2 (near the battery, LH front) - All-Trac layout 1993 p.23, inner circuit p.24

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| 2A (ER Main) | 2 | L-R | 30A CDS FAN out | ER Main -> A/C condenser fan motor A2 pin 2 | J/B2 CDS FAN fuse | p.210 | **re-feed** POWER FAN2 30 (k_fan2) **?** | Pairing CDS -> FAN2, RDI -> FAN is my guess. |
| 2A | 3 | R | 15A HEAD LH out | ER Main -> headlight H1 pin 3 | J/B2 HEAD LH | p.116 | **re-feed** LOGIC HL + HEAD LH relay (cut at J/B2, splice the new feed onto the existing R lead) | Master has a new run K-HL 87 -> H1-3; with the outer loop kept, the old lead can be reused. |
| 2A | 4 | B-R | Radiator fan + (relay No.1 / CDS relay No.2 paths) | ER Main -> radiator fan motor R1 pin 2 | J/B2 rad fan relay No.1 + 2D-2 node | p.210 | **re-feed** POWER FAN 40 (k_fan) | R1 pin 1 W-B -> E3 -> EA stays. |
| 2A | 5 | W-B | Relay/coil ground node | ER Main -> ground EB (front left fender) | J/B2 ground node (relay coils, noise filter, cruise actuator, W3) | p.62, 67, 210 | cut + cap (or remove the lead to EB) | |
| 2A | 6 | R-Y | 15A HEAD RH out | ER Main -> headlight H2 pin 3 | J/B2 HEAD RH | p.116 | **re-feed** LOGIC HR + HEAD RH relay | |
| 2B (Engine) | 2 | W | AM1 in (F11 A-2) + alternator S | - (removed harness) | F11 A-2 / 2B-5 jumper | p.62, 74 | gone with the Engine Wire | Inside J/B2, 2B-2 = 2B-5 = 2E-5. |
| 2B | 3 | B-R | AM2 in (F11 A-7) | - | F11 A-7 | p.62 | gone | Inside J/B2, 2B-3 = 2E-6. |
| 2B | 4 | W | J/B2 B+ bus from FL MAIN | - | Battery (FL MAIN 2.0L) | p.62, 116 | gone | Feeds HEAD/RTR/EFI/DOME/HAZ-HORN and the headlight relay. |
| 2B | 5 | W | to alternator S (G2 A-3) | - | - | p.74 | gone | |
| 2C (Engine) | 1, 3, 4, 5, 6, 10 | LG-B, W, P, W-B, B-W, B-Y | fan relay coil / W3 path, ALT->engine main relay, EFI BATT, ground, A/C clutch, EFI +B | - | - | p.62, 79, 210 | gone with the Engine Wire | p.24 and p.79 swap 2C-4/2C-10 (EFI fuse vs relay). Irrelevant once removed. |
| 2D (ER Main) | 1 | B-W | A/C clutch power hop (R/B5 -> J/B2 -> 2C-6 -> compressor) | ER Main splice E2 -> R/B5 clutch relay pin 3 + condenser fan relay No.3 coil pin 1 | J/B2 (to 2C-6) | p.210 | cut + cap | The compressor clutch is now k_acc -> A4-4 (master). |
| 2D | 2 | B-R | Rad-fan + from condenser fan relay No.2 | ER Main -> R/B5 condenser fan relay No.2 pin 5 | J/B2 node to 2A-4 | p.210 | cut + cap | |
| 2D | 3 | W | Headlight relay out | ER Main W jumper loop -> 2D-6 | J/B2 headlight relay pin 1 | p.62, 116 | cut (remove the loop) | |
| 2D | 5 | LG-B | Fan relay coil (-) to the water-temp SW path | ER Main -> R/B5 condenser fan relay No.2 coil pin 2 | J/B2 (to 2C-1) | p.210 | cut + cap | |
| 2D | 6 | W | HEAD fuse bus in (from 2D-3 loop) | ER Main loop (see 2D-3) | - | p.62, 116 | cut | |
| 2E (ER Main) | 2 | W | 30A RTR out | ER Main -> IE1-3 -> retract control relay R8 pin 3 | J/B2 RTR | p.116 | **re-feed** POWER RTR 30 (master: AMI OUT-2 -> IE1-3) | Under the new plan the splice can sit at the J/B2 end instead of IE1. |
| 2E | 3 | W | 15A HAZ-HORN out | ER Main -> R/B5 horn relay pin 3, and -> IE1-12 -> hazard SW H5-8 | J/B2 HAZ-HORN | p.130, 185 | **re-feed** LOGIC HZ 15 (hazard) + horn relay feed | |
| 2E | 4 | L-Y | 20A DOME out | ER Main -> J/B1 1H-2 | J/B2 DOME | p.132, 200, 207 | **re-feed** LOGIC DM 20 (master: BUS1-5 -> JB1 1H-2) | |
| 2E | 5 | W | AM1 out | ER Main -> IE1-10 -> cowl I2 -> ignition SW I13-4 (AM1) + R/B2 30A POWER fuse pin 1 | F11 AM1 via 2B-2 | p.62, 66 | **re-feed** POWER AM1 40 (master: AMI OUT-3 -> IE1-10) | |
| 2E | 6 | B-R | AM2 out | ER Main -> IE1-17 -> ignition SW I13-10 (AM2) | F11 AM2 via 2B-3 | p.62, 66 | **re-feed** POWER AM2 30 (master: AMI OUT-4 -> IE1-17) | |
| 2E | 7 | R-Y | Headlight relay coil | ER Main -> IE1-2 -> cowl I2 -> light control SW C15 A-14/A-13, retract relay R8-8 | J/B2 headlight relay coil pin 3 | p.116 | **re-feed** LOGIC HEAD LH/RH relay coils (master SP-HEAD-COIL -> IE1-2) | |
| 2E | 8 | B-O | IGN 7.5A to the relay coils | ER Main splice E13 (w/o ABS) or E4 (w/ ABS) <- J/B1 1H-7; the same splice feeds R/B5 condenser fan relay No.2 coil pin 1 | J/B2 coils (EFI main relay, engine main relay, rad fan relay No.1) | p.210, 79 | cut + cap at J/B2 (and at R/B5) | 1H-7 itself stays (master taps it for IG2WAKE/IGNSW). |
| F11-A (Engine) | 2 / 3 / 4 / 7 | W / W / B / B-R | AM1 out / 100A ALT / FL MAIN in / AM2 out | - | battery cable, alternator B | p.62, 64 | gone with the Engine Wire | F11 = the fuse box built into J/B2 (p.23). |
| F11-C | 1 | W-L | 60A ABS out | ER Main splice E12 -> ABS relays (removed) | F11 60A ABS | p.62; 1992 p.192 | cut + cap | |

### R/B No.2 (left kick panel, cowl) - power main relay + 30A POWER fuse

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| R/B2 POWER fuse | 1 | W | AM1 branch in | Cowl splice I2 <- IE1-10 (AM1) | - | p.62 | cut + cap | |
| R/B2 POWER fuse | 2 | W-L | 30A POWER out | Cowl I1/I4 -> power main relay 4, door lock ECU, sunroof, power seat, etc. | - | p.137 | **re-feed** LOGIC WL 15 (master BUS1-6 -> RB2 2) | |
| R/B2 power main relay | 1 | W-G | Window/accessory power out | Cowl I1 -> IC1-3, IK1-3 (windows) | - | p.137 | **re-feed** POWER PWR 30 + power relay (master K-PWR 30) | |
| R/B2 power main relay | 2 | L-Y | Coil + (GAUGE via key-off diode D6) | Cowl I1 / D6 | - | p.136, 137 | **reuse** as the power-relay coil trigger (master K-PWR 86) | |
| R/B2 power main relay | 3 | W-B | Coil ground | Cowl -> ground | - | p.137 | cut + cap | |
| R/B2 power main relay | 4 | W-L | Contact in | Cowl I1/I4 (POWER fuse out) | - | p.137 | cut + cap | |

### R/B No.3 (right kick panel, cowl) - fog light relay [90/92] (no 1993 fog page)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| R/B3 fog relay | 4 | G-R | Contact in (20A FOG) | R/B4 FOG fuse pin 2 (removed) | - | 1992 p.128 | **?** | |
| R/B3 fog relay | 1 | R-W | Fog lamp feed | Cowl -> EA1-6 -> ER Main E1 -> fog lights F1-2 / F2-2 | - | 1992 p.128 | **?** re-feed (no fog slot in spec.py) or cut + cap | |
| R/B3 fog relay | 2 | R-W | Coil + (low-beam on, I2) | Cowl I2 (low-beam R-W line, IE1-18) | - | 1992 p.128 | **?** | |
| R/B3 fog relay | 3 | G-B | Coil - (fog SW) | Fog SW (1992 F11) pin 6 | - | 1992 p.128 | **?** | |

### R/B No.4 (right kick panel, cowl)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| Starter relay | 1 | B-W | Coil + (ST1) | Cowl I8/I9 <- ignition SW I13-7 ST1 | - | p.66, 78 | **reuse** as the crank signal (master B30: RB4-1 -> LOGIC BUS2-13) | |
| Starter relay | 2 | B-W | Contact in (ST1) | Cowl I8/I9 <- I13-7 | - | p.66 | cut + cap | |
| Starter relay | 3 | B | Coil - through the clutch start SW | Clutch start SW C11 pin 1 | - | p.66 | **reuse** (master CSB3 CLUTCH: C11-1 -> CSB3 20) | |
| Starter relay | 4 | B | Starter out | Cowl -> EB1-2 (dead after removal) | - | p.66, 78 | cut + cap | |
| Heater relay | 1 | L-W | Coil - from the A/C amp HR | IQ2-9 -> A31/A32 auto amp HR (A11) | - | p.215 | **reuse** -> K-HTR 85 (master) | |
| Heater relay | 3 | R-L | Coil + (GAUGE via J4) | Cowl J4 | - | p.215 | **reuse** -> K-HTR 86 (master) | |
| Heater relay | 4 | B | Blower + out | Cowl J5 -> blower B4 pin 2, and -> R/B4 10A A/C fuse pin 1 | - | p.215, 211 | **re-feed** from K-HTR 87 / SP-HTR87 (master) | The A/C fuse path is gone with R/B4 (next rows). |
| Heater relay | 5 | L | Contact in | R/B4 40A HEATER fuse pin 2 | - | p.215 | cut + cap | |
| Heater relay | 2 | W-B | 87a = ground | R/B4 plug A pin 4 -> ground IG | - | p.215 | cut + cap (the POWER heater relay grounds its own 87a, B15) | |
| 40A HEATER fuse | 1 / 2 | W / L | Feed in (from EB1-3 via I9) / out to the heater relay | Cowl I9; heater relay pin 5 | - | p.62, 215 | cut + cap | |
| 20A FR FOG fuse | 1 / 2 | W / G-R | Feed in (I9) / out to R/B3 fog relay pin 4 | Cowl I9; R/B3 | - | p.62; 1992 p.128 | **?** (fog decision) | |
| 10A A/C fuse | 1 | B | In from heater relay 4 (J5) | Cowl J5 bus | - | p.211, 215 | cut + cap | |
| 10A A/C fuse | 2 | V-R | A/C IG out | Cowl I9 -> EB2-1 (A5) and the V-R bus to the A/C control/amps | - | p.211, 212 | **re-feed?** - LOGIC ACC 10 is (by its use in the master) the clutch fuse; the A/C amp/control V-R feed needs a slot **?** | Must confirm the V-R loads on p.212-216 before choosing. |

### R/B No.5 (engine compartment front right, ER Main) - the "A/C clutch relay box" in 1993

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| Horn relay | 3 | W | HAZ-HORN feed (coil + contact) | ER Main -> J/B2 2E-3 | - | p.185 | cut + cap | |
| Horn relay | 2 | G | Coil - to the horn SW | ER Main -> IE1-19 -> horn SW C15-10 | - | p.185 | **reuse** -> LOGIC horn relay 85 (master K-HORN 85 -> IE1-19) | |
| Horn relay | 1 | G-R | Horn + | ER Main -> horns H3-1, H4-1 | - | p.185 | **re-feed** from the LOGIC horn relay 87 (splice onto the G-R lead at R/B5) | |
| A/C mag clutch relay | 1, 5 | R-L | Coil + / contact in (GAUGE) | ER Main <- J/B1 1H-1 (GAUGE 15A) | - | p.210 | cut + cap | |
| A/C mag clutch relay | 2 | L-Y | Coil - (A/C amp MGC output) | ER Main -> EA1-3 -> cowl -> IJ1-1 -> A15 pin 8 | - | p.210, 211 | **reuse?** as the A15 clutch request into k_acc **?** | Master currently uses A15-11 (ACT) for ACKILL. |
| A/C mag clutch relay | 3 | B-W | Clutch power out | ER Main E2 -> 2D-1 + condenser fan relay No.3 coil 1 | - | p.210 | cut + cap | |
| Condenser fan relay No.2 | 1 | B-O | Coil + IGN | ER Main E13/E4 <- 1H-7 | - | p.210 | cut + cap | |
| Condenser fan relay No.2 | 2 | LG-B | Coil - | ER Main -> 2D-5 | - | p.210 | cut + cap | |
| Condenser fan relay No.2 | 3 | B | Series-fan link | ER Main B jumper -> relay No.3 pin 3 | - | p.210 | cut + cap | |
| Condenser fan relay No.2 | 4 | W-B | NC to ground | ER Main E2 -> E3 -> EA | - | p.210 | cut + cap | |
| Condenser fan relay No.2 | 5 | B-R | Rad fan + | ER Main -> 2D-2 | - | p.210 | cut + cap | |
| Condenser fan relay No.3 | 5 | B-W | Condenser fan motor (-) | ER Main -> A/C condenser fan motor A2 pin 1 | - | p.210 | **re-ground** A2-1 to EA (or new fan control) **?** | A2's ground ran through R/B5. |
| Condenser fan relay No.3 | 1 / 2 / 3 | B-W / W-B / B | Coil + (clutch on) / coil - (ground) / series link | ER Main E2 / E2-E3-EA / relay No.2-3 | - | p.210 | cut + cap | |
| Fuel pump relay | 1 | L-O | Contact common (from the circuit opening relay) | ER Main -> IE2-18 -> cowl -> C9-1 | - | p.78 | cut + cap | |
| Fuel pump relay | 2 | L-W | Low-speed out to the resistor | ER Main -> fuel pump resistor F10 pin 2 | - | p.78 | cut + cap | F10 is removed. |
| Fuel pump relay | 4 | L-B | Hi-speed out | ER Main E3 -> F10-1 and IE2-19 -> I1 -> IF1-15 -> fuel pump | - | p.78 | cut + cap | |
| Fuel pump relay | 3 | G-R | Coil (ECU FPR) | ER Main -> IE2-20 -> cowl -> OEM ECU plug A pin 6 | - | p.78, 79 | cut + cap | |

Unclear (group 6)
- **Fog lights**: they are on the kept ER Main outer loop but were fed through R/B3/R/B4. Daniel's keep-list doesn't mention them. Keep (needs a fuse + relay slot) or delete?
- **A/C IG feed** (R/B4 10A A/C, V-R bus): which spec.py slot feeds the A/C amps/control once R/B4 is gone?
- **Fan mapping**: should FAN 40 drive the radiator fan and FAN2 30 the condenser fan? And should the OEM series/parallel two-fan logic (R/B5 relays No.2/No.3) be dropped?
- p.24 vs p.79 disagree on 2C-4/2C-10 (EFI fuse vs EFI relay output). Irrelevant: 2C goes with the Engine Wire.
- R/B2/R/B4 also carry unlabeled multi-pin plugs (p.26/27). Their cavity-level pinout is not in the 1993 pulls; the relay/fuse terminals above are what the system pages reference.

## 7. Removed parts sitting on kept harnesses

### 7a. OEM ECU plug A (E9) - on the Cowl Wire (plugs B/E7 and C/E8 go with the Engine Wire)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| E9 (ECU A) | 1 | P | BATT | IG2-7 (dead) | OEM ECU | p.79 | cut + cap | |
| E9 | 2 | O | ELS (tail/defog load) | J/B1 1D-6 | OEM ECU | p.79 | cut + cap | |
| E9 | 4 | G-W | STP | J2 junction <- stop light SW | OEM ECU | p.79 | cut + cap | The CSB3/RearLights taps are on S9-1 G-W. |
| E9 | 5 | P | W (MIL) | Cowl I6 -> comb meter C12-3, IG2-2 | OEM ECU | p.79, 81 | cut + cap | |
| E9 | 6 | G-R | FPR | IE2-20 -> R/B5 FP relay 3 | OEM ECU | p.79 | cut + cap | |
| E9 | 7 | L-Y | ATS | IG2-1 (-> IH1-1 -> A15-2) | OEM ECU | p.79 | **?** see IH1-1 | |
| E9 | 9 | L-W | SPD | J2 junction <- speed sensor in the comb meter (C13-6) | OEM ECU | p.79 | cut + cap | |
| E9 | 10 | B-W | AC | IG1-4 | OEM ECU | p.79 | cut + cap | |
| E9 | 11 | B | STA | Cowl I6 <- IG2-20 | OEM ECU | p.80 | cut + cap | |
| E9 | 12 / 13 | B-Y | +B / +B1 | Cowl I6 <- IG2-18 | OEM ECU | p.80 | cut + cap | |
| E9 | 14 | G | FC | IG2-5 / C9-4 | OEM ECU | p.79 | cut + cap | |
| E9 | 21 | LG-B | ACT (A/C cut) | IJ1-3 (G-Y on the A/C No.1 side) -> A15 pin 11 | OEM ECU | p.79 | **?** this lead could carry ACT to the Link plug A; the master instead taps A15-11 (ACKILL -> ECU-A 18) | |

### 7b. Circuit opening relay C9 (cowl, next to the ECU) - gone per DECISIONS B9

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| C9 | 1 | L-O | FP out | IE2-18 -> R/B5 FP relay 1 | C9 | p.78 | cut + cap | |
| C9 | 2 | B-Y | +B | Cowl I6 <- IG2-18 | C9 | p.78 | cut + cap | |
| C9 | 3 | B | STA coil | Cowl I6 <- IG2-20 | C9 | p.78 | cut + cap | |
| C9 | 4 | G | FC | IG2-5 | C9 | p.78 | cut + cap | |
| C9 | 6 | W-B | E1 ground | J/B3 3B-2 -> 1E-4/1A-4 -> ground ID | C9 | p.78 | cut + cap | |

### 7c. SRS - centre airbag sensor assembly (cowl, under the console), front sensors, squib (Mitchell Fig.12 = 1993; 1992 p.200 agrees)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| Centre airbag sensor | 1 | B-R | IG1 (ECU-IG) | J/B1 1C-3 (ECU-IG 15A) | SRS | Mitchell Fig.12 | cut + cap | |
| Centre airbag sensor | 2 / 3 | W / R | SR- / SR+ | Right front airbag sensor (1993 F4) | SRS | Fig.12; 1992 p.200 | cut both ends, remove | |
| Centre airbag sensor | 4 / 5 | R / W | SL+ / SL- | Left front airbag sensor (F3) | SRS | Fig.12 | cut both ends, remove | |
| Centre airbag sensor | 6 | G-R | B (ECU-B) | J/B1 1C-1 + cowl I4 -> comb meter C12-7 (SRS light +) | SRS | Fig.12 | cut + cap | |
| Centre airbag sensor | 7 | B-O | IG2 (IGN) | J/B1 1C-4 (7.5A IGN) | SRS | Fig.12 | cut + cap | |
| Centre airbag sensor | 8 / 13 | W-B | E2 / E1 grounds | ground IE / R/B4 ground (IG) | SRS | Fig.12 | cut + cap | |
| Centre airbag sensor | 9 | BR | LA (warning light) | Cowl I4 -> comb meter C12-8 + IG2-12 | SRS | Fig.12; p.207 | cut + cap | |
| Centre airbag sensor | 10 / 11 | W / R | D- / D+ (squib) | Spiral cable -> squib | SRS | Fig.12 | cut + cap at the column | |
| Centre airbag sensor | 12 | W-L | TC | IG2-3 | SRS | Fig.12 | cut + cap | |
| Centre airbag sensor | 14 | GR | ACC | J/B1 1C-2 (CIG & RADIO) | SRS | Fig.12 | cut + cap | |
| Front airbag sensors F3 (LH) / F4 (RH) | 1 / 2 | R / W | sensor loops | Cowl Wire runs along each front fender (no joint drawn) | SRS | 1993 p.28 (location); 1992 p.200 | remove the leads back to the cowl trunk | |

### 7d. ABS - ECU (body, 4WD, 2 plugs), actuator A7/A8 + relays A11/A12 + check conn A9/A10 (ER Main, RH front, through ID1)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| ABS ECU 26-pin | 1,3,5,6,9,11-16,18,19,22-26 | see Fig.13 | solenoids SFR/SFL/SRR/SRL, MR/MT/AST/R-, sensors FR+/FR-/FL+/FL-, TC, IG1, BAT, GND | Floor/ER Main/Cowl via ID1 (actuator/relay/LH front sensor), IF1 (RH front sensor, TC), J/B1 1F-11 (BAT), 1F-13 (IG1) | ABS ECU | Mitchell Fig.13; 1992 p.192 | cut + cap at the ECU plugs; remove the ID1-side solenoid leads | |
| ABS ECU 16-pin | 1,3,6-10,12-16 | see Fig.13 | rear sensors RL/RR, decel sensor GS1/GS2/GST, STP, W, PKB, TS | Floor/Luggage (rear sensors), decel sensor, J2 (STP), comb meter ABS light (IF1-9), J/B1 1F-8 (PKB), IF1-16 -> IG2-17 (TS) | ABS ECU | Mitchell Fig.13 | cut + cap | |
| ABS actuator A7/A8, relays A11/A12, check conn A9/A10 | all | (1992 p.192) | solenoids, pump motor, relay coils, 60A ABS feed (W-L via E12), grounds to EA | ER Main (RH front) via ID1 4,2,1,5,9,10,7,11,12,6 | ABS | 1992 p.192 | remove the ER Main branch back to the trunk; cap ID1 cavities | |
| Wheel-speed sensors (A13 LH via ID1-13/8, A14 RH via IF1-10/4, rears) | 1 / 2 | B / W | sensor pairs | ER Main / Cowl / Floor | kept sensors | 1992 p.192 | cut at the sensor plugs; the new WheelSpeed-Front/-Rear harnesses take over | Sensors are kept, OEM leads are not. |

### 7e. Cruise ECU, motor type with ABS (earlier plan) - Mitchell Fig.12 (1993)

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| Cruise ECU A | 1 IGB B-R, 2 STP+ G-R, 3 STP- G-W, 4 N&C B, 5 PKB R-G, 7 SPD L-W(or L), 8 CMS Y-B, 9 GND BR, 10-12 VR3/VR2/VR1 GR-B/GR-R/GR | | | J3 (ECU-IG), stop SW, J2, clutch SW/diode, parking brake SW, stalk C14-15 (CMS), ground, IG1-6/17/7 | cruise ECU | Mitchell Fig.12; [90/92] 1990 p.118-119 | cut + cap **except** keep the stalk leads (CMS Y-B, CCS W, BR ground) for CSB3 | Every OEM cruise stalk function is kept (B9). |
| Cruise ECU B | 3 L G-B, 4 MO P-B, 6 PI LG, 7 TC W-L, 8 CCS W, 9 IDL P, 10 MC R-G | | | stop SW cruise contact, IG1-18, comb meter C12-2, IG2-6, stalk C14-5, IG1-2, IG1-8 | cruise ECU | Fig.12 | cut + cap (keep the CCS W stalk lead) | |

### 7f. Combination meter (earlier plan) - 1993 codes C12 (A), C13 (B), C14 (C), 1993 p.206-207

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| C12 (A) | 1 W-G illum, 2 LG cruise light, 3 P MIL, 5 BR temp gnd, 6 Y-G temp, 7 G-R SRS light +, 8 BR SRS LA, 9 G ABS light, 10 Y-L fuel | | | rheostat, cruise ECU PI, I6/ECU W, IG2-14, IG1-13, 1C-1/I4, I4, IF1-9, IF1-12 | meter | p.206-207 | cut + cap (keep the leads the ClusterLED harness taps) | The master uses the 1990 codes C11/C12. The 1993 book calls them C12/C13/C14. |
| C13 (B) | 1 W-B gnd, 2 G-B turn LH, 3 Y-R fuel, 4 L-R boost, 5 BR speedo gnd, 6 L-W speed out, 7 R-L GAUGE, 10 B bulb check, 11 G-Y turn RH, 12 R-L high beam | | | J/B3 3B-6, J3, IF1-14, IG1-15, J6/IF1-13, J2, 3B-9, IG2-20, J3, IE1-11 | meter | p.206 | cut + cap / reuse per ClusterLED rows | |
| C14 (C) | 1 R-G brake warn, 3 L-Y door, 4 R-W door, 5 V belt, 6 Y-B oil, 8 Y charge, 9 B-O IGN, 10 G tail illum, tacho B (pin not printed) | | | J6 (brake fluid/parking SW), 3B-10, J1, integration relay, IG1-12, I5/IG2-16, 1D-5, 3B-16, IG1-14 | meter | p.206-207 | cut + cap / reuse per ClusterLED rows | |

### 7g. Rear wiper/washer (earlier plan) [90/92] - 1992 p.150

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| Rear wiper motor & relay (1992 R24) | 1 / 2 / 3 | L / P-G / P-B | +B (WIPER 20A) / INT / ON | Back door wire BO1-4/5/6 -> BN1 -> floor IF1-11/5 -> J/B1 1F-10, rear wiper SW C17 | rear wiper | 1992 p.150 | cut + cap at J/B1 1F-10 and at the switch | |
| Washer motor W1 rear outlet | 3 | L-O | rear washer | Cowl -> rear washer SW C17-2 | W1 (front washer kept) | 1992 p.150 | cut + cap | 1993 p.148 draws W1 as 2-pin (front only); check whether the car's pump has pin 3. |

### 7h. OEM igniter, ECU plugs B/C, DLC1, cruise actuator, compressor clutch lead, back-up SW

All of these sit on the Engine Wire and leave with it. Their only kept-side interfaces are the IG1/IG2/IH1/EB1/EB2 rows above.

Unclear (group 7)
- The ABS ECU GND pin labels in Mitchell Fig.13 are partly illegible (the second row reads "GND 15"). Confirm with the ECU plug in hand.
- Front airbag sensor leads: no joint is drawn, so they are taken to be Cowl Wire. Confirm at the car.

## 8. Engine Room Main Wire branches that enter the engine area (chop)

On the 1993 3S-GTE car the ER Main Wire feeds no engine-mounted device directly. Every engine device is on the Engine Wire or the ER No.2 Wire. The ER Main reaches the engine side only through J/B2 (2C/2B hop) and ET1. The branches to chop are therefore these:

| Joint/plug | Pin | Wire colour | Circuit / signal | Kept-side destination (component + pin) | Removed-side source | EWD page | Proposed action | Note |
|---|---|---|---|---|---|---|---|---|
| ER Main -> ET1 lead | 1 | B | J/B1 feed | J/B1 1I-1 | ET1 | p.62 | chop at ET1 (re-feed as group 2) | |
| ER Main -> J/B2 branch | 2A/2D/2E all | see group 6 | headlight, fan, RTR, HAZ-HORN, DOME, AM1/AM2, IGN, ground | outer-loop loads + IE1 | J/B2 | p.23, 62, 116, 210 | chop at J/B2; splice the new POWER/LOGIC feeds onto the kept leads (group 6) | Re-feed list: HL, HR, HEAD coils, RTR, HZ + horn, DM, AM1, AM2, FAN, FAN2. |
| ER Main -> F11-C | 1 | W-L | 60A ABS | ABS relays | F11 | p.62 | chop | |
| ER Main -> R/B5 branch (RH front) | all | see group 6 | fan relays, clutch relay, horn relay, FP relay | horns, A2/R1 fans, IE1-19, IE2-18/19/20, EA1-3 | R/B5 | p.27, 78, 185, 210 | chop at R/B5; re-feed horns; re-ground A2-1 | |
| ER Main -> fuel pump resistor F10 + splice E3 (LH front) | 1 / 2 | L-B / L-W | FP low/high speed | IE2-19 | F10 | p.78 | chop, remove F10 | |
| ER Main -> ABS actuator/relay/check-conn branch (RH front) | all | 1992 p.192 | ABS | ID1 cavities 1,2,4-7,9-12 | ABS | 1992 p.192 | chop | |
| ER Main -> splice E13/E4 B-O IGN branch | - | B-O | IGN to J/B2 2E-8 and R/B5 relay No.2-1 | J/B1 1H-7 | - | p.210 | chop at both ends | |
| ER Main ground lead 2A-5 -> EB | - | W-B | relay/coil ground | ground EB (kept point) | J/B2 | p.62 | remove or cap | |

Unclear (group 8)
- I could not find a direct ER Main -> engine-mounted lead in the 1993 pages (oxygen sensor, alternator, starter, compressor, water-temp SW W3, check connector C1/C2 and A5 are all Engine Wire). A walk-around should confirm that nothing else is taped into the ER Main trunk near J/B2.

---

## Cross-check notes for the repo (not changed)
- DECISIONS **B9** says "No factory engine-bay wire, connector or box is reused", which conflicts with keeping the ER Main outer loop.
  The MASTER rows that crimp into "IE1 cowl side (engine-room main removed)" would move to J/B2/R/B5-end splices under the new plan.
- MASTER ClusterLED rows use the 1990 meter codes C11/C12. The 1993 codes are C12 (A)/C13 (B)/C14 (C).
