from __future__ import annotations

import uuid

from .adapters.base import LLMProvider
from .adapters.registry import build_llm_provider
from .config import CheckerSettings
from .models import CompletenessReport, ExpectedTopic, TopicSource
from .pipeline.analyze_coverage import analyze_coverage
from .pipeline.derive_topics import derive_topics
from .pipeline.scoring import build_report


class CompletenessChecker:
    """The public entry point. Orchestrates:

    1. Determine expected topics — use the caller-supplied list, or infer one
       from the question/requirements/document_type.
    2. Analyze the document's coverage of each topic (quality rating +
       explanation + evidence excerpt), in a single batched LLM call.
    3. Score and assemble the final report.

    Note what this does NOT do: it never judges whether statements in the
    document are true. That's a different tool's job (see the companion
    AI Answer Auditor project). This tool only asks "is this thorough?"
    """

    def __init__(self, settings: CheckerSettings | None = None, llm: LLMProvider | None = None):
        self.settings = settings or CheckerSettings.from_env()
        self.llm = llm or build_llm_provider(self.settings)

    async def check(
        self,
        answer: str,
        question: str | None = None,
        requirements: str | None = None,
        document_type: str | None = None,
        expected_topics: list[str] | None = None,
        auto_derive_topics: bool = True,
    ) -> CompletenessReport:
        topics = await self._resolve_topics(
            question=question,
            requirements=requirements,
            document_type=document_type,
            expected_topics=expected_topics or [],
            auto_derive_topics=auto_derive_topics,
        )

        if not topics:
            return build_report([])

        coverages = await analyze_coverage(
            self.llm,
            topics,
            answer,
            question,
            requirements,
            self.settings.max_document_chars,
        )

        return build_report(coverages)

    async def _resolve_topics(
        self,
        question: str | None,
        requirements: str | None,
        document_type: str | None,
        expected_topics: list[str],
        auto_derive_topics: bool,
    ) -> list[ExpectedTopic]:
        if expected_topics:
            return [
                ExpectedTopic(id=str(uuid.uuid4())[:8], name=name, source=TopicSource.USER_SUPPLIED)
                for name in expected_topics
            ]

        if not auto_derive_topics:
            return []

        return await derive_topics(
            self.llm,
            question=question,
            requirements=requirements,
            document_type=document_type,
            max_topics=self.settings.max_topics,
        )
