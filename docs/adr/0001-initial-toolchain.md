# ADR-0001: Initial Toolchain

Status: Accepted

Context: Per the course's Toolset Justification assignment, the team needed to pick
tools across six categories before beginning the build — AI coding assistant,
editor/IDE, version control & CI, backend/data storage, hosting/deployment, and LLM
API access — including whether the in-product language model is local or hosted.

Decision:

| Category | Chosen | Rejected alternatives | Why |
|---|---|---|---|
| AI coding assistant | Claude Code | Cursor, Codex | Most members already familiar with Cursor-adjacent workflows; team standardized on Claude Code for agentic multi-file work. |
| Editor / IDE | VS Code | Cursor | Free and user-friendly. |
| Version control & CI | Git + GitHub, GitHub Actions | — | Course-recommended universal constant; some members have prior experience. |
| Backend / data storage | PostgreSQL (Supabase) | SQLite | Some members have prior PostgreSQL experience. |
| Hosting / deployment | Netlify | DigitalOcean | Free tier. |
| LLM API (in-product model) | LM Studio, local | Anthropic API / OpenAI API (hosted) | Free; runs locally, so no query data leaves team machines while the product's real data sensitivity is still unknown. |

Rationale: The in-product model is local (LM Studio) rather than hosted mainly
because it's free, but also because it keeps all data on the team's own machines —
the course's default posture for a team that hasn't yet confirmed its data isn't
sensitive (see Lab Manual, "A note on data security"). The other five categories were
chosen for team familiarity and zero/near-zero cost, appropriate for a one-semester
scope with mixed programming backgrounds across the team.

What would change this decision: If the product needs in-app AI features reachable
from the live Netlify deployment — not just local dev — LM Studio's local-only nature
stops working, and the team will need a hosted API (Anthropic, OpenAI, or Hugging
Face) instead, which is a separate cost from the Claude Code subscription. This is
exactly what the Week 12 trade study revisits. Also revisit if: team comfort scores
(Toolset Justification, Part 2) surface a tool nobody can own confidently; or CI
tooling (pytest or Jest, per stack) needs to be wired into
`.github/workflows/ci.yml` once real code exists — currently a placeholder job.
