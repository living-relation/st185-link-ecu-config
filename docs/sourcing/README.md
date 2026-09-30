# Sourcing - what to pick, and in what order

Binding on every part choice in this project.

## Selection order

1. **What Daniel already owns.** `te-on-hand-bom.csv` in this folder. If a part on
   that list will do the job, it wins - even over a "better" part.
2. **TE Connectivity.** Preferred manufacturer for connectors, contacts, seals,
   backshells and heat shrink. Prefer parts TE offers **free samples** on.
3. **Anything else**, and only then. Say in the BOM row why nothing above fit.

Never spec a new connector family without checking step 1 first. This project
already owns HDP20, HD30, Deutsch DT, SuperSeal and AMP MCP hardware.

## Sources in Google Drive

Live originals - this folder holds the machine-readable copy, Drive holds the record.

| What | Drive |
|---|---|
| TE BOM with screenshots (the on-hand list) | [TE_BOM_with_screenshots.xlsx](https://drive.google.com/file/d/1-_bV6aFDEziQ8vdA0O3bY89Y6LLW9Y9y/view) |
| TE order confirmation 12058 | [PDF](https://drive.google.com/file/d/159habnSaez1M1b82IV8AE56DldJ6Wl5H/view) |
| TE order confirmation 14197 | [PDF](https://drive.google.com/file/d/1N_nEqimFTa_wpNMRbFzAKznIFCrN35xy/view) |
| TE order confirmation 16389 | [PDF](https://drive.google.com/file/d/1WNSSx-Xx9_Rw-h-elpAABvGjFEDbmEup/view) |
| Parts Invoices folder (all vendors) | [Folder](https://drive.google.com/drive/folders/1WYnzHIZ_LByvWfHXgBQ5bqrEy9i8sSzS) |
| Tables folder (BOMs, fitting lists) | [Folder](https://drive.google.com/drive/folders/17fnF76zInKW9rPpA7fxFXmNuPEiO-35p) |

The three TE order confirmations are **image-only PDFs** - print-to-PDF web pages
with no extractable text. They cannot be parsed by an agent. Read them by eye when
a quantity needs confirming; the spreadsheet is the list to work from.

`qty_ordered` in the CSV is what was **ordered**, not a live shelf count. Treat it
as an upper bound and confirm before committing to a build.

The same spreadsheet carries a second table of AN / NPT / BSP plumbing fittings.
Not imported here - this folder is electrical.

## What the on-hand list changes right now

### Size 20 contacts: none on hand

The list has roughly 300 size-16 contacts (0460-202-1631, 0462-201-1631,
0460-215-1631, 0462-209-1631, 0462-221-1631) and **zero size 20**.

That matters because:

- Bulkhead A is HDP24-24-47, a 16/20 arrangement. Both halves need size-20
  contacts for the small-gauge cavities.
- Plan 6.40 specs 26 more size-20 sockets for the CSB3 box.
- DigiKey showed 0462-201-2031 at zero stock on 2026-09-21.

So size-20 contacts are a real buy, in quantity, from TE direct. Bulkhead B
(HDP24-24-21, 12/16) is fully covered by what is already here.

### An HD30 pair is already on the shelf, unassigned

`HD34-24-21SN` receptacle + `HD36-24-21PN` plug - shell 24, 21 positions,
contact sizes 12/16. Nothing in the looms claims them.

Twenty-one ways covers the CSB3's 14 used terminals plus 7 spare exactly, and it
takes the size-16 contacts already in stock instead of 26 size-20 that are not.
Two things to weigh before adopting it in place of the 6.40 HD34-24-33PE /
HD36-24-33SE pair:

- **Gender is flipped.** This pair puts sockets on the box and pins on the
  harness. 6.40 deliberately chose pins on the box so the live 12 V side is
  shrouded when unplugged.
- **No room to bring out all 26.** 6.37 brings out the 12 unused CSB3 channels so
  a spare never means opening the box. Twenty-one ways gives 14 + 7 instead.

Daniel's call. Flagged, not decided.

### Other unassigned stock worth remembering

- `YD369-MP33-NP00000` / `YD369-MR33-NS00000` - 369 three-way **shielded** pair
  with a tie-wrap backshell. A candidate for a screened VR sensor drop.
- `HDP24-24-9PE` / `HDP26-24-9SE` x2 - 9-way E-seal, sizes 4/8/12. Heavy pass-through.
- `HDP24-18-6PN-C030` / `HDP26-18-6SN-C030` - 6-way size 4.
- `DT04-12PA` / `DT06-12SA` x2 with wedgelocks - 12-way Deutsch DT.
- `1416010-1` (HCR150) x2 - the EPS pump relay, loom C.

## Rules

- Edit the CSV only. Do not hand-edit generated buy lists - re-run `buylist.py`.
- A part number in a `.harness` file must exist here, or the BOM row must say why
  it is being bought new.
- When a part is consumed by a build, note it - do not silently decrement.
