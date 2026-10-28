# PLAN

## Walking skeleton for UC.1 with a minimal web UI

Status: implemented 2026-10-06. All 4 scenarios render and match
`expected_outputs.json` exactly.

Call path: docs/walking-skeleton.md. No LLM call and no ranking logic. Each stub
returns its own slice of the matched scenario's expected decision record.

### Inputs (sample_data/)

| File | Used by | Contents |
|---|---|---|
| user_inputs.json | UC.1.2 | `scenario_id` + `user_input` text (4 scenarios) |
| expected_outputs.json | every step that returns a record slice | the expected decision record for each `scenario_id` |
| model_spec.json, providers.json, benchmark.json | UC.1.10 / UC.1.11 | model specs, provider data handling, benchmark scores |

The brief's `requirement_samples.json` is split across `user_inputs.json` and
`expected_outputs.json`, and `models.json` is `model_spec.json`. The plan uses
the names on disk.

### 1. Step mapping

The value passed down the chain is `{scenario_id, text}` plus each step's output.
A stub reads `expected_outputs.json` itself and returns its section for that
`scenario_id`. All 4 scenarios have the same 4 sections, each owned by one step.

| Step | Function | Module | Input | Output (record field) |
|---|---|---|---|---|
| UC.1.2 | `receive_requirements(text)` | provide_llm_selection_decision_support | typed text | `scenario_id` (exact match on `user_input`); empty/whitespace text raises `ValueError` (SN-TL-01 / 5.1.1.1) |
| UC.1.3 | `submit_requirements(req)` | provide_requirement_interpretation (STUB) | `{scenario_id, text}` | `interpreted_requirements` |
| UC.1.4 | return value of UC.1.3 | - | - | - |
| UC.1.6 | `present_mapping_for_review(interp)` | provide_llm_selection_decision_support | `interpreted_requirements` | passes the mapping through, no new field |
| UC.1.9 | `confirm_mapping(mapping)` | provide_llm_selection_decision_support | mapping | auto-confirms (the UI has no confirm step), no new field |
| UC.1.10 | `request_model_data(confirmed)` | provide_benchmark_evidence (STUB) | confirmed mapping | `{models, providers, benchmark}` loaded from the 3 files, not a record field |
| UC.1.11 | return value of UC.1.10 | - | - | - |
| UC.1.16 | `present_sensitivity_finding(data)` | provide_llm_selection_decision_support | model data + `scenario_id` | `comparison_result` (`candidate_assessment`, `ranking`, `tradeoffs`) |
| UC.1.17 | `select_model(finding)` | provide_llm_selection_decision_support | finding | `selection_result` (`status`, `recommended_model`, `decision_confidence`, `supporting_evidence`) |
| UC.1.18 | `generate_decision_record(...)` | provide_llm_selection_decision_support | all sections above | `decision_record` (`summary`, `limitations_and_risks`, `next_action`), then assembles the full output: `scenario_id` + the 4 sections, in file order |

This keeps the function names and pairings already in `backend/`. Each
call/return pair (UC.1.3/1.4 and UC.1.10/1.11) is one function whose return value
is the return message.

The Technical Lead is the receiving participant for UC.1.6, 1.16 and 1.18 but had
no module when this was written. Those functions stay in
`provide_llm_selection_decision_support`, the sender, so the UI holds no logic.
(Since 2026-10-22 the Technical Lead's function F.6 has its own module; see
"Module decomposition from the IDEF0" below.)

### 2. UI files

- `backend/app.py`: a Flask app. `GET /` renders the form. `POST /` runs the 8
  functions in call order (`run_uc1`) and renders the record. If UC.1.2 rejects
  empty text, the `ValueError` message is shown under the form. No other logic.
  Run with `python3 backend/app.py` and open http://127.0.0.1:5000.
- `backend/templates/index.html`: the only page. It has the "LLM Compass" title,
  a textarea and a Submit button. The record is shown below them, one section
  per step. Field names are shown as labels, text lists as bullets, lists of
  objects as tables, and empty/null values as "None". The raw JSON sits in a
  collapsible `<details>`. The rendering is generic, with nothing specific to
  any field. Inline `<style>` uses #000, #888 and #fff only. No JavaScript.
- `backend/requirements.txt`: added `Flask==2.2.2`. The file is UTF-16 with
  CRLF line endings, and that encoding is kept.

### 3. Fields with no clear owner

None. `expected_outputs.json` is grouped into one section per producing step
(see the table above).

### Known test impact

- `receive_requirements` raises `ValueError` on empty text, which is what
  `test_SN_TL_01_5_1_1_1_rejects_empty_requirement` checks.
  `test_SN_TL_01_5_1_1_1_accepts_text_requirement` stays red: text that doesn't
  match a scenario raises `StopIteration`, and the function returns
  `scenario_id`, not `requirement_id`.
- Superseded 2026-10-07: `generate_decision_record` now takes SPEC section 4's
  single `selection` and builds the six 5.1.3.2 sections (see "Decision record
  (UC.1.18)" below).

## Sensitivity analysis (UC.1.16)

Status: implemented 2026-10-07. Traces to SN-TL-05 / 5.1.4.1.

UC.1.16 now computes the ranking and sensitivity finding instead of returning the
canned `comparison_result`. `candidate_assessment` and `tradeoffs` are still canned.

### Changes to the step mapping

| Step | Function | Change |
|---|---|---|
| UC.1.9 | `confirm_mapping(mapping)` | STUB: adds `criteria` (designation + weight) from `sample_data/scenario_criteria.json` (SN-TL-07 / 5.1.6.1) |
| UC.1.10 | `request_model_data(confirmed)` | also returns `candidates` in the SPEC section 2 figure shape, built from the 3 sample files |
| UC.1.16 | `present_sensitivity_finding(data, confirmed, scenario_id)` | computes `ranking`, `excluded`, `sensitivity`, `sensitivity_method`, `ranking_is_stable` |
| UC.1.16 | (same) | also shows `score_breakdown` (each weighted criterion's contribution per ranked model, SN-TL-04 / 5.1.3.1) and `evidence` (every figure used, with source, date and stale flag, SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2) |

New functions in `provide_llm_selection_decision_support` (SPEC section 4): `is_stale`, `rank`, `unstable_pairs`.

### Rules and assumptions

- Hard criteria exclude a candidate that fails them, or that has no data for them
  (`missing_data:<metric>`).
- Weighted criteria are min-max normalized across the remaining candidates.
  `>=` means higher is better, `<=` means lower is better, and `==`/`in` score 1 or 0.
  Missing data scores 0 and is listed in `gaps`. Score = sum of weight x normalized.
  Ties are broken by `model_id`.
- Sensitivity: each weight is multiplied by 0.9 and 1.1, one at a time, with no
  renormalization. Any pair whose relative order changes is reported with the
  variations that flipped it. This is the relative reading of SPEC section 5 Q5,
  and it is what the 5.1.4.1 test assumes. Needs team confirmation.
- The weights in `scenario_criteria.json` are a starting point for the team to
  review. They reproduce the expected rankings for SCENARIO_01 to 03, and no pair
  flips under them. SCENARIO_04 excludes every model on the EU-only constraint.
- `data_residency` comes from `providers.json` `default_data_storage_region`.

## Decision record (UC.1.18)

Status: implemented 2026-10-07. Traces to SN-TL-09 / 5.1.3.2.
`test_SN_TL_09_5_1_3_2_decision_record_has_all_sections` passes.

`generate_decision_record(selection)` now has the SPEC section 4 signature and
returns the six required sections plus the selection:

| Field | Comes from |
|---|---|
| `requirements` | the text typed at UC.1.2 |
| `criteria_mapping` | the confirmed criteria (UC.1.9) |
| `weights` | `criterion_id -> weight` for the weighted criteria |
| `evidence` | every figure used, ranked and excluded models, with `source_id`, `collection_date`, `stale` |
| `ranking` | the computed ranking (empty if every model is excluded) |
| `sensitivity` | method, `ranking_is_stable` (None if nothing was ranked), and each unstable pair with the weight changes that flipped it |
| `selected_model` | UC.1.17's selection, or None (UC alt flow 15a) |
| `excluded` | each excluded model and the constraint that removed it (SN-TL-07 / 5.1.6.3) |

Call path changes:

- UC.1.16 `present_sensitivity_finding(model_data, confirmed, requirements)` now
  takes the UC.1.2 `{scenario_id, text}` so the record can state the requirements,
  and returns `record_inputs` alongside `comparison_result`.
- UC.1.17 `select_model(finding)` (STUB: takes the scenario's expected
  recommendation as the Technical Lead's selection) passes `record_inputs` on with
  `selected_model`.
- `backend/app.py` `run_uc1` assembles the page: one section per step.

Still stubbed: the record's `summary`, `limitations_and_risks` and `next_action`
come from `expected_outputs.json`. Storing, retrieving and exporting the record
(5.1.3.3, 5.1.5.1, SPEC section 5 Q3) are not built.

## Module decomposition from the IDEF0 (Lab Manual 4.4)

Status: signatures only, 2026-10-22. Bodies arrive in Chapter 5, driven by tests.

The model's top-level IDEF0 is the Metafunction diagram (SRD §2.3, Fig. 2): eight
functions, each with exactly one mechanism from the Universe hierarchy. F.1 is not
decomposed yet; the seven-function breakdown in SRD Table 1 is still planned, not
modeled, so it does not drive modules this week. One module per function, named
with the function's verb phrase. The three existing modules were renamed to match
(`llm_compass` -> F.1, `benchmark_data_sources` -> F.7,
`language_model_runtime` -> F.8). `backend/app.py` is the analogue of the kiosk's
`kiosk_service`: it calls the functions in UC.1 order and is not a function on the
IDEF0, so it has no traceability row.

### IDEF0 functions (transcribed from the model: SRD Table 2, Fig. 2, §2.3)

```
F.1 -- Provide LLM Selection Decision Support
  in:      stated_requirements (from F.6), proposed_criteria (from F.8),
           model_data_with_provenance (from F.7), model_selection (from F.6)
  control: confirmed_criteria_mapping (from F.6)
  out:     interpretation_request (to F.8), data_request (to F.7),
           presented_mapping (to F.6), presented_ranking_and_sensitivity (to F.6),
           decision_record (to F.6)
  mechanism: C.1 LLM Compass

F.2 -- Define Application Technical Needs
  out:     application_technical_needs (to F.6)
  mechanism: C.2 Application Developer

F.3 -- Define Budget Constraints
  out:     budget_constraints (to F.6, as control)
  mechanism: C.3 Budget Owner

F.4 -- Define Compliance Constraints
  out:     compliance_constraints (to F.6, as control)
  mechanism: C.4 Compliance Officer

F.5 -- Define Product Needs and Priorities
  out:     product_priorities (to F.6)
  mechanism: C.5 Product Owner

F.6 -- Provide Technical Decision Oversight
  in:      application_technical_needs (from F.2), product_priorities (from F.5),
           presented_mapping (from F.1), presented_ranking_and_sensitivity (from F.1),
           decision_record (from F.1)
  control: budget_constraints (from F.3), compliance_constraints (from F.4)
  out:     stated_requirements (to F.1), confirmed_criteria_mapping (to F.1, as
           control), model_selection (to F.1)
  mechanism: C.6 Technical Lead

F.7 -- Provide Benchmark Evidence
  control: data_request (from F.1)
  out:     model_data_with_provenance (to F.1)
  mechanism: C.7 Benchmark Data Sources

F.8 -- Provide Requirement Interpretation
  control: interpretation_request (from F.1)
  out:     proposed_criteria (to F.1)
  mechanism: C.8 Language model runtime
```

14 arrows, each with one source and one destination function (no tunnels).

### Translation rules (Lab Manual Table F-2)

- Input -> positional parameter. Control -> keyword-only parameter (after `*`).
  Output -> return value. Body -> `raise NotImplementedError`.
- Mechanism -> the module itself, as in the manual's worked example (each module is
  performed by exactly one mechanism). It is named in the module docstring, not
  passed as a parameter. External mechanisms keep a `# STUB: <system name>` line.
- A function whose inputs arrive at different points in UC.1 gets one `def` per
  exchange, as the kiosk splits A1 into `accept_flight_number` and
  `display_status`. Each `def` takes only the ICOMs of that exchange.
- F.1's control exists only after UC.1.9, so it governs the `def`s from that step
  on, not the two before it.
- New `def` names must not collide with the SPEC §4 functions already in a module.
  Those stay as they are: they are tested, and moving their logic under the ICOM
  signatures is Chapter 5 work.

### Signatures

| Function | Module | def | ICOMs | UC.1 step |
|---|---|---|---|---|
| F.1 | provide_llm_selection_decision_support | `request_interpretation(stated_requirements: str) -> dict` | in: stated_requirements; out: interpretation_request | 1.2-1.3 |
| F.1 | (same) | `present_criteria_mapping(proposed_criteria: dict) -> dict` | in: proposed_criteria; out: presented_mapping | 1.4-1.6 |
| F.1 | (same) | `request_benchmark_evidence(*, confirmed_criteria_mapping: list) -> dict` | control: confirmed_criteria_mapping; out: data_request | 1.9-1.10 |
| F.1 | (same) | `present_ranking_and_sensitivity(model_data_with_provenance: list, *, confirmed_criteria_mapping: list) -> dict` | in: model_data_with_provenance; control; out: presented_ranking_and_sensitivity | 1.11-1.16 |
| F.1 | (same) | `record_decision(model_selection: Optional[str], *, confirmed_criteria_mapping: list) -> dict` | in: model_selection; control; out: decision_record | 1.17-1.18 |
| F.2 | define_application_technical_needs | `define_application_technical_needs() -> str` (removed 2026-10-25: no SPEC requirement) | out: application_technical_needs | before 1.2 |
| F.3 | define_budget_constraints | `define_budget_constraints() -> list` (removed 2026-10-25: no SPEC requirement) | out: budget_constraints | before 1.2 |
| F.4 | define_compliance_constraints | `define_compliance_constraints() -> list` (removed 2026-10-25: no SPEC requirement) | out: compliance_constraints | before 1.2 |
| F.5 | define_product_needs_and_priorities | `define_product_needs_and_priorities() -> dict` (removed 2026-10-25: no SPEC requirement) | out: product_priorities | before 1.2 |
| F.6 | provide_technical_decision_oversight | `state_requirements(application_technical_needs: str, *, budget_constraints: list, compliance_constraints: list) -> str` | in; controls; out: stated_requirements | 1.2 |
| F.6 | (same) | `confirm_criteria_mapping(presented_mapping: dict, product_priorities: dict, *, budget_constraints: list, compliance_constraints: list) -> list` | in x2; controls; out: confirmed_criteria_mapping | 1.7-1.9 |
| F.6 | (same) | `choose_model(presented_ranking_and_sensitivity: dict, *, budget_constraints: list, compliance_constraints: list) -> Optional[str]` | in; controls; out: model_selection | 1.17 |
| F.6 | (same) | `keep_decision_record(decision_record: dict) -> None` | in: decision_record; no output on the model | after 1.18 |
| F.7 | provide_benchmark_evidence | `provide_model_data(*, data_request: dict) -> list` | control: data_request; out: model_data_with_provenance | 1.10-1.11 |
| F.8 | provide_requirement_interpretation | `propose_criteria(*, interpretation_request: dict) -> dict` | control: interpretation_request; out: proposed_criteria | 1.3-1.4 |

Types follow SPEC §2 (candidate list with figures), §3 (interpretation request
`{requirement_id, text}` and response) and 5.1.3.2 (decision record).
`model_selection` identifies the chosen model, or is None for UC alt flow 15a.
Today's `select_model` STUB passes the `model_name`. `Optional[str]`, not
`str | None`, so the modules still import on the macOS system Python 3.9.

### Findings to take back to the model (not fixed in code)

- F.6 receives `decision_record` but none of F.6's outputs is made from it. By the
  Table F-2 input test ("if the routine could run without it, it is not an
  input"), it is a terminal arrow: the Technical Lead keeps the record. The
  signature returns None and says so, like the kiosk's `display_status`. The team
  should decide whether F.6 needs an output here (for example, a retrieval
  request for 5.1.5.1), which is already noted as missing in SRD §4.
- F.8's `interpretation_request` is modeled as a control, but by Table F-2 it is
  an input. F.8 transforms the requirement text into the proposed criteria, and it
  cannot run without that text. This is the reverse of the manual's A4 example
  (there, a control was modeled as an input). The SRD's reason, "the service
  produces only what it is asked for", fits F.7 better than F.8: `data_request`
  only selects which stored figures come back. But the independent review
  disagrees: in the kiosk, A2's lookup key (`validated_flight_number`) is an
  input, and F.7 has the same pattern. The team should decide F.7 and F.8
  together.
  Proposed fix in Innoslate: make `interpretation_request` an input to F.8 and
  give F.8 a real control, such as the SPEC §3 response schema, as A3 has in the
  kiosk. Then regenerate `propose_criteria`. Until the model changes, the code
  follows the model as it stands (keyword-only).
- `record_decision` gets only `model_selection` and the control. The other 5.1.3.2
  sections (requirements, evidence, ranking, sensitivity) come from F.1's own
  earlier exchanges, so they are state inside F.1, not arrows. They become
  internal arrows when F.1 is decomposed (SRD Table 1). Today `record_inputs`
  carries them.
- `present_ranking_and_sensitivity` has no `today` arrow, but the 90-day stale
  check (5.1.2.2) needs one. The clock reads as part of mechanism C.1. The
  policies that govern ranking do not: the 90-day stale threshold (SPEC §2,
  5.1.2.2) and the ±10% sensitivity method (SPEC §5 Q5) are "policy, threshold,
  or limit" in Table F-2 terms. They are unmodeled controls, like the kiosk's
  Query Timeout Policy on A2.
- Splitting F.1 into one `def` per exchange exposes a role problem. The confirmed
  criteria mapping is a true control only for ranking. `request_benchmark_evidence`
  has no other ICOM, so the mapping is what it works on. `record_decision`
  copies the mapping and weights into the record, so for that def the mapping is
  content. The F.1 decomposition (SRD Table 1) should give those steps the
  mapping as an input.
- `state_requirements` (F.6) takes budget and compliance constraints as
  controls, but the stated requirements carry them. For example, "Stay under two
  hundred dollars a month…" is one of the reference requirements in
  tests/test_technical_lead.py. By the A4 test ("nothing about it ends up
  inside the output"), they act as inputs for this exchange. The SRD's "hard
  limits" reading holds for confirming the mapping and choosing a model.
- F.2–F.5 have no control arrow, which SRD §2.3 leaves out on purpose. IEEE
  1320.1 expects one control per box. This is informational: it isn't on the
  course's assessment list.
- Fig. 2's "Proposed criteria" label is clipped at the left edge ("osed
  criteria"). That fails the "diagram content is legible" criterion, so move the
  label in Innoslate.
- The existing STUBs `confirm_mapping` and `select_model` in the F.1 module stand
  in for the Technical Lead, so they perform F.6, not F.1. They stay where they are
  this week so the walking skeleton keeps running. In Chapter 5 they move to
  `provide_technical_decision_oversight`.

## Requirement-driven tests and first bodies (Lab Manual 5.3)

Status: done, 2026-10-22. 11 of 14 system requirement tests pass. The other
three are unmet requirements, not code faults: SR 1.2.1 (the catalog has 3 models,
not 10), and SR 1.3.1 and 1.4.1 (no walkthrough logged; the web confirm and select
steps are pending). The full suite gives 83 passed and 18 failed. No test was
changed after it was written: the hashes were checked before and after the bodies.

The model authorizes this increment. It has 14 leaf system requirements
(1.1.1-1.4.1, SRD §3), each with a verification criterion (SRD Table 9), and the
RVTM (SRD Fig. 9). They are copied verbatim into SPEC.md §6. One test per
requirement goes in `tests/test_system_requirements.py`, named
`test_SR_<id>_<what>`. The tests are written from the requirement text first,
by an agent that is not shown the bodies. Bodies are then generated one module
at a time, by different agents, and none of them may edit a test.

### Which defs each requirement exercises

| Requirement | Exercised through | Other function on the arrow |
|---|---|---|
| 1.1.5, 1.2.3 | F.1 `request_interpretation` | F.6 sends, F.8 receives |
| 1.1.4, 1.2.4 | F.1 `present_criteria_mapping` | F.8 sends, F.6 receives |
| 1.1.1, 1.2.1 | F.1 `request_benchmark_evidence` (+ F.7 `provide_model_data` for the catalog) | F.6 sends, F.7 receives |
| 1.1.2, 1.2.5 | F.1 `present_ranking_and_sensitivity` | F.7 sends, F.6 receives |
| 1.1.3, 1.2.2 | F.1 `record_decision` | F.6 sends and receives |
| 1.3.2 | F.1 <-> F.8 conduit: the two F.1 defs above that touch F.8 | |
| 1.3.3 | F.1 <-> F.7 conduit: `provide_model_data` and `present_ranking_and_sensitivity` | |
| 1.3.1 | the web interface (`backend/app.py`, C.1 <-> C.6) | |
| 1.4.1 | all of the above plus a timed walkthrough | |

### Interface details the tests rely on

The Chapter 4 signatures don't change. These details fix what each def returns.

- **F.1 holds the decision in progress.** Its defs are called in UC.1 order, and
  `request_interpretation` starts a new decision. F.1 is still one function on
  the model, with C.1 as its mechanism, so the requirements, mapping, evidence,
  ranking and sensitivity are state inside it, not arrows. This resolves the
  Chapter 4 `record_decision` finding until F.1 is decomposed.
- **`request_interpretation(stated_requirements)`** returns `{"requirement_id":
  str, "text": <unaltered>}`, the SPEC §3 request. It raises `ValueError` on
  empty or whitespace-only text.
- **`present_criteria_mapping(proposed_criteria)`** takes the SPEC §3 response.
  `None` means no response or a timeout, and is handled like an invalid response.
  It returns `{"requirement_id", "requirement": <text>, "status", "no_suitable_proxy",
  "criteria"}`. Each criterion also carries `"requirement"` (the text it stands
  for) and its `proxy_strength`.
  - `status` is `"proposed"` for a valid response.
  - On the first invalid response for a requirement, `status` is `"retry"`, and the
    caller sends the same interpretation request to F.8 again.
  - On the second, `status` is `"interpretation_failed"` with no criteria, and the
    Technical Lead enters criteria by hand (SPEC §3).
  - A valid response has 1+ criteria or `no_suitable_proxy` (not both), and every
    metric is a known one (SPEC §2 field names plus the catalog's benchmark ids,
    SPEC §5 Q7). Every `proxy_strength` is strong, moderate or weak.
- **`request_benchmark_evidence(*, confirmed_criteria_mapping)`** validates every
  criterion first. `designation` must be `hard` or `weighted`, and a weighted
  criterion needs a numeric `weight`, else `ValueError`. It returns the data
  request `{"models": "all", "metrics": [<each criterion's metric>]}`, so every
  candidate in the catalog is requested.
- **`provide_model_data(*, data_request)`** (F.7) returns one SPEC §2 candidate
  for every model in the catalog.
- **`present_ranking_and_sensitivity(model_data_with_provenance, *,
  confirmed_criteria_mapping)`**:
  - It raises `ValueError` if any figure lacks a `source_id` or `collection_date`
    (SPEC §2: rejected at entry).
  - It returns `{"ranking": [model_id], "excluded": [{"model_id",
    "failed_constraints"}], "score_breakdown": [{"model_id", "score",
    "contributions": {criterion_id: value}, "gaps": [metrics with no data]}], "unstable_pairs": [[a, b]],
    "evidence": [{"model_id", "metric", "value", "unit", "source_id",
    "collection_date", "stale"}]}`.
  - Staleness is measured against today's date: the clock belongs to mechanism C.1.
- **`record_decision(model_selection, *, confirmed_criteria_mapping)`** returns
  the record with the seven sections `requirements`, `criteria_mapping`,
  `weights`, `evidence`, `ranking`, `sensitivity` and `selected_model`, plus
  `excluded`.
  - `selected_model` is `model_selection` unchanged.
  - A selection that isn't in the ranking raises `ValueError`.
  - `None` is allowed, for UC alt flow 15a.
- `ValueError` is the project's rejection convention, as in 5.1.1.1 and 5.1.6.1.

### Scope of bodies this increment

- F.1: all five defs. The SPEC §4 helpers they need (`validate_interpretation`,
  `validate_criterion`, and `requirement_id` from `receive_requirements`) come
  with them.
- F.7: `provide_model_data`, from the stored sample catalog. There is no live
  source in increment 1, as in the manual's A2.
- Pending, with rows marked as such in docs/traceability.md:
  - F.8 needs the LM Studio runtime (ADR-0001). Its requirements are verified on
    F.1's side.
  - F.6 is a human mechanism, and its requirements are verified on F.1's
    receiving side.
  - F.2-F.5 have no system requirements: SRD §3.2 says those exchanges don't
    cross the boundary.
  - The web interface's confirm and select steps (1.3.1) are pending, like the
    manual's A1.

### Findings from this increment (to take back to the model or the team)

Requirement text:
- SR 1.2.2 says "six sections" but lists seven, and its MOP says 7 of 7. Its
  parent, 5.1.3.2, has six. Decide whether the selection is a section, then fix
  the model.
- SR 1.3.1 can't be verified as logged. walkthroughs.csv records neither the
  exchanges completed (6 of 6) nor whether any step bypassed the interface. The
  test is green as soon as any `full_comparison` row exists. Add a column, or
  reword the criterion.
- SR 1.4.1: "all leaf-level requirements pass" is checked by the whole CI run,
  not by one test. The CSV has no candidate count, so the test uses the catalog
  size (>= 10) as a stand-in.
- SR 1.3.3: the source can't be made "unavailable" while increment 1 has no live
  source. Only the "last stored figures, dated and flagged" half is tested.
- SR 1.1.2: "every figure received is stored". F.1 stores, and the test checks,
  the figures for the confirmed criteria's metrics: the ones used, as 5.1.2.1
  reads. Confirm that this is the intended reading.

Model (unmodeled controls on F.1, as in the Chapter 4 findings):
- The known-metric vocabulary (SPEC §2 fields plus the catalog's benchmark ids) governs
  `present_criteria_mapping`. F.1 imports it from F.7 (`BENCHMARK_IDS`). It is a
  control, like the kiosk's Model Response Contract on A3.
- The operator/threshold compatibility check, the XOR rule (criteria vs
  no_suitable_proxy) and the requirement_id match rule were added to validation.
  Resolved 2026-10-25: the team kept all three, and SPEC §3 now lists them.

Data:
- SR 1.2.1 and 1.4.1 need at least 10 sourced models in the catalog. sample_data
  has 3. The team enters them, as increment 1's manual entry; they aren't
  generated.

Code, known limits that no requirement covers:
- F.1 keeps one decision in a module-level dict. That suits one local operator,
  but it must become per-session before the web UI calls the ICOM defs.
- `backend/app.py` still runs the walking-skeleton helpers. The ICOM defs are
  tested but not yet on the UI path, and SR 1.3.1 being red covers that.
- Accepted without rule: NaN or negative weights, duplicate model_ids, and a
  missing required SPEC §2 field (ranked with a gap). Each needs a requirement
  before it gets code. An unknown metric in a hand-entered confirmed mapping is
  no longer on this list: SR 1.4.1.1 rejects it (kept by the team, 2026-10-28).
- Text that matches no sample scenario still returns HTTP 500, from the F.8 stub
  (unchanged since before Chapter 4). The `SN_TL_01_5_1_1_2` reference-set tests
  fail inside that stub too, until the real F.8 exists.
- tests/test_walking_skeleton.py still says "CI installs pytest only". The test
  files were frozen for this increment, so the comment was left as is.

### Chapter 4 findings this increment resolves

- `record_decision` state: resolved. F.1 holds the decision in progress, the record
  has all seven sections, and it is checked against the mapping the ranking used
  (SR 1.2.2 passes).
- `today` arrow: resolved as the mechanism's clock (`date.today()`). The 90-day
  threshold is still an unmodeled control.
- F.2-F.6 defs with no SPEC ID: resolved for F.6, which sits at the other end of
  SR 1.1.1, 1.1.3, 1.1.5, 1.2.2, 1.2.4 and 1.2.5. For F.2-F.5 it is explained:
  SRD §3.2 generates no system requirement for them, and docs/traceability.md
  says so.
- Confirmed mapping as content for the data request and the record: confirmed.
  `request_benchmark_evidence` builds the request from the mapping's metrics, and
  `record_decision` copies the mapping. Still a model fix.
- Not resolved (they need Innoslate changes or later chapters):
  - F.8 and F.7 request role (input vs control)
  - budget and compliance constraints in `state_requirements`
  - unmodeled stale and ±10% controls (resolved 2026-10-26: now F.1 controls,
    see "F.1 decomposition")
  - F.6 `decision_record` with no output. Decided 2026-10-26: 5.1.3.3 traces to
    SR 1.4.1.7 Generate and Store Decision Record; the 5.1.5.1 and 5.1.5.2 tests
    are strict xfail until the retrieval/re-run arrow is modeled
    (docs/traceability.md)
  - the clipped Fig. 2 label
  - moving `confirm_mapping` and `select_model` to F.6, which would mean changing
    `test_walking_skeleton.py`'s imports (forbidden this increment); it waits
    for the UI confirm and select steps (SR 1.3.1)

## F.7 live sources (increment 2)

Traces to SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2, SN-TL-08 / 5.3.1.1 (SR 1.2.1,
1.3.3, 1.4.1). Sources are in SPEC §2 (picked 2026-10-23). Only F.7
(`backend/provide_benchmark_evidence/`) changes. `provide_model_data(*,
data_request)` keeps its ICOM signature, so F.1, `app.py` and the tests don't see
where the data came from.

### Catalog (14 models, 10 vendors)

`sample_data/model_sources.json` lists each model's Artificial Analysis id,
models.dev entry and OpenRouter id. Adding a model means editing that file, not
the code. Picked from the live Artificial Analysis list on 2026-10-23 for
coverage:

| Model | Vendor | HQ | Weights | $/1M in / out | Intelligence Index | Price tier |
|---|---|---|---|---|---|---|
| claude-fable-5-1 | Anthropic | US | closed | 10 / 50 | 53.4 | premium |
| claude-sonnet-5-5 | Anthropic | US | closed | 2 / 10 | 56.0 | mid |
| claude-haiku-5-5 | Anthropic | US | closed | 0.10 / 0.50 | 43.4 | budget |
| gpt-6-astra | OpenAI | US | closed | 10 / 50 | 52.7 | premium |
| gpt-oss-120b | OpenAI | US | open | 0.15 / 0.60 | 11.6 | budget |
| gemini-4-argon | Google | US | closed | 2 / 10 | 52.6 | mid |
| gemma-4-26b-a4b | Google | US | open | 0.10 / 0.34 | 16.7 | budget |
| muse-spark-open | Meta | US | open | 1.25 / 4.25 | 38.9 | mid |
| deepseek-v4-1-flash-1017 | DeepSeek | CN | open | 0.30 / 1.20 | 45.1 | budget |
| qwen3-8-max | Alibaba | CN | closed | 2 / 6 | 45.4 | mid |
| kimi-k3 | Moonshot AI | CN | open | 3 / 15 | 43.6 | mid-premium |
| mistral-large-4 | Mistral | FR | closed | 1.36 / 4.18 | 38.4 | mid |
| solar-pro4 | Upstage | KR | closed | 0.30 / 1.20 | 26.6 | budget |
| sarvam-105b | Sarvam | IN | open | 0.04 / 0.17 | 8.8 | budget |

The figures above are a snapshot for the selection only. At run time F.7 reads
them from the sources.

Left out: kimi-k3-1-pro (released 2026-10-23, not on models.dev yet); Cohere
(Artificial Analysis lists $0 prices, i.e. missing); xAI and Z AI (they would
weight the catalog further toward US or China).

### Design

- **Config, not code.** `BENCHMARK_SOURCE` (`file` | `api`, default `file`), the
  source URLs and the keys come from `.env` (python-dotenv). `.env.example` is
  committed, and `.env` is gitignored.
- **`file` mode** is today's behaviour: the stored catalog in `sample_data/`. The
  tests run in this mode.
- **`api` mode**, per catalog model:
  - Artificial Analysis (by id): `input_price`, `output_price`, `latency_p50`
    (`median_time_to_first_token_seconds`), and `benchmarks` (each returned
    evaluation).
  - models.dev (provider + model): `context_window` (`limit.context`). OpenRouter
    `context_length` is used when models.dev has no entry.
  - Manual (`sample_data/providers.json`): `data_residency`, `data_retention`,
    `deprecation_date`.
- **Provenance.** Each figure's `source_id` is the URL it came from, and its
  `collection_date` is the pull date (5.1.2.1). Prices for open-weight models are
  hosting-provider prices, and `source_id` says so.
- **Snapshot and fallback.** Each successful pull is saved under `data/`
  (gitignored). If a source fails, F.7 returns the last snapshot with its dates,
  and staleness is flagged as usual (SPEC §2 "Source unavailable", SR 1.3.3).
  With no snapshot, it returns "no model data available".
- **Attribution.** The UI credits artificialanalysis.ai (free-tier term).
- **Rate limit.** Artificial Analysis allows 1,000 requests a day, and one pull
  is one request. Refresh cadence is still open (SPEC §2).

### Open items

- AA-Omniscience is dropped (SPEC §2), but SCENARIO_01 uses it (SPEC §5 Q12).
  `BENCHMARK_IDS` keeps it until that is decided, so the fixture and its tests
  stay as they are.
- Residency and retention are entered for Anthropic only. The other 9 vendors
  need manual entries with sources. Until then, they're gaps (scored 0 if
  weighted, excluded with `missing_data:<field>` if hard).
- Artificial Analysis evaluation keys (`lcr`, `artificial_analysis_intelligence_index`)
  differ from the stored ids (`aa_lcr_v1_1_percent`, `intelligence_index`). Map
  them in `BENCHMARK_IDS` so the restricted vocabulary (SPEC §5 Q7) stays the same in both modes.

## F.1 decomposition (IDEF0 A1, 2026-10-26)

Source: the team's Innoslate diagrams of 2026-10-26 (F.1 A-0 context, F.1 A1
decomposition, functions-requirements spider diagram). F.1 is decomposed into
the seven functions planned in SRD Table 1. Requirement 1.4.1 is decomposed into
1.4.1.1-1.4.1.7, one per sub-function (SPEC §6). Their statements and
verification criteria aren't exported yet.

### F.1 boundary (A-0)

```
F.1 -- Provide LLM Selection Decision Support
  in:      stated_requirements, proposed_criteria, confirmed_criteria_mapping,
           model_data_with_provenance, model_selection
  control: known_metrics_list, staleness_threshold, sensitivity_policy
  out:     interpretation_request, data_request, presented_mapping,
           presented_ranking_and_sensitivity, decision_record
  mechanism: C.1 LLM Compass
```

Changed from Chapter 4: confirmed_criteria_mapping moved from control to input,
and the three controls are new. These resolve the Chapter 4 findings on the
mapping's role and on the unmodeled stale and ±10% controls.

### A1 (transcribed; arrows entering a box's top are controls)

```
F.1.1 Propose Criteria Mapping
  in:      stated_requirements, proposed_criteria, confirmed_criteria_mapping
  control: known_metrics_list
  out:     interpretation_request, presented_mapping (boundary);
           weighted_criteria (to F.1.4, F.1.5), hard_constraints (to F.1.3),
           required_metrics (to F.1.2)
F.1.2 Retrieve Model Data
  in:      required_metrics, model_data_with_provenance
  control: staleness_threshold
  out:     data_request (boundary), candidate_evidence (to F.1.3)
F.1.3 Apply Hard Constraints
  in:      candidate_evidence
  control: hard_constraints
  out:     eligible_candidates (to F.1.4), exclusions (to F.1.6)
F.1.4 Score and Rank Candidates
  in:      eligible_candidates
  control: weighted_criteria
  out:     ranking (to F.1.5, F.1.6)
F.1.5 Analyze Ranking Sensitivity
  in:      ranking
  control: weighted_criteria, sensitivity_policy
  out:     sensitivity_finding (to F.1.6)
F.1.6 Report Selection Rationale
  in:      ranking, exclusions, sensitivity_finding
  out:     presented_ranking_and_sensitivity (boundary), selection_rationale (to F.1.7)
F.1.7 Generate and Store Decision Record
  in:      selection_rationale, model_selection
  out:     decision_record (boundary)
```

### Done this step (boundary only)

The F.1 ICOM defs follow the new A-0 (Table F-2):
- `confirmed_criteria_mapping` is positional (input) in `request_benchmark_evidence`,
  `present_ranking_and_sensitivity` and `record_decision`.
- The controls are keyword-only, with defaults set to today's policy values:
  - `known_metrics` (`present_criteria_mapping`, `validate_interpretation`), default `KNOWN_METRICS`;
  - `staleness_threshold` (`present_ranking_and_sensitivity`, `is_stale`, `rank`), default 90 days;
  - `sensitivity_policy` (`present_ranking_and_sensitivity`, `unstable_pairs`), default ×0.9 / ×1.1.

The tests still call with keywords, and those calls still work. The suite result
is unchanged.

### Module plan (all seven built, 2026-10-28)

Following the repo rule "one module per IDEF0 function, named with its verb
phrase": each sub-function becomes a module inside
`backend/provide_llm_selection_decision_support/`. The package `__init__` keeps
re-exporting the F.1 boundary defs and the SPEC §4 helpers, so test imports don't
change. Signatures follow Table F-2, with one def per exchange:

| Function | Module | Defs | Moves from |
|---|---|---|---|
| F.1.1 | propose_criteria_mapping | `request_interpretation(stated_requirements)`; `present_criteria_mapping(proposed_criteria, *, known_metrics)`; `split_confirmed_mapping(confirmed_criteria_mapping, *, known_metrics) -> (weighted_criteria, hard_constraints, required_metrics)` | same-named defs, `validate_interpretation`, `validate_criterion` |
| F.1.2 | retrieve_model_data | `request_model_data(required_metrics) -> data_request`; `receive_model_data(model_data_with_provenance, *, staleness_threshold) -> candidate_evidence` | `request_benchmark_evidence`; figure checks and `is_stale` from `present_ranking_and_sensitivity` |
| F.1.3 | apply_hard_constraints | `apply_hard_constraints(candidate_evidence, *, hard_constraints) -> (eligible_candidates, exclusions)` | first half of `rank` |
| F.1.4 | score_and_rank_candidates | `score_and_rank_candidates(eligible_candidates, *, weighted_criteria) -> ranking` | second half of `rank` |
| F.1.5 | analyze_ranking_sensitivity | `analyze_ranking_sensitivity(ranking, *, weighted_criteria, sensitivity_policy) -> sensitivity_finding` | `_flips` (re-scores from each entry's normalized values, so it needs only the ranking) |
| F.1.6 | report_selection_rationale | `report_selection_rationale(ranking, exclusions, sensitivity_finding) -> (presented_ranking_and_sensitivity, selection_rationale)` | rest of `present_ranking_and_sensitivity` |
| F.1.7 | generate_and_store_decision_record | `generate_and_store_decision_record(selection_rationale, model_selection) -> decision_record`; plus `store_decision_record` / `retrieve_decision_record` (SPEC §4, 5.1.3.3) | `record_decision`, `generate_decision_record` |

`rank` and `unstable_pairs` (SPEC §4) stay as thin compositions of F.1.3-F.1.5.
The F.1 boundary defs become compositions of the sub-functions.

Order: F.1.7 first, because 5.1.3.3 is traced to 1.4.1.7 and its test is red.
Then F.1.3/F.1.4 (they split `rank`), F.1.5, F.1.2, F.1.6, F.1.1. Each step keeps
the suite at its current result or better.

As built, beyond the table:
- F.1.1 also holds `_decision`, the decision in progress (mechanism C.1 state).
  `request_interpretation` starts it there, and F.1's boundary defs share it, because a
  sub-function module can't import from the package `__init__`.
- `_metric_figure` (reads a SPEC §2 field or benchmark score) is in F.1.2, and F.1.3/F.1.4
  import it. Data flows F.1.2 -> F.1.3 -> F.1.4, so the imports follow the arrows.
- F.1.3's eligible candidates carry the hard-constraint figures it checked
  (`evidence`). F.1.4 appends the weighted figures, so each ranking entry has every
  figure used. F.1.6 gets only ranking, exclusions and finding, and needs them.
- F.1.4's ranking entries carry `normalized` per criterion, which F.1.5 re-scores from.
- F.1.5's finding has `method` (built from the policy) and `unstable_pairs` in
  ranking order.
- `record_decision` adds requirements, mapping and weights from `_decision` to F.1.6's
  selection rationale before calling F.1.7 (first finding below).

### Findings to take back to the model

- F.1.7 needs the stated requirements and the confirmed mapping and weights for
  the record (SR 1.2.2's sections), but it receives only `selection_rationale`
  and `model_selection`. F.1.6 doesn't receive them either. Either
  `selection_rationale` is defined to carry them, which needs arrows from F.1.1
  into F.1.6 or F.1.7, or they stay as state inside F.1, as today.
- F.1.3's eligible-candidates output has a stray loop drawn at its exit in A1.
  It's cosmetic, but it fails "diagram content is legible".
- The retrieval/re-run request (5.1.5.1, 5.1.5.2) is still not on A-0. Those
  tests stay strict xfail.
- The F.7/F.8 request roles (input vs control) aren't visible in these diagrams.
  Check them in the regenerated Metafunction IDEF0.

### Progress

- 2026-10-26: SPEC §6 has 1.4.1.1-1.4.1.7, derived from the diagrams (the SRD
  export doesn't have them yet), with one test each in
  tests/test_system_requirements.py.
- 2026-10-26: F.1.7 built as `generate_and_store_decision_record.py`. Records are
  JSON files in `DECISION_RECORD_DIR` (default `data/decision_records/`,
  gitignored). `record_decision` now calls it. SR 1.4.1.7 and the 5.1.3.3 test
  pass.
  - Side effect: the 5.1.5.1 not-found test passes too, so its strict xfail fails
    the run. The team decides whether to drop that marker.
- 2026-10-28: team decisions. SR 1.4.1.1's derived rule (a confirmed criterion
  whose metric is off the known metrics list is rejected, because that control
  enters F.1.1) is kept. F.1.3/F.1.4 go next.
- 2026-10-28: F.1.3 built as `apply_hard_constraints.py`, F.1.4 as
  `score_and_rank_candidates.py`. `rank` (SPEC §4) is now their composition, with
  the same output as before. Its stale flagging (`_flag_stale`) stays in F.1's
  `__init__` until F.1.2 is built. The suite result is unchanged.
  - The SR 1.4.1.3 and 1.4.1.4 tests are still red. They get their inputs from
    F.1.1 `split_confirmed_mapping` and F.1.2 `receive_model_data`, which don't
    exist yet. Run with stand-ins for those two defs, both pass.
- 2026-10-28: F.1.5, F.1.2, F.1.6, F.1.1 built, in that order, as
  `analyze_ranking_sensitivity.py`, `retrieve_model_data.py`,
  `report_selection_rationale.py`, `propose_criteria_mapping.py`. The F.1 boundary
  defs now compose F.1.1-F.1.7: `request_benchmark_evidence` is F.1.1 split + F.1.2
  request, `present_ranking_and_sensitivity` is F.1.1 split + F.1.2 receive + F.1.3-F.1.6,
  and `record_decision` is F.1.1 split + F.1.7. `rank`, `_flips` and `unstable_pairs`
  compose F.1.3-F.1.5.
  - Suite (uv, Python 3.12, with `werkzeug<3` so Flask 2.2.2 imports): 87 pass,
    21 fail before; 93 pass, 15 fail after. SR 1.4.1.1-1.4.1.6 now pass, and nothing
    that passed fails. Python 3.9 gives the same result on the system-requirement and
    Technical Lead tests.
  - Behaviour changes at the F.1 boundary:
    - A confirmed criterion with an unknown metric is rejected
      (`request_benchmark_evidence`, `present_ranking_and_sensitivity`,
      `record_decision`), per SR 1.4.1.1.
    - Every received figure gets a stale flag, not only the criteria's figures. A
      figure with an unparseable `collection_date` is rejected.
    - For an excluded candidate, the evidence shows the hard-constraint figures it
      was judged on, no longer its weighted-criterion figures. For a ranked
      candidate, hard-constraint figures come first, then the weighted ones.
    - `rank`'s entries carry `normalized` too.
- Next: the remaining red tests are the data gap (catalog < 10), the walkthroughs,
  the F.8 stub, the 5.2.x Product Owner functions, and the 5.1.5.1 strict-xfail decision.

