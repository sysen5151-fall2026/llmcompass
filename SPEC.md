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
- System Requirements Definition report (Project Task 3): system requirements
  1.1.1-1.4.1 generated in Innoslate from the IDEF0-A0 of F.1 (section 6)

Need IDs (SN-TL-xx, SN-PO-xx) are the effective needs from report section 2.5.3.
Technical Lead = Alex Chen, Product Owner = Maya Patel. Each need lists the
primitive needs (PN) and CTQs it came from. StR IDs are the Innoslate numbers.

There are no REQ-xxx IDs. When code or a commit cites a requirement, use the StR
ID with its need, e.g. `# SN-TL-03 / 5.1.2.2`. Only these IDs count as traced.

Test names use the need ID + StR ID, e.g.
`test_SN_TL_03_5_1_2_2_stale_after_90_days`. If a StR traces to more than one need,
its test name uses the first need listed.

MOE targets and verification methods (T = test, I = inspection, A = analysis,
D = demonstration) are from report Table 11.

System requirements (section 6) keep their Innoslate numbers. Cite them as
`SR 1.1.5`, and name their tests `test_SR_1_1_5_<what it checks>`
(tests/test_system_requirements.py). Each one traces up to the StR IDs in its
row, so `SR 1.1.5` and `SN-TL-01 / 5.1.1.1` are both valid citations. Requirements verified by
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

Source: increment 1 is manual entry. Increment 2 is automated pulls, merged by
`model_id` (sources picked 2026-10-23):
- Artificial Analysis data API: prices, benchmark scores, latency. The free tier
  requires attribution to artificialanalysis.ai.
- models.dev (public, no key): context window. OpenRouter's model list is the
  fallback when models.dev has no entry. For open-weight models with no vendor
  entry, the figure comes from a named host, and its `source_id` says so.
- Manual entry: fields no API publishes (data residency, data retention,
  deprecation date).

The catalog is the 14 models in `sample_data/model_sources.json` (10 vendors).
Benchmarks are the ones the Artificial Analysis API returns. AA-Omniscience is
dropped (2026-10-23): the API doesn't publish it.

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
- `requirement_id` is the same as the request's
- either `criteria` has 1+ entries, or `no_suitable_proxy` is true and `criteria`
  is empty, never both
- every `metric` exists in section 2
- each `threshold` fits its `operator`: `in` takes a list; `>=` and `<=` take a
  number or null; `==` takes a number, string, or null
- `proxy_strength` is strong, moderate, or weak

(The ID match, "never both", and operator/threshold rules were confirmed by the
team on 2026-10-25.)

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
| `receive_requirements(text) -> {"requirement_id"}` | provide_llm_selection_decision_support | 5.1.1.1 |
| `submit_requirements({"requirement_id", "text"}) -> model contract response` | provide_requirement_interpretation | 5.1.1.2 |
| `validate_interpretation(response) -> bool` | provide_llm_selection_decision_support | 5.1.1.2, 5.1.1.3 |
| `is_stale(collection_date, today) -> bool` | provide_llm_selection_decision_support | 5.1.2.2 |
| `rank(candidates, criteria, today) -> {"ranked", "excluded"}` | provide_llm_selection_decision_support | 5.1.2.1, 5.1.3.1, 5.1.6.2, 5.1.6.3, 5.3.1.1 |
| `unstable_pairs(candidates, criteria, today) -> set of frozenset pairs` | provide_llm_selection_decision_support | 5.1.4.1 |
| `generate_decision_record(selection) -> record` | provide_llm_selection_decision_support | 5.1.3.2 |
| `store_decision_record(record) -> id`, `retrieve_decision_record(id)` | provide_llm_selection_decision_support | 5.1.3.3, 5.1.5.1 |
| `rerun_decision(record_id, candidates, today) -> rank result` | provide_llm_selection_decision_support | 5.1.5.2 |
| `validate_criterion(criterion)` (raises ValueError) | provide_llm_selection_decision_support | 5.1.6.1 |
| `monthly_cost(candidate, requests_per_day, input_tokens, output_tokens) -> float` | provide_llm_selection_decision_support | 5.2.1.1 |
| `tradeoff_summaries(result) -> {model_id: {other_id: {"gains", "gives_up"}}}` | provide_llm_selection_decision_support | 5.2.2.1 |
| `risk_report(candidate) -> {"vendor_dependence", "switching_cost", "deprecation_risk"}` | provide_llm_selection_decision_support | 5.2.3.1 |
| `over_capability(result, candidates, criteria, usage) -> {model_id: premium_usd}` | provide_llm_selection_decision_support | 5.2.4.1 |

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
12. Section 2: AA-Omniscience is dropped, but SCENARIO_01's `factual_reliability`
    criterion (weight 0.4) and its expected output use it. Pick a replacement
    metric or keep the stored figure for that fixture.

## 6. System requirements (SRD section 3, generated from the IDEF0)

Generated by the Innoslate Generate Requirements script on the IDEF0-A0 of F.1
Provide LLM Selection Decision Support. Statements are verbatim and unedited (SRD
Tables 3-6). The verification method and criterion come from SRD Table 9, the MOP
target from Table 10, and the StR trace from Table 8. Each requirement is satisfied
by F.1. Input and output requirements are also satisfied by the input/output and by
the function at its other end.

| ID | Statement | Satisfied by (besides F.1) | Traces to StR |
|---|---|---|---|
| 1.1.1 | The LLM Compass shall accept Confirmed criteria mapping from the Technical Lead. | Confirmed criteria mapping; F.6 | 5.1.6.1 |
| 1.1.2 | The LLM Compass shall accept Model data with provenance from the Benchmark Data Sources. | Model data with provenance; F.7 | 5.1.2.1 |
| 1.1.3 | The LLM Compass shall accept Model selection from the Technical Lead. | Model selection; F.6 | 5.1.3.2 |
| 1.1.4 | The LLM Compass shall accept Proposed criteria from the Language model runtime. | Proposed criteria; F.8 | 5.1.1.2 |
| 1.1.5 | The LLM Compass shall accept Stated requirements from the Technical Lead. | Stated requirements; F.6 | 5.1.1.1 |
| 1.2.1 | The LLM Compass shall provide Data request to the Benchmark Data Sources. | Data request; F.7 | 5.3.1.1 |
| 1.2.2 | The LLM Compass shall provide Decision record to the Technical Lead. | Decision record; F.6 | 5.1.3.2 |
| 1.2.3 | The LLM Compass shall provide Interpretation request to the Language model runtime. | Interpretation request; F.8 | 5.1.1.2 |
| 1.2.4 | The LLM Compass shall provide Presented mapping to the Technical Lead. | Presented mapping; F.6 | 5.1.1.3 |
| 1.2.5 | The LLM Compass shall provide Presented ranking and sensitivity to the Technical Lead. | Presented ranking and sensitivity; F.6 | 5.1.3.1, 5.1.4.1 |
| 1.3.1 | The LLM Compass shall interface with the Technical Lead through the Requirements and recommendations. | C.1, C.6, conduit | 5.1.1.1 |
| 1.3.2 | The LLM Compass shall interface with the Language model runtime through the Interpretation request and proposed criteria. | C.1, C.8, conduit | 5.1.1.2 |
| 1.3.3 | The LLM Compass shall interface with the Benchmark Data Sources through the Data request and model data with provenance. | C.1, C.7, conduit | 5.1.2.1 |
| 1.4.1 | The LLM Compass shall provide LLM selection decision support. | - | 5.1, 5.2, 5.3 (spider diagram, 2026-10-26); 5.1.2.2, 5.1.5.1, 5.1.5.2, 5.1.6.2, 5.1.6.3, 5.2.x only through this one until 1.4.1.x are traced |

Verification (SRD Table 9) and MOP with target (Table 10), all verbatim:

| ID | Method | Verification criterion | MOP | Target |
|---|---|---|---|---|
| 1.1.1 | T | Every criterion in a submitted mapping is accepted with its hard or weighted designation. A weighted criterion without a weight is rejected. | % of confirmed criteria with a valid designation (and a weight, if weighted) | 100% |
| 1.1.2 | T | Every figure received is stored with a non-null source and collection date. A figure missing either one is rejected when it is entered. | % of received figures that carry a source and collection date | 100% |
| 1.1.3 | T | The candidate the Technical Lead selects appears unchanged in the decision record. | % of selections recorded unchanged | 100% |
| 1.1.4 | T | For each requirement in the reference set, a response is accepted only if it has at least one criterion or reports no suitable proxy, uses known metrics, and rates every criterion's proxy strength. An invalid response is retried once, then marked as an interpretation failure. | % of requirements that end with valid criteria, a no-proxy result, or an explicit interpretation-failure flag | 100% |
| 1.1.5 | T | Non-empty plain-language text is accepted and given an ID without reformatting. Empty input is rejected. | % of non-empty plain-language requirements accepted without reformatting | 100% |
| 1.2.1 | T | In a catalog of at least 10 candidates, a data request is issued for every candidate. | Number of candidates whose data is requested in one comparison | ≥ 10 |
| 1.2.2 | T | Every completed selection produces a record with all six sections filled in (requirements, mapping, weights, evidence, ranking, sensitivity, selection), and every evidence item has a source and date. | Number of record sections completed per selection | 7 of 7, for 100% of selections |
| 1.2.3 | T | Exactly one interpretation request is issued for each stated requirement, carrying its ID and unaltered text. | % of stated requirements sent for interpretation | 100% |
| 1.2.4 | I | Every presented criterion shows the requirement it stands for and a rating of strong, moderate or weak. | % of presented criteria with a proxy-strength rating | 100% |
| 1.2.5 | T, A | Each ranked candidate shows one contribution entry per weighted criterion. On a fixture with a known answer, the reported unstable pairs exactly match those found by changing each weight by −10% and +10%, one at a time. | Weight change covered by the sensitivity check; missed or false unstable pairs | ±10% on any single weight; 0 |
| 1.3.1 | D | The Technical Lead completes UC.1, from stated requirements to decision record, entirely through the system's interface. | Number of UC.1 exchanges with the Technical Lead supported | 6 of 6 |
| 1.3.2 | T | Every request and response conforms to the language model runtime's model contract, and a timeout is handled the same way as an invalid response. | Interpretation response time per requirement | To be set after the local runtime is benchmarked |
| 1.3.3 | T | Every data exchange conforms to the data contract. If the source is unavailable, the ranking uses the last stored figures, each shown with its date and staleness flag. | % of data exchanges that conform to the data contract | 100% |
| 1.4.1 | D | All leaf-level requirements pass, and a timed walkthrough of UC.1 with at least 10 candidates takes 30 minutes or less. | Operator time for a complete comparison | ≤ 30 min with ≥ 10 candidates |

Note: 1.2.2's criterion says "six sections" but lists seven, and its MOP says 7 of
7. Its parent StR 5.1.3.2 (section 1) has six sections, without the selection. Tests
use the seven listed. The model should be corrected, and the team should decide
whether the selection becomes a seventh section of 5.1.3.2 (Chapter 5 finding).

### Functional requirements from the F.1 decomposition (IDEF0 A1, 2026-10-26)

F.1 is now decomposed into F.1.1-F.1.7, and 1.4.1 into one requirement per
sub-function (functions-requirements spider diagram). The SRD export of
2026-10-26 doesn't contain them yet. The team said to use the diagrams as the
main reference, so the rows below are derived, not exported:
- **Statement:** the Innoslate script's pattern for 1.4.1.
- **Satisfied by:** matched by name. The spider diagram shows no satisfied-by
  link for 1.4.1.x yet.
- **StR trace:** from SRD Table 8 (StRs covered "1.4.1 only") and the A1 arrows.
  The SRD names 5.1.6.2 and 5.1.2.2 as examples, and says the 5.2.x StRs are
  expected under Function 6. 1.4.1.7 -> 5.1.3.3 is a team decision (2026-10-26).
- **Verification criterion:** the traced StRs' acceptance criteria, applied at
  the sub-function's own ICOMs.

Replace the rows with the exported text once it exists.

| ID | Statement (derived) | Satisfied by | Traces to StR |
|---|---|---|---|
| 1.4.1.1 | The LLM Compass shall propose criteria mapping. | F.1.1 | 5.1.1.2, 5.1.1.3, 5.1.6.1 |
| 1.4.1.2 | The LLM Compass shall retrieve model data. | F.1.2 | 5.1.2.1, 5.1.2.2, 5.3.1.1 |
| 1.4.1.3 | The LLM Compass shall apply hard constraints. | F.1.3 | 5.1.6.2, 5.1.6.3 |
| 1.4.1.4 | The LLM Compass shall score and rank candidates. | F.1.4 | 5.1.3.1 |
| 1.4.1.5 | The LLM Compass shall analyze ranking sensitivity. | F.1.5 | 5.1.4.1 |
| 1.4.1.6 | The LLM Compass shall report selection rationale. | F.1.6 | 5.1.2.1, 5.1.3.1, 5.1.4.1, 5.1.6.3, 5.2.1.1-5.2.4.1 |
| 1.4.1.7 | The LLM Compass shall generate and store decision record. | F.1.7 | 5.1.3.2, 5.1.3.3 |

5.1.5.1 and 5.1.5.2 still have no system requirement: there is no retrieval or
re-run input on the IDEF0 yet. Their tests are strict xfail
(docs/traceability.md).

| ID | Method | Verification criterion (derived) | MOP | Target |
|---|---|---|---|---|
| 1.4.1.1 | T | A confirmed mapping is split by designation: every weighted criterion goes to the weighted criteria, every hard one to the hard constraints, and the required metrics are the metrics of both, each once. A weighted criterion without a weight, or a metric not on the known metrics list, is rejected. | % of confirmed criteria routed by designation | 100% |
| 1.4.1.2 | T | The data request covers every catalog candidate and every required metric. Every received figure keeps its source and date and is flagged stale when older than the staleness threshold (at 90 days: 91 days old is stale, 90 is not). A figure with no source or date is rejected. | % of received figures with a correct stale flag | 100% |
| 1.4.1.3 | T | In a fixture where the top-scoring candidate fails a hard constraint, it is not eligible. Each excluded candidate lists at least one failed constraint ID, and missing data for a hard constraint excludes with `missing_data:<field>`. | % of failing candidates excluded with a reason | 100% |
| 1.4.1.4 | T | Each ranked candidate has one contribution per weighted criterion, its score is the sum of its contributions, and candidates are in descending score order. On the known-answer fixture the order is model-1, model-2, model-3. | % of ranked candidates with a full contribution breakdown | 100% |
| 1.4.1.5 | T, A | On a fixture with a known answer, the unstable pairs exactly match those found by applying each sensitivity-policy factor (x0.9, x1.1) to each weight, one at a time. A policy with no change finds no unstable pairs. | Missed or false unstable pairs | 0 |
| 1.4.1.6 | T | The presented ranking and sensitivity shows every figure used with its source, date and stale flag, every excluded candidate with its failed constraints, and the unstable pairs. The selection rationale carries the same ranking, exclusions, evidence and sensitivity finding. The 5.2.x StRs are verified by their own tests (tests/test_product_owner.py). | % of figures shown with source, date and stale flag | 100% |
| 1.4.1.7 | T | A record generated from a selection rationale and a model selection has all seven sections, with the selection unchanged. The stored record retrieved by its ID matches the original, including after a restart (module reload). A selection that isn't in the ranking is rejected. | % of records retrievable unchanged after a restart | 100% |

F.1's boundary changed with the decomposition (IDEF0 A-0 of F.1, 2026-10-26):
Confirmed criteria mapping is now an input, not a control. Known metrics list,
Staleness threshold and Sensitivity policy are new controls. The 1.1.x-1.3.x
statements above are unchanged until the regenerated SRD says otherwise.
