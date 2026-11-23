# R4 fallback: test results and live check (Lab Manual 12.3, 2026-11-22)

This is the evidence for report Section 4.5.3 (Table 21). It traces to SR 1.4.1.8, R4.M1 and
ADR-0010.

## Table 21 results

| # | Input (stated requirement or condition) | Path tested | Test(s) in `tests/test_risk_r4_fallback.py` | Result |
|---|---|---|---|---|
| T1 | Names a model that is in the index but not in the catalog ("GPT-6.2 Sol") | Failure | `test_T1_model_in_index_not_in_catalog_is_flagged_with_alternatives_in_page_and_record` | Pass |
| T2 | Names only catalog models, by display name and by model_id | Normal | `test_T2_only_catalog_models_named_nothing_flagged_and_ranking_unchanged` | Pass |
| T3 | The same missing model with different capital letters, spaces, hyphens, dots and underscores (5 variants), and named three ways in one text | Adversarial | `test_T3_same_missing_model_in_any_case_spacing_or_hyphens_is_flagged` (x5), `test_T3_same_missing_model_named_several_ways_is_flagged_once` | Pass (6) |
| T4 | One catalog model and one missing model; a catalog name that is a prefix of the missing one ("GPT-6 Astra" / "GPT-6.2 Sol") | Mixed | `test_T4_one_catalog_and_one_missing_model_only_the_missing_one_is_flagged`, `test_T4_catalog_name_that_prefixes_a_missing_name_does_not_hide_it` | Pass (2) |
| T5 | A model in neither the catalog nor the index ("Gemini 9 Ultra"); ordinary numbers ("within 3 seconds") | Failure | `test_T5_model_in_neither_catalog_nor_index_is_flagged_not_recognised`, `test_T5_numbers_in_ordinary_requirements_are_not_flagged` | Pass (2) |
| T6 | The known-models index does not exist; F.1.6 called with no report | Failure | `test_T6_no_known_models_list_states_the_check_could_not_run`, `test_T6_rationale_built_without_a_report_says_could_not_run` | Pass (2) |
| T7 | A missing model inside a hard-constraint sentence ("Data may not leave the United States, so Grok 6 ...") | Adversarial | `test_T7_missing_model_inside_a_hard_constraint_sentence_is_flagged_and_constraint_still_applies` | Pass |
| T8 | A decision record from a flagged run is reopened after a restart (module reload) | Failure | `test_T8_reopened_decision_record_still_lists_the_missing_models` | Pass |

Supporting tests, all passing:
- `test_refresh_stores_every_listed_model_as_known_models_and_reports_catalog_gap` and
  `test_no_stored_known_models_list_is_none`: step 1 of the fallback, the F.7 known-models list.
- `test_result_page_shows_requested_but_not_compared_box`: step 3, the box on the result page.
- `tests/test_system_requirements.py::test_SR_1_4_1_8_named_non_catalog_models_reported_in_presented_ranking_and_record`:
  the SR 1.4.1.8 verification criterion.

**Adversarial inputs (Lab Manual 12.3.3).** The assistant was given the contract
(`checkRequestedModels`, A34-A37) and the check, and asked for inputs that would defeat
them:
- spelling variants of a missing name
- a catalog name that is a prefix of a missing name
- a missing name inside a hard-constraint sentence
- the same name repeated
- version-like numbers in ordinary requirements
- no stored index
- a reopened record

Each input became a test above. All 20 tests failed before the fallback was built and pass
after it.

## Full suite

| Run | Passed | Failed | xfailed |
|---|---|---|---|
| Before (this environment, same commit as `origin/main` 9179e8c) | 287 | 16 | 2 |
| After | 307 | 16 | 2 |

The 16 failures are the same tests before and after, so there are no regressions. The 20 new
tests account for the +20. Khai's 11.2 run reported 12 pre-existing failures. The 4 extra
here are `test_SN_TL_01_5_1_1_2_reference_set_has_criterion_or_no_proxy[0-3]`, which need a
live LM Studio runtime that wasn't running in this environment.

Contract checks:
- `contracts/generate_stubs.py --check`: stubs match v1.2.0.
- `contracts/check_conformance.py`: conforms, 15 operations.

## Live check against real data (2026-11-23 04:34 UTC)

`python3 -m provide_benchmark_evidence refresh` result:
- status ok; 14 catalog candidates; 765 known models stored.
- **Catalog gap: 16** of the top-20 listed models (variants counted once) are not in the
  catalog: Claude Fable 5.2, GPT-6.2 Astra, Gemini 4 Neon, Gemini 4 Carbon, Claude Opus 5.5,
  GPT-6.2 Sol, GPT-6.1 Sol, Gemini 4 Hydrogen, GPT-6.1 Terra, Muse Wonder Full, Kimi K3.1 Pro,
  Claude Opus 5, GPT-6 Sol, Muse Wonder, Qwen4 Max, Muse Spark 1.3.

That is the first reading of the Table 18 indicator. Its threshold is "more than 0: add the
models (action 4)".

The check on the real catalog and the stored list:

| Stated requirement | Flagged | Reason | Suggestions |
|---|---|---|---|
| "We want GPT-6.2 Sol or Claude Opus 5.5 for summaries." | GPT-6.2 Sol | not_in_catalog | GPT-6 Astra (Max), gpt-oss-120b (High) |
| | Claude Opus 5.5 | not_in_catalog | Claude Sonnet 5.5 (Max, Default Fallback), Claude Fable 5.1 (Max, Default Fallback), Claude Haiku 5.5 (Max) |
| "Compare gpt-6-astra and Claude Haiku 5.5, data stays in the US." | nothing | — | — |
| "Is Gemini 9 Ultra cheaper than Kimi K3?" | Gemini 9 Ultra | not_recognised | Gemini 4 Argon (High), Gemma 4 26B A4B (Reasoning) |
| "Respond within 3 seconds at 5000 requests per day under 200 dollars." | nothing | — | — |

Kimi K3 is a catalog model and was correctly not flagged.

**Found during the live check:** the local `.env` sets `ARTIFICIAL_ANALYSIS_API_URL` to the
endpoint retired on 2026-11-04 (`/api/v2/data/llms/models`, HTTP 410). The refresh fails
until that line is removed, so the default free-tier endpoint is used (ADR-0007). The run
above unset it for the command only.

## R4 re-rating input for the team

With the fallback in place, a missing model is reported with alternatives instead of being
dropped silently. That supports the planned re-rating of R4's technical impact from 4 to 2
(L4 x I2 = 8). The catalog gap of 16 supports keeping the likelihood at 4 until R4.M2 adds
the missing top-20 models.
