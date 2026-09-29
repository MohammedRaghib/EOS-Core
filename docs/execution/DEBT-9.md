# DEBT-9 — Formatting debt

## Parent TODO

`DEBT-9` — **S3** · Formatting debt.
Block F (Code debt).

**Problem** (verbatim): `eos_core/eos_core/doctype/vto/vto.py` is the only Python file indented with
4 spaces, violating `.editorconfig` and `pyproject.toml` (`indent-style = "tab"`); `ruff format` would
rewrite it wholesale. **19** `.py` files are missing a final newline.

**Done when** (verbatim): `ruff format` runs clean and `git diff` is reviewed line by line — the
`vto.py` reindent will show as a whole-file change.

## Objective

The app's Python is formatted by the tool the project already declares, the one-file tab/space
inconsistency is gone, and the whole-formatting change is provably behaviour-preserving.

## Dependencies

- None.
- `BUG-3` (closed) deliberately left `vto.py`'s reindent here "so this commit is not mixed with it".
  This item is where that was always going to happen.
- `DEBT-6` may add or touch `vto_*` controller files. **Do this item after `DEBT-6`**, or accept
  reformatting the same files twice.

## Decisions to settle before implementing

1. **`ruff` is configured but not installed.** `.pre-commit-config.yaml` pins `ruff` `v0.14.10` and
   `pyproject.toml` sets `line-length = 110`, `target-version = "py314"`, `quote-style = "double"`,
   `indent-style = "tab"`. Neither `ruff` nor `pre-commit` is on `env/bin` in this bench. Decide how
   to run it — `pip install ruff==0.14.10` into the bench env, `uvx`, or a pre-commit run — and
   **pin the version** so the formatting is reproducible and a different version does not churn the
   diff.
2. **The pre-commit config already runs `ruff-format`, so this codebase currently does not pass its
   own hooks.** Confirm that before starting, so the item's premise is verified rather than assumed,
   and so it is known whether `ruff-format` will do more than the `vto.py` reindent and the 19
   newlines.
3. **Formatting and behaviour must be separated in the diff.** A whole-file reindent makes a real bug
   invisible. Run the full suite **before** and **after**, record both counts, and review the diff for
   any hunk that is not whitespace.
4. **Do not mix a real change into this commit.** If `ruff format` reveals a genuine defect (a long
   line that should be a call, a shadowed name), fix it under its own `TODO.md` ID, not here.

## Execution Tasks

### DEBT-9.1 — Get `ruff` running at the pinned version
- **Status** `TODO`
- **Scope** tooling only; no repository file changes beyond possibly a documented version pin.
- **Acceptance criteria** `ruff --version` reports `0.14.10`; `ruff check` runs over the app and its
  output is recorded **before** any change, so the lint baseline is known.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  ./env/bin/ruff --version
  ./env/bin/ruff check apps/eos_core/eos_core
  ```
  Record the output verbatim in *Completed* — a non-empty lint result is a finding, not something to
  fix inside this item.

### DEBT-9.2 — Baseline the suite, then format
- **Status** `TODO`
- **Scope** every tracked `.py` in `apps/eos_core`.
- **Acceptance criteria**
  - the full suite count is recorded immediately before formatting and immediately after, and they
    are equal;
  - `ruff format --check` is clean afterwards;
  - the 19 tracked `.py` files that lacked a final newline have one — re-derive the list rather than
    trusting the count:
    ```bash
    cd /workspace/development/frappe-bench/apps/eos_core
    for f in $(git ls-files '*.py'); do [ -n "$(tail -c 1 "$f")" ] && echo "$f"; done | wc -l
    ```
  - `vto.py` is tab-indented like every other file, and the 4-space reindent is the **only** semantic
    diff in that file.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  ./env/bin/ruff format --check apps/eos_core/eos_core
  ./env/bin/ruff check apps/eos_core/eos_core
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Then the line-by-line review the item demands:
  ```bash
  cd /workspace/development/frappe-bench/apps/eos_core
  git diff --stat
  git diff -w --stat          # whitespace-ignoring: should be empty for a pure format change
  ```
  **`git diff -w` being empty is the proof this item changed nothing but formatting.** If it is not,
  something was edited by hand and must be reverted.

### DEBT-9.3 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/TODO.md`, and `AGENTS.md` only if the lint baseline revealed something worth
  recording.
- **Acceptance criteria** the item records the `ruff` version and the command to run it, so the next
  session does not re-derive the tooling; `TODO.md` moves `DEBT-9` to *Done* with the SHA.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`DEBT-9.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

- **`ruff` and `pre-commit` are configured but not installed in this bench.** The item's **Done when**
  ("`ruff format` runs clean") presupposes a tool that is not on `PATH`. This is a prerequisite, not a
  blocker, and it belongs in the item's record so the next session does not conclude the item is
  impossible.
- The `pre-commit` config excludes nothing under `eos_core/templates/`, so formatting is consistent
  with how the project already intends to be checked.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All three tasks.
