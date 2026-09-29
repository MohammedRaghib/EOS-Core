# PARITY-1 — Add Existing Measurable + Duplicate

## Parent TODO

`PARITY-1` — **S2** · Add Existing Measurable + Duplicate.
Block D (Ninety parity features with no representation at all). The largest correctness-parity item
left, and no longer gated on anything — `PERM-9` closed on 2026-09-29.

**Scope** (verbatim from `TODO.md`): share one Measurable across teams with synced data.

**Note recorded in the item**: `PERM-6` makes this harder than it looks — a Measurable shared
across two teams can only have one `team`, so the sharing model has to answer which team a shared
Measurable's *entries* belong to before the scoping rule can stay true.

## Objective

A Measurable can be added to more than one team's scorecard, each team enters its own data against
it, every team sees only its own data, the permission scoping layer stays true, and a Measurable can
be duplicated outright onto another scorecard as an independent copy.

## Dependencies

- `PERM-9` (closed, `e00011d`) — a shared Measurable needs a real, reassignable `owner_user`, which
  now exists. This item was explicitly gated behind it and is now unblocked.
- `PERM-6` (closed) — the team-scoping layer. **This item changes what it operates on**, so
  `eos_core/permissions.py` and the 66 generated `test_visibility_<doctype>_<role>` tests are the
  regression net. If a condition in `eos_core/permissions.py` changes and those 66 do not all still
  pass, the change is wrong.
- `PERM-2`, `PERM-7`, `PERM-8`, `PERM-12` (all closed) — the DocPerm blocks, the field-level
  allow-list, the ownership guard and the ownership-scoped delete guard.
- `UI-8` — the Measurable Manager is where "Add Existing Measurable" is invoked from, but only if
  the surface exists. The model and the server work do **not** depend on it; only the button does.
- Independent of `UI-1`.

## Decisions to settle before implementing

1. **What "synced data" means — settle this first, because the two readings need different schemas.**
   `TODO.md` says "share one Measurable across teams with synced data". If each team entered
   *independent* data, the sharing representation is a set of teams on the Measurable and nothing
   else; if the data is genuinely **synced** — one set of entries shared by every team — then the
   entries are organisation-wide and the per-team scoping model is wrong in a way this item must
   confront head-on. **Check Ninety's current documentation before writing any code**, per
   `AGENTS.md` § Ground rules. This plan assumes neither reading.
2. **Where a Measurable's team set lives.** `EOS Metric.team` is a single `Link`. Candidates: a
   child table of teams on `EOS Metric`; a standalone sharing DocType; or `team` kept as the
   "home" team with a separate membership table. Whichever is chosen, `team_query_condition` and
   `has_permission` must read **the set**, and the 66 generated tests must be extended rather than
   allowed to drift.
3. **`Scorecard Entry` has no `team` column** — it is a child of `EOS Metric`, so it inherits the
   parent's single team. Under sharing, entries have to be attributable to a team, which means a
   new field on the child. This is a schema change with a patch, and it is the same class of change
   `PERM-9` was.
4. **`ensure_scorecard` links one `Scorecard`.** A Measurable on two teams' Weekly scorecards cannot
   keep a single `EOS Metric.scorecard` link, and `validate_group` asserts a group's scorecard equals
   the metric's. Both need to be re-derived per team, or the model needs a different shape. **This
   is the single largest consequence and it is why this item is not small.**
5. **`validate_owner_team` requires the owner to hold a `Player` seat in `self.team`.** With a team
   *set*, the rule needs restating: a seat in at least one of the teams, or in a specific one. Decide
   which, and record it — `architecture.md` §3b states the rule as a pair and will have to change.
6. **Duplicate is a separate capability from sharing.** Duplicate creates an independent copy; sharing
   keeps one Measurable. Ship them as two actions and two code paths. `UI-6.4`'s bulk duplicate must
   reuse whichever lands first, not build a third.

## Execution Tasks

### PARITY-1.1 — The written sharing design, grounded in Ninety's docs
- **Status** `TODO`
- **Scope** a new subsection in `docs/architecture.md` (§3c) recording: what Ninety's Add Existing
  Measurable actually does, the reading chosen in *Decision 1*, the team-set representation, the
  entry attribution rule, the `scorecard` / `group` re-derivation, the restated owner-in-team rule,
  and the permission-layer change. `TODO.md`'s rule 1 applies — this is documentation of a decision,
  not a redefinition of an existing item.
- **Acceptance criteria** the subsection names the chosen representation, lists every existing
  invariant it changes (`team`, `scorecard`, `group`, `validate_owner_team`, the scoping clause for
  `EOS Metric`), and cites Ninety's page for the behaviour it is modelled on. **No code yet.**
- **Verification** the subsection is read by someone who did not write it; specifically, it must be
  possible to implement the rest of the plan from it without re-deriving the model.

### PARITY-1.2 — Schema: the team set and entry attribution
- **Status** `TODO`
- **Scope** `eos_metric.json`, `scorecard_entry.json`, and a new child or standalone DocType per
  *Decision 2*; a patch under `[post_model_sync]`; then `bench migrate`.
- **Acceptance criteria**
  - a Measurable carries an explicit set of teams; existing rows get their single `team` as that
    set, via a patch that is idempotent and safe on a fresh site;
  - a `Scorecard Entry` carries the team it was entered for, defaulted sensibly for existing rows;
  - the schema works on a site that has never had a shared Measurable, with no manual step.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  cat > /tmp/q.py <<'EOF'
  print(frappe.db.sql("show columns from `tabScorecard Entry` like 'team'"))
  print([r[0] for r in frappe.db.sql("select patch from `tabPatch Log` where patch like '%eos_core%' order by creation desc limit 5")])
  EOF
  bench --site resolv.localhost console < /tmp/q.py
  ```

### PARITY-1.3 — Controller: add and remove a team on a Measurable
- **Status** `TODO`
- **Scope** `eos_metric.py`, `validate_group`, `ensure_scorecard`, `validate_owner_team`; tests in
  `test_eos_metric.py`.
- **Acceptance criteria**
  - a Measurable can be added to another team's scorecard and removed again, with validation: the
    target team must exist, and every team in the set must have a `Scorecard` of the Measurable's
    `frequency`;
  - removing the last team is refused, and removing a team that has entries attributed to it is
    refused or explicitly destructive — decide and write down which;
  - `validate_owner_team` follows the restated rule from *Decision 5*;
  - `ensure_scorecard` and `validate_group` resolve per team, and a Measurable on two teams reports
    both scorecards.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PARITY-1.4 — The permission layer reads the team set
- **Status** `TODO`
- **Scope** `eos_core/permissions.py` — `team_query_condition` and `doc_in_assigned_teams` for
  `EOS Metric` (and any new sharing DocType), and the 66 generated tests in `test_permissions.py`.
- **Acceptance criteria**
  - a team-scoped role sees a Measurable when **any** team in its set is one of its seats' teams;
  - a Measurable with no team remains company-wide, per `architecture.md` §3b;
  - a role with no seat still gets `1 = 0` and never a SQL error;
  - entries are scoped per team: a user in Team A does not see Team B's entries against a shared
    Measurable through any endpoint, and that is proven by a test, not asserted from the clause;
  - the `ROCK_COMPANY_SCOPE` and `OWNER_FALLBACK` branches are unchanged and their tests still pass.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  The generated family count must not have gone **down**. If a role × DocType combination stopped
  being generated, the new model is under-tested.

### PARITY-1.5 — Duplicate a Measurable
- **Status** `TODO`
- **Scope** a whitelisted method, with tests in `test_eos_metric.py` and `test_permissions.py`.
- **Acceptance criteria**
  - duplicates a Measurable onto a target team's scorecard as an **independent** row, with its own
    team, its own `owner_user` (defaulting to the caller or explicitly supplied), its own groups, and
    no shared identity with the source;
  - the source is unchanged;
  - whether historical entries are carried over is an explicit parameter with a documented default —
    say which, do not leave it implicit;
  - the duplicate's name does not collide with the source: `EOS Metric` is autonamed
    `field:metric_name`, so a same-named duplicate must be refused with a clear message or renamed by
    an explicit rule. **Resolve this before coding**; it is a real collision, not a theoretical one.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PARITY-1.6 — The surface
- **Status** `TODO`
- **Scope** the Measurable Manager from `UI-8`; no new server work if `PARITY-1.1`–`PARITY-1.5`
  landed.
- **Acceptance criteria** an "Add Existing Measurable" action that searches the caller's reachable
  measurables and adds one; a Duplicate action; a per-row result on partial failure; a `Manager` sees
  neither control, because `PERM-4` gates the whole surface.
- **Verification** manual browser pass as `Owner` and as `Manager`, recorded. Plus a manual pass
  proving Team A's entries are not visible from Team B's scorecard.

### PARITY-1.7 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §3b and §3h, `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** §3b's owner-in-team rule and §3h's per-DocType table reflect the new model;
  `TODO.md` moves `PARITY-1` to *Done* with the SHA and states which parts landed, since the two
  capabilities can legitimately land apart.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PARITY-1.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet. *Decisions 1–6* above are the open questions, not answers.

## Discovered Issues

- **The queue's own scope line and the item's difficulty note are in tension.** "Share one Measurable
  across teams with synced data" reads as one line of work; the note underneath correctly says it
  requires deciding entry attribution before the scoping rule can stay true. The plan follows the
  note. **No code should be written before *Decision 1* is settled against Ninety's current docs.**
- `EOS Metric` is autonamed `field:metric_name`, so Duplicate has a naming collision that has to be
  resolved deliberately.
- `UI-6.4` (bulk duplicate) is the same capability. Whoever lands first, the other must reuse it.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**
  (185 integration + 63 unit). `test_permissions.py` is 96 in the run (30 hand-written + 66
  generated) and that number is the regression net for `PARITY-1.4`.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All seven tasks. It is unblocked, and it is the largest item in the queue.
