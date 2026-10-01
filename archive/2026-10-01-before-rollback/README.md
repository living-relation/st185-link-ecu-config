# 2026-10-01 harness copies kept after main rollback

These are archived copies of harness drawings from commits that are no longer on `main`.
They are **not** the live drawings. Do not restore them under `docs/harness/`.

`main` was rolled back to `77a66d293357ce5087db6ad36960ff869384cca1`.
Nothing in this folder is authoritative.

| Folder | Source commit | What was copied |
|---|---|---|
| `from-main/` | `ab28d22a78bbb712d6971b1e9c4aba6069069af3` | Every `.harness` file that commit had under `docs/harness/` (`rebuild/`, `min/`), plus the shared `parts-library.json` export. Paths inside this folder keep the `docs/harness/` relative layout. |
| `pr40-wire-swap/` | `999ae089b4c8358695a629c3698ff5f42cb2c5a3` (closed pull request 40) | Only the `.harness` files that differ from `ab28d22`: `min` and `rebuild` copies of `ST185-ACAmp-Spur-1.harness` and `ST185-CabinPower-1.harness`. Same relative paths. |

Scripts, CSV lists, and markdown from those commits were not copied.
