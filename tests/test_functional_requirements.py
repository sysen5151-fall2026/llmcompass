"""Component tests for C.1.1 Criteria Mapper (F.1.1 Propose Criteria Mapping), Lab Manual 9.4.

Written from the specification only, before the code: SPEC.md section 7 (component
requirements CR 1.1.1-CR 2.4.1, Form report Tables 3, 9, 10), section 3 (model contract and
adapter), section 2 (data contract), section 4 (walkthrough log) and contracts/api-v1.yaml
v1.1.0 (requestInterpretation, validateProposedCriteria, presentCriteriaMapping,
distributeConfirmedMapping; A28-A31). No module body was read.

One test (or parametrized test) per CR, named test_CR_<id>_<what it checks>. Each def is
imported from its own module in the propose_criteria_mapping package, so a test fails with
"not implemented: <module>.<def>" until that component exists.

Verification methods (SPEC 7 Table 10):
- T: real assertions against the defs. Integration CRs feed distribute_confirmed_mapping's
  outputs into the real downstream defs named by the contract's x-module.
- I (CR 1.2.1, 2.2.1, 2.4.1): configuration, exported-record and source-text checks.
- D (CR 1.2.4, 1.3.6, 1.4.3, 2.1.1): checked from docs/validation/walkthroughs.csv
  (date,operator,scenario,minutes; SPEC 4). SPEC names no label for a mapping-review
  walkthrough, so this file uses MAPPING_REVIEW below, one row label per sample scenario:
  "mapping_review:<scenario_id>". These stay red until a person logs the walkthroughs.

Nothing here needs LM Studio or the network: runtime responses are built by hand in the
SPEC 3 shape. Requirement sets built by hand use a fresh identifier per test, so a
validator that counts retries per requirement (A31) never sees another test's attempts.
"""

import copy
import csv
import importlib
import inspect
import json
import re
import socket
import urllib.parse
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = ROOT / "sample_data"
CONTRACT = ROOT / "contracts" / "api-v1.yaml"
WALKTHROUGHS = ROOT / "docs" / "validation" / "walkthroughs.csv"

F1 = "provide_llm_selection_decision_support"
PKG = f"{F1}.propose_criteria_mapping"
F8 = "provide_requirement_interpretation"
COMPONENT_MODULES = (
    "request_interpretation",        # C.1.1.1 Interpretation Client
    "validate_proposed_criteria",    # C.1.1.2 Criteria Validator
    "present_criteria_mapping",      # C.1.1.3 Mapping Presenter
    "distribute_confirmed_mapping",  # C.1.1.4 Mapping Distributor
)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}  # SPEC 3 Adapter: the only hosts allowed

# Walkthrough label for CR 1.2.4, 1.3.6, 1.4.3, 2.1.1. SPEC 4 defines only `rerun` and
# `full_comparison`; SPEC 7 names no label for reviewing and confirming the mapping, so this
# one is chosen here (not a SPEC value). Each sample scenario is logged as
# "mapping_review:<scenario_id>" because "each scenario" needs the scenario in the row and the
# CSV has no other column for it.
MAPPING_REVIEW = "mapping_review"
MAPPING_REVIEW_MAX_MINUTES = 10  # CR 2.1.1 target

# SPEC 2 candidate fields that hold a figure (the metrics SPEC 3 lets a criterion name).
SPEC2_FIGURE_FIELDS = (
    "input_price", "output_price", "context_window", "latency_p50",
    "data_residency", "data_retention", "deprecation_date",
)
SPEC2_UNITS = {
    "input_price": "USD per 1M input tokens",
    "output_price": "USD per 1M output tokens",
    "context_window": "tokens",
    "latency_p50": "seconds",
    "data_residency": "ISO 3166-1 alpha-2",
    "data_retention": "days",
    "deprecation_date": "date",
}


def _load(name):
    with (SAMPLE_DATA / name).open() as f:
        return json.load(f)


BENCHMARKS = _load("benchmark_map.json")["benchmarks"]
BENCHMARK_IDS = tuple(BENCHMARKS)
# The configured known metrics list: SPEC 2 field names plus every known benchmark_id
# (contract KnownMetricsList x-configured-value; SPEC 5 Q7).
KNOWN_METRICS = frozenset(SPEC2_FIGURE_FIELDS + BENCHMARK_IDS)

USER_INPUTS = {s["scenario_id"]: s["user_input"] for s in _load("user_inputs.json")}
SCENARIO_CRITERIA = _load("scenario_criteria.json")
SCENARIOS = sorted(USER_INPUTS)

OPERATORS = {">=", "<=", "==", "in"}
STRENGTHS = {"strong", "moderate", "weak"}
CATEGORIES = {"capability", "cost", "compliance", "other"}
STATUSES = {"proposed", "retry", "interpretation_failed"}
SPEC3_CRITERION_FIELDS = ("criterion_id", "metric", "operator", "threshold", "unit",
                          "proxy_strength", "category", "rationale")

STATED_TEXT = ("Summarize technical documents of around twenty pages accurately, stay within "
               "five dollars per million input tokens, and process data only in the United States.")


# Import helpers ----------------------------------------------------------------

def _import_or_fail(module_name, attr):
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        pytest.fail(f"not implemented: {module_name}.{attr}")
    fn = getattr(module, attr, None)
    if fn is None:
        pytest.fail(f"not implemented: {module_name}.{attr}")
    return fn


def component(module, attr):
    """A C.1.1.x def from its own module in the propose_criteria_mapping package."""
    return _import_or_fail(f"{PKG}.{module}", attr)


def component_source(module):
    """Source text of a C.1.1.x module (inspection only, CR 2.4.1)."""
    component(module, module)
    return Path(inspect.getsourcefile(importlib.import_module(f"{PKG}.{module}"))).read_text()


def downstream(module, attr):
    """A first-level F.1.x def, by the contract's x-module."""
    return _import_or_fail(f"{F1}.{module}", attr)


def interpret(text):
    # requestInterpretation: (stated_requirements) -> (interpretation_requests, requirement_set)
    return component("request_interpretation", "request_interpretation")(text)


def validate(response, requirement_set, known_metrics=None):
    # validateProposedCriteria: (proposed_criteria, requirement_set, *, known_metrics) -> validated_criteria
    fn = component("validate_proposed_criteria", "validate_proposed_criteria")
    return fn(response, requirement_set, known_metrics=known_metrics)


def present(validated_criteria):
    # presentCriteriaMapping: (validated_criteria) -> presented_mapping
    return component("present_criteria_mapping", "present_criteria_mapping")(validated_criteria)


def distribute(mapping, requirement_set, known_metrics=None):
    # distributeConfirmedMapping: (confirmed_criteria_mapping, requirement_set, *, known_metrics)
    #   -> (required_metrics, hard_constraints, weighted_criteria, decision_basis)
    fn = component("distribute_confirmed_mapping", "distribute_confirmed_mapping")
    return fn(mapping, requirement_set, known_metrics=known_metrics)


# SPEC 3 builders -----------------------------------------------------------------

def proposed(criterion_id, metric, operator, threshold, unit, strength, category):
    """One SPEC 3 proposed criterion."""
    return {
        "criterion_id": criterion_id,
        "metric": metric,
        "operator": operator,
        "threshold": threshold,
        "unit": unit,
        "proxy_strength": strength,
        "category": category,
        "rationale": f"{metric} stands in for the stated requirement.",
    }


def response(requirement_id, criteria, no_suitable_proxy=False):
    """One SPEC 3 response."""
    return {"requirement_id": requirement_id, "no_suitable_proxy": no_suitable_proxy,
            "criteria": criteria}


def fresh_set(*texts):
    """A RequirementSet (flow 1.0.1) in the contract shape, with identifiers no other test uses."""
    texts = texts or ("Respond within a few seconds.",)
    return [{"requirement_id": f"CR-TEST-{uuid.uuid4().hex[:12]}", "text": t} for t in texts]


def valid_criterion():
    return proposed("ctx", "context_window", ">=", 100_000, "tokens", "strong", "capability")


def spec3_fields(criterion):
    """The SPEC 3 part of a criterion (C.1.1.2 may add requirement_id; ProposedCriterion)."""
    return {k: criterion[k] for k in SPEC3_CRITERION_FIELDS}


def scenario_proposal(scenario_id):
    """A sample scenario's criteria as a SPEC 3 proposal (no designation or weight yet)."""
    return [{**{k: v for k, v in c.items() if k not in ("designation", "weight")},
             "proxy_strength": "moderate", "rationale": "sample scenario"}
            for c in SCENARIO_CRITERIA[scenario_id]]


def scenario_mapping(scenario_id, requirement_set):
    """A sample scenario's confirmed criteria mapping (flow 5), tied to its first requirement."""
    rid = requirement_set[0]["requirement_id"]
    return [{"proxy_strength": "moderate", "rationale": "sample scenario", **c, "requirement_id": rid}
            for c in SCENARIO_CRITERIA[scenario_id]]


def integration_setup():
    """Stated requirements and a confirmed mapping with two weighted and two hard criteria.

    The two hard criteria share input_price with a weighted one, so required metrics must
    list it once (contract RequiredMetrics uniqueItems; A25).
    """
    _, requirement_set = interpret(STATED_TEXT)
    rid = requirement_set[0]["requirement_id"]
    mapping = [
        {**proposed("ctx", "context_window", ">=", 100_000, "tokens", "strong", "capability"),
         "requirement_id": rid, "designation": "weighted", "weight": 0.52},
        {**proposed("price", "input_price", "<=", 5.0, "USD per 1M input tokens", "moderate", "cost"),
         "requirement_id": rid, "designation": "weighted", "weight": 0.48},
        {**proposed("residency", "data_residency", "in", ["US"], "ISO 3166-1 alpha-2", "strong", "compliance"),
         "requirement_id": rid, "designation": "hard"},
        {**proposed("price_cap", "input_price", "<=", 10.0, "USD per 1M input tokens", "weak", "cost"),
         "requirement_id": rid, "designation": "hard"},
    ]
    return requirement_set, mapping


INTEGRATION_REQUIRED_METRICS = ["context_window", "input_price", "data_residency"]
INTEGRATION_ELIGIBLE = {"model-1", "model-2", "model-3"}


def weights_of(mapping):
    return {c["criterion_id"]: c["weight"] for c in mapping if c["designation"] == "weighted"}


def unique_metrics(mapping):
    seen = []
    for c in mapping:
        if c["metric"] not in seen:
            seen.append(c["metric"])
    return seen


def requirement_texts(requirements):
    """Texts of StatedRequirement items (plain text or {requirement_id, text}; A19)."""
    return [r if isinstance(r, str) else r["text"] for r in requirements]


# SPEC 2 candidates for the downstream chain -----------------------------------------

def figure(value, unit, days_old=10):
    return {"value": value, "unit": unit, "source_id": "https://example.com/source",
            "collection_date": (date.today() - timedelta(days=days_old)).isoformat()}


def candidate(model_id, context, price, residency):
    return {
        "model_id": model_id,
        "vendor": f"vendor-{model_id}",
        "model_name": model_id,
        "input_price": figure(price, SPEC2_UNITS["input_price"]),
        "output_price": figure(price * 4, SPEC2_UNITS["output_price"]),
        "context_window": figure(context, SPEC2_UNITS["context_window"]),
        "data_residency": figure(list(residency), SPEC2_UNITS["data_residency"]),
    }


def integration_candidates():
    # model-x is best on both weighted criteria but fails the hard residency constraint.
    return [
        candidate("model-1", 200_000, 3.0, ["US"]),
        candidate("model-2", 100_000, 1.0, ["US"]),
        candidate("model-3", 150_000, 3.0, ["US"]),
        candidate("model-x", 1_000_000, 0.1, ["DE"]),
    ]


def scenario_candidates(metrics):
    """Three candidates with a sourced, dated figure for every metric in `metrics`."""
    residencies = (["DE"], ["FR"], ["US"])
    out = []
    for i, model_id in enumerate(("model-s1", "model-s2", "model-s3")):
        cand = {"model_id": model_id, "vendor": f"vendor-{model_id}", "model_name": model_id,
                "benchmarks": []}
        for metric in metrics:
            if metric == "data_residency":
                value = residencies[i]
            elif metric == "deprecation_date":
                value = (date.today() + timedelta(days=365 * (i + 1))).isoformat()
            else:
                value = float(10 * (i + 1) + i * i)
            if metric in SPEC2_FIGURE_FIELDS:
                cand[metric] = figure(value, SPEC2_UNITS[metric])
            else:
                cand["benchmarks"].append({"benchmark_id": metric,
                                           "score": figure(value, BENCHMARKS[metric]["unit"])})
        out.append(cand)
    return out


def run_downstream(required_metrics, hard_constraints, weighted_criteria, decision_basis, candidates):
    """Feed the four outflows into F.1.2-F.1.7 (contract x-flows 5.1-5.4)."""
    request_model_data = downstream("retrieve_model_data", "request_model_data")
    receive_model_data = downstream("retrieve_model_data", "receive_model_data")
    apply_hard_constraints = downstream("apply_hard_constraints", "apply_hard_constraints")
    score_and_rank = downstream("score_and_rank_candidates", "score_and_rank_candidates")
    analyze = downstream("analyze_ranking_sensitivity", "analyze_ranking_sensitivity")
    report = downstream("report_selection_rationale", "report_selection_rationale")
    generate = downstream("generate_and_store_decision_record", "generate_and_store_decision_record")

    data_request = request_model_data(required_metrics)                       # 5.1 -> F.1.2
    evidence = receive_model_data(copy.deepcopy(candidates))
    eligible, exclusions = apply_hard_constraints(evidence, hard_constraints=hard_constraints)  # 5.2 -> F.1.3
    ranking = score_and_rank(eligible, weighted_criteria=weighted_criteria)    # 5.3 -> F.1.4
    finding = analyze(ranking, weighted_criteria=weighted_criteria)           # 5.3 -> F.1.5
    _, rationale = report(ranking, exclusions, finding)
    selection = ranking[0]["model_id"] if ranking else None
    record = generate(rationale, selection, decision_basis)                   # 5.4 -> F.1.7
    return {"data_request": data_request, "evidence": evidence, "eligible": eligible,
            "exclusions": exclusions, "ranking": ranking, "finding": finding, "record": record}


def brute_force_unstable_pairs(ranking, criterion_ids, factors=(0.9, 1.1)):
    """Pairs that flip when one weight is scaled by a factor (A7, A8, A10: contributions are linear)."""
    order = [e["model_id"] for e in ranking]
    pairs = set()
    for cid in criterion_ids:
        for factor in factors:
            score = {e["model_id"]: e["score"] - e["contributions"][cid] + e["contributions"][cid] * factor
                     for e in ranking}
            for i, higher in enumerate(order):
                for lower in order[i + 1:]:
                    if score[lower] > score[higher]:
                        pairs.add((higher, lower))
    return pairs


# Contract conformance -------------------------------------------------------------

def _nonempty_str(x):
    return isinstance(x, str) and x != ""


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check_proposed(c):
    assert isinstance(c, dict), c
    missing = [k for k in SPEC3_CRITERION_FIELDS if k not in c]
    assert not missing, f"criterion missing {missing}: {c}"
    assert _nonempty_str(c["criterion_id"]), c
    assert isinstance(c["metric"], str), c
    assert c["operator"] in OPERATORS, c
    assert c["threshold"] is None or _is_number(c["threshold"]) or isinstance(c["threshold"], (str, list)), c
    assert isinstance(c["unit"], str), c
    assert c["proxy_strength"] in STRENGTHS, c
    assert c["category"] in CATEGORIES, c
    assert isinstance(c["rationale"], str), c


def _check_confirmed(c, designation=None):
    assert isinstance(c, dict), c
    for k in ("criterion_id", "metric", "operator", "designation"):
        assert k in c, f"criterion missing {k}: {c}"
    assert c["operator"] in OPERATORS, c
    assert c["designation"] in {"hard", "weighted"}, c
    if designation:
        assert c["designation"] == designation, c
    if c["designation"] == "weighted":
        assert _is_number(c.get("weight")) and c["weight"] >= 0, c


def _check_request(x):
    assert isinstance(x, dict), x
    assert _nonempty_str(x.get("requirement_id")) and _nonempty_str(x.get("text")), x


def _check_validated(x):
    assert isinstance(x, dict), x
    for k in ("requirement_id", "requirement", "status", "no_suitable_proxy", "criteria"):
        assert k in x, f"validated criteria missing {k}: {x}"
    assert _nonempty_str(x["requirement_id"]), x
    assert isinstance(x["requirement"], str), x
    assert x["status"] in STATUSES, x
    assert isinstance(x["no_suitable_proxy"], bool), x
    assert isinstance(x["criteria"], list), x
    for c in x["criteria"]:
        _check_proposed(c)


def _structural(x, name):
    """Stdlib checks of the contract shapes, run whether or not the schema validator is installed."""
    if name == "InterpretationRequest":
        _check_request(x)
    elif name == "RequirementSet":
        assert isinstance(x, list) and x, x
        for item in x:
            _check_request(item)
    elif name == "ProposedCriterion":
        _check_proposed(x)
    elif name == "SPEC3Response":
        assert isinstance(x, dict), x
        assert _nonempty_str(x.get("requirement_id")), x
        assert isinstance(x.get("no_suitable_proxy"), bool), x
        assert isinstance(x.get("criteria"), list), x
        for c in x["criteria"]:
            _check_proposed(c)
    elif name == "ValidatedCriteria":
        _check_validated(x)
    elif name == "PresentedMapping":
        assert isinstance(x, dict) and isinstance(x.get("requirements"), list) and x["requirements"], x
        for entry in x["requirements"]:
            _check_validated(entry)
    elif name == "RequiredMetrics":
        assert isinstance(x, list) and all(isinstance(m, str) for m in x), x
        assert len(x) == len(set(x)), f"metrics listed more than once: {x}"
    elif name == "HardConstraints":
        assert isinstance(x, list), x
        for c in x:
            _check_confirmed(c, "hard")
    elif name == "WeightedCriteria":
        assert isinstance(x, list), x
        for c in x:
            _check_confirmed(c, "weighted")
    elif name == "DecisionBasis":
        assert isinstance(x, dict), x
        for k in ("requirements", "criteria_mapping", "weights"):
            assert k in x, f"decision basis missing {k}: {x}"
        assert isinstance(x["requirements"], list) and x["requirements"], x
        for r in x["requirements"]:
            assert _nonempty_str(r) or (isinstance(r, dict) and _nonempty_str(r.get("text"))), r
        assert isinstance(x["criteria_mapping"], list), x
        for c in x["criteria_mapping"]:
            _check_confirmed(c)
        assert isinstance(x["weights"], dict), x
        assert all(isinstance(k, str) and _is_number(v) and v >= 0 for k, v in x["weights"].items()), x
    else:
        raise KeyError(name)


_SCHEMAS = {}


def _contract_schemas():
    """components.schemas of contracts/api-v1.yaml, or None without yaml/openapi_schema_validator."""
    if "schemas" not in _SCHEMAS:
        try:
            import yaml  # noqa: F401
            import openapi_schema_validator  # noqa: F401
        except ImportError:
            _SCHEMAS["schemas"] = None
        else:
            with CONTRACT.open() as f:
                _SCHEMAS["schemas"] = yaml.safe_load(f)["components"]["schemas"]
    return _SCHEMAS["schemas"]


def _deref(node, schemas):
    """Inline $refs and drop x- keys. OAS 3.0 `nullable` beside a typeless oneOf doesn't admit
    null in OAS30Validator, but SPEC 3 allows a null threshold, so null is added as a branch."""
    if isinstance(node, dict):
        if "$ref" in node:
            return _deref(schemas[node["$ref"].rsplit("/", 1)[1]], schemas)
        out = {k: _deref(v, schemas) for k, v in node.items() if not k.startswith("x-")}
        if out.get("nullable") and "oneOf" in out and "type" not in out:
            out["oneOf"] = out["oneOf"] + [{"enum": [None]}]
        return out
    if isinstance(node, list):
        return [_deref(v, schemas) for v in node]
    return node


def assert_conforms(instance, name):
    """Check `instance` against a contract schema (or the SPEC 3 response, name SPEC3Response)."""
    _structural(instance, name)
    schemas = _contract_schemas()
    if schemas is None:
        return
    from openapi_schema_validator import OAS30Validator
    if name == "SPEC3Response":
        schema = {"type": "object", "required": ["requirement_id", "no_suitable_proxy", "criteria"],
                  "properties": {"requirement_id": {"type": "string", "minLength": 1},
                                 "no_suitable_proxy": {"type": "boolean"},
                                 "criteria": {"type": "array", "items": schemas["ProposedCriterion"]}}}
    else:
        schema = schemas[name]
    errors = [e.message for e in OAS30Validator(_deref(schema, schemas)).iter_errors(instance)]
    assert not errors, f"{name}: {errors}"


def assert_spec3_valid(criteria, known_metrics):
    """SPEC 3 'Valid only if' rules on criteria that were accepted."""
    for c in criteria:
        assert c["metric"] in known_metrics, c
        op, t = c["operator"], c["threshold"]
        if op == "in":
            assert isinstance(t, list), c
        elif op in (">=", "<="):
            assert t is None or _is_number(t), c
        else:
            assert t is None or _is_number(t) or isinstance(t, str), c
        assert c["proxy_strength"] in STRENGTHS, c


# Walkthroughs (SPEC 4) --------------------------------------------------------------

def walkthrough_minutes(label):
    if not WALKTHROUGHS.exists():
        pytest.fail(f"no timed walkthroughs logged yet: {WALKTHROUGHS}")
    with WALKTHROUGHS.open() as f:
        rows = [r for r in csv.DictReader(f) if (r.get("scenario") or "").strip() == label]
    if not rows:
        pytest.fail(f"no '{label}' walkthrough logged in {WALKTHROUGHS.name}")
    for r in rows:
        date.fromisoformat(r["date"].strip())
        assert (r.get("operator") or "").strip(), r
    return [float(r["minutes"]) for r in rows]


def mapping_review_minutes(scenario_id):
    return walkthrough_minutes(f"{MAPPING_REVIEW}:{scenario_id}")


def block_network(monkeypatch):
    """Fail any outbound connection except to the local host; return the attempts."""
    attempts = []
    real_connect = socket.socket.connect
    real_getaddrinfo = socket.getaddrinfo

    def guarded(sock, address):
        host = address[0] if isinstance(address, tuple) else address
        if host in LOCAL_HOSTS:
            return real_connect(sock, address)
        attempts.append(address)
        raise OSError(f"network blocked in tests: {address}")

    def no_dns(host, *args, **kwargs):
        if host in LOCAL_HOSTS:
            return real_getaddrinfo(host, *args, **kwargs)
        attempts.append((host,) + tuple(args[:1]))
        raise socket.gaierror(f"network blocked in tests: {host}")

    monkeypatch.setattr(socket.socket, "connect", guarded)
    monkeypatch.setattr(socket, "getaddrinfo", no_dns)
    return attempts


# CR 1.1 Inputs --------------------------------------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_1_1_confirmed_mapping_of_each_scenario_accepted_and_passed_on(scenario_id):
    # CR 1.1.1 Accept Confirmed criteria mapping (traces to SR 1.1.1). MOP: confirmed mappings
    # received and passed on, 100%. T: confirm the mapping in each sample scenario.
    _, requirement_set = interpret(USER_INPUTS[scenario_id])
    mapping = scenario_mapping(scenario_id, requirement_set)
    required, hard, weighted, basis = distribute(copy.deepcopy(mapping), requirement_set,
                                                 known_metrics=KNOWN_METRICS)
    for c in mapping:
        receiver = hard if c["designation"] == "hard" else weighted
        assert c["criterion_id"] in [r["criterion_id"] for r in receiver], c
    assert sorted(r["criterion_id"] for r in hard + weighted) == sorted(c["criterion_id"] for c in mapping)
    assert basis["criteria_mapping"] == mapping


@pytest.mark.parametrize("case", ["weighted_without_weight", "non_numeric_weight",
                                  "no_designation", "unknown_designation"])
def test_CR_1_1_1_criterion_without_valid_designation_or_weight_rejected(case):
    # CR 1.1.1 (SR 1.1.1: "A weighted criterion without a weight is rejected."); contract
    # distributeConfirmedMapping 422 -> ValueError.
    requirement_set = fresh_set()
    c = {**valid_criterion(), "requirement_id": requirement_set[0]["requirement_id"],
         "designation": "weighted", "weight": 1.0}
    if case == "weighted_without_weight":
        del c["weight"]
    elif case == "non_numeric_weight":
        c["weight"] = "high"
    elif case == "no_designation":
        del c["designation"]
    else:
        c["designation"] = "preferred"
    with pytest.raises(ValueError):
        distribute([c], requirement_set, known_metrics=KNOWN_METRICS)


def test_CR_1_1_2_changing_known_metrics_list_changes_validation_results():
    # CR 1.1.2 Accept Known metrics list (traces to SR 1.1.8). MOP: validation runs that use
    # the current list, 100%. T: change the list and check validation results.
    with_ctx = KNOWN_METRICS
    without_ctx = KNOWN_METRICS - {"context_window"}
    custom = "custom_metric_cr_1_1_2"
    with_custom = KNOWN_METRICS | {custom}

    def status(criterion, known):
        rs = fresh_set()
        return validate(response(rs[0]["requirement_id"], [criterion]), rs, known_metrics=known)["status"]

    ctx = valid_criterion()
    extra = proposed("custom", custom, ">=", 1, "unit", "weak", "other")
    assert status(ctx, with_ctx) == "proposed"
    assert status(ctx, without_ctx) != "proposed"
    assert status(extra, with_custom) == "proposed"
    assert status(extra, KNOWN_METRICS) != "proposed"

    # The same list controls distribution of the confirmed mapping.
    rs = fresh_set()
    mapping = [{**ctx, "requirement_id": rs[0]["requirement_id"], "designation": "weighted", "weight": 1.0}]
    required, _, _, _ = distribute(copy.deepcopy(mapping), rs, known_metrics=with_ctx)
    assert required == ["context_window"]
    with pytest.raises(ValueError):
        distribute(copy.deepcopy(mapping), rs, known_metrics=without_ctx)


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_1_3_runtime_proposal_accepted_for_each_scenario(scenario_id):
    # CR 1.1.3 Accept Proposed criteria (traces to SR 1.1.4). MOP: runtime responses received,
    # 100%. T: interpretation per sample scenario (responses built here in the SPEC 3 shape).
    requests, requirement_set = interpret(USER_INPUTS[scenario_id])
    proposal = scenario_proposal(scenario_id)
    for req in requests:
        result = validate(response(req["requirement_id"], copy.deepcopy(proposal)), requirement_set,
                          known_metrics=KNOWN_METRICS)
        assert result["status"] == "proposed", result
        assert result["requirement_id"] == req["requirement_id"]
        assert result["no_suitable_proxy"] is False
        assert [spec3_fields(c) for c in result["criteria"]] == proposal


def test_CR_1_1_3_no_suitable_proxy_response_accepted():
    # CR 1.1.3 / SPEC 3: "either criteria has 1+ entries, or no_suitable_proxy is true and
    # criteria is empty" -- an explicit no-proxy result is a valid response.
    rs = fresh_set("Be pleasant to work with.")
    result = validate(response(rs[0]["requirement_id"], [], no_suitable_proxy=True), rs,
                      known_metrics=KNOWN_METRICS)
    assert result["status"] == "proposed", result
    assert result["no_suitable_proxy"] is True
    assert result["criteria"] == []
    assert result["requirement_id"] == rs[0]["requirement_id"]


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_1_4_stated_requirements_of_each_scenario_accepted(scenario_id):
    # CR 1.1.4 Accept Stated requirements (traces to SR 1.1.5). MOP: stated requirements
    # accepted, 100%. T: enter the requirements of each sample scenario. How the text is split
    # into requirements is not fixed (A30): only that each comes from the input, with an ID.
    text = USER_INPUTS[scenario_id]
    _, requirement_set = interpret(text)
    assert_conforms(requirement_set, "RequirementSet")
    ids = [r["requirement_id"] for r in requirement_set]
    assert len(ids) == len(set(ids)), ids
    for r in requirement_set:
        assert r["text"] in text, r  # SR 1.1.5: without reformatting


@pytest.mark.parametrize("bad", ["", None, 42, ["Respond within a few seconds."]])
def test_CR_1_1_4_empty_or_non_text_requirements_rejected(bad):
    # CR 1.1.4 / SR 1.1.5 "Empty input is rejected"; contract requestInterpretation 422:
    # "not text, or are empty" -> ValueError.
    with pytest.raises(ValueError):
        interpret(bad)


# CR 1.2 Outputs -------------------------------------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_2_1_exported_record_holds_decision_basis_per_scenario(scenario_id):
    # CR 1.2.1 Provide Decision basis (traces to SR 1.4.1.1). MOP: decision records containing
    # the decision basis, 100%. I: exported record per scenario.
    _, requirement_set = interpret(USER_INPUTS[scenario_id])
    mapping = scenario_mapping(scenario_id, requirement_set)
    required, hard, weighted, basis = distribute(copy.deepcopy(mapping), requirement_set,
                                                 known_metrics=KNOWN_METRICS)
    assert_conforms(basis, "DecisionBasis")
    assert sorted(requirement_texts(basis["requirements"])) == sorted(r["text"] for r in requirement_set)
    assert basis["criteria_mapping"] == mapping
    assert basis["weights"] == weights_of(mapping)
    if not weighted:
        # SCENARIO_04 is hard-constraint only: its weights section is empty and F.1.7 refuses
        # an empty one (A27). Which record it produces is an open team item (PLAN 8.5), so only
        # the decision basis is inspected here.
        return
    out = run_downstream(required, hard, weighted, basis, scenario_candidates(required))
    retrieve = downstream("generate_and_store_decision_record", "retrieve_decision_record")
    for record in (out["record"], retrieve(out["record"]["record_id"])):
        assert record["requirements"] == basis["requirements"]
        assert record["criteria_mapping"] == mapping
        assert record["weights"] == basis["weights"]


def test_CR_1_2_2_hard_constraints_delivered_to_constraint_filter():
    # CR 1.2.2 Provide Hard constraints (traces to SR 1.4.1.1). MOP: confirmed hard constraints
    # delivered, 100%. T: integration test with the Constraint Filter (F.1.3).
    requirement_set, mapping = integration_setup()
    _, hard, _, _ = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    assert hard == [c for c in mapping if c["designation"] == "hard"]
    receive = downstream("retrieve_model_data", "receive_model_data")
    apply_hard_constraints = downstream("apply_hard_constraints", "apply_hard_constraints")
    eligible, exclusions = apply_hard_constraints(receive(integration_candidates()), hard_constraints=hard)
    assert {c["model_id"] for c in eligible} == INTEGRATION_ELIGIBLE
    assert [e["model_id"] for e in exclusions] == ["model-x"]
    assert "residency" in exclusions[0]["failed_constraints"]


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_2_3_one_request_per_stated_requirement_with_id_and_text(scenario_id):
    # CR 1.2.3 Provide Interpretation request (traces to SR 1.2.3: "Exactly one interpretation
    # request is issued for each stated requirement, carrying its ID and unaltered text").
    # MOP: stated requirements sent for interpretation, 100%. T: request log per scenario.
    text = USER_INPUTS[scenario_id]
    requests, requirement_set = interpret(text)
    by_id = {r["requirement_id"]: r["text"] for r in requirement_set}
    assert len(requests) == len(requirement_set) >= 1
    assert sorted(req["requirement_id"] for req in requests) == sorted(by_id)
    for req in requests:
        assert req["text"] == by_id[req["requirement_id"]]
        assert req["text"] in text


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_2_4_presented_mapping_walkthrough_logged_per_scenario(scenario_id):
    # CR 1.2.4 Provide Presented mapping (traces to SR 1.2.4). MOP: stated requirements shown
    # with their proposed criteria, 100%. D: walkthrough of each scenario (walkthroughs.csv).
    assert mapping_review_minutes(scenario_id)


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_2_4_presented_mapping_shows_each_stated_requirement_with_its_criteria(scenario_id):
    # CR 1.2.4, T-style supplement: every stated requirement is shown with its proposed
    # criteria (contract PresentedMapping).
    requests, requirement_set = interpret(USER_INPUTS[scenario_id])
    proposal = scenario_proposal(scenario_id)
    validated = [validate(response(req["requirement_id"], copy.deepcopy(proposal)), requirement_set,
                          known_metrics=KNOWN_METRICS) for req in requests]
    presented = present(validated)
    assert_conforms(presented, "PresentedMapping")
    shown = presented["requirements"]
    assert sorted(e["requirement_id"] for e in shown) == sorted(r["requirement_id"] for r in requirement_set)
    texts = {r["requirement_id"]: r["text"] for r in requirement_set}
    for entry in shown:
        assert entry["requirement"] == texts[entry["requirement_id"]]
        assert [spec3_fields(c) for c in entry["criteria"]] == proposal
        assert all(c["proxy_strength"] in STRENGTHS for c in entry["criteria"])


def test_CR_1_2_5_required_metrics_delivered_to_evidence_retriever():
    # CR 1.2.5 Provide Required metrics (traces to SR 1.4.1.1). MOP: confirmed criteria with a
    # required metric delivered, 100%. T: integration test with the Evidence Retriever (F.1.2).
    requirement_set, mapping = integration_setup()
    required, _, _, _ = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    assert required == INTEGRATION_REQUIRED_METRICS  # each once, in order of first appearance (A25)
    assert set(required) == {c["metric"] for c in mapping}
    data_request = downstream("retrieve_model_data", "request_model_data")(required)
    assert set(data_request["metrics"]) == set(required)


def test_CR_1_2_6_ranking_engine_and_sensitivity_analyzer_receive_identical_weights():
    # CR 1.2.6 Provide Weighted criteria (traces to SR 1.4.1.1). MOP: receivers given identical
    # weights, 2 of 2. T: integration test with both receivers (F.1.4, F.1.5).
    requirement_set, mapping = integration_setup()
    _, hard, weighted, _ = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    confirmed_weights = weights_of(mapping)
    assert weights_of(weighted) == confirmed_weights

    receive = downstream("retrieve_model_data", "receive_model_data")
    apply_hard_constraints = downstream("apply_hard_constraints", "apply_hard_constraints")
    score_and_rank = downstream("score_and_rank_candidates", "score_and_rank_candidates")
    analyze = downstream("analyze_ranking_sensitivity", "analyze_ranking_sensitivity")
    eligible, _ = apply_hard_constraints(receive(integration_candidates()), hard_constraints=hard)

    received = []
    received.append(weights_of(copy.deepcopy(weighted)))   # what the Ranking Engine is given
    ranking = score_and_rank(eligible, weighted_criteria=weighted)
    received.append(weights_of(copy.deepcopy(weighted)))   # what the Sensitivity Analyzer is given
    finding = analyze(ranking, weighted_criteria=weighted)
    assert received == [confirmed_weights, confirmed_weights], received  # 2 of 2 identical

    # The Ranking Engine uses them: one contribution per weighted criterion, and a contribution
    # scales with its weight (A10).
    for entry in ranking:
        assert set(entry["contributions"]) == set(confirmed_weights), entry
    doubled = copy.deepcopy(weighted)
    doubled[0]["weight"] *= 2
    cid = doubled[0]["criterion_id"]
    base = {e["model_id"]: e["contributions"][cid] for e in ranking}
    for entry in score_and_rank(eligible, weighted_criteria=doubled):
        assert entry["contributions"][cid] == pytest.approx(2 * base[entry["model_id"]])

    # The Sensitivity Analyzer uses the same weights as the ranking (A7-A10).
    found = {tuple(p) for p in finding["unstable_pairs"]}
    assert found == brute_force_unstable_pairs(ranking, confirmed_weights), finding


# CR 1.3 Interfaces ----------------------------------------------------------------

def test_CR_1_3_1_decision_basis_exchanged_with_decision_recorder():
    # CR 1.3.1 Criteria Mapper / Decision Recorder (traces to SR 1.4.1.1). MOP: exchanges in the
    # agreed format, 100%. T: integration test (contract flow 5.4 DecisionBasis -> F.1.7).
    requirement_set, mapping = integration_setup()
    outputs = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    basis = outputs[3]
    assert_conforms(basis, "DecisionBasis")
    record = run_downstream(*outputs, integration_candidates())["record"]
    assert record["requirements"] == basis["requirements"]
    assert record["criteria_mapping"] == basis["criteria_mapping"]
    assert record["weights"] == basis["weights"]
    retrieve = downstream("generate_and_store_decision_record", "retrieve_decision_record")
    assert retrieve(record["record_id"]) == record


def test_CR_1_3_2_weighted_criteria_exchanged_with_sensitivity_analyzer():
    # CR 1.3.2 Criteria Mapper / Sensitivity Analyzer (traces to SR 1.4.1.1). MOP: exchanges in
    # the agreed format, 100%. T: integration test (flow 5.3 WeightedCriteria -> F.1.5).
    requirement_set, mapping = integration_setup()
    outputs = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    assert_conforms(outputs[2], "WeightedCriteria")
    finding = run_downstream(*outputs, integration_candidates())["finding"]
    for k in ("method", "ranking_is_stable", "unstable_pairs"):
        assert k in finding, finding


def test_CR_1_3_3_weighted_criteria_exchanged_with_ranking_engine():
    # CR 1.3.3 Criteria Mapper / Ranking Engine (traces to SR 1.4.1.1). MOP: exchanges in the
    # agreed format, 100%. T: integration test (flow 5.3 WeightedCriteria -> F.1.4).
    requirement_set, mapping = integration_setup()
    outputs = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    weighted = outputs[2]
    assert_conforms(weighted, "WeightedCriteria")
    ranking = run_downstream(*outputs, integration_candidates())["ranking"]
    assert {e["model_id"] for e in ranking} == INTEGRATION_ELIGIBLE
    for entry in ranking:
        assert set(entry["contributions"]) == {c["criterion_id"] for c in weighted}, entry


def test_CR_1_3_4_hard_constraints_exchanged_with_constraint_filter():
    # CR 1.3.4 Criteria Mapper / Constraint Filter (traces to SR 1.4.1.1). MOP: exchanges in the
    # agreed format, 100%. T: integration test (flow 5.2 HardConstraints -> F.1.3).
    requirement_set, mapping = integration_setup()
    outputs = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    assert_conforms(outputs[1], "HardConstraints")
    out = run_downstream(*outputs, integration_candidates())
    eligible = [c["model_id"] for c in out["eligible"]]
    excluded = [e["model_id"] for e in out["exclusions"]]
    assert sorted(eligible + excluded) == sorted(c["model_id"] for c in integration_candidates())
    assert excluded == ["model-x"]


def test_CR_1_3_5_required_metrics_exchanged_with_evidence_retriever():
    # CR 1.3.5 Criteria Mapper / Evidence Retriever (traces to SR 1.4.1.1). MOP: exchanges in the
    # agreed format, 100%. T: integration test (flow 5.1 RequiredMetrics -> F.1.2).
    requirement_set, mapping = integration_setup()
    outputs = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    assert_conforms(outputs[0], "RequiredMetrics")
    data_request = run_downstream(*outputs, integration_candidates())["data_request"]
    assert set(data_request["metrics"]) == set(outputs[0])


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_3_6_technical_lead_walkthrough_logged_per_scenario(scenario_id):
    # CR 1.3.6 Criteria Mapper / Technical Lead (traces to SR 1.3.1). MOP: scenario steps with
    # the Technical Lead completed, 100%. D: walkthrough of each scenario (walkthroughs.csv).
    assert mapping_review_minutes(scenario_id)


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_3_7_runtime_exchanges_follow_model_contract(scenario_id):
    # CR 1.3.7 Criteria Mapper / Language model runtime (traces to SR 1.3.2). MOP: exchanges
    # that follow the model contract, 100%. T: contract validation.
    requests, requirement_set = interpret(USER_INPUTS[scenario_id])
    for req in requests:
        assert_conforms(req, "InterpretationRequest")
        reply = response(req["requirement_id"], scenario_proposal(scenario_id))
        assert_conforms(reply, "SPEC3Response")
        result = validate(reply, requirement_set, known_metrics=KNOWN_METRICS)
        assert result["status"] == "proposed", result
        assert_conforms(result, "ValidatedCriteria")
        for c in result["criteria"]:
            assert_conforms(c, "ProposedCriterion")
        assert_spec3_valid(result["criteria"], KNOWN_METRICS)


def test_CR_1_3_7_timeout_handled_as_invalid_response():
    # CR 1.3.7 / SR 1.3.2 "a timeout is handled the same way as an invalid response": the
    # adapter returns None (SPEC 3 Adapter); retry once, then interpretation_failed.
    rs = fresh_set()
    first = validate(None, rs, known_metrics=KNOWN_METRICS)
    second = validate(None, rs, known_metrics=KNOWN_METRICS)
    for result in (first, second):
        assert_conforms(result, "ValidatedCriteria")
        assert result["requirement_id"] == rs[0]["requirement_id"]
        assert result["criteria"] == []
    assert (first["status"], second["status"]) == ("retry", "interpretation_failed")


@pytest.mark.parametrize("metric", sorted(KNOWN_METRICS))
def test_CR_1_3_8_configured_known_metrics_list_loaded(metric):
    # CR 1.3.8 Criteria Mapper / Benchmark Data Sources (traces to SR 1.3.3). MOP: known metrics
    # list loaded, 100% of runs. T: load test. known_metrics=None means the configured list:
    # SPEC 2 field names plus every benchmark_id (contract KnownMetricsList).
    rs = fresh_set()
    rid = rs[0]["requirement_id"]
    criterion = proposed("m", metric, "==", None, "unit", "moderate", "other")
    assert validate(response(rid, [criterion]), rs)["status"] == "proposed"
    mapping = [{**criterion, "requirement_id": rid, "designation": "weighted", "weight": 1.0}]
    required, _, _, _ = distribute(mapping, rs)
    assert required == [metric]


def test_CR_1_3_8_metric_off_configured_list_rejected():
    # CR 1.3.8: the loaded list is the one applied -- a metric not on it is caught.
    rs = fresh_set()
    rid = rs[0]["requirement_id"]
    criterion = proposed("m", "not_a_known_metric_cr_1_3_8", ">=", 1, "unit", "moderate", "other")
    assert validate(response(rid, [criterion]), rs)["status"] != "proposed"
    with pytest.raises(ValueError):
        distribute([{**criterion, "requirement_id": rid, "designation": "weighted", "weight": 1.0}], rs)


# CR 1.4 Functions -----------------------------------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_4_1_every_stated_requirement_gets_an_interpretation_request(scenario_id):
    # CR 1.4.1 Request Interpretation (traces to SR 1.4.1.1). MOP: stated requirements with an
    # interpretation request, 100%. T: request log per scenario.
    text = USER_INPUTS[scenario_id]
    requests, requirement_set = interpret(text)
    assert requests, "no interpretation request"
    for req in requests:
        assert_conforms(req, "InterpretationRequest")
        assert req["text"] in text
    ids = [req["requirement_id"] for req in requests]
    assert len(ids) == len(set(ids)), ids
    assert {r["requirement_id"] for r in requirement_set} <= set(ids)


def _bad_responses():
    ctx = valid_criterion

    def with_(**changes):
        return lambda rid: response(rid, [{**ctx(), **changes}])

    def without(field):
        return lambda rid: response(rid, [{k: v for k, v in ctx().items() if k != field}])

    return {
        # unknown metric (SPEC 3: "every metric exists in section 2"; known metrics list)
        "unknown_metric": with_(metric="not_a_known_metric_cr_1_4_2"),
        "unknown_among_valid": lambda rid: response(
            rid, [ctx(), proposed("x", "not_a_known_metric_cr_1_4_2", ">=", 1, "unit", "weak", "other")]),
        # wrong requirement_id (SPEC 3; SPEC 7 C.1.1.2)
        "wrong_requirement_id": lambda rid: response(rid + "-other", [ctx()]),
        "missing_requirement_id": lambda rid: {"no_suitable_proxy": False, "criteria": [ctx()]},
        # bad operator / threshold that doesn't fit its operator (SPEC 3)
        "bad_operator": with_(operator="=>"),
        "in_without_list": with_(operator="in", threshold="US"),
        "ge_with_list": with_(operator=">=", threshold=[100_000]),
        "le_with_string": with_(operator="<=", threshold="5"),
        "eq_with_list": with_(operator="==", threshold=["a"]),
        # proxy strength (SPEC 3)
        "bad_proxy_strength": with_(proxy_strength="high"),
        "missing_proxy_strength": without("proxy_strength"),
        # never both / neither (SPEC 3)
        "both_criteria_and_no_proxy": lambda rid: response(rid, [ctx()], no_suitable_proxy=True),
        "neither_criteria_nor_no_proxy": lambda rid: response(rid, []),
        # malformed (wrong schema)
        "criteria_not_a_list": lambda rid: response(rid, "context_window"),
        "criterion_not_an_object": lambda rid: response(rid, ["context_window"]),
        "empty_object": lambda rid: {},
        # no response or not JSON: the adapter returns None (SPEC 3 Adapter)
        "no_response": lambda rid: None,
    }


BAD_RESPONSES = _bad_responses()


@pytest.mark.parametrize("case", sorted(BAD_RESPONSES))
def test_CR_1_4_2_invalid_and_unknown_criteria_caught(case):
    # CR 1.4.2 Validate Proposed Criteria (traces to SR 1.4.1.1). MOP: invalid or unknown
    # criteria caught, 100%. T: inject invalid and unknown criteria. SPEC 3 failure path: retry
    # once, then interpretation_failed; never drop the requirement or make up criteria.
    text = "Summarize technical documents of around twenty pages accurately."
    rs = fresh_set(text)
    rid = rs[0]["requirement_id"]
    bad = BAD_RESPONSES[case](rid)
    first = validate(copy.deepcopy(bad), rs, known_metrics=KNOWN_METRICS)
    second = validate(copy.deepcopy(bad), rs, known_metrics=KNOWN_METRICS)
    for result in (first, second):
        assert_conforms(result, "ValidatedCriteria")
        assert result["requirement_id"] == rid
        assert result["requirement"] == text
        assert result["criteria"] == [], result  # no made-up criteria
    assert first["status"] == "retry", first
    assert second["status"] == "interpretation_failed", second
    # Not dropped: the requirement is still presented, for the Technical Lead to fill in by hand.
    shown = present([second])["requirements"]
    assert [(e["requirement_id"], e["status"], e["criteria"]) for e in shown] == \
        [(rid, "interpretation_failed", [])]


def test_CR_1_4_2_valid_response_after_one_retry_accepted():
    # CR 1.4.2 / SPEC 3 "retry once": a valid second response is accepted.
    rs = fresh_set()
    rid = rs[0]["requirement_id"]
    assert validate(BAD_RESPONSES["unknown_metric"](rid), rs, known_metrics=KNOWN_METRICS)["status"] == "retry"
    result = validate(response(rid, [valid_criterion()]), rs, known_metrics=KNOWN_METRICS)
    assert result["status"] == "proposed", result
    assert [spec3_fields(c) for c in result["criteria"]] == [valid_criterion()]


def test_CR_1_4_2_retry_is_counted_per_requirement():
    # CR 1.4.2 / contract validateProposedCriteria: "status retry the first time for that
    # requirement and interpretation_failed the second".
    rs = fresh_set("Respond within a few seconds.", "Process data that may not leave the United States.")
    a, b = (r["requirement_id"] for r in rs)
    assert validate(BAD_RESPONSES["unknown_metric"](a), rs, known_metrics=KNOWN_METRICS)["status"] == "retry"
    result_b = validate(BAD_RESPONSES["unknown_metric"](b), rs, known_metrics=KNOWN_METRICS)
    assert (result_b["requirement_id"], result_b["status"]) == (b, "retry")
    result_a = validate(BAD_RESPONSES["unknown_metric"](a), rs, known_metrics=KNOWN_METRICS)
    assert (result_a["requirement_id"], result_a["status"]) == (a, "interpretation_failed")


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_1_4_3_mapping_presentation_walkthrough_logged_per_scenario(scenario_id):
    # CR 1.4.3 Present Criteria Mapping (traces to SR 1.4.1.1). MOP: proposed criteria shown
    # with their rating, 100%. D: walkthrough of each scenario (walkthroughs.csv).
    assert mapping_review_minutes(scenario_id)


def test_CR_1_4_3_every_presented_criterion_shows_its_rating_and_requirement():
    # CR 1.4.3, T-style supplement (SR 1.2.4: "Every presented criterion shows the requirement
    # it stands for and a rating of strong, moderate or weak").
    rs = fresh_set("Summarize technical documents of around twenty pages accurately.",
                   "Stay under two hundred dollars a month at five thousand requests per day.",
                   "Process data that may not leave the United States.")
    proposals = [
        [proposed("ctx", "context_window", ">=", 100_000, "tokens", "moderate", "capability")],
        [proposed("price", "input_price", "<=", 5.0, "USD per 1M input tokens", "moderate", "cost"),
         proposed("out_price", "output_price", "<=", 15.0, "USD per 1M output tokens", "weak", "cost")],
        [proposed("residency", "data_residency", "in", ["US"], "ISO 3166-1 alpha-2", "strong", "compliance")],
    ]
    validated = [validate(response(r["requirement_id"], p), rs, known_metrics=KNOWN_METRICS)
                 for r, p in zip(rs, proposals)]
    presented = present(validated)
    assert_conforms(presented, "PresentedMapping")
    shown = {e["requirement_id"]: e for e in presented["requirements"]}
    assert set(shown) == {r["requirement_id"] for r in rs}
    total = 0
    for r, p in zip(rs, proposals):
        entry = shown[r["requirement_id"]]
        assert entry["requirement"] == r["text"]
        assert [c["proxy_strength"] for c in entry["criteria"]] == [c["proxy_strength"] for c in p]
        for c in entry["criteria"]:
            assert c["proxy_strength"] in STRENGTHS
            assert c.get("requirement_id", r["requirement_id"]) == r["requirement_id"]
            total += 1
    assert total == sum(len(p) for p in proposals)  # 100% of criteria shown


def test_CR_1_4_4_confirmed_mapping_reaches_all_five_downstream_subsystems():
    # CR 1.4.4 Distribute Confirmed Mapping (traces to SR 1.4.1.1). MOP: downstream subsystems
    # that receive it, 5 of 5. T: integration test (F.1.2, F.1.3, F.1.4, F.1.5, F.1.7).
    requirement_set, mapping = integration_setup()
    outputs = distribute(copy.deepcopy(mapping), requirement_set, known_metrics=KNOWN_METRICS)
    required, hard, weighted, basis = outputs
    out = run_downstream(*outputs, integration_candidates())
    weighted_ids = set(weights_of(mapping))
    received = {
        "C.1.2 Evidence Retriever": set(out["data_request"]["metrics"]) == set(INTEGRATION_REQUIRED_METRICS),
        "C.1.3 Constraint Filter": [e["model_id"] for e in out["exclusions"]] == ["model-x"]
        and "residency" in out["exclusions"][0]["failed_constraints"],
        "C.1.4 Ranking Engine": bool(out["ranking"])
        and all(set(e["contributions"]) == weighted_ids for e in out["ranking"]),
        "C.1.5 Sensitivity Analyzer": {tuple(p) for p in out["finding"]["unstable_pairs"]}
        == brute_force_unstable_pairs(out["ranking"], weighted_ids),
        "C.1.7 Decision Recorder": out["record"]["criteria_mapping"] == mapping
        and out["record"]["weights"] == weights_of(mapping),
    }
    missed = [name for name, ok in received.items() if not ok]
    assert not missed, f"{5 - len(missed)} of 5 received the confirmed mapping; missed: {missed}"


@pytest.mark.parametrize("case", ["unknown_metric", "empty_requirement_set"])
def test_CR_1_4_4_unusable_confirmed_mapping_rejected(case):
    # CR 1.4.4 / contract distributeConfirmedMapping 422 -> ValueError: "An empty requirement
    # set ... or a metric not on the known metrics list" (C.1.1.4 checks the confirmed mapping
    # against the known metrics list, SPEC 7).
    rs = fresh_set()
    c = {**valid_criterion(), "requirement_id": rs[0]["requirement_id"], "designation": "weighted", "weight": 1.0}
    if case == "unknown_metric":
        c["metric"] = "not_a_known_metric_cr_1_4_4"
    else:
        rs = []
    with pytest.raises(ValueError):
        distribute([c], rs, known_metrics=KNOWN_METRICS)


# CR 2.x System-wide requirements flowed down ----------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_2_1_1_mapping_review_walkthrough_within_10_minutes(scenario_id):
    # CR 2.1.1 Mapping review effort (traces to SR 2.1.1; apportioned 10 of 30 minutes, Table 9).
    # MOP: operator minutes to review and confirm, target <= 10. D: timed walkthrough of each
    # scenario (walkthroughs.csv, label MAPPING_REVIEW:<scenario_id>).
    minutes = mapping_review_minutes(scenario_id)
    assert max(minutes) <= MAPPING_REVIEW_MAX_MINUTES, minutes


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_2_1_2_distributed_copies_identical_to_confirmed_mapping(scenario_id):
    # CR 2.1.2 Mapping consistency (traces to SR 2.1.3 by synthesis). MOP: downstream copies
    # identical to the confirmed mapping, 100%. T: compare received and confirmed mappings.
    _, requirement_set = interpret(USER_INPUTS[scenario_id])
    mapping = scenario_mapping(scenario_id, requirement_set)
    confirmed = copy.deepcopy(mapping)
    required, hard, weighted, basis = distribute(mapping, requirement_set, known_metrics=KNOWN_METRICS)
    assert mapping == confirmed, "the confirmed mapping was modified"
    assert hard == [c for c in confirmed if c["designation"] == "hard"]          # Constraint Filter
    assert weighted == [c for c in confirmed if c["designation"] == "weighted"]  # Ranking Engine, Sensitivity Analyzer
    assert basis["criteria_mapping"] == confirmed                                # Decision Recorder
    assert basis["weights"] == weights_of(confirmed)
    assert required == unique_metrics(confirmed)


def test_CR_2_1_2_receivers_hold_the_confirmed_mapping_unmodified():
    # CR 2.1.2: what the Constraint Filter, Ranking Engine, Sensitivity Analyzer and Decision
    # Recorder receive (and keep) is the confirmed mapping without modification.
    requirement_set, mapping = integration_setup()
    confirmed = copy.deepcopy(mapping)
    outputs = distribute(mapping, requirement_set, known_metrics=KNOWN_METRICS)
    _, hard, weighted, basis = outputs
    given = (copy.deepcopy(hard), copy.deepcopy(weighted), copy.deepcopy(basis))
    assert given[0] + given[1] == [c for c in confirmed if c["designation"] == "hard"] + \
        [c for c in confirmed if c["designation"] == "weighted"]
    record = run_downstream(*outputs, integration_candidates())["record"]
    assert record["criteria_mapping"] == confirmed
    assert record["weights"] == weights_of(confirmed)
    assert mapping == confirmed


def test_CR_2_2_1_runtime_configuration_points_to_local_host(monkeypatch):
    # CR 2.2.1 Local interpretation (traces to SR 2.2.1). MOP: requests sent to a local
    # endpoint, 100%. I: runtime configuration (SPEC 3 Adapter: default
    # http://127.0.0.1:1234/v1; any other host is refused).
    requests, _ = interpret(STATED_TEXT)
    # The request carries no endpoint of its own (SPEC 3 request shape), so where it goes is
    # decided only by the runtime configuration.
    for req in requests:
        assert set(req) == {"requirement_id", "text"}, req
    runtime_config = _import_or_fail(F8, "runtime_config")
    monkeypatch.delenv("LLM_RUNTIME_URL", raising=False)
    assert urllib.parse.urlsplit(runtime_config()["base_url"]).hostname in LOCAL_HOSTS
    default = getattr(importlib.import_module(F8), "DEFAULT_RUNTIME_URL", None)
    assert default and urllib.parse.urlsplit(default).hostname in LOCAL_HOSTS, default


PAID_MARKERS = (
    "api.openai.com", "api.anthropic.com", "openrouter.ai", "generativelanguage.googleapis.com",
    "api.mistral.ai", "api.cohere", "api.groq.com", "api.together",
    "api_key", "openai_api_key", "anthropic_api_key", "openrouter_api_key", "gemini_api_key",
)


def test_CR_2_4_1_configuration_and_run_show_no_paid_calls(monkeypatch):
    # CR 2.4.1 Query cost (traces to SR 2.4.1). MOP: paid charges per comparison, target 0.
    # I: configuration and run logs.
    sources = {f"{PKG}.{m}": component_source(m) for m in COMPONENT_MODULES}
    adapter = importlib.import_module(F8)
    sources[F8] = Path(inspect.getsourcefile(adapter)).read_text()

    # Configuration: the runtime is the local one, with no hosted-API credentials.
    monkeypatch.delenv("LLM_RUNTIME_URL", raising=False)
    config = _import_or_fail(F8, "runtime_config")()
    assert urllib.parse.urlsplit(config["base_url"]).hostname in LOCAL_HOSTS, config
    assert not [k for k in config if re.search(r"key|secret|auth|bearer", k, re.I)], config
    # Source text of the interpretation path names no paid endpoint or hosted-API key.
    found = {name: [m for m in PAID_MARKERS if m in text.lower()] for name, text in sources.items()}
    assert not any(found.values()), found

    # Run log: one comparison's criteria phase per scenario makes no external call.
    attempts = block_network(monkeypatch)
    for scenario_id in SCENARIOS:
        requests, requirement_set = interpret(USER_INPUTS[scenario_id])
        validated = [validate(response(req["requirement_id"], scenario_proposal(scenario_id)),
                              requirement_set, known_metrics=KNOWN_METRICS) for req in requests]
        present(validated)
        distribute(scenario_mapping(scenario_id, requirement_set), requirement_set,
                   known_metrics=KNOWN_METRICS)
    assert attempts == [], attempts


@pytest.mark.parametrize("case", ["requirement_id_not_a_string", "bad_category", "non_bool_no_proxy",
                                  "missing_rationale", "criteria_missing"])
def test_CR_2_3_1_only_model_contract_responses_accepted(case):
    # CR 2.3.1 Model contract (traces to SR 2.3.1). MOP: requests and responses that conform,
    # 100%. T: contract validation. A response outside the SPEC 3 form is not accepted.
    rs = fresh_set()
    rid = rs[0]["requirement_id"]
    reply = response(rid, [valid_criterion()])
    if case == "requirement_id_not_a_string":
        reply["requirement_id"] = 7
    elif case == "bad_category":
        reply["criteria"][0]["category"] = "speed"
    elif case == "non_bool_no_proxy":
        reply["no_suitable_proxy"] = "no"
    elif case == "missing_rationale":
        del reply["criteria"][0]["rationale"]
    else:
        del reply["criteria"]
    result = validate(reply, rs, known_metrics=KNOWN_METRICS)
    assert result["status"] != "proposed", result
    assert result["criteria"] == []


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_CR_2_3_1_requests_and_accepted_responses_conform(scenario_id):
    # CR 2.3.1: requests are sent only in the SPEC 3 request form ({requirement_id, text}), and
    # what is accepted conforms to the SPEC 3 response and the contract's ValidatedCriteria.
    requests, requirement_set = interpret(USER_INPUTS[scenario_id])
    assert_conforms(requirement_set, "RequirementSet")
    for req in requests:
        assert set(req) == {"requirement_id", "text"}, req
        assert_conforms(req, "InterpretationRequest")
        reply = response(req["requirement_id"], scenario_proposal(scenario_id))
        result = validate(copy.deepcopy(reply), requirement_set, known_metrics=KNOWN_METRICS)
        assert result["status"] == "proposed", result
        assert_conforms(result, "ValidatedCriteria")
        accepted = {"requirement_id": result["requirement_id"],
                    "no_suitable_proxy": result["no_suitable_proxy"],
                    "criteria": [spec3_fields(c) for c in result["criteria"]]}
        assert_conforms(accepted, "SPEC3Response")
        assert accepted == reply
        assert_spec3_valid(result["criteria"], KNOWN_METRICS)
