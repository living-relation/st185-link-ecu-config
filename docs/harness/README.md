# Harness files - which one is current

Written 2026-09-22 because the folder had 24 `.harness` files for 8 real looms and
no way to tell them apart. Read this before opening any of them.

## The short answer

**`rebuild/` is the truth. Everything else is a copy, a build product, or history.**

| Folder | What it is | Edit it? |
|---|---|---|
| **`rebuild/`** | The 8 current looms. Human-readable JSON, what git diffs, what matches harness.design | **Yes - this is the source** |
| `min/` | Same 8 documents, whitespace stripped, for upload | No - `make_min.py` regenerates it |
| `legacy-prebuild/` | The 4 pre-split looms the rebuild came from | No - frozen baseline, see below |
| `archive/cursor-engineroom-experiments/` | Cursor's throwaway EngineRoom-C variants | No - history only |

## The 8 current looms

| File | Loom | Scope |
|---|---|---|
| `ST185-A-ECU.harness` | A, cabin | ECU-A pins to bulkhead A |
| `ST185-A-engine.harness` | A, engine | bulkhead A to the engine bay |
| `ST185-B-ECU.harness` | B, cabin | ECU-B pins to bulkhead B |
| `ST185-B-engine.harness` | B, engine | bulkhead B to the engine bay |
| `ST185-CAN.harness` | CAN | the CAN backbone |
| `ST185-EngineRoom-C.harness` | C | engine room, PDB, fuse blocks + relays, EPS, OEM J/B injection |
| `ST185-ClusterLED.harness` | (folding into the cabin accessory loom) | cluster warning LEDs |
| `ST185-WheelSpeed.harness` | (splitting into loom C + rear trunk) | four ABS drops and both VR conditioners |

Loom C's `pmu` node was **repurposed on 2026-09-22**, not deleted. The PMU-16 was
dropped (plan 6.46–6.48) and the node is now the glove-box body block — a second
fuse block plus micro ISO relays — carrying the same ex-J/B2 circuits on the same
wires, plus the CSB3 and device feeds. The element id stays `pmu` for wire
continuity; the label and cavities tell the truth.

The last two are **in transition**. Plan 6.41 dissolves them: ClusterLED joins the
new cabin accessory loom, and WheelSpeed splits - front half into loom C, rear half
into the new rear trunk loom. Until that pass runs they are still the only place
those circuits are drawn, so they stay.

## Why `legacy-prebuild/` still exists

`ST185-Signal.harness` and `ST185-Power.harness` were the two monolithic looms
before the A/B/engine split. They are **not** maintained any more, but they cannot
be deleted yet:

`verify_rebuild.py` diffs every conductor in `rebuild/` against them. That diff is
the safety net that catches an accidentally dropped wire, and it is the reason the
rebuild can be trusted. Delete the baseline and the net goes with it.

They stop being needed once the 6.41 restructure lands and a new baseline is taken.
Until then: read them for history, never edit them.

## The pipeline

```
rebuild/*.harness            <- edit here, or via a fix_*/gen_* script
  |
  +-- lint_v09.py            schema and rule check
  +-- verify_rebuild.py      conductor diff against legacy-prebuild/
  +-- layout_633.py          applies the 6.33 layout standard
  +-- make_min.py            writes min/
  +-- buylist.py             writes ../NEED-TO-BUY.md
  +-- buildlist.py           writes ../HARNESS-BUILD-LIST.csv
  |
  +-- min/*.harness          -> uploaded to harness.design
```

`check_all.py` runs the whole thing in one command and exits non-zero if
anything fails. Use it before every commit:

```
python docs/harness/check_all.py
```

`run_pipeline.bat` runs the first four in order. Run `buylist.py` and
`buildlist.py` after any part change.

## Parts rules

Four rules the checks enforce, all added 2026-09-22 after the buy list was found
to be double-counting:

1. **One cavity, one part.** A cavity holds a contact or a sealing plug, never
   both. A cavity wired in *any* loom gets a contact; a cavity wired in *no* loom
   gets a plug, in its own size. `audit_cavity_parts.py` fails the build otherwise.
2. **One physical connector, one part number, everywhere it is drawn.** Bulkhead A
   is on three drawings and bulkhead B on two. Every copy must carry the same part
   and the same contact stamps; `buylist.py` aborts if two looms disagree. It then
   counts the copy that carries the parts - not whichever file is read first - and
   prints a *Counted once, drawn more than once* table in `NEED-TO-BUY.md`.
3. **Cross-reference dummies claim nothing.** A connector drawn on a second loom
   only so the wire has somewhere to land has no `partId` and no contact stamps.
   That is how the tools tell a dummy from the real thing.
4. **Never invent a part number.** A part that has not been checked against the
   manufacturer gets `TBD ...` and the reason in its description. The RADLOK
   firewall pass-through is the current example.

Adding up the parts lists off the individual drawings by hand will over-order.
`NEED-TO-BUY.md` is the only correct total.

**Both generators were repointed on 2026-09-22.** They used to read the pre-split
files, so every buy list before that date was generated from the wrong harnesses -
which is why the CSB3 HD30 connector and 68 size-20 sockets never appeared on it.

## Versioning

Files are not version-numbered. Git is the version history, and one folder means
one generation:

- a new generation gets a new folder, and the old one moves to `legacy-*` or
  `archive/`
- nothing is ever copied sideways into the same folder with a suffix
- `-v2`, `-new`, `-final`, `-copy` in a filename is a bug, not a version

## Audit

`audit_repo.py` prints every harness file and wiring document with its element
counts and last commit date. Run it when this README looks out of date.
