-- F.7 Provide Benchmark Evidence -- stored snapshots of the on-demand pull (SPEC section 2,
-- "Refresh" and "Source unavailable"; SR 1.3.3). SQLite (ADR-0005). Lab Manual 8.5.
-- Every figure keeps its source and date (SN-TL-02 / 5.1.2.1, SR 1.1.2): the NOT NULL and
-- CHECK constraints reject a figure missing either one at entry.
CREATE TABLE IF NOT EXISTS pulls (
    pull_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    pulled_at    TEXT NOT NULL,                       -- UTC ISO 8601
    status       TEXT NOT NULL CHECK (status IN ('ok', 'source_unavailable')),
    detail_json  TEXT NOT NULL CHECK (json_valid(detail_json))   -- gaps and source errors
);

CREATE TABLE IF NOT EXISTS candidates (
    pull_id         INTEGER NOT NULL REFERENCES pulls(pull_id),
    model_id        TEXT NOT NULL,
    vendor          TEXT NOT NULL,
    model_name      TEXT NOT NULL,
    candidate_json  TEXT NOT NULL CHECK (json_valid(candidate_json)),  -- the SPEC section 2 candidate
    PRIMARY KEY (pull_id, model_id)
);

CREATE TABLE IF NOT EXISTS figures (
    pull_id          INTEGER NOT NULL,
    model_id         TEXT NOT NULL,
    field            TEXT NOT NULL,       -- SPEC section 2 field name, or benchmark:<benchmark_id>
    value_json       TEXT NOT NULL CHECK (json_valid(value_json)),
    unit             TEXT NOT NULL,
    source_id        TEXT NOT NULL CHECK (length(source_id) > 0),
    collection_date  TEXT NOT NULL CHECK (date(collection_date) IS collection_date),
    PRIMARY KEY (pull_id, model_id, field),
    FOREIGN KEY (pull_id, model_id) REFERENCES candidates(pull_id, model_id)
);
