# ST185 RealDash `.rd` build folder

The RealDash dashboard is built and done (Dan 2026-11-12, A24 a; DECISIONS "Parked rows (R102)"): the Pi has
Dan's current dash file, already checked on live CAN. This folder keeps the editor tools and the notes worth
keeping. The build plan and the build notes were deleted 2026-11-15 (Dan A50 a); git history keeps them.

- **Layout spec (the one owner):** repo-root `REALDASH-LAYOUT.md`. Look and feel: repo-root
  `realdash-simulation.html`.
- **CAN channel file:** repo-root `link_g4x_realdash.xml` (single copy). Import it so the `ST185:` inputs exist
  for gauges to bind to.
- **Dashboard `.rd`:** the file on the Pi is the current one (A24 a). The repo copies, root `st185_dash.rd` and
  `rd-build/realdash-root/st185_dash.rd`, are older saves and differ from each other.
- `FINDINGS.md` - why RealDash's editor cannot run on a headless cloud VM (software OpenGL-ES deadlock); it needs
  a real GPU desktop.
- `CREDENTIALS.md` - My RealDash login, local only (gitignored).

## As built (2026-07-06, RealDash 2.6.7 on Windows, editor automation)

Where the built dash differs from `REALDASH-LAYOUT.md`:

1. Editor canvas 1920 x 1080: spec positions scaled x 2.4 (X / W) and x 2.25 (Y / H); RealDash scales it back to
   the Pi's 800 x 480.
2. No mini-bars in the tiles: numbers plus alarm colours carry the function.
3. No strobe fade on the red pills / alarm states: they turn solid red.
4. The caution band is a white-to-red blend (RealDash dynamic colour has 2 stops), not a separate amber step.
5. Title text is solid `#f4f7fb`; the background is flat dark.
6. Labels carry units in plain ASCII ("CHARGE IAT (C)", "COOLANT P (kPa)", "TURBO (RPM)").
7. Boost Map / Cruise / A/C show numbers; enum text depends on RealDash's enum rendering.
8. Gauges are bound with the `185:` search prefix, because plain names matched RealDash core channels first.
9. The Coolant P tile was first built with its red level at 250 kPa; the spec is 200 (DECISIONS R105;
   `CAN-BUS-MASTER-DESIGN.md` display note N6).

## Tools

`tools/` - desktop automation for the RealDash editor (PyAutoGUI; no MCP server needed):

- `automation_helper.py` - PyAutoGUI CLI: screenshot / click / type / key / pixel.
- `requirements.txt` - `pip install -r tools/requirements.txt`.
- `SETUP.md` - install, per-OS permissions, checks, and an optional remote (VNC) path.
- `mcp.example.json` - optional example only.
- RealDash editor macros (each drives the open editor by fixed screen positions; kept and linked, Dan T9 a,
  2026-11-11):
  - `add_gauge.py` - add a text gauge and set its position, text and colours (fullscreen 1920x1080).
  - `bind_pill.py` - bind the selected gauge to an input and set its dynamic background colours.
  - `combo.py` - press one key with the given modifier keys held.
  - `fix_dyncolor.py` - for each gauge list row given, set its text colour 1 to white (`f3f8ffff`).
  - `label_paste.py` - paste copies of the copied label gauge, then position each and set its text.
  - `paste_batch.py` - paste the copied gauge once at each given position.
  - `rebind.py` - rebind gauges to ST185 inputs, by gauge list row and search term.
  - `set_levels.py` - set the warning and critical levels of the gauges on the given list rows.
  - `set_text.py` - set the selected gauge's text (and text colour) in Look'n Feel > Font & Text.
  - `set_xywh.py` - type up to four values into the editor's four position / size fields (`-` skips one).
  - `value_paste_bind.py` - paste value-gauge copies and bind each, with its warning / critical levels and
    dynamic text colour.

RealDash's `.rd` format is an undocumented binary, so a dashboard is made only by driving RealDash's own editor.
Later RealDash work (a few channel updates, a backup camera screen) is parked: `docs/OPEN-ITEMS.md` row 184.
