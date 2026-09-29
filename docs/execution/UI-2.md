# UI-2 — UI trigger for "Make it an Issue"

## Parent TODO

`UI-2` — **S2** · UI trigger for "Make it an Issue".
Block C (Phase 7: UI).

**Done when** (verbatim from `TODO.md`): an off-track metric in the grid has a "Make it an Issue"
action, the Issue is created from the browser, and the streak in the description matches `BUG-1`'s
corrected behaviour.

**Where** (verbatim): `create_issue_from_metric` works and is tested, but is **not** whitelisted and
has no button. Fix `BUG-1` first, or the button will show wrong numbers.

## Objective

`create_issue_from_metric` is reachable from a browser: whitelisted, permission-checked, callable
from the grid row of an off-track Measurable, and producing an `Issue` whose description carries the
**bounded** consecutive-off-track count that `BUG-1` fixed.

## Dependencies

- `BUG-1` — **closed** (`08757c4`). The bounded count exists: `count_consecutive_from_db(metric_name,
  as_of)` caps the query with `week_start_date <= as_of`, and `create_issue_from_metric` passes the
  resolved entry's `week_start_date`. Do not re-derive it.
- **`UI-1`** — the item says the action lives on the grid row, so it needs the grid and the grid's
  row identity. If `UI-1` has not landed, this item is blocked; do not build a second surface to
  dodge that.
- Independent of the rest of Block C.

## Decisions to settle before implementing

1. **Whitelisting is a permission surface, and the function is currently unguarded.** It is a
   module-level function, not a doc method, so `frappe.call` with
   `run_doc_method` semantics does not apply and there is no automatic permission check. It must do
   its own: read the metric through `frappe.get_list`/`get_doc` under the caller's permissions so a
   user cannot raise an Issue on a Measurable they cannot see, and require `create` on `Issue`.
2. **The action only appears on an `Off Track` period.** The server already refuses an `On Track`
   entry; hiding the button is a UX nicety, the refusal is the guarantee. Do not let the two drift
   into two different rules.
3. **Where the button lives: the grid row, or the `EOS Metric` form?** The item says the grid.
   `UI-7` has already established the `doctype_js` pattern for form buttons, so the form route is
   the cheap fallback if the grid is not ready — but the queue's "Done when" names the grid, so
   landing only the form button is a partial close, not a done one.

## Execution Tasks

### UI-2.1 — Whitelist and guard `create_issue_from_metric`
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/issue/issue.py`, tests in
  `eos_core/eos_core/doctype/issue/test_issue.py` (5 tests today) and, for the role matrix, in
  `eos_core/test_permissions.py`.
- **Acceptance criteria**
  - the function is `@frappe.whitelist()` and callable from `frappe.call`;
  - it throws `frappe.PermissionError` when the caller has no `create` on `Issue` — an `Observer`
    is refused;
  - it throws `frappe.PermissionError` when the Measurable is outside the caller's assigned teams,
    proven by a test using a second team's metric, not by reading the code;
  - the existing refusals still work: unknown metric, no entries, `On Track` entry;
  - `BUG-1`'s bounded count is unchanged — a test asserts an Issue for an earlier week does **not**
    carry the later week's streak.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.issue.test_issue --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  No `bench migrate` is needed — this is a controller change, not a schema one.

### UI-2.2 — The grid row action
- **Status** `TODO`
- **Scope** the grid JS from `UI-1`; no new server code if `UI-2.1` landed.
- **Acceptance criteria**
  - an `Off Track` period cell in the grid offers "Make it an Issue";
  - the call passes the metric name and that period's week start — the bounded count depends on it,
    so it must be explicit, not "the latest entry";
  - on success the grid shows the new `Issue`'s name as a link;
  - on refusal the server message is shown verbatim;
  - a manual browser pass creates the Issue end to end and the description's `Consecutive Off Track`
    matches the week shown on screen.
- **Verification** manual browser pass on `resolv.localhost` with an `Off Track` measurables that has
  a multi-week streak, recorded in *Completed* with the exact description text produced. A test that
  the button renders is not sufficient; `TODO.md` says so.

### UI-2.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §3d (the Issues section says "no UI trigger"), `AGENTS.md`,
  `docs/TODO.md`.
- **Acceptance criteria** the docs state the trigger exists and where it lives; `TODO.md` moves
  `UI-2` to *Done* with the SHA and both boxes ticked.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`UI-2.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

None yet. If the grid turns out not to expose an `Off Track` period per cell, that is a `UI-1` gap
— raise it as a new `TODO.md` item rather than fixing `UI-1` from this plan.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All three tasks.
