"""Regression tests for the Lab 9.4 reconcile fixes (docs/deviation-log.md, "Reconciliation").

Each test pins one fixed deviation of the raw generation: D-02 (SR 1.2.3 unaltered text),
D-14 (SPEC 3 failure path, not a crash), D-15 (contract 422 -> ValueError), D-17 (presenter 422).
The CR tests themselves are tests/test_component_criteria_mapper.py (written from spec, unchanged).
"""

import importlib
import uuid

import pytest

# Submodules by module path: the package attribute of the same name is the first-level def (A28).
_PKG = "provide_llm_selection_decision_support.propose_criteria_mapping"
c111 = importlib.import_module(f"{_PKG}.request_interpretation")
c112 = importlib.import_module(f"{_PKG}.validate_proposed_criteria")
c113 = importlib.import_module(f"{_PKG}.present_criteria_mapping")
c114 = importlib.import_module(f"{_PKG}.distribute_confirmed_mapping")


def _requirement_set():
    return [{"requirement_id": f"R-{uuid.uuid4().hex}", "text": "Respond quickly."}]


def _criterion(**over):
    c = {"criterion_id": "c1", "metric": "latency_p50", "operator": "<=", "threshold": 2,
         "unit": "seconds", "proxy_strength": "strong", "category": "capability", "rationale": "speed"}
    return {**c, **over}


def test_D_02_stated_text_kept_as_typed():
    # SR 1.2.3 -- "carrying its ID and unaltered text": a leading "- " or "1." is part of the text
    requests, _ = c111.request_interpretation("- Respond quickly.\n1. Cost little.")
    assert [r["text"] for r in requests] == ["- Respond quickly.", "1. Cost little."]


@pytest.mark.parametrize("field", ["operator", "proxy_strength", "category"])
@pytest.mark.parametrize("bad", [["<="], {"x": 1}])
def test_D_14_unhashable_field_is_retry_then_failed_not_a_crash(field, bad):
    # SPEC 3 -- a wrong-schema response is retried once, then interpretation_failed
    rset = _requirement_set()
    reply = {"requirement_id": rset[0]["requirement_id"], "no_suitable_proxy": False,
             "criteria": [_criterion(**{field: bad})]}
    assert c112.validate_proposed_criteria(reply, rset)["status"] == "retry"
    assert c112.validate_proposed_criteria(reply, rset)["status"] == "interpretation_failed"


@pytest.mark.parametrize("field", ["metric", "operator", "designation"])
def test_D_15_unhashable_field_in_confirmed_mapping_is_value_error(field):
    # contracts/api-v1.yaml distributeConfirmedMapping 422 -> ValueError
    confirmed = [{**_criterion(), "designation": "weighted", "weight": 1, field: ["x"]}]
    with pytest.raises(ValueError):
        c114.distribute_confirmed_mapping(confirmed, _requirement_set())


def test_D_17_presenter_rejects_entry_without_requirement_id():
    with pytest.raises(ValueError):
        c113.present_criteria_mapping([{"status": "proposed", "criteria": []}])


# --- F.1.1 composition propose_mapping: re-send once on retry (ADR-0006; D-05, D-09-D-11, D-25) ---

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import provide_llm_selection_decision_support.propose_criteria_mapping as f11


@pytest.fixture
def fake_runtime(monkeypatch):
    """A local stand-in for LM Studio: replies[n] answers the n-th POST (SPEC 3 Adapter)."""
    state = {"replies": [], "requests": []}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append(body)
            reply = state["replies"][len(state["requests"]) - 1]
            content = reply(body) if callable(reply) else reply
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]}).encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("LLM_RUNTIME_URL", f"http://127.0.0.1:{server.server_port}/v1")
    yield state
    server.shutdown()


def _rid_of(body):
    return body["messages"][0]["content"].split("requirement_id: ")[1].split("\n")[0]


def _valid(body):
    return {"requirement_id": _rid_of(body), "no_suitable_proxy": False, "criteria": [_criterion()]}


def test_propose_mapping_resends_once_then_presents(fake_runtime):
    fake_runtime["replies"] = [{"not": "SPEC 3"}, _valid]
    presented, rset = f11.propose_mapping("Respond quickly.")
    assert len(fake_runtime["requests"]) == 2  # SR 1.3.2 -- re-sent once
    [entry] = presented["requirements"]
    assert entry["status"] == "proposed" and entry["criteria"][0]["proxy_strength"] == "strong"
    assert rset == [{"requirement_id": entry["requirement_id"], "text": "Respond quickly."}]


def test_propose_mapping_twice_invalid_is_interpretation_failed_and_leaves_no_retry(fake_runtime):
    fake_runtime["replies"] = [{"bad": 1}, {"bad": 2}, _valid]
    presented, _ = f11.propose_mapping("Respond quickly.")
    assert len(fake_runtime["requests"]) == 2
    assert presented["requirements"][0]["status"] == "interpretation_failed"
    assert presented["requirements"][0]["criteria"] == []  # never made up
    # D-09: the next comparison with the same text starts clean -- one valid reply is enough
    presented, _ = f11.propose_mapping("Respond quickly.")
    assert presented["requirements"][0]["status"] == "proposed"


def test_propose_mapping_one_request_per_line(fake_runtime):
    fake_runtime["replies"] = [_valid, _valid]
    presented, rset = f11.propose_mapping("Respond quickly.\n\nCost little.")
    assert [r["text"] for r in rset] == ["Respond quickly.", "Cost little."]
    assert [e["status"] for e in presented["requirements"]] == ["proposed", "proposed"]
