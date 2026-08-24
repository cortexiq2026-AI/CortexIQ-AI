# Scoring methodology

`pipeline/scoring.py` turns a list of per-claim `ClaimVerification`s into the
final `AuditReport`. Two numbers are produced; they answer different
questions and can (and often should) disagree.

## Verification score (0-100)

**Question it answers: "How much of this answer's checkable content turned
out to be trustworthy?"**

Only claims tagged `evidence_requirement != not_required` count toward this
score — an opinion-only answer isn't penalized for being unfalsifiable.

```
penalty = (contradicted * 1.0 + unsupported * 0.6 + needs_human_review * 0.25) / checkable_claims
verification_score = 100 * (1 - penalty), floored at 0
```

Weights are intentionally asymmetric:

- **Contradicted (weight 1.0)** — an outright false statement is the worst
  outcome; a single confidently-contradicted claim in a short answer will
  drag the score down hard, by design.
- **Unsupported (weight 0.6)** — no evidence found anywhere. Could be a
  fabrication, or could just be something the pipeline's sources/search
  didn't cover. Penalized meaningfully but less than a confirmed
  contradiction.
- **Needs human review (weight 0.25)** — the pipeline found *something* but
  wasn't confident enough to call it either way. This is the pipeline being
  honest about uncertainty, not a detected problem, so it's penalized
  lightly rather than treated as equivalent to "unsupported."

If there are zero checkable claims, the score is 100 — there's nothing false
in the answer because there's nothing falsifiable in it. Whether that's the
right default for your use case depends on context; override
`pipeline/scoring.py` if you'd rather treat "nothing to check" as neutral
(e.g. 50) instead of clean.

## Completeness score (0-100)

**Question it answers: "How much of the answer's checkable content did the
auditor actually manage to resolve, one way or the other?"**

```
completeness_score = 100 * (supported + contradicted) / checkable_claims
```

A high verification score with a *low* completeness score is a meaningful
combination: it means most of what the auditor could confidently check
turned out fine, but a large fraction of claims went unresolved (typically
because no search provider is configured, or supplied sources didn't cover
the topic) — a signal to add sources or enable web search, not necessarily
that the answer is trustworthy.

## Human-review threshold

`AUDITOR_HUMAN_REVIEW_THRESHOLD` (default `0.6`) is the confidence floor
below which a `supports`/`contradicts` verdict from the LLM judge gets
downgraded to `needs_human_review` instead of being taken at face value. Raise
it to be more conservative (more claims get kicked to human review instead of
auto-resolved); lower it to let the pipeline commit to more verdicts on
thinner evidence.

## Known limitations of this scoring model

- It's a heuristic weighting, not a calibrated statistical model. The
  0.6/0.25 weights reflect a judgment call about relative severity, not a
  measured error rate.
- It does not weight claims by importance/centrality to the answer — one
  wrong footnote-level detail and one wrong central claim are scored
  identically per-claim. If that matters for your use case, extend
  `Claim`/`ClaimVerification` with a salience field and fold it into the
  penalty formula.
- The LLM that judges "supports/contradicts/no_evidence" can itself be wrong,
  particularly on nuanced or contested claims. Treat the whole report as a
  second opinion, not a verdict.
