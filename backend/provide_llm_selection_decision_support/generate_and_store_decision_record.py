"""Implements F.1.7 -- Generate and Store Decision Record. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.7 (SN-TL-09 / 5.1.3.2, SN-TL-06 / 5.1.3.3). IDEF0 A1 of F.1, 2026-10-26.

import json
import os
import uuid
from pathlib import Path
from typing import Optional

# SN-TL-09 / 5.1.3.2 -- the six record sections; the selection is the seventh (SR 1.2.2).
RECORD_SECTIONS = ("requirements", "criteria_mapping", "weights", "evidence", "ranking", "sensitivity")

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


def generate_and_store_decision_record(selection_rationale: dict, model_selection: Optional[str]) -> dict:
    """Function: F.1.7 -- Generate and Store Decision Record.

    in: selection_rationale, model_selection. out: decision_record.
    """
    # UC.1.17-1.18 (SR 1.4.1.7, SR 1.1.3, SR 1.2.2)
    if model_selection is not None and model_selection not in selection_rationale["ranking"]:
        raise ValueError(f"{model_selection} is not in the ranking.")
    record = {section: selection_rationale[section] for section in RECORD_SECTIONS}
    record["selected_model"] = model_selection  # SR 1.1.3 -- unchanged; None = UC alt flow 15a
    if "excluded" in selection_rationale:
        record["excluded"] = selection_rationale["excluded"]  # SN-TL-07 / 5.1.6.3
    record["record_id"] = f"REC-{uuid.uuid4().hex}"
    store_decision_record(record)
    return record
