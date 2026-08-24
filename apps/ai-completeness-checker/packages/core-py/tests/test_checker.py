import json

import pytest

from ai_completeness_checker import CompletenessChecker, CheckerSettings
from ai_completeness_checker.models import CoverageStatus, QualityRating

from .fakes import ScriptedLLMProvider


@pytest.mark.asyncio
async def test_check_with_explicit_topics():
    coverage_response = json.dumps(
        {
            "topics": [
                {"name": "Authentication", "quality": "good", "explanation": "Covers login flow.", "evidence_excerpt": "Users authenticate via OAuth2."},
                {"name": "Logging", "quality": "missing", "explanation": "No mention of logging anywhere.", "evidence_excerpt": ""},
            ]
        }
    )
    llm = ScriptedLLMProvider([coverage_response])
    settings = CheckerSettings(llm_provider="anthropic")
    checker = CompletenessChecker(settings=settings, llm=llm)

    report = await checker.check(
        answer="Users authenticate via OAuth2. The system supports role-based access.",
        expected_topics=["Authentication", "Logging"],
        auto_derive_topics=False,
    )

    assert report.total_topics == 2
    assert report.covered_count == 1
    assert report.missing_count == 1
    assert report.completeness_score == 40.0  # (80 + 0) / 2
    statuses = {c.topic.name: c.status for c in report.topic_coverage}
    assert statuses["Authentication"] == CoverageStatus.COVERED
    assert statuses["Logging"] == CoverageStatus.NOT_COVERED


@pytest.mark.asyncio
async def test_check_auto_derives_topics_when_none_supplied():
    derivation_response = json.dumps(
        {"topics": [{"name": "Scope", "description": "What is and isn't included"}]}
    )
    coverage_response = json.dumps(
        {"topics": [{"name": "Scope", "quality": "mid", "explanation": "Briefly mentioned.", "evidence_excerpt": "covers the API layer"}]}
    )
    llm = ScriptedLLMProvider([derivation_response, coverage_response])
    settings = CheckerSettings(llm_provider="anthropic")
    checker = CompletenessChecker(settings=settings, llm=llm)

    report = await checker.check(
        answer="This proposal covers the API layer.",
        question="What does this proposal cover?",
        auto_derive_topics=True,
    )

    assert report.total_topics == 1
    assert report.topic_coverage[0].topic.source.value == "auto_derived"
    assert report.topic_coverage[0].quality == QualityRating.MID
    assert report.completeness_score == 50.0


@pytest.mark.asyncio
async def test_check_missing_topic_in_model_response_is_marked_missing():
    # Model only returns a rating for one of the two requested topics —
    # pipeline should not silently drop the other.
    coverage_response = json.dumps(
        {"topics": [{"name": "Authentication", "quality": "excellent", "explanation": "Thorough.", "evidence_excerpt": "details..."}]}
    )
    llm = ScriptedLLMProvider([coverage_response])
    settings = CheckerSettings(llm_provider="anthropic")
    checker = CompletenessChecker(settings=settings, llm=llm)

    report = await checker.check(
        answer="Some answer.",
        expected_topics=["Authentication", "Encryption"],
        auto_derive_topics=False,
    )

    assert report.total_topics == 2
    encryption = next(c for c in report.topic_coverage if c.topic.name == "Encryption")
    assert encryption.status == CoverageStatus.NOT_COVERED
    assert encryption.quality == QualityRating.MISSING


@pytest.mark.asyncio
async def test_check_no_topics_returns_empty_report():
    llm = ScriptedLLMProvider([json.dumps({"topics": []})])
    settings = CheckerSettings(llm_provider="anthropic")
    checker = CompletenessChecker(settings=settings, llm=llm)

    report = await checker.check(answer="Just some text.", auto_derive_topics=False)

    assert report.total_topics == 0
    assert report.completeness_score == 0.0
