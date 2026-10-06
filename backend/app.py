"""Walking skeleton entry point. A thin Flask shell around the UC.1 call order
from docs/walking-skeleton.md. No logic here: the typed text goes into the step
chain and the assembled decision record is shown.

Run: python3 backend/app.py, then open http://127.0.0.1:5000
"""

import json

from flask import Flask, render_template, request

from language_model_runtime import submit_requirements
from llm_compass import (
    receive_requirements,
    present_mapping_for_review,
    confirm_mapping,
    present_sensitivity_finding,
    select_model,
    generate_decision_record,
)
from benchmark_data_sources import request_model_data

app = Flask(__name__)


def run_uc1(text: str) -> dict:
    requirements = receive_requirements(text)                                       # 1  UC.1.2
    interpretation = submit_requirements(requirements)                              # 2, 3  UC.1.3, UC.1.4
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


@app.route("/", methods=["GET", "POST"])
def index():
    text = request.form.get("requirements", "")
    if request.method == "GET":
        return render_template("index.html", text=text)
    try:
        record = run_uc1(text)
    except ValueError as e:  # SN-TL-01 / 5.1.1.1 -- show the rejection from UC.1.2
        return render_template("index.html", text=text, error=str(e))
    return render_template("index.html", text=text, record=record,
                           raw=json.dumps(record, indent=2))


if __name__ == "__main__":
    app.run(debug=True)
