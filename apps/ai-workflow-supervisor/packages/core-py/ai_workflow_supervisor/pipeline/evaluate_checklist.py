from __future__ import annotations

from ..adapters.base import LLMProvider
from ..models import CheckStatus, ChecklistItem, ChecklistItemResult
from ..prompts import CHECKLIST_EVALUATION_SYSTEM, CHECKLIST_EVALUATION_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


def _format_checklist(items: list[ChecklistItem]) -> str:
    lines = []
    for item in items:
        tags = []
        if item.min_count:
            tags.append(f"min_count={item.min_count}")
        if not item.required:
            tags.append("optional")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"- {item.description}{tag_str}")
    return "\n".join(lines)


def _enforce_min_count(item: ChecklistItem, status: CheckStatus, actual_count: int | None) -> tuple[CheckStatus, str | None]:
    """Deterministically override the model's status when a min_count
    requirement isn't met, rather than trusting the model's own status
    label — the count itself is objective and shouldn't be a judgment
    call."""
    if item.min_count is None or actual_count is None:
        return status, None

    if actual_count >= item.min_count:
        return status, None

    if actual_count == 0:
        return CheckStatus.NOT_SATISFIED, f"Requires at least {item.min_count}, found {actual_count}."
    return CheckStatus.PARTIALLY_SATISFIED, f"Requires at least {item.min_count}, found only {actual_count}."


async def evaluate_checklist(
    llm: LLMProvider,
    checklist: list[ChecklistItem],
    task: str,
    agent_output: str,
    max_output_chars: int,
) -> list[ChecklistItemResult]:
    """Single batched LLM call: rate every checklist item's status against
    the agent's output in one pass. Batching keeps cost linear in output
    size rather than in checklist length."""

    if not checklist:
        return []

    output_text = (
        agent_output if len(agent_output) <= max_output_chars else agent_output[:max_output_chars] + " [...truncated...]"
    )

    prompt = CHECKLIST_EVALUATION_USER_TEMPLATE.format(
        task=task, checklist_block=_format_checklist(checklist), agent_output=output_text
    )
    raw = await llm.complete(CHECKLIST_EVALUATION_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        parsed = {"items": []}

    returned: dict[str, dict] = {}
    for entry in parsed.get("items", []):
        desc = (entry.get("description") or "").strip().lower()
        if desc:
            returned[desc] = entry

    results: list[ChecklistItemResult] = []
    for item in checklist:
        entry = returned.get(item.description.strip().lower())

        if entry is None:
            # The model dropped this item from its response. Fail safe by
            # marking it not satisfied rather than silently omitting it —
            # an omission here is exactly the kind of gap this tool exists
            # to catch, especially for a completion gate.
            results.append(
                ChecklistItemResult(
                    item=item,
                    status=CheckStatus.NOT_SATISFIED,
                    explanation="The evaluation model did not return a rating for this item; treated as not satisfied pending re-check.",
                    evidence_excerpt=None,
                    actual_count=None,
                )
            )
            continue

        try:
            status = CheckStatus(entry.get("status", "not_satisfied"))
        except ValueError:
            status = CheckStatus.NOT_SATISFIED

        actual_count = entry.get("actual_count")
        status, count_note = _enforce_min_count(item, status, actual_count)

        explanation = entry.get("explanation", "")
        if count_note:
            explanation = f"{explanation} {count_note}".strip()

        excerpt = entry.get("evidence_excerpt") or None
        results.append(
            ChecklistItemResult(
                item=item,
                status=status,
                explanation=explanation,
                evidence_excerpt=excerpt if status != CheckStatus.NOT_SATISFIED else None,
                actual_count=actual_count,
            )
        )

    return results
