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
