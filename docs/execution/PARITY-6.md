# PARITY-6 — Connectors (Jira, Salesforce, Google Sheets)

## Parent TODO

`PARITY-6` — **S3** · Connectors (Jira, Salesforce, Google Sheets).
Block D (Ninety parity features with no representation at all).

**Scope** (verbatim from `TODO.md`): via Webhook / ServerScript. Do not start before `PERM-2` —
connector credentials are a permission surface.

**Done when** (verbatim): a written design exists naming which Ninety connector behaviour is in
scope, and the first connector works end to end for one provider.

## Objective

A written design that names exactly which of Ninety's connector behaviour this app is matching, a
credential store that is permission-gated and stores secrets encrypted, and one provider working end
to end from an external event to a change in the app.

## Dependencies

- `PERM-2` (closed) — the DocPerm blocks are the basis for gating the credential store. **This item
  was explicitly gated on it and is now unblocked.**
- `PERM-6` (closed) — a connector's writes are writes by some user; the team-scoping layer decides
  which team's data a connector may touch. This is the part that is easy to get wrong.
- Independent of every UI item.
- Note: Frappe core's `Data Import` has a `google_sheets_url` field, so the Google Sheets route may be
  materially shorter than the other two. See *Decision 2*.

## Decisions to settle before implementing

1. **Which Ninety connector behaviour is in scope — this is part of the deliverable, not a
   prerequisite.** Ninety's connectors push *external* activity into a Measurable, a Rock or a To-Do.
   Decide the direction (inbound only, or both), the objects, and what happens on a failed or
   duplicate event. Write it down before coding; the item's **Done when** requires the design to
   exist.
2. **Pick the first provider on evidence, not on preference.** Google Sheets is plausibly the
   shortest path because Frappe's own `Data Import` already accepts a `google_sheets_url` and
   `refresh_google_sheet`; Jira has the best public API documentation; Salesforce needs credentials
   and an org instance URL before anything else. **Record why the chosen one was chosen.**
3. **Credentials are secrets and the `Password` fieldtype is the storage answer.** Frappe encrypts
   `Password` fields via `frappe.utils.password.encrypt` / `get_decrypted_password`
   (`frappe/utils/password.py:23,189`). Store tokens as `Password` fields on a credential DocType —
   never as `Data` or `Code` fields, and never in `hooks.py`, a settings Single or a DocType JSON.
4. **The connector acts as a user, and that user must be chosen explicitly.** A background job or a
   webhook has no session. Whichever user the connector runs as must hold a real role and real seats,
   or every write it makes is either refused or — worse — made with `ignore_permissions` and escapes
   the team scoping entirely. **Decide and record this; it is the security core of the item.**
5. **Webhook endpoints are public surface.** A connector endpoint is reachable without a session, so
   it must verify a signature or a shared secret, and must not be implemented as a whitelisted method
   with no check of its own.

## Execution Tasks

### PARITY-6.1 — The written design
- **Status** `TODO`
- **Scope** a new `docs/architecture.md` subsection: direction, objects, event model, idempotency,
  the acting user, the failure path, which Ninety behaviour is matched and which is not, and why the
  first provider was chosen. No code.
- **Acceptance criteria** the design is specific enough to implement from; it names its own
  assumptions and the Ninety pages they came from; the acting-user question is answered, not deferred.
- **Verification** read back by someone who did not write it.

### PARITY-6.2 — Credential store
- **Status** `TODO`
- **Scope** a new DocType for connector credentials with `Password` fields, its DocPerm block, and
  its `has_permission` entry in `eos_core/permissions.py` if it is team-scoped. Tests in
  `test_permissions.py`.
- **Acceptance criteria**
  - secrets are stored in `Password` fields and are unreadable in a list view, in `frappe.get_all`,
    and in the DocType JSON;
  - a `Team Member` and an `Observer` cannot create or read credentials; Manager and above can, for a
    team they are in;
  - the `DOCPERM_MATRIX` test is extended for the new block, not bypassed;
  - the token is never logged and never included in an error message.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost migrate
  bench --site resolv.localhost run-tests --module eos_core.test_permissions --site resolv.localhost
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  Plus a direct check that the stored value is ciphertext:
  ```bash
  cat > /tmp/q.py <<'EOF'
  print(frappe.db.sql("select name, api_token from `tabConnector Credential`"))
  EOF
  bench --site resolv.localhost console < /tmp/q.py
  ```

### PARITY-6.3 — The first provider, end to end
- **Status** `TODO`
- **Scope** the endpoint and the handler for the provider chosen in `PARITY-6.1`.
- **Acceptance criteria**
  - an inbound event creates or updates the app-side object exactly as the design says;
  - the endpoint verifies a signature or shared secret and rejects an unsigned call, with a test;
  - the write runs as the user from *Decision 4* and passes the team scoping layer — a connector
    cannot write outside its teams, proven by a test;
  - a duplicate event is idempotent, and a malformed event fails with a message that does not leak the
    secret;
  - the whole path works from the real provider, not only from a test double — record what was
    actually done.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```
  plus the recorded end-to-end run against the real provider.

### PARITY-6.4 — Close-out and documentation
- **Status** `TODO`
- **Scope** `docs/architecture.md`, `AGENTS.md`, `docs/TODO.md`.
- **Acceptance criteria** the docs state the acting-user rule, which Ninety behaviour is matched, and
  which providers are **not** built; `TODO.md` moves `PARITY-6` to *Done* with the SHA, or records
  which providers remain if the item is closed as a partial.
- **Verification**
  ```bash
  cd /workspace/development/frappe-bench
  bench --site resolv.localhost run-tests --app eos_core --site resolv.localhost
  ```

## Current Task

`PARITY-6.1`. Nothing has been implemented; no task has been started.

## Completed

None.

## Decisions

None made yet.

## Discovered Issues

None yet. The `Data Import.google_sheets_url` route is noted in *Decision 2*; if it turns out to
cover the Google Sheets connector with no app code, that is a finding for `PARITY-6.1`, not a silent
deletion of the item.

## Verification

- Baseline before any change: `bench --site resolv.localhost run-tests --app eos_core` → **248/248**.
- To be filled per task.

## Completion

Pending.

## Remaining Work

All four tasks.
