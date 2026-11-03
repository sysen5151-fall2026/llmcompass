# Data access component for C.7 Benchmark Data Sources (Lab Manual 8.5).
# file mode (default, tests): the stored catalog in sample_data/ -- still a STUB: Benchmark Data Sources.
# api mode: the latest snapshot of the on-demand pull from the live sources (SPEC section 2).
"""Implements F.7 -- Provide Benchmark Evidence. Mechanism: C.7 Benchmark Data Sources."""

import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"


# SPEC section 2, SPEC 5 Q7 -- the benchmark vocabulary and which source field feeds each id
# live in sample_data/benchmark_map.json (team, 2026-10-28), not in code.
BENCHMARK_MAP = json.loads((SAMPLE_DATA / "benchmark_map.json").read_text())["benchmarks"]
BENCHMARK_IDS = {bid: (*b["stored"], b["unit"]) for bid, b in BENCHMARK_MAP.items()}
# SPEC section 2 -- manual-entry fields (data residency, retention, deprecation), one entry per
# catalog model with its source, or a gap with the reason (sample_data/manual_entries.json).
MANUAL_FIELDS = ("data_residency", "data_retention", "deprecation_date")


def _figure(value, unit, source_id, collection_date):
    # SPEC section 2 figure -- every value keeps its source and date (SN-TL-02 / 5.1.2.1)
    return {"value": value, "unit": unit, "source_id": source_id, "collection_date": collection_date}


def _to_candidates(models: list, providers: dict, benchmark: dict) -> list:
    # Converts the sample files to the SPEC section 2 candidate shape.
    scores = {m["model_id"]: m for m in benchmark["models"]}
    bench_date = benchmark["benchmark_provider"]["retrieved_date_utc"]
    manual = json.loads((SAMPLE_DATA / "manual_entries.json").read_text())["models"]
    candidates = []
    for m in models:
        src, when = m["source_url"], m["retrieved_date"]
        cand = {
            "model_id": m["model_id"],
            "vendor": m["provider"],
            "model_name": m["model_name"],
            "input_price": _figure(m["input_price_per_1m_tokens_usd"], "USD per 1M input tokens", src, when),
            "output_price": _figure(m["output_price_per_1m_tokens_usd"], "USD per 1M output tokens", src, when),
            "context_window": _figure(m["context_window_tokens"], "tokens", src, when),
            "benchmarks": [],
        }
        for field in MANUAL_FIELDS:  # a gap stays absent, never filled in (SPEC section 2)
            entry = manual.get(m["model_id"], {}).get(field) or {}
            if "value" in entry:
                cand[field] = _figure(entry["value"], entry["unit"], entry["source_id"], entry["collection_date"])
        b = scores.get(m["model_id"])
        if b:
            for bid, (group, key, unit) in BENCHMARK_IDS.items():
                raw = b[group][key]
                value = raw["value"] if isinstance(raw, dict) else raw
                cand["benchmarks"].append({"benchmark_id": bid,
                                           "score": _figure(value, unit, b["sources"][0]["url"], bench_date)})
        candidates.append(cand)
    return candidates


def _load_catalog():
    # The stored catalog: increment 1 is manual entry in sample_data/ (SPEC section 2).
    models = json.loads((SAMPLE_DATA / "model_spec.json").read_text())
    providers = json.loads((SAMPLE_DATA / "providers.json").read_text())
    benchmark = json.loads((SAMPLE_DATA / "benchmark.json").read_text())
    return models, providers, benchmark


def request_model_data(confirmed_mapping: dict) -> dict:
    # UC.1.10, UC.1.11 -- call and return are the same function call (SN-TL-02 / 5.1.2.1)
    models, providers, benchmark = _load_catalog()
    return {
        "models": models,
        "providers": providers,
        "benchmark": benchmark,
        "candidates": _to_candidates(models, providers, benchmark),
    }


# --- F.7 ICOM signature (Lab Manual 4.4); body added in Chapter 5 (5.3) ---


def provide_model_data(*, data_request: dict) -> list:
    """Function: F.7 -- Provide Benchmark Evidence. Signature from Chapter 4; body added this increment.

    control: data_request. out: model_data_with_provenance.
    """
    # SR 1.3.3, SR 1.2.1 (catalog side), SR 1.4.1 (catalog side), SN-TL-02 / 5.1.2.1
    # UC.1.10, UC.1.11 -- file mode answers from the stored catalog.
    candidates = _to_candidates(*_load_catalog()) if _source_mode() == "file" else []
    # SR 1.2.1 -- "all" requests every candidate in the catalog; a list requests those model_ids.
    if _source_mode() == "api":
        # SPEC section 2 "Refresh" -- between pulls, serve the last stored snapshot; with none,
        # "no model data available" (an empty list; F.1.2 raises LookupError on it).
        candidates = _latest_snapshot()
    if data_request["models"] == "all":
        return candidates
    return [c for c in candidates if c["model_id"] in data_request["models"]]


# --- Data access component, api mode (Lab Manual 8.5; SPEC section 2, increment 2) ---
# SR 1.2.1 (every catalog model), SR 1.1.2 / SN-TL-02 / 5.1.2.1 (source and date on every
# figure), SR 1.3.3 (source unavailable -> last snapshot), SR 2.3.2 (data contract).
# Only fixed GET URLs and the API key header leave the machine (docs/deployment.md).

SOURCE_FIELDS = json.loads((SAMPLE_DATA / "source_fields.json").read_text())
MODEL_SOURCES = SAMPLE_DATA / "model_sources.json"
SNAPSHOT_SCHEMA = Path(__file__).with_name("snapshot_schema.sql")
DEFAULT_SNAPSHOT_DB = Path(__file__).resolve().parents[2] / "data" / "benchmark_snapshots.sqlite3"
DEFAULT_URLS = {
    "ARTIFICIAL_ANALYSIS_API_URL": "https://artificialanalysis.ai/api/v2/data/llms/models",
    "MODELS_DEV_API_URL": "https://models.dev/api.json",
    "OPENROUTER_API_URL": "https://openrouter.ai/api/v1/models",
}
HTTP_TIMEOUT_S = 30
REQUIRED_FIELDS = ("input_price", "output_price", "context_window")  # SPEC section 2, required


class SourceUnavailable(Exception):
    """A live source could not be read (SPEC section 2 "Source unavailable")."""


def _source_mode() -> str:
    mode = os.environ.get("BENCHMARK_SOURCE") or "file"  # empty in .env = the default
    if mode not in ("file", "api"):
        raise ValueError(f"BENCHMARK_SOURCE must be 'file' or 'api', not {mode!r}")
    return mode


def _snapshot_db() -> Path:
    return Path(os.environ.get("BENCHMARK_SNAPSHOT_DB") or DEFAULT_SNAPSHOT_DB)


def _connect() -> sqlite3.Connection:
    db = _snapshot_db()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(SNAPSHOT_SCHEMA.read_text())
    return conn


def _url(name: str) -> str:
    return os.environ.get(name) or DEFAULT_URLS[name]


def _get_json(url: str, headers: Optional[dict] = None):
    request = urllib.request.Request(url, headers={"User-Agent": "llm-compass", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as e:  # HTTPError is a URLError
        raise SourceUnavailable(f"{url}: {e}") from e


def _path(record, dotted: str):
    for key in dotted.split("."):
        if not isinstance(record, dict) or key not in record:
            return None
        record = record[key]
    return record


def _read(record, spec: dict):
    # benchmark_map.json / source_fields.json "missing_values": not measured -> a gap (team, 2026-10-30)
    value = _path(record, spec.get("path") or spec["field"])
    if value in spec.get("missing_values", [None]) or isinstance(value, bool):
        return None
    return value * spec.get("scale", 1) if isinstance(value, (int, float)) else value


def _pull_sources() -> dict:
    # One request per source per pull (Artificial Analysis allows 1,000 a day; docs/PLAN.md).
    key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    if not key:
        raise SourceUnavailable("ARTIFICIAL_ANALYSIS_API_KEY is not set (.env)")
    aa_url = _url("ARTIFICIAL_ANALYSIS_API_URL")
    aa = _get_json(aa_url, {"x-api-key": key})
    aa_records = {r.get(SOURCE_FIELDS["artificial_analysis"]["match"]): r
                  for r in _path(aa, SOURCE_FIELDS["artificial_analysis"]["records"]) or []}
    if not aa_records:
        raise SourceUnavailable(f"{aa_url}: no model records in the response")
    pulled = {"aa": (aa_url, aa_records), "models_dev": None, "openrouter": None, "errors": []}
    try:  # context window: models.dev, then OpenRouter (SPEC section 2)
        pulled["models_dev"] = (_url("MODELS_DEV_API_URL"), _get_json(_url("MODELS_DEV_API_URL")))
    except SourceUnavailable as e:
        pulled["errors"].append(str(e))
    try:
        orr = _get_json(_url("OPENROUTER_API_URL"))
        match = SOURCE_FIELDS["openrouter"]["match"]
        pulled["openrouter"] = (_url("OPENROUTER_API_URL"),
                                {r.get(match): r for r in _path(orr, SOURCE_FIELDS["openrouter"]["records"]) or []})
    except SourceUnavailable as e:
        pulled["errors"].append(str(e))
    return pulled


def _build_candidate(entry: dict, pulled: dict, today: str, manual: dict, gaps: list) -> Optional[dict]:
    # One SPEC section 2 candidate; every figure gets the URL it came from and the pull date.
    model_id = entry["model_id"]
    aa_url, aa_records = pulled["aa"]
    aa = aa_records.get(entry.get("artificial_analysis_id"))
    if aa is None:
        gaps.append({"model_id": model_id, "field": "*", "reason": "not in the Artificial Analysis response"})
        return None
    cand = {"model_id": model_id, "vendor": entry["vendor"],
            "model_name": aa.get(SOURCE_FIELDS["artificial_analysis"]["name"]) or model_id, "benchmarks": []}
    for field, spec in SOURCE_FIELDS["artificial_analysis"]["fields"].items():
        value = _read(aa, spec)
        if value is None:
            gaps.append({"model_id": model_id, "field": field, "reason": f"{spec['path']} not measured"})
        else:
            cand[field] = _figure(value, spec["unit"], aa_url, today)
    context = None
    if pulled["models_dev"] and entry.get("models_dev"):
        url, data = pulled["models_dev"]
        md = _path(data, f"{entry['models_dev']['provider']}.models")
        record = md.get(entry["models_dev"]["model"]) if isinstance(md, dict) else None
        value = _read(record, SOURCE_FIELDS["models_dev"]["fields"]["context_window"]) if record else None
        if value is not None:
            context = _figure(value, "tokens", url, today)
    if context is None and pulled["openrouter"] and entry.get("openrouter_id"):
        url, records = pulled["openrouter"]
        record = records.get(entry["openrouter_id"])
        value = _read(record, SOURCE_FIELDS["openrouter"]["fields"]["context_window"]) if record else None
        if value is not None:
            context = _figure(value, "tokens", url, today)
    if context is None:
        gaps.append({"model_id": model_id, "field": "context_window", "reason": "not on models.dev or OpenRouter"})
    else:
        cand["context_window"] = context
    for bid, b in BENCHMARK_MAP.items():
        api = b.get("artificial_analysis_api")
        value = _read(aa, api) if api else None
        if value is None:
            gaps.append({"model_id": model_id, "field": f"benchmark:{bid}",
                         "reason": "not published by the API" if not api else f"{api['field']} not measured"})
        else:
            cand["benchmarks"].append({"benchmark_id": bid, "score": _figure(value, b["unit"], aa_url, today)})
    for field in MANUAL_FIELDS:  # SPEC section 2 manual entry; a gap stays absent
        item = manual.get(model_id, {}).get(field) or {}
        if "value" not in item:
            continue
        if not item.get("source_id") or not item.get("collection_date"):
            # SR 1.1.2 -- a figure missing its source or date is rejected at entry, not stored
            gaps.append({"model_id": model_id, "field": field, "reason": "manual entry has no source_id or collection_date"})
            continue
        cand[field] = _figure(item["value"], item.get("unit", ""), item["source_id"], item["collection_date"])
    missing = [f for f in REQUIRED_FIELDS if f not in cand]
    if missing:  # SPEC section 2 -- a required field with no sourced figure is never filled in
        gaps.append({"model_id": model_id, "field": ",".join(missing), "reason": "required field missing; left out"})
        return None
    return cand


def _figures(cand: dict):
    for field, fig in cand.items():
        if isinstance(fig, dict) and "source_id" in fig:
            yield field, fig
    for b in cand["benchmarks"]:
        yield f"benchmark:{b['benchmark_id']}", b["score"]


def _store_pull(status: str, detail: dict, candidates: list, pulled_at: str) -> None:
    conn = _connect()
    try:
        _insert_pull(conn, status, detail, candidates, pulled_at)
    finally:
        conn.close()


def _insert_pull(conn: sqlite3.Connection, status: str, detail: dict, candidates: list, pulled_at: str) -> None:
    with conn:  # one transaction: a pull is stored whole or not at all
        cur = conn.execute("INSERT INTO pulls (pulled_at, status, detail_json) VALUES (?, ?, ?)",
                           (pulled_at, status, json.dumps(detail)))
        pull_id = cur.lastrowid
        for c in candidates:
            conn.execute("INSERT INTO candidates VALUES (?, ?, ?, ?, ?)",
                         (pull_id, c["model_id"], c["vendor"], c["model_name"], json.dumps(c)))
            for field, fig in _figures(c):  # SR 1.1.2 -- the schema rejects a figure without source/date
                conn.execute("INSERT INTO figures VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (pull_id, c["model_id"], field, json.dumps(fig["value"]), fig["unit"],
                              fig["source_id"], fig["collection_date"]))


def _latest_snapshot() -> list:
    # SR 1.3.3 -- the last successful pull, each figure with its own date (staleness is flagged by F.1.2)
    if not _snapshot_db().exists():
        return []
    conn = _connect()
    try:
        row = conn.execute("SELECT pull_id FROM pulls WHERE status = 'ok' ORDER BY pull_id DESC LIMIT 1").fetchone()
        rows = conn.execute("SELECT candidate_json FROM candidates WHERE pull_id = ? ORDER BY rowid",
                            (row[0],)).fetchall() if row else []
    finally:
        conn.close()
    return [json.loads(r[0]) for r in rows]


def refresh_model_data() -> dict:
    """On-demand pull from the live sources (SPEC section 2 "Refresh"; Lab Manual 8.5).

    Returns {"status": "ok" | "source_unavailable", "pulled_at", "candidates", "gaps"}.
    """
    pulled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    today = pulled_at[:10]  # collection_date is the pull date (SPEC section 2)
    try:
        pulled = _pull_sources()
    except SourceUnavailable as e:
        # SR 1.3.3 -- the last snapshot stays the one served; nothing is overwritten
        _store_pull("source_unavailable", {"errors": [str(e)]}, [], pulled_at)
        return {"status": "source_unavailable", "pulled_at": pulled_at, "candidates": 0,
                "gaps": [], "errors": [str(e)]}
    manual = json.loads((SAMPLE_DATA / "manual_entries.json").read_text())["models"]
    gaps = []
    entries = json.loads(MODEL_SOURCES.read_text())["models"]
    candidates = [c for c in (_build_candidate(e, pulled, today, manual, gaps) for e in entries) if c]
    if not candidates:
        # SR 1.3.3 -- nothing usable came back: keep serving the last snapshot (SPEC section 2 "Source unavailable")
        errors = pulled["errors"] + ["the pull produced no candidate with every required field"]
        _store_pull("source_unavailable", {"gaps": gaps, "errors": errors}, [], pulled_at)
        return {"status": "source_unavailable", "pulled_at": pulled_at, "candidates": 0,
                "gaps": gaps, "errors": errors}
    _store_pull("ok", {"gaps": gaps, "errors": pulled["errors"]}, candidates, pulled_at)
    return {"status": "ok", "pulled_at": pulled_at, "candidates": len(candidates),
            "gaps": gaps, "errors": pulled["errors"]}
