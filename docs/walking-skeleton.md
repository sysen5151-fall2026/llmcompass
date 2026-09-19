UC.1 -- Technical Lead selects a model for an application
1. Technical Lead -> Language model runtime: UC.1.2 Technical Lead enters requirements and constraints
2. Language model runtime -> LLM Compass: return (unlabeled in the Innoslate model)
3. LLM Compass -> Technical Lead: UC.1.3 Interpret requirements and propose criteria
4. LLM Compass -> Technical Lead: UC.1.5 Present proposed mapping for review
5. Technical Lead -> Benchmark Data Sources: UC.1.8 Confirm the mapping
6. Benchmark Data Sources -> LLM Compass: return (unlabeled in the Innoslate model)
7. LLM Compass -> Technical Lead: UC.1.9 Retrieve model specification and benchmark data
8. LLM Compass -> Technical Lead: UC.1.14 Present sensitivity finding
9. Technical Lead -> LLM Compass: UC.1.15 Review recommendation and select a model
10. LLM Compass -> LLM Compass (self): UC.1.16 Generate decision record

Notes:
- Steps 2 and 6 have no label in the Innoslate diagram. Add return descriptions there before this is done.
- Steps 1 and 5 target Language model runtime and Benchmark Data Sources directly, bypassing LLM Compass. That conflicts with docs/context.md, where the Technical Lead only ever talks to LLM Compass. Check the lifeline targets in Innoslate.
