# ST185 Power and Comms Architecture

**Vehicle:** 1991 Celica GT-Four ST185 (AllTrac), full race buildout. OEM display removed.

**Status:** Sealed from Daniel 2026-09-18 (Grim Council). Feature-branch parchment - not yet merged to main.

## Power

- **Trunk battery** with **main battery kill** and **fusible link** at the battery.
- **RADLOKs** carry battery positive and negative into the engine bay for **starter** and **alternator**.
- **Jump-start lugs** near the firewall.
- **Fuse and relay box** in the passenger-side glove-box area.
- **PDU** next to the fuse box in the cabin.

## CAN 1 (only CAN in use)

Devices on **CAN 1** (CAN 2 unused):

- Custom **3-cluster** dashboard
- Auxiliary **RealDash** (Pi + 7 inch screen)
- Link **CAN-Lambda**
- **ECUMaster CSB** (overflow inputs that do not fit on the ECU)
- **PDU / PDM**

The ECU **CAN 1 comms cable** also carries **12V** and **GND out** to power the new displays and the ECUMaster CSB.

## Reverse camera / gear display

1. OEM **reverse switch** into the ECU.
2. ECU sets **Gear = 7** on CAN.
3. Cluster shows **R**.
4. RealDash switches to the **USB reverse camera** view.

## Related living SoT

- ECU IO / colours: XTREMEX-IO-TABLE.html
- Wiring audit: docs/WIRING-AUDIT-2026-09-18.md
- Residual cluster LED face (diagram SoT): docs/harness/RESIDUAL-LED-FACE.md
- VSS car-side (Path B): gearbox 3-wire 12V Toyota VSS on generic oval 3-pin sockets (PN TBD); Quill faces IGN / GND / SP1 with SP1 to B29 - cavity order still open.

## Still TBD

- Fuel V→% cal on-car (pull-up locked: r_fuellvl = 470 Ω)
- VSS oval cavity order (IGN / GND / SP1 assignment)
- Main merge until Daniel verifies feature branch pass-a-bh-c-delete-locks

## Daniel seals (2026-09-18)

**SoT:** Claude 5sgte/cowork + living-relation/`st185-link-ecu-config` primary; rd-st185 Cursor secondary.

### Power / loom-C
- Loom C purpose: OEM loom-C mods + **12V/GND injection** for trunk battery and fuse relocate.
- Keep **kick-panel junctions** and most of the inner OEM harness.
- Many loom-C diagrams remain **intentional** documentation even where ACTIVE `bh_c_*` bulkhead shells were removed in Pass A.

### Cluster 12V warning LEDs
Face / diagram SoT: [`docs/harness/RESIDUAL-LED-FACE.md`](harness/RESIDUAL-LED-FACE.md).
After OEM gauge remove, prefer **OEM cluster circuit taps** (do not rework dash loom beyond cluster removal):
- low fuel, low oil pressure, alt/charge, park brake, high beam, L/R turn

**Low fuel LED:** drive from float **An Volt** + smoothing (~40–60 s). **Do not** use in-tank thermistor.

### Reverse (unchanged SoT)
OEM reverse → ECUMaster **CSB** → CAN → ECU Trigger **Gear=7** on `0x3EB`. RealDash USB camera page **DEFERRED** 2026-09-04.

No main merge until verified.

## Low-fuel LED (algorithm) — **SCRAPPED**
Thermistor dropped. Gauge: short filter **4–8 s**. Lamp: separate ~45 s confirm + hysteresis (15–20 s off). Do not use one filter for both. See WIRING-AUDIT.

## RealDash reverse camera
Path sealed via CSB / Gear=7. Camera page + triggers **not built** (deferred 2026-09-04). Cam page still unbuilt — flash **`.rd` + XML together**. Trigger = Link **Gear on 0x3EB** only — **not** Reverse Lights; do not display gear.
- Pi/Linux USB Video Gauge **unverified** (Android-only proven). Gate Pi reflash on in-gauge cam smoke test; Jump-to-Page can ship separately.

## Cluster fuel taps (EWD p.145–146)
- F18 **3–4** float (Y–R/BR); **2–1** thermistor (Y–L/W–B) — cavity locked, path dropped.
- Meter: fuel gauge **C11(B) pin 3**; low-fuel lamp **C10(A) pin 10**; gauge power **C11(B) pin 7** (15A GAUGE).
- Low-fuel LED still from float An Volt + smoothing, not thermistor.

## Daniel correction (2026-09-18 afternoon)
- **SCRAP** low-fuel LED / thermistor / cluster lamp plans. Float An Volt + divider = **fuel level only**.
- RealDash reverse: **Gear on `0x3EB`** only — **not** Reverse Lights; no gear display; return-to-main ~10s after out-of-R (or 10 mph later). No new ECU I/O.
- LEDs: hi beam, batt charge, L+R turn, park brake, low oil P. Body electronics for hi beam/turn/park (residual dash harness). Batt+oil via CAN or CSB 12V (verify active-low).
- Ignore OEM meter pin faces.
### RealDash return + CSB (detail)
- Dummy Timer: out of R (Gear≠7) for 10s → Jump to main.
- Oil: `0x3F1` bit4; CSB `0x643` low-side. Batt/charge LED: OEM alt **L** (C12(C)8 Y) + IG (C12(C)9 B-O) — no CSB bit; was TBD → spare `0x643` bit.
- Oil kPa on cluster CAN `0x3E9`; Low Oil Press 2 = `0x3F1` bit4. CSB LS4+ spare after fan/AC for batt-charge candidate.
### Residual dash-harness taps (OEM meter gone)
- Splice **stubs** C11(B)12 hi beam R–L; C11(B)2/11 turn G–B/G–Y; C12(C)1 park R–G (P1 ground-side).
- Not meter PCB. Oil/batt = CSB/CAN. No STEP ST185+3S-GTE.

## Fuel pull-up (living SoT)
- **`r_fuellvl` = 470 Ω** to +5V for An Volt 9 / B24 (SENSOR-AND-ACTUATOR-REFERENCE, NEED-TO-BUY, harness).
- Year lock: **1991** ST185 AllTrac.
- No ask-lists in repo.

## Charge LED (Daniel 2026-09-18)
- **Diagram SoT:** [`docs/harness/RESIDUAL-LED-FACE.md`](harness/RESIDUAL-LED-FACE.md)
- Residual dash: **C12(C)9 B–O** = IG, **C12(C)8 Y** = alt **L** (EWD ~p.144).
- No CSB / CAN invent for charge. Oil LED still Link→CSB.
