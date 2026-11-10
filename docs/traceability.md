# Traceability

Links each module to the IDEF0 function it implements (Metafunction IDEF0, SRD
§2.3, Fig. 2), and each function to the system requirements it satisfies (SRD §3,
SPEC.md §6), the stakeholder requirement and need they trace to (SRD Table 8,
SPEC.md §1), and the test that verifies them (tests/test_system_requirements.py).

## Functions and modules

| Function ID | Function Name | Mechanism | Module | Body |
|---|---|---|---|---|
| F.1 | Provide LLM Selection Decision Support | C.1 LLM Compass | backend/provide_llm_selection_decision_support/ | Chapter 5 |
| F.2 | Define Application Technical Needs | C.2 Application Developer | backend/define_application_technical_needs/ | none: no system requirement (stub removed 2026-10-25) |
| F.3 | Define Budget Constraints | C.3 Budget Owner | backend/define_budget_constraints/ | none: no system requirement (stub removed 2026-10-25) |
| F.4 | Define Compliance Constraints | C.4 Compliance Officer | backend/define_compliance_constraints/ | none: no system requirement (stub removed 2026-10-25) |
| F.5 | Define Product Needs and Priorities | C.5 Product Owner | backend/define_product_needs_and_priorities/ | none: no system requirement (stub removed 2026-10-25) |
| F.6 | Provide Technical Decision Oversight | C.6 Technical Lead | backend/provide_technical_decision_oversight/ | pending (human mechanism) |
| F.7 | Provide Benchmark Evidence | C.7 Benchmark Data Sources | backend/provide_benchmark_evidence/ | Chapter 5 (stored catalog) |
| F.8 | Provide Requirement Interpretation | C.8 Language model runtime | backend/provide_requirement_interpretation/ | pending (needs LM Studio, ADR-0001) |

F.1 is decomposed into F.1.1-F.1.7 (IDEF0 A1, 2026-10-26; docs/PLAN.md "F.1
decomposition"). Each is matched by name to 1.4.1.x with the same last digit (SPEC §6). The
satisfied-by links aren't in the spider diagram yet.
All seven have their modules (F.1.7 on 2026-10-26, the rest on 2026-10-28). F.1's
`__init__` keeps the boundary ICOM defs, which compose them.

| Function ID | Function Name | Requirement | Module (in backend/provide_llm_selection_decision_support/) |
|---|---|---|---|
| F.1.1 | Propose Criteria Mapping | 1.4.1.1 | propose_criteria_mapping (built 2026-10-28) |
| F.1.2 | Retrieve Model Data | 1.4.1.2 | retrieve_model_data (built 2026-10-28) |
| F.1.3 | Apply Hard Constraints | 1.4.1.3 | apply_hard_constraints (built 2026-10-28) |
| F.1.4 | Score and Rank Candidates | 1.4.1.4 | score_and_rank_candidates (built 2026-10-28) |
| F.1.5 | Analyze Ranking Sensitivity | 1.4.1.5 | analyze_ranking_sensitivity (built 2026-10-28) |
| F.1.6 | Report Selection Rationale | 1.4.1.6 | report_selection_rationale (built 2026-10-28) |
| F.1.7 | Generate and Store Decision Record | 1.4.1.7 | generate_and_store_decision_record (built 2026-10-26) |

Entry points (routes, launcher) are mapped to use cases in docs/route-table.md.
`backend/app.py` has no row. It isn't a function on the IDEF0: it calls the
functions in UC.1 order, like the kiosk's `kiosk_service`.

ICOM-to-signature mapping: docs/PLAN.md, "Module decomposition from the IDEF0".
Internal flows between F.1.1-F.1.7: contracts/api-v1.yaml (operation per exchange,
`x-module` names the module above). `compile_decision_basis` (F.1.1) carries the
team's flow 5.4 Decision basis to F.1.7 (ADR-0002).

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
| SR 1.2.1 | F.1 `request_benchmark_evidence`; F.7 `provide_model_data` | 5.3.1.1 | SN-TL-08 | test_SR_1_2_1_data_request_issued_for_every_candidate_in_catalog_of_10 | fail in file mode (stored catalog has 3 models); pass in api mode on the live snapshot of 2026-11-03 (14 models) |
| SR 1.2.2 | F.1 `record_decision`; F.6 | 5.1.3.2 | SN-TL-09 | test_SR_1_2_2_record_has_seven_sections_and_sourced_evidence | pass |
| SR 1.2.3 | F.1 `request_interpretation`; F.8 | 5.1.1.2 | SN-TL-01 | test_SR_1_2_3_one_request_per_requirement_with_id_and_unaltered_text | pass |
| SR 1.2.4 | F.1 `present_criteria_mapping`; F.6 | 5.1.1.3 | SN-TL-01 | test_SR_1_2_4_presented_criterion_shows_requirement_and_strength | pass |
| SR 1.2.5 | F.1 `present_ranking_and_sensitivity`; F.6 | 5.1.3.1, 5.1.4.1 | SN-TL-04, SN-TL-05, SN-PO-05 | test_SR_1_2_5_contributions_and_unstable_pairs_match_known_answer | pass |
| SR 1.3.1 | F.1 web interface (C.1-C.6 conduit) | 5.1.1.1 | SN-TL-01 | test_SR_1_3_1_uc1_walkthrough_through_interface_logged | fail: no full_comparison walkthrough logged; web review/confirm built 2026-11-03 (tests/test_mapping_review_ui.py), select (UC.1.17) pending |
| SR 1.3.2 | F.1 <-> F.8 conduit; F.8 `propose_criteria` (LM Studio adapter, Lab Manual 8.5) | 5.1.1.2 | SN-TL-01 | test_SR_1_3_2_model_contract_conformance_and_timeout_as_invalid | pass |
| SR 1.3.3 | F.1 <-> F.7 conduit; F.7 `provide_model_data`, `refresh_model_data` (snapshot fallback) | 5.1.2.1 | SN-TL-02 | test_SR_1_3_3_data_contract_and_stored_figures_shown_dated_and_flagged; tests/test_data_access_component.py | pass |
| SR 1.4.1 | F.1 (whole) | all | all | test_SR_1_4_1_full_comparison_walkthrough_within_30_minutes | fail: no walkthrough logged; catalog < 10 |

Requirements 1.4.1.1-1.4.1.7 are derived from the diagrams, not exported (SPEC §6).

| Requirement | Function | StR | Test | Status |
|---|---|---|---|---|
| SR 1.4.1.1 | F.1.1 | 5.1.1.2, 5.1.1.3, 5.1.6.1 | test_SR_1_4_1_1_confirmed_mapping_split_by_designation_unknown_metric_rejected | pass |
| SR 1.4.1.2 | F.1.2 | 5.1.2.1, 5.1.2.2, 5.3.1.1 | test_SR_1_4_1_2_data_request_covers_catalog_figures_flagged_stale_unsourced_rejected | pass |
| SR 1.4.1.3 | F.1.3 | 5.1.6.2, 5.1.6.3 | test_SR_1_4_1_3_top_scorer_failing_hard_constraint_excluded_with_reason | pass |
| SR 1.4.1.4 | F.1.4 | 5.1.3.1 | test_SR_1_4_1_4_contributions_sum_to_score_in_known_order | pass |
| SR 1.4.1.5 | F.1.5 | 5.1.4.1 | test_SR_1_4_1_5_unstable_pairs_match_known_answer_under_policy | pass |
| SR 1.4.1.6 | F.1.6 | 5.1.2.1, 5.1.3.1, 5.1.4.1, 5.1.6.3, 5.2.x | test_SR_1_4_1_6_report_shows_sourced_dated_flagged_figures_exclusions_and_pairs | pass |
| SR 1.4.1.7 | F.1.7 | 5.1.3.2, 5.1.3.3 | test_SR_1_4_1_7_record_has_seven_sections_and_is_retrievable_after_restart | pass |

Control input requirements and system-wide requirements (Lab Manual 8.5, 2026-11-03; SPEC §6).
Each is satisfied by C.1; the "Element" column is the Form report Table 4 allocation.

| Requirement | Element / def | StR | Test | Status |
|---|---|---|---|---|
| SR 1.1.6 | F.1 `staleness_threshold` control | 5.1.2.2 | test_SR_1_1_6_staleness_threshold_90_days_flags_only_older_figures | pass |
| SR 1.1.7 | F.1 `sensitivity_policy` control | 5.1.4.1 | test_SR_1_1_7_sensitivity_policy_value_changes_variation_default_is_10_percent | pass |
| SR 1.1.8 | F.1 `known_metrics` control | 5.1.1.2 | test_SR_1_1_8_criterion_off_known_metrics_list_rejected_on_list_accepted | pass |
| SR 2.1.1 | whole system; C.1.1, C.1.2 | 5.3.1.1 | test_SR_2_1_1_full_comparison_walkthroughs_within_30_minutes | fail: no walkthrough logged; catalog < 10 in file mode |
| SR 2.1.2 | C.1.7, C.1.3-C.1.5 | 5.1.5.2 | test_SR_2_1_2_rerun_walkthroughs_within_10_minutes | fail: no rerun walkthrough logged |
| SR 2.1.3 | C.1.3-C.1.5 | 5.1.3.2 | test_SR_2_1_3_five_runs_with_unchanged_inputs_give_identical_ranking | pass |
| SR 2.1.4 | C.1.7 (SQLite, ADR-0005) | 5.1.3.3 | test_SR_2_1_4_records_stored_in_sqlite_and_retrievable_after_session_ends | pass (six months not simulated) |
| SR 2.1.5 | C.1.2, C.1.6, C.1.7 | 5.1.2.1 | test_SR_2_1_5_displayed_and_exported_figures_carry_source_and_date | pass |
| SR 2.1.6 | C.1.6 | 5.2.2.1 | none | not verifiable: restricted term list to be defined |
| SR 2.2.1 | C.1.1.1 / F.8 adapter `runtime_config` | 5.1.1.2 | test_SR_2_2_1_interpretation_requests_sent_to_local_runtime | pass |
| SR 2.3.1 | C.1.1.1, C.1.1.2 / F.8 adapter | 5.1.1.2 | test_SR_2_3_1_runtime_requests_and_responses_conform_to_model_contract | pass |
| SR 2.3.2 | C.1.2 / F.7 data access | 5.1.2.1 | test_SR_2_3_2_data_exchanges_conform_to_data_contract | pass |
| SR 2.4.1 | C.1.1.1 / F.8 adapter | 5.2.1.1 | test_SR_2_4_1_no_paid_external_calls_per_comparison | pass |

## C.1.1 Criteria Mapper component requirements (SPEC §7, Lab Manual 9.4)

Module per second-level function (F.1.1.n is performed by component C.1.1.n): `backend/provide_llm_selection_decision_support/propose_criteria_mapping/`
(`request_interpretation.py` C.1.1.1, `validate_proposed_criteria.py` C.1.1.2,
`present_criteria_mapping.py` C.1.1.3, `distribute_confirmed_mapping.py` C.1.1.4). Tests in
`tests/test_functional_requirements.py` (from spec) and
`tests/test_component_criteria_mapper_reconcile.py` (reconcile fixes, docs/deviation-log.md).
C.1.1.4 imports C.1.1.2's known-metrics and threshold helpers (deviation log D-20).

| Function ID | Module (in backend/provide_llm_selection_decision_support/propose_criteria_mapping/) | Requirement | Element / def | Test | Status |
|---|---|---|---|---|---|
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.1.1 | C.1.1.4 distribute_confirmed_mapping | test_CR_1_1_1_confirmed_mapping_of_each_scenario_accepted_and_passed_on<br>test_CR_1_1_1_criterion_without_valid_designation_or_weight_rejected | pass |
| F.1.1.2<br>F.1.1.4 | validate_proposed_criteria.py<br>distribute_confirmed_mapping.py | CR 1.1.2 | C.1.1.2, C.1.1.4 (known_metrics) | test_CR_1_1_2_changing_known_metrics_list_changes_validation_results | pass |
| F.1.1.2 | validate_proposed_criteria.py | CR 1.1.3 | C.1.1.2 validate_proposed_criteria | test_CR_1_1_3_runtime_proposal_accepted_for_each_scenario<br>test_CR_1_1_3_no_suitable_proxy_response_accepted | pass |
| F.1.1.1 | request_interpretation.py | CR 1.1.4 | C.1.1.1 request_interpretation | test_CR_1_1_4_stated_requirements_of_each_scenario_accepted<br>test_CR_1_1_4_empty_or_non_text_requirements_rejected | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.2.1 | C.1.1.4 (5.4 Decision basis) | test_CR_1_2_1_exported_record_holds_decision_basis_per_scenario | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.2.2 | C.1.1.4 (5.2) | test_CR_1_2_2_hard_constraints_delivered_to_constraint_filter | pass |
| F.1.1.1 | request_interpretation.py | CR 1.2.3 | C.1.1.1 | test_CR_1_2_3_one_request_per_stated_requirement_with_id_and_text | pass |
| F.1.1.3 | present_criteria_mapping.py | CR 1.2.4 | C.1.1.3 present_criteria_mapping | test_CR_1_2_4_presented_mapping_walkthrough_logged_per_scenario<br>test_CR_1_2_4_presented_mapping_shows_each_stated_requirement_with_its_criteria | pass (walkthroughs 2026-11-10, SCENARIO_01–04, 1 min each) |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.2.5 | C.1.1.4 (5.1) | test_CR_1_2_5_required_metrics_delivered_to_evidence_retriever | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.2.6 | C.1.1.4 (5.3) | test_CR_1_2_6_ranking_engine_and_sensitivity_analyzer_receive_identical_weights | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.3.1 | C.1.1.4 → C.1.7 | test_CR_1_3_1_decision_basis_exchanged_with_decision_recorder | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.3.2 | C.1.1.4 → C.1.5 | test_CR_1_3_2_weighted_criteria_exchanged_with_sensitivity_analyzer | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.3.3 | C.1.1.4 → C.1.4 | test_CR_1_3_3_weighted_criteria_exchanged_with_ranking_engine | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.3.4 | C.1.1.4 → C.1.3 | test_CR_1_3_4_hard_constraints_exchanged_with_constraint_filter | pass |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.3.5 | C.1.1.4 → C.1.2 | test_CR_1_3_5_required_metrics_exchanged_with_evidence_retriever | pass |
| F.1.1.1<br>F.1.1.3<br>F.1.1.4 | request_interpretation.py<br>present_criteria_mapping.py<br>distribute_confirmed_mapping.py | CR 1.3.6 | C.1.1.1, C.1.1.3, C.1.1.4 / web UI | test_CR_1_3_6_technical_lead_walkthrough_logged_per_scenario | pass (walkthroughs 2026-11-10, SCENARIO_01–04, 1 min each) |
| F.1.1.1<br>F.1.1.2 | request_interpretation.py<br>validate_proposed_criteria.py | CR 1.3.7 | C.1.1.1 send_interpretation_request, C.1.1.2 | test_CR_1_3_7_runtime_exchanges_follow_model_contract<br>test_CR_1_3_7_timeout_handled_as_invalid_response | pass |
| F.1.1.2 | validate_proposed_criteria.py | CR 1.3.8 | C.1.1.2 configured_known_metrics | test_CR_1_3_8_configured_known_metrics_list_loaded<br>test_CR_1_3_8_metric_off_configured_list_rejected | pass |
| F.1.1.1 | request_interpretation.py | CR 1.4.1 | C.1.1.1 | test_CR_1_4_1_every_stated_requirement_gets_an_interpretation_request | pass |
| F.1.1.2 | validate_proposed_criteria.py | CR 1.4.2 | C.1.1.2 | test_CR_1_4_2_invalid_and_unknown_criteria_caught<br>test_CR_1_4_2_valid_response_after_one_retry_accepted<br>test_CR_1_4_2_retry_is_counted_per_requirement | pass |
| F.1.1.3 | present_criteria_mapping.py | CR 1.4.3 | C.1.1.3 | test_CR_1_4_3_mapping_presentation_walkthrough_logged_per_scenario<br>test_CR_1_4_3_every_presented_criterion_shows_its_rating_and_requirement | pass (walkthroughs 2026-11-10, SCENARIO_01–04, 1 min each) |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 1.4.4 | C.1.1.4 | test_CR_1_4_4_confirmed_mapping_reaches_all_five_downstream_subsystems<br>test_CR_1_4_4_unusable_confirmed_mapping_rejected | pass |
| F.1.1.3 | present_criteria_mapping.py | CR 2.1.1 | C.1.1.3 / web UI review page | test_CR_2_1_1_mapping_review_walkthrough_within_10_minutes | pass (walkthroughs 2026-11-10: 1 min each, target ≤ 10) |
| F.1.1.4 | distribute_confirmed_mapping.py | CR 2.1.2 | C.1.1.4 | test_CR_2_1_2_distributed_copies_identical_to_confirmed_mapping<br>test_CR_2_1_2_receivers_hold_the_confirmed_mapping_unmodified | pass |
| F.1.1.1 | request_interpretation.py | CR 2.2.1 | C.1.1.1 / F.8 runtime_config | test_CR_2_2_1_runtime_configuration_points_to_local_host | pass |
| F.1.1.1<br>F.1.1.2 | request_interpretation.py<br>validate_proposed_criteria.py | CR 2.3.1 | C.1.1.1, C.1.1.2 | test_CR_2_3_1_only_model_contract_responses_accepted<br>test_CR_2_3_1_requests_and_accepted_responses_conform | pass |
| F.1.1.1 | request_interpretation.py | CR 2.4.1 | C.1.1.1 / F.8 | test_CR_2_4_1_configuration_and_run_show_no_paid_calls | pass |

### Web UI (Milestone 2 wiring, 2026-11-03)

| Route | Traces | Test file | Status |
|---|---|---|---|
| POST / → review page | UC.1.2–UC.1.6; SR 1.3.1, SR 1.1.5, CR 1.2.4, CR 1.3.6, CR 1.4.3; SPEC 3 failure path | tests/test_mapping_review_ui.py | pass (fake runtime; live SCENARIO_02 checked by hand and by the verifier) |
| POST /confirm → result page | UC.1.7–UC.1.9, UC.1.10–UC.1.18; CR 1.1.1, CR 1.1.2, CR 1.4.4, CR 2.1.2; A27 | tests/test_mapping_review_ui.py | pass |

F.2-F.5 satisfy no system requirement. Their exchanges with F.6 don't cross the
LLM Compass boundary, so the Innoslate script generated none (SRD §3.2). F.6
appears above only as the other end of F.1's arrows.

## Stakeholder-requirement tests with no system requirement of their own

These tests (tests/test_technical_lead.py) verify a StR that the SRD's
traceability table covered only through SR 1.4.1. With F.1 decomposed (2026-10-26),
5.1.3.3 now traces to SR 1.4.1.7. Decided 2026-10-26 for the F.6
decision-record arrow, which has no output end on the IDEF0.

| StR | Test | Traces to | Status |
|---|---|---|---|
| 5.1.3.3 | test_SN_TL_06_5_1_3_3_stored_record_round_trips | SR 1.4.1.7 Generate and Store Decision Record (F.1.7) | pass |
| 5.1.5.1 | test_SN_TL_06_5_1_5_1_unknown_record_is_not_found | none yet: no retrieval request on the IDEF0 | XPASS (strict, fails the run): F.1.7's retrieve already reports not-found. Team decision pending |
| 5.1.5.2 | test_SN_TL_06_5_1_5_2_rerun_uses_current_data | none yet: no re-run request on the IDEF0 | xfail (strict) |
| 5.1.5.2 | test_SN_TL_06_5_1_5_2_rerun_walkthrough_within_10_minutes | none yet: no re-run request on the IDEF0 | xfail (strict) |

The xfail markers come off when the retrieval/re-run arrow is modeled and the
next SRD export generates its system requirement. Strict means an unexpected
pass fails the run, so a marker can't outlive the gap.
