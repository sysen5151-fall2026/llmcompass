# SPEC - LLM Compass

All build prompts should start from this file. If something here is wrong, fix it
here first and then re-prompt.

Based on:
- Innoslate ORD, section 5 (Stakeholder Requirements)
- OpsCon in the README
- docs/context.md
- docs/walking-skeleton.md

Need IDs (SN-TL-xx, SN-PO-xx) come from the Stakeholder Needs doc (Technical Lead =
Alex Chen, Product Owner = Maya Patel). StR IDs are the ORD paragraph numbers.

Test names for Lab 4 use the need ID + StR ID, e.g.
`test_SN_TL_03_5_1_2_2_stale_after_90_days`. If a StR traces to more than one need,
its test name uses the first need listed.

## 1. Needs and acceptance criteria

### Technical Lead

#### SN-TL-01 (High)
"The Technical Lead needs to compare candidate models against the application's
actual requirements rather than general-purpose benchmark scores."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.1.1 | Accept requirements in natural-language text | Non-empty text is accepted and gets a requirement ID. Empty/whitespace input is rejected. |
| 5.1.1.2 | At least one measurable criterion per requirement, or report no suitable proxy, for 100% of requirements | Every result in the reference set has at least 1 criterion or `no_suitable_proxy = true`. None have neither. |
| 5.1.1.3 | Proxy-strength rating for 100% of criteria | Every criterion has `proxy_strength` of strong, moderate, or weak. |

#### SN-TL-02 (High)
"The Technical Lead needs to know the origin of every piece of evidence used in a
comparison."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.2.1 | Show source and collection date for 100% of figures in a ranking | Every figure in the ranking output shows a non-null `source_id` and `collection_date`. |

#### SN-TL-03 (High)
"The Technical Lead needs to know whether the evidence underlying a comparison is
still current."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.2.2 | Flag figures older than 90 days as stale | Figure dated 91 days ago is stale. Figure dated 90 days ago is not. |

#### SN-TL-04 (High)
"The Technical Lead needs to see which stated requirements drove each candidate's
position in the ranking."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.3.1 | Report each criterion's contribution to each candidate's rank | Each ranked candidate has one contribution entry per weighted criterion. |

#### SN-TL-05 (High)
"The Technical Lead needs to know whether a different weighting of priorities would
change the recommendation."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.4.1 | Find every candidate pair whose order flips under +/-10% change in any one weight | On a test fixture with a known answer, the reported pairs match exactly what you get by changing each weight -10% and +10% one at a time. |

#### SN-TL-06 (High)
"The Technical Lead needs to revisit a completed selection when a new model is
released, without repeating the original analysis."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.3.3 | Store each decision record | A stored record pulled back by ID matches the original. |
| 5.1.5.1 | Retrieve a stored decision record on request | Existing ID returns the record. Unknown ID returns a not-found error. |
| 5.1.5.2 | Updated ranking from a stored record + current data in 10 min or less of operator effort | Re-run uses current data without re-entering requirements. Timed walkthrough from opening the record to seeing the new ranking is 10 min or less every time. |

#### SN-TL-07 (High)
"The Technical Lead needs to reconcile the competing positions of the Application
Developer, Budget Owner, and Compliance Officer into a single decision."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.6.1 | Mark each criterion hard or weighted, with a weight for weighted ones | Criterion accepts `hard` or `weighted`. Weighted with no weight is rejected. |
| 5.1.6.2 | Remove 100% of candidates failing a hard constraint regardless of score | In a fixture where the top-scoring candidate fails a hard constraint, it is not in the ranking. |
| 5.1.6.3 | Report which constraint removed each excluded candidate | Each excluded candidate lists at least one failed constraint ID. |

#### SN-TL-08 (Medium)
"The Technical Lead needs to reduce the repetitive manual effort of gathering and
cross-referencing model information from scattered sources."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.3.1.1 | Compare at least 10 candidates in 30 min or less of operator effort | Comparison has 10+ candidates. Timed walkthrough from first requirement to exported record is 30 min or less every time. |

#### SN-TL-09 (High)
"The Technical Lead needs to explain and defend the selection in a technical review
months after it was made."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.3.2 | Decision record with requirements, mapping, weights, evidence + provenance, ranking, sensitivity, for 100% of selections | Every completed selection produces a record with all 6 sections filled in. |
| 5.1.3.3 | Store each decision record | Covered under SN-TL-06. |

### Product Owner

#### SN-PO-01 (High)
"The Product Owner needs the consequences of a model choice expressed in business
terms rather than benchmark scores."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.2.2.1 | Summary for top 3 candidates in terms of cost, capability, and risk only, with no benchmark names or metric IDs | Top 3 each have a summary. No summary contains a `benchmark_id` or a field name from section 2. |

#### SN-PO-02 (High)
"The Product Owner needs to see how cost behaves as usage grows."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.2.1.1 | Monthly cost per candidate over volumes covering at least 2 orders of magnitude | At 100 and 10,000 requests/day, every candidate gets a monthly USD cost that matches the formula in section 2 within $0.01. |

#### SN-PO-03 (High)
"The Product Owner needs an explicit statement of what the organization gains and
gives up by choosing one model over another."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.2.2.1 | (same as SN-PO-01) | Each top-3 summary states at least one gain and one thing given up relative to each of the other two. |

#### SN-PO-04 (High)
"The Product Owner needs business risks - vendor dependence, switching cost, output
inconsistency - surfaced before development is committed."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.2.3.1 | Report vendor dependence, switching cost, deprecation risk per candidate | All three fields are non-null for every ranked candidate. Units/scale still need to be decided (see section 5). |

Gap: no StR covers output inconsistency (see section 5).

#### SN-PO-05 (Medium)
"The Product Owner needs to know whether the recommendation still holds if cost,
usage, or product priorities change."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.1.4.1 | (same as SN-TL-05) | Covers priority (weight) changes. |
| 5.2.1.1 | (same as SN-PO-02) | Covers usage changes for cost only. |

Gap: no StR checks whether the ranking changes with usage or price (see section 5).

#### SN-PO-06 (Medium)
"The Product Owner needs to avoid paying for capability the customer will not
notice."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.2.4.1 | Flag candidates that exceed every capability requirement, with cost premium over the cheapest candidate that meets all of them | In a fixture, those candidates are flagged and premium = their monthly cost minus the cheapest passing candidate's monthly cost. |

#### SN-PO-07 (High)
"The Product Owner needs to judge the recommendation without acquiring LLM expertise
of her own."

| StR | Requirement | Acceptance criterion |
|---|---|---|
| 5.2.2.1 | (same as SN-PO-01) | Same test as SN-PO-01. |

## 2. Data contract - Benchmark Data Sources (C.7)

Covers UC.1.10 (request model data) and UC.1.11 (model spec + benchmark data).

Source: increment 1 is manual entry. Increment 2 is automated pulls from public
leaderboards and vendor pages (sources not picked yet).

Every value is stored as a "figure" so the source stays attached to it (5.1.2.1):

| Field | Type | Notes |
|---|---|---|
| value | number, string, or list of strings | |
| unit | string | |
| source_id | string | URL or citation, required |
| collection_date | date (YYYY-MM-DD) | required |
| stale | bool | true if older than 90 days (5.1.2.2) |

Candidate model fields:

| Field | Type | Unit | Required |
|---|---|---|---|
| model_id | string | | yes |
| vendor | string | | yes |
| model_name | string | | yes |
| input_price | figure | USD per 1M input tokens | yes |
| output_price | figure | USD per 1M output tokens | yes |
| context_window | figure | tokens | yes |
| latency_p50 | figure | seconds | no |
| data_residency | figure | country codes (ISO 3166-1 alpha-2) | no |
| data_retention | figure | days | no |
| deprecation_date | figure | date | no |
| benchmarks | list of {benchmark_id, score} | score unit given per benchmark | no |

The operator also enters `requests_per_day`, `input_tokens_per_request`, and
`output_tokens_per_request` for the cost calculation (5.2.1.1):

```
monthly_cost_usd = requests_per_day * 30
                 * (input_tokens_per_request * input_price
                  + output_tokens_per_request * output_price) / 1,000,000
```

Refresh: increment 1 updates when the operator enters or edits data. Increment 2
cadence not decided yet. Stale flag applies either way.

Missing values:
- Missing data for a weighted criterion: candidate scores 0 on it and the gap is
  shown in the rationale. Never filled in silently.
- Missing data for a hard constraint: candidate is excluded with reason
  `missing_data:<field>`. (Need team sign-off on this.)
- A figure with no source_id or collection_date is rejected at entry.

Source unavailable: rank using the last stored figures, each shown with its date
and stale flag. No value is shown without a date. If nothing is stored at all,
show "no model data available" and don't rank.

## 3. Model contract - Language model runtime (C.8)

Local model via LM Studio (ADR-0001). Covers UC.1.3 (submit requirement) and UC.1.4
(proposed criteria).

What it's asked to do: for one requirement, propose measurable criteria that stand
in for it, each with a proxy-strength rating. If nothing published fits, say so
instead of using a weak proxy (OpsCon 4.4).

Request:

```json
{ "requirement_id": "string", "text": "string" }
```

Response:

```json
{
  "requirement_id": "string",
  "no_suitable_proxy": false,
  "criteria": [
    {
      "criterion_id": "string",
      "metric": "section 2 field name or known benchmark_id",
      "operator": ">= | <= | == | in",
      "threshold": "number | string | list | null",
      "unit": "string",
      "proxy_strength": "strong | moderate | weak",
      "category": "capability | cost | compliance | other",
      "rationale": "string"
    }
  ]
}
```

Valid only if:
- either `criteria` has 1+ entries, or `no_suitable_proxy` is true and `criteria`
  is empty
- every `metric` exists in section 2
- `proxy_strength` is strong, moderate, or weak

`category` is used by 5.2.4.1 to tell capability criteria apart from cost and
compliance ones.

If the response is bad (not JSON, wrong schema, unknown metric, or timeout - limit
TBD), retry once. If it fails again, mark the requirement `interpretation_failed`
and let the Technical Lead enter criteria by hand. Don't drop the requirement and
don't make up criteria.

All proposed criteria need Technical Lead confirmation (UC.1.9) before ranking.

## 4. Test interface (provisional)

The Lab 4 tests in `tests/` call these functions. The names are placeholders until
the interface contract in Chapter 7. A test fails with `not implemented: <name>`
until its function exists.

| Function | Module | StRs |
|---|---|---|
| `receive_requirements(text) -> {"requirement_id"}` | llm_compass | 5.1.1.1 |
| `submit_requirements({"requirement_id", "text"}) -> model contract response` | language_model_runtime | 5.1.1.2 |
| `validate_interpretation(response) -> bool` | llm_compass | 5.1.1.2, 5.1.1.3 |
| `is_stale(collection_date, today) -> bool` | llm_compass | 5.1.2.2 |
| `rank(candidates, criteria, today) -> {"ranked", "excluded"}` | llm_compass | 5.1.2.1, 5.1.3.1, 5.1.6.2, 5.1.6.3, 5.3.1.1 |
| `unstable_pairs(candidates, criteria, today) -> set of frozenset pairs` | llm_compass | 5.1.4.1 |
| `generate_decision_record(selection) -> record` | llm_compass | 5.1.3.2 |
| `store_decision_record(record) -> id`, `retrieve_decision_record(id)` | llm_compass | 5.1.3.3, 5.1.5.1 |
| `rerun_decision(record_id, candidates, today) -> rank result` | llm_compass | 5.1.5.2 |
| `validate_criterion(criterion)` (raises ValueError) | llm_compass | 5.1.6.1 |
| `monthly_cost(candidate, requests_per_day, input_tokens, output_tokens) -> float` | llm_compass | 5.2.1.1 |
| `tradeoff_summaries(result) -> {model_id: {other_id: {"gains", "gives_up"}}}` | llm_compass | 5.2.2.1 |
| `risk_report(candidate) -> {"vendor_dependence", "switching_cost", "deprecation_risk"}` | llm_compass | 5.2.3.1 |
| `over_capability(result, candidates, criteria, usage) -> {model_id: premium_usd}` | llm_compass | 5.2.4.1 |

Operator-effort criteria (5.1.5.2, 5.3.1.1) are checked from timed walkthroughs
logged in `docs/validation/walkthroughs.csv` (`date,operator,scenario,minutes`,
where scenario is `rerun` or `full_comparison`). The test fails until there's at
least one trial of each and every trial is within its limit.

## 5. Open questions

Trace gaps (need has no StR, or only partial coverage):

1. SN-PO-04: "output inconsistency" has no StR. 5.2.3.1 only covers vendor
   dependence, switching cost, and deprecation.
2. SN-PO-05: 5.1.4.1 only varies weights. Nothing checks whether the ranking holds
   when usage volume or prices change.
3. SN-PO-07 only traces to 5.2.2.1. Probably fine, but it's thin for a High need.
4. Things in the OpsCon/persona with no StR yet: accept/reject/amend the proposed
   criteria (UC.1.6/UC.1.9, fits SN-TL-01), export the decision record (fits
   SN-TL-09), and show what changed on a re-run (fits SN-TL-06).

Ambiguities in the StRs:

5. All StRs show 0% Quality Score - Quality Check hasn't been run. Also typo in
   5.1.6 ("Rtionale").
6. 5.1.1.3 says "proxy-strength rating" but context.md/OpsCon say "confidence
   level". Pick one. The strong/moderate/weak scale is a placeholder.
7. 5.1.4.1: is +/-10% relative (w x 1.1) or absolute (w + 0.10)? Do weights get
   renormalized? Changes which pairs count as unstable.
8. 5.1.5.2 and 5.3.1.1: "operator effort" needs a timed walkthrough. How many
   trials, who runs it, starting from what?
9. 5.2.2.1: the "no benchmark names" part is testable with a blocklist. The
   "only cost, capability, risk" part needs a reviewer checklist.
10. 5.2.3.1 has no units, scale, or data source for vendor dependence or switching
    cost, and they're not in the data contract.
11. 5.1.2.2: do stale figures still count in the ranking, or get excluded?
12. 5.2.1.1: OK with a 30-day month and operator-entered token counts?
13. 5.1.3.1 wants every criterion's contribution shown, 5.2.2.1 bans metric names
    in the summary. Fine as long as they're separate views - confirm.
