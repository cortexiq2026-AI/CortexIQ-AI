from __future__ import annotations

import asyncio
import uuid

from .adapters.base import LLMProvider, SearchProvider
from .adapters.registry import build_llm_provider, build_search_provider
from .config import SupervisorSettings
from .models import ChecklistItem, ChecklistItemSource, SupervisionReport
from .pipeline.derive_checklist import derive_checklist
from .pipeline.evaluate_checklist import evaluate_checklist
from .pipeline.scoring import build_report
from .pipeline.verify_items import verify_item


class WorkflowSupervisor:
    """The public entry point. Orchestrates:

    1. Determine the checklist — either you supply explicit criteria, or one
       is inferred from the task/goal description (unit tests written from
       the spec, before or independent of the implementation).
    2. Evaluate the agent's final output against every checklist item in a
       single batched LLM call.
    3. For items flagged needs_verification, optionally corroborate via web
       search rather than trusting the output-only evaluation alone.
    4. Score, and — critically — compute task_complete: True only if every
       REQUIRED item is fully satisfied. This is the gate: an agent cannot
       declare success while blocking_failures is non-empty.
    """

    def __init__(
        self,
        settings: SupervisorSettings | None = None,
        llm: LLMProvider | None = None,
        search: SearchProvider | None = None,
    ):
        self.settings = settings or SupervisorSettings.from_env()
        self.llm = llm or build_llm_provider(self.settings)
        self.search = search or build_search_provider(self.settings)

    async def supervise(
        self,
        task: str,
        agent_output: str,
        checklist: list[str] | None = None,
        auto_derive_checklist: bool = True,
        allow_web_verification: bool = True,
    ) -> SupervisionReport:
        items = await self._resolve_checklist(task, checklist or [], auto_derive_checklist)

        if not items:
            return build_report([])

        results = await evaluate_checklist(
            self.llm, items, task, agent_output, self.settings.max_output_chars
        )

        if allow_web_verification:
            results = await self._verify_flagged_items(results)

        return build_report(results)

    async def _resolve_checklist(
        self,
        task: str,
        checklist: list[str],
        auto_derive_checklist: bool,
    ) -> list[ChecklistItem]:
        if checklist:
            return [
                ChecklistItem(id=str(uuid.uuid4())[:8], description=desc, source=ChecklistItemSource.USER_SUPPLIED)
                for desc in checklist
            ]

        if not auto_derive_checklist:
            return []

        return await derive_checklist(self.llm, task, self.settings.max_checklist_items)

    async def _verify_flagged_items(self, results):
        flagged_indices = [i for i, r in enumerate(results) if r.item.needs_verification][: self.settings.max_verifications]
        if not flagged_indices:
            return results

        verified = await asyncio.gather(
            *(
                verify_item(self.llm, self.search, results[i], self.settings.verification_confidence_threshold)
                for i in flagged_indices
            )
        )

        updated = list(results)
        for idx, new_result in zip(flagged_indices, verified):
            updated[idx] = new_result
        return updated
