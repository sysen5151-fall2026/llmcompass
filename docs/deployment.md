# Deployment view (Lab Manual 8.5)

What runs where and what talks to what in increment 2. The components are the
physical elements of the Design Definition: Form report (form_architecture_definition.pdf,
Tables 1, 3, 5 and 6). The runtime choice is the provisional baseline from its Pugh chart
(Table 8, Option 1) and ADR-0001. Storage is ADR-0005.

## Where each part runs

Everything runs on one team laptop. Nothing is deployed to Netlify yet: a local
runtime can't be reached from a hosted app (Form report §2.3, ADR-0001 revisit
condition).

| Process | What it is | Started by | Listens on |
|---|---|---|---|
| Flask app | C.1 LLM Compass: `backend/app.py`, the F.1 package `backend/provide_llm_selection_decision_support/` (C.1.1-C.1.7) | `cd backend && ../.venv/bin/python app.py` (set up once: `python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt`) | `127.0.0.1:5000` |
| LM Studio (Bionic app) | C.8 Language model runtime, model Qwen2.5 7B Instruct (GGUF Q4_K_S) | Bionic app → Developer → start server, or `~/.lmstudio/bin/lms server start` | `127.0.0.1:1234` (OpenAI-compatible `/v1`) |
| On-demand pull | Part of C.7's data access in `backend/provide_benchmark_evidence/` | `cd backend && python3 -m provide_benchmark_evidence refresh` | — (one-shot) |
| pytest / CI | Verification tooling, not part of the product | `pytest`; GitHub Actions `.github/workflows/ci.yml` | — |

## What talks to what

```
 Technical Lead (browser)
        │  HTTP, 127.0.0.1:5000        conduit "Requirements and recommendations" (Table 5)
        ▼
 C.1 LLM Compass  (Flask, F.1 package C.1.1–C.1.7)
   │
   │ C.1.1.1 Interpretation Client ──► backend/provide_requirement_interpretation (C.8 adapter)
   │                                     │ HTTP POST /v1/chat/completions, localhost only
   │                                     ▼
   │                                  LM Studio, 127.0.0.1:1234           conduit "Interpretation request
   │                                                                       and proposed criteria"
   │ C.1.2 Evidence Retriever ───────► backend/provide_benchmark_evidence (C.7 data access)
   │                                     │ file mode: sample_data/*.json (default; tests)
   │                                     │ api mode:  data/benchmark_snapshots.sqlite3
   │                                     │ refresh:   HTTPS GET, on demand only:     conduit "Data request and
   │                                     │   artificialanalysis.ai  (API key, .env)  model data with provenance"
   │                                     │   models.dev/api.json    (public)
   │                                     │   openrouter.ai          (public model list)
   │
   │ C.1.7 Decision Recorder ────────► data/decision_records/decision_records.sqlite3
```

## Data that leaves the machine (manual front matter, data-security note)

- **To the language model runtime:** the stated requirements text. It goes only to
  LM Studio on localhost. The adapter refuses any other host before sending anything
  (SR 2.2.1, SR 2.4.1).
- **To the data sources:** only GET requests to the configured source URLs (defaults
  in `.env.example`) with a User-Agent header and, for Artificial Analysis, the API key
  header. No requirement text, mapping or decision record is sent. The responses are public
  model listings.
- **Stored on the machine:** snapshots and decision records in `data/` (gitignored).
  `.env` holds the keys and is gitignored.

## Configuration (`.env`, copied from `.env.example`)

| Variable | Default | Used by |
|---|---|---|
| `BENCHMARK_SOURCE` | `file` | C.7: `file` = stored catalog, `api` = latest pulled snapshot |
| `ARTIFICIAL_ANALYSIS_API_KEY` | — | C.7 refresh |
| `ARTIFICIAL_ANALYSIS_API_URL`, `MODELS_DEV_API_URL`, `OPENROUTER_API_URL` | see `.env.example` | C.7 refresh |
| `BENCHMARK_SNAPSHOT_DB` | `data/benchmark_snapshots.sqlite3` | C.7 |
| `LLM_RUNTIME_URL` | `http://127.0.0.1:1234/v1` | C.8 adapter |
| `LLM_MODEL` | `qwen2.5-7b-instruct` | C.8 adapter |
| `DECISION_RECORD_DIR` | `data/decision_records` | C.1.7 |
