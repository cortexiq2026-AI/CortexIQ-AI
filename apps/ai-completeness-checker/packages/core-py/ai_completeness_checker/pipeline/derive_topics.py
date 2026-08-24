from __future__ import annotations

import uuid

from ..adapters.base import LLMProvider
from ..models import ExpectedTopic, TopicSource
from ..prompts import TOPIC_DERIVATION_SYSTEM, TOPIC_DERIVATION_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


async def derive_topics(
    llm: LLMProvider,
    question: str | None,
    requirements: str | None,
    document_type: str | None,
    max_topics: int,
) -> list[ExpectedTopic]:
    """Infer a topic checklist from whatever context is available. Falls
    back gracefully: if neither a question nor requirements are given, the
    prompt still works off document_type alone (or returns an empty list,
    which the caller should treat as 'nothing to check')."""

    question_clause = f"QUESTION / PROMPT:\n{question}\n\n" if question else ""
    requirements_clause = f"REQUIREMENTS / SPEC:\n{requirements}\n\n" if requirements else ""
    doc_type_clause = f"DOCUMENT TYPE: {document_type}\n\n" if document_type else ""

    if not (question_clause or requirements_clause or doc_type_clause):
        return []

    prompt = TOPIC_DERIVATION_USER_TEMPLATE.format(
        question_clause=question_clause,
        requirements_clause=requirements_clause,
        doc_type_clause=doc_type_clause,
        max_topics=max_topics,
    )

    raw = await llm.complete(TOPIC_DERIVATION_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        return []

    topics: list[ExpectedTopic] = []
    for item in parsed.get("topics", [])[:max_topics]:
        name = item.get("name")
        if not name:
            continue
        topics.append(
            ExpectedTopic(
                id=str(uuid.uuid4())[:8],
                name=name,
                description=item.get("description"),
                source=TopicSource.AUTO_DERIVED,
            )
        )
    return topics
