from __future__ import annotations

from ..adapters.base import LLMProvider, SearchProvider
from ..models import CheckStatus, ChecklistItemResult
from ..prompts import VERIFICATION_SYSTEM, VERIFICATION_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


def _format_results(results: list[dict]) -> str:
    if not results:
        return "(no search results returned)"
    return "\n".join(f"- {r.get('title', '')} ({r.get('url', '')}): {r.get('snippet', '')}" for r in results)


async def verify_item(
    llm: LLMProvider,
    search: SearchProvider,
    result: ChecklistItemResult,
    confidence_threshold: float,
) -> ChecklistItemResult:
    """For a checklist item marked needs_verification, corroborate (or
    contest) it via web search rather than trusting the output-only
    evaluation alone. Only meaningfully runs anything if there's an
    evidence excerpt to check and a real search provider is configured —
    otherwise this is a no-op that returns the result unchanged."""

    if not result.item.needs_verification:
        return result
    if not result.evidence_excerpt:
        # Nothing concrete to check (e.g. already not_satisfied with no
        # excerpt) — web search wouldn't have anything to verify against.
        return result

    query = f"{result.item.description}: {result.evidence_excerpt}"
    search_results = await search.search(query, max_results=5)

    if not search_results:
        # No search results — leave the output-only verdict as-is, but note
        # that verification was attempted and inconclusive for lack of data.
        note = "Web verification attempted but returned no results; status reflects output-only evaluation."
        return result.model_copy(update={"verification_note": note})

    prompt = VERIFICATION_USER_TEMPLATE.format(
        item_description=result.item.description,
        evidence_excerpt=result.evidence_excerpt,
        results_block=_format_results(search_results),
    )
    raw = await llm.complete(VERIFICATION_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        return result.model_copy(
            update={"verification_note": "Web verification response could not be parsed; status reflects output-only evaluation."}
        )

    verdict = parsed.get("verdict", "inconclusive")
    confidence = float(parsed.get("confidence", 0.0) or 0.0)
    explanation = parsed.get("explanation", "")

    if confidence < confidence_threshold or verdict == "inconclusive":
        return result.model_copy(
            update={"verification_note": f"Web verification inconclusive: {explanation}".strip()}
        )

    if verdict == "outdated_or_wrong":
        return result.model_copy(
            update={
                "status": CheckStatus.NOT_SATISFIED,
                "verification_note": f"Web verification found this to be outdated or incorrect: {explanation}".strip(),
            }
        )

    # verdict == "confirmed"
    return result.model_copy(
        update={"verification_note": f"Web verification confirmed: {explanation}".strip()}
    )
