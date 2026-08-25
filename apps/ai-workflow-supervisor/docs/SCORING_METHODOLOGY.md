# Scoring & gating methodology

`pipeline/scoring.py` turns per-item `ChecklistItemResult`s into the final
`SupervisionReport`. There are two outputs here, and they answer different
questions — **only one of them is the actual gate.**

## `task_complete` — the gate

```
blocking_failures = [item.description for item in results
                      if item.required and item.status != SATISFIED]
task_complete = len(blocking_failures) == 0
```

This is deliberately binary and strict, mirroring how a test suite works: a
required item that's `partially_satisfied` still blocks completion, exactly
like a unit test that "sort of" passes still fails CI. There is no partial
credit toward `task_complete` — that's the entire point of using this as a
gate rather than a report.

Non-`required` items never appear in `blocking_failures` regardless of their
status — they can inform the diagnostic score below, but they never stop
the agent from being considered done.

## `completion_score` (0-100) — diagnostic only

```
completion_score = sum(weight[item.status] for item in results) / total_items
# weight: satisfied=100, partially_satisfied=50, not_satisfied=0
```

This is a smoothed, informational signal — useful for tracking "how close"
a failing run was, or for comparing runs over time — but **it is not the
gate**. A run can have a high `completion_score` (e.g. 90) and still have
`task_complete=False`, if the one unmet item happens to be required. Don't
substitute this score for checking `task_complete` directly.

## Why `min_count` is enforced in code, not just judged by the model

When a checklist item has `min_count` set (e.g. "at least 3 alternatives"),
`evaluate_checklist` asks the model for both a `status` label and an
`actual_count`. Rather than trusting the label, `_enforce_min_count`
recomputes the status directly from the count:

- `actual_count >= min_count` → keep the model's status as-is.
- `actual_count == 0` → force `not_satisfied`.
- `0 < actual_count < min_count` → force `partially_satisfied`.

This avoids a specific failure mode: a model that says "satisfied" while
also (correctly) reporting `actual_count: 2` against a `min_count: 3`
requirement — an internally inconsistent response that would otherwise let
a genuinely incomplete result pass the gate.

## Why `needs_verification` items can override a status, but conservatively

`verify_item` only changes a result's `status` when the web-verification
verdict is `outdated_or_wrong` **and** its confidence clears
`SUPERVISOR_VERIFICATION_THRESHOLD` (default `0.6`). A `confirmed` verdict
never downgrades anything (it just adds a `verification_note`), and an
`inconclusive` verdict — or one with confidence below the threshold — never
changes the status either. Raise the threshold to make verification more
conservative (harder to overturn an output-only status); lower it to let
weaker web evidence override more readily.

## Known limitations

- **All required items block equally.** There's currently no notion of "this
  required item matters more than that one" — any single unmet required
  item is as blocking as any other. If your use case needs graded severity,
  extend `ChecklistItem` with a priority field and adjust
  `build_report`/`blocking_failures` accordingly (see `docs/ARCHITECTURE.md`).
- **The evaluating model can be wrong.** `satisfied` vs. `partially_satisfied`
  is a judgment call on non-count-based items, and different runs or
  provider models may disagree on borderline cases. Treat `task_complete` as
  a strong signal to gate on, not an infallible verdict — especially for
  high-stakes automation, consider a human review step when
  `completion_score` is high but not 100 despite `task_complete=True`
  (i.e. optional items are failing) as a sanity check.
- **Auto-derived checklists reflect general task-decomposition conventions,**
  not your organization's specific definition of "done." Supply an explicit
  `checklist` for anything with real operational stakes.
