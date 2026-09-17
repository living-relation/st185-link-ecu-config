# Cluster firmware — status

**Clusters are done for this project.** Flash from `center` / `left` / `right` cluster repos on `main`.

## CAN contract (ECU must mirror)

- TX: **0x3E8, 0x3E9, 0x3EA, 0x3EB, 0x3EE** (0x3EE **bytes 0–5 only**)
- RX: **0x3EC, 0x3ED**
- Source of truth: `center-cluster-esp32-p4/link_g4x_can_setup.json`

## Red ECU WARNING box (already programmed)

Right cluster `ui_warning.c` shows only:

KNOCK · IGN CUT · FUEL CUT · BOOST CUT · SENSOR ERR · THROTTLE ERR

from `g_dash.warn` (CAN 0x3EE → center → UART).

## Gauge colors (already programmed)

Local cluster logic only. **Not** ECU alarms. **Not** additional CAN bytes.

## No further cluster work required for base tune

Unless you change the CAN map in the center repo, ECU PCLink setup is: import `link_g4x_can_setup.lcs` and map the six 0x3EE bytes to Link cut/limit sources.

Do **not** add 0x3EF, extended 0x3EE bytes, or redundant alarm channels for gauge conditions.
