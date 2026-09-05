<!-- ══════════════════════════════════════════════════════════════════════
     RETIRED 2026-09-05 — DO NOT APPLY TO THE ECU.
     Why: this 0x3EE alarm-mapping policy ("never duplicate gauge-shown
     conditions as alarm bytes") was a temporary constraint used while the
     cluster layouts were being designed. It does not describe ECU behaviour.
     Kept only as history, in case the question resurfaces.
     Authoritative for the 0x3EE byte layout: CAN-BUS-ID-ALLOCATION-TABLE.md
     ══════════════════════════════════════════════════════════════════════ -->

<!-- Imported 2026-09-05 from st185-furyx-base-map (config/can/ALARM_CAN_SPEC.md).
     SCOPE: this is the PCLink-side *mapping policy* — which Link protection channels feed
     which 0x3EE alarm byte, and which conditions must never become alarm bytes.
     The authoritative 0x3EE byte layout / wire contract is CAN-BUS-ID-ALLOCATION-TABLE.md
     (mirrored from the frozen cluster firmware). If the two ever disagree, that file wins. -->
# CAN alarm spec — ECU → cluster (authoritative)

**Cluster leads.** Mirror `link_g4x_can_setup.lcs` / `.json` from `center-cluster-esp32-p4` exactly.

## TX streams

| ID | Purpose |
|----|---------|
| 0x3E8–0x3EB | Sensor **values** (incl. oil press, ECT, fuel press on 0x3E9) |
| 0x3EE | Protection **outcomes** — bytes **0–5 only** |

Values and colors stay on 0x3E8–0x3EB + local cluster UI. **Never** duplicate pressure/temp conditions as extra alarm bytes.

## 0x3EE bytes 0–5

Each byte: **0 = OK**, **nonzero = active**. Map from Link **cut / knock / fault / ETB error** channels — not from raw oil PSI or coolant °F.

| Byte | Red box | PCLink source (examples) |
|------|---------|--------------------------|
| 0 | KNOCK | Knock level / knock limit |
| 1 | IGN CUT | Ignition cut % (any cause except intentional TC — see below) |
| 2 | FUEL CUT | Fuel cut % (any cause except intentional TC) |
| 3 | BOOST CUT | Boost cut / overboost limit (any cause except intentional TC) |
| 4 | SENSOR ERR | Fault code / sensor failed / improbable value |
| 5 | THROTTLE ERR | TPS/ETB deviation warning (before hard cut) |

### Causes are not labels

One byte can reflect many underlying limits. Examples:

- **BOOST CUT** — overboost, knock strategy, high IAT, low fuel pressure, low oil pressure, etc., depending on Link tune.
- **FUEL CUT / IGN CUT** — ECT limit (engine off), oil pressure limit, protection strategies.
- **KNOCK** — knock only; may cascade to other cuts in ECU without extra CAN channels.

### Never on 0x3EE (or red box text)

Oil pressure low, coolant hot, coolant pressure spike, fuel pressure low, IAT hot, lambda, fuel low, oil temp, separate overboost message, rev limit as its own alarm.

### Rev limit

Not a driver warning flag. Do not add a “REV LIMIT” cluster string or CAN byte.

### Traction control

When TC is actively controlling slip, assert **TC orange UI** only (when implemented). **Suppress** ign/fuel/boost cut bytes for **intentional** TC actions so the red overlay does not flash during normal TC.

## RX

| ID | Purpose |
|----|---------|
| 0x3EC | Boost map index |
| 0x3ED | TC slip angle index |

## Link limits (base tune) — ECU acts, cluster shows cuts

| Limit type | Cluster red box | ECU action |
|------------|-----------------|------------|
| Knock | KNOCK (+ maybe cuts) | Retard / cut per strategy |
| Boost / overboost | BOOST CUT | Cut boost |
| Oil pressure minimum | FUEL/IGN CUT if limit cuts engine | Cut — **no** “oil low” byte |
| ECT maximum | FUEL/IGN CUT | Engine off — **no** “coolant hot” byte |
| Coolant pressure | FUEL/IGN CUT or log only | As programmed — **no** dedicated byte |
| Fuel pressure minimum | BOOST/FUEL CUT as strategy dictates | As programmed |
| Oil temp | Arc color only | **No** Link limit for dash |
| Lambda | Widget color | **No** Link limit for dash |
| Fuel level | Arc + lamp | **Never** |
| ETB deviation | THROTTLE ERR then cut | Warning then engine off |

Setpoints: `config/limits.yaml` → `ecu_limits` (**loose for v1**). See `docs/LIMITS_STARTUP_VS_TUNED.md`.

Import: PCLink → CAN → Setup → `config/can/link_g4x_can_setup.lcs`.
