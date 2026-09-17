# ECU limits — startup map only

## Context

This note applies **only while building `st185-furyx-base-v1.pclx`**. After you are in PCLink, set and track limits there — not in this repo or Excel.

## Startup map policy

Limits in `config/limits.yaml` → `ecu_limits` are **loose / high** so bad VE/ign/lambda tables do not false-cut the engine during first fire and idle.

| Limit | Startup value (v1) |
|-------|-------------------|
| Overboost cut | 32 psi |
| ECT hard cut | 265°F |
| Oil pressure cut | 5 psi @ RPM >4500 & MAP >120 kPa |
| Fuel / coolant pressure cut | Off |
| Knock cut | High threshold — severe only |

Cluster gauge colors are cosmetic and unchanged.

## Not in scope for this project

Tightening limits for full boost, track, or peak power — that is normal PCLink work on the dyno or street, using PCLink logs and tables. The `*_tuned_ref` fields in `limits.yaml` are **hints for later**, not something to implement in the startup deliverable.
