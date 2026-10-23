# System requirement tests — test-writing prompt (Lab Manual 5.3, step 1)

Given to one agent (the test-writing session). It sees requirement text, the
Chapter 4 signatures and the interface details. It is not shown any module body.

- **Context.** LLM Compass (C.1) helps a Technical Lead pick an LLM for an
  application. The Metafunction IDEF0 gave one module per function (Chapter 4).
  This increment writes one test per system requirement before any body exists.
- **Component.** `tests/test_system_requirements.py` (new file).
- **Function performed.** F.1 Provide LLM Selection Decision Support, plus F.7
  Provide Benchmark Evidence where a requirement's arrow ends there.
- **Requirements.** SPEC.md §6: all 14 statements, verification criteria and MOP
  targets, verbatim. Derive every assertion from that text, not from existing
  code.
- **Interfaces.** The signatures table and "Interface details the tests rely on"
  in docs/PLAN.md. Signatures can be inspected with `inspect.signature`. Data
  shapes are in SPEC §2 (candidate and figure) and SPEC §3 (request and response).
  The fixtures in tests/conftest.py may be reused.
- **Constraints.**
  - Python 3.9 and 3.12, pytest only, plus Flask where a test needs the web
    interface.
  - Only `tests/test_system_requirements.py` may be created. Nothing else changes.
  - Don't read the bodies of anything under backend/: signatures and docstrings
    only.
  - Drive F.1 in UC.1 order, starting each decision with `request_interpretation`.
  - Build dated figures relative to `date.today()` wherever staleness matters,
    because F.1 measures staleness against today.
  - Demonstration-method requirements (1.3.1, 1.4.1) are checked from logged
    walkthroughs in docs/validation/walkthroughs.csv, as SPEC's header says.
- **Success criteria.**
  - Exactly one test function per requirement, named
    `test_SR_<id with underscores>_<what it checks>`. Parametrizing one test is
    fine.
  - Each test has a one-line comment quoting the criterion it checks.
  - Every test currently fails for the right reason: the body raises
    NotImplementedError, the data is missing, or no walkthrough is logged.
    Nothing errors at collection.
- **Output format.** The test file only, then a short report.
- **Out of scope.**
  - Don't loosen a criterion to fit the current data. The sample catalog has 3
    models, and 1.2.1 still requires 10.
  - Don't write tests for anything not in SPEC §6.
  - Don't edit existing tests, conftest.py, SPEC.md or docs.
  - If a requirement can't be tested as written, don't invent a criterion.
    Report it as not verifiable, with the reason; the team repairs it in the model.
