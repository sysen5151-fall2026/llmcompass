# Route table — endpoint-to-use-case audit (Lab Manual 6.4)

Audited on 2026-10-28. Every entry point in the application is mapped to the use
case it serves. The assistant enumerated the entry points (prompts/2026-10-28-entry-point-enumeration.md),
and the team did the mapping and decided the dispositions.

The model is from SYSEN5151_ArchitectureDefinitionReport.pdf:
- UC.1 "Technical Lead selects a model for an application" is the only use case.
- Its sequence diagram has 10 numbered interactions (Fig. 6, p13).
- They are traced over the Metafunction IDEF0 (Fig. 7, Table 6, p14-16) and
  carried to the first-level IDEF0 by direct trace (Fig. 8, Table 7, p15-16).
- The trace passes the pencil test, so the 6.4.1 prerequisites are present.

## Entry points

```
GET  /                -- UC.1 (Technical Lead selects a model). Shows the
  requirements form: the start of UC.1.1/UC.1.2. backend/app.py index()
POST /                -- UC.1.2-UC.1.6. Changed 2026-11-03 (Milestone 2 wiring): the
  stated requirements go to C.1.1 (propose_mapping: C.1.1.1 -> F.8 adapter -> LM Studio
  -> C.1.1.2, re-sent once on retry -> C.1.1.3) and the mapping review page is shown
  (backend/templates/review.html). Was: UC.1.2 -> UC.1.18 in one request through
  run_uc1(), which stays as the walking-skeleton path for its tests only.
POST /confirm         -- UC.1.9 Confirm the mapping (with UC.1.7 review/amend and UC.1.8
  weights). Added 2026-11-03. Triggered by the review page's Confirm button. C.1.1.4
  distribute_confirmed_mapping -> F.1.2 -> F.7 -> F.1.3-F.1.6 -> F.1.7 stores the record;
  shows the result page (backend/templates/result.html). SR 1.3.1, CR 1.1.1, CR 1.3.6.
python3 backend/app.py -- UC.1. Starts mechanism C.1's web server, which is how the
  Technical Lead reaches GET /. Was app.run(debug=True). The Werkzeug interactive
  debugger traces to no requirement, so the team turned it off: now app.run().
GET  /static/<filename> -- ORPHAN, deleted. Flask registers it by default. There is
  no backend/static/ folder, so it only ever returned 404, and it traces to no use
  case. The read-only enumeration missed it. The independent verification found it
  in app.url_map. Removed with Flask(__name__, static_folder=None); the page's CSS
  is inline.
python3 -m provide_benchmark_evidence refresh (from backend/) -- UC.1.10/UC.1.11
  (SR 1.2.1, SR 1.3.3). Added 2026-11-03 (Lab Manual 8.5): the operator's on-demand
  pull (SPEC §2 "Refresh"). backend/provide_benchmark_evidence/__main__.py. It stores
  a snapshot; the app serves it when BENCHMARK_SOURCE=api.
```

Found: 4 entry points. 1 was an orphan and was deleted, so 3 remain, all tracing to
UC.1 (2026-10-28). POST /confirm (UC.1.9) and the refresh CLI were added on 2026-11-03.
**Orphans remaining: 0.** `app.url_map` holds `/` and `/confirm`. Neither pass found
any other route, error handler, request hook, `__main__` block, CLI parser, script,
or live call to an external system.

### Not an application entry point

- `.github/workflows/ci.yml`, triggered on push and pull_request, runs `pytest`.
  It is verification tooling (Lab Manual 5.3) and isn't part of the application.
  No actor in the model triggers it, so it is neither mapped nor an orphan.

## UC.1 interactions and the entry points that serve them

Sequence diagram, Fig. 6 (p13). "Step" is the call in `run_uc1`.

| # | Interaction | From -> To | Served by | Status |
|---|---|---|---|---|
| UC.1.2 | Technical Lead enters requirements and constraints | Technical Lead -> LLM Compass | POST / (`propose_mapping` → C.1.1.1 `request_interpretation`) | Implemented |
| UC.1.3 | Submit requirements for interpretation | LLM Compass -> Language model runtime | POST / (C.1.1.1 `send_interpretation_request` -> F.8 adapter) | Implemented (LM Studio, local) |
| UC.1.4 | Interpret requirements and propose criteria | Language model runtime -> LLM Compass | POST / (C.1.1.2 `validate_proposed_criteria`) | Implemented; invalid reply re-sent once, then interpretation_failed |
| UC.1.6 | Present proposed mapping for review | LLM Compass -> Technical Lead | POST / (C.1.1.3 `present_criteria_mapping`, review page) | Implemented |
| UC.1.9 | Confirm the mapping | Technical Lead -> LLM Compass | POST /confirm (C.1.1.4 `distribute_confirmed_mapping`) | Implemented 2026-11-03, with UC.1.7 (keep/remove/edit/add) and UC.1.8 (hard/weighted, weights) |
| UC.1.10 | Request model data | LLM Compass -> Benchmark Data Sources | POST /confirm (F.1.2 `request_model_data` -> F.7 `provide_model_data`) | Implemented (BENCHMARK_SOURCE=api: live snapshot; file: stored catalog) |
| UC.1.11 | Retrieve model specification and benchmark data | Benchmark Data Sources -> LLM Compass | POST /confirm (F.1.2 `receive_model_data`) | Implemented |
| UC.1.16 | Present sensitivity finding | LLM Compass -> Technical Lead | POST /confirm (F.1.3-F.1.6, result page) | Implemented: ranking, contributions, exclusions, unstable pairs, sourced evidence |
| UC.1.17 | Review recommendation and select a model | Technical Lead -> LLM Compass | none: `select_model` takes the scenario's expected recommendation | **Planned** (SR 1.3.1). It needs its own Technical Lead entry point. |
| UC.1.18 | Generate decision record | LLM Compass -> Technical Lead | POST /confirm (F.1.7 `generate_and_store_decision_record`) | Implemented: stored in SQLite, record_id shown; no selection yet (UC.1.17). A mapping with no weighted criterion is rejected (A27, D-23). |

UC.1.1, 1.5, 1.7, 1.8, 1.12-1.15 and 1.19 are on the action diagram (Fig. 5, p12)
but not on the sequence diagram. UC.1.5 and 1.12-1.15 are internal to LLM Compass,
so they need no entry point.

## Use cases and interactions with no entry point

| Item | Model | Disposition (team, 2026-10-28) |
|---|---|---|
| UC.1.9 Confirm the mapping (with 1.7, 1.8) | On the sequence diagram | **Planned.** A confirm step in the web interface, needed by SR 1.3.1 ("6 of 6 UC.1 exchanges"). |
| UC.1.17 Review recommendation and select a model | On the sequence diagram | **Planned.** A select step in the web interface, needed by SR 1.3.1. |
| UC.1.19 Export decision record | Action diagram only. No input/output on either IDEF0 (report p17). | **Planned.** The model needs an output arrow first. No entry point until it has one. |
| Decision reuse: retrieve a stored record and re-run it (5.1.5.1, 5.1.5.2) | No use case (risk R6, report p24) | **Planned.** The team adds a reuse use case to the model before any entry point is built. `retrieve_decision_record` exists (F.1.7) but has no route. The 5.1.5.2 tests stay strict xfail. The 5.1.5.1 not-found test XPASSes under strict, which fails CI; its marker is a pending team decision (docs/PLAN.md). |

## Count reconciliation

| | Model (report) | Application |
|---|---|---|
| Use cases | 1 (UC.1) | 1 (UC.1). Every entry point traces to it. |
| Entry points | n/a | 2026-10-28: 4 found, 1 orphan (/static) deleted. 2026-11-03: 5 (GET /, POST /, POST /confirm, launcher, refresh CLI), all to UC.1. |
| Technical Lead -> LLM Compass interactions | 3 (UC.1.2, 1.9, 1.17) | 2 have an entry point (UC.1.2 POST /, UC.1.9 POST /confirm, 2026-11-03). 1.17 is planned. |
| LLM Compass -> Technical Lead interactions | 3 (UC.1.6, 1.16, 1.18) | 3: UC.1.6 on the review page (POST /), UC.1.16 and 1.18 on the result page (POST /confirm) |
| Interactions with external systems | 4 (UC.1.3, 1.4, 1.10, 1.11) | 4, all real on the web path since 2026-11-03 (F.8 LM Studio, F.7 snapshot or catalog) |
| Entry point -> use case traces | | 5 |

The model and the application agree on use cases (1 = 1) and have no orphans in
either direction. Since 2026-11-03 one Technical Lead action is still without an entry
point: UC.1.17 (select a model), recorded as planned. SR 1.3.1 also needs a logged
walkthrough, so it stays red until both are done.

## Other findings from the enumeration

These are not entry points, and nothing here was changed in this audit.

- **Input that matches no sample scenario returns HTTP 500.** The F.8 stub raises
  `StopIteration` (`provide_requirement_interpretation/__init__.py:15`). This was
  already known (docs/PLAN.md), and the real F.8 replaces it.
- **The result page showed a "Raw JSON" block** (old `index.html`). Removed 2026-11-03 with
  the walking-skeleton record view; the result page now lists the record ID.
- **The F.1 ICOM defs are reached only from tests.** Those defs are
  `request_benchmark_evidence`, `present_ranking_and_sensitivity` and
  `record_decision`, and F.1.1-F.1.7 through them. F.7's `provide_model_data` is
  in the same position. The web route still runs the
  walking-skeleton helpers. SR 1.3.1 covers this.
- **Some stubs are called by nothing.** These are
  `provide_requirement_interpretation.propose_criteria` (F.8) and
  `provide_technical_decision_oversight.state_requirements`,
  `confirm_criteria_mapping`, `choose_model` and `keep_decision_record` (F.6). They
  stand in for external systems (`# STUB`), so they aren't application entry points.
- **The tests leave stored records behind.** Three tests store records without setting
  `DECISION_RECORD_DIR`, so the records collect in the gitignored
  `data/decision_records/`, more on every run:
  - SR 1.1.3 and SR 1.2.2 (through `record_decision`)
  - SN-TL-06 5.1.3.3 (`store_decision_record`, tests/test_technical_lead.py:154)

  Only the SR 1.4.1.7 test redirects to `tmp_path`.

  Resolved 2026-10-28: an autouse fixture in tests/conftest.py sends every test's
  records to `tmp_path`, and the 197 test records were deleted. All of them were
  test fixtures (model-1/2/3, model-b/c/d).

## Findings to take back to the model

- Add an output arrow for UC.1.19 Export decision record, or remove the action.
- Add a decision-reuse use case for 5.1.5.1 and 5.1.5.2.
- Rename UC.1.16 to "Present ranking and sensitivity finding" (report p16), so the
  interaction matches the output it carries.

## Milestone 2 wiring (2026-11-03)

POST / now starts F.1.1 live and POST /confirm is the UC.1.9 entry point. `app.url_map` holds `/`
and `/confirm`. Typed text that matches no sample scenario no longer returns HTTP 500 on the web
path (it went through the F.8 stub before). UC.1.17 (select a model) is still planned: records are
stored with no selection (A22).
