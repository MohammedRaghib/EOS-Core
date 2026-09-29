# UI-3 — "View by" dropdown wired to `get_rollup_view`

## Parent TODO

`UI-3` — **S2** · "View by" dropdown wired to `get_rollup_view`.
Block C (Phase 7: UI).

**Done when** (verbatim from `TODO.md`): a `Week / Month / Quarter / Year` control on the grid renders
the rolled-up columns, and the weekly Goal column is visibly *not* aggregated (that asymmetry is
Ninety's, not a bug).

**Note** (verbatim): the endpoint is built, correct and tested (11 tests in `test_scorecard.py`).
Only the UI is missing. This is the cheapest parity win in the project.

## Objective

The grid offers Ninety's `Week / Month / Quarter / Year` control; selecting Month, Quarter or Year
re-renders the period columns from `Scorecard.get_rollup_view` instead of the raw weekly grid, and
the Goal column still shows the single weekly target — visibly unaggregated, because that is what
Ninety shows.

## Dependencies

- **`UI-1`** — the control lives on the grid, and the grid is the thing being re-rendered. If
  `UI-1` has not landed, this is blocked.
- `ARCHITECTURE` §3g records the rolled-up view as a **read-only projection** over the existing
  `Scorecard`, not a new DocType. That is one of the five locked Ninety-parity decisions in
  `AGENTS.md` § Ground rules — do not re-open it, and do not create a projection DocType.
- The endpoint exists and is unchanged by this plan.

## Decisions to settle before implementing

1. **The control has four options; only three are valid inputs.** `get_rollup_view` accepts Month,
   Quarter or Year and **throws** for `Week`, because a week is the raw grid. The UI must therefore
   offer `Week` as the default and switch away from it, never pass `Week` to the endpoint. Call the
   option labels Ninety's vocabulary (`Week`, `Month`, `Quarter`, `Year`) even though the
   `Scorecard.timeframe` values are `Weekly`/`Monthly`/`Quarterly`/`Annual` — `normalise_view_by`
   is the documented bridge.
2. **Only a `Weekly` Scorecard can be rolled up.** The endpoint refuses otherwise, with a message
   pointing the user at the team's own `Monthly`/`Quarterly`/`Annual` Scorecard. The control must be
   hidden or disabled on those, not shown-and-throwing.
3. **The asymmetry is a requirement, not a bug.** `rollup` (`Total` / `Average`) aggregates the
   *value* columns across weeks. The **Goal** column is `target_value` — the single weekly target —
   and is not rolled up. The UI must make that visible (a distinct header or a note) rather than
   "fixing" it, and a test must pin that the goal is unchanged across views.
4. **The rolled-up view is read-only.** No cell is editable in Month/Quarter/Year. Entering data
   happens in the weekly grid. The endpoint returns `"read_only": True`; the UI must honour it
   rather than treating it as advisory.

## Execution Tasks

### UI-3.1 — The `View by` control on the grid
- **Status** `TODO`
- **Scope** the grid JS from `UI-1`; no server change.
- **Acceptance criteria**
  - a control offering `Week / Month / Quarter / Year`, defaulting to `Week`;
  - selecting `Week` renders the raw weekly columns and makes cells editable;
  - selecting Month / Quarter / Year calls `get_rollup_view` with the equivalent label and renders
    its `periods` and per-metric `values`;
  - the control is absent or disabled on a non-`Weekly` Scorecard, matching the endpoint's refusal;
  - the rolled-up grid is visibly not editable.
- **Verification** manual browser pass on a `Weekly` Scorecard with at least one metric that has
  data across a month boundary, recorded in *Completed`. Specifically record a week that straddles
  two months and confirm the value is split by `week_overlap_days`, because that is the behaviour
  most likely to be "corrected" by mistake.

### UI-3.2 — The unaggregated Goal column, made visible
- **Status** `TODO`
- **Scope** the same JS/CSS.
- **Acceptance criteria** in a rolled-up view the Goal column shows the same weekly `target_value`
  as the `Week` view and is labelled or marked so a user does not read it as a period total; the
  `Average` / `Total` toggle still drives the value columns.
- **Verification** manual browser pass, recorded. Plus a server-side assertion that
  `get_rollup_view` returns an unchanged `goal` across `Month`, `Quarter` and `Year` for the same
  metric, added to `test_scorecard.py` — the existing 11 rollup tests stay green and one is added.

### UI-3.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §3g (it currently says only the endpoint is reachable),
  `AGENTS.md` (the "There is no UI" paragraph), `docs/TODO.md`.
- **Acceptance criteria** the docs say which piece of "View by" is now reachable from the browser
  and which parts of the locked decision still hold; `TODO.md` moves `UI-3` to *Done* with the SHA
  and both boxes ticked.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`UI-3.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

None yet.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
  `test_scorecard.py` is 19 today, of which 11 are the `get_rollup_view` tests.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All three tasks.
