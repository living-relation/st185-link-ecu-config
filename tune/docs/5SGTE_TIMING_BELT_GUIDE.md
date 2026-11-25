# 5S-GTE Timing Belt and Cam Degreeing (Engine on Stand)

Merged guide. Replaces `5SGTE_TIMING_BELT_CAM_DEGREEING.md` (FSM Rev A) and `5SGTE_TIMING_BELT_INSTALL_HKS.md` (HKS text copy), which are removed in the same PR (R211).

**Build:** 1993 Celica ST185 · 5S-FE block + 3S-GTE Gen 2 head · HKS 264 (2202-RT063 intake / 2202-RT064 exhaust) · ATS adjustable gears (±10 cam°) · ATI Super Damper (P/N 918529) · Hux billet manual tensioner (mechanical set screw, not hydraulic).

**Starting state:** block and head on, cams installed, timing gears and pulleys not installed. Water pump installed. Valve lash already set.

**Sources:** **FSM / OEM** = Toyota ST185 repair manual, Rev A. **HKS** = HKS install guide and cam card. **Both are shown where they apply.** Items marked *per Hux* follow Hux's own instructions.

---

## 0. Rules for an engine on a stand

- No belt means no link between crank and cams. Valves can hit pistons.
- Turn the **crank clockwise only**.
- Never turn a cam alone unless the No.1 piston is at TDC.
- Cold engine for belt install and tension (FSM).

```
1 Stand prep → 2 Crank + TDC → 3 Pulleys → 4 Cam gears → 5 Belt + Hux
     → 6 Degree cams → 7 Clay check → 8 Damper → first start
```

---

## 1. Stand prep

1. Crank turns freely by hand, clockwise.
2. Cam caps torqued. HKS: 19 N·m / 14 ft-lb.
3. Water pump on the block (pulley step only).
4. Remove all four spark plugs. Rag the holes.
5. Crank key in its groove.

---

## 2. Crank sprocket and true TDC

The crank sprocket is the **BEAMS 13521-88560**. It carries the COP trigger. Check its orientation and marks against the part before pressing it on.

1. Fit the degree wheel to the snout with spacer washers **before** the sprocket goes on. Fix a stiff pointer to a block bolt.
2. Slide the crank sprocket on, flange side **inward** (FSM 3.2).
3. Bring No.1 near TDC. Rotate about 15° backward. Install the **14 mm screw-in stop**.
4. Rotate clockwise into the stop. Record the wheel. Rotate back to the other contact. Record.
5. TDC = halfway between the two readings. Set the wheel to 0. Repeat from another start. Two runs must agree.

> Trust the wheel, not the cast mark. A 3–5° gap is normal.

```
   stop ──┐
          ▼
  [head]──[piston]     Read A  ←── halfway ──→  Read B
                         │
                       TDC = 0°
```

---

## 3. Pulleys and idlers

| Part | Action | Torque |
|---|---|---|
| Oil pump pulley | Align cutouts. Nut with SST 09616-30011 | FSM 35 N·m / 26 ft-lb |
| No.2 idler | Install. Check it spins freely | FSM 43 N·m / 32 ft-lb |
| No.1 idler | Loctite 242 on first 2–3 threads. Snug only | Torque after belt is on (FSM 52 N·m / 38 ft-lb) |
| Water pump pulley | Install | Torque per the part's spec |
| Hux tensioner | Mount on head. Leave loose | *per Hux* |

---

## 4. Cam gears on the marks

No old belt marks exist. Cam position comes from the cam groove and the cap marks.

1. Set each ATS hub to its **zero mark** before it goes on.
2. Confirm the crank is at No.1 TDC compression and the piston stop is removed.
3. Turn each cam with a wrench on its hex. Align the **cam groove** with the **drilled mark** on the No.1 cap (FSM 3.7).
4. Slide each ATS gear on, **"S" mark up**. Line up the pin holes. Insert the knock pin.
5. Hold the cam hex. Torque the gear bolt to the value for your tool setup:

| Tool setup | OEM (ST185 manual) | HKS (cam install sheet) |
|---|---|---|
| No SST | 59 N·m / 43 ft-lb | ~109 N·m / ~80 ft-lb (community) |
| With SST 09249-63010 | 41 N·m / 30 ft-lb | 69 N·m / 51 ft-lb |

> ⚠️ The two sources differ a lot. Confirm the value for your tool setup before torquing.

---

## 5. Belt and Hux tension

**Belt:** 178-tooth Gen 2 3S-GTE (HKS 24999-AT007 or OE 13568-79105 family). Never an FE 163T belt.

1. Install the No.1 cover and guide first.
2. Route the belt: crank → oil pump → No.2 idler → water pump → No.1 idler. Keep the crank → intake run tight.
3. Put the belt on the cam gears. Line up the matchmarks. Drive the slack to the tensioner side.
4. Turn the crank 2 full turns clockwise. Re-check the cam marks and crank groove.

**Hux tension (mechanical set screw):**

1. Loosen the jam nut. Back the set screw off.
2. Snug the tensioner bolts. Turn the set screw in until the crank → intake run is tight. Lock the jam nut.
3. Push at midspan on the slack run. Check the flex with a belt tension gauge or a ruler.
4. Tighten the two tensioner bolts *per Hux* while holding the tensioner in place.
5. Set to the Hux flex or gauge method. Cold engine only.

```
  [Hux set screw + jam nut]
  ───────────●──────────  belt run
             ↑ push at midspan, read flex
```

---

## 6. Degree the cams (dial indicator)

**Set up:** dial indicator on the No.1 bucket, rod as vertical as you can get it. Zero at **peak lift**. Approach each point from the same side.

**Find the 1 mm points:** read the wheel at 1 mm before and 1 mm after peak. **Centerline = average of the two.** Both methods should agree within ~1°.

| HKS card target | Intake (RT063) | Exhaust (RT064) |
|---|---|---|
| Centerline | **110° ATDC** | **103° BTDC** |
| Open at 1 mm | 4° BTDC | 36° BBDC |
| Close at 1 mm | 43° ABDC | 10° ATDC |
| Duration at 1 mm | 227° | 226° |

**ATS gear math:** ±10 cam° = ±20 crank°. **1 cam° = 2 crank°.** A 6° wheel error is a 3° gear move.

1. Loosen the five ATS set screws. Rotate the hub. Re-torque. Re-measure. Repeat to within ~1°.
2. For a big move, release belt tension and move one tooth. Don't use the full range.
3. Re-check valve lash after degreeing (timing changes lash).

**Dyno bias (later, not base):** ATS suggests 0 intake, about 6° retard exhaust. Other builders run 4° advance intake, 8° retard exhaust. Sweep in 2° steps on the dyno.

---

## 7. Clay check (mandatory)

> 🛑 Do not use the starter until this passes.

- **Clay:** lay clay on the No.1 piston pockets. Bar the engine two turns by hand. Measure the thinnest spot.
- **Dial:** push each valve with light springs in 5° steps through overlap. Record the minimum.

**Valve lash:** set (intake 0.20 mm, exhaust 0.25 mm, cold). Re-check after degreeing.

---

## 8. ATI Super Damper (P/N 918529)

1. Deburr and light anti-seize the crank snout. The hub is a **press fit**. If it slides on by hand, stop and check the part.
2. Align the **dimple on the hub** with the **arrow decal** on the shell.
3. Shell screws: Torx T40 Plus, Loctite 242, ~16 ft-lb.
4. Crank bolt: **OEM only**. Never a long bolt. FSM 108 N·m / 80 ft-lb (HKS 107 N·m / 79 ft-lb).

---

## Torque card: FSM vs HKS

| Fastener | OEM (ST185 manual) | HKS guide |
|---|---|---|
| Crank pulley / damper bolt | 108 N·m / 80 ft-lb | 107 N·m / 79 ft-lb |
| Cam gear, no SST | OEM: 59 N·m / 43 ft-lb | HKS: ~109 N·m / ~80 ft-lb |
| Cam gear, with SST 09249-63010 | OEM: 41 N·m / 30 ft-lb | HKS: 69 N·m / 51 ft-lb |
| No.1 idler pivot | 52 N·m / 38 ft-lb | 52 or 42 N·m (conflict) |
| No.2 idler × oil pump | 43 N·m / 32 ft-lb | ~18 N·m (community) |
| Oil pump pulley nut (SST 09616-30011) | 35 N·m / 26 ft-lb | ~8 N·m (community) |
| Cam bearing caps | — | 19 N·m / 14 ft-lb |
| Hux tensioner bolts | per Hux | per Hux |
| Cam / valve cover | — | 6 N·m / 53 in-lb |

---

## Log sheet

| Measure | Target | Reading |
|---|---|---|
| True TDC (avg of 2 runs) | 0° | |
| Intake centerline (A / B) | 110° ATDC | |
| Exhaust centerline (A / B) | 103° BTDC | |
| ATS intake / exhaust gear position | from zero | |
| Belt flex / tension (Hux) | per Hux setup | |
| Min valve-to-piston (clay / dial) | > 0 mm | |

---

## First start on the stand

1. Prime oil by cranking with fuel and ignition off.
2. Start, idle, shut down.
3. Re-check the ATS set screws and the Hux jam nut after the first heat cycle.
