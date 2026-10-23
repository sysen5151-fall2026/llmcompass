# F.1 and F.7 first bodies — filled Component Prompt Templates (Lab Manual 5.3, step 2)

Each prompt went to a separate implementation agent. Neither agent wrote the tests,
and neither may change a test. If a test fails, the agent reports whether the test
or the requirement is wrong instead of making the test pass.

## Shared

- **Constraints.**
  - Python 3.9 and 3.12, standard library only. No network calls, no new
    dependencies.
  - Edit only your module's `__init__.py`. Nothing in tests/, docs/, SPEC.md or
    other modules changes.
  - Existing functions keep their behaviour: the walking skeleton and the 29
    tests that pass today must still pass.
  - Cite the SR and StR IDs in comments in the file's existing style, e.g.
    `# SR 1.1.5, SN-TL-01 / 5.1.1.1`.
  - Update each def's docstring with a first line like the manual's
    `"""Function: A2 -- ... Signature from Chapter 4; body added this increment."""`,
    keeping the ICOM line.
- **Out of scope.**
  - No retries inside a def: the caller re-sends on `status == "retry"`.
  - No logging, caching, persistence, extra error handling, or features that no
    requirement asks for.
  - No changes to signatures (they are fixed in Chapter 4).
  - No refactoring of unrelated code.
- **Interfaces.** docs/PLAN.md "Interface details the tests rely on" is the
  contract. SPEC §2 and §3 are the data and model contracts.

## Prompt A — F.7 Provide Benchmark Evidence

- **Context.** F.7's mechanism is C.7 Benchmark Data Sources. Increment 1 is
  manual entry: the stored catalog is `sample_data/`. There is no live source, as
  in the manual's A2 "small in-memory table".
- **Component.** `provide_benchmark_evidence.provide_model_data`
- **Function performed.** F.7 -- Provide Benchmark Evidence
- **Requirements.** SR 1.2.1 (catalog side), SR 1.3.3, SR 1.4.1 (catalog side),
  SN-TL-02 / 5.1.2.1. The text is in SPEC §6.
- **Interfaces.** `provide_model_data(*, data_request: dict) -> list`. The request
  is `{"models": "all" | [model_id], "metrics": [...]}`. The result is one SPEC
  §2 candidate per requested model, every figure with source and date. Reuse the
  existing `_to_candidates`.
- **Success criteria.** `test_SR_1_3_3_*` passes. `test_SR_1_2_1_*` and
  `test_SR_1_4_1_*` may stay red only because the stored catalog has 3 models
  (fewer than 10) or no walkthrough is logged. Don't pad the catalog.
- **Output format.** The edited file.

## Prompt B — F.1 Provide LLM Selection Decision Support

- **Context.** F.1 is the system function, and its mechanism is C.1 LLM Compass.
  Its five ICOM defs from Chapter 4 now get bodies. F.1 holds the decision in
  progress, and `request_interpretation` starts a new one (docs/PLAN.md).
- **Component.** `provide_llm_selection_decision_support`: `request_interpretation`,
  `present_criteria_mapping`, `request_benchmark_evidence`,
  `present_ranking_and_sensitivity`, `record_decision`. Also the SPEC §4 helpers
  these need:
  - `validate_interpretation(response) -> bool` (5.1.1.2, 5.1.1.3)
  - `validate_criterion(criterion)`, which raises ValueError (5.1.6.1)
  - `receive_requirements(text)` gains `requirement_id` via
    `request_interpretation`. It keeps `scenario_id` (None when the text matches no
    sample scenario) so the walking skeleton still works (5.1.1.1).
- **Function performed.** F.1 -- Provide LLM Selection Decision Support
- **Requirements.** SR 1.1.1-1.1.5, SR 1.2.2-1.2.5, SR 1.3.2, SR 1.3.3 (ranking
  side), and the F.1 side of SR 1.2.1. The text is in SPEC §6, and each has a
  `test_SR_*` in tests/test_system_requirements.py.
- **Interfaces.**
  - Signatures are fixed in Chapter 4. Return shapes are in docs/PLAN.md.
  - "Known metrics" means the SPEC §2 figure field names plus the catalog's
    benchmark ids (SPEC §5 Q7). Take the ids from F.7's published vocabulary
    (`provide_benchmark_evidence.BENCHMARK_IDS`) rather than copying them. This
    vocabulary is an unmodeled control on F.1 and is reported as a finding.
  - Operators are `>=`, `<=`, `==` and `in` (SPEC §3).
  - Ranking and sensitivity reuse `rank`, `_flips` and `is_stale`, with today's
    date. The record reuses `generate_decision_record`.
- **Success criteria.**
  - Every `test_SR_*` for these requirements passes. The exceptions are the
    data-gap and walkthrough tests (1.2.1, 1.3.1, 1.4.1).
  - The SPEC §4 tests for 5.1.1.1 (accepts text), 5.1.1.2 (rejects neither),
    5.1.1.3 and 5.1.6.1 pass.
  - All tests that passed before still pass.
- **Output format.** The edited file.
