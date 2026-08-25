from __future__ import annotations

from ..models import CHECK_WEIGHT, CheckStatus, ChecklistItemResult, SupervisionReport


def build_report(results: list[ChecklistItemResult]) -> SupervisionReport:
    total_items = len(results)

    if total_items == 0:
        return SupervisionReport(
            task_complete=False,
            completion_score=0.0,
            total_items=0,
            satisfied_count=0,
            partially_satisfied_count=0,
            not_satisfied_count=0,
            blocking_failures=["No checklist could be derived or supplied — nothing was evaluated."],
            item_results=[],
            summary="No checklist items were available, so completion could not be verified. Supply an explicit checklist or ensure the task description is specific enough to derive one from.",
        )

    satisfied = sum(1 for r in results if r.status == CheckStatus.SATISFIED)
    partial = sum(1 for r in results if r.status == CheckStatus.PARTIALLY_SATISFIED)
    not_satisfied = sum(1 for r in results if r.status == CheckStatus.NOT_SATISFIED)

    # The gate: the task is only complete if every REQUIRED item is fully
    # satisfied. Partial credit never counts, the same way a unit test that
    # "sort of" passes still fails the build.
    blocking = [r.item.description for r in results if r.item.required and r.status != CheckStatus.SATISFIED]
    task_complete = len(blocking) == 0

    completion_score = sum(CHECK_WEIGHT[r.status] for r in results) / total_items

    summary = (
        f"{total_items} checklist item(s) evaluated: {satisfied} satisfied, {partial} partially satisfied, "
        f"{not_satisfied} not satisfied. "
        + (
            "Task is COMPLETE — every required item is satisfied."
            if task_complete
            else f"Task is NOT complete — {len(blocking)} required item(s) still unmet."
        )
    )

    return SupervisionReport(
        task_complete=task_complete,
        completion_score=round(completion_score, 1),
        total_items=total_items,
        satisfied_count=satisfied,
        partially_satisfied_count=partial,
        not_satisfied_count=not_satisfied,
        blocking_failures=blocking,
        item_results=results,
        summary=summary,
    )
