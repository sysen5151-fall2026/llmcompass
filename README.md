# Team CASCADILLA

SYSEN 5151 — Foundations of Systems Engineering: AI-Assisted Product Build

> **Status: early setup phase.** Toolset is chosen and CI scaffolding exists, but the
> product concept, requirements, and architecture haven't been finalized yet. This
> README reflects what's actually in the repo today and will expand as the project
> moves through the SE lifecycle (concept → requirements → architecture → build).

## Product

**LLM Compass** — an LLM Selection and Evaluation Agent that helps organizations pick
the right language model for their AI product. Team: Daniel Distor (dd745), Khai Xin
Kuan (kk996), Charlie Liu (yl4432), Allyanna Panganiban (amp388), Turkhan Yusifli
(ty456).

## Operational Concept

> TBD — pending the team's Innoslate asset diagram for Universe context and OpsCon
> narrative (Lab 1 / Tutorial 3). Once that model exists, its narrative text goes
> here **copied verbatim, not paraphrased** — see docs/decisions and course Week 2
> materials for why.
>
> Working draft, not yet sourced from the model: a user (Application Developer,
> Budget Owner, Compliance Officer, Product Owner, or Technical Lead) describes an
> application's requirements in plain language; LLM Compass checks candidate LLMs
> against published benchmark scores and vendor specifications and returns a ranked
> recommendation with a rationale.

## External Systems

Draft — pending the Innoslate context diagram; see [docs/context.md](docs/context.md).

- Requirement Submitter (the stakeholder roles above)
- Benchmark Source
- Vendor Specification Source

## Status

Scaffold only. No feature code — see SPEC.md, Chapter 3.

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
├── .github/workflows/ci.yml     # CI stub — currently just a "hello world" job
├── backend/
│   └── requirements.txt         # Python deps for the planned backend (not yet implemented)
├── requirement-submitter/       # boundary element scaffold — see docs/context.md
├── benchmark-source/            # boundary element scaffold — see docs/context.md
├── vendor-specification-source/ # boundary element scaffold — see docs/context.md
├── hello.txt                    # initial pipeline smoke test
├── SPEC.md                      # stub — Chapter 3 headings only
├── docs/
│   ├── context.md               # external systems, draft pending Innoslate diagram
│   ├── environment.md
│   ├── prompt-log.md
│   └── decisions/0001-initial-toolchain.md
└── README.md
```

No application code has been written yet — this is repo scaffolding only. The three
boundary-element directories are provisional, named from the draft context inventory
in docs/context.md — rename/add to match once the team's Innoslate context diagram is
final.

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
