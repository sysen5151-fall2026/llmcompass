# Milestone 2 demo: F.1.1 Propose Criteria Mapping, carried out by C.1.1 Criteria Mapper

Milestone 2 item 3: the running product carrying out F.1.1, one step per second-level IDEF0 box
(Form report Figure 4) and flow (Figure 7, SPEC.md §7). Three prompts, rehearsed live on
2026-11-03 (LM Studio, Qwen2.5 7B Instruct; live Artificial Analysis snapshot, 14 models). The
model's proposals can vary slightly between runs, so check the review page before you confirm; the
data-side results below (who is ranked, who is excluded) are fixed by the snapshot.

## Before your turn (about 5 minutes)

1. Bionic (LM Studio) → Developer → start the server with **qwen2.5-7b-instruct** loaded.
   Check: `curl -s http://127.0.0.1:1234/v1/models` lists `qwen2.5-7b-instruct`.
2. `.env` has `BENCHMARK_SOURCE=api` (live snapshot, 14 models). Refresh only if you want newer data:
   `cd backend && ../.venv/bin/python -m provide_benchmark_evidence refresh`.
3. Start the app: `cd backend && ../.venv/bin/python app.py` → http://127.0.0.1:5000. If an older
   server is still running, stop it first (Ctrl+C in its terminal).
4. Innoslate tabs: first-level IDEF0 with mechanisms (demo item 1); second-level IDEF0 of F.1.1
   (Figure 4), function hierarchy, C.1.1 asset hierarchy (Figures 5–6) (demo item 2).
5. Run **Prompt A** once all the way to the result page (warm-up). The first call after the model
   loads is the slowest (up to ~36 s); later calls take ~15–45 s per requirement line.
6. Backup: screenshots of each result page from the rehearsal, in case LM Studio fails live.

## How each run maps to the second-level IDEF0

| What happens | Box (mechanism) | Flows |
|---|---|---|
| You type the requirement and press **Submit** | — (Technical Lead) | **1** Stated requirements → F.1.1.1 |
| It gets an ID (REQ-1, one per line) and goes to the local model | F.1.1.1 Request Interpretation (C.1.1.1 Interpretation Client) | **2** Interpretation request → LM Studio; **1.0.1** Requirement set → F.1.1.2, F.1.1.4 |
| The reply is checked against the model contract and the known metrics list | F.1.1.2 Validate Proposed Criteria (C.1.1.2 Criteria Validator) | **3** Proposed criteria; **3.0.1** Validated criteria → F.1.1.3; control: Known metrics list |
| The review page: each criterion with its proxy-strength rating and rationale | F.1.1.3 Present Criteria Mapping (C.1.1.3 Mapping Presenter) | **4** Presented mapping → Technical Lead |
| You keep / edit / remove / add, set hard or weighted and weights, press **Confirm mapping** | — (Technical Lead, UC.1.7–1.9) | **5** Confirmed criteria mapping → F.1.1.4 |
| The result page: confirmed mapping, ranking, exclusions, sensitivity, evidence, record ID | F.1.1.4 Distribute Confirmed Mapping (C.1.1.4 Mapping Distributor) | **5.1** Required metrics → F.1.2; **5.2** Hard constraints → F.1.3; **5.3** Weighted criteria → F.1.4, F.1.5; **5.4** Decision basis → F.1.7 |

## What to explain while it runs

**The model proposes, the Technical Lead decides** (CR 1.2.4 "must review each proposed criterion
before it is used"; CR 1.4.3 "stays in control of how requirements become criteria"). On the
review page the Technical Lead is responsible for:
- **Checking every threshold and unit.** The model often gets units wrong ("%" on an index, "USD per
  ticket" on a price that is per 1M tokens). A wrong threshold on a hard criterion can exclude
  every model.
- **Hard or weighted.** Only `compliance` criteria start as hard; everything else starts weighted
  with weight 1. Turning a "must" into a hard constraint is the Technical Lead's call (UC.1.8).
  - **Hard** = a gate (F.1.3): a model that fails it, *or has no figure for it*, is excluded and
    listed with the reason (`CRI-1` or `missing_data:<metric>`).
  - **Weighted** = an order (F.1.4): the threshold is not a cut-off; `>=` means higher is better,
    `<=` lower is better; a missing figure scores 0 and is shown in "Missing data".
- **Weights** say what matters most (e.g. quality 3, cost 1). Sensitivity (F.1.5) then shows which
  pairs of models would swap under a ±10% change of one weight.
- **Removing** criteria that don't fit (untick Keep) and **adding** ones the model missed (the "Add
  a criterion" row, from the known metrics list only). The review page can't change a proposed
  criterion's operator: untick it and re-add it the right way round.
- Checking the **Confirmed mapping** table at the top of the result page: it shows what was
  actually sent (hard/weighted, weights, thresholds).

**Error handling (SPEC §3, CR 1.4.2, CR 2.3.1):**
- Every model reply is checked: right requirement ID, known metric names only, valid operator,
  threshold that fits the operator, rating and category from the allowed lists. A bad or missing
  reply is **re-sent once**; a second failure marks the requirement **interpretation_failed** and
  offers manual entry. **No criteria are ever made up.**
- On Confirm, C.1.1.4 checks the confirmed mapping again: an unknown metric, a weighted criterion
  without a weight, or a non-number weight brings the review page back with an error box.
- Empty input is rejected on the form (SR 1.1.5).
- Interpretation only goes to a **local** runtime: a non-local runtime address is refused before
  anything is sent (CR 2.2.1, SR 2.2.1), so no project data leaves the laptop and there are no paid
  per-query charges (CR 2.4.1).

**Evidence:** every figure on the result page has a source and a date; the record is stored
(SQLite) with the requirements, mapping, weights, evidence, ranking and sensitivity.

## Prompt A — warm-up and hard vs weighted

> We need a model to classify support tickets. It must respond within 2 seconds.

**Review page (rehearsal):** one criterion, `latency_p50 <= 2 seconds`, **strong**, capability,
default **weighted**.

**Technical Lead does:**
1. Set `latency_p50` to **hard** ("must respond within 2 seconds" is a gate).
2. Add a criterion: `input_price`, `<=`, threshold blank, **weighted**, weight 1 (so there is an
   order and a stored record).
3. Check the latency dropdown still says hard, then **Confirm mapping** once.

**Result page — expect:**
- **Ranked (7):** the models measured at ≤ 2 s, cheapest first — sarvam-105b, gemma-4-26b-a4b,
  gpt-oss-120b, deepseek-v4-1-flash-1017, solar-pro4, muse-spark-open, qwen3-8-max.
- **Excluded (7):** claude-fable-5-1, claude-sonnet-5-5, claude-haiku-5-5, gpt-6-astra,
  gemini-4-argon (`CRI-1`: over 2 s — reasoning models' time to first token includes thinking);
  kimi-k3, mistral-large-4 (`missing_data:latency_p50`).
- A **Record ID**.

**Explain:** the hard criterion decides who is in; the weighted one decides the order. Left weighted
(the default), all 14 would be ranked and the slow models would only lose points — that is the
difference the Technical Lead controls.

Don't confirm with *only* hard criteria: you still get a ranking, but the record shows "Not stored"
(a known open issue, deviation log D-23).

## Prompt B — wrong units: why the review step exists

> We need a model to classify customer support tickets. It must be at least 90% accurate, respond within 2 seconds, and cost under one cent per ticket.

**Review page (rehearsal):** three criteria, all default **weighted**:
- `intelligence_index >= 90` "%" (strong, capability) — it's an index, not a %; the highest model
  in the data is 56.9.
- `time_to_first_answer_token_seconds <= 2` (strong, capability) — the fastest model is 9.98 s.
- `input_price <= 0.01` "USD per ticket" (moderate, cost) — the real unit is USD per 1M input
  tokens; the cheapest is 0.042.

**Explain first:** as proposed, making any of these hard would exclude every model. The model
mapped "accurate" to a general capability index and guessed units. Weighted, the thresholds are
not cut-offs, so confirming as is would still give a sensible ranking of all 14.

**Technical Lead does:**
1. `intelligence_index`: threshold **45**, **hard** (a realistic capability floor).
2. `time_to_first_answer_token_seconds`: keep **weighted**.
3. `input_price`: clear the threshold, keep **weighted**.
4. **Confirm mapping.**

**Result page — expect:**
- **Ranked (4):** gemini-4-argon, claude-sonnet-5-5, claude-fable-5-1, gpt-6-astra — the four with
  an index of 45 or more (50.4, 54.5, 49.2, 56.9), ordered by speed and price, not by the index.
- **Excluded (10):** 5 below 45 (claude-haiku-5-5, qwen3-8-max, deepseek-v4-1-flash-1017,
  mistral-large-4, muse-spark-open) and 5 with no index (`missing_data:intelligence_index`:
  gemma-4-26b-a4b, gpt-oss-120b, kimi-k3, sarvam-105b, solar-pro4).
- A **Record ID**.

## Prompt C — hard constraint plus weights, and the budget conversion

> We're building an assistant that summarizes 20-page internal engineering documents. Customer data must stay in an approved US region. Budget is under $200 a month at 5,000 requests a day. Summary quality matters most; speed matters less.

**Review page (rehearsal):**
- `data_residency in US` (strong, compliance) — default **hard**. ✅ correct.
- `input_price <= 0.4` and `output_price <= 0.1` (moderate, cost) — thresholds wrong.
- `time_to_first_answer_token_seconds >= 5` (weak, capability) — **wrong direction**: `>=` would
  reward slower models.
- **No quality criterion**, although "summary quality matters most".

**The budget conversion (the Technical Lead's assumption, say it out loud):**
5,000 requests/day × 30 = 150,000 requests/month; a 20-page document ≈ 13,000 input tokens and a
summary ≈ 500 output tokens → ≈ 1,950 M input and 75 M output tokens a month. Budget:
1,950 × input_price + 75 × output_price ≤ $200, so **input_price ≤ about 0.10 USD per 1M tokens**.

**Technical Lead does:**
1. Keep `data_residency in US` **hard**.
2. `input_price`: threshold **0.1**, **weighted**, weight 1.
3. `output_price`: clear the threshold, **weighted**, weight 1.
4. Untick `time_to_first_answer_token_seconds` ("speed matters less"; its operator is backwards and
   can't be edited here).
5. Add a criterion: `intelligence_index`, `>=`, threshold blank, **weighted**, weight **3**
   ("quality matters most").
6. **Confirm mapping.**

**Result page — expect:**
- **Ranked (3):** claude-sonnet-5-5, claude-fable-5-1, claude-haiku-5-5 — the only US-resident
  models in the data. With quality weighted 3, sonnet (54.5) wins despite costing about 20× haiku
  (input 0.10).
- **Sensitivity:** claude-fable-5-1 / claude-haiku-5-5 can swap under a ±10% weight change — a
  close call the Technical Lead should look at.
- **Excluded (11):** 5 in another region — sarvam-105b (IN), deepseek-v4-1-flash-1017 (CN),
  mistral-large-4 (EU), qwen3-8-max and kimi-k3 (SG); 6 with no residency figure
  (`missing_data:data_residency`: gemma-4-26b-a4b, gpt-oss-120b, solar-pro4, muse-spark-open,
  gemini-4-argon, gpt-6-astra).
- A **Record ID**.

**Explain:** a missing residency figure counts as a failure for a hard constraint, because the
system can't show the model meets it. Making the budget hard too (`input_price <= 0.1` hard) leaves
only claude-haiku-5-5 — and at about $230 a month on these assumptions even it is slightly over:
a strict reading leaves no model, which is a real trade-off for the Technical Lead to decide.

## Optional — failure path (not yet rehearsed; try it once before the demo)

Bionic → Developer → **Stop** the server, then submit any requirement. Expect within a few seconds
(connection refused, no long wait): the black **interpretation_failed** badge, "did not return valid
criteria twice, so none were made up", and a manual row. Fill it (e.g. `input_price <= 5`,
weighted, 1) and Confirm: a normal ranking. Start the server again and re-run Prompt A before
continuing.

## If asked about the deviation log

"Of 28 deviations between our C.1.1 spec and the one-pass generation, 18 were gaps in our own spec,
4 were assistant errors we fixed with regression tests, and 6 were unrequested additions. The spec
gaps are listed as new requirements to add in Innoslate." Rehearsal added one more spec gap: the
validator doesn't check that a criterion's unit is the metric's unit (Innoslate item 23).

## Timed walkthroughs

CR 2.1.1 (review and confirm the mapping in ≤ 10 operator minutes) and SR 2.1.1 (a full comparison
in ≤ 30) are demonstrations. Time the operator's own minutes — from Submit to Confirm (mapping
review) and from typing to the result page (full comparison) — and add rows to
`docs/validation/walkthroughs.csv` (`date,operator,scenario,minutes`):

```
2026-11-xx,<your name>,mapping_review:SCENARIO_02,<minutes>
2026-11-xx,<your name>,full_comparison,<minutes>
```

The `mapping_review` rows need the sample scenarios' own texts (sample_data/user_inputs.json,
SCENARIO_01–04), one row each; they turn the 16 demonstration tests green (CR 1.2.4, CR 1.3.6,
CR 1.4.3, CR 2.1.1). Log real timings only.
