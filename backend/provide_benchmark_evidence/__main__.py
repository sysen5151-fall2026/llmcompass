"""On-demand pull for C.7 (SPEC section 2 "Refresh"): cd backend && python3 -m provide_benchmark_evidence refresh

The operator asks for fresh data; otherwise F.7 serves the last snapshot. Traces to UC.1.10/UC.1.11
(SR 1.2.1, SR 1.3.3); listed in docs/route-table.md.
"""

import json
import os
import sys
from pathlib import Path

from provide_benchmark_evidence import refresh_model_data

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_dotenv() -> None:
    # .env (gitignored) holds the API key; values already in the environment win. Never printed.
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            name, sep, value = line.strip().partition("=")
            if sep and name and not name.startswith("#"):
                os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

if __name__ == "__main__":
    if sys.argv[1:] != ["refresh"]:
        sys.exit("usage: python3 -m provide_benchmark_evidence refresh")
    load_dotenv()
    result = refresh_model_data()
    print(json.dumps({k: (len(v) if k == "gaps" else v) for k, v in result.items()}, indent=2))
    sys.exit(0 if result["status"] == "ok" else 1)
