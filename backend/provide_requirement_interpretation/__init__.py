# Model adapter for C.8 Language model runtime (Lab Manual 8.5): LM Studio, local only
# (ADR-0001, SR 2.2.1). The prompt template, parameters, timeout, token limit, response
# schema and failure behaviour are specified in SPEC section 3 "Adapter".
"""Implements F.8 -- Provide Requirement Interpretation. Mechanism: C.8 Language model runtime."""

import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"
EXPECTED_OUTPUTS = SAMPLE_DATA / "expected_outputs.json"
PROMPT_TEMPLATE = Path(__file__).with_name("prompt_template.txt")

# SPEC section 3 "Adapter" -- defaults; LLM_RUNTIME_URL and LLM_MODEL come from .env.
DEFAULT_RUNTIME_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "qwen2.5-7b-instruct"
TIMEOUT_S = 110.0      # provisional: about 3x the slowest measured call, 36.3 s (SPEC section 3, SR 1.3.2)
MAX_TOKENS = 512       # provisional: about 3x the largest measured reply, 165 tokens (SPEC section 3)
TEMPERATURE = 0        # SR 2.1.3 -- repeatable interpretation for the same text
SEED = 5151
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")  # SR 2.2.1, SR 2.4.1 -- no data leaves the machine

# SPEC section 2 figure fields and their units: the metric vocabulary the model may use (SPEC section 3).
FIGURE_UNITS = {
    "input_price": "USD per 1M input tokens",
    "output_price": "USD per 1M output tokens",
    "context_window": "tokens",
    "latency_p50": "seconds",
    "data_residency": "country codes (ISO 3166-1 alpha-2)",
    "data_retention": "days",
    "deprecation_date": "date",
}

# SPEC section 3 response, as the JSON schema sent to the runtime (structured output).
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "requirement_id": {"type": "string"},
        "no_suitable_proxy": {"type": "boolean"},
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion_id": {"type": "string"},
                    "metric": {"type": "string"},
                    "operator": {"type": "string", "enum": [">=", "<=", "==", "in"]},
                    "threshold": {"type": ["number", "string", "array", "null"], "items": {"type": "string"}},
                    "unit": {"type": "string"},
                    "proxy_strength": {"type": "string", "enum": ["strong", "moderate", "weak"]},
                    "category": {"type": "string", "enum": ["capability", "cost", "compliance", "other"]},
                    "rationale": {"type": "string"},
                },
                "required": ["criterion_id", "metric", "operator", "threshold", "unit",
                             "proxy_strength", "category", "rationale"],
            },
        },
    },
    "required": ["requirement_id", "no_suitable_proxy", "criteria"],
}


def runtime_config() -> dict:
    # SPEC section 3 "Adapter" -- everything the adapter sends with, in one place (SR 2.2.1: I)
    return {
        "base_url": os.environ.get("LLM_RUNTIME_URL") or DEFAULT_RUNTIME_URL,
        "model": os.environ.get("LLM_MODEL") or DEFAULT_MODEL,
        "timeout_s": TIMEOUT_S,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "seed": SEED,
    }


def _metric_list() -> str:
    # Known benchmark ids come from the benchmark map data file (SPEC 5 Q7), not from F.7's code.
    benchmarks = json.loads((SAMPLE_DATA / "benchmark_map.json").read_text())["benchmarks"]
    lines = [f"- {name} ({unit})" for name, unit in FIGURE_UNITS.items()]
    lines += [f"- {bid} ({b['unit']}, benchmark)" for bid, b in benchmarks.items()]
    return "\n".join(lines)


def build_prompt(interpretation_request: dict) -> str:
    # SPEC section 3 "Adapter" -- the prompt template the product sends
    return PROMPT_TEMPLATE.read_text().format(metrics=_metric_list(),
                                              requirement_id=interpretation_request["requirement_id"],
                                              text=interpretation_request["text"])


def _check_local(base_url: str) -> None:
    # SR 2.2.1 (local interpretation), SR 2.4.1 (no paid per-query charges): refuse before sending
    host = urlparse(base_url).hostname
    if host not in LOCAL_HOSTS:
        raise ValueError(f"LLM_RUNTIME_URL must point to a local runtime, not {host!r} (SR 2.2.1)")


def propose_criteria(*, interpretation_request: dict) -> Optional[dict]:
    """Function: F.8 -- Provide Requirement Interpretation. Signature from Chapter 4; body added in Lab Manual 8.5.

    control: interpretation_request. out: proposed_criteria.
    Returns the parsed SPEC section 3 response, or None when the runtime times out, can't
    be reached, or doesn't return a JSON object. F.1.1 validates the schema rules and
    retries once (SR 1.3.2, SR 1.1.4).
    """
    # UC.1.3, UC.1.4 (SR 1.2.3, SR 1.1.4, SR 1.3.2, SR 2.3.1; SN-TL-01 / 5.1.1.2)
    config = runtime_config()
    _check_local(config["base_url"])
    body = {
        "model": config["model"],
        "messages": [{"role": "user", "content": build_prompt(interpretation_request)}],
        "temperature": config["temperature"],
        "seed": config["seed"],
        "max_tokens": config["max_tokens"],
        "stream": False,
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "proposed_criteria", "strict": True, "schema": RESPONSE_SCHEMA}},
    }
    request = urllib.request.Request(config["base_url"].rstrip("/") + "/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=config["timeout_s"]) as response:
            reply = json.loads(response.read().decode("utf-8"))
        content = reply["choices"][0]["message"]["content"]
        proposed = json.loads(content)
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError):
        # SR 1.3.2 -- a timeout, an unreachable runtime or a non-JSON reply is handled like an
        # invalid response: F.1.1 retries once, then marks interpretation_failed. No criteria are made up.
        return None
    return proposed if isinstance(proposed, dict) else None


def submit_requirements(requirements: dict) -> dict:
    # SPEC section 4 -- {"requirement_id", "text"} -> model contract response (SN-TL-01 / 5.1.1.2)
    proposed = propose_criteria(interpretation_request={"requirement_id": requirements["requirement_id"],
                                                        "text": requirements["text"]})
    if proposed is None:  # no response: an empty, invalid response (the validator rejects it)
        return {"requirement_id": requirements["requirement_id"], "no_suitable_proxy": False, "criteria": []}
    return proposed


def scenario_interpretation(requirements: dict) -> dict:
    # STUB: Language model runtime -- the walking-skeleton UI path still shows the scenario's
    # stored interpretation until the UI calls the F.1 ICOM defs (SR 1.3.1, docs/route-table.md).
    # UC.1.3, UC.1.4 (SN-TL-01 / 5.1.1.2)
    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == requirements["scenario_id"])
    return {
        "scenario_id": requirements["scenario_id"],
        "interpreted_requirements": scenario["interpreted_requirements"],
    }
