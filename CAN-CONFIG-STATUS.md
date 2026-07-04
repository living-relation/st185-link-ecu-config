# CAN Config Status — handoff note (2026-06-28)

Quick snapshot so a new chat can pick up the ECU / RealDash CAN config without re-deriving everything.

## Which repos are in use
- **ECU + RealDash config:** `C:\projects\st185-link-ecu-config` (this repo). Holds `link_g4x_can_setup.json` (ECU send config), `link_g4x_realdash.xml` (RealDash receive), and `CAN-BUS-ID-ALLOCATION-TABLE.md` (master map).
- **Center cluster firmware:** `C:\projects\center-cluster-esp32-p4`. Decodes the ECU frames; has its own copy of `link_g4x_can_setup.json` + `main/protocols/link_g4x.json`.
- **Stale / not needed:** `C:\projects\copilot-worktrees\st185-link-ecu-config` — old GitHub Copilot experiment copies, missing the RealDash frames. Do not edit; use this repo instead.

## What changed on 2026-06-28
1. **Boost = MAP, not MGP.** `0x3E8` bytes 2-3 must be the ECU's **MAP** (absolute) channel. (MGP would read ~−14 psi at idle.)
2. **`0x3E9` oil & fuel pressure widened 1 → 2 bytes.** New layout: ign 0-1, speed 2, **oil 3-4**, **fuel 5-6**, byte 7 free. (1 byte capped at 37 psi; gauges need 125/160 psi.) **Center cluster must be reflashed** for this.
3. **`0x3F0` coolant pressure widened 1 → 2 bytes** (bytes 2-3). To make room (frame was full), the optional **Cabin Temp** byte was dropped — RealDash can read cabin temp from switchboard `0x640` directly. To keep cabin temp instead: drop Trigger Errors, or add a new frame `0x3F2`.

## RealDash receives (ECU echoes only)
`0x3EF` drive assist/status, `0x3F0` extended sensors, `0x3F1` IMU + warnings. Bind gauges to the `ST185:` input names in `link_g4x_realdash.xml`. RealDash does **not** read `0x3E8–0x3EE` (the cluster shows those) or the switchboard directly.

## Open items
- **Ignition scaling offset (100 vs 1000):** unresolved — depends on whether the G4X applies the Offset before or after the multiply. Affects only the number typed into PCLink for ignition; does not affect byte positions. Verify with PCLink's CAN test calculator when the ECU is in hand.
- **ECU startup/base map:** not yet designed (Link G4X **XtremeX**, not purchased yet). Planned as a separate chat.
- RealDash UI/dashboard layout still being built (`REALDASH-LAYOUT.md`).
