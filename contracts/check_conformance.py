"""Check that F.1's sub-function modules conform to contracts/api-v1.yaml (Lab Manual 7.4).

1. Signatures: each def in backend/provide_llm_selection_decision_support/<x-module>.py
   matches its generated stub in contracts/generated/ (parameter names, kinds, defaults).
2. Payloads: F.1.1-F.1.7 are run on a SPEC section 2 data set, and every request and
   response is validated against its operation's schemas (OpenAPI 3.0).
3. Errors: each operation's x-python-raises is raised for its error condition.
4. Semantics: the rules a schema can't express (descending order, score = sum of
   contributions, pair order, stale flags, failed-constraint order, A25, F.1.7 basis).

Run: python3 contracts/check_conformance.py   (needs PyYAML, openapi-schema-validator)
Exits non-zero and lists every divergence when the code drifts from the contract.
"""

import builtins
import copy
import importlib.util
import inspect
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import yaml
from openapi_schema_validator import OAS30Validator, oas30_format_checker

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "api-v1.yaml"
GENERATED = ROOT / "contracts" / "generated"
sys.path.insert(0, str(ROOT / "backend"))

SPEC = yaml.safe_load(CONTRACT.read_text())
# Strict copy of the named schemas: a key the contract doesn't declare is drift too.
STRICT = copy.deepcopy(SPEC["components"])
for named in STRICT["schemas"].values():
    if named.get("type") == "object" and "properties" in named:
        named.setdefault("additionalProperties", False)
OPS = {op["operationId"]: op for item in SPEC["paths"].values() for m, op in item.items() if m == "post"}
problems = []


def snake(name: str) -> str:
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in name).lstrip("_")


def real_def(op_id: str):
    module = importlib.import_module(f"provide_llm_selection_decision_support.{OPS[op_id]['x-module']}")
    return getattr(module, snake(op_id), None)


def to_json(value):
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(to_json(v) for v in value)
    if isinstance(value, timedelta):
        return value.days
    if isinstance(value, date):
        return value.isoformat()
    return value


def validate(op_id: str, where: str, schema: dict, instance) -> None:
    root = {**schema, "components": STRICT}
    errors = sorted(OAS30Validator(root, format_checker=oas30_format_checker).iter_errors(to_json(instance)),
                    key=lambda e: list(e.absolute_path))
    for e in errors[:3]:
        path = "/".join(str(p) for p in e.absolute_path) or "(root)"
        problems.append(f"{op_id} {where} {path}: {e.message[:160]}")


def call(op_id: str, *args, **kwargs):
    """Call the real def, validating its request and response against the contract."""
    op = OPS[op_id]
    fn = real_def(op_id)
    if fn is None:
        raise LookupError(f"{op_id}: no def {snake(op_id)} in {op['x-module']}")
    request = op["requestBody"]["content"]["application/json"]["schema"]
    names = list(request["properties"])
    validate(op_id, "request", request, {**dict(zip(names, args)), **kwargs})
    result = fn(*args, **kwargs)
    response = op["responses"]["200"]["content"]["application/json"]["schema"]
    order = response["x-return-order"]
    validate(op_id, "response", response, dict(zip(order, result if len(order) > 1 else (result,))))
    return result


def raises(op_id: str, *args, **kwargs) -> None:
    expected = {r["x-python-raises"] for code, r in OPS[op_id]["responses"].items() if r.get("x-python-raises")}
    try:
        real_def(op_id)(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 -- any exception type is checked against the contract
        if not any(isinstance(e, getattr(builtins, name)) for name in expected):
            problems.append(f"{op_id} error: raised {type(e).__name__}, contract says {sorted(expected)}")
        return
    problems.append(f"{op_id} error: nothing raised, contract says {sorted(expected)}")


def expect(ok: bool, message: str) -> None:
    if not ok:
        problems.append(f"semantics: {message}")


def check_signatures() -> None:
    for stub_file in sorted(GENERATED.glob("*_stub.py")):
        spec = importlib.util.spec_from_file_location(stub_file.stem, stub_file)
        stubs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stubs)
        for op_id, op in OPS.items():
            if f"{op['x-module']}_stub" != stub_file.stem:
                continue
            stub, real = getattr(stubs, snake(op_id)), real_def(op_id)
            if real is None:
                problems.append(f"{op_id}: no def {snake(op_id)} in {op['x-module']}")
                continue
            want = [(p.name, p.kind, p.default) for p in inspect.signature(stub).parameters.values()]
            got = [(p.name, p.kind, p.default) for p in inspect.signature(real).parameters.values()]
            if want != got:
                problems.append(f"{op_id} signature: contract {inspect.signature(stub)} != code {inspect.signature(real)}")


def figure(value, unit, days_old=10):
    return {"value": value, "unit": unit, "source_id": "https://example.com/source",
            "collection_date": (date.today() - timedelta(days=days_old)).isoformat()}


def candidate(model_id, context, price, residency=("US",), days_old=10, latency=2.0):
    cand = {"model_id": model_id, "vendor": f"vendor-{model_id}", "model_name": model_id,
            "input_price": figure(price, "USD per 1M input tokens", days_old),
            "output_price": figure(price * 4, "USD per 1M output tokens", days_old),
            "context_window": figure(context, "tokens", days_old),
            "data_residency": figure(list(residency), "ISO 3166-1 alpha-2", days_old)}
    if latency is not None:
        cand["latency_p50"] = figure(latency, "seconds", days_old)
    return cand


def criterion(cid, metric, operator, threshold, designation, weight=None):
    c = {"criterion_id": cid, "metric": metric, "operator": operator, "threshold": threshold, "unit": "",
         "proxy_strength": "strong", "category": "other", "rationale": "", "designation": designation}
    if weight is not None:
        c["weight"] = weight
    return c


def check_payloads() -> None:
    mapping = [criterion("ctx", "context_window", ">=", 100_000, "weighted", 0.4),
               criterion("price", "input_price", "<=", 5.0, "weighted", 0.4),
               criterion("latency", "latency_p50", "<=", 3.0, "weighted", 0.2),
               criterion("ctx_hard", "context_window", ">=", 100_000, "hard"),  # a repeated metric (A25)
               criterion("residency", "data_residency", "in", ["US"], "hard")]
    stored = [candidate("model-1", 200_000, 3.0), candidate("model-2", 100_000, 1.0, days_old=120),
              candidate("model-3", 150_000, 3.0, latency=None),  # a weighted-criterion gap
              candidate("model-x", 300_000, 0.5, residency=("DE",)),  # fails one hard constraint
              candidate("model-y", 50_000, 0.5, residency=("DE",))]  # fails two, in mapping order (A12)
    no_residency = candidate("model-m", 150_000, 1.0)
    del no_residency["data_residency"]  # excluded with missing_data:data_residency
    stored.append(no_residency)
    stored_ids = {c["model_id"]: c for c in stored}

    weighted, hard, required = call("splitConfirmedMapping", copy.deepcopy(mapping))
    basis = call("compileDecisionBasis", ["Summarize long documents cheaply, data stays in the US."],
                 copy.deepcopy(mapping))
    call("requestModelData", required)
    evidence = call("receiveModelData", copy.deepcopy(stored))
    eligible, exclusions = call("applyHardConstraints", evidence, hard_constraints=hard)
    ranking = call("scoreAndRankCandidates", eligible, weighted_criteria=weighted)
    finding = call("analyzeRankingSensitivity", ranking, weighted_criteria=weighted)
    presented, rationale = call("reportSelectionRationale", ranking, exclusions, finding)
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DECISION_RECORD_DIR"] = tmp
        selection = rationale["ranking"][0]
        record = call("generateAndStoreDecisionRecord", rationale, selection, basis)
        retrieved = call("retrieveDecisionRecord", record["record_id"])
        raises("retrieveDecisionRecord", "REC-does-not-exist")
        raises("generateAndStoreDecisionRecord", rationale, "model-not-ranked", basis)
        raises("generateAndStoreDecisionRecord", rationale, selection, {**basis, "weights": {}})

    order = [e["model_id"] for e in ranking]
    pos = {m: i for i, m in enumerate(order)}
    failed = {e["model_id"]: e["failed_constraints"] for e in exclusions}
    expect(required == list(dict.fromkeys(c["metric"] for c in mapping)), "5.1 metrics once each, mapping order (A25)")
    expect([c["criterion_id"] for c in weighted] == ["ctx", "price", "latency"]
           and [c["criterion_id"] for c in hard] == ["ctx_hard", "residency"], "5.2/5.3 split by designation")
    expect(all({k: v for k, v in f.items() if k != "stale"} == s for c, o in zip(evidence, stored)
               for f, s in [(c[m], o[m]) for m in o if isinstance(o[m], dict)]), "7.1 figures keep source and date")
    expect(all(c[m]["stale"] is (c["model_id"] == "model-2") for c in evidence for m in c if isinstance(c[m], dict)),
           "7.1 stale flag: 120 days stale, 10 days not (A5)")
    expect(failed == {"model-x": ["residency"], "model-y": ["ctx_hard", "residency"],
                      "model-m": ["missing_data:data_residency"]}, f"7.3 failed constraints (A12): {failed}")
    expect(sorted(order) == sorted(c["model_id"] for c in eligible)
           and not set(order) & set(failed), "7.2/7.4 eligible = ranked, disjoint from excluded")
    expect(all(a["score"] >= b["score"] for a, b in zip(ranking, ranking[1:])), "7.4 descending score order")
    expect(all(abs(e["score"] - sum(e["contributions"].values())) < 1e-9
               and set(e["contributions"]) == {"ctx", "price", "latency"} for e in ranking),
           "7.4 one contribution per weighted criterion, score = their sum")
    expect(next(e for e in ranking if e["model_id"] == "model-3")["missing_data"] == ["latency_p50"],
           "7.4 a weighted gap is listed in missing_data")
    pairs = finding["unstable_pairs"]
    expect(all(pos[a] < pos[b] for a, b in pairs)
           and pairs == sorted(pairs, key=lambda q: (pos[q[0]], pos[q[1]])), "7.5 pairs [higher, lower] in ranking order (A9)")
    expect(finding["ranking_is_stable"] is (not pairs), "7.5 ranking_is_stable")
    expect(presented["excluded"] == [{"model_id": e["model_id"], "failed_constraints": e["failed_constraints"]}
                                     for e in exclusions], "presented exclusions = 7.3")
    expect(all(presented[k] == rationale[k] for k in ("ranking", "excluded", "evidence", "unstable_pairs")),
           "8.1 carries the presented ranking, exclusions, evidence and pairs (SR 1.4.1.6)")
    expect({(e["model_id"], m) for e in ranking for m in required if m in stored_ids[e["model_id"]]}
           <= {(i["model_id"], i["metric"]) for i in presented["evidence"]}, "every figure used is shown (5.1.2.1)")
    expect(all(record[k] == basis[k] for k in ("requirements", "criteria_mapping", "weights")),
           "record's requirements, mapping and weights come from 5.4 (ADR-0002)")
    expect(record["selected_model"] == selection and retrieved == record, "record keeps the selection, retrieves unchanged")

    raises("splitConfirmedMapping", [{**mapping[0], "metric": "not_a_metric"}])
    raises("compileDecisionBasis", ["text"], [{**mapping[0], "metric": "not_a_metric"}])
    unsourced = copy.deepcopy(stored)
    unsourced[0]["input_price"]["source_id"] = ""
    raises("receiveModelData", unsourced)
    raises("receiveModelData", [])


def main() -> None:
    check_signatures()
    try:
        check_payloads()
    except Exception as e:  # noqa: BLE001 -- a crash mid-run is itself a divergence
        problems.append(f"payload run stopped: {type(e).__name__}: {e}")
    if problems:
        print(f"{len(problems)} divergence(s) from contracts/api-v1.yaml v{SPEC['info']['version']}:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"conforms to contracts/api-v1.yaml v{SPEC['info']['version']}: "
          f"{len(OPS)} operations, signatures, payloads and errors")


if __name__ == "__main__":
    main()
