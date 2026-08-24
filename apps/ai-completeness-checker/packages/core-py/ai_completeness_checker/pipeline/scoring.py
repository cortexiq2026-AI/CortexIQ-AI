from __future__ import annotations

from ..models import CompletenessReport, CoverageStatus, QUALITY_WEIGHT, TopicCoverage


def build_report(coverages: list[TopicCoverage]) -> CompletenessReport:
    total_topics = len(coverages)

    if total_topics == 0:
        return CompletenessReport(
            completeness_score=0.0,
            total_topics=0,
            covered_count=0,
            partially_covered_count=0,
            missing_count=0,
            quality_breakdown={},
            topic_coverage=[],
            summary="No expected topics were supplied or could be derived, so no coverage analysis was performed.",
        )

    covered = sum(1 for c in coverages if c.status == CoverageStatus.COVERED)
    partial = sum(1 for c in coverages if c.status == CoverageStatus.PARTIALLY_COVERED)
    missing = sum(1 for c in coverages if c.status == CoverageStatus.NOT_COVERED)

    quality_breakdown: dict[str, int] = {}
    for c in coverages:
        quality_breakdown[c.quality.value] = quality_breakdown.get(c.quality.value, 0) + 1

    # Weighted average quality across all topics. Missing topics contribute
    # a hard 0, which is deliberate: an unaddressed requirement should pull
    # the score down more sharply than a merely thin one.
    total_weight = sum(QUALITY_WEIGHT[c.quality] for c in coverages)
    completeness_score = total_weight / total_topics

    summary = (
        f"{total_topics} topic(s) checked: {covered} covered, {partial} partially covered, "
        f"{missing} missing entirely."
    )

    return CompletenessReport(
        completeness_score=round(completeness_score, 1),
        total_topics=total_topics,
        covered_count=covered,
        partially_covered_count=partial,
        missing_count=missing,
        quality_breakdown=quality_breakdown,
        topic_coverage=coverages,
        summary=summary,
    )
