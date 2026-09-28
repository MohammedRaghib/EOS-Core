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

## Repository layout

```
apps/eos_core/
├── AGENTS.md                    # this file
├── README.md
├── docs/
│   ├── architecture.md          # domain + data model + scoring logic (READ FIRST)
│   └── roadmap.md               # phases, statuses, and what to build next
└── eos_core/
    ├── scorecard_engine.py      # PURE functions: status/achievement/health/aggregation/formulas
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
| Scoring engine | `eos_core.scorecard_engine` | DONE — `compute_status`, `compute_achievement`, `compute_status_indicator`, `completed_period_statuses`, `aggregate_values`, `extract_variables`, `evaluate_formula`, `prorate_for_period`, `count_consecutive_off_track`, `scorecard_summary`, `default_agenda_sections`, `build_scorecard_report` |
| Auto-status + formulas | `EOSMetric.validate` | DONE — range validation, auto-create Scorecard, formula validation/recalc, entry status loop |
| Org structure | `Organization` / `Team` / `Player` | DONE — nested teams (cycle + cross-org validation), players mapped to users |
| Scorecard header | `Scorecard` | DONE — `team` + `timeframe` (unique combo), format autoname, auto-created on metric save |
| Measurable grouping | `Measurable Group` | DONE — `group_name`, `scorecard`, `order`; max 20 per scorecard, unique name per scorecard |
| Meetings | `Level 10 Meeting` / `Meeting Agenda Item` / `Meeting To Do` | DONE — unique team+date, status transitions, default 6-item agenda auto-filled |
| Issues (IDS) | `Issue` + `create_issue_from_metric` | DONE — forward-only transitions, solution required on Solve, "Make it an Issue" from off-track metric |
| Scorecard report | `Scorecard Report` / `Scorecard Report Metric` | DONE — team×week snapshot, auto-populated metrics, summary + trend counts, `send_report` emails via Jinja template |
| V/TO | `VTO` + 5 child sections | DONE — one per Organization, sections auto-populated on insert |
| Rocks | `Rock` / `Rock Milestone` | DONE — status + milestone gating, `mark_complete` cascades linked To-Dos |
| To-Dos | `To Do` / `To Do Item` | DONE — forward-only status, `cascade_todo_transitions` |
| Quarterly review | `Quarterly Review` | DONE — team × period snapshot of Rocks/To-Dos/Measurables |

Tests: `bench --site resolv.localhost run-tests --app eos_core` runs the whole suite — 47
integration + 35 pure-engine unit = **82 tests** (needs `allow_tests true`, already enabled on
`resolv.localhost`). To run a single module, add
`--module eos_core.eos_core.doctype.rock.test_rock`.

Permissions are System Manager only for now (role model is Phase 6 in the roadmap).

**There is no UI.** `public/js` and `public/css` are empty, there are no client scripts, and only
three `@frappe.whitelist()` methods. Everything is reachable only via the default Frappe form or
the console. Treat "DONE" in the table above as "the code exists and is unit-tested", not "the
feature is reachable by a user".

**Read `docs/roadmap.md` § "Known gaps in Phases 1–5" before starting any phase.** It lists the
unwired code (`aggregate_values`/`rollup`, `prorate_for_period`, `Measurable Group.order`) and the
open logic bugs, so you do not mistake tested-but-unwired code for working functionality.

## Working conventions

- DocType layout: `doctype/<scrubbed_name>/<scrubbed_name>.json` + `.py` + `__init__.py`
  (Frappe v16 — matches the `resolv` app in this bench; no `*_doctype` suffix).
- JSON schemas: follow the format of existing files (fields array, `field_order`,
  `naming_rule: "By fieldname"`, System Manager permission block, module `"Eos Core"`).
- Child DocTypes: `"istable": 1`, empty `permissions`.
- Business logic: keep pure logic in `scorecard_engine.py` (importable, no frappe imports), and use
  thin DocType controller methods for frappe glue (DB, sessions, events).
- Don't commit unless explicitly asked.

## What to build next

See `docs/roadmap.md`. The **code** for Phases 1–5 exists and is tested, but the verified gap list
in that roadmap is the real work queue — in order:

1. **Block 1 — open logic bugs** (Rock double-count in `quarterly_review`, report ignoring its own
   `week_start_date`, `validate_formula` rejecting valid formulas, `apply_formula` nulling
   user-entered values, `compute_achievement` division by zero).
2. **Block 2 — Ninety parity for the unwired features.**
   - **2a DONE** — Ninety's status indicator (3 most recently *completed* periods: Green all on
     track / Yellow ≥1 miss / Red all 3 miss / "No Recent Data") is implemented as
     `compute_status_indicator` + `completed_period_statuses`, persisted on
     `Scorecard Report Metric.status_indicator`. The non-Ninety 10%-tolerance `compute_health`
     was deleted.
   - **2b TODO** — `prorate_for_period` + `aggregate_values` + `rollup` are one feature (Ninety's
     "View by" Week/Month/Quarter/Year aggregation). Weeks that straddle a period boundary are
     split **by calendar day**, per Ninety: a week of Oct 27 – Nov 2 contributes 5/7 to October
     and 2/7 to November. The aggregate is display-only and must not affect on-track status.
   - **2c TODO** — `Measurable Group.order` must feed the L10 agenda order.
3. **Block 3 — Phase 6 Permissions & Roles** (Owner/Admin/Coach/Manager/Team Member/Observer →
   Frappe roles and DocPerm blocks). Ninety's matrix is published in its help centre.
4. **Block 4 — UI**, currently absent entirely.

Re-read the roadmap before starting so naming and data flow stay consistent with the architecture
document, and keep every behavioural decision grounded in Ninety's documented behaviour rather than
assumption.