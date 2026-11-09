# Placement editor (refine-only)

One shared template for every harness's placement editor (CabinPower, WheelSpeed-Front, WheelSpeed-Rear, RearFuel and later ones). Rules: DECISIONS "Placement and lengths (B8)": N120 "Editors refine, agents route", "Top view only", "Simpler is better", own parts only.

- `editor.html`: the page template. The seed format and the save format are documented in its top comment.
- `make_editor.py`: fills the template with one harness's seed and the top-view plan image. Device and fixed-marker names are pulled from the master's plain names (`from_id` / `to_id` -> `from_name` / `to_name`), so a rebuild after a master rename shows the new names. It warns on any code left in a name, short label or note (DECISIONS B22: only fuse box / relay codes and factory EWD plug IDs may show).

## What Dan sees
- Plain names only: ids are keys, never shown. Map labels come from each line's and device's `short` field (a line with no `short` gets no map label; the legend lists every line by name).
- Other harnesses' parts, if shown for context, are grey fixed markers (`refs`), never draggable and never saved.
- Front of the car to the RIGHT, driver side UP, on sideways phones and desktop, with a "Front → / Driver ↑" marker. On a phone held upright the map turns front UP / driver LEFT ("Front ↑ / Driver ←") when that fits the harness at least 10% bigger, e.g. the long rear harnesses (Dan I1 a, 2026-11-08); the turn is view-only, saves stay in car mm.

## What Dan can do in it
- Move devices on the top view (tap a dot to pick it, then drag it). Pan with one finger, zoom with two or with the + / - / Fit keys.
- Set a device's drop (mm), undo, put one device or all of them back on Claude's spot, and Save.
- Nothing else: routes, which route a device hangs on, and the device list come from the seed. No isometric view, no drawing lines, no adding or removing devices.
- A device moved more than `warnMm` (300 mm) from its seed spot is flagged on the map, in the list and in the save (`far`), never blocked.

## Make or reseed an editor
1. Claude draws the harness's route in `ST185-harness.layout.json` (straight, shortest, cleanest) and writes a seed JSON: that harness's own devices on their rough spots, its lines, `doc` = `layouts/<harness>`, and a NEW `seedVersion`. A save made from an older `seedVersion` is not loaded (it stays in the db and is copied to `<doc>_prev` on the next save).
2. `python make_editor.py <seed.json> <topview.png or an earlier editor page> <out.html>`. The top-view plan image is the body manual DI-7 under-body plan already embedded in every earlier editor (its rect: `[-3455.6, -809.1, 4262.1, 1664.1]` mm); passing an earlier editor's saved HTML reuses it.
3. Publish `out.html` with the Artifact tool to that harness's existing editor URL (capabilities `db` and `user`), so the link Dan has keeps working.
4. After Dan saves: read `layouts/<harness>`, check every `far` device, and copy the moved spots into the layout tree by hand (no script writes the tree from a save).
