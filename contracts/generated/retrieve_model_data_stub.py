"""GENERATED from contracts/api-v1.yaml (v1.0.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.2 Retrieve Model Data.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def request_model_data(required_metrics: list) -> dict:
    """operationId: requestModelData. F.1.1 -> F.1.2 (implements SR 1.4.1.2)
    
    in: required_metrics. control: -. out: data_request.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/retrieve_model_data.py


def receive_model_data(model_data_with_provenance: list, *, staleness_threshold: timedelta = timedelta(days=90)) -> list:
    """operationId: receiveModelData. F.1.2 -> F.1.3 (implements SR 1.4.1.2)
    
    in: model_data_with_provenance. control: staleness_threshold. out: candidate_evidence.
    raises: LookupError, ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/retrieve_model_data.py
