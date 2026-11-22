# ADR-0009: Local runtime selected for F.8; model pinned to the measured build

Status: Accepted (team trade study, Week 12; implemented 2026-11-22)

Lab Manual 11.2 (Product Build: Implementing the Selected Alternative). Supersedes
the "Revisit at the Week 12 trade study" line of ADR-0001 for the in-product model.
Traces to SR 2.2.1 Local interpretation, SR 2.4.1 Query cost, SR 1.3.2 Interpretation
request and proposed criteria, SR 2.1.2 Re-evaluation effort, SR 2.1.3 Result
consistency, SR 2.3.1 Model contract.

## Context

The decision was open. The Form report's Pugh chart tied the local runtime and a
hosted commercial API. It kept the local runtime only as a provisional baseline, and
SPEC §3 marked the adapter's timeout and token limit "provisional until the Week 12
runtime trade study". Both alternatives were modelled and simulated in Innoslate (UC.1
with C.8, UC.1A with C.9) before this trade study (Modeling and Simulation report;
the Innoslate model itself is outside this repo).

- **A: local runtime (C.8).** Qwen2.5-7B-Instruct served by LM Studio on a team
  machine, at `127.0.0.1:1234`.
- **B: hosted commercial API (C.9).** OpenAI GPT-6.2 Sol through the OpenAI API.

## Criteria, objective functions and measures

| Criterion | Traces to | Value 0 → 100 | A | B | Source of the measure |
|---|---|---|---|---|---|
| EC.1 Data locality | StR 5.4.1.1; SR 2.2.1 | 0% → 100% of requests on team machines | 100 | 0 | Architecture: A sends to 127.0.0.1 (`runs_meta.json`), B to the provider |
| EC.2 Response time | StR 5.3.1.1; SR 1.3.2, SR 2.1.1 | 110 s → 1 s per request, linear | 94.5 (7.01 s) | 96.8 (4.46 s) | A measured, 150 requests; B from Artificial Analysis TTFT + 150 answer tokens at the published speed |
| EC.3 Quality | StR 5.1.1.2, 5.1.1.3; SR 2.3.1 | 80% → 100% valid on first attempt | 100 (150/150) | 100 | A measured; B **assumed** (Structured Outputs supported, not measured) |
| EC.4 Reproducibility | StR 5.1.5.2; SR 2.1.2 | changes without notice → team pins weights | 100 | 50 | A: team-chosen GGUF, identifier pinned by this ADR; B: GA models retired with ≥ 6 months' notice |
| EC.5 Availability | StR 5.3.2.1; SR 1.3.2 | one laptop → managed service | 0 | 100 | Architecture |

Swing weights (Parnell et al., 2011): EC.1 100, EC.5 70, EC.4 50, EC.3 40, EC.2 25.

## Decision

**Select A, the local runtime.** Total value: A 75.0, B 55.9. One-year life-cycle
cost: A $0.25 (electricity, upper bound), B $28.60 (API usage at 1,000 comparisons).
Under SR 2.4.1 (zero paid queries) only A is affordable, so A dominates B.
Sensitivity: B is preferred only if EC.1's weight drops below 0.198 (swing weight
about 46) or EC.5's rises above 0.367 (about 124). Every assumption test keeps A.

## What "implementing A" changed

A was already the running mechanism of F.8. Implementing it meant making the decided
configuration the enforced one:

1. **Model identifier pinned to the measured build.** The trade study's EC.2 and EC.3 measures
   come from `qwen2.5-7b-instruct-1m`, GGUF Q4_K_M (`runs_meta.json`), not the
   Q4_K_S `qwen2.5-7b-instruct` that SPEC §3 named. LM Studio answers a request for
   a model it doesn't have with whatever model is loaded. A request for
   `qwen2.5-7b-instruct` was answered by `-1m` on 2026-11-22, so the EC.4 = 100 basis
   was not actually enforced. The default model is now `qwen2.5-7b-instruct-1m`, and
   the adapter returns `None` when the reply's `model` field names any other model.
   The check compares the identifier string only. The quantization (Q4_K_M) is fixed by
   the file the team downloads, not checked at run time, and an `LLM_MODEL` override
   moves the pin to whatever it names.
   F.1.1 then retries once and marks the requirement `interpretation_failed`, so a
   substituted model can't silently produce criteria (SR 2.1.3, SR 2.3.1).
2. **Adapter limits confirmed against SR 1.3.2.** SR 1.3.2 in Innoslate states "within
   110 s per interpretation request, with responses limited to 512 tokens", so the
   timeout stays 110 s and `max_tokens` 512. The pinned model's 150 calls peaked at
   18.1 s, and its largest reply was 301 tokens (`token_probe.txt`). Both are inside
   the limits. A 1024 limit was tried, then reverted because it breaks SR 1.3.2.
   If truncated replies show up, SR 1.3.2 has to change first.
3. **Data locality guard kept.** `_check_local` still refuses any non-loopback host
   before sending (SR 2.2.1, SR 2.4.1). That guard is what EC.1 = 100 relies on.

## What the losing alternative (B) would have required

- **Infrastructure:** an OpenAI account, an API key in `.env`, and internet access
  from every deployment.
- **Integration:** a second F.8 adapter behind the same SPEC §3 model contract, plus
  handling of rate limits and network errors.
- **Requirements:** SR 2.2.1 Local interpretation changed, and the provider's
  data-processing terms reviewed with the Compliance Officer (StR 5.4.1.1). SR 2.4.1's
  zero paid-query budget would also have to change, to at least about $0.029 per
  comparison.
- **Code:** `_check_local` would have to allow the provider's host.
- **Reproducibility:** the dated model version would have to be pinned, with a
  migration at each deprecation (at least 6 months' notice).

## Consequences

- **StR 5.3.2.1 is not met.** It requires interpretation "without depending on a specific
  team member's machine", and A depends on one. EC.5 Availability = 0 is accepted: interpretation works only where the runtime
  host is. This is risk R2 in the risk assessment. The cheapest improvement the
  sensitivity analysis found is a shared team server (A rises to 87.2). That would
  need SR 2.2.1's "locally hosted" to be read as "team-controlled host", which the
  current loopback-only guard refuses. This is a team decision, not made here.
- A team machine with a different model loaded now gets `interpretation_failed`
  instead of silently different criteria. That costs time: the check runs after
  generation, and F.1.1's retry fails the same way, so about 2 x 15 s per requirement
  (`live-pin-check.txt`) before the Technical Lead is asked to enter the criteria. Fix: load
  `lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF` Q4_K_M, or set `LLM_MODEL` to what
  is loaded and accept that the trade study's measurements don't describe it.
- Not done: B was not measured (no paid account; SR 2.4.1). Its EC.3 = 100 is an
  assumption. The sensitivity test at 90% validity still selects A, so measuring B
  would not change the decision.

## Verification of the trade study's claims (2026-11-22)

- **Arithmetic and measured inputs:** `tools/swing_weight_analysis.py` recomputed
  every figure from the raw CSVs, and 70 of 71 reproduce
  (`docs/validation/trade-study/swing-weight-check.md`).
- **Sourced figures:** each one was checked against its source
  (`docs/validation/trade-study/sources-check.md`). Artificial Analysis now gives
  2.03 s / 60 tok/s for low effort, which doesn't change the result.
- **Report corrections:** listed in
  `docs/validation/trade-study/section-3-3-implementation.md`.
