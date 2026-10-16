# ST185 custom enclosures - plan and research notes

Claude Code, 2026-10-13. Research only so far. **No Fusion document has been opened or created** (Dan's hold, until Dispatch says the bus bar CAD session is done). The repo was read, not edited.

Downloaded sources are in this session's scratchpad (`...\scratchpad\dl\`), not in the repo.

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

### CSB3 connector: TE Deutsch HD34-24-33PE (DECISIONS / plan 6.40, csb3-bom.csv)
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

### Hammond comparison (current BOM box)
- 1590WYFL: 92 x 92 x 42 mm body (lid included), flange 122.2 mm, inside 85.17 x 85.17 x 36.30, 4 x Ø4.0 flange holes (hammond-1590WYFL.pdf in the repo).
- 1590WUFL: 119.5 x 119.5 x 59 mm, about 150 mm over the flange (RS 228-7226 listing; Rapid 30-6050 for the WUF). Hammond's own page returned 403, so get the drawing before quoting it as final.

### O-ring and groove: Parker O-Ring Handbook ORD 5700 (50th Anniversary Edition)
- **Design Chart 4-3, face seal glands** (p. 4-18), for 1/16 in cross-section W = 1.78 ±0.08 mm (AS568 -004 to -050):
  gland depth **L 1.27-1.37 mm** (.050-.054), groove width **G 2.57-2.72 mm** for liquids (.101-.107), groove radius **R 0.13-0.38 mm**, squeeze 19-32 %. Finish 32 rms on the groove bottom and sides for liquids; break the corners about 0.13 mm.
- External (inward) pressure, e.g. water outside the box: the groove **inside** edge is primary (Hi = O-ring mean ID, +1 %, max +0.060 in).
- **Section 4.3:** for rectangular face grooves, the inside corner radii are **≥ 3 x W (ideally 6 x W)**, so ≥ 5.3 mm, ideally 10.7 mm on a 1.78 mm ring.
- Sizes from **Table 9-1**, AS568 -030 to -040 (ID mm): -030 41.00, -031 44.17, -032 47.35, -033 50.52, -034 53.70, -035 56.87, -036 60.05, -037 63.22, -038 66.40, -039 69.57, -040 72.75 (all W 1.78, tolerance ±0.33 to ±0.51).
- Material: EPDM or NBR 70 Shore A. Pick EPDM for water and road splash, NBR if oil is likely. PN format from Table 9-1 note (a): compound + size, e.g. `N0674-70 2-039` (NBR 70). The EPDM compound code is not picked yet. **Confirm the compound with Dan, then look up the code in Parker's catalogue.**

### Lid screws: ISO 10642 M3, 90° countersunk socket head, A2 stainless
- Head dk 6.72 max (5.54 min), k 1.86, 2 mm hex (Engineers Edge ISO 10642 table; Accu SSK-M3-x-A2 listings).
- Countersink: 90°, Ø6.9 at the surface, so the head sits 0-0.1 mm below flush. Clearance hole Ø3.4.
- Tapped holes in the body: M3 x 0.5, tap drill 2.5 x 9.5 + 118 deg point, 8 mm thread; the M3 x 12 engages 6.0 (2 x D in 6061). (F08, 2026-10-16; Fusion exports the threaded hole at the 6H minor diameter, 2.529.)

### Standoffs and screws already in the BOMs
- Keystone 25510: nylon hex standoff, M3 F-F, **10 mm** long, 5 mm hex (Future Electronics / IBS listings). Würth 97790603111: M3 x 6 nylon pan screw.

---

## 2. Conflicts found in the repo (report only, not fixed)

1. **Plan 6.40 says "mounting holes on a 43.08 mm circle".** TE 114-151014 shows 43.08 mm is the **D-hole diameter**. The HD34 has no screw flange; it is held by the panel nut and lockwasher, as the BOM already lists.
2. **The VRC module has no mounting holes**, but vr-conditioner-bom.csv has 4 x standoffs and 4 x screws per box. A carrier board is needed (section 1).
3. **vr-conditioner-bom.csv `ring_scr` row** runs a 22 AWG screen wire from the IN screens to an M6 ring "on bare case metal". DECISIONS R31 / R33 and SHIELD-RULES say nothing bonds to the case. Same family as OPEN-ITEMS row 75.
4. **Box part:** the BOM says 1590WYFL, while DECISIONS rows 20/23/32 say 1590WUFL (OPEN-ITEMS row 64). A custom box would replace both.
5. **SHIELD-RULES says the VRC box mounts on nylon hardware.** The tab slots below were sized for nylon M5 screws (now M6, S26 E5; slots are 6.6 wide) or shoulder washers, so the box stays isolated.

---

## 3. Proposed design (pre-CAD; SUPERSEDED by the built design in ST185-enclosures.html: VRC 90 x 50 x 45, 7 mm walls; CSB3 70 x 70 x 56)

All boxes: 6061-T6 billet body plus a flat lid. Sealing is metal to metal with the O-ring in a **body-rim** face groove. Lid screws are M3 ISO 10642 into tapped holes **outside** the O-ring, in the corners where the large groove radius leaves room. All vertical internal corners are R ≥ 3 mm for the cutter (tab-to-body corners R3, F11), except the CSB3 tab corners at x ±30: R1.9 (only a 2.0 ledge to the body corner) - cutter r ≤ 1.5 there. Floor-to-wall corners stay sharp: cutter corner OK. Break sharp edges 0.2-0.5 except O-ring / seal faces (F10).

### VRC box (front and rear identical, engrave "IN" / "OUT" on the end faces; suggestion for OPEN-ITEMS row 71)
Internal length stack along the connector axis:
connector back 12.6 + wire bend 8 + carrier 34 + wire bend 8 + connector back 12.6 ≈ **76 mm**.
- Internal **76 x 36 x 32 mm**. Width and height cover the Ø30 nut zone and the 27.8 mm face height.
- Walls 6 mm, floor 5 mm. The **end walls are counterbored Ø30 from the inside down to 3.5 mm** at each connector, which is within the 4.5 mm max and leaves thread for the rear nut. D-cutout Ø18.5 / flat 16.5, flat up.
- Body outside about **88 x 48 x 37 mm**, plus a 6 mm lid, about **88 x 48 x 43 mm** closed.
- Mounting: two tabs on the long sides at floor level, 12 mm out, 6 mm thick, slot 6.6 x 10 mm (M6 nylon, S26 E5). Footprint about **88 x 72 mm**.
- Board held by the printed holder v2 (R126): one PA12 block on 2 floor bosses D11, top z 12.5 (F02 + N4, R131), drilled 5.0 x 11.5 and tapped M6 at the fit, 2 x M6 x 14 ISO 10642 countersunk (9.0 thread, 1.5 x D); holder board top z 17.5. CSB3 lid: a D62 x 6 loft round the HD34 (R132).
- O-ring: groove centreline about 82 x 42 mm, corner R 10.7 (6W), length ≈ 229.6 mm. **AS568-039** (mean circumference 224.1 mm) gives about 2.4 % stretch, which holds it in the groove for inward pressure. Final groove numbers come from the CAD so the stretch lands at 1-3 %.
- Six to eight M3 lid screws (4 corners, plus mid-sides if the span is over 60 mm).
- Compared with the 1590WYFL (92 x 92 x 42, 122 mm over the flange), this is about 45 % of the footprint.

### CSB3 box
- Connector on the **lid**: D-hole Ø43.08 / flat 41.45. The lid is 6 mm, locally faced to 4.0 mm (within 1.59-4.76). A Ø50.8 sealing face at 0.8 µm Ra on the flange side, and Ø52 nut and lockwasher clearance on the other side.
- Lid face at least about 70 x 70 mm (Ø50.8 flange + groove + corner screws).
- CSB3 on 2 x Keystone 25510 at its two Ø3.5 holes (27 x 27 mm diagonal) on floor bosses, with 26 wires from the receptacle contacts to the pads.
- **Internal height is TBD** until the HD34 STEP shows the depth behind the panel. Working guess from plan 6.40 is about 40 mm internal; this is not a datasheet value.
- O-ring is sized the same way as the VRC box once the rim is fixed (likely around AS568-036 to -038).
- Tabs and slots as on the VRC box.

### Deliverables still to do (blocked on Fusion)
Two blockers: (1) wait for Dispatch to say the bus bar session is done; (2) this Claude Code session has **no Fusion 360 MCP tool** (checked 2026-10-13 09:52). It must be connected here, or the job run in a session that has it.

Fusion documents (new, my own): `ST185-VRC-Enclosure`, `ST185-CSB3-Enclosure`. Then STEP per part plus assembly, .f3d, drawing PDF per box, renders, and `ST185-enclosures.html`, into `vrc\` and `csb3\` here.

---

## 4. Questions for Dan (all answered in DECISIONS S26: E1 printed holder, E2 Dual VR Conditioner, E4 NBR, E5 M6)
1. VRC mounting: OK with a carrier board and DIP-8 socket (the module has no holes)? Or would you rather solder wires straight to the module pins and clamp the module in a nylon or POM cradle?
2. Which VRC rev do you have (B2 or B3; the board is 24.1 x 22.6 or 24.1 x 24.1 mm)?
3. OK to download TE's HD34-24-33PE STEP through the browser (needed for the CSB3 box depth)?
4. O-ring compound: EPDM or NBR?
5. Tab hardware size: M5 OK?

## 5. OPEN-ITEMS rows (preliminary; final report after the CAD)
- **56** (do both VRC boxes fit mid-dash): gives real box sizes (about 88 x 72 footprint each). Still needs Dan's test-fit.
- **64** (box size 1590WUFL vs 1590WYFL): answered if Dan adopts the custom box. The BOM update stays with the repo owner.
- **71** (telling IN and OUT apart): suggestion only, engraved IN / OUT on the end faces. Dan still decides.
- **73** (two cables through one plug seal): **not resolved** by the enclosure.
- **75** (docs that rely on a shell for the screen): the custom box design follows R31 (isolated PCB, nylon mount, no bond). The doc rewrite, including the `ring_scr` row conflict, stays open in the repo.
