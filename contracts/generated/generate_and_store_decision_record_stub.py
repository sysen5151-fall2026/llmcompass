"""GENERATED from contracts/api-v1.yaml (v1.0.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.7 Generate and Store Decision Record.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def generate_and_store_decision_record(selection_rationale: dict, model_selection: Optional[str], decision_basis: Optional[dict] = None) -> dict:
    """operationId: generateAndStoreDecisionRecord. F.1.6, F.1.1 -> F.1.7 (implements SR 1.4.1.7)
    
    in: selection_rationale, model_selection, decision_basis. control: -. out: decision_record.
    raises: ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/generate_and_store_decision_record.py


def retrieve_decision_record(record_id: str) -> dict:
    """operationId: retrieveDecisionRecord. F.1.7 -> boundary (implements SR 1.4.1.7)
    
    in: record_id. control: -. out: decision_record.
    raises: LookupError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/generate_and_store_decision_record.py
