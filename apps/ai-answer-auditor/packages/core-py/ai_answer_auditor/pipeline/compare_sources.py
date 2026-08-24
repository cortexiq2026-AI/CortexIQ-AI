from __future__ import annotations

from ..adapters.base import LLMProvider
from ..models import Claim, Evidence, SourceDocument
from ..prompts import SOURCE_COMPARISON_SYSTEM, SOURCE_COMPARISON_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


def _format_sources(sources: list[SourceDocument]) -> str:
    blocks = []
    for s in sources:
        label = s.title or s.id
        # Truncate very long documents to keep prompt size sane; a production
        # deployment would chunk + retrieve relevant passages instead.
        text = s.text if len(s.text) <= 6000 else s.text[:6000] + " [...truncated...]"
        blocks.append(f'[source id="{s.id}"] {label}\n{text}')
    return "\n\n---\n\n".join(blocks) if blocks else "(no source documents supplied)"


async def compare_against_sources(
    llm: LLMProvider,
    claim: Claim,
    sources: list[SourceDocument],
) -> tuple[str, float, list[Evidence]]:
    """Returns (verdict, confidence, evidence_list). verdict is one of
    'supports' | 'contradicts' | 'no_evidence'."""

    if not sources:
        return "no_evidence", 0.0, []

    prompt = SOURCE_COMPARISON_USER_TEMPLATE.format(
        claim_text=claim.text, sources_block=_format_sources(sources)
    )
    raw = await llm.complete(SOURCE_COMPARISON_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        return "no_evidence", 0.0, []

    verdict = parsed.get("verdict", "no_evidence")
    confidence = float(parsed.get("confidence", 0.0) or 0.0)
    excerpt = parsed.get("best_excerpt", "") or ""
    source_id = parsed.get("source_id", "") or ""

    evidence: list[Evidence] = []
    if excerpt and verdict in ("supports", "contradicts"):
        evidence.append(
            Evidence(
                origin=f"source:{source_id}" if source_id else "source:unknown",
                excerpt=excerpt,
                supports=(verdict == "supports"),
                note=parsed.get("explanation"),
            )
        )

    return verdict, confidence, evidence
