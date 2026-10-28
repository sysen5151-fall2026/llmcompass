# Entry-point enumeration — read-only prompts (Lab Manual 6.4.3)

Two read-only agents ran in parallel. Neither one was asked to map anything to a use
case. The team did the mapping and decided the dispositions (docs/route-table.md).

## Agent 1: enumerate the repository's entry points

- **Context.** The LLM Compass repository. Lab Manual 6.4.2, step 1.
- **Task.** Enumerate every route, endpoint, command, or user-triggered entry
  point: anything a person or an external system triggers directly, not something
  only another of our own functions calls. Don't map them to use cases. Just list
  them and what calls them.
- **Where to look.**
  - Flask routes, error handlers and request hooks in `backend/app.py`.
  - Every form, fetch or button in `backend/templates/`.
  - Every `__main__` block or CLI parser, any scripts, and `.github/` workflows.
  - Every public def under `backend/`, and whether an entry point reaches it or
    only tests do.
  - Any live calls to external systems.
- **Report.** For each entry point: file:line, kind, handler, what it does, what it
  calls, and what triggers it. Also the public defs that no entry point reaches,
  and anything that looks like unrequested extra functionality.
- **Constraint.** Read only. No edits.

## Agent 2: extract use cases and traces from the Architecture Definition Report

- **Context.** `SYSEN5151_ArchitectureDefinitionReport.pdf`, cross-checked
  against SPEC.md, README.md and docs/walking-skeleton.md.
- **Task.** With a page number for each item, report:
  - every use case and its status
  - the numbered sequence-diagram interactions, verbatim
  - the trace over the Metafunction and first-level IDEF0, and any errors it exposed
  - the F.x and F.1.x functions and their mechanisms
  - anything the report says about the UI or entry points, and about 5.1.5.1/5.1.5.2
  - whether the 6.4.1 prerequisites (traced interactions; direct trace through
    levels) are present
- **Constraint.** Read only. No edits.
