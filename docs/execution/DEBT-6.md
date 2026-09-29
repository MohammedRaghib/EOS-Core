# DEBT-6 — Three empty controllers with no tests

## Parent TODO

`DEBT-6` — **S3** · Three empty controllers with no tests.
Block F (Code debt). The title says three; the scope note says the real number is **twelve**, and the
ten Child tables are an explicitly undecided scope question.

**Where** (verbatim from `TODO.md`): `organization/organization.py`,
`scorecard_entry/scorecard_entry.py` — `player/player.py` was resolved by `DATA-1` on 2026-09-28 and
now has a validator and `test_player.py` (4 tests).

**Done when** (verbatim): each either has a test file proving it is intentionally passive, or has the
validation it should have. **Empty controllers are fine; untested *and* undocumented is not.**

## Objective

Every bare-`pass` controller in the app is accounted for: it is either given the validation it
should have, or a test that proves it is intentionally passive, and the decision is recorded. No
controller is left in the state the item describes — present, empty, untested and unexplained.

## Dependencies

- None. This is the cheapest item in Block F apart from deleting files.
- `PARITY-2` gives `organization` a purpose (auto-seeding defaults) and creates
  `test_organization.py`. **Sequence this after `PARITY-2` if both are queued**, and update this
  plan's scope note rather than counting the same test file twice.
- `DATA-1` (closed) is the precedent for this item's shape: an empty controller gained a validator
  (`Player.validate_unique_seat_in_team`) and a test file. Read that commit before starting.

## Decisions to settle before implementing

1. **The ten Child tables are in scope, and here is why.** `TODO.md` left this undecided on purpose,
   to avoid silently widening the item. It is the same category of decision as `Scorecard Entry`: a
   child DocType's controller is passive unless the parent needs it to validate. Include them, and
   record the decision so the next audit does not re-open it.
2. **The twelve controllers, as enumerated by the item:**
   `organization`, `scorecard_entry`, `meeting_agenda_item`, `meeting_to_do`, `rock_milestone`,
   `scorecard_report_metric`, `to_do_item`, `vto_core_focus`, `vto_marketing_strategy`,
   `vto_3_year_picture`, `vto_1_year_plan`, `vto_quarterly_rocks`. Ten are Child tables.
3. **A "test proving it is intentionally passive" must be a real test, not a tautology.** A test
   that asserts the module has no validation is worthless. What is wanted is a test that **uses** the
   child through its parent and asserts the invariants the parent is responsible for — that is what
   documents "passive". One module per DocType following the `test_player.py` shape.
4. **Two of the twelve may genuinely need validation, and the audit should not assume otherwise.**
   `rock_milestone` participates in the completion gate (`Rock.validate` reads
   `milestone.completed`), and `scorecard_report_metric` is the stored snapshot. Check both before
   writing a test that says "passive".

## Execution Tasks

### DEBT-6.1 — Audit the twelve and record the decision per controller
- **Status** `TODO`
- **Scope** the twelve controllers listed in *Decision 2*; a table in `docs/architecture.md` §5 (or a
  new subsection) recording, per controller: passive-and-why, or the validation it needs.
- **Acceptance criteria** every one of the twelve has a row; the two candidates in *Decision 4* have
  been checked against how their parents actually use them, not assumed; the scope decision from
  *Decision 1* is written down.
- **Verification** the twelve names in the table are exactly the bare-`pass` controllers, and no
  controller with validation is listed:
  ```bash
  cd /workspace/development/frappe-bench/apps/eos_core
  for f in $(find eos_core -name '*.py' -path '*/doctype/*' ! -name 'test_*' ! -name '__init__.py'); do
    body=$(grep -vE '^\s*(import|from|class|#|$)' "$f" | tr -d '[:space:]')
    [ "$body" = "pass" ] && echo "bare pass: $f"
  done
  ```
  Every line it prints must appear in the table; any that does not is a controller the audit missed.

### DEBT-6.2 — Test modules for the passive controllers
- **Status** `TODO`
- **Scope** `test_<name>.py` beside each controller the audit marked passive, following
  `doctype/player/test_player.py`'s shape and the existing per-doctype test layout.
- **Acceptance criteria** each test exercises the child through its parent and asserts the parent's
  invariant; the new test count is recorded; no test asserts only that a field is absent.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  The suite must grow by exactly the number of tests added, and the count in `AGENTS.md`'s table must
  be re-derived with `grep -rc 'def test_'` rather than edited.

### DEBT-6.3 — Validation for any controller the audit found deficient
- **Status** `TODO`
- **Scope** the controllers `DEBT-6.1` found needed one — currently expected to be none, possibly
  `rock_milestone` and `scorecard_report_metric`.
- **Acceptance criteria** each added validator has a positive and a negative test, and a refusal
  message that names the field and the offending value; no validator is added "for symmetry".
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Mutation check: remove each validator and confirm its negative test fails.

### DEBT-6.4 — Close-out and documentation
- **Status** `TODO`
- **Scope** `AGENTS.md`'s test table, `docs/TODO.md`.
- **Acceptance criteria** the audit table is in the docs; the item's own count is corrected from
  "three" to twelve with the scope decision recorded; `TODO.md` moves `DEBT-6` to *Done* with the
  SHA, or to a narrower item if the twelve were not all resolved.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`DEBT-6.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

None yet. If `PARITY-2` lands first, `organization` is already resolved and this plan should be
narrowed and the item's scope note updated — not silently kept as written.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All four tasks.
