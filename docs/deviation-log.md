# Deviation log: C.1.1 Criteria Mapper, raw generation (Lab Manual 9.4)

## What was generated, from what, how

- **What.** Four modules in
  `backend/provide_llm_selection_decision_support/propose_criteria_mapping/`:
  `request_interpretation.py` (F.1.1.1, C.1.1.1 Interpretation Client),
  `validate_proposed_criteria.py` (F.1.1.2, C.1.1.2 Criteria Validator),
  `present_criteria_mapping.py` (F.1.1.3, C.1.1.3 Mapping Presenter),
  `distribute_confirmed_mapping.py` (F.1.1.4, C.1.1.4 Mapping Distributor). 322 lines in all.
  They are in commit `3be0122` "Lab 9.4 raw one-pass generation of C.1.1.1-C.1.1.4 (unmodified)"
  on branch `ch9-raw-generation`, whose parent `bbab2d3` is the spec and contract base.
- **From what.** SPEC.md §7 (C.1.1 component specification, CR 1.1.1–2.4.1, verbatim from the
  Form report Tables 3, 9, 10), SPEC.md §3 (model contract and adapter), SPEC.md §2 (data contract),
  and `contracts/api-v1.yaml` v1.1.0: the operations requestInterpretation, validateProposedCriteria,
  presentCriteriaMapping and distributeConfirmedMapping, their schemas, and assumptions A28–A31.
  The prompt was `prompts/2026-11-03-criteria-mapper-component.md`, section "Agent 2" (the full
  Component Prompt Template).
- **How.** One pass with no follow-up corrections. The generator had no access to tests/ bodies,
  `_first_level.py` or the package `__init__.py`.
- The component is C.1.1 as a whole — the decomposed subsystem whose specification Lab Manual 9.2–9.3 asks for — so all four of C.1.1.1–C.1.1.4 were generated together; the Milestone 2 demo also needs all four running.
- **Audit.** An independent auditor wrote this log. The auditor did not write the spec
  transcription, the tests or the code, read every line of the raw commit against every CR, the
  contract text and the prompt constraints, and ran edge-case probes against the raw code without
  changing anything. Line numbers refer to the files as they are in `3be0122`.

## Test results on the raw code

- `tests/test_component_criteria_mapper.py` (written from the spec before the code existed):
  **103 passed, 16 failed.** All 16 failures are demonstration tests (CR 1.2.4, CR 1.3.6,
  CR 1.4.3 and CR 2.1.1, four scenarios each). They need `mapping_review:<scenario>` walkthrough
  rows in `docs/validation/walkthroughs.csv`, which no code can supply. The auditor re-ran the file
  and got the same result.
- Existing suite: unchanged against the baseline (129 passed, 13 failed, same test names).
- `contracts/check_conformance.py`: no divergence for the four operations.
- Prompt constraints that were met: exactly four new files; each module docstring has the
  required `"""Implements F.1.1.x -- <Verb phrase>. Mechanism: C.1.1.x <Component name>."""`
  form; stdlib only (`logging`, `re`, `copy`, `urllib.parse`, `typing`); no network access except
  through the F.8 adapter; def names, parameter kinds and defaults match the generated stubs;
  return order matches each `x-return-order`.

## Deviation table

Class: **spec defect** means the spec was silent, ambiguous or wrong, so any reader would have to
guess. **Assistant error** means the spec was clear and the code doesn't follow it. **Unrequested
addition** means code or behaviour the spec did not ask for.
Resolution: **keep** (promote the assumption to a requirement), **fix code**, or **fix
contract/SPEC**.

| ID | Where (raw `3be0122`) | What the specification said | What the code did | Why the gap probably appeared | Class | Proposed resolution |
|---|---|---|---|---|---|---|
| D-01 | `request_interpretation.py:15-23, 35` | A30: "How the stated text is divided into separate stated requirements is not fixed by the model." SPEC 7: C.1.1.1 "assigns an identifier to each stated requirement". | Each non-blank line becomes one stated requirement. A wrapped paragraph becomes several requirements. All four sample scenarios are single paragraphs, so each gives exactly one requirement and one request, which matches the Lab 8.5 measurements. | The model leaves the splitting rule open, so the generator had to pick one (generator assumption 1). | spec defect | Keep. Promote to a requirement under CR 1.1.4 (Innoslate item 1). |
| D-02 | `request_interpretation.py:10-11, 20` | SR 1.2.3 criterion: "Exactly one interpretation request is issued for each stated requirement, carrying its ID and **unaltered text**." A29: "Stated requirements is the text the Technical Lead typed." SPEC 3 Adapter: the request's `text` goes into the prompt "unaltered". | Strips a leading list marker (`-`, `*`, `•`, `1.`, `2)`) and surrounding whitespace from each line before the line becomes the requirement text. The text sent and stored in the decision basis is therefore not what was typed. Only one marker is stripped: `"- 1. foo"` becomes `"1. foo"`. | Layout clean-up chosen as part of the splitting rule (generator assumption 1). Nothing in the spec asked for it. | unrequested addition | **Fix code**: remove the marker stripping and keep only the trimming of leading and trailing whitespace. Promote the trimming (Innoslate item 4). The team can instead promote marker stripping, but then SR 1.2.3's "unaltered" must be redefined. |
| D-03 | `request_interpretation.py:41` | InterpretationRequest / RequirementSet: `requirement_id` is a string with minLength 1. No format and no uniqueness scope is given. | Identifiers are positional (`REQ-1`, `REQ-2`, ...). They are deterministic for the same text but repeat across comparisons, which feeds the cross-comparison leak in D-09. | The identifier scheme is unspecified (generator assumption 1). | spec defect | Keep (determinism supports SR 2.1.3). Promote with an explicit uniqueness scope of one comparison (Innoslate item 2). |
| D-04 | `request_interpretation.py:33-37` | Contract: `stated_requirements` is a `string` with `minLength: 1`, and 422 is returned when it is "not text, or empty". | Whitespace-only text such as `"   \n "` raises ValueError "stated requirements are empty", although the schema accepts it (length ≥ 1). | "Empty" is not defined: it could mean zero length or no non-blank text. The test writer reported the same gap. | spec defect | Keep. **Fix contract**: add `pattern: "\\S"` to `stated_requirements` and say "contains no non-whitespace text". Promote (Innoslate item 3). |
| D-05 | `request_interpretation.py:51-76` | SPEC 7: C.1.1.1 "assigns an identifier to each stated requirement and **sends it** to the language model runtime"; CR 1.2.3; CR 1.3.7. The contract has no operation that sends flow 2: requestInterpretation only *returns* the requests, and A24 puts F.1.1's boundary-only exchanges out of scope. | Adds a public def `send_interpretation_request(interpretation_request) -> Optional[dict]` that is not in the contract. It is the only caller of `provide_requirement_interpretation.propose_criteria` and it raises ValueError on a malformed request. | The behaviour SPEC 7 requires has no contract operation, so the generator added one of its own (generator assumption 2). | unrequested addition | Keep. **Fix contract** first: add a `sendInterpretationRequest` operation (flow 2 out, flow 3 in) with an ADR under `docs/adr/`, then regenerate the stubs. Promote (Innoslate item 5). |
| D-06 | `request_interpretation.py:59-63, 68-72` | SPEC 3 Adapter: the **adapter** raises ValueError for any host other than localhost, 127.0.0.1 or ::1 "before anything is sent". CR 2.2.1 and CR 2.4.1 are verified by inspection of the runtime configuration and run logs. | Re-checks the request shape (exactly `{requirement_id, text}`, both non-empty strings), and also re-checks the runtime host from `runtime_config()["base_url"]` with its own `_LOCAL_HOSTS`. Both checks duplicate the adapter's. | Defence in depth, so that CR 2.2.1 and CR 2.3.1 hold inside the component even if the adapter changes. | unrequested addition | Keep: it puts CR 2.2.1 and CR 2.3.1 inside C.1.1, where the CRs are allocated. Promote (Innoslate item 6). |
| D-07 | `request_interpretation.py:65` | Project rule (CLAUDE.md): `# STUB: <system name>` marks stubs for external systems. SPEC 3 "Adapter" and the prompt describe `propose_criteria` as the real, implemented F.8 adapter (Lab 8.5). | Marks the real adapter call `# STUB: Language model runtime`. An inspector checking STUB markers would wrongly count live interpretation as stubbed. | The marker was copied from the adapter's own walking-skeleton comment style without checking whether the call is a stub. | assistant error | **Fix code**: replace the marker with a plain comment such as "Language model runtime, reached only through the F.8 adapter (C.8, SPEC 3 Adapter)". |
| D-08 | `request_interpretation.py:8, 47, 74`; `validate_proposed_criteria.py:7, 151` | CR 1.2.3 and CR 1.4.1 are verified by "T: request log per scenario". SPEC defines no request log: no location, format, fields or retention. | Uses `logging.getLogger(__name__).info(...)`. The root logger's default level is WARNING (the probe measured 30), so nothing is recorded unless the application configures logging. Line 47 logs each request when it is **built**, before it is sent. The reason a response was invalid goes only to this log, and ValidatedCriteria carries no reason (generator assumption 6). | "Request log" is named as a verification artefact but never specified. | spec defect | **Fix SPEC** (§7 note or §4): define the request log (where it goes and which fields: requirement_id, text, time sent, outcome, invalidity reason). Then fix the code: log at send time to that sink. Promote (Innoslate item 12). |
| D-09 | `validate_proposed_criteria.py:15-16, 112, 127, 133, 144-150` | Contract validateProposedCriteria: "An invalid response gives status retry **the first time** for that requirement and interpretation_failed **the second**." This is history-dependent output from a signature with no attempt or history input. A31 leaves the re-send open. Prompt success criterion: "the defs are deterministic for the same input". | Keeps a process-global dict `_failures`, keyed by `(requirement_id, text)` and cleared on a valid result or on interpretation_failed. The same input gives `retry`, `interpretation_failed`, `retry` on three calls (probed). The state leaks across comparisons and sessions: a retry left over from an abandoned comparison makes the **first** null response of a new comparison with the same first requirement `interpretation_failed` (probed). It is not thread-safe. | The contract requires memory but gives the operation nowhere to keep it, so the state ended up in the module (generator assumption 3). | spec defect | **Fix contract**: give validateProposedCriteria an explicit attempt count, or the previous ValidatedCriteria, as a keyword control, and scope it to one comparison. Then fix the code. The current tests call the def twice with the same inputs and expect retry then interpretation_failed, and tests must not be edited, so the default (no attempt given) must keep that behaviour. Promote (Innoslate item 8). |
| D-10 | `validate_proposed_criteria.py:104-114` | Contract: proposed_criteria is "null when there was no response or it timed out". The inputs are the response and the whole requirement set, and nothing says which request the response answers. | A null response, or one whose requirement_id is not in the set, is charged to the requirement already awaiting a retry, or else to the **first** requirement. A response with id `REQ-9` was charged to `REQ-1` (probed), so the requirement that was really asked is never marked. When two requirements are both awaiting a retry, the first one is chosen. | A null response cannot be attributed from the given inputs (generator assumption 4). | spec defect | **Fix contract**: add the interpretation request (or its requirement_id) as an input to validateProposedCriteria. Then fix the code to attribute by that input. Promote (Innoslate item 8). |
| D-11 | `validate_proposed_criteria.py:86, 107-109` | SPEC 7 C.1.1.2: "rejecting a response whose requirement identifier does not match **its request**". Contract: "does not match **a request in the requirement set**". | Follows the contract. A response to REQ-2's request that carries `"requirement_id": "REQ-1"` is accepted as a valid result for REQ-1 (probed: status `proposed`). | The contract wording is weaker than SPEC 7, and the signature cannot express "its request" (see D-10). | spec defect | **Fix contract** so it matches SPEC 7 ("does not match the request it answers"), together with D-10. Then fix the code. |
| D-12 | `validate_proposed_criteria.py:12-13, 61-62, 84-85` | SPEC 3: a "wrong schema" response is bad. It lists the keys but has no rule on extra keys. The ProposedCriterion schema has no `additionalProperties: false`, so the contract accepts extra keys. | Any missing **or extra** key, in the response or in a criterion, makes the response invalid. | "Wrong schema" is undefined, so the generator chose a strict reading (generator assumption 5). The F.8 adapter's strict `json_schema` response format points the same way. | spec defect | Keep. **Fix contract**: add `additionalProperties: false` to the response schema (see T-1) and to ProposedCriterion. Promote (Innoslate item 9). |
| D-13 | `validate_proposed_criteria.py:98-100`; `distribute_confirmed_mapping.py:56-59` | SPEC 3 validity rules and the distributeConfirmedMapping 422 list have no criterion_id uniqueness rule. | A duplicate `criterion_id` in one response is invalid, and a duplicate in the confirmed mapping raises ValueError. | Weights are keyed by criterion_id (A20), so a duplicate would silently merge two criteria (generator assumptions 5 and 10). | unrequested addition | Keep. **Fix contract**: add the rule to the validateProposedCriteria description and to the distributeConfirmedMapping 422. Promote (Innoslate item 10). |
| D-14 | `validate_proposed_criteria.py:67, 71, 73` | SPEC 3: a bad response ("wrong schema") gets "retry once", then `interpretation_failed`. The contract declares **no** error response for validateProposedCriteria. | `criterion["operator"] not in OPERATORS` (and the same for `proxy_strength` and `category`) raises **TypeError** when the value is a list or dict (unhashable). The probe raised TypeError on `operator: []`, `proxy_strength: {}` and `category: []`. A malformed runtime reply crashes the validator instead of giving `retry`. | Membership is tested before the type, and the generator did not consider non-string values. | assistant error | **Fix code**: check `isinstance(value, str)` before each enum membership test, and return a problem string instead of raising. |
| D-15 | `distribute_confirmed_mapping.py:18, 20, 24` | Contract distributeConfirmedMapping: 422 → **ValueError** for "a criterion without a valid designation ... or a metric not on the known metrics list". | `criterion.get("metric") not in known`, `... not in OPERATORS` and `... not in DESIGNATIONS` raise **TypeError** for an unhashable value (probed for metric, designation and operator). | Same cause as D-14. | assistant error | **Fix code**: check `isinstance(value, str)` before each membership test, so the def raises ValueError as declared. |
| D-16 | `validate_proposed_criteria.py:152` | ValidatedCriteria requires `no_suitable_proxy`. Its description says retry and interpretation_failed come "with no criteria", and says nothing about `no_suitable_proxy`. | Failure results set `no_suitable_proxy: false` and `criteria: []`, and carry no reason. | The value is unspecified (the test writer reported the same gap). | spec defect | Keep. **Fix contract**: state `no_suitable_proxy` is false on retry and interpretation_failed. Promote (Innoslate item 11). |
| D-17 | `validate_proposed_criteria.py:48-55, 126`; `present_criteria_mapping.py:11-12, 18-19` | The contract declares **no** error response for validateProposedCriteria or presentCriteriaMapping, yet their inputs have `minItems: 1` (RequirementSet, `validated_criteria`). | Both raise ValueError on an empty or malformed list (generator assumption 9). The presenter raises **KeyError** for an entry without `requirement_id` (probed), which is neither declared nor ValueError. | The schemas constrain the inputs, but the operations declare no error for violating them. | spec defect | **Fix contract**: add a 422 / `x-python-raises: ValueError` to both operations and regenerate the stubs. Then fix the code: the presenter raises ValueError for a malformed entry. |
| D-18 | `present_criteria_mapping.py:17-20` | Contract presentCriteriaMapping: "Presents the validated criteria of **every stated requirement**". Table 3: the presenter's only input is Validated criteria, with no requirement set. Nothing says what happens when a requirement appears more than once (after a retry). | Keeps the **latest** entry for each requirement_id, in first-seen order. A requirement that was never validated is silently absent, because without the requirement set the presenter cannot tell. | The model gives the presenter no way to check "every", and no rule for repeated results (generator assumption 8). | spec defect | Keep the latest-result rule. **Fix model/contract**: either add Requirement set (1.0.1) as an input to F.1.1.3, or state that the caller passes exactly one final result per requirement. Promote (Innoslate item 13). |
| D-19 | `request_interpretation.py:44`; `present_criteria_mapping.py:15-16`; `validate_proposed_criteria.py:21-22` | Prompt: cite CRs in comments on the code that implements them. Comments must describe the code accurately. | Three comments are wrong. (a) Line 44 says "text unaltered", but the text was marker-stripped at line 20 (D-02). (b) The presenter says "in the order the requirements were stated", but the order is the first-seen order of its input. (c) The validator says the list is "read ... at call time, so a changed list is the one used", but `BENCHMARK_IDS` is built when `provide_benchmark_evidence` is imported, so an edit to `benchmark_map.json` takes effect only after a restart (only a patched module attribute or an explicit `known_metrics` is picked up). | The comments state what was intended, not what the code does. | assistant error | **Fix code**: correct the three comments. |
| D-20 | `validate_proposed_criteria.py:9-11, 19-30, 33-45`; `distribute_confirmed_mapping.py:6, 8` | The contract defines one public def per module. The prompt allows exactly the four defs from the stubs. | Adds public names that are not in the contract: `configured_known_metrics`, `resolve_known_metrics`, `threshold_fits`, `OPERATORS`, `PROXY_STRENGTHS`, `CATEGORIES`, `DESIGNATIONS`. C.1.1.4 imports C.1.1.2's module (component-to-component code coupling). The constants duplicate same-named constants (`OPERATORS`, `CATEGORIES`, `PROXY_STRENGTHS`, `DESIGNATIONS`, `KNOWN_METRICS`) that the package `__init__.py` re-exports from `_first_level.py`, which the generator was not allowed to read. The requirement-set check is also copied between the two modules (`validate_proposed_criteria.py:48-55`, `distribute_confirmed_mapping.py:43-48`). | Shared vocabulary for the known metrics list, which SPEC 7 makes a control on both C.1.1.2 and C.1.1.4, with no designated home. | unrequested addition | **Fix code**: make the helpers private (leading underscore) and keep one copy of the requirement-set check. The C.1.1.4 → C.1.1.2 import may stay, because both take the same control (SPEC 7), but record it in `docs/traceability.md`. |
| D-21 | `validate_proposed_criteria.py:19-25` | SPEC 3: "every `metric` exists in section 2". SPEC 2: "AA-Omniscience is **dropped**" and SPEC 5 Q12 is open. KnownMetricsList `x-configured-value`: "SPEC 2 **candidate field names** plus every known benchmark_id". Prompt: "SPEC 2 candidate **figure** field names plus every known benchmark_id". | Known metrics = `FIGURE_FIELDS` ∪ `BENCHMARK_IDS`: 12 metrics, which include `aa_omniscience_index` (still in `benchmark_map.json`) and exclude the non-figure candidate fields (`model_id`, `vendor`, `model_name`, `benchmarks`). | SPEC 2 conflicts with the benchmark map data, and the contract's "candidate field names" differs from the prompt's "figure field names" (generator assumption 7). | spec defect | **Fix SPEC/contract**: decide SPEC 5 Q12 (keep or remove `aa_omniscience_index` from `benchmark_map.json`), and change `x-configured-value` to "SPEC 2 candidate **figure** fields". Promote (Innoslate item 15). |
| D-22 | `distribute_confirmed_mapping.py:20-23, 26-29` | Contract distributeConfirmedMapping rejects only three cases: "a criterion with no valid designation, a weighted criterion without a numeric weight, and a metric not on the known metrics list". (The Criterion schema does carry an operator enum, `weight minimum: 0` and the threshold/operator rule.) | Also rejects an operator outside `>= <= == in`, a threshold that does not fit its operator, and a negative weight. | The generator enforced the Criterion schema constraints although the 422 list does not name them (generator assumption 10). | unrequested addition | Keep: hand-added criteria must pass the same rules as proposed ones. **Fix contract**: extend the 422 description. Promote (Innoslate item 14). |
| D-23 | `distribute_confirmed_mapping.py:41-42, 54-55, 69-73` | ConfirmedCriteriaMapping has no `minItems`. A27: F.1.7 **rejects** a record whose `criteria_mapping` or `weights` is empty (ValueError / 422). CR 1.2.1 is verified by "I: exported record per scenario". | Accepts an empty confirmed mapping (all outflows empty, `weights: {}`). It also accepts a hard-only mapping, which gives `weights: {}`. SCENARIO_04 (EU residency, a hard constraint only) therefore produces a decision basis that F.1.7 must reject, so no record can exist for CR 1.2.1. | The contract does not say whether an empty or hard-only mapping is valid, and A27 conflicts with hard-only scenarios (generator assumption 11; the test writer reported the same gap). | spec defect | **Fix SPEC/contract**: (a) the distributor rejects an empty mapping (add to the 422); (b) the team decides whether a hard-only mapping yields a record (relax A27 / SR 1.2.2 for `weights`). Promote (Innoslate items 16, 17). |
| D-24 | `distribute_confirmed_mapping.py:43-48, 69-70` | Contract: C.1.1.4 splits the mapping "with the requirement set". Criterion.requirement_id is "The stated requirement this criterion stands for". No rule ties the two together. | The requirement set is used only to build `decision_basis.requirements`. A criterion's `requirement_id` is not checked against the set, so the basis can reference requirements that are not in it. | The distributor's use of the requirement set is unspecified (generator assumption 11). | spec defect | **Fix contract**: state that a criterion carrying a `requirement_id` must name a requirement in the set (hand-added criteria may omit it). Then fix the code. Promote (Innoslate item 18). |
| D-25 | `request_interpretation.py:51-76`; `validate_proposed_criteria.py:142-150` | SPEC 3: "retry once. If it fails again, mark the requirement interpretation_failed". A31: "Which element re-sends the request after a retry status is not fixed by the model." | No C.1.1 component re-sends. The validator only returns `status: retry`, and the re-send is left to the (out-of-scope) first-level composition. | The model does not allocate the re-send (generator assumption 2). | spec defect | **Fix model**: allocate the re-send to C.1.1.1, the only component that talks to the runtime (SPEC 7). Then add it to the code with the D-05 contract operation. Promote (Innoslate item 7). |
| D-26 (verifier) | `distribute_confirmed_mapping.py:11-29` | The Criterion schema gives `proxy_strength` and `category` enums. The distributeConfirmedMapping 422 list does not name them. | Accepts any `proxy_strength` / `category` on a confirmed criterion (probe: "bogus" accepted). | The 422 list names only designation, weight and metric; the schema's enums are not stated as a rejection rule. | spec defect | Keep; promote (Innoslate item 20). The web UI now leaves both out for hand-added criteria instead of inventing them. |
| D-27 (verifier) | `distribute_confirmed_mapping.py:28`; `validate_proposed_criteria.py:34-35` | Weights: number, minimum 0 (A20). Thresholds: number per SPEC 3. | NaN and inf pass `weight < 0` and the number checks; a NaN weight later fails in F.1.7's `json_valid` CHECK (HTTP 500 on the web path). | "Number" was not said to be finite; JSON has no NaN, so the spec never needed to. | spec defect | Web UI rejects non-finite weights and thresholds before C.1.1.4 (app.py). Promote (Innoslate item 21). |
| D-28 (verifier) | `validate_proposed_criteria.py:48-55`; `distribute_confirmed_mapping.py:43-48` | RequirementSet items need a non-empty requirement_id; nothing says unique. | Duplicate requirement_ids in a requirement set are accepted. | Uniqueness was implied by "an identifier to each stated requirement" but not stated. | spec defect | Keep (C.1.1.1 never makes duplicates); promote (Innoslate item 22). |

### Checked and not deviations

These generator assumptions or code features were checked and match the spec:

- Generator assumption 5, partly: `bool` is not accepted as a number (`_is_number`), because JSON
  `true` is not a number under SPEC 3. `in` requires a list (SPEC 3: "`in` takes a list"), and a
  null threshold is accepted for `>=`, `<=` and `==` as SPEC 3 says.
- Generator assumption 11, partly: `decision_basis.requirements` is the requirement set as
  `{requirement_id, text}` objects, which A19 and StatedRequirement allow.
- Timeout and unreachable runtime arrive as `None` and are handled like an invalid response
  (SR 1.3.2). A valid response gets `requirement_id` added to each criterion (ProposedCriterion:
  "added by C.1.1.2"), and confirmed criteria pass to every outflow as deep copies, unmodified
  (CR 2.1.2).
- CR citations: every CR in §7 is cited in a code comment except **CR 2.1.1** (Mapping review
  effort). That CR is a timed demonstration that no code implements, so the omission is correct.

## Spec defects found by the test writer

These are contract or SPEC problems that do not appear as a code difference, or appear only
through the rows cited.

| ID | Defect | Proposed fix |
|---|---|---|
| T-1 | The validateProposedCriteria description says "(ProposedCriteria when valid)", but the contract has **no `ProposedCriteria` schema**. `proposed_criteria` is a bare `type: object`, so the SPEC 3 response shape is not in the contract at all. | Add `components/schemas/ProposedCriteria` (the SPEC 3 response: `requirement_id`, `no_suitable_proxy`, `criteria: [ProposedCriterion]`, `additionalProperties: false`, see D-12) and reference it from `proposed_criteria` with `nullable: true`. Regenerate the stubs. |
| T-2 | `threshold` in Criterion and ProposedCriterion is `nullable: true` next to a **typeless `oneOf`**. In OAS 3.0.3, `nullable` takes effect only together with an explicit `type`, so an OAS30 validator rejects `null`, while SPEC 3 allows `null` for `>=`, `<=` and `==`. | Move `nullable: true` into exactly one branch, e.g. `oneOf: [{type: number, nullable: true}, {type: string}, {type: array, items: {}}]`, so null matches one branch only. Apply this in both schemas. |
| T-3 | SPEC names **no walkthrough label** for the mapping review. SPEC 4 defines only `rerun` and `full_comparison`, yet CR 1.2.4, CR 1.3.6, CR 1.4.3 and CR 2.1.1 are demonstrations "checked from docs/validation/walkthroughs.csv as in section 4". The tests use `mapping_review:<scenario_id>`. | Add `mapping_review:<scenario_id>` (one row per sample scenario, minutes ≤ 10 for CR 2.1.1) to SPEC 4 and the SPEC 7 notes. A team member then logs the 16 walkthroughs. |
| T-4 | It is unclear whether whitespace-only input counts as "empty". | See D-04. |
| T-5 | `no_suitable_proxy` on failed results is unspecified. | See D-16. |
| T-6 | SCENARIO_04 has no weighted criteria, so no record can be produced for CR 1.2.1 under A27. | See D-23. |
| T-7 (auditor) | The second-level distributeConfirmedMapping returns (5.1, 5.2, 5.3, 5.4), but the first-level splitConfirmedMapping returns (5.3, 5.2, 5.1) (A1). The A28 compositions must reorder, and nothing says so. | Add a sentence to A28: "split_confirmed_mapping reorders the F.1.1.4 outputs to the A1 order." |

## To add in Innoslate

**Claude Code cannot edit Innoslate.** A team member must enter these requirements in the model
(Lab Manual 9.4 Done When). Each item names the CR it sits under and the deviation it resolves.
Items 4, 16 and 17 depend on a team decision noted in the item.

1. (under CR 1.1.4; D-01) The Criteria Mapper shall treat each non-blank line of the stated requirements as one stated requirement.
2. (under CR 1.4.1; D-03) The Criteria Mapper shall identify each stated requirement as `REQ-<n>`, where n is its position in the stated requirements, unique within one comparison.
3. (under CR 1.1.4; D-04) The Criteria Mapper shall reject stated requirements that contain no non-whitespace text.
4. (under CR 1.2.3; D-02, if the code fix is accepted) The Criteria Mapper shall send each stated requirement's text as typed, with only leading and trailing whitespace removed.
5. (under CR 1.2.3 / CR 1.3.7; D-05) The Criteria Mapper shall send each interpretation request to the Language model runtime through the F.8 adapter and pass the response, or null when there was none, to the Criteria Validator.
6. (under CR 2.2.1; D-06) The Criteria Mapper shall refuse to send an interpretation request when the configured runtime host is not localhost, 127.0.0.1 or ::1.
7. (under CR 1.4.1; D-25) The Criteria Mapper shall re-send an interpretation request once when its response is invalid or missing, and shall send it no more than twice in one comparison.
8. (under CR 1.4.2; D-09, D-10, D-11) The Criteria Mapper shall validate each response against the interpretation request it answers, and shall count invalid responses per stated requirement within one comparison only.
9. (under CR 2.3.1; D-12) The Criteria Mapper shall treat a response, or a criterion in it, with keys missing from or added to those of the model contract as invalid.
10. (under CR 1.4.2 and CR 1.1.1; D-13) The Criteria Mapper shall treat two criteria with the same criterion_id, in one response or in the confirmed mapping, as invalid.
11. (under CR 1.4.2; D-16) The Criteria Mapper shall report a requirement awaiting retry or marked interpretation_failed with no criteria and with no_suitable_proxy false.
12. (under CR 1.2.3; D-08) The Criteria Mapper shall record in a request log, for each interpretation request sent, its requirement_id, text, time sent and outcome, including the reason when the response was invalid.
13. (under CR 1.4.3; D-18) The Criteria Mapper shall present each stated requirement exactly once, with its latest validation result, in the order of the requirement set.
14. (under CR 1.1.1; D-22) The Criteria Mapper shall reject a confirmed criterion whose operator is not >=, <=, == or in, whose threshold does not fit its operator, or whose weight is negative.
15. (under CR 1.1.2; D-21) The Criteria Mapper shall use as the known metrics list the SPEC 2 candidate figure fields plus every benchmark_id in the benchmark map. (The team must first decide SPEC 5 Q12 on `aa_omniscience_index`.)
16. (under CR 1.1.1; D-23) The Criteria Mapper shall reject an empty confirmed criteria mapping.
17. (under CR 1.2.1; D-23, team decision) The Criteria Mapper shall provide a decision basis for a confirmed mapping that has hard constraints only, with empty weights. (SR 1.2.2 and A27 must then allow empty weights. Otherwise replace this with "shall reject a confirmed mapping with no weighted criterion".)
18. (under CR 1.1.1; D-24) The Criteria Mapper shall reject a confirmed criterion whose requirement_id, when given, is not in the requirement set.
19. (under CR 1.2.4, CR 1.3.6, CR 1.4.3, CR 2.1.1, verification method; T-3) The Criteria Mapper's mapping review shall be demonstrated by walkthroughs logged in docs/validation/walkthroughs.csv with scenario `mapping_review:<scenario_id>`, one per sample scenario.
20. (under CR 1.1.1; D-26) The Criteria Mapper shall reject a confirmed criterion whose proxy_strength or category, when given, is not one of the model contract's values.
21. (under CR 1.1.1; D-27) The Criteria Mapper shall reject a confirmed criterion whose weight or numeric threshold is not a finite number.
22. (under CR 1.4.1; D-28) The Criteria Mapper shall give every stated requirement in one comparison a different identifier.

The contract-only fixes (T-1, T-2, T-7, and the 422 additions in D-17 and D-22) go in
`contracts/api-v1.yaml`, not in Innoslate.

## Summary by class

| Class | Count | Rows |
|---|---|---|
| spec defect | 18 | D-01, D-03, D-04, D-08, D-09, D-10, D-11, D-12, D-16, D-17, D-18, D-21, D-23, D-24, D-25, D-26, D-27, D-28 |
| assistant error | 4 | D-07, D-14, D-15, D-19 |
| unrequested addition | 6 | D-02, D-05, D-06, D-13, D-20, D-22 |
| **Total** | **28** | Plus T-1–T-7 in the spec-defect subsection: T-1–T-3 are contract/SPEC-only, T-4–T-6 repeat D-04, D-16 and D-23, and T-7 was found by the auditor |

## Reconciliation (main session, 2026-11-03)

Each row was reviewed. What was done, by row (the raw code stays on `ch9-raw-generation`):

| Row | Resolution taken |
|---|---|
| D-02 | **Fixed code.** List markers are kept: each line's text is sent as typed, trimmed only (SR 1.2.3). Regression test `test_D_02_stated_text_kept_as_typed`. Innoslate item 4. |
| D-07 | **Fixed code.** The `# STUB` marker is replaced by a plain comment; the F.8 adapter is real. |
| D-14 | **Fixed code.** A non-string operator, proxy_strength or category is a bad response (retry, then interpretation_failed), not a TypeError. Regression tests `test_D_14_*`. |
| D-15 | **Fixed code.** A non-string metric, operator or designation raises ValueError (contract 422). Regression tests `test_D_15_*`. |
| D-17 | **Fixed contract, then code.** validateProposedCriteria and presentCriteriaMapping declare 422 / ValueError (A32); the presenter raises ValueError for an entry without requirement_id. Regression test `test_D_17_*`. |
| D-19 | **Fixed code.** The three wrong comments now describe the code. |
| D-05, D-25 | **Kept, ADR-0006.** `send_interpretation_request` stays the single runtime call site; the re-send is in the F.1.1 composition `propose_mapping`. Innoslate items 5, 7. |
| D-09, D-10, D-11 | **Contained, contract unchanged.** `propose_mapping` validates each response against its own request (one-element set) and always finishes the retry, so no count is left behind and no response is charged to another requirement. The validator's module-level count is still there for direct callers; changing its inputs needs a contract change (Innoslate item 8). |
| D-20 | **Kept.** The extra public helpers are used by C.1.1.4 (`OPERATORS`, `resolve_known_metrics`, `threshold_fits`); the dependency C.1.1.4 → C.1.1.2 follows the shared known-metrics control (SPEC 7). |
| D-21 | **Fixed contract wording** (x-configured-value says figure fields). `aa_omniscience_index` stays on the list until SPEC 5 Q12 is decided (Innoslate item 15). |
| T-1, T-2 | **Fixed contract.** ProposedCriteria schema added; a null threshold is valid on the number branch. |
| T-3 | **SPEC 7 note added** (`mapping_review:<scenario_id>`). The 16 demonstration tests stay red until a team member logs the walkthroughs. |
| T-7 | **Fixed contract** (A28 says which order each def returns). |
| D-01, D-03, D-04, D-06, D-08, D-12, D-13, D-16, D-18, D-22, D-23, D-24 | **Kept as generated, promoted.** Each is on the Innoslate list (items 1–3, 6, 9–14, 16–18). D-23: a hard-only mapping (SCENARIO_04) still can't produce a record under A27; team decision. |

After the reconcile: the CR tests give 103 passed, 16 failed (the walkthrough demonstrations only);
the 11 regression tests pass (and fail on the raw commit); the existing suite is unchanged against
the baseline; `check_conformance.py` and `generate_stubs.py --check` pass.

### Found by the independent verifier (2026-11-03)

The verifier spot-checked 14 rows against `3be0122` (all accurate) and confirmed the raw → current
diff is exactly D-02, D-07, D-14, D-15, D-17, D-19. It found three differences the audit missed,
added above as D-26–D-28 (Innoslate items 20–22). It also noted that the D-09 containment holds
only for one request at a time: the dev server now runs with `threaded=False` (app.py), and the
proper fix stays the contract change in Innoslate item 8. On the raw branch the CR tests were
committed (7d2c088) after the generation commit (3be0122); that they were written first is shown
by the unchanged hash and the order of work in prompts/2026-11-03-criteria-mapper-component.md,
not by git.
