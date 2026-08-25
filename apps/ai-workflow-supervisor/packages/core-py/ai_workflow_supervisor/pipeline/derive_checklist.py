from __future__ import annotations

import uuid

from ..adapters.base import LLMProvider
from ..models import ChecklistItem, ChecklistItemSource
from ..prompts import CHECKLIST_DERIVATION_SYSTEM, CHECKLIST_DERIVATION_USER_TEMPLATE
from .._json_utils import parse_json_response, LLMJSONParseError


async def derive_checklist(
    llm: LLMProvider,
    task: str,
    max_items: int,
) -> list[ChecklistItem]:
    """Infer a checklist of testable success criteria from the task/goal
    description alone — this runs before the agent's output even exists,
    the same way you'd write unit tests before (or independent of) the
    implementation."""

    if not task or not task.strip():
        return []

    prompt = CHECKLIST_DERIVATION_USER_TEMPLATE.format(task=task, max_items=max_items)
    raw = await llm.complete(CHECKLIST_DERIVATION_SYSTEM, prompt, json_mode=True)

    try:
        parsed = parse_json_response(raw)
    except LLMJSONParseError:
        return []

    items: list[ChecklistItem] = []
    for entry in parsed.get("items", [])[:max_items]:
        description = entry.get("description")
        if not description:
            continue
        items.append(
            ChecklistItem(
                id=str(uuid.uuid4())[:8],
                description=description,
                required=bool(entry.get("required", True)),
                needs_verification=bool(entry.get("needs_verification", False)),
                min_count=entry.get("min_count"),
                source=ChecklistItemSource.AUTO_DERIVED,
            )
        )
    return items
