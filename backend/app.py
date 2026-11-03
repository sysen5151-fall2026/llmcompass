"""Web entry point: a thin Flask shell around the UC.1 call order (docs/walking-skeleton.md,
docs/route-table.md). No decision logic here: each route calls the F.1 / C.1.1 defs in order
and shows what they return.

  POST /         UC.1.2-UC.1.6  stated requirements -> C.1.1 (live interpretation) -> review page
  POST /confirm  UC.1.9         confirmed mapping -> C.1.1.4 -> F.1.2-F.1.7 -> result page

run_uc1(text) is the walking-skeleton path for the sample scenarios (tests/test_walking_skeleton.py).

Run: cd backend && ../.venv/bin/python app.py, then open http://127.0.0.1:5000
"""

import copy
import importlib
import json
import math

from flask import Flask, render_template, request

# STUB path for run_uc1 only: the walking skeleton shows the stored interpretation
from provide_requirement_interpretation import scenario_interpretation
from provide_llm_selection_decision_support import (
    analyze_ranking_sensitivity,
    apply_hard_constraints,
    confirm_mapping,
    generate_and_store_decision_record,
    generate_decision_record,
    present_mapping_for_review,
    present_sensitivity_finding,
    receive_model_data,
    receive_requirements,
    report_selection_rationale,
    score_and_rank_candidates,
    select_model,
)
from provide_llm_selection_decision_support import request_model_data as retrieve_model_data_request  # F.1.2
from provide_llm_selection_decision_support.propose_criteria_mapping import KNOWN_METRICS, propose_mapping
from provide_benchmark_evidence import provide_model_data  # F.7 (BENCHMARK_SOURCE: file or api)
from provide_benchmark_evidence import request_model_data

# C.1.1.4 by module path: the package attribute of the same name is a first-level def (A28)
_c114 = importlib.import_module("provide_llm_selection_decision_support.propose_criteria_mapping"
                                ".distribute_confirmed_mapping")

# No /static/<filename> route: it traced to no use case (Lab Manual 6.4 audit, docs/route-table.md)
app = Flask(__name__, static_folder=None)


def run_uc1(text: str) -> dict:
    requirements = receive_requirements(text)                                       # 1  UC.1.2
    interpretation = scenario_interpretation(requirements)                          # 2, 3  UC.1.3, UC.1.4
    mapping = present_mapping_for_review(interpretation)                            # 4  UC.1.6
    confirmed = confirm_mapping(mapping)                                            # 5  UC.1.9
    model_data = request_model_data(confirmed)                                      # 6, 7  UC.1.10, UC.1.11
    finding = present_sensitivity_finding(model_data, confirmed, requirements)      # 8  UC.1.16
    selection = select_model(finding)                                               # 9  UC.1.17
    record = generate_decision_record(selection)                                    # 10 UC.1.18
    # One section per step, shown on the page in this order.
    return {
        "scenario_id": requirements["scenario_id"],
        "interpreted_requirements": interpretation["interpreted_requirements"],
        "comparison_result": finding["comparison_result"],
        "selection_result": selection["selection_result"],
        "decision_record": record,
    }


def run_confirmed_mapping(confirmed_criteria_mapping: list, requirement_set: list) -> dict:
    """UC.1.9-UC.1.18 from the Technical Lead's confirmed mapping (docs/PLAN.md "Milestone 2 UI wiring")."""
    # F.1.1.4 / C.1.1.4 -- flows 5.1-5.4 (CR 1.4.4, CR 2.1.2); ValueError goes back to the review page
    required, hard, weighted, basis = _c114.distribute_confirmed_mapping(confirmed_criteria_mapping,
                                                                         requirement_set)
    data_request = retrieve_model_data_request(required)                             # F.1.2  UC.1.10
    model_data = provide_model_data(data_request=data_request)                       # F.7    UC.1.11
    evidence = receive_model_data(model_data)                                        # F.1.2
    eligible, exclusions = apply_hard_constraints(evidence, hard_constraints=hard)   # F.1.3
    # CR 1.2.6, CR 2.1.2 -- the Ranking Engine and the Sensitivity Analyzer each get their own copy
    ranking = score_and_rank_candidates(eligible, weighted_criteria=copy.deepcopy(weighted))   # F.1.4
    finding = analyze_ranking_sensitivity(ranking, weighted_criteria=copy.deepcopy(weighted))  # F.1.5
    presented, rationale = report_selection_rationale(ranking, exclusions, finding)  # F.1.6  UC.1.16
    try:
        # F.1.7 UC.1.18 -- no selection yet (UC.1.17 planned; A22)
        record, record_error = generate_and_store_decision_record(rationale, None, basis), None
    except ValueError as e:  # e.g. a mapping with no weighted criterion (A27, deviation log D-23)
        record, record_error = None, str(e)
    return {"presented": presented, "record": record, "record_error": record_error}


# --- review page form (docs/PLAN.md "Routes"): the Technical Lead confirms or edits each criterion ---

def _default_designation(criterion: dict) -> str:
    # Review-page default only; the Technical Lead confirms or changes it (UC.1.7, UC.1.8)
    return "hard" if criterion.get("category") == "compliance" else "weighted"


def _parse_threshold(operator: str, text: str):
    text = (text or "").strip()
    if not text:
        return None
    if operator == "in":
        return [part.strip() for part in text.split(",") if part.strip()]
    try:
        number = float(text) if "." in text or "e" in text.lower() else int(text)
    except ValueError:
        if operator == "==":
            return text
        raise ValueError(f"threshold {text!r} must be a number for {operator}")
    if not math.isfinite(number):
        raise ValueError(f"threshold {text!r} must be a finite number")
    return number


def _parse_weight(text: str):
    text = (text or "").strip()
    if not text:
        return None
    try:
        weight = float(text)
    except ValueError:
        raise ValueError(f"weight {text!r} must be a number")
    if not math.isfinite(weight):
        raise ValueError(f"weight {text!r} must be a finite number")
    return weight


def _show_threshold(value) -> str:
    if value is None:
        return ""
    return ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)


def _confirmed_from_form(form, presented: dict, requirement_set: list) -> list:
    confirmed, n = [], 0
    for entry in presented["requirements"]:
        for c in entry["criteria"]:
            if f"keep_{n}" in form:
                item = {k: v for k, v in c.items()}
                item["designation"] = form.get(f"designation_{n}", _default_designation(c))
                item["threshold"] = _parse_threshold(c["operator"], form.get(f"threshold_{n}", ""))
                if item["designation"] == "weighted":
                    item["weight"] = _parse_weight(form.get(f"weight_{n}", ""))
                confirmed.append(item)
            n += 1
    for k, req in enumerate(requirement_set):
        metric = form.get(f"new_{k}_metric", "").strip()
        if not metric:
            continue
        operator = form.get(f"new_{k}_operator", ">=")
        item = {"criterion_id": f"manual-{k + 1}", "requirement_id": req["requirement_id"], "metric": metric,
                "operator": operator, "threshold": _parse_threshold(operator, form.get(f"new_{k}_threshold", "")),
                "unit": form.get(f"new_{k}_unit", "").strip(),  # no proxy_strength: no model rated it
                "designation": form.get(f"new_{k}_designation", "weighted")}
        if item["designation"] == "weighted":
            item["weight"] = _parse_weight(form.get(f"new_{k}_weight", ""))
        confirmed.append(item)
    return confirmed


def _review(presented: dict, requirement_set: list, error=None, status=200):
    pending = json.dumps({"requirement_set": requirement_set, "presented_mapping": presented})
    return render_template("review.html", presented=presented, requirement_set=requirement_set,
                           pending=pending, error=error, known_metrics=sorted(KNOWN_METRICS),
                           default_designation=_default_designation, show_threshold=_show_threshold), status


@app.route("/", methods=["GET", "POST"])
def index():
    text = request.form.get("requirements", "")
    if request.method == "GET":
        return render_template("index.html", text=text)
    try:
        # UC.1.2-UC.1.6 -- F.1.1 / C.1.1: C.1.1.1 -> F.8 (LM Studio) -> C.1.1.2 -> C.1.1.3 (SR 1.3.1, CR 1.3.6)
        presented, requirement_set = propose_mapping(text)
    except ValueError as e:  # SR 1.1.5, CR 1.1.4 -- empty requirements, or a non-local runtime (CR 2.2.1)
        return render_template("index.html", text=text, error=str(e))
    return _review(presented, requirement_set)


@app.route("/confirm", methods=["POST"])
def confirm():
    # UC.1.9 Confirm the mapping (with UC.1.7 review/amend, UC.1.8 weights) -- CR 1.1.1, CR 1.3.6
    try:
        pending = json.loads(request.form["pending"])
        presented, requirement_set = pending["presented_mapping"], pending["requirement_set"]
        if not (isinstance(requirement_set, list) and all(isinstance(e.get("criteria"), list)
                                                           for e in presented["requirements"])):
            raise ValueError("malformed pending mapping")
    except (KeyError, ValueError, TypeError, AttributeError):
        return render_template("index.html", text="", error="Nothing to confirm: start from the requirements form."), 400
    try:
        confirmed = _confirmed_from_form(request.form, presented, requirement_set)
        result = run_confirmed_mapping(confirmed, requirement_set)
    except ValueError as e:  # C.1.1.4 rejection: unknown metric, missing weight, bad threshold (CR 1.1.1)
        return _review(presented, requirement_set, error=str(e), status=422)
    return render_template("result.html", requirement_set=requirement_set, confirmed=confirmed, **result)


if __name__ == "__main__":
    # .env holds LLM_RUNTIME_URL, BENCHMARK_SOURCE and the data keys (docs/deployment.md)
    from provide_benchmark_evidence.__main__ import load_dotenv
    load_dotenv()
    # Debugger off: it traces to no requirement (Lab Manual 6.4 audit, docs/route-table.md)
    # threaded=False: C.1.1.2 keeps its retry count in module memory (deviation log D-09, ADR-0006),
    # so comparisons are served one at a time. This is a single-user local tool (docs/deployment.md).
    app.run(threaded=False)
