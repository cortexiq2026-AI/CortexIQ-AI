from __future__ import annotations

from ..adapters.base import LLMProvider
from ..models import Claim
from ..prompts import CONTRADICTION_SYSTEM, CONTRADICTION_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


async def find_internal_contradictions(llm: LLMProvider, claims: list[Claim]) -> set[str]:
    """Returns the set of claim ids that participate in at least one
    internal (claim-vs-claim) contradiction."""

    if len(claims) < 2:
        return set()

    claims_block = "\n".join(f'- id="{c.id}": {c.text}' for c in claims)
    prompt = CONTRADICTION_USER_TEMPLATE.format(claims_block=claims_block)
    raw = await llm.complete(CONTRADICTION_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        return set()

    flagged: set[str] = set()
    for pair in parsed.get("contradictions", []):
        a = pair.get("claim_id_a")
        b = pair.get("claim_id_b")
        if a:
            flagged.add(a)
        if b:
            flagged.add(b)
    return flagged
