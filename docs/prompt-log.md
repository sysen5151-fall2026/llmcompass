image.png1.# Prompt Log

Running log of significant AI-assisted work on this repo. Each entry: date, who,
tool, what was asked, what came out of it.

---

## 2026-09-02 — Daniel Distor — Claude Code

**Prompt:** Reviewed the course's Student Handout 

---

## 2026-09-08 — Daniel Distor — Claude Code

**Prompt:** Given the team's OpsCon narrative and pitch doc, brought README.md,
SPEC.md, and docs/context.md in line with the Week 2 slide deck
(`Wk02_Business_Mission_Analysis_System_Context.pdf`) — the deck was checked
directly rather than assumed. Also asked to verify what's actually done vs.
outstanding against the deck's "done when" checklist and GitHub itself, and to
scaffold the missing no-op entry point.

**Output:**
- `README.md` — Operational Concept replaced with the real OpsCon narrative
  (copied verbatim, not paraphrased, per slide 10/14); External Systems updated to
  the actual 7 (5 stakeholder roles + Public Benchmark Data + Vendor
  Specifications; end user of the downstream app excluded per the narrative);
  Getting started now documents `python backend/app.py`.
- `SPEC.md` — reverted to a bare stub (headings only) after an earlier pass had
  wrongly filled in Chapter 3-level content; that belongs later, not this
  increment.
- `docs/context.md` — reformatted to the course's In/Out style, matched to the
  real 7 external systems.
- Removed `requirement-submitter/`, `benchmark-source/`, `vendor-specification-source/`
  placeholder directories — the course's own worked example (Airport Kiosk) keeps
  external systems in `docs/context.md` only, no per-actor folders.
- `backend/app.py` — no-op entry point (`python backend/app.py`, exits 0, does
  nothing) — was the one missing item from the "done when" checklist.

**Verified against GitHub directly (not just repo files):**
- `backend/.venv/` — still tracked (12,056 files). Allyanna hasn't run the
  untrack commands from the 09-02 entry yet.
- Branch protection on `main` — confirmed **not set** (`GET
  .../branches/main/protection` → 404).
- Collaborators — confirmed via API: only the 5 team members, **no instructor**.
  Permissions: Khai Xin (KhaiXin30) has **admin**; everyone else (incl. Daniel)
  has push/triage only. The 09-02 note that "no team member has admin" was
  wrong — Khai has it. Branch protection + adding the instructor need to come
  from Khai's own GitHub login; no one else on the team can do either.

**Still open:**
- Whether "one top-level directory per boundary element" (slide 14) applies to
  external actors or to LLM Compass's own internal subsystems is unresolved —
  went with the course example's structure (no per-actor folders) but flagged
  as an interpretation, not a settled fact.
- `backend/requirements.txt` is a raw `pip freeze` dump (~188 packages incl.
  `chromadb`), not a curated dependency list for this project.
- Repo is named `lab-project`, not for the team — unclear if that's fixed by
  the instructor's starter repo or something the team should rename.

---

## 2026-09-09 — Daniel Distor — Claude Code

**Prompt:** The course's "Product Build — Build Steps" slide and the Lab Manual
(`SYSEN_5151_Innoslate_Lab_Manual_v3_0_23_5_5.pdf`, §1.4.2 and the Airport Kiosk
worked example) disagree on the ADR path — `docs/decisions/` vs. `docs/adr/`. Per the
professor (asked directly), followed the Lab Manual: moved the ADR and rewrote it to
match the worked example's field structure and content expectations.


---

## 2026-09-09 — Daniel Distor — Claude Code

**Prompt:** Corrected the Editor/IDE row — the team actually uses both VS Code and
Cursor (member's choice), not VS Code with Cursor as a rejected alternative. That was
wrong in every file that recorded it.

**Output:**
- `README.md`, `docs/environment.md`, `docs/adr/0001-initial-toolchain.md` — Editor /
  IDE row changed from "VS Code (Cursor rejected)" to "VS Code, Cursor — team uses
  both." Team & tool ownership table already listed Cursor for Daniel and Allyanna
  and VS Code for Khai, so no change needed there.

---

## 2026-09-19 — Daniel Distor — Claude Code

**Prompt:** Given team's Innoslate sequence diagram for UC.1
(Technical Lead selects a model for an application), transcribed it into
`docs/walking-skeleton.md` as a numbered call list per the Lab Manual's format
(section 2.4.2.2.1), then asked for the four participants to be stubbed and wired
so one call travels the whole path, per the same section's Build Steps.

**Output:**
- `docs/walking-skeleton.md` — numbered call list, matched to the Lab Manual's
  worked example format (plain `UC.1 -- ...` heading, no extra sections).
- `backend/language_model_runtime/__init__.py` — stub for `enter_requirements`
  (UC.1.2).
- `backend/benchmark_data_sources/__init__.py` — stub for `confirm_mapping`
  (UC.1.8).
- `backend/llm_compass/__init__.py` — stubs for `interpret_requirements` (UC.1.3),
  `present_mapping_for_review` (UC.1.5), `retrieve_model_spec_and_benchmark_data`
  (UC.1.9), `present_sensitivity_finding` (UC.1.14), `select_model` (UC.1.15), and
  `generate_decision_record` (UC.1.16).
- `backend/app.py` — replaced the no-op with the walking skeleton driver; calls
  the eight stub functions in the order from `docs/walking-skeleton.md` and prints
  the resulting decision record. Verified with `python3 backend/app.py`.
- No error handling, retries, or real logic added, per the increment's scope.


---

## 2026-09-19 — Daniel Distor — Claude Code

**Prompt:** Shared the asset descriptions (LLM Compass, Technical Lead,
Benchmark Data Sources, Language model runtime) and the use case step
descriptions (UC.1.2, UC.1.3, UC.1.5, UC.1.8, UC.1.9, UC.1.14, UC.1.15, UC.1.16)
from the Innoslate model. Asked to use them to make the stub return values
match the described shape more closely, since they'd been generic
placeholders.

**Output:**
- `backend/language_model_runtime/__init__.py` — `enter_requirements` now
  returns criteria tied to the requirement each was derived from, with a
  confidence level, matching UC.1.3's description.
- `backend/benchmark_data_sources/__init__.py` — `confirm_mapping` now returns
  a candidate model's spec and benchmark figures with source and collection
  date, matching UC.1.9's description.
- `backend/llm_compass/__init__.py` — `generate_decision_record` now
  assembles requirements, criteria mapping, weights, data provenance,
  ranking, sensitivity finding, and selection into one record, matching
  UC.1.16's description. Still all hard-coded, no real computation.
- `docs/walking-skeleton.md` — softened the bypass note. Language model
  runtime's own description ("external API that receives a stated
  requirement and returns proposed measurable criteria") supports steps 1-2
  as designed; it's a team conversation against docs/context.md now, not a
  likely error.
- Verified with `python3 backend/app.py`.

---

## 2026-09-19 — Daniel Distor — Claude Code

**Prompt:** Team revised the Innoslate sequence diagram (steps now run UC.1.2
through UC.1.18, up from UC.1.16). Asked to re-transcribe and re-wire against
the new version.

**Output:**
- `docs/walking-skeleton.md` — rewritten to the new 10-step sequence.
  "Confirm the mapping" now targets LLM Compass instead of Benchmark Data
  Sources, resolving the bypass note from the prior version. Two new steps
  (UC.1.10 Request model data, UC.1.11 Retrieve model specification and
  benchmark data) replace the old single confirm/retrieve pairing.
- `backend/language_model_runtime/__init__.py` — `submit_requirements`
  (renamed from `enter_requirements`), same return shape.
- `backend/benchmark_data_sources/__init__.py` — `request_model_data`
  (renamed from `confirm_mapping`), same return shape.
- `backend/llm_compass/__init__.py` — added `receive_requirements` (UC.1.2)
  and `confirm_mapping` (UC.1.9, now owned here instead of by Benchmark Data
  Sources); kept `present_mapping_for_review`, `present_sensitivity_finding`,
  `select_model`, `generate_decision_record`.
- `backend/app.py` — rewired to the 10-step chain. Verified with
  `python3 backend/app.py`.
- Two label/arrow pairings were read from a leader-line marker rather than a
  direct label position (UC.1.10/1.11 and UC.1.17/1.18); resolved by numeric
  order and by which reading made semantic sense, flagged in
  `docs/walking-skeleton.md` for a quick visual confirmation in Innoslate.

---

## 2026-09-19 — Daniel Distor — Claude Code

**Prompt:** Shared five new Innoslate exports (hierarchy diagram, spider
diagram, and the UC.1 activity, swimlane, and sequence diagrams) and asked
whether anything in the project is inconsistent.

**Output:**
- `docs/walking-skeleton.md` — fixed steps 2 and 6: both were attributed to
  Technical Lead calling Language model runtime / Benchmark Data Sources
  directly, flagged as unconfirmed in the prior entry. The actual sequence
  diagram shows LLM Compass as the caller in both cases; Technical Lead
  never talks to either external system directly.
- `docs/context.md` — resolved both TBDs from the previous pass:
  Language model runtime is LLM Compass's own requirement-interpretation
  engine (local model, ADR 0001), not a vendor-spec feed; Benchmark Data
  Sources now explicitly covers what used to be split across "Public
  Benchmark Data" and "Vendor Specifications" (confirmed by UC.1.11
  returning model specification and benchmark data together). Product
  Owner's inbound interface is still TBD — not exercised anywhere in UC.1.
- No changes needed to `backend/` — the stub call order in `app.py` already
  matched the corrected sequence; only the prose attribution in the docs was
  wrong.
- `README.md` — External Systems summary list updated to the current 7
  external systems (Operations Lead removed, Product Owner added, Public
  Benchmark Data + Vendor Specifications merged into Benchmark Data Sources,
  Language model runtime added), matching `docs/context.md`.

**Still open (resolved same day):** the OpsCon narrative text itself (§4.3
"Users and their concerns") still described an Operations Lead and didn't
mention a Product Owner. Left as-is initially since that text is supposed to
be copied verbatim from Innoslate, not authored here.

---

## 2026-09-19 — Daniel Distor — Claude Code

**Prompt:** Provided the Product Owner entity's actual description text from
the Innoslate model ("Accountable for the application's outcomes and
priorities. Sets the relative importance of capability, cost, and speed,
which informs the weighting applied during selection.") to close out the
open item above.

**Output:**
- `README.md` §4.3 — replaced the Operations Lead paragraph with a Product
  Owner paragraph built from the verbatim Innoslate description above.
- `docs/context.md` — Product Owner's (C.5) inbound interface updated from
  TBD to the same description; no longer an open item.

---

## 2026-10-06 — KhaiXin30 — Claude Code

**Prompt:** Build the UC.1 walking skeleton from `docs/walking-skeleton.md` with
a minimal local Flask UI: one page with a text box, Submit, and the decision
record, in black/grey/white with no logic in the UI. No LLM call and no ranking.
Each call-list step's stub returns its own section of the matched scenario's
expected record from `sample_data/`, and the plan had to be approved before
any code. Follow-ups asked for empty-input rejection, a more readable output,
and doc updates.

**Output:**
- `docs/PLAN.md`: step → function → module → output mapping for UC.1.2–1.18.
  After `sample_data/expected_outputs.json` was regrouped (by the user) into
  one section per step, every field had an owner. Updated to "implemented"
  with the UI and test-impact notes.
- `backend/llm_compass/__init__.py`: UC.1.2 finds `scenario_id` by exact match
  in `user_inputs.json` and rejects empty/whitespace text with `ValueError`
  (SN-TL-01 / 5.1.1.1). UC.1.6/1.9 pass the mapping through. UC.1.16/1.17/1.18
  return `comparison_result` / `selection_result` / `decision_record`, and
  UC.1.18 assembles the full output.
- `backend/language_model_runtime/__init__.py`: UC.1.3/1.4 stub returns
  `interpreted_requirements`.
- `backend/benchmark_data_sources/__init__.py`: UC.1.10/1.11 stub loads
  `model_spec.json`, `providers.json`, `benchmark.json`.
- `backend/app.py`: Flask app. `run_uc1()` calls the 8 functions in call order,
  and the route renders the result or the UC.1.2 rejection message.
- `backend/templates/index.html` (new): the single page. The record shows as
  one section per step, with tables for lists of objects and bullets for text
  lists, plus a collapsible raw-JSON toggle. No JS.
- `backend/requirements.txt`: added `Flask==2.2.2`, keeping the file's UTF-16
  encoding.
- `README.md`, `docs/walking-skeleton.md`: repo layout, run instructions, and
  stub notes updated to match.
- Verified with the Flask test client. All 4 scenarios render and equal
  `expected_outputs.json` exactly. Empty input shows the error. Headless-Chrome
  screenshots of scenarios 1 and 4 were checked. pytest wasn't run because it
  isn't installed on the local `python3`.

**Still open:** text that doesn't match a scenario raises `StopIteration`
(no error handling, per the brief).
`test_SN_TL_01_5_1_1_1_accepts_text_requirement` and the SPEC 5.1.3.2 record
test stay red. The section 4 signatures for `receive_requirements` and
`generate_decision_record` now differ from the skeleton's.

---

## 2026-10-07 — Allyanna Panganiban — Claude Code

**Prompt:** Given the Lab Manual, the team's business analysis, OpsCon narrative,
stakeholder needs and requirements report, product description, and the UC-01 use
case ("Select a model for an application"), asked for a plan to build the
sensitivity analysis into the UC.1 walking skeleton for Project Milestone Check 1,
on a new `allyanna` branch. Chose to implement the real logic and show it in the
UI, with per-scenario weights in a new sample-data file. Follow-ups: check the
build against the repo's own use case (README, docs/context.md, SPEC.md), show
each model's score breakdown and evidence, update the README, then build the
decision record (UC.1.18) with all six SPEC sections.

**Output:**
- `backend/llm_compass/__init__.py`: added `is_stale` (SN-TL-03 / 5.1.2.2), `rank`
  (5.1.2.1, 5.1.3.1, 5.1.6.2, 5.1.6.3, 5.3.1.1) and `unstable_pairs` (SN-TL-05 /
  5.1.4.1), using the SPEC section 4 signatures. Hard criteria exclude a model.
  Weighted criteria are min-max normalized and summed. Sensitivity varies each
  weight -10% and +10% (relative, one at a time) and reports every pair whose
  order flips, plus which change flipped it.
  - UC.1.9 `confirm_mapping` (STUB) now attaches criteria and weights.
  - UC.1.16 now computes the ranking, score breakdown, evidence with source, date
    and stale flag, exclusions, and the sensitivity finding.
  - UC.1.17 `select_model` (STUB) passes these on.
  - UC.1.18 `generate_decision_record(selection)` now matches SPEC section 4 and
    builds requirements, criteria mapping, weights, evidence, ranking, sensitivity
    and the selected model (SN-TL-09 / 5.1.3.2).
- `backend/benchmark_data_sources/__init__.py`: also returns `candidates` in the
  SPEC section 2 figure shape, built from the three sample files.
- `sample_data/scenario_criteria.json` (new): criteria and weights for each of the
  4 scenarios. These are starting values for the team to review, set so they
  reproduce the expected rankings. Scenario 4 is one hard EU-residency constraint.
- `backend/app.py`: `run_uc1` passes the confirmed mapping and requirements down
  the chain, and assembles the page from each step's output.
- `backend/templates/index.html`: lists inside a section show as text, and empty
  dicts show as "None".
- `tests/test_walking_skeleton.py` (new): computed rankings match
  `expected_outputs.json`, scenario 4 excludes all models, score breakdown and
  evidence are present, and the decision record has all six sections. The Flask
  end-to-end test is skipped in CI, which installs pytest only.
  `tests/test_technical_lead.py`: fixed a comment pointing to the wrong SPEC open
  question (7 → 5).
- `docs/PLAN.md`, `docs/walking-skeleton.md`, `README.md`: documented the new step
  mapping, the scoring and ±10% assumptions, and which sections are computed vs.
  still canned.
- Verified with pytest: 29 pass and 19 fail, up from 3 passing on `main`. The
  newly passing SPEC tests are 5.1.2.1, 5.1.2.2, 5.1.3.1, 5.1.4.1, 5.1.6.2,
  5.1.6.3, 5.3.1.1 (10 candidates) and 5.1.3.2. Every remaining failure is a
  function or walkthrough not built yet. Also checked all 4 scenarios through the
  Flask test client. Scenarios 1–3 are stable under the starting weights, and
  setting scenario 2's capability weight to 0.45 produces a Fable/Haiku flip.

**Still open:**
- SPEC section 5 Q5: ±10% is implemented as relative with no renormalization (what
  the 5.1.4.1 test assumes). Needs team confirmation.
- SPEC section 2: excluding a model with missing data for a hard constraint still
  needs team sign-off.
- The weights in `scenario_criteria.json` need team review.
- Still stubbed in UC.1: requirement interpretation (UC.1.3/1.4), reviewing and
  editing criteria and weights (UC.1.6/1.9), model selection (UC.1.17), and the
  record's summary, limitations and next action. Storing, retrieving and
  re-running records (5.1.3.3, 5.1.5.1, 5.1.5.2) aren't built.

---

## 2026-10-22 — KhaiXin30 — Claude Code (Opus 5.5)

**Built from:** F.1–F.8, the Metafunction IDEF0 in the SRD (Table 2, Fig. 2, §2.3).
F.1 isn't decomposed yet, so the seven planned functions in SRD Table 1 don't
drive modules.

**Prompt:** Lab Manual 4.4, Product Build: Module Decomposition from the IDEF0
(pp. 82–88), with SystemRequirementsDefinition.pdf as the model, run through
multiple agents with validation. The team chose the Metafunction IDEF0 and asked
for every module, including the three existing ones, to be named with its
function's verb phrase. Generation prompts: prompts/2026-10-22-icom-signatures.md
(one per function group, Component Prompt Template).

**Output:**
- Renamed `backend/llm_compass/` to `provide_llm_selection_decision_support/`
  (F.1), `benchmark_data_sources/` to `provide_benchmark_evidence/` (F.7), and
  `language_model_runtime/` to `provide_requirement_interpretation/` (F.8), with
  git mv. Imports updated in `backend/app.py` and `tests/` (module names only).
- New stub modules (signatures only), each `# STUB: <mechanism>`:
  `define_application_technical_needs/` (F.2), `define_budget_constraints/` (F.3),
  `define_compliance_constraints/` (F.4), `define_product_needs_and_priorities/`
  (F.5), `provide_technical_decision_oversight/` (F.6).
- 15 ICOM signatures, each a `def` whose body is `raise NotImplementedError`.
  Inputs are positional, controls keyword-only, outputs are return values (Table
  F-2). Each module docstring states the function ID it implements and its
  mechanism. F.1 and F.6 get one `def` per exchange, as the kiosk splits A1. The
  existing SPEC §4 functions and their bodies are unchanged.
- `docs/traceability.md` (new): one row per module with function ID, name,
  mechanism and path. `app.py` has no row, like `kiosk_service`.
- `docs/PLAN.md`: new section with the transcribed ICOM table, translation rules,
  signature table, and findings to take back to the model. Old module names in
  the earlier sections updated.
- `SPEC.md` §4: Module column only. `README.md` repo tree, `docs/context.md`
  `Module:` lines, `CLAUDE.md` source-of-truth and repo-structure rules.
- Agents: three generators (F.1; F.2–F.6; F.7 and F.8), one docs-sync agent, and
  two independent verifiers (IDEF0 criteria and Done When; spec-trace and
  end-to-end), none of which wrote the code they checked.
- Verified: pytest gives 29 passed and 19 failed on both Python 3.9.6 and 3.12,
  with the same failing set as before the change. `inspect.signature` matches all
  15 rows of the PLAN table. Every new `def` raises NotImplementedError. The
  Flask test client renders all 4 scenarios and rejects empty text.

**Assistant assumptions:**
- Each mechanism is the module itself, as in the worked example, not an injected
  parameter.
- Splitting F.1 and F.6 into one `def` per exchange. F.1's control is applied
  only from UC.1.9 on.
- `Optional[str]` instead of `str | None`, because the macOS system Python is 3.9.

**Still open:**
- Model findings for Innoslate (details in docs/PLAN.md):
  - F.8's `interpretation_request` is an input, not a control; F.7's
    `data_request` is contested.
  - Budget and compliance constraints act as inputs to `state_requirements`.
  - The confirmed mapping is content, not a control, for the data request and
    the record.
  - The stale threshold and the ±10% sensitivity policy are unmodeled controls.
  - F.6's `decision_record` arrow has no output.
  - Fig. 2's "Proposed criteria" label is clipped.
- The F.2–F.6 defs trace to model functions but to no SPEC.md ID, which conflicts
  with the CLAUDE.md rule. The team should decide.
- `confirm_mapping` and `select_model` (STUBs for the Technical Lead) still sit
  in the F.1 module and move to F.6 in Chapter 5.

---

## 2026-10-22 — KhaiXin30 — Claude Code (Opus 5.5)

**Built from:** F.1 and F.7 (IDEF0 functions), and system requirements SR 1.1.1–1.4.1
(SRD §3, generated in Innoslate from the IDEF0-A0 of F.1), with SRD Table 9
verification criteria and the Table 8 RVTM.

**Prompt:** Lab Manual 5.3, Product Build: Requirement-Driven Test Suite and First
Implementations (pp. 95–100), with SystemRequirementsDefinition.pdf as the model.
Asked to orchestrate multiple agents, validate and verify, and say which Chapter 4
open items this resolves. Prompts:
- prompts/2026-10-22-system-requirement-tests.md (tests)
- prompts/2026-10-22-f1-f7-implementations.md (bodies, filled Component Prompt
  Templates)

**Output:**
- `SPEC.md` §6 (new): the 14 system requirements, with statements, verification
  criteria, and MOP and target copied verbatim from the SRD, plus the StR trace and
  the citation and test-name convention (`SR 1.1.5`, `test_SR_1_1_5_*`).
- `tests/test_system_requirements.py` (new): one test per requirement (14 tests,
  53 cases). An agent that saw only SPEC §6, the Chapter 4 signatures and the PLAN
  interface wrote them before any body existed. The test files were hashed then
  and again after the bodies, and no test changed.
- `backend/provide_llm_selection_decision_support/__init__.py`:
  - Bodies for the five F.1 ICOM defs. F.1 holds the decision in progress.
  - The SPEC §4 helpers `validate_interpretation` and `validate_criterion`.
  - `receive_requirements` now returns a `requirement_id`.
  - A second round fixed six reviewer defects: a record mixing two mappings,
    operator/threshold mismatches, ValueError for rejections, the retry counter,
    out-of-order calls, and citations.
- `backend/provide_benchmark_evidence/__init__.py`: a `provide_model_data` body
  over the stored catalog (no live source in increment 1).
- `.github/workflows/ci.yml`: installs Flask 2.2.2 (with Werkzeug<3) next to
  pytest, so the web-interface tests run instead of being skipped. Any unmet
  requirement fails the build.
- `docs/traceability.md`: function → module, and requirement → StR → need → test →
  status.
- `docs/PLAN.md`: increment plan, interface details, findings, and the Chapter 4
  findings resolved.
- `README.md`, `CLAUDE.md`: tree and source-of-truth lines.
- Agents:
  - one test writer
  - two implementers (F.7; F.1, resumed once for the fix round)
  - two independent verifiers: Done-When, test derivation and code review; and CI
    simulation, SPEC fidelity and the app
- Verified:
  - 83 passed and 18 failed on Python 3.9.6, on 3.12, and in a fresh venv built
    exactly as ci.yml does (exit 1, 0 skipped). That was 29 passed and 19 failed
    before.
  - 11 of 14 SR tests pass.
  - 4 earlier SPEC §4 tests turned green: 5.1.1.1 accepts text, 5.1.1.2 rejects
    neither, 5.1.1.3, and 5.1.6.1.
  - The Flask app renders all 4 scenarios.


**Assistant assumptions (not yet promoted to the model):**
- F.1 holds one decision in progress in module state.
- Status values are `proposed`, `retry` and `interpretation_failed`. The caller
  re-sends to F.8 on `retry`.
- `None` stands for a timeout.
- Rejections raise `ValueError`.
- Validation rules: the known-metric vocabulary comes from F.7's benchmark ids,
  operator/threshold compatibility is checked, and a response must carry the
  request's `requirement_id`.

**Still open:**
- SR 1.2.1 and 1.4.1 need at least 10 sourced models in the catalog (3 now). SR
  1.3.1 and 1.4.1 need a logged `full_comparison` walkthrough, and SR 1.3.1 also
  needs the web confirm and select steps.
- Requirement text to repair in the model:
  - SR 1.2.2 "six" vs seven sections
  - SR 1.3.1 isn't verifiable from the walkthrough log
  - SR 1.4.1's "all leaf pass"
  - SR 1.3.3's "source unavailable"
- Bodies still pending: F.8 (LM Studio), F.6 (human), F.2–F.5 (no system
  requirement). `app.py` doesn't yet call the ICOM defs.
- Chapter 4 open items:
  - Resolved:
    - `record_decision` state
    - `today` as the mechanism's clock
    - F.6 now traces to SR IDs
    - F.2–F.5 are explained as having no system requirement
  - Confirmed but still a model fix: the confirmed mapping is content for the data
    request and the record.
  - Not resolved:
    - F.8/F.7 request roles
    - constraints in `state_requirements`
    - unmodeled stale and ±10% controls
    - F.6 `decision_record` with no output
    - Fig. 2 label
    - moving `confirm_mapping`/`select_model` to F.6, which would change
      `test_walking_skeleton.py`'s imports (forbidden this increment)

---

## 2026-10-28 — KhaiXin30 — Claude Code (Opus 5.5)

**Prompt:** Asked where the instructions require a timed walkthrough and what it
requires (answered from SPEC.md 5.1.5.2, 5.3.1.1, §4 and SR 1.4.1, and from
SystemRequirementsDefinition.pdf NFR-1/NFR-2 and TPM-3/TPM-4), and for a detailed
explanation of the derived SR 1.4.1.1 known-metrics rule. The team then decided on
two open items: keep that rule, and continue with F.1.3/F.1.4. After that, asked to
build the rest of the F.1 decomposition per docs/PLAN.md "Module plan" (IDEF0 A1 of
F.1, 2026-10-26), update the relevant documents, and log the work.

**Output:**
- `backend/provide_llm_selection_decision_support/`: one module per F.1
  sub-function, built one at a time in PLAN order (F.1.3/F.1.4, F.1.5, F.1.2, F.1.6, F.1.1).
  Signatures follow PLAN's ICOM table.
  - `apply_hard_constraints.py` (F.1.3, SR 1.4.1.3): moved from the first half of
    `rank`. Eligible candidates carry the hard-constraint figures they were checked on.
  - `score_and_rank_candidates.py` (F.1.4, SR 1.4.1.4): moved from the second half of
    `rank`. Each entry also carries `normalized` and `evidence`.
  - `analyze_ranking_sensitivity.py` (F.1.5, SR 1.4.1.5): moved from `_flips`. It
    re-scores from the ranking's normalized values, and the finding has `method`
    and `unstable_pairs`.
  - `retrieve_model_data.py` (F.1.2, SR 1.4.1.2): `request_model_data` and
    `receive_model_data`. `is_stale`, `STALE_AFTER`, `FIGURE_FIELDS`, the figure
    checks and `_metric_figure` moved here.
  - `report_selection_rationale.py` (F.1.6, SR 1.4.1.6): moved from the rest of
    `present_ranking_and_sensitivity` and the rationale built in `record_decision`.
  - `propose_criteria_mapping.py` (F.1.1, SR 1.4.1.1): the vocabulary, validators,
    `request_interpretation`, `present_criteria_mapping` and the decision-in-progress
    state moved here. New `split_confirmed_mapping` rejects a weighted criterion
    without a weight and a metric off the known metrics list.
  - `__init__.py`: the boundary ICOM defs now compose F.1.1-F.1.7, and `rank`,
    `_flips` and `unstable_pairs` compose F.1.3-F.1.5. It re-exports the moved names,
    so test and app imports are unchanged.
- `SPEC.md` §6: notes that 1.4.1.1's known-metrics rejection is derived from the A1
  control and was kept by the team on 2026-10-28.
- `docs/PLAN.md`:
  - Records both decisions, and removes the unknown hand-entered metric from
    "Accepted without rule".
  - Marks the module plan built and adds "As built" notes on what goes beyond the table.
  - Adds Progress entries with the boundary behaviour changes.
- `docs/traceability.md`: all seven modules are built, and SR 1.4.1.1-1.4.1.6 are pass.
- `README.md`: the repo-tree line for the F.1 package.
- Verified with pytest via `uv run --with pytest --with-requirements
  backend/requirements.txt --with "werkzeug<3"`. Without that pin, Flask 2.2.2 fails
  to import and the 4 walking-skeleton tests fail.
  - 87 pass and 21 fail on `main` before; 93 pass and 15 fail after.
  - SR 1.4.1.1-1.4.1.6 turned green, and nothing that passed fails.
  - Python 3.9 gives the same result on the system-requirement and Technical Lead tests.
  - The walking-skeleton tests (app path through `rank`/`_flips`) pass.

**Still open:**
- Behaviour changes for the team to confirm:
  - Excluded candidates now show only their hard-constraint figures as evidence.
  - Every received figure gets a stale flag, so an unparseable `collection_date`
    is rejected.
  - The boundary defs reject unknown metrics in the confirmed mapping.
- `_decision` lives in F.1.1, which is shared F.1 state. The PLAN finding about
  F.1.7's missing requirements/mapping/weights arrows still stands.
- `backend/requirements.txt` pins Flask 2.2.2 without a compatible Werkzeug.
- Red tests not covered here:
  - catalog < 10 (SR 1.2.1, 1.4.1)
  - no logged walkthroughs (SR 1.3.1, 1.4.1, 5.3.1.1)
  - F.8 stub (5.1.1.2 reference set)
  - 5.2.x Product Owner functions
  - 5.1.5.1 strict-xfail XPASS

---

## 2026-10-28 — KhaiXin30 — Claude Code (Opus 5.5)

**Built from:** docs/route-table.md (this increment's audit), the Lab Manual 6.4
Product Build "Endpoint-to-Use-Case Audit" (pp. 108-113), and
SYSEN5151_ArchitectureDefinitionReport.pdf (UC.1 sequence diagram Fig. 6 p13; trace
Tables 6 and 7, pp. 15-16; risk R6 p24).

**Prompt:** Complete the Chapter 6 product build task using the examples in the
manual and the Architecture Definition Report as context. Orchestrate multiple
agents, validate and verify the output, update the necessary documents, and log it.
The enumeration prompts are in prompts/2026-10-28-entry-point-enumeration.md.

**Reviewed by:** KhaiXin30. The team decided every disposition:
- the launcher is kept, with the debugger off
- the `/static/<filename>` orphan is deleted
- UC.1.19 Export is planned
- decision reuse (5.1.5.1, 5.1.5.2) is planned, once the model has a use case for it

**Output:**
- Agents, all read-only:
  - Agent 1 enumerated the entry points: 3, `GET /`, `POST /` and the launcher.
  - Agent 2 extracted UC.1, its 10 sequence interactions, and the trace from the
    report. It confirmed the 6.4.1 prerequisites are present.
  - Agent 3 then independently verified the table. It found
    a missed entry point (Flask's default `/static/<filename>`, from `app.url_map`),
    UC.1.16 and UC.1.18 overstated as "Implemented", a wrong strict-xfail claim for
    5.1.5.1, an incomplete list of the tests that store records, and two line numbers.
    I checked each claim before correcting it.
- `docs/route-table.md` (new):
  - Entry points: 4 found, 1 orphan deleted, 3 remain, all UC.1. Orphans remaining: 0.
  - CI is listed as verification tooling, not an application entry point.
  - Each UC.1 interaction is mapped to the step that serves it, with its status.
  - Items with no entry point are recorded as planned: UC.1.9 and UC.1.17 (SR 1.3.1),
    UC.1.19, and decision reuse.
  - Also: count reconciliation, other findings, and findings for the model.
- `backend/app.py`: `Flask(__name__, static_folder=None)` removes the orphan, and
  `app.run()` drops `debug=True`. Both are team decisions.
- `prompts/2026-10-28-entry-point-enumeration.md` (new): the two read-only prompts.
- `docs/PLAN.md`: new section "Endpoint-to-use-case audit (Lab Manual 6.4)" with the
  decisions, model findings and open items.
- `README.md`: route-table.md added to the repo tree; `app.py` line points to it.
- `docs/traceability.md`: a pointer to route-table.md.
- Verified:
  - `app.url_map` holds only `/`.
  - Flask test client: GET / is 200, POST / is 200 for all 4 sample scenarios,
    and `/static/x` is 404.
  - The real launcher (`python3 backend/app.py`) serves GET / with "Debug mode: off".
    Unmatched text now gets a plain 500, not the interactive debugger page.
  - pytest gives 93 passed, 15 failed, the same failing set as the previous commit.

**Assistant assumptions:** none were promoted. The mapping and dispositions are the
team's. I drafted the mapping from the agents' enumeration for the team to confirm.

**Still open:**
- Findings for the model:
  - UC.1.19 needs an output arrow.
  - A decision-reuse use case is needed for 5.1.5.1 and 5.1.5.2.
  - UC.1.16 should be renamed "Present ranking and sensitivity finding".
- SR 1.3.1 stays red until UC.1.9 and UC.1.17 have their own Technical Lead entry
  points and the UI calls the F.1 ICOM defs.
- The SR 1.1.3, SR 1.2.2 and SN-TL-06 5.1.3.3 tests write records into
  `data/decision_records/`.
- The 5.1.5.1 strict-xfail marker (XPASS) is still a pending team decision.
- Unmatched text still returns HTTP 500 from the F.8 stub.

---

## 2026-10-28 — KhaiXin30 — Claude Code (Opus 5.5)

**Prompt:** Asked whether the test records building up in `data/decision_records/` (an
open item from the 6.4 audit) needed a fix. After the explanation, asked to fix it.

**Output:**
- `tests/conftest.py`:
  - New autouse fixture `decision_record_dir` sets `DECISION_RECORD_DIR` to each
    test's `tmp_path`.
  - Test records no longer mix with real decision records (SN-TL-06 / 5.1.3.3), and
    tests no longer depend on earlier runs.
  - No test or assertion changed.
- `data/decision_records/` (gitignored): deleted 197 records after checking that
  all were test fixtures (168 with model-1/2/3, 29 with model-b/c/d).
- `docs/route-table.md`, `docs/PLAN.md`: the finding is marked resolved.
- Verified: two full pytest runs leave `data/decision_records/` empty. Results are
  unchanged: 93 passed, 15 failed, same failing set.

---
