"""GENERATED from contracts/api-v1.yaml (v1.0.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.6 Report Selection Rationale.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def report_selection_rationale(ranking: list, exclusions: list, sensitivity_finding: dict) -> tuple[dict, dict]:
    """operationId: reportSelectionRationale. F.1.6 -> F.1.7 (implements SR 1.4.1.6)
    
    in: ranking, exclusions, sensitivity_finding. control: -. out: presented_ranking_and_sensitivity, selection_rationale.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/report_selection_rationale.py
