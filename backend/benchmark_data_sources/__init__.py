# STUB: Benchmark Data Sources
# Loads the manually entered model, provider and benchmark data from sample_data/.

import json
from pathlib import Path

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"


def request_model_data(confirmed_mapping: dict) -> dict:
    # UC.1.10, UC.1.11 -- call and return are the same function call (SN-TL-02 / 5.1.2.1)
    return {
        "models": json.loads((SAMPLE_DATA / "model_spec.json").read_text()),
        "providers": json.loads((SAMPLE_DATA / "providers.json").read_text()),
        "benchmark": json.loads((SAMPLE_DATA / "benchmark.json").read_text()),
    }
