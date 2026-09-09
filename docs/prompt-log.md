# Prompt Log

Running log of significant AI-assisted work on this repo. Each entry: date, who,
tool, what was asked, what came out of it.

---

## 2026-09-02 — Daniel Distor — Claude Code

**Prompt:** Reviewed the course's Student Handout (project options, SE-to-build
progression, toolset guide), then asked for help writing the project README and
starting the required docs structure (`docs/environment.md`,
`docs/decisions/0001-initial-toolchain.md`, `docs/prompt-log.md`, `SPEC.md`,
`docs/context.md`) per the "Product Build — Build Steps" course slide.

**Output:**
- `README.md` — team, toolset, tool ownership, repo layout, SE-lifecycle roadmap.
  (Still missing: OpsCon narrative as its required first section — pending Innoslate
  model.)
- `docs/environment.md` — toolchain record + repo access status.
- `docs/decisions/0001-initial-toolchain.md` — first ADR.
- `docs/prompt-log.md` — this file.
- `SPEC.md` — stub, placeholder headings pending the course's Chapter 3 heading list.
- `docs/context.md` — stub, pending the team's context diagram.

**Also flagged (not yet acted on):**
- `backend/.venv/` is tracked in git despite being in `.gitignore` (~12k files,
  ~188MB) — needs `git rm -r --cached backend/.venv`.
- Repo lacks branch protection on `main`; no team member has admin access to set it
  — needs instructor/org-admin action.

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

**Output:**
- `docs/adr/0001-initial-toolchain.md` — replaces `docs/decisions/0001-initial-toolchain.md`
  (git-removed). Re-fielded as Status / Context / Decision / Rationale / What would
  change this decision (Lab Manual's labels, not the prior Nygard-style
  Context/Decision/Consequences/Revisit-if), and now explicitly frames the LLM API
  choice as the local-vs-hosted decision the Lab Manual's worked example calls for,
  with the same six-category decision table as before.
- `docs/environment.md`, `README.md` — link/path updated from `docs/decisions/` to
  `docs/adr/`.

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
