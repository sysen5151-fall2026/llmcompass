"""Lab Manual 10.4 submission files from tools/measure_uc1.py output (SR 1.3.2, SR 2.1.1; tooling only).

Writes into the runs dir:
  per_run.csv                 one row per run (warm-up marked), per-stage seconds
  interpretation_log.csv      one row per interpretation request: run_id, requirement_id, seconds, outcome
  CONTEXT.md                  model, machine, date, commit, scenario, observations, instrumentation paths
Outcome rule (from the call count per requirement; C.1.1.2 re-sends once on an invalid reply, ADR-0006):
  1 call  -> valid;  2 calls -> first "invalid (re-sent)", second "valid or interpretation_failed (see review)".
"""
import csv
import json
import platform
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/validation/measured-behavior"
rows = list(csv.DictReader(open(OUT / "runs.csv")))
meta = json.loads((OUT / "runs_meta.json").read_text())
per_meta = {r["run_id"]: r for r in meta.get("per_run", [])}

by_run = defaultdict(lambda: defaultdict(float))
start = {}
calls = defaultdict(list)
for r in rows:
    rid = int(r["run_id"])
    by_run[rid][r["stage_id"]] += float(r["duration_s"])
    start.setdefault(rid, r["t_entry_wall"])
    if r["stage_id"] == "UC.1.4":
        calls[(rid, r["requirement_id"])].append(r)

STAGES = ["UC.1.3", "UC.1.4", "UC.1.5", "UC.1.6a", "UC.1.6b", "C.1.1.4", "UC.1.10", "UC.1.11",
          "F.1.2-receive", "UC.1.12", "UC.1.13", "UC.1.14", "UC.1.15-16a", "UC.1.15-16b", "UC.1.18"]
with open(OUT / "per_run.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["run_id", "phase", "start_utc", "n_requirements", "n_interpretation_calls",
                "http_post_review", "http_post_confirm", "record_stored", "request_wall_s",
                "system_total_s"] + [f"{s}_s" for s in STAGES])
    for rid in sorted(by_run, key=lambda x: (x > 0, abs(x))):
        st, m = by_run[rid], per_meta.get(rid, {})
        n_calls = sum(len(v) for (r, _), v in calls.items() if r == rid)
        w.writerow([rid, "warmup" if rid < 0 else "measured", start[rid], m.get("n_requirements"), n_calls,
                    m.get("status_post"), m.get("status_confirm"), m.get("record_stored"),
                    f"{st['REQ:POST /'] + st['REQ:POST /confirm']:.6f}",
                    f"{sum(st[s] for s in STAGES):.6f}"] + [f"{st[s]:.6f}" for s in STAGES])

with open(OUT / "interpretation_log.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["run_id", "phase", "requirement_id", "attempt", "seconds", "outcome", "t_entry_utc"])
    for (rid, req), cs in sorted(calls.items(), key=lambda k: ((k[0][0] > 0, abs(k[0][0])), k[0][1])):
        for i, c in enumerate(cs):
            if c["ok"] not in ("1", "true", "True"):
                outcome = f"error ({c['error']})"
            elif len(cs) == 1:
                outcome = "valid"
            elif i < len(cs) - 1:
                outcome = "invalid (re-sent)"
            else:
                outcome = "retried: valid or interpretation_failed"
            w.writerow([rid, c["phase"], req, i + 1, c["duration_s"], outcome, c["t_entry_wall"]])

measured = [r for r in by_run if r > 0]
warm = [r for r in by_run if r < 0]
interp = sorted(by_run[r]["UC.1.4"] for r in measured)
retried = sum(1 for (r, _), v in calls.items() if r > 0 and len(v) > 1)
mem = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip()
cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
n = len(interp)
lines = [
    "# Lab 10.4 measured runs: context",
    "",
    f"- Runs: {n} measured + {len(warm)} warm-up (warm-up excluded from statistics). Target: 30.",
    f"- Date (UTC): {meta.get('start_wall')} to {meta.get('end_wall')}",
    f"- Language model: {meta.get('llm_model')} (LM Studio, GGUF Q4_K_M, lmstudio-community Qwen2.5-7B-Instruct-1M), "
    f"local endpoint {meta.get('llm_runtime_url')}. This build is now the pinned model identifier (ADR-0009, docs/deployment.md).",
    f"- Machine: {cpu}, {int(mem) // 2**30 if mem.isdigit() else '?'} GB RAM, macOS {platform.mac_ver()[0]}, "
    f"Python {meta.get('python')}.",
    f"- App version: commit {meta.get('git_commit')} plus uncommitted: {', '.join(meta.get('git_dirty_paths') or []) or 'none'} "
    "(includes the D-29 criterion-id fix, ADR-0008).",
    "- Scenario: 5 stated requirements, the sentences of sample SCENARIO_03 and SCENARIO_04 verbatim "
    "(sample_data/user_inputs.json), same text every run. Technical Lead accepts the review page defaults.",
    f"- Benchmark data: BENCHMARK_SOURCE={meta.get('benchmark_source')}, read from the stored snapshot "
    f"{meta.get('snapshot_db')} (pulled {meta.get('snapshot_db_mtime')}), not the live source: F.7 in api mode "
    "serves the last pull between refreshes (SPEC section 2 'Refresh').",
    "",
    "## Observations",
    "",
    f"- Interpretation (UC.1.4, 5 requests per run): median {statistics.median(interp):.2f} s, min {interp[0]:.1f} s, "
    f"max {interp[-1]:.1f} s per run (simulated N(90, 25))." if n else "- No measured runs yet.",
    f"- Retries: {retried} requirement(s) re-sent after an invalid reply; timeouts/errors: "
    f"{sum(1 for v in calls.values() for c in v if c['ok'] not in ('1', 'true', 'True'))}.",
    f"- Warm-up run interpretation: {by_run[warm[0]]['UC.1.4']:.1f} s (model already loaded in LM Studio before "
    "the run, so no load delay was measured)." if warm else "",
    "- Before measuring, the smoke run found Confirm failing with HTTP 422 on multi-line requirements "
    "(criterion ids repeated across requirements, deviation log D-29); fixed before the 30 runs (ADR-0008).",
    "",
    "## Proof of instrumentation",
    "",
    "- Timers: `tools/measure_uc1.py` wraps every sequence-diagram boundary (UC.1.3-UC.1.18, C.1<->C.8, "
    "C.1<->C.7, C.1->Technical Lead) with entry/exit `perf_counter_ns` timestamps; product code unchanged.",
    "- Run command: `LLM_MODEL=qwen2.5-7b-instruct-1m .venv/bin/python tools/measure_uc1.py --runs 30 --warmup 1`",
    "- Raw data: `runs.csv` (one row per stage call), `runs_meta.json`; derived: `per_run.csv`, "
    "`interpretation_log.csv` (this script: `tools/export_submission.py`).",
]
(OUT / "CONTEXT.md").write_text("\n".join(l for l in lines if l is not None) + "\n")
print((OUT / "CONTEXT.md").read_text())
print(f"per_run.csv rows: {len(by_run)}; interpretation_log.csv rows: {sum(len(v) for v in calls.values())}")
