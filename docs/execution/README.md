# Execution plans — AI-managed decomposition of `docs/TODO.md`

**Starting a new session? Copy the prompt in [`RESUME.md`](RESUME.md).** It hardcodes no task ID, so
the same text works after any session.

`docs/TODO.md` is the **work queue**: it says what is outstanding, at what severity, and in what
order. This directory says **how a single large item is built** without a context window running
out. The two are deliberately separate — a queue item is never re-described here, it is only
decomposed.

## The rule

| Situation | What to do |
|---|---|
| An open item in `TODO.md` has a file here | Execute its tasks in order. Never start more than one at a time. |
| An open item in `TODO.md` has **no** file here | It is small enough to do in one session straight from its `TODO.md` text. Follow the `Done when` line. |
| A task here turns out to be bigger than its own acceptance criteria | **Stop and split it here first**, then implement. See *Splitting a task* below. |
| A task is blocked by an item that is not done | Leave its status `TODO` and move to an unblocked task. Record the blocker. |
| Every task is `DONE` but the item is not in `TODO.md`'s *Done* table | Close it out — see *Close-out* below. |
| A plan and `TODO.md` disagree | **`TODO.md` wins.** Fix the plan, and say so under `## Discovered Issues`. A plan may break an item down; it may not restate it. |
| Implementing an item turns out to be impossible as written | Do not quietly narrow it. Record the finding in `TODO.md` as a scope note — the `DEBT-6` and `DEBT-7` items show the format — and keep the plan honest about the deviation. |

## The two boxes

An item is finished only when **both** boxes are ticked:

- `code+tests` — the logic exists and a passing test covers it.
- `reachable` — a real user reaches it in the browser.

`DOC-*` and `DEBT-*` items are internal-only by nature and carry no boxes.

## File layout

Every file uses the same skeleton, so a new session can navigate it blind:

```
## Parent TODO          the queue item, its severity, its "Done when"
## Objective            what is true when the whole plan is finished
## Dependencies         what must be closed first, and what this unblocks
## Decisions to settle  choices that must be made BEFORE the first task, with Ninety's evidence
## Execution Tasks       the actual engineering deliverables, each with Status / Scope /
                        Acceptance criteria / Verification
## Current Task         the single task in flight, or None — this is the resume point
## Completed            filled in per task as work lands, with what was verified
## Decisions            choices actually made, and why
## Discovered Issues    anything found that is not this item — new TODO IDs, not silent fixes
## Verification         the full evidence trail, baseline to close-out
## Completion           the item's Done-when clauses mapped to evidence
## Remaining Work       what is still open
```

**`## Current Task` is the resume point.** A session starting cold reads it, continues that task,
and rewrites it. Never leave it pointing at a task that is actually finished.

## Task sizing

One task must be finishable — understand, inspect, implement, test, verify — inside a single
context window, with the surrounding docs already read. A task is correctly sized when:

- it touches **one** subsystem (schema, or controller, or engine, or JS, or tests, or docs);
- it names concrete files, and they number in the low tens of lines, not the low hundreds;
- its acceptance criteria can be checked by running a command or a test, not by reading prose;
- no other task in the plan is a prerequisite for it beyond the plan's stated `Dependencies`.

### Splitting a task

If any of the above fails, do **not** start implementing. Add `UI-1.4a` / `UI-1.4b` to the same
file, give each its own acceptance criteria and verification, set `## Current Task` to the first
one, and record the reason under `## Discovered Issues`. Splitting is a normal outcome, not a
failure.

### The context budget

Compaction fires at 70% of the context window, and it is a **cliff, not a slope** — whatever was in
flight in the last 30% is what gets summarised away, and it will be the half-finished edit. So:

- **Start a task at 30% or above, and do not start one that cannot finish below 70%.**
- That is roughly 40% of the window. A DocType-level task here fits. `UI-1.2` does not.
- **One task per session** when in doubt. Five tasks in a session means five sets of file reads
  compounding, and the fifth is the one that dies.
- Delegate wide reads — whole DocType JSONs, whole test files, `architecture.md` sections — to a
  subagent and take the `file:line` answer. The read is what fills the window, not the edit.
- **Commit at every task boundary**, even a partial one, with the task ID in the message. This is
  what actually makes a post-compaction session safe: the next session reconstructs where it is
  from `git log` alone instead of trusting this file to be accurate.

### Good task

- Add the `archived` Check field to `To Do`, `Issue` and `Rock`, and register the patch.
- Implement `Scorecard.get_grid` reading metrics through `frappe.get_list` and entries through a
  single grouped query.
- Add the six role-gating tests for the Measurable Manager.
- Add the patch that creates the `(team, timeframe)` unique index on `Scorecard`, behind a
  duplicate pre-check.

### Not a task

- Investigate the codebase. · Understand the permission model. · Review the architecture. ·
  Plan the work.

Those are what the first ten minutes of a session are for. They are not deliverables and they do
not get a `Status`.

## Verification is not optional

Every task carries a `Verification` block with copy-pasteable commands. Run them and paste the
real result into `## Completed`. "Should work" is not a result, and neither is "the code reads
correctly". Where a task changes behaviour, **write or confirm the test that fails without the
change** before you make it, and say so.

A `*.json` edit — including a `permissions` block — requires `bench migrate` before the tests mean
anything.

## Close-out

When the last task is `DONE`:

1. Run the item's full verification command and record the count.
2. Tick both boxes in the item's `**Status**` line in `docs/TODO.md`, and add the SHA to the *Done*
   table there. Never delete the item body, never renumber, never renumber the section headers.
3. Set `## Remaining Work` to `None` and `## Current Task` to `None`.
4. Update `docs/architecture.md` only if the domain model or terminology actually changed.

## Index

### Block A — Correctness

| Plan | Item | Severity | Blocked by |
|---|---|---|---|
| [`DATA-3.md`](DATA-3.md) | `Rock`, `Issue` and `To Do` have no `archived` field | S2 | — |

### Block B — Permissions (all three open items are UI-blocked, not permission-blocked)

| Plan | Item | Severity | Blocked by |
|---|---|---|---|
| [`PERM-3.md`](PERM-3.md) | Team Members may reorder measurables they do not own | S2 | `UI-1` |
| [`PERM-4.md`](PERM-4.md) | Only Owner / Admin / Coach see the Measurable Manager | S2 | `UI-8` |
| [`PERM-5.md`](PERM-5.md) | Worksheet column visibility and status-colour toggles | S3 | — |

### Block C — UI

| Plan | Item | Severity | Blocked by |
|---|---|---|---|
| [`UI-1.md`](UI-1.md) | Scorecard grid (the core Ninety screen) | S2 | — |
| [`UI-2.md`](UI-2.md) | UI trigger for "Make it an Issue" | S2 | `UI-1` |
| [`UI-3.md`](UI-3.md) | "View by" dropdown wired to `get_rollup_view` | S2 | `UI-1` |
| [`UI-4.md`](UI-4.md) | Trends view | S3 | `UI-1` |
| [`UI-5.md`](UI-5.md) | Scorecard column toggles | S3 | `UI-1`, `PERM-5` |
| [`UI-6.md`](UI-6.md) | Bulk UX | S3 | `UI-1`, `DATA-3` |
| [`UI-7.md`](UI-7.md) | Buttons for the three built endpoints nothing can reach | S2 | `DEBT-11` |
| [`UI-8.md`](UI-8.md) | Measurable Manager — the only Ninety surface with no queue item | S2 | — |

### Block D — Parity

| Plan | Item | Severity | Blocked by |
|---|---|---|---|
| [`PARITY-1.md`](PARITY-1.md) | Add Existing Measurable + Duplicate | S2 | — |
| [`PARITY-2.md`](PARITY-2.md) | Auto-seeded default measurables | S3 | — |
| [`PARITY-3.md`](PARITY-3.md) | Set New Goal + Set Custom Goal | S2 | — |
| [`PARITY-4.md`](PARITY-4.md) | Backfilling | S3 | — |
| [`PARITY-5.md`](PARITY-5.md) | Lightning-bolt indicator on formula measurables | S3 | `UI-1` |
| [`PARITY-6.md`](PARITY-6.md) | Connectors (Jira, Salesforce, Google Sheets) | S3 | — |

### Block F — Code debt

| Plan | Item | Severity | Blocked by |
|---|---|---|---|
| [`DEBT-6.md`](DEBT-6.md) | Three empty controllers with no tests | S3 | — |
| [`DEBT-7.md`](DEBT-7.md) | Five DocTypes enforce uniqueness only in Python | S3 | — |
| [`DEBT-9.md`](DEBT-9.md) | Formatting debt | S3 | — |

The remaining open items — `DOC-3`, `DEBT-1`, `DEBT-2`, `DEBT-4`, `DEBT-5`, `DEBT-8`, `DEBT-10`,
`DEBT-11`, `DEBT-12` — have **no** plan on purpose: each is a single-session change with a
one-line `Done when` in `docs/TODO.md`. `DEBT-12` closes as part of `DEBT-7`, and `DEBT-11` is a
prerequisite of `UI-7`.

## Archived plans

| Plan | Item | Closed | SHA |
|---|---|---|---|
| [`PERM-9.md`](PERM-9.md) | `EOS Metric.owner` is Frappe's creator, so a Measurable's owner is fixed | 2026-09-29 | `e00011d` |

A closed plan stays in this directory. It is the record of how the item was actually built,
including the bugs found on the way and the traps it walked into.

`PERM-9.md` predates the conventions above — it uses `- Status: DONE` rather than `- **Status**`,
and `## Decisions taken before implementing` rather than `## Decisions to settle`. **Do not
"correct" it.** Its value is that it is the record of a real session, and rewriting a closed plan to
match a convention invented afterwards destroys the evidence.
