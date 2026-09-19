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
- Corrected against the actual Innoslate sequence diagram (`UC.1 Technical Lead selects a model for an application.png`): steps 2 and 6 were previously attributed to Technical Lead calling Language model runtime / Benchmark Data Sources directly. The diagram shows both calls originate from LLM Compass instead — Technical Lead never talks to either external system directly. The prior version's bypass reading was wrong.
- Language model runtime is LLM Compass's own requirement-interpretation engine (the local model from ADR-0001), not a vendor-spec/pricing feed — it receives a stated requirement and returns proposed criteria (UC.1.3/UC.1.4). Vendor pricing/spec data lives entirely in Benchmark Data Sources (UC.1.11 returns "model specification and benchmark data" together).
