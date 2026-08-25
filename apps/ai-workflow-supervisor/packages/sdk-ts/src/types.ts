export type ChecklistItemSource = "user_supplied" | "auto_derived";

export type CheckStatus = "satisfied" | "partially_satisfied" | "not_satisfied";

export interface ChecklistItem {
  id: string;
  description: string;
  required: boolean;
  needs_verification: boolean;
  min_count?: number | null;
  source: ChecklistItemSource;
}

export interface ChecklistItemResult {
  item: ChecklistItem;
  status: CheckStatus;
  explanation: string;
  evidence_excerpt?: string | null;
  actual_count?: number | null;
  verification_note?: string | null;
}

export interface SupervisionReport {
  task_complete: boolean;
  completion_score: number;
  total_items: number;
  satisfied_count: number;
  partially_satisfied_count: number;
  not_satisfied_count: number;
  blocking_failures: string[];
  item_results: ChecklistItemResult[];
  summary: string;
}

export interface SupervisionRequest {
  task: string;
  agent_output: string;
  checklist?: string[];
  auto_derive_checklist?: boolean;
  allow_web_verification?: boolean;
}
