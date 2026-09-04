# CAN Config Status — handoff note (2026-07-04)

Quick snapshot so a new chat can pick up the ECU / RealDash CAN config without re-deriving everything.

## Single source of truth
The authoritative ECU↔cluster CAN definitions (external Link CAN Lambda, the cluster **receive**
channels 0x3E8–0x3EE, and the cluster **send** channels 0x3EC/0x3ED) come from
`center-cluster-esp32-p4/CANBUS-ENCODE-DECODE-REFERENCE.html` (derived from the cluster firmware
`main/canbus.c`). This repo's config files are reconciled to match it.

## Which repos are in use
- **ECU + RealDash config:** `C:\projects\st185-link-ecu-config` (this repo). Holds `link_g4x_can_setup.json` (ECU send config), `link_g4x_can_setup.lcs` (PCLink import), `link_g4x_realdash.xml` (RealDash receive), and `CAN-BUS-ID-ALLOCATION-TABLE.md` (master map).
- **Center cluster firmware:** `C:\projects\center-cluster-esp32-p4` (GitHub: [living-relation/center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4)). Decodes the ECU frames; holds the source-of-truth HTML plus `main/protocols/link_g4x.json`.

## What was reconciled (2026-07-04)
1. **Boost = MAP, not MGP.** `0x3E8` bytes 2-3 are the ECU's **MAP** (absolute) channel — matches the source-of-truth HTML in `link_g4x_can_setup.json` **and** `link_g4x_can_setup.lcs`. (MGP would read ~−14 psi at idle.)
2. **`0x3E9` oil & fuel pressure are 2 bytes (u16).** Layout: ign 0-1, speed 2, **oil 3-4**, **fuel 5-6**, byte 7 free. (1 byte capped at ~37 psi; gauges need 125/160 psi.) The cluster firmware (`main/canbus.c`, per the HTML) already decodes this 2-byte layout.
3. **`0x3F0` coolant pressure is 2 bytes (u16)** (bytes 2-3). To make room (frame was full at 8 bytes), the optional **Cabin Temp** byte was dropped; **Trigger Error Count** is kept (byte 7).

## Corrected 2026-09-04: Turbo Speed scaling in the rd-build package
`rd-build/link_g4x_realdash.xml` (and its copy embedded in `rd-build/PLAN.md`) had Turbo Speed as
`conversion="V*100" rangeMax="200000"` — internally inconsistent (a single byte maxes at 25,500 at
that scale, never 200,000) and disagreed with every other source. Verified against the canonical
config, `link_g4x_can_setup.json` (`scale: 1000`, "raw x 1000 = RPM"), plus
`CAN-BUS-ID-ALLOCATION-TABLE.md` and `REALDASH-LAYOUT.md`, which both independently state
x1000/0-255,000 RPM — matching this repo's root `link_g4x_realdash.xml` all along. Corrected the
rd-build copy to `V*1000`/`255000` to match. If a `.rd` file was already built from the old rd-build
package, re-import the corrected channel file before trusting turbo-speed readings on it.

## RealDash receives (ECU echoes only)
`0x3EF` drive assist/status, `0x3F0` extended sensors, `0x3F1` IMU + warnings. Bind gauges to the
`ST185:` input names in `link_g4x_realdash.xml`. RealDash does **not** read `0x3E8–0x3EE` (the cluster
shows those) and does **not** read the switchboard `0x640–0x642` frames directly — the ECU echoes the
few display-relevant switchboard values (TC echo, boost echo, comm-fault bit) into `0x3EF`/`0x3F1`.

**One deliberate exception, added 2026-09-04:** RealDash also reads the Gear byte of `0x3EB`
(`ST185: Gear`), as a passive second listener on the same frame the cluster already uses. This exists
solely to drive a reverse-camera auto-switch on the Pi5/RealDash display when Gear=7(R) — the reverse
switch itself is wired to the ECUMaster switchboard, not an ECU DI (`XTREMEX-IO-TABLE.html`), and the
ECU sets Gear=7 on 0x3EB via a PCLink **Trigger** condition. No other byte of `0x3E8–0x3EE` is exposed
to RealDash; Fuel Level (`0x3EB` byte 1) is intentionally left out to keep this carve-out minimal.

## Cabin temp
Cabin temp is **no longer available via the ST185 RealDash inputs** — it was dropped from `0x3F0` and
RealDash does not read `0x640` directly. To restore it, add a new frame `0x3F2` (ECU broadcast) with a
matching RealDash frame/value; do not point RealDash at `0x640`.

## Open items
- **ECU startup/base map:** not yet designed (Link G4X **XtremeX**, wire-in). Planned as a separate chat.
- RealDash UI/dashboard layout still being built (`REALDASH-LAYOUT.md`).
