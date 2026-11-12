# Placement editor (refine-only)

One shared template for every harness's placement editor: all ten harnesses use it since 2026-11-11 (one seed per editor in `seeds/`; one Wheel speed editor, `seeds/WheelSpeed.json`, owns both wheel speed harnesses, DECISIONS B8 "X9"; editor links: `docs/OPEN-ITEMS.md` row 180 and History). Rules: DECISIONS "Placement and lengths (B8)": N120 "Editors refine, agents route", "Top view only", "Simpler is better", own parts only.

- `editor.html`: the page template. The seed format and the save format are documented in its top comment.
- Wireway corridors (DECISIONS B8 "Wireway corridors", approved by Dan 2026-11-11 12:19 with Y5 a-Y8 a): the corridor set is `../corridors.json`, the one source; every main trunk in a seed stays inside it (short device branches may leave, Y7 a). `python ../check_corridors.py` checks every seed (AB-engine: its Route 16 lines) and runs in `tools/check_all.py`; run it after any seed route change.
- `make_editor.py`: fills the template with one harness's seed and the top-view plan image. Device and fixed-marker names are pulled from the master's plain names (`from_id` / `to_id` -> `from_name` / `to_name`), so a rebuild after a master rename shows the new names. It warns on any code left in a name, short label or note (DECISIONS B22: only fuse box / relay codes and factory EWD plug IDs may show). Optional seed keys it reads: `title` (the page title, to keep an artifact's title) and `harnesses` (the harnesses one editor owns; a device of any other harness stops the build).

## What Dan sees
- Plain names only: ids are keys, never shown. Map labels come from each line's and device's `short` field (a line with no `short` gets no map label; the legend lists every line by name).
- Other harnesses' parts, if shown for context, are grey fixed markers (`refs`), never draggable and never saved.
- Front of the car to the RIGHT, driver side UP, on sideways phones and desktop, with a "Front → / Driver ↑" marker. On a phone held upright the map turns front UP / driver LEFT ("Front ↑ / Driver ←") when that fits the harness at least 10% bigger, e.g. the long rear harnesses (Dan I1 a, 2026-11-08); the turn is view-only, saves stay in car mm.

- Zoom (Dan 2026-11-10): dots, markers and labels keep their screen size when zooming in, so close parts spread apart and can be placed; they shrink with the map when zooming out, so zooming out never adds overlap. Every dot is drawn on its true spot at every zoom; nothing is fanned out or rearranged. Zoom out goes past the Fit view (the whole plan plus 10%, at least 2.5x Fit). An editor built before this fix must be rebuilt to get it. Pan and zoom stay on the plan, grown to take in any of the harness's own lines and grey markers drawn off it (2026-11-11, for EngineRoom-C's cabin legs).
- Ends in another frame (Dan X7 a, 2026-11-11): the engine-bay maps are in EWD points, the cabin maps in car mm. EngineRoom-C shows its cabin ends (J/B No.1, IE1, IG2, the LOGIC box, the DRL cut relay, the A/C amplifiers, R/B No.4) as grey markers on their AB-cabin / CabinPower spots turned into EWD points at 5.3 mm per point (DECISIONS B8), anchored on the LH pass-through (side to side) and the RH fender exit (fore and aft), with grey dashed cabin legs to those two exits; an end too far away for the map (the trunk kill switch) is an edge marker labelled with the distance still to go.
- Small parts with no spot of their own (Dan X8 b, 2026-11-11): Claude places them by rule (beside the box, splice or device they serve; splices by DECISIONS B8 "Splice and bussed-plug spots") as normal draggable dots, each noting "placed by Claude by rule; drag to tweak".

## What Dan can do in it
- Move devices on the top view (tap a dot to pick it, then drag it). Pan with one finger, zoom with two or with the + / - / Fit keys.
- Set a device's drop (mm), undo, put one device or all of them back on Claude's spot, and Save.
- Nothing else (except the engine-bay editor, below): routes, which route a device hangs on, and the device list come from the seed. No isometric view, no drawing lines, no adding or removing devices.
- A device moved more than `warnMm` (300 mm) from its seed spot is flagged on the map, in the list and in the save (`far`), never blocked.

## Engine bay only: parts and overall routes (Dan W4 c, 2026-11-10)
The AB-engine editor (`seeds/AB-engine.json`, db doc `layouts/route16`, the Route 16 editor link) is the one editor where Dan also draws routes. Its seed sets `drawRoutes: true`.

- Dan can move every part already in the harness; none can be removed or added.
- "Draw routes" mode: pick a route, drag its points, add points (a tap near another route snaps onto it), remove the last point, delete a route, start a new route, rename a route.
- Dan draws the overall routes only, never each sensor's spur. After a save the agent hangs every sensor on the nearest of Dan's routes with its own spur; no sensor sits at 0 mm from a trunk or branch (the spur is at least the drawn offset plus the part's drop).
- Extra seed keys, all optional and off for every other editor: `drawRoutes`, `unitMm` (mm per map unit; Route 16 points are 5.3), `compass` (the two marker labels), `noTurn` (never turn the map on a phone), `pad`, `minView`.
- The save adds `lines` (the routes as Dan left them), `routesChanged`, `unitMm`, `editor: "parts-and-routes"`, and each device's nearest `line`.
- Build it with the Route 16 engine-bay picture, not the under-body plan: pass an earlier engine-bay editor page (Harness C's or Route 16's) as the second argument.
- The EngineRoom-C editor (`seeds/EngineRoom-C.json`, db doc `layouts/harnessC`, the "Harness C" link) uses the same picture and `unitMm` 5.3 but stays refine-only (no `drawRoutes`).

## Make or reseed an editor
1. Claude draws the harness's route in `ST185-harness.layout.json` (straight, shortest, cleanest) and writes a seed JSON: that harness's own devices on their rough spots, its lines, `doc` = `layouts/<harness>`, and a NEW `seedVersion`. A save made from an older `seedVersion` is not loaded (it stays in the db and is copied to `<doc>_prev` on the next save).
2. `python make_editor.py <seed.json> <topview.png or an earlier editor page> <out.html>`. The top-view plan image is the body manual DI-7 under-body plan already embedded in every earlier editor (its rect: `[-3455.6, -809.1, 4262.1, 1664.1]` mm); passing an earlier editor's saved HTML reuses it (the Artifact tool's `read_file` with `paths` saves a published page as a file).
3. Publish `out.html` with the Artifact tool to that harness's existing editor URL (capabilities `db` and `user`), so the link Dan has keeps working.
4. One editor at a time (DECISIONS B8): after Dan saves: read `layouts/<harness>`, check every `far` device, and copy the moved spots into the layout tree by hand (no script writes the tree from a save); write that harness's lengths and wire list, then hand Dan the next editor.
5. Then the tree: a cabin, trunk or car-mm hand-off node takes its spot from the seed as `mm` (car mm) in `ST185-harness.layout.json`; a segment's bends go in `tree_mm` `via`, a drop or breakout the top view does not draw in `extra`. Run `python ../build_drawings.py --write-tree-mm` (it writes every such segment length from the model), then `--lengths` / `--write-lengths`. Never type a cabin segment length by hand: `build_drawings.py --check` fails when one differs from the model (DECISIONS B8 "One mm model"). Engine-bay trees (Route 16 / 17, EWD points) are built from their route files instead.
