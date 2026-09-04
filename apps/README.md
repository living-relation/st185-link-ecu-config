# apps/

Bench-test tooling for the **RealDash** secondary display. **Not part of any firmware build** —
a standalone helper for driving RealDash on the bench without the car's ECU. It fakes
the three ECU→RealDash frames (**0x3EF / 0x3F0 / 0x3F1**), so RealDash sees exactly what it would
on the real bus. Signal math comes from
[`../link_g4x_can_setup.json`](../link_g4x_can_setup.json) (authoritative encodings) and
[`../link_g4x_realdash.xml`](../link_g4x_realdash.xml) (input names / enums), and the gauge names
match [`../REALDASH-LAYOUT.md`](../REALDASH-LAYOUT.md).

> Modeled on the center cluster's `apps/` tooling
> (`living-relation/center-cluster-esp32-p4`), retargeted from the cluster's frames (0x3E8–0x3EE)
> to RealDash's frames (0x3EF–0x3F1). RealDash is a passive listener, so these are the only three
> frames it decodes.

| App | What it is | How to run |
|---|---|---|
| `harness-schematic/` | Dark schematic canvas (harness.design-style). ST185 devices pre-placed; drag pin-to-pin to finish unwired parts. | Open `harness-schematic/index.html`, or `python3 -m http.server` and browse to the folder. |
| `trackcluster-can-sender/` | Unified desktop app (pywebview + python-can) with a **device selector** — transmits either the RealDash (0x3EF–0x3F1) or Center Cluster (0x3E8–0x3EE) frame set to a connected CAN-USB adapter. Auto-detects adapters, selectable bitrate, Send Once / Send Continuously. Fully self-contained / portable. | See `trackcluster-can-sender/BUILD.md` — run from source or build a portable `.exe`. |

## Frame coverage

| Frame | Period | Signals |
|---|---|---|
| `0x3EF` | 50 ms | Target λ, Throttle, TC setting/intervention, Boost map, Cruise, A/C |
| `0x3F0` | 100 ms | Fuel/Charge-IAT temps, Engine load, Coolant P (u16), Ethanol, Turbo speed, Trigger errors |
| `0x3F1` | 50 ms | G-force X/Y/Z (signed) + 6 extended warning bits packed in byte 6 |

Bus is 1 Mbit/s, standard 11-bit IDs, DLC 8, **big-endian** — the same settings RealDash's
CAN connection uses.

## Related

- `../realdash-simulation.html` — a preview of the RealDash *display itself* (what these frames
  drive). Use the sender app to transmit frames; use the simulation to see the layout.
- `../BENCH-TEST.md` / `../bench/` — a separate command-line bench harness for the whole 4-node
  bus (cluster + RealDash). These `apps/` tools are the browser/desktop, RealDash-focused
  equivalent of the center cluster's own `apps/` tooling.
