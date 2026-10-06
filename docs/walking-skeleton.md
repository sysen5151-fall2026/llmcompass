UC.1 -- Technical Lead selects a model for an application
1. Technical Lead -> LLM Compass: UC.1.2 Technical Lead enters requirements and constraints
2. LLM Compass -> Language model runtime: UC.1.3 Submit requirements for interpretation
3. Language model runtime -> LLM Compass: UC.1.4 Interpret requirements and propose criteria
4. LLM Compass -> Technical Lead: UC.1.6 Present proposed mapping for review
5. Technical Lead -> LLM Compass: UC.1.9 Confirm the mapping
6. LLM Compass -> Benchmark Data Sources: UC.1.10 Request model data
7. Benchmark Data Sources -> LLM Compass: UC.1.11 Retrieve model specification and benchmark data
8. LLM Compass -> Technical Lead: UC.1.16 Present sensitivity finding
9. Technical Lead -> LLM Compass: UC.1.17 Review recommendation and select a model
10. LLM Compass -> Technical Lead: UC.1.18 Generate decision record

Notes:
- See docs/context.md for what each external system sends and receives.
- The typed text (UC.1.2) must exactly match a `user_input` in sample_data/user_inputs.json. Each later stub returns its own section of that scenario's record from sample_data/expected_outputs.json: UC.1.3/1.4 `interpreted_requirements`, UC.1.16 `comparison_result`, UC.1.17 `selection_result`, UC.1.18 `decision_record`. See docs/PLAN.md.
- The Benchmark Data Sources stub (UC.1.10/1.11) loads sample_data/model_spec.json, providers.json and benchmark.json as they are. It does not return the SPEC.md section 2 figure shape yet. The Language model runtime and decision-record stubs don't match the SPEC.md contracts on purpose, so the acceptance tests can't pass on hard-coded stubs.
