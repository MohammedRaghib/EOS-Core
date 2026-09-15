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
        ├── organization/        # Organization (Standard)
        ├── team/                # Team (Standard, nested hierarchy)
        └── player/              # Player (Standard, person/seat)
```

## Current state (what is already done)

| Area | DocType / module | Status |
|---|---|---|
| Metric master data | `EOS Metric` | DONE — `metric_name`, `owner`, `team`, `target_value`, `operator` (`>=`/`<=`/`==`/`Inside min/max`/`Outside min/max`), `min_value`, `max_value`, `frequency`, `unit`, `unit_type`, `rollup`, `is_smart`, `formula`, `scorecard`, `group`, `archived`, `description`, `entries` |
| Period records | `Scorecard Entry` | DONE — `metric`, `week_start_date`, `actual_value`, `status` (On Track/Off Track), `is_manual` |
| Scoring engine | `eos_core.scorecard_engine` | DONE — `compute_status`, `compute_achievement`, `compute_health`, `aggregate_values`, `extract_variables`, `evaluate_formula`, `prorate_for_period`, `count_consecutive_off_track`, `scorecard_summary`, `default_agenda_sections` |
| Auto-status + formulas | `EOSMetric.validate` | DONE — range validation, auto-create Scorecard, formula validation/recalc, entry status loop |
| Org structure | `Organization` / `Team` / `Player` | DONE — nested teams (cycle + cross-org validation), players mapped to users |
| Scorecard header | `Scorecard` | DONE — `team` + `timeframe` (unique combo), format autoname, auto-created on metric save |
| Measurable grouping | `Measurable Group` | DONE — `group_name`, `scorecard`, `order`; max 20 per scorecard, unique name per scorecard |
| Meetings | `Level 10 Meeting` / `Meeting Agenda Item` / `Meeting To Do` | DONE — unique team+date, status transitions, default 6-item agenda auto-filled |
| Issues (IDS) | `Issue` + `create_issue_from_metric` | DONE — forward-only transitions, solution required on Solve, "Make it an Issue" from off-track metric |

Tests: `bench --site resolv.localhost run-tests --app eos_core` runs 36 tests (set `allow_tests true`
first — already enabled on `resolv.localhost`).

Permissions are System Manager only for now (role model is Phase 6 in the roadmap).

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

See `docs/roadmap.md`. Phase 4 (Meetings & Reporting) is now in progress; the weekly scorecard report
is the remaining item. Phase 5 (V/TO, Rocks, To-Dos, quarterly reviews) is the next major phase.
Re-read the roadmap before starting so naming and data flow stay consistent with the architecture
document.