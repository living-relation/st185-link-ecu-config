# Interface and ownership convention

How a drawing shows a harness boundary, and where the facts harness.design cannot hold are
kept. Decisions behind it: [`DECISIONS.md`](DECISIONS.md).

## Where the metadata lives

harness.design rejects unknown keys ("Unrecognized key(s) in object"), so ownership data
cannot go in the `.harness` files. It lives in **`docs/harness/interfaces.json`**, read by
`docs/harness/model.py` and every gate that needs it. The `.harness` files stay pure
harness.design JSON.

## Endpoint types

| Type | How it is drawn | BOM |
|---|---|---|
| `real_connector` | A connector with a real `partId` and contacts or plugs in every cavity. | Counted on the one drawing that owns it. |
| `inline_interface` | Two real connectors of opposite gender, one on each harness, same cavity ids and the same signal text per cavity. No mate (mates stay inside one document). | Each half counted once, on its own harness. |
| `oem_flying_lead` | A `Loose` terminal, no part, whose `signal` reads `EWD <page> <connector>-<pin> <colour> <function> - <method>`. | Nothing. |
| `device_endpoint` | One `Loose` terminal per conductor, no part, `signal` naming the device and pin (`VRC_REAR_IN_L +`). The device is not drawn (harness.design "devices" rule). | Nothing. |
| `reference_only` | A `cp_xref` dummy: this harness populates one cavity of a connector another harness owns (an ECU pin, a CSB3 cavity, a bulkhead engine-plug cavity). Every one is listed in the registry's `references` with the owning harness and the reason. | Nothing. |

## Registry sections

- `harnesses` — every file in `rebuild/`, with the physical harness it is. A file not listed fails
  `validate_ownership.py`.
- `interfaces` — `id`, `type: inline_interface`, `pins` (cavity → function), and two `halves`, each
  `{harness, connector, role}` where `role` is `source` or `receiving`. The receiving harness owns
  the mating half. Optional `alsoDrawnOn` lists other harnesses that draw an excluded copy of the
  same half and wire some of its pins - used when one half's pins belong to both ECU letter looms
  (the front wheel-speed spur: FL on A23, FR on B21). Its wiring counts toward the half.
- `endpoints` — `device_endpoint` groups: `id` (`VRC_REAR_IN_L`), `harness`, `device`, `terminals`.
- `enclosures` — screen landings a device case joins internally (the VRC powered-device exception,
  `SHIELD-RULES.md` §6.30). The graph treats them as one node.
- `flyingLeads` — one per `Loose` terminal: `harness`, `terminal`, and `ewd`
  `{page, connector, pin, color, function, method}`. An unknown field is written `TBD` with the
  reason; `validate_oem_endpoints.py` lists every `TBD`.
- `references` — every `cp_xref` dummy: `harness`, `connector`, `realOn` (the harness that owns the
  real connector) and `reason`. An unlisted dummy fails `validate_ownership.py` (O4).
- `realConnectors` — connectors on OEM parts that the build physically plugs into (J/B2 dummy
  headers) and the CSB3 plug, so they are not mistaken for flying-lead candidates.
- `shieldBothEndsOk` — screens allowed a landing at both ends, each with its reason. Only screen
  continuations through an inline interface or a VRC enclosure belong here.
- `wheelSpeed` — the front/rear specification `validate_wheel_speed.py` checks.

## Rules the gates enforce

- Every conductor id is unique across all drawings (one owner per physical section).
- A connector drawn with a real part on more than one drawing has exactly one copy not
  `excludeFromBom` (legacy shared drawings only; new harnesses draw a thing once).
- Every inline interface has two halves on two different harnesses, the same cavity set, the
  same signal text per cavity, and every pin either wired on both halves or plugged on both.
- A conductor never crosses from one harness to another except through a declared interface,
  a bulkhead pair, or a registered `reference_only` cavity population.
- No device is drawn: no `cp_m8_*` VRC connectors, no CSB3 body, no OEM housing on a flying lead.
