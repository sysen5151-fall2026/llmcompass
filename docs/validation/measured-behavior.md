# 6. Measured Behavior Comparison (Lab Manual 10.4)

Modeling report Section 6 for LLM Compass, UC.1 Technical Lead selects a model for an application.
Raw data, tables and plots are in `docs/validation/measured-behavior/`. Traces to SR 1.3.2 (MOP:
interpretation response time per requirement), SR 2.1.1 and CR 2.1.1, the requirements that
Modeling report Section 5.2 traced the simulation to.

## 6.1 Product Instrumentation and Measured Runs

**What the model authorizes (10.4.1).** Everything the manual requires was already in the Innoslate
model:
- the functional simulation of UC.1 (Monte Carlo, 100 runs, mean 16.84 min; Discrete Event, 10 runs);
- the alternative UC.1A (hosted runtime), simulated for comparison;
- the timelines (Gantt charts).

No resources were modelled, so there was no utilisation to compare.

**Instrumentation.** `tools/measure_uc1.py` times every participant boundary of the UC.1 sequence
diagram (Section 3):
- It drives the real web path in-process: POST / with the stated requirements, the review page, then
  POST /confirm.
- It wraps each callable at a boundary at run time and records entry and exit with
  `time.perf_counter_ns`.
- Product code is not changed, so the code that was measured is the code that ships.

Table 6-1 maps each simulated action to what was timed. The harness also records each request's whole
wall time. The wrapped stages cover at least 99.94% of it in every run, so almost no system time falls
outside the timed stages. The Flask test client calls the app in-process, so browser-to-server
transport (HTTP, socket, page rendering in the browser) is not included; on one local machine it is
expected to be small, but it was not measured.

Table 6-1. Sequence-diagram boundaries and what was timed

| Action (Table X) | Boundary (message) | Timed callable |
|---|---|---|
| UC.1.3 Submit requirements | C.1, before msg 2 | C.1.1.1 `request_interpretation` |
| UC.1.4 Interpret requirements | msgs 2-3, C.1 <-> C.8 | C.1.1.1 `send_interpretation_request` (one call per requirement) |
| UC.1.5 Assign confidence | C.1 | C.1.1.2 `validate_proposed_criteria` |
| UC.1.6 Present mapping | msg 4, C.1 -> Technical Lead | C.1.1.3 `present_criteria_mapping` + review page render |
| UC.1.7-1.9 Review, weight, confirm | msgs 4-5 | not timed: the harness accepts the defaults (see below) |
| UC.1.10 Request model data | msg 6, C.1 -> C.7 | F.1.2 `request_model_data` |
| UC.1.11 Retrieve data | msgs 6-7, C.1 <-> C.7 | F.7 `provide_model_data` |
| UC.1.12 Exclude | C.1 | F.1.3 `apply_hard_constraints` |
| UC.1.13 Score and rank | C.1 | F.1.4 `score_and_rank_candidates` |
| UC.1.14 Sensitivity | C.1 | F.1.5 `analyze_ranking_sensitivity` |
| UC.1.15-1.16 Present ranking and finding | msg 8, C.1 -> Technical Lead | F.1.6 `report_selection_rationale` + result page render |
| UC.1.18 Generate decision record | msg 10, C.1 -> Technical Lead | F.1.7 `generate_and_store_decision_record` |
| (not modelled) | C.1 | C.1.1.4 `distribute_confirmed_mapping`; F.1.2 `receive_model_data` |
| UC.1.1-1.2 Initiate, enter requirements | msg 1, Technical Lead -> C.1 | not timed: human step (the harness posts the text directly) |
| UC.1.17 Select a model; UC.1.19 Export | msg 9 | not timed: UC.1.17 is not implemented yet (contract A22); export is a human step |

**Runs.** The same scenario was run 30 times, plus 1 warm-up that is excluded from the statistics.

| Item | Setting |
|---|---|
| Date | 2026-11-16, 04:30-04:49 UTC |
| Requirements | 5 stated requirements, inside the model's assumption of 5 to 8: the sentences of sample SCENARIO_03 and SCENARIO_04, verbatim (a high-volume customer assistant handling EU data) |
| Runtime | LM Studio on 127.0.0.1:1234, qwen2.5-7b-instruct-1m (GGUF Q4_K_M), temperature 0, max_tokens 512. The team's documented setup is qwen2.5-7b-instruct Q4_K_S. |
| Machine | Apple M2 Pro, 16 GB |
| Data | api mode, the stored snapshot of 2026-11-10 (14 models) |
| Code | commit 0e3f0d1, plus the criterion-id fix described below |
| Command | `LLM_MODEL=qwen2.5-7b-instruct-1m .venv/bin/python tools/measure_uc1.py --runs 30 --warmup 1` |

Results of the 30 runs:
- All 30 returned HTTP 200 on both requests and stored a decision record.
- 150 interpretation requests, all valid on the first attempt: no re-sends, no timeouts.
- All 31 runs (warm-up included) produced the identical confirmed mapping, checked by hashing the
  stored records.

Files: `runs.csv` (one row per timed call), `per_run.csv` (one row per run),
`interpretation_log.csv` (one row per interpretation request), `runs_meta.json`, `CONTEXT.md`.

**Human steps.** The harness accepts the review page's defaults, so it measures system and external
time only. The Technical Lead's steps (UC.1.7-1.9) are compared with the timed walkthroughs in
`docs/validation/walkthroughs.csv`. That is a separate sample of 4, recorded to the nearest minute,
one per sample scenario (SCENARIO_01-04), not the 5-line scenario measured here.

**A defect found before the runs.** The first instrumented smoke run failed at Confirm with HTTP 422:

- **Cause.** Each interpretation reply numbers its own criteria. The prompt asks for ids "unique
  within this response", so REQ-1, REQ-3 and REQ-4 all returned `CRI-1`. C.1.1.4 rejects a confirmed
  mapping that repeats an id (D-13).
- **Effect.** Any comparison in which two replies used the same id failed at Confirm. This is likely,
  because each reply numbers from 1; in the smoke run REQ-1, REQ-3 and REQ-4 collided while REQ-2
  used `C1`. The demo and the tests used one line or distinct ids, so they never hit it.
- **Fix, before the 30 runs.** Ids are now qualified by their requirement (`REQ-3:CRI-1`):
  ADR-0008, deviation log D-29, regression test
  `test_propose_mapping_criterion_ids_unique_across_requirements`.

The simulation could not have shown this defect: it models only the main success path
(Section 5.3).

## 6.2 Measured vs Simulated Comparison

Table 6-2. Simulated duration and measured distribution per stage (seconds per run, n = 30)

| Stage | Simulated (Table X) | Measured mean (SD) | Median [min-max] | Measured / simulated |
|---|---|---|---|---|
| UC.1.3 Submit | N(0.5, 0.1) | 0.00002 (0.00002) | 0.00001 [0.000006-0.0001] | 0.00004 |
| **UC.1.4 Interpret (5 requests)** | **N(90, 25)** | **35.05 (7.26)** | **39.61 [26.42-45.50]** | **0.39** |
| UC.1.5 Validate | N(0.2, 0.05) | 0.0019 (0.0012) | 0.0016 [0.0003-0.0056] | 0.010 |
| UC.1.6 Present mapping | N(1, 0.2) | 0.0037 (0.0020) | 0.0032 [0.0008-0.0089] | 0.004 |
| UC.1.10 Request data | N(0.5, 0.1) | 0.000002 | 0.000002 [0.000001-0.000007] | 0.000004 |
| UC.1.11 Retrieve data | Exp(mean 2) | 0.0054 (0.0046) | 0.0039 [0.0016-0.0242] | 0.003 |
| UC.1.12 Exclude | N(0.2, 0.05) | 0.00004 | 0.00004 [0.00003-0.00009] | 0.0002 |
| UC.1.13 Score and rank | N(0.3, 0.05) | 0.00003 | 0.00002 [0.00002-0.0001] | 0.0001 |
| UC.1.14 Sensitivity | N(0.5, 0.1) | 0.00003 | 0.00002 [0.00002-0.00009] | 0.00005 |
| UC.1.15-16 Present ranking | N(1, 0.2) + N(0.5, 0.1) | 0.0007 (0.0005) | 0.0005 [0.0003-0.0033] | 0.0004 |
| UC.1.18 Decision record | N(0.5, 0.1) | 0.0028 (0.0023) | 0.0021 [0.0012-0.0115] | 0.006 |
| C.1.1.4, F.1.2 receive (not modelled) | - | 0.0008 | - | - |
| **System total** | **97.2 (SD 25.1)** | **35.07 (7.27)** | **39.62 [26.43-45.52]** | **0.36** |
| Human UC.1.7-1.9 (walkthroughs, n = 4) | N(375, 67) | 60 (0) | 60 [60-60] | 0.16 |

Table 6-3. UC.1.4 interpretation response time per requirement (SR 1.3.2 MOP; 150 requests)

| Requirement | Output tokens (probe) | Mean (s) | Runs 1-16 (battery) | Runs 17-30 (mains) | Max (s) |
|---|---|---|---|---|---|
| REQ-1 high-volume customer assistant | 301 | 13.66 | 16.20 | 10.76 | 18.07 |
| REQ-2 cost low, respond quickly | 185 | 8.50 | 10.10 | 6.68 | 11.15 |
| REQ-3 handles EU customer data | 122 | 5.60 | 6.59 | 4.47 | 6.99 |
| REQ-4 stored and processed only in the EU | 121 | 5.68 | 6.82 | 4.37 | 7.70 |
| REQ-5 non-negotiable | 32 | 1.61 | 1.92 | 1.26 | 2.19 |
| All requests | - | 7.01 (p95 16.0) | - | - | 18.07 |

Table 6-4. End-to-end time for one comparison (SR 2.1.1, budget 30 min)

| | Mean (min) | SD (min) |
|---|---|---|
| Hybrid: measured system time + Table X Technical Lead estimates (905 s) | 15.67 | 1.69 |
| UC.1 baseline, Monte Carlo | 16.84 | 1.74 |
| UC.1A hosted runtime, Monte Carlo | 15.42 | 1.76 |

Figures:
- `stage_comparison.png`: every stage, measured box plot against the simulated mean ± 1 SD, on a log
  axis.
- `interpretation_vs_simulated.png`: the 30 per-run UC.1.4 totals against the simulated N(90, 25).
- `interpretation_per_requirement.png`: UC.1.4 per request, by requirement.

Full statistics, including p95 and the warm-up run, are in `measured-behavior/comparison.md`, which
`tools/compare_measured_simulated.py` generates.

## 6.3 Divergence Explanation and Decision

The measured system time is about a third of the simulated time (35 s against 97 s). Almost all of
the difference is in UC.1.4. The measured distribution also has two clusters where the model
expected one bell curve. Each divergence below is followed by the check behind it.

**1. Interpretation is 2.6 times faster than modelled, and its time is set by how much the model
writes.**
- **Explanation.** The 90 s estimate assumed about 15-20 s per requirement, varying with the length
  of the requirements. Measured requests ranged from 1.1 s to 18.1 s, with a mean of 7.0 s.
- **Check: a direct probe of LM Studio** (`measured-behavior/token_probe.txt`): 15 requests, 3 per
  requirement, with the adapter's exact request body (temperature 0, seed 5151, strict JSON schema),
  sent at 05:07 UTC after the measured runs, on mains power:
  - Time fits 0.18 s + 0.0342 s per output token, r = 0.998, about 29 tokens per second.
  - The prompt length barely changes (456-465 tokens), so prompt processing is not what varies.
  - Output length is fixed per requirement at temperature 0. REQ-1 writes 301 tokens (three
    criteria); REQ-5 writes 32 (no suitable proxy).
- **The check predicts the measurement.** For the five requirements (761 tokens), the fit predicts
  26.9 s per comparison, and runs 17-30 (also on mains power) measured 27.5 s.
- **What the model got wrong.** It tied the variation to the length of the requirements. The
  measurement shows it follows the length of the reply, that is, how many criteria a requirement
  produces, while the prompt length barely changes. A requirement with no proxy (REQ-5) costs about
  1.6 s; one with three criteria (REQ-1) costs 8-9 times more.
- **Earlier figures.** The 15-20 s figure came from an earlier setup (SPEC section 3, 2026-11-03,
  "MacBook", LM Studio): 15.0-36.3 s per call, one call per whole sample scenario, 93-165 output
  tokens, which is a decode rate of roughly 6 tokens per second against about 29 here. The setup
  differs (model build, machine), so the two sets are not directly comparable.

**2. The two clusters in UC.1.4 come from the laptop's power state, not from LLM Compass.**
- **What was measured.** Runs 1-16 averaged 41.6 s (SD 1.6); runs 17-30 averaged 27.5 s (SD 0.8).
- **Check: the macOS power log** (`pmset -g log`). The Mac ran on battery from 21:34 and switched to
  mains power at 23:42:34 EST (04:42:34 UTC). Run 17 started at 04:42:33.5 UTC.
- **Check: the model's output did not change.** All 31 stored mappings are identical.
- **Check: every requirement slowed down by the same factor.** The ratio is 0.64-0.68 for each
  requirement, which a change in output length would not produce.
- **Check: the power settings** (`pmset -g custom`). Low Power Mode is enabled in the battery profile
  and disabled on mains power. So runs 1-16 very probably ran in Low Power Mode, which is the likely
  mechanism. This is the current setting; macOS does not log its history, so it is not proven for the
  time of the runs.
- **Meaning.** Within one power state the variation is tiny (SD under 2 s). The simulated SD of 25 s
  does not describe a random spread around one mean; the real spread comes from discrete
  conditions: power state, and which requirements are entered.

**3. LLM Compass's own processing was modelled as seconds; it takes milliseconds.**
- **Explanation.** The ten LLM Compass actions and the data retrieval together take 0.02 s per run
  (max 0.04 s), against 7.2 s simulated (5.2 s for the actions, 2 s for the retrieval).
- **Check: the per-stage timings** (Table 6-2). Each stage is in-memory Python over 14 candidates.
- **Consequence.** The conclusion of Sections 5.1 and 5.4 stands, and is stronger: LLM Compass's
  processing is negligible, under 0.1% of a comparison.

**4. Data retrieval (UC.1.11) was modelled as a call to a web service; in the built system it is a
local database read.**
- **Measured.** 5.4 ms on average, against an exponential with mean 2 s.
- **Check: the code.** In api mode, F.7 `provide_model_data` serves the last stored pull from SQLite
  (`_latest_snapshot`, SPEC section 2 "Refresh"). The live pull from Artificial Analysis runs
  separately, when the data is refreshed (`python -m provide_benchmark_evidence refresh`).
- **What this means for the model.** The model's assumption ("waits on an external web service")
  describes the refresh, which is not on the UC.1 path at all. This is a stage the simulation timed
  that the architecture had moved off the critical path.

**5. The human steps cannot be compared yet.**
- **The data.** The 4 logged mapping-review walkthroughs are recorded as 1 minute each, to the
  nearest minute. The simulation assumed 6.25 minutes.
- **Check: the walkthrough log.** It has 4 rows, all from one operator, at 1-minute resolution. That
  is too small and too coarse to estimate a distribution, so these figures are not used to change
  UC.1.7-1.9.

**6. The effect on the end-to-end result is small.**
- Replacing the simulated system time with the measured one gives 15.67 minutes, against 16.84 in
  the Monte Carlo (Table 6-4).
- Human time is still about 96% of a comparison.
- SR 2.1.1 (30 minutes) and CR 2.1.1 (10 minutes) are still met with a wide margin. This rests on
  the human estimates, which are still unmeasured.

### Decision

| Option (10.4.2) | Decision | Reason |
|---|---|---|
| Update simulation parameters | **Yes, for UC.1.4; also UC.1.11 and the LLM Compass software actions, for fidelity** | UC.1.4 is outside the simulated mean ± 2 SD and matters to the total. UC.1.11 is inside its wide band and the software actions are far below theirs, but neither affects the total; they are updated so the model describes the built system |
| Change the architecture | **No change for performance.** One code change already made: the criterion-id fix (ADR-0008) | Nothing measured breaks an SR or CR target. The fix corrects a defect, not performance |
| Neither | **For the human steps (UC.1.7-1.9)** | No usable measurement yet |

Proposed parameter changes for Innoslate, for the team to confirm:
- **UC.1.4.**
  - Replace N(90, 25) with the measured value for the power state being modelled: N(27.5, 1) per
    comparison of these five requirements on mains power, or N(41.6, 2) on battery in Low Power Mode.
    A single wide Normal would hide that the spread comes from two conditions.
  - Note the rule behind it, for other requirement sets: about 0.2 s plus 0.034 s per output token on
    mains power, about 1.5 times that on battery.
  - UC.1A.4 (hosted) stays at N(15, 5), so the hosted runtime now saves about 12-27 s per comparison
    instead of 75 s.
  - This strengthens Section 5.4's conclusion to keep the local runtime: speed is even less of a
    reason to switch.
- **UC.1.11.** Replace Exp(mean 2) with a constant 0.01 s, and record that the live pull is a
  separate refresh activity, not part of UC.1.
- **LLM Compass actions** (UC.1.3, 1.5, 1.6, 1.10, 1.12-1.16, 1.18). Replace each with 0.01 s.
  They are measured in milliseconds.

**Open items for the team:**
- **Set SR 1.3.2's target.** "Interpretation response time per requirement" was left "to be set
  after the local runtime is benchmarked". The data is now available: mean 7.0 s, p95 16.0 s, max
  18.1 s on this machine. The 110 s timeout is about 6 times the slowest request. The target itself
  is the team's decision.
- **Time the human steps.** Run full comparisons by people, with minutes recorded to at least 0.1,
  for SR 2.1.1 and CR 2.1.1. This is the only way to test the 90% share the simulation gives the
  Technical Lead.
- **Re-run on the team's documented model** (qwen2.5-7b-instruct Q4_K_S) on mains power, if the
  report should match the deployment view exactly.
