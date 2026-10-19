# Circuit tracer - approved plan (not built yet)

Dan, 2026-10-14 (planning session, decisions via chat): "after every harness file is
finalized, create a special skill that can trace each circuit from end to end, through all
devices and nodes, to verify continuity, current flow, and operation in active and inactive
states, with simulated ECU logic for sent and received signals."

**Status: plan approved, build NOT started.** Tracker: `docs/OPEN-ITEMS.md` row 117. The
binding numbers (margins, derating, how findings are handled) are DECISIONS **R89**; this
page is the build brief for the session that runs it.

## When and who runs it

1. Wait until all 15 `docs/harness/rebuild/*.harness` files are final and the repo is clean.
2. Dan tells Dispatch "run the circuit tracer plan". Dispatch starts **one Opus session** on
   this page. One session, not one per harness: the tracer is one graph across every file
   (the brake circuit alone crosses RearLights, CSB3, CabinPower and the ECU looms), so no
   single harness can be traced alone.
3. After the build, the first report is split by harness and **2-3 Sonnet sessions at a
   time** fix drawings (never 15 at once: they all touch `sot/channels.csv` and
   `ST185.harnesslib`, one writer per path). Each finding goes to Dan as A/B/C first.

## What already exists (reuse, do not duplicate)

- `docs/harness/model.py` `Graph` already joins all 15 files into one electrical graph
  (bulkhead halves, inline interface halves, break-offs, VRC enclosures collapse to one node)
  with `reach()` and `path()`. **The tracer is built on this.**
- `verify_connectivity.py` proves each ECU signal pin reaches a labelled far end (C1-C4). The
  tracer goes further (full loop to ground, the power side, both states) and does not re-check
  C1-C4.
- `sot/channels.csv` columns `dir`, `type` (`lowside-sat`, `freq-di`, `switch-12v`, ...) and
  `pullup` (`none` / `int-1k5` / `sel-4k7-to-12v` / `off`) are the ECU behaviour model input.
- `switchboard_frames.json` `ecu_receive` + `link_g4x_can_setup.lcs`: CSB3 bit -> ECU VDI
  (e.g. 0x642 byte 4 bit 6 -> VDI7). `bench/frames.py` encodes / decodes frames: reuse it.
- `cad/fusebox/src/spec.py`: fuse labels and amps (`MINI_COLS`, `AMI_ROWS`), relay types.
- `docs/harness/wirelist/*-wirelist.csv`: every wire with its AWG and `est_length_mm` (the wiring SoT, R206); the load -> fuse path is the CabinPower list plus `cad/fusebox/rev7/wiring_plan.json`; **most load currents are TBD**.

## Deliverables

1. `docs/harness/trace_circuits.py` - the tracer (a test, lives in the repo).
2. `docs/harness/circuits.yaml` - loads in amps (datasheet / estimated, see R89), ECU / CSB3
   logic rules, the circuit list.
3. `docs/harness/CIRCUIT-TRACE.md` - generated report, `--check` mode like `wirelist.py`.
4. `check_all.py` entry, **SOFT** first, HARD the day it reads zero (the standing gate rule);
   self-tests in `test_gates.py` (a loop that passes, an open, an oversized fuse, a floating
   input - each must give the right finding).
5. A "Circuit trace" section on the research hub (`docs/build-research-hub.py` reads the MD).
6. Global skill `C:\Users\danie\.claude\skills\st185-trace-circuits\SKILL.md` (skill-creator
   structure; pointer in `AGENTS.md` "Skills").

## What a circuit is

Source -> protection -> switching -> conductors -> load -> return.

- Source: battery B+, IG / ACC rail, ECU output pin, sensor +5V, CSB3 output.
- Protection: fuse (rating from `spec.py`) or fusible link.
- Switching: relay contact (its coil is another circuit), switch, optoisolator, ECU low-side.
- Conductors: every wire, splice, bulkhead pin and inline mate, across files.
- Load: device plug cavity, flying lead or endpoint lead.
- Return: ground stud, ECU ground, sensor Gnd Out.

A signal circuit adds a **logic leg**: input pin -> threshold / pull-up -> (CSB3 -> CAN bit)
-> ECU virtual input -> ECU output -> that output's own power circuit.

## Checks per circuit

| ID | Check |
|---|---|
| T1 | Closed loop: source reaches the load AND the load reaches its return (no open) |
| T2 | No short: a net never touches a rail or ground it should not (B+ to Gnd, 12 V on a 5 V net) |
| T3 | Fuse protects the wire: fuse A <= derated ampacity of the thinnest wire after it |
| T4 | Fuse vs load: load A x margin < fuse A; `est` when the load is estimated |
| T5 | Voltage drop over length at load current: <= 3 % power, <= 1 % sensor; `assumed` lengths flagged |
| T6 | Relay logic: the coil circuit closes when its driver is ON; the contact feeds the load only then |
| T7 | Active state: driver ON -> load sees ~12 V / input reads ACTIVE |
| T8 | Inactive state: driver OFF -> load 0 V / input reads INACTIVE; no floating input |
| T9 | Logic chain: switch -> opto -> CSB3 input -> CAN frame bit -> ECU VDI agrees with the `.lcs` and `switchboard_frames.json` (via `bench/frames.py`) |

## Simulation (on / off state model, no PWM, no SPICE)

- Every node has a state: `12V`, `5V`, `GND`, `FLOAT`. Switches, relays and outputs flip edges.
- ECU outputs by SoT `type`: low-side pulls to GND when ON and is open when OFF; hi/lo
  drives 12 V or GND.
- ECU inputs by SoT `type` + `pullup`: ACTIVE / INACTIVE from the threshold; a FLOAT on an
  input with pull-up `off` and no pull-down is a finding.
- Opto: input side lit -> output transistor closes to its VCC (CSB3 +5 V).
- CSB3: input active -> sets its bit in 0x642 -> encoded with `bench/frames.py` -> decoded
  on the ECU side through the `.lcs` receive channel -> VDI value.
- Currents: Ohm's law, copper resistance per AWG x length, the load as fixed amps.

## Numbers (binding, DECISIONS R89)

- Unknown load: estimated from a similar part, inrush x3 for motors and lamps, hot engine
  bay, marked `est`; x1.25 margin.
- Missing length: route default (3 m engine bay, 5 m rear, 2 m cabin) x1.2, marked `assumed`.
- Ampacity: SAE J1128 at 85 C, x0.8 in the engine bay, x0.7 in a bundle of 10+ wires.
- Drop limits: 3 % power, 1 % sensor.

## Report

`docs/harness/CIRCUIT-TRACE.md`: one table row per circuit (ID, name, T1-T9 pass / fail /
est, worst finding), then a readable trace per circuit, both states:

```
BRAKE  [PASS T1 T7 T8 T9 | est T4 load]
 ACTIVE (pedal down):
  J/B1 STOP 15A -> S9 pin 1 12V -> RearLights ... -> CSB3 plug opto IN1 lit
  -> opto OUT1 = 5V -> CSB3 S7 ACTIVE -> 0x642 byte 4 bit 6 = 1 -> ECU VDI7 = 1 (cruise cancel)
  -> brake lamps 12V, return body ground. Drop 0.21 V (1.7 %).
 INACTIVE: S9 open -> IN1 dark -> S7 INACTIVE -> bit 6 = 0 -> VDI7 = 0. Lamps 0 V.
```

## Findings

A FAIL or `est` is never logged silently: the skill puts it to Dan at once as A/B/C
(recommended marked), then prints a short paste block for Dispatch. `docs/OPEN-ITEMS.md`
rows only for what Dan defers.

## Delivery: 4 PRs, each via `st185-ship-change`

1. `trace_circuits.py` + `circuits.yaml` + `CIRCUIT-TRACE.md`; the brake chain traces PASS
   in both states.
2. `check_all.py` SOFT gate + `test_gates.py` self-tests + `AGENTS.md` map line.
3. Research-hub "Circuit trace" section.
4. The global skill (+ `AGENTS.md` Skills list) + the findings walk-through with Dan.

Effort about one session (4-6 h): tracer + state model 2 h, CAN / CSB3 leg 1 h, loads + fuse
data 1 h, report + gate + skill 1 h, run on all 15 files 1 h.

## Verification

1. `test_gates.py` self-tests give the right finding for each fake circuit.
2. Run on all 15 files; the brake chain (S9 -> opto -> S7 -> 0x642 bit 6 -> VDI7) is PASS in
   both states.
3. `python docs/harness/check_all.py` and `python bench/check_parity.py` green.
