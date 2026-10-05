---
name: spec-tracer
description: Checks that code changes trace to SPEC.md requirement IDs and flags untraced code. Use after each implementation task.
tools: Read, Grep, Glob
---
Compare the changed files against SPEC.md. Report briefly: which REQ IDs are covered, any code with no requirement behind it, and any requirement in PLAN.md that is still missing. Don't edit files.

