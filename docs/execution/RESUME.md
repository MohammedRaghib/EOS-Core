# RESUME — how to start a session

Copy the block below into a new chat session. It is deliberately short and it hardcodes **no task
ID**, so the same text works after any session: the new session works out the next task itself.

```
Read AGENTS.md, then do exactly one task and commit it.

1. `git status` — if anything is dirty, that is unfinished work from a previous
   session. Finish or commit it first; do not start something new on top of it.
2. `git log --oneline -5` — the last commit names the task that just finished.
3. `docs/TODO.md` — pick the top unblocked open item by the queue's own order
   (block order, S1 first).
4. If that item has `docs/execution/<ID>.md`, read only that file and start at its
   `## Current Task`.

Do not read roadmap.md or architecture.md until the task needs a specific part of one.

Context: start at 30%+ and finish below 70%. If you cross 70% mid-task, stop,
commit what works, and point the plan's `## Current Task` at the next piece.
Never let compaction swallow a half-finished edit.

One task per session. Then update the plan (status, `## Completed` with the real
output, `## Current Task`) and commit with the task ID in the message.
```

## Why it is built this way

Four choices, each of which is a failure mode it prevents:

1. **It starts from `git status`, not from the docs.** A dirty working tree is the real answer to
   "where were we", and it is the one thing a plan file can be wrong about. `docs/TODO.md` and the
   plan are read *after* the state of the tree is known.
2. **It hardcodes no task ID.** A prompt that says "do `UI-1.2`" is a lie the moment that task is
   done, and a stale prompt is worse than none. The session derives the task from
   `git log` + `docs/TODO.md` instead.
3. **It forbids the up-front doc reads.** `TODO.md` + `architecture.md` + `roadmap.md` + `AGENTS.md`
   is roughly 35K of a 200K window — a sixth of the budget, and compaction fires at 70% — spent
   before a line of code is written. The docs are still authoritative; they are just read on demand.
4. **It says what to do at 70%.** Without that, a session at 68% keeps editing and lets compaction
   swallow a half-finished diff. Committing and re-pointing `## Current Task` is the whole point of
   keeping plans.

The rules are not restated in the prompt because `AGENTS.md` is already loaded into every session.
Repeating them costs context twice and gives the agent two versions to reconcile.

## Also worth doing

- **Check the context percentage before picking a task, not during one.** The number at the start
  decides whether one task fits; the number mid-task is too late to act on. See *The context budget*
  in [`README.md`](README.md).
- **Delegate wide reads** — whole DocType JSONs, whole test files, `architecture.md` sections — to a
  subagent and take the `file:line` answer. The read is what fills the window, not the edit.
- **End the session deliberately.** Stopping at 40% with everything committed costs nothing. The next
  session starts at 0% and loses nothing.

## If a task turns out to be too big

Stop, do not push on. Split it in the plan (`UI-1.4a` / `UI-1.4b`), give each its own acceptance
criteria and verification, point `## Current Task` at the first, and record the reason under
`## Discovered Issues`. Then end the session there. A split is a normal outcome; a task that crosses
70% half-done is not.
