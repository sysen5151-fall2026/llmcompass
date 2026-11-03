"""Implements F.1.7 -- Generate and Store Decision Record. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.7 (SN-TL-09 / 5.1.3.2, SN-TL-06 / 5.1.3.3). IDEF0 A1 of F.1, 2026-10-26.
# Sits behind contracts/api-v1.yaml: generateAndStoreDecisionRecord, retrieveDecisionRecord.

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# SN-TL-09 / 5.1.3.2 -- the six record sections; the selection is the seventh (SR 1.2.2).
RECORD_SECTIONS = ("requirements", "criteria_mapping", "weights", "evidence", "ranking", "sensitivity")
DECISION_BASIS_SECTIONS = ("requirements", "criteria_mapping", "weights")  # flow 5.4 (ADR-0002)

# Where records persist, so they survive a restart (5.1.3.3). Storage belongs to
# mechanism C.1 (C.1.7 Decision Recorder), so it is configuration, not an IDEF0 arrow.
# SQLite, one file per directory (ADR-0005); the schema is decision_record_schema.sql.
DEFAULT_RECORD_DIR = Path(__file__).resolve().parents[2] / "data" / "decision_records"
SCHEMA = Path(__file__).with_name("decision_record_schema.sql")
DB_NAME = "decision_records.sqlite3"


def _record_dir() -> Path:
    return Path(os.environ.get("DECISION_RECORD_DIR") or DEFAULT_RECORD_DIR)


def _connect() -> sqlite3.Connection:
    # Lab Manual 8.5 -- schema from the record contract (SPEC section 1 / 5.1.3.2), ADR-0005
    directory = _record_dir()
    directory.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(directory / DB_NAME)
    conn.executescript(SCHEMA.read_text())
    return conn


def _check_id(record_id) -> str:
    if not isinstance(record_id, str) or not record_id or Path(record_id).name != record_id:
        raise LookupError(f"no decision record {record_id!r}")
    return record_id


def store_decision_record(record: dict) -> str:
    # SPEC section 4; SR 1.4.1.7, SN-TL-06 / 5.1.3.3 -- retrievable after the session ends.
    # SR 2.1.4 -- stored with its time; nothing in the product deletes a record.
    record_id = _check_id(record.get("record_id") or f"REC-{uuid.uuid4().hex}")
    stored_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = _connect()
    try:
        with conn:  # same behaviour as the JSON store: storing a record under an existing ID updates it
            conn.execute("INSERT OR REPLACE INTO decision_records VALUES (?, ?, ?, ?)",
                         (record_id, stored_at, record.get("selected_model"), json.dumps(record)))
    finally:
        conn.close()
    return record_id


def retrieve_decision_record(record_id: str) -> dict:
    # SPEC section 4; SR 1.4.1.7, SN-TL-06 / 5.1.3.3 -- an unknown ID is not found
    _check_id(record_id)
    conn = _connect()
    try:
        row = conn.execute("SELECT record_json FROM decision_records WHERE record_id = ?",
                           (record_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise LookupError(f"no decision record {record_id!r}")
    return json.loads(row[0])


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
