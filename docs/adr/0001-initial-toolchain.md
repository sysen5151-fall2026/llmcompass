# ADR-0001: Initial Toolchain

Status: Accepted

Context: Per the course's Toolset Justification assignment, the team needed to pick
tools across six categories, including whether the in-product language model is local
or hosted.

Decision:

| Category | Chosen | Rejected alternatives | Why |
|---|---|---|---|
| AI coding assistant | Claude Code | Cursor, Codex | Most members already familiar with Cursor-adjacent workflows; team standardized on Claude Code for agentic multi-file work. |
| Editor / IDE | VS Code, Cursor | — | Team uses both, member's choice; VS Code is free, Cursor is what some members already knew. |
| Version control & CI | Git + GitHub, GitHub Actions | — | Course-recommended universal constant; some members have prior experience. |
| Backend / data storage | PostgreSQL (Supabase) | SQLite | Some members have prior PostgreSQL experience. |
| Hosting / deployment | Netlify | DigitalOcean | Free tier. |
| LLM API (in-product model) | LM Studio, local | Anthropic API / OpenAI API (hosted) | Free; keeps data on team machines while the product's data sensitivity is still unknown. |

Rationale: The in-product model is local rather than hosted because it's free and
keeps all data on the team's own machines until the team confirms the product's data
isn't sensitive. The other five categories were chosen for team familiarity and
zero/near-zero cost, fitting a one-semester scope with mixed programming backgrounds.

What would change this decision: If the product needs in-app AI features reachable
from the live Netlify deployment, not just local dev, the team will need a hosted API
(Anthropic, OpenAI, or Hugging Face) instead — a separate cost from the Claude Code
subscription. Revisit at the Week 12 trade study.
