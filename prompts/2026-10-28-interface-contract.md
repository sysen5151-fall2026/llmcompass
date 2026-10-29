# Internal interface contract — contract-writing prompt (Lab Manual 7.4)

Given to one agent, the contract author. It was barred from the code, so the
contract comes from the model, not from what the code happens to do (7.4.3).

- **Context.** LLM Compass, F.1's first-level IDEF0
  (SYSEN5151_ArchitectureDefinitionReport.pdf Fig. 8, Tables 4 and 7). The team added
  flow 5.4 Decision basis (F.1.1 -> F.1.7) on 2026-10-28 (ADR-0002).
- **Component.** `contracts/api-v1.yaml` (new). Nothing else is created or changed.
- **Inputs it was given.**
  - Every ICOM of F.1.1-F.1.7 with its role and other end.
  - The 10 internal flows (5.1-5.4, 7.1-7.5, 8.1).
  - The report's verbatim descriptions of what each flow contains.
- **It may read.**
  - SPEC.md §2 (data contract), §3 (model contract), §5 and §6 (1.4.1.x criteria).
  - The report.
  - The SR 1.4.1.x section of tests/test_system_requirements.py, as acceptance
    criteria for call shapes.
- **It may not read.** `backend/`, docs/PLAN.md, docs/traceability.md. Where the model
  is silent, it records the choice under `x-assumptions` instead of looking at code.
- **Form.**
  - OpenAPI 3.0.3, one POST operation per exchange under `/internal/...`.
  - Each operation has `operationId` (its snake_case is the Python def),
    `x-idef0-function` and `x-module`.
  - Each request property has `x-icom: input|control` (Table F-2: inputs positional,
    controls keyword-only) and `x-idef0-flow`.
  - Responses carry `x-return-order`. Errors carry `x-python-raises`.
  - Schemas carry types, units and sources.
- **Success criteria.** Every internal flow is produced and consumed by an
  operation, and every destination has a consuming operation. The file passes
  openapi-spec-validator.

## Review after drafting (main session)

- **5 groups of divergence, 23 in all.** Stubs were generated from the contract
  (`contracts/generate_stubs.py`), and the code was checked against them
  (`contracts/check_conformance.py`). They are recorded in ADR-0002 to ADR-0004.
- **Two corrections to the contract,** both from the model or the acceptance tests:
  - F.1.2's input is named after its IDEF0 arrow (`model_data_with_provenance`).
  - The presented scores key is `score_breakdown`, which the SR 1.2.5 acceptance
    test reads (A26).
