# apps/

Bench-test tooling for the **RealDash** secondary display. **Not part of any firmware build** —
these are standalone helpers for driving RealDash on the bench without the car's ECU. Both fake
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
| `canbus-bench-test.html` | Browser-only tool. Pick a gauge, type the value it should show, copy the computed 8-byte CAN frame into CANgaroo / PCAN-View / SavvyCAN. No hardware access. | Double-click the file — opens in any browser. Works on desktop and mobile. |
| `canbus-live-sender/` | Desktop app (pywebview + python-can) with the same UI, but it actually transmits to a connected CAN-USB adapter (candleLight/gs_usb or slcan), including Send Once / Send Continuously. | See `canbus-live-sender/BUILD.md` — run from source or build a standalone `.exe`. |

The two tools deliberately keep **separate copies** of the signal map;
`canbus-live-sender` never modifies `canbus-bench-test.html`.

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
  drive). Use the bench tools to craft/transmit frames; use the simulation to see the layout.
- `../BENCH-TEST.md` / `../bench/` — a separate command-line bench harness for the whole 4-node
  bus (cluster + RealDash). These `apps/` tools are the browser/desktop, RealDash-focused
  equivalent of the center cluster's own `apps/` tooling.
