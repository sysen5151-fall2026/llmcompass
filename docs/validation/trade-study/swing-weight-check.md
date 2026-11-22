# Swing weight trade study: numerical check

Check of the swing weight trade study (Chapter 3, Alternative Selection; Lab Manual 11.2):
A = local runtime (LM Studio), B = hosted GPT-6.2 Sol API. Traces to SR 2.4.1 (query cost),
SR 2.2.1 (local interpretation), SR 1.3.2 (interpretation response time MOP) and SR 2.1.2
(re-evaluation effort). Every figure is recomputed by `tools/swing_weight_analysis.py` from the raw
data in `docs/validation/measured-behavior/` (warm-up run_id -1 excluded) and the sourced and
assumed inputs as the study states them.

## Reproduce

```
python3.12 tools/swing_weight_analysis.py
```

Stdlib only; prints every table below, including the comparison, and exits 0.

## Measured inputs (A), recomputed from the raw data

| Quantity | n | Mean | p95 | Max | Min |
|---|---|---|---|---|---|
| Interpretation time per request (s) (`interpretation_log.csv`) | 150 | 7.010 | 16.00 | 18.07 | 1.13 |
| Interpretation time per comparison, UC.1.4 (s) (`per_run.csv`; equals the per-run sum of the log) | 30 | 35.050 | 43.35 | 45.50 | 26.42 |
| Per request, runs 1-16 (battery) (s) | 80 | 8.325 | 16.50 | 18.07 | 1.66 |

- Valid on first attempt: 150 of 150 (100%); no row with attempt > 1.
- p95 uses the method of `tools/compare_measured_simulated.py` (`statistics.quantiles`, n = 20, inclusive).
- Model id used (`runs_meta.json` `llm_model`): **`qwen2.5-7b-instruct-1m`** (GGUF Q4_K_M per
  `measured-behavior.md`), endpoint `http://127.0.0.1:1234/v1`.

## Comparison of every printed figure

The study's figure is compared with the recomputed value rounded half-up to the decimals the study
prints. 70 of 71 figures reproduce.

| Claim | Study value | Recomputed (unrounded) | Match? |
|---|---|---|---|
| A mean time per request (s) | 7.01 | 7.01 (7.00996) | yes |
| A valid on first attempt (%) | 100 | 100 (100) | yes |
| A mean time per comparison (s) | 35.05 | 35.05 (35.0498) | yes |
| A mean per request, runs 1-16 (s) | 8.33 | 8.33 (8.32528) | yes |
| B reasoning tokens | 122 | 122 (122) | yes |
| B output tokens billed | 272 | 272 (272) | yes |
| B time per request (s) | 4.46 | 4.46 (4.45902) | yes |
| B cost per request ($) | 0.0057 | 0.0057 (0.00572) | yes |
| B cost per comparison ($) | 0.029 | 0.029 (0.0286) | yes |
| A - B time per request (s) | 2.6 | 2.6 (2.55094) | yes |
| EC.1 normalised weight | 0.351 | 0.351 (0.350877) | yes |
| EC.2 normalised weight | 0.088 | 0.088 (0.0877193) | yes |
| EC.3 normalised weight | 0.140 | 0.140 (0.140351) | yes |
| EC.4 normalised weight | 0.175 | 0.175 (0.175439) | yes |
| EC.5 normalised weight | 0.246 | 0.246 (0.245614) | yes |
| EC.1 A value | 100 | 100 (100) | yes |
| EC.1 B value | 0 | 0 (0) | yes |
| EC.2 A value | 94.5 | 94.5 (94.4863) | yes |
| EC.2 B value | 96.8 | 96.8 (96.8266) | yes |
| EC.3 A value | 100 | 100 (100) | yes |
| EC.3 B value | 100 | 100 (100) | yes |
| EC.4 A value | 100 | 100 (100) | yes |
| EC.4 B value | 50 | 50 (50) | yes |
| EC.5 A value | 0 | 0 (0) | yes |
| EC.5 B value | 100 | 100 (100) | yes |
| EC.1 A weighted | 35.1 | 35.1 (35.0877) | yes |
| EC.1 B weighted | 0.0 | 0.0 (0) | yes |
| EC.2 A weighted | 8.3 | 8.3 (8.28827) | yes |
| EC.2 B weighted | 8.5 | 8.5 (8.49356) | yes |
| EC.3 A weighted | 14.0 | 14.0 (14.0351) | yes |
| EC.3 B weighted | 14.0 | 14.0 (14.0351) | yes |
| EC.4 A weighted | 17.5 | 17.5 (17.5439) | yes |
| EC.4 B weighted | 8.8 | 8.8 (8.77193) | yes |
| EC.5 A weighted | 0.0 | 0.0 (0) | yes |
| EC.5 B weighted | 24.6 | 24.6 (24.5614) | yes |
| A total value | 75.0 | 75.0 (74.9549) | yes |
| B total value | 55.9 | 55.9 (55.862) | yes |
| A - B total | 19.1 | 19.1 (19.093) | yes |
| B gain on response time (weighted) | 0.2 | 0.2 (0.205291) | yes |
| A electricity, 1 year ($) | 0.25 | 0.25 (0.248756) | yes |
| B API usage, 1 year ($) | 28.60 | 28.60 (28.6) | yes |
| B API usage per stated basis $0.029 x 1,000 ($) | 28.60 | 29.00 (29) | **NO** |
| EC.1 base weight (sensitivity table) | 0.35 | 0.35 (0.350877) | yes |
| EC.2 base weight (sensitivity table) | 0.09 | 0.09 (0.0877193) | yes |
| EC.3 base weight (sensitivity table) | 0.14 | 0.14 (0.140351) | yes |
| EC.4 base weight (sensitivity table) | 0.18 | 0.18 (0.175439) | yes |
| EC.5 base weight (sensitivity table) | 0.25 | 0.25 (0.245614) | yes |
| EC.1 tie weight | 0.20 | 0.20 (0.197693) | yes |
| EC.1 tie as swing weight ('about 46') | 46 | 46 (45.5851) | yes |
| EC.2 tie weight | 0.90 | 0.90 (0.900387) | yes |
| EC.5 tie weight | 0.37 | 0.37 (0.366557) | yes |
| EC.5 tie as swing weight ('about 124') | 124 | 124 (124.415) | yes |
| Test 'Base case': A | 75.0 | 75.0 (74.9549) | yes |
| Test 'Base case': B | 55.9 | 55.9 (55.862) | yes |
| Test 'GPT-6.2 Sol never changes its model (EC.4: B = 100)': A | 75.0 | 75.0 (74.9549) | yes |
| Test 'GPT-6.2 Sol never changes its model (EC.4: B = 100)': B | 64.6 | 64.6 (64.6339) | yes |
| Test 'GPT-6.2 Sol answers instantly (EC.2: B = 100)': A | 75.0 | 75.0 (74.9549) | yes |
| Test 'GPT-6.2 Sol answers instantly (EC.2: B = 100)': B | 56.1 | 56.1 (56.1404) | yes |
| Test 'A as slow as in runs 1 to 16 (8.33 s per request)': A | 74.8 | 74.8 (74.8491) | yes |
| Test 'A as slow as in runs 1 to 16 (8.33 s per request)': B | 55.9 | 55.9 (55.862) | yes |
| Test 'A as slow as in runs 1 to 16, study's rounded 8.33 s': A | 74.8 | 74.8 (74.8487) | yes |
| Test 'A as slow as in runs 1 to 16, study's rounded 8.33 s': B | 55.9 | 55.9 (55.862) | yes |
| Test 'EC.3 floor lowered from 80% to 50%': A | 75.0 | 75.0 (74.9549) | yes |
| Test 'EC.3 floor lowered from 80% to 50%': B | 55.9 | 55.9 (55.862) | yes |
| Test 'GPT-6.2 Sol valid on only 90% of first attempts': A | 75.0 | 75.0 (74.9549) | yes |
| Test 'GPT-6.2 Sol valid on only 90% of first attempts': B | 48.8 | 48.8 (48.8444) | yes |
| Test 'A moved to a shared team server (EC.5: A = 50)': A | 87.2 | 87.2 (87.2356) | yes |
| Test 'A moved to a shared team server (EC.5: A = 50)': B | 55.9 | 55.9 (55.862) | yes |
| Test 'Both of the first two changes together': A | 75.0 | 75.0 (74.9549) | yes |
| Test 'Both of the first two changes together': B | 64.9 | 64.9 (64.9123) | yes |
| Largest change from team-judgement tests ('at most 12 points') | 12 | 12 (12.2807) | yes |

## Discrepancies

Numerical:

1. **Life-cycle cost basis does not give the cost it states.** In the Life-cycle cost table, the basis
   "$0.029 × 1,000 comparisons" works out to **$29.00**, not $28.60. The $28.60 total is correct. It
   comes from the unrounded $0.0286 per comparison (5 × $0.00572). Correct the basis to
   "$0.0286 × 1,000 comparisons", or keep the basis and say the $0.029 is rounded.
2. **Weighted-value column does not add up to A's printed total.** A's rounded weighted values
   (35.1 + 8.3 + 14.0 + 17.5 + 0.0) sum to **74.9**, but the table prints a total of 75.0. The 75.0 is
   correct (74.955), so this is only a rounding effect. Add a note such as "totals computed before
   rounding". B's column does add up to 55.9.
3. **"Change the totals by at most 12 points" understates the change slightly.** The shared-team-server
   test raises A by **12.3** points (74.955 to 87.236). The printed totals give 87.2 - 75.0 = 12.2.
   Write "about 12 points" or "at most 12.3 points".

Internal contradictions and wording:

4. **Model id.** Chapter 3 names the local model "Qwen2.5-7B-Instruct in LM Studio" and EC.4 scores A
   on "pinned GGUF weights". The 30 measured runs used **`qwen2.5-7b-instruct-1m` (Q4_K_M)**.
   `measured-behavior.md` gives the team's documented setup as qwen2.5-7b-instruct **Q4_K_S**. So the
   measured inputs (7.01 s, 35.05 s, 150/150) come from a different build than the one the study
   describes, and the pinned build was not the one that ran. That weakens the EC.4 = 100 basis. State
   the measured build, or re-run on the documented one.
5. **The 110 s anchor of EC.2.** *(Withdrawn 2026-11-22: the Innoslate export shows SR 1.3.2 states "within 110 s per interpretation request", so the study's wording is right; SPEC.md was out of date.)* The study calls 110 s "the provisional SR 1.3.2 limit in the model".
   SPEC section 3 sets 110 s as the adapter **timeout** (provisional). SR 1.3.2's MOP target is still
   "To be set after the local runtime is benchmarked" (SPEC section 6), and `measured-behavior.md`
   lists it as an open item. Describe 110 s as the provisional timeout.
6. **Tie-weight wording.** The tie weights reproduce (EC.1 0.198 = swing weight 45.6; EC.2 0.900;
   EC.5 0.367 = swing weight 124.4). The text, though, says B "would be preferred" at those values. At
   those values the two alternatives tie, so B is preferred only *below* about 46 (EC.1) or *above*
   about 124 (EC.5). Also, for EC.3 "None" is right for a change of preference, but the two total
   lines do meet at w = 1, where both score 100.
7. **Swing weight placement.** The cell weights obey the matrix rule (no dominance violation), and
   every criterion's weight equals its cell. However, step 1 defines variation "across the
   alternatives", and on EC.3 both alternatives score 100 (B by assumption). That is zero swing, yet
   EC.3 gets 40, more than EC.2 (25), whose swing is 2.3 value points. This does not change the
   preference, because it adds 14.0 to both totals. It does dilute every normalised weight, including
   the tie weights reported as fractions. Either justify "Small" for EC.3 as the swing on the 80-100%
   scale, or give EC.3 a weight that reflects its zero swing across the alternatives.
8. **Minor.** The 35.05 s mean (used for electricity) mixes two power states: runs 1-16 average
   41.6 s and runs 17-30 average 27.5 s. It describes neither. This does not change the $0.25 upper
   bound.

Everything else reproduces: all measured inputs; B's derived 4.46 s, 122 / 272 tokens, $0.0057 and
$0.029; the normalised weights, scores and weighted values; the totals 75.0 / 55.9 and the 19.1 gap;
the $0.25 and $28.60 costs; the affordability verdict (SR 2.4.1); all five sensitivity rows; and all
eight assumption-test rows.
