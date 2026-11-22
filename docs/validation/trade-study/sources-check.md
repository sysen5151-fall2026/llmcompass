# Trade study: check of sourced claims (Lab Manual 11.2.3)

Every claim in the runtime trade study (Chapter 3 of the System Analysis report, ADR-0009)
that came from outside the team's own measurements, checked against its cited source on
2026-11-22. An assistant (a web-fetch agent) read the pages. **Team check pending:** a team member
must re-open each source and sign below (Lab Manual 11.2.3: "a source you checked
yourself"). The EIA figure was read directly from the downloaded PDF table.

| # | Claim in the study | Source | Result | Actual |
|---|---|---|---|---|
| 1 | GPT-6.2 Sol supports Structured Outputs | OpenAI (2026a), developers.openai.com/api/docs/models/gpt-6.2-sol | Verified | Features list includes `structured_outputs` |
| 2 | $2.00 input / $10.00 output per 1M tokens | OpenAI (2026b), …/api/docs/pricing | Verified | Standard row `gpt-6.2-sol $2.00 $10.00`. Long context (> 272K input) is $4.00 / $15.00, which doesn't apply at about 1,500 input tokens |
| 3 | GA models retired with ≥ 6 months' notice | OpenAI (2026c), …/api/docs/deprecations | Verified, with a caveat | "Generally available models: At least 6 months", qualified by "Unless safety or compliance concerns require a faster timeline" |
| 4 | Reasoning tokens billed as output | OpenAI (2026d), …/api/docs/guides/reasoning | Verified | "billed as output tokens" |
| 5 | TTFT 2.00 s, 61 tok/s at low reasoning effort | Artificial Analysis (2026), artificialanalysis.ai/models/gpt-6-2-sol-high | **Different** | Low row: **2.03 s, 60 tok/s** (5-day rolling average, so the figures drift). The page covers all effort levels, not only "high" |
| 6 | 140 W adapter, largest supplied for M2 Pro 16-inch | Apple (2023), support.apple.com/kb/SP890 | Verified (140 W), with a caveat | The page lists one adapter, "140W USB-C Power Adapter". It doesn't say "largest", so "the adapter supplied" is the accurate wording |
| 7 | $0.1825/kWh, average summer 2026 U.S. residential (forecast) | EIA (2026), STEO Table SF02 | Verified | United States, price, forecast 2026: 18.25 cents/kWh (STEO September 2026) |

## Effect of the one difference (claim 5)

Recomputed with 2.03 s and 60 tok/s:
- **Time per request:** B takes 4.53 s (was 4.46 s), for an EC.2 value of 96.76 (was 96.83).
- **Total value:** B scores **55.86, so 55.9 unchanged**.
- **Cost:** reasoning tokens are 122, unchanged, so the cost per comparison stays $0.0286.

The selection does not change. The report should quote the current figures or state the
retrieval date of the old ones.

## Team-measured inputs

These come from `docs/validation/measured-behavior/` and are recomputed in
`swing-weight-check.md`: 7.01 s per request, 150/150 valid, 35.05 s per comparison, and
8.33 s per request in runs 1-16. All reproduce. The model that produced them is
`qwen2.5-7b-instruct-1m` Q4_K_M, which ADR-0009 now pins.

## Team check

| Checked by | Date | Rows |
|---|---|---|
| | | |

## Not verifiable by the team

- **Hosted API quality.** B's EC.3 = 100 is an assumption, and is marked as one. Measuring
  it needs a paid account (SR 2.4.1 budget = 0). The sensitivity test at 90% validity still
  selects A.
