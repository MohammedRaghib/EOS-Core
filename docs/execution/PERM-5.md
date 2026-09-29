# PERM-5 — Worksheet column visibility and status-colour toggles

## Parent TODO

`PERM-5` — **S3** · Worksheet column visibility and status-colour toggles.
Block B (Phase 6: Permissions & Roles). One of the three items Block B left open, and the one that
is **not** UI-blocked — the other two (`PERM-3`, `PERM-4`) are waiting on a surface that does not
exist yet.

**Scope** (verbatim from `TODO.md`): per-team settings for which columns are visible and whether
status colours show. `PERM-6` settled where these settings *live* (a team-scoped setting row read by
the grid), which this item still has to build.

**Done when** is not written as a line for this item; the plan's completion criteria below stand in
for it.

## Objective

A company-wide default set of worksheet settings exists, a team can override it, and the grid can
read the effective settings for the team and the user in one call — with the reading of those
settings gated so that only the roles Ninety allows may change them, and with tests for both halves.

## Dependencies

- `PERM-6` (closed) settled the representation: team scope comes from `Player` seats, and the
  settings must be keyed on `Team` for the same reason. Do not re-open the User Permission question.
- `PERM-2` (closed) means `Team` already has a DocPerm block for all six roles, which the settings
  DocType must mirror if it is a standalone DocType.
- **Unblocks** `UI-5`, which is the grid-side consumer.
- Independent of `UI-1`: the settings can be built and tested before the grid exists. That is why
  this item is not UI-blocked while `PERM-3` and `PERM-4` are.

## Decisions to settle before implementing

1. **Where the settings physically live — decide this first, it changes the schema.** Three options:
   - a **child table on `Team`** (e.g. `scorecard_settings`, one row per team). Smallest: no autoname,
     no list view, no separate permission block, and the row cannot drift from the team. Costs a
     `Team` JSON edit and `bench migrate`.
   - a **standalone `Scorecard Settings` DocType** linked to `Team`, autonamed from the team. More
     conventional, but it is a new Standard DocType and therefore a new DocPerm block that must be
     kept in step with `architecture.md` §3h by hand.
   - **`frappe` Singles**. Rejected already: settings are per team and Singles are per site.
   Record which one was chosen and why, in `architecture.md` §3h.
2. **What the company-wide default is, and where it lives.** `PERM-5` says "per-team override of
   company defaults". A default held in code is invisible to a user; a default held in a single
   record is editable. Pick one, and make the effective-settings call return the default when no
   override exists, so the grid never has to know the difference.
3. **Which columns are toggleable, exactly.** Ninety's set per `TODO.md`: Owner, Goal, Average,
   Total, "show current period", and the default timeframe. `Average` and `Total` are not two
   columns — they are the two values of the **existing** `EOS Metric.rollup` Select
   (`Total`/`Average`), so this item toggles *visibility of the rollup column*, not a choice. Do not
   build a second rollup concept.
4. **Who may change the settings.** Ninety's roles article is the source; per `PERM-2` the pattern
   is Manager and above for team settings, and the six-role matrix test will fail if the block is
   wrong. Do not hand-edit the matrix without extending
   `test_docperm_matrix_matches_the_ninety_capability_table`.

## Execution Tasks

### PERM-5.1 — The settings representation and its effective-value read
- **Status** `TODO`
- **Scope** whichever of the three options in *Decision 1* is chosen: a `Team` JSON edit, or a new
  `eos_core/eos_core/doctype/<name>/` DocType; plus a new whitelisted reader (the natural home is
  `eos_core/eos_core/doctype/team/team.py` or a small `eos_core/api.py`). Tests in `test_team.py`
  (4 today) or a new test module.
- **Acceptance criteria**
  - the settings row is keyed on `Team`; a team with no override returns the company default;
  - the reader is whitelisted, returns the **effective** settings for `(team, user)`, and never
    raises for a team the user cannot see — it returns the default, or a permission error, and says
    which;
  - the settings survive a `bench migrate` on a fresh site (i.e. the *shape* is in the JSON, not
    created once in the console).
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.team.test_team --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PERM-5.2 — Writing the settings, and who may write them
- **Status** `TODO`
- **Scope** the controller above, plus the DocPerm block if *Decision 1* chose a standalone DocType.
  Tests: `eos_core/test_permissions.py`.
- **Acceptance criteria**
  - a `Manager` and above may set the settings for a team they are in; a `Team Member` and an
    `Observer` are refused, and the refusal is a `frappe.PermissionError` naming the role;
  - the settings are not a permission bypass: a `Manager` in Team B cannot set Team A's settings;
  - the `DOCPERM_MATRIX` test is extended, not bypassed, if a new DocPerm block was added.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PERM-5.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §3h (the DocPerm table, if it changed), `AGENTS.md` (the state
  table), `docs/TODO.md`.
- **Acceptance criteria** the chosen representation and the role rule are written down; `TODO.md`
  moves `PERM-5` to *Done* with the SHA and states plainly that the **UI** half is `UI-5` and is not
  done — this is exactly the `code+tests` vs `reachable` distinction the queue is built around, and
  `PERM-5` is the item where it is easiest to overstate.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PERM-5.1`. Nothing has been implemented; no task has been started.

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

All three tasks, plus `UI-5` for the reachable half.
