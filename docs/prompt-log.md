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
