# PARITY-5 — Lightning-bolt indicator on formula ("Smart") measurables

## Parent TODO

`PARITY-5` — **S3** · Lightning-bolt indicator on formula ("Smart") measurables.
Block D (Ninety parity features with no representation at all).

**Done when** (verbatim from `TODO.md`): a `is_smart` measurable displays Ninety's lightning-bolt
marker, and a manually overridden entry is distinguishable from a computed one.

**Note recorded in the item**: `is_manual` already matches Ninety's Manual Override requirement; only
the indicator is missing.

## Objective

A Measurable whose value is computed by a formula is visibly marked as computed, and a period where
a human overrode the formula's result is visibly marked as overridden — in the grid, in the report
email, and in the rolled-up view, so the marker is not a grid-only decoration.

## Dependencies

- **`UI-1`** — the grid is where the marker is primarily seen. The `is_smart` and `is_manual` flags
  must reach the payload, which `UI-1.1` / `UI-1.2` own.
- Independent of the engine: `is_smart`, `formula` and `is_manual` exist and are validated.
- Independent of `PARITY-1` and `PARITY-3`.

## Decisions to settle before implementing

1. **The marker is a display concern, never a status one.** A computed value that is off track is off
   track. Do not let the marker feed `compute_status`, the indicator or any aggregate.
2. **Where the override marker is a whole cell or a whole row.** Ninety marks the measurable as
   smart and the individual overridden value as manual, which means two markers at two granularities.
   Confirm against Ninety's current docs before building either.
3. **Frappe has icon support** (`options` with an icon, or `frappe.ui.make_icon`), so a bolt does not
   need an asset. Prefer a Frappe icon over shipping an SVG; the project has no asset pipeline and
   adding one for one glyph is not proportionate.
4. **The email must carry it too.** `templates/emails/weekly_scorecard_report.html` renders
   `{{ row.status_indicator }}`; a report that marks computed values in the UI and not in the email is
   a parity gap in the wrong direction.

## Execution Tasks

### PARITY-5.1 — Expose `is_smart` and `is_manual` to every surface
- **Status** `TODO`
- **Scope** the grid endpoint from `UI-1.1` (per-metric `is_smart`), the write endpoint from
  `UI-1.2` (per-entry `is_manual`), `ScorecardReport._build_metric_block` and the snapshot child, and
  `Scorecard._rollup_metric`. Tests in `test_scorecard_report.py` and `test_scorecard.py`.
- **Acceptance criteria** every payload that shows a measurable or an entry carries `is_smart`, and
  every payload that shows a value carries `is_manual`; the `Scorecard Report Metric` child stores
  the flag so the email can render it; a formula-computed value is distinguishable from an
  `is_manual` override in the stored snapshot, with a test.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard_report.test_scorecard_report --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Adding fields to a child DocType means a JSON edit and `bench migrate`; confirm the sync before
  trusting the tests.

### PARITY-5.2 — Render the markers
- **Status** `TODO`
- **Scope** the grid JS from `UI-1`, and `eos_core/templates/emails/weekly_scorecard_report.html`.
- **Acceptance criteria**
  - a smart Measurable shows Ninety's lightning-bolt marker on its name;
  - an overridden entry shows a distinguishable marker, and a computed one does not;
  - the markers are absent on a non-smart Measurable;
  - the email renders the same two markers;
  - nothing about status, colour or the indicator changes.
- **Verification** manual browser pass with one smart Measurable that has both a computed and a
  manually overridden period, plus one plain Measurable as a control, recorded in *Completed*.
  Confirm visually that no status colour moved.

### PARITY-5.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §3c, `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs state the marker is presentational only; `TODO.md` moves
  `PARITY-5` to *Done* with the SHA and both boxes ticked.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PARITY-5.1`. Nothing has been implemented; no task has been started.

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

All three tasks, blocked on `UI-1`.
