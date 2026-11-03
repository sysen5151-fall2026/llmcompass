# ADR-0005: SQLite for local storage

Status: Accepted (team, 2026-11-03)

Context: Lab Manual 8.5 asks for a database schema built from the data contract
(SPEC §2). ADR-0001 picked PostgreSQL on Supabase, with SQLite as the rejected
alternative. Since then:
- the product runs only on a team laptop, because the local runtime can't be reached
  from a hosted app (Form report §2.3, ADR-0001 revisit condition)
- CI has no database or credentials
- decision records were stored as JSON files under `data/`

What needs storing: pulled model-data snapshots for C.7 (SR 1.3.3, which falls back
to the last snapshot), and decision records for C.1.7 Decision Recorder (SR 1.4.1.7,
SR 2.1.4, StR 5.1.3.3).

Decision: use SQLite through Python's standard library `sqlite3`. There is one file
per owning function, so each store stays inside its own module:
- `data/benchmark_snapshots.sqlite3`, F.7 (schema
  `backend/provide_benchmark_evidence/snapshot_schema.sql`)
- `$DECISION_RECORD_DIR/decision_records.sqlite3`, F.1.7 (schema
  `backend/provide_llm_selection_decision_support/decision_record_schema.sql`)

Rationale:
- It needs no account, no service, no credentials and no new dependency.
- It works the same on a laptop, in tests (a temporary directory per test) and in CI.
- It keeps all data on the machine, which fits the data-security default.
- The schema puts the SPEC §2 rules (`source_id` and `collection_date` required) in
  the database as well as in code.

Consequences:
- No shared or remote store, so each team machine has its own records.
- SR 2.1.4's six-month retention depends on the file not being deleted. Nothing in
  the product deletes records.
- The model's storage element (Form report Table 7, row 2) changes from Option 1
  to Option 2. That needs updating in Innoslate.

What would change this decision: deploying the app (Netlify) or sharing decision
records across the team needs a hosted store, in which case Supabase PostgreSQL as
in ADR-0001 comes back. The schema files are plain SQL and port with minor type
changes. Revisit at the Week 12 trade study together with the runtime choice.
