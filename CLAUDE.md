# Project rules

## Source of truth
- System context & external systems: docs/context.md
- OpsCon / overview: README.md
- Requirements/spec: SPEC.md (cite as need ID / StR ID, e.g. SN-TL-03 / 5.1.2.2)
- Data and model contracts: SPEC.md sections 2 and 3
- Internal interfaces between F.1.1-F.1.7: contracts/api-v1.yaml (the authority on what crosses a boundary; change the contract first, regenerate contracts/generated/, never hand-edit stubs; divergences get an ADR in docs/adr/)
- UC.1 call path: docs/walking-skeleton.md
- Function-to-module map: docs/traceability.md (ICOM signatures: docs/PLAN.md)
- Acceptance tests: tests/ (one per SPEC.md criterion; red until implemented)
- System requirement tests: tests/test_system_requirements.py (one per SPEC.md §6 requirement, test_SR_<id>_...). Never edit a test to make an implementation pass.

## Rules
- Only implement what traces to a SPEC.md requirement ID. Cite the ID in code comments and commit messages.
- Never generate the whole project in one pass. Work one component or one requirement at a time.
- Repo structure must mirror the system context: one module per IDEF0 function, named with its verb phrase. Each function has one mechanism from context.md.
- Signatures come from the ICOMs: inputs are positional, controls keyword-only, outputs are return values (Lab Manual Table F-2).
- Stubs are fine for external systems. Mark them `# STUB: <system name>`.
- If SPEC is ambiguous or conflicts with context.md, stop and ask. Don't invent requirements.
- Plans go in docs/PLAN.md. Keep responses concise.