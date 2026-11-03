-- F.1.7 Generate and Store Decision Record -- storage for C.1.7 Decision Recorder.
-- SR 1.4.1.7, SN-TL-06 / 5.1.3.3 (retrievable after the session ends), SR 2.1.4 (retained
-- >= 6 months: no statement in the product deletes a row). SQLite (ADR-0005).
-- The record body is the SPEC section 1 / 5.1.3.2 record as JSON. Only the selection is
-- copied into its own column (SR 1.1.3), so an inspection can see what was chosen.
CREATE TABLE IF NOT EXISTS decision_records (
    record_id       TEXT PRIMARY KEY,
    stored_at       TEXT NOT NULL,              -- UTC ISO 8601, when the record was stored
    selected_model  TEXT,                       -- SR 1.1.3; NULL = UC.1 alt flow 15a
    record_json     TEXT NOT NULL CHECK (json_valid(record_json))
);
