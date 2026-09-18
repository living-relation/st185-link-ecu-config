# ST185 Residual Cluster LED Face

**Vehicle:** 1991 Celica GT-Four ST185 (AllTrac), race build. OEM combination meter removed.
**SoT:** Residual dash-harness stubs only (splice C10/C11/C12 wires — not meter PCB).
**Status:** Living face on `pass-a-bh-c-delete-locks` (2026-09-18).

## Scope

12V LEDs on the custom cluster that tap body / alt / Link→CSB:

| LED | Drive | Stub / path |
|---|---|---|
| High beam | Body residual | **C11(B)12** **R–L** (high-beam feed) |
| Turn LH | Body residual | **C11(B)2** **G–B** (flasher LH) |
| Turn RH | Body residual | **C11(B)11** **G–Y** (flasher RH) |
| Park brake | Body residual | **C12(C)1** **R–G** (grounds via P1 / B2 fluid) |
| Charge / batt | Alternator **L** (OEM) | **C12(C)9** **B–O** = IG feed · **C12(C)8** **Y** = alt **L** |
| Low oil pressure | Link → CSB low-side | `0x3F1` bit4 → CSB `0x643` LS (active-low / GND switch) |

**Not on this face:** low-fuel LED (scrapped). Fuel float + `r_fuellvl` 470 Ω is level-only (An Volt 9 / B24).

## Charge LED + alternator sense (detail)

OEM charging (EWD): alternator has **B**, **IG**, **L**, **S**.

```
IG (+12 switched) ──► C12(C)9 B–O ──► [12V charge LED] ──► C12(C)8 Y ──► alt L
                                                                    │
                         Regulator grounds L → LED ON (not charging)
                         L near battery when charging → LED OFF

Battery sense: alt S ──► battery + (sense / voltage feedback to regulator)
B+ output:     alt B ──► starter B+ / charge cable (heavy DC; see Power harness)
```

Custom cluster: same series path — IG feed stub → LED anode side → L stub to alternator. **No CSB bit** for charge if the 160 A alt still has an **L** terminal.

Confirm on-car that the upgraded 160 A alternator still exposes **L** (and **S** / **IG** as required by that regulator).

## Oil LED (CSB)

```
Link sets 0x3F1 bit4 (Low Oil Press 2)
  → PCLink packs CSB low-side on 0x643
  → CSB LS out sinks LED cathode (LED anode to +12 IG)
```

CSB outputs are **low-side (GND switch)**. Verify LS channel assignment in `ECUMASTER_SWITCHBOARD_SETUP.md` before crimp.

## Related living SoT

- `docs/POWER-AND-COMMS-ARCHITECTURE.md` — power / CAN / LED summary
- `docs/WIRING-AUDIT-2026-09-18.md` — residual tap table
- `docs/harness/ST185-Signal.harness` / Power — mechanical harness (this face is LED-only)
- EWD charging / meter stub pages (1990 family; car is 1991)

## Harness.design

Residual LED harness face: **YES** (Daniel). Add a matching face in harness.design when convenient; this markdown is the interim diagram SoT until that face exists.
