# Throttle body plumbing — source files

Everything here supports `../../THROTTLE-BODY-PLUMBING-SPEC.md`.
Collected 31 August 2026.

## Vendor product records

| File | What it is | Source | Date of source |
|------|-----------|--------|----------------|
| `outsidergarage_74mm_hose_hd_clamp_adapter_product.json` | Full Shopify product record for the part Dan owns: title, description, all six variants, prices, weights, image list | outsidergarage.com, product handle `bosch-74mm-throttle-body-hose-and-hd-clamp-adapters` | Product created 2 Oct 2024, record last updated 31 Aug 2026 |
| `outsidergarage_hose_adapter_weld_on_flanges_product.json` | The separate weld-on version of the hose adapter. Only offered as "Bosch 82mm -> 3in". Dan did NOT buy this | outsidergarage.com, handle `bosch-e-throttle-hose-adapter-weld-on-flanges` | Product created 3 Jan 2026 |
| `outsidergarage_dbw_weld_on_flanges_product.json` | Weld-on manifold-side flange, offered in a Bosch 74mm variant. Dan did NOT buy this either | outsidergarage.com, handle `bosch-82mm-dbw-weld-on-flange` | Retrieved 31 Aug 2026 |

The last two are filed only to close them out. They are the products Dan was
thinking of when he remembered "a separate clamp with a weld flange". Neither is
on his order.

## Product photographs

All four are the vendor's own listing photographs for the 74 mm adapter.
Source: Shopify CDN, `cdn.shopify.com/s/files/1/0435/8979/6001/files/`,
uploaded by the vendor 9 October 2024, photographed 13 August 2024.
`.webp` files are the originals as downloaded. `.png` files are the same images
converted so they open in any viewer.

| File | What it shows |
|------|---------------|
| `OG_74mm_adapter_HDclamp_silver.webp` / `.png` | The exact variant Dan owns — 3" HD Clamp, Silver. Shows the flat radial clamp face, the O-ring, the four bolt ears and the four long yellow-zinc cap screws |
| `OG_74mm_adapter_HDclamp_black.webp` / `.png` | Same part in black. Clearer view of the clamp face profile |
| `OG_74mm_adapter_hose_silver.webp` / `.png` | The 3" Hose variant for comparison — plain straight barrel with a retaining bead instead of a clamp face |
| `OG_74mm_adapter_view2.webp` / `.png` | An adapter fitted to a Bosch throttle body, with a second adapter loose alongside. This is the picture that shows how the part mounts |

## Order record

| File | What it is | Source | Date |
|------|-----------|--------|------|
| `order-7870-line-items.md` | The three line items of order #7870, plus an index of every related Gmail thread that was checked | Gmail, thread `19b91aa70eff010b`, message `19b91bb8779f00ff` | Order placed 5 Jan 2026, email 6 Jan 2026 |

## Calculations

| File | What it is |
|------|-----------|
| `charge-pipe-math.py` | The velocity and pressure drop script. Uses real inside diameters, Colebrook friction factor, Borda-Carnot expansion loss |
| `charge-pipe-math-output.txt` | Its output, which is what the numbers in the specification are taken from |

Run it with `python3 charge-pipe-math.py`.

## Deliberately not here

- **The two manifold adapter PDF drawings.** They exist as Gmail attachments
  (`74mm Custom-DBW-Manifold-Adapter_DGrippin.pdf` in message `19b9465dca3e6e8e`,
  `Custom-DBW-Manifold-Adapter_copy (1).pdf` in message `19b91bb8779f00ff`).
  The Gmail connector in this session can see that they exist but has no tool to
  download the bytes, and neither file is on the local disk. Dan needs to save
  them out of Gmail by hand.
- **The STL file and the flange photographs** (`1000010061.jpg`,
  `1000010062.jpg`, message `19b946ae9a77aad9`) — same reason.
- **No personal information.** No addresses, no card details.

---

## Revision 2 additions — 31 August 2026

Added when the pipe sizing was reworked after Dan pointed out that he has not
bought any piping yet and that 3 inch throughout may not route.

| File | What it is |
|------|-----------|
| `pipe-sizing.py` / `-output.txt` | Velocity and pressure drop for 2.5 / 2.75 / 3.0 in OD at 0.065 in wall, hot and cold runs separately, on real inside diameters |
| `transition-and-packaging.py` / `-output.txt` | Transition cone lengths at 7 / 10 / 14 degrees included, and the outside diameter table for routing clearance |
| `transition-losses-and-system-dp.py` / `-output.txt` | Contraction and expansion losses for a 2.5 in cold side between two 3 in fittings, and total system pressure drop for each build option |

### Key facts established in revision 2

- **SpeedFactory SS-850 has a 3 inch inlet and a 3 inch outlet**, bead-rolled
  tube ends, 24 x 12 x 3 in bar-and-plate core, rated 600-850 hp.
- **Outsider Garage makes no 2.5 inch version of the throttle adapter.** From
  the saved product record, the only options are `3" Hose` and `3" HD Clamp`,
  in Silver, Black or Gold, all $135. Their whole Bosch range starts at 3 inch.
- **Vibrant 12516** is the HD clamp full assembly for 3.00 in OD tubing: clamp,
  two aluminium weld ferrules with O-rings, union sleeve, locking pin.
- The Vibrant HD clamp **outside diameter is not published** and the retailer
  page timed out. It remains an estimate and needs measuring on arrival.
