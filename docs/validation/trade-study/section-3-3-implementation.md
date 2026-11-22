# Section 3.3 Decision Record: product build text (paste-ready)

Draft for the "Product build" placeholders in Section 3.3 of the System Analysis and Risk
Assessment report (Lab Manual 11.2). The team should review it and replace "Figure X" /
"Table X" with the report's numbering. Every figure here comes from the repo and was
checked (see `swing-weight-check.md` and `sources-check.md` in this folder).

---

**Implementation.** The selected alternative was implemented in the F.8 adapter
(`backend/provide_requirement_interpretation/`) and merged to the main branch [commit id], and it is
recorded in architecture decision record ADR-0009 (Team CASCADILLA, 2026c). Because the
local runtime was already the provisional mechanism of F.8, implementing the selection
meant making the configuration the trade study evaluated the one the product enforces.
Checking the study's claims against the product showed this had not been the case.

The measurements behind EC.2 and EC.3 were made with `qwen2.5-7b-instruct-1m`, GGUF
Q4_K_M (Team CASCADILLA, 2026b), while the specification named the Q4_K_S
`qwen2.5-7b-instruct`. LM Studio answers a request for a model it does not have with
whatever model is loaded: a request for `qwen2.5-7b-instruct` was answered by the `-1m`
model. The "team pins the exact weights" basis of EC.4 was therefore not enforced. The
build made three changes:

1. **Model identifier pinned to the measured build.** The default model is now
   `qwen2.5-7b-instruct-1m` Q4_K_M. The adapter rejects any reply that names a different
   model, so it is treated like an invalid response: retried once, then flagged for manual
   entry. It never silently produces criteria from another model (SR 2.1.3, SR 2.3.1).
2. **Provisional limits confirmed.** SR 1.3.2 requires an answer within 110 s per request,
   limited to 512 tokens. The pinned model's 150 measured calls peaked at 18.1 s, and its
   longest answer was 301 tokens, so both adapter limits stay as they are and are no
   longer provisional.
3. **Data locality guard kept.** The adapter still refuses any runtime address other than
   the local machine before anything is sent (SR 2.2.1, SR 2.4.1), which is what EC.1's
   score of 100 relies on.

The losing alternative would have required:
- a second F.8 adapter for the OpenAI API behind the same model contract, with rate-limit
  and network-error handling;
- an API key and internet access from every deployment;
- changes to SR 2.2.1 Local interpretation and SR 2.4.1 Query cost (to at least $0.029 per
  comparison);
- a review of the provider's data-processing terms with the Compliance Officer;
- a model-version migration at each deprecation, with at least 6 months' notice
  (OpenAI, 2026c).

**Verification.**
- **Recomputed figures:** every figure in Section 3.1 and 3.2 was recomputed from the raw
  measurement data by a script (`tools/swing_weight_analysis.py`). 70 of 71 reproduce. The
  one that does not (the cost basis), together with rounding and wording issues, is in the
  corrections table below.
- **Sourced inputs:** every sourced input was checked against its source on 22 November
  2026. All hold except the Artificial Analysis figures, which now read 2.03 s and
  60 tokens/s. With these, B's total stays 55.9.
- **Suite and live run:** the nine new adapter tests pass, and the rest of the suite is
  unchanged: 291 pass, and the same 12 acceptance tests fail as before, none of them
  related to F.8. A live run against LM Studio returned valid criteria for all five
  requirements from the pinned model and rejected all five when another model name was
  requested.

---

## Corrections to make elsewhere in the report (found by the check)

| Where | Now | Change to | Why |
|---|---|---|---|
| Life-cycle cost table, API usage basis | "$0.029 × 1,000 comparisons" | "$0.0286 × 1,000 comparisons" | $0.029 × 1,000 = $29.00; the $28.60 total uses the unrounded value |
| Value table, A total | 75.0 (column sums to 74.9) | add note "totals computed before rounding" | rounding |
| 3.2 text, "at most 12 points" | 12 | "about 12 points" (12.3) | shared-server test raises A by 12.3 |
| 2.1 / 3 alternative A name | "Qwen2.5-7B-Instruct, 4-bit quantised" | "Qwen2.5-7B-Instruct-1M, GGUF Q4_K_M (pinned)" | the measured and now pinned build |
| Sensitivity table, EC.1 and EC.5 text | "B would be preferred only if … fell to about 46 / rose to about 124" | "… fell below about 46 / rose above about 124" | at those values the two tie |
| Input data, B TTFT and speed | 2.00 s, 61 tokens/s | 2.03 s, 60 tokens/s (retrieved 22 Nov 2026), or keep the old values with their 21 Nov retrieval date | Artificial Analysis uses a 5-day rolling average; no change to any total |
| Input data, Apple row | "largest power adapter supplied" | "power adapter supplied" | the source lists one adapter and doesn't say "largest" |
| Swing weight matrix, EC.3 | Small variation, weight 40 | justify "Small" as the swing on the 80-100% scale, or note that both alternatives score 100, so EC.3 adds 14.0 to both totals | variation is defined "across the alternatives", and that is zero here |

## Risk register link (Chapter 4)

R2 (Runtime unavailable) is the accepted consequence of EC.5 = 0. The pin adds one cause of
R2: a team machine with a different model loaded now gets `interpretation_failed`. That is
visible and recoverable, unlike the silent substitution it replaces, which bore on R5
(Ranking not reproducible).
