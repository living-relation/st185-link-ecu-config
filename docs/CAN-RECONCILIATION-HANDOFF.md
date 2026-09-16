# Handoff: CAN reconciliation pass — RealDash and Link ECU

Agent-agnostic work order. Any agent — Claude Code, Cursor, Codex — can execute this. Read
`docs/RECONCILIATION-RULES.md` Rule 2 first; this handoff is one application of it.

Two tasks. They can be done in either order, but neither is complete on its own.

---

## Task 1 — Does the last-flashed RealDash config still match our CAN contract?

**Question to answer:** the RealDash configuration currently running on the Pi was flashed at
some point. Has the CAN contract moved since? If yes, RealDash needs a reflash.

**Inspect:**

| File | What to take from it |
|---|---|
| `st185_dash.rd` | The actual flashed dashboard file — binary layout format |
| `link_g4x_realdash.xml` | RealDash's CAN input definition: frame IDs, offsets, widths, scaling |
| `rd-build/` | Build inputs for the above |
| `REALDASH-LAYOUT.md` | What the layout is supposed to show |

**Compare against:**

- `link_g4x_can_setup.json` and `.lcs` — what the ECU actually transmits
- `CAN-BUS-ID-ALLOCATION-TABLE.md` — the master byte map
- `CANBUS-ENCODE-DECODE-REFERENCE.html` — read-only copy of the cluster's own decode logic

**For every frame RealDash consumes, confirm:** frame ID, byte offsets, field widths,
endianness (BigEndian unless stated), scaling, offset, units.

**Known contract points to verify specifically** — these are the ones most likely to have
drifted:

- MAP, not MGP, on `0x3E8` bytes 2-3.
- Oil pressure `0x3E9` bytes 3-4, uint16 big-endian.
- Fuel pressure `0x3E9` bytes 5-6, uint16 big-endian.
- Coolant pressure `0x3F0` bytes 2-3, uint16 big-endian.
- Turbo speed raw ×1000, range 0-255,000 RPM.
- **Cabin temperature was removed** from the ST185 RealDash inputs. If the flashed file still
  expects it, that is a real mismatch. Restoring it would need a new ECU frame such as `0x3F2`.
- RealDash receives ECU-owned `0x3EF`-`0x3F1` and must **not** read switchboard
  `0x640`-`0x642` directly.

**Deliverable:** a table of every RealDash-consumed frame — matches / mismatches — and a
yes/no on whether a reflash is required. If yes, say exactly which fields changed.

---

## Task 2 — Link ECU CAN configuration checkup

**Question to answer:** is the ECU's CAN configuration in agreement with RealDash, the center
cluster, and the ECUMaster CSB3?

**Inspect:** `link_g4x_can_setup.json`, `link_g4x_can_setup.lcs`, `CANBUS-LINK-G4X-CONFIG.md`,
`CAN-CONFIG-STATUS.md`.

**Reconcile against all three consumers:**

1. **Center cluster** — `center-cluster-esp32-p4` repo, `main/canbus.c` and
   `main/protocols/link_g4x.json`. Checked out at
   `C:\projects\shipping\center-cluster-esp32-p4`.
2. **RealDash** — as Task 1.
3. **ECUMaster CSB3** — `ECUMASTER_SWITCHBOARD_SETUP.md`.

**Also check** the known-open correction in `docs/ECU_DOCUMENTATION_HANDOFF.md`: the free-byte
summary in `CAN-BUS-ID-ALLOCATION-TABLE.md` says `0x3E9 bytes5-7` but should say
`0x3E9 byte7`, because bytes 5-6 carry fuel pressure. Confirm whether that was ever applied,
and recalculate the stated total free bytes if not.

---

## Hard constraints

- **The center cluster firmware is frozen.** It is the highest authority. When a conflict is
  found, the *other* device changes. A cluster reflash is a last resort and needs explicit
  approval from Daniel — never reflash it just to clear a mismatch.
- **Link CAN-Lambda is on CAN bus 1**, with everything else.
- **CAN bus 2 is unused.** Its ECU pins are free for any purpose — do not reserve them, and do
  not propose moving anything onto CAN 2 to solve a bandwidth or conflict problem without
  asking first.
- Single bus, 1 Mbit/s.

## Output

Write findings as a new dated record in `docs/` (e.g. `docs/CAN-RECONCILE-YYYY-MM-DD.md`),
following the existing frozen-record convention: dated, not updated afterwards. Any mismatch
found and not fixed in the same pass goes into that record as an explicit open item — never
left silent.

Do not change any CAN configuration as part of this pass without checking with Daniel first.
This is an inspection, not a repair.
