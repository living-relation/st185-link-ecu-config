# ECU I/O and Wiring Documentation — Cleanup and Consolidation Plan

**Vehicle:** 1993 Toyota Celica GT-Four ST185 · 5S-GTE · Link G4X XtremeX · ESP32 cluster set on CAN
**Prepared:** 2026-08-31
**Status:** PLAN ONLY. Nothing has been edited, moved, deleted, or consolidated. Approve before any change.

---

## 0. Terms defined on first use

- **I/O** — input/output. The ECU's physical pins and the channels Link assigns to them.
- **DBW** — drive by wire. An electric throttle body controlled by the ECU instead of a cable.
- **ETB** — electronic throttle body. The Bosch unit.
- **APS / APP** — accelerator pedal position sensor. The sensor inside the pedal.
- **TPS** — throttle position sensor. The sensor on the throttle body.
- **EPS / EHPS** — electric (hydraulic) power steering. The MR2 pump.
- **VSS / SPD** — vehicle speed signal. A pulse train whose frequency tracks road speed.
- **PCLink** — Link's tuning software for the G4X.
- **LCS file** — a PCLink CAN setup file. `link_g4x_can_setup.lcs`.
- **Frame** — one CAN message with an ID and up to 8 bytes.
- **BE / big-endian** — most significant byte first inside a multi-byte CAN field.
- **Low-side output** — an output that switches the ground side of a load and floats when off.
- **H-bridge** — a four-transistor output that can drive a motor in both directions. Used for the ETB.
- **Working tree** — the files as they sit on disk, which can differ from what git has recorded.
- **Untracked** — a file git has never been told about. It is not backed up by any commit or push.

---

## 1. Executive summary

- **55 documents inventoried** across five locations: the `st185-link-ecu-config` repo, the `center-cluster-esp32-p4` repo, the Celica OneDrive folder, Google Drive, and past Claude session transcripts.
- **22 are flagged bad** — obsolete, incorrect, superseded, or unverifiable.
- **The two best documents are the two least protected.** `XTREMEX-IO-TABLE.html` exists only on a local branch that was never merged or pushed. `SCHEMATIC-WIRING.html` is untracked by git entirely. If this machine's disk fails today, both are gone.
- **The interactive wiring app has no local copy at all.** It lives only as a hosted Claude artifact. Two Google Docs hold saved states of its data, and those two saved states disagree with each other and with the repo.
- **All five new hardware items are already documented** in the two HTML files, with pins assigned. The problem is not missing design work. The problem is that five other documents still describe the old cable-throttle car and contradict it.
- **Two facts are wrong in every repo document:** the engine is recorded as 3S-GTE (it is a 5S-GTE), and much of the source material is for a Link FuryX (the ECU is an XtremeX).
- **All four prior CAN bugfixes are present and correct** in the current `link_g4x_can_setup.lcs`.
- **27 conflicts** are listed in section 6, each with a recommended resolution. Four of them (C24–C27) are throttle-body specific and were found by checking the FuryX pin map line by line against the confirmed Bosch part. One of those, C26, would swap a pedal signal for a throttle signal if the wrong document were followed.
- **The throttle body is now positively identified** from photographs of the part: Bosch 0 280 750 474, Porsche 997 605 115 03, VAG 022 133 062 AJ, 74.5 mm bore. Full electrical specification, connector part numbers and the G4X calibration procedure are in section 5.3.
- **Air conditioning: both control paths are specified in full** at Dan's direction. Neither is ruled out; the choice happens after testing.

---

## 2. Inventory

Status key: **CURRENT** · **SUPERSEDED** (replaced by something newer, keep for history) · **OBSOLETE** (describes a car that no longer exists) · **INCORRECT** (states something factually wrong) · **UNVERIFIED** (could not be opened or checked this pass).

### 2.1 Repo — `C:\projects\st185-link-ecu-config`

Branch `ECU-wiring-design`, 2 commits ahead of `main`, 3 untracked paths.

| # | Path | Format | Modified | Covers | Status | Reason |
|---|---|---|---|---|---|---|
| 1 | `XTREMEX-IO-TABLE.html` | HTML | 2026-07-13 | Full XtremeX channel plan: DBW, EPS, A/C, CAN-Lambda, switchboard, pin budget | **CURRENT** | The only complete and internally consistent I/O document. Exists only on branch `ECU-wiring-design`; never merged to `main`. |
| 2 | `SCHEMATIC-WIRING.html` | HTML/SVG | 2026-07-27 | Schematic with real ECU pin numbers (A/B 34-pin + Comms 6-pin) | **CURRENT** | Newest wiring artifact in the project. **Untracked in git** — never committed, never pushed. |
| 3 | ~~`XTREMEX-IO-TABLE.md`~~ | Markdown | — | Channel plan | **DELETED 2026-09-06** | Fully reconciled against #1 on 2026-09-05 (the An Volt map had disagreed on 10 of 11 channels, not 8), then deleted 2026-09-06 as a duplicate maintenance surface. `XTREMEX-IO-TABLE.html` is the single channel plan. The README row now points at the `.html`. Recoverable from git history. |
| 4 | `CAN-BUS-ID-ALLOCATION-TABLE.md` | Markdown | 2026-07-13 | Master CAN ID map, byte layouts sections A–E | **CURRENT** | Accurate for what it covers. Missing the CAN-Lambda transmit ID 0x3BE and any DBW/EPS/A/C telemetry. |
| 5 | `link_g4x_can_setup.lcs` | XML | 2026-07-13 | PCLink CAN transmit streams | **CURRENT** | All four prior bugfixes verified present. See section 4. |
| 6 | `link_g4x_can_setup.json` | JSON | 2026-07-13 | Canonical twin of the LCS | **UNVERIFIED** | Not opened this pass. Must be diffed against the LCS before it is trusted. |
| 7 | `link_g4x_realdash.xml` | XML | 2026-07-13 | RealDash channel description, frames 0x3EF–0x3F1 | **CURRENT** | RealDash is active work, not frozen. |
| 8 | `CANBUS-ENCODE-DECODE-REFERENCE.html` | HTML | 2026-07-13 | ECU↔cluster encode/decode contract | **CURRENT** | Byte-identical copy of the cluster repo's file (#19). One is redundant. |
| 9 | `CANBUS-LINK-G4X-CONFIG.md` | Markdown | 2026-07-13 | PCLink module settings, stream import, user streams | **CURRENT** | |
| 10 | `CAN-BUS-MASTER-DESIGN.md` | Markdown | 2026-07-13 | Bus architecture, fault tolerance, topology | **CURRENT** | Describes a 4-node bus. There are 5 nodes — CAN-Lambda is on the bus. |
| 11 | `CAN-CONFIG-STATUS.md` | Markdown | 2026-07-04 | Handoff snapshot | **SUPERSEDED** | A dated status note. Its content is now covered by #4 and #9. |
| 12 | `ECUMASTER_SWITCHBOARD_SETUP.md` | Markdown | 2026-07-13 | Switchboard configuration steps | **CURRENT** | |
| 13 | `WIRING.md` | Markdown | 2026-07-13 | CAN physical topology, cluster power, GPIO | **CURRENT** | Says 4-node bus. Overlaps heavily with #21. |
| 14 | `Other ECU IO and MATH.txt` | Text | 2026-07-13 | Living note: extra I/O, tune math ideas | **CURRENT** | Raw note. Content is already reflected in #1. |
| 15 | `AC amplifier input signals.txt` | Text | 2026-07-13 | Living note: OEM A/C amplifier inputs, ACT cancel approach | **CURRENT** | Raw note. The basis for the A/C plan in #1. |
| 16 | `README.md` | Markdown | 2026-07-13 | Repo index and file table | **SUPERSEDED** | Its file table lists neither #1 nor #2. Says 4-node bus. Says cluster firmware is frozen but does not say RealDash is not. |
| 17 | `.claude/worktrees/bridge-cse_018RH.../*` | mixed | 2026-07-18 | Full duplicate of 30+ repo files | **OBSOLETE** | Stale git worktree. Duplicates every document above at an older revision. A search-and-confuse hazard. |
| 18 | `REALDASH-LAYOUT.md`, `realdash-simulation.html`, `rd-build/**` | mixed | 2026-07-13 | RealDash dashboard design | **CURRENT** | Out of scope for this cleanup except as consumers of the CAN map. |

### 2.2 Repo — `C:\projects\center-cluster-esp32-p4` (firmware FROZEN)

| # | Path | Format | Modified | Covers | Status | Reason |
|---|---|---|---|---|---|---|
| 19 | `CANBUS-ENCODE-DECODE-REFERENCE.html` | HTML | 2026-07-04 | ECU↔cluster frame contract, derived from `main/canbus.c` | **CURRENT** | Named source of truth for frames 0x3E8–0x3EE. Frozen. Do not change. |
| 20 | `PINOUT.md` | Markdown | 2026-07-04 | Cluster GPIO | **CURRENT** | Cluster scope, not ECU. |
| 21 | `WIRING.md` | Markdown | 2026-07-04 | Cluster power, CAN transceiver, GPIO | **SUPERSEDED** | The `st185` copy (#13) is newer and broader. |
| 22 | `docs/harness/HARNESS_WIRING_DIAGRAM.html` | HTML | 2026-07-04 | Cluster harness drawing | **CURRENT** | Cluster harness, not ECU harness. |
| 23 | `docs/harness/CONNECTOR_BOM.csv` + `CONNECTOR_BOM_AND_HARNESS.md` | CSV/MD | 2026-07-04 | Cluster connector BOM | **CURRENT** | Cluster scope. |

### 2.3 OneDrive — `...\OneDrive\Desktop\Celica`

| # | Path | Format | Modified | Covers | Status | Reason |
|---|---|---|---|---|---|---|
| 24 | `Tables\FuryX A-B Connector_PinMap_v3.xlsx` | XLSX | 2026-07-04 | A/B connector map with DBW pins | **INCORRECT** | Named for the wrong ECU. Puts CAN-Lambda on CAN2 (DI 9/10). Lists Aux 9 for the ETB motor but no Aux 10 — an H-bridge needs both. Its An Volt map contradicts #1. |
| 25 | `Tables\FuryX_LoomA_LoomB_List.xlsx` | XLSX | 2026-07-04 | Loom A and B wire list | **OBSOLETE** | Every pin number is the literal placeholder `A-??` / `B-??`. Has no MAP sensor. Puts A/C on Aux 1, ignition on loom B, cam on Trigger 1, and a directly-wired LSU 4.9 heater. Contradicts every other source. |
| 26 | `Tables\TE_BOM_with_screenshots.xlsx` | XLSX | — | Connector and terminal BOM | **UNVERIFIED** | Not opened this pass. |
| 27 | `Tables\blueprint (2) (2)_OLD.xlsx` | XLSX | — | Unknown | **OBSOLETE** | Marked `_OLD` in the filename. |
| 28 | `Other ECU IO and MATH.txt`, `AC amplifier input signals.txt` | Text | — | Living notes | **SUPERSEDED** | Duplicates of #14 and #15. Two copies of a living note is one copy too many. |
| 29 | `Link G4X FuryX Trigger & Ignit 1.xml`, `FuryX Harness Connector Parts, 1.xml` | XML | 2026-01 | FuryX harness data | **OBSOLETE** | Pre-dates the switch to XtremeX (commit `d2dda23`, 2026-07-04). |
| 30 | `XtremeXQuickstartGuide.pdf` | PDF | — | Vendor pin and loom reference | **CURRENT** | The authority for pin numbers and wire colours. |
| 31 | `OEM Mini Diagrams\*.png` (9 files) | PNG | — | OEM A/C compressor, combination meter, cooling fan, idle speed, MAP, spark, CEL, circuit opening relay, OEM ECU | **CURRENT** | Needed for the A/C amplifier and EPS speed-signal work. |
| 32 | `TrackCluster CAN Sender\center_cluster_wiring_diagram_v3.png` | PNG | — | Cluster wiring | **SUPERSEDED** | `_v4_shortened.png` in the same folder is newer. |
| 33 | `Parts Invoices\*.pdf` (68 files) | PDF | — | Purchase records | **UNVERIFIED** | Image-only scans with no text layer. Could not confirm the Bosch part number from them without OCR. |

### 2.4 Google Drive

| # | File | Format | Modified | Covers | Status | Reason |
|---|---|---|---|---|---|---|
| 34 | `Link ECU Wiring App` | Google Doc | 2026-08-28 | Saved state of the interactive wiring app (JSON) | **CURRENT** | The newest saved app state. Still carries the stale note "ST185 is not drive-by-wire" on the throttle row. |
| 35 | `Link ECU wiring app` | Google Doc | 2026-08-22 | Earlier saved state + the app's artifact URL | **SUPERSEDED** | Holds the only recorded link to the app: `claude.ai/public/artifacts/fe41bba4-4b82-44aa-9d74-ab1129eae3c8`. |
| 36 | `ECU I/O List.xlsx` | XLSX | 2026-03-10 | Harness build list: wire colour, AWG, terminate-at | **SUPERSEDED** | Useful build detail that exists nowhere else, but the design has moved on. Says "side feed intake manifold". Lists A/C as "if there's IO left". |
| 37 | `st185-furyx-ecu-package.zip` | ZIP | 2026-06-09 | Unknown ECU package | **UNVERIFIED** | Named for the wrong ECU. Not opened. |
| 38 | `FuryX Engine Harness Netlist, 1.pdf` + `.xml` | PDF/XML | 2026-01-23 | FuryX netlist | **OBSOLETE** | Wrong ECU. |
| 39 | `FuryX Harness Connector Parts, 1.xml` | XML | 2026-01-23 | FuryX connectors | **OBSOLETE** | Wrong ECU. Duplicate of #29. |
| 40 | `Link G4X FuryX Trigger & Ignit 1.pdf` + `.xml` | PDF/XML | 2026-01-23 | FuryX trigger/ignition | **OBSOLETE** | Wrong ECU. Duplicate of #29. |
| 41 | `FuryXQuickstartGuide.pdf`, `FuryXQuickstartGuide_copy.pdf` | PDF | 2026-01 | FuryX vendor guide | **OBSOLETE** | Wrong ECU. Two copies. #30 replaces both. |
| 42 | `center-CANBUS-LINK-G4X-CONFIG.md`, `Copy of center-CANBUS-LINK-G4X-CONFIG.md` | MD | 2026-05 | Old PCLink config guide | **SUPERSEDED** | Both 5,033 bytes — identical copies of a May version of #9. |
| 43 | `TrackCluster ECU Dashboard.html` | HTML | 2026-05-18 | 1.3 MB dashboard mock-up | **OBSOLETE** | Predates the current RealDash work by two months. |
| 44 | `Wiring_Harness_Template`, `Blank_Wiring_Harness_Template` | Sheets | 2026-06 / 2026-08 | Empty harness templates | **UNVERIFIED** | Templates, not data. |
| 45 | `Link ECU CAN stream data.png` | PNG | 2026-02-18 | Screenshot of a CAN stream setup | **SUPERSEDED** | Predates the current CAN map by five months. |
| 46 | `3SGTE ECU Pinouts.pdf` | PDF | 2025-06 | OEM 3S-GTE ECU pinout | **CURRENT** | Valid as an OEM reference for the donor loom, but it is not this engine. |
| 47 | `Toyota - ST185 - Electrical Wiring Diagram.pdf` (×2), `90 ST185 Wiring Diagram.pdf`, `90 ST185 Wiring Diagram.png` | PDF/PNG | 2026-02 / 2026-05 | OEM chassis wiring | **CURRENT** | Four copies of the same 2,410,654-byte document. Keep one. |
| 48 | `Custom_stream_setup_LINK.pdf` | PDF | 2026-03-19 | Link custom stream how-to | **CURRENT** | Vendor reference. |
| 49 | `Daves example Bulkhead Pinouts ST185.pdf` | PDF | 2026-03-10 | Example bulkhead pinout | **CURRENT** | Reference. |
| 50 | `Motec 4 Cyl Overall Wiring.pdf` | PDF | 2026-03-03 | Motec example schematic | **CURRENT** | Reference only. Different ECU brand. |
| 51 | `Celica Inventory.xlsx` | XLSX | 2024-10 | Parts inventory | **OBSOLETE** | Out of scope, and 22 months old. |

### 2.5 Generated artifacts and session history

| # | Item | Format | Modified | Covers | Status | Reason |
|---|---|---|---|---|---|---|
| 52 | **Interactive XtremeX wiring app** — `https://claude.ai/public/artifacts/fe41bba4-4b82-44aa-9d74-ab1129eae3c8` | Hosted HTML | unknown | Interactive device/pin/bus editor | **CURRENT** | **No local copy exists anywhere.** Not in any repo, not in `C:\Users\danie\Claude\Artifacts`, not in the Cowork artifact manifest, not in any session transcript. Only the URL and two data exports survive. |
| 53 | `C:\Users\danie\Claude\Artifacts\today-status\index.html` | HTML | 2026-05-22 | Unrelated status page | **OBSOLETE** | Not a Celica artifact. The only file in that folder. |
| 54 | `C:\Users\danie\Claude\Projects` | — | — | — | **not found** | The directory does not exist on this machine. |
| 55 | ~57 session transcripts under `local-agent-mode-sessions` | JSON | 2026-05 → 2026-08 | Reasoning history | **CURRENT** | The DBW dual-APP / dual-TPS requirement is recorded in `local_f8383d8c-1065-484e-b821-7c8cb27149eb.json` (2026-08-26). The 5S-GTE displacement (2.19 L) is confirmed in the 2026-08-30 turbo sessions. |

---

## 3. Where the interactive wiring app lives

- **Newest and only live copy:** the hosted Claude artifact `https://claude.ai/public/artifacts/fe41bba4-4b82-44aa-9d74-ab1129eae3c8`. The URL is recorded in Google Doc #35 (2026-08-22).
- **Newest saved data:** Google Doc #34, "Link ECU Wiring App", 2026-08-28. 30 devices plus 5 bus nodes.
- **Older saved data:** Google Doc #35, "Link ECU wiring app", 2026-08-22. 31 devices plus 5 bus nodes.
- **No source file exists on disk.** Searched every HTML file under `C:\projects`, `C:\Users\danie\Claude`, `C:\Users\danie\Downloads`, `C:\Users\danie\Desktop`, `C:\Users\danie\Documents`, and the Celica OneDrive folder. The only wiring-related HTML files found are #1, #2, #8, #19 and #22 — none of them is the app.
- **`XTREMEX-IO-TABLE.html` and `SCHEMATIC-WIRING.html` are not the app.** They are static documents. They are, however, the documents the app should have been built from, and they are more current than either saved state.

**What the two saved states disagree on** (they are 6 days apart):

| Row | 2026-08-22 save | 2026-08-28 save |
|---|---|---|
| An Volt 2 | "TPS", status confirmed | "Bosch TB Pos1", status confirmed |
| Temp 4 | "Fuel temp", status open | row deleted |
| Aux 2 | "AC Fan", loom A White, decided | row deleted |
| Aux 7 | absent | "CEL (Cluster)", status open |
| DI 1–3, Ign 1–4, Aux 1/4 | status "decided" | status downgraded to "proposed" |
| Bus termination | cluster terminated, ECU and Pi not | ECU and Pi terminated, cluster not |

Neither save reflects the DBW pedal at all. Both still carry the note "Cable throttle — ST185 is not drive-by-wire".

---

## 4. Verification of the four prior CAN bugfixes

Checked against `C:\projects\st185-link-ecu-config\link_g4x_can_setup.lcs` (v1.1, 2026-07-13).

| Fix | Required | Found | Verdict |
|---|---|---|---|
| 0x3E8 must use MAP, not MGP | Parameter named `MAP` at StartBit 16, Length 16 | `<Parameter Name="MAP" StartBit="16" Length="16" .../>` | **PRESENT** |
| 0x3E9 oil and fuel pressure 2-byte big-endian | Oil at StartBit 24 Length 16; Fuel at StartBit 40 Length 16; ByteOrder BigEndian | Exactly that | **PRESENT** |
| 0x3F0 coolant pressure 2 bytes with everything after shifted | Coolant Pressure StartBit 16 Length 16; Ethanol 32; Charge-Pipe IAT 40; Turbo Speed 48; Trigger Errors 56 | Exactly that | **PRESENT** |
| Ghost Trigger Errors entry removed | Exactly one `Trigger Errors` parameter in 0x3F0 | One only, at StartBit 56 | **PRESENT** |

Two additional scale fixes are also present and documented in the file header: `Lambda Target` scale 0.001 (was 1000) and `Accel X/Y/Z` scale 0.1 (was 10).

**Caveat:** `link_g4x_can_setup.json` claims to be the canonical twin of this file but was not opened this pass. It must be diffed against the LCS before either is imported.

---

## 5. The five hardware additions

All five are **already designed and pinned** in `XTREMEX-IO-TABLE.html` and `SCHEMATIC-WIRING.html`. The work is not to invent the design — it is to propagate it into the other documents and fill the gaps listed below.

### 5.1 Link CAN-Lambda wideband controller

**Researched facts** ([Link CAN-Lambda manual](https://linkecu.com/documentation/canlambda.pdf), [Link CAN Setup](https://support.linkecu.com/hc/en-us/articles/1500002420301-CAN-Setup)):

- Ships preconfigured at **1 Mbit/s** — the same rate as this bus. **No bit-rate change needed.** This is the opposite of the switchboard.
- Default receive ID **950 (0x3B6)** for module ID 0.
- Additional modules use **951–957 (0x3B7–0x3BD)** for module IDs 1–7.
- The ECU transmits to all modules on **958 (0x3BE)**.
- Other supported rates: 125, 250, 500 kbit/s. ID and rate are changeable in PCLink or by an inline procedure.
- PCLink setup: ECU Controls → CAN Setup → mode `User Defined`, bit rate `1 Mbit/s`, pick a free channel, mode `Link CAN-Lambda`, CAN ID `950`, format `Normal`.
- Sensor is a Bosch LSU 4.9.

**Delta:**

| Item | Currently documented | Change needed |
|---|---|---|
| 0x3B6 receive | Yes, reserved in the allocation table | none |
| 0x3BE transmit (ECU → module) | **No — not documented anywhere** | Reserve 0x3BE. Reserve the whole block 0x3B6–0x3BE. |
| Bit rate | Not stated | State "1 Mbit/s native, no change required" so it is not mistakenly reconfigured like the switchboard |
| Bus attachment | CAN 1 (docs) vs **CAN 2 on DI 9/10** (pin map #24) | Resolve to CAN 1. See conflict C5. |
| Lambda 1 → 0x3EA | Documented and frozen | none |
| Pins consumed | Zero ECU pins on CAN 1 | none |

**No ID conflicts.** 0x3B6–0x3BE (950–958) sits entirely below the lowest project frame 0x3E8 (1000).

### 5.2 ECUMaster CAN Switch Board V3

**Researched facts** ([ECUMaster switchboard manual v2.1](https://www.ecumaster.com/files/devices/switchboard/switchboardManual.pdf), [ECUMaster product page](https://www.ecumaster.com/products/can-switch-board/)):

- 8 switch inputs (grounded when pressed), 8 analogue inputs (0–5 V), 4 low-side outputs at **0.5 A maximum** — LED level only.
- Base ID default **0x640**. Uses Base+0, Base+1, Base+2 as outputs and Base+3 as an input.
- Ships at **500 kbps**. Must be set to **1000 kbps**.
- Default transmit rate 20 Hz.

**Delta:**

| Item | Currently documented | Change needed |
|---|---|---|
| 0x640–0x643 byte layouts | Yes, allocation table section 5 | none |
| 500 → 1000 kbps | Yes, in three places | none |
| Base ID 0x640 | Yes | none |
| Data routing rule | Yes: switchboard → ECU only; ECU echoes to RealDash; cluster reads ECU only | Restate it once, in one place, and delete the three partial restatements |
| Output current limit | Only in `XTREMEX-IO-TABLE.html` | Promote to the allocation table so nobody wires a fan to it |
| Switch bit assignments 6–8 | Unassigned | Assign: bit5 = A/C request from cabin, bit6 = spare, bit7 = spare. See section 5.4. |

**No ID conflicts.** 0x640–0x643 is 1600–1603; the highest project frame is 0x3F1 (1009).

### 5.3 Bosch electronic throttle body + Subaru BRZ pedal

#### 5.3.1 Part identification — CONFIRMED

Dan identified the unit from photographs of the actual part. This supersedes the earlier inference from the I/O table and the session transcript.

| Field | Value | Source |
|---|---|---|
| Bosch part number | **0 280 750 474** | markings on the part |
| Porsche part number | **997 605 115 03** | markings on the part |
| VAG part number | **022 133 062 AJ** | markings on the part |
| Bore | **74.5 mm** — throttle plate stamped "745" | markings on the part |
| Connector | 6-pin, single integrated housing on the motor/sensor module | photographs |
| Mounting | Square four-bolt flange adapter onto the Soara dual-plenum intake manifold | photographs |

**Note on the "74 mm" figure.** Retailers list this unit as 74 mm. The plate stamp says 745, so **74.5 mm** is the number to use for the flange step calculation and for any airflow work. Both figures refer to the same part.

**Note on the Bosch Motorsport data sheet.** The [Bosch Motorsport ETB data sheet](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Data%20Sheet_68749835_Electronic_Throttle_Body.pdf) lists bores of 32, 40, 44, 46, 52, 54, 60 and 82 mm, and **does not list 74.5 mm**. The 0 280 750 474 is the Porsche/VAG production unit that the motorsport trade resells; it shares the ETB platform and the same 6-pin connector family, and vendors including [EFI Hardware](https://www.efihardware.com/products/3066/bosch-74mm-dbw-electronic-throttle-body) and [Nuke Performance](https://www.nukeperformance.com/product.html/bosch-throttle-body-74mm) sell it against the same mating connector. **The electrical characteristics below are inherited from that data sheet, not from a data sheet that names 0 280 750 474 directly.** Verify the two sensor voltages on the bench before relying on them.

#### 5.3.2 Throttle body electrical specification

From the [Bosch Motorsport data sheet](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Data%20Sheet_68749835_Electronic_Throttle_Body.pdf):

| Parameter | Value |
|---|---|
| Motor supply voltage | 6 to 16 V |
| Sensor supply voltage | 5 ± 0.2 V |
| Maximum motor current | under 10.0 A |
| **Output signal I (Pot 1)** | **0 V → 5 V across 0 to 90 degrees** — rises as the plate opens |
| **Output signal II (Pot 2)** | **5 V → 0 V across 0 to 90 degrees** — falls as the plate opens |
| Operating temperature | −40 to 140 °C |
| Default position | The plate has a sprung idle default position |

**The two tracks run in opposite directions at the same gain.** Their sum is nominally a constant 5 V. That is the redundancy check: if Pot 1 + Pot 2 drifts away from 5 V, one track has failed. This is why the G4X needs both configured with the correct orientation — swapping them or calibrating one backwards defeats the check without producing an obvious symptom.

#### 5.3.3 Six-pin connector pinout and mating parts

Pinout ([EFI Hardware](https://www.efihardware.com/products/3066/bosch-74mm-dbw-electronic-throttle-body), [Bosch Motorsport shop](https://www.bosch-motorsport-shop.com.au/electronic-throttle-body-74mm-bore)):

| Pin | Bosch label | Function | Goes to |
|---|---|---|---|
| 1 / A | Motor − | H-bridge negative | XtremeX Aux 10 (B26) |
| 2 / B | Pot − | Sensor ground | XtremeX Gnd Out (A24 or B22) |
| 3 / C | Pot + | Sensor 5 V supply | XtremeX +5V Out (A32) |
| 4 / D | Motor + | H-bridge positive | XtremeX Aux 9 (B18) |
| 5 / E | Pot 2 | TPS signal, falling 5 V → 0 V | XtremeX An Volt 3 (A33) — **TPS Sub** |
| 6 / F | Pot 1 | TPS signal, rising 0 V → 5 V | XtremeX An Volt 2 (A22) — **TPS Main** |

**Mating connector for the bill of materials:**

| Item | Part number | Notes |
|---|---|---|
| Mating connector, 6-pin AMP | **D 261 205 358-01** | Bosch Motorsport part number. Fits 0 280 750 148/149/150/151/156/101 and **474**. |
| Kit contents | Housing, 6 terminals, 6 wire seals, seal retainer | Sold as a kit by [Bosch Motorsport AU](https://www.bosch-motorsport-shop.com.au/mating-connector-6-pin-amp), [EFI Hardware](https://www.efihardware.com/products/3026/bosch-dbw-throttle-body-6-pin-connector), [Ultra Performance](https://www.ultraperformance.co.uk/bosch-motorsport-e-throttle-connector-kit), [Creative Motorsport Solutions](https://www.gomuchfaster.com/products/6-way-female-connector) |
| Wire gauge | Motor pins carry up to 10 A. Size the two motor wires accordingly; the four sensor wires can be small. | Not specified by Bosch — set it in the harness build list. |

**Buy the kit, not a loose housing.** The AMP terminals in this family are not a common crimp; a pigtail kit avoids sourcing them separately.

#### 5.3.4 Subaru BRZ pedal

6-pin connector, two redundant accelerator pedal position sensors. From the 2026-08-26 session transcript: *"Both APP1 and APP2 MUST be wired ... this is a safety requirement for DBW operation. The Link G4X will not enable the e-throttle if only one APP signal is present."*

**The BRZ pedal is a Toyota-family design, and that matters.** Link's help file states:

> *"Some Accelerator Position sensors have one signal that stops changing before full travel is reached, these sensors are most often found on Toyota and Lexus engines."*

> *"APS(Main) MUST be assigned to the signal that changes over the full working range and the other signal assigned to APS (Sub). Under no conditions should the orientation and these two signals be swapped."*

**Action:** measure both pedal tracks across full travel before assigning them. If one track stops rising at roughly 60–70 percent, that track is APS (Sub) and the PCLink setting **APS (Sub) 100%** must be set to the APS (Main) percentage at which it stops — **not** left at the default 100. Getting this wrong produces a permanent APS tracking-error fault and a 1800 rpm limit.

The BRZ pedal's factory pinout could not be found in an accessible source. It must be probed. See section 10.

#### 5.3.5 Link G4X XtremeX side — current allocation

From `XTREMEX-IO-TABLE.html` and `SCHEMATIC-WIRING.html`:

| Function | Channel | ECU pin | Connects to |
|---|---|---|---|
| ETB motor + | Aux 9 | B18 | Bosch pin 4 / D |
| ETB motor − | Aux 10 | B26 | Bosch pin 1 / A |
| ETB motor supply | V-Ethrottle | B5 | fed by the Aux 2 relay |
| ETB power relay control | Aux 2 | A20 | relay coil, low side |
| TPS Main | An Volt 2 | A22 | Bosch pin 6 / F (Pot 1, rising) |
| TPS Sub | An Volt 3 | A33 | Bosch pin 5 / E (Pot 2, falling) |
| APS Main | An Volt 4 | A14 | BRZ pedal, full-range track |
| APS Sub | An Volt 5 | B33 | BRZ pedal, second track |
| Sensor 5 V | +5V Out | A32 | Bosch pin 3 / C, and both pedal tracks |
| Sensor ground | Gnd Out | A24 / B22 | Bosch pin 2 / B, and both pedal tracks |
| EFI main relay hold | Aux 6 | A28 | keeps the ECU alive for key-off throttle reset |

**Aux 9/10 is the right choice and is not arbitrary.** Link's help file: *"Aux1/2 & Aux3/4 require an External Ethrottle Controller whereas Aux9/10 has a built in controller and can be connected directly to the EThrottle motor."* The current allocation uses the built-in H-bridge. Nothing extra is needed.

**Supply and ground arrangement.** Five sensor circuits share the +5 V rail: MAP, TPS Main, TPS Sub, APS Main, APS Sub — plus the three pressure transducers and the fuel-level divider. That is nine loads on A32. **Confirm the XtremeX +5 V rail current limit against the total.** If it is marginal, the DBW sensors take priority, because Link raises fault code 72 (*Analog 5V Supply Error — E-Throttle*) and shuts the throttle down if that rail sags. Sensor ground for the DBW sensors should come from a Gnd Out pin, not a chassis ground, so the reference tracks the ECU.

#### 5.3.6 E-throttle safety settings and calibration procedure

Source: [Link G4X help — E-Throttle First Time Setup](http://www.frozen-cherry.info/Help_File_ENG/e-throttle_first_time.htm), [APS Setup](http://www.frozen-cherry.info/Help_File_ENG/e-throttle_aps_setup.htm), [Safety Features](http://www.frozen-cherry.info/Help_File_ENG/electronic_throttle_safety_fea.htm).

**Calibration order — do not reorder these steps.**

1. Wire everything per the schematic.
2. **Remove the ETB power relay before first power-up.** This stops the motor being driven unexpectedly.
3. PCLink → E-Throttle Mode = **Setup Mode**.
4. Set PWM Output = **Aux 9/10**. Set EThrottle Relay = **Aux 2**.
5. Set PWM Frequency (500 Hz to 1 kHz typical), Max Clamp and Min Clamp.
6. Build the E-Throttle Target Table. Y axis = APS (Main), X axis = Engine Speed. Start 1:1. Use 0 percent target at 0 percent APS so the G4X idle control works properly.
7. Accelerator Position Sensor window: set APS (Main) Source = An Volt 4, APS (Sub) Source = An Volt 5. **Assign Main to the full-range track.**
8. Set **APS (Sub) 100%** — see 5.3.4. Then run APS Calibration, or enter the four voltages manually.
9. Throttle Position Sensor window: set TPS (Main) Source = An Volt 2, TPS (Sub) Source = An Volt 3.
10. **Reinstall the ETB power relay.** Stand clear; the plate can snap open.
11. Run TPS Calibration with the bore clear of obstructions. If PCLink reports the H-bridge polarity is reversed, fix it by inverting the **Active State of Aux 9** — do not swap the motor wires.
12. Tune the PID gains. Link's typical starting values: Proportional 7.00, Integral 0.145, Derivative 25.00, Max Clamp 90 percent, Min Clamp −90 percent. All must be checked on this throttle body.
13. Set E-Throttle Mode = **ON**. Clear ECU fault codes. Confirm none return.

**Warning to carry into the document:** Setup Mode disables every safety feature. The car must never be driven in Setup Mode.

**Fault behaviour.** With mode ON, any e-throttle fault shuts the throttle down and applies an **1800 rpm limit**. The system will not restart until ECU power is cycled or the mode is changed. The relevant fault codes:

| Code | Fault |
|---|---|
| 69 / 70 | E-Throttle 1 Max / Min percent duty-cycle limit |
| 71 | Aux 9/10 supply error |
| 72 | Analog 5 V supply error |
| 75 | TPS versus target error |
| 76 | **TPS (Main) / TPS (Sub) tracking error** |
| 77 | **APS (Main) / APS (Sub) tracking error** |
| 78 / 79 | TPS Main / TPS Sub fault |
| 84 | Aux 9/10 H-bridge integrated circuit over-temperature |
| 85 / 86 | APS Main / APS Sub fault |

**Analog fault thresholds.** Set Error Low and Error High on all four DBW analog channels. Link's typical values are 0.1 V and 4.9 V, tightened toward the sensor's real working range where possible.

**Fault Delay** defaults to 1 second. Leave it there unless there is a reason.

**Key-off reset.** Aux 6 holds the EFI main relay so the ECU stays powered after the key is off, letting the throttle return to its default position under control. This is the reason Aux 6 exists and it must not be reassigned.

#### 5.3.7 Conflicts with the FuryX A-B pin map (#24)

Checked line by line against `Tables\FuryX A-B Connector_PinMap_v3.xlsx`.

| Item | FuryX pin map says | Current design says | Verdict |
|---|---|---|---|
| ETB motor | **Aux out 9 only** — "ETB Motor (+)". **No Aux 10 row exists.** | Aux 9 (B18) **and** Aux 10 (B26) | **Pin map is wrong.** An H-bridge needs both halves. Aux 9 alone cannot drive the motor. |
| ETB relay | Aux out 8 (A) — "ETB Relay Switched" | **Aux 2 (A20)** | **Conflict.** In the current design Aux 8 is the ECU-controlled start relay. Keep the design: relay on Aux 2, start on Aux 8. |
| V-Ethrottle | B — "ETB Motor Power In" from the ETB relay | Same (B5) | **Agrees.** |
| TPS Main | **An Volt 7** (B) | **An Volt 2** (A22) | **Conflict.** Pin map wins on nothing — it has no MAP sensor, no pressure sensors, and blank An Volt 1–4. |
| TPS Sub | **An Volt 8** (B) | **An Volt 3** (A33) | **Conflict.** Same reason. |
| Pedal Main | **An Volt 5** (B) "FPS MAIN" | **An Volt 4** (A14) | **Conflict.** |
| Pedal Sub | **An Volt 6** (B) "FPS SUB" | **An Volt 5** (B33) | **Conflict.** Note the pin map's An Volt 5 is the pedal main while the design's An Volt 5 is the pedal sub — the same channel with two different jobs. This is the kind of collision that destroys a throttle body. |
| CAN-Lambda | **DI 9 / DI 10 as CAN 2** | CAN 1 on the comms port | **Conflict** — see C5. |
| Aux 1 | "Active Low Boost" | Boost solenoid | **Agrees.** |

**Recommended resolution: the current design wins on every row.** The FuryX pin map has blank An Volt 1–4, no MAP sensor, no oil, fuel or coolant pressure channels, and no Aux 10. It is a partial draft, not a competing design. It should be archived, not reconciled. Its only unique contribution is the phrase *"Triggers ETB Relay, to deliver power to V Ethrottle terminal. Acts as safety. ECU controls the relay"* — carry that sentence forward into `DBW-ETB-AND-PEDAL.md`.

#### 5.3.8 Build note — throttle bore versus manifold flange

| Measurement | Value |
|---|---|
| Bosch throttle bore | 74.5 mm (plate stamped "745") |
| Soara dual-plenum flange inside diameter | 3.000 in = 76.2 mm |
| **Difference** | **1.7 mm on diameter, 0.85 mm on radius** |

**Record this as a build note, not a problem.** A 0.85 mm step on the radius at the throttle-to-plenum joint is a small backward-facing step in the direction of flow. It costs very little, and a backward-facing step (bore smaller than what follows) is the better of the two orientations — a forward-facing step would be worse. It is worth blending the adapter's inner edge if the adapter is being machined anyway, but it is not a reason to change parts.

**What still needs specifying:** the square four-bolt flange adapter itself. Bolt pattern, thickness, sealing arrangement and whether the adapter bore is 74.5 mm, 76.2 mm, or tapered between the two. No document describes it.

#### 5.3.9 Remaining gaps

| Gap | Detail |
|---|---|
| BRZ pedal pinout | Six pins, two sensors, but no factory pinout was found. Probe it: find the two 5 V feeds, the two grounds, and the two signals, then determine which track is full-range. |
| Pedal supply sharing | Confirm whether the two pedal tracks share one 5 V/ground pair or need separate pairs. |
| +5 V rail budget | Nine loads on A32. Confirm the XtremeX rail limit. Fault code 72 shuts the throttle down if it sags. |
| Motor wire gauge | Up to 10 A on two wires. Not yet in any build list. |
| Idle control | ~~With DBW there is no ISC valve. `XTREMEX-IO-TABLE.md` still lists Aux 2/3 as "Idle (ISC)".~~ **Resolved 2026-09-04** — `XTREMEX-IO-TABLE.md` Aux section corrected; Aux 2/3 now read ETB power relay / fuel pump relay, matching #1. |
| Manifold description | Google Drive #36 says "side feed intake manifold". Dan says Soara dual plenum. |
| CAN telemetry | 0x3EE byte 5 already carries `Throttle Error` to the cluster and is frozen — that covers the warning light. Full DBW telemetry for RealDash is proposed in section 5.6. |

### 5.4 Intelligent air conditioning control

**From `AC amplifier input signals.txt`** — the OEM amplifier has its own sensors and takes these inputs: ignitor/tach, coolant temp switch, vent outlet/cabin temperature, evaporator core thermocouple, trinary (high/low pressure) switch, and an ECU cancel/request signal.

**Decision from Dan (2026-08-31): document both paths in parallel, fully specified. Neither is ruled out. He will choose after testing.** This replaces the earlier "Option A preferred, Option B fallback only" framing. Both go into `AC-CONTROL.md` as equal, complete designs, and the pin cost of Option B is treated as a real reservation, not a hypothetical.

**Option A — through the OEM amplifier.**

| Item | Detail |
|---|---|
| ECU pin | Aux 4 (A18), low-side |
| Wiring | Aux 4 → amplifier `ACT` terminal |
| Polarity | Active low. Sinks to ground to cancel, floats when inactive. **No pull-up.** |
| ECU logic | Cancel on high engine load, wide throttle, or boost above a threshold |
| What the ECU does not do | It does not drive the compressor clutch. The amplifier keeps all its own protection logic. |
| Extra I/O | None. One Aux pin total. |
| Risk | The exact `ACT` circuit has not been confirmed against the OEM diagram. `OEM Mini Diagrams\AC compressor simplified.png` is the file to check. |

**Option B — full Link ECU control.**

The ECU replaces the amplifier entirely and drives the compressor clutch itself. It must therefore take over every protection the amplifier used to provide.

| Item | Detail |
|---|---|
| Clutch drive | Aux 4 (A18), low-side, grounds the A/C clutch relay coil directly. Same pin as Option A, different job. |
| Trinary pressure switch | One An Volt. **An Volt 10 (spare)** is the natural home. Reads refrigerant pressure for high and low cut-out. |
| Evaporator core temperature | One Temp channel — **but Temp has zero spare.** Either move the charge-pipe IAT (Temp 4) to An Volt 11 as a 0–5 V part, freeing Temp 4, or use An Volt 11 directly with a thermistor and a divider. |
| Cabin A/C request | Switchboard `SW_MASK` bit 1 over CAN — **no ECU pin needed.** This is already allocated and works for either option. |
| Condenser fan | Ign 5 (B13) as a spare-ignition low-side output. Same for both options. |
| **Total extra ECU pins vs Option A** | **2** — one An Volt for the trinary, one channel for the evaporator sensor. |
| Pin headroom after Option B | An Volt: 2 spare → **0 spare**. Temp: 0 spare → 0 spare (or −1 if the charge-pipe IAT is not moved first). |

**Tune logic Option B must implement, which the amplifier currently does for free:**

1. **Low-pressure cut-out** — disengage the clutch below the trinary's low threshold, to protect the compressor from running with no refrigerant charge.
2. **High-pressure cut-out** — disengage above the high threshold.
3. **Evaporator freeze protection** — disengage when the core sensor drops toward 0 °C, re-engage with hysteresis. Without this the evaporator ices and airflow stops.
4. **Cycling hysteresis** — minimum on-time and minimum off-time so the clutch does not chatter.
5. **Condenser fan trigger** — fan on with the compressor, and on above a pressure threshold.
6. **Load-based cancel** — the same high load / wide throttle / boost cancel as Option A.
7. **Idle handling** — with DBW this is a throttle-target offset rather than an ISC duty, and it must be applied on clutch engagement so the engine does not dip.

**Honest comparison.** Option A costs one pin and inherits proven protection. Option B costs three pins and moves compressor protection into a hand-written tune. Option B gives finer control, full A/C state on CAN, and removes a 33-year-old module from the system. Both are legitimate. **The thing that would make Option B a bad decision is doing it without items 1 through 4 above** — the amplifier is not just a relay, and replacing it means replacing what it protects against.

**Practical note on testing order.** Option A and Option B share the same Aux 4 pin and differ only in what that pin is connected to and in two extra sensor inputs. That means Option A can be wired and tested first, and Option B can be adopted later by adding the trinary and evaporator inputs and rerouting Aux 4 — **provided An Volt 10 and 11 are reserved now and not given to anything else.**

**Recommendation to carry into the plan:** reserve An Volt 10 and An Volt 11 for the Option B A/C sensors. Do not allocate them elsewhere until Dan has tested and chosen. If he settles on Option A, they are released.

**Delta for either option:**

| Item | Change needed |
|---|---|
| A/C request from the cabin | Currently switchboard `SW_MASK` bit 1. Confirm and document the physical switch. |
| Evaporator core state | Currently switchboard `SW_MASK` bit 0. Confirm what device drives it. |
| A/C status to RealDash | 0x3EF byte 7 is already allocated as an enum: 0 = Off, 1 = Requested, 2 = Compressor Engaged, 3 = Fault. No change. |
| A/C condenser fan | `XTREMEX-IO-TABLE.html` puts it on Ign 5 (B13) as a spare-ignition low-side output. Marked proposed. |
| Cabin temperature | Available on switchboard 0x640 but the routing rule forbids RealDash reading it. Restore via the ECU echo in section 5.6. |

### 5.5 Electric power steering pump

**Researched facts** ([Link forum: MR2 power steering speed signal](https://forums.linkecu.com/topic/16021-mr2-power-steering-speed-signal/), [DIY Electric Car: Toyota MR2 EHPS VSS/SPD](https://www.diyelectriccar.com/threads/toyota-mr2-ehps-vss-spd-signal.46812/)):

- The pump's `SPD` input normally comes from the combination meter, not the ECU.
- **4 pulses per revolution.** Reported as 0–5 V on a related RAV4 system; 0–12 V is also reported for MR2 units and is **not resolved**.
- The signal is not required for the pump to run. Without it the pump winds down slowly on its own. With it, the pump reduces assist at speed and reacts faster.

**Current allocation:** Aux 7 (A27), low-side pulse output, direct to the MRS pump `SPD` pin (yellow/white), no series resistor, with speedo-out scaling set so the pump idles down above roughly 10 km/h.

**Delta and gaps:**

| Gap | Detail |
|---|---|
| Signal voltage | **Unresolved: 0–5 V or 0–12 V.** A low-side output pulls to ground and floats when off, so the high level is set by whatever pull-up the pump provides. If the pump has no internal pull-up, a pull-up resistor to 5 V or 12 V is required — which contradicts the "no external pull-ups needed" claim in `XTREMEX-IO-TABLE.html`. **Measure it before wiring.** |
| Scaling | 4 pulses per wheel revolution must be converted to a Link speedo-out frequency. The tyre rolling circumference and final drive ratio are needed and are not recorded. |
| Source of vehicle speed | `XTREMEX-IO-TABLE.html` derives speed from four ABS wheel-speed sensors on DI 3–6 (marked proposed). Google Drive #36 says "using abs sensor for speed instead of trans sensor" and names Highlander sensors at the rear and Camry sensors at the front. Confirm the sensors are the two-wire reluctor type the ECU can read. |
| Idle-up | `Other ECU IO and MATH.txt` calls for "inverse of VSS out — idle up for EPS power draw". With DBW this becomes a throttle-target offset, not an ISC duty. Not yet written as tune logic. |
| Physical location | Google Drive #36: passenger front engine bay. |

### 5.6 Proposed new CAN frame 0x3F2

The three cluster-facing frames are frozen. The three RealDash frames 0x3EF–0x3F1 are full. Five of the eight bytes needed below have nowhere to go. Rather than disturb anything frozen, add one new ECU → RealDash frame.

**0x3F2 (decimal 1010) — DBW, A/C and Chassis Extended. ECU → RealDash. 100 ms. Custom, BigEndian.**

| Byte | Field | Type | Scale | Offset | Source |
|---|---|---|---|---|---|
| 0 | ETB target position % | uint8 | 1 | 0 | ECU E-Throttle target |
| 1 | ETB actual position % | uint8 | 1 | 0 | TPS main |
| 2 | Accelerator pedal % | uint8 | 1 | 0 | APS main |
| 3 | DBW fault code | uint8 | 1 | 0 | 0 = OK; nonzero = Link throttle-error code |
| 4 | Lambda controller status | uint8 | 1 | 0 | CAN-Lambda module status/error |
| 5 | Cabin temperature | uint8 | 1 | −50 | ECU echo of switchboard 0x640 — restores the value dropped from 0x3F0 |
| 6 | EPS speed-out duty % | uint8 | 1 | 0 | The value the ECU is sending to the pump |
| 7 | A/C amplifier cancel state | uint8 | 1 | 0 | 0 = not cancelling, 1 = cancelling |

**Why this is safe:** 0x3F2 is inside the block the allocation table already marks "0x3F2–0x63F reserved / available". It is ECU-transmitted only. The cluster does not decode it and needs no firmware change. Only `link_g4x_realdash.xml` and the LCS/JSON pair change.

**Byte 5 does not break the routing rule.** The switchboard still talks only to the ECU. The ECU echoes. RealDash still reads only ECU frames. This is exactly the pattern already used for 0x3EF bytes 3 and 5.

---

## 6. Conflict list

Every place two sources disagree, with the recommended resolution.

> **Resolution log**
>
> - **C1 (engine 3S-GTE → 5S-GTE) — RESOLVED 2026-09-04.** Applied to the whole-engine identity
>   labels in `README.md`, `XTREMEX-IO-TABLE.md`, `XTREMEX-IO-TABLE.html`, `SCHEMATIC-WIRING.html`,
>   `FUEL-SYSTEM.md`, `REALDASH-LAYOUT.md`, `realdash-simulation.html`, `rd-build/README.md` and
>   `rd-build/realdash-simulation-REFERENCE.html` (16 occurrences). Deliberately **not** applied to
>   genuine 3S-GTE *cylinder head* references, PDF-extracted source text, the intercooler research
>   set, generated reports, or the Source A column of this table — the head really is a 3S-GTE, and
>   rewriting quoted sources would falsify provenance.
> - **C2 (ECU FuryX → XtremeX) — RESOLVED 2026-09-04 for imported calibration data.** The engine
>   calibration in `tune/` was imported from the FuryX-era `st185-furyx-base-map` repo with
>   `ecu.model` corrected to XtremeX and `driveline.reverse_switch` corrected per **C16**
>   (switchboard → CAN, DI 9/10 spare). That repo's `io_assignments.yaml` and `config/can/*` were
>   **not** imported — see `tune/README.md`. C2 remains open for the FuryX-sourced files listed in
>   section 2 that are still awaiting archival.
> - **C3 (throttle type) — CLOSED 2026-09-06.** The cable-throttle claim lived only in
>   `XTREMEX-IO-TABLE.md`, which is now deleted. No current document asserts cable throttle.
> - **C7 / C8 (Aux 2, Aux 7) — CLOSED 2026-09-06.** Source B for both was `XTREMEX-IO-TABLE.md`;
>   with it deleted, `XTREMEX-IO-TABLE.html` is uncontested. C8's consequence still stands as
>   open decision 14 (where CEL moves to).
> - **C26 (DBW analog channels) — CLOSED 2026-09-05.** The An Volt map was reconciled against
>   `XTREMEX-IO-TABLE.html`; the pedal/throttle swap risk is gone from every live document.
> - **C11 (wire colours) — STILL OPEN.** Colours were deliberately dropped rather than carried
>   onto corrected channel numbers. Read them off `XtremeXQuickstartGuide.pdf`.


| # | Subject | Source A | Source B | Recommended | Why |
|---|---|---|---|---|---|
| C1 | Engine | 3S-GTE — every repo document | 5S-GTE — Dan, and the 2026-08-30 turbo research (2.19 L, 5S-FE block, 3S-GTE head) | **5S-GTE** | `XTREMEX-IO-TABLE.html` already contradicts itself, saying "36-2 crank wheel (Beams/5S)". The 3S-GTE label is a copy-forward error. |
| C2 | ECU model | FuryX — pin map, loom list, quickstart PDFs, netlist, harness parts, package zip | XtremeX — repo docs, `XtremeXQuickstartGuide.pdf`, commit `d2dda23` "Switch ECU to Link G4X XtremeX" (2026-07-04) | **XtremeX** | Every FuryX-named file predates 2026-07-04. |
| C3 | Throttle type | Cable — `XTREMEX-IO-TABLE.md`, both app saves | DBW — both HTML files, pin map, Drive I/O list | **DBW** | The hardware is bought. The cable-throttle claim is the single most misleading statement in the documentation set. |
| C4 | An Volt allocation | Three incompatible maps: HTML pair / pin map #24 / loom list #25 | — | **HTML pair** | It is the only one that is complete, pin-numbered, and consistent with the DBW hardware. |
| C5 | CAN-Lambda bus | CAN 1 — HTML pair, all repo docs | CAN 2 on DI 9/10 — pin map #24 | **CAN 1** | Keeps one bus, keeps DI 9/10 free, and the module is already 1 Mbit/s native. Nothing is gained by a second bus. |
| C6 | Aux 1 | Boost solenoid — HTML pair, pin map, both app saves | A/C clutch relay — loom list #25 | **Boost solenoid** | Four sources to one, and the loom list is the file with placeholder pin numbers. |
| C7 | Aux 2 | ETB power relay — HTML pair | Idle ISC — `XTREMEX-IO-TABLE.md`; A/C fan — 2026-08-22 app save | **ETB power relay** | With DBW there is no ISC valve. |
| C8 | Aux 7 | EPS speed-out — HTML pair | Tacho/CEL — `XTREMEX-IO-TABLE.md`; CEL — 2026-08-28 app save | **EPS speed-out** | Aux is 100 percent full. CEL must move to a spare Ign or Inj output. |
| C9 | Trigger 1 | Crank — HTML pair, MD, app saves, pin map | Cam — loom list #25 | **Trigger 1 = crank** | Loom list is the outlier and is obsolete. |
| C10 | Ignition loom | Loom A (A13–A10) — HTML pair, pin map | Loom B — loom list #25 | **Loom A** | The schematic gives real pin numbers. |
| C11 | Ignition wire colour | Orange family — MD; White — pin map; Blue/White etc — loom list | — | **UNRESOLVED** | Read the colours off `XtremeXQuickstartGuide.pdf`. Do not guess. |
| C12 | Turbo speed input | DI 1 (A30) — HTML pair | DI 5 — both app saves; DI 2 — loom list | **DI 1** | Schematic has the pin number. |
| C13 | Flex-fuel input | DI 2 (A31) — HTML pair | DI 1 — app saves and MD | **DI 2** | Same reason. |
| C14 | Fuel temperature source | Flex sensor — HTML pair | Temp 4 discrete — MD, 08-22 app save; Temp 3 — loom list | **Flex sensor** | It frees the Temp 4 input for the charge-pipe IAT. Temp has zero spare, so this matters. |
| C15 | Clutch switch | DI 8 (B29) — HTML pair | DI 2 — app saves and MD | **DI 8** | Flat-shift latency is the reason it is ECU-direct. |
| C16 | Brake / reverse / cruise | Switchboard over CAN — HTML pair | ECU DI 3/DI 4 — MD, app saves | **Switchboard** | Keeps ECU digital inputs for frequency signals, which the switchboard cannot do. |
| C17 | Bus node count | 4 nodes — `WIRING.md`, `CAN-BUS-MASTER-DESIGN.md`, `README.md` | 5 nodes incl. CAN-Lambda — `SCHEMATIC-WIRING.html`, allocation table | **5 nodes** | The lambda module is physically on the bus. |
| C18 | 120 Ω termination ends | ECU + Pi — `WIRING.md`, 08-28 app save | CAN-Lambda end + Pi — `SCHEMATIC-WIRING.html`; cluster — 08-22 app save | **UNRESOLVED** | Termination belongs at the two physical harness extremities. Document it as a measured install step, not a drawing. Three terminations will break the bus. |
| C19 | Lambda sensor path | CAN-Lambda module — repo docs, HTML pair | Direct LSU 4.9 heater on B connector — loom list #25 | **CAN-Lambda module** | The XtremeX has no lambda controller in the current plan. |
| C20 | Intake manifold | Side-feed — Google Drive #36 | Soara dual plenum, 3 in ID flange — Dan | **Soara dual plenum** | Drive file is from March. The 74.5 mm bore versus 76.2 mm flange step is quantified in 5.3.8 and is a build note, not a conflict. |
| C24 | ETB motor output | **Aux 9 only, no Aux 10 row** — FuryX pin map #24 | Aux 9 (B18) + Aux 10 (B26) — HTML pair | **Aux 9 + Aux 10** | An H-bridge needs both halves. Aux 9 alone cannot drive the motor in both directions. Pin map is incomplete, not an alternative. |
| C25 | ETB power relay | **Aux 8** — FuryX pin map #24 | **Aux 2 (A20)** — HTML pair | **Aux 2** | Aux 8 is the ECU-controlled start relay in the current design. Using Aux 8 for the ETB relay would collide with it. |
| C26 | DBW analog channels | An Volt 5/6/7/8 — FuryX pin map #24 | An Volt 2/3/4/5 — HTML pair | **An Volt 2/3/4/5** | The two maps assign **An Volt 5 to different jobs** — pedal main in one, pedal sub in the other. Wiring to the wrong document swaps a pedal signal for a throttle signal. |
| C27 | ETB bore | 74 mm — every retailer listing | **74.5 mm** — plate stamped "745" | **74.5 mm** | Same part. Use 74.5 mm for the flange step and any airflow work. |
| C21 | EPS speed signal voltage | 0–5 V — RAV4 reference | 0–12 V — MR2 reports | **UNRESOLVED — measure it** | Determines whether a pull-up resistor is needed, which contradicts the "no external pull-ups" claim. |
| C22 | Wiring app data | 2026-08-22 save | 2026-08-28 save | **Neither** | They disagree with each other on 8 rows and on termination, and both are behind `SCHEMATIC-WIRING.html` (2026-07-27 content, but pin-accurate). Rebuild the app's data from the schematic. |
| C23 | Cabin temperature | Available on switchboard 0x640 | Routing rule forbids RealDash reading 0x640 | **ECU echo on 0x3F2 byte 5** | Restores the value without breaking the rule. |

---

## 7. Proposed single source of truth

| Domain | Authoritative document | Why | What it replaces |
|---|---|---|---|
| **ECU I/O assignment** | `XTREMEX-IO-TABLE.html` | The only complete, internally consistent, DBW-aware channel plan. Carries the pin budget. | `XTREMEX-IO-TABLE.md`, `FuryX_LoomA_LoomB_List.xlsx`, Google Drive `ECU I/O List.xlsx` |
| **Wiring diagram** | `SCHEMATIC-WIRING.html` | The only document with real ECU pin numbers on every net. | `FuryX A-B Connector_PinMap_v3.xlsx`, all FuryX netlist/connector XML and PDF |
| **Harness build list** | `HARNESS-BUILD-LIST.csv` — **to be created**, derived from the schematic | Nothing currently holds wire colour, gauge and terminate-at in a form that matches the current design. Google Drive #36 has that detail but the wrong design. | Google Drive `ECU I/O List.xlsx` |
| **CAN ID map (human)** | `CAN-BUS-ID-ALLOCATION-TABLE.md` | Already the master map. Needs 0x3BE and 0x3F2 added. | `Link ECU CAN stream data.png`, `CAN-CONFIG-STATUS.md` |
| **CAN frame contract (frozen)** | `center-cluster-esp32-p4/CANBUS-ENCODE-DECODE-REFERENCE.html` | Derived from the frozen cluster firmware. Nothing may contradict it. | the duplicate copy in `st185-link-ecu-config` |
| **PCLink import (machine)** | `link_g4x_can_setup.lcs` + `.json` | Verified correct. | none |
| **RealDash channel map** | `link_g4x_realdash.xml` | Active work. | none |
| **Interactive wiring app** | The hosted artifact, **after** its data is rebuilt from the schematic and its source is saved into the repo | Convenient to work with, but currently the least trustworthy and the least backed-up artifact in the set. | the two Google Doc saved states |

**Retired to `archive/`** (kept, not deleted, with a one-line note saying why): items 3, 11, 16, 17, 21, 24, 25, 27, 28, 29, 32, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 51.

---

## 8. Proposed consolidated structure

All of it inside `C:\projects\st185-link-ecu-config`, so one `git push` protects everything.

```
st185-link-ecu-config/
├── README.md                          index + which file is authoritative for what
├── DOCS-CLEANUP-PLAN.md               this document
│
├── docs/ecu/
│   ├── XTREMEX-IO-TABLE.html          AUTHORITATIVE — channel plan, pin budget
│   ├── SCHEMATIC-WIRING.html          AUTHORITATIVE — schematic with ECU pin numbers
│   ├── HARNESS-BUILD-LIST.csv         AUTHORITATIVE — new; wire colour, AWG, terminate-at
│   └── PIN-BUDGET.md                  new; free vs used per channel group, one page
│
├── docs/can/
│   ├── CAN-BUS-ID-ALLOCATION-TABLE.md AUTHORITATIVE — ID map + byte layouts
│   ├── CANBUS-ENCODE-DECODE-REFERENCE.html  FROZEN mirror of the cluster contract
│   ├── CAN-BUS-MASTER-DESIGN.md       architecture, 5 nodes, fault tolerance
│   └── CANBUS-LINK-G4X-CONFIG.md      PCLink setup steps
│
├── docs/devices/
│   ├── LINK-CAN-LAMBDA.md             new; 0x3B6–0x3BE, 1 Mbit/s native, PCLink steps
│   ├── ECUMASTER-SWITCHBOARD.md       renamed from ECUMASTER_SWITCHBOARD_SETUP.md
│   ├── DBW-ETB-AND-PEDAL.md           new; Bosch 0 280 750 474 (74.5 mm) + BRZ pedal,
│   │                                  connector BOM, safety settings, calibration order
│   ├── AC-CONTROL.md                  new; Option A and Option B BOTH fully specified
│   │                                  (Dan's decision 2026-08-31 — neither ruled out)
│   └── EPS-PUMP.md                    new; SPD signal, scaling, pull-up question
│
├── docs/notes/
│   └── OTHER-ECU-IO-AND-MATH.md       living note, converted from .txt
│
├── config/
│   ├── link_g4x_can_setup.lcs
│   ├── link_g4x_can_setup.json
│   └── link_g4x_realdash.xml
│
├── app/
│   └── xtremex-wiring-app.html        new; the interactive app's source, saved locally
│
├── WIRING.md                          CAN physical topology + cluster power only
└── archive/
    └── README.md                      what was retired, when, and why
```

**Rules to adopt with the structure:**

1. One fact lives in one file. Everything else links to it.
2. Nothing gets published from a working tree. Commit first.
3. Any file that names a Link ECU model must say XtremeX. Any file that names the engine must say 5S-GTE.
4. The interactive app's source lives in `app/` and is regenerated from `docs/ecu/`, never the reverse.

---

## 9. Ordered work plan

Each step lists what Dan must decide before it can start.

### Step 0 — Protect what exists. Do this first, today.

- Commit `SCHEMATIC-WIRING.html` on branch `ECU-wiring-design`.
- Merge `ECU-wiring-design` into `main` and push. Right now `main` on GitHub does not have the DBW I/O table.
- Export the interactive app's source from the hosted artifact and commit it to `app/`.
- Delete the stale worktree `.claude/worktrees/bridge-cse_018RH...` after confirming it holds nothing unique.

**Decision needed:** none. This is pure risk reduction and nothing is lost by doing it.
**Blocks:** everything else.

### Step 1 — Fix the two global facts.

- Replace 3S-GTE with 5S-GTE everywhere.
- Replace FuryX with XtremeX everywhere, and archive the FuryX-sourced files.

**Decision needed:** confirm the engine is a 5S-GTE (5S-FE block, 3S-GTE head, 2.19 L) and the ECU is a G4X XtremeX.
**Depends on:** Step 0.

### Step 2 — Retire the contradictions.

- Move items 3, 11, 16, 17, 21, 24, 25, 27, 28, 29, 32, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 51 to `archive/`.
- Before archiving Google Drive #36, extract its wire colour and AWG detail into the new `HARNESS-BUILD-LIST.csv`. It is the only place that data exists.

**Decision needed:** approve the archive list, and confirm that Drive #36's wiring detail is worth carrying forward.
**Depends on:** Step 1.

### Step 3 — Resolve the two unresolved conflicts that need physical measurement.

- **C11 wire colours:** read them off `XtremeXQuickstartGuide.pdf` and put them in the harness build list.
- **C18 termination:** identify the two physical harness ends and record which devices they are.
- **C21 EPS voltage:** measure the `SPD` line on the MRS pump. Determine whether a pull-up is needed.

**Decision needed:** Dan does the measurements, or approves ordering the work.
**Depends on:** nothing. Can run in parallel with Steps 1–2.

### Step 4 — Build the consolidated structure.

- Create the folder tree from section 8.
- Move files. Write the five new device documents.
- Write `PIN-BUDGET.md` and `HARNESS-BUILD-LIST.csv`.
- Rewrite `README.md` as an index that names the authoritative file for each domain.

**Decision needed:** approve the structure in section 8, including the `docs/ecu`, `docs/can`, `docs/devices` split.
**Depends on:** Steps 1 and 2.

### Step 5 — Close the CAN documentation gaps.

- Reserve 0x3B6–0x3BE for CAN-Lambda in the allocation table.
- Add frame 0x3F2 per section 5.6 to the allocation table, the LCS, the JSON, and `link_g4x_realdash.xml`.
- Diff `link_g4x_can_setup.json` against the LCS and reconcile.
- Correct the node count from 4 to 5 in `WIRING.md`, `CAN-BUS-MASTER-DESIGN.md` and `README.md`.
- Assign switchboard `SW_MASK` bits 5–7.

**Decision needed:** approve the 0x3F2 byte layout, and confirm the cabin-temperature echo is wanted.
**Depends on:** Step 4.

### Step 6 — Write the five device documents in full.

- `LINK-CAN-LAMBDA.md` — PCLink steps, IDs, bit rate, the LSU 4.9.
- `ECUMASTER-SWITCHBOARD.md` — the 500 → 1000 kbps change, base ID, bit assignments, the 0.5 A output limit, the routing rule stated once.
- `DBW-ETB-AND-PEDAL.md` — sections 5.3.1 through 5.3.9 in full: part numbers, the Bosch 6-pin table, the D 261 205 358-01 connector BOM entry, the BRZ pedal probe procedure and the APS (Sub) 100% trap, the supply and ground plan, the four An Volt channels, the calibration order, the twelve fault codes, and the 1.7 mm flange step build note.
- `AC-CONTROL.md` — **both** Option A and Option B specified to the same depth, with the seven pieces of tune logic Option B requires, the shared-pin migration path, and the An Volt 10/11 reservation.
- `EPS-PUMP.md` — signal form, scaling maths, source of speed, the pull-up question, idle-up logic.

**Decision needed:** confirm the ABS wheel-speed sensors are the intended speed source. A/C no longer needs a decision here — both paths are being documented per Dan's instruction, and the choice moves to after testing.
**Depends on:** Steps 3 and 4.

### Step 7 — Rebuild the interactive app's data.

- Regenerate the app's device list from `SCHEMATIC-WIRING.html`, not from either Google Doc save.
- Save the app's source into `app/`.
- Retire both Google Doc saves.

**Decision needed:** confirm the app should be kept at all, given it has drifted twice and has no backup.
**Depends on:** Steps 4, 5 and 6.

### Step 8 — Verify.

- Cross-check every pin in `HARNESS-BUILD-LIST.csv` against `SCHEMATIC-WIRING.html` and `XTREMEX-IO-TABLE.html` — three-way agreement or it does not ship.
- Confirm no channel is assigned twice.
- Confirm the LCS, the JSON, the RealDash XML, and the allocation table all agree byte for byte.
- Confirm nothing in the frozen cluster contract has changed.
- Push. Address any GitHub Copilot review comments.

**Decision needed:** none.
**Depends on:** all of the above.

---

## 10. What could not be found or verified

Stated plainly.

1. **The interactive wiring app's source code.** It does not exist on this machine. It exists only as a hosted Claude artifact. If that artifact is deleted, the app is gone.
2. **`link_g4x_can_setup.json`.** Not opened this pass. It claims to be the canonical twin of the LCS. Unverified.
3. **~~The Bosch part number.~~ RESOLVED 2026-08-31** — Dan identified it from photographs of the part: Bosch **0 280 750 474**, Porsche **997 605 115 03**, VAG **022 133 062 AJ**, plate stamped **745** for 74.5 mm. Still unverified: no Bosch data sheet names 0 280 750 474 directly, so the two sensor voltage curves are inherited from the ETB platform data sheet and should be confirmed on the bench.
4. **The BRZ pedal part number and connector pinout.** No factory pinout was found in an accessible source. Only that it is a 6-pin connector with two redundant sensors. **This one matters more than it looks** — Toyota-family pedals often have a sub track that stops rising at 60–70 percent of travel, and if that is true here, PCLink's `APS (Sub) 100%` must be set to that value or the throttle will fault out. Probe both tracks across full travel before wiring.
5. **Ignition and injector wire colours.** Three sources give three different answers. None matches the vendor guide because the vendor guide was not parsed.
6. **The EPS `SPD` signal voltage.** Sources give both 0–5 V and 0–12 V. This determines whether a pull-up resistor is needed.
7. **The two physical CAN bus ends.** Three sources give three different answers. This is an install-time measurement, not a documentation decision.
8. **`TE_BOM_with_screenshots.xlsx`** and **`st185-furyx-ecu-package.zip`.** Not opened.
9. **~~The A/C amplifier `ACT` circuit.~~ RESOLVED 2026-09-06.** Aux 4 drives the amplifier `ACT` terminal: **ground = kill, floating = normal** — active-low sink, no pull-up, matching `AC amplifier input signals.txt`. `AC1` is an **input** to the amplifier and is **never** a kill signal; it appears nowhere in the repo and must not be introduced. Written into `XTREMEX-IO-TABLE.html` and the harness schematic. Still worth confirming the terminal against `OEM Mini Diagrams\AC compressor simplified.png` before crimping.
10. **The square four-bolt flange adapter** between the 74.5 mm ETB and the 76.2 mm Soara plenum. The step itself is quantified (1.7 mm on diameter — see 5.3.8), but no document describes the adapter's bolt pattern, thickness, sealing arrangement, or whether its bore is 74.5 mm, 76.2 mm, or tapered.
10a. **The XtremeX +5 V rail current limit.** Nine sensor loads are on it, four of them safety-critical DBW channels. Fault code 72 shuts the throttle down if the rail sags.
11. **Tyre rolling circumference and final drive ratio.** Needed for EPS speed-out scaling. Not recorded anywhere.
12. **GitHub remote state.** The `github` MCP server failed to connect this session ("Incompatible auth server: does not support dynamic client registration"), so the remote branch state could not be checked directly. Local git says `main` does not contain commit `b945ac6`.

---

## 11. Assumptions being challenged

Four things the documentation currently asserts that deserve pushback.

1. **"No external pull-up resistors are required."** ~~`XTREMEX-IO-TABLE.html` states this as settled.~~ **Falsified 2026-09-06** — the cam Hall on Trigger 2 needs a **1.8k pull-up to +8V Out**. (Not the 2.4k in the RacerX kit; that value is sized for a 12V supply and is wrong on the 8V rail.) The claim also still cannot be settled for the EPS `SPD` line until its voltage is measured — a low-side output cannot produce a high level on its own.

2. **"The pin budget is a comfortable fit."** Aux has **zero** spare outputs. Temp has **zero** spare inputs. An Volt has two spare, and if Dan chooses A/C Option B, **both of those go too**. Adding one more actuator means a spare Ign/Inj output or a power distribution module. That is not comfortable — it is exactly full, and one decision away from being over-subscribed.

3. **Four ABS wheel-speed sensors on DI 3–6.** This consumes four of ten digital inputs and is still marked "proposed", with a note that it "drops first". Committing four inputs to a feature that is first to be cut is worth reconsidering before the harness is cut.

4. **The interactive wiring app as a working tool.** It has produced two saved states that disagree with each other and with the repo, and it has no backup. Right now it is a source of drift, not a cure for it. Either it becomes generated output from the repo, or it should be retired.

---

## 12. Open questions and decisions for Dan

1. **Confirm the engine and ECU.** 5S-GTE (5S-FE block, 3S-GTE head, 2.19 L) and Link G4X **XtremeX** — correct? Every repo document currently says 3S-GTE, and much of the source material is FuryX.
2. **Approve `XTREMEX-IO-TABLE.html` and `SCHEMATIC-WIRING.html` as authoritative** for ECU I/O and the wiring diagram, superseding the two OneDrive spreadsheets and the Markdown I/O table.
3. **Approve the archive list** in section 7 — 22 items moved to `archive/`, none deleted.
4. **Approve the folder structure** in section 8.
5. **A/C — decided 2026-08-31: both paths documented in parallel, choice deferred until after testing.** The follow-on question: **approve reserving An Volt 10 and An Volt 11** for Option B's trinary pressure switch and evaporator core sensor. If they are given to something else now, Option B stops being available without moving another channel.
6. **Approve new CAN frame 0x3F2** and its byte layout in section 5.6, including the cabin-temperature echo on byte 5.
7. **Decide the fate of the interactive wiring app.** Keep it and regenerate its data from the schematic, or retire it. It has no local backup either way — Step 0 saves it regardless.
8. **Confirm the speed source for EPS and traction control** — four ABS wheel-speed sensors on DI 3–6, or something cheaper in pins.
9. **Provide tyre rolling circumference and final drive ratio** so the EPS speed-out scaling can be calculated.
10. **Measure the MRS pump `SPD` line** — 0–5 V or 0–12 V, and whether it has an internal pull-up.
11. **Identify the two physical CAN bus ends** on the installed harness so termination is documented once and correctly.
12. **~~Confirm the Bosch ETB part number.~~ Done 2026-08-31.** Replaced by: **describe the square four-bolt flange adapter** — bolt pattern, thickness, sealing, and whether its bore is 74.5 mm, 76.2 mm or tapered. The 1.7 mm step itself is recorded as a build note and needs no action.
12a. **Probe the BRZ pedal** across full travel and report both track voltages at closed and at full throttle. If one track stops rising early, report the APS (Main) percentage where it stops — that number goes straight into PCLink's `APS (Sub) 100%` setting.
12b. **Confirm the XtremeX +5 V rail current limit** against the nine sensor loads on it.
12c. **Add `D 261 205 358-01`** (Bosch 6-pin mating connector kit) to the parts list if it is not already bought.
13. **Confirm the intake manifold** is the Soara dual plenum, not the side-feed unit named in the March Drive spreadsheet.
14. **Decide where CEL moves to.** Aux 7 now belongs to the EPS speed-out, and Aux is full. A spare Ign or Inj output is the obvious home.
15. **Fix or replace the GitHub MCP connection** so remote branch state can be checked and Copilot review comments can be addressed.

---

16. **~~PDM vs direct Aux for the fuel pump (Aux 3) and radiator fan (Aux 5).~~ DECIDED 2026-09-06 —
    direct Aux, no PDM.** Dan: *"I will only use a PDM if I am completely out of outputs on my ECU.
    Plan on using all of my ECU outputs first... I can add it myself without much trouble later on."*
    The PDM is **out of the plan**. Plan against the ECU's own outputs — all 10 Aux, then the spare
    Ign 5–8 / Inj 5–8 low-side drives. `XTREMEX-IO-TABLE.html` already reflects this. Where existing
    text says "→ PMU/PDM if more needed", read it as *the fallback Dan adds himself later*, not a
    design step. Note the standing constraint from assumption 2: Aux is at **zero spare**, so any new
    actuator must come out of a spare Ign/Inj output.

17. **VR wheel-speed dropout at low road speed.** The four ABS sensors on DI 3–6 are variable
    reluctance. A VR sensor's output amplitude falls with speed, and Link's own forum moderator puts
    the DI arming threshold at roughly **1.5 V**, with VR wheel-speed sensors going dead below about
    **24 km/h**. `XTREMEX-IO-TABLE.html` already hedges with "conditioner if low-speed dropout", but
    no part has been chosen. The recommended fix is a **VR-to-Hall converter** on each channel.
    This is a real functional gap for traction control, which needs wheel speed exactly in the
    low-speed range where the sensors stop reporting. It also interacts with assumption 3 (four DIs
    committed to a feature marked "drops first") and with decision 8. **Dan's call** — accept the
    low-speed blind spot, fit conditioners, or change the speed source.

---

## 13. Reconciliation log — 2026-09-06

Applied to the repo this pass. Listed so section 9's step numbering does not have to absorb them.

| Decision | Status | Where it landed |
|---|---|---|
| Reverse switch on the switchboard over CAN, **not** DI 4 | **Already correct** — no change needed | `XTREMEX-IO-TABLE.html` switchboard table; DI 3–6 all four wheel speeds. The harness schematic confirms `B21 = DI 4 WSS FR`. There is **no DI shortage**: four sensors on DI 3/4/5/6, DI 9–10 spare. |
| A/C kill on amp `ACT`, ground = kill, floating = normal; `AC1` never a kill signal | **Fixed** | Aux 4 row + A/C panel in `XTREMEX-IO-TABLE.html`; relay note in the harness schematic. `AC1` appears nowhere in the repo — verified, and it must stay that way. |
| "V-Ethrottle", never "+14V Aux 9/10" | **Fixed** | `apps/harness-schematic/index.html` — connector B pin label and the ETB relay wire label. Remaining "Aux 9/10" uses are correct: they name the **motor outputs** and the PCLink E-throttle setting. |
| Cam sensor: +8V Out, **1.8k** pull-up (not the kit's 2.4k), Brown/Black/Blue, shield at ECU end only | **Added** — was absent | Trigger 2 row, pull-up panel and harness-build tasks in `XTREMEX-IO-TABLE.html`; `A6 +8V Out` relabelled in the schematic. The only 2.4k in the repo is the **flex sensor**, which is a different device and stays. |
| Loom B has no native +5V; jumper from Loom A | **Added** — was absent | Power/ground table + harness-build task. Verified against the schematic pin lists: `A32 = +5V Out`, Loom B has no 5V pin. |
| Grounds: Gnd Out for sensors only, never chassis; Ground = ECU reference; shields carry no current, ECU end only; APS/TPS may share Gnd Out | **Added** — was vague | Power/ground table split into four explicit rows. |
| Headers: 5S-GTE, 74.5 mm | **Fixed** | 5S-GTE was done 2026-09-05. 74.5 mm applied to `XTREMEX-IO-TABLE.html`, the schematic app and its README. |
| `XTREMEX-IO-TABLE.md` deleted, README repointed | **Done** | Repo-wide grep first: the only live pointers were `README.md`, `CLAUDE.md`, `archive/README.md` and `tune/README.md`, all repointed to the `.html`. References inside this plan are kept as historical conflict records. |

**Not decided — see decisions 16 and 17 above.**

### Still unverified after this pass

**Every physical pin number** — `A20`, `A22`, `B18`, `B5`, `B21`, `A32` and all others in
`SCHEMATIC-WIRING.html`, `apps/harness-schematic/index.html` and this document — is **drafted, not
confirmed**. Authority order: Link's `XtremeXQuickstartGuide.pdf` first, then other official Link
documentation, then Link forums / HPAcademy / MR2 / ST185 AllTrac forums (Link-affiliated forum
accounts are trustworthy sources). A caveat panel saying so now sits in `XTREMEX-IO-TABLE.html`.
Nothing in this pass verified a pin number, and none was invented.

### Contradictions found but not rewritten

Two files under `docs/5sgte-project-data/` are copies of a claude.ai Project and are **source
material**, so they were left intact rather than edited:

- `ECU_WIRING_MASTER_SOURCE_OF_TRUTH.md` — titled "master source of truth" but is a **staging
  draft** that never landed. It proposes DI4/DI5 decisions that contradict the current wheel-speed
  block. The title is dangerous; treat `XTREMEX-IO-TABLE.html` as authoritative.
- `Reverse_Camera_Trigger_CORRECTED_sourced_from_repos.md` — states "DI4–DI10 (7 channels) are
  marked spare". Stale: DI 4–6 are wheel speed, DI 7 start, DI 8 clutch.

---

*Sections 0–12 were written 2026-08-31 as plan-only. Section 13 records changes actually applied on 2026-09-06.*
