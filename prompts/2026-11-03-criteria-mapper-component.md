# C.1.1 Criteria Mapper from its component specification — prompts (Lab Manual 9.4)

## Main session prompt (Allyanna, 2026-11-03, verbatim)

> Execute the "Chapter 9 build: Component Implementation from Specification" section of the plan, steps 1–7, for C.1.1 Criteria Mapper, then the "Milestone 2 demo alignment" UI wiring, on allyanna.
>
> Decisions already made, do not stop to ask:
> - Generate in ONE pass with no follow-up corrections (Lab Manual 9.4.3). Write docs/deviation-log.md before changing anything; classify each deviation as spec defect, assistant error, or unrequested addition.
> - Where SR 2.2.1–2.4.1 statements are marked "not exported", use the CR 2.2.1–2.4.1 text from the Form report Tables 9 and 10 as written, and record the gap as an open issue.
> - Justified assumptions: list them as new requirements for me to add in Innoslate; do not block on them.
> - After Ch 9, wire the web UI to C.1.1: requirements form → Request Interpretation (live via the Ch 8 adapter) → validated criteria with proxy-strength ratings → a mapping review page where the Technical Lead confirms or edits (UC.1.9 entry point, add to the route table) → Distribute Confirmed Mapping feeds the ranking and the record. A failed interpretation shows interpretation_failed with manual entry.
> - Write the demo script in docs/validation/ using SCENARIO_02 (not SCENARIO_01, which depends on AA-Omniscience), mapped to the second-level IDEF0 boxes and flows.
> - The LM Studio tests stay red in CI; do not change them.
>
> Rules: no test that passes now may fail, no test is edited to pass. Commit Ch 9 and the UI wiring as separate commits. At the end, give me open issues split into (a) what you could not finish and (b) what needs a teammate or Innoslate.

Corrections given at plan approval (Allyanna, 2026-11-03):
- Leave the SR 2.2.1–2.4.1 placeholders in SPEC §6 as they are; use the CR 2.2.1–2.4.1 text
  in §7 only (filling SRs from CRs would write invented model text).
- Promoted assumptions must be entered in Innoslate by a team member (Ch 9 Done When).
- State once that all four of C.1.1.1–C.1.1.4 are generated because the specification is
  written for C.1.1 as a whole.
- Spec defects found in the deviation log also go on the Innoslate list.

## Prep (main session, before any agent)

- SPEC.md §7 transcribed verbatim from Form report Tables 3, 9, 10 (+ §2.2 flow numbering).
- contracts/api-v1.yaml v1.1.0: four second-level operations, flows 1.0.1 and 3.0.1,
  schemas InterpretationRequest, RequirementSet, ProposedCriterion, ValidatedCriteria,
  PresentedMapping, assumptions A28–A31. Stubs regenerated.
- In the generation worktree only: the old module moved unchanged to
  `propose_criteria_mapping/_first_level.py` behind a package `__init__.py` that re-exports
  it, so the generated modules have a package to live in. Suite unchanged (129 / 13).

## Agent 1: component test writer

Sees SPEC §2–§7, the contract and generated stubs, the PLAN signature table, conftest,
sample_data and walkthroughs.csv; never a backend module body. Writes
tests/test_component_criteria_mapper.py only, one `test_CR_<id>_*` per CR; T tests use
hand-built SPEC §3 responses (no LM Studio, no network); I tests check configuration; D tests
read docs/validation/walkthroughs.csv. Spec gaps are reported, not invented.

Result: 39 tests / 119 cases; sha256
`adcb69ccbbd92a5b41c59631425031a674a134a1c601063774613068e61ba67a` (unchanged since).

## Agent 2: generator — the full Component Prompt Template (one pass, no follow-up)

**Context.** LLM Compass (C.1) is a local decision-support tool: a Technical Lead types
plain-language requirements for an application, and the system turns them into measurable
criteria, retrieves benchmark evidence, ranks candidate LLMs and records the decision. It is
built model-to-code from an Innoslate model (IDEF0 functions → one Python module each, named
with the verb phrase; inputs positional, controls keyword-only, outputs are return values).
You are implementing one component from its specification, as a supplier would: you know
nothing else about the project and cannot ask questions.

**Component.** C.1.1 Criteria Mapper, performing F.1.1 Propose Criteria Mapping, decomposed into
four components (SPEC.md §7, Table 3): C.1.1.1 Interpretation Client, C.1.1.2 Criteria
Validator, C.1.1.3 Mapping Presenter, C.1.1.4 Mapping Distributor.

**Function.** F.1.1.1 Request Interpretation, F.1.1.2 Validate Proposed Criteria, F.1.1.3 Present
Criteria Mapping, F.1.1.4 Distribute Confirmed Mapping, connected by the internal flows 1.0.1
Requirement set (C.1.1.1 → C.1.1.2, C.1.1.4) and 3.0.1 Validated criteria (C.1.1.2 → C.1.1.3).

**Requirements.** SPEC.md §7: CR 1.1.1–1.1.4 (inputs), CR 1.2.1–1.2.6 (outputs), CR 1.3.1–1.3.8
(interfaces), CR 1.4.1–1.4.4 (functions), CR 2.1.1–2.4.1 (system-wide, flowed down). Model
contract (request/response schema and failure path): SPEC.md §3. Data contract (figure fields):
SPEC.md §2. Cite the CR ID (and its trace) in a comment on the code that implements it.

**Interfaces.**
- contracts/api-v1.yaml v1.1.0, operations requestInterpretation, validateProposedCriteria,
  presentCriteriaMapping, distributeConfirmedMapping, their schemas, and A28–A31. The exact
  Python signatures are in contracts/generated/propose_criteria_mapping.<module>_stub.py; your
  defs must match them exactly (names, parameter kinds, defaults).
- Outflow shapes 5.1–5.4: schemas RequiredMetrics, HardConstraints, WeightedCriteria,
  DecisionBasis, Criterion, ConfirmedCriteriaMapping in the same contract.
- Known metrics list (`known_metrics=None` = the configured list): SPEC 2 candidate figure
  field names plus every known benchmark_id. Available as importable constants:
  `from provide_benchmark_evidence import BENCHMARK_IDS` and
  `from provide_llm_selection_decision_support.retrieve_model_data import FIGURE_FIELDS`.
- Language model runtime adapter (F.8, Lab Manual 8.5): `from provide_requirement_interpretation
  import propose_criteria` — `propose_criteria(*, interpretation_request: dict) -> Optional[dict]`,
  returns the parsed SPEC §3 response or None on timeout/unreachable/non-JSON;
  `runtime_config()` returns the local base_url (SPEC §3 "Adapter").

**Constraints.**
- Write exactly four new files in
  backend/provide_llm_selection_decision_support/propose_criteria_mapping/:
  request_interpretation.py, validate_proposed_criteria.py, present_criteria_mapping.py,
  distribute_confirmed_mapping.py. Do not modify or read any other file in backend/ (the
  package `__init__.py` and `_first_level.py` are out of scope and must not be read).
- Do not read tests/ bodies. Python 3.9+, stdlib only. No network calls other than through
  the F.8 adapter. Each module starts with a docstring
  `"""Implements F.1.1.x -- <Verb phrase>. Mechanism: C.1.1.x <Component name>."""`.
- One pass: produce the implementation once. No follow-up corrections.

**Success criteria.** `python3 contracts/check_conformance.py` reports no divergence for the
four operations; every CR in SPEC §7 that is verified by test can be met by these defs; the
defs are deterministic for the same input apart from generated identifiers.

**Output format.** The four files, then a short report: for each CR, where it is implemented;
every assumption you had to make where SPEC/contract were silent.

**Out of scope.** The web UI, the Technical Lead's confirmation step itself, F.1.2–F.1.7,
storage, the first-level F.1.1 defs, changes to the contract or SPEC.

## Agent 3: deviation auditor

Did not write the code or the tests. Diffs the raw generation (commit on branch
`ch9-raw-generation`) against SPEC §7, §3 and the contract; runs the CR tests on it; writes one
docs/deviation-log.md row per deviation (spec said / code did / why / class). No code changes.

## Agent 4: independent verifier (after reconcile and after the UI wiring)

Checks the Ch 9 Done When items, the suite against the baseline failing set, the contract
checks, a live SCENARIO_02 run through the web UI on LM Studio and live data, and that no
outbound host other than localhost and the three data APIs is used.
