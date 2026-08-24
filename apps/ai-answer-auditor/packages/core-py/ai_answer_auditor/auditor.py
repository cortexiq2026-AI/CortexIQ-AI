from __future__ import annotations

import asyncio

from .adapters.base import LLMProvider, SearchProvider
from .adapters.registry import build_llm_provider, build_search_provider
from .config import AuditorSettings
from .models import (
    AuditReport,
    Claim,
    ClaimVerification,
    EvidenceRequirement,
    SourceDocument,
    VerificationStatus,
)
from .pipeline.compare_sources import compare_against_sources
from .pipeline.contradictions import find_internal_contradictions
from .pipeline.extract_claims import extract_claims
from .pipeline.scoring import build_report
from .pipeline.web_verify import verify_via_web


class Auditor:
    """The public entry point. Orchestrates the full audit pipeline:

    1. Extract claims from the answer
    2. (classification happens as part of extraction)
    3. Compare claims against supplied source documents
    4. Fall back to web search for claims sources didn't resolve
    5. Detect internal contradictions
    6. Flag unsupported claims
    7/8. Score and assemble the final report

    Any of the LLM/search providers can be injected directly (useful for
    testing, or for wiring in a provider that isn't in the built-in registry
    at all). If omitted, providers are built from environment configuration.
    """

    def __init__(
        self,
        settings: AuditorSettings | None = None,
        llm: LLMProvider | None = None,
        search: SearchProvider | None = None,
    ):
        self.settings = settings or AuditorSettings.from_env()
        self.llm = llm or build_llm_provider(self.settings)
        self.search = search or build_search_provider(self.settings)

    async def audit(
        self,
        answer: str,
        question: str | None = None,
        sources: list[SourceDocument] | None = None,
        allow_web_search: bool = True,
    ) -> AuditReport:
        sources = sources or []

        claims = await extract_claims(self.llm, answer, question, self.settings.max_claims)

        if not claims:
            return build_report([])

        contradicted_ids = await find_internal_contradictions(self.llm, claims)

        verifications = await asyncio.gather(
            *(
                self._verify_claim(claim, sources, allow_web_search, contradicted_ids)
                for claim in claims
            )
        )

        return build_report(list(verifications))

    async def _verify_claim(
        self,
        claim: Claim,
        sources: list[SourceDocument],
        allow_web_search: bool,
        contradicted_ids: set[str],
    ) -> ClaimVerification:
        if claim.evidence_requirement == EvidenceRequirement.NOT_REQUIRED:
            return ClaimVerification(
                claim=claim,
                status=VerificationStatus.NOT_APPLICABLE,
                confidence=1.0,
                evidence=[],
                explanation="Opinion or trivial statement; no evidence required.",
            )

        verdict, confidence, evidence = await compare_against_sources(self.llm, claim, sources)

        # If supplied sources didn't resolve it and it's a claim the open
        # web could plausibly speak to (not "contextual"-only), try search.
        if (
            verdict == "no_evidence"
            and allow_web_search
            and claim.evidence_requirement == EvidenceRequirement.REQUIRED
        ):
            web_verdict, web_confidence, web_evidence = await verify_via_web(
                self.llm, self.search, claim, self.settings.trusted_domains
            )
            if web_verdict != "no_evidence":
                verdict, confidence, evidence = web_verdict, web_confidence, web_evidence

        status, explanation = self._resolve_status(claim, verdict, confidence, contradicted_ids)

        return ClaimVerification(
            claim=claim,
            status=status,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
        )

    def _resolve_status(
        self,
        claim: Claim,
        verdict: str,
        confidence: float,
        contradicted_ids: set[str],
    ) -> tuple[VerificationStatus, str]:
        threshold = self.settings.human_review_threshold

        if claim.id in contradicted_ids:
            return VerificationStatus.CONTRADICTED, "Contradicts another claim in the same answer."

        if verdict == "contradicts":
            if confidence >= threshold:
                return VerificationStatus.CONTRADICTED, "Contradicted by available evidence."
            return VerificationStatus.NEEDS_HUMAN_REVIEW, "Possible contradiction, but confidence was low."

        if verdict == "supports":
            if confidence >= threshold:
                return VerificationStatus.SUPPORTED, "Supported by available evidence."
            return VerificationStatus.NEEDS_HUMAN_REVIEW, "Weak supporting evidence found; confidence too low to confirm."

        # verdict == "no_evidence"
        if claim.evidence_requirement == EvidenceRequirement.CONTEXTUAL:
            return VerificationStatus.UNSUPPORTED, "No supplied source document addressed this claim."
        return VerificationStatus.UNSUPPORTED, "No supporting evidence found in supplied sources or web search."
