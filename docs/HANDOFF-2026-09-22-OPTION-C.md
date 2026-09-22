# HANDOFF — ST185 harness, Option C then Option A

Written 2026-09-22. Hand this to any agent with repo access. Read it start to
finish before touching a file.

Repo: `living-relation/st185-link-ecu-config`
Local: `C:\projects\shipping\st185-link-ecu-config` (Windows, PowerShell — `&&`
does not work, use `;`)
Last commit at handoff: `6c43277 Plan 6.50-6.53`. Tree clean, `main` in sync.

---

## 0. Rules you must not break

1. **Never guess a part number, a pinout, a fuse rating or a wire colour.** If it
   is not in the repo, in an EWD snip, or on a manufacturer page you actually
   read, write `TBD` plus what is missing. Daniel has been burned by invented
   parts already (see plan 6.49, the RADLOK).
2. **`docs/SHIELD-RULES.md` is enforced by `docs/harness/audit_shields.py`.** Read
   it. Do not re-open a rule in it.
3. **Link ECU documentation and the repo SoTs win** over anything you remember.
4. **Run `python docs/harness/check_all.py` before every commit.** It must print
   `all checks passed`.
5. `docs/harness/rebuild/` is the source of truth. `min/` is generated.
   `legacy-prebuild/` is a frozen baseline for `verify_rebuild.py` — never edit.
6. Commit often, push, keep `main` in sync. Trailer:
   `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`

---

## 1. State of play

Eight looms in `docs/harness/rebuild/`:

| File | Scope | Fate |
|---|---|---|
| `ST185-A-ECU` | ECU-A pins → bulkhead A | stays |
| `ST185-A-engine` | bulkhead A → engine bay | stays |
| `ST185-B-ECU` | ECU-B pins → bulkhead B | stays |
| `ST185-B-engine` | bulkhead B → engine bay | stays |
| `ST185-CAN` | CAN backbone | stays |
| `ST185-EngineRoom-C` | engine room, PDB, fuse blocks, relays, EPS, J/B injection | stays, grows |
| `ST185-ClusterLED` | cluster warning LEDs | **dissolves** into the new cabin-accessory loom |
| `ST185-WheelSpeed` | 4 ABS drops + both VR conditioners | **splits**: front → loom C, rear → new rear-trunk loom |

Pipeline (`check_all.py` runs all of it):
`lint_v09.py` → `verify_rebuild.py` → `audit_cavity_parts.py` →
`audit_shields.py` → `buylist.py` → `buildlist.py` → `make_min.py`
(plus `audit_bulkhead_pairs.py`, soft).

harness.design document ids: A-ECU `oOXY`, A-engine `5W0Y`, B-ECU `60VO`,
B-engine `7AJQ`, CAN `89Yj`, EngineRoom-C `nz65`, ClusterLED `wkRX`,
WheelSpeed `xl7P`.

---

## 2. Answers Daniel already gave — treat as settled

### 2.1 Sensor 5V / Gnd Out pass-through — CURRENT STATE IS WRONG

They exist, but **they cross on bulkhead A, not B**, and the splices are modelled
in the **B** files while carrying **loom A's** ECU pins:

| Splice | Lives in | Feeds |
|---|---|---|
| `sp_5v` | `ST185-B-ECU` | `ecu_a.a32` (+5V Out), `aps` c1/c4, **`bh_a_fw` c2** |
| `sp_gndout` | `ST185-B-ECU` | `ecu_a.a24`, `ecu_b.b22`, `aps` c2/c5, `fuellvl` c2, **`bh_a_fw` c3** |
| `sp_5v_eng` | `ST185-B-engine` | engine sensors + **`bh_a_eng` c2** |
| `sp_gndout_eng` | `ST185-B-engine` | engine sensors + **`bh_a_eng` c3** |

One 5V rail and one sensor-ground rail crossing once is electrically right — the
ECU has one +5V Out and one Gnd Out. What is wrong is **which file they live in**:
loom A pins are being wired inside loom B's document. Fix in Option C, §4.2.

### 2.2 Shield grounds — A AND B ARE CURRENTLY BRIDGED. FIX THIS.

`sp_shield_cab` in `ST185-A-ECU` feeds **both** `ecu_a.a7` **and** `ecu_b.b17`
from one splice. Daniel: *"Loom B has its own shield ground at ECU B, correct?
Don't bridge loom A and loom B shield grounds."* Correct intent, wrong file.
Fix in Option C, §4.1.

### 2.3 VSS — no voltage divider needed. Settled.

From Link's own installation manual (`G4Install.pdf`), Digital Input spec:

| | |
|---|---|
| Max input | **±50 V** |
| Low level | < 1 V |
| High level | > 2 V |
| Selectable pull-up | **4k7 to 12 V** (note: to 12 V, not 5 V) |

A 12 V VSS wires straight to a DI. **No divider, no series resistor.** Put this in
the harness note so it is not asked again. Still confirm what the E154F sensor
actually outputs (open-collector vs push-pull vs VR) before choosing the pull-up
setting — that is a tune setting, not a harness change.

### 2.4 Relay coil polarity — all active-LOW

Every relay in the build is driven on the **coil-negative** side by an ECU
low-side output, coil-positive on switched 12 V. So: **active-low, ground
activated**. Verified from the cavity signals in each file.

### 2.5 Anti-theft — the G4X can do it. Confirmed from Link documentation.

`docs/vendor/XtremeXPlugInECUSpecs.pdf` lists, verbatim:
- *"Anti-Theft control through digital inputs, over CAN or both"*
- *"AntiTheft - Via Digital Input, CAN or both"*

So the immobiliser is a G4X feature, not an add-on. Plan: keep the factory
keyless-entry ECU for door locks, and use the G4X anti-theft (fuel + ignition
cut) as the immobiliser, armed from a digital input or over CAN from the CSB3.

**Interaction to check before wiring:** the OEM anti-theft ECU may interrupt the
starter circuit. Our starter is now switched by `k_str`, driven by the Link on
Aux 8 / A26. Find out from the 1993 EWD whether the OEM system cuts STA, and
decide whether it stays in that path or is bypassed.

### 2.6 Deleted — remove from every harness file and from the buy list

| Deleted | Notes |
|---|---|
| Start injector time switch (S2) + cold start injector (C2) | takes the S2 internal diode with it, EWD p.48 |
| ABS controller / ECU | **wheel-speed sensors are KEPT** |
| ABS crash / deceleration sensors | |
| ABS solenoid / actuator / module | |
| Rear windshield wiper | |
| Automatic antenna | |
| OEM amplifier + radio harness | |

### 2.7 NO RELAYS OR FUSES IN THE ENGINE BAY

Everything moves to the cabin block near the main fuse box. This has a
consequence that must be resolved before the loom C rebuild — see §6.1.

---

## 3. What is still missing, and it blocks Option A

**The repo only has 1990 ST185 EWD snips** (`docs/electrical/ewd-snips/`, 20
images). Daniel's car needs the **1993** diagrams for:

- automatic (not manual) climate control — solar sensor, in-cabin temp sensors,
  ambient air temp sensor behind the front bumper, trinary A/C pressure switch
- factory anti-theft + keyless entry ECU
- power / heated / lumbar driver seat
- electric folding mirrors
- sliding moonroof
- pop-up headlight motors, wipers + washer, third brake light, tail / brake /
  reverse lighting

**Do not model any of these from memory.** Ask Daniel for the 1993 ST185 EWD
(body and A/C sections at minimum) and snip it into
`docs/electrical/ewd-snips-1993/` following the existing naming convention.
Until then those systems stay out of the harness files.

Also not yet read: `1990-st185-rb2-left-rb3-right.png`. Read it and add R/B2 and
R/B3 to the keep/remove table in §5.3.

---

## 4. OPTION C — do this now

Loom splits and the corrections that need no new source documents. **No relayout
in this pass** — Daniel reviews the structure first.

### 4.1 Split the shield grounds

In `ST185-A-ECU`:

- Rename `sp_shield_cab` → `sp_shield_a`; it keeps **only** `w_drain_ecu_a`
  (→ `ecu_a.a7`).
- Add `sp_shield_b` → `ecu_b.b17`.
- Re-assign each screen to the splice matching the ECU its signal lands on:

| Screen | Signal lands on | Splice |
|---|---|---|
| crank | Trig 1, A8 | `sp_shield_a` |
| cam | Trig 2, A9 | `sp_shield_a` |
| knock 1 | B9 | **`sp_shield_b`** |
| rear VRC output | B19 RR, B20 RL — both B | **`sp_shield_b`** |
| front VRC output | A23 FL **and** B21 FR — split across ECUs | **ASK DANIEL**, see below |

The front VR conditioner box has one output screen but its two signals land on
different ECU connectors. A screen gets exactly one termination (6.27 rule 2), so
pick one. Recommend `sp_shield_a` because FL on A23 is the reference wheel for
most speed logic — but confirm, do not assume.

- Update `docs/harness/audit_shields.py`: `ECU_SHIELD_PINS` stays the same, but
  add a check that no single splice reaches **both** a7 and b17.
- `ST185-WheelSpeed` has `dm_sp_shield_cab_Splice`; rename the dummies to match
  whichever real splice each one now points at.
- Also look at `w12_c` in `ST185-A-ECU`: `bh_a_fw.c6` → `ecu_a.a7`. Bulkhead c6 is
  labelled "ECU-A A7" and A7 is "Shield/Gnd". Work out what that wire actually is
  before the split, and say so in the commit.

### 4.2 Move the 5V / Gnd Out splices to the right file

`sp_5v` and `sp_gndout` carry `ecu_a.a32` and `ecu_a.a24` but live in
`ST185-B-ECU`. Move both splices and every wire on them into `ST185-A-ECU`,
leaving `dm_*` cross-reference dummies in `ST185-B-ECU` for `ecu_b.b22`,
`aps` and `fuellvl`. Same treatment for `sp_5v_eng` / `sp_gndout_eng`:
they feed `bh_a_eng`, so they belong in `ST185-A-engine`.

`verify_rebuild.py` will show these as `CHANGED` — add `EXPECT_CHANGED` entries
explaining the file move, not the net.

### 4.3 Relay descriptions — amps, active level, contact form

Every relay part description must carry the current rating, and every relay
**connector** must carry a note saying how it is driven and what contact form it
has. Verified data:

| Part | Form | Rating | Coil | Used by |
|---|---|---|---|---|
| `5-1393292-8` | 1 Form A, **N/O** | 25 A | 12 V, diode | `k_efi`, `k_fp` |
| `6-1419137-4` | 1 Form C, **changeover (N/O + N/C)** | 25 A | 12 V, diode | `k_fan`, `k_fan2` |
| `4-1904124-2` | 1 Form A, **N/O** | 25 A | 12 V, 119 Ω | `k_etb`, `k_str` |
| `V23132-A2001-B200` | HCR150 | **130 A** | 12 V, 37 Ω / 3.9 W, internal suppression | `k_eps` |

All are **ACTIVE-LOW (ground activated)** — the ECU pulls coil-negative, coil-positive
is on switched 12 V. Put that phrase, in those words, in every relay connector's
label or a per-relay schematic note, plus the amps and N/O or N/C. Daniel asked
for this explicitly.

### 4.4 Part descriptions must be sourceable

Every part description gets enough spec that Daniel can search for an
equivalent without opening the datasheet. Minimum by type:

| Type | Must state |
|---|---|
| Connector housing | cavity count, gender, series/family, seal type, keying, mating half |
| Contact | size, gauge range, current rating, pin or socket, plating |
| Relay | contact form, current rating, coil voltage and resistance, suppression |
| Cable / wire | AWG or mm², insulation type, shielded or not, temp rating |
| Fuse / breaker | rating, form factor (ANL / MIDI / MINI / blade) |
| Terminal / lug | stud size, wire size, ring or fork |

Sweep every `*Parts` array in all looms and fill the gaps. Where a spec is
unknown, write `TBD — need <the specific thing>`, never a plausible guess.

Daniel on alternates: he will ask in chat when he wants a cross-reference, so do
not build a lookup table into the repo. Just make the descriptions searchable.

### 4.5 Move every relay and fuse out of the engine bay

Currently in the bay and must move to the cabin block:

| Item | Where it is now | Was OEM |
|---|---|---|
| `k_eps` HCR150 | `ST185-EngineRoom-C`, labelled "engine bay" | new |
| `k_fan` uprated | `ST185-EngineRoom-C` | R/B5 / J/B2 |
| `k_fan2` uprated | `ST185-EngineRoom-C` | R/B5 / J/B2 |
| Fuel pump relay | R/B5 | R/B5 |
| Horn relay | R/B5 | R/B5 |
| A/C magnet clutch relay | R/B5 | R/B5 |
| A/C condenser fan relays No.2 and No.3 | R/B5 | R/B5 |

Re-label, re-position and re-route so the drawing shows the coil and the load
feed both originating in the cabin. **Read §6.1 first — this creates a real
problem that needs a decision before you can finish it.**

### 4.6 Create the two new looms

`ST185-CabinAccessory.harness`
- absorbs everything in `ST185-ClusterLED` (6 LEDs, `r_chg_excite`, `cl_c11`,
  `cl_c12`, both splices, both terminals, the OEM-filter schematic note)
- delete `ST185-ClusterLED.harness` once `verify_rebuild.py` is clean
- this is where the 1993 body systems will land in Option A

`ST185-RearTrunk.harness`
- rear VR conditioner (`vrc_r_inl`, `vrc_r_inr`, `vrc_r_out`) and the RL / RR
  sensor cables
- fuel level sender (OEM connector, both halves on hand)
- fuel pump on its own circuit and its own connector — the pump's own connector,
  12 in from the pump; Walbro F90000295 verified at **14.4 A @ 13.5 V** steady
  (Radium bench test), so size for that, not for inrush
- trunk battery positive and negative terminals
- joins the cabin on an **inline DT connector** (Daniel's choice, plan 6.41)

Front VR conditioner and the FL / FR sensor drops move into
`ST185-EngineRoom-C`. Then delete `ST185-WheelSpeed.harness`.

Keep every component id unchanged through the move so `verify_rebuild.py` can
still match them. Add the two new files to `F` in `buylist.py` and `buildlist.py`,
and to the file table in `docs/harness/README.md`.

### 4.7 Fix the four loom-crossing violations

`audit_bulkhead_pairs.py` reports exactly these four, and they are the last ones:

| Cavity | Carries | Fix |
|---|---|---|
| `bh_a_fw` c10 | ECU-A A23, wheel speed FL | branch at the ECU into loom C, do not enter bulkhead A |
| `bh_a_fw` c12 | ECU-B B21, wheel speed FR | same |
| `bh_b_fw` c13 | ECU-A A27, MRS speed pulse | branch at the ECU into loom C |
| `bh_b_fw` c14 | MRS EPS enable | same |

Rule (plan 6.41): the ECU pin decides loom membership, and anything going
somewhere other than loom A or loom B branches **at the ECU connector**, not at
the bulkhead. After this, `audit_bulkhead_pairs.py` should report **0**.

### 4.8 Remove the deleted systems

Sweep §2.6 out of every harness file, out of `buylist.py`'s `ONHAND` and `EXTRA`,
and out of the docs. Add `EXPECT_GONE` entries with the reason.

### 4.9 Add the J/B keep / remove note to the drawings

Daniel asked for this on the diagram, with FSM page references. Put it as a
`schematicNote` on `ST185-EngineRoom-C` **and** on the new cabin-accessory loom:

```
J/B AND RELAY BLOCK DISPOSITION - 1990 ST185 EWD

J/B No.1  left kick panel            KEEP  (EWD p.18 housing, p.19 inner circuit)
  fuses   15A ECU-IG, 20A WIPER, 15A GAUGE, 10A TURN, 7.5A IGN,
          15A CIG & RADIO, 15A STOP, 15A ECU-B, 15A TAIL, 30A DEFOGGER
  relays  Defogger, Taillight, Integration, Turn flasher
  NOTE    contains a 3-terminal DIODE (two diodes, common cathode on pin 2).
          Do not inject power in a way that bypasses or backfeeds it.

J/B No.2  engine bay                 REMOVE ENTIRELY  (EWD p.20, p.21)
  fuses   15A HEAD RH, 15A HEAD LH, 30A FL RDI FAN, 30A FL CDS FAN,
          30A RTR, 15A HAZ-HORN, 20A DOME, 15A EFI
  relays  Radiator Fan No.1, Headlight, Engine Main, EFI Main
  all of the above move to the cabin block

J/B No.3  behind combination meter   KEEP  (EWD p.22)
  no fuses, no relays - pure junction block

R/B No.4  right kick panel           KEEP - already in the cabin  (EWD p.24)
  Starter Relay (M/T), Heater Relay, FR FOG 20A, A/C 10A, 40A HEATER

R/B No.5  engine compartment fr right  REMOVE ENTIRELY  (EWD p.24)
  A/C Condenser Fan Relay No.2, Fuel Pump Relay, Horn Relay,
  A/C Magnet Clutch Relay, A/C Condenser Fan Relay No.3
  all move to the cabin block - NO RELAYS OR FUSES IN THE ENGINE BAY

R/B No.2 / R/B No.3  - NOT YET READ. See ewd-snips/1990-st185-rb2-left-rb3-right.png
```

Confirm the horn relay question is now closed: **the car already has one**, in
R/B No.5.

### 4.10 Add the VSS note

Schematic note on whichever loom carries the VSS:

```
VSS - NO VOLTAGE DIVIDER NEEDED
Link G4X digital inputs: max +/-50 V, low < 1 V, high > 2 V, selectable
4k7 pull-up to 12 V (G4Install.pdf). A 12 V VSS wires straight to a DI.
Still confirm the E154F sensor's output type before choosing the pull-up
setting - that is a tune setting, not a harness change.
```

### 4.11 Close out

- `python docs/harness/check_all.py` → `all checks passed`
- `audit_bulkhead_pairs.py` → 0 one-sided cavities
- regenerate `NEED-TO-BUY.md` and `HARNESS-BUILD-LIST.csv`
- mirror every changed loom to harness.design (ids in §1); `announce_editing`
  first, `validate_harness` after
- write a plan section 6.54 recording what changed and why
- commit, push, report to Daniel with the open items from §6

---

## 5. OPTION A — after Daniel reviews Option C

### 5.1 Prerequisite

The 1993 EWD, snipped into `docs/electrical/ewd-snips-1993/`. Nothing in this
section starts without it.

### 5.2 Body systems to add

Each one gets a row in `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` and lands
in a harness file. Daniel: *"Every circuit in the system that we are modifying
upgrading or replacing should be included in at least one harness file."*

| System | Likely loom | Notes |
|---|---|---|
| Windshield wipers + washer pump | cabin accessory + loom C | wiring fully replaced; 20A WIPER stays in J/B1 |
| Pop-up headlight motors | loom C | RTR 30A circuit; motors are in the bay, relay moves to the cabin |
| Third brake light | rear trunk | fully replaced |
| Tail / brake / reverse lighting | rear trunk | new wire throughout |
| Auto climate control (1993 type) | cabin accessory | solar sensor, in-cabin temp sensors, blower, servos — **1993 diagram only** |
| Trinary A/C pressure switch | loom C | OEM part, feeds A/C amp and condenser fans |
| Ambient air temp sensor, behind front bumper | loom C, terminating in cabin accessory | Daniel's guess is climate control; confirm from the 1993 diagram |
| A/C magnet clutch | loom C, relay in cabin | |
| Electric folding mirrors | cabin accessory | |
| Power / heated / lumbar driver seat | cabin accessory | heated seat is a real current draw — size it |
| Sliding moonroof | cabin accessory | |
| Keyless entry + anti-theft ECU | cabin accessory | see §2.5 on the starter interaction |

### 5.3 Then

- full layout pass on all looms (`layout_633.py`, `layout_room_c.py`, and a new
  one for each new loom) — orthogonal routing, notes close to what they annotate,
  nothing spread out
- take a new `verify_rebuild.py` baseline and retire `legacy-prebuild/`
- refresh `docs/harness/README.md` and `PROJECT_INDEX.md`

---

## 6. Open items — decisions Daniel has to make

1. **Front VR conditioner screen** — its two signals land on different ECU
   connectors (A23 FL, B21 FR) but a screen gets one termination. `sp_shield_a`
   or `sp_shield_b`? (§4.1)
2. **BLOCKER — how do the big engine-bay loads cross the firewall now that no
   relay may live in the bay?** Rad fan (~40 A), condenser fan (~30 A), EPS pump
   (60 A circuit), headlights, horn, A/C clutch all now run switched 12 V from
   the cabin. Bulkhead B is HDP20 size 24 with size-12 (25 A) and size-16 (13 A)
   cavities — the fan and the EPS will not fit. Options: a second RADLOK-class
   crossing for the heavy loads; doubled size-12 pairs; or a separate
   high-current feed-through. **Needs a decision before loom C can be finished.**
3. **1993 EWD** — needed for everything in §5. (§3)
4. **OEM anti-theft vs the starter circuit** — does the factory system cut STA?
   Our starter runs through `k_str` on Aux 8 / A26 now. (§2.5)
5. **`r_chg_excite` value** — 56 Ω 5 W is the bulb-equivalent starting point;
   confirm against the fitted alternator.
6. **E154F VSS output type** — open-collector, push-pull or VR? Decides the DI
   pull-up setting, not the wiring. (§2.3)
7. **`bh_a_fw` c6 → `ecu_a.a7`** — what is this wire actually for? (§4.1)
8. **Glass-break alarm replacement** — Daniel asked for affordable options; see
   the chat message that accompanied this handoff.
9. **Cluster connector face pinout** (`cl_c11`, `cl_c12`) — still unknown, needed
   before the cabin-accessory loom is buildable.
10. **12–16 way second fuse block** — still not chosen (plan 6.48).
11. **Master cutoff with an alternator-excite terminal** — still not specified.
