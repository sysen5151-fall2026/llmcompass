# Traceability

Links each module to the IDEF0 function it implements (Metafunction IDEF0, SRD
§2.3, Fig. 2), and each function to the system requirements it satisfies (SRD §3,
SPEC.md §6), the stakeholder requirement and need they trace to (SRD Table 8,
SPEC.md §1), and the test that verifies them (tests/test_system_requirements.py).

## Functions and modules

| Function ID | Function Name | Mechanism | Module | Body |
|---|---|---|---|---|
| F.1 | Provide LLM Selection Decision Support | C.1 LLM Compass | backend/provide_llm_selection_decision_support/ | Chapter 5 |
| F.2 | Define Application Technical Needs | C.2 Application Developer | backend/define_application_technical_needs/ | pending, no system requirement |
| F.3 | Define Budget Constraints | C.3 Budget Owner | backend/define_budget_constraints/ | pending, no system requirement |
| F.4 | Define Compliance Constraints | C.4 Compliance Officer | backend/define_compliance_constraints/ | pending, no system requirement |
| F.5 | Define Product Needs and Priorities | C.5 Product Owner | backend/define_product_needs_and_priorities/ | pending, no system requirement |
| F.6 | Provide Technical Decision Oversight | C.6 Technical Lead | backend/provide_technical_decision_oversight/ | pending (human mechanism) |
| F.7 | Provide Benchmark Evidence | C.7 Benchmark Data Sources | backend/provide_benchmark_evidence/ | Chapter 5 (stored catalog) |
| F.8 | Provide Requirement Interpretation | C.8 Language model runtime | backend/provide_requirement_interpretation/ | pending (needs LM Studio, ADR-0001) |

`backend/app.py` has no row. It isn't a function on the IDEF0: it calls the
functions in UC.1 order, like the kiosk's `kiosk_service`.

ICOM-to-signature mapping: docs/PLAN.md, "Module decomposition from the IDEF0".

## Requirements, needs and tests

Every requirement is satisfied by F.1 (SRD Fig. 6). An input or output
requirement is also satisfied by the function at the other end of its arrow,
shown in the second column. "Status" is the state of the test in this build (2026-10-22: 11 of 14 pass).

| Requirement | Functions (def) | StR | Need | Test | Status |
|---|---|---|---|---|---|
| SR 1.1.1 | F.1 `request_benchmark_evidence`; F.6 | 5.1.6.1 | SN-TL-07 | test_SR_1_1_1_accepts_designated_criteria_rejects_weighted_without_weight | pass |
| SR 1.1.2 | F.1 `present_ranking_and_sensitivity`; F.7 | 5.1.2.1 | SN-TL-02 | test_SR_1_1_2_figures_stored_with_source_and_date_unsourced_rejected | pass |
| SR 1.1.3 | F.1 `record_decision`; F.6 | 5.1.3.2 | SN-TL-09 | test_SR_1_1_3_selection_appears_unchanged_in_record | pass |
| SR 1.1.4 | F.1 `present_criteria_mapping`; F.8 | 5.1.1.2 | SN-TL-01 | test_SR_1_1_4_reference_responses_accepted_or_retried_then_flagged | pass |
| SR 1.1.5 | F.1 `request_interpretation`; F.6 | 5.1.1.1 | SN-TL-01 | test_SR_1_1_5_text_gets_id_without_reformatting_empty_rejected | pass |
| SR 1.2.1 | F.1 `request_benchmark_evidence`; F.7 `provide_model_data` | 5.3.1.1 | SN-TL-08 | test_SR_1_2_1_data_request_issued_for_every_candidate_in_catalog_of_10 | fail: stored catalog has 3 models, needs 10 (data gap) |
| SR 1.2.2 | F.1 `record_decision`; F.6 | 5.1.3.2 | SN-TL-09 | test_SR_1_2_2_record_has_seven_sections_and_sourced_evidence | pass |
| SR 1.2.3 | F.1 `request_interpretation`; F.8 | 5.1.1.2 | SN-TL-01 | test_SR_1_2_3_one_request_per_requirement_with_id_and_unaltered_text | pass |
| SR 1.2.4 | F.1 `present_criteria_mapping`; F.6 | 5.1.1.3 | SN-TL-01 | test_SR_1_2_4_presented_criterion_shows_requirement_and_strength | pass |
| SR 1.2.5 | F.1 `present_ranking_and_sensitivity`; F.6 | 5.1.3.1, 5.1.4.1 | SN-TL-04, SN-TL-05, SN-PO-05 | test_SR_1_2_5_contributions_and_unstable_pairs_match_known_answer | pass |
| SR 1.3.1 | F.1 web interface (C.1-C.6 conduit) | 5.1.1.1 | SN-TL-01 | test_SR_1_3_1_uc1_walkthrough_through_interface_logged | fail: no full_comparison walkthrough logged; web confirm/select steps pending |
| SR 1.3.2 | F.1 <-> F.8 conduit | 5.1.1.2 | SN-TL-01 | test_SR_1_3_2_model_contract_conformance_and_timeout_as_invalid | pass (F.1 side; F.8 body pending) |
| SR 1.3.3 | F.1 <-> F.7 conduit; F.7 `provide_model_data` | 5.1.2.1 | SN-TL-02 | test_SR_1_3_3_data_contract_and_stored_figures_shown_dated_and_flagged | pass |
| SR 1.4.1 | F.1 (whole) | all | all | test_SR_1_4_1_full_comparison_walkthrough_within_30_minutes | fail: no walkthrough logged; catalog < 10 |

F.2-F.5 satisfy no system requirement. Their exchanges with F.6 don't cross the
LLM Compass boundary, so the Innoslate script generated none (SRD §3.2). F.6
appears above only as the other end of F.1's arrows.
