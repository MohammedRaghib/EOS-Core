# UI-1 — Scorecard grid (the core Ninety screen)

## Parent TODO

`UI-1` — **S2** · Scorecard grid (the core Ninety screen).
Block C (Phase 7: UI). Block C is 0% done and is the largest gap in the project. This is the
prerequisite for most of the rest of the block.

**Scope** (verbatim from `TODO.md`): a Worksheet Page plus a whitelisted grid endpoint over
`EOS Metric` + `Scorecard Entry`. Depends on `PERM-2` for column-level visibility.

**Done when** is not written as a single line for this item, so the plan's own completion criteria
are used instead: a user opens the team's scorecard in the browser and sees their measurables in
groups with one column per reporting period, can enter an actual value, sees the status and the
status indicator recompute, and cannot see another team's measurables.

## Objective

A browser-reachable Scorecard grid that reads through the permission layer, renders metrics grouped
and ordered, one column per reporting period, with the status indicator, and writes an actual value
back through the same permission path a form save takes — so a `Team Member` can enter data and
cannot change a Measurable's settings.

## Dependencies

- `PERM-2` (closed) and `PERM-6` (closed) — the DocPerm blocks and the team-scoping layer exist, so
  the grid can be built against a real permission model rather than a provisional one.
- `DATA-3` — **not required**, but lands first in the queue. `EOS Metric` already carries `archived`
  and the grid must exclude archived rows, so that part does not wait on `DATA-3`.
- **Unblocks** `UI-2` (needs a grid row to hang the action off), `UI-3` (needs the grid shell for the
  "View by" control), `UI-4` (Trends view), `UI-5` (column toggles), `UI-6` (bulk paste into the
  grid), `PARITY-5` (the indicator marker) and `PERM-3` (drag reorder).

## Decisions to settle before implementing

1. **The endpoint reads through `frappe.get_list`, never `frappe.get_all`.** `get_all` sets
   `ignore_permissions=True` (`frappe/__init__.py:1383`) and therefore skips both the DocPerm block
   and the `permission_query_conditions` layer. A grid built on `get_all` shows every team's
   measurables to every team-scoped role. This is the single most important constraint in the item.
2. **Frappe v16 has no Worksheet Page.** The scaffold's `eos_core/templates/pages/` exists but is
   empty, and there is no `worksheet` DocType in `frappe/desk/doctype/`. The realistic options are a
   `frappe.core.doctype.page` record (fields `page_html`, `title`, `icon`, `module`, `roles`), a
   `Workspace` with a custom block, or a Desk route registered from `app_include_js`. **Settle this
   empirically in `UI-1.3` before building any rendering code**, because it determines the file
   layout for the rest of the plan. A `Page` record is *data*: if it is created by a patch or an
   `after_migrate` hook it reproduces on a fresh site, which is the same argument `UI-7` makes for
   `doctype_js` over Client Scripts.
3. **Data entry writes through the parent `EOS Metric`, never a bare `Scorecard Entry`.** `Scorecard
   Entry` is a child with no permissions of its own; Frappe gates child writes on the **parent's**
   `write`, and the `entries` child is only a legal write path because `TEAM_MEMBER_EDITABLE_FIELDS`
   permits it (`PERM-7`). A grid that `insert()`s a `Scorecard Entry` directly would bypass the
   parent's status recomputation, the formula recalc and the guard order that `PERM-7` depends on.
   The write endpoint must load the `EOS Metric`, upsert the child row and `save()` the parent.
4. **Ninety's column layout is periods, not weeks, in the general case.** A `Weekly` scorecard shows
   week columns; anything else should show one column per its own period. The engine already has
   `period_bounds`, `advance_period`, `period_label` and `rollup_periods`, so the period series must
   come from there and not be re-derived here.
5. **Where a Measurable's position inside its group is stored is undecided — see `UI-1.8`.** There is
   no ordering field on `EOS Metric` today. `Measurable Group.order` orders *groups*, not the
   measurables inside one. `UI-1` may ship without per-measurable ordering (rows ordered by
   `metric_name` within a group), but it must not invent an ordering column as a side effect; that is
   `PERM-3`'s decision to make.

## Execution Tasks

### UI-1.1 — Server: the grid read endpoint
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/scorecard/scorecard.py` (new `@frappe.whitelist()` method),
  `eos_core/scorecard_engine.py` only if a genuinely reusable pure helper is missing.
  Tests: `eos_core/eos_core/doctype/scorecard/test_scorecard.py`.
- **Acceptance criteria** a whitelisted method returns, for one `Scorecard`:
  - a `periods` list built from `rollup_periods` / `period_label`, oldest → newest, with a default
    count and an explicit `as_of` accepted;
  - `metrics`: each `EOS Metric` on the scorecard, **read via `frappe.get_list`**, excluding
    `archived = 1`, ordered by `sort_metrics_by_group` with the group's real `order`;
  - per metric: `status_indicator` from `compute_status_indicator` over the completed intervals and
    `consecutive_off_track` from `count_consecutive_off_track`;
  - a `summary` from `scorecard_summary`;
  - ungrouped metrics present and sorted last (the engine's documented behaviour).
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  ```
  Tests must include a permission test: a user with a seat only in Team B gets no Team A metric
  (and the method does not raise). The suite for this module is 19 today and must be 19 + new.

### UI-1.2 — Server: the grid write endpoint
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/scorecard/scorecard.py` (or a new `eos_core/api.py`), reusing
  `EOSMetric`'s existing save path. Tests: `test_scorecard.py` and `eos_core/test_permissions.py`.
- **Acceptance criteria**
  - setting a value for a period upserts the `Scorecard Entry` child and saves the parent
    `EOS Metric`, so `entry.status` is recomputed by `EOSMetric.validate` exactly as a form save
    would;
  - the value is written for the period that **contains** the entry's `week_start_date`, so a
    Monthly grid cell maps onto the right week — use `period_bounds` / `week_overlap_days`, do not
    round;
  - clearing a cell removes the entry rather than writing a zero;
  - a `Team Member` can write a value and **cannot** change `unit_type` in the same request;
  - `validate_data_entry_only` still runs first in `validate` — do not bypass the controller.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Mutation check: set the entry directly with `ignore_permissions=True` instead of going through the
  parent and confirm the Team Member tests fail.

### UI-1.3 — Host the page and prove an app JS asset loads
- **Status** `TODO`
- **Scope** `eos_core/hooks.py` (`app_include_js` and/or `doctype_js` / `page_js`),
  `eos_core/public/js/`, `eos_core/public/css/`, and whichever host was chosen in *Decision 2* —
  including a patch or `after_migrate` step if the host is a data record.
- **Acceptance criteria**
  - the chosen host exists in git and reproduces on a fresh site (a record created by a patch counts
    as reproducing; a record created once in the console does **not**);
  - the page is permission-gated: a user with no Eos Core role cannot route to it, and this is
    enforced server-side, not only by hiding a link;
  - `bench --site resolv.localhost build` (or `bench build`) succeeds and the app's JS asset appears
    in `sites/assets/eos_core/`;
  - a route in the browser renders an empty page and a console message proving the app JS ran.
- **Verification** this task is verified **in a browser**, not by an assertion:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost build
  ls sites/assets/eos_core/js sites/assets/eos_core/css
  ```
  plus a manual pass on `resolv.localhost` as a `Team Member` and as an `Observer`. Record what the
  browser actually showed — `TODO.md` is explicit that an assertion cannot prove a page is clickable.

### UI-1.4 — Render the grid: rows, groups, period columns
- **Status** `TODO`
- **Scope** `eos_core/public/js/` (the grid module from `UI-1.3`), `eos_core/public/css/`.
- **Acceptance criteria**
  - one row per measurable, grouped, in `Measurable Group.order`, ungrouped last;
  - one column per period with the label from `period_label` and the period's date range in the
    header;
  - per row: Owner, Goal (`target_value`), the per-period actual, the per-period status, and the
    status indicator;
  - loading, empty ("no measurables on this scorecard") and error states are all rendered — an
    error state that silently shows an empty grid is a defect, not a state;
  - the grid renders from `UI-1.1`'s payload only. If the JS needs a field the endpoint does not
    return, add it to the endpoint, do not fetch a second time.
- **Verification** manual browser pass on `resolv.localhost` at two roles and two teams, recorded
  under *Completed*. Add a JS-level check only if the project ever adopts one — it does not today,
  and inventing a test runner is out of scope for this item.

### UI-1.5 — Group collapse / expand
- **Status** `TODO`
- **Scope** the same JS/CSS. Ninety lets every role, including `Observer`, view, expand and collapse
  groups (`PERM-11`'s source article).
- **Acceptance criteria** a group header is clickable and toggles its rows; state survives a
  re-render; an `Observer` can collapse (this is a view concern and must not require `write` on
  `Measurable Group`, which they do not have).
- **Verification** manual browser pass as an `Observer`, recorded.

### UI-1.6 — Inline data entry
- **Status** `TODO`
- **Scope** the same JS; server side already exists from `UI-1.2`.
- **Acceptance criteria**
  - a cell is editable for roles with `write` on `EOS Metric` and read-only for `Observer`, decided
    from the endpoint's response rather than hard-coded per role;
  - a successful save updates status and indicator in place without a full page reload;
  - a refused save (`frappe.PermissionError` from `validate_data_entry_only`) surfaces the server's
    message and reverts the cell;
  - an empty input clears the entry rather than writing `0` — `0` is a real value and
    `NOT NULL DEFAULT 0` makes "unset" ambiguous, so this must be explicit.
- **Verification** manual browser pass: enter a value as a `Team Member`, attempt to change
  `unit_type` as the same user and confirm the refusal message. Both recorded.

### UI-1.7 — Period navigation
- **Status** `TODO`
- **Scope** the same JS.
- **Acceptance criteria** previous / next period, a "show current period" control, and a period
  count control; all of them re-query `UI-1.1` with an explicit range rather than filtering in the
  browser; week starts stay Monday-aligned, per `AGENTS.md`.
- **Verification** manual browser pass, recorded. Do not let a test depend on `date.today()`.

### UI-1.8 — Close-out, documentation, and the ordering decision
- **Status** `TODO`
- **Scope** `docs/architecture.md` (a new subsection describing the grid and how it is hosted),
  `AGENTS.md` (the "There is no UI" paragraph is no longer true and must be corrected), `docs/TODO.md`.
- **Acceptance criteria**
  - `TODO.md` moves `UI-1` to *Done* with the SHA and both boxes ticked;
  - the recorded decision on **where a Measurable's position inside a group lives** is written down
    with its consequence for `PERM-3` — including, if a field is added, that it must be added to
    `TEAM_MEMBER_EDITABLE_FIELDS`, which is an allow-list and blocks unknown fields by default;
  - `AGENTS.md` and `architecture.md` §7 no longer say "there is no UI" for this surface.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  grep -rn "There is no UI" docs/ AGENTS.md || true
  ```

## Current Task

`UI-1.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- **No Worksheet Page exists in Frappe v16.** The `TODO.md` scope line names one; there is no such
  DocType. Not a new defect — a scope correction — but it changes what `UI-1` builds, so it is
  recorded here and settled empirically in `UI-1.3`.
- **`EOS Metric` has no ordering field**, so "reorder measurables within a group" (`PERM-3`) has
  nowhere to write. Recorded, not fixed here.
- `PERM-4` also notes Block C has no item for the Measurable Manager surface. That is `UI-8`; it is
  a separate item and is not part of this plan.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**
  (185 integration + 63 unit). Re-derive with
  `grep -rc 'def test_' --include='test_*.py'` rather than trusting the number above.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All eight tasks.
