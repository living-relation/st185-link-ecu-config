# ST185 custom enclosures - source facts

Datasheet and handbook facts the built VRC and CSB3 enclosure designs rest on (the design itself: `ST185-enclosures.html`; decisions: DECISIONS S26, S32, R126-R139).

---

## 1. Facts found (with sources)

### VRC board: OpenLogicEFI Dual VR Conditioner (NCV1124)
Source: OpenLogicEFI KiCad files, `github.com/OpenLogicEFI/Hardware` → `Modules/VR Conditioner NCV1124/RevB3/Duel VR.kicad_pcb` (latest rev, commit 2026-06-21; RevB2 checked too). Shop page `openlogicefi.com/shop/p/duel-vr-conditioner-detonationems` gives no dimensions.

| Item | RevB3 | RevB2 |
|---|---|---|
| PCB outline (Edge.Cuts) | **24.13 x 24.10 mm**, corner R ~0.71 | 24.10 x 22.56 mm |
| PCB thickness | 1.6 mm (board setup) | 1.6 mm |
| Mounting holes | **none** | none |
| Connection | 8-pin DIP header `DIP-8_W7.62mm_Socket_VRConditioner`: 2 x 4 pins, 2.54 mm pitch, 7.62 mm row spacing, 0.8 mm drill | same |
| Pinout (from nets) | 1 VR1-, 2 VR1+, 3 VR2+, 4 VR2-, 5 VDD, 6 GND, 7 VR2OUT, 8 VR1OUT | same |
| Parts | SMD only on top (SO-8 NCV1124, 0603/1206/1210 passives, 2 solder jumpers) | |

**Which rev Dan has is unknown** (order #11139, `docs/devices/VR-WHEEL-SPEED-CONDITIONER.md`). Measure it, or read the rev on the silkscreen.

**SUPERSEDED (DECISIONS S26, 2026-10-14): 3D-printed holder on the box floor, no carrier board; board = OpenLogicEFI Dual VR Conditioner (DetonationEMS). The rest of this section and sections 3-4 are the old reasoning, kept as history.**

**Consequence:** the board is a plug-in module with no holes, so "standoffs matching the board's holes" is not possible as written. Proposed fix (Dan to approve):
- a small carrier board (FR4 perfboard or a custom PCB) with a DIP-8 socket for the module and 4 x M3 holes on Keystone 25510 nylon standoffs, wires from the LP-16 cups to the carrier. The module stays removable and the carrier floats on nylon (R31: the PCB is isolated from the case).
- The carrier size is a design choice, not a datasheet value. Proposed: 34 x 30 mm, holes 3.2 mm on a 28 x 24 mm grid.

### CSB3: ECUMaster CAN Switch Board V3
Source: `switchboardManual.pdf` v2.1 (03 Dec 2024), pages 3-4 (ecumaster.com/files/devices/switchboard/switchboardManual.pdf).
- PCB **33 x 33 mm**, corner R3. Stack height **4.21 mm** total, PCB 1.61 mm.
- **2 mounting holes Ø3.5**, at opposite corners (top-right and bottom-left), centres **27 x 27 mm** apart (so M3 fits).
- Solder pads Ø1.2 on all four edges (S/A/L rows top and bottom, S7/S8/CAN on the left, GND/+12V/+5V/SGND on the right).
- ECUMaster's product page markets it as "25x25 mm". The manual drawing (33 x 33) is what the CAD uses.

### CSB3 connector: TE Deutsch HD34-24-33PE (csb3-bom.csv)
Sources: TE application spec **114-151014 Rev A** (HD30/HDP20), section 3.3 H "Mounting Hardware", 3.3 I "Receptacle Mounting", 3.11 "Panel Installation"; TE/Deutsch HD30 & HDP20 catalogue (Dalroad copy) "HD30 & HDP20 Series Dimensions".
- **HD34 is a jam-nut (panel-nut) receptacle**, not a screw-flange one. Panel nut `112263-90` (A 47.63 mm, B 4.52 mm), lockwasher `112264` (Ø47.93, 1.57 thick), both already in csb3-bom.csv.
- Shell 24 panel cutout: **D-hole ØA 43.08 ±0.13, flat B 41.45 +0.25/-0.00**, sealing-surface **ØC 50.80 ±0.13**, finish 32 rms (0.8 µm), flatness 0.13.
- **Panel thickness 1.59-4.76 mm** (.0625-.1875 in, same figure).
- Panel nut torque, shell 24: 65-75 in-lb (7.4-8.4 N·m), 1-7/8 in socket (114-151014 3.11 table; how the rows line up needs checking against the PDF page).
- Receptacle overall length **41.86 mm**, overall Ø **50.80 mm** (catalogue, "for reference only").
- **Resolved 2026-10-13 from TE's CVM model `c-hd34-24-33pe-a-3d.stp`** (read in the browser with Dan's OK). Axial faces, mating face = 0: mating shell Ø40.11 (0 to -13.34); thread root Ø41.10 (-13.9 to -24.3); pilot Ø42.86 (-24.38 to -26.16); **flange Ø50.80 x 2.54** (-26.16 to -28.70); rear body Ø37.34 to -41.83. So the flange sits **inside** against the panel, the mating side goes out through the D-hole, and the nut and washer go outside. Depth behind the flange face is **15.7 mm**.

### VRC connector: CNLINKO LP-16-C05SX-02-101 (S16)
Source: CNLINKO drawing **LP-16-xxxSX-02-1xxx, Rev A1, 2024-03-14**, sheets 1-2 (the BOM's cnlinko-en.oss link).
- Part-number rules on sheet 1: C = male, 05 = 5 pin, SX = receptacle, 0 = solder, 2 = all plastic, 1 = single-hole straight receptacle. So `C05SX-02-101` is a valid code: male 5-pin, plastic, rear nut.
- Cutout: **D-hole Ø18.5 +0.2/-0, flat 16.5 +0.2/-0**. Thread **M18 x 1.5**. **Max panel 4.5 mm.** Tightening torque **1.0 N·m**.
- Front face Ø25.5 ±1; height with the cap hinge 27.8 ±1. Cap on its tether hangs to 71.0 ±3 overall.
- Lengths: overall "A" = **26.2 ±0.5** (male 5-pin, sheet 2). Front to thread end 22.3 ±0.3. Flange back face to thread end 8.7 ±0.5.
  - Derived (my reading of the view, check it): in front of the panel ≈ 22.3 - 8.7 = **13.6 mm**; behind the panel ≈ 26.2 - 13.6 = **12.6 mm** including the solder cups. The repo's "≤27.0 mm behind the panel" is the whole part length, which is a safe upper bound.
- 5 A / 250 V AC, 22-20 AWG solder cups, IP68 mated.
- **Rear nut OD/thickness is not on the drawing.** Inside clearance is sized at Ø30 to be safe. Measure a sample.

### O-ring and groove: Parker O-Ring Handbook ORD 5700 (50th Anniversary Edition)
- **Design Chart 4-3, face seal glands** (p. 4-18), for 1/16 in cross-section W = 1.78 ±0.08 mm (AS568 -004 to -050):
  gland depth **L 1.27-1.37 mm** (.050-.054), groove width **G 2.57-2.72 mm** for liquids (.101-.107), groove radius **R 0.13-0.38 mm**, squeeze 19-32 %. Finish 32 rms on the groove bottom and sides for liquids; break the corners about 0.13 mm.
- External (inward) pressure, e.g. water outside the box: the groove **inside** edge is primary (Hi = O-ring mean ID, +1 %, max +0.060 in).
- **Section 4.3:** for rectangular face grooves, the inside corner radii are **≥ 3 x W (ideally 6 x W)**, so ≥ 5.3 mm, ideally 10.7 mm on a 1.78 mm ring.
- Sizes from **Table 9-1**, AS568 -030 to -040 (ID mm): -030 41.00, -031 44.17, -032 47.35, -033 50.52, -034 53.70, -035 56.87, -036 60.05, -037 63.22, -038 66.40, -039 69.57, -040 72.75 (all W 1.78, tolerance ±0.33 to ±0.51).
- Material: the boxes are in the cabin, so compound does not matter (Dan 2026-10-26). Keep the repo spec: Parker `N0674-70 2-039` (NBR 70, AS568-039). PN format from Table 9-1 note (a): compound + size.

### Lid screws: ISO 10642 M3, 90° countersunk socket head, A2 stainless
- Head dk 6.72 max (5.54 min), k 1.86, 2 mm hex (Engineers Edge ISO 10642 table; Accu SSK-M3-x-A2 listings).
- Countersink: 90°, Ø6.9 at the surface, so the head sits 0-0.1 mm below flush. Clearance hole Ø3.4.
- Tapped holes in the body: M3 x 0.5, tap drill 2.5 x 9.5 + 118 deg point, 8 mm thread; the M3 x 12 engages 6.0 (2 x D in 6061). (F08, 2026-10-16; Fusion exports the threaded hole at the 6H minor diameter, 2.529.)
