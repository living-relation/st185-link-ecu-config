# Patch note — `intercooler-report.html`

Revision 2, 31 August 2026. Derived from `THROTTLE-BODY-PLUMBING-SPEC.md` rev 2.

> **The report was NOT edited, and should not be.** Another session has been
> working in it. Observed at 12:50 UTC as 313,909 bytes / 4,362 lines, then at
> 12:58 UTC as 444,885 bytes / 5,907 lines, last modified one minute earlier.
>
> **All line numbers below are from the 4,362-line version and are stale.**
> Search on the quoted text instead. Every item quotes enough surrounding text
> to be located reliably.

---

## Summary of what changed and why

The report recommends 2.5 inch pipe on both runs with a taper into the throttle
body. Three facts have come in since:

1. The SpeedFactory SS-850 has **3 inch inlet and 3 inch outlet**.
2. The throttle body adapter Dan owns is a **3 inch HD clamp** fitting, and
   Outsider Garage makes no smaller version.
3. The build is **all welded** with clamps at only two or three joints, which
   changes the packaging arithmetic — a welded 3 inch pipe is narrower than a
   2.5 inch pipe with silicone couplers.

Net effect: **the hot side stays at 2.5 inch. The cold side should go to
3.0 inch.** Neither is forced. Full reasoning in the spec document.

---

## Change 1 — §10 headline recommendation

Find: *"Short answer: **2.5 inch both sides. Do not mix.** The only diameter
change in the system is a short taper into the 74 mm throttle body, and that is a
transition, not a different pipe."*

Replace with a split recommendation: 2.5 inch hot, 3.0 inch cold. The reasoning
that "a single diameter is right, and it makes couplers, clamps and spares
interchangeable" was sound when both ends were unknown. It no longer holds when
the cold run has a 3 inch fitting at each end and the build is welded.

Keep the section's rebuttal of the hot/cold folklore. That is still correct and
still worth saying — the split recommended here is driven by end fittings and
packaging, not by air density.

## Change 2 — §10 velocity table is computed on the wrong diameter

Find the table headed *"Pipe OD"* with rows for 2.00 / 2.25 / 2.50 / 2.75 /
3.00 in.

It was computed using **outside diameter as the flow diameter**. Check: its
2.5 inch cold-side figure is 126 ft/s; recomputing on 63.5 mm outside diameter
gives 129 ft/s, while the correct 60.20 mm inside diameter gives 144.0 ft/s.
Every row is understated by 11–13%.

The §11 pressure drop budget does **not** share this error — its 0.44 psi hot and
0.44 psi cold figures reproduce at 0.442 and 0.446 psi on correct inside
diameters. So §10 and §11 currently contradict each other.

Replacement, computed on inside diameter at 0.065 in wall, same design point
(45.7 lb/min, hot 274 kPa / 180 °C, cold 266 kPa / 62 °C):

| Pipe OD | Inside dia | Hot | Hot ΔP | Cold | Cold ΔP | Volume |
|---------|-----------|-----|--------|------|---------|--------|
| 2.50 in | 60.20 mm | 189.1 ft/s | 0.442 psi | 144.0 ft/s | 0.446 psi | 2.85 L/m |
| 2.75 in | 66.55 mm | 154.7 ft/s | 0.288 psi | 117.9 ft/s | 0.291 psi | 3.48 L/m |
| 3.00 in | 72.90 mm | 128.9 ft/s | 0.196 psi | 98.2 ft/s | 0.198 psi | 4.17 L/m |

Add a column header note that these are inside diameters at 0.065 in wall.

Two conclusions in the surrounding prose need revising as a result:

- The 3.00 in row currently reads *"Oversized. Cold side is now dead volume."*
  Soften. At 98.2 ft/s the cold side is low but it is the correct choice when
  both end fittings are 3 inch.
- The 2.50 in row's claim that it is *"below Garrett's stated band"* is true but
  should note that at 189.1 ft/s — not the 166 ft/s currently shown — it is very
  close to the 200 ft/s lower bound.

## Change 3 — §10, delete the taper callout

Find the callout headed *"The one legitimate reason to change diameter: the
throttle body"*, specifying a taper from 2.5 in to ~2.9 in over the last
100–150 mm at ≤7° half angle.

That taper does not exist in this build. The throttle end is a hard clamped
flange face at 3.00 inch.

Also correct: the callout states the throttle body *"has a bore of 2.91 in"*. The
plate is stamped 745, so 74.5 mm = 2.933 in. The 2.91 figure appears twice in the
document.

Replace with a short description of the actual joint: a Vibrant-pattern HD clamp
joining a 3.000 in weld ferrule on the pipe to the integral clamp face on the
Outsider Garage adapter, with a +1.60 mm step up into the 74.5 mm plate that is
worth 0.0003 psi and should be left alone.

## Change 4 — §10, the volume block needs checking at source

Find the block beginning *"System volume, 2.5 in build:"* with `hot pipe 1.1 m ×
1.58 L/m`.

**1.58 L/m matches neither the inside nor the outside diameter area** — inside
diameter gives 2.85 L/m for 2.5 inch pipe. It is roughly half the correct figure.
Check this at source before trusting anything downstream of it.

Once corrected, the totals move again because the cold side goes to 3.0 inch:
cold run 1.5 m at 4.17 L/m instead of 2.85 L/m adds about 2.0 L. The stated
9.05 L / 4.1× displacement becomes roughly 11 L / 5×. Still inside the healthy
3–6× band — say so rather than leaving the old number.

## Change 5 — §10 and §21, bend radius for the cold side

Find *"For 2.5 in pipe that is a 95 mm centreline radius minimum."*

Still correct for the hot side. Add that the 3.00 in cold side at R/D ≥ 1.5 needs
**114 mm** minimum centreline radius.

## Change 6 — §12 parts list

Find the rows for mandrel bends, silicone couplers and T-bolt clamps.

- Mandrel bends: split into 2.5 in for the hot run (~3 bends, 1.1 m) and 3.0 in
  for the cold run (~4 bends, 1.5 m).
- Silicone couplers: **delete `2.5→2.9 taper ×1`.** It is not used. The
  `2.5→2.0 reducer ×1` stays for the turbo outlet. Add a `2.5→3.0 reducer ×1`
  for the intercooler inlet and a `3.0 in straight ×1` for the intercooler
  outlet. The count drops from six to three, because everything else is welded.
- T-bolt clamps: six, not fourteen, sized to the coupler outside diameters.

Add:

| Item | Spec | Qty | Est. cost |
|------|------|-----|-----------|
| HD clamp, throttle body | Vibrant 3.000 in — clamp band plus one weld ferrule. The OG adapter is the other half | 1 | $60–100 |
| HD clamp, alignment joint | Vibrant 12516 full assembly, 3.00 in | 1 | $150–190 |

## Change 7 — §19.1 and the open questions list: port size conflict is resolved

Find *"(1) Port size. Every assembled unit above ships with 3.0 in ports; §10
specifies 2.5 in piping"* and the matching entry in the open questions list.

Resolved. The SS-850 is 3 in in and 3 in out, and the cold side now runs 3.0 inch
throughout, so there is no step at the cold tank. The hot side keeps a 2.5 → 3.0
reducing coupler at the intercooler inlet, which is a normal coupler and not a
compromise. Mark it closed in both places.

## Change 8 — §21 build sheet

Find the cold pipe spec line: *"2.5 in mandrel alloy / 2.5 → 2.9 in taper, ≤7°,
last 150 mm into the 74 mm TB / BOV mounted close to the throttle"*.

Replace with:

> 3.00 in OD × 0.065 in wall mandrel alloy, R/D ≥ 1.5 (114 mm min centreline
> radius). Welded throughout. Silicone coupler at the intercooler outlet for
> engine movement; one HD clamp mid-run for alignment; Vibrant 3.000 in HD clamp
> to the Outsider Garage throttle adapter. BOV close to the throttle.

The hot pipe line stays at 2.5 in but should gain: *"2.5 → 3.0 in reducing
coupler at the intercooler inlet"*.

## Change 9 — §5 summary spec line

Find *"Cold-side pipe — 2.5 in OD, taper to 2.9 in at the throttle body only"*
and the nearby sentence about *"a short taper into the 74 mm throttle body"*.

Both become: hot side 2.5 in, cold side 3.0 in, HD clamp joint at the throttle.

## Change 10 — new content worth adding

**Engine movement.** The report does not currently address it, and the build is
now mostly welded, which makes it matter. Each run needs at least one flexible
joint, because the engine rocks on its mounts and the intercooler is bolted to
the chassis. A run that is rigid at both ends puts that movement into the welds,
and aluminium has no fatigue limit. Recommended location is the intercooler end
of each run.

**Packaging by outside diameter.** Worth a short table, because pipe diameter is
not what has to clear:

| Configuration | OD |
|---------------|-----|
| Welded 2.50 in pipe | 63.5 mm |
| Welded 3.00 in pipe | 76.2 mm |
| 2.50 in + coupler + T-bolt clamp | 80.5 mm |
| 3.00 in + coupler + T-bolt clamp | 93.2 mm |

The point being that a welded 3 inch run is slimmer than a coupled 2.5 inch run.

**Cross-reference** to `THROTTLE-BODY-PLUMBING-SPEC.md` for the full diameter
chain, the 2.5 inch fallback with its transition cone, and the bill of materials.

---

## What must NOT be changed

- **The §11 pressure drop method.** It is correct and it is the only part of the
  report computed on real inside diameters. Only the numbers move: hot pipe stays
  0.44 psi at 2.5 in, cold pipe drops from 0.44 to 0.198 psi at 3.0 in. Total
  system budget improves from the stated 1.4–1.7 psi to about 1.17 psi.
- **Core selection, end tank design, the thermal model.** Untouched by any of
  this.
- **The hot side at 2.5 inch.** It is the right size: closest of any option to
  Garrett's band, smallest pipe in the tightest and hottest part of the bay, and
  it costs 0.44 psi. Do not let the cold side change drag it along.
