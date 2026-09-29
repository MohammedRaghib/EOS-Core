# TODO — Eos Core (Ninety.io clone)

**This file is the only live work queue.** `docs/roadmap.md` is the phase *history* and
`docs/architecture.md` is the *model*. Neither is a task list. If work is not in this file, it is
not queued.

Last full audit: **2026-09-28** — every item below was re-verified against the code, the live
`resolv.localhost` database, and a 129-test run. 129/129 green at that date.

**Since that audit**, Block A was closed in full (`BUG-1`..`BUG-5`, `DATA-1`, `DATA-2`) and `PERM-1`
landed, taking the suite to **150 (87 integration + 63 unit)**, all green. `DATA-2` was found while
closing `DATA-1` and is new; its recorded mechanism was wrong and is corrected in *Done*. The 129
figure above is kept as the audit record; the live count is 237.

**Block B was then worked**: `PERM-6` (the team-scoping layer) landed *first*, because it was the
stated blocker for `PERM-2`, and `PERM-2` followed. Doing them in that order turned up four items
that no prior list contained — `PERM-7`, `PERM-8`, `PERM-10` and `PERM-11` are closed. Two remain
open, and both were found *after* the release rather than before it:

- **`PERM-9` (S2)** — `EOS Metric.owner` is Frappe's immutable creator field, so a Measurable's
  owner can never be reassigned and only its creator can own one.
- **`PERM-12` (S1)** — five grants are narrower than Ninety publishes. Found by reading the roles
  article row by row after the code had already shipped, which is exactly the kind of check that
  should have happened first.

Suite: **237 (174 integration + 63 unit)**, all green. `bench migrate` run.

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
bench --site resolv.localhost run-tests --app eos_core     # full suite, 237 tests
bench --site resolv.localhost run-tests --module eos_core.test_permissions   # the permission layer
./env/bin/python -c "import sys; sys.path.insert(0,'apps/eos_core'); from eos_core.scorecard_engine import compute_status"  # engine only, no DB
```

**Reading the permission tests.** `eos_core/test_permissions.py` holds 20 hand-written tests plus
**66 generated ones** (11 team-scoped DocTypes × 6 roles), so the total is not visible from a
`grep -c 'def test_'`. The generated names are `test_visibility_<doctype>_<role>`, and each asserts
that a user holding a seat in Team A sees Team A's row of that DocType and — for `Manager`,
`Team Member` and `Observer` — **not** Team B's. Those 66 tests are the regression net for `PERM-6`;
if you change a condition in `eos_core/permissions.py`, this is what tells you.

---

# Queue

## Next up: `PERM-12` (S1), then `PERM-9`

Block A is **closed**. Block B (permissions) is now **mostly** built: the six roles carry DocPerm
blocks, the team-scoping layer exists, and the two field-level ownership/data-entry rules Ninety
states explicitly are enforced and tested. Two things remain before this block can be called correct
rather than merely present:

- **`PERM-12` (S1) — the grants disagree with Ninety in five rows.** Found by reading the roles
  article row by row *after* `PERM-2` shipped, not before. Four of the five rows are unblocked
  (Observer's Issue/To-Do rights, and Team Member's Rock delete); the fifth, Team Member deleting
  their own Measurable, needs an ownership check rather than a DocPerm row.
- **`PERM-9` (S2) — the data model, not the permission code.** `EOS Metric.owner` is Frappe's
  *immutable creator* field, so a Measurable's owner cannot be reassigned, only its creator can own
  one, and `validate_owner_team` is really a rule about creation rather than ownership. This blocks
  the last row of `PERM-12` and all of `PERM-4`'s Reassign action.

`PERM-3`, `PERM-4` and `PERM-5` are **UI-blocked**, not permission-blocked — their DocPerm halves
are already in place and tested.

---

## Block A — Correctness (0 open, 7 done)

---

## Block B — Phase 6: Permissions & Roles (11 items, 6 done, 5 open)

DocPerm blocks and the team-scoping layer are both live. Verified 2026-09-29 in the live DB: all 13
standard DocTypes carry **7** DocPerm rows (`System Manager` plus the six Ninety roles) and all 11
child tables carry none. `tabHas Role` still holds **zero** rows for the six roles on the demo site —
no user has been *given* a role, so nothing is gated there yet; the permission layer is proven by
`eos_core/test_permissions.py`, which creates its own users and seats.

### PERM-2 — S1 · DocPerm blocks per DocType from Ninety's matrix — **DONE**
**Status** `DONE` · code+tests ☑ · reachable ☑ · **Closed 2026-09-29**
**Matrix** (from `docs/roadmap.md` § Phase 6, cross-checked against Ninety's own help centre):

| Role | Scorecard defaults | Groups (create/rename/reorder/delete) | Team scorecard settings | Data entry | Measurable Manager |
|---|---|---|---|---|---|
| Owner | Company-wide | yes | yes | yes | yes |
| Admin | Company-wide | yes | yes | yes | yes |
| Coach | Company-wide | yes | yes | yes | yes |
| Manager | no | yes | yes | yes | no |
| Team Member | no | reorder within a group only | no | yes | no |
| Observer | no | no | no | view only | no |

The mapping actually applied, per DocType (full table in `docs/architecture.md` §3h):

| DocType | create / write / delete | Why |
|---|---|---|
| `Organization` | Owner, Admin, Coach | company setup is not a team action |
| `Team`, `Player` | + Manager | "Managers have … the ability to create new teams", invite users |
| `VTO`, `Scorecard` | + Manager | team/company scorecard settings |
| `EOS Metric` | create + Manager; write + Team Member; delete + Manager | Team Member cannot create a Measurable but must enter data (`PERM-7`) |
| `Measurable Group` | + Manager | only Owner/Admin/Manager manage groups; Coach decided as Admin (`PERM-11`) |
| `Issue`, `Level 10 Meeting`, `To Do` | + Team Member | team-collaborative workflows |
| `Rock` | create/write + Team Member, delete + Manager | Team Members own Rocks; deletion is narrower by choice |
| `Scorecard Report`, `Quarterly Review` | + Manager | snapshot surfaces are a settings-level action |
| child tables | none | children inherit the parent |

`archive`/`unarchive` is not a DocPerm column — it is a write to the `archived` field, which both
`EOS Metric` and `Measurable Group` have. So archiving follows `write`: `Observer` is refused by
DocPerm, `Team Member` is refused twice (DocPerm on the group, and `validate_data_entry_only` on the
metric), and the four Measurable-Manager roles may do it. No bulk-archive surface exists yet, which
is `PERM-4` and `UI-6`.

### PERM-3 — S2 · Team Members may reorder measurables they do not own
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-29**
**Note** this is an explicit Ninety rule and is *not* what a naive "owner-only" DocPerm gives you.
Ninety: *"Team Members can also reorder Measurables within a group — even Measurables they do not
own."* It also interacts with `Measurable Group.order`, where `0` means "unset" rather than "first"
because the column is `int NOT NULL DEFAULT 0`.
**Status after `PERM-2`** the DocPerm half is already correct and tested: a `Team Member` has
`write` on `EOS Metric` and is **read-only** on `Measurable Group` (`create`/`write`/`delete` all
`0`, verified live), so renaming or deleting a *group* is already impossible for them. What is
missing is the reorder itself — reordering measurables within a group means editing
`EOS Metric.group`, and `validate_data_entry_only` currently refuses that, because it is not an
`entries` row. The guard has to carve out the reorder without opening `target_value`/`operator`/
`frequency`/`team`.
**Done when** the grid exists and a user holding only `Team Member` can drag a measurable owned by
someone else inside its group, is refused outside it, and cannot rename or delete it — a test per
case. **Now blocked on `UI-1`.**

### PERM-4 — S2 · Only Owner / Admin / Coach see the Measurable Manager
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-29**
Ninety: *"Accessible only to Admins, Owners, or Coaches/Implementers. Managers and Team
Members/Managees cannot access the Measurable Manager."*
**Status after `PERM-2` — only half is DocPerm-covered, and the two cases differ.** Verified live:
`Team Member` has no `create`/`delete` on `EOS Metric` and no `write`/`create`/`delete` on
`Measurable Group`, and `Observer` has read-only on both — so for them Duplicate and Delete are
already refused, and `validate_data_entry_only` blocks `Team Member` from the remaining `write`.
**`Manager` is the case DocPerm cannot solve.** Ninety hides the Measurable Manager from Manager
while the capability matrix grants Manager full `create`/`write`/`delete` on both `EOS Metric` and
`Measurable Group` — and it must, because a Manager creating measurables on a scorecard is Ninety
behaviour. Narrowing the DocPerm to satisfy the visibility rule would break the capability matrix, so
this item has to gate the **surface** and must not be "solved" by removing grants. Note Block C has
no UI item for the Measurable Manager surface — add one when this starts.
**Done when** the Measurable Manager surface exists, is gated to Owner / Admin / Coach, and a test
asserts each of the six roles sees or does not see it — with a fourth assertion that a Manager can
still create a measurable from the scorecard while being denied the Manager surface.

### PERM-5 — S3 · Worksheet column visibility and status-colour toggles
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-28**
**Scope** per-team settings for which columns are visible and whether status colours show.
`PERM-6` settled where these settings *live* (a team-scoped setting row read by the grid), which
this item still has to build.

### PERM-6 — S1 · Team-scoped row visibility, which no DocPerm can express — **DONE**
**Status** `DONE` · code+tests ☑ · reachable ☑ · **Closed 2026-09-29**
**Representation decided: `Player.user` + `Player.team`, not a Frappe User Permission.** Ninety's own
docs are decisive. Users are invited with a **Team(s)** dropdown, "Many Ninety users are members of
multiple teams", and *"Roles in Ninety are company-wide, not team-specific"* — scope comes from team
membership alone, never from the role. `Player` is already that model (§3b) and is already the
thing `validate_owner_team` queries, so inventing a `User Permission` on `Team` would have created
a second, competing source of truth. A User Permission would also have been wrong: it is a single
link value per user per DocType, which cannot express a multi-team membership.

**Implementation** `eos_core/permissions.py`, wired through `hooks.py`:

- `permission_query_conditions` on the **11 team-scoped DocTypes** returns a SQL fragment, or
  `None` (no restriction) for a company-wide user.
- `has_permission` on the same 11 **denies** a document outside the user's teams. Frappe's
  controller hook can only deny, never grant, so it narrows the DocPerm block and nothing else.
  This is the layer that stops a direct `frappe.get_doc(name)` by name or link, which a query
  condition alone would not.
- `assigned_teams(user)` reads `Player` rows. A user with **no** seat gets `1 = 0` and sees no
  team rows at all — the first implementation spliced the empty clause in after the field name and
  produced `tabTeam.team 1 = 0`, a SQL syntax error; there is now a test
  (`test_seatless_team_scoped_role_sees_no_team_rows`) for it.
- **Unsaved documents are never denied.** The hook returns `True` for a new doc, so `create` is
  governed by DocPerm alone. Without this a Manager could not create a `Team` at all, because the
  new doc's name is `None` and so is in no team. This is correct and matches Ninety: a Manager may
  create a team, and then must be added to it before they can see it.
- **Company-wide rows stay company-wide.** A row with no team is visible to every role, per
  `architecture.md` §3b ("Metrics without `team` are organization-wide"). `Rock.scope = 'Company'`
  gets the same treatment. `To Do` and `Player` have no such notion, so a team-less row of those is
  visible to its **owner** and to the company-wide roles only — a personal item, not a company one.
  `Measurable Group` has no team column and is scoped through its `Scorecard` in a subquery.

**Verification** 66 generated tests, `test_visibility_<doctype>_<role>` — one per role per
team-scoped DocType, exactly the "test per role per DocType" this item asked for. Suite: 174
integration + 63 unit.

### PERM-7 — S2 · A `Team Member` write grant on `EOS Metric` is document-wide — **DONE**
**Status** `DONE` · code+tests ☑ · reachable ☑ · **Closed 2026-09-29** · *found 2026-09-29 while
applying `PERM-2`*
**Where** `eos_core/permissions.py:validate_data_entry_only`, called first in `EOSMetric.validate`
**Problem** data entry in this app is the `entries` child table of `EOS Metric`, and Frappe gates
child rows on the **parent's** `write` permission. So the DocPerm grant that lets a Team Member
enter data — which Ninety requires — also hands them write on every setting on the Measurable.
Landing `PERM-2` without narrowing this would have handed Team Members the right to change
`metric_name`, `unit_type` and `owner` on any Measurable, which Ninety explicitly reserves for
Manager and above.
**How** a field-level guard. `validate_data_entry_only` compares the submitted doc against
`get_doc_before_save()` and throws if any non-child, non-system field other than `entries` changed.
`Administrator` and any `System Manager` holder is exempt; `frappe.flags.ignore_permissions` is
exempt.
**Gotcha worth keeping** the guard must run **first** in `validate`, before `validate_range_target`.
`validate_range_target` rewrites a `0` `min_value`/`max_value` to `None` (they are
`NOT NULL DEFAULT 0`, so a reload gives `0.0`), which would otherwise read as a settings change and
throw on every data entry. The first version ran the guard last and failed exactly that way.
**Verified scope — and the guard is broader than Ninety (see `PERM-12`).** Ninety defines the locked
set precisely, in a footnote on the Scorecard Permissions article: *"'Edit Measurable settings'
refers to a Measurable's title, unit type, and ownership — locked to Manager and above. It does not
include Set new future Goal, Set custom Goal or note, or entering forecasted future values; those are
Scorecard actions any Team Member can use."* The current guard blocks **every** non-entry field, so
it is correct for `metric_name`, `unit_type` and `owner`, but also blocks `target_value`,
`min_value`/`max_value`, `description`, `group` and `archived`, all of which Ninety lets a Team
Member change. Recorded as `PERM-12` rather than loosened here, because two of those fields are the
home of `PARITY-3` (goal-setting) and `PERM-3` (reordering), and neither surface exists yet to test
against.

### PERM-8 — S2 · `Coach` and `Observer` may not own a Measurable or a Rock — **DONE**
**Status** `DONE` · code+tests ☑ · reachable ☑ · **Closed 2026-09-29** · *found 2026-09-29 while
applying `PERM-2`*
**Where** `eos_core/permissions.py:validate_content_owner`, called from `EOSMetric.validate` and
`Rock.validate`
**Evidence** Ninety states it in a footnote on every accountability tool: *"they cannot be assigned
as a Measurable owner on any team's Scorecard"*, *"cannot be assigned as the owner of a Rock"*, and
the same for a To-Do, an Issue and a Headline. The roles tables give the row as
`Own Measurables  ✅ ✅ ✅ ✅ ❌ ❌` in Ninety's own column order —
**Owner | Admin | Manager | Managee (= Team Member) | Observer | Implementer (= Coach)** — and
`Own Rocks`, `Own To-Dos` and `Own Issues` are identical. No DocPerm expresses this, because a
DocPerm cannot see *which user* a field points at, so it is a validation rather than a permission
block: `OWNER_ROLES = Owner, Admin, Manager, Team Member`.

### PERM-9 — S2 · `EOS Metric.owner` is Frappe's creator, so a Measurable's owner is fixed — **OPEN**
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-29** · *found 2026-09-29 while
closing `PERM-8`*
**Where** `eos_core/eos_core/doctype/eos_metric/eos_metric.json`, field `owner`
**Problem** `EOS Metric.owner` is not a business field. It collides with Frappe's document `owner`,
which is in `meta.get_set_only_once_fields()`: Frappe sets it to the creating user on insert and
refuses any later change with `CannotChangeConstantError`. Verified live:
`get_set_only_once_fields()` returns `creation` and `owner` for `EOS Metric`, and only
`rock_name`/`creation`/`owner` for `Rock` — so `Rock.owner_user` **is** a free business field while
`EOS Metric.owner` is not. Three consequences, all test-pinned:
1. A Measurable's owner is always its creator, so only a user who can *create* measurables can own
   one. `PERM-2` gives `create` to Manager and above, and Ninety gives Team Members the right to
   own Measurables — so **a Team Member can never own a Measurable in this app.**
2. There is no way to reassign a Measurable's owner, so Ninety's Measurable Manager "Reassign"
   bulk action has nothing to act on.
3. `validate_owner_team` ("the owner must hold a `Player` record in the metric's team") is therefore
   really a rule about **who is allowed to create a Measurable on a team** — which is right, but is
   not what the docs say it is.
**Not fixed here** on purpose: adding a second owner field, or renaming, is a schema decision with
downstream effects on `validate_owner_team`, the report snapshot, the scorecard grid and the
existing 12 `EOS Metric` tests. It needs its own item, not a drive-by.
**Done when** a Measurable has a real, reassignable owner field distinct from its creator, a
`Team Member` can be assigned one, `validate_owner_team` is re-pointed at it and re-documented, and
`PERM-8`'s ownership guard covers both it and `Rock.owner_user`.

### PERM-10 — S2 · `send_report` was callable by any user with read — **DONE**
**Status** `DONE` · code+tests ☑ · reachable ☑ · **Closed 2026-09-29** · *found 2026-09-29 while
applying `PERM-2`*
**Where** `eos_core/eos_core/doctype/scorecard_report/scorecard_report.py`
**Problem** Frappe's `run_doc_method` loads a document with `check_permission=True`, which is a
**read** check. Before `PERM-2`, no non-`System Manager` had any DocPerm, so `send_report` was
unreachable. After it, an `Observer` has read on `Scorecard Report` and could therefore call
`send_report` — which emails the team leader *before* its own `self.save()` fails on the missing
write permission. The email goes out; the save is what fails.
**Done when** `send_report` calls `self.check_permission("email")` first, and a test asserts an
Observer is refused with `frappe.PermissionError` and that `frappe.sendmail` is never called.
`email` is granted to Manager and above, matching the DocPerm block.

### PERM-11 — S3 · Ninety's docs never say whether a `Coach` may manage Measurable Groups — **DONE**
**Status** `DONE` (as a recorded decision, not code) · **Closed 2026-09-29** · *found 2026-09-29*
**Problem** Ninety's "Organizing Scorecards with Groups" says *"Owners, Admins, and Managers can
create, rename, reorder, and delete Scorecard groups. Team Members and Observers can view, expand,
and collapse groups."* Coach/Implementer is **absent from the article**, and so is the paired
question of whether a Coach can reorder measurables within a group. It is a documentation gap, not
a stated restriction.
**Decision** treat `Coach` as `Admin` for groups, i.e. grant it `create`/`write`/`delete` on
`Measurable Group`. The reasoning is the same one Ninety uses everywhere else: a Coach has Admin
capabilities *"with one exception: they cannot be assigned items"*, and a group is not an item.
Recorded in `architecture.md` §3h rather than left implicit. No test beyond the DocPerm matrix one,
which pins the grant.
**Revisit** if Ninety publishes a contrary statement.

### PERM-12 — S1 · The DocPerm blocks are narrower than Ninety in five places — **OPEN**
**Status** `TODO` · code+tests ☐ · reachable ☐ · **Verified 2026-09-29** · *found 2026-09-29 by
reading the roles article row by row after the release, not before it*
**Evidence** [User Roles and Permissions](https://help.ninety.io/en/articles/14306404-user-roles-and-permissions),
whose tables are ordered **Owner | Admin | Manager | Managee (= Team Member) | Observer |
Implementer (= Coach)**. This is the first pass that compared every row against the grants actually
in the DB, and five rows disagree:

| Action | Ninety grants it to | We grant it to | Deviation |
|---|---|---|---|
| **Remove Measurables** | all but Observer | Owner, Admin, Coach, Manager | **Team Member missing** |
| **Delete a Rock** | all but Observer | Owner, Admin, Coach, Manager | **Team Member missing** |
| **Delete an Issue** | all six, Observer included | all but Observer | **Observer missing** |
| **Delete a To-Do** | all six, Observer included | all but Observer | **Observer missing** |
| **Archive a To-Do** | all but Observer | write, all but Observer | **Observer missing** |

Narrowing is not automatically wrong — but every one of these was written up as a *deliberate*
narrowing or simply went unmentioned, which is not the same thing. Two need care rather than a JSON
edit:

- **`Remove Measurables` is ownership-scoped in Ninety.** The Scorecard Permissions article footnotes
  it: *"Team Members and Managers can delete KPIs they're assigned to from the My 90 Scorecard
  widget, while Admins, Owners, and Coaches can archive or delete any KPI from the KPI Manager"*, and
  lists under *Team Members cannot* → *"Delete Measurables owned by others."* A DocPerm `delete` row
  would grant deletion of **every** measurable in the Team Member's teams, which is a *parity
  regression*, not an implementation. This one needs an ownership check in `validate` (compare `owner`
  to the session user before allowing a delete) — and it is blocked on `PERM-9`, because `owner` is
  the creator, not the assigned owner.
- **`Delete a Rock` needs the same ownership question answered**, because `Rock.owner_user` *is* a
  real field, so unlike `EOS Metric` this could be done today.

**`PERM-7` is also in scope here**, from the other direction: its guard blocks *every* non-entry
field, while Ninety's locked set is only **title, unit type and ownership**. See `PERM-7` for the
quote.

**Done when** each of the five rows is either brought in line with Ninety or recorded as a named,
intentional deviation in `architecture.md` §7 with its reason, and `PERM-7`'s field list matches
Ninety's locked set — each with a test that would fail if the grant moved back.

---

## Block C — Phase 7: UI (7 items, 0% done — the largest gap)

`eos_core/public/` contains only `.gitkeep`. `hooks.py` has no `doctype_js` and no `doc_events`.
Four whitelisted endpoints exist and nothing in the UI calls them — only two of them
have an item below (`UI-2` for the not-yet-whitelisted `create_issue_from_metric`, `UI-3` for
`get_rollup_view`); the other two are `UI-7`.

**Changed by Block B.** The grid can now be built against a real permission model: a
`permission_query_conditions` layer already scopes every team-scoped DocType, and
`eos_core/test_permissions.py` pins the six roles' visibility per DocType. Two consequences for
this block: `UI-1` should read rows through `frappe.get_list` (not `frappe.get_all`, which bypasses
permissions) or the grid will show other teams' measurables, and `UI-5`'s per-team column settings
have a defined home (`PERM-5`).

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
**Note** `PERM-6` makes this harder than it looks: a Measurable shared across two teams can only
have one `team`, so the sharing model has to answer which team a shared Measurable's *entries* belong
to before the scoping rule can stay true. Do not start before `PERM-9` — a shared Measurable also
needs the reassignable owner that item introduces.

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
| `PERM-2` | DocPerm blocks per DocType from Ninety's matrix | 2026-09-29 | `83a2db8` |
| `PERM-6` | Team-scoped row visibility, which no DocPerm can express | 2026-09-29 | `83a2db8` |
| `PERM-7` | A `Team Member` write grant on `EOS Metric` is document-wide | 2026-09-29 | `83a2db8` |
| `PERM-8` | `Coach` and `Observer` may not own a Measurable or a Rock | 2026-09-29 | `83a2db8` |
| `PERM-10` | `send_report` was callable by any user with read | 2026-09-29 | `83a2db8` |
| `PERM-11` | Ninety's docs never say whether a `Coach` may manage Measurable Groups | 2026-09-29 | `83a2db8` |

### `PERM-2` + `PERM-6` — the DocPerm blocks and the scoping layer, in that order

`PERM-6` landed first, because it was the recorded blocker. The order was worth it: applying `PERM-2`
on its own would have shipped three defects that the matrix test now prevents (`PERM-7`, `PERM-8`,
`PERM-10`), and `PERM-6`'s own "which representation" question had a clean answer only once the
DocPerm half was pinned down.

**`PERM-6` — representation: `Player`, not a Frappe User Permission.** Ninety's docs are explicit
that scope comes from team membership and *not* from the role: users are invited with a **Team(s)**
dropdown, *"Many Ninety users are members of multiple teams"*, and *"Roles in Ninety are
company-wide, not team-specific. A user cannot be an Admin on one team and an Observer on another."*
`Player` (`user` + `team`) already models exactly that and is already what `validate_owner_team`
queries, so it became the single source of truth. A User Permission was rejected on two grounds: it
is a single link value per user per DocType and so cannot express multi-team membership, and it
would have been a second competing source of truth for the same fact.

**`PERM-6` — two bugs the tests caught, both worth keeping in mind.**
1. The empty-team case. `team_list_clause({})` returned the bare string `1 = 0`, which was then
   spliced in *after* the column name — `` `tabTeam`.`team` 1 = 0 `` — so a user holding a
   team-scoped role but no `Player` seat got a `ProgrammingError` on **every** list view of **all
   eleven** DocTypes rather than an empty list. Fixed by making the clause carry the field
   reference (`team_clause(field, teams)`) and returning a complete predicate. It was found by the
   seatless-user test, not by reading the code.
2. The unsaved-document case. `has_permission` ran `doc_in_assigned_teams` on a document with no
   name yet, so `doc.name in teams` was `False` and **every** `create` on a team-scoped DocType was
   denied. A Manager could not create a `Team`. Fixed by returning no opinion for a new doc, which
   leaves `create` to DocPerm — the correct division, and it matches Ninety: a Manager may create a
   team and then has to be added to it before they can see it.

**`PERM-2` — the matrix, and what it does not cover.** Full per-DocType table in
`architecture.md` §3h. `archive`/`unarchive` is not a DocPerm column at all — it is a write to the
`archived` field that both `EOS Metric` and `Measurable Group` carry — so it follows `write`, and
`Observer` and `Team Member` are refused for them by the two other guards. `share` is `0` for
`Team Member` and `Observer` everywhere (and for `Manager` on `Organization`, `Player`, `Team` and
`VTO`), so neither can widen a document's visibility past the team scoping `PERM-6` puts around
them; `submit`, `cancel`, `amend`, `import`, `if_owner`, `select` and `print` are `0` on all 78
rows, and `email` is `1` on exactly one row per role, `Scorecard Report`, which is what
`send_report` now checks. `Rock` delete is `Manager` and above while create/write is `Team Member`
and above — **this is a deviation, not a narrowing**, and it is why `PERM-12` exists: Ninety's roles
article publishes `Delete a Rock ✅✅✅✅❌✅`, i.e. every role but Observer, and we deny Team Member.
`Issue`, `Level 10 Meeting` and `To Do` are mapped to "Team Member and above" **by analogy** with the
verified Measurable matrix, not from a Ninety page that enumerates them; that is stated in
`architecture.md` §3h rather than dressed up as a citation.

**`PERM-11` — one genuine documentation gap, decided rather than guessed.** Ninety's Groups article
names Owner, Admin, Manager, Team Member and Observer and omits Coach entirely, in the same
sentence pattern it uses elsewhere. Since Ninety describes a Coach as having Admin capabilities
*"with one exception: they cannot be assigned items"*, and a group is not an item, `Coach` was
granted group management. Logged as a decision so it can be reversed if Ninety says otherwise.

**Tests** `eos_core/test_permissions.py` is new: 20 hand-written tests plus **66 generated**
(`test_visibility_<doctype>_<role>`, 11 team-scoped DocTypes × 6 roles) — the "test per role per
DocType" `PERM-6` asked for, which is why the file's `grep -c 'def test_'` (20) does not match its
86 tests. The generated family is what pins the scoping, and `test_docperm_matrix_matches_the_ninety_capability_table`
is what pins the DocPerm blocks, so a careless JSON edit now fails the suite rather than silently
widening access. Three other suites grew by one test each: the data-entry guard, the ownership
guards, and `send_report`. Suite: **237/237 (174 integration + 63 unit)**. `bench migrate` was
required and run — the 13 `permissions` arrays are inert without it.

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

Next item to land: `PERM-12` (S1). Four of its five rows are unblocked JSON edits; start by reading
the table rather than the prose, and do **not** "fix" `Remove Measurables` with a DocPerm row — that
one needs an ownership check and waits on `PERM-9`. `PERM-9` after that, since it is a schema change
that `PARITY-1` is also gated behind. `PERM-3`, `PERM-4` and `PERM-5` are UI-blocked.
