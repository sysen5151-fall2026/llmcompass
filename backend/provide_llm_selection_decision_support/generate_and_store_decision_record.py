"""Implements F.1.7 -- Generate and Store Decision Record. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.7 (SN-TL-09 / 5.1.3.2, SN-TL-06 / 5.1.3.3). IDEF0 A1 of F.1, 2026-10-26.
# Sits behind contracts/api-v1.yaml: generateAndStoreDecisionRecord, retrieveDecisionRecord.

import json
import os
import uuid
from pathlib import Path
from typing import Optional

# SN-TL-09 / 5.1.3.2 -- the six record sections; the selection is the seventh (SR 1.2.2).
RECORD_SECTIONS = ("requirements", "criteria_mapping", "weights", "evidence", "ranking", "sensitivity")
DECISION_BASIS_SECTIONS = ("requirements", "criteria_mapping", "weights")  # flow 5.4 (ADR-0002)

# Where records persist, so they survive a restart (5.1.3.3). Storage belongs to
# mechanism C.1, so it is configuration, not an IDEF0 arrow.
DEFAULT_RECORD_DIR = Path(__file__).resolve().parents[2] / "data" / "decision_records"


def _record_dir() -> Path:
    return Path(os.environ.get("DECISION_RECORD_DIR") or DEFAULT_RECORD_DIR)


def _record_path(record_id: str) -> Path:
    if not isinstance(record_id, str) or not record_id or Path(record_id).name != record_id:
        raise LookupError(f"no decision record {record_id!r}")
    return _record_dir() / f"{record_id}.json"


def store_decision_record(record: dict) -> str:
    # SPEC section 4; SR 1.4.1.7, SN-TL-06 / 5.1.3.3 -- kept as JSON, retrievable after the session ends
    record_id = record.get("record_id") or f"REC-{uuid.uuid4().hex}"
    path = _record_path(record_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))
    return record_id


def retrieve_decision_record(record_id: str) -> dict:
    # SPEC section 4; SR 1.4.1.7, SN-TL-06 / 5.1.3.3 -- an unknown ID is not found
    path = _record_path(record_id)
    if not path.exists():
        raise LookupError(f"no decision record {record_id!r}")
    return json.loads(path.read_text())


def generate_and_store_decision_record(selection_rationale: dict, model_selection: Optional[str],
                                       decision_basis: Optional[dict] = None) -> dict:
    """Function: F.1.7 -- Generate and Store Decision Record. Contract operation generateAndStoreDecisionRecord.

    in: selection_rationale (8.1), model_selection, decision_basis (5.4). out: decision_record.
    """
    # UC.1.17-1.18 (SR 1.4.1.7, SR 1.1.3, SR 1.2.2)
    if model_selection is not None and model_selection not in selection_rationale["ranking"]:
        raise ValueError(f"{model_selection} is not in the ranking.")
    # SR 1.2.2 -- requirements, mapping and weights come from flow 5.4 Decision basis (ADR-0002).
    # Without it they come from the rationale's same-named keys (contract A4).
    basis = decision_basis if decision_basis is not None else selection_rationale
    # SR 1.2.2 -- each of these sections must be filled in (contract 422, A27)
    empty = [k for k in DECISION_BASIS_SECTIONS if not basis.get(k)]
    if empty:
        raise ValueError(f"The record sections {empty} would be empty.")
    record = {k: basis[k] for k in DECISION_BASIS_SECTIONS}
    record.update({k: selection_rationale[k] for k in ("evidence", "ranking", "sensitivity")})
    if "score_breakdown" in selection_rationale:
        record["score_breakdown"] = selection_rationale["score_breakdown"]
    record["excluded"] = selection_rationale.get("excluded", [])  # SN-TL-07 / 5.1.6.3
    record["selected_model"] = model_selection  # SR 1.1.3 -- unchanged; None = UC alt flow 15a
    record["record_id"] = f"REC-{uuid.uuid4().hex}"
    store_decision_record(record)
    return record
