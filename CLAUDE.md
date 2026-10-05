# Project rules

## Source of truth
- System context & external systems: docs/context.md
- OpsCon / overview: README.md
- Requirements/spec: SPEC.md (requirement IDs like REQ-xxx)

## Rules
- Only implement what traces to a SPEC.md requirement ID. Cite the ID in code comments and commit messages.
- Never generate the whole project in one pass. Work one component or one requirement at a time.
- Repo structure must mirror the system context (one module per subsystem/external interface in context.md).
- Stubs are fine for external systems. Mark them `# STUB: <system name>`.
- If SPEC is ambiguous or conflicts with context.md, stop and ask. Don't invent requirements.
- Plans go in docs/PLAN.md. Keep responses concise.