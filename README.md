# Team CASCADILLA

SYSEN 5151 — Foundations of Systems Engineering: AI-Assisted Product Build

Early setup phase. Toolset's picked and CI is stubbed in; concept, requirements, and
architecture come next as we move through the SE lifecycle.

## Operational Concept

### 1. Scope

This document describes what LLM Compass will do and why, from the point of view of
the people who will use it. It does not describe how the system is built. It covers
the selection of a language model for a software application under development; it
does not cover model hosting, inference, or the operation of the application once a
model has been chosen.

### 2. The current situation

A team building an application that uses a language model must choose which model to
use. There is no universally best choice. A model that performs well on one kind of
task may be too slow, too expensive, or legally unusable for a particular
application. The right choice depends on that application's requirements: accuracy
on the task at hand, cost at the volume the application expects, response latency,
context length, and where the data is permitted to go.

Today this choice is made informally. A developer or technical lead reads published
leaderboards, skims vendor documentation, asks colleagues, and forms a judgement. The
process typically takes a day or more and is repeated, from scratch, by each team
facing the same decision.

Three problems follow from this.

The reasoning is not recorded. The decision lives in a chat thread or in one
person's memory. When the choice is questioned in a design review, or when the
person who made it leaves, there is nothing to point to.

The evidence is generic. Published benchmarks measure broad capabilities. They do
not measure the specific thing an application needs, and the gap between the two is
rarely made explicit. A team may choose a model because it scored well on a
benchmark that has little bearing on their task.

The decision decays. New models are released continually and prices change. A
choice that was correct six months ago may no longer be, but because the reasoning
was never written down, revisiting it means starting over.

### 3. Justification for a new system

A tool is needed that treats model selection as a trade study rather than a lookup.
It should start from the application's stated requirements, make the link between
those requirements and the available evidence explicit, and produce a recommendation
whose reasoning can be inspected, challenged, and revisited.

Existing leaderboards and comparison sites answer the question "which model scores
highest." They do not answer "which model satisfies these constraints," and they
provide no record of why a particular choice was made.

### 4. The proposed system

#### 4.1 Overview

LLM Compass is a decision-support tool. A user describes an application's
requirements and constraints; the system identifies candidate models, evaluates them
against measurable criteria drawn from public benchmark data and vendor
specifications, and returns a ranked recommendation together with the reasoning
behind it.

The system recommends. It does not host models, run inference, or make the choice on
the user's behalf.

#### 4.2 Operational scenario

A technical lead at a small software company is starting work on an application that
summarizes technical documents for its users. The team has agreed on rough
constraints but has not chosen a model.

She opens LLM Compass and describes the application in plain language: it must
summarize documents of around twenty pages accurately, stay under two hundred
dollars a month at five thousand requests per day, respond within a few seconds, and
process data that may not leave the United States.

The system proposes a set of measurable criteria corresponding to what she has
written — a minimum context length, relevant summarization and long-context
benchmark scores, a cost ceiling, a latency threshold, and a data residency
constraint. Beside each proposed criterion it shows how confident it is that the
criterion is a good proxy for the requirement. The summarization benchmark is marked
as a weak proxy; no published benchmark measures the specific task her application
performs.

She reviews the proposed mapping. She removes one benchmark she considers
irrelevant, adds a reasoning benchmark she believes matters for her documents, and
adjusts the weighting so that cost carries less influence than accuracy. Data
residency and the cost ceiling remain as hard constraints rather than weighted
preferences.

The system evaluates the candidate models. Several are eliminated outright by the
residency constraint. The survivors are scored and ranked. For each, she can see
which criteria drove its position, which published figures were used, where each
figure came from, and how recently it was collected. Two figures are flagged as more
than ninety days old.

The top-ranked model is not the one she expected. She opens the sensitivity view and
finds that the ranking between the top two candidates flips at a small change in the
cost weighting — the two are close, and the choice between them is not strongly
determined by the evidence. She notes this, discusses it with her team, and selects
one.

She exports the decision record and attaches it to the project's design
documentation. It states the requirements, the criteria they were mapped to, the
weight applied, the data used with its sources and dates, the resulting ranking, and
the sensitivity finding.

Four months later a new model is released. She reopens the saved decision, refreshes
the data, and re-runs it. The comparison takes minutes rather than a day, and the
resulting record shows what changed and why.

#### 4.3 Users and their concerns

The application developer is concerned with capability: whether a model can actually
do the task well.

The technical lead or architect owns the decision and must justify it to others.
They are concerned with the reasoning being visible and with the cost of switching
later.

The budget owner is concerned with cost per token and total spend at projected
volume, and is in direct tension with the developer's preference for the most
capable model available.

The compliance officer is concerned with data residency, retention, and whether a
vendor is contractually acceptable. Their concerns act as hard constraints: a model
that fails them is excluded regardless of how well it scores.

The operations lead is concerned with latency under load, rate limits, reliability,
and the risk of a model being deprecated by its vendor.

The end user of the downstream application does not interact with LLM Compass, but
the quality of their experience is what the requirements ultimately describe.

#### 4.4 Operational assumptions and limitations

The system relies on published benchmark data and vendor-published specifications.
It does not run its own evaluations against candidate models. Consequently its
recommendations are only as good as the public evidence available, and the system is
designed to make the weakness of that evidence visible rather than to conceal it.

Benchmark results are self-reported and may be affected by test-set contamination.
Every figure the system uses carries its source and the date it was collected, and
the user is expected to weigh that provenance rather than treat all figures as
equally reliable.

Where no published evidence bears on a stated requirement, the system reports that
no suitable proxy exists rather than substituting a weak one silently.

The system supports a decision; it does not make one. Every proposed mapping between
a requirement and a measurable criterion is presented for the user to accept,
reject, or amend before it is used.

## Product

**LLM Compass** — an LLM Selection and Evaluation Agent that helps organizations pick
the right language model for their AI product. Team: Daniel Distor (dd745), Khai Xin
Kuan (kk996), Charlie Liu (yl4432), Allyanna Panganiban (amp388), Turkhan Yusifli
(ty456).

## External Systems

See [docs/context.md](docs/context.md).

- Stakeholder actors
  - Application Developer
  - Technical Lead / Architect
  - Budget Owner
  - Compliance Officer
  - Operations Lead
- Data sources
  - Public Benchmark Data
  - Vendor Specifications

(The end user of the downstream application is out of scope — per §4.3, they don't
interact with LLM Compass directly.)

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
├── .github/workflows/ci.yml   # CI stub — currently just a "hello world" job
├── backend/
│   ├── app.py                 # no-op entry point — see Getting started below
│   └── requirements.txt       # Python deps for the planned backend (not yet implemented)
├── hello.txt                  # initial pipeline smoke test
├── SPEC.md                    # stub — Chapter 3 headings only
├── docs/
│   ├── context.md             # every external system — see Operational Concept above
│   ├── environment.md
│   ├── prompt-log.md
│   └── adr/0001-initial-toolchain.md
└── README.md
```

No application code has been written yet — this is repo scaffolding only. External
systems live in docs/context.md, not as folders (no per-actor directories — matches
the course's own worked example).

## Getting started

```
python backend/app.py
```

That's it — it's a no-op entry point. It starts and exits immediately; no feature
code exists yet (see SPEC.md, Chapter 3, still TBD).

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
