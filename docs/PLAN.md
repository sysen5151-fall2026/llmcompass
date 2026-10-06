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
| UC.1.2 | `receive_requirements(text)` | llm_compass | typed text | `scenario_id` (exact match on `user_input`); empty/whitespace text raises `ValueError` (SN-TL-01 / 5.1.1.1) |
| UC.1.3 | `submit_requirements(req)` | language_model_runtime (STUB) | `{scenario_id, text}` | `interpreted_requirements` |
| UC.1.4 | return value of UC.1.3 | - | - | - |
| UC.1.6 | `present_mapping_for_review(interp)` | llm_compass | `interpreted_requirements` | passes the mapping through, no new field |
| UC.1.9 | `confirm_mapping(mapping)` | llm_compass | mapping | auto-confirms (the UI has no confirm step), no new field |
| UC.1.10 | `request_model_data(confirmed)` | benchmark_data_sources (STUB) | confirmed mapping | `{models, providers, benchmark}` loaded from the 3 files, not a record field |
| UC.1.11 | return value of UC.1.10 | - | - | - |
| UC.1.16 | `present_sensitivity_finding(data)` | llm_compass | model data + `scenario_id` | `comparison_result` (`candidate_assessment`, `ranking`, `tradeoffs`) |
| UC.1.17 | `select_model(finding)` | llm_compass | finding | `selection_result` (`status`, `recommended_model`, `decision_confidence`, `supporting_evidence`) |
| UC.1.18 | `generate_decision_record(...)` | llm_compass | all sections above | `decision_record` (`summary`, `limitations_and_risks`, `next_action`), then assembles the full output: `scenario_id` + the 4 sections, in file order |

This keeps the function names and pairings already in `backend/`. Each
call/return pair (UC.1.3/1.4 and UC.1.10/1.11) is one function whose return value
is the return message.

The Technical Lead is the receiving participant for UC.1.6, 1.16 and 1.18 but has
no module. Those functions stay in `llm_compass`, the sender, so the UI holds no
logic.

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
- `generate_decision_record` now takes `(interpretation, finding, selection)`,
  not SPEC section 4's single `selection`.
- The new record shape doesn't have SPEC 5.1.3.2's six sections.
  `test_SN_TL_09_5_1_3_2_decision_record_has_all_sections` stays red. This is
  expected per the docs/walking-skeleton.md notes.

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

New functions in `llm_compass` (SPEC section 4): `is_stale`, `rank`, `unstable_pairs`.

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
