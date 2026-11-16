# Lab 10.4 measured runs: context

- Runs: 30 measured + 1 warm-up (warm-up excluded from statistics). Target: 30.
- Date (UTC): 2026-11-16T04:30:47.092228+00:00 to 2026-11-16T04:48:59.333919+00:00
- Language model: qwen2.5-7b-instruct-1m (LM Studio, GGUF Q4_K_M, lmstudio-community Qwen2.5-7B-Instruct-1M), local endpoint http://127.0.0.1:1234/v1. Team setup in docs/deployment.md is qwen2.5-7b-instruct Q4_K_S.
- Machine: Apple M2 Pro, 16 GB RAM, macOS 27.0, Python 3.12.14.
- App version: commit 0e3f0d1b70a8cc8a5815b5ada35b3ce1705bde59 plus uncommitted: backend/provide_llm_selection_decision_support/propose_criteria_mapping/__init__.py, contracts/api-v1.yaml, docs/PLAN.md, docs/deviation-log.md, tests/test_component_criteria_mapper_reconcile.py (includes the D-29 criterion-id fix, ADR-0008).
- Scenario: 5 stated requirements, the sentences of sample SCENARIO_03 and SCENARIO_04 verbatim (sample_data/user_inputs.json), same text every run. Technical Lead accepts the review page defaults.
- Benchmark data: BENCHMARK_SOURCE=api, read from the stored snapshot /Users/kuankhaixin/sysen5151/llmcompass/data/benchmark_snapshots.sqlite3 (pulled 2026-11-10T20:48:52.007851+00:00), not the live source: F.7 in api mode serves the last pull between refreshes (SPEC section 2 'Refresh').

## Observations

- Interpretation (UC.1.4, 5 requests per run): median 39.61 s, min 26.4 s, max 45.5 s per run (simulated N(90, 25)).
- Retries: 0 requirement(s) re-sent after an invalid reply; timeouts/errors: 0.
- Warm-up run interpretation: 39.7 s (model already loaded in LM Studio before the run, so no load delay was measured).
- Before measuring, the smoke run found Confirm failing with HTTP 422 on multi-line requirements (criterion ids repeated across requirements, deviation log D-29); fixed before the 30 runs (ADR-0008).

## Proof of instrumentation

- Timers: `tools/measure_uc1.py` wraps every sequence-diagram boundary (UC.1.3-UC.1.18, C.1<->C.8, C.1<->C.7, C.1->Technical Lead) with entry/exit `perf_counter_ns` timestamps; product code unchanged.
- Run command: `LLM_MODEL=qwen2.5-7b-instruct-1m .venv/bin/python tools/measure_uc1.py --runs 30 --warmup 1`
- Raw data: `runs.csv` (one row per stage call), `runs_meta.json`; derived: `per_run.csv`, `interpretation_log.csv` (this script: `tools/export_submission.py`).
