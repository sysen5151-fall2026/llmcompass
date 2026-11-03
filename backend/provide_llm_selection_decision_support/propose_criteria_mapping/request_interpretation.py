"""Implements F.1.1.1 -- Request Interpretation. Mechanism: C.1.1.1 Interpretation Client."""

import logging
import re
from typing import Optional
from urllib.parse import urlsplit

_log = logging.getLogger(__name__)

# A list marker in front of a stated requirement ("- ", "* ", "1. ", "2) ") is layout, not text (A30).
_LIST_MARKER = re.compile(r"^(?:[-*•]|\d+[.)])\s+")
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _split_stated_requirements(stated_requirements: str) -> list:
    # A30: the model does not fix how the text is divided. One non-blank line = one stated
    # requirement; leading list markers and surrounding whitespace are dropped, the rest is kept as typed.
    texts = []
    for line in stated_requirements.splitlines():
        text = _LIST_MARKER.sub("", line.strip()).strip()
        if text:
            texts.append(text)
    return texts


def request_interpretation(stated_requirements: str) -> tuple[list, list]:
    """operationId: requestInterpretation. F.1.1.1 -> runtime (flow 2), F.1.1.2 and F.1.1.4 (flow 1.0.1).

    in: stated_requirements. control: -. out: interpretation_requests, requirement_set.
    raises: ValueError when the stated requirements are not text or are empty.
    """
    # CR 1.1.4 Accept Stated requirements (SR 1.1.5): text from the Technical Lead, never empty.
    if not isinstance(stated_requirements, str):
        raise ValueError("stated requirements must be text (CR 1.1.4)")
    texts = _split_stated_requirements(stated_requirements)
    if not texts:
        raise ValueError("stated requirements are empty (CR 1.1.4)")

    # CR 1.4.1 Request Interpretation (SR 1.4.1.1): assign an identifier to each stated requirement.
    # Identifiers are positional (REQ-1, REQ-2, ...), so the same text always gives the same set.
    requirement_set = [{"requirement_id": f"REQ-{n}", "text": text} for n, text in enumerate(texts, start=1)]

    # CR 1.2.3 Provide Interpretation request (SR 1.2.3) and CR 2.3.1 Model contract (SR 2.3.1):
    # one SPEC 3 request per requirement, exactly {requirement_id, text}, text unaltered.
    interpretation_requests = [{"requirement_id": r["requirement_id"], "text": r["text"]} for r in requirement_set]
    for request in interpretation_requests:
        _log.info("interpretation request %s: %r", request["requirement_id"], request["text"])  # CR 1.2.3 request log
    return interpretation_requests, requirement_set


def send_interpretation_request(interpretation_request: dict) -> Optional[dict]:
    """Send one interpretation request (flow 2) to the language model runtime; return its response (flow 3).

    C.1.1.1 is the only component that calls the runtime (SPEC 7), so this is the single call site.
    Returns the parsed SPEC 3 response, or None on timeout / unreachable runtime / non-JSON reply;
    the response is unchecked here -- C.1.1.2 validates it.
    raises: ValueError when the request is not in SPEC 3 form or the runtime is not local.
    """
    # CR 2.3.1 Model contract (SR 2.3.1) / CR 1.3.7: send only the SPEC 3 request form.
    if (not isinstance(interpretation_request, dict) or set(interpretation_request) != {"requirement_id", "text"}
            or not all(isinstance(interpretation_request[k], str) and interpretation_request[k]
                       for k in ("requirement_id", "text"))):
        raise ValueError("interpretation request must be exactly {requirement_id, text}, non-empty strings (SPEC 3)")

    # STUB: Language model runtime -- reached only through the F.8 adapter (Lab Manual 8.5).
    from provide_requirement_interpretation import propose_criteria, runtime_config

    # CR 2.2.1 Local interpretation (SR 2.2.1) and CR 2.4.1 Query cost (SR 2.4.1): a locally hosted
    # runtime only, so no request leaves the machine and none is paid for. Checked before sending.
    host = urlsplit(runtime_config()["base_url"]).hostname
    if host not in _LOCAL_HOSTS:
        raise ValueError(f"language model runtime host {host!r} is not local (CR 2.2.1)")

    _log.info("sending interpretation request %s", interpretation_request["requirement_id"])  # CR 1.2.3 request log
    # CR 1.1.3 Accept Proposed criteria (SR 1.1.4): the response is handed on as received.
    return propose_criteria(interpretation_request=dict(interpretation_request))
