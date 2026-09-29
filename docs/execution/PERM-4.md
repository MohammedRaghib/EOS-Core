# PERM-4 — Only Owner / Admin / Coach see the Measurable Manager

## Parent TODO

`PERM-4` — **S2** · Only Owner / Admin / Coach see the Measurable Manager.
Block B (Phase 6: Permissions & Roles). One of the three items Block B left open, and **UI-blocked**.

**Problem** (verbatim): Ninety — *"Accessible only to Admins, Owners, or Coaches/Implementers.
Managers and Team Members/Managees cannot access the Measurable Manager."*

**Done when** (verbatim): the Measurable Manager surface exists, is gated to Owner / Admin / Coach, and
a test asserts each of the six roles sees or does not see it — with a fourth assertion that a Manager
can still create a measurable from the scorecard while being denied the Manager surface.

**Note recorded in the item**: Block C has no UI item for the Measurable Manager surface. It is now
`UI-8`, and this item is blocked on it.

## Objective

The Measurable Manager is a real surface, gated **server-side** to Owner, Admin and Coach, and every
endpoint it calls is gated independently of the UI. A `Manager` who is denied the surface can still
create a Measurable from the scorecard. Seven tests: one per role, plus that seventh assertion.

## Dependencies

- **`UI-8`** — the surface itself. This item cannot close before it exists, because its **Done when**
  is about the surface being gated, not about a predicate existing.
- `PERM-2` (closed) — the DocPerm matrix is correct and **must not change**. See *Decision 2*.
- `PERM-6` (closed) — team scoping applies to the surface's data, exactly as it does to the grid.
- Independent of `UI-1`; the Measurable Manager is its own page, not part of the grid.

## Decisions to settle before implementing

1. **The gate is a role predicate, and it lives in `eos_core/permissions.py`.** It belongs beside
   `can_manage_metrics`, `can_own_content` and `MANAGE_METRICS_ROLES`, following the same shape, so
   there is one place that answers "what may this role do". Do not re-derive the role list in the JS
   — the JS may hide the control, but the server decides.
2. **This must not be "solved" by removing DocPerm grants.** Ninety hides the Measurable Manager
   from `Manager` while its capability matrix grants `Manager` full `create`/`write`/`delete` on both
   `EOS Metric` and `Measurable Group` — and it must, because a Manager creating measurables on a
   scorecard is Ninety behaviour. Narrowing the DocPerm to satisfy the visibility rule would break
   the capability matrix, and `test_docperm_matrix_matches_the_ninety_capability_table` will say so
   loudly. **The item gates the surface, not the grants.**
3. **`Manager` and `Team Member` are refused the surface; `Observer` is refused too.** The item's
   wording is "Manager and Team Member cannot access it"; Observer is a fortiori case, and the
   seven-test requirement covers all six roles anyway.
4. **A role gate is not a row filter.** A `Manager` who somehow reaches a Manager endpoint must be
   refused by the endpoint, not merely shown fewer rows. The permission tests must call the endpoint.

## Execution Tasks

### PERM-4.1 — The predicate and the server-side gate
- **Status** `TODO`
- **Scope** `eos_core/permissions.py` (a new role tuple and predicate, e.g. alongside
   `MANAGE_METRICS_ROLES`), and every endpoint `UI-8` exposes.
- **Acceptance criteria**
  - a single predicate answers "may this user open the Measurable Manager" for the six roles, is
    `True` for `Administrator` and any `System Manager` holder (matching `is_privileged`), and reads
    one role list rather than restating the names in each caller;
  - every endpoint the surface calls refuses a non-qualifying role with `frappe.PermissionError`
    naming the role, **before** it does any work;
  - `eos_core/permissions.py`'s DocPerm blocks are untouched.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  The `DOCPERM_MATRIX` test must pass **unchanged**. If it needed editing to make this item work, the
  item was done wrong.

### PERM-4.2 — The seven role tests
- **Status** `TODO`
- **Scope** `eos_core/test_permissions.py`.
- **Acceptance criteria** one test per role for the surface gate — Owner, Admin, Coach, `Manager`,
  `Team Member`, `Observer` — plus the seventh assertion: a `Manager` is refused the Manager surface
  **and** can still create a Measurable from the scorecard. That seventh test is the one that stops
  this item from being "solved" by narrowing grants, so it must exist and must fail if the grants
  are narrowed.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  ```
  Mutation check: remove `Manager` from `EOS Metric.create` and confirm the seventh test **fails**,
  then restore it.

### PERM-4.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §3h (a new guard — this is the fifth rule a DocPerm cannot
  express, alongside the four already listed), `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** §3h's "The four rules a DocPerm cannot express" section becomes five, with
  the surface gate and its explicit note that it is a **gate, not a grant narrowing**; `TODO.md`
  moves `PERM-4` to *Done* with the SHA and both boxes ticked, referencing `UI-8`'s SHA.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PERM-4.1`. Nothing has been implemented; no task has been started. The predicate can be built
immediately; **close-out is blocked on `UI-8`.**

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- **Block C had no item for this surface.** `TODO.md` said so and asked for one to be added when the
  item starts. That item is now `UI-8`; the dependency is recorded in both files so neither can be
  closed while the other is open.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All three tasks, with close-out gated on `UI-8`.
