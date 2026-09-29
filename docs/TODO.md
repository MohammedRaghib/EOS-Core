# TODO — Eos Core (Ninety.io clone)

**This file is the only live work queue.** `docs/roadmap.md` is the phase *history* and
`docs/architecture.md` is the *model*. Neither is a task list. If work is not in this file, it is
not queued.

Last full audit: **2026-09-28** — every item below was re-verified against the code, the live
`resolv.localhost` database, and a 129-test run. 129/129 green at that date.

**Since that audit**, Block A was closed in full (`BUG-1`..`BUG-5`, `DATA-1`, `DATA-2`) and `PERM-1`
landed, taking the suite to **150 (87 integration + 63 unit)**, all green. `DATA-2` was found while
closing `DATA-1` and is new; its recorded mechanism was wrong and is corrected in *Done*. The 129
figure above is kept as the audit record; the live count is 150.

## Rules for agents working this queue

These exist because the previous setup had three competing lists in three formats, and they drifted.
Follow them exactly.

1. **Reference items by ID** (`BUG-1`, `PERM-3`). Never re-describe an item in prose and never
   create a second copy of an existing item under new wording. If you think something is missing,
   add a new item with a new ID instead of editing an existing one's meaning.
2. **Never delete an item.** When finished, move it to the *Done* section at the bottom with the
   commit SHA. Deleting destroys the record that the work was ever needed.
3. **Never mark an item done without running its verification command** and confirming the result.
   "Should work" is not done.
4. **Two boxes, and they mean different things.** This is the distinction the old docs kept
   collapsing, which is how "code written" got reported as "feature usable":
   - `code+tests` — the logic exists and is covered by a passing test.
   - `reachable` — a real user can get to it in the browser. **Only** the four whitelisted
     endpoints in `eos_core/` are reachable today; everything else is desk-form or console only.
   `DOC-*` and `DEBT-*` items are internal-only by nature, so they carry a status line without
   boxes. Everything else must tick **both** boxes before it counts as finished.
5. **Re-verify before you act.** Each item records a `Verified` date. If it is more than a few
   weeks old, confirm the bug still reproduces before fixing it — several items here were fixed in
   a previous session without the doc being updated, and one (`BUG-3`) turned out to still be open.
6. **Do not re-open settled decisions.** The five locked Ninety-parity decisions are in
   `AGENTS.md` § Ground rules. Do not relitigate them.
7. **Severity is triage, not order.** `S1` = a user sees wrong data or is blocked. `S2` = a
   workflow breaks. `S3` = debt or polish. Work the blocks in order; within a block, S1 first.

## Verification commands

```bash
cd /workspace/development/frappe-bench
bench --site resolv.localhost migrate                      # after ANY *.json edit, incl. permissions
bench --site resolv.localhost run-tests --app eos_core     # full suite, 150 tests
bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.issue.test_issue   # one module
./env/bin/python -c "import sys; sys.path.insert(0,'apps/eos_core'); from eos_core.scorecard_engine import compute_status"  # engine only, no DB
```

**Do not trust the test-count tables in `AGENTS.md` or `roadmap.md`.** Re-derive with
`grep -rc 'def test_'`. Those tables have been wrong before.

---

# Queue

## Next up: `PERM-2` (Block B) — but read `PERM-6` first

Block A is **closed**: all five bugs plus `DATA-1` and `DATA-2` are done. Blocks B (permissions) and
C (UI) are where the actual product is; nothing built so far is usable by anyone but a developer with
a console.

`PERM-2` is still the top item, but its "Done when" is narrower than the matrix it cites, and doing
only the DocPerm part would ship a parity regression. `PERM-6` records that gap. Do not add flat
role grants to the 13 DocTypes before deciding `PERM-6`.

---

## Block A — Correctness (0 open, 7 done)

---

## Block B — Phase 6: Permissions & Roles (6 items, 1 of 6 done)

Every DocType is still `System Manager` only — verified against `DocPerm` in the live DB on
2026-09-28: all 13 standard DocTypes carry exactly one DocPerm row, for `System Manager`, and all 11
child tables carry none. The six roles exist (`PERM-1` done), but **no DocType grants any of them
access yet**, so nothing is gated by them until `PERM-2` lands.

### PERM-2 — S1 · DocPerm blocks per DocType from Ninety's matrix
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Matrix** (from `docs/roadmap.md` § Phase 6):

| Role | Scorecard defaults | Groups (create/rename/reorder/delete) | Team scorecard settings | Data entry | Measurable Manager |
|---|---|---|---|---|---|
| Owner | Company-wide | yes | yes | yes | yes |
| Admin | Company-wide | yes | yes | yes | yes |
| Coach | Company-wide | no | yes | yes | yes |
| Manager | no | yes | yes | yes | no |
| Team Member | no | reorder within a group only | no | yes | no |
| Observer | no | no | no | view only | no |

**Done when** every one of the 13 standard DocTypes carries a DocPerm block, **and**
`bench --site resolv.localhost migrate` has been run — editing a `permissions` array in a `*.json`
requires a migrate or the change is inert.
**Read `PERM-6` first.** Verified 2026-09-28: only the **Data entry** column of the matrix below is a
plain DocPerm grant. The other five need a `permission_query_conditions` layer, so ticking the "Done
when" above on its own would make every team's data visible company-wide to all six roles — the
opposite of Ninety's assigned-teams scoping.

### PERM-3 — S2 · Team Members may reorder measurables they do not own
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Note** this is an explicit Ninety rule and is *not* what a naive "owner-only" DocPerm gives you.
It also interacts with `Measurable Group.order`, where `0` means "unset" rather than "first" because
the column is `int NOT NULL DEFAULT 0`.
**Done when** a user holding only `Team Member` can reorder a measurable owned by someone else inside
its group, is refused outside it, and cannot rename or delete it — with a test per case.

### PERM-4 — S2 · Only Owner / Admin / Coach see the Measurable Manager
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Done when** the Measurable Manager surface is gated to those three roles, verified by a test that
asserts each of the six roles sees or does not see it.

### PERM-5 — S3 · Worksheet column visibility and status-colour toggles
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** per-team settings for which columns are visible and whether status colours show.

### PERM-6 — S1 · Team-scoped row visibility, which no DocPerm can express
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28** · *found 2026-09-28 while
triaging `PERM-2`, not in any prior list*
**Problem** `PERM-2` cites a capability matrix, but a DocPerm row only carries
`read`/`write`/`create`/`delete`/`submit`/… — it cannot scope a role to *some* teams. Verified in the
live DB: `tabHas Role` holds **zero** rows for all six roles across 11 users, and `hooks.py` sets no
`permission_query_conditions` or `has_permission` for this app (only the framework defaults exist).
Of the matrix's six columns, only **Data entry** is a plain DocPerm grant. The rest map elsewhere:

| Matrix column | Actually implemented by |
|---|---|
| Scorecard defaults (company-wide or not) | `PERM-5` |
| Groups: create / rename / reorder / delete | `PERM-3` (the reorder-in-group rule) |
| Team scorecard settings | `PERM-5` |
| Measurable Manager visibility | `PERM-4` |
| Visibility (assigned teams only) | **this item** |
| Data entry | `PERM-2` — the one genuine DocPerm column |

**Why it blocks `PERM-2`** adding the six roles to the 13 DocTypes with no scoping layer grants each
of them company-wide read on every team. Ninety scopes `Manager`, `Team Member` and `Observer` to
*assigned* teams, so that is a parity regression, not a partial implementation.
**Done when** `permission_query_conditions` (or User Permissions) restrict `Manager`, `Team Member`
and `Observer` to their assigned teams on every team-scoped DocType, `Owner`/`Admin`/`Coach` keep
company-wide access, and a test per role per DocType asserts a user sees their own team's rows and
not another's. This requires the role→team assignment to be representable — decide whether that is
`Player.user` + `Player.team` (already modelled, per `architecture.md` §3b) or a Frappe User Permission.

---

## Block C — Phase 7: UI (7 items, 0% done — the largest gap)

`eos_core/public/` contains only `.gitkeep`. `hooks.py` is pure boilerplate: no `doctype_js`, no
`doc_events`. Four whitelisted endpoints exist and nothing in the UI calls them — only two of them
have an item below (`UI-2` for the not-yet-whitelisted `create_issue_from_metric`, `UI-3` for
`get_rollup_view`); the other two are `UI-7`.

### UI-1 — S2 · Scorecard grid (the core Ninety screen)
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** a Worksheet Page plus a whitelisted grid endpoint over `EOS Metric` + `Scorecard Entry`.
Depends on `PERM-2` for column-level visibility, and is the prerequisite for most of the rest of
this block.

### UI-2 — S2 · UI trigger for "Make it an Issue"
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Where** `create_issue_from_metric` works and is tested, but is **not** whitelisted and has no
button. Fix `BUG-1` first, or the button will show wrong numbers.
**Done when** an off-track metric in the grid has a "Make it an Issue" action, the Issue is created
from the browser, and the streak in the description matches `BUG-1`'s corrected behaviour.

### UI-3 — S2 · "View by" dropdown wired to `get_rollup_view`
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Note** the endpoint is built, correct and tested (13 tests in `test_scorecard.py`). Only the UI is
missing. This is the cheapest parity win in the project.
**Done when** a `Week / Month / Quarter / Year` control on the grid renders the rolled-up columns,
and the weekly Goal column is visibly *not* aggregated (that asymmetry is Ninety's, not a bug).

### UI-4 — S3 · Trends view
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** Ninety's read-only, filterable list narrowed to off-track measurables. Only the
`count_consecutive_off_track` helper exists today.

### UI-5 — S3 · Scorecard column toggles
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** Owner / Goal / Average / Total visibility, "show current period", default timeframe, and
the per-team override of company defaults (depends on `PERM-5`).

### UI-6 — S3 · Bulk UX
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** import/export XLSX/CSV, bulk paste, bulk archive / duplicate / share.

### UI-7 — S2 · Buttons for the three built endpoints nothing can reach
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28** · *found 2026-09-28 while
answering "is Phase 5 done?", not in any prior list*
**Where** `rock.mark_complete`, `rock.get_rock_summary` (`rock/rock.py`),
`scorecard_report.send_report` (`scorecard_report/scorecard_report.py`)
**Problem** all three are `@frappe.whitelist()` and covered by tests, but no user can invoke any of
them from the browser — only the console or the API. Verified 2026-09-28: all three DocTypes declare
`"actions": []` in their `*.json`, `hooks.py` sets no `doctype_js`, and `public/js` is an empty
directory (`public/` holds only `.gitkeep`). The only mentions of `get_rock_summary` and `send_report`
anywhere in this queue were incidental (a footnote in `DEBT-11` and the `BUG-2` Done row), which is
how they went unqueued.
This makes one of `roadmap.md` Phase 5's own definition-of-done lines true only of the code path and
not of the product: *"add Rocks with milestones → mark complete cascades To-Dos"*. The cascade works;
there is no button that calls it. `mark_complete` is the headline Rock workflow.
**Scope** the smallest possible UI in the project — one form button per endpoint. No grid, no page,
no new DocType. Independent of `PERM-2`/`UI-1` and safe to land first in this block, because it needs
no role-specific column visibility.
**How** two routes, and the choice matters for reproducibility. A **Client Script** record
(`view: Form`, added from the desk) is the quickest but is *data*, so it would not live in git and a
fresh site would not have the buttons. A `doctype_js` file registered per DocType is app code and
reproduces on migrate. Prefer the second for anything meant to be a product; the first is fine for a
throwaway demo.
**Done when** a user can complete a Rock from its form (milestone gating and the To-Do cascade both
observable), read the Rock's summary from the form, and send a weekly `Scorecard Report` by email.
A test that the button exists in the app's own files is *not* sufficient on its own — record a manual
browser pass too, because an assertion cannot prove a button is clickable.
**Note** `DEBT-11` (`Rock.progress` returning `int` rather than `float`) surfaces in this surface
because `get_rock_summary` serialises that value straight to JSON. Fix it with, or before, this item.

---

## Block D — Ninety parity features with no representation at all (6 items)

### PARITY-1 — S2 · Add Existing Measurable + Duplicate
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** share one Measurable across teams with synced data.

### PARITY-2 — S3 · Auto-seeded default measurables
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** on account creation. Ninety ships 17 (or the 20 financial ones, depending on doc version)
— **verify the count against Ninety's current docs before implementing, do not take 17 or 20 on
trust from the roadmap.**

### PARITY-3 — S2 · Set New Goal + Set Custom Goal
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** a goal from a date forward, and a custom goal for a single period. This is distinct from
the per-period *forecasting* that `roadmap.md` Phase 3 deferred.

### PARITY-4 — S3 · Backfilling
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** create periods that predate a Measurable's creation date.

### PARITY-5 — S3 · Lightning-bolt indicator on formula ("Smart") measurables
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Note** `is_manual` already matches Ninety's Manual Override requirement; only the indicator is
missing.
**Done when** a `is_smart` measurable displays Ninety's lightning-bolt marker, and a manually
overridden entry is distinguishable from a computed one.

### PARITY-6 — S3 · Connectors (Jira, Salesforce, Google Sheets)
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** via Webhook / ServerScript. Do not start before `PERM-2` — connector credentials are a
permission surface.
**Done when** a written design exists naming which Ninety connector behaviour is in scope, and the
first connector works end to end for one provider.

---

## Block E — Doc corrections (1 item open)

`DOC-1` and `DOC-2` are done — see *Done*. Note the ID gap is intentional: IDs are stable and are
never renumbered, so `DOC-3` stays `DOC-3`.

### DOC-3 — S3 · `To Do` has no `title_field`
**Status** `TODO` · **Verified 2026-09-28** · *found 2026-09-28, not in any prior list*
**Where** `eos_core/eos_core/doctype/to_do/to_do.json`
**Problem** `To Do` is autonamed `format:TD-{todo_name}` but declares no `title_field`, unlike every
other autonamed DocType in the app. Decide whether to add `title_field: "todo_name"` or to document
that the `TD-` prefix is the intended display form.
**Done when** the decision is recorded in `docs/architecture.md` §7 and applied to the JSON (with a
`bench migrate` if the JSON changes).

---

## Block F — Code debt (12 items)

### DEBT-1 — S3 · Three dead constants, and a range tuple duplicated across modules
**Status** `TODO` · **Verified 2026-09-28**
**Where** `eos_core/scorecard_engine.py:11-13` and
`eos_core/eos_core/doctype/eos_metric/eos_metric.py:12`
**Problem** `RANGE_OPERATORS` (a public alias of the private `_RANGE_OPERATORS`, which *is* used),
`ALL_OPERATORS` and `MATCHLESS_OPERATORS` have zero references anywhere. Worse, `RANGE_OPERATORS` is
re-declared independently in `eos_metric.py`, so the range tuple exists in two modules and can drift.
**Done when** the three dead names are gone and `eos_metric.py` imports the tuple from the engine.

### DEBT-2 — S3 · `populate_snapshot` computes `trends` twice
**Status** `TODO` · **Verified 2026-09-28**
**Where** `eos_core/eos_core/doctype/scorecard_report/scorecard_report.py:42` and `:172`
**Problem** `build_scorecard_report` returns a `trends` list that is discarded; `_email_context`
recomputes the same value from the child rows. Dead work on every report build.
**Done when** one of the two computations is removed.

### DEBT-3 — S3 · Milestone-progress logic implemented twice
**Status** `TODO` · **Verified 2026-09-28**
**Where** `eos_core/eos_core/doctype/rock/rock.py:28` (`Rock.progress` property) and
`eos_core/eos_core/doctype/quarterly_review/quarterly_review.py:69-78`
**Done when** both read one implementation. Watch the return-type difference: the property returns
int `0` with no milestones, the review path returns float `0.0`.

### DEBT-4 — S3 · `compute_achievement` has no production call site
**Status** `TODO` · **Verified 2026-09-28**
**Problem** 11 unit tests, zero production callers. Wire it into the report or the grid, or delete it
and its tests. Do not leave a tested-but-unreachable feature documented as DONE.
**Done when** either a production caller exists, or the function and its tests are gone and
`docs/architecture.md` §4 no longer lists it.

### DEBT-5 — S3 · `week_overlap_ratio` and `quarter_bounds` have no production call site
**Status** `TODO` · **Verified 2026-09-28**
**Note** `week_overlap_days` (the day form) *is* wired, via `aggregate_entries_for_period`.
`quarter_bounds` is entirely unused; the review path computes quarter bounds inline.
Also: `test_quarter_bounds_rolls_over_year` is **misnamed** — it asserts
`quarter_bounds(2026-01-05)` → Jan 1 – Mar 31, i.e. Q1 of the *same* year, and never crosses a year
boundary. The rollover branch in `_quarter_end` is correct but unreachable from `quarter_bounds`,
which normalises a Nov/Dec anchor to a Q4 start first. So no test covers it.
**Done when** each is either wired or deleted, the test is renamed, and a real rollover case exists.

### DEBT-6 — S3 · Three empty controllers with no tests
**Status** `TODO` · **Verified 2026-09-28**
**Where** `organization/organization.py`, `scorecard_entry/scorecard_entry.py` (`player/player.py` was
resolved by `DATA-1` on 2026-09-28 — it now validates one seat per person per team and has
`test_player.py`, 4 tests)
**Problem** the remaining two are `pass` with no test files.
**Done when** each either has a test file proving it is intentionally passive, or has the validation
it should have. Empty controllers are fine; untested *and* undocumented is not.

### DEBT-7 — S3 · Five DocTypes enforce uniqueness only in Python, with no DB index
**Status** `TODO` · **Verified 2026-09-28**
**Where** `rock.json`, `scorecard.json`, `level_10_meeting.json`, `scorecard_report.json`,
`quarterly_review.json`
**Problem** all five are autonamed from an inherently unique key, but the column carries no
`unique: 1`, so `show index` returns nothing and a duplicate is only caught by an app-level
`frappe.db.exists` check — not race-proof. Verified in the live DB: `tabRock`, `tabScorecard`,
`tabLevel 10 Meeting`, `tabScorecard Report` and `tabQuarterly Review` have only a `creation` index.
By contrast `tabTo Do` (`todo_name`), `tabVTO` (`organization`) and `tabEOS Metric` (`metric_name`)
all have real `Non_unique=0` indexes.
**Done when** the unique fields are flagged and `bench --site resolv.localhost migrate` has been run
and `show index` confirms the index exists.

### DEBT-8 — S3 · `Quarterly Review` rock scoping is under-specified
**Status** `TODO` · **Verified 2026-09-28**
**Where** `eos_core/eos_core/doctype/quarterly_review/quarterly_review.py:55-63`
**Problem** two undocumented behaviours: the team query does not filter `scope`, so
`scope == "Individual"` rocks that happen to carry a `team` are pulled into a team review (arguably
intended, never written down); and a rock with no milestones contributes `progress = 0.0` to
`rock_avg_progress` rather than being excluded, which silently drags the average down.
**Done when** both behaviours are decided and recorded in `docs/architecture.md` §3f.

### DEBT-9 — S3 · Formatting debt
**Status** `TODO` · **Verified 2026-09-28**
**Problem** `eos_core/eos_core/doctype/vto/vto.py` is the only Python file indented with 4 spaces,
violating `.editorconfig` and `pyproject.toml` (`indent-style = "tab"`); `ruff format` would rewrite
it wholesale. **20** `.py` files are missing a final newline.
**Done when** `ruff format` runs clean and `git diff` is reviewed line by line — the vto.py
reindent will show as a whole-file change.

### DEBT-10 — S3 · Three orphan `.pyc` files from deleted scratch scripts
**Status** `TODO` · **Verified 2026-09-28** · *found 2026-09-28*
**Where** `eos_core/__pycache__/_e2e_tmp.*.pyc`, `eos_core/__pycache__/_dev_check.*.pyc`,
`eos_core/eos_core/doctype/measurable_group/__pycache__/test_measurable_group.*.pyc`
**Problem** compiled artefacts whose sources no longer exist. Harmless but confusing, and evidence of
a previous session churning. None was ever committed.
**Done when** deleted.

### DEBT-11 — S3 — `Rock.progress` returns `int` where callers expect `float`
**Status** `TODO` · **Verified 2026-09-28** · *found 2026-09-28*
**Where** `eos_core/eos_core/doctype/rock/rock.py:32`
**Problem** `return 0` when there are no milestones, `round(...)` (a float) otherwise. `get_rock_summary`
serialises it straight to JSON, so the type flips depending on data.
**Done when** it returns `0.0`, with a test for the empty-milestone case.

### DEBT-12 — S3 — `Scorecard` has a useless non-unique index
**Status** `TODO` · **Verified 2026-09-28** · *found 2026-09-28*
**Where** live `tabScorecard`
**Problem** the only index is a non-unique `creation` index, which InnoDB adds anyway. See `DEBT-7`
— the team+timeframe pair that gives the DocType its identity has no index of any kind.
**Done when** handled as part of `DEBT-7`: a real index on the identity columns exists and
`show index` confirms it.

---

## Done

Moved here when finished. Never deleted, never renumbered.

| ID | Item | Closed | SHA |
|---|---|---|---|
| `BUG-1` | Issue streak ignored the anchor week | 2026-09-28 | `08757c4` |
| `BUG-2` | `send_report` opened the template without an encoding | 2026-09-28 | `ce168c8` |
| `BUG-3` | V/TO with one section populated left four empty | 2026-09-28 | `138eaf9` |
| `BUG-4` | Dangling `parent_team` raised `TypeError` | 2026-09-28 | `8b5ea3e` |
| `BUG-5` | Dangling `EOS Metric.group` raised `DoesNotExistError` | 2026-09-28 | `a5f5321` |
| `DATA-1` | `Player.user` uniqueness / team-ownership rule undecided | 2026-09-28 | `aedbbc1` |
| `PERM-1` | The six Ninety Frappe roles did not exist | 2026-09-28 | `fbb8b5d` |
| `DATA-2` | Editing a `Scorecard.timeframe` orphaned its name and blocked metric creation | 2026-09-28 | `2983668` |
| `DOC-1` | `architecture.md` wrongly said `Measurable Group` has no `title_field` | 2026-09-28 | `f6f3e73` |
| `DOC-2` | `architecture.md` §4 engine table omitted `validate_formula_syntax` | 2026-09-28 | `f6f3e73` |

**`DATA-2`** — **the mechanism recorded in the item was wrong; corrected here and in the commit.**
The item claimed `ensure_scorecard` stops matching, because it looks the scorecard up by
`{team, timeframe}`. It does **not**: that lookup is on *fields*, which update correctly. Confirmed
live before touching anything — after editing `BPO-Weekly.timeframe` to `Annual`,
`get_value("Scorecard", {"team": "BPO", "timeframe": "Annual"})` still returned `BPO-Weekly`.
The real failure is a **name collision**. `Scorecard` is autonamed `format:{team}-{timeframe}` and
Frappe never re-runs autoname on update — `set_new_name` is called only from `insert()`
(`frappe/model/document.py:479`), and `_sync_autoname_field` (`base_document.py:1247`) syncs only
`field:` autonames — so the row keeps its old name. A metric of a *different* frequency then finds no
`{team, timeframe}` match, inserts a new `Scorecard`, autoname computes the **already-taken** name,
and the old `validate_unique` threw a message asserting something false. Reproduced pre-fix:

```
edit BPO-Weekly.timeframe -> Annual ; save
create a Weekly BPO metric
ValidationError: A Scorecard already exists for team BPO and Weekly timeframe.
```

No Weekly scorecard existed. The user was blocked from creating a valid metric, and the error named a
Scorecard that was not there.

**Branch (a) immutable** was chosen over the rename branch, on Ninety's evidence:
`architecture.md` §2 already records that a metric's timeframe cannot be converted later, and Ninety
keeps one Scorecard per team × timeframe. `Scorecard.validate_immutable_identity` now refuses any
change to `team` or `timeframe` on an existing doc, so the name can no longer go stale. Renaming was
rejected: it would have to rewrite links on both `EOS Metric.scorecard` and
`Measurable Group.scorecard`, and `DEBT-7`'s missing unique index on team+timeframe would leave a
rename racy. `validate_unique` is consequently insert-only — its update branch became unreachable and
was deleted rather than left as a misleading guard.
`ensure_scorecard` cannot be defeated by the mismatch because the mismatch can no longer be created.
The residual legacy case — a row whose name predates this fix — is **deliberately still blocked**,
since such a row cannot be repaired by editing it, but it now says what is actually true: `Scorecard
BPO-Weekly already exists with timeframe Annual. Open that Scorecard instead of creating a new one.`
(was: a false claim that a Weekly scorecard existed). A silent workaround was rejected because it
would create a second scorecard with a misleading name.

6 tests added to `test_scorecard.py` (13 → 19), written **before** the code change and confirmed
failing against it: one per immutability field, one proving `description`/`archived` stay editable
(the guard is not over-broad), one proving `ensure_scorecard` resolves all four timeframes after a
refused change, and two for the legacy-row message from both the insert and the metric-creation path.
No `bench migrate` was needed — controller-only, no `*.json` changed. Suite: 150/150 (87
integration + 63 unit). History: this was live in the demo data when `DATA-1` was closed (the only
`Scorecard` was `BPO-Weekly` with `timeframe = Annual`); that repaired the one existing row, but the
mechanism that produced it stayed live until now.

**`PERM-1`** — the six roles are created by `eos_core.roles.ensure_roles`, wired to `after_migrate` in
`hooks.py`, rather than as one-off console data. The item's note said no `bench migrate` was needed
for the role records; that is true for the records themselves but would have left a **new site with
no roles at all**, since `AGENTS.md` warns new sites need `install-app` + `migrate`. Verified
reproducible rather than assumed: deleted `Observer`, re-ran `bench migrate`, and it came back.
Idempotency has its own test (second call creates nothing), plus tests that all six exist, that each
is `is_custom`/`desk_access`/enabled, and that the list still matches Ninety's vocabulary.

`tabRole` has no collision with the six names, which was worth checking first because `Owner`,
`Admin` and `Manager` are generic — `Administrator` and several `* Manager` roles already exist, but
not bare `Manager`. The names are kept verbatim for parity anyway, and the collision risk is noted in
`architecture.md` §3h.

**No behaviour changed.** No DocType references these roles until `PERM-2`, so this is setup, not a
permission. Suite: 144/144 (81 integration + 63 unit).

**`DATA-1`** — **the item's premise was wrong; decided against it on Ninety's evidence.** The item
asked for a uniqueness rule on `Player.user` because multi-team users made ownership "ambiguous".
Ninety's own docs say the opposite: *"Many Ninety users are members of multiple teams"*, users are
invited via a **Team(s)** dropdown, and ownership is disambiguated by Seat. A unique index on `user`
would therefore have **broken** parity. Decision: `Player.user` stays non-unique, and the rule is
written up in `docs/architecture.md` §3b — ownership is always the pair `(user, team)`, which is what
`validate_owner_team` already queries, and every other consumer resolves a `Player` by its own name
via `Team.leader`, so no lookup was ever ambiguous.

What *is* enforced is one seat per person **per team** (`Player.validate_unique_seat_in_team`), which
closes the real hole: a team could otherwise hold two `Player` rows for one login. This gives the
previously-empty controller a purpose and a first test file (`test_player.py`, 4 tests). Two
deviations are recorded rather than hidden: a team-less `Player` is allowed but owns nothing
team-scoped, and Ninety's genuine multi-Seat-per-user case is narrowed to one seat per team.

The demo-data blocker was real and is fixed: the only `Player` (`Hussein`, user `Administrator`,
leader of `BPO`) had `team: null`, so no team-scoped `BPO` metric could be created. Now `team = BPO`,
and a live `bench` console run created and removed a `BPO` metric that linked to `BPO-Weekly` plus an
Issue — the first end-to-end exercise of this data in the project's history. That run is what
surfaced `DATA-2`. Suite: 140/140.

**`BUG-5`** — **reachability corrected on re-verification.** The item said a deleted group raises a
raw `DoesNotExistError`, but that is only true if Frappe's own link validation is bypassed:
`_validate_links()` runs *before* `validate()` on both insert (`document.py:477`) and save
(`document.py:591`), so on the normal path a deleted group is already rejected with
`frappe.LinkValidationError` ("Could not find Measurable Group: <hash>"). Confirmed with a test.
With `flags.ignore_links = True` the real bug appears — `DoesNotExistError('Measurable Group
voafakpmnt not found')` — and that is now a clean `frappe.ValidationError` naming the field. Both
paths have a test, so a future change to Frappe's link ordering is noticed rather than silently
absorbing this. `validate_group` had **no test at all** before this, so this adds two, plus a
guard on the unguarded `Scorecard` lookup in the same method. Suite: 136/136.

**`BUG-4`** — the walk-up now uses `as_dict=True` and throws a `frappe.ValidationError` naming the
missing team. Note the reachable path is a dangling **grandparent**, not a dangling `parent_team`:
Frappe runs `_validate_links()` *before* `validate()` on insert, so a child pointing at a
non-existent parent is already rejected by the framework. The bug only fires when a grandparent is
deleted after the child was saved, so the test inserts a three-level chain, deletes the top team,
then saves the child. Confirmed it raised `TypeError: cannot unpack non-iterable NoneType object`
before the fix. Suite: 134/134.

**`BUG-3`** — **deviated from the item's suggested `or`**, deliberately. Switching `and` to `or`
would make the guard pass, but `populate_sections` appends *all five* sections unconditionally, so a
caller who supplied `core_focus` would get a second, empty `core_focus` row — trading four missing
sections for a duplicate one. The "Done when" asks that the V/TO "still has all five", which a
duplicate row does not satisfy. `before_insert` now calls `populate_sections` unconditionally and
`populate_sections` appends only the sections that are currently empty, so a supplied section is
preserved and the rest are filled. Two tests cover it, one per direction (only `core_focus`
supplied, only `marketing_strategy` supplied); both failed on the old guard with `0 != 1`. Note
`vto.py` is still 4-space indented — that reindent stays with `DEBT-9` so this commit is not mixed
with it. Suite: 133/133.

**`BUG-2`** — `open(template_path, encoding="utf-8")`. The test wraps `builtins.open` with a
recording pass-through (so the real file is still read and rendered) and asserts the single
template open carries `encoding="utf-8"`, plus that the em-dash survives into the rendered
message. Confirmed the test fails against the unfixed call (`AssertionError: None != 'utf-8'`)
before restoring the fix. Suite: 131/131.

**`BUG-1`** — first re-verified the bug still reproduces by writing the "Done when" test before
touching the code: an Issue for week `2026-09-14` was stamped `Consecutive Off Track: 2` because the
trailing run bled through `2026-09-21`. Fix is `count_consecutive_from_db(metric_name, as_of=None)`,
which now caps the query with `week_start_date <= as_of`; `create_issue_from_metric` passes the
resolved entry's `week_start_date`. The default week-starts list is
`2026-08-31 (off) / 2026-09-07 (on) / 2026-09-14 (off) / 2026-09-21 (off)`, so the unbounded count is
2 and the correct bounded count for `2026-09-14` is 1 — the test asserts both, so an unbounded
implementation cannot pass it. Note the *no-argument* call path still reports 2 for the latest week,
which is the intended "current streak" behaviour. Suite: 130/130 (67 integration + 63 unit).

**`DOC-1`** — re-verified against `measurable_group.json` and the live `tabDocType` row, then §7
rewritten to state the two DocTypes separately: both are hash-named, but `Measurable Group` sets
`title_field`/`search_fields` to `group_name` so it displays the group name, whereas `VTO` sets
neither and shows bare hashes.

**`DOC-2`** — added the missing `validate_formula_syntax` row to §4 with its real signature and its
reason for existing (it does not evaluate, which is why `{A}/(1-{B})` is not rejected for dividing by
zero). §4 now lists 29 of 29 public functions and agrees with `AGENTS.md`.

Next item to land: `PERM-2`.
