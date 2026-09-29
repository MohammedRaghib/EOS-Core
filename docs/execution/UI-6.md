# UI-6 — Bulk UX

## Parent TODO

`UI-6` — **S3** · Bulk UX.
Block C (Phase 7: UI).

**Scope** (verbatim from `TODO.md`): import/export XLSX/CSV, bulk paste, bulk archive / duplicate /
share.

**Done when** is not written as a line for this item; the plan's completion criteria below stand in
for it. This item is the widest in Block C and is the one most likely to be over-claimed, so the
close-out section names exactly which of the four capabilities were built and which were not.

## Objective

A user can get measurables and their period data in and out of the app in bulk without hand-editing
rows, and can archive, duplicate and share a selection in one action — with every bulk action going
through the same permission checks a single-row action goes through, and with a per-row result the
user can read.

## Dependencies

- **`UI-1`** — bulk paste is a grid affordance; the grid is where a selection exists.
- **`DATA-3`** — bulk archive of `Rock` / `Issue` / `To Do` needs the `archived` flag to exist.
  Without it, "bulk archive" is unimplementable for exactly the three DocTypes Ninety archives.
- `PERM-2` (closed) is what makes the role rules available to enforce.
- Independent of `UI-2`, `UI-3`, `UI-4`, `UI-5`.

## Decisions to settle before implementing

1. **Do not write an XLSX writer.** Frappe core already ships both halves: `Data Export`
   (`frappe/core/doctype/data_export/`, `file_type` CSV or XLSX, `filter_list`,
   `fields_multicheck`) and `Data Import` (`frappe/core/doctype/data_import/`, `import_type` Insert
   or Update, `import_file`, `download_template`, `google_sheets_url`, CSV sniffer). `UI-6` should
   configure, restrict and surface them, not reimplement them.
2. **The core importer respects permissions, which is why it is safe to expose.** `insert_record`
   calls `new_doc.insert()` and `update_record` calls `frappe.get_doc(...)` + `updated_doc.save()`
   with no `ignore_permissions` (`frappe/core/doctype/data_import/importer.py:276-308`). So the
   DocPerm block and the `permission_query_conditions` / `has_permission` layer in
   `eos_core/permissions.py` both apply to an imported row. `frappe.flags.in_import` suppresses
   email, module-file exports and a few validations — **it does not bypass permissions**; verified
   rather than assumed, because this is the assumption the whole item rests on.
3. **Which DocType does import/export target?** `EOS Metric` and `Scorecard Entry` are a parent +
   child pair, and Frappe's importer reads child rows from the lines following a parent row. A
   scorecard is the natural export unit; a `Scorecard Entry`-only import has no `Scorecard` to
   attach to. Decide the unit before building the template.
4. **Bulk archive / duplicate / share are three different permission shapes and must not share one
   path.** Archive is a `write`; duplicate is a `create`; share is the `share` permtype. A single
   "bulk action" endpoint that takes an action name is how a `write`-shaped action ends up running
   with `create` authority. Keep them separate endpoints.
5. **`share` is `0` for `Team Member` and `Observer` everywhere**, per `PERM-2`, so bulk share is
   Manager-and-above. Confirm against the live DocPerm block before building the control.

## Execution Tasks

### UI-6.1 — Export
- **Status** `TODO`
- **Scope** `Scorecard Report` or a new whitelisted export method; reuse
  `frappe.core.doctype.data_import.exporter` rather than writing a serializer. Tests in
  `test_scorecard_report.py` or `test_scorecard.py`.
- **Acceptance criteria** a user can export a team's measurables and their entries as XLSX and as
  CSV; the export respects the caller's permissions (a `Team Member` cannot export another team's
  rows, proven by a test); archived rows are excluded unless explicitly included.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  ```
  plus a manual pass: export as a `Manager`, open the file, confirm the row set matches the grid.

### UI-6.2 — Import
- **Status** `TODO`
- **Scope** a `Data Import` template for the chosen unit from *Decision 3*, wired from the grid or
  the Scorecard form. Tests for the app-side constraints.
- **Acceptance criteria**
  - a downloadable template that imports cleanly on a fresh team;
  - `import_type` Insert and Update both exercised; Update matches on the DocType's id field;
  - the app's own validations still fire on imported rows — `validate_owner_team`,
    `validate_data_entry_only`, `validate_range_target` and the `EOS Metric.validate` order must not
    be skipped by going through the importer;
  - a `Team Member` importing entries is permitted where `UI-1.2`'s path permits, and importing a
    settings field is refused;
  - errors are reported per row and do not abort the whole file silently.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  plus a manual pass with a deliberately invalid row, recorded.

### UI-6.3 — Bulk paste
- **Status** `TODO`
- **Scope** the grid JS from `UI-1`; the write endpoint from `UI-1.2`.
- **Acceptance criteria** a rectangular selection can be pasted from a spreadsheet into the grid; each
  cell takes the `UI-1.2` write path individually; cells that are refused are reported individually
  and the rest still save; a pasted value is not silently coerced to `0`.
- **Verification** manual browser pass with a 3 × 4 paste including one cell the user is not allowed
  to set, recorded.

### UI-6.4 — Bulk archive, duplicate and share
- **Status** `TODO`
- **Scope** three separate whitelisted methods. Archive needs `DATA-3`. Duplicate overlaps
  `PARITY-1`'s Duplicate half — **reuse `PARITY-1`'s implementation if it has landed, and do not
  build two**; if it has not, sequence this task after `PARITY-1` rather than racing it.
- **Acceptance criteria**
  - each action is a separate endpoint with its own permission check;
  - a per-row success/failure list is returned and rendered, and a partial failure is not reported
    as a success;
  - bulk archive skips already-archived rows and reports them as no-ops;
  - bulk share refuses `Team Member` and `Observer`.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  plus manual passes as a `Manager` and a `Team Member`, recorded.

### UI-6.5 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md`, `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the close-out states, per capability, whether it was built and verified; if
  only some of import / export / paste / archive / duplicate / share landed, `TODO.md` records the
  remainder rather than the item being closed. This is the item most at risk of being reported as
  more complete than it is.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`UI-6.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- **Bulk duplicate is the same feature as `PARITY-1`'s Duplicate half.** Two items, one capability;
  recorded here so the split is deliberate rather than accidental.
- `Data Import` carries a `google_sheets_url` field. That is a second route to the Google Sheets
  half of `PARITY-6`'s connector scope — noted, not claimed; `PARITY-6` still owns the design.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All five tasks, blocked on `UI-1` and `DATA-3`, with `UI-6.4` additionally sequenced after
`PARITY-1`.
