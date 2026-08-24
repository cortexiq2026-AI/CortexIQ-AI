from __future__ import annotations

from ..adapters.base import LLMProvider
from ..models import ExpectedTopic, QualityRating, QUALITY_TO_STATUS, TopicCoverage
from ..prompts import COVERAGE_ANALYSIS_SYSTEM, COVERAGE_ANALYSIS_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


def _format_topics(topics: list[ExpectedTopic]) -> str:
    lines = []
    for t in topics:
        if t.description:
            lines.append(f"- {t.name}: {t.description}")
        else:
            lines.append(f"- {t.name}")
    return "\n".join(lines)


def _build_context_clause(question: str | None, requirements: str | None) -> str:
    parts = []
    if question:
        parts.append(f"ORIGINAL QUESTION / PROMPT:\n{question}\n")
    if requirements:
        parts.append(f"REQUIREMENTS / SPEC:\n{requirements}\n")
    return ("\n" + "\n".join(parts) + "\n") if parts else "\n"


async def analyze_coverage(
    llm: LLMProvider,
    topics: list[ExpectedTopic],
    document: str,
    question: str | None,
    requirements: str | None,
    max_document_chars: int,
) -> list[TopicCoverage]:
    """Single batched LLM call: rate every topic's coverage quality against
    the document in one pass. Batching (rather than one call per topic)
    lets the model reason about the document once and keeps cost linear in
    document size rather than in topic count."""

    if not topics:
        return []

    doc_text = document if len(document) <= max_document_chars else document[:max_document_chars] + " [...truncated...]"

    prompt = COVERAGE_ANALYSIS_USER_TEMPLATE.format(
        topics_block=_format_topics(topics),
        context_clause=_build_context_clause(question, requirements),
        document=doc_text,
    )

    raw = await llm.complete(COVERAGE_ANALYSIS_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        parsed = {"topics": []}

    # Index returned ratings by normalized name for robust matching.
    returned: dict[str, dict] = {}
    for item in parsed.get("topics", []):
        name = (item.get("name") or "").strip().lower()
        if name:
            returned[name] = item

    coverages: list[TopicCoverage] = []
    for topic in topics:
        item = returned.get(topic.name.strip().lower())
        if item is None:
            # The model dropped this topic from its response. Fail safe by
            # marking it missing with a note, rather than silently omitting
            # it from the report (an omission here would be exactly the
            # kind of gap this tool exists to catch).
            coverages.append(
                TopicCoverage(
                    topic=topic,
                    quality=QualityRating.MISSING,
                    status=QUALITY_TO_STATUS[QualityRating.MISSING],
                    explanation="The analysis model did not return a rating for this topic; treated as missing pending re-check.",
                    evidence_excerpt=None,
                )
            )
            continue

        try:
            quality = QualityRating(item.get("quality", "missing"))
        except ValueError:
            quality = QualityRating.MISSING

        excerpt = item.get("evidence_excerpt") or None
        coverages.append(
            TopicCoverage(
                topic=topic,
                quality=quality,
                status=QUALITY_TO_STATUS[quality],
                explanation=item.get("explanation", ""),
                evidence_excerpt=excerpt if quality != QualityRating.MISSING else None,
            )
        )

    return coverages
