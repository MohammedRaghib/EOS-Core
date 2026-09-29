# Roadmap — Eos Core (Ninety.io clone)

Acknowledge-phase-by-phase build plan. **This file is the phase *history*, not the work queue.**
The live queue is [`TODO.md`](TODO.md) — every open item below has been given a stable ID there and
is tracked there instead.

> Why: this file, `AGENTS.md` and `architecture.md` each used to carry their own copy of the
> outstanding work. Three lists, three formats, no sync — which is how the todos got duplicated and
> went stale. One list, one owner.

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
- [x] `scorecard_engine.py`: `compute_status`, `compute_achievement`, `compute_status_indicator`,
      `completed_period_statuses`, `aggregate_values`
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
- [x] Tests: `test_team.py` (4), `test_eos_metric.py` (12), `test_player.py` (4); engine unit tests (63) — all green

**Exit criteria (met):** org hierarchy usable (Organization → nested Teams), Players attached to
teams and Users, metric creation scoped to a team, per-team list filters possible.

## Phase 3 — Scorecards, Groups, Formulas `[x] DONE`

- [x] Schema revision: range orientation rules (`Inside/Outside min/max`) on `EOS Metric`
      (adds `min_value`/`max_value`)
- [x] `Scorecard` (Standard): `team`, `timeframe` (Weekly/Monthly/Quarterly/Annual) — one per team ×
      timeframe; attached via `EOS Metric.scorecard` (auto-created on metric save)
- [x] `Measurable Group` (Standard): `group_name`, `scorecard` (Link→Scorecard), `order`, up to 20
      groups per scorecard. `order` is read by `sort_metrics_by_group`, which orders the
      `Scorecard Report` snapshot and the L10 "Scorecard Review" agenda (Block 2c)
- [x] Formula Builder (Smart Measurables): `formula` (Small Text, `{Name}` variable syntax) on
      `EOS Metric`, `is_smart` toggle, `is_manual` toggle on `Scorecard Entry` (label
      "Manual Override" — the roadmap previously called this field `manual_override`)
- [ ] Forecasting / custom period goals (per-period target overrides) — deferred
- [x] Rollup views: `Scorecard.get_rollup_view` (Block 2b) is a whitelisted **read-only** endpoint
      returning Ninety's Month/Quarter/Year "View by" columns. `week_overlap_days` splits straddling
      weeks **by calendar day** (Oct 27 – Nov 2 → 5/7 October, 2/7 November), `aggregate_entries_for_period`
      applies `EOS Metric.rollup` (Total/Average), and the weekly `goal` is deliberately left
      unaggregated. No new DocType: Ninety states View by does not convert weekly measurables into
      monthly/quarterly ones. **No UI reads it yet.**
- [~] Trends: only the `count_consecutive_off_track` helper exists (3+ weeks → eligible Issue).
      Ninety's Trends **view** (a read-only, filterable list of measurables narrowed to off-track
      ones) is not built

## Phase 4 — Meetings & Reporting `[x] DONE`

- [x] `Level 10 Meeting` (Standard): `team` + `meeting_date` (unique at the app level, no DB
      index — `DEBT-7`), `status`
      (Planned → In Progress → Complete), format autoname `{team}-{meeting_date}`, default 6-item
      agenda auto-populated (`Segue`/`Scorecard Review`/`Good News`/`To-Dos`/`IDS`/`123s of the Week`).
      The "Scorecard Review" item is pre-filled with the team's measurables **in
      `Measurable Group.order`** (ungrouped last) plus each one's status indicator
- [x] `Meeting Agenda Item` (Child): `section`, `completed`, `notes` — renders the L10 agenda
- [x] `Meeting To Do` (Child): `description`, `owner_user`, `due_date`, `completed`
- [x] `Issue` (Standard): IDS workflow — `status` (`Identified`/`Discussing`/`Solved`/`Dropped`,
      forward-only transitions), `priority`, `owner_user`, `team`, `source` (Manual/Scorecard),
      `originating_metric`, `solution` required on Solve
- [x] "Make it an Issue": `create_issue_from_metric` — turns an off-track measurable into an Issue
      (uses latest entry / specific week, records consecutive-off-track count, links back)
- [x] Weekly scorecard report (`Scorecard Report`): one per team × week, auto-generates a snapshot
      of all non-archived metrics + off-track summary + trend detection, ordered by
      `Measurable Group.order`. `send_report` emails the team leader (or a chosen recipient) via a
      Jinja template.
- [x] Tests: `test_level_10_meeting.py` (7), `test_scorecard_report.py` (14) — all green

## Phase 5 — EOS Operating System `[x] DONE`

- [x] `V/TO` (Vision/Traction Organizer): `VTO` (Standard, one per Organization — enforced by a
      `unique` index on `organization`) with five auto-populated sections —
      `VTO Core Focus` (purpose/niche/10-year target), `VTO Marketing Strategy`
      (threes/uniques/process/guarantee), `VTO 3 Year Picture`, `VTO 1 Year Plan`,
      `VTO Quarterly Rocks`
- [x] `Rock` (90-day goal): `rock_name` (unique at the app level, no DB index — `DEBT-7`),
      `status` (`Not Started`/`In Progress`/`Complete`/`Dropped`, forward completion gated on
      milestones), `scope` (Company/Team/Individual),
      `owner_user`, `duration_start`/`duration_end` (there is no single `duration` field),
      head-down hours, `Rock Milestone` child rows, `mark_complete` closes
      linked To-Dos
- [x] `To Do`: `todo_name`, `status` (`Not Started`/`In Progress`/`Complete`/`Dropped`,
      forward-only), `owner_user`, `team`, `due_date`, optional link to a `Rock`, `To Do Item`
      child rows, `cascade_todo_transitions` for leadership rollups. `todo_name` carries
      `unique: 1`, so it is enforced by a real DB unique index (verified: key `todo_name`,
      `Non_unique=0`); a duplicate raises `frappe.DuplicateEntryError`
- [x] `Quarterly Review`: `team` × `period_start` (unique at the app level, no DB index —
      `DEBT-7`), auto-snapshot on insert — pulls the team's Rocks (Company-scoped + own-team) with
      milestone progress, To-Dos due within the
      period (overdue judged against `period_end`), and team Measurables as **On Track / Off Track
      counts** (not green/red) via `build_quarterly_review`
- [x] Tests: `test_rock.py` (5), `test_to_do.py` (5),
      `test_quarterly_review.py` (5), `test_vto.py` (4) — all green; full suite **243** tests (63 unit + 180 integration) as of 2026-09-29

**Definition of done (met):** all 24 Eos Core DocTypes registered (migrate clean, zero orphans);
create an Organization → auto-populated `V/TO`, add Rocks with milestones → mark complete cascades
To-Dos; `Quarterly Review` snapshots the quarter with a single insert.

> That is met **as a code path, not as a user flow.** `mark_complete` is whitelisted and tested, but
> `Rock` declares `"actions": []` and there is no client script, so nobody can click it — see `UI-7`.
> `V/TO` and `Quarterly Review` are usable today through the default desk form (System Manager only);
> the live database holds **0** rows in `VTO`, `Rock`, `To Do` and `Quarterly Review`, so no Phase 5
> workflow has been exercised by a person.

## Known gaps in Phases 1–5 (audited 2026-09-28, re-verified after Blocks 1 and 2)

> **Audit record — not a queue.** Every item below was re-verified against the code and the live
> database on 2026-09-28 and is tracked with a stable ID in [`TODO.md`](TODO.md). Fixes land here as
> history; new work is queued in `TODO.md` only.

"DONE" above means *the code exists and is tested*. It does **not** mean every roadmap claim is
implemented or that the feature is reachable from the UI. The following were audited against the
current code and are genuinely incomplete.

**Unwired — code exists, zero call sites**

| Item | State |
|---|---|
| `week_overlap_ratio`, `quarter_bounds` | Public, unit-tested, still no production call site. `week_overlap_days` is the form actually used by `aggregate_entries_for_period`; `quarter_bounds` remains unused. |
| 3 unused constants in `scorecard_engine.py` | `RANGE_OPERATORS` (public alias of the private `_RANGE_OPERATORS`, which *is* used), `ALL_OPERATORS`, `MATCHLESS_OPERATORS` — dead. `RANGE_OPERATORS` is **also re-declared independently** in `eos_metric.py:17`, so the range tuple is duplicated across two modules and the two can drift. |

**No user interface at all**

`public/js` and `public/css` are empty; there are no client scripts, no `doctype_js` and no
`doc_events` in `hooks.py` (which is boilerplate only: `app_name`, `app_title`, `app_publisher`,
`app_description`, `app_email`, `app_license`). Only four `@frappe.whitelist()` methods exist:
`rock.mark_complete`, `rock.get_rock_summary`, `scorecard_report.send_report`,
`scorecard.get_rollup_view`. `create_issue_from_metric` is server-side only with no UI trigger.
Everything is currently reachable only through the default Frappe form / console. Block 4 /
Phase 7.

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
| `issue.py` `count_consecutive_from_db` | Signature was `(metric_name)` only — it fetched the metric's **entire** history, so an Issue raised about an old week was stamped with a streak running through the **most recent** week. | fixed — takes `as_of` and caps the query with `week_start_date <= as_of` |
| `scorecard_report.py` `send_report` | `open(template_path)` with no `encoding=`, but the template contains em-dashes (`E2 80 94`). Works on a UTF-8 locale, raises `UnicodeDecodeError` where the platform default is not UTF-8. | fixed — `encoding="utf-8"` |
| `vto.py` `populate_sections` | Appended all five sections unconditionally, so a V/TO created with one of `core_focus` / `marketing_strategy` supplied skipped population entirely (the guard used `and`) — and would have **duplicated** the supplied section had the guard been `or`. | fixed — appends only the sections that are empty |
| `team.py` `validate_parent_team` | The `while current:` walk-up unpacked `frappe.db.get_value("Team", current, [...])` with no `None` guard, so a dangling **grandparent** (reachable only after a parent is deleted under a saved child, since Frappe validates links before `validate()`) raised `TypeError: cannot unpack non-iterable NoneType`. | fixed — `as_dict` + readable validation error naming the missing team |

Still open: **none in this table.** Every bug found by this audit is now fixed.

Found *after* the audit and tracked in `TODO.md`: `BUG-5` and `DATA-2`, both now fixed. `DATA-2`'s
recorded mechanism was wrong — the failure is a `format:` autoname **colliding with an existing name**,
not `ensure_scorecard` failing to match — and `Scorecard.team`/`timeframe` are now immutable so it
cannot recur.

**Smaller items**

- `Organization` and `Scorecard Entry` controllers are still empty (`pass`) with no tests.
  `Player` is resolved (`DATA-1`): `Player.user` is deliberately **not** unique — Ninety states many
  users sit in multiple teams — and ownership is the `(user, team)` pair, which is what
  `validate_owner_team` already queries. One seat per person *per team* is now enforced.
- `compute_achievement` is still covered by unit tests with no production call site.
- `test_quarter_bounds_rolls_over_year` is **misnamed**: it asserts `quarter_bounds(2026-01-05)` →
  Jan 1 – Mar 31, i.e. Q1 of the *same* year, and never crosses a year boundary. The rollover
  branch in `_quarter_end` is correct but only reachable for an anchor in Nov/Dec, which
  `quarter_bounds` normalises to a Q4 start before calling it, so no test covers that path.
- `scorecard_report.py` computes `trends` twice: `build_scorecard_report`'s result is discarded and
  the value recomputed from child rows. Dead work.
- `rock.py` duplicates the milestone-progress logic that `quarterly_review.py` also implements.
- `quarterly_review.py` also pulls `scope == "Individual"` rocks that happen to carry a `team` into
  a team review (arguably intended, undocumented), and rocks with **no** milestones contribute
  `progress = 0.0` to `rock_avg_progress` rather than being excluded.
- **Formatting debt** (recorded, not fixed — deliberately left out of the parity work):
  `vto/vto.py` is the only Python file using 4-space indentation, which violates
  `.editorconfig` / `pyproject.toml` (`indent-style = "tab"`) and would be rewritten wholesale by
  `ruff-format`; and **19** `.py` files are missing a final newline.
- **The database holds test residue only** (~1 Organization, 1 Team, 1 Player, 1 Scorecard).
  Nothing has been exercised end-to-end by a user — the 150 green tests are not evidence that any
  workflow works in the browser.

## Block 2 — Ninety parity `[x] DONE`

- [x] **2a Status indicator.** `compute_status_indicator` + `completed_period_statuses` implement
      Ninety's 3-most-recently-*completed*-periods window; `Scorecard Report Metric.status_indicator`
      persists it and the weekly report email renders it. `compute_health` deleted.
- [x] **2b Proration + rollup.** `prorate_for_period` now clamps the ratio to 0–1 and rejects
      negative/zero input. Added `week_overlap_days` / `week_overlap_ratio` (Ninety's day-level
      split), `aggregate_entries_for_period`, `normalise_view_by`, `period_bounds`,
      `advance_period`, `period_label` and `rollup_periods`. Wired through the whitelisted
      read-only `Scorecard.get_rollup_view`, which applies `EOS Metric.rollup` and leaves `status`,
      `status_indicator` and the on/off-track counts untouched. Ninety parity required a **read-only
      projection, not a new DocType**, so `Scorecard Report` was left alone.
- [x] **2c Group order → L10.** `sort_metrics_by_group` orders the report snapshot and the L10
      "Scorecard Review" agenda item (pre-filled in `notes` at insert) by `Measurable Group.order`,
      ungrouped measurables last.
- [x] **2a follow-up — indicator gap parity.** `completed_period_statuses` now returns exactly the
      last 3 *completed calendar intervals* (via `recent_completed_period_starts`) with `None` for
      unscored ones, and `compute_status_indicator` counts those `None`s as not-on-track, per
      Ninety's "empty periods count against the calculation". Previously gaps were invisible and a
      metric with holes could wrongly read `Green`.

## Phase 6 — Permissions & Roles `[~]`

**Landed 2026-09-29 (commit `83a2db8`):** the six roles now carry DocPerm blocks on all 13 standard
DocTypes, a team-scoping layer confines `Manager` / `Team Member` / `Observer` to their `Player`
seats, and three field-level guards cover what a DocPerm cannot express (a fourth followed in
`676fde8`).

**Landed 2026-09-29 (commit `676fde8`):** `PERM-12`. The grants now match Ninety's published tables
row for row. Team Members can delete a Rock and remove a Measurable, Observers can delete an Issue
and a To-Do, and `PERM-7`'s guard was narrowed to Ninety's documented locked set so a Team Member can
adjust a goal, a note and a group. The Measurable removal needed a fourth guard rather than a DocPerm
row, because Ninety scopes it to the KPI you own. The fifth row of the original audit, `Archive a
To-Do`, was recorded wrongly — Ninety does not grant it to Observer either — and what it exposed is
`DATA-3`: `To Do`, `Issue` and `Rock` have no `archived` field at all.

Still open in this phase: the Measurable Manager surface, the reorder rule, per-team worksheet
settings, and `PERM-9` — `EOS Metric.owner` is Frappe's immutable creator field, so a Measurable's
owner can never be reassigned and a Team Member can never own one.

Ninety's capability matrix:

| Role | Scorecard defaults | Groups (create / rename / reorder / delete) | Team scorecard settings | Data entry | Visibility |
|---|---|---|---|---|---|
| **Owner** | Company-wide | yes | yes | yes | Measurable Manager |
| **Admin** | Company-wide | yes | yes | yes | Measurable Manager |
| **Coach** (Implementer) | Company-wide | omitted † — granted as Admin | yes | yes | Measurable Manager |
| **Manager** | no | yes | yes | yes | no Measurable Manager |
| **Team Member** | no | reorder within a group only | no | yes | no Measurable Manager |
| **Observer** | no | no | no | no (view only) | no Measurable Manager |

- [x] Create the six Frappe roles: Owner, Admin, Coach, Manager, Team Member, Observer (`PERM-1`)
- [x] DocPerm blocks per DocType reflecting the matrix above (`PERM-2`) — per-DocType table in
      `architecture.md` §3h; `archive`/`unarchive` withheld from all six until the Measurable Manager
      exists
- [x] Team-scoped row visibility via `permission_query_conditions` + `has_permission` (`PERM-6`) —
      the layer `PERM-2` depended on, built first; scope is `Player.user` + `Player.team`, **not** a
      Frappe User Permission
- [x] Team Members may enter data without touching Measurable settings (`PERM-7`) — a field-level
      guard, because Frappe gates child rows on the parent's `write`
- [x] `Coach` and `Observer` may not own a Measurable or a Rock (`PERM-8`) — a validation, not a
      DocPerm
- [x] `send_report` gated on `email`, not reachable by a read-only role (`PERM-10`)
- [x] Decide `Coach`'s group access, which Ninety's docs omit (`PERM-11`) — granted, as Admin
- [x] Reconcile the grants with Ninety's published tables (`PERM-12`) — Team Member gained
      `Remove Measurables` (own-only, via a guard) and `Delete a Rock`; Observer gained
      `Delete an Issue` and `Delete a To-Do`; `PERM-7`'s field list now matches Ninety's locked set
- [ ] **Team Members may reorder measurables within a group, even measurables they do not own** (`PERM-3`) — DocPerm half is in place; needs the grid (`UI-1`) and a reorder carve-out in `PERM-7`'s guard
- [ ] Only Owner / Admin / Coach see the Measurable Manager (`PERM-4`) — DocPerm half is in place; needs the surface
- [ ] Worksheet-level column visibility and status-colour toggles (team-level settings) (`PERM-5`)
- [ ] A Measurable's owner is reassignable and distinct from its creator (`PERM-9`) — schema change
- [ ] `Rock`, `Issue` and `To Do` can be archived (`DATA-3`) — the field does not exist, so Ninety's
      archive and archive view are unimplementable

> **The matrix above is not all DocPerm work.** Verified 2026-09-28: a DocPerm row cannot scope a
> role to *some* teams. Of the six columns, only **Data entry** is a plain DocPerm grant; the other
> five need a `permission_query_conditions` layer. Both halves are now implemented — the grants and
> the scoping — and the 66 generated tests in `eos_core/test_permissions.py` pin one per role per
> DocType. What the matrix still does not describe is everything with no UI, which is why `PERM-3`
> and `PERM-4` are blocked on `UI-1` rather than on permissions.
>
> † Ninety's Groups article lists Owner, Admin, Manager, Team Member and Observer and omits Coach
> entirely — so this cell records what Ninety *publishes*, not what we built. Resolved as Admin and
> implemented, since Ninety describes a Coach as having Admin capabilities "with one exception:
> they cannot be assigned items" and a group is not an item. Recorded, not assumed. (Corrected
> 2026-09-29: the cell previously read a flat "no", which contradicted the `PERM-11` decision and the
> `Measurable Group` grant below it.)

## Phase 7 — Integrations, Bulk UX & Ninety parity `[ ]`

- [ ] Scorecard grid UI: a Worksheet Page + whitelisted grid endpoint, plus a UI trigger for
      `create_issue_from_metric` (Block 4, the largest parity gap) — `UI-1`, `UI-2`
- [ ] DocType actions for the three built endpoints that nothing can reach: `rock.mark_complete`,
      `rock.get_rock_summary`, `scorecard_report.send_report` (all whitelisted and tested, all with
      `"actions": []` and no client script) — `UI-7`. Smallest UI work in the project, and
      independent of `PERM-2`/`UI-1`
- [ ] Import/export scorecards (XLSX/CSV), bulk paste, bulk archive/duplicate/share — `UI-6`
- [ ] Connectors (Jira, Salesforce, Google Sheets) via Webhook/ServerScript — design first

Remaining Ninety features with no representation anywhere in the app:

- [ ] **Add Existing Measurable** — share one Measurable across teams with synced data; and Duplicate
- [ ] **Auto-seeded default measurables** on account creation (Ninety ships 17, or 20 financial ones
      depending on the doc version)
- [ ] **Set New Goal** from a date forward, and **Set Custom Goal** for a single period (distinct
      from the deferred per-period forecasting)
- [ ] **Backfilling** periods that predate a Measurable's creation
- [ ] **Lightning-bolt indicator** on formula ("Smart") measurables — the `is_manual` field already
      matches Ninety's Manual Override requirement, so only the indicator is missing
- [ ] Trends view: Ninety's read-only, filterable list narrowed to off-track measurables
- [ ] Scorecard column toggles: Owner / Goal / Average / Total visibility, "Show current period",
      default timeframe, and a per-team override of company defaults (Phase 6)

## Contribution checklist (for every phase)

1. Re-read `AGENTS.md` (rules, commands, gotchas) and `docs/architecture.md` (terminology + model),
   and open `docs/TODO.md` to find the item you are picking up.
2. Ground any behavioural question in Ninety's documented behaviour before designing. It is a clone;
   do not re-ask the five settled decisions listed in `AGENTS.md`.
3. Scaffold DocTypes under `eos_core/eos_core/doctype/<name>/` (v16 layout).
4. Keep pure logic in `scorecard_engine.py`; thin controllers otherwise. No comments/docstrings.
5. Run `bench --site resolv.localhost migrate` and verify registration — required after **any**
   `*.json` edit, including a `permissions` block.
6. Add tests under each doctype dir (`test_<name>.py`) and run
   `bench --site resolv.localhost run-tests --app eos_core`. Keep tests date-independent: pass
   explicit dates or `as_of`, never `date.today()`.
7. When the item is finished, move it from `TODO` to *Done* **in `docs/TODO.md` with the commit
   SHA**, ticking both its `code+tests` and `reachable` boxes where they apply. Update
   `docs/architecture.md` only if the domain model or terminology actually changed. Re-derive test
   counts with `grep -rc 'def test_'` rather than trusting the tables in this file or in `AGENTS.md`.
8. Do not add new work items to this file. They go in `docs/TODO.md` with a new ID.