# Data and model adapters — prompts (Lab Manual 8.5)

Main session prompt (Allyanna, 2026-11-03): execute the Chapter 8 build, steps 1–9,
following Khai's Ch 5–7 pattern. LM Studio (Bionic) with Qwen2.5 7B Instruct.
- F.8 timeout is about 3× the slowest measured time on the 4 sample scenarios, and
  max_tokens comes from the measured response size. Both are marked provisional in
  SPEC §3.
- SR 2.1.6's term list and the 5.1.5.1 XPASS are recorded as open, not resolved.
- A failed live Artificial Analysis pull keeps the snapshot fallback and is recorded
  as open.
- No passing test may fail, and no test is edited to pass.

## Agent 1: system requirement test writer

Given to one agent. It sees requirement text and the interface, never a module body.

- **Context.** LLM Compass (C.1) helps a Technical Lead pick an LLM. Lab Manual 8.5
  replaces the C.7 and C.8 stubs with a data access component and a model adapter.
  The tests come first.
- **Component.** `tests/test_system_requirements.py`. Append only.
- **Requirements.** SPEC.md §6:
  - "Input requirements for the three F.1 controls": SR 1.1.6–1.1.8.
  - "System-wide (non-functional) requirements": SR 2.1.1–2.4.1.
  - Derive every assertion from the verification criterion and MOS text.
- **Interfaces.**
  - docs/PLAN.md "Data and model adapters (Lab Manual 8.5)", "Interface details the
    tests rely on".
  - The earlier "Interface details the tests rely on" section and the signatures in
    contracts/api-v1.yaml (F.1 controls: `staleness_threshold`,
    `sensitivity_policy`, `known_metrics`).
  - tests/conftest.py fixtures may be reused.
- **Constraints.**
  - Python 3.9 and 3.12, pytest, stdlib only. No network: start a stdlib
    `http.server` on 127.0.0.1 where a runtime is needed.
  - Append to `tests/test_system_requirements.py` only. Don't change any existing
    line or any other file.
  - Don't read anything under `backend/` except signatures and docstrings.
  - Demonstration requirements (2.1.1, 2.1.2) are checked from
    docs/validation/walkthroughs.csv, as SPEC §4 says.
- **Success criteria.**
  - One test function per requirement, `test_SR_<id with underscores>_<what>`, with a
    one-line comment quoting the criterion.
  - Each new test fails now for the right reason (missing def or attribute, no
    walkthrough), or passes only where existing code already meets it.
  - Nothing errors at collection, and every existing test is untouched.
- **Out of scope.** Don't invent a criterion. SR 2.1.6's restricted term list is "to
  be defined": write no test for it and report it as not verifiable.
- **Output.** The appended tests, then a short report: each test, why it fails now,
  and anything not verifiable.

## Main session: adapter specifications (written before the code)

See SPEC.md §3 "Adapter" and docs/PLAN.md 8.5. The prompt template is
`backend/provide_requirement_interpretation/prompt_template.txt`.

## Agent 2: independent verifier

An agent that wrote none of the code. It checks:
- 8.5 Done When, item by item
- SPEC §2/§3 fidelity of both adapters
- that the schema-violation path is implemented and tested
- that no host other than localhost and the three data APIs is contacted
- that the suite matches the baseline failing set minus the fixed tests

It reports defects and doesn't fix them.
