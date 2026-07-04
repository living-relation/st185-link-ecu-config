# RealDash `.rd` file format — feasibility findings (2026-07)

**Question:** can a complete, importable RealDash dashboard (`.rd`) be authored/generated
offline (by hand, script, or this repo), or must it be produced inside the RealDash app?

## Finding: `.rd` is a closed, binary, editor-only format — it CANNOT be generated offline

RealDash dashboards are a **proprietary binary format** created and edited **only** inside the
RealDash application's visual editor (Windows / Android / iOS). There is **no public schema, no
text/XML/zip form, and no supported offline authoring path**. This is confirmed by the RealDash
developers and community:

- RealDash devs describe dashboard/animation internals as deliberately closed (premium dashes are
  effectively read-only; animation files are withheld "to make it too easy to duplicate and
  distribute the dashboard"). Users can tweak values of existing gauges but not author the file
  externally. — RealDash Forum, *"How do I modify animations of a dash I purchased?"* and
  *"Editing Premium Dashboard"*.
- The community has repeatedly asked for an offline/desktop dashboard authoring tool or an
  XML-import path for layouts; RealDash has **not** provided one. — RealDash Forum,
  *"Animation XML documentation?"*.
- Dashboards move between platforms only as the finished `.rd` binary: build on Windows →
  `File → Save as` → transfer → `Gallery → Recent → Open from file` (or `Gallery → Load From
  File`). — RealDash Forum, *"Edit dash on Windows 10, use on Android?"*.

**What XML is actually for.** RealDash XML (`RealDashCAN version="2"`) is **only** a *CAN/OBD2
channel-description* file — it defines how CAN frames map to RealDash inputs. It does **not** and
cannot define the dashboard layout. — `janimm/RealDash-extras` *Channel Description File (XML)*;
RealDash FAQ *"How do I customize the OBD2 communication?"*.

### Sources
- https://forum.realdash.net/t/edit-dash-on-windows-10-use-on-android/797
- https://forum.realdash.net/t/how-do-i-modify-animations-of-a-dash-i-purchased/1052
- https://forum.realdash.net/t/editing-premium-dashboard/6064
- https://forum.realdash.net/t/animation-xml-documentation/1420
- https://github.com/janimm/RealDash-extras/blob/master/RealDash-CAN/realdash-can-description-file.md
- https://realdash.net/faq.php

## Consequence for this repo

Because the `.rd` cannot be produced offline, the deliverables are:

1. **`link_g4x_realdash.xml`** — the importable CAN channel-description file (this IS offline-
   authorable and is the real, importable artifact). It creates every `ST185:` input a gauge binds
   to.
2. **`REALDASH-LAYOUT.md`** — a precise, gauge-by-gauge buildable spec (page, tile, type, position,
   size, range, units, source channel, warning thresholds) you assemble once in the RealDash editor,
   then `Save as` to get your `.rd`.
3. **`realdash-simulation.html`** — a browser preview of the finished layout so you can eyeball it
   before building.

The only step that must happen **inside RealDash** is assembling the gauges per the spec and saving
the `.rd`. Full step-by-step is in `REALDASH-LAYOUT.md` §8.

## Optional: version-control animations as XML (not the whole dash)

RealDash *animations* (not layouts) can be exported/imported as XML for dashes you author yourself
(`Edit → Animations`), so strobe/fade behavior can be kept as text alongside this repo. This still
requires the gauges to already exist in-app with matching names. See
`janimm/RealDash-extras` → *Dashboard-animation-examples*. This is a convenience, not an offline
`.rd` generator.
