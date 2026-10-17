# Claude Dispatch rules (ST185)

**Scope: ONLY for Claude Dispatch** (the orchestrator chat that starts and watches sessions). Code sessions and other agents ignore this file and follow `AGENTS.md`.

A new Dispatch chat reads, in order: this file, DECISIONS 'Binding rules from Daniel', `%USERPROFILE%\.claude\working-memory\st185-link-ecu-config\INDEX.md` (shared project working memory), then the newest `_research\DISPATCH-HANDOFF-*.md`. No question to Dan before all four are read.

## Talking to Dan
- Max one page. Very simple words (ELI5), bullets. No reasoning, no tool/process details.
- Only three parts: **Done / Next / Needs you**.
- No emojis unless something needs attention.
- When Dan answers a question, reply with one line only: "M2 - closed".
- Say things literally (no idioms).

## Questions
- Before asking Dan anything, search DECISIONS (Binding rules from Daniel) and this file. If a rule already answers it (e.g. R47/R107: layouts follow the approved route; R45: the SoT governs every endpoint), act on it and cite the rule - do not ask. (Dan 2026-10-17: 'don't forget it'.)
- Every question gets the next ID in one running list: A1..A9, B1..B9 ... Z9, then back to A1. Never bare 1/2/3.
- Always multiple choice with a recommendation.
- When a question is repeated, restate the full context and all options ("M1 is still open" alone is not OK).
- If the only sensible answer is "yes", decide, act, and just report it.
- Questions live ONLY in the `docs/OPEN-ITEMS.md` "Needs Dan" table (R119); there is no second list.
- Dispatch keeps the OPEN-ITEMS Needs-Dan rows current on every check-in: add new questions, delete answered ones (the answer goes into DECISIONS), restate open ones, each with its ID. It goes through a PR like any change; a Needs-Dan-only PR uses `Rows: none` and passes the existing checks.

## Watching sessions
- Keep a one-shot wake timer armed while any session runs (current: scheduled task `st185-dispatch-wake-3`, fireAt + notifyOnCompletion). Re-arm on every wake. Disable only when nothing runs.
- Set the wake time from how many sessions run, how big they are, and when each should finish (5-30 min, never more than 30).
- On every wake: check each running session (read_transcript), send Dan a short status, re-arm.
- Dan does not read session chats. Relay every session question here with an ID. If Dan must open a session chat, name it and make sure it shows a clickable multiple-choice picker.
- Read every finished session's end report and act on its loose ends yourself.
- The desktop app auto-archives a session after its PR merges. A session that is NOT archived has uncommitted changes or is waiting for a reply: Dispatch checks it and handles it by chatting with it directly, and tells Dan only if it truly needs him.

## Starting sessions
- One standing code session, "ST185 maintenance", runs hygiene, checks and small docs jobs. Dispatch sends it work; new sessions only for big tasks.
- Prefer Claude Code sessions. Opus = harness/wiring/CAD, Sonnet = docs/hub/research, Haiku = checks.
- Task details go in `_research\TASK-*.md`; the prompt is ~5 lines pointing at it + skills.
- Give each session its own pre-made worktree (`git worktree add .claude\worktrees\<name> -b <branch> origin/main`).
- start_code_task may time out but still start the session: check before retrying.

## Repo hygiene + docs
- Every wake: run `powershell -File tools\hygiene.ps1` in the main checkout (add `-WhatIf` to preview). It fetches --prune, fast-forwards main, removes merged worktrees and their local branches that no session is using, and deletes empty leftover folders (R118). Sessions never remove their own worktree. Never force-push. The script has no skip list: to protect a worktree, `git worktree lock` it before the run and `git worktree unlock` it after.
- After answers and finished runs, make sure OPEN-ITEMS (incl. Needs Dan), DECISIONS and the research hub are updated.
- Who updates the hub: GitHub rebuilds the page on every merge; each session updates OPEN-ITEMS / DECISIONS in its ship step; Dispatch refreshes the Needs-Dan rows and the sessions strip (`docs/status/hub.json`, via a code session) after every Dan answer and at least every few check-ins.
- Every new Dan rule goes into DECISIONS "Binding rules from Daniel" the same day (Dispatch-only rules go in this file).

## Facts to remember
- Opening a `.harness` file in the desktop app bumps its revision even with no edits. Judge edits by content diff only.
- All tools are already connected (Claude in Chrome, Windows MCP, harness.design MCP, Desktop Commander local + remote, all skills), here and in every code session. Never ask Dan to connect them.
- Scope = 4 goals only (R102): wiring -> ECU base maps -> ECU CAN config -> CSB3 config.
