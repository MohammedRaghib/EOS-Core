# PARITY-3 — Set New Goal + Set Custom Goal

## Parent TODO

`PARITY-3` — **S2** · Set New Goal + Set Custom Goal.
Block D (Ninety parity features with no representation at all).

**Scope** (verbatim from `TODO.md`): a goal from a date forward, and a custom goal for a single
period. This is distinct from the per-period *forecasting* that `roadmap.md` Phase 3 deferred.

## Objective

A Measurable's goal is no longer a single immutable number: it can be changed from a date forward,
and overridden for one period only. Status, the status indicator, the report snapshot, the rolled-up
view, the L10 review and the grid all read the goal **in effect for the period they are showing**, and
history is not rewritten by a future goal change.

## Dependencies

- None blocking. The engine is frappe-free and has `period_bounds`, `advance_period`,
  `is_period_complete` and `completed_period_statuses` to build on.
- **`PARITY-4`** (backfilling) overlaps: a backfilled period may want a custom goal. Sequence them so
  the goal model is in place before backfilling starts, or record the conflict explicitly.
- Independent of the UI items; the surface is `UI-1`'s grid, but the model and engine work is not
  blocked on it.

## Decisions to settle before implementing

1. **This is a new concept, not a field edit.** `EOS Metric.target_value` is a single `Float`, and
   `EOSMetric.validate` recomputes **every** submitted entry's status against it. A goal that varies
   by period therefore needs a new representation — a goal history (effective-from + target) or a
   per-period goal child table — and `compute_status`'s input changes shape. **Settle the
   representation before writing anything.**
2. **A goal change must not rewrite history.** If `target_value` becomes "the current goal", every
   past entry's status would flip the next time the Measurable is saved, because `validate` loops over
   all `entries`. That is a silent data corruption path, not a feature. The engine must resolve the
   goal **as of each entry's `week_start_date`**. This is the single most important constraint in the
   item.
3. **Set New Goal is a *future* change; Set Custom Goal is a *single period* override.** Both are
   recorded in the same history with different semantics, and a custom goal for a past period is
   **not** the same thing as setting a new goal from that date. Decide whether the two share one table
   with a kind, and what happens if a custom goal overlaps a later "from" date.
4. **Verification parity with Ninety first.** Per `AGENTS.md` § Ground rules, the two actions'
   documented behaviour — what the UI says, whether a custom goal replaces or supplements the goal,
   what the trend history shows across a change — is to be read from Ninety's current docs, not
   designed here. `roadmap.md` records that per-period *forecasting* was deferred; do not let that
   deferral leak into this item.

## Execution Tasks

### PARITY-3.1 — The written goal model
- **Status** `TODO`
- **Scope** a new `docs/architecture.md` subsection recording: Ninety's documented behaviour for both
  actions, the chosen representation, the resolution rule "goal as of period X", the overlap
  semantics from *Decision 3*, and every existing consumer the change touches. No code.
- **Acceptance criteria** the subsection names the resolution function's signature and the list of
  consumers (`EOSMetric.validate`, `Scorecard._rollup_metric`, `ScorecardReport._build_metric_block`,
  `build_scorecard_review_lines`, the grid). The rest of the plan is implementable from it.
- **Verification** read back by someone who did not write it.

### PARITY-3.2 — Schema for the goal history
- **Status** `TODO`
- **Scope** a child table on `EOS Metric` or a standalone DocType per *Decision 1*; a patch under
  `[post_model_sync]` seeding the current `target_value` as the initial goal so no existing row loses
  its goal; then `bench migrate`.
- **Acceptance criteria** every existing Measurable resolves to its current `target_value` for any
  period after the change; the patch is idempotent and safe on a fresh site; a Measurable with no goal
  history behaves exactly as it does today.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  A regression test asserting an old Measurable's status is unchanged by the migration.

### PARITY-3.3 — Engine: resolve the goal as of a period
- **Status** `TODO`
- **Scope** `eos_core/scorecard_engine.py` (pure, no frappe) and `test_scorecard_engine.py` (63 tests
  today).
- **Acceptance criteria**
  - a pure function resolves the goal in effect for a given period from a goal history;
  - a period before the first goal resolves to the earliest goal, not to `None` — decide and pin;
  - a custom (single-period) goal beats the surrounding "from" goal for exactly that period;
  - an unknown or empty history returns the Measurable's `target_value`, so no caller has to special
    case it.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  ./env/bin/python -c "import sys; sys.path.insert(0,'apps/eos_core'); import eos_core.scorecard_engine as e; print(e.RESOLVE_GOAL_HERE)"
  bench --site resolv.localhost run-tests --module eos_core.test_scorecard_engine --site resolv.localhost
  ```
  Substitute the function name this task actually defines — it is a placeholder, not a test.
  Unit tests only — this function needs no DB and must stay that way.

### PARITY-3.4 — Controller: `set_new_goal` and `set_custom_goal`
- **Status** `TODO`
- **Scope** `eos_metric.py`; tests in `test_eos_metric.py` and `test_permissions.py`.
- **Acceptance criteria**
  - both are whitelisted, permission-checked, and refused to a `Team Member` — `target_value` is
    **not** in `TEAM_MEMBER_EDITABLE_FIELDS` and must not be added;
  - `Set New Goal` refuses a date in the past unless the caller is Manager and above, per whatever
    Ninety says;
  - after a goal change, only the entries in the affected periods have their status recomputed, and
    entries outside them are **byte-identical**;
  - a Measurable with a custom goal for the current week shows the custom goal as the grid's Goal
    value.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  The "entries outside the change are untouched" test is mandatory and is the one that catches
  *Decision 2* being ignored.

### PARITY-3.5 — Downstream consumers read the resolved goal
- **Status** `TODO`
- **Scope** `scorecard.py` (`_rollup_metric`'s `goal`), `scorecard_report.py` (`_build_metric_block`'s
  `target` and the snapshot child), `level_10_meeting.py`'s scorecard review section if it shows a
  goal, and `test_scorecard.py` / `test_scorecard_report.py` / `test_level_10_meeting.py`.
- **Acceptance criteria** the report snapshot stores the goal in effect for the report's
  `week_start_date`, not "today's goal"; the rolled-up view returns a goal per period, or documents
  why it cannot; the email template's `{{ row.target }}` still renders.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard_report.test_scorecard_report --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PARITY-3.6 — The surface, and close-out
- **Status** `TODO`
- **Scope** the Measurable Manager or grid from `UI-1`/`UI-8`; then `docs/architecture.md`, `AGENTS.md`,
  `docs/TODO.md`.
- **Acceptance criteria** both actions are reachable in the browser; the Goal column shows the goal in
  effect for the period being displayed; the docs record the resolution rule; `TODO.md` moves
  `PARITY-3` to *Done* with the SHA.
- **Verification** manual browser pass, recorded, plus:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PARITY-3.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- `roadmap.md` §6 says "Forecasting/custom period goals are deferred" under Phase 3. `PARITY-3` is
  the item that revisits that, and the roadmap line should be corrected at close-out rather than left
  contradicting the queue.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**
  (185 integration + 63 unit). `test_scorecard_engine.py` is the 63 unit tests and must stay
  frappe-free.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All six tasks.
