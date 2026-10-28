# Team CASCADILLA

SYSEN 5151 — Foundations of Systems Engineering: AI-Assisted Product Build

Walking skeleton runs end to end for UC.1. Stakeholder needs and requirements are
baselined in SPEC.md with acceptance tests wired into CI; system requirements and
architecture come next as we move through the SE lifecycle.

## Operational Concept

A team is building an application and has to choose a model. Today someone spends a
day reading leaderboards and vendor pages, picks something, and the reasoning lives
in a Slack thread. With LLM Compass, the technical lead enters the application's
requirements, reviews the criteria the system proposes, adjusts the weights to
reflect what the team actually cares about, and gets a ranked shortlist with the
reasoning attached. They export the decision record into their design
documentation. When a new model appears six months later, they reopen it and re-run
rather than starting over.

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

**4.1 Overview**

LLM Compass is a decision-support tool. A user describes an application's
requirements and constraints; the system identifies candidate models, evaluates them
against measurable criteria drawn from public benchmark data and vendor
specifications, and returns a ranked recommendation together with the reasoning
behind it.

The system recommends. It does not host models, run inference, or make the choice on
the user's behalf.

**4.2 Operational scenario**

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
weights applied, the data used with its sources and dates, the resulting ranking,
and the sensitivity finding.

Four months later a new model is released. She reopens the saved decision, refreshes
the data, and re-runs it. The comparison takes minutes rather than a day, and the
resulting record shows what changed and why.

**4.3 Users and contributors**

Only the technical lead uses LLM Compass. The others shape the selection without
operating the system: their requirements and constraints reach it as values the
technical lead states, and they see the result through the technical lead rather
than from the system. This is a deliberate boundary decision — see docs/context.md.

The technical lead owns the decision and must justify it to others. They are the
sole operator of the system, and are concerned with the reasoning being visible and
with the cost of switching later.

The application developer builds the AI application that will use the selected
model. Concerned with capability fit for the specific task. Supplies the
application's functional requirements to the technical lead, but does not own the
selection decision.

The budget owner sets the cost ceiling the selection must respect, and is concerned
with cost per token and total spend at projected volume — in direct tension with the
developer's preference for the most capable model available.

The compliance officer is concerned with data residency, retention, and whether a
vendor is contractually acceptable. Their concerns act as hard constraints: a model
that fails them is excluded regardless of how well it scores.

The product owner is accountable for the application's outcomes and priorities.
Sets the relative importance of capability, cost, and speed, which the technical
lead applies as weights during selection.

The end user of the downstream application does not interact with LLM Compass, but
the quality of their experience is what the requirements ultimately describe.

**4.4 Operational assumptions and limitations**

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

## External Assets

See [docs/context.md](docs/context.md).

Three hold an interface to LLM Compass. These are the only crossings of the system
boundary:

- Technical Lead — the sole human interface
- Benchmark Data Sources — model specifications and benchmark figures, with source
  and collection date
- Language model runtime — LLM Compass's own requirement-interpretation engine, not
  a data source in the vendor-spec sense (see docs/context.md)

Four contribute to the selection without an interface. Their constraints and
priorities reach the system through the Technical Lead, and they appear on the
context diagram with no connection to LLM Compass:

- Application Developer
- Budget Owner
- Compliance Officer
- Product Owner

(The end user of the downstream application is out of scope — per §4.3, they don't
interact with LLM Compass directly.)

## Status

Walking skeleton for UC.1 with real ranking and sensitivity analysis (UC.1.16:
SN-TL-05 / 5.1.4.1) and a decision record with all six required sections (UC.1.18:
SN-TL-09 / 5.1.3.2). The other steps are still stubs. SPEC.md is written and its
acceptance tests are wired into CI; the rest fail until their features are built.

## Toolset

| Category | Tool Selected | Notes |
|---|---|---|
| AI coding assistant | Claude Code | Alternatives considered: Cursor, Codex |
| Editor / IDE | VS Code, Cursor | Team uses both — member's choice |
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
├── .github/workflows/ci.yml   # runs every test with pytest + Flask; red while any requirement is unmet
├── .claude/commands/          # /log and the explorer / spec-tracer agents
├── backend/
│   ├── app.py                 # walking skeleton — Flask UI around the UC.1 call path
│   ├── templates/index.html   # the only page: text box, Submit, decision record
│   ├── provide_llm_selection_decision_support/  # F.1, the system itself: one module per sub-function F.1.1-F.1.7 (IDEF0 A1); the ICOM defs compose them; Technical Lead confirm/select are still stubs
│   ├── define_application_technical_needs/  # F.2 (docstring only: no system requirement)
│   ├── define_budget_constraints/  # F.3 (docstring only: no system requirement)
│   ├── define_compliance_constraints/  # F.4 (docstring only: no system requirement)
│   ├── define_product_needs_and_priorities/  # F.5 (docstring only: no system requirement)
│   ├── provide_technical_decision_oversight/  # F.6 (stub, signatures only)
│   ├── provide_requirement_interpretation/  # F.8, C.8 (stub, returns interpreted_requirements from sample_data)
│   ├── provide_benchmark_evidence/  # F.7, C.7 (stored catalog from sample_data in the SPEC §2 figure shape; no live source yet)
│   └── requirements.txt       # Python deps for the planned backend
├── sample_data/               # 4 UC.1 scenarios (user_inputs, expected_outputs, scenario_criteria) and model data
├── hello.txt                  # initial pipeline smoke test
├── CLAUDE.md                  # project rules for the coding assistant
├── SPEC.md                    # needs, acceptance criteria, data + model contracts, system requirements (§6)
├── tests/                     # one test per acceptance criterion; test_system_requirements.py has one per system requirement (SR 1.1.1-1.4.1)
├── prompts/                   # generation prompts
├── pytest.ini
├── docs/
│   ├── context.md             # external assets, and which of them hold an interface
│   ├── walking-skeleton.md    # UC.1 call path from the Innoslate sequence diagram
│   ├── traceability.md        # function -> module, and requirement -> need -> test
│   ├── PLAN.md
│   ├── environment.md
│   ├── prompt-log.md
│   ├── validation/walkthroughs.csv  # timed runs for the operator-effort requirements
│   └── adr/0001-initial-toolchain.md
└── README.md
```

Feature code so far: ranking, sensitivity analysis and the decision record (see docs/PLAN.md). Everything
else is walking skeleton and stubs. External
assets live in docs/context.md, not as folders (no per-actor directories — matches
the course's own worked example). Code folders follow the IDEF0 functions instead
(Lab Manual 4.4): one module per function, named with its verb phrase, mapped in
docs/traceability.md. C.7 and C.8 are the only external assets the system calls.

## Getting started

```
pip install flask
python3 backend/app.py
```

Open http://127.0.0.1:5000 and paste one of the `user_input` texts from
`sample_data/user_inputs.json`. The UC.1 call path runs end to end.
The comparison result's ranking, score breakdown, evidence (source, date, stale
flag), exclusions and sensitivity finding are computed from the sample model data,
using the criteria and weights for that scenario in `sample_data/scenario_criteria.json`.
The decision record carries the requirements, criteria, weights, evidence, ranking,
sensitivity finding and selected model. The written text (assessments, trade-offs,
selection, record summary) is still that scenario's record from
`sample_data/expected_outputs.json`. Empty input is rejected. Any other text isn't
handled yet. To run the
acceptance tests (most fail until features are built):

```
pip install pytest
pytest
```

## Roadmap

Following the course's SE-to-build progression. Submitted so far: the Business Analysis
Report and the Stakeholder Needs and Requirements Definition.

- [x] Toolset justification
- [x] Stakeholder needs / personas — personas and empathy maps for both Players,
      Power-Interest Grid, and needs derived in three traced stages: primitive →
      critical-to-quality → effective (SNRD §2)
- [x] Concept & ConOps — OpsCon and the solution-class trade study in the Business
      Analysis Report (§3, §8, Appendix 1). No separate mockups; the walking-skeleton
      UI stands in for them
- [ ] Requirements (functional + non-functional) — stakeholder requirements done:
      19 statements with rationale, measures of effectiveness and validation criteria
      (SPEC.md; SNRD §3), passing Innoslate Intelligence at 100%. System requirements
      next
- [ ] Architecture (Innoslate model → repo skeleton) — behaviour model done for UC.1
      (use case, action, activity and sequence diagrams) and the repo skeleton matches
      it. Open: decompose F.1 into sub-functions, and trace requirements to the UC.1.n
      actions rather than only to functions
- [ ] Detailed design & first working slice — first slice done: ranking, sensitivity
      analysis and the decision record are real (UC.1.12–1.16, UC.1.18). The remaining
      UC.1 steps are stubs
- [ ] Integration (end-to-end flow) — the UC.1 path runs end to end with C.7 and C.8
      stubbed; real benchmark ingestion and a real runtime call come next
- [ ] Verification & Validation (test suite) — one acceptance test per criterion wired
      into CI, passing for the implemented slice. Validation criteria are defined
      (SNRD §3.4) but not yet run: they need test data the team hasn't built, including
      a requirement set with known-weak proxies and a deliberately marginal ranking
- [ ] Final delivery (deployed app + demo + known-limitations writeup)
