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
  requirements form: the start of UC.1.1/UC.1.2. backend/app.py:47 index()
POST /                -- UC.1. Runs UC.1.2 -> UC.1.18 in one request through
  run_uc1() (backend/app.py:27) and shows the decision record. Triggered by the
  form and its Submit button (backend/templates/index.html:29-32).
python3 backend/app.py -- UC.1. Starts mechanism C.1's web server, which is how the
  Technical Lead reaches GET /. Was app.run(debug=True). The Werkzeug interactive
  debugger traces to no requirement, so the team turned it off: now app.run().
GET  /static/<filename> -- ORPHAN, deleted. Flask registers it by default. There is
  no backend/static/ folder, so it only ever returned 404, and it traces to no use
  case. The read-only enumeration missed it. The independent verification found it
  in app.url_map. Removed with Flask(__name__, static_folder=None); the page's CSS
  is inline.
```

Found: 4 entry points. 1 was an orphan and was deleted, so 3 remain, all tracing to
UC.1. **Orphans remaining: 0.** `app.url_map` now holds only `/`. Neither pass found
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
| UC.1.2 | Technical Lead enters requirements and constraints | Technical Lead -> LLM Compass | POST / (`receive_requirements`) | Implemented |
| UC.1.3 | Submit requirements for interpretation | LLM Compass -> Language model runtime | POST / (`submit_requirements`) | STUB: Language model runtime (F.8) |
| UC.1.4 | Interpret requirements and propose criteria | Language model runtime -> LLM Compass | POST / (`submit_requirements`) | STUB: Language model runtime (F.8) |
| UC.1.6 | Present proposed mapping for review | LLM Compass -> Technical Lead | POST / (`present_mapping_for_review`) | Shown on the result page, not as a separate review step |
| UC.1.9 | Confirm the mapping | Technical Lead -> LLM Compass | none: `confirm_mapping` reads `sample_data/scenario_criteria.json` | **Planned** (SR 1.3.1). It needs its own Technical Lead entry point. UC.1.7 (review/amend) and UC.1.8 (assign weights) belong to the same step. |
| UC.1.10 | Request model data | LLM Compass -> Benchmark Data Sources | POST / (`request_model_data`, F.7) | STUB: Benchmark Data Sources (stored catalog) |
| UC.1.11 | Retrieve model specification and benchmark data | Benchmark Data Sources -> LLM Compass | POST / (`request_model_data`, F.7) | STUB: Benchmark Data Sources (stored catalog) |
| UC.1.16 | Present sensitivity finding | LLM Compass -> Technical Lead | POST / (`present_sensitivity_finding`) | Partial. Ranking and sensitivity are computed; candidate assessment and tradeoffs are still the scenario's expected output. |
| UC.1.17 | Review recommendation and select a model | Technical Lead -> LLM Compass | none: `select_model` takes the scenario's expected recommendation | **Planned** (SR 1.3.1). It needs its own Technical Lead entry point. |
| UC.1.18 | Generate decision record | LLM Compass -> Technical Lead | POST / (`generate_decision_record`) | Partial. The six sections are built and shown, the narrative is a STUB, and the web path doesn't store the record (F.1.7 isn't on the UI path yet). |

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
| Entry points | n/a | 4 found. 1 orphan (/static) deleted, 3 remain (GET /, POST /, launcher), all to UC.1. |
| Technical Lead -> LLM Compass interactions | 3 (UC.1.2, 1.9, 1.17) | 1 has an entry point (UC.1.2). 1.9 and 1.17 are stubs inside POST /: planned. |
| LLM Compass -> Technical Lead interactions | 3 (UC.1.6, 1.16, 1.18) | 3, all on the POST / result page |
| Interactions with external systems | 4 (UC.1.3, 1.4, 1.10, 1.11) | 4, all stubs (F.8, F.7) |
| Entry point -> use case traces | | 3 |

The model and the application agree on use cases (1 = 1) and have no orphans in
either direction. They disagree on one thing: the application compresses UC.1 into a
single request, so two of the three Technical Lead actions have no entry point yet.
That gap is recorded as planned, and SR 1.3.1 stays red until it closes.

## Other findings from the enumeration

These are not entry points, and nothing here was changed in this audit.

- **Input that matches no sample scenario returns HTTP 500.** The F.8 stub raises
  `StopIteration` (`provide_requirement_interpretation/__init__.py:15`). This was
  already known (docs/PLAN.md), and the real F.8 replaces it.
- **The result page shows a "Raw JSON" block** (`index.html:68-71`). It is the same
  decision record as UC.1.18, in a different form. It isn't an entry point.
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

## Findings to take back to the model

- Add an output arrow for UC.1.19 Export decision record, or remove the action.
- Add a decision-reuse use case for 5.1.5.1 and 5.1.5.2.
- Rename UC.1.16 to "Present ranking and sensitivity finding" (report p16), so the
  interaction matches the output it carries.
