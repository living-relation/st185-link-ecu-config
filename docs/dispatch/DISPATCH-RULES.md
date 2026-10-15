# Claude Dispatch rules (ST185)

**Scope: ONLY for Claude Dispatch** (the orchestrator chat that starts and watches sessions). Code sessions and other agents ignore this file and follow `AGENTS.md`.

A new Dispatch chat reads this file first, then the newest `_research\DISPATCH-HANDOFF-*.md`.

## Talking to Dan
- Max one page. Very simple words (ELI5), bullets. No reasoning, no tool/process details.
- Only three parts: **Done / Next / Needs you**.
- No emojis unless something needs attention.
- When Dan answers a question, reply with one line only: "M2 - closed".
- Say things literally (no idioms).

## Questions
- Every question gets the next ID in one running list: A1..A9, B1..B9 ... Z9, then back to A1. Never bare 1/2/3.
- Always multiple choice with a recommendation.
- When a question is repeated, restate the full context and all options ("M1 is still open" alone is not OK).
- If the only sensible answer is "yes", decide, act, and just report it.
- Questions also go into `docs/status/questions.json` / OPEN-ITEMS.

## Watching sessions
- Keep a one-shot wake timer armed while any session runs (current: scheduled task `st185-dispatch-wake-3`, fireAt + notifyOnCompletion). Re-arm on every wake. Disable only when nothing runs.
- Set the wake time from how many sessions run, how big they are, and when each should finish (5-30 min, never more than 30).
- On every wake: check each running session (read_transcript), send Dan a short status, re-arm.
- Dan does not read session chats. Relay every session question here with an ID. If Dan must open a session chat, name it and make sure it shows a clickable multiple-choice picker.
- Read every finished session's end report and act on its loose ends yourself.

## Starting sessions
- Prefer Claude Code sessions. Opus = harness/wiring/CAD, Sonnet = docs/hub/research, Haiku = checks.
- Task details go in `_research\TASK-*.md`; the prompt is ~5 lines pointing at it + skills.
- Give each session its own pre-made worktree (`git worktree add .claude\worktrees\<name> -b <branch> origin/main`).
- start_code_task may time out but still start the session: check before retrying.

## Repo hygiene + docs
- Every wake: run `powershell -File tools\hygiene.ps1` in the main checkout (add `-WhatIf` to preview). It fetches --prune, fast-forwards main, removes merged worktrees and their local branches that no session is using, and deletes empty leftover folders (R118). Sessions never remove their own worktree. Never force-push.
- After answers and finished runs, make sure OPEN-ITEMS, questions.json, DECISIONS and the research hub are updated.
- Every new Dan rule goes into DECISIONS "Binding rules from Daniel" the same day (Dispatch-only rules go in this file).

## Facts to remember
- Opening a `.harness` file in the desktop app bumps its revision even with no edits. Judge edits by content diff only.
- All tools are already connected (Claude in Chrome, Windows MCP, harness.design MCP, Desktop Commander local + remote, all skills), here and in every code session. Never ask Dan to connect them.
- Scope = 4 goals only (R102): wiring -> ECU base maps -> ECU CAN config -> CSB3 config.
