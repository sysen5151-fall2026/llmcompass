# SPEC - LLM Compass

All build prompts should start from this file. If something here is wrong, fix it
here first and then re-prompt.

Based on:
- Stakeholder Needs and Requirements Definition report (Project Task 2):
  effective needs (Tables 7-8), requirement traces (Table 10), MOEs (Table 11)
- Innoslate stakeholder requirements, section 5
- OpsCon in the README
- docs/context.md
- docs/walking-skeleton.md

Need IDs (SN-TL-xx, SN-PO-xx) are the effective needs from report section 2.5.3.
Technical Lead = Alex Chen, Product Owner = Maya Patel. Each need lists the
primitive needs (PN) and CTQs it came from. StR IDs are the Innoslate numbers.

There are no REQ-xxx IDs. When code or a commit cites a requirement, use the StR
ID with its need, e.g. `# SN-TL-03 / 5.1.2.2`. Only these IDs count as traced.

Test names use the need ID + StR ID, e.g.
`test_SN_TL_03_5_1_2_2_stale_after_90_days`. If a StR traces to more than one need,
its test name uses the first need listed.

MOE targets and verification methods (T = test, I = inspection, A = analysis,
D = demonstration) are from report Table 11. Requirements verified by
demonstration are checked from timed walkthroughs (see section 4), not unit tests.

## 1. Needs and acceptance criteria

### Technical Lead

#### SN-TL-01 (from PN-TL-01, 05; CTQ-04, 05)
"The Technical Lead needs to compare candidate models against the application's
actual requirements rather than general-purpose benchmark scores."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.1.1 | Accept requirements in natural-language text | 100% accepted without reformatting / T | Non-empty text is accepted and gets a requirement ID. Empty/whitespace input is rejected. |
| 5.1.1.2 | At least one measurable criterion per requirement, or report no suitable proxy | 100% / T | Every result in the reference set has at least 1 criterion or `no_suitable_proxy = true`. None have neither. |
| 5.1.1.3 | Proxy-strength rating for every criterion | 100% / T | Every criterion has `proxy_strength` of strong, moderate, or weak. |

#### SN-TL-02 (from PN-TL-07; CTQ-03)
"The Technical Lead needs to know the origin of every piece of evidence used in a
comparison."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.2.1 | Show source and collection date for every figure in a ranking | 100% / I | Every figure in the ranking output has a non-null `source_id` and `collection_date`. |

#### SN-TL-03 (from PN-TL-02; CTQ-02)
"The Technical Lead needs to know whether the evidence underlying a comparison is
still current."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.2.2 | Flag figures older than 90 days as stale | 90 days / T | Figure dated 91 days ago is stale. Figure dated 90 days ago is not. |

#### SN-TL-04 (from PN-TL-09; CTQ-01, 04)
"The Technical Lead needs to see which stated requirements drove each candidate's
position in the ranking."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.3.1 | Report each criterion's contribution to each candidate's position | 100% of ranked candidates / I | Each ranked candidate has one contribution entry per weighted criterion. |

#### SN-TL-05 (from PN-TL-10; CTQ-09)
"The Technical Lead needs to know whether a different weighting of priorities would
change the recommendation."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.4.1 | Find every candidate pair whose order flips under +/-10% change in any one weight | +/-10% on any single weight / A | On a fixture with a known answer, the reported pairs match exactly what you get by changing each weight -10% and +10% one at a time. |

#### SN-TL-06 (from PN-TL-04; CTQ-06)
"The Technical Lead needs to revisit a completed selection when a new model is
released, without repeating the original analysis."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.3.3 | Store each decision record | 100% retrievable after session ends / T | A stored record pulled back by ID matches the original, including after the app restarts. |
| 5.1.5.1 | Retrieve a stored decision record on request | 100% / T | Existing ID returns the record. Unknown ID returns a not-found error. |
| 5.1.5.2 | Updated ranking from a stored record + current data | <= 10 min operator effort / D | Re-run uses current data without re-entering requirements. Every logged `rerun` walkthrough is 10 min or less. |

#### SN-TL-07 (from PN-TL-06; CTQ-07)
"The Technical Lead needs to reconcile the competing positions of the Application
Developer, Budget Owner, and Compliance Officer into a single decision."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.6.1 | Mark each criterion hard or weighted, with a weight for weighted ones | 100% / T | Criterion accepts `hard` or `weighted`. Weighted with no weight is rejected. |
| 5.1.6.2 | Remove every candidate failing a hard constraint, regardless of score | 100% / T | In a fixture where the top-scoring candidate fails a hard constraint, it is not in the ranking. |
| 5.1.6.3 | Report which constraint removed each excluded candidate (also SN-TL-09) | 100% / T | Each excluded candidate lists at least one failed constraint ID. |

#### SN-TL-08 (from PN-TL-08; CTQ-08)
"The Technical Lead needs to reduce the repetitive manual effort of gathering and
cross-referencing model information."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.3.1.1 | Complete comparison of at least 10 candidates | <= 30 min operator effort / D | Comparison handles 10+ candidates. Every logged `full_comparison` walkthrough is 30 min or less. |

#### SN-TL-09 (from PN-TL-03; CTQ-01)
"The Technical Lead needs to explain and defend the selection in a technical review
months after it was made."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.3.2 | Decision record with requirements, mapping, weights, evidence + provenance, ranking, sensitivity | 100% of selections have all 6 / T | Every completed selection produces a record with all 6 sections filled in, and every evidence item has a source and date. |
| 5.1.3.3 | Store each decision record | see SN-TL-06 | |
| 5.1.6.3 | Report exclusions | see SN-TL-07 | |

### Product Owner

#### SN-PO-01 (from PN-PO-01, 03; CTQ-10, 13)
"The Product Owner needs the consequences of a model choice expressed in business
terms rather than benchmark scores."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.2.2.1 | Trade-off summary for the top 3 candidates in cost, capability, and risk terms only, with no benchmark names or metric IDs (also SN-PO-03, SN-PO-07) | (a) >= 3 summaries, (b) 0 restricted terms / T; (c) <= 1 clarification question per summary / D | (a) Top 3 each have a summary. (b) No summary contains a term from the restricted vocabulary (every `benchmark_id` plus the field names in section 2). (c) Checked in the Product Owner review session, not in CI. |

#### SN-PO-02 (from PN-PO-02; CTQ-11)
"The Product Owner needs to see how cost behaves as usage grows."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.2.1.1 | Monthly cost per candidate over volumes covering at least 2 orders of magnitude | >= 2 orders of magnitude / T | At 100 and 10,000 requests/day, every candidate gets a monthly USD cost that matches the formula in section 2 within $0.01. |

#### SN-PO-03 (from PN-PO-09; CTQ-13)
"The Product Owner needs an explicit statement of what the organization gains and
gives up by choosing one model over another."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.2.2.1 | see SN-PO-01 | | Each top-3 summary states at least one gain and one thing given up compared to each of the other two. |

#### SN-PO-04 (from PN-PO-04, 07; CTQ-12)
"The Product Owner needs business risks - vendor dependence, switching cost, output
inconsistency - surfaced before development is committed."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.2.3.1 | Report vendor dependence, switching cost, deprecation risk per candidate | 100% of ranked candidates / I | All three fields are non-null for every ranked candidate. Units/scale not decided yet (see section 5). |

Gap: output inconsistency is in the need but no StR covers it (see section 5).

#### SN-PO-05 (from PN-PO-06; CTQ-09, 11)
"The Product Owner needs to know whether the recommendation still holds if cost,
usage, or product priorities change."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.1.4.1 | see SN-TL-05 | | Covers priority (weight) changes only. |

Gap: nothing checks whether the ranking holds when usage or prices change (see
section 5).

#### SN-PO-06 (from PN-PO-08; CTQ-14)
"The Product Owner needs to avoid paying for capability the customer will not
notice."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.2.4.1 | Flag candidates that exceed every capability requirement, with cost premium over the cheapest candidate that meets all requirements | 100% identified with premium / T | In a fixture, those candidates are flagged and premium = their monthly cost minus the cheapest passing candidate's monthly cost. A candidate that only meets the thresholds is not flagged. |

#### SN-PO-07 (from PN-PO-05; CTQ-10)
"The Product Owner needs to judge the recommendation without acquiring LLM expertise
of her own."

| StR | Requirement | MOE / method | Acceptance criterion |
|---|---|---|---|
| 5.2.2.1 | see SN-PO-01 | | Same tests as SN-PO-01. |

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

Trace gaps:

1. SN-PO-04: "output inconsistency" has no StR. 5.2.3.1 only covers vendor
   dependence, switching cost, and deprecation.
2. SN-PO-05: 5.1.4.1 only varies weights. Nothing checks whether the ranking holds
   when usage volume or prices change.
3. In the OpsCon but no StR yet: accept/reject/amend the proposed criteria
   (UC.1.6/UC.1.9), export the decision record, and show what changed on a re-run.

Ambiguities:

4. 5.1.1.3: the strong/moderate/weak scale is a placeholder. Confirm it.
5. 5.1.4.1: is +/-10% relative (w x 1.1) or absolute (w + 0.10)? Do weights get
   renormalized? Changes which pairs count as unstable. Tests assume relative.
6. 5.1.5.2 and 5.3.1.1: how many walkthrough trials, who runs them, and starting
   from what state?
7. 5.2.2.1: the restricted vocabulary list needs an owner (report 3.3 says the team
   maintains it). Right now it's every `benchmark_id` + the section 2 field names.
8. 5.2.3.1 has no units, scale, or data source for vendor dependence or switching
   cost, and they're not in the data contract.
9. 5.1.2.2: do stale figures still count in the ranking, or get excluded?
10. 5.2.1.1: OK with a 30-day month and operator-entered token counts?
11. 5.1.3.1 wants every criterion's contribution shown, 5.2.2.1 bans metric names
    in the summary. Fine as long as they're separate views - confirm.
