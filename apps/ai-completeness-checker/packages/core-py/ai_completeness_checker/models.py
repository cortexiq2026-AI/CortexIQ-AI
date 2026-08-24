"""Core data models for the AI Completeness Checker pipeline.

This tool answers a different question than a fact-checker: not "is this
true?" but "is this thorough?" Nothing in a flagged item is necessarily
wrong — it's just under-addressed relative to what a complete answer should
have covered.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TopicSource(str, Enum):
    USER_SUPPLIED = "user_supplied"
    AUTO_DERIVED = "auto_derived"


class QualityRating(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MID = "mid"
    LOW = "low"
    MISSING = "missing"


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_COVERED = "not_covered"


# Single source of truth for how a quality rating maps to a coverage bucket
# and a numeric weight used in scoring. Keeping this in one place means the
# LLM only ever has to produce a quality rating; status and score are always
# derived consistently from it rather than trusted as separate model output.
QUALITY_TO_STATUS: dict[QualityRating, CoverageStatus] = {
    QualityRating.EXCELLENT: CoverageStatus.COVERED,
    QualityRating.GOOD: CoverageStatus.COVERED,
    QualityRating.MID: CoverageStatus.PARTIALLY_COVERED,
    QualityRating.LOW: CoverageStatus.PARTIALLY_COVERED,
    QualityRating.MISSING: CoverageStatus.NOT_COVERED,
}

QUALITY_WEIGHT: dict[QualityRating, float] = {
    QualityRating.EXCELLENT: 100.0,
    QualityRating.GOOD: 80.0,
    QualityRating.MID: 50.0,
    QualityRating.LOW: 25.0,
    QualityRating.MISSING: 0.0,
}


class ExpectedTopic(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source: TopicSource = TopicSource.USER_SUPPLIED


class TopicCoverage(BaseModel):
    topic: ExpectedTopic
    quality: QualityRating
    status: CoverageStatus
    explanation: str
    evidence_excerpt: Optional[str] = Field(
        default=None, description="Verbatim snippet from the analyzed document supporting this rating, if any."
    )


class CompletenessReport(BaseModel):
    completeness_score: float = Field(ge=0.0, le=100.0, description="Weighted average coverage quality, 0-100")
    total_topics: int
    covered_count: int
    partially_covered_count: int
    missing_count: int
    quality_breakdown: dict[str, int] = Field(default_factory=dict, description="Count of topics per quality rating")
    topic_coverage: list[TopicCoverage]
    summary: str

    def to_compact_dict(self) -> dict:
        return {
            "completeness_score": self.completeness_score,
            "total_topics": self.total_topics,
            "covered_count": self.covered_count,
            "partially_covered_count": self.partially_covered_count,
            "missing_count": self.missing_count,
        }


class CompletenessRequest(BaseModel):
    """Input to CompletenessChecker.check — also the REST/MCP request shape."""

    answer: str = Field(description="The AI response / document text to analyze for completeness.")
    question: Optional[str] = Field(default=None, description="The original question or prompt, if any.")
    requirements: Optional[str] = Field(
        default=None, description="Free-text requirements, spec, or checklist the answer should satisfy."
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Optional hint, e.g. 'security architecture', 'legal contract', 'project plan', 'research paper'.",
    )
    expected_topics: list[str] = Field(
        default_factory=list, description="Explicit topic names to check coverage for. If empty and auto_derive_topics is True, topics are inferred."
    )
    auto_derive_topics: bool = Field(
        default=True, description="If expected_topics is empty, infer a topic checklist from question/requirements/document_type."
    )
