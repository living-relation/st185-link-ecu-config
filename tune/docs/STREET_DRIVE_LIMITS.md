# Street shakedown (startup map only)

Brief drives while validating the **base map** — not a performance tune plan. Adjust tables in PCLink as needed; this doc is operator discipline for the first outings only.

## Boost / load

| Parameter | Street cap |
|-----------|------------|
| Max boost target | **18 psi** (base map seed) |
| Overboost ECU cut (v1 base) | **32 psi** loose — tighten to ~29 psi after dyno (`limits.yaml`) |
| Max TPS duration | Avoid sustained WOT below 3500 RPM |

## RPM

| Phase | Limit |
|-------|-------|
| First outing | 4500 RPM hard |
| After oil temp stable + no knock | 6000 RPM |
| Pre-dyno max | 7000 RPM unless dyno scheduled |

Rev limit table set to **8000** in config — use lower **GP RPM limit** tables until tuned.

## Lambda

- Idle/cruise: 0.92–1.00  
- Partial boost: ≥0.85  
- WOT (when allowed): 0.82–0.88 on 93; richer on high E85%

Pull boost if lambda lean >1.0 under any positive MAP.

## Knock

- v1 ECU knock **cut** threshold is intentionally high — expect retard/logging before cuts.
- Any sustained knock retard >3° under load → lift throttle, note log, fix fuel/ign before tightening limits.

## Fluids / temps

- Oil temp: return to garage if **>230°F** sustained (ring hints at 235).  
- Coolant: gauge color shows heat; ECU **limit** shuts engine off (see `limits.yaml` `ect_f`) — no separate overheat warning.  
- Fuel: keep ≥¼ tank for pump cooling on returnless rail.

## Traction / AWD

- TC enabled with conservative slip tables.  
- No standing-start launches until wheel speeds and gear logic validated on cluster.

## Checklist before each drive

- [ ] No CEL / Link fault codes  
- [ ] Boost map index = street (encoder 0)  
- [ ] Log armed (PCLink or external)  
- [ ] Fire extinguisher / tools per your track policy  
