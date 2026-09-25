# Roadmap — Eos Core (Ninety.io clone)

Acknowledge-phase-by-phase build plan. **Update this file as the project moves**; it is the source
of truth for what exists and what is next.

Legend: `[x]` done, `[ ]` planned, `[~]` in progress

## Phase 1 — Scorecard Engine `[x] DONE`

Core data model and scoring logic for the "Data Component" of EOS.

- [x] `EOS Metric` (Standard): `metric_name`, `owner`(Link→User), `target_value`, `operator`
      (`>=`/`<=`/`==`), `frequency` (`Weekly`/`Monthly`/`Quarterly`/`Annual`), `unit`,
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
- [x] Tests: `test_team.py` (3), `test_eos_metric.py` (2); engine unit tests (6) — all green

**Exit criteria (met):** org hierarchy usable (Organization → nested Teams), Players attached to
teams and Users, metric creation scoped to a team, per-team list filters possible.

## Phase 3 — Scorecards, Groups, Formulas `[x] DONE`

- [x] Schema revision: range orientation rules (`Inside/Outside min/max`) on `EOS Metric`
      (adds `min_value`/`max_value`)
- [x] `Scorecard` (Standard): `team`, `timeframe` (Weekly/Monthly/Quarterly/Annual) — one per team ×
      timeframe; attached via `EOS Metric.scorecard` (auto-created on metric save)
- [x] `Measurable Group` (Standard): `group_name`, `scorecard` (Link→Scorecard), `order`, up to 20
      groups per scorecard, order matters (drives L10 review order)
- [x] Formula Builder (Smart Measurables): `formula` (Small Text, `{Name}` variable syntax) on
      `EOS Metric`, `is_smart` toggle, `manual_override` on `Scorecard Entry`
- [ ] Forecasting / custom period goals (per-period target overrides) — deferred
- [x] Rollup views: `prorate_for_period` helper for split-week proration; `rollup` Total vs Average
- [x] Trends view: `count_consecutive_off_track` helper (3+ weeks → eligible Issue)

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

- [x] `V/TO` (Vision/Traction Organizer): `VTO` (Standard, one per Organization, format autoname)
      with five auto-populated sections —
      `VTO Core Focus` (purpose/niche/10-year target), `VTO Marketing Strategy`
      (threes/uniques/process/guarantee), `VTO 3 Year Picture`, `VTO 1 Year Plan`,
      `VTO Quarterly Rocks`
- [x] `Rock` (90-day goal): `rock_name` (unique), `status` (`Not Started`/`In Progress`/`Complete`/
      `Dropped`, forward completion gated on milestones), `scope` (Company/Team/Individual),
      `owner_user`, duration, head-down hours, `Rock Milestone` child rows, `mark_complete` closes
      linked To-Dos
- [x] `To Do`: `todo_name` (unique), `status` (`Not Started`/`In Progress`/`Complete`, forward-only),
      `owner_user`, `team`, `due_date`, optional link to a `Rock`, `To Do Item` child rows,
      `cascade_todo_transitions` for leadership rollups
- [x] `Quarterly Review`: `team` × `period_start` (unique), auto-snapshot on insert — pulls the
      team's Rocks (Company-scoped + own-team) with milestone progress, To-Dos due within the
      period (overdue judged against `period_end`), and team Measurables (green/red counts) via
      `build_quarterly_review`
- [x] Tests: `test_rock.py` (5), `test_to_do.py` (4), `test_vto.py` (2),
      `test_quarterly_review.py` (4) — all green; full suite 56 tests (19 unit + 37 integration)

**Definition of done (met):** all 24 Eos Core DocTypes registered (migrate clean, zero orphans);
create an Organization → auto-populated `V/TO`, add Rocks with milestones → mark complete cascades
To-Dos; `Quarterly Review` snapshots the quarter with a single insert.

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