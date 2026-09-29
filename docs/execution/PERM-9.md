# PERM-9 — `EOS Metric.owner` is Frappe's creator, so a Measurable's owner is fixed

## Parent TODO

`PERM-9` — **S2** · `EOS Metric.owner` is Frappe's creator, so a Measurable's owner is fixed.
Block B (Phase 6: Permissions & Roles). The last open item in Block B and the item the queue names
as next to land. `PARITY-1` is gated behind it.

**Done when** (verbatim from `TODO.md`): a Measurable has a real, reassignable owner field distinct
from its creator, a `Team Member` can be assigned one, `validate_owner_team` is re-pointed at it
and re-documented, and `PERM-8`'s ownership guard covers both it and `Rock.owner_user`.

## Objective

`EOS Metric` carries a business owner field (`owner_user`) that is independent of Frappe's immutable
`owner` creator column, is freely reassignable after creation, can be assigned to a `Team Member`, and
is the field the ownership guard, the owner-in-team rule and the ownership-scoped delete guard all
read. The whole suite stays green and `bench migrate` has been run.

## Dependencies

- `PERM-2`, `PERM-6`, `PERM-7`, `PERM-8`, `PERM-12` — all closed. In particular `PERM-12` put
  `validate_content_deletion` in `EOSMetric.on_trash` reading `owner`, and `PERM-8` put
  `validate_content_owner` on `EOS Metric` and `Rock`.
- No open prerequisite. `DATA-3` is independent and untouched by this item.

## Decisions taken before implementing

1. **Field name `owner_user`, matching `Rock`.** `AGENTS.md` already records that `Rock.owner_user`
   is the free business field, so reusing the name keeps one vocabulary across the two accountable
   tools instead of introducing `metric_owner`.
2. **Remove the declared `owner` field rather than add a second one.** Frappe's `owner` column is in
   `frappe.db.DEFAULT_COLUMNS` (`frappe/database/database.py:97`), so it survives on the table and
   keeps being set by `Document.set_user_and_timestamp` — it simply stops being a business field.
   Verified this bench is on frappe `16.31.0`. A second declared field would have created the exact
   "two competing sources of truth" that `PERM-6` rejected a `User Permission` for.
3. **Default `owner_user` to the session user on insert.** The old field auto-filled with the
   creator, and ~20 call sites depend on that. Done in `before_insert`, so a later assignment is
   untouched.
4. **`Scorecard Report Metric.owner` is renamed too.** It is the same set-only-once collision on a
   Child DocType, it is a snapshot of the Measurable's owner, and leaving it named `owner` would
   preserve a second colliding field.
5. **`Scorecard.get_rollup_view` keeps `"owner"` as its JSON payload key.** It is the endpoint's own
   read contract with 11 tests and no consumer yet (`UI-3` is queued); only the DB column it reads
   changes.
6. **A backfill patch is required.** A site with existing `EOS Metric` rows would otherwise come
   back from `bench migrate` with a null `owner_user`. The live demo site has zero rows, so the
   patch is verified by construction and by `show columns`, and is idempotent.

## Execution Tasks

### PERM-9.1 — Schema: add `owner_user`, drop the declared `owner`, backfill
- Status: DONE
- Scope: `eos_core/eos_core/doctype/eos_metric/eos_metric.json`,
  `eos_core/eos_core/doctype/scorecard_report_metric/scorecard_report_metric.json`,
  `eos_core/patches/backfill_measurable_owner.py` (new), `eos_core/patches.txt`, then `bench migrate`.
- Acceptance criteria: `tabEOS Metric` and `tabScorecard Report Metric` each carry **both** an
  `owner` column (Frappe's creator, not declared in the JSON) and a new `owner_user` column; no
  declared field is named `owner`; the patch is registered under `[post_model_sync]` and is
  idempotent.
- Verification:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  cat > /tmp/q.py <<'EOF'
  print(frappe.db.sql("show columns from `tabEOS Metric` where Field in ('owner','owner_user')"))
  print(frappe.db.sql("show columns from `tabScorecard Report Metric` where Field in ('owner','owner_user')"))
  print([r[0] for r in frappe.db.sql("select patch from `tabPatch Log` where patch like '%backfill_measurable_owner%'")])
  EOF
  bench --site resolv.localhost console < /tmp/q.py
  ```

### PERM-9.2 — Controller and permission guard re-pointed at `owner_user`
- Status: DONE
- Scope: `eos_core/eos_core/doctype/eos_metric/eos_metric.py`, `eos_core/permissions.py`,
  `eos_core/eos_core/doctype/eos_metric/test_eos_metric.py`,
  `eos_core/test_permissions.py`.
- Acceptance criteria: `before_insert` defaults `owner_user` to the session user;
  `validate_owner_team`, `validate_owner_content_role` and `on_trash` all read `owner_user`;
  `validate_content_deletion` reads `owner_user`; the test that pinned the old bug
  (`test_a_measurable_owner_is_its_creator_and_cannot_be_reassigned`) is replaced with the new
  contract; every `EOS Metric` fixture in these two files passes `owner_user`.
- Verification:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  ```

### PERM-9.3 — Downstream consumers re-pointed at `owner_user`
- Status: DONE
- Scope: `eos_core/eos_core/doctype/scorecard_report/scorecard_report.py`,
  `eos_core/eos_core/doctype/scorecard/scorecard.py`, and the `owner` → `owner_user` fixture keys in
  `test_scorecard_report.py`, `test_scorecard.py`, `test_quarterly_review.py`, `test_issue.py`,
  `test_level_10_meeting.py`, `test_scorecard_engine.py`.
- Acceptance criteria: the report snapshot stores the business owner in `owner_user`; the rollup view
  reads `owner_user` and still returns it under the payload key `owner`; no `EOS Metric` fixture in
  the app still passes `owner`.
- Verification:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard_report.test_scorecard_report --site resolv.localhost
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard.test_scorecard --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

### PERM-9.4 — New tests for the behaviour `PERM-9` asked for
- Status: DONE
- Scope: `eos_core/test_permissions.py`.
- Acceptance criteria, one test each: (a) a Manager may **reassign** a Measurable's owner and the
  creator column does not move; (b) a `Team Member` **with a seat in the team** may be assigned one;
  (c) assignment to a user with no seat in the team is refused by the owner-in-team rule; (d)
  `PERM-8` refuses a `Coach`/`Observer` on the new field as well as on `Rock.owner_user`;
  (e) the `PERM-12` delete guard follows `owner_user`, not the creator — a Manager who created but no
  longer owns is refused, and one who owns but did not create is allowed; (f) `owner_user` defaults
  to the creating user on insert.
- Verification:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  ```

### PERM-9.5 — Documentation and close-out
- Status: DONE
- Scope: `docs/architecture.md`, `AGENTS.md`, `docs/TODO.md`.
- Acceptance criteria: `architecture.md` §3, §3b, §3h (guard 2, guard 4 and the "known gap" section)
  and §5 state the new field and no longer describe `owner` as a business field; `AGENTS.md`'s known
  gaps and test counts match reality; `TODO.md` moves `PERM-9` to *Done* with the commit SHA and
  the "Next item to land" footer is updated to `DATA-3`.
- Verification: the full suite, run once more after the docs edit:
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  plus `grep` sweeps proving no stale `owner` reference to `EOS Metric` remains.

## Current Task

None. `PERM-9` is complete and closed in `docs/TODO.md` as `e00011d`. The next item in the queue is
`DATA-3`.

## Completed

### PERM-9.1 — Schema: add `owner_user`, drop the declared `owner`, backfill

**Implemented**

- `eos_metric.json`: `field_order` entry `owner` → `owner_user` (position unchanged, so it still
  renders as the second column after `metric_name`); the declared Link field renamed in place,
  keeping `label: "Owner"`, `options: "User"`, `reqd: 1` and `in_list_view: 1`.
- `scorecard_report_metric.json`: same rename on the snapshot child, keeping `in_list_view: 1` and
  dropping nothing else. It has no `reqd` today and none was added — a report may legitimately be
  built before the metric's owner is known.
- `eos_core/patches/backfill_measurable_owner.py` (new) exposes `execute()`, which copies `owner`
  into `owner_user` for both tables wherever the new column is still empty, and is a no-op on a site
  that has not synced the column yet (`frappe.db.has_column`).
- `eos_core/patches.txt`: registered under `[post_model_sync]`, i.e. after the schema sync that
  creates the column.

**Files changed** `eos_metric.json`, `scorecard_report_metric.json`, `patches/backfill_measurable_owner.py`
(new), `patches.txt`.

**Verification performed**

`bench --site resolv.localhost migrate` — **passed**. First attempt failed with
`AttributeError: module 'eos_core.patches.backfill_measurable_owner' has no attribute 'execute'`;
Frappe's `patch_handler.execute_patch` requires the module to expose `execute`
(`frappe/modules/patch_handler.py:168`), so the function was renamed and migrate re-run clean.

Console verification after migrate:

| Check | Result |
|---|---|
| `show columns from tabEOS Metric where Field in ('owner','owner_user')` | `owner varchar(140)`, `owner_user varchar(140)` — **both** present |
| same for `tabScorecard Report Metric` | `owner`, `owner_user` — both present |
| declared fields named `owner`/`owner_user` on `EOS Metric` | `['owner_user']` only |
| declared fields named `owner`/`owner_user` on `Scorecard Report Metric` | `['owner_user']` only |
| `tabPatch Log` entry | `eos_core.patches.backfill_measurable_owner` |
| patch called twice more by hand | no error — idempotent |
| `EOS Metric.get_set_only_once_fields()` | `['creation', 'owner']` — `owner` still immutable, `owner_user` free |

**Results** the schema half of `PERM-9` is in place and the creator column survived, because
`owner` is in `frappe.db.DEFAULT_COLUMNS` (`frappe/database/database.py:97`) and is therefore never
dropped when a DocType stops declaring it. The live demo site has zero `EOS Metric` rows, so the
backfill has no rows to copy here and is proven only by idempotency and by the column list.

**Decisions made** none beyond the pre-implementation set. One incidental finding: an ad-hoc check
written as `"owner" in meta.get_set_only_once_fields()` returns `False` — the list holds
`frappe._dict` field objects, not strings. The table above lists fieldnames instead.

### PERM-9.2 — Controller and permission guard re-pointed at `owner_user`

**Implemented**

- `EOSMetric.before_insert` (new): `self.owner_user = self.owner_user or frappe.session.user`. This
  reproduces the old implicit behaviour — the creator used to be stamped into `owner` by Frappe — while
  leaving any explicit assignment alone, so reassignment after creation is unaffected.
- `validate_owner_team` reads `self.owner_user` in all four places, including both error messages, so
  a user named in a refusal is the business owner rather than the creator.
- `validate_owner_content_role` calls `validate_content_owner(self, "owner_user", "Measurable")`,
  matching `Rock`'s `"owner_user"` call, so `PERM-8` now covers both accountable tools by the same
  field name.
- `on_trash` calls `validate_content_deletion(self, "Measurable", owner_field="owner_user")`.
- `validate_content_deletion`'s `owner_field` parameter lost its `"owner"` default. No DocType in the
  app now has a business `owner` field, so the old default was a live invitation to re-introduce this
  exact bug; it is now required at every call site (there is exactly one).
- `TEAM_MEMBER_EDITABLE_FIELDS` deliberately **not** extended: `owner_user` is outside the allow-list,
  so a `Team Member` still cannot reassign ownership, matching Ninety's "locked to Manager and above".

**Tests changed** `test_a_measurable_owner_is_its_creator_and_cannot_be_reassigned` was **encoding the
bug** — it asserted `frappe.CannotChangeConstantError` on reassignment — so it was rewritten as
`test_a_measurable_owner_is_reassignable_and_distinct_from_its_creator`, which asserts the opposite
and additionally pins that the creator column does not move. `_assert_cannot_own` (the `PERM-8` helper
for both Coach and Observer) and `test_team_member_may_not_create_a_measurable` were re-pointed.

**Verification performed**

- `run-tests --module eos_core.eos_core.doctype.eos_metric.test_eos_metric` → **12/12 OK**.
- `run-tests --module eos_core.test_permissions` → **92/92 OK**.

### PERM-9.3 — Downstream consumers re-pointed at `owner_user`

**Implemented**

- `ScorecardReport._build_metric_block` fetches `owner_user` and puts it into the engine block under
  the key `owner` — the block dict already has its own vocabulary (`name`, `actual`, `target`,
  `statuses`), so the engine contract is untouched and `scorecard_engine.py` needed no change.
- `ScorecardReport.populate_snapshot` writes that value to the child's new `owner_user` field.
- `ScorecardReport._email_context` reads `row.owner_user` and still exposes `owner`, so
  `templates/emails/weekly_scorecard_report.html` (`{{ row.owner }}`) is unchanged.
- `Scorecard._rollup_metrics` fetches `owner_user`; `_rollup_metric` still returns the payload key
  `owner`, so the 11 `get_rollup_view` tests and the future `UI-3` consumer see no contract change.
- 15 `"owner": "Administrator"` fixture keys across seven test files became `"owner_user"`.

**Bug caught during this task, worth recording.** The first pass renamed the wrong side of the
mapping — `populate_snapshot` read `metric["owner_user"]`, but `build_scorecard_report` emits
`"owner"` — and produced `KeyError: 'owner_user'` on every `Scorecard Report` insert, which failed all
92 permission tests through their shared `setUp`. Because a failure in `setUp` leaves the fixture rows
behind, the next run also reported `DuplicateEntryError: 'PT Org'`, which looked like residue but was a
downstream symptom. Cleaning the `PT %` rows and fixing the mapping cleared both. The engine block
key is now deliberately **not** renamed, which is what makes the two vocabularies unambiguous.

**Verification performed**

- `run-tests --module eos_core.test_permissions` → **92/92 OK** after the fix.
- `run-tests --app eos_core` → **243/243 OK** (180 integration + 63 unit).

### PERM-9.4 — New tests for the behaviour `PERM-9` asked for

`test_permissions.py` 92 → **96**, and `test_scorecard_report.py` 14 → **15**.

| Test | What it pins |
|---|---|
| `test_a_measurable_owner_is_reassignable_and_distinct_from_its_creator` | a Manager reassigns; `owner_user` moves, `owner` does not |
| `test_a_new_measurable_takes_its_creating_user_as_its_owner` | the `before_insert` default |
| `test_a_team_member_with_a_seat_may_be_assigned_a_measurable` | the headline `PERM-9` consequence — a `Team Member` can own a Measurable, which was impossible when `owner` was the creator |
| `test_a_measurable_may_not_be_assigned_outside_its_team` | `validate_owner_team` now reads `owner_user`, so the refusal names the business owner |
| `test_the_delete_guard_follows_the_owner_and_not_the_creator` | `PERM-12`'s guard tracks `owner_user`: a Manager who **created but no longer owns** is refused; one who **owns but did not create** may delete |
| `test_a_coach_cannot_own_a_measurable_or_a_rock`, `test_an_observer_cannot_own_a_measurable_or_a_rock` | `PERM-8` now covers `EOS Metric.owner_user` as well as `Rock.owner_user` |
| `test_snapshot_stores_the_business_owner_not_the_creator` | the report child stores `owner_user` from the Measurable and leaves its own `owner` creator column alone |

**Verification performed** — each new test was confirmed to **fail against the old behaviour**, not
just pass against the new:

| Mutation | Result |
|---|---|
| `on_trash` back to `owner_field="owner"` | `test_the_delete_guard_follows_the_owner_and_not_the_creator` **FAILED** (1 failure) |
| `before_insert` default removed | **6 errors**, including `test_a_new_measurable_takes_its_creating_user_as_its_owner` |

Both mutations were reverted and the file re-checked line by line afterwards.

`run-tests --app eos_core` → **248/248 OK** (185 integration + 63 unit).

### PERM-9.5 — Documentation and close-out

**`docs/architecture.md`**

- §2 ER model and the metric bullet: `owner` → `owner_user`, plus a note that `owner` is the
  creator and is not declared.
- §3 scoping rule now reads `owner_user`.
- §3h heading no longer says "except the owner-field gap"; the whole "known gap" subsection is
  replaced by "Measurable ownership: `owner_user`, not `owner`" — a two-column table of the two
  owners, the `DEFAULT_COLUMNS` reason the column survives, what the patch does, and the three
  payloads that deliberately keep the key `owner`.
- §3h guard 2 lists the field as `owner_user`; guard 4 no longer says "own means created".
- §5 ER model for `Scorecard Report Metric` renamed; §7 phase summary updated.

**`AGENTS.md`** — field list in the state table; a new "Measurable ownership is `owner_user`" note
replacing the known-gap paragraph; the test table re-derived from `grep -c 'def test_'` (96 / 4 /
12 / … = 185 + 63 = 248) because the old totals were 243 and the old table did not sum to its own
total; a new gotcha that `owner` is never a business field; the "what to build next" summary now
says Block B is complete.

**`README.md`** — Phase 2/6 status, the open-work line and the test count.

**`docs/roadmap.md`** — the Phase 6 "still open" paragraph and the `PERM-9` checkbox; suite count.

**`docs/TODO.md`** — `PERM-9` removed from Block B, added to the *Done* table with SHA `e00011d`,
a *Done* prose entry covering the rename / the undroppable column / the payloads that kept the name
/ the backfill / the `TEAM_MEMBER_EDITABLE_FIELDS` decision / the five tests / the two knock-on
effects; the header narrative; the "Next up" section retitled to "Block B is **closed**"; and the
footer pointing at `DATA-3`. Block B now reads 11 done, 0 open.

Stale-reference sweep after the edits:

```bash
grep -rn 'EOS Metric\.owner[^_]' docs/ AGENTS.md README.md eos_core/
```

The six remaining hits all describe the creator column, which is correct. `243` survives in three
places in `TODO.md` as dated history (the re-verification pass and the two suite results recorded
under `PERM-12`); those are records of what was true at the time, not live counts.

`bench migrate` and the full suite were re-run after the documentation edits → **248/248 OK**.

## Decisions

See *Decisions taken before implementing* above.

## Discovered Issues

- `Scorecard Report Metric.owner` has the same set-only-once collision as `EOS Metric.owner` did. It
  does not currently misbehave (Frappe's `set_user_and_timestamp` only defaults a child's `owner`
  when it is empty — `frappe/model/document.py:811`), but it is latent and is folded into `PERM-9.1`.
- Frappe requires a patch module to expose `execute()`, not any function name. The first
  `bench migrate` failed on it and was re-run after renaming.

## Verification

- Baseline before any change, 2026-09-29: `bench --site resolv.localhost run-tests --app eos_core`
  → **243/243 OK** (180 integration + 63 unit).
- `PERM-9.1`: `bench --site resolv.localhost migrate` passed; schema and patch assertions in
  *Completed* above.
- `PERM-9.2`: `test_eos_metric` 12/12 OK, `test_permissions` 92/92 OK.
- `PERM-9.3`: `test_permissions` 92/92 OK, full suite 243/243 OK.
- `PERM-9.4`: `test_permissions` 96/96 OK, full suite **248/248 OK** (185 integration + 63 unit).
- `PERM-9.5`: docs updated across `architecture.md`, `AGENTS.md`, `README.md`, `roadmap.md` and
  `TODO.md`; `bench migrate` and the full suite re-run after the doc edits — **248/248 OK** again.
- One infrastructure note, not app code: when a test fails inside `setUp`, its fixture rows are left
  behind and the *next* run fails with `DuplicateEntryError` on `PT Org`. That is a symptom, not a
  second defect — fix the original error first. The `PT %` rows were swept before re-running.

## Completion

**Implementation SHA `e00011d`** — "Give EOS Metric a real, reassignable owner (PERM-9)".
`docs/TODO.md` moves `PERM-9` to *Done* with that SHA, and the footer points at `DATA-3` as the next
item to land. Block B (permissions) is now closed at 11/11.

Every clause of the item's **Done when** is satisfied:

| Clause | Evidence |
|---|---|
| A real, reassignable owner field distinct from its creator | `owner_user` declared and free; `owner` retained, set-only-once. Pinned by `test_a_measurable_owner_is_reassignable_and_distinct_from_its_creator`. |
| A `Team Member` can be assigned one | `test_a_team_member_with_a_seat_may_be_assigned_a_measurable`. |
| `validate_owner_team` re-pointed and re-documented | Reads `owner_user`; negative case in `test_a_measurable_may_not_be_assigned_outside_its_team`; `architecture.md` §2 and §3h. |
| `PERM-8`'s ownership guard covers both it and `Rock.owner_user` | `validate_content_owner(self, "owner_user", "Measurable")`; `Rock` already used `owner_user`; `_assert_cannot_own` exercises both. |

The item's own note — that adding a second owner field is a schema decision with downstream effects
on `validate_owner_team`, the report snapshot, the scorecard grid and the 12 `EOS Metric` tests — was
the reason this was its own item, and all four of those are covered by tests that changed with it.

## Remaining Work

None for `PERM-9`. Next in the queue is `DATA-3`.
