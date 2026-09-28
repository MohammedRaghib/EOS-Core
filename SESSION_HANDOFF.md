# SESSION_HANDOFF.md — Eos Core (Ninety.io clone)

**Purpose of this file:** a new OpenCode session should read this and continue the work with zero
prior context. State of the tree at handoff time is captured exactly. Start with
[§9 Continuation instructions](#9-continuation-instructions).

---

## 1. Project and context

### What this is

`eos_core` is a **from-scratch Frappe v16 re-implementation of Ninety.io** — the software
implementation of the *EOS (Entrepreneurial Operating System)* from *Traction*. The user is building
this as a **Ninety clone**, so **Ninety's documented product behaviour is the specification**. Every
behavioural decision must be grounded in how Ninety actually works, not in what seems reasonable.

The app itself lives at `apps/eos_core` inside a Frappe bench. The user described the project as
"a ninety io app" built across ~3 AI chat sessions, and was unable to tell what worked because the
roadmap over-claimed. This session's work was an audit plus correctness/parity fixes.

### Tech stack

- **Frappe v16** (bench, Python 3.14, MariaDB)
- App: `apps/eos_core`, module name `"Eos Core"`
- DocType JSON layout follows the **v16** convention — `doctype/<scrubbed>/<scrubbed>.json` + `.py`,
  **no `*_doctype` suffix** (matches the `resolv` app in the same bench)
- Frappe version observed in tracebacks: **16.31.0**

### Environment

- Bench root: `/workspace/development/frappe-bench`
- Site to use: **`resolv.localhost`** — has `frappe`, `resolv`, and `eos_core` installed
- `site_config.json` has `allow_tests: true` already
- Site DB: MariaDB at host `mariadb`, db `_79cf0ba7517c815f`, type `mariadb`
- There is also `development.localhost` (frappe only, **do not use**)
- Git branch: **`version-16`**

### Commands (run from bench root)

```bash
bench --site resolv.localhost migrate
bench --site resolv.localhost run-tests --app eos_core     # runs the ENTIRE suite
bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.rock.test_rock
bench --site resolv.localhost execute <app.module.function> --kwargs '{"k":"v"}'
bench --site resolv.localhost console < /tmp/script.py    # handy for read-only DB introspection
bench --site resolv.localhost list-doctypes -a
```

**Note:** `run-tests --app eos_core` now discovers both categories and runs everything at once
(47 integration + 35 unit = 82). The old per-module instruction is obsolete. A per-module
`--module` flag still works and is useful while iterating.

---

## 2. Current implementation

### Architecture in one line

Pure business logic lives in `eos_core/scorecard_engine.py` (frappe-free, unit-testable);
`EOSMetric.validate` is the only place that recomputes child `Scorecard Entry.status`.

### DocTypes (24 registered in DB, all migrated)

Verified 2026-09-28 by parsing every `*.json` and reading its `istable` flag. Note
`istable` is **absent** from the 13 non-child files (it only appears in the 11 child files), so a
`grep '"istable"'` on all 24 returns nothing for the non-child ones — parse the JSON instead.

**Non-child (13):** `EOS Metric`, `Issue`, `Level 10 Meeting`, `Measurable Group`,
`Organization`, `Player`, `Quarterly Review`, `Rock`, `Scorecard`, `Scorecard Report`, `Team`,
`To Do`, `VTO`

**Child, `"istable": 1` (11):** `Meeting Agenda Item`, `Meeting To Do`, `Rock Milestone`,
`Scorecard Entry`, `Scorecard Report Metric`, `To Do Item`, `VTO Core Focus`,
`VTO Marketing Strategy`, `VTO 3 Year Picture`, `VTO 1 Year Plan`, `VTO Quarterly Rocks`

13 + 11 = **24**, matching `bench --site resolv.localhost list-doctypes -a`.

**Naming (verified in live DB via `tabDocType.autoname`):**

| DocType | autoname |
|---|---|
| `EOS Metric` | `field:metric_name` |
| `Issue` | `field:issue_name` |
| `Organization` | `field:organization_name` |
| `Player` | `field:player_name` |
| `Team` | `field:team_name` |
| `Level 10 Meeting` | `format:{team}-{meeting_date}` |
| `Scorecard` | `format:{team}-{timeframe}` |
| `Scorecard Report` | `format:SCR-{team}-{week_start_date}` |
| `Quarterly Review` | `format:QR-{team}-{period_start}` |
| `Rock` | `format:R-{rock_name}` |
| `To Do` | `format:TD-{todo_name}` |
| **`VTO`** | **none → Frappe hash naming** (roadmap used to wrongly claim `format` autoname) |
| `Measurable Group` | none → hash naming |

### `scorecard_engine.py` — 17 public functions

```
aggregate_values, build_quarterly_review, build_scorecard_report, completed_period_statuses,
compute_achievement, compute_status, compute_status_indicator, count_consecutive_off_track,
default_agenda_sections, evaluate_formula, extract_variables, is_period_complete,
prorate_for_period, quarter_bounds, rollup_rock_summary, rollup_todo_summary, scorecard_summary,
validate_formula_syntax
```

Private helpers: `_range_status`, `_eval_ast`, `_range_satisfied`, `_range_achievement`, `_clamp`,
`_quarter_start`, `_quarter_end`, `_last_day_of_month`, `_timedelta_one_day`, `_date`, `_today`,
`_as_date`, `_add_days`.

Module constants: `MAX_FORMULA_VARIABLES = 25`, `VARIABLE_PATTERN`, `_SAFE_EXPRESSION`
(`^[\d\.\+\-\*\/\(\)\%\s]+$`), `_COMPARISON_OPERATORS`, `_RANGE_OPERATORS`
(`("Inside min/max", "Outside min/max")`), `STATUS_WINDOW = 3`, `STATUS_INDICATORS`,
`SCORED_STATUSES`, `WEEK_LENGTH_DAYS = 7`, plus **3 dead constants** — `RANGE_OPERATORS`,
`ALL_OPERATORS`, `MATCHLESS_OPERATORS`.

### Key domain rules

- `compute_status(target, actual, operator, min, max)` → `"On Track"` / `"Off Track"` / `None`.
  Missing target or `target == 0` → `"On Track"`. `==` is exact float equality.
- `EOS Metric` fields: `metric_name`, `owner`, `team`, `target_value`, `operator`
  (`>=`/`<=`/`==`/`Inside min/max`/`Outside min/max`), `min_value`, `max_value`, `frequency`
  (Weekly/Monthly/Quarterly/Annual), `unit`, `unit_type` (Number/Currency/Percentage/Yes/No/Time),
  `rollup` (Total/Average), `is_smart`, `formula`, `scorecard`, `group`, `archived`, `description`,
  `entries` (Table → `Scorecard Entry`).
- `Scorecard Entry` fields: `metric`, `week_start_date`, `actual_value`, `status`,
  **`is_manual`** (Check, label "Manual Override"). The roadmap used to call this `manual_override`
  — that name is wrong and has been corrected in the docs. Do **not** rename the field.
- `Rock`: `rock_name`, `status`, `owner_user`, `scope` (Company/Team/Individual), `team`,
  `duration_start`, `duration_end`, `head_down_hours_per_week`, `milestones` (Table), `notes`,
  `amended_from`. **There is no single `duration` field** — the roadmap previously claimed one.
- `To Do`: `todo_name` (**now `unique: 1`**), `status` (Not Started/In Progress/**Complete**/**Dropped**
  — 4 options, roadmap previously said 3), `owner_user`, `team`, `rock`, `due_date`, `priority`,
  `items` (Table), `notes`.
- `Quarterly Review`: `team` × `period_start` (unique), `period_end`, and count/summary fields
  `rock_total`, `rock_active`, `rock_complete`, `rock_avg_progress`, `todo_total`, `todo_open`,
  `todo_complete`, `todo_overdue`, `measurable_total`, `measurable_on_track`, `measurable_off_track`.
  **Measurable counts are On Track / Off Track, not "green/red".**
- L10 default agenda (6, in order, from `default_agenda_sections()`):
  `Segue`, `Scorecard Review`, `Good News`, `To-Dos`, `IDS`, `123s of the Week`
- `Issue` status: `Identified` → `Discussing` → `Solved`/`Dropped`, forward-only;
  `solution` required on Solve. `source` is Manual/Scorecard but has **no default**.
- Email template for the weekly report: `eos_core/templates/emails/weekly_scorecard_report.html`
  (the only real template in the app; verified present at the resolved path and renders).

### Whitelisted (UI-callable) methods — only 3 exist

- `rock.py` `mark_complete()`
- `rock.py` `get_rock_summary(as_of=None)`
- `scorecard_report.py` `send_report()`

`create_issue_from_metric` in `issue.py` is **not** whitelisted and has no UI trigger.

---

## 3. Requirements and decisions

### User's explicit instructions

- The user asked whether the app was complete, then explicitly requested: **"ok ya you can start
  with block 0"** — authorisation to begin executing the plan.
- The user set priorities by answering three questions directly.

### Decisions the user made (all three settled — do not re-ask)

1. **UI last.** "ui after permissions, ui is the least priority." So the build order is
   **Block 1 → Block 2 → Block 3 (permissions) → Block 4 (UI)**.
   (Recommendation that was declined: minimal perms → grid → full Phase 6.)
2. **Delete `compute_health`.** "deleting would be the correct choice." Rationale: it produces a
   10%-tolerance colour **Ninety never shows**, and it is never called, so it is a misleading
   second colour system. Delete `compute_health`, `_range_health`, `_health_by_gap`,
   `SmartMetricStatus`, and the unit tests that cover them.
3. **`To Do.todo_name` → `unique: 1` in JSON** (real DB constraint, `bench migrate`), chosen over a
   softer Python check in `validate` — for consistency with `VTO.organization` which already uses a
   `unique` index. **Already done and migrated.**

### Approaches rejected during this session (do not re-tread)

- **Rejected: wiring `compute_health` as the status colour.** Ninety derives the status indicator
  from the **3 most recently *completed* reporting intervals**, not a tolerance band on one value.
  Wiring it would produce visibly different colours from Ninety (e.g. Red where Ninety shows
  Yellow). Must be a **rewrite**, not a wiring.
- **Rejected: deferring `prorate_for_period` as speculative.** Ninety genuinely prorates, so it is
  required for rollup parity. It is being wired together with `rollup`.
- **Rejected: using the roadmap as the spec.** It over-claimed in 9 places. `docs/architecture.md`
  was more accurate than `roadmap.md` in at least one place (VTO naming).

### Ninety behaviour verified via web search (authoritative, keep for Block 2)

**Status colours (Ninety's real rule):**
- **Green** = met or exceeded goal for **all 3** most recently **completed** intervals
- **Yellow/Orange** = missed goal for **at least one** of the 3
- **Red** = missed goal for **all 3**
- **"No Recent Data"** = no scores entered in any of the 3 — **a 4th state this app does not model**
- The **current in-progress period is never included**, even if shown as a column
- A single on-track entry does not turn a red indicator green; it needs 3 consecutive completed
  periods
- Older ninety.io blog phrasing agrees: "yellow = below goal once in three consecutive weeks,
  red = three weeks in a row"

**Rollup / "View by":**
- Ninety has a **"View by"** dropdown: Week (default) / Month / Quarter / Year. Month, Quarter,
  Year are **read-only** aggregates of the weekly data.
- Weeks spanning multiple periods are **prorated by calendar days, not by whole weeks**. Ninety's
  own example: a week running Oct 27 – Nov 2 contributes **5/7 to October and 2/7 to November**.
  (This corrects an earlier note in this file that said "prorated at the weekly level, not daily" —
  that was wrong. Source: help.ninety.io "Navigating the Data Tool" / "Navigating the Scorecard
  Tool", both updated 2026-07/2026-08.)
- Each Measurable has **"Show rollup data as"** = Average | Total, **default Total**, in the Target
  section of its details panel. Percentage-target measurables should be set to Average.
- The View by filter does **not** convert weekly measurables into monthly/quarterly ones; the four
  scorecards (Weekly/Monthly/Quarterly/Annual) remain separate.
- Ninety **never** compares a single period to a cumulative/YTD total; "the Total and Average
  columns do not affect a period's on-track status." (`architecture.md` already states this.)

**Groups:**
- Up to **20** groups per scorecard (already implemented).
- **Group order carries into the L10 meeting agenda** — verbatim: *"The order you set here carries
  over to your team's L10 meeting agenda... the groups appear in the same order you've set on the
  Scorecard."* This confirms the roadmap's claim was accurate and only the code was missing.
- Team Members can reorder measurables within a group, **even measurables they do not own**.
  (A Phase 6 permission rule.)

**Other Ninety features still missing (for later blocks):**
- Add Existing Measurable (share one Measurable across teams, synced data) and Duplicate
- Auto-seeded default measurables on account creation (17, or 20 financial in one doc version)
- "Set New Goal" from a date forward; "Set Custom Goal" for a single period (distinct from forecasting)
- Trends view (read-only, filterable, narrow to off-track)
- Scorecard column toggles: Owner / Goal / Average / Total visibility, "Show current period",
  default timeframe, per-team override of company defaults
- Bulk actions: Move to group, Duplicate, Create To-Dos, Create an Issue, Remove from group, paste
  from spreadsheet
- Formula measurables show a **lightning bolt** and need Manual Override on (app already has
  `is_manual` — parity there)
- Backfilling periods that predate the Measurable's creation

### Phase 6 role model (from Ninety's help centre, needed for Block 3)

- **Owner / Admin / Coach** — company-wide scorecard defaults
- **Owner / Admin / Manager** — create, rename, reorder, delete groups; customise team scorecard
  settings (Ninety also says "Owners, Admins, Implementers, and Managers" for scorecard settings)
- **Team Member** — enter data; reorder measurables within a group even if not owned; create To-Dos
- **Observer** — view only (can expand/collapse groups)
- Currently the app is **System Manager only** for every DocType.

---

## 4. Current state

### Tests: 82, all green

```
Running 47 integration tests for eos_core    → OK
Running 35 unspecified-category tests ...    → OK
```

| File | Count |
|---|---|
| `eos_core/test_scorecard_engine.py` (unit) | 35 |
| `doctype/eos_metric/test_eos_metric.py` | 10 |
| `doctype/quarterly_review/test_quarterly_review.py` | 5 |
| `doctype/rock/test_rock.py` | 5 |
| `doctype/to_do/test_to_do.py` | 5 |
| `doctype/issue/test_issue.py` | 4 |
| `doctype/scorecard_report/test_scorecard_report.py` | 8 |
| `doctype/level_10_meeting/test_level_10_meeting.py` | 3 |
| `doctype/team/test_team.py` | 3 |
| `doctype/scorecard/test_scorecard.py` | 2 |
| `doctype/vto/test_vto.py` | 2 |
| **Integration total** | **47** |

**Total = 82, all green** (was 69 before Block 2a: +11 engine tests, +4 integration; −2 deleted
health tests).

### Git state — CLEAN, all work committed

Branch `version-16`, HEAD = **`c9fedd2`** *"feat(scorecard): add Ninety status indicator, drop
compute_health"* — this commit contains Block 2a (11 files, +858/−102). Prior tip was `20cb839`
*"docs: correct test counts and add prioritized gap backlog"*, before that `327504e` (Phase 5).

**Block 2a is implemented, tested and COMMITTED as `c9fedd2`.** It was audited after the fact: the
full suite passes (82/82), all 24 DocTypes show zero schema drift against the live DB, and no
code references the deleted `compute_health`/`_range_health`/`_health_by_gap`/`SmartMetricStatus`
symbols. The only defects found in that commit were cosmetic and have since been fixed: a
3-space indentation slip in `scorecard_report_metric.json`'s `field_order`, and `STATUS_INDICATORS`
being defined but unused (now guarded by a test asserting the engine constant matches the
DocType Select options).

**Nothing further should be committed unless the user asks** (project rule).

### Work completed in this session

**Block 0 — unblock + docs**
- `rock.py` `get_rock_summary(as_of=None)` now threads `as_of` into `rollup_todo_summary`, so
  `test_rock.py` no longer depends on the wall clock. Added a second assertion with
  `as_of="2026-11-01"` → `overdue == 1`, which proves `as_of` is actually honoured.
  (Was a time bomb: To-Dos due `2026-10-15`, `overdue == 0` asserted, `as_of` defaulted to
  `date.today()` → would have failed from 2026-10-15.)
- Corrected 9 false claims across `docs/roadmap.md`, `AGENTS.md`, `README.md`,
  `docs/architecture.md`, and added a **"Known gaps in Phases 1–5"** section to the roadmap.

**Block 1 — five correctness bugs, all fixed with tests**
| # | Fix | Location |
|---|---|---|
| 1.1 | Dedupe Rocks matching both queries by name | `quarterly_review.py:64-68` |
| 1.2 | Report entries filtered to `week_start_date <= report.week_start_date` (also fixed trends being measured into the future) | `scorecard_report.py:75-92` |
| 1.3 | New `validate_formula_syntax()` — parse/safety only, no numeric evaluation | `scorecard_engine.py`, `eos_metric.py:122` |
| 1.4 | Incomplete upstream data leaves the entry untouched instead of setting it to `None` | `eos_metric.py:143-151` |
| 1.5 | `<=` with `actual_value=0` returns `100.0`/`0.0` by target sign instead of `ZeroDivisionError` | `scorecard_engine.py:45-48` |

**Two bonus bugs found while testing:**
- **`validate_range_target` was broken for the most common operation.** `min_value`/`max_value` are
  Frappe `Float` columns → `decimal(21,9) NOT NULL DEFAULT 0.000000000`, so they return as `0.0`
  after any reload. Since `0 is not None`, **re-saving any non-range metric threw**
  `ValidationError: Min Value and Max Value apply only to range operators.` No test had ever
  re-saved a metric after a reload, so this survived all five phases. Fixed by normalising
  `0 → None` at the top of `validate_range_target` (`eos_metric.py:46-50`).
- **`evaluate_formula`'s 25-variable guard counted `len(variables)` (the supplied dict) instead of
  the number of variables in the formula.** Fixed to `len(extract_variables(formula))`.

**Decision 3 applied:** `To Do.todo_name` got `unique: 1`; verified live index via
`show index from \`tabTo Do\`` → `('todo_name', 'todo_name', Non_unique=0)`. Table had 0 rows, so
the migration was safe. Test asserts `frappe.DuplicateEntryError`.

### Known failures / flakiness to be aware of

- `MySQLdb.OperationalError: (1020, "Record has changed since last read in table 'tabSingles'")`
  appeared once in `run-tests --module ...test_scorecard_report`. It occurs during
  `_initialize_test_environment` / `disable_scheduler`, **not** in app code. It did not reproduce on
  re-run. Treat as infrastructure flakiness; re-run before investigating.

### 4 still-open bugs (documented in `docs/roadmap.md`)

| Location | Bug |
|---|---|
| `issue.py` `count_consecutive_from_db` | Ignores its `week_start_date` arg; streak computed over the metric's full history |
| `scorecard_report.py` `send_report` | `open(template_path)` with no `encoding=` but the template contains em-dashes (`E2 80 94`) |
| `vto.py` `populate_sections` | Guarded by `if not core_focus and not marketing_strategy` — a VTO created with one section populated leaves the other 4 empty |
| `team.py` `validate_parent_team` | `frappe.db.get_value` result unpacked without a `None` guard |

### The biggest unbuilt thing: NO UI

`eos_core/public/js` and `public/css` are **empty**. Zero JS files anywhere in the app. No
`doctype_js`, no `doc_events` in `hooks.py` (only boilerplate: `app_name`, `app_title`,
`app_publisher`, `app_description`, `app_email`, `app_license`). Only 3 whitelisted methods.
Everything is reachable only through the default Frappe form or the console. Per the user's
decision this is **lowest priority** (Block 4).

### Other structural gaps

- `Player`, `Organization`, `Scorecard Entry` controllers are `pass` with no tests.
  `Player.user` has no uniqueness rule, so one user can be in many teams — making
  `EOSMetric.validate_owner_team` ambiguous about which team owns the user.
- Dead code: 7 unused module constants in `scorecard_engine.py`; the year-rollover branch in
  `_quarter_end` is unreachable (so `test_quarter_bounds_rolls_over_year` is misnamed — it tests
  Q1 of the same year).
- Unwired: `compute_achievement`, `aggregate_values`, `prorate_for_period`, `quarter_bounds`,
  `EOS Metric.rollup`, `Measurable Group.order` (0 call sites for the first four; `rollup` and
  `order` stored but never read).
- `vto/vto.py` is the only file using 4-space indent; all others use tabs. Violates
  `.editorconfig` and `pyproject.toml` (`indent-style = "tab"`), so `ruff-format` would rewrite it.
  7 `.py` files lack a final newline (also `.editorconfig` violations).
- DB is essentially empty — 1 Organization, 1 Team, 1 Player, 1 Scorecard (test residue). Nothing
  has been manually exercised end-to-end.

---

## 5. Important technical details

### Schema gotcha — Float columns are NOT NULL

This bit us and will bite again. Frappe `Float` fields map to
`decimal(21,9) NOT NULL DEFAULT 0.000000000`. You **cannot** distinguish "unset" from "explicitly
zero" via the value alone. The codebase convention is that `0` means unset — see
`compute_status`: `if target_value is None or target_value == 0: return "On Track"`.
Consequence: a legitimate range bound of exactly `0` cannot currently be expressed.

### Test data conventions in existing tests

- Weeks are Mondays: e.g. `2026-08-17`, `2026-08-24`, `2026-08-30`, `2026-09-07`, `2026-09-14`.
- `frappe.get_doc({...}).insert()` is the insertion idiom; `frappe.db.delete(...)` in `tearDown`.
- `self.assertRaises(frappe.ValidationError)` / `frappe.DuplicateEntryError` for rejections.
- Test classes extend `frappe.tests.IntegrationTestCase`.
- `mock.patch.object(frappe, "sendmail")` is used in `test_send_report.py`.
- Current in-session "today" during this work was **2026-09-28**; always pass explicit `as_of` or
  explicit dates in tests to stay date-independent.

### Read-only DB introspection pattern

`bench --site resolv.localhost console` reading a script from stdin works well and avoids the
`bench execute` app-path resolution problem (`bench execute /tmp/x.py` fails — it tries to resolve
`/tmp` as an app module and raises `AppNotInstalledError`). Example:

```bash
cat > /tmp/opencode/q.py <<'EOF'
r = frappe.db.sql("show index from `tabTo Do` where Key_name != 'PRIMARY'")
print("IDX:", [(x[2], x[4], x[1]) for x in r])
EOF
bench --site resolv.localhost console < /tmp/opencode/q.py 2>&1 | grep IDX
```

### Pure-engine testing without frappe

```bash
cd /workspace/development/frappe-bench && ./env/bin/python -c "
import sys; sys.path.insert(0,'apps/eos_core')
from eos_core.scorecard_engine import compute_status
print(compute_status(100, 0, '<='))"
```

---

## 6. User preferences and constraints

### Hard project rules (from `AGENTS.md` — do not violate)

1. **Never write code comments or docstrings** in any `.py` or `.js` file you create or modify.
   State intent in `docs/*.md` and via clear naming. This is a hard constraint from the product
   owner.
2. **Do not rename** the DocTypes `EOS Metric`, `Scorecard Entry`, or the `entries` Table field.
   Terminology mapping to Ninety lives in `docs/architecture.md`.
3. **After editing any `*.json` schema, run `bench migrate`** and verify the DocType synced.
4. **Don't commit unless explicitly asked.** (The user has been committing; still confirm first.)
5. Keep pure logic in `scorecard_engine.py` (no frappe imports); controllers stay thin glue.
6. Child DocTypes: `"istable": 1` with empty `permissions`.

### Working preferences observed

- The user is a developer, not a domain expert in EOS — they care about **what actually works**,
  and were frustrated by a roadmap that hid the difference between "code written" and "feature
  usable". When reporting, **be explicit about that distinction** and never let documentation
  overstate completion.
- The user responded well to a plain, direct answer with a verdict, not hedging.
- Keep responses concise; use tables for comparison and prioritisation.
- The user values **verified** claims. Prefer running code / querying the DB / fetching real docs
  over asserting from memory.

---

## 7. Outstanding work

### Block 2 — Ninety parity (NEXT; the current task)

**2a — DONE (committed as `c9fedd2`).** Ninety's real status indicator is implemented and wired.
- Deleted `compute_health`, `_range_health`, `_health_by_gap`, `SmartMetricStatus` and their 2 tests.
- Added `compute_status_indicator(statuses, window=3)`, `is_period_complete(period_start, today)`
  and `completed_period_statuses(entries, today)`, plus constants `STATUS_WINDOW = 3`,
  `STATUS_INDICATORS`, `SCORED_STATUSES`, `WEEK_LENGTH_DAYS = 7`.
- `build_scorecard_report` now emits `status_indicator` per metric from a new `completed_statuses`
  block key.
- Wired to `Scorecard Report Metric.status_indicator` (new read-only Select:
  `Green`/`Yellow`/`Red`/`No Recent Data`; JSON edited, `bench migrate` run, column verified) and
  rendered in the weekly report email.
- **Design decision:** the report excludes its *own* week as the in-progress period by calling
  `completed_period_statuses(entries, today=self.week_start_date)`. This is date-relative, not
  wall-clock-relative, so historical reports stay correct. It also avoids a
  `TypeError: '<' not supported between 'datetime.date' and 'str'` that occurs because
  `self.week_start_date` is still a `str` during `before_insert`.
- **Documented assumption:** with fewer than 3 completed periods, "all periods present" is used —
  so a single missed period is `Red`, not `Yellow`. Ninety's wording ("missed all 3 of the most
  recently completed") is generalised this way. Revisit if the user prefers `Yellow` for partial
  history.

**2b — Proration + rollup = one feature (Ninety's "View by")**
- Fix `prorate_for_period` to clamp the ratio to 0–1 and reject negative input; it currently returns
  negatives (`prorate_for_period(100, -3, 7)` → `-42.857`). Doc signature in `architecture.md:387`
  is also wrong.
- Add `week_overlap_ratio(week_start, period_start, period_end)` → 0–1, computed as the number of
  calendar days the 7-day week shares with the period, divided by 7 — this is Ninety's day-level
  split (Oct 27–Nov 2 → 5/7 for October, 2/7 for November).
- Add `aggregate_entries_for_period(entries, period_start, period_end, rollup)` → prorate each
  weekly entry into the period, then `aggregate_values` per `rollup`. Entries with no
  `actual_value` are skipped; no contributing entries → `None`.
- **Boundary:** this is a **display-only** aggregate. It must not change `status`,
  `status_indicator`, `on_track`/`off_track` counts, or the trend count. Ninety: "the Total and
  Average columns do not affect a period's on-track status", and in a rolled-up view the Goal and
  Average columns deliberately keep showing the single-period (weekly) value.
- Correct `architecture.md:387` to the real signature `(value, elapsed, total)`.

**2c — Group order → L10 (roadmap claim was correct, code never read `order`)**
- Sort the report snapshot by `Measurable Group.order`, ungrouped last.
- Make the L10 "Scorecard Review" section list measurables in group order.

Each sub-block ships with tests; re-run the full suite after each.

### Block 3 — Permissions (Phase 6, currently zero)
Create the 6 Frappe roles and per-DocType DocPerm blocks using the matrix in §3. Note the Ninety
rule that Team Members may reorder measurables within a group even if they do not own them.

### Block 4 — UI (lowest priority, per the user)
Realistic path: a `Scorecard Worksheet` Page plus a whitelisted grid endpoint. Also expose
`create_issue_from_metric` as a button. This is the largest parity gap.

### Smaller backlog
- Fix the 4 open bugs in §4.
- `Player.user` uniqueness rule; empty-controller tests.
- Delete the 7 dead engine constants; fix `_quarter_end` / rename the misnamed test.
- Tabs/EOF formatting for `vto/vto.py` and the 7 files missing a final newline.
- Fix the 4 roadmap test-count references per module if they drift again.

### Pending decisions
**None.** All three were answered. Block 2's sub-shape (what new fields/endpoints to add) may
warrant a quick confirmation, but no decision is currently blocking.

---

## 8. Conversation-specific context

- The user's opening belief was "phase 4 is done and dusted", then "phase 5 is done and dusted"
  while the roadmap actually claimed **Phases 1–5 all DONE**. The audit's finding was that
  "DONE" in this project has meant **"the code exists and is unit-tested"**, never
  **"a user can use it"**. That distinction is now written into `AGENTS.md`, `README.md` and
  `roadmap.md`. Preserve it in any future doc edits.
- A large audit preceded the fixes and found **zero** stubs, TODOs, FIXME, NotImplementedError or
  undefined references. The code is genuinely clean; the problem was over-claiming, not sloppiness.
- The most quotable finding: the roadmap said `VTO` has a `format` autoname; it has **no
  autoname at all** (hash naming), in both the JSON and the live `tabDocType` row.
- `Scorecard Report` uniqueness and `Quarterly Review` uniqueness are **app-level Python checks
  only** — there is no DB unique index, so they are not race-proof.
- `Measurable Group` has no autoname → hash naming; it has no `title_field`.
- The Jinja email template was specifically checked because a missing template would make
  `send_report` fail at runtime. It exists at
  `apps/eos_core/eos_core/templates/emails/weekly_scorecard_report.html` and was verified to render
  with the exact context `_email_context()` supplies.
- `_email_context()` supplies `report`, `summary`, `trends`, `rows`; `rows` entries have
  `name/group/owner/actual/target/status/trend`. If 2a adds a status indicator, the template needs a
  matching update or the colour won't appear in the email.
- `Scorecard Report._email_context()` does `row.trend >= TREND_THRESHOLD`, which would raise
  `TypeError` if a hand-added child row had `trend = None`. Populated rows always get an int.
- `build_scorecard_report`'s `trends` result is computed at `scorecard_report.py:33` and then
  **discarded**; trends are recomputed from child rows at `~:132-136`. Worth cleaning up.
- `_range_health` was asymmetric for one-sided ranges: `Outside min/max` with only `min_value` set
  could never return `Yellow` (fell through to `"Red"`). This goes away when `compute_health` is
  deleted per decision #2.
- `quarterly_review.py:65` also pulls `scope == "Individual"` rocks that happen to carry a `team`
  into a team review. Arguably intended, undocumented. Separately, rocks with **no** milestones
  contribute `progress = 0.0` to `rock_avg_progress` rather than being excluded.
- `rock.py` duplicates milestone-progress logic that `quarterly_review.py:71-75` also implements.
- I offered wire-vs-delete recommendations for four dead features, then **checked Ninety's real
  behaviour and had to correct two of my own four recommendations** (`compute_health` must be
  rewritten, not wired; `prorate_for_period` must be wired, not deferred). The user's question
  "will these cause a difference in Ninety?" was what prompted that check — it is the right instinct
  to keep applying.

---

## 9. Continuation instructions

### Verify state first (fast)

```bash
cd /workspace/development/frappe-bench
git -C apps/eos_core log --oneline -3        # expect c9fedd2 at HEAD
git -C apps/eos_core status --short          # expect empty
bench --site resolv.localhost run-tests --app eos_core   # expect 47 + 35 = 82, both OK
```

If the test count differs from 82, re-read `apps/eos_core/SESSION_HANDOFF.md` §4 and the test
files before assuming anything.

### Then read, in this order

1. `apps/eos_core/SESSION_HANDOFF.md` (this file)
2. `apps/eos_core/AGENTS.md` — conventions and the prioritised work queue
3. `apps/eos_core/docs/roadmap.md` — especially **"Known gaps in Phases 1–5"** (split into
   *fixed* / *still open*) and the Phase 6/7 sections
4. `apps/eos_core/docs/architecture.md` §2 terminology table and §4 engine table — these were
   corrected and are now accurate
5. `apps/eos_core/eos_core/scorecard_engine.py` — 399+ lines, frappe-free, the right home for all
   new pure logic

### Immediate task

**Block 2a is done and committed** (`c9fedd2`); the tree was audited clean afterwards — 82/82
tests green, 0 schema drift across all 24 DocTypes, no dangling references to the deleted
`compute_health` family. **Start Block 2b** — proration + rollup, i.e. Ninety's "View by":

1. Fix `prorate_for_period(value, elapsed, total)`: clamp the ratio to 0–1 and reject negative
   `elapsed` (it currently returns negatives, e.g. `prorate_for_period(100, -3, 7)` → `-42.857`).
   Add unit tests for the clamp and the negative case.
2. Add `week_overlap_ratio(week_start, period_start, period_end)` → 0–1, computed from the
   **calendar-day** overlap of the 7-day week with the period ÷ 7. Ninety's documented example:
   a week of Oct 27 – Nov 2 contributes **5/7 to October and 2/7 to November**.
3. Add `aggregate_entries_for_period(entries, period_start, period_end, rollup)` → prorate each
   weekly entry into the period, then `aggregate_values` per `rollup`. Skip entries with no
   `actual_value`; return `None` when nothing contributes.
4. Wire it in as a **display-only** aggregate. It must **not** change `status`, `status_indicator`,
   the `on_track`/`off_track` summary, or the trend count. In a rolled-up view Ninety deliberately
   keeps showing the single-period (weekly) Goal and Average values, so do not retro-fit these
   into the existing `total_metrics`/`on_track`/`off_track` fields. `Scorecard Report` is
   week-scoped, so decide between a read-only aggregate block and a new period projection.
5. Update the `prorate_for_period` row of the engine table in `docs/architecture.md` — it currently
   documents the wrong signature.
6. Then **2c**: sort the report snapshot and the L10 "Scorecard Review" agenda by
   `Measurable Group.order`, ungrouped metrics last.

Re-run the full suite after each sub-block. Do not commit unless asked.

### Gotchas learned in 2a (save yourself the time)

- **Never compare `doc.field` to a DB value during `before_insert`.** Frappe has not cast
  `self.week_start_date` yet, so it is still a `str` while `frappe.get_all` returns
  `datetime.date`. This raised
  `TypeError: '<' not supported between instances of 'datetime.date' and 'str'`.
  Use the engine's `_as_date`-backed helpers instead of raw comparisons.
- **The `Float` NOT NULL trap applies to Select/Int too if you add fields** — treat `0` as unset.
- Seeding a metric requires a `Player` in that team for the owner user, or
  `EOSMetric.validate_owner_team` throws
  `Owner <strong>Administrator</strong> has no Player record in team <strong>...</strong>.`
- Running a single doctype module is much faster for iteration:
  `bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard_report.test_scorecard_report`

### Do not forget

- **No comments or docstrings** in code. Intent goes in the docs.
- Ground every behaviour in **Ninety's documented behaviour**; when unsure, search Ninety's help
  centre (`help2.eos.ninety.io`) rather than assuming. Verify claims by running code or querying
  the DB, not from memory.
- After any `*.json` edit: `bench --site resolv.localhost migrate`, then re-run the suite.
- Pass explicit `as_of`/dates in tests — never rely on `date.today()`.
- Keep reporting honest about "tested" vs "usable".
