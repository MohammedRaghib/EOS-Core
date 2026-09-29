# DEBT-7 — Five DocTypes enforce uniqueness only in Python, with no DB index

## Parent TODO

`DEBT-7` — **S3** · Five DocTypes enforce uniqueness only in Python, with no DB index.
Block F (Code debt). **`DEBT-12` closes as part of this item.**

**Where** (verbatim): `rock.json`, `scorecard.json`, `level_10_meeting.json`, `scorecard_report.json`,
`quarterly_review.json`.

**Problem** (verbatim): all five are autonamed from an inherently unique key, but the column carries
no `unique: 1`, so `show index` returns nothing and a duplicate is only caught by an app-level
`frappe.db.exists` check — not race-proof. By contrast `tabTo Do` (`todo_name`), `tabVTO`
(`organization`) and `tabEOS Metric` (`metric_name`) all have real `Non_unique=0` indexes.

**Done when** (verbatim): the unique fields are flagged and `bench --site resolv.localhost migrate`
has been run and `show index` confirms the index exists.

## Objective

The five DocTypes' identity is enforced by the database, so two concurrent requests cannot create a
duplicate — and `Scorecard` has a real index on its identity columns instead of only the `creation`
index InnoDB adds anyway (`DEBT-12`).

## Dependencies

- None. No other open item depends on it, and it does not depend on anything.
- **`DEBT-12`** is explicitly closed by this item: "`Scorecard` has a useless non-unique index" and
  "Done when: handled as part of `DEBT-7`".
- Interacts with `DATA-2` (closed): `Scorecard.validate_immutable_identity` makes `team` and
  `timeframe` immutable, which is what makes the name and the field pair unable to diverge. A unique
  index on the pair is consistent with that; it does not contradict it.

## Decisions to settle before implementing

1. **`unique: 1` cannot express what four of these five need. This is the central finding.**
   Frappe's `unique` is a `Check` on a `DocField` (`frappe/core/doctype/docfield/docfield.json`) and
   is validated as valid only for `Data`, `Link` and `Read Only` fieldtypes
   (`frappe/core/doctype/doctype/doctype.py:1460-1484`). It produces a **single-column** unique
   index. There is no composite-unique flag. The four composite identities are:
   - `Scorecard` (team, timeframe)
   - `Level 10 Meeting` (team, meeting_date)
   - `Scorecard Report` (team, week_start_date)
   - `Quarterly Review` (team, period_start)

   **Only `Rock.rock_name` can take `unique: 1`** — it is a `Data` field and it really is unique on
   its own. Marking `Scorecard.team` unique would be actively wrong: a team has four Scorecards, one
   per timeframe, and the app would refuse the second.
2. **So the composite index has to be created by a patch, not by the JSON.** A patch that issues
   `create unique index` under `[post_model_sync]` runs on a fresh site as well as an existing one,
   which satisfies "reproduces on a fresh site" — the same argument `UI-7` and `UI-1.3` make about
   data-versus-code. **Record this deviation from the item's "Done when" wording explicitly**, and
   consider whether the item's wording should be corrected rather than the work bent to match it.
3. **An index cannot be created on data that already violates it.** Before creating the index, check
   for existing duplicates and either refuse with a clear message naming them or delete them — never
   `DROP` and recreate the table to force it. `doctype.py:1476-1484` performs exactly this check for
   the flag path; the patch needs its own.
4. **`Scorecard`'s `creation` index (DEBT-12) is not dropped by adding another index.** It is useless,
   not harmful, and Frappe's schema sync owns it. Removing it is a separate manual step; say whether
   this item removes it or leaves it.
5. **Column widths matter for an index.** `Team` is autonamed `field:team_name`; confirm the real
   column types for `team`, `meeting_date`, `week_start_date`, `period_start` and `timeframe` before
   writing DDL, so the index matches what the application stores.

## Execution Tasks

### DEBT-7.1 — `Rock.rock_name`: the one case the flag can express
- **Status** `TODO`
- **Scope** `rock.json` (`unique: 1` on `rock_name`), then `bench migrate`. `Rock.validate` already
  checks the same thing in Python (lines 24–26); the two must agree, and the Python check may stay
  because it produces a friendlier message.
- **Acceptance criteria** `tabRock` reports a `Non_unique=0` index on `rock_name`; a duplicate still
  raises a `frappe.DuplicateEntryError` or the existing `frappe.throw` message, not both at once in
  a confusing order; existing tests in `test_rock.py` pass.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  cat > /tmp/q.py <<'EOF'
  print(frappe.db.sql("show index from `tabRock` where Key_name != 'PRIMARY'"))
  EOF
  bench --site resolv.localhost console < /tmp/q.py
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.rock.test_rock --site resolv.localhost
  ```

### DEBT-7.2 — The four composite indexes, via a patch
- **Status** `TODO`
- **Scope** a new `eos_core/patches/…` module registered under `[post_model_sync]`, plus a duplicate
  pre-check inside the patch. No `*.json` change is required for these four.
- **Acceptance criteria**
  - `tabScorecard`, `tabLevel 10 Meeting`, `tabScorecard Report` and `tabQuarterly Review` each
    report a `Non_unique=0` index over their identity columns;
  - the patch is idempotent — running it twice, or on a site that already has the index, does not
    fail;
  - the patch refuses, with a message naming the offending rows, if existing data already violates
    the identity, and it deletes nothing;
  - the patch is registered so a **fresh site** gets the indexes, verified by reading `patches.txt`.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  cat > /tmp/q.py <<'EOF'
  for t in ("tabScorecard", "tabLevel 10 Meeting", "tabScorecard Report", "tabQuarterly Review"):
      print(t, frappe.db.sql(f"show index from `{t}` where Key_name != 'PRIMARY'"))
  print([r[0] for r in frappe.db.sql("select patch from `tabPatch Log` where patch like '%eos_core%' order by creation desc limit 3")])
  EOF
  bench --site resolv.localhost console < /tmp/q.py
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Concurrency test: two inserts of the same identity in one transaction must leave exactly one row,
  and the app's existing `frappe.throw` must not mask the database error into a misleading message —
  `DATA-2` is the precedent for that kind of message bug.

### DEBT-7.3 — `DEBT-12`: the `Scorecard` `creation` index
- **Status** `TODO`
- **Scope** decided in *Decision 4*; recorded either way.
- **Acceptance criteria** `tabScorecard` has a real index on `(team, timeframe)`; whether the
  `creation` index was dropped or left is stated in `docs/architecture.md` §7, which currently claims
  `Scorecard` "has **no** index on team+timeframe".
- **Verification** the same `show index` check as `DEBT-7.2`, and:
  ```bash
  cd /workspace/development/frappe-bench/apps/eos_core
  grep -rn "no\*\* index on team+timeframe\|no index on team" docs/ AGENTS.md
  ```

### DEBT-7.4 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §7 (two bullets describe the current weak uniqueness), `AGENTS.md`,
  `docs/TODO.md`.
- **Acceptance criteria** both `TODO.md` items move to *Done* with SHAs; the docs state that four of
  the five identities are enforced by a **patch-created composite index**, not by the `unique` flag,
  and why. **Do not claim the JSON flags something it cannot express.**
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`DEBT-7.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- **The item's "Done when" is not achievable as written for four of the five DocTypes.** Frappe has
  no composite-unique flag. Rather than narrowing `unique: 1` onto a `team` column — which would
  break the app, since a team legitimately holds four `Scorecard` rows — the plan uses a patch. The
  item's wording should be corrected in `TODO.md` at close-out, or the deviation recorded in *Done*;
  either way it must be visible, because a future reader who trusts the wording will try the flag.
- `DEBT-12` is a duplicate of part of this item by its own admission, and closes here.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All four tasks.
