# UI-7 — Buttons for the three built endpoints nothing can reach

## Parent TODO

`UI-7` — **S2** · Buttons for the three built endpoints nothing can reach.
Block C (Phase 7: UI). S2 inside a block whose only other S2s depend on `UI-1`.

**Done when** (verbatim from `TODO.md`): a user can complete a Rock from its form (milestone gating
and the To-Do cascade both observable), read the Rock's summary from the form, and send a weekly
`Scorecard Report` by email. A test that the button exists in the app's own files is *not*
sufficient on its own — record a manual browser pass too, because an assertion cannot prove a button
is clickable.

## Objective

Each of the three whitelisted, already-tested methods is invocable from its DocType's desk form, by
a button that lives in the app's own files and therefore reproduces on a fresh site — and a manual
browser pass is recorded showing the workflow working, not just the file existing.

## Dependencies

- None from the permission work; `PERM-2` is closed and the methods already carry their guards.
- `send_report` calls `self.check_permission("email")` (`PERM-10`), so the button is only ever
  visible to a role that has `email` on `Scorecard Report` — Manager and above.
- **Requires `DEBT-11` first.** `Rock.progress` returns `int` `0` for a milestone-less rock and a
  `float` otherwise, and `get_rock_summary` serialises it straight to JSON. Fix that before this
  item, or the button ships a value whose JSON type flips with the data. `DEBT-11` is one line and
  has no execution plan — do it inline and record it here.
- **Independent of `UI-1`** and safe to land before it. `TODO.md` says so explicitly; do not let it
  get pulled behind the grid.

## Decisions to settle before implementing

1. **`doctype_js`, not a Client Script.** A Client Script record is *data*: it lives in the
   database, is not in git, and a fresh site would not have the buttons. `doctype_js` is app code
   and is applied on `bench migrate`. This is the choice `TODO.md` already makes and it is the
   reason this item is "reproducible".
2. **One `public/js/<scrubbed>/<scrubbed>.js` per DocType**, wired through
   `doctype_js = {"Rock": "public/js/rock/rock.js", ...}` in `hooks.py`. Do not use
   `app_include_js` — it loads on every desk page, including ones with no Rock on them.
3. **Add the actions to the DocType JSON's `actions` array.** `"actions": []` is why nothing appears
   today. A `doctype_js` file alone adds script but no button.
4. **The three buttons are independent.** They can land in any order and each can be verified on its
   own. Do not build a shared component for three call sites.

## Execution Tasks

### UI-7.1 — `DEBT-11`: `Rock.progress` returns a float
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/rock/rock.py:33` (the `return 0`), and
  `eos_core/eos_core/doctype/rock/test_rock.py`.
- **Acceptance criteria** `Rock.progress` returns `0.0` for a Rock with no milestones and a rounded
  `float` otherwise; a test covers the empty-milestone case and asserts the *type*, not just the
  value; `get_rock_summary` therefore emits a stable JSON type.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.rock.test_rock --site resolv.localhost
  ```
  Then `TODO.md`'s `DEBT-11` is moved to *Done* with the SHA, per rule 2.

### UI-7.2 — `Rock` form: Complete button and Summary dialog
- **Status** `TODO`
- **Scope** `eos_core/eos_core/doctype/rock/rock.json` (`actions`), `eos_core/hooks.py`
  (`doctype_js`), new `eos_core/public/js/rock/rock.js`, new
  `eos_core/public/css/rock/rock.css` only if needed.
- **Acceptance criteria**
  - a form action calls `rock.mark_complete` via `frappe.call` and reloads the form;
  - the milestone-gating refusal (an open milestone) is shown as a server message, not swallowed;
  - a second action calls `get_rock_summary` and renders progress, milestone counts and the To-Do
    rollup;
  - the buttons are declared in the JSON `actions` array, so they are in git;
  - `bench --site resolv.localhost migrate` was run after the JSON edit.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  python3 -c "import json;d=json.load(open('apps/eos_core/eos_core/eos_core/doctype/rock/rock.json'));print(d['actions'])"
  ```
  plus a manual browser pass: complete a Rock whose milestones are all ticked and watch the linked
  To-Dos close; try it on a Rock with an open milestone and confirm the refusal.

### UI-7.3 — `Scorecard Report` form: Send button
- **Status** `TODO`
- **Scope** `scorecard_report.json` (`actions`), `hooks.py`, new
  `eos_core/public/js/scorecard_report/scorecard_report.js`.
- **Acceptance criteria**
  - the action calls `send_report` and the form reflects `status = Sent` and `last_sent_on`;
  - the button is only rendered for roles with `email` on `Scorecard Report` — or, simpler and more
    honest, is rendered for everyone and the server's refusal is displayed. **Pick one and write
    down which**; do not ship a button that fails for `Observer` with no explanation;
  - a failure to find a recipient surfaces `No recipient configured for team …` rather than
    appearing to succeed.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  bench --site resolv.localhost run-tests --module eos_core.eos_core.doctype.scorecard_report.test_scorecard_report --site resolv.localhost
  ```
  `test_scorecard_report.py` already has the `Observer` refusal test from `PERM-10`; it must stay
  green. Plus a manual browser pass confirming the email arrives in the recipient's inbox and
  `status` flips to `Sent`.

### UI-7.4 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md` §7 (the "no UI" bullet), `AGENTS.md` (the "There is no UI"
  paragraph), `docs/TODO.md`.
- **Acceptance criteria** the docs name the three buttons and what each does; `TODO.md` moves
  `UI-7` to *Done* with the SHA and `reachable` ticked; `TODO.md`'s `DEBT-11` row is closed.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  after the doc edits. Plus the three manual passes, recorded verbatim in *Completed* — what was
  clicked, what was observed, which role.

## Current Task

`UI-7.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

None yet.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All four tasks.
