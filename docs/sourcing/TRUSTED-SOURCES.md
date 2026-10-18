# Trusted sources - non-maker short list

Living list (Dan, 2026-10-18; DECISIONS R167). **Maker data always wins**: the maker's spec sheet, customer drawing,
application spec or official 3D model (a maker sheet hosted on a listing site counts). This list is only for the
non-maker sources used when no maker sheet exists, and for availability / price.

## How to use it

- A part spec read on a non-maker listing is validated against the maker's sheet (usually a PDF) before it is used.
- No maker sheet: use a source on this list with the right tag. Not on the list either: confirm the spec with two more
  independent sources. Search-engine result snippets never count.
- Terminal wire ranges (AWG / mm2 min and max) are often wrong off the maker's site: always validate them. Terminals rarely
  take one gauge; if only one gauge seems to fit, look again or look for the sibling part number.
- A vendor's "recommended / compatible parts" list is a fine place to start; its parts still need validating unless the
  vendor is on this list with that tag.
- Once a part number is validated, also search it on Amazon, AliExpress and eBay for cost and availability (shopping only:
  the listing's specs are not used).

## Trust ranks

- **1** - its data for the tagged categories can be used as it stands (still loses to maker data).
- **2** - usable after one independent cross-check.
- **3** - leads only (part numbers, prices, stock); every spec is validated against the maker.

Tags: terminals, connectors, relays, fuses, CAD models, cross-reference, availability.

## Sources

| Source | Rank | Tags | Checked against maker data | Notes |
|---|---|---|---|---|
| TE "Shop our distributors" panel on te.com product pages (TTI, Mouser, DigiKey, Online Components stock and price) | 1 | availability | It is on the maker's own page | 2026-10-18: 1-968851-1 TTI 976,500 at $0.096, Mouser 710,500 at $0.101, Online Components 252,000 at $0.094; 1-968849-1 Mouser 298,113 at $0.250 (qty 1) / $0.139, DigiKey 90,314 at $0.129, TTI 67,500 at $0.082. Prices / stock only. |
| Ballenger Motorsports (bmotorsports.com, also Dan's approved supplier "B Motorsports") | 3 | terminals, connectors, availability | 2026-10-18, CONN-100329 "Tyco TE MCP 2.8 (280) Female Terminal, 1.25-2.5mm2" / spec tab "16 - 14 AWG": names no TE part number; TE's own data for the matching part 1-968851-1 says 1.0 - 2.5 mm2 (DIN) and 16 / 14 AWG crimp data (TE 114-18148 Rev D1 Table 7) - the mm2 range differs. Sister parts CONN-100328 "0.5 - 1.25 mm2" vs TE 1-968849-1 0.5 - 1.0 mm2. | Good for finding the family and buying small lots; never for ranges. Its "Associated & Mating Parts" tab is a starting list only. |

## Tried, not usable (not ranked)

- Octopart (availability / cross-reference): 2026-10-18 the part pages answer automated reads with a CAPTCHA, so nothing
  was checked there. Add it here with a rank once a person has checked it against maker data.

-- Claude Code, 2026-10-18
