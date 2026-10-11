---
name: pick-parts
description: Picks real part numbers for a harness/BOM need, in the project's binding sourcing order. Use when Dan asks "what part for X", "spec a connector/relay/terminal", or a build needs parts picked. Covers checking on-hand stock first, TE Connectivity and free-sample eligibility, the ratings that actually matter (relay, terminal/wire, feed-stud total current), and the OWN/BUY output format. Do NOT guess a part number — an unverified part is `TBD` plus the reason, never a guess.
paths:
  - docs/sourcing/te-on-hand-bom.csv
  - docs/sourcing/README.md
  - docs/harness/NEED-TO-BUY.md
---
# pick-parts

## Where to run
- Repo root, `C:\projects\active\st185-link-ecu-config`. Shell: PowerShell.

## Critical
- Selection order is binding (`docs/sourcing/README.md`): **(1)** what Dan already owns — `docs/sourcing/te-on-hand-bom.csv` — wins even over a "better" part, checked first, every time. Never ask Dan for a count; read the CSV. **(2)** TE Connectivity, preferring parts TE offers free samples on. **(3)** anything else, only then, with the BOM row saying why nothing above fit.
- `qty_ordered` in the on-hand CSV is what was ordered, not a live shelf count — treat it as an upper bound and flag it for confirmation rather than assuming it's available.
- What matters for ratings: the relay (coil + contact rating), the terminal/pin and wire-gauge range of the connector's contacts — not the box/shell itself — plus a total-current check on the feed stud for anything sharing one.
- Never invent or guess a part number. A part not checked against a datasheet/catalog gets `TBD ...` and the reason (`docs/harness/README.md` Parts rule 4).
- Note a part as consumed when a build uses it — don't silently decrement the on-hand CSV.

## Instructions
1. Check `docs/sourcing/te-on-hand-bom.csv` for a part that already does the job. If one fits, use it — stop here for that line item.
2. If nothing on-hand fits, search the TE Connectivity catalog for a compatible part; mark it free-sample-eligible if it is.
3. Only if TE has nothing compatible, consider another maker, and say why in the BOM row.
4. Run the ratings that matter: relay coil/contact rating against the load, the contact's wire-gauge range against the actual wire (combined gauge for a splice), and a total-current check on any shared feed stud.
5. Output an `OWN ×n` / `BUY ×n` table plus a price card with "est." prices, each sourced (datasheet, catalog page, or on-hand BOM row).

## Verification
- Every part number in the output is either in `te-on-hand-bom.csv`, a cited TE catalog entry, a cited other-maker entry with a stated reason, or `TBD` with a reason — none are guessed.
- The OWN/BUY table accounts for every line item in the request.
