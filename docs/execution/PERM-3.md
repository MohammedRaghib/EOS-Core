# PERM-3 — Team Members may reorder measurables they do not own

## Parent TODO

`PERM-3` — **S2** · Team Members may reorder measurables they do not own.
Block B (Phase 6: Permissions & Roles). One of the three items Block B left open, and **UI-blocked**,
not permission-blocked.

**Done when** (verbatim from `TODO.md`): the grid exists and a user holding only `Team Member` can
drag a measurable owned by someone else inside its group, is refused outside it, and cannot rename or
delete it — a test per case.

## Objective

A `Team Member` can move a Measurable they do not own to another position **within its own group**,
is refused when the move would take it out of that group or out of their teams, and still cannot
rename or delete a `Measurable Group`. Each of those three cases has a test, and the `order` integer
trap is pinned by a test of its own.

## Dependencies

- **`UI-1`** — the grid is the drag surface. This item is blocked until the grid exists; it is not
  blocked on any permission work.
- `PERM-2` (closed) — the DocPerm half is already correct and tested: a `Team Member` has `write` on
  `EOS Metric` and is read-only on `Measurable Group` (`create`/`write`/`delete` all `0`, verified
  live), so renaming or deleting a *group* is already impossible for them.
- `PERM-7` / `PERM-12` (closed) — the `TEAM_MEMBER_EDITABLE_FIELDS` allow-list already permits
  `group`, `description`, `entries`, `min_value`, `max_value` and `target_value`, so the group move
  and the goal a reorder may carry are already legal. `test_a_team_member_may_adjust_a_measurable_goal_and_group`
  pins that.

## Decisions to settle before implementing

1. **There is no field to write the order into. This is the real work of the item.** `EOS Metric`
   declares `metric_name, owner_user, team, target_value, operator, min_value, max_value, frequency,
   unit, unit_type, rollup, is_smart, formula, scorecard, group, archived, description, entries` —
   no ordering column. `Measurable Group.order` orders **groups**, not the measurables inside one,
   so the queue's mention of that field is about group ordering, not this item. Settle the
   representation first:
   - a new `Int` field on `EOS Metric` (e.g. `position`, in a group);
   - a child table of explicit order rows;
   - or accept Ninety's real behaviour if it is something else — **check Ninety's documented
     behaviour before building**, per `AGENTS.md` § Ground rules.
2. **A new field is blocked for `Team Member` by default, on purpose.** `TEAM_MEMBER_EDITABLE_FIELDS`
   is an allow-list, so a field added later is refused to a `Team Member` until someone has checked
   Ninety for it. Adding the ordering field to that set is a deliberate, documented act — and the
   existing test that pins the allow-list will fail if it is forgotten, which is the correct
   behaviour.
3. **`Int` means `0` means "unset".** `Measurable Group.order` is `int NOT NULL DEFAULT 0`, and
   `AGENTS.md` records this as a real bug source. A new ordering column inherits it exactly: a
   position of `0` is indistinguishable from "never ordered". Either accept it and make the sort
   total (fall back to `metric_name`) or store `0`-based positions and say so.
4. **Where the group boundary is enforced.** A move that changes `group` is a `group` write, which a
   `Team Member` already may do. Ninety's rule is about reordering *within* a group, so the endpoint
   must refuse a cross-group move for a `Team Member` even though the field edit would otherwise
   pass — a narrower rule than `PERM-7`, enforced in the reorder endpoint rather than in
   `validate_data_entry_only`, which is about the form path.

## Execution Tasks

### PERM-3.1 — Settle and add the ordering representation
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/eos_metric/eos_metric.json`, then `bench migrate`. Tests in
  `test_eos_metric.py`.
- **Acceptance criteria** the chosen representation exists, defaults sanely on a new Measurable, and
  survives `bench migrate`; the sort is **total** — two ungrouped or two unpositioned measurables
  never come back in a nondeterministic order; a `Team Member` may write the ordering field (added to
  `TEAM_MEMBER_EDITABLE_FIELDS` if the chosen representation is a field on `EOS Metric`) and the
  existing `test_team_member_may_adjust_a_measurable_goal_and_group` still passes.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Record the chosen representation and Ninety's evidence in *Decisions* before moving on.

### PERM-3.2 — A reorder endpoint with the group boundary
- **Status** `TODO`
- **Scope** a whitelisted method, naturally on `EOS Metric` or in a small `eos_core/api.py`. Tests in
  `eos_core/test_permissions.py`.
- **Acceptance criteria**
  - a `Team Member` holding a seat in the team can reorder a Measurable **they do not own** to a new
    position **inside the same group**;
  - the same user is refused a move that changes the group, and refused a move to a Measurable in a
    team they have no seat in;
  - a `Team Member` is still refused `Measurable Group` rename and delete (already true — pin it);
  - a manager may reorder across the whole scorecard;
  - the endpoint returns the new order so the caller does not have to re-derive it.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  This is the "a test per case" the item's **Done when** asks for — three cases, three tests.

### PERM-3.3 — The drag surface on the grid
- **Status** `TODO`
- **Scope** the grid JS from `UI-1`; no new server code if `PERM-3.2` landed.
- **Acceptance criteria** a Measurable can be dragged to a new position within its group; a drop
  outside the group is refused client-side **and** server-side (the server refusal is the guarantee);
  the grid re-renders in the new order; an `Observer` sees no drag affordance at all.
- **Verification** manual browser pass as a `Team Member` on a measurable owned by somebody else,
  recorded in *Completed* — including the refused cross-group drop.

### PERM-3.4 — The `order = 0` trap, pinned
- **Status** `TODO`
- **Scope** tests only.
- **Acceptance criteria** a test proves `0` on the ordering field sorts as "unset", not "first"; a
  test proves the grid order is stable across two identical reorders; a test proves an unpositioned
  Measurable does not jump above positioned ones after a reorder.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PERM-3.5 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` (the ordering representation, in §3c, and `TEAM_MEMBER_EDITABLE_FIELDS`
  in §3h), `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs record the representation, the group-boundary rule and the `0`
  trap; `TODO.md` moves `PERM-3` to *Done* with the SHA and both boxes ticked.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PERM-3.1`. Nothing has been implemented; no task has been started. **Blocked on `UI-1`** — do not
start `PERM-3.3` or later until the grid exists.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- **The queue's framing of this item is slightly off and the plan corrects it.** `TODO.md` says the
  reorder "interacts with `Measurable Group.order`". That column orders groups; there is no field
  anywhere that orders a Measurable inside a group. The item is therefore **not** a small surface
  task — it needs a schema decision, which is why it has a plan at all.
- Consequently, `UI-1.8` must not invent an ordering column as a side effect of the grid. The two
  items touch the same decision and it is recorded in both files.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All five tasks, blocked on `UI-1`.
