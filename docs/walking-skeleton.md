UC.1 -- Technical Lead selects a model for an application
1. Technical Lead -> LLM Compass: UC.1.2 Technical Lead enters requirements and constraints
2. Technical Lead -> Language model runtime: UC.1.3 Submit requirements for interpretation
3. Language model runtime -> LLM Compass: UC.1.4 Interpret requirements and propose criteria
4. LLM Compass -> Technical Lead: UC.1.6 Present proposed mapping for review
5. Technical Lead -> LLM Compass: UC.1.9 Confirm the mapping
6. Technical Lead -> Benchmark Data Sources: UC.1.10 Request model data
7. Benchmark Data Sources -> LLM Compass: UC.1.11 Retrieve model specification and benchmark data
8. LLM Compass -> Technical Lead: UC.1.16 Present sensitivity finding
9. Technical Lead -> LLM Compass: UC.1.17 Review recommendation and select a model
10. LLM Compass -> Technical Lead: UC.1.18 Generate decision record

Notes:
- Steps 6-7 and steps 2-3 came from a leader-line label in Innoslate rather than a plain label directly under the arrow. Numeric order and the asset descriptions both point the same way, but worth a quick look at the diagram to confirm.
- Technical Lead still calls Language model runtime (step 2) and Benchmark Data Sources (step 6) directly rather than through LLM Compass. Language model runtime's own description ("external API that receives a stated requirement and returns proposed measurable criteria") supports this being intentional. "Confirm the mapping" (step 5) now correctly routes through LLM Compass, unlike the prior version of this diagram.
