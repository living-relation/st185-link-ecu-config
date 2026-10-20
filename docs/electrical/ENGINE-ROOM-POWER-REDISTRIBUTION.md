# Engine-room power redistribution — 1993 ST185 All-Trac

**Decision (Dan, 2026-10-10, binding):** no factory engine-bay wire or connector is reused. J/B No.2, R/B No.2 / No.3 / No.4 / No.5, F11 and the engine-room main wire (with every factory plug and wire that ran to them) are **removed from the car**. Every engine-bay load gets new wire from the glove-box fuse box (`ST185-CabinPower`) straight to its device plug (the OEM device plug where one is recorded, DT where Dan chose DT). Cabin reuse is unchanged: J/B No.1, J/B No.3, the cowl / dash looms and the cabin side of IE1 stay, and new feeds splice into their factory cabin leads.

OEM landing facts and factory citations; the wire lists own the wiring (DECISIONS R206). Pin facts come from the 1990 ST185 All-Trac EWD (the All-Trac-specific book) cross-checked against the 1992 Celica EWD132U (covers ST185, year-adjacent to 1993). The 1993 bound book is EWD160U; the freely available PDF of that number is the FWD AT180/ST184 book, so it is **not** used as All-Trac pin authority.

Factory snips live in `docs/electrical/ewd-snips/`. The drawing is `docs/harness/rebuild/ST185-EngineRoom-C.harness`. The fuse box is in `docs/harness/rebuild/ST185-CabinPower.harness`. Cabin ECU power stays in `docs/harness/rebuild/ST185-ECU-cabin.harness` (the ECU relay coil wires).

---

## 1. Recommendation

1. Battery moves to the **trunk**. Cables run forward to a POWER box (`ST185-HeavyDC`).
2. The fuse box (two custom boxes, POWER + LOGIC, DECISIONS R75, drawn only in `ST185-CabinPower`) and every relay sit in the **passenger glove box** - except the fuel pump relay, which has its own small block at the battery in the trunk (R75, drawn in `ST185-HeavyDC`). No fuse or relay in the engine bay (R11, R12).
3. EPS power uses the vacated **passenger-side ABS actuator** path. `bh_c` stays deleted. Large cables (battery / starter / alternator charge) cross the firewall on **RADLOK**.
4. Harness C (`ST185-EngineRoom-C`) carries every new bay circuit along the approved route `docs/harness/routes/ROUTE-2-HARNESS-C.html` (rev 9).

---

## 3. Target architecture

```
TRUNK battery +  ──2 AWG / 1/0──►  POWER BOX bus ─┬─► POWER + LOGIC fuse boxes (ECU / EPS / fans / body, ex-J/B2)
                     jump lug                     │   (ST185-CabinPower, Option B)
TRUNK battery −  ──2 AWG / 1/0──►  POWER box ground     ├─► always-hot + AM1 + AM2 to kick-panel J/Bs
                                                  └─► RADLOK +  ──firewall──► starter B+ ◄── 170 A alt B+
                                                     RADLOK −  ──firewall──► engine block
                                                     engine-bay jump post on the starter B+ net
```

Glove box is passenger side, next to the blower (B4). J/B No.1, IE1 and the old R/B No.2 spot are the driver kick — a dash-cross of fused feeds, not a second battery cable.

![Dash J/B and R/B locations, EWD p.17](ewd-snips/1990-st185-locations-dash.png)

![Engine-bay J/B2 / R/B5 / ABS relays, EWD p.16](ewd-snips/1990-st185-locations-engine-bay.png)

### 3.1 Where each load gets its power

No PMU/PDM. The 40 A blower exceeds every PDM channel on the market, so it gets a Mini ISO relay + AMI fuse in the POWER box. The only logic is the ECU's own hold power. The RealDash Pi runs on a switched ignition fuse only, on and off with the car (R20). Every relay and fuse is in the cabin.

Rule: **one source per load** — never two paths feeding the same circuit.

| Load | Path | Why |
|---|---|---|
| Starter motor | Battery cable + RADLOK + existing `k_str` for solenoid | Cranking amps |
| 170 A alternator B+ (Dan 2026-10-18, DECISIONS R161 / R162) | 2 AWG to starter B+, does not recross | Heavy cable. Protected by a fusible link or inline fuse / breaker at the trunk battery or near the cabin fuse box, never at the starter (Daniel 2026-09-28): Littelfuse `880014175` (sealed MEGA SN, 175 A MEGA, 131 A continuous) on H3 at the POWER box ALT/STR stud, sizing in DECISIONS S40 |
| MRS EPS pump | `k_eps` HCR 150 in the glove box beside the fuse box (moved from the engine bay 2026-09-28; drawn on `ST185-CabinPower` since 2026-10-11), POWER AMI OUT-6 Bussmann AMI-60 (was LMI L7, HCFB H4 before that), 8 AWG feed (sized 2026-09-28, `sot/channels.csv` k_eps c1) | Too big for a micro relay |
| Uprated rad / condenser fans | `k_fan` / `k_fan2`, fuse sized to the fan's peak | Coils from Aux 5 / Ign 5 |
| EFI main, ETB, fuel pump | Relays seated in the glove-box fuse box, `ST185-CabinPower.harness` (coil wires on `ST185-ECU-cabin.harness`) | Hold-power and Link's published ETB circuit |
| HEAD LH / HEAD RH | Relay + fuse, LOGIC HL / HR, new wire to headlight H1 / H2 pin 3 | Replaces 15 A HEAD fuses + headlight relay in J/B2 |
| HAZ-HORN | LOGIC HZ fuse: hazard feed to IE1-12 (cowl side); horn relay (LOGIC M3) to a DT 2-way at each horn H3 / H4 | Replaces 15 A HAZ-HORN and the R/B5 horn relay |
| DOME | LOGIC DM fuse only, always-hot, to J/B1 1H-2 (cabin) | Replaces 20 A DOME |
| Retract motors | POWER RTR (AMI OUT-2) fuse only, to IE1-3 → OEM retract control relay R8 | Replaces 30 A RTR (DECISIONS 38) |
| Wiper / washer | J/B No.1 WIPER 20A (R61), no relay of ours | The park switch is in the motor F9 (pins 3-4) and the wiper relay is inside the switch C16 (1993 p.148); no fuse-box position (the Option B `wp` spare is gone) |
| Heater blower | POWER HTR 40 A AMI + heater relay (R1), to blower motor B4 pin 2 | R/B No.4 removed (DECISIONS 26.2) |
| Power windows | POWER PWR 30 A AMI + power relay (R6), to the W-G window feed (old R/B2 power main relay terminal 1) | R/B No.2 removed (DECISIONS 26.2). The always-hot W-L net (door lock ECU, tilt-away) is open - `docs/OPEN-ITEMS.md` |
| Wiper, gauge, turn, CIG, ECU-IG, IGN, STOP, TAIL, ECU-B, DEFOGGER | Stay as **J/B No.1** fuses (rule R61, 2026-10-13: anything in a kept cabin J/B stays fed from it) | That is why the J/B stays. We only restore its upstream B+ and IG; their bay legs (wiper motor, front turn / clearance) are new harness C wire; the rear lamps are the new `ST185-RearLights` (J/B No.1 1F-1 / 1F-3 / 1F-2 and S9 pin 1; reverse relay `k_rev` contact on the GAUGE fuse via J/B3 3B-9) |
| A/C compressor | Engine harness A/B (already drawn) | Not engine-room C |
| ABS actuator / ABS relays / 60 A FL ABS | **Deleted** | Solenoid module removed |
| Crash / SRS sensors | **Deleted** | Do not refeed the airbag IGN circuit |

The glove-box fuse box (`ST185-CabinPower`) is fed from the POWER box stud. Fuse and relay
ratings not written above are `TBD` until sized against the load.

---

## 4. Method

1. Remove J/B No.2 (2A-2E), F11, R/B No.2 / No.3 / No.4 / No.5, the engine-room main wire and every factory engine-bay wire, plus the ABS actuator, ABS relays and crash sensors. Keep J/B No.1, J/B No.3 and the cowl / dash looms; depin and plug the engine-room-main half of IE1, 1H and 1I and keep the cabin half as the splice point.
2. Build the trunk battery, POWER box and POWER + LOGIC fuse boxes with their relays, and the battery relay block in the trunk.
3. Restore always-hot at J/B1 1I-1, AM1 / AM2 at IE1-10 / IE1-17 (cowl side).
4. Land every other ex-J/B2 / R/B load per §5.4: bay loads on new wire to the device plug, cabin loads on their factory cabin lead.
5. Do **not** refeed EFI, engine-main-relay or circuit-opening-relay circuits. Link owns those (`k_efi`, `k_fp`).
6. Continuity-check every row in §5 on the car before first power-up.

---

## 5. Splice / feed table

### 5.1 Heavy DC (trunk → glove box → bay)

| # | Net | AWG | From | To | Hardware | Notes |
|---|---|---|---|---|---|---|
| H1 | Battery + | **1/0** | Trunk battery + post, jump lug | POWER box BAT+ stud, jump lug | Cable along cabin floor / tunnel | Replaces engine-bay battery + F11 FL MAIN 2.0L |
| H2 | Battery − | **1/0** | Trunk battery − , jump lug | POWER box ground + body | Bond to the cargo floor | Separate from sensor Gnd Out |
| H3 | Charge / start + | **1/0** | POWER box ALT/STR stud | RADLOK + firewall, cabin side (`RL00801-50RE`) | Feed-through is `RL9080-301-F1RE` | |
| H4 | Charge / start + | **1/0** | RADLOK + firewall, engine side (`RL00801-50RE`) | Starter B+ post, jump lug | | |
| H5 | Alternator B+ | **2 AWG** (170 A, behind the 175 A fuse; DECISIONS R162 / S40) | Alternator B+ (rear of block, under intake) | Starter B+ | Does **not** recross the firewall | Short bay jumper; factory A17 pin B, we replace that cable |
| H6 | Engine ground | **1/0** | RADLOK − firewall, engine side (`RL00801-50BK`) | Engine block stud, jump lug | Feed-through is `RL9080-301-F1` | OEM grounds EA / EB / EC stay |
| H7 | Cabin ground | **1/0** | POWER box ground | Kick-panel ground **ID** (left) and a new glove-box ground at IG (old R/B4 set bolt) | | |
| H8 | Jump post | 2 AWG | Starter B+ | Engine-bay jump post | So you can still jump-start from the bay | |

![Starting, EWD p.48 — AM1/AM2 through IE1, starter via R/B4](ewd-snips/1990-st185-starting.png)

![Charging, EWD p.52 — alt B+ is W into J/B2 / F11](ewd-snips/1990-st185-charging.png)

**SETTLED 2026-09-22 — 1/0 and RADLOK 8.0.** The old `RL00571-35` spec was wrong twice
over: Amphenol's catalogue has no `-35` (the trailing number is cable mm², and only
`-16` and `-25` exist for 5.7 mm), and 5.7 mm RADSOK is rated **120 A** — under the
170 A the alternator can push back through this crossing (DECISIONS R161).

Sizing, done properly:

| Case | Current | 2 AWG drop | **1/0 drop** | 2/0 drop |
|---|---|---|---|---|
| Alternator at rating, continuous | 170 A (R161; was 160 A) | 0.96 V | **0.61 V (4.4%)** | 0.48 V |
| Cranking, a few seconds | ~300 A | 1.69 V (13%) | **1.06 V (8.4%)** | 0.84 V |

Round trip is about **36 ft** — roughly 18 ft each way, trunk → POWER box → firewall →
starter, with a dedicated negative of similar length. 2 AWG blows past the 10%
a starter circuit is normally held to. 2/0 buys 0.2 V for a lot more money and a
much worse bend radius. **1/0 (50 mm²)** it is, which is exactly the RADLOK 8.0
cable size.

| Piece | Part | Qty |
|---|---|---|
| Firewall feed-through, positive | `RL9080-301-F1RE` — 8.0 mm RADLOK, panel mount, pin both sides, 200 A / 1 kV, IP40 mated, red | 1 |
| Firewall feed-through, negative | `RL9080-301-F1` — same, black | 1 |
| Cable connector, positive | `RL00801-50RE` — female, 200 A, 50 mm², red | 2 (one each side) |
| Cable connector, negative | `RL00801-50BK` — same, black | 2 (one each side) |

Each polarity is three pieces: the feed-through lives in the firewall, a cable
connector plugs onto each side. 200 A continuous gives 18% headroom over the
170 A alternator case (25% at the old 160 A), and a connector of this class shrugs off a few seconds of
cranking. The `-303` nickel variant is discontinued; RS names `-301` as its
replacement.

The alternator still lands on the starter post (H5), so it never needs a second
crossing.

### 5.2 Left kick panel — J/B No.1 (keep)

![J/B No.1 housing, EWD p.18](ewd-snips/1990-st185-jb1-left-kick.png)

![J/B No.1 inner circuit, EWD p.19](ewd-snips/1990-st185-jb1-inner-circuit.png)

J/B No.1 already contains: 15A ECU-IG, 20A WIPER, 15A GAUGE, 10A TURN, 7.5A IGN, 15A CIG & RADIO, 15A STOP, 15A ECU-B, 15A TAIL, 30A DEFOGGER, taillight relay, defogger relay, turn flasher, integration relay.

| # | Inject? | Connector | Pin | Signal | New source | Action |
|---|---|---|---|---|---|---|
| L1 | **YES** | **1I** (engine-room main) | **1** | Always-hot into J/B1 (STOP / ECU-B / DEFOGGER / tail-relay B+) | POWER box OEM HOT, fused 40–60 A upstream of the J/B fuses | Primary left-kick B+. Probe 1I-1 to battery + on the stock car to confirm before cutting |
| L2 | no | **1H** | **7** | IG2 from ignition switch I13-9 | I13 still feeds it via cowl | Do not overlay. Comes alive once AM2 is restored |
| L3 | maybe | **1H** | **8** | Tied to 1I-1 / 1F-8 / 1I-3 on the inner circuit | Follows L1 if the inner bus is intact | Only add a second feed if L1 does not light 1H-8 |
| L4 | no | **1A** | **7** | ACC from I13-3 | Ignition switch | Restored by AM1 (L6) |
| L5 | no | **1A** | **5** | IG1 from I13-2 | Ignition switch | Restored by AM1 (L6) |
| L6 | **YES** | **IE1** (ER main ↔ cowl, left kick) | **10** | AM1 to ignition I13-4 | POWER box AM1, **40 A** fuse (replaces F11 40A FL AM1) | Feeds the switch (the engine-room AM1 run is removed) |
| L7 | **YES** | **IE1** | **17** | AM2 to ignition I13-10 | POWER box AM2, **30 A** fuse (replaces F11 30A FL AM2) | Same |
| L8 | **YES** | Ground **ID** | stud | Left kick body ground | POWER box ground strap | See grounds, EWD p.169 |

Do not land new wires on 1A/1B/1C/1D/1E/1F/1G unless a circuit is dead after L1/L6/L7. Exception (2026-10-13, Route 15): the rear floor wire is missing, so `ST185-RearLights` takes its tail / turn feeds from the 1F-1 / 1F-3 / 1F-2 leads at J/B No.1 (R61). Those cavities are cowl / floor / roof, still OEM. The 1H / 1I / IE1 landings are cabin-side splices into the factory lead (the engine-room main wire that used to mate there is removed).

### 5.3 Right kick panel — R/B No.3 / No.4 removed

R/B No.3 (fog relay; fog lights deleted) and R/B No.4 are removed (Dan, 2026-10-10, DECISIONS 26.2). Their jobs move to the glove-box box: 40 A HEATER + heater relay → POWER box R1 (blower B4 pin 2, §5.4), 10 A A/C → MTA-3 ACPS, OEM starter relay → Link `k_str`, B30 start request → MTA-3. The right-kick body ground **IG** (old R/B4 set bolt) stays and gets a POWER box ground strap (EWD ground index p.171).

J/B No.3 (behind the combination meter) is a **cowl junction only**. It does not need a new battery feed. Do not splice it.

![J/B No.3, EWD p.22](ewd-snips/1990-st185-jb3-behind-meter.png)

### 5.4 Where each ex-J/B2 / R/B load lands (2026-10-12)

Drawn in `ST185-EngineRoom-C` (cabin and bay ends) and `ST185-CabinPower` (fuse / relay). Pins from the 1993 TIS EWD in `st185-celica-repair-manual\electrical\circuits\`. Bay ends are new wire to the device's own plug; cabin ends splice into the factory cabin lead.

| Load | From (box) | AWG | To | Where | EWD 1993 |
|---|---|---|---|---|---|
| HEAD LH | LOGIC HL 15 A + relay | 14 | H1 pin 3 (headlamp plug) | Bay, LH corner | p.116 |
| HEAD RH | LOGIC HR 15 A + relay | 14 | H2 pin 3 (headlamp plug) | Bay, RH corner | p.116 |
| Horns | LOGIC M3 (horn relay 87, HAZ-HORN 15 A) | 14 → splice → 16 each | DT 2-way at H3 and H4, c1 +; c2 16 AWG ground to EA | Bay, front centre | p.185 |
| Hazard | LOGIC HZ 15 A (before the horn relay) | 14 | IE1-12 W | Cabin, left kick | p.130 |
| DOME | LOGIC DM 20 A | 12 | J/B1 1H-2 | Cabin, left kick | p.132 |
| RTR | POWER RTR 30 A | 10 | IE1-3 W → R8 pin 3 | Cabin, left kick | p.116 |
| AM1 / AM2 | POWER AM1 40 A / AM2 30 A | 8 / 10 | IE1-10 / IE1-17 | Cabin, left kick | p.62 |
| J/B1 always-hot | POWER JB1 60 A | 6 | J/B1 1I-1 | Cabin, left kick | p.62 |
| Blower | POWER HTR 40 A + heater relay | 8 | Blower motor B4 pin 2 | Cabin, behind the glove box | p.215-216 |
| Power windows | POWER PWR 30 A + power relay | 10 | W-G window feed (old R/B2 power main relay terminal 1) | Cabin, left kick | p.137 |
| Door lock / tilt-away always-hot | LOGIC WL 15 A (R58, drawn 2026-10-12) | 14 | W-L lead at old R/B2 pin 2 → splice I1 → door lock ECU D8-8 / tilt-away ECU | Cabin, left kick | p.137 / p.170 |

Bay lighting and wipers (2026-10-13, Route 2 rev 10; no side markers, R62) - not a box output, fed from J/B No.1 per R61:

| Load | From (cabin landing) | AWG | To | Where | EWD 1993 |
|---|---|---|---|---|---|
| Front clearance | J/B1 1H-6 (TAIL 15A) | 16 | F7 / F8 pin 1 | Bay, both corners | p.112 |
| Front turn LH / RH | J/B1 1H-4 / 1H-8 (TURN 10A via flasher) | 18 | F7 / F8 pin 3 | Bay, both corners | p.130 |
| Headlamp returns | IE1-18 low (R-W), IE1-11 high (R-L) | 16 per lamp, 14 to IE1 | H1 / H2 pins 2 / 1 | Bay, both corners | p.116 |
| Retract motors | IE1-14 / 15 (R2), IE1-8 / 7 (R3), IE1-9 / 16 limits (OEM R8, RTR 30 A) | pin 4 feed and pin 5 ground 12 -> splice -> 16 pigtail (150 mm max); pin 2 16, limits 18 (DECISIONS S20) | R2 / R3 pins 1-4, ground pin 5 to EB | Bay, both corners | p.117 |
| Front wiper | J/B1 1H-5 (WIPER 20A), IE1-20 / 13 / 6 | 14 | F9 pins 4 / 1 / 2 / 3 | Bay, under the windshield cowl, driver side; feed via the driver (LH) fender pass-through (S19) | p.148 |
| Washer | cowl leads to W1 (L from splice I2, L-R from C16-8) | 14 | W1 pins 2 / 1 | Bay, passenger front corner, lower front fender (S19) | p.148 |

Relay coil wires of the box non-ECU relays: drawn 2026-10-14 in `ST185-CabinPower.harness` (`k_hl` / `k_hr` coil- to IE1-2, `k_horn` to IE1-19, `k_htr` from the old R/B4 R-L / L-W leads, `k_pwr` coil+ from the old R/B2 L-Y lead; `docs/OPEN-ITEMS.md` rows 46, 106).

### 5.5 Engine-room grounds (keep the OEM rings)

![Engine-room grounds, EWD p.168](ewd-snips/1990-st185-grounds-engine.png)

![Cabin grounds, EWD p.169](ewd-snips/1990-st185-grounds-cabin.png)

| Code | Where | Keep? | Add? |
|---|---|---|---|
| **EA** | Right front fender | Yes — lights / fans on that side | Bond uprated fan grounds here |
| **EB** | Left front fender | Yes | Bond EPS pump ground **or** use the engine-block stud (preferred for 60 A) |
| **EC** | Intake manifold | Yes, leftover OEM engine-wire grounds | Do not put EPS / fan current on EC |
| **ID** | Left kick panel | Yes | Strap from POWER box (L8) |
| **IE / IF** | Dash braces | Yes | Untouched |
| **IG** | ex-R/B No.4 set bolt (the body bolt stays; the box is removed, R12) | Yes | Strap from POWER box |

### 5.6 Deleted OEM circuits — do not restore

| Circuit | Connectors / feeds | Why |
|---|---|---|
| ABS actuator | A7, A8; 60A FL ABS; ABS relays A11/A12 | Module removed; space reused for EPS cables |
| ABS ECU / rear sensors (body) | A38, A39, A40, A41 | Wheel-speed, if kept, goes to the Link VR conditioners on A/B, not the OEM ABS ECU |
| ABS deceleration sensor | A37 | Deleted with ABS |
| SRS airbag / crash sensors | Center airbag sensor (dash, EWD p.17); yellow cowl airbag harness | Deleted. Do not refeed 7.5A IGN into the airbag ECU |
| OEM EFI main / circuit opening / OEM ECU | J/B2 EFI fuse, R/B5 fuel-pump relay, C7 | Replaced by Link `k_efi` / `k_fp` |
| OEM radiator / condenser fan relays in J/B2 and R/B5 | R/B5 fan relays 2 and 3; J/B2 RDI FAN relay | Replaced by `k_fan` / `k_fan2` |
| Rear windshield wiper and washer | Rear wiper motor, rear washer pump, their switch outputs, fuse and relay | Deleted (DECISIONS R54, Daniel 2026-10-12). The FRONT wipers / washer stay (R53) |

### 5.7 New Engine Room C runs (the only new bay wiring)

Routed with the OEM engine-room main. Passenger fender / ABS trough for EPS; core support for fans.

| # | Circuit | AWG | Path | Connector |
|---|---|---|---|---|
| C1 | EPS pump 12 V | 8 AWG (sized 2026-09-28 against the AMI-60, `sot/channels.csv` k_eps c1) | `k_eps` 87 (glove box) → passenger kick / EA1 → ABS trough → pump | `90980-12068` pin 1 (OWNED) |
| C2 | EPS pump GND | 8 AWG | Pump pin 2 → engine-block stud (not EA) | `90980-12068` pin 2 |
| C3 | EPS enable | 18 AWG | F13 7.5 A IG-switched → same trough | `90980-10942` pin 1 (OWNED) |
| C4 | EPS relay coil- (R22) | 20 AWG | Pump connector B pin 5 → bulkhead A c27 → `k_eps` coil- | `w_eps_rly_e` / `w_eps_rly_ae` / `w_eps_rly` / `w_eps_rly_cp` (2026-10-12) |
| C5 | EPS speed | 18 AWG shielded | Pump connector B pin 2 → Aux 7 / A27 | Signal file, engine harness A — **not** C |
| C6 | Rad fan 12 V | 8 AWG (size to the fan; OEM was 30 A FL) | `k_fan` 87 → core support | New DT 2-way at the fan |
| C7 | Rad fan GND | 8 AWG | Fan → EA | |
| C8 | Condenser fan 12 V | 8 AWG | `k_fan2` 87 → core support | New DT 2-way |
| C9 | Condenser fan GND | 8 AWG | Fan → EA | |
| C10 | A/C compressor VC control coil (not fitted; the clutch is A4 pin 4 from `k_acc`) | — | **ST185-EngineRoom-C** flying lead `fl_a4_3` (device side; A18-5 amplifier side is on ST185-ECU-cabin, `br_ac_mg` break), not a numbered loom-C circuit | Not on A/B; `docs/harness/ACAMP-SPUR-LABELS.md` |

Wiper, washer, headlights, turn, park and horns are new harness C wire too (§5.4 and Route 2); none of the OEM engine-room loom stays.

---

## 7. Sources

| Manual | Pub. | Why it is here |
|---|---|---|
| 1990 Celica All-Trac/4WD Electrical Wiring Diagram | ST185-only EWD (168 p.) | All-Trac J/B, F11, ABS, grounds, IE1/EA1. Snips above. |
| 1992 Celica Electrical Wiring Diagram | EWD132U | Covers ST185; year-adjacent to 1993. Same J/B No.1 / No.2 / kick-panel layout with All-Trac callouts. |
| 1993 Celica EWD160U | Dealer 265 p. book | The All-Trac pages of this book are the year-exact match. The public PDF labelled EWD160U is the **FWD** AT180/ST184 book — do not mix its J/B2 pin numbers into this table. |

On-car check before first power-up: with the battery isolated, ohmmeter from each §5.4 cabin landing to its named load (dome, R8, hazard switch, ignition I13-4 / I13-10, J/B1 1I-1, window switches, blower).

---
