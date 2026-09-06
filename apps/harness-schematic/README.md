# ST185 harness schematic

Standalone browser schematic editor for the Celica GT-Four ST185 / Link G4X XtremeX build. Dark canvas, connector blocks with numbered pins, orthogonal wires, drag pin-to-pin, right-click to add parts.

Open `index.html` in a browser, or from the repo root run `python3 -m http.server` and browse to `apps/harness-schematic/`.

## Reading the sheet

Signal flows **left to right**, the way schematics are normally drawn:

| Zone | Contents |
|---|---|
| Far left | Sensors and switches (inputs) |
| Middle | XtremeX **Connector A** over **Connector B** |
| Right | Injectors, coils, ETB, relays (outputs) |
| Band 2 | CAN bus at 1 Mbit/s, clusters, RealDash |
| Band 3 | Body and switchboard parts, still unwired |

Solid wires are assigned in `XTREMEX-IO-TABLE.html` and `WIRING.md`. **Dashed** wires are proposed Link-capable assignments, not confirmed on the car.

## Keeping it readable

The full harness is ~175 connections. Four things stop that turning into spaghetti:

**Power drawn as symbols.** 12 V, 5 V and GND end in a small rail symbol at the pin instead of a long wire to one splice — standard schematic practice, and it removes 84 of the 175 wires. Ground points down, supplies point up. Untick *Power as symbols* to see them as real wires.

**Layers.** Every part belongs to a functional layer (ECU, engine sensors, injection & ignition, drive-by-wire, power & relays, CAN bus, clusters, body, proposed). Untick one to hide it, or hover a layer and hit **only** to isolate it. Callout notes travel with the layer they describe, and empty zones disappear so an isolated layer fills the screen.

**Focus.** Click any part and everything it does not touch fades out. The bar at the top of the canvas clears it, as does clicking empty canvas or pressing `Esc`.

**Spacing.** The header **Spacing** control (100 %–230 %) pushes blocks further apart without resizing them. Wires sharing a vertical channel are auto-assigned parallel lanes so they never sit on top of each other.

## Controls

| Action | How |
|---|---|
| Pan | drag empty canvas |
| Zoom | mouse wheel, or the +/− in the footer |
| Frame the sheet | **Fit width** (default) or **Fit all** |
| Hide the side panels | **Wide canvas** |
| Isolate a layer | **only** on a layer row |
| Focus one part | click it, or press `f` |
| Move a part | drag the block |
| Draw a wire | drag from one pin handle to another |
| Add a part | right-click canvas, or the left library |
| Delete | select, then `Delete` |

Wire labels are off by default; tick **Wire labels** to show them all, or select a single wire to see just its own.

Edits autosave in `localStorage` (`st185-harness-v6`). **Reset ST185** reloads the seed. Export JSON or SVG from the header.

Layout view is a placeholder until bundle lengths exist.

## Connector notes

The ECU is two 34-way Superseal looms, **Connector A** (A1–A34) and **Connector B** (B1–B34), numbered from the G4X XtremeX Quickstart (wire side). **B14** is the only empty cavity — no terminal. A6 +8V Out, B1–B4, B10–B11, B27–B28 and B31–B32 are spare terminals with no wire on this build.

The ECUMaster CSB3 V3 has **no I/O harness connector yet**. It appears as a CAN node with PCB screw terminals only. Cabin temp, brake, reverse, cruise, AC request and evap sit in band 3 with no wires and no invented connector in between.

The Waveshare MCP2515 hat takes Pi header 5 V / GND for its fan. **Its CANH/CANL stay open** — it is not a bus node.

## Sources

- `XTREMEX-IO-TABLE.html` — ECU I/O (DBW Bosch 74.5 mm ETB, 1ZZ COP, flex sensor, MRS EPS)
- G4X XtremeX Quickstart — Connector A / B Superseal pin numbers, wire side
- `WIRING.md` — cluster GPIO, 5 V buck, UART, CAN transceiver
- `ECUMASTER_SWITCHBOARD_SETUP.md` — CSB3 analog / switch map
- `CAN-BUS-MASTER-DESIGN.md` — 4-node 1 Mbit/s bus, termination
