# PARITY-2 — Auto-seeded default measurables

## Parent TODO

`PARITY-2` — **S3** · Auto-seeded default measurables.
Block D (Ninety parity features with no representation at all).

**Scope** (verbatim from `TODO.md`): on account creation. Ninety ships 17 (or the 20 financial ones,
depending on doc version) — **verify the count against Ninety's current docs before implementing, do
not take 17 or 20 on trust from the roadmap.**

## Objective

A new organization gets Ninety's default measurables, seeded from a versioned, cited list rather than
from a remembered number, exactly once, and with a documented story for what happens when the
organization has no team or no `Player` yet — which, at account creation, it never does.

## Dependencies

- None. `Organization`, `Team`, `Player`, `Scorecard`, `EOS Metric` and the engine all exist.
- Independent of every other open item, and the only Block D item with no permission or model
  dependency. It is the cheapest item in this block.

## Decisions to settle before implementing

1. **"Account creation" is `Organization` insertion in this app.** The org tree is
   `Organization` → `Team` → `Player`, and an `Organization` is the root. Confirm that is what Ninety
   means by an account, and confirm whether Ninety seeds per **team** or per **organization** — that
   changes the answer to *Decision 3* entirely.
2. **The list is data, and it belongs in a versioned file.** A Python constant or a JSON file inside
   the app, with each entry carrying its `unit_type`, `operator`, `rollup` and Ninety's own
   grouping. Not a DocType row created once, and not typed from memory. The roadmap's "17 or 20" is
   exactly the failure this decision prevents.
3. **Seeding runs with no team and no `Player` in existence.** `validate_owner_team` returns early
   when `self.team` is falsy, and org-wide measurables (`team is null`) are company-wide per
   `architecture.md` §3b and already appear in `Scorecard._rollup_metrics` and
   `ScorecardReport._collect_metric_groups`. So org-wide seeding works today. If Ninety seeds
   per team, the alternative is a default team + a `Player` for the creator, and that is a
   **product** decision, not just a technical one.
4. **Seeding must be idempotent and re-runnable.** A user who deletes a default measurable should be
   able to re-seed, and re-seeding must not duplicate. `EOS Metric` is autonamed
   `field:metric_name`, so a second seed of the same name raises a duplicate rather than a silent
   copy — convenient, but it means "re-seed" is a real operation with a real error mode, not a no-op.
5. **Does seeding include historical entries?** Ninety's defaults may ship with values for past
   periods. If so this stops being a small item and starts overlapping `PARITY-4` (backfilling).
   **Check Ninety's docs;** if entries are included, split the item rather than smuggling it in.

## Execution Tasks

### PARITY-2.1 — The verified default list
- **Status** `TODO`
- **Scope** a new versioned data file in the app carrying Ninety's default measurables, each with
  `metric_name`, `unit_type`, `operator`, `rollup`, `group` and any frequency. A header naming
  Ninety's source page and the date the list was taken.
- **Acceptance criteria** the file is committed to git (it is app data, not a database row); every
  entry carries the fields `EOSMetric.validate` requires; the count in the file is stated in the file
  and the source is cited; **no number is taken from `roadmap.md`**.
- **Verification** the file loads, the count matches what the file says, and every entry passes
  `validate_formula_syntax`-equivalent constraints (no entry is `is_smart` with no formula — none
  should be, but check).

### PARITY-2.2 — The seeding action
- **Status** `TODO`
- **Scope** a whitelisted `seed_default_measurables` method, wired to `Organization.after_insert` only
  if auto-seeding on creation is what Ninety does, plus a manual re-seed path. Tests in a new
  `test_organization.py` (`DEBT-6` notes `Organization` has no test file — this creates one).
- **Acceptance criteria**
  - seeding an `Organization` with no team produces valid `EOS Metric` rows, each with
    `owner_user` defaulted by `before_insert` and `team` empty (org-wide);
  - running it twice does not duplicate, and reports what it skipped;
  - a partial failure rolls back cleanly and says which measurables it created;
  - a seeded measurable appears in `Scorecard.get_rollup_view` and in a `Scorecard Report` for an
    org-wide team, proving it is wired into the existing consumers.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  New module: `eos_core/eos_core/doctype/organization/test_organization.py`. A manual console pass on
  `resolv.localhost` creating an Organization and counting the resulting `EOS Metric` rows, recorded.

### PARITY-2.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §2 / §3b, `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs state the verified count, the source, whether it seeds per org or
  per team, and whether historical entries are included; `TODO.md` moves `PARITY-2` to *Done* with
  the SHA.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PARITY-2.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- `Organization` has an empty controller and no test file, which `DEBT-6` records as a scope
  question. This item gives the controller a purpose and creates the test file. **Check `DEBT-6` after
  this lands** and update its scope note rather than counting the same work twice.
- The roadmap's "17 or 20" is stale by its own admission; `PARITY-2.1` replaces it with a cited
  number and `roadmap.md`'s Phase 7 line should be corrected at close-out.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All three tasks.
