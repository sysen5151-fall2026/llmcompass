# Milestone 2 demo: F.1.1 Propose Criteria Mapping, carried out by C.1.1 Criteria Mapper

What the demo shows (Milestone 2 item 3): the running product carrying out F.1.1, one step per
second-level IDEF0 box (Form report Figure 4) and flow (Figure 7, SPEC.md §7). Scenario:
**SCENARIO_02** (sample_data/user_inputs.json). It doesn't use SCENARIO_01, whose criteria lean on
AA-Omniscience, which no live source publishes (SPEC §5 Q12).

## Before your turn (about 5 minutes)

1. Open Bionic (LM Studio) → Developer → start the server, with **qwen2.5-7b-instruct** loaded.
   Check it: `curl -s http://127.0.0.1:1234/v1/models` lists `qwen2.5-7b-instruct`.
2. Set `BENCHMARK_SOURCE=api` in `.env` (live snapshot, 14 models). The pull from 2026-11-03 is
   stored; run `cd backend && ../.venv/bin/python -m provide_benchmark_evidence refresh` only if you
   want fresher data.
3. Start the app: `cd backend && ../.venv/bin/python app.py`, then open http://127.0.0.1:5000.
4. In Innoslate, open: the first-level IDEF0 with mechanisms (item 1), the second-level IDEF0 of
   F.1.1 (Figure 4), the function hierarchy and the C.1.1 asset hierarchy (Figures 5–6) (item 2).
5. Warm the model once: submit any one-line requirement and wait for the review page. The first
   call after loading is the slowest (Ch 8 measured 18–36 s cold, 15–27 s warm).

## The run (SCENARIO_02), step by step

| # | What you do / say | Second-level box (mechanism) | Flows | What the audience sees |
|---|---|---|---|---|
| 1 | Paste the SCENARIO_02 text (below) into the form and press Submit. | — (Technical Lead) | **1** Stated requirements → F.1.1.1 | The requirements form |
| 2 | "C.1.1.1 gives the requirement an ID and sends it to the local model." | F.1.1.1 Request Interpretation (C.1.1.1 Interpretation Client) | **2** Interpretation request → LM Studio; **1.0.1** Requirement set → F.1.1.2, F.1.1.4 | Wait about 15–45 s. Optional: Bionic's server log shows the request arriving on localhost |
| 3 | "The model's answer is checked against the model contract and the known metrics list; a bad answer is re-sent once, then marked interpretation_failed." | F.1.1.2 Validate Proposed Criteria (C.1.1.2 Criteria Validator) | **3** Proposed criteria → F.1.1.2; **3.0.1** Validated criteria → F.1.1.3; control Known metrics list | (internal) |
| 4 | Point at the review page: the requirement, each proposed criterion, its **proxy strength** rating and rationale. | F.1.1.3 Present Criteria Mapping (C.1.1.3 Mapping Presenter) | **4** Presented mapping → Technical Lead | The review page (CR 1.2.4, CR 1.4.3) |
| 5 | Review and edit: keep both criteria, leave capability weighted at weight 2 and cost weighted at weight 1, clear any threshold you don't want; optionally add `context_window >= 128000` as hard in the "Add a criterion" row. Press **Confirm mapping**. | — (Technical Lead, UC.1.7–1.9) | **5** Confirmed criteria mapping → F.1.1.4 | Your edits |
| 6 | "C.1.1.4 checks the confirmed mapping against the known metrics list and splits it into the four flows the other subsystems need." | F.1.1.4 Distribute Confirmed Mapping (C.1.1.4 Mapping Distributor) | **5.1** Required metrics → F.1.2; **5.2** Hard constraints → F.1.3; **5.3** Weighted criteria → F.1.4, F.1.5; **5.4** Decision basis → F.1.7 | The result page: confirmed mapping, ranking with contributions, exclusions, sensitivity, evidence with sources and dates, stored record ID |
| 7 | Show it isn't a lookup: Start again, type a requirement you make up on the spot (e.g. "Answers must start streaming in under a second."), Submit. | F.1.1.1 → F.1.1.3 | 1 → 2 → 3 → 3.0.1 → 4 | New criteria from the model (e.g. a latency metric) |
| 8 | (If asked) Show the failure path: stop the Bionic server, submit, and the page shows `interpretation_failed` with a manual-entry row; nothing is made up (SPEC §3). | F.1.1.2 | 3 = null twice | `interpretation_failed` + manual entry |

SCENARIO_02 text:

> We are building a general AI product that needs strong overall capability, but we also need to
> keep operating cost reasonable. Cost matters, but we do not want to sacrifice too much
> capability.

Rehearsal result (2026-11-03, live LM Studio + live snapshot): Qwen proposed
`intelligence_index >= 80` (strong, capability) and `input_price <= 0.01` (moderate, cost);
confirmed as weighted (1, 1), the ranking was claude-sonnet-5-5, gemini-4-argon, claude-haiku-5-5,
deepseek-v4-1-flash-1017, qwen3-8-max, …, and a record was stored. Interpretation took 44 s. The
model's proposal can differ between runs of the same text only if the model or its settings change
(temperature 0, seed 5151).

## Timed walkthroughs (log them while rehearsing)

CR 2.1.1 (review and confirm the mapping in ≤ 10 operator minutes) and SR 2.1.1 (a full comparison
in ≤ 30) are demonstrations. Time the operator's own minutes from Submit to Confirm (mapping review)
and from typing to the result page (full comparison), then add rows to
`docs/validation/walkthroughs.csv` (columns `date,operator,scenario,minutes`):

```
2026-11-xx,<your name>,mapping_review:SCENARIO_02,<minutes>
2026-11-xx,<your name>,full_comparison,<minutes>
```

One `mapping_review:<scenario>` row per sample scenario (SCENARIO_01–04) turns the 16 demonstration
tests green (CR 1.2.4, CR 1.3.6, CR 1.4.3, CR 2.1.1). Log real timings only.
