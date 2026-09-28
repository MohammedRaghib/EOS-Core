# TODO — Eos Core (Ninety.io clone)

**This file is the only live work queue.** `docs/roadmap.md` is the phase *history* and
`docs/architecture.md` is the *model*. Neither is a task list. If work is not in this file, it is
not queued.

Last full audit: **2026-09-28** — every item below was re-verified against the code, the live
`resolv.localhost` database, and a 129-test run. 129/129 green at that date.

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
bench --site resolv.localhost run-tests --app eos_core     # full suite, 133 tests
bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.issue.test_issue   # one module
./env/bin/python -c "import sys; sys.path.insert(0,'apps/eos_core'); from eos_core.scorecard_engine import compute_status"  # engine only, no DB
```

**Do not trust the test-count tables in `AGENTS.md` or `roadmap.md`.** Re-derive with
`grep -rc 'def test_'`. Those tables have been wrong before.

---

# Queue

## Next up: `BUG-4` → then Block A in order

Block A is five small, verified bugs. **Two remain open**; `BUG-1` (the only one that put wrong
data in front of a user) is closed. Blocks B (permissions) and C (UI) are where the actual product
is; nothing built so far is usable by anyone but a developer with a console.

---

## Block A — Correctness (3 open, 3 done)

### BUG-4 — S3 · Dangling `parent_team` raises `TypeError`
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Where** `eos_core/eos_core/doctype/team/team.py:22`
**Bug** the `while current:` walk-up unpacks
`frappe.db.get_value("Team", current, ["organization", "parent_team"])` with no `None` guard, so a
dangling link raises `TypeError: cannot unpack non-iterable NoneType` instead of a clean validation
error.
**Done when** the walk-up guards the result and throws a readable validation error.

### BUG-5 — S3 · Dangling `EOS Metric.group` raises `DoesNotExistError`
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28** · *found 2026-09-28, not in any prior list*
**Where** `eos_core/eos_core/doctype/eos_metric/eos_metric.py:83`
**Bug** `validate_group` calls `frappe.get_doc("Measurable Group", self.group)` with no existence
guard. Same bug class as `BUG-4`; raises a raw `DoesNotExistError` rather than a validation message
naming the field.
**Done when** the lookup is guarded and the thrown message names the offending group link.

### DATA-1 — S1 · `Player.user` is not unique, so team ownership is ambiguous
**Status** `TODO` · code+tests ☐ · reachable n/a · **Verified 2026-09-28**
**Where** `eos_core/eos_core/doctype/player/player.json`; consumer at
`eos_core/eos_core/doctype/eos_metric/eos_metric.py:34`
**Problem** one user can hold seats in many teams, which makes
`EOSMetric.validate_owner_team` ambiguous about which team owns the user. A previous list filed this
as a "smaller item"; it is a correctness issue and it also blocks the current demo data — the only
`Player` in the database (`Hussein`, user `Administrator`) has `team: null`, so *no* team-scoped
metric can be created for team `BPO` until a Player is put in that team.
**Done when** the uniqueness rule is decided and enforced in the schema, and the rule for which
team owns a multi-team user is written down in `docs/architecture.md` §3b.

---

## Block B — Phase 6: Permissions & Roles (5 items, 0% done)

Every DocType is `System Manager` only — verified against `DocPerm` in the live DB. All 11 child
tables have no permissions at all. No role below exists yet.

### PERM-1 — S1 · Create the six Frappe roles
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** `Owner`, `Admin`, `Coach`, `Manager`, `Team Member`, `Observer` (Ninety's vocabulary).
**Done when** the six roles exist on the site and are listed in `docs/architecture.md`.
Note: creating a Role is a data change, not a `*.json` edit, so no `bench migrate` is needed for the
role records themselves — but see `PERM-2`.

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

---

## Block C — Phase 7: UI (6 items, 0% done — the largest gap)

`eos_core/public/` contains only `.gitkeep`. `hooks.py` is pure boilerplate: no `doctype_js`, no
`doc_events`. Four whitelisted endpoints exist and nothing in the UI calls them.

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
**Where** `player/player.py`, `organization/organization.py`, `scorecard_entry/scorecard_entry.py`
**Problem** all three are `pass` with no test files. `Player` is the interesting one — see `DATA-1`.
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
| `DOC-1` | `architecture.md` wrongly said `Measurable Group` has no `title_field` | 2026-09-28 | `f6f3e73` |
| `DOC-2` | `architecture.md` §4 engine table omitted `validate_formula_syntax` | 2026-09-28 | `f6f3e73` |

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

Next item to land: `BUG-4`.
