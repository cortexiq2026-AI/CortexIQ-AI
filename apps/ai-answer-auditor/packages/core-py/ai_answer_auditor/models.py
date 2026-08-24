"""Core data models for the AI Answer Auditor pipeline.

These are the shapes that flow between pipeline stages, and the shape of the
final report handed back to the caller. Kept as plain pydantic models so they
serialize cleanly across the library / MCP / REST boundaries.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    CAUSAL = "causal"
    DEFINITIONAL = "definitional"
    PROCEDURAL = "procedural"
    OPINION = "opinion"
    PREDICTION = "prediction"


class EvidenceRequirement(str, Enum):
    REQUIRED = "required"
    NOT_REQUIRED = "not_required"
    CONTEXTUAL = "contextual"  # only checkable against supplied sources, not the open web


class VerificationStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    NOT_APPLICABLE = "not_applicable"


class SourceDocument(BaseModel):
    """A piece of source material the original answer was (or should have
    been) grounded in — e.g. the RAG context passed to the generating model."""

    id: str
    text: str
    title: Optional[str] = None
    url: Optional[str] = None


class Claim(BaseModel):
    id: str
    text: str
    claim_type: ClaimType
    evidence_requirement: EvidenceRequirement
    source_span: Optional[str] = Field(
        default=None, description="The verbatim snippet of the original answer this claim was drawn from."
    )


class Evidence(BaseModel):
    origin: str = Field(description="'source:<id>' for supplied documents, or 'web:<url>' for search results")
    excerpt: str
    supports: bool
    note: Optional[str] = None


class ClaimVerification(BaseModel):
    claim: Claim
    status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    explanation: str


class AuditReport(BaseModel):
    verification_score: float = Field(ge=0.0, le=100.0, description="Overall trust score, 0-100")
    completeness_score: float = Field(ge=0.0, le=100.0, description="% of evidence-requiring claims that were actually checkable")
    total_claims: int
    checkable_claims: int
    supported_claims: int
    unsupported_claims: int
    contradicted_claims: int
    needs_human_review: int
    claim_verifications: list[ClaimVerification]
    summary: str

    def to_compact_dict(self) -> dict:
        """A short summary form, e.g. for logging or chat-surface display."""
        return {
            "verification_score": self.verification_score,
            "completeness_score": self.completeness_score,
            "total_claims": self.total_claims,
            "unsupported_claims": self.unsupported_claims,
            "contradicted_claims": self.contradicted_claims,
            "needs_human_review": self.needs_human_review,
        }


class AuditRequest(BaseModel):
    """Input to Auditor.audit — also the REST/MCP request shape."""

    answer: str
    question: Optional[str] = None
    sources: list[SourceDocument] = Field(default_factory=list)
    allow_web_search: bool = True
