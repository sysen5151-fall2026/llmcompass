# ADR 0001: Initial Toolchain

**Status:** Accepted
**Date:** 2026-09-02

## Context

Per the course's Toolset Justification assignment, the team needed to pick tools across
six categories before beginning the build: AI coding assistant, editor/IDE, version
control & CI, backend/data storage, hosting/deployment, and LLM API access.

## Decision

| Category | Chosen | Rejected alternatives | Why |
|---|---|---|---|
| AI coding assistant | Claude Code | Cursor, Codex | Most members already familiar with Cursor-adjacent workflows; team standardized on Claude Code for agentic multi-file work. |
| Editor / IDE | VS Code | Cursor | Free and user-friendly. |
| Version control & CI | Git + GitHub, GitHub Actions | — | Course-recommended universal constant; some members have prior experience. |
| Backend / data storage | PostgreSQL (Supabase) | SQLite | Some members have prior PostgreSQL experience. |
| Hosting / deployment | Netlify | DigitalOcean | Free tier. |
| LLM API | LM Studio | — | Free; runs locally. |

## Consequences

- LM Studio is local-only. If the product needs in-app AI features reachable from a
  live Netlify deployment (not just local dev), the team will likely need to revisit
  this and add a hosted API (Anthropic, OpenAI, or Hugging Face) — this is a separate
  cost from the Claude Code subscription.
- Standardizing on GitHub Actions for CI means test tooling (pytest or Jest, per
  project stack) needs to be wired into `.github/workflows/ci.yml` once real code
  exists — currently a placeholder job.
- PostgreSQL via Supabase requires managing a hosted DB connection/credentials rather
  than a zero-setup file-based store (the SQLite alternative).

## Revisit if

- The product's AI features need to run in the deployed app, not just locally.
- Team comfort scores (see Toolset Justification, Part 2) surface a tool nobody can
  own confidently.
