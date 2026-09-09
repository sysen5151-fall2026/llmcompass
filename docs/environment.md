# Environment / Toolchain

Recorded from the team's Toolset Justification (Part 1). See
[`docs/adr/0001-initial-toolchain.md`](adr/0001-initial-toolchain.md) for the
rationale behind each choice.

| Category | Tool | Alternatives Considered |
|---|---|---|
| AI coding assistant | Claude Code | Cursor, Codex |
| Editor / IDE | VS Code, Cursor | — |
| Version control & CI | Git + GitHub, GitHub Actions | — |
| Backend / data storage | PostgreSQL (Supabase) | SQLite |
| Hosting / deployment | Netlify | DigitalOcean |
| LLM API | LM Studio | — |

## Tool ownership

| Member | Owns |
|---|---|
| Daniel Distor | Git control, Claude Code, Cursor |
| Khai Xin Kuan | PostgreSQL, VS Code, Claude Code |
| Charlie Liu | Codex |
| Allyanna Panganiban | Claude/Cursor, Netlify |
| Turkhan Yusifli | LM Studio, Claude Code |

## Repo access (as of last check)

- GitHub org: `sysen-5151-Fall26`
- Repo: `lab-project`
- Collaborators: allyannap, DanielDistor, KhaiXin30, charlie111801-lyc, turkhan1
- Branch protection on `main`: **not yet set** — requires admin access, which no team
  member currently has (all are Write/Triage). Needs instructor/org-admin action.
