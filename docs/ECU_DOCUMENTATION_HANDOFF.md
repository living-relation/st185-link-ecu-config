# Handoff: ECU / RealDash documentation corrections

## Scope
Work only in `C:\projects\st185-link-ecu-config` unless a source-of-truth check requires reading the cluster firmware repository. Do not change firmware, ECU tune files, or hardware settings as part of this task.

## Findings to correct

### 1. CAN allocation table: incorrect free-byte note
File: `CAN-BUS-ID-ALLOCATION-TABLE.md`

The `0x3E9 — Speed / Press / Ign` table is correct:
- bytes 0–1: Ignition Angle
- byte 2: Vehicle Speed
- bytes 3–4: Oil Pressure
- bytes 5–6: Fuel Pressure
- byte 7: free

However, the later free-byte summary currently says:
`0x3E9 bytes5-7`

Correct it to:
`0x3E9 byte7`

Recalculate the stated total free bytes if necessary. The current total should be reduced by two bytes because bytes 5–6 are occupied by Fuel Pressure.

### 2. Bench test document: stale cabin-temperature claim
File: `BENCH-TEST.md`, around the decoding table near the temperature row.

It currently lists:
`Temperatures (ECT, IAT, oil, fuel, cabin, charge-pipe)`

This conflicts with the current CAN contract:
- `0x3F0` uses bytes 2–3 for 2-byte Coolant Pressure.
- Cabin Temperature was removed from the ST185 RealDash inputs.
- RealDash must not read the switchboard `0x640` frame directly.
- To restore cabin temperature, allocate a new ECU broadcast frame such as `0x3F2` with a matching RealDash definition.

Update the bench-test documentation so cabin temperature is not presented as an available ST185 RealDash value. Suggested replacement:
`Temperatures (ECT, IAT, oil, fuel, charge-pipe)`

Add a short note that cabin temperature is currently unavailable through the ST185 RealDash input contract and would require a new ECU frame.

## Verify before editing
Use these files as the current references:
- `CAN-BUS-ID-ALLOCATION-TABLE.md`
- `CAN-CONFIG-STATUS.md`
- `REALDASH-LAYOUT.md`
- `link_g4x_can_setup.json`
- `link_g4x_realdash.xml`
- `BENCH-TEST.md`

Preserve the existing decisions:
- MAP, not MGP, on `0x3E8` bytes 2–3.
- Oil pressure on `0x3E9` bytes 3–4, uint16 big-endian.
- Fuel pressure on `0x3E9` bytes 5–6, uint16 big-endian.
- Coolant pressure on `0x3F0` bytes 2–3, uint16 big-endian.
- Turbo speed raw ×1000, range 0–255,000 RPM.
- RealDash receives the ECU-owned `0x3EF`–`0x3F1` frames and does not directly read switchboard `0x640`–`0x642`.

## Deliverable
Make the two ECU documentation corrections, then show:
- exact files changed;
- before/after wording for each correction;
- confirmation that no firmware, cluster, or tune files were changed.
