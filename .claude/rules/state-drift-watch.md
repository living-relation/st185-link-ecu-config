---
description: How the state drift watcher's findings are fixed (always on)
---
# State drift watcher (Dan 2026-11-23)

- A scheduled check-in in the coordinator chat runs `<Projects>\_tools\state-drift-watch.py --repo <this repo>` on Dan's PC every 4 h. Each run pulls the workstation repo first (ff-only), so it checks against the latest workstation-core state rules and tools, and re-reads any template file that changed.
- The watcher is read-only: it prints findings and never edits the repo or the store.
- The coordinator fixes every finding in the next PR without asking Dan, names them on a `Watch:` line in the PR body, and tells Dan in the reply as a note, not a question.
- A finding that would change a SoT data file, the master wire list or SPEC waits for Dan's yes (a BACKLOG line marked `needs owner yes`).
- A repo decision beats the template where DECISIONS says so (example: the one-line `CLAUDE.md`, Dan B2 a); the watcher skips those.
- Enforcer: the watcher itself; no gate.
