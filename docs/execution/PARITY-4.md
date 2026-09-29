# PARITY-4 — Backfilling

## Parent TODO

`PARITY-4` — **S3** · Backfilling.
Block D (Ninety parity features with no representation at all).

**Scope** (verbatim from `TODO.md`): create periods that predate a Measurable's creation date.

## Objective

A user can create the reporting periods that predate a Measurable's start, so history is complete
from the beginning of the window rather than beginning whenever someone got round to adding the
Measurable — and a backfilled period with no data shows the same "no data" the engine already
defines, not a fabricated `0`.

## Dependencies

- None blocking. `is_period_complete`, `recent_completed_period_starts`, `rollup_periods` and
  `completed_period_statuses` already define "period" and "completed period".
- **`PARITY-3`** overlaps: a backfilled period may want a custom goal. If `PARITY-3` lands first, the
  backfill should populate the goal for the period it creates. If it has not, record that the
  backfilled periods inherit the Measurable's current goal, and revisit.
- `UI-1` gives a user a surface; not required for the server work.

## Decisions to settle before implementing

1. **A backfilled period with no value must be a gap, not a zero.** `AGENTS.md` records the locked
   decision: **empty completed intervals count against** the status indicator, and `compute_status`
   returns `On Track` when `target_value == 0`. Writing `0` into a backfilled entry would therefore
   read as *off track* against a positive goal, which is a fabricated result. The backfill must
   create the **row** with no `actual_value` (or not create a row and let the engine's interval grid
   report the gap) — decide which, and prove the indicator still says what it should.
2. **How far back, and to where.** `ROLLUP_RANGE_WEEKS = 13` is the rolled-up view's default window,
   not a backfill bound. A backfill needs an explicit from-period, bounded by something sensible and
   by the `Scorecard`'s own history.
3. **Permission.** Backfilling writes to `Scorecard Entry`, which is a child of `EOS Metric` whose
   write is governed by the parent's DocPerm. Per `PERM-7`, a `Team Member` may enter data — so a
   `Team Member` may arguably backfill. **Check Ninety** rather than assuming it is a Manager action.
4. **Idempotency is the whole feature.** Running it twice must not double the periods, and running it
   after data entry must not overwrite an entered value. That is the difference between a useful
   button and a data-loss bug.

## Execution Tasks

### PARITY-4.1 — The written behaviour, and the period set
- **Status** `TODO`
- **Scope** Ninety's current documentation for backfilling, recorded in `docs/architecture.md` §3c
  alongside the goal model from `PARITY-3.1`; plus a pure helper naming the periods a backfill would
  create, so the set is testable without a database.
- **Acceptance criteria** the documented behaviour is cited; the period set is a pure function of
  `(from_period, to_period, timeframe)` using the engine's existing `rollup_periods` /
   `period_bounds` / `advance_period`; the choice from *Decision 1* is written down.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  ./env/bin/python -c "import sys; sys.path.insert(0,'apps/eos_core'); import eos_core.scorecard_engine as e; print(e.BACKFILL_PERIODS_HERE)"
  bench --site resolv.localhost run-tests --module eos_core.test_scorecard_engine --site resolv.localhost
  ```
  Substitute the function name this task actually defines — it is a placeholder, not a test.

### PARITY-4.2 — The backfill action
- **Status** `TODO`
- **Scope** a whitelisted method on `EOS Metric` (or a small `eos_core/api.py`); tests in
  `test_eos_metric.py` and `test_permissions.py`.
- **Acceptance criteria**
  - creates one `Scorecard Entry` per period in range, with `week_start_date` and no `actual_value`,
    `is_manual` false;
  - is **idempotent** — a second run creates nothing and reports zero created;
  - never overwrites an existing entry's `actual_value`;
  - refuses a range that reaches into the future or before the `Scorecard` existed;
  - the resulting status indicator is unchanged by the backfill, because the new intervals are
    unscored — **this is the test that catches *Decision 1* being ignored**;
  - the action is refused to the roles Ninety refuses it to, per *Decision 3*.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Mutation check: write `0` into `actual_value` in the backfill and confirm the indicator test fails.

### PARITY-4.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md`, `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs state the bound, the idempotency guarantee and the gap-not-zero
  rule; `TODO.md` moves `PARITY-4` to *Done* with the SHA.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PARITY-4.1`. Nothing has been implemented; no task has been started.

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
