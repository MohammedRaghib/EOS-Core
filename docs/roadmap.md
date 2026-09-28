# Roadmap — Eos Core (Ninety.io clone)

Acknowledge-phase-by-phase build plan. **Update this file as the project moves**; it is the source
of truth for what exists and what is next.

Legend: `[x]` done, `[ ]` planned, `[~]` in progress

## Phase 1 — Scorecard Engine `[x] DONE`

Core data model and scoring logic for the "Data Component" of EOS.

- [x] `EOS Metric` (Standard): `metric_name`, `owner`(Link→User), `target_value`, `operator`
      (`>=`/`<=`/`==`, plus `Inside min/max` and `Outside min/max` added in Phase 3),
      `frequency` (`Weekly`/`Monthly`/`Quarterly`/`Annual`), `unit`,
      `unit_type` (Number/Currency/Percentage/Yes/No/Time), `rollup` (Total/Average), `archived`,
      `description`
- [x] `Scorecard Entry` (Child, `istable=1`): `metric`(Link→EOS Metric), `week_start_date`,
      `actual_value`, `status` (`On Track`/`Off Track`)
- [x] `entries` Table field on `EOS Metric` → `Scorecard Entry`
- [x] `scorecard_engine.py`: `compute_status`, `compute_achievement`, `compute_health`,
      `aggregate_values`
- [x] Auto-status on save via `EOSMetric.validate`
- [x] DocTypes registered in DB (migrate run); app installed on `resolv.localhost`

**Definition of done (met):** create an `EOS Metric`, add `entries` with `actual_value`, save —
entry statuses compute automatically; engine functions are importable and pure.

## Phase 2 — People & Structure `[x] DONE`

Ninety's five org levels so Measurables attach to teams and individuals:
Organization → Leadership team → Department → Team → Individual.

- [x] `Organization` (Standard): `organization_name`, `default_language`, `archived`
- [x] `Team` (Standard): `team_name`, `parent_team` (self-link, hierarchy), `leader` (Link→Player),
      `organization` (Link→Organization), `archived`
- [x] `Player` (Standard): `player_name`, `user` (Link→User), `team` (Link→Team), `job_title`,
      `seat`
- [x] Rules:
      - `Team.validate` rejects parent cycles and cross-organization parents
      - `EOSMetric.validate_owner_team`: when a metric is team-scoped its `owner` user must have a
        Player in that team (org-wide metrics with no `team` skip the rule)
- [x] `team` Link added to `EOS Metric` (null = organization-wide/global)
- [x] Tests: `test_team.py` (3), `test_eos_metric.py` (7); engine unit tests (24) — all green

**Exit criteria (met):** org hierarchy usable (Organization → nested Teams), Players attached to
teams and Users, metric creation scoped to a team, per-team list filters possible.

## Phase 3 — Scorecards, Groups, Formulas `[x] DONE`

- [x] Schema revision: range orientation rules (`Inside/Outside min/max`) on `EOS Metric`
      (adds `min_value`/`max_value`)
- [x] `Scorecard` (Standard): `team`, `timeframe` (Weekly/Monthly/Quarterly/Annual) — one per team ×
      timeframe; attached via `EOS Metric.scorecard` (auto-created on metric save)
- [x] `Measurable Group` (Standard): `group_name`, `scorecard` (Link→Scorecard), `order`, up to 20
      groups per scorecard. `order` is stored but **not yet read** — nothing sorts by it, so the
      "drives L10 review order" behaviour is still unbuilt (see Unwired items below)
- [x] Formula Builder (Smart Measurables): `formula` (Small Text, `{Name}` variable syntax) on
      `EOS Metric`, `is_smart` toggle, `is_manual` toggle on `Scorecard Entry` (label
      "Manual Override" — the roadmap previously called this field `manual_override`)
- [ ] Forecasting / custom period goals (per-period target overrides) — deferred
- [ ] Rollup views: `prorate_for_period` and `aggregate_values` exist in the engine and the
      `rollup` field (Total/Average) is stored on `EOS Metric`, but **none of it is wired to any
      call site**. Ninety prorates weekly entries into Month/Quarter/Year "View by" aggregates and
      applies `rollup` to them; that wiring is unbuilt (see Unwired items below)
- [~] Trends: only the `count_consecutive_off_track` helper exists (3+ weeks → eligible Issue).
      Ninety's Trends **view** (a read-only, filterable list of measurables narrowed to off-track
      ones) is not built

## Phase 4 — Meetings & Reporting `[x] DONE`

- [x] `Level 10 Meeting` (Standard): `team` + `meeting_date` (unique), `status`
      (Planned → In Progress → Complete), format autoname `{team}-{meeting_date}`, default 6-item
      agenda auto-populated (`Segue`/`Scorecard Review`/`Good News`/`To-Dos`/`IDS`/`123s of the Week`)
- [x] `Meeting Agenda Item` (Child): `section`, `completed`, `notes` — renders the L10 agenda
- [x] `Meeting To Do` (Child): `description`, `owner_user`, `due_date`, `completed`
- [x] `Issue` (Standard): IDS workflow — `status` (`Identified`/`Discussing`/`Solved`/`Dropped`,
      forward-only transitions), `priority`, `owner_user`, `team`, `source` (Manual/Scorecard),
      `originating_metric`, `solution` required on Solve
- [x] "Make it an Issue": `create_issue_from_metric` — turns an off-track measurable into an Issue
      (uses latest entry / specific week, records consecutive-off-track count, links back)
- [x] Weekly scorecard report (`Scorecard Report`): one per team × week, auto-generates a snapshot
      of all non-archived metrics + off-track summary + trend detection. `send_report` emails the
      team leader (or a chosen recipient) via a Jinja template.

## Phase 5 — EOS Operating System `[x] DONE`

- [x] `V/TO` (Vision/Traction Organizer): `VTO` (Standard, one per Organization — enforced by a
      `unique` index on `organization`) with five auto-populated sections —
      `VTO Core Focus` (purpose/niche/10-year target), `VTO Marketing Strategy`
      (threes/uniques/process/guarantee), `VTO 3 Year Picture`, `VTO 1 Year Plan`,
      `VTO Quarterly Rocks`
- [x] `Rock` (90-day goal): `rock_name` (unique), `status` (`Not Started`/`In Progress`/`Complete`/
      `Dropped`, forward completion gated on milestones), `scope` (Company/Team/Individual),
      `owner_user`, `duration_start`/`duration_end` (there is no single `duration` field),
      head-down hours, `Rock Milestone` child rows, `mark_complete` closes
      linked To-Dos
- [x] `To Do`: `todo_name`, `status` (`Not Started`/`In Progress`/`Complete`/`Dropped`,
      forward-only), `owner_user`, `team`, `due_date`, optional link to a `Rock`, `To Do Item`
      child rows, `cascade_todo_transitions` for leadership rollups. Note: `todo_name` is **not
      enforced as unique** — there is no `unique` index and no Python check; duplicates only
      collide incidentally via the `format:TD-{todo_name}` autoname
- [x] `Quarterly Review`: `team` × `period_start` (unique), auto-snapshot on insert — pulls the
      team's Rocks (Company-scoped + own-team) with milestone progress, To-Dos due within the
      period (overdue judged against `period_end`), and team Measurables as **On Track / Off Track
      counts** (not green/red) via `build_quarterly_review`
- [x] Tests: `test_rock.py` (5), `test_to_do.py` (4), `test_vto.py` (2),
      `test_quarterly_review.py` (4) — all green; full suite 69 tests (26 unit + 43 integration)

**Definition of done (met):** all 24 Eos Core DocTypes registered (migrate clean, zero orphans);
create an Organization → auto-populated `V/TO`, add Rocks with milestones → mark complete cascades
To-Dos; `Quarterly Review` snapshots the quarter with a single insert.

## Known gaps in Phases 1–5 (audited 2026-09-28, re-verified after Block 1)

"DONE" above means *the code exists and is tested*. It does **not** mean every roadmap claim is
implemented or that the feature is reachable from the UI. The following were audited and are
genuinely incomplete.

**Unwired — code exists, zero call sites**

| Item | State |
|---|---|
| `compute_health` (Green/Yellow/Red) | Never called by any controller. It is also **not Ninety's algorithm** — Ninety derives the status indicator from the 3 most recently *completed* reporting intervals (Green = on target for all 3, Yellow = missed ≥1, Red = missed all 3, plus a "No Recent Data" state), not from a 10%-tolerance single-value check. Needs a rewrite, not wiring. |
| `aggregate_values` + `EOS Metric.rollup` | `rollup` (Total/Average) is stored but has no effect. Ninety's equivalent is the "Show rollup data as" option governing Month/Quarter/Year "View by" aggregates. |
| `prorate_for_period` | Never called. Signature is `(value, elapsed, total)` — it does **not** clamp to 0–1 despite `architecture.md` claiming it does, and negative input returns a negative value. Ninety prorates weekly entries into calendar periods, so this is required for rollup parity, not optional. |
| `Measurable Group.order` | Stored, never read. Ninety: group order carries over to the L10 meeting agenda. |

**No user interface at all**

`public/js` and `public/css` are empty; there are no client scripts and only three
`@frappe.whitelist()` methods. `create_issue_from_metric` is server-side only with no UI trigger.
Everything is currently reachable only through the default Frappe form / console.

**Known logic bugs**

Fixed in the Block 1 correctness pass:

| Location | Bug | Status |
|---|---|---|
| `quarterly_review.py` `_rock_rows` | A Rock that is both `scope="Company"` **and** on the review team was returned by both queries and double-counted in `rock_total` and `rock_avg_progress`. | fixed — deduped by name |
| `scorecard_report.py` `_build_metric_block` | Ignored the report's own `week_start_date`, so a report for week W showed each metric's latest entry regardless of date (and the off-track trend was measured into the future). | fixed — entries filtered to `<= week_start_date` |
| `eos_metric.py` `validate_formula` | Validated by substituting `1.0` for every variable, so a valid formula like `{A}/(1-{B})` was rejected ("Formula is invalid") because the probe divided by zero. | fixed — new `validate_formula_syntax()` checks parse/safety without evaluating |
| `eos_metric.py` `apply_formula` | If any referenced metric was missing a value for a week, the entry's `actual_value` was set to `None`, erasing data. | fixed — the entry is now left untouched |
| `scorecard_engine.py` `compute_achievement` | `operator="<="` with `actual_value=0` raised an uncaught `ZeroDivisionError`. | fixed — returns 100.0 / 0.0 by target sign |
| `eos_metric.py` `validate_range_target` | `min_value`/`max_value` are Frappe `Float` columns (`decimal NOT NULL DEFAULT 0`), so they came back as `0.0` after any reload. Because `0 is not None`, **re-saving any non-range metric threw** "Min Value and Max Value apply only to range operators". No test had re-saved a metric. | fixed — 0 normalised to unset |
| `scorecard_engine.py` `evaluate_formula` | The 25-variable guard counted the size of the supplied dict rather than the number of variables in the formula. | fixed |

Still open:

| Location | Bug |
|---|---|
| `issue.py` `count_consecutive_from_db` | Ignores its `week_start_date` argument; the streak is computed over the metric's full history. |
| `scorecard_report.py` `send_report` | Reads the Jinja template with `open()` and no `encoding=`, but the file contains em-dashes. |
| `vto.py` `populate_sections` | Guarded by `if not core_focus and not marketing_strategy`, so a VTO created with only one section populated leaves the other four empty. |
| `team.py` `validate_parent_team` | `frappe.db.get_value` result is unpacked without a `None` guard. |

**Smaller items**

- `Player`, `Organization` and `Scorecard Entry` controllers are empty (`pass`) with no tests.
  `Player.user` has no uniqueness rule, so one user can sit in many teams — which makes
  `EOSMetric.validate_owner_team` ambiguous about which team owns the user.
- `compute_achievement`, `compute_health`, `aggregate_values` and `prorate_for_period` are covered
  by unit tests but have no production call site; the tests give an impression of wiring that does
  not exist.
- Dead code in `scorecard_engine.py`: `_STATUS_ORDER_NONE`, `_STATUS_ORDERS`, `RANGE_OPERATORS`,
  `ALL_OPERATORS`, `MATCHLESS_OPERATORS`, `SmartMetricStatus` are never referenced, and the
  year-rollover branch in `_quarter_end` is unreachable.

## Phase 6 — Permissions & Roles `[ ]`

- [ ] Map Ninety roles → Frappe roles: Owner, Admin, Coach/Implementer, Manager, Team Member (data
      entry), Observer (read-only)
- [ ] DocPerm blocks per DocType; Measurable Manager access restricted to Owner/Admin/Coach
- [ ] Worksheet-level column visibility and status-color toggles (team-level settings)

## Phase 7 — Integrations & Bulk UX `[ ]`

- [ ] Import/export scorecards (XLSX/CSV), bulk paste, bulk archive/duplicate/share
- [ ] Connectors (Jira, Salesforce, Google Sheets) via Webhook/ServerScript — design first

## Contribution checklist (for every phase)

1. Re-read this roadmap + `docs/architecture.md` to keep names/data flow consistent.
2. Scaffold DocTypes under `eos_core/eos_core/eos_core/doctype/<name>/` (v16 layout).
3. Keep pure logic in `scorecard_engine.py`; thin controllers otherwise. No comments/docstrings.
4. Run `bench --site resolv.localhost migrate` and verify registration.
5. Add tests under each doctype dir (`test_<name>.py`) and run `bench run-tests --app eos_core`.
6. Update this roadmap (checkbox) and `docs/architecture.md` (terminology + model).