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
