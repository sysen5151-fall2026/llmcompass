# Prompt Log

Running log of significant AI-assisted work on this repo. Each entry: date, who,
tool, what was built, what's still open.

---

## 2026-09-02 — Daniel Distor — Claude Code

**Built:** Initial repo scaffold, per the course's toolset guide and SE-to-build
progression.

**Output:**
- `README.md` — team, toolset, tool ownership, repo layout, SE-lifecycle roadmap.
  OpsCon narrative still pending the Innoslate model.
- `docs/environment.md` — toolchain record and repo access status.
- `docs/decisions/0001-initial-toolchain.md` — first ADR.
- `docs/prompt-log.md` — this file.
- `SPEC.md` — stub, placeholder headings pending the course's Chapter 3 heading list.
- `docs/context.md` — stub, pending the team's context diagram.

**Open items:**
- `backend/.venv/` tracked in git despite being in `.gitignore` (~12k files, ~188MB);
  needs `git rm -r --cached backend/.venv`.
- No branch protection on `main`; no team member had admin access to set it at the
  time.

---

## 2026-09-08 — Daniel Distor — Claude Code

**Built:** README, SPEC, and context doc brought in line with the Week 2 slide
deck; verified against GitHub directly.

**Output:**
- `README.md` — Operational Concept replaced with the OpsCon narrative (verbatim,
  per slide 10/14); External Systems updated to the actual 7 (5 stakeholder roles +
  Public Benchmark Data + Vendor Specifications; end user of the downstream app
  excluded per the narrative); Getting started documents `python backend/app.py`.
- `SPEC.md` — reverted to a bare stub after an earlier pass had filled in Chapter
  3-level content prematurely.
- `docs/context.md` — reformatted to the course's In/Out style, matched to the 7
  external systems.
- Removed `requirement-submitter/`, `benchmark-source/`, `vendor-specification-source/`
  placeholder directories, matching the course's worked example (external systems
  live in `docs/context.md` only).
- `backend/app.py` — no-op entry point, the one missing item from the "done when"
  checklist.

**Verified against GitHub:**
- `backend/.venv/` still tracked (12,056 files).
- Branch protection on `main` confirmed not set.
- Collaborators: 5 team members, no instructor. Khai Xin has admin; everyone else
  has push/triage only.

**Open items:**
- Whether "one top-level directory per boundary element" applies to external
  actors or to LLM Compass's own internal subsystems is unresolved; went with the
  course example's structure (no per-actor folders).
- `backend/requirements.txt` is a raw `pip freeze` dump, not a curated dependency
  list.
- Repo name (`lab-project`) not yet addressed.

---

## 2026-09-09 — Daniel Distor — Claude Code

**Built:** ADR moved to match the Lab Manual's path and field structure.

**Output:**
- `docs/adr/0001-initial-toolchain.md` replaces `docs/decisions/0001-initial-toolchain.md`.
  Re-fielded as Status / Context / Decision / Rationale / What would change this
  decision, matching the Lab Manual's worked example; frames the LLM API choice as
  the local-vs-hosted decision the worked example calls for.
- `docs/environment.md`, `README.md` — links updated from `docs/decisions/` to
  `docs/adr/`.

---

## 2026-09-09 — Daniel Distor — Claude Code

**Built:** Editor/IDE row correction across README, environment doc, and ADR.

**Output:**
- `README.md`, `docs/environment.md`, `docs/adr/0001-initial-toolchain.md` —
  Editor/IDE row changed from "VS Code (Cursor rejected)" to "VS Code, Cursor —
  team uses both."

---

## 2026-09-19 — Daniel Distor — Claude Code

**Built:** UC.1 walking skeleton (Technical Lead selects a model for an
application), Product Build section, per Lab Manual §2.4.2.

**Output:**
- `docs/walking-skeleton.md` — sequence diagram transcribed as a 10-step
  numbered call list, matched to the Lab Manual's worked example format and
  checked against the Innoslate model.
- `backend/language_model_runtime/__init__.py` — `submit_requirements` stub.
- `backend/benchmark_data_sources/__init__.py` — `request_model_data` stub.
- `backend/llm_compass/__init__.py` — `receive_requirements`,
  `present_mapping_for_review`, `confirm_mapping`, `present_sensitivity_finding`,
  `select_model`, `generate_decision_record` stubs.
- `backend/app.py` — wired all stubs into a single call chain matching
  `docs/walking-skeleton.md`; verified end to end with `python3 backend/app.py`.
- All return values are hard-coded to the correct shape; no real logic, error
  handling, or retries, per this increment's scope.

**Open item:**
- `docs/context.md` states the Technical Lead's boundary is LLM Compass only.
  The current model has the Technical Lead calling Language model runtime and
  Benchmark Data Sources directly for two of the ten steps. Needs a team
  decision on whether to update the model or the doc.
