"""Lab Manual 8.5 data access component (F.7 api mode), tested against local fake sources.

SR 1.2.1 (every catalog model requested), SR 1.1.2 / SN-TL-02 / 5.1.2.1 (source and date on
every figure), SR 1.3.3 (source unavailable -> last snapshot), SR 2.3.2 (data contract).
No network: the three sources are served from 127.0.0.1.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

import provide_benchmark_evidence as f7

SOURCES = json.loads((Path(__file__).resolve().parents[1] / "sample_data" / "model_sources.json").read_text())["models"]


def _fake_payloads():
    aa = {"status": 200, "data": []}
    models_dev = {}
    for i, m in enumerate(SOURCES):
        rec = {"id": m["artificial_analysis_id"], "name": m["model_id"].upper(),
               "pricing": {"price_1m_input_tokens": 1.0 + i, "price_1m_output_tokens": 2.0 + i},
               "median_time_to_first_token_seconds": 0.5,
               "median_time_to_first_answer_token": 0 if i == 0 else 1.5,   # 0 = not measured -> gap
               "median_output_tokens_per_second": 100,
               "evaluations": {"artificial_analysis_intelligence_index": 40 + i, "lcr": 0.5}}
        aa["data"].append(rec)
        md = m.get("models_dev")
        if md and i != 1:  # model 1 has no models.dev entry -> OpenRouter fallback
            models_dev.setdefault(md["provider"], {"models": {}})["models"][md["model"]] = {"limit": {"context": 200000}}
    openrouter = {"data": [{"id": m["openrouter_id"], "context_length": 128000} for m in SOURCES if m.get("openrouter_id")]}
    return {"/aa": aa, "/models.dev": models_dev, "/openrouter": openrouter}


@pytest.fixture
def fake_sources(monkeypatch, tmp_path):
    payloads = _fake_payloads()
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("x-api-key")))
            body = payloads.get(self.path)
            self.send_response(200 if body is not None else 503)
            self.end_headers()
            self.wfile.write(json.dumps(body).encode() if body is not None else b"down")

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("ARTIFICIAL_ANALYSIS_API_URL", base + "/aa")
    monkeypatch.setenv("MODELS_DEV_API_URL", base + "/models.dev")
    monkeypatch.setenv("OPENROUTER_API_URL", base + "/openrouter")
    monkeypatch.setenv("ARTIFICIAL_ANALYSIS_API_KEY", "test-key")
    monkeypatch.setenv("BENCHMARK_SNAPSHOT_DB", str(tmp_path / "snapshots.sqlite3"))
    monkeypatch.setenv("BENCHMARK_SOURCE", "api")
    yield {"base": base, "seen": seen, "payloads": payloads}
    server.shutdown()


def test_pull_builds_one_sourced_candidate_per_catalog_model(fake_sources):
    result = f7.refresh_model_data()
    assert result["status"] == "ok"
    assert result["candidates"] == len(SOURCES) >= 10  # SR 1.2.1
    served = f7.provide_model_data(data_request={"models": "all", "metrics": []})
    assert [c["model_id"] for c in served] == [m["model_id"] for m in SOURCES]
    for c in served:  # SR 1.1.2, SR 2.3.2 -- every figure has a source and a date
        for field in ("input_price", "output_price", "context_window"):
            fig = c[field]
            assert fig["source_id"].startswith(fake_sources["base"]) and fig["collection_date"] == result["pulled_at"][:10]
        for b in c["benchmarks"]:
            assert b["score"]["source_id"] and b["score"]["collection_date"]
    # one request per source, the key only on the Artificial Analysis request
    assert sorted(p for p, _ in fake_sources["seen"]) == ["/aa", "/models.dev", "/openrouter"]
    assert dict(fake_sources["seen"])["/aa"] == "test-key"
    assert dict(fake_sources["seen"])["/models.dev"] is None


def test_missing_values_become_gaps_and_fallback_fills_context(fake_sources):
    result = f7.refresh_model_data()
    served = {c["model_id"]: c for c in f7.provide_model_data(data_request={"models": "all", "metrics": []})}
    first, second = SOURCES[0]["model_id"], SOURCES[1]["model_id"]
    # benchmark_map.json missing_values: 0 = not measured -> left out, recorded as a gap
    assert "time_to_first_answer_token_seconds" not in {b["benchmark_id"] for b in served[first]["benchmarks"]}
    assert {"model_id": first, "field": "benchmark:time_to_first_answer_token_seconds"}.items() <= \
        next(g for g in result["gaps"] if g["model_id"] == first and g["field"].endswith("answer_token_seconds")).items()
    # SPEC section 2 -- no models.dev entry -> OpenRouter's context length
    assert served[second]["context_window"]["value"] == 128000
    assert served[second]["context_window"]["source_id"].endswith("/openrouter")
    # lcr is scaled x100 to % (benchmark_map.json)
    lcr = next(b for b in served[first]["benchmarks"] if b["benchmark_id"] == "aa_lcr_v1_1_percent")
    assert lcr["score"]["value"] == 50


def test_source_unavailable_keeps_last_snapshot(fake_sources, monkeypatch):
    assert f7.refresh_model_data()["status"] == "ok"
    before = f7.provide_model_data(data_request={"models": "all", "metrics": []})
    monkeypatch.setenv("ARTIFICIAL_ANALYSIS_API_URL", fake_sources["base"] + "/down")
    result = f7.refresh_model_data()
    assert result["status"] == "source_unavailable"  # SR 1.3.3
    assert f7.provide_model_data(data_request={"models": "all", "metrics": []}) == before


def test_schema_rejects_a_figure_without_source(fake_sources):
    # SR 1.1.2 -- the database itself refuses a figure with no source_id (snapshot_schema.sql)
    import sqlite3
    f7.refresh_model_data()
    conn = sqlite3.connect(f7._snapshot_db())
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO figures VALUES (1, ?, 'x', '1', 'u', '', '2026-11-03')", (SOURCES[0]["model_id"],))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO figures VALUES (1, ?, 'y', '1', 'u', 'src', 'not-a-date')", (SOURCES[0]["model_id"],))
    conn.close()


def test_pull_with_no_usable_candidate_keeps_last_snapshot(fake_sources, monkeypatch):
    # SR 1.3.3 -- both context sources down: no candidate has every required field, so the
    # pull is source_unavailable and the last good snapshot is still served (verifier defect 1)
    assert f7.refresh_model_data()["status"] == "ok"
    before = f7.provide_model_data(data_request={"models": "all", "metrics": []})
    monkeypatch.setenv("MODELS_DEV_API_URL", fake_sources["base"] + "/down")
    monkeypatch.setenv("OPENROUTER_API_URL", fake_sources["base"] + "/down")
    result = f7.refresh_model_data()
    assert result["status"] == "source_unavailable" and result["candidates"] == 0
    assert any(g["field"] == "context_window" for g in result["gaps"])
    assert f7.provide_model_data(data_request={"models": "all", "metrics": []}) == before


def test_response_with_no_model_records_is_source_unavailable(fake_sources):
    fake_sources["payloads"]["/aa"] = {"status": 200, "data": []}
    result = f7.refresh_model_data()
    assert result["status"] == "source_unavailable"
    assert f7.provide_model_data(data_request={"models": "all", "metrics": []}) == []  # nothing stored yet


def test_required_field_missing_leaves_model_out_with_gap(fake_sources):
    # SPEC section 2 -- a required figure is never filled in: the model is left out and the gap recorded
    first = SOURCES[0]
    rec = next(r for r in fake_sources["payloads"]["/aa"]["data"] if r["id"] == first["artificial_analysis_id"])
    rec["pricing"]["price_1m_input_tokens"] = None
    result = f7.refresh_model_data()
    served = [c["model_id"] for c in f7.provide_model_data(data_request={"models": "all", "metrics": []})]
    assert first["model_id"] not in served and len(served) == len(SOURCES) - 1
    assert any(g["model_id"] == first["model_id"] and "input_price" in g["field"] for g in result["gaps"])


def test_unsourced_manual_entry_is_rejected_not_stored(fake_sources, monkeypatch):
    # SR 1.1.2 -- a manual figure with no source_id is rejected at entry; the rest of the pull goes ahead
    real = json.loads((f7.SAMPLE_DATA / "manual_entries.json").read_text())
    first = SOURCES[0]["model_id"]
    real["models"].setdefault(first, {})["data_retention"] = {"value": 30, "unit": "days", "collection_date": "2026-10-05"}
    original_loads = f7.json.loads

    def loads(text, *a, **k):
        data = original_loads(text, *a, **k)
        return real if isinstance(data, dict) and "researched" in data and "models" in data else data

    monkeypatch.setattr(f7.json, "loads", loads)
    result = f7.refresh_model_data()
    monkeypatch.setattr(f7.json, "loads", original_loads)
    assert result["status"] == "ok"
    served = {c["model_id"]: c for c in f7.provide_model_data(data_request={"models": "all", "metrics": []})}
    assert "data_retention" not in served[first]
    assert any(g["model_id"] == first and g["field"] == "data_retention" for g in result["gaps"])


# --- C.8 adapter failure paths the SR 2.3.1 cases don't cover (verifier defect 2) ---

import provide_requirement_interpretation as f8


@pytest.fixture
def fake_runtime(monkeypatch):
    replies = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            status, body = replies["next"]
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("LLM_RUNTIME_URL", f"http://127.0.0.1:{server.server_port}/v1")
    yield replies
    server.shutdown()


@pytest.mark.parametrize("status,body", [
    (500, b'{"error": "model crashed"}'),           # runtime HTTP error
    (200, b'{"id": "x", "object": "chat.completion"}'),  # reply without choices
    (200, b'{"choices": [{"message": {"content": null}}]}'),  # empty content
])
def test_runtime_error_or_malformed_reply_returns_none(fake_runtime, status, body):
    # SR 1.3.2 -- handled like an invalid response: None, so F.1.1 retries then marks interpretation_failed
    fake_runtime["next"] = (status, body)
    assert f8.propose_criteria(interpretation_request={"requirement_id": "R1", "text": "Respond quickly."}) is None
