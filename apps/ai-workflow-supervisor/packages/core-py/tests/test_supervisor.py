import json

import pytest

from ai_workflow_supervisor import WorkflowSupervisor, SupervisorSettings
from ai_workflow_supervisor.models import CheckStatus

from .fakes import EmptySearchProvider, ScriptedLLMProvider, ScriptedSearchProvider


@pytest.mark.asyncio
async def test_supervise_with_explicit_checklist_all_satisfied():
    evaluation_response = json.dumps(
        {
            "items": [
                {"description": "Compares at least 3 alternatives", "status": "satisfied", "explanation": "3 options analyzed.", "evidence_excerpt": "AWS, GCP, Azure compared.", "actual_count": 3},
                {"description": "Provides a recommendation", "status": "satisfied", "explanation": "Recommends AWS.", "evidence_excerpt": "We recommend AWS.", "actual_count": None},
            ]
        }
    )
    llm = ScriptedLLMProvider([evaluation_response])
    settings = SupervisorSettings(llm_provider="anthropic", search_provider="none")
    supervisor = WorkflowSupervisor(settings=settings, llm=llm, search=EmptySearchProvider())

    report = await supervisor.supervise(
        task="Research 3 cloud architecture options and recommend one.",
        agent_output="AWS, GCP, Azure compared on cost and scalability. We recommend AWS.",
        checklist=["Compares at least 3 alternatives", "Provides a recommendation"],
        auto_derive_checklist=False,
    )

    assert report.total_items == 2
    assert report.task_complete is True
    assert report.blocking_failures == []
    assert report.completion_score == 100.0


@pytest.mark.asyncio
async def test_supervise_blocks_completion_on_required_failure():
    evaluation_response = json.dumps(
        {
            "items": [
                {"description": "Compares at least 3 alternatives", "status": "partially_satisfied", "explanation": "Only 2 analyzed in depth.", "evidence_excerpt": "AWS and GCP compared.", "actual_count": 2},
                {"description": "Provides a recommendation", "status": "satisfied", "explanation": "Recommends AWS.", "evidence_excerpt": "We recommend AWS.", "actual_count": None},
            ]
        }
    )
    llm = ScriptedLLMProvider([evaluation_response])
    settings = SupervisorSettings(llm_provider="anthropic", search_provider="none")
    supervisor = WorkflowSupervisor(settings=settings, llm=llm, search=EmptySearchProvider())

    report = await supervisor.supervise(
        task="Research 3 cloud architecture options and recommend one.",
        agent_output="AWS and GCP compared. We recommend AWS.",
        checklist=["Compares at least 3 alternatives", "Provides a recommendation"],
        auto_derive_checklist=False,
    )

    assert report.task_complete is False
    assert "Compares at least 3 alternatives" in report.blocking_failures
    assert report.completion_score == 75.0  # (50 + 100) / 2


@pytest.mark.asyncio
async def test_min_count_overrides_model_status_deterministically():
    # Model claims "satisfied" but only reports actual_count=2 against a
    # min_count=3 requirement — code should override, not trust the label.
    evaluation_response = json.dumps(
        {
            "items": [
                {"description": "Compares at least 3 alternatives", "status": "satisfied", "explanation": "Looks complete.", "evidence_excerpt": "AWS and GCP compared.", "actual_count": 2},
            ]
        }
    )
    llm = ScriptedLLMProvider([evaluation_response])
    settings = SupervisorSettings(llm_provider="anthropic", search_provider="none")
    supervisor = WorkflowSupervisor(settings=settings, llm=llm, search=EmptySearchProvider())

    from ai_workflow_supervisor.models import ChecklistItem, ChecklistItemSource
    from ai_workflow_supervisor.pipeline.evaluate_checklist import evaluate_checklist

    checklist = [ChecklistItem(id="c1", description="Compares at least 3 alternatives", min_count=3, source=ChecklistItemSource.USER_SUPPLIED)]
    results = await evaluate_checklist(llm, checklist, "task", "output", 15000)

    assert results[0].status == CheckStatus.PARTIALLY_SATISFIED
    assert "found only 2" in results[0].explanation


@pytest.mark.asyncio
async def test_web_verification_overturns_a_status():
    from ai_workflow_supervisor.models import ChecklistItem, ChecklistItemResult, ChecklistItemSource
    from ai_workflow_supervisor.pipeline.verify_items import verify_item

    verification_response = json.dumps(
        {"verdict": "outdated_or_wrong", "confidence": 0.9, "explanation": "Pricing page shows a different current rate."}
    )
    llm = ScriptedLLMProvider([verification_response])
    search = ScriptedSearchProvider([{"url": "https://example.com/pricing", "title": "Pricing", "snippet": "Current rate is different."}])

    item = ChecklistItem(id="c1", description="States current EC2 pricing", needs_verification=True, source=ChecklistItemSource.AUTO_DERIVED)
    result = ChecklistItemResult(item=item, status=CheckStatus.SATISFIED, explanation="Cites a price.", evidence_excerpt="$0.10/hr for t3.micro")

    updated = await verify_item(llm, search, result, confidence_threshold=0.6)

    assert updated.status == CheckStatus.NOT_SATISFIED
    assert updated.verification_note is not None


@pytest.mark.asyncio
async def test_no_checklist_returns_empty_incomplete_report():
    llm = ScriptedLLMProvider([json.dumps({"items": []})])
    settings = SupervisorSettings(llm_provider="anthropic", search_provider="none")
    supervisor = WorkflowSupervisor(settings=settings, llm=llm, search=EmptySearchProvider())

    report = await supervisor.supervise(task="", agent_output="Some output.", auto_derive_checklist=False)

    assert report.total_items == 0
    assert report.task_complete is False
