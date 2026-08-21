# ST185 harness schematic

Standalone browser schematic editor modeled on [harness.design](https://harness.design): dark canvas, connector blocks with numbered pins, orthogonal wires, right-click add, drag pin-to-pin.

Opens with the Celica GT-Four ST185 / Link G4X XtremeX parts already placed. Assigned I/O from `XTREMEX-IO-TABLE.html` and `WIRING.md` is wired. Yellow **UNWIRED** blocks have no confirmed pin-to-pin yet — drag a pin handle to another pin to draw those yourself.

## Run

Open `index.html` in a browser, or from the repo root:

```bash
python3 -m http.server
```

then browse to `apps/harness-schematic/`.

## Use

| Action | How |
|---|---|
| Pan | drag empty canvas, or hold Space |
| Zoom | mouse wheel |
| Move a device | drag the block |
| Draw a wire | drag from a pin handle to another pin |
| Add a part | right-click canvas, or use the left library |
| Delete | select, then Delete |
| Fit | Fit button |

Edits autosave in `localStorage`. **Reset ST185** reloads the seed. Export JSON or SVG from the header.

Layout view is a placeholder until bundle lengths exist.

## Sources

Device list and pin functions come from:

- `XTREMEX-IO-TABLE.html` (ECU I/O — DBW Bosch 74mm ETB, 1ZZ COP, flex sensor, MRS EPS)
- `WIRING.md` (cluster GPIO, 5 V buck, UART, CAN transceiver)
- `ECUMASTER_SWITCHBOARD_SETUP.md` (CSB3 analog / switch map)
- `CAN-BUS-MASTER-DESIGN.md` (4-node 1 Mbit/s bus, termination)

The Waveshare MCP2515 hat is on the canvas **unwired on purpose** — cooling fan only, not a CAN node.
