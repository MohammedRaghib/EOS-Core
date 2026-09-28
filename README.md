# Eos Core

A Frappe (v16) re-implementation of the **Ninety.io** app — the software implementation of the
EOS (Entrepreneurial Operating System) from *Traction*. This repository is a from-scratch clone of
Ninety's data model and workflows built as a native Frappe app.

> Note: Ninety's product language has one gap vs. this codebase: Ninety calls a metric a
> **Measurable** and the roll-up board a **Scorecard**. Here (per an earlier product decision) the
> metric DocType is **EOS Metric** and each period record is a **Scorecard Entry**. The mapping is
> documented in `docs/architecture.md`.

## Status

- **Phase 1 — Scorecard Engine: DONE.** Metric + entry DocTypes, a pure-Python scoring engine, and
  automatic status derivation are implemented and synced to the database.
- **Phase 2 — People & Structure: DONE.** `Organization`, `Team` (nested hierarchy with validation),
  and `Player` DocTypes; `EOS Metric` is now team-scoped with an owner-in-team rule.
- **Phase 3 — Scorecards, Groups & Formulas: DONE.** Range operators (`Inside/Outside min/max`),
  `Scorecard` (team × timeframe), `Measurable Group`, Formula Builder with `{Name}` syntax,
  `prorate_for_period`, `count_consecutive_off_track`, and the read-only "View by" rollup endpoint
  `Scorecard.get_rollup_view`. Forecasting/custom period goals deferred.
- **Phase 4 — Meetings & Reporting: DONE.** `Level 10 Meeting` (agenda + to-dos), `Issue`
  with the IDS workflow, "Make it an Issue" from an off-track measurable, and a weekly
  `Scorecard Report` with snapshot generation, off-track summary, trend detection, and
  email sending via a Jinja template.
- **Phase 5 — EOS Operating System: DONE.** `V/TO` (five auto-populated sections), `Rock`
  with milestone-gated completion that cascades linked To-Dos, forward-only `To Do`, and
  `Quarterly Review` team snapshots (Rocks/To-Dos/Measurables).
- **Phase 6 (permissions) and Phase 7 (integrations, bulk UX, remaining Ninety parity) are not
  started.** Every DocType is currently System Manager only.
- **Test suite: 129 tests** (63 pure-engine unit + 66 integration) — all green. Run them all with
  `bench --site resolv.localhost run-tests --app eos_core`.
- **No user interface yet.** `public/js` is empty and there are no client scripts, so everything is
  currently reachable only through the default Frappe forms or the console.

## Who is this README for?

- If you are a human: read `docs/architecture.md` then `docs/roadmap.md`.
- If you are an AI agent about to work on this repo: read `AGENTS.md` first — it tells you the
  conventions, exact bench commands, and current state so you can pick up without poking around.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench --site YOUR_SITE install-app eos_core
bench --site YOUR_SITE migrate
```

The DocTypes register with the database on `install-app` (which runs a migrate internally); run
`bench migrate` any time a `*.json` schema under `eos_core/.../doctype/` changes.

## Repository layout

```
apps/eos_core/
├── AGENTS.md                      # Hand-off guide for AI agents (read this first)
├── README.md                      # This file
├── docs/
│   ├── architecture.md            # Domain model, data model, scoring logic
│   └── roadmap.md                 # Phase-by-phase build plan + status
└── eos_core/
    ├── scorecard_engine.py        # Pure scoring/aggregation/formula functions (no frappe deps)
    ├── hooks.py
    ├── modules.txt                # Module: "Eos Core"
    └── eos_core/                  # Module directory ("Eos Core")
        └── doctype/
            ├── eos_metric/        # EOS Metric (Standard) + child Table `entries`
            ├── scorecard_entry/   # Scorecard Entry (Child, istable=1)
            ├── scorecard/         # Scorecard (Standard, team × timeframe)
            ├── measurable_group/  # Measurable Group (Standard, linked by metrics)
            ├── issue/             # Issue (Standard) + IDS workflow
            ├── level_10_meeting/  # Level 10 Meeting (Standard) + agenda/to-dos
            ├── meeting_agenda_item/ # Meeting Agenda Item (Child)
            ├── meeting_to_do/     # Meeting To Do (Child)
            ├── scorecard_report/  # Scorecard Report (Standard) + email send
            ├── scorecard_report_metric/ # Scorecard Report Metric (Child)
            ├── organization/      # Organization (Standard)
            ├── team/              # Team (Standard, nested hierarchy)
            └── player/            # Player (Standard, person/seat)
```

## Conventions (mandatory)

- **No code comments or docstrings** in any Python or JavaScript files. Intent goes in the docs
  and in self-explanatory naming.
- DocTypes live in `eos_core/eos_core/eos_core/doctype/<scrubbed_name>/` using Frappe v16's layout
  (no `*_doctype` suffix). See the `resolv` app in this bench for the reference layout.
- After editing any `*.json` schema: run `bench migrate` and verify with `bench list-doctypes -a`.

## License

mit