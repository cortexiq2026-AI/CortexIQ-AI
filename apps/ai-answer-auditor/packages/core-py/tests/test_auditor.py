import json

import pytest

from ai_answer_auditor import Auditor, AuditorSettings, SourceDocument
from ai_answer_auditor.models import VerificationStatus

from .fakes import EmptySearchProvider, ScriptedLLMProvider


@pytest.mark.asyncio
async def test_audit_supported_claim():
    extraction_response = json.dumps(
        {
            "claims": [
                {
                    "text": "The Eiffel Tower was completed in 1889.",
                    "claim_type": "factual",
                    "evidence_requirement": "required",
                    "source_span": "The Eiffel Tower was completed in 1889",
                }
            ]
        }
    )
    contradiction_response = json.dumps({"contradictions": []})
    comparison_response = json.dumps(
        {
            "verdict": "supports",
            "confidence": 0.95,
            "best_excerpt": "Construction finished in 1889.",
            "source_id": "wiki",
            "explanation": "Source confirms the date directly.",
        }
    )

    llm = ScriptedLLMProvider([extraction_response, contradiction_response, comparison_response])
    settings = AuditorSettings(llm_provider="anthropic", search_provider="none")
    auditor = Auditor(settings=settings, llm=llm, search=EmptySearchProvider())

    report = await auditor.audit(
        answer="The Eiffel Tower was completed in 1889.",
        sources=[SourceDocument(id="wiki", text="Construction finished in 1889 in Paris.")],
    )

    assert report.total_claims == 1
    assert report.supported_claims == 1
    assert report.contradicted_claims == 0
    assert report.verification_score == 100.0


@pytest.mark.asyncio
async def test_audit_unsupported_claim_with_no_sources():
    extraction_response = json.dumps(
        {
            "claims": [
                {
                    "text": "The bridge spans 4.2 kilometers.",
                    "claim_type": "statistical",
                    "evidence_requirement": "required",
                    "source_span": "spans 4.2 kilometers",
                }
            ]
        }
    )
    contradiction_response = json.dumps({"contradictions": []})

    llm = ScriptedLLMProvider([extraction_response, contradiction_response])
    settings = AuditorSettings(llm_provider="anthropic", search_provider="none")
    auditor = Auditor(settings=settings, llm=llm, search=EmptySearchProvider())

    report = await auditor.audit(answer="The bridge spans 4.2 kilometers.", sources=[])

    assert report.unsupported_claims == 1
    assert report.claim_verifications[0].status == VerificationStatus.UNSUPPORTED
    assert report.verification_score < 100.0


@pytest.mark.asyncio
async def test_audit_no_claims_returns_perfect_score():
    llm = ScriptedLLMProvider([json.dumps({"claims": []})])
    settings = AuditorSettings(llm_provider="anthropic", search_provider="none")
    auditor = Auditor(settings=settings, llm=llm, search=EmptySearchProvider())

    report = await auditor.audit(answer="Thanks for the update!")

    assert report.total_claims == 0
    assert report.verification_score == 100.0
