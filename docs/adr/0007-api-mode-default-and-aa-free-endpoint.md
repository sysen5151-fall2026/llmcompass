# ADR-0007: Api mode is the default; Artificial Analysis free-tier endpoint

Status: Accepted (team, 2026-11-10)

Context:
- F.7 had two modes (SPEC §2). `file` is increment 1: a hand-entered catalog of 3
  models in `sample_data/`. `api` is increment 2: the last snapshot of an on-demand
  pull of the 14 catalog models in `sample_data/model_sources.json`.
- `file` was the default, so CI and the app used the 3-model prototype catalog, and
  SR 1.2.1 ("a catalog of at least 10 candidates") failed in CI.
- Artificial Analysis retired `/api/v2/data/llms/models` on 2026-11-04 (HTTP 410).
  Its replacement is `/api/v2/language/models` (Pro) or
  `/api/v2/language/models/free` (free tier, paged, 200 records a page). Our key is
  free tier. All 14 catalog ids are on it, unchanged (checked 2026-11-10).

Decision:
- `api` is the default mode (`BENCHMARK_SOURCE` empty or unset). `file` stays for the
  tests that ask for it by name.
- F.7 pulls from `/api/v2/language/models/free` and reads every page.
- Field paths move in the data files, not the code: latency and speed are now under
  `performance.` (`source_fields.json`, `benchmark_map.json`).
- `aa_lcr_v1_1_percent` is not published on the free tier. In api mode it is a
  recorded gap ("not published by the API"), like `aa_omniscience_index`. It is never
  filled in.
- Tests read one frozen live pull, `tests/fixtures/benchmark_snapshot.json`, which
  `tests/conftest.py` loads into a temporary snapshot database for each test. CI makes
  no network call and needs no key.

Consequences:
- SR 1.2.1 passes in CI on the 14-model catalog.
- A long-context criterion has no benchmark in api mode until LCR comes back (Pro
  tier or another source). A weighted criterion on it scores 0, and a hard one
  excludes the model with missing_data.
- The fixture's figures go stale 90 days after 2026-11-10 (SR 1.1.6). Refresh it by
  running a pull and re-exporting it.
- `tests/test_data_access_component.py`'s fake source now answers in the new shape,
  and its LCR check became a gap check (team, 2026-11-10).
