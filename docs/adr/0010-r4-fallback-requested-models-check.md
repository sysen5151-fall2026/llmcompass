# ADR-0010: R4 fallback: report requested models that are not in the catalog

Status: Accepted (implemented 2026-11-22)

Lab Manual 12.3 (Product Build: Guardrails for the Top Risk). Traces to SR 1.4.1.8 Report
models missing from the catalog (Innoslate, 2026-11-22: decomposes SR 1.4.1, satisfied by
mitigation action R4.M1, traces to StR 5.1.6.3). Risk R4 is in `docs/risks.md`; the report
covers it in Sections 4.3-4.5.

## Context

R4 Candidate catalog incomplete is the top risk (L4 x I4 = 16, red). LLM Compass ranks only
the 14 catalog models. A model named in the stated requirements that is not in the catalog
gets no data at UC.1.11 and drops out at UC.1.12 without any message. The Technical Lead
then sees a ranking without that model and thinks the product hallucinated.

The live refresh on 2026-11-22 showed how likely this is. The Artificial Analysis response
listed 765 models. Of the top 20 by intelligence index, 16 base models (variants counted
once) were not in the catalog, among them GPT-6.2 Sol, Claude Opus 5.5 and Gemini 4 Neon.

## Decision

**Build a fallback, not a guardrail.** A guardrail would prevent the failure, which would
mean a catalog containing every model a Technical Lead could name. That is not possible,
because new models are released all the time (report 4.3). The harm in R4 is that the model
drops out *silently*. A fallback contains that harm by making every missing model visible
and naming the closest catalog alternatives (R4.M1, Table 17 actions 1-3).

**Plain code, not the language model.** If Qwen were asked to notice missing models, the
check would itself be exposed to R1 (well-formed but wrong output).

**Where it runs.** Innoslate allocates SR 1.4.1.8 to no function yet. The check is built in
F.1.2 Retrieve Model Data (`check_requested_models`), because that is where the catalog
(7.1 Candidate evidence) is first available, after UC.1.11 and before F.1.3 excludes
anything (UC.1.12). Three exchanges are not on IDEF0 A1. The team adds them to the model or
accepts this divergence:

| Exchange | Role | Contract |
|---|---|---|
| Stated requirements -> F.1.2 | input | `checkRequestedModels.stated_requirements` |
| Known models list (C.7) -> F.1.2 | control | `KnownModels`, from F.7 `provide_known_models()` |
| 7.6 Requested models report, F.1.2 -> F.1.6 | input | `RequestedModelsReport`; F.1.6 passes it to the presented result and to 8.1, and F.1.7 copies it into the record |

**Matching rules.** These are contract assumptions A34-A37:
- Names are compared casefolded, with spaces, hyphens, dots and underscores removed, over runs
  of 1 to 6 words. The longest match wins, and each model is reported once.
- A catalog name takes precedence over a known-models name.
- A word from a model family ("Gemini", "GPT") that has a version number but matches no known
  name is reported as *not recognised*.
- Suggestions are up to three catalog models: the same vendor first, then the nearest on the
  intelligence index.
- If no known-models list is stored, the check reports that it *could not run*. F.1.6 with no
  report says the same, so an unchecked result is never shown as checked.

**Known-models list (step 1).** A successful refresh now also stores every listed model's
name, slug, vendor and intelligence index (new table `known_models`), and returns the
catalog gap, the R4 indicator in report Table 18. Each base model is counted once, and
variants of catalog models are not counted. The refresh makes no new requests and sends
nothing new (R9).

**F.1 boundary unchanged.** `present_ranking_and_sensitivity` (the F.1 ICOM signature) has
no known-models control, so it reports `could_not_run`. The product path (`app.py`
`run_confirmed_mapping`) runs the check. Adding the control to F.1's ICOMs is a model change.

## Consequences

- The result page shows a "Requested but not compared" box above the ranking (UC.1.15), and
  the decision record keeps the same list (UC.1.18, StR 5.1.6.3).
- R4's technical impact falls from 4 to 2: a missing model now leaves the ranking with a
  message and a workaround. Its likelihood stays 4 until R4.M2 (adding missing top-20
  models at each refresh) has run for several weeks.
- **Known limitations:**
  - A requirement that uses a listed model's exact name in another sense (for example a model
    called "Step 3") is flagged. This false positive is visible and harmless.
  - A model named with no family word and no listed name (a brand-new family) is not
    flagged. The catalog-gap indicator and the review points in report Table 19 cover that.
- **Verification:** `tests/test_risk_r4_fallback.py` (report Table 21, T1-T8 plus F.7 and
  page tests) and `test_SR_1_4_1_8_...` in `tests/test_system_requirements.py`. The live
  check is in `docs/validation/risk-register/r4-fallback-check.md`.
