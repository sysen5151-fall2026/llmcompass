# Team CASCADILLA

SYSEN 5151 — Foundations of Systems Engineering: AI-Assisted Product Build

> **Status: early setup phase.** Toolset is chosen and CI scaffolding exists, but the
> product concept, requirements, and architecture haven't been finalized yet. This
> README reflects what's actually in the repo today and will expand as the project
> moves through the SE lifecycle (concept → requirements → architecture → build).

## Project

_TBD — concept and requirements not yet written up._

## Toolset

| Category | Tool Selected | Notes |
|---|---|---|
| AI coding assistant | Claude Code | Alternatives considered: Cursor, Codex |
| Editor / IDE | VS Code | Alternative considered: Cursor |
| Version control & CI | Git + GitHub, GitHub Actions | |
| Backend / data storage | PostgreSQL (Supabase) | Alternative considered: SQLite |
| Hosting / deployment | Netlify | Alternative considered: DigitalOcean |
| LLM API | LM Studio | Local/free; may need a hosted API (Anthropic/OpenAI/Hugging Face) once the app is deployed live |

See the team's Toolset Justification doc for full rationale.

## Team & tool ownership

| Member | Owns |
|---|---|
| Daniel Distor | Git control, Claude Code, Cursor |
| Khai Xin Kuan | PostgreSQL, VS Code, Claude Code |
| Charlie Liu | Codex |
| Allyanna Panganiban | Claude/Cursor, Netlify |
| Turkhan Yusifli | LM Studio, Claude Code |

## Repo layout

```
.
├── .github/workflows/ci.yml   # CI stub — currently just a "hello world" job
├── backend/
│   └── requirements.txt       # Python deps for the planned backend (not yet implemented)
├── hello.txt                  # initial pipeline smoke test
└── README.md
```

No application code has been written yet — this is repo scaffolding only.

## Getting started

Nothing runnable yet. Setup instructions will be added once the first backend slice exists.

## Roadmap

Following the course's SE-to-build progression:

- [x] Toolset justification
- [ ] Stakeholder needs / personas
- [ ] Concept & ConOps (trade study, mockups)
- [ ] Requirements (functional + non-functional)
- [ ] Architecture (Innoslate model → repo skeleton)
- [ ] Detailed design & first working slice
- [ ] Integration (end-to-end flow)
- [ ] Verification & Validation (test suite)
- [ ] Final delivery (deployed app + demo + known-limitations writeup)
