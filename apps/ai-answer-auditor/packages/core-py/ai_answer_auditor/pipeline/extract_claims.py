from __future__ import annotations

import uuid

from ..adapters.base import LLMProvider
from ..models import Claim, ClaimType, EvidenceRequirement
from ..prompts import CLAIM_EXTRACTION_SYSTEM, CLAIM_EXTRACTION_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


async def extract_claims(
    llm: LLMProvider,
    answer: str,
    question: str | None,
    max_claims: int,
) -> list[Claim]:
    """Stage 1 & 2 combined: decompose the answer into atomic claims and tag
    each with a type and evidence requirement in a single LLM call."""

    question_clause = f' (written in response to the question: "{question}")' if question else ""
    prompt = CLAIM_EXTRACTION_USER_TEMPLATE.format(
        answer=answer, question_clause=question_clause, max_claims=max_claims
    )

    raw = await llm.complete(CLAIM_EXTRACTION_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        # Fail safe rather than fail loud: an audit with zero claims and a
        # low completeness score is more useful downstream than a crash.
        return []

    claims: list[Claim] = []
    for item in parsed.get("claims", [])[:max_claims]:
        try:
            claims.append(
                Claim(
                    id=str(uuid.uuid4())[:8],
                    text=item["text"],
                    claim_type=ClaimType(item.get("claim_type", "factual")),
                    evidence_requirement=EvidenceRequirement(item.get("evidence_requirement", "required")),
                    source_span=item.get("source_span"),
                )
            )
        except (KeyError, ValueError):
            # Skip malformed individual claims rather than discarding the whole batch.
            continue

    return claims
