# UI-5 — Scorecard column toggles

## Parent TODO

`UI-5` — **S3** · Scorecard column toggles.
Block C (Phase 7: UI).

**Scope** (verbatim from `TODO.md`): Owner / Goal / Average / Total visibility, "show current
period", default timeframe, and the per-team override of company defaults (depends on `PERM-5`).

## Objective

The grid honours the effective settings from `PERM-5`, and a user with the right role can change them
from the browser, with the company default and a team override both visible and distinguishable.

## Dependencies

- **`PERM-5`** — the setting row and its effective-value reader. Without it there is nothing to
  toggle, and this item is blocked.
- **`UI-1`** — the toggles act on the grid, which does not exist yet.
- Independent of `UI-2`, `UI-3`, `UI-4`.

## Decisions to settle before implementing

1. **`Average` and `Total` are one column, not two.** `EOS Metric.rollup` is already a `Select` of
   `Total`/`Average`. The toggle is *whether the value column is shown*; which of the two it shows is
   the per-metric `rollup`. Do not introduce a second rollup concept at the UI layer.
2. **"Default timeframe" is per user and per team, and they are different settings.** Ninety's
   article describes a per-user default plus a per-team override. Decide which one lives where, and
   make precedence explicit — a silent precedence rule here is the kind of thing that becomes a bug
   nobody can reproduce.
3. **"Show current period" is a visibility rule, not a status rule.** An in-progress week is never
   `is_period_complete`, so a column for it can show data with no status. Hiding it is a display
   choice; do not let it change what the endpoint computes.
4. **The settings UI must respect the role rule `PERM-5` set.** Render the toggles read-only, or hide
   them, for a `Team Member` and an `Observer`, rather than letting them try and fail.

## Execution Tasks

### UI-5.1 — Hide and show the columns
- **Status** `TODO`
- **Scope** the grid JS from `UI-1`; the reader from `PERM-5.1`.
- **Acceptance criteria**
  - the effective settings are fetched once per render and applied to Owner, Goal and the value
    columns;
  - hiding a column does not remove the data from the payload — it is a display decision, and a
    later `UI-4` filter may need it;
  - "show current period" adds or removes the in-progress period's column;
  - two different teams can show different column sets at the same time.
- **Verification** manual browser pass with two teams configured differently, recorded in
  *Completed* with both configurations and what each rendered.

### UI-5.2 — Status colours
- **Status** `TODO`
- **Scope** the same JS/CSS.
- **Acceptance criteria** the `Green` / `Yellow` / `Red` / `No Recent Data` indicator from
  `compute_status_indicator` renders as colour by default, and renders as text or shape when colours
  are switched off; the switch is a display concern only and does not change any computed value.
- **Verification** manual browser pass with colours on and off, including a metric with no recent
  data, recorded.

### UI-5.3 — The settings control and the company-default / team-override distinction
- **Status** `TODO`
- **Scope** the same JS; possibly a form on `Team` depending on what `PERM-5.1` chose.
- **Acceptance criteria**
  - a role permitted by `PERM-5.2` can change the settings from the browser and the grid re-renders
    with them;
  - a `Team Member` / `Observer` sees the settings read-only, or does not see the control;
  - the UI shows which values are inherited from the company default and which are team overrides,
    and a "reset to default" action exists.
- **Verification** manual browser pass as a `Manager` and as a `Team Member`, recorded.

### UI-5.4 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` (the §7 "no UI" bullet), `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs record the precedence rule chosen in *Decision 2*; `TODO.md`
  moves `UI-5` to *Done* with the SHA and both boxes ticked.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`UI-5.1`. Nothing has been implemented; no task has been started.

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

All four tasks, and it is blocked until both `PERM-5` and `UI-1` close.
