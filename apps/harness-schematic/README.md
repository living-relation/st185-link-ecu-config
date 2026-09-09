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

**Zoomed-out names.** At 70 % zoom and below the in-block text stops being legible, so each component's name is mirrored in a label 2.5 × larger floating above its block. They disappear again above 70 %.

## Component library

The left panel is a searchable library of preconfigured blocks. Every part the ST185 seed uses is in it, alongside generic primitives (connector, splice, resistor, relay, sensors, CAN node, note). Each entry carries a manufacturer, part/model number, description, pin list and an optional thumbnail; entries without an image get a neutral placeholder.

Typing filters on part number, model, manufacturer and description, sorted best match first. **+ Add component** creates an entry by hand — name, manufacturer, PN, kind, description, pins as `number, label, side`, plus an optional image. Malformed pin lines are reported rather than silently accepted.

Clicking an entry places it at the centre of the view. **Show mating connector** also drops the assigned mate next to it; with no mate assigned the checkbox does nothing.

Library entries are templates. Placing one copies its data onto the new part, so editing the library afterwards never rewrites anything already on the canvas. User entries and edits persist under `st185-harness-lib-v1`, separately from the schematic.

## Research helper

**Find more…** next to the library search starts a lookup using whatever is in the search box. It opens a confirmation dialog first and will not run on vague input: a subject of at least three characters, a component type, and either a manufacturer or an exact part number are all required, so a bare "ECU" is refused with an explanation rather than a guess.

A result is shown as **unverified** for review — part number, description, pins, the mating connector, and that mate's accessories tagged required or optional. Nothing reaches the library until you accept it, and accepted entries are marked unverified in their notes. Not-found, ambiguous and backend-error outcomes all say so plainly and add nothing.

The helper only ever creates or edits **library** entries. It cannot modify a part already placed on the canvas.

> **There is no search backend.** A static page cannot run a web search, so the shipped
> `researchBackend()` is a clearly-marked stub that reports "no research backend is
> configured" and adds nothing. The whole flow — validation, dialog, review, accept,
> and every failure state — is real and tested against it. To connect a real backend,
> assign one function:
>
> ```js
> window.HARNESS_RESEARCH = async (spec) => ({ status, entry, mate, accessories, message });
> ```
>
> `spec` is `{ q, mfr, pn, type, pinCount, notes }`; `status` is one of `ok`,
> `notfound`, `ambiguous` or `error`. That single hook is the only integration point.

## Mates, accessories and crimp detail

Selecting a part adds four sections to the bottom of the Inspector, collapsed until you open them:

- **Compatible mates** — mating connector part numbers, with manufacturer and a note.
- **Accessories** — tick the categories that apply (crimp terminals by AWG, wire seals, wedge locks / TPA, backshells and strain relief, boots, cavity plugs, crimp tools). Each item you add is tagged **required** or **optional**; click the tag to flip it. The category choice is remembered on the library entry so it comes back next time the part is placed.
- **Per-pin crimp** — a row per cavity showing terminal PN, description, AWG range, finish, gender and type. Pick a terminal family and **Fill all** defaults one terminal per cavity; any single pin can then be overridden or cleared.
- **Notes** — free text, stored with the part.

No terminal part numbers ship with the app. The catalogue is whatever you enter, because a guessed PN is worse than a blank one.

This detail stays in the Inspector. The only thing it adds to the schematic is a small connector badge beside any block that has a mate recorded — placed on the side opposite the wiring, nudged clear of neighbours, and never further from the block edge than 0.7 × its own width.

Mates, accessories and crimp choices belong to the placed part. Editing the library afterwards never resets them.

## Editing wires

The workspace has no sheet edge — pan and place parts anywhere, including negative coordinates.

Wires route orthogonally. A wire leaving a pin never folds back over that pin, and a wire meeting a splice stops at the junction instead of overshooting it.

Drag a wire's body to drop a **fix point**: a pinned waypoint that holds its world position when either endpoint later moves, so the path stretches around it and nothing detaches. Fix points snap to horizontal, vertical and 45° against the wire's endpoints and its other fix points. Right-click a wire to add or clear them.

Select a wire to get orange grips on both ends; drag a grip onto another terminal to reattach that end. Labels and power/ground symbols are selectable and can be dragged clear of crossing wires — **Reset label position** in the right-click menu puts them back.

Pressing a terminal only starts a wire once the pointer actually moves, so a plain click on a terminal selects the part underneath it.

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
| Add a part | click a library entry, or right-click the canvas |
| Find a part | type in the library search box (part no, model or description) |
| Create a library entry | **+ Add component** in the library panel |
| Look a part up | **Find more…** next to the library search |
| Edit a library entry | hover the row, click **edit** |
| Delete | select, then `Delete` |

Wire labels are off by default; tick **Wire labels** to show them all, or select a single wire to see just its own.

Edits autosave in `localStorage` (`st185-harness-v7`). **Reset ST185** reloads the seed. Export JSON or SVG from the header.

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
