export type TopicSource = "user_supplied" | "auto_derived";

export type QualityRating = "excellent" | "good" | "mid" | "low" | "missing";

export type CoverageStatus = "covered" | "partially_covered" | "not_covered";

export interface ExpectedTopic {
  id: string;
  name: string;
  description?: string;
  source: TopicSource;
}

export interface TopicCoverage {
  topic: ExpectedTopic;
  quality: QualityRating;
  status: CoverageStatus;
  explanation: string;
  evidence_excerpt?: string;
}

export interface CompletenessReport {
  completeness_score: number;
  total_topics: number;
  covered_count: number;
  partially_covered_count: number;
  missing_count: number;
  quality_breakdown: Record<string, number>;
  topic_coverage: TopicCoverage[];
  summary: string;
}

export interface CompletenessRequest {
  answer: string;
  question?: string;
  requirements?: string;
  document_type?: string;
  expected_topics?: string[];
  auto_derive_topics?: boolean;
}
