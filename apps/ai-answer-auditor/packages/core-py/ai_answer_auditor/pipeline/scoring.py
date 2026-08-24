from __future__ import annotations

from ..models import AuditReport, ClaimVerification, EvidenceRequirement, VerificationStatus


def build_report(verifications: list[ClaimVerification]) -> AuditReport:
    total_claims = len(verifications)

    checkable = [v for v in verifications if v.claim.evidence_requirement != EvidenceRequirement.NOT_REQUIRED]
    checkable_claims = len(checkable)

    supported = sum(1 for v in verifications if v.status == VerificationStatus.SUPPORTED)
    unsupported = sum(1 for v in verifications if v.status == VerificationStatus.UNSUPPORTED)
    contradicted = sum(1 for v in verifications if v.status == VerificationStatus.CONTRADICTED)
    needs_review = sum(1 for v in verifications if v.status == VerificationStatus.NEEDS_HUMAN_REVIEW)

    # --- Verification score --------------------------------------------
    # Weighted: contradictions are penalized hardest (an outright false
    # statement is worse than one we simply couldn't verify), unsupported
    # claims moderately, and needs_human_review only lightly (it's an
    # honest "unsure", not a detected problem).
    if checkable_claims == 0:
        # Nothing needed checking (e.g. a purely opinion-based answer) —
        # score reflects that there was nothing to contradict or leave
        # unsupported, not a false "perfect" grounding claim.
        verification_score = 100.0
    else:
        penalty = (contradicted * 1.0 + unsupported * 0.6 + needs_review * 0.25) / checkable_claims
        verification_score = max(0.0, 100.0 * (1 - penalty))

    # --- Completeness score ----------------------------------------------
    # Of the claims that actually required evidence, how many did we reach
    # a confident supported/contradicted verdict on (vs. shrugging into
    # unsupported/needs_review for lack of evidence)?
    if checkable_claims == 0:
        completeness_score = 100.0
    else:
        resolved = sum(
            1
            for v in checkable
            if v.status in (VerificationStatus.SUPPORTED, VerificationStatus.CONTRADICTED)
        )
        completeness_score = 100.0 * resolved / checkable_claims

    summary = (
        f"{total_claims} claim(s) extracted, {checkable_claims} required evidence. "
        f"{supported} supported, {unsupported} unsupported, {contradicted} contradicted, "
        f"{needs_review} flagged for human review."
    )

    return AuditReport(
        verification_score=round(verification_score, 1),
        completeness_score=round(completeness_score, 1),
        total_claims=total_claims,
        checkable_claims=checkable_claims,
        supported_claims=supported,
        unsupported_claims=unsupported,
        contradicted_claims=contradicted,
        needs_human_review=needs_review,
        claim_verifications=verifications,
        summary=summary,
    )
