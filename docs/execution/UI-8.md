# UI-8 — Measurable Manager surface

## Parent TODO

`UI-8` — **S2** · Measurable Manager surface.
Block C (Phase 7: UI). Added because `PERM-4`'s own note records that Block C had no item for the
surface, and `PERM-4`'s **Done when** cannot be satisfied without it.

**Scope**: Ninety's Measurable Manager — the "KPI Manager" screen, *"Accessible only to Admins,
Owners, or Coaches/Implementers"*. A list of a team's measurables with per-row Duplicate, Delete
and Archive, reachable in the browser. **Add Existing Measurable** is deliberately *not* in scope
here; it is `PARITY-1`.

## Objective

The Measurable Manager exists as a browser-reachable surface, scoped to the viewer's teams like
every other surface, and every endpoint it calls is refused to a `Manager`, a `Team Member` and an
`Observer` by a server-side gate rather than by a hidden link.

## Dependencies

- `PERM-2`, `PERM-6` (both closed) — the scoping layer and the DocPerm blocks exist.
- **`PERM-4`** owns the gate itself. `UI-8` builds the surface and **consumes** `PERM-4`'s predicate;
  it does not define its own role rule. If `UI-8` starts first, land `PERM-4.1` before wiring any
  endpoint.
- Independent of `UI-1` — the Measurable Manager is its own page.
- `DATA-3` is **not** required: `EOS Metric` already carries `archived`.

## Decisions to settle before implementing

1. **The page is a list, not a grid.** Ninety's Measurable Manager manages measurables; it does not
   display period data. Building it on `UI-1`'s grid would borrow the wrong mental model and drag in
   the grid's permission path for no gain.
2. **Read through `frappe.get_list`.** Same rule as `UI-1.1` — `get_all` bypasses the
   `permission_query_conditions` layer and would show other teams' measurables.
3. **Delete here goes through `validate_content_deletion`, which is stricter than the surface.** A
   `Manager` cannot reach this surface at all, and the surface's Delete is therefore a
   Manager-and-above operation — but the ownership guard is the one Ninety footnotes and it stays
   where `PERM-12` put it, in `EOSMetric.on_trash`. Do not add a second, looser delete path.
4. **"Add Existing Measurable" is `PARITY-1`, not here.** The two share a page but not a schema, and
   they have different dependencies. Keep them separable so `PARITY-1` is not blocked behind a UI
   decision.

## Execution Tasks

### UI-8.1 — The Measurable Manager list
- **Status** `TODO`
- **Scope** a whitelisted list endpoint, naturally beside the rest in `eos_core/api.py` or on
  `EOSMetric`; plus the page host. The host decision is `UI-1.3`'s and should be **reused**, not
  re-made — if `UI-1` has landed, copy its mechanism.
- **Acceptance criteria**
  - a list of the viewer's measurables with Owner, Group, Goal, Status, Indicator, `archived`;
  - team-scoped: a `Manager` sees their teams' measurables and no others, proven by a test;
  - archived rows are excluded from the default list and reachable through an archive toggle;
  - the endpoint refuses a non-qualifying role **before** returning anything.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  plus a manual browser pass at two teams, recorded.

### UI-8.2 — Duplicate, Delete and Archive rows
- **Status** `TODO`
- **Scope** the same surface. **Duplicate reuses `PARITY-1`'s implementation if it has landed**; if
  it has not, leave the action out and record the gap rather than building a second one.
- **Acceptance criteria** each action is a separate endpoint with its own check; Delete shows the
  ownership consequence (`validate_content_deletion`) rather than failing opaquely; Archive flips the
  existing `EOS Metric.archived` flag; a partial failure is reported per row.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  plus manual passes as `Owner`, `Admin`, `Coach` (allowed) and as `Manager` / `Team Member` /
  `Observer` (refused, with the server's message shown), all recorded.

### UI-8.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` (§3h's gate list and §3c's scorecard section), `AGENTS.md`,
  `docs/TODO.md`.
- **Acceptance criteria** the docs name the surface, who reaches it, and what it does **not** include
  (Add Existing Measurable); `TODO.md` moves `UI-8` to *Done* with the SHA. `PERM-4` may then close.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`UI-8.1`. Nothing has been implemented; no task has been started.

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

All three tasks.
