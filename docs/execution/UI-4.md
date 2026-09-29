# UI-4 — Trends view

## Parent TODO

`UI-4` — **S3** · Trends view.
Block C (Phase 7: UI).

**Scope** (verbatim from `TODO.md`): Ninety's read-only, filterable list narrowed to off-track
measurables. Only the `count_consecutive_off_track` helper exists today.

## Objective

A read-only, filterable list of measurables that are trending off track, built on the trailing
off-track count that `count_consecutive_off_track` already computes, reachable in the browser for
any user who can see the underlying measurables — and never showing a row the user is not allowed
to see.

## Dependencies

- **`UI-1`** — the Trends view is a sibling view on the same page, over the same data, with the same
  role scoping. Building it against the grid's endpoint and shell is far cheaper than a second
  surface.
- `count_consecutive_off_track` exists in `eos_core/scorecard_engine.py` and is unit-tested. This
  item is mostly a query-and-render job, not a logic job.
- `build_scorecard_report` already computes a trend per metric against a `trend_threshold=3`
  default, and `ScorecardReport` uses it for the weekly email. Reuse its shape rather than
  inventing a second vocabulary for "trending".

## Decisions to settle before implementing

1. **Ninety's Trends view is read-only and filterable.** It is a *list*, not an editable grid. Do
   not add inline editing — that is the grid's job and duplicating the write path invites the
   `UI-1.2` permission bypass all over again.
2. **What "trending" means must be a parameter, not a constant.** `TREND_THRESHOLD = 3` in
   `scorecard_report.py` is the email's threshold. Ninety's Trends view is a filter, so the threshold
   belongs in the query, defaulting to whatever Ninety documents — **check Ninety's current docs
   before fixing the default**, per `AGENTS.md`'s standing rule that behavioural questions are
   resolved from Ninety, not from the tidier design.
3. **"Narrowed to off-track measurables" means the default filter, not a hard filter.** A filterable
   list with an on-track-off toggle is closer to Ninety than a list that can only ever show one
   thing. Confirm against Ninety's page before building.
4. **Read through `frappe.get_list`.** Same rule as `UI-1`: a Trends view built on `get_all` leaks
   other teams' measurables regardless of how carefully the grid is scoped.

## Execution Tasks

### UI-4.1 — Server: a trends query endpoint
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/scorecard/scorecard.py` (a second whitelisted method next to
  `get_rollup_view`, or a new `eos_core/api.py` if the controller is getting crowded), reusing
  `count_consecutive_off_track` and `scorecard_summary`. Tests: `test_scorecard.py`.
- **Acceptance criteria** the endpoint returns, per measurable the caller may see, the trailing
  off-track count, the last completed period's status and the status indicator; it accepts a
  threshold and an `as_of`; it excludes `archived = 1`; it sorts by the count descending.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  ```
  A cross-team permission test is required, in the same shape as `UI-1.1`'s.

### UI-4.2 — The Trends view in the browser
- **Status** `TODO`
- **Scope** the grid page from `UI-1`; a tab or a toggle between "Scorecard" and "Trends".
- **Acceptance criteria**
  - a read-only list: Measurable, Owner, Group, trailing off-track count, last status, indicator;
  - filters: threshold, group, status;
  - empty state distinguishes "nothing is trending" from "nothing is visible to you";
  - an `Observer` sees the rows for their own teams only;
  - no cell is editable.
- **Verification** manual browser pass at two roles and two teams, recorded in *Completed`.

### UI-4.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` (the "no UI" bullet in §7), `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs record what Ninety's Trends view does that this one does, and any
  difference, rather than claiming parity; `TODO.md` moves `UI-4` to *Done* with the SHA and both
  boxes ticked.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`UI-4.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

None yet.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All three tasks.
