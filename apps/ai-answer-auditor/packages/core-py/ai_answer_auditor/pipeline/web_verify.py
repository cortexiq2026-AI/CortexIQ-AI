from __future__ import annotations

from ..adapters.base import LLMProvider, SearchProvider
from ..models import Claim, Evidence
from ..prompts import WEB_VERDICT_SYSTEM, WEB_VERDICT_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


def _format_results(results: list[dict]) -> str:
    if not results:
        return "(no search results returned)"
    blocks = []
    for r in results:
        blocks.append(f"- {r.get('title', '')} ({r.get('url', '')}): {r.get('snippet', '')}")
    return "\n".join(blocks)


def _filter_trusted(results: list[dict], trusted_domains: list[str]) -> list[dict]:
    if not trusted_domains:
        return results
    return [r for r in results if any(d in r.get("url", "") for d in trusted_domains)]


async def verify_via_web(
    llm: LLMProvider,
    search: SearchProvider,
    claim: Claim,
    trusted_domains: list[str],
) -> tuple[str, float, list[Evidence]]:
    """Returns (verdict, confidence, evidence_list). verdict is one of
    'supports' | 'contradicts' | 'no_evidence'."""

    results = await search.search(claim.text, max_results=5)
    results = _filter_trusted(results, trusted_domains)

    if not results:
        return "no_evidence", 0.0, []

    prompt = WEB_VERDICT_USER_TEMPLATE.format(claim_text=claim.text, results_block=_format_results(results))
    raw = await llm.complete(WEB_VERDICT_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        return "no_evidence", 0.0, []

    verdict = parsed.get("verdict", "no_evidence")
    confidence = float(parsed.get("confidence", 0.0) or 0.0)
    excerpt = parsed.get("best_excerpt", "") or ""
    source_url = parsed.get("source_url", "") or ""

    evidence: list[Evidence] = []
    if excerpt and verdict in ("supports", "contradicts"):
        evidence.append(
            Evidence(
                origin=f"web:{source_url}" if source_url else "web:unknown",
                excerpt=excerpt,
                supports=(verdict == "supports"),
                note=parsed.get("explanation"),
            )
        )

    return verdict, confidence, evidence
