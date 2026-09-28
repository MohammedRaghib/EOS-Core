# AGENTS.md — Hand-off guide for AI agents working on eos_core

You are working on **Eos Core**, a Frappe v16 re-implementation of **Ninety.io** (the EOS operating
system software). This file exists so you can start contributing without re-discovering the repo.
Read `docs/architecture.md` and `docs/roadmap.md` after this file.

## Ground rules (hard constraints from the product owner)

1. **Never write code comments or docstrings** in Python or JavaScript files you create or modify.
   State intent in the docs (`docs/*.md`) and via clear naming.
2. Do not change the DocType names `EOS Metric`, `Scorecard Entry`, or the `entries` Table field.
   Product terminology mapping to Ninety is described in `docs/architecture.md`.
3. After editing any `*.json` schema, run `bench migrate` and verify the DocType synced.
4. **This is a Ninety clone, so match Ninety.** When a behaviour is ambiguous, resolve it by
   checking Ninety's documented behaviour — not by picking the tidier design, and not by asking
   again. These five questions are already settled; do not re-open them:
   - **UI last.** Build order is correctness → parity → **permissions** → UI.
   - `compute_health` was deleted: it encoded a 10%-tolerance colour Ninety never shows.
   - `To Do.todo_name` carries a real `unique` DB index.
   - "View by" is a **read-only projection** over the existing `Scorecard`, not a new DocType.
   - **Empty completed intervals count against** the status indicator.

## Start here

Read in this order, then work from the queue in `docs/TODO.md`:

1. This file — rules, commands, gotchas.
2. `docs/TODO.md` — **the only live work queue**. Pick the top `TODO` item and follow its
   "Done when" line.
3. `docs/roadmap.md` — phase history and the audit behind the queue.
4. `docs/architecture.md` — domain model, engine contract, terminology mapping.
5. `eos_core/scorecard_engine.py` — frappe-free pure logic; the home for all new pure functions.

Never rely on a "DONE" marker in `roadmap.md` to mean a feature is usable — that marker only ever
meant "the code exists and is unit-tested".

## Environment

- Bench root: `frappe-bench` (this app lives at `apps/eos_core`).
- Sites: `resolv.localhost` (has `frappe`, `resolv`, and **`eos_core`** installed — run everything
  here), `development.localhost` (frappe only).
- App is installed on `resolv.localhost` only. If you add a new site, install eos_core there before
  migrating.
- Database: MariaDB. All DocTypes are standard (InnoDB) tables.

## Commands (run from `frappe-bench/`)

```bash
bench --site resolv.localhost migrate                    # sync schema changes
bench --site resolv.localhost install-app eos_core       # first-time install (unnecessary now)
bench --site resolv.localhost execute <path.to.function> --kwargs '{"k":"v"}'   # run one-off
bench --site resolv.localhost console                    # interactive shell (pipable for tests)
bench --site resolv.localhost list-doctypes -a           # confirm DocType is registered
bench run-tests --app eos_core --site resolv.localhost   # when tests exist
```

Example one-off execution of the scoring engine:

```bash
bench --site resolv.localhost execute eos_core.scorecard_engine.compute_status \
  --kwargs '{"target_value": 100, "actual_value": 80, "operator": ">="}'
```

Run one test module while iterating (much faster than the whole suite):

```bash
bench --site resolv.localhost run-tests \
  --module eos_core.eos_core.doctype.scorecard_report.test_scorecard_report
```

Test the pure engine with no site or frappe import at all (~1s, no DB):

```bash
cd /workspace/development/frappe-bench && ./env/bin/python -c "
import sys; sys.path.insert(0, 'apps/eos_core')
from eos_core.scorecard_engine import compute_status
print(compute_status(100, 0, '<='))"
```

Read-only DB introspection — pipe a script into the console:

```bash
cat > /tmp/q.py <<'EOF'
print("IDX:", frappe.db.sql("show index from `tabTo Do` where Key_name != 'PRIMARY'"))
EOF
bench --site resolv.localhost console < /tmp/q.py
```

Note `bench execute /tmp/q.py` does **not** work — Frappe resolves the argument as an app module
and raises `AppNotInstalledError`. Use the console for ad-hoc SQL.

## Repository layout

```
apps/eos_core/
├── AGENTS.md                    # this file
├── README.md
├── docs/
│   ├── TODO.md                  # THE live work queue — read this to pick up work
│   ├── architecture.md          # domain + data model + scoring logic (READ FIRST)
│   └── roadmap.md               # phase history + the audit behind the queue
└── eos_core/
    ├── scorecard_engine.py      # PURE functions: status/indicator/aggregation/formulas/rollup
    └── eos_core/doctype/
        ├── eos_metric/          # EOS Metric (Standard) + Table field `entries`
        ├── scorecard_entry/     # Scorecard Entry (Child, istable=1)
        ├── scorecard/           # Scorecard (Standard, team × timeframe)
        ├── measurable_group/    # Measurable Group (Standard, linked by metrics)
        ├── issue/               # Issue (Standard) + create_issue_from_metric
        ├── level_10_meeting/    # Level 10 Meeting (Standard) + agenda/to-dos
        ├── meeting_agenda_item/ # Meeting Agenda Item (Child)
        ├── meeting_to_do/       # Meeting To Do (Child)
        ├── scorecard_report/    # Scorecard Report (Standard) + snapshot + email send
        ├── scorecard_report_metric/ # Scorecard Report Metric (Child)
        ├── organization/        # Organization (Standard)
        ├── team/                # Team (Standard, nested hierarchy)
        ├── player/              # Player (Standard, person/seat)
        ├── vto/                 # V/TO (Standard, one per org) + 5 child sections
        ├── vto_core_focus/      # V/TO Core Focus (Child): purpose/niche/10-year target
        ├── vto_marketing_strategy/ # V/TO Marketing Strategy (Child): threes/uniques/process
        ├── vto_3_year_picture/  # V/TO 3 Year Picture (Child)
        ├── vto_1_year_plan/     # V/TO 1 Year Plan (Child)
        ├── vto_quarterly_rocks/ # V/TO Quarterly Rocks (Child)
        ├── rock/                # Rock (Standard) + milestone-gated completion
        ├── rock_milestone/      # Rock Milestone (Child)
        ├── to_do/               # To Do (Standard) + cascade_todo_transitions
        ├── to_do_item/          # To Do Item (Child)
        └── quarterly_review/    # Quarterly Review (Standard) + snapshot
```

## Current state (what is already done)

| Area | DocType / module | Status |
|---|---|---|
| Metric master data | `EOS Metric` | DONE — `metric_name`, `owner`, `team`, `target_value`, `operator` (`>=`/`<=`/`==`/`Inside min/max`/`Outside min/max`), `min_value`, `max_value`, `frequency`, `unit`, `unit_type`, `rollup`, `is_smart`, `formula`, `scorecard`, `group`, `archived`, `description`, `entries` |
| Period records | `Scorecard Entry` | DONE — `metric`, `week_start_date`, `actual_value`, `status` (On Track/Off Track), `is_manual` |
| Scoring engine | `eos_core.scorecard_engine` | DONE — status: `compute_status`, `compute_status_indicator`, `is_period_complete`, `completed_period_statuses`, `recent_completed_period_starts`. Achievement: `compute_achievement`. Rollup: `prorate_for_period`, `week_overlap_days`, `week_overlap_ratio`, `aggregate_entries_for_period`, `normalise_view_by`, `period_bounds`, `advance_period`, `period_label`, `rollup_periods`, `quarter_bounds`. Formulas: `extract_variables`, `evaluate_formula`, `validate_formula_syntax`. Aggregation/report: `aggregate_values`, `scorecard_summary`, `sort_metrics_by_group`, `build_scorecard_review_lines`, `build_scorecard_report`, `build_quarterly_review`, `count_consecutive_off_track`, `rollup_rock_summary`, `rollup_todo_summary`, `default_agenda_sections` |
| Auto-status + formulas | `EOSMetric.validate` | DONE — range validation, auto-create Scorecard, formula validation/recalc, entry status loop |
| Org structure | `Organization` / `Team` / `Player` | DONE — nested teams (cycle + cross-org validation), players mapped to users |
| Scorecard header | `Scorecard` | DONE — `team` + `timeframe` (unique combo), format autoname, auto-created on metric save |
| Measurable grouping | `Measurable Group` | DONE — `group_name`, `scorecard`, `order`; max 20 per scorecard, unique name per scorecard. `order` orders the report snapshot and the L10 review |
| Meetings | `Level 10 Meeting` / `Meeting Agenda Item` / `Meeting To Do` | DONE — unique team+date, status transitions, default 6-item agenda auto-filled |
| Issues (IDS) | `Issue` + `create_issue_from_metric` | DONE — forward-only transitions, solution required on Solve, "Make it an Issue" from off-track metric |
| Scorecard report | `Scorecard Report` / `Scorecard Report Metric` | DONE — team×week snapshot, auto-populated metrics, summary + trend counts, `send_report` emails via Jinja template |
| V/TO | `VTO` + 5 child sections | DONE — one per Organization, sections auto-populated on insert |
| Rocks | `Rock` / `Rock Milestone` | DONE — status + milestone gating, `mark_complete` cascades linked To-Dos |
| To-Dos | `To Do` / `To Do Item` | DONE — forward-only status, `cascade_todo_transitions` |
| Quarterly review | `Quarterly Review` | DONE — team × period snapshot of Rocks/To-Dos/Measurables |

Tests: `bench --site resolv.localhost run-tests --app eos_core` runs the whole suite in one go —
**77 integration + 63 pure-engine unit = 140 tests**, all green (needs `allow_tests true`, already
enabled on `resolv.localhost`). The split by file:

| Integration test | Count |
|---|---|
| `doctype/eos_metric/test_eos_metric.py` | 12 |
| `doctype/issue/test_issue.py` | 5 |
| `doctype/level_10_meeting/test_level_10_meeting.py` | 7 |
| `doctype/quarterly_review/test_quarterly_review.py` | 5 |
| `doctype/rock/test_rock.py` | 5 |
| `doctype/scorecard/test_scorecard.py` | 13 |
| `doctype/scorecard_report/test_scorecard_report.py` | 13 |
| `doctype/player/test_player.py` | 4 |
| `doctype/team/test_team.py` | 4 |
| `doctype/to_do/test_to_do.py` | 5 |
| `doctype/vto/test_vto.py` | 4 |
| **Integration total** | **77** |
| `eos_core/test_scorecard_engine.py` (unit, frappe-free) | **63** |

Re-derive these with `grep -rc 'def test_'` rather than trusting the table — the documented totals
have drifted more than once.

Permissions are System Manager only for now (role model is Phase 6 in the roadmap).

**There is no UI.** `public/js` and `public/css` are empty, there are no client scripts, and only
four `@frappe.whitelist()` methods (`rock.mark_complete`, `rock.get_rock_summary`,
`scorecard_report.send_report`, `scorecard.get_rollup_view`). Everything is reachable only via the
default Frappe form or the console. Treat "DONE" in the table above as "the code exists and is unit-tested", not "the
feature is reachable by a user".

**Read `docs/roadmap.md` § "Known gaps in Phases 1–5" before starting any phase.** It separates
bugs that are *fixed* from those *still open* (none), lists code that exists but has no call
site, and records that the database holds only test residue — nothing has been exercised
end-to-end by a user.

## Working conventions

- DocType layout: `doctype/<scrubbed_name>/<scrubbed_name>.json` + `.py` + `__init__.py`
  (Frappe v16 — matches the `resolv` app in this bench; no `*_doctype` suffix).
- JSON schemas: follow the format of existing files (fields array, `field_order`,
  `naming_rule: "By fieldname"`, System Manager permission block, module `"Eos Core"`).
- Child DocTypes: `"istable": 1`, empty `permissions`.
- Business logic: keep pure logic in `scorecard_engine.py` (importable, no frappe imports), and use
  thin DocType controller methods for frappe glue (DB, sessions, events).
- Don't commit unless explicitly asked.

## Gotchas that have already cost time

- **`Float` and `Int` columns are `NOT NULL DEFAULT 0`.** Frappe maps `Float` to
  `decimal(21,9) NOT NULL DEFAULT 0.000000000`, so a reload gives you `0.0` and you **cannot**
  distinguish "unset" from "explicitly zero" by value alone. This codebase treats `0` as unset —
  see `compute_status`, which returns `"On Track"` when `target_value == 0`. It is a real bug source:
  it made `validate_range_target` throw on *every* re-save of a non-range metric, because
  `0 is not None`. Consequence: a legitimate range bound of exactly `0` cannot be expressed today.
  `Measurable Group.order` has the same trap, where `0` means "unset", not "first".
- **Never compare a `doc.field` to a DB value during `before_insert`.** Frappe has not cast the
  attribute yet, so `self.week_start_date` is still a `str` while `frappe.get_all` returns a
  `datetime.date` → `TypeError: '<' not supported between instances of 'datetime.date' and 'str'`.
  Pass it to the engine's `_as_date`-backed helpers instead of comparing raw. Both the Scorecard
  Report and the L10 Scorecard Review rely on this.
- **Seeding a metric in a test requires a `Player` in that team** for the owner user, or
  `EOSMetric.validate_owner_team` throws *"Owner ... has no Player record in team ..."*.
- **Write tests date-independently.** Always pass explicit dates or an explicit `as_of`; never let
  a test depend on `date.today()`. `test_rock` had a latent time bomb that would only have failed
  from 2026-10-15. Week start dates are Mondays (`2026-08-17`, `2026-08-24`, …), and the status
  indicator's grid is Monday-aligned, so a non-Monday entry never matches an interval and is
  deliberately counted as a gap.
- `tabSingles` occasionally raises `MySQLdb.OperationalError (1020, "Record has changed since last
  read")` during test-env setup. It is infrastructure flakiness, not app code — re-run before
  investigating.
- **A failing test after a behaviour change is not automatically a wrong test.** Check whether the
  test encoded the *old* rule before editing the assertion, and say so explicitly when the test was
  the thing that was wrong.
- `Measurable Group` display names are only unique *per Scorecard*, so key any group lookup by the
  group's hash `name`, never by `group_name`.

## What the product owner expects in how you work

- The owner is a developer, **not an EOS domain expert**. They care about what actually works, and
  the roadmap previously hid the difference between "code written" and "feature usable". Keep
  reporting that distinction honestly; never let documentation overstate completion.
- They value **verified** claims. Prefer running the code, querying the DB, or fetching the real
  Ninety docs over asserting from memory, and flag anything you could not verify.
- Plain answers with a verdict beat hedged ones. Tables work well for comparison and prioritisation.
- Keep responses concise.

## What to build next

**`docs/TODO.md` is the only live work queue.** Read it before you start and before you finish.

The **code** for Phases 1–5 exists and is tested, but that is not the same as usable — see the
`code+tests` / `reachable` distinction in `docs/TODO.md` § Rules. As of 2026-09-28: 3 open logic
bugs, permissions at 0%, and no UI at all.

Do not reconstruct the work queue from `docs/roadmap.md` or from this file. Both used to carry their
own copies of the outstanding items, they drifted apart, and that is why the previous setup kept
producing duplicate and stale todos. `roadmap.md` is the phase *history*; `architecture.md` is the
*model*; `TODO.md` is the *tasks*.

Re-read `docs/roadmap.md` and `docs/architecture.md` before starting so naming and data flow stay
consistent, and keep every behavioural decision grounded in Ninety's documented behaviour rather
than assumption.