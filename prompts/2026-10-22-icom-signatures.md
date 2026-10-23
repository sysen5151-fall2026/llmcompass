# ICOM signatures — component prompts (Lab Manual 4.4, Component Prompt Template)

One prompt per IDEF0 function group, each given to a separate generation agent.
Source of the ICOM tables: docs/PLAN.md "Module decomposition from the IDEF0",
transcribed from the SRD (Table 2, Fig. 2, §2.3).

## Shared sections (included in every prompt)

- **Context.** LLM Compass (C.1) helps a Technical Lead pick an LLM for an
  application: it turns stated requirements into measurable criteria, ranks
  candidate models on sourced data, checks how sensitive the ranking is, and
  writes a decision record. The modules below each implement one function from
  the Metafunction IDEF0 (F.1–F.8).
- **Constraints.** Python 3.12, standard library only, under `backend/`. Each
  module is `backend/<module>/__init__.py`. Do not modify any other file. Do not
  rename, change or remove any existing function, constant or import in an
  existing module: they implement SPEC.md §4 and are tested.
- **Translation (Lab Manual Table F-2).** Input -> positional parameter.
  Control -> keyword-only parameter after `*`. Output -> return value. The
  mechanism is the module itself: name it in the module docstring, never as a
  parameter. Body is exactly `raise NotImplementedError`.
- **Docstring per def** in the kiosk style, listing only that def's ICOMs, e.g.
  `"""in: x. control: y. out: z."""`. **Module docstring** states the function
  identifier and name it implements, and its mechanism, e.g.
  `"""Implements F.7 -- Provide Benchmark Evidence. Mechanism: C.7 Benchmark Data Sources."""`.
- **Success criteria.** The module imports. Every new def raises
  NotImplementedError. `pytest` still gives 29 passed and 19 failed. The
  signatures match the docs/PLAN.md "Signatures" table exactly: names, parameter
  order, the `*` placement, and the return annotation.
- **Output format.** Edit or create the file(s) only. No prose.
- **Out of scope.** No bodies, no validation, no error handling, logging,
  retries, defaults, or dependencies. No refactoring of neighbouring code. No
  new tests. Don't use the IDEF0 arrow names for anything other than parameter
  and return names.
- **Requirements.** 1.4.1 "The LLM Compass shall provide LLM selection decision
  support." (satisfied by F.1). Per-def SPEC IDs are cited in a trailing comment
  only where the def's exchange already has one in SPEC.md / docs/PLAN.md
  (e.g. UC.1.18 -> SN-TL-09 / 5.1.3.2). Don't add IDs that aren't there.

## Prompt 1 — F.1 Provide LLM Selection Decision Support

Module: `provide_llm_selection_decision_support` (existing; append the new defs
under a clearly marked section at the end, and put the "Implements F.1" docstring
at the top of the file above the existing header comments).

```
F.1 -- Provide LLM Selection Decision Support
  in:      stated_requirements (from F.6), proposed_criteria (from F.8),
           model_data_with_provenance (from F.7), model_selection (from F.6)
  control: confirmed_criteria_mapping (from F.6)
  out:     interpretation_request (to F.8), data_request (to F.7),
           presented_mapping (to F.6), presented_ranking_and_sensitivity (to F.6),
           decision_record (to F.6)
  mechanism: C.1 LLM Compass
```

The defs: `request_interpretation`, `present_criteria_mapping`,
`request_benchmark_evidence`, `present_ranking_and_sensitivity`,
`record_decision`, as in the docs/PLAN.md table.

## Prompt 2 — F.2–F.6 (stakeholder and Technical Lead functions)

Modules (new): `define_application_technical_needs`, `define_budget_constraints`,
`define_compliance_constraints`, `define_product_needs_and_priorities`,
`provide_technical_decision_oversight`. Each module gets
`# STUB: <mechanism name>` as its first line, then the module docstring.

```
F.2 -- Define Application Technical Needs
  out: application_technical_needs (to F.6)          mechanism: C.2 Application Developer
F.3 -- Define Budget Constraints
  out: budget_constraints (to F.6, as control)       mechanism: C.3 Budget Owner
F.4 -- Define Compliance Constraints
  out: compliance_constraints (to F.6, as control)   mechanism: C.4 Compliance Officer
F.5 -- Define Product Needs and Priorities
  out: product_priorities (to F.6)                   mechanism: C.5 Product Owner
F.6 -- Provide Technical Decision Oversight
  in:      application_technical_needs (from F.2), product_priorities (from F.5),
           presented_mapping (from F.1), presented_ranking_and_sensitivity (from F.1),
           decision_record (from F.1)
  control: budget_constraints (from F.3), compliance_constraints (from F.4)
  out:     stated_requirements (to F.1), confirmed_criteria_mapping (to F.1),
           model_selection (to F.1)
  mechanism: C.6 Technical Lead
```

F.6's `keep_decision_record` docstring must say that the model shows no output
for this input (see docs/PLAN.md findings).

## Prompt 3 — F.7 and F.8 (external services)

Modules: `provide_benchmark_evidence`, `provide_requirement_interpretation`
(existing; keep the existing `# STUB:` first line, put the module docstring
right after it, and append the new def at the end).

```
F.7 -- Provide Benchmark Evidence
  control: data_request (from F.1)
  out:     model_data_with_provenance (to F.1)
  mechanism: C.7 Benchmark Data Sources
F.8 -- Provide Requirement Interpretation
  control: interpretation_request (from F.1)
  out:     proposed_criteria (to F.1)
  mechanism: C.8 Language model runtime
```

The SRD models each request as a control ("the service produces only what it is
asked for"), so the request becomes a keyword-only parameter. That reading comes
from the model and is not the agent's to change. If the ICOMs don't produce a
clean signature, report the finding instead of working around it.

## Note after generation

The prompts said Python 3.12, which is CI's version. Two agents wrote
`str | None`, and that fails to import on the macOS system Python 3.9 that
`python3 backend/app.py` uses. The orchestrator changed both to `Optional[str]`,
which means the same thing and imports on both versions.
