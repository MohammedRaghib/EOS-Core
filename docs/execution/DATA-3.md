# DATA-3 — `Rock`, `Issue` and `To Do` have no `archived` field, so Ninety's archive cannot exist

## Parent TODO

`DATA-3` — **S2** · `Rock`, `Issue` and `To Do` have no `archived` field.
Block A (Correctness). The only item still open in Block A, and the item `docs/TODO.md` names as
next to land.

**Done when** (verbatim from `TODO.md`): the three DocTypes carry an `archived` flag, archive and
restore follow Ninety's role matrix (Observer refused, every other role with `write` allowed),
archived rows are excluded from the default list and reachable from an archive view, and the change
is covered by tests.

## Objective

`Rock`, `Issue` and `To Do` each carry a real `archived` Check column, archiving is a write that the
existing permission model already answers correctly (it follows `write`, so `Observer` is refused by
DocPerm and everyone else with `write` may archive), archived rows drop out of every default list
and out of the aggregate snapshots, and an archived row can still be found and restored. The full
suite stays green and `bench migrate` has been run.

## Dependencies

- None. `PERM-2` (DocPerm) and `PERM-12` (the role matrix) are both closed, so the grant half of this
  item needs no new work — it is a schema + list + archive-view item only.
- Nothing in this plan is blocked. It is the cheapest item in the queue and the safest place for a
  new session to start.

## Decisions to settle before implementing

1. **Archive is a field write, not a new DocPerm column.** There is no `archive` permtype. Ninety's
   roles tables grant "Archive a To-Do" to every role but Observer, and the `PERM-12` analysis
   established that the correct grant is plain `write` with Observer withheld — which is exactly
   what the JSON already has. Do **not** add a permtype, a hook or a guard. `DEBT-1`'s pattern
   applies: a new mechanism here would be a second source of truth for something DocPerm already
   says.
2. **`archived` is a `Check` with `default: 0`, not a `status`.** Six DocTypes already carry it
   (`EOS Metric`, `Measurable Group`, `Organization`, `Player`, `Team`, `Scorecard`). Copy the
   field verbatim from `scorecard.json` so there is one declaration of the flag in the app.
3. **Where the flag sits in `field_order`.** Put it last, after the real business fields, so the
   list view and the form do not change shape. This is the one place where consistency with
   `scorecard.json` is *not* the right call, because in `Scorecard` `archived` is the last field too
   — so "last" is in fact consistent.
4. **An archived row is not a deleted row.** It stays queryable by name, keeps its links, and can be
   restored. In particular `Rock` → `To Do` links and `Quarterly Review` snapshots must not break
   because a To-Do was archived.
5. **The archive *view* is a list-view filter, not a new page.** Ninety's "View archive" is the
   same list with the flag on. In Frappe terms that is a saved filter or a list-view filter in
   `System Filter`/`filters` on the `*.json`. Decide which: a JSON `filters` block is committed with
   the app and reproduces on a fresh site; a `List View Settings` record is data and does not. Prefer
   the JSON, for the reason `UI-7` records about Client Scripts.

## Execution Tasks

### DATA-3.1 — Schema: the `archived` flag on the three DocTypes
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/rock/rock.json`, `.../issue/issue.json`,
  `.../to_do/to_do.json`. No Python patch is required — a new `Check` column defaults to `0`, so
  existing and new rows are both correct without a backfill. Then `bench migrate`.
- **Acceptance criteria**
  - each of the three JSONs declares `archived`, `fieldtype: "Check"`, `default: 0`, last in
    `field_order`;
  - `show columns` reports an `archived` `tinyint(1)` on `tabRock`, `tabIssue` and `tabTo Do`;
  - no controller, `hooks.py` entry or `permissions` block changed — the flag is inert until
    DATA-3.2;
  - `frappe.get_meta("Rock").has_field("archived")` is true for all three.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  cat > /tmp/q.py <<'EOF'
  for dt in ("Rock", "Issue", "To Do"):
      print(dt, frappe.db.sql(f"show columns from `tab{dt}` like 'archived'"))
  print("rows:", frappe.db.sql("select count(*) from tabRock where archived = 1"))
  EOF
  bench --site resolv.localhost console < /tmp/q.py
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  The full suite must be unchanged at **248** after this task.

### DATA-3.2 — Exclude archived rows from the default lists and the aggregate snapshots
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/quarterly_review/quarterly_review.py` (`_rock_rows`,
  `_todo_rows`), `eos_core/eos_core/doctype/rock/rock.py` (`mark_complete`'s To-Do query and
  `get_rock_summary`'s To-Do query), plus `to_do.json` / `rock.json` / `issue.json` `filters`
  blocks for the default list views. Tests in `test_quarterly_review.py`, `test_rock.py`,
  `test_to_do.py`.
- **Acceptance criteria**
  - `QuarterlyReview._rock_rows` and `_todo_rows` add `"archived": 0` to their filters, matching how
    `_measurable_rows` already excludes archived `EOS Metric` rows;
  - `Rock.mark_complete` only cascades to **unarchived** To-Dos, and `get_rock_summary` counts only
    unarchived ones — an archived To-Do is out of the working set, not deleted;
  - the three JSONs carry a committed default list filter hiding `archived = 1`;
  - each exclusion has a test that fails without the filter (see *Verification*).
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.quarterly_review.test_quarterly_review --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.rock.test_rock --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.to_do.test_to_do --site resolv.localhost
  ```
  Mutation check: remove one `"archived": 0` and confirm the matching test **fails**, then restore it.

### DATA-3.3 — Archive / restore whitelisted methods with the role matrix tested
- **Status** `TODO`
- **Scope** `rock.py`, `issue.py`, `to_do.py` (one `@frappe.whitelist()` method per controller, or a
  single helper in `eos_core/permissions.py` called by all three). Tests in
  `eos_core/test_permissions.py`.
- **Acceptance criteria**
  - `archive()` sets `archived = 1` and saves under the caller's normal permissions; `restore()`
    sets it back to `0`. Both are reachable from the browser once `UI-7`-style `doctype_js` exists —
    until then they are API-only, and that must be stated rather than implied;
  - **no permission code is added.** Because archiving is a `write`, an `Observer` is refused by the
    existing DocPerm block and must throw `frappe.PermissionError` without the app inspecting the
    role at all;
  - `restore()` is refused to the same roles, since it is also a write;
  - archiving a row does not delete it or break its links.
- **Verification** — one test per role per DocType is **not** required (the DocPerm matrix test
  already pins the grant); what is required is the negative case plus one positive:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Tests to add: (a) an `Observer` is refused `archive()` on a `Rock` and no row changed;
  (b) a `Team Member` with a seat archives a `To Do` it owns; (c) a `Manager` archives and restores
  an `Issue`; (d) an archived row is still readable by name and its links are intact.

### DATA-3.4 — Documentation and close-out
- **Status** `TODO`
- **Scope** `docs/architecture.md` (§7 currently says the three "cannot be archived at all"),
  `AGENTS.md` § Known gaps, `docs/TODO.md`.
- **Acceptance criteria** the "cannot be archived" bullet in `architecture.md` §7 is replaced with
  the new state; `AGENTS.md`'s known-gaps paragraph no longer lists `DATA-3` as open;
  `TODO.md` moves `DATA-3` to *Done* with the SHA, and the footer points at the next item.
- **Verification** re-run the full suite after the doc edits, and re-derive the counts:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  grep -rn "cannot be archived" docs/ AGENTS.md || true
  ```

## Current Task

`DATA-3.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet. *Decisions to settle* above are the starting position, not settled fact — the first
task is allowed to overturn any of them as long as the reason is recorded here.

## Discovered Issues

None yet. Anything found while working this plan that is **not** this item gets a new `TODO.md` ID
rather than a silent fix. Two things already known to be adjacent, and deliberately *not* in scope:
`UI-6` (bulk archive) and `UI-7` (form buttons, which is where `archive()` becomes clickable).

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**
  (185 integration + 63 unit).
- To be filled per task.

## Completion

Pending.

## Remaining Work

All four tasks.
