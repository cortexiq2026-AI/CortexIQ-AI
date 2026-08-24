export type ClaimType =
  | "factual"
  | "statistical"
  | "causal"
  | "definitional"
  | "procedural"
  | "opinion"
  | "prediction";

export type EvidenceRequirement = "required" | "not_required" | "contextual";

export type VerificationStatus =
  | "supported"
  | "contradicted"
  | "unsupported"
  | "needs_human_review"
  | "not_applicable";

export interface SourceDocument {
  id: string;
  text: string;
  title?: string;
  url?: string;
}

export interface Claim {
  id: string;
  text: string;
  claim_type: ClaimType;
  evidence_requirement: EvidenceRequirement;
  source_span?: string;
}

export interface Evidence {
  origin: string;
  excerpt: string;
  supports: boolean;
  note?: string;
}

export interface ClaimVerification {
  claim: Claim;
  status: VerificationStatus;
  confidence: number;
  evidence: Evidence[];
  explanation: string;
}

export interface AuditReport {
  verification_score: number;
  completeness_score: number;
  total_claims: number;
  checkable_claims: number;
  supported_claims: number;
  unsupported_claims: number;
  contradicted_claims: number;
  needs_human_review: number;
  claim_verifications: ClaimVerification[];
  summary: string;
}

export interface AuditRequest {
  answer: string;
  question?: string;
  sources?: SourceDocument[];
  allow_web_search?: boolean;
}
