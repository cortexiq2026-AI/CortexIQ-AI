# Scoring methodology

`pipeline/scoring.py` turns a list of per-topic `TopicCoverage` ratings into
the final `CompletenessReport`.

## Quality → status → weight

Every topic gets exactly one judgment from the model: a `QualityRating`.
Everything else is derived deterministically from it (see
`models.QUALITY_TO_STATUS` and `models.QUALITY_WEIGHT`):

| Quality     | Status              | Weight |
|-------------|----------------------|--------|
| excellent   | covered              | 100    |
| good        | covered              | 80     |
| mid         | partially_covered    | 50     |
| low         | partially_covered    | 25     |
| missing     | not_covered          | 0      |

## Completeness score (0-100)

```
completeness_score = sum(weight[topic.quality] for topic in topics) / total_topics
```

A straight weighted average across all resolved topics. Deliberately simple
and equal-weighted — see "Known limitations" below for why you might want to
change that for your use case.

If **zero topics** were resolved (no `expected_topics` supplied and
auto-derivation was disabled or returned nothing), the score is `0.0` with
`total_topics = 0`. This is different from the Fact Checker's "nothing to
check = 100" convention: there, checkable claims not existing is a *good*
sign (nothing false was said). Here, a checklist not existing is not a
signal about the document's quality at all — it's a configuration gap — so
scoring it as "complete" would be misleading. Treat `total_topics == 0` as
"re-run with topics," not as a passing grade.

## Why "missing" is weighted 0, not partial credit

An unaddressed topic is weighted as a hard zero rather than, say, 10 points
of "at least it wasn't wrong." This is intentional: the entire value of this
tool is surfacing what's absent, and a scoring scheme that cushions absence
would undercut exactly the signal it exists to produce.

## Known limitations of this scoring model

- **Equal topic weighting.** A missing "risks" section and a missing
  "formatting notes" section currently count the same. If some topics matter
  far more than others for your domain, extend `ExpectedTopic` with a
  priority/weight field and adjust `build_report` to use a weighted sum
  instead of a plain average — this is flagged as a natural extension point
  in `docs/ARCHITECTURE.md`.
- **No inter-topic redundancy detection.** If two derived topics overlap
  heavily (e.g. "Data Security" and "Encryption"), both are scored
  independently, which can double-count or double-penalize the same gap.
  Auto-derived topic lists are more prone to this than hand-supplied ones.
- **The judging model can be wrong or inconsistent.** "Good" vs. "mid" is a
  judgment call, and different runs (or different provider models) may rate
  borderline cases differently. Treat the score as directional, not as a
  precise, reproducible metric — especially near category boundaries.
- **Auto-derived checklists reflect general convention, not your specific
  standards.** For contexts with real compliance stakes, supply
  `expected_topics` explicitly rather than trusting the model's idea of
  what a "complete" document in your domain looks like.
