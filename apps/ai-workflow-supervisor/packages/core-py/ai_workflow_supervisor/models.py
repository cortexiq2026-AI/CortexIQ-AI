"""Core data models for the AI Workflow Supervisor.

This tool is a completion gate, not a report card: an agent's run is not
allowed to be declared "done" until every required checklist item is
satisfied. Think of it as unit testing for agent output — the checklist is
the test suite, derived from the task itself, and the agent's final output
is the code under test.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChecklistItemSource(str, Enum):
    USER_SUPPLIED = "user_supplied"
    AUTO_DERIVED = "auto_derived"


class CheckStatus(str, Enum):
    SATISFIED = "satisfied"
    PARTIALLY_SATISFIED = "partially_satisfied"
    NOT_SATISFIED = "not_satisfied"


CHECK_WEIGHT: dict[CheckStatus, float] = {
    CheckStatus.SATISFIED: 100.0,
    CheckStatus.PARTIALLY_SATISFIED: 50.0,
    CheckStatus.NOT_SATISFIED: 0.0,
}


class ChecklistItem(BaseModel):
    id: str
    description: str = Field(description="A specific, testable success criterion, e.g. 'Compares at least 3 distinct cloud architecture alternatives.'")
    required: bool = Field(default=True, description="If True, this item must be SATISFIED for the task to be considered complete.")
    needs_verification: bool = Field(
        default=False,
        description="If True, this item asserts something time-sensitive or externally checkable (e.g. current pricing) that benefits from a web search rather than trusting the output alone.",
    )
    min_count: Optional[int] = Field(
        default=None, description="If set, this item requires at least this many distinct instances (e.g. 3 alternatives) — enforced in code, not just trusted from the model."
    )
    source: ChecklistItemSource = ChecklistItemSource.USER_SUPPLIED


class ChecklistItemResult(BaseModel):
    item: ChecklistItem
    status: CheckStatus
    explanation: str
    evidence_excerpt: Optional[str] = None
    actual_count: Optional[int] = Field(default=None, description="Distinct instances found, when item.min_count is set.")
    verification_note: Optional[str] = Field(default=None, description="Set when a web-verification pass ran and adjusted or corroborated the status.")


class SupervisionReport(BaseModel):
    task_complete: bool = Field(description="True only if every required checklist item is SATISFIED. Partial credit never counts as complete.")
    completion_score: float = Field(ge=0.0, le=100.0, description="Weighted average across all checklist items, 0-100 — a diagnostic score, not the pass/fail gate itself.")
    total_items: int
    satisfied_count: int
    partially_satisfied_count: int
    not_satisfied_count: int
    blocking_failures: list[str] = Field(
        default_factory=list, description="Descriptions of required items that are not yet SATISFIED — what's standing between the agent and 'done'."
    )
    item_results: list[ChecklistItemResult]
    summary: str

    def to_compact_dict(self) -> dict:
        return {
            "task_complete": self.task_complete,
            "completion_score": self.completion_score,
            "total_items": self.total_items,
            "satisfied_count": self.satisfied_count,
            "partially_satisfied_count": self.partially_satisfied_count,
            "not_satisfied_count": self.not_satisfied_count,
            "blocking_failures": self.blocking_failures,
        }


class SupervisionRequest(BaseModel):
    """Input to WorkflowSupervisor.supervise — also the REST/MCP request shape."""

    task: str = Field(description="The original task/goal description given to the agent.")
    agent_output: str = Field(description="The agent's final output/result to check against the checklist.")
    checklist: list[str] = Field(
        default_factory=list, description="Explicit checklist item descriptions. If empty and auto_derive_checklist is True, a checklist is inferred from the task."
    )
    auto_derive_checklist: bool = Field(default=True, description="If checklist is empty, infer one from the task description.")
    allow_web_verification: bool = Field(default=True, description="Whether to use web search to corroborate items marked needs_verification.")
