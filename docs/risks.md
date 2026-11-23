# Product risk register (Lab Manual 12.3)

The risk register for LLM Compass, kept with the code so it changes when the code does. It extends the
system risk table (report Table 15) with the AI-specific risks the lab manual lists (12.3.2) and with each
risk's control in the product. Report Section 4.5.1 (Table 20) presents this file.

**Cross-reference to the model.** "Source in the model" names the Innoslate entities (actions, functions
and assets) that each risk comes from. R1-R5 are also Risk entities in Innoslate with the same ID and name,
linked to those entities by *caused by* relationships (report Section 4.1, Figures 9-10). R6-R11 are
cross-referenced to the model through that column only.

**Ratings.** R1-R5 are the ratings in report Table 15. The reasoning for R6-R11 is in "Basis for the
R6-R11 ratings" below.

## Rating method

The scales are the ones in report Table 14. Likelihood covers the time up to the capstone review and the
first year of use.

| Rating | Likelihood | Cost impact | Schedule impact | Technical impact |
|---|---|---|---|---|
| 1 Low | 0-20%: remote | Under 2 team-hours, no cash | No slip | No effect on outputs |
| 2 Medium Low | 20-40%: unlikely | Under 1 team-day or under $10 | Under 1 day | Minor degradation, with a workaround |
| 3 Medium | 40-60%: possible | 1 to 3 team-days or under $50 | 1 to 3 days; milestone still met | A function is degraded; results usable with care |
| 4 Medium High | 60-80%: likely | Over 3 team-days or under $200 | Over 3 days; a milestone at risk | A function fails or misleads for some comparisons |
| 5 High | 80-100%: near certain | Over $200, or a paid service the team cannot fund | Misses the capstone review | No recommendation, or a wrong one |

- **Overall impact (I)** is the highest of the cost, schedule and technical impacts. The maximum is used
  rather than the average because one severe consequence, such as a wrong recommendation, is not offset
  by low cost and schedule impacts.
- **Overall risk level** = L x I, from 1 to 25. Its colour is set by the risk's cell (likelihood row,
  overall-impact column) on the Innoslate risk matrix, not by the product L x I: red high, yellow
  medium, green low (report Section 4.2).
- Risks are ranked by colour first, then by L x I.
- In Innoslate, L and I are the Probability and Consequence attributes of a Risk entity, entered as the
  middle of each 20% band (10, 30, 50, 70 or 90%).

## Register

C = cost, S = schedule, T = technical impact. **Guardrail** = the control prevents the failure;
**fallback** = the control contains it (Lab Manual 12.3.2).

| ID | Risk (type; life-cycle phase) | AI-specific category | Source in the model (caused by) | L | C | S | T | I | Level | Control in the product | Control type | Verified by | Status | Owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | Wrong interpretation: Qwen2.5 returns well-formed but wrong proposed criteria, which pass the format check (technical; development, operations) | Well-formed but incorrect output | UC.1.4; F.8; C.8 | 3 | 2 | 2 | 5 | 5 | 15 red | The validator (C.1.1.2) checks requirement ID, known metric names, operator, threshold and rating. The Technical Lead must review and confirm every criterion (CR 1.2.4). | Guardrail (partial) | CR tests; demo rehearsal | Open: units are not checked (deviation log, Innoslate item 23) | Khai |
| R2 | Runtime unavailable or too slow: the laptop running C.8 is off or LM Studio has no model loaded (technical, schedule; test, operations) | Model unavailable or slow | UC.1.4; C.8 | 3 | 1 | 3 | 4 | 4 | 12 yellow | 110 s timeout, one retry, then interpretation_failed and manual entry (SR 1.3.2). No criteria are made up. | Fallback | Fake-runtime failure tests (Chapter 8) | Open: one team laptop (accepted, report Section 3.3, ADR-0009) | [team] |
| R3 | Benchmark source lost: Artificial Analysis removes its free API tier (cost; development, operations) | — | UC.1.11; F.1.2; C.7 | 2 | 5 | 4 | 5 | 5 | 10 yellow | A failed or empty pull keeps serving the last good snapshot (SR 1.3.3). | Fallback | Data-access tests (Chapter 8) | Open | [team] |
| R4 | **Top risk.** Candidate catalog incomplete: a model named in the stated requirements is not in the catalog and silently drops out of the ranking (technical; operations) | — | UC.1.11; UC.1.12; F.1.3 | 4 | 1 | 2 | 4 | 4 | 16 red | Missing-model check (report Section 4.5.2; SR 1.4.1.8): models named in the requirements that are not in the catalog are flagged in a "Requested but not compared" box above the ranking and in the decision record, with up to three catalog alternatives (mitigation action R4.M1). The refresh reports the catalog gap. | Fallback (see below) | `tests/test_risk_r4_fallback.py` (report Table 21), SR 1.4.1.8 test; live check (`docs/validation/risk-register/r4-fallback-check.md`) | Built (SR 1.4.1.8, ADR-0010); all fallback tests pass. Likelihood stays 4 until R4.M2 runs | Khai |
| R5 | Ranking not reproducible: re-running the same requirements gives different criteria and so a different ranking (technical; operations) | Response drift between runs | UC.1.4; F.1.7; C.8 | 3 | 1 | 1 | 3 | 3 | 9 yellow | Temperature 0, fixed seed, pinned model (ADR-0009). The decision record stores the confirmed mapping, so a past decision is re-checked from the record, not by interpreting the requirements again. | Guardrail | Model-pin live check (report Table 12) | Open | [team] |
| R6 | Untrusted input reaches the prompt (technical; operations) | Untrusted input reaching the prompt | UC.1.4; UC.1.11; F.8; C.7 | 2 | 1 | 1 | 3 | 3 | 6 green | The interpretation prompt contains only the requirement text, its ID and the known-metrics list. No text from the data sources (model names, descriptions) is placed in a prompt. Source fields are used only as typed numbers or shown as escaped text. | Guardrail | Inspection of the F.8 prompt template | Open: the requirement text is operator input and is not screened | [team] |
| R7 | Response schema drift after a model update (technical; operations) | Response schema drift | UC.1.4; F.8; C.8 | 2 | 1 | 2 | 2 | 2 | 4 green | Answers from any model other than the pinned Qwen2.5-7B-Instruct-1M are rejected. The strict JSON schema is enforced on every reply; a mismatch is retried once, then interpretation_failed. | Guardrail | Model-pin tests; live check (report Table 12) | Controlled | [team] |
| R8 | Abandoned dependency: LM Studio, Flask or the Artificial Analysis API is discontinued or changes its terms (technical, cost; operations, maintenance) | Abandoned dependency | C.8; C.7; F.8 | 2 | 2 | 3 | 3 | 3 | 6 green | The adapter uses the OpenAI-compatible local endpoint, so another local runtime can replace LM Studio without code changes. Dependency versions are pinned in `backend/requirements.txt`. | Fallback | Inspection | Open | [team] |
| R9 | Data leaves the machine by an unintended path (technical, compliance; operations) | Unintended data egress | UC.1.4; UC.1.11; F.8; F.7 | 2 | 2 | 1 | 4 | 4 | 8 yellow | The F.8 adapter refuses any non-local runtime address before sending (SR 2.2.1, SR 2.4.1). The refresh command sends only GET requests with no requirement text. | Guardrail | Adapter refusal test (Chapter 8) | Open: the refresh command accepts any data-source address from `.env` without checking the host | Allyanna |
| R10 | Build knowledge concentrated in a few members: the product builds are done by two of the five members, so few others can run or rebuild the product (schedule; development) | — | Project risk; no model entity | 2 | 2 | 4 | 1 | 4 | 8 yellow | The prompt log, `docs/deployment.md` and the demo script let another member run and rebuild the product. | Fallback | Inspection | Open | [team] |
| R11 | Decision records lost: the SQLite store lives on one laptop and is not in the repository (technical; operations) | — | F.1.7; C.1.7 | 3 | 2 | 2 | 4 | 4 | 12 yellow | None yet | — | — | Open | [team] |

The six AI-specific risks in Lab Manual 12.3.2 are covered by R1, R2, R6, R7, R8 and R9. R3, R4, R10 and
R11 are conventional risks. R5 is an AI-specific risk found by the team (response drift).

## Top risk R4: fallback, not guardrail

R4 has the highest level in the register (16, red) and is the top risk (report Section 4.3).

- **What was built:** a **fallback**. A guardrail would prevent the failure, which would mean a catalog
  holding every model a Technical Lead could name. That is not possible, because new models are released
  all the time. The harm in R4 is that a model drops out silently, so the fallback contains the failure
  by making every missing model visible. This lowers R4's technical impact from 4 to 2.
- **How it works:** the check is ordinary code in C.1, not an instruction to the language model, because
  a check run by the model would itself be exposed to R1. Its five steps are in report Section 4.5.2.
- **Verified by:** `tests/test_risk_r4_fallback.py`, one test per row of report Table 21. The failure
  path is tested (T1, T5, T6, T8) and so are adversarial inputs (T3, T7), not only the normal path (T2, T4).
- **Re-rating:** with the fallback in place and its tests passing, the team re-rates R4 (expected L4 x
  I2 = 8, yellow). It should reach the residual level L2 x I2 = 4 (green) once R4.M2's refresh rule has
  run for several weeks.

## Basis for the R6-R11 ratings

Each rating applies the scales above to these points:

- **R6 (L2 x I3 = 6):** L2: no source text reaches the prompt; only the Technical Lead's own requirement
  text does, in a local single-user tool. T3: crafted text could steer the proposed criteria, but the
  validator and the Technical Lead's review stand between them and the ranking.
- **R7 (L2 x I2 = 4):** L2: drift needs a model change, and the pin rejects other models. S2 and T2: a
  drifted reply ends as interpretation_failed with manual entry as the workaround, and re-pinning plus
  retesting takes under a day.
- **R8 (L2 x I3 = 6):** L2: LM Studio and Flask are unlikely to disappear before the capstone review or in
  the first year; the loss of the AA free tier is rated separately as R3. S3 and T3: replacing the
  runtime behind the OpenAI-compatible route takes 1-3 days, with interpretation degraded until then.
- **R9 (L2 x I4 = 8):** L2: egress needs a wrong address in `.env`. T4: the refresh would send the
  Artificial Analysis key header to that host and break SR 2.2.1's local-only intent. C2: rotating the
  key takes under a day.
- **R10 (L2 x I4 = 8):** L2: two members do the product builds, but four of five have commits on `main`. S4: losing a builder close to a
  milestone puts that milestone at risk.
- **R11 (L3 x I4 = 12):** L3: one laptop holds the only copy, with no backup, over a year of use. T4: past
  decisions can no longer be re-checked (SN-TL-06 / 5.1.3.3).

### Facts checked in the code (2026-11-22)

- **R6:** `build_prompt` (`backend/provide_requirement_interpretation/__init__.py`) fills
  `prompt_template.txt` with three values only: the known-metrics list, read from the local
  `sample_data/benchmark_map.json` (not from pulled data), the requirement ID, and the requirement text.
  The result templates use Jinja autoescaping and contain no `|safe`. The requirement text goes into the
  prompt as typed, with no screening.
- **R7:** ADR-0009 pins `qwen2.5-7b-instruct-1m`. A reply that names another model is rejected, then
  retried, then marked interpretation_failed (9 adapter tests, `tests/test_data_access_component.py`).
- **R8:** the adapter posts to `<LLM_RUNTIME_URL>/chat/completions`, the OpenAI-compatible route.
  `backend/requirements.txt` pins versions with `==`, but it is saved as UTF-16 and is a full environment
  freeze: it includes packages the product does not import (for example chromadb, kubernetes,
  onnxruntime). So the "pinned dependencies" control lists more than the product uses.
- **R9:** `_check_local` refuses any runtime host other than localhost, 127.0.0.1 or ::1 before sending.
  F.7's `_url` (`backend/provide_benchmark_evidence/__init__.py`) reads `ARTIFICIAL_ANALYSIS_API_URL`,
  `MODELS_DEV_API_URL` and `OPENROUTER_API_URL` from the environment without checking the host. This is
  the open gap in the register.
- **R10:** the prompt log (`docs/prompt-log.md`), `docs/deployment.md` and the ADRs exist. Most commits on
  `main` (2026-11-22) are by three of the five members: DanielDistor 29, KhaiXin30 18, Allyanna Panganiban 17,
  turkhan1 3, none from Charlie Liu.
- **R11:** records are stored in `data/decision_records/decision_records.sqlite3`, which is gitignored.
  There is no backup or export command.
